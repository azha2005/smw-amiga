#!/usr/bin/env python3
"""Negativos de las reservas SG3: memoria, limites y scratch transitorio."""
import unittest
import memmap as M


class Symbols:
    values = dict(SG3_DMA_BYTES=64528, SG3_TABLE_BYTES=72724)
    def sym(self,name): return self.values[name]
    def has(self,name): return name in self.values


class MemoryTests(unittest.TestCase):
    def block(self,expr,size,flags,mem):
        model=M.Model()
        L=Symbols()
        M.classify(L,model,0,size,flags,mem,expr,None,None)
        for b in model.blocks: M.check_block(L,model,b)
        return model

    def test_dma_must_be_chip_and_large_enough(self):
        self.assertFalse(self.block('#SG3_DMA_ALLOC',65024,2,'chip').viol)
        self.assertIn('V-CHIP',{c for c,_ in self.block('#SG3_DMA_ALLOC',65024,4,'slow').viol})
        self.assertIn('V-SG3-BANK',{c for c,_ in self.block('#SG3_DMA_ALLOC',64000,2,'chip').viol})

    def test_tables_must_be_slow_and_large_enough(self):
        self.assertFalse(self.block('#SG3_TABLE_ALLOC',72728,4,'slow').viol)
        for size,flags,mem in ((72728,2,'chip'),(72000,4,'slow')):
            self.assertIn('V-SG3-TABLES',{c for c,_ in self.block('#SG3_TABLE_ALLOC',size,flags,mem).viol})

    def test_scratch_cannot_use_slow(self):
        model=self.block('#SG3_SCRATCH_BYTES',512,2,'chip')
        self.assertFalse(model.viol)
        self.assertEqual(model.blocks[0].kind,'transient')
        self.assertIn('V-CHIP',{c for c,_ in self.block('#SG3_SCRATCH_BYTES',512,4,'slow').viol})


if __name__=='__main__': unittest.main()
