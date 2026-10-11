"""Offline validation and adversarial qualification tests; no live client."""
import ctypes
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/strike_lab'))
import crypto_recovery as recovery


def manifest():
    return {'session_id': 'session-a', 'model': 'packet_reset',
            'tx_key_hex': 'ab' * 256, 'rx_key_hex': 'cd' * 256,
            'packets': [
                {'seq': 1, 'packet_id': 'tx1', 'direction': 'C2S', 'wire_hex': '0600a3a3fdd5',
                 'state_before': 'TX0', 'state_after': 'TX1',
                 'known_plaintext_hex': '0600a60000d8', 'allowed_opcodes': [166],
                 'constants': [{'offset': 2, 'value': 166}]},
                {'seq': 2, 'packet_id': 'rx1', 'direction': 'S2C', 'wire_hex': '0600a3a3fdd5',
                 'state_before': 'RX0', 'state_after': 'RX1'},
                {'seq': 3, 'packet_id': 'tx2', 'direction': 'C2S', 'wire_hex': '0600a3a3fdd5',
                 'state_before': 'TX1', 'state_after': 'TX2', 'expected_state_before': 'TX1'}]}


class ValidationTests(unittest.TestCase):
    def test_separate_directional_objects_and_request_projection(self):
        value = manifest()
        value['packets'][0]['codec_object_id'] = 'object-tx'
        value['packets'][1]['codec_object_id'] = 'object-rx'
        result = recovery.validate_manifest(value)
        self.assertEqual(len(result['packets']), 3)
        self.assertNotIn('seq', result['packets'][0])
        self.assertNotIn('packet_id', result['packets'][0])
        self.assertNotIn('codec_object_id', result['packets'][0])
        self.assertNotEqual(result['tx_key_hex'], result['rx_key_hex'])

    def test_expected_state_rejected(self):
        for field in ('state_before', 'expected_state_before'):
            value = manifest()
            value['packets'][2][field] = 'RX1'
            with self.assertRaises(recovery.ValidationError):
                recovery.validate_manifest(value)

    def test_directional_chaining_hypothesis_rejected(self):
        value = manifest()
        value['model'] = 'directional_chained'
        with self.assertRaises(recovery.ValidationError):
            recovery.validate_manifest(value)

    def test_reset_does_not_inherit_directional_state(self):
        value = manifest()
        value['model'] = 'packet_reset'
        value['packets'][2]['state_before'] = 'TX0'
        value['packets'][2]['expected_state_before'] = 'TX0'
        recovery.validate_manifest(value)

    def test_missing_or_malformed_keys(self):
        for key in ('tx_key_hex', 'rx_key_hex'):
            for replacement in (None, '00', 'zz' * 256, '00 ' * 256):
                value = manifest()
                if replacement is None:
                    del value[key]
                else:
                    value[key] = replacement
                with self.assertRaises(recovery.ValidationError):
                    recovery.validate_manifest(value)

    def test_mixed_session_order_and_repeated_identity(self):
        for field, replacement in (('session_id', 'session-b'), ('seq', 1), ('seq', True),
                                   ('seq', -1), ('packet_id', 'tx1')):
            value = manifest()
            value['packets'][2][field] = replacement
            with self.assertRaises(recovery.ValidationError):
                recovery.validate_manifest(value)

    def test_conflicting_constraints_and_bounds(self):
        for field, replacement in (('wire_hex', '0700a3a3fdd5'), ('allowed_opcodes', [True]),
                                   ('allowed_opcodes', [1]), ('state_before', {'verified': True}),
                                   ('constants', [{'offset': 6, 'value': 0}]),
                                   ('constants', [{'offset': 2, 'value': 1}])):
            value = manifest()
            value['packets'][0][field] = replacement
            with self.assertRaises(recovery.ValidationError):
                recovery.validate_manifest(value)
        value = manifest()
        value['packets'] *= 100
        with self.assertRaises(recovery.ValidationError):
            recovery.validate_manifest(value)

    def test_duplicate_json_nonfinite_and_size(self):
        for data in (b'{"x":1,"x":2}', b'{"x":NaN}', b' ' * (recovery.MAX_JSON + 1)):
            with self.assertRaises(recovery.ValidationError):
                recovery.parse_json(data)


class FakeFunction:
    def __init__(self, response, size=None, second=None):
        self.response = response
        self.size = len(response) if size is None else size
        self.second = second
        self.calls = []

    def __call__(self, request, output, capacity):
        self.calls.append((request, capacity))
        if output is not None:
            ctypes.memmove(output, self.response, min(capacity, len(self.response)))
            return self.size if self.second is None else self.second
        return self.size


