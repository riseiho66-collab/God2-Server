"""Read-only FD subtype12 presentation path upstream of C2S E4 UI gates."""
import hashlib
import json
import struct

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


OUT=SERVER/'artifacts/integration/packet-connections-20261006/fd12-e4-panel-frontier-v1.json'
SLICES=(
    ('fd_world_dispatch',0x69245,0x6925C),
    ('shared_fd_fb_fc_dispatch_guard',0x858B0,0x858E5),
    ('fd_subtype12_ui_case',0x85BBE,0x85C34),
    ('fd_subtype12_option_copy_and_mask',0x955D0,0x956AF),
)


def main():
    if OUT.exists():raise FileExistsError('Preserve prior FD12 evidence')
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
    table=raw[0x85CA4:0x85CD8]
    cases=[f'{struct.unpack_from("<I",table,i*4)[0]-BASE:X}' for i in range(13)]
    if cases[12]!='85BBE':raise ValueError('FD subtype12 target changed')
    value={
        'format':'god2-current-native-fd12-e4-panel-frontier-v1',
        'native_image':IMAGE,'native_sha256':PIN,
        'method':'PINNED_WORLD_FD_DISPATCH_SUBTYPE_SWITCH_AND_UI_COPY',
        'fd_subtype_offset_logical':3,
        'fd_subtype12_case_rva':cases[12],
        'fd_switch_table_rva':'85CA4',
        'fd_switch_table_bytes_hex':table.hex(),
        'fd_subtype_case_rvas_0_to_12':cases,
        'minimum_consumed_logical_size':26,
        'subtype12_consumed_logical_offsets':{
            '4_to_21':'18-byte copy into UI+26108..26119 when logical+22 is nonzero',
            '22':'presentation mode; nonzero calls 4955D0, zero calls 495D50(1)',
            '23':'eight-bit option mask read by 4955D0 when presentation mode is nonzero',
            '24':'branch chooses argument to 495E10, which controls UI+26124',
            '25':'branch chooses argument to 495F40, which controls UI+26126',
        },
        'limits':[
            'The FD length-table kind is u16-variable; this is a minimum consumed prefix, not an exact original producer length.',
            'FB and FC share 858B0 but do not enter its FD subtype switch through their WORLD callsites.',
            'FD subtype12 configures C2S E4 UI availability; no server offer authority or E4 request/reply causality is established.',
            'Unconsumed trailing bytes and any preexisting UI flags are not inferred from this slice.',
        ],
        'slices':slices,'tests_builds_client_execution_deployment':False,
    }
    OUT.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(OUT),'slices':len(slices)}))


if __name__=='__main__':main()
