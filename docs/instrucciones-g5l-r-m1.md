# G5L-R-M1 — medir por qué `build_mid` cuesta ≈ 2,8× en el hardware

2026-10-10. Tarjeta de **medida, sin optimizar**. Nace del cierre de S10
(`informe-g5l-r-s10-1010.md`): el speedcode ahorraba un 6,2 % de CPU en
Musashi y no cabía en el vivo (118 KB contra 61 KB libres). En back, el
máximo de `build_mid` es 180,4 % del frame en WinUAE frente a ≈ 65 % en
Musashi. Antes de elegir otra optimización hay que saber de dónde viene
esa diferencia.

Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama g2t-b2bis.
Sin merge ni push, builds en serie, una sola WinUAE midiendo, R9.

## Hipótesis a separar (no darlas por ciertas)

La lógica corre en la COPER de la línea 272, en el borde. `build_mid`
corre en `dc_loop` (modo usuario), casi siempre durante las líneas
visibles. Ahí compite por el bus con:

1. el DMA de 6 planos lowres (DPF 3+3) en la ventana de fetch `$40-$C0`;
2. el copper, que hace muchos MOVE a mitad de línea;
3. el blitter (columna, bobs), si coincide con la reconstrucción;
4. la slow de la A501, que comparte el bus (P29): código y datos no se
   aceleran por estar fuera de la chip.

## Partida

Igual que S10 §Partida: lint, `regress.py --level --g5l --bm1` y el control
`stress_back` con `dc_loop_verify.py` + `g5l.py game`, todo en verde.
Scripts de build en un `.sh` dentro de `work/m1/`, ejecutados desde Bash.

## Pasos

1. **Pares por foto.** Construir BENCH back (`-DREPLAY -DBENCH -DADRTRAP`)
   y leer con `game_read.py --auto` la s de la peor foto de `build_mid`.
   Buscar esa misma s en `g5l.py game` (Musashi) y dar ciclos CPU contra
   ticks de CIA (1 tick = 1,41 µs ≈ 10 ciclos). Hacer lo mismo con las diez
   fotos del perfil de S10. Resultado: tabla foto → Musashi → WinUAE → ratio.
2. **Dónde corre.** Flag opt-in nuevo `-DM1POS`: guardar VPOSR/VHPOSR al
   entrar y al salir de `build_mid` en un anillo propio de la slow (no en
   el scratch DMA). Leerlo con WinUAE abierta, como hace
   `tools/bm_probe.py --pid` (PID de esta prueba, nunca uno viejo).
   Resultado: histograma de líneas de pantalla durante la reconstrucción.
3. **Variantes de diagnóstico** (solo medida, imagen inválida a propósito,
   nunca por defecto):
   - `-DM1NOBPL`: BPLEN apagado mientras corre `build_mid` (aísla 1);
   - `-DM1BW`: esperar al blitter libre antes de `build_mid` y contar
     esa espera aparte (aísla 3).
   Mismas fotos, mismo binario salvo el flag. Repetir el control en la
   misma tanda si la diferencia es pequeña.
4. **Sin flags, hashes iguales.** Los cinco MD5 normales y el control
   back tienen que quedar idénticos byte a byte (`cmp`). Lint y regresión
   completa antes del commit.

## Entrega

Informe `docs/informe-g5l-r-m1-<fecha>.md` con la tabla de pares, el
histograma de líneas y el reparto (CPU / planos / copper+slow / blitter)
con su fuente. Según el reparto, **proponer** (no implementar) una
tarjeta: mover la reconstrucción al borde o a las líneas sin fetch,
partirla entre frames, reducir accesos por línea o copper→blitter. Cierre
ROADMAP §7.

## Paradas

Un flag que cambie el binario sin flags: retirarlo. Una WinUAE midiendo
a la vez que otra: repetir. Ninguna conclusión desde Musashi solo: no
modela el DMA.
