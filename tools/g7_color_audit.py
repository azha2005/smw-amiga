#!/usr/bin/env python3
"""G7: audita colores de efectos frente a los intervalos PF1 existentes.

Preflight conservador de d8demote, no prueba un nuevo plan del copper ni
autoriza aproximaciones. Las fichas salen del 68000 real, no de su nombre.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

import dpfsplit as D
from g5l import GameRun
import mksprgfx as S
from palette import snes_to_amiga12
from sws_cmp import OAM_GROUPS


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin', required=True)
    ap.add_argument('--lst', required=True)
    ap.add_argument('--bank', default='work/g3/bank')
    ap.add_argument('--out', default='work/g7-colors')
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    vr, _, _ = S.build_vram(S._DEF_SRC, S.LEVEL)
    cg = S.level_cgram(S._DEF_SRC, S.LEVEL)
    fg = np.load('work/fg15.npy')
    ivs = [D.allocate(row, 48)[2] for row in fg]
    run = GameRun(a.bin, a.lst, a.bank)
    cpu, mem, sy, addr = run.cpu, run.mem, run.s, run.addr
    ram_at = addr('_ram')
    rows, bad, first = 0, 0, None
    photos = 0
    seen = set()
    for k in range(run.n):
        if k:
            run.fr.call(addr('dc_cop'), run.G.FAKE)
        ram = cpu.read(ram_at, 0x2000)
        cx = ram[0x1A] | ram[0x1B] << 8
        # PF1 actual usa la ventana fija 192..415 (S8 pendiente).
        cy = 192
        tiles = []
        for engine, groups in OAM_GROUPS.items():
            for start, n in groups:
                for entry in range(start, start + n):
                    x, y, tile, attr = ram[0x200 + 4*entry:0x204 + 4*entry]
                    hi = ram[0x420 + entry]
                    x |= (hi & 1) << 8
                    if x >= 256:
                        x -= 512
                    width = 16 if hi & 2 else 8
                    if y >= 224 or x + width <= 0 or x >= 256:
                        continue
                    key = (tile | (attr & 1) << 8, width, bool(attr & 64), bool(attr & 128))
                    pix = S.ficha(vr, *key)
                    pal = [snes_to_amiga12(cg[128 + 16*((attr >> 1) & 7) + i]) for i in range(16)]
                    if np.any(pix):
                        tiles.append((engine, entry, x, y, pix, pal))
        if not tiles:
            continue
        photos += 1
        for engine, entry, x, y, pix, pal in tiles:
            seen.add((int(ram[0x202 + 4*entry]), int(ram[0x203 + 4*entry]), len(pix)))
            xa, xb = max(0, x) + cx, min(255, x + len(pix) - 1) + cx
            for dy, row in enumerate(pix):
                if not 0 <= y + dy < 224 or not np.any(row):
                    continue
                cols = {pal[int(v)] for i, v in enumerate(row) if v and 0 <= x+i < 256}
                if not cols:
                    continue
                live = [iv for iv in ivs[cy+y+dy] if iv[4] is not None
                        and iv[0] <= xb+48 and iv[1]+48 >= xa]
                covered = {snes_to_amiga12(iv[2]) for iv in live if iv[0] <= xa and iv[1] >= xb}
                free = 7 - len({iv[4] for iv in live})
                missing = cols - covered
                rows += 1
                if len(missing) <= free:
                    continue
                bad += 1
                if first is None:
                    first = dict(k=k, engine=engine, entry=entry, camera_x=cx, x=x, y=y,
                                 dy=dy, colors=sorted(cols), covered=sorted(covered), free=free,
                                 missing=sorted(missing), terrain=[list(iv) for iv in live])
                    img = Image.new('RGB', (len(pix), len(pix)))
                    for iy, rr in enumerate(pix):
                        for ix, v in enumerate(rr):
                            c = pal[int(v)] if v else 0xF0F
                            img.putpixel((ix, iy), ((c >> 8)*17, ((c >> 4)&15)*17, (c&15)*17))
                    img.resize((256, 256), Image.Resampling.NEAREST).save(out / 'first-effect.png')
    result = dict(photos=photos, rows=rows, requires_replan=bad, first=first,
                  source_shapes=len(seen), gap=48,
                  scope='intervalos PF1 existentes; conservador, sin plan nuevo ni temporizacion')
    (out / 'report.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps(result, ensure_ascii=False), flush=True)
    print('G7 COLOR AUDIT: %d filas requieren estudiar otro plan' % bad)


if __name__ == '__main__':
    main()
