import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/strike_lab'))
from post_server_select_observer import PostServerSelectObserver


class PollTests(unittest.TestCase):
    def test_unmatched_six_byte_return_is_not_t0(self):
        observer = PostServerSelectObserver.__new__(PostServerSelectObserver)
        observer.boundary = None
        driver = Mock()
        self.assertFalse(observer.network_return(
            {'api': 'send', 'eax': 6, 'matched': False, 'entry': 146},
            {'a2': 6, 'sequence': 146, 'buffer_file': 'unused.bin'}, driver))
        self.assertIsNone(observer.boundary)
        driver.command.assert_not_called()

    def test_poll_does_not_end_observation_or_infer_direction(self):
        with tempfile.TemporaryDirectory() as directory:
            observer = PostServerSelectObserver.__new__(PostServerSelectObserver)
            observer.run = Path(directory)
            observer.boundary = {'sequence': 147}
            observer.post6b_events = Mock()
            observer.post6b_events.consume.return_value = None
            observer.capture = Mock()
            driver = Mock()
            for sequence in range(10):
                self.assertFalse(observer.network_return(
                    {'api': 'select', 'eax': 0, 'sequence': 148 + sequence},
                    {'a1': 1234}, driver))
            observer.capture.assert_not_called()
            driver.command.assert_not_called()
            samples = list(observer.run.glob('post-six-poll-*.json'))
            self.assertEqual(len(samples), 8)
            self.assertFalse((observer.run / 'post-six-next-event.json').exists())
            for sample in samples:
                self.assertEqual(json.loads(sample.read_text())['next_direction'], 'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
