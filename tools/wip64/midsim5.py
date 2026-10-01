#!/usr/bin/env python3
"""midsim5.py (S4, WIP) - modelo de build_mid sobre work/yi1_s.dat con
contadores de eventos por frame (lineas reescritas, registros escritos,
recorridos de WAIT, ...). Calibrado contra scroll.s en Musashi: los conteos de
"ip" (edicion en el sitio, tools/wip64/s4_inplace.diff) dan exactamente los
del asm en s = 4580 (ida) y 4556 (vuelta).
Modos: full (= master), ip (en el sitio), hyb (ip, pero entera si klo ya
salio yendo a la derecha), fullL (entera siempre; a la izquierda base menor:
S4D=-2 = pista conservadora del min b de la escritura anterior + agregar por
la izquierda las que ya salieron). --defer: diferir la carga que entra por la
derecha hasta que su tramo nuevo se ve (x + b - LASTX; S4K = registros a
mirar). Costes: s4_est*.py del informe (no versionados)."""
import struct, sys, os, collections

DAT = os.environ.get("S4DAT", "work/yi1_s.dat")
LINES, LASTX, MIDMAX = 224, 255, 12
TARDE = 4
NONE_L, NONE_U = -32768, 32767


def s16(v):
    return v - 65536 if v >= 32768 else v


def mkhtab():
    h = []
    for x in range(LASTX + 1):
        if x <= 239:
            q = (x + 8) >> 3
            v = 0x48 + 4 * q
        else:
            t = x - 240
            v = 0xCE if t >= 12 else (t & ~3) + 0xC4
        v &= 0xFE
        v = min(v, 0xE2)
        h.append(v | 1)
    cell = []
    for t in range(LASTX + 1):
        cs = t
        while cs > 0 and h[cs - 1] == h[t]:
            cs -= 1
        ce = t
        while ce < LASTX and h[ce + 1] == h[t]:
            ce += 1
        cell.append((t - ce, t - cs + 1))
    return h, cell


HTAB, CELL = mkhtab()


