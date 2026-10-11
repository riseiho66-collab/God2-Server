"""Current image/message data -> original field loads -> lossless C++ codec.

Synthetic DWORDs are test sentinels, never recovered awards. No UI, helper
replacement, game function patches, or historical fixture frames are used.
"""
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

import test_recover_monster_experience as native
from test_current_battle_command import build_fixture
from unicorn import UC_HOOK_MEM_READ, UC_PROT_READ, UC_PROT_EXEC, UC_PROT_WRITE
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_ECX, UC_X86_REG_ESI, UC_X86_REG_ESP,
)

exp = native.exp
ROOT, BASE = native.ROOT, exp.BASE
MESSAGE = native.CLIENT / 'Data2/Patch/Comm/message.csvZ'
TEXT = 0x2500000
RECORD = native.PACKET + 4096 - 57
OFFSETS = (5, 9, 13, 53, 49)
VALUES = (0, 1, 0x12345678, 0x7fffffff, 0x80000000, 0xffffffff)


def sentinel(values=VALUES[:5], poison=0):
    record = bytearray((offset * 73 + 19 + poison) & 255 for offset in range(57))
    record[0] = 0x89
    for offset, value in zip(OFFSETS, values):
        struct.pack_into('<I', record, offset, value)
    return bytes(record)


