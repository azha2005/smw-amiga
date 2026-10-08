#!/usr/bin/env python3
"""B2bis: cache compactada, recorte con huecos y controles C/ABI reales."""
import argparse
import ctypes as C
import json
from pathlib import Path
import struct
import subprocess

import m68kverify as V
from g5env_verify import EnvCPU, project_fixture, project_call, front_bytes, front_harness, cache_key, block_env
from g5plan_verify import M68k
from sprgfx_final import derived_path


def sprite(grid, x=80, row=40, first=0):
    """Construye DATA por pixel; no necesita graficos ni RAM del juego."""
    out = bytearray(672)
    height, cols = len(grid), len(grid[0]) // 16
    for col in range(cols):
        offset = 336 * (first + col)
        vs, ve, hs = row + 44, row + 44 + height, x + 160 + 16 * col
        for half in range(2):
            struct.pack_into('>HH', out, offset + 168 * half,
                             ((vs & 255) << 8) | (hs >> 1),
                             ((ve & 255) << 8) | (hs & 1) | ((vs >> 8) << 2) |
                             ((ve >> 8) << 1) | (half << 7))
        for j, pixels in enumerate(grid):
            words = [sum(((pixels[16 * col + u] >> p) & 1) << (15-u) for u in range(16))
                     for p in range(4)]
            struct.pack_into('>HH', out, offset + 4 + 4*j, *words[:2])
            struct.pack_into('>HH', out, offset + 172 + 4*j, *words[2:])
    return bytes(out)


