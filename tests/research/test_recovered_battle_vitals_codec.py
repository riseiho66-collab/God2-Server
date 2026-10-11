"""Formal C++ vitals codec compared with executed current-client stores."""
from pathlib import Path
import random
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_current_battle_vitals as native
import test_current_battle_side1_scalars as enemy
from tools.strike_lab import current_battle_side1_scalars as side1

EXE = ROOT / 'build/tests/Release/recovered-battle-vitals.exe'


class RecoveredBattleVitalsCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        native.CurrentBattleVitalsTests.setUpClass()
        if not EXE.is_file():
            raise AssertionError('Build recovered-battle-vitals before this suite')

    def batch(self, records):
        output = subprocess.run([str(EXE), '--batch'],
            input='\n'.join(record.hex() for record in records) + '\n',
            text=True, capture_output=True, check=True, timeout=30)
        self.assertEqual(output.stderr, '')
        return output.stdout.splitlines()

    def test_both_sides_all_slots_cpp_values_match_native_stores_or_explicit_ignore(self):
        helper = native.CurrentBattleVitalsTests()
        records, expected = [], []
        values = ((0, 0), (1, 0xffffffff), (0xffffffff, 1),
                  (0x7fffffff, 0x80000000), (0x80000000, 0x7fffffff))
        rng = random.Random(0x86117)
        for position in range(28):
            if position < 14:
                n, vm = helper.prepare(position)
            for kind in (0, 1):
                for current, maximum in values:
                    raw = bytearray(rng.randbytes(17))
                    raw[:3] = bytes((0x86, kind, position))
                    struct.pack_into('<II', raw, 5, maximum, current)
                    raw = bytes(raw)
                    supported = int(kind == 0 or position < 14)
                    if position < 14:
                        self.assertEqual(helper.dispatch(n, vm, raw), 0xe72a6)
                        observed = helper.words(vm, native.ROLE,
                            (0x5c, 0x60) if kind == 0 else (0x64, 0x68))
                    else:
                        before = enemy.actor(handle=0xffff)
                        run = side1.consume(raw, entities={position: before}, displays={}, owner_value=0)
                        self.assertEqual(run.stop, (0x114482, 0x1144a6)[kind])
                        self.assertIsNone(run.fault)
                        actor = bytes(run.vm.mem_read(side1.actor_address(position), len(before)))
                        wanted = bytearray(before)
                        if kind == 0:
                            struct.pack_into('<I', wanted, 0xde8, current)
                            struct.pack_into('<I', wanted, 0xdf0, maximum)
                            observed = tuple(struct.unpack_from('<I', actor, offset)[0]
                                             for offset in (0xde8, 0xdf0))
                        else:
                            self.assertNotIn(0x11e6e0, run.visits)
                            observed = (current, maximum)  # Decoded but explicitly NOT applied.
                        self.assertEqual(actor, bytes(wanted))
                    self.assertEqual(observed, (current, maximum))
                    records.append(raw)
                    expected.append((raw.hex(), kind, position, position // 14, position % 14,
                                     *observed, supported))
        output = self.batch(records)
        self.assertEqual(len(output), 280)
        for line, wanted in zip(output, expected):
            encoded, *fields = line.split()
            self.assertEqual((encoded, *map(int, fields)), wanted)

    def test_bounds_opcode_kind_and_position_rejection(self):
        raw = bytes.fromhex('8600005a5a65000000530000005a5a5a5a')
        records = [raw[:length] for length in range(17)]
        records += [raw + bytes(length) for length in range(1, 49)]
        records += [raw * 2, b'\x86\x00\x00\x00\x00']  # Other direction's close packet.
        for offset, disallowed in ((0, set(range(256)) - {0x86}),
                                   (1, range(2, 256)), (2, range(28, 256))):
            for value in disallowed:
                records.append(raw[:offset] + bytes([value]) + raw[offset + 1:])
        self.assertEqual(self.batch(records), ['reject'] * len(records))


if __name__ == '__main__':
    unittest.main()
