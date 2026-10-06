"""Puertas sintéticas del recuento D1; no son medidas de rendimiento."""
import unittest

from d1_count import count, timing


def trace(n, omissions=()):
    rows = [dict(vbl=0, logic_frame=0, shown_frame=0,
                 photo_ticks=None, tick_ticks=None)]
    shown = 0
    for vbl in range(1, n + 1):
        presented = vbl not in omissions
        if presented:
            shown = vbl
        rows.append(dict(vbl=vbl, logic_frame=vbl, shown_frame=shown,
                         photo_ticks=vbl if presented else None, tick_ticks=vbl))
    return rows


class CounterTests(unittest.TestCase):
    def test_minimum_percentage_boundary(self):
        self.assertTrue(count(trace(1000, (500,)))["minimum_numeric_thresholds_met"])
        self.assertFalse(count(trace(999, (500,)))["minimum_numeric_thresholds_met"])
        self.assertFalse(count(trace(249))["minimum_numeric_thresholds_met"])

    def test_rolling_window_includes_both_edges(self):
        # Separación 249: ambas caben en una ventana250; separación250: no.
        close = count(trace(2000, (500, 749)))
        apart = count(trace(2000, (500, 750)))
        self.assertEqual(close["worst_window"]["omitted"], 2)
        self.assertFalse(close["minimum_numeric_thresholds_met"])
        self.assertEqual(apart["worst_window"]["omitted"], 1)
        self.assertTrue(apart["minimum_numeric_thresholds_met"])

    def test_streak_age_and_skipped_logical_photos(self):
        result = count(trace(2000, (500, 501)))
        self.assertEqual(result["max_streak"], 2)
        self.assertEqual(result["photo_age_logic_ticks"]["max"], 2)
        self.assertEqual(result["skipped_logical_photos_between_presentations"], 2)
        self.assertEqual(result["lost_logic_ticks"], 0)

    def test_missing_logic_tick_is_a_separate_counter(self):
        rows = trace(1000)
        for row in rows[500:]:
            row["logic_frame"] -= 1
            row["shown_frame"] -= 1
        rows[500]["tick_ticks"] = rows[500]["photo_ticks"] = None
        result = count(rows)
        self.assertEqual(result["lost_logic_ticks"], 1)
        self.assertEqual(result["omitted"], 1)
        self.assertEqual(result["skipped_logical_photos_between_presentations"], 0)

    def test_incomplete_or_inconsistent_trace_fails(self):
        missing = trace(1000)
        missing.pop(500)
        duration = trace(1000)
        duration[500]["photo_ticks"] = None
        future = trace(1000)
        future[500]["shown_frame"] += 1
        for rows in (missing, duration, future):
            with self.subTest(rows=rows[499:501]):
                with self.assertRaises(ValueError):
                    count(rows)

    def test_p99_uses_nearest_rank(self):
        self.assertEqual(timing(list(range(1, 1001)))["p99"], 990)
        self.assertEqual(timing([])["samples"], 0)


if __name__ == "__main__":
    unittest.main()
