"""Static TW/CN record difference and existing shared-table source handoff.

Reads retained raw inputs and source files only. No SQLite/import/native/API/
C++/Lua execution, build or tests. Does not run the retained input's lab tool.
"""
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
from .cn_wrapper_route_frontier import ROOT

NAME='cn-shared-skill-catalog-storage-source-01'
ROUND='20261008-cn-shared-skill-catalog-storage-source'
TW=ROOT/'artifacts/research/enemy-blackbox-20261006/consumer-experiment/inputs/client/Data2/Fight/Spg/cbspec2.bin'
CN=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/Data2/Fight/Spg/cbspec2.bin')
INSTALLED_TW=Path('C:/Users/risei/Desktop/God2/God2/Data2/Fight/Spg/cbspec2.bin')
TW_SHA='7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51'
CN_SHA='857b52e36ceb4d08f61a373f2882593dada84ecbb8150da187f8c5553389a004'
CN_IMAGE_SHA='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
DATASET='cn-native-cbspec2-582f2695-857b52e3-v1'
SOURCES=['src/cn/assets/CnSharedSkillCatalog.h','src/cn/assets/CnSharedSkillCatalog.cpp',
 'src/cn/world/SharedPrebornWindowSource.h','src/cn/world/SharedPrebornWindowSource.cpp',
 'docs/research/cn-shared-skill-catalog-storage-source-20261008.md',
 'tools/reconstruction/cn_shared_skill_catalog_storage_source_delivery.py','tools/reconstruction/dual_client_route_catalog.py']
REMAINING=[
 'Actual common skill/subject gameplay identity/learning/eligibility/cost/native Lua/transaction/save/persistent replay remain unconfigured; raw key intersection is not semantic mapping.',
 'Actual CN dataset import/shared reader/resource supplier/initial issuer/Application hosting remain unconfigured; phase1 makes no database access or import.',
 'Native84 caller and all preborn initial issuer/timing variants remain open.',
 'Full TW/CN/PC/web/WSS/common login/world/all gameplay/numeric64/stack99/whole-game denominator and later comprehensive tests/repair/release remain open.']

def sha(raw):return hashlib.sha256(raw).hexdigest()

def records(raw):
    if len(raw)!=112660 or raw[:4]!=b'1.03':raise RuntimeError('Source envelope differs')
    counts=[int.from_bytes(raw[4+k*0x6e04:8+k*0x6e04],'little') for k in range(4)]
    rows={};ordinal=0
    for kind,count in enumerate(counts):
        if count>255:raise RuntimeError('Outside bounded declared definitions')
        for ident in range(1,count+1):
            offset=8+kind*0x6e04+(ident-1)*110;data=raw[offset:offset+110]
            if data[:2]!=bytes([ident,kind]):raise RuntimeError('Declared native key differs')
            rows[kind,ident]=dict(kind=kind,definition_id=ident,source_record_index=ordinal,
                source_offset=offset,record_sha256=sha(data),raw_hex=data.hex());ordinal+=1
    return counts,rows

