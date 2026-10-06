#!/usr/bin/env python3
"""E12: prueba offline exhaustiva de colores PF1 por Y, sin cambiar el juego.

El dominio conservador incluye cada camara X entera que cabe en el nivel,
cada Y entera que cabe en su altura y todas sus lineas. No depende del
recorrido de los oraculos. Los colores se reconstruyen desde el ultimo
evento iniciado, incluso donde un derrame utiliza el indice fuera de x_fin.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def reconstruct(row, events):
    """Color real por pixel; los extremos finales no borran el registro."""
    state = [None] * 8
    ordered = sorted(events, key=lambda e: e[0])
    out, ei = [], 0
    for x, reg in enumerate(row):
        while ei < len(ordered) and ordered[ei][0] <= x:
            _, _, r, col = ordered[ei]
            state[r] = col
            ei += 1
        color = state[reg] if reg else 0
        if color is None:
            raise ValueError('pixel sin carga inicial: x=%d indice=%d' % (x, reg))
        out.append(color)
    return out


def row_analysis(row, colors, screen):
    """Barrido exacto de todas las ventanas, O(ancho) y sin numpy."""
    whole = [set() for _ in range(8)]
    for reg, color in zip(row, colors):
        if reg:
            whole[reg].add(color)
    counts = [Counter() for _ in range(8)]
    witness = {}
    for x, (reg, color) in enumerate(zip(row, colors)):
        if reg:
            counts[reg][color] += 1
        if x >= screen:
            oldreg, oldcol = row[x-screen], colors[x-screen]
            if oldreg:
                counts[oldreg][oldcol] -= 1
                if not counts[oldreg][oldcol]:
                    del counts[oldreg][oldcol]
        if x >= screen-1:
            for r in range(1, 8):
                if len(counts[r]) > 1 and r not in witness:
                    witness[r] = {'camera_x': x-screen+1,
                                  'colors': sorted(counts[r])}
                    positions = {}
                    for px in range(x-screen+1, x+1):
                        if row[px] == r:
                            positions.setdefault(colors[px], px)
                    witness[r]['pixel_positions'] = positions
    return whole, witness


def selftest():
    # El color sigue vivo despues de x_fin: cubre el caso de derrames P45.
    row = bytearray([1, 1, 0, 1, 0, 1, 1])
    events = [(0, 1, 1, 0x123), (5, 6, 1, 0x456)]
    cols = reconstruct(row, events)
    assert cols == [0x123, 0x123, 0, 0x123, 0, 0x456, 0x456]
    whole, conflicts = row_analysis(row, cols, 3)
    assert whole[1] == {0x123, 0x456}
    assert conflicts[1]['camera_x'] == 3
    _, far = row_analysis(bytearray([1, 0, 0, 0, 1]),
                          [0x123, 0, 0, 0, 0x456], 3)
    assert not far  # Dos variantes globales que nunca coexisten.
    # Cruce independiente de cada ventana contra la optimizacion.
    for width in range(1, len(row)+1):
        _, actual = row_analysis(row, cols, width)
        expected = any(len({cols[x] for x in range(s, s+width)
                            if row[x] == 1}) > 1
                       for s in range(len(row)-width+1))
        assert (1 in actual) == expected
    try:
        reconstruct(bytearray([1]), [])
    except ValueError:
        pass
    else:
        raise AssertionError('se acepto un color sin inicializar')
    # Caso positivo real: PF1 cambia de color por Y, no por X; mueve la
    # carga al borrado y prueba pixeles no vacios, no solo identidad vacia.
    from types import SimpleNamespace
    fake = SimpleNamespace(width=4, height=2,
                           pf1=[bytearray([1, 1, 2, 2])]*2,
                           events=[[(0, 1, 1, 0x123), (2, 2, 2, 0x456),
                                    (3, 3, 2, 0x789)],
                                   [(0, 1, 1, 0xabc), (2, 3, 2, 0x456)]])
    proof = analyze(fake, screen=4, lines=2)
    assert 1 in proof['eligible_constant_per_y']
    assert 2 not in proof['eligible_constant_per_y']
    assert proof['pixel_proof']['eligible_pixels'] == 4


def analyze(level, screen=256, lines=224):
    if not 0 < screen <= level.width or not 0 < lines <= level.height:
        raise ValueError('pantalla fuera del nivel')
    strict, window = set(range(1, 8)), set(range(1, 8))
    witnesses, row_colors, decoded = {}, [], []
    event_mid, visible_mid = Counter(), Counter()
    used = set()
    reference_errors = 0
    sha = hashlib.sha256()
    for y, (row, events) in enumerate(zip(level.pf1, level.events)):
        colors = reconstruct(row, events)
        # Cruce independiente: raster por registro con tramos [evento,
        # siguiente evento), despues seleccion del indice de cada pixel.
        reference = [0]*level.width
        for r in range(1, 8):
            ev = sorted(e for e in events if e[2] == r)
            for ei, e in enumerate(ev):
                end = ev[ei+1][0] if ei+1 < len(ev) else level.width
                for px in range(e[0], end):
                    if row[px] == r:
                        reference[px] = e[3]
        reference_errors += sum(a != b for a, b in zip(colors, reference))
        used.update(row)
        decoded.append(colors)
        whole, conflicts = row_analysis(row, colors, screen)
        row_colors.append(whole)
        strict -= {r for r in range(1, 8) if len(whole[r]) > 1}
        window -= set(conflicts)
        for r, w in conflicts.items():
            witnesses.setdefault(r, dict(y=y, **w))
        state = {}
        for _, _, r, col in sorted(events):
            if r in state and state[r] != col:
                event_mid[r] += 1
            state[r] = col
        for r in range(1, 8):
            values = [c for rr, c in zip(row, colors) if rr == r]
            visible_mid[r] += sum(a != b for a, b in zip(values, values[1:]))
        sha.update(b''.join(c.to_bytes(2, 'big') for c in colors))
    strict &= used
    window &= used
    assert reference_errors == 0
    # Reconstruccion candidata: el indice elegible recibe su color por Y
    # antes de x=0. Otros indices conservan EXACTAMENTE el plan original.
    sha_candidate = hashlib.sha256()
    compared = eligible_pixels = mismatches = 0
    for y, (row, colors) in enumerate(zip(level.pf1, decoded)):
        fixed = {r: next(iter(row_colors[y][r])) for r in strict
                 if row_colors[y][r]}
        candidate = [fixed.get(r, c) for r, c in zip(row, colors)]
        eligible_pixels += sum(r in strict for r in row)
        mismatches += sum(a != b for a, b in zip(colors, candidate))
        compared += len(row)
        sha_candidate.update(b''.join(c.to_bytes(2, 'big') for c in candidate))
    assert mismatches == 0
    assert sha.digest() == sha_candidate.digest()
    nx, ny = level.width-screen+1, level.height-lines+1
    return {
        'domain': {'screen_width': screen, 'screen_lines': lines,
                   'camera_x': [0, nx-1], 'camera_y': [0, ny-1],
                   'camera_pairs': nx*ny, 'screen_row_windows': nx*ny*lines,
                   'distinct_level_row_windows_checked': nx*level.height,
                   'proof': 'todas las filas y todas las X; cada camara Y selecciona un subconjunto'},
        'eligible_constant_per_y': sorted(strict),
        'eligible_no_conflict_in_any_window': sorted(window),
        'conflict_witnesses': witnesses,
        'mid_color_changes_in_events_by_index': dict(event_mid),
        'visible_color_changes_by_index': dict(visible_mid),
        'eligible_mid_moves_to_blank': sum(event_mid[r] for r in strict),
        'eligible_visible_mid_changes': sum(visible_mid[r] for r in strict),
        'avoided_mid_instruction_words': 2*sum(event_mid[r] for r in strict),
        'maximum_avoided_delayed_loads': 0 if not strict else None,
        'initial_palette_rewrites_avoided': 0 if not strict else None,
        'pixel_proof': {'compared': compared, 'eligible_pixels': eligible_pixels,
                        'mismatches': mismatches, 'original_sha256': sha.hexdigest(),
                        'independent_reference_mismatches': reference_errors,
                        'candidate_sha256': sha_candidate.hexdigest()},
        'runtime_measured': False,
        'limit': 'sin reasignar indices/bitmap; no mide tiempo ni reescrituras de build_mid',
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--level', default='levels/yi1.json')
    ap.add_argument('--screen', type=int, default=256)
    ap.add_argument('--lines', type=int, default=224)
    ap.add_argument('--out', default='work/experimental_pf1.json')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--png', help='recorte original/candidato apilado (evidencia offline)')
    args = ap.parse_args()
    selftest()
    if args.selftest:
        print('E12 autoprueba: OK')
    from experimental_planes import LevelPlanes
    level = LevelPlanes.load(args.level)
    report = analyze(level, args.screen, args.lines)
    report['level_descriptor'] = args.level
    report['source_smwd_sha256'] = level.sha256
    if args.png:
        from PIL import Image
        # Primer conflicto: muestra por que no se puede suprimir su carga.
        witness = next(iter(report['conflict_witnesses'].values()),
                       {'camera_x': 0, 'y': 0})
        cx = witness['camera_x']
        cy = max(0, min(witness['y']-args.lines//2, level.height-args.lines))
        pixels = []
        for y in range(cy, cy+args.lines):
            row = level.pf1[y]
            colors = reconstruct(row, level.events[y])
            pixels.extend(colors[x] if row[x] else level.sky
                          for x in range(cx, cx+args.screen))
        image = Image.new('RGB', (args.screen, args.lines*2))
        rgb = [((c>>8 & 15)*17, (c>>4 & 15)*17, (c & 15)*17) for c in pixels]
        # Sin indices elegibles, el candidato conserva el plan original.
        if report['eligible_constant_per_y']:
            raise ValueError('el PNG de descarte exige cero indices elegibles')
        image.putdata(rgb+rgb)
        image.save(args.png)
        report['offline_png'] = {'path': args.png, 'camera': [cx, cy],
                                 'top': 'original', 'bottom': 'candidato sin cambios'}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('E12: indices por Y=%s; sin conflicto en ventana=%s; '
          'MOVE elegibles=%d; palabras evitadas=%d' %
          (report['eligible_constant_per_y'],
           report['eligible_no_conflict_in_any_window'],
           report['eligible_mid_moves_to_blank'],
           report['avoided_mid_instruction_words']))
    print('Dominio: %d camaras; %d ventanas de fila; '
          '%d pixeles, %d diferencias. Informe: %s' %
          (report['domain']['camera_pairs'],
           report['domain']['distinct_level_row_windows_checked'],
           report['pixel_proof']['compared'], report['pixel_proof']['mismatches'],
           args.out))


if __name__ == '__main__':
    main()
