"""CUSTOM-0078 announcement release49->50; prepare only unless apply --execute.

Never replace a save with a backup, never downgrade, never change client resources.
Only an exact two-locale real-client receipt can qualify stage/apply. The new
candidate must reopen migrated50 with announcement gameplay disabled; rehearsal
proves that forward recovery path before an idle managed process may be stopped.
"""
import argparse
from contextlib import closing
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.operations import owned_guild_release_v02_20261004 as base

ROOT = base.ROOT
FORMAT = 'owned-guild-announcement-release-20261004-v1'
MIGRATION_NAME = 'owned_guild_announcements_candidate'
SCHEMA_SOURCE = 'src/db/SqliteOwnedGuildAnnouncementRepository.cpp'
NEW_TABLES = {'owned_guild_announcements_0078'}
LAB_ENV = base.LAB_ENV
RESOURCES = {name: new for name, _, _, new in base.RESOURCES}
managed = base.managed
managed_links = base.managed_links
require, sha, read, write_new, rooted = base.require, base.sha, base.read, base.write_new, base.rooted
exact_json = base.exact_json


def capture_connection(db):
    result = base.capture_connection(db)
    result.pop('history48_typed')
    result['history49_typed'] = base.fingerprint(db, 'schema_migrations', ' WHERE version<=49')
    return result


def capture(path):
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        return capture_connection(db)


def migration_sql():
    source = (ROOT / SCHEMA_SOURCE).read_text('utf-8')
    found = re.search(r'SqliteOwnedGuildAnnouncementRepository::schema\(\)\s*\{\s*return R"SQL\((.*?)\)SQL";', source, re.S)
    require(found, 'Exact migration50 SQL not found')
    return found.group(1)


def require49(state):
    require([row[0] for row in state['history']] == list(range(1, 50)), 'Expected exact history1..49')
    require(not NEW_TABLES.intersection(state['tables']), 'Migration50 exists; no reapply or downgrade')
    require({'owned_guild_governance_0078', 'owned_guild_applications_0078', 'sqlite_sequence'} <= set(state['tables']),
            'Expected existing qualified membership49 tables')


def expected_addition(sql):
    with closing(sqlite3.connect(':memory:')) as db:
        db.executescript(sql)
        return [list(row) for row in db.execute(
            'SELECT type,name,tbl_name,sql FROM sqlite_master WHERE tbl_name=? ORDER BY type,name',
            ('owned_guild_announcements_0078',))]


def require50(before, after, sql, template=None):
    require49(before)
    require(set(after['tables']) == set(before['tables']) | NEW_TABLES, 'Unexpected migration50 table set')
    addition = [row for row in after['schema'] if row[2] in NEW_TABLES]
    require(addition == expected_addition(sql), 'Migration50 DDL/index differs from exact qualified SQL')
    require([row for row in after['schema'] if row[2] not in NEW_TABLES] == before['schema'],
            'Existing schema/index/trigger changed')
    require(len(after['history']) == 50 and after['history'][:-1] == before['history'], 'Old migration history changed')
    require(after['history'][-1][:3] == [50, MIGRATION_NAME, sql], 'Migration50 identity/SQL differs')
    require(after['history49_typed'] == before['history49_typed'], 'Old typed history/unknown columns changed')
    require(after['pragmas'] == before['pragmas'], 'SQLite metadata changed')
    for table, value in before['tables'].items():
        if table != 'schema_migrations':
            require(after['tables'][table] == value, 'Saved typed rows changed: ' + table)
    require(all(after['tables'][table]['rows'] == 0 for table in NEW_TABLES), 'Migration granted gameplay data')
    if template is not None:
        require(addition == [row for row in template['schema'] if row[2] in NEW_TABLES], 'Install DDL differs from stage')
        require(after['history'][-1][:3] == template['history'][-1][:3], 'Install SQL differs from stage')


def announcement_config(config, enabled):
    result = deepcopy(config)
    membership = result.get('world', {}).get('owned_guild_membership', {})
    require(membership.get('enabled') is True and membership.get('entry_resource_bundle') == base.BUNDLE,
            'Announcement requires preserved formally qualified membership entry')
    result['world']['owned_guild_announcements'] = {'enabled': bool(enabled)}
    return result


