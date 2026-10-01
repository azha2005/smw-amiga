/*
 * spr_chuck.c - Clappin' Chuck (sprite $95), ChucksMain de sprite_2-1.s
 * (CODE_02C1F3..CODE_02C81A) y InitClappinChuck de sprite_1-main.s. Segundo
 * sprite en fichero propio (I1, ver msprite.h). Los otros Chucks comparten
 * ChucksMain; aca va lo que usa el $95: estados 8 (salta y aplaude), 3
 * (golpeado), 2 (se recupera), 1 (persigue a Mario) y 0 (camina). Los demas
 * estados de ChuckPtrs (4-7, 9-12) no los alcanza el $95: spr_unsup().
 *
 * Transcripcion instruccion por instruccion (P27). Diferencias con la ROM:
 *   - el dibujo (CODE_02C81A) se reduce a GetDrawInfo2 (los flags de fuera
 *     de pantalla); los tiles son de la 9.2;
 *   - DisplayContactGfx, GivePoints y HurtMario son eventos de Mario
 *     (MEV_SPRITE, MEV_HURT), como en el Rex;
 *   - sin portar (spr_unsup): ShatterBlock (el Chuck con StompImmune contra
 *     un bloque 1E/2E), la estrella en el contacto no lleva la puntuacion.
 *   - GetRand (CODE_01AD07) corre sobre ram[] ($148B..$148E); los
 *     oraculos no graban el estado del azar (siempre 0), asi que lo que
 *     depende de el (la duracion del estado 0) no esta verificado.
 * Las tablas .DB vienen de tools/smwtabx.py (WANT_CHUCK, SMWTABX_CHUCK):
 * solo este fichero las incluye (P78).
 */
#include "msprite.h"
#define SMWTABX_CHUCK
#include "gen/smwtabx.h"

#ifdef LOGIC68K
void spr_pos_axis_asm(u8 x, u8 o);      /* player/logic68k.s */
#define chuck_axis spr_pos_axis_asm
#else
/* UpdateYPosNoGrvty2 (con o = $0C, UpdateXPosNoGrvty2): la velocidad 4.4 a
   la posicion; las tablas X estan $0C bytes despues de las Y. Igual que
   spr_pos_axis de msprite.c */
static void chuck_axis(u8 x, u8 o)
{
    u8 v = SPR(wm_SpriteSpeedY + o, x), c, hi, d;
    unsigned sum;
    if (!v) {
        W8(wm_SprPixelMove, 0);
        return;
    }
    sum = (unsigned)(u8)(v << 4) + SPR(wm_SpriteYAcc + o, x);
    SETSPR(wm_SpriteYAcc + o, x, (u8)sum);
    c = (u8)(sum >> 8);
    d = (u8)(v >> 4);
    hi = 0;
    if (d >= 8) { d |= 0xF0; hi = 0xFF; }
    sum = (unsigned)d + SPR(wm_SpriteYLo + o, x) + c;
    SETSPR(wm_SpriteYLo + o, x, (u8)sum);
    SETSPR(wm_SpriteYHi + o, x, (u8)(hi + SPR(wm_SpriteYHi + o, x) + (sum >> 8)));
    W8(wm_SprPixelMove, (u8)(d + c));
}
#endif

/* CODE_02D4FA (SubHorzPos de este banco): con la X de Mario YA movida
   (wm_MarioXPos; el SubHorizPos del banco 1 usa wm_PlayerXPosLv). m15 = el
   byte bajo de la diferencia, devuelve Y = 1 si Mario esta a la izquierda */
static u8 chuck_horz(u8 x)
{
    u16 d = (u16)(R16(wm_MarioXPos) - (SPR(wm_SpriteXLo, x) | SPR(wm_SpriteXHi, x) << 8));
    W8(m15, (u8)d);
    return (u8)((d & 0x8000) ? 1 : 0);
}

/* CODE_02D50C (SubVertPos): igual con la Y; m14 */
static u8 chuck_vert(u8 x)
{
    u16 d = (u16)(R16(wm_MarioYPos) - (SPR(wm_SpriteYLo, x) | SPR(wm_SpriteYHi, x) << 8));
    W8(m14, (u8)d);
    return (u8)((d & 0x8000) ? 1 : 0);
}

