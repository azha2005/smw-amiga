/*
 * spr_goal.c - la cinta de la meta (sprite $7B, GoalTape / InitGoalTape de
 * sprite_1-1.s), TriggerGoalTape (ex_sprite.s) y el estado 6 de los sprites
 * (HandleSprLvlEnd -> LvlEndSprCoinsRt, ex_sprite.s). Tercer sprite en
 * fichero propio (I1, ver msprite.h). La secuencia final (Mario caminando
 * solo, el fin del nivel) no esta aca: aca solo la cinta y lo que dispara.
 *
 * Transcripcion instruccion por instruccion (P27), con los registros del
 * 65816 anotados donde importan (A, X = ranura, Y). Diferencias con la ROM:
 *   - el dibujo (CODE_01C12D, CODE_07F1CA, GenericSprGfxRt2, CoinSprGfx) se
 *     reduce a GetDrawInfoBnk1 (los flags de fuera de pantalla; los tiles
 *     son de la 9.2). Si GetDrawInfoBnk1 ve el sprite lejos hace PLA/PLA y
 *     salta el dibujo, nada mas: aca da igual;
 *   - GivePoints (CODE_02ACE6: un sprite de puntuacion y la puntuacion) y las
 *     monedas del fin (CODE_05B34A) son de la etapa 10: MEV_SPRITE;
 *   - sin portar (spr_unsup): un sprite en estado $0B (llevado) cuando se
 *     corta la cinta (LvlEndPowerUp), y MiscTbl7 >> 2 >= 32 (DATA_07F1AA
 *     lee mas alla de la tabla: no pasa, la barra sube $7C px como mucho).
 *   - de la cinta, los oraculos cubren el corte SIN contacto con la barra
 *     (oracle_goal: la cinta pasa a estado 6, 138 frames) y el corte CON
 *     contacto (oracle_goalhit, tools/snesorc/goalhit.orc: Tweaker1686
 *     conserva el bit $20, la cinta sigue en estado 8 con MiscTbl8 = 1 y
 *     DecTbl1 = $80 hasta desaparecer, 211 frames). Los oraculos no graban
 *     $18DD/$1900/$1DFC...: SilverCoins, BonusStarsGained y los sonidos de
 *     esta rutina no estan comparados.
 * Las tablas .DB vienen de tools/smwtabx.py (WANT_GOAL, SMWTABX_GOAL):
 * solo este fichero las incluye (P78).
 */
#include "msprite.h"
#define SMWTABX_GOAL
#include "gen/smwtabx.h"

#ifdef LOGIC68K
void spr_pos_axis_asm(u8 x, u8 o);      /* player/logic68k.s */
#define goal_axis(x) spr_pos_axis_asm((x), 0)
#else
/* SubSprYPosNoGrvty: la velocidad 4.4 a la posicion Y. Igual que
   spr_pos_axis(x, 0) de msprite.c (que no es extern en el host) */
static void goal_axis(u8 x)
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

/* InitGoalTape: State/MiscTbl3 = X - 8 (16 bits: el borde izquierdo de la
   zona de contacto), MiscTbl4/5 = la Y original (bit 8 solo), StompImmune =
   el byte alto de la Y de nivel entero (da wm_SecretGoalSprite) */
void goal_init(u8 x)
{
    u16 sx = (u16)((SPR(wm_SpriteXLo, x) | SPR(wm_SpriteXHi, x) << 8) - 8);
    u8 yh;
    SETSPR(wm_SpriteStatus, x, 0x08);       /* CallSpriteInit */
    SETSPR(wm_SpriteState, x, (u8)sx);
    SETSPR(wm_SpriteMiscTbl3, x, sx >> 8);
    SETSPR(wm_SpriteMiscTbl4, x, SPR(wm_SpriteYLo, x));
    yh = SPR(wm_SpriteYHi, x);
    SETSPR(wm_SprStompImmuneTbl, x, yh);
    yh &= 0x01;
    SETSPR(wm_SpriteYHi, x, yh);
    SETSPR(wm_SpriteMiscTbl5, x, yh);
}

