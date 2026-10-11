"""Bounded static cross-reference census for the current native A9 discriminator.

This is an immediate-operand scan of the pinned mapped .text, not a reachability
proof or an assertion that a server-side teleport offer exists in the client.
"""
import hashlib
import json

import capstone
import pefile

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


ROOT = SERVER / 'artifacts/integration/packet-connections-20261006'
OUT = ROOT / 'teleport-a9-context-immediate-frontier-v1.json'
VALUES = tuple(range(0x61e, 0x623))
SLICES = (
    (0x13bcd, 0x13cda, 'resource-table string lookup and fallback'),
    (0x63220, 0x63259, 'unrelated resource-memory initialization'),
    (0xf6da0, 0xf6ddf, 'teleport menu context discriminator'),
)


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Pinned native image changed')
    pe = pefile.PE(data=raw, fast_load=True)
    text_sections = [s for s in pe.sections if s.Name.rstrip(b'\0') == b'.text']
    if len(text_sections) != 1:
        raise ValueError('Expected one mapped .text section')
    section = text_sections[0]
    start, end = section.VirtualAddress, section.VirtualAddress + section.Misc_VirtualSize
    if start != 0x1000 or end != 0x170000:
        raise ValueError('Mapped .text range changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    md.skipdata = True
    references = []
    for ins in md.disasm(raw[start:end], BASE + start):
        if ins.id == 0:
            continue
        for operand in ins.operands:
            if operand.type == capstone.x86.X86_OP_IMM and operand.imm in VALUES:
                rva = ins.address - BASE
                references.append({
                    'value_hex': f'{operand.imm:04X}', 'rva': f'{rva:X}',
                    'instruction_bytes': ins.bytes.hex(),
                    'instruction': f'{ins.mnemonic} {ins.op_str}',
                    'bounded_role': 'A9_CONTEXT_DISCRIMINATOR' if 0xf6da0 <= rva < 0xf6ddf else
                                    'RESOURCE_LOOKUP' if 0x13bcd <= rva < 0x13cda else
                                    'MEMORY_INIT_COUNT' if 0x63220 <= rva < 0x63259 else
                                    'UNCLASSIFIED_IMMEDIATE',
                })
    slices = []
    for begin, finish, purpose in SLICES:
        body = raw[begin:finish]
        slices.append({'begin_rva': f'{begin:X}', 'end_rva_exclusive': f'{finish:X}',
                       'purpose': purpose, 'sha256': hashlib.sha256(body).hexdigest(),
                       'bytes_hex': body.hex()})
    return {
        'format': 'god2-current-native-a9-context-immediate-frontier-v1',
        'native_image': IMAGE, 'native_sha256': PIN,
        'method': 'PINNED_MAPPED_TEXT_LINEAR_DISASSEMBLY_IMMEDIATE_SCAN',
        'text_range': [f'{start:X}', f'{end:X}'],
        'values': [f'{v:04X}' for v in VALUES],
        'references': references, 'bounded_slices': slices,
        'limits': [
            'Linear x86 disassembly and immediate operands do not prove reachability or exhaustive dynamic use.',
            'The generic resource-table references are not a context-to-NPC/item or server-offer join.',
            'Client-side context discrimination does not establish an authoritative server menu trigger, fee, cooldown or arrival.',
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
