"""Seal native source qualifications for world selection and shared scene entry.

Static evidence/source accounting only, with no build/test/runtime/production DB.
"""
import hashlib
import json
from pathlib import Path
from tools.strike_lab.omega_assets import decode_csvz
from .cn_wrapper_route_frontier import ROOT as SERVER,CN,PIN
from .shared_scene_identity_delivery import section

ROOT=SERVER/'artifacts/integration/packet-connections-20261006'
NAME='cn-world-entry-projections-01'
SOURCES=[
    'src/cn/auth/SharedWorldSelection.h','src/cn/auth/SharedWorldSelection.cpp',
    'src/cn/protocol/CnWorldEntry.h','src/cn/protocol/CnWorldCharacterList.h',
    'src/cn/world/SharedSceneIdentity.h','src/cn/world/SharedSceneIdentity.inc',
    'src/cn/world/SharedSceneRows.inc',
]
AGENTS=['cn-world-list-consumers-agent-01','cn-beginplay-fields-agent-01']

def digest(raw):return hashlib.sha256(raw).hexdigest()
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    out=ROOT/NAME
    if out.exists():raise RuntimeError('Preserve immutable previous delivery')
    if digest((CN.parent/'XJZ-CN/God2_opt.exe').read_bytes())!=PIN:raise ValueError('CN pin changed')
    agent_receipts=[]
    for name in AGENTS:
        directory=ROOT/name
        manifest=json.loads((directory/'delivery-manifest.json').read_text(encoding='utf-8'))
        findings=json.loads((directory/'findings.json').read_text(encoding='utf-8'))
        if findings.get('exe_sha256',findings.get('native_sha256'))!=PIN:raise ValueError('Wrong native evidence build')
        entries=manifest.get('source_hashes')
        if entries is None:entries={r['file']:r['sha256'] for r in manifest['files']}
        for name,sha in entries.items():
            path=(directory/name).resolve()
            if not path.is_relative_to(directory.resolve()) or digest(path.read_bytes())!=sha:
                raise ValueError('Agent immutable evidence differs')
        agent_receipts.append({'root':directory.relative_to(SERVER).as_posix(),'files':len(entries),
            'manifest_sha256':digest((directory/'delivery-manifest.json').read_bytes())})
    maproot=ROOT/'shared-scene-identity-01'
    map_manifest=json.loads((maproot/'integration-manifest.json').read_text(encoding='utf-8'))
    for entry in map_manifest['snapshots']:
        path=(maproot/entry['path']).resolve()
        if not path.is_relative_to(maproot.resolve()) or digest(path.read_bytes())!=entry['sha256']:
            raise ValueError('Native map delivery differs')
    baseline=json.loads((maproot/'joined-scenes.json').read_text(encoding='utf-8'))
    native_raw_rows=(maproot/'native-tw/Map_City_Coordniate.csv.native-bytes').read_bytes().splitlines()[1:]
    rows_source='// Exact TW native SQL raw_record bytes, keyed by144-row source ordinal.\n// Generated from shared-scene-identity-01; byte equality avoids metadata-only provenance.\n'
    rows_source+=''.join('"'+''.join('\\x%02x'%b for b in data)+'",\n' for data in native_raw_rows)
    if (SERVER/'src/cn/world/SharedSceneRows.inc').read_text(encoding='ascii')!=rows_source:
        raise ValueError('Generated source differs from its exact native record witness')
    tw_installed=SERVER.parent/'God2/Data2/Patch/Comm/gamedata.csvZ'
    if tw_installed.stat().st_size>4*1024*1024:raise ValueError('Installed native subset extraction bound')
    encoded=tw_installed.read_bytes();plain=decode_csvz(encoded,limit=8*1024*1024)
    installed_section,installed_rows=section(plain)
    differences=[r['ordinal'] for r,b in zip(installed_rows,baseline,strict=True) if r['row_sha256']!=b['tw_row_sha256']]
    if differences:raise ValueError('Installed TW map subset changed; preserve the original baseline')
    out.mkdir();saved=[]
    def save(rel,data,original):
        path=out/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        saved.append({'path':rel,'original':str(original),'bytes':len(data),'sha256':digest(data)})
    for rel in SOURCES:save(rel,(SERVER/rel).read_bytes(),SERVER/rel)
    for rel in ['src/db/NativeMapCatalog.h','src/db/NativeMapCatalog.cpp','src/db/Database.h',
                'src/game/RecoveredPosition.h','tools/strike_lab/import_native_catalog.py']:
        save('authority/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    for name in AGENTS:
        for rel in ['findings.json','delivery-manifest.json']:
            save('native-evidence/'+name+'/'+rel,(ROOT/name/rel).read_bytes(),ROOT/name/rel)
    save('native-evidence/shared-scene-identity-manifest.json',(maproot/'integration-manifest.json').read_bytes(),maproot/'integration-manifest.json')
    save('native-evidence/installed-tw-map-subset.native-bytes',installed_section,tw_installed)
    installed_receipt={'source':str(tw_installed),'whole_resource_sha256':digest(encoded),'decoded_sha256':digest(plain),
        'map_subset_sha256':digest(installed_section),'matching_original_native_rows':len(installed_rows),
        'old_native_resource_sha256':map_manifest['tw_resource_sha256'],'old_baseline_updated':False,'installed_file_modified':False}
    dump(out/'installed-tw-map-subset.json',installed_receipt)
    for rel in ['docs/PACKET_CONNECTION_GOAL_20261006.md','AGENTS.md']:
        save('directives/'+Path(rel).name,(SERVER/rel).read_bytes(),SERVER/rel)
    save('prior-ledger.json',(ROOT/'packet-route-ledger.json').read_bytes(),ROOT/'packet-route-ledger.json')
    save('delivery-tool.py',Path(__file__).read_bytes(),__file__)
    gaps=[
        'Application/listener/native success issuers remain unhosted; no complete gameplay route.',
        'Actual07/1F data supplier must preserve this grant native-row/common-ID associations, including CF retained selector/index lineage. Factory qualifies wire choices but cannot invent that authority.',
        'Native choices with raw advertised slot>=4 are left open; no permission inferred from native clamp-to0. Duplicate projected choices remain ambiguous.',
        'Mandatory authenticated credential aliases/official second-auth or revision/revocation policy still require authoritative source.',
        'Actual shared actor preparation, placement/scene mode, rollback/close and ready1C/later dispatcher must be supplied by real world owner.',
        'Native02/2A full data/opaque values remain required; no guessed zero template, copied TW CUSTOM bootstrap or synthesized native rule.',
        'CF applies2A handle/map only; readiness bootstrap requests1F/23 and retained appearance/workspace rules remain open. Normal renderer fields are not CF reinitialization.',
        'Catalogue identity proves common scene keys/path/category for144 rows, not common geometry/collision/asset versions or spawn authority.',
        'TW integration and whole-game phases/variants/deferred denominator remain open.',
    ]
    data={
        'kind':'native normal/transfer selection projection + real shared-map repository qualification +2A read-only fields',
        'client_sha256':PIN,'source_paths':SOURCES,'snapshots':saved,'agent_evidence':agent_receipts,
        'new_source_scope':{
            'owner_chains_added':0,'new_phase_opcode_bindings':0,
            'selection_paths_qualified':2,
            'normal':'07 low3 slot; complete1F is receive barrier only. No1F names/count used.',
            'transfer':'07 retained ordinal -> fresh1F payload38+40*i slot; explicit common-row IDs/data source required; never assert07slot==1Fslot.',
            'common_map_owner':'SharedWorldSelection reads actual NativeMapCatalog.lookup(current_dataset_id,position.area,position.scene); validates all originalSQL row bytes, source/hash/ordinal and shared keys against native join before queueing02/2A.',
            'positions':'Normal raw2A coords matched to reserved shared position. Transfer requires previous owner position; only same-map+bit16 follows48EF40 clear rule. No client coordinates authorize movement.',
            'no_new_tables':'Existing recovered_characters/native_map_catalog used; no CN database import or _tw/_cn split needed for this144-row identity.',
        },
        'native2a_field_segments_in_evidence':20,'native2a_field_table_is_not_packet_variant_count':True,
        'native2a_fields':'Resource/render/direction/mount/appearance inputs exposed read-only; context-dependent resolution and old actor metadata retained as requirements.8..11/20..23/26..27 anddword0 bits26..30 stayopaque.',
        'shared_scene_identities':144,'installed_tw_map_subset':installed_receipt,
        'previous_goal_turn_classification':'progress: sealed conditional world selection and60+39 native evidence files; this round qualifies actual normal/transfer data flow and ties entry to common native map repository.',
        'remaining':gaps,'formal_application_hosted':False,'new_complete_routes':0,
        'whole_game_route_total':None,'whole_game_completion_percent':None,
        'build_run':False,'tests_run':False,'runtime_run':False,'deployed':False,'production_database_read_or_modified':False,
        'archive_metadata_readonly':True,'text_conversion_modified':False,'font_modified':False,'client_modified':False,
    }
    dump(out/'integration-manifest.json',data)
    path=ROOT/'packet-route-ledger.json';ledger=json.loads(path.read_text(encoding='utf-8'))
    previous=ledger['dual_client_source_segments'][-1]
    previous['source_paths']=sorted(set(previous['source_paths']+SOURCES))
    previous['status']='一般／轉服選角與原生共用地圖lookup已接入条件式來源；完整原生資料及世界owner／Application掛載仍缺'
    previous['shared_storage']=['RecoveredCharacterRepository / recovered_characters','NativeMapCatalog / native_map_catalog / current-map-catalog-v1','owned offered-ID world ticket']
    previous['remaining']=gaps;previous['projection_evidence']=out.relative_to(SERVER).as_posix()
    previous['native_form_qualifications']={'normal_transfer_paths':2,'shared_scene_identities':144,'whole_opcode_variants_complete':False}
    for directory in [out,maproot]+[ROOT/name for name in AGENTS]:
        ledger['cn_account_admission_evidence'][directory.name]={
            'root':directory.relative_to(SERVER).as_posix(),
            'artifact_sha256':{p.relative_to(directory).as_posix():digest(p.read_bytes())
                for p in sorted(directory.rglob('*')) if p.is_file()},
        }
    plan=ledger['dual_client_execution_plan'];plan['latest_work_round']='20261006-cn-world-entry-projections'
    plan['next']=[
        'Recover actual07/1F value suppliers and identity/alias lineage from the selected grant; retain normal/CF selection difference and out-of-range slot variants.',
        'Implement authoritative world actor/session handle, original placements/native scene mode, exact02/2A values and current stored-position revision ownership; use real sharedmap lookup already connected in conditional source.',
        'Connect native1C readiness and normal/CF bootstrap1F/23, cancellation/close/rollback with actual world owner; do not count raw views as gameplay.',
        'Qualify native1D/0A success authority and integrate actual Application listeners/success controllers in source.',
        'Continue full TW/CN phases/variants/deferred and all gameplay source routes; preserve saves, conversion and native fonts; no phase1 build/tests/runtime/deploy.',
    ]
    dump(path,ledger)
    print(json.dumps({'artifact':str(out),'snapshot_files':len(saved),'new_source_files':4,'qualified_selection_paths':2,
        'shared_scene_identities':144,'new_complete_routes':0,'tests_run':False}))

if __name__=='__main__':main()