def resource_pins():
    return {str((managed.CLIENT.parent / 'Data2/Patch/Comm' / name).resolve()): expected
            for name, expected in RESOURCES.items()}


def assert_resources(pins=None):
    actual = resource_pins()
    if pins is not None:
        require(actual == pins, 'Resource target/pins differ from current paired2996')
    for path, expected in actual.items():
        require(sha(path) == expected, 'Preserved client resource changed: ' + path)
    return actual


def validate_contract(path, candidate):
    contract = read(path)
    require(contract.get('design') == 'CUSTOM-0078', 'Wrong design')
    require(rooted(contract['candidate_path']) == Path(candidate).resolve(), 'Candidate path differs')
    require(sha(candidate) == contract['candidate_sha256'], 'Candidate identity changed')
    closure = contract.get('source_sha256')
    require(isinstance(closure, dict) and closure, 'Exact source closure missing')
    for required in (SCHEMA_SOURCE, 'src/db/Migration.cpp', 'src/core/Application.cpp',
                     'src/db/SqliteDatabase.cpp', 'src/core/Config.cpp', 'src/main.cpp',
                     'src/db/ServerSqliteMigrations.h', 'src/db/ServerSqliteMigrations.cpp',
                     'tools/operations/owned_guild_announcement_release_v01_20261004.py',
                     'tools/operations/owned_guild_release_v02_20261004.py',
                     'tools/operations/packet_links_release_20260930.py',
                     'tools/operations/native_quest_catalog_release.py',
                     'tools/operations/verify_frozen_chat_20260927.py'):
        require(required in closure, 'Required runtime/storage source missing: ' + required)
    for source, expected in closure.items():
        require(sha(rooted(source)) == expected, 'Source closure changed: ' + source)
    helper = rooted(contract['helper_path'])
    require(sha(helper) == contract['helper_sha256'], 'Native UI helper identity changed')
    require(any(rooted(p) == helper and h == contract['helper_sha256'] for p, h in closure.items()),
            'Native UI helper is not in source closure')
    return contract


def validate_formal_config_proof(proof, contract, locale):
    require(isinstance(proof, dict), 'Missing exact formal config proof')
    base.true_fields(proof, ('accepted', 'all_other_gameplay_flags_preserved'), 'Formal config')
    path = rooted(proof.get('source_path', ''))
    require(path == managed.CONFIG.resolve(), 'Formal config target differs')
    key = path.relative_to(ROOT).as_posix()
    require(contract['source_sha256'].get(key) == proof.get('source_sha256') == sha(path), 'Formal config pin changed')
    source, actual = proof.get('source'), proof.get('actual')
    require(isinstance(source, dict) and exact_json(source, read(path)) and isinstance(actual, dict), 'Formal config content differs')
    private = Path(proof.get('private_path', ''))
    require(private.is_absolute(), 'Private config must have absolute path')
    expected = announcement_config(source, True)
    expected['database']['path'] = str(private.with_name('town-diagnostic-accounts.db'))
    expected['logging']['file'] = str(private.with_name('server.log'))
    expected['server'].update(host='127.0.0.1', port=2598, character_port=0)
    expected['development']['diagnostic_remote_actor_language'] = int(locale == 936)
    require(exact_json(actual, expected), 'Unrelated formal flags changed in acceptance')


def validate_denied_save(ui, text):
    denied = ui.get('announcement_denied_save_restore', {})
    base.true_fields(denied, ('accepted', 'sql_exact', 'cache_restored', 'native79_via_control28',
                             'no_explicit_help_reopen'), 'Native denied save')
    require(denied.get('denied_log', {}).get('fields', {}).get('committed') == 'false', 'Denied save commit differs')
    fields = denied.get('restored_log', {}).get('fields', {})
    require(fields.get('revision') == '1' and fields.get('published') == 'true', 'Authority restore publication missing')
    cache = denied.get('cache', {})
    require(cache.get('text_hex') == text.hex() and cache.get('logical_size') == len(text) + 4 and
            cache.get('editing') == 0 and cache.get('self_role') == 3, 'Denied native cache not restored')
    draft = denied.get('native_input', {}).get('draft_text_hex')
    require(isinstance(draft, str) and draft and draft != text.hex(), 'Denied save did not exercise changed draft')
    return denied


