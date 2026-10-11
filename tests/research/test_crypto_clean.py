"""Clean DLL properties only. No search, client launch, or original-code execution.

Set GOD2_CLEAN_DLL to the parent-built DLL. The nonzero-seed fixture is derived
from instruction semantics, not an oracle-equivalence claim.
"""
import ctypes
import hashlib
import os
from pathlib import Path
import random
import unittest


ROOT = Path(__file__).resolve().parents[2]
STATE_SIZE = 0x255C
KEY_OFFSET = 0x2420
PROOF_OFFSET = 0x2520
FEEDBACK_OFFSET = 0x2556


def buffer(data):
    return ctypes.create_string_buffer(bytes(data), max(1, len(data)))


class CleanCryptoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(os.environ.get(
            'GOD2_CLEAN_DLL', ROOT / 'build-crypto-oracle/Release/God2CryptoClean.dll'))
        cls.dll = ctypes.CDLL(str(path))
        cls.init = cls.dll.God2CleanInit
        cls.init.argtypes = [ctypes.c_void_p, ctypes.c_uint] * 3
        cls.init.restype = ctypes.c_int
        cls.transform = cls.dll.God2CleanTransform
        cls.transform.argtypes = [ctypes.c_int] + [ctypes.c_void_p, ctypes.c_uint] * 4
        cls.transform.restype = ctypes.c_int

    def initialize(self, seed, table):
        state = buffer(b'\xcc' * (STATE_SIZE + 13))
        self.assertEqual(self.init(buffer(seed), len(seed), buffer(table), len(table),
                                   state, len(state)), STATE_SIZE)
        self.assertEqual(state.raw[STATE_SIZE:], b'\xcc' * 13)
        return state.raw[:STATE_SIZE]

    def call(self, state, data, decrypt=0):
        source, before = buffer(data), buffer(state)
        output, after = buffer(b'\xcc' * (len(data) + 7)), buffer(b'\xdd' * len(state))
        self.assertEqual(self.transform(decrypt, before, len(state), source, len(data),
                                        output, len(output), after, len(after)), len(data))
        self.assertEqual(after.raw, state)
        self.assertEqual(before.raw, state)
        self.assertEqual(source.raw[:len(data)], data)
        self.assertEqual(output.raw[len(data):], b'\xcc' * 7)
        return output.raw[:len(data)]

    def test_nonzero_seed_instruction_fixture(self):
        seed = bytes.fromhex('00ff807f10ef55aa0123456789abcdef')
        table = bytes((i * 73 + 19) & 255 for i in range(1024))
        state = self.initialize(seed, table)
        key = state[KEY_OFFSET:KEY_OFFSET + 256]
        self.assertEqual(key[:16], seed)
        self.assertEqual(hashlib.sha256(key).hexdigest(),
                         '4a0fb9c00222a60e531d8254aad8cf121268802fdd4a03dc8799c8f04c825922')
        self.assertEqual(state[PROOF_OFFSET:PROOF_OFFSET + 16].hex(),
                         '545b95cb7e7a16cc3c5e7db36662feb4')
        self.assertEqual(state[FEEDBACK_OFFSET], 254)
        remainder = bytearray(state)
        remainder[8] = 0
        remainder[KEY_OFFSET:PROOF_OFFSET + 16] = bytes(272)
        remainder[FEEDBACK_OFFSET] = 0
        self.assertEqual(remainder, bytes(STATE_SIZE))

    def test_existing_local_zero_seed_fixture(self):
        image = ROOT / 'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
        if not image.exists():
            self.skipTest('Local captured table is unavailable')
        with image.open('rb') as stream:
            stream.seek(0x184C30)
            table = stream.read(1024)
        state = self.initialize(bytes(16), table)
        expected = bytes(16) + bytes((table[i] + i) & 255 for i in range(16, 256))
        self.assertEqual(state[KEY_OFFSET:KEY_OFFSET + 256], expected)
        self.assertEqual(state[FEEDBACK_OFFSET], (-sum(expected)) & 255)
        self.assertEqual(self.call(state, bytes.fromhex('a60000d8')).hex(), 'a3a3fdd5')

    def test_roundtrip_wrap_reset_and_state_preservation(self):
        rng = random.Random(410690)
        for enabled in (0, 1, 0x100, 0x80000000, 0xFFFFFFFF):
            state = bytearray(rng.randbytes(STATE_SIZE + 19))
            state[8:12] = enabled.to_bytes(4, 'little')
            for length in (0, 1, 2, 15, 16, 255, 256, 257, 511, 512, 4095, 4096):
                for data in (bytes(length), bytes([255]) * length, rng.randbytes(length)):
                    with self.subTest(enabled=enabled, length=length):
                        encoded = self.call(state, data)
                        self.assertEqual(self.call(state, encoded, 1), data)
                        self.assertEqual(self.call(state, data), encoded)
                        if enabled == 0:
                            self.assertEqual(encoded, data)
                        else:
                            previous = bytes([state[FEEDBACK_OFFSET]]) + data
                            expected = bytes(((v ^ state[KEY_OFFSET + (i & 255)]) +
                                              previous[i] - 3) & 255 for i, v in enumerate(data))
                            self.assertEqual(encoded, expected)

    def test_in_place_and_empty_null_body(self):
        state = buffer(self.initialize(bytes(16), bytes(1024)))
        original = state.raw
        body = buffer(bytes(range(256)) * 2)
        plain = body.raw
        for decrypt in (0, 1):
            self.assertEqual(self.transform(decrypt, state, len(state), body, len(body),
                                            body, len(body), state, len(state)), len(body))
            self.assertEqual(state.raw, original)
        self.assertEqual(body.raw, plain)
        self.assertEqual(self.transform(0, state, len(state), None, 0,
                                        None, 0, state, len(state)), 0)
        self.assertEqual(state.raw, original)

    def test_invalid_init_is_transactional(self):
        seed, table, state = buffer(bytes(16)), buffer(bytes(1024)), buffer(b'X' * STATE_SIZE)
        valid = [seed, 16, table, 1024, state, STATE_SIZE]
        for index, value in ((0, None), (1, 0), (1, 15), (1, 17), (2, None),
                             (3, 1023), (3, 1025), (4, None), (5, STATE_SIZE - 1)):
            args = valid.copy()
            args[index] = value
            self.assertLess(self.init(*args), 0)
            self.assertEqual(state.raw, b'X' * STATE_SIZE)

    def test_invalid_transform_is_transactional(self):
        state, data = buffer(bytes(STATE_SIZE)), buffer(bytes(4097))
        output, after = buffer(b'X' * 4097), buffer(b'Y' * STATE_SIZE)
        valid = [0, state, STATE_SIZE, data, 17, output, 4097, after, STATE_SIZE]
        for index, value in ((0, -1), (0, 2), (1, None), (2, STATE_SIZE - 1),
                             (3, None), (4, 4097), (5, None), (6, 16),
                             (7, None), (8, STATE_SIZE - 1), (5, after)):
            args = valid.copy()
            args[index] = value
            self.assertLess(self.transform(*args), 0)
            self.assertEqual(output.raw, b'X' * 4097)
            self.assertEqual(after.raw, b'Y' * STATE_SIZE)


if __name__ == '__main__':
    unittest.main()
