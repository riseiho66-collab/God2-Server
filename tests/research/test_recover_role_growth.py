"""Real-source evidence checks; no invented positive growth tables/formulas."""
import copy
import json
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.strike_lab import recover_role_growth as growth

REPO = Path(__file__).resolve().parents[2]
CLIENT = REPO.parent / 'God2'
sys.path.insert(0, str(REPO / 'artifacts/tooling/crypto-oracle-python'))


class RoleGrowthRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = growth.build_role_growth(CLIENT)
        cls.decoded = {path: growth.decode_csvz((CLIENT / path).read_bytes())
                       for path in growth.CLIENT_SHA256}

    def assert_row(self, row, plain):
        raw = bytes.fromhex(row['raw_record_hex'])
        offset = row['decoded_offset']
        self.assertEqual(plain[offset:offset + len(raw)], raw)
        self.assertEqual(plain[:offset].count(b'\n') + 1, row['source_line'])
        self.assertEqual(growth.digest(raw), row['sha256'])
        self.assertEqual([f.hex() for f in raw.rstrip(b'\r\n').split(b',')], row['fields_hex'])
        self.assertEqual([bytes.fromhex(f).decode('cp950', errors='backslashreplace')
                          for f in row['fields_hex']], row['fields_cp950_display'])

    def test_all_rows_round_trip_exact_source_bytes(self):
        for table in [*self.result['opaque_tables'].values(),
                      *self.result['display_evidence'].values()]:
            plain = self.decoded[table['source_file']]
            for row in [table['header'], *table['records']]:
                self.assert_row(row, plain)
        for path, rows in self.result['lexical_marker_inventory'].items():
            for row in rows:
                self.assert_row(row, self.decoded[path])

    def test_compressed_and_decoded_identities(self):
        for relative, metadata in self.result['sources'].items():
            raw = (CLIENT / relative).read_bytes()
            self.assertEqual(growth.digest(raw), growth.CLIENT_SHA256[relative])
            self.assertEqual(growth.digest(raw), metadata['sha256'])
            self.assertEqual(len(raw), metadata['size'])
            self.assertEqual(growth.digest(self.decoded[relative]), metadata['decoded_sha256'])
            self.assertEqual(len(self.decoded[relative]), metadata['decoded_size'])
        self.assertEqual(self.result['sources'][growth.GAME]['decoded_size'], 2783008)
        self.assertEqual(self.result['sources'][growth.MESSAGES]['decoded_size'], 110622)

    def test_godlevel_is_four_opaque_labels_not_role_exp(self):
        table = self.result['opaque_tables']['GodLevel']
        self.assertEqual(table['header']['source_line'], 21164)
        self.assertEqual(table['header']['decoded_offset'], 2483449)
        self.assertEqual(table['declared_count'], 4)
        raw = b''.join(bytes.fromhex(row['raw_record_hex']) for row in table['records'])
        self.assertEqual(raw.hex(),
                         'a470a550a6ec2c310d0aa5bfa550a6ec2c320d0a'
                         'b16aa550a6ec2c330d0abbf4a550a6ec2c340d0a')
        self.assertIsNone(table['field_semantics'])
        self.assertFalse(table['runtime_verified'])
        self.assertFalse(table['runtime_eligible'])

    def test_opaque_extra_fields_are_not_dropped(self):
        table = self.result['opaque_tables']['InitSettingMacro']
        self.assertEqual(table['header']['decoded_offset'], 318)
        self.assertEqual(table['declared_count'], 5)
        row = table['records'][2]
        self.assertEqual(row['decoded_offset'], 379)
        self.assertEqual(len(row['fields_hex']), 4)
        self.assertEqual(row['fields_hex'][3], '4e70634d697373696f6ec0c9aed7add3bcc6')
        self.assertIsNone(table['field_semantics'])

    def test_messages_preserve_display_values_without_rule_promotion(self):
        anchors = {('SystemMessage', 330): (405, 16736),
                   ('SystemMessage', 844): (919, 37272),
                   ('SystemMessage', 1746): (1821, 81454),
                   ('ProgramMsg', 162): (2188, 90220),
                   ('ProgramMsg', 927): (2953, 106482)}
        for (section, message_id), location in anchors.items():
            table = self.result['display_evidence'][section]
            row = next(row for row in table['records']
                       if row['fields_hex'][0] == str(message_id).encode().hex())
            self.assertEqual((row['source_line'], row['decoded_offset']), location)
            self.assertFalse(table['runtime_verified'])
            self.assertFalse(table['runtime_eligible'])
            self.assertIsNone(table['trigger_consumer'])
        rows = self.result['display_evidence']['ProgramMsg']['records']
        self.assertIn(b'224', bytes.fromhex(rows[-2]['raw_record_hex']))
        self.assertIsNone(self.result['original_server_rules']['level_cap_and_unlocks']['value'])

    def test_unknowns_survive_json_as_null_not_zero_or_empty_table(self):
        rules = json.loads(growth.serialize(self.result))['original_server_rules']
        expected = {
            'role_exp_requirements', 'exp_total_or_per_level', 'exp_rounding_and_overflow',
            'exp_award_modifiers', 'level_transition', 'level_cap_and_unlocks',
            'rebirth_and_class_modifiers', 'birth_hp_mp_attributes', 'hp_growth', 'mp_growth',
            'automatic_attribute_growth', 'manual_attribute_points',
            'attribute_to_hp_mp_conversion', 'stat_rounding_and_clamping',
        }
        self.assertEqual(set(rules), expected)
        for rule in rules.values():
            self.assertEqual(rule['status'], 'unknown')
            self.assertIsNone(rule['value'])
            self.assertFalse(rule['runtime_verified'])
            self.assertFalse(rule['runtime_eligible'])
        self.assertFalse(self.result['runtime_verified'])
        audit = self.result['native_exp_table_audit']
        self.assertIsNone(audit['rows'])
        self.assertIsNone(audit['growth_consumer_rva'])
        for key in ('single_level_thresholds', 'cumulative_thresholds', 'cap'):
            self.assertEqual(audit[key]['status'], 'unknown')
            self.assertIsNone(audit[key]['value'])
            self.assertTrue(audit[key]['reason'])

    def test_only_current_original_sources_are_read(self):
        original_read = growth.read_source
        allowed = {(CLIENT / relative).resolve() for relative in growth.CLIENT_SHA256}
        allowed.add(growth.DEFAULT_IMAGE.resolve())
        observed = set()

        def current_only(root, relative):
            path = (Path(root) / relative).resolve()
            self.assertIn(path, allowed)
            observed.add(path)
            return original_read(root, relative)

        with patch.object(growth, 'read_source', side_effect=current_only):
            rebuilt = growth.build_role_growth(CLIENT)
        self.assertEqual(observed, allowed)
        self.assertEqual(rebuilt, self.result)

    def test_native_spans_match_pinned_original_image(self):
        raw = growth.DEFAULT_IMAGE.read_bytes()
        evidence = self.result['native_display_evidence']
        self.assertEqual(growth.digest(raw), growth.IMAGE_SHA256)
        self.assertEqual(evidence['source']['sha256'], growth.IMAGE_SHA256)
        for span in evidence['spans'].values():
            data = bytes.fromhex(span['raw_hex'])
            self.assertEqual(raw[span['rva']:span['rva'] + span['size']], data)
            self.assertEqual(span['rva'], span['file_offset'])
            self.assertEqual(growth.digest(data), span['sha256'])
        self.assertEqual(evidence['display_scale']['raw_hex'], '0ad7233c')
        self.assertFalse(evidence['runtime_verified'])
        self.assertFalse(evidence['runtime_eligible'])

    def test_every_pinned_source_rejects_drift(self):
        specs = [(CLIENT, path, sha) for path, sha in growth.CLIENT_SHA256.items()]
        specs.append((growth.DEFAULT_IMAGE.parent, growth.DEFAULT_IMAGE.name, growth.IMAGE_SHA256))
        for root, path, sha in specs:
            with self.subTest(path=path):
                raw = (root / path).read_bytes()
                with patch.object(growth, 'read_source', return_value=raw + b'\n'):
                    with self.assertRaisesRegex(ValueError, 're-audit required'):
                        growth.pinned_source(root, path, sha)

    def test_bad_section_counts_fail_on_mutated_real_source(self):
        original = self.decoded[growth.GAME]
        for replacement in (b'GodLevel,3', b'GodLevel,5', b'GodLevel,-1'):
            with self.subTest(replacement=replacement):
                mutated = original.replace(b'GodLevel,4', replacement, 1)
                with self.assertRaises(ValueError):
                    growth.parse_sections(mutated, ('GodLevel',))
        with self.assertRaises(ValueError):
            growth.parse_sections(original[:2483491], ('GodLevel',))

    def test_missing_source_is_not_unknown_zero(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                growth.build_role_growth(directory)
        with self.assertRaisesRegex(ValueError, 'Source escapes root'):
            growth.pinned_source(CLIENT, '../outside.csvZ', '0' * 64)

    def test_determinism_and_no_shared_mutable_result(self):
        again = growth.build_role_growth(CLIENT)
        self.assertEqual(growth.serialize(self.result), growth.serialize(again))
        again['original_server_rules']['hp_growth']['value'] = 'negative-test-marker'
        self.assertIsNone(self.result['original_server_rules']['hp_growth']['value'])
        self.assertNotIn(str(CLIENT).encode(), growth.serialize(self.result))

    def cli(self, *extra):
        return subprocess.run([
            sys.executable, '-B', '-m', 'tools.strike_lab.recover_role_growth',
            '--client-root', str(CLIENT), *map(str, extra),
        ], cwd=REPO, capture_output=True, timeout=30)

    def test_cli_stdout_write_check_and_reject_forged_rules(self):
        stdout = self.cli()
        self.assertEqual(stdout.returncode, 0, stdout.stderr)
        self.assertEqual(stdout.stdout, growth.serialize(self.result))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'role-growth.json'
            written = self.cli('--output', output)
            self.assertEqual(written.returncode, 0, written.stderr)
            self.assertEqual(output.read_bytes(), stdout.stdout)
            checked = self.cli('--output', output, '--check')
            self.assertEqual(checked.returncode, 0, checked.stderr)
            forged = copy.deepcopy(self.result)
            forged['original_server_rules']['hp_growth']['value'] = 0
            forged['runtime_verified'] = True
            output.write_bytes(growth.serialize(forged))
            before = output.read_bytes()
            rejected = self.cli('--output', output, '--check')
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn(b'Artifact differs', rejected.stderr)
            self.assertEqual(output.read_bytes(), before)

    def test_cli_refuses_source_overwrite_and_incomplete_check(self):
        for target in (CLIENT / growth.GAME, growth.DEFAULT_IMAGE):
            with self.subTest(target=target):
                before = target.read_bytes()
                rejected = self.cli('--output', target)
                self.assertNotEqual(rejected.returncode, 0)
                self.assertIn(b'must not overwrite', rejected.stderr)
                self.assertEqual(target.read_bytes(), before)
        self.assertNotEqual(self.cli('--check').returncode, 0)


class NativeDisplayEvidenceTests(unittest.TestCase):
    """Original instructions, synthetic machine operands; not server growth samples."""

    @classmethod
    def setUpClass(cls):
        from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
        cls.image = growth.DEFAULT_IMAGE.read_bytes()
        if growth.digest(cls.image) != growth.IMAGE_SHA256:
            raise AssertionError('Native image changed')
        cls.vm_factory = staticmethod(lambda: Uc(UC_ARCH_X86, UC_MODE_32))

    def vm(self):
        from unicorn import UC_PROT_READ, UC_PROT_EXEC
        vm = self.vm_factory()
        vm.mem_map(0x400000, (len(self.image) + 4095) & ~4095, UC_PROT_READ | UC_PROT_EXEC)
        vm.mem_write(0x400000, self.image)
        for address, size in ((0x3000000, 0x4000), (0x3100000, 0x1000),
                              (0x3200000, 0x1000), (0x4000000, 0x234000),
                              (0x5000000, 0xb3000), (0x5100000, 0x2000)):
            vm.mem_map(address, size)
        return vm

    def run_to(self, vm, start, stop):
        from unicorn import UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_EIP
        hook = vm.hook_add(UC_HOOK_CODE, lambda uc, a, s, c: uc.emu_stop(),
                           begin=0x400000 + stop, end=0x400000 + stop)
        try:
            vm.emu_start(0x400000 + start, 0x400000 + stop, count=1000, timeout=1000000)
        finally:
            vm.hook_del(hook)
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP), 0x400000 + stop)

    def test_original_s2c22_scalar_stores_preserve_other_actor_bytes(self):
        from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_ESP
        vm = self.vm()
        self.assertEqual(struct.unpack_from('<I', self.image, 0x6b5d4 + 4 * 0x22)[0], 0x469ef0)
        self.assertEqual(self.image[0x1258:0x125e], bytes.fromhex('b819000000c3'))
        payload = bytes(range(24))
        before = bytes([0xa5]) * 0x100
        vm.mem_write(0x3100000, payload)
        vm.mem_write(0x3200000, before)
        vm.mem_write(0x4086888, struct.pack('<I', 0x3200000))
        vm.mem_write(0x3001000, struct.pack('<II', 0, 0x3100000))
        vm.reg_write(UC_X86_REG_ECX, 0x4000000)
        vm.reg_write(UC_X86_REG_ESP, 0x3001000)
        self.run_to(vm, 0xe6b40, 0xe6bd4)
        expected = bytearray(before)
        expected[0x26] = payload[0]
        for source, dest, source_width, dest_width in (
            (16, 0x60, 4, 4), (20, 0x68, 4, 4), (2, 0x90, 2, 2),
            (4, 0x78, 2, 4), (6, 0x7c, 2, 4), (8, 0x80, 2, 4),
            (10, 0x84, 2, 4), (12, 0x58, 2, 2),
        ):
            expected[dest:dest + dest_width] = int.from_bytes(
                payload[source:source + source_width], 'little').to_bytes(dest_width, 'little')
        self.assertEqual(bytes(vm.mem_read(0x3200000, len(before))), bytes(expected))
        self.assertEqual(bytes(vm.mem_read(0x3100000, len(payload))), payload)

    def test_original_percent_display_arithmetic_and_message_162_lookup(self):
        from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESI, UC_X86_REG_ESP
        vm = self.vm()
        scale = struct.unpack_from('<f', self.image, 0x171204)[0]
        # These are WORD boundary probes, never alleged level thresholds or caps.
        for operand in (0, 1, 99, 100, 9999, 10000, 65535):
            vm.mem_write(0x3200058, struct.pack('<H', operand))
            vm.mem_write(0x3001000, struct.pack('<II', 0, 0x3200000))
            vm.reg_write(UC_X86_REG_ECX, 0x4000000)
            vm.reg_write(UC_X86_REG_ESP, 0x3001000)
            self.run_to(vm, 0xe6c90, 0xe6cd1)
            sp = vm.reg_read(UC_X86_REG_ESP)
            self.assertEqual(bytes(vm.mem_read(sp + 0x20, 4)), struct.pack('<f', operand * scale))
        plain = growth.decode_csvz((CLIENT / growth.MESSAGES).read_bytes())
        table = growth.parse_sections(plain, ('ProgramMsg',))['ProgramMsg']
        row = next(row for row in table['records'] if row['fields_hex'][0] == b'162'.hex())
        text = bytes.fromhex(row['fields_hex'][1]) + b'\0'
        vm.mem_write(0x3100000, text)
        vm.mem_write(0x40cff70, struct.pack('<I', 0x5000000))
        vm.mem_write(0x50b2c6c, struct.pack('<H', table['declared_count']))
        vm.mem_write(0x50b2c68, struct.pack('<I', 0x5100000))
        vm.mem_write(0x5100000 + 4 * 161, struct.pack('<I', 0x3100000))
        vm.reg_write(UC_X86_REG_ESI, 0x4000000)
        self.run_to(vm, 0xe6ce1, 0xe6cfe)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 0x3100000)
        self.assertEqual(bytes(vm.mem_read(0x3100000, len(text))), text)


if __name__ == '__main__':
    unittest.main()
