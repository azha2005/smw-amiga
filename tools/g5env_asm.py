#!/usr/bin/env python3
"""Genera el arbol 4bpp del decoder B2bis (codigo, sin datos de la ROM).

Solo masks de 16 bits por columna. El caso de dos columnas conserva dos
mitades por indice; el habitual de Mario usa una palabra y menos memoria.
No se borran las celdas cuyo bit de validez esta apagado.
"""
from pathlib import Path

ORDER = (3, 2, 1, 0)

def dense_mono():
    # Las quince palabras quedan completas, incluso para indices ausentes.
    # MOVEM con predecremento escribe grupos contiguos sin desplazamientos;
    # no hay saltos por color. La frontera calcula la presencia al recortar.
    lines = []
    def emit(s):
        lines.append('        ' + s)
    for prefix in (12, 8, 4, 0):
        if prefix == 0:
            emit('move.w  d2,d4'); emit('or.w    d3,d4'); emit('not.w   d4')
        elif prefix == 4:
            emit('move.w  d3,d4'); emit('not.w   d4'); emit('and.w   d2,d4')
        elif prefix == 8:
            emit('move.w  d2,d4'); emit('not.w   d4'); emit('and.w   d3,d4')
        else:
            emit('move.w  d2,d4'); emit('and.w   d3,d4')
        emit('move.w  d4,d6'); emit('and.w   d1,d6'); emit('eor.w   d6,d4')
        emit('move.w  d4,d5'); emit('and.w   d0,d5')
        if prefix:
            emit('eor.w   d5,d4')
        emit('move.w  d6,d7'); emit('and.w   d0,d7'); emit('eor.w   d7,d6')
        emit('movem.w %s,-(a1)' % ('d4-d7' if prefix else 'd5-d7'))
    return '\n'.join(lines)


def tree(mode):
    lines = []
    def emit(s):
        lines.append('        ' + s)
    def leaf(idx, reg=7):
        if mode == 'mono':
            emit('move.w  d%d,%d(a1)' % (reg, 2 * idx))
        elif mode == 'left':
            emit('move.w  d%d,%d(a1)' % (reg, 4 * idx - 2))
            emit('clr.w   %d(a1)' % (4 * idx))
        else:
            emit('btst    #%d,d4' % idx)
            emit('bne.s   .%s_have%d' % (mode, idx))
            emit('clr.w   %d(a1)' % (4 * idx - 2))
            lines.append('.%s_have%d:' % (mode, idx))
            emit('move.w  d%d,%d(a1)' % (reg, 4 * idx))
        emit('ori.w   #$%04x,d4' % (1 << idx))
    def children(level, prefix, parent):
        plane = ORDER[level]
        reg = 4 + level
        # Dividir una sola vez: positivo = padre & plano; negativo =
        # padre XOR positivo. Los dos conjuntos son disjuntos.
        emit('move.w  d%d,d%d' % (parent, reg))
        emit('and.w   d%d,d%d' % (plane, reg))
        if prefix or level != 3:
            emit('eor.w   d%d,d%d' % (reg, parent))
            label = '.%s_p%d_%d' % (mode, plane, prefix)
            emit('beq.s   ' + label)
            if level != 3:
                children(level + 1, prefix, parent)
            else:
                leaf(prefix, parent)
            lines.append(label + ':')
        idx = prefix | 1 << plane
        label = '.%s_p%d_%d' % (mode, plane, idx)
        emit('tst.w   d%d' % reg)
        emit('beq.s   ' + label)
        if level != 3:
            children(level + 1, idx, reg)
        else:
            leaf(idx, reg)
        lines.append(label + ':')
    # Combinar los dos planos altos libera d4 para el mapa de validez.
    hi, lo = ORDER[:2]
    for bits in range(4):
        prefix = (bits >> 1 << hi) | ((bits & 1) << lo)
        if prefix == 0:
            emit('move.w  d%d,d5' % lo); emit('or.w    d%d,d5' % hi); emit('not.w   d5')
            emit('move.w  d%d,d6' % ORDER[2]); emit('or.w    d%d,d6' % ORDER[3]); emit('and.w   d6,d5')
        elif bits == 1:
            emit('move.w  d%d,d5' % hi); emit('not.w   d5'); emit('and.w   d%d,d5' % lo)
        elif bits == 2:
            emit('move.w  d%d,d5' % lo); emit('not.w   d5'); emit('and.w   d%d,d5' % hi)
        else:
            emit('move.w  d%d,d5' % lo); emit('and.w   d%d,d5' % hi)
        emit('beq.%s   .%s_group%d_end' % ('w' if mode == 'right' else 's', mode, prefix))
        children(2, prefix, 5)
        lines.append('.%s_group%d_end:' % (mode, prefix))
    lines.append('.%s_row_end:' % mode)
    emit('move.w  d4,(a1)')
    return '\n'.join(lines)


