#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gamecheck.py - Etapa 6.3: corre la parte de CPU de player/game.s -DREPLAY
(work/game.bin, tools/game_build.sh) en un emulador de 68000, frame a
frame, y comprueba que sigue la partida grabada como el lazo cerrado del
PC (m68kverify.py --mode loop --sprites): despues de cada frame RUN, los
campos de Mario y de la camara tienen que ser los del oraculo.

Hace lo que hace `entry` antes de tomar la maquina (punteros del C al mapa
y a los sprites) y despues llama a replay_init y a game_step por frame. Con Unicorn no corre el scroll: solo la entrada, la logica y las
resincronizaciones. Con --engine musashi corre ademas, frame a frame y en
el mismo orden que el bucle de game.s, cam_to_s, mario_draw y scroll_frame
(O3, Etapa 9.1) y da los ciclos de CPU por parte (peor y media) con las
mismas 7 partes que game.s -DBENCH / game_read.py (O1): entrada, level_frame,
mspr_draw, columna, build_mid, resto de scroll_frame y total. Los mide
cortando por PC: pone una trampa de linea A en la entrada de cada rutina y
en su direccion de retorno (nada de -DBENCH ni del timer de la CIA), asi que
son ciclos de CPU SIN DMA ni blitter (cota inferior, como scrollprof.py).

    python3 tools/gamecheck.py                  # Unicorn (rapido)
    python3 tools/gamecheck.py --engine musashi # + ciclos por frame y por parte (sin DMA)
    python3 tools/gamecheck.py --engine musashi --no-scroll   # sin scroll_frame
    python3 tools/gamecheck.py --cams 5400,6500 # la camara en esos frames
    python3 tools/gamecheck.py --spr            # + mario_sprite (mspr.c, 6b.4)
                                                #   contra un render de referencia, y
                                                #   mspr_draw (asm) suelto y con la cache
                                                #   de dos buffers alternados (MA1)
