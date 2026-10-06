#!/usr/bin/env python3
"""E11a: recuento exacto PF2 y cota offline de cargas PF1.

Modelo EDF del plan actual (mkscroll.plan), con WAIT de dos ranuras P39
como scrollsim.run_list y codo P51 desde 239. El paso de 12 px viene de
copsim/E11; fase WAIT de cinco planos SIN calibrar. No predice CPU, ni
reescrituras incrementales de build_mid/bm_left, ni fotos omitidas.
"""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from experimental_planes import LevelPlanes, Camera, read_cameras, pf2_window, selftest, ROOT


def line_loads(level, y, x, width):
    row = level.pf1[y]
    byreg = {}
    for ev in level.events[y]:
        byreg.setdefault(ev[2], []).append(ev)
    loads = []
    for reg, evs in byreg.items():
        evs.sort()
        for prev, cur in zip(evs, evs[1:]):
            if prev[3] == cur[3]:
                continue
            # P44: pixeles derramados pueden prolongar el color anterior.
            fin = prev[1]
            last = row.rfind(bytes([reg]), prev[1] + 1, cur[0])
            if last >= 0:
                fin = last
            if cur[0] < x or cur[0] >= x + width or fin >= x + width:
                continue
            if fin < x:
                continue  # color inicial puede cargarse en el borrado
            loads.append((fin + 1 - x, cur[0] - x, reg, cur[3]))
    return loads


