# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.**
> Se reescribe al cerrar cada sesión (`ROADMAP.md` §7); el texto anterior
> está en `docs/archivo/sesiones.md`. Estados: `ROADMAP.md` §1/§4 y
> `SUBAGENTES.md` §4. Ejecución: `docs/instrucciones-olas.md`.

**Escrito el 2026-10-07 (noche)**, al cerrar G2T-A.

> **Actualización 2026-10-08 (ola en curso, antes del cierre).**
> Integrado en master: C1 (`7df7ebe`, `ab50698`), la revisión L-OAM
> (`bf950d4`, `docs/informe-revision-loam-1007.md`) y el WIP de B2
> (`876d28d`: envolvente exacta, pero 231 612 ciclos contra 3000).
> Siguiente: tres tarjetas en paralelo, con instrucciones detalladas:
> `docs/instrucciones-g2t-b2bis.md`, `docs/instrucciones-g2t-b35.md` y
> `docs/instrucciones-g2t-cpre.md` (la única con WinUAE). Después, la
> ruta de la piraña en asm (tarjeta propuesta por la revisión L-OAM; la
> puerta de estrés de L-OAM se redefine como «no peor que la medida
> `l4`», 295/32 fotos omitidas, salvo otra decisión del usuario).

- **G2T-A hecha, contrato fijado** (delegación del usuario):
  `docs/instrucciones-g2t-a.md` §1-bis, informe
  `docs/informe-g2t-a-1007.md`, código `70a0c0d`. El candidato de G2T era
  inviable: tras x = 255 caben solo 12 − nb MOVE antes de retrasar la
  línea siguiente (P111). Codo del copper: 231 → 243 (P110).
- **Puerta A-T verde** en las tres trazas (3404 frames con Rex): 0 sin
  plazo, 0 sin variante, 0 errores de color, capa 1 y prioridad; Mario
  desde sus flujos = SNES en 5398 registros. 56 casos exactos y 27
  negativos detectados en WinUAE cycle-exact (`tools/g2t_cal.py` suites
  main/cap/final/knee). Presupuesto **estimado** +16 384 B chip.
- **L-OAM sigue roja** (41,2 % > 40 %; estrés peor que el control).
- Los enemigos todavía no se ven en la Amiga.

---

## 1. La próxima sesión: G2T-B (plan en C/68000) y revisión L-OAM

**Recomendación:** dos tarjetas en paralelo, worktree cada una. La fase C
de G2T (copper del juego, WinUAE) se ejecuta en la misma tarjeta solo si
B queda verde; su compuerta D1 se informa contra control pero no se
declara cerrada con L-OAM roja.

| tarjeta propuesta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **G2T-B/C: el plan del Rex en el juego** | GPT-6.1 Sol high | `player/g5plan.c` y `g5.s` nuevos, `game.s`/`scroll.s` bajo `SPR_G5`, `marioverify.c`, `mkscroll.py --g5`, herramientas nuevas | `docs/instrucciones-g2t-bc.md`: B2 envolventes de la foto = modelo, ≤ 3000 ciclos; B4/B5 plan PC = 68000 = `g2t_ref.py` byte a byte; C3 listas reales en regla; C4 0/57344 px en ≥ 12 frames; builds por defecto idénticos |
| **L-OAM: revisar margen y nueva tarjeta acotada** | GPT-6.1 Sol high | informes/perfiles, inicialmente lectura | `docs/instrucciones-revision-1007.md` §1: diagnóstico del 41,2 %/estrés y una propuesta acotada; conservar ≤ 40 % y estrés no peor que el control |

Preflight: entorno PC, lint, regress `--baseline tools/baseline_pc.json
--level`, OAM68K y la puerta A-T (`g2t_ref.py`) verdes; WinUAE
cycle-exact por candado, controles en la misma tanda, solo PIDs propios.
Cada commit pasa la red de seguridad; cierre según ROADMAP §7.

## 2. Después, en orden

1. G2T-C completa y L-OAM verde; cerrar G5a-bis como G2T.
2. G4+G6, luego G5+G9, con todos los enemigos del lote G3 (reuso de
   canales a mitad de pantalla con el protocolo G0 y la regla P111).
3. Estrés con G5 y S5 inmediatamente después; compuerta D1 sin rebajas.
   Revisar P110 en el scroll (5110 px con el paso medido).
4. C2/C4 para liberar tablas CPU de chip; segundo PF1 y G7.
5. Según dependencias: S8, P7/P9/P10, A0/A2, H2-H4 y T1.

## 3. Pendiente del usuario o de la PC

- Revisar el contrato fijado (`docs/instrucciones-g2t-a.md` §1-bis) si
  querés otra decisión; lo fijé con tu delegación y con las medidas.
- U1: jugar `work/live/game.adf` con teclado, KS 1.2, 512 KB chip + 512 KB
  slow. Enemigos aún no dibujados; diagnósticos si congela.
- U2: comparación de capa 2 contra la referencia (`cmp_ref.py`).
- U3 opcional: A500 real.
- No push hasta indicación explícita del usuario.
