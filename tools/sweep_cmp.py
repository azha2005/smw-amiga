#!/usr/bin/env python3
"""SW1: barrida de la imagen entera contra la SNES, una foto por segundo.

Las capturas anteriores comparaban zonas (sprites, capa 1) o una foto
suelta. Esta compara la pantalla completa en fotos repartidas por todo el
replay:

  1. capture: un build de replay con -DHOLDEVERY=n (game.s) se retiene
     cada n frames; este script lee `SW1HOLD!` de la memoria de WinUAE
     (cycle-exact, bajo el candado) y captura la ventana mientras la foto
     k esta quieta, comprobando antes y despues que sigue siendo k.
  2. snes: el frame del oraculo de cada k (frames_*.json de g5l.py game,
     campo f) y la pantalla de la SNES de ese frame con la PPU de
     snesrev (work/snesorc --shots).
  3. cmp: pixel a pixel a 12 bits (la conversion del port), con la
     alineacion vertical medida, la barra de estado aparte y las
     diferencias agrupadas en cajas; imagenes SNES | Amiga | diferencia.

  GDEFS="-DREPLAY -DHOLDEVERY=50" OUT=work/sw1/yi1 sh tools/bm_build.sh
  python tools/sweep_cmp.py capture --dir work/sw1/yi1
  python tools/sweep_cmp.py snes --dir work/sw1/yi1 --frames work/g9/frames_yi1.json \\
      --script tools/snesorc/boot_yi1.orc --replay work/oracle_yi1.txt --seg 2
  python tools/sweep_cmp.py cmp --dir work/sw1/yi1
  python tools/sweep_cmp.py --selftest
"""
import argparse
import json
import os
import struct
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

LOCK = ROOT.parent / 'winuae_lock.ps1'
ROM = 'C:\\Users\\JC\\Downloads\\amivideo\\kick12.rom'
SIG = b'SW1HOLD!'
ROWS, COLS = 224, 256
HUD_ROWS = 40                   # la barra de estado de SMW (capa 3) y su margen


# ----------------------------------------------------------------------
# 1. capture
# ----------------------------------------------------------------------
UAE = """config_description=SW1 - A500 PAL 512K+512K A501 KS1.2
chipset=ocs
chipset_compatible=A500
ntsc=false
cpu_type=68000
cpu_model=68000
chipmem_size=1
bogomem_size=2
fastmem_size=0
z3mem_size=0
kickstart_rom_file={rom}
floppy0={adf}
floppy0type=0
floppy0wp=false
nr_floppies=1
floppy_speed=100
gfx_width=720
gfx_height=568
gfx_lores=true
gfx_linemode=double
gfx_framerate=10
win32.start_not_captured=true
win32.nonotificationicon=true
win32.active_not_captured_pause=false
win32.inactive_pause=false
win32.iconified_pause=false
use_gui=no
cpu_compatible=true
cpu_speed=real
cycle_exact=true
cpu_cycle_exact=true
cpu_memory_cycle_exact=true
blitter_cycle_exact=true
immediate_blits=false
cachesize=0
"""


def window_of(pid):
    import ctypes as c
    from ctypes import wintypes as w
    u = c.WinDLL('user32', use_last_error=True)
    found = []
    proto = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)

    def cb(h, _):
        p = w.DWORD()
        u.GetWindowThreadProcessId(h, c.byref(p))
        if p.value == pid and u.IsWindowVisible(h):
            found.append(h)
        return True
    u.EnumWindows(proto(cb), 0)
    return found[0] if found else None


def grab(hwnd):
    """PrintWindow (como shot.ps1): la ventana aunque este tapada"""
    import ctypes as c
    from ctypes import wintypes as w
    from PIL import Image
    u, g = c.windll.user32, c.windll.gdi32
    r = w.RECT()
    u.GetWindowRect(hwnd, c.byref(r))
    wd, ht = r.right - r.left, r.bottom - r.top
    hdc = u.GetWindowDC(hwnd)
    mdc = g.CreateCompatibleDC(hdc)
    bmp = g.CreateCompatibleBitmap(hdc, wd, ht)
    g.SelectObject(mdc, bmp)
    ok = u.PrintWindow(hwnd, mdc, 2)

    class BIH(c.Structure):
        _fields_ = [('biSize', w.DWORD), ('biWidth', w.LONG), ('biHeight', w.LONG),
                    ('biPlanes', w.WORD), ('biBitCount', w.WORD), ('biCompression', w.DWORD),
                    ('biSizeImage', w.DWORD), ('biXPelsPerMeter', w.LONG),
                    ('biYPelsPerMeter', w.LONG), ('biClrUsed', w.DWORD), ('biClrImportant', w.DWORD)]
    bi = BIH()
    bi.biSize, bi.biWidth, bi.biHeight, bi.biPlanes, bi.biBitCount = c.sizeof(BIH), wd, -ht, 1, 32
    buf = c.create_string_buffer(wd * ht * 4)
    g.GetDIBits(mdc, bmp, 0, ht, buf, c.byref(bi), 0)
    g.DeleteObject(bmp)
    g.DeleteDC(mdc)
    u.ReleaseDC(hwnd, hdc)
    if not ok:
        return None
    return Image.frombuffer('RGB', (wd, ht), buf.raw, 'raw', 'BGRX', 0, 1)


