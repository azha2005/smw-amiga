# G7-S1 — efectos en sprites de hardware (híbrido con el PF1)

2026-10-11. **Elegida por el usuario el 2026-10-11** (opción (a), PROXIMO §1). Leer antes
`docs/informe-g7-s0-1011.md` (la medida) y `docs/informe-g7-3c-1011.md`
(el productor PF1, que queda para el resto). Orden de AGENTS.md: primero
la especificación en Python con su verificador, después el 68000.

## Entorno

```sh
export PATH="/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python PYTHONIOENCODING=utf-8
# builds siempre con el candado (comparten work/cc)
GDEFS="-DREPLAY -DG7_BOBS" OUT=work/g7s1/b sh work/buildlock.sh sh tools/bm_build.sh
python tools/g7_sprite_room.py --bin work/g7fast/bins/yi1/game.bin \
    --lst work/g7fast/bins/yi1/game.lst --single --pack --out work/g7s0/yi1-pack.json
```

## Pasos

1. **Especificación** (`tools/g7_sprite_fx.py`): a partir de las reglas de
   `g7_sprite_room.py` (canal libre con una línea de margen, frente por
   BPLCON2, color en COLOR17-31 vigente, empaquetado en 16 px), producir
   por foto los **datos de sprite y las cadenas DMA**, no solo el veredicto.
   Lo que no entra en sprites va al productor PF1 (`g7_fast.py`), filas
   aparte.
2. **Lo que G7-S0 no probó**, cerrarlo en la especificación antes de
   escribir asm:
   - solapes entre efectos (1.581 píxeles en YI1): el orden de los canales
     tiene que respetar el de la OAM;
   - canales que Mario o los enemigos usan en otras filas: coordinar con
     los constructores de flujos de G5L (la cadena se copia por lista,
     P125);
   - los 25 casos de YI1 sin plan en ninguna de las dos vías (meta): apoyo
     de color de G7-C o rechazo explícito.
3. **Verificador de píxeles**: componer pantalla (`g7_hw_support.dma_image`
   + `visibility`) y exigir 0 diferencias contra la referencia SNES en las
   cinco trazas (como `g7_color_plan.py`).
4. **Medir antes de portar**: filas PF1 restantes por foto y ciclos
   estimados (armar sprites + `g7fast.s` en lo que quede). Si el p99 no
   baja de un frame, informar y no seguir sin el usuario.
5. 68000 opt-in (`-DG7_SPR`), cruzado palabra a palabra con la
   especificación; puertas de siempre (lint, regresión, `sws_gate`,
   `oam68k_gate`, memmap; hash del vivo por defecto `33f2250a…`).

## No hacer

- No activar G7_BOBS por defecto.
- No usar tablas por número de frame. No aproximar colores.
- No tocar el banco de sprites de Mario/Rex sin cruzarlo con G5L.
