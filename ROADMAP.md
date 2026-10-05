# ROADMAP.md — Plan a futuro y handoff del port-demo SMW → Amiga 500

> **Qué es este fichero.** El plan de trabajo desde el 2026-09-26 hasta el ADF
> final, escrito para que lo ejecute cualquier agente o persona sin contexto
> previo. `AGENTS.md` sigue siendo el contrato: reglas duras, formatos,
> pitfalls y resultados medidos. Este fichero dice **qué hacer, en qué orden y
> cómo saber que está hecho**. Si algo de acá contradice `AGENTS.md` §2 (reglas
> duras), manda `AGENTS.md`.
>
> Se reescribe, no se apila: al cerrar una sesión se actualizan §1 y la tabla
> de estado con la plantilla de §7. El historial detallado queda en los
> commits y en `AGENTS.md`.

---

## 0. Cómo usar este plan

1. Leer en este orden: §1 (handoff) → §2 (presupuesto) → la etapa que toca
   (§5, `docs/etapas.md`) → §8 (scripts de comprobación) → `AGENTS.md` §2 (reglas), §7
   (convenciones), §8 (índice de pitfalls; texto en `docs/pitfalls.md`) y §11 (definición de "hecho"). Si
   la etapa es de optimización, también §9.
2. Trabajar **un paso por vez**. Cada paso dice dónde corre, qué hacer y
   cuándo está hecho. No se empieza el siguiente con el anterior en rojo.
3. Al cerrar un paso: commit `Etapa N.x: <qué>` y actualizar §1.2. Si aparece
   una trampa nueva, se agrega como `Pnn` en `docs/pitfalls.md` y en el índice de `AGENTS.md` §8 (la próxima es
   **P103**).
4. Al cerrar la sesión: handoff con la plantilla de §7, que reemplaza a §1.
5. Para repartir el trabajo entre subagentes (tarjetas por etapa, niveles,
   olas, mapa de conflictos y protocolo de integración): **`SUBAGENTES.md`**.
   Worktree por tarea: `sh tools/wt_new.sh <tarjeta>`.

**Reglas del proceso (no negociables, vienen de lo que ya costó caro):**

| # | Regla | Por qué |
|---|---|---|
| V1 | Todo cambio en `player/*.c` se verifica con `marioverify` (C del PC) **y** con `m68kverify` (binario 68000 de vbcc): `python3 tools/regress.py` hace las dos cosas y compara con `tools/baseline.json`. Ninguna métrica puede empeorar | P38: vbcc compiló mal código que gcc compilaba bien |
| V2 | Los tiempos solo valen en cycle-exact: `tools/fsuae_shot.sh` en cloud, `tools/shot.ps1 -Exact` en la PC. Musashi (`m68kverify --engine musashi`) es una **cota inferior** porque no tiene esperas de DMA | P30; Musashi daba 24 % y la Amiga 34 % |
| V3 | Toda imagen se compara contra el esperado del PC (`scroll_check.py`) y, en la PC, contra `SuperMarioWorldMap02.png`. **Primero lo que se nota a simple vista**, criterio del usuario | la captura de FS-UAE está reescalada ×2,125 y ensucia los bordes |
| V4 | Nada derivado de la ROM entra en git (R9). Las grabaciones del oráculo sí (`work/oracle_*.txt`, `work/oam_*.txt`) | `.gitignore` |
| V5 | Las decisiones marcadas **[usuario]** no las toma el agente: prepara los datos, recomienda y pregunta | D8 y D1 se cerraron así |
| V6 | Antes de pedirle al usuario que juegue para grabar, **probar el grabador** (`oamrec.py --test 10`) | límites del puerto Lua: 1024 caracteres por valor, 16 valores por respuesta, una sola conexión TCP |
| V7 | Antes de cada commit: `python3 tools/lint_port.py` y `python3 tools/regress.py` en verde. Una optimización, además, `tools/abcheck.py` (semántica IGUAL, ciclos menores). Detalle en §8; ideas de optimización en §9 | que el siguiente agente no herede un rojo que no se ve |

---

## 1. Handoff (actualizado al 2026-10-05; estado vigente después de la ola 3 abajo)

### 1.1 Ramas

| rama | contenido |
|---|---|
| `master` | base hasta el 2026-09-27: primer ADF jugable (etapas 0, 6.1-6.3, 8.2, 6b) |
| `claude/brave-ritchie-mm5o6r` | sesión cloud del 2026-09-30, sobre `master`: oráculos sin usuario (snesorc), Etapa 9.1 (6 sprites más, `game` sin resincronizaciones), entrada y modo diagnóstico (6b.7), tres bugs arreglados (cámara vertical, copper de la línea 255, `mario_sprite` mal compilado) y herramientas de la 6.4. **Mergeada a `master` el 2026-09-30** (pedido del usuario, avance rápido) |

| `wt/g0-next` (`../wt-g0-next`) | **2026-10-05, sin commitear:** arreglo de P51 en `player/scroll.s` (`build_mid`/`bm_left`: a 256 px, una carga de la cola con x > `XKNEE` lleva WAIT propio), `tools/scrollsim.py` (`advance()`: 8 px por MOVE después de x = 239) y `tools/scroll_tail_check.py` (nuevo). **Sin verificar**: falta regresión y las capturas SX. Su commit `0d7d51d` es el mismo cambio que `07ef629` en `master` |
| `wt/gfx-regress-next` (`../wt-gfx-regress-next`) | **2026-10-05, sin commitear:** banco SX/SX2, `tools/sxverify.py` + `docs/validacion-sx.md` (24 ADF: 6 posiciones, ida y vuelta, antes/después de SX). Capturas a medias en `work/sxverify/`; la sección "Resultados" sigue vacía. La rama en sí ya está en `master` |
| `wt/oam-next` (`../wt-oam-next`) | limpia; su commit `3def3e4` es el mismo cambio que `cf2ce56` en `master`. Se puede borrar |

- 2026-09-30: trabajo en paralelo con 4 subagentes, cada uno en su worktree; el
  coordinador integró, arregló lo que quedó flojo y verificó todo junto.
- Lo único a medias está fuera del build: `tools/wip64/` (el diseño de la
  6.4, sin ensamblar; lo que falta está en la cabecera de
  `build_mid_incremental.s`).

### 1.2 Estado por etapa

| Etapa | Qué | Estado | Dónde está |
|---|---|---|---|
| 1-2b | Assets, paletas, nivel, capa 1 1:1 | **hecho** (6111/6111 bloques) | `tools/smw2amiga.py`, `palette.py`, `mklvl.py`, `m16diff.py` |
| 3-4 | Esqueleto Amiga y viabilidad | **hecho**; D1, D8 y D9 cerrados | `player/boot.s`, `bench*.s`, `copbench.s` |
| 5 | Conversor del nivel al formato (d) | **hecho en cloud**; falta compararlo contra la referencia en la PC (→ 7) | `tools/mkbg.py`, `mkd8in.py`, `mkleveld.py`, `render_d.py` |
| 6.1-6.3 | Scroll a 256 px, ida y vuelta, lo mueve la cámara del port | **hecho** (2026-09-27). El 2026-09-30: el copper no corría las líneas 212-223 (P59), arreglado | `player/scroll.s`, `tools/mkscroll.py` |
| 6.4 | Scroll ≤ 25 % en el peor frame | **NO hecha**. **S1a+S2 integradas (2026-09-30)**: cargas "tarde" fijas en MLD con celda de 8 px y LNS por grupos de 16 líneas; imagen idéntica; media de la ida 9,9 → 8,4 % (2 px) pero el peor frame sube 0,5-1,9 puntos (P81, aceptado: se recupera con S4/S5). Antes de S1a+S2: Ida: Musashi máx. 54,1 % (2 px/frame), FS-UAE máx. 78,8 % (4 px/frame, s = 4584). **Vuelta: Musashi media 36,6 %, máx. 94,8 %** (P72, no estaba medida). Perfil por zonas (`scrollprof.py --zones`), ida/vuelta simulada (`scrollsim.py --ret`); diseño incremental en `tools/wip64/` | Etapa 6.4 |
| 7 | Capa 2 contra la referencia | pendiente (solo PC) | — |
| 8a/8b | Física y colisión de Mario | **hecho**: `full` 6510/6547 en `oracle_yi1`; en las grabaciones nuevas, 99,6-99,8 % (los fallos son contactos con sprites) | `player/mario.c`, `mcoll.c`, `manim.c` |
| 8 (gfx, cámara) | Gráficos y cámara | **hecho**; `gfx` 100 % en los 5 oráculos. Cámara vertical hacia arriba arreglada (P69) | `player/mgfx.c`, `mcam.c` |
| 8c | Pendientes | **casi cerrada**: `oracle_hills` (colinas 1-4 a toda carrera en los dos sentidos, parado, deslizándose y saltando) da las pendientes 2154/2154 exactas. La colina grande de x = `$AE0` grabada el 2026-09-30 (`oracle_hills2`: `full` sin fallos de pendiente; los 12 fallos son SpeedY `$7D` en pisotones) | `work/oracle_hills.txt`, `oracle_hills2.txt` |
| 8.1 | Grabaciones | **oráculos sin usuario**: `work/snesorc` corre la ROM (U) en el emulador de snesrev/smw con entrada guionizada (`tools/snesorc/*.orc`) y reproduce `oracle_yi1` línea a línea (6871/6871). Grabadas: `normal`, `diagpipe`, `hills`, `banzai`; **ola 1 (2026-09-30, en la PC Windows, P82)**: `hills2`, `chuck`, `shells` (sin pisar al `$02`), `goal` (una altura), `pw_seta`, `pw_flor` (Mario grande por `poke`), `pw_morir_enemigo`, `pw_morir_caida`, `stress_piranha`; `tools/orc_has.py` (qué sprites y qué Mario hay en un oráculo). **Faltan**: `goal_low`/`goal_miss`, R9 `pipe` (notas abajo), punto medio, monedas de Yoshi, estrella, 1-UP, 3-UP, `$C7`, bloques `!`, `stress_back` (a medias: `tools/wipr/`, llega a x `$0BC0`), `stress_sprites`, `stress_vert` (P84) | `tools/snesorc/`, `snesorc_setup.sh`, `snesorc_make.sh` |
| 8.2 | Optimizar la lógica | **hecha** el 2026-09-27 (peor frame con sprites 40,1 % en WinUAE). Con los sprites nuevos, peor frame en Musashi 43 116 → **45 896** (frame 9715: 2 pirañas, 1 Rex, `$8E`, `$C7`), **~45 % estimado** en la A500 (por encima del 40 %). **L1a (2026-09-30)**: `f7f4` hacia arriba en asm, peor frame con sprites en Musashi (vbcc de la PC) 46 000 → 45 054 | `player/logic68k.s` |
| 9.1 | Sprites: lógica | Rex, `$83`, `$B9`, **`$BD` Koopa deslizante, `$02` Koopa sin caparazón, `$9F` Banzai Bill, `$4F` piraña, `$8E` warp, `$C7` seta invisible**. `game`: **0 resincronizaciones** de Mario en los 5 oráculos; sprites exactos por tipo en `regress.py`. Faltan Chuck `$95`, caparazón rojo `$DB`, cinta de meta `$7B` y lo de D12 (grabados: `oracle_chuck`, `shells`, `goal`, `pw_*`). **I1 (2026-09-30)**: cada sprite nuevo va en su `player/spr_*.c` (entra por glob en los tres builds; el Rex ya está en `spr_rex.c`, P78) | `player/msprite.c`, `spr_*.c` |
| 9.2 | Sprites: dibujo | Mario hecho. **G2 documentado, G0 medido a 256 px, G3a en regresión y OAM 68000 opt-in verificada (2026-10-05)**. Falta G3 final, asignador, colores/DMA y bobs; los enemigos todavía no se ven en Amiga | `docs/diseno-9.2.md`, `docs/medida-g0.md`, `docs/oam-amiga.md` |
| 6b | Integración | primer ADF jugable (2026-09-27) + **6b.7** (2026-09-30): entrada como `ControllerUpdate` (P60) y **modo diagnóstico** (P58) con historial del joypad y reproducción en el PC desde una captura. **6b.6 medida (O1, 2026-09-30)**: `game.s -DBENCH` + `game_read.py`; en WinUAE (antes de S1a+S2) peor `build_mid` 84,8 % (s = 1825), `level_frame` 35,6 %, total 127 %, media 46 %, 362 de 6312 frames pasados. Falta la decisión D1 (O4) y 6b.1 (vlink, compresión) | `player/game.s`, `tools/diag_read.py`, `gamesim.py`, `inputtest.py` |
| 10-12 | HUD, audio, pulido | no empezados | — |

