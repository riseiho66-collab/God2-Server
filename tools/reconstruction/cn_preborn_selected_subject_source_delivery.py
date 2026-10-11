"""Static actual selected-subject provenance and existing common-operation handoff.

File/pinned PE/CFG only; never runs clients/C++/services/databases or tests.
"""
import difflib
import hashlib
import json
import re
from collections import deque
from pathlib import Path
import capstone
import pefile
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT

NAME='cn-preborn-selected-subject-source-01'
ROUND='20261008-cn-preborn-selected-subject-source'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=('src/cn/world/CnPrebornSubjectState.h','src/cn/world/CnPrebornSubjectState.cpp',
 'src/cn/world/SharedPrebornChoices.h','src/cn/world/SharedPrebornChoices.cpp',
 'src/cn/world/SharedPrebornWindowSource.h','src/cn/world/SharedPrebornWindowSource.cpp',
 'docs/research/cn-preborn-selected-subject-source-20261008.md',
 'tools/reconstruction/cn_preborn_selected_subject_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
 'Actual CN skill loader/resource/catalog identities and common subject/skills mappings/rules/save/persistent replay/Application remain unconfigured.',
 'Only mode0 inline-role selected-subject layout is qualified; native84 caller and full preborn timing relative1C/pre-world/other variants remain open.',
 'Native pointer/WORD/index/flags and UI bank formula are source operands, not common keys/server cast entitlement/MP charge.',
 'Full TW/CN/PC/web/WSS/common account/world/all gameplay/numeric64/stack99/full denominator and later comprehensive tests/repair/release remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def local_cfg(md,code,entry,tables):
    end=entry+len(code);todo=deque([entry]);decoded={};edges=[];frontier=[]
    while todo:
        pc=todo.popleft()
        if pc in decoded:continue
        if not entry<=pc<end:frontier.append(dict(site=f'{pc:08x}',reason='outside_metadata_code'));continue
        ins=next(md.disasm(code[pc-entry:pc-entry+15],pc,count=1),None)
        if not ins or pc+ins.size>end:frontier.append(dict(site=f'{pc:08x}',reason='incomplete_instruction'));continue
        decoded[pc]=ins;nexts=[]
        if ins.group(capstone.CS_GRP_RET):pass
        elif pc in tables:
            operand,targets=tables[pc]
            if ins.mnemonic!='jmp' or ins.op_str!=operand:raise RuntimeError('Qualified table operand differs')
            nexts=[('primary_qualified_table_case',target) for target in targets]
        elif ins.group(capstone.CS_GRP_JUMP):
            if len(ins.operands)!=1 or ins.operands[0].type!=capstone.x86_const.X86_OP_IMM:
                frontier.append(dict(site=f'{pc:08x}',reason='unqualified_indirect_branch'))
            else:
                nexts=[('direct_branch',ins.operands[0].imm)]
                if ins.mnemonic!='jmp':nexts.append(('conditional_fallthrough',pc+ins.size))
        else:nexts=[('normal_call_return' if ins.group(capstone.CS_GRP_CALL) else 'fallthrough',pc+ins.size)]
        for kind,target in nexts:
            edges.append(dict(source=f'{pc:08x}',target=f'{target:08x}',kind=kind));todo.append(target)
    return dict(entry=f'{entry:08x}',code_end_exclusive=f'{end:08x}',instruction_sites=len(decoded),
        ret_sites=sorted(f'{a:08x}' for a,x in decoded.items() if x.group(capstone.CS_GRP_RET)),edges=edges,frontier=frontier,
        method='PRIMARY_ENTRY_ROOTED_LOCAL_CFG_NORMAL_CALL_RETURN_WITH_QUALIFIED_TABLES',
        helper_exception_or_runtime_reachability_claimed=False),decoded

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=116:raise RuntimeError('Expected116 before files')
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
    prior=(out/'retained-prior/cn-preborn-window-source-01/manifest.json').read_bytes()
    if sha(prior)!='21a9a013fc20b9c6ac44917371af44a7bc71110715df44d9f1767437374a659b' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned native input differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    table=view.read(0x4936a4-ib,32);targets=[int.from_bytes(table[n:n+4],'little') for n in range(0,32,4)]
    if targets!=[0x4934d9,0x4934e2,0x4934eb,0x4934f4,0x4934fd,0x493506,0x49350f,0x493518]:raise RuntimeError('Primary eight-cell table differs')
    save('native/tables/004936A4.bin',table)
    functions=[];instructions={};cfgs={}
    for address in ('0048CAA0','004AC850','004AF370','004D2D30','004D4E00','00492E70','00534640','00533300','004D58B0'):
        paths=list(RECOVERY.glob('part_*/'+address.lower()+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Individual native source not unique: '+address)
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('Native extent missing')
        va=int(address,16);size=int(match.group(1));code=view.read(va-ib,size)
        linear=list(md.disasm(code,va));instructions.update({x.address:x for x in linear})
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        save('native/functions/'+address+'.asm',('\n'.join(f'{x.address:08x} {x.bytes.hex()} {x.mnemonic} {x.op_str}' for x in linear)+'\n').encode())
        full=False
        if address in ('0048CAA0','004D4E00','00492E70'):
            tables={0x4934d2:('dword ptr [eax*4 + 0x4936a4]',targets)} if address=='00492E70' else {}
            cfg,decoded=local_cfg(md,code,va,tables)
            expected={'0048CAA0':['0048d921'],'004D4E00':['004d4eb9','004d4ec1'],'00492E70':['00492efb','004936a0']}[address]
            if cfg['frontier'] or cfg['ret_sites']!=expected:raise RuntimeError('Local normal CFG incomplete: '+address)
            cfgs[address]=cfg;instructions.update(decoded);dump('native/entry-cfg/'+address+'.json',cfg);full=True
        functions.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),
            complete_local_normal_call_return_cfg=full,whole_helper_exception_or_runtime_claimed=False))
    expected={
      0x48cace:('mov','esi, ecx'),0x48d421:('lea','ebx, [esi + 0x1478084]'),
      0x48d65d:('lea','eax, [ebp - 0x37c]'),0x48d663:('mov','dword ptr [ebp - 0x354], ebx'),
      0x48d669:('push','eax'),0x48d670:('call','0x4ac850'),
      0x4ac864:('mov','ebx, dword ptr [ebp + 8]'),0x4ac868:('mov','esi, ecx'),
      0x4ac8d3:('mov','eax, dword ptr [ebx + 0x28]'),0x4ac8d6:('mov','dword ptr [esi + 0x430ac], eax'),
      0x4acf05:('push','dword ptr [ebx + 0x28]'),0x4acf08:('mov','ecx, esi'),0x4acf0a:('call','0x4af370'),
      0x4af3eb:('mov','edi, dword ptr [ebp + 8]'),0x4af485:('lea','ebx, [edi + 0x90]'),
      0x4af493:('push','ebx'),0x4af494:('mov','ecx, esi'),0x4af496:('call','0x4d2d30'),
      0x4d2d40:('mov','eax, dword ptr [ebp + 8]'),0x4d2d47:('mov','ebx, ecx'),
      0x4d2d54:('mov','dword ptr [ebx + 0x430a8], eax'),
      0x4d4e06:('mov','cl, byte ptr [ebp + 8]'),0x4d4e0c:('js','0x4d4ebc'),
      0x4d4e1b:('movzx','edx, byte ptr [esi + 0xd4]'),0x4d4e24:('jge','0x4d4ebc'),
      0x4d4e2a:('mov','byte ptr [esi + 0xcf], cl'),0x4d4e36:('movsx','eax, byte ptr [ecx + 0xcf]'),
      0x4d4e3d:('imul','eax, eax, 0x3ec'),0x4d4e43:('add','eax, 0xd8'),0x4d4e48:('add','eax, ecx'),
      0x4d4e4a:('mov','dword ptr [ecx + 0xd0], eax'),
      0x4934cf:('and','eax, 7'),0x4934d2:('jmp','dword ptr [eax*4 + 0x4936a4]'),
      0x493540:('mov','eax, dword ptr [edi + 0x8885f0]'),0x493546:('add','eax, 0x9d223c'),
      0x493555:('mov','dword ptr [esi + 0x4504], eax'),0x493566:('push','0x3ec0'),
      0x493572:('lea','eax, [esi + 0x168]'),0x493594:('mov','byte ptr [esi + 0x164], 0'),
      0x49359b:('mov','byte ptr [esi + 0x15f], 0xff'),0x4935a2:('mov','dword ptr [esi + 0x160], 0'),
      0x49367f:('lea','ecx, [esi + 0x168]'),0x493687:('mov','dword ptr [esi + 0x160], ecx'),
      0x48d48a:('mov','eax, dword ptr [esi + 0x8885f0]'),0x48d490:('add','eax, 0x9d223c'),
      0x48d49a:('mov','dword ptr [esi + 0x147c588], eax'),
      0x53466c:('mov','eax, dword ptr [esi + 0x430ac]'),0x53467a:('mov','edi, dword ptr [eax + 0x160]'),
      0x5346b0:('lea','edx, [edi + 0x258]'),0x5346c0:('movzx','eax, byte ptr [edi + 0x1f0]'),
      0x5346cb:('test','byte ptr [ecx + edi + 0x1f1], 1'),0x5346df:('cmp','word ptr [edi], 0x64'),
      0x5346e5:('cmp','byte ptr [edi + 0x5b], 0'),0x5346ff:('add','edx, 4'),
      0x5333ae:('imul','eax, eax, 0x6e04'),0x5333b4:('mov','ecx, dword ptr [ecx + 0x4474]'),
      0x5333bf:('imul','eax, eax, 0x6e'),0x5333c2:('add','ecx, -0x6a')}
    qualified=[]
    for site,pair in expected.items():
        x=instructions.get(site)
        if not x or (x.mnemonic,x.op_str)!=pair:raise RuntimeError(f'Primary operand differs at{site:08x}')
        qualified.append(dict(site=f'{site:08x}',bytes=x.bytes.hex(),mnemonic=x.mnemonic,operand=x.op_str))
    dump('native/qualified-primary-operands.json',qualified)
    rejected=[]
    for va,size in [(0x48d5e0,0x95),(0x4934c0,30)]:
        code=view.read(va-ib,size);ins=list(md.disasm(code,va))
        save(f'native/unqualified-initial-views/{va:08X}.bin',code)
        save(f'native/unqualified-initial-views/{va:08X}.asm',('\n'.join(f'{x.address:08x} {x.mnemonic} {x.op_str}' for x in ins)+'\n').encode())
        rejected.append(dict(start=f'{va:08x}',bytes=size,qualified=False,reason='Arbitrary start cuts inside an entry-rooted instruction; excluded from all claims.'))
    save('native/unqualified-initial-views/004936A8-incorrect-table-start.bin',view.read(0x4936a8-ib,32))
    rejected.append(dict(start='004936A8',bytes=32,qualified=False,reason='Wrong table base; actual primary jump at4934D2 uses4936A4, corrected table retained separately.'))
    dump('native/unqualified-initial-views/rejection-receipt.json',rejected)
    for rel in ('cn-preborn-window-source-01/native/window-lifecycle-relations.json',
                'cn-preborn-window-source-01/native/search/native84-caller-frontier.json',
                'cn-preborn-window-source-01/native/entry-cfg/004AF370.json'):
        save('retained-inputs/'+rel,(base/rel).read_bytes())
    for rel in ('src/db/NativeSkillCatalog.h','src/db/NativeSkillCatalog.cpp','CMakeLists.txt'):
        save('retained-inputs/'+rel,(ROOT/rel).read_bytes())
    relations=dict(version='cn',native_sha256=SHA,context='Mode0 initialization selected inline-role source only',
        object_origin='same world+1478084 ->array index10 ->UI+430AC',actual_array_frame_base='EBP-37C',actual_index10_frame_cell='EBP-354',
        inline_role_origin='same index10 object+90 ->004D2D30 ->UI+430A8',
        same_object_field_aliases={'role+D0':'object+160','role+D4':'object+164','role+CF':'object+15F','role+D8':'object+168','role+4474':'object+4504'},
        selected_pointer_source='004D4E00 signed index >=0 AND index <actual BYTE count ->role+D8+index*3EC',
        captured_layout=dict(stride_hex='3EC',list_bytes_cleared_hex='3EC0',captured_slots=16,skill_count_member='1F0',
            skill_flags_start='1F1',skill_pointer_start='258',pointer_words_fit_before='3E8',server_skill_cap_recovered=False),
        skill_bank_source='same actual world+8885F0 +9D223C ->object+4504 ->role+4474',
        A2_native_record_formula='bank +kind*6E04 -6A +id*6E',record_bytes=110,
        actual_CN_skill_loader_resource_catalog_identity_qualified=False,TW_dataset_promoted_to_CN=False,
        source=dict(reader='CnPrebornSubjectState',actual_source_current_before_and_after=True,owned_selection_reference_copy=True,
            no_process_memory_access=True,no_pointer_dereference=True,no_default_selected_slot=True,
            window_requires_same_actual_source_revision=True,actual_subject_passed_to_common_operation=True,
            native_pointer_WORD_index_not_common_ID=True,post_commit_retained_identity_not_old_current=True,
            actual_common_mapping_rule_save_replay_owner_configured=False,formal_application_hosted=False,complete_route=False))
    dump('native/selected-subject-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:130 concrete window lifecycle sealed',native_sha256=SHA,
        native_functions=functions,native_primary_metadata_envelope_bytes=sum(q['metadata_envelope_bytes'] for q in functions),
        native_local_normal_entry_cfgs_qualified=len(cfgs),native_primary_operands_qualified=len(qualified),
        native_role_decode_table_cells_qualified=8,unqualified_initial_views_retained_and_excluded=len(rejected),
        cn_preborn_actual_selected_subject_readers_added=1,cn_preborn_existing_subject_operation_handoffs_strengthened=1,
        native_mode0_inline_role_selected_pointer_lineage_qualified=True,native_skill_bank_pointer_lineage_qualified=True,
        actual_CN_skill_loader_catalog_identity_qualified=False,actual_common_subject_mapping_configured=False,
        actual_preborn_initial_issuer_configured=False,actual_common_rule_save_replay_owner_configured=False,
        formal_application_hosted=False,new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,
        new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        unknown_values_invented=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        levels_changed=False,fonts_changed=False,build_run=False,tests_run=False,runtime_run=False,Cplusplus_source_run=False,
        Windows_API_run=False,native_execution=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    path=base/'packet-route-ledger.json';ledger=json.loads(path.read_text(encoding='utf-8'))
    ledger['cn_preborn_selected_subject_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='CN actual inline-role selected subject/skill references ->existing preborn common-operation handoff',
        version_scope='pinned-cn-mode0-initialized-selected-subject-source-only',
        status='Actual selected source reader/required window subject/common-operation handoff; common mapping/skill catalog/rule/save/replay/Application unconfigured',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual CN skill loader/resource/catalog and shared subject/skill identity ->rule/save/replay/initial issuer/Application; native84 caller/full timing; all TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator. PHASE1.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN actual selected preborn subject ('+ROUND+')\n\n'
            'Pinned mode0 actual array index10/object+90/004D2D30 qualifies UI430AC object and430A8 inline role, thus same selected160/D0 and bank4504/4474. '
            'Added supplied-byte CnPrebornSubjectState reader and required same-source revision/selected snapshot in existing window lifecycle; '
            'actual common apply receives retained native subject/skill references, not pointer-as-DB-ID or guessed eligibility. '
            'Post-commit checks actual new revision and retained identity, never obsolete native Current. '
            'Primary metadata11821B/local normal CFGs3; misaligned initial instruction/table views retained as unqualified, actual4936A4 table recovered from root instruction. '
            'Actual CN skill loader/catalog/common mapping/rules/save/persistent replay/initial issuer/Application and all TW/CN/PC/web/WSS/gameplay/numeric64/stack99 remain open. '
            'New opcode/phase/partial-owner/full routes0, whole totals/percent null. '
            'No build/test/native/C++/API/DB/deploy; see research/cn-preborn-selected-subject-source-20261008.md; full goal active.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','native_primary_metadata_envelope_bytes','native_local_normal_entry_cfgs_qualified',
        'cn_preborn_actual_selected_subject_readers_added','new_native_phase_source_bindings','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
