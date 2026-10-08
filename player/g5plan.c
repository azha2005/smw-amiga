/*
 * g5plan.c - G2T fase B: el bloque de la foto y el plan del Rex en C.
 * Especificacion: tools/g2t_ref.py (contrato de docs/instrucciones-g2t-a.md
 * §1-bis). Solo con -DSPR_G5; sin el, este fichero no emite nada y los
 * builds por defecto no cambian (tools/logicbench_build.sh ni lo compila).
 *
 * Sin int/long a secas, sin float, sin malloc, sin static con direccion
 * tomada (P47): todo el estado va en los buffers que pasa quien llama.
 */
#include "g5plan.h"

#ifdef SPR_G5
#include "gen/smwram.h"
#include "smwmac.h"
#include "msprite.h"
#if !defined(NOOAM) || !defined(SPR_OAM)
#error "SPR_G5 requiere -DNOOAM -DSPR_OAM"
#endif

/* palabras big endian del bloque: nativas en el 68000 (offsets pares) */
#if defined(__VBCC__)
#define GW(p)       (*(const u16 *)(p))
#define PW(p, v)    (*(u16 *)(p) = (u16)(v))
#else
#define GW(p)       ((u16)(((const u8 *)(p))[0] << 8 | ((const u8 *)(p))[1]))
#define PW(p, v)    (((u8 *)(p))[0] = (u8)((u16)(v) >> 8), ((u8 *)(p))[1] = (u8)(v))
#endif

/* --- g5_capture ---
   Mario: cada pareja activa (POS/CTL distintos de 0) del buffer; VSTART,
   VSTOP y HSTART de sus palabras de control; filas R = VSTART - $2C + j,
   x = HSTART - $A0 + px. Un pixel cuenta si 0 <= x < 256 y 0 <= R < 224
   (lo que se ve), igual que g2t_ref.mario_amiga. Los indices salen de
   DATA/DATB del sprite par (planos 0-1) y del impar (2-3). */
