# SW-Q recuperada: bloque volador y power-ups en OAM/G5L

2026-10-10. **Avance funcional, tarjeta completa pendiente. SW-S no iniciada.**
Se conservó y auditó el trabajo abandonado por límite de uso. El usuario
pidió cerrar antes de terminar las medidas de D1; se cancelaron los jobs
propios que esperaban el candado. No se modifica la regla de dos objetos
por foto ni se introduce una prioridad nueva para los efectos.

## Implementación

- OAM del bloque `$83`, sus alas y su estado usado: C de referencia y
  `player/swq68k.s` para el juego, dentro de SPR_OAM. También la OAM
  de seta, flor, estrella y 1-UP; pluma excluida por D12.
- Despacho de `$74/$75/$76/$78`, dirección animada de la flor y
  recepción de los power-ups (puntos/vidas siguen pendientes de SW-S).
- G5L incluye las formas nuevas con sus familias de color. Las poses
  legales de power-ups se derivan de PowerUpTiles/StarPalValues, porque
  los guiones actuales apenas muestran flor/1-UP y no crean una estrella.
  Banco G3 inmutable: no se reemplaza ni se versionan assets.
- `g4a traceall --merge` preserva las formas inventariadas previamente.
- Corrección de contenido de bloque: CODE_00F1AE lee BlockYPos, la X
  según P33. Antes se leía BlockXPos y podía producir moneda en vez de
  1-UP. `pw_1up`: 2216 frames sin resincronización de Mario.
- Padding de DMA limpia a 8 B: elimina dos violaciones de memmap.
- La restauración de SpriteProp solo se compila con SPR_OAM. La primera
  recuperación sumaba 138 ciclos al máximo del build por defecto; se
  eliminó ese coste innecesario y la regresión volvió a verde.
- BENCH: FBSR en gb_scroll_frame evita que vasm convierta una llamada
  lejana a build_mid en dirección absoluta (P102).

## Puertas ejecutadas

`work/swq/` conserva logs, ADF y capturas locales regenerables.

| puerta | resultado |
|---|---|
| lint final | RESULTADO: OK (`lint_final.log`) |
| regress --baseline tools/baseline_pc.json --level --g5l --bm1 | RESULTADO: OK (`regress_final.log`) |
| oam68k_gate.sh completo | OAM68K: OK (`oamgate2.log`), incluidos G2T-B2/B35 y RAM PC=68000 |
| sprite_oam_verify yi1, require 74,83 | 7211 despachos, RAM/mapa/marcas/ABI distintas 0; seta 67/67, bloque 388/388 |
| sprite_oam_verify pw_1up, require78 | 3198 despachos exactos, 1-UP 1/1 |
| sprite_oam_verify pw_flor, require75 | RAM/mapa/marcas/ABI distintas 0 en 3370 despachos; flor1/1; puerta global roja por Rex3770, no ocultada |
| g5l trace multi yi1 / pw_seta | 0 errores; 5657 / 552 fotos |
| g5l trace multi pw_1up / pw_estrella / pw_bloques | G4-1 TRACE: OK; en pw_estrella se informa 1 Rex sin forma |
| g5l game yi1 | G5L GAME: OK, regresión final |
| g5l game pw_seta, BM1 | G5L GAME: OK (`game_pw_seta.log`) |
| memmap replay BM1 | 510808 B chip, margen13480; 420720 B slow; 0 violaciones |
| memmap vivo BM1 | 522336 B chip, margen1952; 457040 B slow; 0 violaciones |

La puerta **all de pw_flor no pasa**: `g5ref.read_trace` rechaza la OAM
del Rex `$AB`, frame3770, ranura5 (`tracegate.log`). También la detecta
sprite_oam_verify (`oam_pw_flor.log`). El guion tiene 120 resincronizaciones
de Mario y la primera diferencia ocurre en MarioFrame3533. No se filtró
ese frame ni se cambió la comparación para pintar la puerta de verde.

