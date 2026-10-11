# ARQ-0 — arquitectura del frame: contrato y prototipos de las palancas grandes

2026-10-11. Decisión del usuario: antes de sumar más cosas que cuestan frame,
resolver la arquitectura del frame con números. **Criterio [usuario,
2026-10-11]: 1:1 lo más posible. Si hay que recortar, que no se note:**
medido contra la SNES y mostrado al usuario lado a lado. **La elección la
hace el usuario.**

Mientras dure ARQ-0 quedan **en pausa** META-R, G7-S1, REX2, BANZAI y
las puertas de G7-3 (PROXIMO §2). No se integra al vivo por defecto
ningún prototipo.

## Por qué (medido)

| causa | peso | fuente |
|---|---|---|
| copper con recargas de color por línea, reconstruido cada frame (`build_mid`) | 83 % del frame normal, 180 % en la vuelta | `docs/informe-p123-scroll-1010.md` |
| DMA de los 6 planos (D8: dos playfields de 3) | ≈ 1,6× sobre todo lo que corre en pantalla | `docs/informe-g5l-r-m1-1010.md` §3 |
| espiral de fotos omitidas (Δs > 16 recorre todas las líneas) | ≈ 1,6× en la vuelta | ídem §4 |
| lógica 1:1 | 29-60 % | ROADMAP §2 |
| recortes chicos de CPU | se pierden en el A/B (S10 −6 %, S11, L3 plano) | informes S10/S11/L3 |

## Paso 0 — la vara: diferencia visible contra la SNES

Antes de cualquier prototipo, una herramienta `tools/arq_diff.py` que
compare una captura de WinUAE con la referencia SNES del mismo frame
(`snesorc --shots`, fila Amiga = fila SNES − 1, P128) y dé:

- % de píxeles distintos (con el color de 12 bits de la Amiga: la base
  1:1 ya es la SNES cuantizada a 12 bits, no a 15);
- diferencia perceptual por píxel (CIEDE2000 sobre el color mostrado):
  media, p99, máximo y **área con ΔE ≥ 2** (umbral de "se nota", a
  confirmar con el usuario viendo ejemplos);
- una imagen lado a lado (SNES | Amiga | mapa de diferencias) para que
  el usuario juzgue.

Puerta: con el vivo actual da la diferencia de hoy (la línea base), y en
las capturas exactas de G9/G7-C da 0.

## Paso 1 — medida de partida en los cuatro tramos

WinUAE cycle-exact, BENCH y VBTRACE (`docs/instrucciones-d1-opt.md` paso
1, P120, P126: replay con `bm_build.sh`). Tramos:
1. normal, YI1 ida;
2. vuelta, `stress_back`;
3. meta, el final de YI1 y `oracle_goal`;
4. Rex, `stress_sprites` y `hills2`.

Para cada uno: fotos omitidas, racha, ventana de 250 y ciclos por
componente (lógica, `build_mid`, resto del scroll, G5L, Mario). Es la
tabla de partida del contrato.

## Paso 2 — prototipos (cada uno opt-in, desechable, 1-2 días)

Primero **en papel** (Python, sin 68000): cuánto gana y qué cambia en la
imagen. Al 68000 solo el que lo merezca.

**P1 — 5 planos (PF2 de 2 planos).**
- (a) Offline: colores distintos por línea de la capa 2 de YI1 en todas
  las cámaras. Si en casi todas las líneas caben en 3, el recorte es
  invisible.
- (b) Con el mejor reparto de 3 colores por línea (o por banda), medir el
  ΔE contra la referencia con `arq_diff`.
- (c) Variante `-DARQ_5PL` con BENCH A/B en los cuatro tramos.

**P2 — menos trabajo del copper por frame.**
- (a) Plan de colores del PF1 precalculado por posición de cámara (tablas
  por estado, no por frame): `build_mid` copia o parcha. Medir memoria
  (comprimida, C3) y cuánto de `build_mid` elimina.
- (b) Paleta optimizada offline que reduzca los cambios de color a
  mitad de línea, aceptando ΔE pequeño. Medir cuántos MOVE por línea se
  ahorran y el ΔE.

**P3 — cortar la espiral.** Si P1/P2 no la eliminan, retomar S11
(`docs/informe-g5l-r-s11-1010.md`, opciones A/B), ahora con el costo base
más bajo, y el colchón de listas (D1).

Para cada prototipo, una fila: fotos omitidas por tramo, ciclos ganados,
memoria, ΔE (media/p99/área) y una imagen lado a lado del peor frame.

## Paso 3 — decisión del usuario y contrato del frame

Informe `docs/informe-arq-0-<fecha>.md` con la tabla y las imágenes. El
usuario elige. Con la elección se escribe el **contrato**: porcentaje del
frame por componente (lógica, scroll, sprites, efectos, HUD, audio,
margen). Cada componente queda con su tope. Después se vuelven a abrir las
tarjetas en pausa, cada una con su tope:
- un componente nuevo entra solo si cabe en su parte;
- la regresión lo comprueba con el BENCH.

## No hacer

- No tomar la decisión de diseño por el usuario (D8, D1 y D10 son
  suyas).
- No integrar un prototipo al vivo por defecto ni cambiar su hash sin la
  decisión.
- No usar tablas por número de frame (por estado del juego o posición de
  cámara sí).
- No declarar "no se nota" sin la medida de `arq_diff` y la imagen.
