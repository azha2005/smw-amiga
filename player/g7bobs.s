; G7-3: restauracion y cola de bobs en el PF1 que libero VERTB.
; Solo G7_BOBS. Los descriptores son palabras fisicas, no coordenadas SNES:
; .l destino, 3 .w mascara, 3 .w planos. Una entrada se escribe en las
; dos copias del anillo. La IRQ solo avanza la cola; el render produce.
G7Q_OFF equ 7616+960
G7Q_MAX equ (12288-G7Q_OFF)/16
G7_PACK_OFF equ 9728
G7_SNAP_SIZE equ 8192
BLTCPTR equ $048
BLTBPTR equ $04c
BLTCMODR equ $060
BLTBMODR equ $062

; --- g7b_clean --- reponer exactamente la lista libre anterior a G7
; entrada: a5 scroll, V_BACK libre; antes de apply_colors/build_mid/G5L
; salida: prefijos, eventos y saltos originales; diario de esa lista vacio
; registros destruidos: d0-d1/a0-a1
; ciclos: proporcionales a bytes guardados; solo escribe la lista libre
g7b_clean:
        movem.l d2-d4/a2-a3,-(sp)
        bsr     g7b_list
        lea     g7b_hdr_flag(pc),a2
        tst.b   (a2,d4.w)
        beq.s   .nohdr
        clr.b   (a2,d4.w)
        lea     g7b_hdr(pc),a2
        move.w  d4,d0
        lsl.w   #7,d0
        add.w   d0,a2
        move.l  V_BACK(a5),a3
        adda.l  #CL_VBL,a3
        moveq   #31,d0
.hdr:   move.l  (a2)+,(a3)+
        dbf     d0,.hdr
.nohdr:
        move.w  (a1),d2
        clr.w   (a1)
        move.l  a0,a3
        add.w   d2,a3
.next:  cmpa.l  a3,a0
        bhs.s   .done
        moveq   #0,d0
        move.w  (a0)+,d0                   ; desplazamiento en CL_LINES (fila << 8 + 4 palabra)
        move.l  V_BACK(a5),a2
        adda.l  #CL_LINES,a2
        add.l   d0,a2
        move.w  (a0)+,d1
        subq.w  #1,d1
.copy:  move.l  (a0)+,(a2)+
        dbf     d1,.copy
        bra.s   .next
.done:  lea     g7b_seen(pc),a0
        mulu    #28,d4
        add.w   d4,a0
        moveq   #6,d0
.clear: clr.l   (a0)+
        dbf     d0,.clear
        movem.l (sp)+,d2-d4/a2-a3
        rts

; --- g7b_begin --- conservar tambien los controles DMA del VBL libre
; entrada: a5 scroll; salida: copia privada por lista de CL_VBL
; registros destruidos: d0-d1/a0-a1
; ciclos: ~1200 sin DMA, una vez por intento
g7b_begin:
        movem.l d4/a2,-(sp)
        bsr     g7b_list
        lea     g7b_hdr_flag(pc),a0
        st      (a0,d4.w)
        lsl.w   #7,d4
        lea     g7b_hdr(pc),a1
        add.w   d4,a1
        move.l  V_BACK(a5),a2
        adda.l  #CL_VBL,a2
        moveq   #31,d0
.copy:  move.l  (a2)+,(a1)+
        dbf     d0,.copy
        movem.l (sp)+,d4/a2
        rts

; --- _g7b_retry --- limpiar intento incompleto sin publicar ni soltar foto
; entrada: ABI C; salida: PF1/lista libres restituidos, nuevo diario abierto
; registros destruidos: d0-d1/a0-a1
; ciclos: restauracion y copia, medir por intento
_g7b_retry:
        movem.l a3-a5,-(sp)
.base:  lea     .base(pc),a5
        sub.l   #.base-binstart,a5
        move.l  a5,a3
        adda.l  #g_data-binstart,a3
        move.l  (a3),a3
        adda.l  #vars-binstart,a5
        lea     CUSTOM,a4
        bsr     g7b_restore
        bsr     g7b_clean
        bsr     g7b_begin
        movem.l (sp)+,a3-a5
        rts

; --- g7b_list --- diario exclusivo de V_BACK
; entrada: a5 scroll; salida: a0 diario, a1 cantidad, d4 indice 0..2
; registros destruidos: d0-d1/d4/a0-a1
; ciclos: ~180 sin DMA
g7b_list:
        moveq   #0,d4
        move.l  V_BACK(a5),d0
        cmp.l   V_COP(a5),d0
        beq.s   .slot
        moveq   #1,d4
        cmp.l   V_COP2(a5),d0
        beq.s   .slot
        moveq   #2,d4
