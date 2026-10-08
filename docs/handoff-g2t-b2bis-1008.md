# Handoff G2T-B2bis — 2026-10-08, actualizado

Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama `g2t-b2bis`.
Commits reales: `8a4a43d` clave; `a401723` decoder; `ec320ab` integración
cache/frontera/foto y herramientas. Sin merge ni push.

Las puertas locales están verdes. Todos los pendientes del handoff viejo
se ejecutaron, incluidos bordes, L1/free-buffer/raros C, foto retenida,
BENCH, cuatro memmap, reinicios, WinUAE y red completa. El informe con
números, límites, formatos y hashes es `informe-g2t-b2bis-1008.md`.
El texto anterior está archivado en `archivo/sesiones.md`.

**Pendiente real:** WinUAE pierde 98 fotos (1,55 %, racha 2), control 27.
Antes de vista compacta eran 100. No declarar D1 cerrada ni integrar como
50 Hz cumplidos. Vivo G3 deja 264 B tras G5EV/work/fotos/salida/pila:
revisar memoria antes de añadir código. B35 no se ejecuta en vivo; Cpre
no se inició. El usuario autorizó continuar iterando sin rebajar puertas.

## Retomar

1. Leer PROXIMO y `instrucciones-g2t-b2bis-rendimiento.md`.
2. Git Bash: PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH",
   VBCC=/c/Users/JC/vbcc, PY=python. `sh tools/g5env_gate.sh`.
3. Perfilar primero el miss/proyecto frío; conservar el formato warm
   portable con copia propia. No dejar punteros a cache mutable en vista.
4. Regenerar ASM con tools/g5env_asm.py. Repetir los 258 sintéticos,
   callbacks reales del juego y los controles ABI/canarios. Leer P112.
5. Para evidencia: work/b2b_shotbuild.sh y work/b2b_shots.ps1; el control
   sale de a52e2ba con el mismo C. BENCH 190 s, visual STOPF=1800 95 s;
   copias de shot.ps1 y candado. `python tools/g5env_shot.py`.
6. Red antes de commit: lint, regress baseline_pc --level, OAM68K, G5ENV,
   hashes. work/b2b_final.sh lo reproduce secuencialmente; no ejecutar
   builds concurrentes porque comparten work/cc y logicbench.

Logs/JSON final: work/b2b/{gate_final,lint_final,regress_final,oam_final,
hashes_final,shot_final}.log, memory_summary.json, shot_summary.json;
cache/decode/game/edges tienen su JSON. Vista control arriba/B2bis abajo:
work/b2b/view_control_ab.png, 0 píxeles distintos, inspeccionada.
No hay WinUAE de prueba pendiente; no cerrar procesos ajenos.

47 SKIP + 1 SYNC difieren del fixture PC provisional por la captura
antes del rollback/gráficos congelados. Todas las fotos son exactas contra
el modelo del estado capturado. No modificar g2t_ref ni replay para
ocultar esta limitación. Decodificación de imágenes arbitrarias de dos
columnas exacta, sin promesa de 12000 ciclos para esos dibujos raros.