/* TriggerGoalTape (CODE_00FA7x, ex_sprite.s): al cortar la cinta, los
   sprites vivos (estado >= 8) pasan a estado 6 (se vuelven monedas) con
   DecTbl1 = $10, o desaparecen; la propia cinta pasa a 6 si no lleva el bit
   $20 de Tweaker1686. Y = $0B..0 */
static void trigger_goal_tape(void)
{
    u8 y, st, i;
    W8(wm_PBalloonFrame, 0);
    W8(wm_BalloonTimer, 0);
    W8(wm_TimeTillRespawn, 0);
    W8(wm_GeneratorNum, 0);
    W8(wm_SilverCoins, 0);
    for (y = 0x0C; y-- > 0; ) {
        st = SPR(wm_SpriteStatus, y);
        if (st < 0x08)                      /* _LvlEndNextSprite */
            continue;
        if (st == 0x0B) {                   /* LvlEndPowerUp: sin portar */
            spr_unsup();
            continue;
        }
        /* CODE_00FAA3: la cinta (SpriteNum $7B) pasa siempre; el resto, solo
           si esta a la vista */
        if (SPR(wm_SpriteNum, y) == 0x7B
            || !(SPR(wm_OffscreenHorz, y) | SPR(wm_OffscreenVert, y))) {
            if (!(SPR(wm_Tweaker1686, y) & 0x20)) {
                SETSPR(wm_SpriteDecTbl1, y, 0x10);
                SETSPR(wm_SpriteStatus, y, 0x06);
                continue;
            }
        }
        if (!(SPR(wm_Tweaker190F, y) & 0x02))   /* CODE_00FAC5 */
            SETSPR(wm_SpriteStatus, y, 0x00);
    }
    for (i = 0; i < 8; i++)                 /* wm_ExSpriteNum[0..7] = 0 */
        W8(wm_ExSpriteNum + i, 0);
}

/* GoalTape (estado 8) */
void goal_tape(u8 x)
{
    u16 d;
    u8 xl, xh;
    /* JSR CODE_01C12D */
    if (SPR(wm_SpriteMiscTbl8, x)) {        /* CODE_01C175: la barra ya se corto */
        if (!SPR(wm_SpriteDecTbl1, x))      /* DecTbl1 != 0: dibuja los puntos (CODE_07F1CA) */
            SETSPR(wm_SpriteStatus, x, 0);  /* CODE_01C17F */
    } else {
        get_draw_info1(x);                  /* CODE_01C12D: GetDrawInfoBnk1 + OAM */
    }
    if (R8(wm_SpritesLocked))
        return;
    if (SPR(wm_SpriteGfxTbl, x))            /* ya cortada */
        return;
    /* CODE_01C0A7 */
    if (!SPR(wm_SpriteDecTbl1, x)) {
        SETSPR(wm_SpriteDecTbl1, x, 0x7C);
        SETSPR(wm_SprObjStatus, x, SPR(wm_SprObjStatus, x) + 1);
    }
    SETSPR(wm_SpriteSpeedY, x, tg_01C0A5[SPR(wm_SprObjStatus, x) & 0x01]);
    goal_axis(x);                           /* SubSprYPosNoGrvty */
    xl = SPR(wm_SpriteState, x);            /* m0 / m1 */
    xh = SPR(wm_SpriteMiscTbl3, x);
    W8(m0, xl);
    W8(m1, xh);
    d = (u16)(R16(wm_MarioXPos) - (u16)(xl | xh << 8));
    if (d >= 0x0010)                        /* BCS: Mario fuera de [X-8, X+8) */
        return;
    {   /* CMP MiscTbl4,MarioYPos / LDA MiscTbl5 AND 1 / SBC MarioYPos+1 / BCC:
           vuelve si la Y original (9 bits) < la Y de Mario */
        u8 lo = SPR(wm_SpriteMiscTbl4, x);
        u8 hi = SPR(wm_SpriteMiscTbl5, x) & 0x01;
        u8 ml = R8(wm_MarioYPos), mh = R8(wm_MarioYPos + 1);
        if ((int)hi - (int)mh - (lo < ml ? 1 : 0) < 0)
            return;
    }
    W8(wm_SecretGoalSprite, SPR(wm_SprStompImmuneTbl, x) >> 2);
    W8(wm_MusicCh1, 0x0C);
    W8(wm_LevelMusicMod, 0xFF);
    W8(wm_EndLevelTimer, 0xFF);
    W8(wm_StarPowerTimer, 0);
    SETSPR(wm_SpriteGfxTbl, x, SPR(wm_SpriteGfxTbl, x) + 1);
    if (mario_spr_interact(x)) {            /* BCC CODE_01C125: barra tocada */
        u8 i;
        W8(wm_SoundCh3, 0x09);
        SETSPR(wm_SpriteMiscTbl8, x, SPR(wm_SpriteMiscTbl8, x) + 1);
        SETSPR(wm_SpriteMiscTbl7, x, (u8)(SPR(wm_SpriteMiscTbl4, x) - SPR(wm_SpriteYLo, x)));
        SETSPR(wm_SpriteDecTbl1, x, 0x80);
        /* CODE_07F252: las estrellas de bonus segun la altura */
        i = SPR(wm_SpriteMiscTbl7, x) >> 2;
        if (i >= 32) {
            spr_unsup();                    /* DATA_07F1AA lee mas alla de la tabla */
        } else {
            W8(wm_BonusStarsGained, tg_07F1AA[i]);
            if (tg_07F1AA[i] == 0x50)
                mario_events |= MEV_SPRITE; /* GivePoints ($0A) */
        }
    } else {
        SETSPR(wm_Tweaker1686, x, 0);       /* CODE_01C125 */
    }
    trigger_goal_tape();                    /* _01C128 */
}

