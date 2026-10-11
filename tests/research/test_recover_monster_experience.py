"""Current original sources only; synthetic sentinels are never recovered EXP."""
import io
from contextlib import redirect_stdout
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_ECX,
                              UC_X86_REG_ESI, UC_X86_REG_ESP)

sys.path.insert(0, str(ROOT))
from tools.strike_lab import recover_monster_experience as exp
from tools.strike_lab.omega_assets import decode_csvz

CLIENT = ROOT.parent / 'God2'
IMAGE = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
STACK, OWNER, TABLE, POINTERS, PACKET = 0x2000000, 0x2100000, 0x2200000, 0x2300000, 0x2400000
SP = STACK + 0x800


class MonsterExperienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = exp.build_evidence(CLIENT, IMAGE)
        cls.image = exp.pinned_read(IMAGE, exp.IMAGE_SHA256)

    def vm(self):
        vm = Uc(UC_ARCH_X86, UC_MODE_32)
        vm.mem_map(exp.BASE, (len(self.image) + 4095) & ~4095)
        vm.mem_write(exp.BASE, self.image)
        for start, size in ((STACK, 4096), (OWNER, 4096), (TABLE, 0xb4000),
                            (POINTERS, 0x2000), (PACKET, 4096)):
            vm.mem_map(start, size)
        vm.reg_write(UC_X86_REG_ESP, SP)
        return vm

    def execute(self, vm, start, stop):
        vm.emu_start(exp.BASE + start, exp.BASE + stop, count=10000)
        from unicorn.x86_const import UC_X86_REG_EIP
        self.assertEqual(vm.reg_read(UC_X86_REG_EIP), exp.BASE + stop)

    def test_deterministic_stdout_and_explicit_unknowns(self):
        with redirect_stdout(io.StringIO()) as output:
            exp.main(['--client', str(CLIENT), '--image', str(IMAGE)])
        self.assertEqual(output.getvalue(), exp.serialize(self.result))
        self.assertEqual(self.result['monster_awarded_experience_records'], [])
        self.assertEqual(self.result['unknowns'], dict.fromkeys(exp.UNKNOWN))
        self.assertFalse(self.result['runtime_eligible'])
        self.assertEqual([r['record_count'] for r in self.result['visual_definition_audit']], [215, 215])

    def test_exact_message_records_and_offsets(self):
        raw = decode_csvz((CLIENT / 'Data2/Patch/Comm/message.csvZ').read_bytes())
        for section in self.result['messages'].values():
            for row in [section['header']] + section['records']:
                value = bytes.fromhex(row['raw_hex'])
                self.assertEqual(raw[row['offset']:row['offset'] + row['size']], value)
                self.assertEqual(exp.digest(value), row['sha256'])
        rows = self.result['messages']['ProgramMsg']['records']
        self.assertEqual([r['line'] for r in rows], [2321, 2322, 2323])
        self.assertEqual([r['text_cp950'].count('%d') for r in rows], [1, 1, 2])

    def test_pins_fail_closed_and_native_slices_are_exact(self):
        altered = bytearray(self.image)
        altered[0x118c70] ^= 1
        with self.assertRaises(ValueError):
            exp.native_evidence(altered)
        with self.assertRaises(ValueError):
            exp.pinned_read(IMAGE, '0' * 64)
        for row in self.result['native']['instruction_spans'].values():
            raw = self.image[row['rva_start']:row['rva_end_exclusive']]
            self.assertEqual(row['raw_hex'], raw.hex())
            self.assertEqual(row['sha256'], exp.digest(raw))

    def test_original_length_and_both_dispatches(self):
        vm = self.vm()
        # Execute the original length return; synthetic return address is a stop.
        target = struct.unpack_from('<I', self.image, 0x1324 + 4 * 0x89)[0] - exp.BASE
        vm.mem_write(SP, struct.pack('<I', exp.BASE + 0x1000))
        self.execute(vm, target, 0x1000)
        self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 57)
        vm.mem_write(PACKET, b'\x89' + bytes(56))
        vm.reg_write(UC_X86_REG_ESI, PACKET)
        self.execute(vm, 0x1193c4, 0x1195cc)
        vm.reg_write(UC_X86_REG_EBP, PACKET)
        self.execute(vm, 0x114332, 0x114582)
        self.assertEqual(self.result['native']['receive_map_index'], 24)
        self.assertEqual(self.result['native']['queue_map_index'], 8)

    def test_original_message_binding_loop(self):
        vm = self.vm()
        vm.mem_write(OWNER + 0x28, struct.pack('<I', TABLE))
        vm.mem_write(TABLE + 0xb2c68, struct.pack('<Ih', POINTERS, 1080))
        expected = []
        for index in range(1080):
            value = 0x3000000 + index * 32
            vm.mem_write(POINTERS + index * 4, struct.pack('<I', value))
        vm.reg_write(UC_X86_REG_ECX, OWNER)
        self.execute(vm, 0x11125f, 0x1112a5)
        for mid in self.result['native']['message_ids']:
            expected.append(0x3000000 + (mid - 1) * 32)
        self.assertEqual(struct.unpack('<10I', vm.mem_read(0x5b8b48, 40)), tuple(expected))
        self.assertEqual(self.result['native']['message_ids'][2:5], [295, 296, 297])

    def test_original_exp_loads_keep_each_recipient_distinct(self):
        # Stop before each real formatter call: no helper replacement or UI runs.
        # Deliberately unequal values reject a base/credited equality assumption.
        values = (0, 1, 0x12345678, 0x80000000, 0xffffffff)
        for seed in range(len(values)):
            amounts = values[seed:] + values[:seed]
            for slot, (_, offsets, mid, global_rva, start, stop) in enumerate(exp.DISPLAY_FIELDS):
                with self.subTest(seed=seed, mid=mid):
                    vm = self.vm()
                    packet = bytearray(57)
                    packet[0] = 0x89
                    for offset, value in zip((5, 9, 13, 53), amounts):
                        struct.pack_into('<I', packet, offset, value)
                    vm.mem_write(PACKET, bytes(packet))
                    vm.mem_write(OWNER + 0x20, struct.pack('<I', TABLE))
                    pointer = 0x3000000 + mid * 32
                    vm.mem_write(exp.BASE + global_rva, struct.pack('<I', pointer))
                    vm.reg_write(UC_X86_REG_ESI, OWNER)
                    vm.reg_write(UC_X86_REG_EBP, PACKET)
                    self.execute(vm, start, stop)
                    sp = vm.reg_read(UC_X86_REG_ESP)
                    actual = struct.unpack('<' + 'I' * (4 + len(offsets)),
                                           vm.mem_read(sp, 4 * (4 + len(offsets))))
                    wanted = tuple(struct.unpack_from('<I', packet, off)[0] for off in offsets)
                    self.assertEqual(actual, (TABLE, 0, slot, pointer) + wanted)

    def test_missing_selected_message_is_rejected(self):
        raw = decode_csvz((CLIENT / 'Data2/Patch/Comm/message.csvZ').read_bytes())
        row = bytes.fromhex(self.result['messages']['ProgramMsg']['records'][0]['raw_hex'])
        with self.assertRaises(ValueError):
            exp.message_rows(raw.replace(row, row.replace(b'295,', b'99999,', 1), 1))


if __name__ == '__main__':
    unittest.main()
