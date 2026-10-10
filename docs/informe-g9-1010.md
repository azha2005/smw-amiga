# G9 — la imagen de los sprites contra la OAM de la SNES

2026-10-10. Rama `g2t-b2bis`. Tarjeta: `instrucciones-g9.md`. Sigue a
G4-B (`informe-g4-b-1010.md`).

**Resultado:**

- **Dibujo:** todos los tipos de enemigo que G5L dibuja en YI1, y Mario,
  salen **exactos contra la OAM de la SNES** en las capturas de WinUAE.
  Son 10 fotos y 8 tipos, limpias y con bandas.
- **Lógica:** apareció otra clase de diferencia, que no es de dibujo.
  Algunas instancias de objetos del port se desvían de la SNES y quedan
  corridas durante cientos de fotos. Va a la tarjeta siguiente, **L-DER**.

## 1. La herramienta (`tools/sprshot_cmp.py`)

Dos modos:

- **Imagen** (`--shot --frames --k --trace`). Toma la foto k de una
  captura con `-DSTOPF`:
  - el frame del oráculo sale de `game_frames.json` (campo `f`);
  - dibuja en Python la OAM que grabó la SNES (`work/oamb_<traza>.trace`):
    los objetos con la VRAM/CGRAM del nivel y Mario con sus fichas
    dinámicas;
  - compara cada píxel opaco contra el bloque 2×2 de la captura (P57).

  Da un veredicto por objeto: `exacto`, `no dibujado` o `distinto`. La
  puerta: Mario y lo que el plan dibujó, exactos; lo demás, no dibujado.
  El plan y el objeto se emparejan por la ranura (`slot`, que `g5l.py
  game` ahora guarda en el plan).
- **Lógica** (`--logic --bin --lst --trace`). Sin captura: corre el
  replay entero en Musashi y compara la OAM absoluta que captura el port
  (`g5l_capture`) con la de la SNES, por objeto y por foto.
  - Solo cuenta las fotos en sincronía, las que tienen Mario igual. En
    las demás, el `SKIP`/`SYNC` del replay hace que el port repita la foto
    anterior.
  - Si un objeto no coincide, la imagen se dibuja desde **la OAM del
    port**. Así la puerta de la imagen mide solo el dibujo, y la
    diferencia de lógica queda anotada aparte.
- `--selftest`: una captura sintética da 0; movida 1 px, falla; un objeto
  dibujado fuera del plan, falla.

Dos trampas que salieron al armarla (P127):

- la x/y de la ranura que captura el port es **posterior** al movimiento
  del frame, y la OAM es **anterior** (SMW dibuja y después mueve). Hay
  que comparar la OAM absoluta;
- el mapa de una variante de la tabla dice su **familia** de colores, no
  su tipo. Todas las formas del Koopa `$BD`, de la caja `$B9` y de `$02`
  ya estaban en el banco G3 y usan los mapas del Rex. El contador de
  `g5l.py game` se llama ahora `familia_XX`.

## 2. La puerta de la imagen (WinUAE cycle-exact, `-DSTOPF`)

Fotos en sincronía elegidas solas (`work/g9/pick.py`): una por tipo, y
con bandas cuando hay. Builds con todos los tipos y un objeto por foto
(`work/g9/`).

| replay, foto | objeto | bandas | píxeles | distintos | Mario |
|---|---|---|---:|---:|---|
| yi1 169 | `$02` | no | 196 | **0** | exacto (238) |
| yi1 112 | Koopa `$BD` | sí | 179 | **0** | exacto (209) |
| yi1 5173 | caja `$B9` | no | 255 | **0** | exacto (309) |
| yi1 5932 | piraña `$4F` | sí | 236 | **0** | exacto (332) |
| yi1 1635 | Rex `$AB` | sí | 421 | **0** | exacto (359) |
| chuck 2756 | cinta `$7B` | no | 186 | **0** | exacto (238) |
| chuck 2451 | Chuck `$95` | sí | 495 | **0** | exacto (238) |
| chuck 2460 | Chuck `$95` | no | 478 | **0** | exacto (197) |
| chuck 1847 | caparazón `$05` | no | 203 | **0** | exacto (238) |
| stress_piranha 1705 | piraña `$4F` | no | 232 | **0** contra la OAM del port | exacto (207) |

- En cada foto, los demás objetos visibles salen como `no dibujado`,
  como pide la regla de un objeto por foto: el Rex al borde, el Chuck
  bajo la cinta.
- **stress_piranha 1705:** contra la SNES, la piraña sale con 138 px
  distintos. Corrida una fila abajo, coincide entera. El modo lógica
  confirma que en esa foto la OAM del port tiene la piraña 1 px más abajo
  (`corrida_+0_+1`). El dibujo es exacto; lo que difiere es la lógica.
- Los 12 px del poste de la meta en chuck 2460 (G4-B §6) quedan fuera de
  las zonas de sprite, como se esperaba.

## 3. La lógica: OAM del port contra la SNES

`--logic` sobre 4 replays. Objetos con la OAM igual en las fotos en
sincronía:

| replay | Rex | piraña | Chuck | cinta | Koopa | caja, `$02`, caparazón | Mario |
|---|---:|---:|---:|---:|---:|---:|---:|
| yi1 | **69,9 %** | 100 % | — | — | 100 % | 100 % | 99,0 % |
| stress_piranha | **83,9 %** | **73,7 %** | — | — | 96,3 % | 100 % | 96,0 % |
| chuck | 99,7 % | 100 % | **91,2 %** | **90,6 %** | 96,3 % | 100 % | 95,5 % |
| hills2 | 99,8 % | 100 % | — | — | 96,3 % | 100 % | 100 % |

Las diferencias no están repartidas. Son pocas instancias que se desvían
una vez y siguen corridas hasta salir de pantalla:

| replay | objeto (ranura) | fotos | frame del oráculo al empezar | forma |
|---|---|---|---:|---|
| yi1 | Rex (6) | 2778-3132 (355) | 7923 | x −2 fija |
| yi1 | Rex (7) | 2456-2888 (433) | 7601 | x −1 / otra pose |
| stress_piranha | piraña (5) | 1353-1505, 1570-1814 | — | y ±1 / otra pose |
| stress_piranha | Rex (6) | 1353-1694 | — | x +1 / otra pose |
| chuck | Chuck (4) y cinta (3) | 2840-2882 (43) | — | otra pose / y −1 |
| todos | Koopa (7) | 6 fotos al empezar | — | y −1 |

- yi1 tiene 1.418 fotos fuera de sincronía de 6.313 (por `SKIP`/`SYNC`).
- La lógica de los sprites se verificó contra snesorc por tarjeta (P1-P6),
  pero en el replay de lazo cerrado una instancia puede separarse. Desde
  ahí se ve corrida 1-2 px o con otra pose, y el criterio 1:1 lo cuenta
  como diferencia visible.
- No es del dibujo: con la OAM del port, la imagen es exacta (§2).

## 4. Cierre

- Puertas:
  - el autotest;
  - 10 capturas con 0 px en los objetos dibujados y en Mario (la piraña
    de 1705, contra la OAM del port);
  - todo objeto no dibujado, con su motivo.

  Regresión y lint en verde (§5 del commit).
- Herramienta nueva en el flujo: `sprshot_cmp.py --logic` no necesita
  WinUAE y cubre el replay entero.
- **Sigue L-DER** (`instrucciones-l-der.md`): encontrar por qué esas
  instancias se separan de la SNES (primer frame distinto, campo de RAM)
  y corregirlo en el 68000.
