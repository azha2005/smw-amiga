#!/usr/bin/env python3
"""SW-B: inventario exacto de reemplazos Map16 con los registros de PF1.

No aproxima colores: cada pixel nuevo debe poder usar un registro que ya
tenga su color en esa posicion. Los rechazos conservan coordenadas y color.
"""
import collections
import json
import os
import struct
import numpy as np
import lvdesc
import mklvl
import mkleveld
import palette
import render_d
import smwgen
from map16 import Map16, TILESET_SET

PG0 = [0x25, 0x25, 0x25, 0x06, 0x49, 0x48, 0x2B, 0xA2, 0xC6]
PG1 = [0x152, 0x11B, 0x123, 0x11E, 0x132, 0x113, 0x115,
       0x116, 0x12B, 0x12C, 0x112, 0x168, 0x169, 0x132, 0x15E]


def active_colors(events, width):
    """Solo intervalos que obligan al copper a conservar el color.

    Un registro en el hueco entre eventos NO es una reserva: la carga
    puede adelantarse en ese hueco y el borrado toma el evento siguiente.
    """
    out = np.full((8, width), -1, np.int32)
    for start, end, reg, color in events:
        out[reg, start:end + 1] = color
    return out


def results(tile, final):
    """Llamadores de GenerateTile en mcoll.c (F160/F309/F2C9)."""
    if tile in (0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x6E, 0x38):
        return [0x25]
    if 0x111 <= tile < 0x12E:
        kind = tile - 0x111
        end = final[kind]
        values = {0x152, PG0[end] if end <= 8 else PG1[end - 9]}
        if tile == 0x11E:
            values.add(0x25)
            values.add(0x48)                 # blocks_update: fase atravesable del giro
        # MultiCoinBlkTimer puede terminar el bloque como usado ($132).
        if end in (0x0A, 0x0B):
            values.add(0x132)
        return sorted(values)
    return []


