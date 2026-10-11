"""CUSTOM-0080 binary-only schema50 release; no live action unless apply --execute.

Relocate this reviewed draft to tools/operations before operational use. Source
ROOT intentionally follows that standard location. No config/resource/save
replacement, migration addition, fixture grant or inverse operation exists.
Old50 binary rollback requires an exact unchanged fresh post-stop save and an
idle stopped owned process. Active players prevent both stop and recovery.
"""
import argparse
import ast
from copy import deepcopy
from pathlib import Path
import shutil
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.operations import owned_guild_announcement_release_v01_20261004 as ann

base, managed, managed_links = ann.base, ann.managed, ann.managed_links
require, sha, read, write_new = ann.require, ann.sha, ann.read, ann.write_new
FORMAT = 'owned-guild-kick-binary50-release-20261005-v1'
CANDIDATE_SHA = '619f04ce6a09bdc2307e59a2d82f9db0bf7a92d4d81fee710843bf63b27d973e'
OLD_SHA = '4972022132b0cf5d68c9f8e620df3be6c81035c2b7a4aa8395743ddf2b09f708'
REQUIRED_SOURCES = (
    'src/core/Application.cpp', 'src/core/Config.cpp', 'src/core/Config.h', 'src/main.cpp',
    'src/db/ServerSqliteMigrations.cpp', 'src/db/ServerSqliteMigrations.h', 'src/db/Migration.cpp',
    'src/db/SqliteDatabase.cpp', 'src/db/SqliteOwnedGuildMembershipRepository.cpp',
    'src/db/SqliteOwnedGuildMembershipRepository.h', 'src/handlers/OwnedGuildKickService.h',
    'src/handlers/OwnedGuildLeaderPanelService.h', 'src/handlers/OwnedGuildAnnouncementService.h',
    'src/db/SqliteOwnedGuildAnnouncementRepository.cpp', 'src/protocol/RecoveredWorldRecords.h',
    'tests/test_owned_guild_kick_0080.cpp', 'tests/storage_owned_guild_kick_0080.cpp',
    'tests/research/test_native_guild_kick_server_20261005.py',
    'tools/operations/owned_guild_announcement_release_v01_20261004.py',
    'tools/operations/owned_guild_release_v02_20261004.py',
    'tools/operations/packet_links_release_20260930.py',
    'tools/operations/native_quest_catalog_release.py',
    'tools/operations/verify_frozen_chat_20260927.py',
)


def rooted(path):
    path = Path(path)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def require50(state):
    require([row[0] for row in state['history']] == list(range(1, 51)), 'Exact existing history1..50 required')
    require(state['history'][-1][:3] == [50, ann.MIGRATION_NAME, ann.migration_sql()], 'Existing migration50 identity differs')
    require(set(ann.NEW_TABLES) <= set(state['tables']), 'Existing announcement50 table missing')
    require([row for row in state['schema'] if row[2] in ann.NEW_TABLES] == ann.expected_addition(ann.migration_sql()),
            'Existing announcement50 DDL differs')


def validate_contract(path, candidate):
    contract = read(path)
    require(contract.get('design') == 'CUSTOM-0080' and contract.get('feature_family') == 'guild-kick0080', 'Wrong release design/feature')
    require(contract.get('formal_config') is True and contract.get('env_lab_false') is True, 'Ordinary formal-config contract required')
    require(rooted(contract['candidate_path']) == Path(candidate).resolve(), 'Candidate path differs')
    require(contract.get('candidate_sha256') == CANDIDATE_SHA == sha(candidate), 'Exact accepted kick candidate required')
    closure = contract.get('source_sha256')
    require(isinstance(closure, dict) and closure, 'Exact source closure missing')
    for source in REQUIRED_SOURCES:
        require(source in closure, 'Required runtime/storage/gate source missing: ' + source)
    for source, expected in closure.items():
        require(sha(rooted(source)) == expected, 'Source closure changed: ' + source)
    helper = rooted(contract['helper_path'])
    require(sha(helper) == contract['helper_sha256'] and
            any(rooted(p) == helper and h == contract['helper_sha256'] for p, h in closure.items()),
            'Exact real-client helper closure missing')
    return contract


