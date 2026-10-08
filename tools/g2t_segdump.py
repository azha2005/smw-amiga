#!/usr/bin/env python3
"""G2T-B3: volcado de las listas del copper que ve g2t_ref.py, para el C.

Repite el bucle de g2t_ref.run (mismo scroll.s, mismo scroll_frame por
frame de la traza, misma condición «frame con Rex») sin tocar g2t_ref.py
(docs/instrucciones-g2t-b35.md B3-1). Por traza escribe en --out:

  segw_<traza>.bin: por frame con Rex, frame u32 y por fila 0..223
      n u8 + n x (u16, u16): las palabras del segmento desde su inicio
      hasta el salto $0084 incluido (lo que lee g5_segment);
  segs_<traza>.bin: por frame con Rex, frame u32 y por fila nb u8,
      last s16 ($7FFF = ninguna), wrap u8 (g2t_ref.segments).

Comprueba que una lista rearmada desde segw da los mismos segs.

    python tools/g2t_segdump.py --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin ...
"""
import argparse
import collections
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import g2t_ref as T          # noqa: E402
import g5ref as R            # noqa: E402
import scrollprof as P       # noqa: E402
import sprgfx_final as F     # noqa: E402


class Mem:
    """Memoria mínima con r16 para rearmar una lista desde segw."""
    def __init__(self, size):
        self.b = bytearray(size)

    def r16(self, a):
        return self.b[a] << 8 | self.b[a + 1]


def seg_words(mem, base, cl, seg, L):
    out = []
    a = base + cl + seg * L
    for o in range(0, seg, 4):
        w1, w2 = mem.r16(a + o), mem.r16(a + o + 2)
        out.append((w1, w2))
        if w1 == 0x84:
            return out
    raise F.FormatError('salto no encontrado (fila %d)' % L)


def pack_segs(segs):
    return b''.join(struct.pack('>Bhb', s['nb'], 0x7fff if s['last'] is None else s['last'], int(s['wrap']))
                    for s in segs)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--trace', action='append', required=True, help='traza=oracle_oam.bin')
    ap.add_argument('--out', default='work/g2tb35')
    a = ap.parse_args()
    F.derived_path(a.out)
    Path(a.out).mkdir(parents=True, exist_ok=True)
    code, lst = P.assemble('player/scroll.s', ['VIS=256', 'SPRITES'])
    syms, local = P.listing(lst)
    cl, seg = syms['CL_LINES'], syms['SEG']
    F.require(cl == 216 and seg == 220, 'layout de scroll distinto')
    V = {n: v for n, v in syms.items() if n.startswith('V_')}
    for pair in a.trace:
        path, oracle = pair.split('=', 1)
        name = Path(path).stem.removeprefix('oam_')
        groups = collections.defaultdict(list)
        for rec in R.read_trace(path, oracle):
            groups[rec['frame']].append(rec)
        sc = P.Scroll(code, syms, local, Path('work/yi1_s.dat').read_bytes(), V)
        sc.init()
        segw, segs, n = bytearray(), bytearray(), 0
        for frame in sorted(groups):
            recs = groups[frame]
            ram = recs[0]['ram']
            sc.mem.w16(sc.vars + V['V_S'], ram[0x1a] | ram[0x1b] << 8)
            sc.call('scroll_frame')
            if not any(r['num'] == 0xab for r in recs):
                continue
            base = sc.mem.r32(P.FAKE + 0x80)
            ref = T.segments(sc.mem, base, cl, seg)
            mem = Mem(cl + seg * T.ROWS + 4)
            segw += struct.pack('>I', frame)
            for L in range(T.ROWS):
                words = seg_words(sc.mem, base, cl, seg, L)
                segw += struct.pack('>B', len(words))
                for k, (w1, w2) in enumerate(words):
                    segw += struct.pack('>HH', w1, w2)
                    o = cl + seg * L + 4 * k
                    mem.b[o:o + 4] = struct.pack('>HH', w1, w2)
            F.require(T.segments(mem, 0, cl, seg) == ref, 'segw no reproduce segments (frame %d)' % frame)
            segs += struct.pack('>I', frame) + pack_segs(ref)
            n += 1
        Path(a.out, 'segw_%s.bin' % name).write_bytes(segw)
        Path(a.out, 'segs_%s.bin' % name).write_bytes(segs)
        print('%s: %d frames con Rex, segw %d B, segs %d B (segw reproduce segments)' %
              (name, n, len(segw), len(segs)), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
