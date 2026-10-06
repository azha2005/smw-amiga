# SUBAGENTES.md — El resto del proyecto, en tareas para subagentes

> **Qué es.** El plan de **todo lo que falta** del port (desde el 2026-09-30
> hasta el ADF final), partido en **tarjetas** que puede ejecutar un
> subagente de menor potencia sin contexto previo, más el protocolo del
> coordinador que las reparte, las revisa y las integra.
>
> Relación con los otros ficheros: `AGENTS.md` es el contrato (reglas duras,
> formatos, pitfalls); **`PROXIMO.md` dice qué se hace a continuación**;
> `ROADMAP.md` tiene el estado por etapa (§1), el presupuesto (§2) y las olas
> con las sesiones que faltan (§4); `docs/plan-tecnico.md`, cómo hacer cada
> cosa. Este fichero dice **cómo repartir el trabajo** y es **el único
> registro del estado de cada tarjeta** (tabla al principio de §4). Si algo
> de aquí contradice a `AGENTS.md` §2, manda `AGENTS.md`.

---

## 1. Roles y niveles

**Coordinador** (nivel F, el agente más capaz de la sesión): elige la ola,
crea los worktrees, escribe o ajusta las tarjetas, lanza los subagentes,
revisa cada rama, integra, corre la regresión completa, mantiene
`tools/baseline.json`, `AGENTS.md` y `ROADMAP.md`, y lleva las decisiones
**[usuario]** al usuario. No delega la revisión ni la integración.

**Niveles de subagente:**

| nivel | para qué sirve | ejemplos |
|---|---|---|
| **F** (fuerte) | diseño, temporización del copper, memoria/enlazado, depurar un fallo que no se entiende, todo lo que no tiene un verificador que diga "bien/mal" | `build_mid` incremental, pool de segmentos, vlink, diseño de la 9.2 |
| **M** (medio) | transcribir rutinas del ROM instrucción por instrucción **contra el oráculo**, pasar C a asm **contra `--cross`**, herramientas con autoprueba, integraciones acotadas | sprites de la 9.1, `sprite_run` en asm, `brr2pcm.py`, `memmap.py` |
| **C** (chico) | tareas mecánicas con una puerta automática trivial: guiones de snesorc, medidas, recuentos, tablas | grabar el Chuck, medir las líneas del HUD, `orc_has.py` |

**Regla para elegir nivel:** una tarjeta puede bajar de nivel solo si
(1) tiene una **puerta automática** que detecta el error (el oráculo,
`--cross`, una autoprueba, `imgdiff`), (2) es **transcripción o mecánica**,
no diseño, y (3) toca **un área** (sin razonar sobre tiempos del copper ni
sobre el mapa de memoria). Si falla una de las tres, sube un nivel.

### Modelos (usuario, 2026-10-05)

Solo **GPT-6.1 Sol** (esfuerzo `high` o `medium`) y **GPT-6 Luna medium**.
Astra queda fuera. Esta asignación reemplaza los perfiles Opus/Sonnet del
plan histórico; expresa el papel de cada modelo, no una equivalencia medida.

**Marco de referencia acordado con el usuario:**

| perfil de referencia | perfil disponible para este proyecto |
|---|---|
| Opus | GPT-6.1 Sol high |
| Sonnet high | GPT-6.1 Sol medium |
| Sonnet low | GPT-6 Luna medium |

Es decir: **Opus → Sol high**, **Sonnet high → Sol medium** y
**Luna medium corresponde a Sonnet low**. Usar este marco al leer las tarjetas
y planes históricos que todavía mencionan Opus/Sonnet.

Para tarjetas sin excepción en la tabla: **F → Sol high**, **M → Sol medium**,
**C → Luna medium**. Si una medida exige derivar primero la temporización o
interpretar estados de hardware, el coordinador resuelve esa parte de diseño
antes de delegar el recuento a Luna.

| tarjetas / responsabilidad | modelo | esfuerzo |
|---|---|---|
| coordinador: revisión, integración y decisiones de diseño | GPT-6.1 Sol | high |
| G4, G5, C2, C4, G7, A2, S5 | GPT-6.1 Sol | high |
| G3 final, G6, G9, Z1, A0, A1 | GPT-6.1 Sol | medium |
| H1, grabaciones, recuentos e informes de medidas con puerta clara | GPT-6 Luna | medium |

Cada prompt fija **modelo, esfuerzo y condición de escalado**. Sol medium
sube a high cuando aparece diseño no resuelto, un cruce de subsistemas o
fallos de la puerta tras intentos distintos; antes se informa al coordinador
con evidencia. Luna solo recibe tareas mecánicas y acotadas con comprobación.
Máximo de esta sesión: **coordinador + tres subagentes**. Dependencias en
serie y un worktree por tarjeta, aunque se libere una plaza antes.

---

## 2. Protocolo

> **En la PC Windows** (no en cloud), cada subagente recibe además
> **`docs/reglas-ola-pc.md`**: entorno (P82), candado de WinUAE, baseline
> `baseline_pc.json` y reglas fijas. Manda sobre lo de abajo donde choquen.

### 2.1 Antes de lanzar (coordinador)

```bash
sh tools/setup_cloud.sh && sh tools/snesorc_setup.sh     # una vez por contenedor
python3 tools/lint_port.py && python3 tools/regress.py   # la base tiene que dar OK
sh tools/wt_new.sh <tarjeta>                             # ../wt-<tarjeta>, rama wt/<tarjeta>
```

`wt_new.sh` copia `work/` (ROM, oráculos, `snesorc`, `yi1_*.dat`) y
`player/gen/`, e imprime las variables que el subagente tiene que exportar
(`FSUAE_BASE`/`FSUAE_DISPLAY` propios, P76). **Nunca dos subagentes en el
mismo árbol**: compilar escribe en `work/`.

### 2.2 La tarjeta (plantilla del prompt)

Cada tarjeta de §4 tiene estos campos; el prompt del subagente es la
tarjeta + el bloque fijo de §2.3:

```
Tarea <ID> — <título>
Worktree: /home/user/wt-<id> (rama wt/<id>). Exporta: <línea de wt_new.sh>
Lee (solo esto): <ficheros y secciones exactas; nada de "lee AGENTS.md entero">
Contexto: <2-5 líneas: por qué, qué hay ya hecho, números de partida>
Hace: <pasos numerados, concretos>
Puerta (hecho cuando): <comandos exactos y lo que tienen que imprimir>
No toca: <ficheros de otras tarjetas de la misma ola>
Entrega: <qué poner en el informe>
```

### 2.3 Reglas fijas (se copian en todos los prompts)

1. Trabajás **solo** en tu worktree. No hagas push. Commits locales en
   español, estilo `Etapa N.x: <qué>`, con las líneas de atribución que te
   pase el coordinador.
2. **No edites** `AGENTS.md`, `ROADMAP.md`, `SUBAGENTES.md` ni
   `tools/baseline.json`. Las trampas nuevas y los números van en el
   informe; el coordinador los integra.
