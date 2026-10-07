"""Arnés G5a opt-in, descartable, con un Rex fijo del oráculo SOT1.

No cambia los builds normales ni convierte este caso en asignador G4.
Genera fuentes y datos exclusivamente en work/g5a; usa el banco base SG3F/1.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

import sprgfx_final as F
from g5a_probe import cases
from g0bench import control


def replace(text, old, new, count=1):
    F.require(text.count(old) == count, 'fuente cambió: ' + old[:80])
    return text.replace(old, new)


def build(args):
    out = Path('work/g5a')
    out.mkdir(exist_ok=True)
    case = next(c for c in cases() if c['frame'] == args.frame)
    metadata = Path('work/g5a_base.idx').read_bytes()
    bank = Path('work/g5a_base.dma').read_bytes()
    poses = F.deserialize(metadata, bank)
    F.require(len(poses) == 48 and len(bank) == 10840, 'banco base desconocido')
    pose = poses[case['pose']]
    F.require(pose['width'] <= 32 and pose['height'] == 32, 'caso requiere dos columnas,32 filas')
    _,_,_,_,_,_,_,_,so,ro,_,_ = struct.unpack_from(F.DESC, metadata, 24+32*case['pose'])
    streams = [x for c in range(2) for x in struct.unpack_from('>II',metadata,so+8*c)]
    # Primera pasada: mapas exactos por fila; no hay Mario opaco en esas Y.
    # Restituir los quince registros en la fila siguiente al Rex.
    pals = struct.unpack('>128H', Path('work/cc/mario_pal.bin').read_bytes())
    maps = [[] for _ in range(224)]
    for y,row in enumerate(pose['row_maps']):
        colors = dict((dma,color) for _,_,dma,color in row)
        maps[case['y']+y] = [(0x1a0+2*d,c) for d,c in sorted(colors.items())]
    maps[case['y']+pose['height']] = [(0x1a0+2*d,pals[d]) for d in range(1,16)]
    data,offsets,jobs = bytearray(),[],[]
    for y,row in enumerate(maps):
        offsets.append(len(data))
        if row:
            jobs.append((y,len(row),len(data)))
        data.extend(struct.pack('>H', len(row)))
        for reg,val in row:
            data.extend(struct.pack('>HH',reg,val))
    lines = ['; Datos derivados, generados por tools/g5a.py; solo en work/.', 'g5a_streams:']
    lines.append('        dc.l ' + ','.join(map(str,streams)))
    lines.append('g5a_controls:')
    lines += ['        ifd G5A_NODMA', '        rept 8', '        dc.l $01fe0000',
              '        endr', '        else', '        ifd G5A_EMPTY', '        rept 8',
              '        dc.l $01fe0000', '        endr', '        else']
    for ch in range(4,8):
        pos,ctl = control(case['x']+16*((ch-4)//2),case['y']+44,case['y']+44+32,ch)
        lines.append('        dc.w $%04x,$%04x,$%04x,$%04x' % (0x140+8*ch,pos,0x142+8*ch,ctl))
    lines += ['        endc', '        endc']
    lines.append('g5a_offsets:')
    for at in range(0,224,16):
        lines.append('        dc.w '+','.join(map(str,offsets[at:at+16])))
    lines.append('g5a_jobs:')
    lines.append('        dc.w '+str(len(jobs)))
    lines += ['        dc.w '+','.join(map(str,j)) for j in jobs]
    lines.append('g5a_rows:')
    for at in range(0,len(data),16):
        lines.append('        dc.b '+','.join('$%02x'%x for x in data[at:at+16]))
    (out/'data.i').write_text('\n'.join(lines)+'\n')
    scroll = Path('player/scroll.s').read_text()
    scroll = replace(scroll,'CL_LINES    equ CL_COL17+60','CL_LINES    equ CL_COL17+60+32')
    scroll = replace(scroll,'SEG         equ 64+MIDMAX*12+12','SEG         equ 284')
    scroll = replace(scroll,'        ; lineas\n        move.l  a3,a1',
                     '        moveq #7,d0\n.g5ctl: move.l #$01fe0000,(a0)+\n        dbf d0,.g5ctl\n        ; lineas\n        move.l  a3,a1')
    scroll = replace(scroll,'        move.l  a0,d0                       ; inicio de las cargas de la linea',
                     '        move.l a1,-(sp)\n        lea .g5ret(pc),a1\n        add.l #g5a_emit-.g5ret,a1\n        jsr (a1)\n.g5ret: move.l (sp)+,a1\n        move.l  a0,d0                       ; inicio de las cargas de la linea')
    (out/'scroll.s').write_text(scroll)
    game = Path('player/game.s').read_text()
    game = replace(game,'        include "player/scroll.s"','        include "work/g5a/scroll.s"')
    game = replace(game,'vars:   ds.b    V_SIZE',
                   'vars:   ds.b    V_SIZE\n        include "player/g5a.s"')
    game = replace(game,'binend:',
                   '        cnop 0,8\ng5a_dma: incbin "work/g5a_base.dma"\n        cnop 0,4\nbinend:')
    game = replace(game,'        move.b  spr_lv(pc),d0',
                   '        GETBASE a0\n        add.l #spr_lv-binstart,a0\n        move.b (a0),d0')
    game = replace(game,'        bsr     scroll_init\n        ifd     DECOUPLE',
                   '        bsr     g5a_init\n        bsr     scroll_init\n        ifd     DECOUPLE')
    game = replace(game,'        bsr     dc_hdr\n        bsr     dc_null',
                   '        bsr     dc_hdr\n        bsr     dc_null\n        bsr     g5a_apply',2)
    # Todo el coste G5a entra en sellos8/9 (build_mid); dc_hdr posterior
    # solo toca SPR0..3 y COLOR17..31 iniciales. PT/POS/CTL son independientes.
    marker = '        ifd     BENCH\n        GBR     9\n        endc\n        lea     dc_st(pc),a2'
    game = replace(game,marker,'        bsr     g5a_apply\n'+marker)
    (out/'game.s').write_text(game)
    # CHG contiene offsets de segmento de220B; adaptar solo su stride.
    dat = bytearray(Path('work/yi1_s.dat').read_bytes())
    chg, l2b = struct.unpack_from('>II',dat,28)
    for off in range(chg,l2b,8):
        x,ptr,cur,prev = struct.unpack_from('>4H',dat,off)
        if x == 65535:
            break
        struct.pack_into('>H',dat,off+2,(ptr//220)*284+ptr%220)
    (out/'scroll.dat').write_bytes(dat)
    case.update(bank_sha256=hashlib.sha256(bank).hexdigest(), moves_colors=sum(map(len,maps)),
                controls_moves=8, pointer_moves=8, jobs=len(jobs), segment=284,
                scope='Rex fijo, selección offline con pertenencia SOT1; no asignador final')
    (out/'case.json').write_text(json.dumps(case,indent=2))
    print(json.dumps(case,indent=2))


def read(args):
    from PIL import Image, ImageChops
    case=json.loads(Path('work/g5a/case.json').read_text())
    poses=F.deserialize(Path('work/g5a_base.idx').read_bytes(),Path('work/g5a_base.dma').read_bytes())
    p=poses[case['pose']]
    shot=Image.open(args.shot).convert('RGB')
    base=Image.open(args.base_shot).convert('RGB')
    # Capturador WinUAE x2, centro de pixel (P57), DIW256 desde(131,70).
    got=Image.new('RGB',(256,224))
    clean=got.copy()
    for y in range(224):
        for x in range(256):
            got.putpixel((x,y),shot.getpixel((131+2*x,70+2*y)))
            clean.putpixel((x,y),base.getpixel((131+2*x,70+2*y)))
    expected=clean.copy()
    for y,row in enumerate(p['rows']):
        colors={d:c for _,_,d,c in p['row_maps'][y]}
        for x,dma in enumerate(row):
            if dma:
                c=colors[dma]
                expected.putpixel((case['x']+x,case['y']+y),tuple(((c>>s)&15)*17 for s in(8,4,0)))
    bad=sum(a!=b for a,b in zip(expected.getdata(),got.getdata()))
    compare=Image.new('RGB',(256,448))
    compare.paste(expected,(0,0));compare.paste(got,(0,224))
    compare.resize((512,896),Image.Resampling.NEAREST).save('work/g5a/compare.png')
    ImageChops.difference(expected,got).save('work/g5a/diff.png')
    print('G5a: %d/57344 píxeles distintos; referencia=OAM exacta SOT1/SG3F + fondo A/B'%bad)
    F.require(bad==0,'captura Amiga distinta (incluye todo terreno y Mario)')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='command',required=True)
    b=sub.add_parser('build');b.add_argument('--frame',type=int,default=6277)
    r=sub.add_parser('read');r.add_argument('--shot',required=True);r.add_argument('--base-shot',required=True)
    args=ap.parse_args()
    {'build':build,'read':read}[args.command](args)