### 1.3 Números de regresión (2026-09-30, cloud)

La fuente de verdad es `tools/baseline.json` (cloud: vbcc de cloud y
FS-UAE); la PC usa `tools/baseline_pc.json`. El 2026-09-27 la PC había
escrito sus ciclos en `baseline.json` (otro vbcc): el 2026-09-30 se volvió a
medir todo en cloud y se guardó con `--update --force`.

| qué | valor | antes (2026-09-27) |
|---|---|---|
| `marioverify full` / `gfx` / `loop` (`oracle_yi1`) | 6510/6547 · 6869/6869 · 37 resincronizaciones | igual |
| `marioverify game` (`oracle_yi1`) | **0 resincronizaciones**, tramo 3824; sprites exactos por tipo: 02 252, 4F 2599, 83 340, 8E 2518, 9F 454, AB 2635, B9 309, BD 322, C7 3178 (ninguno distinto) | 1 (Koopa `$02`, frame 5322) |
| `marioverify sprloop` / `sprload` | 2684/2684 · 20/20 | 2593/2594 · 20/20 |
| oráculos snesorc (`orc.*` en `regress.py`): `full` / `loop` / `game` | normal 1249/1254 · 5 · 0; diagpipe 2693/2699 · 6 · 0; hills 2147/2154 · 7 · 0; banzai 1078/1080 · 2 · 0 (las resincronizaciones de `loop` son pisotones: sprites) | — |
| 68000 `loop --sprites` (Musashi): resincronizaciones / media / p99 / máx. | **0** / 32 730 / 43 234 / 45 896 | 4 / 30 893 / 42 652 / 43 280 (base de la PC) |
| cruces PC = 68000 | `full`, `loop` y **RAM entera** tras cada `level_frame` (`--cross`): 0 diferencias en 6547 y 6549 llamadas | los dos primeros |
| `gamecheck.py` / `--spr` | 0 diferencias en 6181 RUN; `mario_sprite` vbcc = asm = referencia 6184/6184 | 6177 RUN; `--spr` se colgaba en cloud (P62) |
| capturas del replay (FS-UAE), fallos que no explica un vecino | frame 6000: fondo 30, Mario 0; frame 7000: fondo 16, Mario 0 (reescalado ×2,125) | WinUAE: 0 / 0 |
| `inputtest.py` / `diag_read.py --sim` | 35/35 · TODO OK | — |
| FS-UAE (`regress.py --level --emu logic,scrollbench,scrollimg`) | `logicbench` 23,2 % corriendo / 23,4 % saltando (256 px); `scroll.s -DBENCH -DSPEED=4`: con columna media 14,9 %, **máx. 78,8 %** (s = 4584), sin columna media 12,9 %, máx. 31,1 % (s = 4820); `scroll_check --mid` (fallos que no explica un vecino) 500: 15, 1000: 32, 1700: 31, 2500: 1, 3500: **6**, 4500: 47 | 26,5 / 26,9 % y 25,2 % / 307,5 % (320 px); imagen 74 / 31 / 94 / 46 / 72 / 127 (con el origen de 320 px: P59 y el arreglo de `scroll_check`) |

### 1.4 Qué se puede hacer en cada entorno

Igual que antes, con dos cambios: **en cloud ya se pueden grabar partidas**
(snesorc, con guion; no hace falta el usuario) y el juego arma en cloud
(`mkmario.py` usa `work/smw.sfc` si no está la ROM de la PC).

| tarea | Claude cloud | PC local (Windows) |
|---|---|---|
| compilar (vasm, vbcc, gcc) | sí (`setup_cloud.sh`) | sí |
| verificar contra el oráculo | sí | sí |
| **grabar oráculos** | **sí, con guion** (`snesorc_setup.sh`, `snesorc_make.sh`) | sí, jugando (`smwrecomp` + `oamrec.py`) |
| medir en cycle-exact | FS-UAE + AROS; varias capturas, de a una (P76) | WinUAE + KS 1.2 |
| probar el arranque en KS 1.2 y el teclado | **no** | sí |
| comparar contra `SuperMarioWorldMap02.png` | **no** | sí |

Notas de la PC del 2026-09-27 (gcc de msys64 primero en el PATH, el sdist de
`machine68k`, el vbcc de 2022, `scroll_check.py --sc 2`): siguen valiendo,
ver el historial de este fichero.

### 1.5 Arranque rápido en cloud

```bash
sh tools/setup_cloud.sh               # ~2 min la primera vez, ~15 s con caché
export VBCC=~/vbcc PY=python3
python3 tools/lint_port.py && python3 tools/regress.py        # ~1 min: PC + 68000 + 5 oráculos
sh tools/snesorc_setup.sh             # opcional: el generador de oráculos (work/snesorc)
sh tools/game_build.sh && python3 tools/gamecheck.py --spr    # el juego (replay) en Unicorn
GDEFS=" " OUT=work/live sh tools/game_build.sh                # el de jugar
```

### 1.6 Pendiente del usuario o de la PC

1. **Jugar `work/live/game.adf` en WinUAE con teclado** (KS 1.2, 512 KB
   chip + 512 KB slow, `work/play.uae`). Nunca se probó con teclas: el
   modo diagnóstico (ESPACIO cambia de página; RETURN, Z, A o el botón
   vuelven a empezar), el handshake del teclado y los dobles saltos (P55).
   **Esperado:** si Mario se queda quieto al empezar, el Koopa deslizante
   (que se simula pero todavía no se dibuja) lo mata en el frame 219, y el
   diagnóstico muestra `MOTIVO 10 DANO`, `FRAME 00DB`. El juego original
   hace lo mismo en el mismo frame (`$71` = 9; comprobado con snesorc); lo
   que falta es la animación de muerte (P8, Z1) y dibujar al Koopa (9.2).
   Si se congela: captura de la **página 2** y
   `python3 tools/diag_read.py --shot X.png --repro --bin work/live/game.bin`
   (el `game.bin` del ADF que se usó) dice en qué frame y por qué.
2. **PC:** Etapa 7 (`cmp_ref.py` del blob de la etapa 5 contra la referencia).
3. **Usuario, opcional:** probar en una A500 real.
4. Las grabaciones de la 8.1 ya no necesitan al usuario (snesorc). El
   audio de referencia de la 11 tampoco: `snesorc` lleva el driver de
   snesrev y puede registrar las escrituras al DSP (SUBAGENTES A0).
5. ~~Mergear `claude/brave-ritchie-mm5o6r` a `master`~~: hecho el 2026-09-30.

### 1.8 Lo que falta, en sesiones (estimado el 2026-09-30)

Una "sesión" = como la del 2026-09-30: un coordinador + 3-5 subagentes,
unas horas. Detalle de cada punto en §10; tarjetas en `SUBAGENTES.md`.

| # | bloque | sesiones | depende de |
|---|---|---|---|
| 1 | Ola 1: medir el frame entero (O1), grabaciones de snesorc (R0-R6), cargas "tarde" + LNS (S1a+S2), `f7f4` en asm, un fichero por sprite | 1 | — |
| 2 | **50 Hz: scroll** (edición en el sitio, EDF, segmentos compartidos, un plan por sentido) + **la cámara vertical de YI1** (S8) | 2-3 | 1 |
| 3 | **50 Hz: lógica** (asm donde marca el perfil, descartes rápidos) y Mario sin redibujar | 1 | 1 |
| 4 | Sprites que faltan: lógica (Chuck, caparazones, meta, power-ups, bolas de fuego, animaciones de Mario, monedas, reserva) | 2 | 1 |
| 5 | Sprites: dibujo en la Amiga (conversor, asignador, copper, bobs) | 2-3 | 2, 4 |
| 6 | Carga y memoria (tablas de CPU a slow RAM, vlink, loader, compresión) | 1-2 | — |
| 7 | HUD, cajas de mensaje y pausa | 1 | 6 |
| 8 | Audio (captura del DSP, muestras, secuenciador, efectos) | 2 | 6 |
| 9 | Zona de la tubería (D16) | 1 | 6 |
| 10 | Pulido: muerte, punto medio, meta, tiempo, fundidos, prioridad del poste; replay hasta la meta | 1-2 | 4 |
| 11 | Segunda ronda de optimización con todo junto (sprites dibujados + HUD + audio suman coste) | 1 | 5, 7, 8 |
| 12 | Cierre: pruebas en WinUAE KS 1.2/1.3, arreglos de lo que encuentre el usuario, ADF final | 1 | todo |
| | **total, bloque tras bloque** | **16-20** | |

Los bloques se solapan: repartidos en **olas** con 3-5 subagentes a la vez
(`SUBAGENTES.md` §3, donde está cada ola descrita con sus tarjetas y su
criterio de cierre) salen **12-15 sesiones**:

| ola | qué | sesiones |
|---|---|---|
| 1 | medir el frame entero y grabar todo lo que falta; primeras bajas del scroll | 1 |
| 2 | 50 Hz (1): lo más caro según la medida; Chuck; descriptor de nivel | 1-2 |
| 3 | 50 Hz (2): lógica ≤ 40 %, EDF del scroll; diseños del dibujo y del audio | 2 |
| 4 | motores: copper definitivo + cámara vertical, vlink, conversores, resto de la lógica de sprites, zona de la tubería en datos | 2-3 |
| 5 | integraciones: enemigos en pantalla, loader, HUD con números, música | 2 |
| 6 | el juego completo: bobs, barra, efectos, muerte, punto medio, meta, zona de la tubería, replay hasta la meta | 2-3 |
| 7 | segunda ronda de 50 Hz con todo junto | 1 |
| 8 | cierre: KS 1.2/1.3, arreglos, ADF final | 1 |
| | **total** | **12-15** (16-20 si hay que serializar) |

