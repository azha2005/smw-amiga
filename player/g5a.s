; G5a descartable: caso fijo de OAM, no asignador final G4/G5.
; Solo lo incluye el generador tools/g5a.py en fuentes dentro de work/.

; --- g5a_init ---
; entrada: a6 = Exec; banco base validado offline
; salida: g5a_chip = copia chip inmutable
; registros destruidos: ninguno
; ciclos: carga inicial, fuera del frame
g5a_init:
        movem.l d0-d2/a0-a1,-(sp)
        move.l  #10840,d0
        move.l  #MEMF_CHIP,d1
        jsr     _LVOAllocMem(a6)
        tst.l   d0
        beq     gfail
        lea     g5a_chip(pc),a0
        move.l  d0,(a0)
        move.l  d0,a1
        GETBASE a0
        add.l   #g5a_dma-binstart,a0
        move.w  #10840/4-1,d0
.copy:  move.l  (a0)+,(a1)+
        dbf     d0,.copy
        movem.l (sp)+,d0-d2/a0-a1
        rts

; --- g5a_emit ---
; entrada: a0 = salida copper, d2 = linea, a5 = vars (build_copper)
; salida: a0 avanzado; g5a_slots conserva las posiciones por lista
; registros destruidos: ninguno excepto a0
; ciclos: inicializacion de listas, fuera de medida por frame
g5a_emit:
        movem.l d0-d1/d3/a1-a2,-(sp)
        lea     g5a_slots_a(pc),a1
        move.l  a0,d0                      ; build_copper aun no fijo V_BACK
        sub.l   V_COP(a5),d0
        cmp.l   #CL_SIZE,d0
        blo.s   .slot
        lea     g5a_slots_b(pc),a1
.slot:  move.w  d2,d0
        lsl.w   #2,d0
        move.l  a0,(a1,d0.w)
        ifnd    G5A_EMPTY
        cmp.w   #157,d2
        bne.s   .normal
        move.l  #$c941fffe,(a0)+            ; linea201, h40: despues de DMA SPR7
        move.w  #$0130,d0
        moveq   #7,d1
.ireg:  move.w  d0,(a0)+
        clr.w   (a0)+
        addq.w  #2,d0
        dbf     d1,.ireg
        lea     g5a_controls(pc),a1
        moveq   #7,d1
.ictl:  move.l  (a1)+,(a0)+
        dbf     d1,.ictl
.normal:
        endc
        lea     g5a_offsets(pc),a1
        move.w  d2,d0
        add.w   d0,d0
        moveq   #0,d1
        move.w  (a1,d0.w),d1
        lea     g5a_rows(pc),a1
        add.w   d1,a1
        move.w  (a1)+,d1
        ifd     G5A_EMPTY
        moveq   #0,d1
        endc
        beq.s   .done
        subq.w  #1,d1
.emit:  move.l  (a1)+,(a0)+
        dbf     d1,.emit
.done:  movem.l (sp)+,d0-d1/d3/a1-a2
        rts

; --- g5a_apply ---
; entrada: a5 = vars; V_BACK privada, despues de dc_hdr y build_mid
; salida: PT completo al DATA inmutable y POS/CTL en linea157 h40;
;         mapas por fila junto al borrado de build_mid
; registros destruidos: d0-d1/a0-a1 (resto preservado)
; ciclos: CIA-B dentro del intervalo build_mid del arnes; ver informe
g5a_apply:
        ifd     G5A_EMPTY
        rts
        endc
        movem.l d2-d7/a2-a3,-(sp)
        move.l  V_BACK(a5),a0
        lea     g5a_slots_a(pc),a3
        cmp.l   V_COP(a5),a0
        beq.s   .init
        lea     g5a_slots_b(pc),a3
.init:  move.l  157*4(a3),a0
        lea     6(a0),a1
        lea     g5a_streams(pc),a2
        moveq   #4-1,d3
.pt:    move.l  g5a_chip(pc),d2
        add.l   (a2)+,d2
        addq.l  #4,d2                      ; canal detenido: puntero al DATA
        ifd     G5A_NODMA
        move.l  g_null(pc),d2
        endc
        swap    d2
        move.w  d2,(a1)
        swap    d2
        move.w  d2,4(a1)
        addq.l  #8,a1
        dbf     d3,.pt
        lea     36(a0),a1
        lea     g5a_controls(pc),a2
        moveq   #8-1,d3
.ctl:   move.l  (a2)+,(a1)+
        dbf     d3,.ctl
.rows:  lea     g5a_jobs(pc),a2
        move.w  (a2)+,d3
        subq.w  #1,d3
.row:   move.w  (a2)+,d0
        lsl.w   #2,d0
        move.l  (a3,d0.w),a1
        move.w  (a2)+,d1
        moveq   #0,d0
        move.w  (a2)+,d0
        lea     g5a_rows(pc),a0
        add.w   d0,a0
        addq.l  #2,a0
        subq.w  #1,d1
.color: move.l  (a0)+,(a1)+
        dbf     d1,.color
        dbf     d3,.row
        movem.l (sp)+,d2-d7/a2-a3
        rts

        even
g5a_chip: dc.l 0
g5a_slots_a: ds.l 224
g5a_slots_b: ds.l 224
        include "work/g5a/data.i"
        even
