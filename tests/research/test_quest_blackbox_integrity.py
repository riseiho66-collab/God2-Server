"""Shared-state native quest regressions; synthetic inputs, no gameplay claims.

Reuse NativeClose and the established DB dispatcher setup in one VM. No
compiler, client process, sockets, database, or replacement native callees.
"""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
from tools.strike_lab import current_quest_close as close
from tools.strike_lab import quest_player_scenarios as journal
from unicorn import UcError, UC_ERR_READ_UNMAPPED, UC_PROT_READ

q = close.q
SLOTS, PAGE, SUPPRESSION, SELECTED = 0xc2104, 0xc2144, 0x232eb0, 0x232eb8


class QuestBlackboxIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for target in ('subprocess.Popen', 'socket.socket', 'sqlite3.connect'):
            guard = patch(target, side_effect=AssertionError('Offline native test only'))
            guard.start()
            cls.addClassCleanup(guard.stop)
        cls.evidence = journal.Evidence()
        q.qualify(cls.evidence.image)

    def native(self, **state):
        n = close.NativeClose(self.evidence.image)
        incoming = n.ingest(q.fixture(request_word=0x1234, reply_word=0x8002,
                                     context_byte=0x9a))
        self.assertEqual(incoming['stop_rva'], 0xc8234)
        n.prepare(**state)
        # Same closed journal fixture as CurrentQuestSyncTests. The nonnull
        # table pointer is only used for page arithmetic; no row is read.
        outer = q.UI - 0xa7f2f6c
        n.vm.mem_map((outer + 0x1539ad80) & ~4095, 4096)
        n.write(q.RESOURCE + 0xd2ac0, '<II', len(self.evidence.missions),
                q.RESOURCE + 0x1000)
        n.vm.mem_write(q.UI + 0xc2100, b'\xa5' * 0x50)
        n.vm.mem_write(q.UI + SLOTS, bytes(60))
        n.write(q.UI + PAGE, '<hh', 0, 1)
        n.write(q.UI + 0x232e5a, '<h', -1)
        n.write(q.UI + SUPPRESSION, '<I', 1)
        n.write(q.UI + SELECTED, '<I', 0)
        return n

    def dispatch(self, n, record):
        # CurrentQuestSyncTests.dispatch register contract, relocated to the
        # existing NativeClose VM. Logical input ends at an unmapped page.
        address = q.PACKET + 4096 - len(record)
        n.vm.mem_write(address, record)
        n.vm.mem_protect(q.PACKET, 4096, UC_PROT_READ)
        n.setreg('EBP', q.UI - 0xa7f2f6c)
        n.setreg('EBX', address)
        n.setreg('EAX', record[0])
        n.setreg('ESP', q.SP)
        n.phase = 'journal-sync'
        self.assertEqual(n.run(0x68b61, q.BASE + 0x6b517), q.BASE + 0x6b517)
        self.assertEqual(n.getreg('ESP'), q.SP)
        self.assertEqual(bytes(n.vm.mem_read(address, len(record))), record)

    def journal_state(self, n):
        for offset in (0xc2100, 0xc2140, 0xc2148):
            self.assertEqual(bytes(n.vm.mem_read(q.UI + offset, 4)), b'\xa5' * 4)
        return (n.read(q.UI + SLOTS, '<15I'), n.read(q.UI + PAGE, '<hh'),
                n.read(q.UI + SUPPRESSION, '<I'), n.read(q.UI + SELECTED, '<I'))

    def snapshot(self, n):
        return {name: bytes(n.vm.mem_read(address, size)) for name, address, size in (
            ('ui', q.UI, 0x240000), ('globals', q.GLOBALS, 16),
            ('queue', q.QUEUE, 0x5000), ('backing', close.BACKING, 4096),
            ('resource', q.RESOURCE, 0xe0000), ('table', q.TABLE, 4096))}

    def assert_snapshot(self, n, before):
        after = self.snapshot(n)
        for region, expected in before.items():
            self.assertTrue(after[region] == expected, region + ' changed')

    def test_close_and_sync_keep_distinct_identities_and_preserve_other_state(self):
        for subtype in (4, 5):
            with self.subTest(subtype=subtype):
                n = self.native(queued_count=3)
                n.vm.mem_write(q.QUEUE + q.QUEUE_BYTES, b'\x31\x72\xb4')
                for slot, packed in ((0, 0x10001), (14, 0x801a2)):
                    self.dispatch(n, journal.packet(slot, subtype, packed))
                before = self.journal_state(n)
                self.assertEqual(before, ((0x10001,) + (0,) * 13 + (0x801a2,),
                                         (0, 3), (int(subtype == 5),),
                                         (0x801a2 if subtype == 5 else 0,)))
                queued = bytes(n.vm.mem_read(q.QUEUE + q.QUEUE_BYTES, 0xa08))
                result = n.execute('close')
                self.assertTrue(result['returned'])
                self.assertEqual(result['esp'], q.SP + 4)
                # Existing NativeClose evidence: source low word + this high
                # word for 86; stored dialogue words/context for 85.
                emitted = bytes.fromhex('86efbe001085341202009a84')
                self.assertEqual(result['appended_hex'], emitted.hex())
                self.assertEqual([call['opcode'] for call in result['calls']], [0x86, 0x85])
                self.assertEqual(result['after'], dict(active=0, action_state=0,
                    high_bit_flag=0, choice=-1, queue_count=15))
                self.assertEqual(self.journal_state(n), before)
                expected = bytearray(queued)
                expected[3:15] = emitted
                self.assertEqual(bytes(n.vm.mem_read(q.QUEUE + q.QUEUE_BYTES, 0xa08)), expected)

                state, globals_before = n.state(), bytes(n.vm.mem_read(q.GLOBALS, 16))
                queue_before = bytes(n.vm.mem_read(q.QUEUE, 0x5000))
                self.dispatch(n, journal.packet(14, subtype, 0x10001))
                self.assertEqual(n.state(), state)
                self.assertEqual(bytes(n.vm.mem_read(q.GLOBALS, 16)), globals_before)
                self.assertEqual(bytes(n.vm.mem_read(q.QUEUE, 0x5000)), queue_before)
                self.assertEqual(self.journal_state(n),
                    ((0x10001,) + (0,) * 13 + (0x10001,), (0, 3),
                     (int(subtype == 5),), (0x10001 if subtype == 5 else 0,)))
                after_sync = self.snapshot(n)
                replay = n.execute('close')
                self.assertTrue(replay['returned'])
                self.assertEqual(replay['calls'], [])
                self.assert_snapshot(n, after_sync)

    def test_invalid_action_choice_has_no_partial_non_stack_mutation(self):
        for choice in (-1, 8):
            with self.subTest(choice=choice):
                n = self.native(mode=4, choice=choice, queued_count=3)
                self.dispatch(n, journal.packet(14, 5, 0x801a2))
                before = self.snapshot(n)
                event_start = len(n.events)
                result = n.execute('action')
                self.assertFalse(result['returned'])
                self.assertEqual(result['stop_rva'], 0x75d60)
                self.assertEqual(result['calls'], [])
                self.assertEqual(result['appended_hex'], '')
                self.assertEqual(result['before'], result['after'])
                self.assert_snapshot(n, before)
                self.assertFalse(any(e['access'] == 'write' and e['region'] != 'stack'
                                     for e in n.events[event_start:]))

    def test_truncated_sync_preserves_populated_dialogue_journal_and_queue(self):
        for subtype in (4, 5):
            for length in (9, 12):
                with self.subTest(subtype=subtype, length=length):
                    n = self.native(queued_count=3)
                    self.dispatch(n, journal.packet(14, 5, 0x801a2))
                    before = self.snapshot(n)
                    event_start = len(n.events)
                    record = journal.packet(0, subtype, 0x10001)[:length]
                    with self.assertRaises(UcError) as error:
                        self.dispatch(n, record)
                    self.assertEqual(error.exception.errno, UC_ERR_READ_UNMAPPED)
                    self.assertEqual(n.getreg('EIP') - q.BASE,
                                     0x8565b if subtype == 4 else 0x85693)
                    self.assert_snapshot(n, before)
                    self.assertFalse(any(e['access'] == 'write' and e['region'] != 'stack'
                                         for e in n.events[event_start:]))
                    address = q.PACKET + 4096 - length
                    self.assertEqual(bytes(n.vm.mem_read(address, length)), record)


if __name__ == '__main__':
    unittest.main()
