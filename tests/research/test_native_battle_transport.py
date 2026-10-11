"""Unchanged current C2S35 producer -> the formal typed world parser.

Native instruction execution and a C++ subprocess, not a live battle session.
"""
import hashlib
import struct
import subprocess
import unittest

import test_current_battle_command as native


class NativeBattleTransportTests(unittest.TestCase):
    vm = native.CurrentBattleCommandTests.vm
    queued = native.CurrentBattleCommandTests.queued
    builder = native.CurrentBattleCommandTests.builder

    @classmethod
    def setUpClass(cls):
        cls.image = (native.ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != native.ready.IMAGE_SHA:
            raise AssertionError('Pinned current client image changed')
        cls.executable = native.ROOT / 'build/tests/Release/recovered-world-records.exe'
        if not cls.executable.is_file():
            raise AssertionError('Build recovered-world-records first')

    def parse(self, logical, accepted=True):
        self.assertLessEqual(len(logical), 0xa00)
        result = subprocess.run([str(self.executable), '--logical', logical.hex()],
                                capture_output=True, text=True, timeout=20)
        if accepted:
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), logical.hex())
        else:
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, '')

    def parse_records(self, records):
        # Each subprocess receives complete records within the native queue cap.
        self.assertTrue(records)
        for record in records:
            self.assertEqual(len(record), 17)
        for start in range(0, len(records), 150):
            self.parse(b''.join(records[start:start + 150]))

    def control(self, targets, actor=0, modes=(0, 0), poison=0xa5, context=0):
        record, writes, calls, _ = self.builder(
            targets, action=0x0b, actor=actor, modes=modes,
            poison=poison, context=context)
        masks = [0, 0]
        for target in targets:
            masks[target // 14] |= 1 << (target % 14)
        side = int(modes == (0, 1))
        expected = bytes((0x35, actor, 0x0b, side, poison)) + struct.pack(
            '<HHI', *masks, context) + bytes((poison,)) * 4
        self.assertEqual(record, expected)
        self.assertEqual(writes, set(range(16)) - {3, 12, 13, 14, 15})
        self.assertEqual(calls, [0x1156a0, 0x11b900 if side else 0x11b8c0, 0x132e0])
        return record

    def test_original_control_all_actors_modes_and_poison(self):
        records = []
        for actor in range(15):
            for modes in ((0, 0), (1, 0), (0, 1), (1, 1)):
                for poison in (0, 0x5a, 0xa5, 0xff):
                    with self.subTest(actor=actor, modes=modes, poison=poison):
                        records.append(self.control((0, 13, 14, 27), actor=actor,
                            modes=modes, poison=poison, context=0x89abcdef))
        self.assertEqual(len(records), 240)
        self.parse_records(records)

    def test_original_control_context_and_two_side_masks(self):
        records = []
        targets_cases = ((), (0,), (13,), (14,), (27,), (0, 0, 27),
                         tuple(range(14)), tuple(range(14, 28)))
        for modes in ((0, 0), (1, 0), (0, 1), (1, 1)):
            for context in (0, 0x80000000, 0xffffffff, 0x86353025):
                for targets in targets_cases:
                    with self.subTest(modes=modes, context=context, targets=targets):
                        records.append(self.control(targets, actor=14, modes=modes,
                                                    poison=0x5a, context=context))
            for first_count in range(15):
                targets = tuple(range(first_count)) + tuple(range(14, 28 - first_count))
                records.append(self.control(targets, actor=14, modes=modes,
                                            poison=0xff, context=0x80000001))
        self.assertEqual(len(records), 188)
        self.parse_records(records)

    def test_control_attack_and_skill_records_keep_order_and_rejection_atomic(self):
        control = self.control((13, 14), actor=14, context=0x80000000)
        attack, _, _, _ = self.builder((0, 27), actor=13, context=0xffffffff)
        tick = b'\x30\0'
        self.parse(tick + attack + control + tick + control + attack)
        self.parse(control * 150 + tick * 5)  # Exactly 0xA00 bytes.
        for length in range(1, 17):
            self.parse(attack + control[:length], False)
        # Observed revival opening02 is structurally known, not general gameplay authorization.
        action2 = control[:2] + b'\x02' + control[3:]
        self.parse(attack + action2 + control)
        for action in (0, 3, 0x81, 0x83, 0x8b, 0xff):
            changed = control[:2] + bytes((action,)) + control[3:]
            self.parse(attack + changed + control, False)
        skill, _, calls, _ = self.builder((0, 14), action=3, skill=True)
        self.assertEqual(len(skill), 34)
        self.assertEqual(skill[2::17], b'\x83\x03')
        self.assertEqual(calls.count(0x132e0), 2)
        for raw_records in (skill[:17], skill[17:], skill):
            self.parse(control + raw_records + attack)
        self.parse(control + skill[:-1], False)

    def test_control_native_guards_still_apply_with_modes_zero(self):
        for kwargs in ({'actor': 15}, {'actor': 255}, {'count': 15},
                       {'active': 0}, {'connected': 0}):
            with self.subTest(kwargs=kwargs):
                record, _, _, _ = self.builder(action=0x0b, modes=(0, 0), **kwargs)
                self.assertEqual(record, b'')
        attack, _, calls, _ = self.builder(action=1, modes=(0, 0))
        self.assertEqual(attack, b'')
        self.assertNotIn(0x132e0, calls)
        self.parse(self.control((0,), modes=(0, 0)))

    def test_original_attack_bytes_survive_typed_batch(self):
        batch = bytearray()
        for actor in range(15):
            for modes in ((1, 0), (0, 1)):
                for poison in (0, 0xa5, 0xff):
                    record, _, calls, _ = self.builder(
                        (0, 13, 14, 27), actor=actor, modes=modes,
                        poison=poison, context=0x89abcdef)
                    self.assertEqual(len(record), 17)
                    self.assertIn(0x132e0, calls)
                    batch.extend(record)
        self.assertEqual(len(batch), 90 * 17)
        self.parse(bytes(batch))
        self.parse(bytes(batch[:-1]), False)
        self.parse(bytes(batch) + b'\xff', False)

    def test_original_skill_and_other_actions_cannot_alias_basic_attack(self):
        absent, _, _, _ = self.builder((0,), action=3, skill=False)
        self.assertEqual(absent, b'')  # Native missing-selection guard queues nothing.
        record, _, _, _ = self.builder((0,), action=3, skill=True, skill_kind=0)
        self.assertEqual(len(record), 17)
        self.parse(record)  # Distinct typed skill, not a basic attack or cast grant.
        attack, _, _, _ = self.builder((0,))
        for length in range(1, 17):
            self.parse(attack + attack[:length], False)
        self.parse(b'\x30\0' + attack + b'\x30\0')


if __name__ == '__main__':
    unittest.main()
