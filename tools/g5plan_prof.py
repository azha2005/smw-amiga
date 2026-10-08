#!/usr/bin/env python3
"""G2T-B35: perfil por funcion de g5_plan en Musashi (sin DMA).

Usar el build PROF=1 de logicbench_build.sh: sin inline. Se guardan los
ciclos propios y las llamadas por funcion, y ciclos inclusivos de cada
g5_segment. El coste del build de produccion se mide con g5plan_verify.py.
Los binarios anteriores se pueden perfilar con este mismo arnes.
"""
import argparse
import bisect
import collections
import json
from pathlib import Path
import struct

from g5plan_verify import CL, SEG, M68k, read_cap


def profile(m, args):
    cpu, V = m.cpu, m.V
    M = cpu.M
    funcs = sorted((V.BASE + v, k) for k, v in m.syms.items() if k.startswith('_g5_'))
    starts = [v for v, _ in funcs]
    counts, calls = collections.Counter(), collections.Counter()
    sp = V.STACK - 4 * (len(args) + 1)
    cpu.cpu.w_reg(M.Register.A4, V.BASE)
    cpu.cpu.w_reg(M.Register.A7, sp)
    cpu.write(sp, struct.pack('>%dI' % (len(args) + 1), V.RET, *args))
    cpu.cpu.w_pc(m.sym('_g5_plan'))
    total, segments, pending = 0, [], None
    while cpu.cpu.r_pc() != V.RET:
        pc = cpu.cpu.r_pc()
        if pending and pc == pending[0]:
            segments.append(total - pending[1])
            pending = None
        if pc == m.sym('_g5_segment'):
            pending = (cpu.mem.r32(cpu.cpu.r_reg(M.Register.A7)), total)
        i = bisect.bisect_right(starts, pc) - 1
        if i < 0 or pc < starts[0]:
            raise ValueError('PC fuera del planificador: %06X' % pc)
        name = funcs[i][1]
        if pc == funcs[i][0]:
            calls[name] += 1
        cycles = cpu.m.execute(1).cycles
        counts[name] += cycles
        total += cycles
        if total > 10_000_000:
            raise ValueError('g5_plan no regreso en 10M ciclos')
    return dict(total=total, functions=dict(counts), calls=dict(calls), segment_cycles=segments)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cap', required=True)
    ap.add_argument('--segw', required=True)
    ap.add_argument('--frame', type=int, action='append', required=True)
    ap.add_argument('--bin', default='work/prof/logicbench.bin')
    ap.add_argument('--lst', default='work/prof/logicbench.lst')
    ap.add_argument('--bank', default='work/g3/bank')
    ap.add_argument('--pals', default='work/cc/mario_pal.bin')
    ap.add_argument('--out', required=True, help='JSON en work/')
    a = ap.parse_args()
    from sprgfx_final import derived_path
    derived_path(a.out)
    m = M68k(a.bin, a.lst)
    if '_g5_attempt' not in m.syms or '_g5_shape' not in m.syms:
        raise ValueError('compilar con PROF=1 y CDEFS=-DNOOAM -DSPR_OAM -DSPR_G5')
    TAB, ENV, LIST, WORK, PALS, OUT = 0x60000, 0x74000, 0x96000, 0xA4000, 0xAC000, 0xAD000
    tab, env = Path(a.bank + '.idx').read_bytes(), Path(a.bank + '.g5env').read_bytes()
    if (m.V.BASE + Path(a.bin).stat().st_size > TAB or TAB + len(tab) > ENV
            or ENV + len(env) > LIST):
        raise ValueError('el binario o las tablas pisan el mapa del arnes')
    m.cpu.write(TAB, tab)
    m.cpu.write(ENV, env)
    m.cpu.write(PALS, Path(a.pals).read_bytes())
    segw = Path(a.segw).read_bytes()
    so, result = 0, {}
    for c in read_cap(a.cap):
        frame, = struct.unpack_from('>I', segw, so)
        if frame != c['frame']:
            raise ValueError('segw desalineado en frame %d' % c['frame'])
        so += 4
        lst = bytearray(CL + SEG * 224 + 4)
        for r in range(224):
            k = segw[so]
            lst[CL + SEG * r:CL + SEG * r + 4 * k] = segw[so + 1:so + 1 + 4 * k]
            so += 1 + 4 * k
        if frame not in a.frame:
            continue
        m.cpu.write(LIST, bytes(lst))
        m.cpu.write(m.BLK, c['blk'])
        p = profile(m, (frame, m.BLK, TAB, ENV, PALS, LIST, CL, SEG, WORK, OUT))
        result[frame] = p
        print('perfil g5_plan frame %d: %d ciclos (PROF, sin DMA)' % (frame, p['total']), flush=True)
        for name, cyc in sorted(p['functions'].items(), key=lambda kv: -kv[1]):
            print('  %-20s %8d %5.1f%% llamadas %d' %
                  (name, cyc, 100 * cyc / p['total'], p['calls'][name]))
        sc = p['segment_cycles']
        print('  g5_segment inclusivo: %d llamadas, media %.0f, max %d ciclos' %
              (len(sc), sum(sc) / len(sc) if sc else 0, max(sc, default=0)), flush=True)
    if set(result) != set(a.frame):
        raise ValueError('frames no encontrados: %s' % sorted(set(a.frame) - set(result)))
    Path(a.out).write_text(json.dumps(result, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
