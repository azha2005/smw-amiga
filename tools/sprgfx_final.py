#!/usr/bin/env python3
"""Formato G3: poses explícitas, flujos attached y auditoría sin aproximaciones.

No infiere propietarios OAM. La reserva de Mario se suministra por fila;
sin ella un banco es únicamente una fuente para el planificador G4/G6.
"""
import json
import os
import struct

from mksprgfx import ficha, ref_pixel, entries, pose_key, WORK
from palette import snes_to_amiga12


class FormatError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise FormatError(message)


def derived_path(path):
    root, target = os.path.realpath(WORK), os.path.realpath(path)
    require(os.path.commonpath([root, target]) == root, 'R9: salida derivada fuera de work/')


def compose(vram, tiles, independent=False):
    """Primera ficha OAM opaca gana. Conserva paleta/índice de cada píxel."""
    require(bool(tiles), 'pose vacía')
    for dx, dy, tile, size, fx, fy, pal in tiles:
        require(-32768 <= dx <= 32767 and -32768 <= dy <= 32767,
                'origen fuera de s16')
        require(0 <= tile < 512 and size in (8, 16) and fx in (0, 1)
                and fy in (0, 1) and 0 <= pal < 8, 'ficha desconocida')
    x0 = min(t[0] for t in tiles)
    y0 = min(t[1] for t in tiles)
    x1 = max(t[0] + t[3] for t in tiles)
    y1 = max(t[1] + t[3] for t in tiles)
    require(x1 - x0 <= 256 and y1 - y0 <= 256, 'pose mayor de 256x256')
    rows = [[None] * (x1 - x0) for _ in range(y1 - y0)]
    for dx, dy, tile, size, fx, fy, pal in tiles:
        px = None if independent else ficha(vram, tile, size, fx, fy)
        for y in range(size):
            for x in range(size):
                val = (ref_pixel(vram, tile, size, fx, fy, x, y)
                       if independent else px[y][x])
                if val and rows[dy - y0 + y][dx - x0 + x] is None:
                    rows[dy - y0 + y][dx - x0 + x] = (pal, val)
    visible = [(x, y) for y, row in enumerate(rows)
               for x, val in enumerate(row) if val is not None]
    if not visible:
        return x0, y0, []
    left = min(p[0] for p in visible)
    top = min(p[1] for p in visible)
    right = max(p[0] for p in visible) + 1
    bottom = max(p[1] for p in visible) + 1
    return x0 + left, y0 + top, [r[left:right] for r in rows[top:bottom]]


def stable_map(rows, cg, reserved):
    """Coloración exacta por pose; compartir índice solo entre filas disjuntas.

    Intenta conservar la correspondencia entre filas antes de recurrir a
    variantes fila a fila. La ventana de recarga sigue siendo puerta G6.
    """
    row_colors = [{snes_to_amiga12(cg[128 + 16 * v[0] + v[1]])
                   for v in row if v is not None} for row in rows]
    colors = set().union(*row_colors) if row_colors else set()
    allowed = {c: set(range(1, 16)) for c in colors}
    edges = {c: set() for c in colors}
    for present, fixed in zip(row_colors, reserved):
        fixed = {int(k): v for k, v in fixed.items()}
        require(all(1 <= k <= 15 and 0 <= v <= 0xfff for k, v in fixed.items()),
                'reserva de Mario inválida')
        for c in present:
            allowed[c] -= {k for k, v in fixed.items() if c != v}
            edges[c] |= present - {c}
    assignment = {}
    attempts = 0
    def search():
        nonlocal attempts
        attempts += 1
        if attempts > 10000:
            return False  # optimización acotada; fallback exacto por fila
        if len(assignment) == len(colors):
            return True
        choices = {c: allowed[c] - {assignment[n] for n in edges[c] if n in assignment}
                   for c in colors if c not in assignment}
        c = min(choices, key=lambda k: (len(choices[k]), -len(edges[k]), k))
        for target in sorted(choices[c]):
            assignment[c] = target
            if search():
                return True
        assignment.pop(c, None)
        return False
    return assignment if search() else None


