# Estudio G1 + G0: sprites del nivel a 256 px, y encadenar por DMA contra recargar `SPRxPT` por copper

> 2026-10-04. Solo herramientas y modelo: **no se midió en WinUAE** (ver "Qué
> no se probó"). Insumo para G2 (diseño de 9.2). Todo es reproducible con
> los comandos de cada sección, desde `tools/` y con
> `PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH"` (P82).

> **Medida posterior, 2026-10-05:** [G0 en WinUAE a 256 px](medida-g0.md)
> reemplaza los plazos teóricos y el coste de copia de este estudio.
> PT temprano + POS/CTL después del control DMA funciona; PT desde h=$D8
> anterior llega tarde. Copiar 1408 B cuesta ~7,5 % durante el display.
> El [diseño G2 vigente](diseno-9.2.md) usa esos resultados y distingue las
> ventanas sintéticas de las que todavía hay que probar en el juego.

## 0. Resumen para G2

1. **Las herramientas viejas ya cortaban a 256 px**, pero contaban a Mario
   como una tesela más. Mario no es eso: `mspr.c` le reserva **1 o 2
   columnas** (2 si la caja de sus teselas mide > 16 px; entre el 10 y el 27 %
   de los frames según la grabación, 47 % en `pw_seta`) en todo el rectángulo de sus
   teselas, y `mario_draw` ata hoy SPR0-3 a Mario siempre. **Libres de verdad:
   2 ó 3 columnas, no 4.** (4 sólo en las líneas fuera del rectángulo de Mario.)
2. **El Banzai Bill (`$9F`, 64×64 = 4 columnas) es el único que hace falta
   mandar a bob siempre.** Ocupa las 4 columnas durante 64 líneas: con él
   en sprites no cabe nada más en esas líneas. Con `$9F` a bob, `oam_yi1`
   y `banzai` quedan en **0 frames** con algún objeto fuera, a cualquier `gap`.
3. **El Rex (`$AB`) es el segundo problema, y por su ancho:** su pose normal
   mide **20 px** (4113 de ~4900 muestras), así que cuesta **2 columnas**, no 1.
   Dos Rex + Mario = 5 columnas. Con `$9F` a bob y `gap` 1 quedan fuera
   1644 de 69 208 frames (2,4 %), casi todos por `$AB` (y algún Chuck `$95`,
   24-32 px = 2 columnas). Ver el punto 6 para una salida.
4. **La regla de ≥ 17 líneas para reusar un canal es cara:** a `gap` 17 son
   2868 frames fuera (4,1 %) contra 1644 (2,4 %) a `gap` 1. Si el copper recarga
   `SPRxPT`, `gap` 1 basta (G0), y se ahorra casi la mitad del bob/parpadeo.
5. **Los que quedan fuera son pocos y llegan a ráfagas:** con `$9F` a bob y
   `gap` 1, máximo 2 objetos a la vez en casi todo (3 en `pw_estrella` y
   `stress_back`), y 502 "episodios" en 69 208 frames (un episodio = un
   objeto que pasa de dentro a fuera). El parpadeo (alternar frames) es
   viable para el segundo Rex; el bob para el Chuck.
6. **Idea sin verificar (`--tail`):** el sobrante de 4 px del Rex (20 − 16)
   va en **un canal suelto de 3 colores** en vez de una columna adosada de 15
   (8 canales: Mario 2 + 2 Rex × 3 = 8). Baja los frames fuera de 1644 a
   **1242** (`yi1`: 55 → 7). Hay que ver los píxeles del sobrante: ¿caben en 3 colores?
7. **G0: recargar por copper.** Con `$9F` a bob y `gap` 1 hay 1692
   recargas de columna en `oam_yi1` (3017 en `oracle_yi1`, 3617 en
   `stress_back`), una por cada reuso vertical. Con 2 MOVE por canal (banco de
   64 KB distinto) y la recarga en el borrado de la línea, **0 recargas sin
   hueco** en `oam_yi1`, `oracle_yi1`, `oracle_chuck` y `oracle_stress_back`,
   con el copper del modelo de `copsim.py` (14 MOVE en el borrado, ranuras cada
   16 px). Sólo falla (0,03 %-2 %) si además hay que reescribir
   `SPRxPOS`+`SPRxCTL` por canal **y** se prohíbe usar el borrado.
8. **Encadenar por DMA cuesta CPU:** copiar el flujo de las columnas con ≥ 2
   objetos es de media 12-240 B por frame (0,0-0,8 % del frame) y de máximo
   144-1400 B (0,5-**4,5 %** del frame a 4,6 ciclos/B, sin contar el DMA de
   planos). Cabe en el 8 % de G2, pero no es gratis; el copper es 0 CPU.
9. **Decisión G0: "recargar por copper"** (sección 4), con el encadenado por
   DMA como plan B por objeto; no hace falta "mixto" por línea.
10. **Para G2, pedir a `mksprgfx.py`/`mspr.c`:** el ancho real de cada pose
    (Rex 16-20-24...), poses de Rex lo más estrechas posible, y que el
    asignador trate a Mario con su 1 ó 2 columnas reales (no una constante).

## 1. Qué cambió respecto de los estudios de 320 px

| | antes (`oamstudy`, `d8demote`, `copsim`) | ahora |
|---|---|---|
| ancho | las tres ya cortaban a 256 px (`parse` descarta x ≥ 256; `copsim` `SCREEN = 256`); el texto de `decisiones-medidas.md` habla de 320 por el origen de D8 | sin cambio (se verificó) |
| columnas de Mario | Mario = una tesela más en la cobertura (`cover`) | `mario_box`: 1 ó 2 columnas (regla de `mspr.c`), en todo su rectángulo; el resto de objetos se cubren aparte |
| columnas libres | 4 − lo que cubran las teselas | 4 − (1 ó 2) **mientras Mario esté en la línea** |
| grabaciones | sólo `oam_yi1.txt` (2500 frames) | `oam_yi1.txt` + los 26 `oracle_*.txt` (69 208 frames de modo `$14`, translevel `$29`) |
| objetos | por paleta y cercanía | por **ranura de sprite de SMW** (campo "slots" de la grabación, cruzado por posición con la cámara) + clusters para lo que no tiene ranura |

Opciones nuevas (el comportamiento por defecto no cambia; se comprobó que
`oamstudy.py`, `d8demote.py` y `copsim.py` sin opciones dan los mismos números
de antes: 2310 líneas > 4 columnas, 45 frames sin resolver, 1916 cargas que no entran):

- `oamstudy.py --real-cols`, `d8demote.py --oam F --level L --real-cols`,
  `copsim.py --oam F --level L`;
- `copsim.py --sprpt {1,2} [--pt-extra {1,2}] [--pt-first] [--pt-mid-only] [--gap N] [--force-bob 9F]` (G0);
- herramienta nueva `tools/g1study.py` (asignador de columnas, tabla de G1,
  coste del encadenado: `--chain`, hipótesis `--tail`).

Las grabaciones se solapan mucho (casi todas son el mismo nivel con otro
mando): **no sumar los totales como si fueran independientes**; sirven para
ver que el resultado no depende de un solo recorrido.

## 2. G1 — columnas

### Modelo (`tools/g1study.py`)

- 4 columnas adosadas (8 sprites; a 256 px vuelve el sprite 7, D10).
- Mario (paleta OAM 0) reserva `mario_box` = 1 ó 2 columnas durante todo
  el rectángulo de sus teselas.
- Cada objeto pide `k` = máximo de ventanas de 16 px que cubren sus teselas
  en una línea, durante `[y0, y1)`.
- Un canal se reusa si entre el fin de uno y el inicio del siguiente hay
  ≥ `gap` líneas. Se coloca por Y creciente (primer hueco). Lo que no entra
  se saca con el menor número de objetos (a igual número, el de más área): **ese
  objeto va a bob (o parpadea)**.
- `--force-bob 9F`: el Banzai Bill va siempre a bob y no ocupa columnas
  (6182 frames lo tienen en pantalla).

### Tabla

Columnas: *frames* (modo `$14`); *Mario 2 col* (frames con Mario ancho);
*frames/líneas > libres* (modelo por línea con Mario real, sin sacar nada);
*frames con Banzai*; *frames con objeto fuera, sin forzar, gap 17* (incluye
al Banzai); *Banzai a bob*: frames con algún objeto fuera / objetos fuera
(suma) / máximo a la vez / episodios, con `gap` 17 y con `gap` 1;
*d8demote*: líneas > libres / líneas que se resuelven pasando a bob Rex,
Banzai o Mario (color incluido) / frames que quedan sin resolver
(`d8demote --real-cols`; es el estudio D8 con los colores del terreno,
no mira los `gap`).

| grabación | frames | Mario 2 col | frames con líneas > libres | líneas > libres | frames con Banzai | frames con objeto fuera (sin forzar, gap 17) | Banzai a bob, gap 17: frames / objetos / máx. juntos / episodios | Banzai a bob, gap 1: frames / objetos / máx. / episodios | quién queda fuera (gap 1) | `d8demote` (Mario real): líneas >libres / resueltas con bob / frames sin resolver |
|---|--:|--:|--:|--:|--:|--:|---|---|---|---|
| oam_yi1 | 2500 | 677 | 130 | 2327 | 180 | 134 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | - | 2327 / 1707 / 57 de 2500 |
| banzai | 1081 | 110 | 219 | 3790 | 347 | 247 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | - | 3790 / 3790 / 0 de 1081 |
| chuck | 2991 | 315 | 289 | 5433 | 345 | 411 | 171 / 201 / 3 / 31 | 89 / 98 / 2 / 28 | $AB:78, $95:20 | 5433 / 4963 / 84 de 2991 |
| diagpipe | 2700 | 382 | 58 | 1627 | 79 | 74 | 16 / 16 / 1 / 3 | 6 / 6 / 1 / 1 | $AB:6 | 1627 / 1468 / 21 de 2700 |
| goal | 3069 | 283 | 283 | 5404 | 345 | 398 | 158 / 188 / 3 / 31 | 81 / 90 / 2 / 28 | $AB:78, $95:12 | 5404 / 4980 / 74 de 3069 |
| goal_low | 3208 | 297 | 283 | 5404 | 345 | 410 | 170 / 200 / 3 / 33 | 78 / 87 / 2 / 27 | $AB:78, $95:9 | 5404 / 4980 / 74 de 3208 |
| goal_miss | 2913 | 313 | 299 | 5532 | 345 | 437 | 197 / 227 / 3 / 33 | 97 / 106 / 2 / 28 | $AB:78, $95:28 | 5532 / 4980 / 90 de 2913 |
| goalhit | 3069 | 299 | 283 | 5404 | 345 | 458 | 218 / 248 / 3 / 38 | 106 / 115 / 2 / 31 | $AB:78, $7B:25, $95:12 | 5404 / 4980 / 74 de 3069 |
| hills | 2155 | 321 | 57 | 1458 | 78 | 68 | 11 / 11 / 1 / 2 | 0 / 0 / 0 / 0 | - | 1458 / 1299 / 21 de 2155 |
| hills2 | 2836 | 403 | 213 | 4042 | 258 | 306 | 146 / 190 / 3 / 36 | 89 / 98 / 2 / 28 | $AB:98 | 4042 / 3135 / 88 de 2836 |
| normal | 1255 | 241 | 56 | 1430 | 77 | 67 | 10 / 10 / 1 / 2 | 0 / 0 / 0 / 0 | - | 1430 / 1271 / 21 de 1255 |
| pipe | 1821 | 398 | 56 | 1430 | 77 | 85 | 28 / 28 / 1 / 4 | 12 / 12 / 1 / 1 | sin ranura:12 | 1430 / 1271 / 21 de 1821 |
| pw_1up | 2217 | 277 | 243 | 4970 | 272 | 298 | 97 / 127 / 3 / 24 | 64 / 73 / 2 / 24 | $AB:73 | 4970 / 4559 / 61 de 2217 |
| pw_bloques | 2076 | 269 | 248 | 4804 | 279 | 307 | 101 / 131 / 3 / 25 | 65 / 74 / 2 / 25 | $AB:74 | 4804 / 4393 / 61 de 2076 |
| pw_c7 | 1330 | 241 | 56 | 1430 | 77 | 67 | 10 / 10 / 1 / 2 | 0 / 0 / 0 / 0 | - | 1430 / 1271 / 21 de 1330 |
| pw_estrella | 1836 | 276 | 201 | 3501 | 144 | 257 | 155 / 214 / 3 / 36 | 124 / 158 / 3 / 36 | $AB:117, $05:36, sin ranura:5 | 3501 / 2924 / 87 de 1836 |
| pw_flor | 2430 | 293 | 248 | 4809 | 279 | 307 | 101 / 131 / 3 / 25 | 64 / 73 / 2 / 24 | $AB:73 | 4809 / 4398 / 61 de 2430 |
| pw_medio | 2367 | 306 | 233 | 5048 | 235 | 267 | 76 / 90 / 2 / 17 | 44 / 44 / 1 / 13 | $AB:44 | 5048 / 3585 / 131 de 2367 |
| pw_morir_caida | 2050 | 269 | 146 | 2984 | 144 | 205 | 101 / 131 / 3 / 25 | 64 / 73 / 2 / 24 | $AB:73 | 2984 / 2573 / 61 de 2050 |
| pw_morir_enemigo | 1974 | 269 | 146 | 2984 | 144 | 258 | 154 / 184 / 3 / 26 | 64 / 73 / 2 / 24 | $AB:73 | 2984 / 2573 / 61 de 1974 |
| pw_seta | 926 | 432 | 70 | 1444 | 77 | 124 | 67 / 67 / 1 / 3 | 64 / 64 / 1 / 2 | $AB:64 | 1444 / 1285 / 21 de 926 |
| pw_yoshicoin | 2434 | 276 | 278 | 5421 | 347 | 365 | 125 / 157 / 3 / 31 | 72 / 81 / 2 / 27 | $AB:77, $95:4 | 5421 / 4997 / 74 de 2434 |
| shells | 2273 | 305 | 169 | 3112 | 144 | 355 | 251 / 297 / 3 / 48 | 161 / 178 / 2 / 45 | $AB:160, $05:11, $B9:7 | 3112 / 2698 / 63 de 2273 |
| stress_back | 4127 | 335 | 379 | 5742 | 345 | 564 | 324 / 390 / 3 / 73 | 207 / 236 / 3 / 61 | $AB:216, $95:11, $B9:5, $05:4 | 5742 / 5252 / 86 de 4127 |
| stress_piranha | 3018 | 511 | 56 | 1430 | 77 | 89 | 32 / 32 / 1 / 6 | 0 / 0 / 0 / 0 | - | 1430 / 1271 / 21 de 3018 |
| stress_sprites | 1915 | 255 | 181 | 4987 | 234 | 221 | 45 / 48 / 2 / 13 | 19 / 19 / 1 / 7 | $AB:19 | 4987 / 4217 / 103 de 1915 |
| stress_vert | 1766 | 248 | 111 | 2041 | 125 | 138 | 44 / 47 / 2 / 13 | 19 / 19 / 1 / 7 | $AB:19 | 2041 / 1789 / 35 de 1766 |
| yi1 | 6871 | 1008 | 359 | 6201 | 438 | 375 | 60 / 60 / 1 / 11 | 55 / 55 / 1 / 11 | $AB:55 | 6201 / 5628 / 51 de 6871 |

Comandos (cada fila sale de uno de ellos):

```bash
cd tools
python g1study.py --gap 17                       # sin forzar el Banzai
python g1study.py --gap 17 --force-bob 9F        # Banzai a bob
python g1study.py --gap 1  --force-bob 9F
python g1study.py --gap 1  --force-bob 9F --tail # hipotesis del canal suelto (punto 6)
python d8demote.py --oam ../work/oracle_chuck.txt --real-cols
python oamstudy.py --real-cols                   # lineas por numero de columnas, oam_yi1
```

### Lectura

- **Quién pide más columnas que las libres:** el Banzai (4 columnas, 64
  líneas) en 6182 frames; con él en bob, el Rex `$AB` (20 px = 2 columnas)
  junto a Mario y otro Rex o el Chuck `$95` (24-32 px de ancho). El Chuck
  aparece en `chuck`, `goal*`, `pw_*` y `stress_back`.
- **Las dos de referencia.** `oam_yi1`: 180 frames con Banzai y **0 con
  objeto fuera** si el Banzai va a bob (134 si no). `oracle_yi1` (el recorrido
  largo): 438 frames con Banzai; con él a bob y `gap` 1 quedan fuera 55
  frames (`$AB`, 11 episodios, de a uno).
- **Peor caso:** `stress_back`, 207 frames con algún objeto fuera (`gap` 1),
  máximo 3 a la vez. Con `gap` 17: 324 frames y 73 episodios.
- "sin ranura" (`pipe`, `goalhit`, `pw_estrella`: 5-21 frames) son partículas,
  puntos y estrellas de Mario; `$05` es el caparazón de Koopa, `$B9` el Info
  Box, `$7B` la cinta de la meta, `$83` el bloque `?` volador (con `gap` 17
  aparece 10 frames por grabación al principio del nivel).
- `d8demote` (el estudio D8 con los colores del terreno, última columna): con
  Mario real quedan sin resolver **57 de 2500** frames de `oam_yi1` (eran 45
  con Mario como tesela). En las grabaciones largas son 21-131 frames (131 en
  `pw_medio`). Pasar a bob al Rex sólo resuelve el 3,7 % de las líneas (era
  25,8 %): al contar el rectángulo de Mario, el Rex ya no libera lo bastante.
  **El Banzai en bob resuelve el 62 % y es lo único que mueve la aguja.**
- **Cuántos objetos irían a bob o parpadearían** con las reglas de
  `automatizar-9.2.md` §1 (sin contar el Banzai, que va siempre a bob):
  con `gap` 17, 3435 objetos-frame en 2868 frames y 591 episodios; con
  `gap` 1, 1832 en 1644 frames y 502 episodios (69 208 frames en total,
  solapados). Un episodio dura de media 5,8 frames con `gap` 17 y 3,6 con
  `gap` 1: más largo que un período de parpadeo (2 frames), así que el
  parpadeo se nota; el bob es la salida segura.

## 3. Bob del Banzai

`d8demote` ya daba el 61,8 % de las líneas problemáticas con el color
incluido; G1 lo confirma en todas las grabaciones. El Banzai en bob deja en
**0** los frames de `oam_yi1` y `banzai` con algún objeto sin columna, pero el
color (`d8demote`) deja 57 frames de `oam_yi1` con el color más cercano. G7 es
el sitio para eso.

## 4. G0 — recargar `SPRxPT` por copper o encadenar por DMA

### Qué se modeló

`copsim.py` (en lo que ya hacía, sin cambios) reparte línea a línea las cargas
de la capa 1, la capa 2 y los colores de los sprites entre el **borrado**
(`--hbl`, 14 MOVE medidos en `copbench.s`; la lista de hoy usa como máximo 8,
decisiones-medidas "máx. 8 (presupuesto 14)") y las **ranuras a mitad de
línea** (una cada 16 px; P39: el WAIT también ocupa una). En el modelo base
(`oam_yi1`) 389 397 de 560 000 líneas no cargan nada en el borrado y 512 723 no
cargan nada a mitad de línea; el máximo es 9 en el borrado y 10 ranuras.

Se añadieron las **recargas de `SPRxPT`** (`--sprpt M`, `M` = MOVE por canal: 1
si todas las poses están en un banco de 64 KB, 2 si no). Una columna adosada
son **2 canales**, así que cada reuso cuesta `2 M` MOVE (4 con `M` = 2). Salen
del asignador de `g1study.py` (`gap` 1, Banzai a bob): una por cada par de
objetos consecutivos de una misma columna.

Hipótesis de tiempo (de la documentación, no medida aquí; P46): el DMA lee las
palabras de control del siguiente objeto **en la línea `y1`** (la que sigue a la
última del anterior), en la ranura de su canal (hpos `$15 + 4 n`). La recarga
tiene que estar escrita antes. Se probaron dos sitios:

1. **el borrado de la línea `y1`** (lo primero que se escribe; el plazo es de
   unos 5 + n MOVE desde su inicio), con `--pt-first` si debe ir antes que los
   colores; lo que no cabe pasa a las ranuras libres de la línea anterior;
2. **sólo las ranuras libres a mitad de la línea anterior** (`--pt-mid-only`):
   sin plazo de DMA, pero hay que sacarlas de lo que dejan los colores.

`--pt-extra E` suma `E` MOVE por canal (1 = `SPRxPOS`, 2 = `SPRxPOS` +
`SPRxCTL`). **La tarjeta no lo contaba y importa:** una pose precalculada y
compartida no puede llevar en sus palabras de control la Y/X de cada objeto (dos
Rex en la misma pose y en sitios distintos), así que o el copper reescribe
`SPRxPOS`/`SPRxCTL` después de que el DMA leyó las palabras de control, o se
copia el encabezado (y eso ya es "encadenar" con parche).

### Resultado (Banzai a bob, `gap` 1)

Recargas de columna **sin hueco** (de las del recorrido), con `hbl` 14 / 10 (el
segundo es un copper más cargado que lo medido), `--pt-first`:

| grabación (recargas de columna) | `M`=1, E=0 | `M`=2, E=0 | `M`=2, E=1 | `M`=2, E=2 |
|---|---|---|---|---|
| `oracle_chuck` (2939) | 0 / 0 | 0 / 0 | 0 / 1 | 1 / 5 |
| `oracle_stress_back` (3617) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| `oracle_yi1` (3017) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

(`oam_yi1`, 1692 recargas: 0 sin hueco con `M` = 1 y 2, E = 0, `hbl` 14 y 8.)

Plazo del borrado: líneas en las que el borrado **no alcanza** para todos los
MOVE de `SPRxPT` del reuso (se usan las ranuras de la línea anterior), de 2561
líneas con recarga en `oracle_chuck`, `M` = 2, E = 0, sin `--pt-first`:

| `hbl` | 14 | 10 | 8 | 6 |
|---|---|---|---|---|
| líneas | 5 | 332 | 685 | 1091 |

Con `--pt-mid-only` (sin tocar el borrado), `M` = 2, recargas sin hueco:

| grabación | E=0 | E=1 | E=2 |
|---|---|---|---|
| `oracle_chuck` | 1 de 2939 (0,03 %) | 8 (0,27 %) | **60 (2,04 %)** |
| `oracle_stress_back` | 0 | 0 | 49 (1,35 %) |
| `oracle_yi1` | 0 | 0 | 1 (0,03 %) |

Efecto en lo que ya había: las 1916 cargas que no entran de `oam_yi1` (todas de
la capa 1) siguen siendo 1916 con `hbl` 14; en `oracle_chuck` con `hbl` 8 pasan
de 4068 a 4113 (+45) si `SPRxPT` tiene prioridad. La lista del copper crece de
429 a 432 entradas por frame de media (+0,7 %) y de 854 a 862 de máximo
(`--sprpt 2`, `oam_yi1`).

Comandos:

```bash
python copsim.py --oam ../work/oracle_chuck.txt --sprpt 2 --pt-extra 1 --hbl 10 --pt-first
python copsim.py --oam ../work/oracle_chuck.txt --sprpt 2 --pt-extra 2 --pt-mid-only
python copsim.py --oam ../work/oracle_chuck.txt --sprpt 2 --hbl 6
```

### Coste del encadenado por DMA (la alternativa)

Encadenar exige que los objetos de una columna estén contiguos en un mismo
flujo: la CPU copia, por frame, el flujo de las columnas con ≥ 2 objetos (menos
el de Mario, que ya escribe `mspr.c`). Un objeto de `k` columnas y `L` líneas
son `k · 2 · (8 + 4 L)` bytes (el Rex de 32 líneas: 272 B por columna, como decía
`docs/plan-tecnico.md` §10.6). `MOVEM.L` copia a 4,6 ciclos/B (76 + 72 por 32 B); un frame PAL
son 141 876 ciclos.

```bash
python g1study.py --chain --gap 1 --force-bob 9F
```

| grabación | media B | p99 B | max B | max % del frame |
|---|--:|--:|--:|--:|
| `oam_yi1` | 133 | 696 | 736 | 2,4 |
| `oracle_yi1` | 92 | 480 | 896 | 2,9 |
| `oracle_chuck` | 221 | 912 | 1328 | 4,3 |
| `oracle_hills2` | 240 | 1056 | 1400 | 4,5 |
| `oracle_stress_back` | 209 | 1008 | 1376 | 4,5 |

Es un mínimo: no cuenta los ciclos que el DMA de planos le quita a la CPU en chip
RAM (5-6 planos) ni la doble lista (ACE copia sólo los píxeles que cambiaron).

### Decisión G0: **recargar por copper**

- Con `M` = 1 ó 2 y sin reescribir el encabezado (E = 0), **no falló ni una
  recarga** en cuatro grabaciones largas con `hbl` 14, y casi ninguna con un
  copper bastante más cargado (`hbl` 10).
- Lo que lo puede romper es **E = 2** (reescribir `SPRxPOS` + `SPRxCTL` por
  canal): 2 % de las recargas del Chuck si se prohíbe el borrado
  (`--pt-mid-only`), 1 de 2939 con el borrado.
- No hace falta "mixto" por línea. Si G5 ve que una línea concreta no entra, el
  plan B por **objeto** es copiar ese flujo (≤ 1400 B, ≤ 4,5 % del frame en el
  peor frame de todas las grabaciones; media ≤ 0,8 %).
- Pedido a G2/G3: **todas las poses de sprites en un mismo banco de 64 KB**
  (`M` = 1) y contar E = 1-2 (`SPRxPOS`/`SPRxCTL`) en el presupuesto de G5.

## 5. Qué no se probó

- **Nada de esto se midió en WinUAE.** No se escribió `player/bench_g0.s`. El
  modelo de G0 es `copsim.py` con el presupuesto medido en `copbench.s` (14 MOVE
  de borrado, 1 ranura cada 16 px, a 320 px); a 256 px el copper es otro modelo
  (P46) y el plazo del DMA de sprites en el borrado no está calibrado. Falta
  medirlo: una lista con WAIT + `SPRxPT` + `SPRxPOS` en el borrado de una línea
  donde termina un sprite, mirando en qué línea y X aparece el siguiente.
- El plazo exacto del DMA de sprites (control de cada canal en `$15 + 4 n`) sale
  de la documentación del hardware (investigacion-ports §12.5), no de una medida
  nuestra.
- Los colores no entran en la tabla de G1 (15 de la columna adosada, 3 del canal
  suelto de `--tail`): están en `copsim` (cargas) y `d8demote`.
- La asociación tesela → ranura (`group_objects`) es por posición (±16 px); un
  Rex pegado a otro puede intercambiar teselas sin cambiar el número de columnas.
- Frames fuera de modo `$14` y el subnivel de la tubería (translevel distinto de
  `$29`) no entran.

## 6. Trampas nuevas (sin número)

- **"4 columnas libres" ya incluía a Mario.** Mario usa 1 ó 2 (`mspr.c`:
  `cols = x1 - bx > 16 ? 2 : 1`), pero `mario_draw` ata SPR0-3 siempre y deja la
  segunda pareja sin usar en el 73-90 % de los frames. 9.2 tiene que poder dársela
  a un enemigo.
- **El Rex mide 20 px, no 16.** Su pose normal necesita 2 columnas de 16. Dos Rex
  + Mario = 5 columnas.
- **Una pose compartida no lleva su Y/X.** Con `SPRxPT` por copper hay que contar
  también `SPRxPOS` y `SPRxCTL`.
- Windows: sin diferencias; las herramientas corren en segundos (`d8demote` sobre
  las 27 grabaciones, unos minutos).
