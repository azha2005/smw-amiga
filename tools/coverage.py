#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
coverage.py - V2 (docs/investigacion-ports.md §4.4): que parte del C del port
NO corre nunca bajo el verificador. P69: "lo que el oraculo no recorre puede
estar mal aunque todo de 100 %".

Compila marioverify con --coverage (gcc, en work/cov/), lo corre con TODAS
las grabaciones (work/oracle_yi1.bin y cada work/oracle_*.txt, pasadas a
.bin como en regress.py) en los modos de regress.py, junta los contadores
con gcov y escribe docs/cobertura.md: por fichero, las funciones que no
corren nunca y las que corren a medias (con los tramos de lineas sin
ejecutar). Lo que hay despues de "## Notas (a mano)" en ese fichero se
conserva al regenerarlo.

    python3 tools/coverage.py                 # todo, escribe docs/cobertura.md
    python3 tools/coverage.py --no-write      # solo el resumen por pantalla

"Ejecutado" no es "verificado": una linea cuenta si corrio con el
verificador comparando, aunque ese frame haya dado distinto. Lo que da 0
es seguro que ninguna grabacion lo comprueba.
"""
import argparse
import glob
import gzip
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import regress  # noqa: E402

COV = os.path.join(ROOT, "work", "cov")
EXE = os.path.join(COV, "mv" + (".exe" if os.name == "nt" else ""))
DOC = os.path.join(ROOT, "docs", "cobertura.md")
NOTES = "## Notas (a mano)"
YI1_MODES = ["", "full", "gfx", "loop", "sprload", "sprloop", "game"]
ORC_MODES = ["full", "gfx", "loop", "game", "sprload"]


def sh(cmd, **kw):
    p = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kw)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def build():
    if os.path.isdir(COV):
        shutil.rmtree(COV)
    os.makedirs(COV)
    cc = shutil.which("gcc") or shutil.which("cc")
    objs = []
    for src in regress.CSRC:
        o = os.path.join(COV, os.path.splitext(os.path.basename(src))[0] + ".o")
        cov = src.startswith("player/") and "/gen/" not in src
        code, out = sh([cc, "-O0" if cov else "-O2"] + (["--coverage"] if cov else [])
                       + ["-Iplayer", "-c", src, "-o", o])
        if code:
            sys.exit("coverage: no compila %s:\n%s" % (src, out[-1500:]))
        objs.append(o)
    code, out = sh([cc, "--coverage", "-o", EXE] + objs)
    if code:
        sys.exit("coverage: no enlaza:\n" + out[-1500:])


def recordings():
    """[(nombre, .bin)] de todas las grabaciones"""
    out = [("yi1", os.path.join(ROOT, "work", "oracle_yi1.bin"))]
    for txt in sorted(glob.glob(os.path.join(ROOT, "work", "oracle_*.txt"))):
        n = os.path.basename(txt)[len("oracle_"):-len(".txt")]
        if n == "yi1":
            continue
        binf = txt[:-4] + ".bin"
        if not os.path.exists(binf) or os.path.getmtime(txt) > os.path.getmtime(binf):
            code, _ = sh([sys.executable, "tools/oracle2bin.py", "--inp", txt, "--out", binf])
            if code:
                continue
        out.append((n, binf))
    return out


def run_all():
    runs = []
    for n, binf in recordings():
        for mode in (YI1_MODES if n == "yi1" else ORC_MODES):
            code, _ = sh([EXE, binf] + ([mode] if mode else []), timeout=600)
            runs.append((n, mode or "8a", code))
    return runs


def gcov():
    """{fichero: {"functions": [...], "lines": {n: count}}}"""
    res = {}
    for src in regress.CSRC:
        if not src.startswith("player/") or "/gen/" in src:
            continue
        o = os.path.join(COV, os.path.splitext(os.path.basename(src))[0] + ".o")
        p = subprocess.run(["gcov", "--json-format", "--stdout", "-b", "-o", COV, src], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        for line in p.stdout.decode("utf-8", "replace").splitlines():
            if not line.strip().startswith("{"):
                continue
            d = json.loads(line)
            for f in d["files"]:
                fn = f["file"].replace("\\", "/")
                if not fn.endswith(os.path.basename(src)):
                    continue
                lines = {}
                br = [0, 0]
                for ln in f["lines"]:
                    lines[ln["line_number"]] = max(lines.get(ln["line_number"], 0), ln["count"])
                    for b in ln.get("branches", []):
                        br[1] += 1
                        br[0] += 1 if b["count"] else 0
                res[src] = {"functions": f["functions"], "lines": lines, "branches": br}
    return res


def ranges(nums):
    out, start, prev = [], None, None
    for n in sorted(nums):
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append((start, prev))
            start = prev = n
    if start is not None:
        out.append((start, prev))
    return out


def snes_label(src, line):
    """la rutina de SMW que cita el comentario de arriba de la funcion"""
    try:
        text = open(os.path.join(ROOT, src), encoding="latin-1").read().split("\n")
    except OSError:
        return ""
    for k in range(line - 1, max(0, line - 12), -1):
        m = re.search(r"\b(CODE_[0-9A-F]{6}|_0[0-9A-F]{5}|DATA_[0-9A-F]{6}|[A-Z][A-Za-z]+(?:Bnk\d)?)\b",
                      text[k - 1]) if text[k - 1].lstrip().startswith(("/*", "*", "//")) else None
        if m and m.group(1).startswith(("CODE_", "_0")):
            return m.group(1)
    return ""


def report(cov, runs):
    L = []
    tot_l = tot_e = tot_f = tot_fe = 0
    rows = []
    for src, d in sorted(cov.items()):
        lines = d["lines"]
        ex = sum(1 for c in lines.values() if c)
        fs = d["functions"]
        fe = sum(1 for f in fs if f["execution_count"])
        tot_l += len(lines)
        tot_e += ex
        tot_f += len(fs)
        tot_fe += fe
        br = d["branches"]
        rows.append("| `%s` | %d/%d | %d/%d (%.0f %%) | %s |" % (
            src, fe, len(fs), ex, len(lines), 100.0 * ex / max(1, len(lines)),
            "%d/%d (%.0f %%)" % (br[0], br[1], 100.0 * br[0] / br[1]) if br[1] else "-"))
    ok = sum(1 for r in runs if r[2] == 0)
    names = sorted({r[0] for r in runs})
    L.append("# Cobertura del C del port bajo el verificador (V2)")
    L.append("")
    L.append("> Generado por `tools/coverage.py` (no editar a mano salvo la sección "
             "\"Notas (a mano)\" del final, que se conserva). Qué es y por qué: "
             "`docs/investigacion-ports.md` §4.4 y P69.")
    L.append("")
    L.append("**Corridas:** %d de %d terminaron bien (%d grabaciones: %s). Una línea "
             "cuenta como ejecutada si corrió bajo `marioverify` con cualquiera de ellas."
             % (ok, len(runs), len(names), ", ".join(names)))
    bad = ["%s %s (%d)" % r for r in runs if r[2]]
    if bad:
        L.append("")
        L.append("Corridas que salieron con error (también cuentan lo que ejecutaron): " + ", ".join(bad))
    L.append("")
    L.append("## Resumen por fichero")
    L.append("")
    L.append("| fichero | funciones ejecutadas | líneas ejecutadas | ramas tomadas |")
    L.append("|---|---|---|---|")
    L += rows
    L.append("| **total** | %d/%d | %d/%d (%.0f %%) | |" % (tot_fe, tot_f, tot_e, tot_l, 100.0 * tot_e / max(1, tot_l)))
    L.append("")
    L.append("## Funciones que no corren nunca")
    L.append("")
    L.append("Ninguna grabación las comprueba: pueden estar mal sin que `regress.py` lo vea.")
    L.append("")
    L.append("| fichero | función | líneas | rutina de SMW |")
    L.append("|---|---|---|---|")
    for src, d in sorted(cov.items()):
        for f in sorted(d["functions"], key=lambda f: f["start_line"]):
            if f["execution_count"]:
                continue
            L.append("| `%s` | `%s` (l. %d) | %d | %s |" % (
                src, f["name"], f["start_line"], f["end_line"] - f["start_line"] + 1,
                snes_label(src, f["start_line"]) or "-"))
    L.append("")
    L.append("## Funciones que corren a medias")
    L.append("")
    L.append("Las que tienen líneas sin ejecutar, de más a menos. Los tramos son líneas "
             "del fuente (solo las que tienen código).")
    L.append("")
    L.append("| fichero | función | sin ejecutar / con código | tramos sin ejecutar |")
    L.append("|---|---|---|---|")
    part = []
    for src, d in cov.items():
        for f in d["functions"]:
            if not f["execution_count"]:
                continue
            ls = [n for n, c in d["lines"].items() if f["start_line"] <= n <= f["end_line"]]
            miss = [n for n in ls if not d["lines"][n]]
            if miss:
                part.append((len(miss), src, f, len(ls), miss))
    for nmiss, src, f, nl, miss in sorted(part, key=lambda x: (-x[0], x[1], x[2]["start_line"])):
        rs = ", ".join("%d" % a if a == b else "%d-%d" % (a, b) for a, b in ranges(miss))
        L.append("| `%s` | `%s` | %d / %d | %s |" % (src, f["name"], nmiss, nl, rs))
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    if not shutil.which("gcov"):
        sys.exit("coverage: no hay gcov (en Windows: /c/msys64/ucrt64/bin primero en el PATH, P82)")
    build()
    runs = run_all()
    cov = gcov()
    L = report(cov, runs)
    tl = sum(len(d["lines"]) for d in cov.values())
    te = sum(1 for d in cov.values() for c in d["lines"].values() if c)
    print("coverage: %d corridas, lineas ejecutadas %d/%d (%.1f %%)" % (len(runs), te, tl, 100.0 * te / max(1, tl)))
    if a.no_write:
        return 0
    notes = "%s\n\n(vacío)\n" % NOTES
    if os.path.exists(DOC):
        old = open(DOC, encoding="utf-8").read()
        if NOTES in old:
            notes = old[old.index(NOTES):]
    with open(DOC, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n\n" + notes)
    print("coverage: escrito " + os.path.relpath(DOC, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
