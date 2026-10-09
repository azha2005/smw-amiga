# G5L-R-V — cerrar teclado real y defectos

2026-10-09. Implementación en `a728ddc`, informe
`informe-g5l-r-vivo-1009.md`. Falta una puerta externa antes del defecto:
el helper de Computer Use no tiene conexión nativa. No repetir código
de reinicio que ya pasa ni introducir una cuarta lista.

## Entorno y partida verde

Trabajar en `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama g2t-b2bis.
Sin merge/push; compilación serial y una WinUAE midiendo; R9.

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l
# RESULTADO: OK; incluye G5L GAME en 6313 fotos, memmap replay/vivo y Z1.
CDEFS='-DNOOAM -DSPR_OAM' GDEFS='-DG5L -DCUSHION' SPR_BANK=work/g3/bank OUT=work/g5l/liveclose sh tools/game_build.sh
python tools/restart_verify.py --dir work/g5l/liveclose
# CUSHION vivo: tres listas, diagnostico/retorno OK; 188/188 y 190/190.
python tools/memmap.py work/g5l/liveclose/game.lst --data work/yi1_s_g5.dat
# 0 violaciones; chip 495336, slow 437896 B (sin reservas del SO).
```

## Pasos

1. Comprobar que Computer Use puede listar la ventana propia de WinUAE.
   Leer su SKILL.md si se aplica la habilidad. Si vuelve el error de pipe,
   no repetir indefinidamente ni sustituir una prueba física por PADTEST.
   Alternativa válida: el usuario juega y valida U1 en la instancia de prueba.
2. Lanzar el ADF vivo con KS 1.2/A501. Usar el candado y capturas periódicas
   para dejar evidencia de la entrada y del regreso del diagnóstico:

   ```powershell
   & C:\Users\JC\Downloads\sma\winuae_lock.ps1 .\tools\shot.ps1 -Exact -Adf work\g5l\liveclose\game.adf -Out work\g5l\liveclose\keys.png -Wait 180 -Every 5
   ```

   Tras la carga, flecha derecha mueve Mario; Z salta y A corre. Guardar
   antes/después. Dejar morir hasta el diagnóstico (cinco vidas), espacio
   muestra historial y RETURN inicia un juego nuevo. Deben volver Mario,
   cámara y Rex, sin Guru ni foto antigua. La muerte normal ya tiene
   capturas reproducibles con `GDEFS='-DG5L -DCUSHION -DZ1STOP=240'` y
   `-DZ1STOP=411`; `diag_read.py --shot ... --bin ...` debe dar $71=09/00.
3. Leer página 2 con `diag_read.py --shot <PNG> --bin ... --repro`.
   El historial de teclado debe reproducir la RAM; la entrada lógica a
   publicación sigue en dos ticks (40 ms PAL, +20 ms). La llegada de la
   tecla hasta su lectura puede sumar un tick; no atribuir ese tiempo al
   colchón ni presentar el test de CPU como medida del host.
4. **Solo con la interacción verde**, preparar el perfil por defecto
   G5L+CUSHION+SPR_OAM. Respetar los builds explícitos antiguos y los otros
   experimentos (SPR_G5, NODECOUPLE, HZ25). La regresión histórica necesita
   seguir compilando su control sin G5L de forma explícita; no bajar sus
   umbrales para hacer pasar una configuración distinta. Mantener la nueva
   puerta `--g5l` para el perfil integrado. Esta es una fase de diseño del
   build, todavía no implementada; probar replay, vivo y BENCH antes de
   declarar que el script aplica los flags.
5. Registrar cinco MD5 nuevos: replay, vivo, replay BENCH, replay DECOUPLE
   y replay DECOUPLE BENCH. Compararlos con el informe T, anotar flags
   exactos y el cambio intencional. Repetir lint, regress `--level --g5l`,
   memmap replay/vivo y captura. Hacer el cambio de defectos en **su propio
   commit**, al final. BM_FIXED queda aparte hasta cerrar BM1.

## Paradas e informe

Parar el paso dependiente si falta teclado real, hay Guru, estado antiguo
al volver, más chip o una cuarta lista. No hace falta reabrir T para cerrar
V: dos candidatos ya llegaron a su parada con 66/65 fotos BENCH. El informe
lleva capturas, historial/retorno, memoria, flags y MD5 de cada build, latencia
con extremos definidos. Actualizar PROXIMO/ROADMAP/SUBAGENTES y archivar
la sesión conforme a ROADMAP §7; nada derivado en git.
