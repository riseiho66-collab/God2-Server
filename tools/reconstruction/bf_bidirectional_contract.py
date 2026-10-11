"""Pin current-native C2S BF senders and the distinct S2C BF length route.

Only bounded source disassembly is performed. No purchase or reply semantics
are inferred from the shared opcode number.
"""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE, LENGTH_TABLE, WORLD_TABLE


SLICES = (
    (0x842cb, 0x842e9, 'dialog confirmation queues cached eight-byte BF body'),
    (0xcfb79, 0xcfc8c, 'first in-panel BF body construction and queue'),
    (0xcfd7f, 0xcfe7c, 'second in-panel BF body construction and queue'),
    (0x6b22b, 0x6b238, 'S2C BF world dispatch to a separate handler'),
)
QUEUE_CALLS = (0x842e4, 0xcfc87, 0xcfe77)


def recover():
    archive = ArchivedInputs()
    try:
        raw = archive.read(IMAGE)
    finally:
        archive.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Native mapped image changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for start, end, purpose in SLICES:
        body = raw[start:end]
        ins = list(md.disasm(body, BASE + start))
        if not ins or ins[-1].address + ins[-1].size != BASE + end:
            raise ValueError(f'Unaligned BF native slice {start:X}')
        slices.append({'rva': f'{start:X}', 'end_rva_exclusive': f'{end:X}',
                       'purpose': purpose, 'sha256': hashlib.sha256(body).hexdigest(),
                       'bytes_hex': body.hex(),
                       'instructions': [{'rva': f'{i.address-BASE:X}',
                                        'instruction': f'{i.mnemonic} {i.op_str}'}
                                       for i in ins]})
    calls = []
    for pc in QUEUE_CALLS:
        target = pc + 5 + struct.unpack_from('<i', raw, pc + 1)[0]
        if raw[pc] != 0xe8 or target != 0x132e0:
            raise ValueError(f'BF queue call changed at {pc:X}')
        calls.append({'queue_call_rva': f'{pc:X}', 'queue_target_rva': f'{target:X}',
                      'opcode_argument': 'BF', 'body_size_argument': 8,
                      'call_hex': raw[pc:pc+5].hex()})
    leaf = struct.unpack_from('<I', raw, LENGTH_TABLE + 0xbf*4)[0] - BASE
    dispatch = struct.unpack_from('<I', raw, WORLD_TABLE + 0xbf*4)[0] - BASE
    if raw[leaf:leaf+6] != bytes.fromhex('b81d000000c3') or dispatch != 0x6b22b:
        raise ValueError('S2C BF length or dispatch changed')
    return {
        'format': 'god2-current-native-bidirectional-bf-static-v1',
        'native_image': IMAGE, 'native_sha256': PIN,
        'method': 'PINNED_BOUNDED_DISASSEMBLY_ONLY',
        'c2s': {'logical_size': 9, 'body_size': 8,
                'queue_calls': calls,
                'observed_variants': [
                    '842E4 queues an eight-byte body cached at UI child+3AE48; dialog context and original transaction remain separate',
                    'CFC87 queues a local eight-byte body assembled from selected entry and UI state',
                    'CFE77 queues a local eight-byte body assembled from a different selected entry and UI state'],
                'daily_control_15_2C': 'Historical same-build daily lifecycle identifies a purchase confirmation; full ownership, price and item rules are not recovered'},
        's2c': {'logical_size': 29, 'length_leaf_rva': f'{leaf:X}',
                'world_dispatch_rva': f'{dispatch:X}',
                'c2s_reply_pairing': 'NOT_PROVEN',
                'body_field_semantics': 'NOT_QUALIFIED_BY_THIS_SLICE'},
        'slices': slices,
        'open': ['Three BF producer states and complete payload meanings',
                 'Owned purchase inventory, currency, pricing, Lua policy, persistence',
                 'S2C BF body consumer and actual request/reply causality'],
        'tests_builds_client_execution_live_mutation': False,
    }


def main():
    out = SERVER / 'artifacts/integration/packet-connections-20261006/bf-bidirectional-static-v1.json'
    if out.exists():
        raise FileExistsError('Preserve previous native evidence')
    out.write_text(json.dumps(recover(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(out), 'method': 'STATIC_SOURCE_ONLY'}))


if __name__ == '__main__':
    main()
