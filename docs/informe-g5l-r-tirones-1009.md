# G5L-R-T — dos candidatos y parada (2026-10-09)

Rama `g2t-b2bis`. La tarjeta se detiene en su puerta explícita: **dos
candidatos medidos no bajan de unas 55 fotos perdidas**. D1 sigue roja.
Se conserva únicamente la caché compartida, con mejora marginal en esta
tanda; no se presenta como una solución de los tirones.

## WinUAE PAL cycle-exact, KS 1.2 + A501

Todas las filas BENCH llevan SPR_OAM en el C y CUSHION. Capturas en
`work/session/`, ignoradas por git, leídas con `game_read.py --auto`.

| build | fotos perdidas / 6312 | racha | VBL repetidos |
|---|---:|---:|---:|
| `base` (código inicial G5L) | 67 (1,06 %) | 1 | 69 |
| `shared` (último parche compartido entre listas) | 66 (1,05 %) | 1 | 68 |
| `special` (máscaras XOR especializadas) | 65 (1,03 %) | 2 | 67 |
| `control-spr` (sin G5L, con CUSHION y SPR_OAM) | 9 (0,14 %) | 1 | 11 |

El 27 citado en la tarjeta era el control anterior; no tenía esta
configuración de tres listas. El control `control` construido inicialmente
en esta sesión dio 14, pero carecía de SPR_OAM y se descartó como comparación.
El control sin G5L también tiene listas de otro tamaño: el exceso no puede
atribuirse exclusivamente a los XOR del Rex.

## Cambios y coste CPU

La caché compartida añade una clave de 46 B y un puntero de 4 B en slow.
Apunta al último búfer de lista parcheado; mientras esa clave siga vigente,
se copian solo las mitades afectadas. No añade chip RAM ni modifica DMA
que esté en uso. La clave por lista conserva su camino de acierto.

La especialización de máscaras redujo `patch` máximo de 18.804 a 14.646
ciclos sin DMA, pero dejó una racha de dos fotos. Se retiró. Código fuente
de la prueba y binarios solo en work/; no queda compilado en la entrega.

Perfil final de tres listas sin BENCH ni STOPF, `gate-final` (Musashi):
6313 fotos, G5L GAME OK; listas y píxeles DMA exactos, ABI intacta.

| rutina | media en sus llamadas | máximo, ciclos sin DMA |
|---|---:|---:|
| fast | 5.334 | 13.210 |
| sweep | 10.635 | 18.014 |
| plan | 8.648 | 15.366 |
| patch | 1.262 | 19.094 |
| place | 4.357 | 10.046 |
| emit | 3.677 | 8.852 |

Render total: media 10.477,6, máximo 93.752 ciclos en frame del oráculo
6755. La base de tres listas dio media 10.476,5 y máximo 93.462: la
caché compartida no mejora el perfil CPU global. No extrapolar Musashi
a DMA ni sumar máximos de frames distintos. Ninguno de estos candidatos
ha demostrado el objetivo de 55.

## Traza visible sin BENCH

`vt` lleva VBTRACE sin BENCH. `vbtrace.py ... 175` leyó 6722 filas:
26 repeticiones (una es el arranque en 0), **25 fotos omitidas**.
Esta instrumentación tiene otro coste que BENCH; sus 25 no se comparan
directamente con 66. Frames omitidos del replay:

```
1044 1127 1673 1711 2076 2078 2460 2630 2757 2794
3308 3311 3313 3328 3331 3345 3350 3364 4043 4217
4221 4559 4567 5445 5854
```

Reproducen el daño de Mario en 3305–3364 (8 saltos) y los grupos
1041–1127, 1670–1711, 2073–2078, 4214–4221 y 4556–4567.
Las parejas repetir/saltear siguen separadas por aproximadamente tres
frames. Próxima palanca propuesta: medir fast fallido/sweep durante daño
y el presupuesto completo de `build_mid`, antes de otro candidato.
Hace falta autorización para superar la parada de esta tarjeta.

## Red de seguridad

`lint_port.py`, `regress.py --baseline tools/baseline_pc.json --level`,
OAM68K y G5L GAME (dos/tres listas): OK. La comparación visual de frame
1700 con control + referencia Rex dio **0/327680 píxeles distintos**
(`bm2fixed/check.json`); el arranque BM es una tarjeta aparte.

Los cinco MD5 de `game.bin` antes/después, con CDEFS=-DNOOAM:

| modo | MD5 sin cambios |
|---|---|
| REPLAY | `8d567edf313dc0962396f1373e516132` |
| vivo | `5de846a6b0b82d85abc7e913fcb8fcaf` |
| REPLAY BENCH | `e669b2af1e097d0763fdef09ef5ccdfb` |
| REPLAY DECOUPLE | `8d567edf313dc0962396f1373e516132` |
| REPLAY DECOUPLE BENCH | `e669b2af1e097d0763fdef09ef5ccdfb` |
