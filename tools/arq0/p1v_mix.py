# ARQ-0 P1-V2: mezcla por fila de 6 planos (hoy), 5 planos con paleta fija
# (p1v_rows.py) y 5 planos con cortes anclados (p1v_pareto.py --rows).
# Ganancia de una fila de 5 planos: 17 palabras de DMA por linea (el plano 6)
# menos las palabras de copper que gasta. Cada cambio de modo entre filas
# cuesta ~10 palabras (BPLCON0 + reponer colores). Barrido de mu: maximiza
# ganancia - mu * area. Las filas con cortes visibles ademas cuestan CPU por
# frame (se informan aparte: hay que medirlas).
# correr: python tools/arq0/p1v_pareto.py --rows work/arq0/p1v_rows_lam.json --lam 0 0.25 0.5 1 2 4 1000
#         python tools/arq0/p1v_mix.py [--cuts]   (sin --cuts: solo paleta fija por fila, sin CPU)
import json, sys, argparse
ap = argparse.ArgumentParser(); ap.add_argument('--cuts', action='store_true')
ap.add_argument('--json', default='work/arq0/p1v_rows_lam.json')
ap.add_argument('--show', type=float, help='mu: lista las filas elegidas')
a = ap.parse_args()
J = json.load(open(a.json))
ys = sorted(int(y) for y in J['1000'])
TR = 10
opts = {}
for y in ys:
    o = [('6', 0.0, 17.0, 1)]                         # (nombre, area, palabras, tramos); 17 = sin ganancia
    for lam, rows in J.items():
        ar, w, ns = rows[str(y)]
        if ns > 1 and not a.cuts: continue
        o.append(('5' if ns == 1 else '5c%s' % lam, ar, w, ns))
    opts[y] = o
def solve(mu):
    # DP sobre filas con el costo de transicion de modo
    INF = float('inf'); prev = {'6': (0.0, [])}
    for y in ys:
        cur = {}
        for name, ar, w, ns in opts[y]:
            m = '6' if name == '6' else '5'
            val = (17.0 - w) - mu * ar
            for pm, (pv, path) in prev.items():
                v = pv + val - (TR if pm != m else 0)
                if m not in cur or v > cur[m][0]: cur[m] = (v, path + [(y, name, ar, w, ns)])
        prev = cur
    return max(prev.values(), key=lambda t: t[0])[1]
print('%s; ganancia en %% de P1 (17 x 224 = 3808 palabras por frame)' % ('con cortes' if a.cuts else 'solo paleta fija por fila'))
for mu in (100, 30, 10, 5, 3, 2, 1, 0.5, 0.25, 0.1, 0.03, 0.01):
    path = solve(mu)
    gain = sum(17 - w for _, n, ar, w, ns in path if n != '6')
    tr = sum(1 for i in range(1, len(path)) if (path[i][1] == '6') != (path[i - 1][1] == '6'))
    gain -= TR * tr
    area = sum(ar for _, n, ar, w, ns in path)
    n5 = sum(1 for p in path if p[1] != '6'); nc = sum(1 for p in path if p[1].startswith('5c'))
    print('mu %6g: %3d filas de 5 planos (%3d con cortes), %2d cambios de modo, ganancia %5.1f %% de P1, area dE>=2 %5.0f px/foto'
          % (mu, n5, nc, tr, 100 * gain / 3808, area))
    if a.show == mu:
        print(' '.join('%d:%s' % (y - 192, n) for y, n, *_ in path))
