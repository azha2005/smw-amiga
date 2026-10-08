#!/usr/bin/env python3
"""G2T fase B (docs/instrucciones-g2t-bc.md §3): puertas B2 y B5.

  env   B2: las envolventes de Mario que g5_capture saca del buffer de
        sprites (volcado GAME_G2T_CAP del modo game de marioverify con
        -DSPR_G5) contra g2t_ref.mario_amiga de la traza SOT1, en todos los
        frames con Rex. Sale con 0 solo con 0 diferencias.
  m68k  B2/B5: el mismo g5_capture en el 68000 (logicbench con
        CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5', Musashi): mismas entradas que el
        PC, bloque igual (los bytes con significado) y ciclos.

  python tools/g5plan_verify.py env --cap work/g2tb/cap_yi1.bin \\
      --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin
  python tools/g5plan_verify.py m68k --cap work/g2tb/cap_yi1.bin \\
      --bin work/g5gate/logicbench.bin --lst work/g5gate/logicbench.lst

Los derivados se leen y escriben solo en work/ (R9).
"""
import argparse
import collections
import struct
import sys

# --- constantes de player/g5plan.h (el volcado las comprueba por tamaño) ---
G5_ROWS, G5_WIN, G5_MAXREX, G5_MAXT = 224, 40, 12, 16
G5B_FLAGS, G5B_PAL, G5B_NREX, G5B_CAMX, G5B_CAMY, G5B_MROW, G5B_MASK = 0, 2, 3, 4, 6, 8, 12
G5B_ENV = G5B_MASK + 2 * G5_WIN
G5B_REX = G5B_ENV + 30 * G5_WIN
G5R_E = 6
G5R_SIZE = G5R_E + 5 * G5_MAXT
G5_BLK = G5B_REX + G5_MAXREX * G5R_SIZE
MSPR_WORDS = 2 + 2 * 40 + 2
SPRB = 4 * MSPR_WORDS * 2
CAP_REC = 6 + 24 + 0x2000 + SPRB + G5_BLK


def read_cap(path):
    """Registros del volcado GAME_G2T_CAP (marioverify.c, g2t_frame)."""
    data = open(path, 'rb').read()
    if len(data) % CAP_REC:
        raise ValueError('%s: %d bytes, no es multiplo de %d (G5_BLK distinto?)' % (path, len(data), CAP_REC))
    for o in range(0, len(data), CAP_REC):
        frame, pal = struct.unpack_from('>IB', data, o)
        p = o + 6
        first, n = data[p:p + 12], data[p + 12:p + 24]
        p += 24
        ram = data[p:p + 0x2000]
        p += 0x2000
        spr = data[p:p + SPRB]
        p += SPRB
        yield dict(frame=frame, pal=pal, first=first, n=n, ram=ram, spr=spr, blk=data[p:p + G5_BLK])


def block_env(blk):
    """{(fila, indice): (primer x, ultimo x)} del bloque."""
    mrow, = struct.unpack_from('>h', blk, G5B_MROW)
    env = {}
    for j in range(G5_WIN):
        m, = struct.unpack_from('>H', blk, G5B_MASK + 2 * j)
        for i in range(1, 16):
            if m >> i & 1:
                a = G5B_ENV + 30 * j + 2 * (i - 1)
                env[mrow + j, i] = (blk[a], blk[a + 1])
        if m & 1:
            env[mrow + j, 0] = None          # el bit 0 no se usa nunca
    return env


def canonical(blk):
    """Los bytes con significado del bloque (lo demas puede ser de otra foto)."""
    out = bytearray(blk[:G5B_ENV])
    env = block_env(blk)
    for key in sorted(env):
        out += struct.pack('>hBBB', key[0], key[1], *(env[key] or (0, 0)))
    for r in range(blk[G5B_NREX]):
        a = G5B_REX + r * G5R_SIZE
        out += blk[a:a + G5R_E + 5 * blk[a + 1]]
    return bytes(out)


def run_env(args):
    import g5ref as R
    import g2t_ref as T
    import mksprgfx as G
    from pathlib import Path
    gfx = Path(G.WORK, 'cc', 'gfx32.bin').read_bytes()
    caps = {c['frame']: c for c in read_cap(args.cap)}
    path, oracle = args.trace.split('=', 1)
    groups = collections.defaultdict(list)
    for rec in R.read_trace(path, oracle):
        groups[rec['frame']].append(rec)
    frames = [f for f in sorted(groups) if any(r['num'] == 0xab for r in groups[f])]
    diff = frames_bad = flags_bad = dyn_bad = entries = 0
    shown = []
    for f in frames:
        recs = groups[f]
        rex = [r for r in recs if r['num'] == 0xab]
        ram = rex[0]['ram']
        dyn_bad += any(r['ram'][0xd82:0xd9b] != ram[0xd82:0xd9b] for r in recs)
        mario, _ = T.mario_amiga(ram, rex[0]['recorded'], gfx)
        want = {}
        for (x, rr), v in mario.items():
            lo, hi = want.get((rr, v), (x, x))
            want[rr, v] = (min(lo, x), max(hi, x))
        c = caps.get(f)
        if c is None:
            frames_bad += 1
            if len(shown) < 12:
                shown.append('frame %d: sin bloque del C' % f)
            continue
        flags, = struct.unpack_from('>H', c['blk'], G5B_FLAGS)
        flags_bad += bool(flags & 6)
        got = block_env(c['blk'])
        entries += len(want)
        d = sum(1 for k in set(want) | set(got) if want.get(k) != got.get(k))
        diff += d
        frames_bad += bool(d)
        if d and len(shown) < 12:
            ks = sorted(k for k in set(want) | set(got) if want.get(k) != got.get(k))[:4]
            shown.append('frame %d: %d distintas, p.ej. %s' % (
                f, d, ', '.join('R%d i%d ref %s C %s' % (k[0], k[1], want.get(k), got.get(k)) for k in ks)))
    extra = sorted(set(caps) - set(frames))
    for s in shown:
        print('  ' + s)
    print('B2 %s: frames con Rex %d (traza) / %d (C), solo en el C %d; envolventes (fila, indice) de la '
          'referencia %d, distintas %d en %d frames; banderas de desborde %d; punteros de Mario distintos '
          'entre registros %d' % (args.name or path, len(frames), len(caps), len(extra), entries, diff,
                                  frames_bad, flags_bad, dyn_bad))
    ok = frames and not diff and not frames_bad and not extra and not flags_bad and not dyn_bad
    print('PUERTA B2 %s: %s' % (args.name or path, 'OK' if ok else 'FALLA'))
    return 0 if ok else 1


