#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sprshot_cmp.py - G9: la imagen de los sprites de una captura de WinUAE
contra la OAM que grabó el oráculo de la SNES en el mismo frame.

    python tools/sprshot_cmp.py --shot work/g4b/pcand1705/shot.png \\
        --frames work/g4b/frames_stress_piranha_1.json --k 1705 --trace stress_piranha
    python tools/sprshot_cmp.py --selftest

- El frame del oráculo de la foto k sale de game_frames.json de `g5l.py game`
  (campo f; P75: -DSTOPF cuenta fotos del replay, no frames del oráculo).
- Los objetos salen de work/oamb_<traza>.trace (G4-B, todos los tipos) y
  se dibujan con la VRAM/CGRAM del nivel (g4a.ctx, sprgfx_final.compose);
  Mario, de su OAM con las fichas dinámicas (g5ref.mario_pixels).
- Solo se comparan las zonas de sprite: cada píxel opaco de la SNES, en la
  fila del copper (y de la OAM + 1), contra el bloque 2x2 de la captura
  (SHOT_BOX/SHOT_DX de g5l.py, P57).
- Por objeto: 'exacto', 'no dibujado' (casi ningún píxel igual) o
  'distinto' (N px). Si el plan de g5l.py (game_frames.json, plan.rex)
  lo dibujó, se espera exacto; si no, que no esté.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

ROWS = 224
OUT = Path('work/g9')


def snes_objects(trace, frame, types):
    """los registros de la traza en ese frame (de los tipos pedidos) y la
    OAM/RAM del frame; None si la traza no tiene ese frame"""
    import g5ref as R
    recs = []
    for r in R.read_trace('work/oamb_%s.trace' % trace, 'work/oracle_%s_oam.bin' % trace):
        if r['frame'] > frame:
            break
        if r['frame'] == frame:
            recs.append(r)
    if not recs:
        return None
    return dict(objs=[r for r in recs if r['num'] in types], ram=recs[0]['ram'],
                recorded=recs[0]['recorded'], nums=sorted({r['num'] for r in recs}))


def expected(snes, ctx, vram, cg):
    """{(x, fila): (color12, dueño)} con dueño 'M' (Mario) o la ranura;
    Mario delante; entre objetos, el primero (como la OAM). Y los solapes."""
    import g5ref as R
    from palette import snes_to_amiga12
    from sprgfx_final import compose
    ram, recorded = snes['ram'], snes['recorded']
    pi = R.palette_index(ram, ctx['pointers'])
    colors = struct.unpack_from('>16H', ctx['pals'], 32 * pi)
    pix, solape = {}, 0
    for (x, y), (v, _) in R.mario_pixels(ram, recorded, ctx['gfx']).items():
        if y + 1 < ROWS:
            pix[x, y + 1] = (colors[v], 'M')
    for r in snes['objs']:
        ox, oy, truth = compose(vram, [list(t) for t in r['tiles']])
        for yy, row in enumerate(truth):
            for xx, val in enumerate(row):
                if val is None:
                    continue
                x, y = r['sx'] + ox + xx, r['sy'] + oy + yy + 1
                if not (0 <= x < 256 and 0 <= y < ROWS):
                    continue
                if (x, y) in pix:
                    solape += 1
                    continue
                pix[x, y] = (snes_to_amiga12(cg[128 + 16 * val[0] + val[1]]), r['slot'])
    return pix, solape


def sample(shot, x, y):
    """el bloque 2x2 de la captura (P57): None si los 4 no coinciden"""
    import g5l as L
    bx, by = 2 * (x + L.SHOT_DX), 2 * y
    q = {shot.getpixel((bx + i, by + j)) for i in range(2) for j in range(2)}
    return q.pop() if len(q) == 1 else None


def compare(shot, pix, snes, plan):
    import g5l as L
    owners = {}
    for (x, y), (c, who) in pix.items():
        o = owners.setdefault(who, dict(px=0, iguales=0, distintos=[]))
        o['px'] += 1
        if sample(shot, x, y) == L.rgb12(c):
            o['iguales'] += 1
        else:
            o['distintos'].append((x, y))
    out = []
    drawn = list(plan or [])
    for who, o in owners.items():
        if who == 'M':
            num, pos = None, None
        else:
            r = [r for r in snes['objs'] if r['slot'] == who][0]
            num = r['num']
            pos = min((x, y) for (x, y), (_, w) in pix.items() if w == who)
        n = o['px'] - o['iguales']
        if n == 0:
            verdict = 'exacto'
        elif o['iguales'] <= o['px'] // 10:
            verdict = 'no dibujado'
        else:
            verdict = 'distinto'
        planned = None
        if who != 'M':
            # el del plan: la misma ranura (game_frames.json desde G9; antes,
            # la familia de mapas, que coincide con el tipo salvo en las formas
            # del banco G3: $BD, $B9 y $02 son de la familia del Rex)
            for q in drawn:
                if q.get('slot', -1) == who or ('slot' not in q and q.get('tipo') == num):
                    planned = q
                    break
        out.append(dict(dueño='Mario' if who == 'M' else 'ranura %d' % who,
                        tipo=None if num is None else '%02X' % num, origen=pos,
                        px=o['px'], distintos=n, veredicto=verdict,
                        en_plan=None if who == 'M' else planned is not None,
                        muestra=o['distintos'][:8]))
    return sorted(out, key=lambda d: (d['dueño'] != 'Mario', d['dueño']))


