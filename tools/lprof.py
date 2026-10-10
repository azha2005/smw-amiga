#!/usr/bin/env python3
"""Perfil por etiqueta de un json de g5l.py --pcprof (L3, 2026-10-10).

Asigna cada PC a la ultima etiqueta de codigo anterior: incluye las lineas
de macro del listado (1M, 1R: sin ":") y las etiquetas de vbcc (sin ":").

    python tools/lprof.py PERFIL.json game.lst N [logic|build_mid|render] [FUNCION]
"""
import json, re, sys, collections
lst = sys.argv[2]
rows = []
pend = None
for l in open(lst, encoding='latin1'):
    m = re.match(r'00:([0-9A-F]{8}) \S*\s+\t\s*(\d+)(?:: |[MR] )(.*)', l)
    if m:
        t = m.group(3).rstrip()
        if pend and not re.match(r'^[_A-Za-z]\w*:', t):
            t = pend + ': ' + t
        pend = None
        rows.append((int(m.group(1), 16), t))
        continue
    m = re.match(r'^\s+\t\s*\d+: ([_A-Za-z]\w*):', l) or re.match(r'^\s+\t\s*\d+: (_\w+)\s*$', l)
    if m:
        pend = m.group(1)
cur = '?'
lab = {}
for a, t in rows:
    m = re.match(r'^([_A-Za-z]\w*):', t)
    if m and not re.search(r'\b(dc|ds|dcb|rept|incbin)\b', t, re.I):
        cur = m.group(1)
    lab.setdefault(a, cur)
d = json.load(open(sys.argv[1]))
key = sys.argv[4] if len(sys.argv) > 4 else 'logic'
c = collections.Counter()
for k, h in d[key].items():
    for pc, (n, cy) in h.items():
        c[lab.get(int(pc, 16), '?')] += cy
T = sum(c.values())
print('total', T, 'fotos', len(d[key]))
for f, v in c.most_common(int(sys.argv[3])):
    print('%9d %5.1f%%  %s' % (v, 100 * v / T, f))
if len(sys.argv) > 5:
    fn = sys.argv[5]
    rows_d = {}
    for a, t in rows:
        rows_d.setdefault(a, t)
    byl = collections.Counter(); cnt = collections.Counter()
    for k, h in d[key].items():
        for pc, (n, cy) in h.items():
            a = int(pc, 16)
            if lab.get(a) == fn:
                byl[a] += cy; cnt[a] += n
    nf = len(d[key])
    for a in sorted(byl):
        print('%6x %7d %6d %s' % (a, byl[a], cnt[a], rows_d[a][:80]))
