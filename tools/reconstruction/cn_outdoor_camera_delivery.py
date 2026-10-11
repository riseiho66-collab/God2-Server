"""Seal static CN camera/native map-reference source and pinned constants."""
import json
import re
import struct
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_OP_IMM
from .cn_outdoor_cache_lifecycle_delivery import SERVER,CN,PIN,ROOT,sha,dump

NAME='cn-outdoor-camera-trigger-01'
ROUND='20261006-cn-outdoor-camera-trigger'
PREVIOUS='cn-outdoor-cache-lifecycle-01'
SOURCES=[
    'src/cn/world/CnOutdoorCamera.h','src/cn/world/CnOutdoorCamera.cpp',
    'src/cn/world/CnOutdoorWindow.h','src/cn/world/CnOutdoorWindow.cpp',
    'src/cn/world/SharedInitialScene.h','src/cn/world/SharedInitialScene.cpp',
    'src/cn/assets/CnOutdoorSceneResources.h','src/cn/assets/CnOutdoorSceneResources.cpp',
    'docs/research/cn-outdoor-camera-trigger-20261006.md',
]
ADDRESSES=['004749a0','00475be0','00472380','0046ce10','00473120',
    '004621f0','00461ed0','00470440','00470c90']
TABLES=[('projection-x',0x7f0fb8,20,'i32'),('projection-y',0x7f0fcc,20,'i32'),
    ('camera-offsets',0x7f0e68,72,'i32'),('half',0x7ed104,4,'f32'),
    ('minus-half',0x7f1170,4,'f32'),('twenty',0x7f116c,4,'f32'),('zero',0x7ed260,4,'f32'),
    ('map-format',0x7f0100,12,'cstr'),('axis-format',0x7f0384,5,'cstr')]

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve existing delivery')
    path=ROOT/'packet-route-ledger.json';prior=path.read_bytes();ledger=json.loads(prior)
    old_root=ROOT/PREVIOUS;old_raw=(old_root/'integration-manifest.json').read_bytes()
    if sha(old_raw)!=ledger['cn_account_admission_evidence'][PREVIOUS]['artifact_sha256']['integration-manifest.json']:
        raise ValueError('Historical manifest changed')
    old=json.loads(old_raw);old_spans={r['address']:r for r in old['native_spans']}
    old_sources={r['path']:r for r in old['snapshots']}
    pending=[('prior-integration-manifest.json',old_raw,old_root/'integration-manifest.json')];changes=[]
    for rel in SOURCES[2:4]:
        raw=(old_root/rel).read_bytes()
        if sha(raw)!=old_sources[rel]['sha256']:raise ValueError('Historical source snapshot changed')
        pending.append(('prior-sources/'+rel,raw,old_root/rel))
        changes.append({'path':rel,'before_sealed_sha256':sha(raw),'after_sha256':sha((SERVER/rel).read_bytes()),
            'old_snapshot_preserved':True,'adaptation':'bind camera/visibility/native-reference preparation to the same cache identity/generation'})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('CN native pin changed')
    pe=pefile.PE(data=raw,fast_load=True);decoder=Cs(CS_ARCH_X86,CS_MODE_32);decoder.detail=True
    recovery=CN.parent/'God2_opt_source_recovery_20260926_055734/decompiled/part_0006'
    spans=[];calls=[]
    targets={int(a,16) for a in ADDRESSES}
    for address in ADDRESSES:
        p=recovery/(address+'_FUN_'+address+'.c');source=p.read_bytes()
        m=re.search(rb'Address: 0x([0-9a-fA-F]+).*Size: (\d+) bytes',source)
        if not m or int(m.group(1),16)!=int(address,16):raise ValueError('Original native extent/address unavailable')
        size=int(m.group(2));code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        if len(code)!=size:raise ValueError('Pinned native span incomplete')
        if address in old_spans:
            if sha(source)!=old_spans[address]['source_sha256'] or sha(code)!=old_spans[address]['native_sha256']:
                raise ValueError('Previously pinned native span changed')
        ins=list(decoder.disasm(code,int(address,16)))
        asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in ins)+'\n').encode('utf8')
        for i in ins:
            if i.mnemonic=='call' and len(i.operands)==1 and i.operands[0].type==CS_OP_IMM and i.operands[0].imm in targets:
                calls.append({'caller':address,'callsite':f'{i.address:08x}','target':f'{i.operands[0].imm:08x}'})
        for ext,data,origin in [('.c',source,p),('.asm',asm,'pinned PE disassembly'),('.bin',code,exe)]:
            pending.append(('native/functions/'+address+ext,data,origin))
        spans.append({'address':address,'bytes':size,'source_original':str(p),'source_sha256':sha(source),
            'native_sha256':sha(code),'previous_span_preserved':address in old_spans,
            'decoded_bytes':sum(i.size for i in ins),'not_complete_gameplay_route':True})
    tables=[]
    for name,address,size,kind in TABLES:
        data=pe.get_data(address-pe.OPTIONAL_HEADER.ImageBase,size)
        if len(data)!=size:raise ValueError('Pinned native constant extent unavailable')
        value=list(struct.unpack('<'+'i'*(size//4),data)) if kind=='i32' else (
            list(struct.unpack('<f',data)) if kind=='f32' else data.rstrip(b'\0').decode('ascii'))
        pending.append(('native/constants/'+name+'.bin',data,exe))
        tables.append({'name':name,'address':f'{address:08x}','bytes':size,'sha256':sha(data),'type':kind,'value':value})
    native_relation={
        'client_sha256':PIN,'native_functions':spans,'direct_calls':calls,'constants':tables,
        'projection':'mode0 camera+3360/840 ->signed /80,/40 residues ->5 native SSE diamond cases ->21/21 offsets ->subtract21/63',
        'visibility':'actual viewport/tile extents ->4 corners ->signed /21 ->native unique-corner bridges and nine flags',
        'reference':'actual owner prefix +axisA0..Z9 +x +axisA0..Z9 +.map; native%c%d axis helper, ASCII alphabet/digit consumer',
        'switch_gate':'nonzero viewport shift with native map+34 in5/16/17 and nonnegative target center',
        'camera_after_success':'original camera minus pinned007F0E68 offset; must wait for actual00470C90 success',
        'unsupported':'nonalphabet/high-byte/locale/overflow variants, resource replacement/standalone loaders and actual camera/world owner',
        'new_opcode_values':0,'new_complete_routes':0,'whole_game_denominator':None,
        'build_run':False,'tests_run':False,'runtime_run':False,
    }
    out.mkdir(parents=True);snapshots=[]
    def save(rel,data,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(original)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,original in pending:save(rel,data,original)
    save('prior-ledger.json',prior,path)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    dump(out/'native-camera-reference-relation.json',native_relation)
    dump(out/'source-adaptation-receipt.json',changes)
    gaps=[
        'Actual camera/viewport/tile-extents/map+34/native prefix state must be supplied by the real scene owner, not2E, catalog kind or desktop defaults.',
        'Camera/reference candidates are bound to the cache identity/generation, but00470C90 native resource identity/replacement/standalone loading and camera application remain unhosted.',
        'ASCII axis0..259 and native diamond/visibility branches are connected in source; nonalphabet/high-byte/locale/malformed/overflow variants remain open.',
        'Partial/null/failed chunk loads, dynamic object/frame data and actual actor/scene revision/position/cache transaction remain missing.',
        'Native timing/pending sequence/reset/full5D, TW/CN publication, real WorldOwner, later dispatcher and Application listeners remain open.',
        'Every remaining gameplay route and full directional/phase/state/variant/indirect/deferred denominator must still be closed; no full route added.',
    ]
    manifest={
        'kind':'real mode0 View ->native screen/diamond/grid/visibility ->cache-bound native.map switch request and conditional success-camera offset',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,
        'native_spans':spans,'native_function_spans':len(spans),'native_constant_spans':len(tables),
        'new_source_files':2,'source_owner_chains_added':1,'new_phase_opcode_bindings':0,
        'formal_application_hosted':False,'actual_camera_owner_implemented':False,'native_map_loader_connected':False,
        'camera_is_not_applied_without_actual_resource_success':True,'new_complete_routes':0,
        'previous_goal_turn_classification':'progress: retained outdoor resources and full9 cache rotation/reload source sealed',
        'remaining':gaps,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'asset_loaders_executed':False,
        'lua_executed':False,'deployed':False,'production_database_read_or_modified':False,
        'client_modified':False,'font_modified':False,'text_conversion_modified':False,
    }
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({
        'name':'CN native camera projection/visibility/axis-coded.map reference bound to actual cache generation',
        'status':'已接原生畫面菱形投影／九格可見旗標及cache世代的.map切換候選；真正camera／資源替換／world owner未掛載',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':1,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':False,
        'shared_storage':['same initial common lease/cache; no new gameplay table'],
        'native_form_qualifications':{'mode0_diamond_regions':5,'ascii_axis_subset':[0,259],
            'native_map34_switch_values':[5,16,17],'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps,
    })
    for segment in ledger['dual_client_source_segments']:
        if segment['name'].startswith('CN retained native outdoor profile'):
            segment['camera_trigger_source']=out.relative_to(SERVER).as_posix()
            segment['actual_camera_resource_owner_implemented']=False
    ledger['cn_account_admission_evidence'][NAME]={
        'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()},
    }
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=[
        'Connect actual native.map/.mdt resource identity/prefix/current replacement in00470C90 and real actor/camera state; consume the cache-bound request and only apply camera on actual successful switch.',
        'Connect partial/failed/runtime-object/frame cache branches and common position/scene transaction with TW/CN publication and actual WorldOwner.',
        'Recover movement timing/pending/reset/full5D and authoritative native login/character/bootstrap data, then host later dispatcher/Application/shared listeners and TW registry.',
        'Continue all TW/CN phase/state/variant/indirect/deferred accounting and full gameplay; preserve native fonts/conversion/saves, no phase1 build/tests/runtime/deploy.',
    ]
    dump(path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'native_functions':len(spans),
        'native_constant_spans':len(tables),'new_source_files':2,'new_phase_bindings':0,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
