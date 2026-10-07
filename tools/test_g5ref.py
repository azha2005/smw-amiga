#!/usr/bin/env python3
"""G5a-bis: compatibilidad, ventanas y orden sin ROM ni derivados."""
import unittest
import struct

from g5ref import color_writes, first_compatible, mask_table, place_writes, simulate, table_rows, plan_frame
import sprgfx_bank as B
import sprgfx_final as F


class ReferenceTests(unittest.TestCase):
    def pose(self, color):
        return dict(origin=[0, 0], row_maps=[[(1, 2, 3, color)]])

    def test_row_collision_with_mario(self):
        masks, colors = [0] * 224, [0] * 16
        masks[10], colors[3] = 1 << 3, 0x123
        self.assertIsNone(first_compatible([0], [self.pose(0x456)], 10, masks, colors))
        self.assertEqual(first_compatible([0], [self.pose(0x123)], 10, masks, colors), 0)

    def test_directory_order_is_not_best_deadline(self):
        poses, masks, colors = [self.pose(0x123), self.pose(0x456)], [0] * 224, [0] * 16
        self.assertEqual(first_compatible([1, 0], poses, 10, masks, colors), 1)
        self.assertEqual(first_compatible([0, 1], poses, 10, masks, colors), 0)

    def test_empty_window_cannot_be_hidden(self):
        colors = [0] * 16
        colors[3] = 0x123
        desired = [{3: 0x123}, {3: 0x456}] + [{}] * 222
        writes = color_writes(desired, colors)
        self.assertEqual((writes[0]['lo'], writes[0]['hi']), (1, 0))
        lines, missed = place_writes(writes, [])
        self.assertEqual(len(missed), 1)
        self.assertEqual(simulate(lines, colors)[1][3], 0x123)

    def test_latest_line_capacity_is_eight(self):
        moves = [dict(tipo='color', indice=i, valor=i, lo=0, hi=1) for i in range(1, 10)]
        lines, missed = place_writes(moves, [])
        self.assertFalse(missed)
        self.assertEqual([len(lines[y]) for y in (0, 1)], [1, 8])
        moves = [dict(tipo='color', indice=i, valor=i, lo=0, hi=0) for i in range(1, 10)]
        lines, missed = place_writes(moves, [])
        self.assertEqual((len(lines[0]), len(missed)), (8, 1))

    def test_arm_preserves_pt_before_controls(self):
        arm = [dict(tipo='pt' if i < 8 else 'pos', ordinal=i, lo=0, hi=2) for i in range(16)]
        lines, missed = place_writes([], arm)
        self.assertFalse(missed)
        self.assertEqual([m['ordinal'] for line in lines for m in line], list(range(16)))
        self.assertEqual([len(line) for line in lines[:3]], [0, 8, 8])

    def test_arm_above_screen_has_no_window(self):
        arm = [dict(tipo='pt', lo=0, hi=-1)]
        _, missed = place_writes([], arm)
        self.assertEqual(len(missed), 1)

    def test_table_respects_vertical_flip_and_dynamic_names(self):
        gfx = bytearray(744 * 32)
        # Ficha 0: índice 1 en fila 0; ficha 1: índice 2 en fila 7.
        gfx[0] = 0x80
        gfx[32 + 15] = 0x80
        table = mask_table(gfx)
        ram = bytearray(0x2000)
        ram[0xd85:0xd87] = bytes((0, 0x20))
        recorded = [bytes((10, 20, 0, 0x80, 0))]
        rows = table_rows(ram, recorded, table)
        self.assertEqual(rows[27], 1 << 1)
        self.assertEqual(rows[20], 0)
        recorded = [bytes((10, 20, 1, 0, 0))]
        self.assertEqual(table_rows(ram, recorded, table)[27], 1 << 2)

    def test_priority_is_first_opaque_oam(self):
        gfx = bytearray(744 * 32)
        for y in range(8):
            gfx[2 * y] = 0x80
        ram = bytearray(0x2000)
        ram[0xd85:0xd87] = bytes((0, 0x20))
        tiles, bank = [[0, 0, 0, 8, 0, 0, 1]], F.Bank()
        rows = [[1] for _ in range(8)]
        streams = [[bank.add(F.channel(rows, 0, p)) for p in (0, 1)]]
        pose = dict(origin=[0, 0], width=1, height=8, columns=1, priority=2,
                    tiles=tiles, streams=streams, row_maps=[[(1, 1, 1, 0x123)]] * 8,
                    source=0xffffffff, mask=0xffffffff)
        tables = F.serialize([pose], bank)
        poses = [dict(pose, rows=rows)]
        pals = struct.pack('>16H', 0, 0x123, *([0] * 14)) * 8
        rex, mario = bytes((10, 20, 0, 0x22, 0)), bytes((10, 20, 0, 0x20, 0))
        for recorded, expected in (([rex, mario], 8), ([mario, rex], 0)):
            rec = dict(frame=1, slot=0, num=0xab, sx=10, sy=20, tiles=tiles,
                       priority=2, ram=ram, recorded=recorded)
            plan, _ = plan_frame([rec], poses, {B.shape(pose): [0]}, tables, [0] * 8,
                                 pals, gfx, mask_table(gfx), gfx[:32])
            self.assertEqual(plan['contadores']['prioridad_distinta'], expected)


if __name__ == '__main__':
    unittest.main()
