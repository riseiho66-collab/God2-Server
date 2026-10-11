"""Stage/apply/verify the qualified 2026-09-30 packet links and migration39.

Stage is read-only toward the managed server and its save. Apply is a separate,
explicit command: it never copies a backup over the live database. A failed
installation may undo only the empty migration39 addition, under a SQLite
writer transaction, while every old row/schema/history still matches the
fresh at-install backup. Otherwise candidate code/data are retained for repair.
"""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.operations import native_quest_catalog_release as managed
from tools.operations import verify_frozen_chat_20260927 as frozen

ROOT = managed.ROOT
CANDIDATE = ROOT / 'build-town-visibility/Release/god2-server-native-results.exe'
ROLE_TABLE = 'character_role_text'
OLD_TABLE_COUNT = 53  # Includes sqlite_sequence; excludes schema_migrations.
FORMAT = 'packet-links-release-20260930-v1'
TCP_MODULES = {
    'test_owned_role_text_server', 'test_pet_reserve_move_server',
    'test_pet2_revert_server', 'test_recovered_dual_connection_server',
    'test_inventory_move_server', 'test_current_world_ready_builder',
}
TCP_TESTS = {
    'test_native_edit_clear_stale_tail_and_restart_both_languages',
    'test_preprojection_mixed_duplicate_and_invalid_encoding_never_write',
    'test_unrepresentable_cross_language_relogin_preserves_saved_unicode',
    'test_native24_mixed_e3_fb_restart', 'test_native24_owned_reserves_restart',
    'test_mixed_d6_batches_reject_before_any_mutation',
    'test_normal_reverts_and_missing_sources_preserve_connection_and_state',
    'test_unprojected_and_truncated_d6_never_mutate_saved_state',
}


class RollbackUnsafe(RuntimeError):
    """Candidate/save must be retained; restoring an old backup is forbidden."""


def require(value, message):
    if not value:
        raise ValueError(message)


def write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.writing')
    with temporary.open('x', encoding='utf-8') as output:
        output.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def read(path):
    return json.loads(Path(path).read_text('utf-8'))


def quoted(identifier):
    return '"' + identifier.replace('"', '""') + '"'


def fingerprint(db, table):
    digests = []
    for row in db.execute('SELECT * FROM ' + quoted(table)):
        digest = hashlib.sha256()
        for value in row:
            if value is None:
                data = b'N'
            elif isinstance(value, bytes):
                data = b'B' + value
            elif isinstance(value, str):
                data = b'T' + value.encode('utf-8')
            elif isinstance(value, int):
                data = b'I' + str(value).encode('ascii')
            else:
                data = b'F' + repr(value).encode('ascii')
            digest.update(len(data).to_bytes(8, 'little'))
            digest.update(data)
        digests.append(digest.digest())
    return {'rows': len(digests), 'sha256': hashlib.sha256(b''.join(sorted(digests))).hexdigest()}


def capture_connection(db):
    require(db.execute('PRAGMA quick_check').fetchall() == [('ok',)], 'SQLite quick_check failed')
    require(not db.execute('PRAGMA foreign_key_check').fetchall(), 'SQLite foreign_key_check failed')
    schema = [list(row) for row in db.execute(
        'SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name')]
    names = [row[1] for row in schema if row[0] == 'table']
    return {
        'schema': schema,
        'history': [list(row) for row in db.execute(
            'SELECT version,name,sql_text,applied_at FROM schema_migrations ORDER BY version')],
        'tables': {table: fingerprint(db, table) for table in sorted(names)},
        'pragmas': {key: db.execute('PRAGMA ' + key).fetchone()[0]
                    for key in ('application_id', 'user_version', 'encoding')},
    }


def capture(path):
    require(Path(path).is_file(), 'Database is missing')
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')  # All table fingerprints belong to one read snapshot.
        return capture_connection(db)


