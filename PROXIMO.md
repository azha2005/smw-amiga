# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.**
> Se reescribe al cerrar cada sesión (`ROADMAP.md` §7); el texto anterior
> está en `docs/archivo/sesiones.md`. Estados: `ROADMAP.md` §1/§4 y
> `SUBAGENTES.md` §4. Ejecución: `docs/instrucciones-olas.md`.

**Escrito el 2026-10-08**, al cerrar la continuación de B35 en
**`g2t-b35`**. No está integrado en master y no se hizo push.

- B35: `307394a` + `dac4244` + `213ba3c` + `06e777f`. B4/B5 exactas en **3404 frames**,
  ABI intacta, segmentos exactos en **762 496 filas**. Paso 4c de OAM68K,
  ocho tests G5EV en regress, negativos y cinco hashes por defecto verdes.
- **Único intento en C agotado**: media 0,96–1,03 millones, máximo
  **2 405 022 ciclos sin DMA frente a 8000**. Sigue inviable en vivo.
  Perfil, comandos y memoria: `docs/informe-g2t-b35-1008.md`.
- Vivo `SPR_G5` + banco G3: slow libre 191 016 B. Tras reservar G5EV
  (133 040) y `g5_work` (29 952), quedarían **28 024 B estimados**, antes
  de caché B2bis, fotos, salidas y pila. Auditar todas las reservas juntas.
- En master siguen C1 (`7df7ebe`, `ab50698`), revisión L-OAM (`bf950d4`)
  y B2 (`876d28d`, exacta pero máximo 231 612 ciclos). G2T-A y su
  contrato siguen verdes. L-OAM/D1 siguen rojas; enemigos aún no visibles
  mediante el plan B35 en el juego.

## 1. La próxima sesión: viabilidad de B35, B2bis y Cpre

**Recomendación:** comenzar por la fase de medida de B35-asm; una
traducción directa no garantiza el presupuesto. Continuar o revisar las
entregas existentes de B2bis/Cpre en sus ramas antes de relanzarlas.
Cpre puede probar el emisor con datos offline; el plan en vivo espera
las puertas de rendimiento y memoria de B.

| tarjeta propuesta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **G2T-B35-asm: viabilidad del plan exacto** | Codex | núcleo del planificador y arneses opt-in; inicialmente sin juego ni scroll | `docs/instrucciones-g2t-b35-asm.md`: perfil, representación dispersa y microbenchmarks; B1 idéntico, ABI/PIC correctos, plan completo ≤ 8000 ciclos máximo; parar la integración si no hay ruta medida |
| **G2T-B2bis: envolvente barata de Mario** | según tarjeta | foto, clave MA1, caché/decodificación en slow y frontera B2/B3 | `docs/instrucciones-g2t-b2bis.md`: envolventes exactas; captura de clave ≤ 300 ciclos, acierto ≤ 600, fallo ≤ 12 000; sumar su memoria a la reserva de B35 |
| **G2T-Cpre: emisor con plan precalculado** | según tarjeta | `g5_emit`, listas del replay bajo `SPR_G5`, verificador y capturas WinUAE | `docs/instrucciones-g2t-cpre.md`: listas en regla y 0/57 344 px en ≥ 12 frames; coste contra control, sin declarar D1 cerrada |

Preflight: lint, regress `--baseline tools/baseline_pc.json --level`,
OAM68K completo (seis líneas `ok G2T-B5`) y A-T verdes. Repetir hashes
por defecto antes de cada commit opt-in. WinUAE cycle-exact por candado,
controles en la misma tanda, solo PIDs propios. Cierre según ROADMAP §7.

## 2. Después, en orden

1. Revisar e integrar las ramas solo después de repetir sus puertas.
   B35 sigue como control exacto WIP; integración en vivo únicamente con
   rendimiento y reservas completos. Completar G2T-C y cerrar G5a-bis
   como G2T cuando también se cumplan sus puertas visuales.
2. Ruta de la piraña en asm propuesta por la revisión L-OAM, con tarjeta
   detallada antes de implementarla. Conservar la puerta de lógica ≤ 40 %;
   el control de estrés acordado es l4 (295/32 fotos), sin rebajar D1.
3. G4+G6 y G5+G9 con todos los enemigos del lote G3; luego estrés con G5
   y S5 contra D1 (fotos omitidas ≤ 0,1 %, racha 1). P110 en el scroll:
   todavía 5110 px con el paso medido.
4. C2/C4 para liberar tablas CPU de chip y revisar slow; segundo PF1/G7.
5. Según dependencias: S8, P7/P9/P10, A0/A2, H2-H4 y T1.

## 3. Pendiente del usuario o de la PC

- U1: jugar `work/live/game.adf` con teclado, KS 1.2, 512 KB chip +
  512 KB slow; enemigos aún no dibujados, diagnósticos si congela.
- U2: comparación de capa 2 contra la referencia (`cmp_ref.py`).
- U3 opcional: A500 real.
- Mantener la rama B35 separada de master mientras siga inviable para
  el juego en vivo. No push sin instrucción explícita.
