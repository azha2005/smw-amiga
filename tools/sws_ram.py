#!/usr/bin/env python3
"""SW-S: la RAM de los tres motores de efectos (puntos, humo, sprites
extendidos menores) por frame, de `snesorc --ram ... --ram-out`.

    python tools/sws_ram.py stats work/sws/ram_yi1.bin
    python tools/sws_ram.py show work/sws/ram_yi1.bin --from 7540 --to 7560

El volcado (orc.c, `step`): "RAM1", u32 n, n x (u32 inicio, u32 fin), y por
frame u32 etiqueta (el frame de la grabación con --replay) + los rangos
concatenados. Se toma después del frame entero (NMI incluido): estos
motores no se tocan en el NMI.
"""
import argparse
import collections
import struct
import sys

# rangos con que se graba (work/sws_ram.sh)
RANGES = '0F34:0F3A,1697:1698,16E1:170B,17C0:17D0,17F0:185C,1863:1864,18E9:18F8'

SCORE = [('num', 0x16E1), ('ylo', 0x16E7), ('xlo', 0x16ED), ('xhi', 0x16F3),
         ('yhi', 0x16F9), ('vy', 0x16FF), ('capa', 0x1705)]
SMOKE = [('num', 0x17C0), ('y', 0x17C4), ('x', 0x17C8), ('t', 0x17CC)]
MEX = [('num', 0x17F0), ('ylo', 0x17FC), ('xlo', 0x1808), ('yhi', 0x1814),
       ('vy', 0x1820), ('vx', 0x182C), ('yacc', 0x1838), ('t', 0x1850),
       ('xhi', 0x18EA)]
ENGINES = (('puntos', SCORE, 6), ('humo', SMOKE, 4), ('menores', MEX, 12))
GLOBALS = [('ScoreSprIndex', 0x18F7), ('SmokeSprIndex', 0x1863),
           ('OldSmokeIndex', 0x18E9), ('cadena', 0x1697)]


class Frame:
    """bytes por dirección absoluta de WRAM ($0000-$1FFF)"""

    def __init__(self, label, mem):
        self.label = label
        self.mem = mem

    def __getitem__(self, adr):
        return self.mem[adr]

    def engine(self, fields, n):
        return [{k: self.mem[a + i] for k, a in fields} for i in range(n)]

    def score(self):
        return sum(self.mem[0x0F34 + i] << (8 * i) for i in range(3))


def read(path):
    d = open(path, 'rb').read()
    if d[:4] != b'RAM1':
        sys.exit('%s: no es un volcado RAM1' % path)
    n, = struct.unpack_from('<I', d, 4)
    rng = [struct.unpack_from('<II', d, 8 + 8 * i) for i in range(n)]
    o = 8 + 8 * n
    size = sum(hi - lo for lo, hi in rng)
    frames = []
    while o + 4 + size <= len(d):
        label, = struct.unpack_from('<I', d, o)
        o += 4
        mem = {}
        for lo, hi in rng:
            for a in range(lo, hi):
                mem[a] = d[o]
                o += 1
        frames.append(Frame(label, mem))
    return rng, frames


def by_label(frames):
    """el primer volcado de cada etiqueta: con --replay, al terminar el tramo
    snesorc vuelve a etiquetar con su propio contador de frames, que puede
    repetir una etiqueta de la grabación (yi1: el frame 7765)"""
    out = {}
    for f in frames:
        out.setdefault(f.label, f)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('stats', 'show'))
    ap.add_argument('ram')
    ap.add_argument('--from', dest='f0', type=int, default=0)
    ap.add_argument('--to', dest='f1', type=int, default=10 ** 9)
    a = ap.parse_args()
    _, frames = read(a.ram)
    fl = by_label(frames)
    if a.cmd == 'stats':
        act = collections.Counter()
        kinds = {e: collections.Counter() for e, _, _ in ENGINES}
        for lab, f in sorted(fl.items()):
            if not a.f0 <= lab <= a.f1:
                continue
            for e, fields, n in ENGINES:
                nums = [s['num'] for s in f.engine(fields, n) if s['num']]
                if nums:
                    act[e] += 1
                    kinds[e].update(nums)
        print('frames: %d (%d-%d)' % (len(fl), min(fl), max(fl)))
        for e, _, _ in ENGINES:
            print('%-8s activo en %5d frames; numeros %s' % (e, act[e], dict(sorted(kinds[e].items()))))
        return
    for lab, f in sorted(fl.items()):
        if not a.f0 <= lab <= a.f1:
            continue
        parts = ['f %d puntaje %d' % (lab, f.score())]
        for e, fields, n in ENGINES:
            for i, s in enumerate(f.engine(fields, n)):
                if s['num']:
                    parts.append('%s%d{%s}' % (e[0], i, ' '.join('%s=%02X' % kv for kv in s.items())))
        print('  '.join(parts))


if __name__ == '__main__':
    main()