def tuple_rows(values):
    require(isinstance(values, list), 'Native SQL rows must be a list')
    result = []
    for value in values:
        require(isinstance(value, str), 'Native SQL row encoding differs')
        row = ast.literal_eval(value)
        require(isinstance(row, tuple), 'Native SQL row is not a tuple')
        result.append(row)
    return result


def validate_native_kick(ui, locale):
    base.true_fields(ui, ('kick_actual_client_accepted',), 'Native72 acceptance')
    kick = ui.get('native72_member_kick', {})
    base.true_fields(kick, ('accepted', 'cancel_sql_exact', 'cancel_sent_no72', 'all_unrelated_tables_exact',
        'announcement_history_exact', 'founder_guild_retained', 'target_2D_name_cleared',
        'target_panels_closed', 'both_clients_still_running', 'relogin_membership_absent'), 'Native72 flow')
    require(type(kick.get('removed_character')) is int and kick['removed_character'] == 5 and
            type(kick.get('simultaneous_native_clients')) is int and kick['simultaneous_native_clients'] == 2,
            'Two connected actual clients/removed target proof differs')
    log = kick.get('commit_log', '')
    require(isinstance(log, str) and 'OWNED_GUILD_MEMBER_KICK ' in log and
            'character_id=4 slot=1 target_character=5 committed=true' in log, 'Native72 server commit proof differs')
    cache = kick.get('target_92_cache_empty', {})
    require(type(cache.get('count')) is int and cache['count'] == 0 and cache.get('rows_hex') == [] and
            cache.get('by_name') == {}, 'Target native92 cache is not empty')
    delta = kick.get('SQL_delta', {})
    require(set(delta) == {'owned_guilds', 'owned_guild_members'}, 'Native72 changed unrelated SQL')
    members = tuple_rows(delta['owned_guild_members']['before'])
    remaining = tuple_rows(delta['owned_guild_members']['after'])
    removed = [row for row in members if row and row[0] == 5]
    require(len(removed) == 1 and len(removed[0]) >= 3 and type(removed[0][1]) is int,
            'Native72 removed membership identity missing/ambiguous')
    require(remaining == [row for row in members if row[0] != 5], 'Native72 modified another member/opaque column')
    guild_id = removed[0][1]
    before, after = tuple_rows(delta['owned_guilds']['before']), tuple_rows(delta['owned_guilds']['after'])
    require(len(before) == len(after) and len([row for row in before if row[0] == guild_id]) == 1, 'Native72 guild row identity differs')
    changed = 0
    for old, new in zip(before, after):
        if old[0] != guild_id:
            require(old == new, 'Native72 changed foreign guild')
        else:
            require(len(old) >= 3 and len(old) == len(new) and old[:2] == new[:2] and old[3:] == new[3:] and
                    type(old[2]) is int and type(new[2]) is int and new[2] == old[2] + 1, 'Native72 changed protected guild fields/revision increment')
            changed += 1
    require(changed == 1, 'Native72 exact one guild revision mutation required')
    common = kick.get('frozen_common_chat_after_kick', {})
    base.true_fields(common, ('accepted', 'SQL_exact'), 'Post-kick frozen common chat')
    token = 'kick80-common-' + str(locale)
    require(common.get('token') == token and common.get('native_input_hex') == token.encode('ascii').hex(),
            'Post-kick native chat input differs')
    receivers = common.get('native_archive_receivers')
    require(isinstance(receivers, list) and len(receivers) == 2 and {r.get('identity') for r in receivers} == {4, 5},
            'Both actual common chat archives required')
    for receiver in receivers:
        require(type(receiver.get('identity')) is int and type(receiver.get('count')) is int and
                1 <= receiver['count'] <= 200 and
                b'fixedgirl: ' + token.encode('ascii') in bytes.fromhex(receiver.get('common_text_hex', '')),
                'Post-kick common archive did not consume native sender/text')
    chat_log = common.get('server_log', '')
    require(isinstance(chat_log, str) and 'NATIVE_CHAT_ACCEPTED ' in chat_log and 'recipients=2' in chat_log,
            'Post-kick server common audience differs')
    return kick


