# G5L-N — clave normalizada y máscaras compartidas (tabla G5L2)

2026-10-10. Rama `g2t-b2bis`. **Integrado en la rama** (por defecto: es la
tabla que usa G5L). Tarjeta: `instrucciones-g5l-n.md`; origen:
`informe-g4a-1010.md` §3 y §6.

## 1. Qué cambió

- `tools/g5l.py`: formato `G5L2`. La clave de la forma se normaliza al
  mínimo dx/dy (s8) de las fichas, sin reordenarlas (`norm_key`). El
  directorio guarda una forma por clave, y el origen de la variante queda
  relativo al mínimo. Al deduplicar se comprueba que la traslación dé la
  misma imagen (con colores, no con los índices del banco) y el mismo
  origen; si no, aborta. Las máscaras de `g5l_patch` van una vez por forma
  y por color: el byte de relleno del grupo es el número de máscara, y
  donde estaban las máscaras queda un `.l` al bloque.
- `player/g5l.s`: `g5l_choose` hace una pasada de mínimos y los suma a
  sx/sy, así que la clave y `x0`/`r0` salen sin más cambios. `g5l_patch`
  calcula la dirección de la máscara desde el bloque. La caché del plan
  no cambia: su clave es `VLIST`, `R0`, `MSH`, `COL` y Mario, y dos
  traslaciones dan el mismo plan.
- `tools/gvtab_watch.py`: la firma `G5L2`.

## 2. Puertas

| puerta | resultado |
|---|---|
| tabla | 128.724 → **44.810 B**; 48 → 22 formas (26 traslaciones); `g5l_clean.dma` idéntico byte a byte (16.656 B) |
| `g5l.py trace` `yi1`/`normal`/`spin_kill` | contadores **idénticos** al control |
| `g5l.py trace`, grabaciones nuevas (trazas del host, solo `$AB`) | `rex_sin_forma`: `hills2` 340 → **0**, `stress_sprites` 96 → 0, `shells` 62 → 2, `stress_back` 62 → 1, `pw_estrella` 37 → 1; 0 errores de color y 0 `sin_plan` en todas |
| `g5l.py game` (replay YI1) | `G5L GAME: OK`; dibujadas 2.043 → 2.044 |
| regresión completa + lint | `RESULTADO: OK` |
| `memmap.py` (vivo, `rg_bm1`) | slow libre **61.288 → 145.144 B**; chip sin cambios; 0 violaciones |

Ciclos (Musashi, replay YI1; el control es la última regresión de HEAD):
`g5l_choose` media 569 → 635 y máx. 2.566 → 3.162 (la pasada de mínimos).
`g5l_patch` máx. 17.790 → 17.992. Total por foto: media 9.893 → 9.677 y
máx. 90.452 → 90.964 (+0,6 %).

## 3. A/B WinUAE (cycle-exact, BENCH + ADRTRAP, en serie con el candado)

| replay | control | G5L-N |
|---|---|---|
| normal | 14 fotos perdidas (0,22 %), racha 1, peor 40,0 % | **9** (0,14 %), racha 1, 40,5 % |
| back | 392 (9,50 %), racha 5, peor 76,1 % | **373** (9,04 %), racha 4, 75,8 % |
| sprites | 98 (5,12 %), racha 3, peor 73,2 % | **88** (4,60 %), racha 3, 73,3 % |

Ningún lado empeora. El control repite sus números anteriores (back 387
y 392 en tandas distintas), así que la mejora puede ser en parte ruido. No
se la atribuye a la tarjeta. Capturas en `work/g5ln/{ctrl,cand}_*.png`.

## 4. Evidencia visual

Replay de `hills2` (`ORACLE=work/oracle_hills2.bin`). En 260 fotos del
replay de la Amiga, la tabla nueva dibuja un Rex que la clave exacta no
encontraba (primeras: 1702-1741). Foto 1720, `-DSTOPF=1720`, WinUAE
cycle-exact:

- control (tabla vieja): `work/g5ln/h2o1720/shot.png`, sin Rex;
- candidato: `work/g5ln/h2c1720/shot.png`;
- `g5l.py shot`: la captura del candidato es el control más los píxeles
  que planea la referencia, con **0 de 327.680 píxeles distintos** (219
  píxeles del Rex aplastado en la pendiente, `x0` 13, `r0` 128). La hoja
  está en `work/g5ln/h2c1720/check.png` y el recorte en
  `work/g5ln/h2_rex.png`, ambos revisados.

La referencia toma los colores del Rex de la OAM de la SNES, comprobada
por `g5l.py trace` (0 errores de color).

## 5. Lo que queda

- 3 formas del Rex sin forma en el banco ni como traslación (`shells` 2,
  `stress_back` 1, `pw_estrella` 1): agregarlas al banco G3 es otra
  tarjeta.
- G5L sigue dibujando **un** Rex por foto, el más alto (`plan_frame`).
  Los demás enemigos son G4.
- La slow que se libera (≈ 82 KB) deja lugar para la tabla de G4 (formato
  `G5L2`, ≈ 83 KB con 4 mapas para todos; `informe-g4a-1010.md` §5) o
  para parte de las tablas de CPU que hoy están en chip (C2/C4).
