#!/usr/bin/env python3
"""Sonda G7 offline: una foto concreta en WinUAE, nunca un render del juego.

Emite un arnes temporal con paleta y pixeles precalculados para contrastar
el modelo de copper. Escribe PF1 por CPU; no implementa la cola de bobs.
Todos los derivados quedan en work/ (R9).
"""
import argparse
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image

import g5l as L
import g7_color_plan as P
import g7_hw_support as H


def build(a):
    out=Path(a.out)
    assert out.resolve().is_relative_to(Path('work').resolve())
    out.mkdir(parents=True,exist_ok=True)
    g=L.GameRun(a.bin,a.lst,'work/g3/bank')
    assert 0<=a.frame<g.n
    for k in range(a.frame+1):
        if k:
            g.fr.call(g.addr('dc_cop'),g.G.FAKE)
        rec,back=P.render_step(g)
        if k<a.frame:
            P.finish_step(g,rec,back)
    s,mem,cpu=g.s,g.mem,g.cpu
    assert mem.r8(rec+s['R_SWS_VALID']),'foto sin OAM de efectos valida'
    overlay=P.overlays(cpu.read(rec+s['R_OAM'],320),Path(a.sources).read_bytes())
    tab=L.Table(cpu.read(g.addr('g5l_table'),g.addr('g5l_cdma_src')-g.addr('g5l_table')))
    hidden=P.hardware_hidden(g,rec,tab,cpu.read(g.addr('gfx32'),23808))
    overlay[hidden]=-1
    expected_overlay=overlay.copy()
    flows=[]; hardware=[]; primes=[]; assigned=[]
    if a.hardware_entry is not None:
        assert len(a.hardware_entry)<=2, 'sonda acotada a dos parejas libres'
        for entry,pair in zip(a.hardware_entry,(2,6)):
            before=overlay.copy()
            overlay,prime,part,info=H.prepare(g,rec,back,cpu.read(rec+s['R_OAM'],320),
                                             Path(a.sources).read_bytes(),overlay,entry,pair)
            if prime is not None:primes.append(prime)
            flows.extend(part); hardware.append(info)
            assigned.append((info,(before>=0)&(overlay<0)))
        checked=H.validate_plans(g,rec,back,primes,assigned,expected_overlay)
        primes=[(row,dict(words=words)) for row,words in checked.items()]
    data=cpu.read(g.G.DATA,len(Path('work/yi1_s_g5.dat').read_bytes()))
    camera=mem.r16(rec+s['R_S'])
    plans=primes
    patches={}
    for row in np.flatnonzero(np.any(overlay>=0,axis=1)):
        row=int(row)
        words,_=P.T.segment_words(mem,back,s['CL_LINES'],s['SEG'],row)
        nxt,_=P.T.segment_words(mem,back,s['CL_LINES'],s['SEG'],(row+1)%224)
        _,nb=P.prefix_of(nxt,(row+1)%224)
        idx=P.terrain(data,camera,row); idx[hidden[row]]=0
        plan,why=P.plan_line(words,row,idx,overlay[row],nb)
        assert plan is not None,(a.frame,row,why)
        plans.append((row,plan))
        for x in np.flatnonzero(overlay[row]>=0):
            wx=(camera+int(x))%(s['SLOTS']*16)
            bit=0x80>>(wx&7)
            for plane in range(3):
                off=row*s['LINEB1']+plane*s['ROWB1']+wx//8
                for dest in (off,off+s['SLOTS']*2):
                    keep,value=patches.get(dest,(255,0))
                    patches[dest]=(keep&~bit,value|(bit if plan['indices'][x]>>plane&1 else 0))
    assert np.any(expected_overlay>=0),'la sonda requiere efectos visibles'
    code='''
; Sonda generada, no es el emisor G7 del juego.
g7_probe:
        movem.l d0-d7/a0-a6,-(sp)
        GETBASE a2
        add.l #dc_st-binstart,a2
        move.w DC_REND(a2),d0
        mulu #DC_REC,d0
        GETBASE a1
        add.l #dc_rec-binstart,a1
        add.l d0,a1
'''
    code+=f'        cmp.w #{a.frame},R_FRAME(a1)\n        bne .exit\n'
    code+=f'        cmp.w #{camera},R_S(a1)\n        bne .exit\n'
    code+='        move.l V_BACK(a5),a2\n'
    for n,(row,plan) in enumerate(plans):
        code+=f'''        move.l a2,a1
        add.l #CL_LINES+SEG*{row},a1
        move.l a1,a0
.find{n}:
        cmp.w #$84,(a0)
        beq .tail{n}
        addq.l #4,a0
        bra .find{n}
.tail{n}:
        move.l (a0)+,d2
        move.l (a0)+,d3
        move.l (a0),d4
        lea .row{n}(pc),a0
        move.w #{len(plan['words'])-1},d0
.copy{n}:
        move.l (a0)+,(a1)+
        dbf d0,.copy{n}
        move.l d2,(a1)+
        move.l d3,(a1)+
        move.l d4,(a1)+
'''
    if patches:
        code+='        move.l V_BUF1(a5),a1\n        lea .pixels(pc),a0\n'
        code+=f'        move.w #{len(patches)-1},d0\n'
        code+='''.pixel:
        move.l (a0)+,d1
        move.l a1,a2
        add.l d1,a2
        move.b (a0)+,d1
        and.b d1,(a2)
        move.b (a0)+,d1
        or.b d1,(a2)
        dbf d0,.pixel
'''
    code+='.hardware:\n'
    if hardware:
        # El banco G7 todavia no se carga en el juego. Esta sonda usa su
        # reserva real, detras de las fuentes (sin agregar arena chip).
        pool_offset=s['BUF1']+len(Path(a.sources).read_bytes())
        assert len(Path(a.sources).read_bytes())+sum(map(len,flows))<=12288
        code+=f'''        GETBASE a0
        add.l #g7_pf1-binstart,a0
        move.l (a0),a1
        add.l #{pool_offset},a1
        move.l a1,d5
        lea .dma(pc),a0
        move.w #{sum(map(len,flows))//4-1},d0
.dma_copy:
        move.l (a0)+,(a1)+
        dbf d0,.dma_copy
'''
        for n,info in enumerate(hardware):
            code+=f'''        move.l V_BACK(a5),a2
        lea CL_VBL+{info['vbl_offset']}(a2),a2
'''
            for upper,flow in enumerate(flows[2*n:2*n+2]):
                channel=info['pair'][upper]
                pos,ctl=struct.unpack_from('>HH',flow)
                off=sum(map(len,flows[:2*n+upper]))+4 # DATA, POS/CTL por VBL
                code+=f'''        move.l d5,d1
        add.l #{off},d1
        move.w #${0x120+4*channel:04x},(a2)+
        swap d1
        move.w d1,(a2)+
        swap d1
        move.w #${0x122+4*channel:04x},(a2)+
        move.w d1,(a2)+
        move.l #${0x140+8*channel:04x}{pos:04x},(a2)+
        move.l #${0x142+8*channel:04x}{ctl:04x},(a2)+
'''
            if a.hardware_late:
                # Control negativo: anular POS/CTL, dejando solo PT.
                code+='        clr.w -22(a2)\n        clr.w -18(a2)\n        clr.w -6(a2)\n        clr.w -2(a2)\n'
    code+='''
.exit:
        movem.l (sp)+,d0-d7/a0-a6
        rts
'''
    for n,(_,plan) in enumerate(plans):
        code+=f'.row{n}:\n'
        code+=''.join(f'        dc.w ${reg:04x},${value:04x}\n' for reg,value in plan['words'])
    code+='.pixels:\n'
    for off,(keep,value) in sorted(patches.items()):
        code+=f'        dc.l {off}\n        dc.b ${keep:02x},${value:02x}\n'
    if flows:
        code+='        cnop 0,4\n.dma:\n'
        for value in struct.unpack('>'+str(sum(map(len,flows))//2)+'H',b''.join(flows)):
            code+=f'        dc.w ${value:04x}\n'
    code+='        cnop 0,4\n'
    src=Path('player/game.s').read_text(encoding='utf8')
    needle='        bsr     g7_save\n'
    assert src.count(needle)==1
    src=src.replace(needle,needle+'''        GETBASE a0
        add.l #g7_probe-binstart,a0
        jsr (a0)
''')
    assert src.count('\nbinend:')==1
    src=src.replace('\nbinend:',code+'\nbinend:')
    (out/'game.probe.s').write_text(src,encoding='utf8')
    meta=dict(frame=a.frame,camera=camera,rows=len(plans),bytes_patched=len(patches),
              pixels=[(int(x),int(y),int(expected_overlay[y,x])) for y,x in zip(*np.where(expected_overlay>=0))],
              hardware=hardware,hardware_negative=a.hardware_late,
              hardware_pixels=[(int(x),int(y)) for y,x in zip(*np.where(
                  (expected_overlay>=0)&(overlay<0)))] if hardware else [],
              scope='sonda de una foto; escrituras CPU; sin cola ni coste representativo')
    (out/'probe.json').write_text(json.dumps(meta,indent=2),encoding='utf8')
    print('G7 PROBE: generada '+json.dumps({k:v for k,v in meta.items() if k not in ('pixels','hardware_pixels')}))


def compare(a):
    meta=json.loads(Path(a.meta).read_text())
    ctrl=Image.open(a.control).convert('RGB').crop(L.SHOT_BOX)
    shot=Image.open(a.shot).convert('RGB').crop(L.SHOT_BOX)
    want=ctrl.copy()
    for x,y,col in meta['pixels']:
        rgb=L.rgb12(col)
        for dy in range(2):
            for dx in range(2):
                want.putpixel((2*(x+L.SHOT_DX)+dx,2*y+dy),rgb)
    diff=np.any(np.asarray(want)!=np.asarray(shot),axis=2)
    hw_mask=np.zeros(diff.shape,dtype=bool)
    for x,y in meta.get('hardware_pixels',[]):
        hw_mask[2*y:2*y+2,2*(x+L.SHOT_DX):2*(x+L.SHOT_DX)+2]=True
    hw_diff=int(np.count_nonzero(diff&hw_mask))
    other_diff=int(np.count_nonzero(diff&~hw_mask))
    ok=not diff.any()
    if a.expect_negative:
        assert meta.get('hardware_negative'), 'la sonda no es el negativo de armado'
        ok=hw_diff>0 and other_diff==0
    sheet=Image.new('RGB',(640,1536))
    for n,im in enumerate((ctrl,want,shot)):
        sheet.paste(im,(0,512*n))
    sheet.save(Path(a.shot).with_name('check.png'))
    result=dict(frame=meta['frame'],pixels_effect=len(meta['pixels']),different=int(diff.sum()),
                hardware_different=hw_diff,other_different=other_diff,
                expected_negative=a.expect_negative,
                scope='control | esperado OCS | sonda WinUAE; pantalla completa')
    Path(a.shot).with_name('check.json').write_text(json.dumps(result,indent=2))
    print('G7 PROBE: '+('OK ' if ok else 'FALLA ')+json.dumps(result))
    return int(not ok)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='cmd',required=True)
    b=sub.add_parser('build')
    b.add_argument('--bin',required=True);b.add_argument('--lst',required=True)
    b.add_argument('--frame',type=int,required=True);b.add_argument('--out',required=True)
    b.add_argument('--sources',default='work/g7/sources.bin')
    b.add_argument('--hardware-entry',type=int,action='append',help='apoyo SPR2/3 y luego SPR6/7; repetir para dos fichas')
    b.add_argument('--hardware-late',action='store_true',help='negativo: PT sin armar CTL')
    c=sub.add_parser('compare')
    c.add_argument('--expect-negative',action='store_true',help='exige errores solo en el apoyo hardware')
    for name in ('meta','control','shot'):
        c.add_argument('--'+name,required=True)
    a=ap.parse_args()
    return build(a) if a.cmd=='build' else compare(a)


if __name__=='__main__':
    raise SystemExit(main())
