"""Seal static same-MDT/MBD camera-to-cache source and primary return evidence."""
import json
import re
from pathlib import Path
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM
from .cn_outdoor_cache_lifecycle_delivery import SERVER, CN, PIN, ROOT, sha, dump

NAME='cn-camera-map-resource-owner-01'
ROUND='20261006-cn-camera-map-resource-owner'
CAMERA='cn-outdoor-camera-trigger-01'
CACHE='cn-outdoor-cache-lifecycle-01'
INITIAL='cn-initial-scene-provider-01'
MODIFIED=['src/cn/world/CnOutdoorWindow.h','src/cn/world/CnOutdoorWindow.cpp',
    'src/cn/assets/CnOutdoorSceneResources.h','src/cn/assets/CnOutdoorSceneResources.cpp',
    'src/cn/assets/CnSceneAssets.cpp']
SOURCES=MODIFIED+['src/cn/world/CnOutdoorCamera.h','src/cn/world/CnOutdoorCamera.cpp',
    'src/cn/world/SharedInitialScene.h','src/cn/world/SharedInitialScene.cpp',
    'docs/research/cn-camera-map-resource-owner-20261006.md']
FUNCTIONS=[('00470c90',6),('00471eb0',6),('0053ff40',17),('004241b0',2),
    ('0046d9d0',6),('004621f0',6),('00461ed0',6),('0046d460',6),('0046c830',6)]
