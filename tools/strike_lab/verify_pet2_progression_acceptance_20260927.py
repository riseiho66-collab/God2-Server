"""Verify saved own-server live cache receipts; no native growth claim."""
import hashlib
import json
from pathlib import Path
from .recovered_packet_pipeline import pet2_fields
from .current_pet2_stat_labels import audit

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'artifacts/playtests/private-pet-progression-20260927-01'
EVIDENCE = ROOT / 'artifacts/research/bahamut-growth-20260927'


def require(value, message):
    if not value:
        raise ValueError(message)


def verify():
    raw = (RUN / 'run-result.json').read_bytes()
    run = json.loads(raw)
    ui = json.loads((RUN / 'ui-result.json').read_text('utf-8'))
    require(run['accepted'] and ui['accepted'], 'Live acceptance failed')
    for flag in ('source_db_unchanged', 'live_client_unchanged', 'private_client_unchanged'):
        require(run[flag], flag)
    candidate = EVIDENCE / 'pet2-progression.accepted-server.exe'
    require(hashlib.sha256(candidate.read_bytes()).hexdigest() == run['server_sha256'],
            'Archived accepted executable differs')
    require(ui['desktop_before'] == ui['desktop_after'] == ui['desktop_final'],
            'User desktop changed')
    require(len(ui['stages']) == 3, 'Missing select/swap/return stages')
    checked = []
    for stage in ui['stages']:
        pets = []
        for slot, _, encoded, _ in stage['db']['pets']:
            native = bytes.fromhex(stage['native']['pet_cache'][str(slot)])
            if not encoded:
                require(native == bytes(72), 'Empty slot retained native stats')
                continue
            packet = bytes.fromhex(encoded)
            require(native == packet[1:], 'Native client cache differs from committed DB')
            fields = pet2_fields(packet)
            require(fields is not None and fields['slot'] == slot, 'Invalid owned routing')
            expected = {28001: (37, 10, 5), 28002: (98, 5, 10)}[fields['metadata_key']]
            require((fields['level'], fields['star_rank'], fields['star_rating']) == expected,
                    'Level/star identity changed during transfer')
            require(fields['vitals'] == dict(current_hp=50, maximum_hp=100,
                                            current_mp=20, maximum_mp=40),
                    'Packed vitals changed')
            require(fields['progress_display_raw24'] == 0, 'Stars contaminated EXP display')
            pets.append({k: fields[k] for k in ('metadata_key', 'slot', 'level', 'vitals',
                                               'star_rank', 'star_rating')})
        require(len(pets) == 2, 'Transfer lost an owned pet')
        checked.append({'move': stage['move'], 'pets': pets})
    bindings = audit()
    require(len(bindings['packed_fields']) == 7, 'Missing native panel bindings')
    return dict(accepted=True, candidate_sha256=run['server_sha256'],
                run_receipt_sha256=hashlib.sha256(raw).hexdigest(),
                client_sha256=run['live_client_sha256'], native_field_bindings=7,
                live_transfer_stages=checked, origin='SYNTHETIC_OWNED_TEST_VALUES',
                receiver_and_display_contract='NATIVE_VERIFIED',
                native_growth_formula_verified=False, production_enabled=False)


if __name__ == '__main__':
    result = verify()
    (EVIDENCE / 'pet2-progression-acceptance.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Pet2 level/vitals/stars: native bindings and three live owned transfers PASS')
