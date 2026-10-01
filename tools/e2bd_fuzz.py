#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
e2bd_fuzz.py - mario_E2BD (player/logic68k.s, ensamblador a mano) contra el
C del PC (mgfx.c) con estados al azar: el lazo cerrado de m68kverify solo
pasa por los estados que tiene YI1 (sin estrella, sin capa, sin parpadeo...).
Cada caso: ram[] al azar con los campos que lee E2BD sesgados a los valores
que importan (MarioFrame $0A/$13/$1C/$29/$43/$45/$46, HidePlayer 0/$FF, la
estrella en $1E, PowerUp 0-3...), y se compara ram[] entera, mario_oam,
mario_osz, mario_pal, mario_events y mario_unsupported despues de la llamada.

    python tools/e2bd_fuzz.py [N] [semilla]       (N = 200000)

Necesita work/logicbench.bin/.lst (tools/logicbench_build.sh) y work/libport.so
(gcc -shared -O2 -DNOOAM, ver tools/regress.py) y machine68k.
"""
import ctypes
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m68kverify as mv  # noqa: E402

WORK = os.path.join(HERE, "..", "work")
R = {  # direcciones de ram[] (player/gen/smwram.h)
    "m9": 0x09, "m12": 0x0C, "m13": 0x0D, "FrameA": 0x13, "FrameB": 0x14, "PowerUp": 0x19,
    "Bg1H": 0x1A, "Bg1V": 0x1C, "SprProp": 0x64, "Dir": 0x76, "Hide": 0x78, "XPos": 0x94,
    "YPos": 0x96, "Locked": 0x9D, "OWChar": 0x0DB3, "Walk": 0x13DB, "Frame": 0x13E0,
    "Wall": 0x13E3, "Behind": 0x13F9, "Frozen": 0x13FB, "Star": 0x1490, "Hurt": 0x1497,
    "Flash": 0x149B, "ImgY": 0x188B, "Yoshi": 0x18E2,
}


def pick(rng, *vals, p=0.5):
    return rng.choice(vals) if rng.random() < p else rng.randrange(256)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    rng = random.Random(seed)
    syms = mv.symbols(os.path.join(WORK, "logicbench.lst"))
    code = open(os.path.join(WORK, "logicbench.bin"), "rb").read()
    cpu = mv.MusashiCPU()
    cpu.write(mv.BASE, code)
    RAM = mv.BASE + syms["_ram"]
    ext68 = {k: mv.BASE + syms["_" + k] for k in ("mario_oam", "mario_osz", "mario_pal",
                                                   "mario_events", "mario_unsupported")}
    lib = ctypes.CDLL(os.path.abspath(os.path.join(WORK, "libport.so")))
    ram = (ctypes.c_ubyte * 0x2000).in_dll(lib, "ram")
    oam = (ctypes.c_ubyte * 16).in_dll(lib, "mario_oam")
    osz = (ctypes.c_ubyte * 4).in_dll(lib, "mario_osz")
    pal = ctypes.c_ubyte.in_dll(lib, "mario_pal")
    ev = ctypes.c_uint.in_dll(lib, "mario_events")
    un = ctypes.c_int.in_dll(lib, "mario_unsupported")
    bad = fall = 0
    cyc = []
    for i in range(n):
        r = bytearray(rng.randbytes(0x2000))
        f = rng.random()
        if f < 0.4:
            r[R["Frame"]] = rng.choice((0x09, 0x0A, 0x13, 0x1C, 0x29, 0x3C, 0x3D, 0x43, 0x45, 0x46, 0x47))
        elif f < 0.93:
            r[R["Frame"]] = rng.randrange(0x46)
        else:
            r[R["Frame"]] = rng.randrange(256)
        r[R["Dir"]] = rng.choice((0, 1)) if rng.random() < 0.95 else rng.randrange(256)
        r[R["PowerUp"]] = rng.choice((0, 1, 3, 0, 1, 3, 2)) if rng.random() < 0.97 else rng.randrange(256)
        r[R["Hide"]] = pick(rng, 0, 0xFF, 1, 2, 4, 8, 0x0F, 0xF0, p=0.7)
        r[R["Yoshi"]] = rng.choice((0, 0, 0, 1, 0xFF))
        r[R["Star"]] = pick(rng, 0, 0, 1, 0x1D, 0x1E, 0x1F, 0x80, p=0.7)
        r[R["Flash"]] = rng.choice((0, 0, 0, 0, 1, 0x20, 0xFF))
        r[R["Hurt"]] = rng.choice((0, 0, 0, 1, 2, 7, 8, 0x20, 0x7F, 0xFF))
        r[R["Locked"]] = rng.choice((0, 0, 1))
        r[R["Frozen"]] = rng.choice((0, 0, 1))
        r[R["Behind"]] = rng.choice((0, 0, 0, 1, 2, 3, 4, 5, 6)) if rng.random() < 0.97 else rng.randrange(256)
        r[R["Wall"]] = pick(rng, 0, 5, 6, 7, 8, p=0.6)
        r[R["Walk"]] = rng.choice((0, 1, 2, 3, 0x0A)) if rng.random() < 0.7 else rng.randrange(256)
        r[R["ImgY"]] = rng.choice((0, 0, 1, 2, 3, 0xFF, 0xFE)) if rng.random() < 0.7 else rng.randrange(256)
        r[R["OWChar"]] = rng.choice((0, 1))
        # posiciones: cerca unas de otras (que haya entradas visibles y recortadas)
        cam = rng.randrange(0x600)
        for name, base in (("Bg1H", cam), ("XPos", cam + rng.randrange(-40, 330))):
            v = (base + (rng.randrange(65536) if rng.random() < 0.05 else 0)) & 0xFFFF
            r[R[name]], r[R[name] + 1] = v & 0xFF, v >> 8
        camy = rng.randrange(0x100)
        for name, base in (("Bg1V", camy), ("YPos", camy + rng.randrange(-40, 260))):
            v = (base + (rng.randrange(65536) if rng.random() < 0.05 else 0)) & 0xFFFF
            r[R[name]], r[R[name] + 1] = v & 0xFF, v >> 8
        o = bytes(rng.randrange(256) for _ in range(16))
        z = bytes(rng.randrange(256) for _ in range(4))
        p = rng.randrange(256)
        e = rng.randrange(1 << 11)
        u = rng.choice((0, 0, 0, 5))
        # 68000
        cpu.write(RAM, bytes(r))
        cpu.write(ext68["mario_oam"], o)
        cpu.write(ext68["mario_osz"], z)
        cpu.write(ext68["mario_pal"], bytes([p]))
        cpu.write(ext68["mario_events"], struct.pack(">I", e))
        cpu.write(ext68["mario_unsupported"], struct.pack(">i", u))
        c = cpu.call(mv.BASE + syms["_mario_E2BD"], mv.BASE)
        a_ram = cpu.read(RAM, 0x2000)
        a_ext = (cpu.read(ext68["mario_oam"], 16), cpu.read(ext68["mario_osz"], 4),
                 cpu.read(ext68["mario_pal"], 1)[0],
                 struct.unpack(">I", cpu.read(ext68["mario_events"], 4))[0],
                 struct.unpack(">i", cpu.read(ext68["mario_unsupported"], 4))[0])
        # C del PC
        ctypes.memmove(ram, bytes(r), 0x2000)
        ctypes.memmove(oam, o, 16)
        ctypes.memmove(osz, z, 4)
        pal.value, ev.value, un.value = p, e, u
        lib.mario_E2BD()
        b_ram = bytes(ram)
        b_ext = (bytes(oam), bytes(osz), pal.value, ev.value, un.value)
        if r[R["PowerUp"]] == 2 or r[R["Frame"]] >= 0x46 or r[R["Dir"]] >= 2:
            fall += 1
        else:
            cyc.append(c)
        if a_ram != b_ram or a_ext != b_ext:
            bad += 1
            if bad <= 8:
                d = ["$%04X=%02X/%02X" % (k, a_ram[k], b_ram[k]) for k in range(0x2000)
                     if a_ram[k] != b_ram[k]][:8]
                names = ("oam", "osz", "pal", "events", "unsup")
                d += ["%s=%s/%s" % (names[k], a_ext[k], b_ext[k]) for k in range(5) if a_ext[k] != b_ext[k]]
                print("caso %d distinto: %s" % (i, " ".join(d)))
                print("  entrada: Frame=%02X Dir=%d PowerUp=%d Hide=%02X Star=%02X Flash=%02X Hurt=%02X"
                      % (r[R["Frame"]], r[R["Dir"]], r[R["PowerUp"]], r[R["Hide"]], r[R["Star"]],
                         r[R["Flash"]], r[R["Hurt"]]))
    print("e2bd_fuzz: %d casos (semilla %d), %d distintos; %d por el camino de respaldo (C)"
          % (n, seed, bad, fall))
    if cyc:
        cyc.sort()
        print("ciclos del asm (sin los casos de respaldo): media %.0f, p99 %d, max %d"
              % (sum(cyc) / len(cyc), cyc[int(len(cyc) * 0.99)], cyc[-1]))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
