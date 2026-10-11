import struct
import unittest

from tools.strike_lab.current_monster_complete_attributes import (
    CompleteAttributesProbe, MissingSource, dispatch_tables, logical_record,
    SOURCE, MANAGER, PACKET, BASE,
)


class CompleteAttributesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.probe = CompleteAttributesProbe()

    def test_exact_dispatch_tables(self):
        tables = dispatch_tables(self.probe.image)
        self.assertEqual(tables['nondefault_opcodes'], {
            '1C': 0x114358, '38': 0x114525, '83': 0x11436b, '84': 0x1143dd,
            '85': 0x114449, '86': 0x114464, '87': 0x114518,
            '88': 0x114538, '89': 0x114582})
        self.assertEqual(tables['86_subtypes'], [0x11447a, 0x11449e, 0x1144d8,
                                                0x1144ae, 0x1144c8, 0x1144be, 0x11447a])
        self.assertEqual(tables['83_subtypes_1_to_23'][12], 0x117142)
        self.assertEqual(tables['83_actor_subtypes_1_to_23'][12], 0x12ca2d)

    def test_new_writer_and_real_signed_text_consumer_both_sides(self):
        for side in (0, 1):
            for index, word, poison in ((0, 123, 0xa5), (1, 0xffe2, 0x5a), (2, 0x8000, 0xcd)):
                with self.subTest(side=side, index=index):
                    n, before, trace = self.probe.receive(side, word, index=index, poison=poison)
                    expected = bytearray(before)
                    expected[0x1e7], expected[0x1e9] = 32 + index, 13
                    expected[0x27a + index], expected[0x27d + index] = 0x87, 9
                    struct.pack_into('<H', expected, 0x280 + index * 2, word)
                    self.assertEqual(bytes(n.vm.mem_read(SOURCE, 0x1000)), bytes(expected))
                    self.assertEqual(trace['stop_rva'], 0x1143a1)
                    writes = [(e['rva'], e['offset'], e['size'], e['hex'])
                              for e in trace['writes'] if e['region'] == 'actor']
                    self.assertEqual(writes[-3:], [
                        (0x12c1d2, 0x27a + index, 1, '87'),
                        (0x12c1e4, 0x27d + index, 1, '09'),
                        (0x12caaa, 0x280 + index * 2, 2, struct.pack('<H', word).hex())])
                    self.assertIn((0x12ca9c, 9, 2), [(e['rva'], e['offset'], e['size'])
                                                   for e in trace['reads'] if e['region'] == 'packet'])
                    self.assertEqual([(e['rva'], e['offset'], e['hex']) for e in trace['reads']
                                      if e['region'] == 'image' and 0x171600 <= e['offset'] < 0x171653],
                                     [(0x12c062, 0x171609, '87'), (0x12c051, 0x171610, '09')])
                    self.assertEqual(bytes(n.vm.mem_read(PACKET, 15)), logical_record(side, word, 32 + index))
                    result = self.probe.consume_amount(n, trace)
                    self.assertEqual(result['pose_prefix']['stop_rva'], 0x128824)
                    self.assertEqual(result['independent_format']['stop_rva'], 0x12886d)
                    signed = word - 65536 if word >= 32768 else word
                    self.assertEqual(result['text_ascii'], f'MP {signed:+d}')
                    self.assertIn((0x128852, 0x280 + index * 2, 2), [
                        (e['rva'], e['offset'], e['size']) for e in result['independent_format']['reads']
                        if e['region'] == 'actor'])
                    self.assertEqual(bytes(n.vm.mem_read(SOURCE, 0x1000)), bytes(expected))
                    self.assertEqual(bytes(n.vm.mem_read(BASE, len(self.probe.image))), self.probe.image)

    def test_missing_actor_and_unwritten_result_guard(self):
        for side in (0, 1):
            n, before, trace = self.probe.receive(side, 123, actor_present=False)
            self.assertFalse([e for e in trace['writes'] if e['region'] == 'actor'])
            self.assertEqual(bytes(n.vm.mem_read(SOURCE, 0x1000)), before)
            self.assertNotIn(0x12caaa, trace['visits'])
        n, _, trace = self.probe.receive(1, 123)
        n.put(MANAGER + 0x30b, b'\x01')
        with self.assertRaisesRegex(MissingSource, '128809'):
            self.probe.consume_amount(n, trace)

    def test_narrow_input_contract(self):
        for kwargs in ({'index': 3}, {'index': True}, {'poison': -1}, {'actor_present': 1}):
            with self.assertRaises(ValueError):
                self.probe.receive(0, 1, **kwargs)
        for args in ((2, 1, 32), (True, 1, 32), (0, 65536, 32), (0, 1, 256)):
            with self.assertRaises(ValueError):
                logical_record(*args)


if __name__ == '__main__':
    unittest.main()