En paralelo, del lado del usuario (PC): jugar cada ADF nuevo en WinUAE
(U1), la Etapa 7 contra la referencia (U2) y, si quiere, una A500 real.
El riesgo que más puede mover la cuenta es el 2 (el scroll a 50 Hz: la
sesión del 2026-09-30 no lo cerró); si después de 3 sesiones no entra, se
le llevan los números al usuario (D1).

### Lo último que se hizo y lo siguiente

- **Estado general (2026-10-01, fin del día):** la lógica está verificada
  contra la SNES (Mario exacto en todos los oráculos, con crecer, encoger y
  morir; ~15 tipos de sprite exactos; replay del juego 0 frames distintos),
  pero **el rendimiento no llega a 50 Hz en los peores frames** y casi todo
  lo visible y audible además de Mario falta. Musashi sin DMA: juego entero
  peor frame 118 724 (≈ 84 %; en el día bajó de ≈ 95 %), media ≈ 28 %;
  scroll peor frame ≈ 75 % a la vuelta y ≈ 57 % a la ida (objetivo ≤ 25 %);
  lógica de sprites ≈ 27,5 % (objetivo ≤ 40 %, falta confirmarlo en
  WinUAE). Con el DMA (~×1,3) los peores frames siguen pasando del frame:
  50 Hz casi siempre, con tirones puntuales. Del plan de 16-20 olas,
  aproximadamente la mitad del trabajo; falta lo más visible.
- **Orden para la próxima sesión:** (1) capturas WinUAE de SX/SX2 contra
  master (ida 500-4500 y vuelta; ojo P94 y `shot.ps1` no en paralelo en el
  mismo worktree); (2) **O4: informe D1 para el usuario** (aceptar frames
  lentos, 25 Hz en tramos, o seguir optimizando, con números de WinUAE),
  antes de invertir más en el scroll; (3) **9.2, dibujar los sprites del
  nivel** (G1-G2 con opus; hoy los enemigos existen en la lógica pero no se
  ven); (4) **Z1**, reiniciar el nivel tras la muerte (hoy congela).
- **Después, por bloques:** S5/S7 (pico de los postes de la meta a 4 px);
  lógica que falta (P7 bolas de fuego, P9 monedas, P10 reserva, capa;
  RC: `pw_3up`, moneda de Yoshi 4; X1 puede acelerarlo); partida completa
  (Z1-Z5: muerte, punto medio, meta, tiempo, fundidos); HUD (H1-H5) y audio
  (A0-A8, verificado contra el DSP); la zona de la tubería (T1-T3); carga y
  memoria (135 KB de tablas a slow, C2 vlink, C3 compresión, C4 loader);
  segunda ronda de optimización con todo junto; Z7 (WinUAE KS 1.2/1.3,
  ADF final).

- **2026-10-03 (PC):** de la investigación (`docs/investigacion-ports.md`
  §14.10): `mario_draw` solo escribe la paleta de Mario si cambió y los
  punteros de sprite una vez por lista → `game.total` en Musashi peor
  frame 118 724 → **117 796**, media 39 978 → 39 053 (`baseline_pc.json`);
  el sprite vacío pasa a ser válido (`$1905,$1A00,0,0,0,0`). Imagen
  idéntica en WinUAE. El resto de lo investigado confirma lo que ya se
  hace o queda como candidato (§14.10).
- **2026-10-03 (PC), tarjetas L4, V3 y V2** (`docs/investigacion-ports.md`
  §14.10): **L4 descartada** (la RAM con XOR 1 ganaría ~1 % de media y
  perdería 2,7 % en el peor caso, medido contando accesos en los 6836
  frames de `game`); **V3** hecha: `tools/asmlint_port.py` en
  `lint_port.py` (encontró dos cabeceras mal: `columns` destruye d6 y
  `txt_ch` devuelve a1; corregidas); **V2** hecha: `tools/coverage.py` →
  `docs/cobertura.md` (80 % de las líneas del C corren con las 27
  grabaciones; lo que falta y le importa a YI1, en sus notas: salto con
  giro sobre enemigos, matar al Chuck, mirar arriba, caparazones).
- **2026-10-03 (PC), O4:** `docs/informe-d1.md`. En el replay (Musashi)
  0 frames pasan de 20 ms con DMA ×1,2 y 3 de 6310 con ×1,3 (14 si se
  reserva el 15 % para sprites, HUD y audio); lo que sigue sin entrar es
  el scroll hacia atrás en s ≈ 4580 (74,7 % solo). Recomendación: medir
  en WinUAE, **no** 25 Hz, O5 como red de seguridad y una sesión acotada
  al pico de la vuelta. **Decidido por el usuario: O5 como red de seguridad**
  (sin 25 Hz). Cómo automatizar 9.2: `docs/automatizar-9.2.md`.
- **Dónde estamos en las olas (2026-10-03):** olas 1 y 2 cerradas (por
  uso; de la 1 quedan grabaciones sueltas). **Ola 3 a medias:** hechas C1,
  L1b+L1d (L2 probada, no ganó), O4 (adelantada; con O5 decidida), más
  P6, P8, SX 1-2 y RC adelantadas de la ola 4; faltan **S5** (EDF), **G1 →
  G2**, H1, A1, A2 y R7. Ya está hecho de la ola 4: P3-P6 y P8. Van
  ~5 de 12-15 sesiones.

- **2026-10-04, ola 3 integrada:** O5 (render desacoplado, por defecto; `-DNODECOUPLE` = bucle viejo; YI1: 0 frames lógicos perdidos, 11 imágenes salteadas; stress_back: 127, rachas ≤ 2), G8 (OAM de Rex/`SubSprGfx2Entry1` exacta, solo con `SPR_OAM` en el PC), G3a (`mksprgfx.py --selftest` 226/226), G1+G0 (`docs/estudio-g1-g0.md`: 2-3 columnas libres, Rex 2 columnas, recargar por copper; G0 sin medir en WinUAE), R10 (`spin_kill`, `chuck_kill`, `turn_block`). O1 en WinUAE: `docs/informe-d1.md` §5. Trampas P96-P101. **Falta:** G2 (diseño), notas a mano de `docs/cobertura.md`, capturas SX/SX2.

### Continuación de la ola 3 (2026-10-05) — EMPEZAR POR AQUÍ

La ola 3 (`ab51d16`) está integrada. La continuación usa
`tools/baseline_pc.json` **sin modificarlo**. El plan del 2026-10-03 de
abajo queda como referencia histórica.

**Integrado y verificado:**

1. **G2:** [diseño e interfaces](docs/diseno-9.2.md), resumido en §10.6.
   OAM en la lógica original; foto O5 inmutable con propiedad de fichas;
   Mario reservado, Banzai bob y cola explícita para excedentes. El banco
   DMA propuesto, segundo PF1 y audio requieren liberar tablas CPU de chip
   (C2/C4); no caben todos en el mapa actual.
2. **G0 real a 256 px:** [banco y resultados](docs/medida-g0.md).
   Poses compartidas exactas en ocho canales con PT en la línea anterior
   y POS/CTL después del control DMA. PT desde h=$D8 llega tarde.
   Cadena gap 1 exacta; copia de 1408 B cuesta ~7,5 % activo, ~4,9 % VBlank.
   Carga sintética 8+6 MOVE: todavía falta demostrar ventanas con el copper
   real, audio y blitter concurrentes (G5/G7).
3. **OAM 68000:** `CDEFS='-DNOOAM -DSPR_OAM'`, opción coherente C/asm;
   [puertas y comandos](docs/oam-amiga.md). Rex YI1 2671/2671, RAM/mapa/ABI
   exactos; juego integrado 0 frames distintos. Máximo de lógica
   39 026 → 46 718 ciclos (+19,7 % relativo, sin DMA). Limpieza completa
   de fichas y marcas. Corregidas llamadas lejanas absolutas y añadido
   `piccheck.py` a ambos builds (P102). **Sigue apagado por defecto** hasta
   medir O5/DMA integrado; todavía no dibuja enemigos.
4. **Cobertura manual actualizada** con R10 y **G3a en `regress.py`**, también
   en `--quick`. Sin OAM grabada avisa y salta; datos presentes corruptos
   fallan. Autoprueba local: 227/227 poses, 512 fichas × cuatro flips.

**En validación:** SX/SX2, seis posiciones de ida y seis de vuelta,
baseline anterior a SX contra actual, capturas cycle-exact con historial
de scroll y comprobación temporal. Se detectaron seis píxeles alternantes
en s=1700: aceleración del copper después de DDFSTOP, invisible al modelo
uniforme anterior (P51). El arreglo y el banco están sin commitear en
`wt-g0-next` y `wt-gfx-regress-next` (§1.1). No dar la puerta por cerrada
hasta comprobar el arreglo.

**Lo siguiente, en orden:** cerrar SX/SX2; medir OAM/O5 integrado antes de
activarlo por defecto; **G3 final** (poses recortadas, remapeo de colores,
banco y máscaras) → **G4 + G6** (asignador y reconstrucción exacta) →
G5 + G9. C2/C4 antes de añadir el segundo PF1 y G7. Z1, H1 y A1/A2 según
sus dependencias. S5 sigue acotado al pico de vuelta s≈4580 y por detrás
del dibujo: O5 evita que ese render atrase la lógica.

Notas: O5 es el modo por defecto (`-DNODECOUPLE` = bucle viejo); si cambia
`scroll_frame`, sincronizar `dc_loop` y `gb_scroll_frame` (P97).
Regresión PC: `python tools/lint_port.py` y
`python tools/regress.py --baseline tools/baseline_pc.json --level`.
Las capturas deben tener perfiles/archivos privados por worker, máximo
tres instancias; cerrar solo el PID/ventana propios.

### Próxima sesión (plan, 2026-10-03)

Cerrar la ola 3 con el camino de `docs/automatizar-9.2.md` y la red de
seguridad O5. Modelos según la preferencia del usuario: optimización →
Opus (medium), grabaciones → Sonnet (low), el resto → Sonnet (high).
Cada subagente en su worktree (`tools/wt_new.sh`), con la tarjeta de
`SUBAGENTES.md`. Ficheros sin cruces entre agentes.

