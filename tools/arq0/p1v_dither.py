# ARQ-0 P1-V: V3 (terna con lo visible, COLOR00 como cuarto color) contra V4 =
# V3 + tramado: el color que falta se dibuja en damero con los dos colores de
# la terna cuya mezcla (luz lineal) queda mas cerca. Mide la vara por pixel y
# una vara "vista": dE despues de promediar 2x2 en luz lineal (las dos imagenes).
# correr desde la raiz: python tools/arq0/p1v_dither.py [--step 32] [--img 1528]
import sys, itertools, collections, argparse
sys.path.insert(0, 'tools')
import numpy as np
from PIL import Image, ImageDraw
import render_d as R, arq_diff as A
ap = argparse.ArgumentParser(); ap.add_argument('--step', type=int, default=32)
ap.add_argument('--img', type=int, nargs='*', default=[1528, 3328]); a = ap.parse_args()
d = R.load('work/yi1_d.dat'); idx = R.l1_index(d)
Y0, LINES, SW, HUD = 192, 224, 256, 40
def rgb(c): return ((c >> 8 & 15) * 17, (c >> 4 & 15) * 17, (c & 15) * 17)
SKY = rgb(d['sky'])
def lin(c): return tuple(A._lin(float(v)) for v in c)
def unlin(l):
    o = []
    for v in l:
        v = 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
        o.append(min(255, max(0, round(v * 255))))
    return tuple(o)
def mix(p, q): return unlin(tuple((u + v) / 2 for u, v in zip(lin(p), lin(q))))
_best = {}
def best(cnt, pal, ncol, sky_ok):
    key = (tuple(sorted(cnt.items())), tuple(pal), ncol, sky_ok)
    if key in _best: return _best[key]
    cols = list(cnt); targets = [rgb(int(pal[i - 1])) for i in cols]
    cands = list(set(targets)); fixed = [SKY] if sky_ok else []
    choice = cands if len(cands) <= ncol else min(itertools.combinations(cands, ncol),
        key=lambda t: sum(min(A.de(tg, k) for k in list(t) + fixed) * cnt[i] for i, tg in zip(cols, targets)))
    opts = list(choice) + fixed
    m = {}
    for i, tg in zip(cols, targets):
        solo = min(opts, key=lambda k: A.de(tg, k))
        pair = min(((p, q) for p, q in itertools.combinations(opts, 2)), key=lambda pq: A.de(tg, mix(*pq)), default=None)
        dither = pair if pair and A.de(tg, mix(*pair)) + 1.0 < A.de(tg, solo) else None
        m[i] = (solo, dither)
    _best[key] = m
    return m
def frame(s):
    """(original, V3, V4) como listas de 256 x 184 colores (zona de juego)"""
    o, v3, v4 = [], [], []
    x0 = s // 2
    for y in range(Y0 + HUD, Y0 + LINES):
        i1 = idx[y, s:s + SW]
        i2 = d['l2idx'][y, (x0 + np.arange(SW)) % 512].astype(int)
        pal = d['l2pal'][y]
        lc = R.reg_colors(d['events'][y], d['W'])
        vis = (i1 == 0) & (i2 > 0)
        skyvis = bool(((i1 == 0) & (i2 == 0)).any())
        m = best(collections.Counter(int(v) for v in i2[vis]), pal, 3 if skyvis else 4, skyvis) if vis.any() else {}
        for x in range(SW):
            if i1[x] > 0:
                c = rgb(int(lc[i1[x], s + x])); o.append(c); v3.append(c); v4.append(c); continue
            if i2[x] == 0:
                o.append(SKY); v3.append(SKY); v4.append(SKY); continue
            c = rgb(int(pal[i2[x] - 1])); solo, dith = m[int(i2[x])]
            o.append(c); v3.append(solo)
            # damero en coordenadas de la capa 2 (se mueve con ella)
            v4.append(dith[((x0 + x) + y) & 1] if dith else solo)
    return o, v3, v4
def blur(img):
    L = [lin(c) for c in img]; H = len(img) // SW; out = []
    for y in range(H):
        for x in range(SW):
            acc = [0.0, 0.0, 0.0]; n = 0
            for yy in (y, min(y + 1, H - 1)):
                for xx in (x, min(x + 1, SW - 1)):
                    q = L[yy * SW + xx]; acc = [u + v for u, v in zip(acc, q)]; n += 1
            out.append(unlin(tuple(u / n for u in acc)))
    return out
def area(a, b, t=2): return sum(1 for p, q in zip(a, b) if A.de(p, q) >= t)
rows = []
for s in range(0, d['W'] - SW, a.step):
    o, v3, v4 = frame(s)
    bo = blur(o)
    rows.append((area(o, v3), area(o, v4), area(bo, blur(v3)), area(bo, blur(v4))))
n = len(rows)
for j, lab in enumerate(('V3 por pixel', 'V4 tramado, por pixel', 'V3 vista (2x2)', 'V4 tramado, vista (2x2)')):
    v = sorted(r[j] for r in rows)
    print('%-26s area dE>=2: media %5.0f  mediana %5d  peor %5d' % (lab, sum(v) / n, v[n // 2], v[-1]))
def heat(dd):
    if dd < 2: return None
    return (255, 200, 0) if dd < 5 else (255, 100, 0) if dd < 15 else (255, 0, 255)
for s in a.img:
    o, v3, v4 = frame(s); H = len(o) // SW
    bo, b3, b4 = blur(o), blur(v3), blur(v4)
    panels = []
    for img in (o, v3, v4):
        im = Image.new('RGB', (SW, H)); im.putdata(img); panels.append(im)
    for ref, bb in ((bo, b3), (bo, b4)):
        im = Image.new('RGB', (SW, H)); g = [tuple(v // 4 for v in c) for c in o]
        im.putdata([heat(A.de(p, q)) or gg for p, q, gg in zip(ref, bb, g)]); panels.append(im)
    S = 2; out = Image.new('RGB', (5 * SW * S + 32, H * S + 20), (24, 24, 24))
    for i, im in enumerate(panels):
        out.paste(im.resize((SW * S, H * S), Image.NEAREST), (i * (SW * S + 8), 20))
    ImageDraw.Draw(out).text((4, 4), 's=%d: hoy | V3 | V4 tramado | vista 2x2: V3 | V4' % s, fill=(255, 255, 0))
    out.save('work/arq0/p1v_s%d.png' % s)
    for i, nm in enumerate(('hoy', 'v3', 'v4')):
        panels[i].save('work/arq0/de2/p1v_%d_%s.png' % (s, nm))
    print('imagen work/arq0/p1v_s%d.png' % s)
