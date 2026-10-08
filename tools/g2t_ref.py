#!/usr/bin/env python3
"""G2T-A: modelo horizontal calibrado y puerta offline A-T.

Contrato fijado el 2026-10-07 (instrucciones-g2t-a.md §1-bis). Sin ROM en
git: lee las trazas SOT1, el banco G3 inmutable y los derivados de work/.

Filas en coordenadas del copper: la fila R de la Amiga muestra la OAM con
y = R - 1 (mspr.c: vs = $2C + y + 1). El segmento R de la lista lleva el
sufijo que prepara la fila R + 1; el bloque VBL (R = -1) arma SPR4-7 y
pone los colores de partida distintos de R_PAL.

Plazos medidos (tools/g2t_cal.py, suites main y cap, WinUAE exacto):
  - en pantalla, P42/P51 de scrollsim (16 px por MOVE hasta x = 239, 8 px
    después) salvo 231 -> 243 (P110), medido con sondas de COLOR01 de $74
    a $CE y con sprites en el borde de cada MOVE (suites knee y final);
  - el último MOVE del sufijo cae en x <= 351 - 8 nb (nb = MOVE del borrado
    siguiente, 7/8/9) en esas mismas unidades: con WAIT $D0 y copper libre
    k <= 12 - nb (primer MOVE equivalente a x = 263); encadenado tras una
    carga en x = 255, idem; con WAIT tras esa carga, dos menos (no se usa);
  - un WAIT solo con el copper libre: x(h) - última carga >= 48 (medido);
  - cruce PAL255: WAIT ($FF,$DE) sustituye al del sufijo, capacidad K255.
Lo que cae fuera de estos casos es sin_plazo: falla la puerta.
"""
import argparse
import collections
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

import g5ref as R
import mksprgfx as G
import mkmario
import scrollprof as P
import scrollsim as S
import sprgfx_bank as B
import sprgfx_final as F
from g0bench import control, rgb
from smw2amiga import decode_snes_tile
from sprgfx_manifest import signed

ROWS = 224
V0 = 0x2c
END = {7: 351 - 56, 8: 351 - 64, 9: 351 - 72}   # último MOVE del sufijo
X_D0 = 263               # primer MOVE tras WAIT $D0 (equivale a k <= 12 - nb)
IDLE = 48                # WAIT con el copper libre: medido con 48 px o más
K255 = {7: 0}            # cruce PAL255: se amplía solo con medidas (§3)
VBL_ARM = 30             # línea del bloque VBL (medido: 26, 27, 30; 16 falla)
VBL_COLORS = 15          # colores de partida en el bloque VBL
SUFFIX_SLOTS = 9         # 36 B: WAIT opcional + MOVE/NOP (sin WAIT, nueve)
WRAP_SEG = 255 - V0      # el segmento que cruza la línea 255


def advance(x, n=1):
    """scrollsim.advance con el paso medido en el codo (sonda G2T-A, P110):
    el MOVE siguiente a uno en x = 231 cae en x = 243, no en 247."""
    S.W = 256
    for _ in range(n):
        x = 243 if x == 231 else S.advance(x)
    return x


def xh(h):
    S.W = 256
    F.require(h <= 0xce, 'h fuera del modelo medido')
    return S.xh(h)


def htab(x):
    """h del WAIT para que el MOVE caiga en x' >= x (scroll.s htab, 256 px)."""
    if x <= 239:
        return 0x48 + 4 * ((x + 8) >> 3)
    return 0xce if x >= 252 else 0xc4 + ((x - 240) & ~3)


# ----------------------------------------------------------------------
# Mario desde sus flujos, como mspr.c (la foto O5 lleva el buffer dibujado)
# ----------------------------------------------------------------------
def mario_amiga(ram, recorded, gfx):
    """{(x, R): índice} de las dos parejas que arma mario_sprite().

    Las entradas son las de VRAM dinámica y paleta 0 en orden OAM (las
    mismas que mario_pixels); la primera opaca tapa a las siguientes.
    """
    dyn = R.dynamic_tiles(ram, len(gfx))
    entries = []
    for x, y, tile, attr, hi in recorded:
        if (attr >> 1) & 7 or attr & 1 or tile not in dyn or y == 0xf0:
            continue
        ex = x | (hi & 1) << 8
        ex = ex - 512 if ex >= 256 else ex
        ey = y - 256 if y >= 0xf0 else y
        entries.append((ex, ey, tile, attr, 16 if hi & 2 else 8))
    if not entries:
        return {}, 'sin_mario'
    if len(entries) > 4:
        return {}, 'mas_de_4'
    bx = min(e[0] for e in entries)
    by = min(e[1] for e in entries)
    x1 = max(e[0] + e[4] for e in entries)
    y1 = max(e[1] + e[4] for e in entries)
    if x1 - bx > 32 or y1 - by > 40:
        return {}, 'caja_grande'
    canvas = {}
    for ex, ey, tile, attr, size in entries:
        hf, vf, nt = attr >> 6 & 1, attr >> 7, size // 8
        for ty in range(nt):
            for tx in range(nt):
                t = tile + (nt - 1 - tx if hf else tx) + 16 * (nt - 1 - ty if vf else ty)
                if t not in dyn:
                    continue
                rows = decode_snes_tile(gfx[32 * dyn[t]:32 * dyn[t] + 32], 4)
                for r in range(8):
                    src = rows[7 - r if vf else r]
                    for c in range(8):
                        v = src[7 - c if hf else c]
                        key = (ex - bx + 8 * tx + c, ey - by + 8 * ty + r)
                        if v and key not in canvas:
                            canvas[key] = v
    cols = 2 if x1 - bx > 16 else 1
    out = {}
    for (cx, cy), v in canvas.items():
        xx, rr = bx + cx, by + 1 + cy
        if cx < 16 * cols and 0 <= xx < 256 and 0 <= rr < ROWS:
            out[xx, rr] = v
    return out, 'ok'


