"""Exhaustive direct .text calls to native C2S6B producers, plus S2C6B text sink.

Pinned mapped-image bytes and bounded static disassembly only; no client execution.
"""
import hashlib
import json
import struct

import capstone
import pefile

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE

PRODUCERS = {0x972f0, 0x8faf0}
EXPECTED_CALLS = {
    0x8421f, 0x84245, 0x843ac, 0x8f870, 0x97349,
    0x97370, 0xa04a8, 0xa394a, 0xa5fd7, 0xd71d1,
}
SLICES = (
    (0x97320, 0x97378, 'additional lane1/lane3 callers, literal selector2C'),
    (0x84233, 0x8424a, 'second direct lane1 caller'),
    (0x6aabe, 0x6aad6, 'S2C6B dispatch passes DWORD identity and text pointer'),
    (0xcc910, 0xcc94b, 'pool identity lookup then text renderer'),
    (0xccf80, 0xccfa3, 'exact DWORD lookup across256 existing pool records'),
    (0x109e70, 0x109f1a, 'secondary text renderer uses NUL-terminated source'),
    (0x6b4ef, 0x6b50a, 'separate S2CEC owner-or-8000 follower name caller'),
)


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Mapped native image changed')
    pe = pefile.PE(data=raw, fast_load=True)
    calls = []
    for section in pe.sections:
        if section.Name.rstrip(b'\0') != b'.text':
            continue
        start = section.VirtualAddress
        end = min(len(raw), start + max(section.Misc_VirtualSize, section.SizeOfRawData))
        for pc in range(start, end - 4):
            if raw[pc] != 0xe8:
                continue
            target = pc + 5 + struct.unpack_from('<i', raw, pc + 1)[0]
            if target in PRODUCERS:
                calls.append({'call_rva': f'{pc:X}', 'producer_rva': f'{target:X}',
                              'call_hex': raw[pc:pc+5].hex()})
    if {int(c['call_rva'], 16) for c in calls} != EXPECTED_CALLS:
        raise ValueError('Native direct producer caller set changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for start, end, purpose in SLICES:
        body = raw[start:end]
        instructions = list(md.disasm(body, BASE + start))
        if not instructions or instructions[-1].address + instructions[-1].size != BASE + end:
            raise ValueError(f'Unaligned disassembly slice {start:X}')
        slices.append({'rva': f'{start:X}', 'end_rva_exclusive': f'{end:X}',
                       'purpose': purpose, 'sha256': hashlib.sha256(body).hexdigest(),
                       'bytes_hex': body.hex(),
                       'instructions': [{'rva': f'{i.address-BASE:X}',
                                        'instruction': f'{i.mnemonic} {i.op_str}'}
                                       for i in instructions]})
    return {
        'format': 'god2-native-companion-control6b-static-v3',
        'mapped_image': {'path': IMAGE, 'sha256': PIN},
        'method': 'PINNED_TEXT_SECTION_DIRECT_CALL_CENSUS_AND_BOUNDED_DISASSEMBLY',
        'direct_c2s6b_callers': calls,
        'direct_c2s6b_callers_count': len(calls),
        'c2s6b_additional_callers': {
            '97349': 'lane1; formal selector0x2C, slot UI+85602',
            '97370': 'lane3; formal selector0x2C, slot UI+85602',
        },
        's2c6b': {
            'logical_size': 21,
            'body': 'exact existing pool identity DWORD LE; 16-byte NUL-terminated text cell',
            'consumer': '6AABE -> 4CC910 exact pool lookup -> 509E70 secondary text buffer',
            'not_c2s6b_reply': True,
            'separate_follower_name': 'S2CEC handler6B4EF also calls4CC910 with owner|8000',
        },
        'slices': slices,
        'open': ['Indirect callers and alternate modes', 'server authority for world pool names',
                 'original content rows, timing and actor creation ordering',
                 'C2S6B gameplay effects and its genuine S2C responses'],
        'tests_builds_client_execution_live_mutation': False,
    }


def main():
    out = SERVER / 'artifacts/integration/packet-connections-20261006/companion-control6b-static-v3.json'
    if out.exists():
        raise FileExistsError('Preserve previous evidence')
    out.write_text(json.dumps(recover(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(out), 'method': 'STATIC_SOURCE_ONLY'}))


if __name__ == '__main__':
    main()
