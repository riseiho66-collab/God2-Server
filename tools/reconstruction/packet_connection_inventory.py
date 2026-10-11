"""Static native/source index for the connection phase; never executes the client.

Direct call bytes and local push sequences remain investigation candidates.
No emulator, socket, build, test or gameplay completion inference is used.
"""
import hashlib
import json
import re
import struct
from collections import Counter

import capstone
import pefile

from .archive_inputs import ArchivedInputs, SERVER

IMAGE = 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
PIN = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
BASE, QUEUE, LENGTH_TABLE, WORLD_TABLE = 0x400000, 0x132e0, 0x1324, 0x6b5d4
WRAPPERS = {0x157d0: 'opcode argument plus one zero payload byte',
            0x961a0: 'conditional control dispatcher; opcode argument requires branch trace'}


def source_index():
    rows = []
    for root in ('src/protocol', 'src/net', 'src/core', 'src/handlers', 'src/relations53'):
        for path in sorted((SERVER / root).rglob('*')):
            if path.suffix not in ('.h', '.cpp', '.inc'):
                continue
            text = path.read_text(encoding='utf-8-sig')
            for line, value in enumerate(text.splitlines(), 1):
                # Lexical references, not inferred direction or a call graph.
                for match in re.finditer(r'\b0x([0-9a-fA-F]{2})\b', value):
                    rows.append({'opcode': int(match[1], 16), 'path': path.relative_to(SERVER).as_posix(),
                                 'line': line, 'text': value.strip()[:300]})
    grammar = (SERVER / 'src/protocol/RecoveredWorldRecords.h').read_text(encoding='utf-8-sig')
    world_cases = set(int(x, 16) for x in re.findall(r'case\s+0x([0-9a-fA-F]+)\s*:', grammar))
    for owner, constant in re.findall(r'case\s+(\w+)::(\w+)\s*:', grammar):
        header = SERVER / 'src/protocol' / (owner + '.h')
        if not header.is_file():
            continue
        declaration = re.search(r'\b' + re.escape(constant) + r'\s*=\s*0x([0-9a-fA-F]+)', header.read_text(encoding='utf-8-sig'))
        if declaration:
            world_cases.add(int(declaration[1], 16))
    world_cases = sorted(world_cases)
    return rows, world_cases


def inventory():
    archive = ArchivedInputs()
    try:
        raw = archive.read(IMAGE)
    finally:
        archive.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Selected native evidence differs from the recorded build')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    receivers = []
    for opcode in range(256):
        leaf = struct.unpack_from('<I', raw, LENGTH_TABLE + opcode * 4)[0] - BASE if opcode < 254 else 0x131e
        code = raw[leaf:leaf + 8]
        size = struct.unpack_from('<i', code, 1)[0] if len(code) >= 6 and code[0] == 0xb8 and code[5] == 0xc3 else -1 if code[:4] == bytes.fromhex('83c8ffc3') else None
        handler = struct.unpack_from('<I', raw, WORLD_TABLE + opcode * 4)[0] - BASE if opcode < 254 else None
        receivers.append({'opcode': opcode, 'opcode_hex': f'{opcode:02X}', 'direction': 'S2C',
                          'length_leaf_rva': leaf, 'logical_size': size,
                          'length_kind': 'fixed' if size is not None and size > 0 else 'u16_variable' if size == -2 else 'unsupported' if size == -1 else 'needs_static_trace',
                          'world_consumer_rva': handler, 'world_default_consumer': handler == 0x6b517,
                          'status': 'STATIC_NATIVE_FORMAT_INDEX_ONLY'})
    calls = []
    wrappers = []
    pe = pefile.PE(data=raw, fast_load=True)
    for section in pe.sections:
        if section.Name.rstrip(b'\0') != b'.text':
            continue
        start = section.VirtualAddress
        end = min(len(raw), start + max(section.Misc_VirtualSize, section.SizeOfRawData))
        for pc in range(start, end - 4):
            if raw[pc] != 0xe8:
                continue
            target = pc + 5 + struct.unpack_from('<i', raw, pc + 1)[0]
            if target in WRAPPERS:
                wrappers.append({'call_rva': pc, 'wrapper_rva': target, 'wrapper_contract': WRAPPERS[target],
                                 'preceding_48_hex': raw[max(start, pc - 48):pc].hex(),
                                 'status': 'WRAPPER_BYTE_CALL_CANDIDATE_REQUIRES_ARGUMENT_AND_BRANCH_TRACE'})
            if target != QUEUE:
                continue
            # Try bounded decode starts; retain all distinct aligned contexts.
            # This does not certify instruction boundaries or branch ancestry.
            candidates = {}
            for begin in range(max(start, pc - 48), pc):
                ins = list(md.disasm(raw[begin:pc + 5], BASE + begin))
                if not ins or ins[-1].address != BASE + pc or ins[-1].mnemonic != 'call':
                    continue
                # Earlier calls/control transfers invalidate a local push trail.
                trail = []
                for x in ins[:-1]:
                    if x.mnemonic.startswith(('call', 'j', 'ret')):
                        trail.clear()
                    else:
                        trail.append(x)
                push = [x for x in trail if x.mnemonic == 'push']
                if len(push) < 3:
                    continue
                args = push[-3:]
                def immediate(x):
                    try:
                        return int(x.op_str, 0)
                    except ValueError:
                        return None
                length, opcode = immediate(args[0]), immediate(args[2])
                if opcode is None or not 0 <= opcode <= 255:
                    continue
                key = tuple((x.address, x.op_str) for x in args)
                candidates[key] = {'opcode': opcode, 'payload_size_candidate': length,
                                   'pushes': [{'rva': x.address - BASE, 'operand': x.op_str} for x in args]}
            calls.append({'queue_call_rva': pc, 'preceding_48_hex': raw[max(start, pc - 48):pc].hex(),
                          'argument_candidates': list(candidates.values()), 'status': 'DIRECT_BYTE_CALL_CANDIDATE_ONLY'})
    references, cases = source_index()
    candidate_ops = sorted({x['opcode'] for call in calls for x in call['argument_candidates']})
    return {'format': 'god2-static-bidirectional-connection-index-v1', 'native_image': IMAGE,
            'native_sha256': PIN, 'queue_rva': QUEUE, 's2c': receivers,
            'c2s_direct_queue_candidates': calls, 'source_opcode_references': references,
            'c2s_known_wrapper_call_candidates': wrappers,
            'world_parser_opcodes': cases, 'direct_argument_opcode_candidates': candidate_ops,
            'direct_argument_candidates_without_world_parser': sorted(set(candidate_ops) - set(cases)),
            'counts': {'s2c_length_entries': len(receivers), 's2c_length_kinds': dict(Counter(x['length_kind'] for x in receivers)),
                       'direct_queue_call_candidates': len(calls), 'known_wrapper_call_candidates': len(wrappers), 'world_parser_opcodes': len(cases)},
            'limits': ['Static source and disassembly only; no client execution or tests.',
                       'Push candidates can cross branches; field/state recovery remains necessary.',
                       'Indirect calls and producer wrappers remain open.',
                       'Source numeric literals can be fields/constants; references are not directional routes.',
                       'Parser and length counts do not measure completed gameplay or a global percentage.']}


if __name__ == '__main__':
    report = inventory()
    output = SERVER / 'artifacts/integration/packet-connections-20261006/static-packet-index.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'output': str(output), 'counts': report['counts'],
                      'unmapped_direct_argument_candidates': [f'{x:02X}' for x in report['direct_argument_candidates_without_world_parser']]}))
