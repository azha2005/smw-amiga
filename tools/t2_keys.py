#!/usr/bin/env python3
"""t2_keys.py - G5L-R-T2: por que falla la cache del plan de G5L y que daria.

Entrada: work/t2/frames.json (`g5l.py game`, con la clave GV_PK por foto) y
work/t2/frames.csv (`t2_attrib.py`). Un fallo es una foto con g5l_sweep.
Dice que campo de la clave cambio respecto de la foto anterior, cuantos
fallos acertarian con una cache FIFO de N entradas (como g5l_pcput) con la
clave real o sin algunos campos, y los saltos del modelo de cola
(t2_model.py) en combinaciones de recortes. ESTIMADO: el modelo no es la
Amiga, y quitar un campo de la clave solo vale si el plan no depende de el.

    python tools/t2_keys.py --frames work/t2/frames.json --csv work/t2/frames.csv
"""
import argparse
import collections
import csv
import json

from t2_model import simulate

F = {'pose': (0, 26), 'ptrs': (26, 52), 'R0': (52, 54), 'MSH': (54, 56), 'COL': (56, 60), 'VLIST': (60, 64)}
FITS = [(102000, 65000), (103000, 60000), (105000, 50000), (100000, 80000), (96000, 105000)]
SLOW = ('g5l_sweep', 'g5l_plan', 'g5l_fast', 'g5l_need')


def red(pk, drop):
    b = bytearray.fromhex(pk)
    for n in drop:
        i, j = F[n]
        b[i:j] = bytes(j - i)
    return bytes(b)


def fifo_hits(drawn, drop, n):
    cache, hits = [], set()
    for x in drawn:
        key = red(x['pk'], drop)
        miss = x['parts'].get('g5l_sweep', 0) > 0
        if key in cache:
            if miss:
                hits.add(x['k'])
            continue
        if miss:
            cache.append(key)
            if len(cache) > n:
                cache.pop(0)
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', required=True)
    ap.add_argument('--csv', required=True)
    a = ap.parse_args()
    fr = json.load(open(a.frames))
    rows = [{c: int(v) for c, v in r.items()} for r in csv.DictReader(open(a.csv))]
    miss = [x for x in fr[1:] if x['parts'].get('g5l_sweep', 0) > 0]
    mk = set(x['k'] for x in miss)
    prev = {x['k']: fr[i - 1] for i, x in enumerate(fr) if i}
    combos, cnt = collections.Counter(), collections.Counter()
    for x in miss:
        p, q = bytes.fromhex(x['pk']), bytes.fromhex(prev[x['k']]['pk'])
        d = tuple(n for n, (i, j) in F.items() if p[i:j] != q[i:j])
        combos[d] += 1
        cnt.update(d)
    print('fallos %d; campo distinto de la foto anterior: %s' % (len(miss), dict(cnt)))
    for d, n in combos.most_common():
        print('  %3d  %s' % (n, '+'.join(d) or '(igual)'))
    drawn = [x for x in fr[1:] if 'g5l_place' in x['parts']]
    print('\nfallos que acertarian con una FIFO de N (la real: N = 4 y la clave entera)')
    for drop in ((), ('R0', 'MSH'), ('R0', 'MSH', 'ptrs')):
        print('  sin %-13s %s' % ('+'.join(drop) or '-', '  '.join(
            'N=%d: %3d' % (n, len(fifo_hits(drawn, drop, n))) for n in (4, 8, 16, 10 ** 6))))

    med = {c: sorted(r[c] for r in rows[1:])[len(rows) // 2] for c in rows[0]}
    slow = lambda r: sum(r[p] for p in ('g5l_sweep', 'g5l_plan')) if r['k'] in mk else 0
    bm = lambda r, f: int(f * max(0, r['build_mid'] - med['build_mid']))
    g5 = lambda r, f: int(f * r['g5'])
    patch = lambda r: max(0, r['g5l_patch'] - med['g5l_patch'])
    print('\nsaltos del modelo con los 5 mejores ajustes (B/S: %s)' % ' '.join('%dk/%dk' % (b // 1000, s // 1000) for b, s in FITS))

    def run(name, fn):
        print('  %-56s %s' % (name, ' '.join('%2d' % len(simulate([fn(r) for r in rows], B, S)) for B, S in FITS)))
    run('base', lambda r: r['total'])
    for drop, n in ((('R0', 'MSH'), 4), (('R0', 'MSH'), 16), (('R0', 'MSH', 'ptrs'), 4)):
        h = fifo_hits(drawn, drop, n)
        run('aciertos sin %s, N=%d (%d)' % ('+'.join(drop), n, len(h)),
            lambda r, h=h: r['total'] - (sum(r[p] for p in SLOW) if r['k'] in h else 0))
    run('A: sweep+plan gratis en los fallos', lambda r: r['total'] - slow(r))
    run('A/2: sweep+plan+patch+mfill -50 % en los fallos', lambda r: r['total'] - (int(.5 * sum(
        r[p] for p in ('g5l_sweep', 'g5l_plan', 'g5l_patch', 'g5l_mfill'))) if r['k'] in mk else 0))
    run('B: build_mid -50 % del exceso (S5)', lambda r: r['total'] - bm(r, .5))
    run('B: build_mid -75 % del exceso', lambda r: r['total'] - bm(r, .75))
    run('A+B', lambda r: r['total'] - slow(r) - bm(r, .5))
    run('A+B + patch a su mediana', lambda r: r['total'] - slow(r) - bm(r, .5) - patch(r))
    run('A+B + resto de g5l_render -10 %', lambda r: r['total'] - slow(r) - bm(r, .5) - int(.1 * (r['g5'] - slow(r))))
    run('C: g5l_render -20 %', lambda r: r['total'] - g5(r, .2))
    run('C: g5l_render -30 %', lambda r: r['total'] - g5(r, .3))
    run('B+C: build_mid -50 % y g5l_render -20 %', lambda r: r['total'] - bm(r, .5) - g5(r, .2))
    run('B+C: build_mid -50 % y g5l_render -30 %', lambda r: r['total'] - bm(r, .5) - g5(r, .3))


if __name__ == '__main__':
    main()
