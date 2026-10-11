"""Pin bounded original C2S6B producer/caller and distinct S2C6B slices.

Static mapped-image disassembly only. Does not execute gameplay or tests.
"""
import hashlib
import json

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE


SLICES = (
    (0x972f0, 0x9731f, 'shared producer, network body = formal arg3,arg2,arg1'),
    (0x8faf0, 0x8fb25, 'second producer, same reverse formal argument order'),
    (0xa0470, 0xa04ad, 'beast panel control11 passes lane0, selected selector, dragged slot'),
    (0xa3930, 0xa394f, 'producer caller with literal lane1'),
    (0xd71c8, 0xd71d6, 'producer caller with literal lane2'),
    (0x84207, 0x84224, 'producer caller with literal lane3'),
    (0xa5fc1, 0xa5fdc, 'second producer caller with literal lane3'),
    (0x84396, 0x843b1, 'second producer caller with literal lane4'),
    (0x8f84b, 0x8f875, 'second producer caller with literal lane4'),
    (0x6aabe, 0x6aad6, 'distinct S2C6B world consumer, not a food-reply proof'),
)


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Mapped native image changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for start, end, purpose in SLICES:
        body = raw[start:end]
        slices.append({
            'rva': f'{start:X}', 'end_rva_exclusive': f'{end:X}',
            'purpose': purpose, 'sha256': hashlib.sha256(body).hexdigest(),
            'bytes_hex': body.hex(),
            'instructions': [{'rva': f'{i.address-BASE:X}',
                              'instruction': f'{i.mnemonic} {i.op_str}'}
                             for i in md.disasm(body, BASE + start)],
        })
    return {
        'format': 'god2-native-companion-control6b-static-v2',
        'mapped_image': {'path': IMAGE, 'sha256': PIN},
        'method': 'PINNED_BOUNDED_DISASSEMBLY_ONLY',
        'correction': 'Earlier V1 beast-panel note/codec placed lane0 first. The original shared producer copies formal arguments in reverse: logical6B,slot,selector,lane.',
        'observed_lanes': [0, 1, 2, 3, 4],
        'scope': 'C2S format and selected caller constants; eligibility, food effects, consumption, native reply and untraced callers remain OPEN',
        's2c6b': '21-byte separate world consumer6AABE calls4CC910; no C2S6B food reply pairing inferred',
        'slices': slices,
        'tests_builds_emulator_client_execution_live_mutation': False,
    }


def main():
    out = SERVER / 'artifacts/integration/packet-connections-20261006/companion-control6b-static-v2.json'
    if out.exists():
        raise FileExistsError('Preserve existing native evidence; choose a new version')
    out.write_text(json.dumps(recover(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(out), 'method': 'STATIC_SOURCE_ONLY'}))


if __name__ == '__main__':
    main()
