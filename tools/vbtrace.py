#!/usr/bin/env python3
"""vbtrace.py - la sucesion de imagenes que muestra la Amiga, VBL por VBL.

Corre un ADF armado con game.s -DVBTRACE (replay) en WinUAE cycle-exact
(como a500.uae), espera al final del replay, lee la traza de la memoria del
proceso (filas .w R_FRAME de la foto que se ve, .w SPR4POS de su lista; la
firma 'VBTRACE!' esta en el binario) y resume: VBL que repiten la imagen,
fotos salteadas (el frame logico avanza 2) y sus frames.

    sh tools/game_build.sh con GDEFS="-DREPLAY -DG5L -DCUSHION -DVBTRACE"
    python tools/vbtrace.py work/vt/game.adf work/vt/trace.bin [segundos]

Un tiron visible es un par: un VBL repite y, unos frames despues, se
saltea una foto (la latencia no puede quedar en 3, P112)."""
import sys, time, struct, subprocess, ctypes as c
from ctypes import wintypes as w
from pathlib import Path

adf = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
wait = int(sys.argv[3]) if len(sys.argv) > 3 else 160
cfg = adf.parent / 'vt.uae'
cfg.write_text('\n'.join([
    'chipset=ocs', 'chipset_compatible=A500', 'ntsc=false', 'cpu_type=68000', 'cpu_model=68000',
    'cpu_compatible=true', 'cpu_speed=real', 'cycle_exact=true', 'cpu_cycle_exact=true',
    'cpu_memory_cycle_exact=true', 'blitter_cycle_exact=true', 'immediate_blits=false', 'cachesize=0',
    'chipmem_size=1', 'bogomem_size=2', 'fastmem_size=0', 'z3mem_size=0',
    r'kickstart_rom_file=C:\Users\JC\Downloads\amivideo\kick12.rom',
    'floppy0=%s' % adf, 'floppy0type=0', 'nr_floppies=1', 'floppy_speed=100',
    'gfx_width=720', 'gfx_height=568', 'gfx_lores=true', 'gfx_linemode=double',
    'win32.start_not_captured=true', 'win32.nonotificationicon=true', 'use_gui=no', '']), encoding='ascii')
proc = subprocess.Popen([r'C:\Program Files\WinUAE\winuae64.exe', '-f', str(cfg)])
try:
    time.sleep(wait)

    # La misma lectura que bm_probe/load_probe (winuae_memory): regiones
    # de hasta 256 MB. La firma tambien esta en la copia del ADF (ceros).
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from winuae_memory import ProcessMemory
    mem = ProcessMemory(proc.pid)
    read = mem.read
    best, seen = None, 0
    for host, raw in mem.find(b'VBTRACE!', 22):
        seen += 1
        self_, ptr, lst, n = struct.unpack_from('>IIIH', raw, 8)
        if self_ and ptr:
            best = (host, self_, ptr, n)
    if not best:
        raise SystemExit('sin traza (%d firmas sin inicializar)' % seen)
    hs, self_, ptr, n = best
    raw = read(hs + (ptr - self_), n * 4)
    if raw is None:
        raise SystemExit('no pude leer la traza (%x %x)' % (self_, ptr))
    out.write_bytes(raw)
    print('filas', n, 'sig %x ptr %x' % (self_, ptr))
    rows = [struct.unpack_from('>HH', raw, 4 * i) for i in range(n)]
    last = rows[-1][0] if rows else 0
    rep = [f for (f, _), (pf, _) in zip(rows[1:], rows) if f == pf and f != last]
    sk = [f for (f, _), (pf, _) in zip(rows[1:], rows) if (f - pf) & 0xFFFF == 2]
    print('VBL que repiten (sin el final del replay):', len(rep), rep)
    print('fotos salteadas:', len(sk), sk)
finally:
    proc.kill()