class M68k:
    """El logicbench SPR_G5 en Musashi, con la ABI de vbcc (pila, a4)."""
    SPR, BLK = 0xC0000, 0xC1000

    def __init__(self, binpath, lstpath):
        import m68kverify as V
        self.V = V
        self.syms = V.symbols(lstpath)
        for s in ('_g5_capture', '_ram', '_spr_oam_first', '_spr_oam_n', '_mario_pal'):
            if s not in self.syms:
                raise ValueError("falta %s: compilar con CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5'" % s)
        self.cpu = V.MusashiCPU()
        self.cpu.write(V.BASE, open(binpath, 'rb').read())
        self.cpu.call(V.BASE + self.syms['_logic68k_init'], V.BASE)
        self.saved = None

    def sym(self, name):
        return self.V.BASE + self.syms[name]

    def call(self, name, *args):
        """Llama a una funcion del C; devuelve (ciclos sin DMA, d0)."""
        V, cpu = self.V, self.cpu
        M = cpu.M
        saved = {getattr(M.Register, r): 0x23456700 + k
                 for k, r in enumerate(('D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'A2', 'A3', 'A5', 'A6'))}
        for reg, value in saved.items():
            cpu.cpu.w_reg(reg, value)
        sp = V.STACK - 4 * (len(args) + 1)
        cpu.cpu.w_reg(M.Register.A4, V.BASE)
        cpu.cpu.w_reg(M.Register.A7, sp)
        cpu.write(sp, struct.pack('>%dI' % (len(args) + 1), V.RET, *args))
        cpu.cpu.w_pc(self.sym(name))
        cycles = cpu.m.execute(10_000_000).cycles - 34
        abi = (any(cpu.cpu.r_reg(r) != v for r, v in saved.items())
               or cpu.cpu.r_reg(M.Register.A4) != V.BASE or cpu.cpu.r_reg(M.Register.A7) != sp + 4)
        if cpu.cpu.r_pc() != V.RET + 2 and cpu.cpu.r_pc() != V.RET:
            raise ValueError('%s no volvio (pc %06X)' % (name, cpu.cpu.r_pc()))
        return cycles, cpu.cpu.r_reg(M.Register.D0), abi


def run_m68k(args):
    m = M68k(args.bin, args.lst)
    n = bad = abi_bad = 0
    cycles = []
    for c in read_cap(args.cap):
        m.cpu.write(m.sym('_ram'), c['ram'])
        m.cpu.write(m.sym('_spr_oam_first'), c['first'])
        m.cpu.write(m.sym('_spr_oam_n'), c['n'])
        m.cpu.write(m.sym('_mario_pal'), bytes([c['pal']]))
        m.cpu.write(m.SPR, c['spr'])
        cyc, _, abi = m.call('_g5_capture', m.BLK, m.SPR)
        got = m.cpu.read(m.BLK, G5_BLK)
        n += 1
        abi_bad += abi
        if canonical(got) != canonical(c['blk']):
            bad += 1
            if bad <= 5:
                print('  frame %d: bloque del 68000 distinto del PC' % c['frame'])
        cycles.append((cyc, c['frame']))
    if not n:
        print('B2/B5 68000: 0 frames')
        return 1
    mx = max(cycles)
    print('g5_capture 68000 %s: %d frames, bloques distintos %d, ABI distinta %d; ciclos (sin DMA) media %.0f, '
          'max %d (frame %d)' % (args.name or args.cap, n, bad, abi_bad, sum(c for c, _ in cycles) / n, mx[0], mx[1]))
    ok = not bad and not abi_bad
    print('PUERTA G5 CAPTURA 68000 %s: %s' % (args.name or args.cap, 'OK' if ok else 'FALLA'))
    if mx[0] > args.cap_max:
        print('PARADA B2: g5_capture max %d > %d ciclos' % (mx[0], args.cap_max))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('env', help='B2: envolventes del C contra g2t_ref.mario_amiga')
    e.add_argument('--cap', required=True)
    e.add_argument('--trace', required=True, help='SOT1=oracle_oam.bin (las de g2t_ref)')
    e.add_argument('--name')
    k = sub.add_parser('m68k', help='B2/B5: g5_capture en el 68000 (Musashi)')
    k.add_argument('--cap', required=True)
    k.add_argument('--bin', default='work/g5gate/logicbench.bin')
    k.add_argument('--lst', default='work/g5gate/logicbench.lst')
    k.add_argument('--cap-max', type=int, default=3000)
    k.add_argument('--name')
    a = ap.parse_args()
    return run_env(a) if a.cmd == 'env' else run_m68k(a)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, struct.error) as err:
        sys.exit(str(err))
