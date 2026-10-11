#!/usr/bin/env python3
"""ARQ-0 paso 0: la vara de "se nota" contra la SNES.

Compara capturas de WinUAE con la pantalla de la SNES del mismo frame del
oraculo (snesorc --shots) y da, por foto y en conjunto:

  - % de pixeles distintos con el color de 12 bits de la Amiga (la base
    1:1 es la SNES cuantizada a 12 bits, snes_to_amiga12, no a 15);
  - CIEDE2000 por pixel sobre el color mostrado (sRGB del registro de 12
    bits contra el de la SNES cuantizada): media, p99, maximo y AREA con
    dE >= umbral (2 por defecto: "se nota", a confirmar con el usuario);
  - informativo: el piso de la cuantizacion 15 -> 12 bits (dE de la SNES
    de 15 bits contra la SNES de 12), que ningun recorte del port puede
    bajar;
  - una imagen SNES | Amiga | mapa de dE para que el usuario juzgue.

Alineacion: fila Amiga y = fila SNES y - 1 (P128; --dy para otra). La
barra de estado (filas 0-39, sin portar, D11) se informa aparte: las
metricas "juego" la excluyen.

Entradas: un directorio con el formato de sweep_cmp.py (pairs.json,
shots/k*.png, snes/snes_<f>.ppm) o un par suelto.

  python tools/arq_diff.py --dir work/sw1/yi1 --out work/arq0/base_yi1
  python tools/arq_diff.py --snes a.ppm --amiga b.png --out work/arq0/par
  python tools/arq_diff.py --selftest
"""
import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import sweep_cmp as SW                  # noqa: E402  (captura, alineacion, 12 bits)

ROWS, COLS, HUD_ROWS = SW.ROWS, SW.COLS, SW.HUD_ROWS


# ----------------------------------------------------------------------
# color: sRGB -> Lab (D65) y CIEDE2000
# ----------------------------------------------------------------------
def _lin(c):
    c /= 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


_LAB = {}


def lab(rgb):
    v = _LAB.get(rgb)
    if v is None:
        r, g, b = (_lin(float(c)) for c in rgb)
        x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
        y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
        z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

        def f(t):
            return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116
        fx, fy, fz = f(x), f(y), f(z)
        v = _LAB[rgb] = (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))
    return v


def ciede2000(l1, l2):
    """Sharma, Wu y Dalal (2005), kL = kC = kH = 1"""
    L1, a1, b1 = l1
    L2, a2, b2 = l2
    c1, c2 = math.hypot(a1, b1), math.hypot(a2, b2)
    cm7 = ((c1 + c2) / 2) ** 7
    g = 0.5 * (1 - math.sqrt(cm7 / (cm7 + 25 ** 7)))
    a1p, a2p = (1 + g) * a1, (1 + g) * a2
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if c1p else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if c2p else 0.0
    dL, dC = L2 - L1, c2p - c1p
    if c1p * c2p == 0:
        dh = 0.0
    else:
        dh = h2p - h1p
        if dh > 180:
            dh -= 360
        elif dh < -180:
            dh += 360
    dH = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dh / 2))
    Lm, Cm = (L1 + L2) / 2, (c1p + c2p) / 2
    if c1p * c2p == 0:
        hm = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hm = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hm = (h1p + h2p + 360) / 2
    else:
        hm = (h1p + h2p - 360) / 2
    t = (1 - 0.17 * math.cos(math.radians(hm - 30)) + 0.24 * math.cos(math.radians(2 * hm))
         + 0.32 * math.cos(math.radians(3 * hm + 6)) - 0.20 * math.cos(math.radians(4 * hm - 63)))
    sl = 1 + 0.015 * (Lm - 50) ** 2 / math.sqrt(20 + (Lm - 50) ** 2)
    sc = 1 + 0.045 * Cm
    sh = 1 + 0.015 * Cm * t
    cm7 = Cm ** 7
    rt = -2 * math.sqrt(cm7 / (cm7 + 25 ** 7)) * math.sin(math.radians(60 * math.exp(-((hm - 275) / 25) ** 2)))
    return math.sqrt((dL / sl) ** 2 + (dC / sc) ** 2 + (dH / sh) ** 2 + rt * (dC / sc) * (dH / sh))


