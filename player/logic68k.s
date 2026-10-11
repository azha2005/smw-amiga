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
; SW-S: los motores de puntos, humo y sprites extendidos menores, sin el
; dibujo. Al principio del fichero: el C que llama a give_points,
; contact_gfx... queda a menos de 32 KB (P102). La referencia es el C de msprite.c (#ifndef LOGIC68K), que la
; biblioteca del PC compila y m68kverify --cross compara llamada a llamada;
; la puerta contra la SNES es tools/sws_cmp.py (RAM de los tres motores).
;----------------------------------------------------------------------

; --- give_lives_tick ---
; entrada:  a4 = datos del C
; salida:   CODE_028AB1, el principio: las vidas pendientes, una cada $23
; registros destruidos: ninguno
; ciclos:   tools/l_funcs.py
        public  _give_lives_tick
_give_lives_tick:
        tst.b   _ram+wm_GiveLives(a4)
        beq.s   .r
        tst.b   _ram+wm_GiveLifeTimer(a4)
        beq.s   .g
        subq.b  #1,_ram+wm_GiveLifeTimer(a4)
.r:     rts
.g:     subq.b  #1,_ram+wm_GiveLives(a4)
        beq.s   .s
        move.b  #$23,_ram+wm_GiveLifeTimer(a4)
.s:     move.b  #$05,_ram+wm_SoundCh3(a4)
        addq.b  #1,_ram+wm_StatusLives(a4)
        rts

; --- score_slot ---
; entrada:  a4 = datos del C
; salida:   d0.w = ranura de puntos (CODE_02AD34): la libre mas alta o la
;           siguiente de la rueda (ScoreSprIndex)
; registros destruidos: d0/a0 (d1 se conserva: lo usa ss_spawn)
; ciclos:   tools/l_funcs.py
        public  _score_slot
_score_slot:
        lea     _ram+wm_ScoreSprNum(a4),a0
        moveq   #5,d0
.l:     tst.b   (a0,d0.w)
        beq.s   .r
        dbf     d0,.l
        subq.b  #1,_ram+wm_ScoreSprIndex(a4)
        bpl.s   .o
        move.b  #5,_ram+wm_ScoreSprIndex(a4)
.o:     moveq   #0,d0
        move.b  _ram+wm_ScoreSprIndex(a4),d0
.r:     rts

; --- give_points / score_spawn ---
; entrada:  pila vbcc = u8 x, u8 a (give_points: sprite a + 5) o u8 x,
;           u8 n (score_spawn); a4 = datos del C
; salida:   el sprite de puntos sobre el sprite x (CODE_02ACEF)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
        public  _give_points
_give_points:
        moveq   #0,d1
        move.b  7(sp),d1
        move.b  11(sp),d0
        addq.b  #5,d0
        bra.s   ss_spawn
        public  _score_spawn
_score_spawn:
        moveq   #0,d1
        move.b  7(sp),d1
        move.b  11(sp),d0
; d1.w = x, d0.b = n
ss_spawn:
        movem.l d2-d3,-(sp)
        move.b  d0,d3
        bsr.s   _score_slot                 ; d0.w = y
        lea     _ram+wm_ScoreSprNum(a4),a0
        move.b  d3,(a0,d0.w)
        lea     _ram+wm_SpriteYHi(a4),a0
        move.b  (a0,d1.w),d2
        lsl.w   #8,d2
        lea     _ram+wm_SpriteYLo(a4),a0
        move.b  (a0,d1.w),d2
        subq.w  #8,d2                       ; y - 8
        move.b  d2,d3
        sub.b   _ram+wm_Bg1VOfs(a4),d3
        cmp.b   #$f0,d3                     ; CMP #$F0 deja C: el ADC #$10
        blo.s   .n                          ; suma $11
        add.w   #$11,d2
.n:     lea     _ram+wm_ScoreSprYLo(a4),a0
        move.b  d2,(a0,d0.w)
        lsr.w   #8,d2
        lea     _ram+wm_ScoreSprYHi(a4),a0
        move.b  d2,(a0,d0.w)
        lea     _ram+wm_SpriteXLo(a4),a0
        lea     _ram+wm_ScoreSprXLo(a4),a1
        move.b  (a0,d1.w),(a1,d0.w)
        lea     _ram+wm_SpriteXHi(a4),a0
        lea     _ram+wm_ScoreSprXHi(a4),a1
        move.b  (a0,d1.w),(a1,d0.w)
        lea     _ram+wm_ScoreSprSpeedY(a4),a0
        move.b  #$30,(a0,d0.w)
        movem.l (sp)+,d2-d3
        rts

; --- score_update ---
; entrada:  a4 = datos del C
; salida:   ScoreSprGfx sin el dibujo: las 6 ranuras de la 5 a la 0 suben,
;           suman la puntuacion (o vidas / monedas) al pasar SpeedY por $2A
;           y se borran
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
        public  _score_update
_score_update:
        cmp.b   #$c1,_ram+wm_LevelMode(a4)  ; (LevelMode & $40) y == $C1
        beq     .ret
        lea     _ram+wm_ScoreSprNum(a4),a0  ; lo normal: ninguno (el bucle
        move.b  (a0)+,d0                    ; deja SprProcessIndex = 0)
        rept    5
        or.b    (a0)+,d0
        endr
        bne.s   .go
        clr.b   _ram+wm_SprProcessIndex(a4)
        rts
.go:    movem.l d2-d3,-(sp)
        moveq   #5,d1
.lp:    move.b  d1,_ram+wm_SprProcessIndex(a4)
        lea     _ram+wm_ScoreSprNum(a4),a0
        move.b  (a0,d1.w),d3                ; d3 = n
        beq     .nx
        tst.b   _ram+wm_SpritesLocked(a4)
        bne     .nx
        lea     _ram+wm_ScoreSprSpeedY(a4),a1
        move.b  (a1,d1.w),d2
        bne.s   .v
        clr.b   (a0,d1.w)
        bra     .nx
.v:     subq.b  #1,(a1,d1.w)
        cmp.b   #$2a,d2
        bne.s   .mv
        moveq   #0,d0
        move.b  d3,d0
        lea     ss_coins-13(pc),a0
        cmp.b   #$0d,d3
        blo.s   .pts
        cmp.b   #$11,d3
        bhs.s   .coin
        move.b  (a0,d0.w),d0                ; CODE_02AE03: 1-UP ...
        add.b   d0,_ram+wm_GiveLives(a4)
        clr.b   _ram+wm_GiveLifeTimer(a4)
        bra.s   .mv
.coin:  move.b  (a0,d0.w),d0                ; ADDR_05B329
        move.b  #$01,_ram+wm_SoundCh3(a4)
        add.b   d0,_ram+wm_CoinAdder(a4)
        tst.b   _ram+wm_GreenStarCoins(a4)
        beq.s   .pts
        sub.b   d0,_ram+wm_GreenStarCoins(a4)
        bpl.s   .pts
        clr.b   _ram+wm_GreenStarCoins(a4)
.pts:   moveq   #0,d0                       ; CODE_02AE12
        move.b  _ram+wm_OWCharA(a4),d0
        move.w  d0,d2
        add.w   d0,d0
        add.w   d2,d0                       ; 3 * jugador
        lea     _ram+wm_MarioScoreHi(a4),a0
        add.w   d0,a0
        moveq   #0,d2
        move.b  d3,d2
        lea     ss_tab(pc),a1
        add.w   d2,a1
        move.b  (a1),d0
        move.b  17(a1),d2
        add.b   d0,(a0)                     ; X = el carry (move y moveq no
        move.b  1(a0),d0                    ; lo tocan)
        addx.b  d2,d0
        move.b  d0,1(a0)
        moveq   #0,d2
        move.b  2(a0),d0
        addx.b  d2,d0
        move.b  d0,2(a0)
.mv:    lea     _ram+wm_ScoreSprSpeedY(a4),a1
        move.b  (a1,d1.w),d0
        lsr.b   #4,d0
        and.w   #$0f,d0
        lea     ss_tab+34(pc),a0            ; PointSpeedY (y lo que sigue)
        move.b  (a0,d0.w),d0
        and.b   _ram+wm_FrameA(a4),d0
        bne.s   .nx
        lea     _ram+wm_ScoreSprYLo(a4),a0  ; _02AE38: sube, sin pasar del borde
        move.b  (a0,d1.w),d0
        move.b  d0,d2
        sub.b   _ram+wm_Bg1VOfs(a4),d2
        cmp.b   #4,d2
        blo.s   .nx
        subq.b  #1,(a0,d1.w)
        tst.b   d0
        bne.s   .nx
        lea     _ram+wm_ScoreSprYHi(a4),a0
        subq.b  #1,(a0,d1.w)
.nx:    dbf     d1,.lp
        movem.l (sp)+,d2-d3
.ret:   rts

; PointMultiplierLo (17), PointMultiplierHi (17), PointSpeedY (4) y
; DATA_02AD9E (6), contiguas como en la ROM (CODE_02AE12 con n >= $11 lee
; las de la tabla siguiente)
ss_tab: dc.b    $00,$01,$02,$04,$08,$0A,$14,$28,$50,$64,$C8,$90,$20,$00,$00,$00,$00
        dc.b    $00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$00,$01,$03,$00,$00,$00,$00
        dc.b    $03,$01,$00,$00
        dc.b    $B0,$B8,$C0,$C8,$D0,$D8
ss_coins:
        dc.b    $01,$02,$03,$05,$05,$0A,$0F,$14,$19     ; CoinsToGive
        even

; --- mex_slot ---
; entrada:  a4 = datos del C
; salida:   d0.w = ranura de sprite menor: la libre mas alta o la siguiente
;           de la rueda (DelOldExSpr)
; registros destruidos: d0/a0 (d1-d3 se conservan: lo usa smoke_update)
; ciclos:   tools/l_funcs.py
        public  _mex_slot
_mex_slot:
        lea     _ram+wm_MExSprNum(a4),a0
        moveq   #11,d0
.l:     tst.b   (a0,d0.w)
        beq.s   .r
        dbf     d0,.l
        subq.b  #1,_ram+wm_DelOldExSpr(a4)
        bpl.s   .o
        move.b  #$0b,_ram+wm_DelOldExSpr(a4)
.o:     moveq   #0,d0
        move.b  _ram+wm_DelOldExSpr(a4),d0
.r:     rts

sm_dx:  dc.b    $04,$08,$04,$00             ; DATA_0298C2
sm_dy:  dc.b    $FC,$04,$0C,$04             ; DATA_0298C6

; --- mex_update ---
; entrada:  a4 = datos del C
; salida:   CODE_028B67 sin el dibujo: los 12 sprites menores, de la 11 a
;           la 0. Solo los tipos de YI1: 1 = trozo de bloque (CODE_028F8B),
;           2 y 5 = destello (CODE_028ED2); los demas quedan quietos
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
        public  _mex_update
_mex_update:
        lea     _ram+wm_MExSprNum(a4),a0    ; lo normal: ninguno
        move.b  (a0)+,d0
        rept    11
        or.b    (a0)+,d0
        endr
        bne.s   .go
        rts
.go:    movem.l d2-d3/a2,-(sp)
        moveq   #11,d1
.lp:    lea     _ram+wm_MExSprNum(a4),a0
        move.b  (a0,d1.w),d0
        beq     .nx
        move.b  d1,_ram+wm_ExSprIndexM(a4)
        cmp.b   #1,d0
        beq.s   .t1
        cmp.b   #2,d0
        beq.s   .t2
        cmp.b   #5,d0
        bne     .nx
.t2:    lea     _ram+wm_MExSprTimer(a4),a1  ; CODE_028ED2
        tst.b   (a1,d1.w)
        beq     .kill
        tst.b   _ram+wm_SpritesLocked(a4)
        bne.s   .t2c
        subq.b  #1,(a1,d1.w)
.t2c:   lea     _ram+wm_MExSprXLo(a4),a1
        move.b  (a1,d1.w),d0
        sub.b   _ram+wm_Bg1HOfs(a4),d0
        cmp.b   #$f0,d0
        bhs     .kill
        lea     _ram+wm_MExSprYLo(a4),a1
        move.b  (a1,d1.w),d0
        sub.b   _ram+wm_Bg1VOfs(a4),d0
        cmp.b   #$f0,d0
        bhs     .kill
        bra     .nx
.t1:    tst.b   _ram+wm_SpritesLocked(a4)   ; CODE_028F8B
        bne.s   .cull
        moveq   #3,d3
        and.b   _ram+wm_FrameA(a4),d3
        beq.s   .y
        lea     _ram+wm_MExSprXSpeed(a4),a0
        move.b  (a0,d1.w),d0
        lea     _ram+wm_MExSprXLo(a4),a1
        lea     _ram+wm_MExSprXHi(a4),a2
        bsr     mx_add
.y:     lea     _ram+wm_MExSprYSpeed(a4),a0
        move.b  (a0,d1.w),d0
        lea     _ram+wm_MExSprYLo(a4),a1
        lea     _ram+wm_MExSprYHi(a4),a2
        bsr     mx_add
        tst.b   d3
        bne.s   .cull
        lea     _ram+wm_MExSprYSpeed(a4),a0
        addq.b  #1,(a0,d1.w)
.cull:  lea     _ram+wm_MExSprYLo(a4),a1
        lea     _ram+wm_MExSprYHi(a4),a2
        bsr     mx_get
        move.b  _ram+wm_Bg1VOfs+1(a4),d0
        lsl.w   #8,d0
        move.b  _ram+wm_Bg1VOfs(a4),d0
        sub.w   d0,d2                       ; y - Bg1VOfs
        move.b  d2,d3
        lsr.w   #8,d2
        beq.s   .cx
        tst.b   d2
        bmi.s   .nx                         ; por encima: sigue vivo
        bra.s   .kill
.cx:    lea     _ram+wm_MExSprXLo(a4),a1
        lea     _ram+wm_MExSprXHi(a4),a2
        bsr     mx_get
        move.b  _ram+wm_Bg1HOfs+1(a4),d0
        lsl.w   #8,d0
        move.b  _ram+wm_Bg1HOfs(a4),d0
        sub.w   d0,d2
        lsr.w   #8,d2
        bne.s   .kill
        cmp.b   #$f0,d3
        bhs.s   .kill
        bra.s   .nx
.kill:  lea     _ram+wm_MExSprNum(a4),a0    ; CODE_028F87
        clr.b   (a0,d1.w)
.nx:    dbf     d1,.lp
        movem.l (sp)+,d2-d3/a2
        rts

; d2.w = a2[x] << 8 | a1[x]   (x = d1.w)
mx_get: move.b  (a2,d1.w),d2
        lsl.w   #8,d2
        move.b  (a1,d1.w),d2
        rts
; a2:a1[x] += d0.b con signo
mx_add: ext.w   d0
        bsr     mx_get
        add.w   d0,d2
        move.b  d2,(a1,d1.w)
        lsr.w   #8,d2
        move.b  d2,(a2,d1.w)
        rts

; --- smoke_update ---
; entrada:  a4 = datos del C
; salida:   CODE_0296C0 sin el dibujo: las 4 ranuras de humo. 1 = nube,
;           2 = estrella de contacto, 3 = humo de derrape, 5 = destellos
;           (crean sprites menores del tipo 2); los demas no hacen nada
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
        public  _smoke_update
_smoke_update:
        lea     _ram+wm_SmokeSprite(a4),a0  ; lo normal: ninguno
        move.b  (a0)+,d0
        or.b    (a0)+,d0
        or.b    (a0)+,d0
        or.b    (a0),d0
        bne.s   .go
        rts
.go:    movem.l d2-d3,-(sp)
        moveq   #3,d1
.lp:    lea     _ram+wm_SmokeSprite(a4),a0
        move.b  (a0,d1.w),d2                ; d2 = n
        beq     .nx
        lea     _ram+wm_SmokeTimer(a4),a1
        move.b  (a1,d1.w),d3                ; d3 = t
        move.b  d2,d0
        and.b   #$7f,d0
        cmp.b   #1,d0
        beq.s   .s1
        cmp.b   #2,d0
        beq.s   .s2
        cmp.b   #3,d0
        beq.s   .s3
        cmp.b   #5,d0
        beq     .s5
        bra     .nx
.s1:    tst.b   d3                          ; CODE_0296E3
        beq     .kill
        tst.b   d2
        bmi.s   .d1
        tst.b   _ram+wm_SpritesLocked(a4)
        bne.s   .c1
.d1:    subq.b  #1,(a1,d1.w)
.c1:    lea     _ram+wm_SmokeXPos(a4),a0
        move.b  (a0,d1.w),d0
        sub.b   _ram+wm_Bg1HOfs(a4),d0
        cmp.b   #$f4,d0
        bhs     .kill
        lea     _ram+wm_SmokeYPos(a4),a0
        move.b  (a0,d1.w),d0
        sub.b   _ram+wm_Bg1VOfs(a4),d0
        cmp.b   #$e0,d0
        bhs     .kill
        bra     .nx
.s2:    tst.b   d3                          ; CODE_029797
        beq     .kill
        tst.b   _ram+wm_SpritesLocked(a4)
        bne.s   .c2
        subq.b  #1,(a1,d1.w)
.c2:    lea     _ram+wm_SmokeXPos(a4),a0
        move.b  (a0,d1.w),d0
        sub.b   _ram+wm_Bg1HOfs(a4),d0
        cmp.b   #$f0,d0
        bhs     .kill
        bra     .nx
.s3:    tst.b   d3                          ; CODE_029927
        beq     .kill
        tst.b   _ram+wm_SpritesLocked(a4)
        bne     .nx
        subq.b  #1,(a1,d1.w)
        moveq   #7,d0
        and.b   d3,d0
        bne     .nx
        lea     _ram+wm_SmokeYPos(a4),a0
        subq.b  #1,(a0,d1.w)
        bra     .nx
.s5:    tst.b   d3                          ; CODE_0298CA
        beq.s   .kill
        tst.b   _ram+wm_SpritesLocked(a4)
        bne.s   .nx
        subq.b  #1,(a1,d1.w)
        moveq   #3,d0
        and.b   d3,d0
        bne.s   .nx
        bsr     _mex_slot                   ; d0.w = y (d1-d3 intactos)
        lea     _ram+wm_MExSprNum(a4),a0
        move.b  #$02,(a0,d0.w)
        subq.b  #1,d3
        lsr.b   #2,d3
        and.w   #3,d3
        lea     sm_dx(pc),a0
        move.b  (a0,d3.w),d2
        lea     _ram+wm_SmokeXPos(a4),a1
        add.b   (a1,d1.w),d2
        lea     _ram+wm_MExSprXLo(a4),a0
        move.b  d2,(a0,d0.w)
        lea     sm_dy(pc),a0
        move.b  (a0,d3.w),d2
        lea     _ram+wm_SmokeYPos(a4),a1
        add.b   (a1,d1.w),d2
        lea     _ram+wm_MExSprYLo(a4),a0
        move.b  d2,(a0,d0.w)
        lea     _ram+wm_MExSprTimer(a4),a0
        move.b  #$17,(a0,d0.w)
        bra.s   .nx
.kill:  lea     _ram+wm_SmokeSprite(a4),a0  ; CODE_0296DF / CODE_029793
        clr.b   (a0,d1.w)
.nx:    dbf     d1,.lp
        movem.l (sp)+,d2-d3
        rts

; --- contact_gfx ---
; entrada:  pila vbcc = u8 x; a4 = datos del C
; salida:   DisplayContactGfx: la estrellita (humo 2) a los pies de Mario si
;           el sprite x esta en pantalla; sin ranura libre pisa la 0
; registros destruidos: d0-d1/a0
; ciclos:   tools/l_funcs.py
        public  _contact_gfx
_contact_gfx:
        moveq   #0,d1
        move.b  7(sp),d1
        lea     _ram+wm_OffscreenHorz(a4),a0
        move.b  (a0,d1.w),d0
        lea     _ram+wm_OffscreenVert(a4),a0
        or.b    (a0,d1.w),d0
        bne.s   .r
        lea     _ram+wm_SmokeSprite(a4),a0
        moveq   #3,d1
.l:     tst.b   (a0,d1.w)
        beq.s   .f
        dbf     d1,.l
        moveq   #0,d1
.f:     move.b  #$02,(a0,d1.w)
        lea     _ram+wm_SmokeXPos(a4),a0
        move.b  _ram+wm_MarioXPos(a4),(a0,d1.w)
        moveq   #$14,d0
        tst.b   _ram+wm_OnYoshi(a4)
        beq.s   .y
        moveq   #$1e,d0
.y:     add.b   _ram+wm_MarioYPos(a4),d0
        lea     _ram+wm_SmokeYPos(a4),a0
        move.b  d0,(a0,d1.w)
        lea     _ram+wm_SmokeTimer(a4),a0
        move.b  #$08,(a0,d1.w)
.r:     rts

;----------------------------------------------------------------------
; G5L-R-L2: GetDrawInfoBnk1 (msprite.c) y las rutinas de graficos de
; player/spr_gfx.c (salvo chuck_gfx y shell_gfx, que siguen en C). Al
; principio del fichero: el C de msprite.c / spr_*.c que las llama queda
; a menos de 32 KB (P102). Las internas (sg_*) reciben d2.w = x (alto en
; 0) y a3 = ram + x; lo global de ram[] va por a4.
;----------------------------------------------------------------------

; --- get_draw_info1 ---
; entrada:  pila vbcc = u8 x; a4 = datos del C
; salida:   d0.l = 1 cerca / 0 lejos (get_draw_info1 de msprite.c)
; registros destruidos: d0-d1/a1
; ciclos:   tools/l_funcs.py
        public  _get_draw_info1
_get_draw_info1:
        moveq   #0,d0
        move.b  7(sp),d0
        lea     _ram(a4),a1
        add.w   d0,a1
        ; sigue en sg_di1

; --- sg_di1 ---
; entrada:  a1 = ram + x; a4 = datos del C
; salida:   d0.l = 1 cerca / 0 lejos, con Z; OffscreenHorz/Vert y SpriteOffTbl
; registros destruidos: d0-d1
; ciclos:   tools/l_funcs.py
sg_di1:
        move.b  wm_SpriteXHi(a1),d0
        lsl.w   #8,d0
        move.b  wm_SpriteXLo(a1),d0
        move.w  _ram+wm_Bg1HOfs(a4),d1
        ror.w   #8,d1
        sub.w   d1,d0                       ; d = sx - camara X
        move.w  d0,d1
        lsr.w   #8,d1
        sne     d1
        neg.b   d1
        move.b  d1,wm_OffscreenHorz(a1)
        add.w   #$40,d0
        cmp.w   #$180,d0
        bhs.s   .far
        clr.b   wm_SpriteOffTbl(a1)
        move.b  wm_SpriteYHi(a1),d0
        lsl.w   #8,d0
        move.b  wm_SpriteYLo(a1),d0
        move.w  _ram+wm_Bg1VOfs(a4),d1
        ror.w   #8,d1
        sub.w   d1,d0                       ; d = sy - camara Y
        moveq   #0,d1                       ; v
        cmp.b   #$09,wm_SpriteStatus(a1)
        beq.s   .v1
        btst    #5,wm_Tweaker190F(a1)
        beq.s   .v1
        add.w   #$20,d0
        cmp.w   #$100,d0
        blo.s   .v0
        moveq   #2,d1
.v0:    sub.w   #$10,d0                     ; d + $10
        bra.s   .v2
.v1:    add.w   #$10,d0
.v2:    cmp.w   #$100,d0
        blo.s   .w
        addq.b  #1,d1
.w:     move.b  d1,wm_OffscreenVert(a1)
        moveq   #1,d0
        rts
.far:   clr.b   wm_OffscreenVert(a1)
        move.b  #1,wm_SpriteOffTbl(a1)
        moveq   #0,d0
        rts

; --- sub_offscreen3 ---
; entrada:  pila vbcc = u8 x; a4 = datos del C
; salida:   como sub_offscreen3 de msprite.c (SubOffscreen0Bnk3, nivel horizontal)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
        public  _sub_offscreen3
_sub_offscreen3:
        moveq   #0,d1
        move.b  7(sp),d1
        lea     _ram(a4),a1
        add.w   d1,a1                       ; a1 = ram + x
        move.b  wm_OffscreenHorz(a1),d0
        or.b    wm_OffscreenVert(a1),d0
        beq.s   .ret
        move.b  wm_SpriteYHi(a1),d0
        lsl.w   #8,d0
        move.b  wm_SpriteYLo(a1),d0
        add.w   #$50,d0                     ; sy + $50, 16 bits
        cmp.w   #$200,d0
        blo.s   .x
        tst.w   d0                          ; y el bit 15 en 0: muy abajo
        bpl.s   .erase
.x:     btst    #2,wm_Tweaker167A(a1)
        bne.s   .ret
        moveq   #1,d1
        and.b   _ram+wm_FrameA(a4),d1       ; y
        lea     tx_03B83F(pc),a0
        move.b  8(a0,d1.w),d0               ; DATA_03B847 (va detras)
        lsl.w   #8,d0
        move.b  (a0,d1.w),d0
        move.w  _ram+wm_Bg1HOfs(a4),d1
        ror.w   #8,d1
        add.w   d1,d0                       ; lim
        move.b  wm_SpriteXHi(a1),d1
        lsl.w   #8,d1
        move.b  wm_SpriteXLo(a1),d1
        sub.w   d1,d0                       ; m0 = alto de (lim - sx)
        btst    #0,_ram+wm_FrameA(a4)
        beq.s   .n
        eor.w   #$8000,d0
.n:     tst.w   d0
        bpl.s   .ret
.erase: cmp.b   #$08,wm_SpriteStatus(a1)
        blo.s   .z
        moveq   #0,d0
        move.b  wm_SprIndexInLvl(a1),d0
        cmp.b   #$ff,d0
        beq.s   .z
        lea     _ram+wm_SprLoadStatus(a4),a0
        clr.b   (a0,d0.w)
.z:     clr.b   wm_SpriteStatus(a1)
.ret:   rts

; --- mario_spr_interact ---
; entrada:  pila vbcc = u8 x; a4 = datos del C
; salida:   d0.l como mario_spr_interact de msprite.c (MarioSprInteractRt):
;           1 = contacto y lo resuelve el sprite (Tweaker167A bit 7)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
; El contacto sin reaccion propia (DefaultInteractR) es default_interact (C).
        public  _mario_spr_interact
_mario_spr_interact:
        moveq   #0,d1
        move.b  7(sp),d1
        lea     _ram(a4),a1
        add.w   d1,a1                       ; a1 = ram + x
        btst    #5,wm_Tweaker167A(a1)
        bne.s   .go
        move.b  _ram+wm_FrameA(a4),d0       ; un frame si y otro no
        eor.b   d1,d0
        and.b   #1,d0
        or.b    wm_OffscreenHorz(a1),d0
        bne.s   .no
.go:    move.l  d1,-(sp)
        bsr.s   _process_interact
        addq.l  #4,sp
        tst.l   d0
        beq.s   .ret                        ; d0 = 0
        moveq   #0,d1
        move.b  7(sp),d1
        lea     _ram(a4),a1
        add.w   d1,a1
        tst.b   wm_Tweaker167A(a1)
        bmi.s   .yes
        move.l  d1,-(sp)
        PICCALL _default_interact
        addq.l  #4,sp
.no:    moveq   #0,d0
.ret:   rts
.yes:   moveq   #1,d0
        rts

; --- process_interact ---
; entrada:  pila vbcc = u8 x; a4 = datos del C
; salida:   d0.l = 1 si Mario y el sprite se tocan (ProcessInteract); m14, m15
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
; Termina saltando a spr_mario_contact_asm con el mismo argumento en la pila.
        public  _process_interact
_process_interact:
        moveq   #0,d1
        move.b  7(sp),d1
        lea     _ram(a4),a1
        add.w   d1,a1                       ; a1 = ram + x
        move.b  _ram+wm_PlayerXPosLv(a4),d0 ; SubHorizPos: m15 = bajo de (Mario - sx)
        sub.b   wm_SpriteXLo(a1),d0
        move.b  d0,_ram+m15(a4)
        add.b   #$50,d0
        cmp.b   #$a0,d0
        bhs.s   .no
        move.b  _ram+wm_PlayerYPosLv(a4),d0 ; CODE_01AD42: m14
        sub.b   wm_SpriteYLo(a1),d0
        move.b  d0,_ram+m14(a4)
        add.b   #$60,d0
        cmp.b   #$c0,d0
        bhs.s   .no
        tst.b   _ram+wm_MarioAnimation(a4)
        bne.s   .no
        btst    #6,_ram+wm_LevelMode(a4)
        bne     _spr_mario_contact_asm
        move.b  _ram+wm_IsBehindScenery(a4),d0
        cmp.b   wm_SprBehindScrn(a1),d0
        beq     _spr_mario_contact_asm
.no:    moveq   #0,d0
        rts

        ifd     SPR_OAM
; --- spr_oam_index ---
; entrada:  pila vbcc = u8 x; a4 = datos del C
; salida:   d0.l = indice OAM de la ranura (CODE_0180D2), tambien en SprOAMIndex
; registros destruidos: d0-d1/a0
; ciclos:   tools/l_funcs.py
        public  _spr_oam_index
_spr_oam_index:
        moveq   #0,d1
        move.b  7(sp),d1
        ; sigue en sg_index

; --- sg_index ---
; entrada:  d1.w = x; a4 = datos del C
; salida:   d0.l = indice OAM (alto en 0), escrito en SprOAMIndex
; registros destruidos: d0/a0
; ciclos:   tools/l_funcs.py
sg_index:
        moveq   #0,d0
        move.b  _ram+wm_SpriteMemory(a4),d0
        lea     tg2_07F0B4(pc),a0
        move.b  (a0,d0.w),d0
        add.b   d1,d0                       ; i = x + DATA_07F0B4[mem], 8 bits
        lea     tg2_07F000(pc),a0           ; DATA_07F0B4 va detras (i >= 180)
        move.b  (a0,d0.w),d0
        lea     _ram+wm_SprOAMIndex(a4),a0
        move.b  d0,(a0,d1.w)
        rts

; --- sg_g2z ---
; entrada:  d2.w = x; a3 = ram + x; a4 = datos del C
; salida:   d0.l = 1 / 0 como sub_spr_gfx2(x, 0)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
sg_g2z:
        move.w  d2,d1
        bsr.s   sg_index
        moveq   #0,d0
        ; sigue en sg_g2at

; --- sg_g2at ---
; entrada:  d0.b = m4 (atributos extra); d2.w = x; a3 = ram + x; a4 = datos del C
; salida:   d0.l = 1 / 0 (lejos) como sub_spr_gfx2_at de spr_gfx.c
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
sg_g2at:
        move.b  d0,_ram+m4(a4)
        move.l  a3,a1
        bsr     sg_di1
        move.b  wm_SpriteXLo(a3),d1
        sub.b   _ram+wm_Bg1HOfs(a4),d1
        move.b  d1,_ram+m0(a4)
        move.b  wm_SpriteYLo(a3),d1
        sub.b   _ram+wm_Bg1VOfs(a4),d1
        move.b  d1,_ram+m1(a4)
        tst.b   d0
        beq     .ret                        ; lejos: d0 = 0
        move.b  wm_SpriteDir(a3),_ram+m2(a4)
        moveq   #0,d0
        move.b  wm_SpriteNum(a3),d0
        cmp.b   #tg2_SprTilemapOffset_len,d0
        bhs.s   .t0
        lea     tg2_SprTilemapOffset(pc),a0
        move.b  (a0,d0.w),d0
        add.b   wm_SpriteGfxTbl(a3),d0      ; k, 8 bits
        cmp.b   #tg2_SprTilemap_len,d0
        bhs.s   .t0
        lea     tg2_SprTilemap(pc),a0
        move.b  (a0,d0.w),d0
        bra.s   .t
.t0:    moveq   #0,d0
.t:     moveq   #0,d1
        move.b  wm_SprOAMIndex(a3),d1       ; y
        lea     _ram+wm_OamSlot(a4),a0
        add.w   d1,a0                       ; la ficha (sin wrap, como el C)
        move.b  d0,2(a0)                    ; tile
        move.b  _ram+m0(a4),(a0)
        move.b  _ram+m1(a4),1(a0)
        move.b  wm_SpritePal(a3),d0
        btst    #0,wm_SpriteDir(a3)
        bne.s   .nf
        eor.b   #$40,d0
.nf:    or.b    _ram+m4(a4),d0
        or.b    _ram+wm_SpriteProp(a4),d0
        move.b  d0,3(a0)
        lsr.w   #2,d1                       ; i = y / 4
        lea     _ram+wm_OamSize(a4),a1
        add.w   d1,a1
        moveq   #2,d0
        or.b    wm_OffscreenHorz(a3),d0
        move.b  d0,(a1)
        move.b  wm_OffscreenVert(a3),d0     ; CODE_01A3DF (oam_offscreen_vert)
        beq.s   .mk
        lea     _ram+wm_OamSlot(a4),a0
        add.w   d1,d1
        add.w   d1,d1
        add.w   d1,a0                       ; (u8)(i << 2) = y & $FC
        btst    #0,d0
        beq.s   .b1
        move.b  #$01,(a1)
        move.b  #$80,(a0)
.b1:    btst    #1,d0
        beq.s   .mk
        move.b  #$01,1(a1)
        move.b  #$80,4(a0)                  ; (u8)(i << 2) + 4, sin wrap
.mk:    cmp.w   #12,d2                      ; oam_mark(x, y, 1)
        bhs.s   .one
        lea     _spr_oam_first(a4),a0
        move.b  wm_SprOAMIndex(a3),(a0,d2.w)
        lea     _spr_oam_n(a4),a0
        move.b  #1,(a0,d2.w)
.one:   moveq   #1,d0
.ret:   rts

; --- sub_spr_gfx2 ---
; entrada:  pila vbcc = u8 x, u8 m4v; a4 = datos del C
; salida:   d0.l = 1 / 0 como sub_spr_gfx2 de spr_gfx.c
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
        public  _sub_spr_gfx2
_sub_spr_gfx2:
        movem.l d2/a3,-(sp)
        moveq   #0,d2
        move.b  8+7(sp),d2
        lea     _ram(a4),a3
        add.w   d2,a3
        move.w  d2,d1
        bsr     sg_index
        move.b  8+11(sp),d0
        bsr     sg_g2at
        movem.l (sp)+,d2/a3
        rts

; --- spr_gfx2_tile ---
; entrada:  pila vbcc = u8 x, u8 t; a4 = datos del C
; salida:   como spr_gfx2_tile de spr_gfx.c (SubSprGfx2Entry1 + tile fijo)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
        public  _spr_gfx2_tile
_spr_gfx2_tile:
        movem.l d2/a3,-(sp)
        moveq   #0,d2
        move.b  8+7(sp),d2
        lea     _ram(a4),a3
        add.w   d2,a3
        bsr     sg_g2z
        moveq   #0,d0
        move.b  wm_SprOAMIndex(a3),d0
        lea     _ram+wm_OamSlot+2(a4),a0
        move.b  8+11(sp),(a0,d0.w)
        movem.l (sp)+,d2/a3
        rts

; --- spin_jump_gfx ---
; entrada:  pila vbcc = u8 x; a4 = datos del C
; salida:   como spin_jump_gfx de spr_gfx.c (la nube del salto con giro)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
        public  _spin_jump_gfx
_spin_jump_gfx:
        movem.l d2/a3,-(sp)
        moveq   #0,d2
        move.b  8+7(sp),d2
        lea     _ram(a4),a3
        add.w   d2,a3
        bsr     sg_g2z
        moveq   #0,d1
        move.b  wm_SprOAMIndex(a3),d1
        lea     _ram+wm_OamSlot(a4),a0
        add.w   d1,a0
        move.b  wm_SpriteDecTbl1(a3),d0
        lsr.b   #3,d0
        and.w   #3,d0
        lea     tg2_SpinSmoke(pc),a1
        move.b  (a1,d0.w),d0
        move.b  d0,2(a0)
        and.b   #$30,d0
        move.b  d0,3(a0)
        movem.l (sp)+,d2/a3
        rts

; --- spr013_gfx ---
; entrada:  pila vbcc = u8 x; a4 = datos del C
; salida:   como spr013_gfx de spr_gfx.c (_Spr0to13Gfx de una ficha)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
        public  _spr013_gfx
_spr013_gfx:
        movem.l d2-d3/a3,-(sp)
        moveq   #0,d2
        move.b  12+7(sp),d2
        lea     _ram(a4),a3
        add.w   d2,a3
        move.b  wm_SpriteDir(a3),d3         ; d
        move.b  wm_SpriteDecTbl5(a3),d0
        beq.s   .g
        move.b  #2,wm_SpriteGfxTbl(a3)
        cmp.b   #5,d0
        blo.s   .g
        eor.b   #1,wm_SpriteDir(a3)
.g:     bsr     sg_g2z
        move.b  d3,wm_SpriteDir(a3)
        movem.l (sp)+,d2-d3/a3
        rts

; --- banzai_gfx ---
; entrada:  pila vbcc = u8 x; a4 = datos del C
; salida:   como banzai_gfx de spr_gfx.c (CODE_02D5E4, 16 fichas)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
; Las cuatro tablas de 16 van seguidas en smwtabx.i (comprobado abajo).
        public  _banzai_gfx
_banzai_gfx:
        movem.l d2-d5/a3,-(sp)
        moveq   #0,d2
        move.b  20+7(sp),d2
        lea     _ram(a4),a3
        add.w   d2,a3
        move.w  d2,d1
        bsr     sg_index
        move.l  d2,-(sp)
        bsr     _get_draw_info_asm
        addq.l  #4,sp
        tst.l   d0
        beq.s   .ret
        moveq   #0,d1
        move.b  wm_SprOAMIndex(a3),d1       ; y
        move.b  wm_SpriteXLo(a3),d3
        sub.b   _ram+wm_Bg1HOfs(a4),d3
        move.b  d3,_ram+m0(a4)
        move.b  wm_SpriteYLo(a3),d4
        sub.b   _ram+wm_Bg1VOfs(a4),d4
        move.b  d4,_ram+m1(a4)
        lea     _ram+wm_OamSlot(a4),a1
        lea     tg2_DATA_02D5A4(pc),a0
        moveq   #15,d0                      ; i = 15..0
.lp:    move.b  (a0,d0.w),d5
        add.b   d3,d5
        move.b  d5,(a1,d1.w)
        move.b  16(a0,d0.w),d5              ; DATA_02D5B4
        add.b   d4,d5
        move.b  d5,1(a1,d1.w)
        move.b  32(a0,d0.w),2(a1,d1.w)      ; BanzaiBillTiles
        move.b  48(a0,d0.w),3(a1,d1.w)      ; DATA_02D5D4
        addq.b  #4,d1                       ; wrap de 8 bits
        dbf     d0,.lp
        pea     2.w
        pea     15.w
        move.l  d2,-(sp)
        bsr     _finish_oam_write_asm
        lea     12(sp),sp
.ret:   movem.l (sp)+,d2-d5/a3
        rts

; --- sg_g0 ---
; entrada:  d0.b = flip; d2.w = x; a3 = ram + x; a4 = datos del C
; salida:   como sub_spr_gfx0 de spr_gfx.c (cuatro fichas de 8x8)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
SG0T    macro                               ; \1 = i
        move.b  tg2_GeneralSprDispX+\1(pc),d0
        add.b   d3,d0
        move.b  d0,(a1,d1.w)
        move.b  tg2_GeneralSprDispY+\1(pc),d0
        add.b   d4,d0
        move.b  d0,1(a1,d1.w)
        moveq   #\1,d0
        add.b   d5,d0                       ; (u8)(m2 + i)
        move.b  (a0,d0.w),2(a1,d1.w)
        moveq   #\1,d0
        add.b   d6,d0                       ; (u8)((flip << 2) + i)
        move.b  (a2,d0.w),d0
        or.b    d7,d0
        move.b  d0,3(a1,d1.w)
        addq.b  #4,d1
        endm
sg_g0:
        movem.l d3-d7/a2,-(sp)
        moveq   #0,d6
        move.b  d0,d6
        move.b  d0,_ram+m5(a4)
        clr.b   _ram+m15(a4)
        move.l  a3,a1
        bsr     sg_di1
        beq     .ret
        move.b  wm_SpriteXLo(a3),d3
        sub.b   _ram+wm_Bg1HOfs(a4),d3
        move.b  d3,_ram+m0(a4)
        move.b  wm_SpriteYLo(a3),d4
        sub.b   _ram+wm_Bg1VOfs(a4),d4
        move.b  d4,_ram+m1(a4)
        moveq   #0,d0
        move.b  wm_SpriteNum(a3),d0
        lea     tg2_SprTilemapOffset(pc),a0
        move.b  (a0,d0.w),d5
        move.b  wm_SpriteGfxTbl(a3),d0
        add.b   d0,d0
        add.b   d0,d0
        add.b   d0,d5                       ; m2, 8 bits
        move.b  d5,_ram+m2(a4)
        move.b  wm_SpritePal(a3),d7
        or.b    _ram+wm_SpriteProp(a4),d7
        move.b  d7,_ram+m3(a4)
        add.b   d6,d6
        add.b   d6,d6                       ; (u8)(flip << 2)
        moveq   #0,d1
        move.b  wm_SprOAMIndex(a3),d1       ; y
        lea     _ram+wm_OamSlot(a4),a1
        lea     tg2_SprTilemap(pc),a0
        lea     tg2_GeneralSprGfxProp(pc),a2
        SG0T    3
        SG0T    2
        SG0T    1
        SG0T    0
        st      _ram+m4(a4)                 ; m4 = $FF (la ultima vuelta)
        pea     0.w
        pea     3.w
        moveq   #0,d0
        move.w  d2,d0
        move.l  d0,-(sp)
        bsr     _finish_oam_write_asm
        lea     12(sp),sp
.ret:   movem.l (sp)+,d3-d7/a2
        rts

; --- piranha_gfx ---
; entrada:  pila vbcc = u8 x; a4 = datos del C
; salida:   como piranha_gfx de spr_gfx.c (CODE_02E0CD: cabeza y tallo)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
; d3 = Y del sprite, d4 = primer indice OAM, d5 = SpriteProp, d6 =
; spr_oam_n[x] despues de la cabeza (puede venir de un frame anterior).
        public  _piranha_gfx
_piranha_gfx:
        movem.l d2-d6/a3,-(sp)
        moveq   #0,d2
        move.b  24+7(sp),d2
        lea     _ram(a4),a3
        add.w   d2,a3
        move.w  d2,d1
        bsr     sg_index
        move.b  d0,d4                       ; first
        move.b  _ram+wm_SpriteProp(a4),d5
        move.b  wm_SpriteYHi(a3),d3
        lsl.w   #8,d3
        move.b  wm_SpriteYLo(a3),d3         ; sy
        move.b  #$10,_ram+wm_SpriteProp(a4)
        moveq   #8,d0
        and.b   wm_SpriteMiscTbl6(a3),d0
        lsr.b   #2,d0
        eor.b   #2,d0
        move.b  d0,wm_SpriteGfxTbl(a3)
        moveq   #0,d0
        bsr     sg_g2at                     ; la cabeza
        lea     _spr_oam_n(a4),a0
        move.b  (a0,d2.w),d6                ; n
        move.b  d4,d0
        addq.b  #4,d0
        move.b  d0,wm_SprOAMIndex(a3)
        moveq   #4,d0
        and.b   wm_SpriteMiscTbl3(a3),d0
        lsr.b   #2,d0
        addq.b  #1,d0
        move.b  d0,wm_SpriteGfxTbl(a3)
        move.w  d3,d0
        addq.w  #8,d0
        move.b  d0,wm_SpriteYLo(a3)
        lsr.w   #8,d0
        move.b  d0,wm_SpriteYHi(a3)
        move.b  #$0a,wm_SpritePal(a3)
        moveq   #1,d0
        bsr     sg_g0                       ; el tallo
        lea     _spr_oam_n(a4),a0
        moveq   #5,d1
        cmp.b   #4,(a0,d2.w)
        beq.s   .mk
        moveq   #1,d1
        tst.b   d6
        beq.s   .y
.mk:    cmp.w   #12,d2                      ; oam_mark(x, first, d1)
        bhs.s   .y
        lea     _spr_oam_first(a4),a1
        move.b  d4,(a1,d2.w)
        move.b  d1,(a0,d2.w)
.y:     move.b  d3,wm_SpriteYLo(a3)
        move.w  d3,d0
        lsr.w   #8,d0
        move.b  d0,wm_SpriteYHi(a3)
        move.b  d5,_ram+wm_SpriteProp(a4)
        movem.l (sp)+,d2-d6/a3
        rts

; --- goal_gfx ---
; entrada:  pila vbcc = u8 x; a4 = datos del C
; salida:   como goal_gfx de spr_gfx.c (CODE_01C12D: la cinta, tres fichas)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
        public  _goal_gfx
_goal_gfx:
        movem.l d2-d5/a3,-(sp)
        moveq   #0,d2
        move.b  20+7(sp),d2
        lea     _ram(a4),a3
        add.w   d2,a3
        move.w  d2,d1
        bsr     sg_index
        move.l  a3,a1
        bsr     sg_di1
        beq.s   .ret
        moveq   #0,d1
        move.b  wm_SprOAMIndex(a3),d1       ; y
        move.b  wm_SpriteXLo(a3),d3
        sub.b   _ram+wm_Bg1HOfs(a4),d3
        move.b  d3,_ram+m0(a4)
        move.b  wm_SpriteYLo(a3),d4
        sub.b   _ram+wm_Bg1VOfs(a4),d4
        move.b  d4,_ram+m1(a4)
        subq.b  #8,d3                       ; m0 - 8 + 8 i
        addq.b  #8,d4                       ; m1 + 8
        lea     _ram+wm_OamSlot(a4),a1
        moveq   #-$2c,d0                    ; tile $D4
        moveq   #2,d5
.lp:    move.b  d3,(a1,d1.w)
        move.b  d4,1(a1,d1.w)
        move.b  d0,2(a1,d1.w)
        move.b  #$32,3(a1,d1.w)
        addq.b  #4,d1
        addq.b  #8,d3
        moveq   #-$2b,d0                    ; despues $D5
        dbf     d5,.lp
        pea     0.w
        pea     2.w
        move.l  d2,-(sp)
        bsr     _finish_oam_write_asm
        lea     12(sp),sp
.ret:   movem.l (sp)+,d2-d5/a3
        rts

        include "player/swq68k.s"
        endc
; tablas tg2_ / tx_ de smwtabx.h (GENERADO por logicbench_build.sh, no versionado: R9)
        include "work/cc/smwtabx.i"
        if      (tg2_07F0B4-tg2_07F000)<>180
        fail    "smwtabx.i: DATA_07F0B4 tiene que ir detras de DATA_07F000"
        endif
        if      (tg2_DATA_02D5D4-tg2_DATA_02D5A4)<>48
        fail    "smwtabx.i: las tablas de Banzai tienen que ir seguidas"
        endif
        if      (tx_03B847-tx_03B83F)<>8
        fail    "smwtabx.i: DATA_03B847 tiene que ir detras de DATA_03B83F"
        endif
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
; zona muerta. f7f4 (scroll vertical) y f8ab (L/R) tambien son asm. Nivel
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
        bsr     _f8ab
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
.vert:  PICJUMP _camera_F6DB_c              ; P102: con SW-S queda lejos

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
; --- finish_oam_write_asm ---
; entrada: pila vbcc = u8 x, u8 fichas-1, u8 tamano; a4 = datos del C
; salida: OAM y m0-m11 identicos a FinishOAMWriteRt (sprite_1-1.s).
; registros destruidos: d0-d1/a0-a1
; ciclos: tools/l_funcs.py (G5L-R-L2: ~140 por ficha, antes ~250)
; Por ficha solo se compara: d2 = bx - hofs y d3 = by - (vofs - 16) se
; calculan una vez, y (u16)(bx + dx - hofs) >= $100 es lo mismo que el C.
; El contador (m8) y el tamano (m11) van en registros; m4:m5 y m9:m10 (la
; ultima ficha) se rearman despues del bucle con el dx/dy guardado.
;----------------------------------------------------------------------
FOWT    macro                               ; \1 = 1: tamano fijo (m11 >= 0)
.t\@:   move.w  d1,d0
        lsr.w   #2,d0
        lea     (a0,d0.w),a5                ; OamSize + y / 4
        ifne    \1
        move.b  d7,(a5)
        else
        and.b   #2,(a5)
        endif
        move.b  (a3,d1.w),d0
        sub.b   d4,d0
        ext.w   d0
        move.w  d0,a2                       ; dx de la ultima ficha
        add.w   d2,d0
        cmp.w   #$100,d0
        blo.s   .y\@
        or.b    #1,(a5)
.y\@:   move.b  1(a3,d1.w),d0
        sub.b   d5,d0
        ext.w   d0
        move.w  d0,a1                       ; dy de la ultima ficha
        add.w   d3,d0
        cmp.w   #$100,d0
        blo.s   .n\@
        move.b  #$f0,1(a3,d1.w)
.n\@:   addq.b  #4,d1                       ; wrap de 8 bits, alto en 0
        subq.b  #1,d6
        bpl.s   .t\@
        endm

        ifd     SPR_OAM
        public  _finish_oam_write_asm
_finish_oam_write_asm:
        movem.l d2-d7/a2-a3/a5,-(sp)
        moveq   #0,d0
        move.b  36+7(sp),d0                 ; x
        lea     _ram(a4),a1
        add.w   d0,a1                       ; ram + x
        moveq   #0,d1
        move.b  wm_SprOAMIndex(a1),d1       ; y
        move.b  36+11(sp),d6                ; contador (m8)
        move.b  36+15(sp),d7                ; tamano (m11)
        cmp.b   #12,d0                      ; oam_mark(x, y, fichas)
        bhs.s   .init
        lea     _spr_oam_first(a4),a0
        move.b  d1,(a0,d0.w)
        lea     _spr_oam_n(a4),a0
        move.b  d6,d2
        addq.b  #1,d2
        move.b  d2,(a0,d0.w)
.init:  move.b  d7,_ram+m11(a4)
        move.b  wm_SpriteXHi(a1),d2
        move.b  d2,_ram+m3(a4)
        lsl.w   #8,d2
        move.b  wm_SpriteXLo(a1),d2
        move.b  d2,_ram+m2(a4)              ; bx
        move.b  wm_SpriteYHi(a1),d3
        move.b  d3,_ram+m1(a4)
        lsl.w   #8,d3
        move.b  wm_SpriteYLo(a1),d3
        move.b  d3,_ram+m0(a4)              ; by
        move.b  d2,d4
        sub.b   _ram+wm_Bg1HOfs(a4),d4
        move.b  d4,_ram+m7(a4)              ; s7
        move.b  d3,d5
        sub.b   _ram+wm_Bg1VOfs(a4),d5
        move.b  d5,_ram+m6(a4)              ; s6
        move.w  _ram+wm_Bg1HOfs(a4),d0
        ror.w   #8,d0
        sub.w   d0,d2                       ; bx - hofs
        move.w  _ram+wm_Bg1VOfs(a4),d0
        ror.w   #8,d0
        sub.w   #16,d0
        sub.w   d0,d3                       ; by - (vofs - 16)
        lea     _ram+wm_OamSize(a4),a0
        lea     _ram+wm_OamSlot(a4),a3
        tst.b   d7
        bmi.s   .keep
        FOWT    1
        bra.s   .end
.keep:  FOWT    0
.end:   move.b  d6,_ram+m8(a4)              ; el contador al salir
        moveq   #0,d0
        move.b  36+7(sp),d0
        lea     _ram(a4),a3
        add.w   d0,a3                       ; ram + x
        move.b  wm_SpriteXHi(a3),d0
        lsl.w   #8,d0
        move.b  wm_SpriteXLo(a3),d0
        add.w   a2,d0                       ; lx de la ultima ficha
        move.b  d0,_ram+m4(a4)
        lsr.w   #8,d0
        move.b  d0,_ram+m5(a4)
        move.b  wm_SpriteYHi(a3),d0
        lsl.w   #8,d0
        move.b  wm_SpriteYLo(a3),d0
        add.w   a1,d0                       ; ly de la ultima ficha
        move.b  d0,_ram+m9(a4)
        lsr.w   #8,d0
        move.b  d0,_ram+m10(a4)
        movem.l (sp)+,d2-d7/a2-a3/a5
        rts
        endc

;----------------------------------------------------------------------
; --- rex_gfx ---
; entrada: pila vbcc = u8 x; a4 = datos del C
; salida: pose, OAM y temporales identicos a RexGfxRt (sprite_3-1.s).
; registros destruidos: d0-d1/a0-a1; conserva d2-d7/a2-a3.
; ciclos: se mide en work/loam_rexasm_oam_prof.txt (Musashi, sin DMA).
; Las dos vueltas se desenrollan en el orden 1,0 de la SNES. No cambia
; la fase de GetDrawInfo ni FinishOAMWrite ni el orden de las escrituras.
;----------------------------------------------------------------------
        ifd     SPR_OAM
REXOAM macro
        move.w  d4,d0
        ifne    \1
        or.b    #1,d0
        endif
        move.w  d0,d1                     ; idx = m3 | vuelta, 0..255
        tst.b   d5
        bne.s   .dir\@
        add.b   #$0c,d0                   ; wrap de 8 bits como ADC
.dir\@:lea     rex_disp_x(pc),a0
        move.b  (a0,d0.w),d0
        add.b   d6,d0
        move.b  d0,(a1,d3.w)              ; OAM X
        lea     rex_disp_y(pc),a0
        move.b  (a0,d1.w),d0
        add.b   d7,d0
        move.b  d0,1(a1,d3.w)             ; OAM Y
        lea     rex_tiles(pc),a0
        move.b  (a0,d1.w),d0
        move.b  d0,2(a1,d3.w)             ; tile
        lea     rex_prop(pc),a0
        move.b  (a0,d5.w),d0
        or.b    wm_SpriteProp(a2),d0
        move.b  d0,3(a1,d3.w)             ; atributos
        moveq   #0,d0
        cmp.b   #$0a,d4
        bhs.s   .size\@
        moveq   #2,d0
.size\@:move.w d3,d1
        lsr.w   #2,d1
        lea     wm_OamSize(a2),a0
        move.b  d0,(a0,d1.w)
        addq.b  #4,d3                     ; alto de d3 sigue cero
        endm

        public  _rex_gfx_asm
_rex_gfx_asm:
        movem.l d2-d7/a2-a3,-(sp)
        moveq   #0,d2
        move.b  32+7(sp),d2
        lea     _ram(a4),a2
        lea     (a2,d2.w),a3
        tst.b   wm_SpriteDecTbl3(a3)
        beq.s   .cape
        move.b  #5,wm_SpriteGfxTbl(a3)
.cape: tst.b   wm_DisSprCapeContact(a3)
        beq.s   .draw
        move.b  #2,wm_SpriteGfxTbl(a3)
.draw: move.l  d2,-(sp)
        PICCALL _get_draw_info_asm
        addq.l  #4,sp
        tst.l   d0
        beq     .ret
        move.l  d2,-(sp)
        PICCALL _spr_oam_index
        addq.l  #4,sp
        moveq   #0,d3
        move.b  d0,d3                     ; Y OAM
        move.b  wm_SpriteXLo(a3),d6
        sub.b   wm_Bg1HOfs(a2),d6
        move.b  wm_SpriteYLo(a3),d7
        sub.b   wm_Bg1VOfs(a2),d7
        moveq   #0,d4
        move.b  wm_SpriteGfxTbl(a3),d4
        lsl.b   #1,d4
        moveq   #0,d5
        move.b  wm_SpriteDir(a3),d5
        lea     wm_OamSlot(a2),a1
        REXOAM  1
        REXOAM  0
        move.b  d6,m0(a2)
        move.b  d7,m1(a2)
        move.b  d5,m2(a2)
        move.b  d4,m3(a2)
        move.l  #$ff,-(sp)
        move.l  #1,-(sp)
        move.l  d2,-(sp)
        bsr     _finish_oam_write_asm
        lea     12(sp),sp
.ret:  movem.l (sp)+,d2-d7/a2-a3
        rts
; RexTileDispX/Y, RexTiles y RexGfxProp del original sprite_3-1.s.
; vbcc elimina las const C que quedan sin usuarios al sustituir RexGfxRt.
rex_disp_x:
        dc.b    $fc,$00,$fc,$00,$fe,$00,$00,$00
        dc.b    $00,$00,$00,$08,$04,$00,$04,$00
        dc.b    $02,$00,$00,$00,$00,$00,$08,$00
rex_disp_y:
        dc.b    $f1,$00,$f0,$00,$f8,$00,$00,$00,$00,$00,$08,$08
rex_tiles:
        dc.b    $8a,$aa,$8a,$ac,$8a,$aa,$8c,$8c,$a8,$a8,$a2,$b2
rex_prop:
        dc.b    $47,$07
        even
        endc

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
.c:     PICJUMP _mario_E2BD_c               ; lejos con SW-S (P102)

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

;----------------------------------------------------------------------
; --- level_frame --- (G5L-R-L2: manim.c level_frame, CODE_00A295 sin la
; barra de estado; el C queda de referencia en el PC)
; entrada:  a4 = datos del C
; salida:   como level_frame() de manim.c (FrameA, ClearOam, camara,
;           graficos y frame de Mario, sprites, bloques, cargador)
; registros destruidos: d0-d1/a0-a1 (ABI de vbcc)
; ciclos:   tools/l_funcs.py (Musashi, sin DMA)
; sprites_begin va en linea; sprites_all en _sprites_all_asm. Las
; funciones en C lejanas van con PICCALL (P102).
;----------------------------------------------------------------------
        public  _level_frame
_level_frame:
        addq.b  #1,_ram+wm_FrameA(a4)
        ifd     SPR_OAM
        lea     _ram+$0201(a4),a0           ; wm_ClearOam: la Y de las 128
        moveq   #-16,d0                     ; $F0
lfo     set     0
        rept    128
        move.b  d0,lfo(a0)
lfo     set     lfo+4
        endr
        lea     _spr_oam_n(a4),a0
        moveq   #0,d0
lfo     set     0
        rept    12
        move.b  d0,lfo(a0)
lfo     set     lfo+1
        endr
        endc
        clr.l   _mario_unsupported(a4)      ; MARIO_OK
        bsr     _camera_F6DB
        tst.l   _mario_unsupported(a4)
        bne.s   .e2
        PICCALL _mario_E2BD
.e2:    move.b  _ram+wm_MarioXPos(a4),_ram+wm_PlayerXPosLv(a4)    ; CODE_00A2F3
        move.b  _ram+wm_MarioXPos+1(a4),_ram+wm_PlayerXPosLv+1(a4)
        move.b  _ram+wm_MarioYPos(a4),_ram+wm_PlayerYPosLv(a4)
        move.b  _ram+wm_MarioYPos+1(a4),_ram+wm_PlayerYPosLv+1(a4)
        tst.l   _mario_unsupported(a4)
        bne.s   .x
        PICCALL _mario_player
        tst.l   _mario_unsupported(a4)
        bne.s   .x
        move.b  _ram+wm_IsCarrying2(a4),_ram+wm_IsCarrying(a4)    ; sprites_begin
        clr.b   _ram+wm_IsCarrying2(a4)
        clr.b   _ram+wm_IsOnSolidSpr(a4)
        clr.b   _ram+wm_IsInLakituCloud(a4)
        move.b  _ram+wm_YoshiSlot(a4),_ram+wm_LooseYoshiFlag(a4)
        clr.b   _ram+wm_YoshiSlot(a4)
        tst.b   _level_sprites(a4)
        beq.s   .b
        bsr     _sprites_all_asm
        PICCALL _give_lives_tick            ; CODE_028AB1 (SW-S)
.b:     PICCALL _mex_update                 ; CODE_028B67 (SW-S)
        bsr     _blocks_update
        PICCALL _smoke_update               ; CODE_0296C0 (en CODE_02902D, SW-S)
        tst.b   _level_sprites(a4)
        beq.s   .x
        PICCALL _score_update               ; ScoreSprGfx (SW-S)
        bsr     _sprite_load_level
.x:     rts

;----------------------------------------------------------------------
; --- sprites_all_asm --- (manim.c sprites_all, CODE_01808C: las ranuras
; 11..0 sin sprites_begin)
; entrada:  a4 = datos del C
; salida:   como sprites_all()
; registros destruidos: d0-d1/a0-a1
; se conservan d2/a2-a3
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
        public  _sprites_all_asm
_sprites_all_asm:
        movem.l d2/a2-a3,-(sp)
        PICCALL _logic68k_init              ; punteros de logic68k.s
        lea     _ram+wm_SpriteStatus(a4),a2
        lea     _ram+wm_SprIndexInLvl(a4),a3
        moveq   #11,d2
.l:     tst.b   (a2,d2.w)
        beq.s   .e
        move.l  d2,-(sp)                    ; sprite_run(k): u8 en el byte +3
        bsr     _sprite_run
        addq.l  #4,sp
        clr.l   _mario_unsupported(a4)      ; un sprite sin portar no para el frame
        dbf     d2,.l
        bra.s   .x
.e:     move.b  d2,_ram+wm_SprProcessIndex(a4)  ; ranura vacia (EraseSprite)
        st      (a3,d2.w)
        dbf     d2,.l
.x:     movem.l (sp)+,d2/a2-a3
        rts

;----------------------------------------------------------------------
; --- mario_player --- (G5L-R-L2: manim.c mario_player, CODE_00C500 ...
; _00C58F). Con una animacion de $71 (casos raros, rutinas static del C)
; salta a mario_player_c, el C de siempre.
; entrada:  a4 = datos del C
; salida:   como mario_player()
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
MPDEC   macro                               ; DEC1(p + \1): baja si no es 0
        tst.b   \1(a0)
        beq.s   .d\@
        subq.b  #1,\1(a0)
.d\@:
        endm
MPDEC4  macro                               ; NZ32(p + \1) -> DEC4(p + \1)
        tst.l   \1(a0)
        beq.s   .g\@
        MPDEC   \1
        MPDEC   \1+1
        MPDEC   \1+2
        MPDEC   \1+3
.g\@:
        endm

        public  _mario_player
_mario_player:
        tst.b   _ram+wm_MarioAnimation(a4)
        beq.s   .n
        PICJUMP _mario_player_c             ; ExecutePtr != 0: el C
.n:     clr.l   _mario_unsupported(a4)
        clr.l   _mario_events(a4)
        tst.b   _ram+wm_SpritesLocked(a4)
        bne     .an
        addq.b  #1,_ram+wm_FrameB(a4)
        lea     _ram+wm_PlayerAnimTimer(a4),a0      ; $1496: par
        MPDEC4  0
        MPDEC4  4
        MPDEC4  8
        MPDEC4  12
        tst.w   16(a0)
        beq.s   .t16
        MPDEC   16
        MPDEC   17
.t16:   MPDEC   18                          ; $14A8
        moveq   #3,d0
        and.b   _ram+wm_FrameB(a4),d0
        bne.s   .an
        MPDEC   19                          ; $14A9
        MPDEC4  20                          ; $14AA-$14AD
        MPDEC   24                          ; $14AE
.an:    tst.b   _ram+wm_EndLevelTimer(a4)   ; CODE_00C915
        beq.s   .cc
        moveq   #MARIO_UNSUP_TILE,d0
        move.l  d0,_mario_unsupported(a4)
        rts
.cc:    bsr     cddd_asm                    ; CODE_00CCC3
        tst.b   _ram+wm_SpritesLocked(a4)
        bne     .tail
        clr.b   _ram+wm_CapeCanHurt(a4)
        clr.b   _ram+wm_OWCreditsPose(a4)
        tst.b   _ram+wm_LockMarioTimer(a4)
        beq.s   .lm
        subq.b  #1,_ram+wm_LockMarioTimer(a4)
        clr.b   _ram+wm_MarioSpeedX(a4)
        move.b  #$0f,_ram+wm_MarioFrame(a4)
        bra.s   .tail
.lm:    move.b  _ram+wm_LevelMode(a4),d0
        bpl.s   .col
        btst    #0,d0
        bne.s   .col
        moveq   #MARIO_UNSUP_LAYER,d0       ; capa 2 que mueve a Mario
        move.l  d0,_mario_unsupported(a4)
        rts
.col:   bsr     _mario_collide              ; CODE_00CD24 + _00CD39
        tst.l   _mario_unsupported(a4)
        bne.s   .r
        bsr     _mario_D5F2                 ; CODE_00CD82
        tst.l   _mario_unsupported(a4)
        bne.s   .r
        bsr     _mario_D062
        tst.l   _mario_unsupported(a4)
        bne.s   .r
        bsr     _mario_D7E4
        tst.l   _mario_unsupported(a4)
        bne.s   .r
        bsr     _mario_CEB1
        tst.b   _ram+wm_OnYoshi(a4)
        beq.s   .tail
        tst.l   _mario_unsupported(a4)      ; unsup_anim: solo si no habia
        bne.s   .r
        moveq   #MARIO_UNSUP_YOSHI,d0
        move.l  d0,_mario_unsupported(a4)
.r:     rts
.tail:  btst    #5,_ram+wm_JoyFrameA(a4)    ; SELECT: el item de reserva
        beq.s   .t2
        or.w    #1024,_mario_events+2(a4)   ; MEV_SPRITE (unsigned de 32 bits)
.t2:    clr.b   _ram+wm_NoteBlkBounceFlag(a4)   ; _00C58F
        rts

;----------------------------------------------------------------------
; --- cddd_asm --- (manim.c cddd, CODE_00CDDD: la camara con L/R)
; entrada:  a4 = datos del C
; salida:   como cddd()
; registros destruidos: d0-d1/a0
; se conservan d2-d3
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
cddd_asm:
        tst.b   _ram+wm_HorzScrollHead(a4)
        bne.s   .go
        rts
.go:    movem.l d2-d3,-(sp)
        moveq   #0,d2
        move.b  _ram+wm_LRScrollDir(a4),d2  ; y
        move.b  _ram+wm_LRScrollFlag(a4),d0
        move.b  d0,_ram+wm_SpritesLocked(a4)
        bne     .ce4c
        move.b  _ram+wm_LRMoveCamera(a4),d0
        beq.s   .f6
        clr.b   _ram+wm_LRScrollDir(a4)
        move.b  d0,d2                       ; _00CE48: TAY
        bra     .pp
.f6:    move.b  _ram+wm_JoyPadB(a4),d0      ; CODE_00CDF6
        and.b   #$cf,d0
        or.b    _ram+wm_JoyPadA(a4),d0
        bne     .pp
        moveq   #$30,d3
        and.b   _ram+wm_JoyPadB(a4),d3
        beq     .pp
        cmp.b   #$30,d3
        beq     .pp
        lsr.b   #3,d3                       ; x (2 o 4)
        addq.b  #1,_ram+wm_LRFrameTimer(a4)
        cmp.b   #$10,_ram+wm_LRFrameTimer(a4)
        blo     .ce4c
        lea     _rom00+(DATA_00F6CB-ROM00_BASE)(a4),a0
        move.b  1(a0,d3.w),d0
        lsl.w   #8,d0
        move.b  (a0,d3.w),d0                ; T16X(DATA_00F6CB, x)
        move.b  _ram+wm_PosToScrollScreen+1(a4),d1
        lsl.w   #8,d1
        move.b  _ram+wm_PosToScrollScreen(a4),d1
        cmp.w   d0,d1
        beq.s   .ce4c
        and.b   #$fe,_ram+wm_PosToScrollScreen(a4)
        addq.b  #1,_ram+wm_LRScrollFlag(a4)
        moveq   #0,d0
        cmp.b   #2,d3
        bne.s   .a0
        move.b  _ram+wm_LastScreenHorz(a4),d0
        subq.b  #1,d0
.a0:    tst.b   _ram+wm_Bg1HOfs(a4)         ; (a << 8) != R16(Bg1HOfs)
        bne.s   .snd
        cmp.b   _ram+wm_Bg1HOfs+1(a4),d0
        beq.s   .ns
.snd:   move.b  #$0e,_ram+wm_SoundCh3(a4)
.ns:    move.b  d3,_ram+wm_LRScrollDir(a4)
        move.b  d3,d2
.pp:    clr.b   _ram+wm_LRFrameTimer(a4)
.ce4c:  moveq   #0,d0
        move.b  _ram+wm_MarioDirection(a4),d0
        add.b   d0,d0
        move.b  d0,_ram+wm_LRScrollStop(a4)
        move.b  _ram+wm_PosToScrollScreen+1(a4),d1
        lsl.w   #8,d1
        move.b  _ram+wm_PosToScrollScreen(a4),d1    ; w
        lea     _rom00+(DATA_00F6CB-ROM00_BASE)(a4),a0
        move.b  1(a0,d2.w),d3
        lsl.w   #8,d3
        move.b  (a0,d2.w),d3
        cmp.w   d3,d1
        beq.s   .clrf
        lea     _rom00+(DATA_00F6BF-ROM00_BASE)(a4),a0
        move.b  1(a0,d2.w),d3
        lsl.w   #8,d3
        move.b  (a0,d2.w),d3
        add.w   d3,d1
        lea     _rom00+(DATA_00F6B3-ROM00_BASE)(a4),a0
        move.b  1(a0,d0.w),d3
        lsl.w   #8,d3
        move.b  (a0,d0.w),d3
        cmp.w   d3,d1
        bne.s   .st
        clr.b   _ram+wm_LRScrollDir(a4)
.clrf:  clr.b   _ram+wm_LRScrollFlag(a4)
.st:    move.b  d1,_ram+wm_PosToScrollScreen(a4)
        lsr.w   #8,d1
        move.b  d1,_ram+wm_PosToScrollScreen+1(a4)
        clr.b   _ram+wm_LRMoveCamera(a4)
        movem.l (sp)+,d2-d3
        rts

;----------------------------------------------------------------------
; --- mario_collide --- (G5L-R-L2: mcoll.c mario_collide, CODE_00CD24 +
; _00CD39: DC2D, E92B con EB77 y sus seis sondas, F595)
; entrada:  a4 = datos del C
; salida:   como mario_collide()
; registros destruidos: d0-d1/a0-a1 (ABI de vbcc)
; se conservan d2-d7/a2-a3
; ciclos:   tools/l_funcs.py
; Dentro (mc_*): a2 = map16_lo, a3 = map16_hi, d7 = rX, d6 = rY (bytes
; con los 24 bits altos en 0), d4 = probe_mx, d5 = probe_my. rX/rY/
; probe_* no se escriben en sus globales: solo f44d los lee y eb77 los
; arma de nuevo. Las ramas que llaman a GenerateTile, a los sprites de
; rebote, a HurtMario o a tablas del C van al C (mc_* de mcoll.c).
; Verificacion: tools/fuzzcall.py --func mario_collide (las ramas que el
; oraculo no recorre) y el cruce de regress.py.
;----------------------------------------------------------------------
MC_TILESET      equ     $1931               ; wm_LvHeadTileset (mcoll.c TILESET)

MCUNS   macro                               ; unsup(\1): solo si no habia
        tst.l   _mario_unsupported(a4)
        bne.s   .u\@
        moveq   #\1,d0
        move.l  d0,_mario_unsupported(a4)
.u\@:
        endm

        public  _mario_collide
_mario_collide:
        movem.l d2-d7/a2-a3,-(sp)
        clr.l   _mario_unsupported(a4)
        clr.l   _mario_events(a4)
        tst.b   _ram+wm_MarioSpeedY(a4)
        bpl.s   .s0
        btst    #3,_ram+wm_MarioObjStatus(a4)
        beq.s   .s0
        clr.b   _ram+wm_MarioSpeedY(a4)
.s0:    bsr     mc_dc2d
        bsr     mc_e92b
        tst.l   _mario_unsupported(a4)
        bne     .x
        ; CODE_00F595: techo del nivel y caida por abajo
        move.w  _ram+wm_Bg1VOfs(a4),d0
        ror.w   #8,d0
        add.w   #$ff80,d0                   ; t
        move.w  _ram+wm_MarioYPos(a4),d1
        ror.w   #8,d1
        move.w  d0,d2
        sub.w   d1,d2
        bmi.s   .f1
        ror.w   #8,d0
        move.w  d0,_ram+wm_MarioYPos(a4)
.f1:    move.b  _ram+wm_MarioScrPosY+1(a4),d0
        subq.b  #1,d0
        bmi.s   .cd39
        tst.b   _ram+wm_YoshiWingsAboveGrnd(a4)
        beq.s   .f2
        MCUNS   MARIO_UNSUP_YOSHI
        bra.s   .cd39
.f2:    bsr     mc_kill_start               ; _00F60A: se cayo por abajo
.cd39:  clr.b   _ram+wm_PlayerTurningPose(a4)
        tst.b   _ram+wm_PBalloonFrame(a4)
        beq.s   .c1
        MCUNS   MARIO_UNSUP_TILE
        bra.s   .x
.c1:    tst.b   _ram+wm_CanClimbAir(a4)
        beq.s   .c2
        move.b  #$1f,_ram+wm_8B(a4)
.c2:    tst.b   _ram+wm_IsClimbing(a4)
        bne.s   .cl
        move.b  _ram+wm_IsCarrying2(a4),d0
        or.b    _ram+wm_OnYoshi(a4),d0
        bne.s   .sw
        moveq   #$1b,d0
        and.b   _ram+wm_8B(a4),d0
        cmp.b   #$1b,d0
        bne.s   .sw
        moveq   #$0c,d0
        and.b   _ram+wm_JoyPadA(a4),d0
        beq.s   .sw
        tst.b   _ram+wm_IsFlying(a4)
        bne.s   .cl
        btst    #3,_ram+wm_JoyPadA(a4)
        bne.s   .cl
        btst    #2,_ram+wm_8B(a4)
        beq.s   .sw
.cl:    MCUNS   MARIO_UNSUP_CLIMB
        bra.s   .x
.sw:    tst.b   _ram+wm_IsSwimming(a4)
        beq.s   .x
        MCUNS   MARIO_UNSUP_WATER
.x:     movem.l (sp)+,d2-d7/a2-a3
        rts

;----------------------------------------------------------------------
; --- mc_dc2d --- (mcoll.c mario_DC2D + dc4f: velocidad 4.4 a posicion)
; entrada:  a4 = datos del C
; salida:   MarioXPos/YPos, PlayerXAccFixed/YAcc, 8A como el C
; registros destruidos: d0-d2
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
MCDC4F  macro                               ; dc4f(\1): addx = el acarreo de la fraccion
        move.b  _ram+wm_MarioSpeedX+\1(a4),d0
        move.b  d0,d1
        asr.b   #4,d0
        ext.w   d0                          ; (v >> 4) con signo
        lsl.b   #4,d1                       ; (u8)(v << 4)
        move.w  _ram+wm_MarioXPos+\1(a4),d2
        ror.w   #8,d2                       ; ror no toca X
        add.b   d1,_ram+wm_PlayerXAccFixed+\1(a4)
        addx.w  d0,d2
        ror.w   #8,d2
        move.w  d2,_ram+wm_MarioXPos+\1(a4)
        endm

mc_dc2d:
        move.b  _ram+wm_MarioSpeedY(a4),_ram+wm_8A(a4)
        move.b  _ram+wm_WallWalkStatus(a4),d1
        beq.s   .n
        move.b  _ram+wm_MarioSpeedX(a4),d0
        btst    #0,d1
        beq.s   .p
        neg.b   d0
.p:     move.b  d0,_ram+wm_MarioSpeedY(a4)
.n:     MCDC4F  0
        MCDC4F  2
        move.b  _ram+wm_8A(a4),_ram+wm_MarioSpeedY(a4)
        rts

;----------------------------------------------------------------------
; --- mc_f629 --- (mcoll.c f629: KillMario)
; entrada:  a4 = datos del C
; salida:   la animacion de morir como el C
; registros destruidos: ninguno
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_f629:
        move.b  #$90,_ram+wm_MarioSpeedY(a4)
        bsr.s   mc_kill_start
        clr.b   _ram+wm_JoyPadA(a4)         ; no_buttons
        clr.b   _ram+wm_JoyFrameA(a4)
        clr.b   _ram+wm_JoyPadB(a4)
        clr.b   _ram+wm_JoyFrameB(a4)
        rts
;----------------------------------------------------------------------
; --- mc_kill_start ---
; entrada:  a4 = datos del C
; salida:   la animacion de morir (kill_start)
; registros destruidos: ninguno
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_kill_start:
        move.b  #$09,_ram+wm_MusicCh1(a4)
        st      _ram+wm_LevelMusicMod(a4)
        move.b  #$09,_ram+wm_MarioAnimation(a4)
        clr.b   _ram+wm_IsSpinJump(a4)
        move.b  #$30,_ram+wm_PlayerAnimTimer(a4)
        move.b  #$30,_ram+wm_SpritesLocked(a4)
        clr.b   _ram+wm_CapeGlidePhase(a4)
        clr.b   _ram+wm_188A(a4)
        or.b    #8,_mario_events+3(a4)      ; MEV_DEATH
        rts

;----------------------------------------------------------------------
; --- mc_e92b --- (mcoll.c e92b + eaa6 + eadb: CODE_00E92B)
; entrada:  a4 = datos del C
; salida:   como e92b()
; registros destruidos: d0-d7/a0-a3 (los guarda mario_collide)
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_e92b:
        clr.b   _ram+wm_PlayerFrameIndex(a4)        ; eaa6
        clr.b   _ram+wm_MarioObjStatus(a4)
        clr.b   _ram+wm_OnSlopeTypeB(a4)
        clr.b   _ram+wm_OnSlopeTypeA(a4)
        clr.b   _ram+wm_8A(a4)
        clr.b   _ram+wm_8B(a4)
        clr.b   _ram+wm_IsTouchLayer2(a4)
        tst.b   _ram+wm_FallThroughFlag(a4)
        beq.s   .nf
        bsr     mc_ee1d
        bra.s   .e98c
.nf:    move.b  _ram+wm_IsOnGround(a4),_ram+wm_8D(a4)
        clr.b   _ram+wm_IsOnGround(a4)      ; (y el << 1 del C deja 0)
        move.b  _ram+wm_IsFlying(a4),_ram+wm_8F(a4)
        move.b  _ram+wm_IsVerticalLvl(a4),d0
        bpl.s   .nv
        MCUNS   MARIO_UNSUP_LAYER           ; capa 2 interactiva
        rts
.nv:    and.b   #$41,d0
        move.b  d0,_ram+wm_8E(a4)
        add.b   d0,d0
        bmi.s   .e98c
        clr.b   _ram+wm_LayerInProcess(a4)
        move.b  _ram+wm_8D(a4),d0
        add.b   d0,d0
        move.b  d0,_ram+wm_8D(a4)
        moveq   #$0f,d0                     ; eadb
        and.b   _ram+wm_MarioYPos(a4),d0
        move.b  d0,_ram+wm_PlayerBlkPosY(a4)
        tst.b   _ram+wm_WallWalkStatus(a4)
        beq.s   .eb
        MCUNS   MARIO_UNSUP_WALL
        bra.s   .e98c
.eb:    bsr     mc_eb77
.e98c:  tst.b   _ram+wm_SideExitFlag(a4)
        beq.s   .e9a1
        MCUNS   MARIO_UNSUP_LAYER
        rts
.e9a1:  cmp.b   #$f0,_ram+wm_MarioScrPosX(a4)
        blo.s   .e1
        bsr     mc_f629
        bra     .ea32
.e1:    moveq   #3,d0
        and.b   _ram+wm_MarioObjStatus(a4),d0
        bne.s   .e9fb
        move.w  _ram+wm_L1NextPosX(a4),d1
        ror.w   #8,d1
        move.w  _ram+wm_MarioXPos(a4),d2
        ror.w   #8,d2
        moveq   #0,d3                       ; y
        move.w  d1,d0
        add.w   #$00e8,d0
        sub.w   d2,d0
        tst.w   d0                          ; el signo del valor, sin V
        ble.s   .ck
        moveq   #1,d3
        move.w  d2,d0
        subq.w  #8,d0
        sub.w   d1,d0
        tst.w   d0
.ck:    bpl.s   .e9fb                       ; _00E9C8: n == 0 o n > 0
        tst.b   _ram+wm_HorzScrollHead(a4)
        bne.s   .or
        or.b    #$80,_ram+wm_MarioObjStatus(a4)
        move.w  _ram+wm_ScrollSpeedL1X(a4),d0
        ror.w   #8,d0
        lsr.w   #4,d0                       ; sp
        move.b  d0,d1
        sub.b   _ram+wm_MarioSpeedX(a4),d1
        lea     _rom00+(DATA_00E90D+1-ROM00_BASE)(a4),a0
        move.b  (a0,d3.w),d2
        eor.b   d2,d1
        bmi.s   .or
        move.b  d0,_ram+wm_MarioSpeedX(a4)
        move.b  _ram+wm_SprScrollL1X(a4),_ram+wm_PlayerXAccFixed(a4)
.or:    lea     _rom00+(DATA_00E90A-ROM00_BASE)(a4),a0
        move.b  (a0,d3.w),d0
        or.b    d0,_ram+wm_MarioObjStatus(a4)
.e9fb:  moveq   #$1c,d0
        and.b   _ram+wm_MarioObjStatus(a4),d0
        cmp.b   #$1c,d0
        bne.s   .ea0d
        tst.b   _ram+wm_IsOnSolidSpr(a4)
        bne.s   .ea0d
        bsr     mc_f629                     ; aplastado
        bra.s   .ea32
.ea0d:  moveq   #3,d0
        and.b   _ram+wm_MarioObjStatus(a4),d0
        beq.s   .ea34
        and.w   #2,d0                       ; y
        lea     _rom00+(DATA_00E90D-ROM00_BASE)(a4),a0
        move.b  1(a0,d0.w),d1               ; P40 ok
        lsl.w   #8,d1
        move.b  (a0,d0.w),d1
        move.w  _ram+wm_MarioXPos(a4),d2
        ror.w   #8,d2
        add.w   d1,d2
        ror.w   #8,d2
        move.w  d2,_ram+wm_MarioXPos(a4)
        tst.b   _ram+wm_MarioObjStatus(a4)
        bmi.s   .ea34
        move.b  #$03,_ram+wm_PlayerFrameIndex(a4)
        move.b  (a0,d0.w),d1
        move.b  _ram+wm_MarioSpeedX(a4),d2
        eor.b   d1,d2
        bpl.s   .ea34
.ea32:  clr.b   _ram+wm_MarioSpeedX(a4)
.ea34:  cmp.b   #$01,_ram+wm_IsBehindScenery(a4)
        bne.s   .b1
        tst.b   _ram+wm_8B(a4)
        bne.s   .b1
        clr.b   _ram+wm_IsBehindScenery(a4)
.b1:    clr.b   _ram+wm_IsOnWaterTop(a4)
        tst.b   _ram+wm_IsWaterLevel(a4)
        bne.s   .w
        btst    #0,_ram+wm_8A(a4)
        bne.s   .w
        clr.b   _ram+wm_IsSwimming(a4)      ; _00EAA3
        rts
.w:     MCUNS   MARIO_UNSUP_WATER
        rts

;----------------------------------------------------------------------
; --- mc_eb77 --- (mcoll.c eb77, CODE_00EB77: las seis sondas de la capa 1)
; entrada:  a4 = datos del C
; salida:   como eb77()
; registros destruidos: d0-d7/a0-a3 (los guarda mario_collide)
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_eb77:
        tst.b   _probe_ok(a4)
        bne.s   .pk
        PICCALL _mcoll_init                 ; probe_init, una vez
.pk:    move.l  _map16_lo(a4),a2
        move.l  _map16_hi(a4),a3
        move.w  _ram+wm_MarioXPos(a4),d4
        ror.w   #8,d4                       ; probe_mx
        move.w  _ram+wm_MarioYPos(a4),d5
        ror.w   #8,d5                       ; probe_my
        moveq   #0,d6
        moveq   #0,d7                       ; rX
        tst.b   _ram+wm_MarioPowerUp(a4)
        beq.s   .r1
        tst.b   _ram+wm_IsDucking(a4)
        bne.s   .r1
        moveq   #$18,d7
.r1:    tst.b   _ram+wm_OnYoshi(a4)
        beq.s   .r2
        add.b   #$30,d7
.r2:    moveq   #$0f,d0
        and.b   d4,d0                       ; y = MarioXPos & $0F
        moveq   #8,d1
        add.b   d0,d1
        and.b   #$0f,d1
        move.b  d1,_ram+wm_PlayerBlkPosX(a4)
        clr.b   _ram+wm_PlayerBlkSide(a4)
        cmp.b   #8,d0
        blo.s   .r3
        add.b   #$0c,d7                     ; TXA / ADC #$0B con acarreo
        move.b  #1,_ram+wm_PlayerBlkSide(a4)
.r3:    lea     _rom00+(DATA_00E89C+8-ROM00_BASE)(a4),a0
        move.b  (a0,d7.w),d0
        add.b   _ram+wm_PlayerBlkPosY(a4),d0
        and.b   #$0f,d0
        move.b  d0,_ram+wm_PlayerExitBlkPos(a4)

        ; --- sonda 1: el costado, a la altura de la cabeza
        bsr     mc_probe
        beq.s   .ebdd
        cmp.b   #$11,d6
        blo     .ec24
        cmp.b   #$6e,d6
        blo.s   .ebc9
        move.l  d6,-(sp)                    ; f04d(rY): agua (tabla del C)
        PICCALL _mc_f04d
        addq.l  #4,sp
        tst.l   d0
        beq     .ec24
        or.b    #$01,_ram+wm_8A(a4)
        bra     .ec24
.ebc9:  addq.b  #4,d7
        cmp.b   #$1e,d6
        beq.s   .z0
        cmp.b   #$52,d6
        beq.s   .z0
        moveq   #2,d6
        bra     .ec6f
.z0:    moveq   #0,d6
        bra     .ec6f

.ebdd:  cmp.b   #$9c,d6
        bne.s   .d1
        cmp.b   #$01,_ram+MC_TILESET(a4)
        beq.s   .door3
.d1:    cmp.b   #$20,d6
        beq.s   .door2
        cmp.b   #$1f,d6
        beq.s   .d1f
        tst.b   _ram+wm_BluePowTimer(a4)
        beq.s   .ec21
        cmp.b   #$28,d6
        beq.s   .door2
        cmp.b   #$27,d6
        bne.s   .ec21
.d1f:   tst.b   _ram+wm_MarioPowerUp(a4)
        bne.s   .ec24
.door2: moveq   #4,d0                       ; f443
        add.b   d4,d0
        and.b   #$0f,d0
        cmp.b   #8,d0
        bhs.s   .ec24
.door3: tst.b   _ram+wm_8F(a4)
        bne.s   .ec24
        btst    #3,_ram+wm_JoyFrameA(a4)
        beq.s   .ec24
        or.b    #32,_mario_events+3(a4)     ; MEV_PIPE: puerta
        MCUNS   MARIO_UNSUP_PIPE
        rts
.ec21:  move.b  d6,d0                       ; f28c
        sub.b   #$6f,d0
        cmp.b   #4,d0
        bhs.s   .f2c0
        move.b  d6,_rY(a4)                  ; 1-UP invisible: el C
        PICCALL _mc_f28c
        bra.s   .ec24
.f2c0:  moveq   #$01,d0
        bsr     mc_f2c2

        ; --- sonda 2: el costado, a la altura del cuerpo
.ec24:  bsr     mc_probe
        bne.s   .s2
        moveq   #$10,d0
        bsr     mc_f2c9                     ; CODE_00EC35
        bra.s   .ec3a
.s2:    cmp.b   #$11,d6
        blo.s   .ec3a
        cmp.b   #$6e,d6
        bhs.s   .ec3a
        addq.b  #2,d7
        bra.s   .ec4e

        ; --- sonda 3: el costado, a la altura de los pies
.ec3a:  bsr     mc_probe
        bne.s   .s3
        moveq   #$08,d0
        bsr     mc_f2c9
        bra     .ec8a
.s3:    cmp.b   #$11,d6
        blo     .ec8a
        cmp.b   #$6e,d6
        bhs     .ec8a
.ec4e:  move.b  _ram+wm_MarioDirection(a4),d0
        cmp.b   _ram+wm_PlayerBlkSide(a4),d0
        beq.s   .c4f
        cmp.b   #$3f,d6                     ; f3c4: tuberia horizontal
        bne.s   .c67
        tst.b   _ram+wm_8F(a4)
        bne.s   .c4r
        moveq   #$02,d1
        tst.b   d0
        beq.s   .c4a
        moveq   #$01,d1
.c4a:   and.b   _ram+wm_JoyPadA(a4),d1
        beq.s   .c4r
        or.b    #32,_mario_events+3(a4)     ; MEV_PIPE
        MCUNS   MARIO_UNSUP_PIPE
.c4r:   move.b  _ram+wm_Map16NumLo(a4),d6
.c67:   bsr     mc_f267
        move.b  _ram+wm_Map16NumLo(a4),d6
.c4f:   move.b  #$03,_ram+wm_PlayerFrameIndex(a4)
        moveq   #0,d0
        move.b  _ram+wm_PlayerBlkSide(a4),d0
        lea     _rom00+(DATA_00E911-ROM00_BASE)(a4),a0
        moveq   #$0f,d1
        and.b   _ram+wm_MarioXPos(a4),d1
        cmp.b   (a0,d0.w),d1
        beq.s   .ec8a
        move.b  d0,d6
.ec6f:  tst.b   _ram+wm_NoteBlkBounceFlag(a4)
        beq.s   .n6f
        cmp.b   #$52,_ram+wm_Map16NumLo(a4)
        beq.s   .ec8a
.n6f:   lea     _rom00+(DATA_00E90A-ROM00_BASE)(a4),a0
        move.b  (a0,d6.w),d0
        or.b    d0,_ram+wm_MarioObjStatus(a4)
        and.b   #$03,d0
        move.b  d0,d6
        move.b  d6,d1
        move.b  _ram+wm_Map16NumLo(a4),d0
        bsr     mc_f127

        ; --- sonda 4: la cabeza (techo)
.ec8a:  bsr     mc_probe
        bne.s   .ecb1
        moveq   #$02,d0
        bsr     mc_f2c2
        tst.b   _ram+wm_MarioSpeedY(a4)
        bpl     .ed4a
        move.b  _ram+wm_Map16NumLo(a4),d0
        cmp.b   #$21,d0
        blo     .ed4a
        cmp.b   #$25,d0
        bhs     .ed4a
        subq.b  #4,d0                       ; CODE_00ECA6: bloque de nota...
        moveq   #0,d1
        bsr     mc_f17f
        move.b  #$f0,d0
        bra.s   .ed0f
.ecb1:  cmp.b   #$11,d6
        blo     .ed4a
        cmp.b   #$6e,d6
        blo.s   .ecfa
        cmp.b   #$d8,d6
        blo.s   .sl4
        move.w  _ram+wm_BlockXPos(a4),d1
        ror.w   #8,d1
        add.w   #$0010,d1
        move.w  d1,d0
        ror.w   #8,d0
        move.w  d0,_ram+wm_BlockXPos(a4)
        move.w  _ram+wm_BlockYPos(a4),d2
        ror.w   #8,d2
        bsr     mc_pxy                      ; f461
        beq     .ed4a
        cmp.b   #$6e,d6
        blo     .ed4a
        cmp.b   #$d8,d6
        bhs     .ed4a
        sub.b   #$10,_ram+wm_PlayerExitBlkPos(a4)   ; SBC #$0F, C=0
.sl4:   bsr     mc_slope
        tst.b   d1
        bmi.s   .ed0f2
        bra     .ed4a
.ed0f2: move.b  d1,d0
        bra.s   .ed0f
.ecfa:  moveq   #$02,d0
        bsr     mc_f3e9
        move.b  d6,d0
        moveq   #0,d6
        moveq   #0,d1
        bsr     mc_f127
        cmp.b   #$1e,_ram+wm_Map16NumLo(a4)
        beq.s   .ed3b
        move.b  #$f0,d0                     ; _00ED0D
.ed0f:  add.b   _ram+wm_PlayerExitBlkPos(a4),d0
        bpl.s   .ed4a
        cmp.b   #$f9,d0
        bhs.s   .ed28
        tst.b   _ram+wm_IsFlying(a4)
        bne.s   .ed28
        move.b  _ram+wm_MarioObjStatus(a4),d1
        and.b   #$fc,d1
        or.b    #$09,d1
        move.b  d1,_ram+wm_MarioObjStatus(a4)
        clr.b   _ram+wm_MarioSpeedX(a4)
        bra.s   .ed3b
.ed28:  tst.b   _ram+wm_IsFlying(a4)        ; CODE_00ED28
        beq.s   .e8
        not.b   d0
        and.w   #$00ff,d0
        add.w   d0,d5                       ; probe_my
        move.w  d5,d1
        ror.w   #8,d1
        move.w  d1,_ram+wm_MarioYPos(a4)
.e8:    or.b    #$08,_ram+wm_MarioObjStatus(a4)
.ed3b:  tst.b   _ram+wm_MarioSpeedY(a4)
        bpl.s   .ed4a
        clr.b   _ram+wm_MarioSpeedY(a4)
        tst.b   _ram+wm_SoundCh1(a4)
        bne.s   .ed4a
        move.b  #$01,_ram+wm_SoundCh1(a4)

        ; --- sonda 5: los pies (suelo)
.ed4a:  bsr     mc_probe
        beq     .eddb
        cmp.b   #$6e,d6
        bhs.s   .s5
        moveq   #$03,d0
        bsr     mc_f3e9
        bra     .edf7
.s5:    cmp.b   #$d8,d6
        blo.s   .ed86
        cmp.b   #$fb,d6
        blo.s   .ed69
        bra     mc_f629
.ed69:  move.w  _ram+wm_BlockXPos(a4),d1    ; CODE_00ED69
        ror.w   #8,d1
        sub.w   #$0010,d1
        move.w  d1,d0
        ror.w   #8,d0
        move.w  d0,_ram+wm_BlockXPos(a4)
        move.w  _ram+wm_BlockYPos(a4),d2
        ror.w   #8,d2
        bsr     mc_pxy                      ; f461
        beq     .ede9
        cmp.b   #$6e,d6
        blo     .ede9
        cmp.b   #$d8,d6
        bhs     .ede9
        add.b   #$10,_ram+wm_PlayerBlkPosY(a4)      ; ADC #$10, C=0
.ed86:  move.b  _ram+MC_TILESET(a4),d0
        cmp.b   #$03,d0
        beq.s   .t3
        cmp.b   #$0e,d0
        bne.s   .t0
.t3:    cmp.b   #$d2,d6
        bhs     .ede9
.t0:    bsr     mc_slope                    ; d0 = t, d1 = DATA_00E632[...]
        move.b  _ram+wm_PlayerBlkPosY(a4),d2
        sub.b   d1,d2                       ; a
        bpl.s   .g1
        addq.b  #1,_ram+wm_IsOnGround(a4)
.g1:    move.b  d0,d6                       ; rY = t
        lea     _rom00+(DATA_00E51C-ROM00_BASE)(a4),a0
        cmp.b   (a0,d6.w),d2
        bhs     .ede9
        move.b  d2,_ram+wm_PlayerExitBlkPos(a4)
        clr.b   _ram+wm_PlayerBlkPosY(a4)
        move.b  d6,d0                       ; f005: solo con $0E/$0F
        sub.b   #$0e,d0
        cmp.b   #2,d0
        bhs.s   .n5
        move.b  d6,_rY(a4)
        PICCALL _mc_f005
        tst.l   d0
        beq.s   .n5
        move.b  #$24,_ram+wm_IsFlying(a4)   ; PLA/PLA/JMP _00EE35
        rts
.n5:    cmp.b   #$1c,d6
        blo.s   .n6
        move.b  #$08,_ram+wm_SlideImgTimer(a4)
        move.b  d6,d0
        bra     mc_eed1
.n6:    bsr     mc_efbc                     ; CODE_00EDD5
        move.b  d6,d0
        bra     mc_ee85

.eddb:  cmp.b   #$05,d6
        bne.s   .e2
        bsr     mc_f629
        bra.s   .ede9
.e2:    moveq   #$04,d0
        bsr     mc_f2c2

        ; --- sonda 6: los pies, segundo punto
.ede9:  bsr     mc_probe
        bne.s   .s6
        bsr     mc_f309
        bra     mc_ee1d
.s6:    cmp.b   #$6e,d6
        bhs     mc_ee1d
.edf7:  tst.b   _ram+wm_MarioSpeedY(a4)
        bmi     .rts
        move.b  _ram+MC_TILESET(a4),d3      ; t
        cmp.b   #$03,d3
        beq.s   .u3
        cmp.b   #$0e,d3
        bne.s   .u0
.u3:    move.b  _ram+wm_Map16NumLo(a4),d0
        cmp.b   #$59,d0
        blo.s   .u0
        cmp.b   #$5c,d0
        blo     mc_ee1d
.u0:    moveq   #$0f,d0
        and.b   _ram+wm_PlayerBlkPosY(a4),d0
        clr.b   _ram+wm_PlayerBlkPosY(a4)
        move.b  d0,_ram+wm_PlayerExitBlkPos(a4)
        cmp.b   #8,d0
        bhs     mc_ee1d
        move.b  _ram+wm_Map16NumLo(a4),d6   ; CODE_00EE3A
        cmp.b   #$02,d3
        beq.s   .cv
        cmp.b   #$08,d3
        bne.s   .e57
.cv:    move.b  d6,d0
        sub.b   #$0c,d0
        cmp.b   #2,d0
        bhs.s   .e57
        add.b   d0,d0
        bsr     mc_efcd
        moveq   #$20,d0
        bra     mc_ee85
.e57:   bsr     mc_f267                     ; CODE_00EE57
        moveq   #$03,d6
        move.b  _ram+wm_Map16NumLo(a4),d0
        cmp.b   #$1e,d0
        bne.s   .n1e
        tst.b   _ram+wm_8F(a4)
        beq.s   .ee83
        tst.b   _ram+wm_MarioPowerUp(a4)
        beq.s   .ee83
        tst.b   _ram+wm_IsSpinJump(a4)
        beq.s   .ee83
        moveq   #$21,d0                     ; romper el bloque giratorio
        moveq   #$03,d1
        bsr     mc_f17f
        bra     mc_ee1d
.n1e:   cmp.b   #$32,d0
        bne.s   .n32
        clr.b   _ram+wm_RunEaterBlock(a4)
.n32:   move.b  d6,d1
        bsr     mc_f120
.ee83:  moveq   #$20,d0
        bra     mc_ee85
.rts:   rts

;----------------------------------------------------------------------
; --- mc_probe --- (mcoll.c f44d / f461_xy: CODE_00F44D, F465)
; entrada:  mc_probe: d7 = rX, d4/d5 = probe_mx/my; mc_pxy: d2 = x
;           (BlockYPos), d1 = y (BlockXPos); a2/a3 = map16_lo/hi
; salida:   d0.b = pagina con los flags (beq = 0), d6 = rY, d7 = rX + 2;
;           Map16NumLo y BlockYPos/XPos (mc_probe) como el C
; registros destruidos: d0-d2/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_probe:
        addq.b  #2,d7
        moveq   #$7e,d1
        and.b   d7,d1                       ; k = 2 * ((rX >> 1) & 63)
        lea     _probe_dx(a4),a0
        move.w  (a0,d1.w),d2
        add.w   d4,d2                       ; x
        lea     _probe_dy(a4),a0
        move.w  (a0,d1.w),d1
        add.w   d5,d1                       ; y
        move.w  d2,d0
        ror.w   #8,d0
        move.w  d0,_ram+wm_BlockYPos(a4)    ; (el ROM pone x en BlockYPos)
        move.w  d1,d0
        ror.w   #8,d0
        move.w  d0,_ram+wm_BlockXPos(a4)
;----------------------------------------------------------------------
; --- mc_pxy ---
; entrada:  d2 = x (BlockYPos), d1 = y (BlockXPos); a2/a3 = map16_lo/hi
; salida:   d0.b = pagina con flags, d6 = rY (f461_xy)
; registros destruidos: d0-d2/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_pxy:
        clr.b   _ram+wm_WhichSwitchPressed(a4)
        tst.b   _ram+wm_8E(a4)
        bne     .l2
        cmp.w   #$1b0,d1
        bhs     .off
        move.w  d2,d0
        lsr.w   #8,d0                       ; pantalla
        cmp.b   _ram+wm_ScreensInLvl(a4),d0
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
        move.b  (a2,d0.w),d6                ; lo = rY
        move.b  d6,_ram+wm_Map16NumLo(a4)
        move.b  (a3,d0.w),d0                ; pagina
        beq.s   .p0
        cmp.b   #$32,d6
        beq.s   .sw
        cmp.b   #$2f,d6
        beq.s   .sw
        rts                                 ; d0.b != 0, flags de move.b
.p0:    cmp.b   #$29,d6
        beq.s   .sw
        cmp.b   #$2b,d6
        beq.s   .sw
        move.b  d6,d1
        sub.b   #$ec,d1
        cmp.b   #$10,d1
        bhs.s   .z
.sw:    moveq   #0,d1                       ; interruptores P: f545 en C
        move.b  d0,d1
        move.l  d1,-(sp)
        PICCALL _f44d_tail
        addq.l  #4,sp
        move.b  _ram+wm_Map16NumLo(a4),d6
        tst.b   d0
        rts
.z:     moveq   #0,d0
        rts
.l2:    MCUNS   MARIO_UNSUP_LAYER
.off:   moveq   #$25,d6                     ; CODE_00F4A0: fuera del nivel
        moveq   #0,d0
        rts

;----------------------------------------------------------------------
; --- mc_slope --- (eb77: la pendiente bajo la sonda, DATA_00E632)
; entrada:  d6 = rY (>= $6E)
; salida:   d0.b = t = T8V(SlopeSteepness + rY - $6E),
;           d1.b = DATA_00E632[(t << 4) | PlayerBlkPosX]
; registros destruidos: d0-d1/a0
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_slope:
        move.w  _ram+wm_SlopeSteepness(a4),d0
        ror.w   #8,d0
        moveq   #0,d1
        move.b  d6,d1
        sub.b   #$6e,d1
        add.w   d1,d0
        sub.w   #ROM00_BASE,d0
        and.l   #$ffff,d0                   ; T8V: indice de 16 bits sin signo
        lea     _rom00(a4),a0
        move.b  (a0,d0.l),d0
        moveq   #0,d1
        move.b  d0,d1
        lsl.w   #4,d1
        or.b    _ram+wm_PlayerBlkPosX(a4),d1
        lea     _rom00+(DATA_00E632-ROM00_BASE)(a4),a0
        move.b  (a0,d1.w),d1
        rts

;----------------------------------------------------------------------
; --- mc_f3e9 --- (mcoll.c f3e9: tuberia vertical)
; entrada:  d0 = direccion (2/3, f3e9); d6 = rY
; salida:   d6 = rY (Map16NumLo si es una tuberia), como el C
; registros destruidos: d0-d2/a0
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_f3e9:
        moveq   #0,d1
        move.b  d6,d1
        sub.b   #$37,d1
        cmp.b   #2,d1
        bhs.s   .r
        lea     _rom00+(DATA_00F3E3-ROM00_BASE)(a4),a0
        move.b  _ram+wm_PlayerBlkPosX(a4),d2
        sub.b   (a0,d1.w),d2
        subq.b  #1,d2
        cmp.b   #5,d2
        bhs.s   .m
        moveq   #$08,d1                     ; PIPE_BUTTONS
        cmp.b   #2,d0
        beq.s   .b
        moveq   #$04,d1
.b:     and.b   _ram+wm_JoyPadA(a4),d1
        beq.s   .m
        or.b    #32,_mario_events+3(a4)     ; MEV_PIPE
        MCUNS   MARIO_UNSUP_PIPE
.m:     move.b  _ram+wm_Map16NumLo(a4),d6
.r:     rts

;----------------------------------------------------------------------
; --- mc_f267 ---
; entrada:  d6 = rY
; salida:   como f267 (el bloque para tirar)
; registros destruidos: d0
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_f267:
        cmp.b   #$2e,d6
        bne.s   .r
        btst    #6,_ram+wm_JoyFrameA(a4)
        beq.s   .r
        move.b  _ram+wm_IsCarrying2(a4),d0
        or.b    _ram+wm_OnYoshi(a4),d0
        bne.s   .r
        or.b    #4,_mario_events+2(a4)      ; MEV_SPRITE
        MCUNS   MARIO_UNSUP_TILE
.r:     rts

;----------------------------------------------------------------------
; --- mc_f2c2 --- (mcoll.c: el bloque que toca la sonda; monedas,
; cinta y luna van al C: GenerateTile)
; entrada:  d0 = a (f2c2/f2c9); d6 = rY
; salida:   como el C
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_f2c2:
        cmp.b   #$06,d6
        bhs.s   mc_f2c9
        or.b    d0,_ram+wm_8A(a4)
        rts
;----------------------------------------------------------------------
; --- mc_f2c9 ---
; entrada:  d0 = a; d6 = rY
; salida:   como f2c9
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_f2c9:
        cmp.b   #$38,d6
        beq.s   .c
        cmp.b   #$06,d6
        beq.s   .s
        cmp.b   #$07,d6
        blo.s   mc_f309
        cmp.b   #$1d,d6
        bhs.s   mc_f309
        or.b    #$80,d0
.s:     cmp.b   #$01,d0
        bne.s   .o
        or.b    #$18,d0
.o:     or.b    d0,_ram+wm_8B(a4)
        move.b  _ram+wm_PlayerBlkSide(a4),_ram+wm_8C(a4)
        rts
.c:     and.l   #$ff,d0                     ; cinta del punto medio: el C
        move.b  d6,_rY(a4)
        move.l  d0,-(sp)
        PICCALL _mc_f2c9
        addq.l  #4,sp
        rts
;----------------------------------------------------------------------
; --- mc_f309 ---
; entrada:  d6 = rY
; salida:   como f309 (monedas y luna: el C)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_f309:
        move.b  d6,d0
        sub.b   #$2a,d0
        cmp.b   #5,d0
        blo.s   .c
        cmp.b   #$6e,d6
        beq.s   .c
        rts
.c:     move.b  d6,_rY(a4)                  ; monedas y luna: el C
        PICCALL _mc_f309
        rts

;----------------------------------------------------------------------
; --- mc_f120 --- (mcoll.c: el bloque toca a Mario; los bloques que
; danian y los de rebote van al C)
; entrada:  d0 = a (numero de bloque), d1 = y
; salida:   como el C
; registros destruidos: d0-d2/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_f120:
        tst.b   _ram+wm_OnYoshi(a4)
        bne.s   mc_f160
;----------------------------------------------------------------------
; --- mc_f127 ---
; entrada:  d0 = a, d1 = y
; salida:   como f127
; registros destruidos: d0-d2/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_f127:
        cmp.b   #$2f,d0
        beq.s   .c
        cmp.b   #$59,d0
        blo.s   mc_f160                     ; pp: a < $66 -> f160
.c:     and.l   #$ff,d0
        and.l   #$ff,d1
        move.l  d1,-(sp)
        move.l  d0,-(sp)
        PICCALL _mc_f127
        addq.l  #8,sp
        rts
;----------------------------------------------------------------------
; --- mc_f160 ---
; entrada:  d0 = a, d1 = y
; salida:   como f160
; registros destruidos: d0-d2/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_f160:
        move.b  d0,d2
        sub.b   #$11,d2
        cmp.b   #$1d,d2
        blo.s   .f
        cmp.b   #$07,_ram+MC_TILESET(a4)
        bne.s   .u
        sub.b   #$59,d2                     ; CODE_00F176, carry = 1
        cmp.b   #2,d2
        bhs.s   .r
        add.b   #$22,d2
.f:     move.b  d2,d0
        bra.s   mc_f17f
.u:     MCUNS   MARIO_UNSUP_TILE
.r:     rts
;----------------------------------------------------------------------
; --- mc_f17f ---
; entrada:  d0 = a, d1 = y
; salida:   como f17f (sprites de rebote: el C)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_f17f:
        and.l   #$ff,d0                     ; sprites de rebote: el C
        and.l   #$ff,d1
        move.l  d1,-(sp)
        move.l  d0,-(sp)
        PICCALL _mc_f17f
        addq.l  #8,sp
        rts

;----------------------------------------------------------------------
; --- mc_ee1d --- (mcoll.c: apoyar a Mario en el suelo)
; entrada:  d0 = y (tipo de pendiente) en ee85/eed1/eee1
; salida:   como el C
; registros destruidos: d0-d3/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_ee1d:
        tst.b   _ram+wm_IsOnSolidSpr(a4)
        beq.s   .n
        tst.b   _ram+wm_MarioSpeedY(a4)
        bmi.s   .n
        clr.b   _ram+wm_8E(a4)
        moveq   #$20,d0
        bra.s   mc_eee1
.n:     btst    #2,_ram+wm_MarioObjStatus(a4)
        bne.s   .r
        tst.b   _ram+wm_IsFlying(a4)
        bne.s   .r
        move.b  #$24,_ram+wm_IsFlying(a4)
.r:     rts

;----------------------------------------------------------------------
; --- mc_ee85 ---
; entrada:  d0 = y
; salida:   como ee85
; registros destruidos: d0-d3/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_ee85:
        tst.b   _ram+wm_MarioSpeedY(a4)
        bpl.s   .a
        cmp.b   #2,_ram+wm_8D(a4)
        blo.s   .r
.a:     tst.b   _ram+wm_WhichSwitchPressed(a4)
        beq.s   mc_eed1
        or.b    #2,_mario_events+2(a4)      ; MEV_SWITCH: interruptor de palacio
        MCUNS   MARIO_UNSUP_TILE
.r:     rts

;----------------------------------------------------------------------
; --- mc_eed1 ---
; entrada:  d0 = y
; salida:   como eed1
; registros destruidos: d0-d3/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_eed1:
        addq.b  #1,_ram+wm_IsOnGround(a4)
        move.w  _ram+wm_PlayerBlkPosY(a4),d1    ; (BlkPosY << 8) | ExitBlkPos ($90/$91)
        move.w  _ram+wm_MarioYPos(a4),d2
        ror.w   #8,d2
        sub.w   d1,d2
        ror.w   #8,d2
        move.w  d2,_ram+wm_MarioYPos(a4)
;----------------------------------------------------------------------
; --- mc_eee1 ---
; entrada:  d0 = y (tipo de pendiente)
; salida:   como eee1
; registros destruidos: d0-d3/a0-a1
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_eee1:
        moveq   #0,d3
        move.b  d0,d3                       ; y
        lea     _rom00+(DATA_00E53D-ROM00_BASE)(a4),a0
        move.b  (a0,d3.w),d0                ; a
        bne.s   .p1
        move.b  _ram+wm_PlayerSlopePose(a4),d1
        beq.s   .p3
        move.b  _ram+wm_MarioSpeedX(a4),d1
        beq.s   .p2
.p1:    move.b  d0,_ram+wm_OnSlopeTypeA(a4)
        btst    #2,_ram+wm_JoyPadA(a4)
        beq.s   .p3
        move.b  _ram+wm_IsCarrying2(a4),d1
        or.b    _ram+wm_PlayerSlopePose(a4),d1
        bne.s   .p3
        moveq   #$1c,d1
.p2:    move.b  d1,_ram+wm_PlayerSlopePose(a4)
.p3:    lea     _rom00+(DATA_00E4B9-ROM00_BASE)(a4),a1
        move.b  (a1,d3.w),d1                ; x
        move.b  d1,_ram+wm_OnSlopeTypeB(a4)
        cmp.b   #$1c,d3
        bhs.s   .ef38
        move.b  _ram+wm_MarioSpeedX(a4),d2
        beq.s   .ef31
        move.b  (a0,d3.w),d0
        beq.s   .ef31
        eor.b   d2,d0
        bpl.s   .ef31
        move.b  d1,_ram+wm_PlayerFrameIndex(a4)
        move.b  d2,d0
        bpl.s   .ab
        neg.b   d0
.ab:    cmp.b   #$28,d0
        blo.s   .y20
        lea     _rom00+(DATA_00E4FB-ROM00_BASE)(a4),a1
        move.b  (a1,d3.w),d0
        bra.s   .ef60
.y20:   moveq   #$20,d3                     ; CODE_00EF2F
.ef31:  lea     _rom00+(DATA_00E4DA-ROM00_BASE)(a4),a1
        move.b  _ram+wm_MarioSpeedY(a4),d0
        cmp.b   (a1,d3.w),d0
        blo.s   .ef3b
        bra.s   .ef39
.ef38:  lea     _rom00+(DATA_00E4DA-ROM00_BASE)(a4),a1
.ef39:  move.b  (a1,d3.w),d0
.ef3b:  tst.b   _ram+wm_8E(a4)
        bpl.s   .ef60
        MCUNS   MARIO_UNSUP_LAYER
        rts
.ef60:  move.b  d0,_ram+wm_MarioSpeedY(a4)
        bpl.s   .g
        addq.b  #1,_ram+wm_IsOnGround(a4)
.g:     clr.b   _ram+wm_FollowCage(a4)
        clr.b   _ram+wm_IsFlying(a4)
        clr.b   _ram+wm_IsClimbing(a4)
        clr.b   _ram+wm_BouncingWithYoshi(a4)
        clr.b   _ram+wm_IsSpinJump(a4)
        or.b    #$04,_ram+wm_MarioObjStatus(a4)
        move.b  _ram+wm_CapeGlidePhase(a4),d1
        beq.s   .ny
        clr.b   _ram+wm_SprChainStomped(a4) ; CODE_00EF99
        clr.b   _ram+wm_CapeGlidePhase(a4)
        cmp.b   #5,d1
        blo.s   .cp
        tst.b   _ram+wm_8F(a4)
        beq.s   .r
        or.b    #1,_mario_events+2(a4)      ; MEV_POUND
        rts
.cp:    cmp.b   #2,_ram+wm_MarioPowerUp(a4)
        bne.s   .r
        move.b  _ram+wm_PlayerSlopePose(a4),d0
        lsr.b   #1,d0
        or.b    #$80,d0
        move.b  d0,_ram+wm_PlayerSlopePose(a4)
        rts
.ny:    tst.b   _ram+wm_OnYoshi(a4)
        beq.s   .s
        tst.b   _ram+wm_8F(a4)
        beq.s   .s
        tst.b   _ram+wm_YoshiHasStomp(a4)
        beq.s   .s
        or.b    #1,_mario_events+2(a4)      ; MEV_POUND
.s:     clr.b   _ram+wm_SprChainStomped(a4)
.r:     rts

;----------------------------------------------------------------------
; --- mc_efbc --- (mcoll.c: cintas transportadoras)
; entrada:  mc_efcd: d0 = x (indice de 16 bits de las tablas)
; salida:   como el C
; registros destruidos: d0-d2/a0
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_efbc:
        move.b  _ram+wm_Map16NumLo(a4),d0
        sub.b   #$ce,d0
        cmp.b   #4,d0
        bhs.s   .r
        addq.b  #2,d0
        add.b   d0,d0                       ; (x - $CC) << 1
        bra.s   mc_efcd
.r:     rts
;----------------------------------------------------------------------
; --- mc_efcd ---
; entrada:  d0 = x (indice de las tablas)
; salida:   como efcd
; registros destruidos: d0-d2/a0
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mc_efcd:
        moveq   #3,d1
        and.b   _ram+wm_FrameA(a4),d1
        bne.s   .r
        and.w   #$ff,d0
        lea     _rom00+(DATA_00E913-ROM00_BASE)(a4),a0
        move.b  1(a0,d0.w),d1               ; P40 ok
        lsl.w   #8,d1
        move.b  (a0,d0.w),d1
        move.w  _ram+wm_MarioXPos(a4),d2
        ror.w   #8,d2
        add.w   d1,d2
        ror.w   #8,d2
        move.w  d2,_ram+wm_MarioXPos(a4)
        lea     _rom00+(DATA_00E91F-ROM00_BASE)(a4),a0
        move.b  1(a0,d0.w),d1               ; P40 ok
        lsl.w   #8,d1
        move.b  (a0,d0.w),d1
        move.w  _ram+wm_MarioYPos(a4),d2
        ror.w   #8,d2
        add.w   d1,d2
        ror.w   #8,d2
        move.w  d2,_ram+wm_MarioYPos(a4)
.r:     rts

;----------------------------------------------------------------------
; --- mario_D5F2 --- (G5L-R-L2: mario.c mario_D5F2, CODE_00D5F2: velocidad
; X, agacharse, saltar)
; entrada:  a4 = datos del C
; salida:   como mario_D5F2()
; registros destruidos: d0-d1/a0-a1 (ABI de vbcc)
; se conservan d2-d3
; ciclos:   tools/l_funcs.py
; x en d2 y y en d3 (indices de 16 bits, bytes con los bits altos en 0).
;----------------------------------------------------------------------
        public  _mario_D5F2
_mario_D5F2:
        movem.l d2-d3,-(sp)
        clr.l   _mario_unsupported(a4)
        tst.b   _ram+wm_IsFlying(a4)
        bne     .d682
        clr.b   _ram+wm_IsDucking(a4)       ; CODE_00D5F9
        tst.b   _ram+wm_PlayerSlopePose(a4)
        bne.s   .a1
        moveq   #$04,d0
        and.b   _ram+wm_JoyPadA(a4),d0
        beq.s   .a1
        move.b  d0,_ram+wm_IsDucking(a4)
        clr.b   _ram+wm_CapeCanHurt(a4)
.a1:    cmp.b   #$02,_ram+wm_IsOnSolidSpr(a4)
        beq.s   .a2
        btst    #3,_ram+wm_MarioObjStatus(a4)
        bne.s   .a2
        move.b  _ram+wm_JoyFrameA(a4),d0
        or.b    _ram+wm_JoyFrameB(a4),d0
        bmi.s   .d630
.a2:    tst.b   _ram+wm_IsDucking(a4)
        beq     .d682
        tst.b   _ram+wm_MarioSpeedX(a4)
        beq     .d764
        tst.b   _ram+wm_IsSlipperyLevel(a4)
        bne     .d764
        move.b  #1,_fe_cin(a4)              ; C = 1 (CMP #$02, SW-S)
        bsr     mr_fe4a
        bra     .d764

.d630:  move.b  _ram+wm_MarioSpeedX(a4),d0 ; CODE_00D630: empieza el salto
        bpl.s   .ab
        neg.b   d0
.ab:    lsr.b   #2,d0
        and.b   #$fe,d0
        moveq   #0,d2
        move.b  d0,d2                       ; x
        tst.b   _ram+wm_JoyFrameB(a4)
        bpl.s   .d65e
        tst.b   _ram+wm_IsCarrying2(a4)
        bne.s   .d65e
        move.b  #$01,_ram+wm_IsSpinJump(a4)
        move.b  #$04,_ram+wm_SoundCh3(a4)
        moveq   #0,d0
        move.b  _ram+wm_MarioDirection(a4),d0
        lea     _rom00+(DATA_00D5F0-ROM00_BASE)(a4),a0
        move.b  (a0,d0.w),_ram+wm_SpinFireTimer(a4)
        tst.b   _ram+wm_OnYoshi(a4)
        bne.s   .d682
        addq.b  #1,d2
        bra.s   .d663
.d65e:  move.b  #$01,_ram+wm_SoundCh2(a4)
.d663:  lea     _rom00+(DATA_00D2BD-ROM00_BASE)(a4),a0
        move.b  (a0,d2.w),_ram+wm_MarioSpeedY(a4)
        moveq   #$0b,d0
        cmp.b   #$70,_ram+wm_PlayerDashTimer(a4)
        blo.s   .s
        tst.b   _ram+wm_GlideTimer(a4)
        bne.s   .g
        move.b  #$50,_ram+wm_GlideTimer(a4)
.g:     moveq   #$0c,d0
.s:     move.b  d0,_ram+wm_IsFlying(a4)
        clr.b   _ram+wm_PlayerSlopePose(a4)

.d682:  tst.b   _ram+wm_PlayerSlopePose(a4) ; _00D682
        bmi.s   .fe
        moveq   #$03,d0
        and.b   _ram+wm_JoyPadA(a4),d0
        bne.s   .d6b1
        tst.b   _ram+wm_PlayerSlopePose(a4)
        beq     .d764
.fe:    clr.b   _fe_cin(a4)                 ; (sin B abajo: el C de antes)
        bsr     mr_fe4a
        tst.b   _ram+wm_OnSlopeTypeA(a4)
        beq     .d764
        moveq   #0,d0
        bsr     mr_d96a                     ; CODE_00D968
        moveq   #0,d0
        move.b  _ram+wm_OnSlopeTypeB(a4),d0
        moveq   #2,d1
        and.b   d0,d1
        lsr.b   #1,d1                       ; c = acarreo del segundo LSR
        lsr.b   #2,d0                       ; a = y
        moveq   #0,d2
        move.b  d0,d2
        add.b   #$76,d2
        add.b   d1,d2                       ; x = a + $76 + c
        moveq   #1,d1
        and.b   d0,d1                       ; c = y & 1
        lsr.b   #1,d0
        add.b   #$87,d0
        add.b   d1,d0
        moveq   #0,d3
        move.b  d0,d3                       ; y = (y >> 1) + $87 + c
        bra     .d742

.d6b1:  clr.b   _ram+wm_PlayerSlopePose(a4) ; CODE_00D6B1
        and.b   #$01,d0                     ; a
        tst.b   _ram+wm_CapeGlidePhase(a4)
        beq.s   .d6d5
        moveq   #MARIO_UNSUP_CAPE,d0
        move.l  d0,_mario_unsupported(a4)
        bra     .x
.d6d5:  cmp.b   _ram+wm_MarioDirection(a4),d0
        beq.s   .pp
        tst.b   _ram+wm_IsCarrying2(a4)
        beq.s   .sd
        tst.b   _ram+wm_FaceCamImgTimer(a4)
        bne.s   .pp
        move.b  #$08,_ram+wm_FaceCamImgTimer(a4)
.sd:    move.b  d0,_ram+wm_MarioDirection(a4)
.pp:    move.b  d0,_ram+m1(a4)
        moveq   #0,d2
        move.b  d0,d2
        lsl.b   #2,d2
        or.b    _ram+wm_OnSlopeTypeB(a4),d2 ; x
        move.b  _ram+wm_MarioSpeedX(a4),d1
        beq.s   .d713
        lea     _rom00+(MarioAccel+1-ROM00_BASE)(a4),a0
        move.b  (a0,d2.w),d0
        eor.b   d1,d0
        bpl.s   .d713
        tst.b   _ram+wm_SlideImgTimer(a4)
        bne.s   .d713
        tst.b   _ram+wm_IsSlipperyLevel(a4)
        bne.s   .x90
        move.b  #$0d,_ram+wm_PlayerTurningPose(a4)
        clr.b   _fe_cin(a4)                 ; los ASL dejan C = 0
        bsr     mr_fe4a
.x90:   add.b   #$90,d2
.d713:  moveq   #0,d0                       ; _00D713: y
        btst    #6,_ram+wm_JoyPadA(a4)      ; BIT / BVC: Y = correr
        beq.s   .d737
        addq.b  #2,d2
        addq.b  #1,d0
        move.b  _ram+wm_MarioSpeedX(a4),d1
        bpl.s   .ab2
        neg.b   d1
.ab2:   sub.b   #$23,d1
        bmi.s   .d737
        move.b  _ram+wm_IsFlying(a4),d1
        bne.s   .fl
        move.b  #$10,_ram+wm_RunCapeTimer(a4)
        addq.b  #1,d0
        bra.s   .d737
.fl:    cmp.b   #$0c,d1
        bne.s   .d737
        addq.b  #1,d0
.d737:  bsr     mr_d96a                     ; _00D737
        add.b   d0,d0
        or.b    _ram+wm_OnSlopeTypeB(a4),d0
        or.b    _ram+m1(a4),d0
        moveq   #0,d3
        move.b  d0,d3                       ; y

.d742:  lea     _rom00+(DATA_00D535-ROM00_BASE)(a4),a0  ; _00D742
        move.b  _ram+wm_MarioSpeedX(a4),d0
        move.b  (a0,d3.w),d1
        sub.b   d1,d0
        beq.s   .d76b
        eor.b   d1,d0
        bpl.s   .d76b
        lea     _rom00+(MarioAccel-ROM00_BASE)(a4),a0
        tst.b   _ram+wm_IsSlipperyLevel(a4)
        beq.s   .ac
        tst.b   _ram+wm_IsFlying(a4)
        bne.s   .ac
        lea     _rom00+(DATA_00D43D-ROM00_BASE)(a4),a0
.ac:    move.b  1(a0,d2.w),d0               ; P40 ok
        lsl.w   #8,d0
        move.b  (a0,d2.w),d0                ; w
        move.w  _ram+wm_MarioAccSpeedX(a4),d1
        ror.w   #8,d1
        add.w   d1,d0
        ror.w   #8,d0
        move.w  d0,_ram+wm_MarioAccSpeedX(a4)   ; _00D7A0
        bra.s   .x

.d764:  moveq   #0,d0                       ; CODE_00D764
        bsr     mr_d96a
        tst.b   _ram+wm_IsFlying(a4)
        bne.s   .x
.d76b:  moveq   #0,d3                       ; _00D76B
        move.b  _ram+wm_OnSlopeTypeB(a4),d3
        lsr.b   #1,d3                       ; y
        moveq   #0,d2
        move.b  d3,d2
        lsr.b   #1,d2                       ; x
        lea     _rom00+(DATA_00D5C9+1-ROM00_BASE)(a4),a0
        move.b  _ram+wm_MarioSpeedX(a4),d0
        sub.b   (a0,d2.w),d0
        bpl.s   .n
        addq.b  #2,d3
.n:     lea     _rom00+(DATA_00D2CD-ROM00_BASE)(a4),a1
        move.l  a1,a0
        move.b  _ram+wm_EndLevelTimer(a4),d0
        or.b    _ram+wm_IsFlying(a4),d0
        bne.s   .w
        tst.b   _ram+wm_IsWaterLevel+1(a4)  ; BIT con A de 16 bits: el byte siguiente
        bpl.s   .w
        lea     _rom00+(DATA_00D309-ROM00_BASE)(a4),a0
.w:     move.b  1(a0,d3.w),d0               ; P40 ok
        lsl.w   #8,d0
        move.b  (a0,d3.w),d0
        move.w  _ram+wm_MarioAccSpeedX(a4),d1
        ror.w   #8,d1
        add.w   d1,d0                       ; w
        move.w  d0,d1
        ror.w   #8,d1
        move.w  d1,_ram+wm_MarioAccSpeedX(a4)
        lea     _rom00+(DATA_00D5C9-ROM00_BASE)(a4),a0
        move.b  1(a0,d2.w),d1               ; P40 ok
        lsl.w   #8,d1
        move.b  (a0,d2.w),d1                ; tope
        sub.w   d1,d0
        lsr.w   #8,d0
        move.b  1(a1,d3.w),d3               ; P40 ok; byte alto de DATA_00D2CD[y]
        eor.b   d3,d0
        bmi.s   .x
        ror.w   #8,d1
        move.w  d1,_ram+wm_MarioAccSpeedX(a4)   ; _00D7A0
.x:     movem.l (sp)+,d2-d3
        rts

;----------------------------------------------------------------------
; --- mr_d96a --- (mario.c d96a, CODE_00D968/_00D96A: medidor de carrera)
; entrada:  d0.b = y
; salida:   d0 = y (+1 si el medidor llego a $70), de 16 bits
; registros destruidos: d1/a0
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mr_d96a:
        and.w   #$ff,d0
        lea     _rom00+(DATA_00D5EB-ROM00_BASE)(a4),a0
        move.b  _ram+wm_PlayerDashTimer(a4),d1
        add.b   (a0,d0.w),d1
        bpl.s   .p
        moveq   #0,d1
.p:     cmp.b   #$70,d1
        blo.s   .s
        addq.b  #1,d0
        moveq   #$70,d1
.s:     move.b  d1,_ram+wm_PlayerDashTimer(a4)
        rts

;----------------------------------------------------------------------
; --- mr_fe4a --- (mario.c fe4a, CODE_00FE4A: humo al frenar)
; entrada:  a4 = datos del C
; salida:   las tablas de humo como el C
; registros destruidos: d0-d1/a0
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
mr_fe4a:
        moveq   #$03,d0
        and.b   _ram+wm_FrameA(a4),d0
        or.b    _ram+wm_IsFlying(a4),d0
        or.b    _ram+wm_MarioScrPosX+1(a4),d0
        or.b    _ram+wm_MarioScrPosY+1(a4),d0
        or.b    _ram+wm_SpritesLocked(a4),d0
        bne.s   .r
        btst    #2,_ram+wm_JoyPadA(a4)
        beq.s   .l
        move.b  _ram+wm_MarioSpeedX(a4),d0
        addq.b  #8,d0
        cmp.b   #$10,d0
        blo.s   .r
.l:     lea     _ram+wm_SmokeSprite(a4),a0
        moveq   #3,d1
.lp:    tst.b   (a0,d1.w)
        beq.s   .f
        subq.b  #1,d1
        bne.s   .lp
.r:     rts
.f:     move.b  #$03,(a0,d1.w)              ; CODE_00FE72
        move.l  d2,-(sp)
        moveq   #1,d0                       ; el carry de los ADC: 1 si pasó
        btst    #2,_ram+wm_JoyPadA(a4)      ; por el CMP #$10, si no el del
        bne.s   .c                          ; que llama (_fe_cin, SW-S)
        move.b  _fe_cin(a4),d0
.c:     neg.b   d0                          ; X = el carry
        moveq   #4,d2                       ; (moveq, move, lea y tst no
        move.b  _ram+wm_MarioXPos(a4),d0    ; tocan X)
        addx.b  d2,d0                       ; ADC #$04
        lea     _ram+wm_SmokeXPos(a4),a0
        move.b  d0,(a0,d1.w)
        moveq   #$1a,d2
        move.b  _ram+wm_MarioYPos(a4),d0
        addx.b  d2,d0                       ; ADC #$1A
        tst.b   _ram+wm_OnYoshi(a4)
        beq.s   .y
        moveq   #$10,d2
        addx.b  d2,d0                       ; ADC #$10
