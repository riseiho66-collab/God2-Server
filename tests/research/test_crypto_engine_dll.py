"""Contract tests against the parent-built God2RecoverCrypto export only."""
import copy
import ctypes
import json
import os
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/strike_lab'))
from c2s0002 import key as captured_key

SIX = bytes.fromhex('0600a60000d8')  # Permanent captured logical oracle.
SIX_WIRE = bytes.fromhex('0600a3a3fdd5')


def plaintext(payload):
    length = len(payload) + 3
    body = length.to_bytes(2, 'little') + bytes(payload)
    return body + bytes([sum(value + 0x3c for value in body) & 255])


def encode(plain, key, offset=0, feedback=0):
    # Verified inverse: src/protocol/RecoveredC2S0002.h::encode.
    # Offset/feedback variations exercise search parameters, not runtime claims.
    wire = bytearray(plain[:2])
    previous = feedback
    for index, value in enumerate(plain[2:]):
        wire.append(((value ^ key[(offset + index) & 255]) + previous - 3) & 255)
        previous = value
    return wire.hex()


def packet(direction, plain, key, offset=0, feedback=0):
    return dict(direction=direction, wire_hex=encode(plain, key, offset, feedback),
                known_plaintext_hex=plain.hex(), state_before='ready', state_after='ready')


def request(keys=None, plains=None, parameters=((0, 0), (0, 0))):
    if keys is None:
        rng = random.Random(410690)
        keys = tuple(bytes(rng.randrange(256) for _ in range(256)) for _ in range(2))
    if plains is None:
        plains = (SIX, plaintext(bytes(range(1, 48))))
    packets = []
    for d, direction in enumerate(('C2S', 'S2C')):
        packets.extend(packet(direction, p, keys[d], *parameters[d]) for p in plains)
    return dict(session_id='dll-property-fixture', model='packet_reset',
                tx_key_hex=keys[0].hex(), rx_key_hex=keys[1].hex(), packets=packets)


class CryptoEngineDllTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(os.environ.get('GOD2_PROBE_DLL',
                                   ROOT / 'build-strike-lab/Release/God2Probe.dll'))
        cls.dll = ctypes.CDLL(str(path))
        cls.recover = cls.dll.God2RecoverCrypto
        cls.recover.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_uint]
        cls.recover.restype = ctypes.c_int

    def call(self, value):
        source = json.dumps(value, separators=(',', ':')).encode()
        required = self.recover(source, None, 0)
        self.assertGreater(required, 0)
        output = ctypes.create_string_buffer(required)
        self.assertEqual(self.recover(source, output, required), required)
        self.assertEqual(len(output.value) + 1, required)
        result = json.loads(output.value)
        self.assertFalse(result['verified'])
        self.assertFalse(result['CRYPTO_RECOVERED'])
        self.assertFalse(result['fresh_runtime_established'])
        self.assertNotIn('CODEX_VERIFIED', output.value.decode())
        return result

    def assert_accounting(self, report):
        stats = report['stats']
        rejected = sum(value for name, value in stats.items() if name.startswith('rejected_'))
        self.assertEqual(stats['tested'], 65536)
        self.assertEqual(rejected + stats['survivors'], stats['tested'])
        self.assertEqual(report['candidate_count'], stats['survivors'])
        self.assertEqual(report['truncated'], report['candidate_count'] > 256)
        self.assertEqual(len(report['candidates']), min(report['candidate_count'], 256))

    def test_permanent_six_byte_oracle(self):
        key = bytes(captured_key(ROOT))
        self.assertEqual(encode(SIX, key), SIX_WIRE.hex())
        value = request((key, key), (SIX,))
        for p in value['packets']:
            p['wire_hex'] = SIX_WIRE.hex()
        result = self.call(value)
        self.assertNotEqual(result['status'], 'UNIQUE_CANDIDATE')
        for report in result['directions'].values():
            self.assert_accounting(report)
            self.assertTrue(any(c['key_offset'] == 0 and c['feedback'] == 0
                                for c in report['candidates']))

    def test_independent_parameters_wrap_and_reset(self):
        for parameters in (((0, 0), (1, 37)), ((255, 255), (219, 108))):
            with self.subTest(parameters=parameters):
                value = request(parameters=parameters,
                                plains=(SIX, plaintext(bytes(range(255)))))
                result = self.call(value)
                self.assertEqual(result['status'], 'UNIQUE_CANDIDATE')
                for d, direction in enumerate(('C2S', 'S2C')):
                    report = result['directions'][direction]
                    self.assert_accounting(report)
                    c = report['candidates'][0]
                    self.assertEqual((c['key_offset'], c['feedback']), parameters[d])
                    self.assertEqual(c['packets_survived'], 2)
                    self.assertEqual(c['sequence'], 2)
                    self.assertEqual(c['bytes_consumed'], 260)
                    self.assertEqual(c['directional_state']['key_offset'], parameters[d][0])
                    self.assertEqual(c['directional_state']['feedback'], parameters[d][1])
                    self.assertTrue(c['known_plaintext_match'])

    def test_ambiguity_serialization_boundary_and_equivalence(self):
        result = self.call(request((bytes(256), bytes(256))))
        self.assertEqual(result['status'], 'AMBIGUOUS')
        for report in result['directions'].values():
            self.assert_accounting(report)
            # Exact oracle fixes feedback per offset: 256 is the attainable cap.
            self.assertEqual(report['candidate_count'], 256)
            self.assertFalse(report['truncated'])
            self.assertEqual(len({(c['key_offset'], c['feedback'])
                                  for c in report['candidates']}), 256)
            self.assertEqual(report['differential']['status'], 'mathematically_equivalent_states')
            self.assertIsNone(report['differential']['first_differing_offset'])
            self.assertFalse(report['differential']['need_next_real_constraint'])

    def test_duplicate_packet_is_not_fresh_evidence(self):
        result = self.call(request(plains=(SIX, SIX)))
        self.assertNotEqual(result['status'], 'UNIQUE_CANDIDATE')
        for report in result['directions'].values():
            self.assertEqual(report['distinct_packet_count'], 1)
            self.assertFalse(report['fresh_runtime_established'])
            for c in report['candidates']:
                self.assertEqual(c['cross_packet_score'], 1)

    def test_no_oracle_is_not_a_checksum_dump(self):
        for direction in ('C2S', 'S2C'):
            value = request()
            for p in value['packets']:
                if p['direction'] == direction:
                    del p['known_plaintext_hex']
            result = self.call(value)
            self.assertEqual(result['status'], 'INSUFFICIENT_CONSTRAINTS')
            self.assertEqual(result['directions'], {})

    def test_pruning_and_direction_isolation(self):
        cases = (
            ('rejected_length', {'wire_hex': '0700a3a3fdd5'}),
            ('rejected_header', {'wire_hex': '0680a3a3fdd5'}),
            ('rejected_state', {'expected_state_before': 'wrong'}),
            ('rejected_opcode', {'allowed_opcodes': []}),
            ('rejected_known_plaintext', {'constants': [{'offset': 2, 'value': 0}]}),
            ('rejected_bounds', {'constants': [{'offset': 200, 'value': 0}]}),
        )
        for counter, change in cases:
            with self.subTest(counter=counter):
                value = request()
                value['packets'][0].update(change)
                result = self.call(value)
                report = result['directions']['C2S']
                self.assert_accounting(report)
                self.assertEqual(report['candidate_count'], 0)
                self.assertGreater(report['stats'][counter], 0)
                self.assertEqual(result['directions']['S2C']['candidate_count'], 1)

    def test_later_state_and_checksum_prune_survivors(self):
        for kind in ('state', 'checksum'):
            value = request()
            p = value['packets'][1]
            if kind == 'state':
                p['state_before'] = 'unrelated'
            else:
                wire = bytearray.fromhex(p['wire_hex'])
                wire[-1] ^= 1
                p['wire_hex'] = wire.hex()
            result = self.call(value)
            report = result['directions']['C2S']
            self.assert_accounting(report)
            self.assertEqual(report['candidate_count'], 0)
            self.assertGreater(report['stats']['rejected_' + kind], 0)

    def test_credentials_never_serialized(self):
        plain = plaintext(bytes(range(173)))
        self.assertEqual(len(plain), 176)
        value = request(plains=(SIX, plain))
        result = self.call(value)
        encoded = json.dumps(result)
        self.assertNotIn(plain.hex(), encoded)
        self.assertNotIn(value['tx_key_hex'], encoded)
        self.assertNotIn('plain_frame_hex', encoded)
        for report in result['directions'].values():
            self.assertEqual(report['differential']['status'], 'unique')
            self.assertTrue(all(c['plaintext_redacted'] for c in report['candidates']))

    def test_strict_schema_and_unsupported_chaining(self):
        original = request()
        invalid = []
        for field, value in (('session_id', 1), ('tx_key_hex', '00'),
                             ('rx_key_hex', 'zz' * 256), ('packets', {}),
                             ('model', 'directional_chained')):
            changed = copy.deepcopy(original)
            changed[field] = value
            invalid.append(changed)
        for field, value in (('allowed_opcodes', [True]), ('allowed_opcodes', [256]),
                             ('allowed_opcodes', [1.0]), ('state_before', None),
                             ('known_plaintext_hex', '00'), ('wire_hex', '0'),
                             ('direction', 'TX'), ('expected_state_before', False),
                             ('constants', [{'offset': -1, 'value': 0}]),
                             ('constants', [{'offset': 2, 'value': 256}])):
            changed = copy.deepcopy(original)
            changed['packets'][0][field] = value
            invalid.append(changed)
        for value in invalid:
            output = ctypes.create_string_buffer(b'unchanged')
            result = self.recover(json.dumps(value).encode(), output, len(output))
            self.assertLess(result, 0)
            self.assertEqual(output.value, b'unchanged')

    def test_output_capacity_and_null_contract(self):
        source = json.dumps(request()).encode()
        required = self.recover(source, None, 0)
        self.assertGreater(required, 0)
        for capacity in (0, 8, required - 1):
            output = ctypes.create_string_buffer(b'x' * required)
            before = output.raw
            self.assertEqual(self.recover(source, output, capacity), required)
            self.assertEqual(output.raw, before)
        self.assertLess(self.recover(None, None, 0), 0)
        self.assertLess(self.recover(source, None, 1), 0)


if __name__ == '__main__':
    unittest.main()
