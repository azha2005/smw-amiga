# Instrucciones de las olas que faltan (3 a 8)

Escrito el 2026-10-07. Semi-detallado: para cada tarjeta, qué hay que
lograr, en qué orden, con qué comandos se comprueba y dónde suele fallar.
Las fichas cortas de cada tarjeta siguen en `SUBAGENTES.md` §4; el estado,
en `ROADMAP.md` §1/§4; lo que se hace **ahora**, en `PROXIMO.md`. Las dos
tarjetas en curso tienen instrucciones paso a paso propias:
`docs/instrucciones-loam.md` y `docs/instrucciones-g5a-bis.md`.

---

## Parte 1 — Cómo se trabaja (vale para todas las olas)

### 1.1 Entorno de la PC (Windows)

Git Bash, siempre al principio:

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
```

- Sin `ucrt64` primero, gcc falla **sin mensaje** ("FALLO build PC").
- `python` tiene que ser el de WindowsApps (con `machine68k`, `unicorn`,
  `numpy`). `python3` es un stub roto.
- No hay FS-UAE: donde una tarjeta dice "capturas FS-UAE", se usa WinUAE
  cycle-exact por el candado (`tools/shot.ps1 -Exact`, o en paralelo con
  copias por slot como `tools/stress_ab_shots.ps1`).
- Detalle completo: `docs/reglas-ola-pc.md`.

### 1.2 La red de seguridad (antes de **cada** commit)

```sh
python tools/lint_port.py                                          # RESULTADO: OK
python tools/regress.py --baseline tools/baseline_pc.json --level  # RESULTADO: OK
sh tools/oam68k_gate.sh             # si tocaste algo con SPR_OAM: OAM68K: OK
```

Y si el cambio es opt-in (`ifd`, `#ifdef`): los binarios por defecto
**idénticos byte a byte** antes y después (`docs/instrucciones-g5a-bis.md`
§6.1 tiene el bucle de `sha256sum`). Es la prueba más barata y más fuerte
de que no rompiste nada.

### 1.3 Reglas para quien coordina (aprendidas a la mala, 2026-10-06)

1. **Repetir la puerta de cada tarjeta antes de integrarla.** No basta con
   leer el informe: correr los comandos y comparar los números.
2. Mirar las imágenes de evidencia uno mismo. Una "comparación exacta" de
   un solo frame no prueba que algo funcione en movimiento.
3. Toda afirmación del tipo "X entra en `regress.py`" se comprueba con
   `grep` en `work/regress.log`.
4. Hash de commit citado = `git log` real (no uno enmendado).
5. Al cerrar: nada sin commitear en master ni en los worktrees;
   `PROXIMO.md` reescrito según `ROADMAP.md` §7.
6. La compuerta D1 se mide con `tools/stress_ab_*` (fotos perdidas,
   racha) **contra un control**: cada medida nueva lleva la fila "sin el
   cambio" en la misma tanda.

### 1.4 Presupuesto de chip (el límite que ordena las olas)

Hoy: chip 455 728 B (replay) / 467 256 B (vivo) con el banco G3; límite
524 288 B. Lo que viene y ocupa chip: segmento de G5 (+14 336 B), segundo
PF1 de G7 (+59 136 B), muestras de audio (≤ 64 KB). **No entra todo** hasta
que C2/C4 saquen de la chip las ~135 KB de tablas de CPU. Por eso C2/C4
van antes que G7 y que el audio en la Amiga. Cada tarjeta que agregue
chip corre `python tools/memmap.py <game.lst>` en **replay y vivo**.

---

## Parte 2 — Ola 3 (lo que queda; 1 sesión)

| tarjeta | instrucciones | depende de |
|---|---|---|
| **L-OAM** | `docs/instrucciones-loam.md` (paso 1 hecho, `4b713c4`) | — |
| **G5a-bis** | `docs/instrucciones-g5a-bis.md` | L-OAM para medir el coste (la fase A-B no) |
| **A0** registro del DSP | abajo, ola 4 (adelantable) | — |
| **R7** contadores del HUD en el volcado | abajo | — |

