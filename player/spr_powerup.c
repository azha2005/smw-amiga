/*
 * spr_powerup.c - la seta $74 (_PowerUpRt de sprite_1-1.s, CODE_01C371 ..
 * TouchedPowerUp / GiveMarioMushroom) y lo que sale de los bloques
 * (_02887D .. GenSpriteFromBlk de sprite_2-clus.s). Cuarto sprite en fichero
 * propio (I1, ver msprite.h).
 *
 * Transcripcion instruccion por instruccion (P27), con A, X (= ranura x) e Y
 * anotados donde importan. Diferencias con la ROM:
 *   - el dibujo (CODE_01C61A: GetDrawInfoBnk1 + OAM) se reduce a
 *     GetDrawInfoBnk1 (los flags de fuera de pantalla; los tiles son de la
 *     9.2); SpriteProp (PHA/PLA y $10 = detras de la pantalla) es solo
 *     dibujo y no se porta;
 *   - GivePoints (la puntuacion y su sprite) es de la etapa 10: MEV_SPRITE;
 *   - la animacion de crecer de Mario ($71 = 02 con $1496 = $2F) es de la
 *     logica de Mario (P8): aca solo se escriben las variables, como la ROM;
 *   - sin portar (spr_unsup): el modo de nivel con el bit 6 (CODE_01C3F3), el
 *     $21 (moneda), las flores / estrella / pluma / 1-UP al tocarlas
 *     (GiveMarioFire..: P7, P10), el contenido de bloque >= 8 (P-switch,
 *     enredadera...) y la capa 2. El contenido 6 / 7 (moneda que gira,
 *     CODE_028A66) es de P9: no hace nada.
 *   - de msprite.c solo se despachan el $74 (powerup_main) y su init
 *     (powerup_init, InitPowerUp: el $74 que pone el nivel).
 * Las tablas .DB vienen de tools/smwtabx.py (WANT_POWERUP, SMWTABX_POWERUP):
 * solo este fichero las incluye (P78).
 */
#include "msprite.h"
#define SMWTABX_POWERUP
#include "gen/smwtabx.h"

#ifdef LOGIC68K
void spr_pos_axis_asm(u8 x, u8 o);      /* player/logic68k.s */
#define pw_axis(x) spr_pos_axis_asm((x), 0)
#else
/* SubSprYPosNoGrvty: la velocidad 4.4 a la posicion Y (como spr_pos_axis(x, 0)
   de msprite.c, que no es extern en el host) */
static void pw_axis(u8 x)
{
    u8 v = SPR(wm_SpriteSpeedY, x), c, hi, d;
    unsigned sum;
    if (!v) {
        W8(wm_SprPixelMove, 0);
        return;
    }
    sum = (unsigned)(u8)(v << 4) + SPR(wm_SpriteYAcc, x);
    SETSPR(wm_SpriteYAcc, x, (u8)sum);
    c = (u8)(sum >> 8);
    d = (u8)(v >> 4);
    hi = 0;
    if (d >= 8) { d |= 0xF0; hi = 0xFF; }
    sum = (unsigned)d + SPR(wm_SpriteYLo, x) + c;
    SETSPR(wm_SpriteYLo, x, (u8)sum);
    SETSPR(wm_SpriteYHi, x, (u8)(hi + SPR(wm_SpriteYHi, x) + (sum >> 8)));
    W8(wm_SprPixelMove, (u8)(d + c));
}
#endif

/* InitPowerUp: el $74 que pone el nivel nace "dentro" (State = 1: se mueve
   solo cuando deja de tocar bloques, CODE_01C3AE) */
void powerup_init(u8 x)
{
    SETSPR(wm_SpriteStatus, x, 0x08);       /* CallSpriteInit */
    SETSPR(wm_SpriteState, x, SPR(wm_SpriteState, x) + 1);
}

/* CODE_01C56F: A = 4, Y = MiscTbl5: los puntos (si no es un bonus de Yoshi)
   y el sonido */
static void pw_points(u8 x)
{
    if (!SPR(wm_SpriteMiscTbl5, x))
        mario_events |= MEV_SPRITE;         /* GivePoints (A = 4) */
    W8(wm_SoundCh1, 0x0A);
}

