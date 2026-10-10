# L-DER — la deriva de la lógica de sprites contra la SNES

2026-10-10. Sigue a G9. Misma rama y worktree, sin merge ni push.

## Por qué

G9 (`informe-g9-1010.md` §3) midió que el **dibujo** de los sprites es
exacto. Lo que no lo es, en algunas instancias, es la **lógica**: unos
pocos objetos del port se separan de la SNES y quedan corridos 1-2 px, o
con otra pose, durante cientos de fotos. Con el criterio 1:1 eso es una
diferencia visible.

| replay | objeto (ranura) | fotos | primer frame del oráculo | forma |
|---|---|---|---:|---|
| yi1 | Rex (6) | 2778-3132 | 7923 | x −2 fija |
| yi1 | Rex (7) | 2456-2888 | 7601 | x −1 / otra pose |
| stress_piranha | piraña (5) | 1353-1505, 1570-1814 | — | y ±1 / otra pose |
| stress_piranha | Rex (6) | 1353-1694 | — | x +1 / otra pose |
| chuck | Chuck (4) y cinta (3) | 2840-2882 | — | otra pose / y −1 |
| todos | Koopa (7) | primeras fotos | — | y −1 |

## Pasos

1. **Reproducir.**
   `python tools/sprshot_cmp.py --logic --bin <build>/game.bin --lst
   <build>/game.lst --trace <replay>` sobre los builds de
   `work/g4b/all*` (o rearmarlos: `G5L_TYPES=all`, `-DREPLAY -DG5L
   -DCUSHION`). `work/g9/logica_<replay>.json` trae `casos` (foto, frame,
   tipo, ranura, motivo, OAM del port) y las fotos fuera de sincronía.
2. **El primer frame distinto, en la RAM y no en la OAM.** Para cada
   tramo:
   - comparar la RAM de la ranura del port (x/y con subpíxel `$14F8`/
     `$14EC`, velocidades `$B6`/`$AA`, estado `$14C8`, `$C2`, temporizadores,
     contacto con bloques `$1588`) contra la RAM que guarda el despacho de
     la traza `oamb` (el campo `ram` de `g5ref.read_trace`, en el momento
     del despacho);
   - desde unos frames antes del primer caso;
   - **ojo con el momento**: la traza guarda la RAM al despachar el
     sprite, y el port la captura al final del frame (P127).
3. **Clasificar la causa:**
   - un campo que el port no transcribe;
   - el orden de los slots;
   - una interacción con Mario o con bloques (P34);
   - el arranque del tramo (los sprites que ya están al empezar un tramo
     los crea la carga del nivel, P65);
   - o el replay mismo (`SKIP`/`SYNC`).

   Las deltas fijas (x −2 durante 355 fotos) apuntan a una sola diferencia
   que no se corrige después.
4. **Corregir en el 68000** (directiva: todo en asm; el C es solo
   referencia), con el oráculo de la tarjeta del sprite (P1-P6) como
   prueba. Si la causa es el replay, documentarla y excluirla en
   `--logic`.
5. **Puertas:**
   - `--logic` con ≥ 99 % por tipo en yi1, stress_piranha, chuck y hills2
     (o cada tramo restante explicado);
   - regresión completa;
   - `g5l.py game` exacto;
   - si cambia el 68000 de la lógica, también `dc_loop_verify.py` y el
     A/B BENCH, porque la lógica comparte la CPU con D1.
6. Informe y cierre según ROADMAP §7.

## Trampas

- **P35**: los gráficos de Mario se calculan antes que su física.
- **P34**: golpear un bloque cambia el mapa en la fase de sprites.
- **P65**: el arranque de los tramos.
- **P66**: congelamientos que pone un sprite.
- **P68, P75**: el oráculo y el mando; `STOPF`.
- **P127**: la x/y de la ranura es posterior al movimiento, y la familia
  de mapas no es el tipo.
