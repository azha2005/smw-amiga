#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
asmlint_port.py - V3 (docs/investigacion-ports.md §6.4): compara la cabecera
de cada rutina asm con lo que la rutina hace con los registros. La clase de
bug de P53 (mspr_draw destruia d2 sin decirlo).

El motor es el asmlint de AmiGalaga (github.com/mwulffn/AmiGalaga, commit
be410ba, asmlint/src/asmlint; MIT, ver tools/asmlint/LICENSE). Un solo
cambio, marcado "port-amiga" en graph.py: "x set n" / "x equ n" no abre
un ambito de etiquetas locales (como en vasm). Este script le da la entrada en su formato, con los
numeros de linea originales:

- Nuestras cabeceras (AGENTS.md §7):
      ; --- nombre ---
      ; entrada:  ...
      ; salida:   ...
      ; registros destruidos: d0-d3/a0
  pasan a las suyas (In / Out / Clobbers). Esas rutinas SE COMPRUEBAN: un
  registro que la rutina puede cambiar y que no esta en "salida" ni en
  "registros destruidos" es un error; uno listado que nunca cambia, un
  aviso.
- Una rutina `public _xxx` sin cabecera la llama el C: se comprueba contra
  la ABI de vbcc (salida d0; destruye d0-d1/a0-a1; el resto se preserva).
- Las llamadas al C (`jsr _xxx`), a exec (`jsr _LVOxxx(a6)`) y las
  indirectas (`jsr (a0)`) se toman como llamadas con esa ABI.
- Las rutinas sin cabecera NO se comprueban: lo que tocan se infiere
  (se empieza por "todos" y se itera con los avisos del motor hasta que no
  cambia), para que quien las llama herede algo realista.

No se siguen los includes de work/ (el C compilado por vbcc) ni de los
otros .s del juego (cada uno es una unidad aparte; las llamadas entre
ficheros se resuelven igual).

    python3 tools/asmlint_port.py            # los .s del juego
    python3 tools/asmlint_port.py --all      # tambien las rutinas inferidas
    python3 tools/asmlint_port.py player/x.s ...

