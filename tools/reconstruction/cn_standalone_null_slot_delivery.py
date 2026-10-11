"""Seal static native open-failure/null-slot/prior-cell source and stop handoff."""
import json
import re
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from .cn_outdoor_cache_lifecycle_delivery import SERVER,CN,PIN,ROOT,sha,dump

NAME='cn-standalone-null-slot-01'
ROUND='20261006-cn-standalone-null-slot'
PREVIOUS='cn-standalone-cache-reuse-01'
REPLACEMENT='cn-standalone-map-replacement-01'
MODIFIED=['src/cn/world/CnOutdoorWindow.h','src/cn/world/CnOutdoorWindow.cpp',
    'src/cn/assets/CnSceneAssets.h','src/cn/assets/CnSceneAssets.cpp',
    'src/cn/assets/CnOutdoorSceneResources.h','src/cn/assets/CnOutdoorSceneResources.cpp',
    'src/cn/assets/CnResourceBytes.h','src/cn/assets/CnResourceBytes.cpp','src/cn/world/CnMapPassability.h']
SOURCES=MODIFIED+['src/cn/world/CnMapPassability.cpp','src/cn/assets/CnStandaloneMapAsset.h',
    'src/cn/assets/CnStandaloneMapAsset.cpp','docs/research/cn-standalone-null-slot-20261006.md']
