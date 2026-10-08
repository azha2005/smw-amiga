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
from pathlib import Path
import struct
import subprocess
import sys

import m68kverify as V
from g5plan_verify import read_cap
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    k = sub.add_parser('key')
    k.add_argument('--out', default='work/b2b/key')
    k.add_argument('--bin', default='work/b35_mem_replay/game.bin')
    k.add_argument('--lst', default='work/b35_mem_replay/game.lst')
    a = ap.parse_args()
    run_key(a)


if __name__ == '__main__':
    main()
