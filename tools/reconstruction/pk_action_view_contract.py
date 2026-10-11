"""Pin current-native PK action-view dependencies statically; no execution/tests."""
import hashlib
import json
import struct
import capstone
from .archive_inputs import ArchivedInputs, SERVER

IMAGE='artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
PIN='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
RANGES=(
    ('native35_side_and_context_builder',0x118e50,0x118ed8),
    ('native83_source_division_masks_basic_outcome',0x116bb1,0x116cb2),
    ('manager_forwards_payload_after_opcode',0x117152,0x117198),
    ('action_lookup_dispatch_and_basic_forwarding',0x12c520,0x12c645),
    ('skill3_51_pointer_scan_global_definition_and_result',0x12c731,0x12c899),
    ('signed_display_word',0x12b48e,0x12b4ba),
    ('bounded_outcome_table_lookup',0x12bfc0,0x12bff3),
    ('manager_batch_group_comparison',0x114389,0x1143c0),
)

def main():
    reader=ArchivedInputs()
    try:raw=reader.read(IMAGE)
    finally:reader.close()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise ValueError('Original native pin differs')
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    spans=[]
    for name,begin,end in RANGES:
        code=raw[begin:end]
        spans.append({'name':name,'begin_rva':f'{begin:X}','end_rva_exclusive':f'{end:X}',
            'bytes_hex':code.hex(),'sha256':hashlib.sha256(code).hexdigest(),
            'instructions':[{'rva':f'{i.address-0x400000:X}','bytes_hex':i.bytes.hex(),
                'mnemonic':i.mnemonic,'operands':i.op_str} for i in md.disasm(code,0x400000+begin)]})
    data={'format':'god2-static-pk-action-view-v1','mapped_image':IMAGE,'sha256':PIN,
        'method':'STATIC_DISASSEMBLY_OF_ORIGINAL_SELECTED_BYTES',
        'tests_builds_native_client_emulation_network_live_db':False,'spans':spans,
        'action_dispatch_table':{'rva':'12CC3C','bytes_hex':raw[0x12cc3c:0x12cc3c+23*4].hex(),
            'targets_rva':[f'{t-0x400000:X}' for t in struct.unpack_from('<23I',raw,0x12cc3c)]},
        'outcome_table':{'rva':'171610','bytes_hex':raw[0x171610:0x171610+67].hex(),
            'index0':raw[0x171610],'index28':raw[0x171610+28]},
        'qualified_field_dependencies':[
            '118E50 side flag derives current A/B command controls; raw context fromB+3C. Server expects explicit owned view policy, never a roomID-derived context.',
            '116BB1 reads logical83 source+2 and uses /14,%14; EBP=logical+1, masks atEBP+4 are logical5/7. Two-view side exchange is CUSTOM projection.',
            '117183 forwards payload logical+1 to12C520 with source/target side+slot. Basic table action1 targets12C5D3; skill3 targets12C731.',
            'Basic forwards payload WORD8=logical9 and BYTE10=logical11 to12B060. Signed display12B48E remains separate from a damage formula.',
            'Basic outcome payload BYTE11=logical12; skill3 outcome BYTE13=logical14 and scalar selectorBYTE12=logical13; bounded12BFC0 uses171610,0->9 death,28->0 live.',
            'Skill3 payload BYTE10/11=logical11/12 selects id/kind, scans51 actor+DF8 pointers and logs at12C781 if absent. Global definition address later assignedactor+EC4 is not an owned carried-skill list.',
            '114389 group comparison affects batch consumption. Fresh raw group/counter templates are caller-supplied, not inferred from shared revision.'
        ],
        'source':'RecoveredPkRelativeView / RecoveredBattleAttackPresentation / RecoveredPkActionProjection / RecoveredPkCommandSelection / OwnedPkRoomState::act_native',
        'open':['True owned raw/profile/cycle/group inputs and refresh',
            'Opponent PLAYER actor+DF8 cache initialization and full skill consumer',
            'RoomAuthority live dual Session entry, turn permits, genuine0B/action2 receipts, transport callbacks',
            'Terminal WORLD/resource/reward/reconnect recovery and full opcode variants',
            'Enemy four attack/defense,primary/elements/full carried skills remainUNKNOWN'],
        'new_connected_opcodes':0,'native_acceptance':False,'deployment':False}
    out=SERVER/'artifacts/integration/packet-connections-20261006/pk-action-view-static-contract.json'
    if out.exists():raise FileExistsError('Preserve earlier evidence; choose a new version')
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(out),'original_static_spans':len(spans),'execution':'STATIC_ONLY'}))

if __name__=='__main__':main()