FUNCTIONS=[('004657e0',6),('0045e7f0',5),('00470c90',6),('0046f630',6),('0046d460',6),('0046c280',6)]

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve existing delivery')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    pending=[];old_manifests={};old_spans={}
    for name in [PREVIOUS,REPLACEMENT]:
        p=ROOT/name/'integration-manifest.json';raw=p.read_bytes()
        if sha(raw)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']:
            raise ValueError('Historical manifest changed')
        old_manifests[name]=json.loads(raw)
        for row in old_manifests[name]['native_spans']:
            old=old_spans.get(row['address'])
            if old and old['native_sha256']!=row['native_sha256']:raise ValueError('Prior native conflict')
            old_spans[row['address']]=row
        pending.append(('prior-manifests/'+name+'.json',raw,p))
    changes=[];old_sources={r['path']:r for r in old_manifests[PREVIOUS]['snapshots']}
    for rel in MODIFIED:
        p=ROOT/PREVIOUS/rel;raw=p.read_bytes()
        if sha(raw)!=old_sources[rel]['sha256']:raise ValueError('Historical source changed')
        pending.append(('prior-sources/'+rel,raw,p))
        changes.append({'path':rel,'previous_artifact':PREVIOUS,'before_sha256':sha(raw),
            'after_sha256':sha((SERVER/rel).read_bytes()),'old_snapshot_preserved':True})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('CN executable pin changed')
    pe=pefile.PE(data=raw,fast_load=True);decoder=Cs(CS_ARCH_X86,CS_MODE_32)
    recovery=CN.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
    spans=[]
    for address,part in FUNCTIONS:
        p=recovery/f'part_{part:04d}'/(address+'_FUN_'+address+'.c');source=p.read_bytes()
        m=re.search(rb'Address: 0x([0-9a-fA-F]+).*Size: (\d+) bytes',source)
        if not m or int(m.group(1),16)!=int(address,16):raise ValueError('Native extent missing')
        size=int(m.group(2));code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        if len(code)!=size:raise ValueError('Incomplete native span')
        old=old_spans[address]
        if sha(code)!=old['native_sha256'] or old['source_sha256'] not in {sha(source),sha(source.replace(b'\r\n',b'\n'))}:
            raise ValueError('Previously pinned native source changed')
        ins=list(decoder.disasm(code,int(address,16)))
        asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode()
        for ext,data,origin in [('.c',source,p),('.asm',asm,'pinned PE disassembly'),('.bin',code,exe)]:
            pending.append(('native/functions/'+address+ext,data,origin))
        spans.append({'address':address,'bytes':size,'source_original':str(p),'source_sha256':sha(source),
            'native_sha256':sha(code),'previous_span_preserved':True,'decoded_bytes':sum(i.size for i in ins)})
    mode=pe.get_data(0x7efee0-pe.OPTIONAL_HEADER.ImageBase,2)
    if mode!=b'r\0':raise ValueError('Pinned standalone fopen mode differs')
    pending.append(('native/constants/plain-open-mode.bin',mode,exe))
    gaps=['MBD failure paths, malformed scanf/other MAP formats/dimensions and unknown axis/encoding variants remain open.',
        'Native adjacent pointer rotation can dereference a null recycled edge; source explicitly refuses this unqualified variant.',
        'Runtime model/frame/reset/renderer state and actual camera/scene/WorldOwner remain missing.',
        'Common position/cache transaction, timing/pending/reset/full5D, TW/CN publication, Application/listeners/bootstrap and all remaining routes remain open.']
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
    dump(out/'native-null-slot-return-contract.json',{'client_sha256':PIN,'functions':spans,
        'decompiler_return_correction':{'function':'004657e0','original_void_c_preserved':True,
            'zero':['0046580c xor eax,eax','00465840 jmp00465de6','00465de9 xor eax,eax'],
            'success':'00465db7 mov eax,1','caller':'0045e829 call /0045e82e test eax'},
        'outer_slot_delete':['004715a4 call0045e7f0','004715a9 test eax','004715c3 destructor','004715c5 slot=0'],
        'outer_success':'00471628 compose /00471653 esi=1; not proof of full9 success',
        'null_terrain_skip':'0046f675 test /0046f677 skip all21x21 writes',
        'center_overlay_gate':'0046f6be..0046f6de center/resource nonnull',
        'prior_bytes':'same initialized63x63 memory indices, no zero/shift reconstruction',
        'pointer_recycle_open':'adjacent recycled edge+54 has no native null guard; source refuses unqualified dereference',
        'plain_fopen_mode':{'address':'007efee0','bytes':2,'sha256':sha(mode)},'new_opcode_values':0})
    manifest={'kind':'actual standalone file-open failure ->null slot/absent coordinates ->prior-cell/center-overlay gate ->private cache snapshot commit',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,
        'native_spans':spans,'native_function_spans':len(spans),'native_constant_spans':1,
        'new_source_files':0,'modified_cpp_files':9,'source_owner_chains_added':1,'new_phase_opcode_bindings':0,
        'formal_application_hosted':False,'actual_camera_owner_implemented':False,'known_open_failure_null_slots_connected':True,
        'null_center_overlay_skip_connected':True,'prior_cells_are_actual_current_cache':True,
        'all_native_failure_variants_complete':False,'new_complete_routes':0,'remaining':gaps,
        'previous_goal_turn_classification':'progress: retained-byte standalone cache reuse sealed',
        'owner_requested_stop_after_this_round':True,'whole_game_route_total':None,'whole_game_completion_percent':None,
        **{k:False for k in ['build_run','tests_run','runtime_run','asset_loaders_executed','lua_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN known standalone open failure/null-slot/prior-cell cache lifecycle',
        'status':'已接真實MAP開檔失敗/null槽/既有cells保留與中央槽缺失的模型跳過；其他failure與WorldOwner未掛載',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':1,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':False,
        'shared_storage':['same common lease/cache; no new table'],
        'native_form_qualifications':{'actual_open_failure_null_slot':True,'null_center_overlay_skip':True,
            'actual_prior_cell_snapshot':True,'null_recycled_edge_native_crash_variant_complete':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['owner_stop_after_round']=True
    plan['next']=['Owner requested stopping after this round: save catalog/report, pause goal, then no further work until resumed.']+gaps
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'native_functions':len(spans),
        'modified_cpp_files':9,'new_source_files':0,'new_complete_routes':0,'owner_stop_after_round':True,'tests_run':False}))

if __name__=='__main__':main()
