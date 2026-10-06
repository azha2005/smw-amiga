# G2 — Banco DMA directo y tablas deduplicadas

2026-10-06, sin subagentes. Se cierra el **diseño acotado**, con evidencia
offline; no se completa G3 ni se ha dibujado un Rex nuevo en WinUAE.
Contrato vigente: `diseno-9.2.md` §2 y §5. Diseño anterior archivado en
`archivo/diseno-9.2-2026-10-05.md`.

## Resultado y alcance

Se reprodujeron las trazas yi1/normal/spin_kill actuales, filtrando por dueño
AB/BD/02/B9 para conservar el lote de G3 tras G8b. Los despachos exactos son
AB 4082, BD 594, 02 415 y B9 307. La pertenencia procede de SOT1, cotejada
con la OAM SNES; las reservas se reconstruyen desde VRAM dinámica y ocho
paletas de Mario. No se usan proximidad ni frame como clave residente.

| paso | resultado |
|---|---:|
| peticiones con reservas reales de Mario | 2593 |
| formas observadas / formas incluyendo Rex legal | 43 / 48 |
| descriptores únicos por forma + mapa enemigo | 289 |
| máximo de variantes candidatas por forma | 31 |
| DMA directo sin solapes / con solapes | 66336 / **64528 B** |
| metadata / directorio / total tablas residentes | 71554 / 1162 / **72716 B** |
| margen chip dentro de 65536 B | **1008 B** |
| celdas comparadas en las peticiones originales | **1241670** |
| celdas comparadas tras decodificar el catálogo | **134119** |
| rechazos del lote / diferencias | **0 / 0** |

Cada petición se genera y decodifica con el verificador antiguo, incluyendo
bob intermedio descartable. Después se reconstruye el catálogo desde offsets
**del banco solapado**, se comprueban píxeles, transparencia, orden OAM,
recorte/origen, color SNES→OCS y cada alias contra las reservas originales.
El directorio se vuelve a leer y exige cobertura exacta de los 289 índices.

`work/g2/audit.png`: referencia independiente arriba, DMA decodificado abajo;
mitades idénticas pixel a pixel, además de inspección visual. El PNG y todos
los archivos derivados siguen ignorados por Git. El prototipo SG2A es una
prueba de layout, no un nuevo asset ya integrado en el juego.

## Evaluación previa: una imagen por forma y copper

Sin Mario el banco de 48 formas baja a 4824 B (5104 sin solapes), frente a
10840 B antiguos incluyendo bob. Ese tamaño sería interesante, pero no basta.

Para cada fila real se intersectan los índices permitidos de cada color OCS
entre **todas** las peticiones de la misma forma, con sus reservas Mario.
Se resuelve el matching bipartito completo color→índice. Incluso admitiendo
una asignación distinta en cada fila de la única imagen, **12/43 formas**
no tienen solución. Los testigos completos están en `audit.json`.

Ejemplo: `trace_ab_f5811_m0_291`, fila 6. Los colores opacos `$44D`, `$66D`
y `$88F` solo admiten índices **7 y 15**. Tres colores requieren tres índices
simultáneos; ninguna recarga por fila puede cambiar el bitmap fijo de Mario.
El problema se obtiene con reservas reales, no con la unión de todo GFX32.

Esto descarta la propuesta de una imagen por forma **con recargas por fila**.
Recargas por X podrían aprovechar intervalos disjuntos: siguen sin demostrar
compatibilidad, plazos ni coste junto a `build_mid`. No se probó WinUAE ni
se inventan MOVE/ciclos para esa alternativa. G5a/G6 conservan esa puerta.

## Qué reduce la representación

1. Los antiguos 145600 B chip del lote observado incluían fuentes/máscaras
   bob para cada variante de 15 índices. No son las fuentes PF1 exactas de
   siete índices que necesita G7. Se separan de este banco DMA; su eliminación
   no completa el dibujo de bobs ni su memoria futura.
