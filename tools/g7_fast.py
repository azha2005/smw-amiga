#!/usr/bin/env python3
"""G7-3b: especificacion del productor sin busqueda (rediseno 2026-10-11).

Por fila con efectos, en este orden y sin backtracking:
  1. existente: un indice PF1 que ya tiene el color en todo su tramo;
  2. libre: un indice que el terreno visible no usa en la fila; se
     cambia su MOVE del prefijo y sus recargas de la fila pasan a NOP
     (misma ranura: el resto del copper no cambia de posicion);
  3. ventana: un indice que el terreno no usa cerca del efecto; carga
     antes y restauracion despues, colocadas por plazo (EDF);
  4. lo que quede se informa: apoyo de hardware o rechazo explicito.
Cada plan se comprueba por pixel contra la composicion esperada. Es la
referencia del 68000 (g7bobs.s); no lee tablas por numero de frame.
"""
import argparse
import collections
import json
from pathlib import Path

import numpy as np
import g2t_ref as T
import g5l as L
import g7_color_plan as P

NOP = (0x1FE, 0)
GAP = 16                         # px entre grupos de un mismo color
WHY = collections.Counter()      # causas de fallo del paso 3 (diagnostico)


def required(words, row, idx, overlay):
    """Color esperado por x (-1: transparente) con la lista original."""
    base = P.palette(words, row)
    out = np.where(idx > 0, base[idx, np.arange(256)], -1)
    return np.where(overlay >= 0, overlay, out)


def check(words, new, row, idx, out_idx, overlay):
    want = required(words, row, idx, overlay)
    pal = P.palette(new, row)
    got = np.where(out_idx > 0, pal[out_idx, np.arange(256)], -1)
    live = want >= 0
    return bool(np.all(got[live] == want[live]))


def clusters(xs, gap=GAP):
    """Grupos de pixeles de un color separados por mas de `gap` px."""
    cut = np.flatnonzero(np.diff(xs) > gap) + 1
    return np.split(xs, cut)


def fast_row(words, row, idx, overlay):
    """Pasos 1-2. Devuelve (words, out_idx, sin_resolver, indices de efectos)."""
    occ = overlay >= 0
    base = P.palette(words, row)
    terrain = (~occ) & (idx > 0)
    used = 0
    for r in range(1, 8):
        if np.any(terrain & (idx == r)):
            used |= 1 << r
    out_idx = idx.copy()
    reserved = used
    claimed = 0                     # indices de los que depende un efecto
    pending = collections.OrderedDict()
    for c in sorted(set(int(v) for v in overlay[occ])):
        for xs in clusters(np.flatnonzero(overlay == c)):
            hit = 0
            # Primero un indice del terreno (no reserva nada nuevo).
            for r in [r for r in range(1, 8) if used >> r & 1] +                      [r for r in range(1, 8) if not used >> r & 1]:
                if np.all(base[r, xs] == c):
                    hit = r
                    break
            if hit:
                out_idx[xs] = hit
                reserved |= 1 << hit
                claimed |= 1 << hit
            else:
                pending.setdefault(c, []).append(xs)
    new = list(words)
    prefix, nb = P.prefix_of(words, row)
    left = []
    for c, parts in pending.items():
        free = [r for r in range(1, 8) if not reserved >> r & 1]
        if not free:
            left += [(c, xs) for xs in parts]
            continue
        r = free[0]
        reserved |= 1 << r
        claimed |= 1 << r
        reg = 0x180 + 2*r
        for i, (a, b) in enumerate(new):
            if a != reg:
                continue
            if i < len(prefix):
                new[i] = (a, (b & 0xF000) | c)
            else:
                new[i] = NOP
        for xs in parts:
            out_idx[xs] = r
    return new, out_idx, left, claimed


def positions(words, row):
    """x de cada palabra del cuerpo (None: prefijo o WAIT), modelo timeline."""
    v = row + L.V0
    nb, t, stage, out = 0, None, 0, []
    for o, (w1, w2) in enumerate(words):
        if stage == 0 and w1 & 1 and (w1 >> 8 == (v-1) & 255 or w1 == 0xFFDF):
            out.append(None)
            continue
        if stage == 0 and w1 == 0x1FE and o < 2:
            out.append(None)
            continue
        if stage == 0 and not w1 & 1 and w1 != 0x1FE:
            nb += 1
            out.append(None)
            continue
        if stage == 0:
            stage, t = 1, L.T0 + max(0, 16*(nb-9))
        if w1 & 1:
            t = max(T.advance(t, 2), T.xh(w1 & 0xFE) if (w1 & 0xFE) <= 0xCE else T.X_D0)
            out.append(None)
        else:
            out.append(t)
            t = T.advance(t)
    return out, (t if stage else L.T0 + max(0, 16*(nb-9))), stage