class CurrentBattleExperienceTests(unittest.TestCase):
    execute = native.MonsterExperienceTests.execute

    @classmethod
    def setUpClass(cls):
        cls.image = exp.pinned_read(native.IMAGE, exp.IMAGE_SHA256)
        cls.message_raw = exp.pinned_read(MESSAGE,
            exp.CLIENT_SHA256['Data2/Patch/Comm/message.csvZ'])
        cls.plain = native.decode_csvz(cls.message_raw)
        cls.messages = exp.message_rows(cls.plain)['ProgramMsg']
        cls.evidence = exp.native_evidence(cls.image)
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-battle-experience-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.executable = build_fixture(Path(cls.temp.name),
                                       'test_recovered_battle_experience.cpp')

    def vm(self):
        vm = native.MonsterExperienceTests.vm(self)
        vm.mem_protect(BASE, (len(self.image) + 4095) & ~4095,
                       UC_PROT_READ | UC_PROT_EXEC)
        # Only the original message-pointer globals need writable image data.
        vm.mem_protect(0x5b8000, 4096, UC_PROT_READ | UC_PROT_WRITE)
        return vm

    def codec(self, records):
        result = subprocess.run([str(self.executable), '--batch'],
            input=''.join(record.hex() + '\n' for record in records),
            text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = result.stdout.splitlines()
        self.assertEqual(len(rows), len(records))
        return [None if row == 'reject' else
                (bytes.fromhex(row.split()[0]), tuple(map(int, row.split()[1:])))
                for row in rows]

    def bind_messages(self, vm):
        vm.mem_map(TEXT, 4096)
        vm.mem_write(native.OWNER + 0x28, struct.pack('<I', native.TABLE))
        vm.mem_write(native.TABLE + 0xb2c68,
                     struct.pack('<Ih', native.POINTERS, self.messages['declared_count']))
        pointers = {}
        for index, row in enumerate(self.messages['records']):
            pointer = TEXT + index * 256
            text = bytes.fromhex(row['fields_hex'][-1]) + b'\0'
            self.assertLessEqual(len(text), 256)
            vm.mem_write(pointer, text)
            vm.mem_write(native.POINTERS + (row['id'] - 1) * 4, struct.pack('<I', pointer))
            pointers[row['id']] = pointer
        vm.reg_write(UC_X86_REG_ECX, native.OWNER)
        self.execute(vm, 0x11125f, 0x1112a5)
        self.assertEqual(struct.unpack('<3I', vm.mem_read(0x5b8b50, 12)),
                         tuple(pointers[mid] for mid in (295, 296, 297)))
        return pointers

    def native_arguments(self, record):
        vm = self.vm()
        pointers = self.bind_messages(vm)
        vm.mem_write(RECORD, record)
        vm.mem_protect(native.PACKET, 4096, UC_PROT_READ)
        vm.mem_write(native.OWNER + 0x20, struct.pack('<I', native.TABLE))
        reads = []

        def read(machine, access, address, size, value, data):
            if native.PACKET <= address < native.PACKET + 4096:
                reads.append((address - RECORD, size))

        vm.hook_add(UC_HOOK_MEM_READ, read)
        fields = []
        # Independent entry into each unmodified load block, stopping before
        # its formatter call. No call is skipped inside an emulation segment.
        for slot, (_, offsets, mid, _, start, stop) in enumerate(exp.DISPLAY_FIELDS):
            vm.reg_write(UC_X86_REG_ESP, native.SP)
            vm.reg_write(UC_X86_REG_ESI, native.OWNER)
            vm.reg_write(UC_X86_REG_EBP, RECORD)
            self.execute(vm, start, stop)
            sp = vm.reg_read(UC_X86_REG_ESP)
            args = struct.unpack('<' + 'I' * (4 + len(offsets)),
                                 vm.mem_read(sp, 4 * (4 + len(offsets))))
            self.assertEqual(args[:4], (native.TABLE, 0, slot, pointers[mid]))
            fields.extend(args[4:])
        self.assertEqual(reads, [(5, 4), (9, 4), (53, 4), (13, 4)])
        self.assertEqual(bytes(vm.mem_read(RECORD, 57)), record)
        return tuple(fields)

    def test_cpp_guarded_bounds_all_bytes_and_unsigned_fields(self):
        result = subprocess.run([str(self.executable)], text=True,
                                capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(),
                         'Guarded battle-experience checks passed: 32732')

    def test_current_messages_exact_provenance_and_signed_format(self):
        self.assertEqual(exp.digest(self.plain),
                         '370bd6ed9b4892f57190fc7a8dab14061b3e844b0aa9d0171611a9cbab61b5f8')
        expected = (
            (295, 2321, '\u4e3b\u89d2 \u7372\u5f97\u7d93\u9a57 %d',
             'a8bc3ae180944ce8e660cacbd5333ce7b912d211aed7c58dcaafeb0c04717de5'),
            (296, 2322, '\u795e\u4ed9 \u7372\u5f97\u7d93\u9a57 %d',
             'a3f584300bc9a554027f65bfe331360126e3149eb34fd532db6ded0f1f90f305'),
            (297, 2323, '\u6230\u5bf5/\u6d1e\u5e9c\u7d93\u9a57 %d/%d',
             'f03df3b71f22a057ce3bc1f593fe08fe0a89ec732c46f1165ef1be1fa47a0afc'),
        )
        for row, (mid, line, text, sha) in zip(self.messages['records'], expected):
            self.assertEqual((row['id'], row['line'], row['text_cp950'], row['sha256']),
                             (mid, line, text, sha))
            self.assertEqual(self.plain[row['offset']:row['offset'] + row['size']],
                             bytes.fromhex(row['raw_hex']))
        record = sentinel((0x80000000, 0xffffffff, 0x7fffffff, 0x80000001, 0))
        encoded, decoded = self.codec([record])[0]
        native_fields = self.native_arguments(encoded)
        self.assertEqual(decoded[:4], native_fields)
        signed = tuple(struct.unpack('<i', struct.pack('<I', value))[0]
                       for value in native_fields)
        self.assertEqual(signed, (-2147483648, -1, 2147483647, -2147483647))
        # Model the pinned %d text explicitly; the native formatter is not run.
        self.assertTrue((expected[0][2] % signed[0]).endswith('-2147483648'))
        self.assertTrue((expected[1][2] % signed[1]).endswith('-1'))
        self.assertTrue((expected[2][2] % signed[2:]).endswith('2147483647/-2147483647'))

    def test_original_size_and_receive_queue_dispatches(self):
        vm = self.vm()
        target = struct.unpack_from('<I', self.image, 0x1324 + 4 * 0x89)[0] - BASE
        vm.mem_write(native.SP, struct.pack('<I', BASE + 0x1000))
        self.execute(vm, target, 0x1000)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 57)
        record = sentinel()
        vm.mem_write(RECORD, record)
        vm.reg_write(UC_X86_REG_ESI, RECORD)
        self.execute(vm, 0x1193c4, 0x1195cc)
        vm.reg_write(UC_X86_REG_EBP, RECORD)
        self.execute(vm, 0x114332, 0x114582)
        self.assertEqual(self.evidence['receive_map_index'], 24)
        self.assertEqual(self.evidence['queue_map_index'], 8)
        self.assertEqual(self.codec([record])[0][0], record)

    def test_original_multi_recipient_loads_match_cpp_before_and_after_encode(self):
        records = []
        for poison in (0, 0x5a, 0xff):
            for rotation in range(len(VALUES)):
                amounts = VALUES[rotation:] + VALUES[:rotation]
                records.append(sentinel(amounts, poison))
        for record, (encoded, decoded) in zip(records, self.codec(records)):
            with self.subTest(record=record.hex()):
                self.assertEqual(encoded, record)
                self.assertEqual(decoded, tuple(struct.unpack_from('<I', record, at)[0]
                                                for at in OFFSETS))
                self.assertEqual(self.native_arguments(record), decoded[:4])
                self.assertEqual(self.native_arguments(encoded), decoded[:4])
                self.assertEqual(len(set(decoded[:4])), 4)

    def test_opaque_bytes_do_not_alias_recipient_fields(self):
        original = sentinel()
        records = []
        for offset in (*range(1, 5), *range(17, 49)):
            changed = bytearray(original)
            changed[offset] ^= 0xff
            records.append(bytes(changed))
        wanted = tuple(struct.unpack_from('<I', original, at)[0] for at in OFFSETS)
        for record, (encoded, decoded) in zip(records, self.codec(records)):
            self.assertEqual(encoded, record)
            self.assertEqual(decoded, wanted)
            self.assertEqual(self.native_arguments(encoded), wanted[:4])

    def test_original_selector_load_is_49_not_cave_display_53(self):
        for selector in (*range(5), 0x7fffffff, 0x80000000, 0xffffffff):
            record = sentinel((1, 2, 3, selector ^ 0xffffffff, selector))
            encoded, fields = self.codec([record])[0]
            vm = self.vm()
            vm.mem_write(RECORD, encoded)
            vm.mem_write(native.SP, struct.pack('<II', BASE + 0x1000, RECORD))
            vm.reg_write(UC_X86_REG_ECX, native.OWNER)
            self.execute(vm, 0x118bf0, 0x118bfb)
            self.assertEqual(vm.reg_read(UC_X86_REG_EAX), fields[4])
            self.assertEqual(fields[4], selector)
            self.assertEqual(fields[3], selector ^ 0xffffffff)

    def test_cpp_rejects_nonexact_records_and_every_wrong_opcode(self):
        seed = sentinel()
        rejected = [seed[:size] for size in range(57)]
        rejected += [seed + b'\0', seed * 2, b'\x39\0' + seed + b'\0']
        rejected += [bytes([opcode]) + seed[1:] for opcode in range(256) if opcode != 0x89]
        self.assertEqual(self.codec(rejected), [None] * len(rejected))
        self.assertEqual(self.codec([seed])[0][0], seed)


if __name__ == '__main__':
    unittest.main()
