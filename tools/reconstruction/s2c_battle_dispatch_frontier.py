"""Read-only current-native battle S2C opcode and 86 subtype dispatch census.

This is a dispatch inventory, not client execution, packet acceptance, a
server producer, or a complete inventory of battle action variants.
"""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE


ROOT = SERVER/'artifacts/integration/packet-connections-20261006'
FIRST, LAST = 0x1C, 0x89
SELECTORS = 0x11465C
TARGETS = 0x114634
SUBTYPE_TARGETS = 0x1146CC
EXPECTED = {
    0x1C: 0x114358, 0x38: 0x114525, 0x83: 0x11436B,
    0x84: 0x1143DD, 0x85: 0x114449, 0x86: 0x114464,
    0x87: 0x114518, 0x88: 0x114538, 0x89: 0x114582,
}
SLICES = (
    (0x114332, 0x114358, 'battle opcode range, byte selector and DWORD jump table'),
    (0x114464, 0x11447A, 'battle 86 subtype 0..6 branch'),
)


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Pinned mapped client image changed')
    world = json.loads((ROOT/'static-packet-index.json').read_text(encoding='utf-8'))
    if world['native_sha256'] != PIN:
        raise ValueError('WORLD index build mismatch')
    target = [struct.unpack_from('<I', raw, TARGETS+4*i)[0]-BASE for i in range(10)]
    selector = raw[SELECTORS:SELECTORS+(LAST-FIRST+1)]
    if len(selector) != 110 or any(x>9 for x in selector) or target[9] != 0x1145C0:
        raise ValueError('Battle selector/target grammar changed')
    specialized = {FIRST+i: target[x] for i,x in enumerate(selector) if x!=9}
    if specialized != EXPECTED:
        raise ValueError('Battle specialized opcode mapping changed')
    subtype = [struct.unpack_from('<I',raw,SUBTYPE_TARGETS+4*i)[0]-BASE for i in range(7)]
    if subtype != [0x11447A,0x11449E,0x1144D8,0x1144AE,0x1144C8,0x1144BE,0x11447A]:
        raise ValueError('Battle 86 subtype mapping changed')
    md = capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    slices = []
    for begin,end,purpose in SLICES:
        body = raw[begin:end]
        ins = list(md.disasm(body,BASE+begin))
        if not ins or ins[-1].address+ins[-1].size != BASE+end:
            raise ValueError(f'Unaligned battle dispatch slice {begin:X}')
        slices.append({'begin_rva':f'{begin:X}','end_rva_exclusive':f'{end:X}',
                       'purpose':purpose,'bytes_hex':body.hex(),
                       'sha256':hashlib.sha256(body).hexdigest(),
                       'instructions':[{'rva':f'{i.address-BASE:X}',
                                        'instruction':f'{i.mnemonic} {i.op_str}'} for i in ins]})
    entries = []
    for opcode in range(FIRST,LAST+1):
        x = selector[opcode-FIRST]
        current = world['s2c'][opcode]
        entries.append({'opcode':f'{opcode:02X}', 'selector':x,
                        'battle_case_rva':f'{target[x]:X}',
                        'battle_dispatch_class':'SPECIALIZED' if x!=9 else 'DEFAULT',
                        'length_kind':current['length_kind'],
                        'logical_size':current['logical_size'],
                        'world_default_consumer':current['world_default_consumer']})
    counts = {
        'battle_dispatch_indexed_opcode_range_entries':len(entries),
        'battle_specialized_dispatch_opcodes':len(specialized),
        'battle_default_dispatch_opcodes_within_range':len(entries)-len(specialized),
        'battle_specialized_that_are_world_default':sum(world['s2c'][o]['world_default_consumer'] for o in specialized),
        'battle_86_subtype_selector_values':len(subtype),
        'battle_86_distinct_subtype_case_rvas':len(set(subtype)),
    }
    return {'format':'god2-current-native-s2c-battle-dispatch-frontier-v1',
            'native_image':IMAGE,'native_sha256':PIN,
            'method':'PINNED_BATTLE_DISPATCH_TABLE_AND_BOUNDED_DISASSEMBLY',
            'world_index_sha256':hashlib.sha256((ROOT/'static-packet-index.json').read_bytes()).hexdigest(),
            'opcode_first':f'{FIRST:02X}','opcode_last':f'{LAST:02X}',
            'selector_bytes_hex':selector.hex(),
            'target_table_bytes_hex':raw[TARGETS:TARGETS+40].hex(),
            'subtype_target_table_bytes_hex':raw[SUBTYPE_TARGETS:SUBTYPE_TARGETS+28].hex(),
            'counts':counts,'specialized_opcode_cases':{f'{k:02X}':f'{v:X}' for k,v in specialized.items()},
            'battle_86_subtype_cases':{str(i):f'{v:X}' for i,v in enumerate(subtype)},
            'entries':entries,'slices':slices,
            'limits':['Battle dispatch is a different state from WORLD dispatch; no combined completion denominator follows.',
                      '86 subtype 0 and 6 share an entry address, not necessarily semantics.',
                      '83 action subdispatches, 86 field variants and battle timing/state remain separate inventories.',
                      'An opcode case is not proof of a formal server emission, client acceptance or completed gameplay route.'],
            'tests_builds_client_execution_live_mutation':False}


def main():
    out=ROOT/'s2c-battle-dispatch-frontier-v1.json'
    if out.exists():
        raise FileExistsError('Preserve previous battle dispatch evidence')
    value=recover()
    out.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(out),'counts':value['counts']}))


if __name__=='__main__':
    main()
