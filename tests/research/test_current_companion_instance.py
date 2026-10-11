"""New native message/store writer evidence; no display or getter tests."""
from pathlib import Path
import struct
import unittest

from tools.strike_lab import current_companion_instance as instance


ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'


class CurrentCompanionInstanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = instance.qualified_image(IMAGE)
        cls.result = instance.build_evidence(IMAGE)

    def test_both_dispatches_slot_byte_width_and_signed_bounds(self):
        self.assertEqual(self.result['slot_case_count'], 512)
        for dispatch in ('primary', 'secondary'):
            self.assertEqual(self.result['slot_outcomes'][dispatch],
                             {str(i): 0x98e2d if i < 50 else 0x98fbd for i in range(256)})
        self.assertEqual(self.result['bindings']['secondary_opcodes_for_same_case'], [0x3b])
        for case in self.result['auxiliary_cases']:
            intercepted = 38 <= case['slot'] <= 41 and case['auxiliary_state'] == 1
            self.assertEqual(case['stop_rva'], 0x98e05 if intercepted else 0x98e2d)
            self.assertEqual(case['copied'], not intercepted)

    def test_ui_signed_word_and_event_bit_gate(self):
        for case in self.result['ui_entry_gates']:
            admitted = case['slot_word'] < 0x8000 and bool(case['flags'] & 1)
            self.assertEqual(case['stop_rva'], 0x87372 if admitted else 0x874c0)
            self.assertEqual(case['writes'], [])
        for case in self.result['ui_selection_cases']:
            self.assertEqual(case['copied'], case['slot'] < 30 or case['slot'] in (42, 43))
            self.assertEqual(case['stop_rva'], 0x87430 if case['copied'] else 0x873b3)

    def test_every_dword_bit_survives_actual_two_stage_writes(self):
        expected = []
        values = [0, 0xffffffff, 0xa5a5a5a5, 0x5a5a5a5a] + [1 << i for i in range(32)]
        for dispatch in ('primary', 'secondary'):
            for slot in (0, 29, 42, 43):
                for packed in values:
                    expected.append({'dispatch': dispatch, 'slot': slot, 'packed': packed,
                                     'observed': packed,
                                     'packet_write': [0x98e2b, 0x1208561c + 24 * slot, 4, packed],
                                     'ui_write': [0x87416, 0x13003ad0, 4, packed]})
        self.assertEqual(self.result['transfer_count'], 288)
        self.assertEqual(self.result['transfers_sha256'], instance.digest(instance.serialize(expected)))

    def test_all_twenty_bytes_and_exact_native_read_write_provenance(self):
        native = instance.NativeInstance(self.image)
        record = bytes(range(0x81, 0x95))
        store = native.packet_store(29, record)
        self.assertEqual([r for r in store['reads'] if r[0] == 0x98e2b],
                         [[0x98e2b, native.MESSAGE + 5 + i, 4] for i in range(0, 20, 4)])
        self.assertEqual(store['writes'],
                         [[0x98e2b, native.STORE + 24 * 29 + i, 4,
                           int.from_bytes(record[i:i + 4], 'little')] for i in range(0, 20, 4)])
        ui = native.ui_copy(29)
        self.assertEqual([r for r in ui['reads'] if r[0] == 0x87416],
                         [[0x87416, native.STORE + 24 * 29 + i, 4] for i in range(0, 20, 4)])
        self.assertEqual(bytes(native.vm.mem_read(native.RECORD, 20)), record)
        self.assertEqual([w[2] for w in ui['writes']], [4, 4, 4, 4, 4, 2, 1])

    def test_caller_pointer_and_distinct_zero_reset_writer(self):
        self.assertEqual(self.result['caller_pointer']['caller_arguments'],
                         [0x1a6, 0x1b5, 0x13003ac4, 0xffffff81])
        self.assertEqual(self.result['caller_pointer']['stop_rva'], 0x876ac)
        self.assertEqual(self.result['reset']['writes'],
                         [[pc, 0x13003ac4 + i * 4, 4, 0] for i, pc in enumerate(
                             (0x869f4, 0x869f6, 0x869f9, 0x869fc, 0x869ff, 0x86a02))])

    def test_pinned_native_identity_and_range_provenance(self):
        self.assertEqual(self.result['image_sha256'], instance.IMAGE_SHA)
        for kind in ('executed_ranges', 'static_only_ranges'):
            for span in self.result[kind].values():
                self.assertEqual(span['sha256'], instance.digest(
                    self.image[span['start_rva']:span['stop_rva_exclusive']]))
        for call in self.result['bindings']['calls']:
            pc = call['call_rva']
            self.assertEqual(self.image[pc], 0xe8)
            self.assertEqual(pc + 5 + struct.unpack_from('<i', self.image, pc + 1)[0], call['target_rva'])
        with self.assertRaisesRegex(ValueError, 'native image'):
            instance.NativeInstance(self.image[:-1] + bytes((self.image[-1] ^ 1,)))
        self.assertTrue({0x98e2b, 0x87416, 0x869fc, 0x87245, 0x87691} <= set(self.result['executed_pcs']))
        self.assertNotIn(0x876ac, self.result['executed_pcs'])
        self.assertNotIn(0xb5be0, self.result['executed_pcs'])

    def test_unexecuted_calls_fail_instead_of_returning_success(self):
        native = instance.NativeInstance(self.image)
        for start, name in ((0x98e42, 'slot_guard_and_store'), (0x8738f, 'ui_entry_gate'),
                            (0x876ac, 'wrapper_entry'), (0x98e05, 'slot_guard_and_store')):
            native.prepare()
            with self.assertRaises((AssertionError, instance.uc.UcError)):
                native.run(start, (start + 5,), (name,))
        native.prepare()
        native.reg('ECX', native.UI)
        with self.assertRaisesRegex(AssertionError, 'Out-of-bound native write'):
            native.run(0x869e0, (0x86a04,), ('ui_reset',))

    def test_read_only_inputs_null_owner_faults_and_open_semantics(self):
        native = instance.NativeInstance(self.image)
        for address in (native.BUFFER_PAGE, native.AUX, native.SECONDARY):
            permissions = [p for a, b, p in native.vm.mem_regions() if a <= address <= b]
            self.assertEqual(permissions, [instance.uc.UC_PROT_READ])
        native.put32(native.UI + 0xdc, 0)
        with self.assertRaises(instance.uc.UcError):
            native.ui_copy(0)
        for key in ('runtime_eligible', 'growth_formula_verified', 'experience_thresholds_verified'):
            self.assertFalse(self.result[key])
        self.assertEqual(self.result['growth_status'], 'OPEN')
        self.assertEqual(self.result['binding']['packed_message_offset'], 17)
        for slot, record in ((-1, b'a' * 20), (256, b'a' * 20), (0, b'a' * 19)):
            with self.assertRaises(ValueError):
                native.packet_store(slot, record)


if __name__ == '__main__':
    unittest.main()
