#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memmap.py - el mapa de memoria del juego, comprobado (Etapa 6b.1, D13).

A partir del listado de vasm (-L: work/game.lst o work/live/game.lst), de
la tabla del loader (la cabecera A5PL del ADF que escribe mkadf.py) y cabecera
de work/yi1_s.dat saca:

  * cada AllocMem del arranque (tamano y memoria que pide: la expresion de
    d0 y de d1 evaluada con los simbolos del listado) y a que bloque
    pertenece (PF1, listas del copper, sprites, diagnostico, datos del
    scroll...); dentro de los bloques que tienen partes (yi1_s.dat, el
    diagnostico, los buffers de sprites) cada parte con su desplazamiento;
  * TODO lo que lee el chipset (planos, copper, sprites, audio, fuente y
    destino del blitter) tiene que estar en chip RAM (< $80000): pedido con
    MEMF_CHIP, y ningun puntero de chipset que salga de datos del binario (el
    binario se copia a la slow RAM y ahi el chipset no llega);
  * alineaciones: planos y bloques de sprites a 8 bytes, listas del copper a
    4, audio a 2 (lo que pide el OCS es palabra; 8 / 4 son las reglas del
    proyecto, AGENTS.md §7); modulos y pasos de fila pares;
  * el total de chip <= 512 KB ($80000) y el de slow <= 512 KB, con la tabla
    por bloque como la de AGENTS.md §4;
  * el loader: la longitud de stage2 y de los datos que escribio mkadf.py
    contra lo que el binario libera (FreeMem) y reserva (hdr_data_len).

    python tools/memmap.py                      # work/game.lst
    python tools/memmap.py work/live/game.lst   # el juego en vivo
    python tools/memmap.py --selftest           # una violacion de cada tipo

Sale con 0 si no hay violaciones y con 1 si las hay.

