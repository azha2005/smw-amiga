# ROADMAP.md — Estado, presupuesto y decisiones del port-demo SMW → Amiga 500

> **Qué es este fichero.** El estado del proyecto (qué está hecho, con qué
> números), el presupuesto del frame, las decisiones y las olas que faltan.
> **Qué se hace a continuación no está acá: está en `PROXIMO.md`**, el único
> lugar que lo dice. `AGENTS.md` sigue siendo el contrato (reglas duras,
> formatos, pitfalls); si algo de acá contradice `AGENTS.md` §2, manda
> `AGENTS.md`.
>
> Reorganizado el 2026-10-05: el ROADMAP anterior está textual en
> `docs/archivo/roadmap-2026-10-05.md`; sus §9-§11 (optimización, lo que
> falta y cómo, más allá de YI1) viven en `docs/plan-tecnico.md` con los
> mismos números. §2, §3 y §8 conservan su número.

---

## 0. Mapa de los documentos y cómo usarlos

| pregunta | dónde |
|---|---|
| ¿Qué hago ahora? | **`PROXIMO.md`** |
| ¿Qué está hecho y con qué números? | este fichero, §1 (etapas) y §2 (frame) |
| ¿Qué tarjetas hay y en qué estado está cada una? | `SUBAGENTES.md` §4 (tabla de estado al principio) |
| ¿Cuántas sesiones faltan? | este fichero, §4 |
| ¿Cómo se hace X (técnica, diseño, plan detallado)? | `docs/plan-tecnico.md` y los documentos de diseño de `docs/README.md` |
| Reglas duras, convenciones, pitfalls | `AGENTS.md` (texto de las trampas en `docs/pitfalls.md`) |
| ¿Por qué se decidió algo así? | §3, `docs/decisiones-medidas.md`, `docs/archivo/` |

1. Leer `PROXIMO.md`, después §1-§2 de este fichero, después la tarjeta en
   `SUBAGENTES.md` y `AGENTS.md` §2, §7, §8 y §11.
2. Trabajar **un paso por vez**; no se empieza el siguiente con el anterior
   en rojo. Commit `Etapa N.x: <qué>`. Trampa nueva: `Pnn` en
   `docs/pitfalls.md` y en el índice de `AGENTS.md` §8 (la próxima es
   **P110**).
3. **Al cerrar la sesión: §7** (obligatorio: reescribir `PROXIMO.md`).

**Reglas del proceso (no negociables, vienen de lo que ya costó caro):**

| # | Regla | Por qué |
|---|---|---|
| V1 | Todo cambio en `player/*.c` se verifica con `marioverify` (C del PC) **y** con `m68kverify` (binario 68000 de vbcc): `tools/regress.py` hace las dos cosas y compara con la base (`tools/baseline.json` en cloud, `tools/baseline_pc.json` en la PC). Ninguna métrica puede empeorar | P38: vbcc compiló mal código que gcc compilaba bien |
| V2 | Los tiempos solo valen en cycle-exact: `tools/fsuae_shot.sh` en cloud, `tools/shot.ps1 -Exact` en la PC. Musashi (`m68kverify --engine musashi`) es una **cota inferior** porque no tiene esperas de DMA | P30; Musashi daba 24 % y la Amiga 34 % |
| V3 | Toda imagen se compara contra el esperado del PC (`scroll_check.py`) y, en la PC, contra `SuperMarioWorldMap02.png`. **Primero lo que se nota a simple vista**, criterio del usuario | la captura de FS-UAE está reescalada ×2,125 y ensucia los bordes |
| V4 | Nada derivado de la ROM entra en git (R9). Las grabaciones del oráculo sí (`work/oracle_*.txt`, `work/oam_*.txt`) | `.gitignore` |
| V5 | Las decisiones marcadas **[usuario]** no las toma el agente: prepara los datos, recomienda y pregunta | D8 y D1 se cerraron así |
| V6 | Antes de pedirle al usuario que juegue para grabar, **probar el grabador** (`oamrec.py --test 10`). Desde el 2026-09-30 casi todo se graba sin usuario con snesorc | límites del puerto Lua: 1024 caracteres por valor, 16 valores por respuesta, una sola conexión TCP |
| V7 | Antes de cada commit: `tools/lint_port.py` y `tools/regress.py` en verde. Una optimización, además, `tools/abcheck.py` (semántica IGUAL, ciclos menores). Detalle en §8 | que el siguiente agente no herede un rojo que no se ve |

---

## 1. Estado por etapa (al 2026-10-08)

Cifras medidas, con su fuente. Lo que no dice emulador es del PC o de
Musashi. Los números de regresión completos están en
`tools/baseline_pc.json` (PC) y `tools/baseline.json` (cloud); no se
copian acá.

