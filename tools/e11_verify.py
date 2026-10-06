#!/usr/bin/env python3
"""Cruce independiente con render_d y evidencia visual original/reducido/diff."""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
import render_d
from experimental_planes import LevelPlanes, Camera, pf2_window


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--level', default='levels/yi1.json')
    ap.add_argument('--report', default='work/e11a_current.json')
    ap.add_argument('--out', default='work/e11a_validation.png')
    a = ap.parse_args()
    level = LevelPlanes.load(a.level)
    other = render_d.load(level.data_path)
    assert np.array_equal(np.array(level.pf1), render_d.l1_index(other))
    assert np.array_equal(np.array(level.pf2), other['l2idx'])
    assert np.array_equal(np.array(level.pf2pal), other['l2pal'])
    assert level.events == other['events']
    report = json.loads(Path(a.report).read_text())
    all_checked = 0
    for row in report['cameras']:
        camera = Camera(0, row['x'], row['y'], row['l2x'], row['l2y'])
        maxima = [max(pf2_window(level, camera, sy, report['mode'], report['rest_l2y'], report['width']))
                  for sy in range(level.camera['lines'])]
        assert maxima == row['pf2_max']
        all_checked += len(maxima)
    row = max(report['cameras'], key=lambda r: (r['eligible_loads'], r['loads']))
    camera = Camera(0, row['x'], row['y'], row['l2x'], row['l2y'])
    original = []
    reduced = []
    for sy in range(level.camera['lines']):
        idx = pf2_window(level, camera, sy, report['mode'], report['rest_l2y'], report['width'])
        iy = level.camera['y0'] + sy
        if report['mode'] == 'oracle':
            iy += camera.l2y - report['rest_l2y']
        pal = [level.sky, *level.pf2pal[iy]]
        original.append([pal[v] for v in idx])
        reduced.append([pal[v & 3 if max(idx) <= 3 else v] for v in idx])
    original, reduced = np.array(original), np.array(reduced)
    assert np.array_equal(original, reduced)
    rgb = render_d.rgb8(original)
    diff = np.zeros_like(rgb)
    diff[original != reduced] = (255, 0, 255)
    Image.fromarray(np.concatenate((rgb, render_d.rgb8(reduced), diff))).resize(
        (report['width'] * 2, level.camera['lines'] * 6), Image.Resampling.NEAREST).save(a.out)
    print(f'SMWD completo vs render_d: PF1/PF2/paleta/eventos OK; {all_checked} lineas chequeadas')
    print(f'Original/reducido: 0 px distintos; camara {camera}; PNG {a.out}')
    for target in (2832, 4580):
        back = [r for r in report['cameras'] if r['trace'] == 'oracle_stress_back']
        item = min(back, key=lambda r: abs(r['x'] - target))
        print('stress_back cercano', target, {k: item[k] for k in
              ('x', 'y', 'eligible', 'eligible_loads', 'late6', 'late_mix', 'loads')})


if __name__ == '__main__':
    main()
