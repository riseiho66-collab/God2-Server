"""Focused current FB/3B identity and actual consumer probes, never wild stats."""
import struct
import unittest

from tools.strike_lab import current_monster_inspect_identity as subject


class InspectIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = subject.NativeInspect()

    def test_current_source_rows_are_natively_parsed_and_indexed(self):
        n = self.native
        self.assertEqual(set(n.metadata), {28001, 28002})
        for key, item in n.metadata.items():
            raw = bytes.fromhex(item['source']['raw_record_hex'])
            offset = item['source']['decoded_offset']
            self.assertEqual(n.decoded[offset:offset + len(raw)], raw)
            self.assertEqual(subject.digest(raw), item['source']['sha256'])
            fields = subject.growth.fields(item['source'])
            parsed = bytes.fromhex(item['native_record_hex'])
            self.assertEqual(parsed[8:8 + len(fields[4]) + 1], fields[4] + b'\0')
            self.assertEqual(parsed[0x122], int(fields[32]))
            self.assertEqual(n.call(0x59a60, key), item['address'])
            self.assertEqual(item['selector'], 34)
        self.assertEqual(subject.static_evidence(n.image)['packets']['FB']['length'], 73)

    def test_fb_packet_to_identity_bound_row_and_panel(self):
        n = self.native
        for key, slot in ((28001, 42), (28002, 44)):
            body = subject.diagnostic_body(key, slot)
            received = n.receive_fb(body)
            self.assertEqual(received['trace']['stop_rva'], 0xa52f5)
            reads = [r for r in received['trace']['reads'] if r[0] == 0xa52f3]
            self.assertEqual(reads, [[0xa52f3, n.MESSAGE + 1 + i, 4] for i in range(0, 72, 4)])
            self.assertEqual(received['trace']['writes'],
                             [(received['record_address'] + i, 4) for i in range(0, 72, 4)])
            selected = n.select_fb(slot)
            self.assertEqual(selected['trace']['stop_rva'], 0xa4151)
            self.assertEqual(selected['record_address'], received['record_address'])
            self.assertEqual(selected['metadata_address'], n.metadata[key]['address'])
            self.assertEqual(selected['trace']['writes'], [])
            index = n.TABLE + 0xb2d40 + key * 4
            self.assertIn([0x59a6f, index, 4], received['trace']['reads'])
            self.assertIn([0x59a6f, index, 4], selected['trace']['reads'])

    def test_twenty_panel_consumers_use_supplied_record_bits(self):
        n = self.native
        body = bytearray(subject.diagnostic_body())
        struct.pack_into('<I', body, 4, 0xffffbfff)
        struct.pack_into('<I', body, 8, 0xa5abcdef)
        struct.pack_into('<I', body, 12, 0x12345678)
        struct.pack_into('<4H', body, 0x10, 0, 0x7fff, 0x8000, 0xffff)
        received = n.receive_fb(bytes(body))
        selected = n.select_fb(42)
        self.assertEqual(selected['record_address'], received['record_address'])
        before = bytes(n.vm.mem_read(n.PET_UI, 0xe0))
        results = n.panel_fields(selected['record_address'])
        for result, spec in zip(results, subject.PANEL_FIELDS):
            start, stop, offset, shift, mask, field = spec
            width = 1 if mask == 0xff else 2 if mask == 0xffff else 4
            value = (int.from_bytes(body[offset:offset + width], 'little') >> shift) & mask
            self.assertEqual(result['arguments'][0], n.OWNER + 0xe2170)
            self.assertEqual(result['arguments'][1] & 0xffff, 1)
            self.assertEqual(result['arguments'][2], field)
            self.assertEqual(result['arguments'][4], value)
            self.assertTrue(any(address == selected['record_address'] + offset and size == width
                                for _, address, size in result['trace']['reads']))
            self.assertEqual(result['trace']['stop_rva'], stop)
            self.assertEqual(result['trace']['writes'], [])
        self.assertEqual(len(results), 20)
        self.assertEqual(bytes(n.vm.mem_read(n.PET_UI, 0xe0)), before)

    def test_full_inactive_receiver_preserves_sequential_supplied_values(self):
        n = self.native
        n.vm.mem_write(n.PET_UI, b'\xa5' * 0xd8)
        expected = bytearray(b'\xa5' * 0xd8)
        for seed in (0, 127, 255):
            for slot in (42, 43, 44):
                body = subject.diagnostic_body(28001 + (slot % 2), slot, seed)
                result = n.receive_fb_inactive(body)
                trace = result['trace']
                self.assertEqual(trace['stop_rva'], 0x1000)
                self.assertIn(0xad080, trace['pcs'])
                self.assertIn(0xad547, trace['pcs'])
                self.assertIn(0xa5392, trace['pcs'])
                self.assertNotIn(0xa5345, trace['pcs'])
                self.assertNotIn(0xa538b, trace['pcs'])
                self.assertEqual(trace['writes'],
                                 [(result['record_address'] + i, 4) for i in range(0, 72, 4)])
                start = (slot - 42) * 72
                expected[start:start + 72] = body
                self.assertEqual(bytes(n.vm.mem_read(n.PET_UI, 0xd8)), expected)
        rejected = n.receive_fb_inactive(subject.diagnostic_body(28000))
        self.assertEqual(rejected['trace']['writes'], [])
        self.assertNotIn(0xad080, rejected['trace']['pcs'])
        self.assertEqual(bytes(n.vm.mem_read(n.PET_UI, 0xd8)), expected)
        self.assertEqual(bytes(n.vm.mem_read(subject.BASE, len(n.image))), n.image)

    def test_tooltip_identity_labels_unsigned_values_and_type_branch(self):
        n = self.native
        for key in (28001, 28002):
            record = struct.pack('<I4HII', key | (34 << 16) | 0xff000000,
                                 0xffff, 0x8000, 0x1234, 7, 0xfedcba98, 0xe581ff00)
            result = n.tooltip(record)
            self.assertEqual(result['wrapper_arguments'][2] & 0xffff, 0x23)
            self.assertEqual(result['wrapper_arguments'][3] & 0xffff, key)
            self.assertEqual(result['wrapper_arguments'][4:], [n.metadata[key]['address'], n.INSTANCE])
            self.assertEqual(result['branch_trace']['stop_rva'], 0xb77dc)
            args = result['fields'][0]['arguments']
            self.assertEqual(args[2:], [n.labels[84]['address'], 0xe5, n.labels[575]['address'], 127])
            for item in result['fields'][1:]:
                expected = struct.unpack_from('<H', record, item['instance_word_offset'])[0]
                self.assertEqual(item['arguments'][2:], [n.labels[item['label']]['address'], expected])
                address = n.INSTANCE + (4 if item['instance_word_offset'] < 8 else 8)
                self.assertIn([item['native_read_pc'], address, 4], item['trace']['reads'])
        other = struct.pack('<I4HII', 28001 | (32 << 16), 1, 2, 3, 4, 0, 0)
        self.assertEqual(n.tooltip(other)['branch_trace']['stop_rva'], 0xb6f0e)
        labels = {key: subject.growth.fields(row['source'])[1] for key, row in n.labels.items()}
        self.assertEqual(labels[72], bytes.fromhex('b4bc'))
        self.assertEqual(labels[73], bytes.fromhex('c5e9'))
        self.assertEqual(labels[74], bytes.fromhex('a44f'))
        self.assertEqual(labels[75], bytes.fromhex('b374'))

    def test_missing_identity_is_not_fabricated_and_unknown_calls_stop(self):
        n = self.native
        received = n.receive_fb(subject.diagnostic_body(28000))
        self.assertEqual(received['trace']['stop_rva'], 0xa5390)
        self.assertEqual(received['trace']['writes'], [])
        received = n.receive_fb(subject.diagnostic_body(30600))
        self.assertEqual(received['trace']['stop_rva'], 0xa50d7)
        self.assertEqual(received['trace']['writes'], [])
        with self.assertRaises(ValueError):
            subject.static_evidence(n.image[:-1] + bytes((n.image[-1] ^ 1,)))
        n.prepare()
        with self.assertRaisesRegex(AssertionError, 'Unqualified inspect instruction'):
            n.slice(0x1077c0, (0x1077c1,), ())
        self.assertEqual(bytes(n.vm.mem_read(subject.BASE, len(n.image))), n.image)


if __name__ == '__main__':
    unittest.main()
