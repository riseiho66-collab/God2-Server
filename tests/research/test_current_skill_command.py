"""Pinned original kinds0/1/3 mask builder -> standalone C++20 parser process.

Only a one-target-per-record shape and bounded structural sequences are recovered.
No server mutation, original process launch, UI, authentication or sockets.
"""
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

import test_current_battle_command as battle


class CurrentSkillCommandTests(unittest.TestCase):
    queued = battle.CurrentBattleCommandTests.queued
    builder = battle.CurrentBattleCommandTests.builder

    def vm(self):
        vm = battle.CurrentBattleCommandTests.vm(self)
        selection_fixture = getattr(self, 'selection_fixture', None)
        if selection_fixture is not None:
            # Skill-local synthetic inputs, installed after the shared fixture setup.
            # Both real accessors use an index into a DWORD pointer table.
            def configure(machine, address, width, data):
                if address != battle.BASE + 0x118e50:
                    return
                index, entry_byte = selection_fixture
                machine.mem_write(battle.BATTLE + 0xa9df73c,
                                  struct.pack('<i', index))
                for count_offset, table_offset in ((0x10, 0xdc), (0x2d64, 0x2d28)):
                    machine.mem_write(battle.SELECTOR + count_offset, struct.pack('<I', 2))
                    machine.mem_write(battle.SELECTOR + table_offset,
                                      struct.pack('<II', battle.SKILL, battle.SKILL + 0x100))
                machine.mem_write(battle.SKILL + 0x100, bytes([entry_byte, 0]))
            vm.hook_add(battle.UC_HOOK_CODE, configure)
        definition=getattr(self,'native_definition',None)
        if definition is not None:
            def source_record(machine,address,width,data):
                if address==battle.BASE+0x118e50:
                    machine.mem_write(battle.SKILL,definition)
            vm.hook_add(battle.UC_HOOK_CODE,source_record)
        return vm

    @classmethod
    def setUpClass(cls):
        cls.image = (battle.ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != battle.ready.IMAGE_SHA:
            raise AssertionError('Pinned current client image changed')
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-skill-test-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable = battle.build_fixture(Path(cls.temp.name),
                                               'test_recovered_skill_command.cpp')

    def decode(self, record):
        output = subprocess.check_output([str(self.executable), '--decode', record.hex()],
                                         text=True, timeout=5).strip()
        return None if output == 'reject' else tuple(map(int, output.split()))

    def decode_sequence(self, records):
        output = subprocess.check_output(
            [str(self.executable), '--decode-sequence', records.hex()],
            text=True, timeout=5).strip()
        return None if output == 'reject' else [tuple(map(int, line.split()))
                                                for line in output.splitlines()]

    def test_cpp_exhaustive_byte_and_mask_boundaries(self):
        output = subprocess.check_output([str(self.executable)], text=True, timeout=10)
        self.assertIn('assertions passed', output)

    def test_native_sequences_survive_formal_world_transport_decoder(self):
        executable = battle.ROOT / 'build-town-visibility/tests/Release/recovered-world-records.exe'
        self.assertTrue(executable.is_file(), 'Build recovered-world-records first')
        for count in range(1, 15):
            targets = tuple((0, 13, 14, 27)[index % 4] for index in range(count))
            records, _, _, _ = self.builder(targets, action=3, skill=True,
                actor=14, context=0x89abcdef, skill_id=0xff)
            result = subprocess.run([str(executable), '--logical', records.hex()],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stdout.strip(), records.hex())
            rejected = subprocess.run([str(executable), '--logical', records[:-1].hex()],
                                      capture_output=True, text=True, timeout=10)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(rejected.stdout, '')

    def test_cpp_guard_pages_and_deterministic_native_sequence_mutations(self):
        for count in range(1, 15):
            with self.subTest(count=count):
                targets = tuple((0, 13, 14, 27, 0)[index % 5] for index in range(count))
                records, _, _, _ = self.builder(targets, action=3, skill=True,
                    modes=(0, 1) if count % 2 else (1, 0), actor=14,
                    context=0x89abcdef, skill_id=0xff)
                output = subprocess.check_output(
                    [str(self.executable), '--guard-sequence', records.hex()],
                    text=True, timeout=30).strip()
                # Each case runs at both the start and end of a read-only page.
                windows = 17 * count * (count + 1) // 2 + count + 1
                bit_flips = count * 17 * 8 if count > 1 else 0
                seam_mutations = (count - 1) * (256 + 6)
                expected = 2 * (windows + 1 + bit_flips + seam_mutations + 256 + 2)
                self.assertEqual(output, f'Guarded sequence checks passed: {expected}')

    def test_native_kind_zero_field_widths_and_unwritten_byte(self):
        for entry_byte in (0, 1, 0x7f, 0x80, 0x9b, 0xff):
            for modes, actor, poison in (((1, 0), 0, 0), ((0, 1), 14, 0xff),
                                        ((1, 1), 0x1234000e, 0xa5)):
                with self.subTest(entry_byte=entry_byte, modes=modes):
                    record, writes, calls, _ = self.builder((27,), action=0x12340003,
                        skill=True, skill_id=entry_byte, actor=actor, modes=modes,
                        poison=poison, context=0x89abcdef)
                    side = int(modes == (0, 1))
                    self.assertEqual(record, bytes([0x35, actor & 255, 3, side, poison]) +
                        struct.pack('<HHII', 0, 0x2000, 0x89abcdef, entry_byte))
                    self.assertEqual(writes, set(range(16)) - {3})
                    self.assertEqual(calls, [0x1156a0,
                        0x11b900 if side else 0x11b8c0, 0x132e0])
                    self.assertEqual(self.decode(record),
                        (actor & 255, 0, side, poison, 0, 0x2000, 0x89abcdef, entry_byte))

    def test_native_selection_index_is_not_emitted_entry_byte(self):
        for modes in ((1, 0), (0, 1)):
            for entry_byte in (0, 0x9b, 0xff):
                for index in (0, 1, -1, 2, 0x9b, 0x100):
                    with self.subTest(modes=modes, entry_byte=entry_byte, index=index):
                        self.selection_fixture = (index, entry_byte)
                        # The shared helper's legacy skill_id name means entry byte 0.
                        records, _, calls, _ = self.builder(action=3, skill=True,
                                                           skill_id=0x11, modes=modes)
                        if index not in (0, 1):
                            self.assertEqual(records, b'')
                            self.assertNotIn(0x132e0, calls)
                            self.assertIsNone(self.decode_sequence(records))
                        else:
                            expected_byte = 0x11 if index == 0 else entry_byte
                            self.assertEqual(records[13:17], bytes([expected_byte, 0, 0, 0]))
                            decoded = self.decode_sequence(records)
                            self.assertIsNotNone(decoded)
                            self.assertEqual(decoded[0][-1], expected_byte)

    def test_native_bounded_sequences_preserve_order_and_duplicates(self):
        for count in range(1, 15):
            for modes in ((1, 0), (0, 1)):
                with self.subTest(count=count, modes=modes):
                    targets = tuple((27, 0, 14, 13, 27)[i % 5] for i in range(count))
                    records, _, _, _ = self.builder(targets, action=3, skill=True,
                        modes=modes, actor=14, context=0x89abcdef, skill_id=0xff)
                    expected = []
                    for index, target in enumerate(targets):
                        masks = [0, 0]
                        masks[target // 14] = 1 << (target % 14)
                        expected.append((14, int(index + 1 < count), int(modes == (0, 1)),
                                         0xa5, *masks, 0x89abcdef, 0xff))
                    self.assertEqual(self.decode_sequence(records), expected)

    def test_cpp_process_negative_sequence_boundaries(self):
        records, _, _, _ = self.builder((0, 14, 27), action=3, skill=True)
        for length in range(len(records)):
            with self.subTest(length=length):
                self.assertIsNone(self.decode_sequence(records[:length]))
        for bad in (records + b'\0', records * 2, b'\x14\0' + records + b'\0'):
            self.assertIsNone(self.decode_sequence(bad))
        for index in range(3):
            bad = bytearray(records)
            bad[index * 17 + 2] ^= 0x80
            self.assertIsNone(self.decode_sequence(bad))
        # Fifteen individually valid records with otherwise correct termination.
        self.assertIsNone(self.decode_sequence(records[:17] * 14 + records[-17:]))
        basic, _, _, _ = self.builder()
        self.assertIsNone(self.decode_sequence(basic))
        for index in range(3):
            for offset, value in ((0, 0x34), (1, 15), (2, 1), (3, 2),
                                  (6, 0x40), (8, 0x80), (14, 1), (15, 1), (16, 1)):
                with self.subTest(index=index, offset=offset):
                    bad = bytearray(records)
                    bad[index * 17 + offset] = value
                    self.assertIsNone(self.decode_sequence(bad))
            for masks in ((0, 0), (3, 0), (1, 1)):
                bad = bytearray(records)
                bad[index * 17 + 5:index * 17 + 9] = struct.pack('<HH', *masks)
                self.assertIsNone(self.decode_sequence(bad))

    def test_cpp_process_sequence_header_consistency_and_opaque_storage(self):
        records, _, _, _ = self.builder((0, 14, 27), action=3, skill=True,
                                        context=0x89abcdef)
        for index in range(3):
            for offset in (1, 3, 9, 10, 11, 12, 13):
                with self.subTest(index=index, offset=offset):
                    bad = bytearray(records)
                    bad[index * 17 + offset] ^= 1
                    self.assertIsNotNone(self.decode(bad[index * 17:(index + 1) * 17]))
                    self.assertIsNone(self.decode_sequence(bad))
        opaque = bytearray(records)
        for index, poison in enumerate((0, 0xa5, 0xff)):
            opaque[index * 17 + 4] = poison
        decoded = self.decode_sequence(opaque)
        self.assertIsNotNone(decoded)
        self.assertEqual([record[3] for record in decoded], [0, 0xa5, 0xff])

    def test_native_target_order_duplicates_and_continuation(self):
        for targets in ((0,), (13,), (14,), (27,), (0, 14, 0), tuple(range(14)),
                        (27,) * 14):
            with self.subTest(targets=targets):
                records, _, calls, _ = self.builder(targets, action=3, skill=True)
                self.assertEqual(len(records), 17 * len(targets))
                self.assertEqual(calls.count(0x132e0), len(targets))
                for index, target in enumerate(targets):
                    continuation = index < len(targets) - 1
                    masks = [0, 0]
                    masks[target // 14] = 1 << (target % 14)
                    record = records[index * 17:(index + 1) * 17]
                    self.assertEqual(record, bytes([0x35, 0, 0x83 if continuation else 3,
                        0, 0xa5]) + struct.pack('<HHII', *masks, 0, 0x9b))
                    self.assertEqual(self.decode(record),
                        (0, int(continuation), 0, 0xa5, *masks, 0, 0x9b))
                if len(targets) > 1:
                    self.assertIsNone(self.decode(records))

    def test_native_empty_signed_count_and_original_guards(self):
        for kwargs in ({'count': 0}, {'count': -1}, {'count': -0x80000000},
                       {'count': 15}, {'count': 0x7fffffff}, {'actor': 15},
                       {'actor': 255}, {'modes': (0, 0)}, {'active': 0},
                       {'connected': 0}, {'skill': False}):
            with self.subTest(kwargs=kwargs):
                arguments = dict(action=3, skill=True)
                arguments.update(kwargs)
                records, _, calls, _ = self.builder(**arguments)
                self.assertEqual(records, b'')
                self.assertNotIn(0x132e0, calls)
                self.assertIsNone(self.decode(records))

    def test_native_revival_kind_and_transport_roundtrip(self):
        executable = battle.ROOT / 'build-town-visibility/tests/Release/recovered-world-records.exe'
        for identifier in (8,9,10):
            for modes in ((1,0),(0,1)):
                for targets in ((1,), (13,), (14,), (27,), (1,14)):
                    records, _, calls, _ = self.builder(targets, action=3, skill=True,
                        skill_id=identifier, skill_kind=3, modes=modes)
                    self.assertEqual(len(records), 17 * len(targets))
                    self.assertEqual(calls.count(0x132e0), len(targets))
                    for offset in range(0,len(records),17):
                        self.assertEqual(records[offset+13:offset+17], bytes((identifier,3,0,0)))
                        self.assertIsNotNone(self.decode(records[offset:offset+17]))
                    result = subprocess.run([str(executable),'--logical',records.hex()],
                                            capture_output=True,text=True,timeout=10)
                    self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                    self.assertEqual(result.stdout.strip(),records.hex())
                    if len(targets)==2:
                        mixed=bytearray(records);mixed[17+14]=0
                        self.assertIsNone(self.decode_sequence(mixed))

    def test_native_mask_kinds_and_context_aliases(self):
        for kind in (1, 2, 3):
            with self.subTest(kind=kind):
                record, _, _, _ = self.builder(action=3, skill=True, skill_kind=kind)
                self.assertEqual(len(record), 17)
                self.assertEqual(struct.unpack_from('<I', record, 13)[0], (kind << 8) | 0x9b)
                self.assertEqual(self.decode(record) is not None,kind in (1,3))
        for kind in (4, 0x80, 0xff):
            records, _, calls, _ = self.builder(action=3, skill=True, skill_kind=kind)
            self.assertEqual(records, b'')
            self.assertNotIn(0x132e0, calls)
        for target in (28, 41, 42, 55):
            with self.subTest(target=target):
                record, _, _, _ = self.builder((target,), action=3, skill=True,
                                              context=0x12348000)
                self.assertEqual(len(record), 17)
                self.assertEqual(record[5:9], bytes(4))
                context = (0x12340000 | (1 << (target - 28))) if target < 42 else (
                    0x8000 | (1 << (target - 42 + 16)))
                self.assertEqual(struct.unpack_from('<I', record, 9)[0], context)
                self.assertIsNone(self.decode(record))

    def test_all_source_mask_definitions_use_native_identity_and_targets(self):
        from tools.strike_lab.import_native_skills import pinned_records
        records=pinned_records(battle.ROOT.parent/'God2');checked=0
        try:
            for row in records:
                kind,identity=row[5:7]
                if kind==2:continue
                self.native_definition=row[4]
                for modes in ((1,0),(0,1)):
                    raw,_,calls,_=self.builder((0,13,14,27),action=3,skill=True,
                        skill_id=identity,skill_kind=kind,modes=modes,context=0x12345678)
                    self.assertEqual(len(raw),68)
                    self.assertEqual(calls.count(0x132e0),4)
                    sequence=self.decode_sequence(raw);self.assertIsNotNone(sequence)
                    for index,target in enumerate((0,13,14,27)):
                        expected=(1<<target,0) if target<14 else (0,1<<(target-14))
                        part=raw[index*17:(index+1)*17]
                        self.assertEqual(struct.unpack_from('<HH',part,5),expected)
                        self.assertEqual(part[13:17],bytes((identity,kind,0,0)))
                checked+=1
        finally:
            if hasattr(self,'native_definition'):del self.native_definition
        self.assertEqual(checked,361)

    def test_cpp_process_negative_record_boundaries(self):
        record, _, _, _ = self.builder(action=3, skill=True)
        for length in range(17):
            self.assertIsNone(self.decode(record[:length]))
        for bad in (record + b'\0', record * 2, b'\x14\0' + record + b'\0'):
            self.assertIsNone(self.decode(bad))
        for offset, values in ((0, (0, 0x34, 0x36)), (1, (15, 255)),
                               (2, (0, 1, 2, 0x17, 0x81, 0xff)), (3, (2, 255)),
                               (14, (2, 4, 255)), (15, (1, 255)), (16, (1, 255))):
            for value in values:
                bad = bytearray(record)
                bad[offset] = value
                self.assertIsNone(self.decode(bad))
        for masks in ((0, 0), (3, 0), (1, 1), (0, 3), (0x4000, 0), (0, 0x8000)):
            bad = bytearray(record)
            bad[5:9] = struct.pack('<HH', *masks)
            self.assertIsNone(self.decode(bad))
        basic, _, _, _ = self.builder()
        self.assertIsNone(self.decode(basic))


if __name__ == '__main__':
    unittest.main()
