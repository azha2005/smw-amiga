/* B2bis: proyectar una vez por foto, despues de recortar las mascaras.
 * El formato materializado es el de la frontera B2/B3: g5_mario_mask/span
 * leen como siempre. Los campos del Rex no se tocan; no hay RAM viva. */
#include "g5env.h"
#ifdef SPR_G5
#define EW(p) ((u16)((u16)(p)[0] << 8 | (p)[1]))
#define EP(p,v) ((p)[0] = (u8)((u16)(v) >> 8), (p)[1] = (u8)(v))
/* La tabla solo contiene conteos de bits de bytes, nunca assets. */
const u16 g5env_bounds[256] = {
    0xFFFF, 0x0707, 0x0606, 0x0607, 0x0505, 0x0507, 0x0506, 0x0507,
    0x0404, 0x0407, 0x0406, 0x0407, 0x0405, 0x0407, 0x0406, 0x0407,
    0x0303, 0x0307, 0x0306, 0x0307, 0x0305, 0x0307, 0x0306, 0x0307,
    0x0304, 0x0307, 0x0306, 0x0307, 0x0305, 0x0307, 0x0306, 0x0307,
    0x0202, 0x0207, 0x0206, 0x0207, 0x0205, 0x0207, 0x0206, 0x0207,
    0x0204, 0x0207, 0x0206, 0x0207, 0x0205, 0x0207, 0x0206, 0x0207,
    0x0203, 0x0207, 0x0206, 0x0207, 0x0205, 0x0207, 0x0206, 0x0207,
    0x0204, 0x0207, 0x0206, 0x0207, 0x0205, 0x0207, 0x0206, 0x0207,
    0x0101, 0x0107, 0x0106, 0x0107, 0x0105, 0x0107, 0x0106, 0x0107,
    0x0104, 0x0107, 0x0106, 0x0107, 0x0105, 0x0107, 0x0106, 0x0107,
    0x0103, 0x0107, 0x0106, 0x0107, 0x0105, 0x0107, 0x0106, 0x0107,
    0x0104, 0x0107, 0x0106, 0x0107, 0x0105, 0x0107, 0x0106, 0x0107,
    0x0102, 0x0107, 0x0106, 0x0107, 0x0105, 0x0107, 0x0106, 0x0107,
    0x0104, 0x0107, 0x0106, 0x0107, 0x0105, 0x0107, 0x0106, 0x0107,
    0x0103, 0x0107, 0x0106, 0x0107, 0x0105, 0x0107, 0x0106, 0x0107,
    0x0104, 0x0107, 0x0106, 0x0107, 0x0105, 0x0107, 0x0106, 0x0107,
    0x0000, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0004, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0003, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0004, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0002, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0004, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0003, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0004, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0001, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0004, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0003, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0004, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0002, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0004, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0003, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
    0x0004, 0x0007, 0x0006, 0x0007, 0x0005, 0x0007, 0x0006, 0x0007,
};

void g5env_bind(u8 *blk, const u8 *spr, const u8 *data)
{
    u16 pos, ctl, j, height = EW(data), cols = EW(data + 2), mm, bits;
    s16 x, row;
    u8 idx, first, last, u, color, *env;
    u16 count, loc, a, b, c, d;
    const u8 *q;
    u32 clip = 0xFFFFFFFF, raw, tail;
    const u8 *p;
    EP(blk + 10, 0);                     /* control materializado, sin tag disperso */
    for (j = 0; j < G5_WIN; j++)
        EP(blk + G5B_MASK + 2 * j, 0);
    if (!height) {
        EP(blk + G5B_MROW, 0);
        return;
    }
    if (!EW(spr) && !EW(spr + 2))
        spr += 336;
    pos = EW(spr); ctl = EW(spr + 2);
    row = (s16)(((pos >> 8) | ((ctl & 4) << 6)) - G5_V0);
    x = (s16)(((pos & 255) << 1 | (ctl & 1)) - G5_HX0);
    EP(blk + G5B_MROW, row);
    if (x <= -32 || x >= 256)
        return;
    if (x < 0)
        clip >>= (u16)-x;
    if (x > 224)
        clip <<= (u16)(x - 224);
    p = data + 4;
    env = blk + G5B_ENV;
    for (j = 0; j < height; j++, row++, p += cols == 4 ? 0 : cols == 1 ? 30 : 62, env += 30) {
#ifndef __VBCC__
        /* En 68000 el formato 4 y su recorte los resuelve siempre ASM.
         * Este camino por pixels es solo el control independiente del PC. */
        if (cols == 4) {
            mm = EW(p); count = (u16)(EW(p + 2) + 1);
            q = p + 4; p = q + 4 * count;
            if (row < 0 || row >= G5_ROWS)
                continue;
            if (x >= 0 && x <= 240) {
                while (count--) {
                    loc = EW(q); q += 2;
                    env[loc] = (u8)(x + q[0]);
                    env[loc + 1] = (u8)(x + q[1]); q += 2;
                }
                EP(blk + G5B_MASK + 2 * j, mm);
                continue;
            }
            /* Control independiente del fallback asm: volver a leer DATA
             * de la foto, nunca ajustar extremos a traves de un hueco. */
            a = EW(spr + 4 + 4 * j); b = EW(spr + 6 + 4 * j);
            c = EW(spr + 172 + 4 * j); d = EW(spr + 174 + 4 * j);
        }
#endif
        if (row < 0 || row >= G5_ROWS)
            continue;
        mm = 0;
        for (idx = 1, bits = 2; idx < 16; idx++, bits = (u16)(bits << 1)) {
#ifndef __VBCC__
            if (cols == 4) {
                raw = 0;
                for (u = 0; u < 16; u++) {
                    color = (u8)(((a >> (15 - u)) & 1) | (((b >> (15 - u)) & 1) << 1) |
                                 (((c >> (15 - u)) & 1) << 2) | (((d >> (15 - u)) & 1) << 3));
                    if (color == idx)
                        raw |= (u32)1 << (31 - u);
                }
            } else
#endif
            if (cols == 1) {
                raw = (u32)EW(p + 2 * (idx - 1)) << 16;
            } else {
                if (!(EW(p) & bits))
                    continue;
                raw = ((u32)EW(p + 2 + 4 * (idx - 1)) << 16) | EW(p + 4 + 4 * (idx - 1));
            }
            raw &= clip;
            if (!raw)
                continue;
            mm |= bits;
            tail = raw; first = last = 0;
            while (!(raw >> 24)) { first += 8; raw <<= 8; }
            first += (u8)(g5env_bounds[(u8)(raw >> 24)] >> 8);
            while (!(tail & 255)) { last += 8; tail >>= 8; }
            last += (u8)(7 - (g5env_bounds[(u8)tail] & 255));
            env[2 * (idx - 1)] = (u8)(x + first);
            env[2 * (idx - 1) + 1] = (u8)(x + 31 - last);
        }
        EP(blk + G5B_MASK + 2 * j, mm);
    }
}
#endif
