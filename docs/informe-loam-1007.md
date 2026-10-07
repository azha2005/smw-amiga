# L-OAM: Rex y FinishOAMWrite en asm (2026-10-07)

Base: `53c488b`, con el paso 1 `4b713c4` ya integrado. Worktree
`C:/Users/JC/Downloads/sma/wt-loam-1007`, rama `wt/loam-1007`.
Se siguieron `instrucciones-loam.md`, `reglas-ola-pc.md` e
`instrucciones-olas.md` parte 1. La implementación no cambia baselines,
puertas, algoritmos ni la fase de la OAM. El C original sigue siendo
la referencia del PC/NOASM; solo LOGIC68K usa las dos rutinas asm.

## Commits

| hash | cambio |
|---|---|
| `e8ec165` | FinishOAMWrite en asm, coordenadas y scroll en registros |
| `bbdf201` | RexGfxRt en asm, dos fichas desenrolladas en orden 1,0 |
| `cd5001c` | conserva entrada C `rex_gfx` que verifica `game_build`, como puente al asm |

`bbdf201` pasó la RAM/OAM y abcheck pero **no armaba el juego OAM**:
`game_build` busca `_rex_gfx` en el C generado para comprobar que C y
asm comparten SPR_OAM. `cd5001c` conserva ese punto de entrada sin cambiar
la comprobación. Su coste está incluido en todos los números finales.

## Original y temporales

Se leyeron completas RexGfxRt y FinishOAMWriteRt, con CODE_01B844 y
CODE_01C9BF, en `../smw-src-master/project/mw_e10/`.

- Rex: GetDrawInfo puede volver antes de dibujar, conservando sus efectos
  originales. En la vía visible escribe m0/m1 (coordenadas en pantalla),
  m2 (dirección) y m3 (pose por dos). Las fichas se escriben 1,0 y después
  FinishOAMWrite sobrescribe m0-m11. No lee scratch externo dentro del bucle.
- Finish: m0/m1 = Y de sprite, m2/m3 = X; m6/m7 = posición baja menos
  scroll bajo; m8 = contador final; m11 = tamaño. m4/m5 y m9/m10 son las
  posiciones de nivel de la **última** ficha. Los desplazamientos tienen
  signo y la suma de coordenadas envuelve a 16 bits. También se conserva
  el wrap de 8 bits de los índices y el orden de escrituras OAM.
- Las tablas Rex del asm tienen los mismos 50 bytes que el original;
  solo existen con SPR_OAM y son relativas al PC. RAM y tablas del C
  siguen por a4; se preservan d2-d7/a2-a3.

## Perfil por función, frame 3097

Musashi sin DMA, build PROF sin inline, `oracle_stress_back.bin`,
`--sprites --every 4 --worst 3 --at 3097`. Los ciclos son propios,
sin llamadas. Sirven para atribuir coste, no para medir la A500.

| estado | frame | FinishOAMWrite | RexGfxRt | puente C Rex | limpieza level_frame |
|---|---:|---:|---:|---:|---:|
| base sin OAM | 58008 | 0 | 0 | 0 | 2728 |
| base con OAM | 77756 | 8704 | 7150 | 0 | 2728 |
| Rex C locales + atributos/tamaño, descartado | 77796 | 8704 | 7190 | 0 | 2728 |
| Rex C solo scratch local, descartado | 77996 | 8704 | 7390 | 0 | 2728 |
| Finish asm (`e8ec165`) | 74280 | 5836 | 7150 | 0 | 2728 |
| Rex asm sin entrada C (`bbdf201`, no arma game) | 72570 | 5836 | 5440 | 0 | 2728 |
| ambas asm + entrada C (`cd5001c`) | 72900 | 5836 | 5440 | 330 | 2728 |

Logs: `work/loam_{base,rex,rex2,finish,rexasm,rexentry}_oam_prof.txt`;
control sin OAM: `work/loam_base_nooam_prof.txt`.
Binarios/listados preservados en `work/prof/loam_<estado>_<variante>.*`.

