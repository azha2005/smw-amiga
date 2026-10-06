#!/usr/bin/env python3
"""E11/E12: indices originales SMWD, sin dependencia de numpy.

Las filas PF2 del blob estan alineadas con la Y del nivel, no directamente
con Bg2VOfs: la fila y0 representa Bg2VOfs de reposo (192 en YI1).
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parent.parent


def decode_planar(data, width, planes=3):
    stride = width // 8
    if width % 8 or len(data) != planes * stride:
        raise ValueError('fila planar invalida')
    return bytearray(sum(((data[p * stride + x // 8] >> (7 - x % 8)) & 1) << p
                         for p in range(planes)) for x in range(width))


@dataclass
class Camera:
    frame: int
    x: int
    y: int
    l2x: int
    l2y: int


def read_cameras(paths, level_id=0x29):
    result = {}
    for path in paths:
        cams = []
        for number, line in enumerate(Path(path).read_text().splitlines(), 1):
            words = line.split()
            if not words or words[0].startswith('#'):
                continue
            if len(words) < 7:
                raise ValueError(f'{path}:{number}: registro incompleto')
            if int(words[1], 16) == 0x14 and int(words[2], 16) == level_id:
                cams.append(Camera(int(words[0]), *(int(v, 16) for v in words[3:7])))
        if not cams:
            raise ValueError(f'{path}: sin camaras del nivel {level_id:02x}')
        result[str(path)] = cams
    return result


class LevelPlanes:
    @classmethod
    def load(cls, descriptor):
        obj = cls()
        descriptor = Path(descriptor)
        raw = json.loads(descriptor.read_text(encoding='utf-8'))
        obj.camera = raw['camera']
        obj.name = raw['name']
        obj.data_path = ROOT / raw['out']['d']
        data = obj.data_path.read_bytes()
        obj.sha256 = hashlib.sha256(data).hexdigest()
        if data[:4] != b'SMWD':
            raise ValueError('no es SMWD')
        ver, obj.width, obj.height, nblk, cols, rows, obj.sky = struct.unpack_from('>7H', data, 4)
        if ver != 1 or cols * 16 != obj.width or rows * 16 != obj.height:
            raise ValueError('version/dimensiones SMWD invalidas')
        offs = struct.unpack_from('>6I', data, 18)
        expected = (nblk * 96, cols * rows, (obj.height + 1) * 2, 0,
                    obj.height * 192, obj.height * 14)
        for offset, size in zip(offs, expected):
            if offset < 42 or offset + size > len(data):
                raise ValueError('seccion SMWD fuera del blob')
        blocks = [[decode_planar(data[offs[0] + b * 96 + y * 6:
                                     offs[0] + b * 96 + y * 6 + 6], 16)
                   for y in range(16)] for b in range(nblk)]
        obj.pf1 = [bytearray(obj.width) for _ in range(obj.height)]
        for by in range(rows):
            for bx in range(cols):
                block = blocks[data[offs[1] + by * cols + bx]]
                for y in range(16):
                    obj.pf1[by * 16 + y][bx * 16:bx * 16 + 16] = block[y]
        lix = struct.unpack_from(f'>{obj.height + 1}H', data, offs[2])
        if list(lix) != sorted(lix) or offs[3] + lix[-1] * 8 > len(data):
            raise ValueError('indice eventos invalido')
        obj.events = [[tuple(v for j, v in enumerate(struct.unpack_from('>HHBBH', data, offs[3] + k * 8))
                             if j != 3) for k in range(lix[y], lix[y + 1])]
                      for y in range(obj.height)]
        obj.pf2 = [decode_planar(data[offs[4] + y * 192:offs[4] + (y + 1) * 192], 512)
                   for y in range(obj.height)]
        obj.pf2pal = [struct.unpack_from('>7H', data, offs[5] + y * 14) for y in range(obj.height)]
        return obj


def pf2_window(level, camera, sy, mode='oracle', rest_l2y=192, width=256):
    y0 = level.camera['y0']
    y = y0 + sy if mode == 'current' else y0 + camera.l2y - rest_l2y + sy
    x = camera.x // 2 if mode == 'current' else camera.l2x
    if not 0 <= y < level.height:
        raise ValueError(f'PF2 Y={y} fuera del blob; falta fondo para esta camara')
    x %= 512
    repeated = level.pf2[y] * ((x + width + 511) // 512)
    return repeated[x:x + width]


def selftest():
    for row in (bytearray([0] * 16), bytearray([0, 1, 2, 3] * 4), bytearray([4] * 16)):
        planar = bytes(sum(((row[b * 8 + k] >> p) & 1) << (7 - k) for k in range(8))
                       for p in range(3) for b in range(2))
        assert decode_planar(planar, 16) == row
        reduced = decode_planar(planar[:4], 16, 2)
        assert (reduced == row) == (max(row) <= 3)
    dummy = LevelPlanes()
    dummy.camera = {'y0': 0}
    dummy.height = 2
    dummy.pf2 = [bytearray(x % 8 for x in range(512)), bytearray([3] * 512)]
    assert pf2_window(dummy, Camera(0, 0, 0, 511, 192), 0)[:2] == bytearray([7, 0])
    assert max(pf2_window(dummy, Camera(0, 0, 0, 0, 193), 0)) == 3
    print('Autoprueba: 0/3/4, reconstruccion planar, wrap X y desplazamiento Y OK')


if __name__ == '__main__':
    selftest()
