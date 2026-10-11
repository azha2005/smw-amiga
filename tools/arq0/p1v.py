# ARQ-0 P1-V: trucos visuales para la capa 2 con 3 colores por fila (5 planos).
# Mide en pantalla (capa 1 encima, paralaje s/2, zona de juego) el area con
# dE >= 2 y >= 3 por foto, para cada variante:
#   V0  terna fija por fila (P1 tal cual)
#   V1  terna por fila y ventana de la capa 2 (x0 = s/2 mod 512; tabla por camara)
#   V2  V1 + COLOR00 como cuarto color si en esa fila y ventana no se ve el cielo
#   V3  como V2 pero eligiendo con los pixeles visibles (la capa 1 tapa)
# correr desde la raiz: python tools/arq0/p1v.py [--step 8]
import sys, itertools, collections, argparse
sys.path.insert(0, 'tools')
import numpy as np
import render_d as R, arq_diff as A
ap = argparse.ArgumentParser(); ap.add_argument('--step', type=int, default=8); a = ap.parse_args()
d = R.load('work/yi1_d.dat'); idx = R.l1_index(d)
Y0, LINES, SW, HUD = 192, 224, 256, 40
def rgb(c): return ((c >> 8 & 15) * 17, (c >> 4 & 15) * 17, (c & 15) * 17)
SKY = rgb(d['sky'])
_best = {}
def best(cnt, pal, ncol, sky_ok):
    """la terna (o cuarteta) que minimiza la suma de dE; devuelve el mapa i -> color"""
    key = (tuple(sorted(cnt.items())), tuple(pal), ncol, sky_ok)
    if key in _best: return _best[key]
    cols = [c for c in cnt]
    targets = [rgb(int(pal[i - 1])) for i in cols]
    cands = list(set(targets))
    fixed = [SKY] if sky_ok else []
    if len(cands) <= ncol:
        choice = cands
    else:
        choice = min(itertools.combinations(cands, ncol),
                     key=lambda t: sum(min(A.de(tg, k) for k in list(t) + fixed) * cnt[i] for i, tg in zip(cols, targets)))
    m = {i: min(list(choice) + fixed, key=lambda k: A.de(tg, k)) for i, tg in zip(cols, targets)}
    _best[key] = m
    return m
rows = range(Y0 + HUD, Y0 + LINES)
fixed = {}
for y in rows:
    cnt = collections.Counter(int(v) for v in d['l2idx'][y] if v > 0)
    fixed[y] = best(cnt, d['l2pal'][y], 3, True)
res = {v: [] for v in ('V0', 'V1', 'V2', 'V3')}
changes = {v: 0 for v in ('V1', 'V2', 'V3')}
prev = {v: {} for v in changes}
for s in range(0, d['W'] - SW, a.step):
    x0 = s // 2
    acc = {v: [0, 0] for v in res}
    for y in rows:
        i1 = idx[y, s:s + SW]
        i2 = d['l2idx'][y, (x0 + np.arange(SW)) % 512].astype(int)
        pal = d['l2pal'][y]
        vis = (i1 == 0) & (i2 > 0)
        if not vis.any():
            continue
        win = collections.Counter(int(v) for v in i2 if v > 0)
        skyvis_win = bool((i2 == 0).any())              # sin tener en cuenta la capa 1
        skyvis = bool(((i1 == 0) & (i2 == 0)).any())     # lo que de verdad se ve
        visc = collections.Counter(int(v) for v in i2[vis])
        maps = {'V0': fixed[y],
                'V1': best(win, pal, 3, True),
                'V2': best(win, pal, 3 if skyvis_win else 4, skyvis_win),
                'V3': best(visc, pal, 3 if skyvis else 4, skyvis)}
        for v, m in maps.items():
            for i, n in visc.items():
                dd = A.de(rgb(int(pal[i - 1])), m[i])
                if dd >= 2: acc[v][0] += n
                if dd >= 3: acc[v][1] += n
            if v in prev:
                sig = tuple(sorted(set(m.values())))
                if prev[v].get(y) != sig:
                    changes[v] += 1; prev[v][y] = sig
    for v in res: res[v].append(acc[v])
n = len(res['V0']); steps = n
print('encuadres %d (cada %d px de s)' % (n, a.step))
for v, l in res.items():
    a2 = sorted(x[0] for x in l); a3 = sorted(x[1] for x in l)
    extra = '' if v == 'V0' else '; cambios de paleta por fila: %.1f por paso de %d px' % (changes[v] / steps, a.step)
    print('%s  dE>=2: media %5.0f  mediana %5d  peor %5d | dE>=3: media %5.0f  peor %5d%s' % (
        v, sum(a2) / n, a2[n // 2], a2[-1], sum(a3) / n, a3[-1], extra))