| Etapa | Qué | Estado | Dónde está |
|---|---|---|---|
| 1-2b | Assets, paletas, nivel, capa 1 1:1 | **hecho** (6111/6111 bloques) | `tools/smw2amiga.py`, `palette.py`, `mklvl.py`, `m16diff.py` |
| 3-4 | Esqueleto Amiga y viabilidad | **hecho**; D1, D8 y D9 cerrados | `player/boot.s`, `bench*.s`, `copbench.s` |
| 5 | Conversor del nivel al formato (d) | **hecho**; falta compararlo contra la referencia en la PC (→ 7) | `tools/mkbg.py`, `mkd8in.py`, `mkleveld.py`, `render_d.py` |
| 6.1-6.3 | Scroll a 256 px, ida y vuelta | **hecho** (P59 arreglada) | `player/scroll.s`, `tools/mkscroll.py` |
| 6.4 | Scroll en el peor frame | **NO hecha**. S1a+S2 y SX/SX2 integradas; S4 descartada (P89); P51 arreglada (+6,7 % en `build_mid`). `build_mid` máx. **89,16 %** en WinUAE (ida, replay YI1, s ≈ 4576; `docs/medida-oam-o5.md`). Vuelta solo en Musashi (94,8 % en s = 2832, ×~1,3 en la Amiga). Falta S5 (EDF), S3/S6 y S8 (cámara vertical) | `player/scroll.s`; `docs/validacion-sx.md` |
| 7 | Capa 2 contra la referencia | pendiente (solo PC, U2) | — |
| 8a/8b/8c | Física, colisión, pendientes | **hecho**: `full` 6510/6547 en `oracle_yi1`; pendientes 2154/2154 (`oracle_hills`) | `player/mario.c`, `mcoll.c`, `manim.c` |
| 8 (gfx, cámara) | Gráficos de Mario y cámara | **hecho**; `gfx` 100 % en los oráculos (P69 arreglada) | `player/mgfx.c`, `mcam.c` |
| 8.1 | Grabaciones | **32 oráculos** con snesorc sin usuario (`tools/snesorc/*.orc`), entre ellos `stress_back`, `stress_sprites`, `stress_vert`, `pipe`, `goal`/`goal_low`/`goal_miss`, `pw_*` (seta, flor, estrella, 1-UP, `$C7`, bloques, medio, monedas de Yoshi) y los de R10. Faltan: luna 3-UP, R7 (contadores del HUD), R8/A0 (audio) | `tools/snesorc/`, `work/oracle_*.txt` |
| 8.2 | Lógica ≤ 40 % | **hecha para el alcance anterior; L-OAM no cerrada**. Ambas rutinas en asm (`e8ec165`, `bbdf201`, `cd5001c`, fusión `cb8ba8f`), RAM PC=68000 exacta. WinUAE l4: YI1 con `SPR_OAM` **41,2 %** (antes 43,1 %), back 73,9 %; fotos back 295 contra 145 del control, sprites 32 contra 0. Parada explícita tras ambas asm; nueva tarjeta pendiente | `player/logic68k.s`; `docs/informe-loam-1007.md`, `docs/informe-coordinacion-1007.md` |
| 9.1 | Sprites: lógica | **casi hecha**: Rex, `$83`, `$B9`, `$BD`, `$02`, `$9F`, `$4F`, `$8E`, `$C7`, Chuck `$95`, caparazones, meta `$7B`, power-ups (P6), Mario crecer/encoger/morir/estrella (P8); `game` 0 resincronizaciones. Faltan P7 (bolas de fuego), P9 (monedas de Yoshi, puntos), P10 (reserva) | `player/msprite.c`, `spr_*.c` |
| 9.2 | Sprites: dibujo | Mario hecho; G0/G1/G3a/G8 y G8b opt-in verificadas. G3 acotada hecha (64528 B DMA, 72724 B tablas, loader replay/vivo). G5a fallida y revertida (`652b23c`). **G5a-bis parcial en rama** `8fe712d`: A2 y variantes exactas; 59318 ventanas vacías + 18 fallos de capacidad, B/C detenidas. Coordinador reproduce el resumen y revisa las PNG. G2T revisión entregada. **G2T-A hecha (2026-10-07): contrato fijado con medidas y puerta A-T verde** en 3404 frames (0 sin plazo, 0 errores de color/capa 1/prioridad; 69 293 transiciones; 56 casos exactos + 27 negativos en WinUAE). El candidato era inviable: el hueco entre filas admite 12 − nb MOVE (P111); codo 231→243 (P110). **B35 parcial en rama `g2t-b35` (2026-10-08, `213ba3c`/`06e777f`)**: B4/B5 exactas en 3404 frames, ABI intacta, paso 4c/regress/hashes verdes; único intento en C agotado, máximo 2 405 022 ciclos sin DMA frente a 8000. No integrada; informe `docs/informe-g2t-b35-1008.md`. Primer microbench B35-asm entregado (`a9b44fe`): transiciones exactas en 3404 frames, máximo 18 794 ciclos solo en ese núcleo; no hay ruta medida al presupuesto, integración detenida (`docs/informe-g2t-b35-asm-1008.md`). B2bis, C y un nuevo diseño viable del plan, más cobertura global/G4-G7/G9, pendientes. **Los enemigos todavía no se ven en la Amiga** | `docs/informe-g3-final.md`, `docs/informe-g5bis-1007.md`, `docs/informe-coordinacion-1007.md`, `docs/informe-g2t-1007.md`, `docs/informe-g2t-a-1007.md` |
| 6b | Integración | ADF en vivo y replay, O5 por defecto y diagnóstico. Con banco G3 y L-OAM asm, memmap replay/vivo: chip 455728/467256 B, slow 287712/323944 B; 0 violaciones. Gamecheck replay integrado 6313 frames, 0 distintos; Mario 6184/6184. Falta vlink C2, compresión C3 y loader C4 | `player/game.s`; `docs/informe-coordinacion-1007.md` |
| 10-12 | HUD, audio, pulido | **Z1** hecho (muerte normal y reinicio; `docs/validacion-z1.md`). **H1** medido conservadoramente (`docs/medida-hud.md`; falta la alineación exacta PPU). **A1**: conversor verificado, 20 muestras / 50560 B PCM (`docs/informe-a1.md`); audio reproducido y R8 pendientes. HUD visible, punto medio, meta, game over: pendientes | — |
| Experimental E11-E14 | Técnicas de juegos de referencia | E11a hecha: 0 cargas PF1 en franjas aptas de 15.755 frames; E11b descartada para `build_mid`. E12 descartada: 0/7 índices sin conflicto en 1.016.785 cámaras. E13 sin caso. E14a hecha; E14 descartada para estrés: 0/202 frames con las 64 filas libres (Banzai solo: 16/331). No cambia el presupuesto ni la compuerta D1 | `docs/experimentos-e11-e14.md` |

