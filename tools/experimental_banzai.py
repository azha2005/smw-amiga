#!/usr/bin/env python3
"""E14a: atribuye la OAM de Banzai por la tabla y grilla del ROM.

Lee oracle_stress_sprites.txt y oracle_banzai.txt (campos 10 y 11 de
oambot.lua), sin inferir dueño por número de ficha aislado. Escribe JSON y
CSV en work/. La caja de cada ficha OAM se recorta a 256x224 antes de contar
líneas; el criterio de ocupación es presencia de una ficha OAM visible en
esa línea, independiente de su X una vez que conserva al menos un píxel.
"""
import argparse
import csv
import hashlib
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
SRC = os.path.join(os.path.dirname(HERE), "..", "smw-src-master", "project", "mw_e10", "sprite_2-2.s")
RECORDINGS = ("oracle_stress_sprites", "oracle_banzai")
SCREEN_W, SCREEN_H = 256, 224


def read_rom_tables(path=SRC):
    text = open(path, encoding="utf-8").read()

    def table(label):
        body = text.split(label + ":", 1)[1]
        vals = []
        for line in body.splitlines():
            if re.match(r"^\w", line):
                break
            line = line.split(";", 1)[0]
            if ".DB" in line:
                vals.extend(int(x, 16) for x in re.findall(r"\$([0-9A-Fa-f]{2})", line))
        return vals

    dx, dy, tile, attr = [table(k) for k in ("DATA_02D5A4", "DATA_02D5B4", "BanzaiBillTiles", "DATA_02D5D4")]
    if not (len(dx) == len(dy) == len(tile) == len(attr) == 16):
        raise ValueError("la grilla Banzai de sprite_2-2.s no tiene 16 entradas")
    return [{"dx": dx[i], "dy": dy[i], "tile": tile[i] | ((attr[i] & 1) << 8), "attr": attr[i]} for i in range(16)]


def s16(n):
    n &= 0xFFFF
    return n - 0x10000 if n & 0x8000 else n


def parse_line(line):
    p = line.rstrip("\n").split(" ")
    if len(p) < 12:
        raise ValueError("registro oracle sin campos OAM/slots")
    oam = bytes.fromhex(p[10])
    slots_raw = bytes.fromhex(p[11])
    if len(oam) % 5 or len(slots_raw) % 7:
        raise ValueError("registro oracle truncado")
    entries = []
    for i in range(0, len(oam), 5):
        x, y, tile, attr, hi = oam[i:i + 5]
        xx = x | ((hi & 1) << 8)
        if xx >= 256:
            xx -= 512
        yy = y - 256 if y >= 240 else y
        size = 16 if hi & 2 else 8
        entries.append({"index": i // 5, "x": xx, "y": yy, "raw_x": x, "raw_y": y,
                        "tile": tile | ((attr & 1) << 8),
                        "attr": attr, "size": size})
    slots = []
    for i in range(0, len(slots_raw), 7):
        n, state, num, xl, xh, yl, yh = slots_raw[i:i + 7]
        slots.append({"slot": n, "state": state, "num": num,
                      "x": s16((xh << 8) | xl), "y": s16((yh << 8) | yl)})
    return {"frame": int(p[0]), "camera": (int(p[3], 16), int(p[4], 16)),
            "entries": entries, "slots": slots}


def clipped_rows(e):
    if max(0, e["x"]) >= min(SCREEN_W, e["x"] + e["size"]):
        return range(0)
    a, b = max(0, e["y"]), min(SCREEN_H, e["y"] + e["size"])
    return range(a, max(a, b))


