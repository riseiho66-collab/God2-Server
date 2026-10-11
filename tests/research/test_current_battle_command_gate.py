"""Current instructions, synthetic state, closed slice boundaries; no sockets.

The closed-handle cleanup case executes intact to the OS clock boundary.
Other post-cleanup and receive-side slices have explicit entry registers;
they do not stand in for skipped helpers.
"""
from pathlib import Path
import struct
import sys
import unittest

import test_current_battle_command as battle

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.strike_lab import current_battle_command_gate as gate
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX,
    UC_X86_REG_EBP, UC_X86_REG_ESI, UC_X86_REG_EDI,
    UC_X86_REG_EIP, UC_X86_REG_ESP)

BASE, BATTLE, NET, SP = battle.BASE, battle.BATTLE, battle.NET, battle.SP
FIRST, SECOND, WAIT = 0xa9e9c38, 0xa9e9c3c, 0xa9e9c34
RECORD = BATTLE + 0xa9e9cb0


class CurrentBattleCommandGateTests(unittest.TestCase):
    builder = battle.CurrentBattleCommandTests.builder
    queued = battle.CurrentBattleCommandTests.queued
    vm = battle.CurrentBattleCommandTests.vm

    @classmethod
    def setUpClass(cls):
        cls.image = gate.load_image()

    @staticmethod
    def put(vm, offset, value):
        vm.mem_write(BATTLE + offset, struct.pack('<I', value))

    @staticmethod
    def get(vm, offset):
        return struct.unpack('<I', vm.mem_read(BATTLE + offset, 4))[0]

    def slice(self, vm, start, stops, registers=()):
        trace = []
        def stop(machine, address, size, data):
            rva = address - BASE
            trace.append(rva)
            if rva in stops:
                machine.emu_stop()
        hook = vm.hook_add(UC_HOOK_CODE, stop)
        for reg, value in registers:
            vm.reg_write(reg, value)
        try:
            vm.emu_start(BASE + start, battle.ready.RETURN, count=10000)
        except Exception as error:
            raise AssertionError(f'Native slice fault at RVA {vm.reg_read(UC_X86_REG_EIP)-BASE:X}') from error
        finally:
            vm.hook_del(hook)
        end = vm.reg_read(UC_X86_REG_EIP) - BASE
        self.assertIn(end, stops)
        return end, trace

    def fixture(self, state=gate.Controls(1, 0, 0)):
        _, _, _, vm = self.builder(modes=(state.first, state.second))
        vm.mem_map((BATTLE + 0xa9ea4c4) & ~4095, 4096)
        for offset, value in ((FIRST, state.first), (SECOND, state.second),
                              (WAIT, state.waiting)):
            self.put(vm, offset, value)
        vm.mem_write(BATTLE + 0x51, bytes([state.first_actor, state.second_actor]))
        return vm

    def controls(self, vm):
        return gate.Controls(self.get(vm, FIRST), self.get(vm, SECOND), self.get(vm, WAIT),
                             *bytes(vm.mem_read(BATTLE + 0x51, 2)))

    def test_controls_consume_first_then_second_even_without_queue(self):
        for state in (gate.Controls(1, 0, 0), gate.Controls(0, 2, 0),
                      gate.Controls(7, 9, 0), gate.Controls(7, 9, 0xa5),
                      gate.Controls(0, 0, 0xa5)):
            for connected in (0, 1):
                # Action 0B is the native exception to the initial control guard.
                action = 1 if state.first or state.second else 11
                record, _, _, vm = self.builder(action=action,
                    modes=(state.first, state.second), connected=connected)
                self.assertEqual(bool(record), bool(connected))
                self.put(vm, WAIT, state.waiting)
                vm.mem_write(BATTLE + 0x51, b'\xff\xff')
                expected = state
                for _ in range(2 if state.first and state.second else 1):
                    self.slice(vm, 0x119200, (0x119252,),
                               ((UC_X86_REG_ESI, BATTLE), (UC_X86_REG_EBX, 0)))
                    expected = gate.consume_controls(expected)
                    self.assertEqual(self.controls(vm), expected)
                self.assertEqual(self.get(vm, 0x46c), 0xffffffff)
                self.assertEqual(vm.reg_read(UC_X86_REG_EDI), 1)

    def test_native_86_5_dispatch_and_grant_slices_preserve_absent_bits(self):
        state = gate.Controls(7, 9, 0xa5, 12, 13)
        vm = self.fixture(state)
        vm.mem_map((BATTLE + 0xab3b1d0) & ~4095, 4096)
        vm.mem_write(BATTLE + 0xab3b1d0, b'\xff\xff\xff\xff')
        for flags in (0, 1, 2, 3, 0x80, 0xff):
            for packed in (0, 0x1d, 0xde, 0xff):
                state = gate.Controls(0, 0, 0xa5, 12, 13) if packed & 1 else (
                    gate.Controls(7, 9, 0xa5, 12, 13))
                record = bytes([0x86, 5, 0xa5, flags, packed]) + bytes(12)
                vm.mem_write(RECORD, record)
                end, trace = self.slice(vm, 0x114332, (0x117590,), (
                    (UC_X86_REG_EBP, RECORD), (UC_X86_REG_EDI, RECORD),
                    (UC_X86_REG_ESI, BATTLE), (UC_X86_REG_ESP, SP)))
                self.assertIn(0x1144c1, trace)
                for offset, value in ((FIRST, state.first), (SECOND, state.second),
                                      (WAIT, state.waiting)):
                    self.put(vm, offset, value)
                vm.mem_write(BATTLE + 0x51, bytes([12, 13]))
                self.slice(vm, 0x1175b2, (0x117691, 0x1176af),
                           ((UC_X86_REG_ESI, BATTLE), (UC_X86_REG_EDI, RECORD)))
                end, _ = self.slice(vm, 0x11776e, (0x117795, 0x1177ac),
                           ((UC_X86_REG_ESI, BATTLE), (UC_X86_REG_EDI, RECORD)))
                expected = gate.grant_controls(record, state)
                self.assertEqual(self.controls(vm), expected)
                self.assertEqual(end == 0x117795, bool(flags & 2) and not expected.first)

    def test_rearm_helpers_require_control_panel_zero_and_counter_not_minus_one(self):
        vm = self.fixture()
        for entry in (0x115670, 0x115740):
            for panel in (0, 1, 0x80000000):
                for counter in (0, 1, 0xffffffff):
                    self.put(vm, 0xa9e9c28, panel)
                    self.put(vm, 0xa9e9c64, counter)
                    end, _ = self.slice(vm, entry, (0x1121f0, entry + 0x25),
                        ((UC_X86_REG_ECX, BATTLE), (UC_X86_REG_ESP, SP)))
                    self.assertEqual(end == 0x1121f0, panel == 0 and counter != 0xffffffff)
        self.put(vm, WAIT, 1)
        self.slice(vm, 0x11223b, (0x11224d,),
                   ((UC_X86_REG_ESI, BATTLE), (UC_X86_REG_EBX, 0),
                    (UC_X86_REG_EDI, 0xffffffff)))
        self.assertEqual(self.get(vm, WAIT), 0)
        self.assertEqual(self.get(vm, 0xa9df73c), 0xffffffff)

    def test_refusal_regrant_helpers_can_return_with_wait_still_set(self):
        # Explicit post-command state, not a full grant or live refusal replay.
        for entry in (0x115670, 0x115740):
            for panel, counter in ((0, 0xffffffff), (1, 0), (1, 1)):
                vm = self.fixture(gate.Controls(1, 0, 1))
                self.put(vm, 0xa9e9c28, panel)
                self.put(vm, 0xa9e9c64, counter)
                vm.mem_write(SP, struct.pack('<I', battle.ready.RETURN))
                _, trace = self.slice(vm, entry, (battle.ready.RETURN - BASE,), (
                    (UC_X86_REG_ECX, BATTLE), (UC_X86_REG_ESP, SP)))
                self.assertNotIn(0x1121f0, trace)
                self.assertEqual(self.controls(vm), gate.Controls(1, 0, 1))
                self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP + 4)

    def test_secondary_grant_returns_then_two_commands_share_native_state(self):
        # Entry is after the OS clock call, not a substitute implementation of it.
        # First control already exists: native code skips the UI refresh helpers.
        for packed in (0x00, 0x7d, 0xed):
            for flags in (2, 0x82):
                vm = self.fixture(gate.Controls(1, 0, 0, 12, 13))
                vm.mem_map((BATTLE + 0xab3b1d0) & ~4095, 4096)
                vm.mem_write(BATTLE + 0xab3b1d0, b'\xff' * 4)
                record = bytes([0x86, 5, 0xa5, flags, packed]) + bytes(12)
                vm.mem_write(RECORD, record)
                self.put(vm, 0xa9e9c70, 0x12345678)
                # Four saved registers, original return address and packet argument.
                vm.mem_write(SP, struct.pack('<6I', 11, 22, 33, 44,
                                             battle.ready.RETURN, RECORD))
                end, trace = self.slice(vm, 0x1175a0,
                    (battle.ready.RETURN - BASE,), (
                        (UC_X86_REG_ESI, BATTLE), (UC_X86_REG_EDI, RECORD),
                        (UC_X86_REG_EAX, 0x87654321), (UC_X86_REG_ESP, SP)))
                self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP + 24)
                self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 1)
                self.assertIn(0x1177b5, trace)
                self.assertNotIn(0x115740, trace)
                self.assertEqual(self.get(vm, 0xa9e9c10), 0x87654321)
                self.assertEqual(self.get(vm, 0xa9e9c18), 0x12345678)
                self.assertEqual(self.controls(vm), gate.Controls(1, 1, 0, 12, packed >> 4))
                vm.mem_write(NET + 0x36c4, struct.pack('<I', 0))
                for index, actor in enumerate((12, packed >> 4)):
                    vm.mem_write(SP, struct.pack('<5I', battle.ready.RETURN,
                                                 1, actor, 1, battle.TARGETS))
                    self.slice(vm, 0x118e50, (0x1191ee,), (
                        (UC_X86_REG_ECX, BATTLE), (UC_X86_REG_ESP, SP)))
                    queued = self.queued(vm)
                    self.assertEqual(len(queued), 17 * (index + 1))
                    self.assertEqual(queued[index * 17:index * 17 + 4],
                                     bytes([0x35, actor, 1, index]))
                    # Explicit post-UI boundary, not proof of UI helper completion.
                    self.slice(vm, 0x119200, (0x119252,), (
                        (UC_X86_REG_ESI, BATTLE), (UC_X86_REG_EBX, 0)))
                    self.assertEqual((self.get(vm, FIRST), self.get(vm, SECOND)),
                                     (0, 1) if index == 0 else (0, 0))
                vm.mem_write(SP, struct.pack('<5I', battle.ready.RETURN,
                                             1, 12, 1, battle.TARGETS))
                self.slice(vm, 0x118e50, (battle.ready.RETURN - BASE,), (
                    (UC_X86_REG_ECX, BATTLE), (UC_X86_REG_ESP, SP)))
                self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 0)
                self.assertEqual(len(self.queued(vm)), 34)
                self.assertEqual(bytes(vm.mem_read(RECORD, 17)), record)

    def test_kind_zero_continuation_queue_and_real_encoder_boundary(self):
        for count in (1, 2, 14):
            records, _, calls, vm = self.builder(tuple(i % 28 for i in range(count)),
                                                action=3, skill=True)
            self.assertEqual(tuple(records[2::17]), gate.continuation_actions(count))
            self.assertEqual(calls.count(0x132e0), count)
            self.assertEqual(self.get_net(vm, 0x36c4), 17 * count)
            # Fresh native VM preserves the exact produced queue, without the
            # shared builder test's deliberate transport-entry rejection hook.
            transport = battle.CurrentBattleCommandTests.vm(self)
            transport.mem_write(NET, bytes(vm.mem_read(NET, 0x5000)))
            vm = transport
            codec = NET + 0x104 + 0x654
            vm.mem_write(SP, struct.pack('<I', battle.ready.RETURN))
            vm.reg_write(UC_X86_REG_ESP, SP)
            vm.reg_write(UC_X86_REG_ECX, codec)
            vm.emu_start(BASE + 0x10490, battle.ready.RETURN, count=100000)
            self.assertEqual(vm.reg_read(UC_X86_REG_EIP), battle.ready.RETURN)
            vm.mem_write(codec + 8, struct.pack('<I', 1))
            vm.mem_write(SP, struct.pack('<I', battle.ready.RETURN))
            _, trace = self.slice(vm, 0x13370, (0x12501,),
                ((UC_X86_REG_ECX, NET), (UC_X86_REG_ESP, SP)))
            sp = vm.reg_read(UC_X86_REG_ESP)
            socket, pointer, size, flags = struct.unpack('<4I', vm.mem_read(sp, 16))
            wire = bytes(vm.mem_read(pointer, size))
            self.assertEqual(size, len(records) + 3)
            self.assertEqual(struct.unpack_from('<H', wire)[0], size)
            self.assertEqual(flags, 0)
            self.assertIn(0x124ea, trace)
            self.assertEqual(self.get_net(vm, 0x36c4), len(records))
            # Separate post-send slice: no socket success is assumed or stubbed.
            self.slice(vm, 0x133b3, (0x133cc,), ((UC_X86_REG_ESI, NET),))
            self.assertEqual(self.get_net(vm, 0x36c4), 0)

    @staticmethod
    def get_net(vm, offset):
        return struct.unpack('<I', vm.mem_read(NET + offset, 4))[0]

    def test_queue_capacity_flush_boundary_is_per_record_not_continuation(self):
        vm = self.fixture()
        for length in (0, 0x9ef, 0x9f0, 0xa00):
            vm.mem_write(NET + 0x36c4, struct.pack('<I', length))
            vm.mem_write(SP, struct.pack('<4I', battle.ready.RETURN, 0x35, SP - 16, 16))
            # Stop at CALL instruction itself, before the forbidden transport entry.
            end, _ = self.slice(vm, 0x132e0, (0x132fe, 0x13303),
                               ((UC_X86_REG_ECX, NET), (UC_X86_REG_ESP, SP)))
            self.assertEqual(end == 0x132fe, length + 17 > 0xa00)

    def test_action_0b_producer_gate_and_loop_flush_callsite(self):
        vm = self.fixture()
        vm.mem_map((BATTLE + 0x144c1c) & ~4095, 4096)
        for done, event, current, previous, latch, enabled, expected in (
                (0, 0, 4, 4, 0, 1, True), (1, 0, 4, 4, 0, 1, False),
                (0, 0, 4, 3, 0, 1, False), (0, 0, 4, 4, 1, 1, False),
                (0, 0, 4, 4, 0, 2, False), (0, 1, 5, 4, 0, 0, True),
                (0, 1, 3, 4, 0, 1, False),
                (0, 1, 0xffffffff, 4, 0, 0, True),
                (0, 1, 0x80000000, 0, 0, 1, False)):
            for offset, value in ((0xa9df6bc, done), (0x144c1c, event),
                    (0xa9e9c64, current), (0xa9e9c68, previous),
                    (0xa9e9c44, latch), (0xa9e9c48, enabled), (0x45c, 2)):
                self.put(vm, offset, value)
            end, _ = self.slice(vm, 0x115a59, (0x115ad8, 0x115add),
                ((UC_X86_REG_ESI, BATTLE), (UC_X86_REG_EBX, 0),
                 (UC_X86_REG_EDI, 1), (UC_X86_REG_ESP, SP)))
            self.assertEqual(end == 0x115ad8, expected)
            if expected:
                args = struct.unpack('<4I', vm.mem_read(vm.reg_read(UC_X86_REG_ESP), 16))
                self.assertEqual(args[0], 11)
                self.assertEqual(args[2:], (2, BATTLE + 0x44c))
            if event:
                self.assertEqual(self.get(vm, 0x144c1c), 0 if not done else event)
        self.slice(vm, 0x115af7, (0x115afa,), ((UC_X86_REG_ESI, BATTLE),))
        self.assertEqual(vm.reg_read(UC_X86_REG_ECX), NET)
        displacement = struct.unpack_from('<i', self.image, 0x115afb)[0]
        self.assertEqual(0x115aff + displacement, 0x13370)

    def test_completion_consumer_and_loop_state_transition_boundaries(self):
        vm = self.fixture()
        vm.mem_write(RECORD, b'\x89' + bytes(56))
        for pending in (0, 1):
            vm.mem_write(battle.TARGETS, struct.pack('<I', pending))
            vm.mem_write(SP + 0x2c, struct.pack('<I', battle.TARGETS))
            end, _ = self.slice(vm, 0x114332, (0x118bf0, 0x1145c0),
                ((UC_X86_REG_EBP, RECORD), (UC_X86_REG_EDI, RECORD),
                 (UC_X86_REG_ESI, BATTLE), (UC_X86_REG_ESP, SP)))
            self.assertEqual(end, 0x118bf0 if pending == 0 else 0x1145c0)
        self.put(vm, 0xa9e9c30, 7)
        self.slice(vm, 0x118e20, (0x118e35,), ((UC_X86_REG_ESI, BATTLE),))
        self.assertEqual(self.get(vm, 0xa9e9c30), 0)
        self.assertEqual(self.get(vm, 0xa9df6bc), 1)
        for latch, result, expected in ((0, 0, 0x115a40), (0, 1, 0x85070),
                                       (1, 0, 0x85260), (1, 1, 0x85260)):
            self.put(vm, 0xa9e9c50, latch)
            self.slice(vm, 0x115a0b, (expected,),
                ((UC_X86_REG_ESI, BATTLE), (UC_X86_REG_EBX, 0),
                 (UC_X86_REG_EDI, 1), (UC_X86_REG_EAX, result)))
        for result in (0, 1, 0x80000000):
            self.put(vm, 0x44, 1)
            self.slice(vm, 0x115a35, (0x115a40,),
                       ((UC_X86_REG_ESI, BATTLE), (UC_X86_REG_EAX, result)))
            self.assertEqual(self.get(vm, 0x44), 5 if result else 1)
        for result in (0, 1):
            end, _ = self.slice(vm, 0x11584d, (0x115c40, 0x115855),
                               ((UC_X86_REG_EAX, result),))
            self.assertEqual(end, 0x115c40 if result else 0x115855)

    def test_control_gate_continuously_reaches_original_queue(self):
        for event, current, previous, enabled in ((0,4,4,1),(1,5,4,0),(1,0xffffffff,4,0)):
            for connected in (0,1):
                vm = self.vm()
                for page in {BATTLE, (BATTLE+0x144c1c)&~4095,
                             (BATTLE+0xa9df6bc)&~4095, (BATTLE+0xa9e9c38)&~4095,
                             battle.SELECTOR&~4095}:
                    vm.mem_map(page,4096)
                for offset,value in ((0x10,NET),(0x3c,0x12345678),(0x44,1),
                    (0x45c,2),(0xa9df6bc,0),(0x144c1c,event),(FIRST,0),(SECOND,0),
                    (0xa9e9c64,current),(0xa9e9c68,previous),(0xa9e9c44,0),
                    (0xa9e9c48,enabled),(0xa9df73c,0xffffffff)):
                    self.put(vm,offset,value)
                vm.mem_write(BATTLE+0x51,b'\x03')
                vm.mem_write(BATTLE+0x44c,b'\x0e\x1b')
                vm.mem_write(NET+0x2cb8,bytes([connected]))
                vm.mem_write(NET+0x36c4,struct.pack('<I',0))
                before = bytes(vm.mem_read(BASE,len(self.image)))
                end,trace = self.slice(vm,0x115a59,(0x1191ee,),
                    ((UC_X86_REG_ESI,BATTLE),(UC_X86_REG_EBX,0),
                     (UC_X86_REG_EDI,1),(UC_X86_REG_ESP,SP)))
                self.assertEqual(end,0x1191ee)
                self.assertIn(0x115ad8,trace)
                self.assertIn(0x118e50,trace)
                self.assertNotIn(0x112130,trace)
                self.assertNotIn(0x1120b0,trace)
                self.assertNotIn(0x13370,trace)
                self.assertEqual(0x132e0 in trace,bool(connected))
                queued = self.queued(vm)
                if connected:
                    self.assertEqual(len(queued),17)
                    self.assertEqual(queued[:4],b'\x35\x03\x0b\x00')
                    self.assertEqual(struct.unpack_from('<HHI',queued,5),(0,0x2001,0x12345678))
                else:
                    self.assertEqual(queued,b'')
                self.assertEqual(self.get(vm,0xa9e9c44),0)
                self.assertEqual(bytes(vm.mem_read(BASE,len(self.image))),before)

    def test_evidence_is_pinned_and_model_is_research_only(self):
        self.assertFalse(gate.runtime_mutation_enabled)
        with self.assertRaises(ValueError):
            list(gate.disassembly(self.image[:-1]))
        for count in (0, 15, -1):
            with self.assertRaises(ValueError):
                gate.continuation_actions(count)
        with self.assertRaises(ValueError):
            gate.grant_controls(b'\x86\x03' + bytes(15), gate.Controls(0, 0, 0))

    def test_post_clock_latch_return_and_repeat_gate(self):
        world = 0x4000000
        for action in (1, 3, 11):
            for timestamp in (0, 0xffffffff):
                for prior_latch in (0, 1):
                    for second in (0, 1):
                        vm = self.vm()
                        for page in {BATTLE, (BATTLE + 0x144c1c) & ~4095,
                                (BATTLE + 0xa9df6bc) & ~4095,
                                (BATTLE + FIRST) & ~4095,
                                (BATTLE + 0xa9ea4c4) & ~4095,
                                (BATTLE + 0x144938 + 0xa7fbc58) & ~4095,
                                (battle.SELECTOR + 0x2e10) & ~4095,
                                (world + 0x232ec0) & ~4095}:
                            vm.mem_map(page, 4096)
                        for offset, value in ((0x20, world), (SECOND, second),
                                (0xa9e9c44, prior_latch), (0xa9e9c48, 1),
                                (0xa9e9c2c, 7), (0xa9ea4c4, 0xa5)):
                            self.put(vm, offset, value)
                        # Empty participant pool and absent text manager; cursor
                        # already selected, so native code needs no OS cursor call.
                        vm.mem_write(world + 0x232ec8, struct.pack('<I', 1))
                        vm.mem_write(SP, struct.pack('<12I', 11, 22, 33,
                            0, 0, 0, 0, battle.ready.RETURN, action, 3, 1, 0))
                        before = bytes(vm.mem_read(BASE, len(self.image)))
                        stop = 0x115740 if second else battle.ready.RETURN - BASE
                        _, trace = self.slice(vm, 0x119258, (stop,), (
                            (UC_X86_REG_ESI, BATTLE), (UC_X86_REG_EBX, 0),
                            (UC_X86_REG_EDI, 1), (UC_X86_REG_EAX, timestamp),
                            (UC_X86_REG_ESP, SP)))
                        for helper in (0x12d560, 0x11be40, 0x119b20, 0x834e0, 0x1a950):
                            self.assertIn(helper, trace)
                        expected_latch = 1 if action == 11 else prior_latch
                        self.assertEqual(self.get(vm, 0xa9e9c44), expected_latch)
                        self.assertEqual(self.get(vm, 0xa9e9c14), timestamp)
                        self.assertEqual(self.get(vm, 0xa9e9c2c), 0)
                        self.assertEqual(self.get(vm, 0xa9ea4c4), 0xa5 if second else 1)
                        self.assertEqual(bytes(vm.mem_read(world + 0x232f36, 4)), b'\x01\x00' * 2)
                        if not second:
                            self.assertEqual(vm.reg_read(UC_X86_REG_EAX), 1)
                            self.assertEqual(vm.reg_read(UC_X86_REG_ESP), SP + 48)
                        self.assertEqual(bytes(vm.mem_read(BASE, len(self.image))), before)
                        end, _ = self.slice(vm, 0x115a59, (0x115ad8, 0x115add), (
                            (UC_X86_REG_ESI, BATTLE), (UC_X86_REG_EBX, 0),
                            (UC_X86_REG_EDI, 1), (UC_X86_REG_ESP, SP)))
                        self.assertEqual(end, 0x115add if expected_latch else 0x115ad8)

    def test_builder_cleanup_continuously_consumes_controls_before_clock(self):
        world, panel = 0x4000000, 0x4400000
        for first, second in ((1, 0), (0, 1), (1, 1), (0, 0)):
            for connected in (0, 1):
                vm = self.vm()
                for page in {BATTLE, battle.TARGETS, battle.SELECTOR & ~4095,
                        (BATTLE + 0x144c1c) & ~4095,
                        (battle.SELECTOR + 0x2e34) & ~4095,
                        (BATTLE + 0xa9df6cc) & ~4095,
                        (BATTLE + FIRST) & ~4095,
                        (BATTLE + 0xab3b1d0) & ~4095,
                        (world + 0x232dae) & ~4095,
                        (world + 0x23d5e4) & ~4095, panel}:
                    vm.mem_map(page, 4096)
                for offset, value in ((0x10, NET), (0x20, world), (0x44, 1),
                        (FIRST, first), (SECOND, second), (WAIT, 0xa5),
                        (0xa9df73c, 0xffffffff), (0xa9e9c28, 7),
                        (0xa9e9c2c, 9), (0x46c, 0), (0x45c, 1),
                        (0xa9e9c48, 1)):
                    self.put(vm, offset, value)
                # Closed native handles, not patched helper returns. The 28
                # actor references address distinct inactive effect slots.
                vm.mem_write(BATTLE + 0xab3b1d0, b'\xff' * 12)
                for i, offset in enumerate((0x2e2c, 0x2e30, 0x2e34)):
                    vm.mem_write(battle.SELECTOR + offset,
                        struct.pack('<I', BATTLE + 0xab3b1d0 + i * 2))
                effects = BATTLE + 0xa9df74c
                for page in range((effects + 0x40) & ~4095,
                                  ((effects + 27 * 232 + 0x40) & ~4095) + 4096, 4096):
                    if page != (BATTLE + 0xa9df6cc) & ~4095:
                        vm.mem_map(page, 4096)
                vm.mem_write(BATTLE + 0xa9df6cc, struct.pack('<28I', *range(28)))
                for offset in (0x232dae, 0x232dd8, 0x232dd2, 0x232dce,
                               0x232dca, 0x232dc8, 0x232dd6, 0x232dd0,
                               0x232e04, 0x232e56):
                    vm.mem_write(world + offset, b'\xff\xff')
                vm.mem_write(world + 0x232ebc, struct.pack('<I', panel))
                vm.mem_write(panel + 0xdc, struct.pack('<I', world))
                vm.mem_write(world + 0x23d5e8, struct.pack('<I', 0xa5))
                vm.mem_write(battle.TARGETS, b'\x0e')
                vm.mem_write(BATTLE + 0x44c, b'\x0e')
                vm.mem_write(BATTLE + 0x51, b'\x03')
                vm.mem_write(NET + 0x2cb8, bytes([connected]))
                action = 1 if first or second else 11
                vm.mem_write(SP, struct.pack('<5I', battle.ready.RETURN,
                                             action, 3, 1, battle.TARGETS))
                before = bytes(vm.mem_read(BASE, len(self.image)))
                start = 0x115a59 if action == 11 else 0x118e50
                _, trace = self.slice(vm, start, (0x119252,), (
                    (UC_X86_REG_ECX, BATTLE), (UC_X86_REG_ESI, BATTLE),
                    (UC_X86_REG_EBX, 0), (UC_X86_REG_EDI, 1),
                    (UC_X86_REG_ESP, SP)))
                if action == 11:
                    self.assertIn(0x115ad8, trace)
                for helper in (0x112130, 0x1120b0, 0x111cd0, 0x111d30,
                               0x111cc0, 0x111c30, 0x111d60, 0x1127e0, 0x98c90):
                    self.assertIn(helper, trace)
                self.assertEqual(trace.count(0x360b0), 28)
                self.assertNotIn(0x13370, trace)
                expected = gate.consume_controls(gate.Controls(first, second, 0xa5))
                self.assertEqual((self.get(vm, FIRST), self.get(vm, SECOND),
                                  self.get(vm, WAIT)),
                                 (expected.first, expected.second, expected.waiting))
                self.assertEqual(self.get(vm, 0x46c), 0xffffffff)
                for offset in (0xa9e9c28, 0xa9e9c2c, 0xa9e9c44):
                    self.assertEqual(self.get(vm, offset), 0)
                self.assertEqual(bytes(vm.mem_read(world + 0x23d5e4, 8)), bytes(8))
                self.assertEqual(len(self.queued(vm)), 17 if connected else 0)
                self.assertEqual(bytes(vm.mem_read(BASE, len(self.image))), before)


if __name__ == '__main__':
    unittest.main()