**R7.** Qué: que los oráculos de `snesorc` vuelquen los contadores del HUD
(monedas, vidas, tiempo, puntos, estrellas, monedas de Yoshi) por frame,
para que H4 tenga contra qué comparar. Dónde: `tools/snesorc/orc.c`, el
formato del `.txt`/`.bin` y `tools/oracle2bin.py`. Puerta: regenerar
`oracle_yi1` y comprobar que **todo lo que ya existía sale idéntico**
(hash de los campos viejos) y que los contadores cambian donde deben
(moneda tomada → +1 en ese frame). Trampa: P68 (el oráculo se toma antes
del NMI).

---

## Parte 3 — Ola 4: motores y estructura (2-3 sesiones)

Se puede repartir así: **(a)** G4+G6 → G5+G9 (en serie, el centro);
**(b)** C2; **(c)** S8; **(d)** A0 → A2; **(e)** P7/P9/P10; **(f)** T1.

### G4 + G6 — varios enemigos y canales

- **Objetivo:** generalizar G5a-bis: todos los enemigos del lote G3 de la
  foto, a canales 4-7 (y 2-3 cuando Mario no los usa), con reuso por
  líneas según el protocolo **medido** de G0 (`docs/medida-g0.md`: PT en
  la línea anterior desde h=$80/$C0, POS/CTL desde h=$38 de VSTOP; nunca
  h=$D8). Lo que no entra va a una **cola de bobs explícita**, nunca se
  descarta ni parpadea.
- **Cómo:** extender el modelo `tools/g5ref.py` de G5a-bis (fase A) a N
  objetos primero, en Python, con las mismas puertas (todos los frames,
  cero errores de color, ventanas de escritura). Después el C (`g5_plan`)
  y el 68000, como en G5a-bis fase B. G6 es esa comprobación: `tools/
  sprcop_verify.py` reconstruye **cada píxel** desde el plan y lo compara
  con la OAM renderizada (G3a), contando objetos sin destino aparte.
- **Puerta:** las de G5a-bis A y B para todos los objetos del lote, y
  `sin_destino` = solo lo que va a bob, listado.
- **Trampas:** P100 (el Rex mide 20 px: dos columnas), P108 (banco
  inmutable), prioridad OAM entre enemigos (la SNES pinta la primera
  entrada opaca).

### G5 + G9 — en el copper, todos los enemigos

- **Objetivo:** el `g5_emit` de G5a-bis con el plan de G4 (varios bloques
  por línea, reuso de canales).
- **Cómo:** mismas reglas que G5a-bis fase C (bloque después de las
  cargas, capacidad por h, `scrollsim --g5k`). G9 = `tools/g5cmp.py`
  generalizado (todos los objetos) sobre ≥ 20 frames del replay, más los
  de los replays de estrés.
- **Puerta:** 0 px distintos en todas las capturas; A/B de coste.
  **Los enemigos se ven en la Amiga.**
- **Trampas:** P39, P42, P46, P51, P59 (copper); P57 (capturas ×2).

### C2 — enlazado absoluto con vlink

- **Objetivo:** el binario en direcciones fijas (chip y `$C00000`), sin
  la base calculada; desaparecen P36, P52 y P102.
- **Cómo:** 1) un script de enlazado (`tools/link.cmd` o similar) que pone
  código y datos de CPU en slow, lo del chipset en chip; 2) `game.s` sin
  `GETBASE` en lo que pase a absoluto (en un build opt-in primero);
  3) `m68kverify`, `gamecheck`, `abcheck`, `memmap` cargan en la dirección
  fija (eso es E3, misma tarjeta).
- **Puerta:** `regress.py --level` en verde con el binario enlazado;
  replay idéntico (capturas en 6 frames con `imgdiff.py`);
  `memmap.py` con las direcciones fijas sin violaciones.
- **Trampas:** P8 (la A501 puede no estar), P29 (slow no acelera), P36,
  P47. Pensar ya en §11.8 (otros niveles): región común y región por nivel.

### S8 — la cámara vertical de YI1

- **Objetivo:** que el fondo siga a `wm_Bg1VOfs` (P84: solo se mueve con
  `$13F1` ≠ 0). Hoy la Y está fija en 192.
- **Cómo:** `docs/plan-tecnico.md` §10.2b; ventana de datos extendida
  hacia arriba en `mkscroll.py`, punteros PF1/PF2 con `cam_y - 192`,
  segmentos del copper indexados por línea del nivel.
- **Puerta:** capturas del replay de `oracle_normal` en los frames
  2672-2707 (cámara en `$BC`) iguales a lo esperado; `scroll_check.py`
  con `cam_y ≠ 192`; `scrollsim.py` todo el recorrido en 0 px.