HEADER = '''; B2bis: generado por tools/g5env_asm.py, sin datos de la ROM.
; --- _g5env_decode ---
; entrada: pila vbcc +4 = buffer de 4 sprites (84 palabras cada uno),
;          +8 = salida de 2484 B como maximo, alineada a palabra.
; salida: d0 = bytes escritos, $FFFF si cabeceras incompatibles.
;         height.w, columns.w; por fila: masks de indices 1..15.
;         columns=1: 15 masks.w (30 B/fila, todas escritas, cero = ausente).
;         columns=2: indices.w + 15 masks.l (62 B/fila).
;         pixel izquierdo = bit 15/31. En dos columnas solo cuenta el bit valido.
; registros destruidos: d0/d1/a0/a1; preserva d2-d7/a2-a6, incluido a4.
; ciclos: los mide tools/g5env_verify.py decode, Musashi sin DMA.
        ifd SPR_G5
        ifnd G5ENV_N
G5ENV_N equ 8
        endif
; La primera palabra de la clave es n=1..4; cero marca entrada vacia.
; No hace falta una palabra de validez separada.
G5ENV_ENTRY equ 1244
G5ENV_BYTES equ 2484+G5ENV_N*G5ENV_ENTRY
        public _g5env_decode
_g5env_decode:
        move.l  4(sp),a0
        move.l  8(sp),a1
        movem.l d2-d7/a2-a6,-(sp)
        move.l  a1,a6
        move.l  (a0),d0
        bne.s   .first
        lea     336(a0),a0
        move.l  (a0),d0
        bne.s   .one
        clr.l   (a1)
        moveq   #4,d0
        bra.w   .return
.first:
        move.l  336(a0),d1
        beq.s   .one
        ; Ambas columnas de mario_sprite comparten VSTART/VSTOP.
        move.w  (a0),d0
        eor.w   336(a0),d0
        andi.w  #$ff00,d0
        bne.w   .bad
        move.w  2(a0),d0
        eor.w   338(a0),d0
        andi.w  #$ff06,d0
        bne.w   .bad
        bsr.w   .height
        cmpi.w  #40,d1
        bhi.w   .bad
        move.w  d1,(a1)+
        move.w  #2,(a1)+
        move.l  a0,a3
        addq.l  #4,a0
        lea     168(a0),a2
        move.l  a0,a5
        add.w   d1,d1
        add.w   d1,d1
        adda.w  d1,a5
        cmpa.l  a5,a0
        beq.w   .finish_wide
        bra.w   .left_row
.one:
        bsr.w   .height
        cmpi.w  #40,d1
        bhi.w   .bad
        move.w  d1,(a1)+
        move.w  #1,(a1)+
        addq.l  #4,a0
        lea     168(a0),a2
        move.l  a0,a5
        add.w   d1,d1
        add.w   d1,d1
        adda.w  d1,a5
        cmpa.l  a5,a0
        beq.w   .finish
        lea     30(a1),a1
        btst    #2,d1                       ; alto multiplicado por 4: paridad
        bne.w   .mono_second
.mono_row:
.mono_first:
        move.w  (a0)+,d0
        move.w  (a0)+,d1
        move.w  (a2)+,d2
        move.w  (a2)+,d3
'''


