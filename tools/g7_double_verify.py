#!/usr/bin/env python3
"""G7-1: propiedad de PF1 y cursores separados en el 68000 real."""
import argparse

from g5l import GameRun


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin', required=True)
    ap.add_argument('--lst', required=True)
    a = ap.parse_args()
    g = GameRun(a.bin, a.lst, 'work/g3/bank')
    s, mem, cpu, addr = g.s, g.mem, g.cpu, g.addr
    assert 'g7_select' in s
    first, second = mem.r32(addr('g7_original')), mem.r32(addr('g7_pf1'))
    size = s['BUF1']
    assert cpu.read(first, size) == cpu.read(second, size), 'copia inicial'
    # Mientras la foto anterior esta publicada, select no debe escribir
    # PF1 ni cambiar los cursores. Simular luego el ACK del VBL.
    mem.w16(g.dc + s['DC_PEND'], 1)
    before = cpu.read(first, size) + cpu.read(second, size)
    before_vars = cpu.read(g.fr.vars, s['V_SIZE'])
    R = cpu.M.Register
    for reg, value in ((R.A3, g.G.DATA), (R.A4, g.G.FAKE), (R.A5, g.fr.vars), (R.A7, g.V.STACK-4)):
        cpu.cpu.w_reg(reg, value)
    mem.w32(g.V.STACK-4, g.V.RET)
    cpu.cpu.w_pc(addr('g7_select'))
    cpu.m.execute(1000)
    assert cpu.cpu.r_pc() in range(addr('g7_select'), addr('g7_select')+12)
    assert cpu.read(first, size) + cpu.read(second, size) == before
    assert cpu.read(g.fr.vars, s['V_SIZE']) == before_vars
    mem.w16(g.dc + s['DC_PEND'], 0xFFFF)
    cpu.m.execute(10000)
    assert cpu.cpu.r_pc() == g.V.RET+2, 'no salio tras el VBL'
    # Cada anillo tiene una camara, columna parcial y secuencia de mapa propias.
    states = ((4, 23, 7, 13), (9, 28, 11, 17))
    for index, state in enumerate(states):
        for off, value in enumerate(state):
            mem.w16(addr('g7_state') + index*8 + off*2, value)
    for front_index, front_pf, expected in ((0, first, second), (1, second, first), (2, first, second)):
        mem.w16(g.dc + s['DC_PEND'], 0xFFFF)
        mem.w32(g.dc + s['DC_FLIST'], g.cops[front_index])
        mem.w32(addr('g7_lists') + front_index*4, front_pf)
        before = cpu.read(front_pf, size)
        g.fr.call(addr('g7_select'), g.G.FAKE)
        assert mem.r32(g.fr.vars+s['V_BUF1']) == expected
        idx = 0 if expected == first else 1
        actual = tuple(mem.r16(g.fr.vars+s[n]) for n in ('V_P', 'V_CCOL', 'V_CBLK'))
        assert actual == states[idx][:3]
        assert mem.r16(addr('_tile_read')) == states[idx][3]
        assert cpu.read(front_pf, size) == before, 'PF1 visible modificado al seleccionar'
        # Solo el buffer elegido cambia de cursores; el otro conserva su historia.
        original_other = cpu.read(addr('g7_state') + (1-idx)*8, 8)
        mem.w16(g.fr.vars+s['V_P'], 55)
        mem.w16(addr('_tile_read'), 99)
        mem.w32(g.fr.vars+s['V_BACK'], g.cops[(front_index+1) % 3])
        g.fr.call(addr('g7_save'), g.G.FAKE)
        assert mem.r16(addr('g7_state')+idx*8) == 55
        assert mem.r16(addr('g7_state')+idx*8+6) == 99
        assert cpu.read(addr('g7_state')+(1-idx)*8, 8) == original_other
        assert mem.r32(addr('g7_lists')+((front_index+1) % 3)*4) == expected
        # Restaurar las entradas para el siguiente caso independiente.
        for off, value in enumerate(states[idx]):
            mem.w16(addr('g7_state')+idx*8+off*2, value)
    ci = sum(g.fr.call(addr('g7_init'), g.G.FAKE).values())
    cs = sum(g.fr.call(addr('g7_select'), g.G.FAKE).values())
    cw = sum(g.fr.call(addr('g7_save'), g.G.FAKE).values())
    print('G7 ciclos Musashi sin DMA: init %d; select sin espera %d; save %d' % (ci, cs, cw))
    if 'g7_columns' in s and 'gb_rnd_end' not in s:
        for old, target in ((0, 3), (3, 0), (150, 154), (154, 150)):
            scroll = target*16+1
            mem.w16(g.fr.vars+s['V_P'], old)
            mem.w16(g.fr.vars+s['V_S'], scroll)
            mem.w16(g.fr.vars+s['V_CCOL'], 0xFFFF)
            mem.w16(g.fr.vars+s['V_CBLK'], 0)
            cpu.cpu.w_reg(R.D4, 0x12345678)
            cpu.cpu.w_reg(R.D5, 0x87654321)
            stats = g.fr.call(addr('g7_columns'), g.G.FAKE, regions={addr('draw_window'): 'window'})
            assert not stats.get('window', 0), 'redibujo entero en salto corto'
            assert mem.r16(g.fr.vars+s['V_P']) == target
            assert mem.r16(g.fr.vars+s['V_S']) == scroll
            assert cpu.cpu.r_reg(R.D4) == 0x12345678 and cpu.cpu.r_reg(R.D5) == 0x87654321
            print('G7 columnas %d -> %d: %d ciclos, sin draw_window' % (old, target, sum(stats.values())))
    if 'gb_rnd_end' in s:
        # Sellos sinteticos: la espera/columnas diferidas cuentan una vez
        # en columns y en total, y se descuentan de resto. Evita aceptar
        # un BENCH que mide solo la preparacion de fuentes como columns.
        stamps = {6: 10000, 7: 9900, 8: 9800, 9: 9000, 16: 8990,
                  17: 8500, 18: 8490, 19: 8000, 10: 7900, 11: 7800}
        for index, value in stamps.items():
            mem.w16(addr('gb_t') + 2*index, value)
        mem.w16(addr('gb_ovr'), 10)
        mem.w16(addr('gb_tpf'), 14200)
        cpu.write(addr('gb_res'), bytes(6*s['GB_NP']))
        for field, value in [('R_FRAME', 123), ('R_S', 45), ('R_ISR', 500)]:
            mem.w16(addr('dc_rec')+s[field], value)
        mem.w8(addr('dc_rec')+s['R_RS'], 0)
        cpu.cpu.w_reg(R.D7, 0)
        g.fr.call(addr('gb_rnd_end'), g.G.FAKE)
        for part, value in ((3, 570), (4, 790), (5, 700), (6, 2610), (8, 480)):
            assert mem.r16(addr('gb_res')+part*6) == value, ('BENCH parte', part)
        print('G7 BENCH: espera y columnas incluidas, sellos descontados una vez')
    print('G7 DOUBLE: OK (espera/VBL, copia inicial, tres listas, dos PF1 y cursores separados)')


if __name__ == '__main__':
    main()
