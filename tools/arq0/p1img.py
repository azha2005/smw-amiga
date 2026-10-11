# ARQ-0 (docs/informe-arq-0-1011.md): P1: imagen de la capa 2 sola, ventana x0=136
# correr desde la raiz: python tools/arq0/p1img.py
import sys, itertools, collections
sys.path.insert(0, 'tools')
from PIL import Image, ImageDraw
import arq_diff as A
im = Image.open('work/bg_mountains.png').convert('RGB'); W, H = im.size; px = im.load()
SKY = (0, 99, 189); X0 = 136
def q12(c): return tuple(((v >> 3) >> 1) * 17 for v in c)
o = Image.new('RGB', (256, H)); p = Image.new('RGB', (256, H)); m = Image.new('RGB', (256, H))
for y in range(H):
    r = [px[(X0 + i) % W, y] for i in range(256)]
    cnt = collections.Counter(r); cs = [c for c in cnt if c != SKY]
    pal = cs if len(cs) <= 3 else None
    if pal is None:
        pal = min(itertools.combinations(cs, 3), key=lambda t: sum(min(A.de(q12(c), q12(k)) for k in list(t) + [SKY]) * n for c, n in cnt.items()))
    pal = list(pal) + [SKY]
    for x, c in enumerate(r):
        nc = min(pal, key=lambda k: A.de(q12(c), q12(k)))
        o.putpixel((x, y), q12(c)); p.putpixel((x, y), q12(nc))
        d = A.de(q12(c), q12(nc))
        m.putpixel((x, y), A.heat(d, 2.0) or tuple(v // 4 for v in q12(c)))
S = 2
out = Image.new('RGB', (3 * 256 * S + 16, H * S + 20), (24, 24, 24))
for i, x in enumerate((o, p, m)):
    out.paste(x.resize((256 * S, H * S), Image.NEAREST), (i * (256 * S + 8), 20))
ImageDraw.Draw(out).text((4, 4), 'P1: capa 2 de YI1, ventana x0=%d (la peor). 7 colores (hoy) | 3 por fila (5 planos) | dE2000' % X0, fill=(255, 255, 0))
out.save('work/arq0/p1_capa2_x136.png')
