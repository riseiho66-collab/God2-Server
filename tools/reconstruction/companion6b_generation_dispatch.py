"""Pin the native slot-44 generation split of C2S 6B lanes 1 and 3.

Static mapped-image evidence only. This does not execute the client or qualify
food effects, item consumption, ownership, or an S2C response.
"""
import hashlib
import json

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


SLICES = (
    (0x97320, 0x97378, 'slot44 key and generation-dependent C2S6B dispatch'),
    (0xA2980, 0xA29A0, 'first-generation slot guard 42..44'),
    (0xA29A0, 0xA29FB, 'first-generation key range and metadata gate'),
    (0xA5070, 0xA5090, 'second-generation slot guard 42..44'),
    (0xA5090, 0xA50E5, 'second-generation key range and metadata gate'),
)


def recover():
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
    return {
        'format': 'god2-native-companion6b-generation-dispatch-v1',
        'mapped_image': {'path': IMAGE, 'sha256': PIN},
        'method': 'PINNED_BOUNDED_STATIC_DISASSEMBLY',
        'origin': '97324 reads low WORD at owner+85A30; TEST/JBE guard requires nonzero key',
        'ordered_branches': [
            {
                'gate': 'A29A0: slot 2C; key 3391..3778 or 5DC1..6D60; metadata lookup nonnull',
                'on_success': '97349 -> 972F0 queues 6B | UI+85602 | 2C | 01',
                'meaning': 'first-generation pet-domain lane1 producer',
            },
            {
                'gate': 'A5090: only after first gate fails; slot 2C; key 6D61..7F58; metadata lookup nonnull',
                'on_success': '97370 -> 972F0 queues 6B | UI+85602 | 2C | 03',
                'meaning': 'second-generation pet-domain lane3 producer',
            },
        ],
        'on_both_gates_fail': '97375 returns without a C2S6B queue call',
        'scope': ('This is one slot44 caller; other lane1/lane3 callers remain separately '
                  'sourced. UI+85602 is the byte sent as slot, not server authority.'),
        'not_proven': [
            'item ownership or eligibility for either pet generation',
            'food type, amount, consumption, pet mutation or Lua rule',
            'causal S2C reply to either lane',
            'all callers of 972F0 or other 6B producers',
        ],
        'new_complete_routes': 0,
        'tests_builds_client_execution_live_mutation': False,
    }


def main():
    out = SERVER / 'artifacts/integration/packet-connections-20261006/companion6b-generation-dispatch-v1.json'
    if out.exists():
        raise FileExistsError('Preserve prior native evidence')
    out.write_text(json.dumps(recover(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(out), 'method': 'STATIC_NATIVE_REVIEW'}))


if __name__ == '__main__':
    main()