---

## 2. El presupuesto del frame y la compuerta D1

Un frame PAL son 20 ms, ~141 800 ciclos de CPU. Con O5 (render
desacoplado) la **lógica corre siempre a 50 Hz** y lo que se pierde cuando
no entra es la **imagen** de ese VBL. Medidas WinUAE al 2026-10-05; la fila G8b del 2026-10-06 es solo CPU:

| componente | medido (peor frame) | objetivo | fuente |
|---|---|---|---|
| lógica `level_frame` con sprites y OAM | **37,24 %** (WinUAE, replay YI1) | ≤ 40 % | `docs/medida-oam-o5.md` |
| lógica con OAM ampliada G8b (opt-in) | **41,2 %** (WinUAE l4, YI1 entero, L-OAM asm); antes 43,1 % tras paso 1 | ≤ 40 % real; **puerta roja**, parada tras Rex y Finish en asm | `docs/informe-loam-1007.md`; revisión independiente `docs/informe-coordinacion-1007.md` |
| interrupción lógica + foto | 46,40 % (WinUAE) | — | ídem |
| scroll: `build_mid` + columna + lista | ida **89,16 %** (WinUAE, s ≈ 4576, con P51); vuelta 94,8 % en Musashi (s = 2832; ×~1,3 en la Amiga, **sin medir en WinUAE**). Media de la ida ~15 % | repartir los picos (S5) | ídem; `scrollprof.py` |
| Mario en sprites de hardware (`mspr_draw`) | máx. 7 750 ciclos, media 4 169 (Musashi, tras MA1) | ≤ 3 % de media | `baseline_pc.json` |
| dibujo de los sprites del nivel (G5) | juego sin hacer; G2T mide solo sufijo sintético: ocho recargas exactas y cruce255 con barrera única,0 px. Sin coste integrado medido | ≤ 8 % (asignación, DMA y copper) | `docs/diseno-9.2.md`, `docs/informe-g2t-1007.md` |
| plan temporal del Rex (B35, rama) | 2 405 022 ciclos máx., 0 planes distintos/ABI en 3404 frames; Musashi sin DMA, no coste integrado | ≤ 8000 ciclos máx. para el plan | `docs/informe-g2t-b35-1008.md` |
| microbench transiciones B35-asm (rama) | 18 794 ciclos máx. solo en ese núcleo con entrada ya preparada; 3404 estructuras intermedias exactas, ABI/PIC correctos; sin DMA | ≤ 8000 para el plan entero; integración detenida | `docs/informe-g2t-b35-asm-1008.md` |
| bobs en PF1 (Banzai, excedentes) | 22,7-33,8 % (Banzai + 4 Rex, `bench2.s` W3) | caso raro | `docs/decisiones-medidas.md` |
| HUD | sin hacer (H1 midió la banda) | ≤ 2 % | `docs/medida-hud.md` |
| audio | sin hacer | ≤ 3 % (D5) | — |
| estrés D1 (`stress_back`/`stress_sprites`, con `SPR_OAM`) | WinUAE l4 sin traza, L-OAM asm: 295/4126 (7,15 %, racha 6) y 32/1914 (1,67 %, racha 2); antes del asm 616/4126 y 56/1914 | **roja**; controles de la misma tanda: 145/4126 (3,51 %, racha 3) y 0/1914 | `docs/informe-loam-1007.md`; segunda tanda `docs/informe-coordinacion-1007.md` |
| **fotos omitidas** | **14 de 6312 = 0,22 %**, racha máx. 1 (WinUAE, replay YI1, sin G5/HUD/audio) | ver la compuerta | `docs/medida-oam-o5.md` |

**Lectura:** el problema es de **picos**, no de media. El coste de
`build_mid` depende de la posición de scroll, que es conocida de antemano:
repartir el trabajo entre frames (S5) es la palanca principal, antes que
más asm a mano. Lo que falta sumar al render (G5, HUD, audio y el Banzai)
cae justo en los picos; G5 además escribe en la misma lista del copper que
`build_mid`, por eso S5 va inmediatamente después de G5.

**Compuerta D1 [usuario, redefinida el 2026-10-05]:** lo que mide la
fluidez son las **fotos omitidas** (VBL sin imagen nueva). "Peor frame
≤ 100 %" queda como dato, no como puerta. Criterio del usuario: **que se
vea lo más fluido posible.**

| puerta | replays | umbral |
|---|---|---|
| **objetivo** | replay normal de YI1 (ida, `oracle_yi1`) | **0 fotos omitidas** |
| **mínimo aceptable** | estrés: la vuelta (`stress_back`; s ≈ 2832 y 4580), el Banzai (`stress_sprites`) y el tramo con más Rex | **≤ 0,1 %** de las fotos, **racha máxima 1** (nunca dos VBL seguidos sin imagen) y **como mucho 1 en cualquier ventana de 250 frames** (5 s) |

Se mide en WinUAE cycle-exact con el juego integrado: G5, HUD y audio
incluidos en cuanto existan; antes, el número vale solo para lo que haya.
**Hoy no pasa** (0,22 % sin OAM ampliada y 0,43 % con ella en YI1; WinUAE l4). Un frame omitido a 4 px/frame
de scroll es un salto de 8 px: por eso la racha y la ventana importan tanto
como el porcentaje.

