# G8b — validación de OAM y puentes PIC (2026-10-06)

Continuación de [informe-g8b.md](informe-g8b.md), conservado como informe
histórico del WIP 0ef275b8e84dc874177a06c102165bb7036b32c5.
La puerta de OAM PC/68000 de los cinco tipos pasa. **SPR_OAM permanece
opt-in**: falta medir su coste en WinUAE cycle-exact con DMA/O5. No se
declara cerrada la puerta de rendimiento de ≤40 %.

## Cambio y corrección del diagnóstico

Las llamadas C de TUs concretos se redirigen al compilar opt-in:
mcoll→powerup_from_block, manim→mario_E2BD y manim→sprite_run.
Sus puentes están en pic68k.s, junto a mcoll y manim. La llamada lejana
a mario_hurt procede de **spr_rex.c**, no de spr_powerup.c como se atribuyó
en el informe WIP: el listado reveló el emisor real. Su puente se emite
inmediatamente después de spr_rex.code.s al formar msprite.code.s.
No se modificó el fuente de Rex.

La sustitución solo reconoce instrucciones jsr completas en el TU
indicado; no sustituye declaraciones, símbolos de datos ni otros TUs.
El fallback asm→mario_E2BD_c usa PICJUMP. Los puentes preservan retorno
y argumentos vbcc en la pila; a0 es caller saved. Los builds sin SPR_OAM
conservan las llamadas previas. PROF usa el mismo esquema en su directorio.

PICJUMP cuesta 32 ciclos de CPU sin DMA (LEA PC, ADDA.L inmediato,
JMP indirecto), además de la llamada al puente. Frente a BSR.W directo,
la llamada añade 32 ciclos; el fallback añade 22 frente a JMP PC directo.
La medida integrada de abajo incluye esos costes y las rutinas OAM.

Los listados opt-in muestran BSR.W (opcode 6100) hacia los puentes:

| Emisor→puente | logicbench, instrucción / delta | juego, instrucción / delta |
|---|---|---|
| mcoll→powerup | $8792 / $1504 | $8222 / $1506 |
| manim→E2BD | $A716 / −$0A76 | $A1A6 / −$0A74 |
| manim→sprite_run | $A7A2 / −$0AF6 | $A232 / −$0AF4 |
| Rex→hurt | $10F06 / $0080 | $10996 / $0080 |

piccheck.py sigue inspeccionando opcodes, sin listas permisivas ni cambios:

| Build | Instrucciones examinadas | Absolutas |
|---|---:|---:|
| logicbench normal | 13061 | 0 |
| logicbench SPR_OAM | 14882 | 0 |
| juego normal (regresión) | comprobado por game_build | 0 |
| juego SPR_OAM | 17241 | 0 |
| PROF normal | 13061 | 0 |
| PROF SPR_OAM | 14882 | 0 |

## Puerta contra los cinco oráculos

GCC host -O2 -DNOOAM -DSPR_OAM; binario real vbcc/vasm, CPU Musashi.
Las trazas proceden del despacho game del host, sin importar poses o
temporales no grabados de SNES. Se comparan RAM entera, mapa, marcas,
registros preservados, pila, todas las fichas visibles y su orden.

| Oráculo / tipo requerido | Despachos | RAM/mapa / marcas / ABI distintas | OAM exacta PC y 68000 | Orden distinto |
|---|---:|---|---:|---:|
| chuck / 95 | 5282 | 0 / 0 / 0 | 599 / 599 | 0 |
| goal / 7B | 3763 | 0 / 0 / 0 | 82 / 82 | 0 |
| shells / 05 | 4051 | 0 / 0 / 0 | 526 / 526 | 0 |
| banzai / 9F | 759 | 0 / 0 / 0 | 391 / 391 | 0 |
| stress_piranha / 4F | 4221 | 0 / 0 / 0 | 1552 / 1552 | 0 |
| **Total** | **18076** | **0 / 0 / 0** | **3150 / 3150** | **0** |

Todos los otros tipos portados presentes también pasan en cada grabación.
La puerta exige los tipos indicados, muestras no vacías y exactitud total;
la ausencia de Rex en banzai no relaja la exigencia. El tipo requerido por
defecto sigue siendo AB. Cada corrida comprueba además la limpieza de
las 128 Y y las 12 marcas del level_frame real.

Evidencia: work/g8b_chuck.png, g8b_goal.png, g8b_shells.png, g8b_banzai.png
y g8b_piranha.png. Referencia SNES arriba y reconstrucción OAM 68000 abajo,
con gráficos y paleta SNES. El preview admite otros tipos y un Banzai 64×64.
Artefactos derivados ignorados por git (R9); no son capturas OCS ni prueban
colores, remapeo o DMA Amiga.

## Cruce integrado, memoria y coste

m68kverify --engine musashi --mode loop --sprites --cross libport_oam.so:
6547 frames, 0 resincronizaciones; **6549 llamadas, 0 RAM distintas**.
La puerta OAM usa aparte el despacho game para conservar frames animados.

gamecheck --spr opt-in: **6313 frames de replay, 0 distintos del oráculo**;
Mario, dibujo asm y doble buffer **6184/6184**. 6310 frames medidos;
**0 superan 141875 ciclos PAL**. memmap: chip **390704 B**,
slow **214880 B**, **0 violaciones**.

Comparación con build normal de esta misma rama, toolchain cloud, Musashi.
Ciclos de CPU **sin DMA ni blitter**; no equivalen a WinUAE:

| Parte | Normal media / máximo | SPR_OAM media / máximo |
|---|---:|---:|
| level_frame | 28488 / 38950 | 38970 / 62110 |
| total integrado | 39029 / 119908 | 49295 / 132650 |

