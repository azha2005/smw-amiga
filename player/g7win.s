; G7-3c: paso 3 del productor (g7_fast.window_row y place) en 68000.
; Incluido desde player/g7fast.s salvo con -DG7F_NOWIN.
;
; Por color pendiente (orden: el x0 mas chico primero), prestar un indice
; del terreno que no se usa en el tramo del efecto: carga entre su ultimo
; uso a la izquierda y el efecto (o en el prefijo), restauracion entre el
; efecto y su proximo uso; sus recargas dentro de la ventana pasan a NOP.
; Sin backtracking: cada color prueba a lo sumo siete indices.

WV_SL   equ W_WIN+0     ; .w ranura del prestamo
WV_C    equ W_WIN+2     ; .w color
WV_X0   equ W_WIN+4
WV_X1   equ W_WIN+6
WV_CM   equ W_WIN+8     ; .w candidatos que quedan
WV_R    equ W_WIN+10    ; .w indice probado
WV_K    equ W_WIN+12    ; .w grupo (bucle por partes)
WV_NP   equ W_WIN+14    ; .w grupos del color
PV_REG  equ W_WIN+16    ; place: registro, valor, [lo, hi]
PV_VAL  equ W_WIN+18
PV_LO   equ W_WIN+20
PV_HI   equ W_WIN+22
PV_GAP  equ W_WIN+24    ; hueco probado
PV_T    equ W_WIN+26    ; ranura previa al hueco
PV_QW   equ W_WIN+28    ; x resuelto del WAIT del hueco
PV_XW   equ W_WIN+30    ; x del h del WAIT del hueco
PV_NEED equ W_WIN+32    ; holgura exigida al WAIT
PV_OPEN equ W_WIN+34    ; el hueco es el primero
PV_W1   equ W_WIN+36
WV_LO   equ W_WIN+38    ; ultimo uso < x0 (-1 ninguno)
WV_HI   equ W_WIN+40    ; primer uso > x1 (256 ninguno)
WV_KEY  equ W_WIN+42    ; 8 w ancho de la ventana por indice (hasta W_WIN+58)
PV_SCAN equ W_WIN+58    ; .w 1: el analisis de W_TRY sigue valido (place no lo repite)

; --- g7f_window --- paso 3 (window_row) sobre W_SEG
; entrada:  a6 trabajo (W_CL/W_NCL pendientes, W_CLM, W_USED, W_IDX, W_WANT)
; salida:   d0.l = 0: W_SEG/W_NW y W_OUT de los pendientes; -1 sin plan
;           (W_SEG puede quedar a medias; W_OUT no se toca)
; registros destruidos: d0-d7/a0-a5
g7f_window:
        move.w  W_CLM(a6),d0
        move.w  d0,W_WCLM(a6)
        or.w    W_USED(a6),d0
        not.w   d0
        and.w   #$fe,d0
        move.w  d0,W_SPARE(a6)             ; spare: ni terreno ni efecto
        lea     W_CL(a6),a0
        move.w  W_NCL(a6),d7
        subq.w  #1,d7
.c0:    clr.b   1(a0)                      ; 0 pendiente, 1 tratado
        clr.w   6(a0)
        addq.l  #8,a0
        dbf     d7,.c0
.color: ; el color del grupo sin tratar de x0 minimo
        lea     W_CL(a6),a0
        move.w  W_NCL(a6),d7
        subq.w  #1,d7
        moveq   #0,d2
        move.w  #$7fff,d3
.f:     tst.b   1(a0)
        bne.s   .fn
        cmp.w   2(a0),d3
        ble.s   .fn
        move.w  2(a0),d3
        move.b  (a0),d2
.fn:    addq.l  #8,a0
        dbf     d7,.f
        cmp.w   #$7fff,d3
        beq     .success
        ; x1 maximo y cantidad de grupos del color; marcarlos
        lea     W_CL(a6),a0
        move.w  W_NCL(a6),d7
        subq.w  #1,d7
        move.w  d3,d4
        moveq   #0,d5