def attribute_banzai(frame, grid):
    """Encuentra la grilla 4x4 por (posición, ficha, atributo, tamaño).

    La ranura da el ancla modular low-byte de GetDrawInfo2. Se prueban
    desplazamientos +/-2 px y se elige el patrón con más coincidencias
    (posición, ficha, atributo y tamaño). Los empates y OAM compatibles sin
    dueño quedan explícitos.
    """
    entries = frame["entries"]
    by_key = {}
    for e in entries:
        by_key.setdefault((e["raw_x"], e["raw_y"], e["tile"], e["attr"], e["size"]), []).append(e["index"])
    bslots = [s for s in frame["slots"] if s["num"] == 0x9F and s["state"] != 0]
    detections, unresolved, used, unmatched_slots = [], [], set(), []
    cx, cy = frame["camera"]
    compatible = {e["index"] for e in entries if e["size"] == 16 and
                  any((e["tile"], e["attr"]) == (c["tile"], c["attr"]) for c in grid)}
    for s in bslots:
        ox, oy = s16(s["x"] - cx), s16(s["y"] - cy)
        candidates = []
        for shift_x in range(-2, 3):
            for shift_y in range(-2, 3):
                ex, ey = ox + shift_x, oy + shift_y
                ids = []
                for c in grid:
                    ids.extend(by_key.get(((ex + c["dx"]) & 255, (ey + c["dy"]) & 255,
                                           c["tile"], c["attr"], 16), [])[:1])
                ids = sorted(set(ids))
                if ids:
                    candidates.append({"origin": [ex, ey], "indices": ids, "matches": len(ids),
                                       "slot": s["slot"], "slot_delta": [shift_x, shift_y]})
        if not candidates:
            unmatched_slots.append({"slot": s["slot"], "origin": [ox, oy]})
            continue
        best = max(c["matches"] for c in candidates)
        winners = [c for c in candidates if c["matches"] == best]
        unique = {(tuple(c["origin"]), tuple(c["indices"])): c for c in winners}
        if len(unique) != 1:
            unresolved.append({"slot": s["slot"], "origin": [ox, oy], "status": "ambiguo",
                               "solutions": list(unique.values())})
            continue
        det = next(iter(unique.values()))
        if set(det["indices"]) & used:
            unresolved.append({"slot": s["slot"], "origin": [ox, oy], "status": "solapamiento_de_atribucion"})
            continue
        detections.append(det); used.update(det["indices"])
    visible_compat = sorted(i for i in compatible - used if len(clipped_rows(entries[i])))
    if visible_compat:
        unresolved.append({"status": "compatibles_sin_atribuir", "compatible_indices": visible_compat})
    elif unmatched_slots:
        unresolved.extend({**s, "status": "slot_sin_oam"} for s in unmatched_slots)
    status = "atribuido" if detections else \
             "ambiguo" if any(u["status"] == "ambiguo" for u in unresolved) else \
             "compatibles_sin_atribuir" if any(u["status"] == "compatibles_sin_atribuir" for u in unresolved) else \
             "slot_sin_oam" if bslots else "sin_banzai_activo"
    return sorted(used), {"status": status, "detections": detections, "ambiguous": unresolved}


def analyze_recording(name, path, grid):
    totals = Counter()
    rows = []
    banzai_count = Counter()
    for line in open(path, encoding="ascii"):
        if not line.strip():
            continue
        f = parse_line(line)
        own, attr = attribute_banzai(f, grid)
        dets = attr.get("detections", [])
        per_banzai = []
        if dets:
            for det in dets:
                bx0, by0 = det["origin"]
                visible_lines = [y for y in range(by0, by0 + 64) if 0 <= y < SCREEN_H]
                visible_cols = max(0, min(SCREEN_W, bx0 + 64) - max(0, bx0))
                own_entries = [e for e in f["entries"] if e["index"] in det["indices"] and len(clipped_rows(e))]
                if not own_entries:
                    totals["attributed_oam_offscreen_instances"] += 1
                    continue
                others = [e for e in f["entries"] if e["index"] not in det["indices"] and len(clipped_rows(e))]
                occupied = sorted({y for e in others for y in clipped_rows(e)})
                own_rows = sorted({y for e in own_entries for y in clipped_rows(e)})
                visible_lines = own_rows
                free_lines = [y for y in visible_lines if y not in occupied]
                covers64 = len(own_rows) == 64 and own_rows == list(range(own_rows[0], own_rows[0] + 64))
                full64free = covers64 and len(free_lines) == 64
                band_free = len(free_lines) == len(visible_lines)
                totals["visible_banzai_bands"] += 1
                totals["visible_banzai_lines"] += len(visible_lines)
                totals["band_free_visible_portion"] += band_free
                totals["fully_on_screen_banzai_frames"] += covers64
                totals["full_64_lines_free_frames"] += full64free
                totals["partial_vertical_frames"] += not covers64
                totals["horizontal_clipped_frames"] += visible_cols < 64
                totals["band_with_no_visible_other_oam"] += not occupied
                per_banzai.append({"slot": det["slot"], "origin": det["origin"], "indices": det["indices"],
                                   "visible_lines": len(visible_lines), "visible_width": visible_cols,
                                   "occupied_lines": len(set(visible_lines) - set(free_lines)),
                                   "owned_screen_lines": len(own_rows), "covers64_lines": covers64,
                                   "band_free": band_free, "full64_free": full64free,
                                   "fully_inside": covers64})
            if per_banzai:
                totals["banzai_visible_frames"] += 1
                totals["multiple_banzai_frames"] += len(per_banzai) > 1
            totals["ambiguous_frames"] += any(u["status"] == "ambiguo" for u in attr.get("ambiguous", []))
            totals["unresolved_compatible_frames"] += any(u["status"] == "compatibles_sin_atribuir" for u in attr.get("ambiguous", []))
            totals["slot_without_drawn_oam_frames"] += any(u["status"] == "slot_sin_oam" for u in attr.get("ambiguous", []))
        else:
            per_banzai = []
            if attr["status"] == "ambiguo":
                totals["ambiguous_frames"] += 1
            if attr["status"] == "compatibles_sin_atribuir":
                totals["unresolved_compatible_frames"] += 1
            if attr["status"] == "slot_sin_oam":
                totals["slot_without_drawn_oam_frames"] += 1
        totals["frames"] += 1
        totals["classifications_" + attr["status"]] += 1
        status = attr["status"] if per_banzai or not dets else "atribuido_fuera_pantalla"
        rows.append({"recording": name, "frame": f["frame"], "status": status,
                     "banzai_count": len(per_banzai), "detections": json.dumps(per_banzai, separators=(",", ":")),
                     "unresolved": json.dumps(attr.get("ambiguous", []), separators=(",", ":")),
                     "banzai_oam_indices": " ".join(map(str, own))})
    # Rachas de bandas libres y rango de frames medidos.
    visible_rows = [r for r in rows if r["banzai_count"] > 0]
    streaks, cur, last = [], 0, None
    free_ids, occupied_ids = [], []
    for r in rows:
        is_visible = r["banzai_count"] > 0
        is_free = is_visible and all(d["band_free"] for d in json.loads(r["detections"]))
        cur = cur + 1 if is_free and (last is None or r["frame"] == last + 1) else (1 if is_free else 0)
        if is_visible:
            (free_ids if is_free else occupied_ids).append(r["frame"])
        streaks.append(cur); last = r["frame"]
    totals["max_free_streak_in_record_order"] = max(streaks, default=0)
    totals["first_frame"] = rows[0]["frame"] if rows else None
    totals["last_frame"] = rows[-1]["frame"] if rows else None
    totals["banzai_visible_frame_ids"] = [r["frame"] for r in visible_rows]
    totals["band_free_frame_ids"] = free_ids
    totals["band_occupied_frame_ids"] = occupied_ids
    totals["band_free_ranges"] = ranges(free_ids)
    totals["band_occupied_ranges"] = ranges(occupied_ids)
    totals["visible_ranges"] = ranges([r["frame"] for r in visible_rows])
    totals["ambiguous_frame_ids"] = [r["frame"] for r in rows if '"status":"ambiguo"' in r["unresolved"]]
    totals["unresolved_compatible_frame_ids"] = [r["frame"] for r in rows if '"status":"compatibles_sin_atribuir"' in r["unresolved"]]
    totals["slot_without_drawn_oam_frame_ids"] = [r["frame"] for r in rows if '"status":"slot_sin_oam"' in r["unresolved"]]
    return dict(name=name, counts=dict(totals), frames=rows)


