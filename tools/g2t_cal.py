#!/usr/bin/env python3
"""Calibración G2T sintética, seis planos y ocho canales DMA activos.

Reutiliza el arnés G0, no cambia el juego. Prueba un sufijo WAIT+colores+
COP2LC/COPJMP2 seguido del borrado; no certifica todas las listas G5.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

from g0bench import Blob, control, rgb, V0
from sprgfx_final import derived_path


def build(out, repair_wrap=False):
    derived_path(str(out))
    cases=[
        dict(name='control sin transición, ocho MOVE',h=0xd0,k=8,load_h=0xc8,load_n=3,last=True,constant=True),
        dict(name='negativo temprano C0, un MOVE',h=0xc0,k=1,load_h=0xb0,load_n=1,last=False,negative=True),
        dict(name='D0, un MOVE, carga B0',h=0xd0,k=1,load_h=0xb0,load_n=1,last=False),
        dict(name='D0, ocho MOVE, color primero',h=0xd0,k=8,load_h=0xc8,load_n=3,last=False),
        dict(name='D0, ocho MOVE, color último',h=0xd0,k=8,load_h=0xc8,load_n=3,last=True),
        dict(name='DE, ocho MOVE, color último',h=0xde,k=8,load_h=0xc8,load_n=3,last=True),
        dict(name='D0 cruza línea PAL255',h=0xd0,k=8,load_h=0xc8,load_n=3,last=True,start=254),
    ]
    b=Blob()
    for reg,value in ((0x8e,0x2ca1),(0x90,0x0ca1),(0x92,0x40),(0x94,0xc0),
                      (0x100,0x6600),(0x102,0),(0x104,0x24),(0x108,(-34)&65535),(0x10a,(-34)&65535)):
        b.move(reg,value)
    for n in range(6):
        b.ptr(0xe0+4*n,'ones' if n==0 else 'zero')
    for n in range(8):
        b.ptr(0x120+4*n,'zero')
    b.move(0x180,0)
    b.move(0x182,0x111)
    for k in range(1,16):
        b.move(0x1a0+2*k,0xf00)
    bits=[]
    for row in range(6):
        for v in range(50+3*row,52+3*row):
            b.wait(v,0x48)
            for _ in range(16):
                bits.append(b.move(0x182,0x0ff))
            b.wait(v,0xd0)
            b.move(0x182,0x111)
    for j,c in enumerate(cases):
        start=c.setdefault('start',80+24*j)
        c['x']=[0,64,128,240]
        b.wait(start-5,0x38)
        b.move(0x1a2,0xf00)
        for ch in range(8):
            b.ptr(0x120+4*ch,'flow%d_%d'%(j,ch&1),4)
            pos,ctl=control(c['x'][ch//2],start,start+4,ch)
            b.move(0x140+8*ch,pos)
            b.move(0x142+8*ch,ctl)
        for r in range(4):
            v=start+r
            b.label('seg%d_%d'%(j,r))
            # Inicio del segmento: 2 WAIT + 7 MOVE PF1, como el juego.
            if v-1==255 and repair_wrap:
                b.move(0x1fe,0)
            elif v-1==255:
                b.wait(255,0xde)  # FFDF, no WAIT tardío imposible (P59).
            else:
                b.words(((v-1)&255)<<8 | 0xe3,0xfffe)
            if v-1==255 and repair_wrap:
                b.move(0x1fe,0)
            else:
                b.words(((v-1)&255)<<8 | (0xdf if v-1==255 else 0xe3),0xfffe)
            for k in range(7):
                b.move(0x182+2*k,0x111 if not k else k)
            b.wait(v,c['load_h'])
            for k in range(c['load_n']):
                b.move(0x184+2*k,k)
            if r<3:
                if v==255 and repair_wrap:
                    # Ensayo explícito de contrato nuevo: la barrera se
                    # consume ANTES del bloque que puede cruzar 255/256.
                    b.wait(255,0xde)
                    b.wrapped=True
                else:
                    b.wait(v,c['h'])
                target=0xf00 if c.get('constant') or (r+1)%2==0 else 0xfff
                for k in range(c['k']):
                    index=1 if (k==c['k']-1 if c['last'] else k==0) else 2+k
                    b.move(0x1a0+2*index,target if index==1 else k)
                b.ptr(0x84,'seg%d_%d'%(j,r+1))
                b.move(0x8a,0)
    b.words(0xffff,0xfffe)
    b.label('ones')
    b.words(*([0xffff]*32))
    b.label('zero')
    b.words(*([0]*32))
    for j,c in enumerate(cases):
        for upper in (0,1):
            b.label('flow%d_%d'%(j,upper))
            b.words(0,0x80 if upper else 0)
            for _ in range(4):
                b.words(0xffff if not upper else 0,0)
            b.words(0,0)
    b.label('end')
    lines=['; G2T sintetico, sin ROM.','G0_NRELOC equ %d'%len(b.reloc),'g0_reloc:']
    lines+=['        dc.l %d,%d'%(p,b.labels[n]+o) for p,n,o in b.reloc]
    for name,offset in (('g0_bits',0),('g0_bits_second',16)):
        lines.append(name+':')
        for row in range(6):
            lines.append('        dc.l '+','.join(str(p) for p in bits[32*row+offset:32*row+offset+16]))
    lines+=['        cnop 0,4','g0_blob:']
    words=struct.unpack('>%dH'%(len(b.data)//2),b.data)
    for p in range(0,len(words),12):
        lines.append('        dc.w '+','.join('$%04x'%w for w in words[p:p+12]))
    lines.append('g0_blob_end:')
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text('\n'.join(lines)+'\n',encoding='ascii')
    out.with_suffix('.json').write_text(json.dumps(dict(cases=cases,chip=len(b.data),repair_wrap=repair_wrap),indent=2),encoding='utf-8')
    source=Path('player/bench_g0.s').read_text(encoding='utf-8')
    source=source.replace('include "work/bench_g0_data.i"','include "'+out.as_posix()+'"')
    out.with_suffix('.s').write_text(source,encoding='utf-8')
    print('%s: %d casos / %d B chip'%(out,len(cases),len(b.data)))
    return b


def read(shot,meta,require_positive=False):
    from PIL import Image,ImageDraw
    im=Image.open(shot).convert('RGB')
    data=json.loads(meta.read_text(encoding='utf-8'))
    def sample(x,v):
        return im.getpixel((131+2*x+1,70+2*(v-V0)+1))
    values=[]
    for row in range(6):
        value=0
        for bit in range(16):
            p=sample(7+16*bit,50+3*row)
            if p not in ((0,0,0),(255,255,255)):
                raise ValueError('barras no publicadas/alineadas')
            value=value*2+(p==(255,255,255))
        values.append(value)
    if values[0]!=0xa55a or not 14000<=values[1]<=14500:
        raise ValueError('sincronía PAL incorrecta: '+str(values))
    reference=Image.new('RGB',(256,224),rgb(0x111))
    actual=Image.new('RGB',(256,224))
    for y in range(224):
        for x in range(256):
            actual.putpixel((x,y),sample(x,V0+y))
    report=[]
    for c in data['cases']:
        errors,background=[],0
        for r in range(4):
            color=0xf00 if c.get('constant') or r%2==0 else 0xfff
            err=0
            for x in range(256):
                sprite=any(xx<=x<xx+16 for xx in c['x'])
                expected=rgb(color if sprite else 0x111)
                reference.putpixel((x,c['start']+r-V0),expected)
                if sample(x,c['start']+r)!=expected:
                    if sprite:
                        err+=1
                    else:
                        background+=1
            errors.append(err)
        row=dict(name=c['name'],errores_sprite_por_fila=errors,errores_fondo=background,
                 negativo=c.get('negative',False))
        report.append(row)
        print(json.dumps(row,ensure_ascii=False))
    sheet=Image.new('RGB',(512,936),(32,32,32))
    draw=ImageDraw.Draw(sheet)
    draw.text((4,2),'Sintético esperado',fill='white')
    sheet.paste(reference.resize((512,448)),(0,20))
    draw.text((4,470),'WinUAE cycle-exact',fill='white')
    sheet.paste(actual.resize((512,448)),(0,488))
    sheet.save(shot.with_name(shot.stem+'_compare.png'))
    result=dict(ticks=values,casos=report,repair_wrap=data['repair_wrap'],
                hardware_alcance='solo este sufijo sintético, no G5')
    shot.with_suffix('.result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    # La calibración informa los casos exploratorios; solo control y
    # negativo temprano son puertas del arnés, nunca se afloja G5.
    if any(report[0]['errores_sprite_por_fila']) or report[0]['errores_fondo']:
        raise SystemExit('FALLA: control')
    if not any(report[1]['errores_sprite_por_fila']):
        raise SystemExit('FALLA: negativo temprano no observado')
    if require_positive and any(any(c['errores_sprite_por_fila']) or c['errores_fondo']
                                for c in report if not c['negativo']):
        raise SystemExit('FALLA: caso positivo de calibración')
    print('ARNÉS: OK; no implica puerta G5.')


# ---------------------------------------------------------------------
# G2T-A, suite ampliada (§3 de instrucciones-g2t-a.md).
#
# Cada caso reproduce un segmento real de scroll.s con SPRITES: borrado de
# nb MOVE (7/8/9), primera carga WAIT $4C (x = 7), cola de cargas real que
# termina en x <= 255, sufijo WAIT + k MOVE de COLOR17-31 y salto de tres
# MOVE. El sprite A (índice 2) llega hasta x = 255 en la fila y y lo cambia
# el PRIMER MOVE del sufijo; el B (índice 1) empieza en x = 0 en la fila
# y + 1 y lo cambia el ÚLTIMO. Así un solo caso prueba los dos bordes. La
# variante F deja el fondo visible en x = 0..7: el último MOVE del borrado
# (COLOR01) y la primera carga (x = 7) también se comprueban en píxeles.
# ---------------------------------------------------------------------
A_COL = [0xf00, 0x0f0, 0xf0f, 0x0ff]
B_COL = [0xff0, 0x00f, 0x888, 0xf80]
BOR = [0x111, 0x222, 0x333, 0x444]
LOAD = [0x500, 0x050, 0x005, 0x550]
TAIL = [0x0a0, 0xa00, 0x00a, 0xaa0]
TAILS = {'T0': [], 'T1': [(0xce, 1)], 'T2': [(0xc0, 3)], 'T3': [(0x90, 9)],
         'T4': [(0x80, 3), (0xa8, 3), (0xc8, 2)], 'T5': [(0x5c, 2)]}
FULL = 0xffff


def htab(x):
    """h del WAIT para que el MOVE caiga en x' >= x (scroll.s htab, 256 px)."""
    if x <= 239:
        return 0x48 + 4 * ((x + 8) >> 3)
    return 0xce if x >= 252 else 0xc4 + ((x - 240) & ~3)


