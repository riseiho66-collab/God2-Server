"""Bounded current close/action evidence; no original server behavior inferred."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from tools.strike_lab import current_quest_close as c

q = c.q


class CurrentQuestCloseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = q.evidence()

    def native(self, *, request=0x1234, reply=2, context=0x9a, **state):
        n = c.NativeClose(self.raw)
        packet = q.fixture(request_word=request, reply_word=reply, context_byte=context)
        self.assertEqual(n.ingest(packet)['stop_rva'], 0xc8234)
        n.prepare(**state)
        return n

    def opcodes(self, result):
        return [call['opcode'] for call in result['calls']]

    def test_pin_inheritance_and_exact_native_branch_bytes(self):
        self.assertTrue(issubclass(c.NativeClose, q.NativeAction))
        with self.assertRaisesRegex(ValueError, 'requalification'):
            c.NativeClose(bytes([self.raw[0] ^ 1]) + self.raw[1:])
        anchors = {
            0xc8350: '51568bf1', 0xc8354: '6683beee2d230000',
            0xc8362: '8b8600ff0a00', 0xc836c: '8b8604ff0a00',
            0xc8376: '8b868c680800', 0xc8380: '6a04528b08',
            0xc838b: '6886000000', 0xc8390: '81e1ffff000033c1',
            0xc839e: '89442410', 0xc83a2: 'e839aff4ff',
            0xc83a7: 'c78600ff0a0000000000',
            0xc8431: '83f801', 0xc8447: 'e874f9fcff',
            0xc844c: 'c705ec7b5b0000000000',
            0xc858e: 'c78604ff0a0001000000',
            0x133f0: '8a81b82c0000', 0x13407: 'e964ffffff',
        }
        for rva, hex_bytes in anchors.items():
            self.assertEqual(self.raw[rva:rva + len(hex_bytes) // 2].hex(), hex_bytes)
        self.assertEqual(struct.unpack_from('<I', self.raw, 0x193e68), (0xffffffff,))

    def test_86_fields_opaque_source_high_bits_and_stack_poison(self):
        for source in (0, 0xffff, 0xdeadbeef, 0x1234beef, 0xffffffff):
            for poison in (0, 0x55, 0xa5, 0xff):
                n = self.native(source_dword=source, stack_byte=poison)
                r = n.execute()
                self.assertTrue(r['returned'])
                self.assertEqual(r['esp'], q.SP + 4)
                expected = b'\x86' + struct.pack('<I', (q.UI & 0xffff0000) | (source & 0xffff))
                self.assertEqual(r['appended_hex'], expected.hex())
                call, = r['calls']
                self.assertEqual((call['payload_length'], call['caller_rva']), (4, 0xc83a7))
                self.assertTrue(all(w['rva'] == 0xc839e for w in call['last_payload_writes']))
                saved = [w for w in n.stack_writes if w['rva'] == 0xc8350]
                self.assertEqual(saved[0]['value'], q.UI)
                self.assertIn(dict(phase='close', rva=0xc8383, access='read',
                                   region='backing', offset=0x800, size=4), n.events)

    def test_close_gates_and_high_flag_exact_equality(self):
        for active in (0, 1, 0xffffffff):
            for action in (0, 1, 0x12345678):
                for flag in (0, 1, 2, 0xffffffff):
                    n = self.native(active=active, action_state=action)
                    n.write(q.GLOBALS, '<I', flag)
                    r = n.execute()
                    expected = ([0x86] if active and not action else []) + ([0x85] if flag == 1 else [])
                    self.assertEqual(self.opcodes(r), expected, (active, action, flag))
                    self.assertTrue(r['returned'])
                    self.assertEqual(r['after']['active'], 0)
                    self.assertEqual(r['after']['action_state'], action)
                    self.assertEqual(r['after']['high_bit_flag'], 0 if flag == 1 else flag)

    def test_negative_widget_returns_before_any_close_state_change(self):
        for widget in (-32768, -1):
            n = self.native(reply=0x8002, widget=widget, choice=3)
            r = n.execute()
            self.assertTrue(r['returned'])
            self.assertEqual(r['before'], r['after'])
            self.assertEqual(r['calls'], [])
            self.assertNotIn(0xc8700, r['trace'])
        n = self.native(widget=1)
        self.assertTrue(n.execute()['returned'])

    def test_direct_close_full_cleanup_before_second_producer(self):
        n = self.native(reply=0x8002, choice=7)
        r = n.execute()
        self.assertEqual(r['appended_hex'], '86efbe001085341202009a84')
        self.assertEqual(self.opcodes(r), [0x86, 0x85])
        self.assertEqual([x['caller_rva'] for x in r['calls']], [0xc83a7, 0x97df8])
        milestones = (0xc83a2, 0xc83a7, 0xc8700, 0xc7ed0, 0x107bb0,
                      0xc840a, 0xc841b, 0x834e0, 0xc8431, 0xc8447, 0xc844c)
        positions = [r['trace'].index(x) for x in milestones]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(r['trace'].count(0x10cc60), 5)
        self.assertEqual(r['trace'].count(0x146cf7), 5)
        self.assertEqual(r['trace'].count(0x1e500), 5)
        self.assertEqual(r['trace'].count(0x1e440), 5)
        self.assertIn(0x10dbe0, r['trace'])
        self.assertIn(0x1a950, r['trace'])
        self.assertEqual(r['after'], dict(active=0, action_state=0, high_bit_flag=0,
                                          choice=-1, queue_count=12))

    def test_close_85_tail_is_native_call_return_residue(self):
        for poison in (0, 0x55, 0xa5, 0xff):
            n = self.native(reply=0x8002, stack_byte=poison)
            call = n.execute()['calls'][1]
            self.assertEqual(call['payload_hex'], '341202009a84')
            self.assertEqual(call['tail_before'], 0x84)
            writer = call['last_payload_writes'][5]
            self.assertEqual((writer['rva'], writer['size'], writer['value']),
                             (0xc8426, 4, q.BASE + 0xc842b))
            self.assertEqual(call['payload_pointer'] + 5, writer['address'] + 1)
            self.assertEqual([w['rva'] for w in call['last_payload_writes'][:5]],
                             [0x97dd6, 0x97dd6, 0x97dcd, 0x97dcd, 0x97def])

    def test_complete_non_mode4_action_suppresses_86_and_clears_flag(self):
        for mode in (0, 1, 2, 3, 5, 0xffff):
            n = self.native(reply=0x8002, mode=mode)
            r = n.execute('action')
            self.assertTrue(r['returned'])
            self.assertEqual(r['appended_hex'], '85341202009aa5')
            self.assertEqual(self.opcodes(r), [0x85])
            self.assertIsNone(r['calls'][0]['last_payload_writes'][5])
            self.assertEqual(r['after']['action_state'], 1)
            self.assertEqual(r['after']['high_bit_flag'], 0)
            self.assertEqual(r['after']['active'], 0)
            self.assertIn(0xc8350, r['trace'])
            self.assertNotIn(0xc838b, r['trace'])

    def test_exact_parent_action_continuation_uses_live_stack(self):
        n = self.native(reply=0x8002)
        r = n.action(page=0, page_count=1, mode=1, threshold=0, choice=-1,
                     stack_byte=0xa5, queued_count=0, lock_pointer=0)
        self.assertEqual(r['stop_rva'], 0xc8350)
        stack = bytes(n.vm.mem_read(n.getreg('ESP'), 12))
        self.assertEqual(struct.unpack_from('<I', stack)[0], q.BASE + 0xc859f)
        continued = n.resume_close()
        self.assertTrue(continued['returned'])
        self.assertEqual(continued['esp'], q.SP + 4)
        self.assertEqual(continued['calls'], [])
        self.assertEqual(continued['after']['queue_count'], 7)
        self.assertEqual(bytes(n.vm.mem_read(q.QUEUE + q.QUEUE_BYTES, 7)).hex(), '85341202009aa5')
        with self.assertRaisesRegex(ValueError, 'exact NativeAction'):
            n.resume_close()

    def test_mode4_all_choices_and_flag_produce_85_then_85(self):
        for flag_reply in (2, 0x8002):
            for choice in range(8):
                n = self.native(reply=flag_reply, mode=4, choice=choice)
                r = n.execute('action')
                expected = (b'\x85' + struct.pack('<HHBB', 0x1234, choice, 0x9a, 0xa5)).hex()
                if flag_reply & 0x8000:
                    expected += '85341202009a84'
                self.assertTrue(r['returned'])
                self.assertEqual(r['appended_hex'], expected)
                self.assertNotIn(0x86, self.opcodes(r))
                self.assertEqual(r['after']['choice'], -1)
                self.assertEqual(r['after']['high_bit_flag'], 0)

    def test_opaque_words_context_and_ffff_do_not_imply_quest_ids(self):
        for request, reply, context in ((0, 0x8000, 0), (65535, 0xfffe, 255),
                                         (42, 0x9234, 1), (0x1234, 0xffff, 0x9a)):
            n = self.native(request=request, reply=reply, context=context)
            r = n.execute()
            expected = '86efbe0010'
            if reply != 0xffff:
                expected += (b'\x85' + struct.pack('<HHBB', request, reply & 0x7fff, context, 0x84)).hex()
            self.assertEqual(r['appended_hex'], expected)
        n = self.native(reply=0xffff)
        r = n.execute('action')
        self.assertEqual(r['appended_hex'], '86efbe0010')
        self.assertEqual(r['after']['action_state'], 0)

    def test_page_threshold_and_invalid_choice_boundaries(self):
        for state in (dict(page=0, page_count=2),
                      dict(page=-1, page_count=2, mode=4, threshold=0, choice=0)):
            n = self.native(reply=0x8002, **state)
            r = n.execute('action')
            self.assertTrue(r['returned'])
            self.assertEqual(r['calls'], [])
            self.assertEqual(r['before'], r['after'])
        for choice in (-32768, -1, 8, 32767):
            n = self.native(reply=0x8002, mode=4, choice=choice)
            r = n.execute('action')
            self.assertEqual(r['stop_rva'], 0x75d60)
            self.assertEqual(r['calls'], [])
            self.assertEqual(r['before'], r['after'])
        n = self.native(mode=4, page=2, page_count=9, threshold=2, choice=3)
        self.assertTrue(n.execute('action')['returned'])

    def test_queue_canaries_existing_bytes_and_exact_capacity(self):
        for entry, reply, mode, choice, length in (('close', 2, 1, -1, 5),
                                                   ('close', 0x8002, 1, -1, 12),
                                                   ('action', 0x8002, 1, -1, 7),
                                                   ('action', 0x8002, 4, 3, 14)):
            for count in (0, 3, 0xa00 - length):
                n = self.native(reply=reply, mode=mode, choice=choice, queued_count=count)
                before = bytes(n.vm.mem_read(q.QUEUE + q.QUEUE_BYTES, 0xa08))
                r = n.execute(entry)
                self.assertTrue(r['returned'])
                self.assertEqual(r['after']['queue_count'], count + length)
                expected = bytearray(before)
                expected[count:count + length] = bytes.fromhex(r['appended_hex'])
                self.assertEqual(bytes(n.vm.mem_read(q.QUEUE + q.QUEUE_BYTES, 0xa08)), expected)
        n = self.native()
        n.execute()
        writes = [(e['rva'], e['size']) for e in n.events
                  if e['region'] == 'queue' and e['access'] == 'write']
        self.assertEqual(writes, [(0x13320, 1), (0x13338, 4), (0x1334c, 4)])

    def test_first_request_capacity_and_lock_stops_are_not_successes(self):
        for entry, count, lock, stop in (('close', 0xa00 - 4, 0, 0x13370),
                                         ('close', 0xa00, 0, 0x13370),
                                         ('close', 0, 0x12345678, 0x11970),
                                         ('action', 0xa00 - 6, 0, 0x13370),
                                         ('action', 0, 0x12345678, 0x11970)):
            n = self.native(reply=0x8002, queued_count=count, lock_pointer=lock)
            r = n.execute(entry)
            self.assertFalse(r['returned'])
            self.assertEqual(r['stop_rva'], stop)
            self.assertEqual(len(r['calls']), 1)
            self.assertEqual(r['appended_hex'], '')
            self.assertEqual(r['after']['queue_count'], count)
            self.assertEqual(r['after']['active'], 1)
            self.assertEqual(r['after']['action_state'], 0)
            self.assertEqual(r['after']['high_bit_flag'], 0 if entry == 'action' else 1)
            self.assertFalse(any(e['region'] == 'queue' and e['access'] == 'write' for e in n.events))

    def test_second_request_flush_boundary_preserves_first_and_pending_flag(self):
        for entry, mode, choice, count, first in (
                ('close', 1, -1, 0xa00 - 11, '86efbe0010'),
                ('action', 4, 3, 0xa00 - 13, '85341203009aa5')):
            n = self.native(reply=0x8002, mode=mode, choice=choice, queued_count=count)
            before = bytes(n.vm.mem_read(q.QUEUE + q.QUEUE_BYTES, 0xa08))
            r = n.execute(entry)
            self.assertEqual(r['stop_rva'], 0x13370)
            self.assertEqual(len(r['calls']), 2)
            self.assertEqual(r['appended_hex'], first)
            self.assertEqual(r['after']['high_bit_flag'], 1)
            self.assertEqual(r['after']['active'], 0)
            self.assertEqual(r['after']['action_state'], int(entry == 'action'))
            expected = bytearray(before)
            expected[count:count + len(bytes.fromhex(first))] = bytes.fromhex(first)
            self.assertEqual(bytes(n.vm.mem_read(q.QUEUE + q.QUEUE_BYTES, 0xa08)), expected)
            self.assertEqual(n.read(n.getreg('ESP'), '<I'), (q.BASE + 0x13303,))

    def test_explicit_flush_gate_needs_no_86_after_action(self):
        for entry, reply in (('action', 0x8002), ('close', 2), ('close', 0x8002)):
            n = self.native(reply=reply)
            r = n.execute(entry)
            before = bytes(n.vm.mem_read(q.QUEUE + q.QUEUE_BYTES, 32))
            flushed = n.execute('flush')
            self.assertEqual(flushed['stop_rva'], 0x13370)
            self.assertEqual(flushed['before'], flushed['after'])
            self.assertEqual(flushed['calls'], [])
            self.assertEqual(bytes(n.vm.mem_read(q.QUEUE + q.QUEUE_BYTES, 32)), before)
            if entry == 'action':
                self.assertEqual(self.opcodes(r), [0x85])
        n = self.native()
        self.assertTrue(n.execute('flush')['returned'])
        n.execute()
        n.write(q.QUEUE + 0x2cb8, '<B', 0)
        self.assertTrue(n.execute('flush')['returned'])
        self.assertEqual(n.state()['queue_count'], 5)

    def test_repeated_close_preserves_queue_without_repeating_cleared_gates(self):
        n = self.native(reply=0x8002)
        first = n.execute()
        second = n.execute()
        self.assertTrue(second['returned'])
        self.assertEqual(second['calls'], [])
        self.assertEqual(second['after'], first['after'])
        self.assertEqual(n.read(q.UI + c.WIDGET, '<h'), (0,))

    def test_actual_input_event_actions_close_priority_and_boundaries(self):
        for control, flags, reply, expected in ((0, 1, 0x8002, [0x85]),
                                                (1, 1, 0x8002, [0x86, 0x85]),
                                                (0, 2, 2, [0x86]),
                                                (0, 3, 0x8002, [0x86, 0x85]),
                                                (0xffff, 2, 2, [0x86]),
                                                (0, 0, 2, []), (4, 1, 2, [])):
            n = self.native(reply=reply)
            r = n.execute('event', control=control, flags=flags)
            self.assertTrue(r['returned'])
            self.assertEqual(self.opcodes(r), expected)
            self.assertEqual(r['esp'], q.SP + 12)
        for control, stop in ((2, 0xc8720), (3, 0xc8750)):
            n = self.native()
            self.assertEqual(n.execute('event', control=control)['stop_rva'], stop)
        n = self.native(reply=0x8002, mode=4, choice=3)
        r = n.execute('event')
        self.assertEqual(self.opcodes(r), [0x85, 0x85])
        self.assertEqual(r['stop_rva'], 0x10d8a0)
        self.assertFalse(r['returned'])

    def test_populated_ui_stops_without_replacement_callee_success(self):
        probes = ((q.UI + c.LIST + 0x144, '<I', 1, 0x10d362),
                  (q.UI + c.LIST + 0xc, '<B', 1, 0x10dbf0),
                  (q.UI + 0xe2988, '<H', 2, 0x107bed),
                  (q.UI + 0x232ec8, '<I', 0, 0x1a961),
                  (c.BACKING + 0x1e, '<H', 0, 0x26700),
                  (q.UI + c.LIST + 8, '<H', 0x1000, 0x2c70))
        for address, fmt, value, stop in probes:
            n = self.native(reply=0x8002)
            n.write(address, fmt, value)
            r = n.execute()
            self.assertEqual(r['stop_rva'], stop)
            self.assertFalse(r['returned'])
            self.assertEqual(r['appended_hex'], '86efbe0010')
            self.assertEqual(r['after']['high_bit_flag'], 1)
            self.assertEqual(r['after']['active'], 0)

    def test_native_code_resource_input_and_source_unchanged(self):
        n = self.native(reply=0x8002)
        regions = ((q.RESOURCE, 0xe0000), (q.TABLE, 4096), (q.PACKET, 4096),
                   (c.BACKING, 4096))
        before = [bytes(n.vm.mem_read(a, size)) for a, size in regions]
        self.assertTrue(n.execute()['returned'])
        for (address, size), expected in zip(regions, before):
            self.assertEqual(bytes(n.vm.mem_read(address, size)), expected)
        for start, end in ((0, 0x1b5000), (0x1b6000, 0x1b7000), (0x1b8000, len(self.raw))):
            self.assertEqual(bytes(n.vm.mem_read(q.BASE + start, end - start)), self.raw[start:end])
        self.assertFalse(any(e['region'] == 'backing' and e['access'] == 'write' for e in n.events))

    def test_report_and_width_rejections_keep_rules_open(self):
        report = c.build_report()
        self.assertFalse(report['requires_85_then_86'])
        self.assertEqual(report['image_sha256'], q.IMAGE_SHA)
        self.assertIn('server dispatch/validation', report['open'])
        self.assertIn('No inferred server acceptance', report['open'])
        for bad in (dict(active=-1), dict(action_state=2**32), dict(source_dword=-1),
                    dict(widget=32768), dict(queued_count=0xa01), dict(stack_byte=256)):
            with self.assertRaises(ValueError):
                self.native(**bad)
        n = self.native()
        with self.assertRaises(ValueError):
            n.execute('unknown')


if __name__ == '__main__':
    unittest.main()
