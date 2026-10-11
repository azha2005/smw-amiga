"""Puerta G7-C sin assets: propiedad DMA, cadenas y paleta compartida."""
import struct
import unittest
from unittest.mock import patch

import numpy as np
import g7_hw_support as H
from g0bench import control


class Memory:
    def __init__(self):
        self.data = bytearray(256 * 1024)

    def r16(self, at):
        return struct.unpack_from('>H', self.data, at)[0]

    def r32(self, at):
        return struct.unpack_from('>I', self.data, at)[0]

    def w16(self, at, v):
        struct.pack_into('>H', self.data, at, v)

    def w32(self, at, v):
        struct.pack_into('>I', self.data, at, v)


class Game:
    def __init__(self):
        self.mem = Memory()
        self.s = dict(DC_REND=0, MSPR_WORDS=84, CL_VBL=216, CL_VBLSZ=128,
                      CL_LINES=344, SEG=256)
        self.dc = 0x200
        self.mem.w32(0x300, 0x1000)
        self.cpu = self
        self.back = 0x10000
        for ch in range(4, 8):
            at = self.back + self.s['CL_VBL'] + 4 + 16 * (ch - 4)
            self.mem.w16(at + 2, 0)
            self.mem.w16(at + 6, 0x800)
        for off in range(96, 128, 4):
            self.mem.w32(self.back + self.s['CL_VBL'] + off, 0x01FE0000)

    def addr(self, name):
        assert name == 'g_sbuf'
        return 0x300

    def read(self, at, n):
        return bytes(self.mem.data[at:at+n])

    def sprite(self, pair, start, stop, index, chain=False):
        for upper in (0, 1):
            ch = pair + upper
            pt = 0x1000 + ch * 168
            pos, ctl = control(136, start + 44, stop + 44, ch)
            self.mem.w16(pt, pos)
            self.mem.w16(pt + 2, ctl)
            pt += 4
            for _ in range(stop-start):
                for bit in range(2):
                    self.mem.w16(pt, 0xFFFF if index >> (2*upper+bit) & 1 else 0)
                    pt += 2
            if chain:
                pos, ctl = control(144, stop + 45, stop + 47, ch)
                self.mem.w16(pt, pos)
                self.mem.w16(pt + 2, ctl)
                pt += 4
                for _ in range(2):
                    for bit in range(2):
                        self.mem.w16(pt, 0xFFFF if index >> (2*upper+bit) & 1 else 0)
                        pt += 2


