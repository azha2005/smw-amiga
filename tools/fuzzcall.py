#!/usr/bin/env python3
"""fuzzcall.py - G5L-R-L2: una funcion de la logica, C del PC contra 68000.

Cruce diferencial para pasar el C a asm (V1, P69): las grabaciones no
recorren todas las ramas, asi que una rama de logic68k.s que el oraculo
nunca pisa no la verifica nadie. Aca cada prueba parte de un estado real
(un frame del oraculo, `work/oracle_yi1.bin`: pagina cero y $13C0-$14FF;
o con --seedram, la ram[] entera del juego antes de un level_frame), le
cambia unos bytes que la funcion lee (los `wm_*`/`mN` que nombran los
fuentes de --src; con --slots, las doce ranuras de cada tabla de sprites;
el tileset y, a veces, los bloques Map16 alrededor de Mario) y llama a la
MISMA funcion en:

  - el C del PC (gcc -shared --cdefs, por ctypes: la referencia), y
  - el binario del 68000 (--bin, Musashi): el asm o el vbcc;

despues compara ram[] entera, el mapa, mario_unsupported, mario_events,
los globales de --extra y, con --ret, el valor devuelto.

    python tools/fuzzcall.py --func mario_collide --src player/mcoll.c --n 20000
    python tools/fuzzcall.py --func mario_collide --src player/mcoll.c --cov work/fz.json
    CDEFS='-DNOOAM -DSPR_OAM' sh tools/logicbench_build.sh
    python tools/m68kverify.py --mode loop --sprites --engine musashi --dumpall work/fz/ram.bin
    python tools/fuzzcall.py --func piranha_gfx --arg 0-11 --cdefs "-DNOOAM -DSPR_OAM" \\
        --seedram work/fz/ram.bin --slots --src player/spr_gfx.c --extra spr_oam_first:12

--cov guarda los PC del 68000 que se ejecutaron (para ver que ramas del asm
quedaron sin pisar).
"""
import argparse
import ctypes
import glob
import json
import os
import random
import re
import shutil
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import m68kverify as V   # noqa: E402

REC = V.REC
LIBSRC = ["player/mario.c", "player/mcoll.c", "player/manim.c", "player/mgfx.c", "player/mcam.c",
          "player/msprite.c", "player/mspr.c"]
TILESET = 0x1931
# no se mutan: punteros a la ROM guardados en ram[] (fuera de rom00 es indefinido en
# el C) y el tamano del nivel (con mas de 20 pantallas se lee fuera del mapa)
POINTERS = {0x82, 0x83,     # wm_SlopeSteepness
            0x5D}           # wm_ScreensInLvl
VALS = (0x00, 0x01, 0x02, 0x03, 0x04, 0x08, 0x10, 0x1C, 0x20, 0x24, 0x30, 0x7F, 0x80, 0x90, 0xF0, 0xFF)
# bloques que cambian de rama en mcoll.c / msprite.c (pagina 0 y 1)
BLOCKS = (0x00, 0x05, 0x06, 0x0C, 0x0D, 0x0E, 0x0F, 0x11, 0x1E, 0x1F, 0x20, 0x21, 0x24, 0x25,
          0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30, 0x32, 0x37, 0x38, 0x3F,
          0x52, 0x59, 0x5C, 0x66, 0x6A, 0x6B, 0x6E, 0x6F, 0x70, 0x72, 0x9C, 0xCE, 0xD2, 0xD8, 0xEC,
          0xFB)


