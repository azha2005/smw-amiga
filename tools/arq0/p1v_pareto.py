# ARQ-0 P1-V: cortes de paleta de PF2 anclados a la capa 2, optimizados por
# imagen Y por DMA del copper (P1 libera 17 palabras por linea; cada palabra
# de copper se las vuelve a quitar a la CPU y al blitter).
#   paleta de un tramo = 3 colores de PF2 (COLOR09-11) + COLOR00 (el cielo, o
#   otro color si el tramo no tiene cielo)
#   costo de un corte = WAIT (2 palabras) + 2 por color que cambia
#   costo del borrado = 2 por color que cambia entre el ultimo tramo visible
#   de la linea anterior y el primero de esta (lo escribe la CPU por frame)
# Programacion dinamica por fila (bloques de BLK px del mapa de 512, ciclico
# con el corte de vuelta en el bloque 0): min sum(pixel) + LAM * palabras,
# pixel = 1 si dE >= 2 (+ 0,02 dE para desempatar). La tabla no depende de la
# camara. Mide como p1v_anchor.py: area dE >= 2 visible y palabras por linea.
# correr desde la raiz: python tools/arq0/p1v_pareto.py --lam 0 2 8 32 [--step 50]
#   --img s ... --lam L: imagenes work/arq0/de2/p1vp_<L>_<s>_{hoy,p1v,mapa}.png
#   --emit L: work/arq0/p1v_tab_<L>.bin (para el 68000; derivado de la ROM, no versionar)
import sys, itertools, collections, argparse, struct
sys.path.insert(0, 'tools')
import numpy as np
import render_d as R, arq_diff as A
ap = argparse.ArgumentParser()
ap.add_argument('--lam', type=float, nargs='+', default=[0, 2, 8, 32])
ap.add_argument('--step', type=int, default=50); ap.add_argument('--blk', type=int, default=16)
ap.add_argument('--minseg', type=int, default=32); ap.add_argument('--grid', type=int, default=8)
ap.add_argument('--img', type=int, nargs='*'); ap.add_argument('--emit', action='store_true')
ap.add_argument('--rows', help='JSON con area y palabras POR FILA de cada lam (para p1v_mix.py)')
a = ap.parse_args()
d = R.load('work/yi1_d.dat'); idx = R.l1_index(d)
Y0, LINES, SW, HUD, L2W = 192, 224, 256, 40, 512
NB, MB = L2W // a.blk, a.minseg // a.blk
def rgb(c): return ((c >> 8 & 15) * 17, (c >> 4 & 15) * 17, (c & 15) * 17)
SKY = rgb(d['sky'])
ROWS = range(Y0 + (0 if '--rows' in sys.argv else HUD), Y0 + LINES)

def row_setup(y):
    """paletas candidatas y costo de cada bloque con cada una"""
    r = d['l2idx'][y].astype(int); pal = d['l2pal'][y]
    cols = sorted(set(rgb(int(pal[v - 1])) for v in set(r.tolist()) if v > 0))
    pals = []
    for t in itertools.combinations(cols, min(3, len(cols))):
        pals.append((t, SKY))
        for c0 in cols:
            if c0 not in t: pals.append((t, c0))
    NP = len(pals)
    bc = np.zeros((NP, NB))
    for b in range(NB):
        seg = r[b * a.blk:(b + 1) * a.blk]
        cnt = collections.Counter(rgb(int(pal[v - 1])) for v in seg if v > 0)
        sky = bool((seg == 0).any())
        for k, (t, c0) in enumerate(pals):
            if sky and c0 != SKY: bc[k, b] = 1e9; continue
            e = 0.0
            for c, n in cnt.items():
                dd = min(A.de(c, q) for q in t + (c0,))
                e += n * ((dd >= 2) + 0.02 * dd)
            bc[k, b] = e
    # cambios entre paletas: colores de PF2 que no estan + COLOR00 distinto
    D = np.zeros((NP, NP))
    for i, (t, c0) in enumerate(pals):
        st = set(t)
        for j, (u, c1) in enumerate(pals):
            D[i, j] = len(set(u) - st) + (c1 != c0)
    return pals, bc, D

