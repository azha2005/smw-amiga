; G7-3c: paso 3b del productor (g7_fast.edf_assign / edf_row) en 68000.
; Incluido desde player/g7fast.s (mismo modulo, a6 = g7f_w). Variables
; propias en W_EDF .. W_EDF+2047.

; --- g7f_edf --- paso 3b: indice por color pendiente y cuerpo por plazo
; entrada:  a6 trabajo (ver docs/instrucciones-g7-edf.md)
; salida:   d0.l = 0 (W_SEG/W_NW/W_OUT con el plan) o distinto de 0
; registros destruidos: d0-d7/a0-a5
g7f_edf:
        moveq   #-1,d0                     ; TODO
        rts
