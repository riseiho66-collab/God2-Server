"""Preserve pinned ProgramMsg supplier/ID-index lineage; static files only."""
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

NAME='cn-program-message-catalog-source-01';ROUND='20261008-cn-program-message-catalog-source'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=['src/cn/assets/CnProgramMessageCatalog.h','src/cn/assets/CnProgramMessageCatalog.cpp',
 'src/cn/world/CnSubjectPanelOperands.h','docs/research/cn-program-message-catalog-source-20261008.md',
 'tools/reconstruction/cn_program_message_catalog_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual catalog revision/Current/Application supplier, GUI readiness/loaded text/format rendering remain unconfigured; source matching is not runtime acceptance.',
 'Actual common subject/recipient/native roster/all field semantics/rules/save/replay/committed issuer and all native upstream/variants remain open.',
 'Full TW/CN/PC/web/WSS/all gameplay/numeric64/stack99/whole-game denominator and later comprehensive tests/repair/recovery release remain open.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';o=b/NAME
    if not (o/'before-manifest.json').exists() or (o/'findings.json').exists():raise RuntimeError('Fresh before required')
    def save(rel,raw):
        p=o/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(raw)
    def dump(rel,v):save(rel,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((o/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=170:raise RuntimeError('Expected170 before files')
    old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{e}' for e in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before source differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(o/'retained-prior/cn-subject-panel-operands-source-01/manifest.json').read_bytes()
    if sha(prior)!='45300c708e07ad09e4fa9eef6ca9aef1adc4c25e49cb91d41d2f0de68f60efdd' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Pinned native input differs')
    view=FileView(pefile.PE(data=raw,fast_load=True),raw)
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
    paths=['part_0002/00428c80_FUN_00428c80.c','part_0002/004231b0_FUN_004231b0.c',
        'part_0002/004234f0_FUN_004234f0.c','part_0005/0045b270_FUN_0045b270.c',
        'part_0072/0076e085_FUN_0076e085.c','part_0012/004d5440_FUN_004d5440.c',
        'part_0004/004503a0_FUN_004503a0.c','part_0004/00451520_FUN_00451520.c']
    scopes=[];decoded={}
    for rel in paths:
        source=(recovery/rel).read_bytes();meta=re.search(rb'Address: 0x([0-9a-f]+);.*Size: (\d+) bytes',source)
        if not meta:raise RuntimeError('Primary metadata missing')
        va=int(meta[1],16);size=int(meta[2]);code=view.read(va-0x400000,size);cfg,ins=local_cfg(md,code,va,{})
        save('native/source/'+Path(rel).name,source);save(f'native/{va:08X}.bin',code)
        dump(f'native/{va:08X}-cfg.json',cfg)
        save(f'native/{va:08X}-cfg.asm',('\n'.join(f'{a:08x} {x.bytes.hex()} {x.mnemonic} {x.op_str}' for a,x in sorted(ins.items()))+'\n').encode())
        scopes.append(dict(va=f'{va:08X}',bytes=size,sites=len(ins),frontier=cfg['frontier'],primary_source=rel));decoded.update(ins)
    dump('native/source-scopes.json',scopes)
    expected={
        0x4294cb:('mov','ecx, 0x7ee944'),0x42954a:('call','0x423150'),
        0x429555:('dec','eax'),0x429577:('call','0x4231b0'),
        0x4295a6:('mov','dword ptr [edx + ecx*4], eax'),
        0x4295cd:('movsx','eax, word ptr [esi + 0xb2f64]'),
        0x4295de:('lea','eax, [ecx + 1]'),0x4295e1:('mov','word ptr [esi + 0xb2f64], ax'),
        0x42321c:('mov','byte ptr [eax], 0'),0x423515:('push','0x2c'),0x423528:('push','0xa'),
        0x423547:('cmp','edi, 0x17b'),
        0x45b356:('push','0x7efee0'),0x45b35c:('call','0x76d12e'),
        0x45b391:('push','0x7efee0'),0x45b3a3:('call','0x76d12e'),
        0x4d545d:('divss','xmm0, dword ptr [0x7f2c70]'),
        0x4d5498:('mov','eax, dword ptr [eax + 0x290]'),
        0x4d54aa:('cvtps2pd','xmm0, xmm0'),0x4d54c0:('call','0x4503a0'),
        0x450400:('call','0x451520')}
    qualified=[]
    for site,(op,args) in expected.items():
        x=decoded.get(site)
        if not x or (x.mnemonic,x.op_str)!=(op,args):raise RuntimeError('Qualified operand differs: '+hex(site))
        qualified.append(dict(site=f'{site:08X}',bytes=x.bytes.hex(),mnemonic=op,operand=args))
    dump('native/qualified-operand-sites.json',qualified)
    for va,value in [(0x7ee944,b'ProgramMsg\0'),(0x7efee0,b'r\0'),(0x7f2c70,b'\x00\x00\xc8\x42')]:
        if view.read(va-0x400000,len(value))!=value:raise RuntimeError('Pinned literal differs')
        save(f'native/literals/{va:08X}.bin',value)
    previous=b/'cn-subject-panel-operands-source-01'
    for rel in ['native/panel-operand-relations.json','findings.json','source/current/src/cn/world/CnSubjectPanelOperands.h','source/current/docs/research/cn-subject-panel-operands-source-20261008.md']:
        save('retained-142/'+rel,(previous/rel).read_bytes())
    for rel in ['message.csv','message.csvZ','prior-account-phase-evidence.json']:
        save('resources/'+rel,(previous/'resources'/rel).read_bytes())
    plain=(o/'resources/message.csv').read_bytes();packed=(o/'resources/message.csvZ').read_bytes()
    if len(packed)!=59375 or sha(packed)!='9c027fdd114073fe9fc88776f7713c0e60575fbe1a2f15059e9bda01a9ec181e' or len(plain)!=112839 or sha(plain)!='994088ac79051df74b3569fc102ab39849594409964a674796bd67fd9d4bc054':
        raise RuntimeError('Pinned resource pair differs')
    # Static byte/record projection only; no decoder/tokenizer/CRT execution.
    header=b'ProgramMsg,1116\r\n'
    if plain[89354:89371]!=header:raise RuntimeError('Qualified ProgramMsg header differs')
    records=[];offset=89371
    for index,line in enumerate(plain[offset:].splitlines(keepends=True)):
        if not line.endswith(b'\r\n') or b'\0' in line or b'"' in line:raise RuntimeError('Qualified line shape differs')
        cells=line[:-2].split(b',')
        if cells[0]!=str(index+1).encode('ascii'):raise RuntimeError('Qualified ID order differs')
        text=cells[1] if len(cells)>1 else b''
        if len(text)>0x17b:raise RuntimeError('Native field limit exceeded')
        records.append(dict(native_csv_id=index+1,native_zero_based_pointer_index=index,source_line=2028+index,
            decoded_offset=offset,raw_line_hex=line.hex(),record_sha256=sha(line),native_column1_cp936_hex=text.hex(),
            source_text=text.decode('cp936'),opaque_tail_cp936_hex=[v.hex() for v in cells[2:]]))
        offset+=len(line)
    if len(records)!=1116 or offset!=112839:raise RuntimeError('ProgramMsg block count differs')
    if records[164]['source_text']!='%6.2f\uff05':raise RuntimeError('Qualified percent source differs')
    dump('resources/programmsg-source-records.json',records)
    relations=dict(version='cn',native_sha256=PIN,opcode='31',direction='S2C',phase='world-connection-1',
        native_loader='00428C80',primary_entry_reaches_programmsg_case=True,csv_id_to_pointer_index='CSV ID minus1',
        native_column1_getter='004231B0',empty_or_absent_column_explicit_NUL=True,native_text_fopen_mode='r',
        native_tokenizer='004234F0',native_field_max_bytes=379,pinned_text_max_bytes=max(len(bytes.fromhex(r['native_column1_cp936_hex'])) for r in records),
        declared_records=1116,empty_text_ids=[r['native_csv_id'] for r in records if not r['native_column1_cp936_hex']],
        opaque_tail_ids=[r['native_csv_id'] for r in records if r['opaque_tail_cp936_hex']],
        metric_pointer_index=164,metric_csv_id=165,metric_format_source=records[164],
        previous142_wrong_candidate_csv_id=164,previous142_mismatch_resolved_for_pinned_source_only=True,
        previous142_source_and_reports_retained=True,actual_runtime_GUI_acceptance=False,
        catalog='CnProgramMessageCatalog',encoded_and_decoded_source_pins_required=True,
        owned_records_and_lookup_current_before_after=True,separate_one_based_id_and_zero_based_index_lookups=True,
        metric_actual_source_text_handoff='CnSubjectPanelOperands::Metric::actual_source_text',
        process_memory_or_native_pointer_required=False,stat_names_or_gameplay_formulas_supplied=False,
        actual_resource_supplier_configured=False,formal_application_hosted=False,complete_route=False)
    dump('native/programmsg-catalog-and-metric-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:142 panel operand source/word refinement and sealed delivery',
        native_primary_metadata_bytes=sum(s['bytes'] for s in scopes),native_local_normal_entry_CFGs=len(scopes),
        native_instruction_sites=sum(s['sites'] for s in scopes),native_primary_operands_qualified=len(qualified),
        cn_programmsg_actual_source_suppliers_added=1,cn_existing_metric_text_source_handoffs_added=1,
        cn_metric_csv_id_pointer_index_corrections_added=1,CN_declared_programmsg_records=1116,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,actual_resource_supplier_configured=False,formal_application_hosted=False,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        native_snapshot_required=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    lp=ROOT/books[1];ledger=json.loads(lp.read_text(encoding='utf-8'))
    if any(s['name']==NAME for s in ledger['dual_client_source_segments']):raise RuntimeError('Preserve ledger segment')
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='pinned-cn-programmsg-supplier-and-world31-metric-source-only',
        status='Pinned owning1116-row ProgramMsg supplier/source metric handoff; CSV ID165 vs index164 corrected; actual source hosting/GUI/gameplay incomplete',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Actual ProgramMsg source revision/current supplier and GUI gate; common subject/skill/native roster field semantics/rules/save/replay/committed issuer/Application; native84 caller/phase and full TW/CN/web gameplay/numeric64/stack99/denominator. PHASE1 no runtime import.'
    lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN ProgramMsg actual catalog / metric source ('+ROUND+')\n\n'
            'New pinned encoded/decoded/current owned1116-row ProgramMsg supplier and existing metric source lookup. Primary loader CSV ID minus1 proves pointer index164 is CSV165 percent format, correcting142 wrong CSV164 candidate while retaining142 seal/source/report. '
            'Native column1 getter explicitly clears absent/empty text; raw tails retained without joining column2. Native text mode preserves the pinned CRLF boundary projection. '
            'Supplier1/existing metric handoff1/ID-index correction1; resource rows are not packets, new opcode/phase/owner/full routes0. Actual source/Application/GUI readiness/rendering/common semantics/rules/save/replay/issuer and full goal remain open; PHASE1 no build/test/native/API/server/SQL/deploy.\n')
    origins=[]
    for rel in SOURCES+books:
        value=(ROOT/rel).read_bytes();save('source/current/'+rel,value);origins.append(dict(path=rel,bytes=len(value),sha256=sha(value)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),value.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ['round','native_primary_metadata_bytes','native_instruction_sites','native_primary_operands_qualified','CN_declared_programmsg_records','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
