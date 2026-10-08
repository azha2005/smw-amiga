#!/usr/bin/env python3
"""Cpre: planes B1 sobre listas O5 reales; derivados exclusivamente en work/."""
import argparse
import collections
import json
from pathlib import Path
import struct

import gamecheck as G
import m68kverify as V
import g2t_ref as T
import g5ref as R
from sprgfx_final import derived_path


def photo_pixels(spr):
    """Pixels de los cuatro flujos DMA de Mario, sin RAM ni OAM viva."""
    result = {}
    for col in range(2):
        off = 336*col
        pos, ctl = struct.unpack_from('>HH', spr, off)
        if not (pos or ctl):
            continue
        start = (pos>>8) | ((ctl&4)<<6)
        stop = (ctl>>8) | ((ctl&2)<<7)
        x0 = ((pos&255)*2 | (ctl&1))-160
        for j in range(stop-start):
            words = struct.unpack_from('>HH', spr, off+4+4*j)
            words += struct.unpack_from('>HH', spr, off+172+4*j)
            row = start-44+j
            for u in range(16):
                idx = sum(((w>>(15-u))&1)<<p for p,w in enumerate(words))
                if idx and 0 <= x0+u < 256 and 0 <= row < 224:
                    result.setdefault((x0+u, row), idx)
    return result


def table_bytes(entries):
    """G5PR v1: indice frame de foto/offset, B1 y firmas de sus segmentos."""
    out = bytearray(struct.pack('>4sHH', b'G5PR', 1, len(entries)))
    out += bytes(8 * len(entries))
    for i, (stamp, plan, signatures) in enumerate(entries):
        struct.pack_into('>II', out, 8+8*i, stamp, len(out))
        out += T.dump_plans([plan])
        for row in sorted(plan.get('sufijos', {}), key=int):
            out += struct.pack('>BH', int(row), signatures[int(row)])
        if len(out) & 1:
            out.append(0)
    data = bytes(out)
    table_index(data)
    return data


def table_index(data):
    """Valida G5PR/B1 antes de incluirlo o inyectarlo; no necesita ROM.

    Las firmas u16 y los MOVE de B1 pueden estar en direccion impar.
    Los registros completos, en cambio, empiezan alineados a dos bytes.
    """
    def require(ok, message):
        if not ok:
            raise ValueError('G5PR: '+message)

    require(len(data) >= 8 and data[:6] == b'G5PR\0\1', 'cabecera invalida')
    n = struct.unpack_from('>H', data, 6)[0]
    start = 8+8*n
    require(start <= len(data), 'indice truncado')
    entries = [struct.unpack_from('>II', data, 8+8*i) for i in range(n)]
    require(all(entries[i][0] < entries[i+1][0] for i in range(n-1)), 'frames sin orden estricto')
    require(not n or entries[0][1] == start, 'hueco antes del primer B1')
    require(n or len(data) == 8, 'bytes tras tabla vacia')
    for i, (_, off) in enumerate(entries):
        end = entries[i+1][1] if i+1 < n else len(data)
        require(off % 2 == 0 and start <= off < end <= len(data), 'offset invalido')
        def have(p, size):
            require(p+size <= end, 'B1 o firmas truncados')
        have(off, 48)
        for ch in range(4):
            act, pad = data[off+6+10*ch:off+8+10*ch]
            require(act in (0, 1) and pad == 0, 'canal B1 invalido')
        p = off+46
        nvbl = data[p]
        require(nvbl <= 15, 'demasiados MOVE VBL')
        p += 1
        have(p, 3*nvbl+1)
        require(all(1 <= data[p+3*j] <= 15 for j in range(nvbl)), 'indice VBL invalido')
        p += 3*nvbl
        nseg = data[p]
        p += 1
        rows = []
        for _ in range(nseg):
            have(p, 5)
            row, tipo, _, nop, k = data[p:p+5]
            require(row < 224 and row != 211 and (not rows or row > rows[-1]), 'fila invalida')
            require(tipo in (1, 2) and 1 <= k <= 7 and nop+k+(tipo == 1) <= 9,
                    'sufijo fuera de contrato')
            rows.append(row)
            have(p+5, 3*k)
            require(all(1 <= data[p+5+3*j] <= 15 for j in range(k)), 'indice COLOR invalido')
            p += 5+3*k
        have(p, 3*nseg)
        require([data[p+3*j] for j in range(nseg)] == rows, 'filas de firma distintas')
        p += 3*nseg
        require(end == p+(p & 1), 'longitud B1/firmas invalida')
        require(not (p & 1) or data[p] == 0, 'relleno no nulo')
    return dict(entries)


def include(a):
    derived_path(a.table)
    p = Path(a.table)
    data = p.read_bytes()
    table_index(data)
    if len(data) > 16384:
        raise ValueError('tabla C4 mayor de 16 KB')
    name = p.resolve().as_posix()
    if any(c in name for c in ('"', '\n', '\r')):
        raise ValueError('ruta no representable en incbin')
    Path('work/g5_pre.i').write_text('g5_pre_table:\n        incbin "'+name+'"\n', encoding='utf-8')


