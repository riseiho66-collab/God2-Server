"""Property controls for instruction-proven encode/decode, not client qualification."""
import ctypes
from pathlib import Path
import random
import unittest


class RoundtripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[2]
        cls.dll = ctypes.CDLL(str(root / 'build-strike-lab/Release/God2Probe.dll'))
        pointer = ctypes.POINTER(ctypes.c_ubyte)
        for name in ('God2EncodePacket', 'God2DecodePacket'):
            function = getattr(cls.dll, name)
            function.argtypes = [pointer, ctypes.c_uint, pointer, ctypes.c_uint,
                                 ctypes.c_uint, pointer, ctypes.c_uint]
            function.restype = ctypes.c_int

    def apply(self, name, source, key, feedback):
        buffer = (ctypes.c_ubyte * len(source))(*source)
        key_buffer = (ctypes.c_ubyte * 256)(*key)
        output = (ctypes.c_ubyte * len(source))()
        self.assertEqual(getattr(self.dll, name)(buffer, len(source), key_buffer, 256,
                                                feedback, output, len(source)), len(source))
        return bytes(output)

    def test_random_invertible_frames(self):
        rng = random.Random(0x410690)
        for length in range(4, 259):
            key = rng.randbytes(256)
            feedback = rng.randrange(256)
            plain = length.to_bytes(2, 'little') + rng.randbytes(length - 3)
            plain += bytes([sum(value + 0x3c for value in plain) & 255])
            wire = self.apply('God2EncodePacket', plain, key, feedback)
            decoded = self.apply('God2DecodePacket', wire, key, feedback)
            self.assertEqual(decoded, plain)
            self.assertEqual(self.apply('God2EncodePacket', decoded, key, feedback), wire)


if __name__ == '__main__':
    unittest.main()