def require38(state):
    require([row[0] for row in state['history']] == list(range(1, 39)),
            'Expected exact consecutive migration history1..38')
    require(ROLE_TABLE not in state['tables'], 'Role text table exists before migration39')
    require(len(state['tables']) - 1 == OLD_TABLE_COUNT,
            'Expected53 existing tables excluding schema_migrations')


def require39(before, after, template=None, *, unchanged=True, empty=True):
    """Allow exactly one new table and history row; old schema/SQL is immutable."""
    require38(before)
    require(set(after['tables']) == set(before['tables']) | {ROLE_TABLE}, 'Unexpected table set after migration39')
    old_schema = [row for row in after['schema'] if row[1] != ROLE_TABLE]
    addition = [row for row in after['schema'] if row[1] == ROLE_TABLE]
    require(old_schema == before['schema'], 'Existing schema changed after migration39')
    require(len(addition) == 1 and addition[0][:3] == ['table', ROLE_TABLE, ROLE_TABLE],
            'Migration39 must add only the role text table')
    require(len(after['history']) == 39 and after['history'][:-1] == before['history'],
            'Old migration history was rewritten')
    require(after['history'][-1][:2] == [39, 'owned_secondary_role_text'], 'Unexpected migration39 identity')
    require(after['pragmas'] == before['pragmas'], 'Database metadata changed')
    if template is not None:
        expected_addition = [row for row in template['schema'] if row[1] == ROLE_TABLE]
        require(addition == expected_addition, 'Role text schema differs from qualified candidate')
        # applied_at is naturally different for stage and install; SQL/name/version are exact.
        require(after['history'][-1][:3] == template['history'][-1][:3], 'Migration39 SQL differs from stage')
    if unchanged:
        changed = changed_old_tables(before, after)
        require(not changed, 'Old saved rows changed: ' + ','.join(changed))
    if empty:
        require(after['tables'][ROLE_TABLE]['rows'] == 0, 'New role text table is not empty')


def changed_old_tables(before, after):
    return [name for name, value in before['tables'].items()
            if name != 'schema_migrations' and value != after['tables'].get(name)]


def all_true(value):
    return value is True or (isinstance(value, dict) and bool(value) and all(v is True for v in value.values()))


def qualify_hidden(path, candidate_sha):
    receipt = read(path)
    require(receipt.get('accepted') is True and receipt.get('runner_exit') == 0, 'Hidden client run did not pass')
    require(receipt.get('candidate_sha256') == candidate_sha, 'Hidden receipt candidate differs')
    for key in ('source_files_unchanged', 'candidate_unchanged', 'copy_unchanged', 'all_owned_processes_closed'):
        require(all_true(receipt.get(key)), 'Hidden receipt missing guard: ' + key)
    before, after = receipt.get('before'), receipt.get('after')
    require(isinstance(before, dict) and before and before == after, 'Hidden source hashes changed')
    require(before.get('live_client') == managed.sha(managed.CLIENT), 'Current client differs from hidden acceptance')
    ui = receipt.get('ui', {})
    for key in ('accepted', 'desktop_unchanged', 'all_clients_closed'):
        require(ui.get(key) is True, 'Hidden UI receipt missing guard: ' + key)
    stages = ui.get('stages', [])
    require(len(stages) == 2 and {(s.get('source'), s.get('destination')) for s in stages} == {(42, 43), (43, 42)}
            and all(s.get('native24_observed') is True for s in stages), 'Both native24 reserve directions required')
    require(ui.get('reconnect', {}).get('saved_unchanged') is True, 'Reserve re-login persistence missing')
    role = ui.get('role_text', {})
    expected, saved = role.get('expected'), role.get('saved')
    require(isinstance(expected, str) and expected and isinstance(saved, list) and len(saved) == 7
            and saved[1] == expected and saved[2] in (936, 950) and saved[3] > 0
            and saved[4] == 'CUSTOM_DESIGNED' and saved[6] == 'CUSTOM-0056', 'Owned role text save proof missing')
    require(role.get('native20_ui_send_observed') is True, 'Native UI20 send missing')
    reconnect = role.get('reconnect', {})
    require(reconnect.get('native23_receive_observed') is True and reconnect.get('saved_unchanged') is True,
            'Native23 re-login receive/persistence missing')
    for native in (role.get('native_after', {}), reconnect.get('native', {})):
        require(all(native.get(key) == expected for key in ('actor_text', 'renderer_text', 'widget7_static')),
                'Native role text consumers disagree')
    return receipt


