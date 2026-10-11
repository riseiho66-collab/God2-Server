"""Read-only native E3 snapshot / E4 delta cache relationship."""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


OUT=SERVER/'artifacts/integration/packet-connections-20261006/e4-pet1-cache-link-v3.json'
SLICES=(
    ('pet_slot_guard',0xA2980,0xA2999),
    ('pet_metadata_gate',0xA29A0,0xA2A04),
    ('e3_snapshot_copy',0xA2BAF,0xA2BC9),
    ('e4_existing_row_gate',0xA3189,0xA31D2),
    ('e4_field_and_bonus_update',0xA31D2,0xA3281),
)


def main():
    if OUT.exists():raise FileExistsError('Preserve prior native evidence')
    reader=ArchivedInputs()
    try:raw=reader.read(IMAGE)
    finally:reader.close()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise ValueError('Pinned native image changed')
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    slices=[]
    for name,start,end in SLICES:
        instructions=list(md.disasm(raw[start:end],BASE+start))
        if not instructions or instructions[0].address!=BASE+start or \
           instructions[-1].address+instructions[-1].size!=BASE+end:
            raise ValueError('Native slice boundary changed: '+name)
        body=raw[start:end]
        slices.append({'name':name,'begin_rva':f'{start:X}',
                       'end_rva_exclusive':f'{end:X}',
                       'sha256':hashlib.sha256(body).hexdigest(),'bytes_hex':body.hex(),
                       'instructions':[{'rva':f'{i.address-BASE:X}',
                                        'instruction':f'{i.mnemonic} {i.op_str}'} for i in instructions]})
    if 0x9E50+42*52!=0xA6D8:raise ValueError('E3/E4 row offset relation changed')
    table=raw[0xA32BC:0xA32CC]
    cases=[f'{struct.unpack_from("<I",table,4*i)[0]-BASE:X}' for i in range(4)]
    value={
        'format':'god2-current-native-e4-pet1-cache-link-v3',
        'native_image':IMAGE,'native_sha256':PIN,
        'method':'PINNED_NATIVE_E3_COPY_AND_E4_EXISTING_ROW_RECEIVER',
        'e3_row':'UI+9E50+slot*52',
        'e4_row':'UI+A6D8+(slot-42)*52',
        'shared_row_for_slots':[42,43,44],
        'bonus_switch_table_rva':'A32BC',
        'bonus_switch_table_bytes_hex':table.hex(),
        'bonus_index_case_rvas':cases,
        'e4_body_fields':{
            'body_0_word':'existing E3 row+2 maximum HP',
            'body_2_word':'existing E3 row+6 maximum MP',
            'body_4_dword_low_12':'existing E3 row+8 physical attack',
            'body_4_dword_bits_12_23':'existing E3 row+12 physical defense',
            'body_4_dword_high_byte':'pet slot 42..44',
            'body_8_dword_low_12':'existing E3 row+16 magical attack',
            'body_8_dword_bits_12_23':'existing E3 row+20 magical defense',
            'body_8_dword_high_byte':'bonus selector 0..3; larger values skip increment',
            'body_12_word':'existing E3 row+36 remaining points',
            'body_14_15':'unread by bounded update path; preserve opaque',
        },
        'existing_row_gate':'slot 42..44, nonzero existing metadata key at row+1C, matching row+26 slot and native metadata lookup',
        'c2s_e4_causality':'UNPROVEN_SAME_NUMBER_AND_0_TO_3_ARE_NOT_CAUSAL_PROOF',
        'authority_and_formula':'UNRECOVERED',
        'slices':slices,
        'tests_builds_client_execution_deployment':False,
    }
    OUT.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(OUT),'slices':len(slices)}))


if __name__=='__main__':main()