def expected(grid, x, row):
    env = {}
    for j, pixels in enumerate(grid):
        for u, idx in enumerate(pixels):
            if idx and 0 <= x+u < 256 and 0 <= row+j < 224:
                k = row+j, idx
                lo, hi = env.get(k, (x+u, x+u))
                env[k] = min(lo, x+u), max(hi, x+u)
    return env


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin', default='work/b2b_r/game.bin')
    ap.add_argument('--lst', default='work/b2b_r/game.lst')
    ap.add_argument('--out', default='work/b2b/edges')
    a = ap.parse_args()
    derived_path(a.out)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    holes = [[1, 0, 0, 0, 0, 0, 0, 1, 2, 3, 0, 7, 12, 0, 15, 1] for _ in range(32)]
    dense = [list(range(16)) for _ in range(40)]
    limit = [[1,2,3,4,5,6,7]*2+[1,2] for _ in range(35)] + [[1,2,3,4]*4] + [list(range(16))] + [[0]*16]*3
    fixtures = [('holes', holes, 0), ('dense', dense, 0), ('SPR2', holes, 1), ('limit', limit, 0)]
    # Una unica Machine: materializar antes de crear el control del juego.
    dec = EnvCPU(*project_fixture(out, 8))
    packed = {}
    for name, grid, first in fixtures:
        spr = sprite(grid, first=first)
        _, data = dec.decode(spr)
        dec.cpu.write(0xc2000, data)
        _, view, data = project_call(dec, 0xc2000, spr)
        if block_env(view) != expected(grid, 80, 40):
            raise ValueError('fixture compacto distinto: ' + name)
        mode = struct.unpack_from('>H', data, 2)[0]
        if mode != (1 if name in ('dense', 'limit') else 4):
            raise ValueError('no se ejercito pack/fallback denso: ' + name)
        packed[name] = data
    # Misma imagen con puntero no usado distinto: miss de clave, no hit.
    key = bytearray(struct.pack('>HhBBhBB', 2, 0, 0, 0x20, 16, 2, 0x20).ljust(40, b'\0'))
    # El decoder llena hasta el ultimo byte de la ultima entrada. El
    # canario debe estar en el limite real, no en una reserva mayor stale.
    lastkey = bytearray(cache_key(bytes(key)))
    lastkey[5], lastkey[21] = 0xc0, 0x80
    dec.reset_cache(8)
    _, _, hit = dec.lookup(bytes(lastkey), sprite(dense))
    if hit or dec.last_ptr + 1204 != dec.cache + dec.cache_size:
        raise ValueError('fixture no llega al limite real de la cache')
    dec.cpu.write(dec.cache + dec.cache_size, b'FAIL')
    try:
        dec.lookup(bytes(lastkey), sprite(dense))
    except ValueError as err:
        if 'fuera de cache' not in str(err):
            raise
    else:
        raise ValueError('canario alterado de cache no detectado')
    dec.reset_cache(8)
    spr = sprite(holes)
    _, _, hit = dec.lookup(cache_key(bytes(key)), spr)
    if hit:
        raise ValueError('cache no vacia al comenzar')
    project_call(dec, dec.last_ptr, spr)
    key[38] ^= 1                         # Tile7FPtr: no lo leen tiles 0/2
    cyc, _, hit = dec.lookup(cache_key(bytes(key)), spr)
    if hit != 2 or cyc > 12000:
        raise ValueError('alias sin igualdad completa mal clasificado')
    key[18] ^= 1                         # puntero usado: debe decodificar
    changed = [r.copy() for r in holes]
    changed[3][0] = 2
    changed_spr = sprite(changed)
    cyc, _, hit = dec.lookup(cache_key(bytes(key)), changed_spr)
    _, view, _ = project_call(dec, dec.last_ptr, changed_spr)
    if hit or cyc > 12000 or block_env(view) != expected(changed, 80, 40):
        raise ValueError('puntero usado/pixel cambiado no invalidaron la cache')
    del dec

    stub = out / 'globals.c'
    stub.write_text('#include "g5plan.h"\nu8 ram[8192], mario_pal, spr_oam_first[12], spr_oam_n[12];\n')
    dll = out / 'edges.dll'
    subprocess.run(['gcc', '-O2', '-shared', '-DSPR_G5', '-DNOOAM', '-DSPR_OAM', '-Iplayer',
                    '-o', str(dll), 'tools/g5env_front.c', 'player/g5plan.c', 'player/g5env.c', str(stub)], check=True)
    lib = C.CDLL(str(dll.resolve()))
    P = C.POINTER(C.c_ubyte)
    lib.g5env_bind.argtypes = [P, P, P]
    lib.g5env_front.argtypes = [P, C.c_void_p, C.c_void_p, P]
    hostout = (C.c_ubyte * (224*32))()
    m = M68k(a.bin, a.lst)
    front_harness(out, m)
    count, recrops = 0, []
    variants = [(name, grid, first, x, row) for name, grid, first in fixtures
                for x in (-15, -7, -1, 0, 239, 240, 241, 249, 255, 256)
                for row in (-31, -1, 0, 193, 223, 224)]
    # Ancho doble: entrada sin clave, decoder exacto y fallback C del juego.
    wide = [r + list(reversed(r)) for r in holes]
    variants += [('wide', wide, 0, x, row) for x in (-31, -7, 0, 224, 240, 255)
                 for row in (-31, 0, 223)]
    for name, grid, first, x, row in variants:
        spr = sprite(grid, x, row, first)
        want = expected(grid, x, row)
        original = bytes([0xa5]) * 1292
        m.cpu.write(m.SPR - 4, b'HEAD' + spr + b'TAIL')
        data = packed.get(name)
        if data is None:
            m.cpu.write(0xc2000 - 4, b'HEAD' + b'\xa5'*2484 + b'TAIL')
            _, _, abi = m.call('_g5env_decode', m.SPR, 0xc2000)
            if abi:
                raise ValueError('decoder ancho ABI')
            data = m.cpu.read(0xc2000, 2484)
        m.cpu.write(m.BLK - 4, b'HEAD' + original + b'TAIL')
        m.cpu.write(0xc2000 - 4, b'HEAD' + data + b'TAIL')
        m.cpu.write(m.sym('_ram'), b'\xa5'*8192)
        cyc, _, abi = m.call('_g5env_project', m.BLK, m.SPR, 0xc2000)
        got = m.cpu.read(m.BLK, 1292)
        if (abi or block_env(got) != want or m.cpu.read(m.BLK - 4, 4) != b'HEAD'
                or m.cpu.read(m.BLK+1292, 4) != b'TAIL'
                or m.cpu.read(m.SPR - 4, 680) != b'HEAD' + spr + b'TAIL'
                or m.cpu.read(0xc2000 - 4, 4) != b'HEAD'
                or m.cpu.read(0xc2000+len(data), 4) != b'TAIL'):
            raise ValueError('projector distinto/ABI/canario: %s x%d R%d' % (name, x, row))
        blk = (C.c_ubyte * 1292).from_buffer_copy(original)
        host_spr = (C.c_ubyte * 672).from_buffer_copy(spr)
        host_data = (C.c_ubyte * len(data)).from_buffer_copy(data)
        lib.g5env_bind(blk, host_spr, host_data)
        lib.g5env_front(blk, C.cast(lib.g5_mario_mask, C.c_void_p), C.cast(lib.g5_mario_span, C.c_void_p), hostout)
        if bytes(hostout) != front_bytes(want):
            raise ValueError('control/frontera PC distinto: %s x%d R%d' % (name, x, row))
        bound = (C.c_ubyte * 1292).from_buffer_copy(got)
        lib.g5env_front(bound, C.cast(lib.g5_mario_mask, C.c_void_p), C.cast(lib.g5_mario_span, C.c_void_p), hostout)
        if bytes(hostout) != front_bytes(want):
            raise ValueError('vista de produccion/frontera PC distinta')
        _, _, abi = m.call('_g5env_front', m.BLK, m.sym('_g5_mario_mask'), m.sym('_g5_mario_span'), 0xc4000)
        if abi or m.cpu.read(0xc4000, 224*32) != front_bytes(want):
            raise ValueError('frontera 68000 distinta: %s x%d R%d' % (name, x, row))
        if name in ('holes', 'SPR2') and not 0 <= x <= 240:
            recrops.append(cyc)
        count += 1
    if expected(holes, -1, 0)[0, 1][0] != 6:
        raise ValueError('la prueba no ejercita el hueco en el borde')
    (out / 'edges_summary.json').write_text(json.dumps(dict(cases=count, abi=0, diff=0,
                                               recrop_project_max=max(recrops)), indent=2))
    print('B2bis bordes: %d casos PC = ASM = pixel, ABI/canarios 0; pack, overflow, SPR2, ancho doble, huecos y alias exactos' % count)


if __name__ == '__main__':
    main()
