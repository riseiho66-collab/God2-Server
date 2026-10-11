"""C++ wire to original decoder and continuous cold actor; no live client."""
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_cold_world_actor import NativeColdWorldActor
from tools.strike_lab.current_world_actor import MESSAGES, WORLD
import test_current_world_actor as actor_checks
import test_current_world_entry as entry


class CurrentColdWorldActorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entry.CurrentWorldEntryTests.setUpClass()
        cls.transport = entry.CurrentWorldEntryTests()
        cls.native = NativeColdWorldActor()
        cls.body = cls.transport.decode(cls.transport.vm(), cls.transport.wire(217))[3:-1]
        cls.initial = cls.native.initialize(cls.body)

    def test_full_cold_call_uses_original_group_outputs_and_resource_handles(self):
        n = self.native
        pointer = n.call(0x5aa70, 2, 15, this=MESSAGES)
        self.assertEqual(bytes(n.vm.mem_read(pointer, 6)), bytes.fromhex('0f020015028f'))
        self.assertEqual(n.call(0x5a000, 2, 15, this=MESSAGES), 0)
        self.assertEqual(n.bank_visits.count(0x60c60), 1)
        self.assertEqual(n.bank_visits.count(0x616a0), 1)
        self.assertEqual(n.bank_visits.count(0x606d0), 2)
        self.assertEqual(n.tick_calls, [0, 0])
        self.assertNotIn(0x60731, n.bank_visits)
        self.assertEqual(n.next_slot, 8)
        self.assertEqual([item[1] for item in n.parser_inputs], list(range(8)))
        self.assertEqual(n.u32(WORLD+0xa7f2f68), 2)

    def test_cpp_profiles_hit_existing_bank_without_new_loads_or_invented_handles(self):
        n, transport = self.native, self.transport
        before = (list(n.opens), list(n.parser_inputs), len(n.tick_calls))
        for color in range(7):
            identity = (1, 217, 16383)[color % 3]
            x, y = ((17, 13), (18, 12), (0, 0), (32767, 32767))[color % 4]
            wire = bytes.fromhex(subprocess.check_output(
                [str(transport.binary), '--dump', str(identity), str(color),
                 str(6-color), str(x), str(y)], text=True, timeout=5).strip())
            plain = transport.decode(transport.vm(), wire)
            self.assertEqual(plain[:3], b'\x28\0\x2a')
            body, name = plain[3:-1], ('ColdHero'+str(identity)).encode()
            actor = n.initialize(body, name=name)
            actor_checks.CurrentWorldActorTests.assert_actor(
                self, actor, body, name, mount_slot=7)
        self.assertEqual((n.opens, n.parser_inputs, len(n.tick_calls)), before)
        self.assertEqual(n.next_slot, 8)
        self.assertEqual(n.bank_visits.count(0x61ad0), 8)

    def test_unqualified_scene_and_record_fail_before_native_work(self):
        n = self.native
        before = (len(n.visits), len(n.bank_visits), len(n.opens))
        malformed = [self.body[:size] for size in range(36)]+[self.body+b'\0']
        for area, scene in ((2, 0), (7, 13), (0, 15), (16, 9)):
            body = bytearray(self.body)
            struct.pack_into('<H', body, 24, area | (scene << 6))
            malformed.append(bytes(body))
        for body in malformed:
            with self.assertRaises(ValueError):
                n.initialize(body)
        self.assertEqual((len(n.visits), len(n.bank_visits), len(n.opens)), before)


if __name__ == '__main__':
    unittest.main()