.y:     lea     _ram+wm_SmokeYPos(a4),a0
        move.b  d0,(a0,d1.w)
        lea     _ram+wm_SmokeTimer(a4),a0
        move.b  #$13,(a0,d1.w)
        move.l  (sp)+,d2
        rts

;----------------------------------------------------------------------
; --- mario_D062 --- (mario.c mario_D062: capa (giro) y flor de fuego)
; entrada:  a4 = datos del C
; salida:   como mario_D062()
; registros destruidos: d0 (ABI de vbcc)
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
        public  _mario_D062
_mario_D062:
        move.b  _ram+wm_MarioPowerUp(a4),d0
        cmp.b   #$02,d0
        bne.s   .f
        btst    #6,_ram+wm_JoyFrameA(a4)
        beq.s   .r
        move.b  _ram+wm_IsDucking(a4),d0
        or.b    _ram+wm_OnYoshi(a4),d0
        or.b    _ram+wm_IsSpinJump(a4),d0
        bne.s   .r
        move.b  #$12,_ram+wm_CapeSpinTimer(a4)
        move.b  #$04,_ram+wm_SoundCh3(a4)
        rts
.f:     cmp.b   #$03,d0
        bne.s   .r
        moveq   #MARIO_UNSUP_FIRE,d0        ; ShootFireball: sin portar
        move.l  d0,_mario_unsupported(a4)