def run_capture(a):
    from winuae_memory import ProcessMemory
    import ctypes as c
    c.windll.user32.SetProcessDPIAware()
    d = Path(a.dir).resolve()
    adf = d / 'game.adf'
    if not adf.exists():
        sys.exit('falta %s' % adf)
    lst = (d / 'game.lst').read_text(errors='replace')
    if 'sw_hold' not in lst:
        sys.exit('el build no tiene -DHOLDEVERY')
    shots = d / 'shots'
    shots.mkdir(exist_ok=True)
    (d / 'run.uae').write_text(UAE.format(rom=ROM, adf=str(adf)), encoding='ascii')
    for n in ('pid.txt', 'close.flag'):
        (d / n).unlink(missing_ok=True)
    proc = subprocess.Popen(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(LOCK),
                             str(HERE / 'd1_run.ps1'), '-Folder', str(d), '-Limit', str(a.limit)],
                            cwd=ROOT, creationflags=0x08000000)
    log = []
    try:
        while not (d / 'pid.txt').exists():
            if proc.poll() is not None:
                sys.exit('el lanzador termino antes de dar el PID')
            time.sleep(0.5)
        time.sleep(1)
        pid = int((d / 'pid.txt').read_text().strip())
        pm = ProcessMemory(pid)
        t0 = time.monotonic()
        where = None
        while where is None:                   # la firma aparece al arrancar el replay
            if time.monotonic() - t0 > a.boot:
                sys.exit('SW1HOLD! no aparecio en %d s' % a.boot)
            hits = [p for p, _ in pm.find(SIG, 18)]
            if len(hits) > 1:
                sys.exit('SW1HOLD! aparece %d veces' % len(hits))
            where = hits[0] if hits else None
            if where is None:
                time.sleep(2)
        print('firma en %#x tras %.0f s' % (where, time.monotonic() - t0))
        hwnd = window_of(pid)
        done, last_n, last_t = set(), -1, time.monotonic()
        hold_len = a.hold_len
        while True:
            raw = pm.read(where, 18)
            if raw is None or raw[:8] != SIG:
                sys.exit('la firma se perdio')
            n, k, left, _, seq = struct.unpack('>5H', raw[8:18])
            if n != last_n:
                last_n, last_t = n, time.monotonic()
            if left and seq not in done and left <= hold_len - a.settle and left >= a.settle:
                hwnd = hwnd or window_of(pid)
                img = grab(hwnd) if hwnd else None
                raw2 = pm.read(where, 18)
                n2, k2, left2, _, seq2 = struct.unpack('>5H', raw2[8:18])
                if img is not None and seq2 == seq and k2 == k and left2 > 0:
                    img.save(shots / ('k%05d.png' % k))
                    done.add(seq)
                    log.append(dict(k=k, seq=seq, left=left, left2=left2, size=img.size))
                    print('k %5d  (retencion %d, quedan %d..%d ticks)' % (k, seq, left, left2), flush=True)
            if time.monotonic() - last_t > a.idle:
                break                          # el replay termino
            time.sleep(0.1)
        pm.close()
    finally:
        (d / 'close.flag').write_text('1')
        try:
            proc.wait(60)
        except subprocess.TimeoutExpired:
            proc.kill()
    (d / 'capture.json').write_text(json.dumps(log, indent=1))
    print('%d capturas en %s' % (len(log), shots))