class Replay:
    """Una sola Machine; las fotos, las listas y el orden de O5 del juego."""
    def __init__(self, binary, listing, cpu_type=V.MusashiCPU):
        code = Path(binary).read_bytes()
        self.s = V.symbols(listing)
        self.B = G.code_base(len(code))
        self.cpu = cpu_type()
        self.mem = self.cpu.mem
        self.cpu.write(self.B, code)
        s, mem, addr = self.s, self.mem, self.addr
        for n, p in (('_map16_lo', addr('map16')), ('_map16_hi', addr('map16')+s['MAPHALF']),
                     ('_spr_level', addr('spr_lv')), ('_gfx32', addr('gfx32'))):
            mem.w32(addr(n), p)
        self.cpu.write(addr('_level_sprites'), b'\1')
        self.cpu.call(addr('replay_init'), self.B)
        self.fr = G.Frames(self.cpu, self.B, s, Path('work/yi1_s_g5.dat').read_bytes())
        self.first, self.n = mem.r16(addr('replay')+6), mem.r16(addr('replay')+4)
        self.cpu.call(addr('game_step'), self.B)
        self.fr.init_scroll()
        _, _, sprs = G.layout(s)
        for i in range(3):
            mem.w32(addr('g_sbuf')+4*i, sprs+i*s['SPRBUF'])
        mem.w32(addr('g_null'), sprs+3*s['SPRBUF'])
        self.cpu.write(sprs+3*s['SPRBUF'], bytes(16))
        mem.w32(addr('g_data'), G.DATA)
        self.fr.call(addr('dc_init'), G.FAKE)
        self.dc = addr('dc_st')

    def addr(self, name):
        return self.B + self.s[name]

    def photos(self):
        s, mem, addr, fr = self.s, self.mem, self.addr, self.fr
        ops = addr('replay')+mem.r32(addr('replay')+12)
        visual = None
        for k in range(self.n):
            logical = sum(fr.call(addr('dc_cop'), G.FAKE).values()) if k else 0
            photo = mem.r16(self.dc+s['DC_NEW'])
            rec = addr('dc_rec')+photo*s['DC_REC']
            op = mem.r8(ops+6*k)
            # RUN/RUNSYNC llaman level_frame y renuevan graficos. SKIP y
            # SYNC conservan los flujos de la ultima llamada, aunque SYNC
            # cargue otra camara. El stamp identifica logica, no esa pose.
            if op in (V.REP_RUN, V.REP_RUNSYNC):
                visual = self.first+k
            stamp = mem.r16(rec+s['R_FRAME'])
            if stamp != k:
                raise ValueError('foto/oraculo ambiguos: %d/%d' % (k, stamp))
            mem.w16(self.dc+s['DC_REND'], photo)
            mem.w16(fr.vars+s['V_S'], mem.r16(rec+s['R_S']))
            costs = [sum(fr.call(addr(n), G.FAKE).values())
                     for n in ('columns', 'apply_colors', 'set_pointers', 'build_mid', 'dc_g5render')]
            self.cpu.cpu.w_reg(self.cpu.M.Register.D7, photo)
            costs.append(sum(fr.call(addr('dc_hdr'), G.FAKE).values()))
            back = mem.r32(fr.vars+s['V_BACK'])
            yield dict(stamp=stamp, frame=self.first+stamp, photo=photo, rec=rec,
                       visual_frame=visual, op=op, back=back, base_cycles=logical+sum(costs))
            mem.w32(self.dc+s['DC_PLIST'], back)
            mem.w16(self.dc+s['DC_FRONT'], photo)
            mem.w16(self.dc+s['DC_REND'], 0xffff)
            other = mem.r32(fr.vars+(s['V_COP2'] if back == mem.r32(fr.vars+s['V_COP']) else s['V_COP']))
            mem.w32(fr.vars+s['V_BACK'], other)


