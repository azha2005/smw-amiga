; SW-B: diario de cambios del mapa, independiente de fotos descartadas.
; D_TCHG: .w cantidad, registros de 6 B (celda, Map16, BLK.b, original.b).

; --- tile_current --- limite actual para el bucle NODECOUPLE, sin fotos
; entrada: a3/a4/a5 = datos/CUSTOM/scroll; salida: mapa visible actualizado
; registros destruidos: d0-d1/d7/a0-a1
; ciclos: tile_apply mas la lectura del limite
tile_current:
.base:  lea     .base(pc),a0
        sub.l   #.base-binstart,a0
        move.w  _tile_write(a0),d7
        bsr     tile_apply
        rts

; --- tile_apply ---
; entrada: d7.w = limite del diario capturado por la foto; a3 datos, a5 scroll
; salida: D_MAP y las dos copias de cada celda residente actualizadas
; registros destruidos: d0-d1/a0-a1
; conserva los registros restantes con movem
; con D_TCHG vacia (mkscroll.py sin SW_TILES=1) solo avanza tile_read
; ciclos: medidos con g5l.py / WinUAE BENCH en el informe SW-B
tile_apply:
.base0: lea     .base0(pc),a0
        sub.l   #.base0-binstart,a0
        ifd     TILECONTROL
        move.w  d7,_tile_read(a0)           ; A/B: consumir sin parchear mapa/PF1
        rts
        endc
        cmp.w   _tile_read(a0),d7
        beq     .return                    ; ruta usual: nada que blitear
        move.l  a3,a1
        add.l   D_TCHG(a3),a1
        tst.w   (a1)
        bne.s   .on
        move.w  d7,_tile_read(a0)           ; SW-B apagada (D_TCHG vacia): consumir
        rts
.on:
        movem.l d2-d7/a2-a6,-(sp)
.base1: lea     .base1(pc),a6
        sub.l   #.base1-binstart,a6
        move.w  _tile_read(a6),d6
.next:  cmp.w   d7,d6
        beq     .done
        move.w  d6,d0
        and.w   #255,d0
        lsl.w   #2,d0
        lea     _tile_changes(a6),a0
        move.w  (a0,d0.w),d4                ; celda = columna*15 + fila
        move.w  2(a0,d0.w),d5               ; Map16 resultado
        move.l  a3,a1
        add.l   D_TCHG(a3),a1
        move.w  (a1)+,d3
        subq.w  #1,d3
        bmi.s   .missing
.find:  cmp.w   (a1),d4
        blo.s   .missing
        bne.s   .fn
        cmp.w   2(a1),d5
        beq.s   .found
.fn:    addq.l  #6,a1
        dbf     d3,.find
.missing:
        move.l  #5,_mario_unsupported(a6)   ; MARIO_UNSUP_TILE: nunca aproximar
        bra     .advance
.found: moveq   #0,d0
        move.b  4(a1),d0
        move.l  a3,a0
        add.l   D_MAP(a3),a0
        cmp.b   (a0,d4.w),d0
        beq     .advance                   ; cambio repetido ya aplicado
        move.b  d0,(a0,d4.w)
        mulu    #96,d0
        add.l   a3,d0
        add.l   D_BLK(a3),d0
        move.l  d0,a2                      ; fuente inmutable en chip
        moveq   #0,d1
        move.w  d4,d1
        divu    #15,d1                     ; cociente columna, resto fila
        move.w  d1,d2
        sub.w   V_P(a5),d2
        cmp.w   #-2,d2
        blt     .advance
        cmp.w   #19,d2
        bgt     .advance
        swap    d1
        mulu    #16*LINEB1,d1               ; fila del bloque en buffer
        moveq   #0,d0
        move.w  d4,d0
        divu    #15,d0
        and.l   #$ffff,d0
        divu    #SLOTS,d0
        swap    d0
        add.w   d0,d0
        move.l  V_BUF1(a5),a0
        add.l   d1,a0
        add.w   d0,a0
        bsr     bwait
        move.l  #$09f00000,BLTCON0R(a4)
        move.l  #$ffffffff,BLTAFWMR(a4)
        clr.w   BLTAMODR(a4)
        move.w  #ROWB1-2,BLTDMODR(a4)
        move.l  a2,BLTAPTR(a4)
        move.l  a0,BLTDPTR(a4)
        move.w  #(48<<6)|1,BLTSIZER(a4)
        bsr     bwait
        move.l  a2,BLTAPTR(a4)
        lea     SLOTS*2(a0),a0
        move.l  a0,BLTDPTR(a4)
        move.w  #(48<<6)|1,BLTSIZER(a4)
.advance:
        addq.w  #1,d6
        move.w  d6,_tile_read(a6)           ; liberar solo despues de leer
        bra     .next
.done:  movem.l (sp)+,d2-d7/a2-a6
.return:
        rts

; --- tile_reset ---
; entrada: a3 = SMWS cargado; antes de reconstruir PF1 al reiniciar
; salida: D_MAP original y diario vacio (sin reserva adicional de slow)
; registros destruidos: d0-d1/a0-a1
; ciclos: medidos por restart_verify.py en el informe SW-B
tile_reset:
        movem.l d2/a2-a3,-(sp)
.base:  lea     .base(pc),a0
        sub.l   #.base-binstart,a0
        clr.w   _tile_write(a0)
        clr.w   _tile_read(a0)
        move.l  a3,d0
        beq.s   .done
        move.l  a3,a1
        add.l   D_TCHG(a3),a1
        move.l  a3,a2
        add.l   D_MAP(a3),a2
        move.w  (a1)+,d1
        subq.w  #1,d1
        bmi.s   .done
.loop:  move.w  (a1),d0
        move.b  5(a1),(a2,d0.w)
        addq.l  #6,a1
        dbf     d1,.loop
.done:  movem.l (sp)+,d2/a2-a3
        rts
