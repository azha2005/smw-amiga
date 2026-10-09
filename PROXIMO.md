# PRÓXIMO — lo que sigue

2026-10-09. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior; los documentos indican el avance de la rama.

Se iteraron las tres tarjetas. **T llegó a su parada**: 67→66 fotos BENCH;
el segundo intento dio 65 pero racha2 y se retiró. Control con tres listas
9; VBTRACE sin BENCH 25 saltos (instrumentaciones distintas). D1 roja.
**V implementada opt-in**: tres listas en vivo, muerte/reinicio/diagnóstico
y latencia de dos ticks verdes; falta teclado real antes del defecto.
**BM1 opt-in funciona en KS1.2/A501**: MFM y arenas fijas, datos/imagen
exactos, reinicio, 18920 B recuperados y carga 32,24 s. Falta KS1.3.

Commits de código: `5461b8a`, `a728ddc`, `a41da43`, `c30ff27`. Informes:
`docs/informe-g5l-r-tirones-1009.md`, `docs/informe-g5l-r-vivo-1009.md`,
`docs/informe-bm1-1009.md`, `docs/informe-bm1-limites-1009.md`. Lint, regress `--level --g5l --bm1`, OAM68K
y cinco MD5 normales verdes. **Los defectos siguen iguales**.

## 0. Sesión interrumpida 2026-10-09 (tarde) — retomar desde aquí

El usuario pidió la PC; quedó a medias. **Decisiones del usuario:**
KS 1.3 = `C:\Users\JC\Desktop\Escritorio 26\Escritorio 25\jueguitos p amiga\Kickstart v1.3 r34.005 (1987-12)(Commodore)(A500-A1000-A2000-CDTV)[!].rom`;
**sin A501 el juego no carga** (el rojo estable del boot fijo es la
política; se cierra la exclusión). El usuario jugó el vivo: "anda y se
mueve" (U1 a mano). Worktrees redundantes borrados (9, ya en master);
quedan los que tienen commits fuera de master: agent-ab11…, agent-af1f…,
wt-g5bis-1007, wt-review-1007.

Hecho: partida verde (lint, regress `--level --g5l --bm1`), builds
`work/g5l/liveclose` (188/190 verdes) y `work/bm1/compare` (MFM y
memmap verdes). `tools/shot.ps1 -Keys "seg:down|up|tap:TECLA;..."`
manda scancodes con SendInput; **hace falta `-norawinput_keyboard`**
(lo agrega solo) o WinUAE no las ve.

**Abierto con teclas inyectadas** (`work/g5l/liveclose/d_*.png`, no
reproducido a mano por el usuario): mantener RIGHT mata a Mario al
instante (diag: motivo 11 muerte, frame 07EE, X0010 Y0336, $71=09, PIE
FFFF, HIST 0002); reaparece, camina y vuelve a morir. Sin teclas no
muere. Sospecha: artefacto de la inyección (el ALT que `Front()` manda
cada segundo, o el scancode extendido) — **leer la página 2 con
`diag_read.py --shot d_105s.png --bin work/g5l/liveclose/game.bin
--repro`** para ver los bits que vio el juego antes de tocar código.
Espacio → página 2 y RETURN → juego de nuevo funcionaron (d_111s+);
d_117s salió negra (sin explicar).

Faltan: esa lectura, KS 1.3 (BM1 pasos 1-3), control trackdisk (paso
4), defectos G5L+CUSHION y BM_FIXED (ahora sin bloqueo A501), MD5,
informes y cierre §7.

## 1. La próxima sesión

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-V cierre** | teclado real/RETURN en WinUAE; después, G5L+CUSHION por defecto en commit propio | `docs/instrucciones-g5l-r-cierre.md`: arranque/interacción, Z1, historial, memoria y cinco hashes nuevos |
| **BM1 cierre** | KS1.3, política sin A501 y tiempo comparable contra trackdisk; conservar boot opt-in mientras falten puertas | `docs/instrucciones-bm1-cierre.md`: MFM/mapa/Z1 verdes, bytes y píxeles exactos en ambas ROMs, tiempo con mismos extremos |

No repetir implementaciones que ya pasan. Si falta el helper o ROM,
continuar solo puertas independientes. Builds seriales, una WinUAE midiendo,
R9. T no recibe otro candidato antes de revisar los números de su parada.

## 2. Después

Revisión de T: fast fallido/sweep durante daño y presupuesto global de
build_mid/S5; 66 BENCH y 25 VBTRACE aún no cumplen D1. Luego otros enemigos,
dos Rex, bobs/Banzai, HUD y audio. BM1 deja solo 24856 B de chip en vivo:
las tablas CPU en chip (135468 B) todavía necesitan C2/C4 y espacio slow.
**[usuario, 2026-10-09]: el foco es G5L-R**; B2bis/Cpre/B35 aparcadas.

## 3. Pendiente del usuario o la PC

- Ruta local de **Kickstart 1.3**: solo se encontró `amivideo/kick12.rom`.
- Helper Computer Use: error de conexión nativa (`os error 2`) tras dos
  intentos y reinicio; impide enviar teclado real. U1 también puede
  validarse jugando el ADF normal G5L vivo de la rama.
- Antes de sustituir el boot normal, cerrar soporte sin A501: el fijo
  muestra rojo estable, el normal conserva su comportamiento anterior.
- U2 capa 2 contra referencia; U3 opcional A500 real. Borrar worktrees
  viejos sigue siendo decisión del usuario.

ADF vivo normal con Rex/colchón: `work/session/live/game.adf` en el
worktree. ADF vivo bare metal final: `work/rg_bm1/game.adf`.
