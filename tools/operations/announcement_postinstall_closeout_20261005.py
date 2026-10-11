"""Publish immutable announcement0079 post-install proof; metadata-only update."""
import copy
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.operations import owned_guild_announcement_release_v01_20261004 as release


def load(path):
    return json.loads(path.read_text('utf-8'))


def sha(path):
    return hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()


def write_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.write('\n')


def main():
    contract_path = ROOT / 'artifacts/research/native-guild-announcement-0079/post-install-v01/contract.json'
    receipt_path = ROOT / 'artifacts/playtests/ga-20261005-02/run-result.json'
    output = ROOT / 'artifacts/research/native-guild-announcement-0079/implementation-final-v01'
    output.mkdir(parents=True, exist_ok=False)
    contract, receipt = load(contract_path), load(receipt_path)
    assert receipt['accepted'] and receipt['contract_sha256'] == sha(contract_path)
    release.validate_receipt(receipt, contract, sha(contract_path))
    assert all(receipt[key] for key in ('sources_unchanged', 'protected_files_unchanged',
        'protected_DB_exact', 'frozen_unchanged', 'protected_processes_exact',
        'desktop_unchanged', 'foreground_unchanged', 'candidate_unchanged'))
    for name, expected in contract['source_sha256'].items():
        assert sha(ROOT / name) == expected, name
    assert sha(ROOT / contract['candidate_path']) == contract['candidate_sha256']
    registry_path = ROOT / 'docs/custom-designs.json'
    original_bytes = registry_path.read_bytes()
    original = load(registry_path)
    updated = copy.deepcopy(original)
    design = next(record for record in updated['designs'] if record['id'] == 'CUSTOM-0078')
    announcement = design['announcement_candidate']
    announcement.update(status='FORMAL_INSTALLED_POSTINSTALL_CURRENT_NATIVE_CLIENT_ACCEPTED',
        post_install_acceptance=True,
        post_install_receipt=str(receipt_path.relative_to(ROOT)).replace('\\', '/'),
        post_install_receipt_sha256=sha(receipt_path),
        report=str((output / 'report.json').relative_to(ROOT)).replace('\\', '/'),
        verification_scope='13 CTest groups and7 Python checks PASS. Installed4972 executable plus current formal config: normal/cancel/denied-save restore/member/relogin native UI ASCII950/936 accepted2/2. Formal inplace50 retained prior typed saves; no client/resource changes, fixture grants, Chinese IME or rendered-pixel claim.')
    # All other designs and fields remain identical, including frozen metadata.
    restored = copy.deepcopy(updated)
    next(record for record in restored['designs'] if record['id'] == 'CUSTOM-0078')['announcement_candidate'] = next(record for record in original['designs'] if record['id'] == 'CUSTOM-0078')['announcement_candidate']
    assert restored == original
    (output / 'custom-designs.before.json').write_bytes(original_bytes)
    registry_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    differences = {name: {'accepted': expected, 'current': sha(ROOT / name)}
        for name, expected in contract['source_sha256'].items() if sha(ROOT / name) != expected}
    assert set(differences) == {'docs/custom-designs.json'}, differences
    snapshot = release.capture(ROOT / 'artifacts/playtests/persistent-launch-20260923-01/town-diagnostic-accounts.db')
    write_new(output / 'formal-storage-postcheck.json', snapshot)
    report = {'accepted': True, 'utc': datetime.now(timezone.utc).isoformat(),
        'scope_percent': 100, 'scope': 'ANNOUNCEMENT0079_NATIVE_ASCII_TW_CN_CURRENT_INSTALLED_EXECUTABLE',
        'whole_game_percent': None, 'formal_installed': True, 'post_install_acceptance': True,
        'candidate_sha256': contract['candidate_sha256'], 'schema_version': snapshot['history'][-1][0],
        'receipt': str(receipt_path.relative_to(ROOT)), 'receipt_sha256': sha(receipt_path),
        'contract': str(contract_path.relative_to(ROOT)), 'contract_sha256': sha(contract_path),
        'formal_apply': 'artifacts/releases/owned-guild-announcement-20261005-01/apply-result.json',
        'postacceptance_documentation_only_delta': differences,
        'all_compiled_runtime_tools_tests_client_resources_unchanged': True,
        'all_unrelated_registry_values_exact': True,
        'accepted_guards': {key: receipt[key] for key in ('sources_unchanged', 'protected_files_unchanged',
            'protected_DB_exact', 'frozen_unchanged', 'protected_processes_exact', 'desktop_unchanged', 'foreground_unchanged')},
        'cases': [{'locale': case['locale'], 'accepted': case['accepted'],
            'native_ui_accepted': case['ui']['announcement_actual_client_accepted'],
            'denied_save_restored': case['ui']['announcement_denied_save_restore']['accepted'],
            'owned_processes_closed': case['all_owned_processes_closed'],
            'private_port_released': case['exclusive_2598_released']} for case in receipt['cases']],
        'limits': ['CUSTOM0078 owner/lease/help policy; not original-server rules.',
            'Actual authored announcement text ASCII in950/936; no Chinese IME or rendered pixels claim.',
            'Postinstall verification used isolated private fixtures against installed formal EXE/config; no formal fixture grants.',
            'Full-game packet denominator and percentage unknown; guild kick/transfer/disband/officer routes remain open.']}
    write_new(output / 'report.json', report)
    print(json.dumps({'accepted': True, 'report': str(output / 'report.json'), 'locales': 2}))


if __name__ == '__main__':
    main()