3. Antes de cada commit: `python3 tools/lint_port.py && python3
   tools/regress.py`. Si algo sale PEOR y es a propósito (más sprites que
   corren de verdad, por ejemplo), explicalo en el informe; si no, arreglalo.
4. Nunca saltarse, desactivar ni aflojar una comprobación para llegar a la
   puerta. Nunca cambiar la semántica para ganar ciclos (`docs/plan-tecnico.md` §9.8).
5. Los ficheros con barras invertidas (macros `\1` de vasm, `\n` en C) se
   escriben con la herramienta de ficheros, no con heredoc de bash (P56).
6. **Parar y avisar** si: la puerta no se cumple después de 3 intentos
   distintos; hace falta tocar un fichero de "No toca"; aparece algo que
   contradice la tarjeta o `AGENTS.md`. Informe con la evidencia (salida
   de las herramientas), no con suposiciones.
7. Al terminar: nada sin commitear. Lo que quede a medias, en un commit
   `WIP: <qué falta verificar>`.
8. Informe final: qué hiciste, commits (hash + título), la salida de la
   puerta, números antes → después con su herramienta y emulador, qué no
   pudiste probar, trampas nuevas redactadas como `Pnn`.
9. **Nada nuevo fijo a YI1** (`docs/mas-alla-yi1.md` §11.8): las
   herramientas leen el nivel de `levels/<nivel>.json`, los datos de
   sprites van por tipo y la memoria separa lo común de lo que es de cada
   nivel. Si algo tiene que quedar fijo, decirlo en el informe.

### 2.4 Revisión e integración (coordinador)

Por cada rama:
1. `git log` + `git diff master...wt/<id>` (o la rama base de la sesión):
   ¿toca solo lo que decía la tarjeta? ¿el C sigue las convenciones
   (`AGENTS.md` §7)? ¿hay algo derivado de la ROM (R9)?
2. **Volver a correr la puerta** en el worktree; no fiarse del informe.
3. Integrar (`git merge --no-edit wt/<id>`), `python3 tools/smwtabx.py` si
   cambió, y la regresión completa en el árbol integrado. Al cerrar una ola:
   `regress.py --level --emu logic,scrollbench,scrollimg`,
   `game_build.sh` + `gamecheck.py --spr` y capturas del replay
   (`-DSTOPF=F-5145`, P75).
4. `regress.py --update` (o `--accept-last --force` con la explicación en
   el commit) si las métricas cambiaron a propósito.
5. Trampas nuevas a `AGENTS.md` §8 (renumeradas), estado de la tarjeta a
   la tabla de §4 y, si cambió una etapa, a `ROADMAP.md` §1;
   `sh tools/wt_new.sh --rm <id>`. Al terminar la sesión, `ROADMAP.md` §7.

### 2.5 Mapa de conflictos

Dos tarjetas de la misma ola no pueden tocar el mismo fichero. Las zonas:

| zona | ficheros | tarjetas |
|---|---|---|
| juego | `player/game.s`, `tools/game_build.sh` | O1, MA1, H3, Z1-Z6, C4, T3 |
| modelo del copper | `tools/scrollsim.py`, `copcal.s`/`copcal.py` | E1, E2, S3 |
| scroll | `player/scroll.s`, `tools/mkscroll.py`, `mkleveld.py` | S*, G5, H3 |
| lógica de Mario | `player/mario.c`, `mcoll.c`, `manim.c`, `mgfx.c`, `mcam.c` | L1a, L1c, L3, P8, T2, Z1-Z4 |
| sprites | `player/msprite.c` (o `player/spr_*.c`, I1) | P*, L1b, L1d, L2 |
| asm de la lógica | `player/logic68k.s` | L1*, L2, G4 |
| Mario en sprites | `player/mspr.c`, `mspr68k.s`, `tools/mkmario.py` | MA*, G4 |
| verificadores | `tools/marioverify.c`, `m68kverify.py`, `regress.py` | O3, P* (contadores), H4 |
| grabaciones | `tools/snesorc/*.orc`, `work/oracle_*.txt` | R* (cada una su fichero: se pueden paralelizar) |
| cadena del nivel | `tools/mklvl.py`, `mkbg.py`, `mkd8in.py`, `mkleveld.py`, `mkmapbin.py` | I2, T1, S7 |
| audio | `tools/brr2pcm.py`, `player/audio*.s` (nuevos) | A* |

`regress.py` y `marioverify.c` los tocan muchas tarjetas: que cada una
**solo agregue** una función o un modo nuevo, sin reordenar lo existente,
y el coordinador resuelve los conflictos al integrar.

---

## 3. Olas

El estado de las olas, qué contiene cada una y cuántas sesiones faltan está
en **`ROADMAP.md` §4**; la próxima sesión, en **`PROXIMO.md`**. El reparto
original del 2026-09-30, ola por ola, está textual en
`docs/archivo/olas-2026-09-30.md`.

### Reglas de las olas
- R0 es corta: primero ella y después las R en paralelo (cada guion es su
  fichero). P4-P10 van en paralelo gracias a I1, salvo P8 (la lógica de
  Mario), que va sola, y T2, que también toca `$71`: P8 → T2 en serie.
- D1, D15 y D16 están decididas (2026-09-30: 50 Hz haciendo todo lo
  posible, velocidad PAL aceptada, la zona de la tubería entra). O4 es un
  informe; solo se vuelve al usuario si, agotadas las ideas de
  `docs/plan-tecnico.md` §9, la compuerta D1 (fotos omitidas, `ROADMAP.md`
  §2) no pasa.
- Después de cada sesión: integración completa (§2.4), un ADF nuevo para el
  usuario y el cierre de `ROADMAP.md` §7 (archivar y reescribir
  `PROXIMO.md`, actualizar estados).
- **3-5 subagentes a la vez** por sesión. Más, y la revisión del
  coordinador se vuelve el cuello de botella.

---

## 4. Tarjetas

### Estado de las tarjetas (al 2026-10-06)

**Única fuente del estado de cada tarjeta.** Se actualiza al integrar
(`ROADMAP.md` §7). Estados: **hecha**, **parcial** (lo que falta, dicho),
**pendiente**, **descartada** (con el porqué), **reabierta**.

