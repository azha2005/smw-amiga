#!/usr/bin/env python3
"""pa_shift.py - G5L-R-Pa: ¿el plan de un fallo es el de otro corrido en Δr0?

Entrada: work/t2/frames.json de `g5l.py game` (por foto la clave GV_PK y el
plan de Python: vo, r0, groups, remaps, trans). Fallo = foto con
g5l_sweep. Para cada clave reducida (campos de GV_PK a cero) se simula la
FIFO de g5l_pcput (los fallos insertan) y, en cada acierto, se compara el
plan con el de la foto que dejó la entrada: vo, groups y remaps iguales y
trans igual con las filas corridas en Δ = r0_k − r0_j (desde = −1 se queda).

    python tools/pa_shift.py --frames work/t2/frames.json [--n 4 16 1000000]
"""
import argparse
import collections
import json

from t2_keys import F, red


def shifted(pj, pk):
    """None si el plan pk es pj corrido; si no, la primera diferencia"""
    if pj['vo'] != pk['vo']:
        return 'vo'
    if pj['groups'] != pk['groups']:
        return 'groups'
    if pj['remaps'] != pk['remaps']:
        return 'remaps'
    d = pk['r0'] - pj['r0']
    tj = [[i, c, a + d if a >= 0 else a, o, b + d] for i, c, a, o, b in pj['trans']]
    if tj != pk['trans']:
        return 'trans'
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--frames', required=True)
    ap.add_argument('--n', type=int, nargs='+', default=[4, 16, 10 ** 6])
    a = ap.parse_args()
    fr = json.load(open(a.frames))
    drawn = [x for x in fr[1:] if 'g5l_place' in x['parts'] and x['plan']]
    nmiss = sum(1 for x in drawn if x['parts'].get('g5l_sweep', 0) > 0)
    print('fallos con plan: %d' % nmiss)
    out = {}
    for drop in (('R0',), ('R0', 'MSH'), ('R0', 'MSH', 'ptrs')):
        for n in a.n:
            cache = []                          # [(clave, foto)]
            ok, bad, why, ex = 0, 0, collections.Counter(), []
            for x in drawn:
                key = red(x['pk'], drop)
                miss = x['parts'].get('g5l_sweep', 0) > 0
                hit = next((j for kk, j in cache if kk == key), None)
                if hit is not None:
                    if miss:
                        w = shifted(hit['plan'], x['plan'])
                        if w is None:
                            ok += 1
                        else:
                            bad += 1
                            why[w] += 1
                            if len(ex) < 3:
                                ex.append((hit['k'], x['k'], w, x['plan']['r0'] - hit['plan']['r0']))
                    continue
                if miss:
                    cache.append((key, x))
                    if len(cache) > n:
                        cache.pop(0)
            tot = ok + bad
            out['+'.join(drop), n] = (ok, bad)
            print('sin %-12s N=%-7d aciertos %3d: iguales corridos %3d (%s), distintos %3d %s %s' % (
                '+'.join(drop), n, tot, ok, '%d %%' % (100 * ok // tot) if tot else '-', bad,
                dict(why), ' '.join('k%d<-k%d:%s d%+d' % (b, a_, w, d) for a_, b, w, d in ex)))
    # también fuera de los fallos: cada par de fotos con plan y la misma clave sin R0
    pairs = collections.Counter()
    last = {}
    for x in drawn:
        key = red(x['pk'], ('R0',))
        if key in last:
            pairs['igual' if shifted(last[key]['plan'], x['plan']) is None else 'distinto'] += 1
        last[key] = x
    print('todas las fotos con plan, misma clave sin R0 que una anterior:', dict(pairs))


if __name__ == '__main__':
    main()
