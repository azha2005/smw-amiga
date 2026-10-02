#!/usr/bin/env python3
"""
smwtabx.py - tablas .DB de otros bancos (no el 00) que usa el C del port,
sacadas del fuente por su etiqueta, a player/gen/smwtabx.h (generado, no
se versiona: son bytes de la ROM, R9).

    python tools/smwtabx.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from smwgen import SRC, OUT, parse_tables  # noqa: E402

# (fichero, etiqueta, nombre en C)
WANT = [
    ("sprite_2-clus.s", "SpriteSlotMax", "tx_SpriteSlotMax"),
    ("sprite_2-clus.s", "SpriteSlotMax1", "tx_SpriteSlotMax1"),
    ("sprite_2-clus.s", "SpriteSlotMax2", "tx_SpriteSlotMax2"),
    ("sprite_2-clus.s", "SpriteSlotStart", "tx_SpriteSlotStart"),
    ("sprite_2-clus.s", "SpriteSlotStart1", "tx_SpriteSlotStart1"),
    ("sprite_2-clus.s", "ReservedSprite1", "tx_ReservedSprite1"),
    ("sprite_2-clus.s", "ReservedSprite2", "tx_ReservedSprite2"),
    ("sprite_2-clus.s", "DATA_02A7F6", "tx_02A7F6"),
    ("sprite_2-clus.s", "DATA_02A7F9", "tx_02A7F9"),
    ("sprite_1-main.s", "DATA_019030", "tx_019030"),
    ("sprite_1-main.s", "DATA_01902E", "tx_01902E"),
    ("sprite_1-main.s", "SpriteObjClippingX", "tx_SprObjClipX"),
    ("sprite_1-main.s", "SpriteObjClippingY", "tx_SprObjClipY"),
    ("sprite_1-main.s", "DATA_019134", "tx_019134"),
    ("sprite_1-main.s", "DATA_0192C5", "tx_0192C5"),
    ("sprite_1-main.s", "DATA_0192C7", "tx_0192C7"),
    ("sprite_1-main.s", "DATA_019284", "tx_019284"),
    ("sprite_1-main.s", "DATA_019285", "tx_019285"),
    ("sprite_3-1.s", "RexSpeed", "tx_RexSpeed"),
    ("sprite_3-1.s", "DATA_03B83F", "tx_03B83F"),
    ("sprite_3-1.s", "DATA_03B847", "tx_03B847"),
    ("sprite_3-1.s", "DATA_03B75C", "tx_03B75C"),
    ("sprite_3-1.s", "DATA_03B75E", "tx_03B75E"),
    ("sprite_3-2.s", "DATA_03C1C6", "tx_03C1C6"),
    ("sprite_3-2.s", "DATA_03C1C8", "tx_03C1C8"),
    ("sprite_3-1.s", "SprClippingDispX", "tx_ClipDispX"),
    ("sprite_3-1.s", "SprClippingWidth", "tx_ClipWidth"),
    ("sprite_3-1.s", "SprClippingDispY", "tx_ClipDispY"),
    ("sprite_3-1.s", "SprClippingHeight", "tx_ClipHeight"),
    ("sprite_3-1.s", "MarioClipDispY", "tx_MarioClipDispY"),
    ("sprite_3-1.s", "MarioClippingHeight", "tx_MarioClipH"),
    ("sprite_1-1.s", "DATA_01AD68", "tx_01AD68"),
    ("sprite_1-main.s", "DATA_01A61E", "tx_01A61E"),
    ("sprite_3-1.s", "DATA_038954", "tx_038954"),
    ("sprite_3-1.s", "DATA_038956", "tx_038956"),
    ("sprite_3-1.s", "DATA_038D66", "tx_038D66"),
    ("sprite_1-1.s", "DATA_01AD6A", "tx_01AD6A"),
    ("sprite_tables.s", "Sprite1656Vals", "tx_1656"),
    ("sprite_tables.s", "Sprite1662Vals", "tx_1662"),
    ("sprite_tables.s", "Sprite166EVals", "tx_166E"),
    ("sprite_tables.s", "Sprite167AVals", "tx_167A"),
    ("sprite_tables.s", "Sprite1686Vals", "tx_1686"),
    ("sprite_tables.s", "Sprite190FVals", "tx_190F"),
]

# Tablas de un solo sprite (P3, Chuck): van en un bloque aparte, #ifdef
# SMWTABX_CHUCK, para que solo las vea player/spr_chuck.c, que define la
# macro antes de incluir este header. Asi msprite.c (que incluye todo lo
# de arriba) no las emite y spr_chuck.c no emite las de arriba (P36/P78:
# vbcc emite todo static const aunque no se use).
WANT_CHUCK = [
    ("sprite_1-main.s", "DATA_018526", "tc_018526"),
    ("sprite_2-1.s", "DATA_02C213", "tc_02C213"),
    ("sprite_2-1.s", "DATA_02C228", "tc_02C228"),
    ("sprite_2-1.s", "DATA_02C22A", "tc_02C22A"),
    ("sprite_2-1.s", "DATA_02C62E", "tc_02C62E"),
    ("sprite_2-1.s", "DATA_02C639", "tc_02C639"),
    ("sprite_2-1.s", "DATA_02C666", "tc_02C666"),
    ("sprite_2-1.s", "DATA_02C69F", "tc_02C69F"),
    ("sprite_2-1.s", "DATA_02C6A3", "tc_02C6A3"),
    ("sprite_2-1.s", "DATA_02C73D", "tc_02C73D"),
    ("sprite_2-1.s", "DATA_02C743", "tc_02C743"),
    ("sprite_2-1.s", "DATA_02C79B", "tc_02C79B"),
]

# Cinta de meta $7B (P5): igual, bajo SMWTABX_GOAL (player/spr_goal.c)
WANT_GOAL = [
    ("sprite_1-1.s", "DATA_01C0A5", "tg_01C0A5"),
    ("sprite_tables.s", "DATA_07F1AA", "tg_07F1AA"),
]

# Tablas de los caparazones (P4, player/spr_shell.c): bloque #ifdef
# SMWTABX_SHELL, igual que el del Chuck (P36/P78).
WANT_SHELL = [
    ("sprite_1-main.s", "DATA_0197AF", "ts_0197AF"),
    ("sprite_1-main.s", "ShellSpeedX", "ts_ShellSpeedX"),
    ("sprite_1-main.s", "DATA_019F5B", "ts_019F5B"),
    ("sprite_1-main.s", "DATA_019F61", "ts_019F61"),
    ("sprite_1-main.s", "DATA_019F67", "ts_019F67"),
    ("sprite_1-main.s", "DATA_019F69", "ts_019F69"),
    ("sprite_1-main.s", "DATA_019F99", "ts_019F99"),
]


# La seta $74 y lo que sale de los bloques (P6, player/spr_powerup.c): bloque
# #ifdef SMWTABX_POWERUP, igual que los de arriba (P36/P78).
WANT_POWERUP = [
    ("sprite_1-1.s", "ItemBoxSprite", "tp_ItemBox"),
    ("sprite_1-1.s", "GivePowerPtrIndex", "tp_GivePtr"),
    ("sprite_1-1.s", "DATA_01AE88", "tp_01AE88"),
    ("sprite_2-clus.s", "SpriteInBlock", "tp_InBlock"),
    ("sprite_2-clus.s", "StatusOfSprInBlk", "tp_StatInBlk"),
]


def main():
    cache = {}
    with open(os.path.join(OUT, "smwtabx.h"), "w") as f:
        f.write("/* GENERADO por tools/smwtabx.py desde el fuente: no editar ni versionar */\n")
        f.write("#ifndef SMWTABX_H\n#define SMWTABX_H\n")
        for sect, want in (("#if defined(SMWTABX_CHUCK)\n", WANT_CHUCK),
                           ("#elif defined(SMWTABX_SHELL)\n", WANT_SHELL),
                           ("#elif defined(SMWTABX_GOAL)\n", WANT_GOAL),
                           ("#elif defined(SMWTABX_POWERUP)\n", WANT_POWERUP),
                           ("#else\n", WANT)):
            f.write(sect)
            for fn, lab, name in want:
                if fn not in cache:
                    cache[fn] = parse_tables(os.path.join(SRC, fn))
                d = cache[fn].get(lab)
                if not d:
                    sys.exit("no encuentro %s en %s" % (lab, fn))
                f.write("static const unsigned char %s[%d] = {%s};\n"
                        % (name, len(d), ",".join(str(b) for b in d)))
        f.write("#endif\n#endif\n")
    print("smwtabx.h: %d tablas (+ %d del Chuck, + %d de los caparazones, + %d de la meta, + %d de la seta)"
          % (len(WANT), len(WANT_CHUCK), len(WANT_SHELL), len(WANT_GOAL), len(WANT_POWERUP)))


if __name__ == "__main__":
    main()
