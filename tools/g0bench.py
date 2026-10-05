#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G0: genera un banco sintetico y comprueba sus pixels en WinUAE exacto.

python tools/g0bench.py build --out work/bench_g0_data.i
python tools/g0bench.py read --shot work/bench_g0.png --meta work/bench_g0.json
No lee ROM ni assets: cada objeto tiene cuatro filas identificables.
El lector distingue patrones/punteros, posiciones y el primer pixel de cada
fila; los casos tardios son controles negativos, nunca se convierten en OK.
"""
import argparse
import json
import struct
from pathlib import Path

from PIL import Image, ImageDraw

V0 = 0x2C
SPR_COLORS = [0xF00 | ((k & 3) * 4 << 4) | ((k >> 2) * 4) for k in range(1, 16)]


def rgb(word):
    return tuple(((word >> s) & 15) * 17 for s in (8, 4, 0))


def pose(which, row):
    # Los bordes y cada fila llevan firmas diferentes (no un rectangulo liso).
    return [1 + ((x + row * 3) % 7) if which == 0 else 8 + ((x * 3 + row) % 8)
            for x in range(16)]


def control(x, start, stop, channel):
    hp = 0xA0 + x  # hx0 de mspr68k.s a 256 px; DIW empieza en $A1.
    return [(start & 255) << 8 | (hp >> 1),
            (stop & 255) << 8 | (0x80 if channel & 1 else 0) |
            ((start >> 8) << 2) | ((stop >> 8) << 1) | (hp & 1)]


class Blob:
    def __init__(self):
        self.data = bytearray()
        self.reloc = []
        self.labels = {}
        self.wrapped = False

    def words(self, *words):
        self.data.extend(struct.pack('>' + 'H' * len(words), *words))

    def move(self, reg, val):
        self.words(reg, val)
        return len(self.data) - 2

    def wait(self, v, h):
        assert v < 312 and h < 0xE2
        if v >= 256 and not self.wrapped:
            self.words(0xFFDF, 0xFFFE)  # P59: h=$DE todavia alcanza.
            self.wrapped = True
        self.words((v & 255) << 8 | h | 1, 0xFFFE)

    def ptr(self, reg, label, offset=0):
        pos = self.move(reg, 0)
        self.move(reg + 2, 0)
        self.reloc.append((pos, label, offset))

    def label(self, name):
        while len(self.data) & 3:
            self.words(0)
        self.labels[name] = len(self.data)

    def sprite(self, name, x, start, stop, channel, which, terminate=True):
        self.label(name)
        self.words(*control(x, start, stop, channel))
        for row in range(stop - start):
            pixels = pose(which, row)
            shift = 2 if channel & 1 else 0
            self.words(*(sum(((p >> (bit + shift)) & 1) << (15 - x)
                             for x, p in enumerate(pixels)) for bit in (0, 1)))
        if terminate:
            self.words(0, 0)


def suite(name):
    if name == 'chain':
        return [dict(name='DMA gap%d' % g, method='chain', gap=g, load=8)
                for g in (0, 1, 2, 4, 8, 17)]
    if name == 'shared':
        return [dict(name='shared PT prev $%02X POS %s $%02X load%d' %
                          (h, 'prev' if pl == -1 else 'stop', ph, load),
                     method='shared', gap=1, pt_line=-1, pt_h=h,
                     pos_line=pl, pos_h=ph, load=load)
                for load in (0, 8) for h, pl, ph in
                ((0x80, 0, 0x38), (0xC0, 0, 0x38), (0xD8, 0, 0x38),
                 (0x80, 0, 0x80), (0xC0, 0, 0xC0), (0x80, 0, 0x38))]
    return [dict(name='DMA gap1', method='chain', gap=1, load=8)] + [
        dict(name='PT %s $%02X load%d' % ('prev' if line == -1 else 'stop', h, load),
             method='pt', gap=1, pt_line=line, pt_h=h, load=load)
        for load in (0, 8) for line, h in
        ((-1, 0x80), (-1, 0xC0), (-1, 0xD8), (0, 0), (0, 0x10), (0, 0x20))]


def build(args):
    cases = suite(args.suite)
    b = Blob()
    b.move(0x08E, 0x2CA1)
    b.move(0x090, 0x0CA1)
    b.move(0x092, 0x0040)
    b.move(0x094, 0x00C0)
    b.move(0x100, 0x6600)
    b.move(0x102, 0)
    b.move(0x104, 0x0024)
    b.move(0x108, (-34) & 65535)
    b.move(0x10A, (-34) & 65535)
    for n in range(6):
        b.ptr(0x0E0 + 4 * n, 'ones' if n == 0 else 'zero')
    for n in range(8):
        b.ptr(0x120 + 4 * n, 'zero')
    b.move(0x180, 0)
    b.move(0x182, 0x111)
    for k, color in enumerate(SPR_COLORS, 17):
        b.move(0x180 + k * 2, color)
    events = []
    stride = 30 if args.suite == 'chain' else 14
    for i, c in enumerate(cases):
        c['required'] = (c['method'] == 'chain' and c['gap'] >= 1 or
                         c['method'] == 'pt' and c['pt_line'] == -1 and c['pt_h'] <= 0xC0 or
                         c['method'] == 'shared' and c['pt_h'] <= 0xC0 and
                         c['pos_line'] == 0)
        # Controles negativos medidos: el reuso tarde debe perder pixels.
        c['negative'] = (c['method'] == 'pt' and not c['required'] or
                         c['method'] == 'shared' and c['pt_h'] == 0xD8)
        base = 50 + i * stride
        c.update(base=base, start=base + 2, stop=base + 6,
                 second_start=base + 6 + c['gap'])
        if c['second_start'] + 4 > V0 + 200:
            raise ValueError('La suite no cabe antes de las barras de resultados')
        events.append((base - 2, 0x40, 'init', i))
        if c['method'] != 'chain':
            events.append((c['stop'] + c['pt_line'], c['pt_h'], 'pt', i))
        if c['method'] == 'shared':
            events.append((c['stop'] + c['pos_line'], c['pos_h'], 'pos', i))
        for line in range(base - 1, base + stride - 1):
            if c['load']:
                events.append((line - 1, 0xD8, 'hload', i))
                events.append((line, 0x80, 'midload', i))
    for v, h, event, i in sorted(events, key=lambda e: (e[0], e[1], e[2])):
        c = cases[i]
        b.wait(v, h)
        if event == 'init':
            b.move(0x182, 0x111)
            for ch in range(8):
                # El canal detenido se arma escribiendo POS/CTL; el puntero
                # ya va al DATA. No suponer que PT fuerza leer el encabezado.
                b.ptr(0x120 + ch * 4, 'first%d_%d' % (i, ch), 4)
                pos, ctl = control(8 + ch // 2 * 56, c['start'], c['stop'], ch)
                b.move(0x140 + ch * 8, pos)
                b.move(0x142 + ch * 8, ctl)
        elif event == 'pt':
            for ch in range(8):
                label = ('shared%d' % (ch & 1) if c['method'] == 'shared'
                         else 'second%d_%d' % (i, ch))
                b.ptr(0x120 + ch * 4, label)
            b.move(0x182, 0x00F)  # fin de las 16 MOVE de punteros (azul)
        elif event == 'pos':
            for ch in range(8):
                pair = ch // 2
                pos, ctl = control(24 + pair * 56, c['second_start'],
                                   c['second_start'] + 4, ch)
                b.move(0x140 + ch * 8, pos)
                b.move(0x142 + ch * 8, ctl)
            b.move(0x182, 0x0F0)  # fin de POS/CTL (verde)
        else:
            for k in range(c['load'] if event == 'hload' else 6):
                b.move(0x184 if event == 'hload' else 0x186, k)
    bits = []
    # Seis filas: sincronismo, ticks/frame, empty/copy activo, empty/copy vblank.
    # Cada MOVE seguida ocupa 16 px con seis planos (P39/P46).
    for row in range(6):
        for line in range(V0 + 202 + row * 3, V0 + 204 + row * 3):
            b.wait(line, 0x48)
            for bit in range(16):
                bits.append(b.move(0x182, 0x0FF))
            b.wait(line, 0xD0)
            b.move(0x182, 0x111)
    b.words(0xFFFF, 0xFFFE)
    b.label('ones')
    b.words(*([0xFFFF] * 32))
    b.label('zero')
    b.words(*([0] * 32))
    for i, c in enumerate(cases):
        for ch in range(8):
            x = 8 + ch // 2 * 56
            b.sprite('first%d_%d' % (i, ch), x, c['start'], c['stop'], ch, 0,
                     terminate=c['method'] != 'chain')
            if c['method'] == 'chain':
                # No se alinea entre objetos: el control sigue al ultimo DATA.
                pos, ctl = control(x + 16, c['second_start'], c['second_start'] + 4, ch)
                b.words(pos, ctl)
                for r in range(4):
                    pixels = pose(1, r)
                    shift = 2 if ch & 1 else 0
                    b.words(*(sum(((p >> (bit + shift)) & 1) << (15 - xx)
                                 for xx, p in enumerate(pixels)) for bit in (0, 1)))
                b.words(0, 0)
            elif c['method'] == 'pt':
                b.sprite('second%d_%d' % (i, ch), x + 16, c['second_start'],
                         c['second_start'] + 4, ch, 1)
    for ch in (0, 1):
        b.sprite('shared%d' % ch, 0, 250, 254, ch, 1)
    b.label('end')
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ['; Generado por tools/g0bench.py; datos sinteticos, sin ROM.',
             'G0_NRELOC equ %d' % len(b.reloc), 'g0_reloc:']
    lines += ['        dc.l %d,%d' % (pos, b.labels[name] + offset)
              for pos, name, offset in b.reloc]
    lines += ['g0_bits:']
    # Cada fila se escribe en dos lineas de pantalla, para evitar el entrelazado.
    for row in range(6):
        lines += ['        dc.l ' + ','.join(str(x) for x in bits[row * 32:row * 32 + 16])]
    # Publicar tambien la segunda linea mediante alias de offsets (en asm).
    lines += ['g0_bits_second:']
    for row in range(6):
        lines += ['        dc.l ' + ','.join(str(x) for x in bits[row * 32 + 16:row * 32 + 32])]
    lines += ['        cnop 0,4', 'g0_blob:']
    words = struct.unpack('>' + 'H' * (len(b.data) // 2), b.data)
    for p in range(0, len(words), 12):
        lines += ['        dc.w ' + ','.join('$%04x' % w for w in words[p:p + 12])]
    lines += ['g0_blob_end:']
    out.write_text('\n'.join(lines) + '\n', encoding='ascii')
    meta = dict(suite=args.suite, blob_bytes=len(b.data), relocations=len(b.reloc),
                cases=cases, colors=SPR_COLORS, samples=32, copied_bytes=1408,
                capture=dict(x=131, y=70, scale=2))
    out.with_suffix('.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print('%s: %d B chip, %d casos, %d relocaciones' % (out, len(b.data), len(cases), len(b.reloc)))


def read(args):
    meta = json.loads(Path(args.meta).read_text(encoding='utf-8'))
    image = Image.open(args.shot).convert('RGB')
    # P57: centro del pixel, nunca el borde de una captura x2.
    cap = meta['capture']
    x0, y0, s = args.x if args.x is not None else cap['x'], cap['y'], cap['scale']
    px = image.load()
    palette = [rgb(c) for c in meta['colors']]
    def sample(x, v):
        return px[x0 + s * x + s // 2, y0 + s * (v - V0) + s // 2]
    results = []
    reference = Image.new('RGB', (256, 224), rgb(0x111))
    actual = Image.new('RGB', (256, 224))
    for yy in range(224):
        for xx in range(256):
            actual.putpixel((xx, yy), sample(xx, V0 + yy))
    for c in meta['cases']:
        expected = {}
        checks = []
        for which, start, dx in ((0, c['start'], 0), (1, c['second_start'], 16)):
            errors = 0
            for pair in range(4):
                for row in range(4):
                    for x, val in enumerate(pose(which, row)):
                        xx, v = 8 + pair * 56 + dx + x, start + row
                        want = palette[val - 1]
                        expected[xx, v] = want
                        reference.putpixel((xx, v - V0), want)
                        if sample(xx, v) != want:
                            errors += 1
            checks.append(errors)
        # Detecta sprites fuera de posicion y filas extra, ademas del patron.
        extra = []
        for v in range(c['base'], c['base'] + (30 if meta['suite'] == 'chain' else 14)):
            for x in range(256):
                got = sample(x, v)
                if got in palette and (x, v) not in expected:
                    extra.append([x, v])
        markers = {}
        for name, color in (('pt_done', (0, 0, 255)), ('pos_done', (0, 255, 0))):
            for v in range(c['base'], c['base'] + 14):
                positions = [x for x in range(256) if sample(x, v) == color]
                if positions:
                    markers[name] = dict(line=v, x=positions[0])
                    break
        result = dict(name=c['name'], required=c['required'],
                      negative=c.get('negative', False),
                      first_errors=checks[0], second_errors=checks[1],
                      extra_pixels=len(extra), extra_first=extra[:8], markers=markers,
                      ok=not (sum(checks) or extra))
        results.append(result)
        state = ('OK' if result['ok'] else
                 'FALLO esperado' if result['negative'] else 'FALLO')
        print('%-53s %s first=%d second=%d extra=%d %s' %
              (c['name'], state, *checks, len(extra), markers))
    values = []
    for row in range(6):
        value = 0
        for bit in range(16):
            got = sample(7 + bit * 16, V0 + 202 + row * 3)
            if got not in ((0, 0, 0), (255, 255, 255)):
                raise SystemExit('Barras no publicadas/alineadas: fila %d bit %d RGB %s' % (row, bit, got))
            value = value << 1 | (got == (255, 255, 255))
        values.append(value)
    if values[0] != 0xA55A or not 14000 <= values[1] <= 14500:
        raise SystemExit('Sincronia/timing PAL invalidos: %s' % values)
    timings = dict(zip(('sync', 'frame', 'empty_active', 'copy_active', 'empty_blank', 'copy_blank'), values))
    timings.update(active_net=values[3] - values[2], blank_net=values[5] - values[4])
    print('CIA-B ticks:', timings)
    print('Copia 1408 B: %.3f ms / %.2f%% frame activa; %.3f ms / %.2f%% blank' %
          (timings['active_net'] / values[1] * 20, timings['active_net'] / values[1] * 100,
           timings['blank_net'] / values[1] * 20, timings['blank_net'] / values[1] * 100))
    report = dict(shot=str(args.shot), meta=str(args.meta), cases=results, timings=timings)
    Path(args.shot).with_suffix('.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    comparison = Image.new('RGB', (512, 2 * (448 + 18)), (32, 32, 32))
    comparison.paste(reference.resize((512, 448), Image.Resampling.NEAREST), (0, 18))
    comparison.paste(actual.resize((512, 448), Image.Resampling.NEAREST), (0, 484))
    draw = ImageDraw.Draw(comparison)
    draw.text((4, 3), 'Referencia sintetica: patrones y posiciones', fill='white')
    draw.text((4, 469), 'WinUAE exacto: azul=fin PT, verde=fin POS/CTL', fill='white')
    comparison.save(Path(args.shot).with_name(Path(args.shot).stem + '_compare.png'))
    required = [c for c in results if c['required']]
    if not required or any(not c['ok'] for c in required):
        print('PUERTA: FALLA (control positivo o ventana temprana)')
        raise SystemExit(1)
    negatives = [c for c in results if c['negative']]
    if any(c['ok'] or c['first_errors'] for c in negatives):
        print('PUERTA: FALLA (control negativo no aisla el reuso tardio)')
        raise SystemExit(1)
    print('PUERTA: OK (%d positivos, %d negativos con primer objeto intacto)' %
          (len(required), len(negatives)))
    if args.expect_all and any(not c['ok'] for c in results):
        raise SystemExit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='cmd', required=True)
    bp = sub.add_parser('build')
    bp.add_argument('--suite', choices=('pt', 'shared', 'chain'), default='pt')
    bp.add_argument('--out', default='work/bench_g0_data.i')
    bp.set_defaults(func=build)
    rp = sub.add_parser('read')
    rp.add_argument('--shot', required=True)
    rp.add_argument('--meta', default='work/bench_g0_data.json')
    rp.add_argument('--x', type=int)
    rp.add_argument('--expect-all', action='store_true')
    rp.set_defaults(func=read)
    args = ap.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
