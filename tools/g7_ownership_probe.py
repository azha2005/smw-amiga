#!/usr/bin/env python3
"""G7-1: reproduce tres listas ocupadas en dc_loop con el colchon O5.

No decide el numero de PF1: detecta la condicion que un gestor de dos
buffers debe resolver sin tocar la imagen visible ni la pendiente.
"""
import argparse
import json
from pathlib import Path

from g5l import GameRun


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin', required=True)
    ap.add_argument('--lst', required=True)
    ap.add_argument('--bank', default='work/g3/bank')
    ap.add_argument('--out', default='work/g7-ownership.json')
    a = ap.parse_args()
    g = GameRun(a.bin, a.lst, a.bank)
    s, mem, cpu, R = g.s, g.mem, g.cpu, g.cpu.M.Register
    assert len(g.cops) == 3, 'requiere CUSHION'
    rec = g.addr('dc_rec')
    for slot in (1, 2):
        cpu.write(rec + slot*s['DC_REC'], cpu.read(rec, s['DC_REC']))
    for field, value in [('DC_FRONT', 0), ('DC_PEND', 1), ('DC_NEW', 2), ('DC_REND', 0xFFFF)]:
        mem.w16(g.dc + s[field], value)
    mem.w32(g.dc + s['DC_FLIST'], g.cops[0])
    mem.w32(g.dc + s['DC_PLIST'], g.cops[1])
    mem.w32(g.fr.vars + s['V_BACK'], g.cops[2])
    for reg, value in ((R.A3, g.G.DATA), (R.A4, g.G.FAKE), (R.A5, g.fr.vars), (R.A7, g.V.STACK-4)):
        cpu.cpu.w_reg(reg, value)
    cpu.cpu.w_pc(g.addr('dc_loop'))
    for _ in range(200000):
        if cpu.cpu.r_pc() == g.addr('g5l_render'):
            break
        cpu.m.execute(1)
    else:
        raise AssertionError('dc_loop no llego al dibujo')
    lists = [mem.r32(g.dc + s['DC_FLIST']), mem.r32(g.dc + s['DC_PLIST']),
             mem.r32(g.fr.vars + s['V_BACK'])]
    assert len(set(lists)) == 3
    assert mem.r16(g.dc+s['DC_FRONT']) == 0 and mem.r16(g.dc+s['DC_PEND']) == 1
    assert mem.r16(g.dc+s['DC_REND']) == 2
    result = dict(front=lists[0], pending=lists[1], rendering=lists[2],
                  front_photo=0, pending_photo=1, rendering_photo=2,
                  scope='estado alcanzado por el 68000 real, sin temporizacion DMA')
    Path(a.out).write_text(json.dumps(result, indent=2), encoding='utf8')
    print('G7 OWNERSHIP: tres listas ocupadas, foto pendiente conservada; dos PF1 necesitan arbitraje')


if __name__ == '__main__':
    main()
