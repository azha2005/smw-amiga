#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lvdesc.py - descriptor de nivel (ROADMAP 11.2, paso 1).

Un JSON por nivel en levels/<nombre>.json con lo que hoy estaba fijo en las
herramientas de la cadena del nivel (mklvl, mkbg, mkd8in, mkleveld, mkmapbin):

  dir      carpeta del nivel, relativa a mw_e10 (_DEF_SRC)
  obj/spr  nombres de obj*.lv / spr.lv dentro de `dir`
  header   los 5 bytes de la cabecera de obj (hex): las herramientas paran si
           el .lv no la tiene (cazar un descriptor de otro nivel)
  bg       nombre del fondo de la capa 2 (levels/data/bg/<bg>.bg)
  camera   ventana vertical de la camara: y0 (primera linea visible) y lines
           (lineas visibles). Lo lee mkscroll (todavia no: I2 no lo toca)
  out      rutas de salida, relativas a la raiz del repo (la carpeta de tools/..)
  subzones zonas secundarias (obj-1.lv ...): informativo, para T1

Uso en un script:

    import lvdesc
    lvdesc.add_arg(ap)                  # --level levels/yi1.json
    d = lvdesc.load(a.level)            # d.obj, d.spr, d.out["fg15"], d.camera ...

Sin --level se usa levels/yi1.json (YI1): las llamadas de siempre no cambian.
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(_HERE, ".."))
DEFAULT = os.path.join(ROOT, "levels", "yi1.json")

# claves de `out` que tiene que traer todo descriptor
OUT_KEYS = ("mklvl_png", "level_png", "bg_png", "level_comp_png", "fg15", "bg512",
            "d", "d_ideal", "scroll", "map16")


def _src():
    from lvparse import _DEF_SRC
    return _DEF_SRC


class Level(object):
    def __init__(self, path, raw):
        self.path = path
        self.name = raw["name"]
        self.header = bytes.fromhex(raw["header"])
        if len(self.header) != 5:
            raise SystemExit("%s: header tiene que ser de 5 bytes (10 digitos hex)" % path)
        self.dir = os.path.join(_src(), *raw["dir"].split("/"))
        self.obj = os.path.join(self.dir, raw["obj"])
        self.spr = os.path.join(self.dir, raw["spr"]) if raw.get("spr") else None
        self.bg = raw["bg"]
        cam = raw["camera"]
        self.camera = {"y0": int(cam["y0"]), "lines": int(cam["lines"])}
        missing = [k for k in OUT_KEYS if k not in raw["out"]]
        if missing:
            raise SystemExit("%s: faltan salidas en `out`: %s" % (path, ", ".join(missing)))
        # sin normalizar (tools/../work/...): asi los mensajes de las herramientas no cambian
        self.out = {k: os.path.join(_HERE, "..", *v.split("/")) for k, v in raw["out"].items()}
        self.subzones = raw.get("subzones", [])

    def check_header(self, data):
        """`data` = bytes de obj*.lv: la cabecera tiene que ser la del descriptor"""
        if bytes(data[:5]) != self.header:
            raise SystemExit("%s: la cabecera de %s es %s y el descriptor dice %s"
                             % (self.path, self.obj, bytes(data[:5]).hex().upper(),
                                self.header.hex().upper()))


def load(path=None):
    path = path or DEFAULT
    if not str(path).lower().endswith(".json"):
        raise SystemExit("--level espera un descriptor .json (levels/<nombre>.json), no %r" % path)
    with open(path, "r", encoding="utf-8") as f:
        return Level(path, json.load(f))


def add_arg(ap):
    ap.add_argument("--level", default=None, metavar="JSON",
                    help="descriptor del nivel (levels/<nombre>.json); por defecto levels/yi1.json")