def tail_of(c):
    t = c['tail']
    return TAILS[t] if isinstance(t, str) else [tuple(q) for q in t]


def tail_x(tail):
    """x del último MOVE de la cola según scrollsim (medido hasta 255)."""
    import scrollsim as S
    S.W = 256
    t = S.xh(0x4c)
    for h, n in tail:
        t = max(S.advance(t, 2), S.xh(h))
        t = S.advance(t, n - 1)
    return t


def cap_cases():
    """Capacidad del hueco: k = 0..6 MOVE tras x = 255, borrado 7/8/9.

    T0: copper libre, WAIT $D0. T1W: última carga en x = 255 y WAIT $D0.
    T1N: igual, sin WAIT (el primer MOVE ya cae en x >= 256 por sí solo).
    Variante F: COLOR01 del borrado visible en x = 0..7 y la carga en x = 7.
    """
    pool = []
    for tail, sh, nowait in (('T0', 0xd0, False), ('T1', 0xd0, False), ('T1', 0xd0, True)):
        for nb in (7, 8, 9):
            for k in range(7):
                pool.append(dict(name='cap %s%s nb%d k%d' % (tail, 'N' if nowait else 'W', nb, k),
                                 tail=tail, nb=nb, var='F', sh=sh, k=k, nowait=nowait))
    neg = dict(name='NEG temprano C0 T0', tail='T0', nb=7, var='S', sh=0xc0, k=8, negative=True)
    adfs = []
    for a in range(4):
        cases = [dict(name='VBL arma v30 recorte2', arm=30, clip=2, kind='vbl', start=44)]
        mids = [neg] + pool[17 * a:17 * a + 17]
        for j, c in enumerate(mids):
            cases.append(dict(c, kind='seg', start=73 + 10 * j))
        adfs.append(cases)
    assert sum(len(a) - 2 for a in adfs) == len(pool)
    return adfs


