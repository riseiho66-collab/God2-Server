"""Original monster ROM load and independently declared local-default islands."""
import struct
import unittest

from tools.strike_lab import current_monster_resource_initialization as resource
from tools.strike_lab import current_monster_side_initialization as actor
from unicorn import x86_const as reg


class CurrentMonsterResourceInitializationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = []
        for side in (0, 1):
            n = resource.NativeMonsterResourceInitialization(side)
            before_image = bytes(n.vm.mem_read(actor.BASE, 0x170000))
            before_packet = bytes(n.vm.mem_read(actor.PACKET, 45))
            result = n.continue_resource()
            state = (n.vm.reg_read(reg.UC_X86_REG_EIP), n.vm.reg_read(reg.UC_X86_REG_ESP),
                     bytes(n.vm.mem_read(actor.SP - 0x1000, 0x1100)))
            defaults = n.inspect_local_vital_defaults()
            after = (n.vm.reg_read(reg.UC_X86_REG_EIP), n.vm.reg_read(reg.UC_X86_REG_ESP),
                     bytes(n.vm.mem_read(actor.SP - 0x1000, 0x1100)))
            cls.cases.append((n, result, defaults, state, after, before_image, before_packet))

    def test_real_rom_loader_returns_to_same_participant_frame(self):
        for n, result, _, state, _, _, _ in self.cases:
            with self.subTest(side=n.side):
                self.assertIs(n.vm, n.p.vm)
                self.assertEqual(state[:2], (actor.BASE + 0x115fc7, actor.FRAME))
                self.assertEqual(result['source_identity'], (1, 0, 1))
                self.assertEqual(n.u32(actor.NAMES + 0x404), 1)
                self.assertEqual(n.string(n.name_storage), bytes.fromhex(n.prefix['requested_path_hex']))
                self.assertIn((n.monster_asset, 0, len(n.decoded[n.monster_asset])), n.parser_inputs)
                self.assertEqual(n.opens, [n.monster_asset])
                for pc in (0x1206e5, 0x1206ea, 0x120735, 0x120791, 0x1207c9):
                    self.assertEqual(n.continuation_visits[pc], 1)
                self.assertIn(0x29820, n.native_visits)
                self.assertIn(0x1ec0, n.native_visits)
                self.assertIn(0x2a1d0, n.native_visits)
                self.assertGreater(n.u32(resource.BANK + 0x108c), 0)

    def test_rom_load_does_not_turn_reset_fill_into_monster_values(self):
        for n, result, _, _, _, _, _ in self.cases:
            self.assertEqual(result['hp_mp_raw_hex'], 'cd' * 16)
            self.assertEqual(result['original_stat_values_recovered'], 0)
            self.assertEqual(n.actor_writes, [])
            self.assertEqual(bytes(n.vm.mem_read(actor.ACTOR, 0x1000)), n.actor_before)
            self.assertEqual(n.prefix['metadata_hex'][14:16], '00')

    def test_actual_caller_builds_constant_pairs_not_local_stat_lookup(self):
        for n, _, trace, _, _, _, _ in self.cases:
            self.assertEqual(trace['arrays'], [(1, 1), (1, 1)])
            self.assertEqual(tuple(value & 0xff for value in trace['argument_side_slot']), (n.side, 0))
            # Upper argument bits retain poison; native side/slot access is BYTE.
            self.assertNotEqual(trace['argument_side_slot'], (n.side, 0))
            producer = [event for event in trace['writes'] if event[0] == 'producer' and
                        event[1] in (0x1165d9, 0x1165e0, 0x1165e7, 0x1165eb)]
            self.assertEqual(len(producer), 4)
            self.assertTrue(all(event[3:] == (4, '01000000') for event in producer))
            self.assertEqual({event[2] for event in producer},
                             {pointer + delta for pointer in trace['array_pointers'] for delta in (0, 4)})
            self.assertIn(0x116617, trace['producer_visits'])
            self.assertIn(0x12ccd0, trace['producer_visits'])
            self.assertIn(0x11e6e0, trace['producer_visits'])

    def test_side_zero_gets_defaults_side_one_skips_these_stores(self):
        for n, _, trace, _, _, _, _ in self.cases:
            writes = [event for event in trace['writes'] if actor.ACTOR <= event[2] < actor.ACTOR + 0x1000]
            if n.side == 0:
                self.assertEqual(trace['result'], (1, 1, 1, 1))
                self.assertEqual([(x[1], x[2] - actor.ACTOR, x[3], x[4]) for x in writes],
                                 [(pc, off, 4, '01000000') for pc, off in
                                  ((0x12d305, 0xde8), (0x12d312, 0xdec),
                                   (0x12d31a, 0xdf0), (0x12d323, 0xdf4))])
            else:
                self.assertEqual(trace['result'], (0xcdcdcdcd,) * 4)
                self.assertEqual(writes, [])
                self.assertEqual(trace['consumer_visits'], [0x12d219, 0x12d21d, 0x12d21f])

    def test_islands_preserve_pending_continuation_inputs_and_code(self):
        for n, _, _, before, after, image, packet in self.cases:
            self.assertEqual(before, after)
            self.assertEqual(bytes(n.vm.mem_read(actor.PACKET, 45)), packet)
            self.assertEqual(bytes(n.vm.mem_read(actor.BASE, 0x170000)), image)
            with self.assertRaises(ValueError):
                n.continue_resource()
            with self.assertRaises(ValueError):
                n.inspect_local_vital_defaults()
        for side in (-1, 2, True, None):
            with self.assertRaises(ValueError):
                resource.NativeMonsterResourceInitialization(side)


if __name__ == '__main__':
    unittest.main()