.r:     rts

;----------------------------------------------------------------------
; --- mario_D7E4 --- (mario.c mario_D7E4, CODE_00D7E4: gravedad)
; entrada:  a4 = datos del C
; salida:   como mario_D7E4()
; registros destruidos: d0-d1/a0 (ABI de vbcc)
; ciclos:   tools/l_funcs.py
;----------------------------------------------------------------------
        public  _mario_D7E4
_mario_D7E4:
        tst.b   _ram+wm_CapeGlidePhase(a4)
        bne.s   .cape                       ; CODE_00D824
        tst.b   _ram+wm_IsFlying(a4)
        beq.s   .d928
        move.b  _ram+wm_IsCarrying2(a4),d0
        or.b    _ram+wm_OnYoshi(a4),d0
        or.b    _ram+wm_IsSpinJump(a4),d0
        bne.s   .d8cd
        move.b  _ram+wm_PlayerSlopePose(a4),d0
        beq.s   .z
        bpl.s   .d8cd
.z:     clr.b   _ram+wm_PlayerSlopePose(a4)
        cmp.b   #$02,_ram+wm_MarioPowerUp(a4)
        bne.s   .d8cd
        tst.b   _ram+wm_MarioSpeedY(a4)
        bmi.s   .d8cd
        tst.b   _ram+wm_GlideTimer(a4)
        bne.s   .cape                       ; CODE_00D814
