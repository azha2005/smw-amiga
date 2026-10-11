; G7-3b: productor PF1 sin busqueda (rediseno 2026-10-11).
; Especificacion: tools/g7_fast.py (cada decision igual, palabra a palabra).
; Por fila con efectos: 1) indice existente, 2) indice libre (prefijo +
; recargas a NOP), 3) prestamo por ventana, 3b) reconstruccion EDF. Una
; fila sin plan rechaza la foto de forma explicita (g7b_error), nunca
; aproxima. No hay tablas por numero de frame. Solo con G7_BOBS.
;
; Area de trabajo: g7f_w (a6 en todo el modulo).

W_OV    equ 0           ; 256 b ranura de color por pixel de pantalla (0 nada)
W_OUT   equ 256         ; 256 b indice PF1 asignado a cada pixel de efecto
W_IDX   equ 512         ; 256 b indice del terreno (0 bajo efecto), pasos 3/3b
W_OUT2  equ 768         ; 256 b out de prueba del paso 3b
W_CT    equ 1024        ; 16 w color de cada ranura (1..15)
W_ORD   equ 1056        ; 16 b ranuras por color ascendente
W_EM    equ 1072        ; 18 w mascara de efecto por palabra PF1 (17 usadas)
W_ORG   equ 1108        ; 64 l palabras originales del segmento
W_SEG   equ 1364        ; 64 l palabras de trabajo
W_TRY   equ 1620        ; 64 l prueba
W_TAIL  equ 1876        ; 3 l salto $84 y sus tres MOVE
W_POS   equ 1888        ; 64 w x del MOVE del cuerpo ($8000: no es MOVE del cuerpo)
W_BEF   equ 2016        ; 64 w ranura previa a la palabra (cuerpo)
W_FLG   equ 2144        ; 64 b bit0 WAIT del cuerpo, bit1 palabra del cuerpo
W_SLK   equ 2208        ; 64 w holgura del WAIT ($7fff: WAIT de apertura)
W_JOB   equ 2336        ; 64 x 8 b trabajos EDF: a, b, reg, valor
W_CL    equ 2848        ; 48 x 8 b grupos: ranura.b, estado.b, x0.w, x1.w, r.w
W_ENT   equ 3232        ; 32 x 12 b fichas: x, y, size, tile, attr, -
W_EVT   equ 3616        ; 64 x 6 b colores PF1 del segmento: pos, r, valor
W_NW    equ 4000        ; .w palabras de W_SEG
W_NO    equ 4002        ; .w palabras de W_ORG
W_PLEN  equ 4004        ; .w largo del prefijo (prefix_of)
W_NB    equ 4006        ; .w MOVE del prefijo
W_OPEN  equ 4008        ; .w indice de la primera palabra del cuerpo (-1)
W_TEND  equ 4010        ; .w ranura tras el ultimo MOVE del cuerpo
W_FIRST equ 4012        ; .w primer hueco (place)
W_ROW   equ 4014
W_CAM   equ 4016
W_NENT  equ 4018
W_XMIN  equ 4020
W_XMAX  equ 4022
W_NS    equ 4024        ; ranuras de color usadas
W_NCL   equ 4026        ; grupos
W_USED  equ 4028        ; indices del terreno visibles fuera de efectos
W_RES   equ 4030        ; reservados
W_CLM   equ 4032        ; indices de los que depende un efecto
W_END   equ 4034        ; ultima x permitida (351 - 8 nb siguiente), $7fff fuera de modelo
W_NEV   equ 4036
W_NJ    equ 4038
W_YMIN  equ 4040
W_YMAX  equ 4042
W_ORDR  equ 4044        ; 8 b orden de prueba de indices (usados, luego libres)
W_COL0  equ 4052        ; .w columna PF1 de la palabra 0 de pantalla ((cam>>4) mod 22)
W_PF    equ 4056        ; .l PF1 libre
W_COP   equ 4060        ; .l lista libre
W_BANK  equ 4064        ; .l banco G7S1
W_REC   equ 4068        ; .l foto
W_ACT   equ 4072        ; 28 b filas con alguna ficha (bit 7-(fila&7) de fila>>3)
W_PC    equ 4100        ; 16 b ranura de cada color de la paleta de la ficha (0 sin ver)
W_ECNT  equ 4116        ; .w fichas que faltan (overlay)
W_ROFF  equ 4118        ; .w fila dentro de la ficha 8x8, en bytes
W_TROW  equ 4120        ; .w tile + 16 (sy >> 3)
W_NCH   equ 4122        ; .w grupos de 8 pixeles de la ficha
W_CH    equ 4124        ; .w grupo actual
W_PFR   equ 4126        ; .l PF1 libre + fila * LINEB1
W_SR    equ 4130        ; 16 b indice PF1 de cada ranura (camino corto)
W_NEED  equ 4146        ; 16 b ranuras sin indice constante, en orden de color
W_NQ    equ 4162        ; .w entradas de la cola de la fila
W_NSP   equ 4164        ; .w tramos de fichas en la fila
W_SPN   equ 4166        ; 32 x 4 b tramo visible de cada ficha que corta la fila: x0, x1
W_SPW   equ 4294        ; .w suma de los anchos de W_SPN
W_JL    equ 4296        ; 64 b palabras que parcha el camino corto ($ff fin)
W_WANT  equ 4360        ; 256 w color requerido por x (-1 transparente; required())
W_NT    equ 4872        ; .w palabras de W_TRY
W_SPARE equ 4874        ; .w indices sin uso (ni terreno ni efecto): sus recargas son ranuras
W_WCLM  equ 4876        ; .w reclamados de la ventana
W_UIN   equ 4878        ; .w indices del terreno dentro de [x0, x1]
W_UANY  equ 4880        ; .w indices del terreno en la fila
W_ULO   equ 4882        ; 8 w ultimo uso < x0 (-1 ninguno)
W_UHI   equ 4898        ; 8 w primer uso > x1 (256 ninguno)
W_CUR   equ 4914        ; 8 w color vigente por indice (g7f_want)
W_WIN   equ 4930        ; 64 b variables de la ventana y de place
W_EDF   equ 4994        ; 2048 b reservados para el paso 3b (player/g7edf.s)
W_UM    equ 7042        ; 8 x 17 w uso del terreno por indice y palabra de pantalla
W_ULM   equ 7314        ; 17 w pixeles a la izquierda de x0 (g7f_uses)
W_URM   equ 7348        ; 17 w pixeles a la derecha de x1
W_SIZE  equ 7382

G7F_T0   equ -56
G7F_IDLE equ 48
G7F_XD0  equ 263
G7F_V0   equ $2c
G7F_WRAP equ 255-G7F_V0

; pixel decodificado en d5; a0 = W_OV[gx], d6 = gx, a4 = W_PC
OVPX    macro
        tst.b   d5                         ; add.b reescribe Z entre los addx
        beq.s   .n\@
        cmp.w   #256,d6
        bhs.s   .n\@
        tst.b   (a0)
        bne.s   .n\@
        move.b  (a4,d5.w),d0
        bne.s   .h\@
        bsr     g7f_ovmiss
        bmi     .many
.h\@:   move.b  d0,(a0)
.n\@:   addq.l  #1,a0
        addq.w  #1,d6
        endm


; --- g7f_render --- producir los efectos de la foto DC_REND en el PF1 libre
; entrada:  a2 foto, a1 banco G7S1, a5 vars (scroll)
; salida:   d0.l = 0, o 1 ficha sin fuente, 2|fila<<8 sin plan, 4|fila<<8 diario lleno
; registros destruidos: d0
; ciclos:   medir con tools/g7f_verify.py (Musashi, sin DMA)
g7f_render:
        movem.l d1-d7/a0-a6,-(sp)
        lea     g7f_w(pc),a6
        move.l  a2,W_REC(a6)
        move.l  a1,W_BANK(a6)
        move.w  R_S(a2),W_CAM(a6)
        move.l  V_BUF1(a5),W_PF(a6)
        move.l  V_BACK(a5),W_COP(a6)
        moveq   #0,d0
        move.w  W_CAM(a6),d0
        lsr.w   #4,d0
        divu    #SLOTS,d0
        swap    d0
        move.w  d0,W_COL0(a6)
        bsr     g7f_entries                ; W_OV llega limpio: g7f_unov tras cada fila
        tst.w   W_NENT(a6)
        beq.s   .ok
        move.w  W_YMIN(a6),W_ROW(a6)
.row:   move.w  W_ROW(a6),d7
        cmp.w   W_YMAX(a6),d7
        bgt.s   .ok
        move.w  d7,d0
        lsr.w   #3,d0
        lea     W_ACT(a6),a0
        not.w   d7
        btst    d7,(a0,d0.w)               ; bit 7-(fila&7)
        beq.s   .skip
        bsr     g7f_row                    ; destruye d0-d7/a0-a5
        bsr     g7f_unov
        tst.l   d0
        bne.s   .out
.skip:  addq.w  #1,W_ROW(a6)
        bra.s   .row
.ok:    moveq   #0,d0
.out:   movem.l (sp)+,d1-d7/a0-a6
        rts

