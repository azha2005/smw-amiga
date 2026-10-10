# SW-Q — el bloque `?` volador `$83` y los power-ups, visibles

2026-10-10. Sale de SW1 (`informe-sw1-1010.md`, punto 6). **Mediana**: la
lógica ya existe; falta el dibujo por G5L.

## Por qué

En 6 fotos (k 1199-1449) no se ven:

- el bloque `?` volador con alas (`$83`) ni, una vez golpeado, el bloque
  marrón que sigue volando;
- el champiñón que sale de él (k 1299).

La lógica ya está en el port:

- `FlyingBlock` (`msprite.c:960`, el `$83`);
- los power-ups `$74`-`$78` (`spr_powerup.c`).

Lo que falta es que G5L los dibuje. `G5L_OTHER = (0x4F, 0x95, 0xBD,
0x05, 0xB9, 0x7B, 0x02)` no los incluye, y la tabla G5L3 no tiene sus
formas.

## Pasos

1. **Las poses.** Con las trazas `oamb` (`work/oamb_*.trace`), listar las
   poses de `$83` (con alas, con golpe) y de `$74`-`$78` (seta, flor,
   estrella, 1-UP, pluma; en YI1 importan la seta, la flor, la estrella
   y el 1-UP). Traza nueva si alguna no aparece: `pw_seta`, `pw_flor`,
   `pw_estrella`, `pw_1up` y `pw_bloques` ya existen como guiones.
2. **El banco.** Si faltan poses en el banco G3 (`work/g3/bank`):
   regenerarlo con ellas (`sprgfx_*`, G3a). P108: el banco es inmutable,
   así que va una versión nueva, auditada (`g2_bank_audit.py`).
3. **La tabla:**
   - agregar `$83` y `$74`-`$78` a `G5L_OTHER` (`tools/g5l.py`), con su
     familia de colores (P127);
   - `G5L_TYPES=all` ya los incluye;
   - medir el tamaño de la tabla y la DMA limpia (hoy 82 KB slow, 30,9 KB
     chip);
   - **P126:** el replay con Exec ya no entra; el margen real del vivo
     (BM1) es 5.856 B y el del replay BM1, 17.384 B. Si no entra, el
     informe lo dice; no recortar a ciegas.
4. **La regla de la foto:** los power-ups y el bloque compiten con los
   enemigos en la regla de 2 por foto (el punto 3, decisión del
   usuario). Hasta que se decida, el orden de siempre (de arriba abajo).
5. **La captura** (`g5l_capture`): el mapa de bits de tipos ya filtra
   por la tabla. Comprobar que las ranuras de power-up (estado
   `$14C8` = 8 o 1) entren.

## Puertas

- `g5l.py trace` con 0 errores en las trazas de `pw_*` y yi1 (`--types
  all`).
- `g5l.py game` exacto en yi1 y en un replay de power-ups.
- `sprshot_cmp.py` (G9): una captura por pose nueva, 0 px.
- SW1 de yi1: k 1199-1449, el bloque y el champiñón exactos (los puntos
  son de SW-S).
- `memmap`: margen ≥ 0 en el vivo y en el replay BM1.
- A/B BENCH de D1.
- Regresión completa y lint.

## Trampas

- P99, P100: gráficos de sprites, columnas y el bit 8.
- P108: el banco es inmutable.
- P126: la chip retenida por Exec en el replay.
- P127: la familia de mapas no es el tipo.