| tarjetas | estado | nota / evidencia |
|---|---|---|
| I1, I2 | hecha | un fichero por sprite (P78); descriptor `levels/yi1.json` |
| O1, O2 (= R6), O3, O4, O5 | hecha | `docs/informe-d1.md`; O5 render desacoplado por defecto |
| R0-R4, R6, R9, R10 | hecha | 32 oráculos en `tools/snesorc/*.orc` y `work/oracle_*.txt` |
| R5 | parcial | falta la luna 3-UP |
| R7, R8 | pendiente | contadores del HUD; audio de referencia (con A0) |
| S1a, S2, SX/SX2 | hecha | `docs/validacion-sx.md`; P51 arreglada |
| S4 | descartada | P89: editar la lista en el sitio no conviene en el 68000 |
| S5 | pendiente | va inmediatamente después de G5 (`PROXIMO.md` §2) |
| S3, S6, S7, S8 | pendiente | S8 = cámara vertical de YI1 |
| L1a, L1b, L1c, L1d | hecha | `level_frame` máx. 37,24 % en WinUAE |
| L2 | descartada | probada, no ganó como tarjeta propia; lo útil quedó en L1d (`2753e87`) |
| L3, L4 | pendiente / descartada | L4: `docs/investigacion-ports.md` §14.10 |
| MA1 | hecha | `mspr_draw` media 10 393 → 4 169 ciclos |
| MA2 | pendiente | |
| P1-P6, P8 | hecha | Koopas, piraña, Chuck, caparazones, meta, power-ups, estados de Mario |
| P7, P9, P10 | pendiente | bolas de fuego, monedas de Yoshi y puntos, reserva |
| X1 | pendiente | estudio |
| G0, G1, G3a, G8 | hecha | `docs/medida-g0.md`, `docs/estudio-g1-g0.md`, `docs/oam-amiga.md` |
| G2 | reabierta | el banco no entra (`docs/informe-g3.md`); en `PROXIMO.md` |
| G3 | parcial | SG3F y 48 poses exactas; final pendiente de G2 |
| G5a (nueva, prueba mínima de Rex), G8b (nueva, OAM de Banzai, piraña, Chuck, meta, caparazones), D1-medida (nueva) | pendiente | definidas en `PROXIMO.md` |
| G4, G5, G6, G7, G9 | pendiente | después de G2/G3 |
| C1 | hecha | `tools/memmap.py` |
| C2, C3, C4, C5 | pendiente | |
| H1 | hecha | medida conservadora; falta la alineación exacta PPU (`docs/medida-hud.md`) |
| H2-H5 | pendiente | |
| A0-A8 | pendiente | A1 en `PROXIMO.md` |
| T1-T3 | pendiente | |
| Z1 | hecha | `docs/validacion-z1.md` |
| Z2-Z8 | pendiente | |
| E1 | hecha | resuelta como P51 (`0361736`) |
| E2, E3 | pendiente | |
| E11a | hecha | 15.755 frames; 0 cargas PF1 en franjas aptas; `docs/experimentos-e11-e14.md` |
| E11b | descartada | no beneficia cargas de `build_mid` con el banco actual; DMA general sin medir |
| E12 | descartada | 0/7 índices elegibles, 0 MOVE en todas las cámaras posibles; reasignación E09 no evaluada |
| E13 | pendiente | no se abre: ningún caso confirmado en YI1; recurso en `docs/plan-tecnico.md` §9.2 |
| E14a | hecha | atribución exacta auditada; 234 frames visibles de estrés, 347 de Banzai; `docs/experimentos-e11-e14.md` |
| E14 | descartada | estrés: 0/202 frames con 64 filas libres; Banzai solo: 16/331. Peor caso bob E04/G7 intacto |
| V2, V3 (de la investigación) | hecha | `tools/coverage.py`, `tools/asmlint_port.py` |

Formato corto: **Nivel · Depende de · Toca**, y después Lee / Hace /
Puerta / No toca. "Regresión OK" = `lint_port.py` + `regress.py` sin PEOR
que no esté explicado.

### I — Infraestructura

#### I1 — Sprites nuevos en ficheros propios
**M · — · `tools/logicbench_build.sh`, `tools/regress.py`, `tools/setup_cloud.sh`, `tools/game_build.sh`**
- Lee: `logicbench_build.sh` (cómo parte cada `.s` de vbcc en datos y
  código, P36, P47), la lista `CSRC`/`LIBSRC` de `regress.py`, la línea
  `SRCS` de `setup_cloud.sh`.
- Hace: que cualquier `player/spr_*.c` entre solo en los tres builds (gcc
  del PC, biblioteca de `--cross`, vbcc del 68000) sin tocar las listas a
  mano; mover el Rex a `player/spr_rex.c` como prueba.
- Puerta: regresión OK **idéntica** (ninguna métrica cambia, ni los
  ciclos: `abcheck.py HEAD~1 --sprites` IGUAL).
- Por qué: con un fichero por sprite, las tarjetas P* se paralelizan.

#### I2 — Descriptor de nivel
**M · — · `tools/*.py` de la cadena del nivel, `levels/*.json` (nuevo)** ·
`docs/plan-tecnico.md` §11.2 paso 1: un JSON por nivel (rutas de `obj*.lv`/`spr.lv`,
cabecera, ventana de cámara, nombres de salida) que lean `mklvl`, `mkbg`,
`mkd8in`, `mkleveld`, `mkscroll`, `mkmapbin` y `mkmario`. Puerta: con el
descriptor de YI1, **todo sale igual byte a byte** (`regress.py --level`).
Lo necesita la zona de la tubería (T1) y cualquier nivel futuro.

### O — Medir el frame entero (`docs/plan-tecnico.md` §9.1; es la 6b.6)

#### O1 — `game.s -DBENCH`
**M · — · `player/game.s`, `tools/game_read.py` (nuevo)**
- Lee: `docs/plan-tecnico.md` §9.1; `player/bench.s` + `tools/bench_read.py` (cómo se
  mide con el timer A de CIA-B y se escribe en pantalla como bits);
  `player/game.s` (el bucle del frame: `game_step`, `scroll_frame`,
  `mspr_draw`); AGENTS P52, P75.
- Hace: con `-DBENCH`, medir por frame entrada, `level_frame`,
  `mspr_draw`, columna, `build_mid`, resto de `scroll_frame` y el total;
  guardar el peor de cada uno con su frame y su s; al terminar el replay
  (o con `-DSTOPF`), pintarlo como bits con palabras de sincronía;
  `game_read.py --shot X --auto` lo decodifica.
- Puerta: el replay con `-DBENCH` da una tabla con 7 filas y los máximos
  en frames plausibles; sin `-DBENCH`, `game.bin` **idéntico byte a byte**
  al de antes; `gamecheck.py` 0 diferencias.
- No toca: `scroll.s`, `msprite.c`.

#### O2 — Escenarios de estrés (= R6)
Ver R6.

#### O3 — El peor frame por parte en `regress.py`
**M · O1 · `tools/gamecheck.py`, `tools/regress.py`, `tools/scrollprof.py`**
- Hace: `gamecheck.py --engine musashi` corre también `scroll_frame` y da
  ciclos por parte (peor y media); `regress.py` los guarda (`game.*`) y
  agrega el scroll a la vuelta (`scrollprof.py -D RETURN=4864 --stopx 0`),
  y `--emu game` corre O1 en FS-UAE.
- Puerta: métricas nuevas presentes y estables en dos corridas seguidas.

#### O4 — Informe del peor frame (D1 ya decidida: 50 Hz, todo lo posible)
**F (coordinador) · O1, O3, R6**
- Hace: tabla del peor frame del juego integrado (replay + escenarios de
  estrés) por parte, contra ROADMAP §2; las tres opciones de §2 con
  números (otra ronda de optimización con las ideas de §9, dibujo a 25 Hz,
  recortar alcance) y una recomendación. Preguntar al usuario.

### R — Grabaciones con snesorc (nivel C; cada una en su fichero)

