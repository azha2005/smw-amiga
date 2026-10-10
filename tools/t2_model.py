#!/usr/bin/env python3
"""t2_model.py - G5L-R-T2: modelo de cola del render desacoplado.

Atraso L_k = max(0, L_{k-1} + T_k - B), con T_k el coste de la foto k en
Musashi (logica + captura + render, sin DMA; work/t2/frames.csv de
t2_attrib.py). Cuando L supera la holgura S (el colchon), el VBL repite y
una foto se saltea: su render no se hace (L -= T de la siguiente). B y S
se ajustan para reproducir los saltos de VBTRACE; con ese ajuste se cuentan
saltos en contrafacticos (partes recortadas). ESTIMADO: no es la Amiga.

    python tools/t2_model.py --csv work/t2/frames.csv --vblog work/t2/vt/vbtrace.out
"""
import argparse
import csv
import re


def simulate(T, B, S):
    L, ev, skip = 0, [], False
    for k, t in enumerate(T):
        if skip:
            skip = False
            continue
        L = max(0, L + t - B)
        if L > S:
            ev.append(k)
            L = max(0, L - B)
            skip = True
    return ev


def score(ev, want, tol=4):
    hit = sum(1 for w in want if any(abs(e - w) <= tol for e in ev))
    return hit, len(ev)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', required=True)
    ap.add_argument('--vblog', required=True)
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv)))
    for r in rows:
        for c in r:
            r[c] = int(r[c])
    text = open(a.vblog).read()
    want = [int(x) for x in re.search(r'salteadas: \d+ \[(.*?)\]', text).group(1).split(',')]
    T = [r['total'] for r in rows]
    best = None
    for B in range(80000, 140001, 1000):
        for S in range(20000, 160001, 5000):
            ev = simulate(T, B, S)
            hit, n = score(ev, want)
            key = (hit - abs(n - len(want)), hit)
            if best is None or key > best[0]:
                best = (key, B, S, ev)
    (_, hit), B, S, ev = best[0], best[1], best[2], best[3]
    print('ajuste: B = %d ciclos/foto, S = %d; %d saltos del modelo, %d de %d reales a +-4 frames'
          % (B, S, len(ev), hit, len(want)))
    print('modelo:', ev)

    med = {}
    for c in rows[0]:
        v = sorted(r[c] for r in rows[1:])
        med[c] = v[len(v) // 2]
    g5parts = ('g5l_fast', 'g5l_sweep', 'g5l_plan', 'g5l_patch', 'g5l_mfill', 'g5l_place', 'g5l_emit')

    def cf(name, fn):
        T2 = [fn(r) for r in rows]
        e = simulate(T2, B, S)
        print('%-52s %3d saltos (base %d)' % (name, len(e), len(ev)))

    def cap(r, parts, lim=None):
        return r['total'] - sum(max(0, r[p] - (med[p] if lim is None else lim)) for p in parts)
    cf('build_mid a su mediana', lambda r: cap(r, ('build_mid',)))
    cf('build_mid <= 20000', lambda r: cap(r, ('build_mid',), 20000))
    cf('build_mid <= 40000', lambda r: cap(r, ('build_mid',), 40000))
    cf('plan G5L (fast..emit) a su mediana', lambda r: cap(r, g5parts))
    cf('g5l_mfill a su mediana (cache de Mario)', lambda r: cap(r, ('g5l_mfill',)))
    cf('g5l_patch a su mediana', lambda r: cap(r, ('g5l_patch',)))
    cf('g5l_sweep+g5l_plan a su mediana (fast sin fallo)', lambda r: cap(r, ('g5l_sweep', 'g5l_plan')))
    cf('logica a su mediana', lambda r: cap(r, ('logic',)))
    cf('build_mid + plan G5L a su mediana', lambda r: cap(r, ('build_mid',) + g5parts))
    for pct in (5, 10, 15, 20):
        cf('todo el render -%d %%' % pct, lambda r, p=pct: r['total'] - r['render_tot'] * p // 100)
        cf('g5l_render -%d %%' % pct, lambda r, p=pct: r['total'] - r['g5'] * p // 100)


if __name__ == '__main__':
    main()