def plan_row(setup, lam):
    """tramos [(inicio_px, paleta)] minimizando pixeles + lam * palabras"""
    pals, bc, D = setup; NP = len(pals)
    C = np.concatenate([np.zeros((NP, 1)), np.cumsum(bc, axis=1)], axis=1)   # C[:, k] = bloques < k
    T = 2 * lam * D                                                          # MOVE de un corte
    INF = 1e18
    f = np.full((NB + 1, NP), INF); arg = {}
    f[0] = 0.0
    g = np.full((NB + 1, NP), INF); garg = np.zeros((NB + 1, NP), int)
    for k in range(MB, NB + 1):
        # f[k][Q] = min_j g[j][Q] + C[Q,k] - C[Q,j] (+ 2 lam del WAIT si j > 0)
        best = np.full(NP, INF); bj = np.zeros(NP, int)
        for j in range(0, k - MB + 1):
            if j == 0: base = np.zeros(NP)
            else:
                if not np.isfinite(g[j]).any() or g[j].min() >= INF: continue
                base = g[j] + 2 * lam
            v = base + C[:, k] - C[:, j]
            m = v < best; best[m] = v[m]; bj[m] = j
        f[k] = best; arg[k] = bj
        if k < NB:   # g[k][Q] = min_P f[k][P] + T[P, Q]
            M = f[k][:, None] + T
            garg[k] = M.argmin(axis=0); g[k] = M.min(axis=0)
    q = int(f[NB].argmin()); k = NB; segs = []
    while k > 0:
        j = int(arg[k][q]); segs.append((j * a.blk, pals[q]))
        if j > 0: q = int(garg[j][q])
        k = j
    return segs[::-1]

