"""C++ 2A -> original actor/resources -> actual CAN/HMD scene and projection."""
from pathlib import Path
import json
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_world_scene import (
    NativeWorldScene, MAP_MANAGER, SCENE_BRIDGE, WORLD, ACTOR, UI, MESSAGES,
    CAN_PATH, INDOOR_PATH, CWD, SCRATCH)
from tools.strike_lab.indoor_navigation import parse_hmd
import test_current_world_entry as entry


class CurrentWorldSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entry.CurrentWorldEntryTests.setUpClass()
        wire = entry.CurrentWorldEntryTests()
        cls.body = wire.decode(wire.vm(), wire.wire(217))[3:-1]
        cls.native = NativeWorldScene()
        cls.indoor = cls.native.enter_scene(cls.body)
        cls.initial_visits = list(cls.native.scene_visits)

    def test_all_catalog_rows_loaded_with_original_tokenizer_and_writer(self):
        n = self.native
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(MESSAGES+0xd2aba, 2))[0], 144)
        self.assertEqual(n.u32(MESSAGES+0xd2abc), n.catalog_records)
        for ordinal, row in enumerate(n.catalog):
            raw = bytes(n.vm.mem_read(n.catalog_records+ordinal*0x1a4, 0x1a4))
            fields = [bytes.fromhex(field) for field in row['raw_fields_hex']]
            for column, offset in ((0, 0), (1, 0x10), (2, 0x20),
                                   (8, 0x30), (9, 0x70), (10, 0xb0)):
                self.assertEqual(raw[offset:offset+len(fields[column])+1], fields[column]+b'\0')
            self.assertEqual(struct.unpack_from('<H', raw, 0xf0)[0], row['packed_selector'])
            self.assertEqual(struct.unpack_from('<I', raw, 0xf4)[0],
                             row['kind'] | (row['catalog_x'] << 2) | (row['catalog_y'] << 17))
            self.assertEqual(struct.unpack_from('<3H', raw, 0xf8),
                             (row['layer_width'], row['layer_height'], row['layers_per_row']))
            for index, field in enumerate(fields[14:]):
                self.assertEqual(raw[0xfe+index*16:0xfe+index*16+len(field)+1], field+b'\0')
            self.assertEqual(n.call(0x59d80, row['area'], row['scene'], this=MESSAGES),
                             n.catalog_records+ordinal*0x1a4)
        self.assertEqual(n.call(0x59d80, 2, 15, this=MESSAGES), 0)

    def test_actor_to_can_loader_preserves_actual_native_tables_and_paths(self):
        n = self.native
        self.assertTrue(n.scene_loaded)
        self.assertEqual(n.u32(WORLD+0xa7e05dc), SCENE_BRIDGE)
        self.assertEqual(n.u32(SCENE_BRIDGE+0xbc), MAP_MANAGER)
        self.assertEqual(struct.unpack('<4I', n.vm.mem_read(ACTOR, 16)), (217, 1, 17, 13))
        self.assertEqual(n.u32(ACTOR+0x40), 30)
        self.assertEqual(n.next_slot, 8)
        self.assertEqual(n.scene_attempts, [CAN_PATH, INDOOR_PATH+'groceryl.hmdz',
                                           INDOOR_PATH+'groceryl.hmd', INDOOR_PATH+'grol.romz'])
        count = struct.unpack_from('<I', n.can, 8)[0]
        self.assertEqual(count, 36)
        self.assertEqual(n.u32(MAP_MANAGER+0x126c), count)
        for index in range(count):
            pointer = n.u32(MAP_MANAGER+0x1270+index*4)
            self.assertEqual(bytes(n.vm.mem_read(pointer, 64)), n.can[12+64*index:76+64*index])
        self.assertEqual(n.u32(MAP_MANAGER+0x1068), 130)
        self.assertEqual(bytes(n.vm.mem_read(MAP_MANAGER+0x106c, 260)), n.can[16+64*count:])
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(MAP_MANAGER+0x106c+15*2, 2))[0], 12)
        self.assertEqual([rva for rva in self.initial_visits if rva != 0x59d80],
                         [0x44f70, 0xc3ea0, 0x48300, 0x37900, 0x49330])

    def test_original_ui_bounds_and_caller_projection_are_not_stubs(self):
        n = self.native
        base = next(row for row in n.catalog if (row['area'], row['scene']) == (2, 0))
        self.assertEqual(struct.unpack('<2I', n.vm.mem_read(UI+0x8aa30, 8)),
                         (base['catalog_x'], base['catalog_y']))
        self.assertEqual(struct.unpack('<2I', n.vm.mem_read(WORLD+0x224, 8)), (17, 13))
        # Actual caller increments grid y before 49330, obtaining cell interior.
        self.assertEqual(struct.unpack('<2i', n.vm.mem_read(WORLD+0x21c, 8)), (1240, 540))
        self.assertEqual(n.u32(MAP_MANAGER+0x30), 2)
        self.assertEqual(n.u32(MAP_MANAGER+0x34), 11)
        n.call(0x493c0, 1240, 540, SCRATCH+0x1000, SCRATCH+0x1004, this=MAP_MANAGER)
        self.assertEqual(struct.unpack('<2i', n.vm.mem_read(SCRATCH+0x1000, 8)), (17, 13))

    def test_real_scene_models_grid_rom_and_resource_coexistence(self):
        n, indoor = self.native, self.indoor
        self.assertEqual(n.u32(MAP_MANAGER+0x1030), indoor)
        asset = parse_hmd(n.hmd)
        self.assertEqual(n.u32(indoor+0xac), len(asset['models']))
        for index, model in enumerate(asset['models']):
            pointer = n.call(0x4c6f0, index, this=indoor+0x98)
            self.assertNotEqual(pointer, 0)
            for frame, grid in enumerate(model['grids']):
                data, width, height = struct.unpack('<3I', n.vm.mem_read(pointer+0x4c+36*frame, 12))
                self.assertEqual((width, height), (grid['width'], grid['height']))
                self.assertEqual(bytes(n.vm.mem_read(data, width*height)), bytes(grid['cells']))
        pointer, width, height = struct.unpack('<3I', n.vm.mem_read(indoor+0x8c, 12))
        expected = json.loads((ROOT/'artifacts/world-atlas/indoor-2-15.json').read_text())
        self.assertEqual((width, height), (31, 31))
        self.assertEqual(bytes(n.vm.mem_read(pointer, width*height)),
                         bytes.fromhex(expected['grid']['cells_hex']))
        self.assertEqual([n.u32(indoor+0x2c4+offset) for offset in (0, 4, 0x88, 0x108c)],
                         [6974, 1, 2, 2])
        self.assertEqual(len(n.parser_inputs), 9)
        self.assertEqual(n.parser_inputs[-1], ('grol.romz', 0, len(n.decoded['grol.romz'])))
        self.assertNotEqual(n.u32(indoor+0x2a2f0c), 0)
        self.assertFalse(n.handles)
        self.assertTrue(n.locks)
        self.assertTrue(all(depth == 0 for depth in n.locks.values()))
        self.assertEqual(n.u32(0), 0xffffffff)

    def test_original_cold_preload_is_joined_before_actor_and_scene(self):
        n = self.native
        self.assertTrue(n.cold_preload_enabled)
        self.assertEqual(n.bank_visits.count(0x61ad0), 1)
        self.assertEqual(n.bank_visits.count(0x616a0), 1)
        self.assertEqual(n.bank_visits.count(0x60c60), 1)
        self.assertEqual(n.bank_visits.count(0x606d0), 2)
        self.assertNotIn(0x60731, n.bank_visits)
        self.assertEqual(n.tick_calls, [0, 0])
        self.assertEqual(n.bank_state(0)['next_slot'], 8)
        self.assertEqual(n.parser_inputs[:3], [
            ('data2/rom/npc/npc2401.romz', 0, 23139),
            ('data2/rom/npc/npc2721.romz', 1, 330378),
            ('data2/rom/npc/npc2643.romz', 2, 56146)])
        self.assertEqual([item[1] for item in n.parser_inputs[3:8]], [3, 4, 5, 6, 7])
        self.assertEqual(n.u32(ACTOR+0x30), 7)
        self.assertEqual(n.u32(WORLD+0xa7f2f68), 2)
        self.assertEqual(n.manager, WORLD+0xaa364b8)

    def test_reject_other_scene_and_repeat_before_additional_native_work(self):
        n = self.native
        before = (len(n.visits), len(n.scene_visits), len(n.opens), n.next_slot)
        bad = [self.body[:length] for length in range(36)] + [self.body+b'\0']
        for offset, value in ((24, 0), (24, 3), (25, 0), (28, 0x19)):
            changed = bytearray(self.body)
            changed[offset] = value
            bad.append(bytes(changed))
        for body in bad:
            with self.assertRaises(ValueError):
                n.enter_scene(body)
        with self.assertRaisesRegex(ValueError, 'Fresh scene'):
            n.enter_scene(self.body)
        self.assertEqual((len(n.visits), len(n.scene_visits), len(n.opens), n.next_slot), before)

    def test_source_identity_rejected_before_catalog_allocation(self):
        n = self.native
        original = Path.read_bytes
        def changed(path):
            raw = original(path)
            return raw[:-1]+bytes([raw[-1] ^ 1]) if path.name.lower() == 'gamedata.csvz' else raw
        before = (n.heap, len(n.scene_visits), n.catalog_records)
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'Pinned map catalog changed'):
                n._load_catalog()
        self.assertEqual((n.heap, len(n.scene_visits), n.catalog_records), before)

    def test_wrong_can_magic_rejected_by_real_loader_on_fresh_manager(self):
        n = self.native
        manager = 0x7420000
        n._map_rw(manager, 0x2000)
        n.call(0x42a60, this=manager)
        original = n.scene_files[CAN_PATH]
        n.scene_files[CAN_PATH] = b'NOTACAN!'+original[8:]
        path = CWD+b'\\'+CAN_PATH.replace('/', '\\').encode()
        n.vm.mem_write(SCRATCH, path+b'\0')
        try:
            self.assertEqual(n.call(0x44f70, SCRATCH, this=manager), 0)
            self.assertEqual(bytes(n.vm.mem_read(manager+0x1068, 0x608)), bytes(0x608))
            self.assertFalse(n.handles)
        finally:
            n.scene_files[CAN_PATH] = original


if __name__ == '__main__':
    unittest.main()
