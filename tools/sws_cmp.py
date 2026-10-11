#!/usr/bin/env python3
"""SW-S, puerta del paso 2: la RAM de los tres motores de efectos del port,
frame lógico a frame lógico (Musashi, como lder.py), contra el volcado de
snesorc (`tools/sws_ram.py`).

    python tools/sws_cmp.py --bin B/game.bin --lst B/game.lst \
        --ram work/sws/ram_yi1.bin [--engines puntos,humo,menores] [--show 8]

La clave es la de lder.py --key f: la RAM del port después del frame
lógico f contra el volcado de la SNES después del frame f. Los frames del
replay que el port no corre (SKIP) o en que carga un estado (SYNC/RUNSYNC)
no se cuentan: ahí los sprites del port no son los de la SNES.

Paso 4 (con --oam, la OAM grabada <oráculo>_oam.bin): las fichas de los
efectos que el port escribe en ram[$0200-$02FF] (puntos: 2 por ranura en
$B0 + 8x; humo: $20 + 4x y la estrella de $F0-$FF; menores: $50 + 4x),
las visibles de cada grupo seguidas y exactas en la grabación del frame
(x, y, ficha, atributos, tamaño), como G8 con los sprites. Una ficha que
la SNES dibuja y el port no, no se ve aquí: eso lo cubre la RAM.
"""
import argparse
import collections
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sws_ram as S  # noqa: E402

EXTRA = {'puntos': [('ScoreSprIndex', 0x18F7), ('puntaje', 0x0F34), ('puntaje1', 0x0F35),
                    ('puntaje2', 0x0F36)],
         'humo': [('SmokeSprIndex', 0x1863)],
         'menores': []}


def fields_of(engine):
    for e, fields, n in S.ENGINES:
        if e == engine:
            out = [('%s%d.%s' % (e[0], i, k), a + i) for i in range(n) for k, a in fields]
            return out + EXTRA[e]
    raise KeyError(engine)


# grupos de fichas de la OAM (indice de entrada desde $0200): una ranura cada uno
OAM_GROUPS = {'puntos': [(44 + 2 * i, 2) for i in range(6)],
              'humo': [(8 + i, 1) for i in range(4)] + [(60, 4)],
              'menores': [(20 + i, 1) for i in range(12)]}


def oam_read(path):
    """{frame: bytes de las entradas visibles} (oracle2bin.py: <IB + 640)"""
    d = open(path, 'rb').read()
    out = {}
    for o in range(0, len(d) - 644, 645):
        f, n = struct.unpack_from('<IB', d, o)
        out.setdefault(f, d[o + 5:o + 5 + 5 * n])
    return out


def oam_groups(ram, engine):
    """las fichas visibles de cada grupo del port: [bytes de 5 x n]"""
    out = []
    for e0, n in OAM_GROUPS[engine]:
        b = b''.join(bytes(ram[0x200 + 4 * e:0x204 + 4 * e]) + bytes([ram[0x420 + e]])
                     for e in range(e0, e0 + n) if ram[0x201 + 4 * e] != 0xF0)
        if b:
            out.append((e0, b))
    return out


def oam_in(rec, b):
    """b (entradas de 5 bytes) seguidas en rec, alineadas a entrada"""
    for p in range(0, len(rec) - len(b) + 1, 5):
        if rec[p:p + len(b)] == b:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bin', required=True)
    ap.add_argument('--lst', required=True)
    ap.add_argument('--ram', required=True)
    ap.add_argument('--bank', default='work/g3/bank')
    ap.add_argument('--engines', default='puntos,humo,menores')
    ap.add_argument('--show', type=int, default=6)
    ap.add_argument('--key', type=int, default=0, help='desplazamiento de la clave del port (0 = f)')
    ap.add_argument('--oam', help='la OAM grabada (<oraculo>_oam.bin): compara las fichas (paso 4)')
    a = ap.parse_args()
    import g5l as L
    _, frames = S.read(a.ram)
    snes = S.by_label(frames)
    engines = [e for e in a.engines.split(',') if e]
    flds = {e: fields_of(e) for e in engines}
    gr = L.GameRun(a.bin, a.lst, a.bank)
    G, s, mem, fr, addr = gr.G, gr.s, gr.mem, gr.fr, gr.addr
    ram_at = addr('_ram')
    ops_at = addr('replay')
    o_ops = mem.r32(ops_at + 12)
    nops = mem.r16(ops_at + 4)
    ops = [mem.r8(ops_at + o_ops + 6 * i) for i in range(nops)]
    stats = {e: collections.Counter() for e in engines}
    orec = oam_read(a.oam) if a.oam else None
    ostats = {e: collections.Counter() for e in engines}
    oshown = collections.Counter()
    first = {}
    shown = collections.Counter()
    prev = None
    for k in range(gr.n):
        if k:
            fr.call(addr('dc_cop'), G.FAKE)
        nlog = mem.r16(gr.dc + s['DC_NLOG'])
        f = gr.first + nlog
        if f == prev:
            continue
        prev = f
        if nlog >= len(ops) or ops[nlog] != 0:      # solo RUN
            continue
        if nlog + 1 < len(ops) and ops[nlog + 1] == 2:
            # RUN y despues SKIP: el primer frame bloqueado con una animacion
            # no portada (tuberia...). La SNES pone $9D a mitad del frame y
            # el port no (m68kverify --lock run, P130): no es de estos motores
            stats[engines[0]]['excluidos'] += 1
            continue
        sf = snes.get(f + a.key)
        if sf is None:
            continue
        ram = gr.cpu.read(ram_at, 0x2000)
        rec = orec.get(f + a.key) if orec is not None else None
        for e in engines:
            if rec is None:
                continue
            for e0, b in oam_groups(ram, e):
                ostats[e]['fichas'] += 1
                if oam_in(rec, b):
                    continue
                ostats[e]['distintas'] += 1
                if oshown[e] < a.show:
                    oshown[e] += 1
                    print('oam %-8s f %5d: entrada %d port %s | grabada %s' % (
                        e, f, e0, b.hex(' ', 5), rec[:60].hex(' ', 5)))
        for e in engines:
            bad = [(n, sf[adr], ram[adr]) for n, adr in flds[e] if sf[adr] != ram[adr]]
            stats[e]['frames'] += 1
            if bad:
                stats[e]['distintos'] += 1
                first.setdefault(e, f)
                if shown[e] < a.show:
                    shown[e] += 1
                    print('%-8s f %5d: %s' % (e, f, ' '.join('%s=%02X/%02X' % b for b in bad[:10])))
    ok = True
    if stats[engines[0]]['excluidos']:
        print('excluidos %d frames (primer frame bloqueado sin animacion portada)'
              % stats[engines[0]]['excluidos'])
    for e in engines:
        c = stats[e]
        print('%-8s %5d frames, %5d distintos%s' % (e, c['frames'], c['distintos'],
              '' if e not in first else ' (primero f %d)' % first[e]))
        ok &= c['distintos'] == 0
    print('SWS RAM: ' + ('OK' if ok else 'DISTINTA'))
    if orec is None:
        return 0 if ok else 1
    ook = True
    for e in engines:
        c = ostats[e]
        print('oam %-8s %5d grupos de fichas, %5d distintos' % (e, c['fichas'], c['distintas']))
        ook &= c['distintas'] == 0
    print('SWS OAM: ' + ('OK' if ook else 'DISTINTA'))
    return 0 if ok and ook else 1


if __name__ == '__main__':
    sys.exit(main())