Level_frame opt-in: media 27,5 % y máximo **43,8 %** de un frame PAL
(frame 6141). Total: media 34,7 % y máximo **93,5 %** (frame 10587).
No se activa por defecto ni se afirma rendimiento ≤40 %: el máximo de
lógica ya supera ese umbral sin DMA y debe optimizarse/medirse en hardware.

Lint y regresión normal finales: **RESULTADO: OK**, 19 métricas mejoradas
intencionalmente por cobertura PC; sin modificar baseline. La regresión
incluye cinco puertas OAM no vacías y exactas con orden cero. Default
PC/68000: RAM loop 6547 y spr 6549 llamadas, 0 diferencias; memmap chip
390704 B y 0 violaciones. Logs: work/g8b_lint.log, g8b_regress.log,
g8b_cross.log, g8b_gamecheck.log, g8b_memmap.log y g8b_*_68000.log.

## Repetir trazas y puertas

Desde el worktree, con fuente/ROM y derivados autorizados preparados.
Los binarios y trazas se escriben en work; nunca versionarlos:

~~~sh
export VBCC=$HOME/vbcc PY=python3
python3 tools/smwtabx.py
CDEFS='-DNOOAM -DSPR_OAM' sh tools/logicbench_build.sh
cp work/logicbench.bin work/g8b_logicbench.bin
cp work/logicbench.lst work/g8b_logicbench.lst
SRC='player/mario.c player/mcoll.c player/manim.c player/mgfx.c player/mcam.c player/msprite.c player/mspr.c'
gcc -O2 -DNOOAM -DSPR_OAM -Iplayer -o work/marioverify_oam tools/marioverify.c $SRC player/spr_*.c player/gen/smwrom00.c
gcc -shared -fPIC -O2 -DNOOAM -DSPR_OAM -Iplayer -o work/libport_oam.so $SRC player/spr_*.c player/gen/smwrom00.c
for entry in chuck:95 goal:7B shells:05 banzai:9F stress_piranha:4F; do
    name=$(printf '%s' "$entry" | cut -d: -f1)
    kind=$(printf '%s' "$entry" | cut -d: -f2)
    GAME_OAM_TRACE=work/g8b_$name.trace work/marioverify_oam work/oracle_$name.bin game > work/g8b_${name}_pc.log
    python3 tools/sprite_oam_verify.py --bin work/g8b_logicbench.bin --lst work/g8b_logicbench.lst --trace work/g8b_$name.trace --oracle work/oracle_$name.bin --require "$kind" > work/g8b_${name}_68000.log
done
python3 tools/m68kverify.py --engine musashi --mode loop --sprites --cross work/libport_oam.so
CDEFS='-DNOOAM -DSPR_OAM' NOCC=1 OUT=work/g8b_game sh tools/game_build.sh
python3 tools/gamecheck.py --bin work/g8b_game/game.bin --lst work/g8b_game/game.lst --engine musashi --spr
python3 tools/memmap.py work/g8b_game/game.lst
# Evidencia opcional por tipo; para los otros, cambiar traza/oráculo/require.
python3 tools/sprite_oam_verify.py --bin work/g8b_logicbench.bin --lst work/g8b_logicbench.lst --trace work/g8b_banzai.trace --oracle work/oracle_banzai.bin --require 9F --preview work/g8b_banzai.png
PROF=1 CDEFS='-DNOOAM -DSPR_OAM' sh tools/logicbench_build.sh
PROF=1 sh tools/logicbench_build.sh
# Restaurar default y correr la red de seguridad antes de commit.
python3 tools/lint_port.py && python3 tools/regress.py
~~~

## SHA-256 y limitaciones

Oráculos originales .bin y _oam.bin: hashes completos en el informe
WIP, sin cambios. Baseline cloud usado, sin editar:
fe0cc505198638488914fe8a761ddf8a3b78bb937eba446ef095e1c040621990.

| Artefacto | SHA-256 |
|---|---|
| g8b_logicbench.bin | 7299feae3401b6236256f8cbf7d9b3825880e602480bbfa51fc60aa089d72d96 |
| g8b_logicbench.lst | e2b165b8ed543560d1141c91f1633881ab5cdce5fbbe219e04cc9bcb9f666ecf |
| g8b_game/game.bin | f72cac5bff26ea2325703f29c1161b0f2fdaa59bdcc6d674838744257933ae1d |
| g8b_game/game.lst | d21043b3a1c851e2b049aa473a82656970b4d876f5a90258d9726023ac7dee1a |
| g8b_chuck.trace | 83a73c6a3bf7d2ce90e5e6d86585e06d1e05dcf8056debb19cb0166377e981ca |
| g8b_goal.trace | 90408b7acd037ab7ddde3105031735cc3cc6b8df791c83a1f2ec9cf55e857a8f |
| g8b_shells.trace | 43f901b50fa2cbc0f1d1aaf4ae78f54bc7e7347fa0bb35894990c51086447829 |
| g8b_banzai.trace | a341385a1f525e3c7fd3eec9941884a8437c33556fa16056c572a2616faa883c |
| g8b_stress_piranha.trace | 24ed34f5dd5a311a74f65478e01f52fdc570e42319fdff45a364dee9faf625c3 |

No hay captura/medida WinUAE nueva. Los puntos de bonus tras cortar meta,
en ExOamSlot $0200, y las monedas/humo del estado 6 siguen pendientes;
las 82 muestras exigidas de 7B corresponden a la cinta visible sin cortar.
No se amplió el asignador OCS, el renderer de enemigos ni el remapeo.
No se añadieron coordenadas fijas de YI1 al motor. Ninguna trampa nueva
para numerar: P47/P98/P102 siguen aplicando.