| quién | tarjeta | modelo | toca | puerta |
|---|---|---|---|---|
| coordinador, antes de lanzar | **O1 en WinUAE**: `GDEFS="-DREPLAY -DBENCH" OUT=work/bench sh tools/game_build.sh`, `shot.ps1 -Exact -Wait 220`, `game_read.py --auto` → factor real del DMA en `docs/informe-d1.md`; capturas SX/SX2 contra master | — | docs | tabla en el informe |
| agente 1 | **O5**: render desacoplado (red de seguridad, decidido) | Opus medium | `player/game.s` | replay idéntico en `gamecheck` (0 distintos); frames de imagen perdidos contados en el replay y en `stress_*`; imagen igual en WinUAE en los frames que no se pierden |
| agente 2 | **G1 + G0**: estudios con 256 px y medir encadenar por DMA contra `SPRxPT` por copper | Sonnet high | solo `tools/` (lectura) + informe | tabla de líneas que piden más columnas y decisión G0 con números |
| agente 3 | **G8 (nueva)**: `RexGfxRt` + `SubSprGfx2Entry1` escribiendo la OAM y el campo OAM en el verificador | Opus medium | `player/spr_rex.c`, `player/sprgfx.c` (nuevo), el verificador | OAM = grabación de snesorc en `oracle_yi1` en los frames con Rex; `level_frame` medido |
| agente 4 | **G3a**: `tools/mksprgfx.py` (GFX 20 → frames de sprite + máscara), sin formato final (lo fija G2) | Sonnet high | `tools/mksprgfx.py` | `--selftest` de ida y vuelta en todas las poses de las grabaciones |
| agente 5 | **R10 (nueva)**: grabaciones de los huecos de `docs/cobertura.md` | Sonnet low | `tools/snesorc/*.orc`, `work/oracle_*.txt` | `coverage.py` deja de listar `spr_spin_kill`, `chuck_die`, mirar arriba y el aturdimiento del caparazón |

Al cerrar: integrar (§2.4 de `SUBAGENTES.md`), `lint_port` + `regress`,
**G2** (diseño del dibujo; lo escribe el coordinador con G1, G0, G8 y
G3a) y, si sobra tiempo, **S5 acotado** al pico de la vuelta (s ≈ 4580,
Opus medium, `scroll.s`; una sesión como máximo, ver el informe D1). Lo que
sigue después: G4 + G6 (asignador y su verificador), Z1 (reinicio tras la
muerte), H1, A1, A2.

- **Historial de las olas 1-3 y del 2026-09-30** (qué se integró, números de
  cada paso, ramas, notas para las grabaciones): textual en
  `docs/historia.md`, sección "ROADMAP: el día a día del 2026-09-30 al
  2026-10-01".

---

## 2. El presupuesto del frame (lo que manda)

Un frame PAL son 20 ms, ~141 800 ciclos de CPU. Hoy, medido en cycle-exact
salvo donde se indica:

| componente | medido | objetivo propuesto (peor frame) | fuente |
|---|---|---|---|
| scroll: `build_mid` + columna nueva + lista del copper | ida, 4 px/frame, FS-UAE: media 14,9 %, **máx. 78,8 %** (s = 4584). **Vuelta**, 2 px/frame, Musashi (cota inferior, ×~1,3 en la Amiga): media 36,6 %, **máx. 94,8 %** (s = 2832) (2026-09-30, P72) | **≤ 25 %** en el peor frame, en los dos sentidos | `scroll.s -DBENCH`, `scrollprof.py` |
| lógica `level_frame` sin sprites | 20,2 % / 20,5 % (WinUAE, 256 px, tras la 8.2) | — | `logicbench` |
| lógica con sprites | peor frame 40,1 % (WinUAE, 2026-09-27); con los sprites de la 9.1, Musashi 43 116 → 45 896 ciclos: **~45 % estimado** | lógica total **≤ 40 %** | `logicbench -DWORST`, `m68kverify --sprites` |
| Mario en sprites de hardware (`mspr_draw`) | ~10 400 ciclos ≈ 7,3 % (Musashi) | — | `gamecheck.py --engine musashi` |
| dibujo de los sprites del nivel (sprites de hardware + copper) | sin medir | ≤ 10 % | — |
| bobs en PF1 (solo si un objeto pasa a bob) | 22,7-33,8 % (Banzai + 4 Rex, `bench2.s` W3) | caso raro, ver 9.2 | `bench2.s` |
| HUD | sin medir | ≤ 2 % | — |
| audio | sin medir | ≤ 3 % (D5) | — |
| **margen** | — | **≥ 10 %** | — |

**Hoy no entra a 50 Hz en el peor caso.** Por partes, el peor frame suma
scroll (79 % a la ida, ~95 % o más a la vuelta) + lógica con sprites (~45 %)
+ Mario (7 %): bastante más del 100 %, sin dibujar los sprites del nivel,
sin HUD y sin audio. De media: scroll ~15 % a la ida (~37 % a la vuelta) +
lógica ~23-30 % + Mario 7 %. Por eso la 6.4 va **antes** que las etapas que
suman coste (9.2, 10 y 11), y la compuerta D1 se prepara ya con estos
números (6b.6).

**Compuerta D1 [usuario]:** después de las Etapas 6.4, 8.2 y la 6b se mide el
**peor frame del juego integrado**. Si pasa del 100 %, se le presentan al
usuario estas opciones con números: (1) otra ronda de optimización, con
ensamblador a mano en las sondas de colisión y en `build_mid`; (2) dibujo a
25 Hz con la lógica a 50 Hz, que ahorra scroll y copper pero no lógica; (3)
recortar el alcance, por ejemplo menos sprites a la vez. Mover el código a
slow RAM **no** acelera (P29).

---

## 3. Decisiones

Cerradas por el usuario el 2026-09-26: se aceptan las recomendaciones, con
el **teclado primero** en los controles. El criterio general es el mejor
equilibrio entre 1:1 y coste. Solo queda abierta la compuerta D1.

| ID | Decisión | Qué se hace | Consecuencias | Etapa |
|---|---|---|---|---|
| D1 | 50 Hz o no | **cerrada (usuario, 2026-09-30): 50 Hz, haciendo todo lo posible**; "si no se puede, no se puede" | la optimización (§9, §10.1-10.3) va antes que todo lo que suma coste. Si agotadas las ideas el peor frame sigue sin entrar, se le presentan al usuario los números y el plan B (dibujo a 25 Hz) | todas |
| **D15** | Velocidad: el ROM (U) es NTSC y la Amiga va a 50 Hz | **cerrada (usuario, 2026-09-30): se acepta** el 83 % de velocidad, como la SNES PAL (§10.12) | nada que hacer; la música mantiene el tempo (tick por CIA) | — |
| **D16** | ¿La zona de la tubería (`obj-1.lv`) entra en el alcance? | **cerrada (usuario, 2026-09-30): entra** (§10.10) | conversión de una segunda zona, tuberías y transición | 12 |
| **D5** | Música | **secuenciador propio** que lee las secuencias N-SPC de SMW convertidas offline a un formato compacto de eventos (no MOD) | Conserva glissandos, vibrato, envolventes (ADSR aproximado por tick) y el tempo del SPC700 (tick por timer de CIA). **Sin mezcla por CPU**: cada voz va directa a un canal de Paula, 3 de música + 1 de efectos, con prioridad por tema; el eco se omite. Límites: ≤ 64 KB de muestras en chip RAM y **≤ 3 % de CPU** medido. **Verificación** (como sonic2mod de reassembler): contra el registro de escrituras al DSP de `snesorc` en la partida del oráculo, nota por nota, con un informe por tema en `docs/audio/` (SUBAGENTES A0, A3, A6, A8) | 11 |
| **D10** | Ancho de pantalla | **256 px**, como la SNES | DIW centrada; el fetch empieza más tarde, así que vuelve el sprite 7 (4 columnas adosadas); 20 % menos de DMA de planos; la cámara y la aparición de enemigos quedan 1:1 | 6.1 |
| **D11** | HUD | **superpuesto (overlay)**, como la SNES | En las líneas del HUD el copper apunta PF1 a un bitmap fijo del HUD y PF2 sigue con su paralaje. Si en esas líneas aparece capa 1 del nivel, antes de renunciar al overlay se busca otra variante que lo conserve (10.1) y se consulta | 10 |
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

## 4. Orden de trabajo

```
Etapa 0 (consolidar el WIP)
   ├── Etapa 6.1-6.4 (scroll: 256 px, ida y vuelta, cámara, coste) ──┐
   ├── Etapa 8.2 (optimizar la lógica en C nativo)  ─────────────────┤
   └── Etapa 9.1 (lógica de sprites; en paralelo)                    │
                                                                     ▼
                         Etapa 6b (INTEGRACIÓN: primer ADF jugable) → compuerta D1
                                                                     ▼
                      Etapa 9.2 (dibujar sprites) → 10 (HUD) → 11 (audio) → 12 (pulido)

En la PC, cuando se pueda: 6.5, 7 y 8.1 (grabación única), y el arranque en KS 1.2.
```

Las ramas de un mismo nivel se pueden repartir entre agentes o subagentes,
siempre que no toquen los mismos ficheros. La 8.2 y la 9.1 tocan los dos
`player/*.c`, así que se coordinan: `msprite.c` es de la 9.1 y el resto de la
8.2.

---

## 5. Etapas

El paso a paso de cada etapa (dónde, qué hacer, hecho cuando), escrito el
2026-09-26, está textual en **`docs/etapas.md`**. El estado de cada una está
en §1.2; lo que falta, con cómo lo haría, en §10 (más nuevo: si discrepan,
manda §10). Etapas:

- Etapa 0 — Consolidar el WIP
- Etapa 6 — Terminar el scroll
- Etapa 7 — Capa 2 contra la referencia
- Etapa 8 — Mario: cerrar la 8c y bajar el coste
- Etapa 6b — Integración: el primer ADF jugable
- Etapa 9 — Sprites del nivel
- Etapa 10 — HUD
- Etapa 11 — Audio (D5)
- Etapa 12 — Pulido y entrega

---

## 6. Riesgos principales

| riesgo | señal | mitigación |
|---|---|---|
| El frame no entra a 50 Hz | §2: la suma pasa del 100 % | optimizar antes de sumar coste (6.4, 8.2); compuerta D1 |
| Picos escondidos | un frame suelto muy caro (hoy: 307 % en s = 4504 en el scroll) que la media no muestra | medir siempre el máximo **y dónde ocurre**; los bancos descartan solo los frames de arranque |
| Faltan columnas de sprites | con `DDFSTRT $30` solo quedan 3 adosadas | D10 = 256 px; bob en PF1 (`d8demote`) |
| vbcc compila mal | `m68kverify` llega al tope de 10 M ciclos o difiere de `marioverify` | V1 siempre (P38) |
| Datos del C > 32 KB con `-sd` | `logicbench_build.sh` falla o hay referencias absolutas | D13: enlazado absoluto con vlink (6b.1) |
| Índices de 16 bits con signo | escrituras 64 KB antes a partir de 32 KB | `(An,Dn.l)` con `moveq #0` antes (P40) |
| El modelo de tiempos del copper | cargas corridas unos píxeles | calibrar con `copcal` en cada pantalla nueva (0.4, 6.1); los WAIT cuestan ranura (P39) |
| El oráculo no cubre un caso | un sprite o una pendiente sin frames que verificar | sesión de grabación única (8.1) |
| Chip RAM | hoy ≈ 395 KB con todo `yi1_s.dat` en chip; + audio (64 KB) + sprites (~30 KB) no entra | D13: las 7 tablas de CPU de `yi1_s.dat` (129 KB) a `$C00000` (§10.7) |
| La cámara vertical de YI1 | Mario se corre respecto del fondo cuando la cámara sube (`Bg1VOfs` < `$C0`) | §10.2b: segmentos por línea del nivel y la v de los WAIT |
| Muestras de audio | todas las BRR son 92 KB ≈ 164 KB de PCM | solo las del tema y los efectos; bajar la frecuencia donde haga falta (§10.9) |
| Lo que no cubre ningún oráculo | un camino del ROM que nadie recorrió (P69: la cámara vertical) | grabarlo con snesorc antes de darlo por verificado |

