import unittest
import hashlib
import pefile
from tools.strike_lab import current_projection_gate as gate
from tools.strike_lab import current_unpacked_protocol_match as match


class ProjectionGateTests(unittest.TestCase):
    def test_original_import_and_gate_match_unpacked_client(self):
        raw = match.REFERENCE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), match.REFERENCE_SHA)
        self.assertEqual(hashlib.sha256(match.EXE.read_bytes()).hexdigest(), match.EXE_SHA)
        with pefile.PE(str(match.EXE)) as pe:
            self.assertEqual(pe.get_data(0x119e3e, 0x30), raw[0x119e3e:0x119e6e])
            self.assertEqual(raw[0x119e3e:0x119e44], bytes.fromhex('ff15bc075700'))
            imports = [(entry.dll.lower(), symbol.name) for entry in pe.DIRECTORY_ENTRY_IMPORT
                       for symbol in entry.imports if symbol.address == 0x5707bc]
            self.assertEqual(imports, [(b'winmm.dll', b'timeGetTime')])

    def test_count_and_unsigned_elapsed_boundaries(self):
        for count in (0, 1, 0xffffffff):
            for previous in (0, 1234, 0xfffffff0):
                for elapsed in (0, 1, 1999, 2000, 2001, 0xffffffff):
                    now = (previous + elapsed) & 0xffffffff
                    result = gate.evaluate(count, previous, now)
                    expected = bool(count) and elapsed >= 2000
                    self.assertEqual(result['admitted'], expected)
                    self.assertEqual(result['count_after'], count)
                    self.assertEqual(result['time_after'], now if expected else previous)
                    self.assertEqual(result['writes'],
                                     [(0x119e68, gate.BATTLE + gate.LAST_TIME, 4, now)]
                                     if expected else [])
                    self.assertFalse(result['formula_recovered'])

    def test_invalid_fixture_rejected(self):
        for args in ((-1, 0, 0), (0, 2**32, 0), (1, 0, True)):
            with self.assertRaises(ValueError):
                gate.evaluate(*args)


if __name__ == '__main__':
    unittest.main()