def load(path=DAT):
    b = open(path, "rb").read()
    offs = struct.unpack_from(">10I", b, 16)
    MLX, MLD, LNS = offs[6], offs[7], offs[8]
    mlx = struct.unpack_from(">225H", b, MLX)
    lines = []
    for L in range(LINES):
        i = mlx[L] - 1
        recs = []
        while True:
            c, x, r, col, a, bb = struct.unpack_from(">HHHHhh", b, MLD + 12 * i)
            recs.append((c, s16(x), a, bb))
            if x == 0x7FFF:
                break
            i += 1
        lines.append(recs)
    W = struct.unpack_from(">H", b, 4)[0]
    nk = W // 16 + 1
    lns = []
    for k in range(nk):
        o = struct.unpack_from(">H", b, LNS + 2 * k)[0]
        gs = []
        while True:
            goff = s16(struct.unpack_from(">H", b, LNS + o)[0])
            o += 2
            if goff == -1:
                break
            hid = struct.unpack_from(">H", b, LNS + o)[0]
            o += 2
            n = (hid & 63) // 2
            ls = [v // 32 for v in struct.unpack_from(">%dH" % n, b, LNS + o)]
            o += 2 * n
            gs.append((goff, hid, ls))
        lns.append(gs)
    return lines, lns


SZ = {0: 8, 1: 4, 2: 8, 3: 12}


class LS:
    __slots__ = ("klo", "khi", "vl", "vu", "s0", "maxa", "minb", "lvl", "lvu", "wr", "nwait", "hint", "hleft", "kprev")

    def __init__(self):
        self.klo = self.khi = 1
        self.vl, self.vu = 1, 0
        self.s0 = None
        self.maxa, self.minb = -16000, 16000
        self.lvl, self.lvu = NONE_L, NONE_U
        self.wr = False


class Model:
    def __init__(self, lines, lns, mode="ip", defer=False, live=False, lw=False):
        self.lines, self.lns, self.mode, self.defer, self.live, self.lw = lines, lns, mode, defer, live, lw
        self.cons = bool(os.environ.get('S4CONS'))
        self.st = [[LS() for _ in range(LINES)] for _ in range(2)]
        self.last = [0x8000, 0x8000]
        self.gst = [dict() for _ in range(2)]   # goff -> (id, vl, vu, hot)
        # deadlines: D[L][k] = min_{j>=k} (x_j + b_j) para diferir entradas
        self.D = []
        for recs in lines:
            n = len(recs)
            d = [32767] * n
            for k in range(n - 2, 0, -1):
                c, x, a, b = recs[k]
                e = x if c >= TARDE else x + b
                d[k] = min(d[k + 1], e)
            self.D.append(d)

    # --- un frame: escribe la lista li en s ---
    def frame(self, li, s):
        ev = collections.Counter()
        if self.last[li] == s:
            return ev
        d = self.last[li] - s
        right = s >= self.last[li]
        allm = abs(d) > 16
        self.last[li] = s
        st = self.st[li]
        if allm:
            groups = [(None, None, list(range(16 * g, 16 * g + 16))) for g in range(14)]
        else:
            groups = self.lns[s >> 4]
        gs = self.gst[li]
        for goff, hid, ls in groups:
            ev["grp"] += 1
            if goff is not None:
                g = gs.get(goff)
                if g and g[0] == hid and g[1] <= s < g[2]:
                    ev["gskip"] += 1
                    continue
            rw = 0
            gvl, gvu = -32768, 32767
            for L in ls:
                ev["chk"] += 1
                t = st[L]
                if t.vl <= s < t.vu:
                    gvl, gvu = max(gvl, t.vl), min(gvu, t.vu)
                    continue
                rw += 1
                self.line(L, t, s, right, ev)
            if goff is not None:
                if rw == 0:
                    gs[goff] = (hid, gvl, gvu, 0)
                else:
                    gs[goff] = (0, 0, 0, 1)
        return ev

    def line(self, L, t, s, right, ev):
        recs = self.lines[L]
        x = lambda k: recs[k][1]
        if self.mode == "fullL":
            return self.full(L, t, s, ev, "L" if not right else "init", right)
        if self.mode == "full" or not t.wr:
            return self.full(L, t, s, ev)
        klo = t.klo
        if x(klo - 1) >= s:
            return self.full(L, t, s, ev, "reentra", right)
        if (self.mode == "hyb" and right or self.mode == "hyb2") and x(klo) < s:
            return self.full(L, t, s, ev, "exited")
        a0 = t.khi
        lim = s + LASTX
        while x(a0) <= lim:
            a0 += 1
        while a0 > klo and x(a0 - 1) > lim:
            a0 -= 1
        if a0 == klo:
            ev["empty"] += 1
            t.khi = a0
            t.maxa, t.minb = -16000, 16000
            t.lvl, t.lvu = NONE_L, NONE_U
            return self.fin(L, t, s, ev)
        if a0 - klo > MIDMAX:
            return self.full(L, t, s, ev, "midmax")
        maxa, minb, tin = t.maxa, t.minb, False
        if self.live:
            maxa, minb = self.liveab(recs, klo, t.khi, s, ev)
        for k in range(t.khi, a0):
            c, xx, a, b = recs[k]
            if c >= TARDE:
                tin = True
            else:
                maxa, minb = max(maxa, a), min(minb, b)
        d0 = min(s - maxa, x(klo))
        d4 = max(s + 1 - minb, x(a0 - 1) - LASTX)
        if d4 > d0:
            return self.full(L, t, s, ev, "nobase")
        if tin:
            nb = "can"
        elif t.lvl == NONE_L:
            nb = "free"
        elif t.lvl <= s < t.lvu and d4 <= t.s0 <= d0:
            nb = "keep"
        else:
            nb = "can"
        if nb == "can":
            if not (d4 <= s <= d0):
                return self.full(L, t, s, ev, "canout")
            base = s
        elif nb == "free":
            base = t.s0 if d4 <= t.s0 <= d0 else (d0 if right else d4)
        else:
            base = t.s0
        if base == t.s0 and a0 >= t.khi:
            # keep: append
            if a0 > t.khi:
                ev["keep_app"] += 1
                self.write(L, t, t.khi, a0, ev, first=(t.khi == klo), maxa=t.maxa, minb=t.minb)
            else:
                ev["same"] += 1
            t.khi = a0
            return self.fin(L, t, s, ev)
        # rebase (o truncado con la misma base)
        ev["reb"] += 1
        t.s0 = base
        cons = (t.maxa, t.minb)
        t.maxa, t.minb = -16000, 16000
        t.lvl, t.lvu = NONE_L, NONE_U
        end = min(t.khi, a0)
        lastw = None
        for k in range(klo, end):
            c, xx, a, b = recs[k]
            if k == klo or (c & 3) == 0 and (c == 0 or c == 4):
                lastw = xx
                ev["walkw"] += 1
            ev["walk"] += 1
            if c >= TARDE:
                self.cell(t, lastw)
            else:
                t.maxa, t.minb = max(t.maxa, a), min(t.minb, b)
        if self.cons:
            t.maxa, t.minb = max(t.maxa, cons[0]), min(t.minb, cons[1])
        if a0 > t.khi:
            ev["reb_app"] += 1
            self.write(L, t, t.khi, a0, ev, first=(t.khi == klo), maxa=t.maxa, minb=t.minb, lastw=lastw)
        elif a0 < t.khi:
            ev["trunc"] += 1
        t.khi = a0
        return self.fin(L, t, s, ev)

    def cell(self, t, xw):
        tt = xw - t.s0
        lo, hi = CELL[tt]
        t.lvl = max(t.lvl, t.s0 + lo)
        t.lvu = min(t.lvu, t.s0 + hi)

    def write(self, L, t, k0, k1, ev, first, maxa, minb, lastw=None):
        recs = self.lines[L]
        for k in range(k0, k1):
            c, xx, a, b = recs[k]
            ev["wrec"] += 1
            if first and k == k0 or c in (0, 4):
                lastw = xx
            if c >= TARDE:
                self.cell(t, lastw)
            else:
                maxa, minb = max(maxa, a), min(minb, b)
        t.maxa, t.minb = maxa, minb

    def full(self, L, t, s, ev, why="init", right=True):
        ev["full"] += 1
        ev["full_" + why] += 1
        recs = self.lines[L]
        x = lambda k: recs[k][1]
        klo = t.klo
        while x(klo) < s:
            klo += 1
        while x(klo - 1) >= s:
            klo -= 1
        khi = max(t.khi, klo)
        while x(khi) <= s + LASTX:
            khi += 1
        while x(khi - 1) > s + LASTX:
            khi -= 1
        if khi - klo > MIDMAX:
            khi = klo + MIDMAX
        s0 = s
        DD = int(os.environ.get('S4D','0'))
        if DD == -2:
            hint = getattr(t, 'hint', None) if getattr(t, 'hleft', False) else None
            canon = any(recs[k][0] >= TARDE for k in range(klo, khi))
            if not right and khi > klo and not canon and hint is not None:
                kprev = getattr(t, 'kprev', klo)
                mb = hint
                for k in range(klo, max(klo, min(kprev, khi))):
                    mb = min(mb, recs[k][3])
                    ev["hnew"] += 1
                s0 = min(s, max(s + 1 - mb, x(khi - 1) - LASTX))
                while klo > 1 and x(klo - 1) >= s0 and khi - klo < MIDMAX and recs[klo - 1][0] < TARDE and s0 + recs[klo - 1][3] > s and s0 + recs[klo-1][2] <= s:
                    klo -= 1
                    ev["lwrec"] += 1
            # hint nuevo: min(vu_init - s0, b de las escritas)
            if not right:
                vui = (x(khi) - LASTX) if x(khi) > s + LASTX else (x(klo) + 1)
                mb = vui - s0
                for k in range(klo, khi):
                    mb = min(mb, recs[k][3])
                t.hint = 0 if canon else mb
                t.hleft = True
                t.kprev = klo
            else:
                t.hleft = False
            DD = 0
        if DD and not right and khi > klo and all(recs[k][0] < TARDE for k in range(klo, khi)):
            if DD < 0:
                hint = getattr(t, 'hint', 0)
                s0 = min(s, max(s + 1 - hint, x(khi - 1) - LASTX)) if hint > 0 else s
            else:
                s0 = min(s, max(s - DD, x(khi - 1) - LASTX))
            maxa, minb = -16000, 16000
            for k in range(klo, khi):
                maxa, minb = max(maxa, recs[k][2]), min(minb, recs[k][3])
            if not (s0 + maxa <= s < s0 + minb):
                ev["redo"] += 1
                ev["wrec"] += khi - klo
                s0 = s
            else:
                while klo > 1 and x(klo - 1) >= s0 and khi - klo < MIDMAX and recs[klo - 1][0] < TARDE and s0 + recs[klo - 1][3] > s and s0 + recs[klo-1][2] <= s:
                    klo -= 1
                    ev["lwrec"] += 1
        if self.lw and not right and khi > klo and khi - klo < MIDMAX and why != "init":
            if all(recs[k][0] < TARDE for k in range(klo, khi)):
                maxa, minb = -16000, 16000
                for k in range(klo, khi):
                    maxa, minb = max(maxa, recs[k][2]), min(minb, recs[k][3])
                s0 = max(s + 1 - minb, x(khi - 1) - LASTX)
                s0 = min(s0, s, s - maxa)
                while klo > 1 and x(klo - 1) >= s0 and khi - klo < MIDMAX and recs[klo - 1][0] < TARDE and (self.live or s0 + recs[klo - 1][3] > s):
                    klo -= 1
                    ev["lwrec"] += 1
                s0 = min(s0, x(klo))
        t.klo, t.khi, t.s0, t.wr = klo, khi, s0, True
        mb = 16000
        for k in range(klo, khi):
            if recs[k][0] < TARDE:
                mb = min(mb, recs[k][3])
        t.hint = mb if mb < 16000 else 0
        t.lvl, t.lvu = NONE_L, NONE_U
        self.write(L, t, klo, khi, ev, first=True, maxa=-16000, minb=16000)
        return self.fin(L, t, s, ev)

    def liveab(self, recs, k0, k1, s, ev):
        maxa, minb = -16000, 16000
        for k in range(k0, k1):
            c, xx, a, b = recs[k]
            if xx < s or c >= TARDE:
                continue
            ev["liverec"] += 1
            maxa, minb = max(maxa, a), min(minb, b)
        return maxa, minb

    def fin(self, L, t, s, ev):
        recs = self.lines[L]
        x = lambda k: recs[k][1]
        kl = t.klo
        if self.live:
            while kl < t.khi and x(kl) < s:
                kl += 1
            t.maxa, t.minb = self.liveab(recs, kl, t.khi, s, collections.Counter())
        vl = max(t.s0 + t.maxa, x(kl - 1) + 1, x(t.khi - 1) - LASTX, t.lvl)
        if x(t.khi) > s + LASTX:
            nu = x(t.khi) - LASTX
            if self.defer:
                CAP = int(os.environ.get('S4CAP', '100000'))
                m = None
                j = t.khi
                while True:
                    c, xx, a, b = recs[j]
                    if m is not None and xx >= m:
                        break
                    if m is not None and j - t.khi >= int(os.environ.get('S4K', '1000')):
                        m = min(m, xx)
                        break
                    e = xx if c >= TARDE else xx + b
                    if m is None:
                        m = min(e, xx + CAP)
                    else:
                        m = min(m, e)
                    ev["dscan"] += 1
                    if xx == 32767:
                        break
                    j += 1
                nu = max(nu, m - LASTX)
        else:
            nu = x(t.klo) + 1
        vu = min(t.s0 + t.minb, nu, t.lvu)
        if not (vl <= s < vu):
            vl, vu = s, s + 1
            ev["late"] += 1
        t.vl, t.vu = vl, vu


def seq(speed, ret=True, top=4864):
    """s de cada frame como scroll.s (S0 = 0)"""
    out, s = [], 0
    while s < top:
        s = min(s + speed, top)
        out.append(s)
    if ret:
        while s > 0:
            s = max(s - speed, 0)
            out.append(s)
    return out


def run(mode="ip", speed=2, ret=True, defer=False, path=DAT, live=False, lw=False):
    lines, lns = load(path)
    m = Model(lines, lns, mode, defer, live, lw)
    m.frame(0, 0)
    m.frame(1, 0)
    li = 1
    res = []
    for s in seq(speed, ret):
        res.append((s, m.frame(li, s)))
        li ^= 1
    return res


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="ip")
    ap.add_argument("--speed", type=int, default=2)
    ap.add_argument("--defer", action="store_true")
    ap.add_argument("--at", type=int, nargs="*", default=[])
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()
    res = run(a.mode, a.speed, True, a.defer, live=a.live)
    n = len(res) // 2
    for nm, part in (("ida", res[:n]), ("vuelta", res[n:])):
        tot = collections.Counter()
        for s, e in part:
            tot.update(e)
        print(nm, dict(tot))
    for s0 in a.at:
        for i, (s, e) in enumerate(res):
            if s == s0:
                print(s, "ida" if i < n else "vuelta", dict(e))