END = {7: 295, 8: 287, 9: 279}      # regla de g2t_ref: último MOVE <= 351 - 8 nb
LOAD_AT = {255: (0xce, 1), 247: (0xc8, 1), 239: (0xc0, 1), 231: (0xbc, 1), 223: (0xb8, 1), 151: (0x94, 1),
           207: (0xb0, 1), 199: (0xac, 1), 183: (0xa4, 1)}


def adv(x, n=1):
    """Como g2t_ref.advance: scrollsim con el paso medido 231 -> 243 (P110)."""
    import scrollsim as S
    S.W = 256
    for _ in range(n):
        x = 243 if x == 231 else S.advance(x)
    return x


def final_cases():
    """Las familias que usan los planes de g2t_ref, en su límite y un paso más.

    Fin: el último MOVE cae en END[nb] (positivo, variantes S y F) o en el
    siguiente (negativo F: la carga x = 7 o el borrado tienen que fallar).
    Principio: el primer MOVE cae justo después del último píxel A
    (positivo) o encima de él (negativo: un píxel).
    """
    pos, neg = [], []
    for nb in (7, 8, 9):
        for t in (255, 247, 239, 231):
            first = adv(t)
            k = 1
            while adv(first, k) <= END[nb]:
                k += 1
            for kk, bad in ((k, False), (k + 1, True)):
                last = adv(first, kk - 1)
                c = dict(name='%sfin cadena c%d nb%d k%d (u%d)' % ('NEG ' if bad else '', t, nb, kk, last),
                         tail=[LOAD_AT[t]], nb=nb, sh=None, nowait=True, k=kk,
                         a_end=min(first, 256) - 1)
                (neg if bad else pos).extend([dict(c, var='F', negative=True)] if bad else
                                             [dict(c, var=v) for v in 'SF'])
        for kk, bad in ((12 - nb, False), (13 - nb, True)):
            c = dict(name='%sfin D0 tras c207 nb%d k%d' % ('NEG ' if bad else '', nb, kk),
                     tail=[LOAD_AT[207]], nb=nb, sh=0xd0, k=kk, a_end=255)
            (neg if bad else pos).extend([dict(c, var='F', negative=True)] if bad else
                                         [dict(c, var=v) for v in 'SF'])
        first = 243
        k = 1
        while adv(first, k) <= END[nb]:
            k += 1
        for kk, bad in ((k, False), (k + 1, True)):
            c = dict(name='%sfin WAIT C4 nb%d k%d (u%d)' % ('NEG ' if bad else '', nb, kk, adv(first, kk - 1)),
                     tail='T5', nb=nb, sh=0xc4, k=kk, a_end=242)
            (neg if bad else pos).extend([dict(c, var='F', negative=True)] if bad else
                                         [dict(c, var=v) for v in 'SF'])
    # Principio: cadenas en pantalla, con NOP y WAIT con 48 px libres.
    for t, nop in ((183, 0), (223, 0), (239, 0), (247, 0), (199, 3), (151, 4)):
        first = adv(t, 1 + nop)
        for bad in (False, True):
            neg_or_pos = neg if bad else pos
            neg_or_pos.append(dict(name='%sprincipio cadena c%d nop%d (x%d)' % ('NEG ' if bad else '', t, nop, first),
                                   tail=[LOAD_AT[t]], nb=7, sh=None, nowait=True, nop=nop, k=4,
                                   a_end=first if bad else first - 1, var='S', negative=bad))
    # WAIT con el copper libre: 48 px tras una carga en 183, o tras la de x = 7.
    for t, h in ((183, 0xbc), (7, 0x7c)):
        x = 8 * ((h - 0x48) >> 2) - 1
        for bad in (False, True):
            (neg if bad else pos).append(dict(
                name='%sprincipio WAIT %02X tras c%d (x%d)' % ('NEG ' if bad else '', h, t, x),
                tail=[LOAD_AT[t]] if t in LOAD_AT else 'T0', nb=7, sh=h, k=4,
                a_end=x if bad else x - 1, var='S', negative=bad))
    # Colas reales de las listas (realtails), cadena hasta el límite nb 7.
    for seq in (((0x68, 1), (0x90, 2), (0xce, 1)), ((0x88, 3), (0xc0, 3)),
                ((0x80, 4), (0xc0, 3)), ((0xa0, 1), (0xb8, 4))):
        for v in 'SF':
            pos.append(dict(name='cola real %s nb7 k5 %s' % ('+'.join('%02X.%d' % q for q in seq), v),
                            tail=[list(q) for q in seq], nb=7, sh=None, nowait=True, k=5, a_end=255, var=v))
    return pos, neg


