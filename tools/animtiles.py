#!/usr/bin/env python3
"""SW-A: ranuras animadas de CODE_05BB39 y GFX33, sin datos derivados en git."""
import argparse
from pathlib import Path
import struct

from smw2amiga import lc_lz2_decompress, decode_snes_tileset
from smwgen import parse_tables


def animation_wram(src):
    """CODE_00B888: 384 tiles de 3 bpp a 4 bpp en $7E7D00..$7EACFF."""
    data = lc_lz2_decompress((Path(src)/'graphics/anim.lz2').read_bytes())
    out = bytearray()
    for i in range(0, len(data), 24):
        t = data[i:i+24]
        out.extend(t[:16])
        for b in t[16:]:
            out.extend((b, 0))
    return bytes(out)


def graphics_wram(src):
    out=bytearray(0x10000)
    chr=lc_lz2_decompress((Path(src)/'graphics/chr.lz2').read_bytes())
    out[0x2000:0x2000+len(chr)]=chr
    anim=animation_wram(src)
    out[0x7d00:0x7d00+len(anim)]=anim
    return bytes(out)


def slots(src, tileset=7, phase=0, pow_timers=(0, 0, 0)):
    """{tile VRAM: 128 bytes} para las 18 entradas, paso & $18 / 8.

    Cada grupo de tres se renueva en FrameB & 7. Los seis ultimos
    destinos nulos no se suben. Se reproduce la seleccion de las tablas
    originales, incluido el desplazamiento del tileset y el P switch.
    """
    t = parse_tables(str(Path(src)/'dialog.s'))
    dst = struct.unpack('<24H', t['DATA_05B93B'])
    raw = graphics_wram(src)
    out = {}
    for i, vma in enumerate(dst[:18]):
        j = i
        mode = t['DATA_05B96B'][i]
        if mode == 1 and pow_timers[t['DATA_05B97D'][i]]:
            j += 0x26
        elif mode == 2:
            j += t['DATA_05B98B'][tileset]
        addr = struct.unpack_from('<H', t['AnimatedTileData']+t['DATA_05BA39'], 8*j+2*phase)[0]
        start = addr
        assert 0 <= start <= len(raw)-128, (i, addr)
        out[vma//16] = raw[start:start+128]
    return out


def overlay(gfx, files, src, tileset=7, phase=0):
    """Completa los postes de YI1 con una fase de referencia congelada.

    Las ranuras ausentes del GFX estatico son $74-$77 (postes).
    Las otras ranuras ya tienen imagen estatica en el banco del nivel;
    se inventarian y verifican, sin cambiar sus fases al cerrar SW-A.
    """
    if tileset != 7 or len(files) != 4:
        return gfx
    for first, raw in slots(src, tileset, phase).items():
        if first != 0x74:
            continue
        for k, tile in enumerate(decode_snes_tileset(raw, 4)):
            # OBJECTGFXLIST se carga invertida: banco 0 = ultimo fichero.
            f = files[(first+k)//128]
            gfx[f][(first+k)%128] = tile
    return gfx


def main():
    import mklvl
    import lvdesc
    from map16 import Map16, TILESET_SET
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True, help='snesorc --vram --ram 8d00:ad00,d76:d82')
    a = ap.parse_args()
    src = Path(mklvl._DEF_SRC)
    h, _, lv = mklvl.build(lvdesc.load(None).obj, verbose=False)
    m = Map16(set_index=TILESET_SET.get(h['tileset'],0), tileset=h['tileset'])
    allslots = slots(src, h['tileset'])
    used = {}
    for y in range(lv.H):
        for x in range(lv.W):
            idx=lv.get(x,y)
            if idx is None:
                continue
            for tile, pal, pri, _, _ in m.get(idx,x//16) or ():
                if any(first <= tile < first+4 for first in allslots):
                    used.setdefault(tile,set()).add(idx)
    for tile, blocks in sorted(used.items()):
        first=next(f for f in allslots if f <= tile < f+4)
        changing=len({slots(src,h['tileset'],p)[first] for p in range(4)})>1
        print('%03X: Map16 %s; %s' % (tile, ','.join('%03X'%b for b in sorted(blocks)), 'animado' if changing else 'fijo'))
    checked = 0
    for p in sorted(Path(a.dir).glob('snes_*.vram')):
        rp=p.with_suffix('.ram')
        ram=rp.read_bytes() if rp.exists() else None
        vram=p.read_bytes()
        # --ram captura $8D00..$AD00 + $0D76..$0D82. Las tres copias
        # anunciadas por CODE_05BB39 son exactamente lo subido en NMI.
        dma=struct.unpack_from('<6H',ram,0x2000) if ram else (0,)*6
        for adr,vma in zip(dma[:3],dma[3:]):
            if not vma:
                continue
            # GFX32 contiene zonas que la logica sobrescribe (Mario).
            # El banco GFX33 convertido es la puerta de esta tarjeta.
            if adr < 0x7d00:
                continue
            expected=graphics_wram(src)[adr:adr+128]
            actual=vram[vma*2:vma*2+128]
            assert expected==actual,(p.name,hex(adr),hex(vma))
            checked+=128
        # Ademas, postes completos, incluso cuando esta fila no
        # actualiza su ranura: deben coincidir en todos los frames.
        phases=[phase for phase in range(4) if vram[0x740*2:0x780*2]==slots(src,h['tileset'],phase)[0x74]]
        assert phases,p.name
        print('%s postes fase %s' % (p.stem,phases))
    assert checked
    print('SW-A VRAM: %d bytes DMA exactos; postes %d/%d frames' % (checked,len(list(Path(a.dir).glob('snes_*.vram'))),len(list(Path(a.dir).glob('snes_*.vram')))))


if __name__=='__main__':
    main()
