"""Original preview 4B70/cache/FF450 over pinned RoleDoll assets, offline only."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab.current_preview_role_resources import (
    NativePreviewRoleResources, native_preview_records, PREVIEW, COMPONENTS,
    RECORDS, VIRTUAL_ROOT, KEYS, ASSETS, BANK, DIRECTORY)
from tools.strike_lab.current_preview_role_resources import (
    NativePreviewAnimationResources, NativePreviewFrameResources,
    CONTROL_TABLE, RENDERER, FLOW_PATH, BASE, SURFACE)
from tools.strike_lab.current_role_doll_resources import STRIDE
from test_current_role_doll_resources import chunks


class CurrentPreviewRoleResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = native_preview_records()
        cls.native = NativePreviewRoleResources(cls.records)
        n = cls.native
        cls.initial_cache = bytes(n.vm.mem_read(n.cache, 0x410))
        cls.initial_filenames = [bytes(n.vm.mem_read(n.u32(n.cache+4+4*i), 256))
                                 for i in range(22)]
        cls.initial_components = bytes(n.vm.mem_read(COMPONENTS, 0x2c))
        cls.initial_bank = bytes(n.vm.mem_read(BANK, 512*STRIDE))
        cls.results = [n.set_record(key, component) for key, component in
                       (('r1h000', 2), ('r1f002', 1), ('r2f002', 1), ('r2h000', 2))]
        cls.initial_visits = list(n.preview_visits)
        cls.animation = NativePreviewAnimationResources(cls.records)
        cls.frames = NativePreviewFrameResources(cls.records)

    def test_animation_table_has_native_unloaded_initialization_for_all_entries(self):
        n = self.animation
        self.assertEqual(n.animation_visits.count(0x104130), 1)
        self.assertEqual(n.animation_visits.count(0x104160), 1)
        self.assertEqual(n.animation_visits.count(0x1041a0), 1)
        for window in range(128):
            self.assertEqual(struct.unpack_from('<H', n.empty_controls, window*0x2a08)[0], 0)
            for control in range(106):
                self.assertEqual(struct.unpack_from('<H', n.empty_controls,
                                 window*0x2a08+0xaa+control*0x64)[0], 0xffff)
        self.assertEqual(n.call(0x106c30, 1, 22, this=CONTROL_TABLE) & 65535, 65535)
        self.assertEqual(n.call(0x106c30, n.window_selector, 31, this=CONTROL_TABLE) & 65535, 65535)

    def test_animation_control_handles_come_from_original_allocations_and_image_rows(self):
        n = self.animation
        self.assertEqual(n.flow_rows[0][:2], ['0', 'FlowGui.ROM'])
        self.assertEqual(n.parser_inputs[0], ('flowgui.romz', 0, 2337977))
        self.assertEqual(tuple(n.u32(BANK+o) for o in (4, 0x88, 0x108c)), (26, 76, 105))
        self.assertEqual(n.opens[0], FLOW_PATH)
        self.assertEqual(n.control_selectors, (22, 23, 24, 25))
        self.assertEqual(len(n.control_arguments), 12)
        self.assertEqual(len(n.native_handle_writes), 12)
        handles = []
        for index, (args, (destination, handle)) in enumerate(zip(n.control_arguments, n.native_handle_writes)):
            control = 19+index
            image_action, _, image_kind, _ = struct.unpack('<4h', n.vm.mem_read(BASE+0x183908+8*index, 8))
            # C97C/CA48 update AX, preserving the caller's upper EAX bits;
            # 106C70 consumes these selectors/type values as WORDs.
            self.assertEqual(args[0] & 65535, n.window_selector)
            self.assertEqual(args[1:4], (0, control, image_action))
            self.assertEqual(args[5:9], (0, 0x21, 0xff00, 1))
            self.assertEqual(args[9] & 65535, image_kind)
            self.assertEqual(args[10], 1)
            self.assertEqual(destination, CONTROL_TABLE+0x8c2+n.window_selector*0x2a08+control*0x64)
            self.assertEqual(self.word(n, destination), handle)
            self.assertLess(handle, 0x1000)
            self.assertEqual(n.call(0x106c30, n.window_selector, control, this=CONTROL_TABLE) & 65535, handle)
            handles.append(handle)
        self.assertEqual(len(set(handles)), 12)
        self.assertEqual(self.word(n, PREVIEW+0x178cd4), n.window_selector)
        self.assertEqual(n.u32(CONTROL_TABLE+8), RENDERER)
        self.assertIn(0x1afe0, n.animation_visits)

    def test_animation_continuation_uses_real_window_selector_then_ff490(self):
        n = self.animation
        for key, component in (('r1h000', 2), ('r1f002', 1), ('r2f002', 1)):
            with self.subTest(key=key):
                slot, handle = n.set_animated_record(key, component)
                self.assertLess(slot, 512)
                source_control = n.control_selectors[component]
                field = CONTROL_TABLE+0x8c2+n.window_selector*0x2a08+source_control*0x64
                self.assertEqual(handle, self.word(n, field))
                self.assertLess(handle, 0x1000)
                self.assertEqual(n.lookup_arguments[-1], (n.window_selector, source_control))
                self.assertEqual(self.word(n, COMPONENTS+4+6*component), slot)
                self.assertEqual(self.word(n, COMPONENTS+6+6*component), handle)
                before = (len(n.opens), n.animation_visits.count(0x1afe0), len(n.native_handle_writes))
                self.assertEqual(n.set_animated_record(key, component), (slot, handle))
                self.assertEqual((len(n.opens), n.animation_visits.count(0x1afe0), len(n.native_handle_writes)), before)
        self.assertEqual(n.animation_visits.count(0xff490), 6)
        self.assertFalse(n.handles)
        self.assertEqual(n.u32(0), 0xffffffff)
        self.assertTrue(n.locks)
        self.assertTrue(all(depth == 0 for depth in n.locks.values()))

    def test_animation_flow_source_changes_fail_before_control_creation(self):
        original = Path.read_bytes

        def changed(path):
            data = original(path)
            return data[:-1]+bytes([data[-1] ^ 1]) if path.name.lower() == 'flowcomm.csvz' else data

        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(ValueError, 'Pinned FlowComm source changed'):
                NativePreviewAnimationResources(self.records)

    def fresh(self):
        return NativePreviewRoleResources(self.records)

    def test_frame_binding_executes_preview_caller_and_native_reset(self):
        n = self.frames
        self.assertEqual(n.frame_visits[:2], [0xff3c0, 0xff420])
        self.assertEqual(n.bound_components[4:28], b'\xff'*24)
        self.assertEqual(struct.unpack_from('<I', n.bound_components, 0x28)[0], RENDERER)
        self.assertEqual(n.u32(PREVIEW+0x15e80), n.u32(CONTROL_TABLE+8))
        self.assertEqual(n.frame_visits.count(0xffad0), 1)
        self.assertEqual(bytes(n.vm.mem_read(COMPONENTS+0x20, 4)),
                         bytes(n.vm.mem_read(BASE+0x1837e0, 2))+
                         bytes(n.vm.mem_read(BASE+0x1837e4, 2)))
        self.assertEqual(n.component_block, bytes.fromhex('0000000000008000'))
        for component in (0, 3):
            self.assertEqual(self.word(n, COMPONENTS+4+component*6), 0xffff)

    def test_frame_consumers_match_source_actions_pools_images_and_step_wrap(self):
        n = self.frames
        before = len(n.frame_visits)
        for key in ('r1h000', 'r1f002', 'r2f002'):
            with self.subTest(key=key):
                component = KEYS[key][1]
                slot, handle = n.select_component(key)
                obj = n.component_object(component)
                self.assertEqual(obj, RENDERER+0x10+handle*0x290)
                if key == 'r1h000':
                    # Control creation had a FlowGui action, but selection alone
                    # has not installed the new RoleDoll action in the object.
                    self.assertNotEqual(n.u32(obj+0x34), BANK+slot*STRIDE)
                    with self.assertRaisesRegex(ValueError, 'not been initialized'):
                        n.step_component(component)
                n.start_preview_action()
                bank = BANK+slot*STRIDE
                action = n.u32(bank+0x1090+4*6)
                self.assertEqual(n.u32(obj+0x34), bank)
                self.assertEqual(n.u32(obj+0x38), action)
                self.assertEqual(self.word(n, COMPONENTS+0x26), 6)
                self.assertEqual(bytes(n.vm.mem_read(obj+1, 1)), b'\x06')
                name = self.records[key][:30].split(b'\0')[0].decode()
                source, ordinal = iter(chunks(n.decoded[name])), -1
                for tag, body in source:
                    if tag == b'ACT_DATA':
                        ordinal += 1
                        if ordinal == 6:
                            break
                self.assertEqual(ordinal, 6)
                self.assertEqual(bytes(n.vm.mem_read(action, 24)), body[:24])
                step_count, pool_count = struct.unpack_from('<2I', body, 16)
                steps = []
                for _ in range(step_count):
                    tag, data = next(source)
                    self.assertEqual(tag, b'ACT_STEP')
                    self.assertEqual(len(data), 10)
                    steps.append(data)
                pools = []
                for _ in range(pool_count):
                    tag, data = next(source)
                    self.assertEqual(tag, b'ACT_POOL')
                    pools.append(data)
                    self.assertEqual(next(source)[0], b'ACTBLOCK')
                loads = (len(n.opens), len(n.parser_inputs), len(n.allocations))
                for step in range(step_count+1):
                    if step:
                        n.step_component(component)
                    index = step % step_count
                    event = steps[index]
                    self.assertEqual(self.word(n, obj+0x1a), index)
                    pointer = n.u32(action+0x30+4*index)
                    self.assertEqual(n.u32(obj+0x3c), pointer)
                    self.assertIn((obj, pointer, event), n.frame_events)
                    self.assertEqual(bytes(n.vm.mem_read(pointer, 10)), event)
                    self.assertEqual(self.word(n, obj+0x28), event[2])
                    self.assertEqual(self.word(n, obj+0x2a), event[2])
                    self.assertEqual(self.word(n, obj+0x30), event[4] & 31)
                    pool = n.u32(action+0x630+4*event[3])
                    self.assertEqual(n.u32(obj+0x48), pool)
                    self.assertEqual(bytes(n.vm.mem_read(pool, 9)), pools[event[3]][:9])
                    image_index = struct.unpack_from('<H', pools[event[3]], 6)[0]
                    image = n.u32(bank+0x8c+4*image_index)
                    self.assertEqual(n.u32(obj+0x40), image)
                    self.assertEqual(n.u32(obj+0x44), n.u32(bank+8))
                    command = self.word(n, obj+0xe)
                    self.assertLess(command, 0x1388)
                    self.assertEqual(n.u32(SURFACE+0x12e4+command*0xc8), image)
                    self.assertEqual(n.u32(SURFACE+0x12ec+command*0xc8), n.u32(bank+8))
                self.assertEqual((len(n.opens), len(n.parser_inputs), len(n.allocations)), loads)
        visits = n.frame_visits[before:]
        self.assertEqual(visits.count(0xffa20), 3)
        self.assertEqual(visits.count(0xff8e0), 3)
        self.assertEqual(visits.count(0xffa60), 3)
        self.assertEqual(visits.count(0x1bf30), 5)
        self.assertEqual(visits.count(0x1ae20), 5)
        self.assertEqual(visits.count(0x1c360), 25)
        self.assertFalse(n.handles)
        self.assertEqual(n.u32(0), 0xffffffff)
        self.assertTrue(all(depth == 0 for depth in n.locks.values()))

    def test_frame_unqualified_components_and_keys_fail_closed(self):
        n = self.frames
        for component in (0, 3, 4, -1):
            with self.assertRaisesRegex(ValueError, 'qualified'):
                n.step_component(component)
        with self.assertRaisesRegex(ValueError, 'Qualified'):
            n.select_component('r1b000')

    def word(self, n, pointer):
        return struct.unpack('<H', n.vm.mem_read(pointer, 2))[0]

    def test_original_cache_initialization_allocates_22_empty_filename_buffers(self):
        n = self.native
        self.assertEqual(n.u32(PREVIEW+0x178cdc), n.cache)
        self.assertEqual(struct.unpack_from('<3I', self.initial_cache, 0x404), (0, 22, 0))
        pointers = struct.unpack_from('<256I', self.initial_cache, 4)
        self.assertEqual(len(set(pointers[:22])), 22)
        self.assertTrue(all(pointers[:22]))
        self.assertEqual(pointers[22:], (0,)*234)
        self.assertEqual(self.initial_filenames, [bytes(256)]*22)
        for pointer in pointers[:22]:
            self.assertEqual(n.allocations[pointer], 256)
        self.assertEqual(self.initial_components[4:28], b'\xff'*24)
        self.assertEqual(n.u32(PREVIEW+0x15e7c), BANK)

    def test_preview_wrapper_loads_real_roms_and_returns_slots_not_actindices(self):
        n = self.native
        self.assertEqual(self.results, [0, 1, 2, 0])
        self.assertEqual(n.u32(n.cache+0x404), 3)
        self.assertEqual(n.parser_inputs, [(name, slot, len(n.decoded[name]))
                                          for slot, name in enumerate(ASSETS)])
        self.assertEqual(n.opens, [DIRECTORY+name for name in ASSETS])
        for slot, (name, expected) in enumerate(zip(ASSETS, ((4201, 8, 1, 19),
                                                          (4001, 8, 17, 19),
                                                          (0, 8, 22, 19)))):
            with self.subTest(name=name):
                self.assertEqual(struct.unpack_from('<I', self.initial_bank, slot*STRIDE)[0], 0xffffffff)
                self.assertEqual(tuple(n.u32(BANK+slot*STRIDE+offset)
                                       for offset in (0, 4, 0x88, 0x108c)), expected)
                filename = n.string(n.u32(n.cache+4+4*slot)).decode()
                self.assertEqual(filename.lower(), (VIRTUAL_ROOT+'\\'+
                                 (DIRECTORY+name).replace('/', '\\')).lower())
        self.assertEqual(bytes(n.vm.mem_read(BANK+3*STRIDE, 509*STRIDE)), self.initial_bank[3*STRIDE:])
        for rva in (0x29820, 0x1ec0, 0x2a1d0):
            self.assertEqual(n.native_visits.count(rva), 3)
        self.assertEqual(self.initial_visits.count(0x4b70), 4)
        self.assertEqual(self.initial_visits.count(0x4c61), 3)
        self.assertEqual(n.current_directory_calls, 1)

    def test_native_record_cache_writes_and_ff450_component_setter(self):
        n = self.native
        expected_slots = {'r1h000': 0, 'r1f002': 1, 'r2f002': 2, 'r2h000': 0}
        for key, slot in expected_slots.items():
            expected = bytearray(self.records[key])
            struct.pack_into('<H', expected, 30, slot)
            self.assertEqual(bytes(n.vm.mem_read(n.record_pointers[key], 44)), expected)
        self.assertEqual(self.initial_visits.count(0x9b45), 4)
        self.assertEqual(self.initial_visits.count(0xff450), 4)
        self.assertEqual(self.word(n, COMPONENTS+4), 0xffff)
        self.assertEqual(self.word(n, COMPONENTS+4+12), 0)
        self.assertEqual(self.word(n, COMPONENTS+4+18), 0xffff)
        before = bytes(n.vm.mem_read(COMPONENTS, 0x2c))
        n.call(0xff450, 4, 1, this=COMPONENTS)
        self.assertEqual(bytes(n.vm.mem_read(COMPONENTS, 0x2c)), before)

    def test_record_cache_hit_skips_wrapper_and_preserves_real_bank(self):
        n = self.native
        bank = bytes(n.vm.mem_read(BANK, 512*STRIDE))
        visits = len(n.preview_visits)
        parser_count, opens = len(n.parser_inputs), list(n.opens)
        self.assertEqual(n.set_record('r1f002', 1), 1)
        self.assertEqual(n.preview_visits[visits:], [0xff450])
        self.assertEqual(self.word(n, COMPONENTS+4+6), 1)
        self.assertEqual(len(n.parser_inputs), parser_count)
        self.assertEqual(n.opens, opens)
        self.assertEqual(bytes(n.vm.mem_read(BANK, 512*STRIDE)), bank)

    def test_filename_cache_is_case_insensitive_without_reloading(self):
        n = self.native
        before = bytes(n.vm.mem_read(n.cache, 0x410))
        parser_count, opens = len(n.parser_inputs), list(n.opens)
        for slot, name in enumerate(ASSETS):
            visits = len(n.preview_visits)
            self.assertEqual(n.load_wrapper(name, uppercase=True), slot)
            self.assertEqual(n.preview_visits[visits:], [0x4b70])
        self.assertEqual(bytes(n.vm.mem_read(n.cache, 0x410)), before)
        self.assertEqual(len(n.parser_inputs), parser_count)
        self.assertEqual(n.opens, opens)

    def test_missing_assets_do_not_publish_success_and_can_retry(self):
        for key in ('r1h000', 'r1f002', 'r2f002'):
            with self.subTest(key=key):
                n = self.fresh()
                name = self.records[key][:30].split(b'\0')[0].decode()
                raw = n.files.pop(DIRECTORY+name)
                initial_record = bytes(n.vm.mem_read(n.record_pointers[key], 44))
                self.assertEqual(n.set_record(key, KEYS[key][1]), 0xffff)
                self.assertEqual(n.u32(n.cache+0x404), 0)
                self.assertEqual(n.u32(BANK), 0xffffffff)
                self.assertEqual(bytes(n.vm.mem_read(n.record_pointers[key], 44)), initial_record)
                self.assertFalse(n.parser_inputs)
                self.assertEqual(n.attempts, [DIRECTORY+name]*2)
                self.assertFalse(n.handles)
                self.assertEqual(n.u32(0), 0xffffffff)
                n.files[DIRECTORY+name] = raw
                self.assertEqual(n.set_record(key, KEYS[key][1]), 0)
                self.assertEqual(n.u32(n.cache+0x404), 1)
                self.assertEqual(len(n.parser_inputs), 1)

    def test_inputs_files_seh_and_unrelated_component_fields(self):
        n = self.native
        for key in KEYS:
            with self.assertRaisesRegex(ValueError, 'component'):
                n.set_record(key, 4)
        with self.assertRaisesRegex(ValueError, 'filename'):
            n.load_wrapper('../unknown.romz')
        self.assertFalse(n.handles)
        self.assertEqual(n.u32(0), 0xffffffff)
        self.assertTrue({0x4b77, 0x4b7e, 0x4cee} <= n.seh_accesses)
        for offset in range(0x2c):
            if offset in (10, 11, 16, 17):
                continue
            self.assertEqual(n.vm.mem_read(COMPONENTS+offset, 1), self.initial_components[offset:offset+1])
        self.assertEqual(n.u32(n.cache+0x40c), 0)


if __name__ == '__main__':
    unittest.main()
