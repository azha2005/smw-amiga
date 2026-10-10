#!/usr/bin/env python3
"""L-DER: el primer frame en que la RAM de una ranura de sprite del port se
separa de la SNES.

El oráculo de los replays compara `dp` y `$13C0-$14FF`; las tablas de
sprites desde `$1500` (temporizadores, dirección, contacto con bloques,
frame de animación...) no las mira nadie, y una diferencia ahí pasa el
oráculo y aparece después como una posición o una pose distinta (G9).

Corre el juego en Musashi como `sprshot_cmp.py --logic` (GameRun), toma la
WRAM del port (`_ram`, misma disposición que la SNES) después de cada
frame lógico y la compara, ranura por ranura, contra la RAM de la traza
`oamb` DESPUÉS del despacho de esa ranura (la segunda mitad del registro
SOT1). Un sprite que se procesa más tarde en el mismo frame puede tocar
la ranura (contactos): por eso se informa el primer frame y los campos,
y se mira a mano.

    python tools/lder.py --bin B/game.bin --lst B/game.lst --trace yi1 \
        [--slot 7] [--from 7500] [--to 7700] [--show 20]
"""
import argparse
import collections
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# tablas de 12 ranuras (sprite_1-main.s / ram_map.txt); nombre corto
TABLES = [
    (0x009E, 'num'), (0x00AA, 'vy'), (0x00B6, 'vx'), (0x00C2, 'c2'),
    (0x00D8, 'ylo'), (0x00E4, 'xlo'), (0x14C8, 'estado'), (0x14D4, 'yhi'),
    (0x14E0, 'xhi'), (0x14EC, 'ysub'), (0x14F8, 'xsub'), (0x1504, '1504'),
    (0x1510, '1510'), (0x151C, '151C'), (0x1528, '1528'), (0x1534, '1534'),
    (0x1540, 't1540'), (0x154C, 't154C'), (0x1558, 't1558'), (0x1564, 't1564'),
    (0x1570, '1570'), (0x157C, 'dir'), (0x1588, 'bloq'), (0x1594, '1594'),
    (0x15A0, 'fuera'), (0x15AC, 't15AC'), (0x15B8, 'pend'), (0x15C4, 'fuera2'),
    (0x15D0, '15D0'), (0x15DC, '15DC'), (0x15EA, 'oam'), (0x15F6, 'prop'),
    (0x1602, 'frame'), (0x160E, '160E'), (0x161A, 'carga'), (0x1626, '1626'),
    (0x1632, 'capa'), (0x163E, 't163E'), (0x164A, 'agua'), (0x1656, 'tw1656'),
    (0x1662, 'tw1662'), (0x166E, 'tw166E'), (0x167A, 'tw167A'), (0x1686, 'tw1686'),
    (0x186C, 'fueraV'), (0x187B, '187B'), (0x190F, 'tw190F'), (0x1FD6, '1FD6'),
    (0x1FE2, 't1FE2'),
]
# lo que el oráculo ya compara (dp y $13C0-$14FF): se informa igual, marcado
ORACLE = {a for a, _ in TABLES if a < 0x100 or 0x13C0 <= a < 0x1500}
ADDR = {name: a for a, name in TABLES}


def slot_fields(ram, slot):
    return {name: ram[a + slot] for a, name in TABLES}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bin', required=True)
    ap.add_argument('--lst', required=True)
    ap.add_argument('--trace', required=True, help='work/oamb_<traza>.trace')
    ap.add_argument('--bank', default='work/g3/bank')
    ap.add_argument('--slot', type=int, default=None)
    ap.add_argument('--from', dest='f0', type=int, default=0)
    ap.add_argument('--to', dest='f1', type=int, default=10 ** 9)
    ap.add_argument('--show', type=int, default=12, help='primeros casos por ranura')
    ap.add_argument('--ignore', default='', help='campos a no comparar (coma)')
    ap.add_argument('--out', default=None)
    ap.add_argument('--key', choices=('f', 'f1', 'mejor'), default='mejor',
                    help='frame del port contra el del despacho: f, f + 1 o el que menos difiera')
    a = ap.parse_args()
    import g5l as L
    import g5ref as R
    ignore = set(x for x in a.ignore.split(',') if x)
    gr = L.GameRun(a.bin, a.lst, a.bank)
    G, s, mem, fr, addr = gr.G, gr.s, gr.mem, gr.fr, gr.addr
    ram_at = addr('_ram')
    # snapshot de la WRAM del port por frame lógico
    port = {}
    for k in range(gr.n):
        if k:
            fr.call(addr('dc_cop'), G.FAKE)
        f = gr.first + mem.r16(gr.dc + s['DC_NLOG'])
        if a.f0 - 1 <= f <= a.f1 + 1:
            port[f] = bytes(gr.cpu.read(ram_at, 0x2000))
        if f > a.f1 + 1:
            break
    trace = R.read_trace('work/oamb_%s.trace' % a.trace, 'work/oracle_%s_oam.bin' % a.trace)
    first = {}                                     # ranura -> primer caso
    cases = collections.defaultdict(list)
    seen = collections.Counter()
    for d in trace:
        f, slot = d['frame'], d['slot']
        if f < a.f0 or f > a.f1 or (a.slot is not None and slot != a.slot):
            continue
        # el port captura después del frame f: la clave es f + 1 si el
        # contador ya avanzó (se prueban las dos y se usa la que coincide
        # en x/y de la ranura; si ninguna, f + 1)
        sr = slot_fields(d['ram'], slot)
        best = None
        for key in {'f': (f,), 'f1': (f + 1,), 'mejor': (f + 1, f)}[a.key]:
            if key not in port:
                continue
            pr = slot_fields(port[key], slot)
            diff = {n: (sr[n], pr[n]) for n in sr if sr[n] != pr[n] and n not in ignore}
            if best is None or len(diff) < len(best[1]):
                best = (key, diff)
        if best is None:
            continue
        seen[slot] += 1
        key, diff = best
        if diff:
            c = dict(frame=f, port_key=key, num='%02X' % d['num'],
                     campos={n: ['%02X' % v for v in diff[n]] for n in diff},
                     solo_fuera_del_oraculo=all(ADDR[n] not in ORACLE for n in diff))
            cases[slot].append(c)
            first.setdefault(slot, c)
    for slot in sorted(seen):
        n = len(cases[slot])
        print('ranura %2d: %5d despachos, %5d con diferencias' % (slot, seen[slot], n))
        for c in cases[slot][:a.show]:
            print('   f %5d (%s) %s%s' % (c['frame'], c['num'],
                  ' '.join('%s=%s/%s' % (k, v[0], v[1]) for k, v in sorted(c['campos'].items())),
                  '' if c['solo_fuera_del_oraculo'] else '  [oraculo]'))
    if a.out:
        Path(a.out).write_text(json.dumps(dict(primero=first, casos=cases), indent=1), encoding='utf-8')
    print('LDER: %s' % ('sin diferencias' if not first else '%d ranuras con diferencias' % len(first)))


if __name__ == '__main__':
    main()
