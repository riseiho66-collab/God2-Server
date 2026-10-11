"""Record this bounded, isolated delivery; never deploy or mutate a player save."""
import hashlib
import json
from pathlib import Path
import shutil
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/releases/packet-travel-peer-20260930-candidate'
EXPECTED = 'b94ea3dda7bd8c5de8023f2dbaa8be7391d1f72f0b3feac66d2cabca84effc2c'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf-8')


def main():
    binary = ROOT / 'build-town-visibility/Release/god2-server-native-results.exe'
    if sha(binary) != EXPECTED:
        raise RuntimeError('Tested candidate changed')
    old_receipt = json.loads((ROOT / 'artifacts/research/teleport-gem-tcp-20260930/result.json').read_text('utf-8'))
    source = (ROOT / 'src/core/Application.cpp').read_text('utf-8')
    previous, changes = re.subn(r'^ +if\(config\.owned_teleport_gem_enabled && slot\.item_id==RecoveredTeleportGem::item_id\)continue;\n', '', source, flags=re.MULTILINE)
    previous_sha = hashlib.sha256(previous.encode('utf-8')).hexdigest()
    if changes != 2 or previous_sha != old_receipt['source_sha256']['src/core/Application.cpp']:
        raise RuntimeError('Final candidate delta is not the qualified two gem-only guards')
    registry_path = ROOT / 'docs/custom-designs.json'
    registry = json.loads(registry_path.read_text('utf-8'))
    entries = next(value for value in registry.values() if isinstance(value, list))
    role = next(entry for entry in entries if entry.get('id') == 'CUSTOM-0056')
    role['peer_extension_20260930'] = {
        'activation': 'CANDIDATE_ONLY; production remains packet-links-20260930-01 pending explicit qualified release',
        'native_contract': 'Current 9be client 6F logical[45,61) is peer secondary text. Source language flag is shared by primary/secondary/third text. Per-receiver prediction matches native52F170/F330 and rejects lossy or oversized output.',
        'rules': 'Prepare peer language projections inside owned save transaction; after commit send prepared6F. Seed presence cache from owned saved secondary field, including empty clear. All other spawn bytes and primary name preserved. Native6F replaces an actor and resets its interpolation queue; latest authoritative coordinates are retained and later native movement is qualified.',
        'scope': 'Owned secondary text only; no common chat, IME, authentication, streamer styling or client binary changes',
        'evidence': ['docs/research/current-peer-role-text-20260930.md', 'artifacts/reports/peer-role-text-20260930/native.json', 'artifacts/reports/peer-role-text-20260930/codec-native.json'],
    }
    gem = {
        'id': 'CUSTOM-0057', 'name': 'Owned teleport gem instance and bounded town return',
        'authority': 'CUSTOM_DESIGNED',
        'implementation': ['src/protocol/RecoveredTeleportGem.h', 'src/handlers/OwnedTeleportGemOffer.h', 'src/db/SqliteTeleportGemRepository.cpp', 'src/db/Migration.cpp', 'src/handlers/RecoveredMovementService.cpp', 'src/core/Application.cpp', 'src/core/Config.cpp'],
        'native_gap': 'Original acquisition, menu association/context, fees, cooldown, per-city landing authority and four additional destinations remain unrecovered. Item source and executable contract do not establish these server rules.',
        'rules': 'Native item16055/type8 full20 instance; bits25..31 represent1..10 charges, separate from count1. No grants or inference from a scalar item. Owned25/26 opens a60-second context16055 offer, one destination5, no additional currency cost. Only source area2/scene0 to already-qualified CityI1 area2/scene4/56/75. Authorize owner, readiness, battle, exact saved item/position revisions;99 commits one charge and destination atomically before3B/41+61. Cancellation and rejected requests do not debit. One remaining charge clears scalar occupancy and deletes the overlay. Source coordinates originate from the established native map entry, but using them for this gem is explicitly custom. Physical slot24 moves preserve full metadata/provenance.',
        'reason': 'Complete the verified native item/menu/selection/transfer chain without fabricating missing official destinations or creating items. Historical Bahamut special-items description supports selectable single-user teleport and ten uses followed by disappearance; it does not establish fee or packet authority.',
        'activation': 'CANDIDATE_ONLY; world.owned_teleport_gem.enabled defaults false. Schema40 and runtime accepted on isolated own-server current-client tests; formal server/save/config unchanged this round.',
        'field_origins': {'item_id/type/charge_bits/native_packet_layout': 'NATIVE_VERIFIED', 'existing_destination_map_entry': 'NATIVE_VERIFIED map geometry; CUSTOM-0036 arrival selection', 'offer_context/TTL/fee/supported_route/consumption/atomic_storage': 'CUSTOM_DESIGNED', 'test_initial_instance': 'CUSTOM_TEST_NOT_NATIVE'},
        'tests': ['tests/test_recovered_teleport_gem.cpp', 'tests/test_owned_teleport_gem_offer.cpp', 'tests/test_teleport_gem_repository.cpp', 'tests/companion/test_packet_commit_review.cpp', 'tests/research/test_owned_teleport_gem_server.py', 'artifacts/research/teleport-gem-tcp-20260930/final/result.json', 'artifacts/playtests/private-teleport-gem-20260930-03/run-result.json'],
        'replacement': 'Replace custom association/fee/route rules only with build-qualified original authority and preserving migrations; acquire and authorize other destinations separately.',
    }
    if any(entry.get('id') == gem['id'] for entry in entries):
        entries[next(i for i, entry in enumerate(entries) if entry.get('id') == gem['id'])] = gem
    else:
        entries.append(gem)
    write(registry_path, registry)
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'god2-server.candidate.exe'
    if target.exists() and sha(target) != EXPECTED:
        raise RuntimeError('Candidate archive collision')
    shutil.copy2(binary, target)
    names = [
        'src/core/Application.cpp', 'src/core/Config.cpp', 'src/core/Config.h',
        'src/db/Migration.cpp', 'src/db/SqliteDatabase.cpp', 'src/db/SqliteDatabase.h',
        'src/db/SqliteRoleTextRepository.cpp', 'src/db/SqliteRoleTextRepository.h',
        'src/db/SqliteTeleportGemRepository.cpp', 'src/db/SqliteTeleportGemRepository.h',
        'src/handlers/RecoveredMovementService.cpp', 'src/handlers/RecoveredMovementService.h',
        'src/handlers/RecoveredVisibility.h', 'src/handlers/RecoveredPeerRoleText.h',
        'src/handlers/OwnedTeleportGemOffer.h', 'src/protocol/RecoveredRemoteRoleText.h',
        'src/protocol/RecoveredTeleportGem.h', 'src/text/NativePeerRoleTextCodec.cpp',
        'src/text/NativePeerRoleTextCodec.h', 'tests/CMakeLists.txt',
        'tests/test_peer_role_text.cpp', 'tests/test_recovered_teleport_gem.cpp',
        'tests/test_owned_teleport_gem_offer.cpp', 'tests/test_teleport_gem_repository.cpp',
        'tests/companion/test_packet_commit_review.cpp', 'tests/research/test_owned_teleport_gem_server.py',
        'docs/custom-designs.json',
    ]
    for name in names:
        destination = OUT / 'source' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
    write(OUT / 'manifest.json', {
        'candidate_sha256': EXPECTED, 'production_applied': False,
        'formal_database_replaced': False, 'client_modified': False,
        'pause_requested_by_owner': True, 'source_sha256': {name: sha(ROOT / name) for name in names},
        'final_app_delta': {'changed_lines': changes, 'previous_sha256': previous_sha,
                            'scope': 'Two scalar-restoration gem skips behind owned_teleport_gem_enabled; false in peer fixtures'},
        'limits': ['Source snapshot contains changed files, not a standalone full-source distribution', 'Current-client automation verifies native UI controls/state and protocol; pixel appearance was not screenshot-tested', 'Only a bounded single gem destination is supported'],
    })
    print(json.dumps({'recorded': True, 'candidate': str(OUT), 'production_applied': False}))


if __name__ == '__main__':
    main()
