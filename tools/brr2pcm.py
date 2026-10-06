#!/usr/bin/env python3
"""BRR SNES -> PCM raw de 8 bits firmado para Paula (sin normalizar).

python3 tools/brr2pcm.py muestra.brr --out muestra.pcm --loop-offset 36
python3 tools/brr2pcm.py sound/samples --out work/pcm --manifest work/pcm.json
python3 tools/brr2pcm.py --selftest --reference-dsp /ruta/src/snes/dsp.c

Un bloque BRR ocupa 9 bytes y produce 16 muestras. Los offsets de loop
son bytes relativos al BRR, excluido el prefijo opcional --loop-header.
El bit loop sólo tiene efecto junto a end. La historia se conserva al
repetir un loop; --loops permite verificar/renderizar repeticiones finitas.
No se emulan interpolación gaussiana, ADSR, mezcla ni eco del DSP.
"""

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import random
import struct
import subprocess
import tempfile


@dataclass(frozen=True)
class Decoded:
    pcm16: tuple
    blocks: int
    end: bool
    loop: bool
    loop_sample: int | None
    trailing_bytes: int

    @property
    def pcm8(self):
        # El byte alto firmado, sin sumar 128 ni corregir la media natural.
        return bytes((sample >> 8) & 255 for sample in self.pcm16)


def decode_block(block, history=(0, 0)):
    """Devuelve PCM16 y (última, penúltima) en el dominio interno de 15 bits."""
    if len(block) != 9:
        raise ValueError("un bloque BRR debe contener exactamente 9 bytes")
    old, older = history
    if not all(-16384 <= h <= 16383 for h in history):
        raise ValueError("historia fuera del rango firmado de 15 bits")
    shift, filt = block[0] >> 4, (block[0] >> 2) & 3
    samples = []
    for packed in block[1:]:
        for nibble in (packed >> 4, packed & 15):
            signed = nibble if nibble < 8 else nibble - 16
            value = (signed << shift) >> 1 if shift <= 12 else (-4096 if signed < 0 else 0)
            if filt == 1:
                value += old + ((-old) >> 4)
            elif filt == 2:
                value += 2 * old + ((-3 * old) >> 5) - older + (older >> 4)
            elif filt == 3:
                value += 2 * old + ((-13 * old) >> 6) - older + ((3 * older) >> 4)
            # El DSP satura a 16 bits y DESPUÉS envuelve a 15 bits.
            value = max(-32768, min(32767, value))
            value = ((value + 16384) & 32767) - 16384
            older, old = old, value
            samples.append(value * 2)
    return tuple(samples), (old, older)


def decode_brr(data, loop_offset=None, loops=0, history=(0, 0)):
    """Decodifica hasta el primer end, o EOF; loops es número de vueltas extra."""
    if not data or len(data) % 9:
        raise ValueError("BRR vacío o truncado: se requieren bloques completos de 9 bytes")
    if loops < 0:
        raise ValueError("loops debe ser >= 0")
    if loop_offset is not None and (loop_offset < 0 or loop_offset % 9 or loop_offset >= len(data)):
        raise ValueError("loop offset debe apuntar al inicio de un bloque BRR")
    first_end = next((i for i in range(0, len(data), 9) if data[i] & 1), None)
    end_offset = first_end + 9 if first_end is not None else len(data)
    end = first_end is not None
    loop = end and bool(data[first_end] & 2)
    if loop and loop_offset is not None and loop_offset >= end_offset:
        raise ValueError("loop offset apunta después del bloque end")
    if loops and (not loop or loop_offset is None):
        raise ValueError("repetir exige end+loop y un loop offset conocido")
    samples = []
    spans = [(0, end_offset)] + [(loop_offset, end_offset)] * loops
    for start, stop in spans:
        for pos in range(start, stop, 9):
            block_samples, history = decode_block(data[pos:pos + 9], history)
            samples.extend(block_samples)
    return Decoded(tuple(samples), len(samples) // 16, end, loop,
                   loop_offset // 9 * 16 if loop and loop_offset is not None else None,
                   len(data) - end_offset)


