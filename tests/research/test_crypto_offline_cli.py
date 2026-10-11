import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/strike_lab'))
from crypto_fixture_regression import historical_request


class OfflineCliTests(unittest.TestCase):
    def test_actual_dll_session_recovery_through_runner(self):
        request, _ = historical_request()
        for seq, packet in enumerate(request['packets'], 1):
            packet['seq'] = seq
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            manifest = base / 'private-request.json'
            manifest.write_text(json.dumps(request), encoding='utf-8')
            output = base / 'output'
            result = subprocess.run([sys.executable, str(ROOT / 'tools/strike_lab/apex.py'),
                'god2-strike-runner', '--recover-crypto', '--crypto-manifest', str(manifest),
                '--crypto-output', str(output)], cwd=ROOT, capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            report = json.loads((output / 'decrypt-candidates.json').read_text())
            self.assertEqual(report['status'], 'UNIQUE_CANDIDATE')
            self.assertEqual({d: r['candidate_count'] for d, r in report['directions'].items()},
                             {'C2S': 1, 'S2C': 1})
            self.assertEqual([r['survivors'] for r in report['directions']['S2C']['rounds']], [15, 1, 1, 1])
            self.assertFalse(report['CRYPTO_RECOVERED'])
            self.assertEqual(json.loads((output / 'runtime-qualification.json').read_text())['status'],
                             'RUNTIME_VALIDATION_REQUIRED')
            for path in output.glob('*.json'):
                text = path.read_text()
                self.assertNotIn(request['tx_key_hex'], text)
                self.assertNotIn(request['packets'][1]['known_plaintext_hex'], text)


if __name__ == '__main__':
    unittest.main()
