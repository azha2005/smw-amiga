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
# tabla G5L1 (big endian, offsets relativos al principio)
# ----------------------------------------------------------------------
#  0  'G5L1'
#  4  .w formas  .w variantes  .w NHASH  .w 0
# 12  .l offset de la tabla de máscaras de Mario (744 x 8 .w)
# 16  NHASH x .w: offset de la primera forma del cubo (0 = vacío)
# formas (todas antes de las variantes: offsets .w): .w siguiente (0 =
#        fin), .b fichas, .b prioridad, .w variantes, fichas x 4 B (dx, dy,
#        tile bajo, banderas), variantes x .l offset
# variante: .w ox, .w oy, .b ancho, .b alto, .b columnas, .b índices,
#        .b xmax, .b grupos, .w variante del banco, columnas x (.l off0,
#        .l off1) en bank.dma, grupos x (.b índice, .b 0, .w color, .l
#        filas): el filtro A3 por máscaras; grupos x alto x columnas .w:
#        los píxeles del índice del grupo (g5l_patch); índices x (.b índice, .b
#        tramos, tramos x (.b fila primera, .b fila última, .w color),
#        .b cambios, .b última fila, cambios x (.b fila, .b última del
#        tramo anterior o $FF, .w color)): filas seguidas, mismo color;
#        los cambios son el camino rápido de g5l_sweep
def tile_flags(tile, size, fx, fy, pal):
    return (tile >> 8) | (2 if size == 16 else 0) | fx << 2 | fy << 3 | pal << 4


def key_hash(tiles4):
    return (sum(sum(t) for t in tiles4) + len(tiles4)) & (NHASH - 1)


def variant_record(pose, tables, n, offs=None):
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
        out += struct.pack('>BBHI', d, 0, c, m)
    # G5L-R: por grupo, los píxeles de su índice en cada fila y columna
    # (el parche de g5l_patch): h x columnas .w, bit 15 = x 16c
    for (d, c), m in groups.items():
        for r in range(h):
            for col in range(cols):
                wv = 0
                for x in range(16):
                    xx = 16 * col + x
                    if xx < w and pose['rows'][r][xx] == d:
                        wv |= 1 << (15 - x)
                out += struct.pack('>H', wv)
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


def build_table(bank, clean=True):
    import g2t_ref as T
    import g5ref as R
    ctx = T.load_context(bank)
    poses, directory, tables = ctx['poses'], ctx['directory'], ctx['tables']
    ctx['clean'], ctx['cdma'] = [], bytearray()
    cindex = {}
    shapes = []
    for (tiles, pri), variants in directory.items():
        t4 = [((dx & 255), (dy & 255), tile & 255, tile_flags(tile, size, fx, fy, pal))
              for dx, dy, tile, size, fx, fy, pal in tiles]
        if any(not -128 <= dx < 128 or not -128 <= dy < 128 for dx, dy, *_ in tiles):
            raise ValueError('ficha fuera de s8')
        shapes.append((t4, pri, variants))
    vblob = bytearray()
    voff = {}
    if clean:
        for k, (t4, pri, variants) in enumerate(shapes):
            names = []
            for cmap in CLEAN_MAPS:
                cp = clean_pose(poses[variants[0]], cmap)
                offs = clean_streams(cp, ctx['cdma'], cindex)
                ck = len(ctx['clean'])
                ctx['clean'].append(cp)
                if len(vblob) & 1:
                    vblob.append(0)
                voff['c%d' % ck] = len(vblob)
                vblob += variant_record(cp, None, 0x8000 | ck, [
                    (o0 | CLEAN_FLAG, o1 | CLEAN_FLAG) for o0, o1 in offs])
                names.append('c%d' % ck)
            shapes[k] = (t4, pri, names)        # G5L-R: solo la limpia
    sbase = 16 + 2 * NHASH
    vbase = sbase + sum(6 + 4 * len(t4) + 4 * len(v) for t4, _, v in shapes)
    blob = bytearray(sbase)
    struct.pack_into('>4sHHHH', blob, 0, b'G5L1', len(shapes), len(poses), NHASH, 0)
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
        magic, self.nshapes, self.nvar, nh, _ = struct.unpack_from('>4sHHHH', blob, 0)
        if magic != b'G5L1' or nh != NHASH:
            raise ValueError('tabla G5L desconocida')
        self.mo, = struct.unpack_from('>I', blob, 12)

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
        p = o + 12
        offs = [struct.unpack_from('>II', self.b, p + 8 * c) for c in range(cols)]
        groups = [struct.unpack_from('>BBHI', self.b, p + 8 * cols + 8 * j) for j in range(ng)]
        p += 8 * cols + 8 * ng
        p += 2 * h * cols * ng                  # máscaras de píxeles (g5l_patch)
        runs = {}
        for _ in range(nidx):
            d, nr = self.b[p], self.b[p + 1]
            runs[d] = [struct.unpack_from('>BBH', self.b, p + 2 + 4 * j) for j in range(nr)]
            p += 2 + 4 * nr
            p += 2 + 4 * self.b[p]              # cambios (solo el 68000)
        return dict(ox=ox, oy=oy, w=w, h=h, cols=cols, xmax=xmax, offs=offs, runs=runs, n=n,
                    groups=[(d, c, m) for d, _, c, m in groups])

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