.d8cd:  tst.b   _ram+wm_OnYoshi(a4)         ; CODE_00D8CD (IsFlying != 0)
        beq.s   .e7
        move.b  _ram+wm_YoshiHasWings(a4),d0
        lsr.b   #1,d0
        beq.s   .e7
        moveq   #MARIO_UNSUP_YOSHI,d0
        move.l  d0,_mario_unsupported(a4)
        rts
.e7:    cmp.b   #$02,_ram+wm_MarioPowerUp(a4)   ; CODE_00D8E7
        bne.s   .d928
.cape:  moveq   #MARIO_UNSUP_CAPE,d0
        move.l  d0,_mario_unsupported(a4)
        rts
.d928:  moveq   #0,d1                       ; _00D928: B apretado, gravedad menor
        tst.b   _ram+wm_JoyPadA(a4)
        bpl.s   .y
        moveq   #1,d1
.y:     move.b  _ram+wm_MarioSpeedY(a4),d0
        bmi.s   .d948
        lea     _rom00+(DATA_00D7AF-ROM00_BASE)(a4),a0
        cmp.b   (a0,d1.w),d0
        blo.s   .c
        move.b  (a0,d1.w),d0
.c:     cmp.b   #$0b,_ram+wm_IsFlying(a4)
        bne.s   .d948
        move.b  #$24,_ram+wm_IsFlying(a4)
