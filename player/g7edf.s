; G7-3c (EDF): paso 3b del productor en 68000. Traduccion de
; tools/g7_fast.py: edf_assign, edf_row, reach_early, reach_exact.
; Incluido desde player/g7fast.s (mismo modulo, a6 = g7f_w). Variables
; propias en W_EDF .. W_EDF+1279 (equ E_xxx). Cada decision es la de la
; especificacion y en el mismo orden: colores por x0 del primer grupo,
; candidatos por (ancho desc, r asc), trabajos por (b, a), WAIT/NOP con la
; misma busqueda de h, y la comprobacion final con g7f_scan (= timeline).
;
; Formas equivalentes que usa esta version (no cambian ninguna decision):
;  - un trabajo nace por pixel (su b es ese pixel): b es unico, asi que el
;    orden (b, a) es el de generacion, x ascendente, y no hace falta ordenar;
;  - un grupo pendiente es un cluster completo: sus pixeles son los de su
;    ranura dentro de [x0, x1] (no hay otros pixeles del color en el span);
;  - el uso del terreno por indice (ULO, UHI, UIN) se calcula aqui de W_IDX
;    y W_OV, con la definicion de la especificacion.

E_FIX   equ W_EDF+0        ; 64 x 8 b: x.w, reg.w, valor.w, - (eventos fijos)
E_HV    equ W_EDF+512      ; 8 w primer color de cada indice (-1: sin pixeles)
E_PX    equ W_EDF+528      ; 8 w ultimo pixel con cada indice (edf_row)
E_PV    equ W_EDF+544      ; 8 w color de ese pixel
E_CLS   equ W_EDF+560      ; 16 x 4 b clase de color: primer grupo, grupos
E_CAND  equ W_EDF+624      ; 8 x 4 b candidatos: clave.w (-(hi-lo)), r.w
E_OUT   equ W_EDF+656      ; 256 b out comprometido de edf_assign
E_BEST  equ W_EDF+912      ; 64 l lista comprometida (new de edf_assign)
E_ULO   equ W_EDF+1168     ; 8 w ultimo uso del terreno < x0 (-1)
E_UHI   equ W_EDF+1184     ; 8 w primer uso del terreno > x1 (256)
E_UIN   equ W_EDF+1200     ; .w bits r: uso del terreno dentro de [x0, x1]
E_NFIX  equ W_EDF+1202     ; .w eventos fijos
E_NB    equ W_EDF+1204     ; .w nb del prefijo (copia de W_NB antes de g7f_scan)
E_PLEN  equ W_EDF+1206     ; .w largo del prefijo (copia de W_PLEN)
E_NCLS  equ W_EDF+1208     ; .w clases de color
E_CLM   equ W_EDF+1210     ; .w claimed de edf_assign
E_NJOB  equ W_EDF+1212     ; .w trabajos pendientes
E_T     equ W_EDF+1214     ; .w ranura siguiente (t de edf_row)
E_FIRST equ W_EDF+1216     ; .w 1: el cuerpo no ha empezado
E_FI    equ W_EDF+1218     ; .w indice en E_FIX
E_TN    equ W_EDF+1220     ; .w longs de W_TRY
E_BN    equ W_EDF+1222     ; .w longs de E_BEST
E_RA    equ W_EDF+1224     ; .w a de reach_early
E_RB    equ W_EDF+1226     ; .w b de reach_early
E_RF    equ W_EDF+1228     ; .w encontrado (reach_early)
E_RX    equ W_EDF+1230     ; .w x del MOVE (reach_early)
E_RK    equ W_EDF+1232     ; .w 0 NOP, 1 WAIT (reach_early)
E_RN    equ W_EDF+1234     ; .w n de NOP o h del WAIT (reach_early)
E_RXX   equ W_EDF+1236     ; .w x de reach_exact
E_RT    equ W_EDF+1238     ; .w t de reach_exact
E_XF    equ W_EDF+1240     ; .w encontrado (reach_exact)
E_XK    equ W_EDF+1242     ; .w kind (reach_exact)
E_XN    equ W_EDF+1244     ; .w n o h (reach_exact)
E_NCAND equ W_EDF+1246     ; .w candidatos de la ranura
E_CI    equ W_EDF+1248     ; .w candidato en curso
E_R     equ W_EDF+1250     ; .w indice r en curso
E_CS    equ W_EDF+1252     ; .w primer grupo de la clase en curso
E_CN    equ W_EDF+1254     ; .w grupos de la clase en curso
E_PI    equ W_EDF+1256     ; .w grupo en curso (partes)
E_PEND  equ W_EDF+1258     ; .w fin de las partes
E_K     equ W_EDF+1260     ; .w indice de clase / trabajo
E_ERR   equ W_EDF+1262     ; .w 1: edf_row no cabe (la lista pasa de 61 longs)
E_HASN  equ W_EDF+1264     ; .w hay evento fijo pendiente
E_NX    equ W_EDF+1266     ; .w x del evento fijo pendiente
E_NR    equ W_EDF+1268     ; .w registro del evento fijo
E_NV    equ W_EDF+1270     ; .w valor del evento fijo
E_JA    equ W_EDF+1272     ; .w a del trabajo en curso
E_JB    equ W_EDF+1274     ; .w b del trabajo en curso
E_JR    equ W_EDF+1276     ; .w registro del trabajo
E_JV    equ W_EDF+1278     ; .w valor del trabajo
E_KJ    equ W_EDF+1280     ; .w indice del trabajo en W_JOB (g7e_row; no es E_K)

