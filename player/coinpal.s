; SW-M: la paleta de la moneda viaja con la foto de O5. Los bits 15..12
; de COLORxx no existen en OCS; el bit 15 conserva el origen CGRAM $64.
; Opcional (-DCOINANIM, 2026-10-10): el A/B BENCH en WinUAE da 103 -> 148
; fotos perdidas; sin COINANIM las dos rutinas vuelven enseguida.

; --- coin_prepare --- actualizar las fuentes INI/CHG/MLD de esta foto
; entrada: d0.b = FrameB, a3 = SMWS
; salida: fuentes con el paso de la foto; coin_changed = cambió la fuente
; registros destruidos: d0-d1/a0-a1
; ciclos: medidos por tools/coinpal_verify.py (sin DMA)
coin_prepare:
        ifnd    COINANIM                   ; SW-M opcional: D1 +45 fotos (informe)
        rts                                ; paleta estática (paso 2, $27FF)
        endc
        and.w   #$1c,d0
        lsr.w   #2,d0                       ; paso 0..7, cada cuatro frames
        lea     coin_state(pc),a1
        clr.b   5(a1)
        cmp.b   (a1),d0
        beq.s   .x
        move.b  d0,(a1)
        st      5(a1)
        move.l  a3,a0
        add.l   D_COIN(a3),a0
        add.w   d0,d0
        move.w  (a0,d0.w),d0               ; P40 ok: paso*2 <= 14
        move.w  d0,6(a1)
        move.w  16(a0),d1
        lea     24(a0),a1
        subq.w  #1,d1
        bmi.s   .x
.p:     move.l  a3,a0
        add.l   (a1)+,a0
        move.w  d0,(a0)
        dbf     d1,.p
.x:     rts

; --- coin_list --- reparar palabras animadas de la lista de atrás
; entrada: a3 = SMWS, a5 = vars; después de build_mid, antes de publicar
; salida: paleta de esa lista = paso de la foto
; registros destruidos: d0-d1/a0-a1
; ciclos: medidos por tools/coinpal_verify.py (sin DMA)
coin_list:
        ifnd    COINANIM
        rts
        endc
        movem.l d2-d4/a2-a3,-(sp)
        lea     coin_state(pc),a1
        moveq   #1,d0
        move.l  V_BACK(a5),a2
        cmp.l   V_COP(a5),a2
        bne.s   .b
        lea     linetab_a(pc),a3
        bra.s   .ix
.b:     addq.w  #1,d0
        cmp.l   V_COP2(a5),a2
        bne.s   .c
        lea     linetab_b(pc),a3
        bra.s   .ix
.c:     addq.w  #1,d0
        ifd     CUSHION
        move.l  V_LTC(a5),a3
        endc
.ix:    tst.b   5(a1)
        bne.s   .fix
        move.b  (a1,d0.w),d1               ; P40 ok: índice lista 1..3
        cmp.b   (a1),d1
        beq.s   .x
.fix:   move.b  (a1),(a1,d0.w)             ; P40 ok
        move.w  6(a1),d4                   ; conserva etiqueta de origen
        move.l  g_data(pc),a0
        add.l   D_COIN(a0),a0
        move.w  20(a0),d2                  ; filas afectadas
        move.w  18(a0),d3                  ; palabras del borrado
        moveq   #0,d0
        move.w  16(a0),d0
        lsl.l   #2,d0
        lea     24(a0),a0
        add.l   d0,a0                      ; tabla de filas tras offsets
        move.l  a2,a1
        lea     CL_LINES(a1),a2
        subq.w  #1,d3
        bmi.s   .rows
.ini:   move.l  a2,a1
        add.l   (a0)+,a1
        tst.w   (a1)
        bpl.s   .inext
        move.w  d4,(a1)
.inext: dbf     d3,.ini
.rows:
        subq.w  #1,d2
        bmi.s   .x
.row:   move.w  (a0)+,d0                  ; entrada de linetab (fila*32)
        move.w  28(a3,d0.w),d3             ; P40 ok: fila*32 <= 7136
        beq.s   .rnext
        move.l  (a3,d0.w),a1               ; P40 ok: principio de cargas
        lsr.w   #2,d3
        subq.w  #1,d3
.word:  move.w  (a1)+,d0
        cmp.w   #$0182,d0
        blo.s   .next
        cmp.w   #$018e,d0
        bhi.s   .next
        tst.w   (a1)
        bpl.s   .next
        move.w  d4,(a1)
.next:  addq.l  #2,a1
        dbf     d3,.word
.rnext:
        dbf     d2,.row
.x:     movem.l (sp)+,d2-d4/a2-a3
        rts

        even
coin_state:
        dc.b    $ff,$ff,$ff,$ff,0,0        ; fuente, listas A/B/C, reserva, cambió
        dc.w    0                         ; color 12 bits + etiqueta
