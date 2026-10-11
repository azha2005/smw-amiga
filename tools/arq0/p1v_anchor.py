# ARQ-0 P1-V: cortes de paleta de PF2 ANCLADOS AL CONTENIDO de la capa 2.
# Cada fila del mapa de la capa 2 (512 px, ciclica) se parte en tramos de
# >= MINSEG px (bloques de BLK px); cada tramo tiene su terna (+ COLOR00 como
# cuarto color si en el tramo no hay cielo). Con MINSEG = 128 una ventana de
# 256 px ve a lo sumo 3 tramos (2 cortes). En pantalla el corte cae en
# (inicio - x0) mod 512, redondeado hacia abajo a la rejilla GRID del copper.
# La tabla no depende de la camara: una lista de tramos por fila.
# Mide el area dE >= 2 sobre lo visible (la capa 1 tapa), como p1v_split.py.
# correr desde la raiz: python tools/arq0/p1v_anchor.py [--step 64] [--grid 8] [--img s ...]
import sys, itertools, collections, argparse
sys.path.insert(0, 'tools')
import numpy as np
import render_d as R, arq_diff as A
ap = argparse.ArgumentParser(); ap.add_argument('--step', type=int, default=64)
ap.add_argument('--blk', type=int, default=16); ap.add_argument('--minseg', type=int, default=128)
ap.add_argument('--grid', type=int, default=8)
ap.add_argument('--img', type=int, nargs='*', help='solo imagenes de estos s')
a = ap.parse_args()
d = R.load('work/yi1_d.dat'); idx = R.l1_index(d)
Y0, LINES, SW, HUD, L2W = 192, 224, 256, 40, 512
NB, MB = L2W // a.blk, a.minseg // a.blk
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
def segcost(cnt, opts):
    return sum(min((A.de(c, k) for k in opts), default=0.0) * n for c, n in cnt.items())
def plan_row(y):
    """tramos [(inicio_px, opciones)] de la fila y del mapa de la capa 2"""
    r = d['l2idx'][y].astype(int); pal = d['l2pal'][y]
    blk = [collections.Counter(rgb(int(pal[v - 1])) for v in r[b * a.blk:(b + 1) * a.blk] if v > 0) for b in range(NB)]
    sky = [bool((r[b * a.blk:(b + 1) * a.blk] == 0).any()) for b in range(NB)]
    memo = {}
    def seg(i, j):          # bloques i..j-1 (ciclicos)
        k = (i, j)
        if k not in memo:
            c = collections.Counter(); sk = False
            for b in range(i, j): c.update(blk[b % NB]); sk = sk or sky[b % NB]
            op = choose(tuple(sorted(c.items())), sk)
            memo[k] = (segcost(c, op), op)
        return memo[k]
    best = None
    for rot in range(MB):   # el primer corte cae en uno de los primeros MB bloques
        INF = float('inf'); f = [INF] * (NB + 1); pr = [None] * (NB + 1); f[0] = 0
        for j in range(MB, NB + 1):
            for i in range(0, j - MB + 1):
                if f[i] == INF: continue
                e = f[i] + seg(rot + i, rot + j)[0]
                if e < f[j]: f[j], pr[j] = e, i
        if best is None or f[NB] < best[0]:
            cuts = []; j = NB
            while j: i = pr[j]; cuts.append((rot + i, rot + j)); j = i
            best = (f[NB], rot, cuts[::-1])
    return [(((i % NB) * a.blk), seg(i, j)[1]) for i, j in best[2]]
plans = {y: plan_row(y) for y in range(Y0 + HUD, Y0 + LINES)}
nseg = [len(p) for p in plans.values()]
# tabla: por fila, n tramos x (inicio 1 B + 4 colores x 2 B) + 1 B de cuenta
tbytes = sum(1 + n * 9 for n in nseg)
def screen_segs(p, x0):
    """[(x de pantalla donde el copper cambia, opciones)]: el tramo que entra por
    x = 0 y cada corte visible, redondeado a la rejilla mas cercana"""
    c0 = x0 % L2W; first = None
    for k, (st, op) in enumerate(p):
        en = p[(k + 1) % len(p)][0]
        if (st <= c0 < en) if st < en else (c0 >= st or c0 < en): first = k
    out = [(0, p[first][1])]
    for st, op in p:
        sx = (st - x0) % L2W
        if 0 < sx < SW: out.append(((sx + a.grid // 2) // a.grid * a.grid, op))
    return sorted(out, key=lambda t: t[0])
def opts_at(segs, x):
    cur = segs[0][1]
    for cx, op in segs:
        if cx <= x: cur = op
    return cur
def frame(s, keep=False):
    x0 = (s // 2) % L2W; area = 0; o = []; q = []
    for y in range(Y0 + HUD, Y0 + LINES):
        i1 = idx[y, s:s + SW]; i2 = d['l2idx'][y, (x0 + np.arange(SW)) % L2W].astype(int)
        pal = d['l2pal'][y]; sg = screen_segs(plans[y], x0)
        lc = R.reg_colors(d['events'][y], d['W']) if keep else None
        for x in range(SW):
            if i1[x] > 0:
                if keep: c = rgb(int(lc[i1[x], s + x])); o.append(c); q.append(c)
                continue
            if i2[x] == 0:
                if keep: o.append(SKY); q.append(SKY)
                continue
            c = rgb(int(pal[i2[x] - 1])); k = min(opts_at(sg, x), key=lambda t: A.de(c, t))
            if A.de(c, k) >= 2: area += 1
            if keep: o.append(c); q.append(k)
    return area, o, q
if a.img:
    from PIL import Image
    for s in a.img:
        area, o, q = frame(s, True); H = len(o) // SW
        heat = lambda dd: None if dd < 2 else (255, 200, 0) if dd < 5 else (255, 100, 0) if dd < 15 else (255, 0, 255)
        for img, t in ((o, 'hoy'), (q, 'p1v'), ([heat(A.de(u, v)) or tuple(w // 4 for w in u) for u, v in zip(o, q)], 'mapa')):
            im = Image.new('RGB', (SW, H)); im.putdata(img)
            im.resize((SW * 2, H * 2), Image.NEAREST).save('work/arq0/de2/p1va_%d_%s.png' % (s, t))
        print('s=%d: area dE>=2 %d px -> work/arq0/de2/p1va_%d_*.png' % (s, area, s))
    sys.exit(0)
v = sorted(frame(s)[0] for s in range(0, d['W'] - SW, a.step)); n = len(v)
print('%d encuadres (s cada %d px); tramos >= %d px en bloques de %d, rejilla del copper %d px'
      % (n, a.step, a.minseg, a.blk, a.grid))
print('tramos por fila: media %.1f, max %d; tabla %d B (1 + 9 B por tramo)' % (sum(nseg) / len(nseg), max(nseg), tbytes))
print('area dE>=2: media %5.0f  mediana %5d  peor %5d' % (sum(v) / n, v[n // 2], v[-1]))
