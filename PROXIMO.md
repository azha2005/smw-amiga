# PRÓXIMO — lo que sigue

2026-10-08. Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama
`g2t-b2bis`. **Sin merge ni push.** Código de B2b3-5 guardado en `ec320ab`;
clave/decoder en `8a4a43d` y `a401723`.

Se cerraron las puertas locales de B2bis: 3404 frames y 762496 filas
exactos, 258 casos de borde, captura 270 ciclos, cache 558/11904,
reinicios y cuatro memmap verdes. G5ENV, lint, regress con --level,
OAM68K entero y cinco hashes por defecto verdes. Vista WinUAE:
0/327680 píxeles diferentes del control.

**El rendimiento real sigue pendiente:** WinUAE cycle-exact pierde
98 fotos (1,55 %, racha 2) contra 27 del control (0,43 %, racha 1).
La vista compacta bajó de 100 a 98; no alcanza D1. La cota Musashi
0 > PAL no reemplaza esta medida. Vivo G3 deja solo 264 B tras reservas
completas: recuperar margen antes de activar B35 o añadir datos.
Informe: `docs/informe-g2t-b2bis-1008.md`; handoff actualizado:
`docs/handoff-g2t-b2bis-1008.md`.

## 1. La próxima sesión

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G2T-B2bis rendimiento** | perfil frío/cache/vista y memoria; bajar fotos perdidas antes de integrar | `docs/instrucciones-g2t-b2bis-rendimiento.md`: red exacta intacta, control de la misma tanda, no rebajar umbrales ni reservas |
| **G2T-Cpre** | después, emisor con plan precalculado independiente de B35 | `docs/instrucciones-g2t-cpre.md`: C2a control vacío, listas reales exactas y capturas cycle-exact; sin iniciar |

La autorización del usuario es seguir iterando hasta cumplir requisitos.
No tocar modelo, contrato, scroll.s ni banco en B2bis; si el rendimiento
requiere S5/L-OAM, abrir esa tarjeta y leer sus instrucciones primero.
No activar el plan B35 en vivo: la repetición actual cuesta hasta 2423094
ciclos contra 8000. Mantener R9: derivados únicamente en work/.

## 2. Después

Revisar la rama tras cerrar rendimiento y memoria; Cpre/C, rediseño viable
de B35, L-OAM/D1 y OAM de piraña siguen pendientes. Los enemigos todavía
no se ven. El resto del alcance y las estimaciones siguen en ROADMAP.md.

## 3. Pendiente del usuario o la PC

U1: jugar el ADF vivo con teclado/KS1.2/A501. U2: capa 2 contra referencia.
U3 opcional: A500 real. No hace falta autorización adicional para repetir
las puertas ni corregir dentro del alcance de la tarjeta.
