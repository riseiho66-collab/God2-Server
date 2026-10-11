"""Continuous current-image side1 calls, exact snapshots, no fabricated returns."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_battle_side1_scalars as side1
from tools.strike_lab.current_battle_entry import NativeRun, RETURN, pinned_image
from unicorn import UC_MEM_READ_UNMAPPED
from unicorn import x86_const as reg


def record(position=14, kind=0, value5=101, value9=83):
    raw = bytearray(b'\x5a' * 17)
    raw[:3] = bytes((0x86, kind, position))
    struct.pack_into('<II', raw, 5, value5, value9)
    return bytes(raw)


def actor(handle=0, gate=7, scalars=(31, 47, 101, 203)):
    raw = bytearray(b'\xa5' * side1.ACTOR_SIZE)
    struct.pack_into('<H', raw, 0x1a, gate)
    struct.pack_into('<H', raw, 0x1d8, handle)
    struct.pack_into('<4I', raw, 0xde8, *scalars)
    return bytes(raw)


def display(handles=(7, -1, -1, -1), width=83, height=12,
            divisors=(101, 203), numerators=(79, 59)):
    raw = bytearray(b'\xb6' * side1.DISPLAY_SIZE)
    struct.pack_into('<4H2h4I', raw, 0xa79c, *(h & 0xffff for h in handles),
                     width, height, *divisors, *numerators)
    return bytes(raw)


def graphic(state=2, resource=0xffff):
    raw = bytearray(b'\xc7' * side1.GRAPHIC_SIZE)
    raw[0] = state
    struct.pack_into('<H', raw, 0xe, resource)
    return bytes(raw)


def quotient(numerator, width, raw_divisor):
    divisor = raw_divisor if raw_divisor < 0x80000000 else raw_divisor - 0x100000000
    product = numerator * width
    value = abs(product) // abs(divisor)
    return (-value if (product < 0) != (divisor < 0) else value) & 0xffffffff


class CurrentBattleSide1ScalarsTests(unittest.TestCase):
    def run_case(self, raw=None, *, entities=None, displays=None, graphics=None, owner=0x89abcdef):
        return side1.consume(record() if raw is None else raw,
            entities={14: actor()} if entities is None else entities,
            displays={0: display()} if displays is None else displays,
            owner_value=owner, diagnostic_graphics=graphics)

    def changes(self, n):
        return [(pc, address, size, value & ((1 << (8 * size)) - 1))
                for pc, address, size, value in n.writes
                if not side1.STACK <= address < side1.STACK + 0x8000]

    def assert_memory(self, n, replacements=()):
        expected = {page: bytearray(raw) for page, raw in n.data_before.items()}
        for address, raw in replacements:
            for index, value in enumerate(raw):
                here = address + index
                expected[here & ~4095][here & 4095] = value
        for page, raw in expected.items():
            self.assertEqual(bytes(n.vm.mem_read(page, 4096)), bytes(raw), hex(page))
        self.assertEqual(bytes(n.vm.mem_read(side1.BASE, len(n.image))), n.image)

    def assert_complete(self, n, raw, original, d=None, graphics=None):
        position = raw[2]
        a = side1.actor_address(position)
        v5, v9 = struct.unpack_from('<II', raw, 5)
        expected_actor = bytearray(original)
        struct.pack_into('<I', expected_actor, 0xde8, v9)
        struct.pack_into('<I', expected_actor, 0xdf0, v5)
        handle = struct.unpack_from('<H', original, 0x1d8)[0]
        wanted = [(0x12d86c, a + 0xde8, 4, v9), (0x12d875, a + 0xdf0, 4, v5)]
        replacements = [(a, expected_actor)]
        if d is not None:
            pointer = side1.display_address(handle)
            expected_display = bytearray(d)
            expected_display[0x2f] = 1
            n1 = struct.unpack_from('<I', original, 0xdec)[0]
            d1 = struct.unpack_from('<I', original, 0xdf4)[0]
            struct.pack_into('<4I', expected_display, 0xa7a8, v5, d1, min(v9, v5), min(n1, d1))
            replacements.append((pointer, expected_display))
            wanted.insert(0, (0x109227, pointer + 0x2f, 1, 1))
            wanted += [(0x108fe6, pointer + 0xa7a8, 4, v5),
                       (0x108ff0, pointer + 0xa7ac, 4, d1)]
            width, height = struct.unpack_from('<2h', d, 0xa7a4)
            handles = struct.unpack_from('<2h', d, 0xa79c)
            old = struct.unpack_from('<2I', d, 0xa7b0)
            updated_graphics = {h: bytearray(g) for h, g in graphics.items()}
            for stage, numerators in enumerate((old, (min(v9, v5), min(n1, d1)))):
                if stage:
                    for off, supplied, limit, write_pc, clamp_pc in (
                        (0xa7b0, v9, v5, 0x108f7d, 0x108f87),
                        (0xa7b4, n1, d1, 0x108f97, 0x108fa2)):
                        wanted.append((write_pc, pointer + off, 4, supplied))
                        if supplied > limit:
                            wanted.append((clamp_pc, pointer + off, 4, limit))
                for channel, h in enumerate(handles):
                    if h < 0:
                        continue
                    rect = (0, 0, quotient(numerators[channel], width, (v5, d1)[channel]),
                            height & 0xffffffff)
                    target = side1.graphic_address(h)
                    struct.pack_into('<4I', updated_graphics[h], 0x50, *rect)
                    wanted += [(pc, target + off, 4, value) for pc, off, value in zip(
                        (0x1be0d, 0x1be12, 0x1be18, 0x1be1e), (0x50, 0x54, 0x58, 0x5c), rect)]
            replacements += [(side1.graphic_address(h), g) for h, g in updated_graphics.items()]
            self.assertEqual(n.visits.count(0x109280), 1)
            self.assertEqual(n.visits.count(0x108e70), 2)
            self.assertLess(n.visits.index(0x108fc0), n.visits.index(0x108f50))
        self.assertEqual(self.changes(n), wanted)
        self.assert_memory(n, replacements)
        self.assertEqual(n.stop, 0x114482)
        self.assertIsNone(n.fault)
        self.assertEqual(n.vm.reg_read(reg.UC_X86_REG_ESP), side1.SP)
        self.assertEqual(n.vm.reg_read(reg.UC_X86_REG_EAX), 1)
        self.assertEqual(n.vm.reg_read(reg.UC_X86_REG_FPCW), 0x037f)
        wrapper = next(call for call in n.calls if call[0] == 0x12d8c0)
        self.assertEqual(wrapper[1], side1.CONTEXT)
        self.assertEqual(wrapper[2][:3], (side1.BASE + 0x11738d, 0x89abcdef, 1))
        self.assertEqual(wrapper[2][3] & 255, position - 14)
        self.assertEqual(wrapper[2][4:], (v9, v5))
        setter = next(call for call in n.calls if call[0] == 0x12d840)
        self.assertEqual(setter[1], side1.CONTEXT)
        self.assertEqual(setter[2][0:2], (side1.BASE + 0x12d95b, 1))
        self.assertEqual(setter[2][2] & 255, position - 14)
        self.assertEqual(setter[2][3:], (v9, v5))
        self.assertEqual(n.visits.count(0x11e6e0), 2)
        slot = side1.CONTEXT + 0x38 + position * 24
        self.assertEqual([r for r in n.reads if side1.CONTEXT + 0x38 <= r[1] < side1.CONTEXT + 0x2d8],
                         [(0x11e75a, slot, 4)] * 2)
        self.assertEqual([r for r in n.reads if a <= r[1] < a + side1.ACTOR_SIZE],
            [(0x12d8e1, a + 0x1a, 2), (0x12d8e9, a + 0x1d8, 2)] +
            ([(0x12d90f, a + 0x1a, 2), (0x12d917, a + 0x1d8, 2)] if handle >= 4096 else []) +
            [(0x12d936, a + 0x1d8, 2), (0x12d85d, a + 0x1d8, 2)] +
            ([(0x12d87d, a + 0xdf4, 4), (0x12d893, a + 0xdec, 4),
              (0x12d899, a + 0xde8, 4), (0x12d89f, a + 0x1d8, 2)] if handle < 0x8000 else []))
        self.assertEqual([(address - side1.RECORD, size) for _, address, size in n.reads
                          if side1.RECORD <= address < side1.RECORD + 17],
                         [(1, 1), (2, 1), (5, 4), (9, 4)])
        self.assertEqual([(pc, address, size) for pc, address, size in n.reads
                          if address in (side1.PACKET_PAGE, side1.BATTLE + 0x83458, side1.OWNER)],
                         [(0x114332, side1.PACKET_PAGE, 1),
                          (0x117375, side1.BATTLE + 0x83458, 4), (0x11737f, side1.OWNER, 4)])

    def test_pinned_byte_witnesses(self):
        image = pinned_image()
        witnesses = {
            0x117388: 'e833650100', 0x12d8da: 'e8010effff',
            0x12d8e1: '66817e1a0010', 0x12d8e7: '7373',
            0x12d8fa: 'e841b9fdff', 0x109262: '6681bc0ab8a700000010',
            0x12d931: 'e89ab3fdff', 0x108d2c: 'e80f63f1ff',
            0x108e63: 'c23800', 0x12d942: 'e8b9b8fdff',
            0x109227: '88502f', 0x10922a: 'e851000000',
            0x12d956: 'e8e5feffff', 0x11e75a: '8b448e38',
            0x12d86c: '8996e80d0000', 0x12d875: '898ef00d0000',
            0x1b748: '803f01', 0x1b817: 'c20400',
            0x1be39: '6681fe8813', 0x1be45: 'e8569d0000',
            0x1be4d: 'c20800', 0x12d95f: 'c21400',
        }
        for pc, encoded in witnesses.items():
            expected = bytes.fromhex(encoded)
            self.assertEqual(image[pc:pc + len(expected)], expected, hex(pc))

    def test_same_state_packet_binds_every_side1_slot_with_native_returns(self):
        entities = {p: actor(handle=(0, 1, 4095)[p % 3], scalars=(p, p + 1, 101, 203))
                    for p in range(14, 28)}
        displays = {h: display() for h in (0, 1, 4095)}
        for position in range(14, 28):
            raw = record(position)
            n = self.run_case(raw, entities=entities, displays=displays, graphics={7: graphic()})
            self.assert_complete(n, raw, entities[position], displays[(0, 1, 4095)[position % 3]], {7: graphic()})
            self.assertNotIn(0x108cd0, n.visits)
            self.assertNotIn(0xe71e0, n.visits)

    def test_one_continuous_start_and_exact_display_read_footprint(self):
        starts = []
        original_run = NativeRun.run
        def observe(n, start, *args, **kwargs):
            starts.append(start)
            return original_run(n, start, *args, **kwargs)
        with patch.object(NativeRun, 'run', observe):
            n = self.run_case(graphics={7: graphic()})
        self.assertEqual(starts, [0x114332])
        p = side1.display_address(0)
        expected = [(0x109262, 0xa79c, 2), (0x109288, 0xa79c, 2),
                    (0x1092c6, 0xa79e, 2), (0x1092ee, 0xa7a2, 2), (0x109316, 0xa7a0, 2)]
        draw = [(0x108e7d, 0xa79c, 2), (0x108e8b, 0xa7b0, 4),
                (0x108e95, 0xa7a4, 2), (0x108e9c, 0xa7a6, 2),
                (0x108eb3, 0xa7a8, 4), (0x108ee8, 0xa79e, 2)]
        expected += draw + [(0x108f76, 0xa7a8, 4), (0x108f91, 0xa7ac, 4)] + draw
        self.assertEqual([(pc, address - p, size) for pc, address, size in n.reads
                          if p <= address < p + side1.DISPLAY_SIZE], expected)
        self.assert_complete(n, record(), actor(), display(), {7: graphic()})

    def test_subtype1_side1_returns_without_any_lookup_or_writes(self):
        for position in range(14, 28):
            n = self.run_case(record(position, kind=1), entities={}, displays={})
            self.assertEqual(n.stop, 0x1144a6)
            self.assertEqual(self.changes(n), [])
            self.assertNotIn(0x11e6e0, n.visits)
            self.assertNotIn(0x12d8c0, n.visits)
            self.assert_memory(n)

    def test_actor_unsigned_gate_and_null_is_actual_native_fault(self):
        for gate in (0x1000, 0x7fff, 0x8000, 0xffff):
            n = self.run_case(entities={14: actor(gate=gate)}, displays={})
            self.assertEqual(n.stop, 0x114482)
            self.assertEqual(self.changes(n), [])
            self.assertNotIn(0x109240, n.visits)
            self.assertEqual(n.visits.count(0x11e6e0), 1)
            self.assert_memory(n)
        for position in (14, 27):
            n = self.run_case(record(position), entities={}, displays={})
            self.assertEqual(n.fault, (0x12d8e1, UC_MEM_READ_UNMAPPED, 0x1a, 2))
            self.assertEqual(n.stop, 0x12d8e1)
            self.assertNotIn(0x109240, n.visits)
            self.assertEqual(self.changes(n), [])
            self.assert_memory(n)

    def test_invalid_display_handles_really_return_through_create_and_update_helpers(self):
        for handle in (4096, 32767, 32768, 65535):
            before = actor(handle=handle, gate=4095)
            n = self.run_case(entities={14: before}, displays={})
            self.assert_complete(n, record(), before)
            self.assertTrue({0x10924c, 0x108e63, 0x10922f, 0x12d8b2, 0x12d95f} <= set(n.visits))
            if handle < 32768:
                self.assertTrue({0x108ffb, 0x108fae} <= set(n.visits))
            else:
                self.assertNotIn(0x108fc0, n.visits)
            self.assertNotIn(0x108d2c, n.visits)

    def test_create_frontier_exact_arguments_no_actor_or_display_write(self):
        for handle in (0, 4095):
            for channel0 in (4096, 32767, 32768, 65535):
                d = display(handles=(channel0, -1, -1, -1))
                n = self.run_case(entities={14: actor(handle=handle, gate=4095)}, displays={handle: d})
                self.assertEqual(n.stop, 0x108d2c)
                self.assertNotIn(0x1f040, n.visits)
                self.assertNotIn(0x109200, n.visits)
                self.assertNotIn(0x12d840, n.visits)
                self.assertEqual(self.changes(n), [])
                sp = n.vm.reg_read(reg.UC_X86_REG_ESP)
                self.assertEqual(struct.unpack('<9I', n.vm.mem_read(sp, 36)),
                                 (4095, 3, 0xffffcdef, 0x44, 0xffffffe2, 5, 0x1325, 1, 0))
                self.assertEqual(n.vm.reg_read(reg.UC_X86_REG_ECX), side1.GRAPHICS)
                _, manager, args = next(call for call in n.calls if call[0] == 0x108cd0)
                self.assertEqual(manager, side1.MANAGER)
                self.assertEqual(args[0], side1.BASE + 0x12d936)
                self.assertEqual(args[1] & 0xffff, handle)
                self.assertEqual(args[2:], (4095, 3, 0xffffcdef, 0x45, 0xffffffff,
                                          0x44, 0xffffffe2, 5, 0xffffffe2, 5, 0xffffffe2, 11, 0x1324))
                self.assert_memory(n)

    def test_no_graphic_snapshot_stops_at_real_visibility_entry(self):
        n = self.run_case()
        p = side1.display_address(0)
        self.assertEqual(n.stop, 0x1b740)
        self.assertEqual(self.changes(n), [(0x109227, p + 0x2f, 1, 1)])
        self.assertNotIn(0x12d840, n.visits)
        sp = n.vm.reg_read(reg.UC_X86_REG_ESP)
        self.assertEqual(struct.unpack('<2I', n.vm.mem_read(sp, 8)),
                         (side1.BASE + 0x1092c6, side1.graphic_address(7)))
        changed = bytearray(display())
        changed[0x2f] = 1
        self.assert_memory(n, [(p, changed)])

    def test_inactive_graphics_are_explicit_and_active_visibility_stops(self):
        for state in (0, 2, 255):
            for resource in (5000, 65535):
                g = {7: graphic(state, resource)}
                n = self.run_case(graphics=g)
                self.assert_complete(n, record(), actor(), display(), g)
        n = self.run_case(graphics={7: graphic(state=1)})
        self.assertEqual(n.stop, 0x1b751)
        self.assertNotIn(0x12d840, n.visits)
        self.assertEqual(len(self.changes(n)), 1)

    def test_all_visibility_handles_order_and_two_channel_rectangles(self):
        d = display(handles=(0, 4095, 8, 9), width=-83, height=-12)
        g = {h: graphic() for h in (0, 4095, 8, 9)}
        n = self.run_case(displays={0: d}, graphics=g)
        self.assert_complete(n, record(), actor(), d, g)
        self.assertEqual([address for pc, address, size in n.reads if pc == 0x1b748],
                         [side1.graphic_address(h) for h in (0, 4095, 9, 8)])
        self.assertEqual(n.visits.count(0x1b817), 4)
        self.assertEqual(n.visits.count(0x1be4d), 4)

    def test_unsigned_clamps_raw_dwords_and_signed_display_arithmetic(self):
        values = (1, 3, 101, 0x7fffffff, 0x80000000, 0xffffffff)
        for value in values:
            for numerator in (0, 1, 0x80000000, 0xffffffff):
                for width in (-32768, 0, 32767):
                    raw = record(27, value5=value, value9=numerator)
                    before = actor(scalars=(33, numerator, 55, value), gate=0)
                    d = display(handles=(7, 8, -1, -1), width=width, numerators=(0xffffffff, 37))
                    g = {7: graphic(), 8: graphic()}
                    n = self.run_case(raw, entities={27: before}, displays={0: d}, graphics=g)
                    self.assert_complete(n, raw, before, d, g)

    def test_zero_divisor_stops_before_unguarded_native_divide(self):
        n = self.run_case(record(value5=0), graphics={7: graphic()})
        self.assertEqual(n.stop, 0x108ecd)
        self.assertNotIn(0x149630, n.visits)
        self.assertNotIn(0x108f50, n.visits)
        self.assertEqual([pc for pc, *_ in self.changes(n)], [0x109227, 0x12d86c, 0x12d875, 0x108fe6, 0x108ff0])
        n = self.run_case(entities={14: actor(scalars=(1, 2, 101, 0))},
                          displays={0: display(handles=(7, 8, -1, -1))}, graphics={7: graphic(), 8: graphic()})
        self.assertEqual(n.stop, 0x108f23)
        self.assertEqual(n.visits.count(0x1be4d), 1)
        self.assertNotIn(0x108f50, n.visits)

    def test_real_resource_rect_frontier_after_exact_partial_copies(self):
        n = self.run_case(graphics={7: graphic(resource=4999)})
        self.assertEqual(n.stop, 0x1be45)
        self.assertNotIn(0x25ba0, n.visits)
        self.assertNotIn(0x108f50, n.visits)
        self.assertEqual([pc for pc, *_ in self.changes(n)],
                         [0x109227, 0x12d86c, 0x12d875, 0x108fe6, 0x108ff0,
                          0x1be0d, 0x1be12, 0x1be18, 0x1be1e])
        sp = n.vm.reg_read(reg.UC_X86_REG_ESP)
        resource, rect = struct.unpack('<2I', n.vm.mem_read(sp, 8))
        self.assertEqual(resource & 0xffff, 4999)
        self.assertEqual(struct.unpack('<4I', n.vm.mem_read(rect, 16)), (0, 0, 64, 12))
        self.assertEqual(n.vm.reg_read(reg.UC_X86_REG_ECX), side1.RESOURCE_OWNER)

    def test_signed_render_handle_vs_unsigned_visibility_gate(self):
        for second in (4096, 32767):
            n = self.run_case(displays={0: display(handles=(7, second, -1, -1))}, graphics={7: graphic()})
            self.assertEqual(n.stop, 0x1bdde)
            self.assertNotIn(0x2c70, n.visits)
            self.assertEqual(n.visits.count(0x1b740), 1)
        for second in (32768, 65535):
            d = display(handles=(7, second, -1, -1))
            n = self.run_case(displays={0: d}, graphics={7: graphic()})
            self.assert_complete(n, record(), actor(), d, {7: graphic()})

    def test_opaque_packet_bytes_do_not_supply_sources_or_identity(self):
        for offset in (3, 4, 13, 14, 15, 16):
            for value in (0, 127, 255):
                raw = bytearray(record())
                raw[offset] = value
                n = self.run_case(bytes(raw), graphics={7: graphic()})
                self.assert_complete(n, bytes(raw), actor(), display(), {7: graphic()})

    def test_direct_wrapper_low_byte_side_slot_and_helper_low_word(self):
        for side in (0, 2, 255):
            n = side1.prepare(record(), entities={}, displays={}, owner_value=0)
            n.put(side1.SP, struct.pack('<6I', RETURN, 0, side, 0, 17, 19))
            n.registers(ecx=side1.CONTEXT)
            n.run(0x12d8c0, side1.RANGES, side1.STOPS)
            self.assertEqual(n.stop, RETURN)
            self.assertNotIn(0x11e6e0, n.visits)
            self.assertEqual(n.vm.reg_read(reg.UC_X86_REG_ESP), side1.SP + 24)
        for slot in (14, 255):
            n = side1.prepare(record(), entities={}, displays={}, owner_value=0)
            n.put(side1.SP, struct.pack('<6I', RETURN, 0, 1, slot, 17, 19))
            n.registers(ecx=side1.CONTEXT)
            n.run(0x12d8c0, side1.RANGES, side1.STOPS)
            self.assertEqual(n.stop, 0x11e718)
            self.assertNotIn(0x2c70, n.visits)
        for handle, expected in ((0x12340000, 1), (0x12341000, 0), (0xabcdffff, 0)):
            n = side1.prepare(record(), entities={}, displays={0: display()}, owner_value=0)
            n.put(side1.SP, struct.pack('<2I', RETURN, handle))
            n.registers(ecx=side1.MANAGER)
            n.run(0x109240, side1.RANGES, side1.STOPS)
            self.assertEqual(n.vm.reg_read(reg.UC_X86_REG_EAX), expected)
            self.assertEqual(n.vm.reg_read(reg.UC_X86_REG_ESP), side1.SP + 8)

    def test_input_contract_and_missing_snapshots_fail_closed(self):
        for raw in (b'', record()[:-1], record() + b'\0', bytearray(record()),
                    record(position=13), record(position=28), record(kind=2)):
            with self.assertRaises(ValueError):
                self.run_case(raw)
        for kwargs in ({'entities': {13: actor()}}, {'entities': {14: b''}},
                       {'displays': {4096: display()}}, {'displays': {0: b''}},
                       {'graphics': {7: b''}}, {'owner': True}):
            with self.assertRaises(ValueError):
                self.run_case(**kwargs)
        with self.assertRaisesRegex(AssertionError, 'Unqualified'):
            self.run_case(displays={})
        with self.assertRaisesRegex(AssertionError, 'Unqualified'):
            self.run_case(graphics={})

    def test_direct_wrapper_uses_low_bytes_and_setter_has_its_own_null_check(self):
        before = actor(handle=0xffff)
        n = side1.prepare(record(27), entities={27: before}, displays={}, owner_value=0)
        n.put(side1.SP, struct.pack('<6I', RETURN, 0, 0x12340001, 0xabcdef0d, 17, 19))
        n.registers(ecx=side1.CONTEXT)
        n.run(0x12d8c0, side1.RANGES, side1.STOPS)
        self.assertEqual(n.stop, RETURN)
        self.assertEqual(n.vm.reg_read(reg.UC_X86_REG_ESP), side1.SP + 24)
        expected = bytearray(before)
        struct.pack_into('<I', expected, 0xde8, 17)
        struct.pack_into('<I', expected, 0xdf0, 19)
        self.assert_memory(n, [(side1.actor_address(27), expected)])
        n = side1.prepare(record(), entities={}, displays={}, owner_value=0)
        n.put(side1.SP, struct.pack('<5I', RETURN, 1, 0, 17, 19))
        n.registers(ecx=side1.CONTEXT)
        n.run(0x12d840, side1.RANGES, side1.STOPS)
        self.assertEqual(n.stop, RETURN)
        self.assertEqual(n.vm.reg_read(reg.UC_X86_REG_ESP), side1.SP + 20)
        self.assertEqual(self.changes(n), [])
        self.assert_memory(n)

    def test_zero_and_all_bits_copy_without_any_display_work(self):
        for value5 in (0, 1, 0x7fffffff, 0x80000000, 0xffffffff):
            for value9 in (0, 1, 0x7fffffff, 0x80000000, 0xffffffff):
                raw = record(value5=value5, value9=value9)
                before = actor(handle=0xffff)
                n = self.run_case(raw, entities={14: before}, displays={})
                self.assert_complete(n, raw, before)


if __name__ == '__main__':
    unittest.main()
