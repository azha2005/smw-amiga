/*
 * spr_gfx.c - rutinas de graficos de los sprites que ESCRIBEN la OAM como la
 * SNES (G8, docs/automatizar-9.2.md §0): $0300-$03FF (wm_OamSlot: X, Y,
 * tile, atributos) y $0460-$049F (wm_OamSize: bit 0 = bit 8 de la X, bit 1
 * = 16x16), en las mismas direcciones de ram[] que la SNES.
 *
 *   RexGfxRt (sprite_3-1.s) + GetDrawInfoBnk3 + FinishOAMWrite (sprite_1-1.s)
 *   SubSprGfx2Entry0/1 (sprite_1-main.s) + GetDrawInfoBnk1 + CODE_01A3DF
 *   el indice OAM de cada ranura (CODE_0180D2: DATA_07F000/DATA_07F0B4)
 *   y lo que los sprites portados hacen alrededor de SubSprGfx2Entry1:
 *   la nube del salto con giro (HandleSprSpinJump), _Spr0to13Gfx de una
 *   ficha (el Koopa sin caparazon $02), el tile fijo de la caja de mensaje
 *   $B9 y del Koopa deslizante $BD.
 *
 * Solo con SPR_OAM (msprite.h: lo define todo build sin NOOAM, es decir el
 * marioverify del PC). La Amiga lo activa con NOOAM + SPR_OAM: Mario
 * mantiene su OAM propia; rex_main_asm (logic68k.s) llama a rex_gfx en
 * la fase original. Las rutinas mutan pose, scratch y flags: corren en
 * la logica, antes de tomar la foto del render O5 (P35/P97/P98).
 *
 * Las tablas .DB vienen de tools/smwtabx.py (WANT_GFX, SMWTABX_GFX).
 *
 * El verificador (marioverify game) compara las entradas que escribe cada
 * ranura con la OAM grabada: spr_oam_first/spr_oam_n dicen cuales son
 * (indice OAM / 4 + 64 = ranura de la OAM, y cuantas).
 */
#include "msprite.h"
#ifdef SPR_OAM
#define SMWTABX_GFX
#include "gen/smwtabx.h"

/* wm_OamSlot.1 / .2 y wm_OamSize.1 / .2, indexados por Y (bytes) */
#define OAM_X(y)        ram[wm_OamSlot + (y)]
#define OAM_Y(y)        ram[wm_OamSlot + 1 + (y)]
#define OAM_TILE(y)     ram[wm_OamSlot + 2 + (y)]
#define OAM_PROP(y)     ram[wm_OamSlot + 3 + (y)]
#define OAM_SIZE(i)     ram[wm_OamSize + (i)]

u8 spr_oam_first[12], spr_oam_n[12];    /* lo que escribio cada ranura (verificador) */

static void oam_mark(u8 x, u8 y, u8 n)
{
    if (x < 12) { spr_oam_first[x] = y; spr_oam_n[x] = n; }
}

/* CODE_0180D2: el indice OAM de la ranura (TXA / ADC DATA_07F0B4,X / TAX /
   LDA DATA_07F000,X, todo de 8 bits). En la ROM DATA_07F0B4 va justo
   detras de DATA_07F000: con el ajuste de memoria $13 el indice pasa de
   180 y se lee de ahi. */
u8 spr_oam_index(u8 x)
{
    u8 i = (u8)(x + tg2_07F0B4[R8(wm_SpriteMemory)]);
    u8 v = i < sizeof tg2_07F000 ? tg2_07F000[i] : tg2_07F0B4[i - sizeof tg2_07F000];
    SETSPR(wm_SprOAMIndex, x, v);
    return v;
}

/* FinishOAMWriteRt (A = fichas - 1, Y = tamaño o $FF): la X alta de cada
   ficha (CODE_01B844) y la Y fuera de pantalla a $F0 (CODE_01C9BF) */