class Tiles:
    def __init__(self, header):
        self.files = mklvl.gfx_files_for_tileset(header['tileset'])
        self.gfx = mklvl.load_gfx(os.path.join(mklvl._DEF_SRC, 'graphics'), self.files)
        self.m16 = Map16(set_index=TILESET_SET.get(header['tileset'], 0), tileset=header['tileset'])
        bank, labels = palette.load_palette_bank(os.path.join(mklvl._DEF_SRC, 'palettes', 'palettes.a'))
        self.cgram, _ = palette.build_cgram(bank, labels, header['fg_palette'], header['bg_palette'],
                                           header['spr_palette'], header['bg_color'], mklvl.COIN_ANIM_REF)

    def render(self, tile, screen):
        out = np.full((16, 16), -1, np.int32)
        raw = self.m16.get_raw(tile, screen)
        entry = self.m16.get(tile, screen)
        for k, (qx, qy) in enumerate(((0, 0), (0, 8), (8, 0), (8, 8))):
            if not raw[k]:
                continue
            t, pal, _, xf, yf = entry[k]
            pix = np.asarray(self.gfx[self.files[t // 128]][t % 128])
            if xf:
                pix = pix[:, ::-1]
            if yf:
                pix = pix[::-1]
            # CGRAM guarda BGR555; el pipeline RGB555 invierte R y B.
            cg = np.asarray(self.cgram[pal * 16:pal * 16 + 16], np.int32)
            rgb = ((cg & 31) << 10) | (cg & 0x3E0) | ((cg >> 10) & 31)
            block = mkleveld.to12(rgb[pix])
            out[qy:qy + 8, qx:qx + 8] = np.where(pix != 0, block, -1)
        return out


def inventory(d):
    desc = lvdesc.load()
    h, _, lv = mklvl.build(desc.obj, desc=desc)
    tiles = Tiles(h)
    final = smwgen.parse_tables(os.path.join(smwgen.SRC, 'player.s'))['DATA_00F0C8']
    blocks = [b.copy() for b in d['blocks']]
    seen = {b.tobytes(): k for k, b in enumerate(blocks)}
    changes, bad = [], []
    counts = collections.Counter()
    for row in range(12, min(26, lv.H)):
        colors = [active_colors(d['events'][row * 16 + y], d['W']) for y in range(16)]
        for col in range(lv.W):
            source = lv.get(col, row)
            for result in results(source, final):
                counts['%03X->%03X' % (source, result)] += 1
                target = tiles.render(result, col // 16)
                idx = np.zeros((16, 16), np.int8)
                missing = []
                for y in range(16):
                    for x in range(16):
                        color = int(target[y, x])
                        if color < 0:
                            continue
                        regs = [r for r in range(1, 8) if colors[y][r, col * 16 + x] == color]
                        if not regs:
                            missing.append((col * 16 + x, row * 16 + y, color))
                        else:
                            idx[y, x] = regs[0]
                if missing:
                    bad.append(dict(col=col, row=row, source=source, result=result,
                                    pixels=len(missing), first=missing[0],
                                    colors=sorted(set(p[2] for p in missing))))
                    continue
                key = idx.tobytes()
                if key not in seen:
                    seen[key] = len(blocks)
                    blocks.append(idx)
                changes.append((col * 15 + row - 12, result, seen[key]))
    return blocks, sorted(changes), dict(counts), bad


def reserve_colors(d, bad):
    """Reserva colores potenciales en registros sin pixeles estaticos.

    Se exige un tramo de 48px libre a ambos lados; los eventos originales
    siguen intactos. El plan del copper conserva su comprobacion separada.
    """
    idx = render_d.l1_index(d)
    tiles = Tiles(mklvl.build(lvdesc.load().obj, desc=lvdesc.load())[0])
    added, rejected = [], []
    for item in bad:
        col, row = item['col'], item['row']
        target = tiles.render(item['result'], col // 16)
        for y in range(16):
            line, lo, hi = row * 16 + y, col * 16, col * 16 + 15
            colors = active_colors(d['events'][line], d['W'])
            needed = sorted(set(int(c) for c in target[y] if c >= 0))
            for color in needed:
                xs = np.nonzero(target[y] == color)[0] + lo
                if all(color in colors[1:, x] for x in xs):
                    continue
                # Extender una reserva del MISMO color no agrega una carga.
                # Ningun evento de otro color puede quedar dentro del tramo.
                extended = False
                for i, (start, end, reg, old_color) in enumerate(d['events'][line]):
                    if old_color != color or start > hi + 48 or end < lo - 48:
                        continue
                    left, right = min(start, lo), max(end, hi)
                    if any(r == reg and c != color and s <= right and e >= left
                           for s, e, r, c in d['events'][line]):
                        continue
                    d['events'][line][i] = (left, right, reg, color)
                    d['events'][line].sort()
                    added.append((line, left, right, reg, color))
                    extended = True
                    break
                if extended:
                    continue
                for reg in range(1, 8):
                    left, right = max(0, lo - 48), min(d['W'] - 1, hi + 48)
                    if np.any(idx[line, left:right + 1] == reg):
                        continue
                    if any(r == reg and s <= right and e >= left for s, e, r, c in d['events'][line]):
                        continue
                    # Un registro sin uso estatico puede ser el unico que
                    # ya representa OTRO color del reemplazo potencial.
                    if any(target[y, x] >= 0 and target[y, x] != color
                           and colors[reg, lo + x] == target[y, x]
                           and np.sum(colors[1:, lo + x] == target[y, x]) == 1
                           for x in range(16)):
                        continue
                    event = (lo, hi, reg, color)
                    d['events'][line].append(event)
                    d['events'][line].sort()
                    added.append((line, *event))
                    colors[reg, lo:hi + 1] = color
                    break
                else:
                    rejected.append((line, lo, color))
    return added, rejected


def apply_reference(d, data, changes):
    """Aplica (celda,Map16) del diario al render Python desde el mismo SMWS.

    Reconstruye BLK, preserva las filas no visibles y usa los indices exactos
    de D_TCHG; no transforma el mapa de la referencia con una aproximacion.
    """
    _, _, _, bad = inventory(d)
    _, rejected = reserve_colors(d, bad)
    if rejected:
        raise ValueError('reservas de color imposibles: %r' % rejected)
    nblk = struct.unpack_from('>H', data, 8)[0]
    boff = struct.unpack_from('>I', data, 16)[0]
    toff = struct.unpack_from('>I', data, 56)[0]
    count = struct.unpack_from('>H', data, toff)[0]
    table = {(cell, result): block for cell, result, block, old in
             (struct.unpack_from('>HHBB', data, toff + 2 + 6 * k) for k in range(count))}
    raw = np.frombuffer(data, np.uint8, nblk * 96, boff).reshape(nblk, 16, 3, 2)
    bits = np.unpackbits(raw, axis=3)
    d['blocks'] = bits[:, :, 0] | bits[:, :, 1] << 1 | bits[:, :, 2] << 2
    d['nblk'] = nblk
    d['map'] = d['map'].copy()
    for cell, result in changes:
        col, row = divmod(cell, 15)
        d['map'][row + 12, col] = table[cell, result]
    return d


def main():
    work = os.path.join(os.path.dirname(__file__), '..', 'work')
    d = render_d.load(os.path.join(work, 'yi1_d.dat'))
    blocks, changes, counts, bad = inventory(d)
    added, rejected = reserve_colors(d, bad)
    blocks, changes, counts, final_bad = inventory(d)
    report = dict(blocks=len(blocks), entries=len(changes), transitions=counts,
                  rejected=bad, reserves=added, reserves_rejected=rejected, final_rejected=final_bad)
    path = os.path.join(work, 'sw-b-inventory.json')
    open(path, 'w', encoding='utf-8').write(json.dumps(report, indent=2))
    print('SW-B: %d bloques, %d entradas exactas, %d reemplazos rechazados -> %s'
          % (len(blocks), len(changes), len(bad), path))
    if final_bad:
        first = bad[0]
        print('Primer rechazo: celda (%d,%d), $%03X->$%03X, %d px, primer pixel %s'
              % (first['col'], first['row'], first['source'], first['result'], first['pixels'], first['first']))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
