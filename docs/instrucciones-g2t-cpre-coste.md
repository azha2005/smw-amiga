# G2T-Cpre — resolver la parada de coste antes de C3/C4

2026-10-08. Continuación del WIP descrito en `informe-g2t-cpre-1008.md`.
No requiere subagentes. La tarjeta Cpre completa sigue vigente, salvo
una modificación explícita del presupuesto que autorice el usuario.

## Partida y reglas

1. Leer PROXIMO, el informe Cpre, P114 y `instrucciones-g2t-cpre.md`.
   C2a tiene 2288 planes exactos; la sonda C2b llega a 28680 ciclos sin
   emitir. Objetivo 2500, parada 4000. No presentar la sonda como emisor.
2. Trabajar en `wt-g2t-b2bis-1008`, rama g2t-b2bis. No merge/push.
   Modelo, contrato, banco y scroll.s intactos; derivados solo en work/.
   No activar B35 en vivo. No quitar firmas ni convertir una prueba
   negativa en un acierto para alcanzar el presupuesto.
3. Git Bash desde el worktree:

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/test_g2t_preplan.py
# 7 tests, OK
CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' GDEFS='-DREPLAY -DG5_PRE -DG5_PRE_EXT -DG5_PRE_PROBE' SPR_BANK=work/g3/bank OUT=work/g2tc/ext sh tools/game_build.sh
python tools/g2t_preplan.py generate
# 6313 fotos, 2288 Rex, cinco contadores cero, tabla 451172 B
python tools/g2t_emitprobe.py
# salida 1: PARADA por coste; max 28680, ABI/listas/misses cero
```

No construir a la vez: work/cc, logicbench y includes se comparten.
La RAM virtual extra de la tabla completa es solo del arnés, no A500.

## Resolver el coste

4. Leer la respuesta del usuario a la consulta de presupuesto. Mientras
   no haya respuesta, rige 4000: se puede perfilar/rediseñar preservando
   el contrato, pero no avanzar a C4 con un emisor que lo supera.
5. Medir por componente: búsqueda, recorrer B1, suma/búsqueda del salto,
   copia, limpieza y VBL. Las 754 palabras máximas de prefijo ya se
   documentaron; no afirmar una cota imposible sin demostración.
   Repetir la sonda y negativos después de cada cambio; conservar ABI,
   índice lógico/fuente gráfica y las listas completas sin cambios en
   la fase de validación. No trasladar trabajo a scroll.s para ocultarlo.
6. Puerta de decisión: con límite vigente, demostrar el camino completo
   ≤4000 antes de continuar; objetivo ≤2500. Si requiere cambiar el
   contrato/modelo, parar con medidas y una propuesta concreta. Si el
   usuario amplía el presupuesto solo offline, registrar su decisión
   y el coste real; D1 y el presupuesto vivo no cambian por esa excepción.

## Continuación Cpre y cierre

7. Con el presupuesto resuelto, implementar el emisor completo de la
   tarjeta original. Leer build_mid: puede conservar sufijos viejos;
   una limpieza que deja su WAIT/NOP todavía vivo no pasa C3. Preservar
   el salto original, nunca tocar WRAP_SEG ni los eventos de capa 1.
8. Ejecutar C2b/gamecheck y C3 completos antes de WinUAE. Después C4:
   al menos 12 frames con los criterios de la tarjeta, ventanas ≤16 KB,
   0/57344 píxeles, comparador fijo y candado. Nada de capturas para
   simular una puerta que todavía no está implementada.
9. Antes de commit: lint, regress baseline_pc --level, OAM68K, G5ENV,
   cinco hashes inalterados, memmap y reinicios. `work/cpre_safety.sh`
   sirve para la fase de sonda, no es la puerta del emisor final.
10. Informe con costes separados, pruebas negativas, fuentes/frames de
    foto, memoria real y virtual diferenciadas, puertas hechas y pendientes.
    Cerrar ROADMAP §7, archivando y reescribiendo PROXIMO/estados. Un WIP
    por parada de coste nunca se marca como Cpre terminada.