def validate_receipt(receipt, contract, contract_sha):
    base.true_fields(receipt, ('accepted', 'formal_config', 'env_lab_false', 'sources_unchanged', 'candidate_unchanged',
        'protected_files_unchanged', 'protected_DB_exact', 'frozen_unchanged', 'protected_processes_exact',
        'desktop_unchanged', 'foreground_unchanged'), 'Real-client acceptance')
    require(receipt.get('contract_sha256') == contract_sha, 'Receipt/contract identity differs')
    require(receipt.get('sources_before') == contract['source_sha256'] == receipt.get('sources_after'), 'Receipt source closure differs')
    for before, after in (('files_before', 'files_after'), ('frozen_before', 'frozen_after'),
                          ('protected_DB_before', 'protected_DB_after'), ('protected_processes_before', 'protected_processes_after')):
        require(isinstance(receipt.get(before), dict) and receipt[before] and receipt[before] == receipt.get(after),
                'Preservation guard differs: ' + before)
    cases = receipt.get('cases')
    require(isinstance(cases, list) and len(cases) == 2 and {c.get('locale') for c in cases} == {950, 936},
            'Both real-client locale cases required')
    for case in cases:
        require(type(case.get('locale')) is int, 'Locale type differs')
        base.true_fields(case, ('accepted', 'formal_config', 'env_lab_false', 'private_files_unchanged',
                     'all_private_images_closed', 'all_owned_processes_closed', 'exclusive_2598_released'), 'Native case')
        require(type(case.get('runner_exit')) is int and case['runner_exit'] == 0, 'Real native runner failed')
        runtime = case.get('runtime_configured_log', '')
        require(isinstance(runtime, str) and 'OWNED_GUILD_RUNTIME ' in runtime and
                'enabled=true ordinary_entry=true lab=false schema=50 CUSTOM-0078' in runtime, 'Native runtime/config schema differs')
        validate_formal_config_proof(case.get('formal_config_proof'), contract, case['locale'])
        environment = case.get('environment_proof', {})
        for name in ('launch_lab_values', 'observed_server_lab_values'):
            values = environment.get(name)
            require(isinstance(values, dict) and set(values) == set(LAB_ENV) and all(v is None for v in values.values()),
                    'Lab environment proof differs')
        ui = case.get('ui', {})
        base.true_fields(ui, ('accepted', 'env_lab_false', 'ordinary_paired_entry_accepted', 'announcement_actual_client_accepted',
                    'desktop_unchanged', 'all_clients_closed', 'all_loaders_closed'), 'Native announcement UI')
        require(ui.get('locale') == case['locale'] and exact_json(ui.get('formal_config_proof'), case['formal_config_proof']),
                'UI locale/formal proof differs')
        loaded = ui.get('native_loaded_resource_proof', {})
        base.true_fields(loaded, ('original2995_all_rows_byte_exact', 'VM_READ_only'), 'Loaded resource')
        require(loaded.get('count') == 2996 and loaded.get('locale') == case['locale'] and
                len(loaded.get('new2996_rows', {}).get('rows_hex', [])) == 4, 'Native loaded paired resources differ')
        for operation in ('real_create', 'real_pending_application', 'real_native_71_approve'):
            base.true_fields(ui.get(operation, {}), ('accepted',), 'Native guild workflow ' + operation)
        base.true_fields(ui.get('announcement_cancel', {}), ('accepted', 'sql_exact', 'no_save_marker'), 'Native local cancel')
        save = ui.get('announcement_save', {})
        base.true_fields(save, ('accepted', 'native79_via_control28'), 'Native save')
        fields = save.get('log', {}).get('fields', {})
        require(fields.get('committed') == 'true' and fields.get('revision') == '1', 'Server save commit proof missing')
        stored = save.get('stored')
        require(isinstance(stored, list) and len(stored) == 1 and len(stored[0]) == 6 and
                stored[0][2:5] == [1, 'CUSTOM_DESIGNED', 'CUSTOM-0078'], 'Persisted announcement/provenance differs')
        delta = save.get('SQL_delta', {})
        require(set(delta) == NEW_TABLES and len(delta['owned_guild_announcements_0078']['after']) == 1 and
                delta['owned_guild_announcements_0078']['before'] == [], 'Save changed unrelated SQL or row count')
        text = stored[0][1].encode('cp950' if case['locale'] == 950 else 'gbk')
        cache = save.get('cache', {})
        require(cache.get('text_hex') == text.hex() and cache.get('logical_size') == len(text) + 4 and
                cache.get('editing') == 0 and cache.get('self_role') == 3, 'Actual saver98 cache differs')
        validate_denied_save(ui, text)
        member = ui.get('announcement_member_read', {})
        base.true_fields(member, ('accepted', 'sql_exact', 'editing0'), 'Native member read')
        require(member.get('readonly_publication', {}).get('fields', {}).get('write_authorized') == 'false', 'Member received write authorization')
        relogins = ui.get('announcement_relogin_reads')
        require(isinstance(relogins, list) and len(relogins) == 2 and {r.get('identity') for r in relogins} == {4, 5},
                'Founder/member native relogin proof missing')
        for record in relogins:
            require(record.get('sql_exact') is True and record.get('cache', {}).get('text_hex') == text.hex(), 'Relogin persistence/cache differs')
    return receipt