Todas: el guion en `tools/snesorc/<nombre>.orc` (empieza con `include
boot_yi1.orc`), `sh tools/snesorc_make.sh <nombre>`, el `.txt` a git (V4),
el `.bin` no. Sintaxis: `N RIGHT+Y`, `until w$0094>=07B0 max 600 RIGHT+Y`,
`pulse`, `rec on|off|all`, `poke`, `assert $0071==00`, `print`, `include`
(ver `tools/snesorc/orc.c` y los guiones que ya hay). Las X de los objetos
salen de `spr.lv` (`python3 tools/lvparse.py --dump`) y de `AGENTS.md` §9 D3.
Lee: ROADMAP Etapa 8.1, AGENTS P67, P68, P70; `tools/snesorc/diagpipe.orc`
como ejemplo.

#### R0 — `tools/orc_has.py`
**C · — · `tools/orc_has.py` (nuevo)**
- Hace: dado un `oracle_*.txt`, lista por número de sprite en qué frames
  está en alguna ranura y con qué estado, y un resumen de Mario por tramo
  (X, `$19` = power-up, `$71` = animación). Formato del `.txt`: el que lee
  `tools/oracle2bin.py`.
- Puerta: sobre `work/oracle_yi1.txt` da los tramos que dice ROADMAP Etapa
  9.1 (Koopa `$BD` 4437-4597 y 5145-5305, Banzai `$9F` 5799-6077...).

#### R1 — La colina grande de x = `$AE0` (cierra la 8c)
**C · R0** · `hills2.orc`. A toda carrera en los dos sentidos, parado,
deslizándose y saltando, con los 5 Rex (pisarlos o esquivarlos).
Puerta: `marioverify work/oracle_hills2.bin full` sin fallos de
pendiente (la salida los clasifica por causa); `assert` al final.

#### R2 — Clappin' Chuck `$95` (x `$12A0`)
**C · R0** · `chuck.orc`: llegar, dejar que salte y aplauda, pisarlo 3
veces; otra variante en la que daña a Mario. Puerta: `orc_has.py --sprite 95`
lo muestra vivo ≥ 200 frames y con pisotones.

#### R3 — Caparazón rojo `$DB` (x `$D10`) y caparazones del Koopa
**C · R0** · `shells.orc`: patear el caparazón, que choque con un Rex,
agarrarlo (Y) y soltarlo; pisar el Koopa `$02` con caparazón.

#### R4 — Meta `$7B` (x `$12E0`)
**C · R0** · `goal.orc`: cortar la cinta a distintas alturas; pasar sin
cortarla. Grabar hasta el fin de la secuencia (`rec all`).

#### R5 — Power-ups (D12)
**C · R0** · un guion por objeto: seta (bloque volador), flor (bloque `?`
con Mario grande) y disparar, estrella, 1-UP, luna 3-UP, champiñón
invisible `$C7`, bloques `!`, monedas de Yoshi (las 4 + la 5.ª cuenta),
morir (caer y tocar enemigo), punto medio.
Puerta: `orc_has.py` muestra cada objeto y el cambio de `$19`/`$71`.

#### R6 — Estrés (= O2)
**C · R0** · `stress_back.orc` (volver a toda velocidad sobre s ≈
2600-2900 y 4100-4800), `stress_sprites.orc` (Banzai + 4 Rex + Mario a la
vez), `stress_piranha.orc` (las 2 pirañas del frame 9714 con Mario
corriendo) y `stress_vert.orc` (subir la cámara lo más posible: saltos a
toda carrera desde las tuberías y rebotando en Rex; da el mínimo de
`Bg1VOfs` para S8). Puerta: `orc_has.py` confirma los sprites a la vista a la vez;
la cámara (`$1A`) recorre esos tramos.

#### R7 — Contadores del HUD en el volcado
**M · — · `tools/snesorc/orc.c`, `tools/oracle2bin.py`, `tools/marioverify.c` (solo lectura del formato)**
- Hace: agregar al registro las direcciones del HUD (vidas `$0DBE`,
  monedas `$0DBF`, tiempo desde `$0F31`, puntuación desde `$0F34`, monedas
  de Yoshi, reserva; exactas en `equates/memory.i`) **sin romper el
  formato viejo** (campo nuevo al final, opcional).
- Puerta: `snesorc_make.sh --replay` sigue dando 6871/6871; los `.txt`
  viejos se leen igual; `regress.py` OK.

#### R8 — Audio de referencia
**M · — · `tools/snesorc/orc.c`**
- Hace: `--wav X.wav` que vuelque la salida del SPC700 emulado por
  snesrev en la misma corrida del guion.
- Puerta: el WAV de `normal.orc` suena (tema del nivel + saltos) y dura lo
  que el guion a 60 frames por segundo (la SNES NTSC). Documentar cómo se
  alinea con los frames de la Amiga, que van a 50.

#### R9 — La zona de la tubería
**C · R0** · `pipe.orc`: el camino de `oracle_yi1` hasta la tubería del
frame 11425, entrar, recorrer las 2 pantallas de `obj-1.lv` (monedas
incluidas) y volver a salir. Puerta: `orc_has.py` muestra el cambio de
subnivel y la vuelta.

#### R10 — Los huecos de la cobertura (2026-10-03)
**C · — · `tools/snesorc/*.orc`** · grabaciones para lo que
`docs/cobertura.md` ("Notas (a mano)") dice que ninguna recorre y le importa
a YI1: salto con giro sobre un Rex (`spr_spin_kill`), matar al Chuck (tres
pisotones o estrella: `chuck_die`, `chuck_run`), mirar arriba parado
(`mario_CEB1`), el caparazón aturdido y el Koopa que entra al caparazón, y
confirmar si hay bloques giratorios. Puerta: `python3 tools/coverage.py`
deja de listar esas funciones (o explica por qué siguen sin correr).

### S — Scroll ≤ 25 % (ROADMAP Etapa 6.4 y §9.2)

Todas: Lee ROADMAP Etapa 6.4 y §9.2, AGENTS P39-P46, P50, P51, P59, P71,
P72; `player/scroll.s` (`build_mid`), `tools/mkscroll.py` (formato MLD).
Puerta común: `scrollsim.py --speed 2 --ret` ≤ 9282 px e ida = vuelta;
capturas FS-UAE en x = 500, 1000, 1700, 2500, 3500, 4500 con `imgdiff.py`
IDÉNTICAS (o `scroll_check --mid` ≤ base si cambia a propósito);
`game_build.sh` + `gamecheck.py` 0; el peor frame de `scrollprof.py` a 2 y
4 px/frame **en los dos sentidos**, antes → después.

#### S1a — Cargas "tarde" con clasificación fija y celda de 8 px
**M · — · `scroll.s`, `mkscroll.py`** · P71: "tarde" (a > 0 o b ≤ 0) se
decide en `mkscroll.py` y va en MLD; la línea con una tarde viva es
canónica (s0 = s) y la h de la tarde solo cambia cada 8 px de s.
Puerta extra: en s = 4580 las 24 líneas que hoy se reescriben en cada frame
pasan a reescribirse cada 4 frames (2 px/frame).

