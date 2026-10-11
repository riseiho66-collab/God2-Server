"""Exhaustive current Mission_data text lifecycles, not quest gameplay proof.

Run with python -B -m tools.strike_lab.quest_coverage_matrix --output PATH.
Original native instructions, synthetic decoded records and staged selection.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import struct
import time

from . import quest_player_scenarios as scenarios
from unicorn import UcError, UC_ERR_READ_UNMAPPED, UC_HOOK_MEM_READ_UNMAPPED

SUBTYPES = (4, 5)
SLOTS = tuple(range(15))
FULL_MASK = (1 << len(SLOTS)) - 1
UI = scenarios.UI
UI_BASE = UI & ~4095


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def source_manifest(evidence):
    """Retain source identity per original row, without duplicating text traces."""
    manifest, lines = [], set()
    require(len(evidence.missions) == len(evidence.texts), 'Mission/text count mismatch')
    for index, mission in enumerate(evidence.missions, 1):
        require(mission['id'] == index, 'Missing, duplicate or reordered mission')
        texts, objectives = evidence.texts[index - 1], mission['objectives_text']
        require(len(texts) == len(objectives) == mission['step_field'] > 0,
                'Description count mismatch')
        entry = dict(evidence.source(index), steps=[])
        for step, (objective, text) in enumerate(zip(objectives, texts), 1):
            require(objective['step'] == step, 'Missing, duplicate or reordered step')
            line = objective['source_line']
            require(line not in lines, 'Duplicate description source line')
            lines.add(line)
            row = evidence.rows[line]
            require(bytes.fromhex(row['raw_fields_hex'][3]) == text,
                    'Description differs from source bytes')
            entry['steps'].append(dict(step=step, source_line=line,
                source_record_sha256=row['source_record_sha256'],
                text_sha256=hashlib.sha256(text).hexdigest(), text_bytes=len(text),
                passed_slot_masks={'4': 0, '5': 0}, cases_passed=0))
        manifest.append(entry)
    return manifest


def cases(evidence):
    for mission in evidence.missions:
        for step in range(1, mission['step_field'] + 1):
            for subtype in SUBTYPES:
                for slot in SLOTS:
                    yield mission['id'], step, subtype, slot


def validate_case(evidence, mission, step, subtype, slot):
    if (type(mission) is not int or not 1 <= mission <= len(evidence.missions)
            or type(step) is not int or not 1 <= step <= len(evidence.texts[mission - 1])
            or subtype not in SUBTYPES or type(subtype) is not int
            or slot not in SLOTS or type(slot) is not int):
        raise ValueError('Case outside original mission/step/subtype/slot domain')


def record_pass(manifest, mission, step, subtype, slot):
    item = manifest[mission - 1]['steps'][step - 1]
    key, bit = str(subtype), 1 << slot
    require(not item['passed_slot_masks'][key] & bit, 'Duplicate lifecycle case')
    item['passed_slot_masks'][key] |= bit
    item['cases_passed'] += 1


def audit_coverage(evidence, manifest):
    """Compare the executed ledger against a fresh complete source enumeration."""
    expected = source_manifest(evidence)
    require(len(manifest) == len(expected), 'Missing or extra mission coverage')
    for actual, source in zip(manifest, expected):
        require({k: v for k, v in actual.items() if k != 'steps'} ==
                {k: v for k, v in source.items() if k != 'steps'}, 'Mission identity mismatch')
        require(len(actual['steps']) == len(source['steps']), 'Missing or extra step coverage')
        for checked, original in zip(actual['steps'], source['steps']):
            original['passed_slot_masks'] = {'4': FULL_MASK, '5': FULL_MASK}
            original['cases_passed'] = 30
            require(checked == original, 'Incomplete, duplicate or mismatched step coverage')


class NativeMatrix:
    """One persistent Player VM, a small state model, and no retained trace."""
    def __init__(self, evidence, subtype):
        self.evidence, self.subtype = evidence, subtype
        self.player = scenarios.Player(evidence)
        self.player.trace = deque(maxlen=0)
        # Avoid one watchdog thread per tiny emulation slice. Preserve the
        # existing 100,000-instruction bound and exact original stop checks.
        self.native_returns = 0
        self.player.oracle.run_to = self.run_to
        self.expected = self.player.state()
        self.stage = 'seed'
        self.baseline = [(1 << 16) | (slot % len(evidence.missions) + 1) for slot in SLOTS]

    def run_to(self, vm, entry, stop):
        base = scenarios.oracle.BASE
        vm.emu_start(base + entry, base + stop, count=100000)
        require(vm.reg_read(scenarios.oracle.quest.routes.UC_X86_REG_EIP) == base + stop,
                'Original slice did not reach its bounded stop')
        self.native_returns += 1

    def __enter__(self):
        try:
            for slot, packed in enumerate(self.baseline):
                self.receive(slot, packed)
        except BaseException:
            self.player.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *exc):
        self.player.__exit__(*exc)

    def receive(self, slot, packed):
        expected = dict(self.expected, slots=self.expected['slots'].copy())
        expected['slots'][slot] = packed
        highest = max((i for i, value in enumerate(expected['slots'])
                       if 1 <= (value & 0xffff) <= len(self.evidence.missions)), default=0)
        expected['pages'] = highest // 5 + 1
        if expected['page'] >= expected['pages']:
            expected['page'] = 0
        if self.subtype == 5:
            expected['selected'] = packed
            expected['refresh_calls'] += 1
        elif slot == 14:
            expected['refresh_calls'] += int(expected['suppression'] == 0)
            expected['suppression'] = 0
        actual = self.player.receive(slot, self.subtype, packed)
        require(actual == expected, 'Receive/replay/clear changed unexpected journal state')
        self.expected = expected

    def describe(self, slot, *, click, text, source_line, valid):
        result = self.player.describe(slot, click=click)
        require((result['text_hex'], result['source_line'], result['valid_description']) ==
                (text.hex(), source_line, valid), 'Native description/source identity mismatch')
        if click:
            self.expected['page'] = slot // 5
            if valid:
                self.expected['selected'] = self.expected['slots'][slot]
        require(result['state'] == self.expected, 'Description changed unexpected journal state')

    def lifecycle(self, mission, step, slot):
        validate_case(self.evidence, mission, step, self.subtype, slot)
        text = self.evidence.texts[mission - 1][step - 1]
        line = self.evidence.missions[mission - 1]['objectives_text'][step - 1]['source_line']
        packed = step << 16 | mission
        self.stage = 'receive'
        self.receive(slot, packed)
        self.stage = 'read'
        self.describe(slot, click=False, text=text, source_line=line, valid=True)
        self.stage = 'staged_select'
        self.describe(slot, click=True, text=text, source_line=line, valid=True)
        self.stage = 'replay'
        self.receive(slot, packed)
        self.stage = 'replay_read'
        self.describe(slot, click=False, text=text, source_line=line, valid=True)
        self.stage = 'clear'
        self.receive(slot, 0)
        self.stage = 'clear_read'
        self.describe(slot, click=False, text=b'', source_line=None, valid=False)
        self.stage = 'restore_peer'
        self.receive(slot, self.baseline[slot])
        require(self.expected['slots'] == self.baseline, 'Peer slots did not survive lifecycle')
        require(not self.player.trace, 'Matrix unexpectedly retained player traces')


def boundary_checks(evidence, result=None):
    """Two further reused VMs. Native malformed records are not atomic validators."""
    totals = dict(invalid_step=0, zero_selector_alias=0, invalid_mission=0,
                  invalid_slot=0, truncated_record=0, invalid_slot_selection_writes=0)
    result = {} if result is None else result
    result.update(status='RUNNING', cases_passed=0, counts=totals, vms_started=0,
        invalid_slot_boundary='C9688 assertion call; continuation NOT_EXECUTED',
        atomicity='Truncated DB4/DB5 preserves full UI; invalid-slot DB5 changes selection',
        description_boundary='10F580 renderer entry; rendering NOT_EXECUTED')

    def passed(kind):
        totals[kind] += 1
        result['cases_passed'] += 1

    for subtype in SUBTYPES:
        with NativeMatrix(evidence, subtype) as matrix:
            result['vms_started'] += 1
            player = matrix.player
            for mission in evidence.missions:
                identity = mission['id']
                slot = (identity - 1) % 15
                result['current_case'] = dict(kind='invalid_step', subtype=subtype,
                                               mission=identity, slot=slot)
                # One-past-last for EVERY source mission, retaining all peers.
                matrix.receive(slot, (mission['step_field'] + 1) << 16 | identity)
                for click in (False, True):
                    matrix.describe(slot, click=click, text=b'', source_line=None, valid=False)
                passed('invalid_step')
                # Native selector zero aliases the first description, not an extra source step.
                result['current_case']['kind'] = 'zero_selector_alias'
                matrix.receive(slot, identity)
                matrix.describe(slot, click=True, text=evidence.texts[identity - 1][0],
                    source_line=mission['objectives_text'][0]['source_line'], valid=True)
                passed('zero_selector_alias')
                matrix.receive(slot, matrix.baseline[slot])
            for packed in (0, len(evidence.missions) + 1, 0xffff0000, 0xffffffff):
                result['current_case'] = dict(kind='invalid_mission', subtype=subtype, packed=packed)
                matrix.receive(14, packed)
                for click in (False, True):
                    matrix.describe(14, click=click, text=b'', source_line=None, valid=False)
                passed('invalid_mission')
                matrix.receive(14, matrix.baseline[14])
            for slot in (15, 255, 0x80000000, 0xffffffff):
                result['current_case'] = dict(kind='invalid_slot', subtype=subtype, slot=slot)
                matrix.receive(0, matrix.baseline[0])
                matrix.describe(0, click=True, text=evidence.texts[0][0],
                    source_line=evidence.missions[0]['objectives_text'][0]['source_line'], valid=True)
                before = bytes(player.vm.mem_read(UI_BASE, 0x240000))
                packed = 1 << 16 | len(evidence.missions)
                player.oracle.dispatch(player.vm, scenarios.packet(slot, subtype, packed),
                                       stop=0xc9688)
                expected = bytearray(before)
                if subtype == 5:
                    struct.pack_into('<I', expected, UI - UI_BASE + 0x232eb8, packed)
                    matrix.expected['selected'] = packed
                    totals['invalid_slot_selection_writes'] += 1
                require(bytes(player.vm.mem_read(UI_BASE, 0x240000)) == expected,
                        'Invalid slot mutated more than the native DB5 selection write')
                require(player.state() == matrix.expected, 'Invalid slot state mismatch')
                passed('invalid_slot')
            for length in range(1, 13):
                result['current_case'] = dict(kind='truncated_record', subtype=subtype, length=length)
                before = bytes(player.vm.mem_read(UI_BASE, 0x240000))
                faults = []
                hook = player.vm.hook_add(UC_HOOK_MEM_READ_UNMAPPED,
                    lambda vm, access, address, size, value, data: faults.append((address, size)))
                try:
                    player.oracle.dispatch(player.vm, scenarios.packet(0, subtype, 0x10001)[:length])
                except UcError as error:
                    require(error.errno == UC_ERR_READ_UNMAPPED, 'Unexpected truncation fault')
                else:
                    raise AssertionError('Truncated record unexpectedly returned')
                finally:
                    player.vm.hook_del(hook)
                end = scenarios.oracle.quest.PACKET_PAGE + 4096
                expected_fault = (end, 1) if length == 1 else (max(end, end + 9 - length), 4)
                require(faults == [expected_fault], 'Fault outside expected input read')
                fault_rva = 0x854fd if length == 1 else (0x8565b if subtype == 4 else 0x85693)
                require(player.vm.reg_read(scenarios.oracle.quest.routes.UC_X86_REG_EIP) ==
                        scenarios.oracle.BASE + fault_rva, 'Unexpected truncation fault PC')
                require(bytes(player.vm.mem_read(UI_BASE, 0x240000)) == before,
                        'Truncated journal record partially mutated UI')
                require(player.state() == matrix.expected, 'Truncation state mismatch')
                passed('truncated_record')
    result.pop('current_case', None)
    result['status'] = 'PASS'
    return result


def run(evidence=None, progress=None):
    from contextlib import ExitStack
    evidence = evidence or scenarios.Evidence()
    manifest = source_manifest(evidence)
    steps = sum(len(m['steps']) for m in manifest)
    report = dict(schema='current-quest-coverage-matrix-v1', status='RUNNING',
        qualification='OFFLINE_ORIGINAL_NATIVE_TEXT_SCENARIOS_ONLY',
        permission_source='Explicit user request: current-client offline matrix; no gameplay authority granted',
        stimulus='SYNTHETIC decoded DB4/DB5 records, initial memory, staged page/click registers',
        source=dict(image_sha256=scenarios.oracle.quest.routes.IMAGE_SHA,
            mission_source_sha256=scenarios.oracle.SOURCE_SHA,
            mission_decoded_sha256=scenarios.oracle.DECODED_SHA,
            mission_file='God2/Data2/Patch/Comm/Mission_data.csvZ'),
        source_tables={name: dict(source_file=table['source_file'],
            source_sha256=table['source_sha256'], decoded_sha256=table['decoded_sha256'],
            declared_records=table['declared_records'], actual_source_records=len(table['records']),
            coverage_scope='Mission_data native text lifecycle' if name == 'missions' else
                           'Source enumeration only; runtime coverage UNKNOWN',
            gameplay_runtime_coverage='UNKNOWN', cross_table_join_authority='UNKNOWN')
            for name, table in evidence.catalog['tables'].items()},
        coverage=dict(missions=len(manifest), original_description_steps=steps,
            subtypes=list(SUBTYPES), slots=list(SLOTS), cases_expected=steps * 30,
            cases_attempted=0, cases_passed=0, source_byte_checks=0, clear_blank_checks=0,
            lifecycle_operations_passed=0),
        execution=dict(lifecycle_vms=0, boundary_vms=0, retained_trace_entries=0),
        unknown_authority=list(scenarios.UNKNOWN_RULES), missions=manifest, failures=[])
    current, stage = None, 'initialization'
    try:
        with ExitStack() as stack:
            matrices = {}
            for subtype in SUBTYPES:
                matrices[subtype] = stack.enter_context(NativeMatrix(evidence, subtype))
                report['execution']['lifecycle_vms'] += 1
            previous = 0
            for mission, step, subtype, slot in cases(evidence):
                if progress and mission != previous:
                    if previous and (previous % 50 == 0 or previous == len(manifest)):
                        progress(previous, report['coverage']['cases_passed'])
                    previous = mission
                current = dict(mission=mission, step=step, subtype=subtype, slot=slot)
                report['coverage']['cases_attempted'] += 1
                before = matrices[subtype].native_returns
                matrices[subtype].lifecycle(mission, step, slot)
                operations = matrices[subtype].native_returns - before
                require(operations == 8, 'Incomplete native lifecycle operations')
                record_pass(manifest, mission, step, subtype, slot)
                report['coverage']['cases_passed'] += 1
                report['coverage']['source_byte_checks'] += 3
                report['coverage']['clear_blank_checks'] += 1
                report['coverage']['lifecycle_operations_passed'] += operations
            audit_coverage(evidence, manifest)
            if progress:
                progress(len(manifest), report['coverage']['cases_passed'])
        stage, current = 'boundaries', None
        report['boundaries'] = {}
        boundary_checks(evidence, report['boundaries'])
        report['execution']['boundary_vms'] = 2
        report['status'] = 'PASS'
    except (AssertionError, ValueError, UcError) as error:
        if current is not None:
            stage = matrices[current['subtype']].stage
        report['status'] = 'FAIL'
        if stage == 'boundaries':
            report['boundaries']['status'] = 'FAIL'
            current = report['boundaries'].get('current_case')
            report['execution']['boundary_vms'] = report['boundaries'].get('vms_started', 0)
        report['failures'].append(dict(case=current, stage=stage,
                                       error_type=type(error).__name__, message=str(error)))
    return report


def serialize(report):
    return json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.suffix != '.json' or output.is_relative_to(scenarios.ROOT.parent / 'God2'):
        parser.error('Output must be a JSON file outside the read-only client tree')
    started = time.perf_counter()
    report = run(progress=lambda missions, passed: print(
        f'checked_missions={missions} lifecycle_cases_passed={passed}', flush=True))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(serialize(report), encoding='utf-8', newline='\n')
    print(json.dumps(dict(status=report['status'], coverage=report['coverage'],
        boundaries=report.get('boundaries'), elapsed_seconds=round(time.perf_counter() - started, 3)),
        sort_keys=True), flush=True)
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
