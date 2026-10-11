"""Current-only native storage writer and ACTMIS instance provenance."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_quest_instance as q


class CurrentQuestInstanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = q.evidence()

    def test_pin_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'requalification'):
            q.NativeInstance(bytes([self.image[0] ^ 1]) + self.image[1:])

    def test_dispatch_length_and_all_50_slot_writes(self):
        for slot in range(50):
            with self.subTest(slot=slot):
                n = q.NativeInstance(self.image)
                self.assertEqual(n.length(), 25)
                self.assertEqual(n.read(q.BASE + 0x6b5d4 + 4 * 0x3b, '<I'),
                                 (q.BASE + 0x6a029,))
                packet = q.fixture(slot=slot)
                self.assertTrue(n.ingest(packet))
                start = q.UI + q.SLOTS - 4
                expected = bytearray(b'\xcc' * (50 * 24 + 8))
                expected[4 + slot * 24:24 + slot * 24] = packet[5:]
                self.assertEqual(bytes(n.vm.mem_read(start, len(expected))), expected)
                writes = [e for e in n.events if e['access'] == 'write']
                self.assertEqual([(e['rva'], e['offset'], e['size']) for e in writes],
                                 [(0x98e2b, 24 * slot + off, 4) for off in range(0, 20, 4)])
                self.assertEqual(bytes(n.vm.mem_read(n.packet_address, 25)), packet)

    def test_signed_slot_rejection_returns_without_storage_writes(self):
        for slot in (50, 127, 128, 255):
            with self.subTest(slot=slot):
                n = q.NativeInstance(self.image)
                self.assertFalse(n.ingest(q.fixture(slot=slot)))
                self.assertEqual(n.getreg('ESP'), q.SP)
                self.assertFalse(any(e['access'] == 'write' for e in n.events))

    def test_each_truncated_valid_slot_input_faults(self):
        from unicorn import UcError, UC_ERR_READ_UNMAPPED
        for length in range(1, 25):
            with self.subTest(length=length):
                n = q.NativeInstance(self.image)
                with self.assertRaises(UcError) as error:
                    n.ingest(q.fixture()[:length])
                self.assertEqual(error.exception.errno, UC_ERR_READ_UNMAPPED)
                if length == 24:
                    writes = [e for e in n.events if e['access'] == 'write']
                    self.assertEqual(len(writes), 4)

    def test_serial_and_low_word_independent_through_native_callers(self):
        for slot, serial, low_word in ((0, 0, 1), (7, 1, 2),
                                      (38, 169, 0x1234), (49, 65535, 0x7f57)):
            with self.subTest(slot=slot, serial=serial):
                n = q.NativeInstance(self.image)
                packet = q.fixture(slot, serial, low_word)
                n.ingest(packet)
                result = n.forward(slot, low_word)
                self.assertEqual(result['serial'], serial)
                self.assertEqual(bytes(n.vm.mem_read(q.VIEW + q.DISPLAY - 4, 28)),
                                 b'\xdd' * 4 + packet[5:] + b'\xdd' * 4)
                self.assertIn(dict(phase='serial_read', rva=0xb9f9a, access='read',
                                   region='display', offset=8, size=2), n.events)
                self.assertEqual(bytes(n.vm.mem_read(q.BASE, len(self.image))), self.image)

    def test_writer_preserves_arbitrary_bytes_without_actmis_validation(self):
        n = q.NativeInstance(self.image)
        packet = bytearray(q.fixture(category=3, serial=65535))
        packet[5:] = bytes(range(20))
        self.assertTrue(n.ingest(packet))
        self.assertEqual(bytes(n.vm.mem_read(q.UI + q.SLOTS, 20)), packet[5:])

    def test_slots_38_to_41_have_an_excluded_widget_branch(self):
        for slot in range(38, 42):
            n = q.NativeInstance(self.image)
            n.write(q.VIEW + 0x24, '<I', 1)
            packet = q.fixture(slot=slot)
            n.vm.mem_write(q.PACKET, packet)
            n.setreg('ESP', q.SP)
            n.setreg('EBP', q.UI - 0xa7f2f6c)
            n.setreg('EBX', q.PACKET)
            n.run(0x68b4e, q.BASE + 0x961a0)
            self.assertFalse(any(e['access'] == 'write' for e in n.events))

    def test_report_has_exact_writer_binding_and_explicit_boundaries(self):
        report = q.build_report()
        self.assertEqual(report['logical_opcode'], 0x3b)
        self.assertEqual(report['logical_length'], 25)
        self.assertEqual(report['result']['serial'], 169)
        self.assertIn('Synthetic', report['boundary'])
        self.assertIn('turn-in and rewards', report['open'])

    def test_all_native_requirements_from_packet_storage_to_text(self):
        from tools.strike_lab import current_quest_requirements as requirements
        image,table=requirements.evidence()
        consumer=requirements.NativeRequirements(image)
        records=[consumer.load_row(requirements.source_row(row)) for row in table['records']]
        self.assertEqual(len(records),169)
        for record in records:
            serial=record['serial']
            slot=(serial-1)%50
            with self.subTest(serial=serial,slot=slot):
                writer=q.NativeInstance(self.image)
                packet=q.fixture(slot=slot,serial=serial,low_word=0x1234)
                self.assertTrue(writer.ingest(packet))
                self.assertTrue(writer.selection_gate(slot)['copied'])
                selected=bytes(writer.vm.mem_read(q.VIEW+q.DISPLAY,20))
                self.assertEqual(writer.forward(slot,0x1234)['serial'],serial)
                instance=bytes(writer.vm.mem_read(q.VIEW+q.DISPLAY,20))
                self.assertEqual(instance,selected)
                self.assertEqual(instance,packet[5:])
                count=record['nonzero_pair_count']
                keys=record['item_keys_u16'][:count]
                result=consumer.consume_instance(instance,keys)
                self.assertEqual(result['lookup_keys'],keys)
                self.assertEqual([c['quantity'] for c in result['format_calls']],
                                 record['quantities_u8'][:count])
                expected=bytes.fromhex(record['label_hex'])+b''.join(
                    b'\n'+requirements.LOOKUP_FIXTURE_NAME+b' x '+str(n).encode()
                    for n in record['quantities_u8'][:count])
                self.assertEqual(bytes.fromhex(result['text_hex']),expected)
                self.assertEqual(bytes(consumer.vm.mem_read(requirements.INSTANCE,20)),instance)

    def test_requirement_instance_boundary_rejects_wrong_size_and_category(self):
        from tools.strike_lab import current_quest_requirements as requirements
        consumer=requirements.NativeRequirements(self.image)
        for size in (0,1,19,21,25):
            with self.subTest(size=size),self.assertRaises(ValueError):
                consumer.consume_instance(bytes(size))
        with self.assertRaises(ValueError):consumer.consume_instance(q.fixture(category=3)[5:])

    def test_native_selection_event_reaches_copy_for_all_slots(self):
        for slot in range(50):
            with self.subTest(slot=slot):
                native=q.NativeInstance(self.image)
                packet=q.fixture(slot=slot)
                self.assertTrue(native.ingest(packet))
                result=native.selection_gate(slot)
                self.assertEqual(result,{'stop_rva':0x91431,'copied':True,'returned':False})
                self.assertEqual(bytes(native.vm.mem_read(q.VIEW+q.DISPLAY,20)),packet[5:])
                writes=[e for e in native.events if e['phase']=='selection_gate' and e['access']=='write' and e['region']=='display']
                self.assertEqual([(e['rva'],e['offset'],e['size']) for e in writes],
                                 [(0x9142f,offset,4) for offset in range(0,20,4)])
                self.assertEqual(bytes(native.vm.mem_read(q.BASE,len(self.image))),self.image)

    def test_native_selection_rejections_never_copy(self):
        for slot,arguments,stop in ((-1,{},None),(0,{'flags':0},None),
                                   (0,{'control':0x16},None),
                                   (0,{'matching_context':False},0x914dc),
                                   (0,{'definition':False},0x91494)):
            with self.subTest(slot=slot,arguments=arguments):
                native=q.NativeInstance(self.image)
                native.ingest(q.fixture())
                result=native.selection_gate(slot,**arguments)
                self.assertFalse(result['copied'])
                self.assertEqual(result['stop_rva'],stop)
                self.assertEqual(bytes(native.vm.mem_read(q.VIEW+q.DISPLAY,20)),b'\xdd'*20)
                if result['returned']:self.assertEqual(native.getreg('ESP'),q.SP+12)

    def test_selection_gate_with_all_native_mis_definitions(self):
        from tools.strike_lab.current_item_metadata import NativeItemMetadata
        metadata=NativeItemMetadata()
        rows=metadata.sections['MIS']['records']
        self.assertEqual(len(rows),987)
        for index in range(len(rows)):
            parsed=metadata.item_row('MIS',index)
            with self.subTest(key=parsed['key']):
                native=q.NativeInstance(self.image)
                # The low key is native; category/serial assignment is synthetic.
                packet=q.fixture(slot=0,serial=1,low_word=parsed['key'])
                self.assertTrue(native.ingest(packet))
                self.assertTrue(native.selection_gate(0,definition_record=parsed['record'])['copied'])
                self.assertEqual(bytes(native.vm.mem_read(q.VIEW+q.DISPLAY,20)),packet[5:])
                self.assertEqual(bytes(native.vm.mem_read(q.RESOURCE+0x4000,0x18c)),parsed['record'])


if __name__ == '__main__':
    unittest.main()
