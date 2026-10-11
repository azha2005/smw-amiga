"""Contratos de la referencia G7, con datos sinteticos y sin ROM."""
import unittest

import numpy as np

import g7_color_plan as P
from g7_color_bound import certificate


class ColorPlanTests(unittest.TestCase):
    def words(self,row=80):
        wait=(((row+P.L.V0-1)&255)<<8|0xE3,0xFFFE)
        return [wait,wait]+[(0x180+2*r,r*0x111) for r in range(1,8)]

    def test_borrow_preserves_hardware_events(self):
        words=self.words()+[((80+P.L.V0)<<8|0x99,0xFFFE),(0x1A2,0xF00)]
        idx=np.ones(256,dtype=np.int8)
        overlay=np.full(256,-1);overlay[100:108]=0xFFF
        plan,why=P.plan_line(words,80,idx,overlay,7)
        self.assertIsNone(why)
        self.assertEqual(plan['mode'],'borrow')
        self.assertEqual(P.T.timeline(words,80)[-1],P.T.timeline(plan['words'],80)[-1])
        for x in (99,108):
            self.assertEqual(P.palette(plan['words'],80)[1,x],0x111)

    def test_calibrated_deadline_and_optional_margin(self):
        req=np.full((8,256),-1);req[1,10]=0x111;req[1,20]=0x222
        jobs,_=P.transitions(req,[0]*8)
        conservative,_=P.transitions(req,[0]*8,phase_max=7)
        self.assertEqual(jobs,[(11,20,0x182,0x222)])
        self.assertEqual(conservative,[(11,13,0x182,0x222)])

    def test_initial_move_requires_wait(self):
        words=P.schedule([(60,100,0x182,0xFFF)],-56,295,20,80)
        self.assertIsNotNone(words)
        self.assertTrue(words[0][0]&1)
        self.assertGreaterEqual(P.L.xh(words[0][0]&0xFE)+56,P.L.IDLE)

    def test_wrap_can_borrow_without_new_wait(self):
        row=P.L.WRAP_SEG
        words=self.words(row)
        idx=np.ones(256,dtype=np.int8)
        overlay=np.full(256,-1);overlay[150]=0xFFF
        plan,why=P.plan_line(words,row,idx,overlay,7)
        self.assertIsNone(why)
        self.assertEqual(plan['mode'],'borrow')
        self.assertEqual(len(plan['words']),len(words))

    def test_cache_bound_positive(self):
        uses={x:x for x in range(7)}
        uses.update({7:7,23:8})
        self.assertTrue(certificate(uses,[7,23])['feasible'])

    def test_cache_bound_future_uses_prevent_eviction(self):
        uses={x:x for x in range(7)}
        uses.update({16+x:x for x in range(7)})
        uses.update({7:7,23:8})
        self.assertFalse(certificate(uses,[7,23])['feasible'])


if __name__=='__main__':
    unittest.main()
