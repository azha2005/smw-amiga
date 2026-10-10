#!/usr/bin/env python3
"""G5L-R-M1: leer el anillo -DM1POS (m1_post en game.s) de un WinUAE propio.

Lanza la medida BENCH de siempre (winuae_lock.ps1 + shot.ps1 -Exact), busca
el winuae64.exe que arranca después (PID nuevo, nunca uno viejo), espera a
que el contador del anillo deje de crecer y vuelca las filas a JSON:
R_FRAME, s, lista (V_BACK baja), ticks de build_mid con la interrupción,
ticks de la interrupción en ese tramo, línea de pantalla al entrar y al
salir, gb_frn. 1 tick del timer A = 1,41 µs ≈ 10 ciclos de 7,09 MHz.

    python tools/m1_read.py --adf work/m1/pos_back/game.adf \
        --shot work/m1/pos_back.png --wait 150 --out work/m1/pos_back.json
"""
import argparse
import json
import struct
import subprocess
import time
from pathlib import Path

from winuae_memory import ProcessMemory

LOCK = r'C:\Users\JC\Downloads\sma\winuae_lock.ps1'
SIG = b'M1POSBUF'


def winuae_pids():
    out = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq winuae64.exe', '/FO', 'CSV', '/NH'],
                         capture_output=True, text=True).stdout
    return {int(l.split('","')[1]) for l in out.splitlines() if l.startswith('"winuae64')}


def read_ring(mem):
    best = None
    for host, raw in mem.find(SIG, 16):
        n, cap = struct.unpack_from('>II', raw, 8)
        if cap == 4400 and n <= cap and (best is None or n > best[1]):
            best = (host, n)
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--adf', required=True)
    ap.add_argument('--shot', required=True)
    ap.add_argument('--wait', type=int, default=150)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    old = winuae_pids()
    ps = subprocess.Popen(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', LOCK,
                           './tools/shot.ps1', '-Exact', '-Adf', a.adf, '-Out', a.shot, '-Wait', str(a.wait)])
    pid = None
    t0 = time.monotonic()
    while pid is None and time.monotonic() - t0 < 120:
        new = winuae_pids() - old
        if new:
            pid = max(new)
        else:
            time.sleep(.5)
    if pid is None:
        ps.wait()
        raise SystemExit('M1: WinUAE no arrancó (¿candado ocupado?)')
    mem = ProcessMemory(pid)
    rows, last, stable = None, -1, 0
    try:
        while time.monotonic() - t0 < a.wait + 60 and ps.poll() is None:
            r = read_ring(mem)
            if r:
                host, n = r
                if n == last and n > 0:
                    stable += 1
                    if stable >= 6:             # 3 s sin filas nuevas: terminó el replay
                        raw = mem.read(host + 16, 16 * n)
                        rows = [struct.unpack_from('>HhHHHHHH', raw, 16 * i) for i in range(n)]
                        break
                else:
                    stable = 0
                last = n
            time.sleep(.5)
    finally:
        mem.close()
    ps.wait()
    if not rows:
        raise SystemExit('M1: anillo no encontrado o sin filas (PID %d)' % pid)
    keys = ('frame', 's', 'back', 'ticks', 'isr', 'v_in', 'v_out', 'frn')
    Path(a.out).write_text(json.dumps({'pid': pid, 'rows': [dict(zip(keys, r)) for r in rows]}), encoding='utf-8')
    print('M1: PID %d, %d filas -> %s; captura %s (exit %s)' % (pid, len(rows), a.out, a.shot, ps.returncode))


if __name__ == '__main__':
    main()
