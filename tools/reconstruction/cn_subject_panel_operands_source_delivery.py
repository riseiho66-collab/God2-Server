"""Preserve pinned CN panel operand source refinement; static files only."""
import csv
import difflib
import hashlib
import io
import json
import re
from pathlib import Path
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT
from .cn_pe_import_directory import FileView
from .cn_preborn_selected_subject_source_delivery import local_cfg

NAME='cn-subject-panel-operands-source-01'
ROUND='20261008-cn-subject-panel-operands-source'
PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=['src/cn/world/CnSubjectPanelOperands.h','src/cn/world/CnWorldConsumerSource.h',
 'docs/research/cn-subject-panel-operands-source-20261008.md',
 'tools/reconstruction/cn_subject_panel_operands_source_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual common subject/recipient/native roster mappings/all field semantics, rules/save/replay/committed issuer/Application remain unconfigured.',
 'Actual UI readiness/bonus/text supplier, all helpers/upstream/state variants and extended numeric/native display remain open; no guessed stats.',
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
    if len(before)!=167:raise RuntimeError('Expected167 before files')
    old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{e}' for e in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before source differs')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(o/'retained-prior/cn-subject-status31-source-01/manifest.json').read_bytes()
    if sha(prior)!='617682e686cbac7f99011edc8c8533d2161df2fc696ed7a913d88d8a99992c00' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe').read_bytes()
    if sha(raw)!=PIN:raise RuntimeError('Pinned PE differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw)
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    recovery=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
    source_paths=['part_0011/004d5030_FUN_004d5030.c','part_0012/004d5440_FUN_004d5440.c',
        'part_0004/00450b80_FUN_00450b80.c','part_0004/00451520_FUN_00451520.c']
    scopes=[];decoded={}
    for rel in source_paths:
        source=(recovery/rel).read_bytes()
        meta=re.search(rb'Address: 0x([0-9a-f]+);.*Size: (\d+) bytes',source)
        if not meta:raise RuntimeError('Primary metadata missing')
        va=int(meta[1],16);size=int(meta[2]);code=view.read(va-0x400000,size)
        cfg,ins=local_cfg(md,code,va,{})
        save('native/source/'+Path(rel).name,source);save(f'native/{va:08X}.bin',code)
        dump(f'native/{va:08X}-cfg.json',cfg)
        save(f'native/{va:08X}-cfg.asm',('\n'.join(f'{a:08x} {x.bytes.hex()} {x.mnemonic} {x.op_str}' for a,x in sorted(ins.items()))+'\n').encode())
        scopes.append(dict(va=f'{va:08X}',bytes=size,sites=len(ins),frontier=cfg['frontier'],primary_source=rel))
        decoded.update(ins)
        if va in [0x4d5030,0x4d5440]:
            prior_native=(b/f'cn-same-opcode-consumer-source-01/native/{va:08x}.bin').read_bytes()
            if code!=prior_native or cfg['frontier']:raise RuntimeError('Retained panel envelope differs')
    dump('native/source-scopes.json',scopes)
    expected={
        0x4d5034:('mov','ecx, dword ptr [esi + 0x430a8]'),
        0x4d503a:('mov','edi, dword ptr [ecx + 0xd0]'),
        0x4d5052:('js','0x4d535b'),0x4d507e:('movsx','eax, byte ptr [edi + 2]'),
        0x4d50f7:('movzx','eax, word ptr [edi + 0x36]'),
        0x4d50fc:('movzx','eax, word ptr [edi + 0x34]'),
        0x4d511c:('sub','ax, 0x65'),0x4d5120:('cmp','ax, 7'),
        0x4d5124:('movzx','eax, word ptr [edi + 0x38]'),0x4d5128:('ja','0x4d524b'),
        0x4d514d:('movzx','eax, word ptr [edi + 0x3a]'),
        0x4d5170:('movzx','eax, word ptr [edi + 0x3c]'),
        0x4d5193:('movzx','eax, word ptr [edi + 0x3e]'),
        0x4d51f9:('movzx','eax, word ptr [esi + 0x42e22]'),
        0x4d5200:('add','eax, dword ptr [edi + 0x4c]'),
        0x4d5219:('movzx','eax, word ptr [esi + 0x42e24]'),
        0x4d5220:('add','eax, dword ptr [edi + 0x50]'),
        0x4d5239:('movzx','eax, word ptr [esi + 0x42e20]'),
        0x4d5243:('add','eax, dword ptr [edi + 0x54]'),
        0x4d5261:('movzx','eax, word ptr [edi + 0x3a]'),
        0x4d527b:('movzx','eax, word ptr [edi + 0x3c]'),
        0x4d5295:('movzx','eax, word ptr [edi + 0x3e]'),
        0x4d532e:('movsx','edx, word ptr [edi]'),
        0x4d5443:('movzx','eax, word ptr [ebp + 8]'),
        0x4d545d:('divss','xmm0, dword ptr [0x7f2c70]'),
        0x4d5465:('cvttss2si','eax, xmm0'),
        0x4d5489:('cmp','bx, word ptr [eax + 0xb2f64]'),
        0x4d5498:('mov','eax, dword ptr [eax + 0x290]'),
        0x4d54aa:('cvtps2pd','xmm0, xmm0'),0x4d54c0:('call','0x4503a0')}
    qualified=[]
    for site,(op,args) in expected.items():
        x=decoded.get(site)
        if not x or (x.mnemonic,x.op_str)!=(op,args):raise RuntimeError('Native operand differs: '+hex(site))
        qualified.append(dict(site=f'{site:08X}',bytes=x.bytes.hex(),mnemonic=op,operand=args))
    dump('native/qualified-operand-sites.json',qualified)
    for va,length,expected_bytes in [(0x7f2c70,4,b'\x00\x00\xc8\x42'),(0x7ed65c,3,b'%d\0'),(0x7ef9b8,6,b'%d/%d\0')]:
        value=view.read(va-0x400000,length)
        if value!=expected_bytes:raise RuntimeError('Pinned literal differs')
        save(f'native/literals/{va:08X}.bin',value)
    previous_resource=b/'cn-world-exit-ui-binding-source-01/resources'
    plain=(previous_resource/'message.csv').read_bytes();packed=(previous_resource/'message.csvZ').read_bytes()
    receipt_raw=(previous_resource/'prior-account-phase-evidence.json').read_bytes();receipt=json.loads(receipt_raw)
    if sha(plain)!=receipt['asset']['decoded_sha256'] or sha(packed)!=receipt['asset']['sha256'] or receipt['client_sha256']!=PIN:
        raise RuntimeError('Qualified message resource differs')
    save('resources/message.csv',plain);save('resources/message.csvZ',packed);save('resources/prior-account-phase-evidence.json',receipt_raw)
    rows=list(csv.reader(io.StringIO(plain.decode('cp936'))));starts=[i for i,r in enumerate(rows) if r and r[0]=='ProgramMsg']
    if len(starts)!=1:raise RuntimeError('ProgramMsg section not unique')
    start=starts[0];value=next((dict(csv_row=i,cells=r,cells_cp936_hex=[s.encode('cp936').hex() for s in r])
        for i,r in enumerate(rows[start+1:start+1+int(rows[start][1])],start+2) if r and r[0]=='164'),None)
    if value is None:raise RuntimeError('ProgramMsg164 absent')
    dump('resources/programmsg164-source.json',value)
    save('retained-native-consumer/old-report.md',(ROOT/'docs/research/cn-same-opcode-consumer-source-20261007.md').read_bytes())
    relations=dict(version='cn',native_sha256=PIN,opcode='31',direction='S2C',phase='world-connection-1',
        native_panel_consumer='004D5030',native_metric_consumer='004D5440',
        retained_consumer_evidence='cn-same-opcode-consumer-source-01',
        corrected_old_decompiler_word_signedness=True,word_offsets_zero_extended=['34','36','38','3A','3C','3E'],
        special_identifier_words=list(range(101,109)),ui_bonus_offsets_for_controls_D_E_F=['42E22','42E24','42E20'],
        native_scalar_argument_format='%d',native_pair_argument_format='%d/%d',
        native_decimal_bits_preserved=True,special_missing_ui_bonus_is_unknown=True,
        native_32_bit_add_presentation_not_common64_formula=True,
        metric_numerator='unsigned rowWORD28',divisor_float_bits='42C80000',divisor_literal_va='007F2C70',
        programmsg_pointer_index=164,signed_programmsg_count_minimum=165,
        static_programmsg164_cells=value['cells'],static_label_not_actual_runtime_text_provider=True,
        metric_native_double_vs_static_two_integer_format_unresolved=True,
        projection='CnSubjectPanelOperands',existing_world31_projected_row_method='OwnedRowUpdate31::panel_operands',
        native_snapshot_or_pointer_required=False,stat_names_or_common_formulas_supplied=False,
        actual_ui_rule_save_replay_issuer_configured=False,formal_application_hosted=False,complete_route=False)
    dump('native/panel-operand-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='no progress:status reply only; resumed concrete native/source work',
        native_primary_metadata_bytes=sum(x['bytes'] for x in scopes),native_local_normal_entry_CFGs=len(scopes),
        native_instruction_sites=sum(x['sites'] for x in scopes),native_primary_operands_qualified=len(qualified),
        cn_subject_panel_operand_projections_added=1,cn_existing_world31_panel_source_bindings_added=1,
        cn_old_word_signedness_refinements_added=1,cn_metric_literal_source_relations_added=1,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,actual_ui_rule_save_replay_issuer_configured=False,formal_application_hosted=False,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        native_snapshot_required=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        build_run=False,tests_run=False,runtime_run=False,native_execution=False,Cplusplus_source_run=False,
        Windows_API_run=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    lp=ROOT/books[1];ledger=json.loads(lp.read_text(encoding='utf-8'))
    if any(s['name']==NAME for s in ledger['dual_client_source_segments']):raise RuntimeError('Preserve ledger segment')
    ledger['dual_client_source_segments'].append(dict(name=NAME,round=ROUND,
        version_scope='pinned-cn-world31-panel-operands-source-only',
        status='Exact readonly projected-row panel operands; unsigned WORD refinement; actual UI/common semantics/rules/issuer/Application incomplete',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},
        source_owner_chains_added=0,tw_source_owner_chains_added=0,formal_application_hosted=False,
        complete_gameplay_routes_added=0,evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Actual common subject/skill/native roster semantics and UI bonus/text suppliers; rules/save/replay/committed issuers/Application; native84 caller/phase, all TW/CN/web routes/numeric64/stack99/full denominator. Runtime import deferred PHASE1.'
    lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN WORLD31 panel operand source refinement ('+ROUND+')\n\n'
            'New exact readonly panel operands reuse existing WORLD31 projected row. Primary MOVZX proves all six row34/36/38/3A/3C/3E WORD inputs unsigned; retain old113 seal/report and separately correct its decompiler signedness statement. '
            'Special101..108 bonus WORDs kept separate, absent remains unknown, D/E/F use UI42E22/24/20; native32 presentation ADD is not common64 calculation. '
            'Metric unsigned row28 / pinned100.0f and ProgramMsg164 pointer source retained, static two-integer text versus native double remains unresolved; no guessed stat labels/formulas. '
            'New projection1/existing row handoff1/signedness refinement1/literal relation1; new opcode/phase/owner/full route0; actual common/UI/rules/save/replay/issuer/Application and full goal remain open. PHASE1 no builds/tests/native/API/server/SQL/deploy.\n')
    origins=[]
    for rel in SOURCES+books:
        value=(ROOT/rel).read_bytes();save('source/current/'+rel,value);origins.append(dict(path=rel,bytes=len(value),sha256=sha(value)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),value.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ['round','native_primary_metadata_bytes','native_instruction_sites','native_primary_operands_qualified','cn_subject_panel_operand_projections_added','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
