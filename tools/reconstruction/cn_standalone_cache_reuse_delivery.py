"""Seal static retained standalone byte reuse and native model-refresh frontier."""
import json
import re
import struct
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_OP_IMM
from .cn_outdoor_cache_lifecycle_delivery import SERVER,CN,PIN,ROOT,sha,dump

NAME='cn-standalone-cache-reuse-01'
ROUND='20261006-cn-standalone-cache-reuse'
PREVIOUS='cn-standalone-map-replacement-01'
CACHE='cn-outdoor-cache-lifecycle-01'
MODIFIED=['src/cn/world/CnOutdoorWindow.h','src/cn/world/CnOutdoorWindow.cpp',
    'src/cn/assets/CnSceneAssets.h','src/cn/assets/CnSceneAssets.cpp']
SOURCES=MODIFIED+['src/cn/assets/CnStandaloneMapAsset.h','src/cn/assets/CnStandaloneMapAsset.cpp',
    'src/cn/assets/CnOutdoorSceneResources.h','src/cn/assets/CnOutdoorSceneResources.cpp',
    'src/cn/world/CnMapPassability.h','src/cn/world/CnMapPassability.cpp',
    'src/cn/assets/CnResourceBytes.h','src/cn/assets/CnResourceBytes.cpp',
    'docs/research/cn-standalone-cache-reuse-20261006.md']
