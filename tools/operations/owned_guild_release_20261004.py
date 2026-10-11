"""CUSTOM-0078 release preparation; no live mutation unless `apply --execute`.

Never restore a stage/backup database over a save, never downgrade migration49.
Stage migrates only a fresh SQLite backup clone. Apply captures a new baseline
AFTER the idle managed server has stopped and migrates the original save in place.
On failure retain the 49-compatible binary and disabled entry for forward repair.
This file does not implement an inverse migration or grant gameplay fixtures.
"""
import argparse
from contextlib import closing
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import struct
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.operations import packet_links_release_20260930 as managed_links
from tools.operations import native_quest_catalog_release as managed
from tools.operations import verify_frozen_chat_20260927 as frozen

ROOT = Path(__file__).resolve().parents[2]
FORMAT = 'owned-guild-release-20261004-v1'
BUNDLE = 'CUSTOM-0078-2996-v1'
MIGRATION_NAME = 'owned_player_guild_membership_candidate'
SCHEMA_SOURCE = 'src/db/SqliteOwnedGuildMembershipRepository.cpp'
NEW_TABLES = {'owned_guild_governance_0078', 'owned_guild_applications_0078'}
LAB_ENV = ('GOD2_NATIVE_WORLD_RECORDS_LAB', 'GOD2_NATIVE_GUILD_MEMBERSHIP_LAB',
           'GOD2_NATIVE_GUILD_ENTRY_LAB')
RESOURCE_DIR = ROOT / 'artifacts/research/native-guild-membership-0078/entry-resource-parser-v01'
RESOURCES = (
    ('MultiMessage03.csvZ', 'MultiMessage03-custom2996.csvZ',
     'e0551afec2108f478f27f2364bd15bd8d7ff999c8f12a087b320d06d23659e4d',
     '20b0636e77e1ad72eb1d98c7a82e893b45db155982dc63ba6f6f16cd8195377d'),
    ('MultiMessage03-gb.csvZ', 'MultiMessage03-gb-custom2996.csvZ',
     '27b0110a305dedf2a617fc4661c4c60868ca3dc7fd5a8e5ff8f8ff1f58165e9b',
     'ba31e53de24ec100c6e98231bc37daeb8e2ec11c1f1a76abf53e14c7429432fd'),
)


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text('utf-8-sig'))


def write_new(path, data):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def rooted(path):
    path = Path(path)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def quoted(value):
    return '"' + value.replace('"', '""') + '"'


def typed_row(row):
    output = bytearray()
    for value in row:
        if value is None:
            data = b'N'
        elif isinstance(value, bytes):
            data = b'B' + value
        elif isinstance(value, str):
            data = b'T' + value.encode('utf-8')
        elif isinstance(value, int):
            data = b'I' + struct.pack('<q', value)
        elif isinstance(value, float):
            data = b'F' + struct.pack('<d', value)
        else:
            raise ValueError('Unknown SQLite storage type')
        output.extend(struct.pack('<Q', len(data)))
        output.extend(data)
    return bytes(output)


def fingerprint(db, table, where=''):
    rows = sorted(typed_row(row) for row in db.execute('SELECT * FROM ' + quoted(table) + where))
    digest = hashlib.sha256()
    for row in rows:
        digest.update(struct.pack('<Q', len(row)))
        digest.update(row)
    return {'rows': len(rows), 'sha256': digest.hexdigest()}


def capture_connection(db):
    require(db.execute('PRAGMA quick_check').fetchall() == [('ok',)], 'SQLite quick_check failed')
    require(not db.execute('PRAGMA foreign_key_check').fetchall(), 'SQLite FK check failed')
    schema = [list(row) for row in db.execute(
        'SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name')]
    names = [row[1] for row in schema if row[0] == 'table']
    require('schema_migrations' in names, 'Missing migration history')
    return {
        'schema': schema,
        'tables': {name: fingerprint(db, name) for name in names},
        'history': [list(row) for row in db.execute(
            'SELECT version,name,sql_text,applied_at FROM schema_migrations ORDER BY version')],
        # Includes unknown columns in old migration rows, not just four known columns.
        'history48_typed': fingerprint(db, 'schema_migrations', ' WHERE version<=48'),
        'pragmas': {key: db.execute('PRAGMA ' + key).fetchone()[0]
                    for key in ('application_id', 'user_version', 'encoding')},
    }


