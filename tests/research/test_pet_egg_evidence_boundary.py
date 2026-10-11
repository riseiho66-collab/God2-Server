"""Current-native boundaries only; synthetic probes are not gameplay outcomes.

Reuse fixture methods without inheriting or running their historical tests.
No live client, server, database, shared build, or generated evidence output.
"""
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_current_companion_state as state_fixture
import test_current_pet_incubation_guard as egg_fixture
from tools.strike_lab import current_companion_instance as instance
from tools.strike_lab import current_companion_progression as progression
from tools.strike_lab import current_companion_state as state
from tools.strike_lab import current_item_transition as item
from tools.strike_lab import recover_companion_growth as growth
from tools.strike_lab import recover_pet_incubation as incubation


class EggEligibilityBoundaryTests(unittest.TestCase):
    setUpClass = classmethod(egg_fixture.PetIncubationGuardTests.setUpClass.__func__)
    setUp = egg_fixture.PetIncubationGuardTests.setUp
    guard = egg_fixture.PetIncubationGuardTests.guard

    def test_egg_presence_does_not_grant_item_request_or_consume_inventory(self):
        for identity in (9324, 9325, 9427, 9433):
            with self.subTest(identity=identity):
                self.native.consume(struct.pack('<BHBB', 0x41, identity, 45, 1))
                before = self.native._snapshot()
                self.assertEqual(self.guard(45, identity), ('return', 1))
                self.assertEqual(self.native.request(45), b'')
                self.assertEqual(self.native.visits, [0x96390])
                self.assertEqual(self.native._snapshot(), before)
                # Presence checks do not prove possession, even after removal.
                self.native.consume(struct.pack('<BHBB', 0x41, identity, 45, 0))
                self.assertEqual(self.guard(45, identity), ('return', 1))
                self.assertEqual(bytes(self.vm.mem_read(item.SLOTS + 45 * 24, 1)), b'\0')
                self.assertEqual(bytes(self.vm.mem_read(item.SLOTS + 45 * 24 + 4, 2)), b'\0\0')

    def test_lookup_loss_and_restoration_are_not_cached_success(self):
        address = item.DEFINITIONS + 0xb2d40 + 4 * 9325
        original = bytes(self.vm.mem_read(address, 4))
        self.assertNotEqual(original, bytes(4))
        for pointer, expected in ((original, ('return', 1)),
                                  (bytes(4), ('assert', 0x58b)),
                                  (original, ('return', 1))):
            # Host fixture mutation only; the index stays read-only to x86.
            self.vm.mem_write(address, pointer)
            self.assertEqual(self.guard(45, 9325), expected)
            self.assertEqual(self.guard(30, 9325), ('assert', 0x57a))


