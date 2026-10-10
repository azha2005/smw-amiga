#!/usr/bin/env python3
"""SW-B: Map16 -> PF1 exacto, fotos omitidas, wrap y reinicio en Musashi."""
import argparse
import json
import struct
from pathlib import Path
import numpy as np
import scrollsim
import tilechange
import mklvl
import lvdesc
from g5l import GameRun


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', default='work/sw-b')
    ap.add_argument('--bank', default='work/g3/bank')
    ap.add_argument('--replay-frames', help='game_frames.json: todos los cambios reales deben tener entrada')
    a = ap.parse_args()
    gr = GameRun(a.dir + '/game.bin', a.dir + '/game.lst', a.bank)
    cpu, mem, s, fr, addr, G = gr.cpu, gr.mem, gr.s, gr.fr, gr.addr, gr.G
    R = cpu.M.Register
    data = G.DATA
    table = data + mem.r32(data + s['D_TCHG'])
    entries = [struct.unpack('>HHBB', cpu.read(table + 2 + 6 * k, 6))
               for k in range(mem.r16(table))]
    if a.replay_frames:
        valid = {(cell, result) for cell, result, _, _ in entries}
        changes = [(r['k'], cell, result) for r in json.loads(Path(a.replay_frames).read_text())
                   for cell, result in r.get('tile_changes', [])]
        missing = [r for r in changes if r[1:] not in valid]
        assert changes, 'el replay no ejercita cambios del mapa'
        assert not missing, ('reemplazos reales sin representacion', missing)
        print('Diario real del replay: %d cambios, 0 sin representacion' % len(changes))
    mp = data + mem.r32(data + s['D_MAP'])
    blk = data + mem.r32(data + s['D_BLK'])
    write, read, journal = addr('_tile_write'), addr('_tile_read'), addr('_tile_changes')
    costs, pixels = [], 0
    tiles = tilechange.Tiles(mklvl.build(lvdesc.load().obj, desc=lvdesc.load())[0])
    palette_pixels, palette_bad = 0, []
    scrollsim.W, scrollsim.T0 = 256, -120
    scrollsim.CL_LINES, scrollsim.SEG = s['CL_LINES'], s['SEG']

    def blitter(mode, width, address, value):
        if mode != 'W' or address != G.FAKE + s['BLTSIZER']:
            return
        assert width == 1 and mem.r32(G.FAKE + s['BLTCON0R']) == 0x09F00000
        src, dst = mem.r32(G.FAKE + s['BLTAPTR']), mem.r32(G.FAKE + s['BLTDPTR'])
        height, words = value >> 6, value & 63
        smod, dmod = mem.r16(G.FAKE + s['BLTAMODR']), mem.r16(G.FAKE + s['BLTDMODR'])
        for line in range(height):
            cpu.write(dst, cpu.read(src, words * 2))
            src += words * 2 + smod
            dst += words * 2 + dmod

    # Musashi no emula Agnus: implementar A->D por las escrituras reales
    # de BLTSIZE; asi se verifican punteros/modulos/cantidad del binario.
    mem.set_trace_func(blitter)
    mem.set_trace_mode(True)

    def apply(limit):
        cpu.cpu.w_reg(R.D7, limit)
        return sum(fr.call(addr('tile_apply'), G.FAKE).values())

    def check(cell, block):
        nonlocal pixels
        col, row = divmod(cell, 15)
        pf = mem.r32(fr.vars + s['V_BUF1']) + (col % s['SLOTS']) * 2 + row * 16 * s['LINEB1']
        for line in range(48):
            value = mem.r16(blk + block * 96 + line * 2)
            for offset in (0, s['SLOTS'] * 2):
                assert mem.r16(pf + line * s['ROWB1'] + offset) == value, (cell, block, line, offset)
                pixels += 16

    for cell, result, block, old in entries:
        fr.call(addr('tile_reset'), G.FAKE)
        col, _ = divmod(cell, 15)
        mem.w16(fr.vars + s['V_S'], max(1, min(col * 16 - 128, 4864)))
        fr.call(addr('columns'), G.FAKE)
        fr.call(addr('draw_window'), G.FAKE) # reinicio real reconstruye PF1
        cpu.write(journal, struct.pack('>HHHH', cell, result, cell, result))
        mem.w16(write, 2)
        # La logica ya produjo dos cambios, pero la foto limita a uno.
        costs.append(apply(1))
        assert mem.r16(read) == 1 and mem.r16(write) == 2
        assert mem.r8(mp + cell) == block
        check(cell, block)
        apply(2)                         # foto intermedia descartada: termina diario
        assert mem.r16(read) == 2
        assert mem.r32(addr('_mario_unsupported')) == 0
        target = tiles.render(result, col // 16)
        raw = np.frombuffer(cpu.read(blk + block * 96, 96), np.uint8).reshape(16, 3, 2)
        bits = np.unpackbits(raw, axis=2)
        idx = bits[:, 0] | bits[:, 1] << 1 | bits[:, 2] << 2
        # Cada posicion horizontal del bloque a pasos de 4px, incluido
        # el recorte de ambos bordes, contra el copper real del binario.
        for cam in range(max(1, col * 16 - 255), min(4864, col * 16 + 15) + 1, 4):
            mem.w16(fr.vars + s['V_S'], cam)
            for name in ('apply_colors', 'set_pointers', 'build_mid'):
                fr.call(addr(name), G.FAKE)
            events = scrollsim.run_list(mem, mem.r32(fr.vars + s['V_BACK']))
            _, row = divmod(cell, 15)
            for y in range(16):
                regs = [0] * 8
                ev = events[row * 16 + y]
                for x in range(16):
                    screen = col * 16 + x - cam
                    if not 0 <= screen < 256 or target[y, x] < 0:
                        continue
                    for when, reg, color in ev:
                        if when <= screen:
                            regs[reg] = color & 4095
                    palette_pixels += 1
                    if regs[int(idx[y, x])] != int(target[y, x]):
                        palette_bad.append((cell, result, cam, x, y, regs[int(idx[y, x])], int(target[y, x])))

    # Wrap tanto del anillo de 256 como del contador u16.
    cell, result, block, _ = entries[-1]
    for start in (255, 65535):
        mem.w16(read, start)
        mem.w16(write, (start + 2) & 65535)
        for k in (start, start + 1):
            cpu.write(journal + (k & 255) * 4, struct.pack('>HH', cell, result))
        apply((start + 2) & 65535)
        assert mem.r16(read) == (start + 2) & 65535

    reset = sum(fr.call(addr('tile_reset'), G.FAKE).values())
    assert mem.r16(read) == mem.r16(write) == 0
    for cell, _, _, old in entries:
        assert mem.r8(mp + cell) == old, cell
    empty = apply(0)
    print('SW-B Musashi: %d/%d reemplazos, %d pixeles de ambas copias, limite de foto, fotos omitidas, wrap256/u16 y reinicio OK'
          % (len(entries), len(entries), pixels))
    print('Coste CPU sin DMA: vacio %d; cambio min/max %d/%d; reset %d ciclos'
          % (empty, min(costs), max(costs), reset))
    print('Colores del copper real: %d pixeles, %d diferencias' % (palette_pixels, len(palette_bad)))
    assert not palette_bad, palette_bad[:10]


if __name__ == '__main__':
    main()