Sale con 1 si hay errores en rutinas con cabecera (o de la ABI).
"""
import argparse
import os
import re
import sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

from asmlint import linter, reader  # noqa: E402
from asmlint.directives import DATA, OTHER  # noqa: E402
from asmlint.findings import ERROR, WARNING  # noqa: E402
from asmlint.registers import LIST_PATTERN, REGISTERS  # noqa: E402
from asmlint.source import is_local, parse_statement  # noqa: E402

FILES = ["player/game.s", "player/scroll.s", "player/logic68k.s", "player/mspr68k.s"]
ABI_OUT, ABI_CLOB = "d0", "d0-d1/a0-a1"
ALL = "d0-d7/a0-a6"

_HDR = re.compile(r"^;\s*---\s*([A-Za-z_][\w]*)\s*---")
_FIELD = re.compile(r"^\s*(entrada|salida|registros destruidos)\s*:(.*)$", re.IGNORECASE)
_LIST = re.compile(r"(?<![\w$])" + LIST_PATTERN + r"(?![\w$])", re.IGNORECASE)
_INDIRECT = re.compile(r"\(\s*a[0-7]\s*[,)]", re.IGNORECASE)

# nombre de rutina -> (tipo, fichero, linea): "header" (nuestra), "abi"
# (public _xxx), "inferred" (sin cabecera: no se comprueba)
KIND = {}
# lo que se supone que destruyen las rutinas inferidas (se va ajustando)
GUESS = {}


def reglist(text):
    """las listas de registros que aparecen en un texto, unidas con /"""
    found = _LIST.findall(text)
    return "/".join(found)


def our_headers(stmts):
    """{indice de la etiqueta: (nombre, entrada, salida, destruidos o None)}"""
    out = {}
    i = 0
    while i < len(stmts):
        m = _HDR.match(stmts[i].text.strip())
        if not m:
            i += 1
            continue
        name = m.group(1)
        fields, cur = {}, None
        j = i + 1
        while j < len(stmts) and stmts[j].is_comment:
            c = stmts[j].comment
            f = _FIELD.match(c)
            if f:
                cur = f.group(1).lower()
                fields[cur] = f.group(2).strip()
            elif cur and re.match(r"\s{2,}\S", c):
                fields[cur] += " " + c.strip()
            else:
                cur = None
            j += 1
        while j < len(stmts) and not stmts[j].label and not stmts[j].mnemonic:
            j += 1                                  # lineas en blanco
        if j < len(stmts) and stmts[j].label == name:
            out[j] = (name, fields.get("entrada", ""), fields.get("salida", ""),
                      fields.get("registros destruidos"))
        i = j
    return out


def is_code_label(stmts, i):
    """la etiqueta global de stmts[i] empieza codigo (no datos ni equ)"""
    s = stmts[i]
    if not s.label or is_local(s.label):
        return False
    if s.mnemonic in ("equ", "=", "set", "equr", "reg", "macro", "rs", "so", "fo"):
        return False
    for t in stmts[i:i + 40]:
        if t.mnemonic is None or t.mnemonic in OTHER:
            if t is not s and t.label and not is_local(t.label):
                return False                        # otra etiqueta antes de codigo
            continue
        return t.mnemonic not in DATA
    return False


def convert(path, lines):
    """las lineas del fichero con las cabeceras en el formato del motor;
    devuelve [(numero de linea original, texto)]"""
    stmts = [parse_statement(str(path), n + 1, t) for n, t in enumerate(lines)]
    inmac, m = set(), False                         # cuerpos de macro: no se tocan
    for j, t in enumerate(stmts):
        if t.mnemonic == "macro":
            m = True
        elif t.mnemonic == "endm":
            m = False
        elif m:
            inmac.add(j)
    for j in inmac:                                 # para el resto, como lineas vacias
        stmts[j] = parse_statement(str(path), j + 1, "")
    ours = our_headers(stmts)
    publics = {op for s in stmts if s.mnemonic in ("public", "xdef", "global")
               for op in s.operands}
    # como se nombra cada etiqueta: "call" (bsr/jsr), "branch" (bra/bcc/jmp/
    # dbcc) u "other" (lea, move, dc.l...). Una a la que solo se salta es
    # parte de la rutina que la contiene (bm_left en build_mid): sin cabecera
    refs = {}                                       # etiqueta -> [(indice, tipo)]
    for j, t in enumerate(stmts):
        if not t.mnemonic or t.mnemonic in OTHER:
            continue
        kind = ("call" if t.mnemonic in ("bsr", "jsr") else
                "branch" if t.mnemonic in ("jmp",) or (t.mnemonic.startswith("b") and t.mnemonic not in ("btst", "bset", "bclr", "bchg"))
                or t.mnemonic.startswith("db") else "other")
        for op in t.operands:
            for w in re.findall(r"[A-Za-z_][\w]*", op):
                refs.setdefault(w, []).append((j, kind))
    code = [i for i in range(len(stmts)) if is_code_label(stmts, i)]
    # con cabecera seguro: las nuestras, las public, y las que se llaman,
    # se nombran por direccion o nadie nombra (puntos de entrada)
    sure = {i for i in code if i in ours or stmts[i].label in publics
            or any(k != "branch" for _, k in refs.get(stmts[i].label, []))
            or not refs.get(stmts[i].label)}

    def same_region(a, b):
        """a y b quedan bajo la misma cabecera (ninguna en medio)"""
        lo, hi = min(a, b), max(a, b)
        return not any(lo < k <= hi for k in sure)

    headed = set(sure)
    for i in code:
        if i not in sure and not all(same_region(j, i) for j, _ in refs[stmts[i].label]):
            headed.add(i)
    first_code = next((j for j, t in enumerate(stmts) if t.mnemonic and t.mnemonic not in OTHER
                       and t.mnemonic not in DATA and not t.mnemonic.startswith("if")
                       and t.mnemonic not in ("else", "endc", "endif")), None)
    out = []
    for i, (s, text) in enumerate(zip(stmts, lines)):
        n = i + 1
        if i == first_code and not any(k <= i for k in headed):
            name = "inicio_" + os.path.basename(str(path)).replace(".", "_")
            KIND.setdefault(name, ("inferred", str(path), n))
            out += [(n, ";--"), (n, "; " + name), (n, "; In: -"), (n, "; Out: -"),
                    (n, "; Clobbers: " + GUESS.get(name, ALL).replace("/", ", "))]
        if i in headed:
            name = s.label
            if i in ours:
                _, ent, sal, clob = ours[i]
                if clob is None:
                    kind, outr, clobr = "inferred", "-", GUESS.get(name, ALL)
                else:
                    kind = "header"
                    outr = reglist(sal) or "-"
                    clobr = reglist(clob) or "-"
            elif name in publics and name.startswith("_"):
                kind, outr, clobr = "abi", ABI_OUT, ABI_CLOB
            else:
                kind, outr, clobr = "inferred", "-", GUESS.get(name, ALL)
            KIND.setdefault(name, (kind, str(path), n))
            out += [(n, ";--"), (n, "; " + name), (n, "; In: -"),
                    (n, "; Out: " + outr.replace("/", ", ") if outr != "-" else "; Out: -"),
                    (n, "; Clobbers: " + (clobr.replace("/", ", ") if clobr != "-" else "-"))]
        if s.mnemonic in ("jsr", "jmp") and s.operands and _INDIRECT.search(s.operands[0]) \
                and "lint:" not in s.comment:
            text = text + ("  " if ";" in text else "  ;") + " lint: clobbers " + ABI_CLOB
        elif s.mnemonic in ("bsr", "jsr") and s.operands and is_local(s.operands[0]) \
                and "lint:" not in s.comment:
            regs = local_writes(stmts, i, s.operands[0])
            text = text + ("  " if ";" in text else "  ;") + " lint: clobbers " + (regs or "-")
        out.append((n, text))
    return out


_NOWRITE = {"cmp", "cmpa", "cmpi", "cmpm", "tst", "btst", "bra", "bsr", "jsr", "jmp", "rts",
            "dbf", "dbra", "pea", "nop"}


def local_writes(stmts, i, target):
    """una subrutina local (`bsr .x`): los registros que escriben sus
    instrucciones desde la etiqueta hasta el primer rts (por exceso: el
    destino de cada instruccion, y los de un movem desde memoria)"""
    scope = None
    for k in range(i, -1, -1):                      # la etiqueta global de la llamada
        if stmts[k].label and not is_local(stmts[k].label) and stmts[k].mnemonic not in \
                ("=", "equ", "set", "equr", "reg"):
            scope = k
            break
    start = None
    for k in range((scope or 0) + 1, len(stmts)):
        lab = stmts[k].label
        if lab and not is_local(lab) and stmts[k].mnemonic not in ("=", "equ", "set", "equr", "reg"):
            break
        if lab == target:
            start = k
            break
    if start is None:
        return None
    found = set()
    for t in stmts[start:start + 200]:
        m = t.mnemonic
        if m is None:
            continue
        if m == "rts":
            break
        if m in _NOWRITE or m.startswith("b") or m.startswith("db") or not t.operands:
            continue
        if m == "movem":
            if "(" in t.operands[0]:
                found.update(_expand(reglist(t.operands[-1]) or "-"))
            continue
        if m == "exg":
            for o in t.operands:
                found.update(_expand(reglist(o) or "-"))
            continue
        dest = t.operands[-1].strip()
        if re.fullmatch(LIST_PATTERN, dest, re.IGNORECASE):
            found.update(_expand(dest.lower()))
        elif re.match(r"-?\(\s*a[0-7]\s*\)\+?$|^-\(", dest):        # (An)+ / -(An)
            found.update(_expand(re.search(r"a[0-7]", dest).group(0)))
        for o in t.operands[:-1]:
            if re.search(r"\(\s*a[0-7]\s*\)\+|-\(\s*a[0-7]\s*\)", o):
                found.add(re.search(r"a[0-7]", o).group(0))
    return "/".join(r for r in REGISTERS if r in found)


class PortReader(reader.Reader):
    def read_file(self, path):
        path = Path(path)
        rel = os.path.relpath(path.resolve(), ROOT).replace("\\", "/")
        if path.resolve() in self.files_read:
            return
        if rel.startswith("work/") or (self.files_read and rel.startswith("player/")
                                       and rel.endswith(".s")):
            return                                  # el C de vbcc / otra unidad
        self.files_read.add(path.resolve())
        lines = path.read_text(errors="replace").splitlines()
        it = iter(convert(path, lines))
        for number, text in it:
            st = parse_statement(str(path), number, text)
            if st.mnemonic == "end":
                break
            if st.mnemonic == "rem":
                self._skip(it, "erem", st, "rem has no erem")
            elif st.mnemonic == "macro":
                name = st.label or "".join(st.operands[:1])
                self.macros[name] = self._skip(it, "endm", st, "macro %s has no endm" % name)
            else:
                self._add(st, path.parent)


def read_source(path, include_dirs=()):
    r = PortReader(include_dirs)
    r.read_file(Path(path))
    return r.statements, r.findings


_orig_resolve = linter.resolve


def resolve(name, unit, units):
    r = _orig_resolve(name, unit, units)
    if isinstance(r, str) and name.startswith("_"):
        return set(REGISTERS[:2] + REGISTERS[8:10])    # el C / exec: d0-d1/a0-a1
    return r


linter.read_source = read_source
linter.resolve = resolve

_NEVER = re.compile(r"^(\S+) is listed under (?:Out|Clobbers) of (\S+) but is never changed")


def run(files):
    return linter.lint_files([Path(ROOT, f) for f in files], reserved=(), include_dirs=[Path(ROOT)])


def routine_at(path, line):
    """la rutina (por cabecera insertada) que contiene path:line"""
    best = None
    for name, (kind, p, n) in KIND.items():
        if os.path.normcase(os.path.abspath(p)) == os.path.normcase(os.path.abspath(path)) \
                and n <= line and (best is None or n > best[2]):
            best = (name, kind, n)
    return best


def check(files=FILES, inferred=False):
    """[(severidad "error"/"aviso", fichero relativo, linea, mensaje)] de las
    rutinas con cabecera y de la ABI (con inferred, tambien las inferidas)"""
    GUESS.clear()
    for _ in range(12):                 # lo que destruyen las rutinas sin cabecera
        KIND.clear()
        findings = run(files)
        never = {}
        for f in findings:
            m = _NEVER.match(f.message)
            if m and KIND.get(m.group(2), ("",))[0] == "inferred":
                never.setdefault(m.group(2), set()).add(m.group(1))
        changed = False
        for name, (kind, _, _) in KIND.items():
            if kind != "inferred":
                continue
            cur = GUESS.get(name, ALL)
            new = [r for r in REGISTERS[:15] if r in set(_expand(cur))
                   and r not in never.get(name, set())]
            g = "/".join(new) if new else "-"
            if g != cur:
                GUESS[name] = g
                changed = True
        if not changed:
            break
    out = []
    for f in findings:
        where = routine_at(f.file, f.line)
        kind = where[1] if where else "?"
        if kind == "inferred" and not inferred:
            continue
        rel = os.path.relpath(f.file, ROOT).replace("\\", "/")
        out.append(("error" if f.severity == ERROR else "aviso", rel, f.line,
                    f.message + (" [inferida]" if kind == "inferred" else "")))
    return out


def counts():
    return {k: sum(1 for v in KIND.values() if v[0] == k) for k in ("header", "abi", "inferred")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", default=FILES)
    ap.add_argument("--all", action="store_true", help="mostrar tambien lo de las rutinas inferidas")
    a = ap.parse_args()
    res = check(a.files, a.all)
    for sev, rel, line, msg in res:
        print("%s:%d: %s: %s" % (rel, line, sev, msg))
    n = counts()
    errs = sum(1 for r in res if r[0] == "error")
    print("asmlint_port: %d rutinas con cabecera, %d de la ABI (public _xxx), %d sin cabecera "
          "(no se comprueban); %d errores, %d avisos" % (n["header"], n["abi"], n["inferred"],
                                                         errs, len(res) - errs))
    return 1 if errs else 0


def _expand(text):
    if text == "-":
        return []
    from asmlint.registers import parse_list
    out = []
    for part in text.split("/"):
        out += parse_list(part) or []
    return out


if __name__ == "__main__":
    sys.exit(main())
