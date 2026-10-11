"""Save immutable source/native provenance for CN account-selection work.

Static reads/hashes and evidence/ledger writes only. No builds, clients, tests,
database access, server restart or native execution.
"""
import hashlib
import json
from pathlib import Path
from .archive_inputs import SERVER
from .cn_wrapper_route_frontier import CN

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-account-selection-owner-01'
SOURCES=[
    'src/cn/auth/SharedAccountSelection.h',
    'src/cn/auth/SharedAccountSelection.cpp',
    'src/cn/protocol/CnCharacterSummary.h',
    'src/cn/protocol/CnAccountWire.h',
    'src/cn/net/SharedCredentialConnection.h',
    'src/cn/net/SharedCredentialConnection.cpp',
]

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve prior source delivery')
    out.mkdir()
    snapshots=[]
    def snapshot(path,relative):
        raw=path.read_bytes()
        dest=out/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(raw)
        snapshots.append({'original':str(path),'snapshot':relative,
                          'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    for rel in SOURCES:snapshot(SERVER/rel,rel)
    snapshot(CN/'src/protocol/CnCharacterSummary.h','upstream/CnCharacterSummary.h')
    native=CN/'artifacts/native'
    for stem in ['00443080','00443640']:
        for suffix in ['c','asm']:
            snapshot(native/'20261006-cn-character-summary-01'/f'{stem}.{suffix}',f'native/{stem}.{suffix}')
    for stem in ['00481640','0047d1c0']:
        for suffix in ['c','asm']:
            snapshot(native/'20261006-cn-selection-consumers-01'/f'{stem}.{suffix}',f'native/{stem}.{suffix}')
    snapshot(native/'20261006-cn-selection-consumers-01/selection-consumer-evidence.json',
             'native/selection-consumer-evidence.json')
    for suffix in ['c','asm']:
        snapshot(ROOT/'cn-billing-byte5-agent-01'/f'00443fa0.{suffix}',f'native/00443fa0.{suffix}')
    snapshot(ROOT/'cn-account-tail-agent-01/findings.json','native/cn-account-tail-findings.json')
    snapshot(ROOT/'cn-account-tail-agent-01/0044d5f0.asm','native/0044d5f0.asm')
    snapshot(ROOT/'packet-route-ledger.json','prior-ledger.json')
    snapshot(Path(__file__),'delivery-tool.py')
    gaps=[
        'Native07 SummarySource supplying complete flags/opaque/inactive fields and authoritative common-ID row association is not implemented/hosted.',
        'Shared Character CUSTOM-0003 fields cannot qualify a native07 projection; name CP936 projection and version-resource appearance mappings remain open.',
        'Native1D tailA8..CB and billing0A byte5/value authority, issuer/online account policy remain open.',
        'Application listeners/account-success owner are not wired; no selected character/world1F or gameplay activation is implied.',
        'C2S0A disconnect and other Account requests are not handled by this boundedA6 controller; transport close cleanup exists separately.',
        'CF initiation/extra bytesCD..CF, destination authorization and handoff revocation/renewal remain open.',
        'TW adapter shared-grant integration and whole-game directional/state/variant denominator remain open.',
    ]
    manifest={
        'kind':'CN owned AccountA6/shared-grant/conditional-native07 source controller',
        'client_sha256':'582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8',
        'source_paths':SOURCES,'snapshots':snapshots,
        'native_chain':{
            'request':'00481640 emits distinct u8 group/server asA6, then waits07/1E',
            'summary':'07 is75 logical bytes; active rows<=2, stride36; flags/byte18 remain opaque',
            'route':'0047D1C0 searches only selected group/server; row routingkey matches nonzero06 payload0',
            'enabled':'00443FA0 checks server bit in group enable word; actual slot count is configured client data',
            'transfer':'CF payloadCC selector outside204-byte record matches07 low3 slot, rather than direct ordinal',
        },
        'source_increment':{
            'owner_chains_added':1,
            'chain':'A6 aggregate parser -> owned verified-account grant -> catalog bounds/enable/endpoint -> shared CharacterRepository ownership -> required complete native07 supplier -> SharedWorldAdmission.select -> same connection send',
            'native_slot_lookup':'row_for_native_slot returns absent on unmatched/out-of-range; no default0',
            'no_fabricated_data':'flags,opaque bytes and inactive rows preserved verbatim from required server-owned source, never zero-filled',
            'storage':'CharacterRepository.find_by_id read only; common account/character IDs, no new tables or CN DB import',
        },
        'remaining':gaps,'new_complete_routes':0,'formal_application_hosted':False,
        'native_summary_supplier_implemented':False,
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,
        'production_database_modified':False,'text_conversion_modified':False,'font_modified':False,
        'previous_goal_turn_classification':'font-scope confirmation did not advance packet objective; this round adds concrete source and native alias evidence',
    }
    def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    dump(out/'integration-manifest.json',manifest)
    ledger_path=ROOT/'packet-route-ledger.json'
    ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
    ledger['dual_client_source_segments'].append({
        'name':'CN ownedA6 selection to shared character ownership and conditional native07',
        'status':'選服授權與角色歸屬控制器來源已加入；原生07資料供應器及Application未掛載，非完整登入路徑',
        'source_paths':SOURCES,
        'native_c2s_by_phase':{'account':['A6']},
        'native_s2c_by_phase':{'account':['07']},
        'source_owner_chains_added':1,'shared_storage':['CharacterRepository shared character/account IDs'],
        'storage_writes':False,'formal_application_hosted':False,'native_summary_supplier_implemented':False,
        'complete_gameplay_routes_added':0,'remaining':gaps,
        'evidence':(out.relative_to(SERVER)).as_posix(),
    })
    def evidence(directory):
        return {'root':directory.relative_to(SERVER).as_posix(),
                'artifact_sha256':{p.relative_to(directory).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in sorted(directory.rglob('*')) if p.is_file()}}
    ledger['cn_account_admission_evidence'][NAME]=evidence(out)
    ledger['cn_account_admission_evidence']['cn-account-tail-agent-01']=evidence(ROOT/'cn-account-tail-agent-01')
    plan=ledger['dual_client_execution_plan']
    plan['latest_work_round']='20261006-cn-account-selection-owner'
    plan['next']=[
        'Recover native07 authoritative common-ID projection/snapshot source, complete flags/byte18/appearance/location provenance without skeleton defaults.',
        'Continue1D A8..CB and billing0A full authority; trace outside bounded UI direct displacement range/computed aliases.',
        'Integrate native account-success issuer andApplication ownership/listeners after full success data qualification.',
        'Connect1F/1A character admission andCF handoff selector to same shared owner; preserve TW frozen routes and conversion/native fonts.',
    ]
    dump(ledger_path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(snapshots),'owner_chains_added':1,
                      'new_complete_routes':0,'tests_run':False},ensure_ascii=False))

if __name__=='__main__':main()