; --- g7f_edf --- paso 3b: edf_assign de tools/g7_fast.py
; entrada:  a6 trabajo tras g7f_tidx/g7f_want: W_CL/W_NCL, W_OUT, W_OV,
;           W_IDX, W_CLM, W_ORG/W_NO, W_POS/W_NB/W_PLEN (de g7f_scan sobre
;           W_ORG), W_WANT, W_END, W_ROW
; salida:   d0.l = 0: W_SEG/W_NW/W_OUT con el plan; 1: sin plan
; registros destruidos: d0-d7/a0-a5
; ciclos:   medir con tools/g7f_verify.py (Musashi, sin DMA)
g7f_edf:
        ; W_POS/W_NB/W_PLEN son del segmento original: la ventana (g7f_scan
        ; sobre sus listas de prueba) los pisa, asi que se recalculan
        lea     W_ORG(a6),a0
        move.w  W_NO(a6),d0
        bsr     g7f_scan
        move.w  W_NB(a6),E_NB(a6)
        move.w  W_PLEN(a6),E_PLEN(a6)
        move.w  W_CLM(a6),E_CLM(a6)
        bsr     g7e_fix
        bsr     g7e_cls
        bsr     g7e_out
        clr.w   E_K(a6)
.cls:   move.w  E_K(a6),d0
        cmp.w   E_NCLS(a6),d0
        bge.s   .ok
        lsl.w   #2,d0
        lea     E_CLS(a6),a0
        adda.w  d0,a0
        move.w  (a0),E_CS(a6)
        move.w  2(a0),E_CN(a6)
        bsr     g7e_assign
        tst.l   d0
        bne.s   .next
        cmp.w   #1,E_CN(a6)                ; un grupo: no hay partes que probar
        beq.s   .fail
        ; todo el color con un indice fallo: cada grupo con el suyo
        move.w  E_CS(a6),E_PI(a6)
        move.w  E_CS(a6),d0
        add.w   E_CN(a6),d0
        move.w  d0,E_PEND(a6)
.part:  move.w  E_PI(a6),E_CS(a6)
        move.w  #1,E_CN(a6)
        bsr     g7e_assign
        tst.l   d0
        beq.s   .fail
        addq.w  #1,E_PI(a6)
        move.w  E_PI(a6),d0
        cmp.w   E_PEND(a6),d0
        blt.s   .part
.next:  addq.w  #1,E_K(a6)
        bra.s   .cls
.ok:    ; W_SEG = lista comprometida, W_OUT = out comprometido
        move.w  E_BN(a6),W_NW(a6)
        move.w  E_BN(a6),d7
        subq.w  #1,d7
        bmi.s   .ow
        lea     E_BEST(a6),a0
        lea     W_SEG(a6),a1
.cw:    move.l  (a0)+,(a1)+
        dbf     d7,.cw
.ow:    lea     E_OUT(a6),a0
        lea     W_OUT(a6),a1
        moveq   #63,d7
.co:    move.l  (a0)+,(a1)+
        dbf     d7,.co
        moveq   #0,d0
        rts
.fail:  moveq   #1,d0
        rts

; --- g7e_fix --- eventos fijos del cuerpo original (timeline con x >= 0,
; sin MOVE PF1 $182..$18E ni NOP $1FE): E_FIX en orden de palabra
; entrada:  W_ORG, W_POS (g7f_scan sobre W_ORG)
; salida:   E_FIX, E_NFIX
; registros destruidos: d0-d1/d7/a0-a2
g7e_fix:
        clr.w   E_NFIX(a6)
        lea     W_ORG(a6),a0
        lea     W_POS(a6),a1
        lea     E_FIX(a6),a2
        move.w  W_NO(a6),d7
        subq.w  #1,d7
        bmi.s   .d
