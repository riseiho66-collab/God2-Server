"""Current source -> native parser/index -> native ROM -> original item writer."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.strike_lab.current_item_action_binding import (
    NativeItemActionBinding, bind_existing, ASSET, BANK, BASE, ICON, KEY,
    RENDERER, SLOT, BINDING_CODE,
)
from tools.strike_lab.recover_combat_rules import IMAGE, IMAGE_SHA256, read_pinned


class CurrentItemActionBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = NativeItemActionBinding()
        cls.result = cls.native.bind()

    def test_original_source_parser_and_index_stay_on_resource_vm(self):
        n, m = self.native, self.native.metadata
        self.assertIs(n.vm, m.vm)
        self.assertEqual(n.parsed['source_line'], 7636)
        self.assertEqual(n.parsed['key'], KEY)
        self.assertEqual(struct.unpack_from('<3H', n.parsed['record'], 0x114),
                         (ICON, 37, 0xffff))
        self.assertEqual(m.call(0x59a60, KEY), n.record)
        self.assertTrue({0x59943, 0x5994a, 0x59a20} <= m.executed)

    def test_native_rom_loader_supplies_actual_action_table(self):
        n = self.native
        self.assertEqual(n.attempts, [ASSET])
        self.assertEqual(n.opens, [ASSET])
        self.assertEqual(n.parser_inputs, [(ASSET, SLOT, 384327)])
        self.assertEqual(set(n.native_visits),
                         {0x29820, 0x1ec0, 0x2a1d0, 0x2c090, 0x2d930, 0x28740})
        self.assertEqual(n.load_result, 6539)  # Loader result is not a slot/handle.
        self.assertEqual(n.action_count, 200)
        self.assertEqual(n.u32(RENDERER + 0xc), BANK)
        pointer = n.u32(n.resource + 0x1090 + 122 * 4)
        self.assertEqual(n.u32(pointer), ICON)

    def test_original_writer_changes_only_group_action_and_guard(self):
        n, m, result = self.native, self.native.metadata, self.result
        self.assertEqual((result['initial_group'], result['initial_action']), (37, 0xffff))
        self.assertEqual((result['group'], result['action']), (102, 122))
        self.assertEqual(result['resolver_calls'], [(RENDERER, SLOT, ICON)])
        self.assertEqual(result['writes'], [
            (0x81749, n.record + 0x116, 2, 102),
            (0x81763, n.record + 0x118, 2, 122),
            (0x817b3, m.TABLE + 0xd2aa0, 4, 1),
        ])
        self.assertNotIn(0x81795, result['executed'])
        self.assertEqual(n.consume(), (102, 122))
        image = read_pinned(IMAGE, IMAGE_SHA256)
        for low, high in BINDING_CODE:
            self.assertEqual(bytes(n.vm.mem_read(BASE + low, high - low)), image[low:high])

    def test_resolver_searches_rom_ids_instead_of_accepting_an_index(self):
        n = self.native
        for icon, expected in ((51001, 0), (51122, 121), (51123, 122),
                               (51200, 199), (0, 0xffffffff),
                               (122, 0xffffffff), (51201, 0xffffffff)):
            with self.subTest(icon=icon):
                self.assertEqual(n.call(0x1ae70, SLOT, icon, this=RENDERER), expected)

    def test_original_completion_guard_prevents_second_rebase(self):
        n = self.native
        before = bytes(n.vm.mem_read(n.record - 16, 0x18c + 32))
        result = n.bind()
        self.assertEqual(result['writes'], [])
        self.assertEqual(result['resolver_calls'], [])
        self.assertEqual((result['group'], result['action']), (102, 122))
        self.assertEqual(bytes(n.vm.mem_read(n.record - 16, 0x18c + 32)), before)

    def test_rejects_a_different_catalog_or_record_without_writes(self):
        n, m = self.native, self.native.metadata
        before = bytes(n.vm.mem_read(m.TABLE, 0x100000))
        for table, record, message in ((m.TABLE + 4, n.record, 'same native catalog'),
                                       (m.TABLE, n.record + 4, 'sparse original')):
            with self.subTest(table=table, record=record):
                with self.assertRaisesRegex(ValueError, message):
                    bind_existing(n, owner=m.OWNER, table=table, record=record)
        self.assertEqual(bytes(n.vm.mem_read(m.TABLE, 0x100000)), before)


if __name__ == '__main__':
    unittest.main()
