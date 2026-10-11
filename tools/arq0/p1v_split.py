# ARQ-0 P1-V: cortes de paleta de PF2 a mitad de fila (copper: WAIT + 3-4 MOVE
# por corte). Cada fila de la capa 2 se parte en 1, 2 o 3 tramos (cortes en
# multiplos de 32 px de pantalla), cada uno con su terna (+ COLOR00 como cuarto
# color si en el tramo no se ve el cielo). Area dE >= 2 sobre lo que se ve.
#   eleccion "vista": con los pixeles visibles (depende de s: calculo por frame)
#   eleccion "tabla": con toda la ventana de la capa 2 (depende solo de
#                     x0 = s/2 mod 512: se puede tabular por posicion de camara)
# En "vista" los cortes se eligen con lo visible; en "tabla", con la ventana
# (la eleccion entera depende solo de x0). El area se mide siempre en lo visible.
# correr desde la raiz: python tools/arq0/p1v_split.py [--step 64]
import sys, itertools, collections, argparse
sys.path.insert(0, 'tools')
import numpy as np
import render_d as R, arq_diff as A
ap = argparse.ArgumentParser(); ap.add_argument('--step', type=int, default=64)
ap.add_argument('--blk', type=int, default=32)
ap.add_argument('--img', type=int, nargs='*', help='solo imagenes de estos s (tabla, <= 2 cortes)')
a = ap.parse_args()
d = R.load('work/yi1_d.dat'); idx = R.l1_index(d)
Y0, LINES, SW, HUD, BLK = 192, 224, 256, 40, a.blk
def rgb(c): return ((c >> 8 & 15) * 17, (c >> 4 & 15) * 17, (c & 15) * 17)
SKY = rgb(d['sky'])
_ch = {}
def choose(cnt, sky_ok):
    """la terna (+cielo) que minimiza la suma de dE de estos conteos"""
    key = (cnt, sky_ok)
    if key in _ch: return _ch[key]
    cols = [c for c, _ in cnt]
    fixed = [SKY] if sky_ok else []
    ncol = 3 if sky_ok else 4
    combos = [cols] if len(cols) <= ncol else list(itertools.combinations(cols, ncol))
    best = min(combos, key=lambda t: sum(min(A.de(c, k) for k in list(t) + fixed) * n for c, n in cnt)) if cols else []
    _ch[key] = opts = list(best) + fixed
    return opts
def cost(cnt, opts):
    e = a2 = 0
    for c, n in cnt.items():
        dd = min((A.de(c, k) for k in opts), default=0.0)
        e += dd * n; a2 += n if dd >= 2 else 0
    return e, a2
