"""Pin four current-native nine-byte WORLD S2C text/NPC consumers."""

import hashlib
import json

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


OUT = SERVER / 'artifacts/integration/packet-connections-20261006/s2c-text-npc-595a5b79-v1.json'
FRONTIER = SERVER / 'artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v7.json'
SLICES = (
    ('opcode_5a_npc_pool_label', 0x6AB27, 0x6AB69),
    ('opcodes_59_5b_text', 0x6AB69, 0x6AB7B),
    ('opcode_79_mode_switch', 0x6AB7B, 0x6ABD7),
    ('text_resource_consumer', 0xC81A0, 0xC81F0),
    ('npc_pool_label_consumer', 0xCCD10, 0xCCD77),
)


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior S2C text/NPC evidence')
    frontier = json.loads(FRONTIER.read_text(encoding='utf-8'))
    wanted = {'59': '6AB69', '5A': '6AB27', '5B': '6AB69', '79': '6AB7B'}
    entries = {x['opcode']: x for x in frontier['entries'] if x['opcode'] in wanted}
    if set(entries) != set(wanted) or any(
            entries[op]['world_dispatch_rva'] != rva or
            entries[op]['logical_size'] != 9 or
            entries[op]['length_kind'] != 'fixed'
            for op, rva in wanted.items()):
        raise ValueError('Pinned WORLD dispatch or length changed')
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Pinned native image changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for name, start, end in SLICES:
        body = raw[start:end]
        instructions = list(md.disasm(body, BASE + start))
        if not instructions or instructions[0].address != BASE + start or \
                instructions[-1].address + instructions[-1].size != BASE + end:
            raise ValueError('Native slice boundary changed: ' + name)
        slices.append({
            'name': name, 'begin_rva': f'{start:X}',
            'end_rva_exclusive': f'{end:X}',
            'sha256': hashlib.sha256(body).hexdigest(),
            'bytes_hex': body.hex(),
            'instructions': [
                {'rva': f'{i.address-BASE:X}',
                 'instruction': f'{i.mnemonic} {i.op_str}'}
                for i in instructions
            ],
        })
    value = {
        'format': 'god2-current-native-s2c-text-npc-595a5b79-v1',
        'native_image': IMAGE, 'native_sha256': PIN,
        'world_frontier_sha256': hashlib.sha256(FRONTIER.read_bytes()).hexdigest(),
        'method': 'PINNED_WORLD_DISPATCH_AND_BOUNDED_NATIVE_CONSUMER',
        'logical_size': 9,
        'world_dispatch': wanted,
        'branches': {
            '59_and_5B': 'Pass logical+1 to 4C81A0; WORD logical+7 selects a text resource row, WORD logical+1 is passed to 4C81F0.',
            '5A': 'Use DWORD logical+1 as existing NPC pool identity and WORD logical+7 to select a resource row; pass to 4CCD10 for label update.',
            '79': 'If WORD logical+5 != FFFF, enter the same 4C81A0 text branch; if FFFF, use DWORD logical+1 and WORD logical+7 for the 4CCD10 NPC pool label branch.',
        },
        'unread_wire_fields': [
            'Logical bytes3..6 in 59/5B text path are not read by 4C81A0.',
            'Logical bytes5..6 in 5A path are not read by its WORLD case.',
        ],
        'limits': [
            'These are native client receive effects only; original server producers and C2S causality are not proved.',
            'The resource rows, NPC identity ownership, and emission timing are not certified by this slice.',
            'The 79 mode marker is a branch selector, not a server-side permission or content rule.',
        ],
        'slices': slices,
        'tests_builds_client_execution_deployment': False,
    }
    OUT.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(OUT), 'opcodes': list(wanted), 'slices': len(slices)}))


if __name__ == '__main__':
    main()
