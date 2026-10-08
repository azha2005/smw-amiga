#!/usr/bin/env python3
"""G2T-A: modelo horizontal calibrado; sin ROM ni assets (regress.py)."""
import unittest

import g2t_ref as T


def seg(last=None, nb=7, free=-120):
    return dict(nb=nb, last=last, loads=[], wrap=False, free=free)


def segs(**special):
    out = [seg() for _ in range(T.ROWS)]
    for row, s in special.items():
        out[int(row[1:])] = s
    return out


def uses_from(rows):
    """{fila: {indice: uso}} desde [(fila, indice, color, x0, x1, dueno)]."""
    uses = {}
    for rr, i, color, x0, x1, owner in rows:
        uses.setdefault(rr, {})[i] = dict(color=color, first=x0, last=x1, owners={owner})
    return uses


class G2TRefTests(unittest.TestCase):
    def test_knee_step_measured(self):
        self.assertEqual(T.advance(231), 243)
        self.assertEqual(T.advance(223), 239)
        self.assertEqual(T.advance(239), 247)
        self.assertEqual(T.advance(243), 251)
        self.assertEqual(T.advance(199, 4), 251)         # sonda WAIT 94 nop4: 215 231 243 251

    def test_contiguous_black_white_uses_gap_after_last_pixel(self):
        colors = [0] * 16
        colors[1] = 0x123
        uses = uses_from([(168, 1, 0x000, 240, 250, 'R'), (169, 1, 0xfff, 240, 250, 'R')])
        trans = T.transitions(uses, colors)
        self.assertEqual([(t['desde'], t['hasta'], t['valor']) for t in trans],
                         [(-1, 168, 0x000), (168, 169, 0xfff)])
        lines, plans, missed = T.place(trans, segs(s168=seg(last=255)))
        self.assertFalse(missed)
        second = trans[1]
        self.assertEqual(second['segmento'], 168)
        self.assertGreaterEqual(second['x'], 256)       # tras x = 250 y la carga en 255
        self.assertEqual(T.simulate(uses, trans, colors), [])

    def test_mario_neighbour_restores_photo_palette(self):
        colors = [0] * 16
        colors[3] = 0x6a5                               # R_PAL de esa foto, no paleta 0
        uses = uses_from([(100, 3, 0x0f0, 40, 60, 'R'), (101, 3, 0x6a5, 10, 20, 'M')])
        trans = T.transitions(uses, colors)
        self.assertEqual(trans[-1]['valor'], 0x6a5)
        lines, plans, missed = T.place(trans, segs())
        self.assertFalse(missed)
        self.assertEqual(T.simulate(uses, trans, colors), [])

    def test_offscreen_sprite_has_no_transitions(self):
        pose = dict(origin=[0, 0], rows=[[1, 1]], row_maps=[[(0, 1, 1, 0xfff)]])
        uses = T.uses_of(pose, 300, 50, {}, [0] * 16)
        self.assertEqual(T.transitions(uses, [0] * 16), [])

    def test_directory_order_first_variant_with_plan(self):
        tried = []

        def attempt(n):
            tried.append(n)
            return ([dict(indice=1)] if n < 7 else []), n
        n, found, witness = T.choose([4, 7, 9], attempt)
        self.assertEqual((n, tried, witness['variante']), (7, [4, 7], 4))
        n, found, witness = T.choose([4, 5], attempt)
        self.assertIsNone(n)

    def test_no_slot_after_last_load_is_reported(self):
        colors = [0] * 16
        rows = []
        for i in range(1, 8):                           # siete índices cambian a la vez
            rows += [(168, i, 0x100 * i, 240, 255, 'R'), (169, i, 0x10 * i, 240, 255, 'R')]
        uses = uses_from(rows)
        trans = T.transitions(uses, colors)
        lines, plans, missed = T.place(trans, segs(s168=seg(last=255)))
        # tras una carga en 255 caben cinco con borrado de 7 (k = 12 - nb)
        self.assertEqual(len(missed), 2)
        self.assertEqual(len(lines[168]), 5)

    def test_capacity_rule_end_by_next_borrado(self):
        self.assertEqual(T.schedule(seg(last=255), seg(nb=9), [256] * 3, 10)['pos'], [263, 271, 279])
        self.assertIsNone(T.schedule(seg(last=255), seg(nb=9), [256] * 4, 10))
        self.assertEqual(len(T.schedule(seg(last=255), seg(nb=7), [256] * 5, 10)['pos']), 5)
        self.assertIsNone(T.schedule(seg(last=255), seg(nb=7), [256] * 6, 10))
        self.assertIsNone(T.schedule(seg(last=255), seg(nb=14), [256], 10))   # no medido

    def test_wait_needs_idle_copper(self):
        p = T.schedule(seg(last=183), seg(nb=7), [231], 10)
        self.assertEqual((p['tipo'], p['pos'][0]), ('cadena', 231))
        p = T.schedule(seg(last=None), seg(nb=7), [231], 10)
        self.assertEqual((p['tipo'], p['h'], p['pos'][0]), ('wait', 0xbc, 231))
        p = T.schedule(seg(last=None), seg(nb=8), [256] * 4, 10)
        self.assertEqual((p['tipo'], p['h'], p['pos']), ('wait', 0xd0, [263, 271, 279, 287]))
        self.assertIsNone(T.schedule(seg(last=None), seg(nb=8), [256] * 5, 10))

    def test_barrier255_never_gets_a_suffix(self):
        self.assertIsNone(T.schedule(seg(last=None), seg(nb=7), [0], T.WRAP_SEG))
        self.assertEqual(T.schedule(seg(), seg(), [], T.WRAP_SEG)['tipo'], 'vacio')

    def test_suffix_keeps_layer1_and_rederives_positions(self):
        L = 40
        words = [((L + T.V0 - 1) << 8 | 0xe3, 0xfffe)] * 2 + [(0x182 + 2 * k, k) for k in range(7)]
        words += [((L + T.V0) << 8 | 0xbd, 0xfffe), (0x184, 1), (0x186, 2)]   # cargas en 231, 243
        plan = T.schedule(seg(last=243), seg(nb=7), [0, 0], L)
        new = words + T.suffix_words(L, plan, [(1, 0xfff), (2, 0x0f0)])
        old_ev, new_ev = T.timeline(words, L), T.timeline(new, L)
        pf = lambda ev: [e for e in ev if 0x182 <= e[1] <= 0x19e]
        self.assertEqual(pf(old_ev), pf(new_ev))
        self.assertEqual([e[0] for e in new_ev if 0x1a2 <= e[1] <= 0x1be], plan['pos'])
        self.assertEqual(plan['pos'], [251, 259])


if __name__ == '__main__':
    unittest.main()
