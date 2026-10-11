"""Original current instructions: NPC mission dialogue request, never quest rules."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from tools.strike_lab import current_quest_action as q


class CurrentQuestActionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = q.evidence()

    def native(self, request=0x1234, reply=2, context=0x9a):
        n = q.NativeAction(self.raw)
        p = q.fixture(request_word=request, reply_word=reply, context_byte=context)
        incoming = n.ingest(p)
        self.assertEqual(incoming['stop_rva'], 0xc8234)
        self.assertEqual(bytes(n.vm.mem_read(n.packet_address, len(p))), p)
        return n, incoming

    def action(self, n, **changes):
        state = dict(page=0, page_count=1, mode=1, threshold=0, choice=-1,
                     stack_byte=0xa5, queued_count=0, lock_pointer=0)
        state.update(changes)
        return n.action(**state)

    def test_image_pin_and_exact_current_provenance(self):
        with self.assertRaisesRegex(ValueError, 'requalification'):
            q.NativeAction(bytes([self.raw[0] ^ 1]) + self.raw[1:])
        self.assertEqual(struct.unpack_from('<I', self.raw, 0x6b5d4 + 4 * 0x7a)[0],
                         q.BASE + 0x6abd7)
        self.assertEqual(self.raw[0x1318:0x131e].hex(), 'b8feffffffc3')
        self.assertEqual(self.raw[0x56308:0x5630d].hex(), 'be08a15800')
        self.assertEqual(self.raw[0x18a108:0x18a11a], b'NPCMissionMessage\0')
        self.assertEqual(self.raw[0x56349:0x5634e].hex(), 'e842170000')
        self.assertEqual(self.raw[0x57af1:0x57af7].hex(), '89854c2c0b00')
        self.assertEqual(self.raw[0xc8126:0xc812c].hex(), '8b894c2c0b00')
        self.assertEqual(self.raw[0x97de7:0x97def].hex(), '6a06526885000000')
        self.assertEqual(struct.unpack_from('<4I', self.raw, 0xc86cc),
                         tuple(q.BASE + x for x in (0xc85e8, 0xc85ca, 0xc85f1, 0xc85fe)))

    def test_inbound_header_and_echoed_words_are_native_reads(self):
        for request, reply, context in ((0, 0, 0), (65535, 32767, 255),
                                         (0x1234, 0x8000, 0x9a), (42, 0xfffe, 1)):
            with self.subTest(request=request, reply=reply):
                n, incoming = self.native(request, reply, context)
                normalized = reply & 0x7fff
                self.assertEqual(incoming['request_word'], request)
                self.assertEqual(incoming['context_byte'], context)
                self.assertEqual(incoming['normalized_reply_word'], normalized)
                self.assertEqual(incoming['high_bit_flag'], int(bool(reply & 0x8000)))
                result = self.action(n)
                self.assertEqual(result['appended_hex'],
                                 (b'\x85' + struct.pack('<HHBB', request, normalized,
                                                        context, 0xa5)).hex())
                self.assertEqual(result['stop_rva'], 0xc8350)
                self.assertEqual(result['action_state'], 1)
                self.assertEqual(result['queue_count_after'], 7)
                self.assertEqual(result['high_bit_flag'], 0)
                reads = [(e['rva'], e['offset'], e['size']) for e in n.events
                         if e['region'] == 'packet' and e['access'] == 'read']
                base = n.packet_address - q.PACKET
                for expected in ((0xc7f48, base + 4, 1), (0xc80f7, base + 9, 2),
                                 (0xc80fb, base + 5, 2)):
                    self.assertIn(expected, reads)

    def test_ffff_reply_sentinel_closes_without_request(self):
        n, incoming = self.native(reply=0xffff)
        self.assertEqual(incoming['normalized_reply_word'], 0xffff)
        self.assertEqual(incoming['high_bit_flag'], 0)
        result = self.action(n)
        self.assertEqual(result['stop_rva'], 0xc8350)
        self.assertEqual(result['calls'], [])
        self.assertEqual(result['queue_count_after'], 0)
        self.assertEqual(result['action_state'], 0x12345678)

    def test_signed_page_gate_and_non_mode4_values(self):
        for page, count, sends in ((0, 1, True), (0, 2, False), (1, 2, True),
                                    (2, 2, False), (-1, 0, True),
                                    (-1, 1, False), (0x7fffffff, -0x80000000, True)):
            n, _ = self.native()
            result = self.action(n, page=page, page_count=count)
            self.assertEqual(bool(result['calls']), sends, (page, count))
            if not sends:
                self.assertTrue(result['returned'])
                self.assertEqual(result['esp'], q.SP + 4)
                self.assertEqual(result['action_state'], 0x12345678)
        for mode in (0, 1, 2, 3, 5, 0xffff):
            n, _ = self.native()
            self.assertEqual(self.action(n, mode=mode)['appended_hex'], '85341202009aa5')

    def test_mode4_threshold_and_all_eight_choices(self):
        for choice in range(8):
            n, _ = self.native(reply=0x8002)
            result = self.action(n, page=2, page_count=9, mode=4,
                                 threshold=2, choice=choice)
            self.assertEqual(result['appended_hex'],
                             (b'\x85' + struct.pack('<HHBB', 0x1234, choice, 0x9a, 0xa5)).hex())
            self.assertEqual(result['high_bit_flag'], 1)
            self.assertEqual(n.read(q.UI + q.CHOICE, '<h'), (choice,))
        for page, count, threshold, sends in ((1, 9, 2, False), (2, 9, 2, True),
                                               (3, 9, 2, True), (-1, 9, 0, False),
                                               (-1, 9, -1, True), (0, 1, 7, True)):
            n, _ = self.native()
            result = self.action(n, page=page, page_count=count, mode=4,
                                 threshold=threshold, choice=0)
            self.assertEqual(bool(result['calls']), sends, (page, count, threshold))

    def test_invalid_choice_stops_before_original_error_function(self):
        for choice in (-32768, -1, 8, 32767):
            n, _ = self.native()
            result = self.action(n, mode=4, choice=choice)
            self.assertEqual(result['stop_rva'], 0x75d60)
            self.assertEqual(result['calls'], [])
            self.assertEqual(result['action_state'], 0x12345678)
            self.assertEqual(n.read(n.getreg('ESP') + 4, '<I'), (0x26e,))

    def test_sixth_payload_byte_is_preexisting_stack_not_padding(self):
        for poison in (0, 0x55, 0xa5, 0xff):
            n, _ = self.native()
            result = self.action(n, stack_byte=poison)
            call, = result['calls']
            self.assertEqual(call['payload_length'], 6)
            self.assertEqual(call['tail_before'], poison)
            self.assertEqual(bytes.fromhex(call['payload_hex'])[-1], poison)
            tail_offset = call['payload_pointer'] + 5 - (q.SP - 0x1000)
            self.assertFalse(any(e['phase'] == 'action' and e['region'] == 'stack'
                                 and e['access'] == 'write'
                                 and e['offset'] <= tail_offset < e['offset'] + e['size']
                                 for e in n.events))

    def test_queue_append_preserves_canaries_and_existing_bytes(self):
        for count in (0, 3, 0xa00 - 7):
            n, _ = self.native()
            before = bytes(n.vm.mem_read(q.QUEUE + q.QUEUE_BYTES, 0xa08))
            result = self.action(n, queued_count=count)
            expected = bytearray(before)
            expected[count:count + 7] = bytes.fromhex('85341202009aa5')
            self.assertEqual(bytes(n.vm.mem_read(q.QUEUE + q.QUEUE_BYTES, 0xa08)), expected)
            self.assertEqual(result['queue_count_after'], count + 7)
            writes = [e for e in n.events if e['region'] == 'queue' and e['access'] == 'write']
            self.assertEqual([(e['rva'], e['size']) for e in writes],
                             [(0x13320, 1), (0x13338, 4), (0x13340, 1),
                              (0x13340, 1), (0x1334c, 4)])

    def test_queue_capacity_and_lock_are_explicit_unexecuted_boundaries(self):
        for count, lock, endpoint in ((0xa00 - 6, 0, 0x13370), (0xa00, 0, 0x13370),
                                      (0, 0x12345678, 0x11970)):
            n, _ = self.native(reply=0x8002)
            result = self.action(n, queued_count=count, lock_pointer=lock)
            self.assertEqual(result['stop_rva'], endpoint)
            self.assertEqual(len(result['calls']), 1)
            self.assertEqual(result['queue_count_after'], count)
            self.assertEqual(result['action_state'], 0x12345678)
            self.assertEqual(result['high_bit_flag'], 0)
            self.assertFalse(any(e['region'] == 'queue' and e['access'] == 'write'
                                 for e in n.events))

    def test_inbound_truncation_is_not_an_atomic_packet_validator(self):
        from unicorn import UcError, UC_ERR_READ_UNMAPPED
        p = q.fixture(request_word=0x1234, reply_word=2, context_byte=0x9a)
        for length in range(1, 12):
            n = q.NativeAction(self.raw)
            with self.subTest(length=length), self.assertRaises(UcError) as error:
                n.ingest(p[:length])
            self.assertEqual(error.exception.errno, UC_ERR_READ_UNMAPPED)
        for length in range(12, 28):
            n = q.NativeAction(self.raw)
            self.assertEqual(n.ingest(p[:length])['stop_rva'], 0xc8234)
        n = q.NativeAction(self.raw)
        with self.assertRaises(UcError):
            n.ingest(p[:11])
        self.assertEqual(n.read(q.UI + q.CONTEXT, '<B'), (0x9a,))

    def test_closed_widget_and_null_catalog_stop_without_request(self):
        p = q.fixture(request_word=1, reply_word=2, context_byte=3)
        n = q.NativeAction(self.raw)
        n.write(q.UI + 0x232dee, '<h', -1)
        self.assertEqual(n.ingest(p)['stop_rva'], 0x6b517)
        self.assertEqual(n.getreg('ESP'), q.SP)
        self.assertFalse(any(e['region'] == 'ui' and e['access'] == 'write' for e in n.events))
        n = q.NativeAction(self.raw)
        n.write(q.TABLE, '<I', 0)
        self.assertEqual(n.ingest(p)['stop_rva'], 0x2c70)
        self.assertEqual(n.calls, [])

    def test_real_input_event_reaches_request_producer(self):
        # Stage action state with a non-final page, then enter the real handler.
        n, _ = self.native()
        self.action(n, page=0, page_count=2)
        n.write(q.GLOBALS + 8, '<i', 1)
        n.write(q.SP, '<III', q.RETURN, 0, 1)
        n.setreg('ECX', q.UI)
        n.setreg('ESP', q.SP)
        self.assertEqual(n.run(0xc85b0, q.BASE + 0xc8350), q.BASE + 0xc8350)
        self.assertEqual(n.calls[0]['opcode'], 0x85)
        self.assertEqual(n.read(q.QUEUE + q.QUEUE_COUNT, '<I'), (7,))

    def test_input_event_flag_control_and_widget_boundaries(self):
        for control, flags, widget, stop in ((0, 0, 0, q.RETURN),
                                            (0, 1, -1, q.RETURN),
                                            (4, 1, 0, q.RETURN),
                                            (0xffff, 1, 0, q.RETURN),
                                            (0, 2, 0, q.BASE + 0xc8350),
                                            (1, 1, 0, q.BASE + 0xc8350),
                                            (2, 1, 0, q.BASE + 0xc8720),
                                            (3, 1, 0, q.BASE + 0xc8750)):
            n, _ = self.native()
            self.action(n, page=0, page_count=2)
            n.write(q.UI + 0x232dee, '<h', widget)
            n.write(q.SP, '<III', q.RETURN, control, flags)
            n.setreg('ECX', q.UI)
            n.setreg('ESP', q.SP)
            self.assertEqual(n.run(0xc85b0, stop), stop)
            self.assertEqual(n.calls, [])
            self.assertEqual(n.read(q.QUEUE + q.QUEUE_COUNT, '<I'), (0,))
            if stop == q.RETURN:
                self.assertEqual(n.getreg('ESP'), q.SP + 12)

    def test_instructions_and_resource_bytes_unchanged(self):
        n, _ = self.native()
        resource = bytes(n.vm.mem_read(q.RESOURCE, 0xe0000))
        self.action(n)
        self.assertEqual(bytes(n.vm.mem_read(q.RESOURCE, 0xe0000)), resource)
        for start, end in ((0, 0x1b5000), (0x1b6000, 0x1b7000),
                           (0x1b8000, len(self.raw))):
            self.assertEqual(bytes(n.vm.mem_read(q.BASE + start, end - start)), self.raw[start:end])

    def test_report_is_request_evidence_and_keeps_original_rules_open(self):
        report = q.build_report()
        self.assertEqual(report['action']['appended_hex'], '85341202009aa5')
        self.assertIn('untouched stack', report['boundary'])
        self.assertIn('server dispatch/validation', report['open'])
        self.assertIn('No live playable proof', report['open'])


if __name__ == '__main__':
    unittest.main()