/* GetRand / CODE_01AD07 (dos pasos, Y = 1 y Y = 0: $148E y $148D); deja en A
   el segundo ($148D = wm_RandomByte1) */
static u8 chuck_rand(void)
{
    u8 i, lo, hi, c;
    for (i = 0; i < 2; i++) {
        lo = R8(wm_RandomByteNext);
        lo = (u8)((u8)(lo << 2) + lo + 1);              /* ASL ASL / SEC / ADC */
        W8(wm_RandomByteNext, lo);
        hi = R8(wm_RandomByteNext + 1);
        c = (u8)(hi >> 7);                              /* ASL: el acarreo */
        hi = (u8)(hi << 1);
        if (c == ((hi >> 5) & 1))                       /* BIT #$20: INC si C == bit 5 */
            hi++;
        W8(wm_RandomByteNext + 1, hi);
        W8(i ? wm_RandomByte2 : wm_RandomByte1, hi ^ lo);
    }
    return R8(wm_RandomByte1);
}

/* CODE_02C556: mira a Mario */
static void chuck_face(u8 x)
{
    u8 y = chuck_horz(x);
    SETSPR(wm_SpriteDir, x, y);
    SETSPR(wm_SpriteMiscTbl3, x, tc_02C639[y]);
}

/* CODE_02C579 (_02C579): se para */
static void chuck_stop(u8 x)
{
    SETSPR(wm_SpriteSpeedX, x, 0);
    SETSPR(wm_SpriteSpeedY, x, 0);
}

/* CODE_02C810: HurtMario (sin Yoshi). HurtMario no hace nada con Mario en
   una animacion, herido, con estrella o en el final del nivel */
static void chuck_hurt(void)
{
    if (R8(wm_OnYoshi))
        return;
    if (R8(wm_MarioAnimation) | R8(wm_PlayerHurtTimer) | R8(wm_StarPowerTimer) | R8(wm_EndLevelTimer))
        return;
    mario_events |= MEV_HURT;
    spr_unsup();
}

/* _02C7B1: muere (estrella o cuarto pisoton); GivePoints es de la etapa 10 */
static void chuck_die(u8 x)
{
    SETSPR(wm_SpriteSpeedX, x, 0);
    SETSPR(wm_SpriteStatus, x, 0x02);
    W8(wm_SoundCh1, 0x03);
    mario_events |= MEV_SPRITE;
}

/* CODE_02C79D: el contacto con Mario */
static void chuck_contact(u8 x)
{
    if (SPR(wm_SpriteDecTbl4, x))
        return;
    if (!mario_spr_interact(x))                 /* JSL MarioSprInteract: BCC */
        return;
    if (R8(wm_StarPowerTimer)) {
        SETSPR(wm_SpriteSpeedY, x, 0xD0);
        chuck_die(x);
        return;
    }
    chuck_vert(x);
    if (!NEG((u8)(R8(m14) - 0xEC))) {           /* CMP #$EC / BPL CODE_02C810 */
        chuck_hurt();
        return;
    }
    SETSPR(wm_SpriteDecTbl4, x, 0x05);          /* el pisoton */
    W8(wm_SoundCh1, 0x02);
    mario_events |= MEV_SPRITE;                 /* DisplayContactGfx */
    boost_mario();
    SETSPR(wm_SpriteDecTbl6, x, 0);
    if (SPR(wm_SpriteState, x) == 3)
        return;
    SETSPR(wm_SpriteMiscTbl4, x, SPR(wm_SpriteMiscTbl4, x) + 1);
    if (SPR(wm_SpriteMiscTbl4, x) >= 3) {
        SETSPR(wm_SpriteSpeedY, x, 0);
        chuck_die(x);
        return;
    }
    W8(wm_SoundCh3, 0x28);                      /* CODE_02C7F6: golpeado */
    SETSPR(wm_SpriteState, x, 3);
    SETSPR(wm_SpriteDecTbl1, x, 3);
    SETSPR(wm_SpriteMiscTbl6, x, 0);
    W8(wm_MarioSpeedX, tc_02C79B[chuck_horz(x)]);
}

