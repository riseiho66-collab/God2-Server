"""CUSTOM-0081 binary-only schema50 release; no live action unless apply --execute.

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
from tools.operations import owned_guild_kick_release_v01_20261005 as kick
KICK_HELPER_SHA = 'b71b9b6a9a9ea9ce93a6db79768fda943a9ac7a70adb6410a125b32c4b6c9ee8'

base, managed, managed_links = ann.base, ann.managed, ann.managed_links
require, sha, read, write_new = ann.require, ann.sha, ann.read, ann.write_new
FORMAT = 'owned-guild-disband-binary50-release-20261005-v2'
CANDIDATE_SHA = '8eaac6f7e40348585500428007b74cd9656748afdedabdca5a034433805c325b'
OLD_SHA = '619f04ce6a09bdc2307e59a2d82f9db0bf7a92d4d81fee710843bf63b27d973e'
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
    'src/handlers/OwnedGuildDisbandService.h', 'src/protocol/RecoveredGuildDisband75.h',
    'tests/storage_owned_guild_disband_0081.cpp', 'tests/test_owned_guild_disband_service_0081.cpp',
    'tests/test_owned_guild_disband_wire_0081.cpp',
    'tests/research/test_native_guild_disband_server_20261005.py',
    'tools/operations/owned_guild_kick_release_v01_20261005.py',
    'tools/strike_lab/private_guild_disband_0081_v02_20261005.py',
    'artifacts/research/native-guild-management-0081/helper-static-v02/disband_phase.py',
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
    require(contract.get('design') == 'CUSTOM-0081' and contract.get('feature_family') == 'guild-disband0081', 'Wrong release design/feature')
    require(contract.get('formal_config') is True and contract.get('env_lab_false') is True, 'Ordinary formal-config contract required')
    require(rooted(contract['candidate_path']) == Path(candidate).resolve(), 'Candidate path differs')
    require(contract.get('candidate_sha256') == CANDIDATE_SHA == sha(candidate), 'Exact accepted disband candidate required')
    closure = contract.get('source_sha256')
    require(isinstance(closure, dict) and closure, 'Exact source closure missing')
    for source in REQUIRED_SOURCES:
        require(source in closure, 'Required runtime/storage/gate source missing: ' + source)
    for source, expected in closure.items():
        require(sha(rooted(source)) == expected, 'Source closure changed: ' + source)
    helper = rooted(contract['helper_path'])
    require(helper == rooted('tools/strike_lab/private_guild_disband_0081_v02_20261005.py'), 'Native75 exact helper path required')
    require(sha(kick.__file__) == KICK_HELPER_SHA, 'Immutable kick release helper changed')
    require(sha(helper) == contract['helper_sha256'] and
            any(rooted(p) == helper and h == contract['helper_sha256'] for p, h in closure.items()),
            'Exact real-client helper closure missing')
    validate_tcp_receipt(contract, candidate)
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


DISBAND_TABLES = ('owned_guilds', 'owned_guild_members', 'owned_guild_governance_0078', 'owned_guild_applications_0078')


def validate_installed_release(path):
    """Requalify immutable preinstall evidence without requiring old live EXE."""
    info=read(path/'manifest.json');apply=read(path/'apply-result.json')
    base.true_fields(info,('stage_qualified','formal_native_qualified','same_schema50_reopen_qualified'),'Installed stage')
    require(info.get('format')==FORMAT and info.get('candidate_sha256')==CANDIDATE_SHA and
            info.get('old_server_sha256')==OLD_SHA,'Installed manifest identity differs')
    require(info.get('release_tool_path')==str(Path(__file__).resolve()) and
            info.get('release_tool_sha256')==sha(__file__),'Installed release helper identity differs')
    base.true_fields(apply,('accepted','formal_installed','same_schema50_exact_before_start','no_gameplay_grants'), 'Formal apply')
    require(all(record.get(k) is False for record in (info,apply) for k in
                ('database_replaced','config_changed','resources_changed')),'Binary-only same50 release required')
    require(apply.get('candidate_sha256')==CANDIDATE_SHA and apply.get('old_server_sha256')==OLD_SHA and
            apply.get('contract_sha256')==info['contract_sha256'] and
            apply.get('native_receipt_sha256')==info['receipt_sha256'],'Formal apply/stage evidence differs')
    require(str(managed.ACTIVE.resolve())==info['active'] and
            str(managed.CONFIG.resolve())==info['config'],'Installed target path differs')
    required={'god2-server.candidate.exe','god2-server.before.exe','server-config.before.json','contract.json',
              'native-receipt.json','source-snapshot-map.json','stage-before.db','town-diagnostic-accounts.db',
              'stage-config.json','old50-reopen.log','candidate50-first.log','candidate50-repeat.log','database-stage-before.json'}
    require(isinstance(info.get('artifacts'),dict) and required<=set(info['artifacts']),
            'Complete installed stage audit evidence required')
    for name,expected in info['artifacts'].items():
        require(sha(ann.artifact_path(path,name))==expected,'Installed stage artifact changed: '+name)
    for name,key in (('contract.json','contract_sha256'),('native-receipt.json','receipt_sha256'),
                     ('god2-server.candidate.exe','candidate_sha256'),('god2-server.before.exe','old_server_sha256'),
                     ('server-config.before.json','config_sha256')):
        require(info['artifacts'].get(name)==info[key],'Installed stage copy identity differs: '+name)
    precontract=read(path/'contract.json')
    require(precontract.get('design')=='CUSTOM-0081' and precontract.get('feature_family')=='guild-disband0081' and
            precontract.get('candidate_sha256')==CANDIDATE_SHA,'Installed preacceptance contract identity differs')
    validate_receipt(read(path/'native-receipt.json'),precontract,info['contract_sha256'])
    require(set(info['source_snapshot_map'])==set(precontract['source_sha256']) and
            base.exact_json(read(path/'source-snapshot-map.json'),info['source_snapshot_map']),
            'Installed source snapshot map differs')
    for source,name in info['source_snapshot_map'].items():
        require(info['artifacts'].get(name)==precontract['source_sha256'][source],
                'Installed source snapshot differs: '+source)
    before=read(path/'database-install-before.json');after=read(path/'database-install-after.json')
    require50(before);require50(after)
    require(before==after and ann.capture(path/'install-fresh-before.db')==before,
            'Installed same50 fresh backup/reopen proof differs')
    return info,apply

def validate_installed_tcp_binding(contract, compiled):
    """Permit one same-hash installed path, only with complete immutable stage/apply proof.

    Historical install snapshots must be exact; live player rows may legitimately
    advance after install. Current save target/schema/config/resources/frozen gate
    remain exact. This never stops a process, writes storage, or grants gameplay.
    """
    value = contract.get('formal_release')
    require(isinstance(value, str) and value, 'Installed TCP candidate needs formal_release binding')
    directory = rooted(value)
    require(directory.is_relative_to(ROOT.resolve()) and directory != ROOT.resolve(), 'Formal release escapes workspace')
    info, installed = validate_installed_release(directory)
    require(rooted(info['candidate_original_path']) == compiled, 'Installed original compiled candidate path differs')
    precontract = read(directory/'contract.json')
    require(rooted(precontract['candidate_path']) == compiled and
            rooted(precontract.get('tcp_candidate_path', precontract['candidate_path'])) == compiled,
            'Installed precontract compiled TCP identity differs')
    require(info['candidate_sha256'] == installed['candidate_sha256'] == CANDIDATE_SHA == sha(compiled) == sha(managed.ACTIVE),
            'Installed compiled/current candidate hash differs')
    require(info['old_server_sha256'] == installed['old_server_sha256'] == OLD_SHA, 'Installed historical old binary differs')
    require(sha(managed.CONFIG) == info['config_sha256'] and sha(managed.CLIENT) == info['client_sha256'],
            'Installed config/client changed')
    ann.assert_resources(info['resources_preserved'])
    require(base.freeze_gate() == info['frozen_chat'], 'Installed frozen gate changed')
    _, database, state = formal_state()
    require50(state)
    require(Path(database).resolve() == Path(info['database']).resolve(), 'Installed save target changed')
    return info


def validate_tcp_receipt(contract, candidate):
    path = rooted(contract.get('tcp_receipt_path', ''))
    require(path.is_file() and sha(path) == contract.get('tcp_receipt_sha256'), 'Exact TCP proof missing/changed')
    proof = read(path)
    base.true_fields(proof, ('accepted', 'production_source_unchanged', 'formal_binary_unchanged', 'env_lab_false'), 'Native75 TCP safety')
    require(type(proof.get('tests_passed')) is int and proof['tests_passed'] == 7 and
            type(proof.get('results_exit_code')) is int and proof['results_exit_code'] == 0,
            'All seven Native75 TCP tests required')
    require(proof.get('actual_client_acceptance') is False, 'TCP cannot claim actual-client acceptance')
    compiled = rooted(proof['candidate_path'])
    current = Path(candidate).resolve()
    require(proof['candidate_sha256'] == CANDIDATE_SHA == sha(current), 'TCP candidate identity differs')
    if 'tcp_candidate_path' in contract:
        require(rooted(contract['tcp_candidate_path']) == compiled, 'Explicit TCP compiled path differs')
        require(sha(compiled) == CANDIDATE_SHA, 'Original TCP compiled binary changed')
    if compiled != current:
        require('tcp_candidate_path' in contract and current == managed.ACTIVE.resolve(),
                'Only explicitly bound formal installed candidate may differ from TCP compiled path')
        validate_installed_tcp_binding(contract, compiled)

    require(proof.get('formal_binary_sha256') == OLD_SHA, 'TCP formal preservation identity differs')
    require(sha(rooted(proof['test_path'])) == proof['test_sha256'] == contract['source_sha256'].get(
        'tests/research/test_native_guild_disband_server_20261005.py'), 'TCP test closure differs')
    pins = proof.get('source_pins')
    require(isinstance(pins, dict) and 'src/core/Application.cpp' in {p.replace('\\', '/') for p in pins}, 'TCP source closure absent')
    for source, expected in pins.items():
        canonical = source.replace('\\', '/')
        require(contract['source_sha256'].get(canonical) == expected == sha(rooted(source)), 'TCP source pin differs: ' + source)
    require(sha(rooted(proof['results_log'])) == proof['results_log_sha256'], 'TCP result log changed')
    result = rooted(proof['results_log']).read_text('utf-8')
    require('Ran 7 tests' in result and '\nOK' in result and result.count(' ... ok') == 7 and
            CANDIDATE_SHA in result and 'NOT_LIVE_CLIENT_UI' in result, 'TCP successful terminal result absent')
    baseline = proof.get('projection_baseline', {})
    require(baseline.get('fixed_failures_verified') is True and baseline.get('fixed_both_faults_atomic_denial') is True and
            type(baseline.get('failed_assertions')) is int and baseline['failed_assertions'] == 2,
            'Both projection regression fixes required')
    require(sha(rooted(baseline['report_path'])) == baseline['report_sha256'] and
            sha(rooted(baseline['baseline_log_path'])) == baseline['baseline_log_sha256'], 'Projection baseline proof changed')
    cleanup = proof.get('cleanup', {})
    require(cleanup.get('private_port') == 2599 and cleanup.get('connection_refused') is True and
            cleanup.get('matching_private_processes') == [], 'TCP private cleanup proof absent')
    return proof


def empty_native_cache(cache):
    require(isinstance(cache, dict) and type(cache.get('count')) is int and cache['count'] == 0 and
            cache.get('rows_hex') == [] and cache.get('by_name') == {}, 'Native75 cache not empty')


def native_identities(values, label):
    require(isinstance(values, list) and len(values) == 3 and all(isinstance(v, dict) and
            type(v.get('identity')) is int for v in values) and {v['identity'] for v in values} == {4, 5, 6}, label)


def native75_producer(producer):
    require(isinstance(producer, dict), 'Native75 producer missing')
    require(all(type(producer.get(k)) is int and producer[k] == v for k, v in
            (('main_control', 25), ('modal_mode', 5))), 'Native75 control/mode differs')
    require(type(producer.get('modal_widget')) is int and producer['modal_widget'] >= 0 and
            isinstance(producer.get('target_pointer'), str) and int(producer['target_pointer'], 16) > 0 and
            producer.get('self_row_hex') == '0003' and producer.get('native75_body_hex') == '7500' and
            producer.get('producer') == '004EE560 case5 -> 004EF800 -> 004132E0' and
            producer.get('packet_capture_claimed') is False and producer.get('normal_WM_only') is True,
            'Native75 must be normal WM self0/founder3 producer, not injection')


def validate_native75(ui, locale):
    base.true_fields(ui, ('disband_actual_client_accepted',), 'Native75 acceptance')
    event = ui.get('native75_guild_disband', {})
    base.true_fields(event, ('accepted', 'cancel_sql_exact', 'cancel_sent_no75', 'all_unrelated_tables_exact',
        'announcement_history_exact', 'retained_guild_identity', 'target_2D_name_cleared', 'founder_2D_name_cleared',
        'all_cached92_slots_cleared', 'both_clients_still_running', 'relogin_membership_absent'), 'Native75 flow')
    require(event.get('all_affected_permissions_invalidated') is None and
            event.get('permission_evidence_scope') == 'Native panels close/cache empty + subsequent normal relogin; internal server permissions not observable through VM_READ client',
            'Internal permission evidence must remain unobservable; exact TCP proof provides anti-borrowing')
    require(event.get('rendered_pixels_tested') is False and event.get('native75_ack_claimed') is False,
            'Native75 must not invent rendered pixel/ack proof')
    require(type(event.get('simultaneous_native_clients')) is int and event['simultaneous_native_clients'] == 3 and
            event.get('captured_audience_ids') == [4, 5, 6] and all(type(v) is int for v in event['captured_audience_ids']),
            'Native75 complete accepted plus pending audience required')
    native75_producer(event.get('actual_native75_self0')); native75_producer(event.get('cancel_producer'))
    gid = event.get('guild_id'); clock = event.get('revision_clock')
    require(type(gid) is int and gid > 0 and type(clock) is int, 'Native75 guild identity/clock differs')
    before, after = event.get('SQL_before'), event.get('SQL_after')
    require(isinstance(before, dict) and isinstance(after, dict) and set(before) == set(after) == {'schema', 'tables'} and
            before['schema'] == after['schema'] and isinstance(before['tables'], dict) and
            set(before['tables']) == set(after['tables']) and set(DISBAND_TABLES) <= set(before['tables']),
            'Native75 full SQL schema/table snapshot absent')
    delta = event.get('SQL_delta', {})
    require(set(delta) == set(DISBAND_TABLES), 'Native75 allowed SQL delta differs')
    parsed_before = {}; parsed_after = {}
    for table, old_values in before['tables'].items():
        new_values = after['tables'][table]
        old_rows, new_rows = tuple_rows(old_values), tuple_rows(new_values)
        if table not in DISBAND_TABLES:
            require(old_values == new_values, 'Native75 changed unrelated rows/schema/history/announcement: ' + table)
        else:
            require(delta[table] == {'before': old_values, 'after': new_values}, 'Native75 delta/snapshot mismatch: ' + table)
            parsed_before[table], parsed_after[table] = old_rows, new_rows
    guilds = parsed_before['owned_guilds']
    require(guilds and all(len(row) >= 3 and type(row[0]) is int and type(row[2]) is int for row in guilds),
            'Native75 guild rows malformed')
    require(clock == max(row[2] for row in guilds) + 1, 'Native75 global owned guild revision clock differs')
    require(len([row for row in guilds if row[0] == gid]) == 1, 'Native75 retained guild missing/ambiguous')
    expected = [(row[0], row[1], clock, *row[3:]) if row[0] == gid else row for row in guilds]
    require(sorted(map(repr, parsed_after['owned_guilds'])) == sorted(map(repr, expected)),
            'Native75 changed retained name/identity/opaque or foreign guild')
    for table, index in (('owned_guild_members', 1), ('owned_guild_governance_0078', 0), ('owned_guild_applications_0078', 1)):
        old = parsed_before[table]
        require(all(len(row) > index and type(row[index]) is int for row in old), 'Native75 malformed identity row')
        require(sorted(map(repr, parsed_after[table])) == sorted(repr(row) for row in old if row[index] != gid),
                'Native75 did not remove exactly target rows: ' + table)
    members = [row for row in parsed_before['owned_guild_members'] if row[1] == gid]
    pending = [row for row in parsed_before['owned_guild_applications_0078'] if row[1] == gid]
    governance = [row for row in parsed_before['owned_guild_governance_0078'] if row[0] == gid]
    require(len(members) == 2 and {row[0] for row in members} == {4, 5} and len(pending) == 1 and len(pending[0]) > 4 and
            pending[0][4] == 6 and len(governance) == 1 and len(governance[0]) > 2 and governance[0][2] == 4,
            'Native75 founder/member/pending SQL identities differ')
    for label, parsed in (('tables_before', parsed_before), ('tables_after', parsed_after)):
        raw = event.get(label)
        require(isinstance(raw, dict) and set(raw) == set(DISBAND_TABLES), 'Native75 explicit typed table set missing')
        require(event.get('table_rows_encoding') == 'python-repr-typed-sql-v1', 'Native75 typed rows encoding missing')
        for table in DISBAND_TABLES:
            require(sorted(map(repr, tuple_rows(raw[table]))) == sorted(map(repr, parsed[table])),
                    'Native75 full tuple/table snapshot mismatch: ' + table)
    require(event.get('announcement_before') == event.get('announcement_after') and
            'owned_guild_announcements_0078' in before['tables'], 'Native75 announcement preservation proof absent')
    log = event.get('commit_log', '')
    import re
    require(isinstance(log, str) and re.search(r'OWNED_GUILD_DISBAND session_id=\d+ character_id=4 slot=0 guild_id=' +
            str(gid) + r' members=2 pending=1 committed=true CUSTOM-0081\b', log), 'Native75 precise server commit missing')
    observations = event.get('native_clear_observations'); native_identities(observations, 'All three native75 consumers required')
    for observation in observations:
        identity = observation['identity']
        require(observation.get('actor_guild_name_hex') == '' and observation.get('panels_closed') is True and
                observation.get('previously_member') is (identity in (4, 5)) and
                observation.get('pending_applicant_no_membership_fabricated') is (identity == 6), 'Native75 audience projection differs')
        empty_native_cache(observation.get('cache'))
    common = event.get('frozen_common_chat_after_disband', {})
    base.true_fields(common, ('accepted', 'SQL_exact'), 'Native75 frozen common chat')
    token = 'disband81-common-' + str(locale)
    require(common.get('token') == token and common.get('native_input_hex') == token.encode('ascii').hex(), 'Native75 common input differs')
    receivers = common.get('native_archive_receivers'); native_identities(receivers, 'Native75 three common receivers required')
    for receiver in receivers:
        require(type(receiver.get('count')) is int and 1 <= receiver['count'] <= 200 and
                b'fixedgirl: ' + token.encode('ascii') in bytes.fromhex(receiver.get('common_text_hex', '')),
                'Native75 common sender/text consumption absent')
    require(isinstance(common.get('server_log'), str) and 'NATIVE_CHAT_ACCEPTED ' in common['server_log'] and
            'recipients=3' in common['server_log'], 'Native75 common audience differs')
    relogins = event.get('relogin_observations'); native_identities(relogins, 'Three native75 relogins required')
    for record in relogins:
        require(record.get('guild_name_hex') == '' and record.get('SQL_exact') is True, 'Native75 relogin restored state')
        empty_native_cache(record.get('cache'))
    return event


def validate_receipt(receipt, contract, contract_sha):
    # Existing immutable validator covers both announcement locales, real79
    # denied draft restoration, frozen/source/DB/process/desktop preservation.
    ann.validate_receipt(receipt, contract, contract_sha)
    for case in receipt['cases']:
        require(sha(kick.__file__) == KICK_HELPER_SHA, 'Immutable native72 release validator changed')
        kick.validate_native_kick(case['ui'], case['locale'])
        validate_native75(case['ui'], case['locale'])
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
