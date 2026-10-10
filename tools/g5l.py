#!/usr/bin/env python3
"""G5L: el Rex en sprites de hardware con un plan de color por filas.

Diseño (docs/informe-g5l.md): el mismo modelo de copper calibrado de G2T-A
(g2t_ref.py), pero el plan trabaja con máscaras de índices por fila y un
único borde derecho por frame, no con píxeles. Las recargas de COLOR17-31
van en el borrado horizontal (WAIT $D0) con una capacidad segura que no
necesita leer la lista; solo lo que no entra se coloca con el plan exacto
de g2t_ref.schedule, leyendo ese segmento.

G5L-R: una sola variante por forma, la limpia (cada color del Rex en un
índice). Donde un color choca con Mario (Mario usa ese índice con otro
color en las mismas filas) se lo pasa, en una banda de filas, a otro
índice libre (band_assign); los datos de los sprites se parchean en un
búfer de chip por lista. Sin el banco G3 en el juego.

    python tools/g5l.py mk            # work/g5l/g5l.bin (tabla, slow RAM)
    python tools/g5l.py trace         # plan de referencia sobre las trazas
    python tools/g5l.py game          # el 68000 contra la referencia (Musashi)

Todo lo derivado de la ROM va a work/ (R9).
"""
import argparse
import collections
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

ROWS = 224
V0 = 0x2C
WRAP_SEG = 255 - V0
T0 = -56
X_D0 = 263
IDLE = 48
SLOTS = 9
VBL_COLORS = 15
NHASH = 64
MAXREX = 4
MAXT = 6
MAXMRUNS = 8
SELECT = 'first'
MOVE_PAD = 0x01A0          # relleno: COLOR16 nunca se ve (índice 0 de sprite)
JUMP = 0x0084
OUT = Path('work/g5l')


# ----------------------------------------------------------------------
# copper (g2t_ref, 256 px)
# ----------------------------------------------------------------------
def adv(x, n=1):
    for _ in range(n):
        x = 243 if x == 231 else (x + 8 if x >= 239 else x + 16)
    return x


def xh(h):
    if h <= 0xC0:
        return 8 * ((h - 0x48) >> 2) - 1
    return {0xC4: 243, 0xC6: 243, 0xC8: 247, 0xCA: 247, 0xCC: 251}.get(h, 255 if h <= 0xCE else 999)


def htab(x):
    if x <= 239:
        return 0x48 + 4 * ((x + 8) >> 3)
    return 0xCE if x >= 252 else 0xC4 + ((x - 240) & ~3)


def end_of(nb):
    return 351 - 8 * nb if nb in (7, 8, 9) else None


def schedule(row, last, free, nb1, needs):
    """g2t_ref.schedule con los mismos plazos; needs ordenados."""
    k = len(needs)
    if row == WRAP_SEG:
        return None
    end = end_of(nb1)
    if end is None:
        return None
    need = max(needs)
    t = last if last is not None else free
    best = None
    if last is not None:
        pos, nop = adv(t), 0
        while pos < need:
            pos, nop = adv(pos), nop + 1
        chain = [pos] + [adv(pos, j) for j in range(1, k)]
        if nop + k <= SLOTS and chain[-1] <= end:
            best = ('cadena', nop, chain)
    if need <= 255:
        h = htab(need)
        first = xh(h)
        if first - t >= IDLE:
            wait = [first] + [adv(first, j) for j in range(1, k)]
            if k + 1 <= SLOTS and wait[-1] <= end and (best is None or wait[-1] < best[2][-1]):
                best = ('wait', h, wait)
    elif t <= 255 - IDLE:
        wait = [X_D0 + 8 * j for j in range(k)]
        if k + 1 <= SLOTS and wait[-1] <= end and (best is None or wait[-1] < best[2][-1]):
            best = ('wait', 0xD0, wait)
    return best


# ----------------------------------------------------------------------
# tabla G5L2 (big endian, offsets relativos al principio)
# ----------------------------------------------------------------------
# G5L-N (2026-10-10): la clave de la forma está normalizada (dx, dy menos
# su mínimo como s8; el 68000 suma ese mínimo a sx/sy antes de usar el
# origen de la variante) y las máscaras de píxeles van una vez por forma,
# por color, no repetidas en cada mapa (informe-g4a-1010.md §6).
#  0  'G5L2'
#  4  .w formas  .w variantes  .w NHASH  .w 0
# 12  .l offset de la tabla de máscaras de Mario (744 x 8 .w)
# 16  NHASH x .w: offset de la primera forma del cubo (0 = vacío)
# formas (todas antes de las variantes: offsets .w): .w siguiente (0 =
#        fin), .b fichas, .b prioridad, .w variantes, fichas x 4 B (dx, dy,
#        tile bajo, banderas), variantes x .l offset
# variante: .w ox, .w oy, .b ancho, .b alto, .b columnas, .b índices,
#        .b xmax, .b grupos, .w variante del banco, columnas x (.l off0,
#        .l off1) en bank.dma, grupos x (.b índice, .b 0, .w color, .l
#        filas): el filtro A3 por máscaras (el .b 0 es el número de su
#        máscara en el bloque de la forma); .l offset del bloque de
#        máscaras de la forma (por color: alto x columnas .w, los píxeles de
#        ese color, g5l_patch); índices x (.b índice, .b
#        tramos, tramos x (.b fila primera, .b fila última, .w color),
#        .b cambios, .b última fila, cambios x (.b fila, .b última del
#        tramo anterior o $FF, .w color)): filas seguidas, mismo color;
#        los cambios son el camino rápido de g5l_sweep
def tile_flags(tile, size, fx, fy, pal):
    return (tile >> 8) | (2 if size == 16 else 0) | fx << 2 | fy << 3 | pal << 4


def norm_key(t4):
    """G5L-N: (dx, dy) menos su mínimo (s8), sin reordenar las fichas;
    devuelve las fichas normalizadas y el mínimo (el 68000: g5l_choose)"""
    mx = min(s8(t[0]) for t in t4)
    my = min(s8(t[1]) for t in t4)
    return [((s8(t[0]) - mx) & 255, (s8(t[1]) - my) & 255) + tuple(t[2:]) for t in t4], mx, my


def key_hash(tiles4):
    return (sum(sum(t) for t in tiles4) + len(tiles4)) & (NHASH - 1)


def variant_record(pose, tables, n, offs=None, masks=None):
    """masks = (offset del bloque de la forma, [colores en orden]) (G5L2);
    None: las máscaras dentro del registro, como G5L1 (solo para medir)"""
    ox, oy = pose['origin']
    w, h = pose['width'], pose['height']
    cols = (w + 15) // 16
    xmax = max(x for row in pose['rows'] for x, d in enumerate(row) if d)
    out = bytearray(struct.pack('>hhBBBBBBH', ox, oy, w, h, cols, 0, xmax, 0, n))
    if offs is None:
        co, = struct.unpack_from('>I', tables, 24 + n * 32 + 16)
        offs = [struct.unpack_from('>II', tables, co + 8 * c) for c in range(cols)]
    for o0, o1 in offs:
        out += struct.pack('>II', o0, o1)
    runs = rex_runs(pose)
    if max(len(r) for r in runs.values()) > 32 or h > 32:
        raise ValueError('más de 32 tramos en un índice o 32 filas')
    groups = collections.OrderedDict()
    for d in sorted(runs):
        for a, b, c in runs[d]:
            groups[d, c] = groups.get((d, c), 0) | ((1 << (b + 1)) - 1) & ~((1 << a) - 1)
    out[9] = len(groups)
    for (d, c), m in groups.items():
        out += struct.pack('>BBHI', d, masks[1].index(c) if masks else 0, c, m)
    if masks:
        out += struct.pack('>I', masks[0])
    else:
        for (d, c), m in groups.items():
            out += pose_mask(pose, d)
    out[7] = len(runs)
    for d in sorted(runs):
        out += struct.pack('>BB', d, len(runs[d]))
        for a, b, c in runs[d]:
            out += struct.pack('>BBH', a, b, c)
        chg = changes(runs[d])
        out += struct.pack('>BB', len(chg), runs[d][-1][1])
        for a, pb, c in chg:
            out += struct.pack('>BBH', a, pb, c)
    return bytes(out)


