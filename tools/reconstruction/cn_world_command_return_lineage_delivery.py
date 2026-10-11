"""Primary UI command gates and caller/return lineage, file-source only."""
import difflib
import hashlib
import json
import re
from pathlib import Path
import capstone
import pefile
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT
from .cn_world_return_state_frontier_delivery import bounded_cfg

NAME='cn-world-command-return-lineage-01'
ROUND='20261008-cn-world-command-return-lineage'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=('src/cn/protocol/CnPostWorldExitControl.h',
 'docs/research/cn-world-command-return-lineage-20261008.md',
 'tools/reconstruction/cn_world_command_return_lineage_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
 'Actual UI resource/WORD binding names, early signed-WORD command returns, tail/UI helper side effects and state6 sources remain open.',
 'Recovered UI masks/flags/AL/command projections are internal native relations, never server permission, save completion or full reason repertoire.',
 'Actual native03 opaque payload/rule/save/replay/operation issuer and Application remain unconfigured.',
 'Whole TW/CN/PC/web/WSS/common-world/gameplay/numeric64/stack99/state/variant denominator and later comprehensive tests/repairs/release remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=101:raise RuntimeError('Expected retained101-file before snapshot')
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
    prior=(out/'retained-prior/cn-world-return-state-frontier-01/manifest.json').read_bytes()
    if sha(prior)!='5382572c5ebf1e86eef2c288c8624d929596b19748922fa0ec8d1b96223d936d' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned native input differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    functions=[];instructions={};codes={}
    for address in ('004AE370','00527840','005280B0','004AC4F0','00527EE0','00527810','00527730',
                    '004A9B30','004AC020','0048AA10','0048DA20','0044A470','00749104'):
        paths=list(RECOVERY.glob('part_*/'+address.lower()+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Native metadata not unique: '+address)
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('Missing extent')
        size=int(match.group(1));va=int(address,16);code=view.read(va-ib,size);codes[va]=code
        ins=list(md.disasm(code,va));instructions.update({i.address:i for i in ins})
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        save('native/functions/'+address+'.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins)+'\n').encode())
        functions.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),whole_cfg_claimed=False))
    expected={0x4ae5a1:('cmp','dword ptr [esi + 0x1c8654], 0'),0x4ae5a8:('je','0x4ae65c'),
      0x4ae5ae:('cmp','di, word ptr [esi + 0x1c84d0]'),0x4ae5bf:('call','0x4ac4f0'),
      0x4ae5c4:('test','eax, eax'),0x4ae5cc:('mov','ebx, 0xffffffe6'),
      0x4aeb7f:('call','0x4ac4f0'),0x4aeb84:('jmp','0x4af1e5'),
      0x4ae62b:('call','0x5280b0'),0x4ae630:('cmp','al, 1'),0x4ae638:('cmp','al, 2'),
      0x4ae640:('mov','ebx, 0xfffffff7'),0x4aeb09:('call','0x5280b0'),
      0x4aeb21:('call','0x527840'),0x4aeb26:('cmp','al, 1'),0x4aeb2e:('mov','ebx, 0xfffffffe'),
      0x4af1ed:('call','0x50b110'),0x4af1f4:('call','0x50a320'),0x4af202:('call','0x496890'),
      0x4af209:('call','0x51a720'),0x4af20e:('cmp','dword ptr [esi + 0x8ac], 1'),
      0x4af215:('mov','eax, 0xfffffff1'),0x4af21b:('cmove','ebx, eax'),0x4af21f:('mov','eax, ebx'),
      0x52784a:('test','al, 2'),0x52784e:('test','al, 1'),0x527852:('movsx','eax, word ptr [ebp + 8]'),
      0x527856:('sub','eax, 2'),0x5278d4:('call','0x527730'),
      0x5278f5:('cmp','dword ptr [edi + 0x43088], 0'),0x5278fd:('sete','al'),0x527900:('inc','al'),
      0x5280c2:('xor','al, al'),0x5280df:('mov','dword ptr [edi + 0x43088], eax'),
      0x528102:('mov','dword ptr [edi + 0x43088], 1'),0x528142:('xor','al, al'),
      0x4ac4f6:('test','al, 2'),0x4ac516:('test','al, 0x20'),0x4ac51a:('cmp','word ptr [ebp + 8], 0'),
      0x4ac508:('call','0x44e7f0'),0x4ac50d:('mov','eax, 1'),0x4ac521:('xor','eax, eax'),
      0x4ac020:('jmp','0x4a9b30'),0x44a8cd:('cmp','ebx, 1'),0x44a8d0:('je','0x44a940'),0x44a8d2:('jmp','0x44a4c6')}
    qualified=[]
    for site,pair in expected.items():
        actual=instructions.get(site)
        if not actual or (actual.mnemonic,actual.op_str)!=pair:raise RuntimeError(f'Primary operand differs at{site:08x}')
        qualified.append(dict(site=f'{site:08x}',primary_bytes=actual.bytes.hex(),mnemonic=actual.mnemonic,operand=actual.op_str))
    dump('native/qualified-primary-operands.json',qualified)
    graphs={}
    for va in (0x4ae370,0x5280b0,0x527840,0x4ac4f0):
        cfg,decoded=bounded_cfg(md,codes[va],va,None,[]);graphs[va]=cfg
        dump(f'native/entry-cfg/{va:08x}.json',cfg)
    # Static domination over NORMAL RETURN edges: every native5280B0 ret
    # must pass one of two AL-clearing instructions. No native execution.
    cfg=graphs[0x5280b0];successors={}
    for edge in cfg['edges']:successors.setdefault(edge['source'],[]).append(edge['target'])
    pending=['005280b0'];seen=set();uncleared=[];clear={'005280c2','00528142'}
    while pending:
        pc=pending.pop()
        if pc in seen or pc in clear:continue
        seen.add(pc)
        if pc in cfg['ret_sites']:uncleared.append(pc)
        pending.extend(successors.get(pc,[]))
    if cfg['frontier'] or uncleared or cfg['ret_sites']!=['005280c6','00528146']:
        raise RuntimeError('Normal AL0 domination not qualified')
    al_zero=dict(callee='005280B0',observed_by_callers='low-byte AL only; upper EAX unspecified',
        qualified_normal_ret_sites=cfg['ret_sites'],mandatory_al_clear_sites=sorted(clear),
        syntactic_normal_ret_paths_without_AL_clear=uncleared,
        normal_AL_zero_qualified=True,exception_or_runtime_execution_claimed=False,
        nonzero_literal_candidates_excluded_at_callsite='004AE62B',excluded_literal_values=[1,2],
        all_other_callers_or_packet_values_removed=False)
    dump('native/normal-AL-zero-qualification.json',al_zero)
    for rel in ('cn-world-return-state-frontier-01/native/return-state-and-close-relations.json',
                'cn-post-world-exit-source-01/native/producer-consumer-relations.json'):
        save('retained-inputs/'+rel,(base/rel).read_bytes())
    relation=dict(version='cn',phase='world-connection-1',direction='C2S',opcode='02',producer='004AE370',
        actual_owner='0048AA10 ECX=world+89B26C',event_identity='signed WORD matched to same owner binding fields; no inferred names',
        close_helper=dict(callee='004AC4F0',true_condition='flags&02 !=0 OR (flags&20 !=0 AND signed item==0)',
            relevant_context='owner+1C8654 !=0 AND eventID==owner+1C84D0 AND actual helper EAX!=0',
            command=-26,zero_gate_same_helper_command_assignment=False),
        confirm=dict(callee='00527840',nonzero_condition='flags&02 ==0 AND flags&01 !=0 AND signed item==2',
            result_operand='actual owner+43088 AFTER native UI/cleanup/optional audio callbacks',
            post_mode_nonzero=dict(AL=1,command=-2,world_state=0,main_eax=1,control=1),
            post_mode_zero=dict(AL=2,command=-9,world_state=1,main_eax=2,control=1),
            control1_does_not_distinguish_these_native_lifecycle_reasons=True),
        selector_prep=dict(callee='005280B0',item2_sets_43088=1,item3_sets_43088=0,normal_AL_return=0,
            direct_exit_AL1_or_AL2_at_this_callee_proven=False),
        tail=dict(callees=['0050B110','0050A320','00496890','0051A720'],
            actual_post_callbacks_member='owner+8AC',override_value_equals=1,override_command=-15,
            applies_to_early_direct_signed_WORD_returns=False),
        command_to_world_state={'-26':2,'-15':5,'-9':1,'-2':0},
        semantic_UI_labels_recovered=False,native_server_exit_reasons_recovered=False,
        actual_reply_rule_save_owner_configured=False,source_gameplay_handler_connected=False,
        formal_application_hosted=False,complete_route=False,variants_complete=False,request_reply_pairing=None)
    dump('native/command-return-and-close-relations.json',relation)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress: world state/frame/03 followup relation/header/catalog126 sealed',
        native_sha256=SHA,native_functions=functions,native_primary_metadata_envelope_bytes=sum(f['metadata_envelope_bytes'] for f in functions),
        cn_existing_post_world_command_return_projections_added=1,cn_post_callback_tail_override_projections_added=1,
        native_ui_caller_callee_gate_relations_added=3,native_low_byte_zero_normal_return_callees_qualified=1,
        native_syntactic_literal_candidates_excluded_at_one_callsite=2,entry_cfg_instruction_sites={f'{va:08x}':c['instruction_sites'] for va,c in graphs.items()},
        native_internal_UI_labels_recovered=False,native_server_exit_reasons_recovered=False,
        actual_reply_rule_save_owner_configured=False,formal_application_hosted=False,new_packet_values=0,
        new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        unknown_values_invented=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        levels_changed=False,build_run=False,tests_run=False,runtime_run=False,Cplusplus_source_run=False,Windows_API_run=False,
        native_execution=False,database_access=False,deployed=False,protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_world_command_return_lineage']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='CN actual UI command gates/AL ->tail override ->world/main close readonly lineage',
        version_scope='pinned-cn-original-UI-caller-callee-normal-return-only',
        status='Command/tail readonly projections and primary gates; real UI bindings/server03/exit/save authority/hosting remain open',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual UI resource binding1C84AE/1C8544 and post-tail8AC producer/lifetime; early signed-WORD returns/state6 sources; real native03/save/replay authority; all TW/CN/PC/web/gameplay/numeric64/stack99/full denominator. PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN world command return lineage ('+ROUND+')\n\n'
            'Qualified actual004AE370 gates/00527840 post-callback mode AL1/2 and final8AC override after four tail callbacks. '
            '005280B0 normal returns have mandatory AL clears: exclude two literal caller candidates at004AE62B, not two global packets. '
            'Same0201 carries native main1 and main2 paths; cannot invent server exit reason from control alone. '
            'Readonly command projection1/tail projection1/gate relations3; opcode/phase/owner/full routes0, whole totals/percent null. '
            'Actual UI labels/early returns/state6/native03/rule/save/replay/Application and full TW/CN/PC/web/gameplay/numeric/stack remain open. '
            'No build/test/native/C++/API/DB/deploy. See research/cn-world-command-return-lineage-20261008.md; full goal active.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','native_primary_metadata_envelope_bytes','cn_existing_post_world_command_return_projections_added',
        'native_syntactic_literal_candidates_excluded_at_one_callsite','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
