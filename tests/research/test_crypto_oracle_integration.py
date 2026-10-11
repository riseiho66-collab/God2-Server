import ctypes
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/crypto_oracle'))
from oracle import ClientCryptoOracle
from oracle_lab_backend import OracleLabBackend
from differential import Clean, first_difference, run
from semantic_lift import transform_ir, cpp_from_ir

CAPSULE = ROOT / 'artifacts/crypto-oracle/capsule/capsule.json'
DLL = ROOT / 'build-crypto-oracle/Release/God2CryptoClean.dll'


class OracleIntegrationTests(unittest.TestCase):
    def test_actual_local_backend_and_direction_isolation(self):
        backend = OracleLabBackend(CAPSULE, lab_mode=True, production=False)
        backend.init_session(bytes(range(16)))
        before_rx = backend.rx
        plain = bytes(range(256)) + b'GOD2'
        wire = backend.encrypt(plain)
        self.assertEqual(backend.rx, before_rx)
        self.assertEqual(backend.decrypt(wire), plain)
        self.assertEqual(backend.tx, backend.rx)

    def test_guard_precedes_oracle_construction(self):
        with patch('oracle.ClientCryptoOracle') as factory:
            for options in ({}, {'lab_mode': True}, {'production': False},
                            {'lab_mode': True, 'production': False, 'endpoint': '203.0.113.1'}):
                with self.assertRaises(PermissionError):
                    OracleLabBackend(CAPSULE, **options)
            factory.assert_not_called()

    def test_generated_cpp_matches_original_capsule(self):
        ir = transform_ir(CAPSULE)
        self.assertFalse(ir['execution_trace'])
        self.assertEqual(cpp_from_ir(ir), (ROOT / 'generated/crypto_candidate.cpp').read_text())
        oracle = ClientCryptoOracle(CAPSULE)
        rng = random.Random(410690)
        library = ctypes.CDLL(str(ROOT / 'build-crypto-oracle/Release/God2CryptoCandidate.dll'))
        function = library.God2LiftedRaw
        pointer = ctypes.POINTER(ctypes.c_ubyte)
        function.argtypes = [ctypes.c_int, pointer, ctypes.c_uint, ctypes.c_uint,
                            pointer, ctypes.c_uint, pointer, ctypes.c_uint]
        function.restype = ctypes.c_int
        for seed in (bytes(16), bytes(range(16)), rng.randbytes(16)):
            state = bytes.fromhex(oracle.init_session(seed)['state_after_hex'])
            key = Clean.buffer(state[0x2420:0x2520])
            for length in (0, 1, 255, 256, 257, 1024, 4096):
                plain = rng.randbytes(length)
                wire = bytes.fromhex(oracle.encrypt(state, plain)['output_hex'])
                for decrypt, source, expected in ((0, plain, wire), (1, wire, plain)):
                    output = (ctypes.c_ubyte * max(1, length))()
                    self.assertEqual(function(decrypt, key, 256, state[0x2556], Clean.buffer(source),
                                              length, output, length), length)
                    self.assertEqual(bytes(output[:length]), expected)

    def test_first_difference_including_length(self):
        self.assertIsNone(first_difference(b'abc', b'abc'))
        self.assertEqual(first_difference(b'abc', b'ab'), {'offset': 2, 'oracle': 99, 'clean': None})
        self.assertEqual(first_difference(b'abc', b'axc')['offset'], 1)

    def test_mismatch_enables_trace_without_promoting(self):
        original = Clean.apply

        def faulty(self, operation, state, data):
            output, after = original(self, operation, state, data)
            if output:
                output = bytes([output[0] ^ 1]) + output[1:]
            return output, after

        with tempfile.TemporaryDirectory() as temp, patch.object(Clean, 'apply', faulty):
            output = Path(temp) / 'injected-fault'
            self.assertEqual(run(CAPSULE, DLL, output, seed_count=3, vectors_per_seed=1), 1)
            report = json.loads((output / 'differential-report.json').read_text())
            self.assertGreater(report['output_mismatches'], 0)
            self.assertFalse(report['CRYPTO_RECOVERED'])
            record = json.loads(next(output.glob('mismatch-*-encrypt.json')).read_text())
            self.assertEqual(record['FIRST_OUTPUT_DIFF_OFFSET']['offset'], 0)
            self.assertTrue(record['oracle_instruction_trace'])
            self.assertTrue(record['semantic_trace_ir']['operations'])
            self.assertIsNone(record['semantic_trace_ir']['FIRST_SEMANTIC_DIVERGENCE'])


if __name__ == '__main__':
    unittest.main()