2. Las reservas de Mario son restricciones de selección desde la foto O5,
   no propiedad de cada descriptor enemigo. Se retiran las entradas 255
   residentes, conservando su comprobación para **cada** petición.
3. Se comparte el descriptor entero por forma y mapa enemigo. Las 2593
   peticiones usan 284 descriptores; las cinco formas Rex que faltan elevan
   el catálogo a 289. Agregar mapas vacíos nuevos para todas las formas
   legales duplicaría variantes que ya son utilizables sin reservas.
4. Los flujos completos comparten bytes idénticos a offsets de 8 B; controles,
   terminadores y padding quedan intactos. 66336→64528 B, sin recodificación
   ni copia por frame. G5 debe tratar el banco como **inmutable**.

El ensayo antiguo completo de tablas medía **1076520 B**; los **693884 B**
del informe G3 correspondían al subconjunto de 1724 descriptores. No se deben
comparar como si ambos cubrieran 2593. La auditoría reproduce ambos límites
relevantes y mide las tablas nuevas sin nombres de replay residentes.

## Memoria y ampliación

`memmap` verifica los listados reales actuales y se aplica su chequeo de
bloques al banco propuesto. Resultado **proyectado**, cero violaciones:

| modo SPR_OAM opt-in | chip + banco | slow + tablas redondeadas + fotos | slow tras C2/C4 |
|---|---:|---:|---:|
| replay | 455232 | 289976 | 425448 |
| vivo | 466760 | 326216 | 461688 |

La proyección concatena metadata y directorio en una reserva slow de 72720 B.
El contrato reserva hasta **98304 B tablas + 32768 B trabajo + 2376 B fotos**.
Tras mover 135468 B CPU (135472 redondeados), vivo deja 137696 B disponibles:
el tope de 133448 B deja 4248 B para crecimiento. El código nuevo debe hacer
pasar el memmap real; la proyección no prueba el loader ni su pico de arranque.
Con los tamaños medidos y todo el trabajo reservado quedarían 494456 B slow.

La ampliación usa las cinco trazas G8b revisadas (banzai, chuck, goal,
shells, stress_piranha), incluyendo las nuevas formas de tipos compartidos:

| muestra, formas nuevas sin reservas de Mario | formas totales | DMA | metadata, antes de directorio |
|---|---:|---:|---:|
| todos los tipos observados | 154 | **81904 B** | 85798 B |
| excluyendo Banzai, que será bob | 148 | **77152 B** | 83526 B |

Incluso excluyendo Banzai excede 65536 B en 11616 B. Estos tamaños **no son
mínimos**: son el coste de extender esta estrategia con un mapa sin Mario
por nueva forma observada. No incluye variantes Mario nuevas, todas las poses
legales, power-ups, partículas adicionales ni fuentes PF1; no demuestra un
banco completo YI1. La memoria de bobs sale del margen chip de §5 del diseño.
Se requiere otra auditoría antes de ampliar el lote.

## Reproducción

Desde la raíz; fuente SMW y oráculos personales disponibles, derivados en
`work/`. El ejemplo conserva el lote YI1 anterior; la auditoría recibe
`--level levels/yi1.json`, no una cabecera inventada.

