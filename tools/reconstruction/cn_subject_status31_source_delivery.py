"""Preserve WORLD31 source publication and reused native operands; no runtime."""
import difflib
import hashlib
import json
from pathlib import Path
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT
from .cn_pe_import_directory import FileView
from .cn_preborn_selected_subject_source_delivery import local_cfg

NAME='cn-subject-status31-source-01';ROUND='20261008-cn-subject-status31-source'
SOURCES=['src/cn/protocol/CnSubjectStatus31.h','src/cn/world/SharedSubjectStatusPublication.h',
 'src/cn/world/SharedSubjectStatusPublication.cpp','src/cn/world/CnWorldConsumerSource.cpp',
 'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
 'docs/research/cn-subject-status31-source-20261008.md',
 'tools/reconstruction/cn_subject_status31_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual common subject/recipient mapping, rules/save/durable replay/committed issuer/Application remain unconfigured; WORD native identity/ordinal is not a common key.',
 'WORLD31 helper resources/all upstream/state variants and same-value C2S31 causality remain open; no gameplay/stat names invented.',
 'Actual CN skill import/provider/common skill mapping/preborn rules/native84 caller/initial issuer remain open.',
 'Full TW/CN/PC/web/WSS/all gameplay/numeric64/stack99/whole-game denominator and later comprehensive tests/repair/recovery release remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';o=b/NAME
    if not (o/'before-manifest.json').exists() or (o/'findings.json').exists():raise RuntimeError('Fresh before required')
    def save(rel,data):
        p=o/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((o/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=162:raise RuntimeError('Expected162 before files')
    old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{e}' for e in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before source differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(o/'retained-prior/cn-shared-skill-catalog-import-source-01/manifest.json').read_bytes()
    if sha(prior)!='bc0c23b651b0af39e2e7084887075ef1115d322e6ba72e4f44d842754e7ed139' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe').read_bytes()
    pin='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
    if sha(raw)!=pin:raise RuntimeError('Pinned PE differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw)
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    scopes=json.loads((o/'native/source-scopes.json').read_text(encoding='utf-8'));decoded={}
    for item in scopes:
        va=int(item['va'],16);code=(o/f'native/{va:08X}.bin').read_bytes()
        if code!=view.read(va-0x400000,item['bytes']):raise RuntimeError('Saved primary bytes differ')
        cfg,ins=local_cfg(md,code,va,{})
        if cfg['frontier'] or len(ins)!=item['sites']:raise RuntimeError('Native local CFG source differs')
        decoded.update(ins)
    expected={
        0x4d58c1:('mov','eax, dword ptr [edi + 0x430a8]'),
        0x4d58c7:('lea','esi, [eax + 0xd8]'),0x4d58cd:('movzx','eax, byte ptr [eax + 0xd4]'),
        0x4d58d8:('movsx','cx, byte ptr [edx]'),0x4d58e0:('cmp','word ptr [esi], cx'),
        0x4d58e6:('add','esi, 0x3ec'),0x4d5903:('movzx','eax, word ptr [edx + 2]'),
        0x4d5907:('mov','dword ptr [esi + 0x44], eax'),0x4d5923:('mov','dword ptr [esi + 0x54], eax'),
        0x4d5951:('mov','word ptr [esi + 0x28], ax'),0x4d595f:('mov','byte ptr [esi + 0x5a], al'),
        0x4d59be:('mov','dword ptr [eax + 0xd0], esi'),0x4d59ca:('mov','byte ptr [eax + 0xcf], bl'),
        0x4d4e0c:('js','0x4d4ebc'),0x4d4e24:('jge','0x4d4ebc'),
        0x4d4e3d:('imul','eax, eax, 0x3ec'),0x4d4e4a:('mov','dword ptr [ecx + 0xd0], eax')}
    qualified=[]
    for site,(op,args) in expected.items():
        actual=decoded.get(site)
        if not actual or actual.mnemonic!=op or actual.op_str!=args:raise RuntimeError('Qualified native operand differs')
        qualified.append(dict(site=f'{site:08X}',bytes=actual.bytes.hex(),mnemonic=op,operand=args))
    dump('native/qualified-operand-sites.json',qualified)
    previous=b/'cn-same-opcode-consumer-source-01/native'
    for rel in ['consumer-relations.json','primary-table-relations.json','function-envelopes.json','004d58b0.bin']:
        save('retained-native-consumer/'+rel,(previous/rel).read_bytes())
    if (previous/'004d58b0.bin').read_bytes()!=(o/'native/004D58B0.bin').read_bytes():raise RuntimeError('Retained consumer differs')
    tables=json.loads((previous/'primary-table-relations.json').read_text(encoding='utf-8'))
    table=next(row for row in tables if row['opcode']=='31')
    for key,expected_hex in [('world_cell_va',table['world_cell_bytes']),('length_cell_va',table['length_cell_bytes']),('length_target',table['length_return_bytes'])]:
        value=view.read(int(table[key],16)-0x400000,len(bytes.fromhex(expected_hex)))
        if value.hex()!=expected_hex:raise RuntimeError('Retained primary table differs')
        save('native/table-'+key+'.bin',value)
    # A qualified primary-table target is a permitted decoding root. The final
    # dispatcher tail outside this32B span stays an explicit open frontier.
    target=int(table['world_target'],16);code=view.read(target-0x400000,32)
    cfg,ins=local_cfg(md,code,target,{})
    call=ins.get(0x491356)
    if not call or call.mnemonic!='call' or call.op_str!='0x4d58b0':raise RuntimeError('World31 call source differs')
    save('native/WORLD31-primary-table-case.bin',code);dump('native/WORLD31-primary-table-case-cfg.json',cfg)
    save('native/WORLD31-primary-table-case-cfg.asm',('\n'.join(f'{a:08x} {x.bytes.hex()} {x.mnemonic} {x.op_str}' for a,x in sorted(ins.items()))+'\n').encode())
    relations=dict(version='cn',native_sha256=pin,opcode='31',direction='S2C',phase='world-connection-1',logical_size=29,
        retained_native_consumer_evidence='cn-same-opcode-consumer-source-01',primary_dispatch_and_length_table=table,
        native_target_match='signed BYTE->WORD; first equal WORD in actual ordered roster; no insertion on miss',
        primary_consumer='004D58B0',same_actual_selected_pointer_write='role+D0',same_ordinal_write='role+CF',
        shared_view='CnSubjectStatus31',existing_readonly_projection_reuses_same_view=True,
        source_publisher='SharedSubjectStatusPublication',bound_inside_actual_1C_same_ready_lease=True,
        binding_emits_nothing=True,actual_common_committed_event_required=True,
        real_subject_recipient_rules_save_durable_replay_event_order_and_new_revision_qualifier_required=True,
        old_pre_commit_native_Current_not_used=True,native_snapshot_or_pointer_required=False,
        source_before_queue_and_queue_accepted_post_commit_qualification=True,
        immutable_actual_records_owned_through_transport_completion=True,client_request31_pairing=None,
        actual_common_rule_save_replay_issuer_configured=False,formal_application_hosted=False,complete_route=False)
    dump('source/status31-publication-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:140 pinned CN shared-table import source and seals',
        native_primary_metadata_bytes=sum(x['bytes'] for x in scopes),native_local_normal_entry_CFGs=len(scopes),
        native_instruction_sites=sum(x['sites'] for x in scopes),native_primary_operands_qualified=len(qualified),
        cn_subject_status31_shared_views_added=1,cn_existing_owned_row31_projections_reused=1,
        cn_subject_status31_publication_source_owners_added=1,cn_existing_gameplay_status31_bindings_added=1,
        new_packet_values=0,new_native_phase_source_bindings=1,new_source_owner_chains=1,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,actual_common_rule_save_replay_issuer_configured=False,formal_application_hosted=False,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        native_snapshot_required=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    lp=b/'packet-route-ledger.json';ledger=json.loads(lp.read_text(encoding='utf-8'))
    ledger['cn_subject_status31_source']=dict(facts,evidence=o.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='CN actual committed subject-status event ->same ready lease ->held WORLD31 source publication',
        version_scope='pinned-cn-world1-status31-conditional-post-commit-source-only',
        status='Shared native fields/retained row projection and actual event output source; real common subject/issuer/rules/save/replay/Application unconfigured',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={'world-connection-1':['31']},
        source_owner_chains_added=1,tw_source_owner_chains_added=0,formal_application_hosted=False,
        complete_gameplay_routes_added=0,evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Actual common subject/skill/native roster mappings, source issuer/rules/save/replay/Application; WORLD31 payload semantics/helpers/all variants, native84 caller/timing. CN import execution deferred PHASE1; full TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator.'
    lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN WORLD31 committed source publication ('+ROUND+')\n\n'
            'Reused existing WORLD31 native consumer/table/first signed-BYTE-to-WORD roster match; new shared view used by prior OwnedRows31 projection and new held post-commit publisher bound in actual1C on same lease. '
            'Actual common subject/native roster/recipient/fields/rules/save/durable replay/new revision/event/order issuer remains unconfigured; no native process memory prerequisite or same-opcode C2S pairing. '
            'One conditional owner and one S2C WORLD31 association, no new opcode/complete route; PHASE1/full goal/numeric64/stack99 and later comprehensive tests/repair/recovery release retained.\n')
    origins=[]
    for rel in SOURCES+books:
        data=(ROOT/rel).read_bytes();save('source/current/'+rel,data);origins.append(dict(path=rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ['round','cn_subject_status31_publication_source_owners_added',
        'new_native_phase_source_bindings','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