.d948:  lea     _rom00+(DATA_00D7A5-ROM00_BASE)(a4),a0
        add.b   (a0,d1.w),d0
        move.b  d0,_ram+wm_MarioSpeedY(a4)
        rts

;----------------------------------------------------------------------
; --- mario_CEB1 --- (G5L-R-L2: manim.c mario_CEB1, CODE_00CEB1: la capa
; y la pose de Mario)
; entrada:  a4 = datos del C
; salida:   como mario_CEB1()
; registros destruidos: d0-d1/a0 (ABI de vbcc)
; se conservan d2-d3
; ciclos:   tools/l_funcs.py
; x en d2 y y en d3 (bytes con los bits altos en 0).
;----------------------------------------------------------------------
        public  _mario_CEB1
_mario_CEB1:
        movem.l d2-d3,-(sp)
        tst.b   _ram+wm_CapeWaveTimer(a4)
        bne     .w14a2
        moveq   #0,d2
        move.b  _ram+wm_CapeImage(a4),d2    ; x
        moveq   #0,d3
        move.b  _ram+wm_IsFlying(a4),d0
        beq.s   .gr                         ; "MarioAnimAir"
        moveq   #$04,d3                     ; y
        tst.b   _ram+wm_MarioSpeedY(a4)
        bmi.s   .neg
        addq.b  #1,d2                       ; CODE_00CECD
        cmp.b   #$05,d2
        bhs.s   .h
        moveq   #$05,d2
        bra.s   .cf0a
