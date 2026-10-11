#!/usr/bin/env python3
"""G7-3b: el productor 68000 (player/g7fast.s) contra tools/g7_fast.py.

Musashi ejecuta el bucle real de render de cada foto (clean, listas,
restore, columnas, tile_apply, g7b_draw) con el blitter emulado. Para
cada fila con efectos, el segmento del copper tiene que ser palabra a
palabra el de la especificacion y el PF1 tiene que tener sus indices;
el terreno se lee del PF1 materializado (lo que se ve, no el mapa).
Una foto que la especificacion rechaza tiene que rechazarse en la misma
fila. Mide los ciclos del productor (sin DMA).
"""
import argparse
import collections
import json
from pathlib import Path
import struct

import numpy as np
from g5l import GameRun
import g7_color_plan as P
import g7_fast as F
import g2t_ref as T
from g7_bobs_verify import Blitter


def pf1_row(m, pf, cam, row):
    """Indices del PF1 de las 256 columnas de pantalla de una fila."""
    out = np.zeros(256, dtype=np.int8)
    for x in range(256):
        wx = cam + x
        at = pf + row*264 + 2*((wx >> 4) % 22)
        bit = 15 - (wx & 15)
        out[x] = sum(((m.r16(at+88*p) >> bit) & 1) << p for p in range(3))
    return out