def judge(rows):
    """la puerta: Mario y lo que el plan dibujó, exactos; lo demás, no dibujado"""
    bad = []
    for d in rows:
        want = 'exacto' if d['dueño'] == 'Mario' or d['en_plan'] else 'no dibujado'
        if d['veredicto'] != want:
            bad.append(d)
    return bad


def zoom(shot, pix, rows, path):
    """esperado | captura | diferencias, alrededor de lo distinto"""
    from PIL import Image
    import g5l as L
    bad = [p for d in rows for p in d['muestra']] or list(pix)[:1]
    xs, ys = [p[0] for p in bad], [p[1] for p in bad]
    x0, y0 = max(0, min(xs) - 24), max(0, min(ys) - 24)
    x1, y1 = min(256, max(xs) + 24), min(ROWS, max(ys) + 24)
    w, h = x1 - x0, y1 - y0
    sheet = Image.new('RGB', (3 * 4 * w, 4 * h), (40, 40, 40))
    for y in range(y0, y1):
        for x in range(x0, x1):
            got = shot.getpixel((2 * (x + L.SHOT_DX), 2 * y))
            exp = L.rgb12(pix[x, y][0]) if (x, y) in pix else got
            dif = (255, 0, 255) if (x, y) in pix and sample(shot, x, y) != exp else tuple(v // 3 for v in got)
            for k, col in enumerate((exp, got, dif)):
                for i in range(4):
                    for j in range(4):
                        sheet.putpixel((k * 4 * w + 4 * (x - x0) + i, 4 * (y - y0) + j), col)
    sheet.save(path)


def run(a):
    from PIL import Image
    import g2t_ref as T
    import g4a
    import g5l as L
    types = set(L.parse_types(a.types))
    fr = {x['k']: x for x in json.loads(Path(a.frames).read_text(encoding='utf-8'))}[a.k]
    snes = snes_objects(a.trace, fr['f'], types)
    if snes is None:
        raise SystemExit('la traza %s no tiene el frame %d (foto %d)' % (a.trace, fr['f'], a.k))
    ctx = T.load_context(a.bank)
    vram, cg = g4a.ctx()
    # lógica distinta (--logic): esos objetos se dibujan desde la OAM del
    # port, así la puerta de la imagen mide solo el dibujo; la diferencia de
    # lógica queda anotada aparte
    logica = {}
    lj = OUT / ('logica_%s.json' % a.trace)
    if lj.exists():
        for k, _, _, slot, why, q in json.loads(lj.read_text(encoding='utf-8'))['casos']:
            if k == a.k:
                logica[slot] = why
                r = [r for r in snes['objs'] if r['slot'] == slot][0]
                r.update(sx=0, sy=0, tiles=[[x - 512 if x >= 256 else x, y, tl, 16 if sz else 8,
                                             at >> 6 & 1, at >> 7, at >> 1 & 7] for x, y, tl, at, sz in q])
    pix, solape = expected(snes, ctx, vram, cg)
    shot = Image.open(a.shot).convert('RGB').crop(L.SHOT_BOX)
    rows = compare(shot, pix, snes, (fr.get('plan') or {}).get('rex'))
    for d in rows:
        if d['dueño'] != 'Mario' and int(d['dueño'].split()[1]) in logica:
            d['logica_distinta'] = logica[int(d['dueño'].split()[1])]
    bad = judge(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    name = '%s_%d' % (a.trace, a.k)
    zoom(shot, pix, [d for d in rows if d in bad] or rows, OUT / (name + '.png'))
    res = dict(foto=a.k, frame=fr['f'], traza=a.trace, objetos=rows, solape_entre_sprites=solape,
               tipos_en_frame=['%02X' % n for n in snes['nums']], fallos=len(bad))
    (OUT / (name + '.json')).write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding='utf-8')
    for d in rows:
        print('%-9s %-4s %-12s px %4d distintos %4d  %-11s %s%s' % (
            d['dueño'], d['tipo'] or '', d['origen'], d['px'], d['distintos'], d['veredicto'],
            '' if d['en_plan'] is None else ('(en el plan)' if d['en_plan'] else '(fuera del plan)'),
            ' [OAM del port; lógica: %s]' % d['logica_distinta'] if 'logica_distinta' in d else ''))
    print('G9 SPRSHOT: ' + ('OK' if not bad else 'FALLA (%d)' % len(bad)))
    return 0 if not bad else 1


def run_logic(a):
    """sin WinUAE: la foto que captura el port (g5l_capture, en Musashi como
    g5l.py shot) contra la traza del oráculo en su frame, por objeto: las
    entradas OAM absolutas (x, y, ficha, atributos, tamaño), que son lo que
    se dibuja. La x/y de la ranura no sirve: el port la toma después del
    movimiento del frame y la OAM se escribió antes. Si el port no coincide
    aquí, la imagen tampoco podrá."""
    import collections
    import g5l as L
    import g5ref as R
    gr = L.GameRun(a.bin, a.lst, a.bank)
    G, s, cpu, mem, fr, addr = gr.G, gr.s, gr.cpu, gr.mem, gr.fr, gr.addr
    types = set(L.parse_types(a.types))
    gfxlen = Path('work/cc/gfx32.bin').read_bytes()
    trace = R.read_trace('work/oamb_%s.trace' % a.trace, 'work/oracle_%s_oam.bin' % a.trace)
    pend = next(trace, None)
    st = collections.defaultdict(collections.Counter)
    ejemplos = collections.defaultdict(list)
    casos = []                                  # (foto, frame, tipo, ranura, motivo, OAM del port)
    desinc = []                                 # fotos con Mario distinto (no se cuentan)
    for k in range(gr.n):
        if k:
            fr.call(addr('dc_cop'), G.FAKE)
        photo = mem.r16(gr.dc + s['DC_NEW'])
        rec = addr('dc_rec') + photo * s['DC_REC']
        mem.w16(gr.dc + s['DC_REND'], photo)
        mem.w16(fr.vars + s['V_S'], mem.r16(rec + s['R_S']))
        for n in ('columns', 'apply_colors', 'set_pointers', 'build_mid'):
            fr.call(addr(n), G.FAKE)
        f = gr.first + mem.r16(rec + s['R_FRAME'])
        ph = L.read_photo(mem, rec, s)
        # la traza avanza con el frame (las fotos no retroceden)
        snes, allf = [], []
        while pend is not None and pend['frame'] <= f:
            if pend['frame'] == f:
                allf.append(pend)
                if pend['num'] in types:
                    snes.append(pend)
            pend = next(trace, None)
        if allf:                                # Mario: su OAM (como trace_photo)
            ram, recorded = allf[0]['ram'], allf[0]['recorded']
            dyn = R.dynamic_tiles(ram, len(gfxlen))
            mw = [(x, y, tl, at) for x, y, tl, at, hi in recorded
                  if not ((at >> 1) & 7 or at & 1 or tl not in dyn or y == 0xF0)][:4]
            mp = [tuple(ph['moam'][4 * i:4 * i + 4]) for i in range(4) if ph['moam'][4 * i + 1] != 0xF0]
            st['Mario']['snes'] += 1
            st['Mario']['igual' if sorted(mw) == sorted(mp) else 'distinto'] += 1
            if sorted(mw) != sorted(mp) and len(ejemplos['Mario']) < 6:
                ejemplos['Mario'].append(dict(k=k, f=f, snes=sorted(mw)[:2], port=sorted(mp)[:2]))
        # foto en sincronía: Mario igual a la SNES. Si no (SKIP/SYNC del
        # replay: el port repite la foto anterior), los objetos no se cuentan
        if not allf or sorted(mw) != sorted(mp):
            st['?']['fotos_desincronizadas'] += 1
            desinc.append(k)
            snes = []
        port = {}
        for slot, x, y, ents in ph['rex']:
            port[slot] = sorted((ex | (hi & 1) << 8, ey, tl | (at & 1) << 8, at & 0xCE, hi & 2)
                                for ex, ey, tl, at, hi in ents)
        for r in snes:
            t = '%02X' % r['num']
            st[t]['snes'] += 1
            q = port.pop(r['slot'], None)
            if q is None:
                st[t]['sin_captura'] += 1
                continue
            want = sorted((((r['sx'] + dx) & 0x1FF), (r['sy'] + dy) & 255, tl,
                           fx << 6 | fy << 7 | pal << 1, 2 if sz == 16 else 0)
                          for dx, dy, tl, sz, fx, fy, pal in r['tiles'])
            if q == want:
                st[t]['igual'] += 1
                continue
            if len(q) != len(want):
                why = 'fichas_%d_de_%d' % (len(q), len(want))   # G5L_MAXT
            else:
                d = {(a[0] - b[0], a[1] - b[1]) for a, b in zip(q, want)}
                same = all(a[2:] == b[2:] for a, b in zip(q, want))
                why = ('corrida_%+d_%+d' % d.pop()) if len(d) == 1 and same else 'otra_pose'
            st[t][why] += 1
            casos.append((k, f, t, r['slot'], why, q))
            if len(ejemplos[t]) < 6:
                ejemplos[t].append(dict(k=k, f=f, slot=r['slot'], motivo=why, snes=want[:3], port=q[:3]))
        for slot in port:
            st['?']['solo_port'] += 1
        cpu.cpu.w_reg(cpu.M.Register.A0, rec)
        fr.call(addr('g5l_render'), G.FAKE)
        back = mem.r32(fr.vars + s['V_BACK'])
        cpu.cpu.w_reg(cpu.M.Register.D7, photo)
        fr.call(addr('dc_hdr'), G.FAKE)
        if 'DC_PLIST' in s:
            mem.w32(gr.dc + s['DC_PLIST'], back)
        mem.w16(gr.dc + s['DC_FRONT'], photo)
        mem.w16(gr.dc + s['DC_REND'], 0xFFFF)
        other = gr.cops[(gr.cops.index(back) + 1) % len(gr.cops)]
        mem.w32(fr.vars + s['V_BACK'], other)
    res = dict(traza=a.trace, fotos=gr.n, tipos={t: dict(c) for t, c in sorted(st.items())},
               ejemplos=dict(ejemplos), casos=casos, desincronizadas=desinc)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ('logica_%s.json' % a.trace)).write_text(json.dumps(res, indent=2), encoding='utf-8')
    print(json.dumps(res['tipos'], sort_keys=True))
    for t, e in sorted(ejemplos.items()):
        print(t, e[:3])
    ok = all(c['igual'] == c['snes'] - c['sin_captura'] for t, c in st.items() if t != '?')
    for t, c in sorted(st.items()):
        if t != '?':
            print('%-6s %5d de %5d iguales (%.1f %%)' % (t, c['igual'], c['snes'], 100.0 * c['igual'] / max(1, c['snes'])))
    print('G9 LOGICA: ' + ('OK' if ok else 'DISTINTA'))
    return 0 if ok else 1


