"""Seal initial-ready source and pinned native deliveries; static accounting only."""
import hashlib
import json
from pathlib import Path
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import PIN

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-world-ready-owner-01'
ROUND='20261006-cn-world-ready-owner'
SOURCES=[
    'src/game/SharedWorldPresence.h','src/game/SharedWorldPresence.cpp',
    'src/cn/world/SharedWorldReady.h','src/cn/world/SharedWorldReady.cpp',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/auth/SharedWorldSelection.h','src/cn/auth/SharedWorldSelection.cpp',
    'src/cn/protocol/CnWorldEntry.h',
    'docs/research/cn-world-ready-owner-20261006.md',
]
AGENTS=['cn-ready-bootstrap-order-agent-01','cn-character-create-fields-agent-01']

def digest(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve immutable previous delivery')
    receipts=[]
    for name in AGENTS:
        directory=ROOT/name
        manifest=json.loads((directory/'delivery-manifest.json').read_text(encoding='utf8'))
        findings=json.loads((directory/'findings.json').read_text(encoding='utf8'))
        if findings.get('exe_sha256',findings.get('native_sha256'))!=PIN:
            raise ValueError('Wrong native build in evidence')
        for item in manifest['files']:
            rel=item.get('file',item.get('path'));p=(directory/rel).resolve()
            if not p.is_relative_to(directory.resolve()) or digest(p.read_bytes())!=item['sha256']:
                raise ValueError('Immutable agent evidence differs')
        receipts.append({'root':directory.relative_to(SERVER).as_posix(),
            'files':len(manifest['files']),'manifest_sha256':digest((directory/'delivery-manifest.json').read_bytes())})
    prior=(ROOT/'packet-route-ledger.json').read_bytes();ledger=json.loads(prior.decode('utf8'))
    out.mkdir();snapshots=[]
    def save(rel,raw,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        snapshots.append({'path':rel,'original':str(original),'bytes':len(raw),'sha256':digest(raw)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',prior,ROOT/'packet-route-ledger.json')
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    for name in AGENTS:
        for rel in ['findings.json','delivery-manifest.json']:
            p=ROOT/name/rel;save('native-evidence/'+name+'/'+rel,p.read_bytes(),p)
    p=ROOT/AGENTS[0]/'worker-control-contract.json'
    save('native-evidence/worker-control-contract.json',p.read_bytes(),p)
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    gaps=[
        'Application listeners/real success controllers and TW enrollment in the same common presence registry remain unhosted. No mixed-client world exclusion claimed.',
        'Real scene owner must reserve actor handle and establish native-qualified persisted first placement/geometry/scene mode; no fallback spawn or DB-ID truncation.',
        'Full native07/1F/02/2A and1D/0A suppliers, same-grant row/alias lineage and invalid-slot variants remain open.',
        'Required bootstrap/control1F/23/30/36 handlers and world publication/gameplay dispatcher still need actual authority/data; no fabricated same-opcode replies.',
        'Initial normal/CF ordering does not qualify later scene restoration/map-change1C.22 phase and additional independent initial controls remain open.',
        'Ordinary17 and special1B lifecycle must remain distinct;07 row18 and full portrait/appearance issuance cannot be inferred from local preview.',
        'Whole-game TW/CN phase/state/variant/deferred denominator and all remaining gameplay remain open.',
    ]
    data={
        'kind':'initial CN ready FSM connected to actual common stored-position lease and transport cleanup',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':snapshots,'agent_evidence':receipts,
        'new_source_files':4,'source_owner_chains_added':1,'new_phase_opcode_bindings':5,
        'native_initial_forms':2,'initial_order':['1F00','2300','1C(handleLE16,0000)'],
        'aggregate_contract':'complete records in relative order; multiple records or split across aggregates;30/36 may interleave',
        'readiness_authority':'verified account/current committed world session/offered common ID/exact presence lease/stored-position revision/native2A handle',
        'lifecycle':'generation-qualified close/failure release captured by transport even if wrapper expires',
        'storage':'existing common recovered_characters/recovered_positions via RecoveredCharacterRepository; no writes/new tables',
        'native_new_findings':['17 creation versus1B special lifecycle','2A payload7->actorFC->1B UI four-option disable mask'],
        'previous_goal_turn_classification':'progress: native scene identity and normal/transfer projection source',
        'immediately_preceding_font_clarification_turn':'no packet-goal progress; source already retained conversion. This round takes the next safe action and implements actual initial-ready state/lease source.',
        'formal_application_hosted':False,'tw_enrolled_in_common_presence':False,'new_complete_routes':0,
        'remaining':gaps,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,
        'production_database_read_or_modified':False,'text_conversion_modified':False,'font_modified':False,'client_modified':False,
    }
    dump(out/'integration-manifest.json',data)
    ledger['dual_client_source_segments'].append({
        'name':'CN initial1F/23/1C plus interleaved30/36 to common character-position readiness lease',
        'status':'初始就緒狀態／真實角色與存檔revision／世代清理已接來源；實際資料處理與Application仍未掛載',
        'native_c2s_by_phase':{'world_initial_bootstrap':['1F','23','1C','30','36']},
        'native_s2c_by_phase':{},'source_paths':SOURCES,'source_owner_chains_added':1,
        'formal_application_hosted':False,'complete_gameplay_routes_added':0,'storage_writes':False,
        'shared_storage':['RecoveredCharacterRepository / recovered_characters / recovered_positions','shared serial world presence leases'],
        'native_form_qualifications':{'initial_normal_transfer_forms':2,'later_scene_ready_not_qualified':True,'whole_opcode_variants_complete':False},
        'evidence':out.relative_to(SERVER).as_posix(),'remaining':gaps,
    })
    selection=ledger['dual_client_source_segments'][-2]
    selection['ready_owner_evidence']=out.relative_to(SERVER).as_posix()
    selection['status']='原生共用地圖lookup及02/2A→同連線共用存檔lease→初始ready owner已接條件式來源；資料供應與Application仍缺'
    selection['remaining']=gaps
    for directory in [out]+[ROOT/name for name in AGENTS]:
        ledger['cn_account_admission_evidence'][directory.name]={
            'root':directory.relative_to(SERVER).as_posix(),
            'artifact_sha256':{p.relative_to(directory).as_posix():digest(p.read_bytes())
                for p in sorted(directory.rglob('*')) if p.is_file()},
        }
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']=ROUND
    plan['next']=[
        'Recover native07/1F/02/2A full suppliers and same-grant common-ID/alias lineage; use17 versus1B evidence without copied preview templates.',
        'Connect real shared actor allocator, qualified initial placement, bootstrap/control authority, world publication and later dispatcher to the new common lease/ready source; enroll TW in the same owner.',
        'Qualify native1D/0A success and integrate actual Application account/world listeners/success controllers in source.',
        'Implement later scene/map readiness independently from initial bootstrap; trace22 phase and36 payload/response authority.',
        'Continue all TW/CN phases/variants/deferred/gameplay; retain saves/conversion/native fonts; no build/tests/runtime/deploy in phase1.',
    ]
    dump(ROOT/'packet-route-ledger.json',ledger)
    print(json.dumps({'artifact':str(out),'snapshots':len(snapshots),'new_source_files':4,
        'agent_evidence_files':sum(r['files'] for r in receipts),'new_phase_bindings':5,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
