#!/usr/bin/env python3
"""Exporta D1TR del PID WinUAE propio tras done=1, sin pausas.
Valida binario/listado, puntero runtime slow y dos lecturas estables.
"""
import argparse, ctypes as c, hashlib, json, re, struct
from pathlib import Path
from ctypes import wintypes as w
class MBI(c.Structure):
    _fields_=[('BaseAddress',c.c_void_p),('AllocationBase',c.c_void_p),('AllocationProtect',w.DWORD),('PartitionId',w.WORD),('RegionSize',c.c_size_t),('State',w.DWORD),('Protect',w.DWORD),('Type',w.DWORD)]
def export(pid,binary,listing):
    image=binary.read_bytes(); marker=image.index(b'D1TR'); signature=image[marker-2:marker+30]; sigoff=marker-2
    symbols=dict((name,int(addr,16)) for addr,name in re.findall(r'^([0-9A-Fa-f]{8}) (\w+)$',listing.read_text(),re.M))
    ptr_offset=symbols['d1_ptr']; k=c.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.restype=w.HANDLE; k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD]
    k.VirtualQueryEx.argtypes=[w.HANDLE,c.c_void_p,c.POINTER(MBI),c.c_size_t]; k.VirtualQueryEx.restype=c.c_size_t
    k.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)]
    k.CloseHandle.argtypes=[w.HANDLE]
    h=k.OpenProcess(0x410,False,pid)
    if not h: raise OSError(c.get_last_error(),'OpenProcess')
    def read(addr,size):
        b=c.create_string_buffer(size);got=c.c_size_t()
        if not k.ReadProcessMemory(h,addr,b,size,c.byref(got)) or got.value!=size:return None
        return b.raw
    found=[]; seen=[]; codebases=set()
    try:
        addr=0
        while addr<0x7fffffffffff:
            m=MBI()
            if not k.VirtualQueryEx(h,addr,c.byref(m),c.sizeof(m)):break
            region=m.BaseAddress or 0;end=region+m.RegionSize
            if m.State==0x1000 and not m.Protect&0x101 and m.Protect&0xEE:
                for start in range(region,end,4*1024*1024):
                    data=read(start,min(4*1024*1024+160000,end-start))
                    if data is None:continue
                    pos=data.find(signature)
                    while pos>=0:
                        codebases.add(start+pos-sigoff);pos=data.find(signature,pos+1)
                    pos=data.find(b'D1TR')
                    while pos>=0:
                        if pos+32<=len(data):
                            version,row,cap,count,done,overflow,tpf=struct.unpack_from('>HHIIHHH',data,pos+4)
                            events=struct.unpack_from('>H',data,pos+22)[0];selfaddr=struct.unpack_from('>I',data,pos+28)[0]
                            if version==2 and row==20 and cap==4600:
                                seen.append(dict(host=hex(start+pos),rows=count,done=done,overflow=overflow,events=events,self=hex(selfaddr)))
                                size=32+cap*row+events*12
                                if 1<count<=cap and 0<events<=cap and done==1 and not overflow and 0xc00000<=selfaddr and selfaddr+147232<=0xc80000 and pos+size<=len(data):
                                    blob=data[pos:pos+size]
                                    if read(start+pos,size)==blob:found.append((start+pos,selfaddr,blob))
                        pos=data.find(b'D1TR',pos+4)
            if end<=addr:break
            addr=end
        validated=[]
        for host,selfaddr,blob in found:
            mapping=host-selfaddr
            for codebase in codebases:
                amigabase=codebase-mapping
                if 0xc00000<=amigabase and amigabase+len(image)<=0xc80000 and read(codebase+ptr_offset,4)==struct.pack('>I',selfaddr):
                    validated.append((host,selfaddr,blob,codebase,amigabase))
        unique={item[2] for item in validated}
        if len(unique)!=1:raise ValueError('trazas validas distintas %d; cabeceras %r' % (len(unique),seen))
        host,selfaddr,blob,codebase,amigabase=validated[0]
        return blob,dict(pid=pid,host_address=hex(host),amiga_trace_address=hex(selfaddr),amiga_bin_address=hex(amigabase),host_bin_address=hex(codebase),symbol_d1_ptr=hex(ptr_offset),
                         binary_sha256=hashlib.sha256(image).hexdigest(),listing_sha256=hashlib.sha256(listing.read_bytes()).hexdigest(),raw_sha256=hashlib.sha256(blob).hexdigest(),
                         method='ReadProcessMemory; done=1, lectura estable repetida; puntero d1_ptr del bin/listado y rango slow validados')
    finally:k.CloseHandle(h)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--pid',required=True,type=int);ap.add_argument('--bin',required=True,type=Path);ap.add_argument('--lst',required=True,type=Path);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
    blob,meta=export(a.pid,a.bin,a.lst);a.out.write_bytes(blob);a.out.with_suffix('.export.json').write_text(json.dumps(meta,indent=2))
if __name__=='__main__':main()
