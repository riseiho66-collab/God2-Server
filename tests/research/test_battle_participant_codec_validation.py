"""C++ output consumed by unchanged, bounded current-image 83/84 instructions."""
import os
from pathlib import Path
import random
import struct
import subprocess
import unittest

from tests.research import test_current_battle_participant as fixtures
from tools.strike_lab.current_battle_entry import BASE, ROOT, native_length, pinned_image
from tools.strike_lab.current_battle_participant import (
    ACTION_STATE_OFFSET, ACTION_STATE_SIZE, BATTLE, GATE, MANAGER, OUT, consume,
)


class BattleParticipantCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.executable = Path(os.environ.get(
            'GOD2_BATTLE_PARTICIPANT_CODEC_TEST',
            ROOT / 'build/tests/Release/recovered-battle-participant.exe'))
        if not cls.executable.is_file():
            raise AssertionError('Build recovered-battle-participant first, or set '
                                 'GOD2_BATTLE_PARTICIPANT_CODEC_TEST')

    def batch(self, records):
        result = subprocess.run([str(self.executable), '--batch'],
                                input='\n'.join(record.hex() for record in records) + '\n',
                                capture_output=True, text=True, check=True, timeout=30)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), len(records))
        return lines

    def compare_native(self, original, *, stop, **state):
        encoded, = self.batch([original])
        roundtripped = bytes.fromhex(encoded)
        self.assertEqual(roundtripped, original)
        reference = consume(original, **state)
        actual = consume(roundtripped, **state)
        self.assertEqual(reference.stop, stop)
        self.assertEqual(actual.stop, stop)
        # Include every original write (instruction, address, width, raw value),
        # including stack writes, plus full final actor/manager snapshots.
        self.assertEqual(actual.writes, reference.writes)
        self.assertEqual(actual.visits, reference.visits)
        self.assertEqual(actual.packet_reads, reference.packet_reads)
        self.assertEqual(actual.action_reads, reference.action_reads)
        for position in state['entities']:
            self.assertEqual(fixtures.entity(actual, position), fixtures.entity(reference, position))
        self.assertEqual(bytes(actual.vm.mem_read(MANAGER, 0x30a)),
                         bytes(reference.vm.mem_read(MANAGER, 0x30a)))
        for address in (GATE, OUT, BATTLE + 0xa9e9c6c, BATTLE + 0xa9e9c74,
                        BATTLE + 0xa9ea4c4, BATTLE + 0xa9df6c0, BATTLE + 0xa9df6b8):
            self.assertEqual(actual.get32(address), reference.get32(address))
        if 'action_state' in state:
            snapshot = state['action_state']
            self.assertEqual(bytes(actual.vm.mem_read(MANAGER + ACTION_STATE_OFFSET,
                                                     ACTION_STATE_SIZE)),
                             snapshot['manager_tail'])
            self.assertEqual(actual.get32(MANAGER + 0xc), snapshot['manager_0c'])
        self.assertEqual(bytes(actual.vm.mem_read(BASE, len(actual.image))), pinned_image())
        self.assertFalse({0x147af7, 0x11dc00, 0x1b330, 0x12f550} & set(actual.visits))
        return actual

    def test_cli_and_native_lengths(self):
        for make in (fixtures.record83, fixtures.record84):
            record = make()
            result = subprocess.run([str(self.executable), '--roundtrip', record.hex()],
                                    capture_output=True, text=True, check=True, timeout=10)
            self.assertEqual(result.stdout.strip(), record.hex())
            self.assertEqual(native_length(record[0]), 15)

    def test_arbitrary_bytes_are_lossless_without_padding_rules(self):
        rng = random.Random(830120)
        records = []
        for opcode in (0x83, 0x84):
            for _ in range(512):
                record = bytearray(rng.randbytes(15))
                record[0] = opcode
                if opcode == 0x83:
                    record[1] = 1
                record[2 if opcode == 0x83 else 5] = rng.randrange(28)
                records.append(bytes(record))
        self.assertEqual(self.batch(records), [record.hex() for record in records])

    def test_rejects_lengths_opcodes_positions_and_all_other_83_subtypes(self):
        records = []
        for make, position_at in ((fixtures.record83, 2), (fixtures.record84, 5)):
            record = make()
            records += [record[:length] for length in range(15)]
            records += [record + bytes(length) for length in range(1, 16)]
            for position in range(28, 256):
                probe = bytearray(record)
                probe[position_at] = position
                records.append(bytes(probe))
            for opcode in range(256):
                if opcode not in (0x83, 0x84):
                    records.append(bytes([opcode]) + record[1:])
        record = fixtures.record83()
        records += [record[:1] + bytes([subtype]) + record[2:]
                    for subtype in range(256) if subtype != 1]
        self.assertEqual(self.batch(records), ['reject'] * len(records))

    def test_every_source_position_both_target_sides_exact_actor_writes(self):
        for opcode, make in ((0x83, fixtures.record83), (0x84, fixtures.record84)):
            for position in range(28):
                target_position = (position + 14) % 28
                masks = [0xc000, 0xc000]
                masks[target_position // 14] |= 1 << (target_position % 14)
                record = bytearray(make(position=position, masks=masks))
                marker = (position * 97) & 255
                record[3 if opcode == 0x83 else 8] = marker
                if opcode == 0x83:
                    record[4], record[13], record[14] = 0xff, 0xca ^ position, 0xfe ^ position
                before, target = fixtures.actor(active=position % 2), fixtures.actor(ordinal=0xfe)
                state = {'entities': {position: before, target_position: target}}
                if opcode == 0x84:
                    state['metadata'] = fixtures.metadata(0)
                with self.subTest(opcode=opcode, position=position):
                    n = self.compare_native(bytes(record),
                                            stop=0x12c631 if opcode == 0x83 else 0x12c486,
                                            **state)
                    expected = fixtures.action_expected(
                        before, target=target_position, marker=marker,
                        subtype=1 if opcode == 0x83 else 5, ordinal=0xfe)
                    self.assertEqual(fixtures.entity(n, position), expected)
                    expected_target = bytearray(target)
                    if opcode == 0x83:
                        expected_target[0x277] = 0xff
                    else:
                        expected_target[0x1cc:0x1d2] = b'\xff' * 6
                    self.assertEqual(fixtures.entity(n, target_position), expected_target)

    def test_empty_masks_aliasing_and_gate_phase_boundaries(self):
        for opcode, make in ((0x83, fixtures.record83), (0x84, fixtures.record84)):
            for masks in ((0, 0), (0xc000, 0xc000)):
                self.compare_native(make(masks=masks), entities={15: fixtures.actor()},
                                    stop=0x12c631 if opcode == 0x83 else 0x116917)
            self.compare_native(make(), entities={}, gate=-1,
                                stop=0x114384 if opcode == 0x83 else 0x1143f6)
            self.compare_native(make(), entities={}, gate=0x6c, stop=0x1145c0)
            self.compare_native(make(), entities={}, phase_started=False,
                                stop=0x116b14 if opcode == 0x83 else 0x116771)

    def test_83_continuation_raw_words_exact_actor_stores(self):
        for value in (0, 0x7fff, 0x8000, 0xffff):
            record = bytearray(fixtures.record83())
            struct.pack_into('<H', record, 9, value)
            before, target = fixtures.actor(), fixtures.actor(ordinal=2)
            n = self.compare_native(bytes(record), stop=0x12b49c,
                                    entities={15: before, 13: target},
                                    action_state=fixtures.action_state())
            expected = fixtures.action_expected(before, target=13, ordinal=2)
            struct.pack_into('<HH', expected, 0x286, value, 0)
            self.assertEqual(fixtures.entity(n, 15), expected)
            self.assertIn((0x12b3cd, fixtures.entity_address(15) + 0x286, 2, value), n.writes)
            self.assertEqual(fixtures.pending_arguments(n, 3)[2],
                             (value if value < 0x8000 else value - 0x10000) & 0xffffffff)

    def test_84_effect_writes_and_continuation_action_bytes(self):
        for family in (84, 85):
            before, target = fixtures.actor(), fixtures.actor()
            n = self.compare_native(fixtures.record84(), stop=0x12c486,
                                    entities={15: before, 13: target},
                                    metadata=fixtures.metadata(family * 100 + 1),
                                    effect_tables={family: fixtures.effect_table()})
            expected = bytearray(target)
            struct.pack_into('<HHH', expected, 0x1cc, 0x123, 0x234, 0x345)
            self.assertEqual(fixtures.entity(n, 13), expected)
        for action, stop in ((4, 0x12b397), (0x22, 0x12b1f3), (0x24, 0x12b23b)):
            record = bytearray(fixtures.record84())
            record[7] = action
            struct.pack_into('<HH', record, 11, 0x8000, 0xffff)
            before = fixtures.actor()
            n = self.compare_native(bytes(record), stop=stop,
                                    entities={15: before, 13: fixtures.actor()},
                                    metadata=fixtures.metadata(0),
                                    action_state=fixtures.action_state())
            self.assertEqual(fixtures.entity(n, 15),
                             fixtures.action_expected(before, target=13, subtype=5))
            if action != 4:
                args = fixtures.pending_arguments(n, 3 if action == 0x22 else 4)
                self.assertEqual(args[2], 0xffff8000)
                if action == 0x24:
                    self.assertEqual(args[3], 0xffffffff)


if __name__ == '__main__':
    unittest.main()