def generate():
    text = HEADER + dense_mono() + '''
        lea     60(a1),a1
.mono_second:
        move.w  (a0)+,d0
        move.w  (a0)+,d1
        move.w  (a2)+,d2
        move.w  (a2)+,d3
''' + dense_mono() + '''
.mono_advance:
        lea     60(a1),a1
        cmpa.l  a5,a0
        bne.w   .mono_row
        lea     -30(a1),a1
        bra.w   .finish
.left_row:
        moveq   #0,d4
        move.w  (a0)+,d0
        move.w  (a0)+,d1
        move.w  (a2)+,d2
        move.w  (a2)+,d3
''' + tree('left') + '''
        lea     62(a1),a1
        cmpa.l  a5,a0
        bne.w   .left_row
        ; Segunda columna: solo rellena mitades bajas y suma indices.
        lea     340(a3),a0
        lea     168(a0),a2
        move.l  a0,a5
        move.w  (a6),d1
        add.w   d1,d1
        add.w   d1,d1
        adda.w  d1,a5
        lea     4(a6),a1
.right_row:
        moveq   #0,d4
        move.w  (a1),d4
        move.w  (a0)+,d0
        move.w  (a0)+,d1
        move.w  (a2)+,d2
        move.w  (a2)+,d3
''' + tree('right') + '''
        lea     62(a1),a1
        cmpa.l  a5,a0
        bne.w   .right_row
.finish_wide:
.finish:
        move.l  a1,d0
        sub.l   a6,d0
.return:
        movem.l (sp)+,d2-d7/a2-a6
        rts
.bad:
        move.w  #$ffff,d0
        bra.s   .return
.height:
        moveq   #0,d0
        move.b  (a0),d0
        btst    #2,3(a0)
        beq.s   .vs
        addi.w  #256,d0
.vs:
        moveq   #0,d1
        move.b  2(a0),d1
        btst    #1,3(a0)
        beq.s   .ve
        addi.w  #256,d1
.ve:
        sub.w   d0,d1
        rts
        endif
'''
    # EOR solo admite origen Dn (P73): cargar primero la otra cabecera.
    text = text.replace('eor.w   336(a0),d0', 'move.w  336(a0),d1\n        eor.w   d1,d0')
    text = text.replace('eor.w   338(a0),d0', 'move.w  338(a0),d1\n        eor.w   d1,d0')
    return text.rsplit('        endif', 1)[0] + lookup() + project() + '\n        endif\n'


