# P1-B (ARQ-0): bandas de 5 planos. En las filas de pantalla fuera de
# [B1, B2) el copper pone BPLCON0 a 5 planos y el plano 6 no se lee: la capa 2
# (PF2) queda con 2 planos, 3 colores (COLOR09-11) + transparente (COLOR00 =
# el cielo). La ventana vertical es fija, asi que cada fila de pantalla es
# siempre la misma fila de la capa 2: la reduccion se hace aca, una vez, en
# los datos (l2idx a 0..3 y l2pal), y la imagen con 6 o con 5 planos es la
# misma. scroll.s solo cambia BPLCON0 y adelanta BPL6PT B1 filas.
#
# Los 3 colores de cada fila: los que minimizan los pixeles visibles (capa 1
# transparente encima, paralaje s/2, todas las posiciones de la camara) con
# dE >= 2 contra hoy. Las entradas 4..7 de la paleta copian la fila vecina
# del lado de las de 6 planos (no se leen: sin MOVE de copper en el borde), y
# las 1..3 conservan su lugar si el color ya estaba ahi.
#   python tools/p1b.py            -> resumen (filas, colores, error)
import sys, os, itertools, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import render_d as R
import arq_diff as A

# 6 planos en [B1, B2); scroll.s P1B_B1/P1B_B2. Con 208 el borrado de esa
# fila llevaba 10 MOVE (7 + 2 de PF2 + BPLCON0); con 209, 9 como mucho, lo
# mismo que hoy (P43: con 7-9 termina antes de x = 0).
B1, B2 = 17, 209
Y0, LINES, SW, L2W = 192, 224, 256, 512


def rgb(c):
    return ((c >> 8 & 15) * 17, (c >> 4 & 15) * 17, (c & 15) * 17)


def rows5():
    """(fila, vecina): la banda de arriba va de abajo hacia arriba y copia la
    fila siguiente (la fila 0 escribe las 7 igual; asi la B1 no cambia mas
    colores que hoy), la de abajo copia la anterior"""
    return ([(r, r + 1) for r in range(B1 - 1, -1, -1)]
            + [(r, r - 1) for r in range(B2, LINES)])


def apply(d, step=4):
    """reduce d['l2idx'] y d['l2pal'] en las filas de 5 planos; devuelve el
    informe por fila: (fila, colores visibles, error px por foto)"""
    idx = R.l1_index(d)
    ss = list(range(0, d['W'] - SW, step))
    rep = []
    for r, nb in rows5():
        y = Y0 + r
        pal = [int(v) for v in d['l2pal'][y]]
        vis = collections.Counter()
        for s in ss:
            x0 = (s // 2) % L2W
            m = idx[y, s:s + SW] == 0
            i2 = d['l2idx'][y, (x0 + np.arange(SW)) % L2W].astype(int)
            vis.update(int(v) for v in i2[m & (i2 > 0)])
        # candidatos: los colores de la fila (sin repetir), y el error de cada terna
        cols = sorted(set(pal[v - 1] for v in vis))
        best = None
        for t in itertools.combinations(cols, min(3, len(cols))):
            e = sum(n for v, n in vis.items()
                    if min(A.de(rgb(pal[v - 1]), rgb(q)) for q in t + (d['sky'],)) >= 2)
            if best is None or e < best[0]:
                best = (e, t)
        e, t = best if best else (0, ())
        prev = [int(v) for v in d['l2pal'][Y0 + nb]]
        new = list(prev)                # 4..7 (y lo no usado) = la vecina
        free = [k for k in range(3) if prev[k] not in t]
        for c in t:
            if c not in new[:3]:
                new[free.pop(0)] = c
        # cada indice viejo va al color mas cercano: 0 (cielo) o una de 1..3
        cand = [(0, d['sky'])] + [(k + 1, new[k]) for k in range(3) if new[k] in t]
        lut = np.zeros(8, np.uint8)
        for v in range(1, 8):
            lut[v] = min(cand, key=lambda kc: A.de(rgb(pal[v - 1]), rgb(kc[1])))[0]
        d['l2idx'][y] = lut[d['l2idx'][y]]
        d['l2pal'][y] = new
        rep.append((r, len(cols), e / len(ss)))
    rep.sort()
    return rep


if __name__ == '__main__':
    d = R.load(os.path.join('work', 'yi1_d.dat'))
    rep = apply(d)
    for r, n, e in rep:
        print('fila %3d: %d colores visibles, area dE>=2 %.2f px/foto' % (r, n, e))
    print('P1-B %d filas de 5 planos (%.1f %% de P1), area %.1f px/foto'
          % (len(rep), 100.0 * len(rep) / LINES, sum(e for _, _, e in rep)))