def schedule(loads, step):
    # Modelo de recuento, no lista emitida. Conserva EDF y WAIT/fillers.
    pending = sorted(loads)
    ready = []
    t = -120
    late = wait = fill = 0
    locations = []
    def advance(pos, count=1):
        for _ in range(count):
            pos += 8 if pos >= 239 else step
        return pos
    while pending or ready:
        if not ready and pending[0][0] > t:
            release = pending[0][0]
            while pending and pending[0][0] <= release:
                ready.append(pending.pop(0))
        while pending and pending[0][0] <= t:
            ready.append(pending.pop(0))
        ready.sort(key=lambda e: e[1])
        ev = ready.pop(0)
        release, deadline = ev[:2]
        gap = release - t
        if gap <= 0:
            land = t
        elif gap <= 2 * step:
            land = t
            while land < release:
                land = advance(land)
                fill += 1
        else:
            # Fase WAIT 6 planos P46: rejilla de 8 px. Se conserva esta
            # fase en 5 planos como hipotesis explicita, aun no calibrada.
            target = ((release + 8) // 8) * 8 - 1
            land = max(advance(t, 2), target)
            wait += 1
        if land > deadline:
            late += 1
        locations.append((land, deadline))
        t = advance(land)
    return {'loads': len(loads), 'late': late, 'wait': wait, 'fill': fill,
            'delay_px': sum(max(0, land - dl) for land, dl in locations)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--level', default=str(ROOT / 'levels/yi1.json'))
    ap.add_argument('--oracle', action='append')
    ap.add_argument('--translevel', type=lambda v: int(v, 16), default=0x29)
    ap.add_argument('--rest-l2y', type=int, default=192,
                    help='Bg2VOfs que corresponde a camera.y0 en el SMWD')
    ap.add_argument('--mode', choices=('oracle', 'current'), default='oracle')
    ap.add_argument('--width', type=int, default=256)
    ap.add_argument('--out', default='work/e11a')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        selftest()
        assert schedule([(7, 7, 1, 1)], 16)['late'] == 0
        assert schedule([(7, 7, 1, 1), (8, 20, 2, 2)], 16)['late'] == 1
        assert schedule([(7, 7, 1, 1), (8, 20, 2, 2)], 12)['late'] == 0
        assert schedule([(239, 239, 1, 1), (240, 247, 2, 2)], 16)['late'] == 0
        print('Autoprueba EDF: beneficio 12 px y codo P51 OK')
    level = LevelPlanes.load(a.level)
    paths = a.oracle or [str(ROOT / 'work' / f'oracle_{name}.txt')
                        for name in ('yi1', 'stress_back', 'stress_vert', 'chuck')]
    traces = read_cameras(paths, a.translevel)
    cache = {}
    output = []
    totals = Counter()
    for trace, cams in traces.items():
        used = Counter((c.x, c.y, c.l2x, c.l2y) for c in cams)
        for coords, frames in sorted(used.items()):
            camera = Camera(0, *coords)
            key = coords
            if key not in cache:
                maxima = []
                scores = Counter()
                for sy in range(level.camera['lines']):
                    row = pf2_window(level, camera, sy, a.mode, a.rest_l2y, a.width)
                    maximum = max(row)
                    maxima.append(maximum)
                    if maximum <= 3:
                        assert row == bytearray(v & 3 for v in row)
                    y = level.camera['y0'] + sy if a.mode == 'current' else camera.y + sy
                    if not 0 <= y < level.height or not 0 <= camera.x <= level.width - a.width:
                        raise ValueError('camara PF1 fuera de datos SMWD')
                    loads = line_loads(level, y, camera.x, a.width)
                    base = schedule(loads, 16)
                    candidate = schedule(loads, 12 if maximum <= 3 else 16)
                    scores['loads'] += base['loads']
                    scores['eligible_loads'] += base['loads'] if maximum <= 3 else 0
                    scores['late6'] += base['late']
                    scores['late_mix'] += candidate['late']
                    scores['saved_late'] += base['late'] - candidate['late']
                    scores['delay6_px'] += base['delay_px']
                    scores['delay_mix_px'] += candidate['delay_px']
                    scores['wait6'] += base['wait']
                    scores['wait_mix'] += candidate['wait']
                    scores['fill6'] += base['fill']
                    scores['fill_mix'] += candidate['fill']
                cache[key] = dict(scores, pf2_max=maxima,
                                  eligible=sum(v <= 3 for v in maxima),
                                  empty=maxima.count(0))
            result = dict(trace=Path(trace).stem, x=coords[0], y=coords[1],
                          l2x=coords[2], l2y=coords[3], frames=frames, **cache[key])
            output.append(result)
            for k, v in cache[key].items():
                if isinstance(v, int):
                    totals[k] += v * frames
            totals['frames'] += frames
            totals['lines'] += frames * level.camera['lines']
    peaks = {}
    for trace in sorted({r['trace'] for r in output}):
        rows = [r for r in output if r['trace'] == trace]
        peak = max(rows, key=lambda r: r['late6'])
        peaks[trace] = {'max_late6': max(r['late6'] for r in rows),
                         'max_late_mix': max(r['late_mix'] for r in rows),
                         'baseline_peak_camera': {k: peak[k] for k in
                             ('x', 'y', 'l2x', 'l2y', 'late6', 'late_mix', 'eligible_loads')}}
    report = dict(level=level.name, sha256=level.sha256, mode=a.mode,
                  rest_l2y=a.rest_l2y, width=a.width, totals=dict(totals), peaks=peaks,
                  limitations=['EDF plan aproximado, no build_mid/bm_left incremental',
                               'Fase WAIT cinco planos no calibrada; hipotesis fase P46',
                               'No incluye BPLCON0/BPL6PT, sprites ni costes CPU',
                               'No prueba pico CPU ni fotos omitidas; exige E11b integrado'],
                  cameras=output)
    prefix = Path(a.out)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    prefix.with_suffix('.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    with prefix.with_suffix('.csv').open('w', newline='', encoding='utf-8') as f:
        keys = [k for k in output[0] if k != 'pf2_max']
        writer = csv.DictWriter(f, keys)
        writer.writeheader()
        writer.writerows({k: r[k] for k in keys} for r in output)
    print(json.dumps({'totals': dict(totals), 'peaks': peaks}, indent=2))
    print(f'{len(output)} camaras, {totals["frames"]} frames; -> {prefix}.json/.csv')


if __name__ == '__main__':
    main()
