# ARQ-0 (docs/informe-arq-0-1011.md): P1 en pantalla: area dE>=2 por foto e imagenes hoy|P1|dE
# correr desde la raiz: python tools/arq0/p1screen.py
import sys, itertools, collections
sys.path.insert(0, 'tools')
import numpy as np
import render_d as R, arq_diff as A
d = R.load('work/yi1_d.dat'); idx = R.l1_index(d)
Y0, LINES, SW = 192, 224, 256
def rgb(c): return ((c >> 8 & 15) * 17, (c >> 4 & 15) * 17, (c & 15) * 17)
sky = rgb(d['sky'])
# terna fija por fila (lo mejor de P1(b)) con el peso de toda la fila de 512
remap = {}
for y in range(Y0, Y0 + LINES):
    row = d['l2idx'][y]; pal = d['l2pal'][y]
    cnt = collections.Counter(int(v) for v in row if v > 0)
    cols = list(cnt)
    if len(cols) <= 3:
        remap[y] = {i: i for i in cols}; continue
    best = None
    for t in itertools.combinations(cols, 3):
        e = sum(min([A.de(rgb(pal[i - 1]), rgb(pal[k - 1])) for k in t] + [A.de(rgb(pal[i - 1]), sky)]) * n for i, n in cnt.items())
        if best is None or e < best[0]: best = (e, t)
    t = best[1]; m = {}
    for i in cols:
        cands = [(A.de(rgb(pal[i - 1]), rgb(pal[k - 1])), k) for k in t] + [(A.de(rgb(pal[i - 1]), sky), 0)]
        m[i] = min(cands)[1]
    remap[y] = m
areas = []; dsum = 0; npx = 0
for s in range(0, d['W'] - SW, 8):
    area = 0
    for L in range(40 - 0, LINES):           # sin la franja de la barra de estado (filas 0-39 de pantalla)
        y = Y0 + L
        i1 = idx[y, s:s + SW]
        i2 = d['l2idx'][y, (s // 2 + np.arange(SW)) % 512]
        vis = (i1 == 0) & (i2 > 0)
        pal = d['l2pal'][y]
        for v in i2[vis]:
            v = int(v); k = remap[y][v]
            a = rgb(pal[v - 1]); b = sky if k == 0 else rgb(pal[k - 1])
            de = A.de(a, b)
            if de >= 2: area += 1
            dsum += de; npx += 1
    areas.append((area, s))
areas.sort()
n = len(areas)
print('encuadres', n, 'area dE>=2 por foto (zona de juego): media %.0f px, mediana %d, p90 %d, peor %d (s=%d)' % (
    sum(a for a, _ in areas) / n, areas[n // 2][0], areas[int(n * .9)][0], areas[-1][0], areas[-1][1]))
print('dE medio sobre la capa 2 visible: %.3f' % (dsum / npx))

from PIL import Image, ImageDraw
def frame(s, use_p1):
    im = Image.new('RGB', (SW, LINES)); px = im.load()
    for L in range(LINES):
        y = Y0 + L
        lc = R.reg_colors(d['events'][y], d['W'])
        for x in range(SW):
            i1 = idx[y, s + x]
            if i1 > 0:
                px[x, L] = rgb(int(lc[i1, s + x])); continue
            v = int(d['l2idx'][y, (s // 2 + x) % 512])
            if v == 0: px[x, L] = sky; continue
            if use_p1: v = remap[y][v]
            px[x, L] = sky if v == 0 else rgb(int(d['l2pal'][y][v - 1]))
    return im
for s in (areas[-1][1], areas[n // 2][1]):
    a, b = frame(s, False), frame(s, True)
    m = Image.eval(a.convert('L'), lambda v: v // 4).convert('RGB'); mp = m.load(); ap, bp = a.load(), b.load()
    cnt = 0
    for yy in range(LINES):
        for x in range(SW):
            dd = A.de(ap[x, yy], bp[x, yy])
            c = A.heat(dd, 2.0)
            if c: mp[x, yy] = c
            if dd >= 2 and yy >= 40: cnt += 1
    S = 2; out = Image.new('RGB', (3 * SW * S + 16, LINES * S + 20), (24, 24, 24))
    for i, im in enumerate((a, b, m)):
        out.paste(im.resize((SW * S, LINES * S), Image.NEAREST), (i * (SW * S + 8), 20))
    ImageDraw.Draw(out).text((4, 4), 'P1 en pantalla, s=%d: hoy (6 planos) | 5 planos (PF2 3 colores por fila) | dE2000  -  area dE>=2: %d px' % (s, cnt), fill=(255, 255, 0))
    out.save('work/arq0/p1_pantalla_s%d.png' % s); print('imagen s=%d area %d' % (s, cnt))
