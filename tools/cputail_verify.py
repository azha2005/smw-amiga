#!/usr/bin/env python3
"""Comprueba en 68000 la migración BM1 de tablas CPU, ABI y fallo de arena."""
import argparse
import struct
from pathlib import Path

import machine68k as M
import m68kverify as V


def run(a):
    code, data = Path(a.bin).read_bytes(), Path(a.data).read_bytes()
    s = V.symbols(a.lst)
    base, chip = 0xC00000, 0x1000
    rounded = (len(data) + 511) & ~511
    original = data + bytes(rounded - len(data))
    split = struct.unpack_from('>I', data, s['D_LNS'])[0]
    target = (base + len(code) + 7) & ~7
    for fail in (False, True):
        machine = M.Machine(M.CPUType.M68000, 16384)
        cpu, mem = machine.cpu, machine.mem
        tid = machine.traps.alloc(lambda op, pc: machine.abort_execute())
        mem.w16(V.RET, 0xA000 | tid)
        mem.w_block(base, code)
        mem.w_block(chip, original)
        slow = 0xC7BFF8 if fail else target
        mem.w32(base + s['bm_slowcur'], slow)
        mem.w32(base + s['bm_chipcur'], chip + rounded)
        preserved = {}
        for i, reg in enumerate((M.Register.D2, M.Register.D3, M.Register.D4,
                                 M.Register.D5, M.Register.D6, M.Register.D7,
                                 M.Register.A2, M.Register.A3, M.Register.A4,
                                 M.Register.A5, M.Register.A6)):
            value = rounded if reg == M.Register.D2 else chip if reg == M.Register.A3 else 0x123400 + i
            preserved[reg] = value
            cpu.w_reg(reg, value)
        cpu.w_reg(M.Register.A7, V.STACK - 4)
        mem.w32(V.STACK - 4, V.RET)
        cpu.w_pc(base + s['bm_cpu_tail'])
        cycles = machine.execute(10_000_000).cycles
        assert cpu.r_pc() - 2 == V.RET, 'la rutina no volvió'
        assert cpu.r_reg(M.Register.D0) == (0 if fail else 1)
        assert all(cpu.r_reg(reg) == value for reg, value in preserved.items()), 'ABI'
        if fail:
            assert bytes(mem.r_block(chip, rounded)) == original
            assert mem.r32(base + s['bm_chipcur']) == chip + rounded
            assert mem.r32(base + s['bm_slowcur']) == slow
        else:
            assert bytes(mem.r_block(target, rounded - split)) == original[split:]
            expected = bytearray(original[:split])
            delta = target - chip - split
            for name in ('D_LNS', 'D_COIN', 'D_TCHG'):
                if name in s:
                    off = s[name]
                    value = struct.unpack_from('>I', expected, off)[0]
                    struct.pack_into('>I', expected, off, value + delta)
            assert bytes(mem.r_block(chip, split)) == expected
            assert mem.r32(base + s['bm_chipcur']) == chip + split
            assert mem.r32(base + s['bm_slowcur']) == target + ((rounded - split + 7) & ~7)
            print('CPU tail: %d B recuperados, %d ciclos de carga' % (rounded - split, cycles))
    print('CPUTAIL: OK (copia completa, punteros, chip, ABI y arena agotada)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin', default='work/sw-m/game.bin')
    ap.add_argument('--lst', default='work/sw-m/game.lst')
    ap.add_argument('--data', default='work/yi1_s_g5.dat')
    run(ap.parse_args())