def mario_check(ram, recorded, gfx):
    """Diferencias Amiga/SNES en las filas comunes (R = 1..223)."""
    amiga, status = mario_amiga(ram, recorded, gfx)
    snes = R.mario_pixels(ram, recorded, gfx)
    truth = {(x, y + 1): v for (x, y), (v, _) in snes.items() if y + 1 < ROWS}
    common = {k: v for k, v in amiga.items() if k[1] >= 1}
    diff = sum(1 for k in set(common) | set(truth) if common.get(k) != truth.get(k))
    extra = dict(fila0_solo_amiga=sum(1 for k in amiga if k[1] == 0),
                 fila224_solo_snes=sum(1 for (x, y) in snes if y + 1 == ROWS))
    return amiga, diff, status, extra


# ----------------------------------------------------------------------
# Lista real: cargas de build_mid por segmento
# ----------------------------------------------------------------------
def segments(mem, base, cl, seg):
    """Por fila: nb del borrado, x de la última carga (modelo) y si cruza 255.

    Semántica de scrollsim.run_list: T es la x de la próxima ranura del
    copper; un MOVE cae en T y T avanza; un WAIT deja T = max(T + 2, x(h)).
    """
    out = []
    for L in range(ROWS):
        a = base + cl + seg * L
        v = L + V0
        nb, T, stage, loads, wrap, last = 0, None, 0, [], False, None
        for o in range(0, seg, 4):
            w1 = mem.r16(a + o)
            if w1 == 0x84:
                break
            if stage == 0 and w1 & 1 and (w1 >> 8 == (v - 1) & 255 or w1 == 0xffdf):
                wrap |= w1 == 0xffdf
                continue
            if stage == 0 and w1 == 0x1fe and o < 8:
                continue            # NOP del cruce 255 en lugar de un WAIT
            if stage == 0 and not w1 & 1 and w1 != 0x1fe:
                nb += 1
                continue
            if stage == 0:
                stage, T = 1, S.T0 + max(0, 16 * (nb - 9))
            if w1 & 1:
                T = max(advance(T, 2), xh(w1 & 0xfe))
                loads.append([w1 & 0xfe, 0])
            else:
                last = T
                T = advance(T)
                if loads:
                    loads[-1][1] += 1
        else:
            raise F.FormatError('salto no encontrado')
        F.require(last is None or last <= 255, 'carga después de LASTX')
        out.append(dict(nb=nb, last=last, loads=[tuple(l) for l in loads], wrap=wrap,
                        free=S.T0 + max(0, 16 * (nb - 9))))
    return out


def segment_words(mem, base, cl, seg, L):
    """Palabras del segmento L hasta el salto (sin incluirlo)."""
    a = base + cl + seg * L
    out = []
    for o in range(0, seg, 4):
        w1, w2 = mem.r16(a + o), mem.r16(a + o + 2)
        if w1 == 0x84:
            return out, (w1, w2, mem.r16(a + o + 4), mem.r16(a + o + 6), mem.r16(a + o + 8), mem.r16(a + o + 10))
        out.append((w1, w2))
    raise F.FormatError('salto no encontrado')


def suffix_words(L, plan, moves):
    words = []
    if plan['tipo'] == 'wait':
        words.append((((L + V0) & 255) << 8 | plan['h'] | 1, 0xfffe))
    words += [(0x1fe, 0)] * plan['nop']
    words += [(0x1a0 + 2 * i, v) for i, v in moves]
    return words


def timeline(words, L):
    """Eventos (x, registro, valor) del segmento con el modelo de segments()."""
    v = L + V0
    nb, T, stage, events = 0, None, 0, []
    for o, (w1, w2) in enumerate(words):
        if stage == 0 and w1 & 1 and (w1 >> 8 == (v - 1) & 255 or w1 == 0xffdf):
            continue
        if stage == 0 and w1 == 0x1fe and o < 2:
            continue
        if stage == 0 and not w1 & 1 and w1 != 0x1fe:
            nb += 1
            events.append((-1, w1, w2))
            continue
        if stage == 0:
            stage, T = 1, S.T0 + max(0, 16 * (nb - 9))
        if w1 & 1:
            T = max(advance(T, 2), xh(w1 & 0xfe) if (w1 & 0xfe) <= 0xce else X_D0)
        else:
            events.append((T, w1, w2))
            T = advance(T)
    return events


