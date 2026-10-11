#!/usr/bin/env python3
"""G7-2: plan PF1 concreto desde la lista real, el mapa y la OAM de la foto.

Referencia offline: conserva indices del terreno, colores de las capas y
posiciones de las recargas de sprites. Un fallo de busqueda no demuestra
imposibilidad. No genera tablas seleccionadas por frame para el juego.
"""
import argparse
import collections
import functools
import json
import struct
from pathlib import Path

import numpy as np
import g2t_ref as T
import g5l as L
import g7_sources as B
from sws_cmp import OAM_GROUPS


def terrain(data, camera, row):
    blk, mp = struct.unpack_from('>2I', data, 16)
    out = []
    for x in range(256):
        wx = camera+x
        block = data[mp+(wx//16)*15+row//16]
        off = blk+block*96+(row & 15)*6
        out.append(sum(((struct.unpack_from('>H', data, off+2*p)[0] >> (15-(wx & 15))) & 1) << p
                       for p in range(3)))
    return np.array(out, dtype=np.int8)


def palette(words, row, phase=0):
    colors = np.zeros((8, 256), dtype=np.int32)
    for x, reg, value in T.timeline(words, row):
        if 0x182 <= reg <= 0x18E:
            colors[(reg-0x180)//2, max(0, x+(phase if x >= 0 else 0)):] = value & 0xFFF
    return colors


def prefix_of(words, row):
    prefix = []
    for index, (a, b) in enumerate(words):
        if index < 2 and (a & 1 or a == 0x1FE):
            prefix.append((a, b))
        elif a & 1 or a == 0x1FE:
            break
        else:
            prefix.append((a, b))
    nb = sum(not (a & 1) and a != 0x1FE for a, _ in prefix)
    return prefix, nb


def transitions(required, initial, locked=(), phase_max=0):
    jobs, colors = [], list(initial)
    for r in range(1, 8):
        if r in locked:
            continue
        xs = np.flatnonzero(required[r] >= 0)
        if not xs.size:
            continue
        values = required[r, xs]
        colors[r] = int(values[0])
        # Solo una transicion necesita entrar en Python. La busqueda de
        # asignaciones llama miles de veces a esta funcion por fila.
        for i in np.flatnonzero(values[1:] != values[:-1]) + 1:
            jobs.append((int(xs[i-1])+1, int(xs[i])-phase_max,
                         0x180+2*r, int(values[i])))
    return jobs, colors


def schedule(jobs, start, end, capacity, row, max_states=3000, budget=None):
    """Busqueda finita de MOVE/NOP/WAIT sobre la rejilla calibrada.

    Jobs (min,max,reg,color), incluidos los eventos ajenos a PF1 con
    min=max para conservar exactamente su posicion. El deadline ya
    incluye el margen opcional; nunca posponerlo.
    """
    if any(a > b for a, b, _, _ in jobs):
        return None
    jobs = sorted(jobs, key=lambda j: j[1])
    visited = 0

    @functools.lru_cache(None)
    def search(mask, pos, left):
        nonlocal visited
        visited += 1
        if budget is not None:
            if budget[0]<=0:
                return None
            budget[0]-=1
        if visited > max_states:
            return None
        if not mask:
            return ()
        if left < mask.bit_count():
            return None
        pending = [i for i in range(len(jobs)) if mask >> i & 1]
        if any(jobs[i][1] < pos for i in pending):
            return None
        # EDF primero; explorar otro liberado permite ocupar un hueco.
        first_deadline = jobs[pending[0]][1]
        for i in pending:
            a, b, reg, value = jobs[i]
            if a > first_deadline:
                continue
            options = []
            p = pos
            # No encadenar desde el borrado (G2T-A): el primer evento
            # debe tener WAIT propio, con el copper libre.
            first = mask == (1 << len(jobs))-1
            for n in range(0 if first else min(left, 12)):
                if p > min(b, end):
                    break
                if p >= a:
                    options.append((n+1, p, ((0x1FE, 0),)*n+((reg, value),)))
                p = L.adv(p)
            seen = set()
            for h in range(0x20, 0xD0, 2):
                p = max(L.adv(pos, 2), L.xh(h))
                # WAIT libre solo dentro de la ventana calibrada (G2T-A).
                # pos ya es la ranura posterior al ultimo MOVE: este
                # margen es deliberadamente mas conservador que IDLE.
                if p-pos >= L.IDLE and a <= p <= min(b, end) and p not in seen:
                    seen.add(p)
                    options.append((2, p, ((((row+L.V0) & 255) << 8 | h | 1, 0xFFFE), (reg, value))))
            for n, p, words in sorted(options, key=lambda o: (o[0], o[1])):
                if n > left:
                    continue
                tail = search(mask ^ (1 << i), L.adv(p), left-n)
                if tail is not None:
                    return words+tail
        return None

    return search((1 << len(jobs))-1, start, capacity)


def plan_line(words, row, idx, overlay, next_nb, capacity=64, phase_max=0, search_states=3000, row_states=30000):
    budget=[row_states]
    base = palette(words, row)
    # Caso exacto sin recargas: cada pixel puede usar un indice existente
    # distinto. No exigir un unico indice por tinta si la paleta ya cambia
    # por X. Evita buscar cientos de asignaciones para negro/blanco comunes.
    occupied=overlay>=0
    if occupied.any() and len(words)+3<=capacity:
        possible=(base==overlay[None,:])
        possible[0]=False             # un efecto negro sigue siendo opaco
        for phase in range(1,phase_max+1):
            possible &= palette(words,row,phase)==overlay[None,:]
        if np.all(np.any(possible[:,occupied],axis=0)):
            selected=np.argmax(possible,axis=0)
            out_idx=idx.copy();out_idx[occupied]=selected[occupied]
            mapping=[]
            for color in sorted(set(map(int,overlay[occupied]))):
                for index in range(1,8):
                    xs=np.flatnonzero(occupied&(overlay==color)&(selected==index))
                    if xs.size:mapping.append(dict(color=color,index=index,xs=xs.tolist()))
            return dict(words=words,indices=out_idx.tolist(),mapping=mapping,
                        transitions=0,fixed=0,bytes=4*(len(words)+3),mode='existing'),None
    if phase_max==0:
        # Una cota independiente puede cerrar el rechazo antes de la DFS.
        # Ventanas de 31 px antes del codo: siete registros y a lo sumo dos
        # MOVE, incluso permitiendo reasignar todos los indices del terreno.
        from g7_color_bound import certificate
        required=np.where(occupied,overlay,base[idx,np.arange(256)])
        live=occupied|(idx!=0)
        seen=set()
        for left in range(201):
            right=left+30
            uses={x:int(required[x]) for x in range(left,right+1) if live[x]}
            colors=set(uses.values())
            if len(colors)>9:
                return None,f'cota negativa G2T-A: mas de nueve colores en x{left}..{right}'
            if len(colors)!=9:continue
            key=tuple((x-left,c) for x,c in uses.items()),left%8
            if key in seen:continue
            seen.add(key)
            slots=[x for x in range(left,right+1) if x%8==7]
            if not certificate(uses,slots)['feasible']:
                return None,f'cota negativa G2T-A: nueve colores en x{left}..{right}'
    req = np.full((8, 256), -1, dtype=np.int32)
    for x, r in enumerate(idx):
        if r and overlay[x] < 0:
            req[r, x] = base[r, x]
    colors = sorted(set(int(c) for c in overlay if c >= 0))
    prefix, nb = prefix_of(words, row)
    initial = [0]*8
    for reg, value in prefix:
        if 0x182 <= reg <= 0x18E:
            initial[(reg-0x180)//2] = value & 0xFFF
    fixed = [(x, x, reg, value) for x, reg, value in T.timeline(words, row)
             if x >= 0 and not 0x182 <= reg <= 0x18E and reg != 0x1FE]
    # Una recarga original que cruza un pixel usado tiene que conservar
    # su fase exacta: no se puede sustituir por una carga adelantada.
    late = palette(words, row, phase_max)
    locked = {r for r in range(1, 8) if np.any(
        (idx == r) & (overlay < 0) & (base[r] != late[r]))}
    locked_events = [(x,x,reg,value) for x,reg,value in T.timeline(words,row)
                     if x >= 0 and (reg-0x180)//2 in locked and 0x182 <= reg <= 0x18E]
    end = L.end_of(next_nb)
    if end is None:
        return None, 'borrado siguiente fuera del modelo'
    attempts = []
    occupied=np.flatnonzero(overlay>=0)
    cuts=np.flatnonzero(np.diff(occupied)>8)+1
    clusters=np.split(occupied,cuts)
    for grouped,strict_span in ((False,True),(False,False),(True,True),(True,False)):
        if grouped and len(clusters)<2:
            continue
        candidates = []
        pieces=[(color,np.flatnonzero(overlay==color)) for color in colors] if not grouped else [
            (color,part[overlay[part]==color]) for part in clusters
            for color in sorted(set(int(overlay[x]) for x in part))]
        for color,xs in pieces:
            cands = []
            for r in range(1, 8):
                check = req[r, xs[0]:xs[-1]+1] if strict_span else req[r, xs]
                if np.all((check < 0) | (check == color)):
                    test = req.copy()
                    test[r, xs] = color
                    cands.append((len(transitions(test, initial)[0]), r))
            candidates.append((color, xs, [r for _, r in sorted(cands)]))
        candidates.sort(key=lambda p: len(p[2]))
        if any(not c[2] for c in candidates):
            continue

        # Una DFS cortada a las primeras 64 asignaciones sesgaba el
        # resultado hacia el primer registro del primer color. Conservar
        # las mejores asignaciones parciales permite completar cifras
        # multicolor sin confundir ese limite con falta de colores.
        beam=[(req, [])]
        for color,xs,regs in candidates:
            expanded=[]
            for required,mapping in beam:
                for r in regs:
                    if np.any((required[r,xs]>=0)&(required[r,xs]!=color)):
                        continue
                    nxt=required.copy(); nxt[r,xs]=color
                    jobs,init=transitions(nxt,initial,locked,phase_max)
                    if any(lo>hi for lo,hi,_,_ in jobs):
                        continue
                    expanded.append((len(jobs),nxt,mapping+[(color,r,tuple(int(x) for x in xs))]))
            beam=[(nxt,mapping) for _,nxt,mapping in sorted(expanded,key=lambda p:p[0])[:512]]
        for required,mapping in beam:
            jobs,init=transitions(required,initial,locked,phase_max)
            attempts.append((len(jobs),jobs,init,mapping))
        for _, jobs, init, mapping in sorted(attempts, key=lambda p: p[0]):
            # Caso barato: prestar un registro en el borrado y conservar
            # todas las recargas, incluidas las que rozan un pixel visible.
            # La comprobacion por fase decide si el prestamo es valido.
            borrowed = {}
            for color,r,xs in mapping:
                borrowed.setdefault(0x180+2*r,color)
            unchanged = [
                (reg, (value & 0xF000) | borrowed.get(reg, value & 0xFFF))
                if i < len(prefix) and reg in borrowed else (reg, value)
                for i, (reg, value) in enumerate(words)]
            head = [(reg, ((value & 0xF000) | init[(reg-0x180)//2]) if 0x182 <= reg <= 0x18E else value)
                    for reg, value in prefix]
            out_idx = idx.copy()
            for color,r,xs in mapping:
                out_idx[list(xs)] = r
            for mode in ('borrow', 'replan'):
                if mode == 'borrow':
                    new = unchanged
                else:
                    # El cruce PAL255 tiene un contrato separado; nunca
                    # inventar un WAIT de esa fila con el modelo normal.
                    if row == L.WRAP_SEG:
                        continue
                    start = L.T0+max(0, 16*(nb-9))
                    body = schedule(jobs+fixed+locked_events, start, end, capacity-len(head)-3, row,
                                    max_states=search_states,budget=budget)
                    if body is None:
                        continue
                    new = head+list(body)
                ok = len(new)+3 <= capacity
                for phase in range(phase_max+1):
                    old_pal, new_pal = palette(words, row, phase), palette(new, row, phase)
                    expected = np.where(overlay >= 0, overlay, old_pal[idx, np.arange(256)])
                    actual = new_pal[out_idx, np.arange(256)]
                    ok &= bool(np.all((actual == expected) | ((idx == 0) & (overlay < 0))))
                if not ok:
                    continue
                old_fixed = [(x,r,v) for x,r,v in T.timeline(words,row) if x>=0 and not 0x182<=r<=0x18E and r!=0x1FE]
                new_fixed = [(x,r,v) for x,r,v in T.timeline(new,row) if x>=0 and not 0x182<=r<=0x18E and r!=0x1FE]
                assert old_fixed == new_fixed
                assert all(x <= end for x,_,_ in T.timeline(new,row) if x>=0)
                maps=[dict(color=color,index=r,xs=list(xs)) for color,r,xs in mapping]
                return dict(words=new, indices=out_idx.tolist(), mapping=maps,
                            transitions=len(jobs), fixed=len(fixed), bytes=4*(len(new)+3), mode=mode), None
        attempts.clear()
    return None, ('presupuesto de busqueda agotado; no prueba imposibilidad' if budget[0]<=0
                  else 'busqueda sin plan; no prueba imposibilidad')


def overlays(oam, bank):
    out = np.full((224,256), -1, dtype=np.int32)
    entries = sorted({e for groups in OAM_GROUPS.values() for first,n in groups for e in range(first,first+n)})
    pals = struct.unpack_from('>128H', bank, B.PALETTE)
    for e in entries:
        x,y,t,attr = oam[4*e:4*e+4]
        hi = oam[256+e]
        x |= (hi & 1)<<8
        if x >= 256:
            x -= 512
        width = 16 if hi & 2 else 8
        # mspr/g5l: la fila de copper es y de OAM + 1.
        y += 1
        if y>=224 or x+width<=0 or x>=256:
            continue
        px = B.ficha(bank, t | (attr & 1)<<8, width, bool(attr & 64), bool(attr & 128))
        for dy, line in enumerate(px):
            if not 0 <= y+dy < 224:
                continue
            for dx, value in enumerate(line):
                if value and 0<=x+dx<256 and out[y+dy,x+dx]<0:
                    out[y+dy,x+dx] = pals[16*((attr>>1)&7)+value]
    return out


def hardware_hidden(g,rec,tab,gfx):
    """Mascara de hardware de esta foto; solo objetos delante de PF1."""
    import g7_hw_support as H
    return H.visibility(g,rec,g.mem.r32(g.fr.vars+g.s['V_BACK']))


def render_step(g):
    s,mem,cpu,addr = g.s,g.mem,g.cpu,g.addr
    photo = mem.r16(g.dc+s['DC_NEW'])
    rec = addr('dc_rec')+photo*s['DC_REC']
    mem.w16(g.dc+s['DC_REND'],photo)
    mem.w16(g.fr.vars+s['V_S'],mem.r16(rec+s['R_S']))
    cpu.cpu.w_reg(cpu.M.Register.D0,mem.r8(rec+s['R_COIN']))
    for routine in ('coin_prepare','apply_colors','set_pointers','build_mid','coin_list','g5l_render','g7_select','g7_columns'):
        if routine=='g5l_render':
            cpu.cpu.w_reg(cpu.M.Register.A0,rec)
        g.fr.call(addr(routine),g.G.FAKE)
    cpu.cpu.w_reg(cpu.M.Register.D7,mem.r16(rec+s['R_TSEQ']))
    g.fr.call(addr('tile_apply'),g.G.FAKE)
    g.fr.call(addr('set_pointers'),g.G.FAKE)
    cpu.cpu.w_reg(cpu.M.Register.D7,photo)
    g.fr.call(addr('dc_hdr'),g.G.FAKE)
    g.fr.call(addr('g7_save'),g.G.FAKE)
    return rec, mem.r32(g.fr.vars+s['V_BACK'])


def finish_step(g, rec, back):
    s,mem = g.s,g.mem
    mem.w16(g.dc+s['DC_FRONT'],(rec-g.addr('dc_rec'))//s['DC_REC'])
    mem.w32(g.dc+s['DC_FLIST'],back)
    mem.w16(g.dc+s['DC_REND'],0xFFFF)
    mem.w32(g.fr.vars+s['V_BACK'],g.cops[(g.cops.index(back)+1)%3])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bin',required=True)
    ap.add_argument('--lst',required=True)
    ap.add_argument('--sources',default='work/g7/sources.bin')
    ap.add_argument('--from-k',type=int,default=409)
    ap.add_argument('--to-k',type=int,default=409)
    ap.add_argument('--out',default='work/g7-plan')
    ap.add_argument('--phase-max',type=int,choices=range(8),default=0,
                    help='0: contrato G2T-A medido; 7: margen adicional exploratorio')
    ap.add_argument('--search-states',type=int,default=3000,
                    help='limite de estados por asignacion; agotarlo no demuestra imposibilidad')
    ap.add_argument('--row-states',type=int,default=30000,
                    help='presupuesto compartido entre todas las asignaciones de una fila')
    a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    bank=Path(a.sources).read_bytes()
    g=L.GameRun(a.bin,a.lst,'work/g3/bank')
    s,mem,cpu=g.s,g.mem,g.cpu
    gfx=cpu.read(g.addr('gfx32'),23808)
    tab=L.Table(cpu.read(g.addr('g5l_table'),g.addr('g5l_cdma_src')-g.addr('g5l_table')))
    size=len(Path('work/yi1_s_g5.dat').read_bytes())
    stats=collections.Counter(); failures=[]; witnesses=[]; cache={}
    for k in range(min(g.n,a.to_k+1)):
        if k:
            g.fr.call(g.addr('dc_cop'),g.G.FAKE)
        rec,back=render_step(g)
        if k>=a.from_k and mem.r8(rec+s['R_SWS_VALID']):
            oam=cpu.read(rec+s['R_OAM'],320)
            overlay=overlays(oam,bank)
            hidden=hardware_hidden(g,rec,tab,gfx)
            stats['pixels_behind_hardware']+=int(np.count_nonzero((overlay>=0)&hidden))
            overlay[hidden]=-1
            data=cpu.read(g.G.DATA,size)
            camera=mem.r16(rec+s['R_S'])
            for row in np.flatnonzero(np.any(overlay>=0,axis=1)):
                row=int(row)
                words,_=T.segment_words(mem,back,s['CL_LINES'],s['SEG'],row)
                nxt,_=T.segment_words(mem,back,s['CL_LINES'],s['SEG'],(row+1)%224)
                _,nb=prefix_of(nxt,(row+1)%224)
                idx=terrain(data,camera,row)
                # Los bobs van detras de hardware. Estos indices no
                # requieren un color concreto mientras Mario los tapa.
                idx[hidden[row]]=0
                key=(row,tuple(map(tuple,words)),idx.tobytes(),overlay[row].tobytes(),nb)
                if key not in cache:
                    cache[key]=plan_line(words,row,idx,overlay[row],nb,phase_max=a.phase_max,
                                         search_states=a.search_states,row_states=a.row_states)
                    stats['unique_rows']+=1
                plan,reason=cache[key]
                stats['rows']+=1
                if plan is None:
                    stats['unresolved']+=1
                    if len(failures)<1000:
                        failures.append(dict(k=k,row=row,camera=camera,reason=reason,
                            words=words,indices=idx.tolist(),overlay=overlay[row].tolist(),next_nb=nb,phase_max=a.phase_max))
                    if stats['unresolved'] <= 10:
                        print('UNRESOLVED', k, row, reason, flush=True)
                else:
                    stats['planned']+=1
                    stats[plan['mode']]+=1
                    stats['max_bytes']=max(stats['max_bytes'],plan['bytes'])
                    if len(witnesses)<16:
                        witnesses.append(dict(k=k,row=row,camera=camera,original=words,**plan))
        finish_step(g,rec,back)
        if k and k%500==0:
            print(k,dict(stats),flush=True)
    result=dict(stats=dict(stats),failures=failures,witnesses=witnesses,
        scope='lista real/MAP/OAM de Musashi; cadencia ideal sin DMA; no es codigo del juego',
        phase_max=a.phase_max, search_states=a.search_states,row_states=a.row_states,beam_width=512,
        timing_contract='G2T-A: informe-g2t-a-1007.md secciones 4-6')
    (out/'report.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    ok=not stats['unresolved']
    print('G7 COLOR PLAN: '+('OK ' if ok else 'FALLA ')+json.dumps(dict(stats)),flush=True)
    return 0 if ok else 1


if __name__=='__main__':
    raise SystemExit(main())
