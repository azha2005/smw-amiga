#!/usr/bin/env python3
"""G2T-B3: formato y recorte exacto de G5EV con poses sinteticas, sin ROM."""
import struct
import unittest
import zlib

import g5bank_env as E


def pose():
    return dict(width=8, height=3, rows=[[1, 0, 1, 0, 0, 2, 0, 1],
                                       [0] * 8, [1, 1, 0, 2, 0, 1, 0, 0]],
                row_maps=[[(0, 1, 1, 0x123), (0, 2, 2, 0x456)], [],
                          [(0, 1, 1, 0x789), (0, 2, 2, 0x456)]])


class G5EnvTests(unittest.TestCase):
    def setUp(self):
        self.poses = [pose(), dict(width=1, height=1, rows=[[0]], row_maps=[[]])]
        self.data = E.build(b'idx sintetico', b'dma sintetico', self.poses)
        self.heights = [p['height'] for p in self.poses]

    def test_header_offsets_and_crc(self):
        self.assertEqual(self.data[:4], b'G5EV')
        self.assertEqual(struct.unpack_from('>HHII', self.data, 4),
                         (1, 2, zlib.crc32(b'idx sintetico'), zlib.crc32(b'dma sintetico')))
        a, b = struct.unpack_from('>II', self.data, 16)
        self.assertEqual(a, 24)
        self.assertEqual(b, a + len(E.pose_blob(self.poses[0])))
        self.assertEqual(self.data[b:], b'\0\0\0')

    def test_roundtrip_gaps_transparency_and_row_colors(self):
        rows = E.read(self.data, self.heights, b'idx sintetico', b'dma sintetico')
        self.assertTrue(E.check(self.poses, rows))
        self.assertEqual(rows[0], [{1: (0x123, 0x85), 2: (0x456, 0x20)}, {},
                                  {1: (0x789, 0x23), 2: (0x456, 0x08)}])
        self.assertEqual(rows[1], [{}])

    def test_both_edges_keep_exact_pixels_with_holes(self):
        rows = E.read(self.data, self.heights)[0]
        for x0 in range(-9, 258):
            for r, row in enumerate(self.poses[0]['rows']):
                for d, (_, mask) in rows[r].items():
                    want = [x0 + x for x, v in enumerate(row) if v == d and 0 <= x0 + x < 256]
                    got = [x0 + x for x in range(8) if mask >> x & 1 and 0 <= x0 + x < 256]
                    self.assertEqual(got, want)
        # Un extremo (primer/ultimo) no puede sustituir esta mascara.
        self.assertEqual([x for x in range(1, 7) if rows[0][1][1] >> x & 1], [2])

    def test_full_24_bit_mask(self):
        p = dict(width=24, height=1, rows=[[1] * 24], row_maps=[[(0, 1, 1, 0xfff)]])
        self.assertEqual(E.read(E.build(b'', b'', [p]), [1]), [[{1: (0xfff, 0xffffff)}]])

    def test_negative_color_is_detected(self):
        data = bytearray(self.data)
        data[24 + 2 + 2] ^= 1
        self.assertFalse(E.check(self.poses, E.read(data, self.heights)))

    def test_reject_header_crc_and_pose_count(self):
        for off in (0, 5, 7, 16):
            data = bytearray(self.data)
            data[off] ^= 1
            with self.assertRaises(ValueError):
                E.read(data, self.heights)
        with self.assertRaises(ValueError):
            E.read(self.data, self.heights, b'otro banco', b'dma sintetico')
        with self.assertRaises(ValueError):
            E.read(self.data, self.heights, b'idx sintetico', b'otro dma')

    def test_reject_truncation_extra_bytes_and_bad_palette_entry(self):
        for size in range(len(self.data)):
            with self.assertRaises(ValueError):
                E.read(self.data[:size], self.heights)
        with self.assertRaises(ValueError):
            E.read(self.data + b'\0', self.heights)
        data = bytearray(self.data)
        data[24 + 2 + 12 + 1] = 255  # primera fila, primer indice de paleta
        with self.assertRaises(ValueError):
            E.read(data, self.heights)

    def test_reject_invalid_dimensions_and_check_incomplete_rows(self):
        p = pose()
        p['height'] += 1
        with self.assertRaises(ValueError):
            E.pose_blob(p)
        p = pose()
        p['width'] = 25
        p['rows'] = [[0] * 25] * 3
        with self.assertRaises(ValueError):
            E.pose_blob(p)
        rows = E.read(self.data, self.heights)
        self.assertFalse(E.check(self.poses, rows[:1]))
        rows[0].pop()
        self.assertFalse(E.check(self.poses, rows))


if __name__ == '__main__':
    unittest.main()
