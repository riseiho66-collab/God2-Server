"""Real battle resource preload and consumers; bounded native, not live E2E."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_battle_resources as resources
from tools.strike_lab.current_indoor_resources import SCRATCH
from tools.strike_lab.current_battle_entry import pinned_image
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_EAX


class CurrentBattleResourcesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.n = resources.NativeBattleResources()
        cls.handles = cls.n.preload()
        cls.strip = cls.n.initialize_control_strip()

    def test_original_csv_reader_populates_all_ten_rows(self):
        n = self.n
        self.assertEqual(n.native_decoded, [resources.PLAIN_SHA])
        self.assertEqual(n.u32(resources.READER + 0x121e8), 10)
        self.assertEqual(resources.READER + 0x121f0, resources.BATTLE + 0x83458)
        self.assertEqual(n.visits.count(0x54720), 1)
        self.assertEqual(n.visits.count(0x54859), 1)
        for index, row in enumerate(n.rows):
            at = index * resources.STRIDE
            self.assertEqual(struct.unpack_from('<I', n.reader_snapshot, at)[0], index)
            self.assertEqual(n.reader_snapshot[at+4:at+resources.STRIDE].split(b'\0')[0],
                             row[1].encode('ascii'))

    def test_original_preload_resolves_decodes_and_binds_every_asset(self):
        n = self.n
        self.assertEqual(self.handles, list(range(10)))  # Fresh, originally constructed registry.
        self.assertEqual(n.visits.count(0x110e52), 10)
        self.assertEqual(n.visits.count(0x120650), n.visits.count(0x1207c9))
        self.assertEqual(n.u32(n.names + 0x404), 10)
        self.assertEqual(n.u32(n.names + 0x408), 0xfc)
        self.assertEqual(n.u32(n.names + 0x40c), 0)
        self.assertEqual(n.parser_inputs, [(path, i, len(n.decoded[path]))
                                          for i, path in enumerate(resources.ASSETS)])
        self.assertEqual([p for p in n.opens if isinstance(p, str)], list(resources.ASSETS))
        self.assertEqual(len(n.attempts), 10)
        self.assertFalse(n.handles)
        for index, handle in enumerate(self.handles):
            at = n.records + index * resources.STRIDE
            self.assertEqual(n.u32(at), handle)
            self.assertEqual(bytes(n.vm.mem_read(at+4, resources.STRIDE-4)),
                             n.reader_snapshot[index*resources.STRIDE+4:(index+1)*resources.STRIDE])
        self.assertEqual(n.u32(0), 0xffffffff)

    def test_original_control_strip_uses_bound_state_icon_handle(self):
        n = self.n
        self.assertEqual(struct.unpack_from('<H', self.strip, 4)[0], self.handles[6])
        sprites = struct.unpack_from('<25H', self.strip, 6)
        self.assertEqual(len(set(sprites)), 25)
        self.assertTrue(all(handle < 4096 for handle in sprites))
        self.assertEqual(struct.unpack_from('<I', self.strip, 0x3c)[0], resources.RENDERER)
        self.assertEqual(self.strip[:4], b'\xa5' * 4)
        self.assertEqual(self.strip[0x38:0x3c], b'\xa5' * 4)
        strip = resources.MANAGER + 0xa7fbc80
        self.assertEqual(bytes(n.vm.mem_read(strip-16, 16)), b'\xa5' * 16)
        self.assertEqual(bytes(n.vm.mem_read(strip+0x40, 16)), b'\xa5' * 16)
        self.assertEqual(n.visits.count(0x11fbf0), 1)
        self.assertEqual(n.visits.count(0x11149b), 1)
        self.assertEqual(n.visits.count(0x1114aa), 1)
        self.assertEqual(n.visits.count(0x11da10), 1)
        self.assertEqual(n.visits.count(0x11db47), 1)
        self.assertEqual(n.visits.count(0x1afe0), 25)
        self.assertEqual(n.visits.count(0x1b560), 25)

    def test_existing_name_reuses_original_handle_without_reloading(self):
        n = self.n
        before = (len(n.attempts), len(n.parser_inputs), n.u32(n.names + 0x404))
        for index in (9, 6, 0):
            name = n.string(n.u32(n.names + 4 + 4 * index))
            n.cstring(SCRATCH, name)
            self.assertEqual(n.call(0x120650, n.u32(SCRATCH), this=resources.MANAGER),
                             self.handles[index])
        self.assertEqual((len(n.attempts), len(n.parser_inputs), n.u32(n.names + 0x404)), before)
        self.assertFalse(n.handles)
        self.assertEqual(n.u32(0), 0xffffffff)

    def test_failed_preload_cannot_authorize_control_or_retry(self):
        # Exercise stage bookkeeping without executing or mocking any game code.
        n = resources.NativeBattleResources.__new__(resources.NativeBattleResources)
        n.vm = Mock()
        n.run = Mock(side_effect=AssertionError('Native stage failed'))
        n.battle, n.manager = resources.BATTLE, resources.MANAGER
        n.preloaded = n.preload_attempted = n.control_attempted = False
        with self.assertRaisesRegex(AssertionError, 'Native stage failed'):
            n.preload()
        self.assertFalse(n.preloaded)
        self.assertTrue(n.preload_attempted)
        with self.assertRaises(ValueError):
            n.initialize_control_strip()
        with self.assertRaises(ValueError):
            n.preload()
        self.assertEqual(n.run.call_count, 1)

    def test_missing_rom_binding_keeps_handle_but_hits_original_failure(self):
        n = self.n
        # Counterfactual VM only: keep the CSV-derived handle unchanged and
        # remove its native action binding. Restore all touched fixture state.
        count_address = resources.BANK + self.handles[6] * 0x1514 + 0x108c
        original_count = bytes(n.vm.mem_read(count_address, 4))
        self.assertGreater(struct.unpack('<I', original_count)[0], 0)
        context = n.vm.context_save()
        strip = resources.MANAGER + 0xa7fbc80
        snapshots = [(at, bytes(n.vm.mem_read(at, size))) for at, size in (
            (resources.SP - 4096, 8192), (resources.RENDERER, 0x291000), (strip-16, 0x70))]
        before = len(n.visits)
        try:
            n.vm.mem_write(count_address, bytes(4))
            n.vm.reg_write(resources.UC_X86_REG_ESP, resources.SP)
            n.vm.reg_write(resources.UC_X86_REG_EBP, resources.BATTLE)
            n.vm.reg_write(resources.UC_X86_REG_ESI, resources.MANAGER)
            n.run(0x11149b, 0x1b078)  # Before assertion call, never fake its return.
            self.assertEqual(n.vm.reg_read(UC_X86_REG_EIP), resources.BASE + 0x1b078)
            self.assertEqual(n.vm.reg_read(UC_X86_REG_EAX), 0xffffffff)
            self.assertEqual(n.u32(n.records + 0x630), self.handles[6])
            trace = n.visits[before:]
            self.assertEqual(trace.count(0x1afe0), 1)
            self.assertNotIn(0x11db47, trace)
        finally:
            n.vm.mem_write(count_address, original_count)
            for at, raw in snapshots:
                n.vm.mem_write(at, raw)
            n.vm.context_restore(context)
            del n.visits[before:]

    def test_native_call_witnesses_and_executable_bytes_unchanged(self):
        n = self.n
        image = pinned_image()
        for caller, callee in ((0x110a4a, 0x546e0), (0x110be7, 0x54720),
                               (0x110e43, 0x120650), (0x1206e5, 0x29820),
                               (0x1114aa, 0x11fbf0), (0x11fc21, 0x11da10),
                               (0x11da3d, 0x1afe0)):
            raw = image[caller:caller+5]
            self.assertEqual(raw[0], 0xe8)
            self.assertEqual(caller + 5 + struct.unpack_from('<i', raw, 1)[0], callee)
        for lo, hi in ((0x110bb9, 0x110bec), (0x110df2, 0x110e72),
                       (0x11f4ef, 0x11f55c), (0x120650, 0x1207cc),
                       (0x11da10, 0x11db4a), (0x546e0, 0x5485c)):
            self.assertEqual(bytes(n.vm.mem_read(resources.BASE + lo, hi-lo)), image[lo:hi])
        with self.assertRaises(ValueError):
            n.preload()
        with self.assertRaises(ValueError):
            n.initialize_control_strip()


if __name__ == '__main__':
    unittest.main()
