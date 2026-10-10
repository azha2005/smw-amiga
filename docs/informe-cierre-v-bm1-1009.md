# Cierre G5L-R-V y BM1 (2026-10-09, tarde)

Rama `g2t-b2bis`, sin merge ni push. Las dos tarjetas quedan **cerradas**:
teclado real verificado, G5L+CUSHION+SPR_OAM por defecto y el boot BM1 por
defecto del vivo. D1 sigue roja (tirones de T, sin cambios en esta sesión).

Decisiones del usuario (2026-10-09): ROM KS 1.3 local
(`Desktop/Escritorio 26/Escritorio 25/jueguitos p amiga/Kickstart v1.3 r34.005 ...[!].rom`);
**sin A501 el juego no carga** (el rojo estable del boot fijo es la política,
se cierra la exclusión); borrar los worktrees redundantes. El usuario jugó el
vivo a mano: "anda y se mueve" (U1).

## 1. Teclado real (G5L-R-V, pasos 1-3)

`tools/shot.ps1 -Keys "seg:down|up|tap:TECLA;..."` manda scancodes con
`SendInput` a la ventana de WinUAE, después de tomar el foco con
`AttachThreadInput`. Llegan a la Amiga por el teclado emulado (CIA-A SP,
`kb_int`), no por PADTEST. **WinUAE con RawInput las ignora**: el script
lanza el emulador con `-norawinput_keyboard` cuando hay `-Keys` (P117).

WinUAE PAL cycle-exact, A501:

| ADF | ROM | evidencia (work/, ignorado) | resultado |
|---|---|---|---|
| `g5l/liveclose` (G5L+CUSHION, trackdisk) | KS 1.2 | `g5l/liveclose/e_*.png`, `e_montage.png` | corre (A), salta (Z), scroll, moneda de Yoshi y Rex en pantalla; muere, diagnóstico, ESPACIO → página 2, RETURN → juego nuevo con Mario al inicio |
| idem | | `diag_read.py --shot e_104s.png --repro` | historial de 8 entradas: R, Y (A) y BY (Z+A) vistos; **la PC reproduce la muerte igual** (frame 1510, X 0085 Y 0335) |
| `md5/g5l_vivo2` (defecto nuevo, BM) | KS 1.3 | `md5/g5l_vivo2/k_*.png`, `k_montage.png` | lo mismo con el boot BM; historial R/Y/BY, reproducción **IGUAL** (frame 1550, X 0085 Y 0335) |

Las muertes cerca del inicio son **fieles**: snesorc (snesrev) con la misma
entrada muere igual. Mario quieto muere a los 220 frames y quieto 178 +
derecha 85 muere en x $21: el Koopa deslizante `$BD` baja la colina (P117).
Latencia: `restart_verify.py` sigue dando 2 ticks lógicos de entrada a foto
visible (40 ms PAL); la llegada de la tecla hasta `read_input` puede sumar
un tick, que no es del colchón.

## 2. Perfil por defecto (G5L-R-V, pasos 4-5)

`tools/game_build.sh` tiene `PROFILE` (por defecto `g5l`):

- `g5l`: CDEFS por defecto `-DNOOAM -DSPR_OAM`; se agregan `-DG5L -DCUSHION`
  y el banco `work/g3/bank` (para la tabla G5L). **El vivo (sin `-DREPLAY`)
  agrega `-DBM_FIXED`** y arranca con `boot_bm` (sección 3); replay, BENCH,
  `LOADTIME` y `MEMPROBE` siguen con trackdisk.
- No se agrega nada si CDEFS explícito no trae SPR_OAM (builds antiguos) o
  hay un experimento: SPR_G5, NODECOUPLE, HZ25, G5_PRE, o ya trae G5L.
- `PROFILE=legacy`: el build anterior. La regresión histórica (`game_checks`,
  `work/rg_game`) y `stress_ab_build.sh` lo piden explícitamente; sus
  umbrales no se tocaron.

MD5 de `game.bin` (`work/md5/*`):

| modo | GDEFS | defecto nuevo | `PROFILE=legacy` (= informe T) |
|---|---|---|---|
| REPLAY | `-DREPLAY` | `4328e9c83a309e7527c62d0da7e3a6c4` | `8d567edf313dc0962396f1373e516132` |
| vivo | `" "` | `ab75abb4f839d9e2201622375a2726e7` (BM) | `5de846a6b0b82d85abc7e913fcb8fcaf` |
| REPLAY BENCH | `-DREPLAY -DBENCH` | `e8ac5ee84e5a4a801d5ae9b0e9568026` | `e669b2af1e097d0763fdef09ef5ccdfb` |
| REPLAY DECOUPLE | `-DREPLAY -DDECOUPLE` | `4328e9c83a309e7527c62d0da7e3a6c4` | `8d567edf313dc0962396f1373e516132` |
| REPLAY DECOUPLE BENCH | `-DREPLAY -DDECOUPLE -DBENCH` | `e8ac5ee84e5a4a801d5ae9b0e9568026` | `e669b2af1e097d0763fdef09ef5ccdfb` |

