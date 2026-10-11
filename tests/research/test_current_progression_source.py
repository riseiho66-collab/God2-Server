"""Current-only, bounded original-code source/consumer regressions."""
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from tools.strike_lab import current_progression_source as p


class ProgressionSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = p.pinned(p.IMAGE, p.IMAGE_SHA)
        cls.source = p.message_source(p.ROOT.parent / 'God2')

    def setUp(self):
        self.native = p.NativeSource(self.image, bytes.fromhex(self.source['format_hex']))

    def test_current_sources_only_and_open_rules(self):
        allowed = {p.IMAGE.resolve(), (p.ROOT.parent / 'God2' / p.MESSAGE_PATH).resolve()}
        seen = set()
        original = Path.read_bytes

        def read(path):
            self.assertIn(path.resolve(), allowed)
            seen.add(path.resolve())
            return original(path)

        with patch.object(Path, 'read_bytes', read):
            evidence = p.build_evidence(p.ROOT.parent / 'God2')
        self.assertEqual(seen, allowed)
        self.assertFalse(evidence['runtime_verified'])
        self.assertFalse(evidence['runtime_eligible'])
        self.assertEqual(evidence['logical_length'], 29)
        for rule in evidence['open_original_rules'].values():
            self.assertEqual(rule, {'status': 'OPEN', 'value': None})
        self.assertEqual(evidence['next_native_evidence']['rva'], 0x10acb)
        for group in ('executed_spans', 'static_spans'):
            for span in evidence[group].values():
                raw = self.image[span['rva']:span['end_rva_exclusive']]
                self.assertEqual(span['raw_hex'], raw.hex())
                self.assertEqual(span['sha256'], p.digest(raw))

    def test_pins_and_native_call_edges(self):
        changed = bytearray(self.image)
        changed[0xaa296] ^= 1
        with self.assertRaisesRegex(ValueError, 'Unqualified'):
            p.NativeSource(bytes(changed), b'%6.2f\xa2H')
        with self.assertRaisesRegex(ValueError, 'Unqualified'):
            p.NativeSource(self.image, b'%d')
        for call, destination in ((0x69fb1, 0xaa200), (0xa9b9c, 0xaa480),
                                  (0xaa4b0, 0x149630), (0xaa4c2, 0x1060f0),
                                  (0x1061d6, 0x149630), (0x13576, 0x12520),
                                  (0x12544, 0x10af0), (0x10acb, 0x10a10)):
            self.assertEqual(self.image[call], 0xe8)
            self.assertEqual(call + 5 + struct.unpack_from('<i', self.image, call + 1)[0], destination)
        self.assertEqual(self.image[0x171204:0x171208].hex(), '0ad7233c')
        self.assertEqual(self.image[0x171328:0x17132c].hex(), '0ad7233c')

    def test_upstream_original_byte_writer_and_partial_lengths(self):
        n = self.native
        raw = p.synthetic_packet(0xfedc)
        for size in range(1, 30):
            with self.subTest(size=size):
                result = n.receive(raw[:size])
                self.assertEqual(result['count'], size)
                self.assertEqual(bytes.fromhex(result['buffer_hex']), raw[:size] + b'\xa5' * (29 - size))
                self.assertEqual(result['trace']['stop_rva'], 0x13592 if size == 29 else 0x135be)
                byte_writes = [w for w in result['trace']['writes'] if w[0] == 0x10b34]
                self.assertEqual(byte_writes, [[0x10b34, n.CONNECTION + 0x2cc4 + i, 1, raw[i]]
                                               for i in range(size)])
                self.assertEqual(n.u32(n.CONNECTION + 0x1f6c), size)
                self.assertIn(0x120f, result['trace']['pcs'])
                self.assertIn(0x12fa, result['trace']['pcs'])
                self.assertIn([0x120f, p.BASE + 0x13e8, 4], result['trace']['reads'])

    def test_buffer_to_dispatch_to_exact_row_stores(self):
        n = self.native
        raw = p.synthetic_packet(0xfedc, 0x80)
        before, after, trace = n.packet(raw, (0x80, -128), buffered=True)
        row = 0xd8 + 0x3ec
        expected = bytearray(before)
        expected[row + 2] = raw[2]
        for packet_offset, destination in zip((3, 5, 7, 9, 11), (0x44, 0x48, 0x4c, 0x50, 0x54)):
            struct.pack_into('<I', expected, row + destination, struct.unpack_from('<H', raw, packet_offset)[0])
        expected[row + 0x38:row + 0x40] = raw[17:25]
        expected[row + 0x28:row + 0x2a] = b'\xdc\x7e'
        expected[row + 0x5a] = 1
        self.assertEqual(after, bytes(expected))
        self.assertEqual(trace['receive']['buffer_hex'], raw.hex())
        self.assertIn([0x68b61, p.BASE + 0x6b698, 4], trace['reads'])
        source = n.CONNECTION + 0x2cc4
        self.assertEqual([r for r in trace['reads'] if r[0] in (0xaa292, 0xaa2a0)],
                         [[0xaa292, source + 25, 2], [0xaa2a0, source + 25, 2]])
        self.assertEqual([w for w in trace['writes'] if w[0] in (0xaa29c, 0xaa2ac)],
                         [[0xaa29c, n.ACTOR + row + 0x28, 2, 0x7edc],
                          [0xaa2ac, n.ACTOR + row + 0x5a, 1, 1]])
        percent = n.percent(1)
        self.assertEqual([r for r in percent['trace']['reads'] if n.ACTOR <= r[1] < n.ACTOR + 0x1000],
                         [[0xa9b92, n.ACTOR + row + 0x28, 2]])
        self.assertEqual(bytes(n.vm.mem_read(n.ACTOR, 0x1000)), after)

    def test_no_match_zero_count_and_first_duplicate(self):
        n = self.native
        for keys in ((), (2,), (128,)):
            before, after, trace = n.packet(p.synthetic_packet(0xffff, 0x80), keys)
            self.assertEqual(before, after)
            self.assertEqual(trace['stop_rva'], 0x6b517)
        before, after, trace = n.packet(p.synthetic_packet(0x8123), (1, 1))
        self.assertEqual(trace['stop_rva'], 0xaa2af)
        self.assertEqual(after[0xd8 + 0x3ec:], before[0xd8 + 0x3ec:])

    def test_low15_units_high_bit_independence_and_format_width(self):
        n = self.native
        values = {0, 1, 99, 100, 101, 4999, 5000, 9999, 10000, 10001, 32766, 32767}
        values.update(1 << bit for bit in range(15))
        values.update(k * 100 + delta for k in (2, 17, 63, 99, 100, 101, 255, 327)
                      for delta in (-1, 0, 1))
        multiplier = struct.unpack('<f', bytes.fromhex('0ad7233c'))[0]
        for low in sorted(values):
            paired = []
            for flag in (0, 1):
                with self.subTest(low=low, flag=flag):
                    _, snapshot, _ = n.packet(p.synthetic_packet(low | flag << 15))
                    result = n.percent()
                    expected_bits = struct.pack('<f', low * multiplier)
                    expected_value = struct.unpack('<f', expected_bits)[0]
                    self.assertEqual(result['float32_hex'], expected_bits.hex())
                    # MOV CX updates only the low half; panel ID is a WORD.
                    self.assertEqual(result['bar_arguments'][0] & 0xffff, 7)
                    self.assertEqual(result['bar_arguments'][1:], [36, int(expected_value), 0])
                    self.assertIn(0x149649, result['trace']['pcs'])
                    text = n.text_arguments(expected_bits)
                    self.assertEqual(text['arguments'][0], n.UI + 0xe2170)
                    self.assertEqual(text['arguments'][1] & 0xffff, 7)
                    self.assertEqual(text['arguments'][2:], [36, 0, n.FORMAT])
                    self.assertEqual(text['double_hex'], struct.pack('<d', expected_value).hex())
                    self.assertEqual(bytes(n.vm.mem_read(n.ACTOR, 0x1000)), snapshot)
                    paired.append((result['float32_hex'], result['bar_arguments'], text['double_hex']))
            self.assertEqual(paired[0], paired[1])

    def test_other_scalar_and_opaque_bytes_do_not_supply_a_requirement(self):
        n = self.native
        results = []
        for scalar in (0, 1, 127, 128, 255):
            raw = bytearray(p.synthetic_packet(12345))
            raw[2] = scalar
            raw[13:17] = struct.pack('<I', scalar * 0x01010101)
            raw[27:29] = struct.pack('<H', scalar * 257)
            _, after, trace = n.packet(bytes(raw))
            self.assertEqual(after[0xda], scalar)
            packet_reads = [(r[1] - n.PACKET, r[2]) for r in trace['reads']
                            if n.PACKET <= r[1] < n.PACKET + 29]
            for start, size in packet_reads:
                self.assertTrue(set(range(start, start + size)).isdisjoint({13, 14, 15, 16, 27, 28}))
            results.append(n.percent()['float32_hex'])
        self.assertEqual(len(set(results)), 1)

    def test_bar_clamps_only_geometry_with_native_truncation(self):
        n = self.native
        multiplier = struct.unpack('<f', bytes.fromhex('0ad7233c'))[0]
        for value in (-2147483648, -1, *range(0, 328), 2147483647):
            for width in (1, 100, 137):
                result = n.bar(value, width)
                expected = 0 if value < 0 else width if value >= 100 else int(value * multiplier * width)
                self.assertEqual(result['rectangle'], [0, 0, expected, 10], (value, width))
        self.assertEqual(n.bar(50, 100)['rectangle'][2], 49)
        self.assertEqual(n.bar(100, 100)['rectangle'][2], 100)

    def test_guards_reject_ui_execution_exhaustion_and_bad_inputs(self):
        n = self.native
        n.prepare()
        with self.assertRaisesRegex(AssertionError, 'Unallowed native PC'):
            n.run(0xaa4c2, (0xaa4c7,), (p.EXECUTED['percent_conversion'],))
        with self.assertRaisesRegex(AssertionError, 'exhausted'):
            n.run(0xaa480, (0xaa4c2,), (p.EXECUTED['percent_conversion'],), count=1)
        for count in (0, 4097, True):
            with self.assertRaises(ValueError):
                n.run(0x12fa, (0x12ff,), (p.EXECUTED['length_value'],), count=count)
        for raw in (b'', b'\x31' * 28, b'\x31' * 30, b'\x30' + b'\0' * 28):
            with self.assertRaises(ValueError):
                n.packet(raw)
        for value, width in ((1 << 31, 100), (0, 0), (0, 4097)):
            with self.assertRaises(ValueError):
                n.bar(value, width)


if __name__ == '__main__':
    unittest.main()