.h:     cmp.b   #$0b,d2
        blo.s   .cf0a
        moveq   #$07,d2
        bra.s   .cf0a
.neg:   cmp.b   #$0c,d0
        beq.s   .cefd
        tst.b   _ram+wm_IsSwimming(a4)
        bne.s   .cefd
        bra.s   .nw
.gr:    move.b  _ram+wm_MarioSpeedX(a4),d0
        bne.s   .cef0
        moveq   #$08,d3
.nw:    tst.b   d2
        beq.s   .cf0a
        subq.b  #1,d2
        cmp.b   #$03,d2
        blo.s   .cf0a
        moveq   #$02,d2
        bra.s   .cf0a
.cef0:  bpl.s   .p
        neg.b   d0
.p:     moveq   #0,d1
        move.b  d0,d1
        lsr.b   #3,d1
        lea     _rom00+(DATA_00DC7C-ROM00_BASE)(a4),a0
        move.b  (a0,d1.w),d3
.cefd:  addq.b  #1,d2
        cmp.b   #$03,d2
        bhs.s   .c1
        moveq   #$05,d2
.c1:    cmp.b   #$07,d2
        blo.s   .cf0a
        moveq   #$03,d2
.cf0a:  move.b  d2,_ram+wm_CapeImage(a4)
        move.b  d3,d0
        tst.b   _ram+wm_IsSwimming(a4)
        beq.s   .sw
        add.b   d0,d0