def project():
    text = '''
        ifd G5ENV_PROJECT
; --- _g5env_project ---
; entrada: pila vbcc +4 bloque B2, +8 sprites de la foto, +12 mascaras;
;          a4 = binstart (tabla g5env_bounds del C, <32 KB, P36).
; salida: vista Mario B2 o pack propio portable (tag $B2); Rex sin tocar.
; registros destruidos: d0/d1/a0/a1; preserva d2-d7/a2-a6.
; ciclos: tools/g5env_verify.py project; recorte ANTES de hallar extremos.
; La columna doble (camino raro del C) usa g5env_bind como control exacto.
        public _g5env_project
_g5env_project:
        move.l  4(sp),a1
        clr.w   10(a1)                     ; formato materializado por defecto
        move.l  8(sp),a0
        movem.l d2-d7/a2-a6,-(sp)
        move.l  56(sp),a2
        move.w  (a2),d2
        bne.s   .visible
        bsr.w   .clear_mask
        clr.w   8(a1)
        bra.w   .return
.visible:
        cmpi.w  #4,2(a2)
        beq.s   .mono
        cmpi.w  #1,2(a2)
        beq.s   .mono
        movem.l (sp)+,d2-d7/a2-a6
        move.l  a4,a0
        add.l   #_g5env_bind-binstart,a0
        jmp     (a0)
.mono:
        move.l  (a0),d0
        bne.s   .pos
        lea     336(a0),a0
.pos:
        moveq   #0,d7
        move.b  (a0),d7
        btst    #2,3(a0)
        beq.s   .vs
        addi.w  #256,d7
.vs:
        subi.w  #44,d7
        move.w  d7,8(a1)
        moveq   #0,d5
        move.b  1(a0),d5
        add.w   d5,d5
        btst    #0,3(a0)
        beq.s   .hs
        addq.w  #1,d5
.hs:
        subi.w  #160,d5
        cmpi.w  #-16,d5
        ble.w   .blank
        cmpi.w  #256,d5
        bge.w   .blank
        moveq   #-1,d3                     ; no convertir si hay recorte
        tst.w   d5
        bmi.s   .recrop
        cmpi.w  #240,d5
        bgt.s   .recrop
        cmpi.w  #4,2(a2)
        beq.w   .warm
        tst.w   d7
        bmi.s   .raw
        move.w  d7,d0
        add.w   d2,d0
        cmpi.w  #224,d0
        bhi.s   .raw
        moveq   #0,d3
        bra.s   .raw
.recrop:
        cmpi.w  #4,2(a2)
        bne.s   .raw
        ; La caja cruzo el borde: los limites pierden los huecos.
        ; Decodificar DATA de la foto en el scratch slow, antes del recorte.
        move.l  a4,a2
        add.l   #g5env_cache-binstart,a2
        move.l  a2,-(sp)
        move.l  56(sp),-(sp)
        bsr.w   _g5env_decode
        addq.l  #8,sp
        move.l  48(sp),a1                   ; decoder destruye a1: recuperar salida
.raw:
        bsr.w   .clear_mask
        move.w  #$ffff,d6
        tst.w   d5
        bpl.s   .right
        move.w  d5,d0
        neg.w   d0
        lsr.w   d0,d6
.right:
        cmpi.w  #240,d5
        ble.s   .clip
        move.w  d5,d0
        subi.w  #240,d0
        lsl.w   d0,d6
.clip:
        ; x*257 traduce las dos coordenadas a la vez. El recorte garantiza
        ; que primer/ultimo+x estan en 0..255, tambien para x negativo.
        move.w  d5,d0
        lsl.w   #8,d5
        add.w   d0,d5
        lea     _g5env_bounds(a4),a3
        lea     12(a1),a6
        lea     92(a1),a1
        lea     4(a2),a0
        lea     -1204(sp),sp
        move.l  sp,a5
        subq.w  #1,d2
.row:
        cmpi.w  #224,d7
        bhs.w   .skip_row                  ; negativo tambien queda fuera
        moveq   #0,d4
        tst.w   d3
        bne.s   .no_pack_row
        move.l  a5,d0
        sub.l   sp,d0
        cmpi.w  #1136,d0                   ; payload <=1200, incluso fila de 64 B
        bls.s   .pack_row
        moveq   #-1,d3                     ; denso excepcional: conservar mascaras
        bra.s   .no_pack_row
.pack_row:
        move.l  a5,a4
        addq.l  #4,a5
.no_pack_row:
'''
    for idx in range(1, 16):
        text += '''        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done{idx}
        tst.b   d0
        bne.s   .low{idx}
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store{idx}
.low{idx}:
        cmpi.w  #255,d0
        bhi.s   .both{idx}
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store{idx}
.both{idx}:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store{idx}:
        tst.w   d3
        bne.s   .translated{idx}
        move.w  #{offset},(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated{idx}:
        add.w   d5,d1
        move.w  d1,{offset}(a1)
        ori.w   #${bit:04x},d4
.done{idx}:
'''.format(idx=idx, offset=2 * (idx - 1), bit=1 << idx)
    text += '''        tst.w   d3
        bne.s   .keep_raw
        move.w  d4,(a4)
        move.l  a5,d0
        sub.l   a4,d0
        lsr.w   #2,d0
        subq.w  #2,d0                      ; contador DBF: pares - 1
        move.w  d0,2(a4)
.keep_raw:
        move.w  d4,(a6)+
        lea     30(a1),a1
        addq.w  #1,d7
        dbf     d2,.row
        tst.w   d3
        bne.w   .mono_return
        move.w  #4,2(a2)
        move.l  sp,a0
        lea     4(a2),a1
        move.l  a5,a6
        bsr.w   .copy_payload
        bra.w   .mono_return
.skip_row:
        lea     30(a0),a0
        lea     30(a1),a1
        addq.l  #2,a6
        addq.w  #1,d7
        dbf     d2,.row
.mono_return:
        lea     1204(sp),sp
        bra.w   .return
.warm:
        ; Copiar el payload disperso y su indice por fila. La frontera
        ; traduce solo el indice solicitado, sin materializar 15 cajas.
        move.w  #$b200,d0
        or.w    d5,d0
        move.w  d0,10(a1)
        lea     4(a2),a0
        lea     12(a1),a6
        lea     92(a1),a1
        moveq   #0,d1
        moveq   #-1,d4
        move.l  d4,d0
        move.l  d4,d3
        move.l  d4,d5
        move.l  d4,d6
        move.l  d4,a3
        move.l  d4,a4
        move.l  d4,a5
        movem.l d0/d3-d6/a3-a5,(a6)
        movem.l d0/d3-d6/a3-a5,32(a6)
        movem.l d0/d3-d5,64(a6)
        subq.w  #1,d2
        tst.w   d7
        bmi.s   .warm_row
        move.w  d7,d0
        add.w   d2,d0
        cmpi.w  #224,d0
        bhs.s   .warm_row
.warm_inside:
        move.w  d1,(a6)+                   ; todas las filas visibles
        move.w  2(a0),d3
        addq.w  #2,d3
        lsl.w   #2,d3
        adda.w  d3,a0
        add.w   d3,d1
        dbf     d2,.warm_inside
        bra.s   .warm_payload
.warm_row:
        move.w  2(a0),d3
        cmpi.w  #224,d7
        bhs.s   .warm_skip
        move.w  d1,(a6)
.warm_skip:
        addq.w  #2,d3
        lsl.w   #2,d3
        adda.w  d3,a0
        add.w   d3,d1
.warm_next:
        addq.l  #2,a6
        addq.w  #1,d7
        dbf     d2,.warm_row
.warm_payload:
        move.l  a0,a6                      ; fin del payload, sobrevive al MOVEM
        lea     4(a2),a0
        bsr.w   .copy_payload
        bra.w   .return
.copy_payload:
        move.l  a6,d2
        sub.l   a0,d2
        lsr.w   #5,d2
        subq.w  #1,d2
        bmi.s   .warm_tail
.warm_copy:
        movem.l (a0)+,d0-d1/d3-d7
        movem.l d0-d1/d3-d7,(a1)
        lea     28(a1),a1
        move.l  (a0)+,(a1)+
        dbf     d2,.warm_copy
.warm_tail:
        move.l  a6,d0
        sub.l   a0,d0
        lsr.w   #1,d0
        subq.w  #1,d0
        bmi.s   .copy_return
.warm_words:
        move.w  (a0)+,(a1)+
        dbf     d0,.warm_words
.copy_return:
        rts
.blank:
        bsr.w   .clear_mask
        bra.w   .return
.clear_mask:
        lea     12(a1),a6
        moveq   #0,d0
        moveq   #19,d1
.clear_next:
        move.l  d0,(a6)+
        dbf     d1,.clear_next
        rts
.return:
        movem.l (sp)+,d2-d7/a2-a6
        rts
        endif
'''
    begin = text.index('.row:\n')
    end = text.index('        tst.w   d3\n        bne.s   .keep_raw', begin)
    body = text[begin:end]
    # Sin recorte se omite el AND por celda y el test de pack.
    import re
    fast = body.replace('        and.w   d6,d0\n', '')
    # d3=0 solo entra cuando la caja entera esta en pantalla. Un overflow
    # salta al camino conservador: estos tests no hacen falta por fila.
    fast = fast.replace('        cmpi.w  #224,d7\n        bhs.w   .skip_row                  ; negativo tambien queda fuera\n', '')
    fast = fast.replace('        tst.w   d3\n        bne.s   .no_pack_row\n', '')
    # Sin recorte, el byte alto original evita el shift de 22 ciclos.
    fast = fast.replace('        lsr.w   #8,d0\n',
                        '        moveq   #0,d0\n        move.b  -2(a0),d0\n')
    fast = fast.replace('        move.w  d0,d1\n        lsr.w   #8,d1\n',
                        '        moveq   #0,d1\n        move.b  -2(a0),d1\n')
    fast = re.sub(r'        tst.w   d3\n        bne.s   \.translated(\d+)\n', '', fast)
    for label in re.findall(r'^\.(\w+):', fast, re.M):
        fast = re.sub(r'\.' + label + r'\b', '.fast_' + label, fast)
    fast += '        bra.w   .pack_epilogue\n'
    fast = fast.replace('        bra.s   .fast_no_pack_row', '        bra.w   .slow_continue')
    text = text[:begin] + '        tst.w   d3\n        beq.w   .fast_row\n' + text[begin:]
    text = text.replace('        tst.w   d3\n        bne.s   .keep_raw', '.pack_epilogue:\n        tst.w   d3\n        bne.s   .keep_raw', 1)
    text = text.replace('        dbf     d2,.row\n        tst.w   d3', '        tst.w   d3\n        bne.s   .slow_advance\n        dbf     d2,.fast_row\n        bra.s   .rows_done\n.slow_advance:\n        dbf     d2,.row\n.rows_done:\n        tst.w   d3', 1)
    text = text.replace('.no_pack_row:', '.no_pack_row:\n.slow_continue:', 1)
    text = text.replace('.return:\n        movem.l', fast + '.return:\n        movem.l', 1)
    return text