def pose_mask(pose, d):
    """G5L-R: los píxeles del índice d en cada fila y columna (el parche de
    g5l_patch): alto x columnas .w, bit 15 = x 16c"""
    w, h = pose['width'], pose['height']
    out = bytearray()
    for r in range(h):
        for col in range((w + 15) // 16):
            wv = 0
            for x in range(16):
                xx = 16 * col + x
                if xx < w and pose['rows'][r][xx] == d:
                    wv |= 1 << (15 - x)
            out += struct.pack('>H', wv)
    return bytes(out)


def changes(rr):
    """el camino rapido del barrido (g5l_sweep): el primer tramo (sin
    anterior: $FF) y cada tramo de otro color que el anterior, con la ultima
    fila de ese anterior"""
    out = [(rr[0][0], 0xFF, rr[0][2])]
    for (a0, b0, c0), (a, b, c) in zip(rr, rr[1:]):
        if c != c0:
            out.append((a, b0, c))
    return out


def rex_runs(pose):
    """{índice: [(fila primera, fila última, color)]}: filas seguidas, mismo color"""
    runs = collections.defaultdict(list)
    for r in range(pose['height']):
        for _, _, d, c in pose['row_maps'][r]:
            rr = runs[d]
            if rr and rr[-1][1] == r - 1 and rr[-1][2] == c:
                rr[-1] = (rr[-1][0], r, c)
            else:
                rr.append((r, r, c))
    return dict(runs)


# Variantes "limpias" (G5L): cada color del Rex en un solo índice. Blanco y
# negro son los índices 1 y 2 de las 8 paletas de Mario (sin transición).
# Hay varios mapas de los 5 colores propios; por foto se usa el que menos
# choca con Mario (plan_frame). Elegidos sobre yi1 de a uno (cada uno el que
# más fotos con banda le quita a los anteriores) y comprobados sin fallos en
# las tres grabaciones de trace: 1 mapa 694 fotos con 2+ bandas en yi1, 2
# mapas 280, 4 mapas 202.
REXC = [0x44D, 0x66D, 0x88F, 0xB20, 0xF80]
CLEAN_PERMS = [(6, 7, 4, 9, 15), (5, 7, 15, 6, 4), (11, 7, 15, 6, 4), (6, 7, 15, 14, 4)]
CLEAN_MAPS = [{0xFFF: 1, 0x000: 2, **dict(zip(REXC, p))} for p in CLEAN_PERMS]
CLEAN_FLAG = 0x80000000
# G4-B: los demás enemigos de YI1 (informe-g4a-1010.md §2; el Banzai es bob,
# G7). Un mapa limpio por tipo: blanco 1, negro 2 y sus colores propios
# (ordenados) en los índices de BAND_PREF; mapa 4 + su posición aquí.
G5L_OTHER = (0x4F, 0x95, 0xBD, 0x05, 0xB9, 0x7B, 0x02)
NORDS = 16                      # G5L3: órdenes de colores propios (16 x 16 B)


def clean_pose(pose, CLEAN_MAP):
    rows, maps = [], []
    for r, row in enumerate(pose['rows']):
        cmap = {d: c for _, _, d, c in pose['row_maps'][r]}
        rows.append([CLEAN_MAP[cmap[d]] if d else 0 for d in row])
        seen, rm = set(), []
        for p_, i_, d, c in pose['row_maps'][r]:
            if (p_, i_) not in seen:
                seen.add((p_, i_))
                rm.append((p_, i_, CLEAN_MAP[c], c))
        maps.append(rm)
    return dict(pose, rows=rows, row_maps=maps)


def clean_streams(pose, out, index):
    """flujos DMA (POS/CTL 0, DATA/DATB por fila, terminador) de cada
    columna y mitad, alineados a 8 B y compartidos si son iguales"""
    offs = []
    h, w = pose['height'], pose['width']
    for c in range((w + 15) // 16):
        pair = []
        for half in range(2):
            b = bytearray(4)
            for r in range(h):
                wa = wb = 0
                for x in range(16):
                    xx = 16 * c + x
                    v = pose['rows'][r][xx] if xx < w else 0
                    wa |= ((v >> (2 * half)) & 1) << (15 - x)
                    wb |= ((v >> (2 * half + 1)) & 1) << (15 - x)
                b += struct.pack('>HH', wa, wb)
            b += bytes(4)
            b = bytes(b)
            if b not in index:
                out.extend(bytes((-len(out)) % 8))
                index[b] = len(out)
                out.extend(b)
            pair.append(index[b])
        offs.append(tuple(pair))
    return offs


def cp_cols(pose):
    return (pose['width'] + 15) // 16


def other_shapes(types):
    """G4-B: [(fichas, pri, pose, tipo)] y {tipo: (mapa limpio, orden, mapa)}
    de los tipos de G5L_OTHER en types, desde las formas de G4-A
    (work/g4a/shapes.json, g4a.py traceall) y la VRAM/CGRAM del nivel"""
    import g4a
    want = [n for n in G5L_OTHER if n in types]
    if not want:
        return [], {}
    vram, cg = g4a.ctx()
    sj = json.loads(Path('work/g4a/shapes.json').read_text(encoding='utf-8'))
    out, maps = [], {}
    for num in want:
        items = []
        for e in sj['%02X' % num]['todas']:
            tiles, pri = tuple(tuple(x) for x in e[:-1]), e[-1]
            pose = g4a.pose_of(vram, cg, tiles)
            if pose is None:
                continue
            items.append((tiles, pri, pose))
        cols = sorted({c for _, _, pose in items for rm in pose['row_maps'] for _, _, _, c in rm}
                      - {0xFFF, 0x000})
        if len(cols) > len(BAND_PREF):
            raise ValueError('tipo %02X: %d colores propios' % (num, len(cols)))
        idx = BAND_PREF[:len(cols)]
        cmap = {0xFFF: 1, 0x000: 2, **dict(zip(cols, idx))}
        maps[num] = (cmap, list(idx), 4 + G5L_OTHER.index(num))
        for tiles, pri, pose in items:
            out.append((tiles, pri, pose, num))
    return out, maps


def color_image(pose):
    """las filas en colores (para comparar formas de mapas distintos)"""
    out = []
    for r, row in enumerate(pose['rows']):
        cm = {d: c for _, _, d, c in pose['row_maps'][r]}
        out.append(tuple(cm[d] if d else None for d in row))
    return tuple(out)


def build_table(bank, clean=True, types=(0xAB,)):
    import g2t_ref as T
    import g5ref as R
    ctx = T.load_context(bank)
    poses, directory, tables = list(ctx['poses']), dict(ctx['directory']), ctx['tables']
    # G4-B: las formas de los demás tipos, como poses extra con su mapa
    extra, omaps = other_shapes(types) if clean else ([], {})
    pmap = {}                                   # pose -> (mapas limpios, mapa base)
    for tiles, pri, pose, num in extra:
        if (tiles, pri) in directory:
            continue
        pmap[len(poses)] = ([omaps[num][0]], omaps[num][2])
        directory[(tiles, pri)] = [len(poses)]
        poses.append(pose)
    ctx['types'] = sorted(set(types))           # (sin el Rex: control de G4-B)
    ctx['omaps'] = omaps
    ctx['clean'], ctx['cdma'] = [], bytearray()
    ctx['ctype'] = []                           # G4-B: el tipo de cada limpia
    cindex = {}
    shapes = []
    seen = {}
    ctx['norm_dup'] = 0
    for (tiles, pri), variants in directory.items():
        t4 = [((dx & 255), (dy & 255), tile & 255, tile_flags(tile, size, fx, fy, pal))
              for dx, dy, tile, size, fx, fy, pal in tiles]
        if any(not -128 <= dx < 128 or not -128 <= dy < 128 for dx, dy, *_ in tiles):
            raise ValueError('ficha fuera de s8')
        if not clean:
            shapes.append((t4, pri, variants, 0, 0))
            continue
        # G5L-N: una forma por clave normalizada; la traslación tiene que
        # dar la misma imagen con el mismo origen relativo al mínimo
        t4n, mx, my = norm_key(t4)
        pose0 = poses[variants[0]]
        org = (pose0['origin'][0] - mx, pose0['origin'][1] - my)
        img = color_image(pose0)                # colores, no los índices del banco
        k = (tuple(t4n), pri)
        if k in seen:
            o2, img2 = seen[k]
            if o2 != org or img2 != img:
                raise ValueError('traslación con otra imagen u origen')
            ctx['norm_dup'] += 1
            continue
        seen[k] = (org, img)
        shapes.append((t4n, pri, variants, mx, my))
    vblob = bytearray()
    voff = {}
    mfix = []                                   # (en vblob, offset en vblob del bloque)
    if clean:
        for k, (t4, pri, variants, mx, my) in enumerate(shapes):
            names = []
            p0 = poses[variants[0]]
            p0 = dict(p0, origin=[p0['origin'][0] - mx, p0['origin'][1] - my])
            cmaps, mbase = pmap.get(variants[0], (CLEAN_MAPS, 0))
            # el bloque de máscaras de la forma: un color por máscara, con
            # los píxeles del mapa 0 (la misma imagen en los 4 mapas)
            c0 = clean_pose(p0, cmaps[0])
            colors = sorted({c for row in c0['row_maps'] for _, _, _, c in row})
            if len(vblob) & 1:
                vblob.append(0)
            mblk = len(vblob)
            for c in colors:
                vblob += pose_mask(c0, cmaps[0][c])
            for mi, cmap in enumerate(cmaps):
                cp = clean_pose(p0, cmap)
                offs = clean_streams(cp, ctx['cdma'], cindex)
                ck = len(ctx['clean'])
                ctx['clean'].append(cp)
                ctx['ctype'].append(G5L_OTHER[mbase - 4] if mbase else 0xAB)
                if len(vblob) & 1:
                    vblob.append(0)
                voff['c%d' % ck] = len(vblob)
                rec = bytearray(variant_record(cp, None, 0x8000 | ck, [
                    (o0 | CLEAN_FLAG, o1 | CLEAN_FLAG) for o0, o1 in offs], (0, colors)))
                rec[7] |= (mbase + mi) << 4       # G4-B: el orden de sus colores propios
                at = 12 + 8 * cp_cols(cp) + 8 * rec[9]
                mfix.append((len(vblob) + at, mblk))
                vblob += rec
                names.append('c%d' % ck)
            shapes[k] = (t4, pri, names)        # G5L-R: solo la limpia
    else:
        shapes = [(t4, pri, v) for t4, pri, v, _, _ in shapes]
    # G5L3: detrás de las cubetas, los órdenes de los colores propios (16 x
    # 16 B: índices, 0 al final; mapas 0-3 del Rex, 4 + i de G5L_OTHER[i])
    # y los tipos de la captura (256 bits)
    oo = 16 + 2 * NHASH
    sbase = oo + 16 * NORDS + 32
    vbase = sbase + sum(6 + 4 * len(t4) + 4 * len(v) for t4, _, v in shapes)
    blob = bytearray(sbase)
    struct.pack_into('>4sHHHH', blob, 0, b'G5L3', len(shapes), len(poses), NHASH, oo)
    for m, perm in enumerate(CLEAN_PERMS):
        blob[oo + 16 * m:oo + 16 * m + len(perm)] = bytes(perm)
    for num, (_, idx, m) in omaps.items():
        blob[oo + 16 * m:oo + 16 * m + len(idx)] = bytes(idx)
    for num in ctx['types']:
        blob[oo + 16 * NORDS + (num >> 3)] |= 1 << (num & 7)
    heads = [0] * NHASH
    for t4, pri, variants in shapes:
        h = key_hash(t4)
        at = len(blob)
        blob += struct.pack('>HBBH', heads[h], len(t4), pri, len(variants))
        for t in t4:
            blob += bytes(t)
        for n in variants:
            blob += struct.pack('>I', vbase + voff[n])
        heads[h] = at
    if len(blob) != vbase or vbase >= 65536:
        raise ValueError('formas fuera de los offsets .w')
    for h in range(NHASH):
        struct.pack_into('>H', blob, 16 + 2 * h, heads[h])
    for at, mblk in mfix:
        struct.pack_into('>I', vblob, at, vbase + mblk)
    blob += vblob
    if len(blob) & 1:
        blob.append(0)
    mo = len(blob)
    mt = R.mask_table(ctx['gfx'])
    for row in mt:
        blob += struct.pack('>8H', *row)
    struct.pack_into('>I', blob, 12, mo)
    # G5L-R: la misma tabla traspuesta (g5l_mfill), detrás: 744 .w offsets
    # (desde aquí) y por ficha .b n, n x (.b índice x 8, .b filas 0..7)
    tt = bytearray(2 * len(mt))
    for g, row in enumerate(mt):
        struct.pack_into('>H', tt, 2 * g, len(tt))
        pairs = []
        for i in range(1, 16):
            m = sum(1 << r for r in range(8) if row[r] >> i & 1)
            if m:
                pairs += [8 * i, m]
        tt += bytes([len(pairs) // 2] + pairs)
    if len(tt) >= 32768:
        raise ValueError('tabla traspuesta fuera de los offsets .w')
    blob += tt
    if len(blob) & 1:
        blob.append(0)
    return bytes(blob), ctx


class Table:
    def __init__(self, blob):
        self.b = blob
        magic, self.nshapes, self.nvar, nh, oo = struct.unpack_from('>4sHHHH', blob, 0)
        if magic != b'G5L3' or nh != NHASH:
            raise ValueError('tabla G5L desconocida')
        self.mo, = struct.unpack_from('>I', blob, 12)
        self.ords = [list(blob[oo + 16 * m:oo + 16 * m + 16].split(bytes(1))[0]) for m in range(NORDS)]
        tb = blob[oo + 16 * NORDS:oo + 16 * NORDS + 32]
        self.types = {n for n in range(256) if tb[n >> 3] >> (n & 7) & 1}

    def w(self, o):
        return struct.unpack_from('>H', self.b, o)[0]

    def lookup(self, t4, pri):
        o = self.w(16 + 2 * key_hash(t4))
        key = b''.join(bytes(t) for t in t4)
        while o:
            nxt, nt, p, nv = struct.unpack_from('>HBBH', self.b, o)
            if nt == len(t4) and p == pri and self.b[o + 6:o + 6 + 4 * nt] == key:
                return [struct.unpack_from('>I', self.b, o + 6 + 4 * nt + 4 * j)[0] for j in range(nv)]
            o = nxt
        return None

    def variant(self, o):
        ox, oy, w, h, cols, nidx, xmax, ng, n = struct.unpack_from('>hhBBBBBBH', self.b, o)
        omap, nidx = nidx >> 4, nidx & 15     # G5L3: el orden de los colores propios
        p = o + 12
        offs = [struct.unpack_from('>II', self.b, p + 8 * c) for c in range(cols)]
        groups = [struct.unpack_from('>BBHI', self.b, p + 8 * cols + 8 * j) for j in range(ng)]
        p += 8 * cols + 8 * ng
        mblk, = struct.unpack_from('>I', self.b, p)
        p += 4                                  # el bloque de máscaras (g5l_patch)
        runs = {}
        for _ in range(nidx):
            d, nr = self.b[p], self.b[p + 1]
            runs[d] = [struct.unpack_from('>BBH', self.b, p + 2 + 4 * j) for j in range(nr)]
            p += 2 + 4 * nr
            p += 2 + 4 * self.b[p]              # cambios (solo el 68000)
        return dict(ox=ox, oy=oy, w=w, h=h, cols=cols, xmax=xmax, offs=offs, runs=runs, n=n,
                    own=self.ords[omap], omap=omap,
                    groups=[(d, c, m) for d, _, c, m in groups], mblk=mblk,
                    midx=[k for _, k, _, _ in groups])

    def mask(self, v, g):
        """las máscaras del grupo g de la variante v (alto x columnas .w)"""
        n = v['h'] * v['cols']
        o = v['mblk'] + 2 * n * v['midx'][g]
        return list(struct.unpack_from('>%dH' % n, self.b, o))

    def tmask(self, gtile, row):
        return self.w(self.mo + 16 * gtile + 2 * row)


# ----------------------------------------------------------------------
# entradas de la foto
# ----------------------------------------------------------------------
def s8(v):
    return ((v + 128) & 255) - 128


def s16(v):
    return ((v + 32768) & 65535) - 32768


def mario_entries(moam, mosz):
    """como mspr.c mario_sprite(): (ex, ey, tile, attr, nt) o None si no se dibuja"""
    ents = []
    for e in range(4):
        x, y, tile, attr = moam[4 * e:4 * e + 4]
        if y == 0xF0:
            continue
        ex = x | (mosz[e] & 1) << 8
        if ex >= 256:
            ex -= 512
        ey = y - 256 if y >= 0xF0 else y
        ents.append((ex, ey, tile, attr, 2 if mosz[e] & 2 else 1))
    if not ents:
        return None
    bx = min(e[0] for e in ents)
    by = min(e[1] for e in ents)
    x1 = max(e[0] + 8 * e[4] for e in ents)
    y1 = max(e[1] + 8 * e[4] for e in ents)
    if x1 - bx > 32 or y1 - by > 40:
        return None
    return ents


def vram_gtile(ptrs, t):
    """mspr.c vram_tile -> ficha de GFX32 o None. ptrs = RAM $0D85..$0D9A"""
    if t == 0x7F:
        p = ptrs[20] | ptrs[21] << 8
    elif t < 0x20 and (t & 15) < 10:
        o = (10 if t >> 4 else 0) + ((t & 15) >> 1) * 2
        p = (ptrs[o] | ptrs[o + 1] << 8) + (t & 1) * 32
    else:
        return None
    if p < 0x2000 or p > 0x2000 + 0x5D00 - 32:
        return None
    return (p - 0x2000) >> 5


def mario_rows(tab, ents, ptrs, clip=True):
    """{fila del copper: máscara}, borde derecho (o -1). clip=False: también
    las filas fuera de la pantalla (el 68000 cuenta así el límite de tramos)"""
    rows = collections.Counter()
    xm = -1
    for ex, ey, tile, attr, nt in ents or ():
        hf, vf = attr >> 6 & 1, attr >> 7
        xm = max(xm, min(255, ex + 8 * nt - 1))
        for ty in range(nt):
            for tx in range(nt):
                g = vram_gtile(ptrs, (tile + (nt - 1 - tx if hf else tx) + 16 * (nt - 1 - ty if vf else ty)) & 255)
                if g is None:
                    continue
                for r in range(8):
                    R = ey + 1 + 8 * ty + r
                    if 0 <= R < ROWS or not clip:
                        rows[R] |= tab.tmask(g, 7 - r if vf else r)
    return {r: m for r, m in rows.items() if m}, xm


def rex_key(entries, sx, sy):
    t4, pris = [], set()
    for x, y, tile, attr, hi in entries:
        t4.append(((x - sx) & 255, (y - sy) & 255, tile,
                   (attr & 1) | (hi & 2) | (attr >> 6 & 1) << 2 | (attr >> 7) << 3 | ((attr >> 1) & 7) << 4))
        pris.add(attr >> 4 & 3)
    return t4, (pris.pop() if len(pris) == 1 else None)


# ----------------------------------------------------------------------
# el plan
# ----------------------------------------------------------------------
class Stats(collections.Counter):
    pass


def plan_frame(photo, tab, colors, lst, st, seen=None):
    """photo: pal, moam, mosz, ptrs, camx, camy, rex=[(slot, x, y, entries)]
    lst: nb[s], has_loads(s), walk(s) -> (last, free, J)
    seen: lista a la que se agrega (slot, estado) de cada objeto (G4-B)
    Devuelve dict(rex=..., vbl=[(i, color)], segs={s: (forma, moves)}, chans=[...]) o None."""
    if seen is None:
        seen = []
    ents = mario_entries(photo['moam'], photo['mosz'])
    mrow, xm = mario_rows(tab, ents, photo['ptrs'])
    mruns = mario_runs(mrow)
    # el Rex visible más alto
    best = None
    for slot, x, y, entries in photo['rex']:
        sx, sy = s16(x - photo['camx']), s16(y - photo['camy'])
        t4, pri = rex_key(entries, sx, sy)
        if pri is None:
            st['rex_prio_mixta'] += 1
            seen.append((slot, 'prio_mixta'))
            continue
        t4, mx, my = norm_key(t4)               # G5L-N (g5l_choose)
        sx, sy = sx + mx, sy + my
        vs = tab.lookup(t4, pri)
        if vs is None:
            st['rex_sin_forma'] += 1
            seen.append((slot, 'sin_forma'))
            continue
        v0 = tab.variant(vs[0])
        x0, r0 = sx + v0['ox'], sy + v0['oy'] + 1
        if not (r0 + v0['h'] > 0 and r0 < ROWS and x0 + v0['w'] > 0 and x0 < 256):
            continue
        seen.append((slot, 'en_pantalla'))
        if best is None or (r0, slot) < (best[0], best[1]):
            best = (r0, slot, x0, vs)
    if best is None:
        return None
    r0, slot, x0, vs = best
    # la variante limpia que menos choca (la primera si empatan); si no
    # encuentra banda, la siguiente en ese orden
    cands = sorted((band_need(tab.variant(vo), r0, mrow, colors), m, vo) for m, vo in enumerate(vs))
    asg = None
    for n, m, vo in cands:
        v = tab.variant(vo)
        asg = band_assign(v, r0, mrow, colors)
        if asg is not None:
            break
        st['reintento'] += 1
    if asg is None:
        st['sin_indice'] += 1
        st['sin_plan'] += 1
        seen.append((slot, 'sin_indice'))
        return None
    groups, remaps = asg
    st['remap_%d' % len(remaps)] += 1
    st['mapa_%d' % m] += 1
    v2 = dict(v, runs=group_runs(groups))
    trans = sweep(v2, r0, mruns, colors)
    if trans is None:
        raise AssertionError('A3 tras band_assign')
    xr = min(255, x0 + v['xmax'])
    E = (0, xm + 1, xr + 1, max(xm, xr) + 1)
    res = place(trans, lst, E, st)
    if res is None:
        st['sin_plazo'] += 1
        st['sin_plan'] += 1
        seen.append((slot, 'sin_plazo'))
        return None
    vbl, segs = res
    return dict(slot=slot, vo=vo, var=v, x0=x0, r0=r0, E=E, trans=trans, vbl=vbl, segs=segs,
                groups=groups, remaps=remaps)


# Orden fijo de los índices destino de una banda: los que Mario no usa
# nunca (7, 15) y después de menos a más filas de Mario cuando se cruza
# con un Rex en yi1 (medido; ordenarlos por frame según las filas de la
# ventana daba la misma cobertura y costaba 13 máscaras por frame)
BAND_PREF = [7, 15, 4, 6, 14, 9, 13, 8, 12, 11, 5, 10, 3]


def band_need(v, r0, mrow, colors):
    """cuántos colores del Rex chocan con Mario en su índice (band_assign
    los tendría que pasar a una banda): en pantalla, otro color en Mario"""
    vis = sum(1 << r for r in range(v['h']) if 0 <= r0 + r < ROWS)
    n = 0
    for d, c, m in v['groups']:
        if d in (1, 2) or colors[d] == c:
            continue
        if any(mrow.get(r0 + r, 0) >> d & 1 for r in range(v['h']) if (m & vis) >> r & 1):
            n += 1
    return n


def band_assign(v, r0, mrow, colors):
    """G5L-R: ({(índice, color): filas relativas a r0}, [(ic, f, filas, color)])
    o None. Por color propio (REXC, en ese orden): K = sus filas en que Mario usa su
    índice con otro color. Si hay, se lo pasa a otro índice f en una banda
    (todas sus filas; si no, desde la primera de K; si no, de la primera a la
    última de K): f el primero de BAND_PREF que Mario no use en la banda (o
    con ese color) y que el Rex no ocupe en la banda. Solo filas en pantalla."""
    h = v['h']
    vis = sum(1 << r for r in range(h) if 0 <= r0 + r < ROWS)
    mw = [0] * 16
    for r in range(h):
        m = mrow.get(r0 + r, 0)
        for i in range(16):
            if m >> i & 1:
                mw[i] |= 1 << r
    groups = collections.OrderedDict()
    occ = [0] * 16
    cmap = {}
    for d, c, m in v['groups']:
        cmap[d] = c
        if m & vis:
            groups[d, c] = m & vis
            occ[d] |= m & vis
    remaps = []
    for ic in v['own']:                         # G4-B: REXC en el orden del mapa
        if ic not in cmap:
            continue
        c = cmap[ic]
        if colors[ic] == c:
            continue
        rc = groups.get((ic, c), 0)
        k = rc & mw[ic]
        if not k:
            continue
        lo = (k & -k).bit_length() - 1
        hi = k.bit_length() - 1
        f = None
        for b in (rc, rc & ~((1 << lo) - 1), rc & ((1 << (hi + 1)) - 1) & ~((1 << lo) - 1)):
            for g in BAND_PREF:
                if g == ic or ((mw[g] & b) and colors[g] != c) or occ[g] & b:
                    continue
                f = g
                break
            if f is not None:
                break
        if f is None:
            return None
        groups[ic, c] &= ~b
        if not groups[ic, c]:
            del groups[ic, c]
        groups[f, c] = groups.get((f, c), 0) | b
        occ[ic] &= ~b
        occ[f] |= b
        remaps.append((ic, f, b, c))
    return groups, remaps


def group_runs(groups):
    runs = collections.defaultdict(list)
    for (i, c), m in groups.items():
        r = 0
        while m >> r:
            if m >> r & 1:
                a = r
                while m >> (r + 1) & 1:
                    r += 1
                runs[i].append((a, r, c))
            r += 1
    for i in runs:
        runs[i].sort()
    return dict(runs)


RSTRIDE = 136                   # un flujo del búfer: POS/CTL, 32 filas, fin


def remap_halves(remaps):
    """bit h: la mitad h (planos 2h, 2h+1) de cada columna cambia con alguna
    banda: esos flujos van al búfer; los demás, al banco limpio"""
    hm = 0
    for ic, f, _, _ in remaps:
        x = ic ^ f
        hm |= (1 if x & 3 else 0) | (2 if x & 12 else 0)
    return hm


def remap_rows(pose, remaps):
    """las filas de la pose limpia con los índices de las bandas"""
    rows = [list(r) for r in pose['rows']]
    for ic, f, b, _ in remaps:
        for r in range(len(rows)):
            if b >> r & 1:
                rows[r] = [f if (d == ic and o == ic) else d for d, o in zip(rows[r], pose['rows'][r])]
    return rows


def rbuf_streams(pose, remaps):
    """los flujos del búfer de chip (columna, mitad) como los escribe g5l_patch"""
    rows = remap_rows(pose, remaps)
    h, w = pose['height'], pose['width']
    out = []
    for c in range((w + 15) // 16):
        for half in range(2):
            b = bytearray(4)
            for r in range(h):
                wa = wb = 0
                for x in range(16):
                    xx = 16 * c + x
                    v = rows[r][xx] if xx < w else 0
                    wa |= ((v >> (2 * half)) & 1) << (15 - x)
                    wb |= ((v >> (2 * half + 1)) & 1) << (15 - x)
                b += struct.pack('>HH', wa, wb)
            b += bytes(4)
            out.append(bytes(b))
    return out


def remap_pose(pose, remaps):
    """la pose con los índices reasignados (para la comprobación de color)"""
    rows = remap_rows(pose, remaps)
    maps = []
    for r in range(pose['height']):
        rm = []
        for p_, i_, d, c in pose['row_maps'][r]:
            for ic, f, b, _ in remaps:
                if d == ic and b >> r & 1:
                    d = f
                    break
            rm.append((p_, i_, d, c))
        maps.append(rm)
    return dict(pose, rows=rows, row_maps=maps)


def mario_runs(mrow):
    """{índice: [(fila primera, fila última)]} de Mario (filas del copper)"""
    runs = collections.defaultdict(list)
    for r in sorted(mrow):
        m = mrow[r]
        for i in range(1, 16):
            if m >> i & 1:
                rr = runs[i]
                if rr and rr[-1][1] == r - 1:
                    rr[-1] = (rr[-1][0], r)
                else:
                    rr.append((r, r))
    return dict(runs)


def sweep(v, r0, mruns, colors):
    """Transiciones (índice, color, desde, dueños, hasta) o None si A3 falla.

    Por índice: los tramos del Rex (recortados a la pantalla) y los de
    Mario en orden de fila; una transición donde cambia el color pedido,
    desde el último uso anterior. A3: un tramo de otro color que se solapa
    con lo anterior. Orden: índice, después fila (el del 68000)."""
    out = []
    for i in range(1, 16):
        rx = []
        for a, b, c in v['runs'].get(i, ()):
            a, b = max(0, r0 + a), min(ROWS - 1, r0 + b)
            if a <= b:
                rx.append((a, b, c, 2))
        if not any(c != colors[i] for _, _, c, _ in rx):
            continue
        ms = [(a, b, colors[i], 1) for a, b in mruns.get(i, ())]
        cur, last, own = colors[i], -1, 0
        im = ir = 0
        while im < len(ms) or ir < len(rx):
            if ir >= len(rx) or (im < len(ms) and ms[im][0] <= rx[ir][0]):
                a, b, c, o = ms[im]
                im += 1
            else:
                a, b, c, o = rx[ir]
                ir += 1
            if c != cur:
                if last >= a:
                    return None
                out.append((i, c, last, own, a))
                cur = c
            if b > last:
                last, own = b, o
            elif b == last:
                own |= o
    return out


def place(trans, lst, E, st):
    """(vbl, segs) o None. segs[s] = ('blind'|forma de schedule, [(i, color, need)])"""
    vbl = []
    moves = collections.defaultdict(list)       # s -> [(i, color, desde)]
    order = []                                   # segmentos abiertos, en orden
    caps = {}

    def blind(s):
        if s not in caps:
            if s == WRAP_SEG or s + 1 >= ROWS:
                caps[s] = 0
            else:
                nb1 = lst.nb[s + 1]
                c = (10 if lst.has_loads(s) else 12) - nb1 if nb1 in (7, 8, 9) else 0
                caps[s] = max(0, c)
        return caps[s]
    missed = []
    # ventanas más cortas primero (como g2t_ref.place); estable
    order_t = sorted(trans, key=lambda t: min(t[4] - t[2], 4) if t[2] >= 0 else 0)
    for i, color, desde, own, hasta in order_t:
        if desde == -1 and len(vbl) < VBL_COLORS:
            vbl.append((i, color))
            continue
        lo, hi = max(desde, 0), hasta - 1
        pick = None
        for s in order:
            if lo <= s <= hi and len(moves[s]) < blind(s) and (pick is None or s > pick):
                pick = s
        if pick is None:
            for s in range(hi, lo - 1, -1):
                if s not in moves and blind(s) > 0:
                    pick = s
                    order.append(s)
                    break
        if pick is None:
            missed.append((i, color, desde, own, hasta))
            continue
        moves[pick].append((i, color, desde, own))
    for s in order:
        assert len(moves[s]) <= blind(s)
    walked = {}

    def need(m, s):
        return E[m[3]] if m[2] == s else 0
    for i, color, desde, own, hasta in missed:
        st['pase2'] += 1
        lo, hi = max(desde, 0), hasta - 1
        ok = False
        for s in range(hi, lo - 1, -1):
            if s not in walked:
                walked[s] = lst.walk(s)
                st['recorridos'] += 1
            last, free, _ = walked[s]
            trial = moves[s] + [(i, color, desde, own)]
            trial.sort(key=lambda m: need(m, s))
            if s + 1 < ROWS and schedule(s, last, free, lst.nb[s + 1], [need(m, s) for m in trial]):
                if s not in order:
                    order.append(s)
                moves[s] = trial
                ok = True
                break
        if not ok:
            return None
    segs = {}
    for s in order:
        ms = moves[s]
        if s in walked:
            ms = sorted(ms, key=lambda m: need(m, s))
            last, free, _ = walked[s]
            form = schedule(s, last, free, lst.nb[s + 1], [need(m, s) for m in ms])
            if form is None:
                if len(ms) > blind(s):
                    raise AssertionError('plan inestable')
                ms = moves[s]
                form = ('blind',)
        else:
            form = ('blind',)
        segs[s] = (form, [(i, c, need((i, c, d, o), s)) for i, c, d, o in ms])
    return vbl, segs


def suffix_words(s, form, ms):
    words = []
    if form[0] == 'blind':
        words.append((((s + V0) & 255) << 8 | 0xD1, 0xFFFE))
    elif form[0] == 'wait':
        words.append((((s + V0) & 255) << 8 | form[1] | 1, 0xFFFE))
    else:
        words += [(MOVE_PAD, 0)] * form[1]
    words += [(0x01A0 + 2 * i, c) for i, c, _ in ms]
    return words


def positions(s, form, ms):
    """x de cada MOVE para la simulación (999 = en el borrado, tras x = 255)"""
    if form[0] == 'blind':
        return [999] * len(ms)
    return [999 if x >= 256 else x for x in form[2]]


def control(x, start, stop, channel):
    hp = 0xA0 + x
    return ((start & 255) << 8 | (hp >> 1),
            (stop & 255) << 8 | (0x80 if channel & 1 else 0) | ((start >> 8) << 2) | ((stop >> 8) << 1) | (hp & 1))


def channels(p, dma, cdma=0, rbuf=0):
    """[(pt, pos, ctl)] de SPR4-7; None = canal nulo. Los offsets con
    CLEAN_FLAG son del banco de las variantes limpias (cdma); con bandas,
    el búfer de esta lista (rbuf, RSTRIDE por flujo)"""
    out = [None] * 4
    if p is None:
        return out
    v, x0, r0 = p['var'], p['x0'], p['r0']
    clip = max(0, -r0)
    for c in range(v['cols']):
        hx = x0 + 16 * c
        if not (r0 + v['h'] > 0 and r0 < ROWS and -16 < hx < 256):
            continue
        for half in range(2):
            ch = 4 + 2 * c + half
            pos, ctl = control(hx, V0 + max(r0, 0), V0 + r0 + v['h'], ch)
            if remap_halves(p.get('remaps') or ()) >> half & 1:
                out[2 * c + half] = (rbuf + RSTRIDE * (2 * c + half) + 4 + 4 * clip, pos, ctl)
                continue
            off = v['offs'][c][half]
            base = cdma if off & CLEAN_FLAG else dma
            out[2 * c + half] = (base + (off & ~CLEAN_FLAG) + 4 + 4 * clip, pos, ctl)
    return out


# ----------------------------------------------------------------------
# comprobación sobre las trazas del oráculo (lista del scroll simulada)
# ----------------------------------------------------------------------
class SimList:
    def __init__(self, mem, base, syms, ldoff):
        self.mem, self.base, self.syms = mem, base, syms
        self.nb = [(o - 8) // 4 for o in ldoff]
        self.ldoff = ldoff

    def seg(self, s):
        return self.base + self.syms['CL_LINES'] + self.syms['SEG'] * s

    def has_loads(self, s):
        return self.mem.r16(self.seg(s) + self.ldoff[s]) != JUMP

    def walk(self, s):
        a = self.seg(s) + self.ldoff[s]
        T = T0 + max(0, 16 * (self.nb[s] - 9))
        free, last = T, None
        while True:
            w = self.mem.r16(a)
            if w == JUMP:
                return last, free, a
            if w & 1:
                T = max(adv(T, 2), xh(w & 0xFE))
            else:
                last = T
                T = adv(T)
            a += 4


def trace_photo(recs, ctx):
    """foto equivalente desde el oráculo: Mario de la OAM SNES (como mario_amiga)"""
    import g5ref as R
    ram = recs[0]['ram']
    recorded = recs[0]['recorded']
    dyn = R.dynamic_tiles(ram, len(ctx['gfx']))
    moam, mosz = bytearray([0, 0xF0, 0, 0] * 4), bytearray(4)
    k = 0
    for x, y, tile, attr, hi in recorded:
        if (attr >> 1) & 7 or attr & 1 or tile not in dyn or y == 0xF0:
            continue
        if k < 4:
            moam[4 * k:4 * k + 4] = bytes((x, y, tile, attr))
            mosz[k] = hi & 3
        k += 1
    rex = []
    for r in recs:
        if r['num'] not in ctx['types']:         # G4-B: los tipos de la tabla
            continue
        ents = []
        for dx, dy, tile, size, fx, fy, pal in r['tiles']:
            attr = (tile >> 8) | pal << 1 | fx << 6 | fy << 7 | r['priority'] << 4
            ents.append(((r['sx'] + dx) & 255, (r['sy'] + dy) & 255, tile & 255, attr, 2 if size == 16 else 0))
        rex.append((r['slot'], r['sx'], r['sy'], ents))
    return dict(moam=bytes(moam), mosz=bytes(mosz), ptrs=ram[0xD85:0xD9B], camx=0, camy=0,
                rex=rex, nmario=k)


def check_trace(p, recs, ctx, colors):
    """errores de color de cada píxel de Mario y del Rex elegido (g2t_ref.simulate)"""
    import g2t_ref as T
    import sprgfx_bank as B
    chosen = [r for r in recs if r['num'] in ctx['types'] and r['slot'] == p['slot']][0]
    ram, recorded = chosen['ram'], chosen['recorded']
    mario, _, _, _ = T.mario_check(ram, recorded, ctx['gfx'])
    poses = ctx['poses']
    n = p['var']['n']
    pose = ctx['clean'][n & 0x7FFF] if n & 0x8000 else poses[n]
    pose = remap_pose(pose, p['remaps'])
    x0, r0 = p['x0'], p['r0']
    uses = T.uses_of(pose, x0, r0, mario, colors)
    trans = []
    for i, c in p['vbl']:
        trans.append(dict(indice=i, valor=c, segmento=-1, x=None))
    for s, (form, ms) in p['segs'].items():
        for (i, c, _), x in zip(ms, positions(s, form, ms)):
            trans.append(dict(indice=i, valor=c, segmento=s, x=x))
    rexpix = {}
    for r, row in enumerate(pose['rows']):
        cmap = {d: c for _, _, d, c in pose['row_maps'][r]}
        for x, d in enumerate(row):
            if d and 0 <= x0 + x < 256 and 0 <= r0 + r < ROWS:
                rexpix[x0 + x, r0 + r] = (d, cmap[d])
    env = T.simulate(uses, trans, colors)
    pix, _ = T.pixel_errors(mario, rexpix, trans, colors)
    return len(env) + pix


# ----------------------------------------------------------------------
# G4-1: varios Rex por foto (solo la referencia; el 68000 sigue con
# plan_frame hasta G4-2). docs/instrucciones-g4-1.md
# ----------------------------------------------------------------------
class EMap:
    """Bordes por dueños: bit 0 Mario, bit j + 1 el Rex j. E[m] = el mayor
    borde derecho + 1 de los dueños de m (0 sin dueños). Con un Rex es la
    tupla (0, xm + 1, xr + 1, max + 1) de plan_frame."""
    def __init__(self, xs):
        self.x = list(xs)

    def __getitem__(self, m):
        if not m:
            return 0
        return max(self.x[k] for k in range(len(self.x)) if m >> k & 1) + 1


def mario_occ(mrow, colors):
    """ocupación de los índices por fila: occ[i][fila] = color (Mario)"""
    occ = [dict() for _ in range(16)]
    for r, m in mrow.items():
        for i in range(1, 16):
            if m >> i & 1:
                occ[i][r] = colors[i]
    return occ


def occ_bad(occ, i, c, r0, h):
    """filas (bits relativos a r0) en que otro usa el índice i con otro color"""
    o, b = occ[i], 0
    for r in range(h):
        col = o.get(r0 + r)
        if col is not None and col != c:
            b |= 1 << r
    return b


def band_need_n(v, r0, occ):
    """band_need con la ocupación de Mario y de los Rex ya ubicados"""
    vis = sum(1 << r for r in range(v['h']) if 0 <= r0 + r < ROWS)
    n = 0
    for d, c, m in v['groups']:
        if d in (1, 2):
            continue
        if occ_bad(occ, d, c, r0, v['h']) & m & vis:
            n += 1
    return n


def band_assign_n(v, r0, occ):
    """band_assign con la ocupación general (solo Mario: el mismo resultado)"""
    h = v['h']
    vis = sum(1 << r for r in range(h) if 0 <= r0 + r < ROWS)
    groups = collections.OrderedDict()
    own = [0] * 16
    cmap = {}
    for d, c, m in v['groups']:
        cmap[d] = c
        if m & vis:
            groups[d, c] = m & vis
            own[d] |= m & vis
    remaps = []
    for ic in v['own']:                         # G4-B: REXC en el orden del mapa
        if ic not in cmap:
            continue
        c = cmap[ic]
        rc = groups.get((ic, c), 0)
        k = rc & occ_bad(occ, ic, c, r0, h)
        if not k:
            continue
        lo = (k & -k).bit_length() - 1
        hi = k.bit_length() - 1
        f = None
        for b in (rc, rc & ~((1 << lo) - 1), rc & ((1 << (hi + 1)) - 1) & ~((1 << lo) - 1)):
            for g in BAND_PREF:
                if g == ic or occ_bad(occ, g, c, r0, h) & b or own[g] & b:
                    continue
                f = g
                break
            if f is not None:
                break
        if f is None:
            return None
        groups[ic, c] &= ~b
        if not groups[ic, c]:
            del groups[ic, c]
        groups[f, c] = groups.get((f, c), 0) | b
        own[ic] &= ~b
        own[f] |= b
        remaps.append((ic, f, b, c))
    return groups, remaps


def sweep_n(objs, mruns, colors):
    """sweep con varios Rex: objs = [(runs, r0)], dueño 2 << j. Mismo orden
    de mezcla (Mario primero si empatan, después los Rex en su orden)."""
    out = []
    for i in range(1, 16):
        rx = []
        for j, (runs, r0) in enumerate(objs):
            for a, b, c in runs.get(i, ()):
                a, b = max(0, r0 + a), min(ROWS - 1, r0 + b)
                if a <= b:
                    rx.append((a, 1 + j, b, c, 2 << j))
        if not any(c != colors[i] for _, _, _, c, _ in rx):
            continue
        ms = [(a, 0, b, colors[i], 1) for a, b in mruns.get(i, ())]
        cur, last, own = colors[i], -1, 0
        for a, _, b, c, o in sorted(ms + rx):
            if c != cur:
                if last >= a:
                    return None
                out.append((i, c, last, own, a))
                cur = c
            if b > last:
                last, own = b, o
            elif b == last:
                own |= o
    return out


def occ_add(occ, groups, r0):
    for (i, c), m in groups.items():
        r = 0
        while m >> r:
            if m >> r & 1 and 0 <= r0 + r < ROWS:
                occ[i][r0 + r] = c
            r += 1


G5L_MAXPL = 2                   # G4-2: Rex ubicados por foto (el búfer de cadena)
CSTRIDE = 264                   # un flujo de cadena: 2 x 32 filas, POS/CTL, fin
LBLK = 4 * (2 * RSTRIDE + CSTRIDE)  # por lista: bandas del Rex 0 y 1, cadena


def plan_frame_n(photo, tab, colors, lst, st, maxrex=G5L_MAXPL):
    """G4-1/G4-2: varios Rex por foto. Los visibles en orden (fila, ranura):
    uno entra si está separado del último ubicado por una línea libre (los
    pares 4-5 y 6-7 se reusan en vertical por encadenado DMA; así la columna
    c va siempre al par c) y quedan menos de maxrex; si no, bob 'canal'. Los
    colores, con la ocupación de Mario y de los ya ubicados (al no compartir
    filas, la de Mario sola); si no hay variante, bob 'color'. Después las
    transiciones de todos (sweep_n) y place; si no entra, el último ubicado
    pasa a bob 'plazo' y se repite (el 68000, player/g5l.s g5l_render).
    Devuelve dict(rex=[...], trans, vbl, segs, E, bobs) o None si no hay
    ningún Rex visible."""
    ents = mario_entries(photo['moam'], photo['mosz'])
    mrow, xm = mario_rows(tab, ents, photo['ptrs'])
    mruns = mario_runs(mrow)
    cands = []
    for slot, x, y, entries in photo['rex']:
        sx, sy = s16(x - photo['camx']), s16(y - photo['camy'])
        t4, pri = rex_key(entries, sx, sy)
        if pri is None:
            st['rex_prio_mixta'] += 1
            continue
        t4, mx, my = norm_key(t4)
        sx, sy = sx + mx, sy + my
        vs = tab.lookup(t4, pri)
        if vs is None:
            st['rex_sin_forma'] += 1
            continue
        v0 = tab.variant(vs[0])
        x0, r0 = sx + v0['ox'], sy + v0['oy'] + 1
        if not (r0 + v0['h'] > 0 and r0 < ROWS and x0 + v0['w'] > 0 and x0 < 256):
            continue
        cands.append((r0, slot, x0, vs))
    if not cands:
        return None
    cands.sort(key=lambda t: (t[0], t[1]))
    occ = mario_occ(mrow, colors)
    placed, bobs = [], []
    lastb = None
    for r0, slot, x0, vs in cands:
        v0 = tab.variant(vs[0])
        a, b = max(r0, 0), min(ROWS, r0 + v0['h'])
        if placed and (len(placed) >= maxrex or a <= lastb):
            bobs.append((slot, 'canal'))
            continue
        order = sorted((band_need_n(tab.variant(vo), r0, occ), m, vo) for m, vo in enumerate(vs))
        asg = None
        for n, m, vo in order:
            v = tab.variant(vo)
            asg = band_assign_n(v, r0, occ)
            if asg is not None:
                break
            st['reintento'] += 1
        if asg is None:
            bobs.append((slot, 'color'))
            continue
        groups, remaps = asg
        placed.append(dict(slot=slot, vo=vo, var=v, x0=x0, r0=r0, groups=groups, remaps=remaps,
                           mapa=m, pares=list(range(v0['cols']))))
        occ_add(occ, groups, r0)
        lastb = b
    best = None
    while placed:
        objs = [(group_runs(q['groups']), q['r0']) for q in placed]
        trans = sweep_n(objs, mruns, colors)
        if trans is None:
            raise AssertionError('A3 tras band_assign_n')
        E = EMap([xm] + [min(255, q['x0'] + q['var']['xmax']) for q in placed])
        res = place(trans, lst, E, collections.Counter())
        if res is not None:
            best = (trans, res, E)
            break
        bobs.append((placed.pop()['slot'], 'plazo'))
    if not placed:
        st['sin_plan'] += 1
        return dict(rex=[], trans=[], vbl=[], segs={}, E=None, bobs=bobs)
    trans, (vbl, segs), E = best
    for q in placed:
        st['remap_%d' % len(q['remaps'])] += 1
        st['mapa_%d' % q['mapa']] += 1
    return dict(rex=placed, trans=trans, vbl=vbl, segs=segs, E=E, bobs=bobs, slot=placed[0]['slot'])


def channels_n(rex, cdma, lbase):
    """G4-2: [(pt, pos, ctl)] de SPR4-7 (None = nulo) y las cadenas
    {flujo: (dirección, [(filas, n), (pos, ctl), (filas, n)])}. El flujo s
    = 2c + mitad lleva la columna c de cada Rex que la tiene en pantalla:
    uno solo, desde su fuente (banco limpio o sus bandas en lbase + 4 x
    RSTRIDE x k); dos, encadenados en lbase + 8 x RSTRIDE + CSTRIDE x s
    (sus filas, POS/CTL del segundo, sus filas, fin)"""
    out, chains = [None] * 4, {}
    for s in range(4):
        c, half = s >> 1, s & 1
        pres = []
        for k, q in enumerate(rex):
            v, x0, r0 = q['var'], q['x0'], q['r0']
            hx = x0 + 16 * c
            if c >= v['cols'] or not -16 < hx < 256:
                continue
            clip = max(0, -r0)
            pos, ctl = control(hx, V0 + max(r0, 0), V0 + r0 + v['h'], 4 + s)
            if remap_halves(q['remaps']) >> half & 1:
                src = lbase + 4 * RSTRIDE * k + RSTRIDE * s
            else:
                off = v['offs'][c][half]
                assert off & CLEAN_FLAG
                src = cdma + (off & ~CLEAN_FLAG)
            pres.append((src + 4 + 4 * clip, pos, ctl, v['h'] - clip))
        if len(pres) == 1:
            out[s] = pres[0][:3]
        elif pres:
            (p1, pos1, ctl1, n1), (p2, pos2, ctl2, n2) = pres
            C = lbase + 8 * RSTRIDE + CSTRIDE * s
            chains[s] = (C, [(p1, n1), (pos2, ctl2), (p2, n2)])
            out[s] = (C, pos1, ctl1)
    return out, chains


def check_trace_n(p, recs, ctx, colors):
    """errores de color de cada píxel de Mario y de todos los Rex ubicados,
    y píxeles de Rex que se tapan entre sí (prioridad: el primero ubicado)"""
    import g2t_ref as T
    chosen = [r for r in recs if r['num'] in ctx['types']][0]
    ram, recorded = chosen['ram'], chosen['recorded']
    mario, _, _, _ = T.mario_check(ram, recorded, ctx['gfx'])
    uses = collections.defaultdict(dict)

    def add(x, rr, i, color):
        if not (0 <= x < 256 and 0 <= rr < ROWS):
            return
        u = uses[rr].get(i)
        if u is None:
            uses[rr][i] = dict(color=color, first=x, last=x, owners=set())
        else:
            if u['color'] != color:
                raise AssertionError('índice con dos colores en la fila (A3)')
            u['first'], u['last'] = min(u['first'], x), max(u['last'], x)
    for (x, rr), i in mario.items():
        add(x, rr, i, colors[i])
    rexpix, tapados = {}, 0
    for q in p['rex']:
        n = q['var']['n']
        pose = ctx['clean'][n & 0x7FFF] if n & 0x8000 else ctx['poses'][n]
        pose = remap_pose(pose, q['remaps'])
        for r, row in enumerate(pose['rows']):
            cmap = {d: c for _, _, d, c in pose['row_maps'][r]}
            for x, d in enumerate(row):
                if not d:
                    continue
                gx, gy = q['x0'] + x, q['r0'] + r
                add(gx, gy, d, cmap[d])
                if 0 <= gx < 256 and 0 <= gy < ROWS:
                    if (gx, gy) in rexpix:
                        tapados += 1
                    else:
                        rexpix[gx, gy] = (d, cmap[d])
    trans = [dict(indice=i, valor=c, segmento=-1, x=None) for i, c in p['vbl']]
    for s, (form, ms) in p['segs'].items():
        for (i, c, _), x in zip(ms, positions(s, form, ms)):
            trans.append(dict(indice=i, valor=c, segmento=s, x=x))
    env = T.simulate(uses, trans, colors)
    pix, _ = T.pixel_errors(mario, rexpix, trans, colors)
    return len(env) + pix, tapados


def run_trace(a):
    import g2t_ref as T
    import g5ref as R
    import scrollprof as P
    types = parse_types(a.types)
    blob, ctx = build_table(a.bank, types=types)
    tab = Table(blob)
    code, lst = P.assemble('player/scroll.s', ['VIS=256', 'SPRITES'])
    syms, local = P.listing(lst)
    V = {n: v for n, v in syms.items() if n.startswith('V_')}
    summary = {}
    ok = True
    for name in a.traces:
        records = list(R.read_trace('work/%s_%s.trace' % (a.prefix, name), 'work/oracle_%s_oam.bin' % name))
        groups = collections.defaultdict(list)
        for r in records:
            groups[r['frame']].append(r)
        sc = P.Scroll(code, syms, local, Path('work/yi1_s.dat').read_bytes(), V)
        sc.init()
        ldoff = None
        st = Stats()
        tst = collections.defaultdict(Stats)
        for f in sorted(groups):
            recs = groups[f]
            ram = recs[0]['ram']
            sc.mem.w16(sc.vars + V['V_S'], ram[0x1a] | ram[0x1b] << 8)
            sc.call('scroll_frame')
            if not any(r['num'] in ctx['types'] for r in recs):
                continue
            base = sc.mem.r32(P.FAKE + 0x80)
            if ldoff is None:
                ldoff = sim_ldoff(sc.mem, base, syms)
            sl = SimList(sc.mem, base, syms, ldoff)
            photo = trace_photo(recs, ctx)
            pi = R.palette_index(ram, ctx['pointers'])
            colors = struct.unpack_from('>16H', ctx['pals'], 32 * pi)
            st['fotos'] += 1
            num = {r['slot']: r['num'] for r in recs if r['num'] in ctx['types']}
            if getattr(a, 'multi', False):
                run_multi_photo(photo, tab, colors, sl, st, recs, ctx, tst, num)
                continue
            seen = []
            p = plan_frame(photo, tab, colors, sl, st, seen)
            for slot, why in seen:                  # G4-B: por tipo
                tst['%02X' % num[slot]][why] += 1
                if why == 'en_pantalla' and (p is None or p['slot'] != slot):
                    tst['%02X' % num[slot]]['no_' + ('%02X' % num[p['slot']] if p else 'nada')] += 1
            if p is None:
                st['sin_rex_dibujado'] += 1
                continue
            tst['%02X' % num[p['slot']]]['dibujados'] += 1
            st['dibujadas'] += 1
            st['trans'] += len(p['trans'])
            st['max_trans'] = max(st['max_trans'], len(p['trans']))
            st['sufijos'] += len(p['segs'])
            st['max_sufijos'] = max(st['max_sufijos'], len(p['segs']))
            st['vbl'] += len(p['vbl'])
            st['errores'] += check_trace(p, recs, ctx, colors)
            st['remap_max'] = max(st['remap_max'], len(p['remaps']))
        summary[name] = dict(st)
        if types != (0xAB,):
            summary[name]['tipos'] = {k: dict(v) for k, v in sorted(tst.items())}
        print(name, json.dumps(summary[name], sort_keys=True), flush=True)
        # G4-B: sin índice libre para las bandas es un motivo para no dibujar
        # otro tipo (cuenta en 'tipos'); para el Rex sigue siendo un fallo
        ok &= (st['errores'] == 0 and st['sin_plazo'] == 0 and st['distinto_de_uno'] == 0
               and (st['sin_plan'] == 0 or types != (0xAB,)))
    OUT.mkdir(parents=True, exist_ok=True)
    if getattr(a, 'multi', False):
        (OUT / 'trace_multi.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        print('G4-1 TRACE: ' + ('OK' if ok else 'FALLA'))
        return 0 if ok else 1
    (OUT / 'trace_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('G5L TRACE: ' + ('OK' if ok else 'FALLA'))
    return 0 if ok else 1


def run_multi_photo(photo, tab, colors, sl, st, recs, ctx, tst=None, num=None):
    """G4-1 en una foto de la traza: plan_frame_n, su comprobación y la
    equivalencia con plan_frame cuando ubica un solo Rex (el mismo)"""
    seen = []
    p1 = plan_frame(photo, tab, colors, sl, Stats(), seen)
    if tst is not None:
        for slot, why in seen:
            tst['%02X' % num[slot]][why] += 1
    pn = plan_frame_n(photo, tab, colors, sl, st)
    if pn is None:
        st['sin_rex_visible'] += 1
        return
    n = len(pn['rex'])
    st['visibles'] += n + len(pn['bobs'])
    st['ubicados'] += n
    if tst is not None:
        for q in pn['rex']:
            tst['%02X' % num[q['slot']]]['dibujados'] += 1
    st['max_ubicados'] = max(st['max_ubicados'], n)
    st['hoy'] += p1 is not None
    for _, why in pn['bobs']:
        st['bob_' + why] += 1
    st['max_bobs'] = max(st['max_bobs'], len(pn['bobs']))
    if not n:
        return
    for k, q in enumerate(pn['rex'][1:], 1):
        a, b = q['r0'], q['r0'] + q['var']['h']
        both = any(p['r0'] < b and a < p['r0'] + p['var']['h'] for p in pn['rex'][:k])
        st['extra_comparte_filas' if both else 'extra_separado'] += 1
        st['extra_%d_columnas' % q['var']['cols']] += 1
    if n == 1 and p1 is not None and pn['rex'][0]['slot'] == p1['slot']:
        same = (pn['trans'] == p1['trans'] and pn['vbl'] == p1['vbl'] and pn['segs'] == p1['segs']
                and pn['rex'][0]['remaps'] == p1['remaps'])
        st['igual_a_uno' if same else 'distinto_de_uno'] += 1
    st['trans'] += len(pn['trans'])
    st['max_trans'] = max(st['max_trans'], len(pn['trans']))
    st['sufijos'] += len(pn['segs'])
    st['max_sufijos'] = max(st['max_sufijos'], len(pn['segs']))
    st['max_vbl'] = max(st['max_vbl'], len(pn['vbl']))
    err, tap = check_trace_n(pn, recs, ctx, colors)
    st['errores'] += err
    st['pixeles_tapados'] += tap


def sim_ldoff(mem, base, syms):
    """inicio de las cargas de cada segmento: tras 2 WAIT (o WAIT+NOP) y el borrado"""
    out = []
    for L in range(ROWS):
        a = base + syms['CL_LINES'] + syms['SEG'] * L + 8
        o = 8
        while True:
            w = mem.r16(a)
            if w & 1 or w == JUMP:
                break
            a += 4
            o += 4
        out.append(o)
    return out


# ----------------------------------------------------------------------
# el 68000 contra la referencia (Musashi, juego O5 entero)
# ----------------------------------------------------------------------
class MemList:
    """la lista de una copia (bytearray) con la vista de SimList"""
    def __init__(self, buf, base, syms, nb):
        self.buf, self.base, self.syms, self.nb = buf, base, syms, nb

    def r16(self, a):
        return struct.unpack_from('>H', self.buf, a - self.base)[0]

    def r32(self, a):
        return struct.unpack_from('>I', self.buf, a - self.base)[0]

    def w16(self, a, v):
        struct.pack_into('>H', self.buf, a - self.base, v)

    def w32(self, a, v):
        struct.pack_into('>I', self.buf, a - self.base, v)

    def seg(self, s):
        return self.base + self.syms['CL_LINES'] + self.syms['SEG'] * s

    def loads(self, s):
        return self.seg(s) + 8 + 4 * self.nb[s]

    def has_loads(self, s):
        return self.r16(self.loads(s)) != JUMP

    def jump(self, s):
        a = self.loads(s)
        while self.r16(a) != JUMP:
            a += 4
        return a

    def walk(self, s):
        a = self.loads(s)
        T = T0 + max(0, 16 * (self.nb[s] - 9))
        free, last = T, None
        while True:
            w = self.r16(a)
            if w == JUMP:
                return last, free, a
            if w & 1:
                T = max(adv(T, 2), xh(w & 0xFE))
            else:
                last = T
                T = adv(T)
            a += 4

    def put_jump(self, a, s):
        nxt = self.seg(s + 1)
        self.w16(a, 0x0084)
        self.w16(a + 2, nxt >> 16)
        self.w16(a + 4, 0x0086)
        self.w16(a + 6, nxt & 0xFFFF)
        self.w32(a + 8, 0x008A0000)


def read_photo(mem, rec, s):
    g = rec + s['R_G5L']
    raw = bytes(mem.r_block(g, 194))
    rex = []
    for j in range(raw[48]):
        o = 50 + 36 * j
        slot, n = raw[o], raw[o + 1]
        x, y = struct.unpack_from('>HH', raw, o + 2)
        ents = [tuple(raw[o + 6 + 5 * t:o + 11 + 5 * t]) for t in range(n)]
        rex.append((slot, x, y, ents))
    camx, camy = struct.unpack_from('>HH', raw, 44)
    return dict(moam=raw[0:16], mosz=raw[16:20], ptrs=raw[21:43], camx=camx, camy=camy, rex=rex,
                pal=mem.r8(rec + s['R_PAL']))


def expected_list(ml, p, s, dma, null, cdma, rbuf=0, chans=None):
    """con la limpieza ya aplicada: el bloque VBL y los sufijos del plan p
    (chans: los canales ya calculados, G4-2 channels_n)"""
    vbl = ml.base + s['CL_VBL'] + 4
    for n, ch in enumerate(chans if chans is not None else channels(p, dma, cdma, rbuf)):
        a = vbl + 16 * n
        pt, pos, ctl = ch if ch else (null, 0, 0)
        ml.w16(a + 2, pt >> 16)
        ml.w16(a + 6, pt & 0xFFFF)
        ml.w16(a + 10, pos)
        ml.w16(a + 14, ctl)
    a = vbl + 64
    cols = p['vbl'] if p else []
    for k in range(VBL_COLORS):
        if k < len(cols):
            ml.w16(a, 0x01A0 + 2 * cols[k][0])
            ml.w16(a + 2, cols[k][1])
        else:
            ml.w32(a, 0x01FE0000)
        a += 4
    if not p:
        return
    for seg_, (form, ms) in p['segs'].items():
        a = ml.jump(seg_)
        for w1, w2 in suffix_words(seg_, form, ms):
            ml.w16(a, w1)
            ml.w16(a + 2, w2)
            a += 4
        ml.put_jump(a, seg_)


def stale_check(mem, base, s, nb, planned):
    """ningún segmento sin plan tiene COLOR16-31 ni WAIT $D1 antes de su salto"""
    bad = 0
    for L in range(ROWS):
        a = base + s['CL_LINES'] + 256 * L + 8 + 4 * nb[L]
        while True:
            w = mem.r16(a)
            if w == JUMP:
                break
            if L not in planned and (0x01A0 <= w <= 0x01BE or (w & 1 and (w & 0xFF) == 0xD1)):
                bad += 1
            a += 4
    return bad


class GameRun:
    """el binario G5L en Musashi (2 MB: no cabe antes del DATA de 1 MB)"""
    def __init__(self, binary, listing, bank):
        import gamecheck as G
        import m68kverify as V
        G.DATA, G.BUF1, G.COPA, G.COPB, G.SPRS, G.FAKE = 0x70000, 0xB0000, 0xC0000, 0xD0000, 0xE0000, 0xF0000
        self.G, self.V = G, V

        class Big(V.MusashiCPU):
            def __init__(self):
                import machine68k as M
                self.M = M
                self.m = M.Machine(M.CPUType.M68000, 2048)
                self.cpu, self.mem = self.m.cpu, self.m.mem
                tid = self.m.traps.alloc(lambda op, pc: self.m.abort_execute())
                self.mem.w16(V.RET, 0xA000 | tid)
        code = Path(binary).read_bytes()
        s = self.s = V.symbols(listing)
        B = self.B = G.code_base(len(code))
        cpu = self.cpu = Big()
        mem = self.mem = cpu.mem
        cpu.write(B, code)
        addr = self.addr
        for n, p_ in (('_map16_lo', addr('map16')), ('_map16_hi', addr('map16') + s['MAPHALF']),
                      ('_spr_level', addr('spr_lv')), ('_gfx32', addr('gfx32'))):
            mem.w32(addr(n), p_)
        cpu.write(addr('_level_sprites'), b'\1')
        self.DMA = 0x100000
        self.dma = Path(bank + '.dma').read_bytes()
        cpu.write(self.DMA, self.dma)
        if 'sg3_dma' in s:                       # (G5L-R ya no carga el banco)
            mem.w32(addr('sg3_dma'), self.DMA)
        self.cdma = addr('g5l_cdma_src')         # (en el juego: una copia en chip)
        mem.w32(addr('g5l_cdma'), self.cdma)
        self.RBUF = 0x120000                      # búfer de las bandas (en el juego, chip)
        mem.w32(addr('g5l_rbuf'), self.RBUF)
        cpu.call(addr('replay_init'), B)
        self.fr = fr = G.Frames(cpu, B, s, Path('work/yi1_s_g5.dat').read_bytes())
        self.first, self.n = mem.r16(addr('replay') + 6), mem.r16(addr('replay') + 4)
        cpu.call(addr('game_step'), B)
        self.cops = (G.COPA, G.COPB)
        if 'V_COP3' in s:
            self.cops += (0x140000,)
            mem.w32(fr.vars + s['V_COP3'], self.cops[2])
            # Estado solo de CPU para build_mid de la tercera lista.
            mem.w32(fr.vars + s['V_LTC'], 0x160000 + 4 + s['GSZ'] * s['NGRP'])
        fr.init_scroll()
        _, _, sprs = G.layout(s)
        for i in range(3):
            mem.w32(addr('g_sbuf') + 4 * i, sprs + i * s['SPRBUF'])
        if 'V_COP3' in s:
            mem.w32(addr('g_sbuf') + 12, sprs + 3 * s['SPRBUF'] + 16)
        mem.w32(addr('g_null'), sprs + 3 * s['SPRBUF'])
        cpu.write(sprs + 3 * s['SPRBUF'], bytes(16))
        mem.w32(addr('g_data'), G.DATA)
        fr.call(addr('dc_init'), G.FAKE)
        self.nb = [(mem.r16(addr('ldoff') + 2 * L) - 8) // 4 for L in range(ROWS)]
        self.null = mem.r32(addr('g_null'))
        self.dc = addr('dc_st')

    def addr(self, n):
        return self.B + self.s[n]


def step_call(fr, G, V, adr, a4, hist):
    """Q: como Frames.call sin regiones, pero instrucción por instrucción
    (execute(1)); acumula {pc: [veces, ciclos]} y devuelve los ciclos"""
    R, cpu, mem, m = fr.M.Register, fr.cpu.cpu, fr.mem, fr.cpu.m
    cpu.w_reg(R.A3, G.DATA)
    cpu.w_reg(R.A4, a4)
    cpu.w_reg(R.A5, fr.vars)
    cpu.w_reg(R.A7, V.STACK - 4)
    mem.w32(V.STACK - 4, V.RET)
    cpu.w_pc(adr)
    tot = 0
    while True:
        pc = cpu.r_pc()
        if pc == V.RET:
            return tot
        c = m.execute(1).cycles
        e = hist.get(pc)
        if e:
            e[0] += 1
            e[1] += c
        else:
            hist[pc] = [1, c]
        tot += c


def run_game(a):
    gr = GameRun(a.bin, a.lst, a.bank)
    G, s, cpu, mem, fr, addr = gr.G, gr.s, gr.cpu, gr.mem, gr.fr, gr.addr
    # G4-B: la tabla del binario (con sus tipos), no la última de g5l.py mk
    tab = Table(cpu.read(addr('g5l_table'), addr('g5l_cdma_src') - addr('g5l_table')))
    _, cctx = build_table(a.bank, types=tuple(sorted(tab.types)))
    pals = cpu.read(addr('mario_pals'), 256)
    gv, dc, nb = addr('g5l_v'), gr.dc, gr.nb
    R = cpu.M.Register
    st = Stats()
    cycles, caps, frames = [], [], []
    prof = {}
    prof_n, ciclos_n = {}, {}
    regions = {addr(n): n for n in ('g5l_clean', 'g5l_mario', 'g5l_mfill', 'g5l_choose', 'g5l_plan', 'g5l_fast', 'g5l_need', 'g5l_mrow', 'g5l_mwall', 'g5l_mrowba', 'g5l_mba',
                                    'g5l_sweep', 'g5l_patch', 'g5l_place', 'g5l_emit', 'g5l_vblnull', 'g5l_sweepn', 'g5l_emitn', 'g5l_picksel',
                                    'g5l_rxsave', 'g5l_edges', 'g5l_rexmw', 'g5l_rxload', 'g5l_geo')}   # (g5l_place_e y g5l_emitc: se entra cayendo)
    nlim = a.frames or gr.n
    last_key = None
    keys = []
    logic = 0
    pcprof = {'build_mid': {}, 'render': {}, 'logic': {}, 'scroll': {}}
    pcframes = set()
    for r_ in (a.pcframes or '').split(','):
        if r_:
            lo_, _, hi_ = r_.partition('-')
            pcframes.update(range(int(lo_), int(hi_ or lo_) + 1))
    pclogic = set()                             # L: fotos con la lógica paso a paso
    for r_ in (a.pclogic or '').split(','):
        if r_:
            lo_, _, hi_ = r_.partition('-')
            pclogic.update(range(int(lo_), int(hi_ or lo_) + 1))
    dumpset = {int(x) for x in (a.dump_lines or '').split(',') if x}
    rlist = None                                # M1: R_FRAME de las fotos que dibujó la Amiga
    if a.render_list:
        rlist = {r_['frame'] for r_ in json.loads(Path(a.render_list).read_text())['rows']}
        pcprof['m1'] = {}
    for k in range(min(gr.n, nlim)):
        if k and k in pclogic:                  # L: la lógica paso a paso (con la captura)
            h_ = {}
            logic = step_call(fr, G, gr.V, addr('dc_cop'), G.FAKE, h_)
            caps.append(0)
            pcprof['logic'][k] = {'%x' % (pc_ - gr.B): v_ for pc_, v_ in h_.items()}
        elif k:
            cap = fr.call(addr('dc_cop'), G.FAKE, 'x', {addr('g5l_capture'): 'cap'})
            caps.append(cap.get('cap', 0))
            logic = cap.get('x', 0)             # T2: la lógica de la interrupción
        if k % a.render_every:
            continue                            # avanza la lógica sin dibujar esta foto
        photo = mem.r16(dc + s['DC_NEW'])
        rec = addr('dc_rec') + photo * s['DC_REC']
        if rlist is not None and mem.r16(rec + s['R_FRAME']) not in rlist:
            continue                            # M1: la Amiga no dibujó esta foto
        mem.w16(dc + s['DC_REND'], photo)
        mem.w16(fr.vars + s['V_S'], mem.r16(rec + s['R_S']))
        dumpk = a.dump_lines and k in dumpset
        if dumpk:                               # S11: linetab de la lista de atrás, antes
            back_ = mem.r32(fr.vars + s['V_BACK'])
            lt_ = {gr.cops[0]: addr('linetab_a'), gr.cops[1]: addr('linetab_b')}.get(back_)
            if lt_ is None:
                lt_ = mem.r32(fr.vars + s['V_LTC'])
            before_ = cpu.read(lt_, 32 * 224)
        pre = {}                                # T2: coste del render previo, por foto
        for n in ('columns', 'apply_colors', 'set_pointers', 'build_mid'):
            if a.pcprof and (not pcframes or k in pcframes) and (n == 'build_mid' or a.pcscroll):
                h_ = {}
                pre[n] = step_call(fr, G, gr.V, addr(n), G.FAKE, h_)
                hist_ = {'%x' % (pc_ - gr.B): v_ for pc_, v_ in h_.items()}
                if n == 'build_mid' and (pcframes or pre[n] > 10000):
                    pcprof[n][k] = hist_
                if a.pcscroll:
                    pcprof['scroll'].setdefault(k, {})[n] = hist_
            else:
                pre[n] = sum(fr.call(addr(n), G.FAKE).values())
        if dumpk:
            pcprof.setdefault('lines', {})[k] = {'s': mem.r16(fr.vars + s['V_S']), 'lt': lt_,
                                                'before': bytes(before_).hex(), 'after': bytes(cpu.read(lt_, 32 * 224)).hex()}
        if rlist is not None:
            pcprof['m1'][k] = [mem.r16(rec + s['R_FRAME']), mem.r16(rec + s['R_S']), pre['build_mid']]
        back = mem.r32(fr.vars + s['V_BACK'])
        size = s['CL_SIZE']
        snap = bytearray(cpu.read(back, size))
        list_index = gr.cops.index(back)
        recs = gv + s[('GV_RECA', 'GV_RECB', 'GV_RECC')[list_index]]
        ml = MemList(snap, back, s, nb)
        for j in range(mem.r16(recs)):
            J, w0, w1, sg = struct.unpack('>IIIH', cpu.read(recs + 2 + 16 * j, 14))
            if ml.r32(J) == w0 and ml.r32(J + 4) == w1:
                ml.put_jump(J, sg)
        ph = read_photo(mem, rec, s)
        colors = struct.unpack_from('>16H', pals, 32 * ph['pal'])
        p = plan_frame_n(ph, tab, colors, ml, st, s.get("G5L_MAXPL", G5L_MAXPL))  # G4-2 (con un Rex: plan_frame)
        if p is not None and not p['rex']:
            p = None
        rbuf = gr.RBUF + list_index * s.get('G5L_LBLK', LBLK)
        chans, chains = channels_n(p['rex'] if p else [], gr.cdma, rbuf)
        expected_list(ml, p, s, gr.DMA, gr.null, gr.cdma, rbuf, chans)
        if p:
            st['rex_%d' % len(p['rex'])] += 1
            for q in p['rex']:                  # G4-B: por tipo
                st['tipo_%02X' % cctx['ctype'][q['var']['n'] & 0x7FFF]] += 1
        poison = {R.D2: 0x12345602, R.D3: 0x12345603, R.D4: 0x12345604, R.D5: 0x12345605,
                  R.D6: 0x12345606, R.D7: 0x12345607, R.A2: 0x00012342, R.A6: 0x00012346}
        for r_, v_ in poison.items():
            cpu.cpu.w_reg(r_, v_)
        cpu.cpu.w_reg(R.A0, rec)
        if a.pcprof and (not pcframes or k in pcframes):
            h_ = {}
            parts = {'render': step_call(fr, G, gr.V, addr('g5l_render'), G.FAKE, h_)}
            if parts['render'] > 3000:
                pcprof['render'][k] = {'%x' % (pc_ - gr.B): v_ for pc_, v_ in h_.items()}
        else:
            parts = fr.call(addr('g5l_render'), G.FAKE, 'render', regions)
        c = sum(parts.values())
        nrx = len(p['rex']) if p else 0         # G4-2o: partes por Rex ubicados
        for kk, vv in parts.items():
            for pr_ in (prof, prof_n.setdefault(nrx, {})):
                pp = pr_.setdefault(kk, [0, 0, 0])
                pp[0] += vv
                pp[1] = max(pp[1], vv)
                pp[2] += 1
        ciclos_n.setdefault(nrx, []).append(sum(parts.values()))
        for r_, v_ in poison.items():
            if cpu.cpu.r_reg(r_) != v_:
                st['abi'] += 1
        if cpu.cpu.r_reg(R.A5) != fr.vars:
            st['abi'] += 1
        cycles.append((c, gr.first + mem.r16(rec + s['R_FRAME'])))
        frames.append(dict(k=k, c=c, parts=parts, ntr=len(p['trans']) if p else -1,
                           nseg=len(p['segs']) if p else 0, pre=pre,
                           cap=caps[-1] if k else 0, logic=logic, f=cycles[-1][1],
                           pk=cpu.read(gv + s['GV_PK'], 64).hex(),    # T2: clave del plan
                           sc=mem.r16(rec + s['R_S']),                # la s del scroll
                           plan=dict(rex=[dict(vo=q['vo'], r0=q['r0'], x0=q['x0'],   # Pa: el plan de Python
                                               tipo=cctx['ctype'][q['var']['n'] & 0x7FFF],
                                               groups=[[i, c_, m_] for (i, c_), m_ in q['groups'].items()],
                                               remaps=[list(r_) for r_ in q['remaps']]) for q in p['rex']],
                                     trans=[list(t_) for t_ in p['trans']]) if p else None))
        got = cpu.read(back, size)
        dslot = mem.r16(gv + s['GV_DSLOT'])
        want_slot = p['slot'] if p else 0xFFFF
        if got != bytes(snap) or dslot != want_slot:
            st['distintas'] += 1
            if st['distintas'] <= 3:
                diffs = [o for o in range(size) if got[o] != snap[o]]
                print('foto k=%d: lista distinta en %d bytes (primeros %s), slot asm %d ref %d' % (
                    k, len(diffs), [hex(o) for o in diffs[:8]], dslot, want_slot))
                if diffs:
                    o = diffs[0] & ~3
                    print('   asm', got[o - 8:o + 24].hex(), '\n   ref', bytes(snap[o - 8:o + 24]).hex())
        if p:                                   # ¿el mismo plan de filas que la foto anterior?
            ents = mario_entries(ph['moam'], ph['mosz']) or []
            bx = min((e[0] for e in ents), default=0)
            by = min((e[1] for e in ents), default=0)
            q0 = p['rex'][0]
            key = (q0['vo'], q0['r0'], ph['pal'], tuple((e[0] - bx, e[1] - by) + tuple(e[2:]) for e in ents),
                   tuple(ph['ptrs']) if ents else (), q0['r0'] - by, len(p['rex']))
            st['plan_igual'] += key == last_key
            last_key = key
            keys.append(repr(key))
        else:
            last_key = None
        for kq, q in enumerate(p['rex'] if p else []):
            if not q['remaps']:
                continue
            st['con_bandas'] += 1
            pose = cctx['clean'][q['var']['n'] & 0x7FFF]
            hm = remap_halves(q['remaps'])
            for j, want in enumerate(rbuf_streams(pose, q['remaps'])):
                if not hm >> (j & 1) & 1:
                    continue
                n_ = 4 * q['var']['h'] + 8
                if cpu.read(rbuf + 4 * RSTRIDE * kq + RSTRIDE * j, n_) != want[:n_]:
                    st['bufer_distinto'] += 1
                    if st['bufer_distinto'] <= 3:
                        print('foto k=%d: Rex %d, flujo %d del búfer distinto' % (k, kq, j))
                    break
        for sj, (C, ((p1, n1), (pos2, ctl2), (p2, n2))) in chains.items():
            st['cadenas'] += 1                  # G4-2: el flujo encadenado
            want = (bytes(cpu.read(p1, 4 * n1)) + struct.pack('>HH', pos2, ctl2)
                    + bytes(cpu.read(p2, 4 * n2)) + bytes(4))
            if bytes(cpu.read(C, len(want))) != want:
                st['cadena_distinta'] += 1
                if st['cadena_distinta'] <= 3:
                    print('foto k=%d: cadena del flujo %d distinta' % (k, sj))
        planned = set(p['segs']) if p else set()
        st['restos'] += stale_check(mem, back, s, nb, planned)
        st['fotos'] += 1
        st['dibujadas'] += p is not None
        cpu.cpu.w_reg(R.D7, photo)
        fr.call(addr('dc_hdr'), G.FAKE)
        mem.w32(dc + s['DC_PLIST'], back)
        mem.w16(dc + s['DC_FRONT'], photo)
        mem.w16(dc + s['DC_REND'], 0xFFFF)
        if 'DC_FLIST' in s:
            mem.w32(dc + s['DC_FLIST'], back)
        other = gr.cops[(list_index + 1) % len(gr.cops)]
        mem.w32(fr.vars + s['V_BACK'], other)
        if k % 500 == 0:
            print('k=%d %s' % (k, json.dumps(dict(st), sort_keys=True)), flush=True)
    worst = max(cycles) if cycles else (0, 0)
    res = dict(st, ciclos_media=round(sum(c for c, _ in cycles) / max(1, len(cycles)), 1),
               ciclos_max=worst[0], ciclos_max_frame=worst[1],
               captura_max=max(caps) if caps else 0,
               captura_media=round(sum(caps) / max(1, len(caps)), 1),
               partes={kk: dict(media=round(v[0] / v[2]), max=v[1], n=v[2]) for kk, v in prof.items()},
               partes_rex={nr: {kk: dict(media=round(v[0] / v[2]), max=v[1], n=v[2]) for kk, v in pr_.items()} for nr, pr_ in prof_n.items()},
               mediana_rex={nr: sorted(cs)[len(cs) // 2] for nr, cs in ciclos_n.items()})
    if a.pcprof:                                # Q: no pisa la corrida normal
        pcprof['tot'] = {x['k']: [x['c'], x['pre']['build_mid']] for x in frames}
        pcprof['logic_tot'] = {x['k']: x['logic'] for x in frames if x['k'] in pclogic}
        pcprof['scroll_tot'] = {x['k']: x['pre'] for x in frames}
        Path(a.pcprof).write_text(json.dumps(pcprof), encoding='utf-8')
        print(json.dumps(dict(st), sort_keys=True))
        ok = not st['distintas'] and not st['abi'] and not st['restos'] and not st['sin_plan'] and not st['bufer_distinto'] and not st['cadena_distinta'] and not st['cadena_distinta']
        print('G5L GAME (pcprof): ' + ('OK' if ok else 'FALLA'))
        return 0 if ok else 1
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'game_summary.json').write_text(json.dumps(res, indent=2), encoding='utf-8')
    (OUT / 'game_cycles.json').write_text(json.dumps(cycles), encoding='utf-8')
    (OUT / 'game_frames.json').write_text(json.dumps(frames), encoding='utf-8')
    (OUT / 'game_keys.json').write_text(json.dumps(keys), encoding='utf-8')
    print(json.dumps(res, sort_keys=True))
    ok = not st['distintas'] and not st['abi'] and not st['restos'] and not st['sin_plan'] and not st['bufer_distinto'] and not st['cadena_distinta']
    print('G5L GAME: ' + ('OK' if ok else 'FALLA'))
    return 0 if ok else 1


# ----------------------------------------------------------------------
# captura de WinUAE: control (sin G5L) + el Rex esperado = la captura G5L
# ----------------------------------------------------------------------
SHOT_BOX = (67, 70, 707, 582)          # P57: PAL x2 sin el marco de Windows
SHOT_DX = 32                           # DIW $2CA1: x = 0 cae en el px 32 del recorte


def rgb12(c):
    return ((c >> 8) & 15) * 17, ((c >> 4) & 15) * 17, (c & 15) * 17


def mario_pixels(tab, ph, gfx):
    """{(x, fila del copper)}: los pixeles opacos de Mario (como mspr.c)"""
    from smw2amiga import decode_snes_tile
    ents = mario_entries(ph['moam'], ph['mosz'])
    out = set()
    for ex, ey, tile, attr, nt in ents or ():
        hf, vf = attr >> 6 & 1, attr >> 7
        for ty in range(nt):
            for tx in range(nt):
                g = vram_gtile(ph['ptrs'], (tile + (nt - 1 - tx if hf else tx) + 16 * (nt - 1 - ty if vf else ty)) & 255)
                if g is None:
                    continue
                rows = decode_snes_tile(gfx[32 * g:32 * g + 32], 4)
                for r in range(8):
                    src = rows[7 - r if vf else r]
                    for c in range(8):
                        if src[7 - c if hf else c]:
                            out.add((ex + 8 * tx + c, ey + 1 + 8 * ty + r))
    return out


def run_shot(a):
    from PIL import Image
    import g2t_ref as T
    gr = GameRun(a.bin, a.lst, a.bank)
    G, s, cpu, mem, fr, addr = gr.G, gr.s, gr.cpu, gr.mem, gr.fr, gr.addr
    # G4-B: la tabla del binario (con sus tipos), no la última de g5l.py mk
    tab = Table(cpu.read(addr('g5l_table'), addr('g5l_cdma_src') - addr('g5l_table')))
    _, cctx = build_table(a.bank, types=tuple(sorted(tab.types)))
    pals = cpu.read(addr('mario_pals'), 256)
    gfx = cpu.read(addr('gfx32'), 23808)
    R = cpu.M.Register
    st = Stats()
    p = ph = None
    for k in range(a.frame + 1):
        if k:
            fr.call(addr('dc_cop'), G.FAKE)
        photo = mem.r16(gr.dc + s['DC_NEW'])
        rec = addr('dc_rec') + photo * s['DC_REC']
        mem.w16(gr.dc + s['DC_REND'], photo)
        mem.w16(fr.vars + s['V_S'], mem.r16(rec + s['R_S']))
        for n in ('columns', 'apply_colors', 'set_pointers', 'build_mid'):
            fr.call(addr(n), G.FAKE)
        if k == a.frame:
            back = mem.r32(fr.vars + s['V_BACK'])
            ml = MemList(bytearray(cpu.read(back, s['CL_SIZE'])), back, s, gr.nb)
            ph = read_photo(mem, rec, s)
            colors = struct.unpack_from('>16H', pals, 32 * ph['pal'])
            p = plan_frame_n(ph, tab, colors, ml, st, s.get("G5L_MAXPL", G5L_MAXPL))   # G4-2
            if p is not None and not p['rex']:
                p = None
        cpu.cpu.w_reg(R.A0, rec)
        fr.call(addr('g5l_render'), G.FAKE)
        back = mem.r32(fr.vars + s['V_BACK'])
        cpu.cpu.w_reg(R.D7, photo)
        fr.call(addr('dc_hdr'), G.FAKE)
        mem.w32(gr.dc + s['DC_PLIST'], back)
        mem.w16(gr.dc + s['DC_FRONT'], photo)
        mem.w16(gr.dc + s['DC_REND'], 0xFFFF)
        other = mem.r32(fr.vars + (s['V_COP2'] if back == mem.r32(fr.vars + s['V_COP']) else s['V_COP']))
        mem.w32(fr.vars + s['V_BACK'], other)
    if p is None:
        raise SystemExit('la foto %d no tiene Rex dibujado' % a.frame)
    ctx = T.load_context(a.bank)
    mario = mario_pixels(tab, ph, gfx)
    ctrl = Image.open(a.control).convert('RGB').crop(SHOT_BOX)
    shot = Image.open(a.shot).convert('RGB').crop(SHOT_BOX)
    want = ctrl.copy()
    rex = 0
    only = [int(x) for x in a.only.split(',')] if a.only else range(len(p['rex']))
    for q in (p['rex'][j] for j in only):      # G4-2: los Rex que el control no dibuja
        v = q['var']
        pose = cctx['clean'][v['n'] & 0x7FFF] if v['n'] & 0x8000 else ctx['poses'][v['n']]
        for r, row in enumerate(pose['rows']):
            cmap = {d: c for _, _, d, c in pose['row_maps'][r]}
            for x, d in enumerate(row):
                gx, gy = q['x0'] + x, q['r0'] + r
                if not d or not (0 <= gx < 256 and 0 <= gy < ROWS) or (gx, gy) in mario:
                    continue
                rex += 1
                col = rgb12(cmap[d])
                for yy in range(2):
                    for xx in range(2):
                        want.putpixel((2 * (gx + SHOT_DX) + xx, 2 * gy + yy), col)
    bad = sum(1 for q, w in zip(shot.getdata(), want.getdata()) if q != w)
    sheet = Image.new('RGB', (640, 1536))
    sheet.paste(ctrl, (0, 0))
    sheet.paste(want, (0, 512))
    sheet.paste(shot, (0, 1024))
    out = Path(a.shot).with_name('check.png')
    sheet.save(out)
    res = dict(foto=a.frame, rex=[dict(variante=q['var']['n'], x0=q['x0'], r0=q['r0'], bandas=len(q['remaps']))
                                  for q in p['rex']], dibujados=list(only),
               pixeles_rex=rex, pixeles_distintos=bad, de=640 * 512, transiciones=len(p['trans']),
               sufijos=len(p['segs']), vbl=len(p['vbl']))
    print(json.dumps(res))
    Path(a.shot).with_name('check.json').write_text(json.dumps(res, indent=2), encoding='utf-8')
    return 0 if bad == 0 else 1


def parse_types(s):
    """G4-B: 'AB' (el Rex, el defecto), 'all' (el Rex y G5L_OTHER) o una lista
    hexadecimal separada por comas"""
    if s == 'all':
        return (0xAB,) + G5L_OTHER
    return tuple(int(x, 16) for x in s.split(','))


def run_mk(a):
    blob, ctx = build_table(a.bank, types=parse_types(a.types))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'g5l.bin').write_bytes(blob)
    (OUT / 'g5l_clean.dma').write_bytes(bytes(ctx['cdma']))
    print('g5l_clean.dma: %d B' % len(ctx['cdma']))
    Path('work/g5l.i').write_text(
        'g5l_table:\n        incbin "%s"\n        even\n'
        'G5L_CDMA_SIZE equ %d\n'
        'g5l_cdma_src:\n        incbin "%s"\n        even\n'
        % ((OUT / 'g5l.bin').resolve().as_posix(), len(ctx['cdma']),
           (OUT / 'g5l_clean.dma').resolve().as_posix()), encoding='utf-8')
    print('g5l.bin: %d B' % len(blob))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('mk')
    m.add_argument('--bank', default='work/g3/bank')
    m.add_argument('--types', default='AB', help="G4-B: 'AB', 'all' o hex separados por comas")
    t = sub.add_parser('trace')
    t.add_argument('--bank', default='work/g3/bank')
    t.add_argument('--types', default='AB', help="G4-B: 'AB', 'all' o hex separados por comas")
    t.add_argument('--prefix', default='oam', help="G4-B: 'oamb' = trazas con todos los tipos")
    t.add_argument('--traces', nargs='+', default=['yi1', 'normal', 'spin_kill'])
    t.add_argument('--multi', action='store_true', help='G4-1: varios Rex por foto (plan_frame_n)')
    g = sub.add_parser('game')
    g.add_argument('--bin', default='work/g5l/rep/game.bin')
    g.add_argument('--lst', default='work/g5l/rep/game.lst')
    g.add_argument('--bank', default='work/g3/bank')
    g.add_argument('--frames', type=int, default=0)
    g.add_argument('--dump-lines', help='S11: con --pcprof, fotos k cuyo linetab (antes/después de build_mid) se vuelca')
    g.add_argument('--render-list', help='M1: JSON de tools/m1_read.py; dibujar solo las fotos (R_FRAME) que dibujó la Amiga')
    g.add_argument('--render-every', type=int, default=1, help='Dibujar cada N fotos; ejercita el scroll y las cachés con fotos omitidas')
    g.add_argument('--pcprof', help='Q: histograma por PC de g5l_render y build_mid (json)')
    g.add_argument('--pcscroll', action='store_true', help='Con --pcprof: incluir columns, apply_colors y set_pointers')
    g.add_argument('--pcframes', help='Con --pcprof: limitar el paso a paso del render/scroll a fotos k, p.ej. 10-20,40')
    g.add_argument('--pclogic', help="L: con --pcprof, fotos con la lógica (dc_cop) paso a paso: '3290-3370,1000-1050'")
    h = sub.add_parser('shot')
    h.add_argument('--bin', default='work/g5l/rep/game.bin')
    h.add_argument('--lst', default='work/g5l/rep/game.lst')
    h.add_argument('--bank', default='work/g3/bank')
    h.add_argument('--frame', type=int, required=True)
    h.add_argument('--shot', required=True)
    h.add_argument('--control', required=True)
    h.add_argument('--only', help='G4-2: los Rex del plan que se suman al control (p.ej. 1); todos si no')
    a = ap.parse_args()
    if a.cmd == 'game' and a.render_every < 1:
        ap.error('--render-every debe ser >= 1')
    return {'mk': run_mk, 'trace': run_trace, 'game': run_game, 'shot': run_shot}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())