def waits(words, row):
    """Holgura de cada WAIT del cuerpo (x resuelto - ranura previa).

    Misma maquina de estados que positions(); el WAIT que abre el cuerpo
    sale del borrado y queda fuera (G2T-A lo mide aparte)."""
    v = row + L.V0
    nb, t, stage, out = 0, None, 0, {}
    for o, (w1, w2) in enumerate(words):
        if stage == 0 and w1 & 1 and (w1 >> 8 == (v-1) & 255 or w1 == 0xFFDF):
            continue
        if stage == 0 and w1 == 0x1FE and o < 2:
            continue
        if stage == 0 and not w1 & 1 and w1 != 0x1FE:
            nb += 1
            continue
        if stage == 0:
            stage, t = 1, L.T0 + max(0, 16*(nb-9))
            opening = True
        if w1 & 1:
            q = max(T.advance(t, 2), T.xh(w1 & 0xFE) if (w1 & 0xFE) <= 0xCE else T.X_D0)
            if not opening:
                out[o] = q - t
            t = q
        else:
            t = T.advance(t)
        opening = False
    return out


def place_brute(new, tags, row, reg, value, lo, hi, end, spare):
    """Un MOVE reg,value en x de [lo, hi] sin mover ningun evento original.

    1) reusar una ranura sobrante (NOP o recarga de un indice sin uso);
    2) insertar [MOVE], [NOP.., MOVE] o [WAIT, MOVE] en un hueco del
       cuerpo. Se acepta solo si todos los eventos originales conservan
       su x, todo cae antes de `end`, cada WAIT conserva holgura >= IDLE
       (o la original si era menor) y la lista cabe."""
    hi = min(hi, end)
    if lo > hi:
        return None
    pos, _, _ = positions(new, row)
    for i, x in enumerate(pos):
        if x is not None and lo <= x <= hi and (new[i] == NOP or new[i][0] in spare):
            out = list(new)
            out[i] = (reg, value)
            return out, list(tags)
    ref = {tg: x for tg, x in zip(tags, pos) if tg is not None and x is not None}
    slack = waits(new, row)
    ref_slack = {tags[o]: d for o, d in slack.items()}
    body0 = next((i for i, x in enumerate(pos) if x is not None), None)
    first = min([i for i, (w1, _) in enumerate(new) if i >= 2 and (w1 & 1 or w1 == 0x1FE)] +
                [i for i, x in enumerate(pos) if x is not None] + [len(new)])
    for gap in range(first, len(new)+1):
        chunks = []
        if gap > first:
            for n in range(0, 12):
                chunks.append([NOP]*n + [(reg, value)])
        for h in range(0x20, 0xCF, 2):
            chunks.append([(((row+L.V0) & 255) << 8 | h | 1, 0xFFFE), (reg, value)])
        for chunk in chunks:
            trial = new[:gap] + chunk + new[gap:]
            # El MOVE insertado recibe su propia marca: una insercion
            # posterior tampoco puede moverlo.
            mark = ('ins', len(tags), reg, value)
            ttags = tags[:gap] + [None]*(len(chunk)-1) + [mark] + tags[gap:]
            if len(trial) + 3 > 64:
                continue
            tp, _, _ = positions(trial, row)
            x = tp[gap+len(chunk)-1]
            if x is None or not lo <= x <= hi:
                continue
            if any(p is not None and p > end for p in tp):
                continue
            if any(tg is not None and tg != mark and p is not None and ref.get(tg) != p
                   for tg, p in zip(ttags, tp)):
                continue
            ok = True
            for o, d in waits(trial, row).items():
                need = L.IDLE if ttags[o] is None else min(L.IDLE, ref_slack.get(ttags[o], L.IDLE))
                if d < need:
                    ok = False
                    break
            if ok:
                return trial, ttags
    return None