; --- g7f_entries --- fichas de efectos visibles, en orden de OAM
; entrada:  a6 trabajo (W_REC)
; salida:   W_ENT/W_NENT, W_YMIN/W_YMAX
; registros destruidos: d0-d6/a0-a4
; ciclos:   ~32 entradas x 60
g7f_entries:
        move.l  W_REC(a6),a0
        lea     R_OAM(a0),a0
        lea     256(a0),a3                 ; tamano y x alta
        lea     W_ENT(a6),a1
        lea     g7f_slots(pc),a2
        clr.w   W_NENT(a6)
        lea     W_ACT(a6),a4
        moveq   #6,d0
.ca:    clr.l   (a4)+
        dbf     d0,.ca
        lea     W_ACT(a6),a4
        move.w  #999,W_YMIN(a6)
        move.w  #-1,W_YMAX(a6)
.next:  moveq   #0,d0
        move.b  (a2)+,d0
        bmi     .done                      ; $ff: fin de la tabla
        moveq   #0,d1
        move.b  (a2)+,d1                   ; 4e
        moveq   #0,d2
        move.b  1(a0,d1.w),d2
        cmp.b   #223,d2
        bhs.s   .next                      ; y + 1 >= 224
        addq.w  #1,d2                      ; y
        moveq   #0,d6
        move.b  (a3,d0.w),d6
        moveq   #8,d3
        btst    #1,d6
        beq.s   .small
        moveq   #16,d3
.small: moveq   #0,d4
        move.b  (a0,d1.w),d4               ; x baja
        btst    #0,d6
        beq.s   .xok
        add.w   #256,d4
.xok:   cmp.w   #256,d4
        blt.s   .xsign
        sub.w   #512,d4
.xsign: cmp.w   #256,d4
        bge.s   .next
        move.w  d4,d5
        add.w   d3,d5
        ble.s   .next
        moveq   #0,d5
        move.b  3(a0,d1.w),d5              ; atributo
        moveq   #0,d6
        move.b  2(a0,d1.w),d6
        btst    #0,d5
        beq.s   .tile
        add.w   #256,d6
.tile:  move.w  d4,(a1)+
        move.w  d2,(a1)+
        move.w  d3,(a1)+
        move.w  d6,(a1)+
        move.w  d5,(a1)+
        clr.w   (a1)+
        addq.w  #1,W_NENT(a6)
        move.w  d2,d0                      ; filas activas y .. min(y+size,224)-1
        move.w  d2,d1
        add.w   d3,d1
        cmp.w   #224,d1
        ble.s   .act
        move.w  #224,d1
.act:   move.w  d0,d5
        lsr.w   #3,d5
        move.w  d0,d6
        not.w   d6
        bset    d6,(a4,d5.w)
        addq.w  #1,d0
        cmp.w   d1,d0
        blo.s   .act
        cmp.w   W_YMIN(a6),d2
        bge.s   .ymin
        move.w  d2,W_YMIN(a6)
.ymin:  add.w   d3,d2
        cmp.w   #224,d2
        ble.s   .ymax
        move.w  #224,d2
.ymax:  subq.w  #1,d2
        cmp.w   W_YMAX(a6),d2
        ble     .next
        move.w  d2,W_YMAX(a6)
        bra     .next
.done:  rts

; Entradas de OAM de los efectos (sws_cmp.OAM_GROUPS), en orden de prioridad,
; con su desplazamiento 4 e en la tabla baja (e <= 63: cabe en un byte).
g7f_slots:                                 ; e, 4 e
        dc.b    8,32,9,36,10,40,11,44
        dc.b    20,80,21,84,22,88,23,92
        dc.b    24,96,25,100,26,104,27,108
        dc.b    28,112,29,116,30,120,31,124
        dc.b    44,176,45,180,46,184,47,188
        dc.b    48,192,49,196,50,200,51,204
        dc.b    52,208,53,212,54,216,55,220
        dc.b    60,240,61,244,62,248,63,252
        dc.b    $ff
        even

; --- g7f_row --- una fila: overlay, plan y emision
; entrada:  a6 trabajo, W_ROW
; salida:   d0.l = 0 o codigo de rechazo
; registros destruidos: d0-d7/a0-a5
; ciclos:   medir (camino rapido ~5-10 k)
g7f_row:
        bsr     g7f_overlay
        tst.l   d0
        bne.s   .out
        tst.w   W_XMAX(a6)
        bmi.s   .none
        move.w  W_ROW(a6),d0
        mulu    #LINEB1,d0
        add.l   W_PF(a6),d0
        move.l  d0,W_PFR(a6)               ; base de la fila en el PF1 libre
        bsr     g7f_order
        bsr     g7f_v2
        tst.l   d0
        bpl.s   .out                       ; hecha (0) o diario lleno
        bsr     g7f_load
        bsr     g7f_used
        bsr     g7f_fast
        tst.w   W_NCL(a6)                  ; grupos pendientes tras el paso 2
        beq.s   .emit
        bsr     g7f_left
        tst.l   d0
        bne.s   .out
.emit:  bsr     g7f_emit
.out:   rts
.none:  moveq   #0,d0
        rts

; --- g7f_unov --- devolver W_OV a cero en los tramos de las fichas de la fila
; entrada:  a6 trabajo (W_SPN/W_NSP)
; registros destruidos: d1-d2/a0-a1 (d0 lleva el resultado de la fila)
g7f_unov:
        move.w  W_NSP(a6),d1
        lea     W_SPN(a6),a1
        bra.s   .t
.s:     lea     W_OV(a6),a0
        add.w   (a1)+,a0
        move.w  (a1)+,d2
        sub.w   -4(a1),d2
.c:     clr.b   (a0)+
        dbf     d2,.c
.t:     dbf     d1,.s
        rts

; --- g7f_overlay --- color de efecto por pixel de la fila (P.overlays)
; Decodifica de a 8 pixeles (un byte por plano) en el orden de dx de la
; especificacion, asi el primer rechazo es el mismo. W_XMIN/W_XMAX son una
; cota (tramo visible de las fichas que cortan la fila), no el pixel exacto.
; entrada:  a6 trabajo, W_OV limpio
; salida:   W_OV, W_CT/W_NS, W_XMIN/W_XMAX; d0 = 0 o 1/2|fila<<8
; registros destruidos: d0-d7/a0-a5
; ciclos:   ~40 por pixel opaco, ~25 transparente
g7f_overlay:
        clr.w   W_NS(a6)
        clr.w   W_NSP(a6)
        clr.w   W_SPW(a6)
        move.w  #256,W_XMIN(a6)
        move.w  #-1,W_XMAX(a6)
        lea     W_ENT(a6),a5
        move.w  W_NENT(a6),W_ECNT(a6)
        lea     W_PC(a6),a4
.ent:   subq.w  #1,W_ECNT(a6)
        bmi     .done
        move.w  W_ROW(a6),d6
        sub.w   2(a5),d6                   ; sy
        bmi     .skip
        cmp.w   4(a5),d6
        bge     .skip
        btst    #7,9(a5)
        beq.s   .noflipy
        neg.w   d6
        add.w   4(a5),d6
        subq.w  #1,d6
.noflipy:
        move.w  d6,d0
        and.w   #7,d0
        add.w   d0,d0
        move.w  d0,W_ROFF(a6)
        lsr.w   #3,d6
        lsl.w   #4,d6
        add.w   6(a5),d6
        move.w  d6,W_TROW(a6)              ; tile + 16 (sy >> 3)
        move.l  W_BANK(a6),a1
        move.w  8(a5),d0
        lsr.w   #1,d0
        and.w   #7,d0
        lsl.w   #5,d0
        lea     1040(a1),a2
        add.w   d0,a2                      ; paleta de la ficha
        clr.l   (a4)
        clr.l   4(a4)
        clr.l   8(a4)
        clr.l   12(a4)
        move.w  W_NSP(a6),d1               ; tramo [max(x,0), min(x+size,256)-1]
        addq.w  #1,W_NSP(a6)
        lsl.w   #2,d1
        lea     W_SPN(a6),a3
        add.w   d1,a3
        move.w  (a5),d0
        bpl.s   .x0
        moveq   #0,d0
.x0:    move.w  d0,(a3)+
        cmp.w   W_XMIN(a6),d0
        bge.s   .x1
        move.w  d0,W_XMIN(a6)
.x1:    move.w  (a5),d0
        add.w   4(a5),d0
        subq.w  #1,d0
        cmp.w   #255,d0
        ble.s   .x2
        move.w  #255,d0
.x2:    move.w  d0,(a3)
        sub.w   -2(a3),d0
        addq.w  #1,d0
        add.w   d0,W_SPW(a6)
        move.w  (a3),d0
        cmp.w   W_XMAX(a6),d0
        ble.s   .x3
        move.w  d0,W_XMAX(a6)
.x3:    move.w  4(a5),d0
        lsr.w   #3,d0
        move.w  d0,W_NCH(a6)
        clr.w   W_CH(a6)
        move.w  (a5),d6                    ; gx
        lea     W_OV(a6),a0
        adda.w  d6,a0
.chunk: move.w  W_CH(a6),d0
        cmp.w   W_NCH(a6),d0
        bhs     .skip
        addq.w  #1,W_CH(a6)
        cmp.w   #256,d6
        bge     .skip                      ; el resto queda fuera
        cmp.w   #-8,d6
        ble     .cout
        btst    #6,9(a5)
        beq.s   .tc
        not.w   d0
        add.w   W_NCH(a6),d0               ; espejo: n - 1 - k
