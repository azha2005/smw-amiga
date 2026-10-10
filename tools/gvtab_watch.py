#!/usr/bin/env python3
"""P123: vigilar la escritura de GV_TAB en un WinUAE propio, sin sondas asm.

Requiere un ADF -DADRTRAP y su listado. Usa el IPC oficial de WinUAE
(DBG w ... BW): una escritura posterior a g5l_init causa bus error y
ADRTRAP guarda el PC escritor. Cada pipe se cruza con el PID propio.
Fuentes: tonioni/WinUAE, uaeipc.cpp y debug.cpp (comando memwatch).
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import struct
import subprocess
import time
from pathlib import Path

from m68kverify import symbols
from winuae_memory import ProcessMemory


class Pipe:
    def __init__(self, pid):
        self.k = k = C.WinDLL('kernel32', use_last_error=True)
        k.CreateFileW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, W.LPVOID, W.DWORD, W.DWORD, W.HANDLE]
        k.CreateFileW.restype = W.HANDLE
        k.GetNamedPipeServerProcessId.argtypes = [W.HANDLE, C.POINTER(W.ULONG)]
        k.CloseHandle.argtypes = [W.HANDLE]
        k.WriteFile.argtypes = [W.HANDLE, W.LPCVOID, W.DWORD, C.POINTER(W.DWORD), W.LPVOID]
        k.ReadFile.argtypes = [W.HANDLE, W.LPVOID, W.DWORD, C.POINTER(W.DWORD), W.LPVOID]
        k.PeekNamedPipe.argtypes = [W.HANDLE, W.LPVOID, W.DWORD, W.LPVOID, C.POINTER(W.DWORD), W.LPVOID]
        for i in range(10):
            name = r'\\.\pipe\WinUAE' + ('_%d' % i if i else '')
            h = k.CreateFileW(name, 0xC0000000, 0, None, 3, 0, None)
            if h == C.c_void_p(-1).value:
                continue
            owner = W.ULONG()
            if k.GetNamedPipeServerProcessId(h, C.byref(owner)) and owner.value == pid:
                self.h = h
                return
            k.CloseHandle(h)
        raise RuntimeError('no hay IPC de nuestro PID %d' % pid)

    def command(self, text):
        raw = b'\xef\xbb\xbf' + (text + '\0').encode('utf-8')
        count = W.DWORD()
        if not self.k.WriteFile(self.h, raw, len(raw), C.byref(count), None):
            raise C.WinError(C.get_last_error())
        end = time.monotonic() + 5
        available = W.DWORD()
        while time.monotonic() < end:
            self.k.PeekNamedPipe(self.h, None, 0, None, C.byref(available), None)
            if available.value:
                buf = C.create_string_buffer(16384)
                if not self.k.ReadFile(self.h, buf, len(buf), C.byref(count), None):
                    raise C.WinError(C.get_last_error())
                return buf.raw[:count.value].decode('utf-8-sig').rstrip('\0')
            time.sleep(.02)
        raise RuntimeError('IPC sin respuesta')

    def close(self):
        self.k.CloseHandle(self.h)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('adf', type=Path)
    ap.add_argument('lst', type=Path)
    ap.add_argument('--seconds', type=int, default=150)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    s = symbols(str(a.lst))
    # adrtrap.py deja esta configuración cycle-exact junto al ADF.
    cfg = a.adf.parent / 'at.uae'
    if not cfg.exists() or str(a.adf.resolve()) not in cfg.read_text():
        raise RuntimeError('crear primero at.uae con adrtrap.py para este ADF')
    p = subprocess.Popen([r'C:\Program Files\WinUAE\winuae64.exe', '-f', str(cfg.resolve())])
    pipe = None
    mem = None
    try:
        mem = ProcessMemory(p.pid)
        end = time.monotonic() + a.seconds
        host = None
        while time.monotonic() < end and host is None:
            for h, _ in mem.find(b'G5L1', 16):
                raw = mem.read(h + s['g5l_v'] + s['GV_TAB'] - s['g5l_table'], 4)
                if not raw:
                    continue
                ptr = struct.unpack('>I', raw)[0]
                base = ptr - s['g5l_table']
                if 0xC00000 <= base < 0xC80000:
                    host = h - s['g5l_table']
                    break
            if host is None:
                time.sleep(.2)
        if host is None:
            raise RuntimeError('g5l_init no encontrado')
        pipe = Pipe(p.pid)
        target = base + s['g5l_v'] + s['GV_TAB']
        print('PID %d, base $%X, GV_TAB $%X' % (p.pid, base, target), flush=True)
        print(pipe.command('DBG w 0 %x 4 BW' % target), flush=True)
        while time.monotonic() < end:
            raw = mem.read(host + s['at_sig'], 100)
            if raw and struct.unpack_from('>I', raw, 8)[0]:
                a.out.parent.mkdir(parents=True, exist_ok=True)
                a.out.with_suffix('.trap').write_bytes(raw)
                a.out.with_suffix('.slow').write_bytes(mem.read(host - (base - 0xC00000), 0x80000))
                kind = struct.unpack_from('>H', raw, 16)[0]
                if kind == 0:
                    fc, acc, ir, sr, pc = struct.unpack_from('>HIHHI', raw, 18)
                    print('PC $%X = B+$%X; acceso $%X, IR $%04X, fc $%X' % (pc, pc-base, acc, ir, fc))
                else:
                    sr, pc = struct.unpack_from('>HI', raw, 18)
                    print('excepción %d PC B+$%X' % (kind, pc-base))
                print('registros', ' '.join('%08X' % v for v in struct.unpack_from('>16I', raw, 32)))
                return 1
            time.sleep(.1)
        print('sin escritura de GV_TAB después de init')
        return 0
    finally:
        if pipe:
            pipe.close()
        if mem:
            mem.close()
        p.kill()


if __name__ == '__main__':
    raise SystemExit(main())