#### S2 — LNS por grupos de 16 líneas
**M · — (se puede con S1a en la misma tarjeta)** · el mínimo de cada
grupo para saltarlo entero. Puerta extra: `scrollprof.py --zones`
muestra el recorrido de LNS por debajo de ~1 500 ciclos.

#### S4 — Editar en el sitio **(F)**
**F · S1a** · terminar `tools/wip64/build_mid_incremental.s`: rebase de la
h de cada WAIT, append y truncado por la derecha.

#### S5 — Presupuesto por frame (EDF) **(F)**
**F · S4** · cola por plazo con tope de ciclos; neutralizar en el sitio las
cargas muertas (MOVE a `$1FE`).

#### S3 — Un segmento para las dos listas **(F)**
**F · S4** · pool de 2 ranuras por línea + reenganche. El primer paso es
medir con `copcal.s` si la "columna vertebral" de saltos entra en el
borrado (P43, P46); si no entra, documentar por qué y descartar.

#### S6 — Un plan por sentido **(F)**
**F · S5** · plan ALAP para ir a la izquierda (o cargas centradas en su
ventana), elegido por la dirección de la cámara; otro MLD en slow RAM.

#### S8 — La cámara vertical de YI1 (`docs/plan-tecnico.md` §10.2b) **(F)**
**F · R6 (el mínimo de `Bg1VOfs`) · `scroll.s`, `mkscroll.py`, `game.s` (pasarle cam_y)** ·
ventana de datos extendida K líneas hacia arriba; punteros de PF1/PF2 con
(cam_y − 192) y la mitad; segmentos del copper indexados por línea del
nivel, con la v de los WAIT parcheada cuando cambia cam_y. Puerta extra:
capturas del replay de `oracle_normal` en los frames 2672-2707 (la cámara
en `$BC`) iguales al esperado; `scroll_check.py` con cam_y ≠ 192.

#### S7 — Menos cargas desde el origen
**M · — · `mkleveld.py`, `mkscroll.py`** · primero la **estadística**
(nivel C: cargas por línea visible en todo el recorrido, histograma);
después, reparto de registros que reuse el que ya tiene el color.
Puerta extra: `regress.py --level` (`render_d`: 0 px contra la imagen
ideal) y menos cargas en total.

### L — Lógica ≤ 40 % (`docs/plan-tecnico.md` §9.3)

Todas: Lee `docs/plan-tecnico.md` §9.3 y 8.2, AGENTS P36-P38, P47-P49, P62-P64;
`player/logic68k.s` (cómo se reemplaza una rutina de C por asm solo en el
build de la Amiga, y cómo el asm cae al C en los casos raros); la función
de C que se reemplaza. Puerta común: regresión OK con los **cruces de RAM
entera** en `ok`; `abcheck.py HEAD~1 --sprites` con semántica IGUAL y los
ciclos del peor frame menores (dar el número).

#### L1a — Rama hacia arriba de `f7f4` en asm
**M · — · `logic68k.s`** · hoy `_f7f4` salta a `_f7f4_c` hacia arriba
(`mcam.c`, con el arreglo de P69). −~1 000 ciclos en los frames en que
Mario sube. Probar además con `oracle_normal`/`diagpipe` (las que mueven
la cámara en vertical: `marioverify ... loop`).

#### L1b — `sprite_run` + despacho de `sprite_main` en asm
**M · I1 · `logic68k.s`, `msprite.c` (solo quitar/poner `#ifdef`)**
Ojo: en la 8.2 partir `sprite_run` salió peor (vbcc deja de incorporar el
despacho): hacerlo entero.

#### L1c — `mario_E2BD` en asm
**M (grande; F si se traba) · — · `logic68k.s`** · ~4 000 ciclos por frame
hoy. Verificar también `marioverify gfx` en los 5 oráculos (lo corre
`regress.py`).

#### L1d — `spr_obj_interact`, `spr_obj_vert`, `spr_spr_interact`, `jumping_piranha` en asm
**M · I1 · `logic68k.s`** · una rutina por commit.

#### L2 — Descartes rápidos
**M · — · `msprite.c`** · `spr_spr_interact` y el contacto con Mario:
descartar por |dx| (y |dy|) antes de la caja completa, con el mismo
resultado.

#### L3 — Estado nativo de Mario **(F)**
**F · L1a-L1d** · ROADMAP 8.2 paso 2. Solo si después de L1-L2 el peor
frame sigue por encima del 40 %.

### MA — Mario en sprites (`docs/plan-tecnico.md` §9.4)

#### MA1 — No redibujar si la pose no cambió
**M · — · `player/mspr68k.s`, `player/game.s` (solo la llamada)** · clave
= punteros `wm_0D85` + `wm_Tile7FPtr` + OAM relativa (el recuento está en
`docs/plan-tecnico.md` §9.4: cambia en el 33,5 % de los frames). Doble buffer: redibujar
en el buffer libre solo si cambia.
Puerta: `gamecheck.py --spr` 6184/6184; la media de `mspr_draw` en Musashi
baja ~60 %; capturas del replay iguales.

#### MA2 — `mspr_draw` más barato por dentro
**M · MA1** · perfil por etiquetas y atacar lo que salga (§9.4 M4).
Objetivo ≤ 3 % en el peor frame.

### P — Sprites: lógica (ROADMAP Etapa 9.1)

Todas: Lee ROADMAP Etapa 9.1; AGENTS P27, P33-P38, P62, P65, P66;
`player/msprite.c` (cómo está hecho el Rex, el mejor ejemplo); la rutina
del ROM en `/home/user/smw-src-master/project/mw_e10/sprite_*.s` (buscar
el número en la tabla de punteros de `sprite_1-main.s`). Método:
**transcribir instrucción por instrucción** sobre `ram[]`, con el estado de
A, X, Y y `m0..` anotado en comentarios; tablas de otros bancos con
`tools/smwtabx.py`. Puerta común: `marioverify <oráculo>.bin game` con
`sprite XX: seguidos N exactos N` en la grabación que lo contiene, 0
resincronizaciones de Mario, y ninguna métrica existente peor salvo los
ciclos (anotarlos).

| tarjeta | nivel | depende de | qué | oráculo |
|---|---|---|---|---|
| **P1** | M | — | el Koopa `$BD` difiere 1 frame al empezar el nivel (frame 1455, ranura 7, `$AA`: port 0, ROM 3) en las 4 grabaciones de snesorc | `oracle_normal` |
| **P2** | M | — | `diagpipe`: `sprload` 31/33 (la ROM mete la piraña `$4F` en la ranura que un Rex deja libre en el mismo frame) | `oracle_diagpipe` |
| **P3** | M | R2, I1 | Clappin' Chuck `$95` | `oracle_chuck` |
| **P4** | M | R3, I1 | caparazones: rojo `$DB` (estado 9), Koopa `$02` con caparazón, patear, agarrar, soltar | `oracle_shells` |
| **P5** | M | R4, I1 | cinta de meta `$7B` y el disparo de la secuencia final (la secuencia en sí es Z3) | `oracle_goal` |
| **P6** | M | R5, I1 | seta (`$74`), 1-UP, champiñón invisible `$C7` dando la vida, luna 3-UP; lo que sale de los bloques | `oracle_<objeto>` |
| **P7** | M | R5, P6 | flor de fuego y **bolas de fuego** (sprites extendidos: hoy `MARIO_UNSUP_FIRE`) | `oracle_flower` |
| **P8** | M | R5 | crecer, encoger y morir de Mario (`$71`, hoy "sin física normal"); estrella (invencibilidad) | `oracle_<objeto>` |
| **P9** | M | R5 | monedas de Yoshi, monedas que salen de bloques, sprites de puntos | `oracle_yoshicoin` |
| **P10** | M | P6 | caja de reserva (lo que va y lo que cae) | `oracle_reserve` |

