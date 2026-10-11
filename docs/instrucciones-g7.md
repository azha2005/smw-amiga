# G7 — bobs en PF1 (primero, los efectos de SW-S)

2026-10-10. **Decisión del usuario (2026-10-10): los puntos, el humo y los
trozos de SW-S se dibujan como bobs (G7), no por G5L.** No compiten con
los enemigos por los sprites de hardware. Hasta que G7 funcione, no se
ven. **Grande**: es la cola de bobs del plan (`plan-tecnico.md` §10.6,
`diseno-9.2.md` §4-5, tarjeta G7 de `SUBAGENTES.md`), y los efectos son
su primer cliente porque son los más chicos (8×8 y 16×16, < 1 s). El
Banzai Bill (64×64) y los desbordes de G5L vienen después, con la misma
infraestructura.

## Lo que ya está

- La lógica y la OAM de los efectos, exactas contra la SNES
  (`docs/informe-sw-s-1010.md`, `sh tools/sws_gate.sh`). Cada frame
  lógico deja en `ram[$0200-$02FF]` (ExOamSlot) las fichas a dibujar:

  | efecto | entradas | tamaño | paleta (atributo) |
  |---|---|---|---|
  | puntos | `$B0 + 8x`, 2 por ranura (x 0-5) | 8×8 | `$30 \| 8` (4) o `The2Up3UpAttr` |
  | nube (humo 1) | `$20 + 4x` | 16×16 | `SpriteProp` |
  | estrella de contacto (humo 2) | `$F0-$FF`, 4 fichas | 8×8 | `SpriteProp` + bit `$40` |
  | derrape (humo 3) | `$20 + 4x` | 8×8 | `SpriteProp` |
  | trozos / destellos (menores) | `$50 + 4x` (x 0-11) | 8×8 | `SpriteProp` (+`$06` el destello) |

  `y = $F0` es "vacía". `ram[$0420 + entrada]` lleva el tamaño (bit 1) y
  el bit alto de x (bit 0).
- O5 (render desacoplado) con tres buffers de foto; el render es el único
  dueño del blitter (`diseno-9.2.md` §4).

## El problema de memoria (medido el 2026-10-10, `bm1_memmap.py`)

El diseño elige **doble buffer de PF1** (+59 136 B de chip) para no tocar la
imagen publicada cuando O5 repite un frame. En el vivo por defecto (BM1):

| | ocupado | margen |
|---|---:|---:|
| chip | 482 232 B | **42 056 B** |
| slow | 516 512 B | **7 776 B** |

El segundo PF1 no entra: faltan ≥ 17 080 B de chip, más las fuentes y
máscaras de los bobs y las listas de regiones sucias. En chip hay
94 904 B que solo lee la CPU (`CHG` 31 208, `MLD` 52 168, `MAP`, `INI`,
`L2P`, `MLX`), pero la slow está llena: el binario fijo ocupa 407 820 B.

## Pasos

1. **G7-0, memoria.** Conseguir ≥ 59 136 B + fuentes de chip libre en el
   vivo, sin bajar la fidelidad. Medir antes de elegir; candidatos:
   - mover a slow tablas solo de CPU (`CHG`, `MLD`…) haciendo lugar en la
     slow: qué ocupa los 407 820 B del binario (listado
     `work/rg_bm1/game.lst`; replay y fotos de diagnóstico no van en el
     vivo), y si algo se puede comprimir (C3);
   - el modo diagnóstico (11 528 B de chip) fuera del ADF que se
     distribuye, o sus pantallas en el PF1 libre;
   - las tres listas del copper (3 × 57 756 B): ver si la tercera (el
     colchón, aceptado por el usuario el 2026-10-09) puede compartir algo.
   Puerta: `bm1_memmap.py` con el segundo PF1 reservado y 0 violaciones;
   la regresión sin cambios de fidelidad. **Si ninguna opción alcanza sin
   tocar algo visible, consultar al usuario antes de seguir.**
2. **G7-1, doble PF1 sin bobs.** Las dos copias del anillo de PF1 (columnas
   nuevas y cambios de mapa escritos en las dos, o por buffer con su lista
   pendiente); cada lista del copper apunta al PF1 de su foto. Puerta:
   capturas del replay idénticas a las de hoy (la barrida SW1, `tools/sweep_cmp.py`, `docs/informe-sw1-1010.md`)
   y el A/B BENCH (el coste de duplicar las columnas).
3. **G7-2, fuentes y color.** Convertir las fichas de los efectos (GFX de
   sprites: puntos `$29-$5E` y `$83` (`PointTile1/2`), humo `$60-$66`, estrella `$7C/$7D`,
   trozos `$3C/$3D`, destellos `$5C/$66/$6C-$6E`) a fuentes de bob con
   máscara, en chip, con el banco G3 como referencia (`mksprgfx.py`).
   PF1 tiene **7 índices opacos compartidos con el terreno**: resolver los
   colores de cada efecto contra el plan del copper de su línea
   (`d8demote.py`). Si un color no tiene lugar exacto, mostrar el caso al
   usuario: una aproximación no está autorizada (`diseno-9.2.md` §4).
4. **G7-3, la cola de bobs.** En el render de cada foto, sobre el PF1 libre:
   restaurar desde `BLK`/mapa las regiones sucias del último uso de ese
   buffer, aplicar columnas y cambios de mapa, dibujar los bobs de la foto
   (leídos de la OAM de la foto: hay que copiar `ram[$0200-$02FF]` y
   `$0420-$045F` a la foto de O5) y publicar después del último blit.
   Cola por interrupción (P31: ~42 µs de CPU por blit). Recorte en los
   bordes y en el cruce del anillo. Prioridad: los efectos van delante
   del terreno de PF1 (en la SNES, prioridad de OAM `$30` = encima de
   todo) y detrás de los sprites de hardware.
5. **G7-4, los efectos.** Activar los tres motores en la cola. Puertas:
   - capturas de SW1 en las fotos de la lista de SW-S (k 199, 1199, 1349,
     1399, 1549, 1799, 2199, 2749, 2899, 3149, 3449, 4699 y 6049-6299),
     exactas en las cajas de los efectos;
   - A/B BENCH de D1 (control `-DNOSWS`, que tiene que apagar también la
     cola de efectos);
   - `bm1_memmap.py`, regresión, lint, `sws_gate.sh`, `oam68k_gate.sh`.
6. **Después (otra tarjeta):** el Banzai Bill y los desbordes de G5L por la
   misma cola.

## Trampas

- P2, P31: el blitter roba ciclos a la CPU y cada blit cuesta ~42 µs de
  CPU además de los datos.
- P97, P115: O5 y el colchón; una foto que se repite no se toca.
- P123: `columns` destruye a2.
- P126: el replay con Exec no entra en chip; BENCH con `tools/bm_build.sh`.
- P128: fila Amiga = fila SNES − 1 al comparar capturas.
