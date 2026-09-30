#!/usr/bin/env python3
"""
orc_has.py - que hay en un oraculo (work/oracle_*.txt): por numero de sprite,
en que frames esta en alguna ranura y con que estado; y un resumen de Mario
por tramos (X, $19 = power-up, $71 = animacion, subnivel, camara).

Formato del .txt: el de tools/oracle2bin.py (campo 0 = frame, 1 = modo $0100,
2 = translevel $13BF, 12 = WRAM $0000-$00FF, 13 = WRAM $13C0-$14FF).

    python tools/orc_has.py work/oracle_yi1.txt
    python tools/orc_has.py work/oracle_yi1.txt --sprite 95        # solo el Chuck
    python tools/orc_has.py work/oracle_yi1.txt --mario-only
    python tools/orc_has.py work/oracle_yi1.txt --sprites-only --min-len 5

Un "tramo" de sprite es una racha de frames consecutivos del oraculo en que
algun ranura lo tiene con estado != 0 (a la derecha: histograma de estados
$14C8 en frames, rango de X y de Y, ranuras usadas). Un tramo de Mario es una
racha con el mismo ($19, $71, translevel, modo); el $71 != 0 son las
animaciones (tuberia, muerte, crecer...).
"""
import argparse
import sys
from collections import Counter

NSLOT = 12


def read(path):
    """-> lista de dicts por frame (solo lo que se usa)."""
    out = []
    with open(path) as f:
        for ln in f:
            p = ln.rstrip("\r\n").split(" ")
            if len(p) < 14 or len(p[12]) != 512 or len(p[13]) != 640:
                continue
            dp = bytes.fromhex(p[12])
            w = bytes.fromhex(p[13])            # $13C0..$14FF
            fr = {
                "f": int(p[0]), "mode": int(p[1], 16), "tl": int(p[2], 16),
                "x": dp[0x94] | dp[0x95] << 8, "y": dp[0x96] | dp[0x97] << 8,
                "pw": dp[0x19], "anim": dp[0x71], "air": dp[0x72],
                "cam": dp[0x1A] | dp[0x1B] << 8, "camy": dp[0x1C] | dp[0x1D] << 8,
                "sub": dp[0x0E], "dp": dp, "w": w,
            }
            sl = []
            for k in range(NSLOT):
                st = w[0x108 + k]               # $14C8 + k
                if not st:
                    continue
                num = dp[0x9E + k]
                sx = dp[0xE4 + k] | w[0x120 + k] << 8       # $14E0
                sy = dp[0xD8 + k] | w[0x114 + k] << 8       # $14D4
                sl.append((num, st, sx, sy, k))
            fr["spr"] = sl
            out.append(fr)
    return out


def runs(frames, key_of):
    """Agrupa frames consecutivos (por indice en el oraculo, con salto de numero
    de frame roto) con la misma clave. -> [(i0, i1)]"""
    res = []
    i0 = None
    prev = None
    for i, fr in enumerate(frames):
        k = key_of(fr)
        contiguous = prev is not None and fr["f"] == frames[i - 1]["f"] + 1
        if i0 is not None and (k != prev or not contiguous):
            res.append((i0, i - 1))
            i0 = None
        if i0 is None:
            i0 = i
        prev = k
    if i0 is not None:
        res.append((i0, len(frames) - 1))
    return res


def s8(v):
    return v - 256 if v >= 128 else v


def stomps(frames):
    """Pisotones: frames en que Mario, EN EL AIRE ($72 != 0), pasa de caer (o casi
    parado) a subir de golpe (SpeedY $7D <= -$20, salto de >= $20 en un frame) con
    un sprite a menos de $20 px en X y de 0 a $38 px por debajo de sus pies.
    -> lista de (indice de frame, numero de sprite)."""
    out = []
    for i in range(1, len(frames)):
        a, b = frames[i - 1], frames[i]
        if b["f"] != a["f"] + 1 or not a["air"]:
            continue
        va, vb = s8(a["dp"][0x7D]), s8(b["dp"][0x7D])
        if vb > -0x20 or vb - va > -0x20:
            continue
        for (nm, st, sx, sy, k) in b["spr"]:
            if st in (8, 9, 0xA, 0xB, 1) and abs(sx - b["x"]) <= 0x20 and 0 <= sy - b["y"] <= 0x38:
                out.append((i, nm))
                break
    return out


