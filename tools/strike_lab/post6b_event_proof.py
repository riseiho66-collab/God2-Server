"""Exact post-six-byte continuation proof; no call/caller or live-state closure."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
IMAGE = 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
TRACE = 'artifacts/runs/ui-gate-real-04/network-events.jsonl'
WIRE = 'artifacts/runs/ui-gate-real-04/C2S_SERVER_SELECT_0001.bin'
SOURCES = {
    IMAGE: '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763',
    TRACE: '179babb69b9fd726e7c790605aa72406b53165721a8d212b777310565e36e73d',
    WIRE: 'bd1d63babf8850007f21a4130adc00749e9171f769b7edfc38822115b7146fae',
}
PINNED_BYTES = {
    0x12506: '5e33c05fc20800',
    0x133b3: '8b8ed4400000c786c43600000000000085c97405e8c4e5ffff33c05ec3',
}


def source_gate(root=ROOT):
    """Reject changed/missing sources before any semantic or solver claims."""
    root = Path(root)
    blobs = {}
    for path, expected in SOURCES.items():
        data = (root / path).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Source SHA256 mismatch: ' + path)
        blobs[path] = data
    for rva, expected in PINNED_BYTES.items():
        code = bytes.fromhex(expected)
        if blobs[IMAGE][rva:rva + len(code)] != code:
            raise ValueError('Pinned instruction bytes mismatch: ' + hex(rva))
    events = [json.loads(line) for line in blobs[TRACE].splitlines() if line.strip()]
    pair = [[e for e in events if e.get('sequence') == seq] for seq in (146, 147)]
    if any(len(matches) != 1 for matches in pair):
        raise ValueError('Missing or ambiguous captured send pair')
    entry, returned = pair[0][0], pair[1][0]
    if not (entry.get('api') == returned.get('api') == 'send'
            and entry.get('event_type') == 'API_ENTRY'
            and returned.get('event_type') == 'API_RETURN'
            and returned.get('matched') is True and returned.get('entry') == 146
            and returned.get('pc') == entry.get('ret') == 0x412506
            and returned.get('eax') == entry.get('a2') == 6
            and returned.get('sp') == entry.get('sp', -20) + 20
            and returned.get('a1') == 0x4133b3
            and returned.get('pid') == entry.get('pid')
            and returned.get('tid') == entry.get('tid')
            and returned.get('run_id') == entry.get('run_id') == 'ui-gate-real-04'):
        raise ValueError('Captured continuation mismatch')
    return {
        'status': 'PASS',
        'sources': [{'path': p, 'sha256': h} for p, h in SOURCES.items()],
        'pinned_bytes': {hex(r): b for r, b in PINNED_BYTES.items()},
        'sequence': 147, 'object_root': returned['ret'],
        'qualification': 'RESTORED_STATIC_BYTES_NOT_LIVE_CODE_CAPTURE',
    }


def _load_z3(root):
    local = str(Path(root) / 'artifacts/tooling/event-proof-python')
    if local not in sys.path:
        sys.path.insert(0, local)
    try:
        return importlib.import_module('z3'), None
    except (ImportError, OSError) as exc:
        return None, str(exc)


def _solver_checks(z3, timeout_ms):
    # SSA values come directly from the pinned mov/read, mov/store and test.
    h0, prior, ecx, after = z3.BitVecs('H0 queued_prior ECX_after_read Q_after_store', 32)
    zero = z3.BitVecVal(0, 32)
    post = after != prior
    wp = z3.substitute(post, (after, zero))
    transition = [('read_H0_at_0x4133b3', ecx == h0),
                  ('store_zero_at_0x4133b9', after == zero)]
    queries = [
        ('conditional_change_witness', transition + [('change', post)], 'sat'),
        ('conditional_iff_counterexample', transition + [
            ('negated_iff', z3.Xor(post, prior != zero))], 'unsat'),
        ('nonzero_prior_without_change', transition + [
            ('prior_nonzero', prior != zero), ('no_change', z3.Not(post))], 'unsat'),
        ('zero_prior_with_change', transition + [
            ('prior_zero', prior == zero), ('change', post)], 'unsat'),
        ('zero_prior_unmodeled_call', transition + [
            ('prior_zero', prior == zero), ('test_nonzero', ecx != zero)], 'sat'),
        ('zero_prior_unmodeled_caller', transition + [
            ('prior_zero', prior == zero), ('test_zero', ecx == zero)], 'sat'),
        ('store_dominates_nonzero_branch', transition + [
            ('test_nonzero', ecx != zero), ('store_not_zero', after != zero)], 'unsat'),
        ('store_dominates_zero_branch', transition + [
            ('test_zero', ecx == zero), ('store_not_zero', after != zero)], 'unsat'),
    ]
    checks = []
    for name, constraints, expected in queries:
        solver = z3.Solver()
        solver.set(timeout=timeout_ms)
        labels = []
        for label, expression in constraints:
            solver.assert_and_track(expression, label)
            labels.append(label)
        result = solver.check()
        # assert_and_track uses assumption literals. Export them as assertions
        # too, so an independent SMTLIB replay cannot disable tracked facts.
        replay = z3.Solver()
        replay.add(*solver.assertions(), *(z3.Bool(label) for label in labels))
        check = {'name': name, 'scope': 'CONDITIONAL_LOCAL_SLICE',
                 'result': str(result).upper(), 'expected': expected.upper(),
                 'smtlib': replay.to_smt2(), 'unsat_core': [],
                 'unsat_core_minimality': 'NOT_CHECKED',
                 'tracked_constraints': {label: expr.sexpr() for label, expr in constraints}}
        if result == z3.unsat:
            check['unsat_core'] = [str(label) for label in solver.unsat_core()]
        elif result == z3.sat:
            check['witness'] = {
                'queued_prior': solver.model().eval(prior, model_completion=True).as_long(),
                'kind': 'SYMBOLIC_EXAMPLE_NOT_CAPTURED_STATE',
                'H0': 'ARBITRARY_UINT32_NOT_RECOVERED',
            }
        else:
            check['reason_unknown'] = solver.reason_unknown()
        checks.append(check)
    return {'backend': 'Z3', 'version': z3.get_version_string(),
            'module_path': z3.__file__, 'checks': checks,
            'wp': {'postcondition': post.sexpr(), 'store_substitution': 'Q_after_store := 0',
                   'expression': wp.sexpr(), 'simplified': z3.simplify(wp).sexpr()},
            'verified': all(c['result'] == c['expected'] for c in checks)}


def run_proof(root=ROOT, *, backend='auto', timeout_ms=2000):
    """Return JSON proof; backend is auto, z3 (required), or finite-algebra.

    No caller-supplied H0/Q evidence is accepted by this bounded API.
    Source mismatches raise ValueError; missing files raise OSError.
    """
    if backend not in ('auto', 'z3', 'finite-algebra'):
        raise ValueError('Unsupported backend')
    if type(timeout_ms) is not int or not 1 <= timeout_ms <= 10000:
        raise ValueError('timeout_ms must be in 1..10000')
    gate = source_gate(root)
    z3, unavailable = (None, None) if backend == 'finite-algebra' else _load_z3(root)
    if backend == 'z3' and z3 is None:
        raise RuntimeError('Local Z3 unavailable: ' + str(unavailable))
    if z3 is not None:
        proof = _solver_checks(z3, timeout_ms)
    else:
        proof = {
            'backend': 'FINITE_ALGEBRA', 'checks': [], 'solver_executed': False,
            'unavailable_reason': unavailable,
            'wp': {'postcondition': 'Q_after_store != queued_prior',
                   'store_substitution': 'Q_after_store := 0',
                   'simplified': 'queued_prior != 0'},
            'derivation': ['For every uint32 Q, storing 0 changes its value iff Q != 0.',
                           'The two exhaustive classes are Q = 0 and Q != 0.',
                           'H0 is read before the store and tested only after the store.'],
            'verified': True,
        }
    return {
        'query': 'Q_POST6B_DIRECTION', 'method': 'EVENT_FIRST_WP', 'schema_version': 1,
        'unknown_inputs': ['H0:uint32', 'queued_prior:uint32', 'call/caller behavior'],
        'client_first': 'UNKNOWN', 'server_first': 'UNKNOWN',
        'connection_transition': 'UNKNOWN', 'local_transition': 'UNKNOWN',
        'must_direction': None, 'minimal_discriminant': None,
        'concrete_unknowns_recovered': 0, 'proof_complete': False,
        'verdict': 'CONDITIONAL' if proof['verified'] else 'UNKNOWN',
        'source_gate': gate, 'proof': proof,
        'assumptions': [
            'Exact captured continuation and pinned restored code bytes apply.',
            'Object fields H0 at +0x40d4 and Q at +0x36c4 are readable; Q is writable.',
            'Captured stack remains readable; object, stack and code do not alias.',
            'Single thread, stable memory, no external intervention or exceptions in slice.',
        ],
        'symbolic_inputs': {'H0': 'ARBITRARY_UINT32', 'queued_prior': 'ARBITRARY_UINT32'},
        'prior_Q_evidence': 'NONE', 'H0_recovered': False,
        'local_state_change': {
            'status': 'CONDITIONAL' if proof['verified'] else 'UNKNOWN',
            'predicate': 'queued_prior != 0', 'first_change_va': '0x4133b9',
            'meaning': 'First tracked object-value change is queue housekeeping, not certified protocol progress.',
            'basis': 'No preceding call or object write in the pinned tail; Q:=0 precedes the H0 test.',
        },
        'unmodeled_boundaries': [
            {'condition': 'H0 != 0', 'va': '0x4133c7', 'kind': 'UNMODELED_CALL', 'target': '0x411990'},
            {'condition': 'H0 == 0', 'va': '0x4133cf', 'kind': 'UNMODELED_CALLER', 'target': 'UNKNOWN'},
        ],
        'zero_prior_result': 'No value change at store; continues to UNMODELED call/caller. Global events UNKNOWN.',
        'full_scope_events': {event: {'status': 'UNKNOWN', 'reason': 'CALL_CALLER_CLOSURE_AND_PRIOR_Q_EVIDENCE_MISSING'}
                              for event in ('SEND', 'RECEIVE', 'CLOSE', 'STATE_CHANGE')},
        'four_event_full_proof': False, 'global_unsat': False,
        'codegen_allowed': False, 'new_edge_accepted': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--backend', choices=('auto', 'z3', 'finite-algebra'), default='auto')
    parser.add_argument('--timeout-ms', type=int, default=2000)
    args = parser.parse_args()
    result = run_proof(backend=args.backend, timeout_ms=args.timeout_ms)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'output': str(args.output), 'verdict': result['verdict'],
                      'backend': result['proof']['backend'], 'four_event_full_proof': False}))


if __name__ == '__main__':
    main()
