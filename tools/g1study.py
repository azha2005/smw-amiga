#!/usr/bin/env python3
"""
g1study.py - tarjeta G1 (2026-10-04): cuantos objetos del nivel NO entran en
las columnas de sprites libres, con 256 px, sobre cada grabacion.

Modelo (docs/estudio-g1-g0.md):
  * 4 columnas adosadas (8 sprites; a 256 px vuelve el sprite 7, D10).
  * Mario reserva 1 o 2 columnas (mspr.c: 2 si su caja mide > 16 px) en todo
    el rectangulo de sus teselas (paleta OAM 0); las libres son 4 - eso.
  * Cada objeto (ranura de sprite de SMW, o cluster si no tiene ranura) pide
    k columnas = el maximo de columnas de 16 px que cubren sus teselas en
    una linea, durante [y0, y1).
  * Una columna se reusa mas abajo solo si entre el final del uno y el
    inicio del otro hay >= GAP lineas (--gap; 17 = regla de
    docs/automatizar-9.2.md; 1 = recarga de SPRxPT por copper, G0).
  * Se coloca por Y creciente (primer hueco). Si algo no entra se descarta
    el conjunto de menos objetos (a igual cantidad, el de mayor area) que
    deja el resto colocable: esos objetos van a bob (o parpadean).

    python tools/g1study.py [--gap 17] [--cols 4] [--only banzai,chuck]
                            [--detail] [--oam work/oam_yi1.txt ...]
"""
import argparse
import glob
import itertools
import os
from collections import Counter, defaultdict

from oamstudy import parse, cover, mario_box

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
BIG = {0x9F: (0, 64, 0, 64)}               # Banzai Bill: caja relativa a la ranura
BOX = (-8, 24, -16, 32)                    # el resto: 16x32 alrededor del punto


def s16(v):
    v &= 0xFFFF
    return v - 65536 if v >= 32768 else v


def group_objects(f):
    """Teselas -> objetos: dict(id, num, tiles). Mario = id 'M' (paleta 0)."""
    cx, cy = f["cam"]
    slots = []
    for n, st, num, xl, xh, yl, yh in f["slots"]:
        if st:
            slots.append((n, num, s16((xh << 8 | xl) - cx), s16((yh << 8 | yl) - cy)))
    objs = {}
    loose = []
    for t in f["tiles"]:
        if t[3] == 0:
            objs.setdefault("M", dict(id="M", num=-1, tiles=[]))["tiles"].append(t)
            continue
        best = None
        for n, num, sx, sy in slots:
            x0, x1, y0, y1 = BIG.get(num, BOX)
            dx = max(sx + x0 - t[0], 0, t[0] + t[2] - (sx + x1))
            dy = max(sy + y0 - t[1], 0, t[1] + t[2] - (sy + y1))
            d = dx + dy
            if d <= 16 and (best is None or d < best[0]):
                best = (d, n, num)
        if best:
            objs.setdefault(best[1], dict(id=best[1], num=best[2], tiles=[]))["tiles"].append(t)
        else:
            loose.append(t)
    # sin ranura (particulas, puntos, monedas...): cluster por cercania y paleta
    cl = []
    for t in sorted(loose):
        for o in cl:
            if o["pal"] == t[3] and abs(o["x"] - t[0]) <= 16 and \
                    t[1] <= o["y1"] + 1 and t[1] + t[2] >= o["y0"] - 1:
                o["x"] = min(o["x"], t[0])
                o["y0"] = min(o["y0"], t[1])
                o["y1"] = max(o["y1"], t[1] + t[2])
                o["tiles"].append(t)
                break
        else:
            cl.append(dict(pal=t[3], x=t[0], y0=t[1], y1=t[1] + t[2], tiles=[t]))
    for i, o in enumerate(cl):
        objs["x%d" % i] = dict(id="x%d" % i, num=-2, tiles=o["tiles"])
    for o in objs.values():
        ts = o["tiles"]
        o["y0"] = min(t[1] for t in ts)
        o["y1"] = max(t[1] + t[2] for t in ts)
        k = 0
        for y in range(o["y0"], o["y1"]):
            iv = [(max(0, t[0]), min(256, t[0] + t[2])) for t in ts
                  if t[1] <= y < t[1] + t[2] and t[0] + t[2] > 0 and t[0] < 256]
            if iv:
                k = max(k, cover(iv))
        o["k"] = k
        if o["id"] == "M":
            mb = mario_box(ts)
            o["k"] = mb[0]
    return [o for o in objs.values() if o["k"] > 0]


