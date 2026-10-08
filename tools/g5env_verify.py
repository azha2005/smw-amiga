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
from g5plan_verify import block_env as b2_env
from sprgfx_final import derived_path


SPRW = 84


def block_env(blk):
    if blk[10] != 0xb2:
        return b2_env(blk)
    env = {}
    row, = struct.unpack_from('>h', blk, 8)
    for j in range(40):
        off, = struct.unpack_from('>H', blk, 12+2*j)
        if off == 0xffff:
            continue
        mask, count = struct.unpack_from('>Hh', blk, 92+off)
        for k in range(count+1):
            loc, first, last = struct.unpack_from('>HBB', blk, 96+off+4*k)
            idx = loc//2+1
            if not mask>>idx&1:
                raise ValueError('vista dispersa con indice sin presencia')
            env[row+j, idx] = first+blk[11], last+blk[11]
    return env


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
    sources = ['player/' + n + '.c' for n in ('mario', 'mcoll', 'manim', 'mgfx', 'mcam', 'msprite', 'mspr', 'g5plan', 'g5env')]
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
    R = cpu.M.Register
    def exposed():
        if cpu.cpu.r_reg(R.D0) & 0xffff != 1:
            raise ValueError('MA1 no expone clave valida')
        return cpu.read(cpu.cpu.r_reg(R.A0), 18) + cpu.read(cpu.cpu.r_reg(R.A1), 22)
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
                cpu.write(B + syms['_ram'], c['ram'])
                cpu.write(B + syms['_mario_oam'], oam)
                cpu.write(B + syms['_mario_osz'], osz)
                call_args(cpu, B + syms['mspr_draw'], B, BUF)
                if cpu.cpu.r_reg(R.D0) & 0xffff or image(cpu.read(BUF, 672)) != pic:
                    raise ValueError('oculto/C expone clave o DATA distintos: %s %d' % (name, frame))
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
            if exposed() != key:
                raise ValueError('retorno inicial MA1 distinto')
            cpu.write(B + syms['mspr_n'], b'\xa5' * 18)
            call_args(cpu, B + syms['mspr_draw'], B, BUF)
            if exposed() != key or image(cpu.read(BUF, 672)) != pic:
                raise ValueError('retorno L1 lee mspr_n viejo: %s %d' % (name, frame))
            call_args(cpu, B + syms['mspr_draw'], B, BUF + 0x2000)
            if exposed() != key or image(cpu.read(BUF + 0x2000, 672)) != pic:
                raise ValueError('retorno buffer libre distinto: %s %d' % (name, frame))
            checked += 1
        results[name] = dict(frames=len(caps), keys=len(keys), collisions=collisions,
                             asm_checked=checked, l1_poison_checked=checked,
                             free_buffer_checked=checked, no_key_checked=len(caps)-checked, paths=dict(reasons))
        print('B2b-1 %s: %d frames; claves %d; colisiones %d; clave/DATA MA1 real exactos %d; sin clave %d' %
              (name, len(caps), len(keys), len(collisions), checked, len(caps) - checked), flush=True)
    results['global'] = dict(keys=len(global_keys), images=len(images),
                             collisions=sum(len(v['collisions']) for v in results.values()))
    (out / 'key_summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    if results['global']['collisions']:
        raise ValueError('PARADA B2b-1: misma clave, DATA/DATB distintos; ver key_summary.json')
    # Raros que las trazas no contienen: deben invalidar MA1 y exponer
    # bandera cero aun cuando mspr_n/fichas contienen basura anterior.
    c = next(c for c in read_cap(out / 'cap_normal.bin') if any(c['spr'][:4]))
    kd = (out / 'key_normal.bin').read_bytes()
    i = next(i for i in range(len(kd)//24) if struct.unpack_from('>I', kd, i*24)[0] == c['frame'])
    original, sizes = kd[i*24+4:i*24+20], kd[i*24+20:i*24+24]
    for kind in ('vertical', '8x8', 'solape'):
        o, z = bytearray(original), bytearray(sizes)
        if kind == 'vertical': o[3] |= 128
        elif kind == '8x8': z[0] &= ~2
        else: o[5] = o[1]
        cpu.write(B + syms['_ram'], c['ram'])
        cpu.write(B + syms['_mario_oam'], o)
        cpu.write(B + syms['_mario_osz'], z)
        cpu.write(B + syms['mspr_kA'], b'\xa5'*128)
        before = cpu.mem.r16(B + syms['mspr_slow'])
        call_args(cpu, B + syms['mspr_draw'], B, BUF+0x2000)
        if (cpu.cpu.r_reg(R.D0) & 0xffff or cpu.mem.r16(B + syms['mspr_slow']) != (before+1)&0xffff
                or cpu.mem.r16(B+syms['mspr_kA']) or cpu.mem.r16(B+syms['mspr_kB'])):
            raise ValueError('camino C raro no invalida clave: ' + kind)
    print('MA1 retornos: L1 envenenado, buffer libre, oculto y 3 raros C: OK')
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
    if cols == 4:
        if not 0 <= x0 <= 240:
            masks = pixel_masks(spr)
            return {(r0+j, idx): (min(xs), max(xs)) for (j, idx), raw in masks.items()
                    if 0 <= r0+j < 224
                    and (xs := [x0+u for u in range(16) if raw >> (15-u) & 1 and 0 <= x0+u < 256])}
        env, offset = {}, 4
        for j in range(height):
            mask, count = struct.unpack_from('>Hh', data, offset)
            offset += 4
            for _ in range(count + 1):
                loc, bounds = struct.unpack_from('>HH', data, offset)
                offset += 4
                idx = loc // 2 + 1
                if not mask >> idx & 1:
                    raise ValueError('par disperso sin bit de presencia')
                if 0 <= r0+j < 224:
                    env[r0+j, idx] = x0 + (bounds >> 8), x0 + (bounds & 255)
        return env
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


def cache_key(key):
    """La misma clave de 40 B, permutada para MOVEM alineados en la foto."""
    return None if key is None else key[:19] + key[39:40] + key[19:39]


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

    def reset_cache(self, n):
        self.n, self.cache = n, 0x70000
        if n != self.syms['G5ENV_N']:
            raise ValueError('cache del arnes distinta del binario')
        self.cache_size = 2484 + n * self.syms['G5ENV_ENTRY']
        self.cpu.write(self.cache - 4, b'HEAD' + bytes(self.cache_size) + b'TAIL')

    def lookup(self, key, spr):
        cpu, M = self.cpu, self.cpu.M
        inp, kp = 0x60000, 0x50000
        delta = 0x8000 if self.number & 1 else 0
        self.number += 1
        cpu.write(inp - 4, b'HEAD' + spr + b'TAIL')
        cpu.write(kp - 4, b'HEAD' + (key or b'\xcc' * 40) + b'TAIL')
        saved = {getattr(M.Register, r): 0x23456700 + k
                 for k, r in enumerate(('D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'A2', 'A3', 'A4', 'A5', 'A6'))}
        for reg, val in saved.items():
            cpu.cpu.w_reg(reg, val)
        sp = V.STACK - 16
        cpu.cpu.w_reg(M.Register.A7, sp)
        cpu.write(sp, struct.pack('>IIII', V.RET, self.cache, kp if key else 0, inp))
        cpu.cpu.w_pc(V.BASE + delta + self.syms['_g5env_lookup'])
        cycles = cpu.m.execute(1_000_000).cycles - 34
        if cpu.cpu.r_pc() not in (V.RET, V.RET + 2):
            raise ValueError('lookup no regreso')
        if any(cpu.cpu.r_reg(r) != v for r, v in saved.items()) or cpu.cpu.r_reg(M.Register.A7) != sp + 4:
            raise ValueError('lookup rompio ABI')
        ptr, hit = cpu.cpu.r_reg(M.Register.D0), cpu.cpu.r_reg(M.Register.D1)
        if hit not in (0, 1, 2) or not self.cache <= ptr < self.cache + self.cache_size:
            raise ValueError('lookup devolvio entrada invalida')
        height, cols = struct.unpack('>HH', cpu.read(ptr, 4))
        size = 1204 if cols == 4 else 4 + height * (30 if cols == 1 else 62)
        if height > 40 or cols not in (0, 1, 2, 4) or ptr + size > self.cache + self.cache_size:
            raise ValueError('lookup desbordo la entrada')
        if (cpu.read(inp - 4, 680) != b'HEAD' + spr + b'TAIL'
                or cpu.read(kp - 4, 48) != b'HEAD' + (key or b'\xcc' * 40) + b'TAIL'
                or cpu.read(self.cache - 4, 4) != b'HEAD'
                or cpu.read(self.cache + self.cache_size, 4) != b'TAIL'):
            raise ValueError('lookup escribio fuera de cache o cambio entrada')
        self.last_ptr = ptr
        return cycles, cpu.read(ptr, size), hit


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


def project_fixture(out, n):
    """Mismo asm que el juego; tabla matematica y scratch propio, sin assets."""
    from regress import vasm
    src, bp, lp = (out / ('project%d.' % n + ext) for ext in ('s', 'bin', 'lst'))
    words = []
    for b in range(256):
        pos = [i for i in range(8) if b >> (7 - i) & 1]
        words.append((min(pos) << 8 | max(pos)) if pos else 65535)
    src.write_text('SPR_G5 equ 1\nG5ENV_PROJECT equ 1\nG5ENV_N equ %d\nbinstart:\n' % n
                   + '_g5env_bounds:\n' + ''.join(' dc.w $%04x\n' % w for w in words)
                   + ' include "g5env.s"\n_g5env_bind: dc.w $4afc\n'
                   + 'g5env_cache: ds.b 2484\n', encoding='utf-8')
    subprocess.run([vasm(), '-quiet', '-Fbin', '-m68000', '-no-opt', '-Iplayer', '-L', str(lp),
                    '-o', str(bp), str(src)], check=True)
    subprocess.run([sys.executable, 'tools/piccheck.py', '--lst', str(lp)], check=True)
    return bp.read_bytes(), V.symbols(lp)


def project_call(m, ptr, spr):
    """ABI, limites y stack del projector real, alternando sus dos bases."""
    cpu, M = m.cpu, m.cpu.M
    delta = 0x8000 if m.number & 1 else 0
    m.number += 1
    inp, blk = 0x60000, 0xc4000
    cpu.write(inp - 4, b'HEAD' + spr + b'TAIL')
    cpu.write(blk - 4, b'HEAD' + b'\xa5' * 1292 + b'TAIL')
    saved = {getattr(M.Register, r): 0x23456700 + k
             for k, r in enumerate(('D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'A2', 'A3', 'A5', 'A6'))}
    for reg, val in saved.items():
        cpu.cpu.w_reg(reg, val)
    base = V.BASE + delta
    saved[M.Register.A4] = base
    cpu.cpu.w_reg(M.Register.A4, base)
    sp = V.STACK - 20
    cpu.write(sp - 1300, b'\x5a' * 1300)
    cpu.cpu.w_reg(M.Register.A7, sp)
    cpu.write(sp, struct.pack('>IIIII', V.RET, blk, inp, ptr, 1))
    cpu.cpu.w_pc(base + m.syms['_g5env_project'])
    cycles = cpu.m.execute(1_000_000).cycles - 34
    if cpu.cpu.r_pc() not in (V.RET, V.RET + 2):
        raise ValueError('projector no regreso')
    if any(cpu.cpu.r_reg(r) != v for r, v in saved.items()) or cpu.cpu.r_reg(M.Register.A7) != sp + 4:
        raise ValueError('projector rompio ABI')
    if (cpu.read(blk - 4, 4) != b'HEAD' or cpu.read(blk + 1292, 4) != b'TAIL'
            or cpu.read(inp - 4, 680) != b'HEAD' + spr + b'TAIL'
            or cpu.read(sp - 1300, 40) != b'\x5a' * 40):
        raise ValueError('projector escribio fuera de vista/sprite/pila (1260 B)')
    return cycles, cpu.read(blk, 1292), cpu.read(ptr, 1204)



def run_cache(a):
    derived_path(a.out)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    from regress import vasm
    results = {}
    for n in a.sizes:
        if n not in (1, 2, 4, 8, 16, 32):
            raise ValueError('N debe ser potencia de dos entre 1 y 32')
        bp, lp = out / ('env%d.bin' % n), out / ('env%d.lst' % n)
        subprocess.run([vasm(), '-quiet', '-Fbin', '-m68000', '-no-opt', '-DSPR_G5', '-DG5ENV_N=%d' % n,
                        '-L', str(lp), '-o', str(bp), 'player/g5env.s'], check=True)
        subprocess.run([sys.executable, 'tools/piccheck.py', '--lst', str(lp)], check=True)
        m = EnvCPU(*project_fixture(out, n))
        traces = {}
        for name in ('yi1', 'normal', 'spin_kill'):
            m.reset_cache(n)
            kd = Path('work/b2b/key/key_' + name + '.bin').read_bytes()
            hits, misses, aliases, projections, nokey, clipped = [], [], [], [], 0, 0
            profile = collections.defaultdict(list)
            for i, c in enumerate(read_cap('work/g5gate/cap_' + name + '.bin')):
                if struct.unpack_from('>I', kd, 24 * i)[0] != c['frame']:
                    raise ValueError('clave/foto desalineadas')
                key, _ = key_of(kd[24 * i + 4:24 * i + 20], kd[24 * i + 20:24 * i + 24], c['ram'])
                cycles, data, hit = m.lookup(cache_key(key), c['spr'])
                if decode_env(data, c['spr']) != block_env(c['blk']) or (struct.unpack_from('>H', data, 2)[0] != 4 and stored_masks(data) != pixel_masks(c['spr'])):
                    raise ValueError('cache distinta: N%d %s %d' % (n, name, c['frame']))
                if hit == 2:
                    aliases.append((cycles, c['frame']))
                (hits if hit == 1 else misses).append((cycles, c['frame']))
                fmt = struct.unpack_from('>H', data, 2)[0]
                kind = ('no_key' if key is None else
                        'alias' if hit == 2 else 'hit' if hit == 1 else 'decode')
                pcost, view, packed = project_call(m, m.last_ptr, c['spr'])
                profile['%s_fmt%d' % (kind, fmt)].append((pcost, cycles, c['frame']))
                if block_env(view) != block_env(c['blk']):
                    raise ValueError('cache proyectada distinta N%d %s %d' % (n, name, c['frame']))
                projections.append((pcost, c['frame']))
                base = 0 if any(c['spr'][:4]) else 336
                pos, ctl = struct.unpack_from('>HH', c['spr'], base)
                hx = ((pos & 255) * 2 | (ctl & 1)) - 160
                clipped += any(c['spr'][base:base+4]) and not 0 <= hx <= 240
                nokey += key is None
            traces[name] = dict(hit=len(hits), miss=len(misses), no_key=nokey,
                                aliases=len(aliases), clipped=clipped, project_max=max(projections)[0],
                                hit_max=max(hits)[0], miss_max=max(misses)[0],
                                worst_miss=max(misses)[1], mean=sum(x for x, _ in hits + misses) / (len(hits) + len(misses)),
                                profile={kind: dict(count=len(xs),
                                    project_mean=sum(x[0] for x in xs)/len(xs),
                                    lookup_mean=sum(x[1] for x in xs)/len(xs),
                                    project_max=max(xs)[0], worst_frame=max(xs)[2])
                                    for kind, xs in profile.items()})
            print('B2b-3 N%d %s: hit %d, miss %d (sin clave %d); ABI 0, diferencias 0; max hit %d miss %d (frame %d)' %
                  (n, name, len(hits), len(misses), nokey, max(hits)[0], *max(misses)), flush=True)
        results[n] = traces
    (out / 'cache_summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    good = all(t['hit_max'] <= 600 and t['miss_max'] <= 12000 for traces in results.values() for t in traces.values())
    print('PUERTA B2b-3: %s' % ('OK' if good else 'FALTA ciclos'), flush=True)
    return 0 if good else 1


def front_bytes(env):
    out = bytearray(224 * 32)
    for (row, idx), (first, last) in env.items():
        off = row * 32
        mask = struct.unpack_from('>H', out, off)[0] | (1 << idx)
        struct.pack_into('>H', out, off, mask)
        out[off + 2 * idx:off + 2 * idx + 2] = bytes((first, last))
    return bytes(out)


def front_harness(out, m):
    """Callbacks al C real de logicbench, ABI vbcc y direccion relocada."""
    from regress import vasm
    vbcc = os.environ.get('VBCC', 'C:/Users/JC/vbcc')
    compiler = Path(vbcc) / 'bin/vbccm68k.exe'
    # En Git Bash VBCC puede ser /c/...; Python nativo necesita C:/...
    if str(compiler).startswith('/c/'):
        compiler = Path('C:/' + str(compiler)[3:])
    asm, bp, lp = out / 'front.s', out / 'front.bin', out / 'front.lst'
    subprocess.run([str(compiler), '-quiet', '-c99', '-cpu=68000', '-O=991', '-DSPR_G5',
                    '-sc', '-sd', '-Iplayer', '-o=' + str(asm), 'tools/g5env_front.c'], check=True)
    subprocess.run([vasm(), '-quiet', '-Fbin', '-m68000', '-no-opt', '-L', str(lp),
                    '-o', str(bp), str(asm)], check=True)
    subprocess.run([sys.executable, 'tools/piccheck.py', '--lst', str(lp)], check=True)
    where = getattr(m, 'frontcode', 0x90000)
    m.cpu.write(where, bp.read_bytes())
    m.syms['_g5env_front'] = where - getattr(m, 'base', V.BASE) + V.symbols(lp)['_g5env_front']


def run_front(a):
    import ctypes as C
    from g5plan_verify import M68k
    derived_path(a.out)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stub = out / 'globals.c'
    stub.write_text('#include "g5plan.h"\nu8 ram[8192], mario_pal, spr_oam_first[12], spr_oam_n[12];\n')
    dll = out / 'front.dll'
    subprocess.run(['gcc', '-O2', '-shared', '-DSPR_G5', '-DNOOAM', '-DSPR_OAM', '-Iplayer',
                    '-o', str(dll), 'tools/g5env_front.c', 'player/g5plan.c', 'player/g5env.c', str(stub)], check=True)
    lib = C.CDLL(str(dll.resolve()))
    P = C.POINTER(C.c_ubyte)
    lib.g5env_bind.argtypes = [P, P, P]
    lib.g5env_front.argtypes = [P, C.c_void_p, C.c_void_p, P]
    hostout = (C.c_ubyte * (224 * 32))()
    dec = EnvCPU(Path('work/b2b/decode/env.bin').read_bytes(), V.symbols('work/b2b/decode/env.lst'))
    # machine68k comparte el nucleo CPU: no alternar dos Machine vivas.
    records = {name: [(c, dec.decode(c['spr'])[1]) for c in read_cap('work/g5gate/cap_' + name + '.bin')]
               for name in ('yi1', 'normal', 'spin_kill')}
    del dec
    m = M68k(a.bin, a.lst)
    front_harness(out, m)
    DATA, OUTPUT = 0xc2000, 0xc4000
    results = {}
    for name in ('yi1', 'normal', 'spin_kill'):
        count, abi, costs = 0, 0, []
        for c, raw in records[name]:
            blk = (C.c_ubyte * len(c['blk'])).from_buffer_copy(c['blk'])
            spr = (C.c_ubyte * 672).from_buffer_copy(c['spr'])
            data = (C.c_ubyte * len(raw)).from_buffer_copy(raw)
            lib.g5env_bind(blk, spr, data)
            lib.g5env_front(blk, C.cast(lib.g5_mario_mask, C.c_void_p), C.cast(lib.g5_mario_span, C.c_void_p), hostout)
            want = front_bytes(block_env(c['blk']))
            if bytes(hostout) != want:
                raise ValueError('frontera PC distinta: %s %d' % (name, c['frame']))
            m.cpu.write(m.BLK, c['blk'])
            m.cpu.write(m.SPR, c['spr'])
            m.cpu.write(DATA, raw)
            _, _, bad = m.call('_g5env_bind', m.BLK, m.SPR, DATA)
            abi += bad
            m.cpu.write(OUTPUT - 4, b'HEAD' + b'\xa5' * (224 * 32) + b'TAIL')
            cyc, _, bad = m.call('_g5env_front', m.BLK, m.sym('_g5_mario_mask'), m.sym('_g5_mario_span'), OUTPUT)
            abi += bad
            got = m.cpu.read(OUTPUT, 224 * 32)
            if got != want or m.cpu.read(OUTPUT - 4, 4) != b'HEAD' or m.cpu.read(OUTPUT + 224 * 32, 4) != b'TAIL':
                raise ValueError('frontera 68000 distinta/desbordada: %s %d' % (name, c['frame']))
            count += 1
            costs.append((cyc, c['frame']))
        if abi:
            raise ValueError('frontera ABI distinta: %d' % abi)
        results[name] = dict(frames=count, rows=count * 224, abi=abi, max=max(costs)[0], worst_frame=max(costs)[1])
        print('B2b-4 %s: PC = B2 = 68000, %d frames / %d filas, diferencias 0, ABI 0; arnes completo max %d ciclos' %
              (name, count, count * 224, max(costs)[0]), flush=True)
    (out / 'front_summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print('PUERTA B2b-4: OK', flush=True)


def run_project(a):
    from g5plan_verify import M68k
    derived_path(a.out)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    dec = EnvCPU(Path('work/b2b/decode/env.bin').read_bytes(), V.symbols('work/b2b/decode/env.lst'))
    records = {name: [(c, dec.decode(c['spr'])[1]) for c in read_cap('work/g5gate/cap_' + name + '.bin')]
               for name in ('yi1', 'normal', 'spin_kill')}
    del dec
    m = M68k(a.bin, a.lst)
    results = {}
    for name, cases in records.items():
        costs = []
        for c, raw in cases:
            m.cpu.write(m.BLK, c['blk'])
            m.cpu.write(m.SPR, c['spr'])
            m.cpu.write(0xc2000, raw)
            cyc, _, abi = m.call('_g5env_project', m.BLK, m.SPR, 0xc2000)
            got = m.cpu.read(m.BLK, len(c['blk']))
            if abi or block_env(got) != block_env(c['blk']) or got[1292:] != c['blk'][1292:]:
                raise ValueError('proyeccion asm distinta/ABI/Rex: %s %d' % (name, c['frame']))
            costs.append((cyc, c['frame']))
        results[name] = dict(frames=len(costs), max=max(costs)[0], worst_frame=max(costs)[1],
                             mean=sum(c for c, _ in costs) / len(costs))
        print('B2b-4 proyeccion asm %s: %d frames exactos, ABI 0; media %.0f, max %d (frame %d)' %
              (name, len(costs), results[name]['mean'], *max(costs)), flush=True)
    (out / 'project_summary.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print('PUERTA proyeccion B2/B3: OK', flush=True)


def run_game(a):
    """O5 real: COPER captura, render usa esa foto aunque cambie la RAM."""
    import gamecheck as G
    import g2t_ref as T
    derived_path(a.out)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    code, s = Path(a.bin).read_bytes(), V.symbols(a.lst)
    B = G.code_base(len(code))
    cpu = V.MusashiCPU()
    cpu.write(B, code)
    R, mem = cpu.M.Register, cpu.mem
    addr = lambda n: B + s[n]
    for name, value in (('_map16_lo', addr('map16')), ('_map16_hi', addr('map16') + s['MAPHALF']),
                        ('_spr_level', addr('spr_lv')), ('_gfx32', addr('gfx32'))):
        mem.w32(addr(name), value)
    cpu.write(addr('_level_sprites'), b'\1')
    cpu.call(addr('replay_init'), B)
    fr = G.Frames(cpu, B, s, Path('work/yi1_s_g5.dat').read_bytes())
    from types import SimpleNamespace
    front_harness(out, SimpleNamespace(cpu=cpu, syms=s, base=B, frontcode=0xce000))
    first, nframes = mem.r16(addr('replay') + 6), mem.r16(addr('replay') + 4)
    ops_offset = mem.r32(addr('replay') + 12)
    ops = cpu.read(addr('replay') + ops_offset, nframes * 6)[0::6]
    gfx = cpu.read(addr('gfx32'), 23808)
    caps = {c['frame']: c for c in read_cap('work/g5gate/cap_yi1.bin')}
    cpu.call(addr('game_step'), B)
    fr.init_scroll()
    _, _, sprs = G.layout(s)
    for i in range(3):
        mem.w32(addr('g_sbuf') + 4 * i, sprs + i * s['SPRBUF'])
    mem.w32(addr('g_null'), sprs + 3 * s['SPRBUF'])
    cpu.write(sprs + 3 * s['SPRBUF'], bytes(16))
    mem.w32(addr('g_data'), G.DATA)
    fr.call(addr('dc_init'), G.FAKE)
    dc = addr('dc_st')
    copy_costs, render_costs, totals, count, no_key = [], [], [], 0, 0
    profile = []
    frozen_fixture = collections.defaultdict(list)

    def tick():
        markers = {addr('dc_g5copy_start'): 'start', addr('dc_g5copy_end'): 'end'}
        originals = {p: mem.r16(p) for p in markers}
        trap = mem.r16(V.RET)
        for p in markers:
            mem.w16(p, trap)
        for reg, value in ((R.A3, G.DATA), (R.A4, G.FAKE), (R.A5, fr.vars), (R.A7, V.STACK - 4)):
            cpu.cpu.w_reg(reg, value)
        mem.w32(V.STACK - 4, V.RET)
        cpu.cpu.w_pc(addr('dc_cop'))
        elapsed, times = 0, {}
        while True:
            elapsed += cpu.m.execute(1_000_000).cycles - 34
            pc = cpu.cpu.r_pc() - 2
            if pc == V.RET:
                break
            if pc not in markers:
                raise ValueError('COPER no regreso a un marcador conocido')
            times[markers[pc]] = elapsed
            mem.w16(pc, originals[pc])
            cpu.cpu.w_pc(pc)
        for p, word in originals.items():
            mem.w16(p, word)
        if times:
            # 12 preservando fuentes, 20 exponiendo la clave fast en mspr_draw,
            # hasta 8 por los MULU DC_REC que ya existian: cota conservadora.
            copy_costs.append(times['end'] - times['start'] + 40)
        return elapsed

    for k in range(nframes):
        logical = tick() if k else 0
        photo = mem.r16(dc + s['DC_NEW'])
        rec = addr('dc_rec') + photo * s['DC_REC']
        stamp = mem.r16(rec + s['R_FRAME'])
        if stamp != k:
            raise ValueError('mapeo foto/oraculo distinto: k%d foto%d' % (k, stamp))
        f = first + stamp
        mem.w16(dc + s['DC_REND'], photo)
        mem.w16(fr.vars + s['V_S'], mem.r16(rec + s['R_S']))
        costs = [sum(fr.call(addr(n), G.FAKE).values()) for n in ('columns', 'apply_colors', 'set_pointers', 'build_mid')]
        # Estado vivo envenenado tras capturar: el render debe ignorarlo.
        ram = cpu.read(addr('_ram'), 8192)
        oam = cpu.read(addr('_mario_oam'), 16)
        osz = cpu.read(addr('_mario_osz'), 4)
        fichas = cpu.read(addr('mspr_kA'), 128)
        cpu.write(addr('_ram'), b'\xa5' * 8192)
        cpu.write(addr('_mario_oam'), b'\xa5' * 16)
        cpu.write(addr('_mario_osz'), b'\xa5' * 4)
        cpu.write(addr('mspr_kA'), b'\xa5' * 128)
        parts = fr.call(addr('dc_g5render'), G.FAKE, regions={addr('_g5env_lookup'): 'lookup', addr('_g5env_project'): 'project'})
        render = sum(parts.values())
        photo_key = (cpu.read(rec+s['R_G5KEY'], 40).hex()
                     if mem.r16(rec+s['R_G5HAS']) else None)
        cpu.write(addr('_ram'), ram)
        cpu.write(addr('_mario_oam'), oam)
        cpu.write(addr('_mario_osz'), osz)
        cpu.write(addr('mspr_kA'), fichas)
        if f in caps:
            c = caps[f]
            view = cpu.read(addr('g5env_view'), 1292)
            recorded = [(*oam[4 * j:4 * j + 4], osz[j]) for j in range(4)]
            pixels, _ = T.mario_amiga(ram, recorded, gfx)
            expected = {}
            for (x, row), idx in pixels.items():
                key = row, idx
                lo, hi = expected.get(key, (x, x))
                expected[key] = min(lo, x), max(hi, x)
            if block_env(view) != expected:
                raise ValueError('B2 en juego distinto: foto %d -> oraculo %d' % (stamp, f))
            cpu.write(V.STACK, struct.pack('>IIII', addr('g5env_view'), addr('_g5_mario_mask'),
                                         addr('_g5_mario_span'), 0xc8000))
            G.call_args(cpu, addr('_g5env_front'), B)
            if cpu.read(0xc8000, 224*32) != front_bytes(expected):
                raise ValueError('frontera real en foto distinta: %d' % f)
            if expected != block_env(c['blk']):
                if ops[k] == V.REP_RUN:
                    raise ValueError('foto RUN/SYNC distinta del volcado B2: %d (op %d)' % (f, ops[k]))
                # marioverify g2t_frame emite ANTES de deshacer un SKIP;
                # game.s deja la imagen anterior. No cambiar el juego ni el
                # modelo para hacer coincidir ese fixture provisional.
                frozen_fixture["SKIP" if ops[k] == V.REP_SKIP else "SYNC"].append(f)
            count += 1
            no_key += mem.r16(rec + s['R_G5HAS']) == 0
            render_costs.append((render, f))
        cpu.cpu.w_reg(R.D7, photo)
        costs.append(sum(fr.call(addr('dc_hdr'), G.FAKE).values()))
        mem.w16(dc + s['DC_FRONT'], photo)
        mem.w16(dc + s['DC_REND'], 0xffff)
        back = mem.r32(fr.vars + s['V_BACK'])
        other = mem.r32(fr.vars + (s['V_COP2'] if back == mem.r32(fr.vars + s['V_COP']) else s['V_COP']))
        mem.w32(fr.vars + s['V_BACK'], other)
        total = logical + sum(costs) + render
        totals.append((total, f))
        profile.append(dict(frame=f, key=photo_key, lookup=parts.get('lookup', 0),
                            project=parts.get('project', 0), render=render,
                            base=total-render, total=total))
    if count != len(caps):
        raise ValueError('faltan fotos con Rex: %d/%d' % (count, len(caps)))
    # Escenario separado del replay medido: el render retiene una foto
    # mientras COPER avanza y tiene que usar el tercer buffer.
    cpu.call(addr('replay_init'), B)
    cpu.call(addr('game_step'), B)
    fr.init_scroll()
    fr.call(addr('dc_init'), G.FAKE)
    for _ in range(20):
        tick()
    old = mem.r16(dc + s['DC_NEW'])
    oldrec = addr('dc_rec') + old*s['DC_REC']
    oldbuf = mem.r32(addr('g_sbuf') + 4*old)
    record, data = cpu.read(oldrec, s['DC_REC']), cpu.read(oldbuf, 672)
    ram, oam, osz = cpu.read(addr('_ram'), 8192), cpu.read(addr('_mario_oam'), 16), cpu.read(addr('_mario_osz'), 4)
    pixels, _ = T.mario_amiga(ram, [(*oam[4*j:4*j+4], osz[j]) for j in range(4)], gfx)
    wanted = {}
    for (x, row), idx in pixels.items():
        lo, hi = wanted.get((row, idx), (x, x))
        wanted[row, idx] = min(lo, x), max(hi, x)
    if not wanted or old not in (0, 1):
        raise ValueError('fixture tardio no tiene Mario visible en buffer MA1')
    mem.w16(dc + s['DC_FRONT'], 1-old)
    mem.w16(dc + s['DC_REND'], old)
    mem.w16(dc + s['DC_PEND'], 0xffff)
    tick()
    if (mem.r16(dc + s['DC_NEW']) != 2 or cpu.read(oldrec, s['DC_REC']) != record
            or cpu.read(oldbuf, 672) != data):
        raise ValueError('COPER tardio no usa buffer 2 o reescribe foto retenida')
    newrec = addr('dc_rec') + 2*s['DC_REC']
    if mem.r16(newrec + s['R_G5HAS']) != 1:
        raise ValueError('buffer 2 no captura la clave actual')
    cpu.write(addr('_ram'), b'\xa5'*8192)
    cpu.write(addr('_mario_oam'), b'\xa5'*16)
    cpu.write(addr('_mario_osz'), b'\xa5'*4)
    cpu.write(addr('mspr_kA'), b'\xa5'*128)
    fr.call(addr('dc_g5render'), G.FAKE)
    if block_env(cpu.read(addr('g5env_view'), 1292)) != wanted:
        raise ValueError('render tardio lee foto nueva/RAM viva')
    extra = max(copy_costs)
    summary = dict(first=first, frames=nframes, rex_photos=count, diff=0, no_key=no_key,
                   live_ram_poisoned=nframes, capture_extra_max=extra,
                   retained_photo_buffer2=True,
                   render_max=max(render_costs)[0], worst_render=max(render_costs)[1],
                   total_max=max(totals)[0], worst_total=max(totals)[1],
                   over_pal=sum(c > G.PAL_FRAME for c, _ in totals), skip_fixture=frozen_fixture)
    (out / 'game_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    (out / 'game_profile.json').write_text(json.dumps(profile, indent=2), encoding='utf-8')
    print('B2b-5 mapeo: primer frame %d + R_FRAME; foto 5219 -> 10364 comprobada' % first)
    print('B2b-5 juego: %d fotos Rex exactas, sin clave %d; %d renders con RAM/OAM/fichas vivas envenenadas' %
          (count, no_key, nframes))
    print('B2b-5 fixture PC provisional: %d SKIP + %d SYNC; foto congelada exacta contra g2t_ref' %
          (len(frozen_fixture['SKIP']), len(frozen_fixture['SYNC'])))
    print('B2b-5 captura nueva: max %d ciclos (incluye exposicion/preservacion/MULU), objetivo <=300' % extra)
    print('B2b-5 O5 sin DMA: max render B2bis %d (frame %d); total CPU %d (frame %d), >PAL %d' %
          (*max(render_costs), *max(totals), summary['over_pal']))
    if extra > 300 or summary['over_pal']:
        raise ValueError('captura supera 300 ciclos o hay frames O5 por encima de PAL')
    print('PUERTA B2 en el juego: OK', flush=True)
    print('Foto retenida: COPER usa buffer 2, foto/DATA anteriores intactos y render exacto')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    k = sub.add_parser('key')
    k.add_argument('--out', default='work/b2b/key')
    k.add_argument('--bin', default='work/b35_mem_replay/game.bin')
    k.add_argument('--lst', default='work/b35_mem_replay/game.lst')
    d = sub.add_parser('decode')
    d.add_argument('--out', default='work/b2b/decode')
    c = sub.add_parser('cache')
    c.add_argument('--out', default='work/b2b/cache')
    c.add_argument('--sizes', nargs='+', type=int, default=[4, 8, 16, 32])
    f = sub.add_parser('front')
    f.add_argument('--out', default='work/b2b/front')
    f.add_argument('--bin', default='work/b2b/logicbench.bin')
    f.add_argument('--lst', default='work/b2b/logicbench.lst')
    p = sub.add_parser('project')
    p.add_argument('--out', default='work/b2b/project')
    p.add_argument('--bin', default='work/b2b_r/game.bin')
    p.add_argument('--lst', default='work/b2b_r/game.lst')
    g = sub.add_parser('game')
    g.add_argument('--out', default='work/b2b/game')
    g.add_argument('--bin', default='work/b2b_r/game.bin')
    g.add_argument('--lst', default='work/b2b_r/game.lst')
    a = ap.parse_args()
    return {'key': run_key, 'decode': run_decode, 'cache': run_cache, 'front': run_front,
            'project': run_project, 'game': run_game}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())
