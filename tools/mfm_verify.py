#!/usr/bin/env python3
"""BM1: decoder 68000 contra sectores sinteticos, limites y errores."""
import argparse
import random
import struct
from pathlib import Path
import m68kverify as V

MASK = 0x55555555


def pair(value):
    return struct.pack('>II', ((value >> 1) & MASK) | 0xAAAAAAAA,
                       (value & MASK) | 0xAAAAAAAA)


def sector(track, number, data):
    header = pair(0xFF000000 | track << 16 | number << 8 | (11 - number)) + bytes.fromhex('aaaaaaaa') * 8
    words = struct.unpack('>128I', data)
    body = b''.join(struct.pack('>I', (w >> 1 & MASK) | 0xAAAAAAAA) for w in words)
    body += b''.join(struct.pack('>I', (w & MASK) | 0xAAAAAAAA) for w in words)
    def checksum(raw):
        value = 0
        for w in struct.unpack('>%dI' % (len(raw) // 4), raw):
            value ^= w
        return value & MASK
    return bytes.fromhex('44894489') + header + pair(checksum(header)) + pair(checksum(body)) + body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bin', default='work/bm1/boot_bm.bin')
    ap.add_argument('--lst', default='work/bm1/boot_bm.lst')
    a = ap.parse_args()
    code, s = Path(a.bin).read_bytes(), V.symbols(a.lst)
    c = V.MusashiCPU()
    c.m = c.M.Machine(c.M.CPUType.M68000, 16384)
    c.cpu, c.mem = c.m.cpu, c.m.mem
    tid = c.m.traps.alloc(lambda op, pc: c.m.abort_execute())
    c.mem.w16(V.RET, 0xA000 | tid)
    base = 0x10000
    c.write(base, code)
    R = c.M.Register
    rng = random.Random(105)
    worst = 0
    cases = 0
    for track in (0, 1, 42, 79, 80, 158, 159):
        payloads = [rng.randbytes(512) for _ in range(11)]
        order = list(range(11))
        rng.shuffle(order)
        valid = b'\xAA' * 22 + b''.join(sector(track, n, payloads[n]) for n in order)
        assert len(valid) < s['BM_RAWLEN']
        for single_sync in (False, True):
            raw = valid[2:] if single_sync else valid
            # Lectura DMA puede empezar justo despues de un primer sync.
            if single_sync:
                raw = raw[20 + 2:]
            raw += b'\xAA' * (s['BM_RAWLEN'] - len(raw))
            for fault in ('none', 'data', 'header', 'missing', 'track', 'sync'):
                test = bytearray(raw)
                first = test.find(b'\x44\x89')
                header = first + (4 if test[first:first+4] == b'\x44\x89\x44\x89' else 2)
                if fault == 'data':
                    test[header + 56 + 5] ^= 1
                elif fault == 'header':
                    test[header + 20] ^= 1
                elif fault == 'missing':
                    test[first:first + 1084] = b'\xAA' * 1084
                elif fault == 'sync':
                    test[:] = b'\x44\x89' * (s['BM_RAWLEN'] // 2)
                c.write(s['BM_RAW'], test)
                c.write(s['BM_TRACK'], b'\xCC' * 5632)
                c.cpu.w_reg(R.D2, track ^ 1 if fault == 'track' else track)
                cycles = c.call(base + s['bm_decode'], base)
                worst = max(worst, cycles)
                result = c.cpu.r_reg(R.D0)
                assert result == (0 if fault == 'none' else 1), (track, single_sync, fault, result)
                if fault == 'none':
                    assert c.read(s['BM_TRACK'], 5632) == b''.join(payloads), (track, single_sync)
                cases += 1
    print('MFM: %d casos exactos, orden arbitrario, ambos sync y errores detectados; max %d ciclos sin DMA' % (cases, worst))
    print('MFM: OK')


if __name__ == '__main__':
    main()
