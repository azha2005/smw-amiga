#!/usr/bin/env python3
"""OAM del binario 68000 contra la grabada: fichas, orden y fase (G8/G2).

Lee GAME_OAM_TRACE del modo game del host (NOOAM + SPR_OAM), llama al
despacho _sprite_run real y compara RAM, mapa, marcas y fichas grabadas.
Las tablas no grabadas las calcula el C; nunca copia la pose de la SNES.
"""
import collections
import os
import struct
import argparse
import sys

import m68kverify as V


class SpriteOAM:
    REC = 645

    def __init__(self, cpu, base, syms, oracle, records):
        for symbol in ("_spr_oam_first", "_spr_oam_n", "_rex_gfx"):
            if symbol not in syms:
                raise ValueError("falta %s: compilar con CDEFS='-DNOOAM -DSPR_OAM'" % symbol)
        self.cpu = cpu
        self.ram = base + syms["_ram"]
        self.first = base + syms["_spr_oam_first"]
        self.n = base + syms["_spr_oam_n"]
        path = os.path.splitext(oracle)[0] + "_oam.bin"
        with open(path, "rb") as f:
            self.db = f.read()
        if len(self.db) != records * self.REC:
            raise ValueError("%s: %d bytes; se esperan %d registros de %d" %
                             (path, len(self.db), records, self.REC))
        self.frames = collections.Counter()
        self.exact = collections.Counter()
        self.shift = [0, 0, 0]
        self.order_bad = 0
        self.order_frame = None
        self.order_pos = []
        self.shown = []
        self.samples = {}

    def flush_order(self):
        lastpos = lastslot = -1
        for slot, pos in sorted(self.order_pos):
            if slot != lastslot:
                self.order_bad += pos < lastpos
                lastpos, lastslot = pos, slot
        self.order_pos = []

    def recorded(self, i, frame):
        if not 0 <= i * self.REC < len(self.db):
            return None
        rec = self.db[i * self.REC:(i + 1) * self.REC]
        if struct.unpack_from("<I", rec)[0] != frame:
            return None
        count = rec[4]
        if count > 128:
            raise ValueError("OAM grabada invalida: %d fichas en frame %d" % (count, frame))
        return [rec[5 + k * 5:10 + k * 5] for k in range(count)]

    @staticmethod
    def find(entries, want):
        if entries is None:
            return -1
        return next((k for k in range(len(entries) - len(want) + 1)
                     if entries[k:k + len(want)] == want), -1)

    def compare(self, i, frame, pnum):
        ram = self.cpu.read(self.ram, 0x2000)
        first = self.cpu.read(self.first, 12)
        ns = self.cpu.read(self.n, 12)
        recorded = self.recorded(i, frame)
        if recorded is None:
            raise ValueError("OAM/oraculo desalineados en registro %d, frame %d" % (i, frame))
        if frame != self.order_frame:
            self.flush_order()
            self.order_frame = frame
        for k in sorted(range(12), key=lambda k: first[k]):
            if not ns[k]:
                continue
            entries = []
            for c in range(ns[k]):
                s = 64 + (first[k] >> 2) + c
                if s >= 128:
                    raise ValueError("OAM fuera de rango: ranura %d, indice %02X, n %d" % (k, first[k], ns[k]))
                o = ram[0x0200 + 4 * s:0x0204 + 4 * s]
                if o[1] != 0xF0:
                    entries.append(o + ram[0x0420 + s:0x0421 + s])
            if not entries:
                continue
            num = pnum[k]
            self.frames[num] += 1
            pos = self.find(recorded, entries)
            if pos >= 0:
                self.exact[num] += 1
                self.order_pos.append((first[k], pos))
                key = tuple(e[2:] for e in entries)
                if num == 0xAB and len(self.samples) < 8:
                    self.samples.setdefault(key, (frame, recorded[pos:pos + len(entries)], entries))
            elif len(self.shown) < 10:
                self.shown.append("sprite %02X frame %d ranura %d: %s" %
                                  (num, frame, k, " ".join(e.hex() for e in entries)))
            if num == 0xAB:
                for d in (-1, 0, 1):
                    self.shift[d + 1] += self.find(self.recorded(i + d, frame + d), entries) >= 0

    def report(self):
        self.flush_order()
        for num, frames in sorted(self.frames.items()):
            print("OAM 68000 %02X: frames %d exactas %d" % (num, frames, self.exact[num]))
        print("OAM 68000: fuera de orden %d; Rex anterior/mismo/siguiente %d/%d/%d" %
              (self.order_bad, *self.shift))
        for text in self.shown:
            print("  " + text)
        if not self.frames:
            raise ValueError("OAM 68000: 0 comprobaciones; la puerta no se ejecuto")
        if self.frames != self.exact or self.order_bad:
            raise ValueError("OAM 68000: fichas u orden distintos del oraculo")

    def preview(self, path):
        """Evidencia de OAM con G3a; no prueba el remapeo/colores del OCS."""
        from PIL import Image, ImageDraw
        import mksprgfx as G
        vram, _, _ = G.build_vram(G._DEF_SRC, G.LEVEL)
        cg = G.level_cgram(G._DEF_SRC, G.LEVEL)
        samples = list(self.samples.values())
        im = Image.new("RGB", (160 * len(samples), 300), "#19212b")
        draw = ImageDraw.Draw(im)
        for c, (frame, reference, actual) in enumerate(samples):
            draw.text((c * 160 + 4, 3), "frame %d" % frame, fill="white")
            decoded = [[tuple(G.entries(e))[0] for e in es] for es in (reference, actual)]
            xs = [x - 512 if x >= 256 else x for es in decoded for x, *_ in es]
            ys = [y - 256 if y >= 224 else y for es in decoded for _, y, *_ in es]
            x0, y0 = min(xs) - 4, min(ys) - 4
            for r, es in enumerate(decoded):
                draw.text((c * 160 + 4, 20 + r * 140), "SNES" if not r else "68000", fill="white")
                for x, y, tile, attr, hi in es:
                    x = x - 512 if x >= 256 else x
                    y = y - 256 if y >= 224 else y
                    w = 16 if hi & 2 else 8
                    pixels = G.ficha(vram, tile, w, (attr >> 6) & 1, (attr >> 7) & 1)
                    palette = [G.snes_to_rgb8(color) for color in G.cgram_palette(cg, 8 + ((attr >> 1) & 7))]
                    for dy, row in enumerate(pixels):
                        for dx, index in enumerate(row):
                            if index:
                                px, py = c * 160 + (x - x0 + dx) * 3, 34 + r * 140 + (y - y0 + dy) * 3
                                draw.rectangle((px, py, px + 2, py + 2), fill=palette[index])
        im.save(path)
        print("evidencia OAM (paleta SNES, no OCS): " + path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace", required=True, help="GAME_OAM_TRACE del host en modo game")
    ap.add_argument("--oracle", default=os.path.join(V.WORK, "oracle_yi1.bin"))
    ap.add_argument("--bin", default=os.path.join(V.WORK, "logicbench.bin"))
    ap.add_argument("--lst", default=os.path.join(V.WORK, "logicbench.lst"))
    ap.add_argument("--require", default="AB", help="tipos con fichas visibles obligatorias, p.ej. AB,B9,BD,02")
    ap.add_argument("--require-state", default="", help="estados de sprite obligatorios en la traza, p.ej. 04 para nube")
    ap.add_argument("--preview", help="PNG: referencia arriba, OAM del 68000 abajo (G3a, paleta SNES)")
    a = ap.parse_args()
    code = open(a.bin, "rb").read()
    syms = V.symbols(a.lst)
    oracle = open(a.oracle, "rb").read()
    if len(oracle) % V.REC:
        raise ValueError("oraculo truncado")
    records = len(oracle) // V.REC
    indices = {struct.unpack_from("<I", oracle, i * V.REC)[0]: i for i in range(records)}
    cpu = V.MusashiCPU()
    cpu.write(V.BASE, code)
    check = SpriteOAM(cpu, V.BASE, syms, a.oracle, records)
    cpu.call(V.BASE + syms["_logic68k_init"], V.BASE)
    cpu.call(V.BASE + syms["_mcoll_init"], V.BASE)
    calls = bad = marker_bad = abi_bad = 0
    states = collections.Counter()
    cycles = []
    with open(a.trace, "rb") as trace:
        if trace.read(4) != b"SOT1":
            raise ValueError("traza no es SOT1")
        mlen = struct.unpack("<I", trace.read(4))[0]
        if not 0 < mlen <= 0x8000:
            raise ValueError("mapa de la traza fuera de rango")
        mp = 0x80000
        cpu.write(V.BASE + syms["_map16_lo"], struct.pack(">I", mp))
        cpu.write(V.BASE + syms["_map16_hi"], struct.pack(">I", mp + mlen // 2))
        while True:
            header = trace.read(8)
            if not header:
                break
            if len(header) != 8:
                raise ValueError("cabecera de traza truncada")
            frame, slot, num, first, n = struct.unpack("<IBBBB", header)
            body = trace.read(2 * (0x2000 + mlen))
            if len(body) != 2 * (0x2000 + mlen) or slot >= 12 or not n:
                raise ValueError("registro de traza invalido")
            before = body[:0x2000]
            before_map = body[0x2000:0x2000 + mlen]
            after = body[0x2000 + mlen:0x4000 + mlen]
            after_map = body[0x4000 + mlen:]
            cpu.write(check.ram, before)
            cpu.write(mp, before_map)
            cpu.write(check.n, bytes(12))
            states[before[0x14C8 + slot]] += 1
            saved = {getattr(cpu.M.Register, name): 0x23456700 + k
                     for k, name in enumerate(("D2", "D3", "D4", "D5", "D6", "D7", "A2", "A3", "A5", "A6"))}
            for reg, value in saved.items():
                cpu.cpu.w_reg(reg, value)
            # ABI de vbcc: retorno en (sp), u8 en el byte +7 de su ranura long.
            cpu.cpu.w_reg(cpu.M.Register.A4, V.BASE)
            cpu.cpu.w_reg(cpu.M.Register.A7, V.STACK - 8)
            cpu.write(V.STACK - 8, struct.pack(">II", V.RET, slot))
            cpu.cpu.w_pc(V.BASE + syms["_sprite_run"])
            cycles.append(cpu.m.execute(10_000_000).cycles - 34)
            abi_bad += (any(cpu.cpu.r_reg(reg) != value for reg, value in saved.items())
                        or cpu.cpu.r_reg(cpu.M.Register.A4) != V.BASE
                        or cpu.cpu.r_reg(cpu.M.Register.A7) != V.STACK - 4)
            calls += 1
            got = cpu.read(check.ram, 0x2000)
            equal = got == after and cpu.read(mp, mlen) == after_map
            bad += not equal
            marker_bad += cpu.read(check.first + slot, 1) != bytes([first]) or cpu.read(check.n + slot, 1) != bytes([n])
            if not equal and bad <= 10:
                ds = ["$%04X=%02X/%02X" % (k, got[k], after[k]) for k in range(0x2000) if got[k] != after[k]][:8]
                print("despacho sprite %02X frame %d: %s" % (num, frame, " ".join(ds)))
            pnum = [0] * 12
            pnum[slot] = num
            check.compare(indices[frame], frame, pnum)
    print("despacho 68000: %d llamadas, RAM/mapa distintas %d, marcas distintas %d, ABI distinta %d" % (calls, bad, marker_bad, abi_bad))
    print("estados comprobados: " + ", ".join("%02X=%d" % t for t in sorted(states.items())))
    if cycles:
        print("ciclos por sprite_run (sin DMA): media %.0f, max %d" % (sum(cycles) / len(cycles), max(cycles)))
    if not calls or bad or marker_bad or abi_bad:
        raise ValueError("despacho 68000: la puerta falla")
    # Un sprite que desaparece no deja una ficha ni una marca del frame previo.
    # Se corre level_frame REAL, con Mario en NOOAM y sin fase de sprites.
    ghost = bytearray(cpu.read(check.ram, 0x2000))
    for s in range(128):
        ghost[0x0201 + 4 * s] = 17
    cpu.write(check.ram, ghost)
    cpu.write(check.n, bytes([2] * 12))
    cpu.write(V.BASE + syms["_level_sprites"], b"\x00")
    cpu.call(V.BASE + syms["_level_frame"], V.BASE)
    cleared = cpu.read(check.ram, 0x2000)
    if any(cleared[0x0201 + 4 * s] != 0xF0 for s in range(128)) or cpu.read(check.n, 12) != bytes(12):
        raise ValueError("level_frame: quedaron fichas o marcas del frame anterior")
    print("level_frame: limpieza de 128 Y y 12 marcas OK")
    for num in (int(x, 16) for x in a.require.split(",")):
        if not check.frames[num]:
            raise ValueError("OAM 68000: 0 comprobaciones del tipo %02X requerido" % num)
    for state in (int(x, 16) for x in a.require_state.split(",") if x):
        if not states[state]:
            raise ValueError("despacho 68000: 0 comprobaciones del estado %02X requerido" % state)
    check.report()
    if a.preview:
        check.preview(a.preview)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, struct.error) as e:
        sys.exit(str(e))
