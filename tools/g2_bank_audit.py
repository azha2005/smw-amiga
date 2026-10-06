#!/usr/bin/env python3
"""G2: prueba offline de DMA inmutable; no es el conversor final G3.

Reconstruye el lote desde manifiestos SOT1, verifica cada petición con Mario,
compara la alternativa de una imagen por pose y mide una representación directa.
Los archivos SG2A son evidencia descartable, no assets del juego.
"""
import argparse
import collections
import hashlib
import json
import os
import struct

import lvdesc
import memmap as M
import mksprgfx as G
import sprgfx_final as F
import sprgfx_manifest as S
from palette import snes_to_amiga12


def shape(spec):
    return tuple(map(tuple, spec['tiles'])), spec['priority']


def compact(blobs):
    """Comparte subcadenas completas y solapa bytes exactos, siempre a 8 B.

    No se modifica ningún control, terminador ni fila. Orden independiente
    de hashes/diccionarios para que el tamaño sea reproducible.
    """
    out, offsets = bytearray(), {}
    for blob in sorted(set(blobs), key=lambda b: (-len(b), b)):
        haystack = bytes(out)
        at = haystack.find(blob)
        while at >= 0 and at % 8:
            at = haystack.find(blob, at + 1)
        if at < 0:
            overlap = 0
            for n in range(min(len(blob), len(out)), 0, -1):
                if (len(out) - n) % 8 == 0 and out[-n:] == blob[:n]:
                    overlap = n
                    break
            if overlap:
                at = len(out) - overlap
                out.extend(blob[overlap:])
            else:
                out.extend(bytes((-len(out)) % 8))
                at = len(out)
                out.extend(blob)
        offsets[blob] = at
    F.require(all(at % 8 == 0 and out[at:at + len(b)] == b
                  for b, at in offsets.items()), 'solape altera un flujo')
    return bytes(out), offsets


def decode(metadata, chip, limit=65536):
    """Lector independiente del prototipo SG2A: descriptor 32 B sin bob.

    Conserva layout de tablas SG3F/1; $FFFFFFFF marca fuentes bob ausentes.
    No es aceptado por el loader SG3F/1 ni por --final.
    """
    F.require(len(metadata) >= 24, 'cabecera truncada')
    magic, version, ds, count, start, bs, ms = struct.unpack_from(F.HEADER, metadata)
    F.require((magic, version, ds, start) == (b'SG2A', 2, 32, 24), 'formato desconocido')
    F.require(bs == len(chip) <= limit and ms == len(metadata)
              and start + count * ds <= ms, 'tamaños inválidos')
    def section(off, length):
        F.require(start + count * ds <= off <= ms and off + length <= ms, 'tabla fuera de fichero')
        return metadata[off:off + length]
    def flow(off, length):
        F.require(off % 8 == 0 and off + length <= bs, 'flujo fuera de chip/alineación')
        return chip[off:off + length]
    poses = []
    for n in range(count):
        ox, oy, w, h, cols, pri, nt, to, co, ro, so, mo = struct.unpack_from(F.DESC, metadata, start + n * ds)
        F.require(0 <= w <= 256 and 0 <= h <= 256 and bool(w) == bool(h)
                  and cols == (w + 15) // 16 and pri < 4 and nt > 0
                  and so == mo == 0xffffffff, 'descriptor inválido')
        tiles, rows, maps = [], [[] for _ in range(h)], []
        for j in range(nt):
            dx, dy, tile, size, flips, pal, pad = struct.unpack(F.TILE, section(to + 10 * j, 10))
            F.require(tile < 512 and size in (8, 16) and flips < 4 and pal < 8 and pad == 0,
                      'ficha inválida')
            tiles.append([dx, dy, tile, size, flips & 1, flips >> 1, pal])
        for c in range(cols):
            lo, hi = struct.unpack('>II', section(co + 8 * c, 8))
            for y, row in enumerate(F.decode_channels(flow(lo, 8 + 4 * h), flow(hi, 8 + 4 * h), h)):
                rows[y].extend(row)
        F.require(all(not any(row[w:]) for row in rows), 'padding opaco')
        for y in range(h):
            ptr, = struct.unpack('>I', section(ro + 4 * y, 4))
            nr, = struct.unpack('>H', section(ptr, 2))
            row_map, colors = [], {}
            for j in range(nr):
                p, i, d, pad, color = struct.unpack('>BBBBH', section(ptr + 2 + 6 * j, 6))
                F.require(p < 8 and 1 <= i <= 15 and 1 <= d <= 15 and not pad and color <= 0xfff,
                          'mapa inválido')
                F.require(d not in colors or colors[d] == color, 'colisión de color')
                colors[d] = color
                row_map.append((p, i, d, color))
            F.require(len({(p, i) for p, i, _, _ in row_map}) == nr, 'mapa duplicado')
            maps.append(row_map)
        poses.append(dict(origin=[ox, oy], width=w, height=h, priority=pri,
                          tiles=tiles, rows=[r[:w] for r in rows], row_maps=maps))
    return poses


