#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mksprgfx.py - G3a: los graficos de los sprites del nivel (VRAM de OBJ de la
SNES) y su paso a planar Amiga, SIN el formato final (el empaquetado en
sprites adosados lo fija G2). Los .bin/.png van a work/, no a git (R9).

1. VRAM de sprites como la SNES (UploadSpriteGFX, game.s:4768):
   el nibble bajo del byte 2 de la cabecera del nivel (SSSS) elige una fila
   de SPRITEGFXLIST (4 ficheros GFX). El primer byte va a VRAM $6000
   (fichas OBJ 0-127), el segundo a $6800 (128-255), el tercero a $7000
   (256-383) y el cuarto a $7800 (384-511). La tabla se lee de game.s y los
   nombres de fichero de main.S: nada se supone. UploadGFXFile (game.s:4863)
   pasa de 3bpp a 4bpp: el plano 3 es 0, salvo en el GFX 01 (y el 17), donde
   las fichas 0, 1, 16 y 17 del fichero llevan plano 3 = bp0|bp1|bp2 (color
   con el bit 3 puesto: $FF00 en m10). Se reproduce tal cual.
   Tabla de OBJ: OBJSEL de SMW = nombre base $6000, separacion 0, de modo que
   las 512 fichas son contiguas en $6000-$7FFF (palabras).

2. Entrada OAM (x, y, tile, attr, hi) -> ficha: attr = YXPPCCCT (T = bit 8
   del nombre; CCC = paleta de sprites 0-7 = CGRAM 128 + 16*CCC; X/Y = flip);
   hi bit 1 = 16x16 (si no 8x8; SMW usa OBJSEL 8x8/16x16). 16x16 = fichas n,
   n+1 / n+16, n+17 (la suma del nibble bajo da la vuelta en 16, la del alto
   en 256 sin tocar el bit 8). El flip se aplica a toda la ficha de 16x16.
   Salida: indices de color 4 bpp (fila a fila) y mascara (indice != 0).

3. FORMATO INTERMEDIO PLANAR (provisional): para una ficha de w x h px
   (w = h = 8 o 16), bytes por fila b = w/8; el blob son 5 planos seguidos,
   cada uno h filas de b bytes (bit 7 = pixel de la izquierda):
       plano 0, plano 1, plano 2, plano 3, mascara (1 = opaco)
   total 5*h*b bytes: 8x8 = 40 B, 16x16 = 160 B. El flip y la paleta NO van
   en el blob: el flip se hornea en la ficha pedida (cada combinacion
   (tile, tamaño, flipX, flipY) es una ficha), la paleta es solo la tabla
   color->0x0RGB (16 palabras por paleta, se aplica al mostrar).

    python tools/mksprgfx.py --selftest          # ida y vuelta (sale con 1 si falla)
    python tools/mksprgfx.py --sheet             # work/sprgfx_vram.png y _used.png
    python tools/mksprgfx.py --report            # fichas por sprite y bytes
    python tools/mksprgfx.py --dump-vram         # work/cc/sprvram.bin (16 KB)
