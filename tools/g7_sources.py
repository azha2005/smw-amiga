#!/usr/bin/env python3
"""G7: fuentes 8x8 de cuatro planos y mascara, sin duplicar flips/16x16.

Solo genera derivados en work/. Las fichas de 16x16 se componen como la
VRAM SNES (P99); la paleta y los indices PF1 se resuelven por foto/fila.
"""
import argparse
import json
import struct
from pathlib import Path

import mksprgfx as S
from palette import snes_to_amiga12

MAGIC = b'G7S1'
HEADER = 16
DIRECTORY = HEADER
PALETTE = DIRECTORY + 512*2
DATA = PALETTE + 128*2
STRIDE = 80                    # 5 planos x 8 filas x palabra (8 px altos)
LIMIT = 12288


def scope():
    # Rangos de las instrucciones G7, mas los cuadrantes de humo 16x16.
    bases = set(range(0x29, 0x5F)) | {0x83, 0x7C, 0x7D, 0x6C, 0x6D, 0x6E, 0xFF}
    large = set(range(0x60, 0x67))
    tiles = bases | large
    for tile in large:
        tiles.update(t for row in S.tile_grid(tile, 16) for t in row)
    # 3-UP: PointTile1/2 con The2Up3UpAttr $ff (pagina alta de OBJ).
    tiles.update((0x15E, 0x14E))
    return sorted(tiles), sorted(bases | large), large


def encode(pixels):
    words = []
    for plane in range(5):
        for row in pixels:
            bits = sum((bool(v) if plane == 4 else (v >> plane) & 1) << (15-x)
                       for x, v in enumerate(row))
            words.append(bits)
    return struct.pack('>40H', *words)


def tile_at(blob, tile):
    off = struct.unpack_from('>H', blob, DIRECTORY+2*tile)[0]
    if off == 0xFFFF:
        raise KeyError('G7 fuente no cubierta: $%03X' % tile)
    rows = [[0]*8 for _ in range(8)]
    for y in range(8):
        for x in range(8):
            rows[y][x] = sum(((struct.unpack_from('>H', blob, off+p*16+2*y)[0]
                               >> (15-x)) & 1) << p for p in range(4))
            mask = (struct.unpack_from('>H', blob, off+64+2*y)[0] >> (15-x)) & 1
            assert mask == bool(rows[y][x])
    return rows


def ficha(blob, tile, width, fx=False, fy=False):
    rows = [[0]*width for _ in range(width)]
    for ty, grid in enumerate(S.tile_grid(tile, width)):
        for tx, number in enumerate(grid):
            part = tile_at(blob, number)
            for y, row in enumerate(part):
                rows[8*ty+y][8*tx:8*tx+8] = row
    if fx:
        rows = [r[::-1] for r in rows]
    return rows[::-1] if fy else rows


def build(vram, colors):
    tiles, _, _ = scope()
    blob = bytearray(DATA)
    blob[:HEADER] = struct.pack('>4s6H', MAGIC, len(tiles), STRIDE, DIRECTORY, PALETTE, DATA, 0)
    blob[DIRECTORY:PALETTE] = b'\xff'*(512*2)
    struct.pack_into('>128H', blob, PALETTE, *colors)
    intern = {}
    for tile in tiles:
        packed = encode(S.ficha(vram, tile, 8, False, False))
        if packed not in intern:
            intern[packed] = len(blob)
            blob += packed
        struct.pack_into('>H', blob, DIRECTORY+2*tile, intern[packed])
    assert len(blob) % 8 == 0 and len(blob) <= LIMIT
    return bytes(blob), len(intern)


def verify(blob, vram):
    tiles, bases, large = scope()
    count = 0
    for tile in tiles:
        assert tile_at(blob, tile) == S.ficha(vram, tile, 8, False, False)
        off = struct.unpack_from('>H', blob, DIRECTORY+tile*2)[0]
        assert off % 8 == 0 and DATA <= off <= len(blob)-STRIDE
        # La mitad baja de cada palabra es cero: fuente segura de 8 px.
        assert all(v == 0 for v in blob[off+1:off+STRIDE:2])
    for tile in bases + [0x15E, 0x14E]:
        for width in ((8, 16) if tile in large else (8,)):
            for fx in (False, True):
                for fy in (False, True):
                    px = ficha(blob, tile, width, fx, fy)
                    for y, row in enumerate(px):
                        for x, value in enumerate(row):
                            assert value == S.ref_pixel(vram, tile, width, fx, fy, x, y)
                            count += 1
                    # Recorte de todas las fases de borde horizontal y vertical.
                    for x0, y0 in ((-7, 0), (-1, -1), (0, 0), (249, 220), (255, 223)):
                        for y in range(max(0, -y0), min(width, 224-y0)):
                            for x in range(max(0, -x0), min(width, 256-x0)):
                                assert px[y][x] == S.ref_pixel(vram, tile, width, fx, fy, x, y)
    assert struct.unpack_from('>H', blob, DIRECTORY+0x1FF*2)[0] == 0xFFFF
    return count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', default='work/g7')
    a = ap.parse_args()
    vram, _, _ = S.build_vram(S._DEF_SRC, S.LEVEL)
    cg = S.level_cgram(S._DEF_SRC, S.LEVEL)
    blob, unique = build(vram, [snes_to_amiga12(v) for v in cg[128:256]])
    pixels = verify(blob, vram)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out/'sources.bin').write_bytes(blob)
    result = dict(tiles=len(scope()[0]), unique=unique, bytes=len(blob),
                  pool_remaining=LIMIT-len(blob), pixels_verified=pixels,
                  format='G7S1: directorio 512 u16, 128 colores OCS, 5x8 palabras por ficha')
    (out/'sources.json').write_text(json.dumps(result, indent=2), encoding='utf8')
    print('G7 SOURCES: OK ' + json.dumps(result))


if __name__ == '__main__':
    main()
