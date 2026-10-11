"""Legacy per-packet search cannot bypass session-global recovery constraints."""
import ctypes
import json
from pathlib import Path
import unittest


class LegacyBruteTests(unittest.TestCase):
    def test_legacy_requires_manifest(self):
        root = Path(__file__).resolve().parents[2]
        library = ctypes.CDLL(str(root / 'build-strike-lab/Release/God2Probe.dll'))
        function = library.God2BrutePacket
        pointer = ctypes.POINTER(ctypes.c_ubyte)
        function.argtypes = [pointer, ctypes.c_uint, pointer, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint]
        function.restype = ctypes.c_int
        wire = (ctypes.c_ubyte * 6)(*bytes.fromhex('0600a3a3fdd5'))
        key = (ctypes.c_ubyte * 256)()
        size = function(wire, 6, key, 256, None, 0)
        output = ctypes.create_string_buffer(size)
        self.assertEqual(function(wire, 6, key, 256, output, size), size)
        report = json.loads(output.value)
        self.assertEqual(report['status'], 'RECOVERY_MANIFEST_REQUIRED')
        self.assertEqual(report['tested'], 0)
        self.assertFalse(report['CRYPTO_RECOVERED'])
        small = ctypes.create_string_buffer(b'unchanged')
        self.assertEqual(function(wire, 6, key, 256, small, len(small)), size)
        self.assertEqual(small.value, b'unchanged')


if __name__ == '__main__':
    unittest.main()