static void finish_oam_write(u8 x, u8 a, u8 ysz)
{
    u8 y = SPR(wm_SprOAMIndex, x), i, t, hi, c;
    u16 w;
    oam_mark(x, y, (u8)(a + 1));
    W8(m11, ysz);
    W8(m8, a);
    W8(m0, SPR(wm_SpriteYLo, x));
    W8(m6, (u8)(SPR(wm_SpriteYLo, x) - R8(wm_Bg1VOfs)));
    W8(m1, SPR(wm_SpriteYHi, x));
    W8(m2, SPR(wm_SpriteXLo, x));
    W8(m7, (u8)(SPR(wm_SpriteXLo, x) - R8(wm_Bg1HOfs)));
    W8(m3, SPR(wm_SpriteXHi, x));
    for (;;) {
        i = (u8)(y >> 2);
        if (NEG(R8(m11)))
            OAM_SIZE(i) &= 0x02;
        else
            OAM_SIZE(i) = R8(m11);
        t = (u8)(OAM_X(y) - R8(m7));        /* X de la ficha en el nivel */
        hi = NEG(t) ? 0xFF : 0x00;
        w = (u16)t + R8(m2);
        c = (u8)(w >> 8);
        W8(m4, (u8)w);
        W8(m5, (u8)(hi + R8(m3) + c));
        if ((u16)((R8(m4) | R8(m5) << 8) - R16(wm_Bg1HOfs)) >= 0x100)
            OAM_SIZE(i) |= 0x01;
        t = (u8)(OAM_Y(y) - R8(m6));        /* Y de la ficha en el nivel */
        hi = NEG(t) ? 0xFF : 0x00;
        w = (u16)t + R8(m0);
        c = (u8)(w >> 8);
        W8(m9, (u8)w);
        W8(m10, (u8)(hi + R8(m1) + c));
        if ((u16)((R8(m9) | R8(m10) << 8) + 0x10 - R16(wm_Bg1VOfs)) >= 0x100)
            OAM_Y(y) = 0xF0;
        y = (u8)(y + 4);
        W8(m8, (u8)(R8(m8) - 1));
        if (NEG(R8(m8)))
            break;
    }
}

/* RexGfxRt: dos fichas (cuerpo y cabeza; aplastado, dos de 8x8) */
void rex_gfx(u8 x)
{
    u8 y, i, idx, m2v, m3v;
    if (SPR(wm_SpriteDecTbl3, x))
        SETSPR(wm_SpriteGfxTbl, x, 5);
    if (SPR(wm_DisSprCapeContact, x))
        SETSPR(wm_SpriteGfxTbl, x, 2);
    if (!get_draw_info(x))                  /* GetDrawInfoBnk3: lejos, PLA PLA */
        return;
    y = spr_oam_index(x);                   /* LDY wm_SprOAMIndex,X */
    W8(m0, (u8)(SPR(wm_SpriteXLo, x) - R8(wm_Bg1HOfs)));
    W8(m1, (u8)(SPR(wm_SpriteYLo, x) - R8(wm_Bg1VOfs)));
    m3v = (u8)(SPR(wm_SpriteGfxTbl, x) << 1);
    W8(m3, m3v);
    m2v = SPR(wm_SpriteDir, x);
    W8(m2, m2v);
    for (i = 1; ; i--) {
        idx = (u8)(i | m3v);
        OAM_X(y) = (u8)(R8(m0) + tg2_RexTileDispX[m2v ? idx : (u8)(idx + 0x0C)]);
        OAM_Y(y) = (u8)(R8(m1) + tg2_RexTileDispY[idx]);
        OAM_TILE(y) = tg2_RexTiles[idx];
        OAM_PROP(y) = (u8)(tg2_RexGfxProp[m2v] | R8(wm_SpriteProp));
        OAM_SIZE(y >> 2) = m3v >= 0x0A ? 0x00 : 0x02;
        y = (u8)(y + 4);
        if (!i)
            break;
    }
    finish_oam_write(x, 1, 0xFF);
}

/* CODE_01A3DF: fuera de pantalla en vertical (bit 0: esta ficha, bit 1: la
   siguiente) -> X = $80 con el bit 8 puesto (x = $180) y tamaño 8x8.
   i = indice OAM / 4 */
static void oam_offscreen_vert(u8 x, u8 i)
{
    u8 v = SPR(wm_OffscreenVert, x);
    if (!v)
        return;
    if (v & 1) {
        OAM_SIZE(i) = 0x01;
        OAM_X((u8)(i << 2)) = 0x80;
    }
    if (v & 2) {
        OAM_SIZE(i + 1) = 0x01;
        OAM_X((u8)(i << 2) + 4) = 0x80;
    }
}