P6-P10 cambian cosas que hoy congelan el juego (el modo diagnóstico, P58):
comprobar con `tools/diag_read.py --sim` y con el replay que el motivo ya
no aparece.

### X — Traducción asistida 65816 → C (estudio)

Idea de reassembler: él convierte con Python el asm de la Mega Drive al de
la Amiga (mismo CPU). Nosotros no podemos reusar el 65816, pero sí
**generar el borrador en C** que hoy los agentes P escriben a mano
instrucción por instrucción, y dejar a mano solo lo que el traductor no
entiende.

#### X1 — `tools/x65c.py`: rutina del ROM → C del port **(F)**
**F · — · `tools/x65c.py` (nuevo), informe**
- Hace: dada una etiqueta de `smw-src-master` (p. ej. `ChuckMain`), emite
  C con el estilo de `player/spr_*.c`: `ram[]` con `R8/W8/RX8`, A/X/Y y
  `m0..` como locales, ancho de A y X seguido por `REP`/`SEP` (y avisos
  donde no se sabe), saltos como `goto`, `JSR`/`JSL` a funciones por
  etiqueta, tablas `.DB` por `smwtabx.py` (bloque `SMWTABX_<X>`, P78), y
  el flag C/Z/N solo donde se lee después. Lo que no sabe traducir lo
  deja como `spr_unsup()` con la instrucción en un comentario.
- Puerta: regenerar **tres sprites ya portados** (Rex, Chuck, caparazones)
  y que `marioverify <oráculo>.bin game` dé los mismos exactos que el C
  a mano, con las líneas tocadas a mano contadas. Informe: qué fracción
  sale sola, cuánto más lento es que el C a mano (`abcheck --sprites`) y
  si conviene usarlo para P7, P9 y P10.
- No toca: el C del port (los borradores van a `work/x65c/`).

#### G1 — Volver a correr los estudios con la configuración actual
**C · — · solo lectura + informe** · `oamstudy.py`, `d8demote.py`,
`copsim.py` con 256 px y 4 columnas adosadas **libres** (Mario usa 2: hay
que descontarlas), sobre `oam_yi1.txt` y, si se puede, sobre las
grabaciones de snesorc. Entrega: tabla de líneas que piden más columnas y
frames sin resolver.

#### G2 — Diseño **(F)**
**Documentado el 2026-10-05:** `docs/diseno-9.2.md` y `docs/plan-tecnico.md` §10.6.
G0 tiene medida real a 256 px en `docs/medida-g0.md`; G8 también corre como
opción en el 68000 (`docs/oam-amiga.md`). Usar esas interfaces y presupuestos
para las tarjetas siguientes; el banco sintético no completa G5.

**Reabierto el 2026-10-05:** la auditoría G3 excede tanto el banco chip de
64 KiB como el presupuesto slow con sus variantes actuales. Revisar
representación y deduplicación con GPT-6.1 Sol high; los casos reproducibles
están en `docs/informe-g3.md`. Resolver antes de fijar G4/G6.
Evaluar primero el remapeo de color por copper (una pose guardada una vez),
con los números de **V1** (prueba mínima de Rex, descartable, en paralelo):
ROADMAP, "Próxima sesión — banco y variantes G2/G3".

**F · G1** · documento en `ROADMAP.md` Etapa 9.2 (lo escribe el
coordinador con el informe del F): formato de los frames precalculados
por pose en chip, reuso vertical de canales, colores por fila, cuándo pasa
algo a bob, presupuesto de chip (hoy ~117 KB libres) y de CPU (≤ 8 %).
**Otros niveles (§11.8 de `docs/mas-alla-yi1.md`):** banco **por tipo de
sprite**, con una tabla de tipos que se carga por nivel; nada fijo al Rex.
Vale igual para G3 (`mksprgfx.py` recibe el nivel y los tipos).

#### G3 — Conversor `tools/mksprgfx.py`
**M · G2** · GFX `20` (Rex, Banzai) y los demás → frames de sprites
adosados + máscara de bob, con `--selftest` de ida y vuelta (como
`mkmario.py`). Puerta: autoprueba OK en todas las poses que aparecen en los
oráculos.

**Avance del 2026-10-05:** SG3F, 48 poses compuestas exactas, 241 fichas
observadas y 12 rechazos verificados. **Final pendiente:** 2593 variantes
con reservas de Mario requieren 145600 B con esta estrategia; el banco
estricto emite 1724 y rechaza 869. No es una cota mínima. Ver informe G3.
La puerta de la próxima sesión usa un **lote acotado** (tres trazas + Rex
legal) y topes de chip/slow explícitos: ROADMAP, "Próxima sesión — banco y
variantes G2/G3". Banzai, Piraña, Chuck, meta, power-ups y partículas
esperan sus tarjetas G8.

#### G4 — Asignador de columnas (C de referencia + asm)
**M (F si se traba) · G2 + G3 · `player/msprasg.c` (nuevo), `logic68k.s`** ·
objetos → columnas por franja de líneas; la referencia de verdad es
`copsim.py`, actualizado con ancho recortado, propiedad OAM y ventanas G0.
Reservar Mario primero y devolver una cola explícita de bobs para todo
objeto que no quepa; comprobar la reconstrucción de píxeles además de
comparar asignadores. Contrato completo: `docs/diseno-9.2.md`.

#### G5 — El copper: `SPRxPOS`/`SPRxPT` y colores por línea en `scroll.s` **(F)**
**F · G4 · `scroll.s`** · encaja con `build_mid` (misma lista); P39, P42,
P46.

#### G6 — `tools/sprcop_verify.py`
**M · G4** · ROADMAP §8.2 fila 9.2: el asignador del 68000 en Musashi sobre
los frames de `oam_yi1.txt` contra `copsim.py`. Puerta: 0 objetos sin
asignar a DMA o bob, y reconstrucción exacta de posición, pose, orden y
recorte. G9 verifica por separado la imagen final de WinUAE.

#### G8 — Rutinas de gráficos que escriben la OAM (2026-10-03)
**68000 opt-in verificado el 2026-10-05:** `docs/oam-amiga.md`.
No mover las rutinas al render: también modifican el estado lógico.
La activación por defecto depende de medir DMA y O5 integrados.