def final_suite():
    pos, neg = final_cases()
    vbl = [dict(name='VBL arma v30 recorte2', arm=30, clip=2),
           dict(name='VBL arma v26 recorte0', arm=26, clip=0),
           dict(name='VBL arma v27 recorte3', arm=27, clip=3),
           dict(name='NEG VBL arma v16 recorte0', arm=16, clip=0, negative=True)]
    adfs, a = [], 0
    while pos or neg:
        cases = [dict(vbl[a % 4], kind='vbl', start=44)]
        mids = []
        # Cada captura lleva negativos y positivos en la misma tanda.
        # 18 casos: el último termina en v = 246, sin cruzar la línea 255.
        while len(mids) < 18 and (pos or neg):
            src = neg if neg and (len(mids) % 3 == 0 or not pos) else pos
            mids.append(src.pop(0))
        for j, c in enumerate(mids):
            cases.append(dict(c, kind='seg', start=73 + 10 * j))
        adfs.append(cases)
        a += 1
    return adfs


PROBE = [0xf00, 0x0f0, 0x00f, 0xff0, 0x0ff, 0xf0f, 0xfff, 0x888]


def knee_suite():
    """Medida directa: dónde cae cada MOVE de una cadena tras WAIT h (COLOR01).

    Sin sprites a la derecha de x = 64: el fondo muestra cada escritura.
    nop = MOVE nulos ($1FE) entre el WAIT y la primera escritura visible.
    """
    probes = []
    for h in (0x74, 0x78, 0x7c, 0x80, 0xa0, 0xa4, 0xa8, 0xac, 0xb0, 0xb4, 0xb8, 0xbc, 0xc0, 0xc4,
              0xc8, 0xcc, 0xce):
        probes.append(dict(name='sonda WAIT %02X x6' % h, probe=[h, 0, 6]))
    for h, nop in ((0xa4, 2), (0xac, 3), (0xb0, 1), (0xb4, 2), (0xb8, 1), (0xbc, 1), (0x94, 4)):
        probes.append(dict(name='sonda WAIT %02X nop%d x4' % (h, nop), probe=[h, nop, 4]))
    adfs = []
    for a in range(0, len(probes), 18):
        cases = [dict(name='VBL arma v30 recorte2', arm=30, clip=2, kind='vbl', start=44)]
        for j, c in enumerate(probes[a:a + 18]):
            cases.append(dict(c, kind='seg', start=73 + 10 * j, tail='T0', nb=7, var='F', sh=None, k=0))
        adfs.append(cases)
    return adfs