def sprite_report(frames, only, min_len):
    sp = {}
    for i, nm in stomps(frames):
        sp.setdefault(nm, []).append(i)
    nums = sorted({s[0] for fr in frames for s in fr["spr"]})
    if only is not None:
        nums = [n for n in nums if n == only]
    if not nums:
        print("(ningun sprite%s)" % (" $%02X" % only if only is not None else ""))
    for num in nums:
        present = [any(s[0] == num for s in fr["spr"]) for fr in frames]
        total = sum(present)
        print("sprite $%02X: %d frames en total%s" % (num, total, ("; pisotones de Mario: %d (frames %s)" % (
            len(sp[num]), " ".join(str(frames[i]["f"]) for i in sp[num][:12]))) if num in sp else ""))
        for i0, i1 in runs(frames, lambda fr: any(s[0] == num for s in fr["spr"])):
            if not any(s[0] == num for s in frames[i0]["spr"]):
                continue
            n = i1 - i0 + 1
            if n < min_len:
                continue
            st = Counter()
            xs, ys, slots = [], [], set()
            for fr in frames[i0:i1 + 1]:
                seen = set()
                for (nm, s, sx, sy, k) in fr["spr"]:
                    if nm == num:
                        seen.add(s)
                        xs.append(sx)
                        ys.append(sy)
                        slots.add(k)
                for s in seen:
                    st[s] += 1
            print("  %6d-%-6d %5d fr  estados %-26s x $%04X-$%04X  y $%04X-$%04X  ranura %s" % (
                frames[i0]["f"], frames[i1]["f"], n,
                " ".join("%X:%d" % (s, c) for s, c in sorted(st.items())),
                min(xs), max(xs), min(ys), max(ys), ",".join(str(k) for k in sorted(slots))))


def mario_report(frames):
    key = lambda fr: (fr["mode"], fr["tl"], fr["pw"], fr["anim"])
    print("Mario por tramos ($19 = power-up, $71 = animacion, $72 = aire)")
    for i0, i1 in runs(frames, key):
        a, b = frames[i0], frames[i1]
        seg = frames[i0:i1 + 1]
        xs = [fr["x"] for fr in seg]
        ys = [fr["y"] for fr in seg]
        cs = [fr["cam"] for fr in seg]
        cy = [fr["camy"] for fr in seg]
        print("  %6d-%-6d %5d fr  modo %02X tl %02X  $19=%02X $71=%02X  x $%04X->$%04X (min $%04X max $%04X)  "
              "y $%04X-$%04X  cam $%04X-$%04X camY $%04X-$%04X" % (
                  a["f"], b["f"], i1 - i0 + 1, a["mode"], a["tl"], a["pw"], a["anim"],
                  a["x"], b["x"], min(xs), max(xs), min(ys), max(ys), min(cs), max(cs), min(cy), max(cy)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("oracle")
    ap.add_argument("--sprite", help="numero de sprite en hex (ej. 95), solo ese")
    ap.add_argument("--mario-only", action="store_true")
    ap.add_argument("--sprites-only", action="store_true")
    ap.add_argument("--min-len", type=int, default=1, help="ignora rachas de sprite de menos frames")
    a = ap.parse_args()
    frames = read(a.oracle)
    if not frames:
        sys.exit("%s: sin registros" % a.oracle)
    print("%s: %d registros, frames %d-%d" % (a.oracle, len(frames), frames[0]["f"], frames[-1]["f"]))
    only = int(a.sprite, 16) if a.sprite else None
    if not a.mario_only:
        sprite_report(frames, only, a.min_len)
    if not a.sprites_only and only is None:
        mario_report(frames)


if __name__ == "__main__":
    main()
