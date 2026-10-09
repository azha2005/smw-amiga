#!/usr/bin/env python3
"""BM1: leer -DMEMPROBE de WinUAE y cuantificar la chip retenida."""
import argparse
import json
import struct
from pathlib import Path
from winuae_memory import ProcessMemory


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pid', type=int, required=True, help='instancia propia de WinUAE')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    mem = ProcessMemory(a.pid)
    try:
        found = []
        for host, raw in mem.find(b'MEMPROB1', 184):
            self_, stage, length, n, done = struct.unpack_from('>IIIHH', raw, 8)
            if self_ and stage and done == 1 and 0 < n <= 8:
                found.append((host, raw, self_, stage, length, n))
        if not found:
            raise SystemExit('MEMPROBE: sin carga completa')
        host, raw, self_, stage, length, n = found[-1]
        before = struct.unpack_from('>4I', raw, 24)
        after = struct.unpack_from('>4I', raw, 40)
        headers = []
        for i in range(n):
            attr, _, lower, upper, free = struct.unpack_from('>HHIII', raw, 56 + 16 * i)
            headers.append(dict(attr=attr, lower=lower, upper=upper, free=free))
        result = dict(stage_address=stage, stage_bytes=length,
                      before=dict(zip(('chip_free', 'chip_largest', 'fast_free', 'fast_largest'), before)),
                      after=dict(zip(('chip_free', 'chip_largest', 'fast_free', 'fast_largest'), after)),
                      chip_retained=524288 - before[0] - length, headers=headers)
        Path(a.out).write_text(json.dumps(result, indent=2), encoding='utf-8')
        Path(a.out).with_suffix('.bin').write_bytes(raw)
        print(json.dumps(result, indent=2))
        print('MEMPROBE: OK')
    finally:
        mem.close()


if __name__ == '__main__':
    main()
