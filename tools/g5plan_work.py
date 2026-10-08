#!/usr/bin/env python3
"""B35-asm: trabajo real del C intacto y microbench de transiciones dispersas.

collect genera una copia instrumental en work/, ejecuta el arnes B4 y
exige los mismos bytes B1. bench compara TODAS las transiciones de cada
intento con el asm, mide ciclos Musashi sin DMA y suma por frame.
Esto no mide g5_plan completo ni permite habilitarlo en el juego.
"""
import argparse
import collections
import csv
import json
from pathlib import Path
import struct
import subprocess
import sys

from sprgfx_final import derived_path


def collect(a):
    derived_path(a.out)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    src = Path('player/g5plan.c').read_text(encoding='utf-8')
    # Anclas unicas: si cambia el control, fallar antes de observar otra cosa.
    patches = [
        ('#include "g5plan.h"', '#include "g5plan.h"\n#include "g5plan_work.h"'),
        ('    for (o = 0; o < seg; o += 4) {',
         '    for (o = 0; o < seg; o += 4) {\n        g5_work_word();'),
        ('    if (row == 255 - G5_V0)', '    g5_work_schedule();\n    if (row == 255 - G5_V0)'),
        ('    for (i = 1; i < 16; i++) {          /* transitions:',
         '    g5_work_uses(w, rows, nr, n);\n    for (i = 1; i < 16; i++) {          /* transitions:'),
        ('                if (nt >= G5_MAXTR)\n                    return 0;',
         '                if (nt >= G5_MAXTR) {\n                    g5_work_trans(w, nt, 1);\n                    return 0;\n                }'),
        ('    *ntr = nt;', '    g5_work_trans(w, nt, 0);\n    *ntr = nt;'),
        ('        for (s = (s16)(t->hasta - 1); s >= lo; s--) {',
         '        for (s = (s16)(t->hasta - 1); s >= lo; s--) {\n            g5_work_probe();'),
        ('    u8 np = pe[0];\n\n    pal = pe + 2;',
         '    u8 np = pe[0];\n\n    g5_work_a3();\n    pal = pe + 2;'),
        ('    for (i = 0; i < 16; i++)\n        w->colors[i]',
         '    g5_work_frame(frame);\n    for (i = 0; i < 16; i++)\n        w->colors[i]'),
    ]
    for old, new in patches:
        if src.count(old) != 1:
            raise ValueError('ancla instrumental ausente o ambigua: ' + old)
        src = src.replace(old, new)
    old = 'return (u16)(o - out);'
    if src.count(old) != 2:
        raise ValueError('retornos de g5_plan distintos')
    src = src.replace(old, 'g5_work_end((u16)(o - out), w);\n        ' + old)
    copy = out / 'g5plan_observed.c'
    copy.write_text(src, encoding='utf-8')
    exe = out / 'g5plan_work.exe'
    subprocess.run(['gcc', '-O2', '-DNOOAM', '-DSPR_OAM', '-DSPR_G5', '-Iplayer', '-Itools',
                    '-o', str(exe), 'tools/g5plan_work.c', str(copy), 'player/g5env.c'], check=True)
    for name in ('yi1', 'normal', 'spin_kill'):
        plan = out / ('plan_' + name + '.bin')
        subprocess.run([str(exe), 'work/g5gate/cap_' + name + '.bin',
                        'work/g2tb35/segw_' + name + '.bin', 'work/g2tb35/segs_' + name + '.bin',
                        a.bank + '.idx', a.bank + '.g5env', a.pals, str(plan),
                        str(out / ('cases_' + name + '.bin')), str(out / ('stats_' + name + '.csv'))], check=True)
        if plan.read_bytes() != Path('work/g2t_ref/plan_' + name + '.bin').read_bytes():
            raise ValueError('el observador altero B1: ' + name)
        print('B4 instrumental %s: B1 identico' % name, flush=True)


