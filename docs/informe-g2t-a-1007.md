# G2T-A — contrato fijado, calibración ampliada y puerta A-T

2026-10-07 (noche). Ejecutada por el coordinador, sin subagentes, rama
`wt/g2ta-1007` desde `6bef73f`. El usuario delegó la decisión del
contrato («hacelo, te doy libertad creativa»). Commit del código:
`70a0c0d`.

**Resultado: la puerta A-T queda verde en las tres trazas (3404 frames
con Rex) con un contrato corregido por medidas.** El contrato candidato
de G2T no era físicamente válido: el hueco entre filas admite muchos
menos MOVE de los que suponía. Se midió la capacidad real, se corrigió un
paso del modelo de copper en el codo (P110) y el modelo nuevo
(`tools/g2t_ref.py`) usa solo configuraciones con caso exacto y control
negativo en WinUAE cycle-exact. **No hay aún dibujador en la Amiga:**
esto habilita escribir y ejecutar B/C (`docs/instrucciones-g2t-bc.md`).

## 1. Partida (repetida)

Entorno PC, `export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH"`.
Lint, regress `--baseline tools/baseline_pc.json --level`, OAM68K,
`test_g2t.py` (10) y `test_g5ref.py` (8): verdes. G5 original sale 1 con
SHA256 del resumen `3d254a01…4722f8b7` (idéntico). `g2t_audit.py`:
2288/661/455 frames, 0 sin plan en la cota horizontal, 131+44+14 = 189 en
la cota C2. La calibración `--repair-wrap` de G2T se reproduce: 0 errores
en los positivos, negativo $C0 9/9/9/0, 14210-14211 ticks.

## 2. Lo que la calibración de G2T no veía

`tools/g2t_cal.py build-suite --suite main` (5 ADF) reproduce segmentos
reales: borrado de 7/8/9 MOVE con **COLOR01 como último MOVE** (visible en
x = 0..6), primera carga real en x = 7 (WAIT $4C), colas reales, sufijo y
salto; audio DMA encendido además de los seis planos y los ocho sprites.
El sprite A llega a x = 255 en la fila y (lo cambia el primer MOVE del
sufijo); el B empieza en x = 0 en la fila y + 1 (lo cambia el último).

Con el sufijo candidato (WAIT $D0 + 8 MOVE) **los sprites salen exactos,
pero la carga de x = 7 de la línea siguiente cae en x = 47** (borrado 7,
copper libre) y hasta **x = 119** (borrado 9, última carga en x = 255).
El arnés de G2T solo comprobaba el *primer* MOVE del borrado y no tenía
carga temprana: no podía verlo (P111). Logs: `work/g2ta_cal*.result.json`.

## 3. Capacidad medida y regla

Suite `cap` (63 casos, variante F, 4 ADF): MOVE que caben tras x = 255
sin mover el borrado ni la carga de x = 7.

| arranque del sufijo | borrado 7 | 8 | 9 |
|---|---|---|---|
| copper libre, WAIT $D0 | 5 | 4 | 3 |
| tras carga en x = 255, con WAIT $D0 | 3 | 2 | 1 |
| tras carga en x = 255, encadenado | 5 | 4 | 3 |

Todo cuadra con una regla: **el último MOVE del sufijo cae en
x ≤ 351 − 8·nb** en las unidades de `scrollsim` (16 px por MOVE en
pantalla, 8 px después de x = 239). Los casos «medio» de la suite main lo
confirman (arranque en 183 con 8 MOVE: bien; en 243: tarde).

## 4. El codo del copper (P110)

Suite `knee` (24 sondas, COLOR01 sin sprites delante, dos ADF): posición
real de cada MOVE tras WAIT $74..$CE, con y sin NOP. Coincide con el
modelo en todo **salvo un paso: el MOVE siguiente a uno en x = 231 cae en
x = 243, no en 247** (12 px), y desde ahí a 8 px (251, 259...). Ejemplos:
WAIT $A4 → 183 199 215 231 **243** 251; WAIT $BC → 231 **243** 251.
Corregido en `g2t_ref.advance` y en la suite final. Efecto sobre el
scroll actual (`scrollsim.py` con el paso medido, informativo, no se
tocó el scroll): 5119 → 5110 px de capa 1 mal en todo el nivel, 134 → 138
frames con fallos.

## 5. Suite final: cada familia en su límite

`--suite final` (5 ADF, 83 casos: **56 positivos, 27 negativos**), log
`work/g2ta_cal_read.log`, resultados `work/g2ta_final*.result.json`,
comparaciones apiladas `work/g2ta_final*_compare.png` (miradas).

- **Fin**, para nb = 7/8/9: cadena tras x = 255, 247, 239 y 231; WAIT $D0
  tras carga en 207; WAIT $C4 con copper libre. Positivo con el último
  MOVE en el límite (variantes S y F: sprite en x = 0 y fondo en x = 0..7)
  y negativo un paso después. **Todos los positivos exactos y todos los
  negativos fallan** (la carga de x = 7 cae en 16-23 o el borrado llega
  tarde).
- **Principio:** el primer MOVE justo después del último píxel A
  (cadenas tras 183, 223, 239, 247; con 3 y 4 NOP; WAIT $BC a 48 px de la
  carga y WAIT $7C con el copper libre): positivos exactos, negativos con
  exactamente 1 píxel por fila.
