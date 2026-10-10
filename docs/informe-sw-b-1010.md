# SW-B — recuperación y estado WIP (2026-10-10)

**No cerrada ni lista para activar.** Se recuperó la implementación abandonada,
se corrigieron agujeros y se cerró a pedido del coordinador sin nuevas tandas.
El cambio todavía modifica los defaults; antes de integrar hay que hacerlo
opt-in o resolver los cinco costes de regresión. No se cambió ninguna baseline.

## Implementación recuperada y corregida

- Inventario por celda y resultado Map16, bloques exactos y D_TCHG en +56;
  +52 sigue reservado para SW-M. 249 bloques, 33 entradas.
- Diario C de 256 cambios; cada foto captura su límite. El render consume
  hasta ese límite, incluso con fotos omitidas, actualiza D_MAP y las dos
  copias residentes de PF1. Reinicio restaura las celdas originales.
- Se agregó el resultado $048 de blocks_update, omitido en el trabajo previo:
  oracle_turn_block produce seis cambios $152/$048. La reserva de colores
  extiende intervalos del mismo color sin cruzar otro evento del registro.
- NODECOUPLE también aplica cambios y compila; tile_reset usa a3 (SMWS).
  BENCH usa FBSR para build_mid tras cruzar el alcance de BSR (P102).
- Referencia Python y scrollsim --tile-changes aplican el mismo mapa;
  tilechange_verify --replay-frames comprueba que el diario real tiene tabla.
- f17f usa BlockYPos para elegir contenido por columna, según CODE_00F1AE
  del fuente SNES; la versión abandonada ya incluía esta corrección P33.
- memmap reconoce D_COIN/D_TCHG opcionales y la migración BM1 de LNS+ a slow
  por bm_cpu_tail/bm_tail_end/g_cpu_tail. El coordinador ya copió ese soporte.

## Evidencia corrida

- `python tools/lint_port.py`: **OK**.
- `python tools/tilechange_verify.py --dir work/sw-b-turn --replay-frames
  work/sw-b-turn/frames.json`: 33/33 reemplazos, 50.688 píxeles de ambas
  copias PF1, 192.768 píxeles de colores del copper real, **0 diferencias**.
  Límites por foto, fotos omitidas, wrap256/u16 y reset OK; seis cambios
  reales de turn_block, ninguno sin representación.
- CPU Musashi sin DMA: ruta vacía 62 ciclos, cambio 862..2992, reset1820.
  No sustituyen una medida de WinUAE.
- `restart_verify.py --node --dir work/sw-b-node`: muerte219/fin410,
  RAM/mapa/carga OK (2.088.532 ciclos sin DMA).
- `scrollsim.py --g5 --from 3700 --to 4000 --tile-changes
  work/sw-b-changes.json`: 76 fotos, **0 píxeles** distintos.
- Barrida WinUAE existente k6049..6299 comparada con SNES recién generada:
  juego210/0/226/226/209/599 píxeles distintos; desaparecen las cajas16x16
  de giratorios, quedan trozos de SW-S, Rex y diferencias ya conocidas.
  Se inspeccionó visualmente k6049. Esa barrida precede al agregado $048.
- memmap selftest17 OK; todos los memmap de la regresión, sin violaciones.
  Contra el listado SW-M del coordinador: cola51.608 B, chip467.848,
  slow491.808, sin violaciones (no es una medida de SW-B integrado).

## Puertas que NO pasan / pendientes

`regress.py --baseline tools/baseline_pc.json --level --g5l --bm1`
terminó **FALLA (5)**. Todas las comprobaciones funcionales y cruces RAM
PC=68000 pasan, pero las reservas adicionales de color cuestan CPU:

| métrica | base | SW-B |
|---|---:|---:|
| game.build_mid.max | 81244 | 82080 |
| game.build_mid.media | 3513 | 3559 |
| game.total.max | 114430 | 115266 |
| scroll.ida.media | 14875 | 14913 |
| scroll.vuelta.media | 17283 | 17454 |

Los máximos de scroll mejoran: ida73718→73512, vuelta105786→105366.
La regresión anterior, sin representar $048, estaba verde; era incompleta
porque el replay de golpes generaba un resultado ausente. No volver a esa
omisión para aprobar la puerta.

`oam68k_gate.sh`: **FALLA(3)** por falta de `work/oam_{yi1,normal,spin_kill}.trace`;
no por una diferencia de OAM. Regenerar esas trazas y repetir.

La tarjeta nombra pw_bloques, pero ese guion prueba bloques ! punteados
atravesables y explícitamente no los golpea. Se usó turn_block para los
cambios reales. Falta completar su barrida WinUAE cada10 frames: se preparó
work/sw-b-turn-hold/game.adf (HOLDSTART2100, STOPF2190), pero se canceló
esperando un slot al cerrar. Falta comparar también los gráficos animados
de $048 contra la PPU; verificar colores del copper no demuestra esa fase.

Se preparó A/B yi1 BENCH en work/sw-b-control y work/sw-b-bench.
TILECONTROL consume el diario sin tocar D_MAP/PF1: mide el coste del render,
no elimina el coste C del productor. Se canceló la captura propia antes de
completarla; no hay números nuevos de D1 ni se afirma estar dentro del ruido.

## Continuación concreta

1. Hacer SW-B opt-in coherente en C, asm y mkscroll/builds (ficheros separados
   yi1_s*_swb.dat); default idéntico y regresión verde. O reducir costes
   conservando todos los resultados y colores exactos. No tocar baseline.
2. Repetir lint/regress completos y las pruebas anteriores con el opt-in.
3. Capturar turn_block con HOLDEVERY10/HOLDSTART2100/STOPF2190 por el candado;
   `sweep_cmp.py snes --dir work/sw-b-turn-hold --frames
   work/sw-b-turn/frames.json --script tools/snesorc/turn_block.orc`, luego cmp.
4. Medir ambos BENCH en la misma tanda con shot.ps1 -Exact, game_read.py
   --auto; añadir prueba del coste por cambio y comparar contra el control.
5. Al integrar SW-M/Q/A, unir R_TSEQ/R_COIN sin duplicar DC_REC, conservar
   D_COIN52/D_TCHG56 y repetir memmap replay/vivo: slow queda ajustada.

Logs regenerables: work/sw-b-final-gates.log, work/regress.log,
work/sw-b-turn-verify.log, work/sw-b-dynamic-scroll.log,
work/sw-b-oam-gate.log y work/sw-b-sweep/{cmp.log,sweep.json,cmp/}.
