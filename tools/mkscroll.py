#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mkscroll.py - etapa 6 (primer prototipo): del blob de la etapa 5
(work/yi1_d.dat) a lo que lee player/scroll.s, ya en el orden de la Amiga.
Salida: work/yi1_s.dat (derivado del ROM: no se versiona, R9).

Ventana vertical fija: la camara de Yoshi's Island 1 no se mueve en
vertical en toda la partida grabada (Bg1VOfs = Bg2VOfs = 192): se ven las
lineas 192..415 del nivel.

Colores de la capa 1. En el borrado de cada linea, el registro r vale el
color del primer evento de r que todavia no termino a la izquierda de la
pantalla (render_d.camera_line). Eso cambia solo cuando cam_x pasa el
final de un evento: se guarda una lista de cambios ordenada por x (con el
color viejo, para deshacerlos cuando la camara vuelve), y la Amiga la
aplica a la lista del copper segun se mueve la camara. Las cargas a mitad
de linea (MLD) se planifican aca, en coordenadas del nivel (plan()): la
Amiga solo escribe, para cada linea, las que caen en pantalla (Etapa 6.2).

Formato (big-endian):
  +0   "SMWS"  u16 ancho del nivel  u16 columnas de bloques  u16 bloques
       u16 color del cielo (0x0RGB)  u16 nº de cambios
  +16  u32 x 10: BLK, MAP, INI, CHG, L2B, L2P, MLX, MLD, LNS, 0
  BLK  bloques de 96 bytes (16 filas x 3 planos x palabra)
  MAP  por columna de bloques (columnas x 14 filas visibles + 1): nº de
       bloque (byte). Las 224 lineas empiezan en la fila 12 (192 = 12*16)
  INI  224 lineas x 7 colores: la capa 1 con cam_x = 0
  CHG  cambios: u16 x, u16 desplazamiento del valor en la lista del copper
       por lineas (linea*SEG + 8 + (registro-1)*4 + 2: cada segmento de
       linea empieza con 2 WAIT + 7 MOVE de la capa 1),
       u16 color nuevo, u16 color viejo; ordenados por x; empieza con un
       centinela x = 0 (sin efecto) y termina en x = $FFFF
  L2B  capa 2, 224 lineas x 3 planos x 106 bytes (848 px: el periodo de
       512 mas 336, para que el puntero no tenga que dar la vuelta)
  L2P  224 lineas x 7 colores (registros 9..15)
  MLX  225 x u16: primera carga de cada linea en MLD
  MLD  cargas a mitad de linea de la capa 1, en coordenadas del nivel, 12
       bytes: u16 clase (0 = WAIT en x; 1 = MOVE detras de la anterior; 2,
       3 = 1 o 2 MOVE de relleno y el MOVE), u16 x planificada (plan():
       modelo medido del copper; creciente dentro de la linea), u16 registro
       ($182..$18E), u16 color, s16 a = fin del tramo anterior + 1 - x,
       s16 b = principio del nuevo - x - 6. Por linea, en el orden del plan,
       entre dos centinelas: antes, x = $FFFF (-1 con signo) y despues,
       x = $7FFF. La Amiga escribe las de x en [s0, s0 + LASTX]
       (la primera, siempre con WAIT) y esa escritura, fija en pantalla,
       sigue bien mientras s0 + a <= s < s0 + b (el MOVE cae entre x y
       x + 7: ver scroll.s, build_mid). Una carga "tarde" (a > 0 o
       b <= 0: con la base s no cae en su ventana, P50) se clasifica ACA,
       fija (P71): su clase lleva + 4 (4 = WAIT, 5 = detras, 6, 7 = con
       rellenos). La Amiga no usa su a y b: la linea con una tarde escrita
       es canonica (s0 = s) y lo escrito vale mientras la h del WAIT del
       que cuelga la tarde no cambie (celdas de 8 px de s, scroll.s
       build_mid, .td). MLX apunta a la primera carga
  LNS  lineas que build_mid tiene que mirar: u16 x (W/16 + 1) desplazamientos
       (desde LNS) de listas, una por cada 16 px de s (k = s >> 4): las
       lineas con alguna carga en pantalla para alguna s en
       [16k - 16, 16k + 32). Asi tambien se limpian las que se quedan sin
       cargas (la camara no se mueve mas de 16 px entre dos escrituras de
       la misma lista). Cada lista va por grupos de 16 lineas (S2), solo los
       que tienen alguna: s16 goff (estado del grupo en scroll.s, relativo a
       linetab: GSZ * (g - NGRP)), u16 hid = id << 6 | 2 * n (id: 1..1022,
       distinto para cada conjunto de lineas distinto del mismo grupo en k
       seguidos: con el mismo hid, el agregado de scroll.s vale), n x u16
       (linea * 32); al final, $FFFF

    python3 tools/mkscroll.py
    python3 tools/mkscroll.py --g5     # SPR_G5 (G2T C1): SEG = 256 -> work/yi1_s_g5.dat
