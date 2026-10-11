"""Preserve source-only CN native definition import delivery; never run SQLite/C++."""
import difflib
import hashlib
import json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT

NAME='cn-shared-skill-catalog-import-source-01'
ROUND='20261008-cn-shared-skill-catalog-import-source'
SOURCES=['src/cn/assets/CnNativeSkillCatalogImport.h','src/cn/assets/CnNativeSkillCatalogImport.cpp',
 'src/db/SqliteDatabase.h','src/db/SqliteDatabase.cpp',
 'docs/research/cn-shared-skill-catalog-import-source-20261008.md',
 'tools/reconstruction/cn_shared_skill_catalog_import_source_delivery.py',
 'tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual import execution/shared reader/resource provider/initial issuer/Application remain unconfigured; PHASE1 does not access any DB.',
 'Actual common subject/skill identity, native learning/eligibility/cost/Lua rules/character save/persistent replay/committed native publication remain open; definition import grants nothing.',
 'Native84 caller/root/phase/initial window timing remains open; no guessed WORLD84/cancel/A0 pair.',
 'Full TW/CN/PC/web/WSS/all gameplay/numeric64/stack99/whole-game denominator and later comprehensive tests/repair/recovery release remain open.']

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    b=ROOT/'artifacts/integration/packet-connections-20261006';o=b/NAME
    if not (o/'before-manifest.json').exists() or (o/'findings.json').exists():
        raise RuntimeError('Fresh before snapshot required; retain prior delivery')
    def save(rel,data):
        p=o/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((o/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=155:raise RuntimeError('Expected155 before files')
    old={r['path']:(o/r['snapshot']).read_bytes() for r in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{e}' for e in ['json','md']}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before bytes differ')
        if row['path'] not in set(SOURCES+books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:
                raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(o/'retained-prior/cn-preborn-ui-close-caller-lineage-01/manifest.json').read_bytes()
    if sha(prior)!='095f2c32ea42671e1043e91e0c00db881f1fead904b6402a66da7cdf280b8909' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    material=b/'cn-shared-skill-catalog-storage-source-01/prepared-import-material'
    resource=(b/'cn-native-skill-catalog-source-01/resource/cbspec2.bin').read_bytes()
    if len(resource)!=112660 or sha(resource)!='857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004':
        raise RuntimeError('Retained native resource differs')
    save('inputs/cn-cbspec2.bin',resource)
    source_raw=(material/'native-data-source.json').read_bytes()
    source=json.loads(source_raw.decode('utf-8'))
    save('inputs/native-data-source.json',source_raw)
    rows=[]
    for kind,count in enumerate([125,130,87,111]):
        declared=int.from_bytes(resource[4+kind*0x6e04:8+kind*0x6e04],'little')
        if declared!=count:raise RuntimeError('Native group count differs')
        for ident in range(1,count+1):
            at=8+kind*0x6e04+(ident-1)*110;record=resource[at:at+110]
            if record[:2]!=bytes([ident,kind]):raise RuntimeError('Native record key differs')
            rows.append(dict(dataset_id=source['dataset_id'],kind=kind,definition_id=ident,
                source_record_index=len(rows),source_offset=at,record_sha256=sha(record),raw_hex=record.hex()))
    retained_rows=(material/'native-skill-catalog-rows.json').read_bytes()
    if json.loads(retained_rows.decode('utf-8'))!=rows or source['row_count']!=len(rows):
        raise RuntimeError('Retained prepared material differs from raw source')
    save('inputs/native-skill-catalog-rows.json',retained_rows)
    # Schema/source inventory only. Do not import or run lab import helpers.
    for rel in ['src/db/Migration.cpp','src/db/SqliteSupport.h','src/db/NativeSkillCatalog.h',
        'src/db/NativeSkillCatalog.cpp','src/cn/assets/CnNativeSkillCatalog.h',
        'src/cn/assets/CnNativeSkillCatalog.cpp','src/cn/assets/CnSharedSkillCatalog.h',
        'src/cn/assets/CnSharedSkillCatalog.cpp','src/cn/world/SharedPrebornWindowSource.h',
        'src/cn/world/SharedPrebornWindowSource.cpp','CMakeLists.txt','src/core/Application.cpp']:
        save('retained-inputs/'+rel,(ROOT/rel).read_bytes())
    for rel in ['cn-native-skill-catalog-source-01/native/skill-catalog-source-relations.json',
        'cn-shared-skill-catalog-storage-source-01/source/shared-storage-relations.json',
        'cn-preborn-selected-subject-source-01/source-correction/operational-subject-evidence.json']:
        save('retained-inputs/'+rel,(b/rel).read_bytes())
    relations=dict(version='cn',dataset=source['dataset_id'],native_sha256=source['native_image_sha256'],
        resource_sha256=sha(resource),native_declared_record_count=len(rows),
        explicit_database_entry='SqliteDatabase::import_cn_native_skill_catalog',
        writer='CnNativeSkillCatalogImport::import_actual_source',
        actual_provider_type='god2cn::CnNativeSkillCatalog',provider_owns_pinned_bytes=True,
        tables=['native_data_sources','native_skill_catalog'],new_tables=False,new_migration=False,
        writer_uses_same_database_owned_connection=True,transaction='existing BEGIN IMMEDIATE/RAII rollback',
        borrowed_transaction_rejected=True,existing_migration5_required=True,foreign_keys_required=True,
        exact_complete_existing_data_idempotent=True,partial_or_orphan_or_conflicting_data_not_replaced=True,
        post_insert_same_transaction_reader='NativeSkillCatalog::lookup',
        all_source_ordinal_offset_hash_raw_identity_and_total_count_read_back=True,
        actual_resource_current_before_commit=True,reader_current_after_import_requires_existing_CnSharedSkillCatalog_bind=True,
        default_migration_or_login_or_Application_calls_import=False,client_requests_do_not_trigger_import=True,
        actual_database_import_executed=False,actual_shared_reader_bound=False,actual_CN_rows_imported=False,
        common_skill_identity_mapping_qualified=False,learned_skill_grants_added=False,
        native_snapshot_required=False,formal_application_hosted=False,complete_route=False)
    dump('source/import-source-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:139 native84/local GUI lineage plus final accounting and seals',
        cn_shared_skill_catalog_import_writers_added=1,cn_explicit_same_database_skill_import_entries_added=1,
        native_declared_skill_records=len(rows),native_declared_record_bytes=sum(len(bytes.fromhex(r['raw_hex'])) for r in rows),
        new_schema_or_tables_added=0,new_migration_added=0,actual_shared_skill_database_reader_bound=False,
        actual_CN_skill_rows_imported=False,actual_common_skill_identity_mapping_configured=False,
        actual_common_rule_save_replay_owner_configured=False,actual_preborn_initial_issuer_configured=False,
        formal_application_hosted=False,new_packet_values=0,new_native_phase_source_bindings=0,
        new_source_owner_chains=0,new_tw_source_owner_chains=0,new_complete_bidirectional_routes=0,
        whole_game_route_total=None,whole_game_completed_routes=None,whole_game_completion_percent=None,
        original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        learned_skill_grants_added=False,native_snapshot_required=False,levels_changed=False,fonts_changed=False,
        build_run=False,tests_run=False,runtime_run=False,Cplusplus_source_run=False,Windows_API_run=False,
        native_execution=False,database_access=False,database_import=False,database_migration=False,deployed=False,
        protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    lp=b/'packet-route-ledger.json';ledger=json.loads(lp.read_text(encoding='utf-8'))
    ledger['cn_shared_skill_catalog_import_source']=dict(facts,evidence=o.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='CN pinned immutable definitions -> explicit same shared database transactional import/readback source',
        version_scope='pinned-cn-cbspec2-857b52e3-shared-table-import-source-only-no-execution-or-gameplay-grants',
        status='Explicit C++ import writer and existing database entry; actual import/provider/common identities/authority/rules/save/replay/issuer/Application unconfigured',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=o.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Actual common subject/skill identity and native learning/eligibility/cost/rules/save/persistent replay/issuer/Application; explicit CN shared-table import source exists but execution deferred PHASE1. Native84 caller/timing; full TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator.'
    lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN shared-table skill import source ('+ROUND+')\n\n'
            'Added explicit SqliteDatabase entry using its own connection and pinned native453-record C++ import source. '
            'Existing shared tables/migration/foreign keys/own transaction; no overwrite of partial/conflicting/orphan rows, exact source and every record read back before commit, RAII rollback and actual Current gates. '
            'No import/default migration/login/Application execution or grants; actual provider/shared reader/common subject/skill mapping/rules/save/replay/issuer remain open. '
            'Retained original native source and prior seal; PHASE1/full TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator and later comprehensive tests/repair/recovery release unchanged.\n')
    origins=[]
    for rel in SOURCES+books:
        data=(ROOT/rel).read_bytes();save('source/current/'+rel,data)
        origins.append(dict(path=rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            patch=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if patch:save('diff/'+rel+'.diff',patch.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ['round','cn_shared_skill_catalog_import_writers_added',
        'cn_explicit_same_database_skill_import_entries_added','native_declared_skill_records','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