---

## 7. Plantilla de handoff (para el que cierra la sesión)

Reemplaza §1 entero. Tiene que caber en una pantalla o dos.

```markdown
## 1. Handoff (estado al AAAA-MM-DD)

### 1.1 Ramas
rama base, commit de la cabeza, qué hay sin mergear, si queda algo WIP y por qué.

### 1.2 Estado por etapa
la tabla, con cifras medidas (no "funciona"): %, px, frames, ciclos.

### 1.3 Números de regresión
la tabla, con los valores nuevos donde cambiaron y la fecha.

### 1.4 / 1.5
solo si cambió el entorno o el arranque.

### 1.6 Pendiente del usuario o de la PC
decisiones, grabaciones y pruebas que el agente no puede hacer.

### Lo último que se hizo y lo siguiente
3-6 viñetas: paso de §5 en el que se quedó, qué falta para cerrarlo, el
comando exacto para retomar, y las hipótesis sin comprobar (marcadas así).
```

Reglas: nada sin commitear al cerrar (si queda a medias, commit `WIP:` que
diga qué falta verificar); cifras con su fuente (herramienta y emulador); lo
estimado, marcado como **estimado**; lo que se perdió con el contenedor
(scripts en `/tmp`), recreado en `tools/` o anotado.

---

## 8. Comprobaciones: los scripts

Todo cambio pasa por estos scripts **antes del commit**. Corren en cloud y
en la PC; solo necesitan la biblioteca estándar de Python, salvo lo que se
indica.

| script | qué comprueba | cuándo | tiempo |
|---|---|---|---|
| `tools/lint_port.py` | reglas que el compilador no ve. **Errores**: R9 (nada derivado de la ROM en git), `float`/`double`, `malloc`, `#include <...>` fuera de un `#if`, el patrón de P38 (`p = ram + x` indexado con `p[wm_X]`). **V3**: una rutina asm que cambia un registro que su cabecera no declara (`registros destruidos` / `salida`; las `public _xxx`, contra la ABI de vbcc), con `tools/asmlint_port.py`. **Avisos**: `(An,Dn.w)` en asm (P40; una línea revisada se marca con `; P40 ok`), `int` a secas y registros declarados de más (V3) | antes de cada commit | 2 s |
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

## 9. Optimización: plan e ideas (2026-09-30)

> **Ver también `docs/investigacion-ports.md` (2026-10-03):** qué hicieron
> otros ports y juegos de A500 con estos mismos problemas, con tarjetas
> nuevas (O5, V1-V3, L4, L5, G0, E2). Corrige §9.6: la cola de blits por
> interrupción no ganó en una A500 de serie (medido por AmiGalaga).

**Método (siempre):** medir el peor frame y **dónde** ocurre → cambiar
**una** cosa → verificar la semántica (`regress.py`; el C con `abcheck.py`;
`scroll.s` con `scrollsim.py --ret` + `imgdiff.py`) → medir en cycle-exact
(`regress.py --emu`). Se optimiza el **peor frame**, no la media: el frame
que no entra en 20 ms es el que se nota.

**Regla de conversión** (medida en la 8.2 y en la 6.4): en la A500, con el
DMA de 6 planos, un trabajo cuesta ~1,3-1,4 veces lo que da Musashi.
O sea, **~1 000-1 100 ciclos de Musashi por cada 1 % de frame** en la
Amiga (un frame PAL son 141 876 ciclos; en la parte visible de cada línea
el DMA de planos se lleva la mitad de las ranuras pares).

### 9.0 Dónde estamos y a dónde hay que llegar

Peor frame por partes (el del juego entero sin medir: es el paso O1):

| parte | peor frame hoy | dónde | objetivo | falta |
|---|---|---|---|---|
| scroll a la ida (`build_mid` + columna) | 78,8 % (FS-UAE, 4 px/frame) | s = 4584 (postes de la meta) | ≤ 25 % | −54 puntos |
| scroll a la vuelta | 94,8 % en Musashi (≈ 125 % en la Amiga, **estimado**) | s = 2832 | ≤ 25 % | −100 puntos |
| lógica con sprites (`level_frame`) | 45 896 ciclos en Musashi ≈ 45 % | frame 9714 (2 pirañas, Rex, `$8E`, `$C7`) | ≤ 40 % | −6 000 ciclos |
| Mario en sprites (`mspr_draw`) | ~10 400 ciclos ≈ 7,3 % | cada cambio de pose | ≤ 3 % | −4 000 ciclos |
| sprites del nivel (9.2) | sin hacer | — | ≤ 8 % | diseñarlo barato (9.5) |
| HUD / audio | sin hacer | — | ≤ 2 % / ≤ 3 % | — |
| **margen** | — | — | **≥ 10 %** | — |

La suma de los objetivos da 81 % + margen. Hoy el peor caso pasa del
130 %. **Lo que manda es el scroll**; la lógica está cerca.

### 9.1 Paso 0: medir el frame entero (O1-O3)

Sin esto se optimiza a ciegas; además es la **6b.6 (compuerta D1)**.

- **O1. `game.s -DBENCH`:** timer A de CIA-B al principio y al final de
  cada parte (entrada, `level_frame`, `mspr_draw`, `scroll_frame`:
  columna, `build_mid`, lista), **por frame**, en el replay. Se guardan el
  peor frame de cada parte y el del total, con su frame y su s, y se
  escriben en pantalla como bits (el método de `bench.s`), con un lector
  `tools/game_read.py --auto`. Enganchar a `regress.py --emu game`.
- **O2. Escenarios de estrés con snesorc:** `oracle_yi1` no recorre los
  peores casos. Guiones `.orc` nuevos:
  - la cámara volviendo a toda velocidad sobre s ≈ 2600-2900 y 4100-4800,
    las zonas caras del scroll;
  - Banzai + 4 Rex + Mario a la vez en pantalla;
  - las 2 pirañas del frame 9714 con Mario corriendo.

  Pasarlos por `m68kverify.py --replay` → `game.s -DREPLAY -DBENCH`.
- **O3. En `regress.py`:** los ciclos del peor frame por parte en Musashi
  (`gamecheck.py --engine musashi`, que tiene que aprender a correr
  también `scroll_frame`) y el scroll en los **dos sentidos**
  (`scrollprof.py -D RETURN=4864 --stopx 0`). Hoy `-DBENCH` solo mide la
  ida (P72).

### 9.2 Scroll: `build_mid` (lo más grande)

Reparto del peor frame de la ida (s = 4580, 76 850 ciclos en Musashi, ver
Etapa 6.4): 55 líneas reescritas enteras, 276 cargas (~124 ciclos cada
una) + ~520 por línea + ~7 800 para recorrer las 108 líneas de LNS.
Por qué se reescriben:

| motivo | líneas |
|---|---|
| una carga "tarde" (se reescribe en **todos** los frames, P50) | 24 |
| entra una carga por la derecha | 25 |
| caduca una carga | 6 |

A la vuelta, casi todo se reescribe en cada paso (P72). Ideas, de más
barata a más cara:

- **S1. Las cargas "tarde", arregladas en origen.** Son 34, en
  x ≈ 4817-4861 (los postes de la meta), y cada una fuerza su línea unos 128
  frames seguidos.
  - (a) Clasificación fija, con la línea canónica (P71) y la h en celdas de
    8 px: la línea se reescribe cada 8 px de s, no en cada frame.
  - (b) En `mkleveld.py`/`mkscroll.py`, repartir los registros cerca de los
    postes para que las ventanas se puedan cumplir. Si hace falta, aceptar
    un derrame de 1 px donde no se ve (P44).
  - (c) Dibujar los postes con 2 sprites de hardware adosados (15
    colores). En la meta casi no hay enemigos: saca esas cargas del copper.
  - Estimado: −20-30 % del peor frame de la ida.
- **S2. Recorrer LNS por grupos de 16 líneas** con el mínimo de cada grupo
  (el `gmin_a/b` del WIP viejo): de ~7 800 a ~1 000 ciclos en los frames en
  que casi no cambia nada.
- **S3. Escribir cada cambio una sola vez.** Hoy cada lista (A y B) tiene
  su sombra (`V_LSA`/`V_LSB`) y **cada línea que cambia se reescribe dos
  veces**: en la lista de este frame y en la del siguiente. Como un
  segmento vale para un intervalo de s, las dos listas pueden compartirlo:
  un pool con 2 ranuras por línea; la que cambia se escribe en la ranura
  libre y las dos listas se reenganchan (2 palabras cada una). La trampa:
  el salto al segmento siguiente está **dentro** del segmento, así que
  compartirlo obliga a sacar los saltos a una "columna vertebral" por
  lista, que gasta MOVE del copper en el borrado. Medir primero con
  `copcal` si entran (P39, P43, P46). Estimado: hasta −50 % de
  `build_mid` en régimen.
- **S4. Editar en el sitio en vez de reescribir la línea** (el diseño de
  `tools/wip64/`): rebase (solo el byte h de cada WAIT), append y truncado
  por la derecha. En el modelo: ida 48,6 → 38 %, vuelta 78,8 → 56 %. La
  imagen queda igual por construcción si la clasificación "tarde" es fija.
- **S5. Repartir entre frames con un presupuesto.** Cada evento tiene una
  holgura de b + 6 px, así que no hace falta atenderlo en el frame en que
  aparece. Una cola por plazo (EDF) con un tope de ciclos por frame: lo
  urgente primero, el resto después. Aplana el pico hacia la media (hoy
  14,9 % a la ida). Las cargas muertas se neutralizan en el sitio (el MOVE
  pasa a `$1FE`) en vez de reescribir.
- **S6. Un plan por sentido.** El plan pone las cargas lo antes posible
  (a ≈ 0), así que sirve hacia la derecha y casi nada hacia la izquierda
  (P72). Un segundo plan con las cargas lo más tarde posible (ALAP) para
  cuando la cámara va a la izquierda, o las cargas en el centro de su
  ventana para los dos sentidos. Cuesta otro MLD en slow RAM.