Si agotada la optimización (S5 primero, luego asm a mano en `build_mid` y
en las sondas de colisión) no se llega al mínimo, se le presentan al
usuario estas opciones con números: (1) otra ronda de optimización; (2)
dibujo a 25 Hz con la lógica a 50 Hz, que ahorra scroll y copper pero no
lógica; (3) recortar el alcance, por ejemplo menos sprites a la vez. Mover
el código a slow RAM **no** acelera (P29).

**Regla de conversión** (medida en la 8.2 y en la 6.4): en la A500 un
trabajo cuesta ~1,3-1,4 veces lo que da Musashi, o sea ~1 000-1 100 ciclos
de Musashi por cada 1 % de frame.

---

## 3. Decisiones

Cerradas por el usuario el 2026-09-26: se aceptan las recomendaciones, con
el **teclado primero** en los controles. El criterio general es el mejor
equilibrio entre 1:1 y coste. No queda ninguna decisión abierta; la compuerta D1 se
mide como dice §2.

| ID | Decisión | Qué se hace | Consecuencias | Etapa |
|---|---|---|---|---|
| D1 | 50 Hz o no | **cerrada (usuario, 2026-09-30): 50 Hz, haciendo todo lo posible**; "si no se puede, no se puede" | la optimización (`docs/plan-tecnico.md` §9, §10.1-10.3) va antes que todo lo que suma coste. Compuerta medida en **fotos omitidas** desde el 2026-10-05 (§2): objetivo 0; mínimo ≤ 0,1 %, racha 1, ≤ 1 cada 250 frames. Si agotadas las ideas no se llega, se le presentan al usuario los números y el plan B (dibujo a 25 Hz) | todas |
| **D15** | Velocidad: el ROM (U) es NTSC y la Amiga va a 50 Hz | **cerrada (usuario, 2026-09-30): se acepta** el 83 % de velocidad, como la SNES PAL (`docs/plan-tecnico.md` §10.12) | nada que hacer; la música mantiene el tempo (tick por CIA) | — |
| **D16** | ¿La zona de la tubería (`obj-1.lv`) entra en el alcance? | **cerrada (usuario, 2026-09-30): entra** (`docs/plan-tecnico.md` §10.10) | conversión de una segunda zona, tuberías y transición | 12 |
| **D5** | Música | **secuenciador propio** que lee las secuencias N-SPC de SMW convertidas offline a un formato compacto de eventos (no MOD) | Conserva glissandos, vibrato, envolventes (ADSR aproximado por tick) y el tempo del SPC700 (tick por timer de CIA). **Sin mezcla por CPU**: cada voz va directa a un canal de Paula, 3 de música + 1 de efectos, con prioridad por tema; el eco se omite. Límites: ≤ 64 KB de muestras en chip RAM y **≤ 3 % de CPU** medido. **Verificación** (como sonic2mod de reassembler): contra el registro de escrituras al DSP de `snesorc` en la partida del oráculo, nota por nota, con un informe por tema en `docs/audio/` (SUBAGENTES A0, A3, A6, A8) | 11 |
| **D10** | Ancho de pantalla | **256 px**, como la SNES | DIW centrada; el fetch empieza más tarde, así que vuelve el sprite 7 (4 columnas adosadas); 20 % menos de DMA de planos; la cámara y la aparición de enemigos quedan 1:1 | 6.1 |
| **D11** | HUD | **superpuesto (overlay)**, como la SNES | En las líneas del HUD el copper apunta PF1 a un bitmap fijo del HUD y PF2 sigue con su paralaje. Si en esas líneas aparece capa 1 del nivel, antes de renunciar al overlay se busca otra variante que lo conserve (`docs/plan-tecnico.md` §10.8) y se consulta | 10 |
| **D12** | Power-ups | **todos los de Yoshi's Island 1** | ver la lista abajo | 9.1 |
| **D13** | Carga y memoria | **direcciones fijas, enlazado absoluto**; lo que lee el chipset en chip RAM y el resto en `$C00000` | ver el esquema abajo | 6b.1 |
| **D14** | Controles | **teclado primero**, joystick como alternativa | ver la asignación abajo | 6b.3 |

**D12 — qué hay en el nivel** (`lvparse.py --dump` de `obj.lv` y `spr.lv`):

| objeto | cantidad | da |
|---|---|---|
| bloque `?` (flor) | 1 | seta si Mario es chico; flor de fuego si es grande. Hay que portar las **bolas de fuego** (hoy `MARIO_UNSUP_FIRE`) |
| bloque giratorio "estrella 2 / 1-UP / enredadera" | 1 | lo decide el ROM según el estado: transcribir la rutina del golpe, no suponer. Incluye la **estrella** (invencibilidad, música propia) |
| luna 3-UP | 1 | 3 vidas |
| monedas de Yoshi | 4 | puntos; la 5.ª del recuento da 1-UP |
| bloques `!` amarillos | 5 | dependen del palacio amarillo: mirar en el oráculo si son sólidos, y si lo son, portar su contenido (seta) |
| champiñón invisible (sprite `$C7`) | 1 | 1-UP escondido |
| monedas (100) | — | 1-UP |

Estados de Mario: chico, grande y fuego, más la caja de reserva del HUD. En
el nivel no hay pluma: la capa queda fuera por el propio nivel, no por
recorte.

**D13 — esquema de carga** (lo más rápido de programar y de ejecutar dentro
de las reglas de la A500):
1. El bootblock carga con `trackdisk.device`, mientras el SO todavía está
   vivo, un **stage 2 pequeño** (el loader). En KS 1.x trackdisk solo lee a
   chip RAM.
