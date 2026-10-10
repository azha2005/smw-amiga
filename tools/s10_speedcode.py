#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
s10_speedcode.py - G5L-R-S10, paso 1/2: prototipo offline del speedcode de
build_mid/bm_left (instrucciones-g5l-r-s10.md). NO se integra en el juego.

Genera, desde la MLD de yi1_s.dat, un cuerpo 68000 por linea: una carga
por bloque, con las constantes del plan como inmediatos, en el formato que
escribe hoy el bucle .ld/.w/.mv/.k1/.k2 de scroll.s:

  WAIT (clase 0):   move.b  x(a2),d7 / move.w d7,(a3)+ / move.w #$fffe,(a3)+
  rellenos (2, 3):  move.l  #$01fe0000,(a3)+  (1 o 2)
  todas:            move.l  #reg<<16|color,(a3)+
                    cmp.w #a,d3 / bge.s / move.w #a,d3     (vl = max a)
                    cmp.w #b,d4 / ble.s / move.w #b,d4     (vu = min b)

Entrada: quien llama escribe el WAIT de la primera (siempre con WAIT) y
salta al move.l de la carga lo (puntero P_j, +4 B en cada registro de la
MLD); la salida es un RTS parcheado al principio de la carga hi (P_hi menos
el prologo de su clase) y restaurado al volver. Las tardes (clase >= 4) y
el codo de 256 px (P51) siguen por el bucle actual: aca solo se cuentan.

Mide: bytes reales (vasm -Fbin) del codigo generado + tablas, y ciclos del
68000 (tabla de tiempos de Motorola, sin espera de DMA) con los conteos de
clase y de saltos del perfil (--prof, g5l.py --pcprof) del bucle actual.

    python tools/s10_speedcode.py --dat work/yi1_s.dat --out work/s10/sc
    python tools/s10_speedcode.py ... --prof work/s10/control_pc.json \
        --lst work/s10/control_back/game.lst
