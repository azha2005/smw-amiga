#!/usr/bin/env python3
"""Z1: muerte real, carga y fotos O5 en el binario 68000 (Musashi)."""
import struct
import argparse
import m68kverify as V
import gamecheck as G


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--node', action='store_true', help='verificar también build -DNODECOUPLE')
    args = ap.parse_args()
    path = 'work/z1-old' if args.node else 'work/live'
    code = open(path + '/game.bin', 'rb').read()
    s = V.symbols(path + '/game.lst')
    c = V.MusashiCPU()
    # read_input usa también CIA-A: memoria completa para sus direcciones.
    c.m = c.M.Machine(c.M.CPUType.M68000, 16384)
    c.cpu, c.mem = c.m.cpu, c.m.mem
    tid = c.m.traps.alloc(lambda op, pc: c.m.abort_execute())
    c.mem.w16(V.RET, 0xA000 | tid)
    c.mem.w8(0xBFE001, 0xFF)
    c.mem.w16(0xDFF016, 0xFFFF)
    B = V.BASE
    c.write(B, code)
    R = c.M.Register

    def addr(n):
        return B + s[n]

    def w32(n, v):
        c.mem.w32(addr(n), v)

    def call(n, hardware=False):
        c.cpu.w_sr(0)                      # bucle principal en user mode, como KS 1.2
        c.cpu.w_reg(R.D0, 0)
        c.cpu.w_reg(R.D1, 0)
        c.cpu.w_reg(R.A3, G.DATA)
        c.cpu.w_reg(R.A5, addr('vars'))
        cycles = c.call(addr(n), G.FAKE if hardware else B)
        assert c.cpu.r_pc() == V.RET + 2, ('no volvió al arnés', n, hex(c.cpu.r_pc()))
        assert c.cpu.r_sr() & 0xF000 == 0, ('salió del modo usuario', n)
        return cycles

    w32('_map16_lo', addr('map16'))
    w32('_map16_hi', addr('map16') + s['MAPHALF'])
    w32('_spr_level', addr('spr_lv'))
    w32('_gfx32', addr('gfx32'))
    c.write(addr('_level_sprites'), bytes([1]))
    call('live_defaults')
    # live_init toma esta copia antes de live_start y después de los punteros.
    save = 0xD0000
    initial = c.read(addr('cdata0'), s['cdata1'] - s['cdata0'])
    map0 = c.read(addr('map16'), 2 * s['MAPHALF'])
    c.write(save, initial + map0)
    w32('g_save', save)
    call('replay_init')
    call('live_start')
    ram = addr('_ram')
    start = c.read(ram, 0x2000)
    death = None
    for f in range(1, 600):
        call('live_logic')
        assert c.cpu.r_reg(R.D0) == 0, ('diagnóstico inesperado', f, c.cpu.r_reg(R.D0),
                                      c.mem.r8(ram + 0xDBE), c.mem.r8(ram + 0x100),
                                      c.read(ram + 0xF31, 3).hex())
        if c.mem.r8(ram + 0x71) == 9 and death is None:
            death = f
        if c.mem.r16(addr('g_restart')):
            finish = f
            break
    else:
        raise AssertionError('la muerte no pidió cargar el nivel')
    assert death == 219, death
    assert c.mem.r8(ram + 0x100) == 0x0B
    lives = c.mem.r8(ram + 0xDBE)
    assert lives == (start[0xDBE] - 1) & 255
    # Contadores no triviales y un bloque modificado: sobrevivir/resetear.
    persist = {0xDBE: bytes([lives]), 0xDBF: bytes([57]),
               0xDC1: bytes([0]), 0xDC2: bytes([2]), 0xF34: bytes([3, 2, 1, 6, 5, 4]),
               0xF48: bytes([35, 42])}
    for off in [0x1F2F, 0x1F3C, 0x1FEE]:
        persist[off] = bytes(range(1, 13))
    for off, data in persist.items():
        c.write(ram + off, data)
    c.mem.w8(ram + 0xDC0, 8)
    c.write(addr('map16') + 100, bytes([0, 0]))
    # Las dos listas/fotos contienen datos viejos antes de la transacción.
    fr = G.Frames(c, B, s, open('work/yi1_s.dat', 'rb').read())
    for n, val in [('V_BUF1', G.BUF1), ('V_COP', G.COPA), ('V_COP2', G.COPB)]:
        c.mem.w32(addr('vars') + s[n], val)
    c.mem.w16(G.FAKE + s['INTENAR'], 0x4030)
    if args.node:
        w32('g_spra', G.SPRS)
        w32('g_sprb', G.SPRS + s['SPRBUF'])
        w32('g_null', G.SPRS + 2 * s['SPRBUF'])
        call('cam_to_s', True)
        call('scroll_init', True)
        oldframe = c.mem.r32(addr('g_frame'))
        cycles = call('live_restart_hw', True)
        for off, data in persist.items():
            assert c.read(ram + off, len(data)) == data, hex(off)
        assert c.read(addr('map16'), len(map0)) == map0
        assert c.mem.r16(addr('g_restart')) == 0
        assert c.mem.r32(addr('g_frame')) == oldframe
        assert c.mem.r16(G.FAKE + s['INTENA']) == 0xC030
        call('live_logic')
        assert c.mem.r32(addr('g_frame')) == oldframe + 1
        assert c.cpu.r_reg(R.D0) == 0
        print('Z1 NODECOUPLE Musashi/user: muerte219, fin410, RAM/mapa/carga OK; %d ciclos sin DMA' % cycles)
        return
    for i in range(3):
        c.mem.w32(addr('g_sbuf') + 4 * i, G.SPRS + i * s['SPRBUF'])
    w32('g_null', G.SPRS + 3 * s['SPRBUF'])
    w32('g_data', G.DATA)
    call('cam_to_s', True)
    call('scroll_init', True)
    call('dc_init', True)
    oldframe = c.mem.r32(addr('g_frame'))
    oldnlog = c.mem.r16(addr('dc_st') + s['DC_NLOG'])
    call('dc_cop', True)
    assert c.mem.r32(addr('g_frame')) == oldframe, 'COPER durante carga hizo un tick'
    cycles = call('dc_restart', True)
    assert c.mem.r16(G.FAKE + s['INTENA']) == 0xC030
    for off, data in persist.items():
        assert c.read(ram + off, len(data)) == data, hex(off)
    assert c.mem.r8(ram + 0xDC0) == 30
    assert c.read(addr('map16'), len(map0)) == map0
    for off, n in [(0x94, 4), (0x1A, 4), (0x71, 1), (0x1496, 1)]:
        assert c.read(ram + off, n) == start[off:off + n], hex(off)
    assert c.mem.r8(ram + 0x19) == 0
    assert c.mem.r16(addr('g_restart')) == 0
    assert c.mem.r32(addr('g_frame')) == oldframe
    assert c.mem.r16(addr('dc_st') + s['DC_NLOG']) == oldnlog
    assert c.mem.r16(addr('dc_st') + s['DC_NEW']) == c.mem.r16(addr('dc_st') + s['DC_FRONT'])
    for n in ['DC_PEND', 'DC_REND']:
        assert c.mem.r16(addr('dc_st') + s[n]) == 0xFFFF
    front = c.mem.r16(addr('dc_st') + s['DC_FRONT'])
    buffer = c.mem.r32(addr('g_sbuf') + front * 4)
    assert any(c.read(buffer + 4, s['SPRBUF'] - 4)), 'Mario reaparece sin gráfico'
    for cop in [G.COPA, G.COPB]:
        spr0 = cop + s['CL_SPR']
        pointer = c.mem.r16(spr0 + 2) << 16 | c.mem.r16(spr0 + 6)
        assert pointer == buffer, 'lista apunta a foto vieja'
    # Próxima COPER: exactamente un tick, no un tick pendiente de antes.
    call('dc_cop', True)
    assert c.mem.r32(addr('g_frame')) == oldframe + 1
    assert c.mem.r16(addr('dc_st') + s['DC_NLOG']) == oldnlog + 1
    # Cuatro muertes normales y la quinta termina en game over; sin doble descuento.
    call('live_death_restart')
    c.mem.w8(ram + 0xDBE, 4)
    for remaining in [3, 2, 1, 0, 255]:
        c.mem.w8(ram + 0x71, 9)
        c.mem.w8(ram + 0x1496, 2)
        c.mem.w8(ram + 0x13, 3)
        call('live_logic')
        assert c.mem.r8(ram + 0xDBE) == remaining
        assert c.cpu.r_reg(R.D0) == (s['MOT_MUERTE'] if remaining == 255 else 0)
        if remaining != 255:
            call('dc_restart', True)
            assert c.mem.r8(ram + 0xDBE) == remaining
    # Entrada sostenida: restaurar no borra la copia propia de ControllerUpdate.
    c.write(addr('g_pada'), bytes([0x81, 0x80]))
    call('live_death_restart')
    assert c.read(addr('g_pada'), 2) == bytes([0x81, 0x80])
    c.cpu.w_reg(R.D0, 0x81)
    c.cpu.w_reg(R.D1, 0x80)
    c.call(addr('pad_convert'), B)
    assert c.mem.r8(ram + 0x16) == c.mem.r8(ram + 0x18) == 0
    # Game over y punto medio siguen como diagnóstico explícito.
    for mode, mid in [(0x15, 0), (0x0B, 1)]:
        call('live_death_restart')
        c.mem.w8(ram + 0x71, 9)
        c.mem.w8(ram + 0x1496, 2)  # temporizador general y luego anim_death
        c.mem.w8(ram + 0x13, 3)  # callframe incrementa a 4 y vence timer
        c.mem.w8(ram + 0x13CE, mid)
        c.mem.w8(ram + 0xDBE, 0 if mode == 0x15 else 3)
        call('live_logic')
        assert c.cpu.r_reg(R.D0) == s['MOT_MUERTE'], (mode, mid, c.cpu.r_reg(R.D0), c.mem.r8(ram + 0x13), c.mem.r8(ram + 0x1496))
        assert c.mem.r16(addr('g_restart')) == 0
    print('Z1 Musashi: muerte %d, fin %d; vidas %d; RAM/mapa/fotos/O5 OK' % (death, finish, lives))
    print('Carga completa: %d ciclos sin DMA (%.2f frames PAL); carga no ejecuta lógica' %
          (cycles, cycles / V.PAL_FRAME))
    # Los verificadores full saltan $71 != 0: comprobar explícitamente muerte.
    for name in ['enemigo', 'caida']:
        blob = open('work/oracle_pw_morir_%s.bin' % name, 'rb').read()
        pairs = 0
        for i in range(len(blob) // V.REC - 1):
            p, q = blob[i * V.REC:(i + 1) * V.REC], blob[(i + 1) * V.REC:(i + 2) * V.REC]
            if p[8 + 0x71] != 9 or q[8 + 0x71] != 9 or p[4] != 0x29 or q[4] != 0x29:
                continue
            if struct.unpack_from('<I', q)[0] != struct.unpack_from('<I', p)[0] + 1:
                continue
            c.write(ram, p[8:264])
            c.write(ram + 0x13C0, p[264:])
            c.mem.w8(ram + 0x100, 0x14)
            c.mem.w8(ram + 0xDBE, 4)
            c.mem.w8(ram + 0xF31, 3)
            c.write(ram + 0x15, q[8 + 0x15:8 + 0x19])
            call('_level_frame')
            for field, off, n in V.FIELDS + [('anim', 0x71, 1), ('power', 0x19, 1)]:
                want = q[8 + off:8 + off + n] if off < 0x100 else q[264 + off - 0x13C0:264 + off - 0x13C0 + n]
                assert c.read(ram + off, n) == want, (name, struct.unpack_from('<I', q)[0], field, c.read(ram + off, n).hex(), want.hex())
            pairs += 1
        assert pairs > 100
        print('Oráculo muerte %s: %d/%d pares exactos (campos Mario + $71/$19)' % (name, pairs, pairs))


if __name__ == '__main__':
    main()