2. El loader lee el resto del disco en bloques comprimidos a un buffer de
   chip, con un compresor LZ simple y rápido de descomprimir en 68000.
   Descomprime:
   - lo que lee el chipset (planos, `BLK`, `L2B`, listas del copper, frames
     de sprites, muestras) a **direcciones fijas de chip RAM**, con la
     alineación de §7 de `AGENTS.md`;
   - el código y los datos de CPU (`ram[]`, `rom00`, tablas, `MAP`, `CHG`,
     `MLX`, `MLD`, `INI`) a **direcciones fijas de `$C00000`**, después de
     comprobar que responde (P8).
3. Toma la máquina y salta al código.

Todo se enlaza en absoluto con **vlink**, en esas direcciones. Así
desaparecen el límite de 32 KB de datos relativos a `a4` (P36) y la
comprobación de referencias absolutas de `logicbench_build.sh`, y vbcc puede
usar direccionamiento absoluto corto donde convenga. El slow RAM no acelera
(P29): sirve para liberar chip RAM. **Medir** el tiempo de carga (con y sin
compresión) y dejar el que sea más corto.

**D14 — teclado** (códigos raw del Amiga, por posición física, válidos para
cualquier distribución nacional):

| SNES | tecla | raw |
|---|---|---|
| cruz | flechas: arriba / abajo / derecha / izquierda | `$4C` / `$4D` / `$4E` / `$4F` |
| B (salto) | Z | `$31` |
| A (salto con giro) | X | `$32` |
| Y (correr, agarrar, disparar) | A | `$20` |
| X (igual que Y en SMW) | S | `$21` |
| Start (pausa) | Return | `$44` |
| Select | Shift derecho | `$61` |

Joystick de alternativa: botón 1 = B, botón 2 (`POTGO`/`POTINP`) = Y, y
arriba + botón = A. Las dos entradas se combinan con un OR. Asignación
cambiable en un solo lugar (una tabla).

---

## 4. Olas y sesiones (revisado el 2026-10-07)

Una sesión agrupa coordinación, agentes en worktrees, revisión e integración.
Tarjetas y estados: `SUBAGENTES.md` §4. La sesión L-OAM/G5a-bis del
2026-10-07 integra una mejora de lógica, pero **no cierra tarjetas**:
L-OAM queda en 41,2 % de lógica YI1 y estrés peor que su control;
G5a-bis se detiene en A por ventanas de color vacías. Los dos bloqueos
se reproducen y se detallan en `docs/informe-coordinacion-1007.md`.
G2T-A (2026-10-07, noche) fijó el contrato temporal con medidas y dejó
la puerta A-T verde (`docs/informe-g2t-a-1007.md`): G5 B/C quedan
habilitadas con `docs/instrucciones-g2t-bc.md`. La revisión de coste OAM ya se entregó. B35 queda exacta en rama,
pero detenida por coste; primer microbench asm medido (18 794 ciclos solo en transiciones), sin ruta viable al plan completo. Faltan un nuevo diseño, B2bis y C. L-OAM sigue en 41,2 %. Las olas 1 y 2 siguen cerradas.

| ola | contenido (lo que falta) | estado | sesiones que faltan |
|---|---|---|---|
| 1. Medir y preparar | — | **cerrada** | 0 |
| 2. 50 Hz (1) | — (S4 descartada, P89) | **cerrada** | 0 |
| 3. 50 Hz (2) + diseños | G2/G3 acotadas y traza D1 integradas; L-OAM asm parcial (41,2 % YI1, estrés rojo), G5a-bis detenida fase A (ventanas vacías). G2T-A hecha (contrato fijado, A-T verde); B35 exacta en rama pero inviable (2,41 M ciclos máx.); primer microbench asm entregado y detenido (18 794 ciclos solo en transiciones); faltan nuevo diseño viable, B2bis, Cpre/C y la ruta OAM de piraña; A2 y R7. A1/G8b adelantadas | **B35 parcial por coste; L-OAM roja** | **3 estimadas** (nuevo diseño viable de B35 + B2bis/C + L-OAM; el microbench no reduce la ruta crítica) |
| 4. Motores y estructura | G4 + G6, G5 + G9, C2 (vlink), S8 (cámara vertical), A0 + A2, P7/P9/P10, T1, I/E sueltas | pendiente | 2-3 |
| 5. Integraciones y 50 Hz con sprites | S5 (+ S3/S6) con G5 ya hecho, C3/C4/C5 (loader), segundo PF1 + G7 (bobs), H2-H4 (HUD), A3/A4 (música) | pendiente | 2-3 |
| 6. El juego completo | Z2-Z6 (punto medio, meta, tiempo, fundidos, poste), T2/T3 (tubería), A5-A8 (efectos, comparación), H5, R7 | pendiente | 2 |
| 7. Segunda ronda de 50 Hz | todo junto contra la compuerta D1 en estrés | pendiente | 1 |
| 8. Cierre | Z7, Z8, U1-U4, arreglos | pendiente | 1 |
| | **total que falta** | | **10-13 estimadas**, con B35 exacta pero inviable; 14-18 si hay que serializar |

Estimado revisado tras el microbench B35-asm (2026-10-08): se conservan **10-13**
sesiones restantes, 14-18 serializadas, con incertidumbre: la fase de medida se
entregó, pero 18 794 ciclos solo en transiciones no habilitan integración ni
reducen la ruta crítica. Hace falta otro diseño medido. B4/B5 exactas no cierran B/C.
Proyecto completo ~16-18 sesiones estimadas (14-18 restantes si hay que serializar). El estimado anterior se archiva textual en
`docs/archivo/sesiones.md`. E11-E14, A1 y G8b son avances previos parciales
que no cierran las tarjetas de dibujo ni reducen por sí solos la ruta crítica.

