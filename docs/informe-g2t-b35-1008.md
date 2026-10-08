# G2T-B35 — continuación del handoff y parada por coste

2026-10-08. Rama **`g2t-b35`**, sin merge a master ni push.
Se completaron los pendientes verificables del handoff de B35 y su único
intento permitido de optimización en C. **B4/B5 y la red de seguridad
están verdes; la puerta de rendimiento sigue roja.** No se integra el
plan en vivo y no se declara terminada G2T-B/C.

## 1. Commits y alcance

- `307394a`: implementación original y arneses B3/B4/B5.
- `dac4244`: restauración de las declaraciones de `g5plan.h`.
- `213ba3c`: único intento disperso en C, pruebas pendientes, paso 4c
  de OAM68K, perfil reproducible y corrección T0 = −56.
- `06e777f`: revisión final de la frontera opaca de Mario; se repitieron
  todas las puertas y medidas después de esta corrección.

El checkout principal ya estaba en `g2t-b35` al iniciar. El worktree
`agent-ab11504b219aac969` abierto en el IDE estaba limpio, en un commit
anterior (`8073e62`); no contenía los commits del handoff. La continuación
se hizo sobre la rama que sí los tenía. No se modificaron ese worktree
ni los de otras tarjetas. `.claude/` ya aparecía sin seguimiento antes
de esta sesión y queda intacto.

Cambios: Mario se calcula por la frontera B2/B3 una vez por foto; los
usos se recorren en la unión ordenada de filas de Mario y Rex (máximo
72); tres mapas de 14 palabras invalidan usos, segmentos y filas de
salida, sin borrar las tablas de 224 entradas. Solo se serializan las
filas con recargas. Se conserva el orden exacto de la especificación.
`g5_capture` y `tools/g2t_ref.py` no se modificaron.
La frontera se consulta una vez por fila de pantalla, sin leer
`G5B_MROW` fuera de ella; los intentos reutilizan solo sus filas activas.

## 2. Exactitud y negativos

Se recompiló también el **código anterior con el header restaurado** y
se repitió B5 en las tres trazas antes de cambiarlo: 3404 frames, cero
planes distintos y cero violaciones del ABI.

El paso 4c nuevo regenera el modelo, las listas y la tabla de envolventes
desde el código actual; después ejecuta B4 y B5 en todas las trazas.
Registro completo: `work/b35_oam68k.log`; detalle: `work/g2tb35/`.

### B3-0/B3-1/B3-2/B4

```text
yi1: 2288 frames con Rex, segw 23641020 B, segs 2059200 B (segw reproduce segments)
normal: 661 frames con Rex, segw 6847856 B, segs 594900 B (segw reproduce segments)
spin_kill: 455 frames con Rex, segw 4685156 B, segs 409500 B (segw reproduce segments)
```

```text
frontera B2/B3: 512512 filas, 204504 pares; diferencias 0
g5plan_test: 2288 frames; segmentos distintos 0 de 512512 filas; plan -> work/g2tb35/plan_yi1.bin
frontera B2/B3: 148064 filas, 53081 pares; diferencias 0
g5plan_test: 661 frames; segmentos distintos 0 de 148064 filas; plan -> work/g2tb35/plan_normal.bin
frontera B2/B3: 101920 filas, 35939 pares; diferencias 0
g5plan_test: 455 frames; segmentos distintos 0 de 101920 filas; plan -> work/g2tb35/plan_spin_kill.bin
```

Los tres `cmp work/g2tb35/plan_<traza>.bin
work/g2t_ref/plan_<traza>.bin` salieron con 0. Total: **762 496 filas**
y **293 524 pares de Mario**. El área de trabajo se inicializa con
`$A5` y luego se reutiliza: la exactitud no depende de tablas borradas.

### B3-3: envolventes del Rex

Se conserva la opción (a), máscaras exactas de 24 bits con paleta por
pose. Los huecos sobreviven al recorte; no se sustituye por extremos.
La cabecera lleva versión, cantidad de poses y los dos CRC del banco.
El lector rechaza versiones, offsets, longitudes, índices y CRC inválidos.

```text
G5EV usos oam_yi1: 2288 frames, 46025 variantes, 10341 con recorte, diferencias 0
G5EV usos oam_normal: 661 frames, 13768 variantes, 3996 con recorte, diferencias 0
G5EV usos oam_spin_kill: 455 frames, 8687 variantes, 1876 con recorte, diferencias 0
G5EV: OK work/g3/bank.g5env: 289 poses, 133040 B
```