Los cinco legacy son idénticos a los del informe T. El replay por defecto es
idéntico al build explícito `CDEFS='-DNOOAM -DSPR_OAM' GDEFS='-DREPLAY -DG5L
-DCUSHION' SPR_BANK=work/g3/bank`; el vivo G5L trackdisk explícito
(`e634835…`) es el binario de la prueba de teclado; el vivo por defecto es
idéntico a `work/rg_bm1` de `regress.py --bm1`. Cambio intencional: el
defecto pasa de NOOAM sin G5L a G5L+CUSHION (+BM en el vivo).
`inputtest.py`: 35/35 en el vivo BM y en el legacy.

## 3. BM1 en KS 1.3, sin A501 y tiempo (pasos 1-4)

| puerta | KS 1.2 | KS 1.3 |
|---|---|---|
| `bm_probe.py` (replay STOPF=1700) | OK: SR 2000, 230180 B exactos en chip real | OK, idem |
| `g5l.py shot` contra `g5l/c1700` | **0/327680** px | **0/327680** px |
| Z1STOP=411 + `diag_read.py` | (sesión anterior) | frame 411, X 0010 Y 0160, $71 00 |
| sin A501 (`-SlowMem 0`) | rojo estable | rojo estable a 10/20/30 s, idéntico, sin Guru |

`restart_verify.py --dir` sobre un build con `Z1STOP` falla en la prueba de
latencia de `dc_vb` **con y sin BM** (`work/g5l/z1n`): es el arnés con el
flag de captura, no el loader (P119). El reinicio BM lo verifica
`regress.py --bm1` sobre el vivo sin Z1STOP (verde).

**Control trackdisk** (`-DLOADTIME`, opt-in): `boot.s` lee el TOD de CIA-A
**sin escribirlo** al entrar al bootblock y al terminar stage2 y lo pasa en
d7/d6; `game.s` guarda las tres marcas en `TDLOAD!!` (dentro del binario,
que sobrevive a la copia a slow) y la tercera después de leer los datos y
apagar el motor. `tools/load_probe.py --pid` las lee. Mismos extremos que
`BMLOAD!!`; misma imagen de juego (`-DREPLAY -DSTOPF=1700`, G5L+CUSHION;
stage2 394012 B contra 394140 B de BM, datos 230180 B en el mismo offset).
Sin el flag, `boot.s` da el mismo binario (comparado con `cmp`).

| loader | ROM | stage2 | stage2 + datos |
|---|---|---:|---:|
| trackdisk | KS 1.2 | 1008 ticks = 20,16 s | 1651 = **33,02 s** |
| trackdisk | KS 1.3 | 1009 = 20,18 s | 1651 = **33,02 s** |
| BM1 MFM | KS 1.2 | 1018 = 20,36 s | 1599 = **31,98 s** |
| BM1 MFM | KS 1.3 | 1017 = 20,34 s | 1598 = **31,96 s** |

BM1 carga **1,04 s antes (3 %)**; stage2 solo es 0,2 s más lento. Domina la
mecánica del disquete: el beneficio de BM1 es la memoria (18920 B de chip
recuperados) y el mapa fijo, no el tiempo.

## 4. Memoria y red

`memmap.py <game.lst> --data work/yi1_s_g5.dat`, 0 violaciones en los dos:

| build por defecto | chip | margen chip | slow | margen slow |
|---|---:|---:|---:|---:|
| replay (trackdisk) | 483808 B | 40480 B | 401224 B | 123064 B |
| vivo (BM1, fijo) | 499432 B | 24856 B | 454072 B | 70216 B |

`lint_port.py`: OK (`asmlint_port` ya no exige que exista `work/g5_pre.i`,
que es derivado y no se sigue). `regress.py --baseline tools/baseline_pc.json
--level --g5l --bm1`: **OK**, métricas `game.*`/`m68k.*` iguales a la base
(el control histórico ahora pide `PROFILE=legacy`).

Commits: `1cab075` (`shot.ps1 -Keys`), `143c9ea` (LOADTIME, load_probe,
ROM con corchetes, asmlint), `53e6453` (**cambio de defectos, commit
propio**).

## 5. Lo que no cierra esto

D1 sigue roja: 66 fotos BENCH y 25 saltos VBTRACE (informe T); el colchón
fue aceptado por el usuario y G5L+CUSHION es ahora el defecto. KS 1.3 y la
A501 quedan cubiertos; un A500 real (U3) sigue opcional. La captura negra
suelta de `d_117s.png` (sesión interrumpida) no se repitió en las dos
corridas siguientes con RETURN; las negras entre vidas son el fundido de la
muerte.
