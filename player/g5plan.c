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

#endif /* SPR_G5 */
