"""Run the real repository in abruptly exiting child processes, not mocks."""
import pathlib
import subprocess
import sys
import tempfile
import unittest

EXE = pathlib.Path(__file__).resolve().parents[2] / 'build/tests/Release/battle-process-crash.exe'


class BattleProcessCrash(unittest.TestCase):
    def test_settlement_crash_boundaries(self):
        self.assertIsNotNone(EXE)
        points = {
            'character_resources': 73,
            'battle_checkpoints': 73,
            'character_experience': 73,
            'battle_settlements': 73,
            'commit': 74,
            'after_commit': 75,
        }
        for point, exit_code in points.items():
            with self.subTest(point=point), tempfile.TemporaryDirectory(prefix='god2-crash-') as folder:
                db = pathlib.Path(folder) / 'test.sqlite'
                def run(action, fault=point):
                    return subprocess.run([str(EXE), str(db), action, fault],
                                          capture_output=True, text=True, timeout=20)
                result = run('init')
                self.assertEqual(result.returncode, 0, result.stderr)
                result = run('crash')
                self.assertEqual(result.returncode, exit_code, result.stderr)
                result = run('verify')
                self.assertEqual(result.returncode, 0, result.stderr)
                # A second fresh process must see the same single committed reward.
                result = run('verify', 'after_commit')
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        EXE = pathlib.Path(sys.argv.pop(1)).resolve()
    unittest.main()
