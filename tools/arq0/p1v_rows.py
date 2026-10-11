# ARQ-0 P1-V2: 5 o 6 planos POR FILA (BPLCON0 por el copper en el borrado).
# La ventana vertical es fija (Y0), asi que cada fila de pantalla es siempre
# la misma fila de la capa 2: en las filas de 5 planos la capa 2 usa una
# paleta fija de 3 colores (+ COLOR00 si en esa fila nunca se ve el cielo),
# en las de 6 queda como hoy. Costo de imagen: el area dE >= 2 visible de las
# filas de 5 planos (promedio por foto, capa 1 encima, paralaje s/2, las 224
# filas). Costo de copper: 1 MOVE (BPLCON0) por cambio de modo + 2 palabras
# por color de PF2 que cambia entre filas seguidas de 5 planos. Ganancia: la
# fraccion de filas de 5 planos (P1 entero = 224).
# correr desde la raiz: python tools/arq0/p1v_rows.py [--step 50] [--budget 0 50 100 200 400]
#   --bands B1 B2 --img s ...: imagenes work/arq0/de2/p1vb_<B1>_<B2>_<s>_{hoy,p1v,mapa}.png
import sys, itertools, collections, argparse, struct
sys.path.insert(0, 'tools')
import numpy as np
import render_d as R, arq_diff as A
ap = argparse.ArgumentParser(); ap.add_argument('--step', type=int, default=50)
ap.add_argument('--budget', type=float, nargs='+', default=[0, 25, 50, 100, 200, 400, 800])
ap.add_argument('--img', type=int, nargs='*'); ap.add_argument('--emit', action='store_true')
ap.add_argument('--bands', type=int, nargs=2, help='B1 B2: 5 planos fuera de [B1, B2) (con --img)')
a = ap.parse_args()
d = R.load('work/yi1_d.dat'); idx = R.l1_index(d)
Y0, LINES, SW, L2W = 192, 224, 256, 512
def rgb(c): return ((c >> 8 & 15) * 17, (c >> 4 & 15) * 17, (c & 15) * 17)
SKY = rgb(d['sky'])
SS = list(range(0, d['W'] - SW, a.step)); NF = len(SS)
rows = []
for y in range(Y0, Y0 + LINES):
    pal = d['l2pal'][y]; vis = collections.Counter(); sky = False
    for s in SS:
        x0 = (s // 2) % L2W
        i1 = idx[y, s:s + SW]; i2 = d['l2idx'][y, (x0 + np.arange(SW)) % L2W].astype(int)
        m = i1 == 0
        sky = sky or bool((m & (i2 == 0)).any())
        vis.update(int(v) for v in i2[m & (i2 > 0)])
    cnt = collections.Counter()
    for v, n in vis.items(): cnt[rgb(int(pal[v - 1]))] += n
    cols = sorted(cnt)
    best = (0.0, (tuple(cols), SKY)) if len(cols) <= 3 else None
    if best is None:
        for t in itertools.combinations(cols, 3):
            for c0 in ([SKY] if sky else [SKY] + [c for c in cols if c not in t]):
                e = sum(n for c, n in cnt.items() if min(A.de(c, q) for q in t + (c0,)) >= 2)
                if best is None or e < best[0]: best = (e, (t, c0))
    rows.append(dict(y=y, err=best[0] / NF, pal=best[1], vis=sum(cnt.values()) / NF))
def chg(P, Q):
    return len(set(Q[0]) - set(P[0])) + (Q[1] != P[1])
order = sorted(range(LINES), key=lambda r: rows[r]['err'])
def pick(B):
    """filas de 5 planos: las de menor error hasta gastar B px por foto"""
    sel = set(); e = 0.0
    for r in order:
        if e + rows[r]['err'] > B: break
        sel.add(r); e += rows[r]['err']
    return sel, e
def copper(sel):
    w = 0
    for r in range(1, LINES):
        if (r in sel) != (r - 1 in sel): w += 2                    # MOVE BPLCON0
        if r in sel and r - 1 in sel: w += 2 * chg(rows[r - 1]['pal'], rows[r]['pal'])
        elif r in sel: w += 2 * 4                                   # la paleta entera
    return w
z = sum(1 for r in rows if r['err'] == 0)
print('filas con error 0 a 5 planos: %d de %d (capa 2 tapada o <= 3 colores + cielo)' % (z, LINES))
for B in a.budget:
    sel, e = pick(B)
    print('presupuesto %4g px/foto: %3d filas de 5 planos (%4.1f %% de la ganancia de P1), area dE>=2 %5.0f px/foto, copper %d palabras por frame (P1 entero libera %d)'
          % (B, len(sel), 100.0 * len(sel) / LINES, e, copper(sel), 17 * len(sel)))
if a.bands and a.img:
    from PIL import Image
    B1, B2 = a.bands; HUD = 40
    sel = set(r for r in range(LINES) if not (B1 <= r < B2))
    print('bandas: %d filas de 5 planos, area %.0f px/foto (las 224 filas), copper %d palabras por frame'
          % (len(sel), sum(rows[r]['err'] for r in sel), copper(sel)))
    for s_ in a.img:
        x0 = (s_ // 2) % L2W; o = []; q = []
        for r in range(HUD, LINES):
            y = Y0 + r; i1 = idx[y, s_:s_ + SW]; i2 = d['l2idx'][y, (x0 + np.arange(SW)) % L2W].astype(int)
            pal = d['l2pal'][y]; lc = R.reg_colors(d['events'][y], d['W']); t, c0 = rows[r]['pal']
            for x in range(SW):
                if i1[x] > 0: c = rgb(int(lc[i1[x], s_ + x])); o.append(c); q.append(c); continue
                if i2[x] == 0: o.append(SKY); q.append(SKY); continue
                c = rgb(int(pal[i2[x] - 1])); o.append(c)
                q.append(min(tuple(t) + (c0,), key=lambda u: A.de(c, u)) if r in sel else c)
        H = len(o) // SW
        heat = lambda dd: None if dd < 2 else (255, 200, 0) if dd < 5 else (255, 100, 0) if dd < 15 else (255, 0, 255)
        area = sum(1 for u, v in zip(o, q) if A.de(u, v) >= 2)
        for img, t in ((o, 'hoy'), (q, 'p1v'), ([heat(A.de(u, v)) or tuple(z // 4 for z in u) for u, v in zip(o, q)], 'mapa')):
            im = Image.new('RGB', (SW, H)); im.putdata(img)
            im.resize((SW * 2, H * 2), Image.NEAREST).save('work/arq0/de2/p1vb_%d_%d_%d_%s.png' % (B1, B2, s_, t))
        print('s=%d: area de la zona de juego %d px -> work/arq0/de2/p1vb_%d_%d_%d_*.png' % (s_, area, B1, B2, s_))