def copper_only(specs, vram, cg):
    """Una imagen fija por forma, incluso permitiendo mapa distinto por fila.

    Un color presente debe conservar el mismo índice entre todas las peticiones.
    Una recarga por fila no puede cambiar los índices DMA fijos de Mario.
    Matching bipartito exacto: evita confundir unión de colores con colisión.
    """
    grouped = collections.defaultdict(list)
    for spec in specs:
        grouped[shape(spec)].append(spec)
    failures = []
    for key, requests in grouped.items():
        _, _, truth = F.compose(vram, requests[0]['tiles'], True)
        for y, row in enumerate(truth):
            colors = sorted({snes_to_amiga12(cg[128 + 16 * val[0] + val[1]])
                             for val in row if val is not None})
            allowed = {c: set(range(1, 16)) for c in colors}
            for spec in requests:
                fixed = {int(k): v for k, v in spec['reserved_rows'][y].items()}
                for color in colors:
                    allowed[color] -= {k for k, v in fixed.items() if v != color}
            owners = {}
            def assign(color, seen):
                for k in sorted(allowed[color] - seen):
                    seen.add(k)
                    if k not in owners or assign(owners[k], seen):
                        owners[k] = color
                        return True
                return False
            matched = sum(assign(c, set()) for c in colors)
            if matched != len(colors):
                failures.append(dict(shape=requests[0]['name'], row=y, colors=colors,
                                     allowed={str(c): sorted(a) for c, a in allowed.items()},
                                     matched=matched, required=len(colors),
                                     requests=[dict(name=s['name'], reserved=s['reserved_rows'][y])
                                               for s in requests if s['reserved_rows'][y]]))
                break
    return dict(shapes=len(grouped), failed_shapes=len(failures), witnesses=failures)


def build(specs, base, vram, cg):
    bank, dma = F.Bank(0xffffffff), F.Bank(0xffffffff)
    candidates, catalogue, keys, aliases = {}, [], {}, []
    present = {shape(s) for s in specs}
    missing = list({shape(s): s for s in base if shape(s) not in present}.values())
    old_poses = []
    request_pixels = observed_chip = 0
    for request_number, spec in enumerate(specs + missing):
        key = shape(spec)
        pose, _ = F.pack_pose(vram, cg, spec['tiles'], spec['priority'], bank,
                             spec.get('reserved_rows'), candidates.get(key))
        checked = F.verify_measured_pose(vram, cg, pose, bank)
        if request_number < len(specs):
            request_pixels += checked
            observed_chip = len(bank.data)
        mapping = tuple(tuple(x for x in row if x[0] != 255) for row in pose['row_maps'])
        if mapping not in candidates.setdefault(key, []):
            candidates[key].append(mapping)
        if len(old_poses) < len(specs):
            old_poses.append(pose)
        identity = key, mapping
        if identity not in keys:
            streams = []
            for pair in pose['streams']:
                streams.append([bytes(bank.data[at:at + 8 + 4 * pose['height']]) for at in pair])
                for blob in streams[-1]:
                    dma.add(blob)
            keys[identity] = len(catalogue)
            catalogue.append(dict(pose, row_maps=mapping, streams=streams,
                                  source=0xffffffff, mask=0xffffffff))
        aliases.append(keys[identity])
    chip, offsets = compact(dma.offsets)
    packed = [dict(p, streams=[[offsets[b] for b in pair] for pair in p['streams']]) for p in catalogue]
    holder = F.Bank()
    holder.data = bytearray(chip)
    metadata = bytearray(F.serialize(packed, holder))
    struct.pack_into('>4sH', metadata, 0, b'SG2A', 2)
    decoded = decode(metadata, chip, limit=0xffffffff)
    pixels = F.verify(vram, cg, decoded)
    for spec, alias in zip(specs, aliases):
        F.require(shape(spec) == shape(decoded[alias]), 'alias cambia pose/prioridad')
        for row, reserve in zip(decoded[alias]['row_maps'], spec['reserved_rows']):
            fixed = {int(k): v for k, v in reserve.items()}
            F.require(all(d not in fixed or fixed[d] == c for _, _, d, c in row), 'alias pisa Mario')
    return chip, bytes(metadata), decoded, aliases, dict(
        requests=len(specs), added_shapes=len(missing), shapes=len(candidates), descriptors=len(packed),
        max_candidates=max(map(len, candidates.values())), dma_raw=len(dma.data), chip=len(chip),
        chip_margin=65536-len(chip), metadata=len(metadata), pixels_checked=pixels,
        legacy_chip_observed=observed_chip, legacy_chip_including_legal=len(bank.data),
        requested_pixels_checked=request_pixels, old_metadata=len(F.serialize(old_poses, bank)))


