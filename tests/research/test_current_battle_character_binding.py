"""Current-image-only writer -> same-VM battle selector prefix proof."""
import hashlib
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_PROT_READ, UC_PROT_EXEC
from unicorn import x86_const as x86
from tools.strike_lab import current_battle_character_binding as binding

UI, STACK, PACKET, DESCRIPTOR = 0x8700000, 0x8600000, 0x8610000, 0x8620000
SP, BATTLE = STACK + 0x2000, 0x20000000
SELECTOR = BATTLE + 0xa9dc198


def named_record(key, selected=False):
    # Synthetic boundary probes, never an archive or account fixture.
    return bytes((0x30, (-key if selected else key) & 255)) + (
        f'Probe{key}'.encode('ascii') + b'\0').ljust(16, b'\x7d') + b'\x02'


def status_record(key):
    return (bytes((0x31, key, 7)) + struct.pack('<5H', 1, 257, 4095, 32768, 65535)
            + b'\x71\x72\x73\x74' + struct.pack('<5H', 11, 22, 33, 44, 0x8123)
            + b'\x75\x76')


class CurrentBattleCharacterBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = binding.IMAGE.read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != binding.IMAGE_SHA:
            raise AssertionError('Pinned image changed')

    def map_poison(self, address, size):
        lo, hi = address & ~4095, (address + size + 4095) & ~4095
        for page in range(lo, hi, 4096):
            if not any(a <= page <= z for a, z, _ in self.vm.mem_regions()):
                self.vm.mem_map(page, 4096)
                self.vm.mem_write(page, b'\xa5' * 4096)

    def setUp(self):
        self.vm = Uc(UC_ARCH_X86, UC_MODE_32)
        self.vm.mem_map(binding.BASE, (len(self.image) + 4095) & ~4095,
                        UC_PROT_READ | UC_PROT_EXEC)
        self.vm.mem_write(binding.BASE, self.image)
        for address, size in ((STACK, 0x4000), (PACKET, 4096), (DESCRIPTOR, 4096),
                              (UI + 0x86874, 0x20), (BATTLE, 4096),
                              (SELECTOR, 0x351c), (BATTLE + 0xa9df744, 2)):
            self.map_poison(address, size)
        self.n = binding.NativeBattleCharacterBinding(
            self.vm, root=binding.CHARACTER_ROOT, ui=UI, sp=SP, packet=PACKET)
        self.before = b'\xa5' * binding.ROOT_SIZE
        self.n.prepare_new_root(self.before)

    def actor(self):
        return bytes(self.vm.mem_read(self.n.root, binding.ROOT_SIZE))

    def prepare_rows(self, count=16):
        reset = self.n.reset_rows()
        self.n.bind_packet_source()
        for index in range(count):
            self.n.append_named_row(named_record(100 + index, selected=index == count - 1))
            self.n.write_row_scalars(status_record(100 + index))
        self.n.write_role_scalars(b'\x22' + bytes(range(1, 25)))
        return reset

    def test_original_reset_has_exact_footprint_and_preserves_unknown_stats(self):
        trace = self.n.reset_rows()
        expected = bytearray(self.before)
        expected[0x15f] = 255
        expected[0x160:0x165] = bytes(5)
        expected[0x168:0x4028] = bytes(0x3ec0)
        self.assertEqual(self.actor(), expected)
        self.assertIn(0x68135, trace['pcs'])
        self.assertIn(0x6813b, trace['pcs'])
        self.assertEqual(sum(w[2] for w in trace['writes'] if w[0] == 0x68148), 0x3ec0)
        self.assertNotIn(0x97fe0, trace['pcs'])

    def test_original_packet_source_publication_derives_root_plus_90(self):
        derive, publish = self.n.bind_packet_source()
        self.assertEqual(derive['registers']['EDI'], self.n.root + 0x90)
        self.assertEqual(self.n.u32(UI + 0x86888), self.n.source)
        self.assertIn((0xe7cab, UI + 0x86888, 4, self.n.source), publish['writes'])
        self.assertEqual(self.actor(), self.before)

    def test_s2c22_is_scalar_only_and_cannot_supply_count_selection_or_rows(self):
        self.n.bind_packet_source()
        raw = b'\x22' + bytes(range(1, 25))
        trace = self.n.write_role_scalars(raw)
        expected = bytearray(self.before)
        expected[0x90 + 0x26] = raw[1]
        for src, dst, width, widened in ((17, 0x60, 4, 4), (21, 0x68, 4, 4),
                (3, 0x90, 2, 2), (5, 0x78, 2, 4), (7, 0x7c, 2, 4),
                (9, 0x80, 2, 4), (11, 0x84, 2, 4), (13, 0x58, 2, 2)):
            expected[0x90 + dst:0x90 + dst + widened] = int.from_bytes(
                raw[src:src + width], 'little').to_bytes(widened, 'little')
        self.assertEqual(self.actor(), expected)
        self.assertEqual(self.actor()[0x15f:0x4028], self.before[0x15f:0x4028])
        self.assertNotIn(0xe6db0, trace['pcs'])

    def test_s2c2b_exact_current_vitals_footprint(self):
        self.n.bind_packet_source()
        raw = b'\x2b' + struct.pack('<IIIIHH', 0xffffffff, 123, 0x80000001, 456, 4321, 65535)
        trace = self.n.write_role_current_vitals(raw)
        expected = bytearray(self.before)
        struct.pack_into('<I', expected, 0xec, 0xffffffff)
        struct.pack_into('<I', expected, 0xf4, 0x80000001)
        struct.pack_into('<H', expected, 0xe8, 4321)
        self.assertEqual(self.actor(), expected)
        self.assertIn(0x69eba, trace['pcs'])
        self.assertNotIn(0xe63f0, trace['pcs'])
        for bad in (raw[:-1], raw + b'\0', b'\x24' + raw[1:], bytearray(raw)):
            with self.assertRaises(ValueError):
                self.n.write_role_current_vitals(bad)
        self.assertEqual(self.actor(), expected)

    def test_all_sixteen_original_appends_and_nonzero_scalar_rows(self):
        self.prepare_rows()
        actor = self.actor()
        self.assertEqual(actor[0x15f], 15)
        self.assertEqual(actor[0x164], 16)
        self.assertEqual(self.n.u32(self.n.root + 0x160), self.n.root + 0x168 + 15 * 0x3ec)
        for index in range(16):
            row = 0x168 + index * 0x3ec
            self.assertEqual(struct.unpack_from('<H', actor, row)[0], 100 + index)
            self.assertEqual(actor[row + 2], 7)
            self.assertEqual(actor[row + 3:row + 12], f'Probe{100 + index}'.encode() + b'\0')
            self.assertEqual(struct.unpack_from('<5I', actor, row + 0x44),
                             (1, 257, 4095, 32768, 65535))
            self.assertEqual(actor[row + 0x5a], 1)
        with self.assertRaisesRegex(ValueError, 'sixteen'):
            self.n.append_named_row(named_record(116))

    def test_original_writer_to_actual_call_and_source_reads_same_vm(self):
        self.prepare_rows()
        self.n.bind_descriptor(DESCRIPTOR)
        publish = self.n.publish_battle_source(descriptor=DESCRIPTOR, battle=BATTLE)
        self.assertIn((0x111326, BATTLE + 0x14, 4, self.n.root), publish['writes'])
        actor_before = self.actor()
        # Only AX is assigned by 11166A. Its opaque high bits survive the push.
        self.vm.mem_write(BATTLE + 0xa9df744, struct.pack('<H', 0x1234))
        self.vm.reg_write(x86.UC_X86_REG_EAX, 0xbeef9876)
        self.vm.reg_write(x86.UC_X86_REG_EIP, binding.BASE + 0x1116a4)
        self.vm.reg_write(x86.UC_X86_REG_ESP, SP + 0x900)
        trace = self.n.prove_consumer_prefix(battle=BATTLE)
        self.assertIn(0x1116a4, trace['pcs'])
        self.assertIn(0x11bb80, trace['pcs'])
        reads = [r for r in trace['reads'] if self.n.root <= r[1] < self.n.root + binding.ROOT_SIZE]
        self.assertEqual(reads, [(0x11bc18, self.n.root + 0x15f, 1),
                                 (0x11bc21, self.n.root + 0x164, 1)])
        self.assertEqual(bytes(self.vm.mem_read(SELECTOR + 4, 2)), b'\x0f\x10')
        self.assertEqual(bytes(self.vm.mem_read(SELECTOR + 0x2e14, 2)), b'\x34\x12')
        self.assertEqual(self.n.u32(SP - 8), 0xbeef1234)
        self.assertEqual(self.n.u32(SP - 28), BATTLE + 0xa9ea59c)
        for index in range(16):
            pointer = self.n.root + 0x168 + index * 0x3ec
            self.assertEqual(self.n.u32(SELECTOR + 0x2d4 + index * 0x2d0), pointer)
            self.assertIn((0x11bbea, SELECTOR + 0x2d4 + index * 0x2d0, 4, pointer), trace['writes'])
        self.assertEqual(self.actor(), actor_before)
        self.assertEqual(self.vm.reg_read(x86.UC_X86_REG_EAX), 0xbeef9876)
        self.assertEqual(self.vm.reg_read(x86.UC_X86_REG_EIP), binding.BASE + 0x1116a4)
        self.assertEqual(self.vm.reg_read(x86.UC_X86_REG_ESP), SP + 0x900)
        self.assertNotIn(0x11a9d0, trace['pcs'])

    def test_missing_inputs_are_rejected_without_character_defaults(self):
        for raw in (b'', bytes(19), named_record(17), b'\x30\x64' + b'x' * 16 + b'\x02'):
            before = self.actor()
            with self.assertRaises(ValueError):
                self.n.append_named_row(raw)
            self.assertEqual(self.actor(), before)
        with self.assertRaisesRegex(ValueError, 'snapshot'):
            self.n.prepare_new_root(b'')
        with self.assertRaisesRegex(ValueError, 'overlaps'):
            self.n.prepare_new_root(self.before)
        with self.assertRaisesRegex(ValueError, 'publication'):
            self.n.prove_consumer_prefix(battle=BATTLE)
        self.n.reset_rows()
        self.n.bind_packet_source()
        with self.assertRaisesRegex(ValueError, 'matching row'):
            self.n.write_row_scalars(status_record(100))

    def test_pinned_current_dispatch_and_lengths(self):
        for opcode, target, size in ((0x22, 0x69ef0, 25), (0x30, 0x69f85, 19),
                                      (0x31, 0x69fa9, 29)):
            self.assertEqual(struct.unpack_from('<I', self.image, 0x6b5d4 + opcode * 4)[0],
                             binding.BASE + target)
            size_rva = struct.unpack_from('<I', self.image, 0x1324 + opcode * 4)[0] - binding.BASE
            self.assertEqual(self.image[size_rva:size_rva + 6], b'\xb8' + struct.pack('<I', size) + b'\xc3')

    def test_modified_native_code_is_rejected_before_reset(self):
        self.vm.mem_write(binding.BASE + 0x68120, b'\x90')
        with self.assertRaisesRegex(ValueError, 'executable bytes changed'):
            self.n.reset_rows()
        self.assertEqual(self.actor(), self.before)


if __name__ == '__main__':
    unittest.main()