.m:     cmp.b   (a0),d2
        bne.s   .mn
        move.b  #1,1(a0)
        addq.w  #1,d5
        cmp.w   4(a0),d4
        bge.s   .mn
        move.w  4(a0),d4
.mn:    addq.l  #8,a0
        dbf     d7,.m
        move.w  d5,WV_NP(a6)
        bsr     g7f_borrow                 ; todo el color con un indice
        tst.w   d0
        beq.s   .parts
        move.w  WV_SL(a6),d2
        lea     W_CL(a6),a0
        move.w  W_NCL(a6),d7
        subq.w  #1,d7
.sr:    cmp.b   (a0),d2
        bne.s   .srn
        move.w  d0,6(a0)
.srn:   addq.l  #8,a0
        dbf     d7,.sr
        bra     .color
.parts: cmp.w   #1,WV_NP(a6)               ; un grupo: la misma prueba otra vez
        beq.s   .fail
        move.w  WV_SL(a6),d2
        clr.w   WV_K(a6)
.p:     move.w  WV_K(a6),d0
        cmp.w   W_NCL(a6),d0
        bhs     .color
        lsl.w   #3,d0
        lea     W_CL(a6),a0
        add.w   d0,a0
        cmp.b   (a0),d2
        bne.s   .pn
        move.w  2(a0),d3
        move.w  4(a0),d4
        move.l  a0,-(sp)
        bsr     g7f_borrow
        move.l  (sp)+,a0
        tst.w   d0
        beq.s   .fail
        move.w  d0,6(a0)
        move.w  WV_SL(a6),d2
.pn:    addq.w  #1,WV_K(a6)
        bra.s   .p
.success:
        lea     W_CL(a6),a2
        move.w  W_NCL(a6),d7
        subq.w  #1,d7
.so:    move.w  6(a2),d0
        moveq   #0,d2
        move.b  (a2),d2
        move.w  2(a2),d3
        move.w  4(a2),d4
        bsr     g7f_setout
        addq.l  #8,a2
        dbf     d7,.so
        moveq   #0,d0
        rts
.fail:  moveq   #-1,d0
        rts

; --- g7f_borrow --- prestar el mejor indice al tramo [x0, x1] de la ranura
; entrada:  d2.w ranura, d3.w x0, d4.w x1
; salida:   d0.w = indice (W_SEG/W_NW actualizados, W_WCLM) o 0
; registros destruidos: d0-d7/a0-a5
g7f_borrow:
        move.w  d2,WV_SL(a6)
        move.w  d3,WV_X0(a6)
        move.w  d4,WV_X1(a6)
        add.w   d2,d2
        lea     W_CT(a6),a0
        move.w  (a0,d2.w),WV_C(a6)
        bsr     g7f_uses
        ; candidatos: reclamado no, usado en la fila si, dentro del tramo no
        lea     WV_KEY(a6),a1
        lea     W_ULO(a6),a2
        lea     W_UHI(a6),a3
        moveq   #0,d5
        moveq   #1,d0
.r:     move.w  W_WCLM(a6),d1
        btst    d0,d1
        bne.s   .rn
        move.w  W_UANY(a6),d1
        btst    d0,d1
        beq.s   .rn
        move.w  W_UIN(a6),d1
        btst    d0,d1
        bne.s   .rn
        move.w  d0,d6
        add.w   d6,d6
        move.w  WV_X0(a6),d7
        move.w  (a2,d6.w),d1
        bmi.s   .lnone
        sub.w   d1,d7
        subq.w  #1,d7                      ; x0 - lo (lo = ultimo uso + 1)
.lnone: move.w  (a3,d6.w),d1
        cmp.w   #256,d1
        bne.s   .hset
        add.w   #256,d7
        bra.s   .key
.hset:  add.w   d1,d7
        sub.w   WV_X1(a6),d7
.key:   move.w  d7,(a1,d6.w)
        bset    d0,d5
.rn:    addq.w  #1,d0
        cmp.w   #8,d0
        blo.s   .r
        move.w  d5,WV_CM(a6)
