#!/usr/bin/env python3
"""G7-3: RLE reversible del banco; el payload solo vive en work/."""
from pathlib import Path
import argparse


def pack(raw):
    out=bytearray(); i=0
    while i<len(raw):
        run=1
        while i+run<len(raw) and raw[i+run]==raw[i] and run<129: run+=1
        if run>=3:
            out.extend((128+run-2,raw[i]));i+=run
            continue
        first=i;i+=run
        while i<len(raw) and i-first<128:
            n=1
            while i+n<len(raw) and raw[i+n]==raw[i] and n<3:n+=1
            if n>=3:break
            i+=min(n,128-(i-first))
        out.append(i-first-1);out.extend(raw[first:i])
    return bytes(out)


def unpack(raw):
    out=bytearray();i=0
    while i<len(raw):
        n=raw[i];i+=1
        if n&128:
            out.extend(bytes([raw[i]])*((n&127)+2));i+=1
        else:
            n+=1;out.extend(raw[i:i+n]);i+=n
    return bytes(out)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sources',default='work/g7/sources.bin')
    ap.add_argument('--out',default='work/g7/sources.rle')
    a=ap.parse_args();raw=Path(a.sources).read_bytes()
    compact=raw[:1296]+raw[1296::2]
    encoded=pack(compact)
    decoded=unpack(encoded)
    expanded=decoded[:1296]+bytes(v for b in decoded[1296:] for v in (b,0))
    assert len(raw)==7616 and expanded==raw
    assert len(encoded)<=2560,'payload excede cinco sectores'
    Path(a.out).write_bytes(encoded)
    print('G7 PACK: OK source=%d payload=%d'%(len(raw),len(encoded)))


if __name__=='__main__':main()
