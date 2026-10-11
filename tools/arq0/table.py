# ARQ-0: tabla A/B de los BENCH de work/arq0/{b,p5,c<K>}_<tramo>/read.txt (comprueba los frames)
# uso: python tools/arq0/table.py [c8 bd48_192 ...]   (sondas de build_cut.sh)
import re, sys
from pathlib import Path
def LAB(k):
    if k.startswith('bd'): return '5 planos fuera de [%s, %s) (P1-V2)' % tuple(k[2:].split('_'))
    return '5 planos + %s MOVE/linea (P1-V)' % k[1:]
FR = dict(yi1=6312, back=4126, sprites=1914, hills2=2835, goal=2507)
def rd(p):
    t = Path(p).read_text(errors='replace') if Path(p).exists() else ''
    if 'sincronia        : OK' not in t: return None
    g = lambda pat: re.search(pat, t, re.M)
    fm = int(g(r'frames medidos\s*: (\d+)').group(1))
    part = lambda n: float(g(r'^%s\s+\d+\s+\d+\s+([\d.]+)%%' % re.escape(n)).group(1))
    lost = g(r'fotos perdidas\s*: (\d+) \(([\d.]+) %')
    return dict(fm=fm, lost=int(lost.group(1)), pct=float(lost.group(2)),
                racha=int(g(r'racha mas larga\s*: (\d+)').group(1)),
                media=float(g(r'total medio\s*: \d+ ticks = ([\d.]+)%').group(1)),
                lf=part('level_frame'), bm=part('build_mid'), rs=part('resto de scroll_frame'),
                col=part('columna (columns)'), ms=part('mspr_draw'), tot=part('total (hasta blitter libre)'))
print('| tramo | variante | fotos perdidas | racha | total medio | level_frame | build_mid | resto scroll | columns | mspr_draw | total |')
print('|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
for t in FR:
    for v, lab in [('b', '6 planos (hoy)'), ('p5', '5 planos (P1c)')] + [(k, LAB(k)) for k in sys.argv[1:]]:
        r = rd('work/arq0/%s_%s/read.txt' % (v, t))
        if r is None:
            print('| %s | %s | sin captura valida | | | | | | | | |' % (t, lab)); continue
        bad = '' if r['fm'] == FR[t] else ' **(frames %d != %d)**' % (r['fm'], FR[t])
        print('| %s | %s | %d/%d (%.2f %%)%s | %d | %.1f %% | %.1f %% | %.1f %% | %.1f %% | %.1f %% | %.1f %% | %.1f %% |' % (
            t, lab, r['lost'], r['fm'], r['pct'], bad, r['racha'], r['media'], r['lf'], r['bm'], r['rs'], r['col'], r['ms'], r['tot']))