.pick:  move.w  WV_CM(a6),d5
        beq.s   .none
        lea     WV_KEY(a6),a1
        moveq   #0,d1
        move.w  #-32768,d7
        moveq   #1,d0
.pk:    btst    d0,d5
        beq.s   .pkn
        move.w  d0,d6
        add.w   d6,d6
        cmp.w   (a1,d6.w),d7
        bge.s   .pkn                       ; a igual ancho, el r menor
        move.w  (a1,d6.w),d7
        move.w  d0,d1
.pkn:   addq.w  #1,d0
        cmp.w   #8,d0
        blo.s   .pk
        bclr    d1,d5
        move.w  d5,WV_CM(a6)
        move.w  d1,WV_R(a6)
        bsr     g7f_wtry
        tst.w   d0
        beq.s   .pick
        move.w  WV_R(a6),d0
        move.w  W_WCLM(a6),d1
        bset    d0,d1
        move.w  d1,W_WCLM(a6)
        lea     W_TRY(a6),a0
        lea     W_SEG(a6),a1
        move.w  W_NT(a6),d1
        move.w  d1,W_NW(a6)
        subq.w  #1,d1
.cp:    move.l  (a0)+,(a1)+
        dbf     d1,.cp
        rts                                ; d0 = r
.none:  moveq   #0,d0
        rts

; --- g7f_wtry --- un candidato: NOP en la ventana, carga y restauracion
; entrada:  WV_R, WV_C, WV_X0/X1, W_ULO/W_UHI de g7f_uses, W_SEG
; salida:   d0.w = 1 (W_TRY/W_NT con el prestamo) o 0
; registros destruidos: d0-d7/a0-a5
g7f_wtry:
        clr.w   PV_SCAN(a6)
        move.w  WV_R(a6),d0
        add.w   d0,d0
        lea     W_ULO(a6),a0
        move.w  (a0,d0.w),WV_LO(a6)
        lea     W_UHI(a6),a0
        move.w  (a0,d0.w),WV_HI(a6)
        add.w   #$180,d0
        move.w  d0,PV_REG(a6)
        lea     W_SEG(a6),a0
        move.w  W_NW(a6),d0
        bsr     g7f_scan                   ; posiciones de new
        lea     W_SEG(a6),a0
        lea     W_TRY(a6),a1
        move.w  W_NW(a6),d1
        move.w  d1,W_NT(a6)
        subq.w  #1,d1
.cp:    move.l  (a0)+,(a1)+
        dbf     d1,.cp
        ; recargas del indice dentro de la ventana -> NOP
        lea     W_TRY(a6),a1
        lea     W_POS(a6),a2
        move.w  PV_REG(a6),d2
        move.w  WV_LO(a6),d3
        move.w  WV_HI(a6),d4
        move.w  W_NT(a6),d7
        subq.w  #1,d7
.nop:   move.w  (a2)+,d0
        cmp.w   #$8000,d0
        beq.s   .nn
        cmp.w   (a1),d2
        bne.s   .nn
        tst.w   d3
        bmi.s   .nl                        ; sin uso a la izquierda: sin cota
        cmp.w   d3,d0
        ble.s   .nn                        ; x < ultimo uso + 1
.nl:    cmp.w   #256,d4
        beq.s   .nk
        cmp.w   d4,d0
        bge.s   .nn
.nk:    move.l  #$01fe0000,(a1)
.nn:    addq.l  #4,a1
        dbf     d7,.nop
        ; carga
        tst.w   WV_LO(a6)
        bpl.s   .place
        lea     W_TRY(a6),a1
        lea     W_POS(a6),a2
        move.w  W_NT(a6),d7
        subq.w  #1,d7
.pre:   cmp.w   #$8000,(a2)+
        bne.s   .pren
        cmp.w   (a1),d2
        beq.s   .preg
.pren:  addq.l  #4,a1
        dbf     d7,.pre
        bra.s   .no
.preg:  move.w  2(a1),d0
        and.w   #$f000,d0
        or.w    WV_C(a6),d0
        move.w  d0,2(a1)
        bra.s   .rest