Lo que más mueve el estimado: viabilidad temporal del banco G3, alcance
de la siguiente optimización OAM, G5 integrado y el pico del scroll con
enemigos (S5). Las decisiones de 50 Hz y fidelidad permanecen vigentes.
El trabajo del usuario en la PC (U1-U3) sigue registrado en `PROXIMO.md`.

---

## 5. Riesgos principales

| riesgo | señal | mitigación |
|---|---|---|
| El frame no entra a 50 Hz | §2: fotos omitidas por encima del umbral | S5 antes de sumar más coste; compuerta D1 en fotos omitidas |
| Picos escondidos | un frame suelto muy caro (hoy: 307 % en s = 4504 en el scroll) que la media no muestra | medir siempre el máximo **y dónde ocurre**; los bancos descartan solo los frames de arranque |
| Faltan columnas de sprites | 2-3 columnas libres con Mario (G1) | D10 = 256 px; cola de bobs en PF1 (G2/G7) |
| Crecimiento del banco de sprites | G2 acotado entra: 64528 B; G8b sin Banzai mide 77152 B aun sin variantes Mario nuevas | G3 limitado al contrato; nueva auditoría para ampliar. `docs/informe-g2.md` |
| vbcc compila mal | `m68kverify` llega al tope de 10 M ciclos o difiere de `marioverify` | V1 siempre (P38) |
| Datos del C > 32 KB con `-sd` | `logicbench_build.sh` falla o hay referencias absolutas | D13: enlazado absoluto con vlink (6b.1) |
| Índices de 16 bits con signo | escrituras 64 KB antes a partir de 32 KB | `(An,Dn.l)` con `moveq #0` antes (P40) |
| El modelo de tiempos del copper | cargas corridas unos píxeles | calibrar con `copcal` en cada pantalla nueva (0.4, 6.1); los WAIT cuestan ranura (P39) |
| El oráculo no cubre un caso | un sprite o una pendiente sin frames que verificar | sesión de grabación única (8.1) |
| Chip RAM | vivo opt-in 402232 B; + banco G2 =466760 B proyectados. Con banco máximo + PF1 doble + audio =592440 B, `docs/diseno-9.2.md` §5 | C2/C4: las tablas de CPU (135 468 B) a `$C00000` (`docs/plan-tecnico.md` §10.7) |
| La cámara vertical de YI1 | Mario se corre respecto del fondo cuando la cámara sube (`Bg1VOfs` < `$C0`) | `docs/plan-tecnico.md` §10.2b: segmentos por línea del nivel y la v de los WAIT |
| Muestras de audio | todas las BRR son 92 KB ≈ 164 KB de PCM | solo las del tema y los efectos; bajar la frecuencia donde haga falta (`docs/plan-tecnico.md` §10.9) |
| Lo que no cubre ningún oráculo | un camino del ROM que nadie recorrió (P69: la cámara vertical) | grabarlo con snesorc antes de darlo por verificado |

---

## 6. Entornos y arranque

| tarea | Claude cloud | PC local (Windows) |
|---|---|---|
| compilar (vasm, vbcc, gcc) | sí (`setup_cloud.sh`) | sí (Git Bash, PATH de ucrt64 antes de gcc: `docs/reglas-ola-pc.md`) |
| verificar contra el oráculo | sí | sí |
| **grabar oráculos** | **sí, con guion** (`snesorc_setup.sh`, `snesorc_make.sh`) | sí |
| medir en cycle-exact | FS-UAE + AROS; capturas de a una (P76) | WinUAE + KS 1.2 (`tools/shot.ps1 -Exact`) |
| probar el arranque en KS 1.2 y el teclado | **no** | sí |
| comparar contra `SuperMarioWorldMap02.png` | **no** | sí |

```bash
# cloud (en la PC: export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python)
sh tools/setup_cloud.sh               # ~2 min la primera vez, ~15 s con caché
export VBCC=~/vbcc PY=python3
python3 tools/lint_port.py && python3 tools/regress.py        # PC + 68000 + oráculos
sh tools/snesorc_setup.sh             # opcional: el generador de oráculos (work/snesorc)
sh tools/game_build.sh && python3 tools/gamecheck.py --spr    # el juego (replay) en Unicorn
GDEFS=" " OUT=work/live sh tools/game_build.sh                # el de jugar: work/live/game.adf
```

En la PC la regresión es
`python tools/regress.py --baseline tools/baseline_pc.json --level`.
O5 es el modo por defecto (`-DNODECOUPLE` = bucle viejo); si cambia
`scroll_frame`, sincronizar `dc_loop` y `gb_scroll_frame` (P97).

---

## 7. Cierre de sesión (obligatorio)

**Regla [usuario, 2026-10-05]: ninguna sesión termina sin escribir qué es
lo que sigue.** Al cerrar, quien coordina hace, en este orden:

1. **Archivar** el `PROXIMO.md` que se cumplió (o no): copiarlo al final de
   `docs/archivo/sesiones.md` bajo un título con la fecha y la sesión,
   seguido de **qué se hizo**: tarjetas integradas con sus commits, cifras
   medidas con su fuente, lo que quedó a medias y por qué.
2. **Reescribir `PROXIMO.md` en el sitio**, con la misma estructura: la
   próxima sesión (objetivo, tarjetas con modelo, ficheros y puerta), después
   en orden, y lo pendiente del usuario. Si la sesión siguiente no está
   decidida, escribir la recomendación y marcar qué tiene que decidir el
   usuario.
