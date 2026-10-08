#!/usr/bin/env python3
"""Fixtures G5PR/B1 independientes de ROM: alineacion, indices y rechazo."""
import struct
import unittest
import os
import subprocess
from g2t_preplan import table_index, table_bytes


def fixture(row=223):
    # B1: frame 6150, variante 3, cuatro canales nulos; VBL vacio;
    # una fila WAIT con un MOVE COLOR. Firma impar en el buffer final.
    b1 = struct.pack('>IH', 6150, 3)+bytes(40)
    b1 += bytes.fromhex('00 01')
    b1 += struct.pack('>BBBBBBH', row, 1, 0x71, 0, 1, 2, 0x0456)
    signatures = struct.pack('>BH', row, 0xbeef)
    data = struct.pack('>4sHHII', b'G5PR', 1, 1, 1005, 16)+b1+signatures
    return data+(b'\0' if len(data) & 1 else b'')


class TableTests(unittest.TestCase):
    def test_literal_contract_with_unaligned_signature(self):
        data = fixture()
        self.assertEqual(table_index(data), {1005: 16})
        self.assertEqual(data[73:75], b'\xbe\xef')

    def test_empty_and_writer_independent_reader(self):
        self.assertEqual(table_index(b'G5PR\0\1\0\0'), {})
        plan = dict(frame=6150, variante=3, canales=[], vbl_moves=[],
                    sufijos={223: dict(tipo='wait', h=0x71, nop=0, k=1, moves=[[2, 0x456]])})
        self.assertEqual(table_bytes([(1005, plan, {223: 0xbeef})]), fixture())

    def test_every_truncation_rejected(self):
        data = fixture()
        for end in range(len(data)):
            with self.subTest(end=end), self.assertRaises(ValueError):
                table_index(data[:end])

    def test_index_corruption(self):
        for off in (0, 15, 17, 1000):
            data = bytearray(fixture())
            struct.pack_into('>I', data, 12, off)
            with self.subTest(off=off), self.assertRaises(ValueError):
                table_index(data)
        # Dos entradas con el mismo stamp: busqueda binaria ambigua.
        with self.assertRaises(ValueError):
            table_index(struct.pack('>4sHHIIII', b'G5PR', 1, 2, 5, 24, 5, 24))

    def test_wrap_row_and_bad_signature_row(self):
        with self.assertRaises(ValueError):
            table_index(fixture(211))
        data = bytearray(fixture())
        data[72] = 222
        with self.assertRaises(ValueError):
            table_index(data)

    def test_extra_bytes_and_bad_colour(self):
        with self.assertRaises(ValueError):
            table_index(fixture()+bytes(2))
        data = bytearray(fixture())
        data[69] = 16
        with self.assertRaises(ValueError):
            table_index(data)

    def test_partial_build_flags_rejected_before_build(self):
        env = dict(os.environ, SPR_BANK='', CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5')
        for flags, reason in (('-DREPLAY -DG5_PRE_EXT', 'requieren G5_PRE'),
                              ('-DREPLAY -DG5_PRE_PROBE', 'requieren G5_PRE'),
                              ('-DREPLAY -DG5_EMPTY', 'requieren G5_PRE'),
                              ('-DG5_PRE -DG5_PRE_EXT -DG5_PRE_PROBE', 'requiere REPLAY')):
            with self.subTest(flags=flags):
                result = subprocess.run(['sh', 'tools/game_build.sh'], env=dict(env, GDEFS=flags),
                                        capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(reason, result.stdout)


if __name__ == '__main__':
    unittest.main()
