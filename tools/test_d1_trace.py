#!/usr/bin/env python3
"""Pruebas de continuidad, recuperacion de ticks y rechazo de exportaciones incompletas."""
import struct,unittest
from d1_count_v2 import decode,metrics,EVENTS
from d1_count import count
class TraceTests(unittest.TestCase):
    def raw(self):
        b=bytearray(EVENTS+36);b[:4]=b'D1TR'
        struct.pack_into('>HHIIHHHH',b,4,2,20,4600,4,1,0,1000,3);struct.pack_into('>I',b,24,5)
        for i,(l,s,t) in enumerate([(0,0,9000),(0,0,8000),(2,2,7000),(3,3,6000)]):
            struct.pack_into('>IHHIII',b,32+20*i,i,l,s,50,25,t)
        for i,end in enumerate([7990,7010,6010]):struct.pack_into('>III',b,EVENTS+12*i,i+1,25,end)
        return b
    def test_multiple_events_retained(self):
        rows,ev,meta=decode(self.raw(),4);r=metrics(rows)
        self.assertEqual([e['logical_id'] for e in rows[2]['tick_events']],[1,2])
        self.assertEqual(r['intervals_without_completed_tick'],1);self.assertEqual(r['intervals_with_multiple_completed_ticks'],1)
        self.assertEqual(r['completed_tick_events'],3);self.assertEqual(r['net_uncompleted_ticks_at_last_vbl'],0)
        self.assertEqual(r['logic_cia_ticks']['samples'],3)
    def test_singular_still_rejects_two(self):
        rows,_,_=decode(self.raw(),4)
        with self.assertRaises(ValueError):count([dict(vbl=r['vbl'],logic_frame=r['logic_frame'],shown_frame=r['shown_frame'],photo_ticks=r['photo_ticks'],tick_ticks=20 if r['tick_events'] else None) for r in rows])
    def test_overflow_rejected(self):
        b=self.raw();struct.pack_into('>H',b,18,1)
        with self.assertRaises(ValueError):decode(b,4)
    def test_missing_event_rejected(self):
        b=self.raw();struct.pack_into('>I',b,EVENTS+12,4)
        with self.assertRaises(ValueError):decode(b,4)
    def test_event_outside_interval_rejected(self):
        b=self.raw();struct.pack_into('>I',b,EVENTS+8,8100)
        with self.assertRaises(ValueError):decode(b,4)
if __name__=='__main__':unittest.main()