.place: move.w  #1,PV_SCAN(a6)             ; los NOP no mueven nada: vale el de W_SEG
        move.w  WV_C(a6),PV_VAL(a6)
        move.w  WV_LO(a6),d0
        addq.w  #1,d0
        move.w  d0,PV_LO(a6)
        move.w  WV_X0(a6),PV_HI(a6)
        bsr     g7f_place
        tst.w   d0
        beq.s   .no
.rest:  move.w  WV_HI(a6),d0
        cmp.w   #256,d0
        beq.s   .yes
        move.w  d0,d1
        move.w  WV_R(a6),d0
        bsr     g7f_basecol
        move.w  d0,PV_VAL(a6)              ; base[r, hi]
        move.w  WV_HI(a6),PV_HI(a6)
        move.w  WV_X1(a6),d0
        addq.w  #1,d0
        move.w  d0,PV_LO(a6)
        bsr     g7f_place
        tst.w   d0
        beq.s   .no
.yes:   moveq   #1,d0
        rts
.no:    moveq   #0,d0
        rts

; --- g7f_place --- un MOVE PV_REG,PV_VAL en x de [PV_LO, PV_HI] sobre W_TRY
; sin mover ningun evento (g7_fast.place, forma cerrada)
; entrada:  PV_REG/PV_VAL/PV_LO/PV_HI, W_TRY/W_NT, W_END, W_SPARE
; salida:   d0.w = 1 (W_TRY/W_NT cambiados) o 0
; registros destruidos: d0-d7/a0-a5
g7f_place:
        move.w  PV_HI(a6),d0
        cmp.w   W_END(a6),d0
        ble.s   .h
        move.w  W_END(a6),d0
        move.w  d0,PV_HI(a6)
.h:     cmp.w   PV_LO(a6),d0
        blt     .no
        tst.w   PV_SCAN(a6)
        bne.s   .scanned
        lea     W_TRY(a6),a0
        move.w  W_NT(a6),d0
        bsr     g7f_scan
.scanned:
        clr.w   PV_SCAN(a6)
        ; 1) reusar una ranura: NOP o recarga de un indice sin uso
        lea     W_POS(a6),a1
        lea     W_TRY(a6),a2
        move.w  W_NT(a6),d7
        subq.w  #1,d7
.ru:    move.w  (a1)+,d0
        cmp.w   #$8000,d0
        beq.s   .rn
        cmp.w   PV_LO(a6),d0
        blt.s   .rn
        cmp.w   PV_HI(a6),d0
        bgt.s   .rn
        move.l  (a2),d1
        cmp.l   #$01fe0000,d1
        beq.s   .take
        swap    d1
        cmp.w   #$182,d1
        blo.s   .rn
        cmp.w   #$18e,d1
        bhi.s   .rn
        btst    #0,d1
        bne.s   .rn
        sub.w   #$180,d1
        lsr.w   #1,d1
        move.w  W_SPARE(a6),d2
        btst    d1,d2
        beq.s   .rn
.take:  move.w  PV_REG(a6),(a2)
        move.w  PV_VAL(a6),2(a2)
        moveq   #1,d0
        rts
.rn:    addq.l  #4,a2
        dbf     d7,.ru
        ; ningun MOVE del cuerpo despues del fin permitido
        lea     W_POS(a6),a1
        move.w  W_NT(a6),d7
        subq.w  #1,d7
.ov:    move.w  (a1)+,d0
        cmp.w   W_END(a6),d0
        bgt     .no
        dbf     d7,.ov
        ; 2) insertar delante de un WAIT del cuerpo o al final
        move.w  W_FIRST(a6),d3
.gap:   cmp.w   W_NT(a6),d3
        bhi     .no
        beq.s   .atend
        lea     W_FLG(a6),a0
        btst    #0,(a0,d3.w)
        beq     .gnext
        move.w  d3,d0
        add.w   d0,d0
        lea     W_BEF(a6),a0
        move.w  (a0,d0.w),PV_T(a6)
        lea     W_SLK(a6),a0
        move.w  (a0,d0.w),d5               ; holgura del WAIT
        add.w   d0,d0
        lea     W_TRY(a6),a0
        move.w  (a0,d0.w),PV_W1(a6)
        move.w  PV_T(a6),d0
        move.w  PV_W1(a6),d1
        bsr     g7f_waitx
        move.w  d0,PV_QW(a6)
        move.w  PV_W1(a6),d1
        and.w   #$fe,d1
        move.w  #G7F_XD0,d0
        cmp.w   #$ce,d1
        bhi.s   .xw
        bsr     g7f_xh
