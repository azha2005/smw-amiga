#!/usr/bin/env python3
"""Lectura de firmas de una instancia propia de WinUAE (Windows)."""
import ctypes as c
from ctypes import wintypes as w


class MBI(c.Structure):
    _fields_ = [('BaseAddress', c.c_void_p), ('AllocationBase', c.c_void_p),
                ('AllocationProtect', w.DWORD), ('PartitionId', w.WORD),
                ('RegionSize', c.c_size_t), ('State', w.DWORD),
                ('Protect', w.DWORD), ('Type', w.DWORD)]


class ProcessMemory:
    def __init__(self, pid):
        self.k = c.WinDLL('kernel32', use_last_error=True)
        self.k.OpenProcess.restype = w.HANDLE
        self.k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        self.k.CloseHandle.argtypes = [w.HANDLE]
        self.k.VirtualQueryEx.argtypes = [w.HANDLE, c.c_void_p, c.POINTER(MBI), c.c_size_t]
        self.k.VirtualQueryEx.restype = c.c_size_t
        self.k.ReadProcessMemory.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p,
                                            c.c_size_t, c.POINTER(c.c_size_t)]
        self.handle = self.k.OpenProcess(0x410, False, pid)
        if not self.handle:
            raise OSError(c.get_last_error(), 'OpenProcess')

    def read(self, address, size):
        buf, got = c.create_string_buffer(size), c.c_size_t()
        ok = self.k.ReadProcessMemory(self.handle, address, buf, size, c.byref(got))
        return buf.raw if ok and got.value == size else None

    def find(self, signature, size):
        address = 0
        while address < 0x7fffffffffff:
            m = MBI()
            if not self.k.VirtualQueryEx(self.handle, address, c.byref(m), c.sizeof(m)):
                break
            base = m.BaseAddress or 0
            if m.State == 0x1000 and m.Protect in (4, 0x40, 2, 0x20) and m.RegionSize < 1 << 28:
                data = self.read(base, m.RegionSize)
                if data:
                    pos = data.find(signature)
                    while pos >= 0:
                        raw = self.read(base + pos, size)
                        if raw:
                            yield base + pos, raw
                        pos = data.find(signature, pos + 1)
            address = base + m.RegionSize

    def close(self):
        if self.handle:
            self.k.CloseHandle(self.handle)
            self.handle = None