def remap(rows, cg, reserved=None, candidates=None):
    """Mapa por fila a 1..15. Reserva explícita índice DMA -> OCS de Mario.

    La recarga entre filas NO queda validada aquí: es puerta separada de G6.
    """
    output, maps = [], []
    if reserved is None:
        reserved = [{} for _ in rows]
    require(len(reserved) == len(rows), 'reserva de Mario: alto incorrecto')
    for candidate in candidates or []:
        require(len(candidate) == len(rows), 'candidato de remapeo con altura distinta')
        compatible = True
        maps = []
        output = []
        for row, oldmap, fixed in zip(rows, candidate, reserved):
            fixed = {int(k): v for k, v in fixed.items()}
            mapping = {(p, i): (target, color) for p, i, target, color in oldmap if p != 255}
            if any(target in fixed and fixed[target] != color for target, color in mapping.values()):
                compatible = False
                break
            maps.append([(p, i, target, color) for (p, i), (target, color) in sorted(mapping.items())]
                        + [(255, k, k, color) for k, color in sorted(fixed.items())])
            output.append([mapping[v][0] if v is not None else 0 for v in row])
        if compatible:
            return output, maps
    output, maps = [], []
    stable = stable_map(rows, cg, reserved)
    for y, row in enumerate(rows):
        fixed = {int(k): v for k, v in reserved[y].items()}
        require(all(1 <= k <= 15 and 0 <= v <= 0xfff for k, v in fixed.items()),
                'reserva de Mario inválida')
        used = sorted(set(v for v in row if v is not None))
        mapping = {}
        colors = dict(fixed)
        for pal, idx in used:
            color = snes_to_amiga12(cg[128 + pal * 16 + idx])
            if stable is not None:
                target = stable[color]
                require(target not in fixed or fixed[target] == color, 'mapa estable pisa Mario')
                colors[target] = color
                mapping[pal, idx] = (target, color)
                continue
            matches = sorted(k for k, v in colors.items() if v == color)
            if matches:
                target = matches[0]
            else:
                free = [k for k in range(1, 16) if k not in colors]
                require(bool(free), 'fila %d: sin índice exacto para pal=%d idx=%d OCS=%03x; '
                        'reservados=%s usados=%s' % (y, pal, idx, color, fixed, mapping))
                target = free[0]
                colors[target] = color
            mapping[pal, idx] = (target, color)
        maps.append([(p, i, target, color) for (p, i), (target, color)
                     in sorted(mapping.items())] + [(255, k, k, color) for k, color in sorted(fixed.items())])
        output.append([mapping[v][0] if v is not None else 0 for v in row])
    return output, maps


def channel(rows, column, upper):
    # POS/CTL se programan por objeto; solo ATTACH del canal impar es fijo.
    data = bytearray(struct.pack('>HH', 0, 0x80 if upper else 0))
    for row in rows:
        words = [0, 0]
        for x in range(16):
            v = row[column * 16 + x] if column * 16 + x < len(row) else 0
            for p in range(2):
                words[p] |= ((v >> (p + 2 * upper)) & 1) << (15 - x)
        data.extend(struct.pack('>HH', *words))
    data.extend(bytes(4))
    return bytes(data)


def decode_channels(lo, hi, height):
    require(len(lo) == len(hi) == 8 + height * 4, 'longitud DMA inválida')
    require(lo[:4] == bytes(4) and hi[:4] == b'\0\0\0\x80', 'controles DMA inválidos')
    require(lo[-4:] == hi[-4:] == bytes(4), 'terminador DMA inválido')
    rows = []
    for y in range(height):
        words = struct.unpack_from('>HH', lo, 4 + 4 * y) + struct.unpack_from('>HH', hi, 4 + 4 * y)
        rows.append([sum(((word >> (15 - x)) & 1) << p for p, word in enumerate(words))
                     for x in range(16)])
    return rows