class CompanionBoundaryTests(unittest.TestCase):
    vm = state_fixture.CurrentCompanionStateTests.vm
    run_to = state_fixture.CurrentCompanionStateTests.run_to
    consume = state_fixture.CurrentCompanionStateTests.consume
    check_native = state_fixture.CurrentCompanionStateTests.check_native

    @classmethod
    def setUpClass(cls):
        cls.image, cls.decoded = progression.qualified_inputs(CLIENT, IMAGE)

    def test_packet_to_display_uses_copied_dword_and_current_source_values(self):
        receiver = instance.NativeInstance(self.image)
        display = progression.NativeProgression(self.image, self.decoded)
        rows = growth.parse_auxiliary(progression.SOURCE, self.decoded)['records']
        values = [[growth.decimal(v) for v in growth.fields(row)] for row in rows]
        for row in rows:
            raw = bytes.fromhex(row['raw_record_hex'])
            offset = row['decoded_offset']
            self.assertEqual(self.decoded[offset:offset + len(raw)], raw)
            self.assertEqual(growth.digest(raw), row['sha256'])
        for dispatch in ('primary', 'secondary'):
            for slot in (0, 29, 42, 43):
                for packed in (0, 1 << 20, 1 << 16, 0xf5a39c7e, 0xffffffff):
                    with self.subTest(dispatch=dispatch, slot=slot, packed=packed):
                        stored = receiver.packet_store(slot, instance.record_for(packed), dispatch)
                        copied = receiver.ui_copy(slot)
                        observed = struct.unpack('<I', receiver.vm.mem_read(receiver.RECORD + 12, 4))[0]
                        self.assertEqual(observed, packed)
                        self.assertEqual(stored['writes'][3],
                                         [0x98e2b, receiver.STORE + 24 * slot + 12, 4, observed])
                        self.assertEqual(copied['writes'][3],
                                         [0x87416, receiver.RECORD + 12, 4, observed])
                        # Separate slices: passing the observed value does not
                        # claim execution of the intervening UI/metadata calls.
                        for mode in (1, 0x100):
                            args = display.arguments(observed, mode)
                            qi, si = (observed >> 20) & 15, (observed >> 16) & 15
                            self.assertEqual(args['quality'], [qi, values[0][qi]])
                            self.assertEqual(args['star'], [si, values[1][si]])
                            self.assertEqual(args['table_reads'], [
                                [0xb7e38 if mode == 1 else 0xb7efd, display.OUTPUT + qi * 2, 2],
                                [0xb7f98, display.OUTPUT + 0x100 + si * 2, 2]])

    def test_rejected_or_intercepted_packet_is_not_a_fresh_ui_instance(self):
        native = instance.NativeInstance(self.image)
        native.packet_store(29, instance.record_for(0xf5a39c7e))
        native.ui_copy(29)
        before = bytes(native.vm.mem_read(native.RECORD, 24))
        for dispatch in ('primary', 'secondary'):
            for slot, auxiliary, stop in ((50, 0, 0x98fbd), (255, 0, 0x98fbd),
                                          (38, 1, 0x98e05), (41, 1, 0x98e05)):
                with self.subTest(dispatch=dispatch, slot=slot):
                    result = native.packet_store(slot, instance.record_for(0), dispatch, auxiliary)
                    self.assertEqual(result['stop_rva'], stop)
                    self.assertFalse(result['copied'])
                    self.assertEqual(result['writes'], [])
                    self.assertEqual(bytes(native.vm.mem_read(native.RECORD, 24)), before)
        for slot, flags in ((0xffff, 1), (29, 0), (29, 2)):
            self.assertEqual(native.ui_entry_gate(slot, flags)['stop_rva'], 0x874c0)
            self.assertEqual(bytes(native.vm.mem_read(native.RECORD, 24)), before)
        native.put32(native.UI + 0xdc, 0)
        with self.assertRaises(instance.uc.UcError):
            native.ui_copy(29)
        native.put32(native.UI + 0xdc, native.OWNER)
        native.packet_store(29, instance.record_for(0x00120000))
        native.ui_copy(29)
        self.assertEqual(bytes(native.vm.mem_read(native.RECORD, 20)), instance.record_for(0x00120000))

    def test_declared_state_count_hides_residual_rows_and_rejects_truncation(self):
        logical = bytes((0x31, 0x81, 7)) + struct.pack('<5H', 1, 2, 3, 4, 5)
        logical += b'\xa5' * 4 + struct.pack('<5H', 6, 7, 8, 9, 0x800a) + b'\x69\x96'
        original = bytearray(state_fixture.state_with_keys([0x1234, 0xff81]))
        native = self.vm()
        original[state.COUNT_OFFSET] = 1
        hidden = self.check_native(native, bytes(original), logical)
        self.assertIsNone(hidden.matched_index)
        self.assertEqual(hidden.state, bytes(original))
        original[state.COUNT_OFFSET] = 2
        visible = self.check_native(native, bytes(original), logical)
        self.assertEqual(visible.matched_index, 1)
        self.assertNotEqual(visible.state, bytes(original))
        truncated = original[:state.ROWS_OFFSET + 2 * state.ROW_STRIDE - 1]
        before = bytes(truncated)
        with self.assertRaisesRegex(ValueError, 'Truncated declared deity rows'):
            state.project_deity_status_scalar(truncated, logical)
        self.assertEqual(bytes(truncated), before)
        self.assertEqual(self.check_native(native, bytes(original), logical), visible)

    def test_parseable_changed_growth_values_cannot_replace_pinned_provenance(self):
        changed = self.decoded.replace(b'0,15,30', b'0,16,30', 1)
        self.assertNotEqual(changed, self.decoded)
        rows = growth.parse_auxiliary(progression.SOURCE, changed)['records']
        self.assertEqual(growth.fields(rows[0])[1], b'16')
        with self.assertRaisesRegex(ValueError, 'Unqualified decoded QualityStar'):
            progression.NativeProgression(self.image, changed)
        valid = progression.NativeProgression(self.image, self.decoded)
        self.assertEqual(valid.arguments(1 << 20, 1)['quality'], [1, 15])


class UnprovedRuleBoundaryTests(unittest.TestCase):
    def test_serialized_egg_evidence_keeps_exact_unknown_contracts(self):
        result = json.loads(growth.serialize(incubation.extract((CLIENT / incubation.GAME).read_bytes())))
        self.assertIs(result['runtime_eligible'], False)
        entries = {entry['source_key']: entry for entry in result['entries']}
        self.assertEqual(len(entries), 55)
        expected = dict.fromkeys(('growth_formula', 'evolution_result_distribution',
                                  'success_probability', 'server_timer_rule', 'request_result_protocol'))
        for entry in entries.values():
            self.assertEqual(entry['unknown'], expected)
            self.assertIs(entry['runtime_eligible'], False)
            self.assertEqual(set(entry), {'source_key', 'section', 'source', 'claims',
                                          'runtime_eligible', 'unknown'})
        timed = {key: claim['hours'] for key, entry in entries.items()
                 for claim in entry['claims'] if claim['kind'] == 'care_duration_tooltip'}
        self.assertEqual(timed, {9324: 1, 9325: 20})
        self.assertIn(9426, entries)
        self.assertNotIn(9326, entries)

    def test_native_verified_cli_keeps_growth_rules_null(self):
        command = [sys.executable, '-B', '-m', 'tools.strike_lab.recover_companion_growth',
                   '--client-root', str(CLIENT), '--native-image', str(IMAGE), '--summary']
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        native = result['native_verification']
        self.assertEqual(native['status'], 'verified_bounded_original_row_execution')
        self.assertIs(native['growth_formula_verified'], False)
        self.assertIs(native['gameplay_runtime_verified'], False)
        self.assertEqual(set(result['unknown_contracts']), {'battle_pet', 'deity'})
        for contracts in result['unknown_contracts'].values():
            self.assertEqual(set(contracts), {'growth_rate', 'base_value', 'upgrade_formula',
                                             'experience_thresholds'})
            for contract in contracts.values():
                self.assertEqual(contract['status'], 'unknown')
                self.assertIsNone(contract['value'])
                self.assertIs(contract['runtime_eligible'], False)
                self.assertTrue(contract['missing_evidence'])


if __name__ == '__main__':
    unittest.main()
