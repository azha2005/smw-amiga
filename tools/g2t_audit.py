#!/usr/bin/env python3
"""G2T: alternativas offline. No modifica A3/A5 ni autoriza G5 B/C.

El modelo de hueco horizontal es una cota lógica: escribir tras x255
permite cambios entre filas contiguas. NO demuestra ranuras de copper.
El diagnóstico de build_mid lee listas reales, sin extrapolar h > $CE.
"""
import argparse
import collections
import hashlib
import json
import os
import struct
from pathlib import Path

import g5ref as R
import sprgfx_bank as B
import sprgfx_final as F
import scrollprof as P
import scrollsim as S


def desired(pose, sy, masks, colors):
    rows = [{i: colors[i] for i in range(1, 16) if masks[y] & 1 << i}
            for y in range(224)]
    top = sy + pose['origin'][1]
    for r, row in enumerate(pose['row_maps']):
        if 0 <= top + r < 224:
            for _, _, i, color in row:
                F.require(i not in rows[top+r] or rows[top+r][i] == color, 'reserva incompatible')
                rows[top+r][i] = color
    return rows


def windows(rows, colors, horizontal=False):
    """Líneas de escritura: A5 original o cota tras el último píxel de fila.

    Cada escritura en línea L se supone DESPUÉS de todos sus píxeles.
    horizontal=True incluye la fila del uso anterior; no añade slots.
    """
    writes = R.color_writes(rows, colors)
    if horizontal:
        for w in writes:
            w['lo'] = max(0, w['lo'] - 1)
    return writes


def intervals(pose, sx, sy, mario, colors):
    """Envolvente inclusiva de cada índice en X/Y, sin quitar oclusiones.

    Mario se reconstruye desde su VRAM dinámica y Rex desde DMA inmutable.
    Unir min/max reserva también huecos: conservador, no alias de píxeles.
    """
    uses = collections.defaultdict(dict)
    def add(x, y, i, color, owner):
        if not (0 <= x < 256 and 0 <= y < 224):
            return
        old = uses[i].get(y)
        if old:
            F.require(old['color'] == color, 'dos colores por índice en la misma fila')
            old['first'] = min(old['first'], x)
            old['last'] = max(old['last'], x)
            old['owners'] = ''.join(sorted(set(old['owners'] + owner)))
        else:
            uses[i][y] = dict(first=x, last=x, color=color, owners=owner)
    for (x, y), (i, _) in mario.items():
        add(x, y, i, colors[i], 'M')
    x0, y0 = sx + pose['origin'][0], sy + pose['origin'][1]
    for r, row in enumerate(pose['rows']):
        cmap = {i: c for _, _, i, c in pose['row_maps'][r]}
        for x, i in enumerate(row):
            if i:
                add(x0+x, y0+r, i, cmap[i], 'R')
    result = []
    for i, lines in sorted(uses.items()):
        previous, value = None, colors[i]
        for y, use in sorted(lines.items()):
            if use['color'] != value:
                result.append(dict(indice=i, valor=use['color'],
                    despues=previous, antes=dict(linea=y, x=use['first'], owners=use['owners'])))
                value = use['color']
            previous = dict(linea=y, x=use['last'], owners=use['owners'])
    return result


def stable_assignment(pose, sy, masks, colors, max_attempts=10000):
    """Ensayo suficiente: un índice exclusivo por color en TODA la pose.

    Prohíbe además pisar reservas de Mario en filas adyacentes. Así no
    necesita transición de fila contigua; puede ser más fuerte de lo
    necesario. Un límite de búsqueda es indeterminado, nunca imposible.
    """
    top = sy + pose['origin'][1]
    palette = sorted({c for row in pose['row_maps'] for _, _, _, c in row})
    allowed = {c: set(range(1,16)) for c in palette}
    for r, row in enumerate(pose['row_maps']):
        if not 0 <= top+r < 224:
            continue
        for _, _, _, c in row:
            for y in range(max(0,top+r-1), min(224,top+r+2)):
                allowed[c] -= {i for i in range(1,16) if masks[y] & 1 << i and colors[i] != c}
    answer, attempts = {}, 0
    def search():
        nonlocal attempts
        attempts += 1
        if attempts > max_attempts:
            return False
        if len(answer) == len(palette):
            return True
        used = set(answer.values())
        remaining = {c: allowed[c] - used for c in palette if c not in answer}
        c = min(remaining, key=lambda k:(len(remaining[k]),k))
        for i in sorted(remaining[c]):
            answer[c] = i
            if search():
                return True
        answer.pop(c, None)
        return False
    good = search()
    return (answer if good else None), ('ok' if good else 'indeterminado' if attempts > max_attempts else 'sin_asignacion')


