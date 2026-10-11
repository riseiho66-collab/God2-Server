"""No numerical packet supplied: original ROM/reset/create and source limits."""
import struct
import unittest

from tools.strike_lab.current_offline_monster_probe import run_case
from tools.strike_lab import current_monster_side_initialization as actor
from unicorn import x86_const as reg


class CurrentOfflineMonsterProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = [run_case(side) for side in (0, 1)]

    def test_original_reset_and_create_return_to_retained_caller(self):
        for n, report in self.cases:
            with self.subTest(side=n.side):
                self.assertEqual(n.vm.reg_read(reg.UC_X86_REG_EIP), actor.BASE + 0x11602a)
                self.assertEqual(n.vm.reg_read(reg.UC_X86_REG_ESP), actor.FRAME)
                for pc in (0x115fc7, 0x116000, 0x120000, 0x11cfb0, 0x116025,
                           0x1216c0, 0x121630, 0x1e130, 0x12a7c0, 0x12a710,
                           0x1afe0, 0x1e070, 0x1cd40, 0x120970, 0x121ab1):
                    self.assertEqual(n.creation_visits[pc], 1, hex(pc))
                self.assertEqual(n.creation_visits[0x11fde0], 6)
                # REP also visits once with ECX=0; only14 DWORDs are written.
                self.assertEqual(n.creation_visits[0x121a4a], 15)
                metadata_writes = [event for event in n.creation_writes if event[0] == 0x121a4a]
                self.assertEqual([(event[1], event[2]) for event in metadata_writes],
                                 [(offset, 4) for offset in range(0xdb0, 0xde8, 4)])
                self.assertEqual(report['creation']['render_handle'], 0)
                self.assertGreater(report['creation']['sequence_count'], 0)

    def test_vitals_are_native_reset_fill_not_generated_capabilities(self):
        for n, report in self.cases:
            writes = [event for event in n.creation_writes if
                      event[1] < 0xdf8 and event[1] + event[2] > 0xde8]
            self.assertEqual(writes, [(0x11fdfe, offset, 4, 0xcdcdcdcd)
                                     for offset in range(0xde8, 0xdf8, 4)])
            self.assertEqual(n.creation_before[0xde8:0xdf8], b'\xcd' * 16)
            self.assertEqual(n.creation_after[0xde8:0xdf8], b'\xcd' * 16)
            self.assertTrue(all(value is None for value in report['capabilities'].values()))
            self.assertFalse(report['creation']['runtime_eligible'])
            self.assertFalse(report['creation']['live_offline_world_entered'])
            self.assertFalse(report['creation']['full_participant_constructor'])
            self.assertEqual(report['creation']['original_stat_values_recovered'], 0)

    def test_original_metadata_and_resource_binding_not_numerical_authority(self):
        for n, report in self.cases:
            vm = n.vm
            self.assertEqual(bytes(vm.mem_read(actor.PACKET, 45)).hex(),
                             report['explicit_diagnostic_participant_record_hex'])
            self.assertEqual(n.creation_after[0xdb0:0xde8],
                             bytes(vm.mem_read(actor.METADATA, 56)))
            self.assertEqual(struct.unpack_from('<H', n.creation_after, 0x24)[0], 0)
            self.assertEqual(report['native_file_opens'], [n.monster_asset])
            self.assertEqual(report['resource']['source_identity'], (1, 0, 1))
            self.assertFalse(report['default_initializer_separate_islands']['native_monster_values'])

    def test_code_guards_and_single_use(self):
        for n, _ in self.cases:
            self.assertEqual(bytes(n.vm.mem_read(actor.BASE, 0x170000)), n.p.image[:0x170000])
            self.assertEqual(len(set(n.creation_actors)), 168)
            for pointer in n.creation_actors:
                self.assertEqual(bytes(n.vm.mem_read(pointer + actor.ACTOR_SIZE,
                                                     0x1000 - actor.ACTOR_SIZE)),
                                 b'\xa5' * (0x1000 - actor.ACTOR_SIZE))
            with self.assertRaises(ValueError):
                n.continue_actor_creation()


if __name__ == '__main__':
    unittest.main()
