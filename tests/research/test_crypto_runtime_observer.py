import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/strike_lab'))
from crypto_runtime_observer import CryptoRuntimeObserver


class Driver:
    def __init__(self, report=None):
        self.commands = []
        self.report = report or {}

    def command(self, text):
        self.commands.append(text)
        return 'GOD2_PACKET ' + json.dumps(self.report) if text.startswith('!God2Probe.packet') else ''


class RuntimeObserverTests(unittest.TestCase):
    def test_breakpoint_scope(self):
        observer = CryptoRuntimeObserver('.')
        driver = Driver()
        observer.arm(driver)
        self.assertEqual(driver.commands, ['bp260 410a30', 'bp261 410a3e', 'bp262 410690'])

    def test_matching_checksum_return_is_not_parser_acceptance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            private = root / 'crypto-private'
            private.mkdir()
            base = private / 'packet-0001'
            wire_path = Path(str(base) + '.wire.bin')
            plain_path = Path(str(base) + '.plain.bin')
            wire_path.write_bytes(bytes.fromhex('0600a3a3fdd5'))
            plain = bytes.fromhex('0600a60000d8')
            plain_path.write_bytes(plain)
            Path(str(base) + '.client-plain.bin').write_bytes(plain)
            driver = Driver({'decoded': True, 'pid': 7, 'tid': 8, 'wire_address': 0x1000,
                             'wire_len': 6, 'plain_len': 6, 'wire_file': str(wire_path),
                             'plain_file': str(plain_path)})
            observer = CryptoRuntimeObserver(root)
            entry = {'pid': 7, 'tid': 8, 'sp': 0x2000, 'sequence': 1}
            observer.handle(260, entry, driver)
            returned = {'pid': 7, 'tid': 8, 'sp': 0x2008, 'sequence': 2, 'eax': 1}
            observer.handle(261, returned, driver)
            self.assertTrue(returned['matched'])
            report = json.loads(Path(str(base) + '.json').read_text())
            self.assertTrue(report['client_checksum_pass'])
            self.assertTrue(report['client_plaintext_match'])
            self.assertFalse(report['client_parser_runtime_validated'])
            self.assertFalse(report['CRYPTO_RECOVERED'])

    def test_unmatched_thread_is_not_consumed(self):
        with tempfile.TemporaryDirectory() as temp:
            observer = CryptoRuntimeObserver(temp)
            observer.pending[(1, 2)] = ({'sp': 10}, {})
            event = {'pid': 1, 'tid': 3, 'sp': 18, 'sequence': 2, 'eax': 1}
            observer.handle(261, event, Driver())
            self.assertFalse(event['matched'])
            self.assertIn((1, 2), observer.pending)


if __name__ == '__main__':
    unittest.main()
