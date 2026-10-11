# ARQ-0 (docs/informe-arq-0-1011.md): P2(a): segmentos del copper precalculados por camara (MLD de yi1_s.dat)
# correr desde la raiz: python tools/arq0/p2a.py
import struct, collections
raw = open('work/yi1_s.dat', 'rb').read()
W = struct.unpack_from('>H', raw, 4)[0]
BLK, MAP, INI, CHG, L2B, L2P, MLX, MLD, LNS, _ = struct.unpack_from('>10I', raw, 16)
LASTX = 255; LINES = 224
mlx = struct.unpack_from('>225H', raw, MLX)
def rec(i):
    return struct.unpack_from('>HHHHhh', raw, MLD + 12 * i)
# MLX: indice (o desplazamiento) de la primera carga
print('MLX[0..3]', mlx[:4], 'MLD bytes', LNS - MLD, 'registros', (LNS - MLD) // 12)
lines = []
for L in range(LINES):
    i = mlx[L] // 12 if mlx[L] % 12 == 0 and mlx[1] > 12 else mlx[L]
    lines.append(i)
# averiguar la unidad de MLX: el registro anterior a la primera carga debe ser el centinela $FFFF
u = None
for unit in (1, 12):
    ok = all(rec(mlx[L] // unit - 1)[1] == 0xFFFF for L in range(LINES) if mlx[L] // unit > 0)
    if ok: u = unit
print('unidad MLX', u)
SZ = {0: 8, 1: 4, 2: 8, 3: 12}
tot_iv = tot_bytes = 0; per_line = []; maxload = 0; tot_loads = 0
SMAX = W - 256
for L in range(LINES):
    i = mlx[L] // u
    loads = []
    while True:
        c, x, r, col, a, b = rec(i)
        if x == 0x7FFF: break
        loads.append((x, c, a, b)); i += 1
    tot_loads += len(loads)
    xs = [l[0] for l in loads]
    s = 0; n = 0; byt = 0; distinct = set()
    while s <= SMAX:
        w = [l for l in loads if s <= l[0] <= s + LASTX]
        nxt = [x for x in xs if x > s + LASTX]
        end = SMAX + 1
        if nxt: end = min(end, nxt[0] - LASTX)
        tarde = False
        for x, c, a, b in w:
            if c >= 4: tarde = True
            else: end = min(end, s + b)
        if tarde: end = min(end, (s & ~7) + 8)
        end = max(end, s + 1)
        if w:
            key = tuple((x, c, (x - s) >> 3 if c in (0, 4) else 0) for x, c, a, b in w)
            if key not in distinct:
                distinct.add(key); byt += sum(SZ[c & 3] for x, c, a, b in w) + 4
            maxload = max(maxload, len(w))
        n += 1
        s = end
    per_line.append((n, len(distinct), byt))
    tot_iv += n; tot_bytes += byt
print('ancho', W, 'cargas', tot_loads, 'max cargas en pantalla por linea', maxload)
print('intervalos (reescrituras al barrer el nivel a 1 px): %d; segmentos distintos: %d; bytes %d (%.1f KB)'
      % (tot_iv, sum(p[1] for p in per_line), tot_bytes, tot_bytes / 1024))
big = sorted(range(LINES), key=lambda L: -per_line[L][2])[:5]
print('lineas mas caras:', [(L, per_line[L]) for L in big])
