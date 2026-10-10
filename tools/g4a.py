#!/usr/bin/env python3
"""G4-A: todos los enemigos en sprites de hardware, inventario y presupuesto.

Solo medida, en la PC (docs/instrucciones-g4a.md). No cambia el binario.

    python tools/g4a.py inv      # por tipo: formas, tamaño, colores, memoria G5L
    python tools/g4a.py inv2     # idem sin traza: atribución por posición (heurístico)
    python tools/g4a.py traceall # exacto: trazas SOT1 completas del host (marioverify.c)
    python tools/g4a.py lines    # columnas de 16 px por línea fuera de Mario
    python tools/g4a.py bobs     # cota de la cola de bobs (trazas SOT1)

Salida en work/g4a/ (derivado de la ROM, R9).
"""
import argparse
import collections
import glob
import json
import os
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import g5l as L                      # noqa: E402
import g5ref as R                    # noqa: E402
import mksprgfx as G                 # noqa: E402
from palette import snes_to_amiga12  # noqa: E402
from sprgfx_final import compose     # noqa: E402

OUT = Path('work/g4a')
TRACES = ('yi1', 'normal', 'spin_kill')
ROWS = 224
# Fichas de VRAM dinámica de Mario (g5l.vram_gtile / sprgfx_manifest.mario_rows)
MARIO_TILES = {t for t in range(0x20) if (t & 15) < 10} | {0x7F}
NAMES = {0xAB: 'Rex', 0x9F: 'Banzai Bill', 0x4F: 'Jumping Piranha', 0xB9: 'Info Box',
         0x95: "Clappin' Chuck", 0xBD: 'Sliding Koopa', 0x83: '? volador',
         0x8E: 'warp invisible', 0xC7: 'champiñón invisible', 0x05: 'Red Koopa (caparazón)',
         0x04: 'Green Koopa', 0x7B: 'cinta de meta', 0x74: 'seta', 0x75: 'flor',
         0x76: 'estrella', 0x78: '1-UP', 0x7F: 'luna 3-UP', 0x21: 'moneda móvil',
         0x0D: 'bob-omb', 0x80: 'llave'}


def name(num):
    return NAMES.get(num, 'sprite')


def ctx():
    vram, _, _ = G.build_vram(G._DEF_SRC, G.LEVEL)
    cg = G.level_cgram(G._DEF_SRC, G.LEVEL)
    return vram, cg


def pose_of(vram, cg, tiles):
    """La variante limpia de g5l (un índice por color) desde las fichas."""
    ox, oy, truth = compose(vram, [list(t) for t in tiles])
    if not truth:
        return None
    colors = {}
    for row in truth:
        for v in row:
            if v is not None:
                colors.setdefault(snes_to_amiga12(cg[128 + 16 * v[0] + v[1]]), None)
    cmap = {c: k + 1 for k, c in enumerate(sorted(colors))}
    rows, maps = [], []
    for row in truth:
        r, seen, rm = [], set(), []
        for v in row:
            if v is None:
                r.append(0)
                continue
            c = snes_to_amiga12(cg[128 + 16 * v[0] + v[1]])
            r.append(cmap[c] if len(cmap) <= 15 else 1)
            if r[-1] not in seen:              # un tramo por índice y fila
                seen.add(r[-1])
                rm.append((v[0], v[1], r[-1], c))
        rows.append(r)
        maps.append(rm)
    return dict(origin=[ox, oy], width=len(truth[0]), height=len(truth), rows=rows,
                row_maps=maps, ncolors=len(cmap),
                rowmax=max(len({x for x in row if x}) for row in rows))


def g5l_cost(pose, cdma, cindex):
    """bytes de variant_record (slow) y de flujos DMA nuevos (chip) por mapa"""
    cols = (pose['width'] + 15) // 16
    try:
        rec = len(L.variant_record(pose, None, 0, [(0, 0)] * cols))
        ok = True
    except ValueError:
        # más de 32 filas o tramos: G5L no lo admite; medir igual el tamaño
        # del registro sin el límite, como si se partiera en franjas de 32
        rec, ok = 0, False
        h = pose['height']
        for y in range(0, h, 32):
            part = dict(pose, rows=pose['rows'][y:y + 32], row_maps=pose['row_maps'][y:y + 32],
                        height=min(32, h - y))
            if not any(any(r) for r in part['rows']):
                continue
            rec += len(L.variant_record(part, None, 0, [(0, 0)] * cols))
    before = len(cdma)
    L.clean_streams(pose, cdma, cindex)
    return rec, len(cdma) - before, ok


