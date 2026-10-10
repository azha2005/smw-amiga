#!/usr/bin/env python3
"""SW-M: origen CGRAM de los píxeles; nunca deducirlo del color RGB."""
from pathlib import Path

import numpy as np

import lvdesc
import mklvl
from lvparse import _DEF_SRC
from map16 import Map16, TILESET_SET


def origin_mask(level=None, palette=6, color=4):
    """Máscara del color de una paleta, con Map16 por pantalla y flips."""
    desc = lvdesc.load(level)
    h, _, lv = mklvl.build(desc.obj, verbose=False, desc=desc)
    files = mklvl.gfx_files_for_tileset(h['tileset'])
    gfx = mklvl.load_gfx(str(Path(_DEF_SRC) / 'graphics'), files)
    m16 = Map16(set_index=TILESET_SET.get(h['tileset'], 0), tileset=h['tileset'])
    mask = np.zeros((lv.H * 16, lv.W * 16), dtype=bool)
    for gy in range(lv.H):
        for gx in range(lv.W):
            idx = lv.get(gx, gy)
            if idx is None or idx == 0:
                continue
            raw = m16.get_raw(idx, gx // 16)
            if raw is None:
                continue
            for q, (dx, dy) in enumerate(((0, 0), (0, 8), (8, 0), (8, 8))):
                rw = raw[q]
                if not rw or (rw >> 10 & 7) != palette:
                    continue
                tile = rw & 0x3ff
                block, within = divmod(tile, 128)
                if block >= len(files) or within >= len(gfx[files[block]]):
                    continue
                pixels = np.asarray(gfx[files[block]][within])
                if rw & 0x4000:
                    pixels = pixels[:, ::-1]
                if rw & 0x8000:
                    pixels = pixels[::-1]
                mask[gy * 16 + dy:gy * 16 + dy + 8,
                     gx * 16 + dx:gx * 16 + dx + 8] = pixels == color
    return mask


def event_origins(d, mask):
    """Por evento: es animado solo si TODOS sus píxeles vienen de CGRAM $64.

    Rechaza una asignación que fusionó un color estático con el animado.
    No acepta recolorear píxeles ajenos a la moneda.
    """
    import render_d
    idx = render_d.l1_index(d)
    out = []
    for y, events in enumerate(d['events']):
        flags = []
        for start, end, reg, _ in events:
            uses = idx[y, start:end + 1] == reg
            coins = mask[y, start:end + 1] & uses
            tagged = bool(coins.any())
            if tagged and (uses & ~mask[y, start:end + 1]).any():
                raise ValueError('SW-M: registro fusiona moneda y color fijo: y=%d x=%d..%d r=%d'
                                 % (y, start, end, reg))
            flags.append(tagged)
        out.append(flags)
    return out
