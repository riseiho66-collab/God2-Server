"""Original current image only; independent islands are not end-to-end entry."""
import struct
import subprocess
import unittest

from tools.strike_lab import current_battle_entry as entry


def record(first=0x12345678, second=0x9abcdeff):
    return b'\x82' + struct.pack('<II', first, second)


class CurrentBattleEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = entry.pinned_image()

    def test_image_identity_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'SHA256'):
            entry.NativeRun(self.image[:-1] + bytes([self.image[-1] ^ 1]))

    def test_original_world_table_and_battle_table_are_distinct(self):
        table = lambda op: struct.unpack_from('<I', self.image, 0x6b5d4 + op * 4)[0]
        self.assertEqual(table(0x82), entry.BASE + 0x6ae12)
        self.assertEqual(table(0x83), entry.BASE + 0x6b517)
        for op in range(0x7b, 0x82):
            self.assertEqual(table(op), entry.BASE + 0x6ad6d)
        self.assertEqual(table(0xf6), entry.BASE + 0x6ad6d)
        self.assertEqual(entry.battle_dispatch(0x82).stop, 0x1145c0)
        self.assertEqual(entry.battle_dispatch(0x83).stop, 0x11436b)
        self.assertEqual(entry.battle_dispatch(0x84).stop, 0x1143dd)
        self.assertEqual(entry.battle_dispatch(0x86).stop, 0x114464)

    def test_original_length_wrapper_and_exact_logical_contract(self):
        self.assertEqual(entry.native_length(), 9)
        for data in (b'', b'\x82' * 8, b'\x82' * 10, b'\x83' + b'\0' * 8):
            with self.assertRaises(ValueError):
                entry.world_entry(data)
        self.assertEqual(entry.record_fields(record(0, 0xffffffff)), (0, 0xffffffff))

    def test_dispatch_executes_both_raw_dword_writes_and_stops_before_cleanup(self):
        for first, second in ((0, 0), (0xffffffff, 0x80000000),
                              (0x12345678, 0x9abcdeff)):
            with self.subTest(first=first, second=second):
                n = entry.world_entry(record(first, second))
                self.assertEqual(n.stop, 0x6ae2d)
                self.assertIn(0x68b61, n.visits)
                self.assertIn(0x6ae12, n.visits)
                self.assertNotIn(0x857e0, n.visits)
                self.assertEqual(n.get32(entry.SP + 0x3c), 0x82)
                self.assertEqual(n.get32(entry.SP + 0x2c), 3)
                expected = bytearray(b'\xa5' * 0x3ec)
                struct.pack_into('<II', expected, 0x28, first, second)
                self.assertEqual(bytes(n.vm.mem_read(entry.CONTEXT, 0x3ec)), expected)
                writes = [(pc, address, size, value) for pc, address, size, value in n.writes
                          if entry.CONTEXT <= address < entry.CONTEXT + 0x3ec]
                self.assertEqual(writes, [(0x6ae22, entry.CONTEXT + 0x28, 4, first),
                                          (0x6ae2a, entry.CONTEXT + 0x2c, 4, second)])

    def test_original_first_cleanup_with_explicit_negative_handles(self):
        n = entry.world_entry(record(), negative_handles=True)
        self.assertEqual(n.stop, 0x6ae34)
        self.assertEqual(n.visits.count(0x857e0), 1)
        self.assertEqual(n.visits.count(0x6d340), 5)
        self.assertEqual(n.visits.count(0x6e490), 10)
        self.assertEqual(n.visits.count(0x85851), 1)
        self.assertNotIn(0x814f0, n.visits)
        self.assertNotIn(0xa7550, n.visits)
        self.assertEqual(n.get32(entry.SP + 0x2c), 3)
        self.assertEqual(n.vm.reg_read(entry.UC_X86_REG_ESP), entry.SP)
        self.assertEqual(n.vm.reg_read(entry.UC_X86_REG_ECX), entry.UI)

    def test_state_four_suffix_is_explicitly_independent(self):
        n = entry.state_tail()
        self.assertEqual(n.stop, 0x6b517)
        self.assertEqual(n.get32(entry.SP + 0x2c), 4)
        self.assertEqual(n.visits, [0x6ae40, 0x6ae48])

    def test_closed_ui_cleanup_continuously_reaches_state_four(self):
        expected_calls = (0x857e0, 0x814f0, 0xec3c0, 0xf1900, 0x71390,
                          0xc9bd0, 0xf7eb0, 0x9c190, 0x7c9e0, 0x9dd40,
                          0x6f3d0, 0x77750, 0xc4c50, 0xf6410, 0xbc2e0,
                          0xbc2a0, 0xa7550)
        for handle in (-32768, -1):
            for category in (0, 3, 0xffffffff):
                n = entry.world_entry(record(), closed_ui=True,
                                      closed_handle=handle, closing_category=category)
                self.assertEqual(n.stop, 0x6b517)
                self.assertEqual(n.get32(entry.SP + 0x2c), 4)
                self.assertEqual(n.vm.reg_read(entry.UC_X86_REG_ESP), entry.SP)
                for callee in expected_calls:
                    self.assertEqual(n.visits.count(callee), 1, hex(callee))
                self.assertLess(n.visits.index(0x8158e), n.visits.index(0xa7550))
                self.assertLess(n.visits.index(0xa75c3), n.visits.index(0x6ae40))
                self.assertEqual(bytes(n.vm.mem_read(0x5926b0, 2)), b'\xff\xff')
                self.assertEqual(n.get32(entry.UI + 0x23d5e4), 0 if category == 3 else category)
                self.assertEqual(n.get32(entry.UI + 0x23d5e8),
                                 0 if category == 3 else 0xa5a5a5a5)
                # No other nonstack writes are authorized by this fixture.
                nonstack = [(pc, address, size, value) for pc, address, size, value in n.writes
                            if not entry.STACK <= address < entry.STACK + 0x8000]
                expected = [(0x6ae22, entry.CONTEXT + 0x28, 4, 0x12345678),
                            (0x6ae2a, entry.CONTEXT + 0x2c, 4, 0x9abcdeff)]
                if category == 3:
                    expected += [(0xc9c48, entry.UI + 0x23d5e8, 4, 0),
                                 (0xc9c4e, entry.UI + 0x23d5e4, 4, 0)]
                expected += [(0xbc2e2, 0x5926b0, 2, 0xffff)]
                self.assertEqual(nonstack, expected)

    def test_main_return_four_selects_initialization_arm_before_first_call(self):
        n = entry.main_state_selector(record())
        self.assertIn(0x6563d, n.visits)
        self.assertIn(0x6565b, n.visits)
        self.assertEqual(n.get32(entry.SP + 0x10), 4)
        self.assertEqual(n.stop, 0x6569b)
        self.assertNotIn(0x66920, n.visits)

    def test_real_world_receive_function_returns_four_and_preserves_next_record(self):
        for opcode, size in ((0x83, 15), (0x84, 15), (0x86, 17), (0x89, 57)):
            following = bytes([opcode]) + bytes((i * 17) & 255 for i in range(size - 1))
            suffix = following + b'\x86\x05' + bytes(15)
            n = entry.world_entry(record(), closed_ui=True, queued_suffix=suffix)
            self.assertEqual(n.stop, entry.RETURN)
            self.assertEqual(n.vm.reg_read(entry.UC_X86_REG_EAX), 4)
            self.assertEqual(n.vm.reg_read(entry.UC_X86_REG_ESP), entry.SP + 8)
            for name, value in (('EBX', 0xdeadbe01), ('EBP', 0xdeadbe02),
                                ('ESI', 0xdeadbe03), ('EDI', 0xdeadbe04)):
                self.assertEqual(n.vm.reg_read(getattr(entry, 'UC_X86_REG_' + name)), value)
            self.assertEqual(n.visits.count(0x13420), 2)
            self.assertEqual(n.visits.count(0x13670), 1)
            self.assertEqual(n.visits.count(0x13650), 1)
            self.assertEqual(n.visits.count(0x68b61), 1)
            self.assertIn(0x68b39, n.visits)
            self.assertNotIn(0x10d20, n.visits)
            self.assertEqual(n.get32(entry.NET + 0x2cc0), size)
            self.assertEqual(bytes(n.vm.mem_read(entry.NET + 0x2cc4, size)), following)
            cursor = n.get32(entry.NET + 0x758 + 0x1814)
            self.assertEqual(cursor, 9 + size)
            self.assertEqual(n.get32(entry.NET + 0x758 + 0x1810), 9 + len(suffix))
            self.assertEqual(bytes(n.vm.mem_read(entry.NET + 0x758 + 0xc10 + cursor, 17)), suffix[-17:])

    def test_partial_next_record_is_preserved_and_empty_queue_reaches_poll_boundary(self):
        for size in range(1, 15):
            prefix = b'\x83' + bytes(size - 1)
            n = entry.world_entry(record(), closed_ui=True, queued_suffix=prefix)
            self.assertEqual(n.stop, entry.RETURN)
            self.assertEqual(n.vm.reg_read(entry.UC_X86_REG_EAX), 4)
            self.assertEqual(n.get32(entry.NET + 0x2cc0), size)
            self.assertEqual(bytes(n.vm.mem_read(entry.NET + 0x2cc4, size)), prefix)
            self.assertEqual(n.visits.count(0x68b61), 1)
        n = entry.world_entry(record(), closed_ui=True, queued_suffix=b'')
        self.assertEqual(n.stop, 0x10d20)
        self.assertEqual(n.get32(entry.NET + 0x2cc0), 0)
        self.assertIn(0x6ae40, n.visits)
        self.assertNotIn(0x6b5c2, n.visits)

    def test_formal_server_frame_through_native_decoder_and_world_dispatch(self):
        binary = entry.ROOT / 'build/tests/Release/recovered-world-frame.exe'
        self.assertTrue(binary.is_file(), 'Build recovered-world-frame first')
        for opcode, size in ((0x83, 15), (0x84, 15), (0x86, 17), (0x89, 57)):
            suffix = bytes([opcode]) + bytes((i * 13) & 255 for i in range(size - 1))
            logical = record() + suffix
            wire = bytes.fromhex(subprocess.check_output(
                [str(binary), '--encode', logical.hex()], text=True, timeout=10).strip())
            n = entry.world_entry(record(), closed_ui=True, queued_suffix=suffix, wire_frame=wire)
            self.assertEqual(n.stop, entry.RETURN)
            self.assertEqual(n.vm.reg_read(entry.UC_X86_REG_EAX), 4)
            for callee in (0x10490, 0x10ab0, 0x10a10, 0x106f0, 0x10750, 0x68ae0):
                self.assertIn(callee, n.visits)
            self.assertLess(n.visits.index(0x10750), n.visits.index(0x68ae0))
            self.assertEqual(bytes(n.vm.mem_read(entry.NET + 0x2cc4, size)), suffix)
            corrupted = wire[:-1] + bytes([wire[-1] ^ 1])
            with self.assertRaisesRegex(ValueError, 'Original frame decoder rejected'):
                entry.world_entry(record(), closed_ui=True, queued_suffix=suffix, wire_frame=corrupted)

    def test_large_coalesced_native_transition_preserves_remaining_battle_queue(self):
        binary = entry.ROOT / 'build/tests/Release/recovered-world-frame.exe'
        for count in (17, 170):
            following = b'\x83' + bytes(range(14))
            suffix = following * count
            wire = bytes.fromhex(subprocess.check_output(
                [str(binary), '--encode', (record() + suffix).hex()], text=True, timeout=10).strip())
            n = entry.world_entry(record(), closed_ui=True, queued_suffix=suffix, wire_frame=wire)
            self.assertEqual(n.stop, entry.RETURN)
            self.assertEqual(n.vm.reg_read(entry.UC_X86_REG_EAX), 4)
            self.assertEqual(n.get32(entry.NET + 0x758 + 0x1814), 24)
            self.assertEqual(n.get32(entry.NET + 0x2cc0), 15)
            self.assertEqual(bytes(n.vm.mem_read(entry.NET + 0x2cc4, 15)), following)
            self.assertEqual(bytes(n.vm.mem_read(entry.NET + 0x758 + 0xc10 + 24,
                                                len(suffix) - 15)), suffix[15:])

    def test_mixed_participant_scalar_batch_preserves_native_record_boundaries(self):
        binary = entry.ROOT / 'build/tests/Release/recovered-world-frame.exe'
        self.assertTrue(binary.is_file(), 'Build recovered-world-frame first')
        self.assertEqual(entry.native_length(0x1c), 45)
        self.assertEqual(entry.native_length(0x86), 17)
        for count in (1, 14, 28):
            records = []
            for position in range(count):
                # Explicit layout/queue probe, not an official opening sequence.
                records.append(b'\x1c' + bytes((position,)) + b'\xa5' * 43)
                for subtype in (0, 1):
                    scalar = bytearray(b'\x5a' * 17)
                    scalar[:3] = bytes((0x86, subtype, position))
                    struct.pack_into('<II', scalar, 5, 0x12340000 + position,
                                     0x56780000 + subtype)
                    records.append(bytes(scalar))
            suffix = b''.join(records)
            wire = bytes.fromhex(subprocess.check_output(
                [str(binary), '--encode', (record() + suffix).hex()], text=True, timeout=10).strip())
            n = entry.world_entry(record(), closed_ui=True, queued_suffix=suffix, wire_frame=wire)
            self.assertEqual(n.stop, entry.RETURN)
            self.assertEqual(n.vm.reg_read(entry.UC_X86_REG_EAX), 4)
            self.assertEqual(n.get32(entry.NET + 0x2cc0), 45)
            self.assertEqual(bytes(n.vm.mem_read(entry.NET + 0x2cc4, 45)), records[0])
            codec = entry.NET + 0x758
            self.assertEqual(n.get32(codec + 0x1814), 54)
            self.assertEqual(n.get32(codec + 0x1810), 9 + len(suffix))
            self.assertEqual(bytes(n.vm.mem_read(codec + 0xc10 + 54, len(suffix) - 45)), suffix[45:])

    def test_formal_bootstrap_builder_through_original_receiver(self):
        binary = entry.ROOT / 'build/tests/Release/recovered-battle-bootstrap.exe'
        self.assertTrue(binary.is_file(), 'Build recovered-battle-bootstrap first')
        wire = bytes.fromhex(subprocess.check_output(
            [str(binary), '--diagnostic-wire'], text=True, timeout=10).strip())
        # Independent expected records, not a C++ decoder echo. Synthetic values
        # test the builder through the original codec and world receive function.
        records = []
        for position in (0, 14):
            identity = bytearray(range(45))
            identity[:3] = bytes((0x1c, position, 30))
            struct.pack_into('<HH', identity, 5, 0x400, 1)
            identity[9] = 1
            struct.pack_into('<H', identity, 11, 0)
            records.append(bytes(identity))
            for subtype in ((0, 1) if position == 0 else (0,)):
                vital = bytearray(17)
                vital[:4] = bytes((0x86, subtype, position, 0xa5))
                struct.pack_into('<II', vital, 5, 24 if subtype else 120, 20 if subtype else 100)
                vital[16] = 0x5a
                records.append(bytes(vital))
        suffix = b''.join(records)
        n = entry.world_entry(record(), closed_ui=True, queued_suffix=suffix, wire_frame=wire)
        self.assertEqual(n.stop, entry.RETURN)
        self.assertEqual(n.vm.reg_read(entry.UC_X86_REG_EAX), 4)
        self.assertEqual(n.get32(entry.NET + 0x2cc0), 45)
        self.assertEqual(bytes(n.vm.mem_read(entry.NET + 0x2cc4, 45)), records[0])
        codec = entry.NET + 0x758
        self.assertEqual(n.get32(codec + 0x1814), 54)
        self.assertEqual(n.get32(codec + 0x1810), 9 + len(suffix))
        self.assertEqual(bytes(n.vm.mem_read(codec + 0xc10 + 54, len(suffix) - 45)), suffix[45:])

    def test_original_init_prefix_observes_second_field_low_byte(self):
        for second, expected_flag in ((0x123456ff, 1), (0xffffffff, 1),
                                      (0xff000000, 0), (0, 0)):
            source = entry.world_entry(record(second=second))
            context = bytes(source.vm.mem_read(entry.CONTEXT, 0x3ec))
            n = entry.initialization_prefix(context)
            self.assertEqual(n.stop, 0x1113d8)
            self.assertEqual(n.get32(entry.BATTLE + 0xa9ea4c8), expected_flag)
            self.assertEqual(n.get32(entry.BATTLE + 0x10), entry.NET)
            self.assertEqual(n.get32(entry.BATTLE + 0x20), entry.UI)
            self.assertNotIn(0x181b0, n.visits)

    def test_world_built_descriptor_supplies_role_binding_without_pointer_patch(self):
        n = entry.world_descriptor_prefix()
        frame = n.vm.reg_read(entry.UC_X86_REG_ESP)
        descriptor = frame + 0x1c
        self.assertEqual(frame, entry.SP - 0xa24)
        expected = (entry.ROOT_OBJECT, frame + 0x238, entry.UI, 0x6500000,
                    entry.WORLD + 0x1539683c, entry.RESOURCES, entry.WORLD + 0x15383410)
        self.assertEqual(struct.unpack('<7I', n.vm.mem_read(descriptor, 28)), expected)
        for offset, value in ((0x428, 0x6700000), (0x424, 0x6800000),
                              (0x42c, entry.RENDERER), (0x438, entry.NET)):
            n.put32(entry.ROOT_OBJECT + offset, value)
        n.put32(entry.RENDERER + 0xa0, 0x6900000)
        n.put32(entry.RENDERER + 0xac, 0x6a00000)
        n.map(entry.BATTLE, 4096)
        # Separate initializer entry; skipped world transitions are not claimed.
        n.put32(entry.SP + 4, descriptor)
        n.registers(ecx=entry.BATTLE, esp=entry.SP)
        n.run(0x1112c0, [(0x1112c0, 0x11132f)], {0x11132f})
        self.assertEqual(n.get32(entry.BATTLE + 0x14), expected[4])
        self.assertEqual(n.get32(entry.BATTLE + 0x20), expected[2])
        self.assertEqual(n.get32(entry.BATTLE + 0x24), expected[3])
        self.assertEqual(n.get32(entry.BATTLE + 0x2c), expected[6])
        self.assertEqual(struct.unpack('<7I', n.vm.mem_read(descriptor, 28)), expected)
        self.assertEqual(bytes(n.vm.mem_read(entry.BASE, len(n.image))), n.image)

    def test_original_init_copy_preserves_fields_and_full_context(self):
        source = entry.world_entry(record())
        context = bytes(source.vm.mem_read(entry.CONTEXT, 0x3ec))
        n = entry.initialization_copy(context)
        self.assertEqual(n.stop, 0x111424)
        self.assertEqual(n.get32(entry.BATTLE + 0x3c), 0x12345678)
        self.assertEqual(n.get32(entry.BATTLE + 0x40), 0x9abcdeff)
        self.assertEqual(bytes(n.vm.mem_read(entry.BATTLE + 0x48, 0x3ec)), context)
        self.assertEqual(n.get32(entry.BATTLE + 0x70), 0x12345678)
        self.assertEqual(n.get32(entry.BATTLE + 0x74), 0x9abcdeff)
        self.assertEqual(bytes(n.vm.mem_read(entry.BATTLE + 0x434, 16)), b'\xcc' * 16)
        self.assertNotIn(0x11fc40, n.visits)

    def test_static_calls_connect_world_return_initializer_loop_and_dispatch(self):
        calls = {0x6564e: 0x67860, 0x67a63: 0x66b00, 0x67154: 0x68ae0,
                 0x6ae2d: 0x857e0, 0x6ae34: 0x814f0, 0x6ae3b: 0xa7550,
                 0x65836: 0x1112c0, 0x658d9: 0x115770,
                 0x115a4c: 0x1140c0, 0x11431c: 0x15840,
                 0x11432d: 0x11d3d0, 0x1113d8: 0x181b0,
                 0x111424: 0x11fc40}
        for address, target in calls.items():
            self.assertEqual(self.image[address], 0xe8)
            relative = struct.unpack_from('<i', self.image, address + 1)[0]
            self.assertEqual(address + 5 + relative, target)
        self.assertEqual(struct.unpack_from('<I', self.image, 0x65a14 + 4 * 4)[0],
                         entry.BASE + 0x6565b)

    def test_original_instruction_witnesses(self):
        witnesses = {
            0x68b61: 'ff2485d4b54600',
            0x68b31: '817c243c82000000',
            0x6ae12: '8b8424041700008b4b01',
            0x6ae22: '8948288b53058bce89502c',
            0x6ae40: 'c744242c04000000',
            0x6b5c2: '8b44242c',
            0x67159: '83e8047432',
            0x6714a: '8bbc24a00000008bce57',
            0x67190: '8b8e58683915894f0c',
            0x671bf: 'c744243804000000',
            0x671ee: 'c744243804000000',
            0x67206: 'b802000000c744243804000000',
            0x67685: '8b442430',
            0x67a68: '83f8030f8545020000',
            0x65644: '8d8424380200008bcb50',
            0x6582b: '8d4c241c518b8bec057e0a',
            0x1113bf: '807b2cff0f94c1898dc8a49e0a',
            0x111409: '8b432889453c8b4b2c894d40b9fb000000f3a5',
            0x115828: '89bec4a49e0a899ec0f69d0a',
            0x114315: '8a4d00518b4e10',
            0x114332: '8a45008bd081e2ff000000',
        }
        for address, hex_bytes in witnesses.items():
            expected = bytes.fromhex(hex_bytes)
            self.assertEqual(self.image[address:address + len(expected)], expected,
                             f'Original witness RVA {address:X}')

    def test_unknown_control_flow_and_instruction_budget_fail_closed(self):
        with self.assertRaisesRegex(AssertionError, 'Unqualified instruction'):
            entry.NativeRun().run(0x15840, [], set())
        with self.assertRaisesRegex(AssertionError, 'budget exhausted'):
            entry.NativeRun().run(0x15840, [(0x15840, 0x15850)], set(), budget=1)
        previous = entry.state_tail()
        self.assertEqual(previous.stop, 0x6b517)
        with self.assertRaisesRegex(AssertionError, 'budget exhausted'):
            previous.run(0x15840, [(0x15840, 0x15850)], set(), budget=1)


if __name__ == '__main__':
    unittest.main()
