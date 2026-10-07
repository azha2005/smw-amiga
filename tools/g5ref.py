#!/usr/bin/env python3
"""G5a-bis: puerta offline, sin alterar el banco ni las reglas del plan.

La puerta A2 precede al plan: una diferencia conserva toda la evidencia y
detiene A3-A7. Los derivados se escriben exclusivamente dentro de work/.
"""
import argparse
import collections
import json
import os
import struct
import sys
from pathlib import Path

import mksprgfx as G
import mkmario
import sprgfx_bank as B
from g0bench import control, rgb
from smw2amiga import decode_snes_tile
from sprgfx_final import derived_path, require, compose
from sprgfx_manifest import mario_rows, signed


def read_trace(path, oracle):
    """Lectura copiada de sprgfx_manifest.read_trace; devuelve cada despacho.

    Conserva sus comprobaciones SOT1 y la pertenencia exacta contra SNES.
    """
    recordings = {f: [o[i:i + 5] for i in range(0, len(o), 5)]
                  for f, o, _ in G.load_oam_bin(oracle)}
    with open(path, 'rb') as handle:
        require(handle.read(4) == b'SOT1', 'traza desconocida')
        mlen, = struct.unpack('<I', handle.read(4))
        require(0 < mlen <= 0x8000, 'mapa fuera de rango')
        while True:
            header = handle.read(8)
            if not header:
                break
            require(len(header) == 8, 'traza truncada')
            frame, slot, num, first, n = struct.unpack('<IBBBB', header)
            body = handle.read(2 * (0x2000 + mlen))
            require(len(body) == 2 * (0x2000 + mlen) and slot < 12 and n > 0,
                    'registro SOT1 inválido')
            ram = body[0x2000 + mlen:0x4000 + mlen]
            visible = []
            require(first % 4 == 0 and 64 + first // 4 + n <= 128, 'rango OAM inválido')
            for c in range(n):
                s = 64 + first // 4 + c
                entry = ram[0x200 + 4 * s:0x204 + 4 * s] + ram[0x420 + s:0x421 + s]
                if entry[1] != 0xf0:
                    visible.append(entry)
            if not visible:
                continue
            require(frame in recordings, 'frame ausente del oráculo')
            recorded = recordings[frame]
            require(any(recorded[k:k + len(visible)] == visible
                        for k in range(len(recorded) - len(visible) + 1)),
                    'OAM distinta de SNES: %s frame=%d slot=%d sprite=%02x' % (path, frame, slot, num))
            sx = ((ram[0xe4 + slot] | ram[0x14e0 + slot] << 8)
                  - (ram[0x1a] | ram[0x1b] << 8))
            sy = ((ram[0xd8 + slot] | ram[0x14d4 + slot] << 8)
                  - (ram[0x1c] | ram[0x1d] << 8))
            tiles, priorities = [], set()
            for entry in visible:
                x, y, tile, attr, hi = entry
                tiles.append([signed(x - sx), signed(y - sy), tile | (attr & 1) << 8,
                              16 if hi & 2 else 8, attr >> 6 & 1, attr >> 7, attr >> 1 & 7])
                priorities.add(attr >> 4 & 3)
            require(len(priorities) == 1, 'pose con prioridades mixtas: requiere descriptor por ficha')
            yield dict(frame=frame, slot=slot, num=num, sx=sx, sy=sy,
                       tiles=tiles, priority=priorities.pop(), ram=ram, recorded=recorded)


def mask_table(gfx):
    """744 fichas x 8 filas; conserva los índices originales de GFX32."""
    require(len(gfx) == 744 * 32, 'regenerar mkmario.py: GFX32 distinto')
    return [[sum(1 << k for k in set(row) if k)
             for row in decode_snes_tile(gfx[p:p + 32], 4)]
            for p in range(0, len(gfx), 32)]


def dynamic_tiles(ram, gfxlen):
    """Mismos nombres VRAM y punteros que mario_rows; valores = ficha GFX32."""
    dynamic = {}
    for r in range(2):
        for i in range(5):
            off = 0xd85 + 10 * r + 2 * i
            ptr = (ram[off] | ram[off + 1] << 8) - 0x2000
            if 0 <= ptr <= gfxlen - 64:
                require(ptr % 32 == 0, 'puntero GFX32 no alineado')
                for half in range(2):
                    dynamic[16 * r + 2 * i + half] = ptr // 32 + half
    ptr = (ram[0xd99] | ram[0xd9a] << 8) - 0x2000
    if 0 <= ptr <= gfxlen - 32:
        require(ptr % 32 == 0, 'puntero GFX32 no alineado')
        dynamic[0x7f] = ptr // 32
    return dynamic


def table_rows(ram, recorded, table):
    """OR de fichas por fila según A2; no aproxima la reserva de verdad.

    El volteo horizontal no cambia el conjunto. La puerta detecta si el
    recorte u oclusión de la OAM hace insuficiente esta representación.
    """
    dynamic = dynamic_tiles(ram, len(table) * 32)
    rows = [0] * 224
    for x, y, tile, attr, hi in recorded:
        if (attr >> 1) & 7 or attr & 1 or tile not in dynamic or y == 0xf0:
            continue
        ey = y - 256 if y >= 0xf0 else y
        size = 16 if hi & 2 else 8
        for dy in range(size):
            sy = size - 1 - dy if attr & 0x80 else dy
            if not 0 <= ey + dy < 224:
                continue
            for half in range(size // 8):
                t = tile + half + 16 * (sy // 8)
                require(t in dynamic, 'ficha dinámica Mario desconocida %02x' % t)
                rows[ey + dy] |= table[dynamic[t]][sy & 7]
    return rows


def validate_masks(records, gfx, table):
    """Comprueba cada registro, incluidos frames sin Rex; lista fallos exactos."""
    cases, frames, rexframes = [], set(), set()
    for rec in records:
        frame, slot = rec['frame'], rec['slot']
        frames.add(frame)
        if rec['num'] == 0xab:
            rexframes.add(frame)
        truth = mario_rows(rec['ram'], rec['recorded'], gfx)
        actual = table_rows(rec['ram'], rec['recorded'], table)
        for y in range(224):
            expected = sum(1 << k for k in truth[y])
            if expected != actual[y]:
                cases.append(dict(frame=frame, slot=slot, linea=y,
                                  verdad=expected, tabla=actual[y]))
    return dict(frames=len(frames), frames_con_rex=len(rexframes),
                registros=len(records), diferencias_a2=len(cases), casos_a2=cases,
                frames_a2=sorted({c['frame'] for c in cases}))


def first_compatible(variants, poses, sy, masks, colors):
    """A3: primera variante del directorio; el plazo NO cambia la elección."""
    for n in variants:
        pose = poses[n]
        y0 = sy + pose['origin'][1]
        if all(not (masks[y0 + r] & (1 << d)) or colors[d] == color
               for r, row in enumerate(pose['row_maps']) if 0 <= y0 + r < 224
               for _, _, d, color in row):
            return n
    return None


def palette_index(ram, pointers):
    pointer = ram[0xd82] | ram[0xd83] << 8
    require(pointer in pointers, 'wm_PlayerPalPtr desconocido %04x' % pointer)
    return pointers.index(pointer)


def color_writes(desired, colors):
    """A5: ventana desde el último uso no libre, sin mover un uso anterior."""
    regs, last = list(colors), [-1] * 16
    writes = []
    for y, row in enumerate(desired):
        for i, value in sorted(row.items()):
            if value != regs[i]:
                writes.append(dict(tipo='color', indice=i, valor=value,
                                   lo=last[i] + 1, hi=y - 1, destino=y))
                regs[i] = value
            last[i] = y
    return writes


def place_writes(colors, arm, capacity=8):
    """Última línea disponible; armado en orden PT -> POS/CTL.

    Para el armado se colocan sus MOVE desde el último al primero y se
    anteponen en cada línea, conservando el orden real de ejecución.
    """
    lines, missed = [[] for _ in range(224)], []
    armhi = arm[-1]['hi'] if arm else 223
    for move in reversed(arm):
        for y in range(min(move['hi'], armhi, 223), max(move['lo'], 0) - 1, -1):
            if len(lines[y]) < capacity:
                move['linea'] = y
                lines[y].insert(0, move)
                armhi = y
                break
        else:
            missed.append(move)
    for move in colors:
        for y in range(min(move['hi'], 223), max(move['lo'], 0) - 1, -1):
            if len(lines[y]) < capacity:
                move['linea'] = y
                lines[y].append(move)
                break
        else:
            missed.append(move)
    return lines, missed


def simulate(lines, colors):
    regs, states = list(colors), []
    for line in lines:
        states.append(list(regs))
        for move in line:
            if move['tipo'] == 'color':
                regs[move['indice']] = move['valor']
    return states


def mario_pixels(ram, recorded, gfx):
    """Mismos píxeles y selección que mario_rows, con índice OAM para A6."""
    dyn = dynamic_tiles(ram, len(gfx))
    tiles = {k: decode_snes_tile(gfx[32 * n:32 * n + 32], 4) for k, n in dyn.items()}
    pixels = {}
    for order, (x, y, tile, attr, hi) in enumerate(recorded):
        if (attr >> 1) & 7 or attr & 1 or tile not in tiles or y == 0xf0:
            continue
        ex = x | (hi & 1) << 8
        ex = ex - 512 if ex >= 256 else ex
        ey = y - 256 if y >= 0xf0 else y
        size = 16 if hi & 2 else 8
        for dy in range(size):
            for dx in range(size):
                sx = size - 1 - dx if attr & 0x40 else dx
                sy = size - 1 - dy if attr & 0x80 else dy
                t = tile + sx // 8 + 16 * (sy // 8)
                require(t in tiles, 'ficha dinámica desconocida')
                val = tiles[t][sy & 7][sx & 7]
                if val and 0 <= ex + dx < 256 and 0 <= ey + dy < 224:
                    pixels.setdefault((ex + dx, ey + dy), (val, order))
    return pixels


def plan_frame(records, poses, directory, tables, pointers, pals, gfx, masks_table, vram):
    rex = [r for r in records if r['num'] == 0xab]
    require(bool(rex), 'frame sin Rex')
    chosen = min(rex, key=lambda r: (r['sy'] + poses[directory[B.shape(r)][0]]['origin'][1], r['slot']))
    ram, recorded = chosen['ram'], chosen['recorded']
    masks = table_rows(ram, recorded, masks_table)
    pi = palette_index(ram, pointers)
    colors = struct.unpack_from('>16H', pals, 32 * pi)
    n = first_compatible(directory[B.shape(chosen)], poses, chosen['sy'], masks, colors)
    result = dict(frame=chosen['frame'], rex=dict(slot=chosen['slot'], sx=chosen['sx'], sy=chosen['sy'],
                  tiles=chosen['tiles'], priority=chosen['priority']), variante=n, paleta_mario=pi,
                  contadores=dict(sin_destino=len(rex) - 1, sin_variante=int(n is None),
                                  sin_plazo=0, errores_color=0, prioridad_distinta=0),
                  canales=[], escrituras=[], lineas=[[] for _ in range(224)])
    pixels = mario_pixels(ram, recorded, gfx)
    evidence = dict(mario=pixels, colores=colors, rex={}, estados=[colors] * 224)
    if n is None:
        return result, evidence
    pose = poses[n]
    x0, y0 = chosen['sx'] + pose['origin'][0], chosen['sy'] + pose['origin'][1]
    cols = (pose['width'] + 15) // 16
    require(cols in (1, 2), 'Rex excede dos columnas')
    co, = struct.unpack_from('>I', tables, 24 + n * 32 + 16)
    arm = []
    for c in range(cols):
        offsets = struct.unpack_from('>II', tables, co + 8 * c)
        for half in range(2):
            channel = 4 + 2 * c + half
            pos, ctl = control(x0 + 16 * c, 44 + y0, 44 + y0 + pose['height'], channel)
            result['canales'].append(dict(canal=channel, pos=pos, ctl=ctl, pt_relativo=offsets[half] + 4))
    # A5 pide 8 MOVE PT y 8 POS/CTL incluso para la pose de una columna:
    # las parejas restantes se arman inactivas, sin apuntar fuera del banco.
    for channel in range(4, 8):
        actual = next((c for c in result['canales'] if c['canal'] == channel), None)
        for part in ('alto', 'bajo'):
            arm.append(dict(tipo='pt', canal=channel, parte=part,
                            pt_relativo=actual['pt_relativo'] if actual else None, lo=0, hi=y0 - 1))
    for channel in range(4, 8):
        actual = next((c for c in result['canales'] if c['canal'] == channel), None)
        for part in ('pos', 'ctl'):
            arm.append(dict(tipo=part, canal=channel, valor=actual[part] if actual else 0, lo=0, hi=y0 - 1))
    desired = [{i: colors[i] for i in range(1, 16) if masks[y] & 1 << i} for y in range(224)]
    for r, row in enumerate(pose['row_maps']):
        if 0 <= y0 + r < 224:
            for _, _, i, color in row:
                require(i not in desired[y0 + r] or desired[y0 + r][i] == color, 'A3 incompatible')
                desired[y0 + r][i] = color
    writes = color_writes(desired, colors)
    lines, missed = place_writes(writes, arm)
    result['escrituras'] = arm + writes
    result['lineas'] = lines
    result['sin_plazo_detalle'] = missed
    result['contadores']['sin_plazo'] = len(missed)
    states = simulate(lines, colors)
    evidence['estados'] = states
    for (x, y), (i, _) in pixels.items():
        result['contadores']['errores_color'] += states[y][i] != colors[i]
    # Reconstrucción independiente desde las fichas SNES, además del DMA.
    ox, oy, truth = compose(vram, chosen['tiles'], independent=True)
    require([ox, oy] == pose['origin'] and len(truth) == pose['height'], 'origen de fuente distinto')
    for r, row in enumerate(pose['rows']):
        mapping = {(p, i): (d, color) for p, i, d, color in pose['row_maps'][r]}
        for x, d in enumerate(row):
            source = truth[r][x]
            require((source is None) == (d == 0), 'transparencia DMA distinta')
            if not d:
                continue
            di, color = mapping[source]
            require(di == d, 'índice DMA distinto de fuente')
            xx, yy = x0 + x, y0 + r
            if 0 <= xx < 256 and 0 <= yy < 224:
                evidence['rex'][xx, yy] = (d, color)
                result['contadores']['errores_color'] += states[yy][d] != color
    # Primera entrada opaca de OAM gana. Encontrar índice del tramo Rex.
    rex_entries = []
    for entry in recorded:
        x, y, t, attr, hi = entry
        if [signed(x - chosen['sx']), signed(y - chosen['sy']), t | (attr & 1) << 8,
            16 if hi & 2 else 8, attr >> 6 & 1, attr >> 7, attr >> 1 & 7] in chosen['tiles']:
            rex_entries.append(entry)
    start = next(k for k in range(len(recorded)) if recorded[k:k + len(rex_entries)] == rex_entries)
    for (x, y), (_, order) in pixels.items():
        if (x, y) in evidence['rex'] and start < order:
            # Comprobar la primera ficha opaca del Rex, no solo el tramo.
            for j, (dx, dy, tile, size, fx, fy, pal) in enumerate(chosen['tiles']):
                lx, ly = x - chosen['sx'] - dx, y - chosen['sy'] - dy
                if 0 <= lx < size and 0 <= ly < size and G.ref_pixel(vram, tile, size, fx, fy, lx, ly):
                    result['contadores']['prioridad_distinta'] += start + j < order
                    break
    return result, evidence


def evidence_png(samples, path):
    """Referencia SNES de Mario/Rex arriba y simulación de registros abajo."""
    from PIL import Image, ImageDraw
    sheet = Image.new('RGB', (4 * 256, 3 * 470), (32, 32, 32))
    draw = ImageDraw.Draw(sheet)
    for k, (name, plan, ev) in enumerate(samples):
        reference, actual = Image.new('RGB', (256, 224)), Image.new('RGB', (256, 224))
        for (x, y), (d, color) in ev['rex'].items():
            reference.putpixel((x, y), rgb(color))
            actual.putpixel((x, y), rgb(ev['estados'][y][d]))
        for (x, y), (i, _) in ev['mario'].items():
            reference.putpixel((x, y), rgb(ev['colores'][i]))
            actual.putpixel((x, y), rgb(ev['estados'][y][i]))
        bx, by = k % 4 * 256, k // 4 * 470
        draw.text((bx + 2, by + 2), '%s f%d SNES / plan' % (name, plan['frame']), fill='white')
        sheet.paste(reference, (bx, by + 20))
        sheet.paste(actual, (bx, by + 245))
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--trace', action='append', required=True, help='SOT1=oracle_oam.bin')
    ap.add_argument('--bank', required=True)
    ap.add_argument('--rom', default=mkmario.ROM)
    ap.add_argument('--src', default=G._DEF_SRC)
    ap.add_argument('--out', default=os.path.join(G.WORK, 'g5ref'))
    args = ap.parse_args()
    derived_path(args.out)
    for suffix in ('.idx', '.dma'):
        require(os.path.isfile(args.bank + suffix), 'falta banco ' + suffix)
    gfxpath = os.path.join(G.WORK, 'cc', 'gfx32.bin')
    palpath = os.path.join(G.WORK, 'cc', 'mario_pal.bin')
    require(os.path.isfile(gfxpath) and os.path.isfile(palpath), 'faltan derivados de Mario')
    gfx = open(gfxpath, 'rb').read()
    require(len(open(palpath, 'rb').read()) == 256, 'paletas incompletas')
    table = mask_table(gfx)
    os.makedirs(args.out, exist_ok=True)
    summary = dict(fase='A2', trazas={}, puerta_a2=True,
                   fases_no_ejecutadas=['A3-A7', 'B', 'C'])
    traces = {}
    for pair in args.trace:
        path, oracle = pair.split('=', 1)
        name = os.path.splitext(os.path.basename(path))[0].removeprefix('oam_')
        require(name not in summary['trazas'], 'nombre de traza repetido')
        records = list(read_trace(path, oracle))
        traces[name] = records
        result = validate_masks(records, gfx, table)
        summary['trazas'][name] = result
        summary['puerta_a2'] &= result['diferencias_a2'] == 0
        print('%s: registros=%d frames=%d frames_con_rex=%d diferencias_A2=%d' %
              (name, result['registros'], result['frames'], result['frames_con_rex'], result['diferencias_a2']))
        for case in result['casos_a2'][:20]:
            print('  A2 frame={frame} slot={slot} linea={linea} verdad={verdad:04x} tabla={tabla:04x}'.format(**case))
        print('  frames_A2=' + ','.join(map(str, result['frames_a2'])))
    with open(os.path.join(args.out, 'resumen.json'), 'w', encoding='utf-8') as handle:
        json.dump(summary, handle, indent=2)
    if not summary['puerta_a2']:
        print('PUERTA A2: FALLA. PARADA: no ejecutar A3-A7, B ni C.')
        return 1
    print('PUERTA A2: OK')
    tables = Path(args.bank + '.idx').read_bytes()
    poses, index = B.deserialize_bank(tables, Path(args.bank + '.dma').read_bytes())
    directory = {}
    count, = struct.unpack_from('>H', index, 6)
    for j in range(count):
        _, _, _, nv, ptr = struct.unpack_from('>IBBHI', index, 8 + 12 * j)
        variants = list(struct.unpack_from('>%dH' % nv, index, ptr))
        directory[B.shape(poses[variants[0]])] = variants
    rom = Path(args.rom).read_bytes()
    header = len(rom) % 1024
    pointers = [struct.unpack_from('<H', rom, header + ((mkmario.DATA_00E2A2 + 2 * a) & 0x7fff))[0]
                for a in range(8)]
    pals = Path(palpath).read_bytes()
    vram, _, _ = G.build_vram(args.src, G.LEVEL)
    summary.update(fase='A', fases_no_ejecutadas=['B', 'C'], puerta_a=True)
    samples = []
    for name, records in traces.items():
        frames = collections.defaultdict(list)
        for rec in records:
            frames[rec['frame']].append(rec)
        rex_frames = sorted(f for f, rs in frames.items() if any(r['num'] == 0xab for r in rs))
        take = {rex_frames[round(j * (len(rex_frames) - 1) / 3)] for j in range(4)}
        plans, total = [], collections.Counter()
        maxmoves = maxwrites = 0
        bad_variant, bad_deadline, bad_color = [], [], []
        for frame in rex_frames:
            plan, ev = plan_frame(frames[frame], poses, directory, tables, pointers, pals, gfx, table, vram)
            plans.append(plan)
            total.update(plan['contadores'])
            maxmoves = max(maxmoves, max(map(len, plan['lineas'])))
            maxwrites = max(maxwrites, len(plan['escrituras']))
            for counter, target in (('sin_variante', bad_variant), ('sin_plazo', bad_deadline), ('errores_color', bad_color)):
                if plan['contadores'][counter]:
                    target.append(frame)
            if frame in take:
                samples.append((name, plan, ev))
        with open(os.path.join(args.out, 'plan_' + name + '.json'), 'w', encoding='utf-8') as handle:
            json.dump(plans, handle, separators=(',', ':'))
        result = summary['trazas'][name]
        result.update(contadores=dict(total), max_move_linea=maxmoves, max_escrituras_frame=maxwrites,
                      frames_sin_variante=bad_variant, frames_sin_plazo=bad_deadline, frames_errores_color=bad_color)
        summary['puerta_a'] &= bool(rex_frames) and not (bad_variant or bad_deadline or bad_color)
        print('%s: %s max_MOVE_linea=%d max_escrituras_frame=%d' % (name, dict(total), maxmoves, maxwrites))
        for label, bad in (('sin_variante', bad_variant), ('sin_plazo', bad_deadline), ('errores_color', bad_color)):
            print('  frames_%s=%s' % (label, ','.join(map(str, bad))))
    evidence_png(samples, os.path.join(args.out, 'muestra.png'))
    with open(os.path.join(args.out, 'resumen.json'), 'w', encoding='utf-8') as handle:
        json.dump(summary, handle, indent=2)
    print('PUERTA A: ' + ('OK' if summary['puerta_a'] else 'FALLA. PARADA: no ejecutar B ni C.'))
    return 0 if summary['puerta_a'] else 1


if __name__ == '__main__':
    sys.exit(main())
