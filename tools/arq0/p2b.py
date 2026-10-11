# ARQ-0 (docs/informe-arq-0-1011.md): P2(b): fusion de colores de la capa 1 contra intervalos de carga
# correr desde la raiz: python tools/arq0/p2b.py
import sys, collections
sys.path.insert(0, 'tools')
import numpy as np
import render_d as R
import arq_diff as A
d = R.load('work/yi1_d.dat'); W, H = d['W'], d['H']
idx = R.l1_index(d)
def rgb(c): return ((c >> 8 & 15) * 17, (c >> 4 & 15) * 17, (c & 15) * 17)
rowscol = []
cnt = collections.Counter()
for y in range(H):
    lc = R.reg_colors(d['events'][y], W)
    i1 = idx[y]
    col = np.where(i1 > 0, lc[i1, np.arange(W)], -1)
    rowscol.append(col)
    u, n = np.unique(col[col >= 0], return_counts=True)
    for a, b in zip(u, n): cnt[int(a)] += int(b)
nev = sum(len(e) for e in d['events'])
print('filas', H, 'ancho', W, 'eventos (hoy)', nev, 'colores de capa 1', len(cnt))
GAP = 48
def intervals(col, remap):
    c = col[col >= 0]
    xs = np.nonzero(col >= 0)[0]
    by = collections.defaultdict(list)
    for x, v in zip(xs, c): by[remap[int(v)]].append(int(x))
    n = 0
    for v, l in by.items():
        n += 1 + sum(1 for a, b in zip(l, l[1:]) if b - a > GAP)
    return n
def clusters(T):
    reps = []; remap = {}
    for c, _ in cnt.most_common():
        for r in reps:
            if A.de(rgb(c), rgb(r)) < T: remap[c] = r; break
        else:
            reps.append(c); remap[c] = c
    return remap, len(reps)
for T in (0, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0, 12.0, 20.0):
    remap, nrep = clusters(T) if T else ({c: c for c in cnt}, len(cnt))
    tot = 0; over = 0; worst = 0
    for y in range(H):
        n = intervals(rowscol[y], remap)
        tot += n; over += max(0, n - 7); worst = max(worst, n)
    moved = sum(n for c, n in cnt.items() if remap[c] != c)
    print('dE<%.1f: %2d colores; intervalos de color por fila: total %d, por encima de 7: %d, peor fila %d; px recoloreados %d (%.2f %%)'
          % (T, nrep, tot, over, worst, moved, 100 * moved / sum(cnt.values())))