def selftest():
    """una captura sintética desde la propia referencia da 0; movida 1 px, no"""
    from PIL import Image
    import g5l as L
    pix = {(10 + i, 20 + j): (0xF80 if (i + j) & 1 else 0x0F0, 3) for i in range(16) for j in range(16)}
    pix.update({(100 + i, 50): (0xFFF, 'M') for i in range(8)})
    snes = dict(objs=[dict(slot=3, num=0x95)])
    plan = [dict(slot=3)]

    def shot_from(dx):
        im = Image.new('RGB', (640, 512), (0, 0, 0))
        for (x, y), (c, _) in pix.items():
            for i in range(2):
                for j in range(2):
                    im.putpixel((2 * (x + dx + L.SHOT_DX) + i, 2 * y + j), L.rgb12(c))
        return im
    ok = not judge(compare(shot_from(0), pix, snes, plan))
    bad = judge(compare(shot_from(1), pix, snes, plan))
    ok &= len(bad) == 2
    # dibujado sin estar en el plan: falla solo el objeto
    extra = judge(compare(shot_from(0), pix, snes, []))
    ok &= len(extra) == 1 and extra[0]['tipo'] == '95'
    print('selftest: ' + ('OK' if ok else 'FALLA'))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--shot')
    ap.add_argument('--frames', help='game_frames.json de g5l.py game (el mismo build)')
    ap.add_argument('--k', type=int, help='la foto (la de -DSTOPF)')
    ap.add_argument('--trace', help='work/oamb_<traza>.trace')
    ap.add_argument('--types', default='all', help="tipos de objeto a comparar (g5l.parse_types)")
    ap.add_argument('--bank', default='work/g3/bank')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--logic', action='store_true', help='sin captura: la foto del port contra la traza, todas las fotos')
    ap.add_argument('--bin')
    ap.add_argument('--lst')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.logic:
        return run_logic(a)
    return run(a)


if __name__ == '__main__':
    sys.exit(main())
