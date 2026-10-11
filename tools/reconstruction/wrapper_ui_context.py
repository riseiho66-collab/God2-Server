"""Bounded static context for current-native one-zero C2S wrapper senders.

This only reads the verified retained mapped image. It does not execute the
client or infer a server request/reply relationship from matching opcodes.
"""
import hashlib
import json

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE


SLICES = (
    (0xBF300, 0xBF505, '31 complete UI sender, six exclusion guards and local cleanup'),
    (0xC3750, 0xC39DF, '68 UI sender family'),
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
        ins = list(md.disasm(body, BASE + begin))
        if not ins or ins[-1].address + ins[-1].size != BASE + end:
            raise ValueError(f'Unaligned native sender slice {begin:X}')
        slices.append({
            'begin_rva': f'{begin:X}', 'end_rva_exclusive': f'{end:X}',
            'purpose': purpose, 'sha256': hashlib.sha256(body).hexdigest(),
            'instructions': [
                {'rva': f'{i.address-BASE:X}', 'bytes': i.bytes.hex(),
                 'instruction': f'{i.mnemonic} {i.op_str}'} for i in ins],
        })
    return {
        'format': 'god2-current-native-wrapper-ui-context-static-v3',
        'native_image': IMAGE, 'native_sha256': PIN,
        'method': 'PINNED_BOUNDED_DISASSEMBLY', 'slices': slices,
        'tests_builds_client_execution_live_mutation': False,
    }


def main():
    out = SERVER / 'artifacts/integration/packet-connections-20261006/wrapper-ui-context-static-v3.json'
    if out.exists():
        raise FileExistsError('Preserve prior native evidence')
    out.write_text(json.dumps(recover(), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
