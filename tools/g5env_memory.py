#!/usr/bin/env python3
"""Auditoria B2bis con reservas futuras B35 y margen de pila del render."""
import json
from pathlib import Path
from memmap import Listing, build_model, align


def main():
    result = {}
    for mode in ('replay', 'live'):
        for bank in ('plain', 'g3'):
            root = Path('work/b2b_%s_%s' % (mode, bank))
            listing = Listing((root / 'game.lst').read_text(encoding='latin-1'))
            model = build_model(listing, data=Path('work/yi1_s_g5.dat').read_bytes(),
                                adf=(root / 'game.adf').read_bytes())
            if model.viol:
                raise ValueError('memmap distinto: %s' % root)
            # Cache, view, clave en las tres fotos y dc_stk ya estan en el
            # binario: no contarlos otra vez. Fotos Rex: 12 candidatos de
            # 86 B mas 8 B de cabecera por foto. Stack ISR 8192 ya reservado.
            reserves = dict(g5ev=align(133040, 8), work=align(29952, 8),
                            rex_photos=3*align(12*86+8, 8), output=2048,
                            render_stack=1536, allocator_slack=64)
            # B1 <= 48 + 255*3 + 224*5 = 1933 B: un color por transicion.
            # El projector tiene canario inferior a 1300 B; 1536 incluye
            # entrada/retorno del render y margen. Esta es reserva futura,
            # no una afirmacion de que el loader B35 ya exista.
            total = model.slow + sum(reserves.values())
            margin = 524288-total
            if margin < 0:
                raise ValueError('reservas slow no caben: %s, deficit %d' % (root, -margin))
            result[mode+'_'+bank] = dict(chip=model.chip, slow=model.slow,
                                       reserves=reserves, future_slow=total, margin=margin,
                                       cache=listing.sym('G5ENV_BYTES'),
                                       view=1292, photos=3*listing.sym('DC_REC'), irq_stack=8192)
            print('B2bis memoria %s/%s: chip %d, slow %d; con reservas %d, margen %d' %
                  (mode, bank, model.chip, model.slow, total, margin))
    Path('work/b2b/memory_summary.json').write_text(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
