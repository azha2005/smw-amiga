# G4-B — los demás enemigos de YI1 por G5L

2026-10-10. Sigue a G4-2o. Misma rama y worktree, sin merge ni push.

## Por qué

Hoy la Amiga dibuja solo a Mario y al Rex. Los demás enemigos de YI1 que
la lógica ya mueve (P1-P6) **no se ven**:

- la piraña saltarina (`$4F`);
- el Chuck (`$95`);
- el Koopa sin caparazón (`$BD`) y el caparazón (`$05`);
- la caja de mensaje (`$B9`);
- la cinta de meta (`$7B`);
- y `$02`.

Es la diferencia visible más grande que queda. G4-A midió que **todos
entran en un par acoplado** (≤ 15 colores, ≤ 2 columnas; tabla en
`informe-g4a-1010.md` §2). La excepción es el Banzai (`$9F`, 64×64, 4
columnas), que es bob (G7) y queda fuera.

## Objetivo

G5L dibuja **un objeto por foto de cualquiera de esos tipos**, con la
misma regla que el Rex de hoy: el primero por (fila, ranura) que tenga
forma, variante y plazo, en los pares 4-5/6-7. El Rex sigue igual. Con
`-DG5L_MAXPL=2`, el camino de varios ya admite tipos mezclados.

## Pasos

1. **Las formas.**
   - `g4a.py traceall` da las formas de los 9 tipos en las 30 grabaciones
     (`work/g4a/shapes.json`).
   - Llevar el banco/tabla (`g5l.build_table`, tabla `G5L2` → `G5L3`) a
     esos tipos. La clave es (tipo, fichas normalizadas, prioridad), y los
     colores salen de la paleta OAM de cada tipo.
   - Formato según G4-A §6: 4 mapas para el Rex y 1 para el resto, con
     las máscaras compartidas.
   - **Puertas:**
     - el autotest de píxeles de las variantes limpias;
     - memmap sin violaciones en el replay y en el vivo, con el margen de
       chip anotado (G4-A estimó ≈ 17 KB de DMA para los demás con 1
       mapa).
   - Medir antes de elegir si no entra.
2. **La referencia (Python, como G4-1).** `trace_photo`/`plan_frame` con
   candidatos de todos los tipos.
   - Las trazas: las de siempre más las que tienen esos enemigos (los
     oráculos `chuck`, `goal`, `shells`, `stress_piranha`).
   - **Puerta:** `trace` y `trace --multi` con 0 errores de color, y cada
     objeto visible dibujado o en la cola de bobs con su motivo.
   - Contar por tipo cuántos se dibujan y cuántos no.
3. **La captura** (`g5l_capture`). Hoy filtra `wm_SpriteNum == $AB`. Hay
   que copiar los tipos de la tabla con su número, y el registro de la
   foto lleva el tipo. Mirar el tamaño de `R_G5L` en slow (`G5L_MAXREX`).
4. **68000.**
   - `g5l_choose` busca por (tipo, clave).
   - El resto del camino no conoce el tipo: es una variante como otra.
   - Verificar el ABI y la P123 (registros de `dc_loop`).
5. **Puertas:**
   - `g5l.py game` exacto en yi1, hills2 y los replays con esos enemigos;
   - regresión completa y `dc_loop_verify.py`;
   - **A/B BENCH WinUAE**: normal/back/sprites/hills2 y uno con la piraña.
     Las fotos que hoy no tienen Rex pasan a dibujar otro enemigo, así que
     se espera más CPU: medirlo y reportarlo como trade. **No se activa
     por defecto si D1 empeora más que el ruido sin que el usuario lo
     vea**; hasta entonces va con un `-D`;
   - captura WinUAE de una foto con la piraña y otra con el Chuck, con 0
     píxeles distintos contra lo esperado (`g5l.py shot --only`).
6. Informe y cierre según ROADMAP §7.

## Trampas

- P99/P100 (gráficos de sprites y columnas);
- P108 (el banco es inmutable);
- P116 (la clave de la caché de Mario);
- P123/P124/P125.

El Chuck tiene 29 formas normalizadas: es el que más ocupa.
