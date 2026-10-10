# G5L-R-S10 — prototipo acotado de speedcode para la vuelta

2026-10-10. Partir de la corrección de P123, en `g2t-b2bis`, worktree
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Sin merge ni push.
Perfil y parada anterior: `informe-p123-scroll-1010.md` §2/§4.

## Motivación y límites

En diez fotos caras de `stress_back`, `bm_left` suma 712.440 ciclos,
frente a 82.444 de `bm_share`. Los recortes locales de copia y FinishOAM
pasaron los cruces, pero empeoraron BENCH: 387 → 389 fotos; fueron
retirados. Hay que eliminar decisiones repetidas, con una prueba del
coste y del tamaño antes de integrar el generador completo.

El código generado va en slow RAM. El control BENCH back ocupa 398.992 B
de slow (margen 125.296 B); el vivo y el replay normal tienen otro tamaño.
El vivo BM1 final deja solo 61.288 B de slow libres; medir también ese
build al evaluar cualquier expansión de la MLD.
La MLD contiene 3.409 cargas útiles más 448 centinelas. No suponer que
una expansión por carga cabe en todos los builds. No cambiar colores,
rejilla, orden, intervalos de validez, fotos ni frecuencia para ganar.

P123 está corregida: conservar la recarga de `a2` en `dc_loop` y su prueba.
Leer P40/P51/P71/P72/P74/P110/P111/P121/P122 y el contrato de
`build_mid`/`bm_left`. No intercalar una cabecera entre esas dos rutinas
(P122). ABI, alineación, PIC, R2/R3/R9 y presupuestos siguen vigentes.

## Partida y perfil reproducible

Git Bash, con el worktree anterior como directorio actual. Escribir los
comandos de build en un `.sh` dentro de `work/` y ejecutarlo desde Bash;
PowerShell puede truncar un `GDEFS` con varios argumentos al pasar `-c`.

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
ORACLE=work/oracle_stress_back.bin REPLAY=work/stress_back_replay.bin \
  GDEFS='-DREPLAY' OUT=work/s10/control_back sh tools/game_build.sh
python tools/dc_loop_verify.py --bin work/s10/control_back/game.bin --lst work/s10/control_back/game.lst
python tools/g5l.py game --bin work/s10/control_back/game.bin --lst work/s10/control_back/game.lst \
  --pcprof work/s10/control_pc.json --pcscroll \
  --pcframes 498,2567,2571,2575,2577,2580,2582,2589,3612,3785
```

Esperado: lint/regresión `RESULTADO: OK`, `DC LOOP: OK`, `G5L GAME: OK`.
La media/máximo CPU de `build_mid` del control: 9.995,71 / 92.078 ciclos.
El perfil conserva el recorrido completo; solo limita el paso a paso por
PC a esas fotos. Musashi no mide la espera del blitter.

## Pasos y puertas

1. **Prototipo offline antes de modificar el juego.** En `mkscroll.py`,
   generar un cuerpo ejecutable por línea o por tramo, usando constantes
   de la MLD. Hacer explícitos WAIT inicial, rellenos, codo de 256 px,
   cargas tarde, cotas y terminación. Evaluar un corte por RTS parcheado:
   restaurar siempre la instrucción original, incluso si se rehace la
   línea con otra base. El generador y el test se versionan; sus datos y
   código derivados del nivel quedan en `work/`.
2. **Puerta de coste/tamaño.** Ejecutar en Musashi los mismos rangos y
   bases del perfil. Comparar bytes de salida y estado final con el asm
   actual; incluir ventanas vacías, MIDMAX, cambios de sentido y casos
   tarde/codo. Contar bytes reales ensamblados, tablas, alineación y
   reservas en normal/back/sprites/vivo. No integrar un prototipo que no
   ahorre en las fotos caras o que exceda la memoria. Si no cabe entero,
   medir una selección de líneas o compartir cuerpos; no adivinar ahorro.
3. **Integración opt-in**, solo tras la puerta anterior: `player/scroll.s`
   y `tools/game_build.sh`, sin mover los datos small-data fuera de P36.
   Usar punteros calculados/PIC si el código queda lejos (P74/P102).
   Comparar el control sin flag byte a byte, `piccheck.py` y `memmap.py`.
4. **Juego completo.** Construir normal, back y sprites con el candidato.
   Para cada binario, ejecutar `dc_loop_verify.py` y `g5l.py game`:
   lista exacta, ABI, bandas, restos y buffers exactos en 6.313 / 4.127 /
   1.915 fotos. Repetir back con `--render-every 2`, `3`, `5`; eso ejercita
   cachés con fotos omitidas, sin sustituir la prueba del bucle real.
5. **WinUAE A/B en serie**, ambos lados con P123 corregida. Construir
   BENCH con `GDEFS='-DREPLAY -DBENCH -DADRTRAP'`, normal/back/sprites;
   medir con el candado y `game_read.py --auto`. Tiempos de espera usados:
   200/150/100 s respectivamente. Ejemplo PowerShell:

   ```powershell
   & C:/Users/JC/Downloads/sma/winuae_lock.ps1 ./tools/shot.ps1 -Exact -Adf work/s10/candidate_back/game.adf -Out work/s10/candidate_back.png -Wait 150
   python tools/game_read.py --shot work/s10/candidate_back.png --auto
   ```

   Para VBTRACE normal: construir `GDEFS='-DREPLAY -DVBTRACE'` y usar un
   wrapper `.ps1` bajo el mismo candado que ejecute:
   `python tools/vbtrace.py work/s10/candidate_vb/game.adf work/s10/candidate_vb/trace.bin 190`.
   En wrappers que llaman `shot.ps1`, inicializar `$global:LASTEXITCODE=0`
   antes de la llamada (una salida correcta puede dejarlo nulo).
6. Solo activar por defecto si pasa la semántica, memoria y el A/B real.
   Lint + regresión completa antes del commit. Una captura de juego,
   inspeccionada, además de pantallas de números. Informe con los dos
   lados del A/B y los datos de tamaño/ciclos; cierre ROADMAP §7.

## Paradas

Un byte distinto del copper, ABI roto, Guru, PIC inválido o memoria fuera
de presupuesto: retirar el candidato. BENCH o VBTRACE peores: parar,
retirarlo y registrar el resultado. Si una diferencia pequeña exige
resolver variación de la medida, repetir control/candidato en esa tanda
antes de atribuir una mejora. Tras tres intentos distintos sin pasar la
puerta, cerrar con números y una nueva tarjeta de medida; no abrir otra
optimización a ciegas. D1 sigue siendo 0 fotos en normal y el umbral de
estrés de ROADMAP §2, con 50 Hz y el colchón ya aceptado.
