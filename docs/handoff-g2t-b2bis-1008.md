# Handoff B2bis rendimiento + Cpre — 2026-10-08

Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama g2t-b2bis.
Sin merge/push. Partida 2785b74; mejora B2bis comprometida d3e431c,
después Cpre WIP. El handoff y PROXIMO anteriores están en archivo/sesiones.md.

**B2bis:** warm medio 6595→5501, frío 29922→28606; cache 554/11910,
captura 270. N=8 y hash original; N=4 se descartó por juego completo.
Canarios ahora al tamaño del listado, negativo de última entrada incluido.
Red exacta y cinco hashes verdes. WinUAE misma tanda: control 27 fotos,
B2bis 92, racha 2; antes 98. Vista 0/327680 píxeles diferentes, inspeccionada.
D1 roja y solo 272 B de slow libre tras reservas en vivo G3. Informe:
`informe-g2t-b2bis-rendimiento-1008.md`. No hay emuladores propios activos.

**Cpre:** C2a recorre 6313 fotos, 2288 Rex; cinco contadores cero. Índice
lógico R_FRAME y fuente gráfica última RUN/RUNSYNC: 49 fotos retenidas
f7552..7600 conservan gráficos f7551. Mario DMA y colores comprobados;
no se afirma OAM viva de Rex exacta tras resync. Tabla completa 451172 B
solo virtual externa; ventanas WinUAE ≤16 KB todavía no probadas.

`player/g5.s` es una sonda bajo G5_PRE_PROBE, no un emisor: busca B1 y
firma prefijos sin escribir. ABI/listas intactas en 6313 fotos, negativo
de firma detectado. Media 5295,57; máximo 28680 f8508; tabla vacía 468.
Dos fotos del recorrido con sonda superan PAL. Memmap prototipo: chip
472112, slow 317888, cero violaciones, sin contar la tabla externa virtual.
Salida roja esperada por límite 4000, no esconderla como gate verde.

## Retomar

1. Leer PROXIMO y las dos tarjetas enlazadas. Consulta de presupuesto
   enviada al usuario; sin respuesta rige 4000. No avanzar C4 ignorándolo.
2. Git Bash: PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH",
   VBCC=/c/Users/JC/vbcc, PY=python. No builds concurrentes (work/cc).
3. `work/cpre_safety.sh`: siete tests G5PR, build externo PROBE, memmap,
   C2a, sonda vacía/completa, red completa/hashes. La sonda completa sale
   1 por coste; revisar JSON y texto literal, no solo estado del wrapper.
4. `work/g2tc/{summary,emit_probe_summary}.json`, preplan.log,
   emit_probe.log, empty_probe/probe.log, memmap_probe.log. Derivados no
   versionados; el código está en tools/g2t_preplan.py y g2t_emitprobe.py.
5. Faltan emisión, limpieza de sufijos por lista, VBL, G5_EMPTY, C2b
   gamecheck del emisor terminado, C3/listcheck, C4/shotcmp y C5/C6. El
   asm rechaza un build que omita PROBE: no quitar el fail para fingir avance.
6. Seguir coste y rediseño con contrato intacto o decisión explícita del
   usuario para prueba offline. No tocar g2t_ref, banco, scroll o B35 vivo.

Red final en work/g2tc/{lint_final,regress_final,oam_final,g5env_final,
hashes_final}.log. G5ENV incluye cuatro memmap y restart vivo sin G5_PRE.
Cinco hashes idénticos al inicio; baseline_pc intacta. Cpre no tuvo
capturas WinUAE: no hay evidencia visual del Rex ni puerta C4 aprobada.