NCUT = (0, 1, 2)
def render(s):
    """hoy | tabla con <= 2 cortes | mapa: la zona de juego de la camara s"""
    from PIL import Image, ImageDraw
    x0 = s // 2; o = []; q = []
    for y in range(Y0 + HUD, Y0 + LINES):
        i1 = idx[y, s:s + SW]; i2 = d['l2idx'][y, (x0 + np.arange(SW)) % 512].astype(int)
        pal = d['l2pal'][y]; lc = R.reg_colors(d['events'][y], d['W']); nb = SW // BLK
        win = [collections.Counter(rgb(int(pal[v - 1])) for v in i2[b * BLK:(b + 1) * BLK] if v > 0) for b in range(nb)]
        skw = [bool((i2[b * BLK:(b + 1) * BLK] == 0).any()) for b in range(nb)]
        def opts(lo, hi):
            c = collections.Counter(); sk = False
            for b in range(lo, hi): c.update(win[b]); sk = sk or skw[b]
            return choose(tuple(sorted(c.items())), sk)
        def segcost(lo, hi):
            v = collections.Counter()
            for b in range(lo, hi): v.update(win[b])
            return cost(v, opts(lo, hi))
        parts = [[(0, nb)]] + [[(0, k), (k, nb)] for k in range(1, nb)] +                 [[(0, i), (i, j), (j, nb)] for i in range(1, nb) for j in range(i + 1, nb)]
        best = min(parts, key=lambda p: tuple(map(sum, zip(*[segcost(lo, hi) for lo, hi in p]))))
        segof = {}
        for lo, hi in best:
            op = opts(lo, hi)
            for b in range(lo, hi): segof[b] = op
        for x in range(SW):
            if i1[x] > 0:
                c = rgb(int(lc[i1[x], s + x])); o.append(c); q.append(c); continue
            if i2[x] == 0: o.append(SKY); q.append(SKY); continue
            c = rgb(int(pal[i2[x] - 1])); o.append(c)
            q.append(min(segof[x // BLK], key=lambda k: A.de(c, k)))
    H = len(o) // SW
    def heat(dd):
        return None if dd < 2 else (255, 200, 0) if dd < 5 else (255, 100, 0) if dd < 15 else (255, 0, 255)
    ims = []
    for img in (o, q, [heat(A.de(u, v)) or tuple(w // 4 for w in u) for u, v in zip(o, q)]):
        im = Image.new('RGB', (SW, H)); im.putdata(img); ims.append(im)
    area = sum(1 for u, v in zip(o, q) if A.de(u, v) >= 2)
    for im, t in zip(ims, ('hoy', 'p1v', 'mapa')):
        im.resize((SW * 2, H * 2), Image.NEAREST).save('work/arq0/de2/p1v2c_%d_%s.png' % (s, t))
    print('s=%d: area dE>=2 %d px -> work/arq0/de2/p1v2c_%d_*.png' % (s, area, s))
if a.img:
    for s_ in a.img: render(s_)
    sys.exit(0)
tot = {(m, k): [] for m in ('vista', 'tabla') for k in NCUT}
for s in range(0, d['W'] - SW, a.step):
    x0 = s // 2
    acc = {key: 0 for key in tot}
    for y in range(Y0 + HUD, Y0 + LINES):
        i1 = idx[y, s:s + SW]
        i2 = d['l2idx'][y, (x0 + np.arange(SW)) % 512].astype(int)
        pal = d['l2pal'][y]
        vis = (i1 == 0) & (i2 > 0)
        if not vis.any(): continue
        nb = SW // BLK
        B = []
        for b in range(nb):
            sl = slice(b * BLK, (b + 1) * BLK)
            B.append(dict(vis=collections.Counter(rgb(int(pal[v - 1])) for v in i2[sl][vis[sl]]),
                          win=collections.Counter(rgb(int(pal[v - 1])) for v in i2[sl][i2[sl] > 0]),
                          skyv=bool(((i1[sl] == 0) & (i2[sl] == 0)).any()), skyw=bool((i2[sl] == 0).any())))
        for mode in ('vista', 'tabla'):
            kc, ks = ('vis', 'skyv') if mode == 'vista' else ('win', 'skyw')
            def seg(lo, hi):
                # elige con kc (en "tabla" tambien los cortes: solo depende de x0);
                # devuelve (costo de eleccion, area visible dE >= 2)
                c = collections.Counter(); v = collections.Counter(); sk = False
                for bb in B[lo:hi]: c.update(bb[kc]); v.update(bb['vis']); sk = sk or bb[ks]
                op = choose(tuple(sorted(c.items())), sk)
                return cost(c, op)[0], cost(v, op)[1]
            parts = {0: [[(0, nb)]],
                     1: [[(0, k), (k, nb)] for k in range(1, nb)],
                     2: [[(0, i), (i, j), (j, nb)] for i in range(1, nb) for j in range(i + 1, nb)]}
            best = None
            for k in NCUT:
                for p in parts[k]:
                    r = [seg(lo, hi) for lo, hi in p]
                    e = (sum(x[0] for x in r), sum(x[1] for x in r))
                    if best is None or e < best: best = e
                acc[(mode, k)] += best[1]
    for key in tot: tot[key].append(acc[key])
n = len(tot[('vista', 0)])
print('%d encuadres (s cada %d px), cortes en multiplos de %d px' % (n, a.step, BLK))
for (m, k), v in tot.items():
    v = sorted(v)
    print('eleccion %-5s  cortes por fila <= %d   area dE>=2: media %5.0f  mediana %5d  peor %5d' % (m, k, sum(v) / n, v[n // 2], v[-1]))