# WAIT por h ascendente sin repetir x consecutivas: el orden en que la
# referencia prueba los WAIT (xh no es monotona: $C2 cae en 255, $C4 en 243).
HX = []
for _h in range(0x20, 0xCF, 2):
    if not HX or HX[-1][1] != L.xh(_h):
        HX.append((_h, L.xh(_h)))


def body_info(words, row):
    """Por palabra: x (MOVE del cuerpo), ranura previa y si es WAIT."""
    v = row + L.V0
    nb, t, stage = 0, None, 0
    pos, before, wait, opening = [], [], [], None
    for o, (w1, w2) in enumerate(words):
        pre = (stage == 0 and ((w1 & 1 and (w1 >> 8 == (v-1) & 255 or w1 == 0xFFDF)) or
                               (w1 == 0x1FE and o < 2) or (not w1 & 1 and w1 != 0x1FE)))
        if pre:
            if not w1 & 1 and w1 != 0x1FE:
                nb += 1
            pos.append(None); before.append(None); wait.append(False)
            continue
        if stage == 0:
            stage, t = 1, L.T0 + max(0, 16*(nb-9))
            opening = o
        before.append(t)
        if w1 & 1:
            t = max(T.advance(t, 2), T.xh(w1 & 0xFE) if (w1 & 0xFE) <= 0xCE else T.X_D0)
            pos.append(None); wait.append(True)
        else:
            pos.append(t); wait.append(False)
            t = T.advance(t)
    if stage == 0:
        t = L.T0 + max(0, 16*(nb-9))
    return pos, before, wait, opening, t


def place(new, tags, row, reg, value, lo, hi, end, spare):
    """Forma cerrada de place_brute (mismo resultado, sin probar listas).

    Un MOVE insertado delante de otro MOVE lo desplaza: solo hay huecos
    delante de un WAIT del cuerpo o al final. Delante de un WAIT, el
    WAIT tiene que seguir resolviendo en la misma x y con holgura."""
    hi = min(hi, end)
    if lo > hi:
        return None
    pos, before, wait, opening, t_end = body_info(new, row)
    for i, x in enumerate(pos):
        if x is not None and lo <= x <= hi and (new[i] == NOP or new[i][0] in spare):
            out = list(new)
            out[i] = (reg, value)
            return out, list(tags)
    if any(x is not None and x > end for x in pos):
        return None
    slack = waits(new, row)
    first = min([i for i, (w1, _) in enumerate(new) if i >= 2 and (w1 & 1 or w1 == 0x1FE)] +
                [i for i, x in enumerate(pos) if x is not None] + [len(new)])
    for gap in range(first, len(new)+1):
        if gap < len(new) and not wait[gap]:
            continue                            # desplazaria un MOVE
        t = t_end if gap == len(new) else before[gap]
        is_open = gap == first
        if gap < len(new):
            w1 = new[gap][0]
            qw = max(T.advance(t, 2), T.xh(w1 & 0xFE) if (w1 & 0xFE) <= 0xCE else T.X_D0)
            xw = T.xh(w1 & 0xFE) if (w1 & 0xFE) <= 0xCE else T.X_D0
            # Holgura exigida al WAIT original tras la insercion.
            need = L.IDLE if gap == opening else min(L.IDLE, slack.get(gap, L.IDLE))

        def fits(x, extra):
            if not lo <= x <= hi or len(new) + extra + 3 > 64:
                return False
            if gap == len(new):
                return True
            t2 = T.advance(x)
            q2 = max(T.advance(t2, 2), xw)
            return q2 == qw and q2 - t2 >= need

        if not is_open:
            q, n = t, 0
            while n < 12:
                if q >= lo:
                    if fits(q, n+1):
                        mark = ('ins', len(tags), reg, value)
                        return (new[:gap] + [NOP]*n + [(reg, value)] + new[gap:],
                                tags[:gap] + [None]*n + [mark] + tags[gap:])
                    break
                q, n = L.adv(q), n+1
        for h, xh in HX:
            x = max(L.adv(t, 2), xh)
            if x < lo or (not is_open and x - t < L.IDLE):
                continue
            if fits(x, 2):
                mark = ('ins', len(tags), reg, value)
                return (new[:gap] + [(((row+L.V0) & 255) << 8 | h | 1, 0xFFFE), (reg, value)] + new[gap:],
                        tags[:gap] + [None, mark] + tags[gap:])
    return None


