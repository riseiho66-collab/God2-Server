"""Static 22/31/68 wrapper branch frontier and distinct C2S35 raw candidate."""
import hashlib
import json
import struct

import capstone
import pefile

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE

SELECTOR_START = 0x68ac0
SELECTOR_COUNT = 0x17
EXPECTED = {0x1f: 0, 0x22: 1, 0x23: 2, 0x35: 3}
SLICES = (
    (0x68a30, 0x68aa9, 'secondary opcode dispatcher; 22/00 and 35/raw16 candidates'),
    (0xbf433, 0xbf471, '31 caller gated by three existing UI rows bit8'),
    (0xc3781, 0xc379a, '68 UI callback branch'),
    (0xc3800, 0xc3838, '68 caller gated by selected row bit10'),
    (0xc39b7, 0xc39c4, '68 alternative caller after local branch'),
)


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Mapped native image changed')
    table = raw[SELECTOR_START:SELECTOR_START + SELECTOR_COUNT]
    selected = {i + 0x1f: value for i, value in enumerate(table) if value != 4}
    if selected != EXPECTED:
        raise ValueError('Secondary selector map changed')
    targets = [struct.unpack_from('<I', raw, 0x68aac + i*4)[0] - BASE for i in range(5)]
    if targets != [0x68a4e, 0x68a74, 0x68a61, 0x68a87, 0x68aa3]:
        raise ValueError('Secondary dispatcher jump map changed')
    pe = pefile.PE(data=raw, fast_load=True)
    direct_callers = []
    for section in pe.sections:
        if section.Name.rstrip(b'\0') != b'.text':
            continue
        start = section.VirtualAddress
        end = min(len(raw), start + max(section.Misc_VirtualSize, section.SizeOfRawData))
        for pc in range(start, end - 4):
            if raw[pc] == 0xe8 and pc + 5 + struct.unpack_from('<i', raw, pc + 1)[0] == 0x68a30:
                direct_callers.append(f'{pc:X}')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for start, end, purpose in SLICES:
        body = raw[start:end]
        instructions = list(md.disasm(body, BASE + start))
        if not instructions or instructions[-1].address + instructions[-1].size != BASE + end:
            raise ValueError(f'Unaligned slice {start:X}')
        slices.append({'rva': f'{start:X}', 'end_rva_exclusive': f'{end:X}',
                       'purpose': purpose, 'sha256': hashlib.sha256(body).hexdigest(),
                       'bytes_hex': body.hex(),
                       'instructions': [{'rva': f'{i.address-BASE:X}',
                                        'instruction': f'{i.mnemonic} {i.op_str}'}
                                       for i in instructions]})
    return {
        'format': 'god2-current-native-wrapper-frontier-v1',
        'native_image': IMAGE, 'native_sha256': PIN,
        'method': 'PINNED_BOUNDED_DISASSEMBLY_AND_DIRECT_E8_SCAN',
        'secondary_dispatcher_rva': '68A30',
        'secondary_selector_bytes_hex': table.hex(),
        'secondary_jump_bytes_hex': raw[0x68aac:0x68ac0].hex(),
        'secondary_selector_map': {f'{k:02X}': v for k, v in selected.items()},
        'secondary_direct_e8_callers': direct_callers,
        'secondary_dispatcher_reachability': 'NOT_ESTABLISHED; zero direct E8 xrefs does not exclude indirect calls',
        'c2s35_raw_candidate': {
            'logical_size': 17,
            'producer_rva': '68A87..68AA3',
            'body_written_bytes': {'8..11': 'FFFFFFFF'},
            'other_body_bytes': 'NOT_INITIALIZED_IN_THIS_LOCAL_PRODUCER',
            'relationship_to_existing_battle_action35': 'UNPROVEN; not a parsed action1/2/0B or gameplay permission',
        },
        'c2s22': '68A74 ->157D0 may queue22 00 when secondary dispatcher input22 is reached',
        'c2s31': 'BF465 call uses961A0(31,1) after three UI row bit8 guards; no response authority',
        'c2s68': 'C3795/C37B3/C3832/C39BD call961A0(68,1); wrapper may choose local message instead of queue',
        'slices': slices,
        'open': ['Proof of secondary dispatcher reachability and state',
                 '22/31/68 server operation and causal replies',
                 'C2S35 raw candidate semantics and all unwritten bytes',
                 'indirect calls and other native modes'],
        'tests_builds_client_execution_live_mutation': False,
    }


def main():
    out = SERVER / 'artifacts/integration/packet-connections-20261006/c2s-wrapper-frontier-v1.json'
    if out.exists():
        raise FileExistsError('Preserve previous native evidence')
    out.write_text(json.dumps(recover(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(out), 'method': 'STATIC_SOURCE_ONLY'}))


if __name__ == '__main__':
    main()