def place_cols(objs, ncol, gap):
    """Primer hueco por Y creciente. Mario va fijo en las primeras columnas.
    Devuelve (columnas con sus intervalos (y0, y1, id), objetos que no entraron)."""
    cols = [[] for _ in range(ncol)]

    def free(c, o):
        return all(o["y1"] + gap <= a or b + gap <= o["y0"] for a, b, _ in c)
    out = []
    for o in sorted(objs, key=lambda o: (o["id"] != "M", o["y0"])):
        got = [c for c in cols if free(c, o)]
        if len(got) < o["k"]:
            out.append(o)
            continue
        for c in got[:o["k"]]:
            c.append((o["y0"], o["y1"], o["id"]))
    return cols, out


TAIL = False        # --tail: la ultima columna estrecha de un objeto va en 1 canal suelto


def place_ch(objs, ncol, gap):
    """Modelo por canales (2 por columna): un objeto de k columnas cuyo
    sobrante (ancho - 16 (k-1)) mide <= 8 px usa k-1 parejas adosadas mas UN
    canal suelto (3 colores) para el sobrante. Las parejas piden sus dos
    canales libres; el canal suelto se busca primero entre los que tienen la
    pareja ocupada. Hipotesis sin verificar: el sobrante cabe en 3 colores."""
    ch = [[] for _ in range(2 * ncol)]

    def free(c, o):
        return all(o["y1"] + gap <= a or b + gap <= o["y0"] for a, b, _ in c)
    out = []
    for o in sorted(objs, key=lambda o: (o["id"] != "M", o["y0"])):
        xs = [max(0, t[0]) for t in o["tiles"]]
        xe = [min(256, t[0] + t[2]) for t in o["tiles"]]
        w = max(xe) - min(xs)
        k = o["k"]
        tail = k >= 2 and w - 16 * (k - 1) <= 8 and o["id"] != "M"
        pairs = k - 1 if tail else k
        take = []
        for i in range(ncol):
            if len(take) // 2 < pairs and free(ch[2 * i], o) and free(ch[2 * i + 1], o):
                take += [2 * i, 2 * i + 1]
        if len(take) // 2 < pairs:
            out.append(o)
            continue
        if tail:
            cand = [c for c in range(2 * ncol) if c not in take and free(ch[c], o)]
            if not cand:
                out.append(o)
                continue
            cand.sort(key=lambda c: 0 if ch[c ^ 1] and not free(ch[c ^ 1], o) else 1)
            take.append(cand[0])
        for c in take:
            ch[c].append((o["y0"], o["y1"], o["id"]))
    return out


def place(objs, ncol, gap):
    if TAIL:
        return place_ch(objs, ncol, gap)
    return place_cols(objs, ncol, gap)[1]


def pt_events(cols):
    """Recargas de SPRxPT: por columna, entre un objeto y el siguiente
    (ordenados por Y), antes de la linea y1 del anterior: ahi (ranura de DMA del canal, hpos
    $15 + 4 n) el DMA lee las palabras de control del que viene. La recarga
    va despues de la ultima ranura de DMA de la linea y1 - 1 y antes de la
    de y1. Devuelve (linea y1, id)."""
    ev = []
    for c in cols:
        c = sorted(c)
        for (a0, a1, _), (b0, b1, bid) in zip(c, c[1:]):
            line = a1
            if b0 > 0 and 0 < line < 224:
                ev.append((line, bid))
    return ev