/* CODE_01C4AC: Mario toca el power-up (_01A80F + TouchedPowerUp) */
static void pw_touch(u8 x)
{
    u8 n, y, a;
    if (!spr_contact_a80f(x))               /* BCC _Return01C4AB */
        return;
    if (!NEG(SPR(wm_Tweaker167A, x))) {     /* BPL DefaultInteractR: ninguno de $74-$78 */
        spr_unsup();
        return;
    }
    if (SPR(wm_SpriteMiscTbl3, x) && SPR(wm_SpriteState, x))
        return;                             /* _Return01C4FA */
    if (SPR(wm_SpriteDecTbl2, x))
        return;
    if (SPR(wm_SpriteDecTbl1, x) >= 0x18)   /* _01C4BF */
        return;
    SETSPR(wm_SpriteStatus, x, 0);
    n = SPR(wm_SpriteNum, x);
    if ((u8)(n - 0x74) >= 5) {              /* $21 (moneda) y el resto: sin portar */
        spr_unsup();
        return;
    }
    /* TouchedPowerUp: A = SpriteNum; Y = (A - $74) * 4 | MarioPowerUp */
    y = (u8)(((u8)(n - 0x74) << 2) | R8(wm_MarioPowerUp));
    a = tp_ItemBox[y];                      /* ItemBoxSprite */
    if (a) {
        W8(wm_ItemInBox, a);
        W8(wm_SoundCh3, 0x0B);
    }
    switch (tp_GivePtr[y]) {                /* GivePowerPtrIndex -> HandlePowerUpPtrs */
    case 0:                                 /* GiveMarioMushroom (Y = 0: $1496) */
        W8(wm_MarioAnimation, 0x02);
        W8(wm_PlayerAnimTimer + y, 0x2F);
        W8(wm_SpritesLocked, 0x2F);
        pw_points(x);                       /* JMP CODE_01C56F */
        break;
    case 1:                                 /* CODE_01C56F */
        pw_points(x);
        break;
    default:                                /* estrella, pluma, flor, 1-UP: P7 / P10 */
        spr_unsup();
        break;
    }
}

/* _PowerUpRt (el $74), estado 8 */
void powerup_main(u8 x)
{
    u8 n, st;
    if (SPR(wm_SpriteMiscTbl8, x)) {        /* la baya de Yoshi comida: SubSprGfx2Entry1 */
        get_draw_info1(x);
        return;
    }
    pw_touch(x);                            /* CODE_01C371: JSR CODE_01C4AC */
    if (SPR(wm_SpriteMiscTbl5, x)) {        /* sale de Yoshi: sube */
        if (!R8(wm_SpritesLocked)) {
            SETSPR(wm_SpriteSpeedY, x, 0x10);
            pw_axis(x);
        }
        if (!(R8(wm_FrameB) & 0x0C))        /* PLA / RTS: sin dibujo */
            return;
        goto tail;                          /* _01C3AB */
    }
    if (SPR(wm_SpriteDecTbl1, x)) {         /* CODE_01C38F: sale del bloque */
        spr_obj_interact(x);                /* CODE_019140 */
        if (!R8(wm_SpritesLocked)) {
            SETSPR(wm_SpriteSpeedY, x, 0xFC);
            pw_axis(x);
        }
        goto tail;
    }
    /* CODE_01C3AE */
    if (R8(wm_SpritesLocked) || SPR(wm_SpriteStatus, x) == 0x0C)
        goto tail;
    n = SPR(wm_SpriteNum, x);
    SETSPR(wm_SpriteMiscTbl6, x, SPR(wm_SpriteMiscTbl6, x) + 1);
    SETSPR(wm_SpriteSpeedX, x, SPR(wm_SpriteDir, x) ? 0xF8 : 0x08);  /* CODE_018DBB */
    if (n == 0x75 && !SPR(wm_SpriteMiscTbl3, x))
        SETSPR(wm_SpriteSpeedX, x, 0);
    if (n != 0x76 && n != 0x21 && !SPR(wm_SpriteMiscTbl3, x))
        SETSPR(wm_SpriteSpeedX, x, (u8)(SPR(wm_SpriteSpeedX, x) << 1));   /* ASL */
    st = SPR(wm_SpriteState, x);
    if (st) {
        if (!NEG(st)) {
            spr_obj_interact(x);            /* CODE_019140 */
            if (!SPR(wm_SprObjStatus, x))
                SETSPR(wm_SpriteState, x, 0);
        }
    } else {                                /* CODE_01C3F3 */
        u8 lm = R8(wm_LevelMode);
        if (lm != 0xC1 && (lm & 0x40)) {    /* BIT / BVC: modo con el bit 6 */
            spr_unsup();
            return;
        }
        spr_update_pos(x);                  /* CODE_01C42C: SubUpdateSprPos */
        if (R8(wm_FrameA) & 0x03)           /* _01C42F */
            SETSPR(wm_SpriteSpeedY, x, SPR(wm_SpriteSpeedY, x) - 1);
    }
    sub_offscreen3(x);                      /* _01C437: SubOffscreen0Bnk1 */
    if (SPR(wm_SprObjStatus, x) & 0x08)     /* IsTouchingCeiling */
        SETSPR(wm_SpriteSpeedY, x, 0);
    if (SPR(wm_SprObjStatus, x) & 0x04) {   /* IsOnGround, CODE_01C44A */
        if (n == 0x21) {
            spr_unsup();                    /* la moneda */
            return;
        }
        SETSPR(wm_SpriteSpeedY, x,          /* SetSomeYSpeed */
               (NEG(SPR(wm_SprObjStatus, x)) || SPR(wm_SpriteSlopeTbl, x)) ? 0x18 : 0x00);
        if (SPR(wm_SpriteMiscTbl3, x) || n == 0x76)
            SETSPR(wm_SpriteSpeedY, x, 0xC8);
    }
    if (!(SPR(wm_SpriteDecTbl3, x) | SPR(wm_SpriteState, x))   /* _01C47E */
        && (SPR(wm_SprObjStatus, x) & 0x03)                    /* IsTouchingObjSide */
        && !SPR(wm_SpriteDecTbl5, x)) {                        /* FlipSpriteDir */
        SETSPR(wm_SpriteDecTbl5, x, 0x08);
        SETSPR(wm_SpriteSpeedX, x, (u8)-SPR(wm_SpriteSpeedX, x));
        SETSPR(wm_SpriteDir, x, SPR(wm_SpriteDir, x) ^ 1);
    }
tail:                                       /* _01C48D */
    if (SPR(wm_SpriteDecTbl1, x) < 0x36)
        get_draw_info1(x);                  /* CODE_01C61A: GetDrawInfoBnk1 + OAM */
}