void g5_capture(u8 *blk, const u16 *spr)
{
    u16 flags = 0, c, j, n, vs, ve, hs, k;
    s16 x0, r0, wr = 0, rr, x;
    u8 *row, *env, *rex;
    u8 nrex = 0;

    for (j = 0; j < G5_WIN; j++)
        PW(blk + G5B_MASK + 2 * j, 0);
    for (c = 0; c < 2; c++) {
        const u16 *s0 = spr + (2 * c) * G5_SPRW, *s1 = s0 + G5_SPRW;
        u16 pos = s0[0], ctl = s0[1];
        if (!pos && !ctl)
            continue;
        vs = (u16)((pos >> 8) | ((ctl & 4) << 6));
        ve = (u16)((ctl >> 8) | ((ctl & 2) << 7));
        hs = (u16)(((pos & 0xFF) << 1) | (ctl & 1));
        n = (u16)(ve - vs);
        x0 = (s16)(hs - G5_HX0);
        r0 = (s16)(vs - G5_V0);
        if (!(flags & 1)) {
            wr = r0;
            flags |= 1;
        }
        for (j = 0; j < n; j++) {
            const u16 *d = s0 + 2 + 2 * j, *e = s1 + 2 + 2 * j;
            u16 p0 = d[0], p1 = d[1], p2 = e[0], p3 = e[1], op, b, m;
            rr = (s16)(r0 + j);
            if (rr < 0 || rr >= G5_ROWS)
                continue;
            op = (u16)(p0 | p1 | p2 | p3);
            if (!op)
                continue;
            if (rr < wr || rr >= wr + G5_WIN) {
                flags |= 2;
                continue;
            }
            row = blk + G5B_MASK + 2 * (rr - wr);
            env = blk + G5B_ENV + 30 * (rr - wr) - 2;   /* env[i-1] = env + 2 i */
            m = GW(row);
            x = x0;
            for (b = 0x8000; b; b = (u16)(b >> 1), x++) {
                u16 v;
                if (!(op & b) || (u16)x >= 256)
                    continue;
                v = (u16)(((p0 & b) ? 1 : 0) | ((p1 & b) ? 2 : 0)
                          | ((p2 & b) ? 4 : 0) | ((p3 & b) ? 8 : 0));
                if (!(m & (u16)(1 << v))) {
                    m |= (u16)(1 << v);
                    env[2 * v] = (u8)x;
                }
                env[2 * v + 1] = (u8)x;
            }
            PW(row, m);
        }
    }
    PW(blk + G5B_MROW, wr);
    blk[G5B_PAL] = (u8)(mario_pal & 7);
    blk[G5B_CAMX] = ram[wm_Bg1HOfs + 1];
    blk[G5B_CAMX + 1] = ram[wm_Bg1HOfs];
    blk[G5B_CAMY] = ram[wm_Bg1VOfs + 1];
    blk[G5B_CAMY + 1] = ram[wm_Bg1VOfs];
    /* los Rex de la OAM ampliada (spr_oam_first/n de cada ranura): las
       entradas visibles (y != $F0), como sprgfx_manifest.read_trace */
    rex = blk + G5B_REX;
    for (k = 0; k < 12; k++) {
        u16 first, cnt, ne = 0, t;
        if (!spr_oam_n[k] || ram[wm_SpriteNum + k] != 0xAB)
            continue;
        if (nrex >= G5_MAXREX) {
            flags |= 4;
            break;
        }
        first = (u16)(64 + (spr_oam_first[k] >> 2));
        cnt = spr_oam_n[k];
        for (t = 0; t < cnt && first + t < 128; t++) {
            const u8 *o = ram + 0x200 + 4 * (first + t);
            u8 *e;
            if (o[1] == 0xF0)
                continue;
            if (ne >= G5_MAXT) {
                flags |= 4;
                break;
            }
            e = rex + G5R_E + 5 * ne;
            e[0] = o[0];
            e[1] = o[1];
            e[2] = o[2];
            e[3] = o[3];
            e[4] = ram[0x420 + first + t];
            ne++;
        }
        if (!ne)
            continue;
        rex[G5R_SLOT] = (u8)k;
        rex[G5R_N] = (u8)ne;
        rex[G5R_X] = ram[wm_SpriteXHi + k];
        rex[G5R_X + 1] = ram[wm_SpriteXLo + k];
        rex[G5R_Y] = ram[wm_SpriteYHi + k];
        rex[G5R_Y + 1] = ram[wm_SpriteYLo + k];
        rex += G5R_SIZE;
        nrex++;
    }
    blk[G5B_NREX] = nrex;
    PW(blk + G5B_FLAGS, flags);
}

/* ----------------------------------------------------------------------
   G2T-B3 (docs/instrucciones-g2t-b35.md): el plan, como g2t_ref.py.
   Las tablas (bank.idx, bank.g5env, mario_pal.bin) se leen por bytes: sus
   offsets no siempre son pares.
   ---------------------------------------------------------------------- */
#define B16(p)      ((u16)(((const u8 *)(p))[0] << 8 | ((const u8 *)(p))[1]))
#define B32(p)      ((u32)B16(p) << 16 | B16((const u8 *)(p) + 2))

u16 g5_mario_mask(const u8 *blk, s16 row)
{
    s16 j = (s16)(row - (s16)B16(blk + G5B_MROW));
    if (j < 0 || j >= G5_WIN)
        return 0;
    return (u16)(B16(blk + G5B_MASK + 2 * j) & 0xFFFE);
}

void g5_mario_span(const u8 *blk, s16 row, u8 idx, u8 *first, u8 *last)
{
    s16 j = (s16)(row - (s16)B16(blk + G5B_MROW));
    const u8 *e = blk + G5B_ENV + 30 * j + 2 * (idx - 1);
    *first = e[0];
    *last = e[1];
}

