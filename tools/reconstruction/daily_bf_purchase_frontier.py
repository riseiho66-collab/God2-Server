"""Current-native daily-panel BF producer through the shared queue call.

Reads only the verified mapped image. This qualifies bytes and UI provenance,
not an economic transaction, client acceptance or a causal server response.
"""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


ROOT = SERVER / 'artifacts/integration/packet-connections-20261006'
OUT = ROOT / 'daily-bf-purchase-producer-v2.json'
SLICES = (
    (0x8ba8a, 0x8bb31, 'daily purchase display gate and dialog32 open'),
    (0x83d93, 0x83da9, 'confirmation jump-table dispatch'),
    (0x8433d, 0x84374, 'dialog32 body from current daily panel'),
    (0x84505, 0x8451f, 'shared queue call and local close'),
)


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Pinned native image changed')
    target = struct.unpack_from('<I', raw, 0x84520 + 0x32 * 4)[0] - BASE
    if target != 0x8433d or raw[0x8436f:0x84374] != bytes.fromhex('e991010000') or \
       raw[0x8450b:0x84510] != bytes.fromhex('e8d0edf8ff'):
        raise ValueError('Daily BF branch or shared queue changed')
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
            'instructions': [{'rva': f'{ins.address-BASE:X}', 'bytes': ins.bytes.hex(),
                              'instruction': f'{ins.mnemonic} {ins.op_str}'} for ins in instructions],
        })
    return {
        'format': 'god2-current-native-daily-bf-producer-v2',
        'native_image': IMAGE, 'native_sha256': PIN,
        'method': 'PINNED_BOUNDED_DISASSEMBLY_AND_DIALOG_DISPATCH_POINTER',
        'dialog_selector': '32', 'dialog_jump_target_rva': f'{target:X}',
        'shared_queue_call_rva': '8450B', 'queue_target_rva': '132E0',
        'logical_size': 9,
        'body': 'item_u16LE from panel+20FD4, literal01, literal01, amount_u32LE from panel+20FD8',
        'prior_direct_call_producer_rvas': ['842E4', 'CFC87', 'CFE77'],
        'distinct_known_bf_producer_branches': 4,
        'slices': slices,
        'limits': [
            'Dialog32 is opened only after current panel purchase gate and nonzero item lookup.',
            'FD payload supplies the display fields; it does not prove price, wallet, stock, transaction or S2C reply.',
            'The three older direct queue calls remain distinct BF producer branches.',
        ],
        'tests_builds_client_execution_live_mutation': False,
    }


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior native evidence')
    OUT.write_text(json.dumps(recover(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(OUT)


if __name__ == '__main__':
    main()
