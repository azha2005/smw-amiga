#!/usr/bin/env python3
"""l_lines.py - G5L-R-L2: las líneas más caras de una función de la lógica.

Entrada: el json de `g5l.py game --pcprof OUT --pclogic RANGOS`, el listado
de vasm y el nombre de la función como lo escribe l_funcs.py (sin el
fichero: `_level_frame`, `mcoll_l590`...). Ciclos por foto (Musashi, sin
DMA), sobre todas las fotos medidas.

    python tools/l_lines.py work/l/prof.json work/s9/replay/game.lst _level_frame [top]
"""
import collections
import json
import sys

from l_funcs import funcs
from q_report import parse_lst


def main():
    q = json.load(open(sys.argv[1]))
    fn = funcs(sys.argv[2])
    lst = parse_lst(sys.argv[2])
    want = sys.argv[3]
    top = int(sys.argv[4]) if len(sys.argv) > 4 else 25
    ks = list(q['logic'])
    c, n = collections.Counter(), collections.Counter()
    for k in ks:
        for off, (nn, cy) in q['logic'][k].items():
            o = int(off, 16)
            if fn.get(o, '?').split(':')[-1] != want:
                continue
            _, _, where, text = lst.get(o, ('?', '', '?', '?'))
            c[where, '%x' % o, text] += cy
            n[where, '%x' % o, text] += nn
    tot = sum(c.values())
    print('%s: %d ciclos por foto en %d fotos' % (want, tot // len(ks), len(ks)))
    for key, v in sorted(c.items(), key=lambda kv: -kv[1])[:top]:
        print('  %-20s %6s %-40s %6.1f veces %6d/foto %5.1f%%' % (key[0], key[1], key[2][:40], n[key] / len(ks),
                                                                 v // len(ks), 100 * v / max(1, tot)))


if __name__ == '__main__':
    main()