def qualify_tcp(path, log, candidate_sha):
    receipt = read(path)
    require(receipt.get('candidate_sha256') == candidate_sha, 'TCP receipt candidate differs')
    require(receipt.get('passed') is True and receipt.get('tests_run') == 8
            and receipt.get('errors') == 0 and receipt.get('failures') == 0, 'Eight TCP checks must pass')
    modules = receipt.get('modules', [])
    require(len(modules) == len(TCP_MODULES) and {item.get('module') for item in modules} == TCP_MODULES,
            'TCP module coverage differs')
    for item in modules:
        require(item.get('sha256') == managed.sha(ROOT / 'tests/research' / (item['module'] + '.py')),
                'TCP tested source changed: ' + item['module'])
        require(item.get('python_assert_statements') == 0 and item.get('debug_names') == 0
                and item.get('optimization_does_not_change_bytecode') is True, 'TCP optimized checks not qualified')
    output = Path(log).read_text('utf-8-sig')
    observed = re.findall(r'^(test_\w+) \([^\r\n]+\) \.\.\. ok\s*$', output, re.MULTILINE)
    require(len(observed) == 8 and set(observed) == TCP_TESTS
            and re.search(r'^Ran 8 tests in [\d.]+s\s*\n\s*OK\s*$', output, re.MULTILINE),
            'TCP log does not contain all eight passing tests')
    return receipt


def freeze_gate():
    frozen.main()
    return {'baseline_sha256': managed.sha(frozen.BASELINE), 'source_sha256': frozen.hashes()}


def configured_database():
    config = read(managed.CONFIG)
    require(config['server']['port'] == 2592 and config['server']['host'] == '127.0.0.1'
            and config['server'].get('character_port', 0) == 0 and config['database']['type'] == 'sqlite',
            'Managed config target differs')
    database = Path(config['database']['path'])
    if not database.is_absolute():
        database = ROOT / database
    require(database.is_file(), 'Configured database is missing')
    return config, database.resolve()


def backup_new(source, target, release):
    require(target.resolve().parent == release.resolve() and not target.exists(), 'Backup destination must be a new release artifact')
    require(target.resolve() != Path(source).resolve(), 'Backup cannot target its source')
    managed.backup(Path(source), target)


def migrate(binary, config, log):
    with log.open('xb') as output:
        subprocess.run([str(binary), '--config', str(config), '--migrate-only'], cwd=ROOT,
                       check=True, stdout=output, stderr=subprocess.STDOUT, timeout=60,
                       creationflags=managed.FLAGS)


