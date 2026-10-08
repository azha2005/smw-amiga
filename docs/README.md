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
| `pitfalls.md` | texto completo de las trampas P1-P109 (índice en `AGENTS.md` §8) |
| `formato-nivel.md` | assets, formato `.lv`, Map16, tileset, paletas, comparación contra la referencia |
| `formato-sprgfx.md` | formato SG3F de las poses de sprites (G3) |
| `diseno-9.2.md` | **G2**: diseño del dibujo de sprites desde la OAM, interfaces, presupuesto de memoria (§5). Revisado el 2026-10-06: banco acotado y loader SG3F/2 implementados; presupuesto concreto en informe-g3-final |
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
| `informe-g2.md` | 2026-10-06 | banco acotado 64528 B DMA / 72716 B tablas, remapeo copper evaluado y crecimiento G8b |
| `informe-g3.md` | 2026-10-05 | G3: formato anterior y banco que no entra; superado para el lote acotado por informe-g3-final |
| `informe-g3-final.md` | 2026-10-06 | SG3F/2, loader replay/vivo, negativos, memoria y arranque WinUAE verificados |
| `medida-d1-winuae.md` | 2026-10-06 | D1: traza v2 en WinUAE de `stress_back`/`stress_sprites` con `SPR_OAM`; compuerta roja, coste de la traza |
| `informe-loam-1007.md` | 2026-10-07 | L-OAM: FinishOAMWrite y Rex en asm, puertas RAM/OAM, perfiles y A/B de estrés |
| `informe-g5bis-1007.md` | 2026-10-07 | G5a-bis fase A parcial: máscaras y variantes exactas, ventanas vacías; B/C detenidas |
| `informe-coordinacion-1007.md` | 2026-10-07 | revisión independiente, integración parcial de L-OAM y bloqueo temporal de G5a-bis |
| `informe-g2t-1007.md` | 2026-10-07 | G2T: tres alternativas temporales, auditoría de 3404 frames, ocho recargas cycle-exact y barrera PAL255; contrato candidato |
| `instrucciones-g2t-a.md` | 2026-10-07 | **contrato G2T-A fijado** (§1-bis, corregido con medidas) y propuesta original como registro |
| `informe-g2t-a-1007.md` | 2026-10-07 | G2T-A: capacidad del hueco entre filas (P111), codo 231→243 (P110), 83 casos cycle-exact, puerta A-T verde en 3404 frames |
| `instrucciones-g2t-bc.md` | 2026-10-07 | G2T-B/C: plan del Rex en C/68000 idéntico a `g2t_ref.py` y emisión en el copper del juego, con puertas y paradas |
| `instrucciones-g2t-b2bis.md` | 2026-10-08 | G2T-B2bis: envolvente de Mario por pose con la clave MA1, caché en slow y decodificación exacta en asm en el render (≤ 300 ciclos en la interrupción) |
| `instrucciones-g2t-b35.md` | 2026-10-08 | G2T-B3/B5: `g5_plan` en C con segmentos perezosos y envolventes del Rex precalculadas (`bank.g5env`); PC = 68000 = `g2t_ref.py` byte a byte |
| `informe-g2t-b35-1008.md` | 2026-10-08 | B35: handoff completado, único intento en C, B4/B5 exactas en 3404 frames, OAM68K/regress/hashes verdes; máximo 2 405 022 ciclos, parada por coste y memoria reservada |
| `instrucciones-g2t-b35-asm.md` | 2026-10-08 | Viabilidad del planificador disperso/asm tras la parada de B35; misma salida B1, medida por componente y plan completo ≤ 8000 ciclos |
| `instrucciones-g2t-cpre.md` | 2026-10-08 | G2T-Cpre: emisor `g5_emit` y capturas WinUAE (0/57 344 px) con el plan precalculado en el replay, antes de terminar B |
| `instrucciones-revision-1007.md` | 2026-10-07 | revisión propuesta tras las dos paradas: diagnóstico de coste OAM y contrato temporal, antes de nueva implementación |
| `informe-revision-loam-1007.md` | 2026-10-07 | revisión L-OAM: coste de OAM por función en YI1 y estrés (Musashi y WinUAE), por qué el estrés sale peor, y una tarjeta (ruta de la piraña en asm) |
| `instrucciones-loam.md` | 2026-10-07 | L-OAM paso a paso: abaratar la OAM ampliada (paso 1 hecho y medido) |
| `instrucciones-g5a-bis.md` | 2026-10-07 | G5a-bis paso a paso: el Rex desde la OAM por frame, fases A (offline), B (C) y C (copper) |
| `instrucciones-olas.md` | 2026-10-07 | guía semi-detallada de las olas 3 a 8: orden, puertas, trampas y entorno de la PC |
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
| `archivo/diseno-9.2-2026-10-05.md` | diseño G2 anterior a la revisión del banco y memoria vivo/G8b |
| `archivo/sesiones.md` | **registro de sesiones**: cada cierre agrega el `PROXIMO.md` cumplido y qué se hizo (lo más nuevo arriba) |
| `archivo/roadmap-2026-10-05.md` | el `ROADMAP.md` completo antes de la reorganización del 2026-10-05 |
| `archivo/olas-2026-09-30.md` | el reparto original en olas de `SUBAGENTES.md` §3 |
| `archivo/historia.md` | handoffs del 2026-09-24 al 2026-10-01 y la tabla de etapas original |
| `archivo/etapas.md` | el paso a paso por etapa del 2026-09-26 |
| `archivo/plan-original.md` | el análisis de viabilidad del 2026-09-22 (antes `PLAN.md`) |
