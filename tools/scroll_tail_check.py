#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX: inspecciona AMBAS listas tras detener la camara; no altera el dibujo.

python tools/scroll_tail_check.py --src work/scroll_sx_before.s
python tools/scroll_tail_check.py --capture-dir work/sx_tail_capture

El segundo comando emite ADFs de diagnostico que publican siempre la lista
A o B; se siguen actualizando ambas normalmente. Solo cambia COP1LC en una
copia temporal del fuente, para fotografiar cada buffer en STOPX sin azar.
"""
import argparse
import hashlib
import json
import struct
import subprocess
from pathlib import Path

import numpy as np

import render_d
import scrollprof as P
import scrollsim as S


def compare(sc, base, s, idx, ideal):
    errors = []
    for line, events in enumerate(S.run_list(sc.mem, base)):
        index = idx[192 + line, s:s + S.W]
        regs = np.zeros((8, S.W), np.int32)
        for x, reg, color in sorted(events, key=lambda e: e[0]):
            regs[reg, max(0, x):] = color
        cols = np.arange(S.W)
        got = regs[index, cols]
        want = ideal[line][index, s + cols]
        for x in np.flatnonzero((index > 0) & (got != want)):
            errors.append(dict(x=int(x), y=line, register=int(index[x]),
                               got=int(got[x]), want=int(want[x])))
    return errors


def capture_build(args, source):
    folder = Path(args.capture_dir)
    folder.mkdir(parents=True, exist_ok=True)
    anchor = 'move.l  V_BACK(a5),COP1LC(a4)'
    if source.count(anchor) != 1:
        raise SystemExit('No se identifica la unica publicacion COP1LC de scroll_frame')
    for name, var in (('a', 'V_COP'), ('b', 'V_COP2')):
        src = folder / ('scroll_tail_%s.s' % name)
        src.write_text(source.replace(anchor, 'move.l  %s(a5),COP1LC(a4)' % var),
                       encoding='latin-1')
        binary = folder / ('scroll_tail_%s.bin' % name)
        listing = folder / ('scroll_tail_%s.lst' % name)
        cmd = [P.vasm(), '-quiet', '-Fbin', '-m68000', '-no-opt', '-I', 'player',
               '-DSTOPX=%d' % args.stop, '-DS0=%d' % args.start,
               '-DSPEED=%d' % args.speed, '-L', str(listing), '-o', str(binary), str(src)]
        subprocess.run(cmd, check=True)
        import sys
        subprocess.run([sys.executable, 'tools/mkadf.py', '--boot', 'work/boot.bin',
                        '--stage2', str(binary), '--data', args.data,
                        '--out', str(binary.with_suffix('.adf'))], check=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--src', default='player/scroll.s')
    ap.add_argument('--data', default='work/yi1_s.dat')
    ap.add_argument('--start', type=int, default=1188)
    ap.add_argument('--stop', type=int, default=1700)
    ap.add_argument('--speed', type=int, default=2)
    ap.add_argument('--idle', type=int, default=8)
    ap.add_argument('--out', default='work/scroll_tail_check.json')
    ap.add_argument('--capture-dir')
    args = ap.parse_args()
    if args.speed <= 0 or args.stop < args.start or args.idle < 2:
        ap.error('Se necesita ida y al menos dos frames despues de STOPX')
    S.W, S.T0 = 256, -120
    code, listing = P.assemble(args.src, ['VIS=256', 'S0=%d' % args.start,
                                        'STOPX=%d' % args.stop, 'SPEED=%d' % args.speed])
    syms, local = P.listing(listing)
    variables = {n: v for n, v in syms.items() if n.startswith('V_')}
    data = Path(args.data).read_bytes()
    sc = P.Scroll(code, syms, local, data, variables)
    sc.s0 = args.start  # El arnes generico inicializa en cero: hacerlo explicito.
    sc.init()
    d = render_d.load('work/yi1_d.dat')
    index = render_d.l1_index(d)
    ideal = [render_d.reg_colors(d['events'][192 + line], d['W']) for line in range(224)]
    frames, idle, reached = [], 0, False
    for frame in range((args.stop - args.start) // args.speed + args.idle + 3):
        s, cycles = sc.frame()
        if s != args.stop:
            continue
        # La primera llegada aun deja la otra lista con la camara anterior.
        if not reached:
            reached = True
            continue
        idle += 1
        lists = {}
        for name, base in (('a', P.COPA), ('b', P.COPB)):
            lists[name] = compare(sc, base, s, index, ideal)
        frames.append(dict(frame=frame, camera=s, cycles=cycles, lists=lists,
                           active='a' if sc.mem.r32(P.FAKE + 0x80) == P.COPA else 'b'))
        print('frame%d s%d active%s: A=%d B=%d' %
              (frame, s, frames[-1]['active'], len(lists['a']), len(lists['b'])))
        if idle >= args.idle:
            break
    result = dict(source=args.src, source_sha256=hashlib.sha256(Path(args.src).read_bytes()).hexdigest(),
                  data_sha256=hashlib.sha256(data).hexdigest(), start=args.start, stop=args.stop,
                  speed=args.speed, frames=frames)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding='utf-8')
    if args.capture_dir:
        capture_build(args, Path(args.src).read_text(encoding='latin-1'))
    if len(frames) != args.idle or any(f['lists'][n] for f in frames for n in ('a', 'b')):
        print('PUERTA SX: FALLA')
        return 1
    print('PUERTA SX: OK (ambas listas, %d frames detenidos)' % len(frames))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