def bob(rows):
    stride = ((len(rows[0]) + 15) // 16) * 2
    size = stride * len(rows)
    data = bytearray(5 * size)
    for y, row in enumerate(rows):
        for x, val in enumerate(row):
            for p in range(5):
                bit = bool(val) if p == 4 else (val >> p) & 1
                if bit:
                    data[p * size + y * stride + x // 8] |= 0x80 >> (x & 7)
    return bytes(data[:4 * size]), bytes(data[4 * size:]), stride


def decode_bob(source, mask, width, height, stride):
    require(stride == ((width + 15) // 16) * 2 and len(mask) == height * stride
            and len(source) == 4 * len(mask), 'bob: tamaño inválido')
    out = []
    for y in range(height):
        row = []
        for x in range(stride * 8):
            off, shift = y * stride + x // 8, 7 - (x & 7)
            val = sum(((source[p * len(mask) + off] >> shift) & 1) << p for p in range(4))
            require(((mask[off] >> shift) & 1) == bool(val), 'bob: máscara incorrecta')
            require(x < width or val == 0, 'bob: padding opaco')
            if x < width:
                row.append(val)
        out.append(row)
    return out


class Bank:
    def __init__(self, limit=65536):
        self.data = bytearray()
        self.offsets = {}
        self.limit = limit

    def add(self, data):
        if data in self.offsets:
            return self.offsets[data]
        off = (len(self.data) + 7) & ~7
        end = off + len(data)
        require(end <= self.limit, 'banco chip desbordado: %d B > %d B' % (end, self.limit))
        self.data.extend(bytes(off - len(self.data)))
        self.data.extend(data)
        self.offsets[data] = off
        return off


def pack_pose(vram, cg, tiles, priority, bank, reserved=None, candidates=None):
    require(priority in range(4), 'prioridad OAM inválida')
    ox, oy, truth = compose(vram, tiles)
    require((ox, oy, truth) == compose(vram, tiles, True), 'composición pierde píxeles/orden')
    rows, maps = remap(truth, cg, reserved, candidates)
    height, width = len(rows), len(rows[0]) if rows else 0
    columns = (width + 15) // 16
    offsets = []
    for column in range(columns):
        offsets.append([bank.add(channel(rows, column, 0)), bank.add(channel(rows, column, 1))])
    source, mask, stride = bob(rows) if rows else (b'', b'', 0)
    so, mo = (bank.add(source), bank.add(mask)) if rows else (0, 0)
    return dict(origin=[ox, oy], width=width, height=height, columns=columns,
                priority=priority, tiles=tiles, streams=offsets, source=so, mask=mo,
                stride=stride, row_maps=maps), truth


# Cabecera 24 B; descriptor 32 B; referencias relativas al fichero de índices.
HEADER = '>4sHHIIII'
DESC = '>hhHHBBHIIIII'
TILE = '>hhHBBBB'


def serialize(poses, bank):
    metadata = bytearray(24 + 32 * len(poses))
    tables = {}
    def add_table(data):
        if data in tables:
            return tables[data]
        if len(metadata) & 1:
            metadata.append(0)
        off = len(metadata)
        metadata.extend(data)
        tables[data] = off
        return off
    struct.pack_into(HEADER, metadata, 0, b'SG3F', 1, 32, len(poses), 24,
                     len(bank.data), 0)
    for n, pose in enumerate(poses):
        tiles = bytearray()
        for dx, dy, t, size, fx, fy, pal in pose['tiles']:
            tiles.extend(struct.pack(TILE, dx, dy, t, size, fx | fy << 1, pal, 0))
        tile_off = add_table(bytes(tiles))
        stream_off = add_table(b''.join(struct.pack('>II', *pair) for pair in pose['streams']))
        row_offsets = []
        for row_map in pose['row_maps']:
            row = bytearray(struct.pack('>H', len(row_map)))
            for pal, idx, dma, color in row_map:
                row.extend(struct.pack('>BBBBH', pal, idx, dma, 0, color))
            row_offsets.append(add_table(bytes(row)))
        row_off = add_table(b''.join(struct.pack('>I', off) for off in row_offsets))
        struct.pack_into(DESC, metadata, 24 + 32 * n, *pose['origin'],
                         pose['width'], pose['height'], pose['columns'], pose['priority'],
                         len(pose['tiles']), tile_off, stream_off, row_off,
                         pose['source'], pose['mask'])
    struct.pack_into('>I', metadata, 20, len(metadata))
    return bytes(metadata)


def deserialize(metadata, chip):
    require(len(metadata) >= 24, 'cabecera truncada')
    magic, version, ds, count, start, bs, ms = struct.unpack_from(HEADER, metadata)
    require(magic == b'SG3F' and version == 1 and ds == 32 and start == 24,
            'formato desconocido')
    require(bs == len(chip) <= 65536 and ms == len(metadata)
            and start + count * ds <= ms, 'tamaños de banco/índices inválidos')
    poses = []
    def section(off, length):
        require(start + count * ds <= off <= ms and off + length <= ms,
                'offset de tabla fuera de fichero')
        return metadata[off:off + length]
    def flow(off, length):
        require(off % 8 == 0 and 0 <= off and off + length <= bs, 'offset chip inválido')
        return chip[off:off + length]
    for n in range(count):
        ox, oy, w, h, cols, priority, nt, to, co, ro, so, mo = struct.unpack_from(DESC, metadata, start + n * ds)
        require(0 <= w <= 256 and 0 <= h <= 256 and bool(w) == bool(h) and cols == (w + 15) // 16
                and priority < 4 and nt > 0, 'descriptor inválido')
        tiles = []
        for off in range(nt):
            dx, dy, tile, size, flips, pal, pad = struct.unpack(TILE, section(to + off * 10, 10))
            require(tile < 512 and size in (8, 16) and flips < 4 and pal < 8 and pad == 0,
                    'ficha de descriptor desconocida')
            tiles.append([dx, dy, tile, size, flips & 1, flips >> 1, pal])
        rows = [[] for _ in range(h)]
        for c in range(cols):
            lo, hi = struct.unpack('>II', section(co + 8 * c, 8))
            decoded = decode_channels(flow(lo, 8 + 4 * h), flow(hi, 8 + 4 * h), h)
            for y in range(h):
                rows[y].extend(decoded[y])
        require(all(not any(row[w:]) for row in rows), 'DMA: padding opaco')
        rows = [r[:w] for r in rows]
        stride = ((w + 15) // 16) * 2
        if h:
            require(rows == decode_bob(flow(so, 4 * h * stride), flow(mo, h * stride), w, h, stride),
                    'bob distinto de DMA')
        else:
            require(so == mo == 0, 'pose vacía con fuentes DMA')
        maps = []
        for y in range(h):
            row_ptr, = struct.unpack('>I', section(ro + 4 * y, 4))
            nr, = struct.unpack('>H', section(row_ptr, 2))
            row_ptr += 2
            row_map = []
            for _ in range(nr):
                pal, idx, dma, pad, color = struct.unpack('>BBBBH', section(row_ptr, 6))
                row_ptr += 6
                require((pal < 8 or (pal == 255 and idx == dma)) and 1 <= idx <= 15 and 1 <= dma <= 15
                        and pad == 0 and color <= 0xfff, 'mapa de color inválido')
                row_map.append((pal, idx, dma, color))
            require(len({(p, i) for p, i, _, _ in row_map}) == nr, 'mapa duplicado')
            colors = {}
            for _, _, dma, color in row_map:
                require(dma not in colors or colors[dma] == color, 'colisión de color')
                colors[dma] = color
            maps.append(row_map)
        poses.append(dict(origin=[ox, oy], width=w, height=h, priority=priority,
                          tiles=tiles, rows=rows, row_maps=maps))
    return poses


def verify(vram, cg, poses):
    pixels = 0
    for pose in poses:
        ox, oy, truth = compose(vram, pose['tiles'], True)
        require([ox, oy] == pose['origin'], 'origen no conservado')
        require(len(truth) == pose['height'] and (len(truth[0]) if truth else 0) == pose['width'],
                'recorte incorrecto')
        for y, row in enumerate(truth):
            mapping = {(p, i): (dma, color) for p, i, dma, color in pose['row_maps'][y] if p != 255}
            require(set(mapping) == {v for v in row if v is not None}, 'mapa pierde fuente SNES')
            for x, val in enumerate(row):
                got = pose['rows'][y][x]
                require((val is None and got == 0) or (val is not None and got == mapping[val][0]),
                        'píxel/posición/orden incorrecto')
                if val is not None:
                    pal, idx = val
                    require(mapping[val][1] == snes_to_amiga12(cg[128 + 16 * pal + idx]),
                            'color distinto de SNES -> OCS')
                pixels += 1
    return pixels


def verify_measured_pose(vram, cg, pose, bank):
    """Decodifica también variantes que solo se midieron, sin cargarlas.

    Un banco de medida puede exceder 64 KiB; nunca pasa deserialize ni se
    escribe como archivo DMA cargable. Cada blob sí pasa la ida y vuelta.
    """
    h, w = pose['height'], pose['width']
    rows = [[] for _ in range(h)]
    for lo, hi in pose['streams']:
        decoded = decode_channels(bank.data[lo:lo + 8 + 4 * h],
                                  bank.data[hi:hi + 8 + 4 * h], h)
        for y in range(h):
            rows[y].extend(decoded[y])
    require(all(not any(row[w:]) for row in rows), 'medida DMA: padding opaco')
    rows = [r[:w] for r in rows]
    if h:
        size = h * pose['stride']
        require(rows == decode_bob(bank.data[pose['source']:pose['source'] + 4 * size],
                                   bank.data[pose['mask']:pose['mask'] + size], w, h, pose['stride']),
                'medida bob distinta de DMA')
    return verify(vram, cg, [dict(pose, rows=rows)])


def observed(recs):
    keys = set()
    for frames in recs.values():
        for _, oam, _ in frames:
            for _, _, tile, attr, hi in entries(oam):
                require(hi <= 3, 'OAM normalizada: bits altos desconocidos')
                keys.add(pose_key(tile, attr, hi) + ((attr >> 4) & 3,))
    return [dict(name='tile_%03x_%d_%d%d_p%d_pr%d' % k,
                 tiles=[[0, 0, k[0], k[1], k[2], k[3], k[4]]], priority=k[5])
            for k in sorted(keys)]


def evidence(vram, cg, poses, path):
    from PIL import Image
    bg = (48, 48, 56)
    cell, cols = 36, 16
    height = ((len(poses) + cols - 1) // cols) * cell
    img = Image.new('RGB', (cols * cell, height * 2), bg)
    def rgb(color):
        return ((color >> 8) * 17, ((color >> 4) & 15) * 17, (color & 15) * 17)
    for n, pose in enumerate(poses):
        _, _, truth = compose(vram, pose['tiles'], True)
        require(pose['width'] <= cell and pose['height'] <= cell, 'evidencia: celda insuficiente')
        ox, oy = (n % cols) * cell, (n // cols) * cell
        for y, row in enumerate(truth):
            colors = {d: c for _, _, d, c in pose['row_maps'][y]}
            for x, val in enumerate(row):
                if val is not None:
                    p, i = val
                    img.putpixel((ox + x, oy + y), rgb(snes_to_amiga12(cg[128 + 16 * p + i])))
                dma = pose['rows'][y][x]
                if dma:
                    img.putpixel((ox + x, height + oy + y), rgb(colors[dma]))
    img.resize((img.width * 2, img.height * 2), Image.Resampling.NEAREST).save(path)


def run(vram, cg, recs, manifest=None, out=None):
    prefix = out or os.path.join(WORK, 'sprgfx_final')
    derived_path(prefix)
    manifest_data = json.load(open(manifest, encoding='utf-8')) if manifest else None
    specs = manifest_data['poses'] if manifest_data else observed(recs)
    require(bool(specs), 'sin grabaciones ni manifiesto: cobertura vacía')
    bank = Bank()
    # Solo para medir todos los blobs exactos; nunca se emite como banco cargable.
    measure_bank = Bank(0xffffffff)
    candidates = {}
    descriptors, skipped, encoded_names = [], [], []
    all_exact_pixels = 0
    all_color_exact = 0
    for spec in specs:
        # Un rechazo no consume chip de las siguientes poses.
        before = len(bank.data), dict(bank.offsets)
        try:
            key = tuple(tuple(t) for t in spec['tiles']), spec['priority']
            measured, _ = pack_pose(vram, cg, spec['tiles'], spec['priority'], measure_bank,
                                    spec.get('reserved_rows'), candidates.get(key))
            all_exact_pixels += verify_measured_pose(vram, cg, measured, measure_bank)
            all_color_exact += 1
            candidate = [tuple(t for t in row if t[0] != 255) for row in measured['row_maps']]
            if candidate not in candidates.setdefault(key, []):
                candidates[key].append(candidate)
            pose, _ = pack_pose(vram, cg, spec['tiles'], spec['priority'], bank,
                                spec.get('reserved_rows'), [candidate])
            descriptors.append(pose)
            encoded_names.append(spec['name'])
        except FormatError as error:
            del bank.data[before[0]:]
            bank.offsets = before[1]
            skipped.append(dict(name=spec['name'], kind=('BANK' if 'banco chip' in str(error)
                                else 'COLOR' if 'sin índice exacto' in str(error) else 'FORMAT'),
                                error=str(error)))
    metadata = serialize(descriptors, bank)
    decoded = deserialize(metadata, bytes(bank.data))
    pixels = verify(vram, cg, decoded)
    audit = dict(format='SG3F/1', recordings=len(recs), requested=len(specs),
                 encoded=len(decoded), chip_bytes=len(bank.data), slow_bytes=len(metadata),
                 verified_pixels=pixels, failures=skipped,
                 required_chip_all_color_exact=len(measure_bank.data),
                 all_color_exact=all_color_exact, all_exact_pixels=all_exact_pixels,
                 encoded_names=encoded_names,
                 coverage=('explicit_manifest' if manifest else 'observed_single_tiles_only'),
                 final_complete=False,
                 source_coverage=({k: manifest_data[k] for k in ('exact_dispatches', 'legal_coverage')
                                   if k in manifest_data} if manifest_data else {}),
                 pending=(manifest_data.get('pending', ['cobertura legal del manifiesto no declarada'])
                          if manifest_data else ['pertenencia real y poses compuestas: este lote son fichas individuales',
                                                'VRAM dinámica de Mario: este lote usa GFX00 estático'])
                         + ['plazos de recarga y reservas simultáneas de varios enemigos: G6',
                            'remapeo de bob a siete índices PF1 y colores del terreno: G7'])
    os.makedirs(os.path.dirname(prefix), exist_ok=True)
    open(prefix + '.idx', 'wb').write(metadata)
    open(prefix + '.dma', 'wb').write(bank.data)
    with open(prefix + '.json', 'w', encoding='utf-8') as handle:
        json.dump(audit, handle, indent=2, ensure_ascii=False)
    if all(p['width'] <= 36 and p['height'] <= 36 for p in decoded):
        evidence(vram, cg, decoded, prefix + '.png')
    print('SG3F: %d/%d poses, chip=%d B, slow=%d B, %d píxeles exactos, %d fallos' %
          (len(decoded), len(specs), len(bank.data), len(metadata), pixels, len(skipped)))
    print('Cobertura parcial explícita; G3 final pendiente. Informe: ' + prefix + '.json')
    return 1 if skipped else 0
