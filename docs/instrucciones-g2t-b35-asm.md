# G2T-B35-asm — viabilidad del plan exacto antes de integrarlo

2026-10-08. Continuación de `docs/instrucciones-g2t-b35.md`, después de
su **único intento permitido en C**. El C queda como referencia ejecutable:
B4/B5 exactas en 3404 frames, pero máximo **2 405 022 ciclos sin DMA**
frente al objetivo de **8000**. Informe: `docs/informe-g2t-b35-1008.md`.
No se habilita la integración en vivo con ese coste.

## 0. Objetivo y alcance

Medir una representación dispersa y el núcleo asm del planificador,
manteniendo **los mismos bytes B1 y los mismos desempates**. La primera
entrega es una puerta de viabilidad; no asumir que traducir C a asm
alcanza. Incluso una mejora de diez veces dejaría el máximo en unos
241 000 ciclos, todavía casi treinta veces por encima del objetivo.

Toca `player/g5plan.c`, `player/g5plan.h`, un asm nuevo del planificador,
los arneses de B35 y el build opt-in. Inicialmente no toca `game.s`,
`scroll.s`, el emisor, B2bis ni el banco G3. Los cambios de representación
de `bank.g5env` solo se plantean con una medida de ahorro y memoria;
no se cambia ese formato a ciegas.

## 1. Reglas

- `tools/g2t_ref.py` sigue siendo la especificación y no se modifica.
  Mismo orden de variantes, transiciones, segmentos y MOVE; misma regla
  de fin, cruce 255, 231 → 243 y T0 = −56.
- Mantener el C como control y activar asm con un flag adicional bajo
  `SPR_G5`; todos los builds por defecto idénticos byte a byte.
- Función pura por sus argumentos, sin RAM del juego ni estado global.
  Banco por base; áreas de trabajo en slow; ABI vbcc preservada.
- Un benchmark sin DMA no cierra la compuerta D1. El objetivo local es
  `g5_plan` completo ≤ 8000 ciclos **máximos**, no solo una rutina.
- Sin merge a master ni push durante esta tarjeta.

## 2. Partida y entorno

