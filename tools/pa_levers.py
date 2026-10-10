#!/usr/bin/env python3
"""pa_levers.py - G5L-R-Pa: reparto del coste de los fallos y palancas.

Entrada: work/t2/frames.json (`g5l.py game`: partes G5L, plan, s) y
work/t2/frames.csv (`t2_attrib.py`). Imprime el coste por parte en las
fotos de fallo (g5l_sweep) contra las dibujadas sin fallo, `build_mid` por
sentido de la cámara (ds de la s) y los saltos del modelo de cola
(t2_model.py, cinco mejores ajustes) para recortes del camino lento en asm,
de `build_mid` y de `g5l_render`. ESTIMADO: el modelo no es la Amiga.

    python tools/pa_levers.py --frames work/t2/frames.json --csv work/t2/frames.csv
"""
import argparse
import csv
import json
import statistics

from t2_keys import FITS
from t2_model import simulate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', required=True)
    ap.add_argument('--csv', required=True)
    a = ap.parse_args()
    fr = json.load(open(a.frames))
    rows = [{c: int(v) for c, v in r.items()} for r in csv.DictReader(open(a.csv))]
    m = [x for x in fr[1:] if x['parts'].get('g5l_sweep', 0) > 0]
    h = [x for x in fr[1:] if 'g5l_place' in x['parts'] and x['parts'].get('g5l_sweep', 0) == 0]
    mk = set(x['k'] for x in m)
    tot = statistics.mean(x['c'] for x in m)
    hit = statistics.mean(x['c'] for x in h)
    print('g5l_render: fallo %d (%d fotos), dibujada sin fallo %d (%d fotos)' % (tot, len(m), hit, len(h)))
    parts = sorted({p for x in m for p in x['parts']}, key=lambda p: -sum(x['parts'].get(p, 0) for x in m))
    print('%-12s %8s %8s %7s | %8s' % ('parte', 'media F', 'max F', '% F', 'media A'))
    pm = {}
    for p in parts:
        v = [x['parts'].get(p, 0) for x in m]
        pm[p] = statistics.mean(x['parts'].get(p, 0) for x in h)
        print('%-12s %8d %8d %6.1f%% | %8d' % (p, statistics.mean(v), max(v), 100 * statistics.mean(v) / tot, pm[p]))

    ds = {x['k']: (x['sc'] - fr[i - 1]['sc']) if i > 1 else 0 for i, x in enumerate(fr)}
    med = sorted(r['build_mid'] for r in rows[1:])[len(rows) // 2]
    ex = lambda r: max(0, r['build_mid'] - med)
    allex = sum(ex(r) for r in rows[1:])
    print('\nbuild_mid por sentido (mediana %d):' % med)
    for name, cond in (('izquierda', lambda d: d < 0), ('derecha', lambda d: d > 0), ('quieta', lambda d: d == 0)):
        sel = [r for r in rows[1:] if cond(ds[r['k']])]
        big = sum(1 for r in sel if r['build_mid'] > 40000)
        print('  %-9s %4d fotos, exceso %3.0f %%, max %6d, > 40000: %d' % (
            name, len(sel), 100 * sum(ex(r) for r in sel) / allex, max(r['build_mid'] for r in sel), big))
    right = sorted(r['build_mid'] for r in rows[1:] if ds[r['k']] > 0)
    capR = right[int(.99 * len(right))]

    print('\nsaltos del modelo con los 5 mejores ajustes (B/S: %s)' % ' '.join('%dk/%dk' % (b // 1000, s // 1000) for b, s in FITS))

    def run(name, fn):
        print('  %-60s %s' % (name, ' '.join('%2d' % len(simulate([fn(r) for r in rows], B, S)) for B, S in FITS)))
    sp = lambda r, f: int(f * (r['g5l_sweep'] + r['g5l_plan'])) if r['k'] in mk else 0
    spp = lambda r, f: int(f * (r['g5l_sweep'] + r['g5l_plan'] + max(0, r['g5l_patch'] - pm['g5l_patch']))) if r['k'] in mk else 0
    bm = lambda r, f: int(f * ex(r))
    left = lambda r: max(0, r['build_mid'] - capR) if ds[r['k']] < 0 else 0
    run('base', lambda r: r['total'])
    for f in (.3, .5):
        run('sweep+plan -%d %% en los fallos' % (f * 100), lambda r, f=f: r['total'] - sp(r, f))
        run('sweep+plan+exceso de patch -%d %%' % (f * 100), lambda r, f=f: r['total'] - spp(r, f))
        run('sweep+plan+exceso de patch -%d %% + S5 50 %%' % (f * 100), lambda r, f=f: r['total'] - spp(r, f) - bm(r, .5))
    run('cota: el fallo cuesta como una dibujada sin fallo', lambda r: r['total'] - (max(0, r['g5'] - int(hit)) if r['k'] in mk else 0))
    run('cota + S5 50 %', lambda r: r['total'] - (max(0, r['g5'] - int(hit)) if r['k'] in mk else 0) - bm(r, .5))
    run('vuelta: build_mid <= p99 de la ida (%d) (S6)' % capR, lambda r: r['total'] - left(r))
    run('S6 + sweep+plan+exceso de patch -50 %', lambda r: r['total'] - left(r) - spp(r, .5))
    run('S6 + g5l_render -20 %', lambda r: r['total'] - left(r) - r['g5'] // 5)
    for f in (10, 20, 30):
        run('g5l_render -%d %% en todas' % f, lambda r, f=f: r['total'] - r['g5'] * f // 100)
        run('g5l_render -%d %% + S5 50 %%' % f, lambda r, f=f: r['total'] - r['g5'] * f // 100 - bm(r, .5))


if __name__ == '__main__':
    main()
