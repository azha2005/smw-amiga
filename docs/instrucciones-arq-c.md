# ARQ-C — dieta de copper (instrucciones paso a paso)

Escrito el 2026-10-11, al cerrar P1-V (`docs/informe-arq-0-1011.md` §5).

## Por qué

Lo que gana P1 (5 planos) sale de una sola cosa: 17 palabras de DMA por
línea que el plano 6 deja de leer y vuelven a la CPU y al blitter. Medido en
BENCH: 8 MOVE nulos por línea (16 palabras) se comen casi toda esa ganancia
(sonda `-DARQ_CUTN=8`). Por lo tanto **cada palabra de copper por línea
cuesta lo mismo que una del plano 6**.

El copper fijo de cada línea son 24 palabras, y la imagen no depende de
casi ninguna:

| qué | palabras por línea | hace falta |
|---|---:|---|
| 2 WAIT del borrado (`build_copper`, offsets 0 y 4) | 4 | el segundo es un relleno de la etapa 6 (`a1950f6`: el primer lugar era el WAIT que cruzaba la 255); hoy, en las líneas normales, son iguales |
| 7 MOVE de la capa 1 en el borrado (offsets 8-35) | 14 | 2,55 en promedio, criterio conservador (abajo); 2,08 si los registros terminan la línea con el color ideal |
| salto al segmento siguiente (`COP2LCH`, `COP2LCL`, `COPJMP2`) | 6 | `COP2LCH` solo si cambia el banco de 64 KB |

Ahorro estimado, sin medir: ~2 + ~5 + ~2 = **~9 palabras por línea, más de
la mitad del plano 6**, sin cambiar un píxel.

## Reglas

- La imagen no cambia: `regress.py` tiene que dar igual que hoy, y el vivo
  por defecto mantiene su comportamiento. El SHA del binario cambia (es
  código nuevo): anotarlo.
- Cada paso se mide aparte con BENCH en los 5 tramos de ARQ-0
  (`tools/arq0/build_base.sh` como modelo, `shots_par.sh` en paralelo,
  `table.py`) contra `b_*` y `p5_*`.
- Antes de cada commit: lint, `regress.py --baseline tools/baseline_pc.json
  --level --g5l --bm1`, `sws_gate.sh`, `oam68k_gate.sh`, con
  `PATH="/c/msys64/ucrt64/bin:$PATH"` (P82).

## Paso 1 — saltar el WAIT repetido (2 palabras)

1. Listar TODOS los que escriben un salto "al segmento siguiente":
   `build_copper` (`player/scroll.s`), la plantilla de `init_lines` (bytes
   18-31 de cada `linetab`, que copia `build_mid`/`bm_left`/`bm_share`), y
   en `player/g5l.s` `g5l_emit` (sufijos), `g5l_clean` y `.jump`. Buscar
   `#SEG`, `lsl.l #8` con `CL_LINES` y `$0084`.
2. El salto apunta a `segmento + 4` (el segundo WAIT) salvo en el segmento
   cuyo primer WAIT es el de la 255 (`.w255` en `build_copper`: ahí el
   segundo lugar es un MOVE nulo y hay que entrar por el 0). Conviene una
   macro `NEXTSEG` o una tabla de 224 desplazamientos de entrada.
3. El arranque de la lista (cabecera → primer segmento) no pasa por un
   salto: comprobar cómo llega el copper al segmento 0 y dejarlo igual.
4. Comprobar con `copcal`/capturas que el borrado sigue terminando antes de
   x = 0 (P43) y que las cargas caen en la misma x (P42, P110, P111).
5. BENCH en los 5 tramos.

## Paso 2 — `COP2LCH` solo al cambiar de banco (2 palabras)

1. Cada lista (A, B, C) puede cruzar un límite de 64 KB. El primer salto de
   cada frame tiene que escribir `COP2LCH`, porque el registro trae el valor
   de la lista del frame anterior.
2. El salto pasa a ser `COP2LCL` + `COPJMP2`, y `COP2LCH` + los dos donde el
   banco cambia. **G5L busca el salto por `$0084`**: `.jump`, la comprobación
   `cmp.w #$0084,CL_LINES+8(a0)` y el recorrido de tiempos (`g5l.s` ~3611,
   ~3810, ~4200). Cambiar el marcador a `$0086` en todos, y la referencia
   `tools/g5l.py` / `tools/g2t_ref.py` si modelan el salto.
3. BENCH.

## Paso 3 — borrado compacto (≈ 5 palabras netas)

Criterio conservador: el registro r de la línea L necesita MOVE en el
borrado si su color en x = s difiere del de la línea L-1 en x = s, **o** si
la línea L-1 tiene una carga de r con x en (s, s + 255] (una carga diferida
o tarde de `build_mid` puede dejar el registro con otro valor). Medido en
`yi1`: 2,55 MOVE por línea de media, 4,91 de máximo (hoy 7).

1. Diseño: los MOVE necesarios van primero, en los lugares 8, 12, ...; detrás
   un salto corto a `ldoff` (`COP2LCL` + `COPJMP2`, el `COP2LCH` ya es el
   del segmento); lo que queda hasta `ldoff` no se ejecuta. Si hacen falta 6
   o 7, no conviene saltar (el salto cuesta 2 instrucciones): dejar los 7.
2. Hoy `apply_colors` escribe por posición fija (CHG de `tools/mkscroll.py`:
   `L * SEG + 8 + (r - 1) * 4 + 2`) y SW-M también (`D_COIN`, offsets
   `line * SEG + 10 + 4 * reg`). Hay que pasar a (línea, registro) y
   reescribir el borrado de la línea cuando cambie su conjunto. Medir el
   costo de CPU con BENCH (`resto de scroll_frame`).
3. `GV_NB` de G5L (borrado de la línea siguiente, `ldoff`) mide hoy el
   tiempo del borrado en la ranura horizontal: con el borrado compacto es
   menor, y G5L tiene más lugar para los colores del Rex. Revisar que el
   modelo de tiempos de `g5l.s` lea la longitud real y no `ldoff`.
4. `regress.py` cruza los colores de la capa 1 con la referencia: tiene que
   seguir 100 %.
5. BENCH.

## Al terminar

Tabla A/B en el informe de ARQ-0 (o `docs/informe-arq-c-<fecha>.md`), PROXIMO
y ROADMAP §2 al día. Si ARQ-C rinde lo estimado, P1-B (bandas de 5 planos
0-16 + 208-223, invisibles) va después, y luego el contrato del frame (D-C).