Cada variante del Rex elegido, incluidos casos fuera de pantalla, se
compara con `g2t_ref.uses_of`: **68 480 casos**. Ocho pruebas sintéticas
sin ROM en `tools/test_g5bank_env.py` comprueban el formato, colores,
transparencia, huecos y ambos bordes, y ya corren desde `regress.py`.

### B5: planes y ABI

```text
g5_plan 68000 yi1: 2288 frames, planes distintos 0, ABI distinta 0; ciclos (sin DMA) media 1029485, mediana 909174, p99 2127066, max 2395526 (frame 7515)
PUERTA G2T-B5 yi1: OK
g5_plan 68000 normal: 661 frames, planes distintos 0, ABI distinta 0; ciclos (sin DMA) media 975118, mediana 842608, p99 2136028, max 2314848 (frame 2198)
PUERTA G2T-B5 normal: OK
g5_plan 68000 spin_kill: 455 frames, planes distintos 0, ABI distinta 0; ciclos (sin DMA) media 963040, mediana 826594, p99 2164364, max 2405022 (frame 2140)
PUERTA G2T-B5 spin_kill: OK
```

OAM68K repitió también sus seis comprobaciones 4b: B2 PC y captura
68000 exactos en 2288/661/455 frames, ABI distinta 0. `g5_capture` sigue
costando máximo 231 612 ciclos en YI1; esa parada pertenece a B2bis.

El log tiene **seis líneas `ok` G2T-B5** (PC y 68000 por traza), termina
en `OAM68K: OK` y restaura logicbench por defecto.

```text
Negativos B35: WAIT detectado (salida 1); color de pose 55 detectado (plan distinto)
```

Los negativos se regeneraron desde las entradas actuales. No se cambió
la referencia: alterar un WAIT falla la comparación de segmentos y
alterar el color de la pose elegida cambia los bytes del plan.

## 3. Coste antes y después

Fuente: `g5plan_verify.py plan`, **Musashi, sin DMA**, en las tres trazas
completas. Son ciclos del código, no una medida de fluidez en WinUAE.
Control anterior en `work/b35_before/`; resultado en `work/g2tb35/`.

| traza | media anterior | media actual | máximo anterior (frame) | máximo actual (frame) |
|---|---:|---:|---:|---:|
| yi1 | 1 550 708 | 1 029 485 | 2 814 672 (7515) | 2 395 526 (7515) |
| normal | 1 519 482 | 975 118 | 2 809 220 (2126) | 2 314 848 (2198) |
| spin_kill | 1 498 308 | 963 040 | 2 916 672 (2140) | 2 405 022 (2140) |

La media mejora aproximadamente **34–36 %**, y el máximo global baja
**17,5 %**. Sigue **300,6 veces** por encima de 8000. Se agotó el intento
permitido en C; no se hizo otra optimización ni una implementación asm.

### Segmentos realmente pedidos

Se cuentan los segmentos únicos del mapa de validez. Su coste individual
se mide en llamadas separadas, sobre las mismas filas, después de medir
el plan; esas llamadas de diagnóstico no inflan `g5_plan`.

| traza | segmentos/frame media | máximo (frame) | llamadas medidas | ciclos/segmento media | máximo (frame, fila) |
|---|---:|---:|---:|---:|---:|
| yi1 | 14,14 | 39 (6768) | 32 355 | 5474 | 10 626 (9679, 171) |
| normal | 13,99 | 39 (2170) | 9247 | 5233 | 12 260 (2647, 182) |
| spin_kill | 14,21 | 38 (2200) | 6465 | 4484 | 9440 (2316, 124) |

Incluso un solo segmento del C puede exceder los 8000 ciclos del plan
completo. La pereza está implementada, pero no resuelve por sí sola el
presupuesto.

### Perfil y propuesta de asm

`scratchpad/g5prof.py` no estaba disponible en este checkout. Se dejó
`tools/g5plan_prof.py`, basado en ejecución por instrucción de Musashi,
con JSON y ciclos propios por función; usa el build PROF. Se amplió la
extracción de `static` para incluir `s16` y `const g5_seg *`: sin eso,
los helpers quedaban atribuidos a la función anterior (P37).

