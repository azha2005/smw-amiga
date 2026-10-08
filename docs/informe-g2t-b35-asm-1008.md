# G2T-B35-asm — primer microbenchmark y parada de integración

2026-10-08. Rama `g2t-b35`, partida `f3dd8cf`, implementación `a9b44fe`
(`WIP G2T-B35-asm: medir transiciones dispersas exactas; nucleo aun supera 8000 ciclos`). Se ejecutó la fase de
medida de `docs/instrucciones-g2t-b35-asm.md`, no una sustitución completa
del planificador. El C de producción queda intacto como control.

**Resultado:** el prototipo disperso produce las mismas transiciones
en los 3404 frames y respeta ABI/PIC, pero **solo ese núcleo** llega a
18 794 ciclos sin DMA, frente a 8000 para el plan entero. No hay una
ruta medida al presupuesto con esta propuesta. Se aplica §4.5 de la
tarjeta: entregar la prueba y detener la integración. No es una prueba
de imposibilidad de cualquier otro algoritmo exacto.

## 1. Qué se implementó

`player/g5trans68k.s`, únicamente con `SPR_G5` + `G5_TRANS_BENCH` y
ensamblado aislado: grupos de usos por índice, filas ordenadas, acceso
directo a fila/color/último x; produce los registros de transición
en el mismo orden del C. Conserva el último uso aunque no cambie el
color, crucial para el plazo de la transición siguiente. No ubica MOVE,
no sustituye `g5_attempt`, no se incluye en el juego.

`tools/g5plan_work.py`, `.c` y `.h`: instrumentan **una copia** de
`player/g5plan.c` en `work/`, con anclas únicas verificadas. El arnés B4
original comprueba segmentos y frontera, envenena/reutiliza el área de
trabajo y exige que el observador produzca B1 idéntico a `g2t_ref`.
Guarda entrada dispersa y todas las transiciones de cada intento;
Musashi compara sus campos definidos con el asm. El byte de padding
del C no forma parte de la comparación; el asm lo deja en cero.

Además de las trazas reales, prueba grupos vacíos, último uso sin cambio
de color, índice 15/fila 223/color $FFFF, capacidad exacta de 255,
desbordamiento, negativo de color, canarios y entrada inmutable.
Alterna **dos bases de código y de argumentos** y comprueba todos los
registros preservados, incluido a4. El sintético está en `regress.py`.

`g5plan_prof.py` informa ahora el tramo desde la primera entrada en
`g5_put16` hasta el RTS del plan: producción de B1, excluido el
preámbulo de esa primera llamada. No confundirlo con el emisor copper.

## 2. Trabajo real

Todos los valores de esta tabla son del observador del PC en las tres
trazas completas, `work/b35asm/work/stats_<traza>.csv`.

| trabajo/frame | yi1 media / máximo | normal media / máximo | spin_kill media / máximo |
|---|---:|---:|---:|
| variantes filtradas por A3 | 2,90 / 26 | 3,49 / 30 | 2,35 / 31 |
| intentos completos | 1 / 1 | 1 / 1 | 1 / 1 |
| usos (fila, índice) | 174,88 / 253 | 160,20 / 220 | 163,58 / 223 |
| transiciones | 20,60 / 76 | 19,70 / 79 | 20,07 / 80 |
| posiciones probadas | 20,61 / 76 | 19,70 / 79 | 20,08 / 80 |
| segmentos únicos | 14,14 / 39 | 13,99 / 39 | 14,21 / 38 |
| bytes B1 | 160 / 416 | 156,06 / 422 | 157,89 / 423 |

Conclusión concreta: **no hay repetición de intentos completos** en
estas trazas; lo repetido son filtros A3 y recorridos de usos. Casi
todas las transiciones se ubican en el primer segmento probado. Una
caché de intentos fallidos no ataca el problema medido aquí.

El contador de instrucciones del copper solo corre dentro de
`g5_plan`: excluye las 224 decodificaciones por frame que hace el
arnés B3 como verificación independiente.

## 3. Microbenchmark 68000

Musashi, M68000, sin DMA, VASM `-no-opt`. Ciclos incluyen entrada,
salida y preservación de registros; excluyen construir la entrada
dispersa (la prepara el PC), A3, calendario, segmentos y B1.

| traza | frames / intentos comprobados | transiciones distintas / ABI | media ciclos/frame | máximo (frame) | frames > 8000 |
|---|---:|---:|---:|---:|---:|
| yi1 | 2288 / 2288 | 0 / 0 | 11 788 | 18 794 (6782) | 1694 |
| normal | 661 / 661 | 0 / 0 | 10 960 | 17 396 (2198) | 494 |
| spin_kill | 455 / 455 | 0 / 0 | 11 163 | 17 396 (2212) | 347 |