def check_list(mem, base, cl, seg, sufijos):
    """Capa 1 igual a la lista sin sufijo; posiciones re-derivadas de los bytes."""
    capa1 = posiciones = 0
    longest = 0
    for L in range(ROWS):
        words, jump = segment_words(mem, base, cl, seg, L)
        s = sufijos.get(L)
        new = words + (suffix_words(L, s, s['moves']) if s else [])
        longest = max(longest, 4 * (len(new) + 3))
        old_ev, new_ev = timeline(words, L), timeline(new, L)
        pf = lambda ev: [e for e in ev if 0x182 <= e[1] <= 0x19e]
        capa1 += pf(old_ev) != pf(new_ev)
        if s:
            got = [x for x, reg, _ in new_ev if 0x1a2 <= reg <= 0x1be]
            posiciones += got != s['pos']
    return capa1, posiciones, longest


def schedule(seg, nxt, moves, row):
    """Coloca k MOVE en el sufijo del segmento: posiciones o None.

    moves = [x mínimo de cada MOVE]. Prueba encadenar (con NOP si hace
    falta) y un WAIT con el copper libre; elige el que termina antes.
    """
    k = len(moves)
    if not k:
        return dict(tipo='vacio', pos=[], nop=0)
    need = max(moves)
    if row == WRAP_SEG:
        if k <= K255.get(nxt['nb'], -1):
            return dict(tipo='ffdf', pos=[None] * k, nop=0)
        return None
    end = END.get(nxt['nb'])
    if end is None:
        return None
    best = None
    t = seg['last'] if seg['last'] is not None else seg['free']
    # Encadenado solo detrás de una carga: su WAIT ancla la x (P42/P51). El
    # final del borrado es aproximado (P43): sin cargas, siempre WAIT.
    if seg['last'] is not None:
        pos, nop = advance(t), 0
        while pos < need:
            pos, nop = advance(pos), nop + 1
        chain = [pos] + [advance(pos, j) for j in range(1, k)]
        if nop + k <= SUFFIX_SLOTS and chain[-1] <= end:
            best = dict(tipo='cadena', pos=chain, nop=nop)
    # WAIT con el copper libre: x(h) a 48 px o más de la última carga.
    if need <= 255:
        h = htab(need)
        first = xh(h)
        if first - t >= IDLE:
            wait = [first] + [advance(first, j) for j in range(1, k)]
            if k + 1 <= SUFFIX_SLOTS and wait[-1] <= end and (best is None or wait[-1] < best['pos'][-1]):
                best = dict(tipo='wait', h=h, pos=wait, nop=0)
    elif t <= 255 - IDLE:
        wait = [X_D0 + 8 * j for j in range(k)]
        if k + 1 <= SUFFIX_SLOTS and wait[-1] <= end and (best is None or wait[-1] < best['pos'][-1]):
            best = dict(tipo='wait', h=0xd0, pos=wait, nop=0)
    return best


# ----------------------------------------------------------------------
# Plan de un frame
# ----------------------------------------------------------------------
def uses_of(pose, x0, r0, mario, colors):
    """Usos por (fila, índice): color y envolvente [primer x, último x]."""
    uses = collections.defaultdict(dict)

    def add(x, rr, i, color, owner):
        if not (0 <= x < 256 and 0 <= rr < ROWS):
            return
        u = uses[rr].get(i)
        if u is None:
            uses[rr][i] = dict(color=color, first=x, last=x, owners={owner})
        else:
            F.require(u['color'] == color, 'índice con dos colores en la fila (A3)')
            u['first'], u['last'] = min(u['first'], x), max(u['last'], x)
            u['owners'].add(owner)
    for (x, rr), i in mario.items():
        add(x, rr, i, colors[i], 'M')
    for r, row in enumerate(pose['rows']):
        cmap = {d: c for _, _, d, c in pose['row_maps'][r]}
        for x, d in enumerate(row):
            if d:
                add(x0 + x, r0 + r, d, cmap[d], 'R')
    return uses


def a3_compatible(pose, r0, mario_rows, colors):
    """Filtro A3 original por fila, en filas del copper."""
    for r, row_map in enumerate(pose['row_maps']):
        rr = r0 + r
        if 0 <= rr < ROWS:
            for _, _, d, color in row_map:
                if mario_rows[rr] >> d & 1 and colors[d] != color:
                    return False
    return True


def transitions(uses, colors):
    out = []
    for i in range(1, 16):
        value, prev, prev_last = colors[i], -1, None
        for rr in range(ROWS):
            u = uses[rr].get(i) if rr in uses else None
            if u is None:
                continue
            if u['color'] != value:
                out.append(dict(indice=i, valor=u['color'], desde=prev, x_ultimo=prev_last,
                                hasta=rr, x_primero=u['first']))
                value = u['color']
            prev, prev_last = rr, u['last']
    return out