def stage(args, release):
    require(not release.exists(), 'Release directory already exists; choose a new name')
    candidate_sha = managed.sha(CANDIDATE)
    qualify_hidden(args.hidden_receipt, candidate_sha)
    qualify_tcp(args.tcp_receipt, args.tcp_log, candidate_sha)
    guard = freeze_gate()  # Gate before snapshotting managed artifacts.
    config, database = configured_database()
    hashes = {'candidate_sha256': candidate_sha, 'old_server_sha256': managed.sha(managed.ACTIVE),
              'config_sha256': managed.sha(managed.CONFIG), 'client_sha256': managed.sha(managed.CLIENT)}
    release.mkdir(parents=True, exist_ok=False)
    for source, name in ((managed.ACTIVE, 'god2-server.before.exe'), (CANDIDATE, 'god2-server.candidate.exe'),
                         (managed.CONFIG, 'server-config.before.json'), (args.hidden_receipt, 'hidden-receipt.json'),
                         (args.tcp_receipt, 'tcp-receipt.json'), (args.tcp_log, 'tcp-run.log')):
        shutil.copy2(source, release / name)
    backup_new(database, release / 'accounts.before.db', release)
    before = capture(release / 'accounts.before.db')
    require38(before)
    backup_new(release / 'accounts.before.db', release / 'town-diagnostic-accounts.db', release)
    config['database']['path'] = str(release / 'town-diagnostic-accounts.db')
    config['logging']['file'] = str(release / 'migration.log')
    write(release / 'migration-config.json', config)
    migrate(release / 'god2-server.candidate.exe', release / 'migration-config.json', release / 'migration.stdout.log')
    migrated = capture(release / 'town-diagnostic-accounts.db')
    require39(before, migrated)
    migrate(release / 'god2-server.candidate.exe', release / 'migration-config.json', release / 'migration-second.stdout.log')
    require(capture(release / 'town-diagnostic-accounts.db') == migrated, 'Migration is not idempotent')
    write(release / 'database.before.json', before)
    write(release / 'database.migrated.json', migrated)
    require(managed.sha(CANDIDATE) == candidate_sha and managed.sha(managed.ACTIVE) == hashes['old_server_sha256']
            and managed.sha(managed.CONFIG) == hashes['config_sha256'] and managed.sha(managed.CLIENT) == hashes['client_sha256'],
            'Managed artifacts changed while staging')
    require(guard == freeze_gate(), 'Frozen guard changed while staging')
    qualify_hidden(release / 'hidden-receipt.json', candidate_sha)
    qualify_tcp(release / 'tcp-receipt.json', release / 'tcp-run.log', candidate_sha)
    artifacts = {name: managed.sha(release / name) for name in (
        'god2-server.before.exe', 'god2-server.candidate.exe', 'server-config.before.json',
        'accounts.before.db', 'town-diagnostic-accounts.db', 'database.before.json', 'database.migrated.json',
        'hidden-receipt.json', 'tcp-receipt.json', 'tcp-run.log', 'migration-config.json',
        'migration.stdout.log', 'migration-second.stdout.log')}
    require(artifacts['god2-server.before.exe'] == hashes['old_server_sha256']
            and artifacts['god2-server.candidate.exe'] == candidate_sha
            and artifacts['server-config.before.json'] == hashes['config_sha256'], 'Snapshot file identity differs')
    info = {'format': FORMAT, **hashes, 'database': str(database), 'freeze': guard, 'artifacts': artifacts,
            'database_replacement': False, 'old_tables_verified': OLD_TABLE_COUNT, 'migration': [38, 39],
            'scope': 'Owned reserve24, secondary role text20/23; D6 refusal only, no revert effects',
            'source_receipts': [str(args.hidden_receipt.resolve()), str(args.tcp_receipt.resolve()), str(args.tcp_log.resolve())]}
    write(release / 'manifest.json', info)
    result = {'prepared': True, 'applied': False, 'release': str(release), 'candidate_sha256': candidate_sha,
              'old_tables_unchanged': OLD_TABLE_COUNT, 'old_schema_and_history_unchanged': True,
              'empty_role_text_table': True, 'migration_idempotent': True, 'tcp_passed': 8,
              'hidden_client_accepted': True, 'formal_database_replaced': False}
    write(release / 'prepared.json', result)
    print(json.dumps(result))
    return result


