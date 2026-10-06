# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.** Si otro
> documento dice otra cosa, manda este. Se **reescribe en el sitio** al
> cerrar cada sesión (regla de cierre: `ROADMAP.md` §7); lo que reemplaza
> se archiva en `docs/archivo/sesiones.md`. No se agregan secciones
> "próxima sesión" en ningún otro fichero.
>
> Estado de cada etapa: `ROADMAP.md` §1 · olas y sesiones: `ROADMAP.md` §4 ·
> tarjetas con su estado: `SUBAGENTES.md` §4 · índice de docs: `docs/README.md`.

**Escrito el 2026-10-06**, tras G2 sin subagentes. El contrato acotado
está auditado: **64528 B DMA, 72716 B tablas**, 2593 peticiones y Rex legal
sin diferencias. Copper con una imagen por forma/recargas por fila falla
con Mario en 12/43 formas; la ampliación G8b tampoco cabe automáticamente.
Evidencia: `docs/informe-g2.md`, contrato `docs/diseno-9.2.md`.
G3 y su loader siguen pendientes; los enemigos todavía no se ven en Amiga.
A1/G8b/D1 mantienen sus resultados y límites de la sesión anterior:
`docs/informe-a1.md`, `docs/validacion-g8b.md`, `docs/medida-d1-estres.md`.
G8b sigue opt-in (máximo 43,8 % PAL sin DMA); D1 aún no tiene traza WinUAE.

---

## 1. La próxima sesión: implementar G3 y medir el primer Rex

**Objetivo:** que el banco de gráficos de sprites y sus tablas entren en
memoria con reconstrucción exacta, ver el primer Rex en la Amiga y poder
medir la fluidez (compuerta D1) con los replays de estrés.

Modelos (`SUBAGENTES.md` §1): Opus → GPT-6.1 Sol high; Sonnet high →
GPT-6.1 Sol medium; Sonnet low → GPT-6 Luna medium. Astra queda fuera.

| tarjeta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **G3** — conversor y loader del banco acotado | Sol medium | `tools/mksprgfx.py`, `tools/sprgfx_final.py`, `player/` carga mínima | implementar el contrato G2: DMA inmutable solapado, catálogo enemigo deduplicado y directorio. Todas las 2593 peticiones y Rex legal, cero rechazos; tablas ≤98304 B. Formato versionado con bob ausente explícito; memmap real replay/vivo y pico del loader. `--final --scope g2-bounded` acepta solo el lote declarado; `--final` global no declara cubierto todo YI1 |
| **G5a** — prueba mínima de Rex, descartable | Sol high | rama propia; `player/` mínimo | G4 + G5 mínimos sobre el banco base de 48 poses ya verificado (10840 B chip), solo Rex, `-DSPR_OAM`. Rex visible en WinUAE comparado con la OAM del oráculo; MOVE del copper por línea junto a `build_mid` (P51), CPU y DMA medidos en cycle-exact. Los números validan G5/G6; medir también la lógica G8b (hoy máx. 43,8 % sin DMA) antes de activar la OAM ampliada. El código no es el G4/G5 definitivo |
| **D1-medida** — exportar y medir los replays de estrés | Sol medium (el coordinador fija la exportación; recuento ya disponible) | `tools/`, `docs/` | usar `ORACLE`/`REPLAY` de `game_build.sh` y `d1_count.py`; obtener una traza completa por VBL en WinUAE cycle-exact, con identidad de foto puesta y ticks terminados. `stress_back`: 4127 operaciones; `stress_sprites`: 1915. Medir omisiones, racha, ventana250, edad y p99; los agregados BENCH no bastan (`docs/medida-d1-estres.md`) |
| **A0** — registro del DSP | Sol medium | `tools/snesorc/orc.c`, `tools/dsplog.py` | escrituras DSP con frame/tick, notas por voz y efectos; oráculo idéntico con/sin registro. A1 ya da conversión exacta; A0 permite estudiar A2 y contrastar el audio (SUBAGENTES A0) |

**De la investigación** (`docs/investigacion-ports.md`, una línea por tarjeta):

- **D1-medida:** usar §17.2 como protocolo (A/B iguales salvo el cambio;
  fotos omitidas, racha, edad de la foto, ticks perdidos, p99 y máximo; no
  sumar máximos de frames distintos).
- **G2/G3:** E05 (§16.4): recortar márgenes transparentes conservando el
  origen OAM y comparar máscara repetida contra única; la fórmula de
  palabras por fila sirve para el presupuesto de Banzai.
- **G5a:** E02 (§16.5): medir sobre Rex poses compartidas contra cadena DMA
  copiada, con su coste en MOVE, para darle el número a G2. E01 (§16.1,
  perfilador de Bartman) solo como diagnóstico si un pico no se explica;
  las medidas que valen siguen siendo las de `a500.uae`.

G2 está cerrada como **diseño acotado**; G3 implementa su contrato.
`g2_bank_audit.py` emite evidencia SG2A descartable, no sustituye el
conversor/loader definitivo. Si G3 descubre un caso nuevo o un límite
incumplido, vuelve a G2 con evidencia. No ampliar el lote sin auditarlo.

### Decisión de color y DMA

La imagen única con recargas por fila falla con reservas reales de Mario;
se eligen variantes precalculadas con flujos **inmutables** compartidos.
G5 programa PT completo y POS/CTL por copper (G0); no parchea el banco ni
recodifica/copia imágenes por frame. Recargas por X siguen siendo una
alternativa pendiente de G5a/G6, no una medida ya realizada.