Listado real: **37 instrucciones, 0 llamadas/saltos absolutos**.
No se sustituyó ninguna llamada del plan; el B5 completo conserva
sus costes anteriores (máximo 2 405 022), no los de esta tabla.

Representación propuesta: 15 cabeceras de 4 B y hasta 72 usos/índice
de 6 B, **6540 B de capacidad**, salida hasta 255 × 10 = **2550 B**.
Máximo de entrada en las trazas: 60 + 253 × 6 = **1578 B**;
máximo de salida: 80 × 10 = **800 B**. Ambos máximos pueden pertenecer
a frames distintos. Son tamaños medidos/derivados, no una reserva
añadida al juego; falta el calendario y el resto de sus buffers.

## 4. Presupuesto completo y memoria

Los perfiles del control se reprodujeron en los frames 7515/2198/2140.
El plan completo cuesta aproximadamente 2,40/2,31/2,41 M ciclos PROF;
en el último, `g5_attempt` tiene 1 142 032 ciclos propios, 47,5 %.
Incluso concederle coste cero a esa función dejaría **1 263 020 ciclos
del resto** en ese perfil. Es un presupuesto hipotético sobre el
control medido, no una medida de un build mixto ni una cota universal.

Partes reproducidas del control PROF, sin DMA:

| traza (frame) | plan completo | segmentos inclusivos, sumados | tramo B1 desde primera g5_put16 |
|---|---:|---:|---:|
| yi1 (7515) | 2 395 556 | 158 838 | 129 578 |
| normal (2198) | 2 314 878 | 154 760 | 132 662 |
| spin_kill (2140) | 2 405 052 | 129 570 | 139 548 |

La tabla de partes del perfil está en `work/b35asm/prof_<traza>.json`.
Los helpers llamados por el parser no se suman otra vez a su coste
inclusivo. El control también mide cada segmento con
`g5plan_verify.py plan`: hasta **12 260 ciclos** por segmento.
La primera sustitución, aun con entradas preparadas gratuitamente,
ya supera el presupuesto entero. Por eso no se continúa con una
traducción del resto ni se activa el plan en vivo.

Memmap recompilado, `SPR_G5` + banco G3, 0 violaciones:

| build | chip | slow | slow libre |
|---|---:|---:|---:|
| replay | 472 112 | 297 040 | 227 248 |
| vivo | 483 640 | 333 272 | 191 016 |

G5EV (133 040) + work del C (29 952) dejan **28 024 B estimados**
en vivo. La opción (a) de B2bis necesita al menos 2480 B de datos +
40 B de clave por entrada: N=8/16/32 son **20 160 / 40 320 / 80 640 B
estimados mínimos**, antes de metadatos. N=16/32 no entra junto a las
reservas actuales; N=8 deja como máximo 7864 B antes de fotos, salidas
y pila. No se eligió ni se cargó una caché. El prototipo aislado no
cambia estos mapas.

## 5. Reproducción y seguridad

En Git Bash, con el entorno de `docs/instrucciones-olas.md`:

```sh
python tools/g5plan_work.py collect
python tools/g5plan_work.py bench
# 3404 B1 idénticos, 3404 estructuras intermedias iguales, ABI 0
python tools/g5plan_work.py bench --synthetic-only --out work/g5trans_test
PROF=1 CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' sh tools/logicbench_build.sh
python tools/g5plan_prof.py --cap work/g5gate/cap_spin_kill.bin --segw work/g2tb35/segw_spin_kill.bin --frame 2140 --out work/b35asm/prof_spin_kill.json
```

`collect` requiere los insumos frescos de `oam68k_gate.sh` paso 4c;
no modifica ni el modelo, ni el banco ni el C control.

Lint y regress completo: **RESULTADO: OK**; sintético nuevo confirmado
en `work/b35asm/regress_full.log`. OAM68K: **OK**, seis líneas B5 y
0 planes distintos/ABI en 3404 frames. Segmentos: 0 distintos en
762 496 filas. A-T: **OK**. Los cinco hashes por defecto coinciden con
los de `docs/informe-g2t-b35-1008.md` §5; evidencia en `work/b35asm/`.
No se actualizó ninguna base. Negativos repetidos: WAIT detectado
(salida 1), color de pose 55 detectado (plan distinto), además del
negativo sintético nuevo.

No hay imagen nueva del juego ni medida nueva D1/WinUAE: esta tarjeta
es una prueba del núcleo de CPU. Los enemigos siguen sin dibujarse por
este plan en el juego. B2bis y Cpre solo se revisaron: no existen
entregas locales de esas tarjetas; sus implementaciones siguen pendientes.
Sin merge a master y sin push.