/* _02887D: el contenido de un bloque (m5, los de DATA_01AE88 / el que pone el
   golpe de Mario) crea su sprite en la posicion del bloque (wm_BlockYPos =
   X, wm_BlockXPos = Y: P33). Devuelve la ranura creada, o 0xFF si no creo
   ninguna. Despues el $83 pone MiscTbl4 = 1 y, si es la flor, State = $FF */
u8 powerup_from_block(void)
{
    u8 c = R8(m5), x, y, n;
    if (c == 0 || c == 0x06 || c == 0x07)
        return 0xFF;                        /* nada / moneda que gira (P9) */
    if (c >= 0x08 || R8(wm_LayerInProcess)) {
        spr_unsup();                        /* CODE_0288DC con 8..: sin portar; capa 2 */
        return 0xFF;
    }
    /* GenSpriteFromBlk: la ultima ranura libre (X = $0B .. 0) */
    for (x = 0x0C; x-- > 0; )
        if (!SPR(wm_SpriteStatus, x))
            break;
    if (x >= 0x0C) {                        /* ninguna: reemplaza la $0A o la $0B */
        W8(wm_FullSprDelete, R8(wm_FullSprDelete) - 1);
        if (NEG(R8(wm_FullSprDelete)))
            W8(wm_FullSprDelete, 0x01);
        x = (u8)(R8(wm_FullSprDelete) + 0x0A);
    }
    W8(wm_TempTileGen, x);
    y = c;
    SETSPR(wm_SpriteStatus, x, tp_StatInBlk[c]);
    if (R8(wm_LooseYoshiFlag))
        y = (u8)(y + 0x11);
    W8(wm_CheckSprInter, y);
    if (y > 0x10)
        y = (u8)(y - 0x11);                 /* la copia sin usar de SpriteInBlock: igual */
    n = tp_InBlock[y];
    SETSPR(wm_SpriteNum, x, n);
    W8(m14, n);
    W8(wm_SoundCh3, (n >= 0x79 && n < 0x81) ? 0x03 : 0x02);
    spr_init_tables(x);                     /* JSL InitSpriteTables */
    SETSPR(wm_OffscreenHorz, x, SPR(wm_OffscreenHorz, x) + 1);
    SETSPR(wm_SpriteXLo, x, R8(wm_BlockYPos));          /* _028972 */
    SETSPR(wm_SpriteXHi, x, R8(wm_BlockYPos + 1));
    SETSPR(wm_SpriteYLo, x, R8(wm_BlockXPos));
    SETSPR(wm_SpriteYHi, x, R8(wm_BlockXPos + 1));
    /* CODE_0289D3 (n = $74..$78): ni $04, ni $3E, ni $2C -> CODE_028A11 */
    SETSPR(wm_SpriteDecTbl1, x, 0x3E);
    SETSPR(wm_SpriteSpeedY, x, 0xD0);       /* _028A18 */
    SETSPR(wm_SpriteDecTbl2, x, 0x2C);
    if (NEG(SPR(wm_Tweaker190F, x)))
        SETSPR(wm_SpriteDecTbl5, x, 0x10);
    return x;
}

/* DATA_01AE88[MiscTbl3 (+4 si Mario es chico)]: lo que suelta el bloque
   volador al golpearlo (sprite_1-1.s, FlyingBlock) */
u8 powerup_flying_content(u8 x)
{
    u8 y = SPR(wm_SpriteMiscTbl3, x);
    if (!R8(wm_MarioPowerUp))
        y = (u8)(y + 4);
    return tp_01AE88[y & 7];
}