def qualify_inputs(args):
    require(args.candidate and args.contract and args.receipt, 'Exact candidate, contract and two-locale receipt required')
    candidate, contract_path, receipt_path = rooted(args.candidate), rooted(args.contract), rooted(args.receipt)
    contract = validate_contract(contract_path, candidate)
    receipt = validate_receipt(read(receipt_path), contract, sha(contract_path))
    require(receipt['files_before'].get('client') == sha(managed.CLIENT), 'Accepted client differs from current')
    for source, expected in receipt['frozen_before'].items():
        require(sha(rooted(source)) == expected, 'Frozen acceptance dependency changed: ' + source)
    return candidate, contract_path, contract, receipt_path, receipt


def artifact_path(release, name):
    result = (release / name).resolve()
    require(result != release.resolve() and result.is_relative_to(release.resolve()), 'Artifact escapes release root')
    return result


def stage(args):
    candidate, contract_path, contract, receipt_path, _ = qualify_inputs(args)
    release = rooted(args.release)
    require(not release.exists(), 'Choose an unused release directory')
    config, database = base.configured_database()
    require(config.get('world', {}).get('owned_guild_announcements', {}).get('enabled', False) is False,
            'Announcement already enabled; no unrelated release reapply')
    guard, resources = base.freeze_gate(), assert_resources()
    release.mkdir(parents=True, exist_ok=False)
    copies = [(candidate, 'god2-server.candidate.exe'), (managed.ACTIVE, 'god2-server.before.exe'),
              (managed.CONFIG, 'server-config.before.json'), (contract_path, 'contract.json'), (receipt_path, 'native-receipt.json')]
    for source, name in copies:
        shutil.copy2(source, release / name)
    # Snapshot actual sealed sources with ordinal names: absolute and relative
    # closure keys may alias, and no untrusted key may escape the release root.
    snapshot_map = {}
    source_dir = release / 'source-snapshot'
    source_dir.mkdir()
    for index, (source, expected) in enumerate(sorted(contract['source_sha256'].items())):
        name = 'source-snapshot/' + str(index).zfill(5) + '-' + rooted(source).name
        target = artifact_path(release, name)
        shutil.copy2(rooted(source), target)
        require(sha(target) == expected, 'Snapshot source changed during copy: ' + source)
        snapshot_map[source] = name
    write_new(release / 'source-snapshot-map.json', snapshot_map)
    base.backup_new(database, release / 'stage-before.db')
    before = capture(release / 'stage-before.db')
    require49(before)
    base.backup_new(release / 'stage-before.db', release / 'town-diagnostic-accounts.db')
    enabled = announcement_config(config, True)
    enabled['database']['path'] = str(release / 'town-diagnostic-accounts.db')
    enabled['logging']['file'] = str(release / 'stage-server.log')
    disabled = announcement_config(enabled, False)
    write_new(release / 'stage-enabled.json', enabled)
    write_new(release / 'stage-disabled.json', disabled)
    base.migrate(release / 'god2-server.candidate.exe', release / 'stage-enabled.json', release / 'migration-first.log')
    after = capture(release / 'town-diagnostic-accounts.db')
    sql = migration_sql()
    require50(before, after, sql)
    base.migrate(release / 'god2-server.candidate.exe', release / 'stage-enabled.json', release / 'migration-repeat.log')
    require(capture(release / 'town-diagnostic-accounts.db') == after, 'Repeat migration changed saved data/history/schema')
    base.migrate(release / 'god2-server.candidate.exe', release / 'stage-disabled.json', release / 'migration-disabled50.log')
    require(capture(release / 'town-diagnostic-accounts.db') == after, 'Disabled gameplay reopen changed schema50/data')
    write_new(release / 'database-stage-before.json', before)
    write_new(release / 'database-stage-after.json', after)
    write_new(release / 'config-disabled.json', announcement_config(config, False))
    write_new(release / 'config-enabled.json', announcement_config(config, True))
    qualify_inputs(args)
    require(sha(managed.ACTIVE) == sha(release / 'god2-server.before.exe') and
            sha(managed.CONFIG) == sha(release / 'server-config.before.json'), 'Formal code/config changed during stage')
    assert_resources(resources)
    artifacts = {p.relative_to(release).as_posix(): sha(p) for p in release.rglob('*') if p.is_file()}
    info = {'format': FORMAT, 'stage_qualified': True, 'formal_native_qualified': True,
            'release_tool_path': str(Path(__file__).resolve()), 'release_tool_sha256': sha(__file__),
            'candidate_original_path': str(candidate), 'candidate_sha256': sha(candidate),
            'contract_original_path': str(contract_path), 'contract_sha256': sha(contract_path),
            'receipt_original_path': str(receipt_path), 'receipt_sha256': sha(receipt_path),
            'database': str(database), 'database_replaced': False, 'active': str(managed.ACTIVE.resolve()),
            'config': str(managed.CONFIG.resolve()), 'client_sha256': sha(managed.CLIENT),
            'old_server_sha256': sha(managed.ACTIVE), 'config_sha256': sha(managed.CONFIG),
            'frozen_chat': guard, 'sql50_sha256': hashlib.sha256(sql.encode()).hexdigest(),
            'artifacts': artifacts, 'source_snapshot_map': snapshot_map, 'resources_preserved': resources,
            'disabled_schema50_reopen_qualified': True,
            'recovery': 'Retain50CompatibleCandidateAndSave_DisableAnnouncement_ForwardRepair_NoInverse'}
    write_new(release / 'manifest.json', info)
    return info