### Lote y puerta de G2/G3

G2 demuestra **64528 B chip + 72716 B tablas** para el lote. El diseño
anterior de 145600 B incluía fuentes bob de 15 índices que no completan
G7/PF1; G7 tiene presupuesto separado. Ampliar con las trazas G8b mide
77152 B DMA aun excluyendo Banzai y sin nuevas variantes Mario: no cabe.

**Lote de la puerta (acotado):** las variantes de las tres trazas actuales
(`yi1`, `normal`, `spin_kill`) con reservas reales de Mario y ocho paletas,
más las poses legales de Rex de `RexGfxRt`. **Fuera de este lote**:
Banzai, piraña, Chuck, meta, power-ups y partículas, y el remapeo de bobs
a PF1 (G7). G8b ya proporciona OAM de los cinco tipos, pero G3 no amplía
su lote automáticamente: G2 ya midió el crecimiento; antes de ampliar
la puerta se necesita otro presupuesto y auditoría (`docs/informe-g2.md`).

**Puerta de cierre:**

- **Chip:** banco ≤65536 B; `memmap` concreto con cero violaciones en
  replay y vivo con SPR_OAM. Proyección G2: 455232/466760 B chip. Auditar
  también el pico del loader y copias transitorias. PF1 doble/audio requieren C2/C4.
- **Slow:** tablas+índices ≤98304 B; trabajo G4/G6 ≤32768 B; fotos 2376 B.
  Vivo opt-in usa 251120 B; C2/C4 moverán 135472 B redondeados. Tope total
  nuevo 133448 B, margen 4248 B con el binario actual. Recalcular con
  crecimiento de código/loader; no usar el margen de replay para vivo.
- **Exactitud:** todas las variantes del lote sin rechazos ocultos, píxeles
  y colores exactos, PNG referencia/decodificación comparado, regresión
  PC/68000 en verde. `--final --scope g2-bounded` acepta el lote completo (no basta con las 48
  poses base ni con el subconjunto de 1724).
- **Coste:** si la representación agrega trabajo por frame, medirlo en
  WinUAE cycle-exact antes de cerrar.

### Antes de lanzar y al cerrar

- Antes: `python tools/lint_port.py` y `python tools/regress.py --level`
  en verde (cloud: `tools/baseline.json`; PC: agregar
  `--baseline tools/baseline_pc.json`); worktree por tarjeta (`sh tools/wt_new.sh <tarjeta>`); capturas con
  perfiles privados, máximo tres WinUAE a la vez, cada uno cierra solo su
  PID.
- Al cerrar: la regla de `ROADMAP.md` §7 (reescribir este fichero).

---

## 2. Después, en orden

Cada paso con su puerta; nada empieza con el anterior en rojo. Detalle de
cómo hacer cada cosa: `docs/plan-tecnico.md` §10; tarjetas: `SUBAGENTES.md`.

1. Terminar **G3** si la sesión de arriba no completa su puerta.
2. **G4 + G6** (asignador de columnas y `sprcop_verify.py`), con el
   contrato cerrado.
3. **G5 + G9**: `SPRxPOS`/`SPRxPT` y colores por línea en la misma lista que
   `build_mid`; comparación automática contra la OAM. **Los enemigos se ven
   en la Amiga.**
4. **Medida de estrés + S5, inmediatamente después de G5**: render completo
   (scroll + sprites) en la vuelta (s ≈ 2832 y 4580), el Banzai y el tramo
   con más Rex; después S5 (repartir el trabajo de `build_mid` entre frames)
   con esos números. Compuerta D1 en fotos omitidas (`ROADMAP.md` §2).
   Para S5: E09 (reasignar colores a índices con la misma imagen y menos
   MOVE) y E10 (precalcular solo las zonas caras, p. ej. los postes; todas
   las listas serían 792 KB y no caben), `docs/investigacion-ports.md` §17.1.
5. **C2/C4** (vlink + loader) para liberar las ~135 KB de tablas de CPU que
   hoy viven en chip; después el segundo PF1 y **G7** (bobs).
   Para G7: E03 (lotes del blitter), E04 (interior opaco del Banzai) y E06
   (restauración: la copia espejo del buffer circular no es fondo limpio;
   una foto O5 retenida no se toca), `docs/investigacion-ports.md` §16.2-16.4, §17.1.
6. En paralelo según dependencias: S8 (cámara vertical de YI1), lógica que
   falta (P7 bolas de fuego, P9 monedas, P10 reserva), A0/A2 (audio), H2-H4
   (HUD), T1 (zona de la tubería).
   Audio (A3-A7): E08 desde el primer driver (tick separado de la
   reactivación de Paula; auditar qué timer de CIA usa cada cosa, O1 ya usa
   uno), §16.6. HUD (H2): trucos de módulo para líneas constantes, §16.9.
   Lógica (L5): E07 (GCC) solo si un perfil muestra que la lógica limita, §16.7.

## 3. Pendiente del usuario o de la PC

- **U1:** jugar `work/live/game.adf` en WinUAE con teclado (KS 1.2,
  512 KB chip + 512 KB slow). Los enemigos todavía no se dibujan; si se
  congela, captura de la página 2 del diagnóstico y
  `python tools/diag_read.py --shot X.png --repro --bin work/live/game.bin`.
- **U2:** Etapa 7 (`cmp_ref.py` de la capa 2 contra la referencia).
- **U3**, opcional: probar en una A500 real.
