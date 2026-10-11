"""Executed current result arithmetic and provenance, not damage coefficients."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_damage_formula as damage


class CurrentDamageDataflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proof = damage.DamageDataflowProof()

    def test_received_word_sign_extension_add_replace_and_no_add_paths(self):
        for word in (0, 1, 32767, 32768, 65535, 65506, 1234):
            for selector in (0, 1, 2, 3, 4, 5, 7, 8, 9, 20):
                with self.subTest(word=word, selector=selector):
                    before = damage.actor_snapshot(accumulators=(0xfffffff0, 20))
                    target = damage.actor_snapshot(poison=0x6b)
                    raw = damage.logical_record(word, selector)
                    n = self.proof.receive(raw, source=before, target=target)
                    expected = bytearray(before)
                    signed_word = word if word < 32768 else word - 65536
                    a, b = 0xfffffff0, 20
                    if selector <= 5:
                        a = (a + signed_word) & 0xffffffff
                        read_rva, write_rva = 0x12cb2d, 0x12cb31
                    elif selector == 9:
                        b = (b + signed_word) & 0xffffffff
                        read_rva, write_rva = 0x12cb3a, 0x12cb3e
                    elif selector == 20:
                        a = signed_word & 0xffffffff
                        read_rva, write_rva = 0x12cb47, 0x12cb4b
                    else:
                        read_rva = write_rva = None
                    struct.pack_into('<2I', expected, 0xb60, a, b)
                    struct.pack_into('<H', expected, 0x2c4, 1)
                    struct.pack_into('<H', expected, 0x4d0, 1)
                    expected[0x62e] = (before[0x62e] & 0x70) | 1
                    expected[0x55c], expected[0x5a2] = 1, selector
                    expected[0x5e8] = self.proof.image[0x171610] if selector == 0 else 0
                    self.assertEqual(bytes(n.vm.mem_read(damage.SOURCE, 0x1000)), bytes(expected))
                    self.assertEqual(bytes(n.vm.mem_read(damage.TARGET, 0x1000)), target)
                    self.assertEqual(bytes(n.vm.mem_read(damage.PACKET, 15)), raw)
                    self.assertEqual(n.stop, 0x1143a1)
                    self.assertEqual(n.vm.reg_read(damage.UC_X86_REG_EAX), 1)
                    for rva in (0x114332, 0x116ae0, 0x117183, 0x12c520, 0x12ca2d, 0x12cb26):
                        self.assertIn(rva, n.visits)
                    accumulator_writes = [w for w in n.writes
                        if damage.SOURCE + 0xb60 <= w[1] < damage.SOURCE + 0xb68]
                    if read_rva is None:
                        self.assertEqual(accumulator_writes, [])
                        self.assertFalse(any(offset == 9 for _, offset, _ in n.record_reads))
                    else:
                        self.assertIn((read_rva, 9, 2), n.record_reads)
                        offset, value = (0xb64, b) if selector == 9 else (0xb60, a)
                        self.assertEqual(accumulator_writes,
                                         [(write_rva, damage.SOURCE + offset, 4, value)])

    def test_native_caller_prefix_derives_result_pointer_and_target(self):
        n = self.proof.receive(damage.logical_record(0xffe2),
                               source=damage.actor_snapshot(accumulators=(10, 20)))
        source = bytes(n.vm.mem_read(damage.SOURCE, 0x1000))
        target = bytes(n.vm.mem_read(damage.TARGET, 0x1000))
        pointer, entity = self.proof.application_prefix(n)
        self.assertEqual((pointer, entity), (damage.SOURCE + 0xb60, damage.TARGET))
        self.assertEqual(n.stop, 0x12b8de)
        self.assertIn(0x12b8a1, n.visits)
        self.assertIn(0x12b8d9, n.visits)
        self.assertEqual(bytes(n.vm.mem_read(damage.SOURCE, 0x1000)), source)
        self.assertEqual(bytes(n.vm.mem_read(damage.TARGET, 0x1000)), target)
        self.assertTrue(all(damage.STACK <= address < damage.STACK + 0x8000
                            for _, address, _, _ in n.writes))

    def test_declared_post_format_live_ins_execute_both_real_scalar_calls(self):
        examples = ((0xffe2, 0, (80, 70, 200, 80)),
                    (0xffe2, 9, (110, 40, 200, 80)),
                    (7, 20, (107, 70, 200, 80)),
                    (7, 7, (110, 70, 200, 80)),
                    (0x8000, 0, (0, 70, 200, 80)),
                    (0x7fff, 9, (110, 80, 200, 80)))
        for word, selector, expected in examples:
            for selected in (False, True):
                with self.subTest(word=word, selector=selector, selected=selected):
                    n = self.proof.receive(damage.logical_record(word, selector),
                        source=damage.actor_snapshot(accumulators=(10, 20)))
                    pointer, entity = self.proof.application_prefix(n)
                    before = bytearray(n.vm.mem_read(damage.TARGET, 0x1000))
                    source = bytes(n.vm.mem_read(damage.SOURCE, 0x1000))
                    result = self.proof.apply_after_format(n, pointer=pointer,
                                                          target=entity, selected=selected)
                    self.assertEqual(result, expected)
                    struct.pack_into('<4I', before, 0xde8, *expected)
                    self.assertEqual(bytes(n.vm.mem_read(damage.TARGET, 0x1000)), bytes(before))
                    self.assertEqual(bytes(n.vm.mem_read(damage.SOURCE, 0x1000)), source)
                    self.assertEqual(n.stop, 0x12bbea)
                    self.assertEqual(n.vm.reg_read(damage.UC_X86_REG_ESP), damage.SP + 16)
                    self.assertEqual(n.get32(damage.DIRTY), 1 if selected else 0xa5a5a5a5)
                    for entry in (0x12bb91, 0x128a70, 0x12bbe5, 0x128ac0):
                        self.assertIn(entry, n.visits)
                    self.assertNotIn(0x147af7, n.visits)

    def test_exact_wrapping_sign_floor_signed_cap_and_dirty_flag(self):
        # Literal expected outputs include counterexamples to ordinary saturation.
        cases = ((100, 0xffffffe2, 200, 70), (10, 0xffffffe2, 200, 0),
                 (100, 100, 150, 150), (0, 0, 0, 0), (200, 0, 100, 100),
                 (0x7fffffff, 1, 0x7fffffff, 0), (0xffffffff, 2, 100, 1),
                 (0, 1, 0xffffffff, 0xffffffff), (0x80000000, 0, 100, 0),
                 (0, 0x80000000, 100, 0), (0x80000000, 0x80000000, 100, 0),
                 (0x7ffffffe, 1, 0x7fffffff, 0x7fffffff), (0, 0, 0xffffffff, 0xffffffff))
        for channel in (0, 1):
            for selected in (False, True):
                for old, delta, cap, expected in cases:
                    with self.subTest(channel=channel, selected=selected, old=old, delta=delta, cap=cap):
                        n = self.proof.direct_scalar(channel, old, delta, cap, selected=selected)
                        address = damage.TARGET + 0xde8 + 4 * channel
                        cap_address = damage.TARGET + 0xdf0 + 4 * channel
                        self.assertEqual(n.get32(address), expected)
                        self.assertEqual(damage.apply_scalar_bits(old, delta, cap), expected)
                        self.assertEqual(n.get32(cap_address), cap)
                        self.assertEqual(n.stop, damage.RETURN)
                        self.assertEqual(n.vm.reg_read(damage.UC_X86_REG_ESP), damage.SP + 12)
                        expected_reads = {address, damage.MANAGER + 0x2dc}
                        if not (old + delta) & 0x80000000:
                            expected_reads.add(cap_address)
                        self.assertEqual({a for _, a, _ in n.data_reads}, expected_reads)
                        self.assertTrue(all(size == 4 for _, _, size in n.data_reads))
                        writes = [(a, size, value) for _, a, size, value in n.writes
                                  if not damage.STACK <= a < damage.STACK + 0x8000]
                        self.assertEqual(writes, [(address, 4, expected)] +
                                         ([(damage.DIRTY, 4, 1)] if selected else []))
                        self.assertEqual(n.get32(damage.DIRTY), 1 if selected else 0xa5a5a5a5)

    def test_counterfactual_packet_value_and_selector_change_computation(self):
        observed = []
        for word, selector in ((0xffe2, 0), (0xffe3, 0), (0xffe2, 9), (0xffe2, 20)):
            n = self.proof.receive(damage.logical_record(word, selector),
                                   source=damage.actor_snapshot(accumulators=(10, 20)))
            pointer, target = self.proof.application_prefix(n)
            observed.append(self.proof.apply_after_format(n, pointer=pointer, target=target)[:2])
        self.assertEqual(observed, [(80, 70), (81, 70), (110, 40), (70, 70)])
        # A guessed sevenfold coefficient and unsigned-WORD interpretation fail.
        self.assertNotEqual(observed[0][0], max(0, 100 + 10 - 30 * 7))
        self.assertNotEqual(observed[0][0], min(200, 100 + 10 + 65506))
        self.assertNotEqual(damage.apply_scalar_bits(0x7fffffff, 1, 0x7fffffff),
                            min(0x7fffffff, 0x7fffffff + 1))

    def test_unread_actor_bytes_do_not_change_qualified_computation(self):
        results = []
        for poison in (0x00, 0x35, 0xa5, 0xff):
            n = self.proof.receive(damage.logical_record(0xffe2),
                source=damage.actor_snapshot(accumulators=(10, 20), poison=poison),
                target=damage.actor_snapshot(poison=poison))
            pointer, target = self.proof.application_prefix(n)
            results.append(self.proof.apply_after_format(n, pointer=pointer, target=target))
        self.assertEqual(results, [(80, 70, 200, 80)] * 4)

    def test_rejects_unqualified_inputs_before_native_execution(self):
        for selector in (True, 0.0, 6, 21, -1):
            with self.assertRaises(ValueError):
                damage.logical_record(1, selector)
        for channel in (True, 0.0, 2, -1):
            with self.assertRaises(ValueError):
                self.proof.direct_scalar(channel, 1, 1, 10)
        record = damage.logical_record(1)
        for raw in (b'', record[:-1], record + b'\0', b'\x84' + record[1:]):
            with self.assertRaises(ValueError):
                self.proof.receive(raw)
        for triple in ((-1, 1, 10), (1, 1 << 32, 10), (1, 1, True)):
            with self.assertRaises(ValueError):
                damage.apply_scalar_bits(*triple)


if __name__ == '__main__':
    unittest.main()
