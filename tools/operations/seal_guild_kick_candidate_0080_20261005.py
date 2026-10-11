"""Seal a candidate only. No clients, listeners, formal save/config writes."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    folder = ROOT / 'artifacts/research/native-guild-management-0080/kick-live-v01'
    folder.mkdir(exist_ok=False)
    candidate = ROOT / 'build-native-guild-kick-20261005/Release/god2-server.exe'
    assert sha(candidate) == '619f04ce6a09bdc2307e59a2d82f9db0bf7a92d4d81fee710843bf63b27d973e'
    junit = ROOT / 'artifacts/research/native-guild-management-0080/kick-regressions-20261005-v02.xml'
    tests = ET.parse(junit).getroot()
    assert int(tests.attrib['tests']) == 13 and int(tests.attrib.get('failures', '0')) == 0
    tcp = ROOT / 'artifacts/research/native-guild-management-0080/kick-tcp-20261005-v03.log'
    text = tcp.read_text('utf-8')
    assert 'Ran 5 tests' in text and text.strip().endswith('OK') and 'FAILED' not in text
    gate = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-m', 'tools.operations.verify_frozen_chat_20260927'],
        cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True)
    assert json.loads(gate.stdout)['accepted']
    write_new(folder / 'frozen-gate.json', json.loads(gate.stdout))
    registry = ROOT / 'docs/custom-designs.json'
    original = json.loads(registry.read_text('utf-8'))
    updated = copy.deepcopy(original)
    assert not any(record['id'] == 'CUSTOM-0080' for record in original['designs'])
    updated['designs'].append({
        'id': 'CUSTOM-0080', 'name': 'Founder native72 ordinary accepted-member kick',
        'authority': 'NATIVE_WIRE_WITH_CUSTOM_AUTHORIZATION_POLICY',
        'implementation': ['src/handlers/OwnedGuildKickService.h', 'src/handlers/OwnedGuildLeaderPanelService.h',
            'src/db/SqliteOwnedGuildMembershipRepository.h', 'src/db/SqliteOwnedGuildMembershipRepository.cpp', 'src/core/Application.cpp'],
        'native_gap': 'Original-server kick restrictions, officer powers, cooldowns/fees and consent policy are unrecovered. Native main19/modal3/72slot and2D/91/92 consumers are build-matched; member role1 removal distinct from pending role0 rejection.',
        'rules': [
            'Only persisted founder may remove another ordinary accepted member from a complete freshly explicit published panel. Client role/local slot only select action kind, never SQL/account authority. No officer, fee, reward or guild-name reuse invented.',
            'Founder immutable world/SQL/publication serial and full roster/applications plus target exact identity/membership are rechecked under BEGIN IMMEDIATE paired proofs. Permission is single-use even on SQL failure.',
            'CUSTOM nonbattle policy for both founder and target; every connected target must currently have qualified world projection, offline targets require saved nonbattle identity. Target movement while ready is not an immutable ABA lease and need not deny removal.',
            'Only target membership DELETE and monotonic retained guildrevision may change. Preserve governance, pending applications, announcement history, all other typed rows/schema and every opaque retained guild column. No new migration or save replacement.',
            'Native72 role1 is routed separately before frozen pending rejection. Capture once before prefixes; revoke at each success/denial boundary BEFORE suffix recursion and after the whole batch. Samebatch help+deniedkick+approve/reject cannot borrow new authority.',
            'Invalidate entry/member/leader/announcement authorities for every affected connected member/applicant before readonly projections. Existing qualified2D clears guildname,92 clears target roster/panel; current SQL guildchat rejects target immediately. Frozen common chat remains unchanged.',
            'Denied kick sends only a localized existing reserved-sender common notice and qualified readonly roster; explicit help must reopen authority. Native cancel emits no request and preserves rows.',
        ],
        'field_origins': {'native72_role_context_and2D91_92': 'NATIVE_VERIFIED',
            'founder_singleuse_nonbattle_readiness_policy': 'CUSTOM_DESIGNED', 'fees_officers_original_restrictions': 'UNRECOVERED'},
        'activation': 'CANDIDATE_RUNTIME_INTEGRATED_AWAITING_CURRENT_NATIVE_CLIENT_ACCEPTANCE_NOT_FORMAL',
        'tests': ['tests/storage_owned_guild_kick_0080.cpp', 'tests/test_owned_guild_kick_0080.cpp',
            'tests/research/test_native_guild_kick_server_20261005.py'],
        'evidence': ['artifacts/research/native-guild-management-0080/next-route-v01/report.json',
            'artifacts/research/native-guild-management-0080/kick-plan-v01/report.json',
            'artifacts/research/native-guild-management-0080/kick-runtime-review-v01/report.json',
            'artifacts/research/native-guild-kick-0080/storage-v01/additive-source-proof.json'],
        'acceptance': {'ctest_groups': 13, 'ctest_passed': 13, 'Application_TCP_tests_passed': 5,
            'runtime_integrated': True, 'formal_installed': False, 'actual_client_acceptance': False,
            'current_native_workflow_percent': 0, 'whole_game_percent': None,
            'candidate_sha256': sha(candidate), 'report': str(folder.relative_to(ROOT))},
        'replacement': 'Replace custom restrictions only with independently build-matched original server authority and preserved-save live regressions.'})
    assert updated['designs'][:-1] == original['designs']
    (folder / 'custom-designs.before.json').write_bytes(registry.read_bytes())
    registry.write_text(json.dumps(updated, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    accepted_contract = ROOT / 'artifacts/research/native-guild-announcement-0079/post-install-v01/contract.json'
    contract = json.loads(accepted_contract.read_text('utf-8'))
    names = set(contract['source_sha256'])
    names.update(['src/handlers/OwnedGuildKickService.h', 'tests/storage_owned_guild_kick_0080.cpp',
        'tests/test_owned_guild_kick_0080.cpp', 'tests/research/test_native_guild_kick_server_20261005.py',
        'tools/strike_lab/private_guild_kick_0080_v01_20261005.py',
        'tools/operations/seal_guild_kick_candidate_0080_20261005.py',
        'tools/operations/announcement_postinstall_closeout_20261005.py'])
    source_pins = {name: sha(ROOT / name) for name in sorted(names)}
    contract.update(design='CUSTOM-0080', feature_family='guild-kick0080',
        scope='CURRENT_NATIVE_CANCEL_KICK_TWO_CONNECTED_PLAYERS_POSTKICK_COMMON_CHAT_AND_RELOGIN_PLUS_ANNOUNCEMENT_REGRESSION',
        candidate_path=str(candidate.relative_to(ROOT)).replace('\\', '/'), candidate_sha256=sha(candidate),
        helper_path='tools/strike_lab/private_guild_kick_0080_v01_20261005.py',
        helper_sha256=source_pins['tools/strike_lab/private_guild_kick_0080_v01_20261005.py'],
        source_sha256=source_pins, live_accepted=False,
        sealed_at_utc=datetime.now(timezone.utc).isoformat(),
        reason='New72 member route, native samebuild producer/consumer, explicit CUSTOM0080 policy. Formal EXE/save/config/client/resources protected; no SQL guild membership seed.',
        supersedes_attempt_contract=None, formal_release=None)
    contract.pop('static_test_path', None)
    write_new(folder / 'contract.json', contract)
    write_new(folder / 'candidate-verification.json', {'accepted_for_native_test': True, 'formal_installed': False,
        'ctest': {'path': str(junit.relative_to(ROOT)), 'sha256': sha(junit), 'passed': 13},
        'TCP': {'path': str(tcp.relative_to(ROOT)), 'sha256': sha(tcp), 'passed': 5, 'live_client': False},
        'candidate_sha256': sha(candidate), 'source_files': len(source_pins),
        'test_fixture_repair': 'Membership admission fixture explicitly disables dependent announcements in both copied Config comparisons; production dependency guard unchanged.',
        'frozen_chat_gate_passed': True, 'whole_game_percent': None})
    print(json.dumps({'accepted_for_native_test': True, 'contract': str(folder / 'contract.json'), 'source_files': len(source_pins)}))


if __name__ == '__main__':
    main()
