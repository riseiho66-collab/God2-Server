"""Formal frame context -> normal initializer with actual native resources."""
from pathlib import Path
import struct
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_battle_bootstrap as boot
from tools.strike_lab import current_battle_entry as entry
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_EAX, UC_X86_REG_ECX


class CurrentBattleBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.first, cls.second = 0x12345678, 0x89abcdff
        record = b'\x82' + struct.pack('<II', cls.first, cls.second)
        following = b'\x83' + bytes(14)
        executable = ROOT / 'build/tests/Release/recovered-world-frame.exe'
        wire = bytes.fromhex(subprocess.check_output(
            [str(executable), '--encode', (record+following).hex()], text=True, timeout=10).strip())
        received = entry.world_entry(record, closed_ui=True, queued_suffix=following, wire_frame=wire)
        if received.stop != entry.RETURN:
            raise AssertionError('Original world receiver did not return')
        cls.context = bytes(received.vm.mem_read(entry.CONTEXT, 0x3ec))
        cls.display = bytearray(b'\xa7' * boot.DISPLAY_STATE_SIZE)
        struct.pack_into('<II', cls.display, 0, 640, 480)
        cls.source = bytearray(b'\xb6' * boot.SOURCE_STATE_SIZE)
        struct.pack_into('<II', cls.source, 0x84, 913, 577)
        cls.owner_record = bytes.fromhex('3bd32c69963412c7d8697a8b9cadbecfd07e9ca3f5e1f28394')
        cls.character_row = b'\x30\x9c' + b'Probe100\0'.ljust(16, b'\x7d') + b'\x02'
        cls.learned_record = b'\x34\x64\x00\x01'
        instance_codec = ROOT / 'build/tests/Release/recovered-instance-update.exe'
        encoded = subprocess.run([str(instance_codec), '--batch'],
            input=cls.owner_record.hex() + '\n', text=True, capture_output=True, check=True, timeout=10)
        if encoded.stdout.split()[0] != cls.owner_record.hex():
            raise AssertionError('Formal instance codec changed input')
        cls.boot = boot.NativeBattleBootstrap(cls.context, bytes(cls.display), bytes(cls.source),
                                             owner_record=cls.owner_record, owner_catalog=True,
                                             character_row=cls.character_row,
                                             learned_records=(cls.learned_record,))
        cls.n = cls.boot.native
        with patch.object(cls.n, 'run', wraps=cls.n.run) as run:
            cls.boot.initialize()
        cls.runs = run.call_args_list

    def test_one_normal_entry_through_all_real_calls_and_next_boundary(self):
        n, b = self.n, self.boot
        self.assertEqual(len(self.runs), 1)
        self.assertEqual(self.runs[0].args, (0x1112c0, 0x11bc2a))
        self.assertEqual(n.vm.reg_read(UC_X86_REG_EIP), boot.BASE + boot.CHARACTER_BOUNDARY)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_ESP), boot.SP - 0x54)
        self.assertTrue(b.completed_prefix)
        for rva in (0x1112c0, 0x181b7, 0x11d377, 0x11fd6d, 0x1ad2d,
                    0x1114aa, 0x11fbf0, 0x11db47, 0x1081be, 0x1082f0, 0x11f95a):
            self.assertEqual(b.counts[rva], 1, hex(rva))
        self.assertEqual(b.counts[0x1adcd], 2)
        self.assertEqual(b.counts[0x11fff3], 168)
        self.assertEqual(b.counts[0x205e0], 33)
        self.assertEqual(b.reset_counts[0x1afe0], 29)
        self.assertEqual(b.reset_counts[0x1b560], 25)
        self.assertEqual(b.reset_counts[0x1fe00], 2)
        for rva in (0x34650, 0x34680, 0x188c0, 0x343b0, 0x35fa0,
                    0x104160, 0x1041a0, 0x107ca0, 0x1e560):
            self.assertEqual(b.counts[rva], 1, hex(rva))
        self.assertEqual(b.reset_counts[0x1e3d0], 2)

    def test_loaded_resources_and_native_checkpoint_are_retained(self):
        n, b = self.n, self.boot
        self.assertEqual(n.battle, boot.BATTLE)
        self.assertEqual(n.manager, boot.MANAGER)
        self.assertEqual(b.checkpoint, 10)
        self.assertEqual(n.u32(n.names+0x404), 10)
        self.assertEqual(n.u32(n.names+0x40c), 10)
        self.assertEqual(n.u32(boot.BATTLE+0x83458), n.records)
        self.assertEqual(b.registry, [boot.RENDERER, boot.OWNER_RENDERER] + [0]*18)
        self.assertEqual([n.u32(n.records+0x108*i) for i in range(10)], b.handles)
        self.assertEqual(n.u32(boot.BATTLE+0xa9df744), b.handles[0])
        self.assertEqual(n.u32(boot.BATTLE+0xa9df748), b.handles[9])
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(boot.BATTLE+0xa9405a4, 2))[0], b.handles[7])
        self.assertEqual(struct.unpack('<3H', n.vm.mem_read(boot.BATTLE+0xa924c88, 6)),
                         (b.handles[8], 0x3b, 0x48))
        self.assertEqual(n.u32(0), 0xffffffff)
        self.assertFalse(n.handles)

    def test_formal_frame_context_survives_normal_initializer(self):
        n = self.n
        self.assertEqual(n.u32(boot.BATTLE+0x3c), self.first)
        self.assertEqual(n.u32(boot.BATTLE+0x40), self.second)
        self.assertEqual(n.u32(boot.BATTLE+0x70), self.first)
        self.assertEqual(n.u32(boot.BATTLE+0x74), self.second)
        self.assertEqual(n.u32(boot.BATTLE+0xa9ea4c8), 1)
        self.assertEqual(bytes(n.vm.mem_read(boot.CONTEXT, 0x3ec)), self.context)
        self.assertEqual(n.u32(boot.QUEUE+8), 0)
        self.assertEqual(n.u32(boot.QUEUE+12), 0)
        self.assertEqual(bytes(n.vm.mem_read(boot.SOURCE, len(self.source))), self.source)
        self.assertEqual(struct.unpack('<4I', n.vm.mem_read(boot.DISPLAY+0x18, 16)), (0, 0, 913, 577))

    def test_real_program_messages_reach_original_ui_strings(self):
        n = self.n
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(boot.MESSAGES+0xb2c6c, 2))[0], 1080)
        rows = {int(bytes.fromhex(row['fields_hex'][0])): row for row in self.boot.message_rows}
        ui = boot.MANAGER + 0x310
        for message_id, offset in ((738, 0xa7e00ae), (742, 0xa7e00ce),
                                   (743, 0xa7e00ee), (750, 0xa7e010e)):
            expected = bytes.fromhex(rows[message_id]['fields_hex'][1])
            self.assertTrue(expected)
            self.assertEqual(n.string(n.u32(self.boot.message_pointers + (message_id-1)*4)), expected)
            self.assertEqual(n.string(ui+offset), expected)
        # Resource heap and the large UI object cannot alias each other.
        self.assertLess(n.heap_limit, ui)
        self.assertEqual(n.u32(ui+0xc), boot.MESSAGES)

    def test_sprites_and_record_slots_created_without_fake_returns(self):
        n = self.n
        strip = boot.MANAGER+0xa7fbc80
        self.assertEqual(struct.unpack('<25H', n.vm.mem_read(strip+6, 50)), tuple(range(25)))
        self.assertEqual(struct.unpack('<3I', n.vm.mem_read(boot.BATTLE+0xa9e9c1c, 12)), (25, 26, 27))
        for index in range(168):
            self.assertEqual(n.u32(boot.MANAGER+0x38+4*index), boot.ARENA+0xecc*index)
        # The preceding16 bytes are the last two native coordinate pairs.
        self.assertEqual(boot.CONTROL_POSITIONS + 224, boot.ARENA)
        self.assertEqual(bytes(n.vm.mem_read(boot.ARENA - 16, 16)), self.boot.control_positions[-16:])
        self.assertEqual(boot.ATTACHMENTS + 28 * 0x2c, boot.SELECTOR - 4)
        self.assertEqual(bytes(n.vm.mem_read(boot.SELECTOR - 4, 4)), b'\xa5' * 4)
        for at in (boot.SOURCE-16, boot.SOURCE+len(self.source),
                   boot.DISPLAY-16, boot.DISPLAY+len(self.display)):
            self.assertEqual(bytes(n.vm.mem_read(at, 16)), b'\xa5'*16)

    def test_invalid_snapshots_and_reentry_fail_closed(self):
        for context, display, source in ((b'', bytes(self.display), bytes(self.source)),
                                        (self.context, b'', bytes(self.source)),
                                        (self.context, bytes(self.display), b'')):
            with self.assertRaises(ValueError):
                boot.NativeBattleBootstrap(context, display, source)
        with self.assertRaises(ValueError):
            self.boot.initialize()
        for record in (b'', self.owner_record[:-1], self.owner_record + b'\0',
                       b'\x3a' + self.owner_record[1:], self.owner_record[:2] + b'\x2b' + self.owner_record[3:]):
            with self.assertRaises(ValueError):
                boot.NativeBattleBootstrap(self.context, bytes(self.display), bytes(self.source), owner_record=record)

    def test_mouse_and_control_reset_preserves_unowned_bytes(self):
        n = self.n
        mouse = bytearray(b'\xa5' * boot.MOUSE_SIZE)
        mouse[:0x12008] = bytes(0x12008)
        mouse[0x12010:] = bytes(0x20)
        self.assertEqual(self.boot.reset_snapshots['mouse'], mouse)
        controls = bytearray(b'\xa5' * boot.CONTROLS_SIZE)
        for offset, value in ((0, boot.MOUSE), (4, boot.BRIDGE), (8, boot.RENDERER),
                              (0x18, 1), (0x1c, self.boot.handles[0])):
            struct.pack_into('<I', controls, offset, value)
        for index in range(128):
            at = 0x20 + index * 0xe8
            for offset in (0, 8, 0x20, 0x24, 0x3c, 0x40, 0x44, 0x4c, 0x50):
                struct.pack_into('<I', controls, at + offset, 0)
            for offset in (0xc, 0x28, 0xd4, 0xd8, 0xdc):
                struct.pack_into('<I', controls, at + offset, 0xffffffff)
            controls[at + 0x2c] = 0
            struct.pack_into('<I', controls, 0x7420 + index * 0x60 + 0x5c, 0)
        controls[0xa420:0xa43c] = bytes(0x1c)
        self.assertEqual(bytes(n.vm.mem_read(boot.CONTROLS, len(controls))), controls)
        for at in (boot.MOUSE - 16, boot.MOUSE + boot.MOUSE_SIZE,
                   boot.CONTROLS + boot.CONTROLS_SIZE):
            self.assertEqual(bytes(n.vm.mem_read(at, 16)), b'\xa5' * 16)

    def test_panels_reset_and_resource_binding_are_original(self):
        n = self.n
        expected = bytearray(b'\xa5' * boot.PANELS_SIZE)
        struct.pack_into('<4I', expected, 0, boot.BRIDGE, boot.MOUSE,
                         boot.RENDERER, 0xa5a5a5a5)
        struct.pack_into('<HHI', expected, 0x10, 0, 0x61, 0)
        for index in range(128):
            at = 0x818 + index * 0x2a08
            struct.pack_into('<H', expected, at, 0)
            for offset in (4, 0xa, 0x46):
                struct.pack_into('<H', expected, at + offset, 0xffff)
            for offset in (0x14, 0x15, 0x3c):
                expected[at + offset] = 0
            for child in range(106):
                child_at = at + 0xaa + child * 0x64
                expected[child_at - 0xa] = expected[child_at + 0x22] = 0
                struct.pack_into('<2H', expected, child_at, 0xffff, 0xffff)
            slot = 0x18 + index * 0x10
            struct.pack_into('<H', expected, slot, 0xffff)
            struct.pack_into('<I', expected, slot + 4, 10000)
            struct.pack_into('<H', expected, slot + 8, 0xffff)
        struct.pack_into('<H', expected, 0x150c18, 28)
        expected[0x150c1a:0x150c22] = b'\xff' * 8
        expected[0x150c24:0x150c34] = n.vm.mem_read(0x59ba70, 16)
        self.assertEqual(self.boot.reset_snapshots['panels'], expected)
        self.assertEqual(self.boot.reset_snapshots['following'],
                         b'\xff' * 14 + b'\xa5' * 2)
        self.assertEqual(bytes(n.vm.mem_read(boot.PANELS - 16, 16)), b'\xa5' * 16)
        # After the panel IDs comes the actual third list, not an outer guard.
        self.assertEqual(boot.PANELS + boot.PANELS_SIZE + 16, boot.THIRD_LIST)

    def test_control_panel_call_witnesses_and_code_bytes_are_unchanged(self):
        image = entry.pinned_image()
        for caller, callee in ((0x111614, 0x34650), (0x111638, 0x104160),
                               (0x34673, 0x34680), (0x34686, 0x18940),
                               (0x346db, 0x343d0), (0x34710, 0x35fa0),
                               (0x104196, 0x1041a0), (0x104220, 0x107ca0),
                               (0x10424e, 0x1afe0)):
            self.assertEqual(image[caller], 0xe8)
            self.assertEqual(caller + 5 + struct.unpack_from('<i', image, caller + 1)[0], callee)
        for lo, hi in ((0x1112c0, 0x111659), (0x34650, 0x34718),
                       (0x188c0, 0x18945), (0x343b0, 0x343d5),
                       (0x35fa0, 0x35fd7), (0x104160, 0x1042b6),
                       (0x107ca0, 0x107cc7), (0x10fb10, 0x10fdbf)):
            self.assertEqual(bytes(self.n.vm.mem_read(boot.BASE + lo, hi-lo)), image[lo:hi])

    def test_first_window_uses_native_rectangles_labels_and_resource_handles(self):
        n, b = self.n, self.boot
        counts = b.first_window_counts
        self.assertEqual(counts[0x10fb10], 1)
        self.assertEqual(counts[0x10fdbe], 1)
        self.assertEqual(counts[0x104ea0], 1)
        self.assertEqual(counts[0x106550], 10)
        self.assertEqual(counts[0x1057d0], 9)
        self.assertEqual(counts[0x106c70], 4)
        self.assertEqual(counts[0x1afe0], 43)
        self.assertEqual(b.first_window_rect_calls, {'copy': 24, 'offset': 23})
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(boot.PANELS + boot.PANELS_SIZE, 2))[0], 0)
        self.assertEqual(struct.unpack('<3H', n.vm.mem_read(boot.PANELS + 0x818, 6)), (0x13, 0, 29))
        self.assertEqual(bytes(n.vm.mem_read(boot.PANELS + 0x830, 16)),
                         bytes(n.vm.mem_read(0x59c018, 16)))
        for index in range(23):
            child = boot.PANELS + 0x8b8 + index * 0x64
            self.assertEqual(bytes(n.vm.mem_read(child + 0x10, 16)),
                             bytes(n.vm.mem_read(0x59c028 + index * 16, 16)))
            handle = struct.unpack('<H', n.vm.mem_read(child + 0xa, 2))[0]
            self.assertEqual(handle, 0xffff if index < 10 else 20 + index)
            if 10 <= index < 19:
                pointer = n.u32(0x5b8b24 + (index - 10) * 4)
                self.assertTrue(n.string(pointer))
                self.assertEqual(n.string(child + 0x2c), n.string(pointer))
        for index in range(23, 106):
            self.assertEqual(bytes(n.vm.mem_read(boot.PANELS + 0x8b8 + index * 0x64, 1)), b'\0')
        for rva, count in ((0x10c350, 1), (0x10c540, 9), (0x10caa0, 9),
                           (0x10d1d0, 1), (0x10d540, 1), (0x10d310, 1), (0x146cf7, 9)):
            self.assertEqual(counts[rva], count, hex(rva))
        self.assertEqual(n.u32(boot.LIST_CONTROL), boot.MOUSE)
        self.assertEqual(n.u32(boot.LIST_CONTROL + 4), boot.RENDERER)
        self.assertEqual(n.u32(boot.LIST_CONTROL + 0x238), 1)
        self.assertEqual(n.u32(boot.LIST_CONTROL + 0x23c), 0xffff)
        # The third list is physically adjacent; only the four-byte gap is a guard.
        self.assertEqual(bytes(n.vm.mem_read(boot.LIST_CONTROL - 4, 4)), b'\xa5' * 4)
        self.assertEqual(bytes(n.vm.mem_read(boot.LIST_CONTROL + boot.LIST_SIZE, 4)), b'\xa5' * 4)

    def test_second_window_consumes_native_item_metadata_without_fake_lookup(self):
        n, b = self.n, self.boot
        counts = b.second_window_counts
        self.assertEqual(counts[0x10ff00], 1)
        self.assertEqual(counts[0x110210], 1)
        self.assertEqual(counts[0x9b670], 1)
        self.assertEqual(counts[0x9b720], 1)
        self.assertEqual(counts[0x104ea0], 2)
        self.assertEqual(counts[0x106550], 16)
        self.assertEqual(counts[0x1057d0], 14)
        self.assertEqual(counts[0x106c70], 8)
        self.assertEqual(counts[0x1afe0], 53)
        self.assertEqual(counts[0x146cf7], 14)
        self.assertEqual(b.second_window_rect_calls, {'copy': 40, 'offset': 38})
        self.assertEqual(struct.unpack('<2H', n.vm.mem_read(boot.PANELS + boot.PANELS_SIZE, 4)), (0, 1))
        second = boot.PANELS + 0x2a08
        self.assertEqual(struct.unpack('<3H', n.vm.mem_read(second + 0x818, 6)), (0x13, 0, 43))
        self.assertEqual(bytes(n.vm.mem_read(second + 0x830, 16)), bytes(n.vm.mem_read(0x59c2a0, 16)))
        for index in range(15):
            child = second + 0x8b8 + index * 0x64
            self.assertEqual(bytes(n.vm.mem_read(child + 0x10, 16)),
                             bytes(n.vm.mem_read(0x59c2c0 + index * 16, 16)))
            handle = struct.unpack('<H', n.vm.mem_read(child + 0xa, 2))[0]
            self.assertEqual(handle, 0xffff if index < 6 else 38 + index)
            if 6 <= index < 11:
                self.assertEqual(n.string(child + 0x2c), n.string(n.u32(0x5b8ae8 + (index - 6) * 4)))
        self.assertEqual(n.u32(boot.SECOND_LIST), boot.MOUSE)
        self.assertEqual(n.u32(boot.SECOND_LIST + 4), boot.RENDERER)
        self.assertEqual(n.u32(boot.SECOND_LIST + 0x238), 1)
        self.assertEqual(n.u32(boot.SECOND_LIST + 0x23c), 0xffff)
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(boot.BATTLE + 0xab3b8bc, 2))[0], 4660)
        self.assertEqual(bytes(n.vm.mem_read(boot.SECOND_LIST + 0x260, 16)), b'\xa5' * 16)
        owner = boot.OWNER
        self.assertEqual(owner, n.u32(boot.BATTLE + 0x20))
        self.assertEqual(owner, n.u32(boot.DESCRIPTOR + 8))
        self.assertEqual(b.owner_reads, [(0x110228, owner + 0x85a30, 2), (0x9b724, owner + 0xcff70, 4)])
        self.assertEqual(n.u32(owner + 0xcff70), b.owner_metadata.TABLE)
        self.assertEqual(b.counts[0x59a60], 1)
        for pc in (0x1e710, 0x25b60, 0x25dc0, 0x271e0):
            self.assertEqual(b.item_calls[pc], 1, hex(pc))
        self.assertEqual(b.counts[0x111660], 1)
        self.assertEqual(b.counts[0x27400], 1)
        self.assertEqual(n.u32(boot.BATTLE + 0x30), boot.DISPLAY)
        self.assertEqual(n.u32(owner + 0xcff60), boot.OWNER_RENDERER)
        self.assertEqual(n.u32(boot.OWNER_RENDERER + 0xc), boot.OWNER_BANK)
        self.assertEqual(b.item_image_args[:2], (boot.OWNER_BANK + 102 * boot.item_binding.STRIDE, 122))
        success, palette, mode, bitmap = b.item_image_result
        self.assertEqual(success, 1)
        self.assertNotEqual(bitmap, 0)
        self.assertNotEqual(palette, 0)
        handle, x, y, sprite_bitmap, sprite_mode, order, sprite_palette, clip = b.item_sprite_args
        self.assertEqual((handle, sprite_bitmap, sprite_mode, order, sprite_palette, clip),
                         (0, bitmap, mode, 0x2afa, palette, 0))
        self.assertEqual((x & 0xffff, y & 0xffff),
                         (struct.unpack('<H', n.vm.mem_read(0x59c2b0, 2))[0],
                          struct.unpack('<H', n.vm.mem_read(0x59c2b4, 2))[0]))
        self.assertEqual(struct.unpack('<H', n.vm.mem_read(boot.BATTLE + 0xab3b8ba, 2))[0], handle)
        sprite = boot.DISPLAY + 0x1258
        self.assertEqual(bytes(n.vm.mem_read(sprite, 1)), b'\x03')
        self.assertEqual(n.u32(sprite + 0x8c), bitmap)
        self.assertEqual(n.u32(sprite + 0x94), palette)
        self.assertEqual(n.u32(boot.DISPLAY + 0xf555c), sprite)

    def test_display_pool_reset_precedes_real_item_sprite_registration(self):
        n, b = self.n, self.boot
        expected = bytearray(self.display[0x1258:0x1258 + 5000 * 0xc8])
        for index in range(5000):
            offset = index * 0xc8
            expected[offset] = 0
            expected[offset + 0xa:offset + 0xc] = b'\0\0'
            expected[offset + 0xc:offset + 0x8c] = b'\xff' * 128
            struct.pack_into('<I', expected, offset + 0x90, 0x3f800000)
        self.assertEqual(b.sprite_pool_before, expected)
        self.assertEqual(bytes(n.vm.mem_read(boot.DISPLAY + 0x1258 + 0xc8, 4999 * 0xc8)), expected[0xc8:])
        image = b.owner_metadata.image
        for lo, hi in ((0x110e95, 0x110eab), (0x27400, 0x27450), (0x25b60, 0x25b9a),
                       (0x1e710, 0x1e7b2), (0x25dc0, 0x25fdb)):
            self.assertEqual(bytes(n.vm.mem_read(boot.BASE + lo, hi - lo)), image[lo:hi])

    def test_catalog_rows_and_index_share_resource_vm_and_remain_unchanged(self):
        n, b = self.n, self.boot
        m = b.owner_metadata
        self.assertIs(m.vm, n.vm)
        self.assertEqual(m.retained_key, 4660)
        self.assertEqual((b.owner_item['section'], b.owner_item['source_line'], b.owner_item['selector']),
                         ('MIS', 7636, 24))
        self.assertEqual(n.u32(m.TABLE + 0xb2d40 + 4660 * 4), m.RECORD + 16)
        self.assertEqual(bytes(n.vm.mem_read(m.RECORD, 0x1ac)), b.owner_item_bytes)
        self.assertEqual(bytes(n.vm.mem_read(m.MAPS, 0x2000)), b.owner_maps_bytes)
        raw = b.owner_item['record']
        self.assertEqual(struct.unpack_from('<3H', raw, 0x114), (51123, 37, 0xffff))
        self.assertEqual(struct.unpack('<3H', n.vm.mem_read(m.RECORD + 16 + 0x114, 6)), (51123, 102, 122))
        self.assertEqual((b.owner_item_binding['group'], b.owner_item_binding['action']), (102, 122))
        self.assertEqual(b.owner_item_binding['resolver_calls'], [(boot.OWNER_RENDERER, 102, 51123)])
        self.assertEqual(n.u32(boot.OWNER + 0xcff60), boot.OWNER_RENDERER)
        for pc in (0x59f47, 0x59420, 0x59a20, 0x59a60, 0x9b720):
            self.assertIn(pc, m.executed)
        with patch.object(b, 'owner_metadata', None):
            with self.assertRaisesRegex(AssertionError, 'Unqualified owner catalog'):
                b._owner_read(n.vm, 0, boot.OWNER + 0xcff70, 4, 0, None)

    def test_third_window_returns_with_original_controls_and_list(self):
        n, b = self.n, self.boot
        counts = b.third_window_counts
        for pc in (0x110480, 0x11062c, 0x111667):
            self.assertEqual(counts[pc], 1)
        for pc, count in ((0x104ea0, 3), (0x106550, 20), (0x1057d0, 14),
                          (0x106c70, 9), (0x1afe0, 55), (0x146cf7, 18),
                          (0x10c350, 3), (0x10c540, 18), (0x10caa0, 18),
                          (0x10d1d0, 3), (0x10d540, 3), (0x10d310, 3)):
            self.assertEqual(counts[pc], count, hex(pc))
        self.assertEqual(n.rect_calls, {'copy': 46, 'offset': 43})
        self.assertEqual([struct.unpack('<H', n.vm.mem_read(boot.BATTLE + offset, 2))[0]
                          for offset in (0xab3b1d0, 0xab3b1d2, 0xab3b1da)], [0, 1, 2])
        self.assertEqual(bytes(n.vm.mem_read(boot.PANELS + boot.PANELS_SIZE + 4, 6)), b'\xff' * 6)
        third = boot.PANELS + 2 * 0x2a08
        self.assertEqual(struct.unpack('<3H', n.vm.mem_read(third + 0x818, 6)), (0x13, 0, 53))
        self.assertEqual(bytes(n.vm.mem_read(third + 0x830, 16)), bytes(n.vm.mem_read(0x59c228, 16)))
        for index in range(106):
            child = third + 0x8b8 + index * 0x64
            if index < 5:
                self.assertEqual(bytes(n.vm.mem_read(child + 0x10, 16)),
                                 bytes(n.vm.mem_read(0x59c238 + index * 16, 16)))
                self.assertEqual(struct.unpack('<H', n.vm.mem_read(child + 0xa, 2))[0],
                                 54 if index == 4 else 0xffff)
            else:
                self.assertEqual(bytes(n.vm.mem_read(child, 1)), b'\0')
        self.assertEqual(n.u32(boot.THIRD_LIST), boot.MOUSE)
        self.assertEqual(n.u32(boot.THIRD_LIST + 4), boot.RENDERER)
        self.assertEqual(struct.unpack('<2I4H', n.vm.mem_read(boot.THIRD_LIST, 16)),
                         (boot.MOUSE, boot.RENDERER, 53, 54, 1, 0xffff))
        self.assertEqual(n.u32(boot.THIRD_LIST + 0x238), 1)
        self.assertEqual(n.u32(boot.THIRD_LIST + 0x23c), 0xffff)
        self.assertEqual(b.counts[0x11bb80], 1)
        self.assertEqual(b.third_call_this, boot.SELECTOR)
        args = b.third_call_args
        self.assertEqual(args[:7], (boot.OWNER, boot.MOUSE, boot.PANELS,
                                   boot.BATTLE + 0xab3b1d4, boot.BATTLE + 0xab3b1d6,
                                   boot.BATTLE + 0xab3b1d8, boot.CHARACTER_ROOT + 0x90))
        # The caller writes AX only and the callee reads a WORD, not full EAX.
        self.assertEqual(args[7] & 0xffff, b.handles[0])
        self.assertEqual(args[8], boot.BATTLE + 0xa924d7c)
        self.assertNotEqual(n.u32(boot.BATTLE + 0x14), boot.MESSAGES)
        self.assertEqual(n.u32(boot.BATTLE + 0x14), boot.CHARACTER_ROOT)
        image = b.owner_metadata.image
        for lo, hi in ((0x110480, 0x11062d), (0x111662, 0x1116a9)):
            self.assertEqual(bytes(n.vm.mem_read(boot.BASE + lo, hi - lo)), image[lo:hi])

    def test_native_character_writer_feeds_continuous_selector_source_reads(self):
        n, b = self.n, self.boot
        self.assertIs(b.character.vm, n.vm)
        self.assertEqual(b.character_reads, [(0x11bc18, boot.CHARACTER_ROOT + 0x15f, 1),
                                           (0x11bc21, boot.CHARACTER_ROOT + 0x164, 1)])
        self.assertEqual(b.character_prepared[0x15f], 0)
        self.assertEqual(b.character_prepared[0x164], 1)
        self.assertEqual(b.character_prepared[0x168:0x16a], b'\x64\0')
        self.assertEqual(b.character_prepared[0x16b:0x174], b'Probe100\0')
        self.assertEqual(bytes(n.vm.mem_read(boot.CHARACTER_ROOT, len(b.character_prepared))), b.character_prepared)
        self.assertEqual(bytes(n.vm.mem_read(boot.CHARACTER_PACKET, 19)),
                         self.learned_record + self.character_row[4:])
        expected = bytearray(b.selector_constructed)
        expected[4:6] = b'\0\x01'
        struct.pack_into('<H', expected, 0x2e14, b.handles[0])
        struct.pack_into('<I', expected, 0x2e28, boot.OWNER)
        struct.pack_into('<I', expected, 0x3518, boot.BATTLE + 0xa924d7c)
        for index in range(16):
            expected[0x10 + index * 0x2d0:0x2e0 + index * 0x2d0] = bytes(0x2d0)
            struct.pack_into('<III', expected, 0x2d4 + index * 0x2d0,
                             boot.CHARACTER_ROOT + 0x168 + index * 0x3ec, 0, 1)
        self.assertEqual(bytes(n.vm.mem_read(boot.SELECTOR, len(expected))), expected)
        for address, before in b.selector_neighbors.items():
            self.assertEqual(bytes(n.vm.mem_read(address, 16)), before)
        with self.assertRaisesRegex(AssertionError, 'Unqualified character'):
            b._character_read(n.vm, 0, boot.CHARACTER_ROOT + 0x90, 4, 0, None)

    def test_native_loaded_catalog_and_learned_pointer_retained_in_same_vm(self):
        n, b = self.n, self.boot
        catalog = b.skill_catalog
        self.assertEqual(catalog['definition_count'], 448)
        self.assertEqual(catalog['destination'], boot.BATTLE + 0xa924d7c)
        self.assertEqual(bytes(n.vm.mem_read(catalog['destination'], len(catalog['body']))), catalog['body'])
        self.assertIs(b.learned.vm, n.vm)
        self.assertEqual(n.u32(boot.CHARACTER_ROOT + 0x4504), catalog['destination'])
        self.assertEqual(n.u32(boot.CHARACTER_ROOT + 0xa8), 0)
        row = boot.CHARACTER_ROOT + 0x168
        self.assertEqual(n.vm.mem_read(row + 0x1f0, 1)[0], 1)
        self.assertEqual(n.u32(row + 0x258), catalog['destination'] + 4)
        self.assertEqual(b.learned_stages[0]['outcome'], 'appended')
        self.assertEqual(b.learned_stages[0]['pointer'], catalog['destination'] + 4)

    def test_learned_packets_require_explicit_character_and_exact_length(self):
        for records in ([self.learned_record], (b'',), (b'\x34\x64\0',), (b'\x35\x64\0\x01',)):
            with self.assertRaises(ValueError):
                boot.NativeBattleBootstrap(self.context, bytes(self.display), bytes(self.source),
                    owner_record=self.owner_record, owner_catalog=True,
                    character_row=self.character_row, learned_records=records)
        with self.assertRaises(ValueError):
            boot.NativeBattleBootstrap(self.context, bytes(self.display), bytes(self.source),
                                      learned_records=(self.learned_record,))

    def test_character_fixture_requires_explicit_valid_packet(self):
        for row in (b'', bytes(19), self.character_row[:-1],
                    b'\x30\x01' + self.character_row[2:],
                    self.character_row[:-1] + b'\x01'):
            with self.assertRaises(ValueError):
                boot.NativeBattleBootstrap(self.context, bytes(self.display), bytes(self.source),
                                          owner_record=self.owner_record, owner_catalog=True, character_row=row)
        with self.assertRaises(ValueError):
            boot.NativeBattleBootstrap(self.context, bytes(self.display), bytes(self.source), character_row=self.character_row)

    def test_original_packet_store_and_bootstrap_share_exact_owner_bytes(self):
        n, b = self.n, self.boot
        dest = boot.OWNER_STORE + 44 * 24
        self.assertEqual(dest, boot.OWNER + 0x85a30)
        expected = bytearray(b'\xa5' * 1232)
        expected[16 + 44 * 24:36 + 44 * 24] = self.owner_record[5:]
        self.assertEqual(bytes(n.vm.mem_read(boot.OWNER_STORE - 16, 1232)), bytes(expected))
        self.assertEqual(b.owner_store_writes,
            [(0x98e2b, dest + i, 4, struct.unpack_from('<I', self.owner_record, 5 + i)[0])
             for i in range(0, 20, 4)])
        for pc in (0x1193c2, 0x1194f9, 0x98dd0, 0x98e2b):
            self.assertIn(pc, b.owner_store_code)
        self.assertEqual(bytes(n.vm.mem_read(boot.INSTANCE_INPUT, 25)), self.owner_record)

    def test_missing_or_zero_owner_input_keeps_earlier_boundary(self):
        zero = self.owner_record[:5] + b'\0\0' + self.owner_record[7:]
        for record, catalog, boundary in ((None, False, boot.OWNER_READ_BOUNDARY),
                                         (zero, False, boot.OWNER_READ_BOUNDARY),
                                         (self.owner_record, False, boot.BOUNDARY),
                                         (self.owner_record, True, boot.CATALOG_BOUNDARY)):
            fixture = boot.NativeBattleBootstrap.__new__(boot.NativeBattleBootstrap)
            with patch.object(boot, 'BootstrapResources', side_effect=RuntimeError('before preload')):
                with self.assertRaisesRegex(RuntimeError, 'before preload'):
                    fixture.__init__(self.context, bytes(self.display), bytes(self.source),
                                     owner_record=record, owner_catalog=catalog)
            self.assertEqual(fixture.boundary, boundary)
            self.assertEqual(fixture.owner_record, record)
        for record, catalog in ((None, True), (zero, True), (self.owner_record, 1)):
            with self.assertRaises(ValueError):
                boot.NativeBattleBootstrap(self.context, bytes(self.display), bytes(self.source),
                                           owner_record=record, owner_catalog=catalog)

    def test_large_fixture_mapping_coalesces_holes_without_remapping_existing_pages(self):
        fixture = boot.NativeBattleBootstrap.__new__(boot.NativeBattleBootstrap)
        fixture.native = SimpleNamespace(vm=Uc(UC_ARCH_X86, UC_MODE_32))
        vm = fixture.native.vm
        vm.mem_map(0x12000, 4096)
        raw = b'\xa5' * 0x3000
        fixture._put(0x11020, raw)
        self.assertEqual(bytes(vm.mem_read(0x11020, len(raw))), raw)
        self.assertEqual([(start, end) for start, end, _ in vm.mem_regions()],
                         [(0x11000, 0x11fff), (0x12000, 0x12fff), (0x13000, 0x14fff)])


if __name__ == '__main__':
    unittest.main()
