#!/usr/bin/env python3
"""G7-S0: ¿caben los efectos en sprites de hardware? (medida, no plan)

Por cada foto con efectos lee los flujos DMA reales de los ocho canales
(g7_hw_support.dma_image), la paleta COLOR17-31 y BPLCON2 por pixel
(sprite_palette) y la OAM de la foto. Cada ficha de efecto, en orden de
OAM, prueba las parejas adosadas 0/1, 2/3, 4/5 y 6/7:

  canal  la pareja no tiene tramo en [y0-1, y1] (una linea de margen para
         los controles de la cadena) ni otra ficha ya puesta ahi;
  color  cada pixel opaco tiene su color en algun COLOR17-31 vigente en
         esa fila y esa x (sin recargas nuevas);
  frente BPLCON2 deja la pareja delante del PF1 en todos sus pixeles;
Los pixeles que otro sprite ya tapa delante del PF1 (H.visibility) no se
ven en la referencia SNES: no se dibujan y no restringen el canal.

Cuenta ademas los pixeles en que dos efectos se solapan (ahi el orden
entre sus parejas tiene que respetar el de la OAM).
"""
import argparse
import collections
import json
from pathlib import Path

import numpy as np
import g5l as L
import g7_color_plan as P
import g7_hw_support as H
import g7_sources as B
from sws_cmp import OAM_GROUPS

ENTRIES = sorted({e for groups in OAM_GROUPS.values() for first, n in groups for e in range(first, first+n)})


