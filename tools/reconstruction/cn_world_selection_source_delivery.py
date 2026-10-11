"""Seal conditional CN world-selection source and pinned native evidence.

Static source/evidence accounting only. No build, tests, runtime or DB writes.
"""
import hashlib
import json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT as SERVER,CN,PIN

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-world-selection-owner-01'
SOURCES=[
    'src/cn/protocol/CnCharacterEnter.h','src/cn/protocol/CnWorldSelectionStatus.h',
    'src/cn/protocol/CnWorldEntry.h','src/cn/auth/SharedWorldSelection.h',
    'src/cn/auth/SharedWorldSelection.cpp','src/cn/net/SharedCredentialConnection.h',
    'src/cn/net/SharedCredentialConnection.cpp',
]
AGENTS=['cn-world-selection-status-agent-01','cn-world-selection-credential-alias-agent-01']

def digest(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve prior immutable delivery')
    raw=(CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()
    if digest(raw)!=PIN:raise RuntimeError('CN source pin changed')
    agent_receipts=[]
    for name in AGENTS:
        directory=ROOT/name
        manifest=json.loads((directory/'delivery-manifest.json').read_text(encoding='utf-8'))
        findings=json.loads((directory/'findings.json').read_text(encoding='utf-8'))
        if findings['sha256']!=PIN:raise RuntimeError('Wrong native evidence build')
        for row in manifest['files']:
            path=(directory/row['file']).resolve()
            if not path.is_relative_to(directory.resolve()):raise RuntimeError('Invalid evidence path')
            data=path.read_bytes()
            if len(data)!=row['bytes'] or digest(data)!=row['sha256']:
                raise RuntimeError('Agent immutable delivery differs')
        agent_receipts.append({'root':directory.relative_to(SERVER).as_posix(),
            'files':len(manifest['files']),'delivery_manifest_sha256':digest((directory/'delivery-manifest.json').read_bytes()),
            'findings_sha256':digest((directory/'findings.json').read_bytes())})
    out.mkdir();saved=[]
    def save(rel,data,original):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        saved.append({'path':rel,'original':str(original),'bytes':len(data),'sha256':digest(data)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel in ['src/auth/SharedWorldAdmission.h','src/auth/SharedWorldAdmission.cpp',
                'src/db/RecoveredCharacterRepository.h','src/cn/protocol/CnAccountWire.h']:
        save('authority/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel in ['src/protocol/CnCharacterRequests.h','src/protocol/CnWorldEntry.h']:
        save('upstream/'+Path(rel).name,(CN/rel).read_bytes(),CN/rel)
    for name in AGENTS:
        for rel in ['findings.json','delivery-manifest.json']:
            save('native-evidence/'+name+'/'+rel,(ROOT/name/rel).read_bytes(),ROOT/name/rel)
    for rel in ['AGENTS.md','docs/PACKET_CONNECTION_GOAL_20261006.md',
                'artifacts/releases/native-font-restore-20261006/restoration.json']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',(ROOT/'packet-route-ledger.json').read_bytes(),ROOT/'packet-route-ledger.json')
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    gaps=[
        'Application/listener and native account/world success providers are unhosted; no runtime or complete gameplay route.',
        'Required exact125-byte1F and normal/transfer native-slot/common-ID source associations remain unimplemented. No name, ordinal or invalid-slot clamp authorizes a character.',
        'Authenticated source-qualified1A credential-alias issuer/lineage still required. No global world00-prefix equality, case folding, password-policy change or truncated-field authentication.',
        'Official second-auth/revocation/credential-revision rules remain unknown. Native1D comparisons alone do not prove those server rules.',
        'Selected must supply actual shared world actor/storage/rules, full23-byte02 and37-byte2A, actual next1C/gameplay dispatcher and close/cancel/rollback ownership; none is fabricated here.',
        'Read-only1C and61 views are not new source bindings; actor handle/map/resource semantics need current common-world qualification.',
        'Native1D/07/1F/02/2A opaque fields and authoritative issuers remain open; do not zero-fill or copy TW CUSTOM bootstrap.',
        'TW registry integration and whole-game directional/state/variant/deferred denominator remain open.',
    ]
    data={
        'kind':'conditional owned world1F/1A selection -> required real preparation -> complete supplied02 then2A',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':saved,'agent_evidence':agent_receipts,
        'source_owner_chains_added':1,'formal_application_hosted':False,'new_complete_routes':0,
        'contracts':{
            'identity':'Fullworld00 verified account + matched current shared world ticket + offered common ID + fresh RecoveredCharacterRepository ownership;1A echo cannot choose another account.',
            'credentials':'Mandatory explicit authenticated source aliases projected by native strncpy16/forcedNUL15. No aliases synthesized from request, no blanket case conversion. Wipe alias storage after selection and wipe request copies.',
            'credential_policy_limit':'Alias matching is an integration constraint with required issuer, not a recovered official second-auth contract. Transfer pre1D/UI and post1D world00 strings may differ.',
            'slot':'Explicit unique slot0..3/common-ID associations required. Client invalid-slot->0 behavior is not server account authority.',
            'reply':'Complete23-byte02(status0) followed by complete37-byte2A in one transport aggregate. Opaque bytes must be provided; early2A is discarded by47E4D0.',
            'state':'Once selected, only actual supplied next ingress handles1C/later gameplay. Single completion shared across asynchronous/catch paths; close cleanup remains scoped to current admission ticket.',
            'authority':'Same recovered_characters owner as TW; no database reads/writes or new tables by this delivery.',
        },
        'native02':'0047E4D0 consumes status LE16 and nonzero-status message-selector low7;20 other payload bytes opaque;1E code8 still returns failure in this waiter.',
        'native_transport':'0047D8D0/0047D2E0 ->0047A120 preserves decoded aggregate cursor after02 so00481190 can consume following2A. Never split one logical record across aggregates.',
        'native_aliases':'0044CF10 snapshots strings;0047FE30 accepted1D overwrites record afterstricmp;0044D5F0 world00 and0044D2401A can read different authenticated source generations; normal reconnect also has cache/UI divergence.',
        'previous_goal_turn_classification':'progress: common recovered-character ID offers bound to current world ticket; this round adds bounded conditional selection controller and corrects a non-native strict-prefix assumption before sealing.',
        'remaining':gaps,'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,
        'production_database_modified':False,'text_conversion_modified':False,'font_modified':False,
        'owner_clarification':'Traditional/Simplified and CP950/CP936 conversion retained; native font restoration remains separate.',
    }
    dump(out/'integration-manifest.json',data)
    path=ROOT/'packet-route-ledger.json';ledger=json.loads(path.read_text(encoding='utf-8'))
    ledger['dual_client_source_segments'].append({
        'name':'CN owned world selection1F/1A to required shared-world02/2A continuation',
        'status':'世界選角條件式來源已接入；需原生資料／帳密別名供應器與實際世界owner，Application未掛載，非完整路徑',
        'source_paths':SOURCES,'native_c2s_by_phase':{'world_login':['00'],'world_selection':['1A']},
        'native_s2c_by_phase':{'world_login':['1F'],'world_selection':['02','2A']},
        'formal_application_hosted':False,'source_owner_chains_added':1,
        'complete_gameplay_routes_added':0,'storage_writes':False,
        'shared_storage':['RecoveredCharacterRepository / recovered_characters; current offered-ID world ticket'],
        'remaining':gaps,'evidence':out.relative_to(SERVER).as_posix(),
    })
    for directory in [out]+[ROOT/name for name in AGENTS]:
        ledger['cn_account_admission_evidence'][directory.name]={
            'root':directory.relative_to(SERVER).as_posix(),
            'artifact_sha256':{p.relative_to(directory).as_posix():digest(p.read_bytes())
                               for p in sorted(directory.rglob('*')) if p.is_file()},
        }
    plan=ledger['dual_client_execution_plan']
    plan['latest_work_round']='20261006-cn-world-selection-owner'
    plan['next']=[
        'Recover native1F normal/transfer row-slot/common-ID and full07 projections; preserve current recovered-character owner.',
        'Provide authenticated producer-source aliases through actual account/world/transfer owners without deriving them from1A or changing password policy.',
        'Implement real common-world actor/storage/rules preparation and qualified complete02/2A data then owned1C ingress, cancellation/close/rollback.',
        'Qualify native1D and remaining success/listener authority; connect Application source without execution during phase1.',
        'Continue all TW/CN state/variant/deferred inventory and whole-game routes; retain conversion and native fonts separately.',
    ]
    dump(path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(saved),'agent_files':[r['files'] for r in agent_receipts],
        'new_partial_owner_chain':1,'new_phase_source_bindings':5,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
