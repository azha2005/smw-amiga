# G7-3c — abaratar el productor por fila y portar ventana/EDF

2026-10-11. Leer antes `docs/informe-g7-3b-1011.md`. El productor es
`player/g7fast.s`; la especificación, `tools/g7_fast.py`. **Orden de trabajo
para cualquier cambio de regla: primero la especificación (cinco trazas,
`rows_wrong` = 0), después el 68000 y `g7f_verify` igual.** Una mejora
solo cuenta si `--profile all` la muestra.

## Entorno

```sh
export PATH="/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python PYTHONIOENCODING=utf-8
GDEFS="-DREPLAY -DG7_BOBS" OUT=work/g7f/b2 sh tools/bm_build.sh
python tools/g7f_verify.py --bin work/g7f/b2/game.bin --lst work/g7f/b2/game.lst \
    --layers fast --to-k 400 --profile all [--local]
```

Trazas (binarios del mismo árbol, después de compilar yi1):

```sh
for t in pw_bloques chuck_kill spin_kill stress_piranha; do
  GDEFS="-DREPLAY -DG7_BOBS" XCDEFS=-DLSS_SNESORC ORACLE=work/oracle_$t.bin \
  REPLAY=work/sws/${t}_replay.bin OUT=work/g7f/t_$t NOCC=1 sh tools/bm_build.sh
done
```

Especificación sola (rápida, sin 68000):
`python tools/g7_fast.py --bin work/g7fast/bins/<t>/game.bin --lst … --no-hidden`.

## Pasos

1. **Línea base**: repetir el YI1 completo (`--profile all`) y anotar
   media/p99/máximo y ciclos por rutina.
2. **Usados por bloque Map16** para `g7f_free`: tabla de los índices que
   usa cada fila de cada bloque (calculada al iniciar el nivel, no por
   frame). Antes de tocar el 68000, comprobar en Python, en las cinco
   trazas, que el PF1 materializado coincide con lo que da la tabla en
   las palabras sin efectos; si no coincide siempre, buscar la causa
   (cambios de tiles, P34) y no usar la tabla en esas palabras.
3. **Diario disperso**: guardar solo las palabras que el parche cambia
   (MOVE del prefijo y NOP) y restaurarlas en `g7b_restore`. Cruzar con
   `g7_bobs_verify --core-only` y añadir el caso al núcleo.
4. **Overlay**: grupos de 8 enteros en pantalla sin control de rango por
   píxel; `g7f_entries` con salida temprana. Medir.
5. **Ventana y EDF** en el 68000 (`g7f_left`), con `place` cerrado (ya
   igual a la fuerza bruta en Python). `g7f_verify --layers
   fast,window,edf` en las cinco trazas: 0 diferencias y rechazos solo
   donde la especificación no tiene plan.
6. Lint, regresión completa, `sws_gate`, `oam68k_gate`, memmap del vivo
   y del replay con G7_BOBS (márgenes 1.840 B chip y 12.768 B slow hoy).
   Hash del vivo por defecto `33f2250a…` sin cambios.

## No hacer

- No activar G7_BOBS por defecto ni decidir el presupuesto de G7 (decisión
  del usuario pendiente, PROXIMO §1).
- No usar tablas por número de frame. No aproximar colores.
- No declarar un ahorro sin el perfil y la media/p99/máximo del YI1 entero.
