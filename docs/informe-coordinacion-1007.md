# Coordinación L-OAM / G5a-bis — 2026-10-07

Base `53c488b`. Dos agentes GPT-6.1 Sol high en worktrees separados.
El coordinador revisó el código, repitió las puertas y miró la evidencia.
L-OAM se integró como **mejora parcial**, fusión `cb8ba8f`; ninguna de
las dos tarjetas se declara cumplida. Baselines y umbrales intactos.

## L-OAM: revisión e integración parcial

Commits de código: `e8ec165`, `bbdf201`, `cd5001c`; informe `1fcb5a1`.
El coordinador los reprodujo en `../wt-review-1007`, con commits de
revisión equivalentes `b6875bb`, `05fcf2e`, `600abf5`, antes de fusionar.
El build OAM de `bbdf201` falló también en la revisión; se comprobó
la corrección de interfaz `cd5001c` conservando la comprobación original.
Detalle de funciones, intentos C descartados y perfiles:
`docs/informe-loam-1007.md`.

Puertas independientes sobre el último código:

```text
lint: RESULTADO: OK
regress --baseline tools/baseline_pc.json --level: RESULTADO: OK
oam68k_gate: OAM68K: OK (RAM entera: 6549 llamadas, 0 distintas)
abcheck 53c488b --sprites, CDEFS='-DNOOAM -DSPR_OAM':
media 36284 -> 35449; p99 50306 -> 48512; max 52304 -> 50536
semantica: IGUAL; ciclos: iguales o menos
stress_ab_build coord4: STRESS_AB_BUILD: OK
stress_ab_shots -Prefix coord4: STRESS_AB_SHOTS: OK (6 capturas)
stress_ab_read coord4: STRESS_AB_READ: OK
```

La última línea del lector confirma capturas válidas, **no** el umbral
de rendimiento. Esta es la segunda tanda WinUAE cycle-exact, construida
y capturada por el coordinador, con controles en la misma tanda:

| build | fotos perdidas | racha | level_frame máx. | total medio |
|---|---:|---:|---:|---:|
| back_nooam | 145 (3.51 %) | 3 | 55.0% | 46.2% |
| back_oam | 295 (7.15 %) | 6 | 73.9% | 54.3% |
| sprites_nooam | 0 (0.00 %) | 0 | 53.5% | 40.9% |
| sprites_oam | 32 (1.67 %) | 2 | 70.8% | 48.6% |
| yi1_nooam | 14 (0.22 %) | 1 | 29.5% | 31.3% |
| yi1_oam | 27 (0.43 %) | 1 | 41.2% | 38.1% |

La tanda `l4` del agente se conserva en su informe. La tarjeta sigue roja:
YI1 supera el 40 % y el estrés con OAM pierde más fotos que su control.
Tras ambas rutinas en asm se cumplió la parada de
`docs/instrucciones-loam.md` §5. No se amplió la optimización a otras
funciones. Las pantallas BENCH de la tanda independiente fueron abiertas
y revisadas; los lectores exigen sincronía en cada captura.

Comprobación adicional del juego con `SPR_OAM` y banco G3:
`gamecheck.py --bin work/coord-replay/game.bin --lst
work/coord-replay/game.lst --spr`: 6313 frames, 0 distintos; Mario
6184/6184, también con buffers alternados. `memmap.py` replay/vivo:
0 violaciones, chip 455728/467256 B, slow 287712/323944 B.
El primer intento del arnés omitió `--lst` y emparejó el binario con otro
listado; se corrigió el comando y se repitió la prueba con el par correcto.
Replay por defecto idéntico a la base, SHA256
`9403f71c76bc2df9a92a3cc24d8db1e9e67c47e5e62a558e441c3994d0538109`.
Control `back` sin OAM idéntico al paso 1, SHA256
`66230bc599d96dea3cb3ab3eb35527401bccf55de3f8c4fce3238df809ef7338`.

Logs independientes: `../wt-review-1007/work/coord_{lint,regress,oam}.log`,
`coord_ab_final.log`, `coord_stress_build.log`, `coord_gamecheck.log`,
`coord_mem_{replay,live}.log`; seis `work/coord4_*/{bench.png,read.txt}`.

## G5a-bis: fase A detenida

Rama preservada `wt/g5bis-1007`, commit WIP `8fe712d`, worktree limpio.
Herramientas y tests permanecen en esa rama; el informe se copia a master
para conservar el diagnóstico sin integrar una tarjeta con puerta roja.
El coordinador repitió el plan sobre las tres trazas con salida separada
`../wt-g5bis-1007/work/g5ref_coord` y obtuvo exit 1, la parada esperada.
Su `resumen.json` es idéntico byte a byte al del agente, SHA256
`3d254a011312cfa88f6eb6e4ae2d4519c427a251469b0cdd16a5362f4722f8b7`.
La muestra de 12 frames fue abierta: se ven los errores de color.

| traza | frames con Rex | diferencias A2 | sin variante | sin plazo | errores color |
|---|---:|---:|---:|---:|---:|
| yi1 | 2288 | 0 | 0 | 40524 | 136142 |
| normal | 661 | 0 | 0 | 11595 | 35522 |
| spin_kill | 455 | 0 | 0 | 7217 | 23983 |

59318 ventanas vacías, 18 fallos de capacidad, 0 de armado fuera de
pantalla. Testigo: yi1 frame 5811, índice DMA 1 negro en y168 y blanco
en y169, ventana `[169,168]`. El modelo por líneas de A5 no permite
esa transición; asm de CPU más rápido no cambia ese plazo del copper.
El resultado no descarta un diseño con ventanas horizontales.
**B/C no iniciadas**, como exige `docs/instrucciones-g5a-bis.md` §3.

El coordinador repitió los 8 tests sintéticos (OK), lint (OK), regress
`--level` (OK) y OAM68K (OK) en esa rama. `work/regress.log` confirma
`test_g5ref.py` y `Ran 8 tests`. Cuatro hashes del juego por defecto,
incluido SPR_OAM+BENCH explícito, se conservan en el informe del agente.
Listas completas de frames y límites: `docs/informe-g5bis-1007.md`.

## Cierre

Se archiva el PROXIMO anterior textual y se reescribe en el sitio.
ROADMAP §1/§2/§4 y SUBAGENTES reflejan las dos puertas rojas. P109
documenta el contrato entre el símbolo C, las tablas y el build OAM.
El trabajo futuro y las decisiones pendientes quedan en PROXIMO.md.
No hubo push. Los worktrees de evidencia se conservan con estado limpio.
El árbol master integrado repitió lint, regress con baseline PC y --level,
y OAM68K, todos OK. Logs: `work/session1007_{lint,regress,oam}.log`.
La red confirmó nuevamente el cruce de RAM entera (6549 llamadas,
0 distintas); `git diff --check` pasó antes del commit de cierre.
