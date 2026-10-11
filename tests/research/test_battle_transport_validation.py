"""Black-box C2S batch grammar checks, not session or combat authorization."""
from pathlib import Path
import struct
import subprocess
import unittest


EXECUTABLE = (Path(__file__).resolve().parents[2]
              / 'build/tests/Release/recovered-world-records.exe')
MOVE = bytes.fromhex('2e12000e000300')
TICK = bytes.fromhex('3000')
CLOSE = bytes.fromhex('86efbe0010')


class BattleTransportValidationTests(unittest.TestCase):
    @staticmethod
    def attack(first=0x7f, second=0x7f, action=1):
        return struct.pack('<BBBBBHHII', 0x35, 13, action, 1, 0xa5,
                           first, second, 0x86353025, 0xff00852e)

    def check_batch(self, logical, accepted):
        result = subprocess.run([str(EXECUTABLE), '--logical', logical.hex()],
                                capture_output=True, text=True, timeout=10)
        if accepted:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), logical.hex())
            self.assertEqual(result.stderr, '')
        else:
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(result.stdout, '')
            self.assertIn('Invalid world batch', result.stderr)

    def test_combined_target_count_and_reserved_mask_bits(self):
        for first, second, accepted in (
                (0, 0, True), (0x3fff, 0, True), (0, 0x3fff, True),
                (0x7f, 0x7f, True), (0x7f, 0xff, False),
                (0x3fff, 1, False), (1, 0x3fff, False),
                (0x3fff, 0x3fff, False), (0x4000, 0, False),
                (0, 0x8000, False)):
            with self.subTest(first=first, second=second):
                self.check_batch(MOVE + self.attack(first, second) + CLOSE, accepted)

    def test_unsupported_actions_reject_entire_mixed_batch(self):
        for action in (0, 3, 4, 0x81, 0xff):
            for prefix, suffix in ((MOVE, self.attack() + TICK),
                                   (self.attack() + CLOSE, MOVE)):
                with self.subTest(action=action, prefix=prefix.hex()):
                    self.check_batch(prefix + self.attack(action=action) + suffix, False)
        self.check_batch(MOVE + self.attack() + CLOSE + self.attack() + TICK, True)

    def test_observed_action2_is_typed_but_keeps_structural_bounds(self):
        self.check_batch(MOVE + self.attack(action=2) + TICK, True)
        for masks in ((0x4000,0),(0,0x8000),(0x3fff,1)):
            self.check_batch(MOVE + self.attack(*masks,action=2) + TICK, False)
        for size in range(1,17):
            self.check_batch(MOVE + self.attack(action=2)[:size], False)

    def test_attack_batch_queue_boundary_and_invalid_final_record(self):
        attacks = self.attack() * 150
        self.assertEqual(len(attacks), 2550)
        complete = attacks + CLOSE + CLOSE
        self.assertEqual(len(complete), 0xa00)
        self.check_batch(complete, True)
        self.check_batch(attacks + CLOSE + CLOSE[:-1], False)
        self.check_batch(complete + TICK, False)
        self.check_batch(attacks[:-17] + self.attack(action=3) + CLOSE + CLOSE, False)


if __name__ == '__main__':
    unittest.main()