"""
import argparse
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import m68kverify as V                          # noqa: E402

PAL_FRAME = V.PAL_FRAME

# memoria del emulador (1 MB) para correr el scroll: el binario esta en
# V.BASE (0x10000..0x3D000)
DATA = 0x40000                  # work/yi1_s.dat (230 KB)
BUF1 = 0x80000                  # PF1 (59 136 B)
COPA = 0x90000                  # listas del copper (CL_SIZE = 49 500 B)
COPB = 0xA0000
SPRS = 0xB0000                  # sprites de Mario: lista A, lista B y el nulo
FAKE = 0xC0000                  # "CUSTOM" en RAM: DMACONR = 0 (blitter libre)
SCRATCH = 0xF8000               # para calibrar el coste de una trampa

# las 7 partes de game.s -DBENCH (game_read.py PARTS): (clave, nombre)
PARTS = (("entrada", "entrada (game_step sin level_frame)"),
         ("level_frame", "level_frame"),
         ("mspr_draw", "mspr_draw"),
         ("columna", "columna (columns)"),
         ("build_mid", "build_mid"),
         ("resto", "resto de scroll_frame"),
         ("total", "total (game_step + cam_to_s + mario_draw + scroll_frame)"))
# frames de resincronizacion (OP_SYNC/RUNSYNC/LEVEL): game.s no los cuenta en
# la entrada ni en el total
RESYNC_OPS = (V.REP_SYNC, V.REP_RUNSYNC, V.REP_LEVEL)


class Frames:
    """el frame del juego en Musashi, por partes (ver la cabecera)"""

    def __init__(self, cpu, B, syms, data):
        self.cpu, self.B, self.syms = cpu, B, syms
        self.M, self.mem = cpu.M, cpu.mem
        self.trap = self.mem.r16(V.RET)             # la trampa de linea A de vuelta a Python
        self.vars = B + syms["vars"]
        # lo que cuesta una trampa (execute() la cuenta): nop + trampa - nop
        self.mem.w16(SCRATCH, 0x4E71)
        self.mem.w16(SCRATCH + 2, self.trap)
        cpu.cpu.w_reg(self.M.Register.A7, V.STACK - 4)
        cpu.cpu.w_pc(SCRATCH)
        self.trapc = cpu.m.execute(1000).cycles - 4
        cpu.write(DATA, data)

    def v(self, name):
        return self.syms[name]

    def init_scroll(self):
        """lo que hace `entry` entre replay_init y tomar la maquina; despues
        del primer game_step (SYNC)"""
        B, syms, mem = self.B, self.syms, self.mem
        w32 = mem.w32
        mspr = syms["SPRBUF"]
        w32(self.vars + self.v("V_BUF1"), BUF1)
        w32(self.vars + self.v("V_COP"), COPA)
        w32(self.vars + self.v("V_COP2"), COPB)
        w32(B + syms["g_spra"], SPRS)
        w32(B + syms["g_sprb"], SPRS + mspr)
        w32(B + syms["g_null"], SPRS + 2 * mspr)
        w32(B + syms["_gfx32"], B + syms["gfx32"])
        self.call(B + syms["cam_to_s"], FAKE)
        self.call(B + syms["scroll_init"], FAKE)
        back = mem.r32(self.vars + self.v("V_BACK"))
        for lst in ("V_COP", "V_COP2"):             # Mario en las dos listas
            w32(self.vars + self.v("V_BACK"), mem.r32(self.vars + self.v(lst)))
            self.call(B + syms["mario_draw"], FAKE)
        w32(self.vars + self.v("V_BACK"), back)

    def call(self, adr, a4, base="x", regions=None):
        """corre la rutina en `adr` hasta que vuelve. regions = {direccion de
        entrada: etiqueta}: los ciclos entre la entrada y el retorno de esa
        rutina van a la etiqueta (el resto, a `base`). Devuelve {etiqueta: ciclos}"""
        R, cpu, mem = self.M.Register, self.cpu.cpu, self.mem
        arm = dict(regions or {})
        orig, rets, acc = {}, {}, {base: 0}
        label = base

        def patch(a):
            orig[a] = mem.r16(a)
            mem.w16(a, self.trap)

        for a in arm:
            patch(a)
        cpu.w_reg(R.A3, DATA)
        cpu.w_reg(R.A4, a4)
        cpu.w_reg(R.A5, self.vars)
        cpu.w_reg(R.A7, V.STACK - 4)
        mem.w32(V.STACK - 4, V.RET)
        cpu.w_pc(adr)
        while True:
            r = self.cpu.m.execute(10_000_000)
            acc[label] = acc.get(label, 0) + r.cycles - self.trapc
            hit = cpu.r_pc() - 2
            if hit == V.RET:
                break
            mem.w16(hit, orig.pop(hit))
            cpu.w_pc(hit)
            if hit in rets:                         # volvio de la rutina
                entry, label = rets.pop(hit)
                patch(entry)                        # (puede volver a llamarse)
            else:                                   # entro en la rutina
                ret = mem.r32(cpu.r_reg(R.A7))
                assert ret not in orig, "dos trampas en %X" % ret
                rets[ret] = (hit, label)
                patch(ret)
                label = arm[hit]
                acc.setdefault(label, 0)
        for a, w in orig.items():
            mem.w16(a, w)
        return acc

    def frame(self, B, syms):
        """game_step + cam_to_s + mario_draw + scroll_frame, como gframe.
        Devuelve ({parte: ciclos}, ciclos de game_step, s)"""
        st = self.call(B + syms["game_step"], B, "entrada", {B + syms["_level_frame"]: "level_frame"})
        oth = self.call(B + syms["cam_to_s"], FAKE)
        s = self.mem.r16(self.vars + self.v("V_S"))
        md = self.call(B + syms["mario_draw"], FAKE, "x", {B + syms["mspr_draw"]: "mspr_draw"})
        sf = self.call(B + syms["scroll_frame"], FAKE, "resto",
                       {B + syms["columns"]: "columna", B + syms["build_mid"]: "build_mid"})
        p = {"entrada": st["entrada"], "mspr_draw": md["mspr_draw"],
             "columna": sf["columna"], "build_mid": sf["build_mid"], "resto": sf["resto"]}
        if "level_frame" in st:
            p["level_frame"] = st["level_frame"]
        step = sum(st.values())
        p["total"] = step + sum(oth.values()) + sum(md.values()) + sum(sf.values())
        return p, step, s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", default=os.path.join(V.WORK, "game.bin"))
    ap.add_argument("--lst", default=os.path.join(V.WORK, "game.lst"))
    ap.add_argument("--oracle", default=os.path.join(V.WORK, "oracle_yi1.bin"))
    ap.add_argument("--engine", choices=("unicorn", "musashi"), default="unicorn")
    ap.add_argument("--cams", default="", help="frames (del oraculo) de los que dar la camara")
    ap.add_argument("--no-scroll", action="store_true",
                    help="con musashi: sin scroll_frame ni cam_to_s/mario_draw (solo game_step)")
    ap.add_argument("--data", default=os.path.join(V.WORK, "yi1_s.dat"),
                    help="datos del scroll (musashi)")
    ap.add_argument("--spr", action="store_true",
                    help="despues de cada frame, _mario_sprite (vbcc) contra la referencia")
    a = ap.parse_args()

    code = open(a.bin, "rb").read()
    syms = V.symbols(a.lst)
    for s in ("replay_init", "game_step", "replay", "_ram", "map16", "spr_lv",
              "_map16_lo", "_map16_hi", "_spr_level", "_level_sprites", "g_left"):
        if s not in syms:
            sys.exit("falta el simbolo %s en %s (armar con -DREPLAY)" % (s, a.lst))
    B = V.BASE
    cpu = V.MusashiCPU() if a.engine == "musashi" else V.UnicornCPU(False)
    cpu.write(B, code)
    # lo que hace entry con a4 = binstart
    cpu.write(B + syms["_map16_lo"], struct.pack(">I", B + syms["map16"]))
    cpu.write(B + syms["_map16_hi"], struct.pack(">I", B + syms["map16"] + 20 * 0x1B0))
    cpu.write(B + syms["_spr_level"], struct.pack(">I", B + syms["spr_lv"]))
    cpu.write(B + syms["_level_sprites"], b"\x01")
    cpu.call(B + syms["replay_init"], B)
    fr = None
    if a.engine == "musashi" and not a.no_scroll:
        for s in ("vars", "cam_to_s", "mario_draw", "scroll_init", "scroll_frame", "columns",
                  "build_mid", "mspr_draw", "_level_frame", "V_S", "V_BACK", "SPRBUF",
                  "g_spra", "g_sprb", "g_null", "_gfx32", "gfx32"):
            if s not in syms:
                sys.exit("falta el simbolo %s en %s" % (s, a.lst))
        fr = Frames(cpu, B, syms, open(a.data, "rb").read())
    pstat = {k: [] for k, _ in PARTS}               # parte -> [(ciclos, frame, s)]
    if a.spr:
        cpu.write(B + syms["_gfx32"], struct.pack(">I", B + syms["gfx32"]))
        g32 = cpu.read(B + syms["gfx32"], 0x5D00)
    sprbad = sprn = asmbad = cachebad = 0
    cyc_plain, cyc_cache = [], []
    if a.spr:
        # MA1: dos buffers de sprites que se alternan y NO se vuelven a rellenar,
        # como g_spra / g_sprb en la Amiga (mspr_draw reusa lo que ya tienen)
        for b in (BUFA, BUFB):
            cpu.write(b, bytes([0x55]) * (8 * SPRW))
    ctest = {"k": bytes(128), "flip": 0}            # fichas de la cache de la prueba

    rp = B + syms["replay"]
    nframes, first, nst = struct.unpack(">HHH", cpu.read(rp + 4, 6))
    o_ops = struct.unpack(">I", cpu.read(rp + 12, 4))[0]
    ops = cpu.read(rp + o_ops, 6 * nframes)[0::6]

    db = open(a.oracle, "rb").read()
    n = len(db) // V.REC
    orc = {}
    for i in range(n):
        f, tl = struct.unpack_from("<IB", db, i * V.REC)
        if first <= f < first + nframes:
            o = i * V.REC + 8
            orc[f] = (db[o:o + 256], db[o + 256:o + 576])

    def want(f, adr):
        dp, w13 = orc[f]
        return dp[adr] if adr < 0x100 else w13[adr - 0x13C0]

    RAM = B + syms["_ram"]
    fields = V.FIELDS + V.LOOP_FIELDS
    bad, runs, costs, cams = [], 0, [], {}
    wantcam = {int(x) for x in a.cams.split(",") if x}
    for k in range(nframes):
        f = first + k
        if fr and k == 0:                       # el primer frame lo hace `entry`
            cpu.call(B + syms["game_step"], B)
            fr.init_scroll()
            c = 0
        elif fr:
            pf, step, s = fr.frame(B, syms)
            c = step + fr.trapc - 34                # como cpu.call: execute() - 34
            for key, v in pf.items():
                if ops[k] in RESYNC_OPS and key in ("entrada", "total"):
                    continue
                pstat[key].append((v, f, s))
        else:
            c = cpu.call(B + syms["game_step"], B)
        ram = cpu.read(RAM, 0x2000)
        if f in wantcam:
            cams[f] = (ram[0x1A] | ram[0x1B] << 8, want(f, 0x1A) | want(f, 0x1B) << 8)
        if a.spr and ops[k] != V.REP_SKIP:
            sprn += 1
            if not spr_ok(cpu, B, syms, g32, False)[0]:
                sprbad += 1
            ok, cy = spr_ok(cpu, B, syms, g32, True)    # buffer suelto: siempre dibuja
            if not ok:
                asmbad += 1
            cyc_plain.append(cy)
            ok, cy = spr_cache(cpu, B, syms, g32, ctest)
            if not ok:
                cachebad += 1
            cyc_cache.append(cy)
        if ops[k] == V.REP_SKIP:
            continue
        if ops[k] == V.REP_RUN:
            runs += 1
            costs.append((c, f))
        miss = [nm for nm, adr, w in fields
                if any(ram[adr + t] != want(f, adr + t) for t in range(w))]
        if miss:
            bad.append((f, ops[k], miss))
    left = struct.unpack(">H", cpu.read(B + syms["g_left"], 2))[0]
    print("game.bin (%s): replay de %d frames desde %d (%d RUN), quedan %d; frames que no "
          "coinciden con el oraculo: %d" % (a.engine, nframes, first, runs, left, len(bad)))
    for f, op, miss in bad[:10]:
        print("  frame %d (op %d): %s" % (f, op, ", ".join(miss)))
    if a.spr:
        slow = struct.unpack(">H", cpu.read(B + syms["mspr_slow"], 2))[0]
        print("mario_sprite (vbcc) = referencia en %d de %d frames; mspr_draw (asm): %d "
              "(fue al C en %d)" % (sprn - sprbad, sprn, sprn - asmbad, slow))
        print("mspr_draw con dos buffers alternados sin rellenar (como el juego): %d de %d"
              % (sprn - cachebad, sprn))
        if a.engine == "musashi" and cyc_cache:
            for nm, cl in (("buffer suelto (siempre dibuja)", cyc_plain),
                           ("buffers del juego (g_spra/g_sprb)", cyc_cache)):
                print("  mspr_draw %s: media %.0f ciclos (%.1f %% del frame), peor %d (%.1f %%)"
                      % (nm, sum(cl) / len(cl), 100 * sum(cl) / len(cl) / PAL_FRAME,
                         max(cl), 100 * max(cl) / PAL_FRAME))
    for f in sorted(cams):
        print("  camara en el frame %d: %d (oraculo %d)" % (f, cams[f][0], cams[f][1]))
    if a.engine == "musashi" and costs:
        c = sorted(x[0] for x in costs)
        w = max(costs)
        print("ciclos por game_step RUN (sin DMA): media %.0f (%.1f %%), max %d (%.1f %%, frame %d)"
              % (sum(c) / len(c), 100 * sum(c) / len(c) / PAL_FRAME, w[0], 100 * w[0] / PAL_FRAME, w[1]))
    if fr:
        parts_report(pstat)
    return 1 if bad or (a.spr and (sprbad or asmbad or cachebad)) else 0


def parts_report(pstat):
    """peor y media de cada parte (la tabla que lee tools/regress.py)"""
    n = len(pstat["total"])
    over = sum(1 for v, _, _ in pstat["total"] if v > PAL_FRAME)
    print("partes del frame del juego (Musashi, ciclos de CPU SIN DMA ni blitter; %d frames "
          "medidos, el replay sin resincronizaciones en entrada y total):" % n)
    for key, name in PARTS:
        rows = pstat[key]
        if not rows:
            continue
        mx = max(rows)
        mean = sum(v for v, _, _ in rows) / len(rows)
        # (la clave primero: regress.py lo lee; entre parentesis el detalle)
        print("  %-12s max %7d media %7.0f (%5.1f %% / %5.1f %%) frame %5d s %4d  n %5d  %s"
              % (key, mx[0], mean, 100.0 * mx[0] / PAL_FRAME, 100.0 * mean / PAL_FRAME,
                 mx[1], mx[2], len(rows), name))
    print("  frames con el total por encima de un frame PAL (%d ciclos): %d de %d"
          % (PAL_FRAME, over, n))


SPRW = 2 + 2 * 40 + 2           # mario.h: MSPR_WORDS
SPRBUF = 0xE0000                # buffer de los sprites en la memoria del emulador
BUFA, BUFB = 0xE2000, 0xE4000   # los dos buffers del juego (g_spra, g_sprb)


def spr_cache(cpu, B, syms, g32, st):
    """MA1: mspr_draw en un buffer que ya tenia una pose (BUFA/BUFB alternados, sin
    rellenar), con g_spra/g_sprb = BUFA/BUFB y las fichas de la cache (mspr_kA/kB)
    de la prueba; las del juego (si corre el scroll, con sus buffers) se guardan y
    se devuelven, para no tocar lo que esa corrida cree que tienen sus buffers"""
    ka, gs = B + syms["mspr_kA"], B + syms["g_spra"]
    saved = (cpu.read(ka, 128), cpu.read(gs, 8))
    cpu.write(ka, st["k"])
    cpu.write(gs, struct.pack(">II", BUFA, BUFB))
    res = spr_ok(cpu, B, syms, g32, True, BUFA if st["flip"] else BUFB, False)
    st["k"] = cpu.read(ka, 128)
    st["flip"] ^= 1
    cpu.write(ka, saved[0])
    cpu.write(gs, saved[1])
    return res


def spr_ok(cpu, B, syms, g32, asm, buf=SPRBUF, fill=True):
    """_mario_sprite(SPRBUF, $2C, $A0) (o mspr_draw con a2 = SPRBUF, asm)
    decodificado = render de la OAM de Mario (mario_oam) con la VRAM armada
    como el DMA del NMI (ver marioverify mspr)"""
    st = V.STACK - 4
    cpu.write(st + 4, struct.pack(">III", buf, 0x2C, 0xA0))
    if fill:
        cpu.write(buf, bytes([0x55]) * (8 * SPRW))
    cy = call_args(cpu, B + syms["mspr_draw" if asm else "_mario_sprite"], B, buf)
    ram = cpu.read(B + syms["_ram"], 0x2000)
    oam = cpu.read(B + syms["_mario_oam"], 16)
    osz = cpu.read(B + syms["_mario_osz"], 4)
    sp = struct.unpack(">%dH" % (4 * SPRW), cpu.read(buf, 8 * SPRW))
    got = {}
    for col in range(2):
        a, b = sp[2 * col * SPRW:(2 * col + 1) * SPRW], sp[(2 * col + 1) * SPRW:(2 * col + 2) * SPRW]
        if a[0] == 0 and a[1] == 0:
            continue
        if not b[1] & 0x80:
            return False, cy
        vs = (a[0] >> 8) | ((a[1] >> 2) & 1) << 8
        ve = (a[1] >> 8) | ((a[1] >> 1) & 1) << 8
        hs = ((a[0] & 0xFF) << 1) | (a[1] & 1)
        for l in range(ve - vs):
            for x in range(16):
                c = (((a[2 + 2 * l] >> (15 - x)) & 1) | (((a[3 + 2 * l] >> (15 - x)) & 1) << 1)
                     | (((b[2 + 2 * l] >> (15 - x)) & 1) << 2) | (((b[3 + 2 * l] >> (15 - x)) & 1) << 3))
                if c:
                    got[(hs - 0xA0 + x, vs - 0x2C - 1 + l)] = c
    vram = {}
    for r in range(2):
        for i in range(5):
            o = 0x0D85 + 10 * r + 2 * i
            p = (ram[o] | ram[o + 1] << 8) - 0x2000
            if 0 <= p <= len(g32) - 64:
                vram[16 * r + 2 * i] = g32[p:p + 32]
                vram[16 * r + 2 * i + 1] = g32[p + 32:p + 64]
    p = (ram[0x0D99] | ram[0x0D9A] << 8) - 0x2000
    if 0 <= p <= len(g32) - 32:
        vram[0x7F] = g32[p:p + 32]
    want = {}
    for e in range(3, -1, -1):              # la primera tapa a las demas
        o = oam[4 * e:4 * e + 4]
        if o[1] == 0xF0:
            continue
        sz = 16 if osz[e] & 2 else 8
        ex = o[0] | ((osz[e] & 1) << 8)
        ex = ex - 512 if ex >= 256 else ex
        ey = o[1] - 256 if o[1] >= 0xF0 else o[1]
        for v in range(sz):
            for u in range(sz):
                uu = sz - 1 - u if o[3] & 0x40 else u
                vv = sz - 1 - v if o[3] & 0x80 else v
                t = o[2] + (uu >> 3) + 16 * (vv >> 3)
                if t not in vram:
                    continue
                tl, x, y = vram[t], uu & 7, vv & 7
                c = (((tl[2 * y] >> (7 - x)) & 1) | (((tl[2 * y + 1] >> (7 - x)) & 1) << 1)
                     | (((tl[16 + 2 * y] >> (7 - x)) & 1) << 2) | (((tl[17 + 2 * y] >> (7 - x)) & 1) << 3))
                if c:
                    want[(ex + u, ey + v)] = c
    want = {k: v for k, v in want.items() if 0 <= k[0] < 256 and 0 <= k[1] < 240}
    got = {k: v for k, v in got.items() if 0 <= k[0] < 256 and 0 <= k[1] < 240}
    return got == want, cy


def call_args(cpu, adr, a4, a2=0):
    """como cpu.call, sin tocar los argumentos ya escritos en la pila"""
    if isinstance(cpu, V.MusashiCPU):
        M = cpu.M
        cpu.cpu.w_reg(M.Register.A2, a2)
        cpu.cpu.w_reg(M.Register.A4, a4)
        cpu.cpu.w_reg(M.Register.A7, V.STACK - 4)
        cpu.mem.w32(V.STACK - 4, V.RET)
        cpu.cpu.w_pc(adr)
        return cpu.m.execute(10_000_000).cycles - 34    # (la excepcion de linea A del final)
    else:
        from unicorn.m68k_const import UC_M68K_REG_A2
        cpu.uc.reg_write(UC_M68K_REG_A2, a2)
        cpu.uc.reg_write(cpu.A4, a4)
        cpu.uc.reg_write(cpu.A7, V.STACK - 4)
        cpu.uc.mem_write(V.STACK - 4, struct.pack(">I", V.RET))
        cpu.uc.emu_start(adr, V.RET)
        return 0


if __name__ == "__main__":
    sys.exit(main())
