"""Retain primary post-game close switch and source-only terminal composition.

File-backed PE disassembly/source accounting only; no native/controller execution.
"""
import difflib
import hashlib
import json
import re
from pathlib import Path
import capstone
import pefile
from .cn_pe_import_directory import FileView
from .cn_wrapper_route_frontier import ROOT

NAME='cn-post-world-exit-source-01'
ROUND='20261008-cn-post-world-exit-source'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=('src/cn/protocol/CnPostWorldExitControl.h',
 'src/cn/world/SharedPostWorldExit.h','src/cn/world/SharedPostWorldExit.cpp',
 'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
 'docs/research/cn-post-world-exit-source-20261008.md',
 'tools/reconstruction/cn_post_world_exit_source_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
 'Upstream EAX/EBX return reasons and complete world/battle phase/state/variant paths remain unresolved; decompiler void type is not an EAX contract.',
 'Native03 two opaque payload bytes and actual rule/operation/save/replay quiescence issuer remain unknown/unconfigured; no generic ACK or pre-world fallback.',
 'Optional post-world source composition is not installed in actual Application; inherited send_batch gate is not a new held-publication/atomicity claim.',
 'Actual account/profile/billing rights/Plan/native07/22/appearance/scene/world/all authoritative gameplay providers remain open.',
 'Whole TW/CN/PC/web/WSS scope, common world/tables, numeric64/stack99/full denominator and later comprehensive tests/repairs/release remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=93:raise RuntimeError('Expected retained93-file before snapshot')
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
    prior=(out/'retained-prior/cn-billing-presentation-variants-source-01/manifest.json').read_bytes()
    if sha(prior)!='a2d91cec5adb78bc78ababa92572cd4603173ec3c09992e1cd8766a747341193' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned native input differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);native=[];instructions={}
    for address in ('0044A470','00449F50','00445040','0047D6C0','0047FA20','00480B10','00481440'):
        paths=list(RECOVERY.glob('part_*/'+address.lower()+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Native metadata not unique: '+address)
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('Missing extent: '+address)
        size=int(match.group(1));va=int(address,16);code=view.read(va-ib,size)
        ins=list(md.disasm(code,va));instructions.update({i.address:i for i in ins})
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        save('native/functions/'+address+'.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins)+'\n').encode())
        native.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),whole_cfg_claimed=False))
    table=view.read(0x44a960-ib,24);save('native/tables/0044A960.bin',table)
    targets=[int.from_bytes(table[i:i+4],'little') for i in range(0,24,4)]
    if targets!=[0x44a7a7,0x44a79d,0x44a8a7,0x44a7b9,0x44a8bc,0x44a7b0]:raise RuntimeError('Primary post-game table differs')
    # Qualify exact primary instruction operands/edges; never emulate EAX or callbacks.
    operands={0x44a71c:('call','0x48da20'),0x44a727:('mov','ebx, eax'),
        0x44a780:('mov','dword ptr [esi + 0x460], 0'),
        0x44a78a:('lea','eax, [ebx - 1]'),0x44a78d:('cmp','eax, 5'),
        0x44a790:('ja','0x44a8cd'),0x44a796:('jmp','dword ptr [eax*4 + 0x44a960]'),
        0x44a7a7:('push','1'),0x44a7a9:('push','1'),0x44a7ab:('jmp','0x44a8c0'),
        0x44a7b0:('push','1'),0x44a7b2:('push','2'),0x44a7b4:('jmp','0x44a8c0'),
        0x44a8a7:('mov','ecx, dword ptr [esi + 0x458]'),0x44a8ad:('push','1'),
        0x44a8af:('push','0'),0x44a8b1:('push','2'),0x44a8b3:('call','0x480b10'),
        0x44a8bc:('push','1'),0x44a8be:('push','0'),
        0x44a8c0:('mov','ecx, dword ptr [esi + 0x458]'),0x44a8c6:('push','2'),0x44a8c8:('call','0x480b10'),
        0x44a1b5:('call','0x47d6c0'),0x44a1d6:('mov','dword ptr [edi + 0x454], eax'),
        0x44a1dc:('call','0x47fa20'),0x44a280:('call','0x47d6c0'),
        0x44a29e:('mov','dword ptr [edi + 0x458], eax'),0x44a2a4:('call','0x47fa20'),
        0x4450b3:('mov','eax, dword ptr [ecx + 0x458]'),0x4450b9:('mov','dword ptr [esi + 0x16180], eax'),
        0x4450bf:('mov','eax, dword ptr [ecx + 0x454]'),0x4450c5:('mov','dword ptr [esi + 0x1617c], eax'),
        0x480b2c:('push','1'),0x480b32:('call','0x481440'),0x480b39:('call','0x47f430'),
        0x480b3e:('cmp','dword ptr [ebp + 0x10], 0'),0x480be7:('cmp','byte ptr [esi + 0x2cc4], 3')}
    qualifications=[]
    for site,(mnemonic,operand) in operands.items():
        actual=instructions.get(site)
        if not actual or (actual.mnemonic,actual.op_str)!=(mnemonic,operand):raise RuntimeError(f'Primary operand differs at{site:08x}')
        qualifications.append(dict(site=f'{site:08x}',primary_bytes=actual.bytes.hex(),mnemonic=mnemonic,operand=operand))
    dump('native/primary-instruction-relations.json',qualifications)
    values=[1,1,0,None,0,2];calls=[0x44a8c8,0x44a8c8,0x44a8b3,None,0x44a8c8,0x44a8c8]
    cases=[dict(raw_ebx=i+1,table_cell=f'{0x44a960+4*i:08x}',target=f'{target:08x}',
        control_byte=values[i],wait=1 if values[i] is not None else None,
        close_callsite=f'{calls[i]:08x}' if calls[i] else None,
        no_send_claim_scoped_to_this_switch_branch=True) for i,target in enumerate(targets)]
    old_root=base/'cn-close-producer-variants-01';old_facts=json.loads((old_root/'findings.json').read_text(encoding='utf-8'))
    old_contexts=json.loads((old_root/'native-close-producer-contexts.json').read_text(encoding='utf-8'))
    local=[c for c in old_contexts if c['site'].lower()=='0044a8c8']
    if len(local)!=1 or local[0]['payload_control_byte']!=0 or old_facts['retained_direct_call_contexts']!=25:
        raise RuntimeError('Historical nearest-push observation differs')
    for filename in ('findings.json','native-close-producer-contexts.json','manifest.json'):
        save('retained-inputs/cn-close-producer-variants-01/'+filename,(old_root/filename).read_bytes())
    save('retained-inputs/cn-world-close-drain-01/findings.json',(base/'cn-world-close-drain-01/findings.json').read_bytes())
    correction=dict(historical_direct_callsite_count=25,direct_callsites_added=0,
        historical_local_nearest_push_counts=old_facts['control_byte_callsite_counts'],
        historical_full_upstream_repertoire_proven=False,corrected_callsite='0044a8c8',
        locally_adjacent_control=0,qualified_upstream_controls=[0,1,2],newly_qualified_control_values=[1,2],
        correction_authority='primary0044A960 table +exact targets/pushes/jumps +shared0044A8C0 tail',
        original_records_and_seal_unchanged=True,old_default_read_only_forms_unchanged=True,
        direct_callsite_counts_are_not_variant_counts=True)
    dump('native/historical-close-repertoire-correction.json',correction)
    relation=dict(version='cn',direction='C2S',phase='world-connection-1',source_phase='world-entered',opcode='02',
        logical_size=2,producer='0044A470',phase_evidence='post0048DA20 ->destroy main+460 ->return-value switch; main+458 owner',
        raw_selector='EBX copied from actual EAX; EBX-1 unsigned<=5',upstream_reason_semantics_recovered=False,
        switch_table='0044A960',cases=cases,default_no_close_at_this_switch=True,
        controls=[0,1,2],owner='main+458 ->UI+16180; distinct main+454 ->UI+1617C',
        sender='00480B10 ->00481440(opcode,one-byte) ->0047F430',
        native_wait_consumer='00480B10 waits observed03; existing0048FCC0 world03 independently returns8',
        reply_opcode='03',reply_logical_size=3,reply_payload_semantics_recovered=False,
        source_ingress='SharedWorldGameplay ->SharedPostWorldExit ->same close_after_native_world_reply ->drain/OnClosed',
        actual_reply_rule_save_owner_configured=False,source_gameplay_handler_connected=False,
        variants_complete=False,formal_application_hosted=False,complete_route=False)
    dump('native/producer-consumer-relations.json',relation)
    facts=dict(round=ROUND,previous_goal_turn_classification='no_progress: read-only status response; resumed retained source increment',
        native_sha256=SHA,native_functions=native,native_primary_metadata_envelope_bytes=sum(n['metadata_envelope_bytes'] for n in native),
        native_switch_table_bytes=24,native_post_game_switch_cells=6,native_post_game_send_cases=5,
        native_post_game_control_values=[0,1,2],newly_qualified_control_values=[1,2],new_direct_callsites=0,
        native_post_game_context_relations_added=1,native_upstream_return_reason_semantics_recovered=False,
        cn_post_world_terminal_source_compositions_added=1,new_source_owner_chains=1,new_tw_source_owner_chains=0,
        new_native_phase_source_bindings=2,new_packet_values=0,new_complete_bidirectional_routes=0,
        actual_reply_rule_save_owner_configured=False,formal_application_hosted=False,
        terminal_completion_is_local_write_drain_only=True,whole_game_route_total=None,
        whole_game_completed_routes=None,whole_game_completion_percent=None,
        unknown_values_invented=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        levels_changed=False,build_run=False,tests_run=False,runtime_run=False,Cplusplus_source_run=False,
        Windows_API_run=False,native_execution=False,database_access=False,deployed=False,
        protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    p=base/'packet-route-ledger.json';ledger=json.loads(p.read_text(encoding='utf-8'))
    ledger['cn_post_world_exit_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='CN post-world02 control0/1/2 ->same ready lease ->actual03 supplier ->existing write/drain/cleanup',
        version_scope='pinned-cn-post-game-return-and-ready-source-lifecycle-only',
        status='Conditional terminal composition implemented; actual rule/save/native03 issuer and Application hosting remain missing',
        source_paths=list(SOURCES),native_c2s_by_phase={'world-entered':['02']},native_s2c_by_phase={'world-entered':['03']},
        source_owner_chains_added=1,tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Native0048DA20/004AE2B0 raw return-state producers and real exit/save/native03 authority; current common account/profile/world/gameplay/TW/CN/PC/web/WSS/numeric64/stack99/full denominator. PHASE1 only.'
    p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN post-world exit source ('+ROUND+')\n\n'
            'Primary six-cell0044A960 table and upstream pushes qualify controls0/1/2 at existing0044A8C8; preserve historical nearest-push counts and add explicit correction. '
            'Native main+458 game transport is distinct from main+454 account owner; this post-game transition does not close all return/state semantics. '
            'Added same ready lease/current saved position/once terminal designation/actual full03 supplier, integrated as last gameplay aggregate record. '
            'Existing write/drain/OnClosed cleanup; terminal callback does not reread obsolete ready source or pump more gameplay. '
            'Partial owner1/phase bindings2/new control observations2/direct sites0/opcodes0/full routes0; whole totals/percent null. '
            'Actual rule/save/replay/native03 issuer/Application and entire TW/CN/PC/web/gameplay/numeric/stack scope remain open. '
            'No build/test/C++/native/API/DB/deploy. See research/cn-post-world-exit-source-20261008.md; full goal active.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','native_primary_metadata_envelope_bytes','native_post_game_send_cases',
        'cn_post_world_terminal_source_compositions_added','new_native_phase_source_bindings','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
