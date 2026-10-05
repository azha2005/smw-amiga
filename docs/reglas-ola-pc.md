# Reglas comunes para los subagentes (PC Windows, ola 3)

> Movido textual el 2026-10-05 desde `../reglas_ola.md` (fuera del repo),
> que fue lo que recibió cada subagente de la ola 3. Al lanzar una ola
> nueva en la PC, pasarle este fichero; lo agregado después está en la
> sección "Agregado el 2026-10-05", al final.

Leé esto entero antes de empezar. Manda sobre la documentación del repo  
(escrita para cloud) donde se contradigan. Tu worktree es  
`C:\Users\JC\Downloads\sma\wt-<id>` (Git Bash: `/c/Users/JC/Downloads/sma/wt-<id>`),  
rama `wt/<id>`. Hay otros 4 subagentes trabajando a la vez en otros  
worktrees: no toques nada fuera del tuyo.

## Entorno (AGENTS.md P82)

- Al principio de cada comando Bash:  
  `cd /c/Users/JC/Downloads/sma/wt-<id> && export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python`  
  (ucrt64 primero o gcc falla sin mensaje desde Python). Para snesorc  
  agregá también `/c/msys64/usr/bin` (make) al PATH.
- `python3` es un stub roto de WindowsApps: usá `python`. `$TEMP/pyshim/python3`  
  existe para los scripts que llaman `python3`.
- Regresión: `python tools/regress.py --baseline tools/baseline_pc.json`  
  (NO `tools/baseline.json`: es de cloud, otro vbcc). En master da OK.
- No hay FS-UAE: `fsuae_shot.sh` y `regress.py --emu` no funcionan. En su  
  lugar WinUAE cycle-exact con KS 1.2 real (`tools/shot.ps1 -Exact`,  
  `shots6.ps1`, `shots63.ps1`), SIEMPRE por el candado, desde PowerShell  
  con el worktree como directorio actual:  
  `& C:\Users\JC\Downloads\sma\winuae_lock.ps1 .\tools\shot.ps1 -Exact -Adf work\x.adf -Out work\x.png -Wait 80`  
  Semáforo de 3 lugares: hasta 3 WinUAE a la vez entre todos (podés lanzar
  varias capturas en paralelo desde worktrees distintos, NO dentro del
  mismo: `shot.ps1` usa `work\shot.uae` fijo; dejá margen en `-Wait`). Con capturas  
  de WinUAE: `scroll_check.py --sc 2` e `imgdiff.py --crop 130,69,642,517`.  
  No cierres ningún WinUAE que no hayas abierto vos.
- `scrollprof.py` escribe siempre `work/scrollprof.bin`: en tu worktree no  
  hay problema, pero no lo corras dos veces a la vez.
- Finales de línea: `core.autocrlf=true`. No commitees ficheros cuyo único  
  cambio sea CRLF/LF (`git diff --ignore-cr-at-eol` vacío → `git checkout -- <f>`).  
  snesorc necesita los `.orc` y `oracle_*.txt` en LF para leerlos (P82.7).
- snesorc: `work/snesorc.exe` ya está compilado en tu worktree; assets en  
  `C:/msys64/home/JC/.cache/snesrev-smw/smw_assets.dat` (`snesorc_make.sh`  
  exporta `SNESORC_ASSETS` solo; un .exe suelto lo necesita a mano).
- El fuente del ROM: `C:\Users\JC\Downloads\sma\smw-src-master\project\mw_e10\`  
  (donde las tarjetas dicen `/home/user/smw-src-master`).
- Cruces de RAM PC=68000 en Windows: `regress.py` no arma `work/libport.so`;
  armalo antes de la regresión si tocás C del port:
  `gcc -shared -O2 -DNOOAM -Iplayer -o work/libport.so player/mario.c player/mcoll.c player/manim.c player/mgfx.c player/mcam.c player/msprite.c player/mspr.c player/spr_*.c player/gen/smwrom00.c`
- Después de un `git merge` que traiga tablas nuevas: `python tools/smwtabx.py`.
- P36: a los datos del C les quedan ~3 KB antes del límite de 32 KB de a4;
  `logicbench_build.sh` avisa. Tablas nuevas, en bloques `#ifdef SMWTABX_<X>` (P78).
- `sleep` en primer plano está bloqueado en Bash.
- Leé AGENTS.md §8 solo las trampas que te nombre tu tarjeta (grep "\*\*Pnn").

## Reglas fijas

1. Solo tu worktree. Sin push. Commits locales en español (`Etapa N.x: <qué>`)  
   terminando con la línea de atribución que te da tu prompt.
2. No edites AGENTS.md, ROADMAP.md, SUBAGENTES.md, tools/baseline.json ni  
   tools/baseline_pc.json. Trampas y números van en el informe.
3. Antes de cada commit: `python tools/lint_port.py && python tools/regress.py --baseline tools/baseline_pc.json`.  
   MEJOR está bien (decilo); PEOR: arreglalo, o si es a propósito explicalo.
4. Nunca saltarse, desactivar ni aflojar una comprobación para llegar a la  
   puerta. Nunca cambiar la semántica para ganar ciclos.
5. Ficheros con barras invertidas (macros `\1` de vasm, `\n` en C): con  
   Write/Edit, no heredoc.
6. Parar y avisar si: la puerta no se cumple tras 3 intentos distintos; hace  
   falta tocar un fichero de "No toca"; algo contradice la tarjeta o AGENTS.md.
7. Si el coordinador te pide cerrar: commiteá lo que pasa su puerta, el  
   resto en `WIP: <qué falta>`, y mandá el informe. Al terminar, nada sin  
   commitear y sin ficheros de prueba.
8. Informe final (corto y con evidencia): commits (hash + título), salida de  
   la puerta, números antes → después con herramienta y emulador, qué no  
   pudiste probar, trampas nuevas como `Pnn` sin número, diferencias de Windows.

## Agregado el 2026-10-05

- La regresión completa en la PC es
  `python tools/regress.py --baseline tools/baseline_pc.json --level`
  (con `--level` entran las métricas `nivel.*` de la base).
- Varias capturas en paralelo desde **un mismo** worktree: cada worker
  necesita su propia copia de `shot.ps1` en su carpeta (`shot.ps1` escribe
  `work\shot.uae` y `work\shot.log` junto a sí). Es lo que hace
  `tools/sxverify.py` (`work/sxverify/slots/<worker>/`); con tres workers,
  las 12 capturas de SX bajaron de ~30 a ~8 minutos.
- El candado es un directorio (`winuae.lockN`). Si se mata un worker, el
  `finally` no corre y el lugar queda tomado 30 minutos: borrar a mano
  solo el `winuae.lockN` propio (su fecha de creación = el arranque de la
  captura).
- El heredoc de Bash también altera los caracteres no ASCII (acentos, `→`):
  un `str.replace` de Python dentro de un heredoc puede no encontrar el
  texto. Para editar docs en español, Edit; para scripts, Write a un
  fichero y correrlo.