.l:     move.w  (a1)+,d0                   ; x del MOVE del cuerpo ($8000: no)
        bmi.s   .n
        move.w  (a0),d1                    ; registro
        cmp.w   #$182,d1
        blo.s   .keep
        cmp.w   #$18e,d1
        bls.s   .n                         ; PF1: lo rehace edf_row
.keep:  cmp.w   #$1fe,d1
        beq.s   .n                         ; NOP
        move.w  d0,(a2)+
        move.w  d1,(a2)+
        move.w  2(a0),(a2)+
        addq.l  #2,a2
        addq.w  #1,E_NFIX(a6)
.n:     addq.l  #4,a0
        dbf     d7,.l
.d:     rts

; --- g7e_cls --- clases de color como edf_assign: un grupo por cluster,
; color por primer aparicion en el orden de x0 del primer grupo
; entrada:  W_CL/W_NCL (los grupos de un color son contiguos en W_CL)
; salida:   E_CLS/E_NCLS (ordenadas por x0 del primer grupo)
; registros destruidos: d0-d6/a0-a3
g7e_cls:
        clr.w   E_NCLS(a6)
        moveq   #0,d6                      ; grupo
        moveq   #-1,d5                     ; ranura anterior
.e:     move.w  d6,d0
        lsl.w   #3,d0
        lea     W_CL(a6),a0
        adda.w  d0,a0
        moveq   #0,d4
        move.b  (a0),d4                    ; ranura
        cmp.w   d5,d4
        beq.s   .same
        move.w  E_NCLS(a6),d0
        lsl.w   #2,d0
        lea     E_CLS(a6),a1
        adda.w  d0,a1
        move.w  d6,(a1)+                   ; primer grupo
        clr.w   (a1)                       ; grupos
        addq.w  #1,E_NCLS(a6)
        move.w  d4,d5
.same:  move.w  E_NCLS(a6),d0
        subq.w  #1,d0
        lsl.w   #2,d0
        lea     E_CLS+2(a6),a1
        adda.w  d0,a1
        addq.w  #1,(a1)
        addq.w  #1,d6
        cmp.w   W_NCL(a6),d6
        blo.s   .e
        ; orden por x0 del primer grupo (insercion estable)
        move.w  #1,d6                      ; i
.si:    cmp.w   E_NCLS(a6),d6
        bge.s   .sd
        move.w  d6,d0
        lsl.w   #2,d0
        lea     E_CLS(a6),a0
        adda.w  d0,a0
        move.w  (a0),d1                    ; primer grupo de i
        move.w  2(a0),d2                   ; grupos de i
        move.w  d1,d0
        lsl.w   #3,d0
        lea     W_CL(a6),a1
        adda.w  d0,a1
        move.w  2(a1),d3                   ; clave de i: x0
        move.w  d6,d5                      ; j
.sj:    tst.w   d5
        beq.s   .sput
        move.w  d5,d0
        subq.w  #1,d0
        lsl.w   #2,d0
        lea     E_CLS(a6),a2
        adda.w  d0,a2                      ; clase j-1
        move.w  (a2),d0
        lsl.w   #3,d0
        lea     W_CL(a6),a3
        adda.w  d0,a3
        move.w  2(a3),d0                   ; clave de j-1
        cmp.w   d3,d0
        ble.s   .sput
        move.l  (a2),4(a2)                 ; clase j = clase j-1
        subq.w  #1,d5
        bra.s   .sj
.sput:  move.w  d5,d0
        lsl.w   #2,d0
        lea     E_CLS(a6),a0
        adda.w  d0,a0
        move.w  d1,(a0)+
        move.w  d2,(a0)
        addq.w  #1,d6
        bra.s   .si
.sd:    rts

; --- g7e_out --- out de partida de edf_assign: el indice de W_OUT en los
; efectos resueltos; el del terreno (W_IDX) en el resto y en los grupos
; pendientes
; entrada:  W_OV, W_OUT, W_IDX, W_CL/W_NCL
; salida:   E_OUT
; registros destruidos: d0-d6/a0-a2
g7e_out:
        moveq   #0,d0
.x:     lea     E_OUT(a6),a2
        lea     W_IDX(a6),a1
        tst.b   W_OV(a6,d0.w)
        bne.s   .eff
        move.b  (a1,d0.w),(a2,d0.w)
        bra.s   .xn
.eff:   lea     W_OUT(a6),a1
        move.b  (a1,d0.w),(a2,d0.w)