class NativeTests(unittest.TestCase):
    def call(self, function):
        class Library:
            God2RecoverCrypto = function
        with patch.object(recovery.ctypes, 'CDLL', return_value=Library()):
            return recovery.recover_native(recovery.validate_manifest(manifest()), 'unused.dll')

    def test_abi_size_query(self):
        function = FakeFunction(b'{"candidates":[]}\0')
        self.assertEqual(self.call(function), {'candidates': []})
        self.assertEqual(function.argtypes, [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_uint])
        self.assertEqual(function.restype, ctypes.c_int)
        self.assertEqual([c[1] for c in function.calls], [0, len(function.response)])

    def test_bad_size_response_and_terminator(self):
        for function in (FakeFunction(b'', size=-7), FakeFunction(b'', size=recovery.MAX_JSON + 1),
                         FakeFunction(b'{}x'), FakeFunction(b'{}\0', second=4),
                         FakeFunction(b'{\0}\0'), FakeFunction(b'[]\0')):
            with self.assertRaises(recovery.ValidationError):
                self.call(function)


class QualificationTests(unittest.TestCase):
    def test_boolean_forgery_and_old_fixture_never_promote(self):
        for claims in (None, True, {'verified': True, 'parser_check': True, 'fresh_runtime': True},
                       {'session_id': 'session-a', 'fixture_verified': True}):
            result = recovery.audit_runtime(claims, 'session-a', '.')
            self.assertFalse(result['verified'])
            self.assertEqual(result['status'], 'RUNTIME_VALIDATION_REQUIRED')

    def test_all_hashed_evidence_still_cannot_certify(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            refs = []
            for role in ('raw_packet', 'logical_packet', 'runtime_trace', 'parser_check'):
                data = json.dumps({'pid': 123, 'tid': 456, 'seq': 7, 'verified': True}).encode()
                (base / role).write_bytes(data)
                refs.append({'role': role, 'path': role, 'sha256': hashlib.sha256(data).hexdigest()})
            evidence = {'session_id': 'session-b', 'target_pid': 123, 'thread_id': 456,
                        'seq': 7, 'references': refs}
            result = recovery.audit_runtime(evidence, 'session-a', base)
            self.assertEqual(result['checked_reference_count'], 4)
            self.assertEqual(result['status'], 'RUNTIME_VALIDATION_REQUIRED')
            self.assertFalse(result['verified'])
            for field, replacement in (('session_id', 'session-a'), ('target_pid', True)):
                invalid = dict(evidence, **{field: replacement})
                self.assertEqual(recovery.audit_runtime(invalid, 'session-a', base)['checked_reference_count'], 0)
            refs[0]['sha256'] = '0' * 64
            self.assertFalse(recovery.audit_runtime(evidence, 'session-a', base)['verified'])
            refs[0]['path'] = '../outside'
            with self.assertRaises(recovery.ValidationError):
                recovery.EvidenceReference.read(refs[0], base)

    def test_callable_outputs_no_sensitive_engine_fields(self):
        secret = 'PLAINTEXT_SECRET'
        engine = {'verified': True, 'session_id': secret, 'tx_key_hex': 'ab' * 256,
                  'candidates': [{'verified': True, 'plain_frame_hex': secret, 'key': secret}],
                  'qualification': {'status': 'VERIFIED'}}
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / 'manifest.json'
            source.write_text(json.dumps(manifest()), encoding='utf-8')
            with patch.object(recovery, 'recover_native', return_value=engine) as native:
                result = recovery.recover(source, base / 'output', base / 'engine.dll')
                native.assert_called_once()
            self.assertFalse(result['qualification']['verified'])
            for path in (base / 'output').glob('*.json'):
                text = path.read_text(encoding='utf-8')
                self.assertNotIn(secret, text)
                self.assertNotIn('ab' * 256, text)
                self.assertNotIn('0600a60000d8', text)
                self.assertNotIn('"VERIFIED"', text)

    def test_invalid_input_never_loads_dll(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source = base / 'manifest.json'
            value = manifest()
            del value['tx_key_hex']
            source.write_text(json.dumps(value), encoding='utf-8')
            with patch.object(recovery, 'recover_native') as native:
                with self.assertRaises(recovery.ValidationError):
                    recovery.recover(source, base / 'output')
                native.assert_not_called()


if __name__ == '__main__':
    unittest.main()