def chain_bytes(cols, objs):
    """Bytes que la CPU tendria que copiar por frame para encadenar por DMA:
    en cada columna con 2 o mas objetos, el flujo de todos los que no son
    Mario (el de Mario ya lo escribe mspr.c en su buffer). Un objeto de k
    columnas y L lineas: k * 2 canales * (8 + 4 L) bytes (control, datos,
    terminador)."""
    by = {o["id"]: o for o in objs}
    tot = 0
    for c in cols:
        if len(c) < 2:
            continue
        for y0, y1, oid in c:
            if oid != "M":
                tot += 2 * (8 + 4 * (y1 - y0))
    return tot


def solve(objs, ncol, gap):
    """Conjunto minimo a sacar (bob/parpadeo) para que el resto entre."""
    miss = place(objs, ncol, gap)
    if not miss:
        return []
    cand = [o for o in objs if o["id"] != "M"]
    cand.sort(key=lambda o: -(o["k"] * (o["y1"] - o["y0"])))
    for r in range(1, min(len(cand), 4) + 1):
        for sub in itertools.combinations(cand, r):
            rest = [o for o in objs if o not in sub]
            if not place(rest, ncol, gap):
                return list(sub)
    return miss


def lines_over(f, ncol):
    """Lineas de pantalla que piden mas de ncol columnas (Mario real)."""
    mb = mario_box(f["tiles"])
    n = 0
    for y in range(224):
        on = [t for t in f["tiles"] if t[3] != 0 and t[1] <= y < t[1] + t[2]]
        c = cover([(max(0, t[0]), min(256, t[0] + t[2])) for t in on]) if on else 0
        if mb and mb[1] <= y < mb[2]:
            c += mb[0]
        n += c > ncol
    return n


def study(name, frames, ncol, gap, detail, force=()):
    r = dict(name=name, frames=len(frames), over_lines=0, over_frames=0,
             removed_frames=0, removed_objs=0, ep=0, nums=Counter(), worst=0,
             unres_frames=0, wide_m=0)
    prev = set()
    ex = []
    for f in frames:
        ol = lines_over(f, ncol)
        r["over_lines"] += ol
        r["over_frames"] += ol > 0
        objs = group_objects(f)
        if force:
            fb = [o for o in objs if o["num"] in force]
            r["forced"] = r.get("forced", 0) + bool(fb)
            objs = [o for o in objs if o["num"] not in force]
        mb = [o for o in objs if o["id"] == "M"]
        r["wide_m"] += bool(mb and mb[0]["k"] == 2)
        rem = solve(objs, ncol, gap)
        cur = {o["id"] for o in rem}
        # lo que no entra ni sacando objetos: Mario solo ya no cabe (no pasa)
        if rem:
            r["removed_frames"] += 1
            r["removed_objs"] += len(rem)
            r["worst"] = max(r["worst"], len(rem))
            for o in rem:
                r["nums"][o["num"]] += 1
            if detail and len(ex) < 6:
                ex.append((f["frame"], [(o["id"], o["num"], o["k"], o["y0"], o["y1"]) for o in rem]))
        r["ep"] += len(cur - prev)
        prev = cur
    r["ex"] = ex
    return r


