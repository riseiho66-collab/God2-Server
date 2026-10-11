"""Bounded execution of pinned current instructions; synthetic operands only."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.strike_lab import current_role_progression as progression

sys.path.insert(0, str(progression.REPO / 'artifacts/tooling/crypto-oracle-python'))
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX,
    UC_X86_REG_EDI, UC_X86_REG_ESI, UC_X86_REG_ESP)

CLIENT = progression.REPO.parent / 'God2'


class ProgressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = progression.evidence(CLIENT)

    def probe(self, args=()):
        p = progression.NativeProbe()
        p.vm.mem_write(p.STACK, struct.pack('<' + 'I' * (len(args) + 1), 0, *args))
        return p

    def u32(self, p, address):
        return struct.unpack('<I', p.vm.mem_read(address, 4))[0]

    def test_source_allowlist_and_pins(self):
        allowed = {progression.IMAGE.resolve(),
                   *((CLIENT / path).resolve() for path in progression.SOURCES)}
        seen = set()
        original = Path.read_bytes

        def read(path):
            self.assertIn(path.resolve(), allowed)
            seen.add(path.resolve())
            return original(path)

        with patch.object(Path, 'read_bytes', read):
            self.assertEqual(progression.evidence(CLIENT), self.evidence)
        self.assertEqual(seen, allowed)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'drift.bin'
            path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                progression.NativeProbe(path)

    def test_native_edges_lengths_and_unknowns(self):
        raw = progression.IMAGE.read_bytes()
        for span in self.evidence['spans'].values():
            chunk = raw[span['rva']:span['end_rva_exclusive']]
            self.assertEqual(chunk.hex(), span['raw_hex'])
            self.assertEqual(progression.sha(chunk), span['sha256'])
        for opcode, dispatch, length in (('24', 0x69f4d, 17), ('2B', 0x69eb0, 21),
                                          ('2C', 0x69ede, 61), ('9F', 0x69f65, 17)):
            packet = self.evidence['packets'][opcode]
            self.assertEqual(packet['dispatch_rva'], dispatch)
            self.assertEqual(packet['logical_length_including_opcode'], length)
        for call, destination in ((0x69ec2, 0xaa3f0), (0x69ee6, 0xe6600),
                                  (0x69f5b, 0xe71e0), (0x566cd, 0x5a880),
                                  (0xac2fa, 0x149630)):
            self.assertEqual(raw[call], 0xe8)
            self.assertEqual(call + 5 + struct.unpack_from('<i', raw, call + 1)[0], destination)
        for rule in self.evidence['open_original_rules'].values():
            self.assertEqual(rule, {'status': 'open', 'value': None})

    def test_godlevel_category_dispatch_uses_actual_header_and_count(self):
        p = self.probe()
        table = self.evidence['source_schema']['GodLevel']['table']
        header = [bytes.fromhex(x) for x in table['header']['fields_hex']]
        p.vm.mem_write(p.STACK + 0x18, header[0] + b'\0')
        p.vm.mem_write(p.STACK + 0xc, struct.pack('<I', int(header[1])))
        p.vm.reg_write(UC_X86_REG_EDI, p.BANK)
        p.run(0x5668c, 0x566cd)
        self.assertEqual(p.vm.reg_read(UC_X86_REG_ECX), p.BANK)
        self.assertEqual(self.u32(p, p.vm.reg_read(UC_X86_REG_ESP)), 4)

    def test_godlevel_real_fields_read_then_native_slot_copy_and_consumer(self):
        table = self.evidence['source_schema']['GodLevel']['table']
        for ordinal, row in enumerate(table['records']):
            with self.subTest(ordinal=ordinal):
                label, row_id = [bytes.fromhex(x) for x in row['fields_hex']]
                # Native token buffers, after line tokenization; no filesystem/CRT stubs.
                p = self.probe((1, progression.NativeProbe.BODY + 0x100))
                p.vm.mem_write(p.BANK + 8, struct.pack('<H', 2))
                p.vm.mem_write(p.BANK + 0x78, label + b'\0')
                p.vm.mem_write(p.BANK + 0x78 + 0x17c, row_id + b'\0')
                p.vm.reg_write(UC_X86_REG_ECX, p.BANK)
                p.run(0x51b30, 0x51bc4, ((0x51b30, 0x51b43), (0x51b60, 0x51bc4)))
                sp = p.vm.reg_read(UC_X86_REG_ESP)
                self.assertEqual(self.u32(p, sp), p.BANK + 0x78 + 0x17c)
                fmt = self.u32(p, sp + 4)
                self.assertEqual(bytes(p.vm.mem_read(fmt, 3)), b'%d\0')
                # Resume after the decimal reader with the exact source ID.
                # This explicitly excludes sscanf, not a claimed full CSV loader run.
                p.vm.reg_write(UC_X86_REG_ESP, p.STACK)
                p.vm.reg_write(UC_X86_REG_ESI, p.BANK)
                p.vm.mem_write(p.STACK + 0x10, struct.pack('<I', int(row_id)))
                trace = p.run(0x5a8b2, 0x5a8dd,
                              ((0x5a8b2, 0x5a8dd), (0x51ae0, 0x51b2c), (0x51b60, 0x51b98)))
                slot = p.BANK + 0xd2aca + ordinal * 94
                self.assertEqual(bytes(p.vm.mem_read(slot, len(label) + 1)), label + b'\0')
                self.assertTrue(any(a == p.BANK + 0x78 for a, _ in trace['reads']))
                p.vm.mem_write(p.BANK + 0xd2ac8, bytes([table['declared_count']]))
                p.vm.mem_write(p.ACTOR + 0xd0, struct.pack('<I', p.COMPANION))
                p.vm.mem_write(p.BODY, bytes([ordinal]))
                p.vm.mem_write(p.STACK, struct.pack('<II', 0, p.BODY))
                p.vm.reg_write(UC_X86_REG_ESP, p.STACK)
                p.vm.reg_write(UC_X86_REG_ECX, p.UI)
                trace = p.run(0xaa360, 0xaa3c8)
                self.assertEqual(bytes(p.vm.mem_read(p.COMPANION + 0x13, len(label) + 1)), label + b'\0')
                self.assertTrue(any(a == slot for a, _ in trace['reads']))

    def test_category_reader_preserves_original_inclusive_count_guard(self):
        for ordinal in (4, 5):
            p = self.probe((progression.NativeProbe.BODY,))
            p.vm.mem_write(p.BANK + 0xd2ac8, b'\x04')
            p.vm.mem_write(p.BANK + 0xd2aca + 4 * 94, b'guard-probe\0')
            p.vm.mem_write(p.ACTOR + 0xd0, struct.pack('<I', p.COMPANION))
            p.vm.mem_write(p.BODY, bytes([ordinal]))
            p.vm.mem_write(p.COMPANION + 0x13, b'unchanged\0')
            p.run(0xaa360, 0xaa3c8)
            expected = b'guard-probe\0' if ordinal == 4 else b'unchanged\0'
            self.assertEqual(bytes(p.vm.mem_read(p.COMPANION + 0x13, len(expected))), expected)

    def test_s2c2c_copies_modifiers_and_other_stats_without_level_or_exp_write(self):
        p = self.probe((progression.NativeProbe.BODY,))
        payload = bytes((n * 37 + 129) % 256 for n in range(60))
        before = b'\xa5' * 0x100
        p.vm.mem_write(p.BODY, payload)
        p.vm.mem_write(p.ACTOR, before)
        trace = p.run(0xe6600, 0xe66f8)
        expected = bytearray(before)
        for source, target, width in progression.STAT_STORES:
            expected[target:target + width] = payload[source:source + width]
        self.assertEqual(bytes(p.vm.mem_read(p.ACTOR, 0x100)), expected)
        actual = {(a - p.BODY, size) for a, size in trace['reads'] if p.BODY <= a < p.BODY + 60}
        self.assertEqual(actual, {(src, width) for src, _, width in progression.STAT_STORES})
        self.assertEqual(bytes(p.vm.mem_read(p.BODY, 60)), payload)

    def test_modifier_sign_selects_format_does_not_add_to_base(self):
        for modifier in (-32768, -1, 0, 1, 32767):
            p = self.probe()
            p.vm.mem_write(p.ACTOR + 0x78, struct.pack('<I', 4000000000))
            p.vm.mem_write(p.ACTOR + 0x88, struct.pack('<h', modifier))
            p.vm.reg_write(UC_X86_REG_EDI, p.ACTOR)
            p.vm.reg_write(UC_X86_REG_ESI, p.UI)
            p.vm.reg_write(UC_X86_REG_EBX, p.UI + 0xe2170)
            stop = 0xe6e84 if modifier > 0 else 0xe6ec1 if modifier < 0 else 0xe6efc
            p.run(0xe6e61, stop, ((0xe6e61, 0xe6f19),))
            sp = p.vm.reg_read(UC_X86_REG_ESP)
            self.assertEqual(self.u32(p, sp + 16), 4000000000)
            if modifier:
                start, stop = (0xe6e89, 0xe6ea1) if modifier > 0 else (0xe6ec6, 0xe6ede)
                p.vm.reg_write(UC_X86_REG_ESP, p.STACK)
                p.run(start, stop)
                sp = p.vm.reg_read(UC_X86_REG_ESP)
                self.assertEqual(self.u32(p, sp + 16), modifier & 0xffffffff)
                fmt = self.u32(p, sp + 12)
                expected = b'+%d\0' if modifier > 0 else b'%d\0'
                self.assertEqual(bytes(p.vm.mem_read(fmt, len(expected))), expected)
            self.assertEqual(self.u32(p, p.ACTOR + 0x78), 4000000000)

    def test_s2c2b_companion_uses_previously_untraced_body_fields(self):
        p = self.probe((progression.NativeProbe.BODY,))
        payload = bytes(range(20))
        p.vm.mem_write(p.BODY, payload)
        p.vm.mem_write(p.ACTOR + 0xd0, struct.pack('<I', p.COMPANION))
        p.vm.mem_write(p.COMPANION, b'\xa5' * 0x80)
        p.run(0xaa3f0, 0xaa422)
        expected = bytearray(b'\xa5' * 0x80)
        for src, dst, width in ((4, 0x2c, 4), (12, 0x34, 2), (18, 0x28, 2)):
            expected[dst:dst + width] = payload[src:src + width]
        self.assertEqual(bytes(p.vm.mem_read(p.COMPANION, 0x80)), expected)
        p = self.probe((progression.NativeProbe.BODY,))
        trace = p.run(0xaa3f0, 0xaa471)
        self.assertFalse(any(p.BODY <= a < p.BODY + 20 for a, _ in trace['reads']))

    def test_s2c24_derives_companion_hp_loss_but_copies_role_maxima(self):
        cases = ((100, 80, 50, 30), (100, 20, 50, 0), (100, 50, 50, 0),
                 (100, 100, 50, 50), (100, 120, 50, 50),
                 (0xffffffff, 0xfffffffe, 50, 49))
        for old_hp, new_hp, companion_hp, expected_hp in cases:
            p = self.probe((progression.NativeProbe.BODY, 0, 0, 0))
            p.vm.mem_write(p.ACTOR + 0x5c, struct.pack('<I', old_hp))
            p.vm.mem_write(p.ACTOR + 0xd0, struct.pack('<I', p.COMPANION))
            p.vm.mem_write(p.COMPANION + 0x2c, struct.pack('<I', companion_hp))
            p.vm.mem_write(p.BODY, struct.pack('<IIII', new_hp, 77, 900, 800))
            p.vm.mem_write(p.ACTOR + 0x26, b'\xd3')
            p.vm.mem_write(p.ACTOR + 0x58, b'\x34\x12')
            p.run(0xe71e0, 0xe72a6)
            self.assertEqual(self.u32(p, p.COMPANION + 0x2c), expected_hp)
            self.assertEqual(tuple(self.u32(p, p.ACTOR + x) for x in (0x5c, 0x64, 0x60, 0x68)),
                             (new_hp, 77, 900, 800))
            self.assertEqual(bytes(p.vm.mem_read(p.ACTOR + 0x26, 1)), b'\xd3')
            self.assertEqual(bytes(p.vm.mem_read(p.ACTOR + 0x58, 2)), b'\x34\x12')

    def test_s2c2b_then_next_consumer_clamps_unsigned_current_values(self):
        for hp, mp, maximum_hp, maximum_mp in ((120, 60, 100, 50), (80, 20, 100, 50),
                (100, 50, 100, 50), (0xffffffff, 0x80000001, 0x80000000, 0x80000000)):
            p = self.probe((progression.NativeProbe.BODY,))
            p.vm.mem_write(p.BODY, struct.pack('<IIIIHH', hp, 0, mp, 0, 4321, 0))
            p.vm.mem_write(p.ACTOR + 0x60, struct.pack('<I', maximum_hp))
            p.vm.mem_write(p.ACTOR + 0x68, struct.pack('<I', maximum_mp))
            p.run(0xe6390, 0xe63c5)
            self.assertEqual((self.u32(p, p.ACTOR + 0x5c), self.u32(p, p.ACTOR + 0x64)), (hp, mp))
            p.vm.reg_write(UC_X86_REG_ESP, p.STACK)
            p.vm.reg_write(UC_X86_REG_ECX, p.UI)
            p.vm.mem_write(p.STACK, struct.pack('<IIII', 0, p.ACTOR, 0, 0))
            p.run(0xac070, 0xac0b2)
            self.assertEqual((self.u32(p, p.ACTOR + 0x5c), self.u32(p, p.ACTOR + 0x64)),
                             (min(hp, maximum_hp), min(mp, maximum_mp)))
            self.assertEqual(bytes(p.vm.mem_read(p.ACTOR + 0x58, 2)), struct.pack('<H', 4321))

    def test_health_clamp_guards_skip_state_mutation(self):
        for hp_max, mp_max, panel in ((0, 10, 0), (10, 0, 0), (10, 10, -1)):
            p = self.probe((progression.NativeProbe.ACTOR, 0, 0))
            p.vm.mem_write(p.ACTOR + 0x5c, struct.pack('<IIII', 90, hp_max, 80, mp_max))
            p.vm.mem_write(p.UI + 0x232e50, struct.pack('<h', panel))
            before = bytes(p.vm.mem_read(p.ACTOR, 0x100))
            p.run(0xac070, 0xac2ad, ((0xac070, 0xac2ad),))
            self.assertEqual(bytes(p.vm.mem_read(p.ACTOR, 0x100)), before)

    def test_exp_bar_executes_original_float_to_integer_callee(self):
        raw = progression.IMAGE.read_bytes()
        scale = struct.unpack_from('<f', raw, 0x171204)[0]
        for operand in (0, 1, 99, 100, 101, 9999, 10000, 65535):
            p = self.probe((progression.NativeProbe.ACTOR,))
            p.vm.mem_write(p.ACTOR + 0x58, struct.pack('<H', operand))
            before = bytes(p.vm.mem_read(p.ACTOR, 0x100))
            trace = p.run(0xac2c0, 0xac2ff, ((0xac2c0, 0xac2ff), (0x149630, 0x149657)))
            rounded = struct.unpack('<f', struct.pack('<f', operand * scale))[0]
            self.assertEqual(p.vm.reg_read(UC_X86_REG_EAX), int(rounded))
            self.assertIn(0x149649, trace['visited'])
            self.assertEqual(bytes(p.vm.mem_read(p.ACTOR, 0x100)), before)
            actor_reads = {(a - p.ACTOR, size) for a, size in trace['reads'] if p.ACTOR <= a < p.ACTOR + 0x100}
            self.assertEqual(actor_reads, {(0x58, 2)})

    def test_source_message_lookup_binds_health_and_secondary_percent(self):
        records = self.evidence['source_schema']['ProgramMsg']['records']
        for row, start, stop, index in zip(records, (0xac132, 0xac16c, 0xaa4c7),
                                         (0xac153, 0xac190, 0xaa4e8), (162, 163, 164)):
            p = self.probe()
            p.vm.reg_write(UC_X86_REG_ESI, p.UI)
            p.vm.mem_write(p.BANK + 0xb2c6c, struct.pack('<H', 1000))
            p.vm.mem_write(p.BANK + 0xb2c68, struct.pack('<I', p.BODY))
            text = bytes.fromhex(row['fields_hex'][1]) + b'\0'
            p.vm.mem_write(p.BODY + 4 * index, struct.pack('<I', p.COMPANION))
            p.vm.mem_write(p.COMPANION, text)
            p.run(start, stop)
            self.assertEqual(p.vm.reg_read(UC_X86_REG_EAX), p.COMPANION)
            self.assertEqual(bytes(p.vm.mem_read(p.COMPANION, len(text))), text)

    def test_native_bounds_fail_closed(self):
        p = self.probe((progression.NativeProbe.ACTOR,))
        with self.assertRaisesRegex(AssertionError, 'bound'):
            p.run(0xac2c0, 0xac2ff, count=1)
        p = self.probe((progression.NativeProbe.ACTOR,))
        with self.assertRaisesRegex(AssertionError, 'escaped'):
            p.run(0xac2c0, 0xac2ff)


if __name__ == '__main__':
    unittest.main()