def arm(top):
    return [dict(tipo='pt' if j < 8 else 'ctl', lo=0, hi=top-1, ordinal=j) for j in range(16)]


def place_variable(colors, controls, capacities):
    """Igual orden que A5; capacidad por línea y búsqueda hacia atrás."""
    lines, missed = [[] for _ in capacities], []
    hi = controls[-1]['hi'] if controls else len(lines)-1
    for move in reversed(controls):
        for y in range(min(move['hi'],hi,len(lines)-1),max(move['lo'],0)-1,-1):
            if len(lines[y]) < capacities[y]:
                lines[y].insert(0,dict(move,linea=y))
                hi=y
                break
        else:
            missed.append(move)
    for move in colors:
        for y in range(min(move['hi'],len(lines)-1),max(move['lo'],0)-1,-1):
            if len(lines[y]) < capacities[y]:
                lines[y].append(dict(move,linea=y))
                break
        else:
            missed.append(move)
    return lines,missed


def suffix(mem, base, line):
    """Cargas reales antes de COP2LC. Tiempo solo dentro de modelo medido.

    Nunca convierte h tardío no calibrado a x/ciclos. Cuenta las cargas
    posteriores al último WAIT; la regla C2 sobre ese WAIT es OPTIMISTA.
    """
    start = base + 216 + 220*line
    v, nb, active, t, last_h, after = line+44, 0, False, None, None, 0
    for offset in range(0,220,4):
        w1,w2 = mem.r16(start+offset),mem.r16(start+offset+2)
        if w1 == 0x84:
            if not active:
                t = S.T0 + max(0,16*(nb-9))
            return dict(offset_salto=offset, ultimo_wait_h=last_h,
                        move_despues_wait=after, x_modelo_siguiente=t, borrado_move=nb)
        if w1 & 1:
            if w1 >> 8 == (v-1) & 255:
                continue
            if not active:
                active, t = True, S.T0 + max(0,16*(nb-9))
            h = w1 & 0xfe
            F.require(h <= 0xce, 'h fuera del modelo medido de scrollsim')
            t = max(S.advance(t,2),S.xh(h))
            last_h,after = h,0
        elif not active and w1 != 0x1fe:
            nb += 1
        else:
            if not active:
                active,t = True,S.T0 + max(0,16*(nb-9))
            t = S.advance(t)
            after += 1
    raise F.FormatError('salto no encontrado')


def read_bank(path):
    tables, dma = Path(path+'.idx').read_bytes(),Path(path+'.dma').read_bytes()
    poses,index = B.deserialize_bank(tables,dma)
    directory = {}
    for j in range(struct.unpack_from('>H',index,6)[0]):
        _,_,_,count,ptr = struct.unpack_from('>IBBHI',index,8+12*j)
        variants = list(struct.unpack_from('>%dH'%count,index,ptr))
        directory[B.shape(poses[variants[0]])] = variants
    return tables,dma,poses,directory