/* CODE_02C628 */
static void chuck_dectbl5(u8 x)
{
    SETSPR(wm_SpriteDecTbl5, x, 0x08);
}

/* CODE_02C63B, estado 0: camina de un lado a otro; si Mario esta cerca, lo
   mira y pasa al estado 2 */
static void chuck_st0(u8 x)
{
    u8 a, y;
    SETSPR(wm_SpriteGfxTbl, x, 3);
    SETSPR(wm_SprStompImmuneTbl, x, 0);
    if (!(SPR(wm_SpriteDecTbl1, x) & 0x0F)) {
        chuck_vert(x);
        if ((u8)(R8(m14) + 0x28) < 0x50) {
            chuck_face(x);                      /* CODE_02C556 */
            SETSPR(wm_SprStompImmuneTbl, x, SPR(wm_SprStompImmuneTbl, x) + 1);
            goto st2;
        }
    }
    if (!SPR(wm_SpriteDecTbl1, x)) {            /* CODE_02C668 */
        SETSPR(wm_SpriteDir, x, SPR(wm_SpriteDir, x) ^ 1);
        goto st2;
    }
    if (!(R8(wm_FrameB) & 0x03)) {              /* CODE_02C677 */
        y = SPR(wm_SpriteMiscTbl5, x) & 0x01;
        a = (u8)(SPR(wm_SpriteMiscTbl7, x) + tc_02C666[y]);
        if (a >= 0x0B) {                        /* CODE_02C69B */
            SETSPR(wm_SpriteMiscTbl5, x, SPR(wm_SpriteMiscTbl5, x) + 1);
            return;
        }
        SETSPR(wm_SpriteMiscTbl7, x, a);
    }
    SETSPR(wm_SpriteMiscTbl3, x, tc_02C62E[SPR(wm_SpriteMiscTbl7, x)]);
    return;
st2:                                            /* _02C65C */
    SETSPR(wm_SpriteState, x, 2);
    SETSPR(wm_SpriteDecTbl1, x, 0x18);
}

/* CODE_02C6A7, estado 1: persigue a Mario */
static void chuck_st1(u8 x)
{
    u8 y, a;
    chuck_vert(x);                              /* _02C6BA (el bloque de arriba no hace nada) */
    if ((u8)(R8(m14) + 0x30) < 0x60) {
        y = chuck_horz(x);
        if (y == SPR(wm_SpriteDir, x)) {
            SETSPR(wm_SpriteDecTbl1, x, 0x20);
            SETSPR(wm_SprStompImmuneTbl, x, 0x20);
        }
    }
    if (!SPR(wm_SpriteDecTbl1, x)) {
        SETSPR(wm_SpriteState, x, 0);
        chuck_dectbl5(x);
        SETSPR(wm_SpriteDecTbl1, x, (chuck_rand() & 0x3F) | 0x40);
    }
    y = SPR(wm_SpriteDir, x);
    SETSPR(wm_SpriteMiscTbl3, x, tc_02C639[y]);
    if (SPR(wm_SprObjStatus, x) & 0x04) {
        if (SPR(wm_SprStompImmuneTbl, x)) {
            if (!(R8(wm_FrameB) & 0x07))
                W8(wm_SoundCh1, 0x01);
            y += 2;
        }
        SETSPR(wm_SpriteSpeedX, x, tc_02C69F[y]);
    }
    a = R8(wm_FrameA);
    if (!SPR(wm_SprStompImmuneTbl, x))
        a >>= 1;
    a >>= 1;
    SETSPR(wm_SpriteGfxTbl, x, tc_02C6A3[a & 0x03]);
}

/* CODE_02C726, estado 2: parado un rato */
static void chuck_st2(u8 x)
{
    SETSPR(wm_SpriteGfxTbl, x, 3);
    if (!SPR(wm_SpriteDecTbl1, x)) {
        chuck_dectbl5(x);
        SETSPR(wm_SpriteState, x, 1);
        SETSPR(wm_SpriteDecTbl1, x, 0x40);
    }
}