def _reference_block(block, history):
    """Oráculo independiente por coeficientes racionales, dominio PCM16."""
    coefficients = ((), ((1, 2, 0), (-1, 32, 0)),
                    ((1, 1, 0), (-3, 64, 0), (-1, 2, 1), (1, 32, 1)),
                    ((1, 1, 0), (-13, 128, 0), (-1, 2, 1), (3, 32, 1)))
    previous = [history[0] * 2, history[1] * 2]
    result = []
    for index in range(16):
        n = (block[1 + index // 2] // (16 if index % 2 == 0 else 1)) % 16
        n = (n + 8) % 16 - 8
        r = block[0] // 16
        value = (n * 2 ** r) // 2 if r < 13 else (n // 8) * 4096
        value += sum((numerator * previous[h]) // denominator
                     for numerator, denominator, h in coefficients[(block[0] // 4) % 4])
        value = max(-32768, min(32767, value))
        pcm = 2 * ((value + 16384) % 32768 - 16384)
        previous = [pcm, previous[0]]
        result.append(pcm)
    return tuple(result), (previous[0] // 2, previous[1] // 2)


def _compile_reference(dsp_path, temporary):
    """Compila la función original sin modificarla, contra su dsp.h original."""
    dsp_path = Path(dsp_path).resolve()
    source = dsp_path.read_text()
    start = source.rfind("static void dsp_decodeBrr(Dsp* dsp, int ch) {")
    if start < 0:
        raise ValueError("no se encuentra dsp_decodeBrr de snesrev en la referencia")
    depth, stop = 0, None
    for index in range(source.index("{", start), len(source)):
        depth += (source[index] == "{") - (source[index] == "}")
        if depth == 0:
            stop = index + 1
            break
    if stop is None:
        raise ValueError("función de referencia incompleta")
    harness = r'''
#include "dsp.h"
REFERENCE_FUNCTION
int main(void) {
  uint8_t ram[65536] = {0};
  Dsp dsp = {0};
  uint32_t size, calls, loop;
  int16_t history[2];
  if (fread(&size, 4, 1, stdin) != 1 || fread(&calls, 4, 1, stdin) != 1 ||
      fread(&loop, 4, 1, stdin) != 1 || fread(history, 2, 2, stdin) != 2 ||
      size > 65024 || fread(ram + 256, 1, size, stdin) != size) return 2;
  dsp.apu_ram = ram;
  dsp.channel[0].decodeOffset = 256;
  dsp.channel[0].old = history[0];
  dsp.channel[0].older = history[1];
  ram[2] = (256 + loop) & 255;
  ram[3] = (256 + loop) >> 8;
  for (uint32_t block = 0; block < calls; block++) {
    dsp_decodeBrr(&dsp, 0);
    for (int i = 3; i < 19; i++) {
      int16_t pcm = dsp.channel[0].decodeBuffer[i] * 2;
      if (fwrite(&pcm, 2, 1, stdout) != 1) return 3;
    }
  }
  return 0;
}
'''.replace("REFERENCE_FUNCTION", source[start:stop])
    cfile, executable = Path(temporary) / "reference.c", Path(temporary) / "reference"
    cfile.write_text(harness)
    subprocess.run(["cc", "-std=c99", "-O2", "-I", str(dsp_path.parent),
                    str(cfile), "-o", str(executable)], check=True, capture_output=True)
    return executable


def _reference_decode(executable, data, blocks, loop_offset=0, history=(0, 0)):
    request = struct.pack("=IIIhh", len(data), blocks, loop_offset, *history) + data
    output = subprocess.run([str(executable)], input=request, capture_output=True, check=True).stdout
    if len(output) != blocks * 32:
        raise AssertionError("longitud inesperada de la referencia C")
    return struct.unpack("=" + "h" * (blocks * 16), output)


def selftest(reference_dsp=None, sample_files=()):
    if not __debug__:
        raise ValueError("--selftest necesita Python sin -O para ejecutar sus comprobaciones")
    rng = random.Random(0x425252)
    # Incluye todos los nibbles, rangos válidos/ilegales, filtros e historias extremas.
    vectors = []
    histories = ((0, 0), (16383, -16384), (-16384, 16383), (1, -1))
    for header in range(0, 256, 4):
        for history in histories:
            for payload in (bytes.fromhex("0123456789abcdef"), bytes([0x77] * 8),
                            bytes([0x88] * 8), rng.randbytes(8)):
                vectors.append((bytes([header]) + payload, history))
    for block, history in vectors:
        assert decode_block(block, history) == _reference_block(block, history)
    assert decode_brr(bytes([1]) + bytes(8)).pcm8 == bytes(16)
    polarity = decode_brr(bytes([0xc1]) + bytes([0x78] * 8)).pcm8
    assert polarity == bytes([112, 128] * 8)
    saturated, _ = decode_block(bytes([0xc9]) + bytes([0x77] * 8), (16383, -16384))
    assert saturated[0] == -2  # clamp + wrap, distinto de saturar a 15 bits.
    # End detiene, loop aislado no salta y la historia no se reinicia entre bloques/vueltas.
    chain = bytes([0x80]) + rng.randbytes(8) + bytes([0x87]) + rng.randbytes(8)
    once = decode_brr(chain, 9)
    repeated = decode_brr(chain, 9, 2)
    assert len(once.pcm8) == 32 and len(repeated.pcm8) == 64
    assert repeated.loop_sample == 16 and repeated.pcm16[32:48] != repeated.pcm16[16:32]
    assert decode_brr(chain + bytes(9), 9).trailing_bytes == 9
    assert decode_brr(bytes([2]) + bytes(8) + bytes([1]) + bytes(8)).blocks == 2
    for data, offset, loops in ((b"", None, 0), (bytes(8), None, 0),
                                (chain, 1, 0), (chain, 18, 0), (chain, None, 1),
                                (bytes([1]) + bytes(8), 0, 1), (chain, 9, -1)):
        try:
            decode_brr(data, offset, loops)
        except ValueError:
            pass
        else:
            raise AssertionError("entrada inválida aceptada")
    print(f"Autoprueba: {len(vectors)} bloques, filtros 0-3, rangos 0-15, end/loop/PCM firmado OK")
    if reference_dsp:
        with tempfile.TemporaryDirectory(prefix="brr-reference-") as temporary:
            executable = _compile_reference(reference_dsp, temporary)
            for block, history in vectors:
                assert decode_block(block, history)[0] == _reference_decode(executable, block, 1, history=history)
            assert repeated.pcm16 == _reference_decode(executable, chain, repeated.blocks, 9)
            total, correlations = 0, []
            for path in sample_files:
                data = path.read_bytes()
                result = decode_brr(data)
                assert result.pcm16 == _reference_decode(executable, data, result.blocks)
                total += len(result.pcm8)
                # Pérdida de cuantización: PCM8 reexpandido frente a la referencia PCM16.
                x, y = result.pcm16, tuple((b if b < 128 else b - 256) * 256 for b in result.pcm8)
                n = len(x)
                variance_x = n * sum(a * a for a in x) - sum(x) ** 2
                variance_y = n * sum(b * b for b in y) - sum(y) ** 2
                if variance_x and variance_y:
                    correlations.append((n * sum(a * b for a, b in zip(x, y)) - sum(x) * sum(y)) /
                                        (variance_x * variance_y) ** 0.5)
            print(f"Referencia C original: {len(vectors)} bloques + loop con historia + "
                  f"{len(sample_files)} muestras/{total} bytes PCM, 0 diferencias PCM16")
            if correlations:
                print(f"Correlación mínima PCM8/PCM16 referencia: {min(correlations):.8f} "
                      "(cuantización; no comparación contra WAV R8)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="*", type=Path, help="BRR raw o directorios (*.brr)")
    parser.add_argument("--out", type=Path, help="fichero PCM para una entrada; directorio para varias")
    parser.add_argument("--manifest", type=Path, help="metadatos JSON y presupuesto total")
    parser.add_argument("--loop-offset", type=lambda s: int(s, 0), help="offset BRR del loop, una entrada")
    parser.add_argument("--loop-header", action="store_true", help="leer prefijo LE de 2 bytes con offset loop")
    parser.add_argument("--loop-map", type=Path, help="JSON {nombre.brr: offset_bytes} para lotes raw")
    parser.add_argument("--loops", type=int, default=0, help="vueltas adicionales para render/verificación")
    parser.add_argument("--budget", type=int, default=65536, help="presupuesto PCM en bytes (default 65536)")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--reference-dsp", type=Path, help="dsp.c snesrev original para autoprueba C independiente")
    args = parser.parse_args()
    try:
        files = sorted(p for entry in args.inputs for p in
                       (sorted(entry.glob("*.brr")) if entry.is_dir() else [entry]))
        if args.inputs and not files:
            raise ValueError("no se encontraron muestras *.brr")
        if args.reference_dsp and not args.selftest:
            raise ValueError("--reference-dsp requiere --selftest")
        if args.selftest:
            if args.loop_header and args.reference_dsp and files:
                raise ValueError("autoprueba C de ficheros exige BRR raw sin prefijo")
            selftest(args.reference_dsp, files)
        if not files:
            if not args.selftest:
                parser.error("indica entradas o --selftest")
            return 0
        if args.budget < 0:
            raise ValueError("budget debe ser >= 0")
        if args.loop_offset is not None and (len(files) != 1 or args.loop_header or args.loop_map):
            raise ValueError("--loop-offset exige una entrada y no admite otras fuentes de loop")
        if args.loop_header and args.loop_map:
            raise ValueError("--loop-header y --loop-map son excluyentes")
        loop_map = json.loads(args.loop_map.read_text()) if args.loop_map else {}
        if not isinstance(loop_map, dict):
            raise ValueError("loop-map debe ser un objeto JSON")
        if len({p.stem for p in files}) != len(files):
            raise ValueError("nombres de salida duplicados en el lote")
        results = []
        for path in files:
            data = path.read_bytes()
            offset = loop_map.get(path.name, args.loop_offset)
            if args.loop_header:
                if len(data) < 2:
                    raise ValueError("prefijo loop incompleto")
                offset, data = int.from_bytes(data[:2], "little"), data[2:]
            if offset is not None and (not isinstance(offset, int) or isinstance(offset, bool)):
                raise ValueError("offset de loop debe ser entero")
            result = decode_brr(data, offset, args.loops)
            metadata = {"input": str(path), "brr_bytes": len(data), "pcm_bytes": len(result.pcm8),
                        "blocks": result.blocks, "end": result.end, "loop": result.loop,
                        "loop_brr_offset": offset if result.loop else None,
                        "loop_pcm_offset": result.loop_sample, "trailing_bytes": result.trailing_bytes}
            results.append((path, result, metadata))
        # Valida todo antes de escribir; cada BRR genera un múltiplo de 16 (alineación Paula 2).
        input_paths = {p.resolve() for p in files}
        output_paths = set()
        for path, result, metadata in results:
            if args.out:
                destination = args.out / (path.stem + ".pcm") if len(files) > 1 or args.out.is_dir() else args.out
                output_paths.add(destination.resolve())
                if destination.resolve() in input_paths:
                    raise ValueError("la salida no puede sobrescribir una entrada BRR")
        if args.manifest and args.manifest.resolve() in input_paths | output_paths:
            raise ValueError("el manifiesto no puede sobrescribir BRR ni PCM")
        for path, result, metadata in results:
            if args.out:
                destination = args.out / (path.stem + ".pcm") if len(files) > 1 or args.out.is_dir() else args.out
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(result.pcm8)
                metadata["output"] = str(destination)
            print(f"{path.name}: {len(result.pcm8)} B PCM, end={result.end}, loop={result.loop}, "
                  f"loop_pcm={result.loop_sample}")
        total = sum(len(result.pcm8) for _, result, _ in results)
        manifest = {"format": "signed-pcm8", "alignment": 2, "loops_extra": args.loops,
                    "total_pcm_bytes": total, "budget_bytes": args.budget,
                    "fits_budget": total <= args.budget, "samples": [m for _, _, m in results]}
        if args.manifest:
            args.manifest.parent.mkdir(parents=True, exist_ok=True)
            args.manifest.write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"Total PCM: {total}/{args.budget} B; margen {args.budget - total} B; "
              f"{'CABE' if total <= args.budget else 'EXCEDE'}")
        return 0 if total <= args.budget else 1
    except (ValueError, OSError, subprocess.SubprocessError, AssertionError) as error:
        parser.exit(1, f"brr2pcm: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
