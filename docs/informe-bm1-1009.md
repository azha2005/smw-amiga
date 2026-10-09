# BM1 — medición de Exec y loader MFM opt-in (2026-10-09)

Rama `g2t-b2bis`. **WIP: KS 1.2/A501 verde; KS 1.3, política sin A501
y comparación de tiempo contra trackdisk pendientes**. Se conserva el
boot y el build normales. `tools/bm_build.sh` produce un ADF aparte.
No hay mejora de CPU afirmada: el SO ya estaba dormido durante el juego.

## 1. Chip retenida, medida en la máquina emulada

`-DREPLAY -DG5L -DCUSHION -DMEMPROBE` guarda AvailMem antes del primer
AllocMem propio y después del último. `memprobe.py --pid ... --out ...`
leyó la firma de la instancia propia, KS 1.2, PAL cycle-exact, 512+512 KB.
`work/session/memprobe/result.json` contiene:

| | chip libre / mayor bloque | fast libre / mayor bloque |
|---|---:|---:|
| entrada | 106008 / 106008 B | 499200 / 499176 B |
| final | 17464 / 17464 B | 97152 / 97128 B |

Stage2 redondeado: 395264 B, dirección chip 23016. Retenido total:
524288 − 106008 − 395264 = **23016 B**. Esto incluye la reserva inferior,
Exec, librerías y trackdisk. MemList tiene dos encabezados: chip lower
1056/upper524288; slow lower12584168/upper13101056. Sus campos no guardan
propietario de asignaciones: **no permiten separar honestamente** bytes
de Exec, librerías y trackdisk. El búfer de 12 KB de la tarjeta era estimado,
no una medición individual. No se atribuye a ese búfer el total medido.

La arena nueva reserva 4096 B inferiores: recupera **18920 B** frente a
este control. Supera la parada de 16 KB, por lo que se continuaron fases 2–4.

## 2. Supervisor y carga MFM

`boot_bm.s` toma el hardware, entra mediante TRAP a supervisor, instala
su pila y se copia a C7F000. El lector hace motor, home, seek/side, DMA
MFM WORDSYNC $4489 en chip 7A000 (13312 B), timeout y hasta tres intentos,
decodifica los once sectores y verifica checksums de cabecera/datos.
La pista decodificada reside en C7D000: solo la lee la CPU. Stage2 se
carga directamente a C00000; los datos del nivel a chip 1000.

El scratch DMA se usa **antes** de asignar PF/listas y se libera al apagar
el motor; puede ser reutilizado por estas reservas. No hay lecturas de
disco posteriores durante el juego. `BM_FIXED` sustituye GALLOC por arenas
alineadas a 8 B, omite Exec/trackdisk/graphics y habilita IRQ solo después
de instalar vectores. Mantiene INTENA en los reinicios. `BM_SUPERVISOR`
también permite la fase intermedia con Exec; no es el build normal.

Referencias del formato/registros: [Hardware Reference Manual](https://www.ikod.se/wp-content/uploads/2020/08/Amiga_Hardware_Reference_Manual_3rd_Edition.pdf)
y [Amiga Test Kit, formato de sectores](https://raw.githubusercontent.com/keirf/Amiga-Stuff/master/testkit/floppy.c).

## 3. Puertas verificadas

`mfm_verify.py`: **70 casos exactos**, pistas 0/1/42/79/80/158/159,
sectores en orden arbitrario, uno/dos sync, corrupción de cabecera/datos,
pista incorrecta y sector ausente. Máximo 246386 ciclos sin DMA para
decodificar; no representa todo el tiempo mecánico de carga.
`memmap.py --selftest`: 17 casos, incluyendo invasión de scratch MFM y
del espacio slow del loader. El parser reconoce expansiones `3M` de vasm,
sin omitir llamadas GALLOC. `regress.py --bm1` recompila el build en vivo
y ejecuta decoder, selftest, memmap y reinicios.

KS 1.2 + A501, WinUAE cycle-exact:

| evidencia en work/session | resultado |
|---|---|
| `bm2fixed/shot.png` | replay frame 1700, Mario y Rex visibles |
| `bm2fixed/check.json` | control + referencia Rex: **0/327680 px distintos** |
| `bm2fixed/probe.json` | SR2000; **230180 bytes de datos exactos** en chip real |
| `bm-live-final/shot.png` | vivo cargado y funcionando |
| `bm-live-final/probe.json` | SR2000; 230180 bytes exactos; datos en 1000 |
| `bm-z1/shot.png` | Z1STOP=411, X0010/Y0160, $71=00: muerte y reinicio con boot final |
| `bm-no-a501.png` | sin slow RAM: fallo rojo estable, sin Guru |

La primera prueba sin habilitar IRQ quedó inmóvil; se corrigió SR2700→2000
después de instalar vectores y se repitió. No es evidencia de éxito.

TOD de CIA-A reiniciado al entrar en el loader (50 VBL/s PAL):
stage2 **1031 ticks = 20,62 s**, stage2 + datos **1612 ticks = 32,24 s**.
Incluye motor/seek/DMA/decodificación, excluye espera inicial de Kickstart
y scroll_init. Todavía no se instrumentó el control trackdisk con los
mismos extremos: **no se afirma que este loader sea más rápido**.

## 4. Mapa fijo

| modo | chip persistente, incluida reserva inferior | margen chip | slow, incluida reserva loader |
|---|---:|---:|---:|
| replay (`bm2fixed`) | 487904 B | 36384 B | 417784 B |
| vivo (`bm-live-final`) | 499432 B | 24856 B | 454072 B |

`memmap.py ... --data work/yi1_s_g5.dat`: cero violaciones. Vivo: arena
chip termina en 079EE8 y slow en C6ADB8. Reserva superior slow C7C000..C80000
para pista/pila/boot; código de boot por debajo de 1024 B (se vuelve a
comprobar en cada build). Pico chip de lectura de datos: 247808 B.
Todavía quedan 135468 B de tablas CPU en chip; BM1 no sustituye C2/C4.

## 5. Pendiente antes de declarar BM1 completa

Solo existe `Downloads/amivideo/kick12.rom`; se pidió ruta de KS 1.3 y no
se encontró otra en la búsqueda de ROMs local. No se descargó ninguna.
Falta arranque 1.3 y comparación de datos/imagen con la misma puerta.

El nuevo boot detecta patrones en C7F000 y ausencia/espejo C00000/C80000;
requiere A501 y muestra borde rojo si falla. Es **opt-in**. La ruta normal
conserva exactamente su comportamiento anterior sin A501. La tarjeta
pide soporte sin expansión o decisión del usuario: esa política sigue
pendiente; no se hace defecto el boot nuevo.

Faltan teclado real/RETURN (helper de Windows sin conexión) y el tiempo
trackdisk comparable. Los cinco builds
normales siguen los MD5 del informe T; BM_FIXED no cambia sus bytes.
