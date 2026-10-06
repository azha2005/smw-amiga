# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.** Si otro
> documento dice otra cosa, manda este. Se **reescribe en el sitio** al
> cerrar cada sesión (regla de cierre: `ROADMAP.md` §7); lo que reemplaza
> se archiva en `docs/archivo/sesiones.md`. No se agregan secciones
> "próxima sesión" en ningún otro fichero.
>
> Estado de cada etapa: `ROADMAP.md` §1 · olas y sesiones: `ROADMAP.md` §4 ·
> tarjetas con su estado: `SUBAGENTES.md` §4 · índice de docs: `docs/README.md`.

**Escrito el 2026-10-05**, al cerrar la sesión de reorganización de docs
(base `master`). Última sesión de trabajo: G3, Z1 y H1 (resumen en
`docs/archivo/sesiones.md`).

---

## 1. La próxima sesión: banco de sprites (G2/G3) y primer enemigo visible

**Objetivo:** que el banco de gráficos de sprites y sus tablas entren en
memoria con reconstrucción exacta, ver el primer Rex en la Amiga y poder
medir la fluidez (compuerta D1) con los replays de estrés.

Modelos (`SUBAGENTES.md` §1): Opus → GPT-6.1 Sol high; Sonnet high →
GPT-6.1 Sol medium; Sonnet low → GPT-6 Luna medium. Astra queda fuera.

| tarjeta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **G2** — revisar la representación del banco (la escribe el coordinador) | Sol high | `docs/diseno-9.2.md` | contrato con tamaños medidos, tope de slow en bytes y casos exactos que demuestren la reducción. **Evaluar primero el remapeo de color por copper** (nota abajo) |
| **G5a** — prueba mínima de Rex, descartable | Sol high | rama propia; `player/` mínimo | G4 + G5 mínimos sobre el banco base de 48 poses ya verificado (10840 B chip), solo Rex, `-DSPR_OAM`. Rex visible en WinUAE comparado con la OAM del oráculo; MOVE del copper por línea junto a `build_mid` (P51), CPU y DMA medidos en cycle-exact. Los números alimentan G2; el código no es el G4/G5 definitivo |
| **D1-medida** — fluidez con los replays de estrés | Sol medium (el coordinador fija el método; el recuento puede bajar a Luna medium) | `tools/game_build.sh` (variable de replay), `docs/` | replays de `oracle_stress_back` (vuelta de x `$1240` a `$0500`) y `oracle_stress_sprites` (Banzai + 3 Rex) armados como el de `oracle_yi1` (`m68kverify --oracle`); fotos omitidas, racha máxima y peor ventana de 250 frames en WinUAE cycle-exact. Es la primera medida de la compuerta D1 (`ROADMAP.md` §2) en estrés |
| **G8b** — OAM de Banzai `$9F`, piraña `$4F`, Chuck `$95`, meta `$7B`, caparazones | Sol medium | `player/spr_*.c` y `spr_gfx.c` de esos sprites | sus rutinas de gráficos escriben la OAM atribuida como G8 hizo con Rex: `oam_XX` exactas en `regress.py` contra `oracle_chuck`, `goal`, `shells`, `banzai`, `stress_piranha`. La lógica ya está; esto amplía la cobertura que G3 dejó fuera |
| **A1** — `tools/brr2pcm.py` | Sol medium | solo `tools/` | muestras BRR → PCM de 8 bits con signo (P7), ida y vuelta contra el decodificador de referencia; tamaño total frente a los 64 KB de D5 |

G2 y G3 van **en serie**: G3 (Sol medium, `tools/mksprgfx.py`) implementa
el contrato de G2 después de que el coordinador lo revise; si G3 encuentra
una decisión sin resolver, vuelve a G2 con evidencia. Si G2 cierra temprano,
G3 entra en esta misma sesión.

### Nota para G2: el remapeo por copper

La explosión de variantes (pose × reservas de Mario por fila × ocho
paletas) viene de hornear el color en el bitmap. D8 ya recarga los colores
17-31 por línea; si el remapeo pasa a esa recarga, cada pose se guarda
**una vez**. Medir esa opción (bytes de banco y tablas, MOVE extra por línea
con los datos de G5a) antes de optimizar la deduplicación actual. Si se
descarta, dejar en el contrato el número que la descarta.