def suite_cases(suite='main'):
    """Lista de casos de las capturas de la suite; cada uno sabe su ADF."""
    if suite == 'cap':
        return cap_cases()
    if suite == 'final':
        return final_suite()
    if suite == 'knee':
        return knee_suite()
    hb = []
    for tail in ('T0', 'T1', 'T2', 'T3', 'T4'):
        for nb in (7, 8, 9):
            for var in ('S', 'F'):
                hb.append(dict(name='D0 %s nb%d %s k8' % (tail, nb, var), tail=tail, nb=nb,
                               var=var, sh=0xd0, k=8))
    mid = []
    for xl in (100, 175, 239, 247, 254):
        for tail in ('T0', 'T5'):
            mid.append(dict(name='medio x%d %s nb9 k8' % (xl, tail), tail=tail, nb=9, var='S',
                            sh=htab(xl + 1), k=8, xlast=xl))
    chk = [dict(name='cola %s comprobada' % t, tail=t, nb=7, var='F', sh=None, k=0,
                check_tail=True) for t in ('T1', 'T2', 'T3', 'T4')]
    neg = [dict(name='NEG temprano C0 T0', tail='T0', nb=7, var='S', sh=0xc0, k=8, negative=True),
           dict(name='NEG medio x175 una celda antes', tail='T0', nb=9, var='S',
                sh=htab(176) - 4, k=8, xlast=175, negative=True),
           dict(name='NEG medio x247 una celda antes', tail='T0', nb=9, var='S',
                sh=htab(248) - 4, k=8, xlast=247, negative=True),
           dict(name='NEG tarde: B tras la carga x7', tail='T0', nb=7, var='S', sh=0xd0, k=8,
                late=True, negative=True)]
    wrap = [dict(name='PAL255 %s %s' % (t, v), tail=t, nb=7, var=v, sh=0xd0, k=8, wrap=True)
            for t, v in (('T1', 'S'), ('T1', 'F'), ('T3', 'S'), ('T3', 'F'))]
    vbl = [dict(name='VBL arma v30 recorte2', arm=30, clip=2),
           dict(name='VBL arma v26 recorte0', arm=26, clip=0),
           dict(name='VBL arma v30 recorte0', arm=30, clip=0),
           dict(name='VBL arma v27 recorte3', arm=27, clip=3),
           dict(name='NEG VBL arma v16 recorte0', arm=16, clip=0, negative=True)]
    pool = hb + mid + chk
    adfs = []
    for a in range(5):
        cases = [dict(vbl[a], kind='vbl', start=44)]
        # La captura del negativo VBL lleva además un positivo de control.
        mids = [neg[a]] if a < 4 else [dict(hb[2], name='control ' + hb[2]['name'])]
        while len(mids) < 18 and pool:
            mids.append(pool.pop(0))
        for j, c in enumerate(mids):
            cases.append(dict(c, kind='seg', start=73 + 10 * j))
        if a < 4:
            cases.append(dict(wrap[a], kind='seg', start=254))
        adfs.append(cases)
    assert not pool, 'la suite no cabe en cinco capturas'
    return adfs


def sprites_of(c):
    """[(pareja, x, índice, máscaras por fila)]; P0 gana a P3 (prioridad)."""
    if c['kind'] == 'vbl':
        rows = 4 + c['clip']
        pats = lambda p: [(0xffff >> ((r + p) % 5)) & ~(1 << ((r * 3 + p) % 16)) & FULL
                          for r in range(rows)]
        out = [(p, 8 + 64 * p, 1 + (p & 1), pats(p)) for p in range(4)]
        if c.get('negative'):
            # Fila 0 transparente: si el DMA la lee como POS/CTL (armado antes
            # de su lectura) el canal queda en (0,0), sin basura en las barras.
            for _, _, _, masks in out:
                masks[0] = 0
        return out
    if 'probe' in c:
        return [(0, 0, 1, [0x00ff] * 4)]
    if 'a_end' in c:
        p0 = FULL if c['var'] == 'S' else 0x00ff
        return [(0, 0, 1, [p0] * 4), (1, 64, 1, [FULL] * 4), (2, 128, 1, [FULL] * 4),
                (3, c['a_end'] - 15, 2, [FULL] * 4)]
    if 'xlast' in c:
        xl = c['xlast']
        return [(0, 0, 1, [FULL] * 4), (1, 24, 1, [FULL] * 4), (2, 48, 1, [FULL] * 4),
                (3, xl - 15, 2, [FULL] * 4)]
    p0 = FULL if c['var'] == 'S' else 0x00ff
    p3x = 176 if c.get('check_tail') else 240
    return [(0, 0, 1, [p0] * 4), (1, 64, 1, [FULL] * 4), (2, 128, 2, [FULL] * 4),
            (3, p3x, 2, [FULL] * 4)]


