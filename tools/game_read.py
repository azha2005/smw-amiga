#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
game_read.py - decodifica la tabla de player/game.s -DBENCH de una captura.

game.s (-DREPLAY -DBENCH) mide cada parte del frame del juego con el timer A
de CIA-B y, al acabar el replay (o -DSTOPF), pinta 19 palabras largas como
bits: celdas blancas/negras de 8 px, 32 por fila; la fila i ocupa las lineas
8+12*i .. +7 y empieza en x = 32.

  f0  $A55A5AA5 (sincronia)
  f1  ticks por frame << 16 | coste de un sello (ticks)
  f2  frames medidos << 16 | frames de resincronizacion (no cuentan)
  f3  media del total << 16 | frames que pasaron de un frame
  f4+2p  max << 16 | frame (0 = el primero del replay)      p = 0..6
  f5+2p  s (posicion del scroll) << 16
  f18 $5AA5A55A (sincronia)

O5 (render desacoplado, el modo por defecto de game.s): ademas las palabras
bajas de f5, f7 ... f17 (que antes valian 0) y dos filas mas, f19 y f20:

  f5.lo  frames logicos (la logica, una vez por frame)
  f7.lo  imagenes publicadas por el render
  f9.lo  fotos perdidas (frames logicos cuya imagen no se vio nunca)
  f11.lo la racha mas larga de fotos perdidas seguidas
  f13.lo, f15.lo, f17.lo  rachas de 1, de 2, de 3 o mas
  f19    VBL sin imagen nueva << 16 | peor interrupcion de la logica (ticks)
  f20    frame del final de la racha mas larga << 16 | frames sin COPER

Con el bucle de antes (-DNODECOUPLE) f5.lo = 0 y no se imprime nada de O5.

    python tools/game_read.py --shot work/bench/bench.png --auto