def directory(metadata, decoded):
    """Índice por forma: fichas en metadata, lista explícita de variantes u16."""
    groups = collections.defaultdict(list)
    for n, pose in enumerate(decoded):
        groups[shape(pose)].append(n)
    data = bytearray(8 + 12 * len(groups))
    struct.pack_into('>4sHH', data, 0, b'G2IX', 1, len(groups))
    for entry, (key, variants) in enumerate(groups.items()):
        tile_off, = struct.unpack_from('>I', metadata, 24 + 32 * variants[0] + 12)
        ptr = len(data)
        struct.pack_into('>IBBHI', data, 8 + 12 * entry, tile_off, key[1], len(key[0]), len(variants), ptr)
        data.extend(b''.join(struct.pack('>H', n) for n in variants))
    # Leer los índices emitidos y cotejar tanto pertenencia como cobertura.
    seen = []
    for j, (key, expected) in enumerate(groups.items()):
        tile_off, priority, nt, count, ptr = struct.unpack_from('>IBBHI', data, 8 + 12 * j)
        F.require(ptr >= 8 + 12 * len(groups) and ptr + 2 * count <= len(data), 'directorio truncado')
        actual = list(struct.unpack_from('>%dH' % count, data, ptr))
        F.require(actual == expected and all(shape(decoded[n]) == key for n in actual), 'directorio cambia variantes')
        F.require(priority == key[1] and nt == len(key[0]), 'directorio cambia forma')
        raw_tiles = metadata[tile_off:tile_off + 10 * nt]
        F.require(raw_tiles == b''.join(struct.pack(F.TILE, dx, dy, t, z, fx | fy << 1, pal, 0)
                                       for dx, dy, t, z, fx, fy, pal in key[0]), 'directorio cambia fichas')
        seen.extend(actual)
    F.require(sorted(seen) == list(range(len(decoded))), 'directorio pierde variantes')
    return bytes(data)


def memory(listings, chip_size, metadata_size):
    reports = []
    data = open(os.path.join(G.WORK, 'yi1_s.dat'), 'rb').read()
    for path in listings:
        listing = M.Listing(open(path).read())
        model = M.build_model(listing, data=data)
        F.require(not model.viol, 'memmap base: %s' % model.viol)
        bank = M.Block('G2 DMA proyectado', 'chip', chip_size, 'sprite', M.MEMF_CHIP,
                       [M.Sub('flujos inmutables', 0, chip_size, 'sprite', 8)])
        M.check_block(listing, model, bank)
        chip = model.chip + bank.alloc
        slow = model.slow + M.align(metadata_size, 8) + 2376
        F.require(not model.viol and chip <= M.CHIP_TOP and slow <= M.SLOW_TOP, 'memmap proyectado desbordado')
        cpu = sum(s.size for b in model.blocks if b.mem == 'chip' and b.kind == 'data'
                  for s in b.subs if s.role == 'cpu')
        reports.append(dict(listing=path, base_chip=model.chip, base_slow=model.slow,
                            cpu_to_slow=cpu, chip_with_bank=chip, slow_with_metadata_snapshots=slow,
                            slow_after_c2_c4=slow+M.align(cpu, 8), violations=model.viol))
    return reports