- **S7. Menos cargas desde el origen.** Cada carga que no existe ahorra
  CPU y ranuras del copper. Mejor asignación de registros en
  `mkleveld.py` (intervalos que se reusan, preferir el registro que ya
  tiene el color) y más variantes de bloque. Hoy son 244; quedan ~117 KB
  de chip. Medir antes la distribución de cargas por línea visible.
- **S8. El blitter copia los segmentos.** Si las palabras del copper de
  cada segmento están precalculadas en chip, un blit A → D las copia
  mientras la CPU corre la lógica; la CPU solo parchea las h. Evaluarlo
  después de S3-S5: depende de cuánta chip haga falta.

Orden propuesto: S1a + S2 (baratas) → S4 → S5 → S3 → S6. Hecho cuando el
máximo es ≤ 25 % **en los dos sentidos** y en los escenarios de O2, con
`scrollsim.py --ret` (≤ 9282 px, ida = vuelta) y las capturas de las 6 x
sin empeorar.

### 9.3 Lógica (`level_frame` con sprites)

Perfil del 2026-09-30 (`PROF=1 sh tools/logicbench_build.sh &&
python3 tools/m68kprof.py --sprites --worst 5`), en ciclos propios por
frame, sin inline:

| función | media | peor frame real (9709) |
|---|---|---|
| `mario_E2BD` (gráficos de Mario) | 3 970 (12 %) | 4 020 |
| `f44d_asm` (sondas, 5,5 por frame) | 3 060 | 2 740 |
| `spr_tile_asm` | 890 | **2 300** |
| `sprite_run` (temporizadores, ~500 por ranura) | 980 | **2 020** |
| `camera_F6DB` | 1 720 | 1 810 |
| `eb77` / `sprites_all` / `f636` / `mario_D5F2` | 1 030-1 350 cada una | 1 040-1 540 |
| `f7f4_c` (scroll vertical hacia arriba: el asm cae al C) | 510 | **1 390** |
| `spr_obj_interact` / `spr_obj_vert` / `sprite_main` / `jumping_piranha` | 470-550 | 1 050-1 250 cada una |

(El frame 4437 cuesta 53 818 porque paga `probe_init`, 21 454 ciclos: no
es un frame del juego, P64.)

Ideas, por ganancia estimada en el peor frame (hacen falta −6 000):

- **L1. Ensamblador a mano** (el C queda de referencia, como en la 8.2):
  - la rama hacia arriba de `f7f4`: −1 000 en los frames en que Mario sube;
  - `sprite_run` + el despacho de `sprite_main`: −1 000-1 500 con varios
    sprites vivos;
  - `mario_E2BD`: −1 500-2 000 en todos los frames;
  - `spr_obj_interact`/`spr_obj_vert`/`spr_spr_interact` y
    `jumping_piranha`.
- **L2. Descartes rápidos:** `spr_spr_interact` es O(n²): descartar por
  |dx| antes de la caja completa. Lo mismo con el contacto con Mario
  (`DefaultInteractR` en C). Casi siempre están lejos.
- **L3. Estado nativo** de los campos calientes de Mario (8.2, paso 2):
  ≤ 5-8 % estimado. Queda para el final: toca todo el C.
- Verificar cada paso con `abcheck.py <base> --sprites` (semántica IGUAL) y
  con `regress.py`, que corre los cruces de la RAM entera (`--cross`); el
  vbcc de cloud compila mal cosas que gcc compila bien (P38, P62).

Hecho cuando el peor frame con sprites da ≤ 40 % en cycle-exact
(`logicbench -DWORST`) y en los escenarios de O2.

### 9.4 Mario en sprites (`mspr_draw`, 7,3 %)

Medido en el replay (6313 frames): la pose dibujada (punteros de tiles
`wm_0D85` + la OAM relativa) cambia en el **33,5 %** de los frames, y hay
**987** combinaciones distintas.

- **M1. No redibujar si la pose no cambió:** solo SPRxPOS/SPRxCTL. −66 %
  de media. **No** baja el peor frame, que es un cambio de pose.
- **M2. Precalcular todas las poses:** 987 × ~544 B ≈ 530 KB: no entra en
  chip. Descartado.
- **M3. Caché LRU de N poses** en chip (16 × 544 B ≈ 9 KB): ayuda a la
  media (el ciclo de caminar repite 3 poses), no al peor frame.
- **M4. Bajar el coste del dibujo en sí:** perfilar `mspr_draw` por
  etiquetas (como `scrollprof.py --zones`) y atacar lo que salga: filas
  vacías, entradas que se tapan entre sí, el camino del volteo. Objetivo:
  ≤ 3 %.
- **M5. Hacerlo fuera de la pantalla:** es trabajo de bus puro. Hacerlo en
  las 88 líneas sin DMA de planos lo abarata ~1,3×.

### 9.5 Sprites del nivel (9.2): baratos desde el diseño

- Frames **precalculados** por pose (Rex, Banzai, piraña, Koopa...) en chip,
  listos para el DMA de sprites. La CPU solo escribe las palabras de
  control y los punteros; nada de dibujar por CPU.
- Reusar un canal en vertical sin copper: después de la última línea de un
  objeto van las palabras de control del siguiente (0 MOVE).
- Colores 17-31 recargados por el copper solo donde cambian (filas de
  color precalculadas por pose, `copsim.py`).
- Asignador de columnas con coste acotado: ≤ ~10 objetos en pantalla,
  ordenados por Y una vez por frame (inserción: casi ordenados de un frame
  al siguiente).
- Bobs en PF1 solo en el caso raro de `d8demote` (1,8 % de los frames).
- Medir con O1 desde el primer día. Objetivo ≤ 8 %.

### 9.6 Organización del frame y DMA

- Hay **88 líneas sin DMA de planos** (el 28 % del frame). Ahí la CPU va a
  velocidad completa: el trabajo de bus puro (copiar segmentos del copper,
  `mspr_draw`) rinde más ahí. Medir cada trabajo en las dos franjas (método
  de `bench2.s`) y ordenar el frame según eso.
- El blitter trabaja en paralelo: columna nueva y bobs en una cola servida
  por la interrupción del blitter. Nunca esperar a que termine un blit si
  la CPU tiene otra cosa que hacer (P31). `BLTPRI` solo mientras la CPU
  espera (P2).
- Mover código a `$C00000` libera chip pero **no acelera** (P29).
- Si D1 termina en "dibujar a 25 Hz": la lógica sigue a 50 y el scroll se
  calcula cada 2 frames, pero con el doble de desplazamiento por paso. El
  pico de `build_mid` no se divide por 2 automáticamente: medirlo con O1.

### 9.7 Técnicas del 68000 y de vbcc (lo que ya sirvió)

1. **Estado nativo, no `ram[]` byte a byte:** `R16()` son 2 lecturas + `lsl`
   + `or` (~50 ciclos) contra 12 de un `move.w d16(a4),Dn`.
2. **`int` es de 32 bits en vbcc:** los `u8` se promocionan con
   `ext`/`and.l #$FF`. Intermedios en `u16`/`s16`; revisar
   `work/cc/<f>.code.s` buscando `ext.l`, `and.l`, `mulu` y llamadas al
   runtime.
3. **Nada de `mulu`/`divu` en caliente** (38-140 ciclos): tablas o
   desplazamientos.
4. **Punteros que avanzan** (`(An)+`, 8 ciclos) en vez de `d8(An,Dn)` (14),
   con P38 y P62 en mente.
5. Lo caliente en variables locales (registros); las tablas de la ROM
   pasadas a palabras nativas una vez; desenrollar los bucles de vueltas
   fijas; `movem.l` para copiar bloques (la lista del copper: 38 % con un
   bucle, 15 % con `movem`).
6. **Asm a mano solo en lo que el perfil pone arriba**, con la misma
   interfaz que el C, que queda de referencia y para los casos raros.
7. Una palabra en dirección impar cuelga el 68000 (`even`, `cnop 0,2`).
   Los desplazamientos de más de 32 KB van con `(An,Dn.l)` (P40). `tst` y
   `eor` no aceptan `(pc)` ni memoria de origen (P73).

### 9.8 Qué NO hacer

- Cambiar la semántica para ganar ciclos: saltarse sprites, simplificar la
  física o la cámara. Rompe el 1:1, y está bien que el verificador lo marque.
- Tomar Musashi como coste real, o medir con la config rápida (P30).
- Optimizar sin perfil, o por la media en vez de por el peor frame.
- Dar por buena una optimización del scroll probada en un solo sentido
  (P72) o solo en `oracle_yi1` (P69).

---

## 10. Todo lo que falta, y cómo lo haría (2026-09-30)

> Decisiones del usuario del mismo día: D1 = 50 Hz haciendo todo lo
> posible, D15 = se acepta la velocidad PAL, D16 = la zona de la tubería
> entra. Donde abajo dice "decisión [usuario]" o "recomendación", ya está
> decidido así.

La lista completa hasta el ADF final, en el orden en que lo haría. Para
cada punto: **qué falta**, **cómo lo haría** (con las alternativas y por qué
elijo una), los **riesgos**, **cómo se verifica** y las **tarjetas** de
`SUBAGENTES.md` que lo parten. Los detalles de optimización están en §9;
los pasos originales de cada etapa, en §5.

### 10.1 La compuerta D1: medir el juego entero (6b.6)

- **Falta:** nadie midió el peor frame del juego integrado. Solo hay
  medidas por partes, y sumadas pasan del 130 % (§9.0).
- **Cómo lo haría:** `game.s -DBENCH` con el timer A de CIA-B en modo
  continuo (709 379 Hz: ~14 190 ticks por frame, cabe en 16 bits), leído en
  las fronteras de cada parte. Se guarda el máximo de cada parte con su
  frame y su s, y un contador de **frames que se pasan** (el VBL siguiente
  ya llegó). El resultado se pinta al final como en `bench.s`. Se corre
  sobre el replay y sobre escenarios de estrés grabados con snesorc (la
  cámara volviendo sobre las zonas caras, Banzai + 4 Rex, las 2 pirañas).
- **Mi recomendación para D1**, a confirmar con los números: **50 Hz**. Las
  medias entran de sobra (scroll ~15 %, lógica ~25 %, Mario 7 %). Los picos
  son estructurales: son eventos de `build_mid` que se pueden repartir entre
  frames (§9.2 S5) y unas pocas rutinas de la lógica. Dibujar a 25 Hz queda
  de reserva si la 6.4 no baja del 40 %.
- **Además:** qué pasa cuando un frame se pasa igual. Hoy se pierde un VBL
  y se ve un tirón. Con el EDF de S5, lo no urgente se pospone solo; lo
  urgente (lógica, cargas que caducan) siempre entra primero.
- **Verificación:** con `-DBENCH`, el binario sin el banco sale igual byte a
  byte; los máximos caen en frames que se pueden explicar con el perfil.
- **Tarjetas:** O1, O3, R6, O4.

### 10.2 El scroll a ≤ 25 % (6.4)