# ----------------------------------------------------------------------
# 2. snes
# ----------------------------------------------------------------------
def run_snes(a):
    d = Path(a.dir)
    log = json.loads((d / 'capture.json').read_text())
    frames = json.loads(Path(a.frames).read_text())
    kf = {r['k']: r['f'] for r in frames}
    pairs = [dict(k=r['k'], f=kf.get(r['k'])) for r in log]
    miss = [p['k'] for p in pairs if p['f'] is None]
    if miss:
        sys.exit('sin frame del oraculo para k = %s' % miss[:10])
    snes = d / 'snes'
    snes.mkdir(exist_ok=True)
    lf = d / 'lf'                              # P82 (7): snesorc lee LF
    lf.mkdir(exist_ok=True)
    for src in Path(a.script).parent.glob('*.orc'):
        (lf / src.name).write_bytes(src.read_bytes().replace(b'\r', b''))
    (d / 'snes_list.txt').write_text(''.join('%d\n' % p['f'] for p in pairs))
    cmd = [str(ROOT / 'work' / 'snesorc'), '--script', str(lf / Path(a.script).name),
           '--shots', str(d / 'snes_list.txt'), '--shotdir', str(snes)]
    if a.replay:
        rp = lf / 'replay.txt'
        rp.write_bytes(Path(a.replay).read_bytes().replace(b'\r', b''))
        cmd += ['--replay', str(rp), '--replay-seg', str(a.seg)]
    env = dict(os.environ)
    env.setdefault('SNESORC_ASSETS', 'C:/msys64/home/JC/.cache/snesrev-smw/smw_assets.dat')
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    sys.stderr.write(r.stderr[-600:])
    print(r.stdout[-400:])
    if r.returncode:
        sys.exit('snesorc fallo')
    (d / 'pairs.json').write_text(json.dumps(pairs, indent=1))
    falt = [p for p in pairs if not (snes / ('snes_%d.ppm' % p['f'])).exists()]
    print('%d pares; %d sin pantalla SNES' % (len(pairs), len(falt)))


# ----------------------------------------------------------------------
# 3. cmp
# ----------------------------------------------------------------------
def snes12(img):
    """RGB de 8 bits de la PPU (5 bits << 3) -> el color de 12 bits del port"""
    from palette import snes_to_amiga12
    import g5l as L
    raw = img.tobytes()
    out = []
    for i in range(0, len(raw), 3):
        w = (raw[i] >> 3) | (raw[i + 1] >> 3) << 5 | (raw[i + 2] >> 3) << 10
        out.append(L.rgb12(snes_to_amiga12(w)))
    return out


def amiga_px(shot):
    """los 256x224 pixeles del juego (centro del pixel x2, P57)"""
    import g5l as L
    im = shot.convert('RGB').crop(L.SHOT_BOX)
    out, rara = [], 0
    for y in range(ROWS):
        for x in range(COLS):
            bx, by = 2 * (x + L.SHOT_DX), 2 * y
            q = {im.getpixel((bx + i, by + j)) for i in range(2) for j in range(2)}
            if len(q) > 1:
                rara += 1
            out.append(im.getpixel((bx, by)))
    return out, rara


def diff_rows(sn, am, dy):
    """pixeles distintos con la fila Amiga y = fila SNES y + dy"""
    bad = []
    for y in range(ROWS):
        ys = y + dy
        if not 0 <= ys < ROWS:
            continue
        for x in range(COLS):
            if am[y * COLS + x] != sn[ys * COLS + x]:
                bad.append((x, y))
    return bad


def boxes(bad, gap=3):
    """cajas de las diferencias (vecinos a menos de gap px)"""
    s = set(bad)
    seen, out = set(), []
    for p in bad:
        if p in seen:
            continue
        st, comp = [p], []
        seen.add(p)
        while st:
            x, y = st.pop()
            comp.append((x, y))
            for dx in range(-gap, gap + 1):
                for dy in range(-gap, gap + 1):
                    q = (x + dx, y + dy)
                    if q in s and q not in seen:
                        seen.add(q)
                        st.append(q)
        xs, ys = [c[0] for c in comp], [c[1] for c in comp]
        out.append(dict(x0=min(xs), y0=min(ys), x1=max(xs), y1=max(ys), n=len(comp)))
    return sorted(out, key=lambda b: -b['n'])


