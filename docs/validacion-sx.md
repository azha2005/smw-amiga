# Validación visual de SX/SX2 en WinUAE

Banco preparado el 2026-10-05 para cerrar el pendiente 5 del handoff de la
ola 3 (2026-10-04). `tools/sxverify.py` construye 24 ADF: seis posiciones
(500, 1000, 1700, 2500, 3500, 4500), ida y vuelta, antes y después de SX/SX2.

La referencia anterior es `68e2d1e:player/scroll.s` (S2, antes de SX); se
extrae a `work/sxverify/scroll-baseline.s` sin cambiar la rama ni el código
actual. Ambos usan el mismo `yi1_s.dat`, bootblock y parámetros: 256×224,
PAL, 512 KB chip + 512 KB slow, KS 1.2, `SPEED=2`. El manifiesto guarda
SHA-256 de fuentes, datos y cada ADF. Esta comparación aísla SX/SX2;
no reconstruye todos los assets históricos del commit de referencia.

En la ida, `S0=max(0,STOPX-512)` recorre hasta 512 px antes del recorte.
En la vuelta, `S0=0`, `RETURN=4864` y `STOPX` obligan a recorrer toda la
ida y regresar hasta el punto de captura: se conserva el historial que
exige P71. No se compara una imagen inicial tomada directamente en STOPX.

Cada ADF produce dos fotos separadas por diez segundos. Se exige que
los 256×224 píxeles del juego estén estables y que el encuadre coincida
mejor con STOPX que con STOPX±2 y STOPX±16. Las fotos se esperan con
70 segundos de margen sobre distancia / (50×2), redondeado a diez segundos.
El tiempo de espera no constituye una medida de rendimiento.

La configuración archivada de cada captura exige `cycle_exact=true`,
`cpu_speed=real`, `immediate_blits=false` y `ntsc=false`. Cada worker usa
su copia privada de `shot.ps1`, con configuración y log independientes.
Las capturas de esta sesión usan WinUAE 6.0.0.0. El launcher arranca oculto
y habilita el dibujo de su ventana al fondo, sin activarla; enumera el HWND
por PID y envía WM_CLOSE únicamente a esa ventana al terminar.
Se ejecutan como máximo dos workers de este banco, bajo el candado
compartido `winuae_lock.ps1` (tres slots en total, uno reservado para G0).

La comparación contra el PC llama a `scroll_check.py --sc 2 --mid`.
Se muestrea el centro de cada píxel (P57), se conserva el origen calculado
y se apilan referencia / captura / diferencias. El antes/después también
se alinea por píxeles del juego y se apila en `pair_<dirección>_<x>.png`.
La puerta de fidelidad exige que ninguna posición aumente los errores
que no se explican por un vecino respecto a la referencia anterior.

## Reproducir

```powershell
python tools/sxverify.py --build
# En dos procesos independientes como máximo:
powershell -NoProfile -File work/sxverify/capture_baseline.ps1
powershell -NoProfile -File work/sxverify/capture_current.ps1
python tools/sxverify.py --compare
# También se puede comparar mientras avanzan los workers:
python tools/sxverify.py --compare --wait 600
```

`--build` requiere vasm, el decompilado convertido en `work/yi1_s.dat`
y `work/yi1_d.dat`, y el commit de referencia accesible en git. `--vasm`
permite elegir el ensamblador; `--lock` permite elegir el candado compartido.
`--compare` requiere Pillow y numpy. Los derivados y capturas quedan en
`work/sxverify/`, excluido de git por R9.

## Resultados

2026-10-05, WinUAE 6.0.0.0 cycle-exact, 24 capturas (tres workers en
paralelo, cada uno con su copia de `shot.ps1`). "PC" = píxeles distintos
del render del PC que no explica un vecino; "parpadeo" = píxeles que cambian
entre las dos fotos (la clave `stable_bad` de `results.json`).

| s | antes de SX (`68e2d1e`) | SX sin P51 (`afb3658`) | SX + P51 (`0361736`) |
|---|---|---|---|
| ida 500, 1000, 2500, 3500 | 0 | 0 | 0 |
| vuelta 500, 1000, 2500, 3500 | 0 | 0 | 0 |
| ida 1700 | 43 | 6, con parpadeo 6 | **0** |
| vuelta 1700 | 44 | 43 | **0** |
| ida 4500 / vuelta 4500 | 45 / 45 | 45 / 45 | 45 / 45 |

**Las dos puertas pasan con P51** (encuadre en STOPX mejor que ±2 y ±16
en las 24 capturas; ninguna posición empeora respecto de antes de SX).
Sin P51 fallaba la de captura: en la ida a 1700 las listas A y B daban
imágenes distintas (6 píxeles alternantes).

Los 43 píxeles de la vuelta a 1700 (líneas 162-172 en x = 247-249 y
176-186 en x = 247) los predice `scrollsim.py` con el modelo de P51 sobre
el `scroll.s` anterior, línea por línea, y con el arreglo predice 0: la
misma cuenta que dio la captura. Los 45 de s = 4500 son la zona densa de
S5 (cargas que ya llegan tarde en el plan), iguales en las tres versiones.