def validate_receipt(receipt, contract, contract_sha):
    # Existing immutable validator covers both announcement locales, real79
    # denied draft restoration, frozen/source/DB/process/desktop preservation.
    ann.validate_receipt(receipt, contract, contract_sha)
    for case in receipt['cases']:
        validate_native_kick(case['ui'], case['locale'])
    return receipt


def qualify_inputs(args):
    require(args.candidate and args.contract and args.receipt, 'Candidate/contract/complete two-locale receipt required')
    candidate, contract_path, receipt_path = rooted(args.candidate), rooted(args.contract), rooted(args.receipt)
    contract = validate_contract(contract_path, candidate)
    receipt = validate_receipt(read(receipt_path), contract, sha(contract_path))
    require(receipt['files_before'].get('client') == sha(managed.CLIENT), 'Accepted client identity changed')
    for source, expected in receipt['frozen_before'].items():
        require(sha(rooted(source)) == expected, 'Accepted frozen dependency changed: ' + source)
    return candidate, contract_path, contract, receipt_path, receipt


def formal_state():
    config, database = base.configured_database()
    require(config.get('world', {}).get('owned_guild_announcements', {}).get('enabled') is True, 'Formal announcement must remain enabled')
    ann.announcement_config(config, True)  # Validate preserved ordinary membership2996 prerequisites.
    state = ann.capture(database)
    require50(state)
    return config, database, state


def stage(args):
    candidate, contract_path, contract, receipt_path, _ = qualify_inputs(args)
    release = rooted(args.release)
    require(not release.exists(), 'Unused release directory required')
    config, database, _ = formal_state()
    require(sha(managed.ACTIVE) == OLD_SHA, 'Exact qualified old50 formal binary required')
    frozen, resources = base.freeze_gate(), ann.assert_resources()
    release.mkdir(parents=True, exist_ok=False)
    for source, name in ((candidate, 'god2-server.candidate.exe'), (managed.ACTIVE, 'god2-server.before.exe'),
                         (managed.CONFIG, 'server-config.before.json'), (contract_path, 'contract.json'),
                         (receipt_path, 'native-receipt.json')):
        shutil.copy2(source, release / name)
    snapshot_map = {}; (release / 'source-snapshot').mkdir()
    for index, (source, expected) in enumerate(sorted(contract['source_sha256'].items())):
        name = 'source-snapshot/' + str(index).zfill(5) + '-' + rooted(source).name
        target = ann.artifact_path(release, name)
        shutil.copy2(rooted(source), target)
        require(sha(target) == expected, 'Source snapshot changed during copy: ' + source)
        snapshot_map[source] = name
    write_new(release / 'source-snapshot-map.json', snapshot_map)
    base.backup_new(database, release / 'stage-before.db')
    before = ann.capture(release / 'stage-before.db'); require50(before)
    base.backup_new(release / 'stage-before.db', release / 'town-diagnostic-accounts.db')
    private = deepcopy(config)
    private['database']['path'] = str(release / 'town-diagnostic-accounts.db')
    private['logging']['file'] = str(release / 'stage-server.log')
    write_new(release / 'stage-config.json', private)
    for binary, name in (('god2-server.before.exe', 'old50-reopen.log'),
                         ('god2-server.candidate.exe', 'candidate50-first.log'),
                         ('god2-server.candidate.exe', 'candidate50-repeat.log')):
        base.migrate(release / binary, release / 'stage-config.json', release / name)
        require(ann.capture(release / 'town-diagnostic-accounts.db') == before,
                'Same50 migration/reopen changed typed save/schema/history: ' + name)
    write_new(release / 'database-stage-before.json', before)
    qualify_inputs(args)
    require(sha(managed.ACTIVE) == OLD_SHA and sha(managed.CONFIG) == sha(release / 'server-config.before.json'),
            'Formal code/config changed during stage')
    ann.assert_resources(resources)
    require(base.freeze_gate() == frozen, 'Frozen gate changed during stage')
    artifacts = {p.relative_to(release).as_posix(): sha(p) for p in release.rglob('*') if p.is_file()}
    info = {'format': FORMAT, 'stage_qualified': True, 'formal_native_qualified': True,
            'same_schema50_reopen_qualified': True, 'release_tool_path': str(Path(__file__).resolve()),
            'release_tool_sha256': sha(__file__), 'candidate_original_path': str(candidate),
            'candidate_sha256': sha(candidate), 'contract_original_path': str(contract_path),
            'contract_sha256': sha(contract_path), 'receipt_original_path': str(receipt_path),
            'receipt_sha256': sha(receipt_path), 'old_server_sha256': OLD_SHA,
            'database': str(database), 'active': str(managed.ACTIVE.resolve()), 'config': str(managed.CONFIG.resolve()),
            'config_sha256': sha(managed.CONFIG), 'client_sha256': sha(managed.CLIENT),
            'frozen_chat': frozen, 'resources_preserved': resources, 'source_snapshot_map': snapshot_map,
            'artifacts': artifacts, 'database_replaced': False, 'config_changed': False, 'resources_changed': False,
            'recovery': 'Old50BinaryOnlyAfterIdleStopAndExactFreshSave_NoSaveRestore_NoInverse'}
    write_new(release / 'manifest.json', info)
    return info


