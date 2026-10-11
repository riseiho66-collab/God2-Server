"""Current-image S2C72 slices only; no legacy corpus or live spawn claim."""
import hashlib
import struct
import subprocess
import unittest

import test_current_npc_spawn as npc
from unicorn.x86_const import (UC_X86_REG_EBX, UC_X86_REG_EBP,
                               UC_X86_REG_EDI, UC_X86_REG_ESI, UC_X86_REG_ESP)


class CurrentTownNpcSpawnTests(unittest.TestCase):
    call = npc.CurrentNpcSpawnTests.call
    run_to = npc.CurrentNpcSpawnTests.run_to
    vm = npc.CurrentNpcSpawnTests.vm
    load_row = npc.CurrentNpcSpawnTests.load_row

    @classmethod
    def setUpClass(cls):
        cls.image = (npc.ROOT / 'artifacts/capture_work/host-20260918-1430/output/'
                     'native-master-01-stable.bin').read_bytes()
        if hashlib.sha256(cls.image).hexdigest() != npc.routes.IMAGE_SHA:
            raise AssertionError('Current image changed')
        raw = (npc.ROOT.parent / 'God2/Data2/Patch/Comm/gamedata.csvZ').read_bytes()
        decoded = npc.decode_csvz(raw)
        if (hashlib.sha256(raw).hexdigest(), hashlib.sha256(decoded).hexdigest()) != (
                npc.GAME_SHA, npc.GAME_DECODED_SHA):
            raise AssertionError('Current data changed')
        lines = decoded.splitlines()
        starts = [i for i, line in enumerate(lines) if line.startswith(b'NPCAppearData,')]
        if len(starts) != 1:
            raise AssertionError('Expected unique NPC section')
        start = starts[0]
        count = int(lines[start].split(b',')[1])
        cls.rows = {int(line.split(b',')[0]): line for line in lines[start+1:start+1+count]}
        if count != 4043 or len(cls.rows) != count:
            raise AssertionError('NPC inventory changed')
        cls.executable = npc.ROOT / 'build/tests/Release/diagnostic-town-npc.exe'
        if not cls.executable.is_file():
            raise AssertionError('Build diagnostic-town-npc before running this test')

    def logical(self, selector, x, y):
        return bytes.fromhex(subprocess.check_output(
            [str(self.executable), str(selector), str(x), str(y)],
            text=True, timeout=5).strip())

    def test_native_dispatch_and_template_selection(self):
        self.assertEqual(struct.unpack_from('<I', self.image, 0x6b5d4+4*0x72)[0],
                         npc.BASE+0x6a68b)
        self.assertEqual(self.image[0x127c:0x1282], b'\xb8\x15\0\0\0\xc3')
        for selector in (1606, 1607):
            with self.subTest(selector=selector):
                vm = self.vm()
                slot = self.load_row(vm, selector)
                self.assertEqual(struct.unpack('<HH', vm.mem_read(slot+0x10, 4)), (0x4000, 20))
                self.assertEqual(bytes(vm.mem_read(slot, len(self.rows[selector].split(b',')[1])+1)),
                                 self.rows[selector].split(b',')[1]+b'\0')
                vm.mem_write(npc.RESOURCE+0x121e8, struct.pack('<h', 6224))
                record = self.logical(selector, 110, 70)
                self.assertEqual(len(record), 21)
                vm.mem_write(npc.BODY, record)
                vm.reg_write(UC_X86_REG_ESP, npc.SP)
                vm.reg_write(UC_X86_REG_EBP, npc.WORLD)
                vm.reg_write(UC_X86_REG_EBX, npc.BODY)
                self.run_to(vm, 0x6a68b, 0x6a9ef)
                for offset in (0x14, 0x24):
                    self.assertEqual(struct.unpack('<I', vm.mem_read(npc.SP+offset, 4))[0], slot)
                args = struct.unpack('<2I', vm.mem_read(npc.SP-8, 8))
                self.assertEqual(tuple(value & 255 for value in args), (0, 20))
                self.run_to(vm, 0x6a9ef, 0x615ab)
                sp = vm.reg_read(UC_X86_REG_ESP)
                self.assertEqual(vm.mem_read(sp+0x10, 1)[0], 19)

    def test_native_scalar_coordinates(self):
        for selector in (1606, 1607):
            for x, y in ((0, 0), (188, 188), (110, 110), (116, 62), (110, 70)):
                with self.subTest(selector=selector, x=x, y=y):
                    vm = self.vm()
                    record = self.logical(selector, x, y)
                    vm.mem_write(npc.BODY, record[1:])
                    vm.reg_write(UC_X86_REG_ESP, npc.SP)
                    vm.reg_write(UC_X86_REG_EDI, npc.BODY)
                    vm.reg_write(UC_X86_REG_ESI, npc.ACTOR)
                    # Deliberate scalar-test sentinel, not an asset lookup result.
                    vm.reg_write(UC_X86_REG_EBX, 0xa5a5)
                    self.run_to(vm, 0xcc621, 0xcc690)
                    self.assertEqual(struct.unpack('<I3H', vm.mem_read(npc.ACTOR, 10)),
                                     (selector, 0xa5a5, 0, 0))
                    self.assertEqual(struct.unpack('<2I', vm.mem_read(npc.ACTOR+0x10, 8)), (x, y))

    def test_reject_invalid_diagnostic_inputs(self):
        for args in ((1605, 110, 70), (1608, 110, 70), (1606, 189, 0),
                     (1607, 0, 189), (1606, -1, 0), (1606, '1junk', 0),
                     (1606, 4294967296, 0)):
            with self.subTest(args=args):
                result = subprocess.run([str(self.executable), *map(str, args)],
                                        capture_output=True, timeout=5)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, b'')


if __name__ == '__main__':
    unittest.main()
