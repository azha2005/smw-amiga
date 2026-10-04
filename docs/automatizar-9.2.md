# Cómo automatizar 9.2 (dibujar los sprites del nivel), y lo que viene después

> 2026-10-03. Plan, no implementado. Se apoya en `docs/investigacion-ports.md`
> (§5, §12.5, §14), en las tarjetas G0-G7 de `SUBAGENTES.md` y en D8
> (`AGENTS.md` §9: los enemigos van en sprites de hardware con colores
> recargados por línea; bob en PF1 solo si pasan de 4 columnas).

## 0. La idea: la SNES ya resolvió "qué dibujar"; nosotros solo traducimos la OAM

Hoy cada `player/spr_*.c` corre la lógica de la SNES, pero de la rutina de
gráficos (`RexGfxRt`, `GenericSprGfxRt*`, `SubSprGfx*`) solo corre
`get_draw_info` (posición en pantalla y flags). **No se escribe la OAM.**

Si en vez de eso portamos las rutinas de gráficos **enteras**, de modo que
escriban la OAM ($0200-$03FF y $0420) como en la SNES, el problema se
parte en dos piezas que no saben nada de enemigos:

```
lógica de la SNES (C, verificada) ──► OAM (128 fichas 8×8/16×16, x, y, tile, paleta, flip)
                                         │
             UN dibujador genérico ◄─────┘   OAM → sprites de hardware + copper (+ bob)
```

Ventajas:

- **Un sprite nuevo no necesita código de dibujo.** Solo su rutina de
  gráficos portada, que además se verifica sola (punto 2).
- **La verificación es exacta y automática.** snesorc graba la OAM real
  (`work/oam_*.txt`, `tools/oamrec.py`), así que se compara byte a byte,
  igual que la lógica contra el oráculo, sin mirar capturas.
- Muchas rutinas de gráficos son compartidas (a `SubSprGfx2Entry1` se salta
  desde 35 sitios de `sprite_1-*.s`; `GenericSprGfxRt0`, `SubSprGfx0Entry0`,
  `SubSprGfx1`). Pocas rutinas cubren muchos sprites.

Coste: la OAM son ~544 B de RAM más las escrituras; hay que medirlo con
`gamecheck.py --engine musashi` (`level_frame`) y compararlo con el ≤ 8 %
de CPU del dibujo (G2).

## 1. Las piezas y cómo se automatiza cada una

| # | pieza | herramienta | cómo se verifica sin mirar | tarjeta |
|---|---|---|---|---|
| 1 | Rutinas de gráficos → C que escribe OAM | a mano al principio; **`tools/x65c.py`** (transcriptor 65816 → C del estilo de `spr_*.c`, ya propuesto) para las demás | `marioverify` compara la OAM con la de la grabación de snesorc, frame a frame (nuevo campo en el oráculo, P85/P86) | G-OAM (nueva) + X1 |
| 2 | Gráficos: GFX de la ROM → frames de sprite adosados + máscara de bob | **`tools/mksprgfx.py`**, igual que `mkmario.py` | `--selftest` de ida y vuelta: decodificar lo convertido y comparar contra la ficha SNES de la OAM, en **todas** las poses que aparecen en las grabaciones | G3 |
| 3 | Colores: paleta SNES de cada ficha → colores 17-31 recargados por línea | `tools/sprpal.py` (ya existe: qué colores usa de verdad cada paleta de sprite en YI1; falta la salida por línea) | contar colores por línea contra el presupuesto de D9 | G2 |
| 4 | Asignador: fichas de la OAM → canales de sprite por franja de líneas | referencia en Python: **`tools/copsim.py`** (ya existe); el del 68000 en C y luego asm | **`tools/sprcop_verify.py`**: el asignador en Musashi sobre cada frame de todas las grabaciones contra `copsim.py`. Puerta: 0 fichas sin mostrar (o las que `copsim` también descarta) | G0, G4, G6 |
| 5 | Copper: `SPRxPT`/`SPRxPOS`/colores en la lista de `build_mid` | a mano (P39, P42, P46, P59) | `copverify`/`hdrcheck` extendido: la lista simulada pone cada canal en la línea y la X pedidas | G5 |
| 6 | Imagen final | `shot.ps1` + **comparador automático**: render de la OAM de la SNES con los gráficos convertidos (Python) contra la captura de WinUAE en el mismo frame del replay | píxeles distintos = 0 en las zonas de sprite (P57: muestrear el centro del píxel) | G6b (nueva) |
| 7 | Bobs (Banzai Bill, desborde de columnas) | a mano | lo mismo que 6, en los frames del Banzai | G7 |