.slot:
.base:  lea     .base(pc),a0
        adda.l  #g7b_saved-.base,a0
        move.w  d4,d1
        lsl.w   #1,d1
        lea     g7b_saved_n(pc),a1
        add.w   d1,a1
        move.w  d4,d1
        mulu    #G7_SNAP_SIZE,d1
        add.w   d1,a0                     ; maximo 16384, P40 ok
        rts

; --- _g7b_save_row --- puente ABI: guardar segmento antes de modificarlo
; entrada: 4(sp).l fila; salida: d0 = 0 o 4 (capacidad agotada)
; registros destruidos: d0-d1/a0-a1
; ciclos: 4 B por pareja hasta el salto, sin datos por frame
_g7b_save_row:
        movem.l d2-d5/a2-a5,-(sp)
        move.l  36(sp),d5
.base:  lea     .base(pc),a5
        sub.l   #.base-binstart,a5
        adda.l  #vars-binstart,a5
        bsr     g7b_list
        lea     g7b_seen(pc),a2
        mulu    #28,d4
        add.w   d4,a2
        move.w  d5,d0
        lsr.w   #3,d0
        move.w  d5,d1
        and.w   #7,d1
        btst    d1,(a2,d0.w)
        bne.s   .ok
        move.w  d5,d2
        lsl.l   #8,d2
        move.l  V_BACK(a5),a3
        adda.l  #CL_LINES,a3
        add.l   d2,a3
        moveq   #0,d2
.find:  cmp.w   #$84,(a3,d2.w)
        beq.s   .tail
        addq.w  #4,d2
        cmp.w   #SEG-12,d2
        bls.s   .find
        bra.s   .bad
.tail:  add.w   #12,d2
        move.w  (a1),d3
        add.w   d3,a0
        add.w   d2,d3
        addq.w  #4,d3
        cmp.w   #G7_SNAP_SIZE,d3
        bhi.s   .bad
        move.w  d3,(a1)
        bset    d1,(a2,d0.w)
        move.w  d5,d1
        lsl.w   #8,d1
        move.w  d1,(a0)+                   ; desplazamiento de la fila
        lsr.w   #2,d2
        move.w  d2,(a0)+
        subq.w  #1,d2
.copy:  move.l  (a3)+,(a0)+
        dbf     d2,.copy
.ok:    moveq   #0,d0
        bra.s   .out
.bad:   moveq   #4,d0
.out:   movem.l (sp)+,d2-d5/a2-a5
        rts

; --- _g7b_save_sparse --- guardar palabras sueltas de una fila antes de parcharlas
; entrada: 4(sp).l fila, 8(sp).l lista de indices de palabra (bytes, $ff fin)
; salida: d0 = 0 o 4 (capacidad agotada); un registro de 8 B por palabra
; registros destruidos: d0-d1/a0-a1
; ciclos: ~250 + 60 por palabra
_g7b_save_sparse:
        movem.l d2-d5/a2-a5,-(sp)
        move.l  36(sp),d5
        move.l  40(sp),a2
.base:  lea     .base(pc),a5
        sub.l   #.base-binstart,a5
        adda.l  #vars-binstart,a5
        bsr     g7b_list
        lsl.w   #8,d5                      ; fila en CL_LINES
        move.l  V_BACK(a5),a3
        adda.l  #CL_LINES,a3
        move.w  (a1),d3
.w:     moveq   #0,d2
        move.b  (a2)+,d2
        cmp.b   #$ff,d2
        beq.s   .end
        cmp.w   #G7_SNAP_SIZE-8,d3
        bhi.s   .bad
        lsl.w   #2,d2
        add.w   d5,d2                      ; desplazamiento (sin signo)
        move.w  d2,(a0,d3.w)
        move.w  #1,2(a0,d3.w)
        move.l  (a3,d2.l),4(a0,d3.w)
        addq.w  #8,d3
        bra.s   .w
.end:   move.w  d3,(a1)
        moveq   #0,d0
        bra.s   .out
.bad:   move.w  d3,(a1)                    ; lo guardado se repone igual
        moveq   #4,d0
.out:   movem.l (sp)+,d2-d5/a2-a5
        rts

