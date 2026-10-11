"""Preserve native OrangeShop money labels and BF quantity construction."""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


OUT=SERVER/'artifacts/integration/packet-connections-20261006/bf-orange-shop-money-quantity-v6.json'
ODD_MONEY_VA=0x594910
EVEN_MONEY_VA=0x5948f4
SLICES=(
    (0xcf558,0xcf5d6,'odd 48-byte selected row money assertion and balance/price maximum'),
    (0xcf5d6,0xcf64d,'even 6-byte selected row money assertion and balance/price maximum'),
    (0xcf7fd,0xcf828,'selected quantity increments or wraps at maximum'),
    (0xd0b98,0xd0c62,'even row quantity initialization and displayed unit money'),
    (0xd1af8,0xd1bc2,'odd row quantity initialization and displayed unit money'),
    (0xd18c1,0xd196f,'typed quantity cap and selected quantity times displayed money gate'),
)


def c_string(raw,va):
    p=va-BASE
    return raw[p:raw.index(0,p)]


def recover():
    reader=ArchivedInputs()
    try:raw=reader.read(IMAGE)
    finally:reader.close()
    if hashlib.sha256(raw).hexdigest()!=PIN:
        raise ValueError('Pinned native image changed')
    if struct.unpack_from('<I',raw,0xcf58b)[0]!=ODD_MONEY_VA or \
       struct.unpack_from('<I',raw,0xcf60a)[0]!=EVEN_MONEY_VA:
        raise ValueError('OrangeShop row assertion pointers changed')
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
    odd=c_string(raw,ODD_MONEY_VA)
    even=c_string(raw,EVEN_MONEY_VA)
    if odd!=b'm_osgdSC.vi[iItem].money > 0' or even!=b'm_ogdSC.vi[iItem].money > 0':
        raise ValueError('OrangeShop money assertions changed')
    return {'format':'god2-current-native-bf-orange-shop-money-quantity-v6',
            'native_image':IMAGE,'native_sha256':PIN,
            'method':'PINNED_BOUNDED_DISASSEMBLY_AND_ASSERT_STRING_POINTERS',
            'odd_assertion_va':f'{ODD_MONEY_VA:X}',
            'odd_assertion_bytes_hex':odd.hex(),'odd_assertion':odd.decode('ascii'),
            'even_assertion_va':f'{EVEN_MONEY_VA:X}',
            'even_assertion_bytes_hex':even.hex(),'even_assertion':even.decode('ascii'),
            'bf_quantity_body_byte':2,'bf_row_money_body_bytes':'4..7, zero-extended u16',
            'selected_quantity_native_cap':30,
            'client_balance_gate':'selected quantity times displayed money compared with UI+9697A for even flow; odd flow has UI+96B9E group cap and parallel money displays',
            'limits':['Client money and quantity are not server authority; issued offers and owner balance must be checked independently.',
                      'Daily dialog32 BF remains a separate producer despite shape overlap.'],
            'builds_tests_client_execution_deployment':False,'slices':slices}


def main():
    if OUT.exists():raise FileExistsError('Preserve prior native evidence')
    OUT.write_text(json.dumps(recover(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(OUT)


if __name__=='__main__':main()
