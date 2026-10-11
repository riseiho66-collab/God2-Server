"""Seal retained native CN outdoor profile/cache source and trigger frontier.

Static provenance and source accounting. No loaders, Lua or gameplay executed.
"""
import hashlib
import json
import re
from pathlib import Path
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_OP_IMM
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN,PIN

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-outdoor-cache-lifecycle-01'
ROUND='20261006-cn-outdoor-cache-lifecycle'
PREVIOUS='cn-initial-scene-provider-01'
SOURCES=[
    'src/cn/assets/CnOutdoorSceneResources.h','src/cn/assets/CnOutdoorSceneResources.cpp',
    'src/cn/world/CnOutdoorWindow.h','src/cn/world/CnOutdoorWindow.cpp',
    'src/cn/assets/CnOutdoorModelAsset.h','src/cn/assets/CnOutdoorModelAsset.cpp',
    'src/cn/assets/CnSceneAssets.h','src/cn/assets/CnSceneAssets.cpp',
    'src/cn/world/SharedInitialScene.h','src/cn/world/SharedInitialScene.cpp',
    'src/cn/assets/CnOutdoorMapAsset.h','src/cn/assets/CnOutdoorMapAsset.cpp',
    'src/cn/assets/CnOutdoorTerrain.h','src/cn/assets/CnOutdoorTerrain.cpp',
    'src/cn/world/CnMapPassability.h','src/cn/world/CnMapPassability.cpp',
    'src/cn/world/SharedMovement.h','src/cn/world/SharedMovement.cpp',
    'docs/research/cn-outdoor-cache-lifecycle-20261006.md',
]
MODIFIED=[r for r in SOURCES[4:10]]
TARGETS={0x46d460,0x46f630,0x465740,0x45e4e0,0x46c830,0x46ce10,0x470c90,0x472380}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve existing delivery')
    ledger_path=ROOT/'packet-route-ledger.json';prior=ledger_path.read_bytes();ledger=json.loads(prior)
    before=ROOT/PREVIOUS
    raw=(before/'integration-manifest.json').read_bytes()
    expected=ledger['cn_account_admission_evidence'][PREVIOUS]['artifact_sha256']['integration-manifest.json']
    if sha(raw)!=expected:raise ValueError('Historical integration manifest changed')
    previous_manifest=json.loads(raw);snap_index={r['path']:r for r in previous_manifest['snapshots']}
    pending=[('prior-integration-manifest.json',raw,before/'integration-manifest.json')]
    changes=[]
    for rel in MODIFIED:
        old=(before/rel).read_bytes()
        if sha(old)!=snap_index[rel]['sha256']:raise ValueError('Sealed source baseline changed')
        pending.append(('prior-sources/'+rel,old,before/rel))
        changes.append({'path':rel,'previous_sealed_sha256':sha(old),
            'current_sha256':sha((SERVER/rel).read_bytes()),'old_snapshot_preserved':True,
            'adaptation':'retain decoded native profile/heights and seed the exact initial lease cache'})
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('CN native pin changed')
    pe=pefile.PE(data=raw,fast_load=True);decoder=Cs(CS_ARCH_X86,CS_MODE_32);decoder.detail=True
    directory=CN/'artifacts/native/20261006-cn-chunk-lifecycle-01'
    evidence_path=directory/'chunk-lifecycle-evidence.json';raw=evidence_path.read_bytes();evidence=json.loads(raw)
    if evidence['client_sha256']!=PIN:raise ValueError('Historical native evidence pin differs')
    pending.append(('native/chunk-lifecycle-evidence.json',raw,evidence_path))
    spans=[];calls=[]
    def inspect(address,source,original,expected_code=None,legacy=None,asm=None):
        match=re.search(rb'Address: 0x([0-9a-fA-F]+).*Size: (\d+) bytes',source)
        if not match or int(match.group(1),16)!=int(address,16):raise ValueError('Native source extent/address missing')
        size=int(match.group(2));code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
        if len(code)!=size or (expected_code and sha(code)!=expected_code):raise ValueError('Pinned native span changed')
        instructions=list(decoder.disasm(code,int(address,16)))
        if asm is None:
            asm=('\n'.join(f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in instructions)+'\n').encode('utf8')
        for ins in instructions:
            if ins.mnemonic=='call' and len(ins.operands)==1 and ins.operands[0].type==CS_OP_IMM:
                target=ins.operands[0].imm
                if target in TARGETS:calls.append({'caller':address,'callsite':f'{ins.address:08x}','target':f'{target:08x}'})
        for ext,data,origin in [('.c',source,original),('.asm',asm,'pinned PE disassembly' if legacy is None else directory/(address+'.asm')),('.bin',code,exe)]:
            pending.append(('native/functions/'+address+ext,data,origin))
        item={'address':address,'bytes':size,'source_sha256':sha(source),'native_sha256':sha(code),
            'source_original':str(original),'historical_evidence_reference':legacy is not None,
            'disassembly_decoded_bytes':sum(i.size for i in instructions),
            'native_span_is_not_complete_gameplay_route':True}
        if legacy is not None:
            item.update({'legacy_snapshot_sha256':sha(legacy),'legacy_line_endings_differ':legacy!=source,'old_manifest_preserved':True})
        spans.append(item)
    for row in evidence['functions']:
        p=Path(row['source']);source=p.read_bytes();address=row['va']
        if sha(source)!=row['source_sha256']:raise ValueError('Original recovered C changed')
        legacy=(directory/(address+'.c')).read_bytes()
        if source.replace(b'\r\n',b'\n')!=legacy.replace(b'\r\n',b'\n'):raise ValueError('Legacy source content differs')
        inspect(address,source,p,row['code_sha256'],legacy,(directory/(address+'.asm')).read_bytes())
    recovery=CN.parent/'God2_opt_source_recovery_20260926_055734/decompiled/part_0006'
    for address in ['0046ce10','00470c90']:
        p=recovery/(address+'_FUN_'+address+'.c');inspect(address,p.read_bytes(),p)
    frontier={
        'client_sha256':PIN,'direct_native_calls':calls,
        'cache_branch':{'source':'0046c830 ->0046d460 ->valid reuse/invalid0045e4e0 ->0046f630',
            'source_connected':'fully loaded unchanged decoded profile with declared native masks',
            'rotation':'x first then y; |delta|>1 invalidates all; each recycled edge invalidated before row-major reload',
            'cache_labels':'internal allocation labels, not wire/native addresses'},
        'ordinary_camera_trigger':{'source':'00473120 ->0046ce10 ->conditional00470c90',
            'required_inputs':'actual viewport at map+FD8, tile extents+34/+38 and camera/view coordinates through00472380',
            'edge_thresholds':[-19,40],'native_map34_values':[5,16,17],
            'actor_coordinate_div21_equivalent':False,'formal_owner_connected':False},
        'resource_switch':{'source':'00470c90 parses.map reference and selects/replaces map+1024[map+102C] before cache loading',
            'cache_helpers_shared':True,'entire_switch_route_qualified':False,
            'standalone_or_no_mbd_branch_connected':False},
        'new_opcode_values':0,'new_complete_routes':0,'whole_game_route_total':None,
        'tests_run':False,'runtime_run':False,
    }
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
    dump(out/'native-trigger-frontier.json',frontier)
    dump(out/'source-adaptation-receipt.json',changes)
    gaps=[
        'Exact ordinary camera/viewport/00472380 trigger and00470C90.map resource selection/replacement, standalone variants and render lifecycle remain unhosted.',
        'Only fully loaded unchanged profile/declared-frame cache transitions are connected; partial/null/failed slots and runtime object/frame changes remain open.',
        'Internal cache candidate/CAS is not shared position authorization or a native counter; real actor/scene revision and position/cache/publication transaction are still required.',
        'Actual movement timing/sequence/reset/full5D and remote TW/CN broadcast, real WorldOwner and later Application dispatcher remain missing.',
        'All native login/character/full bootstrap suppliers, TW enrollment and remaining gameplay/variant/deferred denominator remain open.',
    ]
    manifest={
        'kind':'actual CN retained MDT/MDL/ROM/MBD profile -> initial shared lease cache -> native full9 rotation/reuse/reload -> full native cells -> private same-instance cache generation CAS',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':snapshots,'source_adaptations':changes,
        'native_spans':spans,'native_function_spans':len(spans),'new_trigger_function_snapshots':2,
        'new_source_files':4,'source_owner_chains_added':1,'new_phase_opcode_bindings':0,
        'source_cache_generation_is_internal_policy_not_native_or_position_revision':True,
        'new_native_movement_trigger_connected':False,'native_actual_world_owner_implemented':False,
        'formal_application_hosted':False,'new_complete_routes':0,'previous_goal_turn_classification':'progress: actual initial resource supplier/normal2A same-lease gate sealed',
        'remaining':gaps,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'asset_loaders_executed':False,'lua_executed':False,
        'deployed':False,'production_database_read_or_modified':False,'client_modified':False,
        'font_modified':False,'text_conversion_modified':False,
    }
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({
        'name':'CN retained native outdoor profile and complete-cache rotation/reload to current grid',
        'status':'已接解碼資源保留、完整九塊X先Y旋轉／重用／重載及內部cache CAS；camera／.map／失敗載入／真正world authority未掛載',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},'source_paths':SOURCES,
        'source_owner_chains_added':1,'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':False,
        'shared_storage':['existing normal initial character/map/presence lease; no added gameplay table'],
        'native_form_qualifications':{'fully_loaded_unchanged_mode0_cache':True,'whole_opcode_variants_complete':False,
            'camera_map_switch_connected':False,'internal_cache_cas_is_not_position_authorization':True},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps,
    })
    for segment in ledger['dual_client_source_segments']:
        if segment['name'].startswith('CN normal initial scene supplier'):
            segment['retained_outdoor_resources_and_cache']=out.relative_to(SERVER).as_posix()
        if segment['name'].startswith('CN adjacent movement'):
            segment['conditional_outdoor_cache_supplier']=out.relative_to(SERVER).as_posix()
            segment['actual_live_world_owner_implemented']=False
    ledger['cn_account_admission_evidence'][NAME]={
        'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()},
    }
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=[
        'Recover actual native camera/viewport/00472380 trigger,00470C90.map source selection and actor/resource ownership; connect the correct cache branch rather than actor coordinate division.',
        'Connect failed/null/runtime-frame cache variants and actual WorldOwner/scene revision with shared position commit and TW/CN publication.',
        'Recover native pending-ring/reset/timing/full5D data authority; connect mixed later dispatcher/Application listeners and actual actor/bootstrap/TW registry enrollment.',
        'Continue full TW/CN gameplay and native success data suppliers with direction/state/variant/deferred accounting; preserve saves/native fonts/conversion, no phase1 tests/build/runtime/deploy.',
    ]
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'native_function_spans':len(spans),
        'new_trigger_snapshots':2,'new_source_files':4,'new_phase_bindings':0,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
