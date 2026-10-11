"""Seal installed CUSTOM-0081 native acceptance; writes new evidence only."""
import json
from datetime import datetime, timezone
from pathlib import Path

from tools.operations import owned_guild_disband_release_v02_20261005 as release

ROOT = Path(__file__).resolve().parents[2]


def main():
    previous = ROOT / 'artifacts/research/native-guild-management-0081/disband-live-v02/contract.json'
    directory = ROOT / 'artifacts/releases/owned-guild-disband-20261005-01'
    installed = release.managed.ACTIVE.resolve()
    contract = release.read(previous)
    compiled = release.rooted(contract['candidate_path'])
    release.validate_contract(previous, compiled)
    info, applied = release.validate_installed_release(directory)
    release.require(release.sha(installed) == contract['candidate_sha256'] == applied['candidate_sha256'],
                    'Installed and accepted compiled candidate differ')
    release.require(release.rooted(info['candidate_original_path']) == compiled,
                    'Installed original build identity differs')
    names = (
        'tools/operations/owned_guild_disband_release_v02_20261005.py',
        'tools/operations/disband_postinstall_closeout_20261005.py',
        'tools/operations/seal_guild_disband_postinstall_20261005.py',
    )
    contract['source_sha256'].update({name: release.sha(ROOT / name) for name in names})
    contract.update(
        candidate_path=installed.relative_to(ROOT).as_posix(),
        tcp_candidate_path=compiled.relative_to(ROOT).as_posix(),
        formal_release=directory.relative_to(ROOT).as_posix(),
        sealed_at_utc=datetime.now(timezone.utc).isoformat(),
        supersedes_attempt_contract=previous.relative_to(ROOT).as_posix(),
        supersedes_attempt_contract_sha256=release.sha(previous),
        reason='Installed same-schema50 binary; repeat full original native79/72/75 workflows in both950/936 isolated owned fixtures. No formal grants, save replacement or client changes.',
    )
    release.validate_tcp_receipt(contract, installed)
    output = ROOT / 'artifacts/research/native-guild-management-0081/post-install-v01'
    release.require(not output.exists(), 'Unused immutable postinstall output required')
    output.mkdir(exist_ok=False)
    release.write_new(output / 'contract.json', contract)
    release.write_new(output / 'installation-proof.json', {
        'accepted_for_postinstall_native_test': True,
        'formal_installed': True,
        'owned_pid': applied['owned_pid'],
        'apply_result_sha256': release.sha(directory / 'apply-result.json'),
        'candidate_sha256': release.sha(installed),
        'compiled_candidate_path': contract['tcp_candidate_path'],
        'same_schema50_typed_save_exact_before_start': True,
        'database_replaced': False,
        'config_changed': False,
        'resources_changed': False,
        'source_files': len(contract['source_sha256']),
        'actual_client_postinstall_accepted': False,
        'whole_game_percent': None,
    })
    print(json.dumps({'accepted_for_postinstall_native_test': True,
                      'contract': str(output / 'contract.json')}))


if __name__ == '__main__':
    main()
