#!/usr/bin/env python3
"""Puertas negativas SG3F y auditoría conservadora de ocho paletas Mario."""
import argparse
import json
import os
import struct

import mksprgfx as G
from smw2amiga import decode_snes_tile
from palette import snes_to_amiga12
from sprgfx_final import (Bank, FormatError, compose, deserialize, pack_pose,
                          remap, require, serialize, verify, derived_path)


def negative_tests(vram, cg):
    count = 0
    def rejects(call):
        nonlocal count
        try:
            call()
        except (FormatError, struct.error):
            count += 1
            return
        raise FormatError('prueba negativa aceptada')
    bank = Bank()
    tile = [[-4, -15, 0x18a, 16, 0, 0, 3], [0, 0, 0x1aa, 16, 0, 0, 3]]
    pose, _ = pack_pose(vram, cg, tile, 2, bank)
    meta = serialize([pose], bank)
    require(verify(vram, cg, deserialize(meta, bank.data)) > 0, 'prueba positiva vacía')
    rejects(lambda: compose(vram, [[0, 0, 512, 16, 0, 0, 3]]))
    rejects(lambda: compose(vram, [[0, 0, 0x18a, 32, 0, 0, 3]]))
    rejects(lambda: Bank().add(bytes(65537)))
    rejects(lambda: derived_path(os.path.join(G.HERE, 'asset.bin')))
    rejects(lambda: derived_path(os.path.join(G.WORK, '..', 'assets-out', 'sprite.dma')))
    unavailable = snes_to_amiga12(cg[128 + 3 * 16 + 1]) ^ 1
    rejects(lambda: remap([[(3, 1)]], cg, [{k: unavailable for k in range(1, 16)}]))
    # Mutar el descriptor serializado, no solo objetos Python.
    for off, value in ((36, 0xffffffff), (40, 1), (44, 0xffffffff), (48, 1)):
        bad = bytearray(meta)
        struct.pack_into('>I', bad, off, value)
        rejects(lambda: deserialize(bad, bank.data))
    bad = bytearray(bank.data)
    # Terminador primer canal.
    stream = pose['streams'][0][0]
    bad[stream + 4 + pose['height'] * 4] = 1
    rejects(lambda: deserialize(meta, bad))
    # Alterar un píxel fuente/bob debe discrepar de DMA.
    bad = bytearray(bank.data)
    bad[pose['source']] ^= 0x80
    rejects(lambda: deserialize(meta, bad))
    # Orden: dos fichas opacas distintas solapadas (primera OAM gana).
    overlap = [[0, 0, 0x18a, 16, 0, 0, 3], [0, 0, 0x1aa, 16, 0, 0, 3]]
    require(compose(vram, overlap) != compose(vram, overlap[::-1]), 'fixture no verifica orden')
    p, _ = pack_pose(vram, cg, overlap, 2, Bank())
    require(p['tiles'] == overlap, 'orden de clave alterado')
    print('SG3F negativos: %d rechazos exactos; orden solapado OK' % count)


def mario_audit(vram, cg, manifest, output):
    derived_path(output)
    specs = json.load(open(manifest, encoding='utf-8'))['poses']
    gfx = open(os.path.join(G.WORK, 'cc', 'gfx32.bin'), 'rb').read()
    pals = open(os.path.join(G.WORK, 'cc', 'mario_pal.bin'), 'rb').read()
    require(len(gfx) == 23808 and len(pals) == 256, 'regenerar mkmario.py')
    used = sorted({v for off in range(0, len(gfx), 32)
                   for row in decode_snes_tile(gfx[off:off + 32], 4) for v in row if v})
    failures, poses, bank = [], [], Bank()
    palette_results = []
    for variant in range(8):
        colors = struct.unpack_from('>16H', pals, variant * 32)
        fixed = {i: colors[i] for i in used}
        successes = 0
        for spec in specs:
            before = len(bank.data), dict(bank.offsets)
            try:
                _, _, truth = compose(vram, spec['tiles'])
                pose, _ = pack_pose(vram, cg, spec['tiles'], spec['priority'], bank,
                                    [fixed for _ in truth])
                # Ningún índice de Mario recibe otro color.
                for row_map in pose['row_maps']:
                    for pal, idx, target, color in row_map:
                        require(target not in fixed or fixed[target] == color, 'remapeo pisa Mario')
                poses.append(pose)
                successes += 1
            except FormatError as error:
                del bank.data[before[0]:]
                bank.offsets = before[1]
                failures.append(dict(pose=spec['name'], mario_variant=variant, error=str(error)))
        palette_results.append(dict(variant=variant, exact=successes, requested=len(specs)))
    meta = serialize(poses, bank)
    pixels = verify(vram, cg, deserialize(meta, bank.data))
    report = dict(mode='reserva conservadora: unión índices de todo GFX32, todas las filas',
                  mario_indices=used, variants=palette_results, chip_bytes=len(bank.data),
                  slow_bytes=len(meta), verified_pixels=pixels, failures=failures,
                  caveat='Un rechazo conservador no demuestra conflicto de dos poses simultáneas. '
                         'Faltan máscaras reales de Mario por fila y ventanas G6. '
                         'Las variantes aceptadas preservan TODOS sus índices.',
                  final_complete=False)
    with open(output + '.json', 'w', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    open(output + '.idx', 'wb').write(meta)
    open(output + '.dma', 'wb').write(bank.data)
    print('Mario: índices %s; %d/%d variantes exactas, %d rechazos, banco %d B' %
          (used, len(poses), len(specs) * 8, len(failures), len(bank.data)))
    return bool(failures)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', default=os.path.join(G.WORK, 'sprgfx_manifest.json'))
    ap.add_argument('--out', default=os.path.join(G.WORK, 'sprgfx_mario_audit'))
    ap.add_argument('--audit-mario', action='store_true')
    args = ap.parse_args()
    vram, _, _ = G.build_vram(G._DEF_SRC, G.LEVEL)
    cg = G.level_cgram(G._DEF_SRC, G.LEVEL)
    negative_tests(vram, cg)
    if args.audit_mario:
        raise SystemExit(int(mario_audit(vram, cg, args.manifest, args.out)))


if __name__ == '__main__':
    main()