def flow_words(index, masks, upper):
    words = [0, 0]
    for m in masks:
        lo, hi = (index >> (2 if upper else 0)) & 1, (index >> (3 if upper else 1)) & 1
        words += [m if lo else 0, m if hi else 0]
    return words + [0, 0]


def row_of(c, index, r):
    """Fila cuyos colores tiene el índice: cambian solo si el sufijo los escribe."""
    if c['kind'] == 'vbl':
        return 0
    k = c.get('k', 0)
    if c.get('check_tail') or (k >= 1 if index == 2 else k >= 2 or c.get('late')):
        return r
    return 0


def suffix_moves(c, r):
    k = c['k']
    if k == 0:
        return []
    moves = [(0x1a4, A_COL[r + 1])]
    if k >= 2:
        moves += [(0x1a6 + 2 * j, 0x123) for j in range(k - 2)]
        if not c.get('late'):
            moves.append((0x1a2, B_COL[r + 1]))
    return moves


def expected_row(c, r, sprites):
    """Colores esperados (256) de la fila r del caso; None = no se compara."""
    row = []
    tx = tail_x(tail_of(c)) if c.get('check_tail') else 999
    for x in range(256):
        color = None
        for p, sx, index, masks in sprites:
            mr = r + c.get('clip', 0)
            if sx <= x < sx + 16 and masks[mr] >> (15 - (x - sx)) & 1:
                color = (A_COL if index == 2 else B_COL)[row_of(c, index, r)]
                break
        if color is None:
            if c['kind'] == 'vbl':
                color = 0x111
            else:
                color = TAIL[r] if x >= tx else LOAD[r] if x >= 7 else BOR[r]
        row.append(color)
    return row


