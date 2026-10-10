# G5L-R-S10 — prototipo de speedcode: puerta de tamaño/coste no cumplida

2026-10-10. Rama `g2t-b2bis`, worktree `wt-g2t-b2bis-1008`, sobre la
corrección de P123. **Nada integrado en el juego**; el binario y los
hashes del control no cambian. Tarjeta: `instrucciones-g5l-r-s10.md`.

## 1. Partida

Lint y `regress.py --baseline tools/baseline_pc.json --level --g5l --bm1`:
**OK**. Control `stress_back` (`GDEFS='-DREPLAY'`, `work/s10/control_back`):
`DC LOOP: OK`, `G5L GAME (pcprof): OK` en 4.127 fotos. El perfil de las
diez fotos (`work/s10/control_pc.json`) da **804.730 ciclos** de
`build_mid`, idéntico al de `informe-p123-scroll-1010.md` (mismo binario).

## 2. Dónde está el coste de `build_mid` (Musashi, 10 fotos)

Agrupado por líneas de `scroll.s` (`work/s10/bmleft_prof.txt`):

| tramo | ciclos | % |
|---|---:|---:|
| `bm_left`: grupos, `.pl`, `.prw` | 98.586 | 12,3 |
| `bm_left`: buscar lo/hi, pista | 91.718 | 11,4 |
| `bm_left`: base s0, `.ex`, `.b` | 131.716 | 16,4 |
| **`bm_left`: bucle por carga `.ch`..`.k2`** | **245.324** | **30,5** |
| `bm_left`: cierre `.c2`..`.jump`..`.j2` | 105.668 | 13,1 |
| `bm_left`: tardes `.td` | 30.692 | 3,8 |
| `bm_share` | 60.484 | 7,5 |
| `build_mid` (ida) y resto | 40.542 | 5,0 |

404 líneas reescritas, 1.863 cargas no tarde (548 con WAIT, 89
rellenos) y 151 tarde: **unas 4,6 cargas por línea**. El trabajo
fijo por línea (≈ 1.060 ciclos) pesa más que la copia de las cargas.

## 3. Prototipo (`tools/s10_speedcode.py`)

Genera, desde la MLD real (`work/yi1_s.dat`), un cuerpo por línea con las
constantes del plan como inmediatos: WAIT (`move.b x(a2),d7` + dos
`move.w`), rellenos, `move.l #reg:color,(a3)+` y la agregación vl/vu con
`cmp.w #a/#b` + `bcc.s` + `move.w`. Entrada: quien llama escribe el WAIT
de la primera y salta al `move.l` de lo (puntero P_j, +4 B por registro
de la MLD). Salida: RTS parcheado al principio de hi y restaurado. Las
tardes (28 de 224 líneas tienen alguna) y el codo de P51 siguen por el
bucle actual: no se cuentan contra el prototipo.

**Tamaño real (vasm -Fbin):** 103.056 B de código + 15.424 B de
punteros = **118.480 B**. Cargas 3.409, clases 0/1/2/3 =
1.226/1.951/148/50, tardes 34.

**Ciclos** (tabla de tiempos del 68000 sobre los conteos medidos del
perfil, saltos de vl/vu con sus resultados reales): cuerpo 137.736 +
entrada/salida 58.176 (144 por línea) = 195.912 contra 246.054 del bucle
actual. **Ahorro: 50.142 ciclos = 6,2 % de `build_mid`.** Cota con
entrada/salida gratis: 13,5 %.

Variante calculada (no generada): agregación vl/vu por tabla dispersa
(niveles 1/2/4/8, 16 B por carga, ≈ 60 ciclos por consulta). Ahorro
estimado con el mismo modelo ≈ 12,7 %, a cambio de ≈ 106 KB. Compartir
cuerpos entre líneas no sirve: cada WAIT lleva su x y cada carga su color.

## 4. Puerta (paso 2) y decisión

| condición | resultado |
|---|---|
| cabe en el vivo BM1 (61.288 B de slow libres) | **no**: 118.480 B |
| cabe en BENCH back (125.296 B) | por 6,8 KB, sin reservas |
| ahorro en las fotos caras | 6,2 % de la CPU de `build_mid` (Musashi) |

**No pasa.** Además está la cota estructural: aunque el speedcode fuera
gratis, el bucle por carga es el **30,6 %** de `build_mid`. En WinUAE,
el máximo de `build_mid` en back es **180,4 % del frame**
(informe P123 §4), frente a 92.078 ciclos en Musashi (65 % de un frame
de 141.875). Son máximos que pueden ser de fotos distintas, así que es un
orden de magnitud y no una medida por foto: **≈ 2,8× más lento en el
hardware**. Lo más probable es que domine la
contención del bus (código y datos en la slow de la A501, que comparte el
bus, P29; 6 planos y el copper en las líneas visibles) y/o la espera
del blitter, que Musashi no modela. Ningún recorte de instrucciones del
bucle cierra esa distancia. Por eso no se gastan otros dos intentos de
speedcode a ciegas: la regla de paradas pide cerrar con números y una
tarjeta de medida.

## 5. Lo que sigue

Tarjeta de medida **G5L-R-M1** (`instrucciones-g5l-r-m1.md`): en
cycle-exact, medir en las fotos caras de back cuánto de `build_mid` es
CPU pura, contención por línea visible y espera del blitter, y en qué
líneas de pantalla corre. Con eso se elige entre mover trabajo a las
líneas sin DMA de planos, reducir accesos a memoria por línea o
copper→blitter. L3 (lógica) puede ir en paralelo; no depende de S10.

Ficheros: `tools/s10_speedcode.py` (versionado); `work/s10/sc/sc.s`,
`sc.bin`, `control_pc.json`, `bmleft_prof.txt`, `partida.log`
(derivados, no versionados, R9).