def load_manifest(release):
    info = read(release / 'manifest.json')
    require(info.get('format') == FORMAT and info.get('database_replacement') is False, 'Invalid release manifest')
    _, database = configured_database()
    require(database == Path(info['database']).resolve(), 'Configured database target changed')
    require(info.get('old_tables_verified') == OLD_TABLE_COUNT and info.get('migration') == [38, 39], 'Unexpected migration scope')
    required = {'god2-server.before.exe', 'god2-server.candidate.exe', 'server-config.before.json',
                'accounts.before.db', 'town-diagnostic-accounts.db', 'database.before.json', 'database.migrated.json',
                'hidden-receipt.json', 'tcp-receipt.json', 'tcp-run.log', 'migration-config.json',
                'migration.stdout.log', 'migration-second.stdout.log'}
    require(set(info.get('artifacts', {})) == required, 'Release artifact set differs')
    for name, digest in info['artifacts'].items():
        require(managed.sha(release / name) == digest, 'Release artifact changed: ' + name)
    require(info['artifacts']['god2-server.candidate.exe'] == info['candidate_sha256']
            and info['artifacts']['god2-server.before.exe'] == info['old_server_sha256']
            and info['artifacts']['server-config.before.json'] == info['config_sha256'], 'Manifest file identities disagree')
    require(managed.sha(managed.CONFIG) == info['config_sha256'] and managed.sha(managed.CLIENT) == info['client_sha256'],
            'Frozen live config/client changed')
    require(read(release / 'database.before.json') == capture(release / 'accounts.before.db'), 'Stage backup fingerprint differs')
    template = read(release / 'database.migrated.json')
    require(template == capture(release / 'town-diagnostic-accounts.db'), 'Stage migration fingerprint differs')
    require39(read(release / 'database.before.json'), template)
    return info, database, template


def install_binary(source, expected_sha):
    # Copy and hash completely before atomically replacing the inactive EXE.
    require(managed.sha(source) == expected_sha, 'Install source identity changed')
    with tempfile.NamedTemporaryFile(dir=managed.ACTIVE.parent, prefix='packet-links-', suffix='.exe', delete=False) as handle:
        temporary = Path(handle.name)
    try:
        shutil.copy2(source, temporary)
        require(managed.sha(temporary) == expected_sha, 'Install copy identity changed')
        temporary.replace(managed.ACTIVE)
    finally:
        temporary.unlink(missing_ok=True)


def process_guard_script():
    active = str(managed.ACTIVE.resolve()).replace("'", "''")
    return ("$ErrorActionPreference='Stop'; $active='" + active + "'; "
            "$rows=@(Get-NetTCPConnection -LocalPort 2592 -ErrorAction SilentlyContinue); "
            "if(@($rows|Where-Object {$_.State -in @('Established','SynReceived','SynSent')}).Count)"
            "{throw 'Player active; candidate and saves retained without interruption'}; "
            "$other=@($rows|Where-Object State -eq Listen|Where-Object {(Get-Process -Id $_.OwningProcess).Path -ne $active}); "
            "if($other.Count){throw 'Unmanaged listener; no process stopped'}; ")


def stop_idle(pid):
    # Recheck connections and PID/path immediately before stopping. The fresh DB
    # backup is taken only after shutdown, so final old-server saves are included.
    managed.powershell(process_guard_script() +
        f"$p=Get-Process -Id {int(pid)}; if($p.Path -ne $active){{throw 'Managed PID identity changed'}}; "
        "Stop-ScheduledTask -TaskName 'GOD2 Local Server'; "
        f"if(Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue){{Stop-Process -Id {int(pid)}}}; " + stopped_wait_script())


def stopped_wait_script():
    return ("$deadline=(Get-Date).AddSeconds(15); do {"
            "$owned=@(Get-Process -Name 'god2-server' -ErrorAction SilentlyContinue|Where-Object Path -eq $active); "
            "if($owned.Count){Start-Sleep -Milliseconds 200}} while($owned.Count -and (Get-Date) -lt $deadline); "
            "if($owned.Count){throw 'Managed process did not stop'}")