def panel(sn, am, bad, dy, k, f, n):
    from PIL import Image, ImageDraw
    a = Image.new('RGB', (COLS, ROWS))
    a.putdata(am)
    s = Image.new('RGB', (COLS, ROWS))
    s.putdata([sn[min(max(y + dy, 0), ROWS - 1) * COLS + x] for y in range(ROWS) for x in range(COLS)])
    dimg = Image.eval(a.convert('L'), lambda v: v // 3).convert('RGB')
    for x, y in bad:
        dimg.putpixel((x, y), (255, 0, 255))
    W = 2
    out = Image.new('RGB', (3 * COLS * W + 16, ROWS * W + 18), (24, 24, 24))
    for i, im in enumerate((s, a, dimg)):
        out.paste(im.resize((COLS * W, ROWS * W), Image.NEAREST), (i * (COLS * W + 8), 18))
    ImageDraw.Draw(out).text((4, 3), 'k %d  oraculo f %d   SNES | Amiga | distintos: %d px' % (k, f, n), fill=(255, 255, 0))
    return out


def run_cmp(a):
    from PIL import Image
    d = Path(a.dir)
    pairs = json.loads((d / 'pairs.json').read_text())
    out = d / 'cmp'
    out.mkdir(exist_ok=True)
    loaded = []
    for p in pairs:
        sp = d / 'snes' / ('snes_%d.ppm' % p['f'])
        ap_ = d / 'shots' / ('k%05d.png' % p['k'])
        if sp.exists() and ap_.exists():
            am, rara = amiga_px(Image.open(ap_))
            loaded.append((p, snes12(Image.open(sp).convert('RGB')), am, rara))
    if not loaded:
        sys.exit('no hay pares')
    # alineacion vertical: la que minimiza en los primeros pares
    tot = {dy: sum(len(diff_rows(sn, am, dy)) for _, sn, am, _ in loaded[:a.align])
           for dy in range(-3, 4)}
    dy = a.dy if a.dy is not None else min(tot, key=tot.get)
    print('alineacion: fila Amiga y = fila SNES y%+d  (%s)' % (dy, ', '.join('%+d: %d' % kv for kv in sorted(tot.items()))))
    rows = []
    for p, sn, am, rara in loaded:
        bad = diff_rows(sn, am, dy)
        hud = [q for q in bad if q[1] < HUD_ROWS]
        jue = [q for q in bad if q[1] >= HUD_ROWS]
        bx = boxes(jue)
        rows.append(dict(k=p['k'], f=p['f'], distintos=len(bad), hud=len(hud), juego=len(jue),
                         cajas=bx[:12], muestreo_raro=rara))
        if len(bad):
            panel(sn, am, bad, dy, p['k'], p['f'], len(bad)).save(out / ('k%05d.png' % p['k']))
    res = dict(alineacion=dy, pares=len(rows), hud_rows=HUD_ROWS,
               exactos=sum(1 for r in rows if not r['distintos']),
               sin_hud_exactos=sum(1 for r in rows if not r['juego']), filas=rows)
    (d / 'sweep.json').write_text(json.dumps(res, indent=1))
    print('%d pares: %d exactos; fuera de la barra de estado, %d exactos' % (res['pares'], res['exactos'], res['sin_hud_exactos']))
    for r in sorted(rows, key=lambda r: -r['juego'])[:a.top]:
        print('  k %5d f %5d  juego %5d  barra %5d  cajas %s' % (
            r['k'], r['f'], r['juego'], r['hud'],
            ' '.join('%d,%d-%d,%d(%d)' % (b['x0'], b['y0'], b['x1'], b['y1'], b['n']) for b in r['cajas'][:4])))


def selftest():
    """una pantalla contra si misma = 0; corrida 1 fila = la alineacion la
    encuentra; un pixel cambiado = 1 caja de 1"""
    import random
    random.seed(1)
    sn = [(random.randrange(16) * 17, random.randrange(16) * 17, random.randrange(16) * 17) for _ in range(ROWS * COLS)]
    assert diff_rows(sn, sn, 0) == []
    am = [sn[min(y + 1, ROWS - 1) * COLS + x] for y in range(ROWS) for x in range(COLS)]
    best = min(range(-3, 4), key=lambda dy: len(diff_rows(sn, am, dy)))
    assert best == 1, best
    am2 = list(sn)
    am2[50 * COLS + 60] = (0, 0, 0) if sn[50 * COLS + 60] != (0, 0, 0) else (17, 17, 17)
    b = diff_rows(sn, am2, 0)
    assert b == [(60, 50)], b
    bx = boxes(b)
    assert len(bx) == 1 and bx[0]['n'] == 1
    print('sweep_cmp selftest: OK')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--selftest', action='store_true')
    sub = ap.add_subparsers(dest='cmd')
    c = sub.add_parser('capture')
    c.add_argument('--dir', required=True)
    c.add_argument('--limit', type=int, default=1200, help='segundos maximos de WinUAE')
    c.add_argument('--boot', type=int, default=180, help='segundos para que aparezca la firma')
    c.add_argument('--idle', type=float, default=15, help='segundos sin frames nuevos = fin')
    c.add_argument('--hold-len', type=int, default=150, help='HOLDLEN del build')
    c.add_argument('--settle', type=int, default=25, help='ticks de margen al principio y al final de la retencion')
    s = sub.add_parser('snes')
    s.add_argument('--dir', required=True)
    s.add_argument('--frames', required=True, help='frames_*.json de g5l.py game (k -> f)')
    s.add_argument('--script', required=True)
    s.add_argument('--replay', help='grabacion de smwrecomp (yi1)')
    s.add_argument('--seg', type=int, default=1)
    m = sub.add_parser('cmp')
    m.add_argument('--dir', required=True)
    m.add_argument('--dy', type=int, help='alineacion fija (por defecto, medida)')
    m.add_argument('--align', type=int, default=8, help='pares para medir la alineacion')
    m.add_argument('--top', type=int, default=25)
    a = ap.parse_args()
    if a.selftest:
        selftest()
    elif a.cmd == 'capture':
        run_capture(a)
    elif a.cmd == 'snes':
        run_snes(a)
    elif a.cmd == 'cmp':
        run_cmp(a)
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