def place(trans, segs):
    """Voraz por ventana más corta; segmento más tardío primero."""
    lines = collections.defaultdict(list)
    plans, missed = {}, []
    order = sorted(trans, key=lambda t: (t['hasta'] - t['desde'], t['hasta'], t['indice']))
    for t in order:
        lo = t['desde']
        candidates = list(range(t['hasta'] - 1, max(lo, -1) - 1, -1))
        done = False
        for s in candidates:
            if s == -1:
                if len(lines[-1]) < VBL_COLORS:
                    lines[-1].append(t)
                    t['segmento'], t['x'] = -1, None
                    done = True
                    break
                continue
            trial = lines[s] + [t]
            reqs = [(m['x_ultimo'] + 1 if m['desde'] == s and m['x_ultimo'] is not None else 0)
                    for m in trial]
            plan = schedule(segs[s], segs[s + 1], reqs, s) if s + 1 < ROWS else None
            if plan is not None:
                lines[s] = trial
                plans[s] = plan
                done = True
                break
        if not done:
            missed.append(t)
    # Posición de cada MOVE: se escriben en orden de x mínimo creciente.
    for s, moves in lines.items():
        if s == -1:
            continue
        moves.sort(key=lambda m: (m['x_ultimo'] + 1 if m['desde'] == s and m['x_ultimo'] is not None else 0,
                                  m['indice']))
        for m, p in zip(moves, plans[s]['pos']):
            m['segmento'], m['x'] = s, p
    return lines, plans, missed


def simulate(uses, trans, colors):
    """Errores de color: cada uso (también ocluido) contra el último MOVE."""
    writes = collections.defaultdict(list)
    for t in trans:
        if 'segmento' in t:
            key = (t['segmento'], 999 if t['x'] is None or t['x'] >= 256 else t['x'])
            writes[t['indice']].append((key, t['valor']))
    errors = []
    for rr, row in uses.items():
        for i, u in row.items():
            for x in (u['first'], u['last']):
                value = colors[i]
                for key, val in sorted(writes[i]):
                    if key < (rr, x):
                        value = val
                if value != u['color']:
                    errors.append(dict(fila=rr, x=x, indice=i))
    return errors


def pixel_errors(mario, rexpix, trans, colors):
    """Comprobación por píxel (no solo envolventes) de Mario y Rex visibles."""
    writes = collections.defaultdict(list)
    for t in trans:
        if 'segmento' in t:
            writes[t['indice']].append(((t['segmento'], 999 if t['x'] is None or t['x'] >= 256 else t['x']),
                                        t['valor']))
    for i in writes:
        writes[i].sort()

    def value(i, rr, x):
        v = colors[i]
        for key, val in writes[i]:
            if key < (rr, x):
                v = val
            else:
                break
        return v
    bad = 0
    states = {}
    for (x, rr), i in mario.items():
        got = value(i, rr, x)
        states[x, rr] = got
        bad += got != colors[i]
    for (x, rr), (d, color) in rexpix.items():
        got = value(d, rr, x)
        states.setdefault((x, rr), got)
        bad += got != color
    return bad, states


def choose(variants, attempt):
    """A3-T: la primera variante del directorio (ya filtrada por A3) con plan."""
    witness = None
    for n in variants:
        missed, found = attempt(n)
        if not missed:
            return n, found, witness
        if witness is None:
            witness = dict(variante=n, n=len(missed), sin_plazo=[dict(m) for m in missed[:4]])
    return None, None, witness