**F · — · `player/spr_rex.c`, `player/sprgfx.c` (nuevo), verificador** ·
el camino de `docs/automatizar-9.2.md` §0: portar `RexGfxRt` y
`SubSprGfx2Entry1` enteras, escribiendo la OAM ($0200-$03FF, $0420) como
la SNES, en vez de solo `get_draw_info`. El verificador compara la OAM
contra `<grabación>_oam.bin` (ya lo escribe `oracle2bin.py`: entradas
visibles por frame). Puerta: OAM igual en `oracle_yi1` en todos los
frames con Rex en pantalla; coste en `level_frame` medido con
`gamecheck.py --engine musashi`. Si cuesta mucho, compilarlo solo en el
render (O5) en vez de en la lógica.

#### G3a — `tools/mksprgfx.py` sin el formato final (2026-10-03)
**M · — · `tools/mksprgfx.py`** · la parte de G3 que no depende de G2:
decodificar el GFX 20 (Rex, Banzai) y los demás GFX de sprites del nivel a
fichas 8×8/16×16 con su máscara, y la prueba de ida y vuelta contra las
fichas que pide la OAM grabada (`oam_yi1.txt`). El empaquetado en sprites
adosados lo fija G2 después.

#### G9 — Comparación automática de la imagen de los sprites (2026-10-03)
**M · G5 · `tools/sprshot_cmp.py` (nuevo)** · renderizar en Python la OAM
de la SNES con los gráficos convertidos y compararla con la captura de
WinUAE en el mismo frame del replay (P57: centro del píxel). Puerta: 0
píxeles distintos en las zonas de sprite.

#### G7 — Bobs en PF1
**M · G5** · restaurar desde `BLK`; las dos copias del buffer circular;
cola de blits por interrupción (P31). Puerta: capturas del replay con el
Banzai como bob.

### C — Carga y memoria (ROADMAP Etapa 6b.1, D13)

#### C1 — `tools/memmap.py`
**M · — · nuevo** · ROADMAP §8.2 fila 6b.1: desde el listado de vasm y la
tabla del loader, todo lo que lee el chipset < `$80000`, alineaciones (8,
4, 2) y total de chip ≤ 512 KB. Puerta: sobre el `game.lst` de hoy da el
mapa de `AGENTS.md` §4.

#### C2 — Enlazado absoluto con vlink **(F)**
**F · C1** · direcciones fijas en chip y en `$C00000`; desaparecen P36 y
P52. `m68kverify`/`abcheck`/`gamecheck` aprenden a cargar en la dirección
fija (E3).
**Otros niveles (§11.8):** regiones separadas para lo común (código, Mario,
HUD) y lo de cada nivel (bloques, capa 2, plan del copper, gráficos de sus
sprites, muestras), así un nivel se reemplaza sin reenlazar lo común.

#### C3 — Compresor y descompresor
**M · — · `tools/lzpack.py`, `player/unlz.s` (nuevos)** · LZ simple y
rápido de descomprimir en 68000. Puerta: ida y vuelta en Unicorn sobre
`yi1_s.dat` y el binario; ciclos por KB medidos en Musashi.

#### C4 — Loader nuevo
**M (F revisa) · C2, C3 · `player/loader.s`, `tools/mkadf.py`** · recorre
la tabla de carga, comprueba `$C00000` (P8), descomprime y salta.
Puerta: el ADF arranca en FS-UAE y el replay coincide (capturas).

#### C5 — Tiempo de carga
**C · C4** · con y sin compresión, en FS-UAE; se queda la más rápida.

### H — HUD (ROADMAP Etapa 10, D11)

#### H1 — Medir el HUD
**C · — · informe** · con la cámara Y de la partida (192), cuántas líneas
ocupa la barra de la SNES y si la capa 1 aparece en ellas (desde
`yi1_d.dat` y la referencia de la capa 3).

**Medida conservadora entregada el 2026-10-05:** `tools/hud_measure.py`
y `docs/medida-hud.md`. Máscara inicial y cruces PF1 cuantificados;
la alineación raster exacta sigue pendiente de referencia PPU SNES.

#### H2 — Gráficos de la barra
**M · H1 · `tools/mkhud.py` (nuevo)** · tiles de capa 3 a 2 bpp (`gb-*`,
`gb-1` = caracteres) → bitmap de PF1 y la paleta de 7 colores. Puerta:
PNG comparado a simple vista con la referencia + autoprueba.

#### H3 — Overlay por copper
**M (F si la capa 1 aparece en esas líneas) · H2 · `game.s`, `scroll.s` (solo las líneas del HUD)** ·
PF1 apunta al bitmap fijo en esas líneas (retardo 0), PF2 sigue con su
paralaje. Puerta: captura con la barra.

#### H4 — Lógica de la barra + `marioverify hud`
**M · R7, H2 · `player/mhud.c` (nuevo), `marioverify.c`** · portar la
actualización de la barra de `game.s` del ROM; comparar los contadores
contra los grabados. Puerta: todos los frames.

#### H5 — Blitear solo lo que cambia
**M · H3, H4** · ≤ 2 % medido con O1.

### A — Audio (ROADMAP Etapa 11, D5)

**Método (tomado de reassembler, `github.com/djyt/sonic2mod`):** la
referencia no es un WAV sino **lo que el driver le escribe al chip**, tick
a tick, en la misma partida que el oráculo (él usa VGM de la Mega Drive;
nosotros, las escrituras al DSP de `snesorc`, que ya lleva el driver de
snesrev). Cada conversión se audita **nota por nota** contra ese registro
y queda un informe por tema (`docs/audio/<tema>.md`: notas N/N, tono,
volumen por canal, lo que falta). El WAV de R8 queda para oír, no para
medir. Referencia legible del driver: `smw_spc_player.c` de snesrev (el
N-SPC de SMW reescrito en C; el asm del SPC700 solo para dudas).

#### A0 — Registro del DSP en `snesorc` (la referencia de audio)
**M · — · `tools/snesorc/orc.c`, `tools/dsplog.py` (nuevo)**
- Hace: `snesorc --dsp X.txt` vuelca cada escritura al DSP (gancho en
  `dsp_write` de snesrev, `src/snes/dsp.c`) con el frame y el tick del
  driver: `KON`/`KOFF`, `P` (tono), `VOL`, `SRCN`, `ADSR`/`GAIN`, `FLG`,
  `EON`. `dsplog.py` lo convierte a notas por voz (inicio, fin, tono en
  cents, volumen, instrumento) y separa música de efectos (`$1DF9`/
  `$1DFA`/`$1DFC`).
- Puerta: con `normal.orc` las notas del tema de YI1 salen con el tempo
  esperado y se repiten en el bucle; los saltos de Mario aparecen como
  efectos en los frames del oráculo en que `$1DFA` cambia; el oráculo
  `.txt` sale idéntico con y sin `--dsp` (no cambia la emulación).

#### A1 — `tools/brr2pcm.py`
**M · — · nuevo** · BRR → PCM de 8 bits **con signo** (P7), sin sesgo DC,
`--selftest`. Puerta: correlación ≥ 0,99 contra las muestras del WAV de R8.