def qualify_stage(args):
    candidate, contract_path, contract, receipt_path, receipt = qualify_inputs(args)
    release = rooted(args.release)
    info = read(release / 'manifest.json')
    require(info.get('format') == FORMAT and info.get('stage_qualified') is True and
            info.get('formal_native_qualified') is True and info.get('disabled_schema50_reopen_qualified') is True, 'Stage unqualified')
    require(info.get('release_tool_path') == str(Path(__file__).resolve()) and info.get('release_tool_sha256') == sha(__file__),
            'Release helper identity changed')
    require(info['candidate_sha256'] == sha(candidate) and info['contract_sha256'] == sha(contract_path) and
            info['receipt_sha256'] == sha(receipt_path), 'Staged code/contract/receipt differs')
    for name, expected in info['artifacts'].items():
        require(sha(artifact_path(release, name)) == expected, 'Stage artifact changed: ' + name)
    for name, expected in (('god2-server.candidate.exe', info['candidate_sha256']), ('contract.json', info['contract_sha256']),
                           ('native-receipt.json', info['receipt_sha256']), ('god2-server.before.exe', info['old_server_sha256']),
                           ('server-config.before.json', info['config_sha256'])):
        require(info['artifacts'].get(name) == expected, 'Stage manifest/copy identity differs: ' + name)
    require(set(info['source_snapshot_map']) == set(contract['source_sha256']), 'Source snapshot closure differs')
    for source, name in info['source_snapshot_map'].items():
        require(info['artifacts'].get(name) == contract['source_sha256'][source], 'Staged source pin differs: ' + source)
    require(info['frozen_chat'] == base.freeze_gate(), 'Frozen gate changed')
    config, database = base.configured_database()
    require(str(database) == info['database'] and str(managed.ACTIVE.resolve()) == info['active'] and
            str(managed.CONFIG.resolve()) == info['config'], 'Formal targets changed')
    require(sha(managed.CONFIG) == info['config_sha256'] and sha(managed.ACTIVE) == info['old_server_sha256'] and
            sha(managed.CLIENT) == info['client_sha256'], 'Formal code/config/client changed since stage')
    require(exact_json(read(release / 'config-enabled.json'), announcement_config(config, True)) and
            exact_json(read(release / 'config-disabled.json'), announcement_config(config, False)), 'Stage activation config differs')
    assert_resources(info['resources_preserved'])
    before, template = read(release / 'database-stage-before.json'), read(release / 'database-stage-after.json')
    require(capture(release / 'stage-before.db') == before and capture(release / 'town-diagnostic-accounts.db') == template,
            'Stage clone fingerprints changed')
    sql = migration_sql()
    require(hashlib.sha256(sql.encode()).hexdigest() == info['sql50_sha256'], 'Migration50 SQL changed')
    require50(before, template, sql)
    return info, config, database, template, receipt


