#!/usr/bin/env python3
"""Contrato sintetico B2bis: clave de pose y bytes significativos del sprite."""
import unittest
import struct
from g5env_verify import key_of, image


class KeyTests(unittest.TestCase):
    def inputs(self):
        return bytearray([10, 50, 0, 0, 10, 66, 2, 0] + [0, 0xf0, 0, 0] * 2), bytes([2] * 4), bytes(8192)

    def test_position_is_not_pose(self):
        o, s, r = self.inputs()
        first, _ = key_of(o, s, r)
        o[0] = o[4] = 80
        o[1] += 15; o[5] += 15
        second, _ = key_of(o, s, r)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 40)

    def test_relative_y_tile_flip_pointer_affect_key(self):
        o, s, r = self.inputs()
        first, _ = key_of(o, s, r)
        for offset, value in ((5, 67), (2, 3), (3, 64)):
            changed = o.copy(); changed[offset] = value
            self.assertNotEqual(first, key_of(changed, s, r)[0])
        changed = bytearray(r); changed[0xd85] = 1
        self.assertNotEqual(first, key_of(o, s, changed)[0])

    def test_invalid_paths(self):
        o, s, r = self.inputs()
        for offset, value in ((3, 128), (4, 11), (5, 60)):
            changed = o.copy(); changed[offset] = value
            self.assertIsNone(key_of(changed, s, r)[0])
        self.assertIsNone(key_of(o, bytes(4), r)[0])
        self.assertIsNone(key_of(bytes([0, 0xf0, 0, 0] * 4), s, r)[0])

    def test_inactive_data_and_pixel_negative(self):
        spr = bytearray([0xa5] * 672)
        for offset in (0, 168, 336, 504):
            struct.pack_into('>HH', spr, offset, 0, 0)
        self.assertEqual(image(spr), bytes(640))
        struct.pack_into('>HH', spr, 0, 0x2c50, 0x2d00)
        before = image(spr)
        spr[4] ^= 1
        self.assertNotEqual(before, image(spr))
        spr[12] ^= 1
        after = image(spr)
        spr[100] ^= 1
        self.assertEqual(after, image(spr))


if __name__ == '__main__':
    unittest.main()