def capture(path):
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        return capture_connection(db)


def backup_new(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    require(source != target and source.is_file() and not target.exists(), 'Backup must be a new independent file')
    with target.open('xb'):
        pass
    with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as db:
        with closing(sqlite3.connect(target)) as output:
            db.backup(output)
    require(capture(target)['pragmas'] == capture(source)['pragmas'], 'Backup metadata differs')


def migration_sql():
    source = (ROOT / SCHEMA_SOURCE).read_text('utf-8')
    found = re.search(r'SqliteOwnedGuildMembershipRepository::schema\(\)\s*\{\s*return R"SQL\((.*?)\)SQL";', source, re.S)
    require(found, 'Exact migration49 SQL not found')
    return found.group(1)


def require48(state):
    require([row[0] for row in state['history']] == list(range(1, 49)), 'Expected exact history1..48')
    require(not NEW_TABLES.intersection(state['tables']), 'Migration49 already exists; no downgrade or reapply')
    require('sqlite_sequence' in state['tables'], 'Expected existing AUTOINCREMENT sequence table')


def expected_addition(sql):
    with closing(sqlite3.connect(':memory:')) as db:
        db.executescript(sql)
        return [list(row) for row in db.execute(
            'SELECT type,name,tbl_name,sql FROM sqlite_master WHERE tbl_name IN (?,?) ORDER BY type,name',
            tuple(sorted(NEW_TABLES)))]


def require49(before, after, sql, template=None):
    require48(before)
    require(set(after['tables']) == set(before['tables']) | NEW_TABLES, 'Unexpected migration49 table set')
    addition = [row for row in after['schema'] if row[2] in NEW_TABLES]
    require(addition == expected_addition(sql), 'Migration49 DDL/index differs from exact qualified SQL')
    require([row for row in after['schema'] if row[2] not in NEW_TABLES] == before['schema'],
            'Existing table/index/trigger/schema changed')
    require(len(after['history']) == 49 and after['history'][:-1] == before['history'], 'Old migration history changed')
    require(after['history'][-1][:3] == [49, MIGRATION_NAME, sql], 'Migration49 identity/SQL differs')
    require(after['history48_typed'] == before['history48_typed'], 'Old typed migration rows/unknown columns changed')
    require(after['pragmas'] == before['pragmas'], 'SQLite metadata changed')
    for table, value in before['tables'].items():
        if table != 'schema_migrations':
            require(after['tables'][table] == value, 'Saved typed rows changed: ' + table)
    require(all(after['tables'][table]['rows'] == 0 for table in NEW_TABLES), 'Migration granted gameplay data')
    if template is not None:
        require(addition == [row for row in template['schema'] if row[2] in NEW_TABLES], 'Install DDL differs from stage')
        require(after['history'][-1][:3] == template['history'][-1][:3], 'Install SQL differs from stage')


def validate_contract(contract_path, candidate):
    contract = read(contract_path)
    require(contract.get('design') == 'CUSTOM-0078', 'Wrong release design')
    require(rooted(contract['candidate_path']) == Path(candidate).resolve(), 'Candidate path differs from contract')
    require(sha(candidate) == contract['candidate_sha256'], 'Candidate code differs from contract')
    closure = contract.get('source_sha256')
    require(isinstance(closure, dict) and closure, 'Missing exact source closure')
    require(SCHEMA_SOURCE in closure and 'src/db/Migration.cpp' in closure and 'src/core/Application.cpp' in closure,
            'Required runtime/migration closure missing')
    for path, expected in closure.items():
        require(sha(rooted(path)) == expected, 'Source closure changed: ' + path)
    require(sha(rooted(contract['helper_path'])) == contract['helper_sha256'], 'Native acceptance helper changed')
    for _, filename, _, expected in RESOURCES:
        path = RESOURCE_DIR / filename
        relative = path.relative_to(ROOT).as_posix()
        require(closure.get(relative) == expected and sha(path) == expected, 'Qualified resource missing from closure')
    return contract


def true_fields(value, fields, label):
    for field in fields:
        require(value.get(field) is True, label + ' missing true guard: ' + field)


def exact_json(left, right):
    # Python equality treats true/1 and 0/0.0 as equal; config proof must not.
    return json.dumps(left, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False) == \
        json.dumps(right, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def validate_formal_config_proof(proof, contract, locale):
    require(isinstance(proof, dict), 'Missing formal config proof')
    true_fields(proof, ('accepted', 'all_other_gameplay_flags_preserved'), 'Formal config proof')
    source_path = rooted(proof.get('source_path', ''))
    require(source_path == managed.CONFIG.resolve(), 'Formal config source target differs')
    source_key = source_path.relative_to(ROOT).as_posix()
    require(contract['source_sha256'].get(source_key) == proof.get('source_sha256')
            and sha(source_path) == proof['source_sha256'], 'Formal config source pin differs')
    source, actual = proof.get('source'), proof.get('actual')
    require(isinstance(source, dict) and exact_json(source, read(source_path)) and isinstance(actual, dict),
            'Formal config proof source/actual differs')
    private_path = Path(proof.get('private_path', ''))
    require(private_path.is_absolute(), 'Formal private config path must be absolute')
    expected = deepcopy(source)
    expected['database']['path'] = str(private_path.with_name('town-diagnostic-accounts.db'))
    expected['logging']['file'] = str(private_path.with_name('server.log'))
    expected['server'].update(host='127.0.0.1', port=2598, character_port=0)
    expected['development']['diagnostic_remote_actor_language'] = int(locale == 936)
    expected['world']['owned_guild_membership'] = {'enabled': True, 'entry_resource_bundle': BUNDLE}
    require(exact_json(actual, expected), 'Formal config changed unrelated gameplay flags')
    require(actual['world']['owned_guild_membership'].get('enabled') is True,
            'Formal entry enablement must be true')
    require(type(actual['server']['port']) is int and type(actual['server']['character_port']) is int
            and type(actual['development']['diagnostic_remote_actor_language']) is int,
            'Formal config numeric proof types differ')


def validate_receipt(receipt, contract, contract_sha):
    true_fields(receipt, ('accepted', 'formal_config', 'env_lab_false', 'candidate_unchanged',
        'protected_files_unchanged', 'protected_DB_exact', 'frozen_unchanged',
        'protected_processes_exact', 'desktop_unchanged', 'foreground_unchanged'), 'Formal acceptance')
    require(receipt.get('contract_sha256') == contract_sha, 'Receipt contract binding differs')
    require(receipt.get('sources_before') == contract['source_sha256'] == receipt.get('sources_after'),
            'Native acceptance source closure differs')
    for before, after in (('files_before', 'files_after'), ('frozen_before', 'frozen_after'),
                          ('protected_DB_before', 'protected_DB_after'), ('protected_processes_before', 'protected_processes_after')):
        require(isinstance(receipt.get(before), dict) and receipt[before] and receipt[before] == receipt.get(after),
                'Acceptance preservation differs: ' + before)
    cases = receipt.get('cases')
    require(isinstance(cases, list) and len(cases) == 2 and {c.get('locale') for c in cases} == {950, 936},
            'Both exact native locales required')
    for case in cases:
        true_fields(case, ('accepted', 'formal_config', 'env_lab_false', 'private_files_unchanged', 'all_private_images_closed',
                         'all_owned_processes_closed', 'exclusive_2598_released'), 'Native case')
        runtime = case.get('runtime_configured_log')
        require(isinstance(runtime, str) and 'OWNED_GUILD_RUNTIME ' in runtime
                and 'enabled=true ordinary_entry=true lab=false schema=49 CUSTOM-0078' in runtime,
                'Formal configured runtime log differs')
        validate_formal_config_proof(case.get('formal_config_proof'), contract, case['locale'])
        environment = case.get('environment_proof', {})
        for name in ('launch_lab_values', 'observed_server_lab_values'):
            values = environment.get(name)
            require(isinstance(values, dict) and set(values) == set(LAB_ENV)
                    and all(value is None for value in values.values()), 'Formal environment proof differs: ' + name)
        require(type(case.get('runner_exit')) is int and case['runner_exit'] == 0, 'Actual native runner failed')
        ui = case.get('ui', {})
        true_fields(ui, ('accepted', 'env_lab_false', 'ordinary_paired_entry_accepted', 'desktop_unchanged',
                         'all_clients_closed', 'all_loaders_closed'), 'Native UI')
        require(ui.get('locale') == case['locale'], 'UI locale mismatch')
        require(exact_json(ui.get('formal_config_proof'), case['formal_config_proof']), 'UI formal config proof differs')
        for name in ('native_loaded_resource_proof', 'ordinary_menu_events', 'real_create',
                     'real_pending_application', 'real_native_71_approve', 'ordinary_member_leave_events',
                     'real_native_72_reject'):
            require(ui.get(name), 'Native workflow evidence missing: ' + name)
        loaded = ui['native_loaded_resource_proof']
        true_fields(loaded, ('original2995_all_rows_byte_exact', 'VM_READ_only'), 'Loaded resources')
        require(loaded.get('count') == 2996 and loaded.get('locale') == case['locale']
                and len(loaded.get('new2996_rows', {}).get('rows_hex', [])) == 4,
                'Native resource table/rows differ')
        for name in ('real_create', 'real_pending_application', 'real_native_71_approve', 'real_native_72_reject'):
            true_fields(ui[name], ('accepted',), 'SQL/native workflow ' + name)
        require(isinstance(ui['ordinary_member_leave_events'], list)
                and len(ui['ordinary_member_leave_events']) == 1, 'Expected one qualified ordinary leave')
        true_fields(ui['ordinary_member_leave_events'][0], ('accepted', 'cancel_SQL_exact',
                    'owner_only_membership_deleted', 'pending6_exact', 'governance_exact',
                    'all_unrelated_tables_exact', 'native_2D_name_empty', 'all_panels_closed'), 'Ordinary leave')
    return receipt


def freeze_gate():
    frozen.main()
    return {'baseline_sha256': sha(frozen.BASELINE), 'source_sha256': frozen.hashes()}


def configured_database():
    config = read(managed.CONFIG)
    require(config['server']['host'] == '127.0.0.1' and config['server']['port'] == 2592
            and config['server'].get('character_port', 0) == 0 and config['database']['type'] == 'sqlite',
            'Formal managed target differs')
    database = rooted(config['database']['path'])
    require(database.is_file(), 'Formal save missing')
    return config, database


def entry_config(config, enabled):
    result = deepcopy(config)
    result.setdefault('world', {})['owned_guild_membership'] = {'enabled': bool(enabled), 'entry_resource_bundle': BUNDLE}
    return result


def clean_environment():
    return {key: value for key, value in os.environ.items() if key not in LAB_ENV}


def migrate(binary, config, log):
    with Path(log).open('xb') as output:
        subprocess.run([str(binary), '--config', str(config), '--migrate-only'], cwd=ROOT,
                       env=clean_environment(), stdout=output, stderr=subprocess.STDOUT, check=True,
                       timeout=90, creationflags=managed.FLAGS)


def atomic_bytes(path, data):
    path = Path(path)
    handle, name = tempfile.mkstemp(prefix='owned-guild-', dir=path.parent)
    try:
        with os.fdopen(handle, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def atomic_config(path, value):
    atomic_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def install_pair(items, replace=os.replace):
    """All targets prechecked, all copies hashed, rollback BOTH on partial failure.

    Caller must keep entry disabled and clients closed. items=(target,source,
    old_hash,new_hash). No database or executable is touched by this function.
    """
    require(len(items) == 2 and len({Path(item[0]).resolve() for item in items}) == 2, 'Expected two distinct resources')
    originals, temporary = {}, []
    for target, source, old_hash, new_hash in items:
        require(sha(target) == old_hash and sha(source) == new_hash, 'Resource original/candidate pin differs')
        originals[Path(target)] = Path(target).read_bytes()
    try:
        for target, source, _, new_hash in items:
            handle, name = tempfile.mkstemp(prefix='owned-guild-pair-', dir=Path(target).parent)
            os.close(handle)
            temporary.append(Path(name))
            shutil.copy2(source, name)
            require(sha(name) == new_hash, 'Resource temp copy changed')
        # Recheck both immediately before first replacement.
        require(all(sha(target) == old for target, _, old, _ in items), 'Resources changed during staging')
        for (target, _, _, _), temp in zip(items, temporary):
            replace(temp, Path(target))
        require(all(sha(target) == new for target, _, _, new in items), 'Installed resource pair differs')
    except BaseException:
        # This restores resources only, never an old database or executable.
        for target, data in originals.items():
            atomic_bytes(target, data)
        require(all(sha(target) == old for target, _, old, _ in items), 'Resource pair rollback incomplete; entry must remain disabled')
        raise
    finally:
        for temp in temporary:
            temp.unlink(missing_ok=True)


def resource_items(client_root):
    return [(Path(client_root) / 'Data2/Patch/Comm' / target, RESOURCE_DIR / source, old, new)
            for target, source, old, new in RESOURCES]


def qualify_inputs(args, *, need_receipt):
    require(args.candidate and args.contract, 'Candidate and contract are required')
    candidate, contract_path = rooted(args.candidate), rooted(args.contract)
    contract = validate_contract(contract_path, candidate)
    receipt = None
    if args.receipt:
        receipt = validate_receipt(read(rooted(args.receipt)), contract, sha(contract_path))
        require(receipt['files_before'].get('client') == sha(managed.CLIENT), 'Accepted client differs from current client')
        for path, expected in receipt['frozen_before'].items():
            require(sha(rooted(path)) == expected, 'Frozen acceptance dependency changed: ' + path)
    require(receipt is not None or not need_receipt, 'Exact formal native acceptance receipt is required')
    return candidate, contract_path, contract, receipt


def stage(args):
    candidate, contract_path, contract, receipt = qualify_inputs(args, need_receipt=False)
    release = rooted(args.release)
    require(not release.exists(), 'Choose an unused release directory')
    config, database = configured_database()
    guard = freeze_gate()
    items = resource_items(managed.CLIENT.parent)
    for target, source, old, new in items:
        require(sha(target) == old and sha(source) == new, 'Paired bundle source pins differ')
    release.mkdir(parents=True, exist_ok=False)
    sources = [(candidate, 'god2-server.candidate.exe'), (managed.ACTIVE, 'god2-server.before.exe'),
               (managed.CONFIG, 'server-config.before.json'), (contract_path, 'contract.json')]
    if args.receipt:
        sources.append((rooted(args.receipt), 'native-receipt.json'))
    for target, source, _, _ in items:
        sources.extend(((target, target.name + '.before'), (source, target.name + '.candidate')))
    for source, name in sources:
        shutil.copy2(source, release / name)
    backup_new(database, release / 'stage-before.db')
    before = capture(release / 'stage-before.db')
    require48(before)
    backup_new(release / 'stage-before.db', release / 'stage-migration.db')
    migrate_config = entry_config(config, False)
    migrate_config['database']['path'] = str(release / 'stage-migration.db')
    migrate_config.setdefault('logging', {})['file'] = str(release / 'stage-server.log')
    write_new(release / 'stage-config.json', migrate_config)
    migrate(release / 'god2-server.candidate.exe', release / 'stage-config.json', release / 'migration-first.log')
    after = capture(release / 'stage-migration.db')
    sql = migration_sql()
    require49(before, after, sql)
    migrate(release / 'god2-server.candidate.exe', release / 'stage-config.json', release / 'migration-repeat.log')
    require(capture(release / 'stage-migration.db') == after, 'Repeat migration changed data/history/schema')
    write_new(release / 'database-stage-before.json', before)
    write_new(release / 'database-stage-after.json', after)
    write_new(release / 'config-disabled.json', entry_config(config, False))
    write_new(release / 'config-enabled.json', entry_config(config, True))
    artifacts = {p.name: sha(p) for p in release.iterdir() if p.is_file()}
    info = {'format': FORMAT, 'stage_qualified': True, 'formal_native_qualified': receipt is not None,
            'candidate_original_path': str(candidate), 'candidate_sha256': sha(candidate),
            'contract_original_path': str(contract_path), 'contract_sha256': sha(contract_path),
            'receipt_original_path': str(rooted(args.receipt)) if args.receipt else None,
            'database': str(database), 'database_replaced': False, 'active': str(managed.ACTIVE.resolve()),
            'config': str(managed.CONFIG.resolve()), 'client_sha256': sha(managed.CLIENT),
            'old_server_sha256': sha(managed.ACTIVE), 'config_sha256': sha(managed.CONFIG),
            'frozen_chat': guard, 'sql49_sha256': hashlib.sha256(sql.encode()).hexdigest(),
            'artifacts': artifacts, 'resources': [[str(t), t.name + '.before', t.name + '.candidate', old, new]
                                               for t, _, old, new in items],
            'recovery': 'Retain49CompatibleCandidateAndSave_DisableEntry_ForwardRepair_NoInverse',
            'native_acceptance': 'qualified' if receipt else 'PENDING_NO_APPLY'}
    write_new(release / 'manifest.json', info)
    return info


def qualify_stage(args, *, apply=False):
    candidate, contract_path, contract, receipt = qualify_inputs(args, need_receipt=apply)
    release = rooted(args.release)
    info = read(release / 'manifest.json')
    require(info.get('format') == FORMAT and info.get('stage_qualified') is True, 'Wrong/unqualified stage')
    require(info['candidate_sha256'] == sha(candidate) and info['contract_sha256'] == sha(contract_path), 'Staged code/contract changed')
    for name, expected in info['artifacts'].items():
        require(Path(name).name == name and sha(release / name) == expected, 'Stage artifact changed: ' + name)
    require(info['artifacts'].get('god2-server.candidate.exe') == info['candidate_sha256']
            and info['artifacts'].get('contract.json') == info['contract_sha256']
            and info['artifacts'].get('god2-server.before.exe') == info['old_server_sha256']
            and info['artifacts'].get('server-config.before.json') == info['config_sha256'],
            'Manifest/copy identities disagree')
    expected_resources = [[str(target), target.name + '.before', target.name + '.candidate', old, new]
                          for target, _, old, new in resource_items(managed.CLIENT.parent)]
    require(info['resources'] == expected_resources, 'Manifest resource targets/pins differ from qualified pair')
    for _, original, replacement, old, new in expected_resources:
        require(info['artifacts'].get(original) == old and info['artifacts'].get(replacement) == new,
                'Staged resource originals/replacements differ')
    require(info['frozen_chat'] == freeze_gate(), 'Frozen chat baseline changed')
    config, database = configured_database()
    require(str(database) == info['database'] and str(managed.ACTIVE.resolve()) == info['active']
            and str(managed.CONFIG.resolve()) == info['config'], 'Formal targets changed')
    require(sha(managed.CONFIG) == info['config_sha256'] and sha(managed.ACTIVE) == info['old_server_sha256']
            and sha(managed.CLIENT) == info['client_sha256'], 'Working config/code/client changed since stage')
    for target, _, _, old, _ in info['resources']:
        require(sha(target) == old, 'Working resource changed since stage')
    before, template = read(release / 'database-stage-before.json'), read(release / 'database-stage-after.json')
    require(capture(release / 'stage-before.db') == before and capture(release / 'stage-migration.db') == template,
            'Stage clone fingerprints changed')
    require49(before, template, migration_sql())
    # Live SAVE ROWS intentionally need not equal the early stage baseline.
    return info, config, database, template, receipt


def assert_clients_closed():
    client = str(managed.CLIENT.resolve()).replace("'", "''")
    managed.powershell("$ErrorActionPreference='Stop'; $client='" + client + "'; "
        "$running=@(Get-Process -ErrorAction SilentlyContinue|Where-Object {$_.Path -eq $client}); "
        "if($running.Count){throw 'Close working clients before paired resource installation'}")


def assert_formal_environment():
    # Migration subprocess strips lab values; scheduled formal launch must not
    # inherit a persistent machine/user lab override. No environment is changed.
    require(not any(os.environ.get(key) for key in LAB_ENV), 'Lab environment present in release process')
    names = ','.join("'" + key + "'" for key in LAB_ENV)
    managed.powershell("$ErrorActionPreference='Stop'; foreach($n in @(" + names + ")) {"
        "foreach($scope in @('User','Machine')) {"
        "if([Environment]::GetEnvironmentVariable($n,$scope)){throw 'Persistent lab environment present'}}}")


def recovery_start_guard(info, original_config, database, candidate_installed):
    """Never restart changed bytes/settings after a failed installation."""
    expected_binary = info['candidate_sha256'] if candidate_installed else info['old_server_sha256']
    require(sha(managed.ACTIVE) == expected_binary, 'Recovery executable pin differs; no restart')
    current_config, current_database = configured_database()
    expected_config = entry_config(original_config, False) if candidate_installed else original_config
    require(exact_json(current_config, expected_config), 'Recovery exact disabled/original config differs; no restart')
    require(current_database == Path(database).resolve() == Path(info['database']).resolve(),
            'Recovery save target differs; no restart')
    if not candidate_installed:
        require(sha(managed.CONFIG) == info['config_sha256'], 'Recovery original config pin differs; no restart')
        require48(capture(current_database))


def apply(args):
    require(args.execute is True, 'Apply requires explicit --execute; default is preparation only')
    info, config, database, template, receipt = qualify_stage(args, apply=True)
    release = rooted(args.release)
    require(not (release / 'apply-started.json').exists(), 'Existing install attempt retained; forward repair required')
    assert_formal_environment()
    assert_clients_closed()
    pid = managed_links.managed_listener()  # Exact PID/image/command/config and idle loopback2592.
    write_new(release / 'apply-started.json', {'owned_idle_pid': pid, 'database_replaced': False})
    stopped = False
    candidate_installed = False
    start_requested = False
    try:
        try:
            managed_links.stop_idle(pid)
            stopped = True
        except BaseException:
            # Stop-ScheduledTask may succeed before a later stop/wait error.
            # Record/recover only if there is no remaining owned process.
            managed.powershell(managed_links.process_guard_script() +
                "$owned=@(Get-Process -Name 'god2-server' -ErrorAction SilentlyContinue|Where-Object Path -eq $active); "
                "if($owned.Count){throw 'Stop failed with owned process still running; manual repair'}")
            stopped = True
            raise
        # Fresh baseline includes final shutdown saves. No use of stage DB for install.
        backup_new(database, release / 'install-fresh-before.db')
        fresh = capture(release / 'install-fresh-before.db')
        require48(fresh)
        require(capture(database) == fresh, 'Save changed after server stopped')
        write_new(release / 'database-install-before.json', fresh)
        qualify_stage(args, apply=True)  # Source/config/resource pins rechecked immediately before writes.
        assert_clients_closed()
        managed_links.install_binary(release / 'god2-server.candidate.exe', info['candidate_sha256'])
        candidate_installed = True
        disabled = entry_config(config, False)
        atomic_config(managed.CONFIG, disabled)
        migrate(managed.ACTIVE, managed.CONFIG, release / 'migration-install.log')
        installed = capture(database)
        require49(fresh, installed, migration_sql(), template)
        write_new(release / 'database-install-after.json', installed)
        items = [(Path(target), release / replacement, old, new)
                 for target, _, replacement, old, new in info['resources']]
        install_pair(items)
        require(sha(managed.CLIENT) == info['client_sha256'], 'Client executable changed')
        require(freeze_gate() == info['frozen_chat'], 'Frozen chat changed during install')
        atomic_config(managed.CONFIG, entry_config(config, True))
        # No lab environment is supplied by the existing hidden scheduled task.
        start_requested = True
        managed.start()
        new_pid = managed_links.wait_listener()
        require(sha(managed.ACTIVE) == info['candidate_sha256'], 'Started binary differs')
        result = {'accepted': True, 'formal_installed': True, 'owned_pid': new_pid,
                  'candidate_sha256': info['candidate_sha256'], 'contract_sha256': info['contract_sha256'],
                  'native_receipt_sha256': sha(rooted(args.receipt)), 'database_replaced': False,
                  'fresh_before_preserved': True, 'migration': 49, 'resource_pair_installed': True,
                  'entry_enabled': True, 'no_gameplay_grants': True}
        write_new(release / 'apply-result.json', result)
        return result
    except BaseException as error:
        # No inverse, no save-file restore, no old48 binary against committed49.
        result = {'accepted': False, 'error': str(error), 'database_replaced': False,
                  'candidate_retained': candidate_installed, 'manual_forward_repair_required': True,
                  'schema_downgraded': False, 'entry_disabled_config': False,
                  'entry_disabled_runtime': False, 'service_restarted': False}
        try:
            if candidate_installed:
                atomic_config(managed.CONFIG, entry_config(config, False))
                result['entry_disabled_config'] = True
            if stopped:
                if not candidate_installed:
                    # Never restart the old48 binary against newly observed49.
                    require48(capture(database))
                    require(sha(managed.ACTIVE) == info['old_server_sha256']
                            and sha(managed.CONFIG) == info['config_sha256'], 'Original availability pins differ')
                if start_requested:
                    # Config edits do not disable an already-running instance.
                    # Restart only an exact candidate that is still idle; an
                    # active player causes refusal and an explicit manual flag.
                    try:
                        recovery_pid = managed_links.managed_listener()
                    except (ValueError, subprocess.CalledProcessError):
                        recovery_pid = None
                    if recovery_pid is not None:
                        require(candidate_installed and sha(managed.ACTIVE) == info['candidate_sha256'],
                                'Recovery running candidate pin differs')
                        managed_links.stop_idle(recovery_pid)
                # Do not kill any newly running process/player after a start failure.
                managed.powershell(managed_links.process_guard_script() +
                    "$owned=@(Get-Process -Name 'god2-server' -ErrorAction SilentlyContinue|Where-Object Path -eq $active); "
                    "if($owned.Count){throw 'Owned process still running; no recovery restart'}")
                recovery_start_guard(info, config, database, candidate_installed)
                managed.start()
                result['owned_pid'] = managed_links.wait_listener()
                result['service_restarted'] = True
                result['entry_disabled_runtime'] = candidate_installed
        except BaseException as recovery:
            result['recovery_error'] = str(recovery)
        write_new(release / 'apply-failed.json', result)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inspect', 'stage', 'qualify', 'apply'), nargs='?', default='inspect')
    parser.add_argument('--candidate')
    parser.add_argument('--contract')
    parser.add_argument('--receipt')
    parser.add_argument('--release')
    parser.add_argument('--execute', action='store_true', help='Required only for live apply after root review')
    args = parser.parse_args()
    if args.command == 'inspect':
        config, database = configured_database()
        result = {'format': FORMAT, 'read_only': True, 'database': str(database),
                  'schema_versions': [row[0] for row in capture(database)['history']],
                  'entry_config': config.get('world', {}).get('owned_guild_membership'),
                  'formal_installed': False, 'client_sha256': sha(managed.CLIENT)}
    else:
        require(args.release, '--release is required')
        if args.command == 'stage':
            result = stage(args)
        elif args.command == 'qualify':
            info, _, _, _, receipt = qualify_stage(args, apply=True)
            result = {'accepted': True, 'candidate_sha256': info['candidate_sha256'], 'formal_native_qualified': receipt is not None}
        else:
            result = apply(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