def build_lib(out, cdefs):
    cc = shutil.which("gcc") or shutil.which("cc")
    src = [os.path.join(ROOT, f) for f in LIBSRC]
    src += sorted(glob.glob(os.path.join(ROOT, "player", "spr_*.c")))
    src += [os.path.join(ROOT, "player", "gen", "smwrom00.c")]
    # cc1 busca sus DLL (gmp, mpfr...) en el PATH: con /mingw64/bin delante sale sin
    # decir nada (codigo 1); el directorio del gcc va primero
    env = dict(os.environ, PATH=os.path.dirname(cc) + os.pathsep + os.environ.get("PATH", ""))
    p = subprocess.run([cc, "-shared", "-O1"] + cdefs.split() + ["-I" + os.path.join(ROOT, "player"),
                       "-o", out] + src, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    if p.returncode:
        sys.exit("gcc fallo:\n" + p.stdout.decode("utf-8", "replace")[-1500:])


def ram_names():
    names = {}
    for ln in open(os.path.join(ROOT, "player", "gen", "smwram.h"), encoding="latin-1"):
        m = re.match(r"#define\s+(\w+)\s+(0x[0-9A-Fa-f]+)", ln)
        if m:
            names[m.group(1)] = int(m.group(2), 16)
    return names


def read_set(srcs, names, slots, keep=()):
    adrs = set()
    for s in srcs:
        txt = open(os.path.join(ROOT, s), encoding="latin-1").read()
        for n in set(re.findall(r"\b(wm_\w+|m\d+)\b", txt)):
            if n in names and names[n] < 0x2000:
                for k in range(12 if slots else 2):     # +1: por si es de 16 bits
                    adrs.add(names[n] + k)
    adrs.add(TILESET)
    skip = set(POINTERS)
    for n in keep:
        skip.update(names[n] + k for k in range(12 if slots else 1))
    return sorted(a for a in adrs if a < 0x2000 and a not in skip)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--func", required=True, help="funcion publica en el C y en el binario")
    ap.add_argument("--arg", action="append", default=[], metavar="LO-HI",
                    help="un argumento u8 por cada --arg, al azar en LO..HI")
    ap.add_argument("--ret", choices=("byte", "int"), help="comparar tambien lo que devuelve")
    ap.add_argument("--src", action="append", default=[], help="fuentes cuyos wm_* se mutan")
    ap.add_argument("--slots", action="store_true", help="mutar las 12 ranuras de cada tabla")
    ap.add_argument("--extra", action="append", default=[], metavar="NOMBRE:BYTES",
                    help="global fuera de ram[]: igual al azar en los dos antes, se compara despues")
    ap.add_argument("--keep", action="append", default=[], metavar="wm_NOMBRE",
                    help="no mutar (un indice que el C usa sin limite: fuera de la tabla es indefinido)")
    ap.add_argument("--setx", action="append", default=[], metavar="wm_NOMBRE=VALOR",
                    help="fijar la tabla en la ranura del primer --arg (p. ej. el numero de sprite)")
    ap.add_argument("--seedram", help="semillas: ram[] enteras seguidas (m68kverify --dumpall)")
    ap.add_argument("--cdefs", default="-DNOOAM", help="opciones del C del PC (como CDEFS)")
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--bin", default=os.path.join(ROOT, "work", "logicbench.bin"))
    ap.add_argument("--lst", default=os.path.join(ROOT, "work", "logicbench.lst"))
    ap.add_argument("--lib", default=os.path.join(ROOT, "work", "fz", "libport.dll"))
    ap.add_argument("--nobuild", action="store_true", help="no recompilar la biblioteca del PC")
    ap.add_argument("--cov", help="guardar los PC ejecutados del 68000 (json)")
    ap.add_argument("--show", type=int, default=8)
    ap.add_argument("--mut", type=int, default=6, help="hasta N bytes mutados por prueba")
    a = ap.parse_args()

    os.makedirs(os.path.dirname(a.lib), exist_ok=True)
    if not a.nobuild:
        build_lib(a.lib, a.cdefs)
    lib = ctypes.CDLL(os.path.abspath(a.lib))
    pram = (ctypes.c_ubyte * 0x2000).in_dll(lib, "ram")
    map0 = open(os.path.join(ROOT, "work", "yi1_map16.bin"), "rb").read()
    pmap = (ctypes.c_ubyte * len(map0))()
    ctypes.c_void_p.in_dll(lib, "map16_lo").value = ctypes.addressof(pmap)
    ctypes.c_void_p.in_dll(lib, "map16_hi").value = ctypes.addressof(pmap) + len(map0) // 2
    punsup = ctypes.c_int.in_dll(lib, "mario_unsupported")
    pev = ctypes.c_uint.in_dll(lib, "mario_events")
    pfunc = getattr(lib, a.func)
    pfunc.argtypes = [ctypes.c_ubyte] * len(a.arg)
    pfunc.restype = ctypes.c_int
    argr = [tuple(int(v, 0) for v in s.split("-")) for s in a.arg]
    extra = [(n, int(k)) for n, k in (e.split(":") for e in a.extra)]
    pext = {n: (ctypes.c_ubyte * k).in_dll(lib, n) for n, k in extra}

    code = open(a.bin, "rb").read()
    syms = V.symbols(a.lst)
    need = ["_ram", "_map16_lo", "_map16_hi", "_mario_unsupported", "_mario_events", "map16",
            "_" + a.func] + ["_" + n for n, _ in extra]
    for s in need:
        if s not in syms:
            sys.exit("falta el simbolo %s en %s" % (s, a.lst))
    cpu = V.MusashiCPU()
    cpu.write(V.BASE, code)
    RAM, MAP = V.BASE + syms["_ram"], V.BASE + syms["map16"]
    cpu.write(V.BASE + syms["_map16_lo"], struct.pack(">I", MAP))
    cpu.write(V.BASE + syms["_map16_hi"], struct.pack(">I", MAP + len(map0) // 2))
    if "_spr_level" in syms:                # los sprites del nivel, como m68kverify --sprites
        spr = open(os.path.join(ROOT, "..", "smw-src-master", "project", "mw_e10", "levels", "data",
                                "world_1", "1", "spr.lv"), "rb").read()
        SPR = V.BASE + ((len(code) + 0x103) & ~3)
        cpu.write(SPR, spr)
        cpu.write(V.BASE + syms["_spr_level"], struct.pack(">I", SPR))
        pspr = (ctypes.c_ubyte * len(spr)).from_buffer_copy(spr)
        try:
            ctypes.c_void_p.in_dll(lib, "spr_level").value = ctypes.addressof(pspr)
        except ValueError:
            pass
    UNS, EV = V.BASE + syms["_mario_unsupported"], V.BASE + syms["_mario_events"]
    entry = V.BASE + syms["_" + a.func]
    M = cpu.M

    names = ram_names()
    setx = [(n, int(v, 0)) for n, v in (e.split("=") for e in a.setx)]
    adrs = read_set(a.src or ["player/mcoll.c"], names, a.slots, a.keep)
    seeds = []
    if a.seedram:
        sr = open(a.seedram, "rb").read()
        seeds = [sr[k:k + 0x2000] for k in range(0, len(sr) - 0x1FFF, 0x2000)]
    else:
        db = open(os.path.join(ROOT, "work", "oracle_yi1.bin"), "rb").read()
        for i in range(len(db) // REC):
            o = i * REC
            f, tl = struct.unpack_from("<IB", db, o)
            if tl == 0x29:
                ram = bytearray(0x2000)
                ram[0:0x100] = db[o + 8:o + 8 + 256]
                ram[0x13C0:0x13C0 + REC - 8 - 256] = db[o + 8 + 256:o + REC]
                ram[TILESET] = 7
                seeds.append(bytes(ram))
    rnd = random.Random(a.seed)
    half = len(map0) // 2

    pcs = set()

    def call68k(args, at=None):
        c = cpu.cpu
        c.w_reg(M.Register.A4, V.BASE)
        c.w_reg(M.Register.A7, V.STACK - 4)
        cpu.mem.w32(V.STACK - 4, V.RET)
        for k, v in enumerate(args):        # vbcc: ranuras de 32 bits, el u8 en el byte +3
            cpu.mem.w32(V.STACK + 4 * k, v)
        c.w_pc(entry if at is None else at)
        if a.cov and at is None:
            for _ in range(200000):
                pc = c.r_pc()
                if pc == V.RET:
                    break
                pcs.add(pc - V.BASE)
                cpu.m.execute(1)
            else:
                sys.exit("el 68000 no volvio de _%s en 200 000 instrucciones" % a.func)
        else:
            cpu.m.execute(10_000_000)
            if c.r_pc() != V.RET + 2 and c.r_pc() != V.RET:
                sys.exit("el 68000 no volvio de _%s" % a.func)
        return c.r_reg(M.Register.D0)

    if "_logic68k_init" in syms:            # punteros a tablas de logic68k.s (_gdi_ofs...)
        call68k([], V.BASE + syms["_logic68k_init"])
    bad = 0
    shown = []
    stats = {}
    changed = 0
    for t in range(a.n):
        ram = bytearray(rnd.choice(seeds))
        seed = bytes(ram)
        for _ in range(rnd.randrange(0, a.mut + 1)):
            ad = rnd.choice(adrs)
            r = rnd.random()
            ram[ad] = rnd.choice(VALS) if r < 0.4 else (ram[ad] + rnd.choice((-1, 1))) & 0xFF if r < 0.6 \
                else rnd.randrange(256)
        if rnd.random() < 0.05:
            ram[TILESET] = rnd.choice((1, 2, 3, 4, 5, 8, 0x0D, 0x0E))
        mp = bytearray(map0)
        if rnd.random() < 0.6:
            x = ram[0x94] | ram[0x95] << 8
            y = ram[0x96] | ram[0x97] << 8
            for _ in range(rnd.randrange(1, 7)):
                bx = (x + rnd.randrange(-16, 32)) & 0xFFFF
                by = (y + rnd.randrange(-16, 48)) & 0xFFFF
                xs = bx >> 8
                if by >= 0x1B0 or xs >= 32:
                    continue
                k = xs * 0x1B0 + (by & 0x1F0) + ((bx & 0xFF) >> 4)
                if k >= half:
                    continue
                mp[k] = rnd.choice(BLOCKS) if rnd.random() < 0.8 else rnd.randrange(256)
                mp[half + k] = rnd.choice((0, 1, 1, 1))
        args = [rnd.randint(lo, hi) for lo, hi in argr]
        for n, v in setx:
            ram[names[n] + args[0]] = v
        # PC
        ctypes.memmove(pram, bytes(ram), 0x2000)
        ctypes.memmove(pmap, bytes(mp), len(mp))
        punsup.value = 0
        pev.value = 0
        xv = {n: bytes(rnd.choice((0, 1, 4, 5, rnd.randrange(256))) for _ in range(k)) for n, k in extra}
        for n, k in extra:
            ctypes.memmove(pext[n], xv[n], k)
        rpcv = pfunc(*args)
        # 68000
        cpu.write(RAM, ram)
        cpu.write(MAP, mp)
        cpu.write(UNS, bytes(4))
        cpu.write(EV, bytes(4))
        for n, k in extra:
            cpu.write(V.BASE + syms["_" + n], xv[n])
        r68v = call68k(args)
        r68, m68 = cpu.read(RAM, 0x2000), cpu.read(MAP, len(mp))
        u68 = struct.unpack(">i", cpu.read(UNS, 4))[0]
        e68 = struct.unpack(">I", cpu.read(EV, 4))[0]
        rpc, mpc = bytes(pram), bytes(pmap)
        xd = []
        for n, k in extra:
            v68, vpc = cpu.read(V.BASE + syms["_" + n], k), bytes(pext[n])
            if v68 != vpc:
                xd.append("%s=%s/%s" % (n, v68.hex(), vpc.hex()))
        if a.ret == "byte" and (r68v & 0xFF) != (rpcv & 0xFF):
            xd.append("ret %02X/%02X" % (r68v & 0xFF, rpcv & 0xFF))
        elif a.ret == "int" and (r68v & 0xFFFFFFFF) != (rpcv & 0xFFFFFFFF):
            xd.append("ret %X/%X" % (r68v & 0xFFFFFFFF, rpcv & 0xFFFFFFFF))
        stats[u68] = stats.get(u68, 0) + 1
        changed += r68 != bytes(ram) or m68 != bytes(mp)
        if r68 == rpc and m68 == mpc and u68 == punsup.value and e68 == pev.value and not xd:
            continue
        bad += 1
        if len(shown) < a.show:
            d = ["$%04X=%02X/%02X" % (k, r68[k], rpc[k]) for k in range(0x2000) if r68[k] != rpc[k]][:8]
            d += ["mapa+%d" % k for k in range(len(mp)) if m68[k] != mpc[k]][:2]
            if u68 != punsup.value:
                d.append("unsup %d/%d" % (u68, punsup.value))
            if e68 != pev.value:
                d.append("events %x/%x" % (e68, pev.value))
            d += xd
            ch = ["$%04X:%02X->%02X" % (k, seed[k], ram[k]) for k in range(0x2000) if ram[k] != seed[k]]
            shown.append("prueba %d%s: %s   [mutado: %s]" % (t, " args %s" % args if args else "",
                                                            " ".join(d), " ".join(ch[:8])))
    print("FUZZ %s: %d pruebas, %d distintas (68000/PC)" % (a.func, a.n, bad))
    print("  cambiaron la RAM o el mapa: %d; unsupported: %s" % (changed, " ".join(
        "%d:%d" % kv for kv in sorted(stats.items()))))
    for s in shown:
        print("  " + s)
    if a.cov:
        json.dump(sorted(pcs), open(a.cov, "w"))
        print("cobertura: %d PC distintos -> %s" % (len(pcs), a.cov))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
