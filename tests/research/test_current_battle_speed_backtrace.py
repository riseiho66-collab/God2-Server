import unittest

from tools.strike_lab.current_battle_speed_backtrace import (
    run_group, pinned_image, logical_record, MissingSource,
    BASE, ACTORS, STRIDE, ACTOR_SIZE, QUEUE, BUFFER,
)


class SpeedBacktraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = pinned_image()

    def test_original_fifo_group_then_fixed_slot_activation(self):
        for order, poison in (((17, 5), 0xa5), ((5, 17), 0x5a)):
            records = ((order[0], 7), (order[1], 7), (17, 8))
            n, before, trace = run_group(records, poison=poison, image=self.image)
            self.assertEqual(trace['receive_order'], list(order))
            self.assertEqual(trace['activation_order'], [5, 17])
            self.assertEqual((trace['selected_marker'], trace['queue_cursor'], trace['activation_count']),
                             (7, 30, 2))
            self.assertEqual(trace['stop_rva'], 0x12ae2f)
            self.assertIn(0x1145db, trace['visits'])
            self.assertIn(0x12ac20, trace['visits'])
            self.assertEqual(trace['pending_hex'], logical_record(17, 8).hex())
            self.assertEqual(trace['marker_owner_hex'], '07')
            self.assertEqual(bytes(n.vm.mem_read(BUFFER, 45)), b''.join(logical_record(*r) for r in records))
            actor_reads = {(e['offset'], e['size']) for e in trace['reads']
                           if e['region'].startswith('actor_')}
            self.assertEqual(actor_reads, {(0x1a, 2), (0x1e7, 1), (0x1e9, 1), (0x239, 1)})
            self.assertEqual([e['hex'] for e in trace['writes'] if e['address'] == QUEUE + 8],
                             ['0f000000', '1e000000'])
            for pos, original in enumerate(before):
                expected = bytearray(original)
                for e in trace['writes']:
                    if e['region'] == f'actor_{pos}':
                        expected[e['offset']:e['offset'] + e['size']] = bytes.fromhex(e['hex'])
                self.assertEqual(bytes(n.vm.mem_read(ACTORS + STRIDE * pos, ACTOR_SIZE)), bytes(expected))
            self.assertEqual(bytes(n.vm.mem_read(BASE, len(self.image))), self.image)
            self.assertNotIn(0x12ca3a, trace['visits'])
            self.assertNotIn(0x128852, trace['visits'])
            self.assertFalse([e for e in trace['reads'] + trace['writes']
                              if e['region'] == 'manager' and e['offset'] in (0x30b, 0x30c)])

    def test_first_packet_marker_not_numeric_marker_sort(self):
        _, _, trace = run_group(((17, 90), (5, 3)), poison=0xcd, image=self.image)
        self.assertEqual(trace['receive_order'], [17])
        self.assertEqual(trace['activation_order'], [17])
        self.assertEqual((trace['selected_marker'], trace['queue_cursor'], trace['activation_count']),
                         (90, 15, 1))
        self.assertEqual(trace['pending_hex'], logical_record(5, 3).hex())

    def test_missing_source_and_narrow_contract(self):
        with self.assertRaisesRegex(MissingSource, '12AFEF'):
            run_group(missing_render_state=17, image=self.image)
        with self.assertRaisesRegex(MissingSource, '12AFEF'):
            run_group(((0, 7), (1, 8)), missing_render_state=1, image=self.image)
        for records in ((), ((17, 7), (5, 7)), ((28, 7), (5, 8)), ((17, 255), (5, 8))):
            with self.assertRaises(ValueError):
                run_group(records, image=self.image)


if __name__ == '__main__':
    unittest.main()
