#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mide altura/ocupacion del HUD SMW y su interseccion con PF1 del blob D."""
import argparse
import os
import struct

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WORK = os.path.join(ROOT, "work")
import sys
sys.path.insert(0, HERE)
import smw2amiga
SRC_DIR = smw2amiga._DEF_SRC
SRC = os.path.join(SRC_DIR, "game.s")


def hud_tile_masks():
    """Máscaras opacas por fila para IDs referenciados en tablas STAT_BAR."""
    gfx_dir = os.path.join(SRC_DIR, "graphics")
    masks = {}
    for name in ("gb-1", "gb-2"):
        raw = smw2amiga.lc_lz2_decompress(open(os.path.join(gfx_dir, name + ".lz2"), "rb").read())
        tiles = smw2amiga.decode_snes_tileset(raw, 2)
        masks[name] = tiles
    return masks


def validate_source():
    src = open(SRC, encoding="latin-1").read()
    checks = (r"LDA\s+#\$53\s+STA BG3SC", r"LDA\.B\s+#\$42\s+STA VMADDL",
              r"LDA\.B\s+#\$63\s+STA VMADDL", r"STZ BG3VOFS",
              r"LDY\s+#\$24\s+_008294:\s+LDA TIMEUP\s+STY VTIMEL",
              r"LDA\s+#\$D0\s+_00A017:\s+STA wm_Bg3VOfs")
    missing = [s for s in checks if not __import__("re").search(s, src)]
    if missing:
        raise SystemExit("game.s cambió: no se verifican los supuestos de H1: " + ", ".join(missing))


def read_db_table(src, label):
    import re
    lines = src.splitlines()
    start = next((i for i, line in enumerate(lines) if re.match(r"\s*"+re.escape(label)+r":", line)), None)
    if start is None:
        raise ValueError("tabla no encontrada: " + label)
    body = []
    for line in lines[start:]:
        if line.split(";")[0].strip().startswith(label + ":"):
            line = line.split(":", 1)[1]
        elif not line.split(";")[0].strip().upper().startswith(".DB"):
            break
        if ".DB" in line.upper():
            body.append(line.split(".DB", 1)[1])
    return [int(x, 16) for x in re.findall(r"\$([0-9A-Fa-f]{2})", "\n".join(body))]