.tc:    add.w   W_TROW(a6),d0
        add.w   d0,d0
        move.w  16(a1,d0.w),d0             ; offset de la ficha
        cmp.w   #$ffff,d0
        beq     .nosrc
        lea     (a1,d0.w),a3               ; offset < 12288
        adda.w  W_ROFF(a6),a3
        move.b  (a3),d1
        move.b  16(a3),d2
        move.b  32(a3),d3
        move.b  48(a3),d4
        move.b  d1,d0
        or.b    d2,d0
        or.b    d3,d0
        or.b    d4,d0
        beq     .cout                      ; 8 pixeles transparentes
        moveq   #7,d7
        btst    #6,9(a5)
        bne     .fx
.p:     moveq   #0,d5
        add.b   d4,d4
        addx.w  d5,d5
        add.b   d3,d3
        addx.w  d5,d5
        add.b   d2,d2
        addx.w  d5,d5
        add.b   d1,d1
        addx.w  d5,d5
        OVPX
        dbf     d7,.p
        bra     .chunk
.fx:    moveq   #0,d5
        lsr.b   #1,d4
        addx.w  d5,d5
        lsr.b   #1,d3
        addx.w  d5,d5
        lsr.b   #1,d2
        addx.w  d5,d5
        lsr.b   #1,d1
        addx.w  d5,d5
        OVPX
        dbf     d7,.fx
        bra     .chunk
.cout:  addq.l  #8,a0
        addq.w  #8,d6
        bra     .chunk
.nosrc: moveq   #7,d7                      ; sin fuente: rechazo si queda visible
.ns:    cmp.w   #256,d6
        bhs.s   .nsn
        tst.b   (a0)
        beq.s   .rej1
.nsn:   addq.l  #1,a0
        addq.w  #1,d6
        dbf     d7,.ns
        bra     .chunk
.skip:  lea     12(a5),a5
        bra     .ent
.done:  move.w  W_XMAX(a6),d0              ; tramos solapados: un solo tramo
        sub.w   W_XMIN(a6),d0
        bmi.s   .one
        cmp.w   W_SPW(a6),d0
        bge.s   .one
        move.w  #1,W_NSP(a6)
        move.l  W_XMIN(a6),W_SPN(a6)       ; W_XMIN, W_XMAX contiguos
.one:   tst.w   W_NS(a6)                   ; todo pixel escrito tiene ranura
        bne.s   .any
        move.w  #-1,W_XMAX(a6)             ; ningun pixel opaco
.any:   moveq   #0,d0
        rts
.rej1:  moveq   #1,d0
        rts
.many:  moveq   #2,d0
        move.w  W_ROW(a6),d1
        lsl.w   #8,d1
        or.w    d1,d0
        rts

; --- g7f_ovmiss --- ranura del color d5 de la paleta a2 (alta si es nuevo)
; entrada:  d5.w indice de paleta 1..15, a2 paleta, a4 W_PC
; salida:   d0.b ranura, N = 1 si pasa de 15 colores
; registros destruidos: d0
g7f_ovmiss:
        movem.l d1-d2/a3,-(sp)
        move.w  d5,d2
        add.w   d2,d2
        move.w  (a2,d2.w),d2               ; color 12 bits
        lea     W_CT+2(a6),a3
        move.w  W_NS(a6),d1
        moveq   #1,d0
        bra.s   .find
.look:  cmp.w   (a3)+,d2
        beq.s   .found
        addq.w  #1,d0
.find:  dbf     d1,.look
        cmp.w   #15,d0
        bhi.s   .many
        move.w  d2,(a3)
        move.w  d0,W_NS(a6)
.found: move.b  d0,(a4,d5.w)               ; N = 0
        movem.l (sp)+,d1-d2/a3             ; movem no toca las banderas
        rts
.many:  movem.l (sp)+,d1-d2/a3
        moveq   #-1,d0
        rts

; --- g7f_load --- segmento original de la fila y la siguiente
; entrada:  a6 trabajo
; salida:   W_ORG/W_SEG/W_NO/W_NW/W_TAIL, analisis de W_ORG (g7f_scan),
;           W_EVT, W_END
; registros destruidos: d0-d7/a0-a3
; ciclos:   ~20 por palabra
g7f_load:
        move.w  W_ROW(a6),d0
        bsr     g7f_segaddr
        lea     W_ORG(a6),a1
        lea     W_SEG(a6),a2
        moveq   #0,d1
.copy:  move.l  (a0)+,d0
        swap    d0
        cmp.w   #$84,d0
        beq.s   .tail
        swap    d0
        move.l  d0,(a1)+
        move.l  d0,(a2)+
        addq.w  #1,d1
        cmp.w   #61,d1
        blo.s   .copy
        illegal                            ; lista sin salto: no ocurre (lint)
.tail:  swap    d0
        lea     W_TAIL(a6),a1
        move.l  d0,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.w  d1,W_NO(a6)
        move.w  d1,W_NW(a6)
        lea     W_ORG(a6),a0
        move.w  d1,d0
        bsr     g7f_scan
        lea     W_ORG(a6),a0
        move.w  W_NO(a6),d0
        bsr     g7f_events
        ; fin permitido: 351 - 8 * nb de la fila siguiente (prefix_of)
        move.w  W_ROW(a6),d0
        addq.w  #1,d0
        cmp.w   #224,d0
        blo.s   .wrap
        moveq   #0,d0
.wrap:  bsr     g7f_segaddr
        moveq   #0,d2                      ; MOVE del prefijo
        moveq   #0,d1                      ; indice
.pre:   move.w  (a0),d0
        cmp.w   #$84,d0
        beq.s   .pend
        cmp.w   #2,d1
        bhs.s   .pre2
        btst    #0,d0
        bne.s   .pskip
        cmp.w   #$1fe,d0
        beq.s   .pskip
        bra.s   .pmove
.pre2:  btst    #0,d0
        bne.s   .pend
        cmp.w   #$1fe,d0
        beq.s   .pend
.pmove: addq.w  #1,d2
.pskip: addq.l  #4,a0
        addq.w  #1,d1
        bra.s   .pre
.pend:  move.w  #$7fff,W_END(a6)
        cmp.w   #7,d2
        blo.s   .noend
        cmp.w   #9,d2
        bhi.s   .noend
        lsl.w   #3,d2
        move.w  #351,d0
        sub.w   d2,d0
        move.w  d0,W_END(a6)
.noend: rts

; --- g7f_segaddr --- a0 = segmento d0 de la lista libre
; registros destruidos: d0/a0
g7f_segaddr:
        move.l  W_COP(a6),a0
        adda.l  #CL_LINES,a0
        and.l   #$ffff,d0
        lsl.l   #8,d0                      ; SEG = 256
        add.l   d0,a0
        rts

; --- g7f_adv --- d0 = ranura siguiente (codo 231 -> 243, 8 px desde 239)
; registros destruidos: d0
g7f_adv:
        cmp.w   #231,d0
        bne.s   .n
        move.w  #243,d0
        rts
.n:     cmp.w   #239,d0
        blt.s   .s16
        addq.w  #8,d0
        rts
.s16:   add.w   #16,d0
        rts

; --- g7f_xh --- d0 = x del primer MOVE tras WAIT h (d1 = h par <= $ce)
; registros destruidos: d0
g7f_xh:
        cmp.w   #$c0,d1
        bhi.s   .tab
        move.w  d1,d0
        sub.w   #$48,d0
        asr.w   #2,d0
        lsl.w   #3,d0
        subq.w  #1,d0
        rts
.tab:   move.w  #243,d0
        cmp.w   #$c4,d1
        beq.s   .r
        cmp.w   #$c6,d1
        beq.s   .r
        move.w  #247,d0
        cmp.w   #$c8,d1
        beq.s   .r
        cmp.w   #$ca,d1
        beq.s   .r
        move.w  #251,d0
        cmp.w   #$cc,d1
        beq.s   .r
        move.w  #255,d0
.r:     rts

; --- g7f_waitx --- d0 = x resuelto de un WAIT d1.w (palabra 1) desde t = d0
; registros destruidos: d0-d2
g7f_waitx:
        move.w  d0,d2
        bsr     g7f_adv
        bsr     g7f_adv                    ; adv(t, 2)
        exg     d0,d2
        and.w   #$fe,d1
        cmp.w   #$ce,d1
        bls.s   .h
        move.w  #G7F_XD0,d0
        bra.s   .m
.h:     bsr     g7f_xh
.m:     cmp.w   d2,d0
        bge.s   .r
        move.w  d2,d0
.r:     rts

; --- g7f_scan --- modelo de tiempos de un segmento (timeline/body_info)
; entrada:  a0 palabras (longs), d0.w cantidad, a6 trabajo (W_ROW)
; salida:   W_POS/W_BEF/W_FLG/W_SLK, W_PLEN/W_NB/W_OPEN/W_TEND/W_FIRST
; registros destruidos: d0-d7/a0-a5
; ciclos:   ~80 por palabra
g7f_scan:
        move.w  d0,d7                      ; n
        move.l  a0,a3
        ; prefix_of: largo y MOVE
        moveq   #0,d1
        moveq   #0,d2
.p:     cmp.w   d7,d1
        bhs.s   .pdone
        move.w  d1,d3
        lsl.w   #2,d3
        move.w  (a3,d3.w),d0
        moveq   #0,d4                      ; 1 = WAIT o NOP
        btst    #0,d0
        bne.s   .pwn
        cmp.w   #$1fe,d0
        bne.s   .pmv
