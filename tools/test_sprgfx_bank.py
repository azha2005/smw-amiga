#!/usr/bin/env python3
"""SG3F/2: ausencia bob, controles, directorio completo y limites estrictos."""
import struct
import unittest
import sprgfx_final as F
import sprgfx_bank as B


class BankTests(unittest.TestCase):
    def fixture(self):
        bank = F.Bank()
        rows = [[1]]
        pair = [bank.add(F.channel(rows, 0, p)) for p in (0, 1)]
        pose = dict(origin=[0,0], width=1, height=1, columns=1, priority=2,
                    tiles=[[0,0,0,8,0,0,0]], streams=[pair],
                    row_maps=[[(0,1,1,0x123)]], source=0xffffffff, mask=0xffffffff)
        meta = bytearray(F.serialize([pose], bank))
        struct.pack_into('>H', meta, 4, 2)
        decoded = B.decode(meta, bytes(bank.data))
        tables = meta+B.directory(meta, decoded)+struct.pack('>4sI', b'S2IX',len(meta))
        return bytearray(tables), bytes(bank.data), len(meta)

    def test_roundtrip_and_legacy_rejection(self):
        tables, chip, _ = self.fixture()
        self.assertEqual(F.deserialize(tables, chip)[0]['rows'], [[1]])
        tables[:4] = b'SG2A'
        with self.assertRaises(F.FormatError):
            F.deserialize(tables, chip)

    def test_corrupt_offsets_bob_directory(self):
        tables, chip, ms = self.fixture()
        row_offsets, = struct.unpack_from('>I', tables, 24+20)
        row_map, = struct.unpack_from('>I', tables, row_offsets)
        mutations = [(24+24, '>I', 0), (24+28, '>I', 0),
                     (24+20, '>I', ms+2), (len(tables)-4, '>I', ms+2),
                     (ms+8+8, '>I', 0), (ms+8+6, '>H', 2),
                     (ms+20, '>H', 1), (ms+8, '>I', 24),
                     (row_map+4, '>B', 2)]
        for offset, fmt, value in mutations:
            with self.subTest(offset=offset):
                bad = bytearray(tables)
                struct.pack_into(fmt, bad, offset, value)
                with self.assertRaises(F.FormatError):
                    B.deserialize_bank(bad, chip)

    def test_dma_control_terminator_padding_alignment(self):
        tables, chip, _ = self.fixture()
        pairs, = struct.unpack_from('>I', tables, 24+16)
        lo, = struct.unpack_from('>I', tables, pairs)
        for offset in (lo, lo+11, lo+5):
            bad = bytearray(chip)
            bad[offset] ^= 1
            with self.assertRaises(F.FormatError):
                B.deserialize_bank(tables, bad)
        struct.pack_into('>I', tables, pairs, lo+1)
        with self.assertRaises(F.FormatError):
            B.deserialize_bank(tables, chip)

    def test_hard_limits(self):
        tables, chip, _ = self.fixture()
        for t,c in ((tables+bytes(98305-len(tables)),chip),
                    (tables,chip+bytes(65537-len(chip)))):
            with self.assertRaises(F.FormatError):
                B.deserialize_bank(t,c)


if __name__ == '__main__':
    unittest.main()
