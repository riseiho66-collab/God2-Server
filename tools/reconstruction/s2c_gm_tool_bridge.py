"""Current-native S2C 7B..81/F6 bridge to the GM Tools FS2 window."""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN, LENGTH_TABLE, WORLD_TABLE


OUT=SERVER/'artifacts/integration/packet-connections-20261006/s2c-gm-tool-bridge-v1.json'
OPCODES=(0x7b,0x7c,0x7d,0x7e,0x7f,0x80,0x81,0xf6)
SLICES=((0x6ad6d,0x6ad80,'shared WORLD dispatch to GM bridge'),
        (0x6b9d0,0x6babe,'bridge opcode switch and window-message construction'))


def recover():
    reader=ArchivedInputs()
    try:raw=reader.read(IMAGE)
    finally:reader.close()
    if hashlib.sha256(raw).hexdigest()!=PIN:
        raise ValueError('Pinned native image changed')
    name=raw[0x18cde4:raw.index(0,0x18cde4)]
    if name!=b'GM Tools FS2':
        raise ValueError('GM tool window string changed')
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
    entries=[]
    for op in OPCODES:
        leaf=struct.unpack_from('<I',raw,LENGTH_TABLE+4*op)[0]-BASE
        leaf_bytes=raw[leaf:leaf+6]
        if leaf_bytes[0]!=0xb8 or leaf_bytes[5]!=0xc3:
            raise ValueError(f'Unsupported length leaf {op:02X}')
        logical=struct.unpack_from('<i',leaf_bytes,1)[0]
        dispatch=struct.unpack_from('<I',raw,WORLD_TABLE+4*op)[0]-BASE
        index=raw[0x6bae4+op-0x7b]
        case=struct.unpack_from('<I',raw,0x6bac0+4*index)[0]-BASE
        if dispatch!=0x6ad6d or case not in (0x6ba00,0x6ba12,0x6ba1c,0x6ba2e,0x6ba40,0x6ba52,0x6ba64,0x6ba76):
            raise ValueError(f'GM bridge dispatch changed {op:02X}')
        entries.append({'opcode':f'{op:02X}','logical_size':logical,
                        'forwarded_payload_bytes':logical-1,
                        'length_leaf_rva':f'{leaf:X}',
                        'world_dispatch_rva':f'{dispatch:X}',
                        'bridge_case_index':index,'bridge_case_rva':f'{case:X}'})
    return {'format':'god2-current-native-s2c-gm-tool-bridge-v1',
            'native_image':IMAGE,'native_sha256':PIN,
            'method':'PINNED_LENGTH_WORLD_DISPATCH_SWITCH_AND_STRING_BYTES',
            'window_title_va':'58CDE4','window_title_bytes_hex':name.hex(),
            'window_title':name.decode('ascii'),
            'window_message_immediate':'004A',
            'window_message_interpretation':'WM_COPYDATA-shaped call sequence; import identity not separately resolved',
            'bridge_dispatch_rva':'6B9D0',
            'switch_pointer_table_rva':'6BAC0',
            'switch_pointer_table_bytes_hex':raw[0x6bac0:0x6bae0].hex(),
            'switch_lookup_rva':'6BAE4',
            'selected_lookup_bytes':{f'{op:02X}':raw[0x6bae4+op-0x7b] for op in OPCODES},
            'entries':entries,'slices':slices,
            'limits':['These eight WORLD packets have an external GM-window bridge, not a proven in-game effect.',
                      'S2C payloads, producer state, external-tool behavior and any C2S causality remain unqualified.',
                      'This is not a reason to subtract them from the native packet inventory.'],
            'builds_tests_client_execution_deployment':False}


def main():
    if OUT.exists():raise FileExistsError('Preserve prior bridge evidence')
    value=recover()
    OUT.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(OUT),'opcodes':[x['opcode'] for x in value['entries']],
                      'lengths':[x['logical_size'] for x in value['entries']]}))


if __name__=='__main__':main()