; --- g7b_load --- leer el banco comprimido directamente en la reserva chip
; entrada: a4 CUSTOM; motor BM todavia encendido, g7_pf1 reservado
; salida: d0=0 o fallo BM; payload temporal fuera de fuentes expandidas
; registros destruidos: d0-d1/a0-a1
; ciclos: lectura de 5 sectores; solo arranque, antes de lectores DMA
g7b_load:
        move.l  g7_pf1(pc),a0
        adda.l  #BUF1,a0
        clr.l   (a0)
        adda.l  #G7_PACK_OFF,a0
.base:  lea     .base(pc),a1
        sub.l   #.base-binstart,a1
        move.l  hdr_data_off-binstart(a1),d0
        add.l   hdr_data_len-binstart(a1),d0
        add.l   #(G5L_CDMA_SIZE+511)&$fffffe00,d0
        lsr.l   #8,d0
        lsr.l   #1,d0
        moveq   #5,d1
        move.l  #BM_READ_ADDR,a1
        jsr     (a1)
        rts

; --- g7b_draw --- producir desde la OAM protegida de DC_REND
; entrada: a3 datos, a4 CUSTOM, a5 scroll; dc_hdr ya preparado
; salida: efectos completos o g7b_error explicito; nunca escribe FRONT
; registros destruidos: ninguno
; ciclos: medir fallos/hits; no hay cache por numero de frame
g7b_draw:
        ifd NOSWS
        rts                               ; sin productor; clean/restore siguen activos
        else
        movem.l d0-d7/a0-a6,-(sp)
        bsr     g7b_wait                    ; leer PF1 solo tras columns/tile_apply
        move.w  dc_st+DC_REND(pc),d0
        move.w  d0,d7
        bsr     dc_recp
        move.b  R_SWS_VALID(a0),d0
        beq.s   .done
        move.l  a0,a2
        bsr     g7b_begin
        move.l  g7b_bank(pc),a1
.cc:    lea     .cc(pc),a0                 ; g7fast.s, al final del binario (P102)
        adda.l  #g7f_render-.cc,a0
        jsr     (a0)
        lea     g7b_error(pc),a0
        move.w  d0,(a0)
.done:  movem.l (sp)+,d0-d7/a0-a6
        rts
        endif

; --- _g7b_send --- puente ABI vbcc: emitir y esperar cola de una fila
; entrada: 4(sp).l cantidad, a4 no reservado por C
; salida: dos copias terminadas, fuente reutilizable
; registros destruidos: d0-d1/a0-a1
; ciclos: coste de submit, IRQ y wait medido por separado
_g7b_send:
        movem.l a3-a5,-(sp)
        move.l  16(sp),d0
.base:  lea     .base(pc),a5
        sub.l   #.base-binstart,a5
        move.l  a5,a3
        adda.l  #g_data-binstart,a3
        move.l  (a3),a3
        adda.l  #vars-binstart,a5
        lea     CUSTOM,a4
        bsr     g7b_submit
        bsr     g7b_wait
        movem.l (sp)+,a3-a5
        rts

; --- g7b_init --- cargar fuentes y vaciar propiedad/cola/suciedad
; entrada: a4 CUSTOM; g7_pf1 ya reservado
; salida: banco G7S1 en chip, ambos mapas de suciedad vacios
; registros destruidos: d0-d1/a0-a1
; ciclos: medir carga; no se ejecuta en cada foto
g7b_init:
        movem.l d2/a2,-(sp)
        bsr     g7b_wait
        move.l  g7_pf1(pc),a1
        adda.l  #BUF1,a1
        lea     g7b_bank(pc),a0
        move.l  a1,(a0)
        cmp.l   #$47375331,(a1)            ; reinicio: banco ya expandido
        beq.s   .ready
        lea     G7_PACK_OFF(a1),a0
        move.w  #4456,d2                   ; cabecera + bytes altos de planos
.decode:
        moveq   #0,d0
        move.b  (a0)+,d0
        bpl.s   .literal
        and.w   #127,d0
        addq.w  #1,d0
        move.b  (a0)+,d1
.run:   bsr.s   .emit
        dbf     d0,.run
        bra.s   .next
.literal:
.lit:   move.b  (a0)+,d1
        bsr.s   .emit
        dbf     d0,.lit
.next:  tst.w   d2
        bne.s   .decode
.ready:
        lea     g7b_dirty(pc),a0
        clr.w   g7b_error-g7b_dirty(a0)
        moveq   #21,d0
