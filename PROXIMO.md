# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.**
> Se reescribe al cerrar cada sesión (`ROADMAP.md` §7); el texto anterior
> está en `docs/archivo/sesiones.md`. Estados: `ROADMAP.md` §1/§4 y
> `SUBAGENTES.md` §4. Ejecución: `docs/instrucciones-olas.md`.

**Escrito el 2026-10-07**, al cerrar L-OAM asm / G5a-bis fase A.
Revisión independiente: `docs/informe-coordinacion-1007.md`.

- **L-OAM mejora parcial integrada**, `e8ec165` + `bbdf201` + `cd5001c`,
  fusión `cb8ba8f`. `finish_oam_write` y `rex_gfx` en asm para la Amiga,
  C como referencia del PC. RAM PC=68000: 6549 llamadas, 0 distintas.
  Frame 3097 Musashi: 77756 -> 72900 ciclos. Default idéntico.
  **Puerta todavía roja** en WinUAE cycle-exact, tanda l4:

  | replay | sin OAM: fotos / racha | con OAM: fotos / racha | level_frame con OAM |
  |---|---|---|---|
  | stress_back | 145 (3,51 %) / 3 | 295 (7,15 %) / 6 | 73,9 % |
  | stress_sprites | 0 / 0 | 32 (1,67 %) / 2 | 70,7 % |
  | yi1 entero | 14 (0,22 %) / 1 | 27 (0,43 %) / 1 | 41,2 % |

  Se cumplió la parada de `docs/instrucciones-loam.md` §5 tras ambas
  rutinas en asm. No seguir optimizando funciones a ciegas.
  Informe: `docs/informe-loam-1007.md`; segunda tanda independiente
  coord4 y sus números: `docs/informe-coordinacion-1007.md`.
- **G5a-bis detenida en la fase A**, WIP `8fe712d`, rama
  `wt/g5bis-1007` (`../wt-g5bis-1007`). Herramientas/tests en esa rama;
  informe en `docs/informe-g5bis-1007.md`. A2=0 diferencias y
  sin_variante=0 en las tres trazas, pero **59318 ventanas de color
  vacías**, 18 fallos de capacidad. Primer testigo yi1 f5811: COLOR17
  negro en y168 y blanco en y169, ventana `[169,168]`. El coordinador
  reprodujo el resumen idéntico y miró las 12 imágenes.
  **B/C no iniciadas**, por la parada de
  `docs/instrucciones-g5a-bis.md` §3. Escribir CPU asm no resuelve
  ventanas vacías del copper.
- G3 permanece acotada e inmutable: 64528 B DMA / 72724 B tablas;
  banco replay/vivo con último código: chip 455728/467256 B, slow
  287712/323944 B (`memmap.py`, 0 violaciones). No dibuja enemigos.

---

## 1. La próxima sesión: revisar los dos bloqueos antes de implementar

**Recomendación del coordinador; las nuevas tarjetas necesitan fijar sus
instrucciones antes de ejecutar.** Las dos tarjetas originales llegaron
a su condición explícita de parada. No se declara cerrada ninguna ni se
habilitan las fases u olas dependientes con estas puertas en rojo.

| revisión propuesta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **L-OAM: revisar el margen restante y fijar nueva tarjeta** | GPT-6.1 Sol high | informes y perfiles, inicialmente lectura | `docs/instrucciones-revision-1007.md` §1: explicar 41,2 % YI1 y exceso en estrés; propuesta acotada con presupuesto y verificador RAM. Umbrales conservados; no ampliar funciones sin nueva instrucción |
| **G2T: contrato temporal de variantes y recargas** | GPT-6.1 Sol high | modelo offline en rama propia, sobre G5a-bis | `docs/instrucciones-revision-1007.md` §2: determinar si variantes con plazos viables o ventanas horizontales permiten color exacto. Propuesta con testigos, slots reales y presupuesto; nuevo contrato decidido antes de B/C |

Para G2T, empezar por el testigo f5811 y separar compatibilidad por fila
de viabilidad temporal. La regla vigente elige la primera variante
compatible; **no cambiarla para esconder la puerta roja**. Evaluar
alternativas explícitamente, con capacidad real después de `build_mid`,
reservas de Mario en X/Y y flujos DMA inmutables (P108). Aumentar MOVE
por línea no soluciona una ventana vacía. Cualquier cambio del contrato
se documenta y se vuelve a comprobar en las tres trazas completas.

Antes de lanzar: entorno de `docs/reglas-ola-pc.md`, lint,
`regress.py --baseline tools/baseline_pc.json --level` y
`sh tools/oam68k_gate.sh` verdes; worktree por tarjeta. WinUAE siempre
por el candado, controles en la misma tanda y solo PIDs propios.
Coordinador repite puertas y mira imágenes (`instrucciones-olas.md` §1.3).
Al cerrar: `ROADMAP.md` §7; nada sin commitear.

---

## 2. Después, en orden

Dependencias originales conservadas; no avanzar mientras sus puertas
anteriores estén rojas (`docs/instrucciones-olas.md`, `SUBAGENTES.md`).

1. Cerrar L-OAM y G5a-bis con instrucciones de revisión resueltas.
2. G4 + G6, luego G5 + G9, con todos los enemigos del lote G3.
3. Medida de estrés con G5 y S5 inmediatamente después (picos de
   `build_mid`, compuerta D1 en fotos omitidas).
4. C2/C4 para liberar tablas CPU de chip; segundo PF1 y G7.
5. Según dependencias: S8, P7/P9/P10, A0/A2, H2-H4 y T1.

## 3. Pendiente del usuario o de la PC

- Fijar las nuevas instrucciones de revisión tras las dos paradas.
  Recomendación: contrato temporal G2T y revisión acotada del coste OAM,
  con Sol high; mantener fidelidad, 50 Hz y umbrales actuales.
- U1: jugar `work/live/game.adf` con teclado, KS1.2, 512 KB chip +
  512 KB slow. Los enemigos aún no se dibujan; diagnóstico si congela.
- U2: comparación de capa 2 contra la referencia (`cmp_ref.py`).
- U3 opcional: A500 real.
- No push hasta indicación explícita del usuario.
