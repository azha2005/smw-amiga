"""Diagnóstico G5a por ReadProcessMemory, solo PID abierto por la prueba."""
import argparse
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import struct
import m68kverify as V


class MBI(c.Structure):
    _fields_=[('BaseAddress',c.c_void_p),('AllocationBase',c.c_void_p),
              ('AllocationProtect',w.DWORD),('PartitionId',w.WORD),
              ('RegionSize',c.c_size_t),('State',w.DWORD),('Protect',w.DWORD),('Type',w.DWORD)]


def dump(pid, binpath, lstpath):
    code=Path(binpath).read_bytes(); syms=V.symbols(lstpath)
    pattern=code[64:128]
    bank=Path('work/g5a_base.dma').read_bytes()
    k=c.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.restype=w.HANDLE
    k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD]
    k.VirtualQueryEx.argtypes=[w.HANDLE,c.c_void_p,c.POINTER(MBI),c.c_size_t]
    k.VirtualQueryEx.restype=c.c_size_t
    k.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)]
    k.CloseHandle.argtypes=[w.HANDLE]
    h=k.OpenProcess(0x410,False,pid)
    if not h: raise OSError(c.get_last_error(),'OpenProcess')
    found=[]
    try:
        addr=0
        while addr<0x7fffffffffff:
            m=MBI()
            if not k.VirtualQueryEx(h,addr,c.byref(m),c.sizeof(m)): break
            region=m.BaseAddress or 0; end=region+m.RegionSize
            if m.State==0x1000 and not m.Protect&0x101 and m.Protect&0xee:
                for start in range(region,end,4*1024*1024):
                    n=min(4*1024*1024+len(code),end-start)
                    buf=c.create_string_buffer(n); got=c.c_size_t()
                    if not k.ReadProcessMemory(h,start,buf,n,c.byref(got)):continue
                    data=buf.raw[:got.value]; pos=data.find(pattern)
                    while pos>=64:
                        base=pos-64
                        if base+len(code)<=len(data):
                            item={'host_bin':hex(start+base)}
                            for name in('g_left','gl_done','gb_frn','dc_st','g5a_chip','vars'):
                                if name in syms:
                                    offset=base+syms[name]
                                    item[name]=data[offset:offset+40].hex()
                            for name in ('dc_rec','g5a_controls','g5a_jobs'):
                                if name in syms:
                                    offset=base+syms[name]
                                    item[name]=data[offset:offset+64].hex()
                            found.append(item)
                        pos=data.find(pattern,pos+len(pattern))
                    pos=data.find(bank)
                    while pos>=0:
                        found.append({'bank_host':hex(start+pos),'bank_sha256':'exact match'})
                        pos=data.find(bank,pos+len(bank))
            if end<=addr:break
            addr=end
        live=[f for f in found if 'g5a_chip' in f]
        for item in live:
            ptr=int(item['g5a_chip'][:8],16)
            copa=int(item['vars'][16:24],16);copb=int(item['vars'][24:32],16)
            for bankitem in [f for f in found if 'bank_host' in f]:
                chipbase=int(bankitem['bank_host'],16)-ptr
                for name,amiga in [('copa',copa),('copb',copb)]:
                    buf=c.create_string_buffer(248);got=c.c_size_t()
                    if k.ReadProcessMemory(h,chipbase+amiga,buf,248,c.byref(got)):
                        item[name+'_'+hex(chipbase)]=buf.raw[:got.value].hex()
    finally:k.CloseHandle(h)
    return found


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pid',type=int,required=True)
    ap.add_argument('--bin',required=True);ap.add_argument('--lst',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args();results=dump(a.pid,a.bin,a.lst)
    Path(a.out).write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