def spec_row(m, back, s, row, idx, ov, layers):
    """(palabras, out_idx) o None si la fila queda sin plan."""
    words, _ = T.segment_words(m, back, s['CL_LINES'], s['SEG'], row)
    got = F.fast2_row(words, row, idx, ov)
    if got:
        return words, got[0], got[1]
    new, out, left, claimed = F.fast_row(words, row, idx, ov)
    if not left:
        return words, new, out
    nxt, _ = T.segment_words(m, back, s['CL_LINES'], s['SEG'], (row+1) % 224)
    _, nb = P.prefix_of(nxt, (row+1) % 224)
    if 'window' in layers:
        got = F.window_row(new, row, idx, ov, out.copy(), left, claimed, nb)
        if got:
            return words, got[0], got[1]
    if 'edf' in layers:
        got = F.edf_assign(words, row, idx, ov, out, left, claimed, nb)
        if got:
            return words, got[0], got[1]
    return words, None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin', required=True)
    ap.add_argument('--lst', required=True)
    ap.add_argument('--from-k', type=int, default=0)
    ap.add_argument('--to-k', type=int, default=99999)
    ap.add_argument('--layers', default='fast,window,edf',
                    help='capas que implementa el 68000 (las mismas en la especificacion)')
    ap.add_argument('--out', help='informe JSON')
    ap.add_argument('--local', action='store_true', help='perfil tambien por etiqueta local')
    ap.add_argument('--profile', default='',
                    help='fotos (k,k,...) con perfil por muestreo del PC cada ~200 ciclos; '
                         '"all": perfil acumulado de todas')
    a = ap.parse_args()
    every = a.profile == 'all'
    profile = set(range(100000)) if every else {int(x) for x in a.profile.split(',') if x}
    total = collections.Counter()
    labels = []
    if profile:
        import re
        lab = re.compile(r'^\s+	\s*\d+:\s*([A-Za-z_.]\w*):')
        glob = ''
        adr = re.compile(r'^\d\d:([0-9A-F]{8})\s')
        pending = []
        both = re.compile(r'^\d\d:([0-9A-F]{8})\s+[0-9A-F]*\s*	\s*\d+:\s*([A-Za-z_.]\w*):')
        for line in open(a.lst, encoding='latin-1'):
            mm = both.match(line)
            if mm:
                name = mm.group(2)
                if name.startswith('.'):
                    if not a.local:
                        name = None
                    else:
                        name = glob+name
                else:
                    glob = name
                if name:
                    labels += [(int(mm.group(1), 16), n) for n in pending+[name]]
                    pending = []
                    continue
            mm = lab.match(line)
            if mm:
                name = mm.group(1)
                if name.startswith('.'):
                    if not a.local:
                        continue
                    name = glob+name
                else:
                    glob = name
                pending.append(name)
                continue
            mm = adr.match(line)
            if mm and pending:
                labels += [(int(mm.group(1), 16), n) for n in pending]
                pending = []
        labels.sort()
    layers = set(a.layers.split(','))
    g = GameRun(a.bin, a.lst, 'work/g3/bank')
    s, m, cpu = g.s, g.mem, g.cpu
    R = cpu.M.Register
    blit = Blitter(g)
    blit.hook_wait()
    bank = m.r32(g.addr('g7b_bank'))
    sources = Path('work/g7/sources.bin').read_bytes()
    assert cpu.read(bank, len(sources)) == sources, 'banco G7S1 no exacto'
    # Sembrar el terreno inicial de los dos PF1 (los blits de scroll_init
    # ocurrieron antes de instalar el blitter del arnes).
    mp = g.G.DATA+m.r32(g.G.DATA+s['D_MAP'])
    blocks = g.G.DATA+m.r32(g.G.DATA+s['D_BLK'])
    for state, pf in enumerate((m.r32(g.addr('g7_original')), m.r32(g.addr('g7_pf1')))):
        camera = m.r16(g.addr('g7_state')+8*state)
        if camera >= 32768:
            camera -= 65536
        for col in range(camera-2, camera+20):
            if not 0 <= col < m.r16(g.G.DATA+s['D_COLS']):
                continue
            for brow in range(14):
                block = m.r8(mp+15*col+brow)
                for y in range(16):
                    for p in range(3):
                        v = m.r16(blocks+96*block+6*y+2*p)
                        for copy in (0, 44):
                            m.w16(pf+(brow*16+y)*264+88*p+2*(col % 22)+copy, v)
    # La cola se observa como descriptores y se aplica en el arnes (el
    # consumidor BLIT/IRQ lo cruza g7_bobs_verify --core-only).
    def send(op, pc):
        sp = cpu.cpu.r_reg(R.A7)
        n = m.r32(sp+4)
        assert 0 < n <= s['G7Q_MAX'], n
        pf = m.r32(g.fr.vars+s['V_BUF1'])
        active = m.r16(g.addr('g7_active'))//8
        for j in range(n):
            dest, *words = struct.unpack('>I6H', cpu.read(bank+s['G7Q_OFF']+16*j, 16))
            off = dest-pf
            row, rem = divmod(off, 264)
            assert 0 <= row < 224 and rem < 44 and not rem % 2, (hex(dest), hex(pf))
            at = g.addr('g7b_dirty')+active*44+rem
            m.w16(at, m.r16(at) | (1 << (row//16)))
            for copy in (0, 44):
                for p in range(3):
                    at = dest+copy+88*p
                    mask, v = words[p], words[3+p]
                    m.w16(at, (m.r16(at) & ~mask) | (v & mask))
        cpu.cpu.w_pc(m.r32(sp))
        cpu.cpu.w_reg(R.A7, sp+4)
    tid = cpu.m.traps.alloc(send)
    m.w16(g.addr('_g7b_send'), 0xA000 | tid)
    st = collections.Counter()
    cycles_all = []
    worst = []
    rejects = []
    for k in range(min(g.n, a.to_k+1)):
        if k:
            g.fr.call(g.addr('dc_cop'), g.G.FAKE)
        photo = m.r16(g.dc+s['DC_NEW'])
        rec = g.addr('dc_rec')+photo*s['DC_REC']
        m.w16(g.dc+s['DC_REND'], photo)
        m.w16(g.fr.vars+s['V_S'], m.r16(rec+s['R_S']))
        cpu.cpu.w_reg(R.D0, m.r8(rec+s['R_COIN']))
        g.fr.call(g.addr('g7b_clean'), g.G.FAKE)
        cpu.cpu.w_reg(R.D0, m.r8(rec+s['R_COIN']))
        for name in ('coin_prepare', 'apply_colors', 'set_pointers', 'build_mid', 'coin_list',
                     'g5l_render', 'g7_select', 'g7b_restore', 'g7_columns'):
            if name == 'g5l_render':
                cpu.cpu.w_reg(R.A0, rec)
            g.fr.call(g.addr(name), g.G.FAKE)
        cpu.cpu.w_reg(R.D7, m.r16(rec+s['R_TSEQ']))
        g.fr.call(g.addr('tile_apply'), g.G.FAKE)
        g.fr.call(g.addr('set_pointers'), g.G.FAKE)
        cpu.cpu.w_reg(R.D7, photo)
        g.fr.call(g.addr('dc_hdr'), g.G.FAKE)
        blit.flush()
        back = m.r32(g.fr.vars+s['V_BACK'])
        pf = m.r32(g.fr.vars+s['V_BUF1'])
        cam = m.r16(rec+s['R_S'])
        valid = m.r8(rec+s['R_SWS_VALID'])
        if k < a.from_k or not valid:
            g.fr.call(g.addr('g7_save'), g.G.FAKE)
            P.finish_step(g, rec, back)
            continue
        ov = P.overlays(cpu.read(rec+s['R_OAM'], 320), sources)
        rows = [int(r) for r in np.flatnonzero(np.any(ov >= 0, axis=1))]
        expect = {}
        fail_row = None
        for row in rows:
            idx = pf1_row(m, pf, cam, row)
            words, new, out = spec_row(m, back, s, row, idx, ov[row], layers)
            if new is None:
                fail_row = row
                break
            assert F.check(words, new, row, idx, out, ov[row]), ('especificacion', k, row)
            expect[row] = (words, new, out, idx)
        before = cpu.read(pf, s['BUF1'])
        for reg, value in ((R.A3, g.G.DATA), (R.A4, g.G.FAKE), (R.A5, g.fr.vars), (R.A7, g.V.STACK-4)):
            cpu.cpu.w_reg(reg, value)
        m.w32(g.V.STACK-4, g.V.RET)
        cpu.cpu.w_pc(g.addr('g7b_draw'))
        cycles = 0
        hist = collections.Counter()
        step = 200 if k in profile else 1_000_000
        base = (g.addr('g7f_render')-dict((n, x) for x, n in labels)['g7f_render']) if profile else 0
        while cpu.cpu.r_pc() != g.V.RET+2:
            got = cpu.m.execute(step).cycles
            cycles += got
            if k in profile:
                pc = cpu.cpu.r_pc()-base
                import bisect
                i = bisect.bisect_right([x for x, _ in labels], pc)-1
                hist[labels[i][1] if i >= 0 else '?'] += got
            assert cycles < 200_000_000, ('productor sin fin', k, hex(cpu.cpu.r_pc()))
        total.update(hist)
        if k in profile and not every:
            print('PERFIL k', k, 'ciclos', cycles)
            for name, c in hist.most_common(25):
                print('   %-28s %9d  %5.1f%%' % (name, c, 100*c/cycles))
        error = m.r16(g.addr('g7b_error'))
        want = 0 if fail_row is None else 2 | (fail_row << 8)
        assert error == want, ('rechazo distinto', k, hex(error), hex(want), rows)
        for row, (words, new, out, idx) in expect.items():
            got, tail = T.segment_words(m, back, s['CL_LINES'], s['SEG'], row)
            _, otail = T.segment_words(m, back, s['CL_LINES'], s['SEG'], row) if False else (None, None)
            assert got == new, ('segmento distinto', k, row, cam,
                                ' '.join('%03x:%04x' % w for w in words),
                                ' '.join('%03x:%04x' % w for w in got),
                                ' '.join('%03x:%04x' % w for w in new))
            occ = ov[row] >= 0
            now = pf1_row(m, pf, cam, row)
            bad = np.flatnonzero(np.where(occ, now != out, now != idx))
            assert not bad.size, ('PF1 distinto', k, row, cam, bad[:10].tolist(),
                                  now[bad[:10]].tolist(), out[bad[:10]].tolist(), idx[bad[:10]].tolist())
        if error:
            m.w16(g.addr('g7b_error'), 0)
            rejects.append(dict(k=k, row=fail_row))
            st['photos_rejected'] += 1
        else:
            st['photos'] += 1
            st['rows'] += len(rows)
            st['pixels'] += int(np.count_nonzero(ov >= 0))
        cycles_all.append(cycles)
        worst.append((cycles, k, len(rows)))
        worst = sorted(worst, reverse=True)[:10]
        g.fr.call(g.addr('g7_save'), g.G.FAKE)
        P.finish_step(g, rec, back)
        if k % 250 == 0:
            print(k, dict(st), 'ciclos max', worst[0] if worst else None, flush=True)
    c = np.array(cycles_all) if cycles_all else np.zeros(1)
    res = dict(stats=dict(st), rejects=rejects, layers=sorted(layers),
               cycles=dict(mean=float(c.mean()), median=float(np.median(c)),
                           p99=float(np.percentile(c, 99)), max=int(c.max()),
                           total=int(c.sum())),
               worst=[dict(cycles=w[0], k=w[1], rows=w[2]) for w in worst],
               scope='Musashi sin DMA; cola aplicada por el arnes; consumidor en g7_bobs_verify --core-only')
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(res, indent=1), encoding='utf8')
    if every:
        allc = sum(total.values()) or 1
        print('PERFIL acumulado, ciclos', allc)
        for name, c in total.most_common(40 if a.local else 25):
            print('   %-28s %10d  %5.1f%%' % (name, c, 100*c/allc))
    print('G7F: OK '+json.dumps(dict(stats=res['stats'], cycles=res['cycles'])), flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