3. **Escribir las instrucciones paso a paso** de cada tarjeta de la
   próxima sesión [usuario, 2026-10-07], en `docs/instrucciones-<tarjeta>.md`
   (agregarlo a `docs/README.md`), y enlazarlo desde su fila en
   `PROXIMO.md` §1. Modelo: `docs/instrucciones-loam.md` y
   `docs/instrucciones-g5a-bis.md`. Cada una dice, en orden: por qué existe
   la tarjeta (con la medida que la motiva), las reglas que no se
   negocian, el entorno y cómo comprobar que se parte de verde, los pasos
   con el **comando exacto y la salida esperada**, las puertas automáticas,
   las **condiciones de parada** ("si X, parar y avisar") y qué tiene que
   llevar el informe. Lo que todavía no se sabe se escribe como fase con
   puerta de medida, no como paso adivinado. Las tarjetas de olas
   posteriores bastan en semi-detalle (`docs/instrucciones-olas.md`).
   Antes de escribirlas, probar uno mismo lo que haga falta para que
   ningún paso sea a ciegas (como el paso 1 de L-OAM). `lint_port.py`
   (D6) falla si una tarjeta de `PROXIMO.md` §1 no tiene su fichero.
4. **Actualizar el estado**: §1 de este fichero (las filas que cambiaron,
   con cifras medidas: %, px, frames, ciclos), §2 si cambió algún número del
   frame, §4 (olas y sesiones que faltan, re-estimado) y la tabla de estado
   de `SUBAGENTES.md` §4.
5. **Lo que quedó viejo se archiva, no se apila**: un plan o un texto que
   ya no rige se mueve textual a `docs/archivo/` (con una línea que diga
   cuándo y por qué) o se borra si ya está archivado. Nunca una sección
   nueva "próxima sesión" fuera de `PROXIMO.md`.
6. `tools/lint_port.py` (comprueba también estas reglas de los docs) y
   `tools/regress.py` en verde; nada sin commitear (si algo queda a medias,
   commit `WIP:` que diga qué falta verificar).

Cifras siempre con su fuente (herramienta y emulador); lo estimado,
marcado como **estimado**.

---

## 8. Comprobaciones: los scripts

Todo cambio pasa por estos scripts **antes del commit**. Corren en cloud y
en la PC; solo necesitan la biblioteca estándar de Python, salvo lo que se
indica.

| script | qué comprueba | cuándo | tiempo |
|---|---|---|---|
| `tools/lint_port.py` | reglas que el compilador no ve. **Errores**: R9 (nada derivado de la ROM en git), `float`/`double`, `malloc`, `#include <...>` fuera de un `#if`, el patrón de P38 (`p = ram + x` indexado con `p[wm_X]`). **V3**: una rutina asm que cambia un registro que su cabecera no declara (`registros destruidos` / `salida`; las `public _xxx`, contra la ABI de vbcc), con `tools/asmlint_port.py`. **Avisos**: `(An,Dn.w)` en asm (P40; una línea revisada se marca con `; P40 ok`), `int` a secas y registros declarados de más (V3). **Docs** (§7): `PROXIMO.md` existe y es el único con "próxima sesión" (D1, D2), nada cita con la ruta vieja un documento archivado (D3), `docs/README.md` lista todo (D4) y aviso si hubo commits de código después del último `PROXIMO.md` (D5) | antes de cada commit | 2 s |
| `tools/regress.py` | **compila desde el código actual** y compara ~40 métricas (~55 con `--level --emu`) con `tools/baseline.json`. Cubre los 7 modos de `marioverify`, `m68kverify` (full, loop y loop con sprites, con ciclos) y los **cruces PC = 68000** (si el binario de vbcc no da lo mismo que gcc es P38, no el port) | antes de cada commit que toque `player/` o las herramientas del port | 4 s |
| `tools/regress.py --level` | + la cadena de la etapa 5 (`mkbg` → `mkleveld` → `mkscroll` → `render_d`); necesita numpy | si se tocó el conversor | ~1-2 min |
| `tools/regress.py --emu logic,scrollbench,scrollimg` | + medidas en FS-UAE cycle-exact: `logicbench` (% de frame), `scroll.s -DBENCH` (media y máximo, con la s del peor frame) y `scroll_check --mid` en 6 x del nivel (`--scroll-x` para elegirlas). Si una captura no está en la x pedida (> 20 % distinto), lo dice en vez de contarlo como fallo de imagen | al cerrar un paso de optimización o del scroll | ~13 min |
| `tools/regress.py --shots DIR` | lee capturas ya hechas (en la PC, las de `shot.ps1 -Exact`): `DIR/logicbench.png`, `DIR/scrollb.png`. La base del repo es de FS-UAE: en la PC usar `--baseline tools/baseline_winuae.json` (se crea con `--update` la primera vez) para no mezclar emuladores | en la PC | s |
| `tools/abcheck.py BASE [--sprites] [--prof]` | A/B de una optimización: compila `BASE` (en un worktree) y el árbol actual y los corre en Musashi. Dice si la **semántica es igual** (resincronizaciones y tramo) y cuánto cambian los ciclos de media, p99 y máximo; con `--prof`, también por función | cada optimización del C | 3 s (`--prof`: ~2 min) |
| `tools/coverage.py` | qué líneas y funciones del C no corren nunca bajo `marioverify` con ninguna grabación (P69): compila con `--coverage`, corre todas las `work/oracle_*.txt` y escribe `docs/cobertura.md` (conserva sus notas a mano). Necesita `gcov` | al agregar grabaciones o portar lógica nueva | 5 s |
| `tools/imgdiff.py A.png B.png` | dos capturas del mismo emulador son **idénticas** (sale con 0) o no, con la caja y un PNG de las diferencias. Las capturas de FS-UAE son deterministas: comprobado con dos corridas de x = 1000 | optimizar `scroll.s` (antes/después); scroll de ida y de vuelta (6.2) | s |