.sw:    move.b  d0,_ram+wm_CapeWaveTimer(a4)

.w14a2: move.b  _ram+wm_IsSpinJump(a4),d0
        or.b    _ram+wm_CapeSpinTimer(a4),d0
        beq.s   .cf4e
        clr.b   _ram+wm_IsDucking(a4)
        moveq   #$06,d2
        and.b   _ram+wm_FrameB(a4),d2       ; x
        move.w  d2,d3                       ; y
        tst.b   _ram+wm_IsFlying(a4)
        beq.s   .y
        tst.b   _ram+wm_MarioSpeedY(a4)
        bmi.s   .y
        addq.b  #1,d3
.y:     lea     _rom00+(DATA_00CEA9-ROM00_BASE)(a4),a0
        move.b  (a0,d3.w),_ram+wm_CapeImage(a4)
        tst.b   _ram+wm_MarioPowerUp(a4)
        beq.s   .x
        addq.b  #1,d2
.x:     lea     _rom00+(DATA_00CEA1-ROM00_BASE)(a4),a0
        move.b  (a0,d2.w),_ram+wm_MarioDirection(a4)
        cmp.b   #$02,_ram+wm_MarioPowerUp(a4)
        bne.s   .ok
        tst.l   _mario_unsupported(a4)      ; CODE_00D044: unsup_anim
        bne     .ret
        moveq   #MARIO_UNSUP_CAPE,d0
        move.l  d0,_mario_unsupported(a4)
        bra     .ret
