# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.**
> Se reescribe al cerrar cada sesión (`ROADMAP.md` §7); el texto anterior
> está en `docs/archivo/sesiones.md`. Estados: `ROADMAP.md` §1/§4 y
> `SUBAGENTES.md` §4. Ejecución: `docs/instrucciones-olas.md`.

**Escrito el 2026-10-07**, al cerrar la revisión G2T del coordinador.

- **G2T revisión entregada**, sin subagentes: `docs/informe-g2t-1007.md`.
  Tres trazas,3404 frames con Rex. Cambiar solo la selección A5 deja1261
  frames sin plan; ensayo estable incompleto (995 frames sin asignación).
  Cota horizontal8 MOVE:0 sin plan lógico; cota antigua C2:189 sin plan.
  **WinUAE cycle-exact:** ocho recargas desde h=$D0 exactas en el banco
  sintético; control temprano $C0 detecta27 píxeles erróneos. Cruce
  PAL255 con barrera única antes del sufijo:64 ->0 errores. No equivale
  a tener un plan calibrado completo ni un dibujador de enemigos.
- **Contrato candidato A3-T/A5-T/C2-T** en `docs/instrucciones-g2t-a.md`:
  primera variante compatible con plan temporal válido, intervalos X/Y,
  banco inmutable, WAIT+8 MOVE, barrera255 única. **Propuesta pendiente
  de fijar**, antes de implementarla. Segmento +36 B, dos listas +16128 B
  chip estimados (incluye WAIT). No se cambia la puerta roja anterior.
- **G5a-bis sigue detenida en A**, WIP `8fe712d`. Su referencia original
  y tests se incorporan como evidencia, sin modificar A3/A5: resumen
  SHA256 `3d254a01…4722f8b7` reproducido, A2=0, sin_variante=0,
 59318 ventanas vacías. **B/C no iniciadas**.
- **L-OAM mejora parcial integrada**, fusión `cb8ba8f`: Finish y Rex asm,
 6549 llamadas PC=68000, RAM idéntica. WinUAE l4/coord4: YI1 con OAM
 41,2% >40%; back295 fotos contra145 del control, sprites32 contra0.
  Parada original respetada. Revisión de coste aún pendiente;
  `docs/informe-loam-1007.md`, `docs/informe-coordinacion-1007.md`.
- G3 acotada:64528 B DMA/72724 B tablas, banco intacto; chip replay/vivo
 455728/467256 B, slow287712/323944 B. Los enemigos no se dibujan.

---

## 1. La próxima sesión: fijar el contrato y probar toda la fase A-T

**Recomendación; fijar el contrato candidato antes de ejecutar la nueva
tarjeta.** La revisión G2T está entregada; las puertas G5 y L-OAM siguen
rojas. No implementar B/C ni olas dependientes con este estado.

| tarjeta propuesta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **G2T-A: timeline calibrado y puerta horizontal offline** | GPT-6.1 Sol high | `tools/g2t_ref.py` nuevo, tests, `scrollsim.py`, banco sintético | `docs/instrucciones-g2t-a.md`: calibrar slots reales, controles y todas las cargas;3404 frames,0 sin_variante_temporal/sin_plazo/errores_color/capa1/prioridad. Banco≤65536, tablas≤98304, trabajo≤32768. Repetición e imágenes del coordinador antes de B/C |
| **L-OAM: revisar margen y nueva tarjeta acotada** | GPT-6.1 Sol high | informes/perfiles, inicialmente lectura | `docs/instrucciones-revision-1007.md` §1: diagnóstico de41,2%/estrés y propuesta acotada; conservar≤40% y estrés no peor que control; no ampliar funciones sin instrucciones nuevas |

Preflight: entorno PC, lint, regress `--baseline tools/baseline_pc.json
--level`, OAM68K verdes; worktree por tarjeta. WinUAE cycle-exact por
candado, controles en la misma tanda y solo PIDs propios. Cada commit
pasa red de seguridad; cierre ROADMAP§7, nada sin commitear.

## 2. Después, en orden

1. Nueva A-T verde y L-OAM resuelta; escribir las instrucciones B/C
   con el contrato temporal medido y cerrar G5a-bis.
2. G4+G6, luego G5+G9, con todos los enemigos del lote G3.
3. Estrés con G5 y S5 inmediatamente después; compuerta D1 sin rebajas.
4. C2/C4 para liberar tablas CPU de chip; segundo PF1 y G7.
5. Según dependencias: S8, P7/P9/P10, A0/A2, H2-H4 y T1.

## 3. Pendiente del usuario o de la PC

- Fijar el contrato candidato temporal G2T-A; el informe ya contiene
  alternativas, evidencia y límites. Mantener fidelidad y50Hz.
- U1: jugar `work/live/game.adf` con teclado, KS1.2,512KB chip+512KB slow.
  Enemigos aún no dibujados; diagnósticos si congela.
- U2: comparación de capa2 contra la referencia (`cmp_ref.py`).
- U3 opcional: A500 real.
- No push hasta indicación explícita del usuario.
