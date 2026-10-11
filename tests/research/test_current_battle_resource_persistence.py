import hashlib
import json
from pathlib import Path
import sqlite3
import struct
import unittest


class CurrentBattleResourcePersistence(unittest.TestCase):
    def test_terminal_disconnect_first_move_persists_and_restores(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        terminal=root/'native-second-exchange-resume-20260921-01'
        moved=root/'native-terminal-disconnect-move-20260923-01'
        restored=root/'native-terminal-disconnect-position-restore-20260923-01'
        terminal_evidence=json.loads((terminal/'run.json').read_text(encoding='utf-8'))
        move_evidence=json.loads((moved/'run.json').read_text(encoding='utf-8'))
        restore_evidence=json.loads((restored/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(move_evidence['result'],'NATIVE_MOVEMENT_ACK_APPLIED')
        self.assertIsNone(move_evidence.get('error'))
        self.assertNotEqual(move_evidence['world_loop_entry']['pid'],terminal_evidence['world_loop_entry']['pid'])
        self.assertEqual(move_evidence['terminal_restore_world_ready']['position_hex'],'110000000d000000')
        self.assertEqual(len(move_evidence['movement_steps']),1)
        step=move_evidence['movement_steps'][0]
        self.assertEqual(step['precondition'],{'position_hex':'110000000d000000','ring_hex':'010001'})
        self.assertEqual((step['ack_hex'],step['ack_token_after'],step['ring_after_ack']),('5d01','01','010102'))
        self.assertEqual(restore_evidence['result'],'NATIVE_SETTLED_BATTLE_POSITION_RESTORED')
        self.assertIsNone(restore_evidence.get('error'))
        self.assertNotEqual(restore_evidence['world_loop_entry']['pid'],move_evidence['world_loop_entry']['pid'])
        self.assertEqual(restore_evidence['restored_position_hex'],'120000000c000000')
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(restore_evidence['world_resource_update_return']['values_hex'])),(76,120,26,80))
        for evidence in (move_evidence,restore_evidence):
            for key in ('socket_battle_entry','socket_skill_commands','socket_outcome_entry'):
                self.assertNotIn(key,evidence)
        manifests=[json.loads((folder/'terminal-restore.json').read_text(encoding='utf-8'))
                   for folder in (moved,restored)]
        sources=(terminal/'diagnostic-accounts.db',moved/'diagnostic-accounts.db')
        self.assertIsNone(manifests[0]['position'])
        self.assertEqual(manifests[1]['position'],[1,2,15,18,12,1])
        for manifest,source in zip(manifests,sources):
            self.assertEqual(Path(manifest['source']).resolve(),source.resolve())
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),manifest['source_sha256'])
        databases=[sqlite3.connect((folder/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)
                   for folder in (terminal,moved,restored)]
        try:
            tables=[row[0] for row in databases[0].execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            for table in tables:
                quoted='"'+table.replace('"','""')+'"'
                rows=[database.execute('SELECT * FROM '+quoted).fetchall() for database in databases]
                if table=='recovered_positions':
                    self.assertEqual(rows,[[],[(1,2,15,18,12,1)],[(1,2,15,18,12,1)]])
                else:
                    self.assertEqual(rows[0],rows[1],table)
                    self.assertEqual(rows[1],rows[2],table)
            for database in databases:
                self.assertEqual(database.execute('PRAGMA integrity_check').fetchall(),[('ok',)])
                self.assertEqual(database.execute('SELECT total FROM character_experience').fetchall(),[(250,)])
                self.assertEqual(database.execute('SELECT count(*) FROM battle_settlements').fetchone()[0],1)
        finally:
            for database in databases:database.close()

    def test_terminal_disconnect_restores_world_without_reaward(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        source=root/'native-second-exchange-resume-20260921-01'
        run=root/'native-terminal-disconnect-restore-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        before=json.loads((source/'run.json').read_text(encoding='utf-8'))
        manifest=json.loads((run/'terminal-restore.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SETTLED_BATTLE_RESTORED_TO_WORLD')
        self.assertIsNone(evidence.get('error'))
        self.assertNotEqual(evidence['world_loop_entry']['pid'],before['world_loop_entry']['pid'])
        self.assertEqual(evidence['restored_position_hex'],'110000000d000000')
        for key in ('socket_battle_entry','socket_skill_commands','socket_outcome_entry'):
            self.assertNotIn(key,evidence)
        returned=evidence['world_resource_update_return']
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(returned['values_hex'])),(76,120,26,80))
        actor=bytes.fromhex(returned['role_snapshot_hex'])
        self.assertEqual(actor[0x26],2)
        self.assertEqual(int.from_bytes(actor[0x58:0x5a],'little'),1250)
        self.assertLess(evidence['world_resource_update_entry']['sequence'],returned['sequence'])
        database=source/'diagnostic-accounts.db'
        self.assertEqual(Path(manifest['source']).resolve(),database.resolve())
        self.assertEqual(hashlib.sha256(database.read_bytes()).hexdigest(),manifest['source_sha256'])
        original=sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)
        restored=sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)
        try:
            tables=[row[0] for row in original.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
            self.assertEqual(tables,[row[0] for row in restored.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")])
            for table in tables:
                quoted='"'+table.replace('"','""')+'"'
                self.assertTrue(original.execute('SELECT * FROM '+quoted).fetchall()==restored.execute('SELECT * FROM '+quoted).fetchall(),table)
            self.assertEqual(restored.execute('PRAGMA integrity_check').fetchall(),[('ok',)])
            self.assertEqual(restored.execute('SELECT count(*) FROM battle_settlements').fetchone()[0],1)
            self.assertEqual(restored.execute('SELECT total FROM character_experience').fetchall(),[(250,)])
            self.assertEqual(restored.execute('SELECT * FROM recovered_positions').fetchall(),[])
        finally:
            original.close();restored.close()

    def test_live_second_exchange_leaves_active_checkpoint_without_reward(self):
        run=Path(__file__).resolve().parents[2]/'artifacts/runs/native-second-exchange-pending-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SECOND_EXCHANGE_CHECKPOINT_CAPTURED')
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(len(evidence['socket_skill_commands']),2)
        self.assertEqual(len(evidence['animation_batch_completions']),4)
        for batch in evidence['animation_batch_completions']:
            self.assertEqual((batch['expected'],batch['completed'],batch['timeout_fallback']),(1,1,False))
        self.assertEqual(evidence['interrupted_checkpoint']['completed_exchanges'],2)
        self.assertNotIn('socket_outcome_entry',evidence)
        connection=sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)
        try:
            rows=connection.execute('SELECT document,resource_revision FROM battle_checkpoints').fetchall()
            self.assertEqual(len(rows),1)
            checkpoint=json.loads(rows[0][0])
            self.assertEqual((checkpoint['state'],checkpoint['revision'],checkpoint['winner'],rows[0][1]),('active',5,None,5))
            self.assertEqual(checkpoint['actors'][0],[0,1,76,120,34,80,31,40,8,10])
            self.assertEqual(checkpoint['actors'][14],[14,0,42,150,0,0,20,25,13,6])
            self.assertEqual(connection.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),[(76,120,34,80,5)])
            for table in ('battle_settlements','character_experience'):
                self.assertEqual(connection.execute('SELECT count(*) FROM '+table).fetchone()[0],0)
            role=connection.execute('SELECT logical,revision FROM character_role_snapshots').fetchone()
            self.assertEqual((role[0][1],role[1]),(1,1))
        finally:
            connection.close()

    def test_live_first_exchange_leaves_active_checkpoint_without_reward(self):
        run=Path(__file__).resolve().parents[2]/'artifacts/runs/native-player-pending-checkpoint-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_FIRST_EXCHANGE_CHECKPOINT_CAPTURED')
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(len(evidence['socket_skill_commands']),1)
        self.assertEqual(len(evidence['animation_batch_completions']),2)
        for batch in evidence['animation_batch_completions']:
            self.assertEqual((batch['expected'],batch['completed'],batch['timeout_fallback']),(1,1,False))
        self.assertEqual(evidence['interrupted_checkpoint']['battle_revision'],3)
        self.assertNotIn('socket_outcome_entry',evidence)
        connection=sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)
        try:
            rows=connection.execute('SELECT document,resource_revision FROM battle_checkpoints').fetchall()
            self.assertEqual(len(rows),1)
            checkpoint=json.loads(rows[0][0])
            self.assertEqual((checkpoint['state'],checkpoint['revision'],checkpoint['winner'],rows[0][1]),('active',3,None,4))
            self.assertEqual(checkpoint['actors'][0],[0,1,88,120,42,80,31,40,8,10])
            self.assertEqual(checkpoint['actors'][14][2],96)
            self.assertEqual(connection.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),[(88,120,42,80,4)])
            self.assertEqual(connection.execute('SELECT count(*) FROM battle_settlements').fetchone()[0],0)
            self.assertEqual(connection.execute('SELECT count(*) FROM character_experience').fetchone()[0],0)
            role=connection.execute('SELECT logical,revision FROM character_role_snapshots').fetchone()
            self.assertEqual((role[0][1],role[1]),(1,1))
        finally:
            connection.close()

    def test_live_durable_checkpoint_terminal_and_level_projection(self):
        run=Path(__file__).resolve().parents[2]/'artifacts/runs/native-player-durable-checkpoint-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        self.assertEqual([(v['level'],v['progress']) for v in evidence['role_level_returns']],[(1,0),(2,1250)])
        self.assertEqual(evidence['role_progress_bar_argument']['amount'],12)
        self.assertEqual(evidence['socket_character_exp_format_call']['amount'],250)
        self.assertEqual(len(evidence['socket_skill_commands']),3)
        self.assertEqual(len(evidence['animation_batch_completions']),5)
        for batch in evidence['animation_batch_completions']:
            self.assertEqual((batch['expected'],batch['completed'],batch['timeout_fallback']),(1,1,False))
        connection=sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)
        try:
            checkpoints=connection.execute('SELECT document,resource_revision,policy_id FROM battle_checkpoints').fetchall()
            self.assertEqual(len(checkpoints),1)
            document,revision,policy=checkpoints[0]
            state=json.loads(document)
            self.assertEqual((revision,policy,state['revision'],state['state'],state['winner']),
                             (6,'CUSTOM-0012/diagnostic-v1',6,'finished',0))
            self.assertEqual(state['actors'][0],[0,1,76,120,26,80,31,40,8,10])
            self.assertEqual(state['actors'][14][2],0)
            ledger=connection.execute('SELECT request,total_experience,resource_revision FROM battle_settlements').fetchall()
            self.assertEqual(len(ledger),1)
            request=json.loads(ledger[0][0])
            self.assertEqual((request['version'],ledger[0][1:]),(3,(250,6)))
            self.assertEqual(request['checkpoint']['after'],document)
            before=json.loads(request['checkpoint']['before'])
            self.assertEqual((before['revision'],before['actors'][14][2],before['actors'][0][4]),(5,42,34))
            self.assertNotEqual(before['rng'],state['rng'])
            self.assertEqual(connection.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),[(76,120,26,80,6)])
            self.assertEqual(connection.execute('SELECT total FROM character_experience').fetchall(),[(250,)])
            role=connection.execute('SELECT logical,revision FROM character_role_snapshots').fetchone()
            self.assertEqual((role[0][1],role[1]),(2,2))
            self.assertEqual(connection.execute('SELECT x,y,revision FROM recovered_positions').fetchall(),[(18,12,3)])
        finally:
            connection.close()

    def test_live_saved_level_restored_without_reawarding_or_healing(self):
        runs=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=runs/'native-player-level-restore-20260921-01'
        source=runs/'native-player-level-snapshot-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SAVED_POSITION_RESTORED')
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['restored_position_hex'],'120000000c000000')
        entry=evidence['world_resource_update_entry']
        returned=evidence['world_resource_update_return']
        self.assertLess(entry['sequence'],returned['sequence'])
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(returned['values_hex'])),(76,120,26,80))
        for record in (entry,returned):
            actor=bytes.fromhex(record['role_snapshot_hex'])
            self.assertEqual(actor[0x26],2)
            self.assertEqual(int.from_bytes(actor[0x58:0x5a],'little'),1250)
            self.assertEqual(struct.unpack_from('<4I',actor,0x78),(10,10,10,10))
            self.assertEqual(struct.unpack_from('<I',actor,0x60)[0],120)
            self.assertEqual(struct.unpack_from('<I',actor,0x68)[0],80)
        original=sqlite3.connect((source/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)
        restored=sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)
        try:
            for table in ('character_role_snapshots','character_resources','character_experience',
                          'battle_reservations','battle_settlements','recovered_positions'):
                self.assertEqual(restored.execute('SELECT * FROM '+table).fetchall(),
                                 original.execute('SELECT * FROM '+table).fetchall(),table)
        finally:
            original.close();restored.close()

    def test_live_atomic_level_snapshot_crosses_threshold_without_healing(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-player-level-snapshot-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        entries=evidence['role_level_entries'];returns=evidence['role_level_returns']
        self.assertEqual(len(entries),2)
        self.assertEqual([(r['level'],r['progress']) for r in returns],[(1,0),(2,1250)])
        for entry,returned in zip(entries,returns):
            self.assertEqual(returned['sp'],entry['sp']+8)
            self.assertLess(entry['global_sequence'],returned['global_sequence'])
            self.assertEqual(bytes.fromhex(returned['base_hex']),struct.pack('<4I',10,10,10,10))
        self.assertEqual(entries[0]['role'],entries[1]['role'])
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(returns[1]['resources_hex'])),(76,120,26,80))
        self.assertLess(returns[1]['global_sequence'],evidence['role_progress_entry']['global_sequence'])
        self.assertEqual(evidence['role_progress_bar_argument']['amount'],12)
        self.assertEqual(evidence['socket_character_exp_format_call']['amount'],250)
        self.assertEqual(len(evidence['socket_skill_commands']),3)
        self.assertEqual(len(evidence['animation_batch_completions']),5)
        for batch in evidence['animation_batch_completions']:
            self.assertEqual((batch['expected'],batch['completed'],batch['timeout_fallback']),(1,1,False))
        connection=sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)
        try:
            self.assertEqual(connection.execute('SELECT total,design_id FROM character_experience').fetchall(),[(250,'CUSTOM-0012')])
            self.assertEqual(connection.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),[(76,120,26,80,5)])
            roles=connection.execute('SELECT logical,revision,design_id FROM character_role_snapshots').fetchall()
            self.assertEqual(roles,[(b'\x22'+bytes.fromhex(entries[1]['body_hex']),2,'CUSTOM-0013')])
            ledger=connection.execute('SELECT request,total_experience,resource_revision FROM battle_settlements').fetchall()
            self.assertEqual(len(ledger),1)
            self.assertEqual(ledger[0][1:],(250,5))
            self.assertEqual(json.loads(ledger[0][0])['version'],2)
            self.assertEqual(connection.execute('SELECT x,y,revision FROM recovered_positions').fetchall(),[(18,12,3)])
        finally:
            connection.close()

    def test_live_committed_xp_lua_projection_is_not_fixed_sentinel(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-player-derived-progress-20260921-01'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        entry=evidence['role_progress_entry']
        returned=evidence['role_progress_return']
        self.assertEqual(bytes.fromhex(entry['body_hex']),struct.pack('<IIIIHH',76,0,26,0,1250,0))
        self.assertEqual(evidence['role_progress_bar_argument']['amount'],12)
        self.assertEqual(evidence['role_progress_bar_argument']['role_progress_hex'],'e204')
        self.assertEqual(bytes.fromhex(returned['after_hex'])[:2],struct.pack('<H',1250))
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(returned['after_hex'])[4:20]),(76,120,26,80))
        self.assertEqual(evidence['socket_character_exp_format_call']['amount'],25)
        self.assertEqual(len(evidence['socket_skill_commands']),3)
        self.assertEqual(len(evidence['animation_batch_completions']),5)
        connection=sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)
        try:
            self.assertEqual(connection.execute('SELECT total,design_id FROM character_experience').fetchall(),[(25,'CUSTOM-0012')])
            self.assertEqual(connection.execute('SELECT total_experience,resource_revision FROM battle_settlements').fetchall(),[(25,4)])
            self.assertEqual(connection.execute('SELECT x,y,revision FROM recovered_positions').fetchall(),[(18,12,3)])
        finally:
            connection.close()

    def test_live_role_progress_reaches_native_bar_and_preserves_resources(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-player-role-progress-20260921-02'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        entry = evidence['role_progress_entry']
        returned = evidence['role_progress_return']
        bar = evidence['role_progress_bar_argument']
        self.assertEqual(bytes.fromhex(entry['body_hex']), struct.pack('<IIIIHH',76,0,26,0,2500,0))
        after = bytes.fromhex(returned['after_hex'])
        self.assertEqual(int.from_bytes(after[:2],'little'),2500)
        self.assertEqual(struct.unpack('<4I',after[4:20]),(76,120,26,80))
        self.assertEqual(bar['amount'],25)
        self.assertEqual(bar['role_progress_hex'],'c409')
        self.assertLess(entry['sequence'],bar['sequence'])
        self.assertLess(bar['sequence'],returned['sequence'])
        self.assertEqual(evidence['socket_character_exp_format_call']['amount'],25)
        self.assertEqual(len(evidence['socket_skill_commands']),3)
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)
        try:
            self.assertEqual(connection.execute('SELECT total FROM character_experience').fetchall(),[(25,)])
            self.assertEqual(connection.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),
                             [(76,120,26,80,4)])
            self.assertEqual(connection.execute('SELECT x,y,revision FROM recovered_positions').fetchall(),[(18,12,3)])
        finally:
            connection.close()

    def test_live_test_award_matches_database_and_native_formatter(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-player-test-award-20260921-01'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        entry = evidence['socket_outcome_entry']
        expected = bytearray(57)
        expected[0] = 0x89
        struct.pack_into('<I', expected, 5, 25)
        self.assertEqual(bytes.fromhex(entry['logical_hex']), bytes(expected))
        formatted = evidence['socket_character_exp_format_call']
        self.assertEqual(formatted['amount'], 25)
        self.assertLess(entry['sequence'], formatted['sequence'])
        self.assertLess(formatted['sequence'], evidence['socket_outcome_return']['sequence'])
        self.assertEqual(len(evidence['socket_skill_commands']), 3)
        self.assertEqual(len(evidence['animation_batch_completions']), 5)
        for batch in evidence['animation_batch_completions']:
            self.assertEqual((batch['expected'], batch['completed'], batch['timeout_fallback']), (1,1,False))
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT total,design_id FROM character_experience').fetchall(),
                             [(25,'CUSTOM-0012')])
            rows = connection.execute('SELECT request,resource_revision,total_experience FROM battle_settlements').fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][1:], (4,25))
            request = json.loads(rows[0][0])
            self.assertEqual((request['experience'], request['won'], request['design_id']), (25,True,'CUSTOM-0012'))
            self.assertEqual(connection.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),
                             [(76,120,26,80,4)])
            self.assertEqual(connection.execute('SELECT x,y,revision FROM recovered_positions').fetchall(), [(18,12,3)])
        finally:
            connection.close()

    def test_live_atomic_terminal_ledger_and_world_return(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-player-atomic-settlement-20260921-01'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(len(evidence['socket_skill_commands']), 3)
        self.assertEqual(len(evidence['socket_skill_settlement']), 8)
        self.assertEqual(len(evidence['animation_batch_completions']), 5)
        for batch in evidence['animation_batch_completions']:
            self.assertEqual((batch['expected'], batch['completed'], batch['timeout_fallback']), (1, 1, False))
        self.assertEqual(evidence['movement_completion']['position_hex'], '120000000c000000')
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),
                             [(76,120,26,80,4)])
            self.assertEqual(connection.execute('SELECT character_id,total,design_id FROM character_experience').fetchall(),
                             [(1,0,'CUSTOM-0012')])
            rows = connection.execute('SELECT battle_id,request,resource_revision,total_experience,design_id FROM battle_settlements').fetchall()
            self.assertEqual(len(rows), 1)
            battle, request, revision, total, design = rows[0]
            self.assertEqual((battle, revision, total, design), (1,4,0,'CUSTOM-0012'))
            request = json.loads(request)
            self.assertEqual(request, {'version': 1, 'account': 1, 'character': 1, 'battle': 1,
                                      'before': [76,120,34,80,3,'CUSTOM-0012'],
                                      'after': [76,120,26,80,0,'CUSTOM-0012'],
                                      'won': True, 'experience': 0, 'design_id': 'CUSTOM-0012'})
            self.assertEqual(connection.execute('SELECT x,y,revision FROM recovered_positions').fetchall(), [(18,12,3)])
        finally:
            connection.close()

    def test_live_persisted_battle_identity_keeps_three_round_path(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-player-durable-battle-id-20260921-01'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(len(evidence['socket_skill_commands']), 3)
        self.assertEqual(len(evidence['animation_batch_completions']), 5)
        for batch in evidence['animation_batch_completions']:
            self.assertEqual((batch['expected'],batch['completed'],batch['timeout_fallback']), (1,1,False))
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT id,character_id,resource_revision,design_id FROM battle_reservations').fetchall(),
                             [(1,1,1,'CUSTOM-0012')])
            self.assertEqual(connection.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),
                             [(76,120,26,80,4)])
        finally:
            connection.close()

    def test_three_normal_power_skills_finish_and_persist(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-player-three-round-skill-finish-20260921-03'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(len(evidence['socket_skill_commands']), 3)
        records = evidence['socket_skill_settlement']
        self.assertEqual([(bytes.fromhex(r['logical_hex'])[1], bytes.fromhex(r['logical_hex'])[2]) for r in records],
                         [(1,0),(0,14),(0,0),(1,0),(0,14),(0,0),(1,0),(0,14)])
        enemy_hp = [int.from_bytes(bytes.fromhex(records[i]['actor_vitals_hex'])[:4], 'little') for i in (1,4,7)]
        self.assertEqual(enemy_hp, [96,42,0])
        self.assertEqual(struct.unpack('<4I', bytes.fromhex(records[6]['actor_vitals_hex'])), (76,26,120,80))
        self.assertEqual(len(evidence['animation_batch_completions']), 5)
        for batch in evidence['animation_batch_completions']:
            self.assertEqual((batch['expected'],batch['completed'],batch['timeout_fallback']), (1,1,False))
        self.assertEqual(evidence['movement_completion']['position_hex'], '120000000c000000')
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),
                             [(76,120,26,80,4)])
        finally:
            connection.close()

    def test_missing_resources_do_not_seed_or_block_world_movement(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-player-world-missing-resource-20260921-02'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        self.assertNotIn('world_resource_update_entry', evidence)
        self.assertNotIn('socket_battle_entry', evidence)
        self.assertEqual(evidence['movement_completion']['position_hex'], '120000000c000000')
        elapsed = evidence['movement_completion']['event']['timestamp'] - evidence['missing_resource_observation_started']
        self.assertGreaterEqual(elapsed, 5)
        log = (run / 'diagnostic-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_WORLD_RESOURCES_ABSENT'), 1)
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT * FROM character_resources').fetchall(), [])
            self.assertEqual(connection.execute('SELECT character_id,area,scene,x,y,revision FROM recovered_positions').fetchall(),
                             [(1, 2, 15, 18, 12, 3)])
        finally:
            connection.close()

    def test_world_sync_then_battle_preserves_one_resource_debit(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-player-world-battle-resource-chain-20260921-01'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP')
        self.assertIsNone(evidence.get('error'))
        loaded = evidence['world_resource_update_return']
        grant = evidence['world_resource_before_battle']
        final = evidence['world_resource_after_battle']
        self.assertEqual(struct.unpack('<4I', bytes.fromhex(loaded['values_hex'])), (76, 120, 34, 80))
        self.assertEqual(grant['hp_maxhp_mp_maxmp_hex'], loaded['values_hex'])
        self.assertEqual(struct.unpack('<4I', bytes.fromhex(final['hp_maxhp_mp_maxmp_hex'])), (76, 120, 26, 80))
        self.assertTrue(final['same_source'])
        self.assertEqual(evidence['world_resource_update_entry']['source'], final['source'])
        settled = evidence['socket_skill_terminal_vitals'][0]
        self.assertEqual(struct.unpack('<4I', bytes.fromhex(settled['actor_vitals_hex'])), (76, 26, 120, 80))
        self.assertEqual(len(evidence['socket_skill_commands']), 1)
        order = [loaded['sequence'], evidence['socket_battle_entry']['sequence'], grant['sequence'],
                 settled['sequence'], final['sequence']]
        self.assertEqual(order, sorted(set(order)))
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),
                             [(76, 120, 26, 80, 4)])
        finally:
            connection.close()

    def test_world_only_saved_resources_pass_native_consumer(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-player-world-resource-sync-20260921-02'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_SAVED_POSITION_RESTORED')
        self.assertIsNone(evidence.get('error'))
        self.assertNotIn('socket_battle_entry', evidence)
        initial = evidence['world_resource_at_entry']
        entry = evidence['world_resource_update_entry']
        returned = evidence['world_resource_update_return']
        self.assertEqual((entry['ui'], entry['source']), (initial['ui'], initial['source']))
        self.assertEqual(bytes.fromhex(entry['before_hex']), bytes(16))
        self.assertEqual(struct.unpack('<4I', bytes.fromhex(entry['body_hex'])), (100, 42, 120, 80))
        self.assertEqual(struct.unpack('<4I', bytes.fromhex(returned['values_hex'])), (100, 120, 42, 80))
        self.assertLess(initial['sequence'], entry['sequence'])
        self.assertLess(entry['sequence'], returned['sequence'])
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),
                             [(100, 120, 42, 80, 2)])
        finally:
            connection.close()

    def test_recorded_world_only_login_gap_is_not_resource_acceptance(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-player-world-only-resource-observe-20260921-01'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_SAVED_POSITION_RESTORED')
        self.assertNotIn('socket_battle_entry', evidence)
        self.assertEqual(bytes.fromhex(evidence['world_resource_at_entry']['hp_maxhp_mp_maxmp_hex']), bytes(16))
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),
                             [(100, 120, 42, 80, 2)])
        finally:
            connection.close()

    def test_native_battle_updates_retained_world_role_resources(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-player-world-resource-observe-20260921-01'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP')
        self.assertIsNone(evidence.get('error'))
        before = evidence['world_resource_before_battle']
        after = evidence['world_resource_after_battle']
        self.assertTrue(after['same_source'])
        self.assertEqual((before['ui'], before['source']), (after['ui'], after['source']))
        self.assertEqual(struct.unpack('<IIII', bytes.fromhex(before['hp_maxhp_mp_maxmp_hex'])),
                         (76, 120, 34, 80))
        self.assertEqual(struct.unpack('<IIII', bytes.fromhex(after['hp_maxhp_mp_maxmp_hex'])),
                         (76, 120, 26, 80))
        settled = evidence['socket_skill_terminal_vitals'][0]
        self.assertEqual(struct.unpack('<IIII', bytes.fromhex(settled['actor_vitals_hex'])),
                         (76, 26, 120, 80))
        self.assertLess(before['sequence'], settled['sequence'])
        self.assertLess(settled['sequence'], after['sequence'])
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),
                             [(76, 120, 26, 80, 4)])
        finally:
            connection.close()

    def test_damaged_hp_survives_fresh_connection(self):
        root = Path(__file__).resolve().parents[2] / 'artifacts/runs'
        saved = root / 'native-player-damaged-resource-save-20260921-01'
        restored = root / 'native-player-damaged-resource-restore-20260921-01'
        before = json.loads((saved / 'run.json').read_text(encoding='utf-8'))
        after = json.loads((restored / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(before['result'], 'NATIVE_SOCKET_SKILL_ANIMATIONS_COMPLETED')
        self.assertEqual(after['result'], 'NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP')
        self.assertIsNone(after.get('error'))
        self.assertEqual(len(before['socket_skill_rounds']), 2)
        self.assertEqual(struct.unpack('<IIII', bytes.fromhex(before['socket_skill_settlement'][-1]['actor_vitals_hex'])),
                         (76, 34, 120, 80))
        initial = after['socket_battle_vitals_entry']
        self.assertNotEqual(initial['pid'], before['socket_battle_vitals_entry']['pid'])
        self.assertEqual(struct.unpack_from('<II', bytes.fromhex(initial['logical_hex']), 5), (76, 34))
        settled = after['socket_skill_terminal_vitals'][0]
        self.assertEqual(struct.unpack('<IIII', bytes.fromhex(settled['actor_vitals_hex'])), (76, 26, 120, 80))
        self.assertLess(initial['sequence'], settled['sequence'])
        for evidence, count in ((before, 4), (after, 1)):
            self.assertEqual(len(evidence['animation_batch_completions']), count)
            for batch in evidence['animation_batch_completions']:
                self.assertEqual((batch['expected'], batch['completed'], batch['timeout_fallback']), (1, 1, False))
        for folder, mp, revision in ((saved, 34, 3), (restored, 26, 4)):
            connection = sqlite3.connect((folder / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
            try:
                self.assertEqual(connection.execute(
                    'SELECT character_id,hp,max_hp,mp,max_mp,revision,design_id FROM character_resources'
                ).fetchall(), [(1, 76, 120, mp, 80, revision, 'CUSTOM-0012')])
            finally:
                connection.close()

    def test_fresh_client_restores_then_spends_saved_mp(self):
        root = Path(__file__).resolve().parents[2] / 'artifacts/runs'
        source = root / 'native-player-skill-resource-save-20260921-01'
        target = root / 'native-player-skill-resource-restore-20260921-01'
        before = json.loads((source / 'run.json').read_text(encoding='utf-8'))
        evidence = json.loads((target / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_SAVED_POSITION_RESTORED')
        self.assertIsNone(evidence.get('error'))
        initial = evidence['socket_battle_vitals_entry']
        self.assertNotEqual(initial['pid'], before['socket_battle_vitals_entry']['pid'])
        logical = bytes.fromhex(initial['logical_hex'])
        self.assertEqual(struct.unpack_from('<II', logical, 5), (100, 42))
        records = evidence['socket_skill_terminal_vitals']
        self.assertEqual(len(records), 2)
        self.assertEqual(struct.unpack('<IIII', bytes.fromhex(records[0]['actor_vitals_hex'])),
                         (100, 34, 120, 80))
        self.assertLess(initial['sequence'], records[0]['sequence'])
        self.assertEqual(len(evidence['socket_skill_commands']), 1)
        batches = evidence['animation_batch_completions']
        self.assertEqual(len(batches), 1)
        self.assertEqual((batches[0]['expected'], batches[0]['completed'], batches[0]['timeout_fallback']),
                         (1, 1, False))
        self.assertEqual(evidence['restored_position_hex'], '120000000c000000')
        for folder, mp, revision in ((source, 42, 2), (target, 34, 3)):
            connection = sqlite3.connect((folder / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
            try:
                self.assertEqual(connection.execute(
                    'SELECT character_id,hp,max_hp,mp,max_mp,revision,design_id FROM character_resources'
                ).fetchall(), [(1, 100, 120, mp, 80, revision, 'CUSTOM-0012')])
            finally:
                connection.close()

    def test_live_terminal_skill_matches_disk_resources(self):
        root = Path(__file__).resolve().parents[2]
        run = root / 'artifacts/runs/native-player-skill-resource-save-20260921-01'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        config = json.loads((run / 'diagnostic-server-config.json').read_text(encoding='utf-8'))
        self.assertTrue(config['development']['diagnostic_battle_resources'])
        self.assertEqual(evidence['result'], 'NATIVE_MOVEMENT_PATH_COMPLETED')
        records = evidence['socket_skill_terminal_vitals']
        self.assertEqual(len(records), 2)
        self.assertEqual(bytes.fromhex(records[0]['logical_hex'])[:3], bytes((0x86, 1, 0)))
        self.assertEqual(struct.unpack('<IIII', bytes.fromhex(records[0]['actor_vitals_hex'])),
                         (100, 42, 120, 80))
        self.assertEqual(bytes.fromhex(records[1]['logical_hex'])[:3], bytes((0x86, 0, 14)))
        self.assertEqual(int.from_bytes(bytes.fromhex(records[1]['actor_vitals_hex'])[:4], 'little'), 0)
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute(
                'SELECT character_id,hp,max_hp,mp,max_mp,revision,design_id FROM character_resources'
            ).fetchall(), [(1, 100, 120, 42, 80, 2, 'CUSTOM-0012')])
            self.assertEqual(connection.execute(
                'SELECT character_id,area,scene,x,y,revision FROM recovered_positions'
            ).fetchall(), [(1, 2, 15, 18, 12, 3)])
        finally:
            connection.close()


class InterruptedResumeEvidence(unittest.TestCase):
    def test_movement_ring_restarts_after_battle_without_position_reset(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-movement-encounter-return-20260921-02'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        self.assertEqual([(s['step'], s['queue_sequence'], s['ack_hex']) for s in evidence['movement_steps']],
                         [(1, 1, '5d01'), (2, 1, '5d01'), (3, 2, '5d02')])
        done = evidence['movement_completion']
        self.assertEqual((done['position_hex'], done['ring_hex'], done['motion_state']),
                         ('120000000c000000', '010203', 0))
        self.assertLess(evidence['socket_post_battle_world_loop_entry']['global_sequence'],
                        done['event']['global_sequence'])
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT x,y,revision FROM recovered_positions').fetchall(), [(18, 12, 3)])
            self.assertEqual(connection.execute('SELECT hp,mp,revision FROM character_resources').fetchall(), [(76, 26, 6)])
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM battle_settlements').fetchone()[0], 1)
        finally:
            connection.close()

    def test_committed_movement_ack_precedes_encounter_and_world_return(self):
        run = Path(__file__).resolve().parents[2] / 'artifacts/runs/native-movement-encounter-20260921-01'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP')
        self.assertIsNone(evidence.get('error'))
        movement = evidence['pre_battle_movement']
        self.assertEqual((movement['ack_hex'], movement['ring_after_ack']), ('5d01', '010102'))
        self.assertLess(movement['ack_sequence'], evidence['socket_battle_entry']['global_sequence'])
        self.assertLess(evidence['socket_battle_entry']['global_sequence'],
                        evidence['socket_post_battle_world_loop_entry']['global_sequence'])
        self.assertEqual(movement['world'], evidence['socket_post_battle_world_loop_entry']['world'])
        self.assertEqual(len(evidence['socket_skill_commands']), 3)
        self.assertEqual(len(evidence['animation_batch_completions']), 5)
        for batch in evidence['animation_batch_completions']:
            self.assertEqual((batch['expected'], batch['completed'], batch['timeout_fallback']), (1, 1, False))
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT x,y,revision FROM recovered_positions').fetchall(), [(18, 12, 1)])
            self.assertEqual(connection.execute('SELECT hp,mp,revision FROM character_resources').fetchall(), [(76, 26, 6)])
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM battle_settlements').fetchone()[0], 1)
            self.assertEqual(connection.execute('SELECT * FROM character_experience').fetchall(), [(1, 250, 'CUSTOM-0012')])
        finally:
            connection.close()

    def test_resumed_and_uninterrupted_terminal_state_are_identical(self):
        root = Path(__file__).resolve().parents[2] / 'artifacts/runs'
        snapshots = []
        for name in ('native-player-durable-checkpoint-20260921-01',
                     'native-player-checkpoint-resume-20260921-02',
                     'native-second-exchange-resume-20260921-02'):
            connection = sqlite3.connect((root / name / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
            try:
                snapshots.append({table: connection.execute('SELECT '+
                                  ('battle_id,document,resource_revision,policy_id' if table=='battle_checkpoints' else '*')+
                                  ' FROM ' + table).fetchall()
                                  for table in ('battle_checkpoints', 'character_resources',
                                                'character_experience', 'character_role_snapshots',
                                                'battle_settlements', 'recovered_positions')})
                # Later revival migration adds a nullable, unrelated phase document.
                if name=='native-second-exchange-resume-20260921-02':
                    self.assertEqual(connection.execute('SELECT revival_document FROM battle_checkpoints').fetchall(),[(None,)])
            finally:
                connection.close()
        self.assertEqual(snapshots[0], snapshots[1])
        self.assertEqual(snapshots[0], snapshots[2])
        self.assertEqual(len(snapshots[0]['battle_checkpoints']), 1)
        self.assertEqual(len(snapshots[0]['battle_settlements']), 1)

    def test_second_exchange_fresh_resume_finishes_once_and_moves(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/'native-second-exchange-resume-20260921-02'
        source=root/'native-second-exchange-pending-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        before=json.loads((source/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        self.assertNotEqual(evidence['socket_battle_vitals_entry']['pid'],before['socket_battle_vitals_entry']['pid'])
        self.assertEqual(struct.unpack_from('<II',bytes.fromhex(evidence['socket_battle_vitals_entry']['logical_hex']),5),(76,34))
        self.assertEqual(int.from_bytes(bytes.fromhex(evidence['socket_actor_vitals'][1])[:4],'little'),42)
        self.assertEqual(len(evidence['socket_skill_commands']),1)
        self.assertEqual(len(evidence['socket_skill_settlement']),2)
        self.assertEqual(len(evidence['animation_batch_completions']),1)
        batch=evidence['animation_batch_completions'][0]
        self.assertEqual((batch['expected'],batch['completed'],batch['timeout_fallback']),(1,1,False))
        self.assertEqual([(x['level'],x['progress']) for x in evidence['role_level_returns']],[(1,0),(2,1250)])
        self.assertEqual(evidence['socket_character_exp_format_call']['amount'],250)
        self.assertEqual(evidence['movement_completion']['position_hex'],'120000000c000000')
        packets=[json.loads(path.read_text(encoding='utf-8')) for path in run.glob('packet-decode-*.json')]
        receipts=[p for p in packets if p.get('plain_frame_hex')=='140035000b0000000001000000000000000000c9']
        self.assertEqual(len(receipts),1)
        self.assertTrue(receipts[0]['client_plaintext_match'])
        self.assertTrue(receipts[0]['checksum_valid'])
        receipt=receipts[0]
        for kind in ('plain','wire'):
            raw=(run/'crypto-private'/Path(receipt[kind+'_file']).name).read_bytes()
            self.assertEqual(raw.hex(),receipt['plain_frame_hex' if kind=='plain' else 'wire_hex'])
            if kind=='plain':
                self.assertEqual(hashlib.sha256(raw).hexdigest(),receipt['client_plaintext_sha256'])
        skills=[p for p in packets if p.get('opcode')==0x35 and p.get('plain_frame_hex') and
                bytes.fromhex(p['plain_frame_hex'])[2:-1].hex()==evidence['socket_skill_commands'][0]['queued_logical_hex']]
        self.assertEqual(len(skills),1)
        self.assertEqual(skills[0]['socket'],receipt['socket'])
        self.assertLess(skills[0]['client_plaintext_entry_sequence'],batch['sequence'])
        self.assertGreater(receipt['client_plaintext_entry_sequence'],batch['sequence'])
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_FINISHED_BATTLE_RELEASED'),1)
        self.assertNotIn('policy or response rejected',log)
        connection=sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)
        try:
            self.assertEqual(connection.execute('SELECT hp,mp,revision FROM character_resources').fetchall(),[(76,26,6)])
            self.assertEqual(connection.execute('SELECT * FROM character_experience').fetchall(),[(1,250,'CUSTOM-0012')])
            self.assertEqual(connection.execute('SELECT count(*) FROM battle_settlements').fetchone()[0],1)
            self.assertEqual(connection.execute('SELECT x,y,revision FROM recovered_positions').fetchall(),[(18,12,3)])
        finally:
            connection.close()

    def test_fresh_resume_finishes_remaining_exchanges_and_moves(self):
        root = Path(__file__).resolve().parents[2] / 'artifacts/runs'
        source = root / 'native-player-pending-checkpoint-20260921-01'
        run = root / 'native-player-checkpoint-resume-20260921-02'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        before = json.loads((source / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        self.assertNotEqual(evidence['socket_battle_vitals_entry']['pid'],
                            before['socket_battle_vitals_entry']['pid'])
        self.assertEqual(struct.unpack_from('<II', bytes.fromhex(
            evidence['socket_battle_vitals_entry']['logical_hex']), 5), (88, 42))
        self.assertEqual(len(evidence['socket_skill_commands']), 2)
        self.assertEqual(len(evidence['socket_skill_settlement']), 5)
        batches = evidence['animation_batch_completions']
        self.assertEqual(len(batches), 3)
        for batch in batches:
            self.assertEqual((batch['expected'], batch['completed'], batch['timeout_fallback']), (1, 1, False))
        self.assertEqual([(x['level'], x['progress']) for x in evidence['role_level_returns']],
                         [(1, 0), (2, 1250)])
        connection = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(connection.execute('SELECT hp,mp,revision FROM character_resources').fetchall(), [(76, 26, 6)])
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM battle_settlements').fetchone()[0], 1)
            self.assertEqual(connection.execute('SELECT * FROM character_experience').fetchall(), [(1, 250, 'CUSTOM-0012')])
            self.assertEqual(connection.execute('SELECT x,y,revision FROM recovered_positions').fetchall(), [(18, 12, 3)])
            checkpoint = json.loads(connection.execute('SELECT document FROM battle_checkpoints').fetchone()[0])
            self.assertEqual((checkpoint['state'], checkpoint['revision'], checkpoint['winner']), ('finished', 6, 0))
            self.assertEqual(checkpoint['actors'][14][2], 0)
        finally:
            connection.close()

    def test_first_resume_exchange_is_durable_but_not_settled(self):
        root = Path(__file__).resolve().parents[2] / 'artifacts/runs'
        run = root / 'native-player-checkpoint-resume-20260921-01'
        source = root / 'native-player-pending-checkpoint-20260921-01'
        evidence = json.loads((run / 'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'EVENT_BUDGET_END')
        self.assertEqual(len(evidence['socket_skill_commands']), 1)
        self.assertEqual(len(evidence['socket_skill_settlement']), 3)
        receipt = json.loads((run / 'packet-decode-0383.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['client_plaintext_match'])
        self.assertTrue(receipt['checksum_valid'])
        self.assertEqual(receipt['plain_frame_hex'], '140035000b0000000001000000000000000000c9')
        for folder, hp, mp, resource_revision, battle_revision, enemy_hp in (
                (source, 88, 42, 4, 3, 96), (run, 76, 34, 5, 5, 42)):
            connection = sqlite3.connect((folder / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
            try:
                self.assertEqual(connection.execute('SELECT hp,mp,revision FROM character_resources').fetchall(),
                                 [(hp, mp, resource_revision)])
                self.assertEqual(connection.execute('SELECT COUNT(*) FROM battle_settlements').fetchone()[0], 0)
                checkpoint = json.loads(connection.execute('SELECT document FROM battle_checkpoints').fetchone()[0])
                self.assertEqual((checkpoint['state'], checkpoint['revision']), ('active', battle_revision))
                self.assertEqual(checkpoint['actors'][14][2], enemy_hp)
            finally:
                connection.close()


if __name__ == '__main__':
    unittest.main()