def plan_frame(photo, tab, colors, lst, st):
    """photo: pal, moam, mosz, ptrs, camx, camy, rex=[(slot, x, y, entries)]
    lst: nb[s], has_loads(s), walk(s) -> (last, free, J)
    Devuelve dict(rex=..., vbl=[(i, color)], segs={s: (forma, moves)}, chans=[...]) o None."""
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
            continue
        vs = tab.lookup(t4, pri)
        if vs is None:
            st['rex_sin_forma'] += 1
            continue
        v0 = tab.variant(vs[0])
        x0, r0 = sx + v0['ox'], sy + v0['oy'] + 1
        if not (r0 + v0['h'] > 0 and r0 < ROWS and x0 + v0['w'] > 0 and x0 < 256):
            continue
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
    inv = {c: d for d, c in cmap.items()}
    for c in REXC:
        if c not in inv:
            continue
        ic = inv[c]
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
        if r['num'] != 0xAB:
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
    chosen = [r for r in recs if r['num'] == 0xAB and r['slot'] == p['slot']][0]
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


def run_trace(a):
    import g2t_ref as T
    import g5ref as R
    import scrollprof as P
    blob, ctx = build_table(a.bank)
    tab = Table(blob)
    code, lst = P.assemble('player/scroll.s', ['VIS=256', 'SPRITES'])
    syms, local = P.listing(lst)
    V = {n: v for n, v in syms.items() if n.startswith('V_')}
    summary = {}
    ok = True
    for name in a.traces:
        records = list(R.read_trace('work/oam_%s.trace' % name, 'work/oracle_%s_oam.bin' % name))
        groups = collections.defaultdict(list)
        for r in records:
            groups[r['frame']].append(r)
        sc = P.Scroll(code, syms, local, Path('work/yi1_s.dat').read_bytes(), V)
        sc.init()
        ldoff = None
        st = Stats()
        for f in sorted(groups):
            recs = groups[f]
            ram = recs[0]['ram']
            sc.mem.w16(sc.vars + V['V_S'], ram[0x1a] | ram[0x1b] << 8)
            sc.call('scroll_frame')
            if not any(r['num'] == 0xAB for r in recs):
                continue
            base = sc.mem.r32(P.FAKE + 0x80)
            if ldoff is None:
                ldoff = sim_ldoff(sc.mem, base, syms)
            sl = SimList(sc.mem, base, syms, ldoff)
            photo = trace_photo(recs, ctx)
            pi = R.palette_index(ram, ctx['pointers'])
            colors = struct.unpack_from('>16H', ctx['pals'], 32 * pi)
            st['fotos'] += 1
            p = plan_frame(photo, tab, colors, sl, st)
            if p is None:
                st['sin_rex_dibujado'] += 1
                continue
            st['dibujadas'] += 1
            st['trans'] += len(p['trans'])
            st['max_trans'] = max(st['max_trans'], len(p['trans']))
            st['sufijos'] += len(p['segs'])
            st['max_sufijos'] = max(st['max_sufijos'], len(p['segs']))
            st['vbl'] += len(p['vbl'])
            st['errores'] += check_trace(p, recs, ctx, colors)
            st['remap_max'] = max(st['remap_max'], len(p['remaps']))
        summary[name] = dict(st)
        print(name, json.dumps(dict(st), sort_keys=True), flush=True)
        ok &= st['errores'] == 0 and st['sin_plan'] == 0
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'trace_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('G5L TRACE: ' + ('OK' if ok else 'FALLA'))
    return 0 if ok else 1


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


