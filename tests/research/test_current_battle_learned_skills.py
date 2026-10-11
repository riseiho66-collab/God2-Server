"""Original S2C34 proof; cbspec2 bytes below are a RAW FIXTURE, not native-loaded."""
import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC
from unicorn import x86_const as x86
from tools.strike_lab import current_battle_character_binding as binding
from tools.strike_lab import current_battle_learned_skills as skills

UI, STACK, PACKET, BATTLE = 0x8700000, 0x8600000, 0x8610000, 0x20000000
SP = STACK + 0x2000
CATALOG = BATTLE + skills.CATALOG_OFFSET
RESOURCE = ROOT / 'artifacts/capture_work/host-20260918-1430/client/Data2/Fight/Spg/cbspec2.bin'
RESOURCE_SHA = '7676acd93f164d071f7681a3fe74de94d65892759dbf2e69e3c0f748423d2f51'


def named_row(key):
    # Synthetic branch probe, not a statement of character or skill ownership.
    return bytes((0x30, key)) + (f'Probe{key}'.encode() + b'\0').ljust(16, b'\x7d') + b'\x02'


def packet(key=100, bank=0, entry=1):
    return bytes((0x34, key, bank, entry))


class CurrentBattleLearnedSkillsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = binding.IMAGE.read_bytes()
        cls.resource = RESOURCE.read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != binding.IMAGE_SHA:
            raise AssertionError('Pinned current image changed')
        if hashlib.sha256(cls.resource).hexdigest() != RESOURCE_SHA:
            raise AssertionError('Pinned current cbspec2 source changed')
        if cls.resource[:4] != b'1.03' or len(cls.resource) != 4 + skills.CATALOG_SIZE:
            raise AssertionError('Current raw fixture layout changed')

    def map_poison(self, address, size):
        lo, hi = address & ~4095, (address + size + 4095) & ~4095
        self.vm.mem_map(lo, hi - lo)
        self.vm.mem_write(lo, b'\xa5' * (hi - lo))

    def setUp(self):
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vm.mem_map(binding.BASE, (len(self.image) + 4095) & ~4095,
                        UC_PROT_READ | UC_PROT_EXEC)
        self.vm.mem_write(binding.BASE, self.image)
        for address, size in ((STACK, 0x4000), (PACKET, 4096),
                              (UI + 0x86874, 0x20), (CATALOG, skills.CATALOG_SIZE)):
            self.map_poison(address, size)
        # RAW-FIXTURE BOUNDARY: copy the source payload, not an emulated loader.
        # Main owns 12D3B0 and must supply native-loaded same-VM memory itself.
        self.vm.mem_write(CATALOG, self.resource[4:])
        self.n = binding.NativeBattleCharacterBinding(
            self.vm, root=binding.CHARACTER_ROOT, ui=UI, sp=SP, packet=PACKET)
        self.n.prepare_new_root(b'\xa5' * binding.ROOT_SIZE)
        self.n.reset_rows()
        self.n.bind_packet_source()
        self.n.append_named_row(named_row(100))
        self.s = skills.NativeBattleLearnedSkills(self.n, battle=BATTLE)
        self.s.publish_catalog_pointer()
        self.row = self.n.source + binding.ROWS_OFFSET

    def actor(self):
        return bytes(self.vm.mem_read(self.n.root, binding.ROOT_SIZE))

    def context(self):
        return tuple(self.vm.reg_read(getattr(x86, 'UC_X86_REG_' + name)) for name in
                     ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP', 'ESP', 'EIP', 'EFLAGS'))

    def test_original_publication_exact_footprint_and_context(self):
        self.vm.mem_write(self.n.root + 0xa8, b'\x91' * 4)
        self.vm.mem_write(self.n.root + 0x4504, b'\x92' * 4)
        before = bytearray(self.actor())
        self.vm.reg_write(x86.UC_X86_REG_EAX, 0xabcdef98)
        state = self.context()
        trace = self.s.publish_catalog_pointer()
        before[0xa8:0xac] = bytes(4)
        before[0x4504:0x4508] = struct.pack('<I', CATALOG)
        self.assertEqual(self.actor(), before)
        self.assertEqual(self.context(), state)
        self.assertIn((0x687fe, self.n.root + 0x4504, 4, CATALOG), trace['writes'])
        self.assertEqual(trace['pcs'], [0x687eb, 0x687f1, 0x687fb, 0x687fe])

    def test_actual_nonzero_entries_exact_writes_and_reads_same_vm(self):
        for bank, entry in ((0, 1), (1, 1), (2, 2), (3, 111), (1, 129)):
            count = self.vm.mem_read(self.row + skills.LEARNED_COUNT, 1)[0]
            flag = self.row + skills.LEARNED_FLAGS + count
            self.vm.mem_write(flag, b'\x7c')
            before = bytearray(self.actor())
            self.vm.reg_write(x86.UC_X86_REG_EIP, binding.BASE + 0x1116a4)
            self.vm.reg_write(x86.UC_X86_REG_ESP, SP + 0x900)
            self.vm.reg_write(x86.UC_X86_REG_EFLAGS, 0x602)
            state = self.context()
            trace = self.s.write_learned_skill(packet(bank=bank, entry=entry))
            pointer = CATALOG + bank * skills.BANK_STRIDE + entry * skills.ENTRY_SIZE - 0x6a
            offset = self.row - self.n.root
            before[offset + 0x1f0] = count + 1
            before[offset + 0x1f1 + count] = 0
            struct.pack_into('<I', before, offset + 0x258 + count * 4, pointer)
            self.assertEqual(self.actor(), before)
            self.assertEqual(self.context(), state)
            self.assertEqual(trace['outcome'], 'appended')
            self.assertEqual(trace['stop'], 0xaa7bf)
            self.assertIn(0x69fe7, trace['pcs'])
            self.assertIn(0xaa660, trace['pcs'])
            self.assertNotIn(0xaa7bf, trace['pcs'])
            self.assertIn((0xaa780, self.n.root + 0x4504, 4), trace['reads'])
            self.assertIn((0xaa7a8, self.row + 0x258 + count * 4, 4, pointer), trace['writes'])
            self.assertIn((0xaa7b9, self.row + 0x1f0, 1, count + 1), trace['writes'])
            payload_reads = [(addr - PACKET, size) for _, addr, size in trace['reads']
                             if PACKET <= addr < PACKET + 4]
            self.assertEqual(payload_reads, [(1, 1), (3, 1), (2, 1)])
            self.assertEqual(bytes(self.vm.mem_read(pointer, 110)),
                             self.resource[4 + pointer - CATALOG:4 + pointer - CATALOG + 110])
            self.assertTrue(any(self.vm.mem_read(pointer + 2, 108)))
        self.assertEqual(bytes(self.vm.mem_read(CATALOG, skills.CATALOG_SIZE)), self.resource[4:])

    def test_duplicate_is_original_detection_stopped_before_diagnostic(self):
        for bank, entry in ((0, 1), (1, 1), (0, 2)):
            self.s.write_learned_skill(packet(bank=bank, entry=entry))
        for index, (bank, entry) in enumerate(((0, 1), (1, 1), (0, 2))):
            before, state = self.actor(), self.context()
            trace = self.s.write_learned_skill(packet(bank=bank, entry=entry))
            self.assertEqual(trace['outcome'], 'duplicate')
            self.assertEqual(trace['stop'], 0xaa72b)
            self.assertIn(0xaa70a, trace['pcs'])
            self.assertNotIn(0xaa72b, trace['pcs'])
            self.assertNotIn(0x2b10, trace['pcs'])
            pointer = CATALOG + bank * skills.BANK_STRIDE + 4 + (entry - 1) * 110
            self.assertIn((0xaa6fb, self.row + 0x258 + index * 4, 4), trace['reads'])
            self.assertIn((0xaa6fd, pointer + 1, 1), trace['reads'])
            self.assertIn((0xaa706, pointer, 1), trace['reads'])
            self.assertEqual(self.actor(), before)
            self.assertEqual(self.context(), state)

    def test_compiled_revival_seed_reaches_original_learned_writer(self):
        raw = bytes.fromhex(subprocess.check_output(
            [str(ROOT/'build/tests/Release/battle-revival.exe'), '--seed'],
            text=True, timeout=10).strip())
        self.assertEqual(len(raw), 23)
        self.assertEqual(raw[19:], bytes((0x34, 1, 3, 8)))
        self.n.reset_rows()
        # Explicit name metadata fixture; execute the actual low-key lookup.
        names, metadata = 0x9000000, 0x9200000
        for address, size in ((UI+0xcff70, 4), (names+0xb2d40+4*2801, 4), (metadata, 32)):
            self.map_poison(address, size)
        self.vm.mem_write(UI+0xcff70, struct.pack('<I', names))
        self.vm.mem_write(names+0xb2d40+4*2801, struct.pack('<I', metadata))
        self.vm.mem_write(metadata, bytes(8)+b'RevivalFixture\0')
        row_trace = self.n._packet_stage(raw[:19], 0x30, 19, 0x69f85, 0xaa1b5,
            ((0x69f85, 0x69f92), (0xaa040, 0xaa1b5), (0x59a60, 0x59a7e)))
        self.assertIn(0x59a60, row_trace['pcs'])
        self.assertEqual(bytes(self.vm.mem_read(self.row, 2)), b'\x01\x00')
        trace = self.s.write_learned_skill(raw[19:])
        pointer = CATALOG + 3 * skills.BANK_STRIDE + 4 + 7 * skills.ENTRY_SIZE
        self.assertEqual(trace['outcome'], 'appended')
        self.assertEqual(trace['pointer'], pointer)
        self.assertEqual(bytes(self.vm.mem_read(pointer, 2)), bytes((8, 3)))
        self.assertEqual(self.n.u32(self.row + skills.LEARNED_POINTERS), pointer)
        self.assertEqual(self.vm.mem_read(self.row + skills.LEARNED_COUNT, 1)[0], 1)

    def test_capacity_one_hundred_and_full_skips_without_pointer_reads(self):
        for entry in range(1, 101):
            trace = self.s.write_learned_skill(packet(entry=entry))
            self.assertEqual(trace['outcome'], 'appended')
        self.assertEqual(self.vm.mem_read(self.row + 0x1f0, 1)[0], 100)
        self.assertEqual(self.n.u32(self.row + 0x258 + 99 * 4), CATALOG + 4 + 99 * 110)
        for entry in (1, 101):
            before = self.actor()
            trace = self.s.write_learned_skill(packet(entry=entry))
            self.assertEqual(trace['outcome'], 'full')
            self.assertEqual(trace['stop'], 0x69fec)
            self.assertIn(0xaa6a6, trace['pcs'])
            self.assertNotIn(0xaa6fd, trace['pcs'])
            self.assertEqual(self.actor(), before)

    def test_sixteen_rows_unsigned_key_and_absent_key(self):
        for key in range(101, 116):
            self.n.append_named_row(named_row(key))
        trace = self.s.write_learned_skill(packet(key=115, bank=2, entry=87))
        self.assertEqual(trace['row'], self.row + 15 * binding.ROW_STRIDE)
        self.assertEqual(sum(pc == 0xaa696 for pc in trace['pcs']), 16)
        for key in (0, 99, 128, 255):
            before = self.actor()
            trace = self.s.write_learned_skill(packet(key=key))
            self.assertEqual(trace['outcome'], 'no_matching_row')
            self.assertEqual(trace['stop'], 0x69fec)
            self.assertEqual(self.actor(), before)
        self.n.reset_rows()
        trace = self.s.write_learned_skill(packet())
        self.assertEqual(trace['outcome'], 'no_matching_row')
        self.assertNotIn(0xaa696, trace['pcs'])

    def assert_rejected_unchanged(self, raw, message):
        before, state = self.actor(), self.context()
        scratch = bytes(self.vm.mem_read(PACKET, 4))
        with self.assertRaisesRegex(ValueError, message):
            self.s.write_learned_skill(raw)
        self.assertEqual(self.actor(), before)
        self.assertEqual(self.context(), state)
        self.assertEqual(bytes(self.vm.mem_read(PACKET, 4)), scratch)

    def test_exact_packet_and_catalog_bounds_rejected_before_mutation(self):
        for raw in (b'', b'\x34\x64\0', packet() + b'\0', b'\x35\x64\0\x01', bytearray(packet())):
            self.assert_rejected_unchanged(raw, '4-byte')
        for raw in (packet(entry=0), packet(bank=4), packet(bank=255)):
            self.assert_rejected_unchanged(raw, 'bounds')
        for bank, entry in ((0, 122), (1, 130), (2, 88), (3, 112), (3, 255)):
            self.assert_rejected_unchanged(packet(bank=bank, entry=entry), 'populated')
        self.vm.mem_write(CATALOG + 4, b'\x01\0' + bytes(108))
        self.assert_rejected_unchanged(packet(), 'Nonzero')
        self.vm.mem_write(CATALOG + 4, self.resource[8:118])
        self.vm.mem_write(CATALOG, struct.pack('<I', 257))
        self.assert_rejected_unchanged(packet(), 'populated')

    def test_bad_counts_bindings_and_existing_pointers_rejected(self):
        for addr, raw, message in (
                (self.n.source + binding.COUNT_OFFSET, b'\x11', 'sixteen'),
                (self.row + skills.LEARNED_COUNT, b'\x65', 'one hundred'),
                (UI + 0x86888, bytes(4), 'packet-source'),
                (self.n.root + 0x4504, bytes(4), 'publication')):
            old = bytes(self.vm.mem_read(addr, len(raw)))
            self.vm.mem_write(addr, raw)
            self.assert_rejected_unchanged(packet(), message)
            self.vm.mem_write(addr, old)
        self.s.write_learned_skill(packet())
        for pointer in (0, CATALOG - 1, CATALOG, CATALOG + 5,
                        CATALOG + skills.CATALOG_SIZE, CATALOG + 4 + 121 * 110):
            self.vm.mem_write(self.row + 0x258, struct.pack('<I', pointer))
            self.assert_rejected_unchanged(packet(entry=2), 'pointer|populated')

    def test_ambiguous_rows_are_not_silently_resolved(self):
        self.n.append_named_row(named_row(100))
        self.assert_rejected_unchanged(packet(), 'Ambiguous')

    def test_pinned_dispatch_length_and_modified_code_rejection(self):
        self.assertEqual(struct.unpack_from('<I', self.image, 0x6b5d4 + 0x34 * 4)[0],
                         binding.BASE + 0x69fdf)
        length = struct.unpack_from('<I', self.image, 0x1324 + 0x34 * 4)[0] - binding.BASE
        self.assertEqual(self.image[length:length + 6], b'\xb8\x04\0\0\0\xc3')
        self.vm.mem_write(binding.BASE + 0xaa7a8, b'\x90')
        self.assert_rejected_unchanged(packet(), 'executable bytes changed')
        self.vm.mem_write(binding.BASE + 0x687fe, b'\x90')
        before, state = self.actor(), self.context()
        with self.assertRaisesRegex(ValueError, 'executable bytes changed'):
            self.s.publish_catalog_pointer()
        self.assertEqual(self.actor(), before)
        self.assertEqual(self.context(), state)

    def test_storage_overlap_and_unmapped_catalog_are_rejected(self):
        with patch.object(self.n, 'packet', self.n.root):
            with self.assertRaisesRegex(ValueError, 'overlap'):
                skills.NativeBattleLearnedSkills(self.n, battle=BATTLE)
        with self.assertRaisesRegex(ValueError, 'unmapped'):
            skills.NativeBattleLearnedSkills(self.n, battle=BATTLE + 0x100000)
        with self.assertRaisesRegex(ValueError, '32-bit'):
            skills.NativeBattleLearnedSkills(self.n, battle=2**32)

    def test_guard_failure_restores_cpu_and_removes_hooks(self):
        before, state = self.actor(), self.context()
        with self.assertRaisesRegex(AssertionError, 'Unqualified character-stage write'):
            self.s._run(0x687eb, 0x68804, ((0x687eb, 0x68804),),
                        registers={'ECX': BATTLE, 'EBP': self.n.root}, writable=())
        self.assertEqual(self.context(), state)
        # Failed runs are not transactional; caller discards/requalifies memory.
        # This first forbidden write stores zero into an already-zero field.
        self.assertEqual(self.actor(), before)
        self.assertEqual(self.s.write_learned_skill(packet())['outcome'], 'appended')

    def test_read_instruction_and_execution_bounds_restore_cpu(self):
        before, state = self.actor(), self.context()
        with self.assertRaisesRegex(AssertionError, 'Unqualified learned-skill read'):
            self.s._run(0xaa660, 0xaa6be, ((0xaa660, 0xaa6be),),
                        registers={'ECX': UI + 4}, writable=())
        self.assertEqual(self.context(), state)
        with self.assertRaisesRegex(AssertionError, 'Unqualified character-stage PC'):
            self.s._run(0x687eb, 0x68804, ((0x687eb, 0x687f1),),
                        registers={'ECX': BATTLE, 'EBP': self.n.root}, writable=())
        self.assertEqual(self.context(), state)
        original_start = self.vm.emu_start

        def limited_start(begin, until, *, count, timeout):
            self.assertEqual(count, 30000)
            self.assertEqual(timeout, 1000000)
            return original_start(begin, until, count=1, timeout=timeout)

        with patch.object(self.vm, 'emu_start', limited_start):
            with self.assertRaisesRegex(AssertionError, 'execution bound'):
                self.s.publish_catalog_pointer()
        self.assertEqual(self.context(), state)
        self.assertEqual(self.actor(), before)
        self.assertEqual(self.s.write_learned_skill(packet())['outcome'], 'appended')


if __name__ == '__main__':
    unittest.main()
