"""Seal native75 candidate for owned hidden-client QA; no service/save writes."""
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_SHA = '8eaac6f7e40348585500428007b74cd9656748afdedabdca5a034433805c325b'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text('utf-8'))


def write(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def main():
    home = ROOT / 'artifacts/research/native-guild-management-0081'
    candidate = ROOT / 'build-native-guild-disband-20261005/Release/god2-server.exe'
    assert sha(candidate) == CANDIDATE_SHA
    assert sha(ROOT / 'build-town-visibility/Release/god2-server.exe') == '619f04ce6a09bdc2307e59a2d82f9db0bf7a92d4d81fee710843bf63b27d973e'
    assert read(home / 'integration-v01/build-full-v01-result.json')['exit_code'] == 0
    assert read(home / 'projection-fix-v01/build-v01-result.json')['exit_code'] == 0
    unit = read(home / 'integration-v01/ctest-full-v01-result.json')
    assert unit['accepted'] is True and unit['tests'] == 17
    tcp_path = home / 'tcp-tests-v01/report.json'
    tcp = read(tcp_path)
    assert tcp['accepted'] is True and tcp['tests_passed'] == 7
    assert tcp['candidate_sha256'] == CANDIDATE_SHA
    assert all(tcp[k] is True for k in ('production_source_unchanged', 'formal_binary_unchanged', 'env_lab_false'))
    assert tcp['actual_client_acceptance'] is False
    assert read(home / 'projection-fix-review-v01/report.json')['accepted_static_review'] is True
    static = read(home / 'helper-static-v01/report.json')
    assert static['tests_exit'] == 0 and static['tests_passed'] is True and static['test_count'] == 11
    helper = 'tools/strike_lab/private_guild_disband_0081_v01_20261005.py'
    phase = 'artifacts/research/native-guild-management-0081/helper-static-v01/disband_phase.py'
    assert sha(ROOT / helper) == '8e2e950720d4303a7e24a9db749f8a3937aa2df651c66fe56886b39ee1f4a8ee'
    assert sha(ROOT / phase) == '37dc25e12ea2ca9fa81eb9f9ce54c95fd00125604c3c30b5d11a26cee26102e1'
    gate = subprocess.run([sys.executable, '-X', 'utf8', '-B', '-m', 'tools.operations.verify_frozen_chat_20260927'],
                          cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True)
    frozen = json.loads(gate.stdout)
    assert frozen['accepted'] is True
    out = home / 'disband-live-v01'
    out.mkdir(exist_ok=False)
    registry = ROOT / 'docs/custom-designs.json'
    before = read(registry)
    updated = copy.deepcopy(before)
    entries = [v for v in updated['designs'] if v['id'] == 'CUSTOM-0081']
    assert len(entries) == 1
    entry = entries[0]
    entry['activation'] = 'CANDIDATE_SERVER_CPP_TCP_VERIFIED_AWAITING_CURRENT_NATIVE_CLIENT_ACCEPTANCE_NOT_FORMAL'
    entry['acceptance'].update(full_Application_candidate_compiled=True, Application_TCP_accepted=True,
                               ctest_groups_passed=17, Application_TCP_tests_passed=7,
                               actual_client_acceptance=False, formal_installed=False,
                               current_native_workflow_percent=0, whole_game_percent=None,
                               candidate_sha256=CANDIDATE_SHA)
    entry['tests'].append('tests/research/test_native_guild_disband_server_20261005.py')
    entry['rules'].append('Native75 projection readability preflight uses frozen private_chat_peer outside SQL proof before usable lease capture and after each prefix. Missing role/resources or unsupported stored codepage denies retirement rather than leaving a live stale guild name; paired transaction proof stays world-only.')
    entry['evidence'].extend([str(p.relative_to(ROOT)).replace('\\', '/') for p in (
        tcp_path, home / 'projection-fix-v01/source-proof.json', home / 'projection-fix-review-v01/report.json')])
    assert [d for d in updated['designs'] if d['id'] != 'CUSTOM-0081'] == [d for d in before['designs'] if d['id'] != 'CUSTOM-0081']
    (out / 'custom-designs.before.json').write_bytes(registry.read_bytes())
    registry.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    old_path = ROOT / 'artifacts/research/native-guild-management-0080/post-install-v01/contract.json'
    contract = read(old_path)
    additions = read(home / 'integration-v01/source-addition-proof.json')['after']
    names = set(contract['source_sha256']) | set(additions)
    names.update((helper, phase, 'tools/operations/seal_guild_disband_candidate_0081_20261005.py',
                  'tools/operations/integrate_disband_candidate_0081_20261005.py',
                  'tools/operations/add_disband_projection_preflight_0081_20261005.py',
                  'tests/research/test_native_guild_disband_server_20261005.py',
                  'artifacts/research/native-guild-management-0081/disband-plan-v01/report.json',
                  'artifacts/research/native-guild-management-0081/helper-static-v01/test_helper_static.py',
                  'artifacts/research/native-guild-management-0081/helper-static-v01/report.json'))
    names.update(str(p.relative_to(ROOT)).replace('\\', '/') for p in (
        tcp_path, home / 'integration-v01/ctest-full-v01-result.json',
        home / 'projection-fix-v01/source-proof.json', home / 'projection-fix-review-v01/report.json'))
    pins = {name: sha(ROOT / name) for name in sorted(names)}
    contract.update(design='CUSTOM-0081', feature_family='guild-disband0081',
                    scope='CURRENT_NATIVE_CANCEL_DISBAND_THREE_CONNECTED_ACCEPTED_PENDING_PLAYERS_NAME_ROSTER_CLEAR_COMMON_CHAT_RELOGIN_PLUS_FULL_ANNOUNCEMENT_KICK_REGRESSION',
                    candidate_path=candidate.relative_to(ROOT).as_posix(), candidate_sha256=CANDIDATE_SHA,
                    helper_path=helper, helper_sha256=pins[helper], source_sha256=pins,
                    tcp_receipt_path=tcp_path.relative_to(ROOT).as_posix(), tcp_receipt_sha256=sha(tcp_path),
                    live_accepted=False, formal_release=None, supersedes_attempt_contract=None,
                    sealed_at_utc=datetime.now(timezone.utc).isoformat(),
                    reason='Native75 producer/consumer and CUSTOM0081 retirement policy. Candidate TCP7/7 plus old guild CTest17/17; no current-client acceptance or formal install claimed.')
    contract.pop('static_test_path', None)
    write(out / 'contract.json', contract)
    write(out / 'frozen-gate.json', frozen)
    write(out / 'candidate-verification.json', {
        'accepted_for_native_test': True, 'formal_installed': False,
        'ctest_passed': 17, 'TCP_passed': 7, 'helper_static_passed': 11,
        'source_files': len(pins), 'candidate_sha256': CANDIDATE_SHA,
        'actual_client_acceptance': False, 'whole_game_percent': None})
    print(json.dumps({'accepted_for_native_test': True, 'contract': str(out / 'contract.json'), 'source_files': len(pins)}))


if __name__ == '__main__':
    main()