class SupportTests(unittest.TestCase):
    def setUp(self):
        self.g = Game()
        self.overlay = np.full((224,256), -1, dtype=np.int32)
        for y in range(158,166):
            self.overlay[y,169:174] = (0,0x851,0xDA3,0xFD7,0xFFF)

    def words(self, mem, back, cl, seg, row):
        wait = (((row+43)&255)<<8|0xE3,0xFFFE)
        return [wait,wait]+[(0x180+2*i,i*0x111) for i in range(1,8)], None

    def prepare(self):
        with patch.object(H.P,'overlays',return_value=self.overlay.copy()), \
                patch.object(H.P.T,'segment_words',side_effect=self.words):
            return H.prepare(self.g,0,self.g.back,bytes(320),b'',self.overlay,31)

    def test_stopped_controls_are_free(self):
        image, audit = H.dma_image(self.g,0,self.g.back)
        self.assertFalse(image.any())
        self.assertFalse(any(a['spans'] for a in audit))

    def test_transparent_data_still_owns_dma(self):
        self.g.sprite(2,130,162,0)
        image, audit = H.dma_image(self.g,0,self.g.back)
        self.assertFalse(image.any())
        self.assertEqual(audit[2]['spans'][0]['stop'],162)
        with self.assertRaisesRegex(AssertionError,'DMA activo'):
            self.prepare()

    def test_chain_keeps_controls_and_indices(self):
        self.g.sprite(0,130,132,5,chain=True)
        image, audit = H.dma_image(self.g,0,self.g.back)
        self.assertEqual(len(audit[0]['spans']),2)
        self.assertEqual(image[130,136],1<<5)
        self.assertEqual(image[132,144],0)
        self.assertEqual(image[133,144],1<<5)

    def test_disjoint_destinations_and_shared_indices(self):
        self.g.sprite(0,130,162,5)
        residual, prime, flows, info = self.prepare()
        self.assertFalse((residual>=0).any())
        self.assertNotIn(5,info['mapping'].values())
        self.assertEqual(info['pixels'],40)
        self.assertEqual(info['loads_x'][-1],295)
        self.assertEqual(sum(map(len,flows)),80)
        self.assertEqual(prime[0],157)

    def test_rejects_copper_rearming_free_pair(self):
        old=self.words
        def rearm(*args):
            words,_=old(*args)
            return words+[(0x150,0xCC90)],None
        self.words=rearm
        with self.assertRaisesRegex(AssertionError,'rearmada'):
            self.prepare()

    def test_rejects_shared_color_reload(self):
        old=self.words
        def reload(*args):
            words,_=old(*args)
            if args[-1]==161:
                words += [(0x1A2,0x123)]
            return words,None
        self.words=reload
        with self.assertRaisesRegex(AssertionError,'recarga compartida'):
            self.prepare()

    def test_rejects_one_more_prefix_move(self):
        old=self.words
        def longer(*args):
            words,_=old(*args)
            if args[-1]==158:
                words += [(0x192,0)]
            return words,None
        self.words=longer
        with self.assertRaisesRegex(AssertionError,'fila siguiente'):
            self.prepare()

    def test_reuses_colors_even_when_mario_owns_indices(self):
        self.g.sprite(0,130,162,5)
        cols=np.zeros((224,16,256),dtype=np.int32)
        for i,c in enumerate((0xFFF,0,0x851,0xDA3,0xFD7),1):
            cols[:,i,:]=c
        with patch.object(H,'sprite_palette',return_value=(cols,np.full((224,256),4))):
            _,prime,_,info=self.prepare()
        self.assertIsNone(prime)
        self.assertEqual(info['mapping']['4055'],5)
        self.assertEqual(info['loads_x'],[])

    def test_rejects_pair_behind_pf1(self):
        with patch.object(H,'sprite_palette',return_value=(np.zeros((224,16,256)),np.zeros((224,256)))):
            with self.assertRaisesRegex(AssertionError,'PF1 tapa'):
                self.prepare()

    def joint(self, primes=(), assigned=None, colors=None):
        if colors is None:
            colors=np.zeros((224,16,256),dtype=np.int32)
            colors[:,1,:]=0xFFF
        if assigned is None:
            assigned=[(dict(pair=[2,3],mapping={'4095':1}),self.overlay==0xFFF)]
        with patch.object(H,'sprite_palette',return_value=(colors,np.full((224,256),4))):
            return H.validate_plans(self.g,0,self.g.back,primes,assigned,self.overlay)

    def test_identical_joint_prefix_is_emitted_once(self):
        prime=(157,dict(words=[(0x1A2,0xFFF)]))
        self.assertEqual(self.joint([prime,prime]),{157:[(0x1A2,0xFFF)]})

    def test_different_joint_prefixes_need_joint_schedule(self):
        primes=[(157,dict(words=[(0x1A2,0xFFF)])),(157,dict(words=[(0x1A2,0x123)]))]
        with self.assertRaisesRegex(AssertionError,'plan conjunto'):
            self.joint(primes)

    def test_joint_plan_preserves_original_hardware_color(self):
        self.g.sprite(0,130,162,5)
        old=np.zeros((224,16,256),dtype=np.int32);old[:,5,:]=0xFFF
        new=old.copy();new[:,5,:]=0
        with patch.object(H,'sprite_palette',side_effect=[(old,None),(new,np.full((224,256),4))]):
            with self.assertRaisesRegex(AssertionError,'otro sprite alterado'):
                H.validate_plans(self.g,0,self.g.back,[],[],self.overlay)

    def test_joint_plan_checks_every_assigned_pixel(self):
        with self.assertRaisesRegex(AssertionError,'colores incompatibles'):
            self.joint(colors=np.zeros((224,16,256),dtype=np.int32))

    def test_joint_plan_rejects_overlapping_destinations(self):
        assignment=(dict(pair=[2,3],mapping={'4095':1}),self.overlay==0xFFF)
        with self.assertRaisesRegex(AssertionError,'destinos hardware solapados'):
            self.joint(assigned=[assignment,assignment])


if __name__=='__main__':
    unittest.main()