def selftest():
    lo = F.channel([[1]*16]*3, 0, 0)
    hi = F.channel([[1]*16]*3, 0, 1)
    data, offsets = compact([lo, hi, lo, bytes(8)])
    F.require(all(data[a:a+len(b)] == b and a % 8 == 0 for b, a in offsets.items()), 'autoprueba solape')
    F.require(F.decode_channels(data[offsets[lo]:offsets[lo]+len(lo)],
                               data[offsets[hi]:offsets[hi]+len(hi)], 3) == [[1]*16]*3, 'autoprueba píxeles')
    for bad in (b'', bytes(24)):
        try:
            decode(bad, data)
        except F.FormatError:
            pass
        else:
            raise F.FormatError('aceptó metadata inválida')
    print('G2 autoprueba: OK')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    lvdesc.add_arg(ap)
    ap.add_argument('--src', default=G._DEF_SRC)
    ap.add_argument('--variants', default='work/g2/variants.json')
    ap.add_argument('--base', default='work/g2/base.json')
    ap.add_argument('--listing', action='append', default=[])
    ap.add_argument('--growth-trace', action='append', default=[], help='SOT1=oracle_oam.bin (estimación sin Mario)')
    ap.add_argument('--out', default='work/g2/audit')
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return
    F.derived_path(args.out)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    level = lvdesc.load(args.level)
    vram, _, _ = G.build_vram(args.src, level.header.hex())
    cg = G.level_cgram(args.src, level.header.hex())
    specs = json.load(open(args.variants))['poses']
    base = json.load(open(args.base))['poses']
    legal = {}
    S.legal_rex(args.src, legal)
    F.require({shape(s) for s in legal.values()} <= {shape(s) for s in base}, 'faltan poses Rex legales')
    copper = copper_only(specs, vram, cg)  # evaluar antes de elegir variantes
    chip, metadata, decoded, aliases, report = build(specs, base, vram, cg)
    F.require(len(chip) <= 65536 and len(metadata) <= 98304, 'G2 excede contrato')
    index = directory(metadata, decoded)
    report['directory'] = len(index)
    report['runtime_tables'] = len(metadata) + len(index)
    F.require(report['runtime_tables'] <= 98304, 'tablas exceden 96 KiB')
    report['copper_only'] = copper
    report['memory_projection'] = memory(args.listing, len(chip), report['runtime_tables'])
    growth, counts = {}, collections.Counter()
    for pair in args.growth_trace:
        path, oracle = pair.split('=', 1)
        S.read_trace(path, oracle, growth, counts)
    if growth:
        _, _, _, _, report['growth_sample_no_mario'] = build(specs, base + list(growth.values()), vram, cg)
        resident = [s for s in growth.values() if not s['name'].startswith('trace_9f_')]
        _, _, _, _, report['growth_resident_no_banzai_no_mario'] = build(specs, base + resident, vram, cg)
        report['growth_dispatches'] = dict(counts)
    report['base_without_mario'] = build([], base, vram, cg)[-1]
    report['inputs_sha256'] = {}
    for path in [args.variants, args.base, *args.listing]:
        with open(path, 'rb') as handle:
            report['inputs_sha256'][path] = hashlib.sha256(handle.read()).hexdigest()
    decode(metadata, chip)  # límite estricto antes de escribir el prototipo
    report['scope'] = 'prueba G2 offline; no loader G3, asignador, PF1 bob ni plazos copper integrados'
    with open(args.out + '.json', 'w') as handle:
        json.dump(report, handle, indent=2)
    with open(args.out + '.dma', 'wb') as handle:
        handle.write(chip)
    with open(args.out + '.sg2a', 'wb') as handle:
        handle.write(metadata)
    with open(args.out + '.groups', 'wb') as handle:
        handle.write(index)
    with open(args.out + '.aliases.json', 'w') as handle:
        json.dump(aliases, handle)
    F.evidence(vram, cg, decoded, args.out + '.png')
    from PIL import Image, ImageChops
    with Image.open(args.out + '.png') as evidence:
        half = evidence.height // 2
        F.require(ImageChops.difference(evidence.crop((0, 0, evidence.width, half)),
                                       evidence.crop((0, half, evidence.width, 2 * half))).getbbox() is None,
                  'PNG difiere de referencia')
    print(json.dumps({k: v for k, v in report.items() if k not in ('copper_only',)}, indent=2))
    print('Copper una imagen/fila: %d/%d formas incompatibles con Mario' %
          (copper['failed_shapes'], copper['shapes']))


if __name__ == '__main__':
    main()