.xn:    addq.w  #1,d0
        cmp.w   #256,d0
        blo.s   .x
        moveq   #0,d6
.e:     cmp.w   W_NCL(a6),d6
        bhs.s   .d
        move.w  d6,d0
        lsl.w   #3,d0
        lea     W_CL(a6),a0
        adda.w  d0,a0
        moveq   #0,d2
        move.b  (a0),d2                    ; ranura
        move.w  2(a0),d3
        move.w  4(a0),d4
.x2:    cmp.b   W_OV(a6,d3.w),d2
        bne.s   .x2n
        lea     W_IDX(a6),a1
        lea     E_OUT(a6),a2
        move.b  (a1,d3.w),(a2,d3.w)
.x2n:   addq.w  #1,d3
        cmp.w   d4,d3
        ble.s   .x2
        addq.w  #1,d6
        bra.s   .e
.d:     rts

; --- g7e_uses --- uso del terreno por indice respecto de [x0, x1]
; (terreno = W_OV 0 y W_IDX <> 0): ultimo uso < x0, primer uso > x1 y bits
; de los usos dentro
; entrada:  d3.w x0, d4.w x1
; salida:   E_ULO[r] (-1), E_UHI[r] (256), E_UIN (bits 1..7)
; (calculo por mascaras de palabra: g7f_uses sobre W_UM)
; registros destruidos: d0-d2/d5-d7/a0-a2
g7e_uses:
        bsr     g7f_uses
        lea     W_ULO(a6),a0
        lea     E_ULO(a6),a1
        moveq   #7,d0
.c:     move.l  (a0)+,(a1)+                ; W_ULO y W_UHI contiguos: 16 w
        dbf     d0,.c
        move.w  W_UIN(a6),E_UIN(a6)
        rts

; --- g7e_assign --- edf_assign.assign(xs) para la clase (E_CS, E_CN): el
; indice con mas hueco (ancho desc, r asc) que pase edf_row
; entrada:  E_CS, E_CN; E_OUT, E_CLM
; salida:   d0.l = 1: E_OUT/E_BEST/E_CLM comprometidos; 0: sin cambios
; registros destruidos: d0-d7/a0-a5
g7e_assign:
        move.w  E_CS(a6),d0
        lsl.w   #3,d0
        lea     W_CL(a6),a0
        adda.w  d0,a0
        move.w  2(a0),d3                   ; x0 del primer grupo
        move.w  E_CS(a6),d0
        add.w   E_CN(a6),d0
        subq.w  #1,d0
        lsl.w   #3,d0
        lea     W_CL(a6),a0
        adda.w  d0,a0
        move.w  4(a0),d4                   ; x1 del ultimo grupo
        bsr     g7e_uses
        clr.w   E_NCAND(a6)
        moveq   #1,d5
.cr:    move.w  E_CLM(a6),d0
        btst    d5,d0
        bne.s   .crn                       ; ya reclamado
        move.w  E_UIN(a6),d0
        btst    d5,d0
        bne.s   .crn                       ; el terreno lo usa dentro del tramo
        move.w  d5,d0
        add.w   d0,d0
        lea     E_ULO(a6),a1
        move.w  (a1,d0.w),d1               ; lo
        lea     E_UHI(a6),a1
        move.w  (a1,d0.w),d2               ; hi
        sub.w   d1,d2                      ; hi - lo
        neg.w   d2                         ; clave: el mas ancho primero
        bsr     g7e_cins
.crn:   addq.w  #1,d5
        cmp.w   #7,d5
        bls.s   .cr
        clr.w   E_CI(a6)
.cl:    move.w  E_CI(a6),d0
        cmp.w   E_NCAND(a6),d0
        bge.s   .no
        lsl.w   #2,d0
        lea     E_CAND(a6),a0
        adda.w  d0,a0
        move.w  2(a0),E_R(a6)
        bsr     g7e_trial
        move.w  E_R(a6),d5
        bsr     g7e_paint
        bsr     g7e_row
        tst.l   d0
        bne.s   .lose
        bsr     g7e_commit
        moveq   #1,d0
        rts
.lose:  addq.w  #1,E_CI(a6)
        bra.s   .cl
.no:    moveq   #0,d0
        rts

; --- g7e_cins --- inserta (clave d2, r d5) en E_CAND por (clave, r asc)
; registros destruidos: d0/d7/a0
g7e_cins:
        move.w  E_NCAND(a6),d7
