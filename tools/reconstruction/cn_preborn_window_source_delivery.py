"""Static pinned native UI initialization and concrete issued-window source delivery.

Only file/PE/CFG/source accounting; never runs clients, C++, services or tests.
"""
import difflib
import hashlib
import json
import re
import subprocess
from pathlib import Path
import capstone
import pefile
from .cn_pe_import_directory import FileView
from .cn_preborn_choice_source_delivery import primary_cfg
from .cn_wrapper_route_frontier import ROOT

NAME='cn-preborn-window-source-01'
ROUND='20261008-cn-preborn-window-source'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe')
RECOVERY=Path('C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled')
SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
SOURCES=('src/cn/world/SharedPrebornChoices.h','src/cn/world/SharedPrebornChoices.cpp',
 'src/cn/world/SharedPrebornWindowSource.h','src/cn/world/SharedPrebornWindowSource.cpp',
 'src/cn/world/SharedWorldGameplay.h','src/cn/world/SharedWorldGameplay.cpp',
 'docs/research/cn-preborn-window-source-20261008.md','tools/reconstruction/cn_preborn_window_source_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py')
REMAINING=[
 'Actual native initial issuer/timing/selected subject/resource capacity and common skills/rules/transaction/save/persistent replay/Application are unconfigured.',
 'Native84 caller and phase, whole native preborn timing relative1C/pre-world and full subject pointer/common-ID lineage remain open; no84->A0 pairing inferred.',
 'Concrete prepared/issued/consumed lifecycle requires real source callbacks and does not complete all native output variants or persisted cross-connection replay.',
 'Full TW/CN/PC/web/WSS/common login/world/all gameplay/numeric64/stack99/state/variant denominator and later comprehensive test/repair/release remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=112:raise RuntimeError('Expected112 before files')
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
    prior=(out/'retained-prior/cn-preborn-choice-source-01/manifest.json').read_bytes()
    if sha(prior)!='b83e0075f5d6f83e9cd9e15fd86a7b0dadac44a74452f6ca3d4fc9a1b6226300' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    raw=CN.read_bytes()
    if sha(raw)!=SHA:raise RuntimeError('Pinned CN input differs')
    pe=pefile.PE(data=raw,fast_load=True);view=FileView(pe,raw);ib=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
    functions=[];instructions={};cfgs={}
    for address in ('004AC850','004AF370','00533DB0','004D58B0','004D5B20','005342B0','00534D10','00534640'):
        paths=list(RECOVERY.glob('part_*/'+address.lower()+'_*.c'))
        if len(paths)!=1:raise RuntimeError('Individual native source not unique: '+address)
        source=paths[0].read_bytes();match=re.search(rb'Size: (\d+) bytes',source)
        if not match:raise RuntimeError('No metadata extent')
        va=int(address,16);size=int(match.group(1));code=view.read(va-ib,size)
        ins=list(md.disasm(code,va));instructions.update({i.address:i for i in ins})
        save('native/functions/'+address+'.c',source);save('native/functions/'+address+'.bin',code)
        save('native/functions/'+address+'.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}' for i in ins)+'\n').encode())
        full_normal=False
        if address in ('004AF370','00533DB0','004D58B0'):
            cfg,decoded=primary_cfg(md,code,va,-1,[])
            expected={'004AF370':['004af689','004af6d2'],'00533DB0':['005342ac'],'004D58B0':['004d5a0d']}[address]
            if cfg['frontier'] or cfg['ret_sites']!=expected:raise RuntimeError('Local normal CFG remains open: '+address)
            cfgs[address]=cfg;dump('native/entry-cfg/'+address+'.json',cfg);full_normal=True
        functions.append(dict(va=address,metadata_envelope_bytes=size,sha256=sha(code),
            complete_local_normal_call_return_cfg=full_normal,whole_exception_or_runtime_cfg_claimed=False))
    expected={
      0x4acf03:('push','0'),0x4acf05:('push','dword ptr [ebx + 0x28]'),0x4acf08:('mov','ecx, esi'),0x4acf0a:('call','0x4af370'),
      0x4af37f:('mov','dword ptr [ebp - 4], ecx'),0x4af382:('mov','byte ptr [ecx + 0x77858], al'),
      0x4af399:('mov','esi, dword ptr [ebp - 4]'),0x4af3c2:('lea','edi, [esi + 0x1c8490]'),
      0x4af3df:('mov','eax, 0xffffffff'),0x4af3e4:('mov','ecx, 0x40'),0x4af3e9:('rep stosd','dword ptr es:[edi], eax'),
      0x4af3f0:('mov','bl, byte ptr [esi + 0x77858]'),0x4af40c:('test','bl, bl'),0x4af40e:('jne','0x4af68c'),
      0x4af598:('mov','ecx, esi'),0x4af59a:('call','0x533db0'),
      0x533dd8:('mov','dword ptr [ebp - 0x12c], ecx'),0x533ec6:('mov','ebx, dword ptr [ebp - 0x12c]'),
      0x533eec:('call','0x451460'),0x533f04:('mov','word ptr [ebx + 0x1c8500], ax'),
      0x5341d0:('mov','esi, dword ptr [ebp - 0x12c]'),0x534295:('mov','dword ptr [esi + 0x8a4], 1'),
      0x4d58c1:('mov','eax, dword ptr [edi + 0x430a8]'),0x4d58c7:('lea','esi, [eax + 0xd8]'),
      0x4d58cd:('movzx','eax, byte ptr [eax + 0xd4]'),0x4d58d8:('movsx','cx, byte ptr [edx]'),
      0x4d58e0:('cmp','word ptr [esi], cx'),0x4d58e6:('add','esi, 0x3ec'),
      0x4d59be:('mov','dword ptr [eax + 0xd0], esi'),0x4d59ca:('mov','byte ptr [eax + 0xcf], bl'),
      0x4d5b43:('mov','al, byte ptr [edx + 0xd4]'),0x4d5b55:('imul','esi, eax, 0x3ec'),
      0x534d1c:('cmp','byte ptr [eax + 0xd4], 0'),0x534d23:('jbe','0x534d9e'),
      0x534647:('movzx','eax, word ptr [esi + 0x1c8500]'),0x534651:('js','0x5347d3'),
      0x53465e:('test','byte ptr [eax + esi + 0x78074], 0x10'),0x53466c:('mov','eax, dword ptr [esi + 0x430ac]'),
      0x53467a:('mov','edi, dword ptr [eax + 0x160]'),
      0x5342b4:('mov','eax, dword ptr [ecx + 0x430ac]'),0x5342ba:('mov','ecx, dword ptr [ecx + 0x4308c]'),
      0x5342c0:('push','2'),0x5342c2:('mov','ax, word ptr [eax]'),0x5342cd:('push','0x84'),0x5342d2:('call','0x481440')}
    qualified=[]
    for site,pair in expected.items():
        ins=instructions.get(site)
        if not ins or (ins.mnemonic,ins.op_str)!=pair:raise RuntimeError(f'Primary operand differs at{site:08x}')
        qualified.append(dict(site=f'{site:08x}',bytes=ins.bytes.hex(),mnemonic=ins.mnemonic,operand=ins.op_str))
    dump('native/qualified-primary-operands.json',qualified)
    #Literal/direct-name search is a scoped negative observation, not proof of
    #global unreachability. Raw E8 bytes have no entry/phase qualification.
    search=subprocess.run(['rg','-l','-g','00*.c','FUN_005342b0',str(RECOVERY)],capture_output=True)
    if search.returncode not in (0,1):raise RuntimeError('Bounded individual-source search failed')
    save('native/search/native84-direct-name-search.stdout',search.stdout)
    save('native/search/native84-direct-name-search.stderr',search.stderr)
    sections=[];literal=[];relative=[];target=0x5342b0
    for section in pe.sections:
        data=section.get_data();start=ib+section.VirtualAddress;name=section.Name.rstrip(b'\0').decode('ascii',errors='replace')
        if start<0x1000000:
            scope=data[:0x1000000-start];sections.append(dict(name=name,start_va=f'{start:08x}',file_backed_bytes=len(scope)))
            at=-1
            while True:
                at=scope.find(target.to_bytes(4,'little'),at+1)
                if at<0:break
                literal.append(dict(va=f'{start+at:08x}',section=name))
        if section.Characteristics & 0x20000000:
            at=-1
            while True:
                at=data.find(b'\xe8',at+1)
                if at<0:break
                if at+5<=len(data) and (start+at+5+int.from_bytes(data[at+1:at+5],'little',signed=True))&0xffffffff==target:
                    relative.append(dict(va=f'{start+at:08x}',section=name,bytes=data[at:at+5].hex(),entry_qualified=False))
    callers=dict(target='005342B0',individual_source_glob='part_*/00*.c',direct_name_matches=search.stdout.decode('utf-8',errors='replace').splitlines(),
        literal_search_file_backed_sections_below_va01000000=sections,literal_pointer_hits=literal,
        executable_section_raw_relative_E8_candidates=relative,native_caller_qualified=False,
        phase=None,global_unreachability_claimed=False,request_reply_pairing=None,
        remaining=['Relative tail branches/indirect/computed sources and root/phase/subject lineage remain unresolved.'])
    dump('native/search/native84-caller-frontier.json',callers)
    retained=('cn-preborn-choice-source-01/native/preborn-producer-consumer-relations.json',
              'cn-preborn-choice-source-01/source-placement-frontier.json',
              'cn-world-exit-ui-binding-source-01/native/exit-ui-binding-and-flag-relations.json')
    for rel in retained:save('retained-inputs/'+rel,(base/rel).read_bytes())
    cmake=(ROOT/'CMakeLists.txt').read_bytes();save('retained-inputs/CMakeLists.txt',cmake)
    relations=dict(version='cn',phase_scope='conditional ready-world after actual1C source only',
        native_initialization=dict(caller='004ACF0A',mode_argument=0,actual_ECX='same saved UI owner',
            mode_member='77858',constructor_call='004AF59A',constructor='00533DB0',
            nonzero_mode_branch='004AF40E ->004AF68C excludes this constructor in local normal CFG',
            reset_region=dict(member='1C8490',DWORD_count=64,value='FFFFFFFF',includes_preborn_WORD='1C8500'),
            handle_from_actual_return_AX=dict(site='00533F04',member='1C8500',producer='00451460'),
            initialized_flag=dict(site='00534295',member='8A4',value=1),
            all_preborn_activation_timing_relative1C_qualified=False),
        native_A0_prerequisites=dict(role_pointer_member='430A8',BYTE_list_count_member='D4',consumer_site='00534D1C',
            list_origin='004D58B0 role+D8',stride_hex='3EC',lookup_key='sign-extended payload BYTE compared with entry WORD0',
            selected_role_pointer_member='D0',selected_role_index_member='CF',
            GUI_handle='signed WORD1C8500 >=0 AND GUI slot flags&10',
            preborn_subject_pointer_member='430AC',resource_pointer_member='160',
            selected_role_and_preborn_subject_pointer_equivalence_qualified=False,server_permission_recovered=False),
        native84=dict(producer='005342B0',queue_call='005342D2',logical_bytes=3,body='raw native subject WORD0',
            native_caller_qualified=False,phase=None,common_identity_mapping_qualified=False,request_reply_pairing=None),
        source=dict(controller='SharedPrebornChoices',concrete_owner='SharedPrebornWindowSource',
            prepared_to_issued_before_window_bytes_release=True,actual_order_and_bytes_preserved=True,
            exactly_one_A0_and_exact_scope_counts=True,actual_issuer_checkpoints=['BeforeQueue','QueueAccepted','BeforeSelection'],
            bind_same_lease_and_window_owner=True,bind_sends_no_output=True,actual_event_calls_publish=True,
            scope_retired_before_actual_common_transaction=True,post_commit_uses_actual_revision=True,
            persisted_cross_connection_replay_required=True,new_partial_owner_chain=False,
            actual_issuer_rule_save_owner_configured=False,formal_application_hosted=False,complete_route=False))
    dump('native/window-lifecycle-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='no_progress: status reply only; this round resumed concrete source/native work',
        previous_sealed_work_round_classification='progress:129 preborn conditional source sealed',native_sha256=SHA,
        native_functions=functions,native_primary_metadata_envelope_bytes=sum(r['metadata_envelope_bytes'] for r in functions),
        native_local_normal_entry_cfgs_qualified=len(cfgs),native_primary_operands_qualified=len(qualified),
        cn_preborn_concrete_window_lifecycle_owners_added=1,cn_preborn_held_window_publication_entries_added=1,
        cn_preborn_existing_gameplay_source_bindings_added=1,native_UI_initialization_relations_added=1,
        native_A0_list_count_prerequisite_relations_added=1,native84_caller_qualified=False,
        native84_phase_source_binding_added=False,actual_preborn_initial_issuer_configured=False,
        actual_preborn_common_rule_save_owner_configured=False,formal_application_hosted=False,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        unknown_values_invented=False,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        levels_changed=False,fonts_changed=False,build_run=False,tests_run=False,runtime_run=False,Cplusplus_source_run=False,
        Windows_API_run=False,native_execution=False,database_access=False,deployed=False,
        protected_contexts=protected,CMake_recursive_source_glob_retained_sha256=sha(cmake),remaining=REMAINING)
    dump('findings.json',facts)
    path=base/'packet-route-ledger.json';ledger=json.loads(path.read_text(encoding='utf-8'))
    ledger['cn_preborn_window_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='CN actual issued preborn window publication ->same81/83 operation scope lifecycle',
        version_scope='pinned-cn-original-conditional-ready-world-preborn-source-only',
        status='Concrete prepared/issued/consumed window owner composed with existing81/83 source; actual native issuer/rule/save/replay/Application unconfigured',
        source_paths=list(SOURCES),native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next_source_frontier']='Actual preborn selected subject/resource/native initial issuer timing and common skills/rule/save/replay owner; native84 caller; formal shared login/world providers; entire TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator. PHASE1.'
    path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN actual preborn window lifecycle ('+ROUND+')\n\n'
            'Pinned primary initialization qualifies same saved UI owner/mode0 constructor/actual AX handle; A0 gate D4 is native list count, not server permission. '
            'Added concrete SharedPrebornWindowSource and held initial window publication: actual supplied records/revision/scope publish before bytes release, '
            'then existing81/83 retires local scope before real common transaction and uses actual post-commit output. '
            'Gameplay binds same lease/controller/source only, never emits at1C or invents native activation timing. '
            'Native84 producer saved but caller/phase unresolved, no84->A0 pairing. Local complete normal CFGs3, primary metadata4968B. '
            'Same existing chain lifecycle increment, new opcode/phase/partial-owner/full routes0, whole totals/percent null. '
            'Actual subject/resources/initial issuer/rules/skills/save/persistent replay/Application and full TW/CN/PC/web/WSS/gameplay/numeric64/stack99 scope remain open. '
            'No build/test/native/C++/API/DB/deploy; see research/cn-preborn-window-source-20261008.md; full goal active.\n')
    origins=[]
    for rel in sorted(set(SOURCES)|set(books)):
        data=(ROOT/rel).read_bytes();save('source/'+rel,data)
        origins.append(dict(path=rel,snapshot='source/'+rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ('round','native_primary_metadata_envelope_bytes',
        'native_local_normal_entry_cfgs_qualified','new_native_phase_source_bindings','new_source_owner_chains','new_complete_bidirectional_routes')}))

if __name__=='__main__':main()