def recovery_start_guard(info, original_config, database, candidate_installed, fresh):
    expected_binary = info['candidate_sha256'] if candidate_installed else info['old_server_sha256']
    require(sha(managed.ACTIVE) == expected_binary, 'Recovery binary identity differs; no restart')
    config, current_database = base.configured_database()
    expected_config = announcement_config(original_config, False) if candidate_installed else original_config
    require(exact_json(config, expected_config) and current_database == Path(database).resolve() == Path(info['database']).resolve(),
            'Recovery exact config/save target differs; no restart')
    assert_resources(info['resources_preserved'])
    state = capture(current_database)
    versions = [row[0] for row in state['history']]
    require(versions == list(range(1, 50)) or (candidate_installed and versions == list(range(1, 51))),
            'Recovery incompatible migration history; no restart')
    if versions == list(range(1, 51)):
        require(state['history'][:-1] == fresh['history'] and state['history49_typed'] == fresh['history49_typed'] and
                state['history'][-1][:3] == [50, MIGRATION_NAME, migration_sql()], 'Recovery schema50 identity differs')
        require([row for row in state['schema'] if row[2] in NEW_TABLES] == expected_addition(migration_sql()),
                'Recovery schema50 DDL differs')
    else:
        require49(state)
        require(state['history'] == fresh['history'] and state['history49_typed'] == fresh['history49_typed'],
                'Recovery schema49 identity differs')