Limites (dicho claro): las direcciones de AllocMem se deciden al arrancar; lo
que se comprueba es lo que el codigo pide, no donde cae. La auditoria de
punteros de chipset es una heuristica sobre el listado (mira de donde salio el
registro que se escribe en BLTxPT / COPxLC / BPLxPT / SPRxPT / AUDxLC / DSKPT)
y no sigue datos que viajan por la memoria. Los chequeos de la maquina real
(que $C00000 responda, P8) estan en game.s bajo -DMEMCHK.
"""
import argparse
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))

CHIP_TOP = 0x80000          # 512 KB de chip: $000000-$07FFFF
SLOW_TOP = 0x80000          # 512 KB de slow: $C00000-$C7FFFF
SECTOR = 512
MEMF_CHIP, MEMF_FAST = 2, 4
ALLOC_ALIGN = 8             # exec: MEM_BLOCKSIZE (KS 1.2 y posteriores)

# registros de puntero del chipset (nombres de custom.i / scroll.s)
PTR_REG = re.compile(r"^(BLT[ABCD]PT[HLR]?|COP[12]LC[HL]?|BPL\dPT[HL]?|SPR\dPT[HL]?"
                     r"|AUD\dLC[HL]?|DSKPT[HL]?)$")

# cabecera de yi1_s.dat (mkscroll.py): simbolo del listado -> (nombre, rol, alineacion)
DATA_SECS = {
    "D_BLK": ("BLK", "blit", 8),        # bloques 16x16: fuente del blitter
    "D_MAP": ("MAP", "cpu", 2),
    "D_INI": ("INI", "cpu", 2),
    "D_CHG": ("CHG", "cpu", 2),
    "D_L2B": ("L2B", "plane", 8),       # capa 2: planos de DMA
    "D_L2P": ("L2P", "cpu", 2),
    "D_MLX": ("MLX", "cpu", 2),
    "D_MLD": ("MLD", "cpu", 2),
    "D_LNS": ("LNS", "cpu", 2),
}


def align(n, a):
    return (n + a - 1) // a * a


# --------------------------------------------------------------------------
# el listado de vasm
# --------------------------------------------------------------------------
CODE_RX = re.compile(r"^(\d\d):([0-9A-F]{8}) ([0-9A-F ]*?)\s*\t\s*(\d+): ?(.*)$")
SYM_RX = re.compile(r"^(\S+)\s+(E:|\d\d:)([0-9A-F]{8})")


class Listing:
    """lineas de codigo con direccion y la tabla de simbolos"""

    def __init__(self, text):
        self.code = []          # (addr, etiqueta, instruccion, operandos, fuente)
        self.equ = {}           # nombre -> valor (con signo si pasa de $7FFFFFFF)
        self.label = {}         # nombre -> direccion
        self.size = None        # tamano de la seccion
        in_sym = False
        for ln in text.splitlines():
            if ln.startswith("Symbols by name"):
                in_sym = True
                continue
            if ln.startswith("Symbols by value"):
                in_sym = False
                continue
            m = re.match(r'^\d\d: ".*" \(0-([0-9A-F]+)\)', ln)
            if m and self.size is None:
                self.size = int(m.group(1), 16)
                continue
            if in_sym:
                m = SYM_RX.match(ln)
                if m:
                    v = int(m.group(3), 16)
                    if m.group(2) == "E:":
                        self.equ[m.group(1)] = v - (1 << 32) if v >= 0x80000000 else v
                    else:
                        self.label[m.group(1)] = v
                continue
            m = CODE_RX.match(ln)
            if m:
                src = m.group(5).split(";")[0].rstrip()
                lab = ""
                mm = re.match(r"^([A-Za-z_.][\w.$@]*):?(?=\s|$)", src) if src[:1] not in " \t" else None
                if mm:
                    lab = mm.group(1)
                    src = src[mm.end():]
                src = src.strip()
                if src and not src.startswith("*"):
                    parts = src.split(None, 1)
                    self.code.append((int(m.group(2), 16), lab, parts[0].lower(),
                                      parts[1].strip() if len(parts) > 1 else "", src))

    def sym(self, name):
        if name in self.equ:
            return self.equ[name]
        if name in self.label:
            return self.label[name]
        raise KeyError(name)

    def has(self, name):
        return name in self.equ or name in self.label

    def ev(self, expr):
        """evalua una expresion de vasm (+ - * / & | << >> ( ) $hex %bin)"""
        e = expr.strip()
        if e.startswith("#"):
            e = e[1:]

        def name(m):
            n = m.group(0)
            if n in self.equ:
                return str(self.equ[n])
            if n in self.label:
                return str(self.label[n])
            raise KeyError(n)
        e = re.sub(r"\$([0-9A-Fa-f]+)", lambda m: str(int(m.group(1), 16)), e)
        e = re.sub(r"%([01]+)", lambda m: str(int(m.group(1), 2)), e)
        e = re.sub(r"[A-Za-z_.][\w.]*", name, e)
        e = e.replace("/", "//")
        if not re.fullmatch(r"[\d\s+\-*/&|^~()<>]*", e):
            raise ValueError(expr)
        return int(eval(e, {"__builtins__": {}}, {}))      # noqa: S307 (solo digitos y operadores)

    def is_label_expr(self, expr):
        """la expresion nombra una etiqueta del binario (no un equ)"""
        for n in re.findall(r"[A-Za-z_.][\w.]*", expr.lstrip("#")):
            if n in self.equ:
                continue
            if n in self.label or n.startswith("."):
                return n
        return None


# --------------------------------------------------------------------------
# el modelo
# --------------------------------------------------------------------------
class Sub:
    def __init__(self, name, off, size, role, align_req):
        self.name, self.off, self.size, self.role, self.align = name, off, size, role, align_req


class Block:
    def __init__(self, name, mem, size, kind, flags=None, subs=None, note=""):
        self.name, self.mem, self.size, self.kind = name, mem, size, kind
        self.flags = flags
        self.subs = subs or []
        self.note = note

    @property
    def alloc(self):
        return align(self.size, ALLOC_ALIGN)


class Model:
    def __init__(self):
        self.blocks = []
        self.viol = []          # (codigo, texto)
        self.warn = []
        self.info = []
        self.ptr_writes = []    # (addr, registro, origen, veredicto)

    def v(self, code, text):
        self.viol.append((code, text))


def find_allocs(L):
    """cada jsr _LVOAllocMem: (addr, d0, d1, destino)"""
    out = []
    code = L.code
    for i, (addr, lab, ins, ops, src) in enumerate(code):
        if ins != "jsr" or not re.match(r"_LVO(AllocMem|FreeMem)\(a6\)", ops):
            continue
        d0 = d1 = None
        for j in range(i - 1, max(i - 14, -1), -1):
            _, _, ins2, ops2, _ = code[j]
            m = re.match(r"(.+),(d0|d1)$", ops2)
            if ins2 in ("move.l", "moveq", "move.w") and m:
                if m.group(2) == "d0" and d0 is None:
                    d0 = m.group(1).strip()
                if m.group(2) == "d1" and d1 is None:
                    d1 = m.group(1).strip()
            if d0 is not None and d1 is not None:
                break
        dest = None
        for j in range(i + 1, min(i + 9, len(code))):
            _, _, ins2, ops2, _ = code[j]
            if ins2 in ("jsr", "bsr", "bra", "rts") or re.search(r",d0$", ops2):
                break                       # el siguiente AllocMem / otra cosa en d0
            m = re.match(r"d0,(\w+)\(a5\)$", ops2)
            if ins2 == "move.l" and m:
                dest = m.group(1)
                break
            if ins2 == "lea":
                mm = re.match(r"(\w+)\(pc\),a(\d)$", ops2)
                if mm:
                    nxt = code[j + 1][3] if j + 1 < len(code) else ""
                    if re.match(r"d0,\(a%s\)\+?$" % mm.group(2), nxt):
                        dest = mm.group(1)
                        break
        out.append((addr, ops, d0, d1, dest))
    return out


def audit_pointers(L, m):
    """escrituras en registros de puntero del chipset: ninguna puede salir
    de una direccion del binario"""
    code = L.code

    def writer(reg, i, depth=0):
        """de donde sale el valor de `reg` antes de la instruccion i:
        devuelve (None | texto de la etiqueta del binario, descripcion)"""
        for j in range(i - 1, max(i - 12, -1), -1):
            _, lab, ins, ops, src = code[j]
            mm = re.match(r"(.+),(\w+)$", ops)
            if not mm or mm.group(2) != reg:
                continue
            s = mm.group(1).strip()
            if ins == "lea":
                lb = re.match(r"(\w+)\(pc\)$", s) or re.match(r"(\w[\w.]*)$", s)
                if lb and (L.has(lb.group(1)) and lb.group(1) in L.label or lb.group(1).startswith(".")):
                    return lb.group(1), src
                return None, src
            if ins in ("move.l", "moveq", "move.w"):
                if s.startswith("#"):
                    n = L.is_label_expr(s)
                    return (n, src) if n else (None, src)
                if re.fullmatch(r"[ad]\d", s) and depth < 3:
                    return writer(s, j, depth + 1)
                return None, src
            if ins in ("add.l", "sub.l", "add.w", "adda.l", "adda.w") and s.startswith("#"):
                n = L.is_label_expr(s)
                if n:
                    return n, src
                continue                    # sumar un equ: sigue mirando
            if ins in ("add.l", "adda.l", "sub.l"):
                continue                    # sumar un registro o (An): sigue
            if ins in ("clr.l", "swap", "ext.l", "lsl.l", "lsr.l", "mulu", "divu"):
                continue
            return None, src
        return None, "?"

    for i, (addr, lab, ins, ops, src) in enumerate(code):
        if ins not in ("move.l", "move.w", "lea"):
            continue
        mm = re.match(r"(.+),(\w+)\(a4\)$", ops)
        if not mm or not PTR_REG.match(mm.group(2)):
            continue
        s, reg = mm.group(1).strip(), mm.group(2)
        bad = None
        if s.startswith("#"):
            bad = L.is_label_expr(s)
            how = s
        elif re.fullmatch(r"[ad]\d", s):
            bad, how = writer(s, i)
        else:
            how = s
        m.ptr_writes.append((addr, reg, how.strip(), bad))
        if bad:
            m.v("V-STATIC", "$%06X: %s <- %s: el puntero sale de '%s', una etiqueta del binario "
                "(que va a la slow RAM): lo que lee el chipset tiene que estar en chip"
                % (addr, reg, how.strip(), bad))


def check_strides(L, m):
    """modulos y pasos de fila del chipset: pares (el bit 0 del modulo se
    ignora y un puntero impar no existe)"""
    need = {}
    for k in ("ROWB1", "ROWB2", "LINEB1", "LINEB2", "FETCHW", "SLOTS"):
        if L.has(k):
            need[k] = L.sym(k)
    if "LINEB1" in need and "FETCHW" in need:
        need["BPL1MOD"] = need["LINEB1"] - need["FETCHW"] * 2
    if "LINEB2" in need and "FETCHW" in need:
        need["BPL2MOD"] = need["LINEB2"] - need["FETCHW"] * 2
    if "DG_STRIPB" in need or L.has("DG_STRIPB"):
        need["DG_STRIPB"] = L.sym("DG_STRIPB")
    for k in ("ROWB1", "LINEB1", "ROWB2", "LINEB2"):
        if k in need and need[k] % 2:
            m.v("V-STRIDE", "%s = %d es impar: los planos tienen que avanzar de a palabras" % (k, need[k]))
    for k in ("BPL1MOD", "BPL2MOD", "DG_STRIPB"):
        if k in need and need[k] % 2:
            m.v("V-STRIDE", "%s = %d es impar (modulo del chipset)" % (k, need[k]))
    if "ROWB1" in need and "SLOTS" in need and need["ROWB1"] != need["SLOTS"] * 4:
        m.warn.append("ROWB1 (%d) != SLOTS*4 (%d)" % (need["ROWB1"], need["SLOTS"] * 4))
    if "BUF1" in L.equ and "LINEB1" in need and L.has("LINES"):
        if L.sym("BUF1") != need["LINEB1"] * L.sym("LINES"):
            m.v("V-STRIDE", "BUF1 (%d) != LINEB1*LINES (%d)" % (L.sym("BUF1"), need["LINEB1"] * L.sym("LINES")))
    return need


def data_subblocks(L, data, m, total):
    """las partes de yi1_s.dat: cabecera (posiciones de D_* del listado)"""
    subs = []
    if data is None:
        m.warn.append("sin yi1_s.dat: no se desglosa el bloque de datos")
        return subs
    if data[:4] != b"SMWS":
        m.v("V-LOADER", "yi1_s.dat no empieza con 'SMWS'")
        return subs
    offs = []
    for sym, (nm, role, al) in DATA_SECS.items():
        if not L.has(sym):
            m.warn.append("el listado no define %s" % sym)
            continue
        pos = L.sym(sym)
        if pos + 4 > len(data):
            m.v("V-LOADER", "%s (%d) cae fuera de la cabecera de yi1_s.dat" % (sym, pos))
            continue
        off = struct.unpack_from(">I", data, pos)[0]
        offs.append((off, nm, role, al))
    offs.sort()
    for k, (off, nm, role, al) in enumerate(offs):
        end = offs[k + 1][0] if k + 1 < len(offs) else len(data)
        subs.append(Sub(nm, off, end - off, role, al))
    return subs


def build_model(L, data=None, adf=None, data_len=None):
    m = Model()
    if L.size is None or not L.has("binend") or not L.has("binstart"):
        m.v("V-PARSE", "el listado no tiene la seccion o binstart/binend: no es el de game.s")
        return m
    binlen = L.sym("binend") - L.sym("binstart")
    # ---- el loader: lo que escribio mkadf.py --------------------------------
    stage2_len = align(binlen, SECTOR)
    if adf is not None:
        ad = parse_adf(adf, m)
        if ad:
            if ad["stage2_len"] != stage2_len:
                m.v("V-LOADER", "el bootblock lee %d bytes de stage2 y el binario (binend-binstart = %d) "
                    "redondeado a sector son %d" % (ad["stage2_len"], binlen, stage2_len))
            stage2_len = ad["stage2_len"]
            if data is not None and ad["data_len"] != align(len(data), SECTOR):
                m.v("V-LOADER", "la cabecera A5PL dice %d bytes de datos y yi1_s.dat redondeado a sector "
                    "son %d (ADF viejo?)" % (ad["data_len"], align(len(data), SECTOR)))
            data_len = ad["data_len"]
    if data_len is None and data is not None:
        data_len = align(len(data), SECTOR)
    m.info.append("loader: stage2 %d B en chip (boot.s, se libera al copiarse a la slow), datos %s B"
                  % (stage2_len, data_len))

    # ---- los AllocMem --------------------------------------------------------
    allocs = find_allocs(L)
    seen_free = False
    for addr, ops, d0, d1, dest in allocs:
        if "FreeMem" in ops:
            if d0 is not None:
                try:
                    n = L.ev(d0) if d0.startswith("#") else None
                except (KeyError, ValueError):
                    n = None
                if n is not None and "binend" in d0 and n != stage2_len:
                    m.v("V-LOADER", "$%06X: FreeMem(%d) y boot.s reservo %d: la chip de stage2 "
                        "no se libera entera" % (addr, n, stage2_len))
                seen_free = True
            continue
        if d0 is None or d1 is None:
            m.v("V-PARSE", "$%06X: AllocMem sin tamano o requisitos reconocibles" % addr)
            continue
        try:
            if re.fullmatch(r"d\d", d0):
                if data_len is None:
                    m.v("V-PARSE", "$%06X: AllocMem de %s: hace falta --data o --adf" % (addr, d0))
                    continue
                size = data_len                          # d2 = hdr_data_len redondeado
            else:
                size = L.ev(d0)
            flags = L.ev(d1)
        except (KeyError, ValueError) as e:
            m.v("V-PARSE", "$%06X: no puedo evaluar '%s' / '%s' (%s)" % (addr, d0, d1, e))
            continue
        mem = "chip" if flags & MEMF_CHIP else ("slow" if flags & MEMF_FAST else "any")
        classify(L, m, addr, size, flags, mem, d0, dest, data)
    # ---- los bloques ---------------------------------------------------------
    for b in m.blocks:
        check_block(L, m, b)
    audit_pointers(L, m)
    check_strides(L, m)
    chip = sum(b.alloc for b in m.blocks if b.mem == "chip")
    slow = sum(b.alloc for b in m.blocks if b.mem != "chip")
    if chip > CHIP_TOP:
        m.v("V-CHIP-TOTAL", "chip: %d B > %d (512 KB)" % (chip, CHIP_TOP))
    if slow > SLOW_TOP:
        m.v("V-SLOW-TOTAL", "slow: %d B > %d (512 KB)" % (slow, SLOW_TOP))
    m.chip, m.slow, m.stage2_len = chip, slow, stage2_len
    if not any(b.mem != "chip" and "binario" in b.name for b in m.blocks):
        m.warn.append("no hay AllocMem(MEMF_FAST) del binario: se queda en chip (%d B)" % binlen)
    return m


def classify(L, m, addr, size, flags, mem, d0expr, dest, data):
    """pone nombre y partes a un AllocMem"""
    nm = dest or ""
    ex = d0expr
    if dest == "V_BUF1" or re.search(r"\bBUF1\b", ex):
        m.blocks.append(Block("PF1: buffer circular (V_BUF1)", mem, size, "plane", flags,
                              [Sub("PF1", 0, size, "plane", 8)]))
    elif dest in ("V_COP", "V_COP2") or "CL_SIZE" in ex:
        m.blocks.append(Block("lista del copper (%s)" % (dest or "?"), mem, size, "copper", flags,
                              [Sub("lista", 0, size, "copper", 4)]))
    elif dest == "g_spra" or "SPRBUF" in ex:
        sb = L.sym("SPRBUF") if L.has("SPRBUF") else size // 2
        m.blocks.append(Block("sprites de Mario (g_spra/g_sprb/g_null)", mem, size, "sprite", flags,
                              [Sub("g_spra", 0, sb, "sprite", 8), Sub("g_sprb", sb, sb, "sprite", 8),
                               Sub("g_null", 2 * sb, size - 2 * sb, "sprite", 8)]))
    elif dest == "g_dmem" or re.search(r"\bDG_SIZE\b", ex):
        subs = []
        if all(L.has(k) for k in ("DG_STRIP", "DG_ONES", "DG_COP")):
            page, strip, ones, cop = 0, L.sym("DG_STRIP"), L.sym("DG_ONES"), L.sym("DG_COP")
            if L.has("DG_PAGE"):
                page = L.sym("DG_PAGE")
            subs = [Sub("pagina 2 (1 plano)", page, strip - page, "plane", 8),
                    Sub("franja (2 planos)", strip, ones - strip, "plane", 8),
                    Sub("linea de $FF", ones, cop - ones, "plane", 8),
                    Sub("lista del copper de la pagina 2", cop, size - cop, "copper", 4)]
        m.blocks.append(Block("modo diagnostico (g_dmem)", mem, size, "diag", flags, subs))
    elif re.fullmatch(r"d\d", ex.strip()):
        m.blocks.append(Block("yi1_s.dat (datos del scroll)", mem, size, "data", flags,
                              data_subblocks(L, data, m, size)))
    elif "binend" in ex:
        m.blocks.append(Block("el binario (copia a la slow RAM)", mem, size, "binary", flags))
    elif re.search(r"aud|snd|samp|pcm", nm, re.I) or re.search(r"aud|snd|samp|pcm", ex, re.I):
        m.blocks.append(Block("audio (%s)" % (nm or ex), mem, size, "audio", flags,
                              [Sub("muestras", 0, size, "audio", 2)]))
    elif dest == "g_save" or mem == "any":
        m.blocks.append(Block("copia de los datos del C y del mapa (%s)" % (nm or "?"), "slow" if mem == "any"
                              else mem, size, "cpu", flags))
    else:
        # no se sabe quien lo lee: en chip se supone que el chipset
        m.blocks.append(Block("sin clasificar (%s)" % (nm or ex), mem, size,
                              "unknown", flags, [Sub("?", 0, size, "plane", 8)] if mem == "chip" else []))
        m.warn.append("$%06X: AllocMem '%s' sin clasificar; si es de chip se supone leido por el "
                      "chipset (alinear a 8)" % (addr, nm or ex))


def check_block(L, m, b):
    reads = [s for s in b.subs if s.role in ("plane", "copper", "sprite", "audio", "blit")]
    if b.kind in ("plane", "copper", "sprite", "audio", "diag") or any(
            s.role != "cpu" for s in b.subs):
        if b.mem != "chip":
            m.v("V-CHIP", "%s: el chipset lo lee y se pide en memoria '%s' (flags $%X): tiene que ser "
                "MEMF_CHIP" % (b.name, b.mem, b.flags))
    if b.kind == "binary" and b.mem == "chip":
        m.warn.append("el binario se queda en chip: con los bloques de chip no entra en 512 KB")
    for s in b.subs:
        if s.off % s.align:
            what = {"plane": "plano", "copper": "lista del copper", "sprite": "sprite",
                    "audio": "audio", "blit": "fuente del blitter", "cpu": "dato de la CPU"}.get(s.role, s.role)
            m.v("V-ALIGN", "%s / %s (%s): desplazamiento %d (0x%X) no es multiplo de %d"
                % (b.name, s.name, what, s.off, s.off, s.align))
        if s.role == "audio" and s.size % 2:
            m.v("V-ALIGN", "%s / %s: audio de %d bytes, Paula lee palabras (longitud par)"
                % (b.name, s.name, s.size))
        if s.role == "copper" and s.size % 4:
            m.v("V-ALIGN", "%s / %s: la lista del copper mide %d bytes, no multiplo de 4"
                % (b.name, s.name, s.size))
        if s.role == "plane" and s.size % 2:
            m.v("V-ALIGN", "%s / %s: plano de %d bytes (impar)" % (b.name, s.name, s.size))
    # el copper: tamanos de la lista que arma scroll.s
    if b.kind == "copper":
        for k in ("CL_SIZE", "CL_TAIL", "CL_LINES", "SEG"):
            if L.has(k) and L.sym(k) % 4:
                m.v("V-ALIGN", "%s = %d no es multiplo de 4 (lista del copper)" % (k, L.sym(k)))
    del reads


def parse_adf(adf, m):
    """la tabla del loader: bootblock + cabecera A5PL del stage2"""
    if len(adf) < 1024 + 14 or adf[:3] != b"DOS":
        m.v("V-LOADER", "el ADF no tiene bootblock DOS")
        return None
    s2len = struct.unpack_from(">I", adf, 8)[0]
    i = adf.find(b"A5PL", 1024, 1024 + 64)
    if i < 0:
        m.v("V-LOADER", "no hay cabecera A5PL en el stage2 del ADF")
        return None
    doff, dlen = struct.unpack_from(">II", adf, i + 4)
    if doff != 1024 + s2len:
        m.v("V-LOADER", "los datos empiezan en %d y stage2 acaba en %d" % (doff, 1024 + s2len))
    if doff + dlen > len(adf):
        m.v("V-LOADER", "los datos (%d + %d) pasan del final del ADF (%d)" % (doff, dlen, len(adf)))
    if s2len % SECTOR or dlen % SECTOR:
        m.v("V-LOADER", "stage2 (%d) o los datos (%d) no son multiplo de sector" % (s2len, dlen))
    return {"stage2_len": s2len, "data_off": doff, "data_len": dlen, "adf_len": len(adf)}


# --------------------------------------------------------------------------
# informe
# --------------------------------------------------------------------------
def fmt(n):
    return "{:,}".format(n).replace(",", " ")


def report(m, verbose=False, out=print):
    out("| donde | bloque | bytes | alin. | lo lee |")
    out("|---|---|---:|---:|---|")
    reads_of = {"plane": "chipset (planos)", "copper": "copper", "sprite": "sprites (DMA)",
                "audio": "Paula (DMA)", "blit": "blitter", "cpu": "solo CPU"}
    for b in m.blocks:
        who = sorted({reads_of.get(s.role, s.role) for s in b.subs if s.role != "cpu"})
        if not who:
            who = ["solo CPU"]
        out("| %s | %s | %s | %d | %s |" % (b.mem, b.name, fmt(b.size), ALLOC_ALIGN, ", ".join(who)))
        if b.subs and (verbose or b.kind in ("data", "diag", "sprite")):
            for s in b.subs:
                out("|   | .. %s @ +%d | %s | %d | %s |" % (s.name, s.off, fmt(s.size), s.align,
                                                             reads_of.get(s.role, s.role)))
    chip = [b for b in m.blocks if b.mem == "chip"]
    out("")
    out("chip : %s B (%.1f KB, %.1f%% de 512 KB; margen %s B)"
        % (fmt(m.chip), m.chip / 1000.0, 100.0 * m.chip / CHIP_TOP, fmt(CHIP_TOP - m.chip)))
    out("slow : %s B (%.1f KB, %.1f%% de 512 KB; margen %s B)"
        % (fmt(m.slow), m.slow / 1000.0, 100.0 * m.slow / SLOW_TOP, fmt(SLOW_TOP - m.slow)))
    cpu_only = sum(s.size for b in chip for s in b.subs if b.kind == "data" and s.role == "cpu")
    if cpu_only:
        out("en chip pero solo de la CPU (candidato a slow, ROADMAP 10.7): %s B" % fmt(cpu_only))
    out("sin la A501 el binario se queda en chip: %s B > 512 KB (D13: hace falta la expansion)"
        % fmt(m.chip + m.stage2_len) if m.chip + m.stage2_len > CHIP_TOP else
        "sin la A501 el binario se queda en chip: %s B (entra)" % fmt(m.chip + m.stage2_len))
    for t in m.info:
        out("info : " + t)
    if verbose:
        out("")
        out("escrituras en registros de puntero del chipset (%d):" % len(m.ptr_writes))
        for addr, reg, how, bad in m.ptr_writes:
            out("  $%06X  %-8s <- %-28s %s" % (addr, reg, how, "VIOLACION (%s)" % bad if bad
                                             else "sin rastrear (origen lejos)" if how == "?" else "ok"))
    for w in m.warn:
        out("AVISO: " + w)
    for code, t in m.viol:
        out("VIOLACION %s: %s" % (code, t))
    out("")
    out("memmap: %d violaciones" % len(m.viol))


# --------------------------------------------------------------------------
# autocomprobacion: un listado sintetico con una violacion de cada tipo
# --------------------------------------------------------------------------
SYN_CODE = """
entry:
        move.l  #binend-binstart,d0
        move.l  #MEMF_FAST,d1
        jsr     _LVOAllocMem(a6)
        tst.l   d0
        move.l  d2,d0
        move.l  #MEMF_CHIP,d1
        jsr     _LVOAllocMem(a6)
        move.l  #BUF1,d0
        move.l  #{BUFFL},d1
        jsr     _LVOAllocMem(a6)
        move.l  d0,V_BUF1(a5)
        move.l  #CL_SIZE+CL_TAIL,d0
        move.l  #MEMF_CHIP|MEMF_CLEAR,d1
        jsr     _LVOAllocMem(a6)
        move.l  d0,V_COP(a5)
        move.l  #{AUDSZ},d0
        move.l  #MEMF_CHIP,d1
        jsr     _LVOAllocMem(a6)
        lea     g_audio(pc),a0
        move.l  d0,(a0)
        move.l  #(binend-binstart+511)&-512,d0
        move.l  a1,a1
        jsr     _LVOFreeMem(a6)
{PTRCODE}
        rts