.ci:    tst.w   d7
        beq.s   .put
        move.w  d7,d0
        subq.w  #1,d0
        lsl.w   #2,d0
        lea     E_CAND(a6),a0
        adda.w  d0,a0
        cmp.w   (a0),d2                    ; clave contra la existente
        bge.s   .put                       ; existente <= clave
        move.l  (a0),4(a0)                 ; desplazar
        subq.w  #1,d7
        bra.s   .ci
.put:   move.w  d7,d0
        lsl.w   #2,d0
        lea     E_CAND(a6),a0
        adda.w  d0,a0
        move.w  d2,(a0)+
        move.w  d5,(a0)
        addq.w  #1,E_NCAND(a6)
        rts

; --- g7e_paint --- W_OUT2: r (d5) en los pixeles de la clase (E_CS, E_CN),
; o sea los de cada grupo dentro de su span con la ranura del grupo
; entrada:  d5.w r; E_CS, E_CN
; salida:   W_OUT2
; registros destruidos: d0/d2-d4/d6-d7/a0-a1
g7e_paint:
        move.w  E_CS(a6),d6
        move.w  E_CS(a6),d7
        add.w   E_CN(a6),d7
.g:     cmp.w   d7,d6
        bge.s   .d
        move.w  d6,d0
        lsl.w   #3,d0
        lea     W_CL(a6),a0
        adda.w  d0,a0
        moveq   #0,d2
        move.b  (a0),d2                    ; ranura
        move.w  2(a0),d3
        move.w  4(a0),d4
.x:     cmp.b   W_OV(a6,d3.w),d2
        bne.s   .xn
        lea     W_OUT2(a6),a1
        move.b  d5,(a1,d3.w)
.xn:    addq.w  #1,d3
        cmp.w   d4,d3
        ble.s   .x
        addq.w  #1,d6
        bra.s   .g
.d:     rts

; --- g7e_trial --- W_OUT2 = E_OUT (out de partida de la prueba)
; registros destruidos: d0/a0-a1
g7e_trial:
        lea     E_OUT(a6),a0
        lea     W_OUT2(a6),a1
        moveq   #63,d0
.c:     move.l  (a0)+,(a1)+
        dbf     d0,.c
        rts

; --- g7e_commit --- la prueba de r = E_R se queda: E_OUT = W_OUT2, E_BEST =
; W_TRY, E_CLM |= 1 << r
; registros destruidos: d0-d1/a0-a1
g7e_commit:
        lea     W_OUT2(a6),a0
        lea     E_OUT(a6),a1
        moveq   #63,d0
.c:     move.l  (a0)+,(a1)+
        dbf     d0,.c
        move.w  E_TN(a6),E_BN(a6)
        move.w  E_TN(a6),d0
        subq.w  #1,d0
        bmi.s   .cl
        lea     W_TRY(a6),a0
        lea     E_BEST(a6),a1
.b:     move.l  (a0)+,(a1)+
        dbf     d0,.b
.cl:    move.w  E_CLM(a6),d1
        move.w  E_R(a6),d0
        bset    d0,d1
        move.w  d1,E_CLM(a6)
        rts

; --- g7e_row --- edf_row(words, row, idx, overlay, W_OUT2, next_nb): trabajos
; por r, cuerpo por plazo (EDF). Lista candidata en W_TRY (E_TN longs).
; entrada:  W_OUT2 (out de prueba), W_WANT, W_ORG/E_PLEN, E_NB, E_FIX, W_END
; salida:   d0.l = 0 (W_TRY valida), 1 sin plan
; registros destruidos: d0-d7/a0-a5
g7e_row:
        clr.w   E_ERR(a6)
        clr.w   E_NJOB(a6)
        lea     E_HV(a6),a0
        moveq   #7,d0
.hv:    move.w  #-1,(a0)+
        dbf     d0,.hv
        ; trabajos: un barrido por x
        moveq   #0,d6                      ; x
.x:     moveq   #0,d5
        lea     W_OUT2(a6),a0
        move.b  (a0,d6.w),d5               ; r
        beq.s   .xn
        cmp.w   #7,d5
        bhi.s   .xn
        lea     W_WANT(a6),a1
        move.w  d6,d0
        add.w   d0,d0
        move.w  (a1,d0.w),d4               ; color requerido
        bmi.s   .xn                        ; transparente
        move.w  d5,d0
        add.w   d0,d0                      ; 2r
        lea     E_HV(a6),a0
        cmp.w   #-1,(a0,d0.w)
        bne.s   .seen
        move.w  d4,(a0,d0.w)               ; primer pixel del indice
        bra.s   .setp
