"""Saved own-server revival diagnostics; not general UI/reconnect acceptance."""
import json
from pathlib import Path
import struct
import subprocess
import sqlite3
import unittest


ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT/'artifacts/runs/native-revival-bootstrap-20260921-01'


class RevivalLiveBootstrapTests(unittest.TestCase):
    def test_settled_relogin_restores_native_position_and_resources_without_replay(self):
        source=ROOT/'artifacts/runs/native-revival-postbattle-move-20260921-01'
        run=ROOT/'artifacts/runs/native-revival-settled-relogin-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SAVED_POSITION_RESTORED')
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['restored_position_hex'],'120000000c000000')
        projected=evidence['world_resource_update_return']
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(projected['values_hex'])),(100,120,14,80))
        self.assertGreater(projected['sequence'],evidence['world_resource_update_entry']['sequence'])
        self.assertNotIn('revival_followup_damage',evidence)
        with sqlite3.connect((source/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as before, \
             sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as after:
            for query in (
                    'SELECT character_id,area,scene,x,y,revision FROM recovered_positions',
                    'SELECT character_id,hp,max_hp,mp,max_mp,revision,design_id FROM character_resources',
                    'SELECT battle_id,document,resource_revision,policy_id,revival_document FROM battle_checkpoints',
                    'SELECT battle_id,request,resource_revision,total_experience,design_id FROM battle_settlements'):
                self.assertEqual(before.execute(query).fetchall(),after.execute(query).fetchall())
            self.assertEqual(after.execute('SELECT count(*) FROM battle_settlements').fetchone()[0],1)
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertNotIn('DIAGNOSTIC_BATTLE_TRANSITION_SENT',log)
        self.assertNotIn('DIAGNOSTIC_FINISHED_BATTLE_RELEASED',log)
        self.assertNotIn('policy or response rejected',log)

    def test_post_revival_terminal_world_movement_is_persisted(self):
        run=ROOT/'artifacts/runs/native-revival-postbattle-move-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        completion=evidence['movement_completion']
        self.assertEqual((completion['position_hex'],completion['ring_hex'],completion['motion_state']),
                         ('120000000c000000','010304',0))
        self.assertEqual([s['ack_hex'] for s in evidence['movement_steps']],['5d01','5d02','5d03'])
        self.assertLess(evidence['socket_battle_loop_return']['sequence'],
                        evidence['socket_post_battle_world_loop_entry']['sequence'])
        self.assertLess(evidence['socket_post_battle_world_loop_entry']['sequence'],completion['event']['sequence'])
        with sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as db:
            self.assertEqual(db.execute('SELECT character_id,area,scene,x,y,revision FROM recovered_positions').fetchall(),
                             [(1,2,15,18,12,3)])
            self.assertEqual(db.execute('SELECT hp,mp,revision FROM character_resources').fetchall(),[(100,14,10)])
            self.assertEqual(db.execute('SELECT resource_revision,total_experience FROM battle_settlements').fetchall(),[(10,0)])
            document,revision,phase=db.execute('SELECT document,resource_revision,revival_document FROM battle_checkpoints').fetchone()
            self.assertEqual((json.loads(document)['state'],revision,phase),('finished',10,None))
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        after=log.split('DIAGNOSTIC_FINISHED_BATTLE_RELEASED',1)[1]
        self.assertEqual(after.count('DIAGNOSTIC_PLAYER_RECORD type_index=0\n'),3)
        self.assertEqual(after.count('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=5'),3)
        self.assertNotIn('accepted=false',log)
        self.assertNotIn('policy or response rejected',log)

    def test_resumed_terminal_settlement_returns_to_native_world_loop(self):
        run=ROOT/'artifacts/runs/native-revival-terminal-resume-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP')
        self.assertIsNone(evidence.get('error'))
        names=('revival_followup_damage','revival_followup_animation_return','socket_outcome_entry',
               'socket_outcome_return','socket_outcome_panel_entry','socket_outcome_panel_return',
               'socket_battle_cleanup_entry','socket_battle_loop_return','socket_post_battle_world_loop_entry')
        sequences=[evidence[name]['sequence'] for name in names]
        self.assertEqual(sequences,sorted(set(sequences)))
        self.assertEqual(evidence['socket_outcome_return']['result_received'],1)
        self.assertEqual(evidence['socket_outcome_panel_return']['panel_latch'],1)
        batch=evidence['animation_batch_completions']
        self.assertEqual(len(batch),1)
        self.assertEqual((batch[0]['expected'],batch[0]['completed']),(1,1))
        self.assertFalse(batch[0]['timeout_fallback'])
        actors=evidence['revival_followup_damage']['actors']
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(actors[2]['vitals_hex']))[0],0)
        with sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as db:
            document,revision,phase=db.execute('SELECT document,resource_revision,revival_document FROM battle_checkpoints').fetchone()
            state=json.loads(document)
            self.assertEqual((state['state'],state['revision'],revision),('finished',9,10))
            self.assertEqual(state['actors'][14][2],0)
            self.assertIsNone(phase)
            self.assertEqual(db.execute('SELECT hp,mp,revision FROM character_resources').fetchall(),[(100,14,10)])
            self.assertEqual(db.execute('SELECT resource_revision,total_experience,design_id FROM battle_settlements').fetchall(),[(10,0,'CUSTOM-0012')])
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_FINISHED_BATTLE_RELEASED'),1)
        self.assertNotIn('accepted=false',log)
        self.assertNotIn('policy or response rejected',log)

    def test_two_continuous_resumed_rounds(self):
        run=ROOT/'artifacts/runs/native-revival-two-round-resume-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        rounds=evidence['revival_resumed_rounds']
        self.assertEqual(len(rounds),2)
        self.assertEqual(len(evidence['animation_batch_completions']),2)
        for turn,hp,batch in zip(rounds,(78,60),evidence['animation_batch_completions']):
            self.assertEqual((batch['expected'],batch['completed']),(1,1))
            self.assertFalse(batch['timeout_fallback'])
            self.assertLess(batch['elapsed_ms'],10000)
            actors=turn['damage']['actors']
            values=[struct.unpack('<4I',bytes.fromhex(actor['vitals_hex'])) for actor in actors]
            self.assertEqual(values[0],(100,14,120,80))
            self.assertEqual(values[1],(1,5,120,20))
            self.assertEqual((values[2][0],values[2][2]),(hp,150))
            self.assertLess(turn['command']['sequence'],turn['damage']['sequence'])
            self.assertLess(turn['damage']['sequence'],batch['sequence'])
            self.assertLess(batch['sequence'],turn['animation_return']['sequence'])
        self.assertLess(rounds[0]['animation_return']['sequence'],rounds[1]['command']['sequence'])
        with sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as db:
            self.assertEqual(db.execute('SELECT hp,mp,revision FROM character_resources').fetchall(),[(100,14,9)])
            document,revision,phase_document=db.execute('SELECT document,resource_revision,revival_document FROM battle_checkpoints').fetchone()
            state=json.loads(document);phase=json.loads(phase_document)
            self.assertEqual((state['revision'],revision,state['actors'][14][2]),(8,9,60))
            self.assertEqual(phase['battle'],document)
            self.assertTrue(phase['action'] and phase['control'])
            self.assertEqual(db.execute('SELECT count(*) FROM battle_settlements').fetchone()[0],0)
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertNotIn('accepted=false',log)
        self.assertNotIn('policy or response rejected',log)
        self.assertEqual(log.count('DIAGNOSTIC_REVIVAL_RESUME_REARMED'),1)
        self.assertEqual(log.count('DIAGNOSTIC_NEXT_ROUND_GRANTED'),1)
        self.assertEqual(log.count('accepted=true bytes=156'),2)
        packets=[json.loads(path.read_text(encoding='utf-8')) for path in sorted(run.glob('packet-decode-*.json'))]
        receipts=[p for p in packets if p.get('plain_frame_hex','').startswith('140035000b')]
        self.assertEqual([p['plain_frame_hex'] for p in receipts],[
            '140035000b0000000000000000000000000000c8',
            '140035000b0000000001000000000000000000c9',
            '140035000b0000010000000000000000000000c9'])
        self.assertTrue(all(p['client_plaintext_match'] and p['checksum_valid'] for p in receipts))

    def test_fresh_resume_basic_animation_and_durable_receipt(self):
        for name,receipt_ok,battle_revision,enemy_hp in (
                ('native-revival-resume-action-20260921-01',False,5,114),
                ('native-revival-resume-action-20260921-02',True,5,114),
                ('native-revival-repeat-resume-20260921-01',True,6,96)):
            with self.subTest(run=name):
                run=ROOT/'artifacts/runs'/name
                evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
                self.assertIsNone(evidence.get('error'))
                self.assertTrue(evidence['revival_restored_participants_observed'])
                self.assertTrue(evidence['revival_followup_receipt_observation'])
                batches=evidence['animation_batch_completions']
                self.assertEqual(len(batches),1)
                self.assertEqual((batches[0]['expected'],batches[0]['completed']),(1,1))
                self.assertFalse(batches[0]['timeout_fallback'])
                self.assertLess(batches[0]['elapsed_ms'],10000)
                actors=evidence['revival_followup_damage']['actors']
                vitals=[struct.unpack('<4I',bytes.fromhex(a['vitals_hex'])) for a in actors]
                self.assertEqual(vitals[0],(100,14,120,80))
                self.assertEqual(vitals[1],(1,5,120,20))
                self.assertEqual((vitals[2][0],vitals[2][2]),(enemy_hp,150))
                initial=evidence['revival_actor_states'][2]
                self.assertEqual(struct.unpack('<4I',bytes.fromhex(initial['vitals_hex']))[0],enemy_hp+18)
                with sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as db:
                    self.assertEqual(db.execute('SELECT hp,mp,revision FROM character_resources').fetchall(),[(100,14,battle_revision+1)])
                    rows=db.execute('SELECT document,resource_revision,revival_document FROM battle_checkpoints').fetchall()
                    self.assertEqual(len(rows),1)
                    document,revision,phase_document=rows[0]
                    state=json.loads(document);phase=json.loads(phase_document)
                    self.assertEqual((state['revision'],revision),(battle_revision,battle_revision+1))
                    self.assertEqual(state['actors'][14][2],enemy_hp)
                    self.assertEqual(phase['battle'],document)
                    self.assertTrue(phase['action'])
                    self.assertEqual(phase['control'],receipt_ok)
                    self.assertEqual(db.execute('SELECT count(*) FROM battle_settlements').fetchone()[0],0)
                log=(run/'cpp-server.log').read_text(encoding='utf-8')
                self.assertEqual(log.count('DIAGNOSTIC_REVIVAL_RESUME_REARMED'),1)
                self.assertEqual(log.count('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=156'),1)
                self.assertNotIn('accepted=true bytes=173',log)
                after=log.split('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=156',1)[1]
                self.assertEqual('policy or response rejected' in after,not receipt_ok)
                if receipt_ok:
                    self.assertGreaterEqual(after.count('DIAGNOSTIC_PLAYER_RECORD type_index=1\n'),3)
                    self.assertIn('DIAGNOSTIC_TIMER36_ACCEPTED',after)
                packets=[json.loads(p.read_text(encoding='utf-8')) for p in run.glob('packet-decode-*.json')]
                receipts=[p for p in packets if p.get('plain_frame_hex')=='140035000b0000000001000000000000000000c9']
                self.assertEqual(len(receipts),1)
                self.assertTrue(receipts[0]['checksum_valid'] and receipts[0]['client_plaintext_match'])

    def test_restore_opening_accepted_then_heartbeats_continue_without_mutation(self):
        run=ROOT/'artifacts/runs/native-revival-restore-20260921-03'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertTrue(evidence['revival_restored_participants_observed'])
        self.assertIsNone(evidence.get('error'))
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        after=log.split('DIAGNOSTIC_PLAYER_RECORD type_index=11',1)[1]
        self.assertIn('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=0',after)
        self.assertGreaterEqual(after.count('DIAGNOSTIC_PLAYER_RECORD type_index=1\n'),3)
        self.assertIn('DIAGNOSTIC_TIMER36_ACCEPTED',after)
        self.assertNotIn('accepted=false',log)
        self.assertNotIn('policy or response rejected',log)
        self.assertNotIn('DIAGNOSTIC_NEXT_ROUND_GRANTED',log)
        packets=[json.loads(path.read_text(encoding='utf-8')) for path in run.glob('packet-decode-*.json')]
        opening=[p for p in packets if p.get('plain_frame_hex')=='14003500020000010000000000000000000000c0']
        self.assertEqual(len(opening),1)
        self.assertTrue(opening[0]['checksum_valid'] and opening[0]['client_plaintext_match'])
        source=ROOT/'artifacts/runs/native-revival-durable-20260921-01/diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as before, \
             sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as after_db:
            for query in ('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources',
                          'SELECT document,resource_revision,revival_document FROM battle_checkpoints'):
                self.assertEqual(before.execute(query).fetchall(),after_db.execute(query).fetchall())

    def test_restore_initial_notice_passes_but_opening_action_still_rejects(self):
        run=ROOT/'artifacts/runs/native-revival-restore-20260921-02'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertIsNone(evidence.get('error'))
        self.assertTrue(evidence['revival_restored_participants_observed'])
        actors=evidence['revival_actor_states']
        self.assertEqual([actor['slot'] for actor in actors],[0,1,14])
        vitals=[struct.unpack('<4I',bytes.fromhex(actor['vitals_hex'])) for actor in actors]
        self.assertEqual(vitals[0],(100,14,120,80))
        self.assertEqual(vitals[1],(1,5,120,20))
        self.assertEqual((vitals[2][0],vitals[2][2]),(132,150))
        for sequence,plain in ((323,'140035000b0000000000000000000000000000c8'),
                               (347,'14003500020000010000000000000000000000c0')):
            packet=json.loads((run/f'packet-decode-{sequence:04d}.json').read_text(encoding='utf-8'))
            self.assertTrue(packet['checksum_valid'] and packet['client_plaintext_match'])
            self.assertEqual(packet['plain_frame_hex'],plain)
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        initial=log.split('DIAGNOSTIC_PLAYER_RECORD type_index=7',1)[1]
        self.assertIn('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=0',initial)
        opening=initial.split('DIAGNOSTIC_PLAYER_RECORD type_index=11',1)[1]
        self.assertIn('DIAGNOSTIC_PLAYER_REPLY accepted=false bytes=0',opening)
        self.assertIn('closing: Recovered world policy or response rejected',opening)
        # This is preserved negative evidence, not reconnect acceptance.
        source=ROOT/'artifacts/runs/native-revival-durable-20260921-01/diagnostic-accounts.db'
        with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as before, \
             sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as after:
            for query in ('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources',
                          'SELECT document,resource_revision,revival_document FROM battle_checkpoints'):
                self.assertEqual(before.execute(query).fetchall(),after.execute(query).fetchall())

    def test_live_revival_resources_checkpoint_and_receipt_are_durable(self):
        run=ROOT/'artifacts/runs/native-revival-durable-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'HARD_TIMEOUT')
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(len(evidence['animation_batch_completions']),3)
        for batch in evidence['animation_batch_completions']:
            self.assertEqual((batch['expected'],batch['completed']),(1,1))
            self.assertFalse(batch['timeout_fallback'])
        with sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True) as db:
            self.assertEqual(db.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources').fetchall(),
                             [(100,120,14,80,5)])
            rows=db.execute('SELECT document,resource_revision,revival_document FROM battle_checkpoints').fetchall()
            self.assertEqual(len(rows),1)
            document,revision,phase_document=rows[0]
            state=json.loads(document);phase=json.loads(phase_document)
            self.assertEqual((state['revision'],revision),(4,5))
            self.assertEqual(phase['battle'],document)
            self.assertTrue(all(phase[k] for k in ('initial','opening','action','control','opening_notice')))
            self.assertEqual(phase['design_id'],'CUSTOM-0017')
            executable=ROOT/'build/tests/Release/battle-revival.exe'
            projected=subprocess.run([str(executable),'--resume'],input=phase_document,
                text=True,capture_output=True,timeout=10)
            self.assertEqual(projected.returncode,0,projected.stderr)
            payload=bytes.fromhex(projected.stdout)
            self.assertEqual(len(payload),375)
            self.assertEqual(struct.unpack_from('<I',payload,79+9)[0],14)
            self.assertEqual(struct.unpack_from('<I',payload,141+9)[0],1)
            self.assertEqual(struct.unpack_from('<I',payload,220+9)[0],132)
            self.assertEqual(payload[358:360],bytes.fromhex('8605'))
            incomplete=dict(phase);incomplete['control']=False
            denied=subprocess.run([str(executable),'--resume'],
                input=json.dumps(incomplete,sort_keys=True,separators=(',',':')),
                text=True,capture_output=True,timeout=10)
            self.assertNotEqual(denied.returncode,0)
            self.assertEqual(denied.stdout,'')
            observed=evidence['revival_followup_damage']['actors']
            for actor in observed:
                slot=actor['slot'];hp,mp,max_hp,max_mp=struct.unpack('<4I',bytes.fromhex(actor['vitals_hex']))
                stored=state['actors'][slot]
                self.assertEqual((stored[2],stored[3]),(hp,max_hp))
                if slot<14:self.assertEqual((stored[4],stored[5]),(mp,max_mp))
            self.assertEqual(db.execute('SELECT count(*) FROM battle_settlements').fetchone()[0],0)
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_NEXT_ROUND_GRANTED'),1)
        self.assertEqual(log.count('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=173'),1)
        self.assertEqual(log.count('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=156'),1)
        self.assertNotIn('policy or response rejected',log)

    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((RUN/'run.json').read_text(encoding='utf-8'))

    def test_three_real_participants_and_resource_projection(self):
        evidence = self.evidence
        self.assertEqual(evidence['result'], 'NATIVE_SOCKET_PARTICIPANTS_GRANTED')
        self.assertIsNone(evidence.get('error'))
        self.assertEqual([bytes.fromhex(row['logical_hex'])[1]
                          for row in evidence['socket_participants']], [0, 1, 14])
        actors = evidence['revival_actor_states']
        self.assertEqual([row['slot'] for row in actors], [0, 1, 14])
        self.assertEqual(len({row['actor'] for row in actors}), 3)
        self.assertEqual(struct.unpack('<4I', bytes.fromhex(actors[0]['vitals_hex'])),
                         (100, 80, 120, 80))
        self.assertEqual(struct.unpack('<4I', bytes.fromhex(actors[1]['vitals_hex'])),
                         (0, 5, 120, 20))
        # Enemy MP was not projected; do not relabel allocator bytes as a value.
        enemy = struct.unpack('<4I', bytes.fromhex(actors[2]['vitals_hex']))
        self.assertEqual((enemy[0], enemy[2]), (150, 150))

    def test_owned_skill_and_native_loaded_hotbar_match(self):
        skills = self.evidence['socket_skill_prerequisites']
        self.assertEqual((skills['source_row_count'], skills['first_source_learned_count']), (1, 1))
        self.assertEqual(skills['banks'][0]['first_state_word'], 0x8308)
        self.assertEqual(skills['banks'][0]['first_definition_identity_hex'], '0803')
        self.assertEqual(bytes.fromhex(skills['hotbar']['primary_records_hex']),
                         struct.pack('<HHH', 2, 3, 8)+b'\xff'*54)
        self.assertEqual((RUN/'hotbar-fixture-input.bin').read_bytes(),
                         (RUN/'hotbar-fixture-final.bin').read_bytes())

    def test_zero_hp_is_not_native_death_animation_acceptance(self):
        ally = self.evidence['revival_actor_states'][1]
        self.assertEqual((ally['presentation_state'], ally['pending_state']), (15, 0))
        self.assertEqual(self.evidence['revival_scope'],
                         'INITIALIZATION_ONLY_NO_CAST_OR_DEATH_ANIMATION_CLAIM')
        self.assertNotIn('socket_skill_command_return', self.evidence)

    def test_unsolicited_lethal_preludes_are_not_animation_acceptance(self):
        for suffix in ('01', '02'):
            evidence = json.loads((ROOT/'artifacts/runs'/
                ('native-revival-death-20260921-'+suffix)/'run.json').read_text(encoding='utf-8'))
            self.assertEqual(evidence['result'], 'EVENT_BUDGET_END')
            self.assertFalse(evidence.get('animation_batch_completions'))
            self.assertNotIn('revival_death_state', evidence)
            self.assertNotIn('socket_skill_command_return', evidence)
            ally = evidence['revival_actor_states'][1]
            # Different sampling order: run01 sampled after damage, run02 before.
            self.assertEqual(struct.unpack('<4I', bytes.fromhex(ally['vitals_hex']))[0],
                             0 if suffix == '01' else 4)
            self.assertEqual(ally['pending_state'], 9 if suffix == '01' else 0)

    def test_post_effect_bulk_snapshot_allows_one_natural_batch(self):
        evidence = json.loads((ROOT/'artifacts/runs/native-revival-death-20260921-05/run.json')
                              .read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'NATIVE_REVIVAL_DEATH_PRELUDE_OBSERVED')
        self.assertIsNone(evidence.get('error'))
        batches = evidence['animation_batch_completions']
        self.assertEqual(len(batches), 1)
        self.assertEqual((batches[0]['expected'], batches[0]['completed']), (1, 1))
        self.assertFalse(batches[0]['timeout_fallback'])
        self.assertLess(batches[0]['elapsed_ms'], 10000)
        death = evidence['revival_death_state']
        self.assertGreater(death['sequence'], batches[0]['sequence'])
        self.assertEqual(struct.unpack('<4I', bytes.fromhex(death['vitals_hex'])), (0, 5, 120, 20))
        self.assertEqual((death['presentation_state'], death['pending_state']), (15, 9))
        self.assertNotIn('revival_action_probe', evidence)
        self.assertNotIn('socket_skill_command_return', evidence)

    def test_cast_attempt_without_regrant_stops_before_command(self):
        evidence = json.loads((ROOT/'artifacts/runs/native-revival-cast-20260921-01/run.json')
                              .read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'], 'TOOL_ERROR')
        self.assertIn('Native skill selection did not select', evidence['error'])
        selection = evidence['socket_skill_select_return']
        self.assertEqual((selection['selected_index'], selection['battle_action_mode']), (-1, 0xffffffff))
        self.assertNotIn('socket_skill_command_return', evidence)
        self.assertNotIn('revival_cast_projection', evidence)
        self.assertFalse(evidence['animation_batch_completions'][0]['timeout_fallback'])

    def test_actual_action2_control_batch_roundtrips_formal_parser(self):
        run=ROOT/'artifacts/runs/native-revival-receipt-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        packet=json.loads((run/'packet-decode-0519.json').read_text(encoding='utf-8'))
        self.assertTrue(packet['checksum_valid'] and packet['client_plaintext_match'])
        plain=bytes.fromhex(packet['plain_frame_hex'])
        self.assertEqual((len(plain),plain[2],plain[4],plain[19],plain[21]),(37,0x35,2,0x35,11))
        logical=subprocess.check_output([str(ROOT/'build/tests/Release/recovered-world-records.exe'),
            '--frame',packet['wire_hex']],text=True,timeout=10).strip()
        self.assertEqual(bytes.fromhex(logical),plain[2:-1])
        self.assertLess(519,evidence['revival_death_state']['sequence'])
        self.assertIn('World frame contract rejected',(run/'cpp-server.log').read_text(encoding='utf-8'))

    def test_opening_policy_keeps_connection_but_does_not_regrant(self):
        run=ROOT/'artifacts/runs/native-revival-receipt-20260921-03'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'HARD_TIMEOUT')
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertNotIn('World frame contract rejected',log)
        self.assertNotIn('Recovered world policy or response rejected',log)
        opening=log.index('DIAGNOSTIC_PLAYER_RECORD type_index=11')
        self.assertIn('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=0',log[opening:])
        self.assertGreater(log[opening:].count('RECOVERED_WORLD_BATCH_HANDLED'),3)
        self.assertNotIn('revival_regrant',evidence)
        self.assertNotIn('socket_skill_command_return',evidence)
        commands=[]
        for path in run.glob('packet-decode-*.json'):
            record=json.loads(path.read_text(encoding='utf-8'))
            if int(path.stem.split('-')[-1])>=519 and record.get('opcode')==53:
                commands.append(record['plain_frame_hex'])
        self.assertEqual(len(commands),1)

    def test_regrant_survives_animation_and_native_cast_projects_resources(self):
        run=ROOT/'artifacts/runs/native-revival-regrant-20260921-02'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_REVIVAL_HP_PROJECTION_OBSERVED')
        self.assertIsNone(evidence.get('error'))
        grant=evidence['revival_early_regrant']
        death=evidence['revival_death_state']
        select=evidence['socket_skill_select_return']
        command=evidence['socket_skill_command_return']
        projection=evidence['revival_cast_projection']
        self.assertLess(grant['sequence'],death['sequence'])
        self.assertLess(death['sequence'],select['sequence'])
        self.assertLess(select['sequence'],command['sequence'])
        self.assertLess(command['sequence'],projection['sequence'])
        self.assertEqual(evidence['revival_post_death_controls']['first_grant'],1)
        self.assertEqual((select['selected_index'],select['battle_action_mode']),(0,3))
        raw=bytes.fromhex(command['queued_logical_hex'])
        self.assertEqual((len(raw),raw[:4],raw[5:9],raw[13:]),
                         (17,bytes.fromhex('35000300'),bytes.fromhex('02000000'),bytes.fromhex('08030000')))
        # Byte4 is unwritten native scratch, not a semantic parameter.
        actors=projection['actors']
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(actors[0]['vitals_hex'])),(100,14,120,80))
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(actors[1]['vitals_hex'])),(1,5,120,20))
        self.assertEqual(actors[1]['pending_state'],89)
        self.assertEqual(actors[1]['presentation_state'],15)
        self.assertEqual(len(evidence['animation_batch_completions']),1)  # Prelude only.
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertIn('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=52',log)
        self.assertNotIn('policy or response rejected',log)

    def test_native_revival_consumer_restores_ally_target_membership(self):
        run=ROOT/'artifacts/runs/native-revival-animation-20260921-03'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_REVIVAL_ANIMATION_OBSERVED')
        self.assertIsNone(evidence.get('error'))
        batches=evidence['animation_batch_completions']
        self.assertEqual(len(batches),2)
        for batch in batches:
            self.assertEqual((batch['expected'],batch['completed']),(1,1))
            self.assertFalse(batch['timeout_fallback'])
            self.assertLess(batch['elapsed_ms'],10000)
        entry=evidence['revival_native_consumer_entry']
        returned=evidence['revival_native_consumer_return']
        self.assertEqual(entry['argument'],89)
        self.assertEqual(entry['actor'],evidence['revival_death_state']['actor'])
        self.assertEqual(entry['manager'],evidence['socket_battle_entry']['battle']+0x144938)
        self.assertEqual(struct.unpack('<2I',bytes.fromhex(entry['target_masks_hex'])),(1,1))
        self.assertEqual(struct.unpack('<2I',bytes.fromhex(returned['target_masks_hex'])),(3,1))
        before=bytes.fromhex(entry['state_hex']);after=bytes.fromhex(returned['state_hex'])
        self.assertEqual((before[12],after[12]),(9,0))  # entity+1EA, not +1EB.
        self.assertEqual(entry['vitals_hex'],returned['vitals_hex'])
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(returned['vitals_hex'])),(1,5,120,20))
        self.assertLess(entry['sequence'],returned['sequence'])
        self.assertLess(returned['sequence'],batches[1]['sequence'])
        self.assertGreater(evidence['revival_animation_state']['sequence'],batches[1]['sequence'])


    def test_followup_receipt_is_accepted_and_connection_continues(self):
        run=ROOT/'artifacts/runs/native-revival-followup-receipt-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'HARD_TIMEOUT')  # Deliberate bounded observation.
        self.assertTrue(evidence['revival_followup_receipt_observation'])
        self.assertEqual(len(evidence['animation_batch_completions']),3)
        packet=json.loads((run/'packet-decode-0590.json').read_text(encoding='utf-8'))
        self.assertTrue(packet['checksum_valid'] and packet['client_plaintext_match'])
        self.assertEqual(packet['plain_frame_hex'],'140035000b0000010000000000000000000000c9')
        self.assertGreater(packet['client_plaintext_entry_sequence'],
                           evidence['revival_followup_animation_return']['sequence'])
        logical=subprocess.check_output([str(ROOT/'build/tests/Release/recovered-world-records.exe'),
            '--frame',packet['wire_hex']],text=True,timeout=10).strip()
        self.assertEqual(bytes.fromhex(logical),bytes.fromhex(packet['plain_frame_hex'])[2:-1])
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        after=log.split('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=156',1)[1]
        receipt=after.index('DIAGNOSTIC_PLAYER_RECORD type_index=7')
        later=after[receipt:]
        self.assertIn('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=0',later)
        self.assertGreater(later.count('RECOVERED_WORLD_BATCH_HANDLED'),3)
        self.assertIn('DIAGNOSTIC_TIMER36_ACCEPTED',later)
        self.assertNotIn('policy or response rejected',log)
        self.assertNotIn('World frame contract rejected',log)
        self.assertEqual(log.count('DIAGNOSTIC_NEXT_ROUND_GRANTED'),1)

    def test_followup_settled_snapshot_completes_third_native_batch(self):
        run=ROOT/'artifacts/runs/native-revival-next-animation-20260921-02'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_POST_REVIVAL_BASIC_ANIMATION_OBSERVED')
        self.assertIsNone(evidence.get('error'))
        batches=evidence['animation_batch_completions']
        self.assertEqual(len(batches),3)
        for batch in batches:
            self.assertEqual((batch['expected'],batch['completed']),(1,1))
            self.assertFalse(batch['timeout_fallback'])
            self.assertLess(batch['elapsed_ms'],10000)
        self.assertLess(evidence['revival_followup_damage']['sequence'],batches[2]['sequence'])
        self.assertLess(batches[2]['sequence'],evidence['revival_followup_animation_return']['sequence'])
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertIn('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=156',log)
        self.assertEqual(log.count('DIAGNOSTIC_NEXT_ROUND_GRANTED'),1)
        self.assertNotIn('policy or response rejected',log)

    def test_followup_without_settled_snapshot_does_not_complete_animation(self):
        run=ROOT/'artifacts/runs/native-revival-next-animation-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'HARD_TIMEOUT')
        self.assertIn('revival_followup_damage',evidence)
        self.assertEqual(len(evidence['animation_batch_completions']),2)
        self.assertNotIn('revival_followup_animation_return',evidence)
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertIn('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=35',log)
        self.assertNotIn('policy or response rejected',log)

    def test_post_revival_round_grant_and_basic_damage(self):
        run=ROOT/'artifacts/runs/native-revival-next-turn-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_POST_REVIVAL_BASIC_DAMAGE_OBSERVED')
        self.assertIsNone(evidence.get('error'))
        milestones=json.loads((run/'milestones.json').read_text(encoding='utf-8'))
        self.assertFalse(milestones['WORLD'])
        batches=evidence['animation_batch_completions']
        self.assertEqual(len(batches),2)
        for batch in batches:
            self.assertEqual((batch['expected'],batch['completed']),(1,1))
            self.assertFalse(batch['timeout_fallback'])
        names=('revival_animation_state','revival_followup_grant',
               'revival_followup_command','revival_followup_damage_entry',
               'revival_followup_damage')
        sequences=[evidence[name]['sequence'] for name in names]
        self.assertEqual(sequences,sorted(set(sequences)))
        grant=evidence['revival_followup_grant']
        self.assertEqual((grant['first_grant'],grant['control_state']['waiting']),(1,0))
        command=bytes.fromhex(evidence['revival_followup_command']['logical_hex'])
        self.assertEqual(len(command),17)
        self.assertEqual(command[:4],bytes.fromhex('35000100'))
        # Native scratch bytes are not stable command fields.
        actors=evidence['revival_followup_damage']['actors']
        self.assertEqual([actor['slot'] for actor in actors],[0,1,14])
        vitals=[struct.unpack('<4I',bytes.fromhex(actor['vitals_hex'])) for actor in actors]
        self.assertEqual(vitals[0],(100,14,120,80))
        self.assertEqual(vitals[1],(1,5,120,20))
        self.assertEqual((vitals[2][0],vitals[2][2]),(132,150))
        log=(run/'cpp-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_NEXT_ROUND_GRANTED'),1)
        self.assertEqual(log.count('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=173'),1)
        self.assertIn('DIAGNOSTIC_PLAYER_REPLY accepted=true bytes=35',log)
        self.assertNotIn('policy or response rejected',log)
        self.assertNotIn('World frame contract rejected',log)


if __name__ == '__main__':
    unittest.main()