Los dos intentos Rex C pasaron RAM/OAM pero subieron los ciclos, por eso
se descartaron sin commit, según §3.4. Tras la aclaración del coordinador
sobre la parada §5 (Rex **y** Finish en asm) se escribió Rex asm.

## A/B en lazo cerrado

`CDEFS='-DNOOAM -DSPR_OAM' python tools/abcheck.py BASE --sprites`.
En todos los estados se mantuvieron 6547 frames, 0 resincronizaciones,
tramo 3824 y `semantica: IGUAL`.

| comparación | media | p99 | máximo | salida ciclos |
|---|---:|---:|---:|---|
| base → primer Rex C | 36284 → 36287 | 50306 → 50314 | 52304 → 52312 | SUBEN, descartado |
| base → segundo Rex C | 36284 → 36303 | 50306 → 50354 | 52304 → 52352 | SUBEN, descartado |
| base → Finish asm | 36284 → 35555 | 50306 → 48788 | 52304 → 50812 | iguales o menos |
| Finish → Rex asm sin entrada C | 35555 → 35423 | 48788 → 48446 | 50812 → 50470 | iguales o menos |
| Rex sin entrada → entrada C | 35423 → 35449 | 48446 → 48512 | 50470 → 50536 | SUBEN, coste necesario de interfaz |
| Finish → Rex final con entrada C | 35555 → 35449 | 48788 → 48512 | 50812 → 50536 | iguales o menos |

La comparación contra `bbdf201` descubre y cuantifica el coste del puente;
no se declara verde. La optimización Rex final sí baja frente al build
válido previo, `e8ec165`. No se cambió ningún límite para aceptarla.
Logs: `work/loam_*_abcheck.log` y
`work/loam_rexentry_finish_abcheck.log`.

Máximos `sprite_run` de `oam68k_gate`, sin DMA:

| oráculo | base | Finish asm | Rex final |
|---|---:|---:|---:|
| yi1 | 14320 | 12858 | 12858 |
| chuck | 17486 | 15406 | 15406 |
| goal | 17486 | 15406 | 15406 |
| shells | 17486 | 15406 | 15406 |
| banzai | 18414 | 16334 | 16334 |
| stress_piranha | 17486 | 15406 | 15406 |

Logs preservados: `work/loam_{rex,finish,rexentry}_cycles.txt` y
`work/oamgate/*_68000.log`. El primer intento C no modificó máximos,
por lo que su tabla también sirve para los máximos base.

## WinUAE cycle-exact

Tanda final `l4`: `sh tools/stress_ab_build.sh l4` dio:

```text
ok     work/l4_back_nooam/game.adf
ok     work/l4_back_oam/game.adf
ok     work/l4_sprites_nooam/game.adf
ok     work/l4_sprites_oam/game.adf
ok     work/l4_yi1_nooam/game.adf
ok     work/l4_yi1_oam/game.adf
STRESS_AB_BUILD: OK
```

Las seis capturas se corren con `tools/stress_ab_shots.ps1 -Prefix l4`,
sus copias por slot y el candado compartido. Cada configuración usa PAL,
`cycle_exact=true`, `cpu_speed=real`, `immediate_blits=false`.
El build l3 (solo Finish) se conserva; no se capturó: §4 permite la tanda
después de 2-3 pasos y el perfil/abcheck atribuyen cada función por separado.

`STRESS_AB_SHOTS: OK (6 capturas)` y salida completa de
`sh tools/stress_ab_read.sh l4`, sin repetir ni descartar capturas:

```text
build                  fotos perdidas    racha level_frame max  total medio
l4_back_nooam          145 (3.51 %)          3 55.0%            46.2%
l4_back_oam            295 (7.15 %)          6 73.9%            54.3%
l4_sprites_nooam       0 (0.00 %)            0 53.7%            40.9%
l4_sprites_oam         32 (1.67 %)           2 70.7%            48.6%
l4_yi1_nooam           14 (0.22 %)           1 29.5%            31.3%
l4_yi1_oam             27 (0.43 %)           1 41.2%            38.1%
STRESS_AB_READ: OK
```