Resultados de `regress.py`, por métrica:
- **OK:** igual a la base, dentro de la tolerancia.
- **MEJOR:** no falla. Si el cambio es intencional, `--update` y explicarlo
  en el commit.
- **PEOR** o **FALTA** (la herramienta murió o cambió su salida): fallan, y
  el script sale con 1.

Las métricas tienen dirección: `eq` (tiene que dar exactamente lo mismo),
`max` (más es mejor), `min` (menos es mejor) e `info` (solo se muestra).
Detalles de uso:
- La salida completa de cada herramienta queda en `work/regress.log`; lo
  medido, en `work/regress_last.json`.
- `--update` **se niega** si hay fallos (una base peor esconde regresiones);
  `--update --force` solo para un cambio de alcance explicado en el commit.
- `--accept-last` pasa a la base lo de la última corrida sin volver a medir
  (útil después de una corrida `--emu` larga).

### 8.1 Flujo según lo que se cambia

| cambio | pasos |
|---|---|
| lógica en C (`player/*.c`) | `lint_port.py` → `regress.py` → si era para ganar ciclos, `abcheck.py <commit anterior> --sprites` (semántica IGUAL y ciclos menores) → al cerrar el paso, `regress.py --emu logic` → commit. Si algo sale MEJOR, `--update` en el mismo commit |
| optimización de `scroll.s` | capturas con el mismo `-DSTOPX` antes y después → `imgdiff.py` tiene que dar IDENTICAS en las 6 x → `regress.py --emu scrollbench` (media y **máximo** menores). La versión "antes" sale de `git show BASE:player/scroll.s > work/scroll_base.s` y se arma igual, con `-I player` |
| función nueva de `scroll.s` | `scroll_check.py --mid` en las 6 x (fallos que no explica un vecino ≤ base) → `regress.py --emu scrollimg,scrollbench` → `--update` |
| conversor del nivel | `regress.py --level` (`render_d`: 0 px contra la imagen ideal) |
| etapa nueva | agregarle métricas a `regress.py` (una función `xxx_checks` que corre la herramienta y hace `r.put(nombre, valor, dirección)`) y guardarlas con `--update` |

### 8.2 Comprobaciones que hay que crear con cada etapa

Cada etapa futura tiene que dejar su propia comprobación automática, y
engancharla en `regress.py`. Especificación mínima:

| etapa | script a crear | qué compara | pasa si |
|---|---|---|---|
| 6.1 | parametrizar `scroll_check.py` (`--w`, `--sc`, origen) | capturas a 256 px y capturas de WinUAE ×2, no solo FS-UAE ×2,125 | lo mismo que hoy a 320 px |
| 6.2 | `-DRETURN` en `scroll.s` + `imgdiff.py` | captura en x a la ida y a la vuelta | IDENTICAS en 6 x |
| 6.3 / 6b.5 | `tools/replay_check.py` | ADF en modo replay parado en el frame N (`-DSTOPFRAME=N`) contra el esperado del PC: cámara `$1A-$1D` del oráculo + `yi1_d.dat` (+ la OAM de Mario de `oracle_yi1_oam.bin` desde la 6b) | ≤ 0,25 % de fallos limpios que no explica un vecino, en ≥ 5 frames repartidos por el nivel |
| 6b.1 | `tools/memmap.py` + chequeos en el arranque | a partir del listado de vasm (`-L`) y de la tabla del loader: todo lo que lee el chipset < `$80000`; planos alineados a 8, listas del copper a 4 y audio a 2; total de chip ≤ 512 KB. En la Amiga, al arrancar: `$C00000` responde (P8) y cada `AllocMem` quedó alineado; si no, color de borde de error, como `demo.s` | 0 violaciones; el arranque no pinta el borde de error |
| 6b.3 | `tools/inputtest.c` | tabla de casos de la conversión joystick → `$15-$18` (flanco: `JoyFrame = nuevo & ~anterior`) | todos los casos |
| 6b.4 | `tools/mkmario.py --selftest` | ida y vuelta: frames de sprite adosado → píxeles contra los tiles de `chr` renderizados, volteados incluidos | todas las poses idénticas |
| 9.1 | modo `marioverify game` con contadores por número de sprite | frames exactos de cada tipo (Banzai, piraña, Chuck...) | 100 % o fallos listados por causa |
| 9.2 | `tools/sprcop_verify.py` | el asignador de columnas del 68000, corrido en Musashi (como `m68kverify`) sobre los frames de `oam_yi1.txt`, contra el modelo de `copsim.py`: palabras de control de sprite, MOVE de color, objetos que pasan a bob | 0 objetos sin mostrar; colores mal solo donde `copsim` también falla |
| 10 | modo `marioverify hud` | contadores del port contra los grabados en la 8.1 (vidas, monedas, tiempo, puntos) | todos los frames |
| 11 | `tools/brr2pcm.py --selftest` + un render offline del secuenciador | PCM contra el WAV de `smwrecomp` (correlación ≥ 0,99 por muestra); notas a ±1 tick y ±5 cents | los umbrales |
| 12 | replay completo sobre el ADF final | el modo replay se queda en el binario final como opción de compilación: la partida grabada termina en la meta en el mismo frame que el oráculo | llega a la meta, mismo frame |

---

## 9-11. Optimización, lo que falta y más allá de YI1

Movidos textuales a **`docs/plan-tecnico.md`**, con los mismos números de
sección (2026-10-05).
