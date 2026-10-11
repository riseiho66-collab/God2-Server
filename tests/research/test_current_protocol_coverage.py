"""Bounded pinned-native census and honest formal-route classification."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import current_protocol_coverage as coverage


class CurrentProtocolCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = coverage.qualified_image()
        cls.report = coverage.build_report()
        cls.catalog = cls.report['native_catalog']
        cls.rows = cls.catalog['rows']
        cls.contracts = {row['id']: row for row in cls.report['contracts']}

    def test_complete_native_table_and_byte_domain(self):
        self.assertEqual(self.catalog['table_entries'], 254)
        self.assertEqual(self.catalog['byte_domain_queries'], 256)
        self.assertEqual([row['opcode'] for row in self.rows], list(range(256)))
        self.assertEqual(sum(row['table_entry_rva'] is not None for row in self.rows), 254)
        self.assertEqual(self.catalog['counts'], {'FIXED': 230, 'VARIABLE_U16': 22, 'UNSUPPORTED': 4})
        for row in self.rows:
            opcode = row['opcode']
            with self.subTest(opcode=opcode):
                self.assertEqual(row['direction'], 'S2C_RECEIVE_QUERY')
                self.assertEqual(row['layer'], 'logical')
                self.assertIn(0x15840, row['trace_rvas'])
                self.assertIn(0x1000, row['trace_rvas'])
                self.assertIn(0x1200, row['trace_rvas'])
                self.assertIn(row['length_leaf_rva'], row['trace_rvas'])
                self.assertLess(len(row['trace_rvas']), 64)
                if opcode < 254:
                    table_target = struct.unpack_from('<I', self.raw, 0x1324 + 4 * opcode)[0]
                    self.assertEqual(table_target, coverage.BASE + row['length_leaf_rva'])
                else:
                    self.assertIsNone(row['table_entry_rva'])
                    self.assertEqual(row['length_leaf_rva'], 0x131e)

    def test_exact_variable_and_unsupported_sets(self):
        variable = {int(x, 16) for x in '19 20 5c 63 65 7a 98 a2 a7 ab af b0 b5 be cc d8 dc dd ee f3 fc fd'.split()}
        self.assertEqual({r['opcode'] for r in self.rows if r['native_return'] == -2}, variable)
        self.assertEqual({r['opcode'] for r in self.rows if r['native_return'] == -1}, {0x21, 0x25, 0xfe, 0xff})

    def test_full_u32_wrapper_masks_to_low_byte(self):
        native = coverage.NativeLengths(self.raw)
        for opcode in range(256):
            for high in (0x100, 0xffffff00):
                result, _ = native.query(high | opcode)
                self.assertEqual(result, self.rows[opcode]['native_return'])
        for value in (-1, 0x100000000, True, '85'):
            with self.assertRaises(ValueError):
                native.query(value)

    def test_variable_total_length_guard_is_not_acceptance(self):
        guards = {probe['word']: probe for probe in self.catalog['variable_guard_probes']}
        for value in (0, 1, 2, 3):
            self.assertEqual(guards[value]['result'], 'BUFFERED_COUNT_SATISFIED')
        for value in (27, 2559):
            self.assertEqual(guards[value]['result'], 'NEEDS_BODY_BYTE')
        self.assertEqual(guards[2560]['result'], 'LIMIT_BRANCH')
        for value in (2561, 65535):
            self.assertEqual(guards[value]['result'], 'ASSERTION_BOUNDARY')
            self.assertNotIn(0x2c70, guards[value]['trace_rvas'])
        self.assertIn('short lengths are not certified valid', self.catalog['variable_scope'])

    def test_direction_collisions_cannot_share_length_contract(self):
        for opcode, received, produced in ((0x85, 2, 7), (0x25, -1, 5),
                                          (0x35, 4, 17), (0x2e, 5, 7), (0x30, 19, 2)):
            self.assertEqual(self.rows[opcode]['native_return'], received)
            producer = next(row for row in self.report['native_producers'] if row['opcode'] == opcode)
            self.assertEqual(producer['logical_size'], produced)
            self.assertEqual(producer['direction'], 'C2S')
            self.assertNotEqual(received, produced)
        self.assertEqual(self.report['frame_distinction']['logical_opcode'], None)
        self.assertEqual(self.report['frame_distinction']['implemented_logical_opcodes'], [0, 4])
        self.assertEqual(self.rows[2]['logical_size'], 23)

    def test_world_default_does_not_erase_battle_consumers(self):
        for key, opcode, target in (('skill_bank_state', 0x38, 0x114525),
                                   ('skill_identity', 0x87, 0x114518),
                                   ('battle_experience', 0x89, 0x114582)):
            self.assertTrue(self.rows[opcode]['world_default'])
            self.assertEqual(self.contracts[key]['battle_dispatch_rva'], target)
            self.assertEqual(self.contracts[key]['direction'], 'S2C')
            self.assertEqual(self.contracts[key]['status'], 'CODEC_ONLY')
        for opcode, target in ((0x72, 0x6a68b), (0x7a, 0x6abd7), (0xdb, 0x6b44e),
                               (0x3b, 0x6a029), (0x41, 0x6a04d), (0x31, 0x69fa9)):
            self.assertEqual(self.rows[opcode]['world_dispatch_rva'], target)

    def test_quest85_transport_is_not_an_authoritative_gameplay_route(self):
        probe = self.report['quest_native_probe']
        self.assertEqual(probe['appended_hex'], '85341202009aa5')
        self.assertEqual(probe['queued_bytes'], 7)
        self.assertEqual(probe['stop_rva'], 0xc8350)
        self.assertEqual(probe['acceptance_kind'], 'bounded_native')
        quest = self.contracts['quest_request']
        self.assertEqual(quest['status'], 'TRANSPORT_ROUTE')
        self.assertFalse(quest['application_policy_installed'])
        self.assertEqual(quest['logical_size'], 7)
        self.assertIn('stack storage', quest['evidence'])
        self.assertTrue(any('Recovered world handler unavailable' in a['text']
                            for a in quest['transport_anchors']))

    def test_codec_route_and_client_acceptance_are_distinct(self):
        classify = coverage.coverage_status
        self.assertEqual(classify(codec=True, acceptance_kind='bounded_native'), 'CODEC_ONLY')
        self.assertEqual(classify(codec=True, transport_route=True), 'TRANSPORT_ROUTE')
        self.assertEqual(classify(codec=True, runtime_route=True, acceptance_kind='bounded_native'), 'RUNTIME_ROUTE')
        self.assertEqual(classify(runtime_route=True, acceptance_kind='live_current_client'), 'CLIENT_ACCEPTED')
        with self.assertRaises(ValueError):
            classify(codec=True, acceptance_kind='live_current_client')
        with self.assertRaises(ValueError):
            classify(codec=True, transport_route=True, acceptance_kind='live_current_client')
        self.assertEqual(self.report['contract_status_counts'],
                         {'CODEC_ONLY': 11, 'NATIVE_ONLY': 1, 'RUNTIME_ROUTE': 3, 'TRANSPORT_ROUTE': 6})
        self.assertEqual({key for key, row in self.contracts.items() if row['status'] == 'RUNTIME_ROUTE'},
                         {'movement_request', 'periodic_tick', 'movement_ack'})
        for row in self.contracts.values():
            self.assertEqual(row['client_acceptance'], {'status': 'UNKNOWN', 'evidence': None})
        self.assertFalse(self.report['original_rules_complete'])
        self.assertFalse(self.report['all_original_packets_wired'])

    def test_close_route_preserves_native_sequence_uncertainty(self):
        bulk = self.contracts['battle_vitals_batch']
        self.assertEqual((bulk['direction'], bulk['opcode'], bulk['logical_size']), ('S2C', 0x88, 121))
        self.assertEqual(bulk['status'], 'CODEC_ONLY')
        self.assertEqual(bulk['battle_dispatch_rva'], 0x114538)
        self.assertEqual(bulk['runtime_references'], [])
        vitals = self.contracts['battle_vitals']
        self.assertEqual((vitals['direction'], vitals['opcode'], vitals['logical_size']), ('S2C', 0x86, 17))
        self.assertEqual(vitals['status'], 'CODEC_ONLY')
        self.assertEqual(vitals['runtime_references'], [])
        self.assertIn('enemy MP not applied', vitals['state'])
        result = self.contracts['battle_result_flags']
        self.assertEqual((result['direction'], result['opcode'], result['logical_size']), ('S2C', 0x86, 17))
        self.assertEqual(result['status'], 'CODEC_ONLY')
        self.assertEqual(result['battle_dispatch_rva'], 0x114464)
        self.assertEqual(result['runtime_references'], [])
        close = self.contracts['quest_close_request']
        self.assertEqual((close['opcode'], close['logical_size']), (0x86, 5))
        self.assertEqual(close['status'], 'TRANSPORT_ROUTE')
        self.assertFalse(close['application_policy_installed'])
        probe = self.report['quest_close_native_probe']
        self.assertEqual(probe['acceptance_kind'], 'bounded_native')
        self.assertFalse(probe['requires_85_then_86'])
        self.assertEqual(probe['sequences'], ['85341202009aa5', '86efbe0010',
                         '86efbe001085341202009a84', '85341203009aa585341202009a84'])

    def test_runtime_routes_have_callsite_and_state_anchors(self):
        anchors = self.contracts['movement_request']['route_anchors']
        for fragment in ('WorldTailAccepted', 'RecoveredWorldRecords::parse_frame', 'game_handlers.movement',
                         'recovered_movement->move', 'RecoveredMovement::ack', 'config.recovered_dual_connection'):
            self.assertTrue(any(fragment in anchor['text'] for anchor in anchors), fragment)
        for key in ('npc_record', 'quest_journal', 'instance_update', 'inventory_projection',
                    'battle_experience', 'inventory_request'):
            self.assertEqual(self.contracts[key]['runtime_references'], [])
        skill = self.contracts['skill_request']
        self.assertEqual(skill['status'], 'TRANSPORT_ROUTE')
        self.assertFalse(skill['application_policy_installed'])
        self.assertTrue(skill['runtime_sequence_assembly'])
        self.assertTrue(any('InBattle' in a['text'] for a in skill['transport_anchors']))
        self.assertEqual({ref['path'] for ref in skill['runtime_references']}, {'src/net/Session.cpp'})
        attack = self.contracts['basic_attack_request']
        self.assertEqual(attack['status'], 'TRANSPORT_ROUTE')
        self.assertFalse(attack['application_policy_installed'])
        self.assertTrue(any('InBattle' in anchor['text'] for anchor in attack['transport_anchors']))
        self.assertEqual({ref['path'] for ref in attack['runtime_references']}, {'src/net/Session.cpp'})
        control = self.contracts['battle_control_request']
        self.assertEqual(control['status'], 'TRANSPORT_ROUTE')
        self.assertFalse(control['application_policy_installed'])
        self.assertTrue(any('parse_control_logical' in a['text'] for a in control['transport_anchors']))
        self.assertTrue(any('ControlRequest' in a['text'] for a in control['transport_anchors']))
        self.assertTrue(any('InBattle' in a['text'] for a in control['transport_anchors']))
        self.assertEqual({ref['path'] for ref in control['runtime_references']}, {'src/net/Session.cpp'})

    def test_source_drift_cannot_silently_claim_old_gaps(self):
        files = coverage.source_snapshot()
        changed = copy.deepcopy(files)
        changed['src/net/Session.cpp']['sha256'] = '0' * 64
        with self.assertRaisesRegex(AssertionError, 'route snapshot changed'):
            coverage.formal_contracts(self.raw, changed)
        changed = copy.deepcopy(files)
        changed['src/protocol/RecoveredMovement.h']['text'] += '\nif(decoded[i]==0x85) {}\n'
        with self.assertRaisesRegex(AssertionError, 'dispatcher changed'):
            coverage.formal_contracts(self.raw, changed)
        changed = copy.deepcopy(files)
        changed['src/protocol/RecoveredWorldRecords.h']['text'] += '\ncase 0x35:\n'
        with self.assertRaisesRegex(AssertionError, 'dispatcher changed'):
            coverage.formal_contracts(self.raw, changed)
        changed = copy.deepcopy(files)
        changed['src/core/Application.cpp']['text'] += '\ngame_handlers.world_records = policy;\n'
        with self.assertRaisesRegex(AssertionError, 'Application acquired'):
            coverage.formal_contracts(self.raw, changed)
        changed = copy.deepcopy(files)
        changed['src/handlers/RecoveredMovementService.cpp']['text'] += '\nRecoveredQuestSync::decode(record);\n'
        with self.assertRaisesRegex(AssertionError, 'acquired runtime references'):
            coverage.formal_contracts(self.raw, changed)
        with self.assertRaisesRegex(AssertionError, 'anchor changed'):
            coverage.source_anchor(files, 'src/net/Session.cpp', 'missing_contract_anchor_85')

    def test_image_pin_rejects_altered_image(self):
        with self.assertRaisesRegex(ValueError, 'image mismatch'):
            coverage.NativeLengths(bytes([self.raw[0] ^ 1]) + self.raw[1:])

    def test_cli_stdout_is_complete_json_without_live_completion(self):
        result = subprocess.run([sys.executable, '-B', 'tools/strike_lab/current_protocol_coverage.py', '--json'],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['schema'], 'current-protocol-coverage-v1')
        self.assertEqual(len(report['native_catalog']['rows']), 256)
        self.assertFalse(report['all_original_packets_wired'])
        self.assertTrue(report['source_snapshot'])


if __name__ == '__main__':
    unittest.main()