def build_suite(out, adf, suite='main'):
    derived_path(str(out))
    cases = suite_cases(suite)[adf]
    b = Blob()
    for reg, value in ((0x8e, 0x2ca1), (0x90, 0x0ca1), (0x92, 0x40), (0x94, 0xc0),
                       (0x100, 0x6600), (0x102, 0), (0x104, 0x24), (0x108, (-34) & 65535),
                       (0x10a, (-34) & 65535)):
        b.move(reg, value)
    for n in range(6):
        b.ptr(0xe0 + 4 * n, 'ones' if n == 0 else 'zero')
    # Como la cabecera del juego: los ocho punteros al sprite nulo.
    for n in range(8):
        b.ptr(0x120 + 4 * n, 'zero')
    # Audio DMA en sus ranuras fijas (silencio): todos los DMA del juego.
    for ch in range(4):
        b.ptr(0xa0 + 16 * ch, 'zero')
        b.move(0xa4 + 16 * ch, 2)
        b.move(0xa6 + 16 * ch, 124)
        b.move(0xa8 + 16 * ch, 0)
    b.move(0x180, 0)
    b.move(0x182, 0x111)
    for k in range(1, 16):
        b.move(0x1a0 + 2 * k, 0x777)

    def arm(c, j):
        vs = c['start']
        for p, sx, index, masks in sprites_of(c):
            for upper in (0, 1):
                ch = 2 * p + upper
                b.ptr(0x120 + 4 * ch, 'flow%d_%d' % (j, ch), 4 + 4 * c.get('clip', 0))
                pos, ctl = control(sx, vs, vs + 4, ch)
                b.move(0x140 + 8 * ch, pos)
                b.move(0x142 + 8 * ch, ctl)
        b.move(0x1a4, A_COL[0])
        b.move(0x1a2, B_COL[0])

    bits = []

    def bars():
        for row in range(6):
            for v in range(50 + 3 * row, 52 + 3 * row):
                b.wait(v, 0x48)
                for _ in range(16):
                    bits.append(b.move(0x182, 0x0ff))
                b.wait(v, 0xd0)
                b.move(0x182, 0x111)

    for j, c in enumerate(cases):
        if c['kind'] == 'vbl':
            b.wait(c['arm'], 0)
            arm(c, j)
            bars_done = False
            continue
        if not bars_done:
            bars()
            bars_done = True
        tail = tail_of(c)
        b.wait(c['start'] - 5, 0x38)
        arm(c, j)
        for r in range(4):
            v = c['start'] + r
            b.label('seg%d_%d' % (j, r))
            prev_wrapped = c.get('wrap') and v - 1 == 255
            if prev_wrapped:
                # La barrera ya se consumió en el sufijo de la 255.
                b.move(0x1fe, 0)
                b.move(0x1fe, 0)
            else:
                b.words(((v - 1) & 255) << 8 | 0xe3, 0xfffe)
                b.words(((v - 1) & 255) << 8 | 0xe3, 0xfffe)
            # Borrado: PF1 3..7, extras PF2 y COLOR01 el último (se ve en x 0..6).
            for k in range(2, 8):
                b.move(0x182 + 2 * (k - 1), k)
            for k in range(c['nb'] - 7):
                b.move(0x192 + 2 * k, 0)
            b.move(0x182, BOR[r])
            b.wait(v, 0x4c)
            b.move(0x182, LOAD[r])
            if c.get('late') and r > 0:
                b.move(0x1a2, B_COL[r])
            if 'probe' in c:
                h, nop, cnt = c['probe']
                b.wait(v, h)
                for _ in range(nop):
                    b.move(0x1fe, 0)
                for q in range(cnt):
                    b.move(0x182, PROBE[q])
            for n, (h, cnt) in enumerate(tail):
                b.wait(v, h)
                for k in range(cnt):
                    last = n == len(tail) - 1 and k == cnt - 1
                    if last and c.get('check_tail'):
                        b.move(0x182, TAIL[r])
                    else:
                        b.move(0x186 + 2 * (k % 6), k)
            if r < 3:
                if c['k']:
                    if c.get('wrap') and v == 255:
                        b.wait(255, 0xde)
                        b.wrapped = True
                    elif not c.get('nowait'):
                        b.wait(v, c['sh'])
                    for _ in range(c.get('nop', 0)):
                        b.move(0x1fe, 0)
                    for reg, val in suffix_moves(c, r):
                        b.move(reg, val)
                elif c.get('check_tail'):
                    b.wait(v, 0xd0)
                    b.move(0x1a4, A_COL[r + 1])
                    b.move(0x1a2, B_COL[r + 1])
                b.ptr(0x84, 'seg%d_%d' % (j, r + 1))
                b.move(0x8a, 0)
            elif c.get('wrap') and v == 255:
                b.wrapped = True
    if not bars_done:
        bars()
    b.words(0xffff, 0xfffe)
    b.label('ones')
    b.words(*([0xffff] * 32))
    b.label('zero')
    b.words(*([0] * 32))
    for j, c in enumerate(cases):
        for p, sx, index, masks in sprites_of(c):
            for upper in (0, 1):
                b.label('flow%d_%d' % (j, 2 * p + upper))
                b.words(*flow_words(index, masks, upper))
    lines = ['; G2T-A sintetico %d, sin ROM.' % adf, 'G0_NRELOC equ %d' % len(b.reloc), 'g0_reloc:']
    lines += ['        dc.l %d,%d' % (p, b.labels[n] + o) for p, n, o in b.reloc]
    for name, offset in (('g0_bits', 0), ('g0_bits_second', 16)):
        lines.append(name + ':')
        for row in range(6):
            lines.append('        dc.l ' + ','.join(str(p) for p in bits[32 * row + offset:32 * row + offset + 16]))
    lines += ['        cnop 0,4', 'g0_blob:']
    words = struct.unpack('>%dH' % (len(b.data) // 2), b.data)
    for p in range(0, len(words), 12):
        lines.append('        dc.w ' + ','.join('$%04x' % w for w in words[p:p + 12]))
    lines.append('g0_blob_end:')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines) + '\n', encoding='ascii')
    out.with_suffix('.json').write_text(json.dumps(dict(adf=adf, suite=suite, cases=cases, chip=len(b.data)), indent=2),
                                        encoding='utf-8')
    source = Path('player/bench_g0.s').read_text(encoding='utf-8')
    source = source.replace('include "work/bench_g0_data.i"', 'include "' + out.as_posix() + '"')
    old = 'move.w #$83e0,DMACON(a4)'
    if old not in source:
        raise SystemExit('bench_g0.s cambió: no encuentro DMACON')
    source = source.replace(old, 'move.w #$83ef,DMACON(a4)')   # + AUD0-3
    out.with_suffix('.s').write_text(source, encoding='utf-8')
    print('%s: ADF %d, %d casos / %d B chip' % (out, adf, len(cases), len(b.data)))


