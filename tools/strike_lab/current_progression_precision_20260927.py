"""Execute the exact pet EXP display prefix; never infer server EXP tables.

Uses pinned native bytes offline. Inputs are diagnostic, NOT wild-monster data.
The companion evidence export binds the entire function to saved actual RAM.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from .current_monster_inspect_identity import NativeInspect, BASE, ROOT
from .omega_assets import decode_csvz


def require(condition, message):
    if not condition:
        raise ValueError(message)


def audit():
    directory = ROOT / 'artifacts/research/progression-stat-entrypoints-20260927-01'
    receipt_raw = (directory / 'memory-qualified.json').read_bytes()
    receipt = json.loads(receipt_raw)
    require(any(f['entry'] == '0x4a40c0' for f in receipt['functions']),
            'Missing whole-function actual RAM comparison')
    # The native source and live code must agree for the executed slice.
    capture = ROOT / receipt['memory_receipt']
    memory_raw = (capture / 'memory-result.json').read_bytes()
    require(hashlib.sha256(memory_raw).hexdigest() == receipt['memory_receipt_sha256'],
            'Memory receipt changed')
    memory = json.loads(memory_raw)['capture']['whole_live_text']
    live = (capture / memory['file']).read_bytes()
    require(hashlib.sha256(live).hexdigest() == memory['live_sha256'], 'RAM code changed')
    v = NativeInspect()
    start, stop = 0xa4151, 0xa418e
    origin = int(memory['rva'], 16)
    require(v.image[start:stop] == live[start-origin:stop-origin], 'Executed RAM code differs')
    constant = v.image[0x171204:0x171208]
    require(constant.hex() == '0ad7233c', 'Native float32 constant changed')
    raw_message = (ROOT.parent / 'God2/Data2/Patch/Comm/message.csvZ').read_bytes()
    require(hashlib.sha256(raw_message).hexdigest() ==
            '5cd34cce66feae96d947cd45e32984765ce625673c0fb19c73cb63d7d9178598',
            'Message source changed')
    lines = decode_csvz(raw_message).decode('cp950').splitlines()
    labels = {str(i): lines[n-1] for i, n in ((162, 2188), (165, 2191))}
    require('%6.2f' in labels['162'] and '%6.2f' in labels['165'], 'Percentage labels changed')
    probes = []
    # Crossing 16 bits distinguishes panel low24 from the separate HUD low16.
    for low in (0, 1, 9999, 10000, 0x7fff, 0xffff, 0x10000, 0x7fffff, 0xffffff):
        for upper in (0, 0x5a, 0xff):
            packed = low | (upper << 24)
            body = bytearray(72)
            struct.pack_into('<I', body, 8, packed)
            v.prepare()
            v.vm.mem_write(v.PET_UI, bytes(body))
            v.reg('EBX', v.PET_UI)
            v.reg('EBP', v.PET_UI)
            v.reg('EDI', 0)  # Explicit original prefix live-in; no full UI execution.
            trace = v.slice(start, (stop,), ((start, stop),), ((v.SP-12, v.SP+0x50),))
            got = bytes(v.vm.mem_read(v.SP+0x40, 4))
            expected = struct.pack('<f', low * struct.unpack('<f', constant)[0])
            require(got == expected, 'Native x87 percentage mismatch')
            require(bytes(v.vm.mem_read(v.PET_UI, 72)) == body, 'Source record mutated')
            probes.append({'packed_body8': packed, 'raw24': low,
                           'native_float32_hex': got.hex(), 'instructions': trace['instruction_count']})
    return {'authority': 'NATIVE_DISPLAY_ARITHMETIC_WITH_SYNTHETIC_OPERANDS',
            'client_sha256': receipt['client_sha256'],
            'memory_qualification_sha256': hashlib.sha256(receipt_raw).hexdigest(),
            'entry': hex(BASE+start), 'stop_before_call': hex(BASE+stop),
            'code_hex': v.image[start:stop].hex(), 'constant_float32_hex': constant.hex(),
            'program_message_source_rows': labels, 'probes': probes,
            'original_level_requirement_tables': {'role': None, 'deity': None, 'pet': None},
            'wild_monster_intrinsic_stats': None,
            'limitations': ['Only the 17-instruction display prefix runs; no full UI or gameplay claim.',
                           'The upper byte is preserved, not discarded from the packet.',
                           'A percentage cannot determine total or per-level EXP requirements.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit()
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'native_display_probes': len(result['probes']), 'original_exp_tables': 0}))


if __name__ == '__main__':
    main()
