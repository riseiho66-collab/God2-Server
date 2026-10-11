"""Recover pinned PK/player entry dependencies statically; no execution/tests."""
import hashlib
import json
import struct
from pathlib import Path
import capstone
from .archive_inputs import ArchivedInputs, SERVER

IMAGE='artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
RANGES=(
    ('world82',0x6ae12,0x6ae40),
    ('normal_entry_manager_reset',0x111409,0x11143a),
    ('manager_168_pointer_population',0x11fc40,0x11fd06),
    ('actor_record_reset',0x11fde0,0x11fe36),
    ('manager_lookup_only',0x11e6e0,0x11e76a),
    ('appearance_subtype_dispatch',0x114464,0x1144da),
    ('appearance_mode1_parser',0x1177c0,0x117834),
    ('appearance_components0_3_2_1',0x1182b9,0x118333),
    ('identity_metadata_and_variant_dispatch',0x115c90,0x115df1),
    ('identity_requires_existing_render_handle',0x116149,0x116210),
    ('player_cache_and_local_skill_branch',0x116210,0x11646c),
)

def main():
    archive=ArchivedInputs()
    try:raw=archive.read(IMAGE)
    finally:archive.close()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise ValueError('Selected native image differs')
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    spans=[]
    for name,begin,end in RANGES:
        code=raw[begin:end]
        spans.append({'name':name,'begin_rva':f'{begin:X}','end_rva_exclusive':f'{end:X}',
            'bytes_hex':code.hex(),'sha256':hashlib.sha256(code).hexdigest(),
            'instructions':[{'rva':f'{i.address-0x400000:X}','bytes_hex':i.bytes.hex(),
                             'mnemonic':i.mnemonic,'operands':i.op_str} for i in md.disasm(code,0x400000+begin)]})
    result={'format':'god2-static-pk-player-initialization-v1','mapped_image':IMAGE,'sha256':PIN,
        'method':'STATIC_DISASSEMBLY_OF_ORIGINAL_SELECTED_BYTES',
        'tests_builds_native_client_emulation_network_live_db':False,'spans':spans,
        'variant_table':{'rva':'11662C','bytes_hex':raw[0x11662c:0x11663c].hex(),
                         'targets_rva':[f'{x-0x400000:X}' for x in struct.unpack_from('<4I',raw,0x11662c)]},
        'dependency_chain':[
            'World82 stores raw DWORDs into transition+28/+2C; normal initializer copies them unchanged.',
            '111424 calls11FC40;11FC8E fills manager+38 pointers from inline arena, loops2 sides*14 slots*6 components.',
            'Actor pointers exist after normal reset; initial renderer handle is distinct and must be established.',
            'Battle86 subtype4 handler receives logical+1: position logical2,mode logical3; ordinary1 branch needs WORD logical13=0.',
            '1182B9 resolves components0,3,2,1; appearance logical4..11 remains full packed input. Complete resource/render success not asserted.',
            '1C variant index1 goes116149, copies14 DWORD metadata to existing actor+DB0, rejects handle-1 before later cache processing.',
            '116210 player branch reads existing world-role names/flags through FAC70/FAD20; local side0 identity branch builds own skill pointers only.'
        ],
        'source_projection':'RecoveredBattlePlayerAppearance + RecoveredPkEntryProjection; CUSTOM0086 two-viewer ordering requires owned full records, contexts/bulk/control supplied explicitly.',
        'open':['Two-owner qualified raw snapshot provisioning and native world appearance conversion',
                'Real shared RoomAuthority, canonical combat/skill authority and SQLite CAS/lifecycle',
                'Current native acceptance deferred; enemy four attack/defense,primary/elements/full carried skills remain UNKNOWN']}
    output=SERVER/'artifacts/integration/packet-connections-20261006/pk-player-initialization-static-contract.json'
    if output.exists():raise FileExistsError('Preserve previous static evidence')
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(output),'spans':len(spans),'execution':'STATIC_ONLY'}))

if __name__=='__main__':main()
