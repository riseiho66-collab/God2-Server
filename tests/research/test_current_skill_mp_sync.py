"""Original receive state retained through both MP predicates."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.strike_lab.current_skill_mp_sync import NativeSkillMpSync
from tools.strike_lab.current_skill_mp_gate import ROLE


def packet(mp):
    raw = bytearray(21)
    raw[0] = 0x2b
    struct.pack_into('<I', raw, 1, 300)
    struct.pack_into('<I', raw, 9, mp)
    struct.pack_into('<H', raw, 17, 7)
    return bytes(raw)


class SkillMpSyncTests(unittest.TestCase):
    def setUp(self):
        self.n = NativeSkillMpSync()

    def test_native_current_records_retained_across_receive_and_recheck(self):
        for identity, definition in self.n.definitions.items():
            cost = struct.unpack_from('<H', definition.raw, 0x42)[0]
            for mode in ('indexed', 'selected'):
                with self.subTest(identity=identity, mode=mode):
                    self.n.evaluate(definition.raw, cost + 10, mode=mode)
                    for mp in (cost, max(0, cost - 1), cost + 10):
                        self.assertEqual(self.n.apply_current_vitals(packet(mp)), mp)
                        before = bytes(self.n.vm.mem_read(ROLE, 4096))
                        expected = bool(definition.raw[0x67]) and mp >= cost
                        self.assertEqual(self.n.run_staged_predicate(mode, 0), expected)
                        self.assertEqual(self.n.run_staged_predicate(mode, 0), expected)
                        self.assertEqual(bytes(self.n.vm.mem_read(ROLE, 4096)), before)

    def test_received_absolute_value_not_inferred_cost_subtraction(self):
        raw = bytearray(110)
        raw[0x67] = 1
        struct.pack_into('<H', raw, 0x42, 50)
        self.n.evaluate(bytes(raw), 100)
        for mp in (80, 50, 49, 0, 0xffffffff, 100):
            self.assertEqual(self.n.apply_current_vitals(packet(mp)), mp)
            self.assertEqual(self.n.run_staged_predicate('indexed', 0), mp >= 50)

    def test_invalid_packets(self):
        for raw in (b'', packet(1)[:-1], packet(1) + b'\0', b'\x22' + packet(1)[1:]):
            with self.assertRaises(ValueError):
                self.n.apply_current_vitals(raw)


if __name__ == '__main__':
    unittest.main()