### Lote y puerta de G2/G3

Hoy: 2593 variantes necesitan 145600 B de chip con la estrategia ensayada
(banco: 65536 B); el subconjunto emitido (1724) ocupa 693884 B de tablas
en slow. No son cotas mínimas. Casos y reproducción: `docs/informe-g3.md`.

**Lote de la puerta (acotado):** las variantes de las tres trazas actuales
(`yi1`, `normal`, `spin_kill`) con reservas reales de Mario y ocho paletas,
más las poses legales de Rex de `RexGfxRt`. **Fuera**: Banzai, piraña,
Chuck, meta, power-ups y partículas (esperan G8b) y el remapeo de bobs a
PF1 (G7). G2 diseña con margen para esa cobertura: estima cuánto crecen
banco y tablas al sumarla.

**Puerta de cierre:**

- **Chip:** banco ≤ 65536 B; `memmap` con cero violaciones sobre el juego
  actual + banco (≈ 456 KB), en replay **y en vivo**. Segundo PF1 y audio no
  cuentan aquí: necesitan C2/C4 (`docs/diseno-9.2.md` §5).
- **Slow:** las tablas entran en lo que queda después de C2/C4: 524288 −
  207296 (uso actual) − 135468 (tablas de CPU que C2/C4 mueven a slow) =
  **181524 B**, menos lo que sume el modo en vivo. G2 fija el tope concreto.
- **Exactitud:** todas las variantes del lote sin rechazos ocultos, píxeles
  y colores exactos, PNG referencia/decodificación comparado, regresión
  PC/68000 en verde. `--final` acepta el lote completo (no basta con las 48
  poses base ni con el subconjunto de 1724).
- **Coste:** si la representación agrega trabajo por frame, medirlo en
  WinUAE cycle-exact antes de cerrar.

### Antes de lanzar y al cerrar

- Antes: `python tools/lint_port.py` y
  `python tools/regress.py --baseline tools/baseline_pc.json --level` en
  verde; worktree por tarjeta (`sh tools/wt_new.sh <tarjeta>`); capturas con
  perfiles privados, máximo tres WinUAE a la vez, cada uno cierra solo su
  PID.
- Al cerrar: la regla de `ROADMAP.md` §7 (reescribir este fichero).

---

## 2. Después, en orden

Cada paso con su puerta; nada empieza con el anterior en rojo. Detalle de
cómo hacer cada cosa: `docs/plan-tecnico.md` §10; tarjetas: `SUBAGENTES.md`.

1. **G3** sobre el contrato de G2 (si no entró en la sesión de arriba).
2. **G4 + G6** (asignador de columnas y `sprcop_verify.py`), con el
   contrato cerrado.
3. **G5 + G9**: `SPRxPOS`/`SPRxPT` y colores por línea en la misma lista que
   `build_mid`; comparación automática contra la OAM. **Los enemigos se ven
   en la Amiga.**
4. **Medida de estrés + S5, inmediatamente después de G5**: render completo
   (scroll + sprites) en la vuelta (s ≈ 2832 y 4580), el Banzai y el tramo
   con más Rex; después S5 (repartir el trabajo de `build_mid` entre frames)
   con esos números. Compuerta D1 en fotos omitidas (`ROADMAP.md` §2).
5. **C2/C4** (vlink + loader) para liberar las ~135 KB de tablas de CPU que
   hoy viven en chip; después el segundo PF1 y **G7** (bobs).
6. En paralelo según dependencias: S8 (cámara vertical de YI1), lógica que
   falta (P7 bolas de fuego, P9 monedas, P10 reserva), A0/A2 (audio), H2-H4
   (HUD), T1 (zona de la tubería).

## 3. Pendiente del usuario o de la PC

- **U1:** jugar `work/live/game.adf` en WinUAE con teclado (KS 1.2,
  512 KB chip + 512 KB slow). Los enemigos todavía no se dibujan; si se
  congela, captura de la página 2 del diagnóstico y
  `python tools/diag_read.py --shot X.png --repro --bin work/live/game.bin`.
- **U2:** Etapa 7 (`cmp_ref.py` de la capa 2 contra la referencia).
- **U3**, opcional: probar en una A500 real.
