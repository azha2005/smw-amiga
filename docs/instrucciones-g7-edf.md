# G7-3c (EDF) — portar el paso 3b del productor al 68000

2026-10-11. Tarjeta parte de G7-3c (`docs/instrucciones-g7-3c.md`). La
especificación es `tools/g7_fast.py`: `edf_assign`, `edf_row`,
`reach_early`, `reach_exact` (y `required`, `palette`, `prefix_of` de
`tools/g7_color_plan.py`, `timeline` de `tools/g2t_ref.py`). **El 68000
tiene que tomar exactamente las mismas decisiones, palabra a palabra.** No
se toca la especificación.

## Dónde va

- Todo el código en `player/g7edf.s` (incluido desde `player/g7fast.s`,
  mismo módulo, `a6` = `g7f_w`). Hay un esbozo `g7f_edf` que devuelve -1.
- **No editar** `player/g7fast.s` ni `player/g7win.s` (el paso 3, ventana,
  se porta en paralelo). Si hace falta algo de `g7fast.s`, pedirlo en el
  informe final.
- Variables propias en `W_EDF` .. `W_EDF+2047` (equ relativas: `E_xxx equ
  W_EDF+n`). Se pueden usar además `W_TRY`, `W_OUT2`, `W_JOB` (64 × 8 b) y
  las salidas de `g7f_scan` (`W_POS`, `W_BEF`, `W_FLG`, `W_SLK`, `W_PLEN`,
  `W_NB`, `W_OPEN`, `W_TEND`, `W_FIRST`).
- No tocar `W_OV`, `W_CT`, `W_EM`, `W_ORG`, `W_NO`, `W_TAIL`, `W_EVT`,
  `W_IDX`, `W_WANT`, `W_CL`.

## Qué llega a `g7f_edf` (lo prepara `g7f_left`)

| campo | contenido |
|---|---|
| `W_ORG`/`W_NO` | palabras originales del segmento (longs, sin el salto `$84` ni su cola) = `words` de `edf_assign` |
| `W_EVT`/`W_NEV` | colores PF1 de `W_ORG` en orden de palabra: pos.w (`$8000` = prefijo), r.w, valor.w (& `$fff`) |
| `W_IDX` | 256 b: `idx` de la especificación (índice del terreno en cada x, **también bajo los efectos**) |
| `W_WANT` | 256 w: `required(words, row, idx, overlay)` (-1 transparente) |
| `W_OV`, `W_CT` | ranura de color por x (0 = sin efecto) y color de cada ranura (1..15) |
| `W_CL`/`W_NCL` | grupos pendientes (`left`): 8 b cada uno: ranura.b, estado.b (**libre, puede venir con cualquier valor**), x0.w, x1.w (primer y último píxel de la ranura en el grupo), r.w. Orden: por color ascendente, dentro de cada color por x |
| `W_CLM` | `claimed` de `fast_row` (bits 1..7) |
| `W_OUT` | índice asignado por `fast_row` **solo en los píxeles de efecto ya resueltos**; en el resto, basura |
| `W_END` | `end_of(nb de la fila siguiente)` (nunca `$7fff` aquí: `g7f_left` ya rechazó) |
| `W_ROW` | fila (nunca `G7F_WRAP` aquí) |

`out` de la especificación = `W_IDX[x]` en todo x salvo los píxeles de
efecto resueltos por `fast_row` (= `W_OUT[x]`). Los píxeles de los grupos
pendientes valen `W_IDX[x]` (el terreno de debajo): eso crea trabajos en
`edf_row` para ese índice, **igual que en la especificación; reproducirlo**.

Rutinas que se pueden llamar: `g7f_scan` (a0 palabras, d0.w cantidad;
destruye d0-d7/a0-a5), `g7f_adv` (d0), `g7f_xh` (d1 = h → d0),
`g7f_waitx` (d0 = t, d1 = palabra 1 → d0; destruye d0-d2), `g7f_uses`
(d3 x0, d4 x1 → `W_UIN`, `W_UANY`, `W_ULO[r]` = último uso < x0 o -1,
`W_UHI[r]` = primer uso > x1 o 256; terreno = `W_OV` 0 y `W_IDX` ≠ 0).

## Salida

