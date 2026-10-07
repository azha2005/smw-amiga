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
#ifdef __VBCC__
extern u8 logic68k_zero;              /* P47: base de RAM sin direccion absoluta */
#else
#define logic68k_zero 0
#endif

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
#ifdef LOGIC68K
/* Solo la Amiga usa el bucle de registros; el C sigue como referencia
   del PC/NOASM y oam68k_gate cruza todos los bytes de RAM. */
void finish_oam_write_asm(u8 x, u8 a, u8 ysz);
#define finish_oam_write finish_oam_write_asm
#else
static void finish_oam_write(u8 x, u8 a, u8 ysz)
{
    /* Los temporales $00-$0B de la ROM viven en variables locales y se
       escriben UNA vez al final, con el valor que la ROM les deja (la
       semantica de la RAM no cambia: regress.py cruza la RAM entera).
       m5:m4 = X del sprite (16 bits) + desplazamiento de la ficha con
       signo: es lo que hacen LDX #0 / BPL / DEX / ADC m2 / TXA / ADC m3. */
    u8 y = SPR(wm_SprOAMIndex, x), i, n = a;
    u8 s0 = SPR(wm_SpriteYLo, x), s1 = SPR(wm_SpriteYHi, x);
    u8 s2 = SPR(wm_SpriteXLo, x), s3 = SPR(wm_SpriteXHi, x);
    u8 s6 = (u8)(s0 - R8(wm_Bg1VOfs)), s7 = (u8)(s2 - R8(wm_Bg1HOfs));
    u16 bx = (u16)(s2 | s3 << 8), by = (u16)(s0 | s1 << 8);
    u16 hofs = R16(wm_Bg1HOfs), vofs = (u16)(R16(wm_Bg1VOfs) - 0x10);
    u16 lx, ly;
    oam_mark(x, y, (u8)(a + 1));
    for (;;) {
        i = (u8)(y >> 2);
        if (NEG(ysz))
            OAM_SIZE(i) &= 0x02;
        else
            OAM_SIZE(i) = ysz;
        lx = (u16)(bx + (u16)(s16)(s8)(u8)(OAM_X(y) - s7));   /* X de la ficha en el nivel */
        if ((u16)(lx - hofs) >= 0x100)
            OAM_SIZE(i) |= 0x01;
        ly = (u16)(by + (u16)(s16)(s8)(u8)(OAM_Y(y) - s6));   /* Y de la ficha en el nivel */
        if ((u16)(ly - vofs) >= 0x100)
            OAM_Y(y) = 0xF0;
        y = (u8)(y + 4);
        n = (u8)(n - 1);
        if (NEG(n))
            break;
    }
    W8(m0, s0);
    W8(m1, s1);
    W8(m2, s2);
    W8(m3, s3);
    W8(m4, (u8)lx);
    W8(m5, (u8)(lx >> 8));
    W8(m6, s6);
    W8(m7, s7);
    W8(m8, n);
    W8(m9, (u8)ly);
    W8(m10, (u8)(ly >> 8));
    W8(m11, ysz);
}
#endif