- **Falta:** todo. Ida 78,8 % y vuelta ~125 % (estimado).
- **Cómo lo haría** (detalle en §9.2), en este orden:
  1. las cargas "tarde" de los postes de la meta, que hoy obligan a
     reescribir 24 líneas en cada frame;
  2. recorrer LNS por grupos de 16 líneas;
  3. edición en el sitio (rebase de la h, append y truncado por la
     derecha);
  4. EDF con presupuesto;
  5. segmentos compartidos entre las dos listas, si el copper tiene
     ranuras en el borrado;
  6. un plan por sentido.

  Del 1 al 4 se puede hacer sin tocar el formato del copper.
- **Riesgos:** romper la ida = vuelta (P71). Por eso `scrollsim.py --ret`
  va en cada paso. El modelo del copper después de `DDFSTOP` (P51) todavía
  no está medido: medirlo antes del paso 5.
- **Verificación:** la puerta común de las tarjetas S.
- **Tarjetas:** S1a, S2, S4, S5, S3, S6, S7, E1.

### 10.2b La cámara vertical en YI1 — **nuevo, hallado el 2026-09-30**

- **El hecho:** YI1 **sí** tiene scroll vertical. Su cabecera trae
  `wm_VertScrollHead` = 2 ("solo en algunos casos", `CODE_00F82A`), que es
  lo que hay en `$1412` en todos los frames del nivel. `lvparse.py` leía mal
  el byte 4 y decía 0 (P77, arreglado), y `oracle_yi1` nunca movió la
  cámara. En las grabaciones de snesorc, `Bg1VOfs` baja de `$C0` a `$BC`
  durante 36 frames (`normal`) y 51 (`diagpipe`).
- **Qué pasa hoy en la Amiga:** `game.s` y `scroll.s` **no leen**
  `Bg1VOfs`; la ventana está fija en las líneas 192-415. Cuando la cámara
  sube, Mario (dibujado con la posición de pantalla que calcula el ROM) se
  corre respecto del fondo tantos píxeles como suba la cámara: se ve
  hundirse o flotar.
- **Cuánto puede subir:** sin medir. Solo se vio hasta 4 px. Un guion de
  estrés de snesorc (saltos a toda carrera desde lo alto de las tuberías y
  de los Rex) da el mínimo real de `Bg1VOfs`. Hacia abajo el límite es
  `$C0` (el `limit` de `f7f4`).
- **Cómo lo haría (barato, porque el movimiento es chico y raro):**
  - **Datos:** extender la ventana de `mkscroll.py` K líneas hacia arriba
    (las del mínimo medido). Cada línea de más cuesta ~320 B de `L2B` y lo
    proporcional de las tablas de CPU.
  - **PF1 y PF2:** sumar (cam_y − 192) filas a los punteros de planos; PF2
    con la mitad (`Bg2VOfs = Bg1VOfs >> 1`, el paralaje vertical de
    YI1). Es gratis.
  - **El copper:** que los segmentos queden **indexados por línea del
    nivel**, no de pantalla. El contenido (las cargas de color) depende de
    la línea del nivel y de s, no de cam_y; lo único que depende de cam_y
    es la **v de los WAIT** de cada segmento. Al cambiar cam_y se parchean
    esas v (224 × 2 palabras, del orden de 3 000 ciclos, **estimado**) y se
    mueven el principio y el final de la cadena. No hay que reescribir
    ninguna carga.
  - Es el mismo paso que prepara el scroll vertical de otros niveles
    (11.3).
- **Verificación:** `scroll_check.py` con cam_y ≠ 192, y capturas del replay
  de `oracle_normal` en los frames 2672-2707.
- **Tarjetas:** R6 (`stress_vert.orc`, el guion de estrés vertical) y S8.

### 10.3 La lógica a ≤ 40 % (8.2, segunda ronda)

- **Falta:** −6 000 ciclos en el peor frame (45 896 → ~40 000 en Musashi).
- **Cómo lo haría:** ensamblador en lo que marca el perfil:
  - la rama hacia arriba de `f7f4`, que hoy cae al C;
  - `sprite_run` entero;
  - `mario_E2BD`;
  - las interacciones.

  Más descartes rápidos por |dx| en las colisiones sprite-sprite y
  sprite-Mario. El estado nativo de Mario (8.2 paso 2) solo si con eso no
  alcanza: toca todo el C y el beneficio estimado es ≤ 5-8 %.
- **Riesgos:** el vbcc de cloud compila mal cosas que gcc compila bien (P38,
  P62). Los cruces de RAM entera de `regress.py` y `gamecheck.py --spr` son
  obligatorios.
- **Tarjetas:** L1a-L1d, L2, L3.

### 10.4 Las pendientes (8c)

- **Falta:** la colina grande de x = `$AE0` (pendiente hacia el otro lado,
  con 5 Rex encima).
- **Cómo lo haría:** un guion de snesorc (a toda carrera en los dos
  sentidos, parado, deslizándose y saltando); `marioverify full` clasifica
  los fallos por causa y los de pendiente se arreglan en `mcoll.c`
  transcribiendo la rutina de la pendiente que falte. Las colinas 1-4 ya dan
  2154/2154.
- **Tarjetas:** R1 (y un M para lo que falle).

### 10.5 Los sprites que faltan: lógica (9.1)

- **Falta:**
  - Clappin' Chuck `$95`;
  - caparazones: el rojo `$DB`, y el Koopa `$02` con caparazón;
  - la cinta de meta `$7B`;
  - lo que sale de los bloques: seta, flor, estrella, 1-UP y enredadera
    (el giratorio "estrella 2/1-UP/enredadera" lo decide el ROM según el
    estado); la luna 3-UP; el champiñón invisible dando la vida;
  - las **bolas de fuego**, que son sprites extendidos (`ex_sprite.s`);
  - las monedas que salen de los bloques y los sprites de puntos;
  - las monedas de Yoshi, contadas (la 5.ª da 1-UP);
  - la caja de reserva;
  - las animaciones de Mario por `$71`: crecer, encoger, morir, la
    estrella.

  Además, dos diferencias chicas: el Koopa `$BD` en el primer frame del
  nivel y un nacimiento de la piraña en `diagpipe`.
- **Cómo lo haría:**
  - **Cada sprite en su fichero** (`player/spr_*.c`, tarjeta I1), así se
    trabaja en paralelo.
  - Transcripción instrucción por instrucción, como el Rex.
  - Para cada objeto, primero la grabación con snesorc y después el port
    contra esa grabación.
  - Los sprites extendidos y las animaciones de `$71` son motores propios
    del ROM (`ex_sprite.s`, la tabla de `$71` en `player.s`): se portan
    enteros, no solo el caso que se ve, porque la flor, la estrella y la
    muerte los usan.
  - El orden: lo que hoy **congela el juego en vivo** primero (el modo
    diagnóstico dice cuál aparece más), después lo que falta para
    terminar el nivel (la meta).
- **Riesgos:** el coste. Cada sprite activo suma ~1 000-2 500 ciclos en el
  peor frame (el perfil de §9.3). Medir con O1 a medida que entran.
- **Verificación:** `marioverify <grabación> game` con
  `sprite XX: seguidos N exactos N` y 0 resincronizaciones.
- **Tarjetas:** R2-R5, I1, P1-P10.

### 10.6 Los sprites que faltan: dibujo (9.2)

- **G2 documentado el 2026-10-05:** [diseño e interfaces](docs/diseno-9.2.md).
  G8 escribe OAM de Rex y rutinas compartidas en el PC; G3a convierte las
  fichas (227/227 poses en las grabaciones actuales). Los enemigos todavía
  **no se ven** en la Amiga: faltan G3 final, G4/G6, G5/G9 y G7.
- **Decisiones de implementación:** OAM en la lógica en su fase original;
  foto de O5 ampliada con OAM/cámara/pertenencia a ranura en slow RAM;
  cuatro parejas adosadas, descontando las una o dos de Mario; Banzai
  siempre bob; desbordes con destino explícito, sin descartarlos.
- **Reuso:** PT + POS/CTL por copper, conforme a la medida G0 a 256 px.
  Contar hasta 8 MOVE por pareja (6 si los punteros comparten banco de
  64 KiB). El encadenado queda como alternativa por objeto; no asumir
  válida la ventana de una línea a partir del modelo de 320 px.
- **Color:** G3 debe remapear los índices de cada paleta a COLOR17-31,
  respetando los de Mario. La unión de 11 colores medida con poses de
  referencia no verifica todas las poses. Autoprueba de píxeles y tamaño
  de las variantes antes de aprobar el banco de 64 KiB.
- **Bobs:** segundo PF1 (+59 136 B), para conservar la imagen publicada
  cuando O5 repite un frame. G7 restaura y dibuja en el buffer libre, y
  publica al terminar los blits. Los casos sin color exacto de
  `d8demote.py` siguen pendientes.
- **Memoria:** mapa actual de replay: chip 390 704 B. Con banco de poses,
  segundo PF1 y audio: 580 912 B. C2/C4 deben sacar las tablas de CPU
  (135 468 B) de chip antes de integrar todo; quedarían 78 844 B para
  HUD, listas adicionales, flujos encadenados y subzona. Es una reserva
  de diseño, no el tamaño final demostrado de los assets.
- **Puertas:** OAM real del 68000 contra grabaciones; asignación y píxeles
  reconstruidos exactos; capturas contra la OAM; `memmap`; coste de lógica
  con OAM ≤40 %, preparación de sprites ≤8 %, ticks/fotos perdidos O5
  medidos en cycle-exact. Detalle y comandos en el diseño y sus informes.
- **Tarjetas:** G0, G3-G9, C2/C4; Z1, H1 y A1/A2 según sus dependencias.

### 10.7 Carga y memoria (6b.1)

- **Falta:** el loader definitivo, el enlazado absoluto (vlink), la
  compresión y un mapa de memoria que alcance para todo.
- **La cuenta de la chip** (hoy ≈ 395 KB de 512):
  - `yi1_s.dat` son 223 600 B y hoy van **enteros a chip**. De eso, el
    chipset solo lee `BLK` (23 424, el blitter) y `L2B` (71 232, el DMA de
    planos). `MAP`, `INI`, `CHG`, `L2P`, `MLX`, `MLD` y `LNS` (129 000 B)
    los lee solo la CPU.
  - Moverlos a `$C00000` (D13) deja la chip en **≈ 266 KB**, con sitio
    para el audio (≤ 64 KB), los gráficos de sprites (< 30 KB), el HUD y la
    zona de la tubería (10.10).
  - **Sin esto no entra todo**: 395 + 64 + 30 ya pasa de 490 KB.
- **Cómo lo haría:**
  1. partir `yi1_s.dat` en una parte de chip y otra de CPU (`mkscroll.py`
     ya sabe dónde empieza cada sección);
  2. `memmap.py` que compruebe el mapa desde el listado;
  3. vlink con direcciones fijas: se van P36/P52 y los `GETBASE`;
  4. compresión LZ solo si el tiempo de carga lo pide. El ADF va por el
     46 % y leer 412 KB con trackdisk tarda del orden de 15-20 s
     (**estimado**; medirlo).

  Todo se carga con `trackdisk` mientras el SO vive (D13); después de tomar
  la máquina no hay que leer del disco.