def run(args):
    F.derived_path(args.out)
    os.makedirs(args.out,exist_ok=True)
    tables,dma,poses,directory = read_bank(args.bank)
    gfx=Path('work/cc/gfx32.bin').read_bytes()
    pals=Path('work/cc/mario_pal.bin').read_bytes()
    masktable=R.mask_table(gfx)
    rom=Path(R.mkmario.ROM).read_bytes()
    head=len(rom)%1024
    pointers=[struct.unpack_from('<H',rom,head+((R.mkmario.DATA_00E2A2+2*a)&0x7fff))[0] for a in range(8)]
    code,lst=P.assemble('player/scroll.s',['VIS=256','SPRITES'])
    syms,local=P.listing(lst)
    F.require(syms['CL_LINES']==216 and syms['SEG']==220,
              'layout de scroll distinto: actualizar el lector de sufijos')
    V={n:v for n,v in syms.items() if n.startswith('V_')}
    S.W,S.T0=256,-120
    summary=dict(contrato='G2T revisión, NO puerta G5', hardware_validado=False,
        banco_dma=len(dma), tablas=len(tables), trazas={}, testigo=None,testigo_visible=None)
    all_samples=[]
    stable_catalogue={}
    for pair in args.trace:
        path,oracle=pair.split('=',1)
        name=Path(path).stem.removeprefix('oam_')
        groups=collections.defaultdict(list)
        for rec in R.read_trace(path,oracle):
            groups[rec['frame']].append(rec)
        counters=collections.Counter()
        cases=[]
        sc=P.Scroll(code,syms,local,Path('work/yi1_s.dat').read_bytes(),V)
        sc.init()
        for frame,recs in sorted(groups.items()):
            rex=[r for r in recs if r['num']==0xab]
            if not rex:
                continue
            chosen=min(rex,key=lambda r:(r['sy']+poses[directory[B.shape(r)][0]]['origin'][1],r['slot']))
            ram=chosen['ram']
            pi=R.palette_index(ram,pointers)
            colors=struct.unpack_from('>16H',pals,32*pi)
            masks=R.table_rows(ram,chosen['recorded'],masktable)
            variants=[n for n in directory[B.shape(chosen)] if R.first_compatible([n],poses,chosen['sy'],masks,colors)==n]
            F.require(bool(variants),'sin variante compatible')
            cam=ram[0x1a] | ram[0x1b]<<8
            camy=ram[0x1c] | ram[0x1d]<<8
            sc.mem.w16(sc.vars+V['V_S'],cam)
            sc.call('scroll_frame')
            base=sc.mem.r32(P.FAKE+0x80)
            endings=[suffix(sc.mem,base,y) for y in range(224)]
            capacities=[min(8,max(0,(0xe2-e['ultimo_wait_h'])//8))
                        if e['ultimo_wait_h'] is not None else 8 for e in endings]
            results=[]
            for n in variants:
                rows=desired(poses[n],chosen['sy'],masks,colors)
                top=chosen['sy']+poses[n]['origin'][1]
                old=windows(rows,colors)
                blank=windows(rows,colors,True)
                _,oldmiss=R.place_writes(old,arm(top))
                lines,miss=R.place_writes(blank,arm(top))
                timed,timemiss=place_variable(blank,arm(top),capacities)
                # C2 es solo una cota optimista, no prueba de slots: ni
                # incluye MOVE tras WAIT, WAIT del bloque, salto ni DMA.
                reject=[]
                for y,moves in enumerate(lines):
                    if not moves:
                        continue
                    last=endings[y]['ultimo_wait_h']
                    if last is not None and last > 0xe2-8*len(moves):
                        reject.append(y)
                results.append(dict(variante=n,vacias=sum(w['lo']>w['hi'] for w in old),
                    sin_plazo_a5=len(oldmiss),sin_plazo_cota_horizontal=len(miss),
                    lineas_rechazadas_c2=reject,sin_plazo_c2_optimista=len(timemiss),
                    max_move=max(map(len,timed)),lineas=timed))
            first=results[0]
            counters['frames']+=1
            counters['compatibles']+=len(variants)
            counters['vacias_primera']+=first['vacias']
            counters['frames_con_vacias']+=bool(first['vacias'])
            counters['frames_a5_otra_sin_vacias']+=bool(first['vacias'] and any(not r['vacias'] for r in results[1:]))
            counters['frames_a5_sin_plan']+=not any(not r['sin_plazo_a5'] for r in results)
            feasible=[r for r in results if not r['sin_plazo_cota_horizontal']]
            counters['frames_horizontal_sin_plan_cota8']+=not bool(feasible)
            tested=[r for r in feasible if not r['sin_plazo_c2_optimista']]
            counters['frames_horizontal_rechazados_c2_todas_variantes']+=not bool(tested)
            counters['frames_camera_y_no192']+=camy!=192
            stable,status=stable_assignment(poses[variants[0]],chosen['sy'],masks,colors)
            counters['frames_estable_'+status]+=1
            if stable is not None:
                pose=poses[variants[0]]
                cmap=[{i:c for _,_,i,c in row} for row in pose['row_maps']]
                newrows=[[stable[cmap[y][i]] if i else 0 for i in row] for y,row in enumerate(pose['rows'])]
                newmaps=[[(p,i,stable[c],c) for p,i,_,c in row] for row in pose['row_maps']]
                identity=(B.shape(pose),tuple(tuple(row) for row in newmaps))
                stable_catalogue.setdefault(identity,dict(pose,rows=newrows,row_maps=newmaps,
                    columns=(pose['width']+15)//16,source=0xffffffff,mask=0xffffffff))
            pick=(tested or feasible or results)[0]
            counters['max_move_c2_optimista']=max(counters['max_move_c2_optimista'],pick['max_move'])
            # Cota de color exacta solo en el modelo que escribe después
            # del último píxel. No usa esos ceros como validación hardware.
            if not pick['sin_plazo_c2_optimista']:
                states=R.simulate(pick['lineas'],colors)
                want=desired(poses[pick['variante']],chosen['sy'],masks,colors)
                errors=sum(states[y][i]!=c for y,row in enumerate(want) for i,c in row.items())
                F.require(errors==0,'cota horizontal altera usos de color')
                counters['frames_color_cota_comprobados']+=1
            item=dict(frame=frame,slot=chosen['slot'],sx=chosen['sx'],sy=chosen['sy'],
                cam_x=cam,cam_y=camy,primera={k:v for k,v in first.items() if k!='lineas'},
                candidata={k:v for k,v in pick.items() if k!='lineas'},estable=status)
            if name=='yi1' and frame==5811:
                pixelwindows=intervals(poses[variants[0]],chosen['sx'],chosen['sy'],
                    R.mario_pixels(ram,chosen['recorded'],gfx),colors)
                y=168
                summary['testigo']=dict(item,ventanas_pixel=pixelwindows,
                    suffix_y168=endings[y],cargas_y168=pick['lineas'][y])
            if summary['testigo_visible'] is None and first['vacias']:
                pix=intervals(poses[variants[0]],chosen['sx'],chosen['sy'],
                    R.mario_pixels(ram,chosen['recorded'],gfx),colors)
                adjacent=[w for w in pix if w['despues'] is not None
                          and w['antes']['linea']==w['despues']['linea']+1]
                if adjacent:
                    y=adjacent[0]['despues']['linea']
                    summary['testigo_visible']=dict(traza=name,**item,
                        ventana_pixel=adjacent[0],suffix=endings[y],escrituras=pick['lineas'][y])
            if first['vacias'] or not tested or stable is None:
                cases.append(item)
            if len(all_samples)<12 and (not tested or frame==5811):
                all_samples.append(dict(traza=name,**item))
        summary['trazas'][name]=dict(counters)
        Path(args.out,'casos_'+name+'.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
        print(name,json.dumps(dict(counters),sort_keys=True),flush=True)
    # Presupuesto real de la alternativa estable solo sobre frames elegidos,
    # NO sustituye las 2593 peticiones/ocho paletas y 48 formas legales G3.
    catalogue=list(stable_catalogue.values())
    blobs=[F.channel(p['rows'],c,h) for p in catalogue for c in range(p['columns']) for h in (0,1)]
    chip,offsets=B.compact(blobs)
    packed=[dict(p,streams=[[offsets[F.channel(p['rows'],c,h)] for h in (0,1)] for c in range(p['columns'])]) for p in catalogue]
    holder=F.Bank(0xffffffff)
    holder.data=bytearray(chip)
    metadata=bytearray(F.serialize(packed,holder))
    struct.pack_into('>4sH',metadata,0,b'SG3F',2)
    decoded=B.decode(metadata,chip,limit=0xffffffff)
    vram,_,_=R.G.build_vram(R.G._DEF_SRC,R.G.LEVEL)
    cg=R.G.level_cgram(R.G._DEF_SRC,R.G.LEVEL)
    checked=F.verify(vram,cg,decoded)
    F.evidence(vram,cg,decoded,str(Path(args.out,'estable.png')))
    index=B.directory(metadata,decoded)
    stable_tables=bytes(metadata)+index+struct.pack('>4sI',b'S2IX',len(metadata))
    summary['ensayo_estable']=dict(descriptores=len(packed),formas=len({B.shape(p) for p in packed}),
        chip=len(chip),tablas=len(stable_tables),pixeles_verificados=checked,cobertura_completa=False,
        omitidos=sum(t.get('frames_estable_sin_asignacion',0)+t.get('frames_estable_indeterminado',0) for t in summary['trazas'].values()))
    Path(args.out,'estable.dma').write_bytes(chip)
    Path(args.out,'estable.idx').write_bytes(stable_tables)
    summary['sha256_banco_original']={suffix:hashlib.sha256(Path(args.bank+suffix).read_bytes()).hexdigest() for suffix in ('.idx','.dma')}
    Path(args.out,'resumen.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    Path(args.out,'muestra_casos.json').write_text(json.dumps(all_samples,indent=2),encoding='utf-8')
    print('estable:',summary['ensayo_estable'])
    print('REVISION: hardware_validado=False; G5 B/C siguen detenidas.')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--trace',action='append',required=True)
    ap.add_argument('--bank',default='work/g3/bank')
    ap.add_argument('--out',default='work/g2t')
    run(ap.parse_args())


if __name__=='__main__':
    main()