.xw:    move.w  d0,PV_XW(a6)
        moveq   #G7F_IDLE,d0
        cmp.w   W_OPEN(a6),d3
        beq.s   .need
        cmp.w   d0,d5
        bge.s   .need
        move.w  d5,d0                      ; min(IDLE, holgura original)
.need:  move.w  d0,PV_NEED(a6)
        bra.s   .body
.atend: move.w  W_TEND(a6),PV_T(a6)
.body:  move.w  d3,PV_GAP(a6)
        clr.w   PV_OPEN(a6)
        cmp.w   W_FIRST(a6),d3
        bne.s   .nop0
        move.w  #1,PV_OPEN(a6)
        bra.s   .waits
.nop0:  ; MOVE detras de n NOP (n < 12): la primera ranura >= lo
        move.w  PV_T(a6),d4
        moveq   #0,d5
.nq:    cmp.w   #12,d5
        bhs.s   .waits
        cmp.w   PV_LO(a6),d4
        blt.s   .nadv
        move.w  d4,d0
        move.w  d5,d1
        addq.w  #1,d1
        bsr     g7f_fits
        tst.w   d0
        beq.s   .waits
        move.w  d5,d0
        addq.w  #1,d0
        bsr     g7f_shift                  ; a0 = &W_TRY[gap]
        bra.s   .nf
.nfl:   move.l  #$01fe0000,(a0)+
.nf:    dbf     d5,.nfl
        move.w  PV_REG(a6),(a0)+
        move.w  PV_VAL(a6),(a0)+
        moveq   #1,d0
        rts
.nadv:  move.w  d4,d0
        bsr     g7f_adv
        move.w  d0,d4
        addq.w  #1,d5
        bra.s   .nq
.waits: ; WAIT h + MOVE, h ascendente (g7f_hx: sin x repetidas seguidas)
        move.w  PV_T(a6),d0
        bsr     g7f_adv
        bsr     g7f_adv
        move.w  d0,d7                      ; adv(t, 2)
        lea     g7f_hx(pc),a3
.hl:    move.w  (a3)+,d6
        bmi.s   .gnext
        move.w  (a3)+,d0
        move.w  d7,d4
        cmp.w   d4,d0
        ble.s   .hx
        move.w  d0,d4
.hx:    cmp.w   PV_LO(a6),d4
        blt.s   .hn
        tst.w   PV_OPEN(a6)
        bne.s   .hf
        move.w  d4,d0
        sub.w   PV_T(a6),d0
        cmp.w   #G7F_IDLE,d0
        blt.s   .hn
.hf:    move.w  d4,d0
        moveq   #2,d1
        bsr     g7f_fits
        tst.w   d0
        beq.s   .hn
        moveq   #2,d0
        bsr     g7f_shift
        move.w  W_ROW(a6),d0
        add.w   #G7F_V0,d0
        lsl.w   #8,d0
        or.w    d6,d0
        or.w    #1,d0
        move.w  d0,(a0)+
        move.w  #$fffe,(a0)+
        move.w  PV_REG(a6),(a0)+
        move.w  PV_VAL(a6),(a0)+
        moveq   #1,d0
        rts
.hn:    bra.s   .hl
.gnext: addq.w  #1,d3
        bra     .gap
.no:    moveq   #0,d0
        rts

