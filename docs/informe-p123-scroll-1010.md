# P123 corregida y recortes del scroll / FinishOAM retirados — 2026-10-10

Rama `g2t-b2bis`, partida `6797dd0`, sin merge ni push. Implementación
de la sesión indicada por `PROXIMO.md`: primero la corrupción, después
perfil y recortes medidos. **Los recortes se retiraron tras empeorar
BENCH; solo queda la corrección de P123 y las herramientas/pruebas.**
El generador de speedcode y el resto de los núcleos calientes quedan
pendientes; esta sesión llegó a la parada de L2, no cierra el estrés.

## 1. El Guru tiene una causa concreta, corregida

`dc_loop` conservaba `a2 = dc_st` antes de llamar a `columns`. Pero
`columns` declara y efectivamente destruye `a2`. Después, el camino G5L
leía `DC_REND(a2)` sin recuperar el puntero. El índice podía salir de
los píxeles del PF1 y `dc_recp` devolver una dirección dentro del código.
No era un segmento fuera de rango de `g5l_wcache`.

Con esa falsa foto, `g5l_choose` encontraba una ficha con contador cero:
`subq.w #1,d2` lo convertía en `$FFFF` y el `dbf` escribía mucho más allá
de `GV_KEY`, hasta `GV_TAB`. Añadir sondas al asm cambia el layout y
puede ocultarlo. También lo ocultaba el arnés G5L, que suministraba una
foto válida directamente a cada fase en lugar de ejecutar `dc_loop`.

El watchpoint del WinUAE original atrapó la primera escritura, sin
modificar el binario. Evidencia `work/p123/watch.log/.trap/.slow`:

```
binstart = $C04A18; GV_TAB = $C3CE76
escritura en $C3CE76; IR = $14C0 (move.b d0,(a2)+)
PC guardado = B+$32732 (la instrucción siguiente)
escritor = B+$32730, g5l_choose .k, g5l.s:1221
a4 (foto G5L) = $C1D006, dentro de loadstate
d6 (fichas) = 0; d2 = $0001FCB7
```

Corrección: `lea dc_st(pc),a2` antes de obtener `DC_REND` para G5L.
Se recarga el dueño del estado; no se tapa el desbordamiento con un límite.

`tools/dc_loop_verify.py` ejecuta el bucle real hasta `g5l_render`, con
columnas nuevas en ambas direcciones. En el binario anterior, al pedir la
foto 2 en `s=33`, pasaba la foto 0. Con la corrección: **3/3 fotos
correctas**. Prueba conectada a `regress.py --g5l`.

Reconstrucción aislada de `e7234ab`, con ADRTRAP y solo la corrección:
**150 s en WinUAE cycle-exact sin excepción**. Antes, la vigilancia del
índice de `g5l_wcache` no interceptaba el Guru. La secuencia de fotos
observada y las corridas con omisiones periódicas 2/3/5 también pasaban
en serie; eso no probaba que el bucle real fuera correcto.

