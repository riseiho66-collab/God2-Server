"""All current definitions x all actors x explicit states; target evidence only."""
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import time

from . import current_skill_identity as identity
from . import current_skill_target_setup as targeting
from .recover_combat_rules import CLIENT, IMAGE, read_pinned

ROOT = Path(__file__).resolve().parents[2]
EXECUTABLE = ROOT / 'build/tests/Release/native-skill-targeting.exe'
OUTPUT = ROOT / 'artifacts/research/skill-coverage-matrix-20260920.json'
ACTORS = tuple(range(14))
FORMULAS = ('damage', 'hit', 'crit', 'five_element_coefficients', 'resource_cost')
RESULT_COLUMNS = ('mask_0', 'mask_1', 'saved_mask_0', 'saved_mask_1',
                  'stored_mode', 'setup_value', 'setup_flag', 'passes_kind_gate')
SAVED = (0x89abcdef, 0x76543210)
STATES = {
    'empty': targeting.TargetState((0, 0), SAVED, (None,) * 28),
    'full': targeting.TargetState((0x3fff, 0x3fff), SAVED, (0,) * 28),
    'sparse_signed': targeting.TargetState(
        (0x2001, 0x0420), SAVED, (None, -32768, -1, 0, 32767, None, -1) * 4),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def serialize(report):
    return json.dumps(report, sort_keys=True, ensure_ascii=True, indent=2) + '\n'


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def state_records():
    return [{'id': name, 'masks': list(state.masks),
             'saved_masks': list(state.saved_masks),
             'entity_words': list(state.entity_words)} for name, state in STATES.items()]


def formula_evidence():
    return {name: {'status': 'unverified', 'authoritative_formula': None,
                   'server_coefficients': None, 'runtime_enabled': False}
            for name in FORMULAS}


def target_branch(mode):
    if mode in (1, 2, 3, 4, 5, 13, 14, 16):
        return 'reachable_rows'
    if mode in (6, 7, 15):
        return 'row_template_' + str(mode)
    return {8: 'fixed_mask_001f', 9: 'fixed_mask_0400', 10: 'fixed_mask_0400',
            11: 'actor_only', 12: 'reachable_side_zero',
            17: 'actor_only_save_original_masks'}.get(mode, 'clear_masks')


def batch_line(fields, actor, state):
    values = (fields.identifier, fields.kind, fields.word_3e,
              fields.reach_44, fields.mode_45, actor,
              *state.masks, *state.saved_masks,
              *(32768 if word is None else word for word in state.entity_words))
    return ' '.join(map(str, values))


def parse_batch(stdout, expected_count):
    rows = []
    for line in stdout.splitlines():
        fields = line.split()
        if len(fields) != len(RESULT_COLUMNS):
            raise ValueError('Formal batch result must have eight integers')
        rows.append([int(value) for value in fields])
    if len(rows) != expected_count:
        raise ValueError('Formal batch result denominator mismatch')
    return rows


class NativeTargetOracle:
    """Compose fixture methods without loading or inheriting any test suite."""

    def __init__(self, image):
        sys.path.insert(0, str(ROOT / 'tests/research'))
        import test_current_skill_target_setup as fixture_module
        self.module = fixture_module
        self.fixture = fixture_module.CurrentSkillTargetSetupTests(methodName='runTest')
        self.fixture.image = image
        self.vm = self.fixture.target_machine()

    def kind_gate(self, raw):
        m, f, vm = self.module, self.fixture, self.vm
        vm.mem_write(m.RECORD, raw)
        vm.reg_write(m.UC_X86_REG_EBP, m.RECORD)
        f.target_invoke(vm, 0x115571, stops=(0x11557f, 0x11559a))
        return int(vm.reg_read(m.UC_X86_REG_EIP) == m.native.BASE + 0x11559a)

    def observe(self, fields, actor, state, gate):
        m, f, vm = self.module, self.fixture, self.vm
        before = f.install_target(vm, state)
        f.target_invoke(vm, 0x11ee90,
            (m.OUTPUT, fields.mode_45, actor, fields.reach_44, fields.kind, fields.identifier),
            writes=((m.OUTPUT, m.OUTPUT + 8), (m.CONTEXT + 0x2fc, m.CONTEXT + 0x308)))
        masks = struct.unpack('<2I', vm.mem_read(m.OUTPUT, 8))
        saved_mode = struct.unpack('<3I', vm.mem_read(m.CONTEXT + 0x2fc, 12))
        lookup_executed = 0x11e6e0 in f.executed
        # Check untouched memory using actual outputs, not a translated formula.
        struct.pack_into('<3I', before, 0x2fc, *saved_mode)
        f.assertEqual(bytes(vm.mem_read(m.CONTEXT, 0x308)), bytes(before))
        battle = bytearray(b'\xa5' * 4096)
        struct.pack_into('<2I', battle, 0x434, *masks)
        f.assertEqual(bytes(vm.mem_read(m.native.BATTLE, 4096)), bytes(battle))
        value, flag = -1, -1
        if 1 <= fields.mode_45 <= 17:
            value = f.target_invoke(vm, 0x11ead0, (fields.mode_45, m.FLAG),
                                    writes=((m.FLAG, m.FLAG + 4),))
            flag, = struct.unpack('<I', vm.mem_read(m.FLAG, 4))
        return [*masks, *saved_mode, value, flag, gate], lookup_executed


def summarize(report):
    rows = report['definitions']
    cases = [case for row in rows for case in row['cases']]
    branches = {}
    for row in rows:
        branch = branches.setdefault(row['target_branch'],
                                     {'definitions': 0, 'cases_run': 0, 'cases_pass': 0})
        branch['definitions'] += 1
        branch['cases_run'] += len(row['cases'])
        branch['cases_pass'] += sum(case['passed'] for case in row['cases'])
    passed = sum(case['passed'] for case in cases)
    return {
        'definitions_discovered': len(rows), 'actor_positions': len(ACTORS),
        'target_states': len(STATES), 'cases_expected': len(rows) * len(ACTORS) * len(STATES),
        'cases_run': len(cases), 'cases_pass': passed, 'cases_fail': len(cases) - passed,
        'definitions_all_cases_pass': sum(all(c['passed'] for c in r['cases']) for r in rows),
        'kind_gate_rejected_definitions': sum(not r['native_kind_gate'] for r in rows),
        'native_setup_cases': sum(r['setup_cases_run'] for r in rows),
        'setup_unqualified_cases': sum(r['setup_cases_unqualified'] for r in rows),
        'kind3_entity_lookup_cases': sum(c['entity_lookup_executed'] for c in cases),
        'target_branches': branches,
        'formula_counts': {name: {'definitions': len(rows), 'verified': 0,
                                  'unverified': len(rows)} for name in FORMULAS},
    }


def validate_report(report, source):
    """Reject missing/duplicate identities, inflated counts and promoted formulas."""
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    require(digest(source) == identity.SOURCE_SHA256, 'Unpinned definition source')
    definitions = identity.decode_definitions(source)
    require(report['schema_version'] == 1 and report['scope'] == 'current_client_target_helpers_only',
            'Unexpected report scope')
    require(report['source'] == {'path': identity.SOURCE, 'sha256': digest(source),
            'bytes': len(source), 'group_counts': [struct.unpack_from('<I', source,
                4 + kind * identity.GROUP_STRIDE)[0] for kind in range(4)]},
            'Source provenance mismatch')
    require(report['native_image']['sha256'] == identity.IMAGE_SHA256, 'Native pin mismatch')
    require(report['states'] == state_records(), 'Target states changed')
    require(report['actor_positions'] == list(ACTORS), 'Actor denominator mismatch')
    require(report['result_columns'] == list(RESULT_COLUMNS), 'Result columns changed')
    rows = report['definitions']
    require([(r['kind'], r['id']) for r in rows] == sorted(definitions),
            'Definition keys missing, duplicated or out of order')
    expected_keys = [(actor, state) for actor in ACTORS for state in STATES]
    for row in rows:
        definition = definitions[row['kind'], row['id']]
        fields = targeting.Fields.from_record(definition.raw)
        require(row['source_sha256'] == digest(source) and
                row['source_offset'] == definition.source_offset and
                row['record_length'] == len(definition.raw) and
                row['record_sha256'] == digest(definition.raw), 'Definition provenance mismatch')
        require(row['raw_fields'] == asdict(fields), 'Raw field mismatch')
        require(row['target_branch'] == target_branch(fields.mode_45), 'Target branch mismatch')
        require(type(row['native_kind_gate']) is int and row['native_kind_gate'] in (0, 1),
                'Invalid native gate')
        require(row['formula_evidence'] == formula_evidence(), 'Formula authority promotion')
        cases = row['cases']
        require([(c['actor'], c['state']) for c in cases] == expected_keys,
                'Case keys missing, duplicated or out of order')
        for case in cases:
            for name in ('native', 'formal'):
                require(len(case[name]) == 8 and all(type(v) is int for v in case[name]),
                        'Invalid result vector')
            require(case['passed'] is (case['native'] == case['formal']),
                    'Case comparison mismatch')
            require(case['native'][7] == row['native_kind_gate'], 'Native gate mismatch')
            require(case['native'][4] == fields.mode_45, 'Native stored mode mismatch')
            require(case['entity_lookup_executed'] is
                    (fields.kind == 3 and 8 <= fields.identifier <= 10),
                    'Native entity lookup branch mismatch')
            if not 1 <= fields.mode_45 <= 17:
                require(case['native'][5:7] == [-1, -1], 'Unqualified setup executed')
        passed = sum(c['passed'] for c in cases)
        require((row['cases_run'], row['cases_pass'], row['cases_fail']) ==
                (len(cases), passed, len(cases) - passed), 'Definition counters mismatch')
        setup = len(cases) if 1 <= fields.mode_45 <= 17 else 0
        require((row['setup_cases_run'], row['setup_cases_unqualified']) ==
                (setup, len(cases) - setup), 'Setup denominator mismatch')
    require(report['summary'] == summarize(report), 'Summary counters mismatch')


def require_success(report):
    summary = report['summary']
    if summary['cases_fail'] or summary['cases_run'] != summary['cases_expected']:
        raise ValueError('Target comparison failed or matrix incomplete')


def run_matrix(timeout_seconds=300, progress=None):
    if not 1 <= timeout_seconds <= 1800:
        raise ValueError('Matrix timeout must be 1..1800 seconds')
    started = time.perf_counter()
    deadline = started + timeout_seconds
    source = read_pinned(CLIENT / identity.SOURCE, identity.SOURCE_SHA256)
    image = read_pinned(IMAGE, identity.IMAGE_SHA256)
    executable_hash = digest(EXECUTABLE.read_bytes())
    definitions = identity.decode_definitions(source)
    oracle = NativeTargetOracle(image)
    report = {
        'schema_version': 1, 'scope': 'current_client_target_helpers_only',
        'source': {'path': identity.SOURCE, 'sha256': digest(source), 'bytes': len(source),
                   'group_counts': [struct.unpack_from('<I', source,
                       4 + kind * identity.GROUP_STRIDE)[0] for kind in range(4)]},
        'native_image': {'path': IMAGE.relative_to(ROOT).as_posix(),
                         'sha256': digest(image), 'bytes': len(image)},
        'formal_executable': {'path': EXECUTABLE.relative_to(ROOT).as_posix(),
                              'sha256': executable_hash, 'arguments': ['--batch']},
        'actor_positions': list(ACTORS), 'states': state_records(),
        'result_columns': list(RESULT_COLUMNS), 'definitions': [],
        'limits': {'native_instructions_per_invocation': 20000,
                   'formal_batch_timeout_seconds': 30, 'native_vm_instances': 1},
        'evidence_boundary': 'Synthetic offline helper states, including caller-gated definitions. '
            'Mode-zero setup is unqualified. Target matches do not recover server damage, hit, '
            'crit, element or resource formulas; no cast authorization or live gameplay claim.',
    }
    lines, flat_cases = [], []
    native_started = time.perf_counter()
    for index, (_, definition) in enumerate(sorted(definitions.items()), 1):
        fields = targeting.Fields.from_record(definition.raw)
        gate = oracle.kind_gate(definition.raw)
        row = {'kind': definition.kind, 'id': definition.id,
               'source_sha256': digest(source), 'source_offset': definition.source_offset,
               'record_length': len(definition.raw), 'record_sha256': digest(definition.raw),
               'raw_fields': asdict(fields), 'native_kind_gate': gate,
               'target_branch': target_branch(fields.mode_45),
               'formula_evidence': formula_evidence(), 'cases': []}
        for actor in ACTORS:
            for name, state in STATES.items():
                if time.perf_counter() >= deadline:
                    raise TimeoutError('Native matrix deadline exceeded; no report emitted')
                observed, lookup = oracle.observe(fields, actor, state, gate)
                case = {'actor': actor, 'state': name, 'native': observed,
                        'entity_lookup_executed': lookup}
                row['cases'].append(case)
                flat_cases.append(case)
                lines.append(batch_line(fields, actor, state))
        report['definitions'].append(row)
        if progress and (index % 64 == 0 or index == len(definitions)):
            progress(f'Native definitions {index}/{len(definitions)}; cases {len(flat_cases)}')
    native_seconds = time.perf_counter() - native_started
    remaining = deadline - time.perf_counter()
    if remaining <= 0:
        raise TimeoutError('Matrix deadline exceeded before formal batch')
    formal_started = time.perf_counter()
    result = subprocess.run([str(EXECUTABLE), '--batch'], input='\n'.join(lines) + '\n',
                            capture_output=True, text=True, check=True,
                            timeout=min(30, remaining), cwd=ROOT)
    formal = parse_batch(result.stdout, len(flat_cases))
    if digest(EXECUTABLE.read_bytes()) != executable_hash:
        raise ValueError('Formal executable changed during matrix')
    formal_seconds = time.perf_counter() - formal_started
    for case, actual in zip(flat_cases, formal):
        case['formal'] = actual
        case['passed'] = case['native'] == actual
    for row in report['definitions']:
        row['cases_run'] = len(row['cases'])
        row['cases_pass'] = sum(c['passed'] for c in row['cases'])
        row['cases_fail'] = row['cases_run'] - row['cases_pass']
        row['setup_cases_run'] = row['cases_run'] if 1 <= row['raw_fields']['mode_45'] <= 17 else 0
        row['setup_cases_unqualified'] = row['cases_run'] - row['setup_cases_run']
    report['summary'] = summarize(report)
    validate_report(report, source)
    return report, {'native_seconds': round(native_seconds, 6),
                    'formal_seconds': round(formal_seconds, 6),
                    'total_seconds': round(time.perf_counter() - started, 6)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--timeout-seconds', type=float, default=300)
    args = parser.parse_args()
    if args.output is not None and args.output.resolve() != OUTPUT.resolve():
        parser.error('--output must be artifacts/research/skill-coverage-matrix-20260920.json')
    try:
        report, timing = run_matrix(args.timeout_seconds, lambda s: print(s, file=sys.stderr, flush=True))
        encoded = serialize(report).encode('ascii')
        if args.output is not None:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(encoded)
            print(serialize({'summary': report['summary'], 'report_sha256': digest(encoded)}), end='')
        else:
            print(encoded.decode('ascii'), end='')
        print(json.dumps({'timing': timing}, sort_keys=True), file=sys.stderr, flush=True)
        require_success(report)
    except (OSError, ValueError, AssertionError, TimeoutError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