/* CODE_02C74A, estado 3: golpeado (la secuencia de poses de MiscTbl6) */
static void chuck_st3(u8 x)
{
    u8 y = SPR(wm_SpriteMiscTbl6, x), a;
    if (!SPR(wm_SpriteDecTbl1, x)) {
        SETSPR(wm_SpriteMiscTbl6, x, SPR(wm_SpriteMiscTbl6, x) + 1);
        y++;
        if (y == 0x07) {                        /* CODE_02C777 (no es el $94 ni el $46) */
            SETSPR(wm_SpriteDecTbl1, x, 0x30);
            SETSPR(wm_SpriteState, x, 2);
            SETSPR(wm_SprStompImmuneTbl, x, SPR(wm_SprStompImmuneTbl, x) + 1);
            chuck_face(x);
            return;
        }
        SETSPR(wm_SpriteDecTbl1, x, tc_02C743[y]);
    }
    /* DATA_02C73D tiene 6 bytes: con y = 6 el ROM lee el primero de DATA_02C743 */
    SETSPR(wm_SpriteGfxTbl, x, y < 6 ? tc_02C73D[y] : tc_02C743[0]);
    a = 2;
    if (y == 5)
        a = (u8)(((R8(wm_FrameB) >> 1) & 0x02) + 1);
    SETSPR(wm_SpriteMiscTbl3, x, a);
}

/* CODE_02C4E3, estado 8: salta y aplaude (el $95 nace en este estado) */
static void chuck_st8(u8 x)
{
    u8 a = 6, sy;
    chuck_face(x);
    sy = SPR(wm_SpriteSpeedY, x);
    if (!NEG((u8)(sy - 0xF0)) && SPR(wm_SpriteMiscTbl8, x)) {
        if (!SPR(wm_DisSprCapeContact, x)) {
            W8(wm_SoundCh3, 0x19);
            SETSPR(wm_DisSprCapeContact, x, 0x20);
        }
        a = 7;
    }
    SETSPR(wm_SpriteGfxTbl, x, a);
    if (!(SPR(wm_SprObjStatus, x) & 0x04))
        return;
    SETSPR(wm_SpriteMiscTbl8, x, 0);
    SETSPR(wm_SpriteGfxTbl, x, 4);
    if (SPR(wm_SpriteDecTbl1, x))
        return;
    SETSPR(wm_SpriteDecTbl1, x, 0x20);
    SETSPR(wm_SpriteSpeedY, x, 0xF0);
    chuck_vert(x);
    a = R8(m14);
    if (NEG(a) && a < 0xD0) {
        SETSPR(wm_SpriteSpeedY, x, 0xC0);
        SETSPR(wm_SpriteMiscTbl8, x, SPR(wm_SpriteMiscTbl8, x) + 1);
        W8(wm_SoundCh3, 0x08);                  /* _02C536 */
    }
}