Sale con 1 si las palabras de sincronia no aparecen.
"""

import argparse
import os
import sys

from PIL import Image

E_CLOCK = 709379.0          # Hz del CIA en una Amiga PAL
CPU_PER_TICK = 10           # 7,09 MHz / 709379 Hz
REPLAY_FIRST = 5145         # frame del oraculo del primer frame del replay (P75)
NROWS = 19
NROWS_O5 = 21               # + f19, f20 (O5)
SHOT_X, SHOT_Y, SCALE = 67, 70, 2

PARTS = [
    "entrada (game_step sin level_frame)",
    "level_frame",
    "mspr_draw",
    "columna (columns)",
    "build_mid",
    "resto de scroll_frame",
    "total (hasta blitter libre)",
]


def read_longs(path, ox, oy, sx, sy, nrows=NROWS):
    im = Image.open(path).convert("L")
    px = im.load()
    out = []
    for i in range(nrows):
        y = int(round(oy + (8 + 12 * i + 4) * sy))
        v = 0
        for k in range(32):
            x = int(round(ox + (32 + k * 8 + 4) * sx))
            v = (v << 1) | (1 if px[x, y] > 128 else 0)
        out.append(v)
    return out


def autodetect(path):
    """(ox, oy, sx, sy): las bandas blancas son las filas; la fila 0 es la
    sincronia $A55A5AA5 (primera celda y ultima celda a 1)."""
    im = Image.open(path).convert("L")
    w, h = im.size
    px = im.load()
    # (sin el marco de la ventana de WinUAE: barra de titulo y de estado)
    top, bot = int(h * 0.07), int(h * 0.93)
    rows_set = set(y for y in range(top, bot) if any(px[x, y] > 128 for x in range(12, w - 12, 2)))
    bands, start = [], None
    for y in range(top, bot + 1):
        if y in rows_set and start is None:
            start = y
        elif y not in rows_set and start is not None:
            bands.append((start, y - 1))
            start = None
    if len(bands) < NROWS:
        raise SystemExit("autodetect: %d bandas blancas, esperaba %d" % (len(bands), NROWS))
    bands = bands[:NROWS]
    c0 = (bands[0][0] + bands[0][1]) / 2.0
    c18 = (bands[NROWS - 1][0] + bands[NROWS - 1][1]) / 2.0
    sy = (c18 - c0) / (12.0 * (NROWS - 1))
    oy = c0 - 12 * sy
    yc = int(round(c0))
    runs, x = [], 0
    while x < w:
        if px[x, yc] > 128:
            x0 = x
            while x < w and px[x, yc] > 128:
                x += 1
            runs.append((x0, x - 1))
        x += 1
    # celda 0 empieza en x = 32 y la celda 31 acaba en x = 32 + 256
    sx = (runs[-1][1] + 1 - runs[0][0]) / 256.0
    ox = runs[0][0] - 32 * sx
    return ox, oy, sx, sy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shot", default="work/shot.png")
    ap.add_argument("--x", type=int, default=SHOT_X)
    ap.add_argument("--y", type=int, default=SHOT_Y)
    ap.add_argument("--auto", action="store_true", help="detectar escala y origen")
    a = ap.parse_args()

    if a.auto:
        ox, oy, sx, sy = autodetect(a.shot)
    else:
        ox, oy, sx, sy = a.x, a.y, SCALE, SCALE
    f = read_longs(a.shot, ox, oy, sx, sy, NROWS_O5)
    if f[0] != 0xA55A5AA5 or f[18] != 0x5AA5A55A:
        print("FALLO: sincronia %08X / %08X (esperaba A55A5AA5 / 5AA5A55A)" % (f[0], f[18]))
        print("       la captura no es la pantalla de resultados de game.s -DBENCH")
        return 1

    tpf, ovh = f[1] >> 16, f[1] & 0xFFFF
    nfr, nrs = f[2] >> 16, f[2] & 0xFFFF
    mean, over = f[3] >> 16, f[3] & 0xFFFF
    exp = E_CLOCK / 50.0
    print("sincronia        : OK")
    print("ticks por frame  : %d  (esperado %.0f para 50 Hz PAL: %+.2f%%)"
          % (tpf, exp, 100.0 * (tpf - exp) / exp))
    print("coste de un sello: %d ticks (ya restado de cada intervalo)" % ovh)
    print("frames medidos   : %d en el bucle (%d de resincronizacion: sin entrada ni total)"
          % (nfr, nrs))
    print("total medio      : %d ticks = %.1f%% del frame; %d frames pasaron de un frame"
          % (mean, 100.0 * mean / tpf, over))
    print()
    print("%-38s %7s %8s %7s %7s %7s %6s" % ("parte (peor frame)", "ticks", "ciclos",
                                            "% frame", "frame", "oraculo", "s"))
    for p, name in enumerate(PARTS):
        mx, fr, s = f[4 + 2 * p] >> 16, f[4 + 2 * p] & 0xFFFF, f[5 + 2 * p] >> 16
        print("%-38s %7d %8d %6.1f%% %7d %7d %6d"
              % (name, mx, mx * CPU_PER_TICK, 100.0 * mx / tpf, fr, REPLAY_FIRST + fr, s))
    print()
    print("(frame = del replay, 0 = el primero; oraculo = %d + frame; s = Bg1HOfs)" % REPLAY_FIRST)
    print("(el peor de cada parte es de frames distintos: no se suman)")
    o5_report(f, tpf)
    return 0


def o5_report(f, tpf):
    """las palabras de O5 (render desacoplado); nada si f5.lo = 0"""
    lo = lambda i: f[i] & 0xFFFF
    nlog = lo(5)
    if not nlog:
        return
    npub, nlost, mx = lo(7), lo(9), lo(11)
    h1, h2, h3 = lo(13), lo(15), lo(17)
    rep, isr = f[19] >> 16, f[19] & 0xFFFF
    mxf, late = f[20] >> 16, f[20] & 0xFFFF
    print()
    print("O5, render desacoplado (la logica una vez por frame; la imagen salta si el render no llega):")
    print("  frames logicos          : %d" % nlog)
    print("  imagenes publicadas     : %d" % npub)
    print("  fotos perdidas          : %d (%.2f %% de los frames logicos)" % (nlost, 100.0 * nlost / nlog))
    print("  racha mas larga         : %d%s" % (mx, "  (termina en el frame %d, oraculo %d)"
                                                % (mxf, REPLAY_FIRST + mxf) if mx else ""))
    print("  rachas de 1 / 2 / >=3   : %d / %d / %d" % (h1, h2, h3))
    print("  VBL sin imagen nueva    : %d" % rep)
    print("  peor interrupcion       : %d ticks = %.1f %% del frame (logica + foto)" % (isr, 100.0 * isr / tpf))
    print("  frames sin COPER        : %d (la logica corrio en la VERTB)" % late)


if __name__ == "__main__":
    sys.exit(main())
