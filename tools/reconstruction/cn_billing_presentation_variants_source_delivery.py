"""Recover primary billing switch, ProgramMsg lineage and readonly operands.

File/PE/CSV accounting only; never execute a loader, formatter or account route.
"""
import csv
import difflib
import hashlib
import io
import json
import re
from pathlib import Path
import capstone
import pefile
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT

NAME='cn-billing-presentation-variants-source-01'
ROUND='20261008-cn-billing-presentation-variants-source'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
OLD_CN=Path('C:/Users/risei/Desktop/God2-xjz/God2-Server-CN')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=('src/cn/protocol/CnAccountBilling.h',
 'docs/research/cn-billing-presentation-variants-source-20261008.md',
 'tools/reconstruction/cn_billing_presentation_variants_source_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
 'Opaque billing byte5 and native1D AA..CB server serialization/rights remain unknown; no zero/default values supplied.',
 'Actual runtime ProgramMsg resource owner/pointers and assertion exits are not acquired/emulated or proven by static tables.',
 'Eight display cases/default8/assertion>=9 are not all gameplay/state variants, permissions or native billing policy.',
 'Actual common snapshot/write authority, entitlement/deadline/catalog/native07/22/world/bootstrap/Application providers remain unconfigured.',
 'All TW/CN/PC/web/WSS authoritative gameplay/numeric64/stack99/full denominator/final validation/release remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=81:raise RuntimeError('Expected retained81-file before snapshot')
    old={r['path']:(out/r['snapshot']).read_bytes() for r in before}
    books=('docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json')
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{e}' for e in ('json','md')}
    protected=[]
    for row in before:
        rel=row['path']
        if sha(old[rel])!=row['sha256']:raise RuntimeError('Before snapshot differs')
        if rel not in set(SOURCES)|set(books)|reports:
            if (ROOT/rel).read_bytes()!=old[rel]:raise RuntimeError('Protected source differs: '+rel)
            protected.append(row)
    prior=(out/'retained-prior/cn-stored-account-profile-source-01/manifest.json').read_bytes()
    if sha(prior)!='ccec8709d7ebbfda9d7d7f3656c16c6054c2e3498e40d53ae8df1bd237d2d522' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned input differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);native=[]
    for address in ('00443FA0','00445040'):
        paths=list(RECOVERY.glob('part_*/'+address+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Metadata not unique')
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('Missing extent')
        size=int(match.group(1));va=int(address,16);code=view.read(va-ib,size)
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        save('native/functions/'+address+'.asm',('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(code,va))+'\n').encode())
        native.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),whole_cfg_claimed=False))
    cells=view.read(0x44445c-ib,32);save('native/tables/0044445C.bin',cells)
    targets=[int.from_bytes(cells[x:x+4],'little') for x in range(0,32,4)]
    expected=[0x44430c,0x4443ca,0x4443d5,0x4443e0,0x4443e8,0x4443f0,0x4443f8,0x444400]
    if targets!=expected:raise RuntimeError('Primary billing dispatch differs')
    ids_raw=view.read(0x886918-ib,22);save('native/tables/00886918.bin',ids_raw)
    ids=[int.from_bytes(ids_raw[x:x+2],'little') for x in range(0,22,2)]
    if ids!=[319,320,321,322,323,324,478,651,657,688,689]:raise RuntimeError('Native label table differs')
    loader=view.read(0x4294cb-ib,0x4295f6-0x4294cb)
    save('native/ranges/ProgramMsg-loader.bin',loader)
    save('native/ranges/ProgramMsg-loader.asm',('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in md.disasm(loader,0x4294cb))+'\n').encode())
    paths=list(RECOVERY.glob('part_*/00428c80_*.c'))
    if len(paths)!=1:raise RuntimeError('Loader source not unique')
    save('native/ranges/00428C80-metadata.c',paths[0].read_bytes())
    literal=view.read(0x7ee944-ib,11)
    if literal!=b'ProgramMsg\0':raise RuntimeError('Native section literal differs')
    save('native/literals/007EE944.bin',literal)
    resource=base/'cn-directory-display-fields-01/native/resources'
    receipt_raw=(resource/'account-phase-evidence.json').read_bytes();receipt=json.loads(receipt_raw)
    packed=(CN.parent/'Data2/Patch/Comm/message.csvZ').read_bytes();plain=(resource/'message.csv').read_bytes()
    if receipt['client_sha256']!=SHA or receipt['asset']['codepage']!=936 or sha(packed)!=receipt['asset']['sha256'] or sha(plain)!=receipt['asset']['decoded_sha256']:
        raise RuntimeError('Pinned resource receipt differs')
    save('resources/message.csvZ',packed);save('resources/message.csv',plain);save('resources/prior-account-phase-evidence.json',receipt_raw)
    rows=list(csv.reader(io.StringIO(plain.decode('cp936'))));sections={}
    for section in ('ProgramMsg','SystemMessage'):
        starts=[n for n,row in enumerate(rows) if row and row[0]==section]
        if len(starts)!=1:raise RuntimeError('Resource section not unique')
        start=starts[0];count=int(rows[start][1]);values={}
        for n,row in enumerate(rows[start+1:start+1+count],start+2):
            ident=int(row[0])
            if ident in values:raise RuntimeError('Duplicate section ID')
            values[ident]=dict(id=ident,csv_row=n,cells=row,cells_cp936_hex=[s.encode('cp936').hex() for s in row])
        if any(ident not in values for ident in ids):raise RuntimeError('Missing label resource')
        sections[section]=dict(declared_rows=count,selected={str(i):values[i] for i in ids})
    dump('resources/selected-section-rows.json',sections)
    rejected=OLD_CN/'artifacts/native/20261006-cn-creation-fields-01/system-message-resources.json'
    rejected_raw=rejected.read_bytes();save('resources/rejected-SystemMessage-source.json',rejected_raw)
    dump('resources/rejected-source-reason.json',dict(source=rejected.as_posix(),sha256=sha(rejected_raw),
        reason='SystemMessage same-ID rows are not billing labels/formats; actual pointer owner+B2F60 uses ProgramMsg.',
        original_historical_source_unchanged=True))
    for segment in ('cn-billing-byte5-agent-01','cn-account-tail-agent-01'):
        save('retained-inputs/'+segment+'/findings.json',(base/segment/'findings.json').read_bytes())
    labels=[321,319,323,324,478,651,688,689]
    cases=[dict(effective_paytype=i,primary_cell=f'{0x44445c+4*i:08x}',primary_target=f'{target:08x}',
        label_programmsg_id=labels[i],rows=[9,10,11],action='date-and-points' if i<=2 else 'label-and-clear-details',
        date_programmsg_id=322 if i<=2 else None,points_programmsg_id=320 if i<=2 else None,
        monthly_date_assertion=i==0) for i,target in enumerate(targets)]
    relation=dict(version='cn',direction='S2C',phase='account',opcode='0A',logical_size=17,
        receive_consumer='0047FE30',retained_alias='network[0] ->actual UI+7C',display_consumer='00443FA0',
        primary_dispatch='00444305',primary_table='0044445C',cases=cases,
        raw_paytype_operand='UI+7C',group_operand='UI+8D+group*14h',group_override_values=[6,7],
        default8=dict(target='00444449',billing_rows_written=False,ninth_named_paytype=False),
        assert_ge9=dict(site='004442DD',callee='0053E3D0',return_behavior_qualified=False),
        label_initializer='00445040',label_id_table='00886918',label_globals_start='009EDDE4',
        correct_section='ProgramMsg',loader_match_site='004294CB',resource_owner='UI+16188 = main+464',
        table_member='resource+B2F60',maximum_member='resource+B2F64',one_based_id_pointer_stride=4,
        monthly_date_assertion_operands=['signed year<0','BYTE(month-1)>11','day<1 or day>31'],
        year_zero_triggers_monthly_assertion=False,actual_calendar_validity_recovered=False,
        billing_byte5_semantics_recovered=False,backend_rights_recovered=False,variants_complete=False,
        source_gameplay_handler_connected=False,request_reply_pairing=None)
    dump('native/consumer-relations.json',relation)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress: common stored account Profile source/catalog123/124-file seal',
        native_sha256=SHA,native_functions=native,native_primary_metadata_envelope_bytes=sum(n['metadata_envelope_bytes'] for n in native),
        native_programmsg_loader_range_bytes=len(loader),native_jump_table_bytes=32,native_label_id_table_bytes=22,
        native_section_literal_bytes=11,native_range_overlap_not_unique_byte_count=True,
        cn_billing_presentation_operand_projections_added=1,native_billing_dispatch_cells_qualified=8,
        native_billing_no_row_update_condition_values=1,native_billing_assertion_condition_ranges=1,
        native_billing_group_override_values=2,native_programmsg_label_source_relations_added=1,
        native_programmsg_initialized_ids=ids,native_billing_selected_label_ids=labels,
        unreferenced_in_this_switch_programmsg_id=657,wrong_SystemMessage_resource_promoted=False,
        native_billing_byte5_semantics_recovered=False,native_metadata_tail_semantics_recovered=False,
        source_plan_authority_owner_configured=False,actual_runtime_resource_owner_acquired=False,
        unknown_values_invented=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        levels_changed=False,formal_application_hosted=False,new_packet_values=0,new_native_phase_source_bindings=0,
        new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        build_run=False,tests_run=False,runtime_run=False,Cplusplus_source_run=False,Windows_API_run=False,
        native_execution=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_billing_presentation_variants_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='CN original0A billing display eight cases/default8/assertion>=9 ->exact ProgramMsg owner ->existing issuer billing view',
        version_scope='pinned-cn-billing-presentation-operands-and-resource-lineage-only',
        status='Original display operand view and primary switch/resource relation implemented; billing rights/current native values/hosting remain absent',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual full billing/profile values and rights/Plan/common snapshot write source; native07/22/world/appearance/all gameplay/TW/CN/PC/web/WSS/numeric/stack/full denominator. PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN billing presentation variants ('+ROUND+')\n\n'
            'Qualified actual eight-cell44445C table, group6/7 display override, default8 no billing-row writes and assertion>=9 boundary. '
            'ProgramMsg owner+B2F60/4-byte pointer rows and actual11 WORD label IDs are distinct from SystemMessage; wrong same-ID rows retained as rejected source. '
            'Added readonly presentation operands to SAME CnAccountBilling already supplied by issuer Observation; no rights/date normalization/serializer defaults. '
            'Projection1/resource relation1/eight display cells, new opcode/phase/full owner/full routes0; whole totals/percent null. '
            'Actual native values/rights/Plan/Application and whole scope remain open; no build/test/native/C++/API/DB/deploy. '
            'See research/cn-billing-presentation-variants-source-20261008.md; full goal active.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','native_primary_metadata_envelope_bytes','native_programmsg_loader_range_bytes',
        'cn_billing_presentation_operand_projections_added','native_billing_dispatch_cells_qualified','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
