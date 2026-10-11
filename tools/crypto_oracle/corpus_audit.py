"""Audit recorded raw differential evidence, never promote live recovery."""
import argparse
import hashlib
import json
from pathlib import Path
from qualification import evaluate_qualification


def reference(kind, record):
    raw = json.dumps(record, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return {'type': kind, 'raw_hex': raw.hex(), 'sha256': hashlib.sha256(raw).hexdigest()}


def audit(directory):
    directory = Path(directory)
    report = json.loads((directory / 'differential-report.json').read_text())
    results, rules = [], {'feedback_unchanged_contradictions': 0, 'feedback_last_input_contradictions': 0,
                         'feedback_last_output_contradictions': 0, 'transform_calls': 0,
                         'key_changed_between_transform_calls': 0}
    for session_dir in sorted((directory / 'crypto-oracle-corpus').iterdir()):
        metadata = json.loads((session_dir / 'session.json').read_text())
        state = (session_dir / 'state.bin').read_bytes()
        if hashlib.sha256(state).hexdigest() != metadata['state_sha256']:
            raise ValueError('Corpus state hash mismatch')
        inputs = []
        sequence = 0
        for vector_path in sorted(session_dir.glob('vector-*.json')):
            vector = json.loads(vector_path.read_text())
            # Guardian requires nonempty distinct evidence; empty bodies remain unit controls.
            if not vector['input_hex']:
                continue
            sequence += 1
            for direction, raw, expected, actual, after, clean_after in (
                ('C2S', vector['input_hex'], vector['expected_wire_hex'], vector['clean_wire_hex'],
                 vector['state_after_tx_hex'], vector['clean_state_after_tx_hex']),
                ('S2C', vector['expected_wire_hex'], vector['oracle_plain_hex'], vector['clean_plain_hex'],
                 vector['state_after_rx_hex'], vector['clean_state_after_rx_hex'])):
                inputs.append(reference('oracle_diff_vector_v1', {
                    'run_id': directory.name, 'session_id': session_dir.name,
                    'vector_id': vector_path.stem + '-' + direction, 'sequence': sequence,
                    'direction': direction, 'input_hex': raw, 'state_before_hex': state.hex(),
                    'oracle_output_hex': expected, 'clean_output_hex': actual,
                    'oracle_state_after_hex': after, 'clean_state_after_hex': clean_after}))
                output, following = bytes.fromhex(expected), bytes.fromhex(after)
                body = bytes.fromhex(raw)
                rules['transform_calls'] += 1
                rules['feedback_unchanged_contradictions'] += following[0x2556] != state[0x2556]
                rules['feedback_last_input_contradictions'] += following[0x2556] != body[-1]
                rules['feedback_last_output_contradictions'] += following[0x2556] != output[-1]
                rules['key_changed_between_transform_calls'] += following[0x2420:0x2520] != state[0x2420:0x2520]
        evidence = {k: report[k] for k in ('capsule_corpus_pass', 'output_mismatches', 'state_mismatches', 'brute_force_count')}
        evidence.update(run_id=directory.name, session_id=session_dir.name, offline_vectors=inputs, live_sessions=[])
        results.append({'session': session_dir.name, **evaluate_qualification(evidence)})
    result = {'status': 'ORACLE_EQUIVALENT_OFFLINE' if all(not r['offline_errors'] for r in results)
              else 'ORACLE_EVIDENCE_REJECTED', 'CRYPTO_RECOVERED': False, 'sessions': results,
              'state_rules': rules, 'offset_rule': 'PER_CALL_RESET: hash-bound instruction motif, not a persisted offset field',
              'protocol_reset_boundaries': 'NOT_OBSERVED: pure initializer and transform calls only'}
    with (directory / 'corpus-audit.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps({'status': result['status'], 'sessions': len(results), 'state_rules': rules,
                      'CRYPTO_RECOVERED': False}))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    audit(parser.parse_args().directory)
