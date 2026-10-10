#!/usr/bin/env python3
"""q_levers.py - G5L-R-Q: los recortes posibles por bucle, sobre el perfil.

Entrada: el histograma por PC de `g5l.py game --pcprof` (por foto), el
listado, work/t2/frames.csv (t2_attrib.py) y la salida de vbtrace.py.
Cada reescritura es (rutina.bucle, fracción de sus ciclos que se ahorra,
nota); se aplica foto por foto sobre el histograma y el ahorro se resta del
coste de la foto en el modelo de cola (t2_model.py, cinco ajustes). Las
fracciones son ESTIMADAS (ciclos del 68000 de la reescritura contra los
medidos), no reescrituras probadas. `--generic` suma un recorte uniforme
del resto (ajuste a mano sin bucle concreto).

    python tools/q_levers.py --prof work/t2/q_prof.json --lst work/t2/replay/game.lst \
        --csv work/t2/frames.csv --frames work/t2/frames.json --vblog work/t2/vt/vbtrace.out
"""
import argparse
import collections
import csv
import json

from q_report import parse_lst, windows
from t2_keys import FITS
from t2_model import simulate

# (rutina.bucle, fracción ahorrada, por qué)
RENDER = [
    ('g5l_pcget.c', .75, 'clave con VLIST/MSH/R0 primero: falla en la 1a .l, no en la ~6a (38 c/.l)'),
    ('g5l_patch.cl', .35, 'copia con movem.l de 8 .l: ~19,5 c/.l contra 30 (move.l+dbf)'),
    ('g5l_emit.mv', .45, 'MOVE empaquetados de 4 B y bucle desenrollado: ~21 c contra 38'),
    ('g5l_emit.jl', .90, 'el salto $0084 en un offset conocido (GV_NB), sin buscarlo'),
    ('g5l_place.f1', .60, 'mapa de bits de segmentos con lugar, 32 filas por .l, contra 20 c por fila'),
    ('g5l_pckey.k', .35, 'copia de la clave con movem'),
    ('g5l_pcput.bc', .35, 'copia de las cubetas con movem'),
    ('g5l_pcget.bc', .35, 'idem al acertar'),
    ('g5l_pcget.r', .35, 'idem'),
    ('g5l_mario.kz', .60, 'borrar 52 B con movem de registros a cero'),
]
BUILD = [
    ('bm_left.mv', .25, 'sin probar: sacar del bucle por carga el max a / min b (.k1/.k2)'),
    ('bm_left.k1', .60, 'idem'),
    ('bm_left.k2', .30, 'idem: solo queda el fin de la línea'),
]


def saving(hist, lst, table, generic):
    rules = {name: f for name, f, _ in table}
    s = tot = 0
    for off, (n, c) in hist.items():
        g, l, _, _ = lst.get(int(off, 16), ('?', '', '', ''))
        f = rules.get(g + l)
        tot += c
        s += c * f if f is not None else c * generic
    return int(s), tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prof', required=True)
    ap.add_argument('--lst', required=True)
    ap.add_argument('--csv', required=True)
    ap.add_argument('--frames', required=True)
    ap.add_argument('--vblog', required=True)
    a = ap.parse_args()
    q = json.load(open(a.prof))
    lst = parse_lst(a.lst)
    rows = [{c: int(v) for c, v in r.items()} for r in csv.DictReader(open(a.csv))]
    fr = json.load(open(a.frames))
    win = windows(a.vblog)
    miss = {x['k'] for x in fr[1:] if x['parts'].get('g5l_sweep', 0) > 0}
    drawn = {x['k'] for x in fr[1:] if 'g5l_place' in x['parts']}
    med = sorted(r['build_mid'] for r in rows[1:])[len(rows) // 2]

    print('reescrituras (fracción ESTIMADA de los ciclos del bucle):')
    for name, f, why in RENDER + BUILD:
        print('  %-16s %3d %%  %s' % (name, f * 100, why))

    def cut(part, table, generic):
        return {int(k): saving(h, lst, table, generic) for k, h in q[part].items()}

    for generic in (0, .05, .10):
        sr = cut('render', RENDER, generic)
        sb = cut('build_mid', BUILD, generic)
        print('\n== resto con -%d %% (ajuste general)' % (generic * 100))
        for title, ks, sv in (('g5l_render, ventanas de salto', win, sr), ('g5l_render, fallos', miss, sr),
                              ('g5l_render, dibujadas sin fallo', drawn - miss, sr),
                              ('build_mid, ventanas de salto', win, sb)):
            s = sum(sv[k][0] for k in ks if k in sv)
            t = sum(sv[k][1] for k in ks if k in sv)
            print('  %-34s ahorro %9d de %10d ciclos: %4.1f %%' % (title, s, t, 100 * s / max(1, t)))

        def run(name, fn):
            print('  %-50s %s' % (name, ' '.join('%2d' % len(simulate([fn(r) for r in rows], B, S)) for B, S in FITS)))
        sR = lambda r: sr.get(r['k'], (0, 0))[0]
        sB = lambda r: sb.get(r['k'], (0, 0))[0]
        s5 = lambda r, bm: int(.5 * max(0, r['build_mid'] - bm - med))
        print('  saltos del modelo (B/S: %s)' % ' '.join('%dk/%dk' % (b // 1000, s // 1000) for b, s in FITS))
        run('base', lambda r: r['total'])
        run('recortes de g5l_render', lambda r: r['total'] - sR(r))
        run('recortes de g5l_render y de build_mid', lambda r: r['total'] - sR(r) - sB(r))
        run('... + S5 (-50 % del exceso que queda)', lambda r: r['total'] - sR(r) - sB(r) - s5(r, sB(r)))


if __name__ == '__main__':
    main()
