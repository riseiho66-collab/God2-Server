"""Seal imported CN native movement and its shared position mutation source."""
import hashlib
import json
import re
from pathlib import Path
import pefile
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN,PIN

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-shared-movement-owner-01'
ROUND='20261006-cn-shared-movement-owner'
SOURCES=[
    'src/cn/protocol/CnMovement.h','src/cn/world/CnMapPassability.h','src/cn/world/CnMapPassability.cpp',
    'src/cn/scripting/CnMovementRules.h','src/cn/scripting/CnMovementRules.cpp','scripts/cn/native_movement.lua',
    'src/cn/world/SharedMovement.h','src/cn/world/SharedMovement.cpp',
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'docs/research/cn-shared-movement-owner-20261006.md',
]
EVIDENCE=[('20261006-cn-movement-01','movement-evidence.json'),
          ('20261006-cn-map-passability-01','map-passability-evidence.json')]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    out=ROOT/NAME
    if (out/'integration-manifest.json').exists():raise RuntimeError('Preserve sealed delivery')
    imports=json.loads((out/'import-receipt.json').read_text(encoding='utf8'))
    for row in imports:
        if sha((out/row['snapshot']).read_bytes())!=row['source_sha256'] or sha((SERVER/row['target']).read_bytes())!=row['target_sha256']:
            raise ValueError('Imported source differs')
    exe=CN.parent/'XJZ-CN/God2_opt.exe';raw=exe.read_bytes()
    if sha(raw)!=PIN:raise ValueError('CN native pin changed')
    pe=pefile.PE(data=raw,fast_load=True)
    native=[];pending=[]
    for name,filename in EVIDENCE:
        directory=CN/'artifacts/native'/name
        evidence=json.loads((directory/filename).read_text(encoding='utf8'))
        if evidence['client_sha256']!=PIN:raise ValueError('Native evidence pin changed')
        pending.append(('native/'+name+'/'+filename,(directory/filename).read_bytes(),directory/filename))
        for row in evidence['functions']:
            address=row['va'];p=Path(row['source']);source=p.read_bytes()
            if sha(source)!=row['source_sha256']:raise ValueError('Native C changed')
            legacy_path=directory/(address+'.c');legacy=legacy_path.read_bytes()
            if source.replace(b'\r\n',b'\n')!=legacy.replace(b'\r\n',b'\n'):
                raise ValueError('Legacy native snapshot content differs beyond line endings')
            match=re.search(rb'Size: (\d+) bytes',source)
            if not match:raise ValueError('Native extent unavailable')
            size=int(match.group(1));code=pe.get_data(int(address,16)-pe.OPTIONAL_HEADER.ImageBase,size)
            if len(code)!=size or sha(code)!=row['code_sha256']:raise ValueError('Native PE extent changed')
            for extension,data,original in [('.c',source,p),('.asm',(directory/(address+'.asm')).read_bytes(),directory/(address+'.asm')),('.bin',code,exe)]:
                pending.append(('native/'+name+'/'+address+extension,data,original))
            native.append({'evidence':name,'address':address,'bytes':size,'native_sha256':sha(code),'source_sha256':sha(source)})
            native[-1].update({'legacy_snapshot_sha256':sha(legacy),'legacy_line_endings_differ':source!=legacy,'old_manifest_preserved':True})
    path=ROOT/'packet-route-ledger.json';prior=path.read_bytes();ledger=json.loads(prior.decode('utf8'));snapshots=[]
    def save(rel,data,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as file:file.write(data)
        snapshots.append({'path':rel,'bytes':len(data),'sha256':sha(data),'original':str(original)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel,data,original in pending:save(rel,data,original)
    save('prior-ledger.json',prior,path)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    gaps=[
        'Actual native WorldOwner scene asset/lifecycle/permission/timing/sequence/reset/full5D supplier and cross-version movement publication are required, not defaulted.',
        'Only ordinary adjacent mode0/2 steps are connected conditionally; collision/path/portal/map/battle/duplicate/out-of-order variants remain open.',
        'Mixed aggregate/later gameplay dispatcher and Application routing remain unhosted; TW movement does not yet share this registry.',
        'Common persisted position CAS does not prove common geometry or authorize a client destination; the required scene/permission owner supplies those prerequisites.',
        'Native login/character/full bootstrap suppliers and all remaining TW/CN gameplay remain open.',
        'Whole-game direction/state/variant/deferred denominator, complete routes and native acceptance remain unknown/uncompleted.',
    ]
    manifest={
        'kind':'CN native adjacent2E/Lua/cells -> required real world authority -> common saved-position CAS -> publication -> required complete5D',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':snapshots,'imports':imports,'native_spans':native,
        'new_source_files':8,'source_owner_chains_added':1,'new_phase_opcode_bindings':2,
        'qualified_geometry_modes':[0,2],'geometry_modes_are_not_full_packet_variants':True,
        'shared_mutation_path':'SharedWorldPresence.commit_owned_step -> RecoveredCharacterRepository.commit_position -> existing recovered_positions ownership/revision CAS',
        'reply':'complete5D supplied by required real authority; no ring-index echo/defaultbyte',
        'failure':'close/release owned lease; preserve already committed authorized steps for actual reentry recovery',
        'native_world_owner_implemented':False,'formal_application_hosted':False,'new_complete_routes':0,
        'previous_goal_turn_classification':'progress: conditional account success/shared grant and connection-owned0A source sealed; count correction preserved',
        'remaining':gaps,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'lua_executed':False,'deployed':False,
        'production_database_read_or_modified':False,'client_modified':False,'font_modified':False,'text_conversion_modified':False,
    }
    dump(out/'integration-manifest.json',manifest)
    ledger['dual_client_source_segments'].append({
        'name':'CN adjacent movement2E/native Lua/cells to common owned-position CAS and supplied5D',
        'status':'原生單步幾何／Lua與共用位置CAS已接条件式來源；真正world permission／資料／廣播及Application未掛載',
        'native_c2s_by_phase':{'world_movement':['2E']},'native_s2c_by_phase':{'world_movement':['5D']},
        'source_paths':SOURCES,'source_owner_chains_added':1,'formal_application_hosted':False,
        'complete_gameplay_routes_added':0,'storage_writes':False,
        'source_mutation_paths':['actual recovered_positions ownership/revision CAS after required real authority'],
        'shared_storage':['RecoveredCharacterRepository / recovered_characters / recovered_positions','same current world ticket/presence lease'],
        'native_form_qualifications':{'ordinary_adjacent_step':True,'geometry_modes':[0,2],'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps,
    })
    ledger['cn_account_admission_evidence'][NAME]={
        'root':out.relative_to(SERVER).as_posix(),
        'artifact_sha256':{p.relative_to(out).as_posix():sha(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()},
    }
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=[
        'Implement actual native scene asset/window lifecycle/timing/pending ring/reset owner and qualified5D issuance, then connect movement publication and Application dispatcher.',
        'Recover native1D/0A/07/1F/02/2A data authority and authenticated aliases; compose actual shared account/world listeners without fake providers.',
        'Complete common actor/initial placement/TW registry enrollment, bootstrap/control and later scene/map/battle/gameplay transitions.',
        'Continue full TW/CN phase/state/variant/deferred/world/content accounting and all gameplay; no phase1 build/tests/runtime/deploy, preserve conversion/native fonts/saves.',
    ]
    dump(path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'native_function_spans':len(native),
        'new_source_files':8,'new_phase_bindings':2,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