def composite_mask(src, masks):
    """Compone las máscaras opacas de las cuatro DMA BG3 iniciales."""
    specs = (("DATA_008C81", 1, 14, 8), ("DATA_008C89", 2, 2, 0x38),
             ("DATA_008CC1", 3, 3, 0x36), ("DATA_008CF7", 4, 14, 8))
    out = np.zeros((40, 256), np.uint8)
    for label, row, col, nbytes in specs:
        raw = read_db_table(src, label)[:nbytes]
        if len(raw) != nbytes:
            raise ValueError("longitud incorrecta en " + label)
        for i in range(0, len(raw), 2):
            tile, attr = raw[i], raw[i+1]
            bank, tid = tile // 0x80, tile % 0x80
            name = "gb-%d" % (bank+1)
            if name not in masks or tid >= len(masks[name]):
                raise ValueError("tile BG3 $%02X fuera de gb-1/gb-2 en %s" % (tile, label))
            pix = np.array([[p != 0 for p in line] for line in masks[name][tid]], np.uint8)
            if attr & 0x40:
                pix = pix[:, ::-1]
            if attr & 0x80:
                pix = pix[::-1, :]
            x, y = (col+i//2)*8, row*8
            out[y:y+8, x:x+8] = pix
    return out


def tile_union(masks, bank, ids):
    chosen = [np.array([[p != 0 for p in row] for row in masks[bank][i]], np.uint8)
              for i in sorted(set(ids))]
    return np.maximum.reduce(chosen)


def load_blob(path):
    b = open(path, "rb").read()
    if len(b) < 42 or b[:4] != b"SMWD":
        raise ValueError("blob no es SMWD")
    ver, width, height, nblk, cols, rows, _ = struct.unpack_from(">7H", b, 4)
    if ver != 1 or width == 0 or height == 0 or width != cols*16 or height != rows*16:
        raise ValueError("cabecera/dimensiones SMWD invalidas")
    off = struct.unpack_from(">6I", b, 18)
    sizes = (nblk*96, rows*cols, (height+1)*2)
    if any(o < 42 or o+s > len(b) for o, s in zip(off[:3], sizes)):
        raise ValueError("seccion SMWD truncada o fuera de rango")
    if any(o >= len(b) for o in off[3:]):
        raise ValueError("offset SMWD fuera de rango")
    lix = np.frombuffer(b, ">u2", height+1, off[2])
    if np.any(lix[1:] < lix[:-1]):
        raise ValueError("indice LIX invalido")
    if off[3] + int(lix[-1])*8 > len(b) or off[4] + height*192 > len(b) or off[5] + height*14 > len(b):
        raise ValueError("secciones EVT/L2B/L2P truncadas")
    blocks = np.unpackbits(np.frombuffer(b, np.uint8, nblk * 96, off[0])
                           .reshape(nblk, 16, 3, 2), axis=3)
    blocks = blocks[:, :, 0] | (blocks[:, :, 1] << 1) | (blocks[:, :, 2] << 2)
    tilemap = np.frombuffer(b, np.uint8, rows * cols, off[1]).reshape(rows, cols)
    idx = np.zeros((height, width), np.uint8)
    for y in range(rows):
        for x in range(cols):
            idx[y*16:y*16+16, x*16:x*16+16] = blocks[tilemap[y, x]]
    return idx


def cameras(path):
    vals = []
    with open(path, encoding="ascii") as f:
        for line in f:
            p = line.split()
            if len(p) >= 14 and len(p[12]) == 512 and len(p[13]) == 640:
                try:
                    ram = bytes.fromhex(p[12] + p[13])
                    vals.append((int(p[0]), (ram[0x1c] | ram[0x1d] << 8) & 0x1ff,
                                 (ram[0x1a] | ram[0x1b] << 8) & 0x1fff))
                except (ValueError, IndexError):
                    continue
    return vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dat", default=os.path.join(WORK, "yi1_d.dat"))
    ap.add_argument("--out", default=os.path.join(WORK, "hud_medida.png"))
    ap.add_argument("--step", type=int, default=4)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    validate_source()
    idx = load_blob(a.dat)
    H, W = idx.shape
    masks = hud_tile_masks()
    src = open(SRC, encoding="latin-1").read()
    hud_mask = composite_mask(src, masks)
    regular_digits = tile_union(masks, "gb-1", range(10))
    bonus_ids = read_db_table(src, "DATA_008E06")
    bonus_union = tile_union(masks, "gb-2", [i-0x80 for i in bonus_ids])
    if a.selftest:
        assert hud_mask.shape == (40, 256) and hud_mask.sum() > 0
        assert [len(masks["gb-%d" % n]) for n in (1, 2)] == [128, 128]
        assert regular_digits.shape == (8, 8) and regular_digits.sum() > 0
        assert bonus_union.shape == (8, 8) and bonus_union.sum() > 0
        assert len(bonus_ids) == 20
        assert tuple(sum(p != 0 for p in row) for row in masks["gb-1"][0x3A]) == (0, 0, 1, 3, 4, 5, 5, 6)
        import tempfile
        raw = open(a.dat, "rb").read()
        with tempfile.NamedTemporaryFile(delete=False, dir=WORK, suffix=".tmp") as f:
            f.write(raw[:32])
            badpath = f.name
        try:
            try:
                load_blob(badpath)
                raise AssertionError("se aceptó blob truncado")
            except ValueError:
                pass
        finally:
            os.unlink(badpath)
        print("Auto-test HUD: OK (cabecera SMWD, fuente, bancos gb-1/2, composición/flip, unión de dígitos, rechazo truncado)")
    # GM04DoDMA escreve $502E/$5042/$5063/$508E (filas BG3 1..4):
    # 4, 28, 27, 4 tiles. BG3VOFS e IRQ controlam o corte vertical.
    # A área conservadora é y=0..35/36; máscara opaca vem de gb-1.
    hud_screen_y0, hud_screen_y1 = 0, 36
    screen_h = 224
    default_cam_y = 192
    print("HUD del codigo: BG3SC=$53 -> $5000; DMA estaticas $502E/$5042/$5063/$508E = filas 1..4")
    print("Banda de cambio PF1/PF2 conservadora: y=%d..%d (%d lineas); source NMI fuerza BG3VOFS=0" %
          (hud_screen_y0, hud_screen_y1-1, hud_screen_y1-hud_screen_y0))
    print("Máscara compuesta de DMA estáticas gb-1/2: %d/%d píxeles opacos; filas opacas=%s" %
          (int(hud_mask.sum()), hud_mask.size,
           ",".join(str(i) for i, n in enumerate(hud_mask.sum(axis=1)) if n)))
    print("Reserva gb-1 tile $3A/$3B opacidad por fila: %s / %s" %
          (tuple(sum(p != 0 for p in row) for row in masks["gb-1"][0x3A]),
           tuple(sum(p != 0 for p in row) for row in masks["gb-1"][0x3B])))
    print("Dígitos regulares $00..$09 (gb-1), opacos por fila=%s" %
          (tuple(int(x) for x in regular_digits.sum(axis=1)),))
    print("DATA_008E06 bonus stars (%d bytes, %d IDs únicos gb-2): %s; unión opaca por fila=%s" %
          (len(bonus_ids), len(set(bonus_ids)), ",".join("$%02X" % x for x in sorted(set(bonus_ids))),
           tuple(int(x) for x in bonus_union.sum(axis=1))))
    print("D blob: %dx%d; PF1 opaco = indice planar > 0 (no se usa el color cielo como mascara)" % (W, H))
    print("camY=192: nivel visible %d..%d; banda conservadora candidata en pantalla y=%d..%d" %
          (default_cam_y, default_cam_y + screen_h - 1, hud_screen_y0, hud_screen_y1-1))
    # El blob almacena un lienzo de nivel sin el BG3/IRQ; compara la banda
    # candidata con el mismo tramo de coordenadas bajo la cámara documentada.
    visible_y0, visible_y1 = default_cam_y + hud_screen_y0, default_cam_y + hud_screen_y1
    visible_band = idx[visible_y0:visible_y1, :256]
    visible_counts = np.count_nonzero(visible_band, axis=1)
    print("PF1 en banda conservadora nivel Y=%d..%d a camY=192 (ventana 256px desde x de cámara): %d/%d lineas; %d pixeles de %d (%0.3f%%)" %
          (visible_y0, visible_y1-1, np.count_nonzero(visible_counts), len(visible_counts), int(visible_counts.sum()),
           visible_band.size, 100*visible_counts.sum()/max(visible_band.size, 1)))
    extra = idx[visible_y1:visible_y1+1, :256]
    print("Sensibilidad al borde +1: si se incluye screen y=36 (nivel y=%d), añade %d píxeles PF1/256 en x=0" %
          (visible_y1, int(np.count_nonzero(extra))))
    sweep = [(int(np.count_nonzero(idx[visible_y0:visible_y1, x:x+256])), x)
             for x in range(0, W-255, a.step)]
    sweep_plus = [(int(np.count_nonzero(idx[visible_y0:visible_y1+1, x:x+256])), x)
                  for x in range(0, W-255, a.step)]
    swmin, swmax = min(sweep), max(sweep)
    print("Barrido camX completo (0..%d paso %d, camY=192): PF1 min %d/9216 en x=%d; max %d/9216 en x=%d" %
          (W-256, a.step, swmin[0], swmin[1], swmax[0], swmax[1]))
    pmin, pmax = min(sweep_plus), max(sweep_plus)
    print("Incluyendo y=36 (+1 linea): PF1 min %d/9472 x=%d; max %d/9472 x=%d" %
          (pmin[0], pmin[1], pmax[0], pmax[1]))
    values = [(os.path.basename(p).removesuffix(".txt"), p)
              for p in sorted(__import__("glob").glob(os.path.join(WORK, "oracle_*.txt")))]
    all_cam_y = set()
    for name, path in values:
        if not os.path.isfile(path):
            continue
        cams = cameras(path)
        if not cams:
            print("camara %s: sin registros legibles" % name)
            continue
        unique = sorted({y for _, y, _ in cams})
        all_cam_y.update(unique)
        lo, hi = min(unique), max(unique)
        ranges = []
        # El nivel D tiene 5120 px; cada grabación aporta sus camX reales.
        frames = cams
        view_counts = []
        for _, y, x in frames:
            y0, y1 = hud_screen_y0, hud_screen_y1
            rows = idx[max(0, y+y0):min(H, y+y1), x:min(W, x+256)]
            view_counts.append((int(np.count_nonzero(rows)), int(rows.size), y, x))
        for y in unique:
            y0, y1 = hud_screen_y0, hud_screen_y1
            rows = idx[max(0, y+y0):min(H, y+y1), :256]
            n = int(np.count_nonzero(rows))
            ranges.append((y, y0, y1-1, n, rows.size))
        print("camara %s: %d frames; camY=%s" %
              (name, len(cams), ",".join(map(str, unique))))
        if ranges:
            dens = [100*r[3]/max(r[4], 1) for r in ranges]
            if view_counts:
                lo_v = min(view_counts, key=lambda q:q[0]); hi_v=max(view_counts,key=lambda q:q[0])
                print("  ventanas 256px observadas: min=%d/%d (%0.1f%%) camY=%d camX=%d; max=%d/%d (%0.1f%%) camY=%d camX=%d" %
                      (lo_v[0],lo_v[1],100*lo_v[0]/max(lo_v[1],1),lo_v[2],lo_v[3],
                       hi_v[0],hi_v[1],100*hi_v[0]/max(hi_v[1],1),hi_v[2],hi_v[3]))
        else:
            print("  ninguna interseccion HUD con viewport")

    print("Unión exacta de camY observadas en todos los oráculos: %s" %
          ",".join(map(str, sorted(all_cam_y))))

    # Evidencia geometrica: PF1 claro, PF2/cielo oscuro, banda HUD roja.
    y0 = default_cam_y
    frame = idx[y0:y0+screen_h]
    rgb = np.zeros((screen_h, W, 3), np.uint8)
    rgb[:] = (30, 55, 95)
    rgb[frame > 0] = (220, 220, 220)
    image = Image.fromarray(rgb).resize((W, screen_h), Image.Resampling.NEAREST)
    draw = ImageDraw.Draw(image)
    yy0, yy1 = hud_screen_y0, hud_screen_y1
    draw.rectangle((0, yy0, W-1, yy1-1), outline=(255, 30, 30), width=1)
    image.save(a.out)
    print("-> %s" % a.out)


if __name__ == "__main__":
    main()