"""
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_d                                 # noqa: E402
import tilechange                               # noqa: E402
import coinpal                                  # noqa: E402

WORK = os.path.join(HERE, "..", "work")
Y0, LINES = 192, 224
LASTXMAX = 316              # LASTX de scroll.s a 320 px (a 256: 255); MSK con el mayor
SEG = 220                   # bytes por linea en la lista del copper (scroll.s: SEG)
SEG_G5 = 256                # con -DSPR_G5: 36 B mas por segmento para el sufijo del Rex
NGRP, GSZ = LINES // 16, 8  # LNS por grupos de 16 lineas (scroll.s: NGRP, GSZ)
TARDE = 4                   # clase + TARDE: carga "tarde" en MLD (scroll.s: build_mid, .td)


def plan(loads):
    """Planifica las cargas de una linea con el modelo MEDIDO del copper en
    DPF (tools/copcal.py, P39): tiempo T en px de pantalla; un MOVE escribe
    en T y T += 16; un WAIT cuesta 32 px (T = max(T + 32, x)); hasta 32 px
    de espera salen mejor con 1-2 MOVE de relleno. Orden: por plazo (EDF)
    entre las liberadas. Carga = (fin anterior, principio nuevo, reg,
    color): se libera en fin + 1 y vence en principio.
    Devuelve [(x en que se escribe, clase, carga)] y cuantas llegan tarde.
    Clase: 0 = WAIT; 1 = MOVE detras del anterior; 2, 3 = con 1 o 2
    rellenos."""
    pend = sorted(loads)
    out, ready, i, late = [], [], 0, 0
    T = -10 ** 6
    while i < len(pend) or ready:
        if not ready and pend[i][0] + 1 > T:
            nxt = pend[i][0] + 1
            while i < len(pend) and pend[i][0] + 1 <= nxt:
                ready.append(pend[i])
                i += 1
        while i < len(pend) and pend[i][0] + 1 <= T:
            ready.append(pend[i])
            i += 1
        ready.sort(key=lambda e: e[1])
        e = ready.pop(0)
        r = e[0] + 1
        g = r - T
        if g <= 0:
            land, k = T, 1
        elif g <= 32:
            k = (g + 15) // 16
            land, k = T + 16 * k, 1 + k
        else:
            land, k = max(T + 32, r), 0
        if land > e[1]:
            late += 1
        out.append((land, k, e))
        T = land + 16
    return out, late
L2W = 848


def main():
    global SEG
    g5 = "--g5" in sys.argv[1:]
    if g5:
        SEG = SEG_G5
    d = render_d.load(os.path.join(WORK, "yi1_d.dat"))
    # SW-B activada por defecto (usuario, 2026-10-10: fidelidad 1:1
    # primero). Sus reservas de color alargan el plan del copper
    # (informe-sw-b-1010.md). SW_TILES=0 deja D_TCHG vacia (control A/B):
    # tile_apply solo consume el diario.
    tch = bytearray(struct.pack(">H", 0))
    if os.environ.get("SW_TILES", "1") != "0":
        blocks, _, _, bad = tilechange.inventory(d)
        added, rejected = tilechange.reserve_colors(d, bad)
        blocks, replacements, _, bad = tilechange.inventory(d)
        if bad or rejected or len(blocks) > 256:
            raise SystemExit("SW-B: reemplazos sin representacion exacta: %r / %r; bloques=%d"
                             % (bad, rejected, len(blocks)))
        d["blocks"], d["nblk"] = blocks, len(blocks)
        tch = bytearray(struct.pack(">H", len(replacements)))
        for cell, result, block in replacements:
            col, row = divmod(cell, 15)
            old = int(d["map"][row + Y0 // 16, col])
            tch += struct.pack(">HHBB", cell, result, block, old)
        print("SW-B: %d reemplazos, %d reservas de color exactas" % (len(replacements), len(added)))
    else:
        print("SW-B: apagada (SW_TILES=0); D_TCHG vacia")
    W, cols = d["W"], d["cols"]
    ini = np.zeros((LINES, 7), np.int32)
    chg = []
    mld = [[] for _ in range(LINES)]
    idx = render_d.l1_index(d)
    coin_flags = coinpal.event_origins(d, coinpal.origin_mask())
    coin_rows = []
    coin_data = []
    coin_initial = set()
    for L in range(LINES):
        by_reg = {}
        for ev, animated in zip(d["events"][Y0 + L], coin_flags[Y0 + L]):
            if animated:
                coin_rows.append(L)
                ev = (*ev[:3], ev[3] | 0x8000)
            by_reg.setdefault(ev[2], []).append(ev)
        row = idx[Y0 + L]
        for r, lst in by_reg.items():
            lst.sort()
            # visible a cam_x: el primer evento con fin >= cam_x
            ini[L, r - 1] = lst[0][3]
            for prev, cur in zip(lst, lst[1:]):
                if cur[3] != prev[3]:
                    # fin REAL del tramo anterior: mkleveld.py reparte los
                    # "derrames" (pixeles fuera de todo tramo) al registro
                    # que conserva el color, asi que despues de prev[1]
                    # puede haber pixeles de r que todavia necesitan el
                    # color viejo. La carga no puede caer antes del ultimo.
                    use = np.nonzero(row[prev[1] + 1:cur[0]] == r)[0]
                    fin = prev[1] + 1 + int(use[-1]) if len(use) else prev[1]
                    chg.append((fin + 1, L * SEG + 8 + (r - 1) * 4 + 2, cur[3], prev[3]))
                    mld[L].append((fin, cur[0], 0x180 + 2 * r, cur[3]))
    chg.sort()
    mlx, mldb = [], bytearray()
    pxs = [[] for _ in range(LINES)]
    late = tardes = 0
    for L in range(LINES):
        mldb += struct.pack(">HHHHHH", 0, 0xFFFF, 0, 0, 0, 0)
        mlx.append(len(mldb) // 12)
        out, lt = plan(mld[L])
        late += lt
        for tx, k, (pe, cs, r, c) in out:
            a, b = pe + 1 - tx, cs - tx - 6
            if a > 0 or b <= 0:                 # "tarde": fija, decidida aca (P71)
                k += TARDE
                tardes += 1
            mldb += struct.pack(">HHHHhh", k, tx, r, c, a, b)
            pxs[L].append(tx)
        mldb += struct.pack(">HHHHHH", 0, 0x7FFF, 0, 0, 0, 0)
    mlx.append(len(mldb) // 12)
    print("cargas a mitad de linea que llegan tarde en el plan (modelo medido): %d de %d"
          % (late, len(mldb) // 12 - 2 * LINES))
    print("cargas \"tarde\" (a > 0 o b <= 0, fijas en MLD): %d" % tardes)
    nk = W // 16 + 1
    lns_o, lns_d = [], bytearray()
    gid, gprev = [0] * NGRP, [None] * NGRP
    for k in range(nk):
        lo, hi = 16 * k - 16, 16 * k + 31 + LASTXMAX
        lns_o.append(2 * nk + len(lns_d))
        ls = [L for L in range(LINES) if any(lo <= x <= hi for x in pxs[L])]
        for g in range(NGRP):
            gl = [L for L in ls if L // 16 == g]
            if not gl:
                continue
            if gl != gprev[g]:                  # otro conjunto: otro id
                gid[g] += 1
                gprev[g] = gl
                assert gid[g] < 1023            # 1023: alllines de scroll.s
            lns_d += struct.pack(">hH%dH" % len(gl), GSZ * (g - NGRP), gid[g] << 6 | 2 * len(gl),
                                 *[32 * L for L in gl])
        lns_d += struct.pack(">H", 0xFFFF)
    lns = struct.pack(">%dH" % nk, *lns_o) + bytes(lns_d)
    assert len(lns) < 0x10000                   # scroll.s: desplazamientos u16
    rows0 = Y0 // 16
    mp = bytearray()
    for c in range(cols):
        for r in range(rows0, rows0 + 15):
            mp.append(int(d["map"][r, c]) if r < d["rows"] else 0)
    blk = bytearray()
    for b in d["blocks"]:
        for y in range(16):
            for p in range(3):
                bits = ((b[y] >> p) & 1).astype(np.uint8)
                blk += np.packbits(bits).tobytes()
    l2 = bytearray()
    for L in range(LINES):
        row = d["l2idx"][Y0 + L]
        row = np.concatenate([row, row[:L2W - 512]])
        for p in range(3):
            l2 += np.packbits(((row >> p) & 1).astype(np.uint8)).tobytes()
    l2p = struct.pack(">%dH" % (LINES * 7), *[int(v) for v in d["l2pal"][Y0:Y0 + LINES].flatten()])
    inib = struct.pack(">%dH" % (LINES * 7), *[int(v) for v in ini.flatten()])
    chgb = (struct.pack(">HHHH", 0, 0, 0, 0)
            + b"".join(struct.pack(">HHHH", *c) for c in chg) + struct.pack(">HHHH", 0xFFFF, 0, 0, 0))
    secs = [bytes(blk), bytes(mp), inib, chgb, bytes(l2), l2p,
            struct.pack(">%dH" % len(mlx), *mlx), bytes(mldb), lns, bytes(tch)]
    # El bit 15 conserva el origen animado en las copias de las listas;
    # COLORxx del OCS sólo usa los bits 11..0. No buscar por igualdad RGB.
    for section, start, stride in ((2, 0, 2), (3, 4, 8), (3, 6, 8), (7, 6, 12)):
        for pos in range(start, len(secs[section]) - 1, stride):
            if struct.unpack_from('>H', secs[section], pos)[0] & 0x8000:
                coin_data.append((section, pos))
                if section == 2:
                    line, reg = divmod(pos // 2, 7)
                    coin_initial.add(line * SEG + 10 + 4 * reg)
                elif section == 3:
                    coin_initial.add(struct.unpack_from('>H', secs[section], pos // 8 * 8 + 2)[0])
    head = b"SMWS" + struct.pack(">HHHHH", W, cols, d["nblk"], d["sky"], len(chg))
    off = len(head) + 2 + 4 * 11
    offs = []
    for s in secs:
        off = (off + 7) & ~7
        offs.append(off)
        off += len(s)
    # +52 D_COIN (SW-M) y +56 D_TCHG (SW-B), al final de la cabecera.
    from palette import COIN_ANIM, snes_to_amiga12
    coin = struct.pack('>8H4H', *[snes_to_amiga12(c) | 0x8000 for c in COIN_ANIM],
                       len(coin_data), len(coin_initial), len(set(coin_rows)), 0)
    coin += b''.join(struct.pack('>I', offs[section] + pos) for section, pos in coin_data)
    coin += b''.join(struct.pack('>I', offset) for offset in sorted(coin_initial))
    coin += b''.join(struct.pack('>H', L * 32) for L in sorted(set(coin_rows)))
    coin_off = (off + 7) & ~7
    out = bytearray(head + b"\0\0" + struct.pack(">11I", *offs[:9], coin_off, offs[9]))
    for o, s in zip(offs, secs):
        out += bytes(o - len(out)) + s
    out += bytes(coin_off - len(out)) + coin
    print('SW-M: %d palabras de origen CGRAM $64, %d filas, tabla %d B'
          % (len(coin_data), len(set(coin_rows)), len(coin)))
    name = "yi1_s_g5.dat" if g5 else "yi1_s.dat"
    open(os.path.join(WORK, name), "wb").write(out)
    print("%s: %d bytes, %d bloques, %d cambios de color (capa 1, borrado)"
          % (name, len(out), d["nblk"], len(chg)))


if __name__ == "__main__":
    main()
