#!/usr/bin/env python3
"""P123: ejecutar dc_loop hasta su llamada a g5l_render, con columnas nuevas.

El arnés G5L normalmente llama cada fase por separado y suministra la
foto correcta a g5l_render. Este cruce ejercita la llamada del bucle real:
columns puede destruir a2, y la foto debe seguir siendo DC_REND.
"""
import argparse

from g5l import GameRun


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin', required=True)
    ap.add_argument('--lst', required=True)
    ap.add_argument('--bank', default='work/g3/bank')
    a = ap.parse_args()
    bad = 0
    for slot, sc in ((1, 16), (2, 33), (3, 1)):
        gr = GameRun(a.bin, a.lst, a.bank)
        s, mem, cpu = gr.s, gr.mem, gr.cpu
        R = cpu.M.Register
        rec = gr.addr('dc_rec') + slot * s['DC_REC']
        cpu.write(rec, cpu.read(gr.addr('dc_rec'), s['DC_REC']))
        mem.w16(rec + s['R_S'], sc)
        mem.w16(gr.dc + s['DC_NEW'], slot)
        mem.w16(gr.dc + s['DC_FRONT'], 0)
        mem.w16(gr.dc + s['DC_PEND'], 0xFFFF)
        mem.w16(gr.dc + s['DC_REND'], 0xFFFF)
        # Fuerza una columna nueva en ambas direcciones, sin falsear el ABI.
        mem.w16(gr.fr.vars + s['V_P'], 1 if sc == 1 else 0)
        for reg, value in ((R.A3, gr.G.DATA), (R.A4, gr.G.FAKE),
                           (R.A5, gr.fr.vars), (R.A7, gr.V.STACK - 4)):
            cpu.cpu.w_reg(reg, value)
        cpu.cpu.w_pc(gr.addr('dc_loop'))
        target = gr.addr('g5l_render')
        for _ in range(200000):
            if cpu.cpu.r_pc() == target:
                break
            cpu.m.execute(1)
        else:
            raise RuntimeError('dc_loop no llegó a g5l_render')
        got = cpu.cpu.r_reg(R.A0)
        good = got == rec and mem.r16(gr.dc + s['DC_REND']) == slot
        print('slot %d s %d: foto $%X, esperada $%X %s' % (slot, sc, got, rec, 'OK' if good else 'MAL'))
        bad += not good
    print('DC LOOP: %s' % ('MAL' if bad else 'OK'))
    return int(bool(bad))


if __name__ == '__main__':
    raise SystemExit(main())