def place_checked(*a):
    got, ref = place(*a), place_brute(*a)
    assert got == ref, ('place distinta', a[1:], got, ref)
    return got


PLACE = place


def window_row(words, row, idx, overlay, out_idx, left, claimed, next_nb):
    """Paso 3: prestar indices del terreno por ventana, sin backtracking.

    Para cada color sin indice: el primer indice del terreno sin uso en
    el tramo del efecto. Carga entre su ultimo uso a la izquierda y el
    efecto (o en el prefijo), restauracion entre el efecto y su proximo
    uso. Sus recargas dentro de esa ventana pasan a NOP."""
    occ = overlay >= 0
    base = P.palette(words, row)
    terrain = (~occ) & (idx > 0)
    end = L.end_of(next_nb)
    if end is None or row == L.WRAP_SEG:
        WHY['fila sin modelo'] += 1
        return None
    new = list(words)
    tags = list(range(len(words)))
    shown = claimed
    for r in range(1, 8):
        if np.any(terrain & (idx == r)):
            shown |= 1 << r
    spare = {0x180+2*r for r in range(1, 8) if not shown >> r & 1}
    state = dict(new=new, tags=tags, claimed=claimed)

    def borrow(c, xs):
        """Prestar el mejor indice para el tramo xs; True si quedo puesto."""
        new, tags, claimed = state['new'], state['tags'], state['claimed']
        x0, x1 = int(xs[0]), int(xs[-1])
        cand = []
        for r in range(1, 8):
            use = np.flatnonzero(terrain & (idx == r))
            if claimed >> r & 1 or not use.size or np.any((use >= x0) & (use <= x1)):
                continue
            lo = int(use[use < x0].max()) + 1 if np.any(use < x0) else None
            hi = int(use[use > x1].min()) if np.any(use > x1) else None
            # La ventana mas ancha deja mas ranuras: primero esa.
            cand.append((-((x0 if lo is None else x0-lo) + (256 if hi is None else hi-x1)), r, lo, hi))
        if not cand:
            state['why'] = 'sin indice con ventana limpia'
        for _, r, lo, hi in sorted(cand):
            state['why'] = 'sin ranura de copper'
            reg = 0x180 + 2*r
            pos, _, _ = positions(new, row)
            trial, ttags = list(new), list(tags)
            for i, x in enumerate(pos):
                if x is not None and trial[i][0] == reg and                         (lo is None or x >= lo) and (hi is None or x < hi):
                    trial[i] = NOP
            if lo is None:
                j = [k for k, (a, _) in enumerate(trial) if a == reg and pos[k] is None]
                if not j:
                    continue
                trial[j[0]] = (reg, (trial[j[0]][1] & 0xF000) | c)
            else:
                got = PLACE(trial, ttags, row, reg, c, lo, x0, end, spare)
                if got is None:
                    continue
                trial, ttags = got
            if hi is not None:
                got = PLACE(trial, ttags, row, reg, int(base[r, hi]), x1+1, hi, end, spare)
                if got is None:
                    continue
                trial, ttags = got
            state.update(new=trial, tags=ttags, claimed=claimed | 1 << r)
            out_idx[xs] = r
            return True
        return False

    groups = collections.OrderedDict()
    for c, xs in sorted(left, key=lambda t: t[1][0]):
        groups.setdefault(c, []).append(xs)
    for c, parts in groups.items():
        # Todo el color con un indice; si no, cada grupo por separado.
        if borrow(c, np.concatenate(parts)):
            continue
        for xs in parts:
            if not borrow(c, xs):
                WHY[state.get('why', '?')] += 1
                return None
    return state['new'], out_idx


def reach_exact(t, x, first, row):
    """Palabras para que el proximo MOVE caiga exactamente en x desde la
    ranura t (G2T-A: encadenado con NOP o WAIT con holgura >= IDLE; desde
    el borrado solo WAIT)."""
    if not first:
        q, n = t, 0
        while q < x and n < 12:
            q, n = L.adv(q), n+1
        if q == x:
            return [NOP]*n
    for h in range(0x20, 0xCF, 2):
        q = max(L.adv(t, 2), L.xh(h))
        if q == x and q - t >= L.IDLE:
            return [(((row+L.V0) & 255) << 8 | h | 1, 0xFFFE)]
    return None


