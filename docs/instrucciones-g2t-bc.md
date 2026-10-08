# G2T-B/C — el plan del Rex en C/68000 y en el copper del juego

2026-10-07. Instrucciones paso a paso para la sesión siguiente. Parte del
contrato **fijado** en `docs/instrucciones-g2t-a.md` §1-bis y de la puerta
A-T verde (`docs/informe-g2t-a-1007.md`). Sustituye a las fases B y C de
`docs/instrucciones-g5a-bis.md` (C2 «h ≤ $E2 − 8n» queda derogada: era
falsa, P111). Modelo previsto: GPT-6.1 Sol high, worktree propio
(`tools/wt_new.sh g2tbc`). Un Rex por frame (el de menor `sy+origen_y`),
como A-T; G4/G6 vienen después.

## 0. Por qué existe y qué no es

A-T demuestra offline, con 56 casos exactos y 27 negativos en WinUAE, que
un plan de recargas COLOR17-31 entre filas existe para los 3404 frames con
Rex. Falta que **el juego** lo calcule (B) y lo escriba en sus listas (C),
dentro del presupuesto. No es: ampliar a varios enemigos, tocar el banco
G3, cambiar el scroll, ni rebajar ninguna regla del contrato.

## 1. Reglas que no se negocian

1. Builds por defecto **idénticos byte a byte** (todo bajo `SPR_G5`,
   que implica `NOOAM SPR_OAM`). Bucle de hashes de
   `docs/instrucciones-g5a-bis.md` §6.1 antes de cada commit.
2. `tools/g2t_ref.py` es la especificación: el C/68000 la imita; nunca al
   revés. Si hay que cambiar el modelo, **parar** y pedir instrucciones.
3. Constantes del contrato tal cual: `END = 351 − 8·nb` (nb 7/8/9),
   `IDLE = 48`, `X_D0 = 263` con última carga ≤ 207, `K255 = 0`, bloque
   VBL en v = 30, paso 231 → 243, sufijo ≤ 9 ranuras.
4. Render sin RAM viva (P97): todo sale de la foto O5. Sin `int`/`long`
   a secas, sin `static` con dirección tomada (P47), tablas C en bloques
   `#ifdef` (P78); comprobar el listado por P102.
5. R9: derivados solo en `work/`. No push.

## 2. Entorno y partida en verde

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py                                          # RESULTADO: OK
python tools/regress.py --baseline tools/baseline_pc.json --level  # RESULTADO: OK
sh tools/oam68k_gate.sh                                            # OAM68K: OK
python tools/g2t_ref.py --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin --trace work/oam_normal.trace=work/oracle_normal_oam.bin --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin --bank work/g3/bank --out work/g2t_ref
# PUERTA A-T: OK; los contadores de informe-g2t-a-1007.md §6 iguales
```

`wt_new.sh` no copia `work/g3`: copiarlo, junto con las trazas
`oam_{yi1,normal,spin_kill}.trace`, sus `oracle_*_oam.bin`, `cc/gfx32.bin`,
`cc/mario_pal.bin` y `yi1_s.dat`. Si algo no da lo esperado: parar.

## 3. Fase B — el plan, igual en PC y en 68000

### B1. Volcado binario de referencia

Agregar a `g2t_ref.py` la opción `--dump` que escribe
`work/g2t_ref/plan_<traza>.bin`, big endian, por frame con Rex:
`frame u32`, `variante u16` (`$FFFF` sin plan), 4 × (`activo u8`, pad,
`pt u32`, `pos u16`, `ctl u16`), `nvbl u8` + `nvbl` × (`índice u8`,
`valor u16`), `nseg u8` + por segmento `fila u8`, `tipo u8` (1 = WAIT,
2 = cadena), `h u8`, `nop u8`, `k u8`, `k` × (`índice u8`, `valor u16`).
Segmentos en orden de fila; MOVE en el orden del plan. Prueba: el
volcado se relee y reproduce `plan_<traza>.json` (test nuevo en
`test_g2t_ref.py`, sin assets, con un plan sintético).

### B2. Envolvente de Mario desde la foto real

`g5_capture()` (C nuevo, `player/g5plan.c`, llamado en `dc_capture`
**después** de `mspr_draw`) decodifica las dos parejas del buffer de
Mario de esa foto (DATA/DATB, POS/CTL) y escribe, en un bloque slow por
foto: por fila R y por índice 1..15, primer y último x (224 × 15 × 2 B),
más `R_PAL`, cámara y la ranura/fichas del Rex elegido. **Puerta B2:**
en el modo `game` de `marioverify.c` (y en la grabación del juego), las
envolventes son iguales a las de `g2t_ref.mario_amiga` para todos los
frames con Rex de las tres trazas: 0 diferencias. Medir sus ciclos en
Musashi (máx. y media). **Si el máximo pasa de 3000 ciclos: parar y
avisar** (corre en la interrupción y se come lo de L-OAM).

### B3. `g5_plan()`

Función pura en `player/g5plan.c`: entrada = bloque de la foto, tablas G3
por su base (P102), segmentos de la lista que se escribe (nb del borrado
y x de la última carga, calculados del mismo modo que
`g2t_ref.segments`: `htab` inverso solo hasta $CE, paso 231 → 243);
salida = el plan de B1. Orden de colocación idéntico a `g2t_ref.place`
(ventana más corta, segmento más tardío primero) y `schedule` idéntico
(cadena solo tras una carga, WAIT con copper libre, regla de fin).

### B4. Puerta en el PC

Modo `g2t` en `tools/marioverify.c` (`GAME_G2T_TRACE=...`) que en cada
frame arma el bloque, llama `g5_plan()` y vuelca con el formato de B1.
`cmp` contra `work/g2t_ref/plan_<traza>.bin`: **idénticos** en las tres
trazas. Un fallo se diagnostica por frame/segmento; tres intentos
distintos sin cerrar → entregar parcial.

### B5. Puerta en el 68000

`CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' sh tools/logicbench_build.sh` y
`tools/g5plan_verify.py` (estructura de `sprite_oam_verify.py`): plan
byte a byte igual al del PC en todos los frames; ciclos de `g5_capture`
y `g5_plan` (media, máximo, frame del máximo). Agregarlo a
`tools/oam68k_gate.sh` y comprobar en `work/regress.log`/salida que corre.
Presupuesto: render G4/G5 ≤ 8 % del frame (11 350 ciclos) incluyendo
emisión; si `g5_plan` solo ya pasa, **parar** con cifras.