def records(path):
    data = Path(path).read_bytes()
    if data[:4] != b'G5WC':
        raise ValueError('magia de casos distinta')
    p = 4
    while p < len(data):
        if p + 10 > len(data):
            raise ValueError('cabecera de caso truncada')
        frame, variant, size, nt = struct.unpack_from('>IHHH', data, p)
        nout = (255 if nt == 65535 else nt) * 10
        p += 10
        if size > 6540 or nt != 65535 and nt > 255 or p + size + nout > len(data):
            raise ValueError('caso invalido o truncado')
        inp, want = data[p:p + size], data[p + size:p + size + nout]
        q = 0
        for _ in range(15):
            count, color = struct.unpack_from('>HH', inp, q)
            if count > 72:
                raise ValueError('mas de 72 filas por indice')
            q += 4
            prev = -1
            for _ in range(count):
                row, val, last = struct.unpack_from('>HHH', inp, q)
                if not prev < row < 224 or last > 255:
                    raise ValueError('usos fuera de orden o pantalla')
                prev = row
                q += 6
        if q != size:
            raise ValueError('bytes sobrantes en usos')
        yield frame, variant, inp, nt, want
        p += size + nout


class Bench:
    def __init__(self, code, offset):
        import m68kverify as V
        self.V, self.cpu, self.offset = V, V.MusashiCPU(), offset
        self.cpu.write(V.BASE, code)
        self.cpu.write(V.BASE + 0x8000, code)
        self.number = 0

    def call(self, inp, nt):
        V, cpu = self.V, self.cpu
        M = cpu.M
        # Dos bases de carga y de argumentos; comprueba independencia de base.
        delta = 0x8000 if self.number & 1 else 0
        self.number += 1
        buf, out = 0x60000 + delta, 0x64000 + delta
        cpu.write(buf - 4, b'HEAD' + inp + b'TAIL')
        cpu.write(out - 4, b'HEAD' + b'\xa5' * 2550 + b'TAIL')
        regs = {getattr(M.Register, r): 0x23456700 + k
                for k, r in enumerate(('D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'A2', 'A3', 'A4', 'A5', 'A6'))}
        for reg, value in regs.items():
            cpu.cpu.w_reg(reg, value)
        sp = V.STACK - 12
        cpu.cpu.w_reg(M.Register.A7, sp)
        cpu.write(sp, struct.pack('>III', V.RET, buf, out))
        cpu.cpu.w_pc(V.BASE + delta + self.offset)
        cycles = cpu.m.execute(1_000_000).cycles - 34
        if cpu.cpu.r_pc() not in (V.RET, V.RET + 2):
            raise ValueError('asm no regreso')
        if any(cpu.cpu.r_reg(r) != v for r, v in regs.items()) or cpu.cpu.r_reg(M.Register.A7) != sp + 4:
            raise ValueError('asm rompio la ABI')
        count = cpu.cpu.r_reg(M.Register.D0) & 65535
        if count != nt:
            raise ValueError('contador de transiciones distinto: %d != %d' % (count, nt))
        size = (255 if count == 65535 else count) * 10
        if (cpu.read(buf - 4, len(inp) + 8) != b'HEAD' + inp + b'TAIL'
                or cpu.read(out - 4, 4) != b'HEAD' or cpu.read(out + 2550, 4) != b'TAIL'
                or cpu.read(out + size, 2550 - size) != b'\xa5' * (2550 - size)):
            raise ValueError('asm escribio fuera de su salida o cambio entrada')
        return cycles, cpu.read(out, size)


def synthetic(b):
    # Incluye usos sin cambio, actualizacion del ultimo uso, alternancia y
    # desbordamiento. Esperados calculados independientemente del C del port.
    patterns = [{}, {1: [(0, 2, 9), (1, 2, 20), (2, 3, 25), (3, 0, 30)],
                     15: [(223, 65535, 255)]},
                {i: [(r, 1 + (r & 1), r) for r in range(72 if i < 4 else 39)]
                 for i in range(1, 5)},
                {i: [(r, 1 + (r & 1), r) for r in range(72)] for i in range(1, 16)}]
    for groups in patterns:
        inp, want, overflow = bytearray(), bytearray(), False
        for i in range(1, 16):
            rows = groups.get(i, [])
            inp += struct.pack('>HH', len(rows), 0)
            val, prev, last = 0, -1, 32767
            for row, color, x in rows:
                inp += struct.pack('>HHH', row, color, x)
                if color != val and not overflow:
                    if len(want) == 2550:
                        overflow = True
                    else:
                        want += struct.pack('>BBHhhh', i, 0, color, prev, last, row)
                val, prev, last = color, row, x
        nt = 65535 if overflow else len(want) // 10
        _, got = b.call(bytes(inp), nt)
        if got != want:
            raise ValueError('transiciones sinteticas distintas')
    # Negativo: el mismo registro con otro color debe cambiar la salida.
    groups = struct.pack('>HHHHH', 1, 0, 10, 2, 15) + struct.pack('>HH', 0, 0) * 14
    _, before = b.call(groups, 1)
    changed = bytearray(groups)
    changed[7] = 3
    _, after = b.call(bytes(changed), 1)
    if before == after:
        raise ValueError('el negativo de color no fue detectado')
    print('asm: sinteticos, desborde, negativo, ABI y dos bases OK', flush=True)


def summarize(values):
    vals = sorted(values)
    return dict(mean=sum(vals) / len(vals), max=vals[-1], p99=vals[99 * len(vals) // 100])


def bench(a):
    derived_path(a.out)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.vbcc:
        vbcc = Path(a.vbcc)
        assembler = vbcc / 'bin/vasmm68k_mot.exe'
        if not assembler.exists():
            assembler = vbcc / 'bin/vasmm68k_mot'
    else:
        from regress import vasm
        assembler = vasm()
        if not assembler:
            raise ValueError('no encuentro vasm: VBCC=... o --vbcc <directorio>')
    binpath, lst = out / 'trans.bin', out / 'trans.lst'
    subprocess.run([str(assembler), '-quiet', '-Fbin', '-m68000', '-no-opt',
                    '-DSPR_G5', '-DG5_TRANS_BENCH', '-L', str(lst), '-o', str(binpath),
                    'player/g5trans68k.s'], check=True)
    subprocess.run([sys.executable, 'tools/piccheck.py', '--lst', str(lst)], check=True)
    from m68kverify import symbols
    b = Bench(binpath.read_bytes(), symbols(lst)['_g5_trans_sparse'])
    synthetic(b)
    if a.synthetic_only:
        return
    result = {}
    for name in ('yi1', 'normal', 'spin_kill'):
        totals, worst_case, n = collections.Counter(), (0, 0, 0), 0
        for frame, variant, inp, nt, want in records(Path(a.cases) / ('cases_' + name + '.bin')):
            cycles, got = b.call(inp, nt)
            if got != want:
                raise ValueError('asm distinto: %s frame %d variante %d' % (name, frame, variant))
            totals[frame] += cycles
            worst_case = max(worst_case, (cycles, frame, variant))
            n += 1
        rows = list(csv.DictReader((Path(a.cases) / ('stats_' + name + '.csv')).open()))
        frame_ids = {int(r['frame']) for r in rows}
        if not rows or set(totals) - frame_ids or n != sum(int(r['attempts']) for r in rows):
            raise ValueError('casos y estadisticas desalineados')
        metrics = {k: summarize([int(r[k]) for r in rows]) for k in rows[0] if k != 'frame'}
        all_cycles = [(totals[f], f) for f in frame_ids]
        metrics['asm_transitions'] = dict(summarize([c for c, _ in all_cycles]),
                                         worst_frame=max(all_cycles)[1], worst_attempt=worst_case,
                                         over_8000=sum(c > 8000 for c, _ in all_cycles))
        metrics['frames'], metrics['attempts_checked'] = len(rows), n
        result[name] = metrics
        print('%s: %d frames, %d intentos; transiciones asm distintas 0, ABI 0; '
              'solo transiciones media %.0f max %d ciclos/frame (frame %d); >8000: %d' %
              (name, len(rows), n, metrics['asm_transitions']['mean'],
               metrics['asm_transitions']['max'], metrics['asm_transitions']['worst_frame'],
               metrics['asm_transitions']['over_8000']), flush=True)
    (out / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    c = sub.add_parser('collect')
    c.add_argument('--out', default='work/b35asm/work')
    c.add_argument('--bank', default='work/g3/bank')
    c.add_argument('--pals', default='work/cc/mario_pal.bin')
    b = sub.add_parser('bench')
    b.add_argument('--cases', default='work/b35asm/work')
    b.add_argument('--out', default='work/b35asm/bench')
    b.add_argument('--vbcc', help='directorio de vbcc; por defecto el mismo descubrimiento que regress')
    b.add_argument('--synthetic-only', action='store_true')
    a = ap.parse_args()
    collect(a) if a.command == 'collect' else bench(a)


if __name__ == '__main__':
    main()