## Capturas WinUAE cycle-exact

Todas contra OAM SNES, con sprshot_cmp, dos objetos por foto y arranque BM1.
Inspección visual realizada de1199.

| foto yi1 | objeto | píxeles | distintos |
|---|---|---:|---:|
|1199| bloque con alas |456|0|
|1249| bloque usado |242|0|
|1299| seta |208|0|

Mario también exacto en las tres:197,241,241 píxeles. En1199, Rex219/219
exacto. En1299 el bloque queda fuera del plan porque comparte filas con
la seta: sprshot_cmp confirma que no se dibuja, según la regla vigente.
Logs `cmp1199.log`, `cmp1249.log`, `cmp1299.log`; PNG en
`work/swq/shot<k>/shot.png`. No equivale a validar todas las poses.

## Reproducir e integrar

En Git Bash, PATH/VBCC/PY según reglas-ola-pc. Antes de compilar en otro
checkout es obligatorio regenerar los derivados, especialmente shapes.json:

```sh
python tools/smwtabx.py
gcc -O2 -DNOOAM -DSPR_OAM -Iplayer -o work/swq_host.exe tools/marioverify.c player/mario.c player/mcoll.c player/manim.c player/mgfx.c player/mcam.c player/msprite.c player/mspr.c player/spr_*.c player/gen/smwrom00.c
python tools/g4a.py traceall --merge --host work/swq_host.exe --recs yi1 normal pw_seta pw_flor pw_1up pw_estrella pw_bloques
python tools/g5l.py mk --types all
OUT=work/swq_replay sh tools/bm_build.sh
GDEFS=' ' OUT=work/swq_live sh tools/game_build.sh
python tools/memmap.py work/swq_replay/game.lst --data work/yi1_s_g5.dat
python tools/memmap.py work/swq_live/game.lst --data work/yi1_s_g5.dat
```

Tabla G5L94668 B, DMA limpia34760 B, frente a82376/30856 B con los
tipos anteriores: +12292 B slow y +3904 B chip. Repetir memoria al
integrar SW-M/SW-B: estas cifras pertenecen a este worktree aislado.

## Qué sigue, en orden

1. Integrar y regenerar inventario. Verificar split de chip/slow con
   los demás trabajos; el margen aislado de chip del vivo es1952 B.
2. Resolver/explicar el Rex3770 de pw_flor con L-DER. Repetir
   `python tools/g5l.py trace --types all --prefix oamb --traces yi1 pw_seta pw_flor pw_1up pw_estrella pw_bloques --multi`
   con trazas del código actual. La puerta global sigue pendiente.
3. Grabar una estrella real y flor/1-UP con más de una foto; verificar
   sus tablas/OAM, variantes de paleta y capturas por pose.
4. A/B BENCH: los ADF `work/swq_control_yi1_oam/game.adf` y
   `work/swq_candidate_yi1_oam/game.adf` quedaron preparados. Control =
   tipos anteriores; candidato = all. Comparten la lógica nueva: este
   par solo mide el coste incremental del dibujo, no todo el cambio
   histórico. Capturar por candado y decodificar con
   `python tools/game_read.py --auto --shot <PNG>`; agregar control HEAD
   anterior para medir también el coste de OAM/lógica. **No hay medidas
   nuevas de D1** en este cierre.
5. Repetir la barrida SW1 en1199-1449 y luego la puerta completa.
6. SW-S: empezar por el volcado opcional de RAM de los tres motores
   del oráculo; implementar lógica asm y comparar cada frame. El dibujo
   por G5L requiere decisión de fidelidad del usuario, o esperar G7.
   No se agregaron efectos compitiendo silenciosamente con enemigos.

Los insumos base que faltaban para oam68k_gate se regeneraron filtrando
las trazas existentes a AB/BD/02/B9 según informe-g2. Los duplicados
abandonados `player/gen/gen` se movieron a `work/swq/abandoned-gen`,
fuera de los archivos versionados.
