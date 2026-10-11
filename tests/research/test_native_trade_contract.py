"""Current machine versus compiled C++ codec; not actual UI/network acceptance."""
import os
from pathlib import Path
import subprocess
import unittest
from tools.strike_lab.current_trade_20261002 import prove


class NativeTradeContract(unittest.TestCase):
    def test_pinned_native_and_cpp_producers(self):
        proof = prove()
        self.assertEqual(proof['passed'], 61)
        self.assertEqual(proof['S2C_logical_widths'],
                         {'27': 5, '4E': 19, '4F': 3, '50': 25,
                          '51': 9, '52': 3, '53': 3, '8A': 45})
        binary = Path(os.environ.get('GOD2_TRADE_CODEC_BINARY',
                      'build-town-visibility/tests/Release/recovered-trade.exe'))
        self.assertTrue(binary.is_file(), 'Build recovered-trade first')
        result = subprocess.run([str(binary.resolve()), 'producer-fixtures'],
                                capture_output=True, text=True, check=True, timeout=10)
        self.assertEqual(result.stdout.splitlines(), proof['five_producer_fixture_records'])
        self.assertEqual(proof['classification']['69_8A'], 'PK challenge, ProgramMsg733')


if __name__ == '__main__':
    unittest.main()
