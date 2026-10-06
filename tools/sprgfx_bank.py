"""SG3F/2: banco DMA inmutable y catalogo residente acotado."""
import collections
import struct
import sprgfx_final as F
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
    """Lector SG3F/2: descriptor 32 B y bob ausente ($FFFFFFFF).

    Valida metadata separada; deserialize_bank exige tambien directorio.
    Conserva el lector SG3F/1 sin reinterpretar sus campos bob.
    """
    F.require(len(metadata) >= 24, 'cabecera truncada')
    magic, version, ds, count, start, bs, ms = struct.unpack_from(F.HEADER, metadata)
    F.require((magic, version, ds, start) == (b'SG3F', 2, 32, 24), 'formato desconocido')
    F.require(0 < count <= 65535 and 0 < bs == len(chip) <= limit and ms == len(metadata)
              and start + count * ds <= ms, 'tamaños inválidos')
    def section(off, length):
        F.require(off % 2 == 0 and start + count * ds <= off <= ms and off + length <= ms, 'tabla fuera de fichero')
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
            F.require(set(colors) == {d for d in rows[y][:w] if d},
                      'mapa no cubre exactamente indices opacos DMA')
            maps.append(row_map)
        poses.append(dict(origin=[ox, oy], width=w, height=h, priority=pri,
                          tiles=tiles, rows=[r[:w] for r in rows], row_maps=maps))
    return poses


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
    struct.pack_into('>4sH', metadata, 0, b'SG3F', 2)
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


def deserialize_bank(tables, chip):
    """SG3F/2 concatena metadata, G2IX y trailer S2IX/base relativa u32.

    La metadata mantiene su longitud en +20; todos los offsets del directorio
    siguen relativos a su propia base. No acepta el prototipo SG2A.
    """
    F.require(32 <= len(tables) <= 98304, 'tablas fuera del contrato')
    magic, offset = struct.unpack_from('>4sI', tables, len(tables) - 8)
    F.require(magic == b'S2IX' and offset % 2 == 0 and 24 <= offset <= len(tables)-16,
              'trailer/directorio invalido')
    ms, = struct.unpack_from('>I', tables, 20)
    F.require(ms == offset, 'metadata/directorio discontinuos')
    metadata, index = tables[:offset], tables[offset:-8]
    poses = decode(metadata, chip)
    F.require(len(index) >= 8, 'directorio truncado')
    magic, version, count = struct.unpack_from('>4sHH', index)
    F.require(magic == b'G2IX' and version == 1 and 8 + 12*count <= len(index),
              'cabecera directorio invalida')
    seen, shapes = [], set()
    for j in range(count):
        to, pri, nt, nv, ptr = struct.unpack_from('>IBBHI', index, 8+12*j)
        F.require(nv > 0 and ptr % 2 == 0 and 8+12*count <= ptr and ptr+2*nv <= len(index),
                  'lista de variantes fuera del directorio')
        variants = struct.unpack_from('>%dH' % nv, index, ptr)
        F.require(all(n < len(poses) for n in variants), 'variante fuera del catalogo')
        key = shape(poses[variants[0]])
        F.require(key not in shapes and pri == key[1] and nt == len(key[0]),
                  'forma repetida o distinta')
        shapes.add(key)
        F.require(all(shape(poses[n]) == key for n in variants), 'variante de otra forma')
        F.require(to % 2 == 0 and 24+32*len(poses) <= to and to+10*nt <= ms,
                  'fichas del directorio fuera de metadata')
        truth = b''.join(struct.pack(F.TILE, dx,dy,t,z,fx|fy<<1,pal,0)
                         for dx,dy,t,z,fx,fy,pal in key[0])
        F.require(metadata[to:to+10*nt] == truth, 'directorio cambia fichas')
        seen.extend(variants)
    F.require(sorted(seen) == list(range(len(poses))), 'directorio pierde/duplica variantes')
    return poses, index


def run_bounded(vram, cg, src, manifest, base_path, out):
    """Acepta solo el contrato declarado, sin equivalerlo a cobertura YI1."""
    import json
    import os
    import hashlib
    import sprgfx_manifest as S
    from PIL import Image, ImageChops
    F.require(manifest and base_path, 'g2-bounded requiere --manifest y --base')
    variants = json.load(open(manifest, encoding='utf-8'))
    base = json.load(open(base_path, encoding='utf-8'))
    counts = {'AB': 4082, 'BD': 594, '02': 415, 'B9': 307}
    F.require(variants['exact_dispatches'] == counts and base['exact_dispatches'] == counts,
              'despachos fuera del lote G2')
    specs = variants['poses']
    F.require(len(specs) == 2593 and all('reserved_rows' in s for s in specs),
              'peticiones incompletas/reservas ausentes')
    F.require(all(s.get('source') == 'SOT1/oracle/dynamic_rows' for s in specs)
              and all(s.get('mario_variant') in range(8) for s in specs),
              'fuente/ocho paletas fuera del contrato G2')
    legal = {}
    S.legal_rex(src, legal)
    F.require({shape(s) for s in legal.values()} <= {shape(s) for s in base['poses']},
              'Rex legal incompleto')
    chip, metadata, _, aliases, report = build(specs, base['poses'], vram, cg)
    decoded = decode(metadata, chip)
    index = directory(metadata, decoded)
    tables = metadata + index + struct.pack('>4sI', b'S2IX', len(metadata))
    decoded, _ = deserialize_bank(tables, chip)
    F.verify(vram, cg, decoded)
    F.require(report['shapes'] == 48 and len(decoded) == 289 and report['added_shapes'] == 5,
              'catalogo fuera del lote auditado')
    prefix = out or os.path.join(F.WORK, 'g3/bank')
    F.derived_path(prefix)
    os.makedirs(os.path.dirname(prefix), exist_ok=True)
    F.evidence(vram, cg, decoded, prefix+'.png')
    with Image.open(prefix+'.png') as img:
        h = img.height//2
        F.require(ImageChops.difference(img.crop((0,0,img.width,h)),
                                        img.crop((0,h,img.width,2*h))).getbbox() is None,
                  'PNG referencia/decodificacion distinto')
    report.update(format='SG3F/2', scope='g2-bounded', scope_complete=True,
                  final_complete=False, rejected=[], differences=0,
                  directory=len(index), runtime_tables=len(tables), bob_present=False,
                  immutable_dma=True, aliases=aliases,
                  pending=['cobertura global YI1', 'G4/G5/G6', 'bob PF1 G7'])
    for suffix, blob in (('.idx', tables), ('.dma', chip)):
        open(prefix+suffix, 'wb').write(blob)
    report['sha256'] = {suffix: hashlib.sha256(open(prefix+suffix,'rb').read()).hexdigest()
                        for suffix in ('.idx','.dma','.png')}
    json.dump(report, open(prefix+'.json','w'), indent=2)
    print('SG3F/2 g2-bounded: %d peticiones, %d formas, %d descriptores; chip=%d tablas=%d; diferencias=0' %
          (len(specs), report['shapes'], len(decoded), len(chip), len(tables)))
    return 0
