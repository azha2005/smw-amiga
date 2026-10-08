#!/usr/bin/env python3
"""B2bis: clave MA1 recogida en la fase exacta y verificada con mspr_draw.

key genera una copia instrumental del arnes PC en work/, recoge OAM/osz,
exige B2 identico, reconstruye la clave y la compara con la ficha real del
68000. Comprueba misma clave => mismos DATA/DATB en las tres trazas y
entre ellas, omitiendo bytes inactivos que el hardware nunca lee.
"""
import argparse
import collections
import json
import os
import random
from pathlib import Path
import struct
import subprocess
import sys

import m68kverify as V
from g5plan_verify import read_cap
from g5plan_verify import block_env
from sprgfx_final import derived_path


SPRW = 84


def image(spr):
    """DATA/DATB significativos, canvas relativo de 40 filas x 32 px.
    Los terminadores, columnas inactivas y las filas despues de VSTOP
    son ajenos a la imagen: pueden contener bytes de la pose anterior.
    """
    out = bytearray(640)
    for c in range(2):
        pos, ctl = struct.unpack_from('>HH', spr, 2 * c * SPRW * 2)
        if not (pos or ctl):
            continue
        vs = (pos >> 8) | ((ctl & 4) << 6)
        ve = (ctl >> 8) | ((ctl & 2) << 7)
        if not 0 <= ve - vs <= 40:
            raise ValueError('alto de sprite fuera de 40')
        for j in range(ve - vs):
            a = 2 * c * SPRW * 2 + 4 + 4 * j
            out[320 * c + 8 * j:320 * c + 8 * j + 8] = spr[a:a + 4] + spr[a + SPRW * 2:a + SPRW * 2 + 4]
    return bytes(out)


def key_of(oam, osz, ram):
    """Replica la normalizacion de mspr_draw, y rechaza sus caminos al C.
    No usa numero de pose/direccion/powerup como sustituto de la clave.
    """
    entries, xs = [], set()
    for e in range(4):
        x, y, tile, prop = oam[4 * e:4 * e + 4]
        if y == 0xf0:
            continue
        if not osz[e] & 2 or prop & 0x80:
            return None, 'C: tamano/volteo vertical'
        xs.add(x - 256 if osz[e] & 1 else x)
        y = y - 256 if y > 0xf0 else y
        entries.append((y, tile, prop))
    if not entries:
        return None, 'sin entradas visibles'
    if len(xs) != 1:
        return None, 'C: distintas X'
    by = min(e[0] for e in entries)
    if max(e[0] for e in entries) + 16 - by > 40:
        return None, 'C: alto'
    if any(abs(a[0] - b[0]) < 16 for i, a in enumerate(entries) for b in entries[i + 1:]):
        return None, 'C: solape'
    pose = struct.pack('>H', len(entries)) + b''.join(struct.pack('>hBB', y - by, t, p) for y, t, p in entries)
    return pose.ljust(18, b'\0') + ram[0xd85:0xd9b], 'MA1'


def dump_keys(out):
    src = Path('tools/marioverify.c').read_text(encoding='utf-8')
    patches = [
        ('static void g2t_frame(long i)', '#include "g5env_keydump.h"\n\nstatic void g2t_frame(long i)'),
        ('    if (!g2t_has_rex()) return;', '    if (!g2t_has_rex()) return;\n    g5key_dump(f);'),
        ('        g2t_cap = NULL;', '        g2t_cap = NULL;\n        g5key_finish();'),
    ]
    for old, new in patches:
        if src.count(old) != 1:
            raise ValueError('ancla del arnes ausente/ambigua: ' + old)
        src = src.replace(old, new)
    copy = out / 'marioverify_key.c'
    copy.write_text(src, encoding='utf-8')
    exe = out / 'marioverify_key.exe'
    sources = ['player/' + n + '.c' for n in ('mario', 'mcoll', 'manim', 'mgfx', 'mcam', 'msprite', 'mspr', 'g5plan')]
    sources += [str(p) for p in sorted(Path('player').glob('spr_*.c'))] + ['player/gen/smwrom00.c']
    subprocess.run(['gcc', '-O2', '-DNOOAM', '-DSPR_OAM', '-DSPR_G5', '-Iplayer', '-Itools',
                    '-o', str(exe), str(copy), *sources], check=True)
    for name in ('yi1', 'normal', 'spin_kill'):
        env = dict(os.environ, GAME_G5KEY_CAP=str(out / ('key_' + name + '.bin')),
                   GAME_G2T_CAP=str(out / ('cap_' + name + '.bin')))
        with (out / ('dump_' + name + '.log')).open('w') as log:
            subprocess.run([str(exe), 'work/oracle_' + name + '.bin', 'game'], env=env,
                            stdout=log, stderr=subprocess.STDOUT, check=True)
        if (out / ('cap_' + name + '.bin')).read_bytes() != Path('work/g5gate/cap_' + name + '.bin').read_bytes():
            raise ValueError('el dump de la clave altero el bloque B2: ' + name)
        print('dump clave %s: B2 identico' % name, flush=True)


