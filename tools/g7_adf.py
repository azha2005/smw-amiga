#!/usr/bin/env python3
"""Agregar fuente G7 tras los datos, sin retenerla en el binario slow."""
from pathlib import Path
import argparse
import struct


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--adf',required=True)
    ap.add_argument('--payload',default='work/g7/sources.rle')
    ap.add_argument('--cdma',default='work/g5l/g5l_clean.dma')
    a=ap.parse_args();p=Path(a.adf);adf=bytearray(p.read_bytes())
    header=adf.index(b'A5PL',1024);off,n=struct.unpack_from('>II',adf,header+4)
    start=off+n;payload=Path(a.payload).read_bytes();dma=Path(a.cdma).read_bytes()
    pad=(len(dma)+511)&~511
    assert len(dma)==34760
    assert len(payload)<=2560 and start+pad+2560<=len(adf)
    assert not any(adf[start:start+pad+2560]),'zona ocupada'
    adf[start:start+len(dma)]=dma
    adf[start+pad:start+pad+len(payload)]=payload;p.write_bytes(adf)
    print('G7 ADF: OK cdma=%d payload=%d start=%d sectors=%d+5'%(len(dma),len(payload),start,pad//512))


if __name__=='__main__':main()
