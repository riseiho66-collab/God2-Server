"""Original x86 capsule versus clean C++; controlled crypto-unit vectors only."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import random
import time

ROOT = Path(__file__).resolve().parents[2]
STATE_SIZE = 0x255c


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def first_difference(expected, actual):
    for index in range(max(len(expected), len(actual))):
        left = expected[index] if index < len(expected) else None
        right = actual[index] if index < len(actual) else None
        if left != right:
            return {'offset': index, 'oracle': left, 'clean': right}
    return None


class Clean:
    def __init__(self, library):
        self.library = ctypes.CDLL(str(Path(library).resolve()))
        pointer = ctypes.POINTER(ctypes.c_ubyte)
        self.init = self.library.God2CleanInit
        self.init.argtypes = [pointer, ctypes.c_uint, pointer, ctypes.c_uint, pointer, ctypes.c_uint]
        self.init.restype = ctypes.c_int
        self.transform = self.library.God2CleanTransform
        self.transform.argtypes = [ctypes.c_int, pointer, ctypes.c_uint, pointer, ctypes.c_uint,
                                   pointer, ctypes.c_uint, pointer, ctypes.c_uint]
        self.transform.restype = ctypes.c_int

    @staticmethod
    def buffer(data):
        return (ctypes.c_ubyte * max(1, len(data)))(*data)

    def init_session(self, seed, table):
        output = (ctypes.c_ubyte * STATE_SIZE)()
        size = self.init(self.buffer(seed), len(seed), self.buffer(table), len(table), output, STATE_SIZE)
        if size != STATE_SIZE:
            raise RuntimeError('Clean initializer rejected vector')
        return bytes(output)

    def apply(self, operation, state, data):
        output = (ctypes.c_ubyte * max(1, len(data)))()
        after = (ctypes.c_ubyte * STATE_SIZE)()
        size = self.transform(operation == 'decrypt', self.buffer(state), len(state),
                              self.buffer(data), len(data), output, len(data), after, STATE_SIZE)
        if size != len(data):
            raise RuntimeError('Clean transform rejected vector')
        return bytes(output[:size]), bytes(after)


def run(capsule_path, clean_path, output, seed_count=3, vectors_per_seed=16):
    from capsule import load_capsule
    from oracle import ClientCryptoOracle
    if not 3 <= seed_count <= 256 or not 1 <= vectors_per_seed <= 256:
        raise ValueError('Bounded seed/vector counts required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    corpus = output / 'crypto-oracle-corpus'
    corpus.mkdir()
    manifest = load_capsule(capsule_path)
    table_region = next(r for r in manifest['regions'] if r['kind'] == 'CONSTANT_TABLE')
    table = (Path(capsule_path).parent / table_region['file']).read_bytes()
    oracle = ClientCryptoOracle(capsule_path)
    clean = Clean(clean_path)
    rng = random.Random(0x60d2)
    lengths = (0, 1, 2, 15, 16, 17, 254, 255, 256, 257, 511, 512, 1024, 2048, 4096, 33)
    started = time.monotonic()
    report = {'status': 'RUNNING', 'CRYPTO_RECOVERED': False, 'brute_force_count': 0,
              'capsule_sha256': digest(Path(capsule_path).read_bytes()),
              'clean_dll_sha256': digest(Path(clean_path).read_bytes()),
              'output_mismatches': 0, 'state_mismatches': 0, 'vectors': 0,
              'sessions': [], 'live_sessions': [], 'input_kind': 'CONTROLLED_CRYPTO_UNIT_VECTORS',
              'original_client_launched': False}
    footprint = []

    def compare(operation, seed_index, vector_index, state, data, result, clean_output, clean_after):
        expected = bytes.fromhex(result['output_hex'])
        after = bytes.fromhex(result['state_after_hex'])
        out_diff, state_diff = first_difference(expected, clean_output), first_difference(after, clean_after)
        report['vectors'] += 1
        report['output_mismatches'] += out_diff is not None
        report['state_mismatches'] += state_diff is not None
        if out_diff is not None or state_diff is not None:
            details = {'operation': operation, 'session': seed_index, 'vector': vector_index,
                       'FIRST_OUTPUT_DIFF_OFFSET': out_diff, 'FIRST_STATE_DIFF_OFFSET': state_diff,
                       'state_before_hex': state.hex(), 'state_after_oracle_hex': after.hex(),
                       'state_after_clean_hex': clean_after.hex(), 'input_hex': data.hex()}
            # Successful vectors never enable instruction trace.
            traced = getattr(oracle, operation)(state, data, trace=True)
            details['oracle_instruction_trace'] = traced.get('instruction_trace', traced.get('trace', []))
            from semantic_lift import trace_ir
            details['semantic_trace_ir'] = trace_ir(details['oracle_instruction_trace'])
            write_json(output / f'mismatch-{seed_index:03}-{vector_index:03}-{operation}.json', details)
        return out_diff is None and state_diff is None

    for seed_index in range(seed_count):
        seed = bytes(16) if seed_index == 0 else rng.randbytes(16)
        session_name = f'session-{chr(65 + seed_index)}' if seed_index < 26 else f'session-{seed_index:03}'
        directory = corpus / session_name
        directory.mkdir()
        initialized = oracle.init_session(seed)
        before = bytes.fromhex(initialized['state_after_hex'])
        clean_before = clean.init_session(seed, table)
        init_diff = first_difference(before, clean_before)
        report['state_mismatches'] += init_diff is not None
        (directory / 'state.bin').write_bytes(before)
        session = {'session_id': session_name, 'seed_hex': seed.hex(),
                   'key_sha256': digest(before[0x2420:0x2520]), 'init_state_match': init_diff is None,
                   'state_before': 'state.bin', 'state_sha256': digest(before),
                   'origin': 'OFFLINE_ORIGINAL_X86_EXECUTION', 'live': False}
        write_json(directory / 'session.json', session)
        report['sessions'].append({k: v for k, v in session.items() if k != 'seed_hex'})
        if seed_index == 0:
            write_json(directory / 'init-entry-snapshot.json', initialized.get('snapshot', {}))
            footprint.append({'operation': 'init_session', 'memory_reads': initialized.get('memory_reads', []),
                              'memory_writes': initialized.get('memory_writes', []),
                              'code_fetches': initialized.get('code_fetches', [])})
        if init_diff is not None:
            traced = oracle.init_session(seed, trace=True)
            from semantic_lift import trace_ir
            write_json(output / f'mismatch-{seed_index:03}-init.json',
                       {'FIRST_STATE_DIFF_OFFSET': init_diff, 'oracle': before.hex(),
                        'clean': clean_before.hex(), 'semantic_trace_ir': trace_ir(traced.get('instruction_trace', [])),
                        'trace': traced.get('instruction_trace', traced.get('trace', []))})
            continue
        for vector_index in range(vectors_per_seed):
            length = lengths[vector_index % len(lengths)]
            plain = bytes(length) if vector_index % 3 == 0 else rng.randbytes(length)
            # The captured six-byte frame contributes this four-byte cipher span.
            if seed_index == 0 and vector_index == 0:
                plain = bytes.fromhex('a60000d8')
            tx = oracle.encrypt(before, plain)
            wire = bytes.fromhex(tx['output_hex'])
            clean_wire, clean_after = clean.apply('encrypt', clean_before, plain)
            match_tx = compare('encrypt', seed_index, vector_index, before, plain, tx, clean_wire, clean_after)
            rx = oracle.decrypt(before, wire)
            clean_plain, clean_after_rx = clean.apply('decrypt', clean_before, wire)
            match_rx = compare('decrypt', seed_index, vector_index, before, wire, rx, clean_plain, clean_after_rx)
            roundtrip = bytes.fromhex(rx['output_hex']) == plain
            if not roundtrip:
                report['output_mismatches'] += 1
            if seed_index == 0 and vector_index == 0 and wire != bytes.fromhex('a3a3fdd5'):
                raise RuntimeError('Permanent original-client six-byte oracle changed')
            write_json(directory / f'vector-{vector_index:04}.json',
                       {'state_before': 'state.bin', 'input_hex': plain.hex(), 'expected_wire_hex': wire.hex(),
                        'clean_wire_hex': clean_wire.hex(), 'oracle_plain_hex': rx['output_hex'],
                        'clean_plain_hex': clean_plain.hex(),
                        'state_after_tx_hex': tx['state_after_hex'], 'state_after_rx_hex': rx['state_after_hex'],
                        'clean_state_after_tx_hex': clean_after.hex(), 'clean_state_after_rx_hex': clean_after_rx.hex(),
                        'OUTPUT_MATCH': match_tx and match_rx, 'STATE_MATCH': clean_after == bytes.fromhex(tx['state_after_hex'])
                        and clean_after_rx == bytes.fromhex(rx['state_after_hex']), 'roundtrip': roundtrip,
                        'credential_data': False, 'origin': 'CONTROLLED_CRYPTO_UNIT_VECTOR'})
            if seed_index == 0 and vector_index == 0:
                for name, result in (('encrypt', tx), ('decrypt', rx)):
                    write_json(directory / f'{name}-entry-snapshot.json', result.get('snapshot', {}))
                    footprint.append({'operation': name, 'memory_reads': result.get('memory_reads', []),
                                      'memory_writes': result.get('memory_writes', []),
                                      'code_fetches': result.get('code_fetches', [])})
        print(json.dumps({'session': session_name, 'vectors': report['vectors'],
                          'output_mismatches': report['output_mismatches'],
                          'state_mismatches': report['state_mismatches']}), flush=True)
    report['elapsed_seconds'] = round(time.monotonic() - started, 3)
    passed = report['output_mismatches'] == 0 and report['state_mismatches'] == 0
    report['capsule_corpus_pass'] = passed
    report['status'] = 'ORACLE_EQUIVALENT_OFFLINE' if passed else 'DIFFERENTIAL_MISMATCH'
    report['promotion'] = 'TWO_FRESH_LIVE_SESSIONS_REQUIRED'
    write_json(output / 'crypto-memory-footprint.json', footprint)
    write_json(output / 'differential-report.json', report)
    return 0 if passed else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capsule', type=Path, required=True)
    parser.add_argument('--clean-dll', type=Path, default=ROOT / 'build-crypto-oracle/Release/God2CryptoClean.dll')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seeds', type=int, default=3)
    parser.add_argument('--vectors-per-seed', type=int, default=16)
    args = parser.parse_args()
    return run(args.capsule, args.clean_dll, args.output, args.seeds, args.vectors_per_seed)


if __name__ == '__main__':
    raise SystemExit(main())
