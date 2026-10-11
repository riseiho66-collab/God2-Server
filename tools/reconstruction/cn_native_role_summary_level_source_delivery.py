"""Retain actual CN22 WORLD/BATTLE consumer and source07 level projection."""
import difflib
import hashlib
import json
import re
from pathlib import Path
import capstone
import pefile
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT

NAME='cn-native-role-summary-level-source-01'
ROUND='20261008-cn-native-role-summary-level-source'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
OLD_CN=Path('C:/Users/risei/Desktop/God2-xjz/God2-Server-CN')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=('src/cn/protocol/CnRoleStatus.h','src/cn/auth/SharedCommonCharacterSummarySource.h',
 'src/cn/auth/SharedCommonCharacterSummarySource.cpp','docs/research/cn-native-role-summary-level-source-20261008.md',
 'tools/reconstruction/cn_native_role_summary_level_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
 'Actual native22 role/identity/revision and full native07 metadata/visibility owner remain unconfigured; shape/revision alone is not authority.',
 'CUSTOM-0013 stored role remains diagnostic and is NOT promoted as CN native state or official growth.',
 'CN07 FF local display sentinel differs from native22 level255; all level/gameplay/panel variants/caps are not qualified.',
 'Actual account metadata40/billing16/rights/deadline and group billing/load/location/world/bootstrap/hosting providers remain open.',
 'All TW/CN/PC/web/WSS/native gameplay/shared rules/storage/output/numeric/stack/full denominator and final validation/release remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    old={r['path']:(out/r['snapshot']).read_bytes() for r in before}
    books=('docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json')
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ('json','md')}
    protected=[]
    for row in before:
        rel=row['path']
        if sha(old[rel])!=row['sha256']:raise RuntimeError('Before snapshot differs')
        if rel not in set(SOURCES)|set(books)|reports:
            if (ROOT/rel).read_bytes()!=old[rel]:raise RuntimeError('Protected source differs: '+rel)
            protected.append(row)
    prior=(out/'retained-prior/cn-common-character-summary-source-01/manifest.json').read_bytes()
    if sha(prior)!='3dd092f4722325741ea4b8fbe64cf2cdd9a3107c64ee88a0b15527e2b9127967' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned native input differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);image_base=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);native=[]
    for address in ('00519590','00519640','00443640'):
        paths=list(RECOVERY.glob('part_*/'+address+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Metadata source not unique')
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('Missing native extent')
        size=int(match.group(1));va=int(address,16);code=view.read(va-image_base,size)
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        save('native/functions/'+address+'.asm',('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(code,va))+'\n').encode())
        native.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),source=str(paths[0]),whole_cfg_claimed=False))
    ranges=[]
    def retain(va,size,label):
        code=view.read(va-image_base,size);save('native/ranges/'+label+'.bin',code)
        save('native/ranges/'+label+'.asm',('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(code,va))+'\n').encode())
        ranges.append(dict(va=f'{va:08x}',bytes=size,label=label,sha256=sha(code),whole_cfg_claimed=False))
        return code
    world_cell=retain(0x492a60,4,'world22-cell');world_target=int.from_bytes(world_cell,'little')
    if world_target!=0x491295:raise RuntimeError('WORLD22 target differs')
    world=retain(world_target,20,'world22-selected-branch')
    selector=retain(0x548d98+0x22,1,'battle22-selector')[0]
    battle_cell=0x548c9c+4*selector;battle_target=int.from_bytes(retain(battle_cell,4,'battle22-cell'),'little')
    if selector!=5 or battle_target!=0x54875f:raise RuntimeError('BATTLE22 target differs')
    battle=retain(battle_target,17,'battle22-selected-branch')
    retain(0x548659,30,'battle-selector-dispatch');retain(0x4438be,32,'selection-FF-normalization')
    for code,va in ((world,world_target),(battle,battle_target)):
        ins=list(md.disasm(code,va))
        if sum(i.mnemonic=='call' and i.op_str=='0x519590' for i in ins)!=1 or ins[-1].mnemonic!='jmp':
            raise RuntimeError('Selected primary branch changed')
    saved_inputs=[]
    lengths_path=OLD_CN/'artifacts/native/20261006-cn-baseline/s2c-lengths.json'
    lengths_raw=lengths_path.read_bytes();save('retained-phase-branches/s2c-lengths.json',lengths_raw)
    length_rows=[row for row in json.loads(lengths_raw.decode('utf-8')) if row['opcode']==0x22]
    if len(length_rows)!=1 or length_rows[0]['length']!=25:raise RuntimeError('Retained22 length differs')
    length_row=length_rows[0]
    length_cell=retain(int(length_row['table_va'],16),4,'role22-length-cell')
    length_branch=int(length_row['branch_va'],16);expected_length=bytes.fromhex(length_row['branch_bytes'])
    if int.from_bytes(length_cell,'little')!=length_branch or retain(length_branch,len(expected_length),'role22-length-return')!=expected_length:
        raise RuntimeError('Primary22 length branch differs')
    saved_inputs.append(dict(source=lengths_path.as_posix(),bytes=len(lengths_raw),sha256=sha(lengths_raw)))
    for rel in ('artifacts/native/20261006-cn-dispatch-01/branches/0048fcc0-switch-0-case-7.c.txt',
                'artifacts/native/20261006-cn-dispatch-01/branches/005485f0-switch-0-case-12.c.txt'):
        data=(OLD_CN/rel).read_bytes();save('retained-phase-branches/'+Path(rel).name,data)
        saved_inputs.append(dict(source=(OLD_CN/rel).as_posix(),bytes=len(data),sha256=sha(data)))
    level=ROOT/'artifacts/continuation/numeric64-scope-20261007/native-level-display-01/evidence.json'
    level_raw=level.read_bytes();save('retained-level-display/evidence.json',level_raw)
    consumers=[dict(version='cn',direction='S2C',phase='world-connection-1',opcode='22',logical_size=25,
        caller='0048fcc0',primary_cell='00492a60',primary_branch='00491295',consumer='00519590',
        payload_operand='EDI+1',ui_owner_operand='main+89B26C',actual_role_pointer_member='UI+430A8',
        variants_complete=False,source_gameplay_handler_connected=False),
        dict(version='cn',direction='S2C',phase='battle-connection-2',opcode='22',logical_size=25,
        caller='005485f0',primary_selector='00548dba',selector_value=5,primary_cell='00548cb0',
        primary_branch='0054875f',consumer='00519590',payload_operand='ESI+1',
        ui_owner_operand='actual battle owner member+20',actual_role_pointer_member='UI+430A8',
        variants_complete=False,source_gameplay_handler_connected=False)]
    relation=dict(consumers=consumers,role_status_level_logical_offset=1,role_level_destination='actual retained role+26',
        selection_level_logical_offsets=[19,55],role_panel_formatter_unsigned_byte_max=255,
        selection_FF_local_normalized_value=1,new_projection_rejects_FF_without_changing_native_input=True,
        official_level_cap=None,request_reply_pairing=None,official_role_growth_rules_recovered=False,
        stored_CUSTOM0013_role_promoted=False)
    dump('native/consumer-relations.json',relation)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress: actual common-name producer/catalog121/85-file seal',
        native_sha256=SHA,native_functions=native,native_ranges=ranges,
        native_primary_metadata_envelope_bytes=sum(n['metadata_envelope_bytes'] for n in native),
        native_primary_branch_table_bytes=sum(n['bytes'] for n in ranges),retained_phase_branches=saved_inputs,
        native_ranges_include_overlap_not_unique_byte_count=True,native_role22_length_source=length_row,
        retained_level_display_evidence_sha256=sha(level_raw),cn_native_role22_readers_added=1,
        existing_cn07_explicit_native_level_source_projections_added=1,native_role22_consumer_contexts=2,
        native_role_state_owner_configured=False,actual_native_summary_metadata_owner_configured=False,
        diagnostic_role_CUSTOM0013_promoted=False,role_level_field_width_unchanged=8,levels_changed=False,
        unknown_values_invented=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        formal_application_hosted=False,new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,
        new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,whole_game_route_total=None,
        whole_game_completed_routes=None,whole_game_completion_percent=None,build_run=False,tests_run=False,
        runtime_run=False,Cplusplus_source_run=False,Windows_API_run=False,native_execution=False,
        database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_native_role_summary_level_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(
        name='Actual original CN WORLD/BATTLE22 level BYTE ->explicit same-character native07 level source; no diagnostic role promotion',
        version_scope='pinned-cn-native-role22-common-id-summary-level-source-only',
        status='Full native22 reader and explicit07 level projection implemented; actual role/metadata owner/hosting remain open',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual native22 role/identity/revision and native07 metadata/visibility owner; profile40/billing16/rights/deadline/group fields; all world/gameplay/numeric/TW/PC/web/WSS/full denominator. PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN native role22 summary level source ('+ROUND+')\n\n'
            'Primary-qualified WORLD22 direct cell/branch and BATTLE22 selector/cell/branch reach00519590 with distinct actual UI owners. '
            'Added full original25-byte CN22 reader and explicitly revised same-common-ID07 level source; role255 cannot silently become selection-panel1. '
            'No level field/progression/cap change, no CUSTOM-0013 stored diagnostic promotion, no other raw metadata defaults. '
            'Reader1/existing level projection1/consumer contexts2; opcode/phase/full owner/full routes0. '
            'Actual role/metadata/rights/host remain unconfigured; whole totals/percent null. '
            'No build/test/C++/native/API/DB/deploy. See research/cn-native-role-summary-level-source-20261008.md; full goal active.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),
                fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','native_primary_metadata_envelope_bytes','native_primary_branch_table_bytes',
        'cn_native_role22_readers_added','existing_cn07_explicit_native_level_source_projections_added','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
