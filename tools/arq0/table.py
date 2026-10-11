# ARQ-0: tabla A/B de los BENCH de work/arq0/{b,p5}_<tramo>/read.txt (comprueba los frames)
import re, sys
from pathlib import Path
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
    for v, lab in (('b', '6 planos (hoy)'), ('p5', '5 planos (P1c)')):
        r = rd('work/arq0/%s_%s/read.txt' % (v, t))
        if r is None:
            print('| %s | %s | sin captura valida | | | | | | | | |' % (t, lab)); continue
        bad = '' if r['fm'] == FR[t] else ' **(frames %d != %d)**' % (r['fm'], FR[t])
        print('| %s | %s | %d/%d (%.2f %%)%s | %d | %.1f %% | %.1f %% | %.1f %% | %.1f %% | %.1f %% | %.1f %% | %.1f %% |' % (
            t, lab, r['lost'], r['fm'], r['pct'], bad, r['racha'], r['media'], r['lf'], r['bm'], r['rs'], r['col'], r['ms'], r['tot']))
