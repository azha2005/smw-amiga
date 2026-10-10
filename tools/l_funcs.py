#!/usr/bin/env python3
"""l_funcs.py - G5L-R-L: la lógica por función, del histograma por PC.

Entrada: el json de `g5l.py game --pcprof OUT --pclogic RANGOS` (la lógica,
dc_cop, paso a paso en esas fotos), el listado de vasm y work/.../frames.json
(la lógica por foto de la corrida normal; "picos" = mediana + 8000). Una
función es la última etiqueta global con ':' (asm) o la etiqueta sin ':'
que sigue a un `cnop` (las de vbcc, también las static: `mcoll_lN`).

    python tools/l_funcs.py work/l/prof.json work/s9/replay/game.lst work/s9/frames.json [top]
"""
import json, re, collections, sys

LINE = re.compile(r'^(?:([0-9A-F]{2}):([0-9A-F]{8}) [0-9A-F]*)?\s*\t\s*(\d+)(M|R|:) ?(.*)$')
GLAB = re.compile(r'^([A-Za-z_]\w*):')
BARE = re.compile(r'^([A-Za-z_]\w*)\s*$')


def funcs(lst):
    """{offset: 'fichero:funcion'}: etiqueta global con ':' (asm) o la
    etiqueta sin ':' que sigue a un cnop (funciones de vbcc)."""
    out = {}
    cur, src, prev_cnop = '?', '', False
    for raw in open(lst, encoding='latin-1'):
        raw = raw.rstrip('\r\n')
        if raw.startswith('Source: '):
            src = raw[9:-1].replace(chr(92), '/').split('/')[-1]
            continue
        m = LINE.match(raw)
        if not m:
            continue
        text = m.group(5)
        if m.group(4) == ':' and not text.startswith(('\t', ' ')):
            g = GLAB.match(text)
            b = BARE.match(text)
            if g:
                cur = src + ':' + g.group(1)
            elif b and prev_cnop:
                cur = src + ':' + b.group(1)
        prev_cnop = text.strip().startswith('cnop')
        if m.group(2):
            out.setdefault(int(m.group(2), 16), cur)
    return out


def main():
    q = json.load(open(sys.argv[1]))
    fn = funcs(sys.argv[2])
    fr = {x['k']: x for x in json.load(open(sys.argv[3]))}
    top = int(sys.argv[4]) if len(sys.argv) > 4 else 30
    ks = [int(k) for k in q['logic']]
    med = sorted(x['logic'] for x in fr.values())[len(fr) // 2]
    spk = [k for k in ks if fr[k]['logic'] > med + 8000]
    c, cs = collections.Counter(), collections.Counter()
    for k in ks:
        for off, (n, cy) in q['logic'][str(k)].items():
            f = fn.get(int(off, 16), '?')
            c[f] += cy
            if k in spk:
                cs[f] += cy
    tot = sum(c.values())
    print('fotos %d, %d por foto; picos %d' % (len(ks), tot // len(ks), len(spk)))
    for f, v in c.most_common(top):
        print('  %-40s %6d/foto %5.1f%%   picos %6d' % (f, v // len(ks), 100 * v / tot, cs[f] // max(1, len(spk))))


if __name__ == '__main__':
    main()
