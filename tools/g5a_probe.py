"""Inspección descartable G5a: casos Rex con pertenencia SOT1 exacta."""
import struct
import json
from pathlib import Path
import mksprgfx as G
import sprgfx_manifest as S
import sprgfx_final as F


def cases():
    meta = Path('work/g5a_base.idx').read_bytes()
    bank = Path('work/g5a_base.dma').read_bytes()
    poses = F.deserialize(meta, bank)
    recorded = {f: [o[i:i+5] for i in range(0, len(o), 5)]
                for f, o, _ in G.load_oam_bin('work/oracle_yi1_oam.bin')}
    gfx = Path('work/cc/gfx32.bin').read_bytes()
    with open('work/oam_yi1.trace', 'rb') as src:
        F.require(src.read(4) == b'SOT1', 'SOT1 ausente')
        mlen, = struct.unpack('<I', src.read(4))
        while head := src.read(8):
            f, slot, num, first, n = struct.unpack('<IBBBB', head)
            body = src.read(2 * (0x2000 + mlen))
            if num != 0xab or not 5145 < f < 7000:
                continue
            ram = body[0x2000+mlen:0x4000+mlen]
            sx = ((ram[0xe4+slot] | ram[0x14e0+slot] << 8) -
                  (ram[0x1a] | ram[0x1b] << 8)) & 65535
            sy = ((ram[0xd8+slot] | ram[0x14d4+slot] << 8) -
                  (ram[0x1c] | ram[0x1d] << 8)) & 65535
            entries = [ram[0x300+first+4*k:0x304+first+4*k] +
                       ram[0x460+first//4+k:0x461+first//4+k] for k in range(n)]
            visible = [e for e in entries if e[1] != 0xf0]
            if not visible:
                continue
            F.require(any(recorded[f][k:k+len(visible)] == visible
                          for k in range(len(recorded[f])-len(visible)+1)), 'OAM distinta')
            tiles = [[S.signed(e[0]-sx), S.signed(e[1]-sy), e[2] | (e[3]&1)<<8,
                      16 if e[4]&2 else 8, e[3]>>6&1, e[3]>>7, e[3]>>1&7] for e in visible]
            match = [i for i,p in enumerate(poses) if p['tiles'] == tiles and p['priority'] == visible[0][3]>>4&3]
            if not match:
                continue
            p = poses[match[0]]
            x,y = sx+p['origin'][0], sy+p['origin'][1]
            if not (100 <= x <= 215 and 20 <= y <= 175):
                continue
            mrows = S.mario_rows(ram, recorded[f], gfx)
            if any(mrows[yy] for yy in range(y, y+p['height'])):
                continue
            yield dict(frame=f, replay=f-5145, slot=slot, pose=match[0], x=x, y=y,
                       camera=ram[0x1a] | ram[0x1b]<<8, tiles=tiles,
                       oam=[list(e) for e in visible], width=p['width'], height=p['height'])


if __name__ == '__main__':
    for i,c in enumerate(cases()):
        print(json.dumps(c))
        if i >= 15:
            break
