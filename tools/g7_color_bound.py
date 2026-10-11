#!/usr/bin/env python3
"""Cota de paleta local, independiente del asignador heuristico G7.

Prueba un intervalo con nueve colores, siete registros y como maximo dos
MOVE de COLOR. Explora todas las caches iniciales y las dos cargas. La
rejilla/espaciado son los del contrato G2T-A, no una prueba sobre otros
modos DMA ni sobre un futuro plan que cambie esa temporizacion.
"""
import argparse
import itertools
import json
from pathlib import Path

from PIL import Image, ImageDraw

from g7_color_plan import palette
from g5l import rgb12


def certificate(uses, slots, registers=7):
    colors=set(uses.values())
    assert len(colors)==registers+2,'la cota requiere exactamente dos colores adicionales'
    assert slots==sorted(set(slots))
    assert not any(c-a>=32 and b-a>=16 and c-b>=16 for a,b,c in itertools.combinations(slots,3)), 'mas de dos MOVE posibles'
    checked=0; witness=None
    for missing in itertools.combinations(sorted(colors),2):
        for loads in itertools.permutations(missing):
            initial=colors-set(missing)
            for times in itertools.combinations(slots,2):
                if times[1]-times[0]<16:continue
                states=[(initial,[])]
                last=min(uses)-1
                for t,color in zip(times,loads):
                    nxt=[]
                    for cache,history in states:
                        if any(c not in cache for x,c in uses.items() if last<x<t):continue
                        for victim in cache:
                            fresh=(cache-{victim})|{color}
                            checked+=1
                            # Sin recargas: nueve colores distintos y dos
                            # MOVE obligan a conservar todo uso futuro.
                            if any(c==victim for x,c in uses.items() if x>=t):continue
                            nxt.append((fresh,history+[(t,victim,color)]))
                    states=nxt;last=t-1
                for cache,history in states:
                    if all(c in cache for x,c in uses.items() if x>=times[-1]):
                        witness=history;break
                if witness is not None:break
            if witness is not None:break
        if witness is not None:break
    return dict(colors=sorted(colors),registers=registers,slots=slots,
                max_moves=2,candidates_checked=checked,feasible=witness is not None,witness=witness)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--report',required=True)
    ap.add_argument('--frame',type=int,default=6047);ap.add_argument('--row',type=int,default=161)
    ap.add_argument('--left',type=int,default=151);ap.add_argument('--right',type=int,default=181)
    ap.add_argument('--out',default='work/g7-bound')
    a=ap.parse_args()
    data=json.loads(Path(a.report).read_text())
    assert data.get('phase_max',0)==0,'usar el contrato calibrado, no el margen exploratorio'
    f=next(f for f in data['failures'] if f['k']==a.frame and f['row']==a.row)
    pal=palette(f['words'],a.row)
    uses={x:(f['overlay'][x] if f['overlay'][x]>=0 else int(pal[f['indices'][x],x]))
          for x in range(a.left,a.right+1) if f['overlay'][x]>=0 or f['indices'][x]}
    # Antes del codo: WAIT solo da x = 7 mod 8, cadena avanza 16.
    assert a.right<231 and a.right-a.left<32
    slots=[x for x in range(a.left,a.right+1) if x%8==7]
    result=certificate(uses,slots)
    result.update(frame=a.frame,row=a.row,left=a.left,right=a.right,
                  uses=uses,scope='indices libres; siete registros PF1; contrato G2T-A; sin costes de sprites ni WAIT')
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    (out/'certificate.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    im=Image.new('RGB',(900,175),'#25252a');d=ImageDraw.Draw(im)
    d.text((10,8),f'G7: k{a.frame}, fila {a.row}, x={a.left}..{a.right}; 7 registros, 9 colores',fill='white')
    for x in range(a.left,a.right+1):
        xx=10+(x-a.left)*28
        d.rectangle((xx,35,xx+26,86),fill=rgb12(uses[x]) if x in uses else '#444444')
        d.text((xx,90),str(x),fill='white')
        if x in slots:d.text((xx,111),'MOVE',fill='#ffcc55')
    d.text((10,142),'Colores: '+', '.join(f'{c:03X}' for c in sorted(set(uses.values()))),fill='white')
    im.save(out/'window.png')
    print('G7 COLOR BOUND: '+('SIN PLAN EN ESTE CONTRATO ' if not result['feasible'] else 'FACTIBLE ')+json.dumps(result))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
