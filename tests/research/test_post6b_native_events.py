from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/strike_lab'))
from post6b_native_events import NativePost6BEvents, normalize
from post_server_select_observer import PostServerSelectObserver


def event(sequence, **extra):
    return dict(sequence=sequence, global_sequence=sequence, pid=7, tid=2,
                native_timestamp=sequence, timestamp=float(sequence), **extra)


class NativeEventTests(unittest.TestCase):
    def test_select_poll_and_recv_do_not_imply_wait(self):
        for api in ('select', 'recv'):
            self.assertEqual(normalize(event(11, event_type='API_ENTRY', api=api))['event_class'],
                             'UNCLASSIFIED')
        poll = event(12, event_type='API_ENTRY', api='select', a2=0, a3=0, select_wait_evidence={
            'source': 'NATIVE_SELECT_ARGUMENTS', 'read_count': 1,
            'seconds': 0, 'microseconds': 0, 'infinite': False})
        self.assertFalse(normalize(poll)['qualified'])
        poll['select_wait_evidence']['infinite'] = True
        poll['a2'] = 1234
        self.assertFalse(normalize(poll)['qualified'])

    def test_real_select_argument_hook_persists_before_capture(self):
        observer = PostServerSelectObserver.__new__(PostServerSelectObserver)
        observer.boundary = event(10)
        calls = []
        observer.post6b_events = NativePost6BEvents(observer.boundary,
            lambda result: calls.append(result), 'test')
        observer.capture = lambda *args: self.assertEqual(len(calls), 1)
        driver = Mock()
        driver.command.return_value = 'POST6B_SELECT count=1 timeout=0'
        self.assertTrue(observer.network_entry(event(11, event_type='API_ENTRY',
            api='select', a1=0x1000, a2=0, a3=0), driver))
        self.assertEqual(calls[0]['observed_candidate_direction'], 'SERVER_FIRST')
        self.assertEqual(calls[0]['next_direction'], 'UNKNOWN')
        self.assertFalse(calls[0]['capture_complete'])

    def test_send_bytes_exist_at_persistence_and_cross_thread_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            observer = PostServerSelectObserver.__new__(PostServerSelectObserver)
            observer.run = Path(directory)
            observer.boundary = dict(event(10), tid=1)
            (observer.run/'attempt.bin').write_bytes(b'abc')
            results = []
            def persist(result):
                self.assertEqual((observer.run/'C2S_AFTER_6B_NEXT.bin').read_bytes(), b'ab')
                results.append(result)
            observer.post6b_events = NativePost6BEvents(observer.boundary, persist, 'test')
            observer.capture = Mock()
            pending = event(11, event_type='API_ENTRY', api='send', a2=3, buffer_file='attempt.bin')
            returned = event(12, event_type='API_RETURN', api='send', eax=2, matched=True, entry=11)
            self.assertTrue(observer.network_return(returned, pending, Mock()))
            self.assertEqual(results[0]['observed_candidate_direction'], 'CLIENT_FIRST')
            self.assertEqual(results[0]['next_direction'], 'UNKNOWN')

    def test_identity_pair_and_uncertified_state_rejected(self):
        adapter = NativePost6BEvents(event(10), Mock(), 'test')
        with self.assertRaisesRegex(ValueError, 'PROCESS_TRANSITION'):
            adapter.consume(dict(event(11), pid=8))
        with self.assertRaisesRegex(ValueError, 'global sequence'):
            adapter.consume(dict(event(11), global_sequence=None))
        with self.assertRaisesRegex(ValueError, 'pair'):
            adapter.consume(event(11, event_type='API_RETURN', api='send', eax=1))
        with self.assertRaisesRegex(ValueError, 'certified'):
            adapter.consume(event(11, event_class='LOCAL_PROTOCOL_TRANSITION'))


if __name__ == '__main__':
    unittest.main()
