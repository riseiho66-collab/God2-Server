"""Preserve the native OrangeShop source assertion tied to S2C EE."""
import hashlib
import json
import struct

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


OUT = SERVER/'artifacts/integration/packet-connections-20261006/bf-orange-shop-identity-v5.json'
ASSERT_RVA = 0xce003
SOURCE_EXPR_VA = 0x5947dc
SOURCE_FILE_VA = 0x594894


def read_c_string(raw, va):
    start=va-BASE
    end=raw.index(0,start)
    return raw[start:end]


def recover():
    reader=ArchivedInputs()
    try:
        raw=reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest()!=PIN:
        raise ValueError('Pinned native image changed')
    call=raw[ASSERT_RVA:0xce017]
    if struct.unpack_from('<I',raw,0xce009)[0]!=SOURCE_FILE_VA or \
       struct.unpack_from('<I',raw,0xce00e)[0]!=SOURCE_EXPR_VA:
        raise ValueError('EE diagnostic pointers changed')
    expression=read_c_string(raw,SOURCE_EXPR_VA)
    source_file=read_c_string(raw,SOURCE_FILE_VA)
    if b'ORANGESHOP_GOODS_DATA_SC' not in expression or \
       not source_file.endswith(b'PMOrangeShop.cpp'):
        raise ValueError('Native OrangeShop identity changed')
    return {
        'format':'god2-current-native-bf-orange-shop-identity-v5',
        'native_image':IMAGE,'native_sha256':PIN,
        'method':'PINNED_EE_DIAGNOSTIC_POINTERS_AND_NATIVE_STRING_BYTES',
        's2c_ee_consumer_rva':'CDF90',
        'assert_call_begin_rva':f'{ASSERT_RVA:X}',
        'assert_call_bytes_hex':call.hex(),
        'assert_call_sha256':hashlib.sha256(call).hexdigest(),
        'source_expression_va':f'{SOURCE_EXPR_VA:X}',
        'source_expression_bytes_hex':expression.hex(),
        'source_expression':expression.decode('ascii'),
        'source_file_va':f'{SOURCE_FILE_VA:X}',
        'source_file_bytes_hex':source_file.hex(),
        'source_file':source_file.decode('ascii'),
        'inference':'S2C EE is OrangeShop goods data; three row counts at logical+5,+6,+8 align with nKindNum,nSaleNum,u8LimitNum in the assertion.',
        'limits':['This source identity does not prove C2S BF economic rules, owner funds or causal response.',
                  'F3 uses the same UI class but has no direct source expression in this artifact.'],
        'builds_tests_client_execution_deployment':False,
    }


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior native evidence')
    OUT.write_text(json.dumps(recover(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(OUT)


if __name__=='__main__':
    main()