def reach_early(t, a, b, first, row):
    """La ranura mas temprana en [a, b] alcanzable desde t: (x, palabras)."""
    best = None
    if not first:
        q, n = t, 0
        while q < a and n < 12:
            q, n = L.adv(q), n+1
        if a <= q <= b:
            best = (q, [NOP]*n)
    for h in range(0x20, 0xCF, 2):
        q = max(L.adv(t, 2), L.xh(h))
        if a <= q <= b and q - t >= L.IDLE:
            if best is None or q < best[0]:
                best = (q, [(((row+L.V0) & 255) << 8 | h | 1, 0xFFFE)])
            break
    return best


def edf_row(words, row, idx, overlay, out_idx, next_nb):
    """Paso 3b: reconstruir el cuerpo por plazo, una sola pasada.

    Requisitos por indice desde out_idx (terreno con su color original,
    efectos con el suyo). Cada cambio de color es un trabajo [a, b]; los
    MOVE que no son de PF1 conservan su x exacta. EDF: en cada paso el
    trabajo liberado de plazo mas cercano, en la ranura mas temprana,
    siempre que el proximo evento fijo siga alcanzable."""
    end = L.end_of(next_nb)
    if end is None or row == L.WRAP_SEG:
        return None
    want = required(words, row, idx, overlay)
    prefix, nb = P.prefix_of(words, row)
    head = list(prefix)
    jobs = []
    for r in range(1, 8):
        xs = np.flatnonzero((out_idx == r) & (want >= 0))
        if not xs.size:
            continue
        vals = want[xs]
        for i, (reg, val) in enumerate(head):
            if reg == 0x180+2*r:
                head[i] = (reg, (val & 0xF000) | int(vals[0]))
        for i in np.flatnonzero(vals[1:] != vals[:-1]) + 1:
            jobs.append([int(xs[i-1])+1, int(xs[i]), 0x180+2*r, int(vals[i])])
    fixed = [(x, reg, val) for x, reg, val in T.timeline(words, row)
             if x >= 0 and not 0x182 <= reg <= 0x18E and reg != 0x1FE]
    t = L.T0 + max(0, 16*(nb-9))
    first = True
    body = []
    fi = 0
    while jobs or fi < len(fixed):
        nxt = fixed[fi] if fi < len(fixed) else None
        cand = sorted((j for j in jobs), key=lambda j: (j[1], j[0]))
        placed = False
        for j in cand:
            if nxt is not None and j[0] > nxt[0]:
                continue
            got = reach_early(t, j[0], min(j[1], end), first, row)
            if got is None:
                if j is cand[0]:
                    return None                 # el plazo mas cercano no entra
                continue
            x, pre = got
            if nxt is not None and (x >= nxt[0] or
                                    reach_exact(L.adv(x), nxt[0], False, row) is None):
                if j[1] < nxt[0]:
                    return None
                continue
            body += pre + [(j[2], j[3])]
            t, first = L.adv(x), False
            jobs.remove(j)
            placed = True
            break
        if placed:
            continue
        if nxt is None:
            return None
        if any(j[1] < nxt[0] for j in jobs):
            return None
        pre = reach_exact(t, nxt[0], first, row)
        if pre is None:
            return None
        body += pre + [(nxt[1], nxt[2])]
        t, first = L.adv(nxt[0]), False
        fi += 1
    if any(x > end for x, _, _ in T.timeline(head+body, row) if x >= 0):
        return None
    new = head + body
    if len(new) + 3 > 64:
        return None
    return new


