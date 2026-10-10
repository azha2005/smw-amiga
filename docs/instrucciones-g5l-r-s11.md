# G5L-R-S11 — cortar la espiral de la vuelta en `build_mid`

2026-10-10. Nace de M1 (`informe-g5l-r-m1-1010.md`). Optimización ya
autorizada (D1, 50 Hz con colchón); **la imagen no cambia**: lista del
copper exacta byte a byte en los tres replays.

## Por qué

En la vuelta de `stress_back` (frames 2.560-2.598) cada lista se reescribe
con un |Δs| desde su última escritura que crece −12 … −48. Con |Δs| > 16,
86 fotos cuestan 10.386 ticks de media (máx. 25.365 = la peor del
estrés), contra ≈ 1.540 con |Δs| ≤ 16. Foto 2580 en Musashi: con la
secuencia real 134.292 ciclos, 79 líneas reescritas, 339 cargas y 10
copiadas por `bm_share`. Dibujando todas las fotos: 85.096, 39 líneas
reescritas, 191 cargas y 25 copiadas. El DMA de planos multiplica por
≈ 1,6 todo lo que quede.

## Reglas

P123 (recarga de `a2` en `dc_loop`), P40/P50/P51/P71/P72/P74/P110/P111/
P121/P122, contrato de `build_mid`/`bm_left`/`bm_share`. No intercalar
cabeceras entre `build_mid` y `bm_left` (P122). ABI, PIC, R2/R3/R9.
Worktree `wt-g2t-b2bis-1008`, builds en serie, una WinUAE midiendo.

## Partida

Igual que S10 (lint, regresión `--level --g5l --bm1`, control back con
`dc_loop_verify.py` y `g5l.py game`). Además la referencia de la espiral:

```sh
B=work/s10/control_back
python tools/g5l.py game --bin $B/game.bin --lst $B/game.lst \
  --render-list work/m1/pos_back.json --pcprof work/m1/spiral_pc.json \
  --pcframes 2580,2584,2594
# G5L GAME (pcprof): OK; k=2580: 134.292 ciclos de build_mid
```

`work/m1/pos_back.json` sale de `tools/m1_read.py` sobre la build
`-DREPLAY -DBENCH -DADRTRAP -DM1POS` (ver informe M1 §1). Si falta,
regenerarlo antes.

## Fases (cada una con su puerta)

1. **Medir antes de cambiar.** En las fotos 2580/2584/2594, contar por
   línea reescrita: si la línea de `prevlt` tenía `[vl, vu)` cerca de s
   (distancia en px) y cuántos pasos de `.lof/.lob/.hif/.hib` se dieron.
   Resultado: cuántas de las 79 reescrituras serían copiables si `prevlt`
   se escribiera con una validez más ancha o si se buscara desde sus
   punteros lo/hi.
2. **Candidato A — buscar desde `prevlt`:** en `.rw` de `bm_left`, partir
   de lo/hi de la línea de `prevlt` (una foto de distancia) en vez de los
   propios (3+ fotos). Misma salida; menos pasos de búsqueda.
3. **Candidato B — sin `alllines` en |Δs| > 16:** ampliar la ventana de
   LNS (hoy [16k − 16, 16k + 32)) para cubrir |Δs| hasta 48. Medir antes
   el tamaño nuevo de LNS en `yi1_s.dat` y la memoria en vivo (61.288 B de
   slow libres).
4. Cada candidato, por separado: arnés exacto en los tres replays
   (6.313/4.127/1.915), `--render-every 2/3/5`, `--render-list`,
   `dc_loop_verify.py`, `fuzzcall.py` si toca rutinas sueltas.
5. **A/B WinUAE** contra el control en la misma tanda: BENCH back,
   sprites, YI1 y VBTRACE normal. Puerta: menos fotos perdidas en back y
   sprites, ninguna peor en YI1/VBTRACE. Con `-DM1POS`, contar fotos con
   |Δs| > 16 (control M1POS: 86).

## Paradas

Un byte distinto del copper, ABI, Guru o PIC: retirar. BENCH o VBTRACE
peores: retirar y registrar. Tras tres candidatos sin pasar la puerta,
cerrar con números. Informe con el A/B, tamaños, ciclos y la tabla de
|Δs|; cierre ROADMAP §7.
