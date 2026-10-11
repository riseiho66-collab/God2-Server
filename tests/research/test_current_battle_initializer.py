"""Continuous original initializer extent; no world/TCP/live-entry claim."""
import struct
import subprocess
import unittest
from unittest.mock import patch

from tools.strike_lab import current_battle_initializer as init
from tools.strike_lab import current_battle_entry as entry
from tools.strike_lab.current_battle_entry import (
    UC_X86_REG_EIP, UC_X86_REG_EBP, UC_X86_REG_ESP, UC_X86_REG_ECX,
)


class CurrentBattleInitializerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        context = bytearray((i * 29 + 7) & 255 for i in range(0x3ec))
        struct.pack_into('<II', context, 0x28, 0x12345678, 0x9abcdeff)
        cls.context = bytes(context)
        cls.starts = []
        original_run = init.NativeRun.run

        def observe_run(n, start, *args, **kwargs):
            cls.starts.append(start)
            return original_run(n, start, *args, **kwargs)

        with patch.object(init.NativeRun, 'run', observe_run):
            cls.n = init.initialize(cls.context)

    def test_single_real_entry_and_precise_pre_call_boundary(self):
        n = self.n
        self.assertEqual(self.starts, [0x1112c0])
        self.assertEqual(n.visits[0], 0x1112c0)
        self.assertEqual(n.stop, 0x111456)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_EIP), init.BASE + 0x111456)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_ECX), init.DISPLAY)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_EBP), init.BATTLE)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_ESP), init.SP - 0x1c)
        self.assertNotIn(0x20580, n.visits)
        self.assertNotIn(0x11145b, n.visits)

    def test_explicit_display_storage_runs_all_original_resets_continuously(self):
        initial = bytearray(b'\xa7' * init.DISPLAY_STATE_SIZE)
        struct.pack_into('<II', initial, 0, 640, 480)  # Synthetic dimensions, not a server default.
        n = init.initialize(self.context, display_state=bytes(initial))
        self.assertEqual(n.stop, 0x11145b)
        self.assertEqual(n.visits[0], 0x1112c0)
        self.assertEqual(n.visits.count(0x20580), 1)
        self.assertEqual(n.visits.count(0x205a0), 32)
        for callee in (0x273c0, 0x27400, 0x27450, 0x20597):
            self.assertEqual(n.visits.count(callee), 1)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_ESP), init.SP - 0x1c)
        self.assertNotIn(0x1ad10, n.visits)
        expected = bytearray(initial)
        expected[8:8 + 31 * 16] = bytes(31 * 16)
        struct.pack_into('<II', expected, 16, 640, 480)
        for index in range(5000):
            at = 0x1258 + index * 0xc8
            expected[at] = 0
            expected[at + 0xa:at + 0xc] = bytes(2)
            expected[at + 0xc:at + 0x8c] = b'\xff' * 128
            struct.pack_into('<I', expected, at + 0x90, 0x3f800000)
        struct.pack_into('<II', expected, 0xf5558, 0, 0)
        struct.pack_into('<I', expected, 0xf66e0, 0x6900000)
        for index in range(3096):
            expected[0xf66e8 + index * 0x8c] &= 0xfc
        self.assertEqual(bytes(n.vm.mem_read(init.DISPLAY, len(expected))), expected)
        self.assertEqual(bytes(n.vm.mem_read(init.DISPLAY - 16, 16)), b'\xa5' * 16)
        self.assertEqual(bytes(n.vm.mem_read(init.DISPLAY + len(expected), 16)), b'\xa5' * 16)
        for bad in (b'', bytes(init.DISPLAY_STATE_SIZE - 1), bytearray(initial)):
            with self.assertRaisesRegex(ValueError, 'display-manager'):
                init.initialize(self.context, display_state=bad)

    def test_formal_entry_frame_context_feeds_original_initializer(self):
        # Two explicit native stages, not a claim that the intervening main loop ran.
        first, second = 0x89abcdef, 0x123456ff
        trigger = b'\x82' + struct.pack('<II', first, second)
        following = b'\x83' + bytes(14)
        binary = init.ROOT / 'build/tests/Release/recovered-world-frame.exe'
        wire = bytes.fromhex(subprocess.check_output(
            [str(binary), '--encode', (trigger + following).hex()], text=True, timeout=10).strip())
        received = entry.world_entry(trigger, closed_ui=True,
                                     queued_suffix=following, wire_frame=wire)
        self.assertEqual(received.stop, entry.RETURN)
        self.assertEqual(received.vm.reg_read(entry.UC_X86_REG_EAX), 4)
        context = bytes(received.vm.mem_read(entry.CONTEXT, 0x3ec))
        display = bytearray(b'\xa5' * init.DISPLAY_STATE_SIZE)
        struct.pack_into('<II', display, 0, 640, 480)
        initialized = init.initialize(context, display_state=bytes(display))
        self.assertEqual(initialized.stop, 0x11145b)
        self.assertEqual(initialized.get32(init.BATTLE + 0x3c), first)
        self.assertEqual(initialized.get32(init.BATTLE + 0x40), second)
        self.assertEqual(initialized.get32(init.BATTLE + 0x70), first)
        self.assertEqual(initialized.get32(init.BATTLE + 0x74), second)
        self.assertEqual(initialized.get32(init.BATTLE + 0xa9ea4c8), 1)
        self.assertEqual(bytes(initialized.vm.mem_read(init.CONTEXT, 0x3ec)), context)

    def test_original_callees_and_real_return_counts(self):
        for first, last, count in ((0x181b0, 0x181b7, 1),
                                   (0x11d350, 0x11d377, 1),
                                   (0x11fc40, 0x11fd6d, 1),
                                   (0x11e6e0, 0x11e760, 168),
                                   (0x11fde0, 0x11fff3, 168),
                                   (0x11ca30, 0x11ca5c, 168),
                                   (0x11ca90, 0x11cacc, 168),
                                   (0x11cfb0, 0x11cff8, 140),
                                   (0x12aea0, 0x12aec2, 1)):
            with self.subTest(callee=hex(first)):
                self.assertEqual(self.n.visits.count(first), count)
                self.assertEqual(self.n.visits.count(last), count)

    def test_input_and_queue_reset_preserve_unowned_bytes(self):
        n = self.n
        self.assertEqual(bytes(n.vm.mem_read(init.INPUT, 16)), b'\0' * 8 + b'\xa5' * 8)
        self.assertEqual([n.get32(init.QUEUE + i * 4) for i in range(6)],
                         [0, init.QUEUE_STORAGE, 0, 0, 0x1000, 0])
        self.assertEqual(bytes(n.vm.mem_read(init.QUEUE_STORAGE, 0x1000)), b'\xa5' * 0x1000)
        self.assertEqual(n.get32(init.DISPLAY + 0xf66e0), 0x6900000)

    def test_entry_fields_and_context_copied_on_continuous_path(self):
        n = self.n
        self.assertEqual(n.get32(init.BATTLE + 0x3c), 0x12345678)
        self.assertEqual(n.get32(init.BATTLE + 0x40), 0x9abcdeff)
        self.assertEqual(n.get32(init.BATTLE + 0x70), 0x12345678)
        self.assertEqual(n.get32(init.BATTLE + 0x74), 0x9abcdeff)
        self.assertEqual(n.get32(init.BATTLE + 0xa9ea4c8), 1)
        expected = bytearray(self.context)
        expected[9:11] = b'\xff\xff'
        expected[0x1c:0x20] = self.context[0x18:0x1c]
        struct.pack_into('<II', expected, 0x20, 3, 0)
        self.assertEqual(bytes(n.vm.mem_read(init.BATTLE + 0x48, 0x3ec)), expected)
        self.assertEqual(bytes(n.vm.mem_read(init.CONTEXT, 0x3ec)), self.context)
        self.assertEqual(n.get32(init.BATTLE + 0xa9e9c74), 0)
        for pc in (0x1113d8, 0x1113e3, 0x11140c, 0x111412, 0x111424, 0x111429):
            self.assertEqual(n.visits.count(pc), 1)

    def test_all_168_original_records_and_28_attachment_bindings(self):
        n = self.n
        for side in range(2):
            for slot in range(14):
                attachment = init.ATTACHMENTS + (side * 14 + slot) * 0x2c
                for kind in range(6):
                    index = (side * 14 + slot) * 6 + kind
                    entity = init.ARENA + index * 0xecc
                    self.assertEqual(n.get32(init.MANAGER + 0x38 + index * 4), entity)
                    self.assertEqual(bytes(n.vm.mem_read(entity + 0x1a, 2)), b'\xff\xff')
                    self.assertEqual(n.get32(entity + 0xec8), attachment)
                    flags = n.vm.mem_read(entity + 0x234, 1)[0]
                    self.assertEqual(flags, 0x40 | (side << 7) | slot)
                    self.assertEqual(bytes(n.vm.mem_read(entity + 0x278, 2)), b'\0\0')
                self.assertEqual(n.get32(attachment + 0x28), init.MANAGER_RENDERER)
                self.assertEqual(bytes(n.vm.mem_read(attachment + 4, 16)), b'\xff' * 16)
        self.assertEqual(bytes(n.vm.mem_read(init.ARENA - 16, 16)), b'\xa5' * 16)
        self.assertEqual(init.ARENA + init.ARENA_SIZE, init.ATTACHMENTS)
        self.assertEqual(bytes(n.vm.mem_read(init.ATTACHMENTS + 28 * 0x2c, 16)), b'\xa5' * 16)
        self.assertEqual(n.get32(init.MANAGER + 0x2d8), 0)
        self.assertEqual(n.get32(init.MANAGER + 0x2dc), 0)
        self.assertEqual(n.get32(init.MANAGER + 0x2e0), 1)
        self.assertEqual(n.get32(init.MANAGER + 0x2e4), 1)

    def test_missing_queue_buffer_stops_before_native_assertion(self):
        n = init.initialize(self.context, queue_allocated=False)
        self.assertEqual(n.stop, 0x11d367)
        self.assertEqual(n.visits.count(0x181b7), 1)
        self.assertNotIn(0x2c70, n.visits)
        self.assertNotIn(0x111409, n.visits)
        self.assertEqual(n.get32(init.QUEUE + 8), 0x120)
        self.assertEqual(n.get32(init.BATTLE + 0x3c), 0xa5a5a5a5)

    def test_existing_active_attachment_stops_before_unqualified_cleanup(self):
        n = init.initialize(self.context, occupied_handle=7)
        self.assertEqual(n.stop, 0x11cfe5)
        self.assertEqual(n.visits.count(0x11fff3), 1)
        self.assertNotIn(0x1b330, n.visits)
        self.assertNotIn(0x11fd6d, n.visits)
        self.assertEqual(n.get32(n.vm.reg_read(UC_X86_REG_ESP)),
                         init.MANAGER_RENDERER + 0x10 + 7 * 0x290)

    def test_original_byte_witnesses_and_code_remains_unchanged(self):
        witnesses = {
            0x181b0: '33c08901894104c3',
            0x11d356: '397e047514',
            0x11d36f: '897e08897e0c5f5ec3',
            0x1113d8: 'e8d36df0ff',
            0x1113e3: 'e868bf0000',
            0x111424: 'e817e80000',
            0x11fc51: 'b9786d0200',
            0x11fc94: 'e847eaffff',
            0x11fca4: 'e837010000',
            0x11fcb7: 'e874cdffff',
            0x11fccb: '83c10483fe06',
            0x11fce5: '83fd0e',
            0x11fcf9: '83fe02',
            0x111456: 'e825f1f0ff',
        }
        for address, hex_bytes in witnesses.items():
            raw = bytes.fromhex(hex_bytes)
            self.assertEqual(self.n.image[address:address + len(raw)], raw, hex(address))
        for lo, hi in init.RANGES:
            self.assertEqual(bytes(self.n.vm.mem_read(init.BASE + lo, hi - lo)),
                             self.n.image[lo:hi])

    def test_invalid_fixture_inputs_are_rejected(self):
        for context in (b'', bytes(0x3eb), bytes(0x3ed), bytearray(0x3ec)):
            with self.assertRaises(ValueError):
                init.initialize(context)
        for kwargs in ({'queue_allocated': 1}, {'occupied_handle': -1},
                       {'occupied_handle': 0x1000}, {'occupied_handle': True}):
            with self.assertRaises(ValueError):
                init.initialize(self.context, **kwargs)


class CurrentBattleInitializerRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = bytes(0x3ec)
        display = bytearray(b'\xa7' * init.DISPLAY_STATE_SIZE)
        struct.pack_into('<II', display, 0, 640, 480)
        cls.display = bytes(display)
        cls.pool = (bytes(range(256)) * ((init.REGISTRY_POOL_SIZE + 255) // 256)
                    )[:init.REGISTRY_POOL_SIZE]
        cls.registry = (None,) * 19 + (cls.pool,)
        cls.starts = []
        original_run = init.NativeRun.run

        def observe_run(n, start, *args, **kwargs):
            cls.starts.append(start)
            return original_run(n, start, *args, **kwargs)

        with patch.object(init.NativeRun, 'run', observe_run):
            cls.n = init.initialize(cls.context, display_state=cls.display,
                                    registry_state=cls.registry)
        cls.address = init.REGISTRY_POOL_BASE + 19 * init.REGISTRY_POOL_STRIDE

    def test_nonnull_last_registry_entry_and_original_returns(self):
        n = self.n
        self.assertEqual(self.starts, [0x1112c0])
        self.assertEqual(n.visits[0], 0x1112c0)
        self.assertEqual(n.visits.count(0x1ad16), 20)
        for address in (0x20597, 0x1ad10, 0x1ad30, 0x1adcd, 0x1ad2d, 0x111466):
            self.assertEqual(n.visits.count(address), 1, hex(address))
        self.assertEqual(n.visits.count(0x1ad3e), 4096)
        self.assertEqual(n.visits.count(0x1ad53), 4096 * 106)
        self.assertEqual(n.visits.count(0x11fff3), 168)
        self.assertEqual(n.get32(init.BATTLE + 0xa9df6c8), 0xdead0000)
        self.assertNotIn(0xdead0000, n.pages)
        self.assertEqual([n.get32(init.REGISTRY + 4 * i) for i in range(20)],
                         [0] * 19 + [self.address])

    def test_all_4096_pool_slots_exact_bytes_preservation_and_guards(self):
        expected = bytearray(self.pool)
        for index in range(4096):
            at = 0x10 + index * 0x290
            for offset in (0, 9, 0xa, 0x98, 0x99):
                expected[at + offset] = 0
            for offset in (0xe, 0x2e, 0x288):
                expected[at + offset:at + offset + 2] = b'\xff\xff'
            struct.pack_into('<H', expected, at + 0x10, index)
            for offset in (0x70, 0x254, 0x286):
                expected[at + offset:at + offset + 2] = b'\0\0'
            expected[at + 0xac:at + 0x254] = b'\xff' * 0x1a8
            expected[at + 0x256:at + 0x278] = b'\xff' * 0x22
            expected[at + 0x27a:at + 0x286] = b'\xff' * 12
        self.assertEqual(bytes(self.n.vm.mem_read(self.address, len(expected))), expected)
        self.assertEqual(bytes(self.n.vm.mem_read(self.address, 16)), self.pool[:16])
        for address in (self.address - 16, self.address + len(expected)):
            self.assertEqual(bytes(self.n.vm.mem_read(address, 16)), b'\xa5' * 16)
        for address in (init.REGISTRY - 16, init.REGISTRY + 20 * 4):
            offset = address - init.BASE
            self.assertEqual(bytes(self.n.vm.mem_read(address, 16)),
                             self.n.image[offset:offset + 16])

    def test_precise_missing_source_boundary_and_original_instruction_witnesses(self):
        n = self.n
        self.assertEqual(n.stop, 0x111469)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_EIP), init.BASE + 0x111469)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_ESP), init.SP - 0x1c)
        self.assertEqual(n.vm.reg_read(entry.UC_X86_REG_EAX), 0x6900000)
        self.assertEqual(n.get32(init.BATTLE + 0x18), 0x6900000)
        self.assertNotIn(0x6900000, n.pages)
        self.assertNotIn(0x111469, n.visits)
        self.assertNotIn(0x111484, n.visits)
        witnesses = {
            0x11145b: '8b8dc8f69d0a',
            0x111461: 'e8aa98f0ff',
            0x1ad11: 'bed84e5b00',
            0x1ad16: '8b0e85c97405e80f000000',
            0x1ad21: '83c60481fe284f5b007cea',
            0x1ad38: '8d5110',
            0x1ad4e: 'b96a000000',
            0x1ad96: '81c290020000',
            0x1ad9f: '81fe00100000',
            0x1adc9: '5f5e5d5bc3',
            0x111466: '8b45188b88880000008b9084000000',
            0x111484: 'e817f1f0ff',
        }
        for address, encoded in witnesses.items():
            raw = bytes.fromhex(encoded)
            self.assertEqual(n.image[address:address + len(raw)], raw, hex(address))
        for lo, hi in init.RANGES + init.REGISTRY_RANGES:
            self.assertEqual(bytes(n.vm.mem_read(init.BASE + lo, hi - lo)), n.image[lo:hi])

    def test_registry_snapshots_require_explicit_complete_prior_storage(self):
        for registry in ((None,) * 19, (None,) * 21, [None] * 20,
                         (None,) * 19 + (b'',),
                         (None,) * 19 + (bytearray(self.pool),)):
            with self.assertRaisesRegex(ValueError, 'registry'):
                init.initialize(self.context, display_state=self.display, registry_state=registry)
        with self.assertRaisesRegex(ValueError, 'registry'):
            init.initialize(self.context, registry_state=self.registry)


class CurrentBattleInitializerSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = bytes(0x3ec)
        display = bytearray(b'\xa7' * init.DISPLAY_STATE_SIZE)
        struct.pack_into('<II', display, 0, 640, 480)
        cls.display = bytes(display)
        source = bytearray((i * 31 + 5) & 255 for i in range(init.SOURCE_STATE_SIZE))
        struct.pack_into('<II', source, 0x84, 913, 577)
        cls.source = bytes(source)
        manager_source = bytearray((i * 17 + 11) & 255
                                   for i in range(init.MANAGER_SOURCE_STATE_SIZE))
        struct.pack_into('<I', manager_source, 0x404, 0x31415926)
        struct.pack_into('<I', manager_source, 0x40c, 0xcafebabe)
        cls.manager_source = bytes(manager_source)
        cls.starts = []
        original_run = init.NativeRun.run

        def observe_run(n, start, *args, **kwargs):
            cls.starts.append(start)
            return original_run(n, start, *args, **kwargs)

        with patch.object(init.NativeRun, 'run', observe_run):
            cls.n = init.initialize(cls.context, display_state=cls.display,
                registry_state=(None,) * 19 + (b'\xa7' * init.REGISTRY_POOL_SIZE,),
                source_state=cls.source, manager_source_state=cls.manager_source)

    def test_normal_entry_nonnull_registry_and_dimension_call_return_continuously(self):
        n = self.n
        self.assertEqual(self.starts, [0x1112c0])
        self.assertEqual(n.visits[0], 0x1112c0)
        for address in (0x1adcd, 0x1ad2d, 0x111469, 0x11146f,
                        0x111484, 0x111489, 0x11148f, 0x111495):
            self.assertEqual(n.visits.count(address), 1, hex(address))
        self.assertEqual(n.visits.count(0x205a0), 33)
        self.assertEqual(n.visits.count(0x205e0), 33)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_ESP), init.SP - 0x1c)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_EIP), init.BASE + 0x11149b)
        self.assertEqual(n.vm.reg_read(entry.UC_X86_REG_EAX), init.MANAGER_SOURCE)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_ECX), 0xcafebabe)
        self.assertEqual(n.get32(init.BATTLE + 0x14494c), init.MANAGER_SOURCE)
        self.assertNotIn((init.BATTLE + 0x83458) & ~4095, n.pages)
        self.assertNotIn(0x11149b, n.visits)
        self.assertNotIn(0x1114a3, n.visits)
        self.assertNotIn(0x11fbf0, n.visits)

    def test_dimension_call_exact_nonzero_writes_and_source_preservation(self):
        n = self.n
        writes = [w for w in n.writes if w[0] in (0x205c2, 0x205c9, 0x205d0, 0x205d7)]
        self.assertEqual(len(writes), 33 * 4)
        self.assertEqual(writes[-4:], [
            (0x205c2, init.DISPLAY + 0x18, 4, 0),
            (0x205c9, init.DISPLAY + 0x1c, 4, 0),
            (0x205d0, init.DISPLAY + 0x20, 4, 913),
            (0x205d7, init.DISPLAY + 0x24, 4, 577),
        ])
        self.assertEqual(bytes(n.vm.mem_read(init.DISPLAY + 8, 0x30)),
            struct.pack('<12I', 0, 0, 640, 480, 0, 0, 913, 577, 0, 0, 0, 0))
        self.assertEqual(bytes(n.vm.mem_read(init.SOURCE, len(self.source))), self.source)
        self.assertFalse(any(init.SOURCE <= address < init.SOURCE + len(self.source)
                             for _, address, _, _ in n.writes))
        for address in (init.SOURCE - 16, init.SOURCE + len(self.source)):
            self.assertEqual(bytes(n.vm.mem_read(address, 16)), b'\xa5' * 16)

    def test_manager_source_raw_copy_changes_exactly_one_dword(self):
        n = self.n
        expected = bytearray(self.manager_source)
        expected[0x404:0x408] = expected[0x40c:0x410]
        self.assertEqual(bytes(n.vm.mem_read(init.MANAGER_SOURCE, len(expected))), expected)
        self.assertEqual([w for w in n.writes if
                          init.MANAGER_SOURCE <= w[1] < init.MANAGER_SOURCE + len(expected)],
                         [(0x111495, init.MANAGER_SOURCE + 0x404, 4, 0xcafebabe)])
        for address in (init.MANAGER_SOURCE - 16, init.MANAGER_SOURCE + len(expected)):
            self.assertEqual(bytes(n.vm.mem_read(address, 16)), b'\xa5' * 16)
        witnesses = {
            0x111469: '8b88880000008b9084000000',
            0x111478: '5152578b88a8000000576a01',
            0x111484: 'e817f1f0ff',
            0x111489: '8b854c4914008b880c040000898804040000',
            0x11149b: '8b9558340800',
        }
        for address, encoded in witnesses.items():
            raw = bytes.fromhex(encoded)
            self.assertEqual(n.image[address:address + len(raw)], raw, hex(address))
        for lo, hi in init.RANGES + init.REGISTRY_RANGES + init.SOURCE_RANGES + ((0x205a0, 0x205e3),):
            self.assertEqual(bytes(n.vm.mem_read(init.BASE + lo, hi - lo)), n.image[lo:hi])

    def test_source_only_preserves_high_bits_and_stops_before_manager_read(self):
        source = bytearray(self.source)
        struct.pack_into('<II', source, 0x84, 0xffffffff, 0x80000001)
        # Independent complete run; explicit all-null registry for this input case.
        n = init.initialize(self.context, display_state=self.display,
                            registry_state=(None,) * 20, source_state=bytes(source))
        self.assertEqual(n.stop, 0x111489)
        self.assertEqual(n.get32(init.DISPLAY + 0x20), 0xffffffff)
        self.assertEqual(n.get32(init.DISPLAY + 0x24), 0x80000001)
        self.assertEqual(n.visits.count(0x205e0), 33)
        self.assertNotIn(0x111489, n.visits)
        self.assertNotIn(init.MANAGER_SOURCE, n.pages)

    def test_source_snapshots_reject_missing_prerequisites_and_partial_storage(self):
        prerequisites = {'display_state': self.display, 'registry_state': (None,) * 20}
        for bad in (b'', self.source[:-1], self.source + b'\0', bytearray(self.source)):
            with self.assertRaisesRegex(ValueError, 'source snapshot'):
                init.initialize(self.context, **prerequisites, source_state=bad)
        with self.assertRaisesRegex(ValueError, 'source snapshot'):
            init.initialize(self.context, source_state=self.source)
        for bad in (b'', self.manager_source[:-1], bytearray(self.manager_source)):
            with self.assertRaisesRegex(ValueError, 'manager source snapshot'):
                init.initialize(self.context, **prerequisites, source_state=self.source,
                                manager_source_state=bad)
        with self.assertRaisesRegex(ValueError, 'manager source snapshot'):
            init.initialize(self.context, **prerequisites,
                            manager_source_state=self.manager_source)


if __name__ == '__main__':
    unittest.main()
