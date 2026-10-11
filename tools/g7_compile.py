#!/usr/bin/env python3
"""Compilar productor G7 opt-in separado del small-data de la logica."""
import os
from pathlib import Path
import re
import subprocess


def main():
    root=Path('C:/Users/JC/vbcc')
    if os.environ.get('VBCC','').startswith('C:'):root=Path(os.environ['VBCC'])
    dest=Path('work/g7/prod.s')
    subprocess.run([str(root/'bin/vbccm68k.exe'),'-quiet','-c99','-cpu=68000',
                    '-O='+os.environ.get('G7_OPT','1'),'-inline-size=0','-sc','-o='+str(dest),'player/g7prod.c'],check=True)
    text=dest.read_text()
    text=re.sub(r'\bl([0-9]+)\b',r'g7prod_l\1',text)
    text=text.replace('__divs','_g7b_div16')
    text=re.sub(r'^(\s*jsr\s+)(_g7b_(?:send|save_row|retry|div16))\s*$',r'\1\2_bridge',text,flags=re.M)
    text=re.sub(r'^\s*section\s+.*\n','',text,flags=re.M)
    dest.write_text(text)


if __name__=='__main__':main()
