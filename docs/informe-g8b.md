# G8b — OAM de enemigos, WIP (2026-10-06)

Base de trabajo: `07d4047fc1c09aa848ecb222d7499c3db1daf933`, rama
`wt/g8b`, árbol `/workspace/wt-g8b`. **G8b no está realizada**: la puerta
PC pasa, pero el build 68000 opt-in queda bloqueado por el detector PIC.
El coordinador recibió la escalación; no se ampliaron los ficheros PIC
fuera del alcance autorizado. El hash del commit WIP se comunica en el
handoff (este informe forma parte de él).

## Implementación

`spr_gfx.c` escribe las fichas originales de Banzai `$9F` (16), piraña
`$4F` (cabeza 16×16 y cuatro fichas 8×8 de tallo), Chuck `$95` (cinco
ranuras, tamaños variables), cinta `$7B` (tres 8×8) y caparazón `$04-$07`
(ficha principal y dos ranuras de humo cuando corresponda). Las tablas
se extraen del fuente mediante `smwtabx.py`, sin versionar bytes derivados.

Los enganches quedan en la fase original de la lógica. Se preservan las
variantes sin OAM de Amiga, y el puente de piraña en `logic68k.s` llama a
la misma rutina C que el host cuando `SPR_OAM` está activo. El helper
de una ficha permite un índice temporal para cabeza/tallo y caparazones;
restaurarlo dentro de cada helper perdería las fichas adicionales.

`regress.py` exige muestras no vacías, igualdad total y orden cero de los
cinco tipos en sus oráculos, además de las métricas `oam_XX` existentes.
Se añade `stress_piranha` a los oráculos corridos. `sprite_oam_verify.py`
permite exigir otros tipos sin que un oráculo sin Rex falle por falta de
Rex: `--require` sigue teniendo `AB` por defecto, y la puerta general sigue
rechazando trazas vacías, OAM distinta, orden incorrecto y cualquier
diferencia de RAM/mapa/marcas/ABI.

## Evidencia PC

Build GCC `-O2 -DNOOAM -DSPR_OAM`. Despacho real en modo `game`, sin
inyectar pose ni temporales de SNES. Salidas: `work/g8b_*_pc.log`.

| Oráculo | Tipo requerido | Exactas / visibles | Fuera de orden |
|---|---|---:|---:|
| chuck | 95 | 599 / 599 | 0 |
| goal | 7B | 82 / 82 | 0 |
| shells | 05 | 526 / 526 | 0 |
| banzai | 9F | 391 / 391 | 0 |
| stress_piranha | 4F | 1552 / 1552 | 0 |

Todos los demás tipos portados de esas cinco grabaciones también dieron
OAM exacta. La regresión por defecto mantiene la OAM Amiga desactivada;
el host sí ejecuta las rutinas completas. Antes de ampliar la cobertura,
ninguno de estos cinco tipos tenía muestras OAM atribuidas.

Comando para regenerar las trazas (repetir para cada oráculo):

```sh
export VBCC=$HOME/vbcc PY=python3
SRC='player/mario.c player/mcoll.c player/manim.c player/mgfx.c player/mcam.c player/msprite.c player/mspr.c'
gcc -O2 -DNOOAM -DSPR_OAM -Iplayer -o work/marioverify_oam tools/marioverify.c $SRC player/spr_*.c player/gen/smwrom00.c
GAME_OAM_TRACE=work/g8b_chuck.trace work/marioverify_oam work/oracle_chuck.bin game
```

## Bloqueo 68000 y siguiente paso

`CDEFS='-DNOOAM -DSPR_OAM' sh tools/logicbench_build.sh` falla en
`piccheck.py`, que conserva su exigencia. El C extra desplaza los destinos
fuera de ±32 KB. Último listado opt-in:

```text
ERROR PIC: $00008792: 4EB900010C28 (jsr _powerup_from_block)
ERROR PIC: $0000A6F2: 4EB9000127BE (jsr _mario_E2BD)
ERROR PIC: $00010EE6: 4EB9000084D0 (jsr _mario_hurt)
ERROR PIC: $00012BCA: 4EF90000A8F0 (jmp _mario_E2BD_c)
PIC: 14879 instrucciones, 4 llamadas/saltos absolutos
```

Antes de esa puerta aparecieron referencias absolutas de vbcc P47 al
escribir dos veces `SpriteGfxTbl` en piraña. Tres variantes de acceso
permitieron diagnosticarlo; la última usa `logic68k_zero` como las rutinas
existentes, limitado a vbcc. El guard de direcciones C ahora pasa y el
detector de instrucciones descubre las cuatro llamadas anteriores.

Escalado al coordinador, sin rebajar oracle ni guard: autorizar puentes
en `player/pic68k.s` y reescribir **solo llamadas** a los tres destinos C
en `tools/logicbench_build.sh`; usar `PICJUMP` en el fallback de
`logic68k.s`. Después volver a compilar opt-in, correr los cinco
`sprite_oam_verify.py --require XX`, el cruce de RAM y el juego integrado.

## Validación y límites

Lint y regresión normal: `RESULTADO: OK`, sin actualizar baseline.
Cruce normal loop: 6547 llamadas, RAM distinta 0; spr: 6549, distinta 0.
`memmap` normal: chip **390704 B**, **0 violaciones**. La primera corrida
verde indicó 19 métricas mejoradas por ejecutar las rutinas de gráficos
completas en PC; los tiempos nuevos de juego registrados son de Musashi
sin DMA y no prueban la fluidez OCS. Los logs finales son
`work/g8b_lint.log`, `work/g8b_regress.log`, `work/regress.log`.

No se validó la OAM 68000 nueva, ni se midió su coste integrado, ni hay
captura nueva. No se activó OAM por defecto. Los puntos de bonus tras
cortar la cinta usan `ExOamSlot` en `$0200`, fuera del rango `$0300` de
atribución de sprites; siguen pendientes, igual que monedas/humo del
estado 6. La puerta de cinta comprueba su fase visible sin cortar.
No se añadieron IDs o coordenadas fijos a YI1 al motor.

## SHA-256 de los oráculos usados

| Oráculo | `.bin` | `_oam.bin` |
|---|---|---|
| chuck | `6b72eaaa941824b1f10b7ae860c5e81f0c73009238f2c8adc3007d5604b415fc` | `ab1f9c14bd938a7062403f747bb4f906b3539f2d6fb67b204c27d24aa5a1e2dd` |
| goal | `f3bfff711f18ec84542ae05fefc0c3b22a35136bed2361d4448531c16f1ca39c` | `8925e9c59d3f64c28a10d9526311c6a529a3cc42264ee396179045511400681e` |
| shells | `2b76d35b131c1ad08472867ffb8b273858a6747f99607a5d5811b39239894e24` | `453d4526645a757cc1b2f7727f4fb46d31faa8614c405260a6d3b0ad1a67ad71` |
| banzai | `6164ccfdd5671079f5456f6b91c961b5ef41f1b094c7568ee59cfd9a56f7cf28` | `6df92eb5ed1ef9003e38db94a5954a136238cc1e973e95bfcd040f7a78618ab0` |
| stress_piranha | `a9ac1c5f40db6298b1e39aad7588f79b2b84f4a9786ae4416a58fcbb2f1bea41` | `dbc13dd1ae89fd1ab54734dfb92567e278148c1397281d4d449667abc4799cbb` |

Trampas: ninguna nueva para numerar; aplican P47, P98 y P102.
