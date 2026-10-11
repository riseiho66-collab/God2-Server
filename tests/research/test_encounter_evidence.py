import copy
import json
from pathlib import Path
import unittest

from tools.strike_lab.encounter_evidence import archive_first_encounter


class EncounterEvidenceTests(unittest.TestCase):
    def test_two_encounter_results_survive_fresh_login_without_mutation(self):
        import sqlite3
        import struct
        root = Path(__file__).resolve().parents[2] / 'artifacts/runs'
        source = root / 'native-two-encounters-20260921-03'
        target = root / 'native-two-encounters-relogin-20260921-01'
        before = json.loads((source / 'run.json').read_text(encoding='utf-8'))
        evidence = json.loads((target / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_SAVED_POSITION_RESTORED')
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['restored_position_hex'], '120000000c000000')
        self.assertNotEqual(before['world_initializer']['pid'], evidence['world_initializer']['pid'])
        entry = evidence['world_resource_update_entry']
        returned = evidence['world_resource_update_return']
        self.assertLess(entry['sequence'], returned['sequence'])
        self.assertEqual(struct.unpack('<4I', bytes.fromhex(returned['values_hex'])), (52,120,2,80))
        for record in (entry, returned):
            role = bytes.fromhex(record['role_snapshot_hex'])
            self.assertEqual(role[0x26], 2)
            self.assertEqual(int.from_bytes(role[0x58:0x5a], 'little'), 7500)
            self.assertEqual(struct.unpack_from('<4I', role, 0x78), (10,10,10,10))
        connections = [sqlite3.connect((p / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
                       for p in (source, target)]
        try:
            for table in ('character_role_snapshots', 'character_resources', 'character_experience',
                          'battle_checkpoints', 'battle_reservations', 'battle_settlements', 'recovered_positions'):
                self.assertEqual(connections[0].execute('SELECT * FROM '+table).fetchall(),
                                 connections[1].execute('SELECT * FROM '+table).fetchall(), table)
        finally:
            for connection in connections:
                connection.close()

    def test_two_complete_encounters_keep_resources_and_distinct_rewards(self):
        import sqlite3
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-two-encounters-20260921-03'
        result = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(result['result'], 'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(result.get('error'))
        self.assertEqual(len(result['completed_encounters']), 1)
        first = result['completed_encounters'][0]
        for encounter in (first, result):
            self.assertEqual(len(encounter['socket_skill_commands']), 3)
            self.assertEqual(len(encounter['animation_batch_completions']), 5)
            for batch in encounter['animation_batch_completions']:
                self.assertEqual((batch['expected'],batch['completed'],batch['timeout_fallback']), (1,1,False))
            self.assertEqual(encounter['socket_character_exp_format_call']['amount'], 250)
        self.assertEqual([(x['level'],x['progress']) for x in first['role_level_returns']], [(1,0),(2,1250)])
        self.assertEqual([(x['level'],x['progress']) for x in result['role_level_returns']], [(2,1250),(2,7500)])
        self.assertLess(first['socket_post_battle_world_loop_entry']['global_sequence'], result['socket_battle_entry']['global_sequence'])
        self.assertEqual(result['movement_completion']['motion_state'], 0)
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT hp,mp,revision FROM character_resources').fetchall(), [(52,2,10)])
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM battle_settlements').fetchone()[0], 2)
            self.assertEqual(connection.execute('SELECT * FROM character_experience').fetchall(), [(1,500,'CUSTOM-0012')])
            self.assertEqual(connection.execute('SELECT x,y,revision FROM recovered_positions').fetchall(), [(18,12,3)])
            checkpoints = [json.loads(x[0]) for x in connection.execute('SELECT document FROM battle_checkpoints ORDER BY battle_id')]
            self.assertEqual([(x['id'],x['state'],x['revision']) for x in checkpoints], [(1,'finished',6),(2,'finished',6)])
        finally:
            connection.close()

    def test_second_entry_failure_preserves_first_reward_and_resources(self):
        import sqlite3
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-two-encounters-20260921-02'
        result = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(result['result'], 'EVENT_BUDGET_END')
        self.assertEqual(len(result['completed_encounters']), 1)
        packet = json.loads((run / 'packet-decode-0791.json').read_text(encoding='utf-8'))
        self.assertTrue(packet['checksum_valid'] and packet['client_plaintext_match'])
        self.assertEqual(packet['plain_frame_hex'], '140035000b0000010000000000000000000000c9')
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT hp,mp,revision FROM character_resources').fetchall(), [(76,26,7)])
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM battle_settlements').fetchone()[0], 1)
            checkpoints = [json.loads(row[0]) for row in connection.execute('SELECT document FROM battle_checkpoints ORDER BY battle_id')]
            self.assertEqual([(x['id'],x['state'],x['revision']) for x in checkpoints], [(1,'finished',6),(2,'active',1)])
        finally:
            connection.close()

    def setUp(self):
        path = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-movement-encounter-return-20260921-02/run.json'
        self.result = json.loads(path.read_text(encoding='utf-8'))

    def test_real_first_encounter_rollover_preserves_world_and_independent_copy(self):
        before = copy.deepcopy(self.result)
        archived = archive_first_encounter(self.result)
        self.assertEqual(archived['socket_skill_commands'], before['socket_skill_commands'])
        self.assertNotIn('socket_skill_commands', self.result)
        self.assertEqual(self.result['movement_steps'], before['movement_steps'])
        self.assertEqual(self.result['world_initializer'], before['world_initializer'])
        self.result['socket_skill_commands'] = []
        self.assertEqual(len(archived['socket_skill_commands']), 3)
        with self.assertRaises(ValueError):
            archive_first_encounter(self.result)

    def test_partial_or_failed_completion_does_not_mutate_result(self):
        mutations = [lambda r: r.pop('role_progress_return'),
                     lambda r: r['socket_post_battle_world_loop_entry'].update(world=0),
                     lambda r: r['socket_post_battle_world_loop_entry'].update(global_sequence=0),
                     lambda r: r['role_level_returns'][-1].update(level=1),
                     lambda r: r['socket_skill_commands'].pop(),
                     lambda r: r['animation_batch_completions'][0].update(timeout_fallback=True),
                     lambda r: r['socket_character_exp_format_call'].update(amount=0)]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                result = copy.deepcopy(self.result)
                mutate(result)
                before = copy.deepcopy(result)
                with self.assertRaises(ValueError):
                    archive_first_encounter(result)
                self.assertEqual(result, before)


if __name__ == '__main__':
    unittest.main()