.pwn:   moveq   #1,d4
.pmv:   cmp.w   #2,d1
        bhs.s   .p2
        tst.w   d4
        bne.s   .pin
        addq.w  #1,d2
        bra.s   .pin
.p2:    tst.w   d4
        bne.s   .pdone
        addq.w  #1,d2
.pin:   addq.w  #1,d1
        bra.s   .p
.pdone: move.w  d1,W_PLEN(a6)
        move.w  d2,W_NB(a6)
        ; timeline
        lea     W_POS(a6),a2
        lea     W_BEF(a6),a4
        lea     W_FLG(a6),a5
        move.w  W_ROW(a6),d5
        add.w   #G7F_V0-1,d5
        and.w   #255,d5                    ; linea anterior
        moveq   #0,d6                      ; stage
        moveq   #0,d4                      ; nb del timeline
        move.w  #-1,W_OPEN(a6)
        move.w  d7,W_FIRST(a6)
        moveq   #0,d3                      ; o
.w:     cmp.w   d7,d3
        bhs     .wend
        move.w  d3,d2
        add.w   d2,d2                      ; 2 o
        move.w  #$8000,(a2,d2.w)
        clr.b   (a5,d3.w)
        move.w  d3,d0
        lsl.w   #2,d0
        move.w  (a3,d0.w),d1               ; w1
        ; FIRST: primer i>=2 con WAIT o NOP
        cmp.w   #2,d3
        blo.s   .nf
        cmp.w   W_FIRST(a6),d3
        bhs.s   .nf
        btst    #0,d1
        bne.s   .sf
        cmp.w   #$1fe,d1
        bne.s   .nf
.sf:    move.w  d3,W_FIRST(a6)
.nf:    tst.w   d6
        bne.s   .body
        btst    #0,d1
        beq.s   .s0m
        move.w  d1,d0
        lsr.w   #8,d0
        cmp.w   d5,d0
        beq     .wnext
        cmp.w   #$ffdf,d1
        beq     .wnext
        bra.s   .open
.s0m:   cmp.w   #$1fe,d1
        bne.s   .s0mv
        cmp.w   #2,d3
        blo     .wnext
        bra.s   .open
.s0mv:  addq.w  #1,d4
        bra     .wnext
.open:  moveq   #1,d6
        move.w  d3,W_OPEN(a6)
        move.w  #G7F_T0,d0
        move.w  d4,a0
        sub.w   #9,a0
        cmp.w   #0,a0
        ble.s   .t0
        move.w  a0,d0
        lsl.w   #4,d0
        add.w   #G7F_T0,d0
.t0:    move.w  d0,a1                      ; t
.body:  bset    #1,(a5,d3.w)
        move.w  a1,(a4,d2.w)
        btst    #0,d1
        bne.s   .bwait
        cmp.w   W_FIRST(a6),d3
        bhs.s   .bm
        move.w  d3,W_FIRST(a6)
.bm:    move.w  a1,(a2,d2.w)
        move.w  a1,d0
        bsr     g7f_adv
        move.w  d0,a1
        bra.s   .wnext
.bwait: bset    #0,(a5,d3.w)
        move.w  a1,d0
        move.w  d2,-(sp)
        bsr     g7f_waitx
        move.w  (sp)+,d2
        lea     W_SLK(a6),a0
        move.w  #$7fff,(a0,d2.w)
        cmp.w   W_OPEN(a6),d3
        beq.s   .slk
        move.w  d0,d1
        sub.w   a1,d1
        move.w  d1,(a0,d2.w)
.slk:   move.w  d0,a1
.wnext: addq.w  #1,d3
        bra     .w
.wend:  tst.w   d6
        bne.s   .te
        move.w  #G7F_T0,d0
        sub.w   #9,d4
        ble.s   .t1
        lsl.w   #4,d4
        add.w   d4,d0
.t1:    move.w  d0,a1
.te:    move.w  a1,W_TEND(a6)
        rts

; --- g7f_events --- colores PF1 del segmento analizado (orden de palabras)
; entrada:  a0 palabras, d0.w cantidad, analisis de g7f_scan sobre ellas
; salida:   W_EVT/W_NEV: pos ($8000 prefijo), r, valor & $fff
; registros destruidos: d0-d4/a1-a3
g7f_events:
        move.w  d0,d4
        lea     W_EVT(a6),a1
        lea     W_FLG(a6),a2
        lea     W_POS(a6),a3
        moveq   #0,d3
        moveq   #0,d1                      ; o
        bra.s   .t
.e:     move.w  d1,d0
        lsl.w   #2,d0
        move.w  (a0,d0.w),d2
        cmp.w   #$182,d2
        blo.s   .n
        cmp.w   #$18e,d2
        bhi.s   .n
        btst    #1,(a2,d1.w)
        beq.s   .pre
        move.w  d1,d0
        add.w   d0,d0
        move.w  (a3,d0.w),(a1)+
        bra.s   .r
.pre:   move.w  #$8000,(a1)+
.r:     sub.w   #$180,d2
        lsr.w   #1,d2
        move.w  d2,(a1)+
        move.w  d1,d0
        lsl.w   #2,d0
        move.w  2(a0,d0.w),d2
        and.w   #$fff,d2
        move.w  d2,(a1)+
        addq.w  #1,d3
.n:     addq.w  #1,d1
.t:     cmp.w   d4,d1
        blo.s   .e
        move.w  d3,W_NEV(a6)
        rts

; --- g7f_order --- ranuras por color ascendente y mascara de efecto
; entrada:  a6 trabajo (W_OV, W_CT, W_NS, W_CAM)
; salida:   W_ORD, W_EM
; registros destruidos: d0-d5/a0-a2
g7f_order:
        lea     W_ORD(a6),a0
        lea     W_CT(a6),a1
        move.w  W_NS(a6),d0
        moveq   #1,d1
.fill:  move.b  d1,-1(a0,d1.w)
        addq.w  #1,d1
        cmp.w   d0,d1
        bls.s   .fill
        ; insercion (<= 15 ranuras)
        moveq   #1,d1
.ins:   cmp.w   d0,d1
        bhs.s   .sorted
        move.w  d1,d2
.down:  tst.w   d2
        beq.s   .nxt
        moveq   #0,d3
        move.b  -1(a0,d2.w),d3
        moveq   #0,d4
        move.b  (a0,d2.w),d4
        add.w   d3,d3
        add.w   d4,d4
        move.w  (a1,d3.w),d5
        cmp.w   (a1,d4.w),d5
        bls.s   .nxt
        move.b  -1(a0,d2.w),d3
        move.b  (a0,d2.w),-1(a0,d2.w)
        move.b  d3,(a0,d2.w)
        subq.w  #1,d2
        bra.s   .down
.nxt:   addq.w  #1,d1
        bra.s   .ins
.sorted:
        lea     W_EM(a6),a2
        move.l  a2,a0
        moveq   #8,d0
.clr:   clr.l   (a0)+
        dbf     d0,.clr
        move.w  W_CAM(a6),d5
        and.w   #15,d5                     ; s
        lea     W_SPN(a6),a1
        move.w  W_NSP(a6),d0
        bra.s   .st
.sp:    move.w  (a1)+,d1
.px:    tst.b   W_OV(a6,d1.w)
        beq.s   .pn
        move.w  d1,d2
        add.w   d5,d2
        move.w  d2,d3
        lsr.w   #4,d3
        add.w   d3,d3                      ; palabra
        not.w   d2
        and.w   #15,d2                     ; 15 - ((x+s)&15)
        move.w  (a2,d3.w),d4
        bset    d2,d4
        move.w  d4,(a2,d3.w)
.pn:    addq.w  #1,d1
        cmp.w   (a1),d1
        ble.s   .px
        addq.l  #2,a1
.st:    dbf     d0,.sp
        rts

; --- g7f_pf1 --- a0 = palabra de pantalla d0 (0..16) de la fila en el PF1
; (W_PFR ya calculado por g7f_row)
; registros destruidos: d0/a0
g7f_pf1:
        add.w   W_COL0(a6),d0
        cmp.w   #SLOTS,d0
        blo.s   .c
        sub.w   #SLOTS,d0
.c:     add.w   d0,d0
        move.l  W_PFR(a6),a0
        add.w   d0,a0
        rts

; --- g7f_used --- indices del terreno visibles fuera de los efectos
; entrada:  a6 trabajo (W_EM, PF1)
; salida:   W_USED (bits 1..7), W_ORDR (usados ascendentes, luego libres)
; registros destruidos: d0-d7/a0-a5
; ciclos:   ~17 palabras x 150
g7f_used:
        lea     W_EM(a6),a2
        moveq   #0,d7                      ; usados
        moveq   #0,d0
        bsr     g7f_pf1                    ; a0 = palabra 0
        move.l  W_PFR(a6),a3
        lea     2*SLOTS(a3),a3             ; reenganche del anillo
        move.w  W_CAM(a6),d1
        and.w   #15,d1
        moveq   #-1,d5
        lsr.w   d1,d5
        move.w  d5,a4                      ; borde de la palabra 0
        not.w   d5
        move.w  d5,a5                      ; borde de la palabra 16 (s = 0 -> 0)
        moveq   #0,d6                      ; palabra j
.w:     moveq   #-1,d5
        tst.w   d6
        bne.s   .nj0
        move.w  a4,d5
        bra.s   .edge