- **Riesgos:** que el binario enlazado en absoluto rompa las herramientas
  que lo cargan en `BASE` (`m68kverify`, `gamecheck`, `gamesim`, `abcheck`):
  tarjeta E3.
- **Tarjetas:** C1-C5, E3.

### 10.8 HUD, caja de mensajes y pausa (10)

- **Falta:** la barra de estado, **las 2 cajas de mensaje** del nivel (la
  lógica del sprite `$B9` está, pero el texto no se muestra) y la pausa.
- **Cómo lo haría:**
  - **Barra (D11, overlay).** En sus líneas, el copper apunta PF1 a un
    bitmap fijo con retardo 0 y carga los 7 colores del HUD. PF2 sigue con
    su paralaje. Es el mismo mecanismo de recarga por línea que ya existe.
    Primero, medir si la capa 1 aparece alguna vez en esas líneas (H1):
    con la cámara en Y = 192 es casi todo cielo. Los dígitos se blitean
    solo cuando cambian: el tiempo cambia cada ~40 frames y el resto casi
    nunca.
  - **Cajas de mensaje.** En YI1 son solo 2 textos, que están en
    `strings/level_messages.a`. Los **renderizaría offline** a dos bitmaps
    con la fuente `gb-1`. En la Amiga, mostrar uno es cambiar punteros y
    colores en el copper en las líneas de la ventana, con el juego
    congelado como en la SNES. La animación de apertura se hace creciendo
    esas líneas frame a frame (`dialog.s` dice cuántas).
  - **Pausa.** Start congela la lógica (la rutina del ROM) y baja el
    volumen de la música.
- **Verificación:** `marioverify hud` contra los contadores grabados (R7);
  capturas de la barra y de la caja contra la referencia.
- **Tarjetas:** H1-H5, R7 (y una H6 para las cajas de mensaje, que se
  agrega cuando esté H3).

### 10.9 Audio (11)

- **Falta:** todo.
- **Números:**
  - todas las muestras BRR del juego son 92 KB (`sound/samples`), unos
    164 KB en PCM de 8 bits: no entran en 64 KB. Hay que quedarse con las
    del tema del nivel y los efectos, y bajar la frecuencia de muestreo de
    alguna si hace falta;
  - música: el tema del nivel está en `sound/music1`; las secuencias son de
    N-SPC.
- **Cómo lo haría** (el cambio más grande respecto de la idea original de
  D5): **no escribir un intérprete de N-SPC**, sino **capturar las
  escrituras al DSP** con snesorc (el SPC700 emulado de snesrev), tick a
  tick, mientras suena el tema. Por voz:
  - la fuente de la muestra (SRCN), la altura (P), el volumen y la
    envolvente (ADSR/GAIN), y los KON/KOFF;
  - la altura se pasa a periodo de Paula y la envolvente a una tabla de
    volumen por tick;
  - las 8 voces se reparten en 3 canales por prioridad (melodía, bajo,
    percusión), robando la voz cuando otra calla;
  - se captura un bucle del tema;
  - los efectos igual: se dispara cada uno solo, escribiendo en los
    puertos de sonido (`$1DF9-$1DFC`), y se graba lo que hace el DSP.

  El 68000 solo recorre flujos de eventos por tick (timer de CIA): es
  casi nada de CPU, y exacto en tiempo y en altura. Lo que se pierde (eco,
  filtros, modulación entre voces) D5 ya lo daba por perdido.
- **Riesgos:** voces que no caben en 3 canales en los momentos densos del
  tema (medir en la captura cuántas suenan a la vez); el periodo mínimo de
  Paula (124) para las notas agudas de muestras con mucha frecuencia de
  muestreo.
- **Verificación:** render offline de los eventos contra el WAV de snesorc
  (R8): notas a ±1 tick y ±5 cents; en FS-UAE, a oído.
- **Tarjetas:** R8, A1-A7 (A2 y A3 cambian: "capturar el DSP" en vez de
  "leer N-SPC").

### 10.10 La zona de la tubería (`obj-1.lv`) — **nuevo**

- **Qué es:** el nivel tiene una segunda zona: `obj-1.lv`, 2 pantallas,
  tileset 3, música 1, con nubes, monedas y tuberías. Se llega por una
  tubería: en `oracle_yi1`, Mario entra en una en el frame 11425 (P68). El
  nivel tiene una salida de pantalla (pantalla 18, destino `$CB`).
- **Falta:** todo: la conversión de la zona, entrar y salir por tubería,
  la transición y el regreso.
- **Cómo lo haría:**
  - generalizar la cadena del nivel (`mklvl` → `mkd8in` → `mkleveld` →
    `mkscroll`) para que reciba el nivel como parámetro, y generar
    `yi1b_s.dat`. Son 2 pantallas: poca memoria;
  - en la Amiga, la transición es un fundido, cambiar los punteros del
    scroll (otra `yi1_s`), la paleta y la cámara, y seguir;
  - la lógica: las animaciones de tubería de `$71` y la carga de la
    subzona (cabecera, sprites si los hay, posición de entrada) del ROM;
  - grabarlo con snesorc (el camino de `oracle_yi1` hasta la tubería).
- **Decisión [usuario] (D16):** entra en el alcance si "Yoshi's Island 1"
  quiere decir el nivel entero (criterio 1:1: sí). Si no, la tubería se
  queda cerrada.
- **Tarjetas:** R9 (grabación), I2 (descriptor de nivel), T1 (conversión),
  T2 (lógica de tubería), T3 (transición en la Amiga).

### 10.11 Pulido y final del nivel (12)

- **Falta:**
  - la muerte con su animación, y reaparecer (en el punto medio si se
    pasó);
  - el **punto medio**: el objeto `Midway/Goal point` + `Midway point
    rope` del nivel; al tocarlo, marca y Mario grande;
  - la **meta**: la cinta, "course clear", la cuenta de puntos
    (`lv_end_seq.s`) y el fundido;
  - el tiempo agotado;
  - los fundidos de entrada y salida;
  - Mario detrás del poste de la meta.
- **Cómo lo haría:**
  - **Fundidos:** el OCS no tiene brillo global, así que hay que
    reescribir todos los colores. Durante un fundido la lógica está parada
    y sobra CPU: se regeneran los MOVE de color de las dos listas con una
    tabla de 16 pasos por componente.
  - **Mario detrás del poste:** `BPLCON2` por línea con el copper (la
    prioridad es por playfield, no por píxel: en esas líneas Mario queda
    detrás de toda la capa 1, que en la meta es casi solo el poste).
  - **Muerte, punto medio y meta:** son rutinas del ROM que se transcriben
    contra grabaciones de snesorc, como todo lo demás.
- **Tarjetas:** Z1-Z6, R4, R5.

### 10.12 La velocidad: 50 Hz contra 60 — **decisión nueva (D15) [usuario]**

- **El hecho:** el port corre **un frame de lógica del ROM (U), que es
  NTSC, por cada frame PAL**. El juego va a 50/60 = **83 % de la velocidad
  de la SNES americana**, igual que les pasaba a los juegos PAL de SNES
  que no se ajustaban. La música no cambia de tempo, porque el tick sale
  de un timer de CIA (D5).
- **Opciones:**
  - (a) aceptarlo, como la SNES PAL; es lo que hay hoy y no cuesta nada;
  - (b) correr 6 frames de lógica cada 5 de pantalla: +20 % de CPU de
    lógica, que hoy no hay;
  - (c) ajustar la física: rompe el 1:1 con el oráculo.
- **Mi recomendación:** (a), y dejarlo escrito.

### 10.13 Hardware real y pruebas finales

- **Falta:** que el juego corra alguna vez en una A500 de verdad.
- **Riesgos, ordenados:**
  - el handshake del teclado (medido en WinUAE, no en un 8520 real);
  - la temporización del copper (calibrada en WinUAE: WinUAE cycle-exact es
    muy fiel, pero conviene una captura real de `copcal`);
  - la detección de la A501 (P8);
  - la lectura del disco en KS 1.2/1.3.
- **Cómo lo haría:** un ADF de diagnóstico con `copcal`, el teclado
  mostrando los códigos y `logicbench`, para que el usuario le saque una
  foto a la pantalla. El modo diagnóstico del juego (P58) sirve también
  para los fallos en el hardware real: una foto de la página 2 alcanza
  para reproducirlo.
- **Tarjetas:** U1-U4, Z7.

### 10.14 Verificación continua

- **Falta:**
  - el replay completo **hasta la meta** como prueba de `regress.py`: hoy
    `oracle_yi1` se corta antes;
  - una grabación de snesorc que cubra todo el nivel de punta a punta;
  - las métricas del frame entero (O3).
- **Idea, sin decidir:** correr `setup_cloud.sh` + `regress.py` en GitHub
  Actions en cada push. La ROM se arma desde el fuente público y no se
  publica nada derivado de ella, pero se arma en máquinas de GitHub.
  **[usuario]**: consultar antes, por R9.
- **Tarjetas:** Z8, O3.

### 10.15 Orden global

Las decisiones están tomadas (D1 = 50 Hz haciendo todo lo posible, D15 =
velocidad PAL, D16 = la zona de la tubería entra). El orden va en **8 olas**,
descritas una por una en `SUBAGENTES.md` §3 (tarjetas, entrega, criterio de
cierre, sesiones) y resumidas en §1.8:

1. medir el frame entero y grabar todo lo que falta;
2. y 3. 50 Hz: el scroll y la lógica, y los diseños del dibujo y del audio;
4. motores: copper definitivo + cámara vertical (10.2b), vlink,
   conversores, el resto de la lógica de sprites, la zona de la tubería en
   datos;
5. integraciones: enemigos en pantalla, loader, HUD, música;
6. el juego completo: muerte, punto medio, meta, zona de la tubería,
   replay hasta la meta;
7. segunda ronda de 50 Hz con todo junto;
8. cierre: KS 1.2/1.3, arreglos, ADF final.

Total: 12-15 sesiones con las olas en paralelo; 16-20 si hay que
serializar.

Cómo repartirlo entre subagentes (niveles, tarjetas, protocolo):
`SUBAGENTES.md`.

---

## 11. Más allá de YI1: otro nivel y la lógica extra del juego

Fuera del alcance de hoy. Textual en **`docs/mas-alla-yi1.md`**:

- 11.1 Qué es de YI1 y qué es genérico
- 11.2 El proceso, paso a paso
- 11.3 El scroll vertical (el trabajo más grande de otro nivel)
- 11.4 Cargar entre niveles
- 11.5 Pantalla de carga, título y demo
- 11.6 Partidas guardadas
- 11.7 Otros extras (baratos, cuando haya tiempo)
- 11.8 Cosas que conviene decidir YA pensando en esto