def effect_entities(oam, bank):
    """[(entrada, y0, y1, x, mask, color)] de las fichas visibles con pixeles."""
    import struct
    pals = struct.unpack_from('>128H', bank, B.PALETTE)
    out = []
    for e in ENTRIES:
        x, y, t, attr = oam[4*e:4*e+4]
        hi = oam[256+e]
        x |= (hi & 1) << 8
        if x >= 256:
            x -= 512
        width = 16 if hi & 2 else 8
        y += 1
        if y >= 224 or x+width <= 0 or x >= 256:
            continue
        px = np.array(B.ficha(bank, t | (attr & 1) << 8, width, bool(attr & 64), bool(attr & 128)))
        color = np.full((224, 256), -1, dtype=np.int32)
        for dy in range(width):
            if not 0 <= y+dy < 224:
                continue
            for dx in range(width):
                v = px[dy, dx]
                if v and 0 <= x+dx < 256:
                    color[y+dy, x+dx] = pals[16*((attr >> 1) & 7)+v]
        mask = color >= 0
        if mask.any():
            rows = np.flatnonzero(mask.any(axis=1))
            out.append((e, int(rows[0]), int(rows[-1])+1, x, mask, color))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin', required=True)
    ap.add_argument('--lst', required=True)
    ap.add_argument('--sources', default='work/g7/sources.bin')
    ap.add_argument('--to-k', type=int, default=99999)
    ap.add_argument('--out', required=True)
    ap.add_argument('--single', action='store_true', help='probar tambien canales sueltos de 3 colores')
    ap.add_argument('--pack', action='store_true', help='juntar fichas que caben en 16 px en un mismo sprite')
    a = ap.parse_args()
    bank = Path(a.sources).read_bytes()
    g = L.GameRun(a.bin, a.lst, 'work/g3/bank')
    s, mem, cpu = g.s, g.mem, g.cpu
    st = collections.Counter()
    why = collections.Counter()
    pairs_used = collections.Counter()
    bad_photos = []
    pf1_rows, full_rows = [], []
    heavy = []
    for k in range(min(g.n, a.to_k+1)):
        if k:
            g.fr.call(g.addr('dc_cop'), g.G.FAKE)
        rec, back = P.render_step(g)
        if mem.r8(rec+s['R_SWS_VALID']):
            ents = effect_entities(cpu.read(rec+s['R_OAM'], 320), bank)
            if ents:
                image, audit = H.dma_image(g, rec, back)
                palette, front = H.sprite_palette(g, back)
                busy = {p: [] for p in (0, 2, 4, 6)}
                for flow in audit:
                    for sp in flow['spans']:
                        busy[flow['channel'] & 6].append((sp['start'], sp['stop']))
                hidden = H.visibility(g, rec, back)
                placed = np.zeros((224, 256), dtype=bool)
                left_rows = np.zeros(224, dtype=bool)
                objs = []
                photo_why = []
                all_rows = np.zeros(224, dtype=bool)
                for _, _, _, _, m0, _ in ents:
                    all_rows |= (m0 & ~hidden).any(axis=1)
                st['photos'] += 1
                photo_ok = True
                for e, y0, y1, x, mask, color in ents:
                    st['entities'] += 1
                    st['pixels'] += int(mask.sum())
                    st['over_sprite_px'] += int(np.count_nonzero(mask & (image != 0)))
                    # Lo que otro sprite ya tapa no se ve (referencia SNES):
                    # no se dibuja, y el orden entre canales no importa ahi.
                    vis = mask & ~hidden
                    if not vis.any():
                        st['entities_hidden'] += 1
                        continue
                    rows = np.flatnonzero(vis.any(axis=1))
                    y0, y1 = int(rows[0]), int(rows[-1])+1
                    yy, xx = np.nonzero(vis)
                    cc = color[yy, xx]
                    have = np.any(palette[yy, 1:, xx] == cc[:, None], axis=1)
                    color_ok = bool(have.all())
                    st['ent_overlap_px'] += int(np.count_nonzero(vis & placed))
                    placed |= vis
                    got = None
                    reason = 'canal'
                    vx0, vx1 = int(xx.min()), int(xx.max())

                    def fits(kind, n, ya, yb, skip=None):
                        p = n & 6
                        chans = (n,) if kind == 's' else (n, n+1)
                        spans = list(busy[p])
                        for o in objs:
                            if o is not skip and set(o['ch']) & set(chans):
                                spans.append((o['y0'], o['y1']))
                        if any(s0 < yb+1 and ya-1 < s1 for s0, s1 in spans):
                            return 'canal'
                        if not np.all(front[yy, xx] > p//2):
                            return 'frente'
                        if kind == 's':
                            base = 1 + 2*p
                            if not np.all(np.any(palette[yy, base:base+3, xx] == cc[:, None], axis=1)):
                                return 'color'
                        elif not color_ok:
                            return 'color'
                        return None
                    # 1) Sumarse a un sprite propio si todo cabe en 16 px.
                    if a.pack:
                        for o in objs:
                            if max(o['x1'], vx1)-min(o['x0'], vx0) >= 16:
                                continue
                            ya, yb = min(o['y0'], y0), max(o['y1'], y1)
                            if fits(o['kind'], o['ch'][0], ya, yb, skip=o) is None:
                                o.update(y0=ya, y1=yb, x0=min(o['x0'], vx0), x1=max(o['x1'], vx1))
                                got = ('m', o['ch'][0])
                                st['packed'] += 1
                                break
                    # 2) Canal suelto (3 colores), 3) pareja adosada (15).
                    tries = ([('s', ch) for ch in range(8)] if a.single else [])+[('p', p) for p in (0, 2, 4, 6)]
                    for kind, n in tries if got is None else []:
                        r = fits(kind, n, y0, y1)
                        if r is None:
                            got = (kind, n)
                            objs.append(dict(kind=kind, ch=(n,) if kind == 's' else (n, n+1),
                                             y0=y0, y1=y1, x0=vx0, x1=vx1))
                            break
                        if kind == 'p' and reason == 'canal':
                            reason = r
                    if got is None:
                        left_rows |= vis.any(axis=1)
                        photo_why.append((e, reason, y0, y1, x))
                        why[reason] += 1
                        st['entities_fail'] += 1
                        st['pixels_fail'] += int(mask.sum())
                        photo_ok = False
                    else:
                        pairs_used['%s%d' % got] += 1
                pf1_rows.append(int(left_rows.sum()))
                if left_rows.sum() >= 10:
                    heavy.append(dict(k=k, rows=int(left_rows.sum()), fail=photo_why))
                full_rows.append(int(all_rows.sum()))
                if not photo_ok:
                    st['photos_fail'] += 1
                    if len(bad_photos) < 400:
                        bad_photos.append(k)
        P.finish_step(g, rec, back)
        if k and k % 1000 == 0:
            print(k, dict(st), dict(why), flush=True)
    def dist(v):
        v = np.array(v or [0])
        return dict(mean=round(float(v.mean()), 2), p99=float(np.percentile(v, 99)), max=int(v.max()),
                    total=int(v.sum()))
    st_rows = dict(pf1_only=dist(full_rows), hybrid_left=dist(pf1_rows))
    res = dict(stats=dict(st), why=dict(why), pairs=dict(pairs_used), rows=st_rows, bad_photos=bad_photos, heavy=heavy)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, indent=1), encoding='utf8')
    print('G7 SPRITE ROOM: '+json.dumps(dict(stats=dict(st), why=dict(why), pairs=dict(pairs_used))), flush=True)
    print('filas PF1 por foto con efectos: '+json.dumps(st_rows), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
