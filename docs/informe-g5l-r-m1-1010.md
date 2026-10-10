# G5L-R-M1 — por qué `build_mid` cuesta ≈ 2,8× en el hardware

2026-10-10. Rama `g2t-b2bis`. **Solo medida**; los flags nuevos son
opt-in y sin ellos el binario no cambia. Tarjeta:
`instrucciones-g5l-r-m1.md`.

## 1. Herramientas nuevas

- `-DM1POS` (`game.s`, requiere BENCH + DECOUPLE): por cada foto dibujada,
  una fila de 16 B en `m1_buf` (al final del binario, 4.400 filas):
  R_FRAME, s, lista, ticks de `build_mid` con la interrupción, ticks de la
  interrupción, líneas de pantalla al entrar y al salir. Mide desde dentro
  de `m1_pre`/`m1_post`, sin el coste de los sellos.
- `-DM1NOBPL`: apaga BPLEN durante `build_mid` (la imagen no vale).
- `tools/m1_read.py`: lanza la medida con el candado y `shot.ps1 -Exact`,
  encuentra el PID nuevo de WinUAE y vuelca el anillo cuando deja de crecer.
- `g5l.py game --render-list`: Musashi dibuja **solo las fotos que dibujó
  la Amiga** y guarda R_FRAME, s y ciclos de cada una.

**Sin flags, idéntico byte a byte** a lo construido con el `game.s` de HEAD
(`cmp`): replay YI1, BENCH back, vivo por defecto y BENCH YI1. PIC 0
absolutos y memmap 0 violaciones en la build M1POS.

## 2. Pares por foto (stress_back, WinUAE cycle-exact)

| corrida | fotos dibujadas | perdidas (BENCH) | `build_mid` máx. | ratio WinUAE/Musashi, fotos > 20 k ciclos (mediana) | suma |
|---|---:|---:|---:|---:|---:|
| control (informe P123) | — | 387, racha 5 | 180,4 % | — | — |
| M1POS | 3.718 | 408, racha 4 | 179,2 % | **1,60** (8 peores: 1,70-1,75) | 1,60 |
| M1POS + M1NOBPL | 3.873 | 253, racha 3 | 98,8 % | **1,07** | 1,09 |

Coincide la s de cada foto en los dos lados (3.718/3.718 y 3.873/3.873),
`G5L GAME: OK` con listas exactas. La instrumentación agrega unas 21
fotos perdidas (408 contra 387): sirve para repartir, no como control
nuevo. 1 tick = 1,41 µs ≈ 10 ciclos.

Fuentes: `work/m1/pos_back.json`, `nobpl_back.json`, `pair_pc.json`,
`pair_nobpl.json`, `*_bench.log`, `work/m1/pair.py`.

## 3. Reparto del ≈ 2,8×

1. **Fotos omitidas, ≈ 1,6×.** Con la secuencia real de la Amiga, el
   máximo de Musashi pasa de 92.078 (todas las fotos) a **146.860**
   ciclos. `--render-every 2/3` da 118.740/131.868.
2. **DMA de los 6 planos, ≈ 1,6×** (1,73 / 1,07). Sin planos, el
   hardware queda a 1,06-1,09 de Musashi.
3. **Copper, slow de la A501 y blitter juntos: ≈ 6-9 %.** Por eso no se
   construyó `-DM1BW`: lo que queda no justifica aislar el blitter.

## 4. Mecanismo de los picos: una espiral a la izquierda

Cada lista (son 3 con el colchón) se reescribe 3 fotos o más después de
la anterior. Si |Δs| desde **su** última escritura pasa de 16, `build_mid`
recorre todas las líneas (`alllines`):

| \|Δs\| misma lista | fotos | ticks medios | máx. |
|---|---:|---:|---:|
| 0 | 489 | 58 | 91 |
| 1-8 | 1.948 | 1.545 | 14.073 |
| 9-16 | 1.192 | 1.534 | 12.948 |
| **> 16** | **86** | **10.386** | **25.365** |

Entre fotos seguidas, Δs > 16 solo pasa 2 veces. En la vuelta
(frames 2.560-2.598), con la cámara a ≈ 4 px/frame, el Δs de cada lista
crece −12, −17, −21 … −48: cada reconstrucción tarda 2-4 frames, se
omiten fotos y la siguiente es más cara. Sin espiral, esas fotos cuestan
60-92 k ciclos en Musashi (≈ 0,7-1,1 frame con el 1,6× de los planos);
con ella llegan a 2,5 frames. Sin planos hay 45 fotos con Δs > 16 en vez
de 86.

Las reconstrucciones arrancan sobre todo en las líneas 32-128 y las
grandes duran varios frames: moverlas al borde no alcanza.

## 5. Propuesta (no implementada)

**G5L-R-S11: cortar la espiral de la vuelta**, sin cambiar la imagen:

1. Que una lista con |Δs| > 16 no pague el camino de todas las líneas:
   partir de la última lista escrita (`prevlt`, Δs de una foto) en vez de
   su propio estado, o ampliar la ventana de LNS a ±48 px (medir memoria).
2. Bajar el trabajo fijo por línea de `bm_left` (≈ 53 % del coste, informe
   S10 §2), que paga cada línea reescrita.

Cada ciclo de CPU que se ahorra vale doble: el 1,6× de los planos lo
multiplica y menos fotos omitidas bajan el Δs. Puerta: fotos con Δs > 16
y el máximo de `build_mid` en el A/B WinUAE, además de las de siempre.

**Decisión del usuario (no se toma acá):** con 5 planos (PF2 de 2) el
1,6× de los planos casi desaparece (R5: 5 planos lowres no roban ciclos
apreciables), pero cambia D8 y la fidelidad del fondo. Solo se registra
como dato.