def plan_frame(recs, ctx, segs):
    poses, directory, tables, dma = ctx['poses'], ctx['directory'], ctx['tables'], ctx['dma']
    rex = [r for r in recs if r['num'] == 0xab]
    chosen = min(rex, key=lambda r: (r['sy'] + poses[directory[B.shape(r)][0]]['origin'][1], r['slot']))
    ram, recorded = chosen['ram'], chosen['recorded']
    pi = R.palette_index(ram, ctx['pointers'])
    colors = struct.unpack_from('>16H', ctx['pals'], 32 * pi)
    mario, mdiff, mstatus, mextra = mario_check(ram, recorded, ctx['gfx'])
    mrows = [0] * ROWS
    for (x, rr), i in mario.items():
        mrows[rr] |= 1 << i
    shape = B.shape(chosen)
    compatible = [n for n in directory[shape]
                  if a3_compatible(poses[n], chosen['sy'] + poses[n]['origin'][1] + 1, mrows, colors)]
    result = dict(frame=chosen['frame'], slot=chosen['slot'], sx=chosen['sx'], sy=chosen['sy'],
                  paleta=pi, variante_a3=compatible[0] if compatible else None, variante=None,
                  mario=dict(estado=mstatus, diferencias=mdiff, **mextra),
                  contadores=dict(sin_destino=len(rex) - 1, sin_variante_temporal=0, sin_plazo=0,
                                  errores_color=0, errores_capa1=0, prioridad_distinta=0))
    ev = dict(colors=colors, mario=mario, rex={}, states={}, chosen=chosen)

    def attempt(n):
        pose = poses[n]
        x0 = chosen['sx'] + pose['origin'][0]
        r0 = chosen['sy'] + pose['origin'][1] + 1
        uses = uses_of(pose, x0, r0, mario, colors)
        trans = transitions(uses, colors)
        lines, plans, missed = place(trans, segs)
        return missed, (pose, x0, r0, uses, trans, lines, plans)
    n, found, witness = choose(compatible, attempt)
    if n is None:
        result['contadores']['sin_variante_temporal'] = 1
        result['testigo'] = witness
        return result, ev
    pose, x0, r0, uses, trans, lines, plans = found
    # --- validación independiente del plan elegido ---
    rexpix = {}
    for r, row in enumerate(pose['rows']):
        cmap = {d: c for _, _, d, c in pose['row_maps'][r]}
        for x, d in enumerate(row):
            if d and 0 <= x0 + x < 256 and 0 <= r0 + r < ROWS:
                rexpix[x0 + x, r0 + r] = (d, cmap[d])
    # Fuente SNES independiente: mismas fichas, mismo índice DMA por píxel.
    ox, oy, truth = F.compose(ctx['vram'], chosen['tiles'], independent=True)
    F.require([ox, oy] == pose['origin'] and len(truth) == pose['height'], 'origen de fuente distinto')
    for r, row in enumerate(pose['rows']):
        mapping = {(p, i): (d, c) for p, i, d, c in pose['row_maps'][r]}
        for x, d in enumerate(row):
            src = truth[r][x]
            F.require((src is None) == (d == 0), 'transparencia DMA distinta de la fuente')
            if d:
                F.require(mapping[src][0] == d, 'índice DMA distinto de la fuente')
    env = simulate(uses, trans, colors)
    pix, states = pixel_errors(mario, rexpix, trans, colors)
    result['contadores']['errores_color'] = len(env) + pix
    # Armado VBL: PT completo (+recorte), POS/CTL, ATTACH en el canal impar.
    co, = struct.unpack_from('>I', tables, 24 + n * 32 + 16)
    clip = max(0, -r0)
    channels = []
    for c in range((pose['width'] + 15) // 16):
        offsets = struct.unpack_from('>II', tables, co + 8 * c)
        hx = x0 + 16 * c
        visible = r0 + pose['height'] > 0 and r0 < ROWS and -16 < hx < 256
        for half in range(2):
            ch = 4 + 2 * c + half
            if not visible:
                channels.append(dict(canal=ch, activo=False))
                continue
            vs = V0 + max(r0, 0)
            pos, ctl = control(hx, vs, V0 + r0 + pose['height'], ch)
            pt = offsets[half] + 4 + 4 * clip
            # El flujo desde PT reproduce las filas visibles de la pose.
            words = struct.unpack_from('>%dH' % (2 * (pose['height'] - clip)), dma, pt)
            for rr in range(pose['height'] - clip):
                for x in range(16):
                    v = ((words[2 * rr] >> (15 - x)) & 1) | ((words[2 * rr + 1] >> (15 - x)) & 1) << 1
                    want = pose['rows'][clip + rr][16 * c + x] if 16 * c + x < pose['width'] else 0
                    F.require(v == (want >> (2 * half)) & 3, 'flujo DMA distinto en PT')
            channels.append(dict(canal=ch, activo=True, pt=pt, pos=pos, ctl=ctl,
                                 attach=bool(ctl & 0x80)))
    # Capa 1: el sufijo solo escribe COLOR17-31 y respeta el plazo medido.
    for s, plan in plans.items():
        if s >= 0 and lines[s]:
            nxt = segs[s + 1]
            if plan['tipo'] != 'ffdf' and plan['pos'][-1] > END[nxt['nb']]:
                result['contadores']['errores_capa1'] += 1
    # Prioridad: Mario (canales 0-3) siempre delante del Rex (4-7).
    snes = R.mario_pixels(ram, recorded, ctx['gfx'])
    rex_entries = []
    for entry in recorded:
        x, y, t, attr, hi = entry
        if [signed(x - chosen['sx']), signed(y - chosen['sy']), t | (attr & 1) << 8,
                16 if hi & 2 else 8, attr >> 6 & 1, attr >> 7, attr >> 1 & 7] in chosen['tiles']:
            rex_entries.append(entry)
    start = next(k for k in range(len(recorded)) if recorded[k:k + len(rex_entries)] == rex_entries)
    for (x, y), (_, order) in snes.items():
        if (x, y + 1) in rexpix and start < order:
            for j, (dx, dy, tile, size, fx, fy, pal) in enumerate(chosen['tiles']):
                lx, ly = x - chosen['sx'] - dx, y - chosen['sy'] - dy
                if 0 <= lx < size and 0 <= ly < size and G.ref_pixel(ctx['vram'], tile, size, fx, fy, lx, ly):
                    result['contadores']['prioridad_distinta'] += start + j < order
                    break
    result['rex_fuera_pantalla'] = not rexpix
    result.update(variante=n, canales=channels, recorte=clip,
                  transiciones=len(trans), vbl=len(lines.get(-1, [])),
                  vbl_moves=[(m['indice'], m['valor']) for m in lines.get(-1, [])],
                  sufijos={s: dict(tipo=p['tipo'], h=p.get('h'), k=len(lines[s]), nop=p['nop'], pos=p['pos'],
                                   nb_sig=segs[s + 1]['nb'], ultima_carga=segs[s]['last'],
                                   moves=[(m['indice'], m['valor']) for m in lines[s]])
                           for s, p in plans.items() if s >= 0 and lines[s]})
    ev.update(rex=rexpix, states=states, uses=uses)
    return result, ev


TIPO = {'wait': 1, 'cadena': 2}


def dump_plans(plans):
    """Volcado binario B1 (instrucciones-g2t-bc.md §3): big endian, por frame.

    frame u32, variante u16 ($FFFF sin plan), 4 x (activo u8, pad u8, pt u32,
    pos u16, ctl u16) para SPR4-7, nvbl u8 + (índice u8, valor u16), nseg u8
    + por segmento (fila u8, tipo u8 1=WAIT 2=cadena, h u8, nop u8, k u8,
    k x (índice u8, valor u16)). Segmentos por fila; MOVE en orden del plan.
    """
    out = bytearray()
    for p in plans:
        out += struct.pack('>IH', p['frame'], 0xffff if p['variante'] is None else p['variante'])
        chans = {c['canal']: c for c in p.get('canales', [])}
        for ch in range(4, 8):
            c = chans.get(ch)
            if c and c.get('activo'):
                out += struct.pack('>BBIHH', 1, 0, c['pt'], c['pos'], c['ctl'])
            else:
                out += struct.pack('>BBIHH', 0, 0, 0, 0, 0)
        vbl = p.get('vbl_moves', [])
        out += struct.pack('>B', len(vbl))
        for i, v in vbl:
            out += struct.pack('>BH', i, v)
        segs = sorted(p.get('sufijos', {}).items(), key=lambda kv: int(kv[0]))
        out += struct.pack('>B', len(segs))
        for row, x in segs:
            out += struct.pack('>BBBBB', int(row), TIPO[x['tipo']], x.get('h') or 0, x['nop'], x['k'])
            for i, v in x['moves']:
                out += struct.pack('>BH', i, v)
    return bytes(out)


def read_dump(data):
    """Inverso de dump_plans: lista de dicts con los mismos campos."""
    plans, o = [], 0
    names = {v: k for k, v in TIPO.items()}
    while o < len(data):
        frame, var = struct.unpack_from('>IH', data, o)
        o += 6
        canales = []
        for ch in range(4, 8):
            act, _, pt, pos, ctl = struct.unpack_from('>BBIHH', data, o)
            o += 10
            canales.append(dict(canal=ch, activo=bool(act), pt=pt, pos=pos, ctl=ctl))
        n = data[o]
        o += 1
        vbl = [struct.unpack_from('>BH', data, o + 3 * j) for j in range(n)]
        o += 3 * n
        nseg = data[o]
        o += 1
        sufijos = {}
        for _ in range(nseg):
            row, tipo, h, nop, k = struct.unpack_from('>BBBBB', data, o)
            o += 5
            moves = [struct.unpack_from('>BH', data, o + 3 * j) for j in range(k)]
            o += 3 * k
            sufijos[row] = dict(tipo=names[tipo], h=h or None, nop=nop, k=k, moves=[list(m) for m in moves])
        plans.append(dict(frame=frame, variante=None if var == 0xffff else var, canales=canales,
                          vbl_moves=[list(m) for m in vbl], sufijos=sufijos))
    return plans


def evidence_png(samples, path):
    """Recorte x4 alrededor de Mario y Rex: fuente SNES / simulación / fallos."""
    from PIL import Image, ImageDraw
    Z, W, H = 4, 96, 64
    cols = 3
    rows = (len(samples) + cols - 1) // cols
    cw, ch = 3 * W * Z + 16, H * Z + 30
    sheet = Image.new('RGB', (cols * cw, rows * ch), (32, 32, 32))
    draw = ImageDraw.Draw(sheet)
    for k, (title, ev) in enumerate(samples):
        pts = list(ev['rex']) or list(ev['mario'])     # el Rex manda: bordes y recortes
        cx = sorted(p[0] for p in pts)[len(pts) // 2] if pts else 128
        cy = sorted(p[1] for p in pts)[len(pts) // 2] if pts else 112
        x0 = max(0, min(256 - W, cx - W // 2))
        y0 = max(0, min(ROWS - H, cy - H // 2))
        panes = [Image.new('RGB', (W, H), (60, 60, 60)) for _ in range(3)]
        for (x, rr), (d, color) in ev['rex'].items():
            if x0 <= x < x0 + W and y0 <= rr < y0 + H:
                got = ev['states'].get((x, rr), 0)
                panes[0].putpixel((x - x0, rr - y0), rgb(color))
        for (x, rr), i in ev['mario'].items():
            if x0 <= x < x0 + W and y0 <= rr < y0 + H:
                panes[0].putpixel((x - x0, rr - y0), rgb(ev['colors'][i]))
        for (x, rr), got in ev['states'].items():
            if x0 <= x < x0 + W and y0 <= rr < y0 + H:
                panes[1].putpixel((x - x0, rr - y0), rgb(got))
                want = rgb(ev['colors'][ev['mario'][x, rr]]) if (x, rr) in ev['mario'] else rgb(ev['rex'][x, rr][1])
                panes[2].putpixel((x - x0, rr - y0), (255, 0, 255) if rgb(got) != want else (90, 160, 90))
        bx, by = k % cols * cw, k // cols * ch
        draw.text((bx + 2, by + 2), '%s  [x%d,y%d]  SNES | simulacion | fallos (magenta)' % (title, x0, y0),
                  fill='white')
        for j, pane in enumerate(panes):
            sheet.paste(pane.resize((W * Z, H * Z), 0), (bx + j * (W * Z + 4), by + 26))
    sheet.save(path)


def load_context(bank):
    tables, dma = Path(bank + '.idx').read_bytes(), Path(bank + '.dma').read_bytes()
    poses, index = B.deserialize_bank(tables, dma)
    directory = {}
    for j in range(struct.unpack_from('>H', index, 6)[0]):
        _, _, _, count, ptr = struct.unpack_from('>IBBHI', index, 8 + 12 * j)
        variants = list(struct.unpack_from('>%dH' % count, index, ptr))
        directory[B.shape(poses[variants[0]])] = variants
    gfx = Path(G.WORK, 'cc', 'gfx32.bin').read_bytes()
    pals = Path(G.WORK, 'cc', 'mario_pal.bin').read_bytes()
    rom = Path(mkmario.ROM).read_bytes()
    head = len(rom) % 1024
    pointers = [struct.unpack_from('<H', rom, head + ((mkmario.DATA_00E2A2 + 2 * a) & 0x7fff))[0]
                for a in range(8)]
    vram, _, _ = G.build_vram(G._DEF_SRC, G.LEVEL)
    return dict(tables=tables, dma=dma, poses=poses, directory=directory, gfx=gfx, pals=pals,
                pointers=pointers, vram=vram, table=R.mask_table(gfx))


def run(args):
    F.derived_path(args.out)
    os.makedirs(args.out, exist_ok=True)
    ctx = load_context(args.bank)
    code, lst = P.assemble('player/scroll.s', ['VIS=256', 'SPRITES'])
    syms, local = P.listing(lst)
    F.require(syms['CL_LINES'] == 216 and syms['SEG'] == 220, 'layout de scroll distinto')
    V = {n: v for n, v in syms.items() if n.startswith('V_')}
    summary = dict(contrato='G2T-A fijado 2026-10-07', puerta_a_t=True, trazas={},
                   calibracion=dict(END=END, X_D0=X_D0, IDLE=IDLE, K255=K255, VBL_ARM=VBL_ARM),
                   banco=dict(dma=len(ctx['dma']), tablas=len(ctx['tables']),
                              sha256={s: hashlib.sha256(Path(args.bank + s).read_bytes()).hexdigest()
                                      for s in ('.idx', '.dma')}))
    samples, picks = [], args.picks
    for pair in args.trace:
        path, oracle = pair.split('=', 1)
        name = Path(path).stem.removeprefix('oam_')
        records = list(R.read_trace(path, oracle))
        a2 = R.validate_masks(records, ctx['gfx'], ctx['table'])
        groups = collections.defaultdict(list)
        for rec in records:
            groups[rec['frame']].append(rec)
        # Mario: todos los registros, con y sin Rex.
        mdiff, mstatus, mextra = 0, collections.Counter(), collections.Counter()
        for rec in records:
            _, d, st, ex = mario_check(rec['ram'], rec['recorded'], ctx['gfx'])
            mdiff += d
            mstatus[st] += 1
            mextra.update(ex)
        sc = P.Scroll(code, syms, local, Path('work/yi1_s.dat').read_bytes(), V)
        sc.init()
        totals, plans, bad = collections.Counter(), [], collections.defaultdict(list)
        stats = collections.Counter()
        for frame in sorted(groups):
            recs = groups[frame]
            ram = recs[0]['ram']
            sc.mem.w16(sc.vars + V['V_S'], ram[0x1a] | ram[0x1b] << 8)
            sc.call('scroll_frame')
            if args.frames and frame not in args.frames:
                continue
            if not any(r['num'] == 0xab for r in recs):
                continue
            base = sc.mem.r32(P.FAKE + 0x80)
            segs = segments(sc.mem, base, syms['CL_LINES'], syms['SEG'])
            plan, ev = plan_frame(recs, ctx, segs)
            plan['cam_y'] = ram[0x1c] | ram[0x1d] << 8
            if plan.get('sufijos') is not None:
                c1, pd, longest = check_list(sc.mem, base, syms['CL_LINES'], syms['SEG'], plan['sufijos'])
                plan['contadores']['errores_capa1'] += c1
                plan['contadores']['errores_color'] += pd
                stats['max_segmento'] = max(stats['max_segmento'], longest)
            plans.append(plan)
            totals.update(plan['contadores'])
            stats['frames'] += 1
            stats['cam_y_no192'] += plan['cam_y'] != 192
            stats['variante_distinta_a3'] += plan['variante'] != plan['variante_a3']
            stats['recorte'] += bool(plan.get('recorte'))
            stats['rex_fuera_pantalla'] += bool(plan.get('rex_fuera_pantalla'))
            for s, p in plan.get('sufijos', {}).items():
                stats['sufijo_' + p['tipo']] += 1
                stats['max_k'] = max(stats['max_k'], p['k'])
                stats['cruce255'] += s == WRAP_SEG
            stats['max_vbl'] = max(stats['max_vbl'], plan.get('vbl', 0))
            for c, v in plan['contadores'].items():
                if v and c != 'sin_destino':
                    bad[c].append(frame)
            for key, test in picks:
                if key not in [s[2] for s in samples] and test(name, frame, plan, ev):
                    samples.append(('%s f%d v%s %s' % (name, frame, plan['variante'], key), ev, key))
        res = dict(registros=len(records), frames_con_rex=stats['frames'],
                   diferencias_a2=a2['diferencias_a2'], mario_diferencias=mdiff,
                   mario_estado=dict(mstatus), mario_bordes=dict(mextra),
                   contadores=dict(totals), estadisticas=dict(stats),
                   frames_fallo={k: v[:200] for k, v in bad.items()})
        summary['trazas'][name] = res
        ok = (a2['diferencias_a2'] == 0 and mdiff == 0 and stats['frames'] > 0 and
              not any(totals[c] for c in ('sin_variante_temporal', 'sin_plazo', 'errores_color',
                                          'errores_capa1', 'prioridad_distinta')))
        summary['puerta_a_t'] &= ok
        Path(args.out, 'plan_' + name + '.json').write_text(json.dumps(plans, separators=(',', ':')),
                                                           encoding='utf-8')
        if args.dump:
            blob = dump_plans(plans)
            back = read_dump(blob)
            F.require(len(back) == len(plans) and all(
                b['frame'] == q['frame'] and b['variante'] == q['variante'] and
                {int(k): v['moves'] for k, v in b['sufijos'].items()} ==
                {int(k): [list(m) for m in v['moves']] for k, v in q.get('sufijos', {}).items()}
                for b, q in zip(back, plans)), 'volcado B1 no reproduce el plan')
            Path(args.out, 'plan_' + name + '.bin').write_bytes(blob)
        print('%s: frames=%d A2=%d mario_dif=%d %s %s' % (name, stats['frames'], a2['diferencias_a2'],
              mdiff, json.dumps(dict(totals), sort_keys=True), json.dumps(dict(stats), sort_keys=True)),
              flush=True)
        for c, frames in bad.items():
            print('  %s: %d frames, primeros %s' % (c, len(frames), frames[:12]))
    if samples:
        evidence_png([(t, ev) for t, ev, _ in samples], os.path.join(args.out, 'muestras.png'))
        summary['muestras'] = [t for t, _, _ in samples]
    Path(args.out, 'resumen.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('PUERTA A-T: ' + ('OK' if summary['puerta_a_t'] else 'FALLA'))
    return 0 if summary['puerta_a_t'] else 1


def default_picks():
    """Muestras para las imágenes: una por criterio y traza (las tres trazas)."""
    def visible(e):
        return bool(e['rex'])

    def edge(e):
        xs = [x for x, _ in e['rex']]
        return xs and (min(xs) == 0 or max(xs) == 255)
    picks = []
    for trace in ('yi1', 'normal', 'spin_kill'):
        picks += [
            ('%s compartido' % trace, lambda n, f, p, e, t=trace: n == t and visible(e) and
             any('M' in u['owners'] and 'R' in u['owners'] for row in e['uses'].values() for u in row.values())),
            ('%s izquierda' % trace, lambda n, f, p, e, t=trace: n == t and visible(e) and
             e['chosen']['tiles'][0][4] == 1 and p['transiciones'] >= 6),
            ('%s derecha' % trace, lambda n, f, p, e, t=trace: n == t and visible(e) and
             e['chosen']['tiles'][0][4] == 0 and p['transiciones'] >= 6),
            ('%s borde' % trace, lambda n, f, p, e, t=trace: n == t and visible(e) and edge(e)),
            ('%s solape' % trace, lambda n, f, p, e, t=trace: n == t and visible(e) and
             any(k in e['mario'] for k in e['rex'])),
            ('%s max sufijo' % trace, lambda n, f, p, e, t=trace: n == t and visible(e) and
             max([x['k'] for x in p.get('sufijos', {}).values()] or [0]) >= 6),
        ]
    picks.append(('f6150', lambda n, f, p, e: n == 'yi1' and f == 6150))
    return picks


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--trace', action='append', required=True, help='SOT1=oracle_oam.bin')
    ap.add_argument('--bank', default='work/g3/bank')
    ap.add_argument('--out', default='work/g2t_ref')
    ap.add_argument('--frames', type=lambda s: {int(x) for x in s.split(',')}, default=None)
    ap.add_argument('--dump', action='store_true', help='escribe plan_<traza>.bin (formato B1)')
    args = ap.parse_args()
    args.picks = default_picks()
    return run(args)


if __name__ == '__main__':
    sys.exit(main())
