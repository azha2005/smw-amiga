#!/usr/bin/env python3
"""G2T-B3: envolventes del Rex por pose, derivadas del banco G3 (bank.g5env).

El banco G3 trae por fila el mapa índice DMA -> color, pero no dónde está
cada índice en x: g2t_ref.py lo saca decodificando los flujos DMA. El
68000 no puede hacerlo por frame (el mismo coste que la parada de B2), así
que esta tabla lo precalcula una vez. El banco no se toca; el fichero va en
work/ (R9).

Formato (big endian), docs/instrucciones-g2t-b35.md §2.3, opción (a):
  'G5EV', versión u16 = 1, poses u16, CRC32 de bank.idx u32, de bank.dma u32
  poses x u32: offset de cada pose desde el principio del fichero
  por pose: npal u8, 0, npal x (d u8, 0, color u16), y por fila 0..h-1:
            n u8, n x (paleta u8, máscara u24): bit x = el índice d de esa
            entrada de paleta está en la columna x (0 = izquierda) de la fila.
La máscara (no solo primer/último) hace exacto el recorte por x < 0 o
x > 255: el 46 % de los pares fila-índice tiene huecos.

    python tools/g5bank_env.py --bank work/g3/bank --out work/g3/bank.g5env
"""
import argparse
import struct
import sys
import zlib
from pathlib import Path

MAGIC = b'G5EV'


def pose_blob(pose):
    """Bytes de una pose: paleta (d, color) y por fila (paleta, máscara)."""
    pal, rows = [], []
    for row, row_map in zip(pose['rows'], pose['row_maps']):
        cmap = {d: c for _, _, d, c in row_map}
        masks = {}
        for x, d in enumerate(row):
            if d:
                masks[d] = masks.get(d, 0) | 1 << x
        out = []
        for d in sorted(masks):
            key = (d, cmap[d])
            if key not in pal:
                pal.append(key)
            out.append((pal.index(key), masks[d]))
        rows.append(out)
    if len(pal) > 255 or pose['width'] > 24:
        raise ValueError('pose fuera del formato (paleta > 255 o ancho > 24)')
    b = bytearray(struct.pack('>BB', len(pal), 0))
    for d, c in pal:
        b += struct.pack('>BBH', d, 0, c)
    for out in rows:
        b += struct.pack('>B', len(out))
        for p, m in out:
            b += struct.pack('>B', p) + m.to_bytes(3, 'big')
    return bytes(b)


def build(tables, dma, poses):
    blobs = [pose_blob(p) for p in poses]
    head = MAGIC + struct.pack('>HHII', 1, len(poses), zlib.crc32(tables), zlib.crc32(dma))
    off = len(head) + 4 * len(poses)
    offs = []
    for b in blobs:
        offs.append(off)
        off += len(b)
    return head + b''.join(struct.pack('>I', o) for o in offs) + b''.join(blobs)


def read(data, heights):
    """Inverso: por pose, por fila, {d: (color, máscara)}."""
    if data[:4] != MAGIC:
        raise ValueError('no es G5EV')
    _, n, _, _ = struct.unpack_from('>HHII', data, 4)
    out = []
    for j in range(n):
        o, = struct.unpack_from('>I', data, 16 + 4 * j)
        npal = data[o]
        pal = [struct.unpack_from('>BBH', data, o + 2 + 4 * k) for k in range(npal)]
        o += 2 + 4 * npal
        rows = []
        for _ in range(heights[j]):
            cnt = data[o]
            o += 1
            row = {}
            for _ in range(cnt):
                p = data[o]
                m = int.from_bytes(data[o + 1:o + 4], 'big')
                row[pal[p][0]] = (pal[p][2], m)
                o += 4
            rows.append(row)
        out.append(rows)
    return out


def check(poses, env):
    """La tabla reproduce filas y colores de la pose decodificada del banco."""
    for pose, rows in zip(poses, env):
        for r, (row, row_map) in enumerate(zip(pose['rows'], pose['row_maps'])):
            cmap = {d: c for _, _, d, c in row_map}
            want = {}
            for x, d in enumerate(row):
                if d:
                    c, m = want.get(d, (cmap[d], 0))
                    want[d] = (c, m | 1 << x)
            if rows[r] != want:
                return False
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--bank', default='work/g3/bank')
    ap.add_argument('--out', default='work/g3/bank.g5env')
    a = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).parent))
    import sprgfx_bank as B
    import sprgfx_final as F
    F.derived_path(a.out)
    tables, dma = Path(a.bank + '.idx').read_bytes(), Path(a.bank + '.dma').read_bytes()
    poses, _ = B.deserialize_bank(tables, dma)
    data = build(tables, dma, poses)
    env = read(data, [p['height'] for p in poses])
    if not check(poses, env):
        print('G5EV: FALLO (la tabla no reproduce el banco)')
        return 1
    Path(a.out).write_bytes(data)
    print('G5EV: OK %s: %d poses, %d B' % (a.out, len(poses), len(data)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