def chain_main(a, paths, force):
    FRAME = 141876                       # ciclos de CPU por frame PAL (7,0938 MHz / 50)
    print("cols=%d gap=%d bob=%s" % (a.cols, a.gap, a.force_bob))
    print("| grabacion | frames | media B | p99 B | max B | max ciclos | max % frame | frames con copia |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|")
    for p in paths:
        nm = os.path.basename(p).replace("oracle_", "").replace(".txt", "")
        frames = [f for f in parse(p, 0x29) if f["mode"] == 0x14]
        if not frames:
            continue
        v = []
        for f in frames:
            objs = [o for o in group_objects(f) if o["num"] not in force]
            rem = solve(objs, a.cols, a.gap)
            keep = [o for o in objs if o not in rem]
            cols, _ = place_cols(keep, a.cols, a.gap)
            v.append(chain_bytes(cols, keep))
        v.sort()
        n = len(v)
        print("| %s | %d | %.0f | %d | %d | %d | %.1f | %d |" % (
            nm, n, sum(v) / n, v[int(n * 0.99) - 1], v[-1], v[-1] * 4.6,
            100 * v[-1] * 4.6 / FRAME, sum(1 for x in v if x)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oam", nargs="*", default=None,
                    help="grabaciones (por defecto work/oam_yi1.txt y work/oracle_*.txt)")
    ap.add_argument("--gap", type=int, default=17)
    ap.add_argument("--cols", type=int, default=4)
    ap.add_argument("--only", default="")
    ap.add_argument("--force-bob", default="",
                    help="numeros de sprite SMW (hex, coma) que van siempre a bob y no "
                         "ocupan columnas, p.ej. 9F; se cuentan aparte")
    ap.add_argument("--tail", action="store_true",
                    help="modelo por canales: el sobrante estrecho (<= 8 px) de un objeto "
                         "de ancho 17-24 (Rex = 20 px) va en un canal suelto de 3 colores")
    ap.add_argument("--chain", action="store_true",
                    help="G0: en vez de la tabla, bytes por frame que copiaria la CPU para "
                         "encadenar por DMA (media, p99, max) y ciclos a 4,6 c/B (MOVEM.L)")
    ap.add_argument("--detail", action="store_true")
    a = ap.parse_args()
    paths = a.oam or [os.path.join(WORK, "oam_yi1.txt")] + \
        sorted(glob.glob(os.path.join(WORK, "oracle_*.txt")))
    global TAIL
    TAIL = a.tail
    force = tuple(int(x, 16) for x in a.force_bob.split(",") if x)
    if a.chain:
        return chain_main(a, paths, force)
    only = [s for s in a.only.split(",") if s]
    print("cols=%d gap=%d" % (a.cols, a.gap))
    print("| grabacion | frames | M2col | frames con lineas >libres | lineas | "
          "frames con objeto fuera | objetos fuera (suma) | max a la vez | episodios | quien (nº SMW: veces) |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    tot = Counter()
    for p in paths:
        nm = os.path.basename(p).replace("oracle_", "").replace(".txt", "")
        if only and nm not in only:
            continue
        frames = [f for f in parse(p, 0x29) if f["mode"] == 0x14]
        if not frames:
            continue
        r = study(nm, frames, a.cols, a.gap, a.detail, force)
        if force:
            tot["forced"] += r.get("forced", 0)
        who = ", ".join("%s: %d" % ("$%02X" % k if k >= 0 else ("sin ranura" if k == -2 else "M"), v)
                        for k, v in r["nums"].most_common(5))
        print("| %s | %d | %d | %d | %d | %d | %d | %d | %d | %s |" % (
            nm, r["frames"], r["wide_m"], r["over_frames"], r["over_lines"],
            r["removed_frames"], r["removed_objs"], r["worst"], r["ep"], who))
        for k in ("frames", "wide_m", "over_frames", "over_lines", "removed_frames",
                  "removed_objs", "ep"):
            tot[k] += r[k]
        for e in r["ex"]:
            print("    ej. frame %d: %s" % e)
    if force:
        print("frames con objetos forzados a bob (%s): %d" % (a.force_bob, tot["forced"]))
    print("| TOTAL | %d | %d | %d | %d | %d | %d | - | %d | |" % (
        tot["frames"], tot["wide_m"], tot["over_frames"], tot["over_lines"],
        tot["removed_frames"], tot["removed_objs"], tot["ep"]))


if __name__ == "__main__":
    main()
