#!/usr/bin/env python3
"""q_report.py - G5L-R-Q: el histograma por PC, por línea, bucle y rutina.

Entrada: el json de `g5l.py game --pcprof` ({render|build_mid: {k: {offset:
[veces, ciclos]}}, tot}), work/t2/frames.json (fallos, s), la salida de
vbtrace.py (ventanas de salto) y el listado de vasm. Un "bucle" es la
etiqueta local (.x) dentro de su rutina global. Ciclos de Musashi, sin DMA.

    python tools/q_report.py --prof work/t2/q_prof.json --frames work/t2/frames.json \
        --vblog work/t2/vt/vbtrace.out --lst work/t2/replay/game.lst [--top 25]
"""
import argparse
import collections
import json
import re

ADDR = re.compile(r'^([0-9A-F]{2}):([0-9A-F]{8}) [0-9A-F]*\s*\t\s*(\d+)(M|R|:) ?(.*)$')
NOADDR = re.compile(r'^\s*\t\s*(\d+)(M|R|:) ?(.*)$')
GLOB = re.compile(r'^([A-Za-z_]\w*):')
LOC = re.compile(r'^(\.\w+):')


def parse_lst(path):
    """{offset: (rutina, bucle, línea, texto)}"""
    out = {}
    g, l, src, line = '?', '', '', 0
    for raw in open(path, encoding='latin-1'):
        raw = raw.rstrip('\r\n')
        if raw.startswith('Source: '):
            src = raw[9:-1]
            continue
        m = ADDR.match(raw)
        if m:
            off, ln, sep, text = int(m.group(2), 16), m.group(3), m.group(4), m.group(5)
        else:
            m = NOADDR.match(raw)
            if not m:
                continue
            off, ln, sep, text = None, m.group(1), m.group(2), m.group(3)
        if sep == ':':                          # 'nM'/'nR' = línea n de una macro o un rept
            line = int(ln)
        t = text.strip()
        mg, ml = GLOB.match(text), LOC.match(t)
        if sep == ':' and mg and not text.startswith((' ', '\t')):
            g, l = mg.group(1), ''
        elif ml:
            l = ml.group(1)
        if off is not None and off not in out:
            out[off] = (g, l, '%s:%d' % (src.replace(chr(92), '/').split('/')[-1], line), t.split(';')[0].strip())
    return out


def windows(vblog):
    text = open(vblog, encoding='utf-8', errors='replace').read()
    rep = [int(x) for x in re.search(r'repiten.*?\[(.*?)\]', text).group(1).split(',') if int(x)]
    sk = [int(x) for x in re.search(r'salteadas: \d+ \[(.*?)\]', text).group(1).split(',')]
    ks = set()
    for s in sk:
        r0 = max([r for r in rep if r <= s] or [s])
        ks.update(range(r0 - 2, s + 1))
    return ks


def agg(hists, ks, lst):
    line, loop, rout = collections.Counter(), collections.Counter(), collections.Counter()
    nline = collections.Counter()
    tot = 0
    for k in ks:
        for off, (n, c) in hists.get(str(k), {}).items():
            g, l, where, text = lst.get(int(off, 16), ('?', '', '?', '?'))
            line[where, g, l, text] += c
            nline[where, g, l, text] += n
            loop[g + l] += c
            rout[g] += c
            tot += c
    return tot, line, nline, loop, rout


def show(title, hists, ks, lst, top):
    tot, line, nline, loop, rout = agg(hists, ks, lst)
    n = len([k for k in ks if str(k) in hists])
    print('\n== %s: %d fotos, %d ciclos (%d por foto)' % (title, n, tot, tot // max(1, n)))
    print('-- rutinas')
    for g, c in rout.most_common(top):
        print('  %-24s %10d %5.1f %%' % (g, c, 100 * c / tot))
    print('-- bucles (rutina.etiqueta)')
    for g, c in loop.most_common(top):
        print('  %-32s %10d %5.1f %%' % (g, c, 100 * c / tot))
    print('-- líneas')
    for key, c in line.most_common(top):
        where, g, l, text = key
        print('  %-16s %-26s %-34s %8d veces %9d %5.1f %%' % (where, g + l, text[:34], nline[key], c, 100 * c / tot))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prof', required=True)
    ap.add_argument('--frames', required=True)
    ap.add_argument('--vblog', required=True)
    ap.add_argument('--lst', required=True)
    ap.add_argument('--top', type=int, default=25)
    a = ap.parse_args()
    q = json.load(open(a.prof))
    fr = json.load(open(a.frames))
    lst = parse_lst(a.lst)
    win = windows(a.vblog)
    miss = {x['k'] for x in fr[1:] if x['parts'].get('g5l_sweep', 0) > 0}
    drawn = {x['k'] for x in fr[1:] if 'g5l_place' in x['parts']}
    ds = {x['k']: (x['sc'] - fr[i - 1]['sc']) if i > 1 else 0 for i, x in enumerate(fr)}
    big = {int(k) for k, t in q['tot'].items() if t[1] > 40000}
    show('g5l_render en las ventanas de salto', q['render'], win, lst, a.top)
    show('g5l_render en los 145 fallos', q['render'], miss, lst, a.top)
    show('g5l_render en las dibujadas sin fallo', q['render'], drawn - miss, lst, a.top)
    show('build_mid > 40000, cámara a la izquierda', q['build_mid'], {k for k in big if ds[k] < 0}, lst, a.top)
    show('build_mid > 40000, a la derecha o quieta', q['build_mid'], {k for k in big if ds[k] >= 0}, lst, a.top)
    show('build_mid en las ventanas de salto', q['build_mid'], win, lst, a.top)


if __name__ == '__main__':
    main()