def screen_segs(p, x0):
    c0 = x0 % L2W; first = 0
    for k, (st, _) in enumerate(p):
        if st <= c0: first = k
    out = [(0, p[first][1])]
    for st, op in p:
        sx = (st - x0) % L2W
        if 0 < sx < SW: out.append(((sx + a.grid // 2) // a.grid * a.grid, op))
    return sorted(out, key=lambda t: t[0])
def chg(P, Q):
    return len(set(Q[0]) - set(P[0])) + (Q[1] != P[1])

def frame(plans, s, keep=False):
    x0 = (s // 2) % L2W; area = 0; words = 0; o = []; q = []; last = None
    for y in ROWS:
        sg = screen_segs(plans[y], x0)
        if last is not None: words += 2 * chg(last, sg[0][1])
        for (_, P), (_, Q) in zip(sg, sg[1:]): words += 2 + 2 * chg(P, Q)
        last = sg[-1][1]
        i1 = idx[y, s:s + SW]; i2 = d['l2idx'][y, (x0 + np.arange(SW)) % L2W].astype(int)
        pal = d['l2pal'][y]; lc = R.reg_colors(d['events'][y], d['W']) if keep else None
        cur = 0
        for x in range(SW):
            while cur + 1 < len(sg) and sg[cur + 1][0] <= x: cur += 1
            if i1[x] > 0:
                if keep: c = rgb(int(lc[i1[x], s + x])); o.append(c); q.append(c)
                continue
            if i2[x] == 0:
                if keep: o.append(SKY); q.append(SKY)
                continue
            t, c0 = sg[cur][1]
            c = rgb(int(pal[i2[x] - 1])); k = min(t + (c0,), key=lambda u: A.de(c, u))
            if A.de(c, k) >= 2: area += 1
            if keep: o.append(c); q.append(k)
    return area, words / LINES, o, q

def per_row(plans):
    """por fila: area dE >= 2 visible y palabras de copper (cortes + borrado
    contra la fila anterior), promedio por foto"""
    ar = collections.Counter(); wd = collections.Counter(); n = 0
    for s in range(0, d['W'] - SW, a.step):
        n += 1; x0 = (s // 2) % L2W; last = None
        for y in ROWS:
            sg = screen_segs(plans[y], x0)
            w = 2 * chg(last, sg[0][1]) if last is not None else 0
            for (_, P), (_, Q) in zip(sg, sg[1:]): w += 2 + 2 * chg(P, Q)
            wd[y] += w; last = sg[-1][1]
            i1 = idx[y, s:s + SW]; i2 = d['l2idx'][y, (x0 + np.arange(SW)) % L2W].astype(int)
            pal = d['l2pal'][y]; cur = 0
            for x in np.nonzero((i1 == 0) & (i2 > 0))[0]:
                while cur + 1 < len(sg) and sg[cur + 1][0] <= x: cur += 1
                t, c0 = sg[cur][1]; c = rgb(int(pal[i2[x] - 1]))
                if min(A.de(c, u) for u in t + (c0,)) >= 2: ar[y] += 1
    return {y: (ar[y] / n, wd[y] / n, len(plans[y])) for y in ROWS}
setups = {y: row_setup(y) for y in ROWS}
if a.rows:
    import json
    out = {}
    for lam in a.lam:
        plans = {y: plan_row(setups[y], lam) for y in ROWS}
        out['%g' % lam] = {str(y): v for y, v in per_row(plans).items()}
        print('lam %g listo' % lam); sys.stdout.flush()
    json.dump(out, open(a.rows, 'w'))
    sys.exit(0)
for lam in a.lam:
    plans = {y: plan_row(setups[y], lam) for y in ROWS}
    nseg = [len(p) for p in plans.values()]
    tag = ('%g' % lam).replace('.', 'p')
    if a.emit:
        # por fila: .w n, n x (.w inicio px, .w COLOR09, COLOR10, COLOR11, COLOR00) en 12 bits
        def c12(c): return (c[0] // 17) << 8 | (c[1] // 17) << 4 | c[2] // 17
        out = bytearray()
        for y in ROWS:
            out += struct.pack('>H', len(plans[y]))
            for st, (t, c0) in plans[y]:
                t3 = list(t) + [t[-1]] * (3 - len(t))
                out += struct.pack('>5H', st, *[c12(c) for c in t3], c12(c0))
        open('work/arq0/p1v_tab_%s.bin' % tag, 'wb').write(out)
        print('lam %g: work/arq0/p1v_tab_%s.bin, %d B' % (lam, tag, len(out)))
    if a.img:
        from PIL import Image
        for s in a.img:
            area, w, o, q = frame(plans, s, True); H = len(o) // SW
            heat = lambda dd: None if dd < 2 else (255, 200, 0) if dd < 5 else (255, 100, 0) if dd < 15 else (255, 0, 255)
            for img, t in ((o, 'hoy'), (q, 'p1v'), ([heat(A.de(u, v)) or tuple(z // 4 for z in u) for u, v in zip(o, q)], 'mapa')):
                im = Image.new('RGB', (SW, H)); im.putdata(img)
                im.resize((SW * 2, H * 2), Image.NEAREST).save('work/arq0/de2/p1vp_%s_%d_%s.png' % (tag, s, t))
            print('lam %g s=%d: area %d px, %.1f palabras/linea -> work/arq0/de2/p1vp_%s_%d_*.png' % (lam, s, area, w, tag, s))
        continue
    if a.emit: continue
    r = [frame(plans, s)[:2] for s in range(0, d['W'] - SW, a.step)]
    ar = sorted(x[0] for x in r); wd = sorted(x[1] for x in r); n = len(r)
    print('lam %5g: area dE>=2 media %5.0f mediana %5d peor %5d | palabras de copper por linea media %4.1f max %4.1f (P1 libera 17) | tramos/fila %.1f'
          % (lam, sum(ar) / n, ar[n // 2], ar[-1], sum(wd) / n, wd[-1], sum(nseg) / len(nseg)))
    sys.stdout.flush()