.nj0:   cmp.w   #16,d6
        bne.s   .edge
        move.w  a5,d5
.edge:  move.w  (a2)+,d0
        not.w   d0
        and.w   d0,d5                      ; m
        beq     .wn
        move.w  (a0),d0                    ; p0
        move.w  ROWB1(a0),d1               ; p1
        move.w  2*ROWB1(a0),d2             ; p2
        move.w  d0,d3
        and.w   d5,d3                      ; a = p0 & m
        not.w   d0
        and.w   d5,d0                      ; na = ~p0 & m
        move.w  d1,d4
        not.w   d4                         ; ~p1
        move.w  d2,a1                      ; p2
        ; t01 = a & ~p1, t11 = a & p1, t00 = na & ~p1, t10 = na & p1
        move.w  d3,d5
        and.w   d4,d5                      ; t01
        and.w   d1,d3                      ; t11
        move.w  d0,d2
        and.w   d4,d2                      ; t00
        and.w   d1,d0                      ; t10
        move.w  a1,d1                      ; p2
        move.w  d1,d4
        not.w   d4                         ; ~p2
        move.w  d5,a1                      ; t01: 1 / 5
        and.w   d4,d5
        beq.s   .r1
        bset    #1,d7
.r1:    move.w  a1,d5
        and.w   d1,d5
        beq.s   .r5
        bset    #5,d7
.r5:    move.w  d3,d5                      ; t11: 3 / 7
        and.w   d4,d5
        beq.s   .r3
        bset    #3,d7
.r3:    and.w   d1,d3
        beq.s   .r7
        bset    #7,d7
.r7:    move.w  d2,d5                      ; t00: 4 (el 0 no cuenta)
        and.w   d1,d5
        beq.s   .r4
        bset    #4,d7
.r4:    move.w  d0,d5                      ; t10: 2 / 6
        and.w   d4,d5
        beq.s   .r2
        bset    #2,d7
.r2:    and.w   d1,d0
        beq.s   .wn
        bset    #6,d7
.wn:    addq.l  #2,a0
        cmpa.l  a3,a0
        bne.s   .nw
        lea     -2*SLOTS(a0),a0
.nw:    addq.w  #1,d6
        cmp.w   #17,d6
        blo     .w
        move.w  d7,W_USED(a6)
        ; orden de prueba: usados ascendentes, despues los libres
        lea     W_ORDR(a6),a0
        moveq   #1,d0
.u:     btst    d0,d7
        beq.s   .un
        move.b  d0,(a0)+
.un:    addq.w  #1,d0
        cmp.w   #8,d0
        blo.s   .u
        moveq   #1,d0
.f:     btst    d0,d7
        bne.s   .fn
        move.b  d0,(a0)+
.fn:    addq.w  #1,d0
        cmp.w   #8,d0
        blo.s   .f
        rts

; --- g7f_cand --- indices r cuyo color es c en todos los pixeles del grupo
; (una pasada por los eventos para los 7 indices a la vez)
; entrada:  d1.w c, d2.w ranura, d3.w x0, d4.w x1 (W_EVT de W_ORG)
; salida:   d0.w mascara (bits 1..7)
; registros destruidos: d0/d3/d5-d7/a0
g7f_cand:
        lea     W_EVT(a6),a0
        move.w  W_NEV(a6),d6               ; eventos restantes
        moveq   #0,d7                      ; malos: color actual != c
        tst.w   d1
        beq.s   .z
        move.w  #$fe,d7                    ; todos empiezan en 0
.z:     move.w  #$fe,d0
        move.w  d3,d5
.px:    cmp.b   W_OV(a6,d5.w),d2
        bne.s   .pn
.adv:   tst.w   d6
        beq.s   .cmp
        cmp.w   (a0),d5
        blt.s   .cmp                       ; evento despues del pixel
        move.w  2(a0),d3
        cmp.w   4(a0),d1
        beq.s   .good
        bset    d3,d7
        bra.s   .nx
.good:  bclr    d3,d7
.nx:    addq.l  #6,a0
        subq.w  #1,d6
        bra.s   .adv
.cmp:   move.w  d7,d3
        not.w   d3
        and.w   d3,d0
        beq.s   .out
.pn:    addq.w  #1,d5
        cmp.w   d4,d5
        ble.s   .px
.out:   rts

; --- g7f_fast --- pasos 1 y 2 (fast_row)
; entrada:  a6 trabajo (orden de colores, W_USED, W_EVT de W_ORG)
; salida:   W_OUT de pixeles resueltos, W_SEG parchado, W_CLM;
;           W_CL/W_NCL: grupos que quedan sin indice, en orden de color
; registros destruidos: d0-d7/a0-a3
g7f_fast:
        move.w  W_USED(a6),W_RES(a6)
        clr.w   W_CLM(a6)
        clr.w   W_NCL(a6)
        lea     W_CL(a6),a3
        moveq   #0,d7                      ; k en W_ORD
.color: cmp.w   W_NS(a6),d7
        bhs     .assign
        lea     W_ORD(a6),a0
        moveq   #0,d2
        move.b  (a0,d7.w),d2               ; ranura
        lea     W_CT(a6),a0
        move.w  d2,d0
        add.w   d0,d0
        move.w  (a0,d0.w),d1               ; c
        move.w  W_XMIN(a6),d3
.seek:  cmp.b   W_OV(a6,d3.w),d2
        beq.s   .start
        addq.w  #1,d3
        cmp.w   W_XMAX(a6),d3
        ble.s   .seek
        bra     .cnext
.start: move.w  d3,d4                      ; ultimo pixel del grupo
        move.w  d3,d5
.grow:  addq.w  #1,d5
        cmp.w   W_XMAX(a6),d5
        bgt.s   .gend
        move.w  d5,d0
        sub.w   d4,d0
        cmp.w   #16,d0
        bgt.s   .gend
        cmp.b   W_OV(a6,d5.w),d2
        bne.s   .grow
        move.w  d5,d4
        bra.s   .grow
.gend:  ; grupo [d3, d4] de la ranura d2, color d1
        movem.l d1-d4/d7,-(sp)
        bsr     g7f_cand
        movem.l (sp)+,d1-d4/d7
        move.w  d0,d6
        beq.s   .miss
        lea     W_ORDR(a6),a1
        moveq   #6,d5
.try:   moveq   #0,d0
        move.b  (a1)+,d0
        btst    d0,d6
        bne.s   .hit
        dbf     d5,.try
.miss:  cmp.w   #48,W_NCL(a6)
        bhs     .many
        move.b  d2,(a3)+                   ; pendiente
        clr.b   (a3)+
        move.w  d3,(a3)+
        move.w  d4,(a3)+
        clr.w   (a3)+
        addq.w  #1,W_NCL(a6)
        bra.s   .after
.hit:   move.w  d3,-(sp)
        bsr     g7f_setout                 ; d0 = r
        move.w  (sp)+,d3
        move.w  W_RES(a6),d5
        bset    d0,d5
        move.w  d5,W_RES(a6)
        move.w  W_CLM(a6),d5
        bset    d0,d5
        move.w  d5,W_CLM(a6)
.after: move.w  d4,d3
        addq.w  #1,d3
        cmp.w   W_XMAX(a6),d3
        ble     .seek
.cnext: addq.w  #1,d7
        bra     .color
        ; indices libres: uno por color pendiente, en orden de color
.assign:
        lea     W_CL(a6),a3
        move.w  W_NCL(a6),d7
        beq     .done
        subq.w  #1,d7
.g:     move.b  (a3),d2                    ; ranura de este grupo
        tst.b   1(a3)
        bne     .gnext                     ; ya tratado con su color
        move.w  W_RES(a6),d5
        moveq   #1,d0
.free:  btst    d0,d5
        beq.s   .got
        addq.w  #1,d0
        cmp.w   #8,d0
        blo.s   .free
        move.l  a3,a0                      ; sin libre: quedan (estado 1)
        move.w  d7,d6
.mark:  cmp.b   (a0),d2
        bne.s   .mk
        move.b  #1,1(a0)
.mk:    addq.l  #8,a0
        dbf     d6,.mark
        bra.s   .gnext
.got:   bset    d0,d5
        move.w  d5,W_RES(a6)
        move.w  W_CLM(a6),d5
        bset    d0,d5
        move.w  d5,W_CLM(a6)
        moveq   #0,d1
        move.b  d2,d1
        add.w   d1,d1
        lea     W_CT(a6),a0
        move.w  (a0,d1.w),d1               ; c
        bsr     g7f_patch                  ; d0 r, d1 c
        move.l  a3,a0
        move.w  d7,d6
.done2: cmp.b   (a0),d2
        bne.s   .dn
        move.b  #2,1(a0)                   ; resuelto
        movem.l d2-d4,-(sp)
        move.w  2(a0),d3
        move.w  4(a0),d4
        bsr     g7f_setout
        movem.l (sp)+,d2-d4
.dn:    addq.l  #8,a0
        dbf     d6,.done2
.gnext: addq.l  #8,a3
        dbf     d7,.g
        ; compactar: quedan los de estado 1, en orden
        lea     W_CL(a6),a0
        move.l  a0,a1
        move.w  W_NCL(a6),d7
        subq.w  #1,d7
        moveq   #0,d6
.cp:    cmp.b   #1,1(a0)
        bne.s   .cpn
        move.l  (a0),(a1)+
        move.l  4(a0),(a1)+
        addq.w  #1,d6
