"""Historical same-session replay only. Never a fresh runtime qualification."""
import argparse
import hashlib
import json
from pathlib import Path
from c2s0002 import key
from crypto_recovery import ROOT, recover_native, candidate_report


def frame(payload):
    body = (len(payload) + 3).to_bytes(2, 'little') + payload
    return body + bytes([sum(value + 0x3c for value in body) & 255])


def historical_request():
    source = ROOT / 'artifacts/runs/ui-gate-real-04/network'
    logical = (source / 'C2S_0002.logical.bin').read_bytes()
    if len(logical) != 173 or logical[0] != 4:
        raise ValueError('Historical pre-transform oracle mismatch')
    captures = (
        ('S2C', 'S2C_0002.bin', frame(bytes([1, 0x53]))),
        ('C2S', 'C2S_0002.bin', frame(logical)),
        ('S2C', 'S2C_0003.bin', frame(bytes([29]) + logical[1:])),
        ('S2C', 'S2C_SERVER_LIST_0001.bin', frame(bytes([4, 0, 0, 1, 0]))),
        ('S2C', 'S2C_0004.bin', frame(bytes([10]) + bytes(16))),
        ('C2S', 'C2S_0003.bin', bytes.fromhex('0600a60000d8')),
    )
    packets, provenance = [], []
    for direction, name, plain in captures:
        wire = (source / name).read_bytes()
        if len(wire) != len(plain):
            raise ValueError('Historical frame size changed')
        packets.append({'direction': direction, 'wire_hex': wire.hex(),
            'known_plaintext_hex': plain.hex(), 'allowed_opcodes': [plain[2]],
            'state_before': 'CODEC_ENABLED', 'state_after': 'CODEC_ENABLED',
            'expected_state_before': 'CODEC_ENABLED'})
        provenance.append({'source': str((source / name).relative_to(ROOT)),
                           'wire_sha256': hashlib.sha256(wire).hexdigest(), 'direction': direction})
    captured_key = key(ROOT).hex()
    return {'session_id': 'ui-gate-real-04', 'model': 'packet_reset',
            'tx_key_hex': captured_key, 'rx_key_hex': captured_key, 'packets': packets}, provenance


def run(output):
    request, provenance = historical_request()
    result = recover_native(request, ROOT / 'build-strike-lab/Release/God2Probe.dll')
    report = candidate_report(result, len(request['packets']))
    report['evidence_kind'] = 'HISTORICAL_SAME_SESSION_REPLAY'
    report['source_packets'] = provenance
    report['state_constraint_scope'] = 'codec enabled only; not fresh opcode/state parser acceptance'
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'decrypt-candidates.json').open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    with (output / 'runtime-qualification.json').open('x', encoding='utf-8') as stream:
        json.dump({'status': 'RUNTIME_VALIDATION_REQUIRED', 'CRYPTO_RECOVERED': False,
                   'reason': 'Historical zero-seed replay; no fresh connection, key or parser trace.'}, stream, indent=2)
    print(json.dumps({'status': report['status'], 'CRYPTO_RECOVERED': False,
                      'survivors': {name: d['candidate_count'] for name, d in report['directions'].items()},
                      'rounds': {name: d['rounds'] for name, d in report['directions'].items()}}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