def run_key(a):
    derived_path(a.out)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    dump_keys(out)
    cpu, B = V.MusashiCPU(), V.BASE
    syms = V.symbols(a.lst)
    cpu.write(B, Path(a.bin).read_bytes())
    cpu.mem.w32(B + syms['_gfx32'], B + syms['gfx32'])
    BUF = 0xc0000
    cpu.mem.w32(B + syms['g_spra'], BUF)
    cpu.mem.w32(B + syms['g_sprb'], BUF + 0x1000)
    from gamecheck import call_args
    global_keys, images, results = {}, set(), {}
    for name in ('yi1', 'normal', 'spin_kill'):
        kd = (out / ('key_' + name + '.bin')).read_bytes()
        caps = list(read_cap(out / ('cap_' + name + '.bin')))
        if len(kd) != 24 * len(caps):
            raise ValueError('clave y B2 desalineados: ' + name)
        keys, reasons, collisions, checked = {}, collections.Counter(), [], 0
        for i, c in enumerate(caps):
            frame, = struct.unpack_from('>I', kd, 24 * i)
            if frame != c['frame']:
                raise ValueError('frames clave/B2 distintos')
            oam, osz = kd[24 * i + 4:24 * i + 20], kd[24 * i + 20:24 * i + 24]
            key, reason = key_of(oam, osz, c['ram'])
            reasons[reason] += 1
            pic = image(c['spr'])
            images.add(pic)
            if key is None:
                continue
            for table in (keys, global_keys):
                if key in table and table[key][0] != pic:
                    collisions.append(dict(frame=frame, previous=table[key][1], key=key.hex()))
                table[key] = (pic, frame)
            cpu.write(B + syms['_ram'], c['ram'])
            cpu.write(B + syms['_mario_oam'], oam)
            cpu.write(B + syms['_mario_osz'], osz)
            cpu.write(B + syms['mspr_kA'], b'\0' * 128)
            cpu.write(BUF, b'\xa5' * 672)
            call_args(cpu, B + syms['mspr_draw'], B, BUF)
            ficha = cpu.read(B + syms['mspr_kA'], 64)
            if ficha[:2] != b'\0\1' or ficha[46:64] + ficha[3:25] != key:
                raise ValueError('clave reconstruida != MA1 real: %s frame %d' % (name, frame))
            if image(cpu.read(BUF, 672)) != pic:
                raise ValueError('datos mspr_draw != B2: %s frame %d' % (name, frame))
            checked += 1
        results[name] = dict(frames=len(caps), keys=len(keys), collisions=collisions,
                             asm_checked=checked, paths=dict(reasons))
        print('B2b-1 %s: %d frames; claves %d; colisiones %d; clave/DATA MA1 real exactos %d; sin clave %d' %
              (name, len(caps), len(keys), len(collisions), checked, len(caps) - checked), flush=True)
    results['global'] = dict(keys=len(global_keys), images=len(images),
                             collisions=sum(len(v['collisions']) for v in results.values()))
    (out / 'key_summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    if results['global']['collisions']:
        raise ValueError('PARADA B2b-1: misma clave, DATA/DATB distintos; ver key_summary.json')
    print('PUERTA B2b-1: OK', flush=True)


def decode_env(data, spr):
    """La mascara exacta se recorta antes de buscar los extremos."""
    height, cols = struct.unpack_from('>HH', data)
    if not height:
        return {}
    base = 0 if any(spr[:4]) else 336
    pos, ctl = struct.unpack_from('>HH', spr, base)
    vs = (pos >> 8) | ((ctl & 4) << 6)
    hs = ((pos & 255) << 1) | (ctl & 1)
    x0, r0 = hs - 160, vs - 44
    width, stride = cols * 16, 30 if cols == 1 else 62
    env = {}
    for j in range(height):
        row = r0 + j
        if not 0 <= row < 224:
            continue
        mask = 0xfffe if cols == 1 else struct.unpack_from('>H', data, 4 + stride * j)[0]
        for idx in range(1, 16):
            if not mask >> idx & 1:
                continue
            offset = 4 + stride * j + (0 if cols == 1 else 2) + (idx - 1) * (2 if cols == 1 else 4)
            raw = int.from_bytes(data[offset:offset + (2 if cols == 1 else 4)], 'big')
            xs = [x0 + u for u in range(width) if raw >> (width - 1 - u) & 1 and 0 <= x0 + u < 256]
            if xs:
                env[row, idx] = min(xs), max(xs)
    return env


def pixel_masks(spr):
    """Oraculo independiente por pixel, en coordenadas relativas."""
    base = 0 if any(spr[:4]) else 336
    if not any(spr[base:base + 4]):
        return {}
    pos, ctl = struct.unpack_from('>HH', spr, base)
    height = ((ctl >> 8) | ((ctl & 2) << 7)) - ((pos >> 8) | ((ctl & 4) << 6))
    cols = 2 if base == 0 and any(spr[336:340]) else 1
    masks = {}
    for j in range(height):
        for col in range(cols):
            p = struct.unpack_from('>HH', spr, base + 336 * col + 4 + 4 * j)
            p += struct.unpack_from('>HH', spr, base + 336 * col + 172 + 4 * j)
            for u in range(16):
                idx = sum(((p[k] >> (15 - u)) & 1) << k for k in range(4))
                if idx:
                    masks[j, idx] = masks.get((j, idx), 0) | (1 << (16 * cols - 1 - 16 * col - u))
    return masks


def stored_masks(data):
    height, cols = struct.unpack_from('>HH', data)
    stride = 30 if cols == 1 else 62
    masks = {}
    for j in range(height):
        valid = 0xfffe if cols == 1 else struct.unpack_from('>H', data, 4 + stride * j)[0]
        for idx in range(1, 16):
            if valid & (1 << idx):
                off = 4 + stride * j + (0 if cols == 1 else 2) + (idx - 1) * (2 if cols == 1 else 4)
                raw = int.from_bytes(data[off:off + (2 if cols == 1 else 4)], 'big')
                if raw:
                    masks[j, idx] = raw
    return masks


def synthetic_decode(m):
    """Todas las tintas, huecos y ambos bordes, sin datos de la ROM."""
    rng = random.Random(0xB2B)
    count = 0
    for cols in (1, 2):
        for height in (1, 16, 32, 40):
            for x0, r0 in ((-15, -4), (0, 0), (240, 210), (255, 223)):
                spr = bytearray(672)
                vs, ve = 44 + r0, 44 + r0 + height
                for col in range(cols):
                    hs = 160 + x0 + 16 * col
                    for half in range(2):
                        b = col * 336 + half * 168
                        struct.pack_into('>HH', spr, b, ((vs & 255) << 8) | (hs >> 1),
                                         ((ve & 255) << 8) | (hs & 1) | ((vs >> 8) << 2) |
                                         ((ve >> 8) << 1) | (half << 7))
                    for j in range(height):
                        ps = [rng.getrandbits(16) for _ in range(4)]
                        struct.pack_into('>HH', spr, col * 336 + 4 + 4 * j, *ps[:2])
                        struct.pack_into('>HH', spr, col * 336 + 172 + 4 * j, *ps[2:])
                _, data = m.decode(bytes(spr))
                want = pixel_masks(spr)
                if stored_masks(data) != want:
                    raise ValueError('mascaras sinteticas distintas')
                env = {}
                for (j, idx), raw in want.items():
                    xs = [x0 + u for u in range(16 * cols)
                          if raw >> (16 * cols - 1 - u) & 1 and 0 <= x0 + u < 256]
                    if xs and 0 <= r0 + j < 224:
                        env[r0 + j, idx] = min(xs), max(xs)
                if decode_env(data, spr) != env:
                    raise ValueError('recorte sintetico distinto')
                count += 1
    # Una unica columna activa puede ser SPR2/3, no solo SPR0/1.
    spr[:336] = bytes(336)
    _, data = m.decode(bytes(spr))
    if stored_masks(data) != pixel_masks(spr):
        raise ValueError('segunda columna aislada distinta')
    print('B2b-2 sinteticos: %d casos + SPR2 aislado; mascaras completas, huecos y recorte exactos' % count)


class EnvCPU:
    """Rutinas puras, dos bases, ABI completa y limites de escritura."""
    def __init__(self, code, syms):
        self.cpu = V.MusashiCPU()
        self.syms, self.number = syms, 0
        self.cpu.write(V.BASE, code)
        self.cpu.write(V.BASE + 0x8000, code)

    def decode(self, spr):
        cpu, M = self.cpu, self.cpu.M
        delta = 0x8000 if self.number & 1 else 0
        self.number += 1
        inp, out = 0x60000 + delta, 0x64000 + delta
        cpu.write(inp - 4, b'HEAD' + spr + b'TAIL')
        cpu.write(out - 4, b'HEAD' + b'\xa5' * 2484 + b'TAIL')
        saved = {getattr(M.Register, r): 0x23456700 + k
                 for k, r in enumerate(('D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'A2', 'A3', 'A4', 'A5', 'A6'))}
        for reg, val in saved.items():
            cpu.cpu.w_reg(reg, val)
        sp = V.STACK - 12
        cpu.cpu.w_reg(M.Register.A7, sp)
        cpu.write(sp, struct.pack('>III', V.RET, inp, out))
        cpu.cpu.w_pc(V.BASE + delta + self.syms['_g5env_decode'])
        cycles = cpu.m.execute(1_000_000).cycles - 34
        if cpu.cpu.r_pc() not in (V.RET, V.RET + 2):
            raise ValueError('decoder no regreso')
        if any(cpu.cpu.r_reg(r) != v for r, v in saved.items()) or cpu.cpu.r_reg(M.Register.A7) != sp + 4:
            raise ValueError('decoder rompio ABI')
        size = cpu.cpu.r_reg(M.Register.D0) & 65535
        if not 4 <= size <= 2484:
            raise ValueError('decoder rechazo cabecera valida: %d' % size)
        data = cpu.read(out, size)
        height, cols = struct.unpack_from('>HH', data)
        if height > 40 or size != 4 + height * (30 if cols == 1 else 62):
            raise ValueError('decoder devolvio tamano/formato invalido')
        if (cpu.read(inp - 4, 680) != b'HEAD' + spr + b'TAIL'
                or cpu.read(out - 4, 4) != b'HEAD' or cpu.read(out + 2484, 4) != b'TAIL'
                or cpu.read(out + size, 2484 - size) != b'\xa5' * (2484 - size)):
            raise ValueError('decoder escribio fuera de salida o cambio entrada')
        return cycles, data


def run_decode(a):
    derived_path(a.out)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    from regress import vasm
    assembler = vasm()
    if not assembler:
        raise ValueError('no encuentro vasm')
    bp, lp = out / 'env.bin', out / 'env.lst'
    subprocess.run([assembler, '-quiet', '-Fbin', '-m68000', '-no-opt', '-DSPR_G5',
                    '-L', str(lp), '-o', str(bp), 'player/g5env.s'], check=True)
    subprocess.run([sys.executable, 'tools/piccheck.py', '--lst', str(lp)], check=True)
    m = EnvCPU(bp.read_bytes(), V.symbols(lp))
    results = {}
    for name in ('yi1', 'normal', 'spin_kill'):
        costs, bad, cases = [], [], 0
        for c in read_cap('work/g5gate/cap_' + name + '.bin'):
            cycles, data = m.decode(c['spr'])
            if stored_masks(data) != pixel_masks(c['spr']):
                raise ValueError('mascara completa distinta: %s %d' % (name, c['frame']))
            got, want = decode_env(data, c['spr']), block_env(c['blk'])
            if got != want:
                bad.append(c['frame'])
                if len(bad) < 4:
                    print('decoder distinto %s %d: %s' % (name, c['frame'],
                          [(k, want.get(k), got.get(k)) for k in want.keys() | got.keys() if want.get(k) != got.get(k)][:5]))
            costs.append((cycles, c['frame']))
            cases += 1
        if not cases:
            raise ValueError('captura vacia')
        mx = max(costs)
        results[name] = dict(frames=cases, diff=bad, mean=sum(c for c, _ in costs) / cases,
                             max=mx[0], worst_frame=mx[1])
        print('B2b-2 %s: %d frames; diferentes %d, ABI 0; decoder sin DMA media %.0f max %d (frame %d)' %
              (name, cases, len(bad), results[name]['mean'], *mx), flush=True)
    (out / 'decode_summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    if any(v['diff'] for v in results.values()):
        raise ValueError('decoder distinto del control')
    synthetic_decode(m)
    c = next(c for c in read_cap('work/g5gate/cap_yi1.bin') if c['frame'] == 10364)
    caught = False
    for j in range(32):
        for u in range(16):
            spr = bytearray(c['spr'])
            spr[4 + 4 * j + u // 8] ^= 1 << (7 - u % 8)
            _, data = m.decode(bytes(spr))
            if decode_env(data, spr) != block_env(c['blk']):
                caught = True
                break
        if caught:
            break
    if not caught:
        raise ValueError('el pixel alterado escapo a la puerta')
    print('B2b-2 negativa: pixel alterado detectado (frame 10364, fila %d, x relativo %d)' % (j, u))
    over = max(v['max'] for v in results.values())
    print('PUERTA B2b-2 exactitud/ABI: OK; ciclos <=12000: %s' % ('OK' if over <= 12000 else 'FALTA'), flush=True)
    return 0 if over <= 12000 else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    k = sub.add_parser('key')
    k.add_argument('--out', default='work/b2b/key')
    k.add_argument('--bin', default='work/b35_mem_replay/game.bin')
    k.add_argument('--lst', default='work/b35_mem_replay/game.lst')
    d = sub.add_parser('decode')
    d.add_argument('--out', default='work/b2b/decode')
    a = ap.parse_args()
    return run_key(a) if a.cmd == 'key' else run_decode(a)


if __name__ == '__main__':
    sys.exit(main())