.seen:  lea     E_PV(a6),a1
        cmp.w   (a1,d0.w),d4
        beq.s   .setp
        ; trabajo: a = ultimo pixel + 1, b = x, reg = $180+2r, valor = color
        move.w  E_NJOB(a6),d3
        cmp.w   #61,d3
        bhs     .fail
        lsl.w   #3,d3
        lea     W_JOB(a6),a2
        adda.w  d3,a2
        lea     E_PX(a6),a3
        move.w  (a3,d0.w),d1
        addq.w  #1,d1
        move.w  d1,(a2)+                   ; a
        move.w  d6,(a2)+                   ; b
        move.w  d0,d1
        add.w   #$180,d1
        move.w  d1,(a2)+                   ; registro
        move.w  d4,(a2)                    ; valor
        addq.w  #1,E_NJOB(a6)
.setp:  lea     E_PX(a6),a3
        move.w  d6,(a3,d0.w)
        lea     E_PV(a6),a1
        move.w  d4,(a1,d0.w)
.xn:    addq.w  #1,d6
        cmp.w   #256,d6
        blo     .x
        ; cabeza: prefijo original con el primer color de cada registro
        lea     W_ORG(a6),a0
        lea     W_TRY(a6),a1
        move.w  E_PLEN(a6),d7
        subq.w  #1,d7
        bmi.s   .hd
.hp:    move.w  (a0)+,d0                   ; w1
        move.w  (a0)+,d1                   ; w2
        cmp.w   #$182,d0
        blo.s   .hn
        cmp.w   #$18e,d0
        bhi.s   .hn
        move.w  d0,d2
        sub.w   #$180,d2                   ; 2r
        lea     E_HV(a6),a2
        move.w  (a2,d2.w),d3
        bmi.s   .hn                        ; sin pixeles del indice
        and.w   #$f000,d1
        or.w    d3,d1
.hn:    move.w  d0,(a1)+
        move.w  d1,(a1)+
        dbf     d7,.hp
.hd:    move.w  E_PLEN(a6),E_TN(a6)
        ; t inicial = T0 + max(0, 16 (nb - 9))
        move.w  E_NB(a6),d0
        sub.w   #9,d0
        bgt.s   .tp
        move.w  #G7F_T0,E_T(a6)
        bra.s   .t1
.tp:    lsl.w   #4,d0
        add.w   #G7F_T0,d0
        move.w  d0,E_T(a6)
.t1:    move.w  #1,E_FIRST(a6)
        clr.w   E_FI(a6)
        ; bucle EDF
.loop:  tst.w   E_ERR(a6)
        bne     .fail
        tst.w   E_NJOB(a6)
        bne.s   .cont
        move.w  E_FI(a6),d0
        cmp.w   E_NFIX(a6),d0
        bge     .done
.cont:  move.w  E_FI(a6),d0
        cmp.w   E_NFIX(a6),d0
        bge.s   .nonx
        lsl.w   #3,d0
        lea     E_FIX(a6),a0
        adda.w  d0,a0
        move.w  (a0),E_NX(a6)
        move.w  2(a0),E_NR(a6)
        move.w  4(a0),E_NV(a6)
        move.w  #1,E_HASN(a6)
        bra.s   .jobs
.nonx:  clr.w   E_HASN(a6)
.jobs:  clr.w   E_KJ(a6)
.jl:    move.w  E_KJ(a6),d0
        cmp.w   E_NJOB(a6),d0
        bge     .nojob
        lsl.w   #3,d0
        lea     W_JOB(a6),a0
        adda.w  d0,a0
        move.w  (a0),E_JA(a6)
        move.w  2(a0),E_JB(a6)
        move.w  4(a0),E_JR(a6)
        move.w  6(a0),E_JV(a6)
        tst.w   E_HASN(a6)
        beq.s   .jin
        move.w  E_JA(a6),d0
        cmp.w   E_NX(a6),d0
        bgt     .jskip                     ; a > x fijo: no cabe antes
.jin:   move.w  E_JB(a6),d1
        cmp.w   W_END(a6),d1
        ble.s   .jb
        move.w  W_END(a6),d1
.jb:    move.w  E_JA(a6),d0
        bsr     g7e_rearly
        tst.w   E_RF(a6)
        bne.s   .jf
        tst.w   E_KJ(a6)
        beq     .fail                      ; el trabajo de plazo mas corto no entra
        bra.s   .jskip
.jf:    tst.w   E_HASN(a6)
        beq.s   .jok
        move.w  E_RX(a6),d0
        cmp.w   E_NX(a6),d0
        bge.s   .jbad                      ; x >= x del fijo
        bsr     g7f_adv
        move.w  E_NX(a6),d1
        moveq   #0,d2
        bsr     g7e_rexact                 ; reach_exact(adv(x), x_fijo, False)
        tst.w   E_XF(a6)
        bne.s   .jok