.cpn:   addq.l  #8,a0
        dbf     d7,.cp
        move.w  d6,W_NCL(a6)
.done:  rts
.many:  move.w  #$7fff,W_NCL(a6)           ; mas grupos que W_CL: rechazo
        rts

; --- g7f_setout --- W_OUT = d0 en los pixeles de la ranura d2 entre d3 y d4
; registros destruidos: d3/a1
g7f_setout:
        lea     W_OUT(a6),a1
.p:     cmp.b   W_OV(a6,d3.w),d2
        bne.s   .n
        move.b  d0,(a1,d3.w)
.n:     addq.w  #1,d3
        cmp.w   d4,d3
        ble.s   .p
        rts

; --- g7f_patch --- indice libre r = d0 con color d1 en W_SEG: prefijo, y
; sus recargas del cuerpo pasan a NOP (misma ranura)
; registros destruidos: d3-d5/a1
g7f_patch:
        lea     W_SEG(a6),a1
        move.w  d0,d5
        add.w   d5,d5
        add.w   #$180,d5                   ; registro
        moveq   #0,d3
.w:     cmp.w   (a1),d5
        bne.s   .n
        cmp.w   W_PLEN(a6),d3
        bhs.s   .nop
        move.w  2(a1),d4
        and.w   #$f000,d4
        or.w    d1,d4
        move.w  d4,2(a1)
        bra.s   .n
.nop:   move.l  #$01fe0000,(a1)
.n:     addq.l  #4,a1
        addq.w  #1,d3
        cmp.w   W_NW(a6),d3
        blo.s   .w
        rts

; --- g7f_left --- pasos 3 (ventana) y 3b (EDF) para los grupos sin indice
; entrada:  a6 trabajo tras g7f_fast (W_CL/W_NCL pendientes, W_CLM, W_SEG)
; salida:   d0.l = 0 (W_SEG/W_NW/W_OUT con el plan) o 2|fila<<8
; registros destruidos: d0-d7/a0-a5
g7f_left:
        cmp.w   #$7fff,W_NCL(a6)           ; mas grupos que W_CL
        beq.s   .rej
        cmp.w   #$7fff,W_END(a6)           ; end_of(nb siguiente) = None
        beq.s   .rej
        cmp.w   #G7F_WRAP,W_ROW(a6)
        beq.s   .rej
        bsr     g7f_umask
        ifnd    G7F_NOWIN
        bsr     g7f_window
        tst.l   d0
        beq.s   .ok
        endc
        bsr     g7f_tidx                   ; solo el paso 3b usa W_IDX y W_WANT
        bsr     g7f_want
        bsr     g7f_edf
        tst.l   d0
        beq.s   .ok
.rej:   moveq   #2,d0
        move.w  W_ROW(a6),d1
        lsl.w   #8,d1
        or.w    d1,d0
.ok:    rts

; --- g7f_tidx --- W_IDX = indice del terreno de cada x de la fila (PF1),
; tambien bajo los efectos (el idx de la especificacion)
; registros destruidos: d0-d7/a0-a3
g7f_tidx:
        moveq   #0,d0
        bsr     g7f_pf1                    ; a0 = palabra 0
        move.l  W_PFR(a6),a3
        lea     2*SLOTS(a3),a3             ; reenganche del anillo
        lea     W_IDX(a6),a1
        move.w  W_CAM(a6),d6
        and.w   #15,d6
        neg.w   d6                         ; x del bit 15 de la palabra 0
        moveq   #16,d7
.w:     move.w  (a0),d1
        move.w  ROWB1(a0),d2
        move.w  2*ROWB1(a0),d3
        moveq   #15,d4
.b:     moveq   #0,d5
        add.w   d3,d3
        addx.b  d5,d5
        add.w   d2,d2
        addx.b  d5,d5
        add.w   d1,d1
        addx.b  d5,d5
        cmp.w   #256,d6                    ; sin signo: x < 0 tambien queda fuera
        bhs.s   .s
        move.b  d5,(a1,d6.w)
.s:     addq.w  #1,d6
        dbf     d4,.b
        addq.l  #2,a0
        cmpa.l  a3,a0
        bne.s   .nw
        lea     -2*SLOTS(a0),a0
.nw:    dbf     d7,.w
        rts

; --- g7f_want --- W_WANT = required(): color del efecto, o el del indice
; del terreno con la lista original (W_EVT de W_ORG), o -1
; registros destruidos: d0-d1/d6-d7/a0-a4
g7f_want:
        lea     W_CUR(a6),a2
        clr.l   (a2)
        clr.l   4(a2)
        clr.l   8(a2)
        clr.l   12(a2)
        lea     W_EVT(a6),a0
        move.w  W_NEV(a6),d7
        lea     W_IDX(a6),a3
        lea     W_WANT(a6),a1
        lea     W_CT(a6),a4
        moveq   #0,d6
.x:     tst.w   d7
        beq.s   .px
        cmp.w   (a0),d6
        blt.s   .px                        ; el evento es despues de x
        move.w  2(a0),d0
        add.w   d0,d0
        move.w  4(a0),(a2,d0.w)
        addq.l  #6,a0
        subq.w  #1,d7
        bra.s   .x
.px:    moveq   #0,d0
        move.b  W_OV(a6,d6.w),d0
        beq.s   .ter
        add.w   d0,d0
        move.w  (a4,d0.w),d1
        bra.s   .st
.ter:   move.b  (a3,d6.w),d0
        beq.s   .tr
        add.w   d0,d0
        move.w  (a2,d0.w),d1
        bra.s   .st
.tr:    moveq   #-1,d1
.st:    move.w  d1,(a1)+
        addq.w  #1,d6
        cmp.w   #256,d6
        blo.s   .x
        rts

; --- g7f_umask --- W_UM: por palabra de pantalla j e indice r, los pixeles
; del terreno (fuera de los efectos y de la pantalla) con ese indice
; entrada:  a6 trabajo (W_EM, PF1)
; registros destruidos: d0-d7/a0-a5
; ciclos:   ~17 palabras x 200
g7f_umask:
        lea     W_EM(a6),a2
        lea     W_UM(a6),a5
        moveq   #0,d0
        bsr     g7f_pf1                    ; a0 = palabra 0
        move.l  W_PFR(a6),a3
        lea     2*SLOTS(a3),a3
        move.w  W_CAM(a6),d1
        and.w   #15,d1
        moveq   #-1,d5
        lsr.w   d1,d5
        move.w  d5,a4                      ; borde de la palabra 0
        moveq   #0,d6
.w:     moveq   #-1,d5
        tst.w   d6
        bne.s   .nj0
        move.w  a4,d5
        bra.s   .edge
.nj0:   cmp.w   #16,d6
        bne.s   .edge
        move.w  a4,d5
        not.w   d5
.edge:  move.w  (a2)+,d0
        not.w   d0
        and.w   d0,d5                      ; m
        move.w  (a0),d0                    ; p0
        move.w  ROWB1(a0),d1               ; p1
        move.w  2*ROWB1(a0),d7             ; p2
        move.w  d0,d3
        and.w   d5,d3                      ; a = p0 & m
        not.w   d0
        and.w   d5,d0                      ; na
        move.w  d1,d4
        not.w   d4                         ; ~p1
        move.w  d3,d2
        and.w   d4,d2                      ; t01
        and.w   d1,d3                      ; t11
        move.w  d0,d5
        and.w   d4,d5                      ; t00
        and.w   d1,d0                      ; t10
        move.w  d7,d4
        not.w   d4                         ; ~p2
        move.w  d2,d1
        and.w   d4,d1
        move.w  d1,1*34(a5)                ; 1
        move.w  d0,d1
        and.w   d4,d1
        move.w  d1,2*34(a5)                ; 2
        move.w  d3,d1
        and.w   d4,d1
        move.w  d1,3*34(a5)                ; 3
        and.w   d7,d5
        move.w  d5,4*34(a5)                ; 4
        and.w   d7,d2
        move.w  d2,5*34(a5)                ; 5
        and.w   d7,d0
        move.w  d0,6*34(a5)                ; 6
        and.w   d7,d3
        move.w  d3,7*34(a5)                ; 7
        addq.l  #2,a5
        addq.l  #2,a0
        cmpa.l  a3,a0
        bne.s   .nw
        lea     -2*SLOTS(a0),a0
.nw:    addq.w  #1,d6
        cmp.w   #17,d6
        blo     .w
        rts

; --- g7f_uses --- uso del terreno por indice alrededor de [x0, x1] (W_UM)
; entrada:  d3.w x0, d4.w x1
; salida:   W_UIN, W_UANY (bits 1..7), W_ULO/W_UHI por indice
;           (ultimo uso < x0 o -1, primer uso > x1 o 256)
; registros destruidos: d0-d2/d5-d7/a0-a2
g7f_uses:
        ; mascaras de x < x0 y x > x1 por palabra
        lea     W_ULM(a6),a0
        lea     W_URM(a6),a1
        move.w  W_CAM(a6),d6
        and.w   #15,d6
        neg.w   d6                         ; x del bit 15 de la palabra
        moveq   #16,d7
.mk:    move.w  d3,d0
        sub.w   d6,d0                      ; pixeles < x0 en la palabra
        bgt.s   .l1
        moveq   #0,d1
        bra.s   .l3
