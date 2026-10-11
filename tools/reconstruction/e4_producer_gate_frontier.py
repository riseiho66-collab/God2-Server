"""Read-only current-native C2S E4 UI producer control-flow slices."""
import hashlib
import json

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


OUT=SERVER/'artifacts/integration/packet-connections-20261006/e4-producer-gates-v5.json'
SLICES=(
    ('outer_ui_control_dispatch',0x82B56,0x82B79),
    ('operation3_composite_flags_and_queue',0x95A20,0x95B28),
    ('operations0_1_2_button_gates_and_queue',0x95B30,0x95C53),
    ('operation0_local_toggle',0x95D50,0x95E02),
)


def main():
    if OUT.exists():raise FileExistsError('Preserve prior E4 producer evidence')
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
    value={
        'format':'god2-current-native-c2s-e4-producer-gates-v5',
        'native_image':IMAGE,'native_sha256':PIN,
        'method':'PINNED_BOUNDED_C2S_E4_UI_CONTROL_FLOW',
        'c2s_logical_size':2,'observed_operations':[0,1,2,3],
        'outer_control_guard':'UI control id equals dispatcher-owner+232E0E before 95B30 callback',
        'operation0':'requires local byte+26128==1; calls 95D50(0) then queues E4 00',
        'operation1':'requires local byte+26124==1 and byte+26127==0; queues E4 01',
        'operation2':'requires local byte+26126==1 and byte+26127==0; queues E4 02',
        'operation3':'after composite local flag/message path, scans eight bytes+26129..+26130 and queues E4 03 when any is nonzero',
        's2c_e4_bonus_selector_causality':'UNPROVEN_DIFFERENT_SENDER_BRANCHES',
        'target_pet_slot':'NOT_PRESENT_IN_C2S_PAYLOAD_AND_NOT_ESTABLISHED_BY_THESE_SLICES',
        'limits':[
            'Local UI flags are producer gates, not server authorization or recovered gameplay verbs.',
            'The matching 0..3 numeric ranges in C2S operations and S2C bonus selector do not prove a reply mapping.',
            'Selected-control id at dispatcher-owner+232E0E is not qualified as a pet instance id.',
        ],
        'slices':slices,'tests_builds_client_execution_deployment':False,
    }
    OUT.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(OUT),'slices':len(slices)}))


if __name__=='__main__':main()