.jbad:  move.w  E_JB(a6),d0
        cmp.w   E_NX(a6),d0
        blt     .fail                      ; plazo antes del fijo: no hay plan
        bra.s   .jskip
.jok:   bsr     g7e_pre
        move.w  E_JR(a6),d0
        move.w  E_JV(a6),d1
        bsr     g7e_put
        move.w  E_RX(a6),d0
        bsr     g7f_adv
        move.w  d0,E_T(a6)
        clr.w   E_FIRST(a6)
        move.w  E_KJ(a6),d4
        bsr     g7e_rem
        bra     .loop
.jskip: addq.w  #1,E_KJ(a6)
        bra     .jl
.nojob: tst.w   E_HASN(a6)
        beq     .fail                      ; sin fijo y ningun trabajo entra
        tst.w   E_NJOB(a6)
        beq.s   .nj0
        move.w  W_JOB+2(a6),d0             ; b del trabajo de b minimo
        cmp.w   E_NX(a6),d0
        blt     .fail
.nj0:   move.w  E_T(a6),d0
        move.w  E_NX(a6),d1
        move.w  E_FIRST(a6),d2
        bsr     g7e_rexact
        tst.w   E_XF(a6)
        beq     .fail
        move.w  E_XK(a6),E_RK(a6)
        move.w  E_XN(a6),E_RN(a6)
        bsr     g7e_pre
        move.w  E_NR(a6),d0
        move.w  E_NV(a6),d1
        bsr     g7e_put
        move.w  E_NX(a6),d0
        bsr     g7f_adv
        move.w  d0,E_T(a6)
        clr.w   E_FIRST(a6)
        addq.w  #1,E_FI(a6)
        bra     .loop
        ; comprobacion final: ninguna x de la lista pasa de W_END (g7f_scan)
.done:  move.w  E_TN(a6),d0
        cmp.w   #61,d0
        bhi     .fail
        lea     W_TRY(a6),a0
        bsr     g7f_scan                   ; d0 = n
        move.w  E_TN(a6),d7
        subq.w  #1,d7
        bmi.s   .ok
        lea     W_POS(a6),a1
.ck:    move.w  (a1)+,d0
        bmi.s   .ckn
        cmp.w   W_END(a6),d0
        bgt     .fail
.ckn:   dbf     d7,.ck
.ok:    moveq   #0,d0
        rts
.fail:  moveq   #1,d0
        rts

; --- g7e_rearly --- reach_early(E_T, a, b, E_FIRST): la ranura mas temprana
; en [a, b] alcanzable desde t (NOP chain o WAIT con holgura >= IDLE)
; entrada:  d0.w a, d1.w b (ya acotado por el fin)
; salida:   E_RF; E_RX (x del MOVE), E_RK (0 NOP, 1 WAIT), E_RN (n o h)
; registros destruidos: d0-d4/a0-a2
g7e_rearly:
        move.w  d0,E_RA(a6)
        move.w  d1,E_RB(a6)
        clr.w   E_RF(a6)
        tst.w   E_FIRST(a6)
        bne.s   .w
        move.w  E_T(a6),d0
        moveq   #0,d2
.nop:   cmp.w   E_RA(a6),d0
        bge.s   .nd
        cmp.w   #12,d2
        bhs.s   .nd
        bsr     g7f_adv
        addq.w  #1,d2
        bra.s   .nop
.nd:    cmp.w   E_RA(a6),d0
        blt.s   .w
        cmp.w   E_RB(a6),d0
        bgt.s   .w
        move.w  #1,E_RF(a6)
        move.w  d0,E_RX(a6)
        clr.w   E_RK(a6)
        move.w  d2,E_RN(a6)
.w:     move.w  E_T(a6),d0
        bsr     g7f_adv
        bsr     g7f_adv
        move.w  d0,d2                      ; adv(t, 2), no depende de h
        lea     g7f_hx(pc),a2              ; h ascendentes sin x repetidas seguidas
.wl:    move.w  (a2)+,d3
        bmi.s   .rts
        move.w  (a2)+,d0
        cmp.w   d2,d0
        bge.s   .mx
        move.w  d2,d0
.mx:    cmp.w   E_RA(a6),d0
        blt.s   .wn
        cmp.w   E_RB(a6),d0
        bgt.s   .wn
        move.w  d0,d4
        sub.w   E_T(a6),d4
        cmp.w   #G7F_IDLE,d4
        blt.s   .wn
        ; primer h valido: se queda si mejora el NOP (estrictamente)
        tst.w   E_RF(a6)
        beq.s   .set
        cmp.w   E_RX(a6),d0
        bge.s   .rts
