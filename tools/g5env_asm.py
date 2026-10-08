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
        emit('move.w  d4,d5'); emit('and.w   d0,d5'); emit('eor.w   d5,d4')
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
.mono_row:
.mono_first:
        move.w  (a0)+,d0
        move.w  (a0)+,d1
        move.w  (a2)+,d2
        move.w  (a2)+,d3
'''


def generate():
    text = HEADER + dense_mono() + '''
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
    return text


if __name__ == '__main__':
    Path('player/g5env.s').write_text(generate(), encoding='utf-8')
