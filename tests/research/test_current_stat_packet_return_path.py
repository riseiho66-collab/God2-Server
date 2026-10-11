import unittest

from tools.strike_lab.current_stat_packet_return_path import (
    run_action, static_evidence, pinned_image, SP, QUEUE_BYTES, QUEUE_COUNT,
)


class StatPacketReturnTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = pinned_image()

    def test_native_action_sources_and_queue_writer(self):
        for pet_slot, poison in ((42, 0xa5), (43, 0x3c), (44, 0xff)):
            for control in range(0x17, 0x1b):
                option = 4 if control == 0x17 else control - 0x17
                r = run_action(control=control, pet_slot=pet_slot, poison=poison,
                               item_slot=7, image=self.image)
                self.assertTrue(r['returned'])
                self.assertEqual(r['appended_hex'], bytes((0xd6, 7, pet_slot, option)).hex())
                self.assertEqual(r['queue_count_after'], 4)
                self.assertEqual(r['calls'][0]['payload_length'], 3)
                self.assertEqual(r['calls'][0]['payload_pointer'], SP + 0x14)
                self.assertIn(0xa57ff, r['visits'])
                self.assertIn(0x13365, r['visits'])
                self.assertLess(r['instruction_count'], 300)
                self.assertTrue(r['records_unchanged'])
                reads = [e for e in r['events'] if e['region'] == 'pet2']
                self.assertEqual({(e['offset'], e['size']) for e in reads}, {(0xdc, 4), (0xd8, 1)})
                writes = [e for e in r['events'] if e['region'] == 'queue' and e['access'] == 'write']
                self.assertEqual([(e['rva'], e['offset'], e['size']) for e in writes],
                                 [(0x13320, QUEUE_BYTES, 1),
                                  (0x13340, QUEUE_BYTES + 1, 1),
                                  (0x13340, QUEUE_BYTES + 2, 1),
                                  (0x13340, QUEUE_BYTES + 3, 1),
                                  (0x1334c, QUEUE_COUNT, 4)])
                self.assertEqual(r['original_monster_values_recovered'], 0)

    def test_missing_inventory_and_real_no_match_path(self):
        r = run_action(missing_inventory=True, image=self.image)
        self.assertEqual(r['stop_rva'], 0xa5799)
        self.assertEqual(r['queue_count_after'], 0)
        self.assertEqual(r['calls'], [])
        for flags in (0x20, 0x60):
            r = run_action(item_slot=None, event_flags=flags, image=self.image)
            self.assertEqual(r['appended_hex'], bytes((0xd6, flags, 43, 1)).hex())
            self.assertNotIn(0xa57ba, r['visits'])
            self.assertLess(r['instruction_count'], 300)

    def test_queue_boundaries_and_append_offset(self):
        r = run_action(queued_count=3, image=self.image)
        self.assertEqual((r['queue_count_before'], r['queue_count_after']), (3, 7))
        self.assertEqual(r['appended_hex'], 'd6072b01')
        for kwargs, stop in ((dict(queued_count=0xa00), 0x13370),
                             (dict(lock_pointer=0x12345678), 0x11970)):
            r = run_action(image=self.image, **kwargs)
            self.assertEqual(r['stop_rva'], stop)
            self.assertEqual(r['queue_count_before'], r['queue_count_after'])
            self.assertEqual(r['appended_hex'], '')
            self.assertNotIn(stop, r['visits'])

    def test_image_and_input_guards(self):
        changed = bytearray(self.image)
        changed[0xa57ff] ^= 1
        with self.assertRaises(ValueError):
            static_evidence(changed)
        for kwargs in (dict(control=0), dict(pet_slot=41), dict(item_slot=30)):
            with self.assertRaises(ValueError):
                run_action(image=self.image, **kwargs)


if __name__ == '__main__':
    unittest.main()
