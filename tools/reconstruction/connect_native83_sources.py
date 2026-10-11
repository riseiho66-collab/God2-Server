"""Connect the retained native83 implementation to formal sources only.

Owner 2026-10-06 sequencing: source connections now, all testing later.
No build, tests, server restart, configuration activation or SQLite operation.
"""
import hashlib
import json
from pathlib import Path
from tools.reconstruction.archive_inputs import ArchivedInputs, SERVER

BASE = 'artifacts/research/native-guild-founder-transfer-0083/'
STAGING = BASE + 'formal83-release-preparation-v07/'
OUT = SERVER / 'artifacts/integration/packet-connections-20261006/native83-source'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    archive = ArchivedInputs()
    try:
        phase = json.loads(archive.read(BASE + 'root-source-phase-preparation-v01/source-phase-draft.json'))
        registry_path = SERVER / phase['registry_CAS']['path']
        registry_before = registry_path.read_bytes()
        if digest(registry_before) != phase['registry_CAS']['before']:
            raise RuntimeError('Registry changed since retained source plan')
        # Use the original prepared inactive registry bytes, rather than
        # relabeling candidate/client acceptance as formal activation.
        changes = []
        for name, row in phase['replacements'].items():
            target = SERVER / name
            before = target.read_bytes()
            if digest(before) != row['before']:
                raise RuntimeError('Concurrent formal source change: ' + name)
            after = archive.read(STAGING + 'staged-source/' + name)
            if digest(after) != row['after']:
                raise RuntimeError('Retained source payload differs: ' + name)
            changes.append((target, before, after))
        for name, pin in phase['additions'].items():
            target = SERVER / name
            if target.exists():
                raise FileExistsError(target)
            after = archive.read(STAGING + 'staged-source/' + name)
            if digest(after) != pin:
                raise RuntimeError('Retained source addition differs: ' + name)
            changes.append((target, None, after))

        # Locate the exact inactive registry prepared in the source manifest.
        registry_candidates = [
            BASE + 'root-source-phase-preparation-v01/inactive-registry.json',
            BASE + 'root-source-phase-preparation-v01/registry-after.json',
            STAGING + 'staged-source/docs/custom-designs.json',
        ]
        registry_after = None
        for name in registry_candidates:
            try:
                raw = archive.read(name)
            except FileNotFoundError:
                continue
            if digest(raw) == phase['registry_CAS']['after']:
                registry_after = raw
                break
        if registry_after is None:
            raise RuntimeError('Exact prepared inactive registry payload not located')
        OUT.mkdir(parents=True, exist_ok=False)
        written = []
        try:
            (OUT / 'registry-before.json').write_bytes(registry_before)
            registry_path.write_bytes(registry_after)
            for target, before, after in changes:
                relative = target.relative_to(SERVER)
                if before is not None:
                    backup = OUT / 'before' / relative
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    backup.write_bytes(before)
                target.parent.mkdir(parents=True, exist_ok=True)
                if before is None:
                    with target.open('xb') as stream:
                        stream.write(after)
                else:
                    target.write_bytes(after)
                written.append((target, before, after))
        except BaseException:
            for target, before, after in reversed(written):
                if before is None:
                    if target.read_bytes() == after:
                        target.unlink()
                else:
                    target.write_bytes(before)
            registry_path.write_bytes(registry_before)
            raise
        result = {
            'kind': 'FORMAL_NATIVE83_SOURCE_CONNECTION_PHASE',
            'owner_directive': '2026-10-06 connect all routes before tests',
            'replacement_count': len(phase['replacements']),
            'addition_count': len(phase['additions']),
            'source_paths': [target.relative_to(SERVER).as_posix() for target, _, _ in changes],
            'registry_qualified_inactive': True,
            'source_connected': True, 'compiled_this_phase': False,
            'tests_or_acceptance_run_this_phase': False,
            'formal_server_deployed': False, 'database_mutated': False,
            'configuration_activated': False,
        }
        (OUT / 'connection.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result))
    finally:
        archive.close()

if __name__ == '__main__':
    main()