def run_inv(a):
    vram, cg = ctx()
    types = collections.defaultdict(lambda: dict(frames=set(), per_frame=collections.Counter(),
                                                 shapes={}, records=0))
    for tr in a.traces:
        for r in R.read_trace('work/oam_%s.trace' % tr, 'work/oracle_%s_oam.bin' % tr):
            t = types[r['num']]
            t['records'] += 1
            t['frames'].add((tr, r['frame']))
            t['per_frame'][(tr, r['frame'])] += 1
            key = (tuple(tuple(x) for x in r['tiles']), r['priority'])
            t['shapes'].setdefault(key, 0)
            t['shapes'][key] += 1
        print('leída', tr, flush=True)
    # cruce: el Rex contra el banco G3 de G5L
    import g2t_ref as T
    import sprgfx_bank as B
    bank = T.load_context(a.bank)
    bank_keys = {B.shape(bank['poses'][v[0]]) for v in bank['directory'].values()}
    rex_keys = set(types[0xAB]['shapes'])
    cross = dict(banco=len(bank_keys), trazas=len(rex_keys), comunes=len(bank_keys & rex_keys),
                 solo_banco=len(bank_keys - rex_keys), solo_trazas=len(rex_keys - bank_keys))
    # tamaño real de la tabla del Rex (g5l.bin): registros de variante
    blob = Path('work/g5l/g5l.bin').read_bytes()
    tab = L.Table(blob)
    sbase = 16 + 2 * L.NHASH
    o, vbase = sbase, None
    vbase = sbase
    for h in range(L.NHASH):
        p = tab.w(16 + 2 * h)
        while p:
            nxt, nt, pri, nv = struct.unpack_from('>HBBH', blob, p)
            vbase += 6 + 4 * nt + 4 * nv
            p = nxt
    cross['g5l_bin'] = len(blob)
    cross['g5l_registros'] = tab.mo - vbase
    cross['g5l_mascaras'] = len(blob) - tab.mo
    out = {}
    for num in sorted(types):
        t = types[num]
        cdma, cindex = bytearray(), {}
        rec = 0
        ws = hs = colsmax = ncol = rowmax = 0
        bad = 0
        tall = 0
        for key in t['shapes']:
            pose = pose_of(vram, cg, key[0])
            if pose is None:
                continue
            ws, hs = max(ws, pose['width']), max(hs, pose['height'])
            colsmax = max(colsmax, (pose['width'] + 15) // 16)
            ncol, rowmax = max(ncol, pose['ncolors']), max(rowmax, pose['rowmax'])
            if pose['ncolors'] > 15:
                bad += 1
            r_, d_, ok = g5l_cost(pose, cdma, cindex)
            rec += r_ + 4 * len(key[0]) + 10            # + entrada de forma (cabecera + fichas + 1 variante)
            tall += not ok
        out['%02X' % num] = dict(nombre=name(num), registros=t['records'], frames=len(t['frames']),
                                 max_simultaneos=max(t['per_frame'].values()),
                                 formas=len(t['shapes']), formas_completas=len(t['full']), ancho_max=ws, alto_max=hs,
                                 columnas_max=colsmax, colores_max=ncol, colores_fila_max=rowmax,
                                 formas_mas_de_15_colores=bad, formas_mas_de_32_filas=tall,
                                 slow_1mapa=rec, chip_dma_1mapa=len(cdma))
        print('%02X %-22s formas %3d  %3dx%-3d col %d  colores %2d (fila %2d)  slow %6d  chip %6d' % (
            num, name(num), len(t['shapes']), ws, hs, colsmax, ncol, rowmax, rec, len(cdma)), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    res = dict(cruce=cross, tipos=out)
    (OUT / 'inv.json').write_text(json.dumps(res, indent=1), encoding='utf-8')
    print('cruce', json.dumps(cross))
    return 0


# ----------------------------------------------------------------------
# inventario sin traza: atribución por posición contra la WRAM del oráculo
# (como mksprgfx.assign, pero con la ranura). Heurístico: una partícula
# cerca de un sprite se le suma; se mide contra SOT1 en yi1.
# ----------------------------------------------------------------------
def s8(v):
    return ((v + 128) & 255) - 128


def assign_slots(oam, wram):
    wr = G.wr
    cx = wr(wram, 0x1A) | wr(wram, 0x1B) << 8
    cy = wr(wram, 0x1C) | wr(wram, 0x1D) << 8
    mx = (wr(wram, 0x94) | wr(wram, 0x95) << 8) - cx
    my = (wr(wram, 0x96) | wr(wram, 0x97) << 8) - cy
    cands = [(-1, -1, mx, my)]
    for i in range(12):
        if wr(wram, 0x14C8 + i) == 0:
            continue
        sx = (wr(wram, 0xE4 + i) | wr(wram, 0x14E0 + i) << 8) - cx
        sy = (wr(wram, 0xD8 + i) | wr(wram, 0x14D4 + i) << 8) - cy
        sx = sx - 0x10000 if sx >= 0x8000 else sx
        sy = sy - 0x10000 if sy >= 0x8000 else sy
        cands.append((i, wr(wram, 0x9E + i), sx, sy))
    objs = collections.defaultdict(list)
    for k in range(0, len(oam), 5):
        x, y, t, a, hi = oam[k:k + 5]
        if y == 0xF0:
            continue
        ex = x | (hi & 1) << 8
        ex = ex - 512 if ex >= 256 else ex
        if is_mario(t, a):
            continue
        best, bd = None, 1 << 30
        for c in cands:
            dx, dy = ex - c[2], y - c[3]
            if -24 <= dx <= 72 and -24 <= dy <= 72:
                d = abs(dx - 8) + abs(dy - 8)
                if d < bd:
                    best, bd = c, d
        if best is None or best[0] < 0:
            objs[None].append((x, y, t, a, hi))
            continue
        objs[best[:4]].append((x, y, t, a, hi))
    return objs


def key_of(cand, ents):
    _, _, sx, sy = cand
    tiles, pris = [], set()
    for x, y, t, a, hi in ents:
        tiles.append((s8(x - sx), s8(y - sy), t | (a & 1) << 8, 16 if hi & 2 else 8,
                      a >> 6 & 1, a >> 7, a >> 1 & 7))
        pris.add(a >> 4 & 3)
    return tuple(tiles), (pris.pop() if len(pris) == 1 else -1)


def run_inv2(a):
    vram, cg = ctx()
    types = collections.defaultdict(lambda: dict(frames=0, per_frame=0, shapes=set(), recs=set()))
    loose = collections.Counter()
    for f in sorted(glob.glob('work/oracle_*_oam.bin')):
        nm = os.path.basename(f)[7:-8]
        txt = 'work/oracle_%s.txt' % nm
        if not os.path.exists(txt):
            continue
        for fr, oam, wram in G.load_oam_bin(f, txt):
            if wram is None:
                continue
            objs = assign_slots(oam, wram)
            cnt = collections.Counter()
            for cand, ents in objs.items():
                if cand is None:
                    loose[nm] += len(ents)
                    continue
                num = cand[1]
                cnt[num] += 1
                types[num]['shapes'].add(key_of(cand, ents))
                types[num]['recs'].add(nm)
            for num, n in cnt.items():
                types[num]['frames'] += 1
                types[num]['per_frame'] = max(types[num]['per_frame'], n)
        print('leída', nm, flush=True)
    out = {}
    for num in sorted(types):
        t = types[num]
        cdma, cindex = bytearray(), {}
        rec = ws = hs = colsmax = ncol = rowmax = bad = tall = 0
        for key in t['shapes']:
            pose = pose_of(vram, cg, key[0])
            if pose is None:
                continue
            ws, hs = max(ws, pose['width']), max(hs, pose['height'])
            colsmax = max(colsmax, (pose['width'] + 15) // 16)
            ncol, rowmax = max(ncol, pose['ncolors']), max(rowmax, pose['rowmax'])
            bad += pose['ncolors'] > 15
            r_, d_, ok = g5l_cost(pose, cdma, cindex)
            rec += r_
            tall += not ok
        out['%02X' % num] = dict(nombre=name(num), frames=t['frames'], max_simultaneos=t['per_frame'],
                                 formas=len(t['shapes']), formas_completas=len(t['full']), ancho_max=ws, alto_max=hs, columnas_max=colsmax,
                                 colores_max=ncol, colores_fila_max=rowmax, formas_mas_de_15_colores=bad,
                                 formas_mas_de_32_filas=tall, slow_1mapa=rec, chip_dma_1mapa=len(cdma),
                                 grabaciones=len(t['recs']))
        print('%02X %-22s frames %6d max %2d formas %4d  %3dx%-3d col %d  colores %2d (fila %2d)  >15c %3d  >32f %3d  slow %7d  chip %6d' % (
            num, name(num), t['frames'], t['per_frame'], len(t['shapes']), ws, hs, colsmax, ncol, rowmax,
            bad, tall, rec, len(cdma)), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'inv2.json').write_text(json.dumps(dict(tipos=out, sueltas=dict(loose)), indent=1,
                                              ensure_ascii=False), encoding='utf-8')
    print('sueltas (sin dueño):', sum(loose.values()))
    return 0


# ----------------------------------------------------------------------
# inventario exacto: trazas SOT1 completas del host (marioverify.c con
# GAME_OAM_TRACE, como docs/informe-g2.md, sin el filtro de 4 tipos). Un
# despacho cuya OAM no está en la de la SNES se cuenta aparte (no aborta).
# ----------------------------------------------------------------------
def read_sot1(path, oracle, bad):
    recordings = {f: [o[i:i + 5] for i in range(0, len(o), 5)] for f, o, _ in G.load_oam_bin(oracle)}
    with open(path, 'rb') as h:
        assert h.read(4) == b'SOT1'
        mlen, = struct.unpack('<I', h.read(4))
        while True:
            head = h.read(8)
            if len(head) < 8:
                break
            frame, slot, num, first, n = struct.unpack('<IBBBB', head)
            body = h.read(2 * (0x2000 + mlen))
            ram = body[0x2000 + mlen:0x4000 + mlen]
            vis = []
            for c in range(n):
                s = 64 + first // 4 + c
                e = ram[0x200 + 4 * s:0x204 + 4 * s] + ram[0x420 + s:0x421 + s]
                if e[1] != 0xF0:
                    vis.append(e)
            if not vis:
                continue
            rec = recordings.get(frame)
            if rec is None or not any(rec[k:k + len(vis)] == vis for k in range(len(rec) - len(vis) + 1)):
                bad['%02X' % num] += 1
                continue
            sx = (ram[0xE4 + slot] | ram[0x14E0 + slot] << 8) - (ram[0x1A] | ram[0x1B] << 8)
            sy = (ram[0xD8 + slot] | ram[0x14D4 + slot] << 8) - (ram[0x1C] | ram[0x1D] << 8)
            sx = sx - 0x10000 if sx >= 0x8000 else sx
            sy = sy - 0x10000 if sy >= 0x8000 else sy
            tiles, pris = [], set()
            for x, y, t, at, hi in vis:
                tiles.append((s8(x - sx), s8(y - sy), t | (at & 1) << 8, 16 if hi & 2 else 8,
                              at >> 6 & 1, at >> 7, at >> 1 & 7))
                pris.add(at >> 4 & 3)
            ex = [((x | (hi & 1) << 8) + 256) % 512 - 256 for x, y, t, at, hi in vis]
            ey = [y - 256 if y >= 0xF0 else y for x, y, t, at, hi in vis]
            sz = [16 if hi & 2 else 8 for *_, hi in vis]
            # por ficha, recortada a la pantalla (un objeto en el borde puede
            # tener fichas a los dos lados: X de 9 bits)
            rects = [(max(0, p), min(256, p + q), max(0, v + 1), min(ROWS, v + 1 + q))
                     for p, v, q in zip(ex, ey, sz)]
            rects = [r_ for r_ in rects if r_[0] < r_[1] and r_[2] < r_[3]]
            box = (rects and min(r_[2] for r_ in rects), rects and max(r_[3] for r_ in rects), rects)
            yield dict(frame=frame, slot=slot, num=num, tiles=tuple(tiles),
                       priority=pris.pop() if len(pris) == 1 else -1, box=box, recorded=rec)


def run_traceall(a):
    import subprocess
    vram, cg = ctx()
    types = collections.defaultdict(lambda: dict(frames=set(), per_frame=collections.Counter(),
                                                 shapes=set(), recs=set()))
    bad = collections.Counter()
    bobst = {}
    names = a.recs or sorted(os.path.basename(f)[7:-8] for f in glob.glob('work/oracle_*_oam.bin'))
    OUT.mkdir(parents=True, exist_ok=True)
    for nm in names:
        orc = 'work/oracle_%s.bin' % nm
        if not os.path.exists(orc):
            continue
        tr = OUT / ('%s.trace' % nm)
        env = dict(os.environ, GAME_OAM_TRACE=str(tr))
        with open(OUT / ('%s_host.log' % nm), 'w') as lg:
            subprocess.run([a.host, orc, 'game'], env=env, stdout=lg, stderr=subprocess.STDOUT)
        frames = collections.defaultdict(list)
        mrows_of = {}
        for r in read_sot1(str(tr), 'work/oracle_%s_oam.bin' % nm, bad):
            t = types[r['num']]
            t['frames'].add((nm, r['frame']))
            t['per_frame'][(nm, r['frame'])] += 1
            t['shapes'].add((r['tiles'], r['priority']))
            t['recs'].add(nm)
            if r['box'][2]:
                frames[r['frame']].append((r['num'],) + r['box'])
                if r['frame'] not in mrows_of:
                    mrows_of[r['frame']] = frame_lines(b''.join(r['recorded']))[1]
        tr.unlink()
        bobst[nm] = bob_bound(frames, mrows_of)
        print(nm, 'bobs', json.dumps(bobst[nm], ensure_ascii=False), flush=True)
    out = {}
    tot_slow = tot_chip = 0
    dump = {}
    for num in sorted(types):
        t = types[num]
        # una pose recortada por el borde (sus fichas visibles son un
        # subconjunto estricto de otra forma del mismo tipo) no necesita
        # registro propio si el motor recorta: se cuenta aparte
        full = [k for k in t['shapes']
                if not any(o[1] == k[1] and set(k[0]) < set(o[0]) for o in t['shapes'])]
        dump['%02X' % num] = dict(todas=[list(map(list, k[0])) + [k[1]] for k in t['shapes']],
                                  completas=len(full))
        t['full'] = full
        cdma, cindex = bytearray(), {}
        rec = ws = hs = colsmax = ncol = rowmax = bad15 = tall = 0
        for key in full:
            pose = pose_of(vram, cg, key[0])
            if pose is None:
                continue
            ws, hs = max(ws, pose['width']), max(hs, pose['height'])
            colsmax = max(colsmax, (pose['width'] + 15) // 16)
            ncol, rowmax = max(ncol, pose['ncolors']), max(rowmax, pose['rowmax'])
            bad15 += pose['ncolors'] > 15
            r_, d_, ok = g5l_cost(pose, cdma, cindex)
            rec += r_ + 6 + 4 * len(key[0]) + 4      # + la forma en el directorio
            tall += not ok
        tot_slow += rec
        tot_chip += len(cdma)
        out['%02X' % num] = dict(nombre=name(num), frames=len(t['frames']),
                                 max_simultaneos=max(t['per_frame'].values()),
                                 formas=len(t['shapes']), formas_completas=len(t['full']), ancho_max=ws, alto_max=hs, columnas_max=colsmax,
                                 colores_max=ncol, colores_fila_max=rowmax, formas_mas_de_15_colores=bad15,
                                 formas_mas_de_32_filas=tall, slow_1mapa=rec, chip_dma_1mapa=len(cdma),
                                 grabaciones=sorted(t['recs']))
        print('%02X %-22s frames %6d max %2d formas %4d (completas %4d)  %3dx%-3d col %d  colores %2d (fila %2d)  >15c %3d  >32f %3d  slow %7d  chip %6d' % (
            num, name(num), len(t['frames']), max(t['per_frame'].values()), len(t['shapes']), len(t['full']), ws, hs,
            colsmax, ncol, rowmax, bad15, tall, rec, len(cdma)), flush=True)
    res = dict(tipos=out, total_slow_1mapa=tot_slow, total_chip_1mapa=tot_chip,
               despachos_distintos_de_snes=dict(bad), bobs=bobst)
    (OUT / 'shapes.json').write_text(json.dumps(dump), encoding='utf-8')
    (OUT / 'traceall.json').write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding='utf-8')
    print('total 1 mapa: slow', tot_slow, 'chip', tot_chip, '| despachos distintos de la SNES', dict(bad))
    return 0


def bob_bound(frames, mrows_of):
    """objetos enteros a los canales en orden de despacho; lo que no entra, bob"""
    st = collections.Counter()
    bt = collections.Counter()
    areas = []
    for fr in sorted(frames):
        mrows = mrows_of.get(fr, set())
        cap = [2 if {y - 1, y, y + 1} & mrows else 4 for y in range(ROWS)]
        used = [0] * ROWS
        nb = area = 0
        for num, y0, y1, rects in frames[fr]:
            k = cover([(r_[0], r_[1]) for r_ in rects])
            lo = max(0, y0 - 1)                         # G0: PT una línea antes
            if all(used[y] + k <= cap[y] for y in range(lo, y1)):
                for y in range(lo, y1):
                    used[y] += k
            else:
                nb += 1
                area += len({(x, y) for x0, x1, ya, yb in rects for x in range(x0, x1) for y in range(ya, yb)})
                bt['%02X %s' % (num, name(num))] += 1
        st['frames'] += 1
        st['frames_con_bob'] += bool(nb)
        st['max_bobs'] = max(st['max_bobs'], nb)
        areas.append(area)
    areas.sort()
    return dict(st, area_max=areas[-1] if areas else 0,
                area_p99=areas[int(0.99 * (len(areas) - 1))] if areas else 0,
                por_tipo=dict(bt.most_common()))


# ----------------------------------------------------------------------
# demanda por línea
# ----------------------------------------------------------------------
def entries_xy(oam):
    for i in range(0, len(oam), 5):
        x, y, t, a, hi = oam[i:i + 5]
        if y == 0xF0:
            continue
        ex = x | (hi & 1) << 8
        ex = ex - 512 if ex >= 256 else ex
        ey = y - 256 if y >= 0xF0 else y
        yield ex, ey + 1, t, a, 16 if hi & 2 else 8     # +1: la OAM dibuja una línea más abajo


def is_mario(t, a):
    return not (a >> 1) & 7 and not a & 1 and t in MARIO_TILES


def cover(iv):
    """mínimo de ventanas de 16 px que cubren los intervalos [a, b)"""
    n, end = 0, -1
    for a, b in sorted(iv):
        if b <= end:
            continue
        x = max(a, end)
        while x < b:
            n += 1
            end = x + 16
            x = end
    return n


def frame_lines(oam):
    lines = collections.defaultdict(list)
    mrows = set()
    for ex, ey, t, a, sz in entries_xy(oam):
        x0, x1 = max(0, ex), min(256, ex + sz)
        if x0 >= x1:
            continue
        for y in range(max(0, ey), min(ROWS, ey + sz)):
            if is_mario(t, a):
                mrows.add(y)
            else:
                lines[y].append((x0, x1))
    return {y: cover(iv) for y, iv in lines.items()}, mrows


def run_lines(a):
    res = {}
    for f in sorted(glob.glob('work/oracle_*_oam.bin')):
        nm = os.path.basename(f)[7:-8]
        st = collections.Counter()
        hist = collections.Counter()
        for fr, oam, _ in G.load_oam_bin(f):
            cols, mrows = frame_lines(oam)
            st['frames'] += 1
            mx = max(cols.values(), default=0)
            hist[mx] += 1
            st['max'] = max(st['max'], mx)
            over2 = [y for y, c in cols.items() if c > 2]
            over4 = [y for y, c in cols.items() if c > 4]
            # sin Mario en la línea (±1), los canales 0-3 también sirven
            over_free = [y for y, c in cols.items()
                         if c > (2 if {y - 1, y, y + 1} & mrows else 4)]
            st['frames_mas_de_2'] += bool(over2)
            st['frames_mas_de_4'] += bool(over4)
            st['frames_sobre_capacidad'] += bool(over_free)
            st['lineas_mas_de_2'] += len(over2)
            st['lineas_sobre_capacidad'] += len(over_free)
        res[nm] = dict(st, hist={str(k): v for k, v in sorted(hist.items())})
        print('%-22s frames %5d  max %d  >2: %5d  >4: %5d  sobre cap.: %5d  líneas sobre cap.: %6d' % (
            nm, st['frames'], st['max'], st['frames_mas_de_2'], st['frames_mas_de_4'],
            st['frames_sobre_capacidad'], st['lineas_sobre_capacidad']), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'lines.json').write_text(json.dumps(res, indent=1), encoding='utf-8')
    return 0


# ----------------------------------------------------------------------
# cota de bobs (objetos enteros, orden de despacho)
# ----------------------------------------------------------------------
def run_bobs(a):
    res = {}
    for tr in a.traces:
        frames = collections.defaultdict(list)
        mario = {}
        for r in R.read_trace('work/oam_%s.trace' % tr, 'work/oracle_%s_oam.bin' % tr):
            ys, xs = [], []
            for dx, dy, tile, size, fx, fy, pal in r['tiles']:
                xs += [r['sx'] + dx, r['sx'] + dx + size]
                ys += [r['sy'] + dy + 1, r['sy'] + dy + 1 + size]
            sy = lambda v: v - 0x10000 if v >= 0x8000 else v
            x0, x1 = max(0, min(xs)), min(256, max(xs))
            y0, y1 = max(0, min(sy(v) for v in ys)), min(ROWS, max(sy(v) for v in ys))
            if x0 >= x1 or y0 >= y1:
                continue
            frames[r['frame']].append((r['num'], x0, x1, y0, y1))
            if r['frame'] not in mario:
                _, mrows = frame_lines(b''.join(r['recorded']))
                mario[r['frame']] = mrows
        st = collections.Counter()
        bob_types = collections.Counter()
        bob_area = []
        for fr in sorted(frames):
            mrows = mario[fr]
            cap = [2 if {y - 1, y, y + 1} & mrows else 4 for y in range(ROWS)]
            used = [0] * ROWS
            nb = area = 0
            for num, x0, x1, y0, y1 in frames[fr]:
                k = cover([(x0, x1)])
                lo = max(0, y0 - 1)                     # G0: una línea antes para PT
                if all(used[y] + k <= cap[y] for y in range(lo, y1)):
                    for y in range(lo, y1):
                        used[y] += k
                else:
                    nb += 1
                    area += (x1 - x0) * (y1 - y0)
                    bob_types[num] += 1
            st['frames'] += 1
            st['frames_con_bob'] += bool(nb)
            st['max_bobs'] = max(st['max_bobs'], nb)
            st['bobs'] += nb
            bob_area.append(area)
        bob_area.sort()
        res[tr] = dict(st, area_bob_max=bob_area[-1] if bob_area else 0,
                       area_bob_p99=bob_area[int(0.99 * (len(bob_area) - 1))] if bob_area else 0,
                       por_tipo={'%02X %s' % (k, name(k)): v for k, v in bob_types.most_common()})
        print(tr, json.dumps(res[tr], ensure_ascii=False), flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'bobs.json').write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding='utf-8')
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    i = sub.add_parser('inv')
    i.add_argument('--traces', nargs='+', default=list(TRACES))
    i.add_argument('--bank', default='work/g3/bank')
    sub.add_parser('inv2')
    t = sub.add_parser('traceall')
    t.add_argument('--host', default='work/g4a/host.exe')
    t.add_argument('--recs', nargs='*')
    sub.add_parser('lines')
    b = sub.add_parser('bobs')
    b.add_argument('--traces', nargs='+', default=list(TRACES))
    a = ap.parse_args()
    return dict(inv=run_inv, inv2=run_inv2, traceall=run_traceall, lines=run_lines, bobs=run_bobs)[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())