.clear: clr.l   (a0)+
        dbf     d0,.clear
        lea     g7b_saved_n(pc),a0
        clr.l   (a0)+
        clr.w   (a0)
        lea     g7b_hdr_flag(pc),a0
        clr.l   (a0)
        lea     g7b_seen(pc),a0
        moveq   #20,d0
.seen:  clr.l   (a0)+
        dbf     d0,.seen
        movem.l (sp)+,d2/a2
        rts
.emit:  move.b  d1,(a1)+
        cmp.w   #3160,d2
        bhi.s   .byte
        clr.b   (a1)+
.byte:  subq.w  #1,d2
        rts

; --- g7b_restore --- restaurar bloques sucios del anillo seleccionado
; entrada: a3 datos, a4 CUSTOM, a5 scroll; g7_select ya ejecutado
; salida: dos copias limpias, ultimo blit pendiente, bitmap vacio
; registros destruidos: d0-d1/a0-a1
; ciclos: medir por numero de bloques; 2 blits de 96 B por bloque
g7b_restore:
        movem.l d2-d7/a2-a3/a6,-(sp)
        bsr     g7b_wait
        move.w  g7_active(pc),d0
        mulu    #11,d0                     ; 0 u 88: convertir abajo a 0/44
        lsr.w   #1,d0
        lea     g7b_dirty(pc),a6
        add.w   d0,a6
        move.w  V_P(a5),d6
        subq.w  #2,d6
        moveq   #SLOTS-1,d7
.column:
        moveq   #0,d0
        move.w  d6,d0
        ; La camara inicial puede dejar columnas negativas; el modulo
        ; debe ser matematico, igual que las columnas de scroll.s.
        divs    #SLOTS,d0
        swap    d0
        tst.w   d0
        bpl.s   .slot
        add.w   #SLOTS,d0
.slot:  add.w   d0,d0
        move.w  (a6,d0.w),d5
        clr.w   (a6,d0.w)
        move.w  d0,d4
        moveq   #0,d3
.row:   btst    d3,d5
        beq     .advance
        tst.w   d6
        bmi     .advance                   ; margen fuera del mapa: nunca sucio
        cmp.w   D_COLS(a3),d6
        bhs     .advance
        move.w  d6,d0
        mulu    #15,d0
        add.w   d3,d0
        move.l  a3,a0
        add.l   D_MAP(a3),a0
        moveq   #0,d1
        move.b  (a0,d0.w),d1
        mulu    #96,d1
        move.l  a3,a2
        add.l   D_BLK(a3),a2
        add.l   d1,a2
        move.w  d3,d0
        mulu    #16*LINEB1,d0
        move.l  V_BUF1(a5),a1
        add.l   d0,a1
        add.w   d4,a1
        bsr     g7b_wait
        move.l  #$09f00000,BLTCON0R(a4)
        move.l  #$ffffffff,BLTAFWMR(a4)
        clr.w   BLTAMODR(a4)
        move.w  #ROWB1-2,BLTDMODR(a4)
        move.l  a2,BLTAPTR(a4)
        move.l  a1,BLTDPTR(a4)
        move.w  #(48<<6)|1,BLTSIZER(a4)
        bsr     g7b_wait
        move.l  a2,BLTAPTR(a4)
        lea     SLOTS*2(a1),a1
        move.l  a1,BLTDPTR(a4)
        move.w  #(48<<6)|1,BLTSIZER(a4)
.advance:
        addq.w  #1,d3
        cmp.w   #14,d3
        blo     .row
        addq.w  #1,d6
        dbf     d7,.column
        movem.l (sp)+,d2-d7/a2-a3/a6
        rts

; --- g7b_submit --- empezar una cola completa, conservada hasta wait
; entrada: d0.w cantidad (1..G7Q_MAX); banco+G7Q_OFF contiene registros
; salida: primer blit iniciado; IRQ BLIT habilitada mientras haya trabajo
; registros destruidos: d0-d1/a0-a1
; ciclos: medir coste fijo y 2 IRQ por palabra; no busca ni dibuja en IRQ
g7b_submit:
        movem.l d2/a2,-(sp)
        move.w  d0,d2
        bsr     g7b_wait
        tst.w   d2
        beq     .done
        cmp.w   #G7Q_MAX,d2
        bhi     .bad
        movem.l d3-d5/a3,-(sp)
        move.l  g7b_bank(pc),a1
        lea     G7Q_OFF(a1),a1
        move.w  g7_active(pc),d0
        mulu    #11,d0
        lsr.w   #1,d0
        lea     g7b_dirty(pc),a3
        add.w   d0,a3
        move.w  d2,d5
        subq.w  #1,d5