.set:   move.w  d0,E_RX(a6)
        move.w  #1,E_RF(a6)
        move.w  #1,E_RK(a6)
        move.w  d3,E_RN(a6)
        rts
.wn:    bra.s   .wl
.rts:   rts

; --- g7e_rexact --- reach_exact(d0 = t, d1 = x, d2 = first): NOP chain que
; cae exacto en x, o WAIT con holgura >= IDLE; desde el borrado, solo WAIT
; entrada:  d0.w t, d1.w x, d2.w first
; salida:   E_XF, E_XK, E_XN
; registros destruidos: d0-d4/a0-a2
g7e_rexact:
        move.w  d1,E_RXX(a6)
        move.w  d0,E_RT(a6)
        clr.w   E_XF(a6)
        tst.w   d2
        bne.s   .w
        moveq   #0,d3
.nop:   cmp.w   E_RXX(a6),d0
        bge.s   .nd
        cmp.w   #12,d3
        bhs.s   .nd
        bsr     g7f_adv
        addq.w  #1,d3
        bra.s   .nop
.nd:    cmp.w   E_RXX(a6),d0
        bne.s   .w
        move.w  #1,E_XF(a6)
        clr.w   E_XK(a6)
        move.w  d3,E_XN(a6)
        rts
.w:     move.w  E_RT(a6),d0
        bsr     g7f_adv
        bsr     g7f_adv
        move.w  d0,d2                      ; adv(t, 2)
        lea     g7f_hx(pc),a2
.wl:    move.w  (a2)+,d3
        bmi.s   .out
        move.w  (a2)+,d0
        cmp.w   d2,d0
        bge.s   .mx
        move.w  d2,d0
.mx:    cmp.w   E_RXX(a6),d0
        bne.s   .wn
        move.w  d0,d4
        sub.w   E_RT(a6),d4
        cmp.w   #G7F_IDLE,d4
        blt.s   .wn
        move.w  #1,E_XF(a6)
        move.w  #1,E_XK(a6)
        move.w  d3,E_XN(a6)
        rts
.wn:    bra.s   .wl
.out:   rts

; --- g7e_pre --- escribe el prefijo de reach (E_RK/E_RN) en W_TRY
; registros destruidos: d0-d1/d2/d3/a0 (d7 se conserva en g7e_put)
g7e_pre:
        tst.w   E_RK(a6)
        bne.s   .wt
        move.w  E_RN(a6),d7
        subq.w  #1,d7
        bmi.s   .r
.nl:    move.w  #$1fe,d0
        moveq   #0,d1
        bsr     g7e_put
        dbf     d7,.nl
        rts
.wt:    move.w  W_ROW(a6),d0
        add.w   #G7F_V0,d0
        and.w   #255,d0
        lsl.w   #8,d0
        or.w    E_RN(a6),d0
        or.w    #1,d0
        move.w  #$fffe,d1
        bsr     g7e_put
.r:     rts

; --- g7e_put --- W_TRY[E_TN] = (d0.w, d1.w); si ya hay 61 longs, E_ERR = 1
; (mas de 61 no cabe: len + 3 <= 64)
; registros destruidos: d2-d3/a0
g7e_put:
        move.w  E_TN(a6),d2
        cmp.w   #61,d2
        blo.s   .ok
        move.w  #1,E_ERR(a6)
        rts
.ok:    move.w  d2,d3
        lsl.w   #2,d3
        lea     W_TRY(a6),a0
        adda.w  d3,a0
        move.w  d0,(a0)+
        move.w  d1,(a0)
        addq.w  #1,E_TN(a6)
        rts

; --- g7e_rem --- quita el trabajo d4 de W_JOB (desplaza los siguientes)
; entrada:  d4.w indice
; registros destruidos: d0/d5-d6/a0-a1
g7e_rem:
        move.w  E_NJOB(a6),d5
        subq.w  #1,d5                      ; ultimo indice
        move.w  d4,d0
        lsl.w   #3,d0
        lea     W_JOB(a6),a0
        adda.w  d0,a0
        move.w  d4,d6
.sh:    cmp.w   d5,d6
        bge.s   .shd
        move.l  8(a0),(a0)
        move.l  12(a0),4(a0)
        addq.l  #8,a0
        addq.w  #1,d6
        bra.s   .sh
.shd:   subq.w  #1,E_NJOB(a6)
        rts
