#!/usr/bin/env python3
"""BM1: comprobar direccion fija, supervisor y datos MFM en WinUAE propio."""
import argparse
import json
import struct
from pathlib import Path
from winuae_memory import ProcessMemory
import m68kverify as V


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pid', type=int, required=True)
    ap.add_argument('--lst', required=True)
    ap.add_argument('--data', default='work/yi1_s_g5.dat')
    ap.add_argument('--out', required=True)
    ap.add_argument('--retained', type=int, help='chip retenida medida por MEMPROBE en el control')
    a = ap.parse_args()
    s = V.symbols(a.lst)
    mem = ProcessMemory(a.pid)
    try:
        records = []
        for host, raw in mem.find(b'BMFIXED!', 28):
            self_, data, chip_end, slow_end, sr, _ = struct.unpack_from('>IIIIHH', raw, 8)
            if self_ == 0xC00000 + s['bm_fixedsig'] and data == 0x1000:
                records.append(dict(self=self_, data=data, chip_end=chip_end, slow_end=slow_end, sr=sr))
        if not records:
            raise SystemExit('BM1: sin inicializacion completa')
        result = records[-1]
        assert result['sr'] & 0xF000 == 0x2000, ('SR no supervisor con IRQ habilitada', result)
        assert result['chip_end'] <= 0x80000 and result['slow_end'] <= 0xC7C000, result
        expected = Path(a.data).read_bytes()
        correct = False
        irq = struct.pack('>I', 0xC00000 + s['dc_vbl'])
        for host, raw in mem.find(expected[:64], len(expected)):
            # Identificar RAM chip por su vector real, no una copia del ADF
            # que WinUAE conserva tambien en memoria del proceso.
            if mem.read(host - 0x1000 + 0x6C, 4) == irq:
                assert raw == expected, 'MFM leyo datos distintos del ADF'
                correct = True
                break
        assert correct, 'no se encontro el bloque en la chip real'
        result.update(data_bytes=len(expected), chip_free_arena=0x80000 - result['chip_end'])
        for host, raw in mem.find(b'BMLOAD!!', 20):
            loader, stage_ticks, total_ticks = struct.unpack_from('>III', raw, 8)
            if 0xC7F000 <= loader < 0xC7F400 and 0 < stage_ticks <= total_ticks:
                result.update(load_stage_ticks=stage_ticks, load_total_ticks=total_ticks,
                              load_stage_seconds=stage_ticks / 50,
                              load_total_seconds=total_ticks / 50)
                break
        if a.retained is not None:
            result['chip_reclaimed'] = a.retained - 4096
        Path(a.out).write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))
        print('BM1 WINUAE: OK')
    finally:
        mem.close()


if __name__ == '__main__':
    main()
