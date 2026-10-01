#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mkd8in.py - las entradas de dpfsplit.py / copsim.py / d8objs.py, sacadas de
los datos del ROM (antes salian de la imagen de referencia de SNESMaps):

  work/fg15.npy   capa 1 del nivel, 432 x 5120, color RGB555 por pixel
                  (r << 10 | g << 5 | b, 5 bits) y SKY = 0x197 donde no hay
                  tile (el cielo $5D80 en ese mismo formato)
  work/bg512.npy  capa 2 (el fondo), 432 x 512, mismo formato

    python tools/mkd8in.py [--level levels/yi1.json]
                                (usa work/level_final.png y work/bg_mountains.png;
                                 los genera con mkbg si no estan; los nombres
                                 salen del descriptor del nivel, lvdesc.py)
"""
import argparse
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "..", "work")
sys.path.insert(0, HERE)
import lvdesc                                   # noqa: E402


def rgb555(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.int32) >> 3
    return (a[..., 0] << 10 | a[..., 1] << 5 | a[..., 2]).astype(np.int32)


def main():
    ap = argparse.ArgumentParser()
    lvdesc.add_arg(ap)
    a = ap.parse_args()
    d = lvdesc.load(a.level)
    l1 = d.out["level_png"]
    bg = d.out["bg_png"]
    if not (os.path.exists(l1) and os.path.exists(bg)):
        subprocess.check_call([sys.executable, os.path.join(HERE, "mkbg.py")]
                              + (["--level", a.level] if a.level else []))
    fg = rgb555(l1)
    b = rgb555(bg)
    sky = 0x197
    print("capa 1 %s, cielo %d px; capa 2 %s, cielo %d px"
          % (fg.shape, (fg == sky).sum(), b.shape, (b == sky).sum()))
    np.save(d.out["fg15"], fg)
    np.save(d.out["bg512"], b)
    print("-> work/fg15.npy, work/bg512.npy")


if __name__ == "__main__":
    main()