- **Colas reales** copiadas de las listas (`$68.1+$90.2+$CE.1`,
  `$88.3+$C0.3`, `$80.4+$C0.3`, `$A0.1+$B8.4`) + cadena k = 5, nb 7: exactas.
- **Armado VBL** en v = 26, 27, 30 con recorte 0/2/3: exacto; v = 16:
  falla (detectado).

Barras $A55A y 14202-14211 ticks PAL en las cinco capturas. Repetición:
`python tools/g2t_cal.py build-suite --suite final --adf N`, ensamblar con
`-I player -I work`, `mkadf.py`, captura por el candado con
`tools/shot.ps1 -Exact -Wait 80`, `read-suite --shot ... --meta ...`.

Dos fallos de la primera tanda eran del arnés y se corrigieron, no se
ocultaron: un caso en v = 253 cruzaba la línea 255 con WAIT (255,$E2)
(P59; ahora los casos terminan en v ≤ 246) y un negativo de WAIT $7C
partía de una cola que el modelo ya decía que terminaba en x = 71.

## 6. Modelo y puerta A-T

```sh
python tools/g2t_ref.py --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin --trace work/oam_normal.trace=work/oracle_normal_oam.bin --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin --bank work/g3/bank --out work/g2t_ref
# PUERTA A-T: OK   (log work/g2t_ref.log, ~35 s)
```

| traza | registros | frames con Rex | A2 | Mario Amiga≠SNES | sin_variante_temporal | sin_plazo | errores_color | errores_capa1 | prioridad_distinta | sin_destino |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| yi1 | 3712 | 2288 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 383 |
| normal | 1045 | 661 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 220 |
| spin_kill | 641 | 455 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 75 |

- 69 293 transiciones de color (máx. 80 en un frame); sufijos: 20 365
  encadenados y 13 595 con WAIT; máx. 7 MOVE en un sufijo; el bloque VBL
  nunca necesitó colores (máx. 0); el segmento más largo con sufijo mide
  124 B (cabe aun en los 220 actuales; se presupuestan +36 por las 12
  cargas posibles de `build_mid`).
- En los 3404 frames la variante elegida es la **primera A3**.
- Ningún frame necesita sufijo en la línea 255 ni recorte superior.
- Rex sin píxeles visibles (testigos fuera de pantalla, informados
  aparte): 372 / 132 / 53. f5811 es uno (sx = 283). f6150 se resuelve con
  15 transiciones en 11 sufijos.
- Cámara Y ≠ 192: 0 / 15 / 145 frames; el fondo sigue fijo en Y = 192
  hasta S8 (repetir esa parte con S8).
- Mario: `mario_amiga` reproduce `mario_sprite()` (caja ≤ 32×40, cuatro
  entradas, primera opaca gana) y coincide con la VRAM dinámica en las
  filas comunes (R = 1..223) de los 5398 registros. Encuadre del port
  entero, no de esta tarjeta: 62 píxeles de Mario en la fila 224 de la
  SNES (OAM y = 223) no existen en la Amiga.
- Comprobaciones independientes: cada píxel de Mario y del Rex (también
  ocluidos) contra el registro simulado; la fuente SNES de cada píxel del
  Rex contra el índice DMA; los flujos desde PT contra la pose; y la lista
  reconstruida con cada sufijo: eventos de capa 1 idénticos a la original
  y posiciones de los MOVE re-derivadas de los bytes iguales a las del
  plan (esta comprobación encontró un error mío, encadenar desde el
  final del borrado, que se corrigió prohibiéndolo).
- Imágenes: `work/g2t_ref/muestras.png`, 17 recortes ×4 de las tres
  trazas (compartido, sentidos, borde, solape, sufijo máximo, f6150):
  fuente SNES | simulación | fallos; ningún píxel en magenta.
- Banco G3 intacto: SHA256 `.dma 4dd51fcc…`, `.idx 8589b85a…`;
  SHA256 de `work/g2t_ref/resumen.json`: `ad87f9a3…effe1b`.

Tests sin ROM: `tools/test_g2t_ref.py` (10: codo, negro/blanco contiguo,
restauración a `R_PAL`, sprite fuera de pantalla, orden de directorio,
sin ranura, regla de fin, WAIT con copper libre, barrera 255, capa 1 y
re-derivación), llamado por `regress.py` (consta en `work/regress.log`).

## 7. Presupuesto

| recurso | antes | con G2T-A | límite |
|---|---:|---:|---:|
| banco DMA (chip) | 64 528 | 64 528 | 65 536 |
| tablas (slow) | 72 724 | 72 724 | 98 304 |
| segmento × 224 × 2 listas (chip) | 220 B | 256 B: **+16 128 B** | — |
| bloque VBL × 2 listas (chip) | — | ≤ 128 B: **+256 B** | — |
| chip replay / vivo (estimado) | 455 728 / 467 256 | 472 112 / 483 640 | 524 288 |
| trabajo del plan (slow, estimado) | — | ≤ 24 KiB | 32 768 |

Estimado: margen vivo ≈ 40 648 B. Repetir `memmap.py` al implementar C.

## 8. No hecho

Plan en C/68000 (B), emisor en el juego y captura con las listas reales
(C), coste de captura/plan/emisión, compuerta D1 con control, cobertura
global (G4-G7/G9), S8. La envolvente de Mario se emula desde la OAM de la
traza: B debe comprobar que coincide con el buffer real de la foto O5.
L-OAM sigue roja (41,2 % > 40 %). No se hizo push.
