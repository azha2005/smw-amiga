#!/usr/bin/env python3
"""adrtrap.py - el PC de una excepcion de la CPU en el juego (-DADRTRAP).

Exec muestra la Guru 3 sin el PC del fallo. Con game.s -DADRTRAP, los
vectores de bus, direccion e ilegal guardan el marco y los registros detras
de 'ADRTRAP!'; esto corre el ADF en WinUAE cycle-exact, espera, lo lee de la
memoria del proceso y lo traduce con el listado.

    GDEFS="-DREPLAY -DBENCH -DADRTRAP" OUT=work/at sh tools/game_build.sh
    python tools/adrtrap.py work/at/game.adf work/at/game.lst [segundos]
"""
import re, sys, time, struct, subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from winuae_memory import ProcessMemory

adf = Path(sys.argv[1]).resolve()
lst = Path(sys.argv[2])
wait = int(sys.argv[3]) if len(sys.argv) > 3 else 190
cfg = adf.parent / 'at.uae'
cfg.write_text('\n'.join([
    'chipset=ocs', 'chipset_compatible=A500', 'ntsc=false', 'cpu_type=68000', 'cpu_model=68000',
    'cpu_compatible=true', 'cpu_speed=real', 'cycle_exact=true', 'cpu_cycle_exact=true',
    'cpu_memory_cycle_exact=true', 'blitter_cycle_exact=true', 'immediate_blits=false', 'cachesize=0',
    'chipmem_size=1', 'bogomem_size=2', 'fastmem_size=0', 'z3mem_size=0',
    r'kickstart_rom_file=C:\Users\JC\Downloads\amivideo\kick12.rom',
    'floppy0=%s' % adf, 'floppy0type=0', 'nr_floppies=1', 'floppy_speed=100',
    'gfx_width=720', 'gfx_height=568', 'gfx_lores=true', 'gfx_linemode=double',
    'win32.start_not_captured=true', 'win32.nonotificationicon=true', 'use_gui=no', '']), encoding='ascii')

# etiquetas del listado de vasm: "00:0000ABCD ... nombre:" (incluye locales)
labels = []
for ln in open(lst, encoding='latin-1'):
    m = re.match(r'^[0-9A-F]{2}:([0-9A-F]{8}) .*?\t\s*\d+: ([A-Za-z_.][\w.]*):', ln)
    if m:
        labels.append((int(m.group(1), 16), m.group(2)))
labels.sort()


def where(off):
    best = None
    for v, k in labels:
        if v > off:
            break
        best = (k, off - v)
    return '%s+$%X' % best if best else '?'


proc = subprocess.Popen([r'C:\Program Files\WinUAE\winuae64.exe', '-f', str(cfg)])
try:
    time.sleep(wait)
    mem = ProcessMemory(proc.pid)
    hit = None
    for host, raw in mem.find(b'ADRTRAP!', 100):
        if struct.unpack_from('>I', raw, 8)[0]:
            hit = raw
    if not hit:
        print('sin excepcion (ninguna firma ADRTRAP! escrita)')
        sys.exit(0)
    base, kind = struct.unpack_from('>IH', hit, 12)
    fr = hit[18:32]
    regs = struct.unpack_from('>16I', hit, 32)
    usp = struct.unpack_from('>I', hit, 96)[0]
    if kind == 0:
        fc, acc, ir, sr, pc = struct.unpack_from('>HIHHI', fr)
        print('grupo 0: fc $%X (%s), direccion $%X, IR $%04X, SR $%04X'
              % (fc, 'lectura' if fc & 16 else 'escritura', acc, ir, sr))
    else:
        sr, pc = struct.unpack_from('>HI', fr)
        print('grupo 1/2: SR $%04X' % sr)
    print('PC $%X = binstart + $%X (%s)  [binstart $%X]' % (pc, pc - base, where(pc - base), base))
    print('d0-d7 ' + ' '.join('%08X' % r for r in regs[:8]))
    print('a0-a7 ' + ' '.join('%08X' % r for r in regs[8:]))
    print('usp %08X' % usp)
    sys.exit(1)
finally:
    proc.kill()
