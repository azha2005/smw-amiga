# BM1 — cerrar compatibilidad y tiempo de carga

2026-10-09. Código `a41da43` + límite MFM `c30ff27`; `informe-bm1-1009.md` distingue lo probado
de lo pendiente. KS 1.2/A501 funciona, MFM y arenas están implementados.
Faltan ROM 1.3 local, tiempo trackdisk comparable y decisión de soporte
sin expansión si se pretende sustituir el boot normal. El boot nuevo
sigue opt-in; no hace falta repetir sus cuatro fases desde cero.

## Partida y reglas

Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama g2t-b2bis;
una WinUAE, builds seriales, sin merge/push, R9, DMA solo en chip.
No descargar ROMs ni inventar un desglose de propietarios de MemList.

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
# RESULTADO: OK; MFM 84 casos, memmap 17 casos, G5L GAME y Z1.
GDEFS='-DREPLAY -DSTOPF=1700' OUT=work/bm1/compare sh tools/bm_build.sh
python tools/mfm_verify.py --bin work/bm1/compare/boot_bm.bin --lst work/bm1/compare/boot_bm.lst
# MFM: OK
python tools/memmap.py work/bm1/compare/game.lst --data work/yi1_s_g5.dat
# 0 violaciones; scratch MFM transitorio, arena chip desde 1000.
```

## Pasos

1. Obtener del usuario la **ruta** de KS 1.3, que falta en la PC; no usar
   KS 3.0 como sustituto. Con la ROM existente, repetir KS 1.2 si hubo
   algún cambio de código. Arranque KS 1.3, mismo ADF/STOPF:

   ```powershell
   & C:\Users\JC\Downloads\sma\winuae_lock.ps1 .\tools\shot.ps1 -Exact -Rom <ruta-KS1.3> -Adf work\bm1\compare\game.adf -Out work\bm1\compare\ks13.png -Wait 90
   ```

   Mientras está abierto, el PID que muestra `shot.ps1` se usa en:

   ```sh
   python tools/bm_probe.py --pid <PID-de-esta-prueba> --lst work/bm1/compare/game.lst --out work/bm1/compare/ks13.json --retained 23016
   # BM1 WINUAE: OK; SR2000, datos 1000 y 230180 bytes exactos.
   python tools/g5l.py shot --bin work/bm1/compare/game.bin --lst work/bm1/compare/game.lst --frame 1700 --shot work/bm1/compare/ks13.png --control work/g5l/c1700/shot.png
   # pixeles_distintos: 0 de 327680 (control existente sin Rex, misma foto).
   ```

   No reutilizar PID viejo. Si falta ese control, generarlo con build
   normal sin G5L, REPLAY+CUSHION+STOPF=1700 y SPR_OAM. Verificar mismo
   recorte/escala antes de atribuir diferencias al loader.
2. Vivo/reinicio bajo la ROM nueva:

   ```sh
   GDEFS='-DZ1STOP=411' OUT=work/bm1/z1 sh tools/bm_build.sh
   python tools/restart_verify.py --dir work/bm1/z1
   ```

   Capturar con `shot.ps1 -Exact -Rom ... -Wait 70` y leer con
   `diag_read.py --shot ... --bin ...`: frame411, $71=00, X0010/Y0160.
   En KS 1.2 esta captura ya está en `work/session/bm-z1/shot.png`.
   Teclado/RETURN comparte la puerta pendiente de G5L-R-V.
3. Sin A501, `shot.ps1 -SlowMem 0 -Wait 20` ya dio rojo estable en KS 1.2.
   Repetir en 1.3. El build normal conserva su fallback anterior; el fijo
   exige A501. Antes de sustituir el boot por defecto, cumplir el contrato
   de la tarjeta original: conservar ese caso o cerrar con el usuario la
   exclusión. Mantener ambos builds mientras no se cierre.
4. **Fase de medida pendiente: control trackdisk.** Instrumentar el boot
   antiguo y el fin de lectura de datos con flag opt-in, sin alterar los
   cinco hashes normales. Usar lecturas no destructivas del TOD CIA-A y
   guardar inicio/fin-stage/fin-datos en memoria reservada propia que
   sobreviva a la copia del binario; no usar una dirección fija que Exec
   pueda asignar ni poner datos CPU en el scratch DMA. Definir y comparar
   los mismos extremos: desde entrada del boot hasta lectura de datos
   terminada, sin Kickstart ni scroll_init. El BM medido dio 20,62/32,24 s;
   repetirlo con la misma imagen de juego del control. No afirmar mejora
   de tiempo hasta medir ambos. Se trata de una investigación con puerta,
   no de un arnés que ya exista.
5. Con compatibilidad, bytes/imagen, Z1 y tiempos verdes: repetir red,
   cinco MD5 normales idénticos (informe T), memmap y dejar informe final.
   Hacer el boot por defecto requiere que esté cerrado el
   alcance sin A501; no se ha hecho en esta sesión.

## Paradas e informe

Si falta KS 1.3, continuar solo tareas independientes, sin marcar
compatibilidad completa. Si la arena invade C7C000 o DMA toca slow,
corregir antes de emular. El informe separa 23016 B retenidos de 18920 B
recuperados con reserva inferior de 4096; no atribuye ciclos de juego al
SO dormido. Conservar scratch transitorio (solo durante carga), mapa en
replay/vivo, ROM/configuración, tiempo con extremos definidos y evidencia
de bytes, píxeles y reinicio. Cerrar docs según ROADMAP §7.
