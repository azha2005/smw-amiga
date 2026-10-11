"""G7-C: apoyo DMA acotado para sondas, sobre la foto y el copper reales.

No es un asignador general ni autoriza omitir fichas. Acepta SPR2/3 o
SPR6/7 detenidos, con colores existentes exactos o indices libres.
"""
import struct

import numpy as np
import g5l as L
import g7_color_plan as P


def control(pos, ctl):
    return (((pos >> 8) | ((ctl & 4) << 6)) - L.V0,
            ((ctl >> 8) | ((ctl & 2) << 7)) - L.V0,
            (pos & 255) * 2 + (ctl & 1) - 0xA0)


def dma_image(g, rec, back):
    """Decodifica DATA y controles de los flujos chip efectivos, incluidas cadenas."""
    s, mem = g.s, g.mem
    spr = mem.r32(g.addr('g_sbuf') + 4 * mem.r16(g.dc + s['DC_REND']))
    image = np.zeros((224, 256), dtype=np.uint16)
    audit = []
    for pair in (0, 2, 4, 6):
        flows = []
        for ch in (pair, pair + 1):
            if ch < 4:
                pt = spr + ch * s['MSPR_WORDS'] * 2
                pos, ctl = mem.r16(pt), mem.r16(pt + 2)
                pt += 4
                # G7 puede armar una pareja Mario detenida desde los
                # ocho NOP del VBL: PT a DATA y POS/CTL explicitos.
                regs={g.mem.r16(back+s['CL_VBL']+off):g.mem.r16(back+s['CL_VBL']+off+2)
                      for off in range(4,s['CL_VBLSZ'],4)}
                if 0x140+8*ch in regs:
                    pt=regs[0x120+4*ch]<<16|regs[0x122+4*ch]
                    pos,ctl=regs[0x140+8*ch],regs[0x142+8*ch]
            else:
                at = back + s['CL_VBL'] + 4 + 16 * (ch - 4)
                pt = mem.r16(at + 2) << 16 | mem.r16(at + 6)
                pos, ctl = mem.r16(at + 10), mem.r16(at + 14)
            rows = {}
            spans = []
            for _ in range(32):
                start, stop, x = control(pos, ctl)
                if stop <= start:
                    break
                assert -L.V0 <= start < stop <= 312 - L.V0
                assert bool(ctl & 0x80) == bool(ch & 1), 'flujo no adosado'
                spans.append(dict(start=start, stop=stop, x=x, data=pt))
                for y in range(start, stop):
                    assert y not in rows, 'cadena DMA solapada'
                    rows[y] = (x, mem.r16(pt), mem.r16(pt + 2))
                    pt += 4
                pos, ctl = mem.r16(pt), mem.r16(pt + 2)
                pt += 4
            else:
                raise AssertionError('cadena sin terminador')
            audit.append(dict(channel=ch, spans=spans))
            flows.append(rows)
        for y in set(flows[0]) | set(flows[1]):
            assert y in flows[0] and y in flows[1], 'pareja con filas distintas'
            x, a, b = flows[0][y]
            xx, c, d = flows[1][y]
            assert x == xx
            if not 0 <= y < 224:
                continue
            for dx in range(16):
                value = sum(((bits >> (15 - dx)) & 1) << p
                            for p, bits in enumerate((a, b, c, d)))
                if value and 0 <= x + dx < 256:
                    image[y, x + dx] |= 1 << value
    return image, audit


