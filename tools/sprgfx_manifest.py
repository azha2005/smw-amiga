#!/usr/bin/env python3
"""Poses G3 con pertenencia real SOT1 y Rex legal de tablas del ROM.

Se coteja la secuencia visible completa contra la grabación. Nunca agrupa
por proximidad. Salida derivada exclusivamente en work/.
"""
import argparse
import collections
import json
import os
import re
import struct

import mksprgfx as G
from sprgfx_final import require, compose, derived_path
from smw2amiga import decode_snes_tile


def signed(value):
    return ((value + 128) & 255) - 128


def mario_rows(ram, recorded, gfx):
    """Índices por fila desde VRAM dinámica real (gamecheck.spr_ok).

    Selecciona por dirección VRAM dinámica y paleta 0, no por proximidad ni
    por nombre de dueño. Se reserva también cualquier partícula que comparta
    esas fichas: mismo índice y mismo COLOR16+k que Mario.
    """
    dynamic = {}
    for r in range(2):
        for i in range(5):
            off = 0xd85 + 10 * r + 2 * i
            ptr = (ram[off] | ram[off + 1] << 8) - 0x2000
            if 0 <= ptr <= len(gfx) - 64:
                for half in range(2):
                    dynamic[16 * r + 2 * i + half] = decode_snes_tile(gfx[ptr + 32 * half:ptr + 32 * half + 32], 4)
    ptr = (ram[0xd99] | ram[0xd9a] << 8) - 0x2000
    if 0 <= ptr <= len(gfx) - 32:
        dynamic[0x7f] = decode_snes_tile(gfx[ptr:ptr + 32], 4)
    pixels = {}
    # Misma prioridad: primera OAM opaca tapa a posteriores, incluso si no
    # son Mario. Aquí solo necesitamos las entradas de VRAM dinámica.
    for entry in recorded:
        x, y, tile, attr, hi = entry
        if (attr >> 1) & 7 or attr & 1 or tile not in dynamic or y == 0xf0:
            continue
        ex = x | (hi & 1) << 8
        ex = ex - 512 if ex >= 256 else ex
        ey = y - 256 if y >= 0xf0 else y
        size = 16 if hi & 2 else 8
        for dy in range(size):
            for dx in range(size):
                sx = size - 1 - dx if attr & 0x40 else dx
                sy = size - 1 - dy if attr & 0x80 else dy
                t = tile + sx // 8 + 16 * (sy // 8)
                require(t in dynamic, 'ficha dinámica Mario desconocida %02x' % t)
                val = dynamic[t][sy & 7][sx & 7]
                if val and 0 <= ex + dx < 256 and 0 <= ey + dy < 224:
                    pixels.setdefault((ex + dx, ey + dy), val)
    rows = collections.defaultdict(set)
    for (_, y), val in pixels.items():
        rows[y].add(val)
    return rows