Reglas sacadas de la investigación que el asignador (4) aplica de entrada,
sin redescubrirlas:

- un canal se reutiliza más abajo solo con **≥ 17 líneas** entre el final
  de un sprite y el inicio del siguiente (amiga-game-kit; regla de las
  palabras de control);
- recargar `SPRxPT` por copper en el blanco horizontal (`$D8`, unos 8 MOVE
  seguros, 15 no) cuando encadenar por DMA no alcanza (§12.5; G0 decide
  con números en las líneas más cargadas);
- ordenar por Y con **inserción continua** (la lista casi no cambia entre
  frames: orden de Ocean, multiplexores del C64);
- cuando no hay canal: **parpadear** (alternar entre frames, Silkworm) antes
  que desaparecer; y si una franja pide más de 4 columnas, el objeto pasa a
  bob (D8);
- los punteros se escriben una vez por lista y la paleta solo si cambió
  (como `mario_draw` desde 00c63f8).

## 2. Encaje con O5 (red de seguridad, decidido el 2026-10-03)

O5 separa la lógica (50 Hz fija) del render. El render toma una **foto
coherente `(cámara, OAM)` del mismo frame lógico** (P35) y la publica con el
cambio de `COP1LC`. Con el dibujador genérico, esa foto es exactamente
"la OAM + la cámara": **conviene hacer O5 primero**, así 9.2 nace sobre la
foto y no hay que adaptarlo después.

## 3. Orden propuesto

1. **O5** (prototipo; decidido): foto `(cámara, OAM)` + render desacoplado;
   contar frames de imagen perdidos en el replay y en los `stress_*`.
2. **G1 + G0** (solo herramientas): estudios con 256 px y medir encadenar
   contra recargar.
3. **G-OAM** sobre Rex (18 en el nivel) y `SubSprGfx2Entry1`, con el campo
   OAM en el verificador. Con eso: Rex, Koopa, caparazones y la mayoría
   de lo que usa la rutina compartida.
4. **G3** `mksprgfx.py` (GFX 20 y los demás), en paralelo con 3.
5. **G4 + G6** asignador + `sprcop_verify.py`.
6. **G5** copper, **G6b** comparación de imagen, **G7** bobs del Banzai.

Los pasos 2-5 son casi todos de herramientas con puerta automática: se
pueden repartir entre subagentes (`SUBAGENTES.md`) sin que nadie mire
capturas hasta el 6.

## 4. A futuro (más allá de YI1, `docs/mas-alla-yi1.md`)

Todo lo anterior no tiene nada de YI1 salvo los datos:

- **Otro nivel u otro enemigo** = portar su lógica y su rutina de gráficos
  (con `x65c.py`, verificadas contra una grabación nueva de snesorc) y pasar
  su GFX por `mksprgfx.py`. El dibujador, el asignador, el copper y los
  verificadores no cambian.
- **Estudio previo automático por nivel:** con la grabación de snesorc del
  nivel nuevo, `oamstudy.py` + `copsim.py` dicen antes de escribir código
  cuántas líneas piden más canales, qué objetos van a bob y cuántos
  parpadean. Es el "cabe o no cabe" de cada nivel en minutos.
- **Regresión:** `regress.py` suma la comparación de OAM (por sprite) y
  `sprcop_verify.py` por grabación; `coverage.py` muestra qué rutinas de
  gráficos ninguna grabación recorre (lo mismo que hizo V2 con la lógica).
- **Presupuesto:** `gamecheck.py` ya cuenta los frames que pasan con DMA
  (líneas `O4`). Con el dibujo sumado, la misma métrica dice si un nivel
  nuevo depende de la red de seguridad de O5 y cuánto.
