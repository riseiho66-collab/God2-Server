"""CPU-only ABI regression; synthetic inputs are not fresh runtime evidence."""
import ctypes
from pathlib import Path
import random
import unittest

ROOT = Path(__file__).resolve().parents[2]


class CryptoBoundsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dll = ctypes.CDLL(str(ROOT / 'build-strike-lab/Release/God2Probe.dll'))
        cls.decode = cls.dll.God2DecodePacket
        pointer = ctypes.POINTER(ctypes.c_ubyte)
        cls.decode.argtypes = [pointer, ctypes.c_uint, pointer, ctypes.c_uint,
                              ctypes.c_uint, pointer, ctypes.c_uint]
        cls.decode.restype = ctypes.c_int

    def check(self, wire, key, feedback, capacity, expected, plain=None):
        source = (ctypes.c_ubyte * max(1, len(wire)))(*wire)
        key_buffer = (ctypes.c_ubyte * max(1, len(key)))(*key)
        output = (ctypes.c_ubyte * 274)(*([0xCC] * 274))
        destination = ctypes.cast(ctypes.byref(output, 8), ctypes.POINTER(ctypes.c_ubyte))
        status = self.decode(source, len(wire), key_buffer, len(key), feedback,
                             destination, capacity)
        self.assertEqual(status, expected)
        self.assertEqual(bytes(source)[:len(wire)], bytes(wire))
        self.assertEqual(bytes(key_buffer)[:len(key)], bytes(key))
        if expected < 0:
            self.assertEqual(bytes(output), b'\xcc' * 274)
        else:
            self.assertEqual(bytes(output[:8]), b'\xcc' * 8)
            self.assertEqual(bytes(output[8:8 + len(plain)]), plain)
            self.assertEqual(bytes(output[8 + len(plain):]), b'\xcc' * (266 - len(plain)))

    @staticmethod
    def frame(rng, length, key, feedback):
        plain = bytearray(length.to_bytes(2, 'little') + rng.randbytes(length - 3))
        plain.append(sum(value + 0x3C for value in plain) & 255)
        wire = bytearray(plain[:2])
        previous = feedback
        for index, value in enumerate(plain[2:]):
            wire.append(((value ^ key[index]) + previous - 3) & 255)
            previous = value
        return wire, bytes(plain)

    def test_deterministic_malformed_bounds(self):
        rng = random.Random(0x60D2)
        for index in range(256):
            length = (4, 258)[index] if index < 2 else rng.randint(4, 258)
            key = rng.randbytes(256)
            feedback = rng.randrange(256)
            wire, plain = self.frame(rng, length, key, feedback)
            with self.subTest(index=index, length=length):
                self.check(wire, key, feedback, length, length, plain)
                bad = bytearray(wire)
                bad[-1] ^= rng.randint(1, 255)
                self.check(bad, key, feedback, 258, -5)
                bad = bytearray(wire)
                bad[1] |= 0x80
                self.check(bad, key, feedback, 258, -3)
                bad = bytearray(wire)
                header = rng.randrange(0x8000)
                if header == length:
                    header ^= 1
                bad[:2] = header.to_bytes(2, 'little')
                self.check(bad, key, feedback, 258, -4)
                key_length = rng.choice((0, 1, 255, 257, 512))
                self.check(wire, rng.randbytes(key_length), feedback, 258, -2)
                self.check(wire, key, rng.randint(256, 0xFFFFFFFF), 258, -2)
                self.check(wire, key, feedback, rng.randrange(length), -6)
                invalid_length = rng.choice((0, 1, 2, 3, 259, 260, 512, 4096))
                self.check(rng.randbytes(invalid_length), key, feedback, 258, -1)


if __name__ == '__main__':
    unittest.main()