def read_trace(path, oracle, specs, counts, mario=None):
    recordings = {f: [o[i:i + 5] for i in range(0, len(o), 5)]
                  for f, o, _ in G.load_oam_bin(oracle)}
    with open(path, 'rb') as handle:
        require(handle.read(4) == b'SOT1', 'traza desconocida')
        mlen, = struct.unpack('<I', handle.read(4))
        require(0 < mlen <= 0x8000, 'mapa fuera de rango')
        while True:
            header = handle.read(8)
            if not header:
                break
            require(len(header) == 8, 'traza truncada')
            frame, slot, num, first, n = struct.unpack('<IBBBB', header)
            body = handle.read(2 * (0x2000 + mlen))
            require(len(body) == 2 * (0x2000 + mlen) and slot < 12 and n > 0,
                    'registro SOT1 inválido')
            ram = body[0x2000 + mlen:0x4000 + mlen]
            visible = []
            require(first % 4 == 0 and 64 + first // 4 + n <= 128, 'rango OAM inválido')
            for c in range(n):
                s = 64 + first // 4 + c
                entry = ram[0x200 + 4 * s:0x204 + 4 * s] + ram[0x420 + s:0x421 + s]
                if entry[1] != 0xf0:
                    visible.append(entry)
            if not visible:
                continue
            require(frame in recordings, 'frame ausente del oráculo')
            recorded = recordings[frame]
            require(any(recorded[k:k + len(visible)] == visible
                        for k in range(len(recorded) - len(visible) + 1)),
                    'OAM distinta de SNES: %s frame=%d slot=%d sprite=%02x' % (path, frame, slot, num))
            sx = ((ram[0xe4 + slot] | ram[0x14e0 + slot] << 8)
                  - (ram[0x1a] | ram[0x1b] << 8))
            sy = ((ram[0xd8 + slot] | ram[0x14d4 + slot] << 8)
                  - (ram[0x1c] | ram[0x1d] << 8))
            tiles, priorities = [], set()
            for entry in visible:
                x, y, tile, attr, hi = entry
                tiles.append([signed(x - sx), signed(y - sy), tile | (attr & 1) << 8,
                              16 if hi & 2 else 8, attr >> 6 & 1, attr >> 7, attr >> 1 & 7])
                priorities.add(attr >> 4 & 3)
            require(len(priorities) == 1, 'pose con prioridades mixtas: requiere descriptor por ficha')
            priority = priorities.pop()
            if mario is None:
                key = (tuple(tuple(t) for t in tiles), priority)
                specs.setdefault(key, dict(name='trace_%02x_%d' % (num, len(specs)),
                                           tiles=tiles, priority=priority, source='SOT1/oracle'))
            else:
                vram, gfx, pals = mario
                _, oy, truth = compose(vram, tiles)
                myrows = mario_rows(ram, recorded, gfx)
                # Y de la ranura como número firmado en pantalla.
                sy_screen = sy if sy < 0x8000 else sy - 0x10000
                for variant in range(8):
                    colors = struct.unpack_from('>16H', pals, 32 * variant)
                    reserve = [{k: colors[k] for k in sorted(myrows[sy_screen + oy + y])}
                               for y in range(len(truth))]
                    key = (tuple(tuple(t) for t in tiles), priority,
                           tuple(tuple(sorted(r.items())) for r in reserve))
                    specs.setdefault(key, dict(name='trace_%02x_f%d_m%d_%d' % (num, frame, variant, len(specs)),
                                               tiles=tiles, priority=priority, source='SOT1/oracle/dynamic_rows',
                                               reserved_rows=reserve, mario_variant=variant))
            counts['%02X' % num] += 1


def rom_table(text, label):
    block = text.split(label + ':', 1)[1]
    vals = []
    for line in block.splitlines():
        if re.match(r'^\w', line):
            break
        line = line.split(';')[0]
        if '.DB' in line:
            vals.extend(int(v, 16) for v in re.findall(r'\$([0-9A-Fa-f]{2})', line))
    return vals


def legal_rex(src, specs):
    text = open(os.path.join(src, 'sprite_3-1.s'), encoding='utf-8').read()
    dx, dy, tiles, prop = [rom_table(text, label) for label in
                          ('RexTileDispX', 'RexTileDispY', 'RexTiles', 'RexGfxProp')]
    require((len(dx), len(dy), len(tiles), len(prop)) == (24, 12, 12, 2),
            'tablas Rex desconocidas')
    for pose in range(6):
        for direction in range(2):
            # RexGfxRt emite X=1 antes de X=0; tamaño 8 solo en pose 5.
            entries = []
            attr = prop[direction] | 0x20  # wm_SpriteProp normal YI1
            for part in (1, 0):
                index = 2 * pose + part
                xindex = index + (12 if direction == 0 else 0)
                entries.append([signed(dx[xindex]), signed(dy[index]), tiles[index] | (attr & 1) << 8,
                                8 if pose == 5 else 16, attr >> 6 & 1, attr >> 7, attr >> 1 & 7])
            priority = attr >> 4 & 3
            key = (tuple(tuple(t) for t in entries), priority)
            specs.setdefault(key, dict(name='rex_legal_%d_%d' % (pose, direction),
                                       tiles=entries, priority=priority, source='RexGfxRt/tables'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default=G._DEF_SRC)
    ap.add_argument('--trace', action='append', default=[], help='SOT1:oracle_*_oam.bin')
    ap.add_argument('--out', default=os.path.join(G.WORK, 'sprgfx_manifest.json'))
    ap.add_argument('--mario-rows', action='store_true', help='reservas reales por fila, ocho variantes')
    args = ap.parse_args()
    derived_path(args.out)
    specs, counts = {}, collections.Counter()
    mario = None
    if args.mario_rows:
        vram, _, _ = G.build_vram(args.src, G.LEVEL)
        gfx = open(os.path.join(G.WORK, 'cc', 'gfx32.bin'), 'rb').read()
        pals = open(os.path.join(G.WORK, 'cc', 'mario_pal.bin'), 'rb').read()
        require(len(gfx) == 23808 and len(pals) == 256, 'regenerar mkmario.py')
        mario = vram, gfx, pals
    for pair in args.trace:
        # Windows drive colon permitido: separador es =.
        path, oracle = pair.split('=', 1)
        read_trace(path, oracle, specs, counts, mario)
    require(bool(counts), 'sin despachos de SOT1 verificados')
    if mario is None:
        legal_rex(args.src, specs)
    with open(args.out, 'w', encoding='utf-8') as handle:
        json.dump(dict(poses=list(specs.values()), exact_dispatches=dict(counts),
                       legal_coverage=(['Rex poses 0..5, ambas direcciones, prioridad normal'] if mario is None else []),
                       pending=['Banzai/Piranha/Chuck/meta/powerups/partículas: G8 ausente',
                                'variantes legales fuera del replay de compartidas, muerte y prioridades',
                                ('poses dinámicas de Mario no observadas en estas trazas'
                                 if mario else 'poses dinámicas y variantes de paleta de Mario')]),
                  handle, indent=2)
    print('Manifiesto: %d poses, despachos exactos %s; modo=%s' %
          (len(specs), dict(counts), 'Mario filas reales/8 paletas' if mario else 'Rex legal 12 combinaciones'))


if __name__ == '__main__':
    main()