## 4. Fase C — el copper del juego

### C1. Segmento y bloque VBL (opt-in)

Con `SPR_G5`: `SEG` 220 → 256 en `player/scroll.s` **y** en
`tools/mkscroll.py` (`--g5` → `work/yi1_s_g5.dat`; `game_build.sh` lo usa
solo con `SPR_G5`); `CL_LINES` + 128 para el bloque VBL tras la cabecera
(WAIT (30,0), 16 MOVE SPR4-7, 15 ranuras de color, NOP de relleno).
`python tools/memmap.py` en replay y vivo: chip ≤ 524 288 (estimado
472 112 / 483 640). Builds por defecto idénticos.

### C2. `g5_emit`

Asm nuevo (`player/g5.s`), en el render después de `build_mid`, para la
lista que se escribe: por cada segmento con sufijo ahora o en el frame
anterior de **esa** lista, recorrer desde `ldoff` hasta el primer `$0084`
(o un MOVE `$1A2-$1BE`: `build_mid` nunca los escribe), escribir el
sufijo del plan y el salto de tres MOVE; sin sufijo, solo el salto. El
segmento 211 nunca lleva sufijo. Bloque VBL: siempre los 16 MOVE (canal
inactivo: POS/CTL = 0, PT al nulo) y los colores del plan; el resto NOP.

### C3. Puerta sobre las listas reales (sin la Amiga)

`tools/g2t_listcheck.py` (nuevo): corre el juego con `SPR_G5` en Musashi
(como `game_read.py`), lee cada lista que se muestra y aplica
`g2t_ref.check_list` + la regla de fin a los sufijos **emitidos**:
eventos de capa 1 iguales al build sin `SPR_G5`, posiciones re-derivadas
iguales al plan, 0 sufijos fuera de regla, 0 en el segmento 211.

### C4. Puerta en WinUAE, pantalla entera

≥ 12 frames del replay YI1 elegidos desde `work/g2t_ref/plan_yi1.json`:
f6150, solapes Mario/Rex (≥ 3), ambos sentidos, borde derecho, sufijo de
7 MOVE y una cadena tras carga en 231 (P75: `-DSTOPF` cuenta desde el
primer frame del replay). Por frame: build `-DSPR_G5 -DSTOPF=N` y control
`-DSPR_G5 -DG5_EMPTY -DSTOPF=N` (mismos segmentos, sin escrituras ni
armado). Capturas por el candado con `tools/shot.ps1 -Exact`. Esperado =
control con los píxeles del Rex del plan encima (Mario delante).
**0/57 344 píxeles distintos en cada frame** (P57, centro del píxel);
`work/g2tbc/compare_<N>.png`, miradas una por una.

### C5. Coste con control

`tools/stress_ab_build.sh` como modelo: YI1 y estrés, `SPR_G5` contra
`SPR_G5 -DG5_EMPTY` en la misma tanda: fotos omitidas, racha,
`level_frame`, `build_mid`, `g5_emit` y total. La compuerta D1 no se
rebaja; con L-OAM aún roja se informa, no se declara cerrada.

## 5. Paradas

- Cualquier cambio necesario en `g2t_ref.py`, en el contrato o en las
  constantes: parar y pedir instrucciones.
- B2 > 3000 ciclos; B5 > 8 % sin emitir; chip > límite: parar con cifras.
- Una captura C4 con un solo píxel distinto: parar, guardar la PNG y el
  plan del frame; no ajustar el comparador.
- Tres intentos distintos sin cerrar una puerta: entregar parcial (WIP).

## 6. Informe

Commits (hash de `git log`), salidas de B2/B4/B5/C3/C4/C5 con cifras y
fuente, las PNG miradas, `memmap` replay/vivo, hashes de los builds por
defecto, lo no hecho. Cierre según `ROADMAP.md` §7.
