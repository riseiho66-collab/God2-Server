"""Current-original evidence and bounded native arithmetic; no game/UI process."""
import copy
import io
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import recover_combat_rules as rules
from tools.strike_lab.omega_assets import decode_csvz


class CurrentCombatRuleInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = rules.build_inventory()

    def test_only_four_current_original_inputs_are_opened(self):
        allowed = {str((rules.CLIENT / p).resolve()) for p in rules.SOURCE_HASHES}
        allowed.add(str(rules.IMAGE.resolve()))
        opened = []
        original = Path.open

        def checked_open(path, mode='r', *args, **kwargs):
            self.assertEqual(mode, 'rb')
            self.assertIn(str(path.resolve()), allowed)
            opened.append(str(path.resolve()))
            return original(path, mode, *args, **kwargs)

        with patch.object(Path, 'open', checked_open):
            rebuilt = rules.build_inventory()
        self.assertEqual(set(opened), allowed)
        self.assertEqual(len(opened), 4)
        self.assertEqual(rebuilt, self.inventory)

    def test_determinism_and_all_server_rules_stay_unknown(self):
        value = self.inventory
        self.assertEqual(rules.serialize(value), rules.serialize(copy.deepcopy(value)))
        self.assertEqual(json.loads(rules.serialize(value)), value)
        self.assertEqual([row['id'] for row in value['rules']], list(rules.RULES))
        for row in value['rules']:
            self.assertEqual(row['status'], 'unknown')
            self.assertIsNone(row['server_formula'])
            self.assertIsNone(row['server_coefficients'])
            self.assertIs(row['runtime_enabled'], False)
        self.assertEqual(value['counts'], {
            'skill_books': 381, 'displayed_mp_costs': 243,
            'card_effects': 1202, 'selection_definitions': 448,
            'native_slices': 9, 'recovered_server_formulas': 0})

    def test_table_bytes_offsets_lines_and_hashes(self):
        for source in (rules.SKILLS, rules.EFFECTS):
            encoded = (rules.CLIENT / source).read_bytes()
            decoded = decode_csvz(encoded)
            self.assertEqual(rules.sha256(encoded), self.inventory['sources'][source]['sha256'])
            self.assertEqual(rules.sha256(decoded), self.inventory['sources'][source]['decoded_sha256'])
            if source == rules.SKILLS:
                table = self.inventory['skill_books']
                rows = [table['header'], *table['definitions']]
                for row in rows:
                    raw = bytes.fromhex(row['raw_record_hex'])
                    offset = row['decoded_offset']
                    self.assertEqual(decoded[offset:offset + len(raw)], raw)
                    self.assertEqual(decoded.splitlines()[row['source_line'] - 1], raw)
                    self.assertEqual(rules.sha256(raw), row['source_record_sha256'])
            else:
                table = self.inventory['card_effects']
                for row in [table['header'], table['marker'], *table['records']]:
                    raw = bytes.fromhex(row['raw_hex'])
                    self.assertEqual(decoded[row['offset']:row['offset'] + row['length']], raw)
                    self.assertEqual(decoded.splitlines()[row['line'] - 1], raw)
                    self.assertEqual(rules.sha256(raw), row['sha256'])

    def test_displayed_cost_is_not_server_cost_or_missing_zero(self):
        rows = self.inventory['skill_books']['definitions']
        first = next(row for row in rows if row['item_id'] == 6501)
        self.assertEqual(first['displayed_mp_cost'], 5)
        self.assertEqual(first['description_claims']['mp_cost']['source_column'], 9)
        self.assertEqual(first['source_line'], 8916)
        self.assertEqual(first['source_record_sha256'],
                         '60ecb5b6d632e5439a280cf53fa2b32755c5dc13b2507b4522b6a74dd1d5c2cb')
        self.assertEqual(sum(row['displayed_mp_cost'] is None for row in rows), 138)
        for row in rows:
            self.assertIsNone(row['server_resource_cost'])
            self.assertEqual(row['authority'], 'description_only')
        # A matching trailing value cannot recover a missing description label.
        decoded = decode_csvz((rules.CLIENT / rules.SKILLS).read_bytes())
        changed = decoded.replace('\u4f7f\u7528\u6d88\u8017 5 MP'.encode('cp950'), b'unknown', 1)
        parsed = rules.parse_skills(changed)
        self.assertNotIn('mp_cost', parsed['definitions'][0]['description_claims'])

    def test_effect_literals_do_not_imply_numeric_column_scaling(self):
        rows = {row['index']: row for row in self.inventory['card_effects']['records']}
        absorption = rows[2]
        self.assertEqual(absorption['line'], 7)
        self.assertEqual(absorption['fields'][3], '50')
        self.assertTrue(absorption['fields'][4].endswith('Hp 5%'))
        hit = rows[302]
        self.assertEqual(hit['line'], 307)
        self.assertEqual(hit['fields'][3], '5')
        self.assertTrue(hit['fields'][4].endswith('5%'))
        self.assertEqual(hit['matched_categories'], ['hit'])
        for row in rows.values():
            self.assertEqual(row['authority'], 'description_only')
            self.assertNotIn('coefficient', row)
            self.assertNotIn('multiplier', row)

    def test_effect_parser_rejects_bad_header_counts_duplicates_and_encoding(self):
        raw = decode_csvz((rules.CLIENT / rules.EFFECTS).read_bytes())
        variants = [raw.replace(b'Index,', b'Unknown,', 1),
                    raw.replace(b'ChangeDollEffectCount,1202', b'ChangeDollEffectCount,1201'),
                    raw.replace(b'ChangeDollEffectCount,1202', b'ChangeDollEffectCount,1203'),
                    raw.replace(b'\r\n2,1,', b'\r\n1,1,', 1),
                    raw + b'1202,0,unknown,0,unknown\r\n',
                    raw.replace(b'GOD_6421', b'\x81', 1)]
        for changed in variants:
            with self.subTest(sha256=rules.sha256(changed)):
                with self.assertRaises(ValueError):
                    rules.parse_effects(changed)

    def test_selection_and_native_bytes_are_exact_not_formula_fields(self):
        raw = (rules.CLIENT / rules.IDENTITIES).read_bytes()
        for row in self.inventory['selection_definitions']:
            record = raw[row['offset']:row['offset'] + row['length']]
            self.assertEqual(row['length'], 110)
            self.assertEqual(record.hex(), row['raw_hex'])
            self.assertEqual(rules.sha256(record), row['sha256'])
            self.assertEqual(record[:2], bytes((row['id'], row['kind'])))
            self.assertEqual(row['authority'], 'identity_only')
        image = rules.IMAGE.read_bytes()
        for row in self.inventory['native_evidence']:
            record = image[row['rva_start']:row['rva_end_exclusive']]
            self.assertEqual(record.hex(), row['raw_hex'])
            self.assertEqual(rules.sha256(record), row['sha256'])

    def test_changed_or_oversized_source_and_changed_native_image_fail_closed(self):
        with patch.object(Path, 'open', return_value=io.BytesIO(b'changed')):
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                rules.read_pinned('unused', rules.IMAGE_SHA256)
        with patch.object(rules, 'MAX_BYTES', 4):
            with patch.object(Path, 'open', return_value=io.BytesIO(b'12345')):
                with self.assertRaisesRegex(ValueError, 'bound'):
                    rules.read_pinned('unused', rules.sha256(b'12345'))
        changed = bytearray(rules.IMAGE.read_bytes())
        changed[0x108ecd] ^= 1
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            rules.native_evidence(changed)


