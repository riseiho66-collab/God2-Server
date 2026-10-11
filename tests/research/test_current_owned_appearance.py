"""Fresh original preview blocks versus actual-source world selection."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_owned_appearance import (
    OwnedAppearance, project_owned_bits, INSTRUCTIONS, MANAGER,
    PROFILE, BANK, RECORDS,
)


def profile(binary, first, second, poison=0xa5):
    value = bytearray([poison]*40)
    value[32], value[33], value[36] = first, binary, second << 5
    return bytes(value)


class CurrentOwnedAppearanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oracle = OwnedAppearance()
        cls.cases = {}
        for binary in (0, 1):
            for first in range(7):
                for second in range(7):
                    p = cls.oracle.preview(profile(binary, first, second))
                    w = cls.oracle.world(p.block, selector=0)
                    cls.cases[binary, first, second] = p, w

    def test_all_98_fresh_blocks_match_all_four_actual_primary_records(self):
        self.assertEqual(len(self.cases), 98)
        for (binary, first, second), (p, w) in self.cases.items():
            with self.subTest(binary=binary, first=first, second=second):
                self.assertEqual(p.block, bytes((binary, first << 5, binary,
                                                second << 5, binary, 0, 0x80 | binary, 0)))
                self.assertEqual(w.block, p.block)
                self.assertEqual(len(p.primary), 4)
                self.assertEqual(p.primary, w.primary)
                expected = (
                    (('r1b000', 158, 'r01b000.romz'), ('r1f002', 601, 'r01f002.romz'),
                     ('r1h000', 26, 'r01w800.romz'), ('r1w800', 292, 'r01w800.romz')),
                    (('r2b000', 182, 'r02b000.romz'), ('r2f002', 611, 'r02f002.romz'),
                     ('r2h000', 92, 'r01w800.romz'), ('r2w800', 377, 'r02w800.romz')),
                )[binary]
                self.assertEqual(tuple((r.key, r.source_line, r.filename) for r in p.primary),
                                 expected)
                self.assertEqual(p.variants, (first, second, 0, 0))
                self.assertEqual(w.variants, p.variants)
                self.assertEqual(w.driver_actions, (0,)*5)
                self.assertEqual([key[1] for key in p.lookups], [0, 2, 1, 2, 3])
                self.assertEqual(p.lookups[:1]+p.lookups[2:],
                                 w.lookups[:1]+w.lookups[2:])
                for item in p.primary+w.primary+p.derived+w.derived:
                    self.assertEqual(item, self.oracle.identity(item.record_pointer))

    def test_real_derived_record_mismatch_is_retained_for_every_binary_one_case(self):
        for (binary, first, second), (p, w) in self.cases.items():
            with self.subTest(binary=binary, first=first, second=second):
                self.assertEqual(p.lookups[1], (0, 2, 0, 0, 0))
                self.assertEqual(w.lookups[1], (binary, 2, 0, 0, 0))
                self.assertEqual(len(p.derived), 1)
                self.assertEqual(len(w.derived), 1)
                a, b = p.derived[0], w.derived[0]
                self.assertEqual((a.key, a.source_line, a.filename, a.derived),
                                 ('r1h000', 26, 'r01w800.romz', 2))
                self.assertEqual((b.key, b.source_line, b.filename, b.derived),
                                 ('r2h000' if binary else 'r1h000',
                                  92 if binary else 26, 'r01w800.romz', 2))
                self.assertEqual(a == b, binary == 0)
                self.assertEqual(p.lookups[2], (binary, 1, 0, 2, 0))
                self.assertEqual(w.lookups[2], p.lookups[2])
                self.assertEqual(p.primary[1].source_line, 611 if binary else 601)

    def test_exact_masks_only_on_source_qualified_fresh_block_domain(self):
        masks = {0: 0x0f, 1: 0xe0, 2: 0x0f, 3: 0xe0, 4: 0x0f, 6: 0x0f}
        # Every source-generated block is tested as both source and target.
        for source, _ in self.cases.values():
            for values, (target, _) in self.cases.items():
                projected = project_owned_bits(source.block, profile(*values))
                self.assertEqual(projected, target.block)
                for i in range(8):
                    self.assertEqual((source.block[i] ^ projected[i]) & (255 ^ masks.get(i, 0)), 0)

    def test_original_construction_ignores_unowned_profile_and_prior_stack_bits(self):
        a = self.oracle
        for binary in (0, 1):
            expected, _ = self.cases[binary, 6, 5]
            for poison in (0, 0x55, 0xaa, 0xff):
                changed = bytearray(profile(binary, 6, 5, poison))
                changed[32] |= poison & 0xf8
                changed[36] |= poison & 0x1f
                observed = a.preview(bytes(changed), poison=poison)
                self.assertEqual(observed, expected)
                self.assertEqual(a.world(observed.block, selector=0, poison=poison),
                                 self.cases[binary, 6, 5][1])
                self.assertEqual(bytes(a.vm.mem_read(PROFILE, 40)), changed)

    def test_offsets_and_source_storage_are_unchanged_original_data(self):
        a = self.oracle
        a.validate_instructions()
        self.assertGreater(len(INSTRUCTIONS), 30)
        self.assertEqual(bytes(a.vm.mem_read(RECORDS, len(a.baseline))), a.baseline)
        self.assertEqual(bytes(a.vm.mem_read(MANAGER+0x682e0, 0x60000)),
                         bytes(a.vm.mem_read(BANK, 0x60000)))
        for pointer in a.by_key.values():
            self.assertEqual(a.record(pointer)[30:32], b'\xff\xff')
        row = a.driver_rows[0]
        self.assertEqual(row[0], '0')
        self.assertEqual(int(row[2]), 0)
        self.assertEqual(struct.unpack('<H', a.vm.mem_read(
            MANAGER+0x682e0+0x121f8+0x12, 2))[0], int(row[2]))

    def test_unqualified_inputs_are_rejected_before_execution(self):
        a = self.oracle
        valid, _ = self.cases[1, 3, 4]
        for selector in (-1, 1, 27, 92, 65535, None, False):
            with self.assertRaises(ValueError):
                a.world(valid.block, selector=selector)
        bad_blocks = [b'', bytes(7), bytes(9)]
        for offset, value in ((0, 2), (1, 1), (1, 0xe0), (2, 0), (3, 0xe0),
                              (4, 0), (5, 1), (6, 1), (7, 1)):
            changed = bytearray(valid.block)
            changed[offset] = value
            bad_blocks.append(bytes(changed))
        for block in bad_blocks:
            with self.assertRaises(ValueError):
                a.world(block, selector=0)
            with self.assertRaises(ValueError):
                project_owned_bits(block, profile(1, 3, 4))
        for value in (b'', bytes(39), bytes(41), profile(2, 0, 0),
                      profile(0, 7, 0), profile(0, 0, 7)):
            with self.assertRaises(ValueError):
                a.preview(value)
        self.assertEqual(bytes(a.vm.mem_read(RECORDS, len(a.baseline))), a.baseline)


if __name__ == '__main__':
    unittest.main()
