"""Seal native CN asset imports and normal initial scene/common-lease supply.

Static source/provenance accounting only; never invokes a loader or gameplay.
"""
import hashlib
import json
import re
from pathlib import Path
import pefile
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN,PIN

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-initial-scene-provider-01'
ROUND='20261006-cn-initial-scene-provider'
ADDITIONAL=[
    'src/cn/world/SharedInitialScene.h','src/cn/world/SharedInitialScene.cpp',
    'src/cn/auth/SharedWorldSelection.h','src/cn/auth/SharedWorldSelection.cpp',
    'src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp',
    'docs/research/cn-initial-scene-provider-20261006.md',
]
EVIDENCE=[
    ('20261006-cn-house-assets-01','house-assets-evidence.json'),
    ('20261006-cn-scene-binding-01','scene-binding-evidence.json'),
    ('20261006-cn-outdoor-map-01','outdoor-map-evidence.json'),
    ('20261006-cn-outdoor-models-01','outdoor-model-evidence.json'),
    ('20261006-cn-outdoor-terrain-01','outdoor-terrain-evidence.json'),
    ('20261006-cn-outdoor-coordinates-01','outdoor-coordinate-evidence.json'),
    ('20261006-cn-rom-geometry-01','rom-geometry-evidence.json'),
]