.mark:  move.l  (a1),d0
        sub.l   V_BUF1(a5),d0
        divu    #LINEB1,d0
        move.w  d0,d3
        lsr.w   #4,d3
        swap    d0
        and.w   #$ffff,d0
        move.w  (a3,d0.w),d4
        bset    d3,d4                      ; palabra: BTST/BSET en memoria es byte
        move.w  d4,(a3,d0.w)
        lea     16(a1),a1
        dbf     d5,.mark
        movem.l (sp)+,d3-d5/a3
        move.l  g7b_bank(pc),a1
        lea     G7Q_OFF(a1),a1
        lea     g7b_qptr(pc),a0
        move.l  a1,(a0)
        move.w  d2,g7b_qleft-g7b_qptr(a0)
        clr.w   g7b_qcopy-g7b_qptr(a0)
        move.w  #$0040,INTREQ(a4)
        move.w  #$0040,INTREQ(a4)
        move.l  #$0fca0000,BLTCON0R(a4)     ; D = A ? B : C; sin shift
        move.l  #$ffffffff,BLTAFWMR(a4)
        clr.w   BLTAMODR(a4)
        clr.w   BLTBMODR(a4)
        move.w  #ROWB1-2,BLTCMODR(a4)
        move.w  #ROWB1-2,BLTDMODR(a4)
        move.w  #$8040,INTENA(a4)
        bsr     g7b_start
.done:  movem.l (sp)+,d2/a2
        rts
.bad:   lea     g7b_error(pc),a0
        move.w  #1,(a0)                    ; rechazo explicito, nunca truncar
        bra.s   .done

; --- g7b_start --- ejecutar entrada actual de la cola
; entrada: a4 CUSTOM; cola propiedad del render, fuentes en chip
; salida: blit 1 palabra x 3 planos iniciado
; registros destruidos: d0/a0-a1
; ciclos: ~188 sin DMA; verificar con banco de rendimiento
g7b_start:
        move.l  g7b_qptr(pc),a0
        move.l  (a0)+,a1
        move.w  g7b_qcopy(pc),d0
        beq.s   .first
        lea     SLOTS*2(a1),a1
.first: move.l  a0,BLTAPTR(a4)
        addq.l  #6,a0
        move.l  a0,BLTBPTR(a4)
        move.l  a1,BLTCPTR(a4)
        move.l  a1,BLTDPTR(a4)
        move.w  #(3<<6)|1,BLTSIZER(a4)
        rts

; --- g7b_irq --- avanzar exclusivamente una cola ya preparada
; entrada: IRQ BLIT reconocida dos veces; a4 CUSTOM
; salida: siguiente blit iniciado o IRQ BLIT deshabilitada
; registros destruidos: d0/a0-a1
; ciclos: ~300 sin DMA; no busca colores ni consulta la OAM
g7b_irq:
        lea     g7b_qleft(pc),a0
        tst.w   (a0)
        beq.s   .stop
        eori.w  #1,g7b_qcopy-g7b_qleft(a0)
        bne.s   .start
        subq.w  #1,(a0)
        beq.s   .stop
        add.l   #16,g7b_qptr-g7b_qleft(a0)
.start: bra     g7b_start
.stop:  move.w  #$0040,INTENA(a4)
        rts

; --- g7b_wait --- terminar cola antes de reutilizar fuente/PF1/publicar
; entrada: a4 CUSTOM; IRQ habilitada en bucle principal
; salida: cola vacia y blitter detenido
; registros destruidos: ninguno
; ciclos: depende de la cola, medir; consulta con IRQ habilitada
g7b_wait:
        movem.l d0-d1/a0-a1,-(sp)
.wait:  move.w  g7b_qleft(pc),d0
        bne.s   .wait
.far:   lea     .far(pc),a0
        adda.l  #bwait-.far,a0
        jsr     (a0)
        movem.l (sp)+,d0-d1/a0-a1
        rts

        cnop 0,4
g7b_bank: dc.l 0
g7b_qptr: dc.l 0
g7b_qleft: dc.w 0
g7b_qcopy: dc.w 0
g7b_error: dc.w 0
g7b_dirty: ds.w SLOTS*2
        cnop 0,4
g7b_saved_n: ds.w 3
g7b_hdr_flag: ds.b 4
        cnop 0,4
g7b_hdr: ds.b 128*3
g7b_seen: ds.b 28*3
        cnop 0,4
        even