"""
import argparse
import collections
import json
import os
import re
import struct
import subprocess
import sys

VASM = os.environ.get('VASM', r'C:\Users\JC\vbcc\bin\vasmm68k_mot.exe')
LINES = 224

# bytes y ciclos (68000, sin estados de espera) de cada pieza del cuerpo
WAIT_B, WAIT_C = 4 + 2 + 4, 12 + 8 + 12   # move.b d16(a2) / move.w d7 / #$fffe
FILL_B, FILL_C = 6, 20                    # move.l #$01fe0000,(a3)+
MOVE_B, MOVE_C = 6, 20                    # move.l #imm,(a3)+
AGG_B = 2 * (4 + 2 + 4)                   # cmp.w #,dn / bcc.s / move.w #,dn
# ciclos de un cmp/bcc/move: 8 + (10 tomado | 8 + 8 no tomado)
AGG_TAKEN, AGG_NOT = 8 + 10, 8 + 8 + 8


def read_mld(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'SMWS', 'no es yi1_s.dat'
    mlx_off, mld_off = struct.unpack('>II', d[40:48])
    mlx = struct.unpack('>%dH' % (LINES + 1), d[mlx_off:mlx_off + 2 * (LINES + 1)])
    lines = []
    for L in range(LINES):
        i0, i1 = mlx[L], mlx[L + 1]
        recs = []
        for i in range(i0, i1):
            c, x, reg, col, a, b = struct.unpack('>HHHHhh', d[mld_off + 12 * i:mld_off + 12 * i + 12])
            recs.append((c, x, reg, col, a, b))
        lines.append(recs)
    return lines


def gen(lines, out):
    """asm del cuerpo de cada linea; devuelve (texto, cargas, centinelas)"""
    s = ['; generado por tools/s10_speedcode.py (prototipo S10, derivado: work/)',
         '        section code,code', 'sc_base:']
    n = nsent = 0
    for L, recs in enumerate(lines):
        s.append('sc_l%d:' % L)
        for j, (c, x, reg, col, a, b) in enumerate(recs):
            if x in (0xFFFF, 0x7FFF):            # centinelas: solo un RTS al final
                nsent += 1
                continue
            n += 1
            k = c & 3
            if k == 0:
                s.append('        move.b  %d(a2),d7' % x)
                s.append('        move.w  d7,(a3)+')
                s.append('        move.w  #$fffe,(a3)+')
            for _ in range(max(0, k - 1)):
                s.append('        move.l  #$01fe0000,(a3)+')
            s.append('p_%d_%d:' % (L, j))
            s.append('        move.l  #$%04x%04x,(a3)+' % (reg, col))
            s.append('        cmp.w   #%d,d3' % a)
            s.append('        bge.s   *+6')
            s.append('        move.w  #%d,d3' % a)
            s.append('        cmp.w   #%d,d4' % b)
            s.append('        ble.s   *+6')
            s.append('        move.w  #%d,d4' % b)
        s.append('        rts')
    os.makedirs(out, exist_ok=True)
    src = os.path.join(out, 'sc.s')
    open(src, 'w').write('\n'.join(s) + '\n')
    return src, n, nsent


def assemble(src, out):
    binp = os.path.join(out, 'sc.bin')
    r = subprocess.run([VASM, '-Fbin', '-m68000', '-no-opt', '-quiet', '-o', binp, src],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit('vasm: ' + r.stdout + r.stderr)
    return os.path.getsize(binp)


def prof_counts(prof, lst):
    """conteos del bucle actual de bm_left/build_mid en las fotos del perfil"""
    src = {}
    for l in open(lst, encoding='latin1'):
        m = re.match(r'00:([0-9A-F]{8}) \S*\s+\t\s*(\d+): (.*)', l)
        if m:
            src[int(m.group(1), 16)] = (int(m.group(2)), m.group(3))
    cyc = collections.Counter()
    cnt = collections.Counter()
    for h in json.load(open(prof))['build_mid'].values():
        for pc, (n, c) in h.items():
            ln, t = src.get(int(pc, 16), (0, ''))
            cyc[ln] += c
            cnt[(ln, t.split(';')[0].strip())] += n
    return cyc, cnt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dat', default='work/yi1_s.dat')
    ap.add_argument('--out', default='work/s10/sc')
    ap.add_argument('--prof')
    ap.add_argument('--lst')
    a = ap.parse_args()

    lines = read_mld(a.dat)
    src, n, nsent = gen(lines, a.out)
    code = assemble(src, a.out)
    cls = collections.Counter(r[0] for recs in lines for r in recs if r[1] not in (0xFFFF, 0x7FFF))
    late_lines = sum(1 for recs in lines if any(r[0] >= 4 and r[1] not in (0xFFFF, 0x7FFF) for r in recs))
    ptab = 4 * (n + nsent)                       # P_j, +4 B por registro de MLD
    print('cargas %d, centinelas %d, por clase %s' % (n, nsent, dict(sorted(cls.items()))))
    print('lineas con alguna tarde: %d de %d' % (late_lines, LINES))
    print('codigo generado (vasm): %d B; punteros P_j: %d B; total %d B' % (code, ptab, code + ptab))

    if not a.prof:
        return
    cyc, cnt = prof_counts(a.prof, a.lst)
    loop = sum(v for ln, v in cyc.items() if 1365 <= ln <= 1417)     # bm_left .ch..k2
    loop += sum(v for ln, v in cyc.items() if 1017 <= ln <= 1031)    # build_mid .ld..k2
    loop += sum(v for ln, v in cyc.items() if 1035 <= ln <= 1082)    # build_mid .ch..
    tot = sum(cyc.values())

    def c(ln, pre):
        return sum(v for (l, t), v in cnt.items() if l == ln and t.startswith(pre))
    # bm_left (lineas de scroll.s en el control): ver work/s10/bmleft_prof.txt
    nmv = c(1409, '.mv') + c(1023, '.mv')        # cargas no tarde escritas
    nw = c(1405, '.w') + c(1019, '.w')           # con WAIT (primeras + clase 0)
    nl = c(1432, '.jump') + c(1083, '.jump')     # lineas reescritas (no copiadas)
    nf1 = c(1377, '.f1') + c(1057, '.f1')        # rellenos escritos
    nf2 = c(1376, 'move.l') + c(1056, 'move.l')
    na = c(1412, 'move.w') + c(1026, 'move.w')   # vl actualizada
    nb = c(1415, 'move.w') + c(1029, 'move.w')   # vu actualizada
    first = nl                                    # una primera por linea
    inner_w = max(0, nw - first)
    sc = (first * (12 + 14 + 8 + 12)              # quien llama: x, htab, WAIT, $FFFE
          + inner_w * WAIT_C
          + (nf1 + nf2) * FILL_C
          + nmv * MOVE_C
          + na * AGG_NOT + (nmv - na) * AGG_TAKEN
          + nb * AGG_NOT + (nmv - nb) * AGG_TAKEN)
    # entrada/salida por linea: P_lo (16), P_hi (16), clase de hi y su prologo
    # (8 + 14 + 8), guardar/parchear/restaurar (8 + 12 + 8), jsr/rts (16 + 16),
    # buscar las del codo desde hi (cmp/bcc, 8 + 10 + 4)
    io = nl * (16 + 16 + 8 + 14 + 8 + 8 + 12 + 8 + 16 + 16 + 22)
    print('perfil: build_mid %d ciclos; bucle por carga actual %d (%.1f %%)' % (tot, loop, 100.0 * loop / tot))
    print('  lineas %d, cargas %d (WAIT %d, rellenos %d), vl/vu actualizadas %d/%d' %
          (nl, nmv, nw, nf1 + nf2, na, nb))
    print('speedcode: cuerpo %d + entrada/salida %d = %d ciclos' % (sc, io, sc + io))
    print('ahorro: %d ciclos = %.1f %% de build_mid (cota sin entrada/salida: %.1f %%)' %
          (loop - sc - io, 100.0 * (loop - sc - io) / tot, 100.0 * (loop - sc) / tot))


if __name__ == '__main__':
    main()