FUNCTIONS=[('00470c90',6),('0046d460',6),('0045e7f0',5),('0046f630',6),
    ('00473a20',6),('0046c280',6),('0046bd50',6),('00470010',6)]

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve existing delivery')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    pending=[];old_manifests={};old_spans={}
    for name in [PREVIOUS,CACHE]:
        p=ROOT/name/'integration-manifest.json';raw=p.read_bytes()
        if sha(raw)!=ledger['cn_account_admission_evidence'][name]['artifact_sha256']['integration-manifest.json']:
            raise ValueError('Historical manifest changed')
        old_manifests[name]=json.loads(raw)
        for row in old_manifests[name]['native_spans']:
            old=old_spans.get(row['address'])
            if old and old['native_sha256']!=row['native_sha256']:raise ValueError('Historical native conflict')
            old_spans[row['address']]=row
        pending.append(('prior-manifests/'+name+'.json',raw,p))
    changes=[];old_sources={r['path']:r for r in old_manifests[PREVIOUS]['snapshots']}
    for rel in MODIFIED:
        p=ROOT/PREVIOUS/rel;raw=p.read_bytes()
        if sha(raw)!=old_sources[rel]['sha256']:raise ValueError('Historical source changed')
        pending.append(('prior-sources/'+rel,raw,p))
        changes.append({'path':rel,'before_sha256':sha(raw),'after_sha256':sha((SERVER/rel).read_bytes()),
            'previous_artifact':PREVIOUS,'old_snapshot_preserved':True})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('CN executable pin changed')
    pe=pefile.PE(data=raw,fast_load=True);decoder=Cs(CS_ARCH_X86,CS_MODE_32);decoder.detail=True
    recovery=CN.parent/'God2_opt_source_recovery_20260926_055734/decompiled'
    spans=[];calls=[];targets={int(a,16) for a,_ in FUNCTIONS}
    for address,part in FUNCTIONS:
        p=recovery/f'part_{part:04d}'/(address+'_FUN_'+address+'.c');source=p.read_bytes()
        m=re.search(rb'Address: 0x([0-9a-fA-F]+).*Size: (\d+) bytes',source)
        if not m or int(m.group(1),16)!=int(address,16):raise ValueError('Native extent missing')
        size=int(m.group(2));code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        if len(code)!=size:raise ValueError('Incomplete native span')
        old=old_spans.get(address)
        if old and (sha(code)!=old['native_sha256'] or old['source_sha256'] not in
            {sha(source),sha(source.replace(b'\r\n',b'\n'))}):raise ValueError('Prior native baseline changed')
        ins=list(decoder.disasm(code,int(address,16)))
        asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode()
        for i in ins:
            if i.mnemonic=='call' and len(i.operands)==1 and i.operands[0].type==CS_OP_IMM and i.operands[0].imm in targets:
                calls.append({'caller':address,'site':f'{i.address:08x}','target':f'{i.operands[0].imm:08x}'})
        for suffix,data,origin in [('.c',source,p),('.asm',asm,'pinned PE disassembly'),('.bin',code,exe)]:
            pending.append(('native/functions/'+address+suffix,data,origin))
        spans.append({'address':address,'bytes':size,'source_original':str(p),'source_sha256':sha(source),
            'native_sha256':sha(code),'previous_span_preserved':bool(old),'decoded_bytes':sum(i.size for i in ins)})
    table=pe.get_data(0x7f0ed0-pe.OPTIONAL_HEADER.ImageBase,200)
    if len(table)!=200:raise ValueError('Native5x5 model-offset span missing')
    pending.append(('native/constants/model-5x5-offsets.bin',table,exe))
    gaps=['Failed/null/partial native-success slots, other MAP versions/dimensions and nonalphabet/high-byte axes remain open.',
        'Model refresh00473A20/0046C280 runtime handles/frames/type7 registry and actual camera/scene revisions remain unconnected.',
        'Common scene/position/cache transaction, actual WorldOwner, timing/pending/reset/full5D and TW/CN publication remain missing.',
        'Application/listeners/native login/character/bootstrap and all remaining gameplay routes/denominator remain open.']
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
    dump(out/'native-reuse-model-frontier.json',{'client_sha256':PIN,'functions':spans,'calls':calls,
        'same_resource_reuse':'native pointer/valid rotation; valid updates slot3C with no I/O; invalid calls0045E7F0',
        'source_payloads':'actual immutable byte snapshots/provenance follow internal allocation labels',
        'same_mdt_standalone_resource_replaced':False,'renderer_handle_is_not_cache_or_actor_id':True,
        'refresh_open':'previous5x5 model cleanup ->invalidate1058/105C ->new5x5 type7 renderer',
        'offset_table':{'address':'007f0ed0','native_middle_anchor':'007f0f30','bytes':200,'sha256':sha(table),
            'raw_i32':list(struct.unpack('<50i',table))},'new_opcode_values':0})
    manifest={'kind':'same-MDT standalone native rotation ->retain valid actual MAP bytes/read invalid slots ->real grid ->cache/snapshot commit',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,
        'native_spans':spans,'native_function_spans':len(spans),'native_constant_spans':1,
        'new_source_files':0,'modified_cpp_files':4,'source_owner_chains_added':1,'new_phase_opcode_bindings':0,
        'formal_application_hosted':False,'actual_camera_owner_implemented':False,'same_standalone_full9_reuse_connected':True,
        'valid_payloads_are_not_reread':True,'runtime_model_refresh_connected':False,'new_complete_routes':0,
        'previous_goal_turn_classification':'progress: native flag0/full9 resource replacement sealed',
        'remaining':gaps,'whole_game_route_total':None,'whole_game_completion_percent':None,
        **{k:False for k in ['build_run','tests_run','runtime_run','asset_loaders_executed','lua_executed','deployed',
            'production_database_read_or_modified','client_modified','font_modified','text_conversion_modified']}}
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({'name':'CN same-MDT standalone valid-byte reuse and invalid-slot reload cache owner',
        'status':'已接同MDT獨立MAP格塊原生旋轉/已載入bytes重用/失效格塊讀取及世代提交；partial與WorldOwner未掛載',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':1,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':False,
        'shared_storage':['same common lease/cache; no new table'],
        'native_form_qualifications':{'same_standalone_full9_reuse':True,'valid_chunk_disk_reads':0,
            'native_rotation_horizontal_then_vertical':True,'runtime_model_refresh_connected':False,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps})
    ledger['cn_account_admission_evidence'][NAME]={'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()}}
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=gaps+['Keep native fonts/conversion and frozen saves; no phase1 build/test/runtime/deploy.']
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'native_functions':len(spans),
        'native_constant_spans':1,'new_source_files':0,'modified_cpp_files':4,'new_phase_bindings':0,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
