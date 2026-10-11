"""Primary world/frame return-state lineage and bounded table CFG, file-only.

No native, C++, UI, API, RNG, source controller, database or test execution.
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

NAME='cn-world-return-state-frontier-01'
ROUND='20261008-cn-world-return-state-frontier'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=('src/cn/protocol/CnPostWorldExitControl.h',
 'docs/research/cn-world-return-state-frontier-20261008.md',
 'tools/reconstruction/cn_world_return_state_frontier_delivery.py',
 'tools/reconstruction/cn_world_return_state_frontier_delivery_recovery.py',
 'tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
 'Actual004AE370 command producers, state6 source, negative selector reasons and complete indirect/deferred/state/caller denominator remain open.',
 'Native03 two opaque bytes, actual reply/save/replay/operation/rule source and Application are unconfigured; readonly client state is not server permission.',
 'Local primary bounded CFG follows syntactic branches/normal call return only; no whole call graph, exception or runtime reachability proof.',
 'Whole TW/CN/PC/web/WSS/common-world/gameplay/numeric64/stack99 scope and later comprehensive tests/repairs/release remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def bounded_cfg(md,code,entry,table_site,targets):
    end=entry+len(code);pending=deque([entry]);decoded={};edges=[];frontier=[]
    while pending:
        pc=pending.popleft()
        if pc in decoded:continue
        if not entry<=pc<end:frontier.append(dict(site=f'{pc:08x}',reason='outside_metadata_envelope'));continue
        ins=next(md.disasm(code[pc-entry:pc-entry+15],pc,count=1),None)
        if not ins or pc+ins.size>end:frontier.append(dict(site=f'{pc:08x}',reason='decode_crosses_envelope'));continue
        decoded[pc]=ins;successors=[]
        if ins.group(capstone.CS_GRP_RET):pass
        elif pc==table_site:
            if ins.op_str!='dword ptr [eax*4 + 0x48e080]':raise RuntimeError('Qualified indirect table operand differs')
            successors=[('qualified_primary_table_case',target) for target in targets]
        elif ins.group(capstone.CS_GRP_JUMP):
            if len(ins.operands)!=1 or ins.operands[0].type!=capstone.x86_const.X86_OP_IMM:
                frontier.append(dict(site=f'{pc:08x}',reason='unqualified_indirect_branch'))
            else:
                successors=[('direct_branch',ins.operands[0].imm)]
                if ins.mnemonic!='jmp':successors.append(('conditional_fallthrough',pc+ins.size))
        else:successors=[('normal_call_return' if ins.group(capstone.CS_GRP_CALL) else 'fallthrough',pc+ins.size)]
        for kind,target in successors:
            edges.append(dict(source=f'{pc:08x}',target=f'{target:08x}',kind=kind));pending.append(target)
    return dict(entry=f'{entry:08x}',metadata_end_exclusive=f'{end:08x}',
        method='ENTRY_ROOTED_PRIMARY_TABLE_CFG_NORMAL_CALL_RETURNS_ONLY',
        instruction_sites=len(decoded),unique_instruction_bytes=sum(i.size for i in decoded.values()),
        ret_sites=[f'{pc:08x}' for pc,i in sorted(decoded.items()) if i.group(capstone.CS_GRP_RET)],
        edges=edges,frontier=frontier,call_side_effects_or_exception_paths_recovered=False,
        all_runtime_states_reachable_claimed=False),decoded

def main(*,resume=None):
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists():
            expected=resume.get(rel) if resume else None
            if expected and sha(p.read_bytes())==expected and sha(data)==expected:return
            raise RuntimeError('Preserve existing static output: '+rel)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=98:raise RuntimeError('Expected retained98-file before snapshot')
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
    prior=(out/'retained-prior/cn-post-world-exit-source-01/manifest.json').read_bytes()
    if sha(prior)!='767a3f0cd09187270814d6782102e3e88e6122eb11cb0192de1555a8803d3a70' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned native input differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    functions=[];instructions={};codes={}
    for address in ('0048DA20','0048A4D0','0048AA10','004AE2B0','00480C50','00749104','0044A470','0048FCC0'):
        paths=list(RECOVERY.glob('part_*/'+address.lower()+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Native metadata not unique')
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('Missing extent')
        size=int(match.group(1));va=int(address,16);code=view.read(va-ib,size);codes[va]=code
        ins=list(md.disasm(code,va));instructions.update({i.address:i for i in ins})
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        save('native/functions/'+address+'.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins)+'\n').encode())
        functions.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),whole_cfg_claimed=False))
    world_table=view.read(0x48e080-ib,32);save('native/tables/0048E080.bin',world_table)
    world_targets=[int.from_bytes(world_table[i:i+4],'little') for i in range(0,32,4)]
    if world_targets!=[0x48dfa4,0x48dff4,0x48dfcc,0x48dab2,0x48dac8,0x48e01c,0x48e061,0x48e039]:raise RuntimeError('World table differs')
    cmd_table=view.read(0x48bd54-ib,20);cmd_select=view.read(0x48bd68-ib,25)
    save('native/tables/0048BD54.bin',cmd_table);save('native/tables/0048BD68.bin',cmd_select)
    cmd_targets=[int.from_bytes(cmd_table[i:i+4],'little') for i in range(0,20,4)]
    if cmd_targets!=[0x48ab16,0x48ab27,0x48b198,0x48ab08,0x48ab38] or list(cmd_select)!=[0]+[4]*10+[1]+[4]*5+[2]+[4]*6+[3]:
        raise RuntimeError('Frame primary tables differ')
    world03cell=view.read(0x4929e4-ib,4)
    if int.from_bytes(world03cell,'little')!=0x492936:raise RuntimeError('Prior qualified world03 cell differs')
    world03code=view.read(0x492936-ib,24)
    save('native/tables/004929E4-world03.bin',world03cell);save('native/ranges/00492936-world03-terminal-complete.bin',world03code)
    ins=list(md.disasm(world03code,0x492936));instructions.update({i.address:i for i in ins})
    save('native/ranges/00492936-world03-terminal-complete.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins)+'\n').encode())
    expected={0x48da80:('mov','dword ptr [ebx + 0x89b178], 3'),0x48daa0:('mov','eax, dword ptr [ebx + 0x89b178]'),
      0x48daa6:('cmp','eax, 7'),0x48daa9:('ja','0x48daa0'),0x48daab:('jmp','dword ptr [eax*4 + 0x48e080]'),
      0x48dabb:('call','0x48a4d0'),0x48dac0:('mov','dword ptr [ebx + 0x89b178], eax'),
      0x48dfb8:('mov','eax, 1'),0x48e008:('mov','eax, 2'),0x48dfe0:('mov','eax, 6'),
      0x48e025:('mov','eax, 4'),0x48e06b:('mov','eax, 5'),0x48e04d:('mov','eax, 3'),
      0x44a727:('mov','ebx, eax'),0x48a782:('call','0x48aa10'),0x48a787:('cmp','eax, 3'),
      0x48a78a:('jne','0x48a9e4'),0x48a797:('je','0x48a9e2'),0x48a9e2:('xor','eax, eax'),
      0x48aae1:('call','0x4ae370'),0x48aaf2:('add','eax, 0x1a'),0x48aaf5:('cmp','eax, 0x18'),
      0x48aaf8:('ja','0x48ab38'),0x48aafa:('movzx','eax, byte ptr [eax + 0x48bd68]'),
      0x48ab01:('jmp','dword ptr [eax*4 + 0x48bd54]'),0x48ab1d:('mov','eax, 2'),
      0x48ab2e:('mov','eax, 5'),0x48ab0f:('xor','eax, eax'),0x48b19f:('mov','eax, 1'),
      0x492938:('mov','eax, 8'),0x49294b:('ret','4'),0x48b180:('call','0x48fcc0'),
      0x48b185:('sub','eax, 4'),0x48b18a:('sub','eax, 3'),0x48b18f:('sub','eax, 1'),
      0x48b192:('jne','0x48b22c'),0x48b1a4:('jmp','0x48bd34'),0x48bd4e:('ret','8')}
    qualified=[]
    for site,pair in expected.items():
        actual=instructions.get(site)
        if not actual or (actual.mnemonic,actual.op_str)!=pair:raise RuntimeError(f'Primary operand differs at{site:08x}')
        qualified.append(dict(site=f'{site:08x}',primary_bytes=actual.bytes.hex(),mnemonic=actual.mnemonic,operand=actual.op_str))
    # Cookie's qualified normal branch touches only ECX/flags; failure is a separate jump.
    cookie=list(md.disasm(codes[0x749104],0x749104))
    if [(i.address,i.mnemonic,i.op_str) for i in cookie]!=[(0x749104,'cmp','ecx, dword ptr [0x8a6194]'),
        (0x74910a,'bnd jne','0x74910f'),(0x74910d,'bnd ret',''),(0x74910f,'bnd jmp','0x748e1d')]:raise RuntimeError('Normal cookie branch differs')
    dump('native/qualified-primary-operands.json',qualified)
    cfg,decoded=bounded_cfg(md,codes[0x48da20],0x48da20,0x48daab,world_targets)
    dump('native/world-loop-entry-table-cfg.json',cfg)
    save('native/world-loop-entry-table-cfg.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for pc,i in sorted(decoded.items()))+'\n').encode())
    prior_cfg_raw=(base/'cn-world-monster-lifecycle-01/native/0048da20-cfg.json').read_bytes();prior_cfg=json.loads(prior_cfg_raw)
    save('retained-inputs/prior-world-loop-entry-cfg.json',prior_cfg_raw)
    for rel in ('cn-world-close-drain-01/findings.json','cn-world-close-drain-01/native03-primary-branches.json',
                'cn-post-world-exit-source-01/native/producer-consumer-relations.json'):
        save('retained-inputs/'+rel,(base/rel).read_bytes())
    returns=[(0,1,1,True),(1,2,1,True),(2,6,2,True),(5,4,None,False),(6,5,0,False),(7,3,0,True)]
    rows=[dict(raw_loop_state=state,primary_target=f'{world_targets[state]:08x}',normal_main_eax=ret,
        close_control_at_main_switch=control,calls_00480c50=cleanup,server_reason_qualified=False) for state,ret,control,cleanup in returns]
    selectors=[dict(raw_signed_selector=i-26,selector_cell=f'{0x48bd68+i:08x}',selector_value=int(value),
        primary_target=f'{cmd_targets[value]:08x}',normal_frame_return={0:2,1:5,2:1,3:0}.get(value),
        semantic_command_name=None) for i,value in enumerate(cmd_select)]
    relation=dict(version='cn',phase='world-connection-1',c2s_opcode='02',s2c_opcode='03',
        world_loop='0048DA20',state_member='world+89B178',world_table='0048E080',terminal_rows=rows,
        nonterminal_states=[3,4],unsigned_out_of_range_behavior='same native load loop, not terminal default',
        frame='0048A4D0 ->0048AA10',frame_selector_supplier='004AE370',frame_selectors=selectors,
        frame_default_selector_values_in_range=21,frame_return3_stays_loop_only_if_global00886060_nonzero=True,
        cookie_normal_path_preserves_eax=True,cookie_failure_path_normal_return_claimed=False,
        world03_trigger=dict(cell='004929E4',target='00492936',normal_receiver_return=8,
            frame_branch='0048B185..0048B1A4',normal_frame_return=1,raw_loop_state=1,normal_main_eax=2,
            post_main_branch='0044A79D ->0044A7A7 ->0044A8C8',post_main_control=1,
            direction_order=['S2C03','native-frame','native-loop','native-main','C2S0201'],
            s2c03_is_default_reply_to_c2s0201_proven=False),
        complete_reason_repertoire=False,source_gameplay_handler_connected=False,
        actual_reply_rule_save_owner_configured=False,formal_application_hosted=False,complete_route=False,
        request_reply_pairing=None)
    dump('native/return-state-and-close-relations.json',relation)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress: implemented/sealed post-world exit source/catalog125',
        native_sha256=SHA,native_functions=functions,native_primary_metadata_envelope_bytes=sum(f['metadata_envelope_bytes'] for f in functions),
        native_primary_table_bytes=81,native_world03_terminal_range_bytes=24,
        static_capture_recovery_receipt='recovery/attempt-01-receipt.json',
        rejected_truncated_world03_range_preserved=True,
        native_world_loop_state_cells=8,native_terminal_return_state_projections=6,
        native_frame_negative_selector_branches=4,native_frame_default_selector_cells=21,
        cn_existing_post_world_readonly_return_projections_added=1,native_world03_followup_close_relations_added=1,
        prior_world_loop_entry_cfg_instruction_sites=prior_cfg['decoded_cfg_instructions'],
        expanded_world_loop_entry_cfg_instruction_sites=cfg['instruction_sites'],
        bounded_world_loop_cfg_frontier=cfg['frontier'],native_server_exit_reasons_recovered=False,
        actual_reply_rule_save_owner_configured=False,formal_application_hosted=False,new_packet_values=0,
        new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        unknown_values_invented=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        levels_changed=False,build_run=False,tests_run=False,runtime_run=False,Cplusplus_source_run=False,Windows_API_run=False,
        native_execution=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_world_return_state_frontier']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='CN world loop state ->actual EAX ->main close; frame selectors/world03 conditional followup',
        version_scope='pinned-cn-primary-world-return-context-and-readonly-projection-only',
        status='Primary terminal/table/cookie/context relations and readonly projection; actual server exit/save/native03 issuer absent',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual004AE370 command producers/return reasons and state6 source; actual native03/save/replay authority; all common account/world/gameplay/TW/CN/PC/web/WSS/numeric64/stack99/full denominator. PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN world return state frontier ('+ROUND+')\n\n'
            'Primary8-cell0048E080 world loop table qualifies6 terminal EAX values; preserved actual main0044A727 use despite void decompiler signatures. '
            'Frame25-selector/5-target tables qualify4 negative command selectors; their semantic producers remain open. '
            'Cookie normal path preserves EAX; independent world03 cell/24-byte return8/ret4 ->frame1 ->world1 ->main2 ->0201 relation, not default reply policy. '
            'Readonly projection1, expanded local entry/table CFG; opcode/phase/owner/full routes0, whole totals/percent null. '
            'Actual native03/server rules/saves/replay/Application and full TW/CN/PC/web/gameplay/numeric/stack scope remain open. '
            'No build/test/native/C++/API/DB/deploy. See research/cn-world-return-state-frontier-20261008.md; full goal active.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','native_primary_metadata_envelope_bytes','native_terminal_return_state_projections',
        'expanded_world_loop_entry_cfg_instruction_sites','native_world03_followup_close_relations_added','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
