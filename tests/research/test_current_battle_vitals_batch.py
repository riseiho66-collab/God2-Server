"""Original bulk S2C88 writer and lossless C++ codec; synthetic values only."""
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

import test_current_battle_scalar_result as scalar
from test_current_instance_update import build_fixture, ROOT
from unicorn import UcError, UC_ERR_WRITE_UNMAPPED, UC_PROT_READ


class BattleVitalsBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        scalar.CurrentBattleScalarResultTests.setUpClass()
        cls.temp = tempfile.TemporaryDirectory(prefix='god2-bulk-vitals-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.exe = build_fixture(Path(cls.temp.name),
                                source=ROOT / 'tests/test_recovered_battle_vitals_batch.cpp')

    @staticmethod
    def packet(seed):
        raw = bytearray((i * 31 + seed) & 255 for i in range(121))
        raw[0] = 0x88
        for slot in range(14):
            struct.pack_into('<II', raw, 5 + slot * 8,
                             (seed + slot) & 0xffffffff, (seed ^ (slot * 0x10101)) & 0xffffffff)
        return bytes(raw)

    def decode(self, packets):
        result = subprocess.run([str(self.exe)], input=''.join(p.hex() + '\n' for p in packets),
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), len(packets))
        return [None if line == 'reject' else tuple(map(int, line.split())) for line in lines]

    def prepare(self, raw):
        n = scalar.CurrentBattleScalarResultTests()
        n.ranges = ((0x12d360, 0x12d3a2), (0x11e6e0, 0x11e76a), (0x12d9f0, 0x12da23))
        vm = n.machine()
        actors = [scalar.ENTITY + slot * 4096 for slot in range(28)]
        for slot, address in enumerate(actors):
            n.map_page(vm, address)
            vm.mem_write(address, n.entity(handle=-1, scalars=(slot, slot + 1, 123, 456)))
            vm.mem_write(scalar.CONTEXT + 0x38 + slot * 24, struct.pack('<I', address))
        vm.mem_write(scalar.INPUT, raw)
        vm.mem_protect(scalar.INPUT, 4096, UC_PROT_READ)
        n.allowed = tuple((address + 0xde8, address + 0xdf0) for address in actors[:14])
        return n, vm, actors

    def test_native_binding_and_all_slots_match_cpp_without_maxima_or_enemy_writes(self):
        image = scalar.CurrentBattleScalarResultTests.image
        self.assertEqual(struct.unpack_from('<I', image, 0x1324 + 0x88 * 4)[0], scalar.BASE + 0x123a)
        self.assertEqual(image[0x123a:0x1240], bytes.fromhex('b879000000c3'))
        for pc, target in ((0x114550, 0x118a90), (0x118bcb, 0x12d360), (0x12d38e, 0x12d9f0)):
            self.assertEqual(image[pc], 0xe8)
            self.assertEqual(pc + 5 + struct.unpack_from('<i', image, pc + 1)[0], target)
        for seed in (0, 1, 0x7fffffff, 0x80000000, 0xffffffff):
            raw = self.packet(seed)
            expected = self.decode([raw])[0]
            n, vm, actors = self.prepare(raw)
            before = [bytes(vm.mem_read(address, 4096)) for address in actors]
            n.execute(vm, 0x12d360, args=(scalar.INPUT + 1,),
                      registers=(('ECX', scalar.CONTEXT),), callee_pop=4)
            self.assertEqual(n.trace.count(0x11e6e0), 14)
            self.assertEqual(n.trace.count(0x12d9f0), 14)
            self.assertNotIn(0x12da1a, n.trace)  # Negative UI handles, not a stub.
            self.assertEqual(n.writes, [(address + 0xde8 + channel * 4, 4, expected[slot * 2 + channel])
                                       for slot, address in enumerate(actors[:14]) for channel in range(2)])
            for slot, address in enumerate(actors):
                wanted = bytearray(before[slot])
                if slot < 14:
                    wanted[0xde8:0xdf0] = raw[5 + slot * 8:13 + slot * 8]
                self.assertEqual(bytes(vm.mem_read(address, 4096)), wanted)
            self.assertEqual([(at - scalar.INPUT, size) for at, size in n.reads
                              if scalar.INPUT <= at < scalar.INPUT + len(raw)],
                             [(5 + index * 4, 4) for index in range(28)])
            self.assertEqual(bytes(vm.mem_read(scalar.INPUT, len(raw))), raw)
            self.assertEqual(bytes(vm.mem_read(scalar.BASE, len(image))), image)

    def test_missing_actor_is_not_a_supported_sparse_update(self):
        n, vm, _ = self.prepare(self.packet(1))
        vm.mem_write(scalar.CONTEXT + 0x38, bytes(4))
        with self.assertRaises(UcError) as raised:
            n.execute(vm, 0x12d360, args=(scalar.INPUT + 1,), registers=(('ECX', scalar.CONTEXT),), callee_pop=4)
        self.assertEqual(raised.exception.errno, UC_ERR_WRITE_UNMAPPED)
        self.assertIn(0x12d37d, n.trace)

    def test_receiver_header_branches_continuously_reach_all_fourteen_updates(self):
        for cached in (0xffffffff, 0x11223344):
            for flag in (0, 1, 2):
                raw = bytearray(self.packet(0x80000000))
                struct.pack_into('<I', raw, 1, 0xfedcba98)
                raw[118] = 0xa7
                n, vm, actors = self.prepare(bytes(raw))
                n.ranges += ((0x118a90, 0x118beb),)
                for offset in (0xa9defb0, 0xa9df6b8):
                    n.map_page(vm, scalar.BATTLE + offset)
                vm.mem_write(scalar.BATTLE + 0x51, b'\xff')  # No local-slot UI path.
                for offset, value in ((0x44, 0), (0xa9e9c64, cached),
                                      (0xa9e9c68, 0x12345678), (0xa9e9c6c, flag),
                                      (0xa9e9c70, 0x87654321)):
                    vm.mem_write(scalar.BATTLE + offset, struct.pack('<I', value))
                n.allowed += tuple((scalar.BATTLE + a, scalar.BATTLE + z) for a, z in (
                    (0x44, 0x48), (0xa9e9c44, 0xa9e9c88),
                    (0xa9defb0, 0xa9defb4), (0xa9df6b8, 0xa9df6bc)))
                before = {page: bytearray(vm.mem_read(page, 4096)) for page in n.pages
                          if not scalar.STACK <= page < scalar.STACK + 0x4000}
                stop = n.execute(vm, 0x118a90, args=(scalar.INPUT,),
                                 registers=(('ECX', scalar.BATTLE),), stops=(0x116ac0,))
                self.assertEqual(stop, 0x116ac0)
                self.assertEqual(n.trace.count(0x12d360), 1)
                self.assertEqual(n.trace.count(0x11e6e0), 14)
                for offset, expected in (
                    (0x44, 1), (0xa9e9c48, 1), (0xa9defb0, 0),
                    (0xa9e9c64, cached if cached != 0xffffffff and flag == 1 else 0xfedcba98),
                    (0xa9e9c68, 0xfedcba98 if cached == 0xffffffff else 0x12345678),
                    (0xa9e9c6c, 0 if flag == 1 else flag),
                    (0xa9e9c70, 0x87654321 if cached == 0xffffffff else 20),
                    (0xa9e9c44, 0), (0xa9df6b8, 0)):
                    self.assertEqual(struct.unpack('<I', vm.mem_read(scalar.BATTLE + offset, 4))[0], expected)
                self.assertEqual(bytes(vm.mem_read(scalar.BATTLE + 0xa9e9c84, 1)), b'\xa7')
                self.assertEqual(bytes(vm.mem_read(scalar.BATTLE + 0xa9e9c78, 2)), b'\0\0')
                for slot, actor in enumerate(actors[:14]):
                    self.assertEqual(bytes(vm.mem_read(actor + 0xde8, 8)), raw[5 + slot * 8:13 + slot * 8])
                consumed = set()
                for address, size in n.reads:
                    if scalar.INPUT <= address < scalar.INPUT + len(raw):
                        consumed.update(range(address - scalar.INPUT, address - scalar.INPUT + size))
                expected_reads = set(range(5, 117)) | {118}
                if cached == 0xffffffff or flag != 1:
                    expected_reads.update(range(1, 5))
                self.assertEqual(consumed, expected_reads)
                for address, size, value in n.writes:
                    for index, byte in enumerate(value.to_bytes(size, 'little')):
                        at = address + index
                        before[at & ~4095][at & 4095] = byte
                for page, wanted in before.items():
                    self.assertEqual(bytes(vm.mem_read(page, 4096)), wanted)
                self.assertEqual(bytes(vm.mem_read(scalar.BASE, len(n.image))), n.image)

    def test_codec_exact_bounds_and_opaque_bytes(self):
        raw = self.packet(0x80000000)
        packets = [(raw + b'\xcc')[:size] for size in range(123)]
        expected = [len(p) == 121 for p in packets]
        for opcode in range(256):
            packets.append(bytes((opcode,)) + raw[1:]); expected.append(opcode == 0x88)
        for offset in (1, 2, 3, 4, 117, 118, 119, 120):
            for value in (0, 255):
                changed = bytearray(raw); changed[offset] = value
                packets.append(bytes(changed)); expected.append(True)
        for packet, accepted, parsed in zip(packets, expected, self.decode(packets)):
            self.assertEqual(parsed is not None, accepted)
            if accepted:
                self.assertEqual(parsed, struct.unpack_from('<28I', packet, 5))

    def test_dispatch_consumption_wraps_without_eating_following_record(self):
        raw = self.packet(7)
        following = b'\x86' + bytes(range(16))
        for head in (0, 135, 200, 255):
            for tail in (b'', following):
                n = scalar.CurrentBattleScalarResultTests()
                n.ranges = ((0x114555, 0x114582), (0x15840, 0x15850),
                    (0x1000, 0x1013), (0x1200, 0x1216), (0x123a, 0x1240),
                    (0x11d3d0, 0x11d4d2))
                vm = n.machine()
                ring, scratch = scalar.AUX, scalar.AUX + 0x400
                for offset in (0xa9df6c0, 0xa9ea4c4):
                    n.map_page(vm, scalar.BATTLE + offset)
                source = bytearray(b'\xa5' * 256)
                for index, byte in enumerate(raw + tail):
                    source[(head + index) % 256] = byte
                vm.mem_write(scalar.INPUT, bytes(source))
                vm.mem_protect(scalar.INPUT, 4096, UC_PROT_READ)
                vm.mem_write(scratch, raw)
                end = (head + len(raw) + len(tail)) % 256
                vm.mem_write(ring, struct.pack('<5I', 0, scalar.INPUT, head, end, 256))
                n.allowed = ((ring + 8, ring + 16), (scratch, scratch + 121),
                    (scalar.BATTLE + 0xa9df6c0, scalar.BATTLE + 0xa9df6c4),
                    (scalar.BATTLE + 0xa9ea4c4, scalar.BATTLE + 0xa9ea4c8))
                self.assertEqual(n.execute(vm, 0x114555,
                    registers=(('ESI', scalar.BATTLE), ('EDI', scratch),
                               ('EBP', scratch), ('EBX', ring)),
                    stops=(0x1145c0,)), 0x1145c0)
                self.assertEqual(vm.reg_read(scalar.reg.UC_X86_REG_ESP), scalar.SP)
                self.assertEqual(bytes(vm.mem_read(scratch, 121)), raw)
                self.assertEqual(struct.unpack('<2I', vm.mem_read(ring + 8, 8)),
                    ((head + 121) % 256, end) if tail else (0, 0))
                self.assertEqual(bytes(vm.mem_read(scalar.INPUT, 256)), bytes(source))
                self.assertEqual(bytes(vm.mem_read(scalar.BASE, len(n.image))), n.image)

    def test_cleanup_actor_pass_covers_all_types_without_changing_vitals(self):
        n = scalar.CurrentBattleScalarResultTests()
        n.ranges = ((0x120300, 0x12039d), (0x11e6e0, 0x11e76a), (0x11fd70, 0x11fdd7))
        vm = n.machine()
        n.map_page(vm, scalar.CONTEXT + 0x38 + 168 * 4)
        vm.mem_write(scalar.CONTEXT + 0x28, bytes(4))  # No resource owner.
        actors = [scalar.ENTITY + i * 4096 for i in range(168)]
        expected = {}
        for i, address in enumerate(actors):
            n.map_page(vm, address)
            raw = bytearray(n.entity(handle=-1, marker=-1, scalars=(i, i + 1, 123, 456)))
            vm.mem_write(address, bytes(raw))
            vm.mem_write(scalar.CONTEXT + 0x38 + i * 4, struct.pack('<I', address))
            raw[0xdf8:0xec8] = bytes(0xd0)
            for index in range(50):
                for offset in (0, 2, 6):
                    start = 0x34 + index * 8 + offset
                    raw[start:start + 2] = b'\xff\xff'
            expected[address] = raw
        n.allowed = tuple(span for address in actors for span in
                          ((address + 0xdf8, address + 0xec8), (address + 0x34, address + 0x1c4)))
        stop = n.execute(vm, 0x120300, registers=(('ECX', scalar.CONTEXT),),
                         stops=(0x12039d,), instruction_limit=250000)
        self.assertEqual(stop, 0x12039d)
        self.assertEqual(n.trace.count(0x11e6e0), 168)
        self.assertEqual(n.trace.count(0x11fd70), 168 * 50)
        self.assertNotIn(0x120356, n.trace)  # Type5 negative handle, no renderer free.
        self.assertNotIn(0x11fdb5, n.trace)  # No resource owner, no substitute call.
        for address, wanted in expected.items():
            self.assertEqual(bytes(vm.mem_read(address, 4096)), wanted)
        self.assertEqual(bytes(vm.mem_read(scalar.BASE, len(n.image))), n.image)
        # Full function with inactive graphics entries and the real formatter.
        text_owner, graphics, counters = 0x7000000, 0x7400000, 0x7800000
        cursor = text_owner + 0x2a2800
        entries = [graphics + i * 0x2034 for i in range(80)]
        for address in (cursor, counters, graphics + 0xa6540, *entries):
            n.map_page(vm, address)
            n.map_page(vm, address + 0x40c if address == counters else address + 0x28)
        for offset, pointer in ((0x18, text_owner), (0x20, graphics), (0x24, counters)):
            vm.mem_write(scalar.CONTEXT + offset, struct.pack('<I', pointer))
        vm.mem_write(graphics + 0xa6558, struct.pack('<I', counters))
        vm.mem_write(counters + 0x404, b'\xa5' * 12)
        n.allowed += tuple((entry, entry + 0x2a) for entry in entries)
        n.allowed += ((cursor + 8, cursor + 12), (cursor + 0x304, cursor + 0x308),
                      (graphics + 0xa6540, graphics + 0xa6544),
                      (counters + 0x404, counters + 0x410))
        n.ranges += ((0x12039d, 0x1203f1), (0x2d9c0, 0x2da1c),
                     (0x28880, 0x288d5), (0x289b0, 0x289b1),
                     (0x2dfa0, 0x2e017), (0x2de30, 0x2df35),
                     (0x146cf7, 0x146d48), (0x14cf08, 0x14d67e))
        n.execute(vm, 0x120300, registers=(('ECX', scalar.CONTEXT),), instruction_limit=250000)
        self.assertEqual(n.trace.count(0x146cf7), 2)
        self.assertEqual(n.trace.count(0x2de30), 80)
        self.assertNotIn(0x2dfba, n.trace)
        for address, wanted in expected.items():
            self.assertEqual(bytes(vm.mem_read(address, 4096)), wanted)
        for entry in entries:
            self.assertEqual(bytes(vm.mem_read(entry, 4)), bytes(4))
            self.assertEqual(bytes(vm.mem_read(entry + 0x28, 2)), b'\xff\xff')
        self.assertEqual(bytes(vm.mem_read(counters + 0x404, 12)), bytes(4) + b'\xa5' * 4 + bytes(4))
        self.assertEqual(bytes(vm.mem_read(scalar.BASE, len(n.image))), n.image)
        # Continuous receiver -> both cleanup callees -> actual receiver return.
        resource_table = scalar.BATTLE + 0x4bf4c + 0x121ec
        table_size = 0x404 * 0x4c
        for address in range(resource_table & ~4095, resource_table + table_size + 4095, 4096):
            n.map_page(vm, address)
        vm.mem_write(resource_table, b'\xa5' * table_size)
        for offset in (0xa9defb0, 0xa9df6b8):
            n.map_page(vm, scalar.BATTLE + offset)
        vm.mem_write(scalar.BATTLE + 0x51, b'\xff')
        vm.mem_write(scalar.BATTLE + 0xa9e9c64, b'\xff' * 4)
        raw_packet = self.packet(0x80000000)
        vm.mem_write(scalar.INPUT, raw_packet)
        vm.mem_protect(scalar.INPUT, 4096, UC_PROT_READ)
        n.allowed += tuple((actors[slot * 6] + 0xde8, actors[slot * 6] + 0xdf0) for slot in range(14))
        n.allowed += ((resource_table, resource_table + table_size),)
        n.allowed += tuple((scalar.BATTLE + a, scalar.BATTLE + z) for a, z in (
            (0x44, 0x48), (0xa9e9c44, 0xa9e9c88),
            (0xa9defb0, 0xa9defb4), (0xa9df6b8, 0xa9df6bc)))
        n.ranges += ((0x118a90, 0x118beb), (0x12d360, 0x12d3a2),
                     (0x12d9f0, 0x12da23), (0x116ac0, 0x116adb), (0x5f450, 0x5f46c))
        n.ranges += ((0x114332, 0x114358), (0x114538, 0x114582),
                     (0x1145c0, 0x1145e0), (0x12ac20, 0x12ae2f),
                     (0x115a59, 0x115add), (0x15840, 0x15850),
                     (0x1000, 0x1013), (0x1200, 0x1216), (0x123a, 0x1240),
                     (0x11d3d0, 0x11d4d2))
        n.map_page(vm, scalar.BATTLE + 0xa9ea4c4)
        phase_counters = scalar.CONTEXT + 0xa7fbc64
        n.map_page(vm, phase_counters)
        vm.mem_write(phase_counters, b'\xa5' * 8)
        n.allowed += ((phase_counters, phase_counters + 8),
                      (scalar.CONTEXT + 0x308, scalar.CONTEXT + 0x309))
        n.allowed += ((scalar.BATTLE + 0xa9ea4c4, scalar.BATTLE + 0xa9ea4c8),)
        vm.mem_write(scalar.BATTLE + 0xa9e9c44, struct.pack('<I', 1))
        vm.mem_write(scalar.BATTLE + 0xa9e9c48, struct.pack('<I', 1))
        gate_registers = (('ESI', scalar.BATTLE), ('EBX', 0), ('EDI', 1))
        self.assertEqual(n.execute(vm, 0x115a59, registers=gate_registers,
                         stops=(0x115ad8, 0x115add)), 0x115add)
        # The dispatcher checks its pending-event pointer at stack +2C.
        phase_pointer = scalar.AUX + 0x800
        vm.mem_write(phase_pointer, b'\x00')
        dispatch_args = (0,) * 9 + (phase_pointer, scalar.AUX)
        ring, scratch = scalar.AUX + 0x100, scalar.AUX + 0x400
        vm.mem_write(ring, struct.pack('<5I', 0, scalar.INPUT, 0, len(raw_packet), 256))
        vm.mem_write(scratch, raw_packet)
        n.allowed += ((ring + 8, ring + 16), (scratch, scratch + len(raw_packet)),
                      (scalar.BATTLE + 0xa9df6c0, scalar.BATTLE + 0xa9df6c4))
        dispatch_registers = (('ESI', scalar.BATTLE), ('EDI', scratch),
                              ('EBP', scratch), ('EBX', ring))
        vm.mem_write(scalar.AUX, struct.pack('<I', 1))
        vm.mem_write(scalar.BATTLE + 0xa9ea4c4, struct.pack('<I', 1))
        self.assertEqual(n.execute(vm, 0x114332, args=dispatch_args,
            registers=dispatch_registers, stops=(0x1145c0, 0x118a90)), 0x1145c0)
        self.assertNotIn(0x118a90, n.trace)
        self.assertEqual(bytes(vm.mem_read(scalar.BATTLE + 0xa9e9c44, 4)), struct.pack('<I', 1))
        self.assertEqual(bytes(vm.mem_read(scalar.BATTLE + 0xa9ea4c4, 4)), bytes(4))
        vm.mem_write(scalar.AUX, bytes(4))
        for i, address in enumerate(actors):
            vm.mem_write(address, n.entity(handle=-1, marker=-1, scalars=(i, i + 1, 123, 456)))
        formatted = []
        def observe_text(machine, address, size, _):
            if address == scalar.BASE + 0x2da10:
                sp = machine.reg_read(scalar.reg.UC_X86_REG_ESP)
                pointer = struct.unpack('<I', machine.mem_read(sp + 4, 4))[0]
                formatted.append(bytes(machine.mem_read(pointer, 512)).split(b'\0', 1)[0])
        hook = vm.hook_add(scalar.UC_HOOK_CODE, observe_text)
        try:
            self.assertEqual(n.execute(vm, 0x114332, args=dispatch_args,
                registers=dispatch_registers, stops=(0x12ae2f,),
                instruction_limit=250000), 0x12ae2f)
            self.assertEqual(vm.reg_read(scalar.reg.UC_X86_REG_ESP), scalar.SP - 32)
        finally:
            vm.hook_del(hook)
        self.assertEqual(formatted, [n.image[at:n.image.index(0, at)] for at in (0x19d644, 0x19d634)])
        self.assertEqual(n.trace.count(0x11e6e0), 210)
        self.assertEqual(n.trace.count(0x12ac20), 1)
        self.assertEqual(n.trace.count(0x12ac71), 28)
        self.assertEqual(bytes(vm.mem_read(phase_counters, 8)), bytes(8))
        self.assertEqual(bytes(vm.mem_read(scalar.CONTEXT + 0x308, 1)), b'\x00')
        self.assertNotIn(0x1145e4, n.trace)
        self.assertEqual(n.trace.count(0x120300), 1)
        self.assertEqual(n.trace.count(0x5f450), 1)
        self.assertIn(0x118be8, n.trace)
        self.assertEqual(n.trace.count(0x11d3d0), 1)
        self.assertIn(0x123a, n.trace)
        self.assertEqual(bytes(vm.mem_read(ring + 8, 8)), bytes(8))
        self.assertEqual(bytes(vm.mem_read(scratch, len(raw_packet))), raw_packet)
        self.assertEqual(bytes(vm.mem_read(scalar.BATTLE + 0xa9df6c0, 4)), struct.pack('<I', 1))
        self.assertEqual(bytes(vm.mem_read(scalar.BATTLE + 0xa9ea4c4, 4)), bytes(4))
        for slot in range(14):
            expected[actors[slot * 6]][0xde8:0xdf0] = raw_packet[5 + slot * 8:13 + slot * 8]
        for address, wanted in expected.items():
            self.assertEqual(bytes(vm.mem_read(address, 4096)), wanted)
        table = bytearray(b'\xa5' * table_size)
        for index in range(0x404):
            table[index * 0x4c:index * 0x4c + 4] = b'\xff' * 4
        self.assertEqual(bytes(vm.mem_read(resource_table, table_size)), table)
        self.assertEqual(bytes(vm.mem_read(scalar.INPUT, len(raw_packet))), raw_packet)
        self.assertEqual(bytes(vm.mem_read(scalar.BASE, len(n.image))), n.image)
        self.assertEqual(bytes(vm.mem_read(scalar.BATTLE + 0xa9e9c44, 4)), bytes(4))
        self.assertEqual(n.execute(vm, 0x115a59, registers=gate_registers,
                         stops=(0x115ad8, 0x115add)), 0x115ad8)
        sp = vm.reg_read(scalar.reg.UC_X86_REG_ESP)
        self.assertEqual(struct.unpack('<I', vm.mem_read(sp, 4))[0], 11)
        # The final side1/slot13/type5 entry is also dereferenced unchecked.
        vm.mem_write(scalar.CONTEXT + 0x38 + 167 * 4, bytes(4))
        with self.assertRaises(UcError) as raised:
            n.execute(vm, 0x120300, registers=(('ECX', scalar.CONTEXT),),
                      stops=(0x12039d,), instruction_limit=250000)
        self.assertEqual(raised.exception.errno, UC_ERR_WRITE_UNMAPPED)
        self.assertEqual(n.trace.count(0x11e6e0), 168)
        self.assertEqual(n.trace[-1], 0x12033f)


if __name__ == '__main__':
    unittest.main()