def generate(a):
    derived_path(a.out)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ctx = T.load_context(a.bank)
    oracle_frames = {f for f, _, _ in R.G.load_oam_bin(a.oracle)}
    groups = collections.defaultdict(list)
    for rec in R.read_trace(a.trace, a.oracle):
        groups[rec['frame']].append(rec)
    replay = Replay(a.bin, a.lst)
    s, mem = replay.s, replay.mem
    if s['CL_LINES'] != 344 or s['SEG'] != 256:
        raise ValueError('layout distinto de C1')
    totals = collections.Counter()
    entries, plans, cameras, frozen = [], [], 0, []
    for photo in replay.photos():
        f, stamp, base = photo['frame'], photo['stamp'], photo['back']
        if f not in oracle_frames:
            raise ValueError('foto sin frame logico del oraculo f%d' % f)
        source = photo['visual_frame']
        recs = groups.get(source, [])
        if not any(r['num'] == 0xab for r in recs):
            continue
        ram = recs[0]['ram']
        live = replay.cpu.read(replay.addr('_ram'), 8192)
        camera = live[0x1a] | live[0x1b]<<8
        current = groups.get(f)
        if photo['op'] != V.REP_SKIP and current:
            expected_camera = current[0]['ram'][0x1a] | current[0]['ram'][0x1b]<<8
        else:
            expected_camera = ram[0x1a] | ram[0x1b]<<8
        if camera != expected_camera:
            raise ValueError('camara logica distinta del oraculo f%d' % f)
        if mem.r16(photo['rec']+s['R_S']) != camera:
            ops = replay.addr('replay')+mem.r32(replay.addr('replay')+12)
            problem = dict(frame=f, stamp=stamp, oracle_camera=camera,
                           photo_camera=mem.r16(photo['rec']+s['R_S']),
                           game_camera=live[0x1a] | live[0x1b]<<8,
                           op=mem.r8(ops+6*stamp), data_width=mem.r16(G.DATA+s['D_W']),
                           rex_photos_before=len(entries))
            (out/'mapping_failure.json').write_text(json.dumps(problem, indent=2), encoding='utf-8')
            raise ValueError('camara de foto distinta del oraculo f%d' % f)
        cameras += 1
        ptr = mem.r32(replay.addr('g_sbuf')+4*photo['photo'])
        drawn = photo_pixels(replay.cpu.read(ptr, 672))
        truth, _ = T.mario_amiga(ram, recs[0]['recorded'], ctx['gfx'])
        if drawn != truth:
            raise ValueError('pose de foto distinta del frame grafico f%d -> f%s' % (f, source))
        pal = mem.r8(photo['rec']+s['R_PAL'])
        refpal = R.palette_index(ram, ctx['pointers'])
        if ctx['pals'][32*pal:32*pal+32] != ctx['pals'][32*refpal:32*refpal+32]:
            (out/'palette_mapping_failure.json').write_text(json.dumps(dict(frame=f, source=source,
                actual=pal, reference=refpal), indent=2), encoding='utf-8')
            raise ValueError('colores de foto distintos del frame grafico f%d' % f)
        if source != f:
            frozen.append(dict(stamp=stamp, logical=f, visual=source, op=photo['op'], camera=camera))
        segs = T.segments(mem, base, s['CL_LINES'], s['SEG'])
        p, ev = T.plan_frame(recs, ctx, segs)
        if p.get('sufijos') is not None:
            c1, pos, _ = T.check_list(mem, base, s['CL_LINES'], s['SEG'], p['sufijos'])
            p['contadores']['errores_capa1'] += c1
            p['contadores']['errores_color'] += pos
        totals.update(p['contadores'])
        signs = {}
        for row in p.get('sufijos', {}):
            words, _ = T.segment_words(mem, base, s['CL_LINES'], s['SEG'], int(row))
            signs[int(row)] = sum(x for pair in words for x in pair) & 65535
        entries.append((stamp, p, signs))
        p['photo_frame'] = f
        p['photo_stamp'] = stamp
        plans.append(p)
        if len(entries) % 200 == 0:
            print('C2a %d fotos Rex; ultima foto %d -> f%d' % (len(entries), stamp, f), flush=True)
    failures = {k: totals[k] for k in ('sin_variante_temporal', 'sin_plazo', 'errores_color',
                                     'errores_capa1', 'prioridad_distinta') if totals[k]}
    if failures:
        raise ValueError('C2a falla puerta del modelo sobre listas reales: %s' % failures)
    blob = table_bytes(entries)
    (out/'g2t_pre.bin').write_bytes(blob)
    (out/'plans.json').write_text(json.dumps(plans), encoding='utf-8')
    summary = dict(first=replay.first, frames=replay.n, rex_photos=len(entries),
                   photos_without_oracle=0,
                   camera_checks=cameras, mapping='logical = first + R_FRAME; visual = last RUN/RUNSYNC',
                   frozen=frozen,
                   counters=dict(totals), failures=failures, bytes=len(blob),
                   max_suffix_rows=max(len(p.get('sufijos', {})) for p in plans))
    (out/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    if a.stopf is not None:
        selected = [e for e in entries if a.stopf-16 <= e[0] <= a.stopf]
        window = table_bytes(selected)
        if len(window) > 16384:
            raise ValueError('ventana mayor de 16 KB')
        (out/'window.bin').write_bytes(window)
    print('C2a: %s' % summary, flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    inc = sub.add_parser('include')
    inc.add_argument('--table', required=True)
    gen = sub.add_parser('generate')
    gen.add_argument('--bin', default='work/g2tc/ext/game.bin')
    gen.add_argument('--lst', default='work/g2tc/ext/game.lst')
    gen.add_argument('--bank', default='work/g3/bank')
    gen.add_argument('--trace', default='work/oam_yi1.trace')
    gen.add_argument('--oracle', default='work/oracle_yi1_oam.bin')
    gen.add_argument('--out', default='work/g2tc')
    gen.add_argument('--stopf', type=int)
    a = ap.parse_args()
    (include if a.cmd == 'include' else generate)(a)


if __name__ == '__main__':
    main()
