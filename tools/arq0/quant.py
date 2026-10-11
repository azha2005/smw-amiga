# ARQ-0 (docs/informe-arq-0-1011.md): piso de 12 bits (truncar, redondear, el mejor por dE)
# correr desde la raiz: python tools/arq0/quant.py
import sys, collections
sys.path.insert(0, 'tools')
from pathlib import Path
from PIL import Image
import arq_diff as A
cnt = collections.Counter()
for p in sorted(Path('work/sw1/yi1/snes').glob('snes_*.ppm')):
    if '_no_' in p.name: continue
    im = Image.open(p).convert('RGB').crop((0, 40, 256, 224))
    for n, c in im.getcolors(1 << 16):
        cnt[(c[0] >> 3, c[1] >> 3, c[2] >> 3)] += n
tot = sum(cnt.values())
def disp5(c): return tuple((v * 255 + 15) // 31 for v in c)
grid = [(r * 17, g * 17, b * 17) for r in range(16) for g in range(16) for b in range(16)]
glab = [(g, A.lab(g)) for g in grid]
tr = rd = ne = 0.0; worst = []
for c, n in cnt.items():
    L = A.lab(disp5(c))
    t = A.ciede2000(L, A.lab(tuple((v >> 1) * 17 for v in c)))
    r = A.ciede2000(L, A.lab(tuple(min(15, (v * 15 + 15) // 31) * 17 for v in c)))
    best = min(A.ciede2000(L, gl) for _, gl in glab)
    tr += t * n; rd += r * n; ne += best * n
    worst.append((t * n, c, t, r, best))
print('colores distintos', len(cnt), 'px', tot)
print('dE medio: truncar (hoy) %.3f | redondear %.3f | el 12 bits mas cercano en dE %.3f' % (tr / tot, rd / tot, ne / tot))
for w in sorted(worst, reverse=True)[:8]:
    print('  color5 %s peso %.0f  truncar %.2f redondear %.2f mejor %.2f' % (w[1], w[0], w[2], w[3], w[4]))