`d0.l = 0`: `W_SEG` = lista nueva (`head + body`), `W_NW` = su largo,
`W_OUT[x]` = índice asignado en cada píxel de efecto. `g7f_emit` la compara
con `W_ORG`, la escribe con la cola y encola los píxeles. Cualquier otro
`d0`: sin plan (la foto se rechaza).

## Puntos finos de la especificación

- Orden de colores: el de la primera aparición en `left` ordenado por x0
  (= el color cuyo grupo pendiente tiene el x0 más chico va primero).
- `assign(all)`: x0 = mínimo, x1 = máximo de los grupos del color; píxeles
  = los de la ranura. Si falla y hay más de un grupo, `assign` de cada grupo
  en orden; las asignaciones hechas persisten aunque uno falle (y entonces
  sin plan).
- Candidatos: r 1..7 no reclamado y sin uso del terreno en [x0, x1] (un
  índice **sin ningún uso sí vale**, a diferencia de la ventana). Orden por
  ancho `hi - lo` descendente (lo = último uso < x0 o -1, hi = primer uso >
  x1 o 256), a igualdad r ascendente.
- `edf_row`: trabajos por r (el b de dos trabajos nunca coincide: el orden
  `(b, a)` es por b). `j is cand[0]` = el trabajo pendiente de b mínimo.
  `fixed` = eventos del cuerpo de `W_ORG` con x ≥ 0 y registro fuera de
  `$182..$18E` y distinto de `$1FE`. El t inicial usa el `nb` de
  `prefix_of` (`W_NB` de `g7f_scan` sobre `W_ORG`).
- `reach_early`/`reach_exact`: h de `$20` a `$CE` de dos en dos; NOP =
  `$01FE0000`; WAIT = `((fila+$2C)&255)<<8 | h | 1`, `$FFFE`.
- Comprobación final: ninguna x de la lista nueva > `W_END` (correr
  `g7f_scan` sobre ella) y largo + 3 ≤ 64.
- 68000: el desplazamiento de `(d8,An,Xn)` es de 8 bits con signo:
  `W_xxx(a6,d0.w)` solo vale para `W_OV`; para el resto, `lea` antes.
  `(An,Dn.w)` suma con signo (P40). La herramienta Bash rompe las barras
  invertidas en los heredoc (P56): escribir ficheros con la herramienta de
  escritura o con Python.

## Compilar y verificar

```sh
export PATH="/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python PYTHONIOENCODING=utf-8
# los builds comparten work/cc: SIEMPRE con el candado
GDEFS="-DREPLAY -DG7_BOBS -DG7F_NOWIN" OUT=work/g7edf/b sh work/buildlock.sh sh tools/bm_build.sh
python tools/g7f_verify.py --bin work/g7edf/b/game.bin --lst work/g7edf/b/game.lst \
    --layers fast,edf --check-clean [--from-k N --to-k M]
```

`-DG7F_NOWIN` deja fuera la ventana en el 68000 y `--layers fast,edf` la
deja fuera de la especificación: así el EDF se cruza solo. `g7f_verify`
exige el mismo segmento palabra a palabra, los mismos índices PF1 y la
misma fila de rechazo. Fotos con EDF en YI1: ver `work/g7fast/yi1-v2.log`
o correr la especificación (`python tools/g7_fast.py --bin
work/g7f/b2/game.bin --lst work/g7f/b2/game.lst --no-hidden`).

Trazas (después de compilar YI1; mismo candado, `NOCC=1`):

```sh
for t in pw_bloques chuck_kill spin_kill stress_piranha; do
  GDEFS="-DREPLAY -DG7_BOBS -DG7F_NOWIN" XCDEFS=-DLSS_SNESORC ORACLE=work/oracle_$t.bin \
  REPLAY=work/sws/${t}_replay.bin OUT=work/g7edf/t_$t NOCC=1 sh work/buildlock.sh sh tools/bm_build.sh
done
```

**Hecho** = `G7F: OK` con `--layers fast,edf --check-clean` en YI1 completo
y en las cuatro trazas. Informar media/p99/máximo de ciclos y las fotos
rechazadas antes y después. No hacer commit, no activar G7_BOBS por
defecto, no borrar nada de `work/`, worktrees ni `.claude/`.
