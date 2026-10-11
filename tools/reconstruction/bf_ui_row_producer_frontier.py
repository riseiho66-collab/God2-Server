"""Preserve bounded native evidence for the two BF UI-row producers."""
import hashlib
import json

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


OUT = SERVER / 'artifacts/integration/packet-connections-20261006/bf-ui-row-producer-v3.json'
SLICES = (
    (0xCFABA, 0xCFB79, 'selection and quantity gates for both UI row families'),
    (0xCFB79, 0xCFC8C, '48-byte row family immediate BF request'),
    (0xCFCB0, 0xCFCE0, '48-byte row family confirmation cache'),
    (0xCFD7F, 0xCFE7C, '6-byte row family immediate BF request'),
    (0xCFEA0, 0xCFECD, '6-byte row family confirmation cache'),
)


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Pinned native image changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for begin, end, purpose in SLICES:
        body = raw[begin:end]
        instructions = list(md.disasm(body, BASE + begin))
        if not instructions or instructions[-1].address + instructions[-1].size != BASE + end:
            raise ValueError(f'Unaligned native slice {begin:X}')
        slices.append({
            'begin_rva': f'{begin:X}', 'end_rva_exclusive': f'{end:X}',
            'purpose': purpose, 'sha256': hashlib.sha256(body).hexdigest(),
            'bytes_hex': body.hex(),
            'instructions': [{'rva': f'{ins.address-BASE:X}',
                              'instruction': f'{ins.mnemonic} {ins.op_str}'}
                             for ins in instructions],
        })
    return {
        'format': 'god2-current-native-bf-ui-row-producer-v3',
        'native_image': IMAGE, 'native_sha256': PIN,
        'method': 'PINNED_BOUNDED_DISASSEMBLY_ONLY',
        'logical_c2s_size': 9,
        'shared_body': {
            'byte_2': 'UI+9695E, observed at CFACF..CFAD8',
            'byte_3': 'UI mode+97FA2 maps even 0/2/4/6 or odd 1/3/5/7 to 1/2/3/4',
            'bytes_4_to_7': 'zero-extended u16 selected row+2, possibly replaced by duplicate-row search',
        },
        'row_families': [
            {'mode': 'odd 1/3/5/7', 'stride': 48,
             'selected_index': 'signed word UI+97FA0',
             'key_u16': 'UI+96BA4+index*48',
             'value_u16': 'UI+96BA6+index*48',
             'immediate_queue_rva': 'CFC87', 'confirm_cache_rva': 'CFCB0'},
            {'mode': 'even 0/2/4/6', 'stride': 6,
             'selected_index': 'signed word UI+97FA0',
             'key_u16': 'UI+96980+index*6',
             'value_u16': 'UI+96982+index*6',
             'immediate_queue_rva': 'CFE77', 'confirm_cache_rva': 'CFEA0'},
        ],
        'confirmation': 'Matching key in later row segment caches body at child+3AE48; dialog confirmation may queue it at 842E4.',
        'limits': [
            'No server-side owner, price, inventory or transaction source was recovered.',
            'No causal relation to S2C BE/BF panel was proven.',
            'One BF opcode has multiple UI producer branches; none is a complete gameplay route.',
        ],
        'builds_tests_client_execution_deployment': False,
        'slices': slices,
    }


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior native evidence')
    OUT.write_text(json.dumps(recover(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(OUT)


if __name__ == '__main__':
    main()