def read_suite(shot, meta):
    from PIL import Image, ImageDraw
    im = Image.open(shot).convert('RGB')
    data = json.loads(meta.read_text(encoding='utf-8'))

    def sample(x, v):
        return im.getpixel((131 + 2 * x + 1, 70 + 2 * (v - V0) + 1))
    values = []
    for row in range(6):
        value = 0
        for bit in range(16):
            p = sample(7 + 16 * bit, 50 + 3 * row)
            if p not in ((0, 0, 0), (255, 255, 255)):
                raise SystemExit('FALLA: barras no publicadas/alineadas')
            value = value * 2 + (p == (255, 255, 255))
        values.append(value)
    if values[0] != 0xa55a or not 14000 <= values[1] <= 14500:
        raise SystemExit('FALLA: sincronía PAL incorrecta: ' + str(values))
    reference = Image.new('RGB', (256, 224), (40, 40, 40))
    actual = Image.new('RGB', (256, 224))
    for y in range(224):
        for x in range(256):
            actual.putpixel((x, y), sample(x, V0 + y))
    report, ok = [], True
    for c in data['cases']:
        if 'probe' in c:
            land = []
            for r in range(4):
                seen = [sample(x, c['start'] + r) for x in range(256)]
                land.append([next((x for x in range(16, 256) if seen[x] == rgb(col)), None)
                             for col in PROBE[:c['probe'][2]]])
            row = dict(name=c['name'], sonda=c['probe'], x=land[0],
                       puerta='OK' if all(l == land[0] for l in land) else 'FALLA: filas distintas')
            ok &= row['puerta'] == 'OK'
            report.append(row)
            print(json.dumps(row, ensure_ascii=True))
            continue
        sprites = sprites_of(c)
        spr_err, bg_err, first = [], 0, None
        for r in range(4):
            want = expected_row(c, r, sprites)
            e = 0
            for x, color in enumerate(want):
                v = c['start'] + r
                reference.putpixel((x, v - V0), rgb(color))
                if sample(x, v) != rgb(color):
                    cover = any(sx <= x < sx + 16 and m[r + c.get('clip', 0)] >> (15 - (x - sx)) & 1
                                for _, sx, _, m in sprites)
                    if cover:
                        e += 1
                    else:
                        bg_err += 1
                    if first is None:
                        first = dict(fila=r, x=x, esperado='%03x' % color,
                                     visto='%02x%02x%02x' % sample(x, v))
            spr_err.append(e)
        bad = any(spr_err) or bg_err
        row = dict(name=c['name'], errores_sprite_por_fila=spr_err, errores_fondo=bg_err,
                   negativo=c.get('negative', False), primer_error=first)
        if c['kind'] == 'seg':
            # Diagnóstico del fondo: COLOR01 del borrado en x = 0 y x de la carga.
            seen = [['%03x' % ((p[0] // 17) << 8 | (p[1] // 17) << 4 | p[2] // 17)
                     for p in (sample(x, c['start'] + r) for x in range(256))] for r in range(4)]
            row['borrado_x0'] = [seen[r][0] == '%03x' % BOR[r] for r in range(4)]
            row['carga_x'] = [next((x for x in range(256) if seen[r][x] == '%03x' % LOAD[r]), None)
                              for r in range(4)]
        if c.get('negative'):
            row['puerta'] = 'OK (detecta)' if bad else 'FALLA: negativo sin errores'
            ok &= bool(bad)
        else:
            row['puerta'] = 'FALLA' if bad else 'OK'
            ok &= not bad
        report.append(row)
        print(json.dumps(row, ensure_ascii=True))
    sheet = Image.new('RGB', (512, 936), (32, 32, 32))
    draw = ImageDraw.Draw(sheet)
    draw.text((4, 2), 'G2T-A ADF %d esperado (gris = sin comparar)' % data['adf'], fill='white')
    sheet.paste(reference.resize((512, 448)), (0, 20))
    draw.text((4, 470), 'WinUAE cycle-exact', fill='white')
    sheet.paste(actual.resize((512, 448)), (0, 488))
    sheet.save(shot.with_name(shot.stem + '_compare.png'))
    shot.with_suffix('.result.json').write_text(json.dumps(dict(ticks=values, casos=report, puerta=ok),
                                                           indent=2), encoding='utf-8')
    print('ADF %d: %s (ticks %d)' % (data['adf'], 'PUERTA OK' if ok else 'PUERTA FALLA', values[1]))
    return 0 if ok else 1


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='cmd',required=True)
    gen=sub.add_parser('build')
    gen.add_argument('--out',type=Path,default=Path('work/g2t_cal.i'))
    gen.add_argument('--repair-wrap',action='store_true')
    rd=sub.add_parser('read')
    rd.add_argument('--shot',type=Path,required=True)
    rd.add_argument('--meta',type=Path,default=Path('work/g2t_cal.json'))
    rd.add_argument('--require-positive',action='store_true')
    gs=sub.add_parser('build-suite')
    gs.add_argument('--adf',type=int,required=True,choices=range(5))
    gs.add_argument('--suite',default='main',choices=('main','cap','final','knee'))
    gs.add_argument('--out',type=Path)
    rs=sub.add_parser('read-suite')
    rs.add_argument('--shot',type=Path,required=True)
    rs.add_argument('--meta',type=Path,required=True)
    args=ap.parse_args()
    if args.cmd=='build-suite':
        name='g2ta_%s%d.i'%('cal' if args.suite=='main' else args.suite,args.adf)
        return build_suite(args.out or Path('work')/name,args.adf,args.suite)
    if args.cmd=='read-suite':
        return read_suite(args.shot,args.meta)
    build(args.out,args.repair_wrap) if args.cmd=='build' else read(args.shot,args.meta,args.require_positive)


if __name__=='__main__':
    sys.exit(main())
