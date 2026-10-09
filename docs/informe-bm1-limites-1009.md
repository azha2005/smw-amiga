# BM1 — límite de sincronías en pistas corruptas (2026-10-09)

Revisión posterior al WIP `a41da43`. Una pista llena de palabras $4489
podía prolongar la búsqueda de sincronía fuera del DMA antes de probar
una cabecera. Se comprueba también el límite en ese bucle: cualquier
cabecera que se decodifique tiene sus 1080 bytes completos dentro de
BM_RAW. No cambia el formato ni la disposición de memoria.

`mfm_verify.py` añade pistas de sincronía continua para cada pista/mode:
**84 casos exactos**, máximo **342588 ciclos sin DMA**, incluido el caso
corrupto. El informe BM1 anterior medía 70 casos y otro conjunto de
entradas; sus 246386 ciclos no son una regresión del coste por frame.
El decoder solo corre durante carga. Boot final: **988 bytes**, límite 1024.

Lint y regress `--baseline tools/baseline_pc.json --level --bm1`: OK,
incluyendo selftest de memoria de 17 casos y Z1. El juego normal/boot normal no
cambian: cinco MD5 del informe T. La ROM1.3 y el teclado físico siguen
pendientes. Evidencia del boot final en `work/session/bm-z1/shot-final.png`;
el frame411 debe volver con $71=00, X0010/Y0160.
