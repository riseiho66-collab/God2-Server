"""Seal typed-row QA repair only; native75 compiled runtime stays identical."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


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
    previous = home / 'disband-live-v01/contract.json'
    contract = read(previous)
    for name, expected in contract['source_sha256'].items():
        assert sha(ROOT / name) == expected, name
    assert sha(ROOT / contract['candidate_path']) == contract['candidate_sha256']
    receipt_path = ROOT / 'artifacts/playtests/gd-20261005-01/run-result.json'
    receipt = read(receipt_path)
    assert receipt['accepted'] is False
    assert all(receipt[k] is True for k in (
        'sources_unchanged', 'candidate_unchanged', 'protected_files_unchanged', 'protected_DB_exact',
        'frozen_unchanged', 'protected_processes_exact', 'desktop_unchanged', 'foreground_unchanged'))
    assert len(receipt['cases']) == 1
    assert all(receipt['cases'][0][k] is True for k in (
        'all_owned_processes_closed', 'exclusive_2598_released', 'all_private_images_closed'))
    terminal = read(home / 'native-launch-v01/terminal-classification.json')
    assert terminal['classification'] == 'ROOT_MANUAL_QA_ABORT_KNOWN_HELPER_BLOB_JSON_SERIALIZATION_DEFECT_NOT_RUNTIME_FAILURE'
    assert terminal['receipt_sha256'] == sha(receipt_path)
    final_path = home / 'helper-static-v02/final-manifest.json'
    final = read(final_path)
    assert final['encoding'] == 'python-repr-typed-sql-v1'
    assert final['tests_passed'] is True and final['test_count'] == 14
    assert final['actual_inherited_dump_v01_blob_failure_reproduced'] is True
    assert final['actual_inherited_dump_v02_event_whole_UI_and_actual_announcement_history_roundtrip'] is True
    for name, expected in final['file_sha256'].items():
        assert sha(ROOT / name) == expected, name
    helper = 'tools/strike_lab/private_guild_disband_0081_v02_20261005.py'
    phase = 'artifacts/research/native-guild-management-0081/helper-static-v02/disband_phase.py'
    assert sha(ROOT / helper) == '78ad91b6abde621ac81080b2ec891fa1c77f37cd8d76e42df79fcf3a54c8711f'
    assert sha(ROOT / phase) == '7082260525db3a1775ec5be37b035992c2d04fe67db9443860907e68aa746180'
    result = subprocess.run([sys.executable, '-X', 'utf8', '-B', str(home / 'helper-static-v02/test_helper_static.py')],
                            cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True)
    out = home / 'disband-live-v02'
    out.mkdir(exist_ok=False)
    (out / 'helper-regressions.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    names = set(final['file_sha256'])
    names.update((final_path.relative_to(ROOT).as_posix(),
                  'tools/operations/seal_guild_disband_helper_v02_20261005.py'))
    contract['source_sha256'].update({name: sha(ROOT / name) for name in names})
    contract.update(helper_path=helper, helper_sha256=sha(ROOT / helper),
                    tcp_candidate_path=contract['candidate_path'],
                    sealed_at_utc=datetime.now(timezone.utc).isoformat(),
                    supersedes_attempt_contract=previous.relative_to(ROOT).as_posix(),
                    supersedes_attempt_contract_sha256=sha(previous),
                    reason='QA-only typed-row JSON encoding repair. v01 root manual abort and all guards retained; same compiled8eaac runtime/source/config/resources/save. Normal native waits and SQL validation remain exact; no native75 acceptance claimed.')
    write(out / 'contract.json', contract)
    write(out / 'repair-proof.json', {
        'accepted_for_native_test': True, 'compiled_candidate_unchanged': True,
        'old_source_closure_exact': True, 'registry_unchanged': True,
        'helper_static_regressions_passed': 14, 'actual_client_acceptance': False,
        'formal_installed': False, 'candidate_sha256': contract['candidate_sha256'],
        'terminal_v01_receipt_sha256': sha(receipt_path),
        'terminal_classification_sha256': sha(home / 'native-launch-v01/terminal-classification.json'),
        'typed_receipt_encoding': final['encoding'], 'source_files': len(contract['source_sha256']),
        'whole_game_percent': None})
    print(json.dumps({'accepted_for_native_test': True, 'contract': str(out / 'contract.json'),
                      'source_files': len(contract['source_sha256'])}))


if __name__ == '__main__':
    main()