/* RexGfxRt: dos fichas (cuerpo y cabeza; aplastado, dos de 8x8) */
#ifndef LOGIC68K
/* El PC/NOASM conserva esta referencia; _rex_gfx en logic68k.s hace
   exactamente las mismas escrituras con indices y coordenadas locales. */
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
#endif

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
static u8 sub_spr_gfx2_at(u8 x, u8 m4v)
{
    u8 y, n, t, a;
    u8 near;
    W8(m4, m4v);
    near = (u8)get_draw_info1(x);
    y = SPR(wm_SprOAMIndex, x);
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

u8 sub_spr_gfx2(u8 x, u8 m4v)
{
    spr_oam_index(x);
    return sub_spr_gfx2_at(x, m4v);
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

/* CODE_02D5E4: las dieciseis fichas de Banzai, en orden inverso. */
void banzai_gfx(u8 x)
{
    u8 y, i;
    spr_oam_index(x);
    if (!get_draw_info(x)) return;
    y = SPR(wm_SprOAMIndex, x);
    W8(m0, (u8)(SPR(wm_SpriteXLo, x) - R8(wm_Bg1HOfs)));
    W8(m1, (u8)(SPR(wm_SpriteYLo, x) - R8(wm_Bg1VOfs)));
    for (i = 15; ; i--) {
        OAM_X(y) = (u8)(R8(m0) + tg2_DATA_02D5A4[i]);
        OAM_Y(y) = (u8)(R8(m1) + tg2_DATA_02D5B4[i]);
        OAM_TILE(y) = tg2_BanzaiBillTiles[i];
        OAM_PROP(y) = tg2_DATA_02D5D4[i];
        y = (u8)(y + 4);
        if (!i) break;
    }
    finish_oam_write(x, 15, 2);
}

/* SubSprGfx0Entry0: cuatro fichas de 8x8, A = selector de volteo. */
static void sub_spr_gfx0(u8 x, u8 flip)
{
    u8 y, i;
    W8(m5, flip);
    W8(m15, 0);
    if (!get_draw_info1(x)) return;
    W8(m0, (u8)(SPR(wm_SpriteXLo, x) - R8(wm_Bg1HOfs)));
    W8(m1, (u8)(SPR(wm_SpriteYLo, x) - R8(wm_Bg1VOfs)));
    W8(m2, (u8)((SPR(wm_SpriteGfxTbl, x) << 2) + tg2_SprTilemapOffset[SPR(wm_SpriteNum, x)]));
    W8(m3, SPR(wm_SpritePal, x) | R8(wm_SpriteProp));
    y = SPR(wm_SprOAMIndex, x);
    for (i = 3; ; i--) {
        W8(m4, i);
        OAM_X(y) = (u8)(R8(m0) + tg2_GeneralSprDispX[i]);
        OAM_Y(y) = (u8)(R8(m1) + tg2_GeneralSprDispY[i]);
        OAM_TILE(y) = tg2_SprTilemap[(u8)(R8(m2) + i)];
        OAM_PROP(y) = tg2_GeneralSprGfxProp[(u8)((flip << 2) + i)] | R8(m3);
        y = (u8)(y + 4);
        if (!i) break;
    }
    W8(m4, 0xFF);
    finish_oam_write(x, 3, 0);
}

/* CODE_02E0CD: cabeza 16x16 y tallo de cuatro fichas; restaura Y y prioridad. */
void piranha_gfx(u8 x)
{
    u8 first = spr_oam_index(x), prop = R8(wm_SpriteProp), n;
    u16 sy = (u16)(SPR(wm_SpriteYLo, x) | SPR(wm_SpriteYHi, x) << 8);
    W8(wm_SpriteProp, 0x10);
    SETSPR(wm_SpriteGfxTbl + logic68k_zero, x, ((SPR(wm_SpriteMiscTbl6, x) & 8) >> 2) ^ 2);
    sub_spr_gfx2_at(x, 0);
    n = spr_oam_n[x];
    SETSPR(wm_SprOAMIndex, x, (u8)(first + 4));
    SETSPR(wm_SpriteGfxTbl + logic68k_zero, x, ((SPR(wm_SpriteMiscTbl3, x) & 4) >> 2) + 1);
    SETSPR(wm_SpriteYLo, x, (u8)(sy + 8));
    SETSPR(wm_SpriteYHi, x, (u16)(sy + 8) >> 8);
    SETSPR(wm_SpritePal, x, 0x0A);
    sub_spr_gfx0(x, 1);
    if (spr_oam_n[x] == 4) oam_mark(x, first, 5);
    else if (n) oam_mark(x, first, 1);
    SETSPR(wm_SpriteYLo, x, (u8)sy);
    SETSPR(wm_SpriteYHi, x, sy >> 8);
    W8(wm_SpriteProp, prop);
}

/* CODE_01C12D: cinta sin cortar, tres fichas de 8x8. */
void goal_gfx(u8 x)
{
    u8 y, i;
    spr_oam_index(x);
    if (!get_draw_info1(x)) return;
    y = SPR(wm_SprOAMIndex, x);
    W8(m0, (u8)(SPR(wm_SpriteXLo, x) - R8(wm_Bg1HOfs)));
    W8(m1, (u8)(SPR(wm_SpriteYLo, x) - R8(wm_Bg1VOfs)));
    for (i = 0; i < 3; i++) {
        OAM_X(y) = (u8)(R8(m0) - 8 + (i << 3));
        OAM_Y(y) = (u8)(R8(m1) + 8);
        OAM_TILE(y) = i ? 0xD5 : 0xD4;
        OAM_PROP(y) = 0x32;
        y = (u8)(y + 4);
    }
    finish_oam_write(x, 2, 0);
}

/* CODE_019806 / CODE_019A2A: caparazon y sus dos fichas de humo. */
void shell_gfx(u8 x, u8 kicked)
{
    u8 first = spr_oam_index(x), y, t, a, n, phase = (R8(wm_FrameB) >> 2) & 3;
    a = first ? 6 : 8;
    if (kicked) {
        SETSPR(wm_SpriteDecTbl3, x, SPR(wm_SpriteState, x));
        a = tg2_ShellAniTiles[phase];
    }
    SETSPR(wm_SpriteGfxTbl, x, a);
    y = first ? (u8)(first + 8) : first;
    SETSPR(wm_SprOAMIndex, x, y);
    sub_spr_gfx2_at(x, 0);
    n = spr_oam_n[x];
    SETSPR(wm_SprOAMIndex, x, first);
    if (!NEG(R8(wm_MapData + 0x49)) && a == 6) { /* OwLvFlags.Lv125 */
        t = SPR(wm_SpriteDecTbl3, x);
        if (t || ((t = SPR(wm_SpriteDecTbl1, x)) && t < 0x30)) {
            if (t < 0x30 || SPR(wm_SpriteDecTbl3, x)) {
                u16 w = (u16)OAM_X((u8)(first + 8)) + (t & 1);
                if (w < 0x100) OAM_X((u8)(first + 8)) = (u8)w;
            }
        }
        if ((SPR(wm_SpriteDecTbl3, x) || SPR(wm_SpriteDecTbl1, x))
            && SPR(wm_SpriteNum, x) != 0x11
            && !(SPR(wm_OffscreenHorz, x) | SPR(wm_OffscreenVert, x))) {
            W8(m0, (SPR(wm_SpritePal, x) & 0x80) ? 0 : 8);
            OAM_X(first) = (u8)(OAM_X((u8)(first + 8)) + 2);
            OAM_X((u8)(first + 4)) = (u8)(OAM_X(first) + 4);
            OAM_Y(first) = OAM_Y((u8)(first + 4)) = (u8)(OAM_Y((u8)(first + 8)) + R8(m0));
            OAM_TILE(first) = OAM_TILE((u8)(first + 4)) = (R8(wm_FrameB) & 0xF8) ? 0x64 : 0x4D;
            OAM_PROP(first) = OAM_PROP((u8)(first + 4)) = R8(wm_SpriteProp);
            OAM_SIZE(first >> 2) = OAM_SIZE((first >> 2) + 1) = 0;
            n = 3;
        }
    }
    if (n) oam_mark(x, first, first ? 3 : 1);
    if (kicked) {
        SETSPR(wm_SpriteDecTbl3, x, 0);
        OAM_PROP((u8)(first + 8)) ^= tg2_ShellGfxProp[phase];
    }
}

/* CODE_02C81A: cabeza, cuerpo y manos del Chuck $95; cinco ranuras. */
void chuck_gfx(u8 x)
{
    u8 pose, dir, y, j, idx, h, off, body, shift = 0;
    spr_oam_index(x);
    if (!get_draw_info(x)) return;
    W8(m0, (u8)(SPR(wm_SpriteXLo, x) - R8(wm_Bg1HOfs)));
    W8(m1, (u8)(SPR(wm_SpriteYLo, x) - R8(wm_Bg1VOfs)));
    pose = SPR(wm_SpriteGfxTbl, x);
    W8(m7, 0);
    W8(m4, pose);
    if (pose == 9 && SPR(wm_SpriteDecTbl1, x) >= 0x20) {
        shift = (SPR(wm_SpriteDecTbl1, x) - 0x20) >> 5;
        W8(m7, shift);
        /* El ultimo LSR deja su carry al ADC m0,#0. */
        W8(m0, R8(m0) + (((SPR(wm_SpriteDecTbl1, x) - 0x20) >> 1) & 1));
    }
    h = SPR(wm_SpriteMiscTbl3, x);
    dir = SPR(wm_SpriteDir, x);
    W8(m2, h); W8(m3, dir);
    W8(m8, SPR(wm_SpritePal, x) | R8(wm_SpriteProp));
    W8(m5, SPR(wm_SprOAMIndex, x));
    y = (u8)(R8(m5) + tg2_DATA_02C864[pose]);
    off = tg2_DATA_02C830[pose];
    OAM_X(y) = (u8)(R8(m0) + (dir ? off : (u8)-off));
    OAM_Y(y) = (u8)(R8(m1) + tg2_DATA_02C84A[pose] - shift);
    OAM_PROP(y) = tg2_DATA_02C885[h] | R8(m8);
    OAM_TILE(y) = tg2_ChuckHeadTiles[h]; OAM_SIZE(y >> 2) = 2;
    W8(m6, dir ? 0 : 0x40);
    body = dir ? pose : (u8)(pose + 0x1A);
    y = (u8)(R8(m5) + tg2_DATA_02CA0D[pose]);
    OAM_X(y) = (u8)(R8(m0) + tg2_DATA_02C909[body]);
    OAM_X((u8)(y + 4)) = (u8)(R8(m0) + tg2_DATA_02C93D[body]);
    OAM_Y(y) = (u8)(R8(m1) + tg2_DATA_02C971[pose]);
    OAM_Y((u8)(y + 4)) = R8(m1);
    OAM_TILE(y) = tg2_ChuckBody1[pose]; OAM_TILE((u8)(y + 4)) = tg2_ChuckBody2[pose];
    OAM_PROP(y) = (R8(m8) | R8(m6)) ^ tg2_DATA_02C9BF[pose];
    OAM_PROP((u8)(y + 4)) = (R8(m8) | R8(m6)) ^ tg2_DATA_02C9D9[pose];
    OAM_SIZE(y >> 2) = tg2_DATA_02C9F3[pose]; OAM_SIZE((y >> 2) + 1) = 2;
    y = R8(m5);
    if (pose == 6 || pose == 7) {
        idx = pose - 6;
        for (j = 0; j < 2; j++) {
            OAM_X(y) = (u8)(R8(m0) + (j ? tg2_DATA_02CA95[idx] : tg2_DATA_02CA93[idx]));
            OAM_Y(y) = (u8)(R8(m1) + tg2_DATA_02CA99[idx]);
            OAM_TILE(y) = tg2_ClappinChuckTiles[idx];
            OAM_PROP(y) = R8(m8) | (j ? 0x40 : 0);
            OAM_SIZE(y >> 2) = tg2_DATA_02CA9B[idx]; y = (u8)(y + 4);
        }
    } else if (pose == 18 || pose == 19) {
        for (j = 0; j < 2; j++) {
            OAM_X(y) = (u8)(R8(m0) + ((dir << 3) ^ (j ? 0 : 8)));
            OAM_Y(y) = (u8)(R8(m1) - 8); OAM_TILE(y) = 0x1C + j;
            OAM_PROP(y) = tg2_ChuckGfxProp[dir] | R8(wm_SpriteProp);
            OAM_SIZE(y >> 2) = 0; y = (u8)(y + 4);
        }
    } else if (pose >= 20) {
        W8(m2, pose); idx = (u8)(pose + (dir ? 0 : 6));
        y = (u8)(R8(m5) + 8);
        OAM_X(y) = (u8)(R8(m0) + tg2_DATA_02CB41[idx - 20]);
        off = tg2_DATA_02CB41[pose - 8];
        if (off) {
            OAM_Y(y) = (u8)(R8(m1) + off); OAM_TILE(y) = 0xAD;
            OAM_PROP(y) = 9 | R8(wm_SpriteProp); OAM_SIZE(y >> 2) = 0;
        }
    }
    finish_oam_write(x, 4, 0xFF);
}
#endif
