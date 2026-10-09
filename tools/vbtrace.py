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
    'win32.start_not_captured=true', 'win32.nonotificationicon=true', '']), encoding='ascii')
proc = subprocess.Popen([r'C:\Program Files\WinUAE\winuae64.exe', '-f', str(cfg)])
try:
    time.sleep(wait)

    class MBI(c.Structure):
        _fields_ = [('BaseAddress', c.c_void_p), ('AllocationBase', c.c_void_p), ('AllocationProtect', w.DWORD),
                    ('PartitionId', w.WORD), ('RegionSize', c.c_size_t), ('State', w.DWORD),
                    ('Protect', w.DWORD), ('Type', w.DWORD)]
    k = c.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.restype = w.HANDLE
    k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    k.VirtualQueryEx.argtypes = [w.HANDLE, c.c_void_p, c.POINTER(MBI), c.c_size_t]
    k.VirtualQueryEx.restype = c.c_size_t
    k.ReadProcessMemory.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t, c.POINTER(c.c_size_t)]
    h = k.OpenProcess(0x410, False, proc.pid)
    if not h:
        raise SystemExit('OpenProcess fallo')

    def read(a, n):
        b = c.create_string_buffer(n)
        got = c.c_size_t()
        if not k.ReadProcessMemory(h, c.c_void_p(a), b, n, c.byref(got)) or got.value != n:
            return None
        return b.raw
    addr, best = 0, None
    while addr < 0x7fffffffffff:
        m = MBI()
        if not k.VirtualQueryEx(h, c.c_void_p(addr), c.byref(m), c.sizeof(m)):
            break
        base = m.BaseAddress or 0
        if m.State == 0x1000 and m.Protect in (0x04, 0x40, 0x02, 0x20) and m.RegionSize < (1 << 31):
            data = read(base, m.RegionSize)
            if data:
                i = data.find(b'VBTRACE!')
                while i >= 0:
                    self_, ptr, lst, n = struct.unpack_from('>IIIH', data, i + 8)
                    if self_ and ptr:
                        best = (base + i, self_, ptr, n)
                    i = data.find(b'VBTRACE!', i + 1)
        addr = base + m.RegionSize
    if not best:
        raise SystemExit('sin traza')
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
