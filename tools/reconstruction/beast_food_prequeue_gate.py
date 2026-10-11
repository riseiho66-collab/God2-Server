"""Bounded static native evidence for the C2S6B lane0 prequeue branch."""
import hashlib
import json

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


SLICES = (
    (0xA0470, 0xA04C8, 'panel control11 gate and lane0 queue; other control uses UI helper'),
    (0x99A60, 0x99AD1, 'direct UI-message helper body called by food control'),
)


def main():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Mapped image SHA256 changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for start, end, purpose in SLICES:
        body = raw[start:end]
        instructions = list(md.disasm(body, BASE + start))
        if not instructions or instructions[-1].address + instructions[-1].size != BASE + end:
            raise ValueError(f'Unaligned native slice {start:X}..{end:X}')
        slices.append({
            'rva': f'{start:X}', 'end_rva_exclusive': f'{end:X}',
            'purpose': purpose, 'sha256': hashlib.sha256(body).hexdigest(),
            'bytes_hex': body.hex(),
            'instructions': [
                {'rva': f'{i.address-BASE:X}', 'instruction': f'{i.mnemonic} {i.op_str}'}
                for i in instructions
            ],
        })
    result = {
        'format': 'god2-beast-food-prequeue-gate-v1',
        'mapped_image': {'path': IMAGE, 'sha256': PIN},
        'method': 'PINNED_BOUNDED_STATIC_DISASSEMBLY',
        'qualified': (
            'Control11 sends 6B lane0 only after dragged slot >=0 and local flag0x20; '
            'the direct 499A60 helper reads UI state and calls UI message functions. '
            'This bounded path does not itself establish PFD class, food effect, '
            'consumption, server ownership or S2C causality.'
        ),
        'source_join': (
            'Build-matched PFD section has 65 exact declarations; some are special '
            'transformation rows, so section membership is not food eligibility.'
        ),
        'new_complete_routes': 0,
        'tests_builds_client_execution_live_mutation': False,
        'slices': slices,
    }
    out = SERVER / 'artifacts/integration/packet-connections-20261006/beast-food-prequeue-gate-v1.json'
    if out.exists():
        raise FileExistsError('Preserve prior native evidence')
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(out), 'method': 'STATIC_NATIVE_REVIEW'}))


if __name__ == '__main__':
    main()