def sprite_palette(g, back, overrides=None):
    """COLOR17-31 y prioridad desde la cabecera y todos los eventos reales."""
    current = np.zeros(16, dtype=np.int32)
    priority = 4
    for off in range(0,g.s['CL_LINES'],4):
        reg=g.mem.r16(back+off); value=g.mem.r16(back+off+2)
        if 0x1A2 <= reg <= 0x1BE:
            current[(reg-0x1A0)//2]=value&0xFFF
        elif reg==0x104:
            priority=value&7
    colors=np.zeros((224,16,256),dtype=np.int32)
    front=np.zeros((224,256),dtype=np.int8)
    for row in range(224):
        colors[row]=current[:,None]
        front[row]=priority
        words,_=P.T.segment_words(g.mem,back,g.s['CL_LINES'],g.s['SEG'],row)
        if overrides and row in overrides:words=overrides[row]
        for x,reg,value in P.T.timeline(words,row):
            if 0x1A2 <= reg <= 0x1BE:
                index=(reg-0x1A0)//2
                current[index]=value&0xFFF
                if x<256:colors[row,index,max(0,x):]=current[index]
            elif reg==0x104:
                priority=value&7
                if x<256:front[row,max(0,x):]=priority
    return colors,front


def visibility(g,rec,back):
    """Mascara efectiva delante de PF1, tambien en el camino de un objeto.

    GV_NPL/GV_RX solo describen el camino multiple; pueden conservar
    registros viejos cuando se emite un solo objeto. Leer los flujos y
    BPLCON2 que consumira el chipset evita depender de ese scratch.
    """
    _,audit=dma_image(g,rec,back)
    priority=4
    for off in range(0,g.s['CL_LINES'],4):
        if g.mem.r16(back+off)==0x104:priority=g.mem.r16(back+off+2)&7
    front=np.empty((224,256),dtype=np.uint8)
    for row in range(224):
        front[row]=priority
        words,_=P.T.segment_words(g.mem,back,g.s['CL_LINES'],g.s['SEG'],row)
        for x,r,v in P.T.timeline(words,row):
            if r==0x104:
                priority=v&7
                if x<256:front[row,max(0,x):]=priority
    hidden=np.zeros((224,256),dtype=bool)
    shifts=np.arange(15,-1,-1)
    for ch,flow in enumerate(audit):
        for span in flow['spans']:
            y0,y1,x=span['start'],span['stop'],span['x']
            raw=g.cpu.read(span['data'],4*(y1-y0))
            words=np.frombuffer(raw,dtype='>u2').reshape((-1,2))
            bits=(words[:,0]|words[:,1])[:,None]>>shifts[None,:]&1
            a,b=max(0,y0),min(224,y1);l,r=max(0,x),min(256,x+16)
            if a<b and l<r:
                hidden[a:b,l:r]|=bits[a-y0:b-y0,l-x:r-x].astype(bool)&(front[a:b,l:r]>ch//2)
    return hidden


def visible_image(g,rec,back):
    """Color de la primera pareja opaca por pixel, con BPLCON2 efectivo."""
    _,audit=dma_image(g,rec,back)
    palette,front=sprite_palette(g,back)
    image=np.zeros((224,256),dtype=np.uint16)
    occupied=np.zeros((224,256),dtype=bool)
    shifts=np.arange(15,-1,-1)
    for pair in (0,2,4,6):
        values=np.zeros((224,256),dtype=np.uint8)
        for upper in (0,1):
            for span in audit[pair+upper]['spans']:
                a,b,x=span['start'],span['stop'],span['x']
                words=np.frombuffer(g.cpu.read(span['data'],4*(b-a)),dtype='>u2').reshape((-1,2))
                bits=sum(((words[:,p,None]>>shifts[None,:])&1)<<(2*upper+p) for p in (0,1))
                y0,y1=max(0,a),min(224,b);l,r=max(0,x),min(256,x+16)
                if y0<y1 and l<r:values[y0:y1,l:r]|=bits[y0-a:y1-a,l-x:r-x].astype(np.uint8)
        mask=(values!=0)&(front>pair//2)&~occupied
        yy,xx=np.where(mask)
        image[yy,xx]=palette[yy,values[yy,xx],xx];occupied|=mask
    return image,occupied


def validate_plans(g, rec, back, primes, assigned, expected):
    """Comprueba juntas las recargas y todos los propietarios de COLOR17-31."""
    overrides = {}
    for row, plan in primes:
        words = plan['words']
        assert row not in overrides or overrides[row] == words, 'dos cargas en la misma fila requieren plan conjunto'
        overrides[row] = words
    old_pal, _ = sprite_palette(g, back)
    new_pal, front = sprite_palette(g, back, overrides)
    image, _ = dma_image(g, rec, back)
    for i in range(1, 16):
        live = (image & (1 << i)) != 0
        assert np.array_equal(new_pal[:, i, :][live], old_pal[:, i, :][live]), 'color de otro sprite alterado'
    covered = np.zeros(expected.shape, dtype=bool)
    for info, mask in assigned:
        assert not np.any(covered & mask), 'destinos hardware solapados'
        assert set(map(int, expected[mask])) <= set(map(int, info['mapping'])), 'color hardware sin indice'
        covered |= mask
        assert np.all(front[mask] > info['pair'][0] // 2), 'PF1 tapa el apoyo emitido'
        for col, i in info['mapping'].items():
            wanted = mask & (expected == int(col))
            assert np.all(new_pal[:, i, :][wanted] == int(col)), 'planes hardware con colores incompatibles'
    return overrides


def prepare(g, rec, back, oam, bank, overlay, entry, pair=2):
    assert 0 <= entry < 64
    single = bytearray(320)
    for e in range(64):
        single[4 * e + 1] = 0xF0
    single[4 * entry:4 * entry + 4] = oam[4 * entry:4 * entry + 4]
    single[256 + entry] = oam[256 + entry]
    hw = P.overlays(single, bank)
    mask = (hw >= 0) & (overlay == hw)
    assert mask.any(), 'ficha sin pixeles visibles'
    hw[~mask] = -1
    ys, xs = np.where(mask)
    start, stop, x0 = int(ys.min()), int(ys.max()) + 1, int(xs.min())
    assert int(xs.max()) - x0 < 16 and start > 0
    image, audit = dma_image(g, rec, back)
    assert pair in (2,6), 'sonda acotada a las parejas 2/3 y 6/7'
    assert not audit[pair]['spans'] and not audit[pair+1]['spans'], 'pareja con DMA activo'
    # No asumir canales libres por transparencia: sus controles tienen que
    # estar detenidos; tampoco admitir un emisor posterior que los rearme.
    for row in range(224):
        words, _ = P.T.segment_words(g.mem, back, g.s['CL_LINES'], g.s['SEG'], row)
        assert not any(0x120+4*pair <= r <= 0x126+4*pair or
                       0x140+8*pair <= r <= 0x14A+8*pair
                       for r, _ in words if not r & 1), 'pareja rearmada por copper'
    palette,front=sprite_palette(g,back)
    assert np.all(front[mask]>pair//2), 'PF1 tapa la pareja elegida'
    prime = start - 1
    # Incluir la fila de carga: una cadena puede escribir antes de x=255.
    used = int(np.bitwise_or.reduce(image[prime:].ravel(), initial=0))
    available = [i for i in range(1, 16) if not used & (1 << i)]
    colors = sorted(set(int(v) for v in hw[mask]))
    existing={col:next((i for i in range(1,16) if np.all(palette[ys[hw[mask]==col],i,xs[hw[mask]==col]]==col)),None)
              for col in colors}
    reuse=all(i is not None for i in existing.values())
    if reuse:
        mapping=existing
    else:
        assert len(colors) <= len(available), 'faltan indices compartidos libres'
        mapping = dict(zip(colors, available))
    # Si una recarga ajena pisa la paleta durante el efecto, rechazar el
    # candidato. El prototipo no desplaza eventos de G5L para hacer lugar.
    for row in (() if reuse else range(start, stop)):
        words, _ = P.T.segment_words(g.mem, back, g.s['CL_LINES'], g.s['SEG'], row)
        assert not any(r in {0x1A0 + 2 * i for i in mapping.values()}
                       for r, _ in words if not r & 1), 'recarga compartida durante efecto'
    words, _ = P.T.segment_words(g.mem, back, g.s['CL_LINES'], g.s['SEG'], prime)
    nxt, _ = P.T.segment_words(g.mem, back, g.s['CL_LINES'], g.s['SEG'], start)
    _, nb = P.prefix_of(nxt, start)
    timeline = P.T.timeline(words, prime)
    last = max((x for x, _, _ in timeline if x >= 0), default=L.T0)
    assert prime != L.WRAP_SEG, 'cruce PAL sin contrato de apoyo DMA'
    loads = [(0x1A0 + 2 * mapping[col], col) for col in colors]
    end = L.end_of(nb)
    assert end is not None
    if reuse:
        extra=[]; positions=[]; mode='paleta existente'
    elif L.X_D0 - last >= L.IDLE and L.X_D0 + 8 * (len(loads) - 1) <= end:
        extra = [(((prime + L.V0) & 255) << 8 | 0xD1, 0xFFFE)] + loads
        positions = [L.X_D0 + 8 * j for j in range(len(loads))]
        mode = 'WAIT D0'
    else:
        # Contrato G2T-A ya medido: encadenar desde una carga activa,
        # nunca desde el borrado. No desplazar eventos de las capas.
        assert last >= 0 and L.adv(last,len(loads)) <= end, 'sufijo retrasa fila siguiente'
        extra = loads
        positions = [L.adv(last,j+1) for j in range(len(loads))]
        mode = 'cadena'
    new = words + extra
    assert 4 * (len(new) + 3) <= g.s['SEG']
    assert P.T.timeline(new, prime)[:len(timeline)] == timeline
    residual = overlay.copy()
    residual[mask] = -1
    if not reuse:
        assert not np.any(residual[prime]>=0), 'fila de carga necesita plan PF1 conjunto'
    assert np.array_equal(np.where(mask, hw, residual), overlay), 'destinos incompletos'
    flows = []
    from g0bench import control as encode_control
    for upper in (0, 1):
        flow = bytearray(struct.pack('>HH', *encode_control(x0, start + L.V0, stop + L.V0, pair + upper)))
        for y in range(start, stop):
            values = [mapping[int(hw[y, x])] if 0 <= x < 256 and hw[y, x] >= 0 else 0
                      for x in range(x0, x0 + 16)]
            for bit in range(2):
                flow += struct.pack('>H', sum(((v >> (2 * upper + bit)) & 1) << (15 - dx)
                                             for dx, v in enumerate(values)))
        flow += bytes(4)
        flows.append(bytes(flow))
    # Ocho NOP consecutivos del bloque VBL: PT y POS/CTL de cada canal.
    vb = g.cpu.read(back + g.s['CL_VBL'], g.s['CL_VBLSZ'])
    needle = struct.pack('>HH', 0x1FE, 0) * 8
    offsets = [off for off in range(4, len(vb) - len(needle) + 1, 4)
               if vb[off:off + len(needle)] == needle]
    if pair==6:
        offsets=[4+16*(pair-4)] # campos VBL de esta pareja ya auditada nula
    assert offsets, 'VBL sin ocho MOVE disponibles'
    info = dict(entry=entry, pair=[pair, pair+1], start=start, stop=stop, x=x0,
                mapping={str(k): v for k, v in mapping.items()}, prime=prime,
                loads_x=positions, prime_mode=mode,
                next_nb=nb, last_before=last, vbl_offset=offsets[0],
                dma=audit, pixels=int(mask.sum()), dma_bytes=sum(map(len, flows)),
                scope='pareja detenida, armado VBL; sin reuso durante display; paleta existente exacta o indices libres')
    return residual, None if reuse else (prime, dict(words=new)), flows, info
