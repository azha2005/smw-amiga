# G7-2/G7-3 — fuentes, color y cola de efectos

2026-10-10. Continuación de `docs/instrucciones-g7.md`. La memoria está
resuelta (`docs/informe-g7-1010.md`); hay un prototipo `G7_DOUBLE` de doble
PF1 con cursores independientes. **Los efectos aún no se ven.**

**Prerequisito:** conservar las pruebas de propiedad y SW1 de G7-1
(`instrucciones-g7-1.md`). El doble PF1 prepara primero el copper de
la lista libre y espera al anillo antes de escribir columnas/mapa.
D1 sigue roja: medir el coste de cada añadido, sin ocultar la espera.

## Partida y comprobaciones

Git Bash:

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
```

Esperado: RESULTADO: OK en ambos. La regresión arma
`work/rg_g7_double_live/` y `work/rg_g7_double_replay/`; ambos tienen
segundo PF1 y **12 KiB reservados para fuentes/máscaras**, 0 violaciones.
No volver a reservar ese banco sin descontar la reserva existente.

```sh
python tools/g7_double_verify.py --bin work/rg_g7_double_replay/game.bin --lst work/rg_g7_double_replay/game.lst
python tools/g7_color_audit.py --bin work/rg_g7_double_replay/game.bin --lst work/rg_g7_double_replay/game.lst
```

Esperado: `G7 DOUBLE: OK`; el audit es informativo (1.075 filas del
criterio conservador requieren otro plan), **no una prueba de que faltan
colores**. Consultar las evidencias nuevas del informe antes de comparar
tiempos antiguos. No activar G7_DOUBLE por defecto antes de mostrar efectos.

## Pasos, en orden

1. Leer P2/P31/P97/P115/P123/P126/P128/P132, `diseno-9.2.md` §4,
   `coinpal.s`, `tilechange.s` y `g7_select/g7_save` en `game.s`.
   Mantener foto tomada antes de preparar el copper/esperar a DC_PEND; no quitar la espera
   sin un verificador de propiedad. Probar un estado que repite el VBL.
2. **Capturar OAM en la foto.** Añadir 320 B por foto (256 de $0200 y
   64 de $0420; con CUSHION, cuatro fotos). Copiar en `dc_capture`, con
   DC_REC actualizado en todos los consumidores. Usar la OAM de DC_REND
   al renderizar, nunca RAM lógica futura. Medir slow en vivo y replay.
   Puerta nueva: comparar esas fichas con `sws_cmp.py` y los cinco oráculos.
3. **Fuentes exactas.** Generar desde `mksprgfx.py`, respetando P99 y
   flip de toda la ficha 16×16. Empezar por las 26 formas del replay,
   después completar los rangos de G7 original (incluidos puntos $83).
   Codificar máscara opaca e índices fuente; colores PF1 se remapean
   por fila. El banco se reutiliza tras `bwait`, porque el DMA muestra
   el PF1, no las fuentes del bob. No multiplicarlo por cuatro fotos
   sin una necesidad medida. Puerta: ida/vuelta píxel a píxel contra G3,
   también clipping, tamaño y flip; cantidad real ≤ 12.288 B o rediseñar.
4. **Paleta junto al terreno.** Usar el testigo k409 para construir un
   plan concreto, con índices PF1 que no alteren el terreno y cargas
   que entren de verdad en el copper. Reconstruir color vigente por x,
   incluida animación de monedas, derrames y P51/P110/P111. El GAP=48
   del audit solo selecciona casos a estudiar: no prueba que una recarga
   sea imposible. Puerta de esta fase: píxeles ideales exactos de bob y
   terreno y ventanas de escritura válidas, antes de programar el blitter.
5. **Regiones sucias por PF1.** Guardar las cajas del último uso del
   anillo; restaurarlas desde BLK y D_MAP, actualizar las columnas y
   el diario del mapa hasta R_TSEQ, dibujar fichas de R_OAM. Cubrir las
   dos copias del anillo, bordes, solapamiento y vuelta de cámara.
   IRQ solo avanza la cola; render es dueño del blitter. Publicar después
   del último `bwait`. Probar restauración sin efectos y VBL repetidos.
6. **Activar efectos y medir.** `NOSWS` debe apagar también su cola.
   Repetir SW1 a `HOLDEVERY=50`; además fotos k 199,1199,1349,1399,
   1549,1799,2199,2749,2899,3149,3449,4699 y 6049-6299. Comparar cajas
   de efectos contra SNES, con fila Amiga = SNES − 1. Repetir A/B BENCH
   en la misma tanda y registrar fotos perdidas, racha y ventana250.

## Puertas y parada

- Antes de cada commit: lint y regresión completa de arriba, más
  `sh tools/sws_gate.sh` y `sh tools/oam68k_gate.sh`.
- No cambiar D8, no aproximar colores, no reducir a 25 Hz, no tocar
  el PF1 visible ni el pendiente, no saltar ni aflojar verificadores.
- Si un **plan concreto** demuestra un color sin lugar exacto, mostrar
  al usuario el caso y las alternativas; el preflight conservador solo
  no alcanza para pedir esa decisión. Si falta memoria, iterar tamaño,
  reutilización y representación antes de proponer recortes visibles.
- Informe: fuentes y tamaños medidos, píxeles, escenas, contadores D1,
  comandos, límites de la prueba y commit real. Cierre según ROADMAP §7.
