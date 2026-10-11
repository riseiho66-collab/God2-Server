"""Bounded source/consumer evidence, never a monster assignment test."""
import copy
import hashlib
import struct
import unittest
from unittest.mock import patch

from tools.strike_lab import current_monster_skill_element_experience as audit


class CurrentMonsterSkillElementExperienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit.build_report()

    def test_all_source_rows_same_vm_consumers_and_missing_definitions(self):
        expected = {'FightPetSkill': (254, 238, 0), 'NewFightPet2Skill': (255, 203, 50)}
        for name, counts in expected.items():
            table = self.report['tables'][name]
            self.assertEqual(tuple(table[k] for k in ('row_count', 'distinct_pairs', 'without_populated_definition')), counts)
            for ordinal, row in enumerate(table['rows'], 1):
                source = row['source']
                raw = bytes.fromhex(source['raw_record_hex'])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])
                self.assertEqual(row['alias_index'], ordinal)
                self.assertEqual(row['writer']['columns'], [0, 1, 1])
                self.assertEqual(row['writer']['stop_rva'], audit.TABLES[name][2])
                self.assertEqual(row['consumer']['stop_rva'], audit.TABLES[name][-1])
                self.assertEqual(row['consumer']['pair'], row['native_pair'])
                self.assertEqual(len(row['writer']['writes']), 2)
                self.assertEqual([tuple(w[2:]) for w in row['writer']['writes']],
                                 [(1, v) for v in row['native_pair']])
                if row['definition_status'] == 'no_populated_definition':
                    self.assertEqual(row['native_pair'], [0, 0])
                    self.assertEqual(bytes.fromhex(source['fields_hex'][1]), b'SpcA00')
                    self.assertIsNone(row['definition_identity_cross_check_only'])

    def test_section_index_is_not_a_global_skill_id(self):
        first = [self.report['tables'][name]['rows'][0] for name in audit.TABLES]
        self.assertEqual([r['alias_index'] for r in first], [1, 1])
        self.assertEqual([r['native_pair'] for r in first], [[0, 1], [1, 67]])
        self.assertNotEqual(first[0]['source']['decoded_offset'], first[1]['source']['decoded_offset'])

    def test_unknown_fields_remain_null_and_no_catalog_sweep(self):
        proof = self.report['wild_monster_proof']
        self.assertEqual(proof['verified_identity_bound_values'], 0)
        for field in ('skill_assignments', 'elements', 'base_experience'):
            self.assertIsNone(proof[field])
        self.assertFalse(proof['all_monsters_including_bosses_complete'])
        self.assertFalse(self.report['catalog']['recomputed'])
        for table in self.report['tables'].values():
            for row in table['rows']:
                self.assertIsNone(row['monster_identity_join'])
                self.assertIsNone(row['monster_skill_assignment'])
                self.assertFalse(row['runtime_eligible'])

    def test_native_lookup_rejects_invalid_alias_and_uses_low_word(self):
        vm = audit.NativeAliases()
        for name, config in audit.TABLES.items():
            row = self.report['tables'][name]['rows'][0]
            vm.load_row(name, row['source'], 1)
            for alias in (0, config[0] + 1, 65535):
                result = vm.lookup(name, alias)
                self.assertEqual(result['status'], 'native_alias_rejection')
                self.assertEqual(result['outputs'], [0xffffffff, 0xffffffff])
                self.assertFalse(any(vm.array[name] <= r[1] < vm.array[name] + 0x400 for r in result['reads']))
            self.assertEqual(vm.lookup(name, 0xa5000001)['pair'], row['native_pair'])

    def test_source_fields_drive_pair_not_description_or_live_in(self):
        vm = audit.NativeAliases()
        original = self.report['tables']['FightPetSkill']['rows'][0]['source']
        for letter, bank in (('A', 0), ('B', 3), ('C', 2), ('D', 1)):
            row = copy.deepcopy(original)
            row['raw_record_hex'] = f'1,Spc{letter}07,different,opaque\r\n'.encode().hex()
            pair, trace = vm.load_row('FightPetSkill', row, 1, bank_live_in=0xe3)
            self.assertEqual(pair, [bank, 7])
            self.assertEqual(trace['columns'], [0, 1, 1])
            self.assertEqual(vm.lookup('FightPetSkill', 1)['pair'], pair)
        self.assertEqual(bytes(vm.vm.mem_read(vm.array['FightPetSkill'] + 2, 0x3fe)), b'\xa5' * 0x3fe)

    def test_pins_and_modified_executable_fail_closed(self):
        with self.assertRaises(ValueError):
            audit.check_pin(b'changed', audit.GAME_SHA)
        vm = audit.NativeAliases()
        vm.vm.mem_write(vm.BASE + 0xa2880, b'\x90')
        with self.assertRaises(ValueError):
            vm.lookup('FightPetSkill', 1)
        with patch.object(audit, 'GAME_SHA', '0' * 64), self.assertRaises(ValueError):
            audit.sources()

    def test_static_frontiers_are_not_executed_or_promoted(self):
        spans = self.report['spans']
        for key in ('template_lookup', 'template_candidate', 'category_tail', 'dispatch', 'bank_literals'):
            self.assertEqual(spans[key]['authority'], 'static_only')
        image = audit.pinned_image()
        for caller, target in ((0x56813, 0x58920), (0x5685e, 0x58ac0),
                               (0xad9bd, 0x59a60), (0xada15, 0x59a60),
                               (0xa28fd, 0xa9710), (0xa4fe3, 0xa9710)):
            self.assertEqual(image[caller], 0xe8)
            self.assertEqual(caller + 5 + struct.unpack_from('<i', image, caller + 1)[0], target)


if __name__ == '__main__':
    unittest.main()
