/*
 * g5plan.h - G2T fase B (docs/instrucciones-g2t-bc.md §3): el bloque de la
 * foto (g5_capture) y el plan de recargas COLOR17-31 del Rex (g5_plan).
 * Solo con -DSPR_G5 (que implica NOOAM + SPR_OAM). La especificacion es
 * tools/g2t_ref.py: este C la imita, nunca al reves.
 *
 * Todo lo que cruza entre el PC y el 68000 (el bloque y el plan) son bytes
 * en big endian con offsets fijos: el mismo volcado sirve a las dos
 * maquinas (tools/g5plan_verify.py lo compara byte a byte).
 */
#ifndef G5PLAN_H
#define G5PLAN_H

#include "mario.h"

#ifdef SPR_G5

#if defined(__VBCC__)
typedef long s32;
typedef unsigned long u32;
#else
#include <stdint.h>
typedef int32_t s32;
typedef uint32_t u32;
#endif

#define G5_ROWS     224         /* filas del copper (R = linea - $2C) */
#define G5_V0       0x2C        /* primera linea de la pantalla */
#define G5_HX0      0xA0        /* HSTART de x = 0 (mspr_draw, g0bench.control) */
#define G5_WIN      40          /* filas de Mario en el bloque (MSPR_LINES) */
#define G5_MAXREX   12          /* candidatos Rex (una ranura cada uno) */
#define G5_MAXT     16          /* fichas visibles por candidato */
#define G5_SPRW     (2 + 2 * G5_WIN + 2)    /* palabras por sprite (MSPR_WORDS) */

/* --- el bloque de la foto (g5_capture lo escribe, g5_plan lo lee) ---
   flags: bit 0 Mario visible (alguna pareja activa), bit 1 una fila de
   Mario fuera de la ventana de G5_WIN filas, bit 2 mas candidatos o
   fichas de los que caben. Envolventes de Mario: fila R = mrow + j
   (j < G5_WIN); mask[j] bit i = el indice i (1..15) se usa en R, y
   env[j][i-1] = primer x, ultimo x (inclusivos, 0..255). Las filas fuera
   de 0..223 no se guardan (mask 0), como g2t_ref.mario_amiga. */
#define G5B_FLAGS   0           /* u16 */
#define G5B_PAL     2           /* u8 R_PAL (0..7) */
#define G5B_NREX    3           /* u8 candidatos */
#define G5B_CAMX    4           /* u16 Bg1HOfs ($1A) */
#define G5B_CAMY    6           /* u16 Bg1VOfs ($1C) */
#define G5B_MROW    8           /* s16 fila R de j = 0 */
#define G5B_MASK    12          /* G5_WIN x u16 */
#define G5B_ENV     (G5B_MASK + 2 * G5_WIN)             /* G5_WIN x 15 x 2 B */
#define G5B_REX     (G5B_ENV + 30 * G5_WIN)
/* candidato: ranura u8, n u8, x u16 (ranura en el nivel), y u16, n x 5 B
   (las entradas OAM visibles: x, y, ficha, atributos, byte alto) */
#define G5R_SLOT    0
#define G5R_N       1
#define G5R_X       2
#define G5R_Y       4
#define G5R_E       6
#define G5R_SIZE    (G5R_E + 5 * G5_MAXT)
#define G5_BLK      (G5B_REX + G5_MAXREX * G5R_SIZE)

/* el bloque de la foto: Mario desde su buffer de sprites (4 sprites de
   G5_SPRW palabras, como mario_sprite/mspr_draw), R_PAL, camara y los
   Rex con fichas visibles de la OAM ampliada. Lee ram[]: corre en la
   logica (dc_capture), despues de mspr_draw. */
void g5_capture(u8 *blk, const u16 *spr);

#endif /* SPR_G5 */
#endif