def qualify_stage(args):
    candidate, contract_path, contract, receipt_path, receipt = qualify_inputs(args)
    release = rooted(args.release);info = read(release / 'manifest.json')
    base.true_fields(info, ('stage_qualified', 'formal_native_qualified', 'same_schema50_reopen_qualified'), 'Binary-only stage')
    require(info.get('format') == FORMAT and info.get('release_tool_path') == str(Path(__file__).resolve()) and
            info.get('release_tool_sha256') == sha(__file__), 'Exact release helper identity differs')
    require(all(info.get(key) is False for key in ('database_replaced', 'config_changed', 'resources_changed')),
            'Binary-only stage preservation scope differs')
    require(info['candidate_sha256'] == CANDIDATE_SHA == sha(candidate) and info['old_server_sha256'] == OLD_SHA and
            info['contract_sha256'] == sha(contract_path) and info['receipt_sha256'] == sha(receipt_path), 'Staged release identities differ')
    artifacts = info.get('artifacts')
    required_artifacts = {'god2-server.candidate.exe', 'god2-server.before.exe', 'server-config.before.json',
        'contract.json', 'native-receipt.json', 'source-snapshot-map.json', 'stage-before.db',
        'town-diagnostic-accounts.db', 'stage-config.json', 'old50-reopen.log',
        'candidate50-first.log', 'candidate50-repeat.log', 'database-stage-before.json'}
    require(isinstance(artifacts, dict) and required_artifacts <= set(artifacts),
            'Complete same50 rehearsal audit artifacts required')
    for name, expected in artifacts.items():
        require(sha(ann.artifact_path(release, name)) == expected, 'Stage artifact changed: ' + name)
    for name, expected in (('god2-server.candidate.exe', CANDIDATE_SHA), ('god2-server.before.exe', OLD_SHA),
                           ('server-config.before.json', info['config_sha256']), ('contract.json', info['contract_sha256']),
                           ('native-receipt.json', info['receipt_sha256'])):
        require(info['artifacts'].get(name) == expected, 'Stage copy identity differs: ' + name)
    require(set(info['source_snapshot_map']) == set(contract['source_sha256']), 'Source snapshot closure differs')
    require(base.exact_json(read(release / 'source-snapshot-map.json'), info['source_snapshot_map']),
            'Source snapshot map artifact differs')
    for source, name in info['source_snapshot_map'].items():
        require(info['artifacts'].get(name) == contract['source_sha256'][source], 'Staged source identity differs: ' + source)
    config, database, _ = formal_state()
    private = deepcopy(config)
    private['database']['path'] = str(release / 'town-diagnostic-accounts.db')
    private['logging']['file'] = str(release / 'stage-server.log')
    require(base.exact_json(read(release / 'stage-config.json'), private),
            'Rehearsal config differs from preserved formal flags/private database')
    require(str(database) == info['database'] and str(managed.ACTIVE.resolve()) == info['active'] and
            str(managed.CONFIG.resolve()) == info['config'] and sha(managed.CONFIG) == info['config_sha256'] and
            sha(managed.ACTIVE) == OLD_SHA and sha(managed.CLIENT) == info['client_sha256'], 'Formal targets/config/code/client changed')
    require(base.freeze_gate() == info['frozen_chat'], 'Frozen baseline changed')
    ann.assert_resources(info['resources_preserved'])
    before = read(release / 'database-stage-before.json');require50(before)
    require(ann.capture(release / 'stage-before.db') == before and
            ann.capture(release / 'town-diagnostic-accounts.db') == before, 'Stage SQLite backup/rehearsal changed')
    # Formal player rows may advance between stage and the authorized idle stop.
    return info, config, database, receipt