def main():
    base=ROOT/'artifacts/integration/packet-connections-20261006';out=base/NAME
    if not (out/'before-manifest.json').exists() or (out/'findings.json').exists():raise RuntimeError('Fresh before snapshot required')
    def save(rel,data):
        p=out/rel;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(data)
    def dump(rel,value):save(rel,(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    before=json.loads((out/'before-manifest.json').read_text(encoding='utf-8'))
    if len(before)!=127:raise RuntimeError('Expected127 retained before files')
    old={row['path']:(out/row['snapshot']).read_bytes() for row in before}
    books=['docs/PACKET_CONNECTION_GOAL_20261006.md','artifacts/integration/packet-connections-20261006/packet-route-ledger.json']
    reports={f'artifacts/integration/packet-connections-20261006/packet-progress-latest.{ext}' for ext in ('json','md')}
    protected=[]
    for row in before:
        if sha(old[row['path']])!=row['sha256']:raise RuntimeError('Before snapshot differs')
        if row['path'] not in set(SOURCES)|set(books)|reports:
            if (ROOT/row['path']).read_bytes()!=old[row['path']]:raise RuntimeError('Protected source differs: '+row['path'])
            protected.append(row)
    prior=(out/'retained-prior/cn-native-skill-catalog-source-01/manifest.json').read_bytes()
    if sha(prior)!='fe48389fd00bece1bce48659c05dd234a98904e9b065945131fbd74248b1dfb3' or not json.loads(prior)['sealed']:
        raise RuntimeError('Prior seal differs')
    input_facts=[];raws={};decoded={};counts={}
    for version,path,pin in [('tw',TW,TW_SHA),('cn',CN,CN_SHA)]:
        raw=path.read_bytes()
        if sha(raw)!=pin:raise RuntimeError('Pinned resource differs: '+version)
        counts[version],decoded[version]=records(raw);raws[version]=raw
        save('inputs/'+version+'/cbspec2.bin',raw)
        input_facts.append(dict(version=version,original_path=str(path),bytes=len(raw),sha256=pin,
            declared_counts=counts[version],declared_records=len(decoded[version]),native_input_not_lab_output=True))
    dump('inputs/source-identities.json',input_facts)
    tw=decoded['tw'];cn=decoded['cn'];common=set(tw)&set(cn);pairs=[];different=Counter()
    for key in sorted(common):
        a=bytes.fromhex(tw[key]['raw_hex']);b=bytes.fromhex(cn[key]['raw_hex'])
        offsets=[n for n in range(110) if a[n]!=b[n]];different.update(offsets)
        pairs.append(dict(kind=key[0],definition_id=key[1],tw=tw[key],cn=cn[key],
            identical_full_record=not offsets,different_offsets=offsets,shared_gameplay_identity_qualified=False))
    dump('comparison/shared-native-keys-not-semantic-mappings.json',pairs)
    comparison=dict(tw_declared_records=len(tw),cn_declared_records=len(cn),shared_native_keys=len(common),
        identical_full_records=sum(p['identical_full_record'] for p in pairs),different_full_records=sum(bool(p['different_offsets']) for p in pairs),
        tw_only_keys=[list(k) for k in sorted(set(tw)-set(cn))],cn_only_keys=[list(k) for k in sorted(set(cn)-set(tw))],
        differing_byte_frequency=[dict(offset=k,record_pairs=v) for k,v in sorted(different.items())],
        localized_names_or_same_ID_not_semantic_proof=True,numeric_field_meanings_not_invented=True,
        TW_dataset_promoted_to_CN=False,common_skill_identity_mapping_qualified=False)
    dump('comparison/findings.json',comparison)
    installed=INSTALLED_TW.read_bytes();installed_counts,installed_records=records(installed)
    dump('inputs/installed-TW-observation.json',dict(path=str(INSTALLED_TW),bytes=len(installed),sha256=sha(installed),
        declared_counts=installed_counts,declared_records=len(installed_records),
        original_TW_baseline_replaced=False,installed_CUSTOM_promoted_to_CN=False,installed_bytes_changed=False))
    source=dict(dataset_id=DATASET,source_path='data2/fight/spg/cbspec2.bin',source_sha256=CN_SHA,
        decoded_sha256=CN_SHA,native_image_sha256=CN_IMAGE_SHA,source_section='CN preborn cbspec2 version1.03',
        loader_rva='0x161bb0',lookup_rva='0x133300',row_count=len(cn))
    dump('prepared-import-material/native-data-source.json',source)
    dump('prepared-import-material/native-skill-catalog-rows.json',[dict(dataset_id=DATASET,**cn[k]) for k in sorted(cn)])
    dump('prepared-import-material/scope.json',dict(material_only=True,SQL_or_import_executed=False,
        storage_tables=['native_data_sources','native_skill_catalog'],new_tables_required=False,new_migration_required=False,
        production_backup_recovery_and_later_validation_required=True,TW_dataset_or_rows_overwritten=False,
        learned_skill_or_gameplay_identity_or_cost_material=False))
    for rel in ['src/db/NativeSkillCatalog.h','src/db/NativeSkillCatalog.cpp','src/db/Migration.cpp','src/db/SqliteDatabase.h',
                'src/cn/assets/CnNativeSkillCatalog.h','src/cn/assets/CnNativeSkillCatalog.cpp','CMakeLists.txt']:
        save('retained-inputs/'+rel,(ROOT/rel).read_bytes())
    for rel in ['cn-native-skill-catalog-source-01/native/skill-catalog-source-relations.json',
                'cn-native-skill-catalog-source-01/resource/source.json',
                'cn-native-skill-catalog-source-01/source/source-origins.json',
                'cn-preborn-selected-subject-source-01/source-correction/operational-subject-evidence.json']:
        save('retained-inputs/'+rel,(base/rel).read_bytes())
    relations=dict(version='cn',native_sha256=CN_IMAGE_SHA,resource_sha256=CN_SHA,dataset_id=DATASET,
        source_reader='CnSharedSkillCatalog',shared_tables=['native_data_sources','native_skill_catalog'],
        existing_reader='NativeSkillCatalog::lookup(dataset,kind,id)',new_migration_required=False,
        actual_source_rows_required=453,all_rows_required_at_bind=True,actual_shared_rows_read_again_per_lookup=True,
        exact_native_source_metadata_ordinal_offset_raw_and_hash_required=True,same_game_owner_required=True,
        DB_reader_and_connection_lifetime_borrowed=True,TW_dataset_fallback=False,
        preborn_actual_common_apply_receives_owning_shared_store_native_records=True,
        ordered_duplicate_raw_words_preserved=True,post_commit_retained_identity_not_retired_window_current=True,
        native_snapshot_required=False,actual_shared_reader_bound=False,actual_CN_rows_imported=False,
        common_skill_identity_mapping_qualified=False,rule_save_replay_owner_configured=False,
        formal_application_hosted=False,complete_route=False,comparison=comparison)
    dump('source/shared-storage-relations.json',relations)
    facts=dict(round=ROUND,previous_goal_turn_classification='progress:132 actual CN resource/supplier/453 records sealed',
        native_sha256=CN_IMAGE_SHA,tw_resource_sha256=TW_SHA,cn_resource_sha256=CN_SHA,
        tw_declared_skill_definition_records=448,cn_declared_skill_definition_records=453,
        shared_native_keys_not_semantic_mappings=448,identical_full_native_records=0,different_full_native_records=448,
        CN_only_declared_keys=comparison['cn_only_keys'],cn_shared_skill_catalog_source_adapters_added=1,
        cn_preborn_existing_shared_store_handoffs_strengthened=1,new_schema_or_tables_added=0,new_migration_added=0,
        actual_shared_skill_database_reader_bound=False,actual_CN_skill_rows_imported=False,
        actual_common_skill_identity_mapping_configured=False,actual_common_rule_save_replay_owner_configured=False,
        actual_preborn_initial_issuer_configured=False,formal_application_hosted=False,
        new_packet_values=0,new_native_phase_source_bindings=0,new_source_owner_chains=0,new_tw_source_owner_chains=0,
        new_complete_bidirectional_routes=0,whole_game_route_total=None,whole_game_completed_routes=None,
        whole_game_completion_percent=None,original_native_wire_layout_changed=False,original_native_baseline_changed=False,
        unknown_values_invented=False,native_snapshot_required=False,levels_changed=False,fonts_changed=False,
        build_run=False,tests_run=False,runtime_run=False,Cplusplus_source_run=False,Windows_API_run=False,
        native_execution=False,database_access=False,database_import=False,database_migration=False,deployed=False,
        protected_contexts=protected,remaining=REMAINING)
    dump('findings.json',facts)
    ledger_path=base/'packet-route-ledger.json';ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
    ledger['cn_shared_skill_catalog_storage_source']=dict(facts,evidence=out.relative_to(ROOT).as_posix())
    ledger['dual_client_source_segments'].append(dict(name='CN qualified native definitions in existing shared catalog tables ->preborn common-operation record handoff',
        version_scope='pinned-cn-cbspec2-857b52e3-shared-table-source-only-no-TW-semantic-alias',
        status='Actual shared-table adapter and record handoff source; actual CN rows/import/reader binding/common skill identity/rules/save/replay/issuer/Application unconfigured',
        source_paths=SOURCES,native_c2s_by_phase={},native_s2c_by_phase={},source_owner_chains_added=0,
        tw_source_owner_chains_added=0,formal_application_hosted=False,complete_gameplay_routes_added=0,
        evidence=out.relative_to(ROOT).as_posix(),remaining=REMAINING))
    ledger['dual_client_execution_plan']['latest_work_round']=ROUND
    ledger['dual_client_execution_plan']['next_source_frontier']='Actual common skill/subject gameplay identity and native eligibility/rules/save/replay/issuer/Application. CN shared-table import remains deferred PHASE1. Native84 caller/timing; full TW/CN/PC/web/WSS/gameplay/numeric64/stack99/denominator.'
    ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/books[0]).open('a',encoding='utf-8') as f:
        f.write('\n\n## CN same-table skill source ('+ROUND+')\n\n'
            'Retained original TW resource7676 and CN857b comparison:448 intersecting native keys, zero identical complete records, CN-only0/122..125 and1/130. '
            'Installed TW3adc CUSTOM resource remains distinct; no source baseline replacement or same-ID/name semantic alias. '
            'Added CnSharedSkillCatalog binding actual CN rows in existing native_data_sources/native_skill_catalog through the same NativeSkillCatalog reader, full source/ordinal/offset/raw/hash/current/thread checks; existing preborn apply receives owned shared-store native records. '
            'Prepared CN source/row material only: no DB access/import/migration/activation. Common skill identity/learning/rules/save/replay/issuer/Application and full-game goal remain open. '
            'No new opcode/phase/partial owner/complete route; PHASE1 and later comprehensive tests/repair/recovery release unchanged.\n')
    origins=[]
    for rel in SOURCES+books:
        data=(ROOT/rel).read_bytes();save('source/current/'+rel,data);origins.append(dict(path=rel,bytes=len(data),sha256=sha(data)))
        if rel in old:
            diff=''.join(difflib.unified_diff(old[rel].decode('utf-8-sig').splitlines(True),data.decode('utf-8-sig').splitlines(True),fromfile='before/'+rel,tofile='source/'+rel))
            if diff:save('diff/'+rel+'.diff',diff.encode('utf-8'))
    dump('source/source-origins.json',origins)
    print(json.dumps({k:facts[k] for k in ['round','shared_native_keys_not_semantic_mappings','identical_full_native_records','cn_shared_skill_catalog_source_adapters_added','new_complete_bidirectional_routes']}))

if __name__=='__main__':main()
