#!/usr/bin/env python3
"""t2_attrib.py - G5L-R-T2: atribuir los saltos de VBTRACE al coste por foto.

Entrada: work/g5l/game_frames.json de `g5l.py game` (Musashi, ciclos sin
DMA, por foto: logica de la interrupcion, captura, columns/apply_colors/
set_pointers/build_mid y las partes de g5l_render) y la lista de VBL que
repiten / fotos salteadas de `vbtrace.py` (frames del replay = R_FRAME).

    python tools/t2_attrib.py --frames work/t2/frames.json --vblog work/t2/vt/vbtrace.out \
        --csv work/t2/frames.csv

Escribe el CSV por foto y, por salto, la ventana [repeticion-2, salto]:
el coste total (logica + captura + render) de cada foto, la parte que mas
sube sobre su mediana y si pasa el umbral. Musashi no es la Amiga: las
cifras sirven para ordenar y atribuir, no como tiempo real.
"""
import argparse
import json
import re
import statistics

PRE = ('columns', 'apply_colors', 'set_pointers', 'build_mid')
G5 = ('g5l_clean', 'g5l_mario', 'g5l_mfill', 'g5l_choose', 'g5l_plan', 'g5l_fast', 'g5l_need',
      'g5l_mrow', 'g5l_mwall', 'g5l_mrowba', 'g5l_mba', 'g5l_sweep', 'g5l_patch', 'g5l_place',
      'g5l_emit', 'g5l_vblnull', 'render')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', required=True)
    ap.add_argument('--vblog', required=True, help='salida de vbtrace.py')
    ap.add_argument('--csv', required=True)
    a = ap.parse_args()
    fr = json.load(open(a.frames))
    first = fr[1]['f'] - fr[1]['k']
    assert all(x['f'] - x['k'] == first for x in fr[1:]), 'R_FRAME no sigue a k'
    text = open(a.vblog, encoding='utf-8', errors='replace').read()
    rep = [int(x) for x in re.search(r'repiten.*?\[(.*?)\]', text).group(1).split(',')]
    sk = [int(x) for x in re.search(r'salteadas: \d+ \[(.*?)\]', text).group(1).split(',')]
    rep = [r for r in rep if r]                          # el 0 es el arranque

    cols = ['k', 'frame', 'logic', 'cap'] + list(PRE) + list(G5) + ['g5', 'render_tot', 'total']
    rows = []
    for x in fr:
        r = dict(k=x['k'], frame=x['f'], logic=x.get('logic', 0), cap=x.get('cap', 0))
        r.update({n: x['pre'][n] for n in PRE})
        r.update({n: x['parts'].get(n, 0) for n in G5})
        r['g5'] = x['c']
        r['render_tot'] = sum(x['pre'][n] for n in PRE) + x['c']
        r['total'] = r['render_tot'] + r['logic'] + r['cap']
        rows.append(r)
    with open(a.csv, 'w') as fh:
        fh.write(','.join(cols) + '\n')
        for r in rows:
            fh.write(','.join(str(r[c]) for c in cols) + '\n')

    med = {c: statistics.median(r[c] for r in rows[1:]) for c in cols[2:]}
    print('fotos %d, origen %d; media g5l_render %.1f, max %d' % (
        len(rows), first, sum(r['g5'] for r in rows) / len(rows), max(r['g5'] for r in rows)))
    print('medianas: ' + ', '.join('%s %d' % (c, med[c]) for c in ('logic', 'cap', 'build_mid', 'g5', 'render_tot', 'total')))
    tot = sorted(r['total'] for r in rows[1:])
    p = lambda q: tot[int(q * (len(tot) - 1))]
    print('total por foto: p50 %d, p90 %d, p99 %d, max %d' % (p(.5), p(.9), p(.99), tot[-1]))

    by_k = {r['k']: r for r in rows}
    windows = []
    for s in sk:
        r0 = max([r for r in rep if r <= s] or [s])
        ks = list(range(r0 - 2, s + 1))
        win = [by_k[k] for k in ks if k in by_k]
        windows.append((s, r0, win))
    print('\nsalto  rep   fotos(total/1000) ... | lo que mas sube (x mediana) en la foto mas cara')
    causes = {}
    for s, r0, win in windows:
        worst = max(win, key=lambda r: r['total'])
        ups = sorted(((worst[c] - med[c], c) for c in ('logic', 'cap') + PRE + G5[:-1]), reverse=True)
        top = [c for d, c in ups[:2] if d > 0]
        causes[s] = top
        print('%5d %5d  %s | %s' % (s, r0, ' '.join('%d:%d' % (r['k'], r['total'] // 1000) for r in win),
                                    ', '.join('%s +%d' % (c, worst[c] - med[c]) for c in top)))
    agg = {}
    for top in causes.values():
        for c in top[:1]:
            agg[c] = agg.get(c, 0) + 1
    print('\nprimera causa por salto:', json.dumps(dict(sorted(agg.items(), key=lambda x: -x[1]))))
    near = set()
    for s, r0, win in windows:
        near.update(r['k'] for r in win)
    for thr in (p(.9), p(.95), p(.98), p(.99)):
        hot = [r['k'] for r in rows[1:] if r['total'] >= thr]
        hit = sum(1 for k in hot if k in near)
        cover = sum(1 for s, r0, win in windows if any(r['total'] >= thr for r in win))
        print('umbral %6d: %4d fotos calientes, %3d dentro de ventanas de salto; ventanas con alguna: %d/%d'
              % (thr, len(hot), hit, cover, len(windows)))


if __name__ == '__main__':
    main()
