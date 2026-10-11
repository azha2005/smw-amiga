#!/usr/bin/env python3
"""Extrae el arranque del vivo sin las operaciones posteriores del replay."""
import argparse
import struct
from pathlib import Path


def seed(raw):
    if len(raw) < 148 or raw[:4] != b'SMWR':
        raise ValueError('cabecera SMWR invalida')
    frames, first, states, reserved, ops, sts = struct.unpack_from('>4H2I', raw, 4)
    if not frames or not states or ops < 148 or sts < ops + frames * 6:
        raise ValueError('replay sin arranque completo')
    if len(raw) != sts + states * 576 or raw[ops] not in (1, 4):
        raise ValueError('primer op debe cargar un estado (SYNC o LEVEL)')
    return (b'SMWR' + struct.pack('>4H2I', 1, first, 1, reserved, 148, 154)
            + raw[20:148] + raw[ops:ops + 6] + raw[sts:sts + 576])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('replay', nargs='?')
    ap.add_argument('out', nargs='?')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        raw = (b'SMWR' + struct.pack('>4H2I', 2, 123, 2, 0, 148, 160)
               + bytes(range(128)) + b'\x04\x00\x80\x00\x40\x00'
               + bytes(6) + bytes(range(256))*2 + bytes(64) + bytes(576))
        compact = seed(raw)
        assert len(compact) == 730
        op, state = struct.unpack_from('>2I', compact, 12)
        assert compact[20:148] == raw[20:148]
        assert compact[op:op+6] == raw[148:154]
        assert compact[state:state+576] == raw[160:736]
        assert struct.unpack_from('>3H', compact, 4) == (1, 123, 1)
        for invalid in (b'', raw[:-1], raw[:148] + bytes(6) + raw[154:]):
            try:
                seed(invalid)
            except ValueError:
                continue
            raise AssertionError('replay invalido aceptado')
        print('LIVE SEED: selftest OK (arranque exacto y entradas invalidas)')
        return
    if not a.replay or not a.out:
        ap.error('se requieren replay y out')
    raw = Path(a.replay).read_bytes()
    result = seed(raw)
    Path(a.out).write_bytes(result)
    print('LIVE SEED: %d -> %d B; estado, op y carga de sprites exactos' % (len(raw), len(result)))


if __name__ == '__main__':
    main()