class CurrentNativeDisplayArithmeticTests(unittest.TestCase):
    """Original instructions with synthetic inputs, stopping before UI calls.

    No C++ fixtures, processes, hooks, patched instructions or graphics stubs.
    The second scale block is entered directly with its documented registers.
    This does not exercise receive dispatch or claim live HP/MP observations.
    """
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
        import unicorn
        from unicorn import x86_const
        cls.uc, cls.reg = unicorn, x86_const
        cls.image = rules.read_pinned(rules.IMAGE, rules.IMAGE_SHA256)
        cls.base, cls.stack, cls.manager = 0x400000, 0x3000000, 0x4000000
        cls.sp, cls.return_address = cls.stack + 0x2000, cls.base + 0x1000

    def machine(self):
        uc = self.uc
        vm = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_32)
        vm.mem_map(self.base, (len(self.image) + 4095) & ~4095,
                   uc.UC_PROT_READ | uc.UC_PROT_EXEC)
        vm.mem_write(self.base, self.image)
        vm.mem_map(self.stack, 0x4000)
        vm.reg_write(self.reg.UC_X86_REG_ESP, self.sp)
        vm.reg_write(self.reg.UC_X86_REG_ECX, self.manager)
        vm.reg_write(self.reg.UC_X86_REG_FPCW, 0x037f)
        return vm

    def execute(self, vm, start, stop):
        vm.emu_start(self.base + start, self.base + stop,
                     timeout=1000000, count=512)
        self.assertEqual(vm.reg_read(self.reg.UC_X86_REG_EIP), self.base + stop)

    def test_native_unsigned_clamps_and_handle_addressing(self):
        for handle in (0, 1, 4095, 0x12340001):
            for left, right, max_left, max_right in (
                    (30, 40, 100, 200), (101, 201, 100, 200),
                    (0xffffffff, 0x80000000, 100, 200),
                    (0, 1, 0, 0), (0x80000000, 0xfffffffe, 0xffffffff, 0xffffffff)):
                with self.subTest(handle=handle, values=(left, right, max_left, max_right)):
                    vm = self.machine()
                    record = self.manager + 0x1c + (handle & 0xffff) * 0xa7e0
                    vm.mem_map(record & ~4095, 0xc000)
                    vm.mem_write(record + 0xa7a8, struct.pack('<4I', max_left, max_right, 0, 0))
                    vm.mem_write(self.sp, struct.pack('<4I', self.return_address, handle, left, right))
                    self.execute(vm, 0x108f50, 0x108fa9)
                    actual = struct.unpack('<2I', vm.mem_read(record + 0xa7b0, 8))
                    self.assertEqual(actual, (min(left, max_left), min(right, max_right)))

    def test_native_invalid_handle_returns_without_dereferencing_record(self):
        for handle in (0x1000, 0xffff, 0xabcd1000):
            vm = self.machine()
            vm.mem_write(self.sp, struct.pack('<4I', self.return_address, handle, 1, 1))
            self.execute(vm, 0x108f50, self.return_address - self.base)
            self.assertEqual(vm.reg_read(self.reg.UC_X86_REG_ESP), self.sp + 16)

    def test_native_supplied_divisor_setter_preserves_literal_dwords(self):
        vm = self.machine()
        record = self.manager + 0x1c
        vm.mem_map(self.manager, 0xc000)
        vm.mem_write(self.sp, struct.pack('<4I', self.return_address, 0, 0, 0x80000000))
        self.execute(vm, 0x108fc0, 0x108ff6)
        self.assertEqual(struct.unpack('<2I', vm.mem_read(record + 0xa7a8, 8)), (0, 0x80000000))

    def test_native_both_scale_blocks_and_original_truncation(self):
        for channel in (0, 1):
            for numerator, divisor, width in (
                    (0, 100, 100), (1, 3, 100), (99, 100, 83),
                    (50, 100, 100), (33, 100, -99),
                    (0xffffffff, 0x7fffffff, 100), (50, -100, 100)):
                with self.subTest(channel=channel, values=(numerator, divisor, width)):
                    vm = self.machine()
                    record = self.manager + 0x1c
                    vm.mem_map(self.manager, 0xc000)
                    vm.mem_write(record + 0xa79c, struct.pack('<2h', 1, 2))
                    vm.mem_write(record + 0xa7a4, struct.pack('<2h', width, 12))
                    vm.mem_write(record + 0xa7a8 + channel * 4, struct.pack('<i', divisor))
                    vm.mem_write(record + 0xa7b0 + channel * 4, struct.pack('<I', numerator))
                    vm.mem_write(self.sp, struct.pack('<2I', self.return_address, record))
                    if channel:
                        vm.reg_write(self.reg.UC_X86_REG_ESI, record)
                        vm.reg_write(self.reg.UC_X86_REG_EBP, self.manager)
                        vm.reg_write(self.reg.UC_X86_REG_EBX, 0)
                    self.execute(vm, 0x108ee8 if channel else 0x108e70,
                                 0x108f39 if channel else 0x108ee3)
                    # Integer oracle avoids Python floor semantics for negative quotients.
                    product = numerator * width
                    expected = abs(product) // abs(divisor)
                    if (product < 0) != (divisor < 0):
                        expected = -expected
                    sp = vm.reg_read(self.reg.UC_X86_REG_ESP)
                    handle, rectangle = struct.unpack('<2I', vm.mem_read(sp, 8))
                    actual, = struct.unpack('<I', vm.mem_read(rectangle + 8, 4))
                    self.assertEqual(handle, channel + 1)
                    self.assertEqual(actual, expected & 0xffffffff)
                    self.assertEqual(vm.reg_read(self.reg.UC_X86_REG_FPCW), 0x037f)


if __name__ == '__main__':
    unittest.main()
