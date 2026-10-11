"""Seal native6F/5E/73 private-incarnation source and common CN cleanup."""
import json
import re
import struct
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .archive_inputs import ArchivedInputs,SERVER
from .packet_connection_inventory import IMAGE,PIN as TW_PIN,BASE,LENGTH_TABLE,WORLD_TABLE
from .cn_wrapper_route_frontier import CN,PIN as CN_PIN
from .cn_shared_movement_owner_delivery import sha,dump

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='shared-actor-visibility-01'
ROUND='20261007-tw-cn-actor-visibility'
MODIFIED=['src/cn/world/SharedMovementPublication.h','src/cn/world/SharedMovementPublication.cpp',
    'src/cn/world/SharedMovement.h','src/cn/world/SharedMovement.cpp',
    'src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp']
ADDED=['src/cn/protocol/CnRemoteActor.h','src/cn/world/SharedActorVisibility.h','src/cn/world/SharedActorVisibility.cpp']
SOURCES=MODIFIED+ADDED+['src/cn/protocol/CnRemoteActorMove.h','src/protocol/RecoveredRemoteActor.h',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'docs/research/shared-actor-visibility-20261007.md']
FUNCTIONS=[('0048fcc0',8),('0052f170',16),('0052f5a0',16),('00532410',16),('0052fd40',16),
    ('0052ffc0',16),('005309f0',16),('00532800',16),('004fa750',13),('004f1450',12)]

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve sealed actor visibility delivery')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    cat=ROOT/'dual-client-route-catalog-20';manifest_raw=(cat/'source-file-manifest.json').read_bytes()
    if sha(manifest_raw)!=ledger['dual_client_endpoint_catalog']['artifact_sha256']['source-file-manifest.json']:
        raise ValueError('Prior catalog manifest changed')
    previous=json.loads(manifest_raw);pending=[];changes=[]
    for rel in MODIFIED:
        expected=previous[rel]['sha256'];found=None
        for key,evidence in ledger['cn_account_admission_evidence'].items():
            directory=SERVER/evidence['root'];p=directory/rel
            if not p.is_file():continue
            raw=p.read_bytes()
            if sha(raw)==expected:
                if evidence['artifact_sha256'].get(rel)!=expected:raise ValueError('Historical source receipt changed')
                found=(key,p,raw);break
        if not found:raise ValueError('Exact prior source not recoverable: '+rel)
        key,p,raw=found;pending.append(('prior-sources/'+rel,raw,p))
        changes.append({'path':rel,'previous_artifact':key,'before_sha256':expected,
            'after_sha256':sha((SERVER/rel).read_bytes()),'old_snapshot_preserved':True})
    previous_movement=ROOT/'shared-movement-publication-01/integration-manifest.json';old_raw=previous_movement.read_bytes()
    if sha(old_raw)!=ledger['cn_account_admission_evidence']['shared-movement-publication-01']['artifact_sha256']['integration-manifest.json']:
        raise ValueError('Previous movement manifest changed')
    old=json.loads(old_raw);old_native={r['address']:r for r in old['native_spans']}
    pending.extend([('prior-manifests/movement-publication.json',old_raw,previous_movement),
        ('prior-manifests/catalog20-source-files.json',manifest_raw,cat/'source-file-manifest.json')])
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=CN_PIN:raise ValueError('CN native pin changed')
    pe=pefile.PE(data=raw,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32)
    recovery=CN.parent/'God2_opt_source_recovery_20260926_055734/decompiled';native=[]
    for address,part in FUNCTIONS:
        p=recovery/f'part_{part:04d}'/(address+'_FUN_'+address+'.c');source=p.read_bytes()
        match=re.search(rb'Address: 0x([0-9a-fA-F]+).*Size: (\d+) bytes',source)
        if not match or int(match.group(1),16)!=int(address,16):raise ValueError('Native extent missing')
        size=int(match.group(2));code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        if len(code)!=size:raise ValueError('Native span incomplete')
        if address in old_native and (sha(code)!=old_native[address]['native_sha256'] or sha(source)!=old_native[address]['source_sha256']):
            raise ValueError('Prior CN span changed')
        ins=list(md.disasm(code,int(address,16)))
        asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode()
        for ext,data,origin in [('.c',source,p),('.bin',code,exe),('.asm',asm,'pinned CN disassembly')]:
            pending.append(('native/cn/functions/'+address+ext,data,origin))
        native.append({'version':'cn','address':address,'bytes':size,'native_sha256':sha(code),
            'source_sha256':sha(source),'source_original':str(p),'decoded_bytes':sum(i.size for i in ins)})
    phase_raw=(cat/'inputs/cn-s2c-phases.json').read_bytes();phases=json.loads(phase_raw)
    branches=[]
    for opcode,length in [(0x6f,81),(0x73,5)]:
        row=next(r for r in phases if r['phase']=='world-connection-1' and r['opcode']==opcode)
        if row['length']!=length or row['function']!='0x0048fcc0':raise ValueError('CN actor branch differs')
        path=cat/'native-cn-branches'/Path(row['branch_source']).name;branch=path.read_bytes()
        if branch!=(CN/row['branch_source']).read_bytes():raise ValueError('Historical CN branch changed')
        pending.append((f'native/cn/world-{opcode:02x}-branch.c.txt',branch,path));branches.append(row)
    pending.append(('native/cn/phase-index.json',phase_raw,cat/'inputs/cn-s2c-phases.json'))
    reader=ArchivedInputs()
    try:tw=reader.read(IMAGE)
    finally:reader.close()
    if sha(tw)!=TW_PIN:raise ValueError('TW mapped image pin changed')
    tw_spans=[]
    for opcode,length,expected_target in [(0x6f,81,0x695c8),(0x73,5,0x69a28)]:
        leaf=struct.unpack_from('<I',tw,LENGTH_TABLE+4*opcode)[0]-BASE
        target=struct.unpack_from('<I',tw,WORLD_TABLE+4*opcode)[0]-BASE
        if target!=expected_target or tw[leaf:leaf+6]!=b'\xb8'+struct.pack('<I',length)+b'\xc3':
            raise ValueError('TW native actor length/dispatch differs')
        code=tw[leaf:leaf+6];pending.append((f'native/tw/{opcode:02x}-length.bin',code,IMAGE))
        tw_spans.append({'name':f'{opcode:02x}-length','rva':f'{leaf:08x}','bytes':6,'sha256':sha(code)})
    for name,rva,size in [('73-world',0x69a28,0x38),('6f-constructor-prefix',0xfc1c0,0xfc2d3-0xfc1c0)]:
        code=tw[rva:rva+size];ins=list(md.disasm(code,BASE+rva))
        if sum(i.size for i in ins)!=size:raise ValueError('TW slice extent differs')
        pending.append(('native/tw/'+name+'.bin',code,IMAGE))
        pending.append(('native/tw/'+name+'.asm',('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}'
            for i in ins)+'\n').encode(),'pinned TW mapped image disassembly'))
        tw_spans.append({'name':name,'rva':f'{rva:08x}','bytes':size,'sha256':sha(code)})
    gaps=['Actual scene visibility policy, actor allocation/full native records/resources/text and camera/cache/position lifecycle remain required.',
        'TW common enrollment/cleanup/TW-origin movement, Application/listeners/native login/full bootstrap and timing/pending/reset/full5D remain unhosted.',
        'Native61/full scene reset must bind actual owner to reset_recipient; normal128-entry flag1 subset only, other pool/alias states remain open.',
        'Dynamic appearance/mount/state/resource/text, larger handle/coordinate, battle/path/transfer and all remaining gameplay variants/denominator remain open.',
        'Registry stores expected send-submitted actor state, not observed client memory, queue acceptance, rendered acceptance or deployment.']
    out.mkdir(parents=True);snapshots=[]
    def save(rel,data,origin):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(origin)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,origin in pending:save(rel,data,origin)
    save('prior-ledger.json',prior,ledger_path)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    dump(out/'source-adaptation-receipt.json',changes)
    dump(out/'native-visible-actor-contract.json',{'native_pins':{'cn':CN_PIN,'tw':TW_PIN},'cn_spans':native,
        'tw_spans':tw_spans,'cn_branches':branches,'remote_identity':'both6F constructors low12; both5E/73 low16',
        'cn_constructor':'0052f5a0 replaces ->00532410 freeFFFFFFFF/128; state body+6,15-bit position body+12',
        'cn_delete':'0052fd40 ->0052ffc0 retires resources; identity cleared only owner13418==1',
        'normal_delete_flag_initialization':['0052f170','005309f0'],
        'same_opcode_equivalence_assumed':False,'strings_unconverted_by_registry':True,
        'private_binding_source':'exact full6F/5E/73 inputs and real ready pair ->6F send API submission',
        'all_registered_observers_checked_before_and_after_cas':True,'client_receipt_or_render_observed':False})
    manifest={'kind':'full native6F ->expected directed actor/private incarnation ->all registered observers5E/common position ->retained coordinates ->native73/pool reset/generation-qualified CN ready/movement/transport cleanup',
        'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,'native_spans':native,'tw_native_spans':tw_spans,
        'new_source_files':3,'modified_cpp_files':6,'source_owner_chains_added':1,
        'new_phase_opcode_bindings':3,'new_unique_cn_phase_opcode_binding_values':2,'new_opcode_values':0,
        'formal_application_hosted':False,'concrete_common_visible_incarnation_owner':True,
        'actual_visibility_policy_and_native_data_supplier_implemented':False,'tw_enrolled_in_common_presence':False,
        'cn_transport_owned_visible_cleanup_connected':True,'new_complete_routes':0,'remaining':gaps,
        'previous_goal_turn_classification':'progress: dual-native5E/common-position/real send API chain sealed',
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        **{k:False for k in ['build_run','tests_run','runtime_run','lua_executed','asset_loaders_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'TW/CN native visible6F/5E/73 incarnation and common lifecycle cleanup',
        'status':'已接原生6F提交/私有角色實例/全部登記觀察者5E/73移除與CN斷線清理；可見性政策及原生資料供應未掛載',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{'world-connection-1':['6F','5E','73']},
        'source_paths':SOURCES,'source_owner_chains_added':1,'formal_application_hosted':False,
        'complete_gameplay_routes_added':0,'storage_writes':'no new tables/writes; existing common position CAS retained',
        'shared_storage':['common ready presence and current saved position; expected view data transient'],
        'native_form_qualifications':{'cn_native_6f_73':True,'both_remote_handles_low12':True,
            'private_incarnation_and_all_observers':True,'cn_transport_cleanup':True,
            'native_render_acceptance':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=['Bind actual scene actor/native data/resource/text suppliers and native pool reset to this common visible-incarnation owner.']+gaps
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'cn_native_functions':len(native),
        'new_cpp_files':3,'modified_cpp_files':6,'new_unique_cn_phase_bindings':2,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