/* scrollsim.advance a 256 px con el paso medido 231 -> 243 (P110) */
static s16 g5_adv(s16 x, u16 n)
{
    while (n--)
        x = (s16)(x == 231 ? 243 : x >= 239 ? x + 8 : x + 16);
    return x;
}

/* scrollsim.xh a 256 px; h <= $CE (g2t_ref.xh); fuera: 999 */
static s16 g5_xh(u16 h)
{
    if (h <= 0xC0) {
        s16 d = (s16)(h - 0x48);
        return (s16)(8 * (d >= 0 ? d >> 2 : -((3 - d) >> 2)) - 1);
    }
    if (h == 0xC4 || h == 0xC6)
        return 243;
    if (h == 0xC8 || h == 0xCA)
        return 247;
    if (h == 0xCC)
        return 251;
    return (s16)(h <= 0xCE ? 255 : 999);
}

/* g2t_ref.htab: h del WAIT para que el MOVE caiga en x' >= x */
static u16 g5_htab(s16 x)
{
    if (x <= 239)
        return (u16)(0x48 + 4 * ((x + 8) >> 3));
    return (u16)(x >= 252 ? 0xCE : 0xC4 + ((x - 240) & ~3));
}

u8 g5_segment(const u8 *list, u16 cl, u16 seg, s16 row, g5_seg *out)
{
    const u8 *a = list + cl + (u32)seg * (u16)row;
    u16 v = (u16)(row + G5_V0), o, w1;
    u8 nb = 0, stage = 0, wrap = 0;
    s16 t = 0, last = G5_NONE, x;

    out->ok = 0;
    for (o = 0; o < seg; o += 4) {
        w1 = B16(a + o);
        if (w1 == 0x84)
            break;
        if (!stage && (w1 & 1) && ((w1 >> 8) == ((v - 1) & 255) || w1 == 0xFFDF)) {
            if (w1 == 0xFFDF)
                wrap = 1;
            continue;
        }
        if (!stage && w1 == 0x1FE && o < 8)
            continue;
        if (!stage && !(w1 & 1) && w1 != 0x1FE) {
            nb++;
            continue;
        }
        if (!stage) {
            stage = 1;
            t = (s16)(G5_T0 + (nb > 9 ? 16 * (nb - 9) : 0));
        }
        if (w1 & 1) {
            if ((w1 & 0xFE) > 0xCE)
                return 0;               /* fuera del modelo medido */
            x = g5_adv(t, 2);
            t = g5_xh((u16)(w1 & 0xFE));
            if (x > t)
                t = x;
        } else {
            last = t;
            t = g5_adv(t, 1);
        }
    }
    if (o >= seg || (last != G5_NONE && last > 255))
        return 0;
    out->ok = 1;
    out->nb = nb;
    out->wrap = wrap;
    out->last = last;
    out->free = (s16)(G5_T0 + (nb > 9 ? 16 * (nb - 9) : 0));
    return 1;
}

/* el segmento de la fila, calculado la primera vez que se pide */
static const g5_seg *g5_seg_of(g5_work *w, const u8 *list, u16 cl, u16 seg, s16 row)
{
    g5_seg *s = &w->segs[row];
    u16 bit = (u16)(1 << (row & 15));
    if (!(w->segbits[row >> 4] & bit)) {
        g5_segment(list, cl, seg, row, s);
        w->segbits[row >> 4] |= bit;
        w->nsegs++;
    }
    return s;
}

/* g2t_ref.schedule: k MOVE con x minimo need en el sufijo de la fila;
   0 = no caben (None) */
