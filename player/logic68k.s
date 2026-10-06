;----------------------------------------------------------------------
; logic68k.s - rutinas de la logica en ensamblador a mano (Etapa 8.2).
;
; Cada rutina reemplaza, SOLO en el build de la Amiga (vbcc, sin NOASM), a
; una funcion de player/*.c que sigue siendo la referencia: el PC
; (marioverify) corre el C, y m68kverify/abcheck comparan el binario del
; 68000 contra el. Los casos raros no se escriben aca: la rutina salta a la
; version en C con los mismos argumentos (antes de cambiar nada que el C
; no vuelva a escribir igual).
;
; ABI de vbcc: argumentos en la pila en ranuras de 32 bits (un u8 en el
; byte +3), resultado en d0, se conservan d2-d7/a2-a6; a4 = datos pequenos
; (_ram(a4), _map16_lo(a4)...). Las direcciones de ram[] salen de
; work/cc/smwram.i (lo genera logicbench_build.sh desde gen/smwram.h).
;----------------------------------------------------------------------
        include "player/picmacros.i"       ; tambien visible al verificador ABI
;----------------------------------------------------------------------
; u8 spr_tile_asm(u8 x, u8 y) = spr_tile de msprite.c (CODE_019441 /
; _01944D / CODE_0194BF): el bloque bajo el punto de choque y del sprite x.
; Deja m0, m1, m10-m13, m15 y Map16NumLo como el C.
;----------------------------------------------------------------------
        public  _spr_tile_asm
_spr_tile_asm:                              ; guarda solo d2-d3; ram por a4
        movem.l d2-d3,-(sp)
        moveq   #0,d1
        move.b  8+7(sp),d1                  ; x
        moveq   #0,d2
        move.b  8+11(sp),d2                 ; y
        lea     _ram(a4),a1
        add.w   d1,a1                       ; a1 = ram + x ((d8,An,Dn) no llega)
        move.b  d2,_ram+m15(a4)
        move.b  wm_Tweaker1656(a1),d0
        and.b   #$0f,d0
        lsl.b   #2,d0
        add.b   d0,d2                       ; y = punto de choque
        move.b  _ram+wm_TempTileGen(a4),d0
        addq.b  #1,d0
        and.b   _ram+wm_IsVerticalLvl(a4),d0
        bne     .inc                        ; generador / nivel vertical: el C
        ; py = Y del sprite + SprObjClipY[y]
        moveq   #0,d3
        move.b  wm_SpriteYHi(a1),d3
        lsl.w   #8,d3
        move.b  wm_SpriteYLo(a1),d3
        move.l  _spr_clip_y(a4),a0
        moveq   #0,d0
        move.b  (a0,d2.w),d0
        add.w   d0,d3
        move.b  d3,_ram+m12(a4)
        move.w  d3,-(sp)                    ; byte alto, sin desplazar
        move.b  (sp)+,_ram+m13(a4)
        moveq   #-16,d0                     ; $F0
        and.b   d3,d0
        move.b  d0,_ram+m0(a4)
        cmp.w   #$1b0,d3
        bhs     .out
        ; px = X del sprite + SprObjClipX[y]  (d1: x ya no hace falta)
        move.b  wm_SpriteXHi(a1),d1
        lsl.w   #8,d1
        move.b  wm_SpriteXLo(a1),d1
        move.l  _spr_clip_x(a4),a0
        moveq   #0,d0
        move.b  (a0,d2.w),d0
        add.w   d0,d1
        move.b  d1,_ram+m10(a4)
        move.b  d1,_ram+m1(a4)
        move.w  d1,d0
        lsr.w   #8,d0
        move.b  d0,_ram+m11(a4)
        tst.w   d1
        bmi     .out
        cmp.b   _ram+wm_ScreensInLvl(a4),d0
        bhs     .out
        ; o = scr_ofs[pantalla] + (py & $1F0) + (px & $FF) >> 4  (< $3600)
        and.w   #$1f,d0
        add.w   d0,d0
        lea     _scr_ofs(a4),a0
        move.w  (a0,d0.w),d0
        and.w   #$1f0,d3
        add.w   d3,d0
        moveq   #0,d3
        move.b  d1,d3
        lsr.b   #4,d3
        add.w   d3,d0
        move.l  _map16_lo(a4),a0
        move.b  (a0,d0.w),d2                ; lo
        move.l  _map16_hi(a4),a0
        moveq   #0,d3
        move.b  (a0,d0.w),d3                ; pagina
        move.b  d2,_ram+wm_Map16NumLo(a4)
        tst.b   d3
        beq.s   .p0
        cmp.b   #$32,d2
        beq.s   .uns
        cmp.b   #$2f,d2
        beq.s   .uns
        bra.s   .ret
.p0:    cmp.b   #$29,d2
        beq.s   .uns
        cmp.b   #$2b,d2
        beq.s   .uns
        sub.b   #$ec,d2
        cmp.b   #$10,d2
        bhs.s   .ret
.uns:   tst.l   _mario_unsupported(a4)      ; interruptores P: sin portar
        bne.s   .ret
        moveq   #MARIO_UNSUP_TILE,d0
        move.l  d0,_mario_unsupported(a4)
.ret:   move.l  d3,d0
        movem.l (sp)+,d2-d3
        rts
.out:   clr.b   _ram+wm_Map16NumLo(a4)      ; CODE_0194B4
        clr.b   _ram+wm_SprMoveDownPixels(a4)
        moveq   #0,d0
        movem.l (sp)+,d2-d3
        rts
.inc:   movem.l (sp)+,d2-d3                 ; los argumentos siguen en la pila
        jmp     _spr_tile_c

;----------------------------------------------------------------------
; u8 f44d_asm(void) = f44d de mcoll.c (CODE_00F44D): la sonda siguiente
; (rX += 2) respecto de la posicion de Mario (probe_mx/my), el bloque que
; toca y su pagina. Deja BlockYPos/XPos, Map16NumLo y rY como el C. Con
; wm_8E (capa 2) salta al C; con un bloque de los interruptores P llama a
; f44d_tail (f545 en C).
;----------------------------------------------------------------------
        public  _f44d_asm
_f44d_asm:                                  ; solo d2 se guarda: base en a1
        tst.b   _ram+wm_8E(a4)
        bne     .c
        move.l  d2,-(sp)
        lea     _ram(a4),a1
        move.b  _rX(a4),d0
        addq.b  #2,d0
        move.b  d0,_rX(a4)
        moveq   #$7e,d1
        and.b   d0,d1                       ; k = 2 * ((rX >> 1) & 63)
        lea     _probe_dx(a4),a0
        move.w  (a0,d1.w),d2
        add.w   _probe_mx(a4),d2            ; d2 = x
        lea     _probe_dy(a4),a0
        move.w  (a0,d1.w),d1
        add.w   _probe_my(a4),d1            ; d1 = y
        move.b  d2,wm_BlockYPos(a1)         ; (el ROM pone x en BlockYPos)
        move.w  d2,d0
        lsr.w   #8,d0                       ; d0 = xs = pantalla
        move.b  d0,wm_BlockYPos+1(a1)
        move.b  d1,wm_BlockXPos(a1)
        move.w  d1,-(sp)                    ; byte alto de y, sin desplazar
        move.b  (sp)+,wm_BlockXPos+1(a1)
        clr.b   wm_WhichSwitchPressed(a1)
        cmp.w   #$1b0,d1
        bhs.s   .off
        cmp.b   wm_ScreensInLvl(a1),d0
        bhs.s   .off
        and.w   #$1f,d0
        add.w   d0,d0
        lea     _scr_ofs(a4),a0
        move.w  (a0,d0.w),d0
        and.w   #$1f0,d1
        add.w   d1,d0
        moveq   #0,d1
        move.b  d2,d1
        lsr.b   #4,d1
        add.w   d1,d0                       ; o (< $3600)
        move.l  _map16_lo(a4),a0
        move.b  (a0,d0.w),d1                ; lo
        move.l  _map16_hi(a4),a0
        moveq   #0,d2
        move.b  (a0,d0.w),d2                ; pagina
        move.b  d1,wm_Map16NumLo(a1)
        move.b  d1,_rY(a4)
        tst.b   d2
        beq.s   .p0
        cmp.b   #$32,d1
        beq.s   .sw
        cmp.b   #$2f,d1
        beq.s   .sw
        bra.s   .ret
.p0:    cmp.b   #$29,d1
        beq.s   .sw
        cmp.b   #$2b,d1
        beq.s   .sw
        sub.b   #$ec,d1
        cmp.b   #$10,d1
        bhs.s   .ret
.sw:    move.l  d2,-(sp)                    ; interruptores P: f545 en C
        PICCALL _f44d_tail                  ; tambien el build normal excede 32 KB (P102)
        addq.l  #4,sp
        moveq   #0,d2
        move.b  d0,d2
.ret:   move.l  d2,d0
        move.l  (sp)+,d2
        rts
.off:   move.b  #$25,_rY(a4)                ; CODE_00F4A0: fuera del nivel
        moveq   #0,d0
        move.l  (sp)+,d2
        rts
.c:
        PICJUMP _f44d_c

;----------------------------------------------------------------------
; void spr_pos_axis_asm(u8 x, u8 o) = spr_pos_axis de msprite.c
; (SubSprYPosNoGrvty; o = $0C: SubSprXPosNoGrvty). Velocidad 4.4 a la
; posicion: YAcc += v << 4, YLo:YHi += (v asr 4) + acarreo, con addx
; (la cadena de acarreo del 65816, sin rearmar 16 bits).
;----------------------------------------------------------------------
        public  _spr_pos_axis_asm
_spr_pos_axis_asm:
        movem.l d2-d3,-(sp)
        moveq   #0,d1
        move.b  8+7(sp),d1                  ; x
        moveq   #0,d0
        move.b  8+11(sp),d0                 ; o
        add.w   d0,d1
        lea     _ram(a4),a1
        add.w   d1,a1                       ; a1 = ram + x + o
        move.b  wm_SpriteSpeedY(a1),d0      ; v
        beq.s   .zero
        move.b  d0,d1
        asr.b   #4,d1                       ; d = v >> 4 con signo
        smi     d2                          ; hi = $FF si d < 0
        lsl.b   #4,d0                       ; v << 4
        move.b  wm_SpriteYAcc(a1),d3
        add.b   d0,d3                       ; X = C = acarreo c
        scs     d0                          ; d0 = -c (antes del move: el move
        move.b  d3,wm_SpriteYAcc(a1)        ; borra C; X no lo toca)
        move.b  wm_SpriteYLo(a1),d3
        addx.b  d1,d3                       ; YLo + d + c
        move.b  d3,wm_SpriteYLo(a1)
        move.b  wm_SpriteYHi(a1),d3
        addx.b  d2,d3                       ; YHi + hi + acarreo
        move.b  d3,wm_SpriteYHi(a1)
        sub.b   d0,d1                       ; d + c
        move.b  d1,_ram+wm_SprPixelMove(a4)
        movem.l (sp)+,d2-d3
        rts
.zero:  clr.b   _ram+wm_SprPixelMove(a4)
        movem.l (sp)+,d2-d3
        rts

;----------------------------------------------------------------------
; int get_draw_info_asm(u8 x) = get_draw_info de msprite.c
; (GetDrawInfoBnk3, solo los flags de fuera de pantalla). Devuelve 0 si
; el sprite esta lejos.
;----------------------------------------------------------------------
        public  _get_draw_info_asm
_get_draw_info_asm:
        movem.l d2-d4,-(sp)
        moveq   #0,d1
        move.b  12+7(sp),d1                 ; x
        lea     _ram(a4),a1
        add.w   d1,a1                       ; a1 = ram + x
        lea     _ram(a4),a0
        clr.b   wm_OffscreenVert(a1)
        move.b  wm_SpriteXHi(a1),d2
        lsl.w   #8,d2
        move.b  wm_SpriteXLo(a1),d2         ; sx
        move.b  wm_Bg1HOfs+1(a0),d0
        lsl.w   #8,d0
        move.b  wm_Bg1HOfs(a0),d0           ; camara X
        sub.w   d0,d2                       ; sx - cam
        move.w  d2,d0
        lsr.w   #8,d0
        sne     d0
        neg.b   d0
        move.b  d0,wm_OffscreenHorz(a1)     ; alto != 0
        add.w   #$40,d2
        cmp.w   #$180,d2
        shs     d0
        neg.b   d0
        move.b  d0,wm_SpriteOffTbl(a1)
        bne.s   .far
        move.b  wm_Bg1VOfs+1(a0),d3
        lsl.w   #8,d3
        move.b  wm_Bg1VOfs(a0),d3           ; camara Y
        move.b  wm_SpriteYHi(a1),d2
        lsl.w   #8,d2
        move.b  wm_SpriteYLo(a1),d2
        sub.w   d3,d2                       ; sy - camY (+ tabla abajo)
        moveq   #0,d4
        btst    #5,wm_Tweaker1662(a1)
        beq.s   .y0
        moveq   #1,d4                       ; y = 1: dos puntos
.lp:    move.l  _gdi_ofs(a4),a0
        moveq   #0,d0
        move.b  (a0,d4.w),d0
        add.w   d2,d0
        lsr.w   #8,d0
        beq.s   .nx
        move.l  _gdi_bit(a4),a0
        move.b  (a0,d4.w),d0
        or.b    d0,wm_OffscreenVert(a1)
.nx:    subq.w  #1,d4
        bpl.s   .lp
        bra.s   .on
.y0:    move.l  _gdi_ofs(a4),a0
        moveq   #0,d0
        move.b  (a0),d0
        add.w   d2,d0
        lsr.w   #8,d0
        beq.s   .on
        move.l  _gdi_bit(a4),a0
        move.b  (a0),d0
        or.b    d0,wm_OffscreenVert(a1)
.on:    moveq   #1,d0
        movem.l (sp)+,d2-d4
        rts
.far:   moveq   #0,d0
        movem.l (sp)+,d2-d4
        rts

;----------------------------------------------------------------------
; void camera_F6DB(void) = camera_F6DB_c de mcam.c (CODE_00F6DB, nivel
; horizontal): Bg1/Bg2 a partir de L1/L2NextPos y de Mario respecto de la
; zona muerta. f7f4 (scroll vertical) y f8ab (L/R) siguen en C. Nivel
; vertical: el C (lo marca sin portar).
; d3 = pts  d4 = bg1h  d5 = bg1v  d6 = bg2h  d7 = bg2v  a2 = ram
;----------------------------------------------------------------------
RD16    macro                               ; \2.w = ram[\1] (little endian)
        move.b  \1+1(a2),\2
        lsl.w   #8,\2
        move.b  \1(a2),\2
        endm
WR16    macro                               ; ram[\1] = \2.w (destruye d0)
        move.b  \2,\1(a2)
        move.w  \2,d0
        lsr.w   #8,d0
        move.b  d0,\1+1(a2)
        endm

        public  _camera_F6DB
_camera_F6DB:
        btst    #0,_ram+wm_IsVerticalLvl(a4)
        bne     .vert
        movem.l d2-d7/a2,-(sp)
        lea     _ram(a4),a2
        RD16    wm_PosToScrollScreen,d3
        move.w  d3,d1
        sub.w   #$000c,d1
        WR16    wm_CanScrollScreen,d1
        add.w   #$0018,d1
        WR16    wm_CanScrollScreen+2,d1
        RD16    wm_L1NextPosX,d4
        RD16    wm_L1NextPosY,d5
        RD16    wm_L2NextPosX,d6
        RD16    wm_L2NextPosY,d7
        WR16    wm_Bg1HOfs,d4
        moveq   #0,d0                       ; bg1v = f7f4($00C0, bg1v)
        move.w  d5,d0
        move.l  d0,-(sp)
        move.l  #$00c0,-(sp)
        jsr     _f7f4
        addq.l  #8,sp
        move.w  d0,d5
        tst.b   wm_HorzScrollHead(a2)
        beq     .l2
        RD16    wm_MarioXPos,d1
        sub.w   d4,d1                       ; v0 = MarioXPos - bg1h
        WR16    m0,d1
        moveq   #2,d2                       ; y
        move.w  d1,d0
        sub.w   d3,d0
        bpl.s   .y2
        moveq   #0,d2
.y2:    move.b  d2,wm_Layer1ScrollDir(a2)
        move.b  d2,wm_Layer2ScrollDir(a2)
        move.w  d3,d0                       ; a = v0 - (pts - $0C [+ $18])
        sub.w   #$000c,d0
        tst.b   d2
        beq.s   .y0
        add.w   #$0018,d0
.y0:    sub.w   d0,d1                       ; d1 = a
        beq     .l2
        lea     _rom00+(DATA_00F6A3-ROM00_BASE)(a4),a0
        move.w  d1,d0                       ; (a ^ T16X(DATA_00F6A3, y)) & $8000:
        lsr.w   #8,d0                       ; solo cuenta el bit 15, o sea el
        move.b  1(a0,d2.w),d2               ; bit 7 de los bytes altos
        eor.b   d2,d0
        bpl     .l2
        WR16    m2,d1
        jsr     _f8ab
        RD16    m2,d1                       ; v2
        add.w   d4,d1                       ; a = v2 + bg1h
        bpl.s   .pos
        moveq   #0,d1
.pos:   move.w  d1,d4
        moveq   #0,d0
        move.b  wm_LastScreenHorz(a2),d0
        subq.b  #1,d0
        lsl.w   #8,d0                       ; ((LastScreenHorz - 1) & $FF) << 8
        bpl.s   .lim
        move.w  #$0080,d0
.lim:   cmp.w   d4,d0                       ; a - bg1h < 0 (con signo)?
        bge.s   .l2
        move.w  d0,d4
.l2:    moveq   #0,d0                       ; _00F79D: la capa 2
        move.b  wm_HorzScrollLyr2(a2),d0
        beq.s   .v2
        move.w  d4,d6
        cmp.b   #1,d0
        beq.s   .v2
        lsr.w   #1,d6
.v2:    move.b  wm_VertScrollLyr2(a2),d0
        beq.s   .wr
        move.w  d5,d1
        cmp.b   #1,d0
        beq.s   .v1
        cmp.b   #2,d0
        bne.s   .v5
        lsr.w   #1,d1
        bra.s   .v1
.v5:    lsr.w   #5,d1
.v1:    RD16    wm_VertL2ScrollLength,d7
        add.w   d1,d7
.wr:    WR16    wm_Bg1HOfs,d4
        WR16    wm_Bg1VOfs,d5
        WR16    wm_Bg2HOfs,d6
        WR16    wm_Bg2VOfs,d7
        move.b  d4,d0                       ; cuanto se movio cada capa
        sub.b   wm_L1NextPosX(a2),d0
        move.b  d0,wm_L1CurXChange(a2)
        move.b  d5,d0
        sub.b   wm_L1NextPosY(a2),d0
        move.b  d0,wm_L1CurYChange(a2)
        move.b  d6,d0
        sub.b   wm_L2NextPosX(a2),d0
        move.b  d0,wm_L2CurXChange(a2)
        move.b  d7,d0
        sub.b   wm_L2NextPosY(a2),d0
        move.b  d0,wm_L2CurYChange(a2)
        WR16    wm_L1NextPosX,d4
        WR16    wm_L1NextPosY,d5
        WR16    wm_L2NextPosX,d6
        WR16    wm_L2NextPosY,d7
        movem.l (sp)+,d2-d7/a2
        rts
.vert:  jmp     _camera_F6DB_c

;----------------------------------------------------------------------
; int spr_mario_contact_asm(u8 x) = spr_mario_contact de msprite.c: cajas
; de Mario y del sprite x; 1 si se tocan. Primero Y, despues X, como el C.
; Tablas por puntero (logic68k_init): _mcl (MarioClipDispY, MarioClipH) y
; _cl (ClipDispX, ClipDispY, ClipWidth, ClipHeight).
;----------------------------------------------------------------------
CONTACT macro                               ; \1 = a  \2 = b  \3 = wa  \4 = wb
        move.w  \1,d0                       ; (u16)(a - b + $80) >= $100: no
        sub.w   \2,d0
        add.w   #$80,d0
        cmp.w   #$100,d0
        bhs     .no
        move.b  \3,d0                       ; (u8)(wa + wb) <
        add.b   \4,d0
        move.b  \2,d1                       ;   (u8)((u8)b - (u8)a + wb): no
        sub.b   \1,d1
        add.b   \4,d1
        cmp.b   d1,d0
        blo     .no
        endm

        public  _spr_mario_contact_asm
_spr_mario_contact_asm:
        movem.l d2-d7/a2,-(sp)
        moveq   #0,d1
        move.b  28+7(sp),d1                 ; x
        lea     _ram(a4),a2
        lea     (a2,d1.w),a1                ; a1 = ram + x
        moveq   #1,d2                       ; k
        tst.b   wm_IsDucking(a2)
        bne.s   .k
        tst.b   wm_MarioPowerUp(a2)
        beq.s   .k
        moveq   #0,d2
.k:     tst.b   wm_OnYoshi(a2)
        beq.s   .k2
        addq.w  #2,d2
.k2:    RD16    wm_MarioYPos,d3
        move.l  _mcl_dy(a4),a0
        moveq   #0,d0
        move.b  (a0,d2.w),d0
        add.w   d0,d3                       ; my
        move.l  _mcl_h(a4),a0
        move.b  (a0,d2.w),d4                ; mh
        moveq   #$3f,d7
        and.b   wm_Tweaker1662(a1),d7       ; c
        move.b  wm_SpriteYHi(a1),d5
        lsl.w   #8,d5
        move.b  wm_SpriteYLo(a1),d5
        move.l  _cl_dy(a4),a0
        move.b  (a0,d7.w),d0
        ext.w   d0
        add.w   d0,d5                       ; sy
        move.l  _cl_h(a4),a0
        move.b  (a0,d7.w),d6                ; sh
        CONTACT d3,d5,d4,d6
        RD16    wm_MarioXPos,d3
        addq.w  #2,d3                       ; mx
        moveq   #$0c,d4                     ; mw
        move.b  wm_SpriteXHi(a1),d5
        lsl.w   #8,d5
        move.b  wm_SpriteXLo(a1),d5
        move.l  _cl_dx(a4),a0
        move.b  (a0,d7.w),d0
        ext.w   d0
        add.w   d0,d5                       ; sx
        move.l  _cl_w(a4),a0
        move.b  (a0,d7.w),d6                ; sw
        CONTACT d3,d5,d4,d6
        moveq   #1,d0
        movem.l (sp)+,d2-d7/a2
        rts
.no:    moveq   #0,d0
        movem.l (sp)+,d2-d7/a2
        rts

;----------------------------------------------------------------------
; void rex_main_asm(u8 x) = rex_main de msprite.c (el Rex, sprite $AB):
; pose, temporizadores, velocidad, movimiento e interacciones. Las rutinas
; de sprite siguen en C (o en este fichero) y el contacto con Mario, que
; es raro, es rex_contact (C). a3 = ram + x: SPR(t, x) = t(a3).
;----------------------------------------------------------------------
CALLX   macro                               ; \1(x), x en d2
        move.l  d2,-(sp)
        jsr     \1
        addq.l  #4,sp
        endm

        public  _rex_main_asm
_rex_main_asm:
        movem.l d2/a2-a3,-(sp)
        moveq   #0,d2
        move.b  12+7(sp),d2                 ; x
        lea     _ram(a4),a2
        lea     (a2,d2.w),a3
        ifd     SPR_OAM
        CALLX   _rex_gfx                    ; misma fase que RexGfxRt, antes de la fisica
        else
        tst.b   wm_SpriteDecTbl3(a3)        ; RexGfxRt
        beq.s   .g1
        move.b  #5,wm_SpriteGfxTbl(a3)
.g1:    tst.b   wm_DisSprCapeContact(a3)
        beq.s   .g2
        move.b  #2,wm_SpriteGfxTbl(a3)
.g2:    CALLX   _get_draw_info_asm
        endc
        cmp.b   #$08,wm_SpriteStatus(a3)
        bne     .ret
        tst.b   wm_SpritesLocked(a2)
        bne     .ret
        move.b  wm_SpriteDecTbl3(a3),d0
        beq.s   .alive
        move.b  d0,wm_SpriteEatenTbl(a3)
        cmp.b   #1,d0
        bne     .ret
        clr.b   wm_SpriteStatus(a3)
        bra     .ret
.alive: CALLX   _sub_offscreen3
        addq.b  #1,wm_SpriteMiscTbl6(a3)
        move.b  wm_SpriteMiscTbl6(a3),d0
        lsr.b   #2,d0
        tst.b   wm_SpriteState(a3)
        beq.s   .s0
        and.b   #1,d0
        addq.b  #3,d0
        bra.s   .s1
.s0:    lsr.b   #1,d0
        and.b   #1,d0
.s1:    move.b  d0,wm_SpriteGfxTbl(a3)
        btst    #2,wm_SprObjStatus(a3)
        beq.s   .n2
        move.b  #$10,wm_SpriteSpeedY(a3)
        moveq   #0,d0
        move.b  wm_SpriteDir(a3),d0
        tst.b   wm_SpriteState(a3)
        beq.s   .d
        addq.b  #2,d0
.d:     move.l  _rex_speed(a4),a0
        move.b  (a0,d0.w),wm_SpriteSpeedX(a3)
.n2:    tst.b   wm_DisSprCapeContact(a3)
        bne.s   .n3
        CALLX   _spr_update_pos_asm
.n3:    moveq   #3,d0
        and.b   wm_SprObjStatus(a3),d0
        beq.s   .n4
        eor.b   #1,wm_SpriteDir(a3)
.n4:    CALLX   _spr_spr_interact
        CALLX   _mario_spr_interact
        tst.l   d0
        beq.s   .ret
        CALLX   _rex_contact
.ret:   movem.l (sp)+,d2/a2-a3
        rts

;----------------------------------------------------------------------
; void spr_update_pos_asm(u8 x) = spr_update_pos de msprite.c
; (SubUpdateSprPos): Y con gravedad, X, y la interaccion con los bloques
; (spr_obj_interact, C). Las dos constantes de la ROM, por puntero.
;----------------------------------------------------------------------
        public  _spr_update_pos_asm
_spr_update_pos_asm:
        movem.l d2-d3/a3,-(sp)
        moveq   #0,d2
        move.b  12+7(sp),d2                 ; x
        lea     _ram(a4),a3
        add.w   d2,a3                       ; a3 = ram + x
        clr.l   -(sp)                       ; spr_pos_axis(x, 0)
        move.l  d2,-(sp)
        bsr     _spr_pos_axis_asm
        addq.l  #8,sp
        tst.b   wm_SprInWaterTbl(a3)
        bne.s   .unsup
        move.l  _upd_grav(a4),a0
        move.b  wm_SpriteSpeedY(a3),d0
        add.b   (a0),d0                     ; v = SpeedY + gravedad
        bmi.s   .v
        move.l  _upd_max(a4),a0
        cmp.b   (a0),d0
        blo.s   .v
        move.b  (a0),d0                     ; tope de caida
.v:     move.b  d0,wm_SpriteSpeedY(a3)
        move.b  wm_SpriteSpeedX(a3),d3      ; keep
        pea     $0c.w                       ; spr_pos_axis(x, $0C)
        move.l  d2,-(sp)
        bsr     _spr_pos_axis_asm
        addq.l  #8,sp
        move.b  d3,wm_SpriteSpeedX(a3)
        tst.b   wm_SpriteInterTbl(a3)
        beq.s   .obj
        clr.b   wm_SprObjStatus(a3)
        bra.s   .ret
.obj:   move.l  d2,-(sp)
        jsr     _spr_obj_interact
        addq.l  #4,sp
.ret:   movem.l (sp)+,d2-d3/a3
        rts
.unsup: tst.l   _mario_unsupported(a4)      ; spr_unsup (agua: sin portar)
        bne.s   .ret
        moveq   #MARIO_UNSUP_TILE,d0
        move.l  d0,_mario_unsupported(a4)
        bra.s   .ret

;----------------------------------------------------------------------
; void sprite_run(u8 x) = sprite_run de msprite.c (CODE_0180D2, los
; temporizadores, + HandleSprite) para el estado 8 de los sprites que
; conoce: pone SprProcessIndex, baja los 7 temporizadores y salta (tail
; call: la pila y el argumento x quedan como llegaron) a la rutina del
; sprite, que vuelve a quien llamo a sprite_run. Lo demas (estado 1 = init,
; 2-6, 9-B, y los sprites que no estan en la lista) lo hace
; sprite_run_post de msprite.c, en C, con los temporizadores ya bajados.
;
; AGREGAR UN SPRITE: un SPRMAIN con su numero y el simbolo de su rutina
; (la de msprite.c tiene que ser MSS, no static; ver P37). Sin la linea
; funciona igual por sprite_run_post -> sprite_main (C), solo mas lento.
; Solo usa d0-d1/a0-a1 (no guarda nada): la rutina saltada ve la pila
; de sprite_run.
;----------------------------------------------------------------------
DECT    macro                               ; if (t[x]) t[x]--  (a0 = ram + x)
        tst.b   \1(a0)
        beq.s   .d\@
        subq.b  #1,\1(a0)
.d\@:
        endm

SPRMAIN macro                               ; \1 = numero de sprite  \2 = rutina(x)
        cmp.b   #\1,d0
        beq     \2
        endm

        public  _sprite_run
_sprite_run:
        moveq   #0,d1
        move.b  4+3(sp),d1                  ; x
        lea     _ram(a4),a1
        lea     (a1,d1.w),a0                ; a0 = ram + x (x < 12: P40 ok)
        move.b  d1,wm_SprProcessIndex(a1)
        move.b  wm_SpriteStatus(a0),d0      ; st
        beq     .erase
        tst.b   wm_SpritesLocked(a1)
        bne.s   .nt
        DECT    wm_SpriteDecTbl1
        DECT    wm_SpriteDecTbl2
        DECT    wm_SpriteDecTbl3
        DECT    wm_SpriteDecTbl4
        DECT    wm_DisSprCapeContact
        DECT    wm_SpriteDecTbl5
        DECT    wm_SpriteDecTbl6
.nt:    subq.b  #8,d0
        bne.s   .post                       ; no es el estado 8
        clr.b   wm_SprPixelMove(a1)         ; sprite_main
        move.b  wm_SpriteNum(a0),d0
        ; ---- sprites con rutina propia (por frecuencia) ----
        SPRMAIN $ab,_rex_main_asm
        SPRMAIN $4f,_jumping_piranha
        SPRMAIN $8e,_warp_blocks
        SPRMAIN $c7,_invis_mushroom
        SPRMAIN $83,_flying_block
        SPRMAIN $b9,_info_box
        SPRMAIN $bd,_sliding_koopa
        SPRMAIN $02,_shellless_koopa
        SPRMAIN $9f,_banzai_bill
        SPRMAIN $95,_chuck_main             ; spr_chuck.c
        SPRMAIN $7b,_goal_tape              ; spr_goal.c
        ; ---- aca, una linea mas por sprite nuevo ----
.post:  bra     _sprite_run_post            ; el resto, en C (los mismos argumentos)
.erase: move.b  #$ff,wm_SprIndexInLvl(a0)   ; EraseSprite
        rts

;----------------------------------------------------------------------
; void spr_spr_interact(u8 y) = spr_spr_interact de msprite.c
; (SubSprSprInteract): la ranura y contra las de abajo (x = y-1 .. 0). Lo
; que depende solo de y se lee una vez (L2): si el filtro de y
; (Tweaker1686 bit 3, DecTbl4) falla, falla con todas las x y no pasa nada
; (ni CheckSprInter ni reaccion). Despues de una reaccion (sprspr_react, C)
; y puede haber cambiado: se vuelve a leer todo y sigue desde la x
; siguiente, como el C.
; d2 = y  d3 = x  d4 = X de y  d5 = Y de y + 10/2  d6 = BehindScrn de y
; a2 = ram  a3 = ram + y
;----------------------------------------------------------------------
        public  _spr_spr_interact
_spr_spr_interact:
        moveq   #0,d0
        move.b  4+3(sp),d0                  ; y
        beq     .ret0                       ; y = 0: nadie debajo
        move.b  _ram+wm_FrameA(a4),d1
        eor.b   d0,d1
        btst    #0,d1
        beq     .ret0                       ; solo las ranuras de paridad distinta a FrameA
        movem.l d2-d6/a2-a3,-(sp)
        move.l  d0,d2                       ; d2 = y (long limpio: se empuja entero)
        move.l  d0,d3                       ; d3 = x (limpio, 0..11)
        lea     _ram(a4),a2
        lea     (a2,d2.w),a3                ; P40 ok (y < 12)
.reload:
        move.b  wm_Tweaker1686(a3),d0
        and.b   #$08,d0
        or.b    wm_SpriteDecTbl4(a3),d0
        bne     .ret                        ; y no interactua con nadie
        move.b  wm_SprBehindScrn(a3),d6
        move.b  wm_SpriteXHi(a3),d4
        lsl.w   #8,d4
        move.b  wm_SpriteXLo(a3),d4         ; X de y
        move.b  wm_SpriteYHi(a3),d5
        lsl.w   #8,d5
        move.b  wm_SpriteYLo(a3),d5
        moveq   #2,d0
        move.b  wm_Tweaker1662(a3),d1
        and.b   #$0f,d1
        beq.s   .y2
        moveq   #10,d0
.y2:    add.w   d0,d5                       ; Y de y + 10 / 2
.loop:  subq.w  #1,d3
        bmi.s   .ret
        lea     (a2,d3.w),a1                ; P40 ok (x < 12)
        cmp.b   #$08,wm_SpriteStatus(a1)
        blo.s   .loop
        move.b  wm_Tweaker1686(a1),d0
        and.b   #$08,d0
        or.b    wm_SpriteDecTbl4(a1),d0
        or.b    wm_SpriteEatenTbl(a1),d0
        move.b  wm_SprBehindScrn(a1),d1
        eor.b   d6,d1
        or.b    d1,d0
        bne.s   .loop
        move.b  d3,wm_CheckSprInter(a2)
        move.b  wm_SpriteXHi(a1),d0
        lsl.w   #8,d0
        move.b  wm_SpriteXLo(a1),d0
        sub.w   d4,d0
        add.w   #$10,d0
        cmp.w   #$20,d0                     ; (u16)(a - b + $10) >= $20: lejos
        bhs.s   .loop
        move.b  wm_SpriteYHi(a1),d0
        lsl.w   #8,d0
        move.b  wm_SpriteYLo(a1),d0
        move.b  wm_Tweaker1662(a1),d1
        and.b   #$0f,d1
        beq.s   .a2
        addq.w  #8,d0                       ; +10 = 2 + 8
.a2:    addq.w  #2,d0
        sub.w   d5,d0
        add.w   #$0c,d0
        cmp.w   #$18,d0                     ; (u16)(a - b + $0C) >= $18: lejos
        bhs     .loop
        move.l  d3,-(sp)                    ; sprspr_react(y, x): CODE_01A4BA (C)
        move.l  d2,-(sp)
        bsr     _sprspr_react
        addq.l  #8,sp
        bra     .reload
.ret:   movem.l (sp)+,d2-d6/a2-a3
.ret0:  rts

;----------------------------------------------------------------------
; void spr_obj_interact(u8 x) = spr_obj_interact de msprite.c (CODE_019140,
; nivel horizontal, capa 1, sin agua): spr_obj_vert (C), el lado hacia
; donde va (spr_tile_asm), el empuje de los caparazones (spr_obj_push, C)
; y el aviso de agua. Con agua o nivel vertical: sin portar, como el C.
; d2 = x  a2 = ram  a3 = ram + x
;----------------------------------------------------------------------
        public  _spr_obj_interact
_spr_obj_interact:
        movem.l d2/a2-a3,-(sp)
        moveq   #0,d2
        move.b  12+7(sp),d2                 ; x
        lea     _ram(a4),a2
        lea     (a2,d2.w),a3                ; P40 ok (x < 12)
        clr.b   wm_SprMoveDownPixels(a2)
        clr.b   wm_SprObjStatus(a3)
        clr.b   wm_SpriteSlopeTbl(a3)
        clr.b   wm_TempTileGen(a2)
        move.b  wm_SprInWaterTbl(a3),wm_CheckSprInter(a2)
        clr.b   wm_SprInWaterTbl(a3)
        tst.b   wm_SpriteBuoyancy(a2)
        bne     .unsup
        tst.b   wm_IsVerticalLvl(a2)
        bmi     .unsup
        tst.b   wm_Tweaker1686(a3)
        bmi.s   .after
        CALLX   _spr_obj_vert
        move.b  wm_SpriteSpeedX(a3),d0      ; el lado hacia donde va
        beq.s   .zero
        rol.b   #1,d0
        and.w   #1,d0                       ; y = bit 7 de la velocidad
        bra.s   .tile
.zero:  tst.b   wm_Tweaker190F(a3)          ; parado, bit 7: un lado por frame
        bpl.s   .after
        tst.b   wm_SpriteDecTbl5(a3)
        bne.s   .after
        moveq   #1,d0
        and.b   wm_FrameA(a2),d0
.tile:  move.l  d0,-(sp)                    ; spr_tile(x, y)
        move.l  d2,-(sp)
        bsr     _spr_tile_asm
        addq.l  #8,sp
        move.b  d0,wm_SprOnTileXHi(a2)
        beq.s   .nobit
        move.b  wm_Map16NumLo(a2),d1
        cmp.b   #$11,d1
        blo.s   .nobit
        cmp.b   #$6e,d1
        bhs.s   .nobit
        moveq   #1,d0                       ; spr_obj_bit: tx_019134[m15] = 1 << m15
        move.b  _ram+m15(a4),d1
        lsl.b   d1,d0
        or.b    d0,wm_SprObjStatus(a3)
        move.b  wm_Map16NumLo(a2),wm_MirBlkCheck(a2)
.nobit: move.b  wm_Map16NumLo(a2),wm_SprOnTileXLo(a2)
.after: tst.b   wm_Tweaker190F(a3)
        bpl.s   .water
        moveq   #3,d0
        and.b   wm_SprObjStatus(a3),d0
        beq.s   .water
        CALLX   _spr_obj_push
        tst.l   d0
        bne.s   .ret
.water: move.b  wm_SprInWaterTbl(a3),d0
        cmp.b   wm_CheckSprInter(a2),d0
        beq.s   .ret
.unsup: tst.l   _mario_unsupported(a4)      ; spr_unsup
        bne.s   .ret
        moveq   #MARIO_UNSUP_TILE,d0
        move.l  d0,_mario_unsupported(a4)
.ret:   movem.l (sp)+,d2/a2-a3
        rts

;----------------------------------------------------------------------
; void spr_obj_vert(u8 x) = spr_obj_vert de msprite.c (CODE_0192C9: el
; bloque de arriba / abajo del sprite). Portado el techo y el suelo llano
; (tile < $6E, _0193B8); las pendientes y lo que sube 1 px y repite
; (tile >= $6E), y el caso raro $59-$5B con $1931 = $0E / $03, saltan al C
; (spr_obj_vert_c) con los mismos argumentos: antes de decidir solo se
; escribio lo que el C vuelve a escribir igual (spr_tile y SprOnTileY*).
; d2 = x  d3 = y (2 = abajo, 3 = arriba)  d1 = tile  a2 = ram  a3 = ram + x
;----------------------------------------------------------------------
        public  _spr_obj_vert
_spr_obj_vert:
        movem.l d2-d3/a2-a3,-(sp)
        moveq   #0,d2
        move.b  16+7(sp),d2                 ; x
        lea     _ram(a4),a2
        lea     (a2,d2.w),a3                ; P40 ok (x < 12)
        moveq   #2,d3
        tst.b   wm_SpriteSpeedY(a3)
        bpl.s   .go
        moveq   #3,d3
.go:    move.l  d3,-(sp)                    ; spr_tile(x, y)
        move.l  d2,-(sp)
        bsr     _spr_tile_asm
        addq.l  #8,sp
        move.b  d0,wm_SprOnTileYHi(a2)
        move.b  wm_Map16NumLo(a2),d1        ; t
        move.b  d1,wm_SprOnTileYLo(a2)
        tst.b   d0
        beq     .ret                        ; sin bloque
        cmp.b   #2,d3
        bne     .ceil
        cmp.b   #$59,d1                     ; el suelo
        blo.s   .f1
        cmp.b   #$5c,d1
        bhs.s   .f1
        move.b  $1931(a2),d0
        cmp.b   #$0e,d0
        beq     .toc
        cmp.b   #$03,d0
        beq     .toc
.f1:    cmp.b   #$11,d1
        bhs.s   .f2
        moveq   #$0f,d0                     ; tile < $11 (CODE_0193B0)
        and.b   _ram+m12(a4),d0
        cmp.b   #5,d0
        bhs     .ret
        bra.s   .b8
.f2:    cmp.b   #$6e,d1
        bhs     .toc                        ; pendiente / sube 1 px: el C
.b8:    btst    #2,wm_Tweaker1686(a3)       ; _0193B8
        bne.s   .bit
        move.b  wm_SpriteStatus(a3),d0
        cmp.b   #2,d0
        beq     .ret
        cmp.b   #5,d0
        beq     .ret
        cmp.b   #$0b,d0
        beq     .ret
        cmp.b   #$0c,d1
        beq.s   .t1
        cmp.b   #$0d,d1
        bne.s   .t2
.t1:    moveq   #3,d0
        and.b   wm_FrameA(a2),d0
        beq     .unsup
.t2:    tst.b   wm_SpriteEatenTbl(a3)
        bne.s   .bit
        moveq   #$f0-256,d0
        and.b   wm_SpriteYLo(a3),d0
        add.b   wm_SprMoveDownPixels(a2),d0
        move.b  d0,wm_SpriteYLo(a3)
.bit:   moveq   #1,d0                       ; spr_obj_bit: 1 << m15
        move.b  _ram+m15(a4),d1
        lsl.b   d1,d0
        or.b    d0,wm_SprObjStatus(a3)
.ret:   movem.l (sp)+,d2-d3/a2-a3
        rts
.ceil:  cmp.b   #$11,d1                     ; el techo
        blo.s   .ret
        cmp.b   #$6e,d1
        blo.s   .cb
        cmp.b   wm_LowestSolidSprTile(a2),d1
        blo.s   .ret
        cmp.b   wm_HighestSolidSprTile(a2),d1
        bhs.s   .ret
.cb:    move.b  d1,wm_SprOnBreakableBlk(a2)
        bra.s   .bit
.unsup: tst.l   _mario_unsupported(a4)      ; spr_unsup (los tiles $0C/$0D)
        bne.s   .ret
        moveq   #MARIO_UNSUP_TILE,d0
        move.l  d0,_mario_unsupported(a4)
        bra.s   .ret
.toc:   movem.l (sp)+,d2-d3/a2-a3           ; los argumentos siguen en la pila
        jmp     _spr_obj_vert_c

;----------------------------------------------------------------------
; void jumping_piranha(u8 x) = jumping_piranha de msprite.c (el $4F):
; dibujo (cabeza y tallo), temporizadores, contactos y los tres estados
; (en la tuberia, sube, baja). sprite_tweakers, get_draw_info1,
; sub_offscreen3 y mario_spr_interact siguen en C. El despachador de
; sprite_run salta aca (tail call).
; d2 = x  d3 = Y (u16)  a2 = ram  a3 = ram + x
;----------------------------------------------------------------------
        public  _jumping_piranha
_jumping_piranha:
        movem.l d2-d3/a2-a3,-(sp)
        moveq   #0,d2
        move.b  16+7(sp),d2                 ; x
        lea     _ram(a4),a2
        lea     (a2,d2.w),a3                ; P40 ok (x < 12)
        moveq   #0,d0
        move.b  wm_SpriteNum(a3),d0
        move.l  _tab_166e(a4),a0
        move.b  (a0,d0.w),d0
        and.b   #$0f,d0
        move.b  d0,wm_SpritePal(a3)         ; LoadSpriteTables
        CALLX   _sprite_tweakers
        ifd SPR_OAM
        CALLX   _piranha_gfx
        else
        move.b  wm_SpriteYHi(a3),d3
        lsl.w   #8,d3
        move.b  wm_SpriteYLo(a3),d3         ; y
        move.w  d3,d0
        addq.w  #8,d0                       ; el tallo, 8 px mas abajo
        move.b  d0,wm_SpriteYLo(a3)
        lsr.w   #8,d0
        move.b  d0,wm_SpriteYHi(a3)
        CALLX   _get_draw_info1
        move.b  d3,wm_SpriteYLo(a3)
        move.w  d3,d0
        lsr.w   #8,d0
        move.b  d0,wm_SpriteYHi(a3)
        move.b  wm_SpriteMiscTbl3(a3),d0
        and.b   #$04,d0
        lsr.b   #2,d0
        addq.b  #1,d0
        move.b  d0,wm_SpriteGfxTbl(a3)
        move.b  #$0a,wm_SpritePal(a3)
        endif
        tst.b   wm_SpritesLocked(a2)
        bne     .ret
        CALLX   _sub_offscreen3
        CALLX   _spr_spr_interact
        CALLX   _mario_spr_interact
        clr.l   -(sp)                       ; spr_pos_axis(x, 0)
        move.l  d2,-(sp)
        bsr     _spr_pos_axis_asm
        addq.l  #8,sp
        move.b  wm_SpriteState(a3),d0
        beq.s   .s0
        subq.b  #1,d0
        beq.s   .s1
        subq.b  #1,d0
        beq     .s2
        tst.l   _mario_unsupported(a4)      ; spr_unsup
        bne     .ret
        moveq   #MARIO_UNSUP_TILE,d0
        move.l  d0,_mario_unsupported(a4)
        bra     .ret
.s0:    clr.b   wm_SpriteSpeedY(a3)         ; en la tuberia
        tst.b   wm_SpriteDecTbl1(a3)
        bne     .ret
        move.b  wm_MarioXPos(a2),d0
        sub.b   wm_SpriteXLo(a3),d0
        move.b  d0,_ram+m15(a4)
        add.b   #$1b,d0
        cmp.b   #$37,d0
        blo     .ret                        ; Mario cerca: no sale
        move.b  #$c0,wm_SpriteSpeedY(a3)
        move.b  #1,wm_SpriteState(a3)
        clr.b   wm_SpriteGfxTbl(a3)
        bra     .ret
.s1:    move.b  wm_SpriteSpeedY(a3),d0      ; sube frenando
        bmi.s   .s1a
        cmp.b   #$40,d0
        bhs.s   .s1b
.s1a:   addq.b  #2,d0
        move.b  d0,wm_SpriteSpeedY(a3)
.s1b:   addq.b  #1,wm_SpriteMiscTbl6(a3)
        move.b  wm_SpriteSpeedY(a3),d0
        sub.b   #$f0,d0
        bmi.s   .ret
        move.b  #$50,wm_SpriteDecTbl1(a3)
        move.b  #2,wm_SpriteState(a3)
        bra.s   .ret
.s2:    addq.b  #1,wm_SpriteMiscTbl3(a3)    ; baja flotando
        addq.b  #1,wm_SpriteMiscTbl6(a3)
        moveq   #3,d0
        and.b   wm_FrameB(a2),d0
        bne.s   .s2a
        move.b  wm_SpriteSpeedY(a3),d0
        sub.b   #$08,d0
        bpl.s   .s2a
        addq.b  #1,wm_SpriteSpeedY(a3)
.s2a:   CALLX   _spr_obj_interact
        btst    #2,wm_SprObjStatus(a3)
        beq.s   .ret
        clr.b   wm_SpriteState(a3)
        move.b  #$40,wm_SpriteDecTbl1(a3)
.ret:   movem.l (sp)+,d2-d3/a2-a3
        rts

;----------------------------------------------------------------------
; u16 f7f4(u16 limit, u16 bg1v) = f7f4_c de mcam.c (CODE_00F7F4, el scroll
; vertical de la capa 1). Hacia arriba (v2 < 0) salta al C, que vuelve a
; escribir igual m0, m2, m4 y las direcciones antes de seguir.
; d1 = a / v2  d2 = y  d3 = limit  d4 = bg1v  d5 = valor de tabla
;----------------------------------------------------------------------
T16Y    macro                               ; \2.w = T16X(\1, y), y en d2
        lea     _rom00+(\1-ROM00_BASE)(a4),a0
        move.b  1(a0,d2.w),\2
        lsl.w   #8,\2
        move.b  (a0,d2.w),\2
        endm

        public  _f7f4
_f7f4:
        tst.b   _ram+wm_VertScrollHead(a4)
        bne.s   .on
        moveq   #0,d0
        move.w  10(sp),d0                   ; bg1v
        rts
.on:    movem.l d2-d5/a2,-(sp)
        lea     _ram(a4),a2
        move.w  20+6(sp),d3                 ; limit
        move.w  20+10(sp),d4                ; bg1v
        WR16    m4,d3
        moveq   #0,d2
        RD16    wm_MarioYPos,d1
        sub.w   d4,d1                       ; v0
        WR16    m0,d1
        move.w  d1,d0
        sub.w   #$0070,d0
        bmi.s   .y0
        moveq   #2,d2
.y0:    move.b  d2,wm_Layer1ScrollDir(a2)
        move.b  d2,wm_Layer2ScrollDir(a2)
        T16Y    DATA_00F69F,d5
        sub.w   d5,d1                       ; v2
        move.w  d1,d0                       ; (v2 ^ T16X(DATA_00F6A3, y)) & $8000
        lsr.w   #8,d0
        lea     _rom00+(DATA_00F6A3-ROM00_BASE)(a4),a0
        move.b  1(a0,d2.w),d5
        eor.b   d5,d0
        bmi.s   .keep
        moveq   #2,d2
        moveq   #0,d1
.keep:  WR16    m2,d1
        tst.w   d1
        bmi.s   .up
        clr.b   wm_ScrScrollToPlayer(a2)
.f883:  T16Y    DATA_00F6A7,d5              ; _00F883: limita la velocidad
        move.w  d1,d0
        sub.w   d5,d0
        eor.w   d5,d0
        bmi.s   .nc
        move.w  d5,d1
.nc:    add.w   d4,d1                       ; a + bg1v
        T16Y    DATA_00F6AD,d5
        move.w  d1,d0
        sub.w   d5,d0
        bpl.s   .ok
        move.w  d5,d1
.ok:    move.w  d1,d4                       ; bg1v = a
        moveq   #0,d0
        move.w  d3,d0
        sub.w   d4,d0
        bmi.s   .lim
        moveq   #0,d0
        move.w  d4,d0
        bra.s   .out
.lim:   clr.b   wm_EnableVertScroll(a2)
        moveq   #0,d0
        move.w  d3,d0
.out:   movem.l (sp)+,d2-d5/a2
        rts
.up:    move.b  wm_WallWalkStatus(a2),d5    ; CODE_00F82A: hacia arriba (P69)
        cmp.b   #$06,d5
        bhs.s   .xtst
        move.b  wm_YoshiHasWingsB(a2),d5
        lsr.b   #1,d5
        or.b    wm_GlideTimer(a2),d5
        or.b    wm_IsClimbing(a2),d5
        or.b    wm_PBalloonFrame(a2),d5
        or.b    wm_IsInLakituCloud(a2),d5
        or.b    wm_BouncingWithYoshi(a2),d5
.xtst:  tst.b   d5
        bne.s   .xset
        tst.b   wm_OnYoshi(a2)
        beq.s   .swim
        move.b  wm_YoshiHasWings(a2),d5
        cmp.b   #$02,d5
        bhs.s   .xset
.swim:  moveq   #0,d5                       ; (con Yoshi con alas < 2 no hay x)
        tst.b   wm_IsSwimming(a2)
        beq.s   .xnone
        move.b  wm_IsFlying(a2),d5
        bne.s   .xset
.xnone: cmp.b   #1,wm_VertScrollHead(a2)
        beq.s   .en
        tst.b   wm_EnableVertScroll(a2)
        beq.s   .y4
.en:    tst.b   wm_ScrScrollToPlayer(a2)
        bne.s   .f881
        tst.b   wm_IsFlying(a2)
        bne.s   .same                       ; return bg1v
        addq.b  #1,wm_ScrScrollToPlayer(a2)
.f881:  bra     .f883                       ; a = v2 (d1), y en d2
.xset:  move.b  d5,wm_EnableVertScroll(a2)
        bra     .f883
.y4:    moveq   #4,d2
        bra     .f883
.same:  moveq   #0,d0
        move.w  d4,d0
        bra     .out

;----------------------------------------------------------------------
; void mario_E2BD(void) = mario_E2BD_c de mgfx.c (CODE_00E2BD: paleta,
; MarioScrPosX/Y, las 4 entradas de OAM de Mario y CODE_00F636, los
; punteros de DMA). Solo el build NOOAM (el de la Amiga): la OAM va a
; mario_oam / mario_osz. Cae al C, ANTES de escribir nada, cuando:
;   - PowerUp = 2 (capa: el C la marca sin portar);
;   - MarioFrame >= $46 o MarioDirection > 1: el indice de DATA_00DCEC /
;     DATA_00DD32 se sale de la tabla. Dentro del rango, m5v <= $80 + 6 y
;     las palabras de DATA_00DD4E / DATA_00DE32 son un byte con el signo
;     extendido (comprobado contra rom00 por tools/lint_port.py): se leen
;     como bytes + ext.w en vez de armar la palabra (-30 ciclos por lectura).
; Lo que no se calcula porque es constante (no cambia lo que se escribe):
;   - m4 termina siempre en $80 (m4v = $C8/$E8, 4 x ASL), y el bit de
;     tamano de cada entrada es 2,2,e,0 (e = 2 con MarioFrame = $43);
;   - en f636 el acarreo del segundo ROR es siempre 0 (la mascara $F700
;     deja el byte bajo en 0): el valor es (m & $F7) << 6 + (m & 8) << 11
;     + $2000, que sale de las tablas f636hi / f636lo (byte alto y bajo);
;   - la entrada y de DATA_00E2B2 (solo la usa la OAM de la SNES) no se lee.
; Los valores de a+$200 de f636 comparten el byte bajo: solo cambia el alto.
; d1 = m6v  d3 = e (tamano de la 3.a entrada: 2 con MarioFrame = $43)
; d4 = hp  d5 = Y en pantalla + $10  d6 = X en pantalla + $80  d7 = m5v
; a0 = Mario8x8Tiles  a1 = DATA_00DD4E + $72 (DATA_00DE32 = a1 + $72)
;----------------------------------------------------------------------
        ifnd    DATA_00E2A2
DATA_00E2A2 equ $E2A2                       ; (mgfx.c: el generador no las lee)
        endc
        ifnd    MarioPalIndex
MarioPalIndex equ $E18C
        endc
MEV_SPRITE equ  1024                        ; enum de mario.h

OAM1    macro                               ; \1 = k (0-3)  \2 = tamano (9: d3)
        btst    #\1,d4
        bne.s   .h\@                        ; oculto: cc = 1
        move.b  (a0,d1.w),d0                ; Mario8x8Tiles[m6v] ; P40 ok
        bmi.s   .n\@                        ; tile negativo: cc = 0
        move.b  d0,_mario_oam+2+4*\1(a4)
        move.b  $72(a1,d7.w),d0             ; DATA_00DE32 (ext) ; P40 ok
        ext.w   d0
        add.w   d5,d0                       ; w + $10
        cmp.w   #$100,d0
        bhs.s   .h\@                        ; fuera por Y: cc = 1
        sub.b   #$10,d0
        move.b  d0,_mario_oam+1+4*\1(a4)
        move.b  -$72(a1,d7.w),d0            ; DATA_00DD4E (ext) ; P40 ok
        ext.w   d0
        add.w   d6,d0                       ; w + $80
        cmp.w   #$200,d0
        bhs.s   .h\@                        ; fuera por X: cc = 1
        sub.w   #$80,d0
        move.b  d0,_mario_oam+4*\1(a4)
        ifeq    \2-9
        move.b  d3,d2
        else
        moveq   #\2,d2
        endc
        btst    #8,d0                       ; cc = bit 8 de la X
        beq.s   .s\@
        addq.b  #1,d2
        bra.s   .s\@
.h\@:   ifeq    \2-9
        move.b  d3,d2
        else
        moveq   #\2,d2
        endc
        addq.b  #1,d2
        bra.s   .s\@
.n\@:   ifeq    \2-9
        move.b  d3,d2
        else
        moveq   #\2,d2
        endc
.s\@:   move.b  d2,_mario_osz+\1(a4)
        addq.b  #2,d7                       ; m5v += 2
        addq.b  #1,d1                       ; m6v++
        endm

F636P   macro                               ; a = d2:d3 (alto:bajo) en \1 y a + $200 en \2
        move.b  d3,_ram+\1(a4)
        move.b  d3,_ram+\2(a4)
        move.b  d2,_ram+\1+1(a4)
        addq.b  #2,d2
        move.b  d2,_ram+\2+1(a4)
        endm

        ifnd    E2BD_OFF                    ; (E2BD_OFF: build con OAM, CDEFS= en logicbench_build.sh)
        public  _mario_E2BD
_mario_E2BD:
        cmp.b   #$46,_ram+wm_MarioFrame(a4)
        bhs     .c
        cmp.b   #$02,_ram+wm_MarioDirection(a4)
        bhs     .c
        cmp.b   #$02,_ram+wm_MarioPowerUp(a4)
        beq     .c
        moveq   #-16,d0                     ; las 4 entradas fuera de pantalla
        move.b  d0,_mario_oam+1(a4)
        move.b  d0,_mario_oam+5(a4)
        move.b  d0,_mario_oam+9(a4)
        move.b  d0,_mario_oam+13(a4)
        move.b  _ram+wm_HidePlayer(a4),d1
        cmp.b   #$ff,d1
        beq.s   .noyo
        tst.b   _ram+wm_LooseYoshiFlag(a4)
        beq.s   .noyo
        tst.l   _mario_unsupported(a4)      ; Yoshi suelto: sin portar
        bne.s   .rts
        moveq   #MARIO_UNSUP_YOSHI,d0
        move.l  d0,_mario_unsupported(a4)
.rts:   rts
.noyo:  movem.l d2-d7,-(sp)
        move.b  d1,d4                       ; hp
        moveq   #0,d0
        move.b  _ram+wm_FlashingPalTimer(a4),d2
        bne.s   .shift
        move.b  _ram+wm_StarPowerTimer(a4),d2   ; y
        bne.s   .star
        move.b  _ram+wm_MarioPowerUp(a4),d0     ; CODE_00E314
        add.b   d0,d0
        or.b    _ram+wm_OWCharA(a4),d0
        bra.s   .e31a
.star:  cmp.b   #$ff,d4
        beq.s   .nodec
        move.b  _ram+wm_FrameB(a4),d0
        and.b   #$03,d0
        bne.s   .nodec
        subq.b  #1,_ram+wm_StarPowerTimer(a4)
.nodec: move.b  _ram+wm_FrameA(a4),d0
        cmp.b   #$1e,d2
        bhi.s   .e30c
        bne.s   .shift
        or.l    #MEV_SPRITE,_mario_events(a4)   ; vuelve la musica
.shift: move.b  _ram+wm_FrameA(a4),d0
        lsr.b   #2,d0
.e30c:  and.b   #$03,d0
        addq.b  #4,d0
.e31a:  move.b  d0,_mario_pal(a4)
        add.b   d0,d0                       ; (u8)(a << 1)
        lea     _rom00+(DATA_00E2A2-ROM00_BASE)(a4),a0
        move.b  (a0,d0.w),_ram+wm_PlayerPalPtr(a4)      ; P40 ok
        move.b  1(a0,d0.w),_ram+wm_PlayerPalPtr+1(a4)   ; P40 ok
        ; MarioScrPosX = MarioXPos - Bg1HOfs - (acarreo ? 0 : 1)
        moveq   #0,d2
        move.b  _ram+wm_MarioFrame(a4),d2   ; x
        move.w  _ram+wm_MarioXPos(a4),d6
        ror.w   #8,d6                       ; little endian (direccion par)
        move.w  _ram+wm_Bg1HOfs(a4),d1
        ror.w   #8,d1
        sub.w   d1,d6
        move.b  _ram+wm_WallWalkStatus(a4),d1
        cmp.b   #$05,d1
        bls.s   .xc                         ; WallWalkStatus <= 5: acarreo 1
        tst.b   _ram+wm_MarioPowerUp(a4)
        beq.s   .xr
        cmp.b   #$13,d2
        bne.s   .xn
.xr:    eori.b  #$01,d1
.xn:    btst    #0,d1                       ; LSR: acarreo = bit 0
        bne.s   .xc
        subq.w  #1,d6
.xc:    move.b  d6,_ram+wm_MarioScrPosX(a4)
        move.w  d6,-(sp)                    ; byte alto, sin desplazar
        move.b  (sp)+,_ram+wm_MarioScrPosX+1(a4)
        ; MarioScrPosY = PlayerImgYPos + MarioYPos - (PowerUp ? 0 : 1)
        ;                - Bg1VOfs - (acarreo ? 0 : 1) (+ 2 con MarioFrame = $1C)
        moveq   #0,d1                       ; y
        moveq   #0,d0                       ; ajuste
        tst.b   _ram+wm_MarioPowerUp(a4)
        beq.s   .p0
        moveq   #1,d1
        bra.s   .p1
.p0:    moveq   #-1,d0
.p1:    cmp.b   #$0a,d2
        bhs.s   .yc
        cmp.b   _ram+wm_PlayerWalkPose(a4),d1
        bhs.s   .yc                         ; y >= PlayerWalkPose: acarreo 1
        subq.w  #1,d0
.yc:    cmp.b   #$1c,d2
        bne.s   .yn
        addq.w  #2,d0
.yn:    moveq   #0,d5
        move.b  _ram+wm_PlayerImgYPos(a4),d5
        add.w   d0,d5
        move.w  _ram+wm_MarioYPos(a4),d3
        ror.w   #8,d3
        add.w   d3,d5
        move.w  _ram+wm_Bg1VOfs(a4),d3
        ror.w   #8,d3
        sub.w   d3,d5
        move.b  d5,_ram+wm_MarioScrPosY(a4)
        move.w  d5,-(sp)
        move.b  (sp)+,_ram+wm_MarioScrPosY+1(a4)
        move.b  _ram+wm_PlayerHurtTimer(a4),d0
        beq.s   .draw
        moveq   #0,d1
        move.b  d0,d1
        lsr.b   #3,d1
        lea     _rom00+(DATA_00E292-ROM00_BASE)(a4),a0
        and.b   (a0,d1.w),d0                ; P40 ok
        or.b    _ram+wm_SpritesLocked(a4),d0
        or.b    _ram+wm_IsFrozen(a4),d0
        beq     .ret                        ; parpadeo: este frame no se dibuja
        ; CODE_00E385
.draw:  add.w   #$10,d5
        add.w   #$80,d6
        moveq   #0,d3
        cmp.b   #$43,d2
        bne.s   .m4a
        moveq   #2,d3                       ; m4v = $E8: la 3.a entrada es 16x16
.m4a:   cmp.b   #$29,d2
        bne.s   .m4b
        tst.b   _ram+wm_MarioPowerUp(a4)
        bne.s   .m4b
        moveq   #$20,d2
.m4b:   lea     _rom00+(DATA_00DCEC-ROM00_BASE)(a4),a0
        moveq   #0,d0
        move.b  (a0,d2.w),d0                ; P40 ok
        or.b    _ram+wm_MarioDirection(a4),d0
        lea     _rom00+(DATA_00DD32-ROM00_BASE)(a4),a0
        moveq   #0,d7
        move.b  (a0,d0.w),d7                ; m5v ; P40 ok
        moveq   #0,d0
        move.b  _ram+wm_MarioFrame(a4),d0
        cmp.b   #$3d,d0
        bhs.s   .ty
        moveq   #0,d1
        move.b  _ram+wm_MarioPowerUp(a4),d1
        lea     _rom00+(TilesetIndex-ROM00_BASE)(a4),a0
        add.b   (a0,d1.w),d0                ; P40 ok
.ty:    lea     _rom00+(TileExpansion-ROM00_BASE)(a4),a0
        moveq   #0,d1
        move.b  (a0,d0.w),d1                ; m6v ; P40 ok
        lea     _rom00+(DATA_00E00C-ROM00_BASE)(a4),a0
        move.b  (a0,d0.w),_ram+m10(a4)      ; P40 ok
        lea     _rom00+(DATA_00E0CC-ROM00_BASE)(a4),a0
        move.b  (a0,d0.w),_ram+m11(a4)      ; P40 ok
        move.b  _ram+wm_SpriteProp(a4),d0
        move.b  _ram+wm_IsBehindScenery(a4),d2
        beq.s   .nb
        lea     _rom00+(DATA_00E2B9-ROM00_BASE)(a4),a0
        move.b  (a0,d2.w),d0                ; P40 ok
.nb:    move.b  _ram+wm_MarioDirection(a4),d2
        lea     _rom00+(MarioPalIndex-ROM00_BASE)(a4),a0
        or.b    (a0,d2.w),d0                ; P40 ok
        move.b  d0,_mario_oam+3(a4)
        move.b  d0,_mario_oam+7(a4)
        move.b  d0,_mario_oam+15(a4)
        tst.b   d3
        beq.s   .nx
        eori.b  #$40,d0                     ; m4v = $E8
.nx:    move.b  d0,_mario_oam+11(a4)
        lea     _rom00+(Mario8x8Tiles-ROM00_BASE)(a4),a0
        lea     _rom00+(DATA_00DD4E-ROM00_BASE+$72)(a4),a1
        OAM1    0,2
        OAM1    1,2
        OAM1    2,9
        OAM1    3,0
        lsr.b   #4,d4
        move.b  d4,_ram+wm_HidePlayer(a4)
        move.b  #$80,_ram+m4(a4)
        move.b  d7,_ram+m5(a4)
        move.b  d1,_ram+m6(a4)
        ; CODE_00F636: punteros de DMA a los graficos
        lea     f636hi(pc),a0
        lea     f636lo(pc),a1
        moveq   #0,d0
        move.b  _ram+m10(a4),d0
        move.b  (a0,d0.w),d2                ; P40 ok
        move.b  (a1,d0.w),d3                ; P40 ok
        F636P   wm_0D85,wm_0D85+10
        moveq   #0,d0
        move.b  _ram+m11(a4),d0
        move.b  (a0,d0.w),d2                ; P40 ok
        move.b  (a1,d0.w),d3                ; P40 ok
        F636P   wm_0D85+2,wm_0D85+12
        move.b  _ram+m12(a4),d3             ; (m12 << 8) >> 3 + $2000
        move.b  d3,d2
        lsr.b   #3,d2
        add.b   #$20,d2
        lsl.b   #5,d3
        F636P   wm_0D85+4,wm_0D85+14
        move.b  _ram+m13(a4),d3
        move.b  d3,d2
        lsr.b   #3,d2
        add.b   #$20,d2
        lsl.b   #5,d3
        move.b  d3,_ram+wm_Tile7FPtr(a4)
        move.b  d2,_ram+wm_Tile7FPtr+1(a4)
        move.b  #$0a,_ram+wm_PlayerDmaTiles(a4)
.ret:   movem.l (sp)+,d2-d7
        rts
.c:     jmp     _mario_E2BD_c

f636n   set     0                           ; f636: (m & $F7) << 6 + (m & 8) << 11 + $2000
f636hi: rept    256
        dc.b    (((f636n&$f7)<<6)+((f636n&8)<<11)+$2000)>>8
f636n   set     f636n+1
        endr
f636n   set     0
f636lo: rept    256
        dc.b    (((f636n&$f7)<<6)+((f636n&8)<<11)+$2000)&$ff
f636n   set     f636n+1
        endr
        even
        endc
