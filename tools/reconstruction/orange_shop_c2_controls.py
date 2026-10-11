"""Preserve bounded native OrangeShop C2 control producers and F5 field use."""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN, QUEUE


OUT=SERVER/'artifacts/integration/packet-connections-20261006/orange-shop-c2-controls-v7.json'
SLICES=(
    (0xceeb0,0xcef0a,'mode1 conditional UI-flag producer'),
    (0xcffb0,0xd0011,'UI control switch prologue and seven-case jump table'),
    (0xd0024,0xd0069,'mode3 selected F5 type8 field with alternate slot sentinel'),
    (0xd00e6,0xd0111,'mode4 F5 type7 field and mode5 control'),
    (0xd01bb,0xd01fd,'mode6 F5 type8 field after UI gate'),
    (0xd0213,0xd0305,'mode2 F5 type7 field and selected bit position'),
)


def recover():
    reader=ArchivedInputs()
    try:raw=reader.read(IMAGE)
    finally:reader.close()
    if hashlib.sha256(raw).hexdigest()!=PIN:
        raise ValueError('Pinned native image changed')
    direct=(0xceef6,0xd01f8,0xd0300)
    for p in direct:
        if raw[p]!=0xe8 or p+5+struct.unpack_from('<i',raw,p+1)[0]!=QUEUE:
            raise ValueError(f'OrangeShop C2 queue call changed at {p:X}')
    table=[struct.unpack_from('<I',raw,0xd0320+4*i)[0]-BASE for i in range(7)]
    if table!=[0xd0011,0xd0024,0xd0043,0xd0069,0xd00b1,0xd00e6,0xd00fe]:
        raise ValueError('OrangeShop C2 UI switch changed')
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    slices=[]
    for begin,end,purpose in SLICES:
        body=raw[begin:end]
        ins=list(md.disasm(body,BASE+begin))
        if not ins or ins[-1].address+ins[-1].size!=BASE+end:
            raise ValueError(f'Unaligned native slice {begin:X}')
        slices.append({'begin_rva':f'{begin:X}','end_rva_exclusive':f'{end:X}',
                       'purpose':purpose,'sha256':hashlib.sha256(body).hexdigest(),
                       'bytes_hex':body.hex(),
                       'instructions':[{'rva':f'{i.address-BASE:X}',
                                        'instruction':f'{i.mnemonic} {i.op_str}'} for i in ins]})
    return {'format':'god2-current-native-orange-shop-c2-controls-v7',
            'native_image':IMAGE,'native_sha256':PIN,
            'method':'PINNED_BOUNDED_DISASSEMBLY_QUEUE_TARGETS_AND_UI_JUMP_TABLE',
            'c2s_opcode':'C2','logical_size':9,'body_size':8,
            'direct_queue_call_rvas':[f'{p:X}' for p in direct],
            'ui_switch_table_rva':'D0320',
            'ui_switch_case_target_rvas':[f'{p:X}' for p in table],
            'observed_mode_values':[1,2,3,4,5,6],
            'known_fields':{
                'mode1':'body u16 at +0 = 1; other body bytes not explicitly assigned in bounded producer',
                'mode2':'body u16 +0 = 2, +4 = F5 type7 UI+97C88, +6 = selected bit position',
                'mode3':'body u16 +0 = 3, +4 = F5 type8 UI+97CA4, +6 = FFFF or 0001',
                'mode4':'body u16 +0 = 4, +4 = F5 type7 UI+97C88',
                'mode5':'body u16 +0 = 5',
                'mode6':'body u16 +0 = 6, +4 = F5 type8 UI+97CA4',
            },
            'limits':['Unwritten body bytes are retained as opaque, not assumed zero.',
                      'F5-to-C2 field sourcing is proven; C2 response pairing and server authority are not.',
                      'The mode1 producer uses a different UI-flag condition and may have distinct owner context.'],
            'builds_tests_client_execution_deployment':False,'slices':slices}


def main():
    if OUT.exists():raise FileExistsError('Preserve prior native evidence')
    OUT.write_text(json.dumps(recover(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(OUT)


if __name__=='__main__':main()