pfdata: dc.w    0
g_audio: dc.l   0
binend:
"""


def synth(buf_flags="MEMF_CHIP|MEMF_CLEAR", cl_size=0x1000, aud_size=2000, l2b=0x1000,
          binlen=0x30000, blob_extra=0, lineb1=264, ptr="", free_ok=True, chip_extra=0):
    """devuelve (texto del listado, yi1_s.dat sintetico, ADF sintetico)"""
    code = SYN_CODE.replace("{BUFFL}", buf_flags).replace("{AUDSZ}", str(aud_size)).replace("{PTRCODE}", ptr)
    if not free_ok:
        code = code.replace("(binend-binstart+511)&-512", "(binend-binstart)/2")
    equ = {"MEMF_CHIP": 2, "MEMF_FAST": 4, "MEMF_CLEAR": 0x10000, "_LVOAllocMem": -198, "_LVOFreeMem": -210,
           "BUF1": lineb1 * 100, "LINEB1": lineb1, "ROWB1": 88, "LINES": 100, "SLOTS": 22, "FETCHW": 17,
           "CL_SIZE": cl_size, "CL_TAIL": 64, "CL_LINES": 92, "SEG": 220,
           "COP1LC": 0x80, "BLTAPTR": 0x50, "BLTDPTR": 0x54, "CUSTOM": 0xDFF000,
           "D_BLK": 16, "D_MAP": 20, "D_INI": 24, "D_CHG": 28, "D_L2B": 32, "D_L2P": 36,
           "D_MLX": 40, "D_MLD": 44, "D_LNS": 48}
    lines = ["Sections:", '00: "CODE" (0-%X)' % binlen, "", 'Source: "syn.s"']
    labels = {"binstart": 0}
    addr, n = 0x1C, 1
    for ln in code.strip("\n").splitlines():
        if not ln.strip():
            continue
        lab = re.match(r"^(\w+):", ln)
        if lab:
            labels[lab.group(1)] = addr
        lines.append("00:%08X 4E71            \t%5d: %s" % (addr, n, ln))
        addr += 4
        n += 1
    labels["binend"] = binlen
    lines += ["", "Symbols by name:"]
    for k, v in sorted(equ.items()):
        lines.append("%-32s E:%08X" % (k, v & 0xFFFFFFFF))
    for k, v in sorted(labels.items()):
        lines.append("%-32s 00:%08X" % (k, v))
    lines += ["", "Symbols by value:"]
    # el blob: cabecera con las posiciones de D_* y secciones de 4 KB
    offs = [0x38, 0x0800, 0x0900, 0x0A00, l2b, 0x3000, 0x3100, 0x3200, 0x3300]
    hdr = b"SMWS" + bytes(12) + struct.pack(">10I", *offs, 0)
    data = bytearray(hdr) + bytes(0x3400 + blob_extra - len(hdr))
    return "\n".join(lines) + "\n", bytes(data), None


def selftest():
    cases = []

    def case(name, want, **kw):
        cases.append((name, want, kw))
    case("base (sin violaciones)", None)
    case("plano pedido en slow", "V-CHIP", buf_flags="MEMF_FAST")
    case("plano pedido PUBLIC", "V-CHIP", buf_flags="1")
    case("puntero del blitter a una etiqueta del binario", "V-STATIC",
         ptr="        move.l  #pfdata,BLTAPTR(a4)")
    case("puntero por registro: lea etiqueta(pc)", "V-STATIC",
         ptr="        lea     pfdata(pc),a0\n        move.l  a0,COP1LC(a4)")
    case("plano de la capa 2 desalineado (L2B)", "V-ALIGN", l2b=0x1004)
    case("lista del copper no multiplo de 4", "V-ALIGN", cl_size=0x1002)
    case("audio de longitud impar", "V-ALIGN", aud_size=2001)
    case("paso de fila de PF1 impar", "V-STRIDE", lineb1=263)
    case("chip > 512 KB", "V-CHIP-TOTAL", blob_extra=0x80000)
    case("slow > 512 KB", "V-SLOW-TOTAL", binlen=0x81000)
    case("FreeMem de otro tamano que el de boot.s", "V-LOADER", free_ok=False)
    bad = 0
    for name, want, kw in cases:
        text, data, _ = synth(**kw)
        L = Listing(text)
        m = build_model(L, data=data, data_len=align(len(data), SECTOR))
        codes = {c for c, _ in m.viol}
        if want is None:
            ok = not codes
            got = "ninguna" if ok else ", ".join(sorted(codes))
        else:
            ok = want in codes
            got = ", ".join(sorted(codes)) or "NINGUNA"
        print("  %-52s %s  (%s)" % (name, "ok" if ok else "FALLA", got))
        bad += 0 if ok else 1
    # el ADF: stage2 de otra longitud que el binario
    text, data, _ = synth()
    adf = bytearray(901120)
    adf[0:4] = b"DOS\0"
    struct.pack_into(">I", adf, 8, 0x30000)
    adf[1024:1028] = b"\0\0\0\0"
    adf[1026:1030] = b"A5PL"
    struct.pack_into(">II", adf, 1030, 1024 + 0x30000, 0x3400)
    m = build_model(Listing(text), data=data, adf=bytes(adf))
    ok = not m.viol
    print("  %-52s %s  (%s)" % ("ADF coherente", "ok" if ok else "FALLA", ", ".join(c for c, _ in m.viol) or "ninguna"))
    bad += 0 if ok else 1
    struct.pack_into(">I", adf, 8, 0x20000)
    m = build_model(Listing(text), data=data, adf=bytes(adf))
    ok = "V-LOADER" in {c for c, _ in m.viol}
    print("  %-52s %s" % ("ADF: stage2 de otra longitud que el binario", "ok" if ok else "FALLA"))
    bad += 0 if ok else 1
    print("selftest: %s" % ("FALLA (%d)" % bad if bad else "OK (%d casos)" % (len(cases) + 2)))
    return 1 if bad else 0


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("lst", nargs="?", default=os.path.join(ROOT, "work", "game.lst"),
                    help="listado de vasm (-L) de game.s")
    ap.add_argument("--data", default=None, help="yi1_s.dat (por defecto work/yi1_s.dat)")
    ap.add_argument("--adf", default=None, help="ADF (por defecto game.adf junto al listado)")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    if a.selftest:
        return selftest()
    if not os.path.exists(a.lst):
        print("memmap: no existe %s (armarlo con tools/game_build.sh)" % a.lst, file=sys.stderr)
        return 2
    L = Listing(open(a.lst, encoding="latin-1").read())
    datap = a.data or os.path.join(ROOT, "work", "yi1_s.dat")
    data = open(datap, "rb").read() if os.path.exists(datap) else None
    adfp = a.adf or os.path.join(os.path.dirname(os.path.abspath(a.lst)), "game.adf")
    adf = open(adfp, "rb").read() if os.path.exists(adfp) else None
    print("memmap: %s (datos: %s, ADF: %s)" % (os.path.relpath(a.lst, ROOT) if a.lst.startswith(ROOT) else a.lst,
                                                datap if data else "-", adfp if adf else "-"))
    m = build_model(L, data=data, adf=adf)
    report(m, a.verbose)
    return 1 if m.viol else 0


if __name__ == "__main__":
    sys.exit(main())
