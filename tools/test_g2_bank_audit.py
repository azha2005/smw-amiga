#!/usr/bin/env python3
"""G2: corrupción de tablas/DMA, padding y flujos compartidos inmutables."""
import struct
import unittest
from unittest.mock import patch

import g2_bank_audit as A
import sprgfx_final as F


class AuditTests(unittest.TestCase):
    def fixture(self, width=1):
        bank = F.Bank()
        rows = [[1] + [0] * (width - 1)]
        pair = [bank.add(F.channel(rows, 0, upper)) for upper in (0, 1)]
        pose = dict(origin=[0, 0], width=width, height=1, columns=1, priority=2,
                    tiles=[[0, 0, 0, 8, 0, 0, 0]], streams=[pair],
                    row_maps=[[(0, 1, 1, 0x123)]], source=0xffffffff, mask=0xffffffff)
        metadata = bytearray(F.serialize([pose], bank))
        struct.pack_into('>4sH', metadata, 0, b'SG2A', 2)
        return metadata, bytes(bank.data)

    def test_direct_decode_and_directory(self):
        metadata, chip = self.fixture()
        poses = A.decode(metadata, chip)
        self.assertEqual(poses[0]['rows'], [[1]])
        directory = A.directory(metadata, poses)
        self.assertEqual(struct.unpack_from('>4sHH', directory), (b'G2IX', 1, 1))
        with self.assertRaises(F.FormatError):
            F.deserialize(metadata, chip)  # no se confunde con el conversor final

    def test_exact_aligned_overlap_and_determinism(self):
        lo = F.channel([[3] * 16] * 4, 0, 0)
        hi = F.channel([[3] * 16] * 4, 0, 1)
        a = A.compact([lo, hi, lo, bytes(8)])
        b = A.compact([bytes(8), hi, lo])
        self.assertEqual(a, b)
        data, offsets = a
        for blob, off in offsets.items():
            self.assertEqual(off % 8, 0)
            self.assertEqual(data[off:off + len(blob)], blob)
        self.assertEqual(F.decode_channels(data[offsets[lo]:offsets[lo] + len(lo)],
                                          data[offsets[hi]:offsets[hi] + len(hi)], 4), [[3] * 16] * 4)

    def test_copper_image_must_work_for_every_reservation(self):
        cg = [0] * 256
        cg[129:132] = [31, 992, 31744]
        truth = [[(0, 1), (0, 2), (0, 3)]]
        tiles = [[0, 0, 0, 8, 0, 0, 0]]
        specs = [dict(name='first', tiles=tiles, priority=2,
                      reserved_rows=[{k: 0 for k in range(1, 7)}]),
                 dict(name='second', tiles=tiles, priority=2,
                      reserved_rows=[{k: 0 for k in range(7, 14)}])]
        # Cada caso tiene solución; una imagen fija para ambos solo dispone
        # de dos índices para tres colores y debe rechazarse.
        for spec in specs:
            F.remap(truth, cg, spec['reserved_rows'])
        with patch.object(F, 'compose', return_value=(0, 0, truth)):
            result = A.copper_only(specs, None, cg)
        self.assertEqual(result['failed_shapes'], 1)
        self.assertEqual(result['witnesses'][0]['matched'], 2)
        self.assertEqual(result['witnesses'][0]['required'], 3)

    def test_invalid_tables_and_dma(self):
        metadata, chip = self.fixture()
        bad_table = bytearray(metadata)
        struct.pack_into('>I', bad_table, 24 + 20, len(metadata) + 8)
        bad_pair = bytearray(metadata)
        pair_table, = struct.unpack_from('>I', metadata, 24 + 16)
        struct.pack_into('>I', bad_pair, pair_table, 1)
        bad_control = bytearray(chip)
        lo, = struct.unpack_from('>I', metadata, pair_table)
        bad_control[lo] = 1
        bad_terminator = bytearray(chip)
        bad_terminator[lo + 11] = 1
        for table, data in ((metadata[:-1], chip), (bad_table, chip),
                            (bad_pair, chip), (metadata, bad_control), (metadata, bad_terminator)):
            with self.subTest(table=len(table), data=len(data)):
                with self.assertRaises(F.FormatError):
                    A.decode(table, data)

    def test_padding_must_be_transparent(self):
        metadata, chip = self.fixture(width=2)
        # Reducir W a uno y encender el segundo píxel del flujo bajo.
        struct.pack_into('>H', metadata, 24 + 4, 1)
        data = bytearray(chip)
        ptr, = struct.unpack_from('>I', metadata, 24 + 16)
        lo, = struct.unpack_from('>I', metadata, ptr)
        data[lo + 4] |= 0x40
        with self.assertRaisesRegex(F.FormatError, 'padding'):
            A.decode(metadata, data)


if __name__ == '__main__':
    unittest.main()
