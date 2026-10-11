"""Source -> original reader -> +214 -> original consumer, without graphics."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_world_ui_resource import (
    NativeWorldUIResource, pinned_sources, SOURCE, ASSET, SOURCE_PLAIN_SHA,
    ASSET_PLAIN_SHA, LITERAL_PATH, CWD, UI, READER, RECORD_POINTER,
    STRIDE, INDEX, PATH_OFFSET, CAPACITY, BASE)


class CurrentWorldUIResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = NativeWorldUIResource()

    def test_exact_current_source_line_and_real_asset(self):
        sources, rows = pinned_sources()
        self.assertEqual(rows[INDEX][:3],
                         ['2', LITERAL_PATH.decode(), 'ROM_DTITLEGUI,'])
        self.assertEqual(sources[0][1].splitlines()[6].split(b',', 2)[:2],
                         [b'2', LITERAL_PATH])
        self.assertEqual(len(sources[1][0]), 10310)
        self.assertEqual(len(sources[1][1]), 30310)
        self.assertTrue(sources[1][1].startswith(b'IGSROM02\0\0\0\0ACTINDEX'))
        self.assertFalse((ROOT.parent/'God2'/SOURCE[:-1]).exists())
        self.assertFalse((ROOT.parent/'God2'/ASSET[:-1]).exists())

    def test_complete_native_reader_and_exact_path_writer(self):
        n = self.native
        self.assertEqual(n.reader_result, 1)
        self.assertEqual(n.native_decoded, [SOURCE_PLAIN_SHA, ASSET_PLAIN_SHA])
        self.assertEqual(n.callocs, [(STRIDE, CAPACITY)])
        self.assertEqual(n.u32(READER+0x121e8), CAPACITY)
        self.assertEqual(RECORD_POINTER-UI, 0xe2164)
        self.assertEqual(0xa7f2f6c+0xe2164, 0xa8d50d0)
        self.assertEqual(PATH_OFFSET, INDEX*STRIDE+4)
        self.assertEqual(n.u32(n.records+INDEX*STRIDE), INDEX)
        self.assertEqual(n.string(n.records+PATH_OFFSET), LITERAL_PATH)
        self.assertEqual(len(n.path_copies), CAPACITY)
        self.assertEqual(n.path_copies[INDEX], (1, n.records+PATH_OFFSET))
        self.assertEqual({rva for rva, _, _ in n.path_writes}, {0x51b12, 0x51b19})
        covered = {offset+i for _, offset, size in n.path_writes for i in range(size)}
        self.assertEqual(covered, set(range(len(LITERAL_PATH)+1)))
        for rva in (0x815c0, 0x54720, 0x54776, 0x54800, 0x51ae0):
            self.assertIn(rva, n.visits)
        self.assertFalse(n.handles)
        self.assertEqual(n.u32(0), 0xffffffff)

    def test_native_resolver_and_actual_consumer_argument(self):
        n = self.native
        expected = CWD + LITERAL_PATH
        self.assertEqual(n.resolve(), expected)
        self.assertEqual(n.consumer_path(), expected)
        self.assertEqual(n.consumer_path(), expected)
        self.assertEqual(n.rom_open_path(), expected+b'Z')
        self.assertEqual(n.u32(0), 0xffffffff)
        self.assertEqual(n.string(0x584954), b'%s')
        self.assertEqual(n.string(0x5847f8), b'%s%s')
        self.assertEqual(n.string(0x585bc8), b'%s\\%s')

    def test_missing_record_has_no_literal_fallback(self):
        # Explicit counterfactual fixture; current pinned source is never edited.
        n = NativeWorldUIResource()
        n.plain_csv = b''.join(line for line in n.plain_csv.splitlines(keepends=True)
                              if not line.startswith(b'2,'))
        n.path_writes.clear()
        self.assertEqual(n.call(0x815c0, this=UI), 1)
        records = n.u32(RECORD_POINTER)
        self.assertEqual(n.u32(READER+0x121e8), CAPACITY)
        self.assertEqual(n.string(records+PATH_OFFSET), b'')
        self.assertFalse(n.path_writes)
        self.assertFalse(n.handles)

    def test_pinned_call_targets_and_handle_handoff(self):
        n = self.native
        for call, target in ((0x815fb, 0x54720), (0x54800, 0x51ae0),
                             (0x64cc2, 0x12f550), (0x64cd2, 0x147af7),
                             (0x64ce1, 0x60a90), (0x60acc, 0x29820),
                             (0x64d0d, 0x1081c0), (0x64f4b, 0x1081c0)):
            code = bytes(n.vm.mem_read(BASE+call, 5))
            self.assertEqual(code[0], 0xe8)
            self.assertEqual(call+5+struct.unpack('<i', code[1:])[0], target)
        self.assertEqual(bytes(n.vm.mem_read(BASE+0x64cf2, 2)), b'\x8b\xf0')
        self.assertEqual(bytes(n.vm.mem_read(BASE+0x64f3f, 1)), b'\x56')


if __name__ == '__main__':
    unittest.main()
