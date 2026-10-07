#!/usr/bin/env python3
"""Calibración G2T sintética, seis planos y ocho canales DMA activos.

Reutiliza el arnés G0, no cambia el juego. Prueba un sufijo WAIT+colores+
COP2LC/COPJMP2 seguido del borrado; no certifica todas las listas G5.
"""
import argparse
import json
import struct
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
    args=ap.parse_args()
    build(args.out,args.repair_wrap) if args.cmd=='build' else read(args.shot,args.meta,args.require_positive)


if __name__=='__main__':
    main()
