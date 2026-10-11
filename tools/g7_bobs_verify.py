#!/usr/bin/env python3
"""G7-3: productor 68000 y consumidor BLIT con memoria efectiva.

Musashi no emula el blitter: este arnes ejecuta su minterm sobre los
punteros/modulos reales. La cola/IRQ se prueban aparte del productor.
"""
import argparse
import json
from pathlib import Path
import struct

import numpy as np
from g5l import GameRun
import g7_color_plan as P
import g7_sources as B
import g7_hw_support as H


class Blitter:
    def __init__(self,g):
        self.g=g;self.count=0

    def flush(self):
        g=self.g;m=g.mem;b=g.G.FAKE;size=m.r16(b+0x58)
        if not size:return
        h=size>>6;w=size&63
        con=m.r16(b+0x40);mode=con&255
        assert mode in (0xf0,0xca) and w,('minterm',hex(con),size)
        ptr={c:m.r32(b+o) for c,o in (('a',0x50),('b',0x4c),('c',0x48),('d',0x54))}
        mod={c:m.r16(b+o) for c,o in (('a',0x64),('b',0x62),('c',0x60),('d',0x66))}
        mod={c:v-65536 if v&32768 else v for c,v in mod.items()}
        for _ in range(h):
            for x in range(w):
                a=m.r16(ptr['a']+2*x)
                if x==0:a&=m.r16(b+0x44)
                if x==w-1:a&=m.r16(b+0x46)
                if mode==0xf0:out=a
                else:out=(a&m.r16(ptr['b']+2*x))|((~a&65535)&m.r16(ptr['c']+2*x))
                m.w16(ptr['d']+2*x,out)
            for c in ptr:ptr[c]+=2*w+mod[c]
        m.w16(b+0x58,0);self.count+=1

    def hook_wait(self):
        g=self.g;R=g.cpu.M.Register
        def flush(op,pc):
            self.flush();sp=g.cpu.cpu.r_reg(R.A7)
            g.cpu.cpu.w_pc(g.mem.r32(sp));g.cpu.cpu.w_reg(R.A7,sp+4)
        tid=g.cpu.m.traps.alloc(flush)
        g.mem.w16(g.addr('bwait'),0xA000|tid)