def stop_for_recovery():
    # No blanket process kills and no active-player interruption on failure.
    managed.powershell(process_guard_script() +
        "Stop-ScheduledTask -TaskName 'GOD2 Local Server'; "
        "$owned=@(Get-Process -Name 'god2-server' -ErrorAction SilentlyContinue|Where-Object Path -eq $active); "
        "foreach($p in $owned){Stop-Process -Id $p.Id}; " + stopped_wait_script())


def wait_listener():
    managed.powershell("$ErrorActionPreference='Stop'; $deadline=(Get-Date).AddSeconds(15); do {"
        "Start-Sleep -Milliseconds 300; $rows=@(Get-NetTCPConnection -LocalPort 2592 -State Listen -ErrorAction SilentlyContinue)"
        "} while(-not $rows.Count -and (Get-Date) -lt $deadline); "
        "if($rows.Count -ne 1){throw 'Managed server did not listen'}")
    return managed_listener(allow_players=True)


def require_commandline(command):
    # Current managed launch has exactly these three arguments. Reject extra
    # arguments, alternate config, unpaired quotes and ambiguous spaced paths.
    def token(path):
        raw = str(Path(path).resolve())
        escaped = re.escape(raw)
        return '(?:"' + escaped + '"' + ('' if re.search(r'\s', raw) else '|' + escaped) + ')'
    pattern = r'\s*' + token(managed.ACTIVE) + r'\s+--config\s+' + token(managed.CONFIG) + r'\s*'
    require(isinstance(command, str) and re.fullmatch(pattern, command, re.IGNORECASE),
            'Managed process does not use the exact release config')


def managed_listener(allow_players=False):
    pid = managed.listener(allow_players=allow_players)
    process = json.loads(managed.powershell(
        "$ErrorActionPreference='Stop'; "
        f"$p=Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}'; "
        "if(-not $p){throw 'Managed process disappeared'}; "
        "$p|Select-Object ExecutablePath,CommandLine|ConvertTo-Json -Compress").stdout)
    require(Path(process['ExecutablePath']).resolve() == managed.ACTIVE.resolve(), 'Managed process image differs')
    require_commandline(process['CommandLine'])
    return pid


def restore_original_availability(release, info, original_error):
    """A stop command may fail after stopping; recover without code/DB writes."""
    try:
        require(managed.sha(managed.ACTIVE) == info['old_server_sha256']
                and managed.sha(managed.CONFIG) == info['config_sha256'], 'Original executable/config changed')
        try:
            pid = managed_listener(allow_players=True)
        except (ValueError, subprocess.CalledProcessError):
            # A running but unqualified/stuck process is never blindly replaced.
            managed.powershell(process_guard_script() +
                "$owned=@(Get-Process -Name 'god2-server' -ErrorAction SilentlyContinue|Where-Object Path -eq $active); "
                "if($owned.Count){throw 'Original process still running but not verified; manual repair required'}")
            managed.start()
            pid = wait_listener()
        write(release / 'stop-recovery.json', {'original_available': True, 'service_pid': pid,
              'database_replaced': False, 'original_error': str(original_error)})
    except BaseException as error:
        write(release / 'stop-recovery.json', {'original_available': False, 'manual_repair_required': True,
              'database_replaced': False, 'original_error': str(original_error), 'recovery_error': str(error)})
        raise RuntimeError('Stop failed and original availability requires repair: ' + str(error)) from error