.l1:    moveq   #-1,d1
        cmp.w   #16,d0
        bge.s   .l3
        move.w  #$ffff,d1
        lsr.w   d0,d1
        not.w   d1
.l3:    move.w  d1,(a0)+
        move.w  d4,d0
        sub.w   d6,d0
        addq.w  #1,d0                      ; pixeles <= x1
        bgt.s   .r1
        moveq   #-1,d1
        bra.s   .r3
.r1:    moveq   #0,d1
        cmp.w   #16,d0
        bge.s   .r3
        move.w  #$ffff,d1
        lsr.w   d0,d1
.r3:    move.w  d1,(a1)+
        add.w   #16,d6
        dbf     d7,.mk
        ; por indice
        moveq   #0,d5                      ; dentro
        moveq   #0,d7                      ; en la fila
        moveq   #1,d2
.r:     move.w  d2,d0
        add.w   d0,d0
        lea     W_ULO(a6),a1
        move.w  #-1,(a1,d0.w)
        lea     W_UHI(a6),a1
        move.w  #256,(a1,d0.w)
        move.w  d2,d0
        mulu    #34,d0
        lea     W_UM(a6),a0
        add.w   d0,a0                      ; W_UM + 34 r
        move.l  a0,-(sp)
        lea     W_ULM(a6),a1
        lea     W_URM(a6),a2
        moveq   #16,d6
.a:     move.w  (a0)+,d0
        beq.s   .an
        bset    d2,d7
        move.w  (a1),d1
        or.w    (a2),d1
        not.w   d1
        and.w   d0,d1
        beq.s   .an
        bset    d2,d5
.an:    addq.l  #2,a1
        addq.l  #2,a2
        dbf     d6,.a
        btst    d2,d7
        beq     .rx
        ; ultimo uso a la izquierda: palabra mas alta, bit mas bajo
        moveq   #16,d6
.lo:    move.w  -(a0),d0
        and.w   -(a1),d0
        dbne    d6,.lo
        tst.w   d0
        beq.s   .hi
        moveq   #0,d1
.lob:   btst    d1,d0
        bne.s   .lox
        addq.w  #1,d1
        bra.s   .lob
.lox:   bsr.s   .x
        lea     W_ULO(a6),a1
        move.w  d1,(a1,d0.w)
        ; primer uso a la derecha: palabra mas baja, bit mas alto
.hi:    move.l  (sp),a0
        lea     W_URM(a6),a2
        moveq   #16,d6
.hl:    move.w  (a0)+,d0
        and.w   (a2)+,d0
        dbne    d6,.hl
        tst.w   d0
        beq.s   .rx
        neg.w   d6
        add.w   #16,d6                     ; j
        moveq   #15,d1
.hib:   btst    d1,d0
        bne.s   .hix
        subq.w  #1,d1
        bra.s   .hib
.hix:   bsr.s   .x
        lea     W_UHI(a6),a1
        move.w  d1,(a1,d0.w)
.rx:    addq.l  #4,sp
.rn:    addq.w  #1,d2
        cmp.w   #8,d2
        blo     .r
        move.w  d5,W_UIN(a6)
        move.w  d7,W_UANY(a6)
        rts
.x:     neg.w   d1
        add.w   #15,d1                     ; 15 - b
        lsl.w   #4,d6
        add.w   d6,d1
        move.w  W_CAM(a6),d6
        and.w   #15,d6
        sub.w   d6,d1                      ; x = 16 j - s + 15 - b
        move.w  d2,d0
        add.w   d0,d0
        rts

; --- g7f_emit --- escribir el segmento si cambio y encolar los pixeles
; entrada:  a6 trabajo (W_SEG/W_NW, W_TAIL, W_OUT, W_EM)
; salida:   d0.l = 0 o 4|fila<<8 (diario lleno)
; registros destruidos: d0-d7/a0-a5
g7f_emit:
        move.w  W_NW(a6),d0
        cmp.w   W_NO(a6),d0
        bne.s   .write
        lea     W_ORG(a6),a0
        lea     W_SEG(a6),a1
        subq.w  #1,d0
        bmi.s   .queue
.cmp:   cmpm.l  (a0)+,(a1)+
        bne.s   .write
        dbf     d0,.cmp
        bra.s   .queue
.write: moveq   #3,d0
        add.w   W_NW(a6),d0
        move.l  d0,-(sp)                   ; guardar tambien lo que el nuevo pisa
        moveq   #0,d0
        move.w  W_ROW(a6),d0
        move.l  d0,-(sp)
        bsr     _g7b_save_row_far
        addq.l  #8,sp
        tst.l   d0
        bne     .full
        move.w  W_ROW(a6),d0
        bsr     g7f_segaddr
        lea     W_SEG(a6),a1
        move.w  W_NW(a6),d0
        subq.w  #1,d0
        bmi.s   .tl
.cw:    move.l  (a1)+,(a0)+
        dbf     d0,.cw
.tl:    lea     W_TAIL(a6),a1
        move.l  (a1)+,(a0)+
        move.l  (a1)+,(a0)+
        move.l  (a1)+,(a0)+
.queue: moveq   #0,d0
        lea     W_OUT(a6),a4
        lea     g7f_ident(pc),a1
        bsr     g7f_queue
        moveq   #0,d0
        rts
.full:  moveq   #4,d0
        move.w  W_ROW(a6),d1
        lsl.w   #8,d1
        or.w    d1,d0
        rts

; --- g7f_v2 --- camino corto (g7_fast.fast2_row): prefijo canonico y, por
; color ascendente, un indice constante en la fila o uno libre
; entrada:  a6 trabajo (W_OV, W_CT/W_NS/W_ORD, W_EM, W_PFR)
; salida:   d0.l = 0 fila hecha y encolada, -1 no entra (sigue el camino
;           de capas, la lista sin tocar), 4|fila<<8 diario lleno
; registros destruidos: d0-d7/a0-a5
; ciclos:   ~1500 + 20 por palabra del cuerpo (sin libres)
g7f_v2:
        move.w  W_ROW(a6),d0
        bsr     g7f_segaddr
        move.l  a0,a3                      ; segmento en la lista libre
        btst    #0,1(a3)                   ; palabras 0 y 1: WAIT
        beq     .no
        btst    #0,5(a3)
        beq     .no
        lea     8(a3),a1
        move.w  #$182,d1
        moveq   #6,d2
.pre:   cmp.w   (a1),d1                    ; palabras 2..8: $182..$18E
        bne     .no
        addq.l  #4,a1
        addq.w  #2,d1
        dbf     d2,.pre
        bsr     g7f_reloads                ; d3 = indices recargados en el cuerpo
        lea     W_SR(a6),a2
        clr.l   (a2)
        clr.l   4(a2)
        clr.l   8(a2)
        clr.l   12(a2)
        moveq   #0,d4                      ; indices tomados
        moveq   #0,d6                      ; colores sin constante
        lea     W_ORD(a6),a4
        lea     W_NEED(a6),a5
        move.w  W_NS(a6),d7
        subq.w  #1,d7
        bmi     .emit
.col:   moveq   #0,d2
        move.b  (a4)+,d2                   ; ranura
        move.w  d2,d0
        add.w   d0,d0
        lea     W_CT(a6),a0
        move.w  (a0,d0.w),d1               ; c
        lea     10(a3),a0                  ; valor del MOVE de r = 1
        moveq   #1,d0
.r:     btst    d0,d3
        bne.s   .rn
        move.w  (a0),d5
        and.w   #$fff,d5
        cmp.w   d1,d5
        beq.s   .hit
.rn:    addq.l  #4,a0
        addq.w  #1,d0
        cmp.w   #8,d0
        blo.s   .r
        move.b  d2,(a5)+                   ; sin constante: libre despues
        addq.w  #1,d6
        bra.s   .cn
.hit:   move.b  d0,(a2,d2.w)
        bset    d0,d4
.cn:    dbf     d7,.col
        tst.w   d6
        beq     .emit
        ; libres: el terreno no los usa fuera de los efectos
        lea     W_NEED(a6),a5
        lea     W_SR(a6),a2
        move.w  d6,d7
        subq.w  #1,d7
.need:  bsr     g7f_free                   ; d0 = r o 0
        tst.w   d0
        beq     .no                        ; sin libre: nada se escribio
        bset    d0,d4
        moveq   #0,d2
        move.b  (a5)+,d2
        move.b  d0,(a2,d2.w)
        dbf     d7,.need
        ; diario disperso (solo las palabras que cambian) y parche:
        ; pasada 0 arma la lista, pasada 1 escribe
        lea     W_JL(a6),a1
        moveq   #0,d4
.pass:  lea     W_NEED(a6),a5
        lea     W_SR(a6),a2
        move.w  d6,d7
        subq.w  #1,d7
.patch: moveq   #0,d2
        move.b  (a5)+,d2                   ; ranura
        moveq   #0,d0
        move.b  (a2,d2.w),d0               ; r
        add.w   d2,d2
        lea     W_CT(a6),a0
        move.w  (a0,d2.w),d1               ; c
        move.w  d0,d5
        lsl.w   #2,d5
        lea     6(a3,d5.w),a0              ; valor del MOVE de r (palabra 1 + r)
        tst.w   d4
        bne.s   .pv
        move.w  d0,d5
        addq.w  #1,d5
        move.b  d5,(a1)+
        bra.s   .pb