static u8 g5_schedule(const g5_seg *s, const g5_seg *nx, u8 k, s16 need, s16 row, g5_sfx *out)
{
    s16 end, t, pos, first, wl, bl = 0;
    u8 nop, j, best = 0;

    if (row == 255 - G5_V0)
        return 0;                       /* K255 = {7: 0}: nunca cabe nada */
    if (!s->ok || !nx->ok)
        return 0;
    if (nx->nb == 7)
        end = 351 - 56;
    else if (nx->nb == 8)
        end = 351 - 64;
    else if (nx->nb == 9)
        end = 351 - 72;
    else
        return 0;
    t = s->last != G5_NONE ? s->last : s->free;
    if (s->last != G5_NONE) {           /* encadenado tras una carga */
        pos = g5_adv(t, 1);
        nop = 0;
        while (pos < need) {
            pos = g5_adv(pos, 1);
            nop++;
        }
        if (nop + k <= G5_SLOTS && g5_adv(pos, (u16)(k - 1)) <= end) {
            out->tipo = 2;
            out->h = 0;
            out->nop = nop;
            for (j = 0; j < k; j++)
                out->pos[j] = g5_adv(pos, j);
            bl = out->pos[k - 1];
            best = 1;
        }
    }
    if (need <= 255) {                  /* WAIT con el copper libre */
        u16 h = g5_htab(need);
        first = g5_xh(h);
        if (first - t >= 48) {
            wl = g5_adv(first, (u16)(k - 1));
            if (k + 1 <= G5_SLOTS && wl <= end && (!best || wl < bl)) {
                out->tipo = 1;
                out->h = (u8)h;
                out->nop = 0;
                for (j = 0; j < k; j++)
                    out->pos[j] = g5_adv(first, j);
                best = 1;
            }
        }
    } else if (t <= 255 - 48) {
        wl = (s16)(263 + 8 * (k - 1));
        if (k + 1 <= G5_SLOTS && wl <= end && (!best || wl < bl)) {
            out->tipo = 1;
            out->h = 0xD0;
            out->nop = 0;
            for (j = 0; j < k; j++)
                out->pos[j] = (s16)(263 + 8 * j);
            best = 1;
        }
    }
    out->k = k;
    return best;
}

/* x minimo de un MOVE de la transicion t en el segmento s */
static s16 g5_req(const g5_tr *t, s16 s)
{
    return (s16)(t->desde == s && t->xult != G5_NONE ? t->xult + 1 : 0);
}

/* un uso (fila, indice): como uses_of.add, ya recortado */
static void g5_use(g5_work *w, s16 rr, u8 i, u16 color, u8 first, u8 last)
{
    u16 bit = (u16)(1 << (rr & 15));
    if (!(w->usebits[rr >> 4] & bit)) {
        w->usebits[rr >> 4] |= bit;
        w->umask[rr] = 0;
        w->urows[w->nrows++] = (u8)rr;
    }
    if (!(w->umask[rr] & (u16)(1 << i))) {
        w->umask[rr] |= (u16)(1 << i);
        w->ucol[rr][i] = color;
        w->ufirst[rr][i] = first;
        w->ulast[rr][i] = last;
        return;
    }
    if (first < w->ufirst[rr][i])
        w->ufirst[rr][i] = first;
    if (last > w->ulast[rr][i])
        w->ulast[rr][i] = last;
}

/* primer y ultimo bit de una mascara no nula de 24 bits */
static void g5_bits(u32 m, u8 *lo, u8 *hi)
{
    u8 b = 0;
    while (!(m & 1)) {
        m >>= 1;
        b++;
    }
    *lo = b;
    while (m >>= 1)
        b++;
    *hi = b;
}

/* datos de una pose en las tablas G3 (sprgfx_final.DESC) */
#define G5D(tab, n)  ((tab) + 24 + 32 * (u16)(n))

/* un intento con la variante n (g2t_ref.plan_frame, attempt): 1 = sin
   transiciones perdidas */