STRINGS=[('native-map-root',0x7f2604),('cwd-with-separator',0x7ed048),
    ('cwd-concatenated',0x7ef868),('mdt-extension',0x7f0d04)]

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve existing delivery')
    ledger_path=ROOT/'packet-route-ledger.json'
    prior=ledger_path.read_bytes();ledger=json.loads(prior)
    pending=[];old_manifests={};spans_index={}
    for name in [CAMERA,CACHE,INITIAL]:
        p=ROOT/name/'integration-manifest.json';raw=p.read_bytes()
        expected=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']
        if sha(raw)!=expected:raise ValueError('Historical manifest changed')
        old_manifests[name]=json.loads(raw)
        for row in old_manifests[name]['native_spans']:
            previous=spans_index.get(row['address'])
            if previous and previous['native_sha256']!=row['native_sha256']:
                raise ValueError('Historical native span conflict')
            spans_index[row['address']]=row
        pending.append(('prior-manifests/'+name+'.json',raw,p))
    changes=[]
    for rel in MODIFIED:
        name=CACHE if rel.endswith('CnSceneAssets.cpp') else CAMERA
        source_index={row['path']:row for row in old_manifests[name]['snapshots']}
        p=ROOT/name/rel;raw=p.read_bytes()
        if sha(raw)!=source_index[rel]['sha256']:raise ValueError('Sealed source changed')
        pending.append(('prior-sources/'+rel,raw,p))
        changes.append({'path':rel,'previous_artifact':name,'before_sha256':sha(raw),
            'after_sha256':sha((SERVER/rel).read_bytes()),'old_snapshot_preserved':True})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('CN native executable pin changed')
    pe=pefile.PE(data=raw,fast_load=True)
    decoder=Cs(CS_ARCH_X86,CS_MODE_32);decoder.detail=True
    recovery=CN.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
    spans=[];calls=[];targets={int(a,16) for a,_ in FUNCTIONS}
    for address,part in FUNCTIONS:
        p=recovery/f'part_{part:04d}'/(address+'_FUN_'+address+'.c');source=p.read_bytes()
        m=re.search(rb'Address: 0x([0-9a-fA-F]+).*Size: (\d+) bytes',source)
        if not m or int(m.group(1),16)!=int(address,16):raise ValueError('Native extent unavailable')
        size=int(m.group(2));code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        if len(code)!=size:raise ValueError('Incomplete native span')
        old=spans_index.get(address)
        if old:
            if sha(code)!=old['native_sha256']:raise ValueError('Prior native bytes changed')
            if sha(source)!=old['source_sha256']:
                # Older receipts may normalize CRLF; retain both original hashes.
                if sha(source.replace(b'\r\n',b'\n'))!=old['source_sha256']:
                    raise ValueError('Prior native source changed')
        ins=list(decoder.disasm(code,int(address,16)))
        asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode()
        for i in ins:
            if i.mnemonic=='call' and len(i.operands)==1 and i.operands[0].type==CS_OP_IMM and i.operands[0].imm in targets:
                calls.append({'caller':address,'callsite':f'{i.address:08x}','target':f'{i.operands[0].imm:08x}'})
        for suffix,data,origin in [('.c',source,p),('.asm',asm,'pinned PE'),('.bin',code,exe)]:
            pending.append(('native/functions/'+address+suffix,data,origin))
        spans.append({'address':address,'bytes':size,'source_original':str(p),'source_sha256':sha(source),
            'native_sha256':sha(code),'previous_span_preserved':bool(old),'decoded_bytes':sum(i.size for i in ins)})
    strings=[]
    for name,address in STRINGS:
        data=pe.get_data(address-pe.OPTIONAL_HEADER.ImageBase,40).split(b'\0',1)[0]+b'\0'
        pending.append(('native/constants/'+name+'.bin',data,exe))
        strings.append({'name':name,'address':f'{address:08x}','bytes':len(data),'sha256':sha(data),
            'value':data[:-1].decode('ascii')})
    gaps=[
        'Different/absent MDT replacement and standalone.map loading remain unconnected.',
        'Full9 retained-MBD subset only: partial/null/failed native-success slots and runtime frames remain open.',
        'Actual actor camera/viewport/map34/prefix, scene revision, common position/cache transaction and WorldOwner are unhosted.',
        'Movement timing/pending/reset/full5D, TW/CN publication and Application/shared listeners remain missing.',
        'All remaining game routes and full direction/phase/state/variant/indirect/deferred denominator remain open.',
    ]
    out.mkdir(parents=True);snapshots=[]
    def save(rel,data,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(original)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,original in pending:save(rel,data,original)
    save('prior-ledger.json',prior,ledger_path)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    dump(out/'source-adaptation-receipt.json',changes)
    dump(out/'native-resource-relation.json',{'client_sha256':PIN,'functions':spans,'direct_calls':calls,
        'strings':strings,'qualified_subset':'same-MDT/retained-MBD/full9/ASCII identity',
        'native_cwd_is_concatenation_not_canonicalization':True,'new_opcode_values':0})
    dump(out/'decompiler-return-correction.json',{'function':'00470c90','original_c_preserved':True,
        'old_return_declaration':'void','primary_return_register':'EAX',
        'primary_asm':['00471653 mov esi,1','00471662 xor esi,esi','004716e3 mov eax,esi','00471700 ret 0xc'],
        'consumer':'00473120 conditional camera offset','all_slots_success_not_proven_by_return':True})
    manifest={'kind':'current camera.map request ->actual retained MDT identity/MBD cells ->private cache commit ->conditional camera result',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,
        'native_spans':spans,'native_function_spans':len(spans),'native_constant_spans':len(strings),
        'new_source_files':0,'modified_cpp_files':5,'source_owner_chains_added':1,'new_phase_opcode_bindings':0,
        'formal_application_hosted':False,'actual_camera_owner_implemented':False,
        'native_same_resource_mbd_full9_connected':True,'native_resource_replacement_connected':False,
        'camera_result_only_after_cache_commit':True,'new_complete_routes':0,'remaining':gaps,
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'asset_loaders_executed':False,
        'lua_executed':False,'deployed':False,'production_database_read_or_modified':False,
        'client_modified':False,'font_modified':False,'text_conversion_modified':False}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({
        'name':'CN current camera request to same-MDT retained-MBD full9 cache commit',
        'status':'已接同MDT身分/MBD真實九格及cache提交後camera結果；替換資源與WorldOwner未掛載',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':1,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':False,
        'shared_storage':['same common lease/cache; no new gameplay table'],
        'native_form_qualifications':{'same_resource_mbd_full9':True,'printable_ascii_identity':True,
            'resource_replacement_connected':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=[gaps[0],gaps[1],gaps[2],gaps[3],
        'Continue complete TW/CN route denominator and source integration; preserve native fonts/conversion, no phase1 execution.']
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'native_functions':len(spans),
        'native_strings':len(strings),'modified_cpp_files':5,'new_source_files':0,
        'new_phase_bindings':0,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