def edf_assign(words, row, idx, overlay, out_idx, left, claimed, next_nb):
    """Elegir indice para cada color pendiente (ventana limpia, la mas
    ancha primero) y reconstruir por EDF. Sin backtracking: cada color
    prueba a lo sumo siete indices."""
    occ = overlay >= 0
    terrain = (~occ) & (idx > 0)
    out = out_idx.copy()
    groups = collections.OrderedDict()
    for c, xs in sorted(left, key=lambda t: t[1][0]):
        groups.setdefault(c, []).append(xs)
    new = None

    def assign(xs):
        nonlocal out, new, claimed
        x0, x1 = int(xs[0]), int(xs[-1])
        cand = []
        for r in range(1, 8):
            use = np.flatnonzero(terrain & (out == r))
            if claimed >> r & 1 or np.any((use >= x0) & (use <= x1)):
                continue
            lo = int(use[use < x0].max()) if np.any(use < x0) else -1
            hi = int(use[use > x1].min()) if np.any(use > x1) else 256
            cand.append((-(hi-lo), r))
        for _, r in sorted(cand):
            trial = out.copy()
            trial[xs] = r
            got = edf_row(words, row, idx, overlay, trial, next_nb)
            if got is not None:
                out, new = trial, got
                claimed |= 1 << r
                return True
        return False

    for c, parts in groups.items():
        # Todo el color con un indice; si no, cada grupo con el suyo.
        if assign(np.concatenate(parts)):
            continue
        if len(parts) > 1 and all(assign(xs) for xs in parts):
            continue
        WHY['edf sin plan'] += 1
        return None
    return new, out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin', required=True)
    ap.add_argument('--lst', required=True)
    ap.add_argument('--sources', default='work/g7/sources.bin')
    ap.add_argument('--from-k', type=int, default=0)
    ap.add_argument('--to-k', type=int, default=99999)
    ap.add_argument('--no-hidden', action='store_true',
                    help='no quitar los pixeles tapados por hardware (lo que hace el 68000)')
    ap.add_argument('--check-place', action='store_true',
                    help='comparar place() con la version por fuerza bruta')
    ap.add_argument('--out', default='work/g7fast/report.json')
    a = ap.parse_args()
    global PLACE
    if a.check_place:
        PLACE = place_checked
    bank = Path(a.sources).read_bytes()
    g = L.GameRun(a.bin, a.lst, 'work/g3/bank')
    s, mem, cpu = g.s, g.mem, g.cpu
    gfx = cpu.read(g.addr('gfx32'), 23808)
    tab = L.Table(cpu.read(g.addr('g5l_table'), g.addr('g5l_cdma_src')-g.addr('g5l_table')))
    size = len(Path('work/yi1_s_g5.dat').read_bytes())
    st = collections.Counter()
    left_rows = []
    for k in range(min(g.n, a.to_k+1)):
        if k:
            g.fr.call(g.addr('dc_cop'), g.G.FAKE)
        rec, back = P.render_step(g)
        if k >= a.from_k and mem.r8(rec+s['R_SWS_VALID']):
            oam = cpu.read(rec+s['R_OAM'], 320)
            ov = P.overlays(oam, bank)
            hid = P.hardware_hidden(g, rec, tab, gfx)
            if not a.no_hidden:
                ov[hid] = -1
            data = cpu.read(g.G.DATA, size)
            cam = mem.r16(rec+s['R_S'])
            bad = False
            for row in np.flatnonzero(np.any(ov >= 0, axis=1)):
                row = int(row)
                words, _ = T.segment_words(mem, back, s['CL_LINES'], s['SEG'], row)
                idx = P.terrain(data, cam, row)
                idx[hid[row]] = 0
                new, out_idx, left, reserved = fast_row(words, row, idx, ov[row])
                st['rows'] += 1
                mode = 'fast'
                if left:
                    nxt, _ = T.segment_words(mem, back, s['CL_LINES'], s['SEG'], (row+1) % 224)
                    _, nb = P.prefix_of(nxt, (row+1) % 224)
                    got = window_row(new, row, idx, ov[row], out_idx.copy(), left, reserved, nb)
                    if got:
                        new, out_idx = got
                        left = []
                        mode = 'window'
                    else:
                        got = edf_assign(words, row, idx, ov[row], out_idx, left, reserved, nb)
                        if got:
                            new, out_idx = got
                            left = []
                            mode = 'edf'
                if left:
                    st['rows_left'] += 1
                    bad = True
                    if len(left_rows) < 2000:
                        left_rows.append(dict(k=k, row=row, camera=cam,
                                              colors=[c for c, _ in left]))
                    continue
                if not check(words, new, row, idx, out_idx, ov[row]):
                    st['rows_wrong'] += 1
                    print('MAL', k, row, flush=True)
                    continue
                st['rows_'+mode] += 1
            st['photos'] += 1
            st['photos_left'] += bad
        P.finish_step(g, rec, back)
        if k and k % 1000 == 0:
            print(k, dict(st), flush=True)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(stats=dict(st), left=left_rows), indent=1), encoding='utf8')
    ok = not st['rows_wrong']
    print('paso 3, causas:', dict(WHY))
    print('G7 FAST: '+('OK ' if ok else 'FALLA ')+json.dumps(dict(st)), flush=True)
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