/* HandleSprLvlEnd (estado 6) = LvlEndSprCoinsRt: el sprite acompana a la
   capa 1 y, pasado DecTbl1 (el humo), sube y cae como una moneda; al
   alcanzar SpeedY = $20 suma monedas y desaparece */
void goal_lvlend(u8 x)
{
    u8 t;
    u16 sx = (u16)(SPR(wm_SpriteXLo, x) | SPR(wm_SpriteXHi, x) << 8);
    sx = (u16)(sx + (u16)(s16)(s8)R8(wm_L1CurXChange));     /* Y = 0 o $FF, ADC */
    SETSPR(wm_SpriteXLo, x, (u8)sx);
    SETSPR(wm_SpriteXHi, x, sx >> 8);
    t = SPR(wm_SpriteDecTbl1, x);
    if (t) {
        if (t == 1)
            SETSPR(wm_SpriteSpeedY, x, 0xD0);
        SETSPR(wm_SpritePal, x, 0x04);
        get_draw_info1(x);                  /* GenericSprGfxRt2 (el humo) */
        return;
    }
    /* CODE_00FBF0 */
    SETSPR(wm_SpriteMiscTbl6, x, SPR(wm_SpriteMiscTbl6, x) + 1);
    goal_axis(x);                           /* UpdateYPosNoGrvty */
    SETSPR(wm_SpriteSpeedY, x, SPR(wm_SpriteSpeedY, x) + 2);
    if (!((u8)(SPR(wm_SpriteSpeedY, x) - 0x20) & 0x80)) {   /* CMP #$20 / BMI */
        W8(wm_CoinAdder, R8(wm_CoinAdder) + 1);             /* CODE_05B34A */
        W8(wm_SoundCh3, 0x01);
        if (R8(wm_GreenStarCoins))
            W8(wm_GreenStarCoins, R8(wm_GreenStarCoins) - 1);
        mario_events |= MEV_SPRITE;         /* GivePoints (min(SilverCoins, $0D)) */
        W8(wm_SilverCoins, R8(wm_SilverCoins) + 2);
        SETSPR(wm_SpriteStatus, x, 0x00);
    }
    get_draw_info1(x);                      /* CoinSprGfx */
}