def expected_list(ml, p, s, dma, null, cdma, rbuf=0):
    """con la limpieza ya aplicada: el bloque VBL y los sufijos del plan p"""
    vbl = ml.base + s['CL_VBL'] + 4
    for n, ch in enumerate(channels(p, dma, cdma, rbuf)):
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
        fr.init_scroll()
        _, _, sprs = G.layout(s)
        for i in range(3):
            mem.w32(addr('g_sbuf') + 4 * i, sprs + i * s['SPRBUF'])
        mem.w32(addr('g_null'), sprs + 3 * s['SPRBUF'])
        cpu.write(sprs + 3 * s['SPRBUF'], bytes(16))
        mem.w32(addr('g_data'), G.DATA)
        fr.call(addr('dc_init'), G.FAKE)
        self.nb = [(mem.r16(addr('ldoff') + 2 * L) - 8) // 4 for L in range(ROWS)]
        self.null = mem.r32(addr('g_null'))
        self.dc = addr('dc_st')

    def addr(self, n):
        return self.B + self.s[n]


def run_game(a):
    gr = GameRun(a.bin, a.lst, a.bank)
    G, s, cpu, mem, fr, addr = gr.G, gr.s, gr.cpu, gr.mem, gr.fr, gr.addr
    tab = Table(Path('work/g5l/g5l.bin').read_bytes())
    _, cctx = build_table(a.bank)
    pals = cpu.read(addr('mario_pals'), 256)
    gv, dc, nb = addr('g5l_v'), gr.dc, gr.nb
    R = cpu.M.Register
    st = Stats()
    cycles, caps, frames = [], [], []
    prof = {}
    regions = {addr(n): n for n in ('g5l_clean', 'g5l_mario', 'g5l_mfill', 'g5l_choose', 'g5l_plan', 'g5l_fast', 'g5l_need', 'g5l_mrow', 'g5l_mwall', 'g5l_mrowba', 'g5l_mba',
                                    'g5l_sweep', 'g5l_patch', 'g5l_place', 'g5l_emit', 'g5l_vblnull')}
    nlim = a.frames or gr.n
    last_key = None
    keys = []
    for k in range(min(gr.n, nlim)):
        if k:
            cap = fr.call(addr('dc_cop'), G.FAKE, 'x', {addr('g5l_capture'): 'cap'})
            caps.append(cap.get('cap', 0))
        photo = mem.r16(dc + s['DC_NEW'])
        rec = addr('dc_rec') + photo * s['DC_REC']
        mem.w16(dc + s['DC_REND'], photo)
        mem.w16(fr.vars + s['V_S'], mem.r16(rec + s['R_S']))
        for n in ('columns', 'apply_colors', 'set_pointers', 'build_mid'):
            fr.call(addr(n), G.FAKE)
        back = mem.r32(fr.vars + s['V_BACK'])
        size = s['CL_SIZE']
        snap = bytearray(cpu.read(back, size))
        recs = gv + (s['GV_RECA'] if back == mem.r32(fr.vars + s['V_COP']) else s['GV_RECB'])
        ml = MemList(snap, back, s, nb)
        for j in range(mem.r16(recs)):
            J, w0, w1, sg = struct.unpack('>IIIH', cpu.read(recs + 2 + 16 * j, 14))
            if ml.r32(J) == w0 and ml.r32(J + 4) == w1:
                ml.put_jump(J, sg)
        ph = read_photo(mem, rec, s)
        colors = struct.unpack_from('>16H', pals, 32 * ph['pal'])
        p = plan_frame(ph, tab, colors, ml, st)
        rbuf = gr.RBUF + (0 if back == mem.r32(fr.vars + s['V_COP']) else 4 * RSTRIDE)
        expected_list(ml, p, s, gr.DMA, gr.null, gr.cdma, rbuf)
        poison = {R.D2: 0x12345602, R.D3: 0x12345603, R.D4: 0x12345604, R.D5: 0x12345605,
                  R.D6: 0x12345606, R.D7: 0x12345607, R.A2: 0x00012342, R.A6: 0x00012346}
        for r_, v_ in poison.items():
            cpu.cpu.w_reg(r_, v_)
        cpu.cpu.w_reg(R.A0, rec)
        parts = fr.call(addr('g5l_render'), G.FAKE, 'render', regions)
        c = sum(parts.values())
        for kk, vv in parts.items():
            pp = prof.setdefault(kk, [0, 0, 0])
            pp[0] += vv
            pp[1] = max(pp[1], vv)
            pp[2] += 1
        for r_, v_ in poison.items():
            if cpu.cpu.r_reg(r_) != v_:
                st['abi'] += 1
        if cpu.cpu.r_reg(R.A5) != fr.vars:
            st['abi'] += 1
        cycles.append((c, gr.first + mem.r16(rec + s['R_FRAME'])))
        frames.append(dict(k=k, c=c, parts=parts, ntr=len(p['trans']) if p else -1,
                           nseg=len(p['segs']) if p else 0))
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
            key = (p['vo'], p['r0'], ph['pal'], tuple((e[0] - bx, e[1] - by) + tuple(e[2:]) for e in ents),
                   tuple(ph['ptrs']) if ents else (), p['r0'] - by)
            st['plan_igual'] += key == last_key
            last_key = key
            keys.append(repr(key))
        else:
            last_key = None
        if p and p['remaps']:
            st['con_bandas'] += 1
            pose = cctx['clean'][p['var']['n'] & 0x7FFF]
            hm = remap_halves(p['remaps'])
            for j, want in enumerate(rbuf_streams(pose, p['remaps'])):
                if not hm >> (j & 1) & 1:
                    continue
                n_ = 4 * p['var']['h'] + 8
                if cpu.read(rbuf + RSTRIDE * j, n_) != want[:n_]:
                    st['bufer_distinto'] += 1
                    if st['bufer_distinto'] <= 3:
                        print('foto k=%d: flujo %d del búfer distinto' % (k, j))
                    break
        planned = set(p['segs']) if p else set()
        st['restos'] += stale_check(mem, back, s, nb, planned)
        st['fotos'] += 1
        st['dibujadas'] += p is not None
        cpu.cpu.w_reg(R.D7, photo)
        fr.call(addr('dc_hdr'), G.FAKE)
        mem.w32(dc + s['DC_PLIST'], back)
        mem.w16(dc + s['DC_FRONT'], photo)
        mem.w16(dc + s['DC_REND'], 0xFFFF)
        other = mem.r32(fr.vars + (s['V_COP2'] if back == mem.r32(fr.vars + s['V_COP']) else s['V_COP']))
        mem.w32(fr.vars + s['V_BACK'], other)
        if k % 500 == 0:
            print('k=%d %s' % (k, json.dumps(dict(st), sort_keys=True)), flush=True)
    worst = max(cycles) if cycles else (0, 0)
    res = dict(st, ciclos_media=round(sum(c for c, _ in cycles) / max(1, len(cycles)), 1),
               ciclos_max=worst[0], ciclos_max_frame=worst[1],
               captura_max=max(caps) if caps else 0,
               captura_media=round(sum(caps) / max(1, len(caps)), 1),
               partes={kk: dict(media=round(v[0] / v[2]), max=v[1], n=v[2]) for kk, v in prof.items()})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'game_summary.json').write_text(json.dumps(res, indent=2), encoding='utf-8')
    (OUT / 'game_cycles.json').write_text(json.dumps(cycles), encoding='utf-8')
    (OUT / 'game_frames.json').write_text(json.dumps(frames), encoding='utf-8')
    (OUT / 'game_keys.json').write_text(json.dumps(keys), encoding='utf-8')
    print(json.dumps(res, sort_keys=True))
    ok = not st['distintas'] and not st['abi'] and not st['restos'] and not st['sin_plan'] and not st['bufer_distinto']
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
    tab = Table(Path('work/g5l/g5l.bin').read_bytes())
    _, cctx = build_table(a.bank)
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
            p = plan_frame(ph, tab, colors, ml, st)
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
    blob, cctx = build_table(a.bank)
    v = p['var']
    pose = cctx['clean'][v['n'] & 0x7FFF] if v['n'] & 0x8000 else ctx['poses'][v['n']]
    mario = mario_pixels(tab, ph, gfx)
    ctrl = Image.open(a.control).convert('RGB').crop(SHOT_BOX)
    shot = Image.open(a.shot).convert('RGB').crop(SHOT_BOX)
    want = ctrl.copy()
    rex = 0
    for r, row in enumerate(pose['rows']):
        cmap = {d: c for _, _, d, c in pose['row_maps'][r]}
        for x, d in enumerate(row):
            gx, gy = p['x0'] + x, p['r0'] + r
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
    res = dict(foto=a.frame, variante=v['n'], limpia=bool(v['n'] & 0x8000), x0=p['x0'], r0=p['r0'],
               pixeles_rex=rex, pixeles_distintos=bad, de=640 * 512, transiciones=len(p['trans']),
               sufijos=len(p['segs']), vbl=len(p['vbl']))
    print(json.dumps(res))
    Path(a.shot).with_name('check.json').write_text(json.dumps(res, indent=2), encoding='utf-8')
    return 0 if bad == 0 else 1


def run_mk(a):
    blob, ctx = build_table(a.bank)
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
    t = sub.add_parser('trace')
    t.add_argument('--bank', default='work/g3/bank')
    t.add_argument('--traces', nargs='+', default=['yi1', 'normal', 'spin_kill'])
    g = sub.add_parser('game')
    g.add_argument('--bin', default='work/g5l/rep/game.bin')
    g.add_argument('--lst', default='work/g5l/rep/game.lst')
    g.add_argument('--bank', default='work/g3/bank')
    g.add_argument('--frames', type=int, default=0)
    h = sub.add_parser('shot')
    h.add_argument('--bin', default='work/g5l/rep/game.bin')
    h.add_argument('--lst', default='work/g5l/rep/game.lst')
    h.add_argument('--bank', default='work/g3/bank')
    h.add_argument('--frame', type=int, required=True)
    h.add_argument('--shot', required=True)
    h.add_argument('--control', required=True)
    a = ap.parse_args()
    return {'mk': run_mk, 'trace': run_trace, 'game': run_game, 'shot': run_shot}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())