; --- g7f_fits --- fits() de place: el MOVE en x deja el WAIT del hueco igual
; entrada:  d0.w x, d1.w palabras insertadas, PV_*
; salida:   d0.w = 1 o 0
; registros destruidos: d0-d1
g7f_fits:
        cmp.w   PV_LO(a6),d0
        blt.s   .no
        cmp.w   PV_HI(a6),d0
        bgt.s   .no
        add.w   W_NT(a6),d1
        addq.w  #3,d1
        cmp.w   #64,d1
        bhi.s   .no
        move.w  PV_GAP(a6),d1
        cmp.w   W_NT(a6),d1
        beq.s   .yes
        bsr     g7f_adv
        move.w  d0,d1                      ; t2
        bsr     g7f_adv
        bsr     g7f_adv
        cmp.w   PV_XW(a6),d0
        bge.s   .q
        move.w  PV_XW(a6),d0               ; q2 = max(adv(t2, 2), xw)
.q:     cmp.w   PV_QW(a6),d0
        bne.s   .no
        sub.w   d1,d0
        cmp.w   PV_NEED(a6),d0
        blt.s   .no
.yes:   moveq   #1,d0
        rts
.no:    moveq   #0,d0
        rts

; --- g7f_shift --- abrir d0 palabras en W_TRY en PV_GAP
; salida:   a0 = &W_TRY[PV_GAP], W_NT += d0
; registros destruidos: d1-d2/a0-a2 (d0 se conserva)
g7f_shift:
        lea     W_TRY(a6),a0
        move.w  W_NT(a6),d1
        move.w  d1,d2
        lsl.w   #2,d2
        lea     (a0,d2.w),a1               ; fin de la fuente
        move.w  d0,d2
        lsl.w   #2,d2
        lea     (a1,d2.w),a2               ; fin del destino
        sub.w   PV_GAP(a6),d1
        bra.s   .t
.m:     move.l  -(a1),-(a2)
.t:     dbf     d1,.m
        add.w   d0,W_NT(a6)
        move.w  PV_GAP(a6),d1
        lsl.w   #2,d1
        add.w   d1,a0
        rts

; --- g7f_basecol --- color del indice d0 en x = d1 con la lista original
; (palette(words)[r, x]: el ultimo evento de r con posicion <= x)
; salida:   d0.w color
; registros destruidos: d0/d2-d3/a0
g7f_basecol:
        move.w  d0,d2
        moveq   #0,d0
        lea     W_EVT(a6),a0
        move.w  W_NEV(a6),d3
        bra.s   .t
.e:     cmp.w   (a0),d1
        blt.s   .out                       ; evento despues de x
        cmp.w   2(a0),d2
        bne.s   .n
        move.w  4(a0),d0
.n:     addq.l  #6,a0
.t:     dbf     d3,.e
.out:   rts

; (h, x del primer MOVE tras WAIT h) de $20 a $ce, sin repetir x seguidas
; (g7_fast.HX: mismo orden de prueba que la especificacion)
g7f_hx:
        dc.w    $20,-81
        dc.w    $24,-73
        dc.w    $28,-65
        dc.w    $2c,-57
        dc.w    $30,-49
        dc.w    $34,-41
        dc.w    $38,-33
        dc.w    $3c,-25
        dc.w    $40,-17
        dc.w    $44,-9
        dc.w    $48,-1
        dc.w    $4c,7
        dc.w    $50,15
        dc.w    $54,23
        dc.w    $58,31
        dc.w    $5c,39
        dc.w    $60,47
        dc.w    $64,55
        dc.w    $68,63
        dc.w    $6c,71
        dc.w    $70,79
        dc.w    $74,87
        dc.w    $78,95
        dc.w    $7c,103
        dc.w    $80,111
        dc.w    $84,119
        dc.w    $88,127
        dc.w    $8c,135
        dc.w    $90,143
        dc.w    $94,151
        dc.w    $98,159
        dc.w    $9c,167
        dc.w    $a0,175
        dc.w    $a4,183
        dc.w    $a8,191
        dc.w    $ac,199
        dc.w    $b0,207
        dc.w    $b4,215
        dc.w    $b8,223
        dc.w    $bc,231
        dc.w    $c0,239
        dc.w    $c2,255
        dc.w    $c4,243
        dc.w    $c8,247
        dc.w    $cc,251
        dc.w    $ce,255
        dc.w    -1
