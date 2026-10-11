# ARQ-0 (docs/informe-arq-0-1011.md): P1(a)(b): colores de la capa 2 por fila y ventana; mejor terna
# correr desde la raiz: python tools/arq0/p1a.py
import sys, itertools, collections
sys.path.insert(0, 'tools')
from PIL import Image
import arq_diff as A
im = Image.open('work/bg_mountains.png').convert('RGB'); W, H = im.size; px = im.load()
SKY = (0, 99, 189)
rows = [[px[x, y] for x in range(W)] for y in range(H)]
def q12(c):  # el color tal como lo muestra la Amiga
    return tuple(((v >> 3) >> 1) * 17 for v in c)
hist = collections.Counter(); worst_rows = collections.Counter()
used_rows = 0
for y, r in enumerate(rows):
    if all(c == SKY for c in r): continue
    used_rows += 1
    m = 0
    for x0 in range(W):
        n = len({r[(x0 + i) % W] for i in range(256)} - {SKY})
        hist[n] += 1; m = max(m, n)
    worst_rows[m] += 1
tot = sum(hist.values())
print('filas con algo de capa 2: %d de %d' % (used_rows, H))
print('colores (sin cielo) por linea y ventana de 256 px:', ' '.join('%d:%.1f%%' % (k, 100 * v / tot) for k, v in sorted(hist.items())))
print('filas segun su peor ventana:', dict(sorted(worst_rows.items())))
# (b) mejor terna fija por fila (toda la fila de 512) y por ventana: pixel -> el mas cercano en dE
def best3(cols_cnt):
    cs = [c for c in cols_cnt if c != SKY]
    if len(cs) <= 3: return tuple(cs), 0.0, 0
    best = None
    for t in itertools.combinations(cs, 3):
        pal = list(t) + [SKY]
        e = n2 = 0
        for c, n in cols_cnt.items():
            d = min(A.de(q12(c), q12(p)) for p in pal)
            e += d * n
            if d >= 2: n2 += n
        if best is None or e < best[1]: best = (t, e, n2)
    return best
tot_px = tot_e = tot_area = 0
for y, r in enumerate(rows):
    cnt = collections.Counter(r)
    t, e, n2 = best3(cnt)
    nonsky = sum(n for c, n in cnt.items() if c != SKY)
    tot_px += nonsky; tot_e += e; tot_area += n2
print('terna FIJA por fila: dE medio sobre px de capa 2 (sin cielo) %.3f; px con dE>=2: %d de %d (%.2f %%)' % (tot_e / tot_px, tot_area, tot_px, 100 * tot_area / tot_px))
# por ventana (la peor y la media), muestreando x0 cada 8
we = []; warea = []
for x0 in range(0, W, 8):
    e = a = n = 0
    for r in rows:
        cnt = collections.Counter(r[(x0 + i) % W] for i in range(256))
        t, ee, n2 = best3(cnt)
        e += ee; a += n2; n += sum(v for c, v in cnt.items() if c != SKY)
    we.append(e / n); warea.append((a, n, x0))
print('terna por fila Y ventana: dE medio %.3f (peor ventana %.3f); px dE>=2 peor ventana %d de %d (x0=%d)' % (sum(we) / len(we), max(we), *max(warea)))
