from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/strike_lab'))
from post6b_event_arbiter import Post6BEventArbiter


class ArbiterTests(unittest.TestCase):
    def setUp(self):
        self.persist = Mock()
        self.arbiter = Post6BEventArbiter({'sequence': 100, 'pid': 7, 'tid': 1}, self.persist)

    def event(self, seq, kind, tid=1, **extra):
        return dict(sequence=seq, pid=7, tid=tid, event_class=kind, qualified=True, **extra)

    def test_wait_before_other_thread_send(self):
        self.arbiter.consume(self.event(103, 'RX_WAIT'))
        result = self.arbiter.consume(self.event(104, 'CLIENT_TX', tid=2))
        self.assertEqual(result['direction'], 'SERVER_FIRST')
        self.persist.assert_called_once()

    def test_send_before_close(self):
        self.arbiter.consume(self.event(101, 'CLIENT_TX', tid=2))
        self.arbiter.consume(self.event(102, 'CONNECTION_TRANSITION'))
        self.assertEqual(self.arbiter.first['direction'], 'CLIENT_FIRST')

    def test_housekeeping_ignored(self):
        self.assertIsNone(self.arbiter.consume(self.event(101, 'QUEUE_HOUSEKEEPING')))
        self.assertEqual(self.arbiter.consume(self.event(102, 'RX_WAIT'))['direction'], 'SERVER_FIRST')

    def test_connect(self):
        self.assertEqual(self.arbiter.consume(self.event(101, 'CONNECTION_TRANSITION'))['direction'], 'CONNECTION_TRANSITION')

    def test_barrier(self):
        self.assertIsNone(self.arbiter.consume(self.event(100, 'CLIENT_TX')))
        self.assertIsNone(self.arbiter.first)

    def test_wrong_pid_and_reverse_order_rejected(self):
        wrong = self.event(101, 'CLIENT_TX'); wrong['pid'] = 8
        with self.assertRaises(ValueError): self.arbiter.consume(wrong)
        self.arbiter.consume(self.event(103, 'RX_WAIT'))
        with self.assertRaises(ValueError): self.arbiter.consume(self.event(102, 'CLIENT_TX'))

    def test_unqualified_relevant_event_blocks(self):
        event = self.event(101, 'RX_WAIT'); event['qualified'] = False
        with self.assertRaises(ValueError): self.arbiter.consume(event)
        self.persist.assert_not_called()

    def test_state_needs_evidence(self):
        with self.assertRaises(ValueError):
            self.arbiter.consume(self.event(101, 'LOCAL_PROTOCOL_TRANSITION'))

    def test_exit_is_not_direction(self):
        self.assertEqual(self.arbiter.consume(self.event(101, 'CLIENT_EXIT'))['direction'], 'UNKNOWN')

    def test_persistence_error_does_not_latch(self):
        self.persist.side_effect = OSError('disk error')
        with self.assertRaises(OSError): self.arbiter.consume(self.event(101, 'CLIENT_TX'))
        self.assertIsNone(self.arbiter.first)


if __name__ == '__main__': unittest.main()
