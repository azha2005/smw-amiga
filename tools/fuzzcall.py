#!/usr/bin/env python3
"""fuzzcall.py - G5L-R-L2: una funcion de la logica, C del PC contra 68000.

Cruce diferencial para pasar el C a asm (V1, P69): las grabaciones no
recorren todas las ramas, asi que una rama de logic68k.s que el oraculo
nunca pisa no la verifica nadie. Aca cada prueba parte de un frame real del
oraculo (`work/oracle_yi1.bin`: pagina cero y $13C0-$14FF), le cambia unos
bytes que la funcion lee (los `wm_*`/`mN` que nombran los fuentes de --src,
el tileset y, a veces, los bloques Map16 alrededor de Mario) y llama a la
MISMA funcion en:

  - el C del PC (gcc -shared -DNOOAM, por ctypes: la referencia), y
  - el binario del 68000 (work/logicbench.bin, Musashi): el asm o el vbcc;

despues compara ram[] entera, el mapa, mario_unsupported y mario_events.

    python tools/fuzzcall.py --func mario_collide --src player/mcoll.c --n 20000
    python tools/fuzzcall.py --func mario_collide --src player/mcoll.c --cov work/fz.json

--cov guarda los PC del 68000 que se ejecutaron (para ver que ramas del asm
quedaron sin pisar: `--uncov RUTINA` las lista contra el listado).
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
          0x52, 0x59, 0x5C, 0x66, 0x6E, 0x6F, 0x70, 0x72, 0x9C, 0xCE, 0xD2, 0xD8, 0xEC, 0xFB)


def build_lib(out):
    cc = shutil.which("gcc") or shutil.which("cc")
    src = [os.path.join(ROOT, f) for f in LIBSRC]
    src += sorted(glob.glob(os.path.join(ROOT, "player", "spr_*.c")))
    src += [os.path.join(ROOT, "player", "gen", "smwrom00.c")]
    p = subprocess.run([cc, "-shared", "-O1", "-DNOOAM", "-I" + os.path.join(ROOT, "player"),
                        "-o", out] + src, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode:
        sys.exit("gcc fallo:\n" + p.stdout.decode("utf-8", "replace")[-1500:])


def ram_names():
    names = {}
    for ln in open(os.path.join(ROOT, "player", "gen", "smwram.h"), encoding="latin-1"):
        m = re.match(r"#define\s+(\w+)\s+(0x[0-9A-Fa-f]+)", ln)
        if m:
            names[m.group(1)] = int(m.group(2), 16)
    return names


def read_set(srcs, names):
    adrs = set()
    for s in srcs:
        txt = open(os.path.join(ROOT, s), encoding="latin-1").read()
        for n in set(re.findall(r"\b(wm_\w+|m\d+)\b", txt)):
            if n in names and names[n] < 0x2000:
                adrs.add(names[n])
                adrs.add(names[n] + 1)          # por si es de 16 bits
    adrs.add(TILESET)
    return sorted(a for a in adrs if a < 0x2000 and a not in POINTERS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--func", required=True, help="funcion sin argumentos, publica en el C y en el binario")
    ap.add_argument("--src", action="append", default=[], help="fuentes cuyos wm_* se mutan")
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
        build_lib(a.lib)
    lib = ctypes.CDLL(os.path.abspath(a.lib))
    pram = (ctypes.c_ubyte * 0x2000).in_dll(lib, "ram")
    map0 = open(os.path.join(ROOT, "work", "yi1_map16.bin"), "rb").read()
    pmap = (ctypes.c_ubyte * len(map0))()
    ctypes.c_void_p.in_dll(lib, "map16_lo").value = ctypes.addressof(pmap)
    ctypes.c_void_p.in_dll(lib, "map16_hi").value = ctypes.addressof(pmap) + len(map0) // 2
    punsup = ctypes.c_int.in_dll(lib, "mario_unsupported")
    pev = ctypes.c_uint.in_dll(lib, "mario_events")
    pfunc = getattr(lib, a.func)

    code = open(a.bin, "rb").read()
    syms = V.symbols(a.lst)
    for s in ("_ram", "_map16_lo", "_map16_hi", "_mario_unsupported", "_mario_events", "map16", "_" + a.func):
        if s not in syms:
            sys.exit("falta el simbolo %s en %s" % (s, a.lst))
    cpu = V.MusashiCPU()
    cpu.write(V.BASE, code)
    RAM, MAP = V.BASE + syms["_ram"], V.BASE + syms["map16"]
    cpu.write(V.BASE + syms["_map16_lo"], struct.pack(">I", MAP))
    cpu.write(V.BASE + syms["_map16_hi"], struct.pack(">I", MAP + len(map0) // 2))
    UNS, EV = V.BASE + syms["_mario_unsupported"], V.BASE + syms["_mario_events"]
    entry = V.BASE + syms["_" + a.func]

    names = ram_names()
    adrs = read_set(a.src or ["player/mcoll.c"], names)
    db = open(os.path.join(ROOT, "work", "oracle_yi1.bin"), "rb").read()
    seeds = []
    for i in range(len(db) // REC):
        o = i * REC
        f, tl = struct.unpack_from("<IB", db, o)
        if tl == 0x29:
            seeds.append(o)
    rnd = random.Random(a.seed)
    half = len(map0) // 2

    pcs = set()
    if a.cov:
        M = cpu.M
        hits = pcs

        def call68k():
            c = cpu.cpu
            c.w_reg(M.Register.A4, V.BASE)
            c.w_reg(M.Register.A7, V.STACK - 4)
            cpu.mem.w32(V.STACK - 4, V.RET)
            c.w_pc(entry)
            for _ in range(200000):
                pc = c.r_pc()
                if pc == V.RET:
                    return
                hits.add(pc - V.BASE)
                cpu.m.execute(1)
            sys.exit("el 68000 no volvio de _%s en 200 000 instrucciones" % a.func)
    else:
        def call68k():
            cpu.call(entry, V.BASE)

    bad = 0
    shown = []
    stats = {}
    changed = 0
    for t in range(a.n):
        o = rnd.choice(seeds)
        ram = bytearray(0x2000)
        ram[0:0x100] = db[o + 8:o + 8 + 256]
        ram[0x13C0:0x13C0 + REC - 8 - 256] = db[o + 8 + 256:o + REC]
        ram[TILESET] = 7
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
        # PC
        ctypes.memmove(pram, bytes(ram), 0x2000)
        ctypes.memmove(pmap, bytes(mp), len(mp))
        punsup.value = 0
        pev.value = 0
        pfunc()
        # 68000
        cpu.write(RAM, ram)
        cpu.write(MAP, mp)
        cpu.write(UNS, bytes(4))
        cpu.write(EV, bytes(4))
        call68k()
        r68, m68 = cpu.read(RAM, 0x2000), cpu.read(MAP, len(mp))
        u68 = struct.unpack(">i", cpu.read(UNS, 4))[0]
        e68 = struct.unpack(">I", cpu.read(EV, 4))[0]
        rpc, mpc = bytes(pram), bytes(pmap)
        stats[u68] = stats.get(u68, 0) + 1
        changed += r68 != bytes(ram) or m68 != bytes(mp)
        if r68 == rpc and m68 == mpc and u68 == punsup.value and e68 == pev.value:
            continue
        bad += 1
        if len(shown) < a.show:
            d = ["$%04X=%02X/%02X" % (k, r68[k], rpc[k]) for k in range(0x2000) if r68[k] != rpc[k]][:8]
            d += ["mapa+%d" % k for k in range(len(mp)) if m68[k] != mpc[k]][:2]
            if u68 != punsup.value:
                d.append("unsup %d/%d" % (u68, punsup.value))
            if e68 != pev.value:
                d.append("events %x/%x" % (e68, pev.value))
            ch = ["$%04X:%02X->%02X" % (k, (db[o + 8 + k] if k < 0x100 else 0), ram[k])
                  for k in range(0x2000) if k < 0x100 and ram[k] != db[o + 8 + k]]
            shown.append("prueba %d: %s   [mutado: %s]" % (t, " ".join(d), " ".join(ch[:8])))
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
