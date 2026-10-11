"""Pinned static census of current-native one-zero-byte C2S wrapper producers.

This is producer coverage, not handler/response discovery or a gameplay test.
"""
import hashlib
import json
import struct

import capstone
import pefile

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE

DISPATCHER = 0x961a0
ONE_ZERO = 0x157d0
EXPECTED = {
    0x65510: 0x1f, 0x6551b: 0x23, 0x66c47: 0x1f, 0x66d38: 0x1f,
    0x68a56: 0x1f, 0x68a69: 0x23, 0x68a7c: 0x22,
    0x6b40b: 0x1f, 0x6b416: 0x23, 0x8448b: 0x1f,
    0x96201: 0x1f, 0x96211: 0x23, 0x96234: 0x68,
    0x9625a: 0x6d, 0x9626a: 0x31,
    0x98e05: 0x6d, 0x990c0: 0x6d, 0x992a4: 0x6d,
    0x9a6c4: 0x1f, 0x9b2ed: 0x1f, 0xa6abc: 0x6d,
    0xa8927: 0x1f, 0xa8cf8: 0x1f, 0xbf46c: 0x31,
    0xc3795: 0x68, 0xc37b3: 0x68, 0xc3832: 0x68,
    0xc39bd: 0x68, 0xe7aae: 0x1f, 0x101f7a: 0x6d,
    0x103aec: 0x6d,
}
SELECTORS = {0x1f: 0, 0x23: 1, 0x31: 2, 0x68: 3, 0x6d: 4}


def selected_push(md, raw, pc):
    values = set()
    locations = set()
    for begin in range(pc - 20, pc):
        ins = list(md.disasm(raw[begin:pc + 5], BASE + begin))
        if not ins or ins[-1].address != BASE + pc or ins[-1].mnemonic != 'call':
            continue
        if any(x.mnemonic.startswith(('call', 'ret', 'j')) for x in ins[:-1]):
            continue
        pushes = [x for x in ins[:-1] if x.mnemonic == 'push']
        if not pushes:
            continue
        try:
            value = int(pushes[-1].op_str, 0)
        except ValueError:
            continue
        if not 0 <= value <= 255:
            continue
        values.add(value)
        locations.add(pushes[-1].address - BASE)
    if len(values) != 1 or len(locations) != 1:
        raise ValueError(f'Ambiguous opcode push at {pc:X}: {values}, {locations}')
    return values.pop(), locations.pop()


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Mapped image changed')
    pe = pefile.PE(data=raw, fast_load=True)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
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
            if target not in (DISPATCHER, ONE_ZERO):
                continue
            opcode, push_pc = selected_push(md, raw, pc)
            if EXPECTED.get(pc) != opcode:
                raise ValueError(f'Wrapper call opcode changed at {pc:X}')
            calls.append({'call_rva': f'{pc:X}', 'target_rva': f'{target:X}',
                          'opcode_hex': f'{opcode:02X}', 'opcode_push_rva': f'{push_pc:X}',
                          'call_bytes_hex': raw[pc:pc+5].hex(),
                          'opcode_push_hex': raw[push_pc:push_pc+2].hex(),
                          'preceding_20_hex': raw[pc-20:pc].hex(),
                          'dispatcher_guard': 'Opcode68 branch may display local message instead of queueing'
                          if target == DISPATCHER and opcode == 0x68 else None})
    if {int(x['call_rva'], 16) for x in calls} != set(EXPECTED):
        raise ValueError('Direct wrapper call census changed')
    table = raw[0x9628c:0x9628c + 0x4f]
    selected = {i + 0x1f: value for i, value in enumerate(table) if value != 5}
    if selected != SELECTORS:
        raise ValueError('Dispatcher selector map changed')
    jumps = [struct.unpack_from('<I', raw, 0x96274 + i*4)[0] - BASE for i in range(6)]
    if jumps != [0x961bf, 0x96209, 0x96262, 0x96219, 0x96252, 0x9626f]:
        raise ValueError('Dispatcher branch table changed')
    slices = []
    for first, end in ((ONE_ZERO, 0x157ed), (DISPATCHER, 0x96272)):
        body = raw[first:end]
        ins = list(md.disasm(body, BASE + first))
        if not ins or ins[-1].address + ins[-1].size != BASE + end:
            raise ValueError('Wrapper function boundary changed')
        slices.append({'rva': f'{first:X}', 'end_rva_exclusive': f'{end:X}',
                       'sha256': hashlib.sha256(body).hexdigest(), 'bytes_hex': body.hex(),
                       'instructions': [{'rva': f'{i.address-BASE:X}',
                                        'instruction': f'{i.mnemonic} {i.op_str}'} for i in ins]})
    opcodes = sorted({int(x['opcode_hex'], 16) for x in calls})
    return {
        'format': 'god2-current-native-c2s-wrapper-census-v1',
        'native_image': IMAGE, 'native_sha256': PIN,
        'method': 'PINNED_TEXT_SECTION_RELATIVE_CALL_AND_ARGUMENT_DISASSEMBLY',
        'direct_wrapper_call_sites': len(calls),
        'wrapper_argument_opcode_candidates': [f'{x:02X}' for x in opcodes],
        'wrapper_argument_opcode_candidate_count': len(opcodes),
        'calls': calls, 'dispatcher_selector_bytes_hex': table.hex(),
        'dispatcher_selector_sha256': hashlib.sha256(table).hexdigest(),
        'dispatcher_jump_bytes_hex': raw[0x96274:0x9628c].hex(),
        'dispatcher_selected_opcodes': {f'{k:02X}': v for k, v in selected.items()},
        'one_zero_wrapper': '157D0 writes one literal zero byte and queues length1 plus caller opcode',
        'slices': slices,
        'limits': ['Only direct E8 calls in mapped .text; indirect calls and other modes remain open',
                   'Push candidates are pinned static callsite evidence, not reachability or server permission',
                   'Opcode68 dispatcher has a conditional local-message branch',
                   'No C2S->S2C response, gameplay effect, or whole-game packet total inferred'],
        'tests_builds_client_execution_live_mutation': False,
    }


def main():
    out = SERVER / 'artifacts/integration/packet-connections-20261006/c2s-wrapper-census-v1.json'
    if out.exists():
        raise FileExistsError('Preserve existing wrapper evidence')
    out.write_text(json.dumps(recover(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(out), 'method': 'STATIC_SOURCE_ONLY'}))


if __name__ == '__main__':
    main()