_DE = {}


def de(p, q):
    if p == q:
        return 0.0
    k = (p, q)
    v = _DE.get(k)
    if v is None:
        v = _DE[k] = ciede2000(lab(p), lab(q))
    return v


# ----------------------------------------------------------------------
# una foto
# ----------------------------------------------------------------------
def snes_both(img):
    """la PPU guarda 5 bits << 3: el color mostrado de 15 bits y el de 12"""
    import g5l as L
    from palette import snes_to_amiga12
    raw = img.convert('RGB').tobytes()
    s15, s12 = [], []
    for i in range(0, len(raw), 3):
        r, g, b = raw[i] >> 3, raw[i + 1] >> 3, raw[i + 2] >> 3
        s15.append(((r * 255 + 15) // 31, (g * 255 + 15) // 31, (b * 255 + 15) // 31))
        s12.append(L.rgb12(snes_to_amiga12(r | g << 5 | b << 10)))
    return s15, s12


def pct(vals, q):
    if not vals:
        return 0.0
    s = sorted(vals)
    return s[min(len(s) - 1, int(math.ceil(q * len(s))) - 1)]


def measure(s15, s12, am, dy, thr):
    """metricas de una foto; devuelve (dict, mapa de dE fila Amiga)"""
    dmap = [0.0] * (ROWS * COLS)
    reg = {'juego': dict(n=0, dist=0, des=[], floor=0.0),
           'todo': dict(n=0, dist=0, des=[], floor=0.0)}
    for y in range(ROWS):
        ys = y + dy
        if not 0 <= ys < ROWS:
            continue
        zones = (reg['todo'], reg['juego']) if y >= HUD_ROWS else (reg['todo'],)
        for x in range(COLS):
            i, j = y * COLS + x, ys * COLS + x
            a, s = am[i], s12[j]
            d = de(s, a)
            dmap[i] = d
            fl = de(s15[j], s)
            for z in zones:
                z['n'] += 1
                z['floor'] += fl
                if a != s:
                    z['dist'] += 1
                    z['des'].append(d)
    out = {}
    for name, z in reg.items():
        n, ds = z['n'], z['des']
        area = sum(1 for v in ds if v >= thr)
        out[name] = dict(px=n, distintos=z['dist'], pct_distintos=round(100.0 * z['dist'] / n, 4),
                         de_media=round(sum(ds) / n, 5), de_p99=round(pct(ds + [0.0] * (n - len(ds)), 0.99), 4),
                         de_max=round(max(ds, default=0.0), 4),
                         area=area, pct_area=round(100.0 * area / n, 4),
                         piso_12bit=round(z['floor'] / n, 5))
    return out, dmap


def heat(d, thr):
    if d == 0:
        return None
    if d < thr:
        return (0, 160, 255)            # distinto pero bajo el umbral
    if d < 5:
        return (255, 200, 0)
    if d < 15:
        return (255, 100, 0)
    return (255, 0, 255)


def panel(s12, am, dmap, dy, title, thr):
    from PIL import Image, ImageDraw
    a = Image.new('RGB', (COLS, ROWS))
    a.putdata(am)
    s = Image.new('RGB', (COLS, ROWS))
    s.putdata([s12[min(max(y + dy, 0), ROWS - 1) * COLS + x] for y in range(ROWS) for x in range(COLS)])
    m = Image.eval(a.convert('L'), lambda v: v // 4).convert('RGB')
    px = m.load()
    for i, d in enumerate(dmap):
        c = heat(d, thr)
        if c:
            px[i % COLS, i // COLS] = c
    W = 2
    out = Image.new('RGB', (3 * COLS * W + 16, ROWS * W + 34), (24, 24, 24))
    for i, im in enumerate((s, a, m)):
        out.paste(im.resize((COLS * W, ROWS * W), Image.NEAREST), (i * (COLS * W + 8), 18))
    dr = ImageDraw.Draw(out)
    dr.text((4, 3), title, fill=(255, 255, 0))
    y = ROWS * W + 20
    dr.text((4, y), 'SNES (12 bits) | Amiga | dE2000:', fill=(200, 200, 200))
    x = 230
    for lab_, c in (('< %g' % thr, (0, 160, 255)), ('%g-5' % thr, (255, 200, 0)),
                    ('5-15', (255, 100, 0)), ('>= 15', (255, 0, 255))):
        dr.rectangle((x, y + 2, x + 9, y + 11), fill=c)
        dr.text((x + 13, y), lab_, fill=(200, 200, 200))
        x += 80
    dr.line((2 * COLS * W + 16, 18 + HUD_ROWS * W, 3 * COLS * W + 15, 18 + HUD_ROWS * W), fill=(80, 80, 80))
    return out


def shot_ok(img):
    """la ventana entera: una captura minimizada (199x34) no se mide"""
    import g5l as L
    return img.size[0] >= L.SHOT_BOX[2] and img.size[1] >= L.SHOT_BOX[3]


def one(snes_path, amiga_path, dy, thr):
    from PIL import Image
    s15, s12 = snes_both(Image.open(snes_path))
    shot = Image.open(amiga_path)
    if not shot_ok(shot):
        return None, None
    am, rara = SW.amiga_px(shot)
    m, dmap = measure(s15, s12, am, dy, thr)
    m['muestreo_raro'] = rara
    return m, (s12, am, dmap)


# ----------------------------------------------------------------------
# conjunto
# ----------------------------------------------------------------------
def summary(rows, zone):
    zs = [r[zone] for r in rows]
    n = len(zs)
    return dict(fotos=n,
                exactas=sum(1 for z in zs if not z['distintos']),
                sin_area=sum(1 for z in zs if not z['area']),
                pct_distintos_media=round(sum(z['pct_distintos'] for z in zs) / n, 4),
                de_media=round(sum(z['de_media'] for z in zs) / n, 5),
                de_p99_peor=max(z['de_p99'] for z in zs),
                de_max=max(z['de_max'] for z in zs),
                area_media_px=round(sum(z['area'] for z in zs) / n, 1),
                area_peor_px=max(z['area'] for z in zs),
                pct_area_media=round(sum(z['pct_area'] for z in zs) / n, 4),
                piso_12bit=round(sum(z['piso_12bit'] for z in zs) / n, 5))


def run_dir(a):
    d = Path(a.dir)
    out = Path(a.out)
    (out / 'img').mkdir(parents=True, exist_ok=True)
    pairs = json.loads((d / 'pairs.json').read_text())
    if a.k:
        want = set(a.k)
        pairs = [p for p in pairs if p['k'] in want]
    rows, kept, malas = [], {}, []
    for p in pairs:
        sp = d / 'snes' / ('snes_%d.ppm' % p['f'])
        ap_ = d / 'shots' / ('k%05d.png' % p['k'])
        if not (sp.exists() and ap_.exists()):
            continue
        m, data = one(sp, ap_, a.dy, a.thr)
        if m is None:
            malas.append(p['k'])
            continue
        m.update(k=p['k'], f=p['f'])
        rows.append(m)
        if a.all_img:
            kept[p['k']] = data
        else:
            kept[p['k']] = None
        j = m['juego']
        print('k %5d f %5d  juego: distintos %5d (%6.3f %%)  dE media %.4f p99 %.2f max %5.1f  area>=%g %5d'
              % (p['k'], p['f'], j['distintos'], j['pct_distintos'], j['de_media'], j['de_p99'],
                 j['de_max'], a.thr, j['area']), flush=True)
    if not rows:
        sys.exit('no hay pares en %s' % d)
    worst = sorted(rows, key=lambda r: (-r['juego']['area'], -r['juego']['distintos']))[:a.top]
    for r in worst if not a.all_img else rows:
        data = kept.get(r['k'])
        if data is None:
            _, data = one(d / 'snes' / ('snes_%d.ppm' % r['f']), d / 'shots' / ('k%05d.png' % r['k']), a.dy, a.thr)
        j = r['juego']
        t = 'k %d  f %d   juego: %d px distintos (%.2f %%), area dE>=%g: %d px, dE max %.1f' % (
            r['k'], r['f'], j['distintos'], j['pct_distintos'], a.thr, j['area'], j['de_max'])
        panel(*data, a.dy, t, a.thr).save(out / 'img' / ('k%05d.png' % r['k']))
    if malas:
        print('AVISO: %d capturas de tamano equivocado, sin medir: %s' % (len(malas), ' '.join(map(str, malas))))
    res = dict(origen=str(d), alineacion=a.dy, umbral=a.thr, hud_rows=HUD_ROWS, sin_medir=malas,
               juego=summary(rows, 'juego'), todo=summary(rows, 'todo'),
               peores=[r['k'] for r in worst], fotos=rows)
    (out / 'arq_diff.json').write_text(json.dumps(res, indent=1))
    for z in ('juego', 'todo'):
        s = res[z]
        print('%-5s %d fotos: %d exactas, %d sin area; distintos %.3f %%; dE media %.4f (piso 12 bits %.4f); '
              'p99 peor %.2f; max %.1f; area media %.1f px, peor %d px'
              % (z, s['fotos'], s['exactas'], s['sin_area'], s['pct_distintos_media'], s['de_media'],
                 s['piso_12bit'], s['de_p99_peor'], s['de_max'], s['area_media_px'], s['area_peor_px']))
    print('peores (area, juego): %s  -> %s' % (' '.join(map(str, res['peores'])), out / 'img'))


def run_pair(a):
    m, data = one(a.snes, a.amiga, a.dy, a.thr)
    if m is None:
        sys.exit('captura de tamano equivocado: %s' % a.amiga)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    j = m['juego']
    panel(*data, a.dy, 'juego: %d px distintos, area dE>=%g: %d px' % (j['distintos'], a.thr, j['area']),
          a.thr).save(out / 'par.png')
    (out / 'arq_diff.json').write_text(json.dumps(m, indent=1))
    print(json.dumps(m, indent=1))


def gate(a):
    """puerta del paso 0: las fotos que sweep_cmp cuenta exactas fuera de la
    barra dan 0 aqui (distintos, dE y area), y en todas las fotos el
    recuento de 12 bits es el de sweep_cmp"""
    from PIL import Image
    d = Path(a.dir)
    pairs = json.loads((d / 'pairs.json').read_text())
    bad = n = ex = 0
    for p in pairs:
        sp = d / 'snes' / ('snes_%d.ppm' % p['f'])
        ap_ = d / 'shots' / ('k%05d.png' % p['k'])
        if not (sp.exists() and ap_.exists()):
            continue
        if not shot_ok(Image.open(ap_)):
            print('k %d: captura de tamano equivocado, sin medir' % p['k'])
            continue
        n += 1
        sn = SW.snes12(Image.open(sp).convert('RGB'))
        am, _ = SW.amiga_px(Image.open(ap_))
        ref = SW.diff_rows(sn, am, a.dy)
        rj = sum(1 for q in ref if q[1] >= HUD_ROWS)
        m, _ = one(sp, ap_, a.dy, a.thr)
        j = m['juego']
        ok = j['distintos'] == rj and m['todo']['distintos'] == len(ref)
        if rj == 0:
            ex += 1
            ok = ok and j['de_max'] == 0 and j['area'] == 0
        if not ok:
            bad += 1
            print('k %d: sweep_cmp %d/%d, arq_diff %d/%d dE max %.2f' % (
                p['k'], rj, len(ref), j['distintos'], m['todo']['distintos'], j['de_max']))
    print('puerta arq_diff: %d fotos, %d exactas segun sweep_cmp, %d fallos' % (n, ex, bad))
    sys.exit(1 if bad or not ex else 0)


def selftest():
    # Sharma, Wu y Dalal (2005), tabla 1: pares 1, 2, 3, 7, 17, 18 y 25
    for l1, l2, want in (((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485), 2.0425),
                         ((50.0, 3.1571, -77.2803), (50.0, 0.0, -82.7485), 2.8615),
                         ((50.0, 2.8361, -74.0200), (50.0, 0.0, -82.7485), 3.4412),
                         ((50.0, 0.0, 0.0), (50.0, -1.0, 2.0), 2.3669),
                         ((50.0, 2.5, 0.0), (73.0, 25.0, -18.0), 27.1492),
                         ((50.0, 2.5, 0.0), (61.0, -5.0, 29.0), 22.8977),
                         ((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387), 1.2644)):
        got = ciede2000(l1, l2)
        assert abs(got - want) < 1e-4, (l1, l2, got, want)
        assert abs(ciede2000(l2, l1) - want) < 1e-4
    w = lab((255, 255, 255))
    assert abs(w[0] - 100) < 1e-3 and abs(w[1]) < 1e-2 and abs(w[2]) < 1e-2, w
    # una foto contra si misma = 0; un pixel cambiado = 1 distinto y su dE
    import random
    random.seed(2)
    s12 = [(random.randrange(16) * 17, random.randrange(16) * 17, random.randrange(16) * 17)
           for _ in range(ROWS * COLS)]
    s15 = list(s12)
    am = [s12[min(max(y - 1, 0), ROWS - 1) * COLS + x] for y in range(ROWS) for x in range(COLS)]
    m, dmap = measure(s15, s12, am, -1, 2.0)
    assert m['juego']['distintos'] == 0 and m['juego']['de_max'] == 0 and m['juego']['area'] == 0, m
    i = 100 * COLS + 30
    old = am[i]
    am[i] = (255, 255, 255) if old != (255, 255, 255) else (0, 0, 0)
    m, dmap = measure(s15, s12, am, -1, 2.0)
    assert m['juego']['distintos'] == 1 and m['todo']['distintos'] == 1
    assert abs(m['juego']['de_max'] - de(old, am[i])) < 1e-4 and dmap[i] > 0
    assert m['juego']['area'] == (1 if dmap[i] >= 2 else 0)
    print('arq_diff selftest: OK')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--gate', action='store_true', help='puerta contra sweep_cmp (con --dir)')
    ap.add_argument('--dir', help='directorio de sweep_cmp (pairs.json, shots/, snes/)')
    ap.add_argument('--snes', help='un par suelto: la pantalla de la SNES (.ppm)')
    ap.add_argument('--amiga', help='un par suelto: la captura de WinUAE (.png)')
    ap.add_argument('--out', default='work/arq0/diff')
    ap.add_argument('--dy', type=int, default=-1, help='fila Amiga y = fila SNES y + dy (P128: -1)')
    ap.add_argument('--thr', type=float, default=2.0, help='umbral de dE2000 para el area')
    ap.add_argument('--top', type=int, default=12, help='imagenes de las peores fotos')
    ap.add_argument('--all-img', action='store_true', help='una imagen por foto')
    ap.add_argument('--k', type=int, nargs='*', help='solo estas fotos')
    a = ap.parse_args()
    if a.selftest:
        selftest()
    elif a.gate and a.dir:
        gate(a)
    elif a.dir:
        run_dir(a)
    elif a.snes and a.amiga:
        run_pair(a)
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