- **Trampas:** P77, P84; afecta a G5 (las líneas de pantalla de los
  sprites dependen de la cámara: rehacer la puerta C4 de G5a-bis).

### A0 → A2 — la referencia de audio y el formato

- **A0:** `snesorc --dsp X.txt` registra cada escritura al DSP con frame y
  tick; `tools/dsplog.py` lo convierte en notas por voz. Puerta: el
  oráculo `.txt` **idéntico** con y sin `--dsp`; las notas del tema de YI1
  se repiten en el bucle; los saltos de Mario aparecen como efectos en los
  frames en que cambia `$1DFA`.
- **A2 (informe, sin código del juego):** qué tiene `sound/` del fuente y
  `smw_spc_player.c` de snesrev; qué 3 voces quedan (D5) **medido sobre
  el registro de A0** (notas perdidas por cada elección). Trampas: P104-P106
  (BRR).

### P7 / P9 / P10 — lógica que falta

- P7 bolas de fuego, P9 monedas de Yoshi y puntos, P10 la reserva.
- **Cómo:** como los sprites ya portados (`player/spr_*.c`, I1); la
  verdad son las grabaciones (`pw_flor`, `pw_yoshicoin`...).
- **Puerta:** `marioverify <oráculo> game` sin resincronizaciones en las
  grabaciones de cada una, y PC = 68000 en `regress.py`. Si la rutina
  escribe la OAM, también `oam68k_gate.sh` (agregar su oráculo).
- **Trampas:** P34, P35, P65, P66, P78.

### T1 — la zona de la tubería convertida

- `obj-1.lv`, tileset 3. **Puerta:** `m16diff` contra la referencia de la
  zona y `render_d` 0 px. **Trampas:** P11, P15-P18, P28 (Map16).

---

## Parte 4 — Ola 5: integraciones y 50 Hz con sprites (2-3 sesiones)

Orden: **C3/C4 → (PF1 doble + G7) y (A3/A4)**; **S5** en paralelo desde
el principio; H2-H4 en paralelo.

### S5 (+ S3/S6) — el pico de `build_mid`

- **Dato de partida:** sin OAM ampliada, `stress_back` pierde 3,51 % de
  las fotos por `build_mid` en la vuelta (165 % de un frame en s = 4606,
  `docs/medida-d1-winuae.md`).
- **Objetivo:** repartir el trabajo de `build_mid` entre frames con un
  tope de ciclos (cola por plazo, EDF); cargas muertas neutralizadas en
  el sitio (`MOVE $1FE`).
- **Ojo:** la ficha de S5 en `SUBAGENTES.md` depende de S4 (editar las
  listas en el sitio), pero **S4 se descartó** (P89: en el 68000 no
  conviene). S5 se plantea sin S4, o se justifica con una medida nueva por
  qué ahora sí; leer P89 antes de decidir.
- **Puerta:** `scrollsim.py --ret` ≤ base e ida = vuelta; 0 px en todo el
  recorrido; `tools/stress_ab_*` con G5 encima: fotos perdidas ≤ 0,1 %,
  racha 1 en estrés. **Esta es la compuerta D1.**
- **Trampas:** P43-P46, P50, P51, P59, P71, P72.

### C3 / C4 / C5 — compresión y loader

- **C3:** `tools/lzpack.py` + `player/unlz.s`; ida y vuelta en Unicorn
  sobre `yi1_s.dat` y el binario; ciclos por KB en Musashi.
- **C4:** `player/loader.s` recorre una tabla de carga (con C2), comprueba
  `$C00000` (P8), descomprime, salta. **Integrar el banco G3 en esa
  tabla** (hoy lo carga `sprbank.s` aparte). Puerta: el ADF arranca en
  WinUAE KS 1.2 y el replay coincide (capturas); `memmap.py` muestra la
  chip liberada.
- **C5:** tiempo de carga con y sin compresión, en WinUAE (no Unicorn).

### Segundo PF1 + G7 — bobs

- **Objetivo:** el Banzai (siempre bob) y la cola de bobs de G4, en un PF1
  doble (+59 136 B chip: **solo después de C2/C4**).
