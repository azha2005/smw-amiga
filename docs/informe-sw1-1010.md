# SW1 — barrida de la pantalla entera contra la SNES, una foto por segundo

2026-10-10. Pedido del usuario: comparar una foto por segundo del port
con la de la SNES para encontrar diferencias que las barridas anteriores
no veían. Rama `g2t-b2bis` (= master tras el merge).

## 1. Cómo se mide

Las barridas anteriores comparaban **zonas**: la capa 1 contra el mapa
(`m16diff`, `cmp_ref`), los sprites contra la OAM (G9), el scroll contra
su simulación. Esta compara **la pantalla entera**, píxel a píxel, contra
lo que dibuja la PPU de la SNES en el mismo frame del oráculo.

- **Port:** build de replay `yi1` con `-DHOLDEVERY=50` (`game.s`, SW1).
  - Cada 50 frames del replay (1 s), la lógica se detiene 150 ticks, igual
    que al terminar el replay: la foto se repite.
  - `sw_hold` (firma `SW1HOLD!`) dice qué foto k se ve.
  - `tools/sweep_cmp.py capture` lee la firma desde la memoria de WinUAE
    (cycle-exact, A501, arranque BM1, bajo el candado). Captura con
    `PrintWindow` y vuelve a leer la firma: solo guarda si sigue siendo
    la misma k.
- **SNES:** `snesorc --shots` (nuevo en `orc.c`).
  - Después del NMI de cada frame pedido, la PPU de snesrev dibuja la
    pantalla.
  - Se guardan y restauran la RAM, la PPU y el DMA, porque el IRQ de la
    barra de estado corre en C.
  - El oráculo sale **idéntico** con y sin `--shots`: 6312/6312 frames
    iguales a la grabación.
- **Correspondencia:** k → frame del oráculo con `frames_yi1.json`
  (`g5l.py game`, campo `f`). Depende solo de las operaciones del replay,
  no del build.
- **Comparación:**
  - colores a 12 bits con la conversión del port (`snes_to_amiga12`) y la
    captura muestreada al centro del píxel (P57);
  - la alineación vertical se mide, no se supone: **fila Amiga = fila
    SNES − 1** (12.200 px distintos contra ≥ 73.649 con las demás);
  - la barra de estado (filas 0-39) se cuenta aparte, porque no está
    portada (D11);
  - las diferencias se agrupan en cajas;
  - salidas en `work/sw1/yi1/`: `cmp/k*.png` (SNES | Amiga |
    diferencia), `sweep.json`, `cajas1.png` y `cajas2.png` (recortes de
    cada caja).

Build: todos los tipos de objeto y 2 por foto (los defectos del
2026-10-10). Chip 506.904 B (margen 17.384 B), 0 violaciones.

## 2. Resultado

**126 fotos (k = 49 … 6299, una por segundo):**

- **Barra de estado:** ninguna exacta (no está portada).
- **Fuera de la barra:** 50 exactas.
  - En sincronía con la SNES (Mario igual, lista de G9): 98 fotos, 44
    exactas.
  - Fuera de sincronía (`SKIP`/`SYNC` del replay): 28 fotos, 6 exactas.

En las fotos en sincronía, el scroll, la capa 1, el fondo y Mario
coinciden, salvo los detalles del punto 11 y los postes del punto 3. Lo que falla son **objetos que nadie dibuja** y algunos
detalles. Ordenado por cuánto se ve:

| # | diferencia | fotos | qué es | ya se sabía |
|---|---|---:|---|---|
| 1 | **barra de estado** (MARIO, vidas, tiempo, monedas, puntos, reserva) | 126 | no portada (D11, etapa 10) | sí |
| 2 | **la piraña se ve delante de la tubería** | 11 | en la SNES está detrás de la capa 1 (dentro de la tubería no se ve; al salir, solo la mitad de arriba). En el port, entera y delante: falta la prioridad sprite/capa 1 | **no** |
| 3 | **los postes del punto medio no se ven** | 9 | son tiles de la capa 1 (no están en la OAM). La cinta sí se ve. Como el mapa de la capa 1 da 100 % (`m16diff`), la sospecha es la indirección (§11): el color o el índice por línea. Sin confirmar | **no** |
| 4 | **los bloques giratorios no se rompen** | 6 | en la SNES Mario los rompe (desaparecen y vuelan 4 trozos de 8×8); en el port siguen enteros, incluso en fotos en sincronía (6049-6249) | **no** |
| 5 | **los puntos ("200", "400", "1000")** no se dibujan | 12 | sprites de puntos, sin portar | **no** (no estaba en la lista) |
| 6 | **el bloque `?` volador `$83`** (con alas, y marrón después del golpe) y el champiñón que sale | 6 | sin portar a G5L | parcial (D3 lo lista; G4-B no lo incluye) |
| 7 | **Rex sin dibujar** | 12 | la regla de 2 objetos por foto (el punto 3): el segundo Rex en las mismas filas | sí |
| 8 | **Banzai Bill** | 9 | cola de bobs (G7) | sí |
| 9 | **la moneda de Yoshi**, otro tono | 12 | la animación de paleta (P22) en otra fase o sin animar: ≈ 100 px por moneda | **no** |
| 10 | las estrellas del pisotón | 1 | sprites de efecto, sin portar | **no** |
| 11 | detalles de 1-6 px | ~15 | la esquina de una cornisa (4 px, k 1799-2099), un píxel en la fila 185 que acompaña a la cámara, el pie del Koopa sobre la pendiente (5 px) | **no** |
| 12 | fuera de sincronía: cámara corrida (k 2449) y Mario que no entra en la tubería (k 6299) | 2 | el replay salta lo no portado y resincroniza; la imagen de ese momento no es la de la SNES | en parte (P58) |

Los puntos 2, 3, 4, 5, 9, 10 y 11 no aparecían en ninguna medida
anterior. Las métricas de zonas daban 100 % porque cada una mira solo su
capa o sus tipos de sprite.

## 3. Lo que esta barrida no ve

- **Fotos quietas.** Muestra el contenido de la foto, no el movimiento:
  los tirones, las fotos salteadas (D1) y el desgarro no salen aquí. Para
  eso siguen `-DVBTRACE` y `d1_count`.
- **1 de cada 50 frames.** Algo que dura menos de 1 s puede no salir.
  `-DHOLDEVERY=10` da 5 fotos por segundo, con la misma herramienta
  (≈ 4× más tiempo de WinUAE).
- **Solo el replay `yi1`.** Los otros replays (chuck, hills2,
  stress_piranha) usan guiones de snesorc: `sweep_cmp.py snes --script
  tools/snesorc/<x>.orc` sin `--replay`.

## 4. Cómo repetirla

```
GDEFS="-DREPLAY -DHOLDEVERY=50" OUT=work/sw1/yi1 sh tools/bm_build.sh
python tools/sweep_cmp.py capture --dir work/sw1/yi1          # ~9 min de WinUAE
python tools/sweep_cmp.py snes --dir work/sw1/yi1 --frames work/g9/frames_yi1.json \
    --script tools/snesorc/boot_yi1.orc --replay work/oracle_yi1.txt --seg 2
python tools/sweep_cmp.py cmp --dir work/sw1/yi1
```

`work/snesorc` tiene que estar recompilado con el `orc.c` nuevo
(`snesorc_setup.sh`, o el `gcc` de su última línea en la PC, P82).