def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed delivery')
    imports=json.loads((out/'import-receipt.json').read_text(encoding='utf8'))
    adaptations=[]
    for row in imports:
        raw=(out/row['snapshot']).read_bytes()
        if sha(raw)!=row['source_sha256']:raise ValueError('Raw upstream snapshot differs')
        include_only=raw.replace(b'#include "assets/',b'#include "cn/assets/').replace(
            b'#include "protocol/CnWorldEntry.h"',b'#include "cn/protocol/CnWorldEntry.h"').replace(
            b'#include "world/CnMapPassability.h"',b'#include "cn/world/CnMapPassability.h"')
        if sha(include_only)!=row['initial_target_sha256']:raise ValueError('Original include adaptation differs')
        final=(SERVER/row['target']).read_bytes()
        if row['target'] not in ('src/cn/assets/CnSceneAssets.h','src/cn/assets/CnSceneAssets.cpp'):
            if sha(final)!=row['initial_target_sha256']:raise ValueError('Unexpected imported source adaptation')
        adaptations.append({'target':row['target'],'initial_include_only_sha256':sha(include_only),
            'final_sha256':sha(final),'further_adaptation':
            'retain actual CAN and selected HMD source paths' if final!=include_only else 'none'})
    sources=[r['target'] for r in imports]+ADDITIONAL
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('CN native pin changed')
    pe=pefile.PE(data=raw,fast_load=True)
    native={};pending=[];references=0
    for name,filename in EVIDENCE:
        directory=CN/'artifacts/native'/name
        raw=(directory/filename).read_bytes();evidence=json.loads(raw)
        if evidence['client_sha256']!=PIN:raise ValueError('Native evidence pin differs')
        pending.append(('native/evidence/'+name+'/'+filename,raw,directory/filename))
        for row in evidence['functions']:
            references+=1;address=row['va']
            original=row.get('source',row.get('original'))
            if not original:raise ValueError('Original native C provenance missing')
            p=Path(original);source=p.read_bytes()
            if sha(source)!=row['source_sha256']:raise ValueError('Original native C changed')
            legacy_path=directory/(address+'.c');legacy=legacy_path.read_bytes()
            if source.replace(b'\r\n',b'\n')!=legacy.replace(b'\r\n',b'\n'):
                raise ValueError('Legacy C differs beyond preserved line endings')
            match=re.search(rb'Size: (\d+) bytes',source)
            if not match:raise ValueError('Native extent unavailable')
            size=int(match.group(1));code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
            if len(code)!=size or sha(code)!=row['code_sha256']:raise ValueError('Native PE extent changed')
            link={'evidence':name,'legacy_snapshot_sha256':sha(legacy),
                  'legacy_line_endings_differ':legacy!=source,'old_manifest_preserved':True}
            if address in native:
                if native[address]['source_sha256']!=sha(source) or native[address]['native_sha256']!=sha(code):
                    raise ValueError('Native repeated span identity differs')
                native[address]['evidence_references'].append(link)
            else:
                native[address]={'address':address,'bytes':size,'source_sha256':sha(source),
                    'native_sha256':sha(code),'evidence_references':[link]}
                for extension,data,original in [('.c',source,p),('.asm',(directory/(address+'.asm')).read_bytes(),directory/(address+'.asm')),('.bin',code,exe)]:
                    pending.append(('native/functions/'+address+extension,data,original))
    path=ROOT/'packet-route-ledger.json';prior=path.read_bytes();ledger=json.loads(prior);snapshots=[]
    def save(rel,data,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as file:file.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(original)})
    for rel in sources:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,original in pending:save(rel,data,original)
    save('prior-ledger.json',prior,path)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    dump(out/'adaptation-receipt.json',adaptations)
    gaps=[
        'Actual scene owner/profile revision and pinned loaded asset lifetime, actor allocation/placement/full2A data authority and bootstrap remain required.',
        'Normal initial mode0/2 grids are supplied in source; live outdoor rotation/objects/animation, movement permission/timing/pending reset/full5D/publication remain open.',
        'CF transfer/restoration/61/map/battle paths cannot reuse normal initial snapshots; modes1/3, legacy resource/path variants remain open.',
        'Initial movement snapshot is usable only at exact unchanged initial saved position/owner revision; it is not a live WorldOwner implementation.',
        'Shared resource paths and common catalog keys do not prove TW/CN geometry equivalence; real TW enrollment, cross-version publication and Application dispatch remain unhosted.',
        'Native success/character data suppliers and every remaining TW/CN gameplay route/variant/deferred denominator remain open; new complete routes0.',
    ]
    manifest={
        'kind':'normal initial shared character/position lease -> native CN CAN/HMD or MDT/MDL/ROM/MBD -> full initial grid -> exact2A/ready gate and initial movement snapshot',
        'client_sha256':PIN,'source_paths':sources,'snapshots':snapshots,'imports':imports,
        'adaptations':adaptations,'native_spans':list(native.values()),'native_function_references':references,
        'native_unique_function_spans':len(native),'new_source_files':20,
        'source_owner_chains_added':1,'new_phase_opcode_bindings':0,'qualified_initial_geometry_modes':[0,2],
        'geometry_modes_are_not_complete_packet_variants':True,
        'source_files_are_selected_paths_not_resource_content_hashes':True,
        'normal_world_selection_requires_actual_scene_supplier':True,
        'ready_requires_same_presence_and_generation':True,'live_scene_owner_implemented':False,
        'initial_movement_snapshot_invalid_after_position_or_scene_revision_change':True,
        'formal_application_hosted':False,'new_complete_routes':0,
        'previous_goal_turn_classification':'no progress: clarification reaffirmed already persisted conversion/font separation; current turn takes next safe concrete supplier action',
        'remaining':gaps,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'asset_loaders_executed':False,
        'lua_executed':False,'deployed':False,'production_database_read_or_modified':False,
        'client_modified':False,'font_modified':False,'text_conversion_modified':False,
    }
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({
        'name':'CN normal initial scene supplier bound to common prepared character/map/ready lease',
        'status':'實際CAN／HMD及MDT／MDL／ROM／MBD初始格網已接來源；一般02／2A前需同租約場景，真正world生命周期與Application未掛載',
        'native_c2s_by_phase':{},'native_s2c_by_phase':{},
        'source_paths':sources,'source_owner_chains_added':1,'formal_application_hosted':False,
        'complete_gameplay_routes_added':0,'storage_writes':False,
        'shared_storage':['existing NativeMapCatalog identity','existing common prepared character/position lease'],
        'native_form_qualifications':{'normal_initial_geometry_modes':[0,2],'new_phase_opcode_bindings':0,
            'whole_opcode_variants_complete':False,'transfer_or_live_geometry_supplied':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps,
    })
    for segment in ledger['dual_client_source_segments']:
        if segment['name'].startswith('CN owned world selection'):
            segment['normal_initial_scene_supplier']=out.relative_to(SERVER).as_posix()
            segment['normal_scene_same_presence_generation_required']=True
        if segment['name'].startswith('CN adjacent movement'):
            segment['initial_scene_supplier']=out.relative_to(SERVER).as_posix()
            segment['actual_live_world_owner_implemented']=False
    ledger['cn_account_admission_evidence'][NAME]={
        'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()},
    }
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=[
        'Connect real live scene/window lifecycle to the imported asset readers and shared actor, with actual direction/revision/profile; recover native pending-ring/reset/timing and5D issuance.',
        'Complete owned movement publication/mixed later dispatcher and Application world routing; do not reuse initial geometry after the saved-position revision changes.',
        'Recover complete native1D/0A/07/1F/02/2A data authority and aliases, real account/world listeners and actual actor/initial placement/bootstrap/TW enrollment.',
        'Continue all TW/CN gameplay direction/state/variant/deferred accounting and connections, preserving saves/native fonts/conversion; no phase1 build/tests/runtime/deploy.',
    ]
    dump(path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),
        'native_function_references':references,'native_unique_spans':len(native),
        'new_source_files':20,'new_phase_bindings':0,'new_complete_routes':0,
        'asset_loaders_executed':False,'tests_run':False}))

if __name__=='__main__':main()