- **Cómo:** `docs/diseno-9.2.md` §4: restaurar desde BLK/mapa en el PF1
  libre, las dos copias del buffer circular, publicar O5 después del
  último blit. PF1 tiene **7 índices**: el color de cada bob se resuelve
  con el terreno; si no hay color exacto, **mostrar el caso al usuario**
  (no aproximar por cuenta propia).
- **Puerta:** capturas del replay con el Banzai comparadas como G9; A/B.
- **Trampas:** P2, P31, P97; E03, E04, E06 de `docs/investigacion-ports.md`.

### H2 / H3 / H4 — el HUD

- **H2:** `tools/mkhud.py`, capa 3 a 2 bpp → bitmap PF1 + paleta; PNG
  mirado y autoprueba.
- **H3:** overlay por copper en las líneas del HUD (`docs/medida-hud.md`).
- **H4:** `player/mhud.c` + `marioverify hud` contra los contadores de R7,
  todos los frames.
- **Trampas:** P14 (paletas), la banda del HUD cruza la capa 1 (H1).

### A3 / A4 — música

- **A3:** `tools/nspc2ev.py`; `tools/audiocmp.py` contra el registro de
  A0 nota por nota (N/N, inicio ±1 tick, tono ±5 cents, volumen ±1 dB);
  informe `docs/audio/yi1.md`.
- **A4:** `player/audio.s`, tick por timer de CIA (**auditar qué timer
  usa cada cosa**: BENCH usa CIA-B A, D1TIMER CIA-B B), sin mezcla.
  Puerta: estado de Paula por tick en Musashi = render offline; suena.
- **Trampas:** P7 (PCM con signo), P104-P106; ≤ 64 KB de muestras en chip.

---

## Parte 5 — Ola 6: el juego completo (2 sesiones)

| tarjeta | qué | puerta |
|---|---|---|
| **Z2** punto medio | poste, estado guardado, reaparecer | grabación de R5 (`pw_medio`) sin resincronizar |
| **Z3** meta | la secuencia entera | `oracle_goal` hasta el final |
| **Z4** tiempo agotado | guion que espera | grabación nueva |
| **Z5** fundidos | por copper, entrar y salir | captura |
| **Z6** Mario detrás del poste | prioridad sprite / capa 1 (BPLCON2 por línea) | captura en la meta |
| **T2** lógica de la tubería | entrar, subzona, volver | `marioverify <oracle_pipe> game` sin resincronizar |
| **T3** tubería en la Amiga | fundido, punteros, paleta, cámara | capturas dentro de la zona |
| **A5** efectos | `wm_SoundCh1/2/3` con prioridad sobre la voz que comparte canal | registro A0 |
| **A6/A8** comparación | Paula por tick contra A0, 60→50 Hz (D15); un informe por tema | `audiocmp.py` |
| **H5** HUD barato | blitear solo lo que cambia | ≤ 2 % (BENCH) |

Trampas comunes: P58 (lo no portado congela el juego y lo explica en el
diagnóstico: usarlo), P65, Z1 (`docs/validacion-z1.md`) como modelo de
cómo se valida una secuencia.

---

## Parte 6 — Ola 7: segunda ronda de 50 Hz (1 sesión)

Todo junto (sprites, bobs, HUD, audio) contra la compuerta D1:

1. `tools/stress_ab_build.sh` ampliado con las variantes que existan
   (escenarios `back`, `sprites`, `vert`, `piranha` y `yi1`).
2. Capturas y lectura con `stress_ab_shots.ps1` / `stress_ab_read.sh`.
3. Si no pasa: perfil (`m68kprof.py --oracle ... --worst`), el peor frame
   por parte (BENCH) y la traza D1 v2 (`docs/medida-d1-winuae.md`) para
   ver **qué** se come el frame. Cada optimización con su A/B.
4. Si agotada la optimización no entra: **llevarle los números al
   usuario** (D1: 25 Hz solo con su decisión, `ROADMAP.md` §2).

---

## Parte 7 — Ola 8: cierre (1 sesión)

- **Z8:** el replay completo hasta la meta como prueba de `regress.py`:
  llega a la meta en el mismo frame que el oráculo.
- **Z7 / U1-U4 (usuario):** el ADF final en WinUAE KS 1.2 y 1.3 (y A500
  real si quiere); jugarlo con teclado.
- Limpieza de deuda: E1, E2 (`scrollsim` comprueba que la lista termina
  donde debe, P59), docs archivados, `PROXIMO.md` final.