static u8 g5_attempt(g5_work *w, const u8 *g3tab, const u8 *g3env, u16 n,
                     s16 x0, s16 r0, const u8 *list, u16 cl, u16 seg, u8 *ntr)
{
    const u8 *d = G5D(g3tab, n), *pe, *pal;
    u16 hgt = B16(d + 6), wid = B16(d + 4), r, i, m, e, cnt;
    s16 rr, s, lo;
    u8 np, a, b, nt = 0, jj, kk;
    u8 rows[G5_USEDROWS], ma, rx, nr;

    for (r = 0; r < G5_ROWWORDS; r++) {
        w->usebits[r] = 0;
        w->linebits[r] = 0;
    }
    w->nrows = w->nlrows = 0;
    w->ln[0] = 0;
    for (r = 0; r < w->nmrows; r++) {   /* Mario ya calculado una vez */
        const g5_muse *mr = &w->mario[r];
        for (i = 1; i < 16; i++)
            if (mr->mask & (u16)(1 << i))
                g5_use(w, w->mrows[r], (u8)i, w->colors[i], mr->first[i], mr->last[i]);
    }
    pe = g3env + B32(g3env + 16 + 4 * n);   /* Rex: bank.g5env */
    np = pe[0];
    pal = pe + 2;
    pe = pal + 4 * np;
    for (r = 0; r < hgt; r++) {
        cnt = *pe++;
        rr = (s16)(r0 + (s16)r);
        for (e = 0; e < cnt; e++, pe += 4) {
            u32 mk = (u32)pe[1] << 16 | (u32)pe[2] << 8 | pe[3];
            s16 xlo = (s16)(x0 < 0 ? -x0 : 0), xhi = (s16)(255 - x0);
            if (rr < 0 || rr >= G5_ROWS)
                continue;
            if (xhi > (s16)wid - 1)
                xhi = (s16)(wid - 1);
            if (xlo > xhi)
                continue;
            mk &= ((u32)1 << (xhi + 1)) - 1;
            mk &= ~(((u32)1 << xlo) - 1);
            if (!mk)
                continue;
            g5_bits(mk, &a, &b);
            g5_use(w, rr, pal[4 * pe[0]], B16(pal + 4 * pe[0] + 2),
                   (u8)(x0 + a), (u8)(x0 + b));
        }
    }
    /* urows tiene dos tramos ordenados: Mario y las filas nuevas del Rex.
       Mezclarlos cuesta <= 72 filas, sin recorrer la pantalla vacia. */
    ma = nr = 0;
    rx = w->nmrows;
    while (ma < w->nmrows || rx < w->nrows) {
        if (rx == w->nrows || (ma < w->nmrows && w->urows[ma] < w->urows[rx]))
            rows[nr++] = w->urows[ma++];
        else
            rows[nr++] = w->urows[rx++];
    }
    for (i = 1; i < 16; i++) {          /* transitions: solo filas con usos */
        u16 value = w->colors[i];
        s16 prev = -1, pl = G5_NONE;
        for (e = 0; e < nr; e++) {
            r = rows[e];
            if (!(w->umask[r] & (u16)(1 << i)))
                continue;
            if (w->ucol[r][i] != value) {
                g5_tr *t = &w->tr[nt];
                if (nt >= G5_MAXTR)
                    return 0;
                t->idx = (u8)i;
                t->val = w->ucol[r][i];
                t->desde = prev;
                t->xult = pl;
                t->hasta = (s16)r;
                value = t->val;
                nt++;
            }
            prev = (s16)r;
            pl = w->ulast[r][i];
        }
    }
    *ntr = nt;
    /* place: orden (hasta - desde, hasta, indice), insercion estable */
    for (jj = 0; jj < nt; jj++) {
        const g5_tr *t = &w->tr[jj];
        for (kk = jj; kk > 0; kk--) {
            const g5_tr *u = &w->tr[w->order[kk - 1]];
            s16 lt = (s16)(t->hasta - t->desde), lu = (s16)(u->hasta - u->desde);
            if (lu < lt || (lu == lt && (u->hasta < t->hasta ||
                                         (u->hasta == t->hasta && u->idx <= t->idx))))
                break;
            w->order[kk] = w->order[kk - 1];
        }
        w->order[kk] = jj;
    }
    for (jj = 0; jj < nt; jj++) {
        const g5_tr *t = &w->tr[w->order[jj]];
        u8 done = 0;
        lo = t->desde > -1 ? t->desde : -1;
        for (s = (s16)(t->hasta - 1); s >= lo; s--) {
            if (s == -1) {
                if (w->ln[0] < 15) {
                    w->lid[0][w->ln[0]++] = w->order[jj];
                    done = 1;
                    break;
                }
                continue;
            }
            if (s + 1 < G5_ROWS) {
                u16 bit = (u16)(1 << ((s + 1) & 15));
                u8 k = (w->linebits[(s + 1) >> 4] & bit) ? w->ln[s + 1] : 0;
                s16 need = g5_req(t, s);
                g5_sfx p;
                if (k >= G5_SLOTS)
                    continue;
                for (m = 0; m < k; m++) {
                    s16 q = g5_req(&w->tr[w->lid[s + 1][m]], s);
                    if (q > need)
                        need = q;
                }
                if (g5_schedule(g5_seg_of(w, list, cl, seg, s), g5_seg_of(w, list, cl, seg, (s16)(s + 1)),
                                (u8)(k + 1), need, s, &p)) {
                    if (!k) {
                        /* filas de salida en orden, sin limpiar 224 entradas */
                        for (m = w->nlrows; m && w->lrows[m - 1] > s; m--)
                            w->lrows[m] = w->lrows[m - 1];
                        w->lrows[m] = (u8)s;
                        w->nlrows++;
                        w->linebits[(s + 1) >> 4] |= bit;
                    }
                    w->lid[s + 1][k] = w->order[jj];
                    w->ln[s + 1] = (u8)(k + 1);
                    w->sfx[s] = p;
                    done = 1;
                    break;
                }
            }
        }
        if (!done)
            return 0;                   /* una transicion sin plazo */
    }
    return 1;
}

