"""Pinned current-native S2C83 two-stage action dispatch inventory.

Dispatch addresses classify branches only. They do not establish damage,
skill ownership, server policy, or a complete bidirectional combat route.
"""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE


ROOT = SERVER/'artifacts/integration/packet-connections-20261006'
FIRST_SELECTOR = 0x1171D4
FIRST_TARGETS = 0x1171AC
SECOND_TARGETS = 0x12CC3C
ACTION_COUNT = 23
SLICES = (
    (0x116C80, 0x116C9C, '83 first action BYTE 1..23 selector and default'),
    (0x12C5B6, 0x12C5D3, '83 actor action BYTE 1..23 target table and default'),
)


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Pinned current mapped image changed')
    battle_path=ROOT/'s2c-battle-dispatch-frontier-v1.json'
    battle=json.loads(battle_path.read_text(encoding='utf-8'))
    if battle['native_sha256']!=PIN or battle['specialized_opcode_cases'].get('83')!='11436B':
        raise ValueError('Battle outer 83 dispatch changed')
    selector=raw[FIRST_SELECTOR:FIRST_SELECTOR+ACTION_COUNT]
    first=[struct.unpack_from('<I',raw,FIRST_TARGETS+4*i)[0]-BASE for i in range(10)]
    second=[struct.unpack_from('<I',raw,SECOND_TARGETS+4*i)[0]-BASE for i in range(ACTION_COUNT)]
    if len(selector)!=ACTION_COUNT or any(x>=10 for x in selector) or first[9]!=0x117152 or \
       second[2]!=second[22] or first[selector[2]]!=first[selector[22]]:
        raise ValueError('83 action-table shape changed')
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    slices=[]
    for begin,end,purpose in SLICES:
        body=raw[begin:end]
        ins=list(md.disasm(body,BASE+begin))
        if not ins or ins[-1].address+ins[-1].size!=BASE+end:
            raise ValueError(f'Unaligned 83 action slice {begin:X}')
        slices.append({'begin_rva':f'{begin:X}','end_rva_exclusive':f'{end:X}',
                       'purpose':purpose,'bytes_hex':body.hex(),
                       'sha256':hashlib.sha256(body).hexdigest(),
                       'instructions':[{'rva':f'{i.address-BASE:X}',
                                        'instruction':f'{i.mnemonic} {i.op_str}'} for i in ins]})
    rows=[{'action_hex':f'{i+1:02X}','first_selector':selector[i],
           'first_case_rva':f'{first[selector[i]]:X}',
           'second_actor_case_rva':f'{second[i]:X}'} for i in range(ACTION_COUNT)]
    counts={'s2c83_table_action_values':ACTION_COUNT,
            's2c83_first_distinct_case_rvas':len(set(first)),
            's2c83_second_distinct_actor_case_rvas':len(set(second)),
            's2c83_scalar_attack_projection_qualified_actions':2}
    return {'format':'god2-current-native-s2c83-action-frontier-v1',
            'native_image':IMAGE,'native_sha256':PIN,
            'battle_outer_dispatch_sha256':hashlib.sha256(battle_path.read_bytes()).hexdigest(),
            'method':'PINNED_TWO_STAGE_83_DISPATCH_TABLE_AND_BOUNDED_DISASSEMBLY',
            'first_selector_bytes_hex':selector.hex(),
            'first_target_table_bytes_hex':raw[FIRST_TARGETS:FIRST_TARGETS+40].hex(),
            'second_actor_target_table_bytes_hex':raw[SECOND_TARGETS:SECOND_TARGETS+4*ACTION_COUNT].hex(),
            'counts':counts,'actions':rows,'slices':slices,
            'source_scopes':{
                'RecoveredBattleAttackPresentation':'01,03 scalar one-target presentation only',
                'RecoveredBattleDelta':'0D existing-action nonzero WORD+11 branch only',
                'DiagnosticShunyingFemaleDeity':'07 diagnostic effect path only'},
            'limits':['Shared first/second case RVAs do not prove equivalent action semantics.',
                      '01/03 are only one qualified scalar projection, not all possible uses of these action values.',
                      '23 action selectors are nested within one opcode and not 23 additional opcode types.',
                      'No server emission, native acceptance, complete skill effect or whole-game completion is inferred.'],
            'tests_builds_client_execution_live_mutation':False}


def main():
    out=ROOT/'s2c-battle83-action-frontier-v1.json'
    if out.exists():
        raise FileExistsError('Preserve previous battle83 evidence')
    value=recover()
    out.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(out),'counts':value['counts']}))


if __name__=='__main__':
    main()