"""
import argparse
import glob
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smw2amiga import lc_lz2_decompress, decode_snes_tile, _DEF_SRC   # noqa: E402
from palette import (load_palette_bank, build_cgram, snes_to_amiga12,   # noqa: E402
                     snes_to_rgb8, cgram_palette)

WORK = os.path.join(HERE, "..", "work")
LEVEL = "3340088027"            # cabecera de Yoshi's Island 1 (como mkmario.py)


# ---------------------------------------------------------------------------
# 1. VRAM de sprites
# ---------------------------------------------------------------------------
def read_gfx_names(src):
    """GFXxx -> nombre de fichero .lz2 (main.S)."""
    names = {}
    for ln in open(os.path.join(src, "main.S"), encoding="utf-8", errors="replace"):
        m = re.match(r"GFX([0-9A-F]{2}):\s*\.INCBIN\s+\"([^\"]+)\"", ln)
        if m:
            names[int(m.group(1), 16)] = m.group(2)
    return names


def read_sprite_gfx_list(src):
    """SPRITEGFXLIST (game.s): lista de bytes, 4 por conjunto."""
    txt = open(os.path.join(src, "game.s"), encoding="utf-8", errors="replace").read()
    blk = txt.split("SPRITEGFXLIST:")[1].split("OBJECTGFXLIST:")[0]
    vals = []
    for ln in blk.splitlines():
        ln = ln.split(";")[0]
        if ".DB" in ln:
            vals += [int(v.strip().lstrip("$"), 16) for v in ln.split(".DB")[1].split(",")]
    return vals


def sprite_files(src, level):
    """-> [(vram_word, gfx_id, nombre)] para los 4 huecos del conjunto del nivel."""
    h = bytes.fromhex(level)
    sset = h[2] & 0x0F
    lst = read_sprite_gfx_list(src)
    row = lst[sset * 4:sset * 4 + 4]            # UploadSpriteGFX: byte k -> m4+3-k
    names = read_gfx_names(src)
    out = []
    for k, gid in enumerate(row):               # k = 0 -> X = 3 -> DATA_00A9D2[3] = $60
        out.append((0x6000 + 0x800 * k, gid, names[gid]))
    return sset, out


def gfx3_to_vram4(raw, gid):
    """UploadGFXFile: 3bpp (24 B/ficha) -> 4bpp SNES (32 B/ficha), 128 fichas."""
    out = bytearray()
    for k in range(128):
        t = raw[k * 24:(k + 1) * 24]
        if len(t) < 24:
            t = t + bytes(24 - len(t))
        y = 0x7F - k                            # contador Y de UploadGFXFile
        m10 = 0
        if gid in (0x01, 0x17) and (y >= 0x7E or 0x6E <= y < 0x70):
            m10 = 0xFF00
        out += t[:16]                           # planos 0 y 1
        for r in range(8):
            bp0, bp1, bp2 = t[2 * r], t[2 * r + 1], t[16 + r]
            p3 = ((bp2 | bp0 | bp1) & 0xFF) if (m10 & 0xFF00) else 0
            out += bytes([bp2, p3])
    return bytes(out)


def build_vram(src, level):
    """VRAM de OBJ: 512 fichas x 32 B (4bpp SNES), tile n en [32n, 32n+32)."""
    sset, files = sprite_files(src, level)
    vram = bytearray(512 * 32)
    for vw, gid, name in files:
        raw = lc_lz2_decompress(open(os.path.join(src, "graphics", name), "rb").read())
        v4 = gfx3_to_vram4(raw, gid)
        base = (vw - 0x6000) // 16 * 32        # palabras -> ficha (16 palabras) -> bytes
        vram[base:base + len(v4)] = v4
    return bytes(vram), sset, files


# ---------------------------------------------------------------------------
# 2. OAM -> ficha
# ---------------------------------------------------------------------------
def tile_grid(n, w):
    """Numeros de ficha (9 bits) de una ficha de w px, en filas."""
    k = w // 8
    return [[(n & 0x100) | (((n & 0xF0) + 16 * r) & 0xF0) | ((n + c) & 0x0F)
             for c in range(k)] for r in range(k)]


def ficha(vram, tile, w, fx, fy):
    """Indices de color (lista de h filas de w) con el flip ya aplicado."""
    g = tile_grid(tile, w)
    rows = [[0] * w for _ in range(w)]
    for r, trow in enumerate(g):
        for c, t in enumerate(trow):
            px = decode_snes_tile(vram[t * 32:(t + 1) * 32], 4)
            for y in range(8):
                rows[r * 8 + y][c * 8:c * 8 + 8] = px[y]
    if fx:
        rows = [row[::-1] for row in rows]
    if fy:
        rows = rows[::-1]
    return rows


def mask_of(idx):
    return [[1 if v else 0 for v in row] for row in idx]


# ---------------------------------------------------------------------------
# 3. Planar Amiga (intermedio) e inverso
# ---------------------------------------------------------------------------
def to_planar(idx):
    w = len(idx[0])
    h = len(idx)
    b = w // 8
    planes = [bytearray(h * b) for _ in range(5)]
    for y in range(h):
        for x in range(w):
            v = idx[y][x]
            bit = 0x80 >> (x & 7)
            o = y * b + x // 8
            for p in range(4):
                if (v >> p) & 1:
                    planes[p][o] |= bit
            if v:
                planes[4][o] |= bit
    return b"".join(bytes(p) for p in planes)


def from_planar(blob, w):
    b = w // 8
    h = w
    ps = h * b
    assert len(blob) == 5 * ps
    idx = [[0] * w for _ in range(h)]
    mask = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            o = y * b + x // 8
            s = 7 - (x & 7)
            v = 0
            for p in range(4):
                v |= ((blob[p * ps + o] >> s) & 1) << p
            idx[y][x] = v
            mask[y][x] = (blob[4 * ps + o] >> s) & 1
    return idx, mask


# ---------------------------------------------------------------------------
# Referencia independiente: leer la VRAM pixel a pixel (palabras SNES)
# ---------------------------------------------------------------------------
def ref_pixel(vram, tile, w, fx, fy, x, y):
    sx = w - 1 - x if fx else x
    sy = w - 1 - y if fy else y
    t = tile_grid(tile, w)[sy // 8][sx // 8]
    base = t * 32
    ry, rx = sy & 7, 7 - (sx & 7)
    word = lambda o: vram[base + o] | vram[base + o + 1] << 8   # noqa: E731
    w01 = word(2 * ry)
    w23 = word(16 + 2 * ry)
    return (((w01 >> rx) & 1) | ((w01 >> (8 + rx)) & 1) << 1 |
            ((w23 >> rx) & 1) << 2 | ((w23 >> (8 + rx)) & 1) << 3)


# ---------------------------------------------------------------------------
# Grabaciones
# ---------------------------------------------------------------------------
def load_oam_txt(path):
    """oam_yi1.txt -> [(frame, oam_bytes)]"""
    out = []
    for ln in open(path):
        p = ln.rstrip("\n").split(" ")
        if len(p) < 11 or len(p[10]) % 10:
            continue
        out.append((int(p[0]), bytes.fromhex(p[10]), None))
    return out


def load_oam_bin(path, txt=None):
    """oracle_X_oam.bin (645 B/registro) [+ oracle_X.txt para la WRAM] -> [(frame, oam, wram)]"""
    d = open(path, "rb").read()
    wr = {}
    if txt and os.path.exists(txt):
        for ln in open(txt):
            p = ln.rstrip("\n").split(" ")
            if len(p) >= 14 and len(p[12]) == 512 and len(p[13]) == 640:
                wr[int(p[0])] = bytes.fromhex(p[12]) + bytes.fromhex(p[13])
    out = []
    for o in range(0, len(d) - 644, 645):
        fr, n = struct.unpack_from("<IB", d, o)
        out.append((fr, d[o + 5:o + 5 + 5 * n], wr.get(fr)))
    return out


def all_recordings():
    recs = {}
    p = os.path.join(WORK, "oam_yi1.txt")
    if os.path.exists(p):
        recs["oam_yi1.txt"] = load_oam_txt(p)
    for f in sorted(glob.glob(os.path.join(WORK, "oracle_*_oam.bin"))):
        base = os.path.basename(f)[:-8]
        recs[os.path.basename(f)] = load_oam_bin(f, os.path.join(WORK, base + ".txt"))
    return recs


def entries(oam):
    for i in range(0, len(oam), 5):
        x, y, t, a, hi = oam[i:i + 5]
        yield x | (hi & 1) << 8, y, t | (a & 1) << 8, a, hi


def pose_key(t, a, hi):
    return (t, 16 if hi & 2 else 8, (a >> 6) & 1, (a >> 7) & 1, (a >> 1) & 7)


# ---------------------------------------------------------------------------
# Paletas
# ---------------------------------------------------------------------------
def level_cgram(src, level):
    h = bytes.fromhex(level)
    bank, labels = load_palette_bank(os.path.join(src, "palettes", "palettes.a"))
    cg, _ = build_cgram(bank, labels, h[3] & 0x07, h[0] >> 5, (h[3] >> 3) & 0x07, h[1] >> 5)
    return cg


# ---------------------------------------------------------------------------
# Autoprueba
# ---------------------------------------------------------------------------
def selftest(vram, cg, recs):
    poses = {}
    for name, frames in recs.items():
        for _, oam, _ in frames:
            for _, _, t, a, hi in entries(oam):
                poses.setdefault(pose_key(t, a, hi), set()).add(name)
    # ademas, cada (tile, tamaño, flip) con los 8 flips/paletas no vistos no hace falta;
    # la ida y vuelta exige TODAS las poses que aparecen.
    bad = 0
    pals = {}
    for (t, w, fx, fy, c), _ in poses.items():
        idx = ficha(vram, t, w, fx, fy)
        blob = to_planar(idx)
        if len(blob) != 5 * w * w // 8:
            bad += 1
            print("FALLA tamaño", t, w)
            continue
        got, mask = from_planar(blob, w)
        pal = pals.setdefault(c, [snes_to_amiga12(v) for v in cgram_palette(cg, 8 + c)])
        ok = True
        for y in range(w):
            for x in range(w):
                r = ref_pixel(vram, t, w, fx, fy, x, y)
                if got[y][x] != r or mask[y][x] != (1 if r else 0):
                    ok = False
                    break
                # color final: planar -> paleta == SNES -> CGRAM -> OCS (color 0 = transparente)
                if r and pal[got[y][x]] != snes_to_amiga12(cg[128 + 16 * c + r]):
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            bad += 1
            print("FALLA tile=%03x %dx%d fx=%d fy=%d pal=%d" % (t, w, w, fx, fy, c))
    n = len(poses)
    print("%d grabaciones, %d poses distintas (tile,tamaño,flipX,flipY,paleta), %d OK, %d mal"
          % (len(recs), n, n - bad, bad))
    for nm, fr in recs.items():
        print("  %-34s %6d frames" % (nm, len(fr)))
    # ida y vuelta de TODAS las fichas de 8x8 de la VRAM con los 4 flips
    tb = 0
    for t in range(512):
        for fx in (0, 1):
            for fy in (0, 1):
                got, _ = from_planar(to_planar(ficha(vram, t, 8, fx, fy)), 8)
                if any(got[y][x] != ref_pixel(vram, t, 8, fx, fy, x, y)
                       for y in range(8) for x in range(8)):
                    tb += 1
    print("barrido extra: 512 fichas x 4 flips, %d mal" % tb)
    if bad or tb:
        print("FALLO")
        return 1
    print("TODO OK")
    return 0


# ---------------------------------------------------------------------------
# Cruce con los numeros de sprite (heuristico, por posicion)
# ---------------------------------------------------------------------------
def wr(wram, adr):
    """WRAM $0000-$00FF y $13C0-$14FF."""
    return wram[adr] if adr < 0x100 else wram[256 + adr - 0x13C0]


def assign(oam, wram):
    cx = wr(wram, 0x1A) | wr(wram, 0x1B) << 8
    cy = wr(wram, 0x1C) | wr(wram, 0x1D) << 8
    mx = (wr(wram, 0x94) | wr(wram, 0x95) << 8) - cx
    my = (wr(wram, 0x96) | wr(wram, 0x97) << 8) - cy
    cands = [(-1, "mario", mx, my)]
    for i in range(12):
        if wr(wram, 0x14C8 + i) == 0:
            continue
        sx = (wr(wram, 0xE4 + i) | wr(wram, 0x14E0 + i) << 8) - cx
        sy = (wr(wram, 0xD8 + i) | wr(wram, 0x14D4 + i) << 8) - cy
        cands.append((i, wr(wram, 0x9E + i), sx, sy))
    res = []
    for x, y, t, a, hi in entries(oam):
        x = x - 512 if x >= 256 else x
        best, bd = None, 1 << 30
        for i, num, sx, sy in cands:
            dx, dy = x - sx, y - sy
            if -24 <= dx <= 72 and -24 <= dy <= 72:
                d = abs(dx - 8) + abs(dy - 8)
                if d < bd:
                    best, bd = num, d
        res.append(best)
    return res


def report(vram, recs, files):
    per = {}
    used = {}
    for name, frames in recs.items():
        for _, oam, wram in frames:
            es = list(entries(oam))
            for t, (x, y, tt, a, hi) in enumerate(es):
                w = 16 if hi & 2 else 8
                for row in tile_grid(tt, w):
                    for tile in row:
                        used[tile] = used.get(tile, 0) + 1
            if wram is None:
                continue
            nums = assign(oam, wram)
            for (x, y, tt, a, hi), num in zip(es, nums):
                w = 16 if hi & 2 else 8
                d = per.setdefault(num, [set(), set()])
                for row in tile_grid(tt, w):
                    d[0].update(row)
                d[1].add((tt, w, (a >> 6) & 1, (a >> 7) & 1))
    print("Conjunto de GFX de sprites (SSSS) y VRAM:")
    for vw, gid, nm in files:
        print("  VRAM $%04X (fichas %3d-%3d)  GFX %02X = %s" % (vw, (vw - 0x6000) // 16,
                                                              (vw - 0x6000) // 16 + 127, gid, nm))
    tot = len(used)
    print("Fichas 8x8 distintas pedidas por la OAM (todas las grabaciones): %d = %d B (40 B c/u)"
          % (tot, tot * 40))
    for vw, gid, nm in files:
        lo = (vw - 0x6000) // 16
        n = sum(1 for t in used if lo <= t < lo + 128)
        print("  %-10s %3d fichas  %5d B" % (nm, n, n * 40))
    print("Por nº de sprite (cruce por posicion con la WRAM; None = sin cruzar, puede ser extendido/particula):")
    print("  %-8s %8s %12s %8s" % ("sprite", "fichas8", "poses(flips)", "bytes"))
    for num in sorted(per, key=lambda k: (k is None, str(k))):
        t8, ps = per[num]
        s = "%02X" % num if isinstance(num, int) else str(num)
        print("  %-8s %8d %12d %8d" % (s, len(t8), len(ps), len(t8) * 40))
    return used


# ---------------------------------------------------------------------------
# PNG
# ---------------------------------------------------------------------------
def render_png(vram, cg, recs, files):
    from PIL import Image
    # paleta preferida por ficha: la mas usada en la OAM
    pref = {}
    for frames in recs.values():
        for _, oam, _ in frames:
            for _, _, t, a, hi in entries(oam):
                w = 16 if hi & 2 else 8
                c = (a >> 1) & 7
                for row in tile_grid(t, w):
                    for tt in row:
                        pref.setdefault(tt, {}).setdefault(c, 0)
                        pref[tt][c] += 1
    rgb = lambda c, i: snes_to_rgb8(cg[128 + 16 * c + i])   # noqa: E731
    bg = (40, 40, 48)
    img = Image.new("RGB", (16 * 8, 32 * 8), bg)
    px = img.load()
    for t in range(512):
        c = max(pref[t], key=pref[t].get) if t in pref else 6
        idx = ficha(vram, t, 8, 0, 0)
        for y in range(8):
            for x in range(8):
                v = idx[y][x]
                px[(t % 16) * 8 + x, (t // 16) * 8 + y] = rgb(c, v) if v else bg
    img = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
    p1 = os.path.join(WORK, "sprgfx_vram.png")
    img.save(p1)
    # poses distintas (sin flip colapsado: tal cual aparecen), 16x16 y 8x8 en dos tiras
    poses = {}
    for frames in recs.values():
        for _, oam, _ in frames:
            for _, _, t, a, hi in entries(oam):
                poses.setdefault(pose_key(t, a, hi), 0)
                poses[pose_key(t, a, hi)] += 1
    keys = sorted(poses, key=lambda k: (-k[1], k[0], k[2:]))
    cols = 24
    rows = (len(keys) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 18, rows * 18), bg)
    sp = sheet.load()
    for n, (t, w, fx, fy, c) in enumerate(keys):
        idx = ficha(vram, t, w, fx, fy)
        ox, oy = (n % cols) * 18, (n // cols) * 18
        for y in range(w):
            for x in range(w):
                if idx[y][x]:
                    sp[ox + x, oy + y] = rgb(c, idx[y][x])
    sheet = sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST)
    p2 = os.path.join(WORK, "sprgfx_used.png")
    sheet.save(p2)
    print("%s\n%s (%d poses)" % (p1, p2, len(keys)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=_DEF_SRC)
    ap.add_argument("--level", default=LEVEL)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--dump-vram", action="store_true")
    a = ap.parse_args()
    vram, sset, files = build_vram(a.src, a.level)
    cg = level_cgram(a.src, a.level)
    rc = 0
    if a.dump_vram:
        os.makedirs(os.path.join(WORK, "cc"), exist_ok=True)
        open(os.path.join(WORK, "cc", "sprvram.bin"), "wb").write(vram)
        print("work/cc/sprvram.bin: %d B (conjunto SSSS=%d)" % (len(vram), sset))
    recs = all_recordings() if (a.selftest or a.sheet or a.report) else {}
    if a.selftest:
        rc = selftest(vram, cg, recs)
    if a.report:
        report(vram, recs, files)
    if a.sheet:
        render_png(vram, cg, recs, files)
    sys.exit(rc)


if __name__ == "__main__":
    main()
