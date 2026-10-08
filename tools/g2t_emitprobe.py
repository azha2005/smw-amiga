#!/usr/bin/env python3
"""C2b: coste de la consulta y firmas obligatorias, antes de emitir."""
import argparse
import json
from pathlib import Path
from g2t_preplan import Replay, table_index
import g2t_ref as T
from sprgfx_final import derived_path
import gamecheck as G
import m68kverify as V


class ExternalCPU(V.MusashiCPU):
    """RAM virtual extra solo para la tabla G5_PRE_EXT de la tarjeta C3.

    No cambia el mapa del juego ni afirma que la tabla cabe en la A500.
    """
    def __init__(self):
        import machine68k as M
        self.M = M
        self.m = M.Machine(M.CPUType.M68000, 2048)
        self.cpu, self.mem = self.m.cpu, self.m.mem
        tid = self.m.traps.alloc(lambda op, pc: self.m.abort_execute())
        self.mem.w16(V.RET, 0xa000 | tid)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin', default='work/g2tc/ext/game.bin')
    ap.add_argument('--lst', default='work/g2tc/ext/game.lst')
    ap.add_argument('--table', default='work/g2tc/g2t_pre.bin')
    ap.add_argument('--out', default='work/g2tc')
    a = ap.parse_args()
    derived_path(a.out)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    replay = Replay(a.bin, a.lst, ExternalCPU)
    mem, cpu, addr, s = replay.mem, replay.cpu, replay.addr, replay.s
    blob = Path(a.table).read_bytes()
    base = 0x180000                       # fuera del mapa; solo G5_PRE_EXT
    indices = table_index(blob)
    if base+len(blob) > 2048*1024:
        raise ValueError('tabla externa excede la RAM virtual del arnes')
    cpu.write(base, blob)
    mem.w32(addr('g5_pre'), base)
    costs, totals, prefixes, checked, negative = [], [], [], 0, False
    for photo in replay.photos():
        original = cpu.read(photo['back'], s['CL_SIZE'])
        cpu.cpu.w_reg(cpu.M.Register.D7, photo['photo'])
        saved = {getattr(cpu.M.Register, r): cpu.cpu.r_reg(getattr(cpu.M.Register, r))
                 for r in ('D2','D3','D4','D5','D6','D7','A2','A3','A4','A5','A6')}
        saved[cpu.M.Register.A3] = G.DATA
        saved[cpu.M.Register.A4] = G.FAKE
        saved[cpu.M.Register.A5] = replay.fr.vars
        cost = sum(replay.fr.call(addr('g5_emit'), G.FAKE).values())
        if cpu.cpu.r_reg(cpu.M.Register.D0) or mem.r32(addr('g5_miss')):
            raise ValueError('firma real distinta, f%d' % photo['frame'])
        if any(cpu.cpu.r_reg(r) != v for r,v in saved.items()):
            raise ValueError('ABI distinta, f%d' % photo['frame'])
        if cpu.read(photo['back'], s['CL_SIZE']) != original:
            raise ValueError('prototipo escribio en lista')
        costs.append((cost, photo['frame']))
        totals.append((cost+photo['base_cycles'], photo['frame']))
        off = indices.get(photo['stamp'])
        if off is not None:
            checked += 1
            p = off+46
            p += 1+3*blob[p]
            n = blob[p]
            p += 1
            word_count = 0
            for _ in range(n):
                words, _ = T.segment_words(mem, photo['back'], s['CL_LINES'], s['SEG'], blob[p])
                word_count += 2*len(words)
                p += 5+3*blob[p+4]
            prefixes.append((word_count, photo['frame'], n))
            if not negative:
                p = off+46
                p += 1+3*blob[p]
                n = blob[p]
                if n:
                    p += 1
                    for _ in range(n):
                        p += 5+3*blob[p+4]
                    at = base+p+1          # byte alto de primera firma
                    old = mem.r8(at)
                    mem.w8(at, old^1)
                    cpu.cpu.w_reg(cpu.M.Register.D7, photo['photo'])
                    replay.fr.call(addr('g5_emit'), G.FAKE)
                    if cpu.cpu.r_reg(cpu.M.Register.D0) != 1 or mem.r32(addr('g5_miss')) != 1:
                        raise ValueError('firma negativa no detectada')
                    if cpu.read(photo['back'], s['CL_SIZE']) != original:
                        raise ValueError('firma negativa escribio lista')
                    mem.w8(at, old)
                    mem.w32(addr('g5_miss'), 0)
                    negative = True
    result = dict(frames=len(costs), plans_checked=checked, diff=0, abi=0,
                  negative_signature=negative, misses=mem.r32(addr('g5_miss')),
                  mean=sum(c for c,_ in costs)/len(costs), max=max(costs)[0],
                  worst_frame=max(costs)[1], total_max=max(totals)[0],
                  over_pal=sum(c>G.PAL_FRAME for c,_ in totals),
                  prefix_words_max=max(prefixes, default=(0, None, 0)),
                  limit=4000, complete_emitter=False, writes_to_lists=False)
    (out/'emit_probe_summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('C2b validacion obligatoria (sin emitir): %s' % result, flush=True)
    if result['max'] > 4000:
        raise SystemExit('Cpre: PARADA por coste >4000, antes de C3/C4')


if __name__ == '__main__':
    main()
