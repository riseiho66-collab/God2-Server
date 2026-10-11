"""Synthetic x86 controls; these tests do not establish live-client equivalence."""
import hashlib
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('crypto_oracle_runtime', ROOT / 'tools/crypto_oracle/oracle.py')
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)
HAS_UNICORN = importlib.util.find_spec('unicorn') is not None


@unittest.skipUnless(HAS_UNICORN, 'Parent must install local Unicorn dependency')
class OracleRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'capsule.json'
        # seed[0] -> proof[0]; no write to the caller-controlled enabled DWORD.
        self.init_code = bytes.fromhex('8b5424048a02888120250000c20400')
        # input[0] ^= 0x5a; feedback++; preserve ECX and callee stack cleanup.
        self.transform = bytes.fromhex('8b54240480325afe8156250000c20800')
        self.make_capsule(self.transform)
        self.loader = patch.object(oracle, '_load_capsule', side_effect=lambda p: json.loads(p.read_text()))
        self.loader.start()
        self.addCleanup(self.loader.stop)

    def make_capsule(self, transform, extra_regions=()):
        code = self.init_code.ljust(0x100, b'\x90') + transform
        (self.root / 'code.bin').write_bytes(code)
        manifest = dict(image_base=0x400000,
            entries=dict(init_session=0x410000, encrypt=0x410100, decrypt=0x410100),
            regions=[dict(address=0x410000, size=len(code), kind='CODE', file='code.bin',
                          sha256=hashlib.sha256(code).hexdigest()), *extra_regions])
        self.path.write_text(json.dumps(manifest), encoding='utf-8')

    def test_seed_fixture_and_snapshot(self):
        runtime = oracle.ClientCryptoOracle(self.path)
        result = runtime.init_session(bytes(range(16)))
        state = bytes.fromhex(result['state_after_hex'])
        self.assertEqual(len(state), oracle.STATE_SIZE)
        self.assertEqual(state[8:12], b'\x01\0\0\0')
        self.assertEqual(result['snapshot']['origin'], 'SYNTHETIC_EMULATOR_ENTRY')
        self.assertEqual(result['snapshot']['regs']['ECX'], oracle.OBJECT)
        self.assertNotIn('instruction_trace', result)
        with self.assertRaises(ValueError):
            runtime.init_session(b'bad')

    def test_transform_determinism_state_and_footprints(self):
        runtime = oracle.ClientCryptoOracle(self.path)
        state = bytes(oracle.STATE_SIZE)
        a = runtime.encrypt(state, b'abc')
        self.assertEqual(a, runtime.encrypt(state, b'abc'))
        self.assertEqual(bytes.fromhex(a['output_hex']), b';bc')
        self.assertEqual(bytes.fromhex(a['state_after_hex'])[0x2556], 1)
        self.assertEqual(a['modified_state']['bytes'], [dict(offset=0x2556, before=0, after=1)])
        self.assertTrue(any(r['kind'] == 'OUTPUT' and r['pc'] for r in a['memory_writes']))
        self.assertEqual(runtime.decrypt(state, bytes.fromhex(a['output_hex']))['output_hex'], b'abc'.hex())
        with self.assertRaises(ValueError):
            runtime.encrypt(b'', b'x')

    def test_trace_registers_and_memory(self):
        result = oracle.ClientCryptoOracle(self.path).encrypt(bytes(oracle.STATE_SIZE), b'a', trace=True)
        trace = result['instruction_trace']
        self.assertEqual(trace[0]['rva'], 0x10100)
        self.assertIn('register_after', trace[-1])
        writes = [w for ins in trace for w in ins['memory_writes']]
        self.assertTrue(any(w['before_hex'] == '61' and w['after_hex'] == '3b' for w in writes))

    def test_refuses_mutated_region(self):
        (self.root / 'code.bin').write_bytes(b'bad')
        with self.assertRaisesRegex(oracle.OracleError, 'hash mismatch'):
            oracle.ClientCryptoOracle(self.path)

    def test_loader_binding_failure_propagates(self):
        with patch.object(oracle, '_load_capsule', side_effect=ValueError('binding mismatch')):
            with self.assertRaisesRegex(ValueError, 'binding mismatch'):
                oracle.ClientCryptoOracle(self.path)

    def test_unmapped_read(self):
        self.make_capsule(bytes.fromhex('a100005050c20800'))
        with self.assertRaises(oracle.OracleError):
            oracle.ClientCryptoOracle(self.path).encrypt(bytes(oracle.STATE_SIZE), b'x')

    def test_page_padding_read_rejected(self):
        # First byte past the exact object is still in its allocated page.
        self.make_capsule(bytes.fromhex('a15c250010c20800'))
        with self.assertRaisesRegex(oracle.OracleError, 'Forbidden memory'):
            oracle.ClientCryptoOracle(self.path).encrypt(bytes(oracle.STATE_SIZE), b'x')

    def test_code_write_rejected(self):
        self.make_capsule(bytes.fromhex('c6050000410090c20800'))
        with self.assertRaises(oracle.OracleError):
            oracle.ClientCryptoOracle(self.path).encrypt(bytes(oracle.STATE_SIZE), b'x')

    def test_noncode_execution_rejected(self):
        self.make_capsule(bytes.fromhex('b800000010ffe0'))
        with self.assertRaises(oracle.OracleError):
            oracle.ClientCryptoOracle(self.path).encrypt(bytes(oracle.STATE_SIZE), b'x')

    def test_empty_input_padding_is_not_readable(self):
        self.make_capsule(bytes.fromhex('a100000020c20800'))
        with self.assertRaisesRegex(oracle.OracleError, 'Forbidden memory'):
            oracle.ClientCryptoOracle(self.path).encrypt(bytes(oracle.STATE_SIZE), b'')

    def test_code_padding_execution_rejected(self):
        self.make_capsule(bytes.fromhex('b800084100ffe0'))
        with self.assertRaisesRegex(oracle.OracleError, 'outside code allowlist'):
            oracle.ClientCryptoOracle(self.path).encrypt(bytes(oracle.STATE_SIZE), b'x')

    def test_constant_table_access_control(self):
        data = b'abcd'
        (self.root / 'table.bin').write_bytes(data)
        region = dict(address=0x500000, size=4, kind='CONSTANT_TABLE', file='table.bin',
                      sha256=hashlib.sha256(data).hexdigest())
        self.make_capsule(bytes.fromhex('a100005000c20800'), [region])
        result = oracle.ClientCryptoOracle(self.path).encrypt(bytes(oracle.STATE_SIZE), b'x')
        self.assertTrue(any(r['kind'] == 'CONSTANT_TABLE' for r in result['memory_reads']))
        self.make_capsule(bytes.fromhex('a300005000c20800'), [region])
        with self.assertRaises(oracle.OracleError):
            oracle.ClientCryptoOracle(self.path).encrypt(bytes(oracle.STATE_SIZE), b'x')

    def test_timeout(self):
        self.make_capsule(b'\xeb\xfe')
        with self.assertRaisesRegex(oracle.OracleError, 'timeout'):
            oracle.ClientCryptoOracle(self.path, timeout_us=1).encrypt(bytes(oracle.STATE_SIZE), b'')

    def test_budget_and_calling_convention(self):
        self.make_capsule(b'\xeb\xfe')
        with self.assertRaisesRegex(oracle.OracleError, 'budget'):
            oracle.ClientCryptoOracle(self.path, instruction_budget=10).encrypt(bytes(oracle.STATE_SIZE), b'')
        self.make_capsule(b'\xc3')
        with self.assertRaisesRegex(oracle.OracleError, 'calling convention'):
            oracle.ClientCryptoOracle(self.path).encrypt(bytes(oracle.STATE_SIZE), b'')

    def test_empty_input_and_batch_cli(self):
        self.make_capsule(bytes.fromhex('c20800'))
        runtime = oracle.ClientCryptoOracle(self.path)
        self.assertEqual(runtime.encrypt(bytes(oracle.STATE_SIZE), b'')['output_hex'], '')
        request = self.root / 'request.json'
        output = self.root / 'output.json'
        request.write_text(json.dumps([
            dict(mode='init_session', seed_hex='aa' * 16),
            dict(mode='encrypt', state_hex='00' * oracle.STATE_SIZE, input_hex='')]))
        self.assertEqual(oracle.main(['--capsule', str(self.path), '--batch', str(request),
                                      '--output', str(output)]), 0)
        results = json.loads(output.read_text())
        self.assertEqual(len(results), 2)
        self.assertEqual(bytes.fromhex(results[0]['state_after_hex'])[0x2520], 0xaa)

    @staticmethod
    def rehash(snapshot):
        snapshot.pop('entry_layout_sha256', None)
        snapshot['entry_layout_sha256'] = hashlib.sha256(
            oracle._canonical(snapshot).encode('utf-8')).hexdigest()

    def test_replay_all_modes_exact_results(self):
        runtime = oracle.ClientCryptoOracle(self.path)
        initialized = runtime.init_session(bytes(range(16)))
        state = bytes.fromhex(initialized['state_after_hex'])
        results = [initialized, runtime.encrypt(state, b'abc'), runtime.decrypt(state, b'abc')]
        for result in results:
            with self.subTest(mode=result['snapshot']['mode']):
                snapshot = json.loads(json.dumps(result['snapshot']))
                self.assertEqual(snapshot['capsulehash'], runtime.capsulehash)
                self.assertEqual(runtime.replay(snapshot), result)
                traced = runtime.replay(snapshot, trace=True)
                self.assertTrue(traced.pop('instruction_trace'))
                self.assertEqual(traced, result)
                self.assertEqual(sum(r['count'] for r in result['code_fetches']), result['instruction_count'])
                self.assertTrue(all(r['kind'] == 'CODE' for r in result['code_fetches']))
                self.assertNotIn('instruction_trace', result)

    def test_replay_rejects_modified_registers_even_with_recomputed_digest(self):
        runtime = oracle.ClientCryptoOracle(self.path)
        snapshot = runtime.encrypt(bytes(oracle.STATE_SIZE), b'x')['snapshot']
        for register in snapshot['regs']:
            with self.subTest(register=register):
                modified = copy.deepcopy(snapshot)
                modified['regs'][register] ^= 1
                self.rehash(modified)
                with self.assertRaisesRegex(oracle.OracleError, 'canonical deterministic entry layout'):
                    runtime.replay(modified)

    def test_replay_rejects_every_modified_map_region(self):
        runtime = oracle.ClientCryptoOracle(self.path)
        snapshot = runtime.encrypt(bytes(oracle.STATE_SIZE), b'x')['snapshot']
        for index in range(len(snapshot['memorymap'])):
            with self.subTest(region=index):
                modified = copy.deepcopy(snapshot)
                region = modified['memorymap'][index]
                data = bytes.fromhex(region['hex'])
                data = bytes([data[0] ^ 1]) + data[1:]
                region['hex'] = data.hex()
                region['sha256'] = hashlib.sha256(data).hexdigest()
                self.rehash(modified)
                with self.assertRaisesRegex(oracle.OracleError, 'canonical deterministic entry layout'):
                    runtime.replay(modified)

    def test_replay_rejects_snapshot_metadata_and_stack_changes(self):
        runtime = oracle.ClientCryptoOracle(self.path)
        snapshot = runtime.encrypt(bytes(oracle.STATE_SIZE), b'x')['snapshot']
        modifications = [dict(origin='LIVE_CAPTURE'), dict(format_version=2),
                         dict(mode='unknown'), dict(capsulehash='0' * 64),
                         dict(stack=dict(address=oracle.STACK, hex='00')),
                         dict(memorymap=snapshot['memorymap'][:-1])]
        for fields in modifications:
            with self.subTest(fields=list(fields)):
                modified = copy.deepcopy(snapshot)
                modified.update(fields)
                self.rehash(modified)
                with self.assertRaises(oracle.OracleError):
                    runtime.replay(modified)
        snapshot['regs']['EAX'] = 42
        with self.assertRaisesRegex(oracle.OracleError, 'layout hash mismatch'):
            runtime.replay(snapshot)

    def test_replay_rechecks_artifacts(self):
        runtime = oracle.ClientCryptoOracle(self.path)
        snapshot = runtime.encrypt(bytes(oracle.STATE_SIZE), b'x')['snapshot']
        (self.root / 'code.bin').write_bytes(b'modified')
        with self.assertRaisesRegex(oracle.OracleError, 'hash mismatch'):
            runtime.replay(snapshot)

    def test_replay_cli(self):
        runtime = oracle.ClientCryptoOracle(self.path)
        original = runtime.encrypt(bytes(oracle.STATE_SIZE), b'abc')
        request = self.root / 'snapshot.json'
        output = self.root / 'replayed.json'
        request.write_text(json.dumps(original['snapshot']), encoding='utf-8')
        self.assertEqual(oracle.main(['--capsule', str(self.path), '--replay',
                                     '--request', str(request), '--output', str(output)]), 0)
        self.assertEqual(json.loads(output.read_text()), original)


if __name__ == '__main__':
    unittest.main()