.pv:    move.w  (a0),d5
        and.w   #$f000,d5
        or.w    d1,d5
        move.w  d5,(a0)
.pb:    add.w   d0,d0
        add.w   #$180,d0                   ; registro
        lea     36(a3),a0                  ; palabra 9
        moveq   #9,d5
        move.w  #$84,d2
.nop:   move.w  (a0),d1
        cmp.w   d2,d1
        beq.s   .pn
        cmp.w   d0,d1
        bne.s   .nn
        tst.w   d4
        bne.s   .nv
        move.b  d5,(a1)+
        bra.s   .nn
.nv:    move.l  #$01fe0000,(a0)
.nn:    addq.l  #4,a0
        addq.w  #1,d5
        bra.s   .nop
.pn:    dbf     d7,.patch
        tst.w   d4
        bne.s   .emit
        st      (a1)                       ; fin de la lista
        pea     W_JL(a6)
        moveq   #0,d0
        move.w  W_ROW(a6),d0
        move.l  d0,-(sp)
        bsr     _g7b_save_sparse_far       ; ABI C: d2-d7/a2-a6 intactos
        addq.l  #8,sp
        tst.l   d0
        bne     .full
        moveq   #1,d4
        bra     .pass
.emit:  moveq   #0,d0
        cmp.w   #1,W_NS(a6)
        bne.s   .many
        move.b  W_SR+1(a6),d0              ; un solo color: ranura 1
.many:  lea     W_OV(a6),a4
        lea     W_SR(a6),a1
        bsr     g7f_queue
        moveq   #0,d0
        rts
.no:    moveq   #-1,d0
        rts
.full:  moveq   #4,d0
        move.w  W_ROW(a6),d1
        lsl.w   #8,d1
        or.w    d1,d0
        rts

; --- g7f_free --- el mayor indice r fuera de d4 que el terreno visible no
; usa fuera de los efectos (fast2_row: de 7 a 1). Cada candidato se prueba
; contra el PF1 y se descarta en la primera palabra que lo usa.
; entrada:  d4.w ocupados, W_EM, W_PFR
; salida:   d0.w r o 0
; registros destruidos: d0-d1/d5/a0-a1
g7f_free:
        movem.l d2-d3/d6-d7/a2-a3,-(sp)
        move.w  W_CAM(a6),d1
        and.w   #15,d1
        moveq   #-1,d0
        lsr.w   d1,d0
        move.w  d0,a1                      ; borde de la palabra 0
        moveq   #7,d0
.r:     btst    d0,d4
        bne     .rn
        moveq   #0,d1                      ; x0 = 0 si el bit 0 de r vale 1
        btst    #0,d0
        bne.s   .b0
        not.w   d1
.b0:    moveq   #0,d2
        btst    #1,d0
        bne.s   .b1
        not.w   d2
.b1:    moveq   #0,d3
        btst    #2,d0
        bne.s   .b2
        not.w   d3
.b2:    move.w  d0,-(sp)
        moveq   #0,d0
        bsr     g7f_pf1                    ; a0 = palabra 0
        move.w  (sp)+,d0
        move.l  W_PFR(a6),a3
        lea     2*SLOTS(a3),a3             ; reenganche del anillo
        lea     W_EM(a6),a2
        move.w  a1,d5                      ; palabra 0: borde
        moveq   #15,d7                     ; palabras 1..15 enteras, 16 al final
        bra.s   .m
.w:     moveq   #-1,d5
        tst.w   d7
        bpl.s   .m
        move.w  a1,d5
        not.w   d5                         ; palabra 16 (s = 0 -> 0)
.m:     move.w  (a2)+,d6
        not.w   d6
        and.w   d6,d5                      ; m: visible fuera de efectos
        beq.s   .wn
        move.w  (a0),d6
        eor.w   d1,d6                      ; 1 donde p0 = bit 0 de r
        and.w   d6,d5
        move.w  ROWB1(a0),d6
        eor.w   d2,d6
        and.w   d6,d5
        move.w  2*ROWB1(a0),d6
        eor.w   d3,d6
        and.w   d6,d5
        bne.s   .rn                        ; el terreno usa r
.wn:    addq.l  #2,a0
        cmpa.l  a3,a0
        bne.s   .nw
        lea     -2*SLOTS(a0),a0
.nw:    subq.w  #1,d7
        cmp.w   #-2,d7
        bne.s   .w
        bra.s   .out                       ; r libre
.rn:    subq.w  #1,d0
        bne     .r
.out:   movem.l (sp)+,d2-d3/d6-d7/a2-a3
        rts

; --- g7f_reloads --- indices PF1 que el cuerpo recarga
; entrada:  a1 primera palabra del cuerpo (termina en el salto $84)
; salida:   d3.w bits 1..7
; registros destruidos: d0/d2/d3/a1
g7f_reloads:
        moveq   #0,d3
        move.w  #$84,d2
.w:     move.w  (a1),d0
        cmp.w   d2,d0
        beq.s   .r
        btst    #0,d0                      ; WAIT (con v = 1 empieza por $01xx)
        bne.s   .n
        sub.w   #$182,d0
        cmp.w   #$18e-$182,d0
        bhi.s   .n
        lsr.w   #1,d0
        addq.w  #1,d0
        bset    d0,d3
.n:     addq.l  #4,a1
        bra.s   .w
.r:     rts

; --- g7f_queue --- encolar los pixeles de efecto de la fila (palabras con mascara)
; entrada:  d0.w = r si toda la fila usa un solo indice (0: por pixel),
;           a4 un byte por x de pantalla, a1 su traduccion a indice PF1
;           (16 b; fuera de la mascara puede leer basura, se descarta)
; salida:   cola en G7Q_OFF del banco y _g7b_send
; registros destruidos: d0-d7/a0-a5
g7f_queue:
        tst.w   d0
        bne     .uni
        move.l  W_BANK(a6),a2
        lea     G7Q_OFF(a2),a2
        lea     W_EM(a6),a3
        clr.w   W_NQ(a6)                   ; entradas
        moveq   #0,d6                      ; palabra j
        move.w  W_CAM(a6),d5
        and.w   #15,d5
        suba.w  d5,a4                      ; base + 16 j - s
.j:     move.w  (a3)+,d4                   ; mascara
        beq.s   .jn
        move.l  a4,a5
        moveq   #0,d0
        moveq   #15,d7                     ; 16 pixeles, el primero queda en el bit 15
.b:     move.b  (a5)+,d0
        move.b  (a1,d0.w),d0
        lsr.b   #1,d0
        addx.w  d1,d1
        lsr.b   #1,d0
        addx.w  d2,d2
        lsr.b   #1,d0
        addx.w  d3,d3
        dbf     d7,.b
        and.w   d4,d1                      ; fuera de la mascara: basura
        and.w   d4,d2
        and.w   d4,d3
        move.w  d6,d0
        bsr     g7f_pf1
        move.l  a0,(a2)+
        move.w  d4,(a2)+
        move.w  d4,(a2)+
        move.w  d4,(a2)+
        move.w  d1,(a2)+
        move.w  d2,(a2)+
        move.w  d3,(a2)+
        addq.w  #1,W_NQ(a6)
.jn:    lea     16(a4),a4
        addq.w  #1,d6
        cmp.w   #17,d6
        blo.s   .j
.send:  moveq   #0,d0
        move.w  W_NQ(a6),d0
        beq.s   .ok
        move.l  d0,-(sp)
        bsr     _g7b_send_far
        addq.l  #4,sp
.ok:    rts
.uni:   moveq   #0,d1                      ; un solo indice r = d0: plano = mascara o 0
        btst    #0,d0
        beq.s   .u0
        moveq   #-1,d1
.u0:    moveq   #0,d2
        btst    #1,d0
        beq.s   .u1
        moveq   #-1,d2
.u1:    moveq   #0,d3
        btst    #2,d0
        beq.s   .u2
        moveq   #-1,d3
.u2:    move.l  W_BANK(a6),a2
        lea     G7Q_OFF(a2),a2
        lea     W_EM(a6),a3
        clr.w   W_NQ(a6)
        moveq   #0,d6
.uj:    move.w  (a3)+,d4
        beq.s   .ujn
        move.w  d6,d0
        bsr     g7f_pf1
        move.l  a0,(a2)+
        move.w  d4,(a2)+
        move.w  d4,(a2)+
        move.w  d4,(a2)+
        move.w  d1,d5
        and.w   d4,d5
        move.w  d5,(a2)+
        move.w  d2,d5
        and.w   d4,d5
        move.w  d5,(a2)+
        move.w  d3,d5
        and.w   d4,d5
        move.w  d5,(a2)+
        addq.w  #1,W_NQ(a6)
.ujn:   addq.w  #1,d6
        cmp.w   #17,d6
        blo.s   .uj
        bra.s   .send

; Traduccion identidad (W_OUT ya guarda indices).
g7f_ident:
        dc.b    0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
        even

        include "player/g7edf.s"
        ifnd    G7F_NOWIN
        include "player/g7win.s"
        endc

; Puentes a g7bobs.s (fuera del alcance de bsr, P102). ABI C: pila.
_g7b_save_row_far:
        PICJUMP _g7b_save_row
_g7b_send_far:
        PICJUMP _g7b_send
_g7b_save_sparse_far:
        PICJUMP _g7b_save_sparse

        cnop 0,4
g7f_w:  ds.b    W_SIZE
        even