/* SubSprGfx2Entry0 (m4 = atributos extra, p. ej. $80 = volteado en Y) /
   SubSprGfx2Entry1 (m4 = 0): una ficha de 16x16 con el tile de
   SprTilemap[GfxTbl + SprTilemapOffset[numero]]. Devuelve 0 si
   GetDrawInfoBnk1 lo ve lejos: entonces no escribe la ficha, pero deja Y
   (el indice OAM), m0 y m1 como la ROM (CODE_01A3CB cae en _01A3CD), y el
   que llama sigue (la ROM vuelve a el, no a su llamador).
   OJO: SprTilemapOffset solo tiene entradas para los sprites $00-$53. Con
   un numero mayor la ROM lee lo que sigue a la tabla (otras tablas y
   codigo); los sprites portados que pasan por aca con numero >= $54 (la
   nube del salto con giro, $B9, $BD) escriben despues su propio tile, asi
   que ese tile no se ve nunca: el port deja 0. */
u8 sub_spr_gfx2(u8 x, u8 m4v)
{
    u8 y, n, t, a;
    u8 near;
    W8(m4, m4v);
    near = (u8)get_draw_info1(x);
    y = spr_oam_index(x);
    W8(m0, (u8)(SPR(wm_SpriteXLo, x) - R8(wm_Bg1HOfs)));
    W8(m1, (u8)(SPR(wm_SpriteYLo, x) - R8(wm_Bg1VOfs)));
    if (!near)
        return 0;
    W8(m2, SPR(wm_SpriteDir, x));
    n = SPR(wm_SpriteNum, x);
    t = 0;
    if (n < sizeof tg2_SprTilemapOffset) {
        u8 k = (u8)(SPR(wm_SpriteGfxTbl, x) + tg2_SprTilemapOffset[n]);
        if (k < sizeof tg2_SprTilemap)
            t = tg2_SprTilemap[k];
    }
    OAM_TILE(y) = t;
    OAM_X(y) = R8(m0);
    OAM_Y(y) = R8(m1);
    a = SPR(wm_SpritePal, x);
    if (!(SPR(wm_SpriteDir, x) & 1))
        a ^= 0x40;
    OAM_PROP(y) = (u8)(a | R8(m4) | R8(wm_SpriteProp));
    OAM_SIZE(y >> 2) = (u8)(0x02 | SPR(wm_OffscreenHorz, x));
    oam_offscreen_vert(x, (u8)(y >> 2));
    oam_mark(x, y, 1);
    return 1;
}

/* SubSprGfx2Entry1 y despues un tile fijo en la ficha (STA
   wm_OamSlot.1.Tile con Y = wm_SprOAMIndex): la caja de mensaje $B9
   ($C0) y el Koopa deslizante $BD ($86 / $E0). Lo escribe aunque el
   sprite este lejos, como la ROM. */
void spr_gfx2_tile(u8 x, u8 t)
{
    sub_spr_gfx2(x, 0);
    OAM_TILE(SPR(wm_SprOAMIndex, x)) = t;
}

/* HandleSprSpinJump (DecTbl1 != 0): SubSprGfx2Entry1 y la nube de humo */
void spin_jump_gfx(u8 x)
{
    u8 y, t;
    sub_spr_gfx2(x, 0);
    y = SPR(wm_SprOAMIndex, x);
    t = tg2_SpinSmoke[(SPR(wm_SpriteDecTbl1, x) >> 3) & 0x03];
    OAM_TILE(y) = t;
    OAM_PROP(y) = t;                        /* (asi en la ROM: STA y despues AND) */
    OAM_PROP(y) = (u8)(t & 0x30);
}

/* _Spr0to13Gfx de una ficha (Spr0to13Prop bit 6 = 0, el $02): girando
   (DecTbl5), la pose 2 y la direccion invertida solo para el dibujo
   (DecTbl5 >= 5); despues _DoneWithSprite la repone */
void spr013_gfx(u8 x)
{
    u8 d = SPR(wm_SpriteDir, x), t = SPR(wm_SpriteDecTbl5, x);
    if (t) {
        SETSPR(wm_SpriteGfxTbl, x, 2);
        SETSPR(wm_SpriteDir, x, (u8)(d ^ (t >= 5 ? 1 : 0)));
    }
    sub_spr_gfx2(x, 0);
    SETSPR(wm_SpriteDir, x, d);
}
#endif
