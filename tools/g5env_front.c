/* Arnes B2b-4: llama a las dos funciones reales en todas las filas.
 * Los callbacks permiten usar el mismo arnes en gcc y sobre el logicbench
 * de produccion, sin una copia de las funciones que se comprueban. */
#include "g5plan.h"
typedef u16 (*g5_mask_fn)(const u8 *, s16);
typedef void (*g5_span_fn)(const u8 *, s16, u8, u8 *, u8 *);

void g5env_front(const u8 *blk, g5_mask_fn mask, g5_span_fn span, u8 *out)
{
    s16 r;
    u8 idx;
    u16 mm, bit;
    for (r = 0; r < G5_ROWS; r++, out += 32) {
        mm = mask(blk, r);
        out[0] = (u8)(mm >> 8);
        out[1] = (u8)mm;
        for (idx = 1, bit = 2; idx < 16; idx++, bit = (u16)(bit << 1)) {
            out[2 * idx] = out[2 * idx + 1] = 0;
            if (mm & bit)
                span(blk, r, idx, out + 2 * idx, out + 2 * idx + 1);
        }
    }
}