#### A2 — Estudio del formato N-SPC **(F)**
**F · A0 · informe** · qué hay en `sound/` del fuente y en
`smw_spc_player.c`, cómo se leen las secuencias, qué efectos usa el tema
de YI1, qué 3 voces quedan (D5), medido sobre el registro de A0 (qué voz
suena más, cuántas notas se pierden con cada elección).

#### A3 — Conversor de secuencias
**M · A0, A2 · `tools/nspc2ev.py` (nuevo)** · eventos con el periodo de
Paula precalculado, glissando/vibrato y ADSR como tablas por tick.
Puerta: `tools/audiocmp.py` (nuevo) contra el registro de A0, nota por
nota: N/N notas de las voces elegidas, inicio a ±1 tick, tono a ±5 cents,
volumen a ±1 dB; informe `docs/audio/yi1.md`.
**Otros niveles (§11.8):** eventos y muestras **por tema**; las muestras
compartidas (efectos) aparte. Vale también para A4.

#### A4 — Secuenciador del 68000
**M · A3 · `player/audio.s` (nuevo)** · tick por timer de CIA, escribe
`AUDxPER/VOL/LC/LEN`, sin mezcla. Puerta: en FS-UAE suena; el estado por
tick en Musashi = el render offline.

#### A5 — Efectos
**C · A4** · engancharlos a `wm_SoundCh1/2/3` (ya los escribe el port) con
prioridad sobre la voz de música que comparte canal.

#### A6 — Comparación
**M · A4, A0** · el estado de Paula por tick (Musashi: `AUDxPER/VOL/LC`
escritos por `audio.s`) contra el registro de A0 con `audiocmp.py`, en
el replay de `oracle_yi1`, alineado de 60 a 50 Hz (D15). Escuchar en
WinUAE con el WAV de R8 al lado, como control, no como puerta.

#### A8 — Auditorías por tema
**C · A3 · `docs/audio/`** · un informe por tema y efecto que use YI1
(nivel, estrella, meta, muerte, 1-UP...) con la salida de `audiocmp.py`
y lo que no se puede (eco, voces descartadas). Así se sabe en todo
momento qué está bien y qué no, sin escucharlo.

#### A7 — Coste
**C · A4** · ≤ 3 % medido con el método de `bench2.s` / O1.

### T — La zona de la tubería (`obj-1.lv`, D16; `docs/plan-tecnico.md` §10.10)

| tarjeta | nivel | depende de | qué | puerta |
|---|---|---|---|---|
| **T1** | M | I2, R9 | la zona convertida: capa 1 (tileset 3), capa 2, formato (d), `yi1b_s.dat` | `m16diff` contra el mapa de referencia de la zona (PC) o la imagen ideal; `render_d` 0 px |
| **T2** | M | P8, R9 | la lógica: animaciones de tubería (`$71`), la carga de la subzona (cabecera, posición de entrada) y la vuelta | `marioverify <oracle_pipe> game` sin resincronizaciones en la entrada y la salida |
| **T3** | M (F revisa) | T1, T2, G5 | en la Amiga: fundido, cambiar los punteros del scroll, la paleta y la cámara, y volver | capturas del replay de `oracle_pipe` dentro de la zona |

### Z — Pulido y entrega (ROADMAP Etapa 12)

| tarjeta | nivel | depende de | qué | puerta |
|---|---|---|---|---|
| **Z1** | M | P8 | muerte normal y reinicio implementados el 2026-10-05; punto medio y game over siguen en diagnóstico | oráculos enemigo 188/188 y caída 190/190; O5/user, cinco vidas, captura y coste en `docs/validacion-z1.md` |
| **Z2** | M | R5 | punto medio: el poste, el estado guardado, reaparecer ahí | grabación de R5 |
| **Z3** | M (F revisa) | P5, R4 | secuencia de la meta hasta el final | `oracle_goal` |
| **Z4** | C | — | tiempo agotado | guion que espera |
| **Z5** | M | — | fundidos por copper al entrar y salir | captura |
| **Z6** | M | G5 | Mario detrás del poste de la meta (prioridad sprite/capa 1) | captura en la meta |
| **Z7** | usuario/PC | todo | ADF final probado en WinUAE KS 1.2 y 1.3 (y A500 real, opcional) | — |
| **Z8** | M | Z3 | el replay completo hasta la meta como prueba de `regress.py` (ROADMAP §8.2 fila 12) | llega a la meta en el mismo frame que el oráculo |

### E — Deuda técnica

| tarjeta | nivel | qué |
|---|---|---|
| **E1** | M | P51: medir con `copcal.s` el copper después de `DDFSTOP` a 256 px y meterlo en el modelo (`scrollsim.py`, `mkscroll.py`) |
| **E2** | M | `scrollsim.py` supone que corren todos los segmentos: agregar una comprobación de que la lista termina donde tiene que terminar (P59) |
| **E3** | M | después de C2: `m68kverify`, `abcheck`, `gamecheck`, `gamesim` con la carga en la dirección fija |

### U — Usuario / PC (no se delegan)

| | qué |
|---|---|
| **U1** | jugar `work/live/game.adf` en WinUAE con teclado; si se congela, captura de la página 2 del diagnóstico → `diag_read.py --repro` |
| **U2** | Etapa 7: `cmp_ref.py` contra `SuperMarioWorldMap02.png` |
| **U3** | probar en una A500 real (opcional) |
| **U4** | arranque en KS 1.2 después de cada cambio del loader (C4) |
| **D1** | la compuerta de §2 de `ROADMAP.md` (O4) |

---

## 5. Lo que aprendió el coordinador (2026-09-30, 4 subagentes a la vez)

**De reassembler (2026-10-01; OutRun y Sonic en la Amiga, `djyt` en
GitHub):** porta desde el código original y reescribe solo la capa de
hardware; automatiza la conversión con Python; verifica contra lo que el
original le manda al chip (VGM) con un informe por elemento (notas N/N);
trabaja con Claude Code (`CLAUDE.md`, `agents.md`, `docs/` con
referencias y auditorías). Apunta a A1200/AGA o 68030, no a la A500.
De ahí salen A0/A8 (audio contra el registro del DSP) y X1 (borrador
de C desde el 65816).

- **Worktrees siempre**; el script (`wt_new.sh`) evita repetir a mano la
  copia de `work/` y `player/gen/`.
- Pedirles que **no toquen** `AGENTS.md`/`ROADMAP.md`/la base: tres de
  cuatro propusieron trampas con el mismo número (P59-P65).
- Los informes de los subagentes son buenos pero **no son verificación**:
  al integrar aparecieron un fallo que el subagente vio y dejó de lado
  (`gamecheck --spr` se colgaba: era P62, un fallo real en la Amiga) y un
  arreglo de otro (`scroll_check` a 256 px) que cambió los números de un
  tercero. Siempre volver a correr las puertas en el árbol integrado.
- Un aviso de tiempo ("quedan 15 minutos: redondeá") funciona: todos
  dejaron el árbol limpio y un informe completo.
- Las tarjetas con una **puerta automática exacta** salieron bien a la
  primera (9.1 contra el oráculo, snesorc contra `oracle_yi1`). La que era
  diseño con temporización (6.4) no cerró: esas van a nivel F y con un
  primer paso de medida.
