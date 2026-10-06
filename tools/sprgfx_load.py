#!/usr/bin/env python3
"""Empaqueta SG3F/2 al final del ADF; no agranda hdr_data_len del scroll."""
import argparse
import pathlib
import struct
import zlib
from sprgfx_final import derived_path, require
from sprgfx_bank import deserialize_bank


def prepare(prefix, include):
    chip = pathlib.Path(prefix+'.dma').read_bytes()
    tables = pathlib.Path(prefix+'.idx').read_bytes()
    deserialize_bank(tables, chip)
    scroll = pathlib.Path('work/yi1_s.dat').read_bytes()
    align = lambda n: (n+511)&-512
    constants = dict(SG3_DMA_BYTES=len(chip), SG3_DMA_ALLOC=align(len(chip)),
                     SG3_TABLE_BYTES=len(tables), SG3_TABLE_ALLOC=(len(tables)+7)&-8,
                     SG3_DMA_REL=align(len(scroll)),
                     SG3_TABLE_REL=align(len(scroll))+align(len(chip)),
                     SG3_DMA_CRC=zlib.crc32(chip), SG3_TABLE_CRC=zlib.crc32(tables))
    derived_path(include)
    pathlib.Path(include).write_text(''.join('%s equ $%08x\n' % pair for pair in constants.items()))
    return constants


def append(prefix, adf):
    deserialize_bank(pathlib.Path(prefix+'.idx').read_bytes(), pathlib.Path(prefix+'.dma').read_bytes())
    image = bytearray(pathlib.Path(adf).read_bytes())
    magic = image.find(b'A5PL', 1024, 1088)
    require(magic >= 0, 'ADF sin A5PL')
    offset, length = struct.unpack_from('>II', image, magic+4)
    require(length == (len(pathlib.Path('work/yi1_s.dat').read_bytes())+511)&-512,
            'ADF/scroll distinto')
    at = offset+length
    for suffix in ('.dma', '.idx'):
        blob = pathlib.Path(prefix+suffix).read_bytes()
        end = at+((len(blob)+511)&-512)
        require(end <= len(image), 'banco no cabe en ADF')
        image[at:at+len(blob)] = blob
        image[at+len(blob):end] = bytes(end-at-len(blob))
        at = end
    derived_path(adf)
    pathlib.Path(adf).write_bytes(image)
    print('SG3F/2 ADF: banco+tablas hasta byte %d; scroll sin cambio' % at)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bank', required=True)
    ap.add_argument('--include')
    ap.add_argument('--adf')
    a = ap.parse_args()
    require(bool(a.include) != bool(a.adf), 'usar --include o --adf')
    if a.include:
        prepare(a.bank, a.include)
    else:
        append(a.bank, a.adf)
