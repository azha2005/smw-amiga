#!/usr/bin/env python3
"""Recuento D1 de una traza completa por VBL; no captura ni emula WinUAE.

CSV: vbl,logic_frame,shown_frame,photo_ticks,tick_ticks.
Primera fila = estado inicial (fuera del denominador). Después, una fila
por VBL PAL. Los frames son contadores absolutos sin wrap; shown_frame es
la foto efectivamente mostrada, no DC_NPUB. Duraciones integradas en ticks
CIA-B calibrados: tick_ticks del tick terminado y photo_ticks de la foto
nueva mostrada. Vacío solo cuando no hubo ese evento. Ver medida-d1-estres.
"""
import argparse
import csv
import json
import math
import sys


def timing(values):
    if not values:
        return {"samples": 0, "mean": None, "p99": None, "max": None}
    ordered = sorted(values)
    return {"samples": len(values), "mean": sum(values) / len(values),
            "p99": ordered[math.ceil(.99 * len(values)) - 1], "max": ordered[-1]}


def count(rows):
    if len(rows) < 2:
        raise ValueError("se necesitan estado inicial y al menos un VBL")
    omitted, ages, photos, ticks = [], [], [], []
    lost_ticks = skipped_photos = streak = longest = 0
    for i, row in enumerate(rows):
        if min(row["vbl"], row["logic_frame"], row["shown_frame"]) < 0:
            raise ValueError("contadores negativos o anteriores a la primera foto")
        if row["shown_frame"] > row["logic_frame"]:
            raise ValueError("la foto mostrada es posterior a la lógica")
        if not i:
            continue
        prev = rows[i - 1]
        dl = row["logic_frame"] - prev["logic_frame"]
        ds = row["shown_frame"] - prev["shown_frame"]
        if row["vbl"] != prev["vbl"] + 1 or dl not in (0, 1) or ds < 0:
            raise ValueError("traza discontinua, wrap o más de un tick por VBL")
        for column, event, values in (("tick_ticks", dl > 0, ticks),
                                      ("photo_ticks", ds > 0, photos)):
            value = row[column]
            if event != (value is not None) or (value is not None and value < 0):
                raise ValueError("%s debe existir exactamente cuando hay evento" % column)
            if value is not None:
                values.append(value)
        missed = int(ds == 0)
        omitted.append(missed)
        streak = streak + 1 if missed else 0
        longest = max(longest, streak)
        lost_ticks += int(dl == 0)
        skipped_photos += max(0, ds - 1)
        ages.append(row["logic_frame"] - row["shown_frame"])
    n = len(omitted)
    width = min(250, n)
    rolling = sum(omitted[:width])
    worst, start = rolling, rows[1]["vbl"]
    for i in range(width, n):
        rolling += omitted[i] - omitted[i - width]
        if rolling > worst:
            worst, start = rolling, rows[i - width + 2]["vbl"]
    total = sum(omitted)
    return {"vbl_total": n, "omitted": total, "omitted_percent": 100 * total / n,
            "max_streak": longest, "worst_window": {"width": width,
            "omitted": worst, "first_vbl": start}, "photo_age_logic_ticks": timing(ages),
            "lost_logic_ticks": lost_ticks, "skipped_logical_photos_between_presentations": skipped_photos,
            "integrated_photo_cia_ticks": timing(photos), "logic_cia_ticks": timing(ticks),
            "objective_zero_omissions": total == 0,
            "minimum_numeric_thresholds_met": n >= 250 and total * 1000 <= n
            and longest <= 1 and worst <= 1}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("trace", help="CSV por VBL exportado de WinUAE")
    args = ap.parse_args()
    try:
        with open(args.trace, newline="") as stream:
            reader = csv.DictReader(stream)
            required = {"vbl", "logic_frame", "shown_frame", "photo_ticks", "tick_ticks"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("faltan columnas CSV: " + ",".join(sorted(required)))
            rows = [{k: (int(r[k]) if r[k] != "" else None) for k in required}
                    for r in reader]
        if any(any(r[k] is None for k in ("vbl", "logic_frame", "shown_frame")) for r in rows):
            raise ValueError("contador obligatorio vacío")
        report = count(rows)
        report["provenance"] = "CSV declarado; verificar WinUAE y configuración en manifiesto externo"
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
