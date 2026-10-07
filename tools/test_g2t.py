#!/usr/bin/env python3
"""G2T: ventanas, reservas adyacentes y capacidad; sin ROM ni assets."""
import unittest
import contextlib
import io
import tempfile
from pathlib import Path

from g2t_audit import desired, windows, intervals, stable_assignment, place_variable, suffix
import scrollsim as S
from g2t_cal import build


class G2TTests(unittest.TestCase):
    def test_successive_rex_rows_need_horizontal_window(self):
        colors=[0]*16
        rows=[{} for _ in range(224)]
        rows[168],rows[169]={1:0},{1:0xfff}
        old=windows(rows,colors)
        new=windows(rows,colors,True)
        self.assertEqual((old[0]['lo'],old[0]['hi']),(169,168))
        self.assertEqual((new[0]['lo'],new[0]['hi']),(168,168))

    def test_actual_x_includes_both_mario_and_rex(self):
        colors=[0]*16
        colors[1]=0x123
        pose=dict(origin=[0,0],rows=[[1,1],[1,1]],row_maps=[[(1,1,1,0)],[(1,2,1,0xfff)]])
        mario={(250,10):(1,0),(1,12):(1,0)}
        # Mario and Rex using different colors on the same row is rejected.
        with self.assertRaises(ValueError):
            intervals(pose,40,10,mario,colors)
        mario={(250,9):(1,0),(1,12):(1,0)}
        ws=intervals(pose,40,10,mario,colors)
        transition=next(w for w in ws if w['antes']['linea']==11)
        self.assertEqual(transition['despues'],dict(linea=10,x=41,owners='R'))
        self.assertEqual(transition['antes'],dict(linea=11,x=40,owners='R'))
        restore=next(w for w in ws if w['antes']['linea']==12)
        self.assertEqual((restore['antes']['x'],restore['valor']),(1,0x123))

    def test_offscreen_rex_has_no_pixel_deadlines(self):
        pose=dict(origin=[0,0],rows=[[1],[1]],row_maps=[[(1,1,1,0)],[(1,2,1,0xfff)]])
        self.assertEqual(intervals(pose,283,168,{},[0]*16),[])

    def test_preserves_row_reservations(self):
        pose=dict(origin=[0,0],row_maps=[[(1,1,3,0x456)]])
        masks,colors=[0]*224,[0]*16
        masks[10],colors[3]=1<<3,0x123
        with self.assertRaises(ValueError):
            desired(pose,10,masks,colors)

    def test_stable_remap_protects_neighbor_mario(self):
        pose=dict(origin=[0,0],row_maps=[[(1,1,1,0x456)]])
        masks,colors=[0]*224,[0]*16
        masks[9],masks[11]=1<<1,1<<2
        mapping,status=stable_assignment(pose,10,masks,colors)
        self.assertEqual(status,'ok')
        self.assertNotIn(mapping[0x456],(1,2))

    def test_stable_failure_and_search_limit_are_distinct(self):
        pose=dict(origin=[0,0],row_maps=[[(1,1,1,0x456)]])
        masks=[0]*224
        masks[9]=0xfffe
        self.assertEqual(stable_assignment(pose,10,masks,[0]*16)[1],'sin_asignacion')
        self.assertEqual(stable_assignment(pose,10,[0]*224,[0]*16,0)[1],'indeterminado')

    def test_no_slot_is_not_no_window(self):
        move=dict(tipo='color',indice=1,valor=0xfff,lo=0,hi=0)
        self.assertEqual(len(place_variable([move],[],[0])[1]),1)
        self.assertFalse(place_variable([move],[],[1])[1])

    def test_controls_order_and_earlier_free_slot(self):
        moves=[dict(tipo='ctl',ordinal=i,lo=0,hi=2) for i in range(3)]
        lines,miss=place_variable([],moves,[1,0,2])
        self.assertFalse(miss)
        self.assertEqual([m['ordinal'] for line in lines for m in line],[0,1,2])

    def test_suffix_includes_moves_after_last_wait(self):
        class Mem:
            def r16(self,addr):
                return {0:0x6be3,2:0xfffe,4:0x182,6:0,
                        8:0x6cc9,10:0xfffe,12:0x182,14:0,
                        16:0x184,18:0,20:0x84,22:0}[addr-(216+220*64)]
        oldw,oldt=S.W,S.T0
        try:
            S.W,S.T0=256,-120
            result=suffix(Mem(),0,64)
        finally:
            S.W,S.T0=oldw,oldt
        self.assertEqual((result['ultimo_wait_h'],result['move_despues_wait']),(0xc8,2))
        self.assertEqual(result['x_modelo_siguiente'],263)

    def test_wrap_barrier_replaces_wait_and_is_unique(self):
        with tempfile.TemporaryDirectory(dir='work') as folder, contextlib.redirect_stdout(io.StringIO()):
            b=build(Path(folder,'cal.i'),True)
            mark=b'\xff\xdf\xff\xfe'
            self.assertEqual(b.data.count(mark),1)
            at=b.data.index(mark)
            # Sin un segundo WAIT255 después de la barrera: MOVE color.
            self.assertEqual(b.data[at+4:at+6],b'\x01\xa4')


if __name__=='__main__':
    unittest.main()
