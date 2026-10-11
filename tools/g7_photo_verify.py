#!/usr/bin/env python3
"""G7-2: OAM capturada, cobertura de fuentes y foto protegida en Musashi."""
import argparse
import json
from pathlib import Path

from g5l import GameRun
import g7_sources as B
import mksprgfx as S
from sws_cmp import OAM_GROUPS


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin', required=True)
    ap.add_argument('--lst', required=True)
    ap.add_argument('--sources', default='work/g7/sources.bin')
    a = ap.parse_args()
    blob = Path(a.sources).read_bytes()
    vr, _, _ = S.build_vram(S._DEF_SRC, S.LEVEL)
    g = GameRun(a.bin, a.lst, 'work/g3/bank')
    s, mem, cpu, addr = g.s, g.mem, g.cpu, g.addr
    assert 'R_OAM' in s and s['DC_REC'] == s['R_OAMHI']+64
    forms = set()
    visible = 0
    for k in range(g.n):
        if k:
            g.fr.call(addr('dc_cop'), g.G.FAKE)
        slot = mem.r16(g.dc+s['DC_NEW'])
        record = addr('dc_rec')+slot*s['DC_REC']
        lo = cpu.read(record+s['R_OAM'], 256)
        hi = cpu.read(record+s['R_OAMHI'], 64)
        assert lo == cpu.read(addr('_ram')+0x200, 256)
        assert hi == cpu.read(addr('_ram')+0x420, 64)
        if not mem.r8(record+s['R_SWS_VALID']):
            continue                       # SYNC/LEVEL no contienen OAM de efectos
        for groups in OAM_GROUPS.values():
            for first, n in groups:
                for entry in range(first, first+n):
                    x, y, tile, attr = lo[4*entry:4*entry+4]
                    x |= (hi[entry] & 1) << 8
                    if x >= 256:
                        x -= 512
                    width = 16 if hi[entry] & 2 else 8
                    if y >= 224 or x+width <= 0 or x >= 256:
                        continue
                    key = (tile | (attr & 1) << 8, width, bool(attr & 64), bool(attr & 128))
                    visible += 1
                    if key not in forms:
                        try:
                            pixels = B.ficha(blob, *key)
                        except KeyError as ex:
                            raise AssertionError(('fuente ausente', k, entry, key)) from ex
                        assert pixels == S.ficha(vr, *key)
                        forms.add(key)
    # Las tres fotos ocupadas deben sobrevivir a capturas nuevas aunque
    # la RAM de OAM cambie cada vez (render detenido/espera al PF1).
    for field, slot in (('DC_FRONT', 0), ('DC_PEND', 1), ('DC_REND', 2), ('DC_NEW', 3)):
        mem.w16(g.dc+s[field], slot)
    held = cpu.read(addr('dc_rec'), s['DC_REC']*3)
    cycles = []
    for nonce in range(10):
        low = bytes((i*7+nonce) & 255 for i in range(256))
        high = bytes((i+nonce) & 3 for i in range(64))
        cpu.write(addr('_ram')+0x200, low)
        cpu.write(addr('_ram')+0x420, high)
        cpu.cpu.w_reg(cpu.M.Register.D0, 0)
        cycles.append(sum(g.fr.call(addr('dc_capture'), g.G.FAKE).values()))
        assert mem.r16(g.dc+s['DC_NEW']) == 3
        assert cpu.read(addr('dc_rec'), s['DC_REC']*3) == held, 'foto ocupada pisada'
        record = addr('dc_rec')+3*s['DC_REC']
        assert cpu.read(record+s['R_OAM'], 256) == low
        assert cpu.read(record+s['R_OAMHI'], 64) == high
    print('G7 PHOTO: OK '+json.dumps(dict(frames=g.n, visible_tiles=visible,
        forms=len(forms), protected_captures=10, capture_max_cycles=max(cycles))))


if __name__ == '__main__':
    main()