def assert_owned_stopped():
    managed.powershell(managed_links.process_guard_script() +
        "$owned=@(Get-Process -Name 'god2-server' -ErrorAction SilentlyContinue|Where-Object Path -eq $active); "
        "if($owned.Count){throw 'Owned process remains running; no replacement/recovery'}")


def exact_unchanged_guard(info, database, fresh):
    require(sha(managed.CONFIG) == info['config_sha256'] and sha(managed.CLIENT) == info['client_sha256'],
            'Config/client changed; no binary recovery')
    _, current_database = base.configured_database()
    require(current_database == Path(database).resolve() == Path(info['database']).resolve(), 'Save target changed; no recovery')
    ann.assert_resources(info['resources_preserved'])
    require(base.freeze_gate() == info['frozen_chat'], 'Frozen gate changed; no binary recovery')
    state = ann.capture(current_database);require50(state)
    require(state == fresh, 'Fresh save has new rows/schema/history; retain current binary for forward repair')


def apply(args):
    require(args.execute is True, 'Live apply requires explicit --execute after root review')
    info, _, database, _ = qualify_stage(args)
    release = rooted(args.release)
    require(not (release / 'apply-started.json').exists(), 'Existing attempt journal retained; forward repair only')
    base.assert_formal_environment()
    pid = managed_links.managed_listener()  # Existing exact2592 idle PID/image/config/commandline guard.
    write_new(release / 'apply-started.json', {'owned_idle_pid': pid, 'database_replaced': False,
        'config_changed': False, 'resources_changed': False})
    stopped = candidate_installed = start_requested = False
    fresh = None
    try:
        try:
            managed_links.stop_idle(pid);stopped = True
        except BaseException:
            assert_owned_stopped();stopped = True;raise
        base.backup_new(database, release / 'install-fresh-before.db')
        fresh = ann.capture(release / 'install-fresh-before.db');require50(fresh)
        require(ann.capture(database) == fresh, 'Save changed after managed stop')
        write_new(release / 'database-install-before.json', fresh)
        qualify_stage(args)
        assert_owned_stopped()
        managed_links.install_binary(release / 'god2-server.candidate.exe', CANDIDATE_SHA)
        candidate_installed = True
        require(sha(managed.ACTIVE) == CANDIDATE_SHA, 'Installed candidate identity differs')
        base.migrate(managed.ACTIVE, managed.CONFIG, release / 'same50-install-reopen.log')
        exact_unchanged_guard(info, database, fresh)
        write_new(release / 'database-install-after.json', ann.capture(database))
        start_requested = True;managed.start();new_pid = managed_links.wait_listener()
        require(sha(managed.ACTIVE) == CANDIDATE_SHA and sha(managed.CONFIG) == info['config_sha256'], 'Started code/config identity differs')
        result = {'accepted': True, 'formal_installed': True, 'owned_pid': new_pid,
            'candidate_sha256': CANDIDATE_SHA, 'old_server_sha256': OLD_SHA,
            'contract_sha256': info['contract_sha256'], 'native_receipt_sha256': info['receipt_sha256'],
            'database_replaced': False, 'config_changed': False, 'resources_changed': False,
            'same_schema50_exact_before_start': True, 'no_gameplay_grants': True,
            'current_client_post_promotion_pending': True}
        write_new(release / 'apply-result.json', result);return result
    except BaseException as error:
        result = {'accepted': False, 'error': str(error), 'database_replaced': False, 'config_changed': False,
            'resources_changed': False, 'schema_downgraded': False, 'candidate_retained': candidate_installed,
            'old50_binary_restored': False, 'service_restarted': False, 'manual_forward_repair_required': True}
        try:
            # Even a replacement that raised after atomic rename is qualified
            # by observed hashes, never by an optimistic local success flag.
            active_sha = sha(managed.ACTIVE)
            require(active_sha in (OLD_SHA, CANDIDATE_SHA), 'Unknown active binary; no recovery')
            candidate_installed = active_sha == CANDIDATE_SHA
            result['candidate_retained'] = candidate_installed
            if stopped:
                if start_requested:
                    try:
                        running = managed_links.managed_listener()  # Refuses active players.
                    except (ValueError, subprocess.CalledProcessError):
                        running = None
                    if running is not None:
                        require(sha(managed.ACTIVE) == CANDIDATE_SHA, 'Recovery running candidate identity differs')
                        managed_links.stop_idle(running)
                assert_owned_stopped()
                if fresh is None:
                    base.backup_new(database, release / 'install-stop-recovery-before.db')
                    fresh = ann.capture(release / 'install-stop-recovery-before.db');require50(fresh)
                    write_new(release / 'database-stop-recovery-before.json', fresh)
                exact_unchanged_guard(info, database, fresh)
                if candidate_installed:
                    require(sha(release / 'god2-server.before.exe') == OLD_SHA, 'Qualified old50 copy changed; no recovery')
                    managed_links.install_binary(release / 'god2-server.before.exe', OLD_SHA)
                    result['old50_binary_restored'] = True;result['candidate_retained'] = False
                require(sha(managed.ACTIVE) == OLD_SHA, 'Old50 recovery binary identity differs')
                exact_unchanged_guard(info, database, fresh)
                managed.start();result['owned_pid'] = managed_links.wait_listener();result['service_restarted'] = True
        except BaseException as recovery:
            result['recovery_error'] = str(recovery)
        write_new(release / 'apply-failed.json', result);raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('inspect', 'stage', 'qualify', 'apply'), nargs='?', default='inspect')
    for name in ('candidate', 'contract', 'receipt', 'release'):
        parser.add_argument('--' + name)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if args.command == 'inspect':
        _, database, state = formal_state()
        result = {'format': FORMAT, 'read_only': True, 'database': str(database),
                  'schema_versions': [row[0] for row in state['history']], 'formal_installed': False,
                  'resources_preserved': ann.assert_resources()}
    else:
        require(args.release, '--release required')
        if args.command == 'stage':result = stage(args)
        elif args.command == 'qualify':
            info, _, _, _ = qualify_stage(args);result = {'accepted': True, 'candidate_sha256': info['candidate_sha256']}
        else:result = apply(args)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
