"""Operational safety tests; fabricated records are never runtime evidence."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools'/'research'))
from runtime_environment_probe import ARTIFACT, CHECKS, probe, ready
from host_capture import firewall_ready
from normalize_cdb_capture import mapped_to_candidate, native_bytes, observed_marks
from test_artifact_vault import synthetic_pe
import pefile


class CdbNormalizationTests(unittest.TestCase):
    def trace(self):
        locations = [('PACKER', 0x702001), ('TRANSFER_SOURCE', 0x7023bf),
                     ('TRANSFER_TARGET', 0x54a3e8), ('CONTINUATION_1', 0x54a3e9),
                     ('CONTINUATION_2', 0x54a3eb), ('STARTUP_CALL', 0x54a40e)]
        return ''.join(f'GOD2_{name} pid=10 tid=20 base=00400000 pc={pc:08x}'
                       + (' target=0054a3e8' if name == 'TRANSFER_SOURCE' else '')
                       + f' time={100+index:x}\n' for index, (name, pc) in enumerate(locations))

    def test_native_marks_must_be_complete_and_same_thread(self):
        self.assertEqual(observed_marks(self.trace())['PACKER']['pid'], 16)
        for trace in (self.trace().replace('tid=20', 'tid=21', 1),
                      self.trace().replace('target=0054a3e8', 'target=0054a3e9'),
                      self.trace().replace('GOD2_TRANSFER_TARGET', 'MISSING')):
            with self.assertRaises(ValueError):
                observed_marks(trace)

    def test_native_bytes_are_parsed_not_guessed(self):
        row = ' '.join(f'{i:02x}' for i in range(16))
        native = f'0054a3e8  {row}\n0054a3f8  {row}\n'
        self.assertEqual(native_bytes(native, 0x54a3e8), bytes(range(16))*2)
        with self.assertRaises(ValueError):
            native_bytes(native, 0x54a3e9)

    def test_candidate_raw_mapping_preserves_code_and_flags(self):
        raw = synthetic_pe()
        mapped = bytearray(0x2000)
        mapped[:0x200] = raw[:0x200]
        mapped[0x1000:0x1200] = raw[0x200:]
        candidate, changes = mapped_to_candidate(bytes(mapped), 0x1010)
        with pefile.PE(data=candidate, fast_load=True) as pe:
            self.assertEqual(pe.OPTIONAL_HEADER.AddressOfEntryPoint, 0x1010)
            self.assertEqual(pe.sections[0].PointerToRawData, 0x1000)
            self.assertEqual(pe.sections[0].Characteristics, 0x60000020)
            self.assertEqual(pe.get_data(0x1000, 0x200), raw[0x200:])
        self.assertEqual(bytes(mapped)[0x1000:0x1200], raw[0x200:])
        self.assertFalse(changes['imports_repaired'])


class HostFirewallTests(unittest.TestCase):
    def fixture(self):
        return {'profiles': [{'enabled': 'True', 'local_rules': 'NotConfigured'} for _ in range(3)],
                'rules': [{'program': 'C:\\lab\\God2.exe', 'direction': d, 'action': 'Block',
                           'enabled': 'True', 'profile': 'Any', 'status': 'OK', 'enforcement': [1, 5]}
                          for d in ('Inbound', 'Outbound')]}

    def test_requires_effective_bidirectional_program_blocks(self):
        state = self.fixture()
        self.assertTrue(firewall_ready(state, ['C:\\lab\\God2.exe']))
        self.assertFalse(firewall_ready(state, ['C:\\other\\God2.exe']))
        state['rules'].pop()
        self.assertFalse(firewall_ready(state, ['C:\\lab\\God2.exe']))

    def test_allow_disabled_or_inactive_rule_cannot_pass(self):
        for key, value in [('action', 'Allow'), ('enabled', 'False'), ('profile', 'Private'),
                           ('status', 'Error'), ('enforcement', [5]), ('enforcement', [1, 16])]:
            state = self.fixture()
            state['rules'][0][key] = value
            self.assertFalse(firewall_ready(state, ['C:\\lab\\God2.exe']))

    def test_disabled_profiles_or_local_policy_rejection_blocks(self):
        for key, value in [('enabled', 'False'), ('local_rules', 'False')]:
            state = self.fixture()
            state['profiles'][0][key] = value
            self.assertFalse(firewall_ready(state, ['C:\\lab\\God2.exe']))


class EnvironmentTests(unittest.TestCase):
    def test_ready_requires_every_boolean_and_identity(self):
        report = {'status': 'RUNTIME_ENVIRONMENT_READY', 'tool_sha256': 'ab',
                  'checks': dict.fromkeys(CHECKS, True)}
        self.assertTrue(ready(report, 'AB'))
        self.assertFalse(ready(report, 'cd'))
        for name in CHECKS:
            for value in (False, None, 1, 'true'):
                report['checks'][name] = value
                self.assertFalse(ready(report, 'ab'))
            report['checks'][name] = True
        report['status'] = 'BLOCKED'
        self.assertFalse(ready(report, 'ab'))

    def test_bad_isolation_stops_before_copy_or_launch(self):
        class FakeSandbox:
            sandbox_id = 'fixture'
            calls = []
            def query(self, name, expression):
                self.calls.append(name)
                return {'non_loopback_addresses': ['192.0.2.1'], 'source_readonly': True,
                        'source_sha256': ARTIFACT}
        sandbox = FakeSandbox()
        report = probe(sandbox, {})
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertEqual(sandbox.calls, ['native-environment'])

    def test_policy_denial_is_not_runtime_evidence(self):
        class FakeSandbox:
            sandbox_id = 'fixture'
            def query(self, name, expression):
                raise RuntimeError('An Application Control policy has blocked this file')
        report = probe(FakeSandbox(), {})
        self.assertEqual(report['status'], 'BLOCKED_EXTERNAL_POLICY')
        self.assertFalse(ready(report, 'ab'))


if __name__ == '__main__':
    unittest.main()