static u8 *g5_put16(u8 *o, u16 v)
{
    o[0] = (u8)(v >> 8);
    o[1] = (u8)v;
    return o + 2;
}

/* la forma de un candidato (sprgfx_bank.shape) en el directorio G2IX:
   la lista de variantes o 0 */
static const u8 *g5_shape(const u8 *g3tab, const u8 *rx, s16 sx, s16 sy, u16 *nv)
{
    const u8 *ix = g3tab + B32(g3tab + 20);     /* metadata | G2IX (+20 = largo) */
    u16 count = B16(ix + 6), j, t, n = rx[G5R_N];
    u8 prio = (u8)(rx[G5R_E + 3] >> 4 & 3);

    for (t = 1; t < n; t++)
        if ((rx[G5R_E + 5 * t + 3] >> 4 & 3) != prio)
            return 0;                   /* prioridades mixtas: no hay forma */
    for (j = 0; j < count; j++) {
        const u8 *de = ix + 8 + 12 * j, *tl = g3tab + B32(de);
        if (de[4] != prio || de[5] != n)
            continue;
        for (t = 0; t < n; t++, tl += 10) {
            const u8 *e = rx + G5R_E + 5 * t;
            s16 dx = (s16)((u8)(e[0] - (u8)sx) ^ 0x80) - 128;
            s16 dy = (s16)((u8)(e[1] - (u8)sy) ^ 0x80) - 128;
            if ((s16)B16(tl) != dx || (s16)B16(tl + 2) != dy
                || B16(tl + 4) != (u16)(e[2] | (e[3] & 1) << 8)
                || tl[6] != ((e[4] & 2) ? 16 : 8)
                || tl[7] != (u8)((e[3] >> 6 & 1) | (e[3] >> 7) << 1)
                || tl[8] != (u8)(e[3] >> 1 & 7))
                break;
        }
        if (t == n) {
            *nv = B16(de + 6);
            return ix + B32(de + 8);
        }
    }
    return 0;
}

