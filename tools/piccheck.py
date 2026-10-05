#!/usr/bin/env python3
"""Rechaza jsr/jmp que vasm relajo a absoluta (P102).

El binario se carga fuera de la base del ensamblado. Un opcode 4EB8/4EF8
o 4EB9/4EF9 (absoluto corto/largo)
pierde esa base; las llamadas por registros (a6/a0) y las relativas al PC
siguen siendo validas. Usa el listado REAL ensamblado, sin confiar en nombres.
"""
import argparse
import re
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--lst", required=True)
    a = ap.parse_args()
    bad = []
    instructions = 0
    rx = re.compile(r"^[0-9a-f]+:([0-9a-f]+)\s+([0-9a-f]+)\s+.*?:\s*(.*)", re.I)
    for line in open(a.lst, encoding="utf-8", errors="replace"):
        m = rx.search(line)
        if m:
            adr, opcode, source = m.groups()
            source = re.sub(r"^[\w.]+:\s*", "", source).strip()
            mnemonic = source.split()[0].lower() if source else ""
            # Los mismos bytes pueden venir de datos: no son instrucciones.
            if not mnemonic or mnemonic.startswith(("dc.", "dcb.", "ds.")) or mnemonic in ("incbin", "cnop", "even", "align"):
                continue
            instructions += 1
            # Mirar el opcode tambien cubre BRA/BSR relajados por vasm, y el
            # nombre del destino (simbolo, numero, macro) no autoriza absolutas.
            if opcode[:4].upper() in ("4EB8", "4EB9", "4EF8", "4EF9"):
                bad.append("$%s: %s (%s)" % (adr, opcode, source))
    for text in bad:
        print("ERROR PIC: " + text)
    print("PIC: %d instrucciones, %d llamadas/saltos absolutos" % (instructions, len(bad)))
    if not instructions:
        print("ERROR PIC: listado vacio o sin instrucciones reconocibles")
    return bool(bad) or not instructions


if __name__ == "__main__":
    sys.exit(main())