```sh
mkdir -p work/g2
python3 tools/smwtabx.py
python3 tools/mkmario.py
SRC='player/mario.c player/mcoll.c player/manim.c player/mgfx.c player/mcam.c player/msprite.c player/mspr.c'
gcc -O2 -DNOOAM -DSPR_OAM -Iplayer -o work/g2/host tools/marioverify.c $SRC player/spr_*.c player/gen/smwrom00.c
for name in yi1 normal spin_kill; do
    GAME_OAM_TRACE=work/g2/$name.all.trace work/g2/host work/oracle_$name.bin game > work/g2/${name}_host.log
done
python3 - <<'PY'
import pathlib, struct
for name in ('yi1', 'normal', 'spin_kill'):
    source = pathlib.Path('work/g2/' + name + '.all.trace')
    with source.open('rb') as src, pathlib.Path('work/g2/' + name + '.trace').open('wb') as dst:
        header = src.read(8)
        assert header[:4] == b'SOT1'
        mlen, = struct.unpack_from('<I', header, 4)
        assert 0 < mlen <= 0x8000
        dst.write(header)
        while entry := src.read(8):
            assert len(entry) == 8
            frame, slot, num, first, count = struct.unpack('<IBBBB', entry)
            body = src.read(2 * (0x2000 + mlen))
            assert len(body) == 2 * (0x2000 + mlen)
            if num in (0xab, 0xbd, 0x02, 0xb9):
                dst.write(entry + body)
    source.unlink()
PY
python3 tools/sprgfx_manifest.py --trace work/g2/yi1.trace=work/oracle_yi1_oam.bin --trace work/g2/normal.trace=work/oracle_normal_oam.bin --trace work/g2/spin_kill.trace=work/oracle_spin_kill_oam.bin --out work/g2/base.json
python3 tools/sprgfx_manifest.py --trace work/g2/yi1.trace=work/oracle_yi1_oam.bin --trace work/g2/normal.trace=work/oracle_normal_oam.bin --trace work/g2/spin_kill.trace=work/oracle_spin_kill_oam.bin --mario-rows --out work/g2/variants.json
export VBCC=$HOME/vbcc PY=python3
CDEFS='-DNOOAM -DSPR_OAM' OUT=work/g2_replay sh tools/game_build.sh
CDEFS='-DNOOAM -DSPR_OAM' GDEFS='' OUT=work/g2_live sh tools/game_build.sh
python3 tools/g2_bank_audit.py --level levels/yi1.json --listing work/g2_replay/game.lst --listing work/g2_live/game.lst
python3 tools/g2_bank_audit.py --selftest
python3 tools/test_g2_bank_audit.py
```

Para crecimiento, generar las cinco trazas con el mismo host y pasar
`--growth-trace work/g2/banzai.trace=work/oracle_banzai_oam.bin`, análogamente
para chuck/goal/shells/stress_piranha (goal usa **oracle_goal**, no goal_low).
La prueba de pertenencia rechaza una traza asociada a otro oráculo.
Las trazas originales de revisión son `work/review_<nombre>.trace`; las bases
son `work/review_oam/game.lst` y `work/review_live_oam/game.lst`.

## Validación y límites

Cinco tests negativos/de integración del layout: corrupción de tablas,
offsets chip desalineados, controles/terminadores, padding opaco, identidad
de bytes compartidos, determinismo y rechazo del prototipo por el lector
SG3F/1. Autoprueba G2 y regresión PC/68000 antes/después en verde; baseline
sin cambios. No se modificó código Amiga ni se agregó coste de conversión
por frame. El coste de buscar hasta 31 mapas, las recargas y la simultaneidad
corresponden a G4/G5/G6 y aún no se han medido. No hay ejecutable WinUAE en
este entorno. G5a, DMA real y `--final` G3 siguen pendientes explícitos.

La salida completa de regresión antes y después es idéntica (`cmp`, código 0).
Las mejoras frente al baseline antiguo ya existían al iniciar G2; no se
atribuyen a esta revisión offline y no se actualiza el baseline. Repetir la
auditoría produce los mismos SHA-256 de DMA, tablas, directorio y PNG.

| artefacto local | SHA-256 |
|---|---|
| `audit.dma` | `4dd51fcc9bd03edd9afaad0b0a2459af7113259f43caa8c0789ff457a839f4fc` |
| `audit.sg2a` | `0f38349850187652dbdb15cb4b0f06efe93d5947a30c5cf2dd93af40c7576653` |
| `audit.groups` | `fd565fc0f3d4ee76fcec387658b99fab2e9c6fa77bae73fcbce1fccfe3b7ff15` |
| `audit.png` | `43bb7589bfe6c98a999276ddd53cea93ccce1b3eb72def9af35b744c26b2eeac` |
