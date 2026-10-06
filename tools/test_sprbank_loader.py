#!/usr/bin/env python3
"""Ejecuta el loader 68000 REAL, con Exec/trackdisk simulados (no DMA).

    python tools/test_sprbank_loader.py --game work/g3-replay --bank work/g3/bank
"""
import argparse
import pathlib
import struct
import time
import memmap as M
from sprgfx_final import require


def execute(folder, prefix, corrupt=None, fail_alloc=0, short_read=False):
    from unicorn import Uc, UC_ARCH_M68K, UC_MODE_BIG_ENDIAN, UC_HOOK_CODE
    from unicorn import m68k_const as R
    cpu = Uc(UC_ARCH_M68K, UC_MODE_BIG_ENDIAN)
    cpu.ctl_set_cpu_model(R.UC_CPU_M68K_M68000)
    cpu.mem_map(0, 0x1000000)
    listing = M.Listing(pathlib.Path(folder+'/game.lst').read_text())
    base, ret, stack, req, execbase = 0x10000, 0xffff00, 0x7f000, 0x81000, 0x90000
    cpu.mem_write(base, pathlib.Path(folder+'/game.bin').read_bytes())
    chip = bytearray(pathlib.Path(prefix+'.dma').read_bytes())
    tables = bytearray(pathlib.Path(prefix+'.idx').read_bytes())
    if corrupt == 'chip': chip[10] ^= 1
    if corrupt == 'tables': tables[10] ^= 1
    diskbase = 0x100000
    dma_rel, table_rel = listing.sym('SG3_DMA_REL'), listing.sym('SG3_TABLE_REL')
    chunks = {diskbase+dma_rel: bytes(chip)+bytes(listing.sym('SG3_DMA_ALLOC')-len(chip))}
    padded = bytes(tables)+bytes((-len(tables))%512)
    chunks.update({diskbase+table_rel+i: padded[i:i+512] for i in range(0,len(padded),512)})
    reg = lambda name: getattr(R,'UC_M68K_REG_'+name.upper())
    get = lambda name: cpu.reg_read(reg(name))
    put = lambda name,v: cpu.reg_write(reg(name),v)
    read32 = lambda adr: struct.unpack('>I',cpu.mem_read(adr,4))[0]
    allocations, frees, reads = [], [], []
    originals = {}
    for n in ('d2','d3','d4','d5','d6','d7','a2','a3','a4','a5','a6'):
        originals[n] = 0x123400+len(originals)*8
    originals.update(a2=req,a6=execbase,d7=diskbase)
    for n,v in originals.items(): put(n,v)
    put('a7',stack-4)
    cpu.mem_write(stack-4,struct.pack('>I',ret))
    services = {execbase+listing.sym(n): n for n in ('_LVOAllocMem','_LVOFreeMem','_LVODoIO')}
    def hook(uc, address, size, user):
        if address not in services: return
        name = services[address]
        if name == '_LVOAllocMem':
            n,flags = get('d0'),get('d1')
            target = (0x60000,0xc00000,0x70000)[len(allocations)]
            allocations.append((target,n,flags))
            put('d0',0 if len(allocations)==fail_alloc else target)
        elif name == '_LVOFreeMem':
            frees.append((get('a1'),get('d0')))
        else:
            request = get('a1')
            actual,length,offset = read32(request+40),read32(request+36),read32(request+44)
            # IO_DATA=40, LENGTH=36, OFFSET=44 (exec.i).
            blob = chunks[offset]
            require(len(blob)==length,'DoIO longitud inesperada')
            cpu.mem_write(actual,blob)
            cpu.mem_write(request+32,struct.pack('>I',length-1 if short_read else length))
            reads.append((actual,length,offset))
            put('d0',0)
        # ABI caller-save realmente destruida para detectar dependencia.
        put('d1',0xdeadbeef); put('a0',0xdeadbeef); put('a1',0xdeadbeef)
        sp = get('a7')
        put('pc',read32(sp)); put('a7',sp+4)
    cpu.hook_add(UC_HOOK_CODE,hook)
    cpu.emu_start(base+listing.sym('sg3_load'),ret)
    success = not(corrupt or fail_alloc or short_read)
    require(get('d0')==(0 if success else 1),'loader resultado incorrecto')
    require(all(get(n)==v for n,v in originals.items()),'loader rompe ABI')
    if success:
        require(bytes(cpu.mem_read(0x60000,len(chip)))==chip,'DMA cargado distinto')
        require(bytes(cpu.mem_read(0xc00000,len(tables)))==tables,'tablas cargadas distintas')
        require(frees==[(0x70000,512)],'scratch no liberado exactamente')
        require(read32(base+listing.sym('sg3_dma'))==0x60000 and
                read32(base+listing.sym('sg3_tables'))==0xc00000,'publicacion invalida')
    else:
        require(read32(base+listing.sym('sg3_dma'))==read32(base+listing.sym('sg3_tables'))==0,
                'publicacion antes de validar todo el banco')
    return len(reads)


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game',required=True)
    ap.add_argument('--bank',required=True)
    a=ap.parse_args()
    started=time.perf_counter()
    count=execute(a.game,a.bank)
    wall=time.perf_counter()-started
    for kw in (dict(corrupt='chip'),dict(corrupt='tables'),dict(short_read=True),
               dict(fail_alloc=1),dict(fail_alloc=2),dict(fail_alloc=3)):
        execute(a.game,a.bank,**kw)
    print('Loader 68000: OK (7 casos, ABI, %d lecturas, scratch liberado)' % count)
    print('Caso valido completo: %.3f s de host Unicorn (sin disco ni DMA; no tiempo PAL)' % wall)