/* filtro A3 (g2t_ref.a3_compatible) con las filas de bank.g5env */
static u8 g5_a3(const g5_work *w, const u8 *g3tab, const u8 *g3env, u16 n, s16 r0)
{
    const u8 *pe = g3env + B32(g3env + 16 + 4 * n), *pal;
    u16 hgt = B16(G5D(g3tab, n) + 6), r, e, cnt, j = 0;
    u8 np = pe[0];

    pal = pe + 2;
    pe = pal + 4 * np;
    for (r = 0; r < hgt; r++) {
        s16 rr = (s16)(r0 + (s16)r);
        u16 mm;
        while (j < w->nmrows && w->mrows[j] < rr)
            j++;
        mm = j < w->nmrows && w->mrows[j] == rr ? w->mario[j].mask : 0;
        cnt = *pe++;
        for (e = 0; e < cnt; e++, pe += 4) {
            const u8 *p = pal + 4 * pe[0];
            if ((mm & (u16)(1 << p[0])) && w->colors[p[0]] != B16(p + 2))
                return 0;
        }
    }
    return 1;
}

u16 g5_plan(u32 frame, const u8 *blk, const u8 *g3tab, const u8 *g3env, const u8 *pals,
            const u8 *list, u16 cl, u16 seg, g5_work *w, u8 *out)
{
    const u8 *rx = blk + G5B_REX, *vl = 0, *d;
    u16 nv = 0, j, n = 0, r, i, m, c, var = 0xFFFF;
    s16 camx = (s16)B16(blk + G5B_CAMX), camy = (s16)B16(blk + G5B_CAMY);
    s16 bkey = 0, sx = 0, sy = 0, x0 = 0, r0 = 0;
    u8 *o = out, *cnt, nr = blk[G5B_NREX], ntr, slot = 0, have = 0;

    for (i = 0; i < 16; i++)
        w->colors[i] = B16(pals + 32 * (blk[G5B_PAL] & 7) + 2 * i);
    w->nsegs = 0;
    for (r = 0; r < G5_ROWWORDS; r++)
        w->segbits[r] = 0;
    w->nmrows = 0;
    /* La frontera B2/B3 sigue siendo el unico lector de las envolventes. */
    for (r = 0; r < G5_ROWS; r++) {
        s16 rr = (s16)r;
        u16 mm;
        g5_muse *mr;
        mm = g5_mario_mask(blk, rr);
        if (!mm)
            continue;
        w->mrows[w->nmrows] = (u8)rr;
        mr = &w->mario[w->nmrows++];
        mr->mask = mm;
        for (i = 1; i < 16; i++)
            if (mm & (u16)(1 << i))
                g5_mario_span(blk, rr, (u8)i, &mr->first[i], &mr->last[i]);
    }
    /* el Rex de menor sy + origen_y (primera variante de su forma), luego ranura */
    for (c = 0; c < nr; c++, rx += G5R_SIZE) {
        s16 csx = (s16)(B16(rx + G5R_X) - camx), csy = (s16)(B16(rx + G5R_Y) - camy), key;
        u16 cnv;
        const u8 *cvl = g5_shape(g3tab, rx, csx, csy, &cnv);
        if (!cvl)
            continue;
        key = (s16)(csy + (s16)B16(G5D(g3tab, B16(cvl)) + 2));
        if (!have || key < bkey || (key == bkey && rx[G5R_SLOT] < slot)) {
            have = 1;
            bkey = key;
            slot = rx[G5R_SLOT];
            sx = csx;
            sy = csy;
            vl = cvl;
            nv = cnv;
        }
    }
    for (j = 0; have && j < nv; j++) {
        n = B16(vl + 2 * j);
        d = G5D(g3tab, n);
        x0 = (s16)(sx + (s16)B16(d));
        r0 = (s16)(sy + (s16)B16(d + 2) + 1);
        if (!g5_a3(w, g3tab, g3env, n, r0))
            continue;
        if (g5_attempt(w, g3tab, g3env, n, x0, r0, list, cl, seg, &ntr)) {
            var = n;
            break;
        }
    }
    o = g5_put16(g5_put16(o, (u16)(frame >> 16)), (u16)frame);
    o = g5_put16(o, var);
    if (var == 0xFFFF) {
        for (i = 0; i < 4 * 10 + 2; i++)
            *o++ = 0;
        return (u16)(o - out);
    }
    /* canales SPR4-7 (armado VBL) */
    d = G5D(g3tab, var);
    {
        u16 hgt = B16(d + 6), cols = d[8];
        u32 co = B32(d + 16);
        s16 clip = (s16)(r0 < 0 ? -r0 : 0);
        for (c = 0; c < 2; c++) {
            s16 hx = (s16)(x0 + 16 * c);
            u8 vis = c < cols && r0 + (s16)hgt > 0 && r0 < G5_ROWS && hx > -16 && hx < 256;
            for (m = 0; m < 2; m++) {
                if (!vis) {
                    for (i = 0; i < 10; i++)
                        *o++ = 0;
                    continue;
                }
                {
                    u16 vs = (u16)(G5_V0 + (r0 > 0 ? r0 : 0)), ve = (u16)(G5_V0 + r0 + hgt);
                    u16 hp = (u16)(0xA0 + hx), ch = (u16)(4 + 2 * c + m);
                    u32 pt = B32(g3tab + co + 8 * c + 4 * m) + 4 + 4 * (u32)clip;
                    *o++ = 1;
                    *o++ = 0;
                    o = g5_put16(g5_put16(o, (u16)(pt >> 16)), (u16)pt);
                    o = g5_put16(o, (u16)((vs & 255) << 8 | (hp >> 1)));
                    o = g5_put16(o, (u16)((ve & 255) << 8 | ((ch & 1) ? 0x80 : 0)
                                          | (vs >> 8) << 2 | (ve >> 8) << 1 | (hp & 1)));
                }
            }
        }
    }
    *o++ = w->ln[0];                    /* colores de partida (bloque VBL) */
    for (m = 0; m < w->ln[0]; m++) {
        const g5_tr *t = &w->tr[w->lid[0][m]];
        *o++ = t->idx;
        o = g5_put16(o, t->val);
    }
    cnt = o++;
    *cnt = 0;
    for (j = 0; j < w->nlrows; j++) {   /* sufijos, solo filas escritas */
        r = w->lrows[j];
        u8 *ids = w->lid[r + 1], k = w->ln[r + 1], a, b;
        const g5_sfx *p = &w->sfx[r];
        if (!k)
            continue;
        for (a = 1; a < k; a++) {       /* MOVE por (x minimo, indice) */
            u8 id = ids[a];
            s16 q = g5_req(&w->tr[id], (s16)r);
            for (b = a; b > 0; b--) {
                const g5_tr *u = &w->tr[ids[b - 1]];
                s16 qu = g5_req(u, (s16)r);
                if (qu < q || (qu == q && u->idx <= w->tr[id].idx))
                    break;
                ids[b] = ids[b - 1];
            }
            ids[b] = id;
        }
        *o++ = (u8)r;
        *o++ = p->tipo;
        *o++ = p->h;
        *o++ = p->nop;
        *o++ = k;
        for (a = 0; a < k; a++) {
            const g5_tr *t = &w->tr[ids[a]];
            *o++ = t->idx;
            o = g5_put16(o, t->val);
        }
        (*cnt)++;
    }
    return (u16)(o - out);
}

#endif /* SPR_G5 */
