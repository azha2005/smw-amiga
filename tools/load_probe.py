#!/usr/bin/env python3
"""BM1 paso 4: tiempo de carga del boot trackdisk (-DLOADTIME) en WinUAE.

Lee el registro TDLOAD!! de game.s (TOD de CIA-A al entrar al bootblock,
stage2 leido y datos leidos con el motor apagado: los mismos extremos que
BMLOAD!! de boot_bm.s). El TOD cuenta VBL PAL (50 Hz) y se lee sin
reiniciarlo: las diferencias van modulo 2^24.

    python tools/load_probe.py --pid <PID> --out work/bm1/td/load.json
"""
import argparse
import json
import struct
from pathlib import Path
from winuae_memory import ProcessMemory


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pid', type=int, required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    mem = ProcessMemory(a.pid)
    try:
        best = None
        for host, raw in mem.find(b'TDLOAD!!', 20):
            start, stage, end = struct.unpack_from('>III', raw, 8)
            if not end or max(start, stage, end) >= 1 << 24:
                continue                    # copia vieja (chip liberada) o del ADF
            st = (stage - start) & 0xFFFFFF
            tot = (end - start) & 0xFFFFFF
            if 0 < st <= tot and (best is None or tot > best['load_total_ticks']):
                best = dict(tod_start=start, load_stage_ticks=st, load_total_ticks=tot,
                            load_stage_seconds=st / 50, load_total_seconds=tot / 50)
        if best is None:
            raise SystemExit('LOADTIME: sin registro completo (todavia cargando?)')
        Path(a.out).write_text(json.dumps(best, indent=2), encoding='utf-8')
        print(json.dumps(best, indent=2))
        print('LOADTIME WINUAE: OK')
    finally:
        mem.close()


if __name__ == '__main__':
    main()