Herramienta reproducible: `tools/gvtab_watch.py`. Abre su propia instancia,
cruza el PID del pipe y configura el watchpoint de escritura con bus error
mediante el [IPC oficial](https://github.com/tonioni/WinUAE/blob/6000/uaeipc.cpp)
y el [comando memwatch de WinUAE 6.0](https://github.com/tonioni/WinUAE/blob/6000/debug.cpp).
Los volcados de RAM quedan en `work/` (R9).

## 2. Perfil y candidatos retirados

Se amplió `g5l.py game` con `--pcscroll` (columnas, colores, punteros),
`--pcframes` (selección de fotos) y `--render-every N` (omitir fotos en
el arnés). Sin opciones, conserva el recorrido normal.

Perfil de diez fotos de `stress_back`: en el trabajo previo al Rex,
`bm_left` suma 712.440 ciclos, `bm_share` 82.444, `blit_steps` 16.540.
Dominan las decisiones de reconstrucción de líneas. **Musashi no modela
las esperas del DMA**: `bwait` lee un DMACONR falso y no permite descartar
un coste grande de blitter en la Amiga.

`bm_share` copia `lo`, `hi`, `vl/vu` con dos MOVEM y copia juntas las dos
palabras de longitud/pista. Conserva el contenido y reduce el código.
Sobre las 4.127 fotos del estrés, CPU sin DMA:

| `build_mid` | antes | después |
|---|---:|---:|
| media | 9.995,71 | 9.917,70 |
| máximo | 92.078 | 91.758 |
| k=2577 | 90.206 | 89.606 |
| k=2589 | 92.078 | 91.758 |

Fuente: `work/render1010/back_pc.json` / `opt_pc.json`. El máximo baja
**0,35 %**, insuficiente para cerrar el estrés. Las diez fotos perfiladas
bajan; no se alteran los intervalos de validez ni se posponen líneas.

Se probó leer las cotas `a/b` en un registro antes de compararlas.
**Descartado:** el máximo subía a 92.438 y la media a 9.947,05 (frente a
9.917,70 del candidato anterior). El CMP con postincremento ya es barato;
añadir MOVE no compensaba las actualizaciones evitadas.

`finish_oam_write_asm` conserva `bx/by` en dos palabras de la pila y los
usa al salir, evitando releer índices y tablas. **−80 ciclos por llamada**
en las pruebas de 1/2/4/16 fichas (1 ficha: 1.020 → 940; 16: 3.480 →
3.400, Musashi). **20.000 casos PC=68000, cero diferencias**. No se
cambió el orden de fichas, su recorte ni los temporales finales.

La siguiente palanca sigue siendo el generador por línea: el MLD actual
ocupa 46.288 B, aproximadamente 3.409 cargas útiles más centinelas.
El control BENCH back tiene 125.296 B de slow libres según `memmap.py`.
El vivo por defecto con BM1 tiene solo **61.288 B** libres (slow
463.000 B); replay normal 114.136 B (slow 410.152 B). Fuente: `work/regress.log`,
memmap de los builds finales. Hay que calcular el tamaño del código
generado para todos los builds antes de duplicar las cargas.
No se implementó copper→blitter: el perfil de CPU no justifica elegirlo
y falta una medida de espera en cycle-exact.

## 3. Verificación

- Regresión completa final `--baseline tools/baseline_pc.json --level
  --g5l --bm1`: **OK**; test del bucle real incluido. No se cambia la base.
  Los cuatro recortes de métricas de CPU eran del candidato retirado.
- Lista del copper byte a byte, estado de sprites, bandas, restos y ABI:
  **OK en YI1, stress_back y stress_sprites** (6.313 / 4.127 / 1.915 fotos).
- `dc_loop_verify.py`: **OK** en los tres binarios.
- `fuzzcall.py`, FinishOAM: **20.000/20.000 exactos**.
- Memmap final back: chip 483.808 B, slow 398.992 B, **0 violaciones**.
  Binario 391.700 B, idéntico al control corregido. El candidato retirado
  ocupaba 391.668 B; esa reducción no queda en la rama.
- Memmap replay normal 483.808/410.152 B; vivo BM1 499.432/463.000 B
  (chip/slow), ambos con **0 violaciones** en la regresión final.
- Captura cycle-exact del juego final, STOPF=1200:
  `work/render1010/final_gameplay.png`, inspeccionada: Mario, Rex, suelo y
  fondo visibles, sin excepción. Las listas de todos los frames se
  comprueban por separado; esta captura es evidencia visual del juego.

## 4. WinUAE cycle-exact

El control incluye la corrección de P123: las cifras previas del bucle
defectuoso no sirven como un A/B limpio de estos recortes. Todos los
BENCH de esta tanda llevan ADRTRAP, con idénticos flags a ambos lados.

| replay BENCH | control corregido / final | candidato retirado |
|---|---:|---:|
| stress_back | 387/4.126 (9,38 %), racha 5 | 389/4.126 (9,43 %), racha 4 |
| stress_sprites | 98/1.914 (5,12 %), racha 3 | 104/1.914 (5,43 %), racha 3 |
| YI1 normal | 14/6.312 (0,22 %), racha 1 | 13/6.312 (0,21 %), racha 1 |

Fuente: `work/render1010/control_back.png`, `final_sprites.png`, `final_yi1.png`,
`fix_back.png`, `fix_sprites.png`; `game_read.py --auto`. El binario final
back se comparó byte a byte con el control (`cmp`, exacto).
**El candidato empeora el número de fotos en ambos estrés: retirado**, de
acuerdo con la parada de `instrucciones-g5l-r-l2.md`. No se atribuye la
diferencia a una única rutina: se midió el conjunto. El A/B mide también
sus cambios de layout/fase; ahorrar CPU sin DMA no garantiza fluidez.

**VBTRACE normal final: 2 fotos omitidas**, frames 2.758/3.313; igual al
candidato retirado. Fuente `work/render1010/final_vbtrace.log` y
`final_vb/trace.bin`: 7.000 filas, repeticiones 0/2.755/3.310 (la 0 es
inicial). No se confunden las fotos omitidas con esas repeticiones o
con las del final del replay (P107). **D1 normal sigue roja**: el objetivo
es 0, y el mínimo de estrés tampoco se cumple. El dato anterior de L2
(0 omitidas) era del bucle defectuoso.

Costes reales del control, BENCH cycle-exact:

| parte (máximo) | normal | back | sprites |
|---|---:|---:|---:|
| level_frame | 29,2 % | 60,4 % | 57,5 % |
| build_mid | 83,2 % | 180,4 % | 67,6 % |
| mspr_draw | 7,9 % | 10,3 % | 10,5 % |

Los máximos de partes son de fotos distintas y no se suman. En back,
el máximo de build_mid es en s=4.581; el total hasta blitter libre llega
a 329,3 % en otra foto (k=2.571, s=4.655). Esto acota el alcance de los
pequeños recortes CPU: no eliminaban el coste de esas reconstrucciones.

## 5. Alcance pendiente

Speedcode de `build_mid`, medida real de espera del blitter, y recortes
del resto de la lógica caliente (`mario_E2BD`, `spr_tile`, `mc_pxy`, cámara,
`mspr_draw`). Se mantienen 50 Hz y el colchón aceptado; no se decidió
25 Hz, ni se hizo merge/push.
