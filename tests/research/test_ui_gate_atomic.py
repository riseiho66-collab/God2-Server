import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/strike_lab'))
from ui_gate import atomic_json


class AtomicJsonTests(unittest.TestCase):
    def test_transient_sharing_collision(self):
        original = Path.replace
        error = PermissionError('sharing collision')
        error.winerror = 32
        calls = []

        def replace(source, target):
            calls.append(target)
            if len(calls) < 3:
                raise error
            return original(source, target)

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'hold.json'
            with patch.object(Path, 'replace', replace), patch('ui_gate.time.sleep'):
                atomic_json(target, {'hold': True})
            self.assertEqual(json.loads(target.read_text()), {'hold': True})
            self.assertEqual(len(calls), 3)
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_permanent_denial_preserves_previous_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'hold.json'
            atomic_json(target, {'hold': False})
            error = PermissionError('access denied')
            error.winerror = 5
            with patch.object(Path, 'replace', side_effect=error) as replace, patch('ui_gate.time.sleep'):
                with self.assertRaises(PermissionError):
                    atomic_json(target, {'hold': True})
            self.assertEqual(replace.call_count, 10)
            self.assertEqual(json.loads(target.read_text()), {'hold': False})
            self.assertEqual(list(Path(directory).iterdir()), [target])


if __name__ == '__main__':
    unittest.main()
