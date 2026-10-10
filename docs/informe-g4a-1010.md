# G4-A — todos los enemigos en sprites: inventario y presupuesto

2026-10-10. Rama `g2t-b2bis`. **Solo medida, en la PC; el binario no
cambia.** Tarjeta: `instrucciones-g4a.md`. Herramienta: `tools/g4a.py`
(nuevo). Salidas en `work/g4a/` (derivadas de la ROM, R9).

## 1. Fuentes y método

- **Inventario exacto:** `g4a.py traceall` compila el host de la PC
  (`tools/marioverify.c` + el C del juego, como `informe-g2.md`) y escribe
  la traza SOT1 de **las 30 grabaciones** (`GAME_OAM_TRACE`), sin el
  filtro de 4 tipos de G2. Cada despacho se cruza con la OAM de la SNES
  del mismo frame. Coinciden todos menos 34 despachos del Rex, que se
  descartan. La clave de forma es la de `g5l.build_table`: fichas
  relativas a la ranura y prioridad.
- **Hueco del inventario:** el host solo traza sprites con la rutina
  gráfica portada (`spr_oam_n`). **Faltan los power-ups (seta, flor,
  estrella, 1-UP, luna) y el `?` volador.** Son de 16×16, una columna;
  no cambian el orden de magnitud (estimado: ≤ 1 KB cada uno en slow).
- `g4a.py inv2` (atribución por posición contra la WRAM) quedó descartado:
  al Rex le da 937 formas de 87×96, porque le suma partículas y vecinos.
- **Memoria:** `g4a.g5l_cost` arma la variante limpia (un índice por
  color) y mide `g5l.variant_record` y `g5l.clean_streams`. **Validado
  exacto:** sobre las 48 formas del banco G3, 4 × 26.222 = 104.888 B,
  igual que los registros de `work/g5l/g5l.bin`.

## 2. Inventario (30 grabaciones, exacto)

| nº | tipo | frames | máx. a la vez | formas | normalizadas (1) | tamaño máx. | columnas | colores (fila) |
|---|---|---:|---:|---:|---:|---|---:|---|
| `$AB` | Rex | 40.166 | 5 | 59 | 17 | 20×32 | 2 | 7 (7) |
| `$4F` | Jumping Piranha | 14.782 | 1 | 24 | 4 | 16×21 | 1 | 8 (5) |
| `$9F` | Banzai Bill | 7.800 | 1 | 6 | 4 | 64×64 | 4 | 7 (6) |
| `$B9` | Info Box | 6.358 | 1 | 1 | 1 | 16×16 | 1 | 7 (6) |
| `$BD` | Sliding Koopa | 4.877 | 1 | 17 | 6 | 16×16 | 1 | 5 (5) |
| `$05` | Red Koopa (caparazón) | 2.906 | 1 | 6 | 6 | 16×16 | 1 | 5 (5) |
| `$95` | Clappin' Chuck | 2.212 | 1 | 90 | 29 | 30×29 | 2 | 8 (7) |
| `$7B` | cinta de meta | 1.990 | 1 | 3 | 1 | 24×8 | 2 | 5 (2) |
| `$02` | (sin nombre) | 896 | 1 | 4 | 4 | 16×16 | 1 | 5 (5) |

(1) La misma lista de fichas con otro desplazamiento respecto de la
ranura es la misma imagen: normalizar al mínimo dx/dy deja el origen
para el tiempo de ejecución.

Ninguna forma pasa de 15 colores: todas entran en un par acoplado. El
Banzai mide más de 32 filas, el límite actual de `variant_record`, y el
cálculo lo parte en franjas de 32.

## 3. Hallazgo: poses del Rex que G5L no dibuja hoy

El banco G3 (48 formas) sale de las trazas `yi1`, `normal` y `spin_kill`
más las poses legales de la ROM. En otras grabaciones aparecen 33 formas
del Rex que no están: el Rex aplastado o medio aplastado (fichas
`$1A8`/`$18C` solas, `$18A` + `$1AA`/`$1AC`) con otro desplazamiento
vertical (−3 … +1). G5L busca la forma exacta (`plan_frame`: `rex_sin_forma`)
y **ese Rex no se dibuja**:

| grabación | frames con Rex | con una forma fuera del banco |
|---|---:|---:|
| `yi1`, `normal` | 2.288, 661 | 0, 0 |
| `hills2` | 2.110 | **340** |
| `stress_sprites` | 1.189 | 96 |
| `shells` | 1.522 | 62 |
| `stress_back` | 2.939 | 62 |
| `pw_estrella` | 1.110 | 37 |

**30 de las 33 son traslaciones de una forma que ya está en el banco.**
Con la clave normalizada, el banco del Rex pasa de 48 a 22 formas y cubre
todas menos 3.

## 4. Columnas por línea y cota de bobs

`g4a.py lines`, con toda la OAM fuera de Mario (incluye partículas):
mínimo de ventanas de 16 px que cubren cada línea. En `yi1`, 644 de
7.699 frames piden más de 2 columnas en alguna línea, 123 más de 4, y el
máximo es 5. En `stress_back`: 862, 200 y 7 de 4.127. La tabla completa
está en `work/g4a/lines.json`.