Logs: `work/loam_stress4_{build,shots,read}.log`, capturas y decodificación
en `work/l4_<escenario>_<variante>/{bench.png,read.txt}`. Las seis tienen
sincronía OK. Se inspeccionaron visualmente las tres capturas OAM:
pantallas BENCH completas y limpias, con sus filas de resultados.

**Puerta de cierre §5: NO cumplida.** YI1 con OAM tiene `level_frame`
máximo **41,2 % > 40 %**. Back con OAM pierde **295 > 145** fotos del
control; sprites con OAM pierde **32 > 0**. Frente al paso 1 sí mejora:
back 616 → 295 fotos, sprites 56 → 32; YI1 máximo 43,1 → 41,2 %.
Esto es una mejora parcial y no autoriza declarar L-OAM terminada.

Se cumple la parada expresa tras Rex y Finish en asm: no se siguen
probando funciones ni se toca lógica fuera de la OAM. El coordinador
recibe la tabla para decidir la siguiente tarjeta; el informe se entrega
como WIP de la puerta de rendimiento, con las optimizaciones semánticas
verificadas. No queda trabajo sin commitear.

## Verificación final y control por defecto

Preflight: Python WindowsApps, `import machine68k, unicorn` → `ok`;
status vacío y las tres puertas verdes antes de editar
(`work/loam_base_{lint,regress,gate}.log`).

Últimas líneas repetidas sobre `cd5001c` (código) con este informe e índice,
`work/loam_final_{lint,regress,gate}.log`:

```text
RESULTADO: OK
RESULTADO: OK
ok     cruce RAM PC = 68000: cruce con el C del PC (RAM entera tras cada llamada): 6549 llamadas, 0 distintas
ok     logicbench por defecto restaurado
OAM68K: OK
```

La puerta también recorre yi1/chuck/goal/shells/banzai/stress_piranha,
todos `OAM 68000: fuera de orden 0`. No se reemplaza por la regresión PC.

Control opt-in: PROF sin OAM antes y después es idéntico byte a byte,
SHA256 `ec8147ac1989ab7e7714f1db3f3cebbc723730a980aa33158a6a41173e4dc37e`.
Juego BENCH back sin OAM l3/l4 también idéntico:
`66230bc599d96dea3cb3ab3eb35527401bccf55de3f8c4fce3238df809ef7338`.
Los juegos sin OAM de los tres escenarios l3/l4 se compararon con `cmp`:
todos idénticos. Hashes completos: `work/loam_default_hashes.txt`.

## Fallos y trampas sin número

- **Pnn sin número: const Rex eliminadas.** Al excluir Rex C en LOGIC68K,
  vbcc elimina sus const no usadas. El primer enlace asm falló con
  `error 3007: undefined symbol <_tg2_RexTiles>` (también X/Y/Prop).
  Se transcribieron los mismos 50 bytes al bloque asm relativo PC.
  Evidencia: `work/loam_rexasm_gate.log`, `OAM68K: FALLA (1)`.
- **Pnn sin número: la comprobación de modo usa el símbolo C.**
  `game_build` prueba SPR_OAM buscando `_rex_gfx` en el C generado.
  La versión solo asm pasó OAM68K pero stress build dio tres fallos:
  `ERROR: C y asm tienen distinto SPR_OAM; recompilar sin NOCC`.
  Se conserva la entrada C a la implementación asm. La comprobación queda
  intacta. Logs del fallo: `work/loam_rexasm_game_failed.log` y
  `work/loam_rexasm_stress_failed.log`.
- El hoist en C de Rex no garantiza ganar con vbcc: dos versiones
  equivalentes aumentaron ciclos. Se conservan sus perfiles y abcheck;
  ninguna quedó integrada.

No se tocaron la limpieza de OAM, otros algoritmos, G5, baselines ni
documentos de estado reservados al coordinador. No se usó FS-UAE.

**No medido/corrido:** capturas intermedias l3 (motivo arriba), FS-UAE
(no instalado en esta PC), hardware A500 físico (solo WinUAE cycle-exact).
No se declara alcanzada la puerta de rendimiento, ni se declara una
comparación visual del nivel: esta tarjeta mide el coste de la OAM y
comprueba todos sus bytes contra el original grabado y la RAM del PC.