/* CODE_02C22C: un frame del Chuck */
static void chuck_run(u8 x)
{
    u8 a, y;
    if (SPR(wm_SpriteStatus, x) != 0x08) {      /* CODE_02C217: muriendo */
        SETSPR(wm_SpriteMiscTbl3, x, tc_02C213[(R8(wm_FrameB) >> 2) & 0x03]);
        get_draw_info(x);                       /* CODE_02C81A */
        return;
    }
    if (SPR(wm_SpriteDecTbl5, x))
        SETSPR(wm_SpriteGfxTbl, x, 5);
    if (!(SPR(wm_SprObjStatus, x) & 0x04) && NEG(SPR(wm_SpriteSpeedY, x))
        && SPR(wm_SpriteState, x) < 5)
        SETSPR(wm_SpriteGfxTbl, x, 6);
    get_draw_info(x);                           /* CODE_02C81A: dibujo */
    if (R8(wm_SpritesLocked))
        return;
    sub_offscreen3(x);                          /* SubOffscreen0Bnk2 */
    chuck_contact(x);
    spr_spr_interact(x);
    spr_obj_interact(x);                        /* CODE_019138 */
    if (SPR(wm_SprObjStatus, x) & 0x08)
        SETSPR(wm_SpriteSpeedY, x, 0x10);
    if (!(SPR(wm_SprObjStatus, x) & 0x03)) {
        chuck_axis(x, 0x0C);                    /* CODE_02C2F4: UpdateXPosNoGrvty2 */
    } else {
        a = 0;                                  /* a = 1: va a CODE_02C2E4 */
        if (!(SPR(wm_OffscreenHorz, x) | SPR(wm_OffscreenVert, x)) && SPR(wm_SprStompImmuneTbl, x)
            && (u8)((u8)(SPR(wm_SpriteXLo, x) - R8(wm_Bg1HOfs)) + 0x14) >= 0x1C
            && !(SPR(wm_SprObjStatus, x) & 0x40)
            && (R8(wm_MirBlkCheck) == 0x2E || R8(wm_MirBlkCheck) == 0x1E))
            a = 1;                              /* el Chuck embiste un bloque */
        if (a) {
            if (SPR(wm_SprObjStatus, x) & 0x04) {
                spr_unsup();                    /* ShatterBlock + GenerateTile (sin portar) */
                chuck_axis(x, 0x0C);            /* BRA CODE_02C2F4 */
            }
        } else {                                /* CODE_02C2E4 */
            if (SPR(wm_SprObjStatus, x) & 0x04) {
                SETSPR(wm_SpriteSpeedY, x, 0xC0);
                chuck_axis(x, 0);
                goto c301;                      /* BRA _02C301 */
            }
        }
    }
    if (SPR(wm_SprObjStatus, x) & 0x04)         /* _02C2F7 */
        chuck_stop(x);
c301:
    chuck_axis(x, 0);                           /* UpdateYPosNoGrvty2 */
    y = 0;
    a = SPR(wm_SpriteSpeedY, x);
    if (SPR(wm_SprInWaterTbl, x)) {
        y = 1;
        if (NEG(a) && a < 0xE0)
            a = 0xE0;
    }
    a = (u8)(a + tc_02C22A[y]);
    if (!NEG(a)) {
        if (a >= tc_02C228[y])
            a = tc_02C228[y];
        if (SPR(wm_SpriteState, x) == 7)
            a = (u8)(a + 3);
    }
    SETSPR(wm_SpriteSpeedY, x, a);
    switch (SPR(wm_SpriteState, x)) {           /* ExecutePtr ChuckPtrs */
    case 0: chuck_st0(x); break;
    case 1: chuck_st1(x); break;
    case 2: chuck_st2(x); break;
    case 3: chuck_st3(x); break;
    case 8: chuck_st8(x); break;
    default: spr_unsup(); break;                /* estados de los otros Chucks */
    }
}

/* ChucksMain: llama a CODE_02C22C; un Chuck que se hizo inmune a los
   pisotones en este frame arranca DecTbl6 */
void chuck_main(u8 x)
{
    u8 imm = SPR(wm_SprStompImmuneTbl, x);
    chuck_run(x);
    if (!imm && SPR(wm_SprStompImmuneTbl, x) && !SPR(wm_SpriteDecTbl6, x))
        SETSPR(wm_SpriteDecTbl6, x, 0x28);
}

/* InitClappinChuck / _01851A: estado 8, mira a Mario (SubHorizPos del banco
   1: con wm_PlayerXPosLv) */
void chuck_init(u8 x)
{
    u16 d = (u16)(R16(wm_PlayerXPosLv) - (SPR(wm_SpriteXLo, x) | SPR(wm_SpriteXHi, x) << 8));
    u8 y = (u8)((d & 0x8000) ? 1 : 0);
    SETSPR(wm_SpriteStatus, x, 0x08);
    SETSPR(wm_SpriteState, x, 0x08);
    W8(m15, (u8)d);
    SETSPR(wm_SpriteDir, x, y);
    SETSPR(wm_SpriteMiscTbl3, x, tc_018526[y]);
}