def core(g):
    s,m,cpu,addr=g.s,g.mem,g.cpu,g.addr;R=cpu.M.Register
    bank=m.r32(addr('g7b_bank'));raw=Path('work/g7/sources.bin').read_bytes()
    assert cpu.read(bank,len(raw))==raw,'decoder RLE no exacto'
    assert cpu.read(bank+7616,960)==bytes(960),'decodificador invade flujos'
    blit=Blitter(g);blit.hook_wait()
    pf=m.r32(g.fr.vars+s['V_BUF1']);other=m.r32(addr('g7_original'))
    if pf==other:other=m.r32(addr('g7_pf1'))
    initial=bytes((i*17+5)&255 for i in range(s['BUF1']))
    cpu.write(pf,initial);cpu.write(other,initial)
    saved=cpu.read(other,s['BUF1'])
    queue=bank+s['G7Q_OFF'];expected=bytearray(initial)
    records=[]
    for row,col,mask,bits in ((0,0,0x8001,(0xffff,0,0xaaaa)),
                              (15,21,0x03ff,(0x0555,0xffff,0)),
                              (223,3,0xffff,(0,0x1234,0xffff))):
        at=row*s['LINEB1']+2*col;dest=pf+at
        record=struct.pack('>I6H',dest,mask,mask,mask,*bits);records.append(record)
        for copy in (0,44):
            for p,v in enumerate(bits):
                off=at+copy+p*s['ROWB1'];old=struct.unpack_from('>H',expected,off)[0]
                struct.pack_into('>H',expected,off,(old&~mask)|(v&mask))
    cpu.write(queue,b''.join(records));cpu.cpu.w_reg(R.D0,len(records))
    g.fr.call(addr('g7b_submit'),g.G.FAKE)
    for _ in range(2*len(records)):
        blit.flush();g.fr.call(addr('g7b_irq'),g.G.FAKE)
    assert m.r16(addr('g7b_qleft'))==0 and m.r16(g.G.FAKE+0x9a)==0x40
    assert cpu.read(pf,s['BUF1'])==expected,'minterm/copia anillo'
    assert cpu.read(other,s['BUF1'])==saved,'cola escribio PF1 no seleccionado'
    active=m.r16(addr('g7_active'))//8;dirty=addr('g7b_dirty')+active*44
    assert [(i,m.r16(dirty+2*i)) for i in range(22) if m.r16(dirty+2*i)]==[(0,1),(3,8192),(21,1)]
    # Restaura el bloque usando D_MAP actual, en ambas copias. Incluye
    # ultima fila y columna 21; el mapa mutado se lee al restaurar.
    m.w16(g.fr.vars+s['V_P'],2)
    data=g.G.DATA;mp=data+m.r32(data+s['D_MAP']);blocks=data+m.r32(data+s['D_BLK'])
    for col,row in ((0,0),(21,0),(3,13)):
        block=m.r8(mp+col*15+row)
        for y in range(16):
            for p in range(3):
                v=m.r16(blocks+96*block+y*6+2*p)
                for copy in (0,44):
                    off=(row*16+y)*264+88*p+2*col+copy
                    struct.pack_into('>H',expected,off,v)
    g.fr.call(addr('g7b_restore'),g.G.FAKE);blit.flush()
    assert cpu.read(pf,s['BUF1'])==expected,'restauracion no exacta'
    assert cpu.read(dirty,44)==bytes(44)
    assert cpu.read(other,s['BUF1'])==saved
    # El diario modifica y repone solo V_BACK. FRONT/PEND permanecen
    # byte a byte; repetir save_row no duplica ni pierde el original.
    back=m.r32(g.fr.vars+s['V_BACK'])
    lists=[m.r32(g.fr.vars+s[n]) for n in ('V_COP','V_COP2','V_COP3')]
    others={at:cpu.read(at,s['CL_SIZE']) for at in lists if at!=back}
    original=cpu.read(back,s['CL_SIZE'])
    g.fr.call(addr('g7b_begin'),g.G.FAKE)
    row=101;m.w32(g.V.STACK,row)
    g.fr.call(addr('_g7b_save_row'),g.G.FAKE)
    assert cpu.cpu.r_reg(R.D0)==0
    index=lists.index(back);count=addr('g7b_saved_n')+2*index
    size=m.r16(count);assert size>4
    at=back+s['CL_LINES']+s['SEG']*row+8
    m.w32(at,0x01820abc);m.w32(back+s['CL_VBL']+96,0x01400000)
    g.fr.call(addr('_g7b_save_row'),g.G.FAKE)
    assert m.r16(count)==size,'fila duplicada en diario'
    g.fr.call(addr('g7b_clean'),g.G.FAKE)
    assert cpu.read(back,s['CL_SIZE'])==original,'copper/VBL no restituidos'
    assert all(cpu.read(at,s['CL_SIZE'])==raw for at,raw in others.items()),'FRONT/PEND modificadas'
    m.w16(count,s['G7_SNAP_SIZE']-4);m.w32(g.V.STACK,row)
    g.fr.call(addr('_g7b_save_row'),g.G.FAKE)
    assert cpu.cpu.r_reg(R.D0)==4 and m.r16(count)==s['G7_SNAP_SIZE']-4
    m.w16(count,0)
    # Una cola vacia no dispara DMA; exceder la capacidad se rechaza.
    cpu.cpu.w_reg(R.D0,0);g.fr.call(addr('g7b_submit'),g.G.FAKE)
    assert m.r16(addr('g7b_qleft'))==0
    cpu.cpu.w_reg(R.D0,s['G7Q_MAX']+1);g.fr.call(addr('g7b_submit'),g.G.FAKE)
    assert m.r16(addr('g7b_error'))==1 and m.r16(addr('g7b_qleft'))==0
    print('G7 CORE: OK (fuentes, minterm, IRQ, dos copias, restauracion, cola vacia/limite)',flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin',required=True);ap.add_argument('--lst',required=True)
    ap.add_argument('--to-k',type=int,default=450);ap.add_argument('--core-only',action='store_true')
    ap.add_argument('--from-k',type=int,default=0)
    ap.add_argument('--out',help='informe completo JSON')
    a=ap.parse_args();g=GameRun(a.bin,a.lst,'work/g3/bank');core(g)
    if a.core_only:return 0
    # Instancia nueva: el caso de cola no altera la partida de referencia.
    g=GameRun(a.bin,a.lst,'work/g3/bank');s,m,cpu=g.s,g.mem,g.cpu;R=cpu.M.Register
    blit=Blitter(g);blit.hook_wait();bank=m.r32(g.addr('g7b_bank'))
    # El puente de reintento recarga CUSTOM real; redirigir solamente
    # esa constante a los registros del blitter del arnes.
    retry=g.addr('_g7b_retry');code=cpu.read(retry,128)
    at=code.index(bytes.fromhex('49f900dff000'))
    m.w32(retry+at+2,g.G.FAKE)
    # Los blits de scroll_init ocurrieron antes de instalar el modelo.
    # Sembrar el terreno inicial; desde aqui el 68000 mantiene los anillos.
    mp=g.G.DATA+m.r32(g.G.DATA+s['D_MAP']);blocks=g.G.DATA+m.r32(g.G.DATA+s['D_BLK'])
    for state,pf in enumerate((m.r32(g.addr('g7_original')),m.r32(g.addr('g7_pf1')))):
        camera=m.r16(g.addr('g7_state')+8*state)
        if camera>=32768:camera-=65536
        for col in range(camera-2,camera+20):
            if not 0<=col<m.r16(g.G.DATA+s['D_COLS']):continue
            for row in range(14):
                block=m.r8(mp+15*col+row)
                for y in range(16):
                    for p in range(3):
                        v=m.r16(blocks+96*block+6*y+2*p)
                        for copy in (0,44):m.w16(pf+(row*16+y)*264+88*p+2*(col%22)+copy,v)
    tab=P.L.Table(cpu.read(g.addr('g5l_table'),g.addr('g5l_cdma_src')-g.addr('g5l_table')))
    gfx=cpu.read(g.addr('gfx32'),23808);sources=Path('work/g7/sources.bin').read_bytes()
    stats=dict(photos=0,rejects=[],pixels=0,cycles_max=0,cycles_max_k=None,cycles_total=0,saved_bytes_max=0)
    sent=[]
    # El puente de C se observa aqui como descriptor. El consumidor real
    # submit/IRQ/minterm fue ejecutado arriba; no sustituir ambos cruces.
    def send(op,pc):
        sp=cpu.cpu.r_reg(R.A7);n=m.r32(sp+4);assert n<=s['G7Q_MAX']
        pf=m.r32(g.fr.vars+s['V_BUF1']);active=m.r16(g.addr('g7_active'))//8
        for j in range(n):
            dest,*words=struct.unpack('>I6H',cpu.read(bank+s['G7Q_OFF']+16*j,16))
            off=dest-pf;row,rem=divmod(off,264);assert 0<=row<224 and rem<44 and not rem%2
            sent.append((row,rem,words))
            at=g.addr('g7b_dirty')+active*44+rem
            m.w16(at,m.r16(at)|(1<<(row//16)))
            for copy in (0,44):
                for p in range(3):
                    at=dest+copy+88*p;mask=words[p];v=words[3+p]
                    m.w16(at,(m.r16(at)&~mask)|(v&mask))
        cpu.cpu.w_pc(m.r32(sp));cpu.cpu.w_reg(R.A7,sp+4)
    tid=cpu.m.traps.alloc(send);m.w16(g.addr('_g7b_send'),0xA000|tid)
    for k in range(min(g.n,a.to_k+1)):
        if k:g.fr.call(g.addr('dc_cop'),g.G.FAKE)
        # Reproducir el orden del bucle real, incluida restauracion anterior
        # a columns y tile_apply (P132).
        photo=m.r16(g.dc+s['DC_NEW']);rec=g.addr('dc_rec')+photo*s['DC_REC']
        m.w16(g.dc+s['DC_REND'],photo);m.w16(g.fr.vars+s['V_S'],m.r16(rec+s['R_S']))
        cpu.cpu.w_reg(R.D0,m.r8(rec+s['R_COIN']))
        g.fr.call(g.addr('g7b_clean'),g.G.FAKE)
        cpu.cpu.w_reg(R.D0,m.r8(rec+s['R_COIN']))
        for name in ('coin_prepare','apply_colors','set_pointers','build_mid','coin_list','g5l_render',
                     'g7_select','g7b_restore','g7_columns'):
            if name=='g5l_render':cpu.cpu.w_reg(R.A0,rec)
            g.fr.call(g.addr(name),g.G.FAKE)
        cpu.cpu.w_reg(R.D7,m.r16(rec+s['R_TSEQ']));g.fr.call(g.addr('tile_apply'),g.G.FAKE)
        g.fr.call(g.addr('set_pointers'),g.G.FAKE)
        cpu.cpu.w_reg(R.D7,photo);g.fr.call(g.addr('dc_hdr'),g.G.FAKE);blit.flush()
        back=m.r32(g.fr.vars+s['V_BACK']);pf=m.r32(g.fr.vars+s['V_BUF1'])
        original_copper=cpu.read(back,s['CL_SIZE'])
        cam=m.r16(rec+s['R_S'])
        ov=(P.overlays(cpu.read(rec+s['R_OAM'],320),sources)
            if m.r8(rec+s['R_SWS_VALID']) else np.full((224,256),-1,dtype=np.int32))
        hidden=P.hardware_hidden(g,rec,tab,gfx);ov[hidden]=-1
        old=[]
        for row in np.flatnonzero(np.any(ov>=0,axis=1)):
            words,_=P.T.segment_words(m,back,s['CL_LINES'],s['SEG'],int(row))
            idx=P.terrain(cpu.read(g.G.DATA,243384),cam,int(row))
            old.append((int(row),P.palette(words,int(row))[idx,np.arange(256)]))
        if k<a.from_k:
            g.fr.call(g.addr('g7_save'),g.G.FAKE);P.finish_step(g,rec,back)
            continue
        for reg,value in ((R.A3,g.G.DATA),(R.A4,g.G.FAKE),(R.A5,g.fr.vars),(R.A7,g.V.STACK-4)):
            cpu.cpu.w_reg(reg,value)
        m.w32(g.V.STACK-4,g.V.RET);cpu.cpu.w_pc(g.addr('g7b_draw'))
        cycles=0;sent.clear()
        while cpu.cpu.r_pc()!=g.V.RET+2:
            cycles+=cpu.m.execute(10_000_000).cycles
            assert cycles<2_000_000_000,('presupuesto productor',k,hex(cpu.cpu.r_pc()))
        if cycles>stats['cycles_max']:stats['cycles_max']=cycles;stats['cycles_max_k']=k
        stats['cycles_total']+=cycles
        stats['saved_bytes_max']=max(stats['saved_bytes_max'],*(m.r16(g.addr('g7b_saved_n')+2*i) for i in range(3)))
        error=m.r16(g.addr('g7b_error'))
        if error:stats['rejects'].append(dict(k=k,error=error));m.w16(g.addr('g7b_error'),0)
        else:
            hardware=None
            if cpu.read(back+s['CL_VBL'],s['CL_VBLSZ'])!=original_copper[s['CL_VBL']:s['CL_VBL']+s['CL_VBLSZ']]:
                cpu.write(0x1d0000,original_copper)
                original_hw,original_mask=H.visible_image(g,rec,0x1d0000)
                hardware,new_mask=H.visible_image(g,rec,back)
                assert np.all(new_mask[original_mask]) and np.array_equal(hardware[original_mask],original_hw[original_mask]),('hardware original alterado',k)
            for row,colors in old:
                words,_=P.T.segment_words(m,back,s['CL_LINES'],s['SEG'],row)
                pal=P.palette(words,row)
                out=np.array([sum(((m.r16(pf+row*264+88*p+2*(((cam+x)//16)%22))>>(15-((cam+x)&15)))&1)<<p
                                  for p in range(3)) for x in range(256)])
                terrain=P.terrain(cpu.read(g.G.DATA,243384),cam,row)
                live=(terrain!=0)|(ov[row]>=0);live&=~hidden[row]
                expected=np.where(ov[row]>=0,ov[row],colors)
                bad=np.flatnonzero(live&(pal[out,np.arange(256)]!=expected))
                if bad.size:
                    if hardware is None:hardware,new_mask=H.visible_image(g,rec,back)
                    bad=np.array([x for x in bad if not new_mask[row,x] or hardware[row,x]!=expected[x]])
                assert not bad.size,('pixel PF1',k,row,cam,[(int(x),int(out[x]),int(terrain[x]),int(ov[row,x]),int(pal[out[x],x]),int(expected[x])) for x in bad[:12]], [t for t in sent if t[0]==row],cycles)
            stats['photos']+=1;stats['pixels']+=int(np.count_nonzero(ov>=0))
        g.fr.call(g.addr('g7_save'),g.G.FAKE);P.finish_step(g,rec,back)
        if k%50==0:print(k,stats,flush=True)
    print('G7 BOBS: '+json.dumps(stats),flush=True)
    if a.out:
        stats.update(complete=True,completed_until=min(g.n,a.to_k+1)-1,from_k=a.from_k)
        Path(a.out).write_text(json.dumps(stats,indent=2),encoding='utf8')
    return int(bool(stats['rejects']))


if __name__=='__main__':raise SystemExit(main())
