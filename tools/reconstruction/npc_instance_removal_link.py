"""Read-only native slices relating S2C72 pool identity to S2C75 removal."""
import hashlib
import json

import capstone

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import BASE, IMAGE, PIN


OUT = SERVER/'artifacts/integration/packet-connections-20261006/npc-instance-removal-link-v1.json'
SLICES = (
    ('npc72_selector_low_word', 0x6A691, 0x6A695),
    ('npc72_ordinary_constructor_call', 0x6AA82, 0x6AA8E),
    ('ordinary_pool_lookup_identity', 0xCC3B6, 0xCC3C3),
    ('ordinary_pool_store_identity', 0xCC621, 0xCC635),
    ('composite_pool_lookup_identity', 0xCBD7A, 0xCBD87),
    ('composite_pool_store_identity', 0xCBFFC, 0xCC00E),
    ('npc75_removal_dispatch', 0x6AA93, 0x6AAA5),
    ('pool_exact_dword_lookup', 0xCCF80, 0xCCFA2),
)


def main():
    if OUT.exists():
        raise FileExistsError('Preserve prior native evidence')
    reader=ArchivedInputs()
    try: raw=reader.read(IMAGE)
    finally: reader.close()
    if hashlib.sha256(raw).hexdigest()!=PIN:
        raise ValueError('Pinned native image changed')
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    slices=[]
    for name,start,end in SLICES:
        instructions=list(md.disasm(raw[start:end],BASE+start))
        if not instructions or instructions[0].address!=BASE+start or \
           instructions[-1].address+instructions[-1].size!=BASE+end:
            raise ValueError('Native slice boundary changed: '+name)
        body=raw[start:end]
        slices.append({
            'name':name,'begin_rva':f'{start:X}','end_rva_exclusive':f'{end:X}',
            'sha256':hashlib.sha256(body).hexdigest(),'bytes_hex':body.hex(),
            'instructions':[{'rva':f'{i.address-BASE:X}',
                             'instruction':f'{i.mnemonic} {i.op_str}'} for i in instructions],
        })
    value={
        'format':'god2-current-native-npc-instance-removal-link-v1',
        'native_image':IMAGE,'native_sha256':PIN,
        'method':'PINNED_NATIVE_DISPATCH_CONSTRUCTOR_AND_POOL_LOOKUP_SLICES',
        's2c_spawn_opcode':'72','s2c_remove_opcode':'75',
        'npc_pool_world_offset':'1539AED8',
        'instance_identity':'LOW_WORD_OF_S2C72_SELECTOR',
        'removal_identity':'LOW_WORD_AT_S2C75_LOGICAL_PLUS_ONE',
        'limits':[
            'This links native display identity and removal lookup only; it does not recover dynamic despawn authority or timing.',
            'The two high bytes of logical S2C75 are unread in the bounded dispatch slice and remain opaque.',
            'A source-qualified S2C72 scene record does not itself authorize sending S2C75.',
        ],
        'slices':slices,'tests_builds_client_execution_deployment':False,
    }
    OUT.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(OUT),'slices':len(slices)}))


if __name__=='__main__':
    main()
