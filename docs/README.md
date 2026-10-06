# Índice de `docs/`

> Qué hay en cada documento y si está vigente. **Lo que se hace a
> continuación está solo en `../PROXIMO.md`**; el estado y los números
> vigentes, en `../ROADMAP.md` §1-§2. Un documento de esta carpeta no se
> usa para saber "qué sigue".
>
> Tres tipos, con reglas distintas:
>
> - **Referencia**: se mantiene al día; si cambia lo que describe, se edita.
> - **Informe**: la foto de una medida o de una tarjeta en una fecha. **No se
>   reescribe**; si una medida nueva lo supera, se escribe otro informe y se
>   actualiza `ROADMAP.md` §1-§2.
> - **Archivo** (`archivo/`): lo superado, textual, con la fecha y el porqué
>   en la cabecera. No se edita.
>
> Al agregar un documento, agregarlo aquí (`tools/lint_port.py` avisa si
> falta).

## Referencia (vigente)

| documento | qué |
|---|---|
| `plan-tecnico.md` | cómo hacer lo que falta: optimización (§9), cada bloque pendiente (§10), más allá de YI1 (§11). Escrito el 2026-09-30; sus números de estado son de esa fecha |
| `pitfalls.md` | texto completo de las trampas P1-P107 (índice en `AGENTS.md` §8) |
| `formato-nivel.md` | assets, formato `.lv`, Map16, tileset, paletas, comparación contra la referencia |
| `formato-sprgfx.md` | formato SG3F de las poses de sprites (G3) |
| `diseno-9.2.md` | **G2**: diseño del dibujo de sprites desde la OAM, interfaces, presupuesto de memoria (§5). Reabierto el 2026-10-05 por el tamaño del banco |
| `oam-amiga.md` | `SPR_OAM` en el 68000: opción, puertas y comandos |
| `decisiones-medidas.md` | datos con los que se cerraron D7, D8 y D9 y los resultados de la etapa 4 |
| `cobertura.md` | qué del C no corre con ninguna grabación (`tools/coverage.py`, con notas a mano) |
| `reglas-ola-pc.md` | entorno y reglas fijas para subagentes en la PC Windows |
| `mas-alla-yi1.md` | otro nivel y la lógica extra del juego (detalle de `plan-tecnico.md` §11) |
| `investigacion-ports.md` | qué hicieron otros ports y juegos de A500; tarjetas que salieron de ahí |
| `automatizar-9.2.md` | la idea de traducir la OAM (2026-10-03); antecedente de `diseno-9.2.md` |

## Informes (fotos con fecha; no se reescriben)

| documento | fecha | qué |
|---|---|---|
| `informe-d1.md` | 2026-10-03 | O4: peor frame y compuerta D1 (antes de redefinirla en fotos omitidas) |
| `estudio-g1-g0.md` | 2026-10-04 | G1 + G0: columnas de sprites a 256 px, DMA contra copper |
| `medida-g0.md` | 2026-10-05 | G0 real a 256 px en WinUAE |
| `medida-oam-o5.md` | 2026-10-05 | OAM + O5 en WinUAE cycle-exact: lógica, `build_mid`, fotos omitidas |
| `validacion-sx.md` | 2026-10-05 | SX/SX2 y P51: 24 capturas cycle-exact |
| `informe-g3.md` | 2026-10-05 | G3: formato verificable y banco que no entra |
| `validacion-z1.md` | 2026-10-05 | Z1: muerte y recarga del nivel |
| `medida-hud.md` | 2026-10-05 | H1: banda del HUD y cruces con la capa 1 |
| `informe-a1.md` | 2026-10-06 | BRR exacto, inventario PCM y límites de loops/R8 |
| `medida-d1-estres.md` | 2026-10-06 | replays y contador verificados; sin medida real de fluidez |
| `informe-g8b.md` | 2026-10-06 | entrega inicial PC exacta, bloqueo PIC; superado por validacion-g8b |
| `integracion-a1-g8b-d1.md` | 2026-10-06 | revisión conjunta, regresión, cobertura añadida y límites de hardware |
| `validacion-g8b.md` | 2026-10-06 | OAM PC/68000, puentes PIC, coste CPU sin DMA y límites |
| `experimentos-e11-e14.md` | 2026-10-06 | ronda offline: franjas PF2, conflictos PF1 y ocupación de Banzai |

## Archivo (`archivo/`)

| documento | qué |
|---|---|
| `archivo/sesiones.md` | **registro de sesiones**: cada cierre agrega el `PROXIMO.md` cumplido y qué se hizo (lo más nuevo arriba) |
| `archivo/roadmap-2026-10-05.md` | el `ROADMAP.md` completo antes de la reorganización del 2026-10-05 |
| `archivo/olas-2026-09-30.md` | el reparto original en olas de `SUBAGENTES.md` §3 |
| `archivo/historia.md` | handoffs del 2026-09-24 al 2026-10-01 y la tabla de etapas original |
| `archivo/etapas.md` | el paso a paso por etapa del 2026-09-26 |
| `archivo/plan-original.md` | el análisis de viabilidad del 2026-09-22 (antes `PLAN.md`) |