def lookup():
    text = '''
; --- _g5env_lookup ---
; entrada: pila vbcc +4 = cache G5ENV_BYTES, +8 = clave 40 B o cero,
;          +12 = sprites de la foto. Cache inicialmente a cero.
; salida: d0 = entrada, cero si invalida; d1 = 1 hit, 0 miss, 2 miss con alias.
; registros destruidos: d0/d1/a0/a1; preserva d2-d7/a2-a6.
; ciclos: tools/g5env_verify.py cache (incluye el decoder en los fallos).
; La tabla directa solo selecciona candidato: se comparan los 40 B siempre.
; Clave alineada: n/entradas 18 B, primer/ultimo byte de punteros,
; interior de punteros 20 B (permutacion sin perdida).
        public _g5env_lookup
_g5env_lookup:
        move.l  a2,-(sp)
        move.l  8(sp),a2
        move.l  12(sp),a0
        move.l  a0,d0
        beq.w   .uncached
        moveq   #0,d0
        move.b  5(a0),d0
        lsr.b   #6,d0
        move.b  21(a0),d1
        lsr.b   #5,d1
        eor.b   d1,d0
        move.b  18(a0),d1
        lsr.b   #6,d1
        eor.b   d1,d0
        add.w   d0,d0
        andi.w  #2*(G5ENV_N-1),d0
        lea     .offsets(pc),a1
        moveq   #0,d1
        move.w  (a1,d0.w),d1                ; P40: indice 0..62
        lea     2484(a2),a2
        adda.l  d1,a2                      ; offset unsigned, N=32 supera 32767
        tst.w   (a2)
        beq.w   .miss
        lea     16(a0),a0
        lea     16(a2),a1
'''
    for i in range(6):
        text += '        cmpm.l  (a0)+,(a1)+\n        bne.s   %s\n' % ('.reject' if i in (0,3) else '.miss')
    text += '''        move.l  a1,d0
        move.l  12(sp),a0
        move.l  a2,a1
'''
    text += '        cmpm.l  (a0)+,(a1)+\n        bne.s   .miss\n' * 4
    text += '''        moveq   #1,d1
        move.l  (sp)+,a2
        rts
.reject:
        bra.w   .cold
.miss:
        tst.w   (a2)
        beq.w   .cold
        move.l  12(sp),a0
        ; Prueba conservadora para las fichas 0..2: solo leen punteros
        ; 0/1/5/6. Comparar 34 B cubre esos cuatro y algunos no usados.
        ; Otros tiles siempre decodifican: nunca se deduce una imagen
        ; de un hash ni se ignora un puntero usado.
        cmpi.w  #2,(a0)
        bhi.w   .cold
        cmpi.b  #2,4(a0)
        bhi.w   .cold
        cmpi.b  #2,8(a0)
        bhi.w   .cold
        move.l  a2,a1
'''
    text += '        cmpm.l  (a0)+,(a1)+\n        bne.w   .cold\n' * 4
    text += '''        cmpm.w  (a0)+,(a1)+
        bne.w   .cold
        move.l  12(sp),a0
        move.l  a2,a1
'''
    # Mismos ocho bytes usados; dos grupos alineados evitan seis CMP.B.
    for off, mask in ((20, 0xffffff00), (28, 0x00ffffff)):
        text += f'''        move.l  {off}(a0),d0
        move.l  {off}(a1),d1
        eor.l   d1,d0
        andi.l  #${mask:08x},d0
        bne.w   .cold
'''
    for off in (18, 32):
        text += f'''        move.b  {off}(a0),d0
        cmp.b   {off}(a1),d0
        bne.w   .cold
'''
    text += '''        move.l  12(sp),a0
        move.l  a2,a1
'''
    text += '        move.l  (a0)+,(a1)+\n' * 10
    text += '''        move.l  a1,d0
        moveq   #2,d1                      ; fallo de clave, igualdad DATA demostrada
        move.l  (sp)+,a2
        rts
.cold:
        move.l  12(sp),a0
        move.l  a2,a1
'''
    text += '        move.l  (a0)+,(a1)+\n' * 10
    text += '''        move.l  a1,-(sp)
        move.l  20(sp),-(sp)               ; buffer de la foto
        bsr.w   _g5env_decode
        addq.l  #8,sp
        cmpi.w  #$ffff,d0
        beq.s   .bad
        lea     40(a2),a0
        move.l  a0,d0
        moveq   #0,d1
        move.l  (sp)+,a2
        rts
.bad:
        clr.w   (a2)
        moveq   #0,d0
        moveq   #0,d1
        move.l  (sp)+,a2
        rts
.uncached:
        move.l  a2,-(sp)
        move.l  20(sp),-(sp)
        bsr.w   _g5env_decode
        addq.l  #8,sp
        cmpi.w  #$ffff,d0
        beq.s   .bad
        move.l  a2,d0
        moveq   #0,d1
        move.l  (sp)+,a2
        rts
.offsets:
        rept G5ENV_N
        dc.w REPTN*G5ENV_ENTRY
        endr
'''
    return text


if __name__ == '__main__':
    Path('player/g5env.s').write_text(generate(), encoding='utf-8')