def undo_empty_migration(database, baseline, template):
    """Never restore a DB file. Check+undo in one transaction blocking writers."""
    require38(baseline)
    try:
        with closing(sqlite3.connect(Path(database).resolve().as_uri() + '?mode=rw', uri=True, timeout=5)) as db:
            db.execute('PRAGMA foreign_keys=ON')
            db.execute('BEGIN IMMEDIATE')
            try:
                current = capture_connection(db)
                if current == baseline:  # Migration failed atomically before committing39.
                    db.rollback()
                    return {'schema': 38, 'migration39_removed': False}
                require39(baseline, current, template, unchanged=True, empty=True)
                db.execute('DROP TABLE character_role_text')
                deleted = db.execute('DELETE FROM schema_migrations WHERE version=39').rowcount
                require(deleted == 1 and capture_connection(db) == baseline, 'Inverse migration did not reproduce old schema/rows/history')
                db.commit()
                return {'schema': 38, 'migration39_removed': True}
            except BaseException:
                db.rollback()
                raise
    except Exception as error:
        raise RollbackUnsafe('Rollback refused: save/schema changed or could not be proven unchanged; '
                             'candidate retained, no player database overwritten. ' + str(error)) from error


def installation_baseline(release, install):
    require(managed.sha(release / 'accounts.at-install.db') == install['database_backup_sha256'], 'At-install backup changed')
    require(managed.sha(release / 'database.at-install.json') == install['database_snapshot_sha256'], 'At-install fingerprint changed')
    baseline = read(release / 'database.at-install.json')
    require(baseline == capture(release / 'accounts.at-install.db'), 'At-install backup/fingerprint disagree')
    require38(baseline)
    return baseline


def recover(release, info, database, baseline, template, original_error):
    try:
        require(managed.sha(managed.CONFIG) == info['config_sha256'], 'Config changed; automatic recovery refused')
        require(managed.sha(managed.ACTIVE) in (info['candidate_sha256'], info['old_server_sha256']), 'Executable changed; recovery refused')
        stop_for_recovery()
        result = undo_empty_migration(database, baseline, template)
        install_binary(release / 'god2-server.before.exe', info['old_server_sha256'])
        managed.start()
        pid = wait_listener()
        write(release / 'rollback.json', {'recovered_old_code': True, 'database_replaced': False,
              **result, 'service_pid': pid, 'original_error': str(original_error)})
    except BaseException as error:
        # Never try a code-only rollback or start old code against schema39.
        # If players connected, stop_for_recovery refuses and candidate stays up.
        write(release / 'rollback.json', {'recovered_old_code': False, 'database_replaced': False,
              'candidate_artifact_retained': True, 'manual_repair_required': True,
              'original_error': str(original_error), 'recovery_error': str(error)})
        raise RollbackUnsafe('Automatic rollback unavailable; preserve candidate/save and repair forward. ' + str(error)) from error


def apply(release):
    info, database, template = load_manifest(release)
    require(not (release / 'installation.json').exists(), 'Apply already attempted; inspect installation/rollback receipts')
    require(freeze_gate() == info['freeze'], 'Frozen guard changed since staging')
    require(managed.sha(CANDIDATE) == info['candidate_sha256'], 'Current candidate changed since staging')
    require(managed.sha(managed.ACTIVE) == info['old_server_sha256'], 'Active executable changed since staging')
    qualify_hidden(release / 'hidden-receipt.json', info['candidate_sha256'])
    qualify_tcp(release / 'tcp-receipt.json', release / 'tcp-run.log', info['candidate_sha256'])
    # Refuse before stopping or mutating any managed artifact when players exist.
    pid = managed_listener()
    baseline = None
    installed = False
    try:
        stop_idle(pid)
        backup_new(database, release / 'accounts.at-install.db', release)
        baseline = capture(release / 'accounts.at-install.db')
        require38(baseline)
        staged = read(release / 'database.before.json')
        require(baseline['schema'] == staged['schema'] and baseline['history'] == staged['history']
                and baseline['pragmas'] == staged['pragmas'], 'Schema/history changed since stage; restage')
        require(capture(database) == baseline, 'Database changed after managed server stopped')
        write(release / 'database.at-install.json', baseline)
        install = {'candidate_sha256': info['candidate_sha256'], 'database_replacement': False,
                   'database_backup_sha256': managed.sha(release / 'accounts.at-install.db'),
                   'database_snapshot_sha256': managed.sha(release / 'database.at-install.json')}
        write(release / 'installation.json', install)
        require(managed.sha(managed.CONFIG) == info['config_sha256'] and managed.sha(managed.CLIENT) == info['client_sha256'],
                'Config/client changed before installation')
        install_binary(release / 'god2-server.candidate.exe', info['candidate_sha256'])
        installed = True
        # Validate in place before opening a gameplay listener. --migrate-only
        # does not load Lua or accept connections; config and DB paths stay exact.
        migrate(managed.ACTIVE, managed.CONFIG, release / 'install-migration.stdout.log')
        migrated = capture(database)
        require39(baseline, migrated, template, unchanged=True, empty=True)
        write(release / 'database.at-migration.json', migrated)
        install['migration_snapshot_sha256'] = managed.sha(release / 'database.at-migration.json')
        install['migration_verified_before_listen'] = True
        write(release / 'installation.json', install)
        managed.start()
        wait_listener()
        return verify(release)
    except BaseException as error:
        if installed and baseline is not None:
            # Re-read the durable baseline; never authorize inverse migration
            # from an in-memory value whose saved audit artifacts disagree.
            try:
                baseline = installation_baseline(release, read(release / 'installation.json'))
            except Exception as audit_error:
                raise RollbackUnsafe('At-install audit failed; keep candidate/save for repair: ' + str(audit_error)) from error
            recover(release, info, database, baseline, template, error)
        else:
            # No executable/DB mutation has occurred. Restore availability using
            # the same original executable, without writing config or database.
            restore_original_availability(release, info, error)
        raise