.ok:    lea     _rom00+(DATA_00CE99-ROM00_BASE)(a4),a0
        move.b  (a0,d2.w),d0
        bra     .d01a

.cf4e:  move.b  _ram+wm_PlayerSlopePose(a4),d0  ; CODE_00CF4E
        beq.s   .cf62
        bpl     .d01a
        moveq   #0,d1
        move.b  _ram+wm_OnSlopeTypeB(a4),d1
        lsr.b   #2,d1
        or.b    _ram+wm_MarioDirection(a4),d1
        lea     _rom00+(DATA_00CE79+6-ROM00_BASE)(a4),a0
        move.b  (a0,d1.w),d0
        bra     .d01a
.cf62:  moveq   #$3c,d0                     ; CODE_00CF62
        tst.b   _ram+wm_IsCarrying2(a4)
        beq.s   .ca
        moveq   #$1d,d0
.ca:    tst.b   _ram+wm_IsDucking(a4)
        bne     .d01a
        tst.b   _ram+wm_FireballImgTimer(a4)
        beq.s   .k
        moveq   #$3f,d0
        tst.b   _ram+wm_IsFlying(a4)
        beq     .d01a
        moveq   #$16,d0
        bra     .d01a
.k:     moveq   #$0e,d0                     ; CODE_00CF7E
        tst.b   _ram+wm_KickImgTimer(a4)
        bne     .d01a
        moveq   #$1d,d0                     ; CODE_00CF88
        tst.b   _ram+wm_PickUpImgTimer(a4)
        bne     .d01a
        moveq   #$0f,d0
        tst.b   _ram+wm_FaceCamImgTimer(a4)
        bne     .d01a
        moveq   #0,d0
        tst.b   _ram+wm_IsInLakituCloud(a4)
        bne.s   .noabs
        move.b  _ram+wm_IsFlying(a4),d0
        beq.s   .cfb7
        tst.b   _ram+wm_RunCapeTimer(a4)
        bne.s   .cfbc
        moveq   #0,d1
        move.b  _ram+wm_CapeGlidePhase(a4),d1
        beq.s   .c9
        lea     _rom00+(DATA_00CE79-1-ROM00_BASE)(a4),a0
        move.b  (a0,d1.w),d0
.c9:    tst.b   _ram+wm_IsCarrying2(a4)
        beq     .d01a
        moveq   #$09,d0
        bra     .d01a                       ; en el aire: la pose es $72
.cfb7:  move.b  _ram+wm_PlayerTurningPose(a4),d0    ; CODE_00CFB7
        bne     .d01a
.cfbc:  move.b  _ram+wm_MarioSpeedX(a4),d0
        bpl.s   .noabs
        neg.b   d0
.noabs: moveq   #0,d2
        move.b  d0,d2                       ; x
        bne.s   .cfd4
        btst    #3,_ram+wm_JoyPadA(a4)      ; parado: mirar arriba
        beq.s   .z
        move.b  #$03,_ram+wm_OWCreditsPose(a4)
.z:     moveq   #0,d0
        bra.s   .pp
.cfd4:  tst.b   _ram+wm_IsSlipperyLevel(a4) ; CODE_00CFD4
        beq.s   .ns
        moveq   #$03,d1
        and.b   _ram+wm_JoyPadA(a4),d1
        bne.s   .s68
        moveq   #0,d0
        bra.s   .pp
.s68:   move.b  #$68,_ram+wm_PlayerFrameIndex(a4)
.ns:    move.b  _ram+wm_PlayerWalkPose(a4),d0
        tst.b   _ram+wm_PlayerAnimTimer(a4)
        bne.s   .pp
        subq.b  #1,d0
        bpl.s   .b
        moveq   #0,d1
        move.b  _ram+wm_MarioPowerUp(a4),d1
        lea     _rom00+(DATA_00DC7C-4-ROM00_BASE)(a4),a0    ; NumWalkingFrames
        move.b  (a0,d1.w),d0
.b:     moveq   #0,d1
        move.b  d2,d1
        lsr.b   #3,d1
        or.b    _ram+wm_PlayerFrameIndex(a4),d1
        lea     _rom00+(DATA_00DC7C-ROM00_BASE)(a4),a0
        move.b  (a0,d1.w),_ram+wm_PlayerAnimTimer(a4)
.pp:    move.b  d0,_ram+wm_PlayerWalkPose(a4)
        add.b   _ram+wm_OWCreditsPose(a4),d0
        tst.b   _ram+wm_IsCarrying2(a4)
        beq.s   .nc
        addq.b  #7,d0
        bra.s   .d01a
.nc:    cmp.b   #$2f,d2
        blo.s   .d01a
        addq.b  #4,d0                       ; ADC #$03 con acarreo
.d01a:  move.b  _ram+wm_WallWalkStatus(a4),d1
        beq.s   .f
        moveq   #$01,d3
        and.b   d1,d3
        move.b  d3,_ram+wm_MarioDirection(a4)
        moveq   #$10,d0
        cmp.b   #$06,d1
        blo.s   .f
        move.b  _ram+wm_PlayerWalkPose(a4),d0
        add.b   #$11,d0
.f:     move.b  d0,_ram+wm_MarioFrame(a4)
.ret:   movem.l (sp)+,d2-d3
        rts


;----------------------------------------------------------------------
; G5L-R-L2 (2): la carga de sprites por columna, los bloques que rebotan,
; la zona muerta de L/R, los tweakers y la Banzai. Al final del fichero
; para no alejar nada mas del C (P102): el C que las llama (raro) entra
; por los puentes de pic68k.s.
;----------------------------------------------------------------------

; --- sprite_load_level ---
; entrada:  a4 = datos del C
; salida:   como sprite_load_level de msprite.c (LoadSprFromLevel, nivel
;           horizontal): spr_spawned = 0 y, un frame si y otro no, la columna
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
; Recorre la pantalla que entra sin escribir nada; si hay un sprite que
; crear (o hay que rearmar sll_y/sll_i) salta a load_column (C), que
; vuelve a recorrer lo mismo desde el principio y lo crea.
        public  _sprite_load_level
_sprite_load_level:
        clr.b   _spr_spawned(a4)
        btst    #0,_ram+wm_FrameA(a4)
        bne     .ret
        movem.l d2-d5,-(sp)
        moveq   #0,d1
        move.b  _ram+wm_Layer1ScrollDir(a4),d1  ; d
        lea     tx_02A7F6(pc),a0
        moveq   #0,d0
        move.b  (a0,d1.w),d0
        moveq   #0,d2
        move.b  _ram+wm_Bg1HOfs(a4),d2
        add.w   d0,d2                       ; c = Bg1HOfs bajo + DATA_02A7F6[d]
        moveq   #-$10,d3
        and.b   d2,d3                       ; col
        lsr.w   #8,d2                       ; el acarreo de c
        lea     tx_02A7F9(pc),a0
        add.b   (a0,d1.w),d2
        add.b   _ram+wm_Bg1HOfs+1(a4),d2    ; scrn
        bmi.s   .out
        move.l  _spr_level(a4),a1
        cmp.l   _sll_for(a4),a1
        bne.s   .c                          ; sll_y/sll_i viejas: las rearma el C
        moveq   #0,d0
        move.b  d2,d0
        cmp.b   #32,d0
        bls.s   .s
        moveq   #32,d0
.s:     lea     _sll_y(a4),a0
        moveq   #0,d1
        move.b  (a0,d0.w),d1                ; y
        lea     _sll_i(a4),a0
        moveq   #0,d4
        move.b  (a0,d0.w),d4                ; index
        lea     _ram+wm_SprLoadStatus(a4),a0
.lp:    move.b  (a1,d1.w),d0                ; b0
        cmp.b   #$ff,d0
        beq.s   .out
        lsl.b   #3,d0
        and.b   #$10,d0
        moveq   #$0f,d5
        and.b   1(a1,d1.w),d5
        or.b    d5,d0                       ; scr
        cmp.b   d2,d0
        blo.s   .nx                         ; de una pantalla anterior
        bne.s   .out                        ; ordenados por pantalla
        moveq   #-$10,d0
        and.b   1(a1,d1.w),d0
        cmp.b   d3,d0
        bne.s   .nx                         ; otra columna
        tst.b   (a0,d4.w)
        beq.s   .c                          ; sin cargar: lo crea el C
.nx:    addq.b  #3,d1
        addq.b  #1,d4
        bra.s   .lp
.c:     movem.l (sp)+,d2-d5
        PICJUMP _load_column
.out:   movem.l (sp)+,d2-d5
.ret:   rts

; --- blocks_update ---
; entrada:  a4 = datos del C
; salida:   como blocks_update de mcoll.c (CODE_02902D)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
; Sin bloques que rebotan (lo normal) solo baja el temporizador de los
; bloques de varias monedas; si no, todo lo hace el C (blocks_update_c).
        public  _blocks_update
_blocks_update:
        lea     _ram+wm_BounceSprNum(a4),a0
        move.b  (a0)+,d0
        or.b    (a0)+,d0
        or.b    (a0)+,d0
        or.b    (a0),d0
        beq.s   .t
        PICJUMP _blocks_update_c
.t:     cmp.b   #2,_ram+wm_MultiCoinBlkTimer(a4)
        blo.s   .r
        tst.b   _ram+wm_SpritesLocked(a4)
        bne.s   .r
        subq.b  #1,_ram+wm_MultiCoinBlkTimer(a4)
.r:     rts

; --- f8ab ---
; entrada:  a4 = datos del C; m2 = desplazamiento de la camara (16 bits)
; salida:   como f8ab de mcam.c (CODE_00F8AB): m2 y LRMoveCamera
; registros destruidos: d0-d1/a0
; ciclos:   tools/l_funcs.py
        public  _f8ab
_f8ab:
        tst.b   _ram+wm_LRScrollFlag(a4)
        bne.s   .ret
        movem.l d2-d3,-(sp)
        moveq   #0,d1
        move.b  _ram+wm_LRScrollStop(a4),d1     ; x
        lea     _rom00+(DATA_00F6B3-ROM00_BASE)(a4),a0
        move.b  1(a0,d1.w),d0
        lsl.w   #8,d0
        move.b  (a0,d1.w),d0                ; T16X(DATA_00F6B3, x)
        move.w  _ram+wm_PosToScrollScreen(a4),d2
        ror.w   #8,d2
        moveq   #8,d3                       ; y
        sub.w   d0,d2
        bpl.s   .y
        moveq   #$0a,d3
.y:     move.w  _ram+m2(a4),d2
        ror.w   #8,d2                       ; v2
        lea     _rom00+(DATA_00F6BF-ROM00_BASE)(a4),a0
        move.b  1(a0,d3.w),d0
        lsl.w   #8,d0
        eor.w   d2,d0                       ; signos de T16X(F6BF, y) y v2
        bpl.s   .out
        move.b  1(a0,d1.w),d0
        lsl.w   #8,d0
        eor.w   d2,d0                       ; signos de T16X(F6BF, x) y v2
        bpl.s   .out
        lea     _rom00+(DATA_00F6CF-ROM00_BASE)(a4),a0
        move.b  1(a0,d3.w),d0
        lsl.w   #8,d0
        move.b  (a0,d3.w),d0
        add.w   d2,d0                       ; a = v2 + T16X(DATA_00F6CF, y)
        beq.s   .out
        ror.w   #8,d0
        move.w  d0,_ram+m2(a4)
        move.b  d3,_ram+wm_LRMoveCamera(a4)
.out:   movem.l (sp)+,d2-d3
.ret:   rts

; --- sprite_tweakers ---
; entrada:  pila vbcc = u8 x; a4 = datos del C
; salida:   como sprite_tweakers de msprite.c (los seis Tweaker del numero)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
        public  _sprite_tweakers
_sprite_tweakers:
        moveq   #0,d1
        move.b  7(sp),d1
        lea     _ram(a4),a1
        add.w   d1,a1
        moveq   #0,d0
        move.b  wm_SpriteNum(a1),d0
        lea     tx_1656(pc),a0
        move.b  (a0,d0.w),wm_Tweaker1656(a1)
        lea     tx_1662(pc),a0
        move.b  (a0,d0.w),wm_Tweaker1662(a1)
        lea     tx_166E(pc),a0
        move.b  (a0,d0.w),wm_Tweaker166E(a1)
        lea     tx_167A(pc),a0
        move.b  (a0,d0.w),wm_Tweaker167A(a1)
        lea     tx_1686(pc),a0
        move.b  (a0,d0.w),wm_Tweaker1686(a1)
        lea     tx_190F(pc),a0
        move.b  (a0,d0.w),wm_Tweaker190F(a1)
        rts

; --- banzai_bill ---
; entrada:  pila vbcc = u8 x; a4 = datos del C
; salida:   como banzai_bill de msprite.c (BanzaiRotating, el $9F, con SPR_OAM)
; registros destruidos: d0-d1/a0-a1
; ciclos:   tools/l_funcs.py
; Las rutinas que llama son asm y no tocan su ranura de argumento: se
; reusa la misma para todas.
        ifd     SPR_OAM
        public  _banzai_bill
_banzai_bill:
        move.l  d2,-(sp)
        moveq   #0,d2
        move.b  8+3(sp),d2                  ; x
        move.l  d2,-(sp)
        bsr     _banzai_gfx
        lea     _ram+wm_SpriteStatus(a4),a0
        cmp.b   #$02,(a0,d2.w)
        beq.s   .ret
        tst.b   _ram+wm_SpritesLocked(a4)
        bne.s   .ret
        bsr     _sub_offscreen3
        lea     _ram+wm_SpriteSpeedX(a4),a0
        move.b  #$e8,(a0,d2.w)
        pea     $0c.w
        move.l  d2,-(sp)
        bsr     _spr_pos_axis_asm           ; UpdateXPosNoGrvty2
        addq.l  #8,sp
        bsr     _mario_spr_interact         ; DefaultInteractR
.ret:   addq.l  #4,sp
        move.l  (sp)+,d2
        rts
        endc

