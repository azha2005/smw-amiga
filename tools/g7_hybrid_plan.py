#!/usr/bin/env python3
"""G7-C: barrida offline PF1 con apoyo puntual de parejas DMA detenidas.

Conserva el contrato de PF1 y todos los eventos del copper. El apoyo usa
colores existentes o sufijos calibrados; no rearma canales ocupados.
Un rechazo de este modelo acotado no demuestra imposibilidad fisica.
"""
import argparse
import collections
import itertools
import json
from pathlib import Path

import numpy as np
import g5l as L
import g7_color_plan as P
import g7_hw_support as H
from sws_cmp import OAM_GROUPS


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin',required=True);ap.add_argument('--lst',required=True)
    ap.add_argument('--sources',default='work/g7/sources.bin')
    ap.add_argument('--from-k',type=int,default=0)
    ap.add_argument('--to-k',type=int,default=65535)
    ap.add_argument('--out',default='work/g7-hybrid')
    ap.add_argument('--row-states',type=int,default=30000)
    ap.add_argument('--search-states',type=int,default=3000)
    a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    bank=Path(a.sources).read_bytes()
    g=L.GameRun(a.bin,a.lst,'work/g3/bank')
    s,mem,cpu=g.s,g.mem,g.cpu
    gfx=cpu.read(g.addr('gfx32'),23808)
    tab=L.Table(cpu.read(g.addr('g5l_table'),g.addr('g5l_cdma_src')-g.addr('g5l_table')))
    size=len(Path('work/yi1_s_g5.dat').read_bytes())
    entries=sorted({e for groups in OAM_GROUPS.values() for first,n in groups for e in range(first,first+n)})
    stats=collections.Counter();cache={};failures=[];witnesses=[]
    def report(complete,k):
        result=dict(stats=dict(stats),failures=failures,witnesses=witnesses,
                    complete=complete,completed_until=k,row_states=a.row_states,search_states=a.search_states,
                    scope='offline ideal; PF1 G2T-A + SPR2/3 o SPR6/7 detenidos, paleta existente o sufijo G2T-A; sin reuso ni renderer')
        (out/'report.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    for k in range(min(g.n,a.to_k+1)):
        if k>=a.from_k and (k-a.from_k)%25==0:
            print('PHOTO',k,dict(stats),flush=True)
            report(False,k-1)
        if k:g.fr.call(g.addr('dc_cop'),g.G.FAKE)
        rec,back=P.render_step(g)
        if k<a.from_k or not mem.r8(rec+s['R_SWS_VALID']):
            P.finish_step(g,rec,back);continue
        oam=cpu.read(rec+s['R_OAM'],320)
        overlay=P.overlays(oam,bank)
        hidden=P.hardware_hidden(g,rec,tab,gfx)
        overlay[hidden]=-1
        if not np.any(overlay>=0):
            P.finish_step(g,rec,back);continue
        data=cpu.read(g.G.DATA,size);camera=mem.r16(rec+s['R_S'])
        rows={}
        for row in np.flatnonzero(np.any(overlay>=0,axis=1)):
            row=int(row)
            words,_=P.T.segment_words(mem,back,s['CL_LINES'],s['SEG'],row)
            nxt,_=P.T.segment_words(mem,back,s['CL_LINES'],s['SEG'],(row+1)%224)
            _,nb=P.prefix_of(nxt,(row+1)%224)
            idx=P.terrain(data,camera,row);idx[hidden[row]]=0
            rows[row]=(words,nb,idx)
        def solve(ov):
            bad=[]
            for row,(words,nb,idx) in rows.items():
                if not np.any(ov[row]>=0):continue
                key=(row,tuple(map(tuple,words)),nb,idx.tobytes(),ov[row].tobytes())
                if key not in cache:
                    cache[key]=P.plan_line(words,row,idx,ov[row],nb,
                                           row_states=a.row_states,search_states=a.search_states)
                    stats['unique_rows']+=1
                plan,why=cache[key]
                if plan is None:bad.append(dict(row=row,reason=why))
            return bad
        bad=solve(overlay)
        stats['photos']+=1;stats['pixels']+=int(np.count_nonzero(overlay>=0))
        if not bad:
            stats['pf1_only']+=1
        else:
            stats['pf1_rejected_photos']+=1
            _,audit=H.dma_image(g,rec,back)
            free=[p for p in (2,6) if not audit[p]['spans'] and not audit[p+1]['spans']]
            failing_rows={b['row'] for b in bad}
            candidates=[]
            for e in entries:
                single=bytearray(320)
                for ee in range(64):single[4*ee+1]=0xF0
                single[4*e:4*e+4]=oam[4*e:4*e+4];single[256+e]=oam[256+e]
                tile=P.overlays(single,bank)
                mask=(tile>=0)&(tile==overlay)
                score=sum(int(np.count_nonzero(mask[row])) for row in failing_rows)
                if score:candidates.append((-score,e))
            candidates=[e for _,e in sorted(candidates)]
            chosen=None;rejections=[]
            # Una pareja primero; dos solo si siguen fallando filas.
            for n in range(1,min(len(free),len(candidates))+1):
                for es in itertools.combinations(candidates,n):
                    for ps in itertools.permutations(free,n):
                        residual=overlay.copy();infos=[];primes=[];assigned=[]
                        try:
                            for entry,pair in zip(es,ps):
                                before=residual.copy()
                                residual,prime,_,info=H.prepare(g,rec,back,oam,bank,residual,entry,pair)
                                if prime is not None:primes.append(prime)
                                assigned.append((info,(before>=0)&(residual<0)))
                                infos.append(info)
                            H.validate_plans(g,rec,back,primes,assigned,overlay)
                        except AssertionError as ex:
                            rejections.append(str(ex));continue
                        remaining=solve(residual)
                        if not remaining:
                            chosen=infos;break
                    if chosen:break
                if chosen:break
            if chosen:
                stats['hybrid_photos']+=1
                stats['hw_tiles']+=len(chosen)
                stats['hw_pixels']+=sum(i['pixels'] for i in chosen)
                stats['max_dma_bytes']=max(stats['max_dma_bytes'],sum(i['dma_bytes'] for i in chosen))
                if len(witnesses)<30:
                    witnesses.append(dict(k=k,camera=camera,hardware=chosen))
            else:
                stats['unresolved_photos']+=1
                if len(failures)<100:
                    failures.append(dict(k=k,camera=camera,rows=bad,free_pairs=free,
                                         entries=candidates,reasons=dict(collections.Counter(rejections))))
                if stats['unresolved_photos']<=10:
                    print('UNRESOLVED',k,failures[-1],flush=True)
        P.finish_step(g,rec,back)
        if k%500==0:print(k,dict(stats),flush=True)
    report(True,min(g.n,a.to_k+1)-1)
    print('G7 HYBRID: '+('OK ' if not stats['unresolved_photos'] else 'PARCIAL ')+json.dumps(dict(stats)),flush=True)
    return int(bool(stats['unresolved_photos']))


if __name__=='__main__':
    raise SystemExit(main())