Cota de bobs (`traceall`, `bob_bound`): objetos enteros, asignados en
orden de despacho a 2 columnas acopladas (canales 4-7), o a 4 en las
líneas sin Mario (±1), reservando una línea antes para el PT (G0). Lo que
no entra se cuenta como bob. Es una cota, no el plan de G4:

| grabación | frames | con bob | máx. bobs | por tipo |
|---|---:|---:|---:|---|
| `yi1` | 5.083 | 545 | 1 | Banzai 359, Rex 186 |
| `stress_back` | 3.230 | 638 | 3 | Rex 481, Banzai 250, Chuck 20, meta 17, caparazón 7 |
| `shells` | 1.682 | 431 | 3 | Rex 311, caparazón 120, Banzai 106 |
| `stress_piranha` | 2.017 | 98 | 1 | Banzai 61, piraña 37 |

El área máxima de bob por frame es 4.096 px, un Banzai. El Banzai mide 4
columnas: cuando se cruza con las líneas de Mario no entra nunca en
sprites. Eso es la regla de D8 ("bob en PF1 cuando hay más de 4
columnas") y pide el segundo PF1 de G7 (+59.136 B de chip).

## 5. Memoria

Formas normalizadas, sin las poses recortadas por el borde que son un
subconjunto de otra (`fmt`, `work/g4a/shapes.json`):

| formato | slow, los 9 tipos | de eso, el Rex | chip (DMA) |
|---|---:|---:|---:|
| G5L actual, 4 mapas | 180.236 | 36.152 | 83.576 |
| G5L actual, 1 mapa | 46.130 | 9.242 | 21.240 |
| máscaras compartidas entre mapas, 4 mapas | 82.874 | 17.462 | 83.576 |
| sin máscaras guardadas (se calculan desde el DMA), 4 mapas | 50.420 | 11.232 | 83.576 |
| sin máscaras guardadas, 1 mapa | 13.676 | 3.012 | 21.240 |
| *(hoy: la tabla del Rex, 48 formas sin normalizar)* | *128.724 con las máscaras de Mario* | | *16.656* |

Las máscaras por grupo (`g5l_patch`) son el 69 % del registro. Para una
forma, los píxeles de cada color son los mismos en los 4 mapas; solo
cambia el índice. Guardarlas una vez por forma no cuesta nada en
ejecución: el byte de relleno del grupo puede llevar el número de máscara.
El chip con 4 mapas se calculó con permutaciones sintéticas (en el Rex,
4 mapas ≈ 3,3 × 1 mapa, como el banco real).

Margen del vivo (`memmap.py work/rg_bm1/game.lst`): slow 61.288 B, chip
24.856 B. Si se reemplazan la tabla y el DMA del Rex de hoy, quedan
≈ 167 KB de slow (las máscaras de Mario, 22 KB, se conservan) y ≈ 41,5 KB
de chip.

## 6. Qué formato puede servir para G4

Decisión de diseño (no es del usuario: no cambia lo que se ve):

1. **Clave normalizada.** Es una ganancia pura: el Rex baja de 48 a 22
   formas y se arregla el Rex que hoy no se dibuja (§3). El costo en
   ejecución es una pasada de mínimos sobre ≤ 6 fichas.
2. **Máscaras compartidas entre mapas.** También es ganancia pura: 4
   mapas del Rex en 17,5 KB. Con los puntos 1 y 2, la tabla del Rex
   (las 24 formas normalizadas del banco y de las grabaciones) pasa de
   128.724 B a 45.918 B, contando las máscaras de Mario, y libera
   ≈ 82 KB de slow.
3. **Mapas por tipo.** El chip ordena: 4 mapas para todos son 84 KB y no
   entran. El Rex con 4 (16,3 KB) y los demás con 1 (≈ 17 KB) suman
   ≈ 33 KB, dentro de los ≈ 41,5 KB. Quedan ≈ 8 KB para el segmento de G5
   y nada para el segundo PF1.
4. **Máscaras calculadas en vivo**, solo si falta slow. Cuestan CPU en las
   fotos con banda reasignada; hay que medirlo antes.

**Lo que no entra con ningún formato:** el Banzai como bob (segundo PF1,
+59 KB de chip) y el audio (≤ 64 KB de chip) no caben en el chip de hoy.
Primero hay que sacar las tablas de CPU que están en chip (C2/C4,
135.468 B). La slow tampoco alcanza para todas, ni siquiera con el ahorro
del punto 2, así que hace falta compresión (C3) o recortar esas tablas. Se
registra como dato para la ola 4/5. No se elige aquí.

## 7. Siguiente

Puntos 1 y 2 sobre el Rex de G5L-R, que hoy existe: tarjeta **G5L-N**
(`instrucciones-g5l-n.md`). Arregla una diferencia visible (§3), libera
slow y deja el formato listo para G4.