Trabajar sobre la continuación de `g2t-b35`, en un worktree aislado si
hay otras tarjetas activas. Copiar los derivados según B35 §4.
En Git Bash, ejecutar desde la raíz del worktree:

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level
sh tools/oam68k_gate.sh > work/b35_asm_pre.log 2>&1
grep 'G2T-B5' work/b35_asm_pre.log
tail -1 work/b35_asm_pre.log
```

Esperado: `RESULTADO: OK` dos veces, seis líneas `ok` de B5 y
`OAM68K: OK`. Las advertencias de 8000 ciclos son el problema de partida;
no borrarlas ni convertirlas en una puerta de rendimiento verde.

Guardar los cuatro hashes de juego y el de logicbench con el bucle
de B35 §5.1; deben ser los de `docs/informe-g2t-b35-1008.md`.

## 3. Reproducir el perfil, antes de implementar

```sh
PROF=1 CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' sh tools/logicbench_build.sh
python tools/g5plan_prof.py --cap work/g5gate/cap_yi1.bin --segw work/g2tb35/segw_yi1.bin --frame 7515 --out work/b35_asm_prof_yi1.json
python tools/g5plan_prof.py --cap work/g5gate/cap_normal.bin --segw work/g2tb35/segw_normal.bin --frame 2198 --out work/b35_asm_prof_normal.json
python tools/g5plan_prof.py --cap work/g5gate/cap_spin_kill.bin --segw work/g2tb35/segw_spin_kill.bin --frame 2140 --out work/b35_asm_prof_spin.json
```

Esperado: aproximadamente 2,40 / 2,31 / 2,41 millones de ciclos;
`g5_attempt` tiene 47,5–49,3 % de ciclos propios. El build PROF deja
visibles también los helpers `s16` y `const g5_seg *`: no atribuirles los
ciclos al símbolo anterior. El informe separa ciclos propios e inclusivos.

## 4. Fase de viabilidad con una puerta de medida

1. Contar el trabajo real por frame: variantes A3 probadas, usos por
   índice, transiciones, intentos de ubicación y segmentos únicos.
   Ya medido: 14 segmentos/frame de media, máximo 39; un segmento del
   C llega a 12 260 ciclos, más que el objetivo del plan completo. Medir el coste
   mínimo de decodificarlos y de producir B1 por separado.
2. Diseñar usos **por índice con filas ordenadas** y acceso directo a
   color y límites. Mantener los empates estables de `transitions/place`.
   Evitar reconstruir Mario y barrer índices ausentes. Estimar bytes,
   número de operaciones y costes con microbenchmarks de 68000.
3. Primera rutina asm propuesta: construir transiciones y ubicar sus
   MOVE (`g5_attempt`, con `g5_use`). Comparar sus estructuras intermedias
   con el C en **todos** los frames antes de sustituir la llamada.
4. Segundo grupo: filtro A3 y recorte por máscaras (`g5_a3`, `g5_bits`).
   Tercero: segmentos y calendario (`g5_segment`, `g5_schedule`, helpers).
   Medir cada grupo antes/después. El perfil no permite prometer que
   solo el primer grupo cerrará el presupuesto.
5. Tras el primer microbenchmark, sumar un presupuesto máximo completo,
   con los componentes todavía en C identificados. Si la propuesta
   exige cambiar el contrato o no deja una ruta medida hacia 8000,
   entregar la prueba de viabilidad y detener la integración.

No fijar una cifra esperada sin distinguir **medido** de **estimado**.
Como hipótesis inicial, una traducción con mejora global de 5–10 veces
ahorraría unos 1,9–2,2 millones de ciclos en el peor frame, pero aún
costaría 0,24–0,48 millones. Hace falta eliminar trabajo repetido,
además de traducir instrucciones.

## 5. Puertas de cada sustitución y del plan completo

El arnés debe poder llamar al C y al asm con las mismas entradas.
Extender `g5plan_verify.py plan` para elegir la implementación, sin
cambiar la referencia ni aceptar tolerancias. Para el C actual:

```sh
CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' sh tools/logicbench_build.sh
for name in yi1 normal spin_kill; do
  python tools/g5plan_verify.py plan --name "$name" --cap "work/g5gate/cap_$name.bin" --segw "work/g2tb35/segw_$name.bin" --ref "work/g2t_ref/plan_$name.bin" --bin work/logicbench.bin --lst work/logicbench.lst
done
```

Esperado: 2288 / 661 / 455 frames, planes distintos 0, ABI distinta 0.
Repetir para asm y sobre el área de trabajo envenenada/reutilizada.
Incluir los negativos: cambiar un WAIT o un color debe ser detectado.
Verificar PIC con el listado real y leer P36/P38/P40/P47/P62/P102 antes
de tocar direcciones o llamadas. Nueva rutina asm pública con cabecera
de registros y preservación d2-d7/a2-a6, incluido a4.

Puerta final: plan completo ≤ 8000 ciclos máximo en las tres trazas,
sin cambios en B4/B5. Si la medida no pasa, el estado es **parcial**.
No activar el plan en vivo ni pasar a D1 por una media menor.

## 6. Memoria y red de seguridad

Vivo actual `SPR_G5` + banco G3: slow libre 191 016 B. `bank.g5env`
133 040 B + `g5_work` 29 952 B dejan **28 024 B estimados**, antes de
foto, salida, caché B2bis y pila. Una representación nueva debe entrar
con **todas** esas reservas; no añadir una caché sin contarla.

Repetir `memmap.py` en replay y vivo, hashes de B35 §5.1, lint,
regress completo (comprobar `test_g5bank_env` en `work/regress.log`) y
OAM68K antes de cada commit de código. No cambiar la base para ocultar
una regresión.

## 7. Paradas e informe

Parar ante un hash por defecto distinto, cambio requerido en modelo o
banco G3, memoria insuficiente, ABI/PIC roto o tres intentos sin cerrar
una puerta. No reducir el objetivo ni la fidelidad.

Informe: commits reales, B4/B5 por traza, ciclos completos y por parte,
ABI, negativos, presupuestos medidos/estimados, memoria con reservas,
hashes, lint/regress/OAM68K y el impedimento concreto si no entra.
Cierre y handoff según ROADMAP §7.