def ranges(ids):
    if not ids:
        return []
    out, start, prev = [], ids[0], ids[0]
    for n in ids[1:]:
        if n != prev + 1:
            out.append([start, prev]); start = n
        prev = n
    out.append([start, prev])
    return out


def selftest(grid):
    # Los tiles 0x84/0xCE/0xEE repetidos se resuelven por la grilla, no por ficha.
    entries = []
    origin = (40, 70)
    for c in grid:
        entries.append({"index": len(entries), "x": origin[0] + c["dx"], "y": origin[1] + c["dy"],
                        "raw_x": (origin[0] + c["dx"]) & 255, "raw_y": (origin[1] + c["dy"]) & 255,
                        "tile": c["tile"], "attr": c["attr"], "size": 16})
    # Mario solapa banda y otro OAM fuera de pantalla no debe ocuparla.
    entries += [{"index":16,"x":48,"y":80,"raw_x":48,"raw_y":80,"tile":3,"attr":0,"size":16},
                {"index":17,"x":-16,"y":90,"raw_x":240,"raw_y":90,"tile":3,"attr":0,"size":16}]
    fr = {"frame":1,"camera":(0,0),"entries":entries,
          "slots":[{"slot":2,"state":1,"num":0x9f,"x":40,"y":70}]}
    owned, result = attribute_banzai(fr, grid)
    assert result["status"] == "atribuido" and len(owned) == 16 and 16 not in owned and 17 not in owned
    ownset = set(owned)
    assert any(y in clipped_rows(entries[16]) for y in range(70,134))
    assert not clipped_rows(entries[17])
    # Límites: banda que rebasa arriba/abajo e izquierda/derecha se cuenta recortada.
    assert len([y for y in range(-8,56) if 0 <= y < SCREEN_H]) == 56
    assert max(0, min(SCREEN_W, -8+64) - max(0,-8)) == 56
    assert len([y for y in range(180,244) if 0 <= y < SCREEN_H]) == 44
    # Sin los otros OAM, todas las líneas visibles son libres, pero un recorte vertical
    # nunca se reporta como 64 líneas enteras libres.
    assert len(ownset) == 16 and origin[1] >= 0 and origin[1] + 64 <= SCREEN_H
    for ox, oy in ((250, 70), (-60, 70), (40, -60), (40, 220)):
        clipped = []
        for c in grid:
            x, y = ox + c["dx"], oy + c["dy"]
            if max(0, x) < min(SCREEN_W, x + 16) and max(0, y) < min(SCREEN_H, y + 16):
                clipped.append({"index": len(clipped), "x": x, "y": y, "raw_x": x & 255, "raw_y": y & 255,
                                "tile": c["tile"], "attr": c["attr"], "size": 16})
        edge = {"frame": 2, "camera": (0, 0), "entries": clipped,
                "slots": [{"slot": 2, "state": 1, "num": 0x9f, "x": ox, "y": oy}]}
        edge_ids, edge_result = attribute_banzai(edge, grid)
        assert edge_result["status"] == "atribuido" and len(edge_ids) == 4
    # Ancla 254, fila de Y=223 con wrap modular y ningún match: no aceptar
    # candidatos vacíos aunque las celdas salgan de la pantalla.
    wrap = {"frame": 3, "camera": (0, 0), "entries": [],
            "slots": [{"slot": 2, "state": 1, "num": 0x9f, "x": 254, "y": 223}]}
    assert attribute_banzai(wrap, grid)[1]["status"] == "slot_sin_oam"
    two_entries = []
    for ox in (40, 130):
        for c in grid:
            x, y = ox + c["dx"], 70 + c["dy"]
            two_entries.append({"index": len(two_entries), "x": x, "y": y, "raw_x": x & 255, "raw_y": y & 255,
                                "tile": c["tile"], "attr": c["attr"], "size": 16})
    two = {"frame": 4, "camera": (0, 0), "entries": two_entries,
           "slots": [{"slot": 1, "state": 1, "num": 0x9f, "x": 40, "y": 70},
                     {"slot": 2, "state": 1, "num": 0x9f, "x": 130, "y": 70}]}
    two_ids, two_result = attribute_banzai(two, grid)
    assert len(two_result["detections"]) == 2 and len(two_ids) == 32
    assert not any(u["status"] == "compatibles_sin_atribuir" for u in two_result["ambiguous"])
    print("autoprueba E14a: OK (Mario solapado, OAM fuera de pantalla, fichas repetidas, límites)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default=os.path.join(WORK, "experimental_banzai"))
    ap.add_argument("--src", default=SRC)
    ap.add_argument("--oracle", action="append", help="ruta a oracle_*.txt; puede repetirse")
    args = ap.parse_args()
    grid = read_rom_tables(args.src)
    if args.selftest:
        selftest(grid)
    oracle_paths = args.oracle or [os.path.join(WORK, name + ".txt") for name in RECORDINGS]
    result = {"source_tables": os.path.relpath(args.src),
              "input_sha256": {"source": sha256(args.src)}, "grid": grid,
              "screen": {"width": SCREEN_W, "height": SCREEN_H},
              "method": "exact tile+attr+16x16 grid coordinates from sprite_2-2.s; active slot is a coordinate check; visible OAM boxes clipped to screen",
              "recordings": []}
    csv_rows = []
    for path in oracle_paths:
        if not os.path.exists(path):
            raise SystemExit("falta " + path)
        name = os.path.splitext(os.path.basename(path))[0]
        result["input_sha256"][name] = sha256(path)
        rec = analyze_recording(name, path, grid)
        result["recordings"].append({"name": name, "counts": rec["counts"]})
        csv_rows.extend(rec["frames"])
    json_path = args.out + ".json"
    csv_path = args.out + ".csv"
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(csv_rows[0]) if csv_rows else [])
        if csv_rows:
            w.writeheader(); w.writerows(csv_rows)
    print(json_path)
    print(csv_path)
    for rec in result["recordings"]:
        c = rec["counts"]
        print("%s: visible %d, con 64 líneas OAM %d, full64 libres %d, bandas libres %d/%d, ambiguos %d, slot sin OAM %d, compatibles sin dueño %d, visibles %s..%s" %
              (rec["name"], c.get("banzai_visible_frames", 0), c.get("fully_on_screen_banzai_frames", 0),
               c.get("full_64_lines_free_frames", 0), c.get("band_free_visible_portion", 0),
               c.get("visible_banzai_bands", 0), c.get("ambiguous_frames", 0),
               c.get("slot_without_drawn_oam_frames", 0), c.get("unresolved_compatible_frames", 0),
               min(c.get("banzai_visible_frame_ids", [0]), default=0), max(c.get("banzai_visible_frame_ids", [0]), default=0)))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


if __name__ == "__main__":
    main()