def verify(release):
    info, database, template = load_manifest(release)
    require(managed.sha(managed.ACTIVE) == info['candidate_sha256'], 'Managed executable is not the candidate')
    install = read(release / 'installation.json')
    require(install.get('candidate_sha256') == info['candidate_sha256'] and install.get('migration_verified_before_listen') is True,
            'Verified pre-listen installation receipt missing')
    baseline = installation_baseline(release, install)
    require(managed.sha(release / 'database.at-migration.json') == install['migration_snapshot_sha256'], 'Migration verification artifact changed')
    require39(baseline, read(release / 'database.at-migration.json'), template, unchanged=True, empty=True)
    current = capture(database)
    # Runtime saves after listener startup are valid. Report them, never roll
    # them back or require live rows to equal an old staging backup.
    require39(baseline, current, template, unchanged=False, empty=False)
    changed = changed_old_tables(baseline, current)
    role_rows = current['tables'][ROLE_TABLE]['rows']
    result = {'verified': True, 'candidate_sha256': info['candidate_sha256'], 'schema': 39,
              'old_tables_preserved_at_migration': OLD_TABLE_COUNT, 'old_schema_and_history_preserved': True,
              'config_unchanged': True, 'client_unchanged': True, 'database_replaced': False,
              'tables_changed_since_install': changed, 'role_text_rows': role_rows,
              'data_eligible_for_empty_inverse': not changed and role_rows == 0,
              'service_pid': managed_listener(allow_players=True)}
    write(release / 'verification.json', result)
    print(json.dumps(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('stage', 'apply', 'verify'))
    parser.add_argument('--release-name', required=True)
    parser.add_argument('--hidden-receipt', type=Path)
    parser.add_argument('--tcp-receipt', type=Path)
    parser.add_argument('--tcp-log', type=Path)
    args = parser.parse_args()
    require(re.fullmatch(r'packet-links-20260930-[A-Za-z0-9-]+', args.release_name), 'Invalid release directory name')
    release = ROOT / 'artifacts/releases' / args.release_name
    if args.mode == 'stage':
        require(all((args.hidden_receipt, args.tcp_receipt, args.tcp_log)), 'Stage needs hidden and TCP receipts plus TCP log')
        stage(args, release)
    else:
        {'apply': apply, 'verify': verify}[args.mode](release)


if __name__ == '__main__':
    main()