En los peores frames actuales, `g5_attempt` consume **47,5–49,3 %** de
ciclos propios. Perfil del máximo global, frame 2140 (`work/b35_after/`):

| función | ciclos propios | % |
|---|---:|---:|
| g5_attempt | 1 142 032 | 47,5 |
| g5_a3 | 248 158 | 10,3 |
| g5_plan | 198 416 | 8,2 |
| g5_adv | 156 140 | 6,5 |
| g5_use | 131 690 | 5,5 |
| g5_schedule | 129 504 | 5,4 |
| g5_segment | 116 660 | 4,9 |
| g5_bits | 68 540 | 2,8 |
| g5_seg_of | 52 472 | 2,2 |
| g5_req | 40 856 | 1,7 |

Total PROF 2 405 052 ciclos; se observa una diferencia constante de 30
con el arnés de producción. Los 30 segmentos de ese frame cuestan de forma
inclusiva media 4319 / máximo 5550 ciclos: no sumar ese coste de nuevo
a los ciclos propios de sus helpers.

Orden propuesto: núcleo `g5_attempt`/`g5_use` con usos por índice y filas
ordenadas; A3/recorte (`g5_a3`, `g5_bits`); parser/calendario de segmentos
y helpers; serialización y búsqueda de forma. **Asm directo no basta**:
incluso una mejora global estimada de 5–10 veces dejaría 0,24–0,48
millones de ciclos. Ahorro hipotético 1,9–2,2 millones, sin garantía;
hace falta eliminar trabajo además de traducirlo. Las instrucciones de
la fase de viabilidad están en `docs/instrucciones-g2t-b35-asm.md`.

## 4. Memoria

Builds reales con `SPR_G5` y `SPR_BANK=work/g3/bank`, replay y vivo,
auditados con `memmap.py`; logs `work/b35_mem_replay/memmap.log` y
`work/b35_mem_live/memmap.log`. **Cero violaciones** en ambos.

| build | chip | slow | slow libre | libre con G5EV | libre con G5EV y g5_work |
|---|---:|---:|---:|---:|---:|
| replay | 472 112 | 297 040 | 227 248 | 94 208 | 64 256 |
| vivo | 483 640 | 333 272 | 191 016 | 57 976 | 28 024 |

`g5_work` mide **29 952 B**, offset de `nsegs` **29 950**; gcc lo
informa y el 68000 confirma el contador/mapa con ese layout.
G5EV y el área de trabajo **no están cargados todavía en el juego**:
las dos columnas de reservas son **estimaciones** sobre el mapa medido.
No incluyen fotos/salidas adicionales, caché B2bis ni margen de pila.
La integración deberá volver a sumar todas esas reservas.

## 5. Red de seguridad, hashes y evidencia

```text
RESULTADO: OK                       (lint_port.py)
===== G2T test_g5bank_env.py         (work/regress.log, ocho tests OK)
RESULTADO: OK                       (regress.py --baseline tools/baseline_pc.json --level)
OAM68K: OK                         (seis líneas ok G2T-B5)
```

No se cambiaron baselines. Los cuatro juegos por defecto y logicbench
se recompilaron antes y después; los cinco hashes permanecen idénticos:

```text
c03b569643c7bf5ac62f55cdd2813951a6895a6d4801d1eef241e96cfa422769  vivo
9403f71c76bc2df9a92a3cc24d8db1e9e67c47e5e62a558e441c3994d0538109  replay
2bc486d77af939aedfb183457e33cc41eba172521959bb0192ddbe6f594363bb  replay BENCH
71071566e75a0c1a9dd5391d8398fc44f69ace2e1a4dd489e936c5f7c8bbfad4  replay BENCH SPR_OAM
ec8147ac1989ab7e7714f1db3f3cebbc723730a980aa33158a6a41173e4dc37e  logicbench
```

Modelo regenerado: `PUERTA A-T: OK`; los tres planes y `bank.idx`/`dma`
mantienen los SHA256 de B35 §4. Se inspeccionó personalmente
`work/g2t_ref/muestras.png`: los recortes fuente/simulación coinciden,
sin píxeles magenta de error, incluidos solapes y bordes. Es evidencia
del modelo offline; **no** una captura nueva del juego en WinUAE.

No se hicieron Cpre, B2bis, asm ni una medida D1 integrada en esta
continuación. Los enemigos aún no se dibujan con este plan en el juego.
El siguiente trabajo y sus puertas quedan en `PROXIMO.md`.
