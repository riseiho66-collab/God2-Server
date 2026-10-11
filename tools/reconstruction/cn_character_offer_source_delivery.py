"""Seal common-character offer wiring and native CN route fallback evidence.

Static source/native reads and evidence/ledger writes only; no tests/runtime.
"""
import csv
import hashlib
import json
from pathlib import Path
import capstone
import pefile
from .cn_wrapper_route_frontier import ROOT as SERVER,CN,RECOVERY,PIN

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-character-offer-owner-01'
SOURCES=[
    'src/auth/SharedWorldAdmission.h','src/auth/SharedWorldAdmission.cpp',
    'src/cn/auth/SharedAccountSelection.h','src/cn/auth/SharedAccountSelection.cpp',
    'src/cn/net/SharedCredentialConnection.h','src/cn/net/SharedCredentialConnection.cpp',
    'src/cn/protocol/CnCatalogRoute.h','src/cn/protocol/CnCharacterSummary.h',
]

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve prior delivery')
    raw=(CN.parent/'XJZ-CN/God2_opt.exe').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN:raise RuntimeError('CN source pin changed')
    pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
    md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
    with (RECOVERY/'functions.tsv').open(encoding='utf-8-sig') as stream:
        functions={r['address']:r for r in csv.DictReader(stream,delimiter='\t')}
    out.mkdir();saved=[]
    def save(rel,data,original):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        saved.append({'path':rel,'original':str(original),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    def snapshot(rel):save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel in SOURCES:snapshot(rel)
    for rel in ['src/db/Database.h','src/db/RecoveredCharacterRepository.h',
                'src/db/SqliteRecoveredCharacterRepository.cpp','src/db/SqliteCharacterRepository.cpp',
                'src/handlers/RecoveredCharacterService.cpp','src/game/RecoveredCharacter.h']:
        save('authority/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    application=SERVER/'src/core/Application.cpp'
    text=application.read_text(encoding='utf-8')
    save('authority/Application-character-owner.txt',('\n'.join(text.splitlines()[288:303])+'\n').encode(),
         'src/core/Application.cpp lines289..303; full SHA256='+hashlib.sha256(application.read_bytes()).hexdigest())
    native=[]
    for address in ['0047faa0','0047d1c0','0047c830']:
        row=functions[address];source=RECOVERY/row['file'];va=int(address,16)
        code=pe.get_data(va-base,int(row['bytes']))
        save('native/'+address+'.c',source.read_bytes(),source)
        save('native/'+address+'.bin',code,'God2_opt.exe VA '+address)
        save('native/'+address+'.asm',('\n'.join(
            f'{i.address:08x} {i.bytes.hex():24} {i.mnemonic:8} {i.op_str}' for i in md.disasm(code,va))+'\n').encode(),
            'God2_opt.exe VA '+address)
        native.append({'va':address,'bytes':len(code),'sha256':hashlib.sha256(code).hexdigest()})
    for rel in ['cn-account-selection-owner-01/integration-manifest.json',
                'shared-world-admission-owner-01/integration-manifest.json',
                'cn-summary-opaque-agent-01/findings.json']:
        save('prior-evidence/'+rel.replace('/','-'),(ROOT/rel).read_bytes(),ROOT/rel)
    save('prior-ledger.json',(ROOT/'packet-route-ledger.json').read_bytes(),ROOT/'packet-route-ledger.json')
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    gaps=[
        'Native07 complete owner-qualified data supplier and same common-ID/native-row association still missing; no TW40-byte profile copied as CN36-byte row.',
        'RecoveredCharacter IDs are shared with existing TW gameplay; its profile/raw codepage/CUSTOM state do not by themselves prove CN native fields/rules.',
        'The world_character_offered API is a scoped query for the pending world-selection controller, not an installed1A handler or active character.',
        'Entry must recheck current repository ownership/revision; an old offer alone cannot authorize deleted/transferred characters.',
        'Native1D/0A success fields, issuer and Application listener/success ownership remain unhosted.',
        'World1F row/slot/common-ID mapping,1A/02/2A/1C transitions and create/delete/transfer rules remain incomplete.',
        'Flags bit0 client UI effects do not establish authoritative server issuance; row18 business meaning remains open.',
        'Whole-game directional/state/variant denominator, TW adapter registry hosting and all later gameplay remain open.',
    ]
    data={
        'kind':'shared recovered-character offers + owned world-ticket scope + native catalog fallback',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':saved,'native_functions':native,
        'corrected_prior_source':{
            'prior':'cn-account-selection-owner-01 used CharacterRepository.find_by_id -> independent skeleton characters table',
            'current':'SharedAccountSelection uses RecoveredCharacterRepository.list_for_account, same owner instantiated by Application and used by TW gameplay',
            'no_alias_or_migration':'No name/slot/numeric-ID join between characters and recovered_characters; no DB reads/writes performed by this delivery',
            'historical_receipts_preserved':True,
        },
        'new_source_scope':{
            'owner_chains_added':1,
            'offer':'Qualified07 common IDs copied into this grant generation at select; duplicates/zero refused, empty list authorizes no character',
            'world_query':'Committed current world-session/reservation ticket required; account close retains selected handoff; world release invalidates query',
            'protocol_boundary':'Only common IDs in core; native slots/route keys remain in CN adapter; no activation or guessed reply',
        },
        'native_fallback':{
            'call_chain':'0047FAA0 calls0047D1C0; on null explicitly calls0047C830',
            'choice':'Exact nonzero route-key match within selected group/server; otherwise first node/location with nonzero key, preserving group-wide05 ordinals',
            'source_change':'CnCatalogRoute.resolve replaces match-only rejection in07 source qualification',
            'no_location_fabrication':True,
        },
        'previous_goal_turn_classification':'progress: saved selection controller and CF selector evidence; current turn corrects its repository and extends owned common-ID scope',
        'remaining':gaps,'new_complete_routes':0,'formal_application_hosted':False,
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,
        'production_database_modified':False,'text_conversion_modified':False,'font_modified':False,
    }
    def dump(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    dump(out/'integration-manifest.json',data)
    path=ROOT/'packet-route-ledger.json';ledger=json.loads(path.read_text(encoding='utf-8'))
    previous=ledger['dual_client_source_segments'][-1]
    previous['shared_storage']=['RecoveredCharacterRepository / recovered_characters; same IDs as current TW gameplay']
    previous['status']='選服來源已改接實際TW角色owner；共用角色offer綁grant世代，原生資料供應器及Application仍未掛載'
    previous['source_paths']=sorted(set(previous['source_paths']+SOURCES))
    previous['correction_evidence']=out.relative_to(SERVER).as_posix()
    previous['remaining']=gaps
    ledger['dual_client_source_segments'].append({
        'name':'CN selected common-character offers scoped to owned world ticket',
        'status':'共用角色ID offer與世界ticket查詢來源已接入；尚無1A handler／原生成功回覆，非完整世界入口',
        'source_paths':SOURCES,'native_c2s_by_phase':{'account':['A6'],'world_login':['00']},
        'native_s2c_by_phase':{'account':['07']},'formal_application_hosted':False,
        'source_owner_chains_added':1,'complete_gameplay_routes_added':0,'storage_writes':False,
        'shared_storage':['RecoveredCharacterRepository / recovered_characters; grant holds common IDs only'],
        'remaining':gaps,'evidence':out.relative_to(SERVER).as_posix(),
    })
    for directory in [out,ROOT/'cn-summary-opaque-agent-01']:
        ledger['cn_account_admission_evidence'][directory.name]={
            'root':directory.relative_to(SERVER).as_posix(),
            'artifact_sha256':{p.relative_to(directory).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(directory.rglob('*')) if p.is_file()},
        }
    ledger['dual_client_execution_plan']['latest_work_round']='20261006-cn-character-offer-owner'
    ledger['dual_client_execution_plan']['next']=[
        'Recover native07 owner-qualified projections and flags/row18 issuer; preserve actual recovered-character IDs and no guessed fields.',
        'Connect world1F/1A/02 source controller with fresh repository ownership, offered-ID ticket scope and qualified native slot/row association.',
        'Continue native1D/0A authority and source-success/listener ownership in Application; no activation until full first-phase source completion.',
        'Complete TW/CN whole-game state/variant/deferred inventory and gameplay routes; preserve saves/conversion/native fonts.',
    ]
    dump(path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(saved),'new_partial_owner_chain':1,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
