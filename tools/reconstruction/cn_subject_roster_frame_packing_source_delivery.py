"""Preserve native cursor lineage/existing ordered event frame packing; static."""
import difflib
import hashlib
import json
import re
from pathlib import Path
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT
from .cn_pe_import_directory import FileView
from .cn_preborn_selected_subject_source_delivery import local_cfg

NAME='cn-subject-roster-frame-packing-source-01';ROUND='20261008-cn-subject-roster-frame-packing-source'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=['src/cn/world/SharedSubjectRosterPublication.h','src/cn/world/SharedSubjectRosterPublication.cpp',
 'docs/research/cn-subject-roster-frame-packing-source-20261008.md',
 'tools/reconstruction/cn_subject_roster_frame_packing_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual common subject/recipient/roster/inactive row/name/field/skill semantics/rules/save/durable replay/committed issuer/Application remain unconfigured.',
 'Actual runtime native multi-record/multi-frame receipt, timing/variants/GUI/state recovery/other native paths remain unaccepted; byte cursor/queue source is not gameplay acceptance.',
 'Full TW/CN/PC/web/WSS/all gameplay/numeric64/stack99/denominator and later comprehensive tests/repair/recovery release remain open.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';o=b/NAME
    if not (o/'before-manifest.json').exists() or (o/'findings.json').exists():raise RuntimeError('Fresh before required')
    def save(rel,raw):
        p=o/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
    def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((o/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=179:raise RuntimeError('Expected179 before files')
    old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{e}' for e in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before source differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(o/'retained-prior/cn-subject-roster-publication-source-01/manifest.json').read_bytes()
    if sha(prior)!='7a01d456393320f204097588d6997af246d88d3ed83ebda9939d85ba68080948' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Pinned native input differs')
    view=FileView(pefile.PE(data=raw,fast_load=True),raw)
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled/part_0007')
    scopes=[];decoded={}
    for rel in ['0047a120_FUN_0047a120.c','0047a290_FUN_0047a290.c','0047d2e0_FUN_0047d2e0.c','0047d8d0_FUN_0047d8d0.c','0047a170_FUN_0047a170.c']:
        source=(recovery/rel).read_bytes();meta=re.search(rb'Address: 0x([0-9a-f]+);.*Size: (\d+) bytes',source)
        if not meta:raise RuntimeError('Primary metadata missing')
        va=int(meta[1],16);size=int(meta[2]);code=view.read(va-0x400000,size);cfg,ins=local_cfg(md,code,va,{})
        if cfg['frontier']:raise RuntimeError('Local source CFG frontier differs')
        save('native/source/'+rel,source);save(f'native/{va:08X}.bin',code);dump(f'native/{va:08X}-cfg.json',cfg)
        save(f'native/{va:08X}-cfg.asm',('\n'.join(f'{a:08x} {x.bytes.hex()} {x.mnemonic} {x.op_str}' for a,x in sorted(ins.items()))+'\n').encode())
        scopes.append(dict(va=f'{va:08X}',bytes=size,sites=len(ins),frontier=cfg['frontier']));decoded.update(ins)
    dump('native/source-scopes.json',scopes)
    expected={
        0x47a12e:('mov','eax, dword ptr [edi + 0x1810]'),0x47a134:('mov','ecx, dword ptr [edi + 0x1814]'),
        0x47a13a:('sub','eax, ecx'),0x47a142:('cmovl','esi, eax'),0x47a145:('add','ecx, 0xc10'),
        0x47a15a:('add','dword ptr [edi + 0x1814], esi'),0x47a29e:('setle','al'),
        0x47d2e4:('lea','esi, [ecx + 0x654]'),0x47d2f9:('push','1'),0x47d2fe:('call','0x47a120'),
        0x47d94f:('call','0x47d2e0'),0x47d964:('call','0x567b50'),
        0x47d9a4:('call','0x47d2e0'),0x47da0e:('call','0x47d2e0'),0x47a268:('call','0x47a590')}
    qualified=[]
    for site,(op,args) in expected.items():
        x=decoded.get(site)
        if not x or (x.mnemonic,x.op_str)!=(op,args):raise RuntimeError('Qualified native operand differs: '+hex(site))
        qualified.append(dict(site=f'{site:08X}',bytes=x.bytes.hex(),mnemonic=op,operand=args))
    dump('native/qualified-operand-sites.json',qualified)
    contexts=['src/cn/net/CnTransportSession.h','src/cn/net/CnTransportSession.cpp','src/cn/protocol/CnTransport.h',
        'src/cn/protocol/CnTransport.cpp','src/cn/net/SharedCredentialConnection.cpp']
    for rel in contexts:
        value=(ROOT/rel).read_bytes()
        if rel in old and value!=old[rel]:raise RuntimeError('Transport context changed')
        save('source/retained-context/'+rel,value)
    previous=b/'cn-subject-roster-publication-source-01'
    for rel in ['findings.json','native/roster-declaration-and-publication-relations.json',
        'source/current/src/cn/world/SharedSubjectRosterPublication.h','source/current/src/cn/world/SharedSubjectRosterPublication.cpp']:
        save('retained-144/'+rel,(previous/rel).read_bytes())
    relations=dict(version='cn',native_sha256=PIN,direction='S2C',phase='world-connection-1',actual_record_forms=['30','31','34','35'],
        native_record_reader='0047D8D0',native_one_byte_getter='0047D2E0',native_network_owner='actual channel+654',
        native_decoded_cursor_reader='0047A120',native_remaining_operands='owner1810-owner1814',
        native_decoded_buffer='owner+C10+cursor',native_cursor_advance='owner1814+=actualCopiedBytes',
        native_end_predicate='0047A290 signed extent<=cursor',native_outer_receive='0047A170',
        native_decoder_callee='0047A590',native_whole_graph_or_runtime_claimed=False,
        original_record_bytes_and_order_retained=True,whole_actual_records_packed_without_padding_or_split=True,
        max_logical_per_frame=2560,max_publication_frames=256,max_batch_logical_bytes=655360,
        maxima_are_existing_transport_operational_bounds_not_game_rules=True,
        old_event_total2560_cap_removed=True,old_one_record_one_frame_replaced=True,
        frame_tail_not_padded=True,typed_minimum_record4_implied_preflight_budget=True,
        actual_existing_pending_and_output_frame_capacity_still_required=True,actual_existing_wire_queue_byte_capacity=1048576,
        all_frames_encoded_and_capacity_observed_before_one_game_publication=True,
        actual_original_held_batch_barrier_reused=True,transport_and_codecs_unchanged=True,
        immutable_framing_record_ranges_and_bytes_observed_at_before_queue_and_queue_accepted=True,
        plan_definitions_and_framing_retained_by_completion=True,no_client_ACK_or_delivery_claim=True,
        actual_common_rule_save_replay_issuer_configured=False,formal_application_hosted=False,complete_route=False)
    dump('native/record-cursor-and-frame-packing-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:144 WORLD30 typed source and ordered roster publisher/seals',
        native_primary_metadata_bytes=sum(s['bytes'] for s in scopes),native_local_normal_entry_CFGs=len(scopes),
        native_instruction_sites=sum(s['sites'] for s in scopes),native_primary_operands_qualified=len(qualified),
        cn_existing_ordered_subject_frame_packing_bindings_added=1,cn_immutable_framing_observation_handoffs_added=1,
        cn_existing_subject_publication_capacity_boundaries_strengthened=1,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,actual_common_rule_save_replay_issuer_configured=False,formal_application_hosted=False,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        native_snapshot_required=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    lp=ROOT/books[1];ledger=json.loads(lp.read_text(encoding='utf-8'))
    if any(s['name']==NAME for s in ledger['dual_client_source_segments']):raise RuntimeError('Preserve ledger segment')
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='pinned-cn-world-ordered-subject-event-frame-packing-source-only',
        status='Existing actual committed event publisher packs whole native records across bounded frames; actual common authority/issuer/Application/native acceptance incomplete',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Actual common roster/subject/name/inactive row/recipient/skill/field semantics and committed issuer/rules/save/durable replay/Application; declaration helper initialization/template/current, all native timing/variants/preborn84 caller; full TW/CN/web gameplay/numeric64/stack99/denominator. PHASE1 no runtime import.'
    lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN ordered subject event frame packing ('+ROUND+')\n\n'
            'Existing ordered30/31/34/35 publisher now packs whole actual records into frames<=2560, bounded256-frame batch instead of old event-total2560 cap/one record per frame. No padding/split/reorder, records/definitions stay aligned. '
            'Immutable frame ranges/byte totals retained and supplied to same BeforeQueue/QueueAccepted actual post-commit authority. Existing socket codec/pending/output/wire capacity and held publication unchanged; native byte-cursor/record-reader source retained, not runtime acceptance. '
            'Frame binding1/layout observation1/capacity boundary strengthening1, new opcode/phase/owner/full0; actual common rules/save/replay/issuer/Application/all variants/full goal remain open. PHASE1 no build/test/native/API/server/SQL/deploy.\n')
    origins=[]
    for rel in SOURCES+books:
        value=(ROOT/rel).read_bytes();save('source/current/'+rel,value);origins.append(dict(path=rel,bytes=len(value),sha256=sha(value)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),value.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ['round','native_primary_metadata_bytes','native_instruction_sites','native_primary_operands_qualified','cn_existing_ordered_subject_frame_packing_bindings_added','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
