#!/usr/bin/env python3
"""SW-M: fuentes y listas del 68000 contra los ocho pasos de la SNES.

Ejercita tres listas, copias S9, ida/vuelta del replay y fotos omitidas.
La RAM lógica se adelanta deliberadamente después de capturar la foto.
"""
import argparse
import json
import struct
from pathlib import Path

import g5l
import gamecheck as G
from palette import COIN_ANIM, snes_to_amiga12, load_palette_bank, _DEF_SRC


def run(a):
    bank, labels = load_palette_bank(Path(_DEF_SRC) / 'palettes' / 'palettes.a')
    start = labels['PALETTE_Flashing']
    assert COIN_ANIM == bank[start:start + 8], 'los ocho amarillos del fuente'
    results = []
    for stride in (1, 7):
        gr = g5l.GameRun(a.bin, a.lst, a.bank)
        s, mem, cpu, fr = gr.s, gr.mem, gr.cpu, gr.fr
        addr, R = gr.addr, cpu.M.Register
        original = cpu.read(G.DATA, len(Path('work/yi1_s_g5.dat').read_bytes()))
        table = struct.unpack_from('>I', original, 52)[0]
        npatches = struct.unpack_from('>H', original, table + 16)[0]
        offsets = struct.unpack_from('>%dI' % npatches, original, table + 24)
        costs, steps, writes = [], set(), 0
        for k in range(min(a.frames or gr.n, gr.n)):
            if k:
                fr.call(addr('dc_cop'), G.FAKE)
            if k % stride:
                continue
            photo = mem.r16(gr.dc + s['DC_NEW'])
            rec = addr('dc_rec') + photo * s['DC_REC']
            frameb = mem.r8(rec + s['R_COIN'])
            # La fase del render NO se lee de una lógica ya adelantada.
            ram = addr('_ram') + 0x14
            saved = mem.r8(ram)
            mem.w8(ram, frameb ^ 0x1c)
            back = gr.cops[len(costs) % len(gr.cops)]
            mem.w32(fr.vars + s['V_BACK'], back)
            mem.w16(fr.vars + s['V_S'], mem.r16(rec + s['R_S']))
            cpu.cpu.w_reg(R.D0, frameb)
            c = sum(fr.call(addr('coin_prepare'), G.FAKE).values())
            for name in ('columns', 'apply_colors', 'set_pointers', 'build_mid'):
                fr.call(addr(name), G.FAKE)
            c += sum(fr.call(addr('coin_list'), G.FAKE).values())
            mem.w8(ram, saved)
            step = frameb >> 2 & 7
            steps.add(step)
            color = snes_to_amiga12(COIN_ANIM[step]) | 0x8000
            expected = bytearray(original)
            for offset in offsets:
                struct.pack_into('>H', expected, offset, color)
            assert cpu.read(G.DATA, len(original)) == expected, ('fuente', stride, k)
            # Toda palabra animada emitida, incluidos los borrados y las
            # cargas a mitad de línea que S9 copió de otra lista.
            listing = cpu.read(back, s['CL_SIZE'])
            for pos in range(s['CL_LINES'], len(listing) - 3, 4):
                reg, value = struct.unpack_from('>HH', listing, pos)
                if 0x182 <= reg <= 0x18e and value & 0x8000:
                    assert value == color, ('lista', stride, k, pos, hex(value), hex(color))
                    writes += 1
            costs.append(c)
        assert steps == set(range(8)), steps
        results.append(dict(stride=stride, fotos=len(costs), pasos=sorted(steps),
                            palabras_comprobadas=writes,
                            ciclos_media=round(sum(costs) / len(costs), 1), ciclos_max=max(costs)))
    Path(a.out).write_text(json.dumps(results, indent=2))
    print(json.dumps(results))
    print('COINPAL: OK (fuentes completas, 3 listas, RAM adelantada, fotos omitidas)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin', default='work/sw-m/game.bin')
    ap.add_argument('--lst', default='work/sw-m/game.lst')
    ap.add_argument('--bank', default='work/g3/bank')
    ap.add_argument('--frames', type=int, default=0)
    ap.add_argument('--out', default='work/coinpal_verify.json')
    run(ap.parse_args())