def apply(args):
    require(args.execute is True, 'Live apply requires explicit --execute after root review')
    info, config, database, template, _ = qualify_stage(args)
    release = rooted(args.release)
    require(not (release / 'apply-started.json').exists(), 'Prior attempt retained; forward repair required')
    base.assert_formal_environment()
    assert_resources(info['resources_preserved'])
    pid = managed_links.managed_listener()  # Exact process/config identity and idle loopback2592.
    write_new(release / 'apply-started.json', {'owned_idle_pid': pid, 'database_replaced': False, 'resources_changed': False})
    stopped = candidate_installed = start_requested = False
    fresh = None
    try:
        try:
            managed_links.stop_idle(pid)
            stopped = True
        except BaseException:
            managed.powershell(managed_links.process_guard_script() +
                "$owned=@(Get-Process -Name 'god2-server' -ErrorAction SilentlyContinue|Where-Object Path -eq $active); "
                "if($owned.Count){throw 'Owned process still running after stop failure; no recovery restart'}")
            stopped = True
            raise
        # The fresh post-shutdown save is authoritative; stage clone is never installed.
        base.backup_new(database, release / 'install-fresh-before.db')
        fresh = capture(release / 'install-fresh-before.db')
        require49(fresh)
        require(capture(database) == fresh, 'Save changed after owned server stopped')
        write_new(release / 'database-install-before.json', fresh)
        qualify_stage(args)  # No writes before exact source/code/config/frozen/resource requalification.
        managed_links.install_binary(release / 'god2-server.candidate.exe', info['candidate_sha256'])
        candidate_installed = True
        base.atomic_config(managed.CONFIG, announcement_config(config, True))
        base.migrate(managed.ACTIVE, managed.CONFIG, release / 'migration-install.log')
        installed = capture(database)
        require50(fresh, installed, migration_sql(), template)
        write_new(release / 'database-install-after.json', installed)
        require(sha(managed.CLIENT) == info['client_sha256'], 'Client changed during install')
        assert_resources(info['resources_preserved'])
        require(base.freeze_gate() == info['frozen_chat'], 'Frozen gate changed during install')
        start_requested = True
        managed.start()
        new_pid = managed_links.wait_listener()
        require(sha(managed.ACTIVE) == info['candidate_sha256'] and
                exact_json(read(managed.CONFIG), announcement_config(config, True)), 'Started binary/config differs')
        result = {'accepted': True, 'formal_installed': True, 'owned_pid': new_pid,
                  'candidate_sha256': info['candidate_sha256'], 'contract_sha256': info['contract_sha256'],
                  'native_receipt_sha256': info['receipt_sha256'], 'database_replaced': False, 'migration': 50,
                  'fresh_before_preserved': True, 'resources_changed': False, 'announcement_enabled': True,
                  'no_gameplay_grants': True, 'current_client_post_promotion_pending': True}
        write_new(release / 'apply-result.json', result)
        return result
    except BaseException as error:
        result = {'accepted': False, 'error': str(error), 'database_replaced': False, 'resources_changed': False,
                  'candidate_retained': candidate_installed, 'manual_forward_repair_required': True,
                  'schema_downgraded': False, 'announcement_disabled_config': False,
                  'announcement_disabled_runtime': False, 'service_restarted': False}
        try:
            if candidate_installed:
                base.atomic_config(managed.CONFIG, announcement_config(config, False))
                result['announcement_disabled_config'] = True
            if stopped:
                if fresh is None:
                    fresh = capture(database)
                    require49(fresh)
                if start_requested:
                    try:
                        recovery_pid = managed_links.managed_listener()
                    except (ValueError, subprocess.CalledProcessError):
                        recovery_pid = None
                    if recovery_pid is not None:
                        require(candidate_installed and sha(managed.ACTIVE) == info['candidate_sha256'], 'Recovery process identity differs')
                        managed_links.stop_idle(recovery_pid)
                # An active player or unqualified live process always prevents a restart.
                managed.powershell(managed_links.process_guard_script() +
                    "$owned=@(Get-Process -Name 'god2-server' -ErrorAction SilentlyContinue|Where-Object Path -eq $active); "
                    "if($owned.Count){throw 'Owned process still running; no recovery restart'}")
                recovery_start_guard(info, config, database, candidate_installed, fresh)
                managed.start()
                result['owned_pid'] = managed_links.wait_listener()
                result['service_restarted'] = True
                result['announcement_disabled_runtime'] = candidate_installed
        except BaseException as recovery:
            result['recovery_error'] = str(recovery)
        write_new(release / 'apply-failed.json', result)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inspect', 'stage', 'qualify', 'apply'), nargs='?', default='inspect')
    for name in ('candidate', 'contract', 'receipt', 'release'):
        parser.add_argument('--' + name)
    parser.add_argument('--execute', action='store_true', help='Root-reviewed live application only')
    args = parser.parse_args()
    if args.command == 'inspect':
        config, database = base.configured_database()
        result = {'format': FORMAT, 'read_only': True, 'database': str(database),
                  'schema_versions': [row[0] for row in capture(database)['history']],
                  'announcement_config': config.get('world', {}).get('owned_guild_announcements'),
                  'resources_preserved': assert_resources(), 'formal_installed': False}
    else:
        require(args.release, '--release required')
        if args.command == 'stage':
            result = stage(args)
        elif args.command == 'qualify':
            info, _, _, _, _ = qualify_stage(args)
            result = {'accepted': True, 'candidate_sha256': info['candidate_sha256'], 'formal_native_qualified': True}
        else:
            result = apply(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
