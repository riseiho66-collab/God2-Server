"""Owner-authorized isolated enemy-view experiment; never official monster data.

Runs pinned original x86 instruction islands in disposable VMs. These are two
synthetic actor controls, not game accounts, a live PK, or full client playback.
Only files below the dedicated research directory are written. No sockets,
process attachment, binary patching, databases, builds, or live service changes.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import struct

from tools.reconstruction.archive_inputs import ArchivedInputs

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'artifacts/research/enemy-blackbox-20261006/consumer-experiment'
ORIGIN = 'CUSTOM_TEST_NOT_NATIVE'
IMAGE_REL = 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
CATALOG_REL = 'artifacts/capture_work/host-20260918-1430/client/Data2/Fight/Spg/cbspec2.bin'
IMAGE_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
CATALOG_SHA = '7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51'


def retained_inputs():
    reader = ArchivedInputs()
    try:
        blobs = [(IMAGE_REL, IMAGE_SHA, OUT / 'inputs/native-image.bin'),
                 (CATALOG_REL, CATALOG_SHA, OUT / 'inputs/client/Data2/Fight/Spg/cbspec2.bin')]
        facts = []
        for relative, pin, path in blobs:
            raw = reader.read(relative)
            if sha256(raw).hexdigest() != pin:
                raise ValueError('Retained input identity differs')
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.read_bytes() != raw:
                raise ValueError('Dedicated retained input already differs')
            if not path.exists():
                path.write_bytes(raw)
            facts.append({'original_reference': relative, 'experiment_copy': str(path),
                          'bytes': len(raw), 'sha256': pin})
        return facts
    finally:
        reader.close()


def scalar_packet(kind, maximum, current):
    return bytes((0x86, kind, 14)) + bytes(2) + struct.pack('<II', maximum, current) + bytes(4)


def snapshot_hp_modules(control, scalar):
    actor = bytearray(b'\xa5' * scalar.ACTOR_SIZE)
    struct.pack_into('<H', actor, 0x1a, 1)
    struct.pack_into('<h', actor, 0x1d8, -1)  # Explicit absent display.
    struct.pack_into('<4I', actor, 0xde8, 0, 0, 1, 1)
    outputs = []
    for kind, current, maximum in ((0, control['hp'], control['max_hp']),
                                  (1, control['mp'], control['max_mp'])):
        packet = scalar_packet(kind, maximum, current)
        before = bytes(actor)
        run = scalar.consume(packet, entities={14: before}, displays={}, owner_value=0)
        actor[:] = run.vm.mem_read(scalar.actor_address(14), scalar.ACTOR_SIZE)
        outputs.append({'packet_hex': packet.hex(), 'kind': kind,
                        'stop_rva': hex(run.stop), 'instruction_count': len(run.visits),
                        'actor_before_sha256': sha256(before).hexdigest(),
                        'actor_after_sha256': sha256(actor).hexdigest(),
                        'actor_changes': [{'offset': hex(i), 'before': a, 'after': b}
                                          for i, (a, b) in enumerate(zip(before, actor)) if a != b],
                        'native_writes': [{'rva': hex(pc), 'address': hex(address),
                                           'width': size, 'value': value}
                                          for pc, address, size, value in run.writes
                                          if scalar.actor_address(14) <= address < scalar.actor_address(14) + scalar.ACTOR_SIZE]})
    return {'actor_hp_mp_raw': list(struct.unpack_from('<4I', actor, 0xde8)),
            'actor_sha256': sha256(actor).hexdigest(), 'stages': outputs}


def observed_skill(control, skill, client):
    probe = skill.NativeSkillActions(client)
    # Both controls exist in each private VM; ordinary actors and enemy actors
    # are synthetic snapshots. Full skill ownership is kept on the control side.
    probe.install_actors({0: skill.diagnostic_actor(poison=0xa5),
                          14: skill.diagnostic_actor(poison=0x5a)})
    bank, entry = control['cast']
    record = skill.diagnostic_record(bank, entry, 14)
    before = probe.actor(14)
    producer = probe.produce(record, gate=record[3], phase_started=True)
    consumer = probe.consume(record, target_side=0, target_slot=0)
    after = probe.actor(14)
    cache = struct.unpack_from('<51I', after, skill.CACHE)
    inverse = {probe.pointer(*identity): identity for identity in probe.definitions}
    return {'packet_hex': record.hex(), 'producer_stop_rva': hex(producer['stop_rva']),
            'consumer_stop_rva': hex(consumer['stop_rva']),
            'observed_cache_pairs': [list(inverse[p]) for p in cache if p],
            'current_skill_pair': list(inverse[struct.unpack_from('<I', after, skill.CURRENT)[0]]),
            'actor_sha256': sha256(after).hexdigest(),
            'actor_changes': [{'offset': hex(i), 'before': a, 'after': b}
                              for i, (a, b) in enumerate(zip(before, after)) if a != b],
            'producer_writes': producer['writes'], 'consumer_writes': consumer['writes'],
            'boundaries': ['Original producer stops BEFORE resource lookup 116DF1.',
                           'Consumer is an independent original call in the same VM; intervening playback is not claimed.',
                           'Catalog payload is a pinned explicit memory input; native resource loading is not claimed.']}


def main():
    facts = retained_inputs()
    from tools.strike_lab import current_battle_entry as entry
    entry.IMAGE = OUT / 'inputs/native-image.bin'  # Process-local path selection; code is unchanged.
    from tools.strike_lab import current_battle_side1_scalars as scalar
    from tools.strike_lab import current_monster_skill_assignments as skill
    client = OUT / 'inputs/client'
    controls = {
        'A': {'constitution': 53, 'strength': 59, 'intelligence': 61, 'speed': 67,
              'physical_attack': 101, 'physical_defense': 103,
              'magical_attack': 107, 'magical_defense': 109,
              'metal': 11, 'wood': 13, 'water': 17, 'fire': 19, 'earth': 23,
              'hp': 419, 'max_hp': 503, 'mp': 127, 'max_mp': 211,
              'carried_skills': [[0, 1], [0, 2], [1, 1]], 'cast': [0, 1]},
        'B': {'constitution': 71, 'strength': 73, 'intelligence': 79, 'speed': 83,
              'physical_attack': 211, 'physical_defense': 223,
              'magical_attack': 227, 'magical_defense': 229,
              'metal': 31, 'wood': 37, 'water': 41, 'fire': 43, 'earth': 47,
              'hp': 631, 'max_hp': 701, 'mp': 293, 'max_mp': 307,
              'carried_skills': [[1, 2], [2, 1], [3, 1]], 'cast': [1, 2]},
    }
    result = {'origin': ORIGIN, 'scope': 'ISOLATED_ORIGINAL_X86_CONSUMER_IDENTIFIABILITY',
              'actual_accounts_created': False, 'actual_native_pk': False,
              'live_network': False, 'official_service_used': False,
              'production_changes': False, 'pinned_inputs': facts,
              'controls': controls, 'cases': [], 'tool_sha256': sha256(Path(__file__).read_bytes()).hexdigest()}
    hidden = ['constitution', 'strength', 'intelligence', 'speed',
              'physical_attack', 'physical_defense', 'magical_attack', 'magical_defense',
              'metal', 'wood', 'water', 'fire', 'earth', 'carried_skills']
    for who, opponent in (('A', 'B'), ('B', 'A')):
        base = controls[opponent]
        base_vitals = snapshot_hp_modules(base, scalar)
        base_skill = observed_skill(base, skill, client)
        cases = []
        for field in hidden:
            changed = deepcopy(base)
            changed[field] = changed[field] + 1000 if field != 'carried_skills' else [changed['cast'], [3, 2], [3, 3], [3, 4]]
            vitals = snapshot_hp_modules(changed, scalar)
            action = observed_skill(changed, skill, client)
            cases.append({'changed_control_field': field, 'changed_control_value': changed[field],
                          'vitals_packet_identical': [s['packet_hex'] for s in vitals['stages']] == [s['packet_hex'] for s in base_vitals['stages']],
                          'vitals_actor_identical': vitals['actor_sha256'] == base_vitals['actor_sha256'],
                          'action_packet_identical': action['packet_hex'] == base_skill['packet_hex'],
                          'action_actor_identical': action['actor_sha256'] == base_skill['actor_sha256']})
        changed_hp = deepcopy(base); changed_hp['hp'] += 1
        hp = snapshot_hp_modules(changed_hp, scalar)
        changed_cast = deepcopy(base); changed_cast['cast'] = [3, 2]
        cast = observed_skill(changed_cast, skill, client)
        result['cases'].append({'observer_control': who, 'opponent_control': opponent,
                                'baseline_vitals': base_vitals, 'baseline_action': base_skill,
                                'hidden_control_changes': cases,
                                'positive_control_hp_plus_one': hp,
                                'positive_control_cast_changed': cast})
    result['conclusions'] = [
        'Enemy side1 kind0 writes actual received HP/maximum HP into actor DE8/DF0 in these supplied native states.',
        'Enemy side1 kind1 returns without writing MP; supplied MP packet presence is distinct from actor update.',
        'Action3 records populate enemy DF8 cache/current EC4 with observed skill identities only.',
        'These fourteen hidden-control mutations leave the selected packets and native actor outputs identical because this experiment projection omits them.',
        'This bounded non-identifiability result does NOT prove every official packet, initial actor state, or resource omits those fields.',
        'An unobserved carried skill cannot be concluded absent from the repertoire; sampling casts gives a lower bound only.'
    ]
    result['live_experiment_gap'] = {
        'retained_server': 'build-town-visibility/Release/god2-server.exe',
        'retained_server_sha256': '1062075f3d2063650a28adc4c9053ac5a68c646dbbb4ea0229af28bfdb8251c9',
        'old_private_client_bootstrap': 'tools/strike_lab/private_current_client_variant.py modifies startup port bytes in a client copy; parent subsequently authorized only a minimal disposable-copy startup-port patch for this experiment.',
        'missing': ['A newly prepared current native-client bootstrap to an isolated port with separate account DB and owned hidden desktop. Historical account DB / PID / receipts cannot be reused as current authority.',
                    'An accepted native player-PK route, or controlled monster encounter route, capable of injecting these field-level values into an enemy-view capture.'],
        'not_substituted': 'The custom fixture combat protocol is incompatible with the native client and cannot prove native exposure.'}
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / 'identifiability-result.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(path), 'actual_native_pk': False,
                      'observer_cases': len(result['cases']),
                      'hidden_mutations': sum(len(c['hidden_control_changes']) for c in result['cases']),
                      'input_bytes': sum(f['bytes'] for f in facts)}, ensure_ascii=True))


if __name__ == '__main__':
    main()
