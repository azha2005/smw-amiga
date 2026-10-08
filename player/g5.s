; Cpre C2b: medir la validacion obligatoria antes de emitir sprites.
        ifnd G5_PRE_PROBE
        fail "Cpre C2b parcial: requiere G5_PRE_PROBE, no hay emisor completo"
        endc
; --- g5_emit --- prototipo de consulta y firmas C2b
; entrada: d7.w = foto, a5 = vars, a4 = CUSTOM; tabla G5PR v1.
; salida: d0 = 0 firmas validas/sin plan, 1 firma invalida; lista intacta.
; registros destruidos: d0/d1/a0/a1; preserva d2-d7/a2-a6 (ABI vbcc).
; ciclos: tools/g2t_emitprobe.py, sobre todos los prefijos reales.
g5_emit:
        movem.l d2-d7/a2-a6,-(sp)
        move.w  d7,d0
        mulu    #DC_REC,d0
        GETBASE a0
        add.l   #dc_rec-binstart,a0
        adda.w  d0,a0                      ; 0..2 registros, P40
        moveq   #0,d7
        move.w  R_FRAME(a0),d7
        ifd G5_PRE_EXT
        move.l  g5_pre(pc),a0
        else
        lea     g5_pre_table(pc),a0
        endc
        move.l  a0,d0
        beq.w   .good
        cmpi.l  #$47355052,(a0)            ; G5PR
        bne.w   .bad
        cmpi.w  #1,4(a0)
        bne.w   .bad
        moveq   #0,d2
        moveq   #0,d3
        move.w  6(a0),d3
        subq.w  #1,d3
        bmi.w   .good
.search:
        cmp.w   d3,d2
        bhi.w   .good
        move.w  d2,d5
        add.w   d3,d5
        lsr.w   #1,d5
        moveq   #0,d0
        move.w  d5,d0
        lsl.l   #3,d0
        lea     8(a0),a1
        adda.l  d0,a1
        cmp.l   (a1),d7
        beq.s   .found
        bhi.s   .higher
        move.w  d5,d3
        subq.w  #1,d3
        bmi.w   .good
        bra.s   .search
.higher:
        move.w  d5,d2
        addq.w  #1,d2
        bra.s   .search
.found:
        move.l  4(a1),d0
        adda.l  d0,a0
        lea     46(a0),a0                 ; B1: cabecera + cuatro canales
        moveq   #0,d0
        move.b  (a0)+,d0                  ; nvbl
        mulu    #3,d0
        adda.w  d0,a0
        moveq   #0,d6
        move.b  (a0)+,d6                  ; nseg
        subq.w  #1,d6
        bmi.w   .good
        move.l  a0,a2                     ; registros de sufijo B1
        move.l  a0,a3
        move.w  d6,d3
.locate:
        moveq   #0,d0
        move.b  4(a3),d0
        mulu    #3,d0
        lea     5(a3),a3
        adda.w  d0,a3
        dbf     d3,.locate                ; a3 = firmas, posiblemente impar
.row:
        moveq   #0,d2
        move.b  (a2),d2
        cmp.w   #224,d2
        bhs.w   .bad
        cmp.w   #255-$2c,d2
        beq.w   .bad                      ; nunca segmento 211
        moveq   #0,d5
        move.b  (a3)+,d5
        cmp.w   d2,d5
        bne.w   .bad
        move.b  (a3)+,d5                  ; u16 BE sin acceso impar
        lsl.w   #8,d5
        move.b  (a3)+,d5
        lsl.l   #8,d2                     ; SEG=256, offset unsigned
        move.l  V_BACK(a5),a1
        adda.l  #CL_LINES,a1
        adda.l  d2,a1                     ; P40: ultima fila pasa de 32767
        moveq   #0,d7
        moveq   #(SEG-12)/4-1,d4
.sum:
        move.w  (a1)+,d0
        cmp.w   #$0084,d0
        beq.s   .compare
        add.w   d0,d7
        add.w   (a1)+,d7
        dbf     d4,.sum
        bra.s   .bad                      ; segmento sin salto
.compare:
        cmp.w   d5,d7
        bne.s   .bad
        moveq   #0,d0
        move.b  4(a2),d0
        mulu    #3,d0
        lea     5(a2),a2
        adda.w  d0,a2
        dbf     d6,.row
.good:
        moveq   #0,d0
        bra.s   .return
.bad:
        lea     g5_miss(pc),a0
        addq.l  #1,(a0)
        moveq   #1,d0
.return:
        movem.l (sp)+,d2-d7/a2-a6
        rts
        cnop    0,4
g5_pre:     dc.l 0                         ; tabla externa solo en Musashi
g5_miss:    dc.l 0
g5_disable: dc.b 0                         ; reservado para C3, sin usar aun
        even
g5_masks:   ds.b 2*28                      ; historial separado por lista
