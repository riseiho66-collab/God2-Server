"""Preserve independent current-native S2C C2 length/dispatch/consumer."""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN, LENGTH_TABLE, WORLD_TABLE


OUT=SERVER/'artifacts/integration/packet-connections-20261006/c2-same-opcode-receiver-v8.json'
SLICES=((0x6b261,0x6b279,'S2C C2 world dispatch enters unrelated UI refresh'),
        (0xc2e20,0xc2e33,'S2C C2 UI method ignores packet pointer and refreshes two views'),
        (0xc2890,0xc28c4,'first UI refresh updates 8AA20/8AA24 state'),
        (0xc2a40,0xc2a59,'second UI refresh reads 232DF8 widget state'))


def recover():
    reader=ArchivedInputs()
    try:raw=reader.read(IMAGE)
    finally:reader.close()
    if hashlib.sha256(raw).hexdigest()!=PIN:
        raise ValueError('Pinned native image changed')
    op=0xc2
    leaf=struct.unpack_from('<I',raw,LENGTH_TABLE+4*op)[0]-BASE
    dispatch=struct.unpack_from('<I',raw,WORLD_TABLE+4*op)[0]-BASE
    if leaf!=0x12dc or raw[leaf:leaf+6]!=bytes.fromhex('b803000000c3') or dispatch!=0x6b261:
        raise ValueError('S2C C2 length or WORLD dispatch changed')
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
    return {'format':'god2-current-native-c2-same-opcode-receiver-v8',
            'native_image':IMAGE,'native_sha256':PIN,
            'method':'PINNED_LENGTH_WORLD_DISPATCH_AND_BOUNDED_CONSUMER_DISASSEMBLY',
            's2c_opcode':'C2','logical_size':3,'world_dispatch_rva':'6B261',
            'consumer_rva':'C2E20','body_use_in_C2E20':'NONE_OBSERVED',
            'c2s_c2_pairing':'NOT_PROVEN',
            'limits':['A same-number opcode is not a causal reply.',
                      'The bounded consumer updates UI paths separate from F5-fed OrangeShop fields.',
                      'World dispatch also performs common post-handler work outside the bounded method.'],
            'builds_tests_client_execution_deployment':False,'slices':slices}


def main():
    if OUT.exists():raise FileExistsError('Preserve prior native evidence')
    OUT.write_text(json.dumps(recover(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(OUT)


if __name__=='__main__':main()
