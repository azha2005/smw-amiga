#!/usr/bin/env python3
"""Lee BENCH cycle-exact con control y compara los recortes de STOPF=1800."""
import json
from pathlib import Path
from PIL import Image, ImageChops
from game_read import autodetect, read_longs, NROWS_O5


def bench(name):
    shot = Path('work') / name / 'shot.png'
    f = read_longs(str(shot), *autodetect(str(shot)), NROWS_O5)
    if f[0] != 0xa55a5aa5 or f[18] != 0x5aa5a55a:
        raise ValueError('BENCH sin sincronia: ' + name)
    result = dict(logic=f[5]&65535, published=f[7]&65535,
                  lost=f[9]&65535, streak=f[11]&65535,
                  total_mean=f[3]>>16, total_max=f[16]>>16,
                  total_frame=5145+(f[16]&65535), over_pal=f[3]&65535)
    if not result['logic']:
        raise ValueError('BENCH sin frames')
    if name == 'b2b_env':
        result.update(copy_ticks=f[4]>>16, copy_frame=5145+(f[4]&65535),
                      render_ticks=f[6]>>16, render_frame=5145+(f[6]&65535))
    print('%s: %s' % (name, result))
    return result


def main():
    result = {name: bench(name) for name in ('b2b_control_bench', 'b2b_bench', 'b2b_env')}
    # P57: recorte PAL x2 del proyecto, se excluye el marco de Windows.
    box = (67, 70, 707, 582)
    control = Image.open('work/b2b_control_view/shot.png').convert('RGB').crop(box)
    actual = Image.open('work/b2b_view/shot.png').convert('RGB').crop(box)
    diff = ImageChops.difference(control, actual)
    count = sum(v != (0, 0, 0) for v in diff.getdata())
    result['view'] = dict(replay_frame=1800, oracle_frame=6945, pixels=640*512, diff=count)
    stacked = Image.new('RGB', (640, 1024))
    stacked.paste(control, (0, 0)); stacked.paste(actual, (0, 512))
    stacked.save('work/b2b/view_control_ab.png')
    Path('work/b2b/shot_summary.json').write_text(json.dumps(result, indent=2))
    if count:
        diff.save('work/b2b/view_diff.png')
        raise ValueError('vista B2bis distinta del control: %d pixeles' % count)
    print('B2bis visual: 0/%d pixeles distintos; control arriba, B2bis abajo' % (640*512))


if __name__ == '__main__':
    main()
