"""Actual login entry evidence, not successful authentication or world entry."""
import json
import sqlite3
from pathlib import Path
import struct
import unittest

from tools.strike_lab.current_offline_entry_bridge import pinned_image

ROOT = Path(__file__).resolve().parents[2]


class LiveLoginEntryTests(unittest.TestCase):
    def test_fresh_login_restores_post_battle_position_and_same_character(self):
        source=ROOT/'artifacts/runs/native-post-battle-movement-20260921-02'
        run=ROOT/'artifacts/runs/native-post-battle-restore-20260921-01'
        before=json.loads((source/'run.json').read_text())
        r=json.loads((run/'run.json').read_text())
        self.assertEqual(before['result'],'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertEqual(r['result'],'NATIVE_SAVED_POSITION_RESTORED')
        self.assertNotEqual(r['login_entry']['pid'],before['login_entry']['pid'])
        self.assertEqual(bytes.fromhex(r['character_list_consumer']['copied_hex'])[0],1)
        self.assertEqual(r['restored_position_hex'],struct.pack('<II',18,12).hex())
        self.assertNotIn('creation_submit',r)
        self.assertNotIn('movement_step',r)
        self.assertNotIn('socket_battle_entry',r)
        config=json.loads((run/'diagnostic-server-config.json').read_text())
        self.assertFalse(config['development']['diagnostic_battle_terminal'])
        self.assertFalse(config['development']['diagnostic_battle_transition'])
        self.assertEqual(Path(config['database']['path']).parent,run)
        profiles=[]
        for directory in (source,run):
            db=sqlite3.connect((directory/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)
            try:
                self.assertEqual(db.execute('SELECT character_id,area,scene,x,y,revision FROM recovered_positions').fetchall(),
                                 [(1,2,15,18,12,3)])
                profiles.append(db.execute('SELECT * FROM recovered_characters ORDER BY id').fetchall())
            finally:
                db.close()
        self.assertEqual(len(profiles[0]),1)
        self.assertEqual(profiles[0],profiles[1])
        log=(run/'cpp-server.log').read_text()
        self.assertNotIn('CHARACTER_PROFILE_COMMITTED',log)
        self.assertNotIn('DIAGNOSTIC_BATTLE_TRANSITION_SENT',log)
        self.assertIn('hr=0 written=4',r['restoration'])

    def test_natural_battle_cleanup_returns_to_world_and_movement_persists(self):
        run=ROOT/'artifacts/runs/native-post-battle-movement-20260921-03'
        r=json.loads((run/'run.json').read_text())
        self.assertEqual(r['result'],'NATIVE_MOVEMENT_PATH_COMPLETED')
        cleanup,end,world=(r[k] for k in ('socket_battle_cleanup_entry',
                         'socket_battle_loop_return','socket_post_battle_world_loop_entry'))
        self.assertEqual((cleanup['pc'],cleanup['stage'],end['pc'],end['eax'],world['pc']),
                         (0x515c40,5,0x4658de,0,0x467860))
        self.assertEqual(end['sp'],cleanup['sp']+0x68)
        self.assertEqual(world['world'],r['world_initializer']['world_object'])
        chain=[r['socket_outcome_return'],r['socket_outcome_panel_return'],cleanup,end,world,
               r['movement_completion']['event']]
        self.assertEqual(len({(e['pid'],e['tid']) for e in chain}),1)
        seq=[e['sequence'] for e in chain]
        self.assertTrue(all(a<b for a,b in zip(seq,seq[1:])))
        self.assertEqual(len(r['movement_steps']),3)
        for n,step in enumerate(r['movement_steps'],1):
            self.assertEqual(step['ack_hex'],bytes([0x5d,n]).hex())
            self.assertEqual(step['ring_after_ack'],bytes([1,n,n+1]).hex())
        self.assertEqual(r['movement_completion']['position_hex'],struct.pack('<II',18,12).hex())
        self.assertEqual(r['movement_completion']['motion_state'],0)
        log=(run/'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_FINISHED_BATTLE_RELEASED'),1)
        self.assertEqual(log.count('DIAGNOSTIC_POST_BATTLE_CONTEXT_ACCEPTED'),1)
        self.assertNotIn('World frame contract rejected',log)
        self.assertNotIn('Recovered world policy or response rejected',log)
        db=sqlite3.connect((run/'diagnostic-accounts.db').as_uri()+'?mode=ro',uri=True)
        try:
            self.assertEqual(db.execute('SELECT character_id,area,scene,x,y,revision FROM recovered_positions').fetchall(),
                             [(1,2,15,18,12,3)])
        finally:
            db.close()
        self.assertIn('hr=0 written=4',r['restoration'])

    def test_native_outcome_panel_function_returns_after_result(self):
        run=ROOT/'artifacts/runs/native-socket-outcome-panel-20260921-02'
        r=json.loads((run/'run.json').read_text())
        self.assertEqual(r['result'],'NATIVE_SOCKET_OUTCOME_PANEL_FUNCTION_RETURNED')
        entry,end=r['socket_outcome_panel_entry'],r['socket_outcome_panel_return']
        self.assertEqual((entry['pc'],entry['ret'],end['pc']),(0x485070,0x515a25,0x515a25))
        self.assertEqual(end['sp'],entry['sp']+4)
        self.assertEqual((end['panel_latch'],end['panel_mode'],end['handles_hex']),
                         (1,0,'0e000f00'))
        chain=[r['socket_damage_return'],r['socket_outcome_entry'],r['socket_outcome_return'],entry,end]
        self.assertEqual(len({(e['pid'],e['tid']) for e in chain}),1)
        seq=[e['sequence'] for e in chain]
        self.assertTrue(all(a<b for a,b in zip(seq,seq[1:])))
        self.assertEqual(r['socket_outcome_return']['result_received'],1)
        self.assertNotIn('ui',entry)  # Reserved for warning-event structured data.
        self.assertIn('hr=0 written=4',r['restoration'])

    def test_terminal_socket_action_reaches_zero_award_outcome(self):
        run=ROOT/'artifacts/runs/native-socket-outcome-20260921-01'
        r=json.loads((run/'run.json').read_text())
        self.assertEqual(r['result'],'NATIVE_SOCKET_ZERO_AWARD_OUTCOME_CONSUMED')
        damage=r['socket_damage_return']
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(damage['enemy_vitals_hex'])),
                         (0,0xcdcdcdcd,150,0xcdcdcdcd))
        entry,end=r['socket_outcome_entry'],r['socket_outcome_return']
        self.assertEqual((entry['pc'],entry['ret'],end['pc']),(0x518bf0,0x51459f,0x51459f))
        self.assertEqual(bytes.fromhex(entry['logical_hex']),b'\x89'+bytes(56))
        self.assertEqual((end['eax'],end['result_received']),(1,1))
        self.assertEqual(end['sp'],entry['sp']+8)
        chain=[r['socket_action_return'],damage,entry,end]
        self.assertEqual(len({(e['pid'],e['tid']) for e in chain}),1)
        seq=[e['sequence'] for e in chain]
        self.assertTrue(all(a<b for a,b in zip(seq,seq[1:])))
        self.assertNotIn('socket_retaliation_return',r)
        self.assertNotIn('Recovered world policy or response rejected',(run/'cpp-server.log').read_text())
        self.assertIn('hr=0 written=4',r['restoration'])

    def test_two_socket_rounds_preserve_vitals_and_reauthorize_once(self):
        run=ROOT/'artifacts/runs/native-socket-two-rounds-20260921-02'
        r=json.loads((run/'run.json').read_text())
        self.assertEqual(r['result'],'NATIVE_SOCKET_DIAGNOSTIC_RETALIATION_APPLIED')
        rounds=r['socket_completed_rounds']
        self.assertEqual(len(rounds),2)
        chain=[]
        for n,round_ in enumerate(rounds,1):
            keys=('socket_grant_entry','socket_grant_return','socket_action_return',
                  'socket_damage_entry','socket_damage_return',
                  'socket_retaliation_entry','socket_retaliation_return')
            chain.extend(round_[key] for key in keys)
            self.assertEqual(round_['socket_action_return']['eax'],1)
            self.assertEqual(round_['socket_action_return']['controls_hex'],
                             '010000000000000000000000')
            for prefix,hp,maximum,position in (
                    ('socket_damage',150-18*n,150,14),
                    ('socket_retaliation',100-12*n,120,0)):
                entry,end=round_[prefix+'_entry'],round_[prefix+'_return']
                logical=bytes.fromhex(entry['logical_hex'])
                self.assertEqual(logical[:3],bytes([0x86,0,position]))
                self.assertEqual(struct.unpack_from('<II',logical,5),(maximum,hp))
                values=struct.unpack('<4I',bytes.fromhex(end['enemy_vitals_hex']))
                self.assertEqual((values[0],values[2]),(hp,maximum))
                self.assertEqual(end['sp'],entry['sp']+8)
                self.assertEqual(end['pc'],entry['ret'])
        self.assertEqual(len({(e['pid'],e['tid']) for e in chain}),1)
        sequence=[e['sequence'] for e in chain]
        self.assertTrue(all(a<b for a,b in zip(sequence,sequence[1:])))
        log=(run/'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_NEXT_ROUND_GRANTED'),1)
        self.assertEqual(log.count('WORLD_ENTRY_CANDIDATE_SENT'),1)
        self.assertNotIn('Recovered world policy or response rejected',log)
        self.assertIn('hr=0 written=4',r['restoration'])

    def test_socket_retaliation_updates_both_actor_hp(self):
        run=ROOT/'artifacts/runs/native-socket-retaliation-20260921-01'
        r=json.loads((run/'run.json').read_text())
        self.assertEqual(r['result'],'NATIVE_SOCKET_DIAGNOSTIC_RETALIATION_APPLIED')
        enemy=r['socket_damage_return'];friendly=r['socket_retaliation_return']
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(enemy['enemy_vitals_hex'])),
                         (132,0xcdcdcdcd,150,0xcdcdcdcd))
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(friendly['enemy_vitals_hex'])),(88,50,120,80))
        entry=r['socket_retaliation_entry']
        record=bytes.fromhex(entry['logical_hex'])
        self.assertEqual(record[:3],bytes([0x86,0,0]))
        self.assertEqual(struct.unpack_from('<II',record,5),(120,88))
        self.assertEqual(friendly['sp'],entry['sp']+8)
        self.assertLess(enemy['sequence'],entry['sequence'])
        self.assertEqual((enemy['pid'],enemy['tid']),(friendly['pid'],friendly['tid']))
        self.assertNotIn('Recovered world policy or response rejected',(run/'cpp-server.log').read_text())

    def test_socket_custom_damage_reaches_original_enemy_hp(self):
        run=ROOT/'artifacts/runs/native-socket-damage-20260921-01'
        r=json.loads((run/'run.json').read_text())
        self.assertEqual(r['result'],'NATIVE_SOCKET_DIAGNOSTIC_DAMAGE_APPLIED')
        entry,end=r['socket_damage_entry'],r['socket_damage_return']
        logical=bytes.fromhex(entry['logical_hex'])
        self.assertEqual(logical[:3],bytes([0x86,0,14]))
        self.assertEqual(struct.unpack_from('<II',logical,5),(150,132))
        self.assertEqual(end['sp'],entry['sp']+8)
        self.assertEqual(end['pc'],entry['ret'])
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(end['enemy_vitals_hex'])),
                         (132,0xcdcdcdcd,150,0xcdcdcdcd))
        chain=[r['socket_grant_return'],r['socket_action_return'],entry,end]
        self.assertEqual(len({(e['pid'],e['tid']) for e in chain}),1)
        self.assertEqual([e['sequence'] for e in chain],sorted(e['sequence'] for e in chain))
        log=(run/'cpp-server.log').read_text()
        self.assertNotIn('Recovered world policy or response rejected',log)
        self.assertIn('RECOVERED_WORLD_BATCH_HANDLED records=2',log)

    def test_original_socket_action_emits_attack_and_control_batch(self):
        from tools.strike_lab.current_offline_vitals_live import action_call_page
        run=ROOT/'artifacts/runs/native-socket-action-20260921-01'
        r=json.loads((run/'run.json').read_text())
        probe=r['socket_action_probe']
        raw,_=action_call_page(probe['page']['address'],r['socket_battle_entry']['battle'])
        self.assertEqual(raw.hex(),probe['page']['hex'])
        self.assertEqual(r['socket_action_return']['eax'],1)
        self.assertEqual(r['socket_action_return']['controls_hex'],'010000000000000000000000')
        packet=run/'crypto-private/packet-0496.json'
        meta=json.loads(packet.read_text())
        self.assertEqual(meta['direction'],'C2S')
        self.assertTrue(meta['checksum_valid'])
        plain=(packet.parent/meta['plain_file']).read_bytes()
        self.assertEqual(len(plain),37)
        self.assertEqual(struct.unpack_from('<H',plain)[0],37)
        attack,control=plain[2:19],plain[19:36]
        self.assertEqual(attack[:4],bytes([0x35,0,1,0]))
        self.assertEqual(attack[5:13],bytes([0,0,1,0,0,0,0,0]))
        self.assertEqual(control[:4],bytes([0x35,0,0x0b,0]))
        events=[json.loads(line) for line in (run/'network-events.jsonl').read_text().splitlines()]
        wire=(packet.parent/meta['wire_file']).read_bytes()
        sends=[e for e in events if e.get('api')=='send' and e.get('accepted_buffer')]
        self.assertTrue(any((run/e['accepted_buffer']).read_bytes()==wire and e['eax']==len(wire) for e in sends))
        self.assertIn('Recovered world policy or response rejected',(run/'cpp-server.log').read_text())

    def test_socket_participants_vitals_and_first_grant(self):
        from tools.strike_lab.current_offline_monster_live import identity_record
        from tools.strike_lab.current_offline_vitals_live import grant_record
        run=ROOT/'artifacts/runs/native-socket-participants-20260921-01'
        r=json.loads((run/'run.json').read_text())
        self.assertEqual(r['result'],'NATIVE_SOCKET_PARTICIPANTS_GRANTED')
        self.assertEqual([bytes.fromhex(e['logical_hex']) for e in r['socket_participants']],
                         [identity_record(0),identity_record(1)])
        self.assertEqual(bytes.fromhex(r['socket_grant_entry']['logical_hex']),grant_record())
        end=r['socket_grant_return']
        self.assertEqual((end['eax'],end['first_grant'],end['selectors_hex']),(1,1,'00ff'))
        self.assertEqual(end['sp'],r['socket_grant_entry']['sp']+8)
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(r['socket_actor_vitals'][0])),(100,50,120,80))
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(r['socket_actor_vitals'][1])),
                         (150,0xcdcdcdcd,150,0xcdcdcdcd))
        chain=[r['socket_battle_return'],*r['socket_participants'],r['socket_battle_vitals_return'],
               r['socket_grant_entry'],end]
        self.assertEqual(len({(e['pid'],e['tid']) for e in chain}),1)
        self.assertEqual([e['sequence'] for e in chain],sorted(e['sequence'] for e in chain))
        self.assertNotIn('closing: Recovered world policy',(run/'cpp-server.log').read_text())

    def test_deferred_socket_vitals_reach_original_battle_receiver(self):
        run = ROOT / 'artifacts/runs/native-socket-queue-20260920-02'
        r = json.loads((run / 'run.json').read_text())
        self.assertEqual(r['result'],'NATIVE_SOCKET_BATTLE_VITALS_CONSUMED')
        entry,end=r['socket_battle_vitals_entry'],r['socket_battle_vitals_return']
        self.assertEqual(entry['pc'],0x518a90)
        self.assertEqual(entry['ret'],end['pc'])
        self.assertEqual(end['sp'],entry['sp']+8)
        self.assertEqual(end['eax'],1)
        self.assertEqual((entry['counter_before'],end['counter_after']),(0xffffffff,0))
        self.assertEqual(bytes.fromhex(entry['logical_hex']),b'\x88'+bytes(120))
        events=r['socket_battle_queue_events']
        self.assertEqual([e['event_type'] for e in events],
                         ['SOCKET_BATTLE_QUEUE_FORWARD','SOCKET_BATTLE_DISPATCH_ENTRY'])
        self.assertEqual(events[0]['opcode'],0x88)
        self.assertTrue(all(e['battle_matches'] for e in events))
        chain=[r['socket_battle_return'],*events,entry,end]
        self.assertEqual(len({(e['pid'],e['tid']) for e in chain}),1)
        self.assertEqual([e['sequence'] for e in chain],sorted(e['sequence'] for e in chain))
        log=(run/'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_VITALS88_SENT_AFTER_TIMER36'),1)
        self.assertNotIn('World frame contract rejected',log)
        self.assertIn('hr=0 written=4',r['restoration'])

    def test_socket_battle_timer36_keeps_diagnostic_connection_alive(self):
        run = ROOT / 'artifacts/runs/native-socket-vitals-20260920-02'
        r = json.loads((run / 'run.json').read_text())
        self.assertEqual(r['socket_battle_return']['eax'],1)
        log = (run / 'cpp-server.log').read_text()
        self.assertGreaterEqual(log.count('DIAGNOSTIC_TIMER36_ACCEPTED'),2)
        self.assertNotIn('World frame contract rejected',log)
        self.assertIn('Server stopped cleanly',log)
        # This run did NOT reach the 88 receiver; keep that evidence boundary.
        self.assertNotIn('socket_battle_vitals_return',r)
        image = pinned_image()
        self.assertEqual(image[0x117c3:0x117d0],bytes.fromhex('81c7840000006a08576a368bce'))

    def test_socket_fed_world_transition_calls_native_battle_initializer(self):
        run = ROOT / 'artifacts/runs/native-socket-battle-20260920-01'
        r = json.loads((run / 'run.json').read_text())
        self.assertEqual(r['result'], 'NATIVE_SOCKET_BATTLE_INITIALIZED')
        entry, end = r['socket_battle_entry'], r['socket_battle_return']
        self.assertEqual((entry['pc'],entry['ret'],end['pc']), (0x5112c0,0x46583b,0x46583b))
        self.assertEqual(end['eax'], 1)
        self.assertEqual(end['sp'], entry['sp']+8)
        self.assertEqual((entry['pid'],entry['tid']), (end['pid'],end['tid']))
        self.assertLess(entry['sequence'],end['sequence'])
        self.assertNotIn('movement_step',r)
        log = (run / 'cpp-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_BATTLE_TRANSITION_SENT'),1)
        self.assertIn('WORLD_INITIALIZER_TAIL_ACCEPTED',log)
        config = json.loads((run / 'diagnostic-server-config.json').read_text())
        self.assertTrue(config['development']['diagnostic_battle_transition'])
        self.assertEqual(Path(config['database']['path']).parent,run)
        self.assertIn('hr=0 written=4',r['restoration'])

    def test_native_path_finishes_final_step_and_returns_to_idle(self):
        run = ROOT / 'artifacts/runs/native-movement-complete-20260920-01'
        r = json.loads((run / 'run.json').read_text())
        self.assertEqual(r['result'], 'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertEqual(len(r['movement_steps']), 3)
        completion = r['movement_completion']
        self.assertEqual(completion['position_hex'], struct.pack('<II',18,12).hex())
        self.assertEqual(completion['ring_hex'], '010304')
        self.assertEqual(completion['motion_state'], 0)
        events = [json.loads(line) for line in (run / 'compat-events.jsonl').read_text().splitlines()]
        acks = [e for e in events if e.get('event_type') == 'LIVE_MOVEMENT_ACK_APPLIED']
        self.assertEqual(len(acks), 3)
        self.assertGreater(completion['event']['sequence'], acks[-1]['sequence'])
        self.assertEqual((completion['event']['pid'],completion['event']['tid']),
                         (acks[-1]['pid'],acks[-1]['tid']))
        db = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(db.execute('SELECT x,y,revision FROM recovered_positions').fetchall(), [(18,12,3)])
        finally:
            db.close()

    def test_fresh_client_restores_saved_position_without_new_creation(self):
        run = ROOT / 'artifacts/runs/native-movement-restore-20260920-01'
        source = ROOT / 'artifacts/runs/native-movement-chain-20260920-03'
        r = json.loads((run / 'run.json').read_text())
        before = json.loads((source / 'run.json').read_text())
        self.assertEqual(r['result'], 'NATIVE_SAVED_POSITION_RESTORED')
        self.assertEqual(r['restored_position_hex'], struct.pack('<II',18,12).hex())
        self.assertNotEqual(r['login_entry']['pid'], before['login_entry']['pid'])
        self.assertEqual(bytes.fromhex(r['character_list_consumer']['copied_hex'])[0], 1)
        self.assertEqual(r['world_initializer_return']['eax'], 1)
        self.assertEqual(len(r['world_frame_samples']), 6)
        self.assertNotIn('creation_submit', r)
        self.assertNotIn('movement_step', r)
        log = (run / 'cpp-server.log').read_text()
        self.assertNotIn('CHARACTER_PROFILE_COMMITTED', log)
        self.assertIn('EXISTING_CHARACTER_BOUND character_id=1', log)
        for directory in (source, run):
            db = sqlite3.connect((directory / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
            try:
                self.assertEqual(db.execute('SELECT character_id,area,scene,x,y,revision FROM recovered_positions').fetchall(),
                                 [(1,2,15,18,12,3)])
            finally:
                db.close()
        self.assertIn('hr=0 written=4', r['restoration'])

    def test_native_path_three_steps_preserve_sequence_and_coordinates(self):
        from tools.strike_lab.current_login_command import movement_path_page
        run = ROOT / 'artifacts/runs/native-movement-chain-20260920-03'
        r = json.loads((run / 'run.json').read_text())
        self.assertEqual(r['result'], 'NATIVE_MOVEMENT_ACK_APPLIED')
        self.assertEqual(len(r['movement_steps']), 3)
        for number, step in enumerate(r['movement_steps'], 1):
            self.assertEqual(step['step'], number)
            raw, _ = movement_path_page(step['page']['address'], step['world'], number)
            self.assertEqual(raw.hex(), step['page']['hex'])
            self.assertEqual(step['return_eax'], 1)
            self.assertEqual(step['ack_hex'], bytes([0x5d, number]).hex())
            self.assertEqual(step['ring_after_ack'], bytes([1, number, number+1]).hex())
            expected = (17,13) if number%2 else (18,12)
            self.assertEqual(step['precondition']['position_hex'], struct.pack('<II', *expected).hex())
        events = [json.loads(line) for line in (run / 'compat-events.jsonl').read_text().splitlines()]
        observed = [e for e in events if e.get('event_type') in (
            'LIVE_MOVEMENT_STEP_RETURN', 'LIVE_MOVEMENT_ACK_ENTRY', 'LIVE_MOVEMENT_ACK_APPLIED')]
        self.assertEqual([e['event_type'] for e in observed], [
            'LIVE_MOVEMENT_STEP_RETURN', 'LIVE_MOVEMENT_ACK_ENTRY', 'LIVE_MOVEMENT_ACK_APPLIED'] * 3)
        self.assertEqual(len({(e['pid'],e['tid']) for e in observed}), 1)
        db = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(db.execute('SELECT x,y,revision FROM recovered_positions WHERE character_id=1').fetchall(),
                             [(18,12,3)])
        finally:
            db.close()
        for invalid in (0,40,-1):
            with self.assertRaises(ValueError):
                movement_path_page(0x2000000, 0x3000000, invalid)

    def test_native_movement_ack_applies_and_position_is_committed(self):
        from tools.strike_lab.current_login_command import movement_step_page
        run = ROOT / 'artifacts/runs/native-movement-ack-20260920-02'
        r = json.loads((run / 'run.json').read_text())
        self.assertEqual(r['result'], 'NATIVE_MOVEMENT_ACK_APPLIED')
        self.assertEqual(r['movement_precondition'], {
            'position_hex': '110000000d000000', 'ring_hex': '010001'})
        step = r['movement_step']
        raw, trap = movement_step_page(step['page']['address'], step['world'])
        self.assertEqual(raw.hex(), step['page']['hex'])
        self.assertEqual(step['page']['return_trap'], step['page']['address'] + trap)
        self.assertEqual(step['return_eax'], 1)
        self.assertEqual(step['ring_after'], '020002')
        self.assertEqual(step['ack_hex'], '5d01')
        self.assertEqual(step['ack_token_after'], '01')
        self.assertEqual(step['ring_after_ack'], '010102')
        events = [json.loads(line) for line in (run / 'compat-events.jsonl').read_text().splitlines()]
        chosen = [next(e for e in events if e.get('event_type') == kind) for kind in (
            'LIVE_MOVEMENT_STEP_RETURN', 'LIVE_MOVEMENT_ACK_ENTRY', 'LIVE_MOVEMENT_ACK_APPLIED')]
        self.assertEqual(len({(e['pid'], e['tid']) for e in chosen}), 1)
        self.assertEqual([e['sequence'] for e in chosen], sorted(e['sequence'] for e in chosen))
        self.assertEqual(chosen[-1]['pc'], 0x46b517)
        db = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(db.execute('SELECT character_id,area,scene,x,y,revision FROM recovered_positions').fetchall(),
                             [(1, 2, 15, 18, 12, 1)])
        finally:
            db.close()
        self.assertIn('hr=0 written=4', r['restoration'])

    def test_original_world_completes_three_frame_iterations(self):
        run = ROOT / 'artifacts/runs/native-world-frames-20260920-01'
        r = json.loads((run / 'run.json').read_text())
        self.assertEqual(r['result'], 'NATIVE_WORLD_FRAMES_OBSERVED')
        samples = r['world_frame_samples']
        self.assertEqual([e['pc'] for e in samples], [0x467bca, 0x467bd7] * 3)
        self.assertEqual([e['frame_counter'] for e in samples], [0, 0, 1, 1, 2, 2])
        self.assertEqual(len({(e['pid'], e['tid'], e['sp']) for e in samples}), 1)
        self.assertEqual(r['world_initializer_return']['eax'], 1)
        self.assertIn('hr=0 written=4', r['restoration'])
        image = pinned_image()
        self.assertEqual(0x67bca + struct.unpack_from('<i', image, 0x67bc6)[0], 0x32a20)
        self.assertEqual(0x67bd7 + struct.unpack_from('<i', image, 0x67bd3)[0], 0x32f60)

    def test_isolated_world_handler_accepts_periodic_native_records(self):
        run = ROOT / 'artifacts/runs/native-world-movement-20260920-01'
        r = json.loads((run / 'run.json').read_text())
        self.assertEqual(r['result'], 'HARD_TIMEOUT')
        self.assertEqual(r['world_initializer_return']['eax'], 1)
        self.assertEqual(r['world_loop_entry']['pc'], 0x4655e0)
        config = json.loads((run / 'diagnostic-server-config.json').read_text())
        self.assertTrue(config['development']['recovered_movement'])
        self.assertEqual(Path(config['database']['path']).resolve(), (run / 'diagnostic-accounts.db').resolve())
        self.assertTrue(Path(config['development']['recovered_navigation']).is_absolute())
        log = (run / 'cpp-server.log').read_text()
        self.assertGreaterEqual(log.count('RECOVERED_WORLD_BATCH_HANDLED records=1'), 3)
        self.assertNotIn('Post-initializer world contract not implemented', log)
        packets = [json.loads(p.read_text()) for p in run.glob('packet-decode-*.json')]
        periodic = [p for p in packets if p.get('plain_frame_hex') == '0500300025']
        self.assertGreaterEqual(len(periodic), 3)
        self.assertTrue(all(p['checksum_valid'] and p['client_plaintext_match'] for p in periodic))
        self.assertIn('hr=0 written=4', r['restoration'])

    def test_world_loop_reached_but_world_contract_remains_open(self):
        run = ROOT / 'artifacts/runs/native-world-loop-20260920-01'
        r = json.loads((run / 'run.json').read_text())
        self.assertEqual(r['result'], 'EVENT_BUDGET_END')
        entry = r['world_loop_entry']
        self.assertEqual((entry['pc'], entry['ret']), (0x4655e0, 0x40e0fd))
        self.assertEqual(r['world_initializer_return']['eax'], 1)
        states = r['world_loop_dispatches']
        self.assertEqual([e['world_state'] for e in states], [3])
        self.assertEqual(states[0]['pc'], 0x465638)
        self.assertEqual((states[0]['pid'], states[0]['tid']), (entry['pid'], entry['tid']))
        self.assertIn('Post-initializer world contract not implemented', (run / 'cpp-server.log').read_text())
        self.assertIn('hr=0 written=4', r['restoration'])

    def test_actual_world_initialization_returns_success_and_sends_tail(self):
        run = ROOT / 'artifacts/runs/native-world-entry-20260920-01'
        r = json.loads((run / 'run.json').read_text())
        self.assertEqual(r['result'], 'NATIVE_WORLD_INITIALIZER_SUCCEEDED')
        constructor, initializer, returned = (r[k] for k in (
            'world_constructor', 'world_initializer', 'world_initializer_return'))
        self.assertEqual(constructor['world_object'], initializer['world_object'])
        self.assertEqual((constructor['pc'], initializer['pc'], returned['pc']),
                         (0x4643b0, 0x464910, 0x40e0db))
        self.assertEqual(returned['eax'], 1)
        self.assertEqual(returned['sp'], initializer['sp'] + 28)
        self.assertEqual(len(bytes.fromhex(initializer['arguments_hex'])), 24)
        self.assertLess(constructor['sequence'], initializer['sequence'])
        self.assertLess(initializer['sequence'], returned['sequence'])
        self.assertEqual(len({(e['pid'], e['tid']) for e in (constructor, initializer, returned)}), 1)
        self.assertIn('WORLD_INITIALIZER_TAIL_ACCEPTED opcodes=31,35,28',
                      (run / 'cpp-server.log').read_text())
        self.assertIn('hr=0 written=4', r['restoration'])

    def test_native_character_confirmation_returns_to_application(self):
        from tools.strike_lab.current_login_command import character_select_page
        im = pinned_image()
        self.assertEqual(struct.unpack_from('<I', im, 0x88e8 + 2 * 4)[0], 0x408865)
        run = ROOT / 'artifacts/runs/native-character-select-20260920-01'
        r = json.loads((run / 'run.json').read_text())
        c = r['character_selection_command']
        raw, trap = character_select_page(c['page']['address'], c['login_object'])
        self.assertEqual(raw.hex(), c['page']['hex'])
        self.assertEqual(c['page']['return_trap'], c['page']['address'] + trap)
        self.assertEqual((c['selected'], c['state_after'], c['return_eax']), (0, 20, 1))
        returned = r['character_selection_return']
        self.assertEqual((returned['pc'], returned['eax']), (0x40df8c, 1))
        self.assertEqual(returned['sp'], r['login_entry']['sp'] + 24)
        self.assertEqual(r['result'], 'NATIVE_CHARACTER_SELECTION_RETURNED')
        log = (run / 'cpp-server.log').read_text()
        self.assertIn('EXISTING_CHARACTER_BOUND character_id=1', log)
        self.assertIn('WORLD_ENTRY_CANDIDATE_SENT length=40 opcode=42', log)
        self.assertIn('hr=0 written=4', r['restoration'])

    def test_created_character_refreshed_into_native_selection(self):
        run = ROOT / 'artifacts/runs/native-create-refresh-20260920-03'
        r = json.loads((run / 'run.json').read_text())
        self.assertEqual(r['result'], 'NATIVE_CREATED_SELECTION_READY')
        refresh, ready = r['created_refresh'], r['created_selection_ready']
        self.assertEqual((refresh['pc'], refresh['login_state']), (0x40c099, 4))
        self.assertEqual((ready['pc'], ready['login_state']), (0x40557e, 19))
        self.assertGreaterEqual(ready['panel_handle'], 0)
        self.assertEqual(refresh['character_list_hex'], ready['character_list_hex'])
        body = bytes.fromhex(ready['character_list_hex'])
        self.assertEqual(len(body), 74)
        self.assertEqual(body[0], 1)
        self.assertEqual(body[2:13], b'CodexTrial\0')
        self.assertLess(refresh['sequence'], ready['sequence'])
        self.assertEqual((refresh['pid'], refresh['tid']), (ready['pid'], ready['tid']))
        self.assertEqual(r['create_slot_ack']['return_eax'], 0)
        log = (run / 'cpp-server.log').read_text()
        self.assertIn('session_id=3 ACCOUNT_CHARACTER_LIST_QUEUED', log)
        self.assertIn('session_id=4 RECOVERED_ACCOUNT_BOUND', log)
        self.assertIn('Character operation requires advertised independent connection', log)
        self.assertIn('hr=0 written=4', r['restoration'])

    def test_live_creation_slot_ack_consumed_in_isolated_database(self):
        import sqlite3
        run = ROOT / 'artifacts/runs/native-create-ack-20260920-02'
        r = json.loads((run / 'run.json').read_text())
        self.assertEqual(r['result'], 'NATIVE_CREATE_SLOT_ACK_RETURNED')
        ack = r['create_slot_ack']
        self.assertEqual((ack['logical_hex'], ack['copied_slot'], ack['return_eax']), ('180000', 0, 0))
        events = [json.loads(line) for line in (run / 'compat-events.jsonl').read_text().splitlines()]
        selected = [next(e for e in events if e.get('event_type') == name) for name in (
            'CREATE_SLOT_ACK_ENTRY', 'CREATE_SLOT_ACK_CONSUMED', 'CREATE_SLOT_ACK_RETURN')]
        self.assertEqual([e['pc'] for e in selected], [0x4152be, 0x4152d0, 0x40bee0])
        self.assertEqual(selected[-1]['sp'], ack['entry_sp'] + 20)
        self.assertEqual(len({(e['pid'], e['tid']) for e in selected}), 1)
        config = json.loads((run / 'diagnostic-server-config.json').read_text())
        self.assertEqual(Path(config['database']['path']).resolve(), (run / 'diagnostic-accounts.db').resolve())
        for key in ('bootstrap', 'script_root'):
            self.assertTrue(Path(config['lua'][key]).is_absolute())
        db = sqlite3.connect((run / 'diagnostic-accounts.db').as_uri() + '?mode=ro', uri=True)
        try:
            self.assertEqual(db.execute('SELECT id,account_id,slot,name_bytes FROM recovered_characters').fetchall(),
                             [(1, 1, 0, b'CodexTrial')])
        finally:
            db.close()
        self.assertIn('hr=0 written=4', r['restoration'])

    def test_native_opcode17_committed_then_postcreate_remains_open(self):
        run = ROOT / 'artifacts/runs/native-create-submit-20260920-04'
        r = json.loads((run / 'run.json').read_text())
        self.assertEqual(r['result'], 'EVENT_BUDGET_END')
        log = (run / 'cpp-server.log').read_text()
        self.assertIn('CHARACTER_CREATE_FRAME_VALID length=48 opcode=23', log)
        self.assertIn('CHARACTER_PROFILE_COMMITTED character_id=1', log)
        self.assertIn('Post-create selection prefix rejected', log)
        packets = [json.loads((run / f'packet-decode-{n:04}.json').read_text()) for n in (251, 263, 267)]
        self.assertEqual([p['opcode'] for p in packets], [0x17, 0x18, 0x30])
        self.assertTrue(all(p['checksum_valid'] and p['client_plaintext_match'] for p in packets))
        self.assertEqual(packets[1]['plain_frame_hex'], '050018010e')
        self.assertIn('hr=0 written=4', r['restoration'])

    def test_actual_creation_uses_opcode17_not_existing_opcode1b_contract(self):
        from tools.strike_lab.current_login_command import creation_page
        image = pinned_image()
        self.assertEqual(image[0x14d04:0x14d06], b'\x6a\x17')
        self.assertEqual(0xc117 + struct.unpack_from('<i', image, 0xc113)[0], 0x14cf0)
        self.assertEqual(0xc13c + struct.unpack_from('<i', image, 0xc138)[0], 0x14eb0)
        run = ROOT / 'artifacts/runs/native-create-submit-20260920-03'
        r = json.loads((run / 'run.json').read_text())
        self.assertNotEqual(r['result'], 'TOOL_ERROR')
        for key, submit, state in (('creation_next', False, 6), ('creation_submit', True, 24)):
            c = r[key]
            raw, trap = creation_page(c['page']['address'], c['login_object'], submit)
            self.assertEqual(raw.hex(), c['page']['hex'])
            self.assertEqual(c['page']['return_trap'], c['page']['address'] + trap)
            self.assertEqual(c['state_after'], state)
        p = json.loads((run / 'packet-decode-0251.json').read_text())
        self.assertEqual((p['length'], p['opcode'], p['payload_length']), (48, 0x17, 44))
        self.assertTrue(p['checksum_valid'])
        self.assertTrue(p['client_plaintext_match'])
        self.assertFalse(p['brute_force_used'])
        self.assertEqual(bytes.fromhex(p['plain_frame_hex'])[3:14], b'CodexTrial\0')
        self.assertEqual(r['endpoint_count'], 2)
        self.assertEqual(r['seed_snapshot_count'], 2)
        for n in (1, 2):
            endpoint = json.loads((run / f'network/RUNTIME_SERVER_ENDPOINT_{n:04}.json').read_text())
            self.assertEqual(endpoint['destination']['ip'], '127.0.0.1')
        log = (run / 'cpp-server.log').read_text()
        self.assertIn('session_id=2 RECOVERED_ACCOUNT_BOUND account_id=1', log)
        self.assertIn('Character-create contract rejected', log)
        self.assertNotIn('CHARACTER_CREATE_FRAME_VALID', log)
        self.assertIn('hr=0 written=4', r['restoration'])

    def test_empty_list_reaches_original_creation_panel(self):
        image = pinned_image()
        self.assertEqual(image[0x56c5], 0xe8)
        self.assertEqual(0x56ca + struct.unpack_from('<i', image, 0x56c6)[0], 0x9590)
        run = ROOT / 'artifacts/runs/native-create-panel-20260920-01'
        r = json.loads((run / 'run.json').read_text())
        p = r['character_create_panel']
        self.assertEqual(r['result'], 'NATIVE_CHARACTER_CREATE_PANEL_READY')
        self.assertEqual((p['pc'], p['login_state']), (0x4056db, 21))
        self.assertGreaterEqual(p['panel_handle'], 0)
        self.assertEqual(len(bytes.fromhex(p['draft_hex'])), 40)
        c = r['character_list_consumer']
        self.assertEqual(c['return_eax'], 0)
        self.assertEqual(bytes.fromhex(c['copied_hex']), bytes.fromhex(c['logical_hex'])[1:])
        self.assertEqual(bytes.fromhex(c['copied_hex'])[0], 0)
        events = [json.loads(line) for line in (run / 'compat-events.jsonl').read_text().splitlines()]
        chosen = [next(e for e in events if e.get('event_type') == name) for name in (
            'CHARACTER_LIST_NATIVE_RETURN', 'CHARACTER_CREATE_PANEL_READY')]
        self.assertLess(chosen[0]['sequence'], chosen[1]['sequence'])
        self.assertEqual(len({(e['pid'], e['tid']) for e in chosen}), 1)
        self.assertIn('hr=0 written=4', r['restoration'])
        self.assertIn('ACCOUNT_CHARACTER_LIST_QUEUED length=78', (run / 'cpp-server.log').read_text())

    def test_actual_empty_character_list_consumed_and_returned(self):
        run = ROOT / 'artifacts/runs/native-character-list-20260920-01'
        r = json.loads((run / 'run.json').read_text())
        c = r['character_list_consumer']
        logical, copied = bytes.fromhex(c['logical_hex']), bytes.fromhex(c['copied_hex'])
        self.assertEqual(len(logical), 75)
        self.assertEqual(logical[0], 7)
        self.assertEqual(copied, logical[1:])
        self.assertEqual(copied[0], 0)  # Empty account, not a selectable character.
        self.assertEqual(c['return_eax'], 0)
        events = [json.loads(line) for line in (run / 'compat-events.jsonl').read_text().splitlines()]
        chosen = [next(e for e in events if e.get('event_type') == name) for name in (
            'CHARACTER_LIST_NATIVE_ENTRY', 'CHARACTER_LIST_CONSUMED', 'CHARACTER_LIST_NATIVE_RETURN')]
        self.assertEqual([e['pc'] for e in chosen], [0x4148b9, 0x414963, c['return_pc']])
        self.assertEqual(chosen[-1]['sp'], c['entry_sp'] + 48)
        self.assertEqual(len({(e['pid'], e['tid']) for e in chosen}), 1)
        self.assertEqual(r['result'], 'NATIVE_CHARACTER_LIST_CONSUMER_RETURNED')
        self.assertIn('hr=0 written=4', r['restoration'])

    def test_native_two_list_confirmations_reach_character_list_request(self):
        from tools.strike_lab.current_login_command import select_page
        run = ROOT / 'artifacts/runs/native-server-confirm-20260920-02'
        r = json.loads((run / 'run.json').read_text())
        login = r['login_entry']['login_object']
        for key, channel, state, eax in (('server_confirm', False, 3, 0), ('channel_confirm', True, 18, 1)):
            c = r[key]
            raw, _ = select_page(c['page']['address'], login, channel)
            self.assertEqual(raw.hex(), c['page']['hex'])
            self.assertEqual((c['selected'], c['state_after'], c['return_eax']), (0, state, eax))
        events = [json.loads(line) for line in (run / 'compat-events.jsonl').read_text().splitlines()]
        names = ('SERVER_LIST_UI_READY', 'SERVER_CONFIRM_READY', 'SERVER_CONFIRM_RETURN',
                 'CHANNEL_CONFIRM_READY', 'CHANNEL_CONFIRM_RETURN')
        chosen = [next(e for e in events if e.get('event_type') == name) for name in names]
        self.assertEqual([e['sequence'] for e in chosen], sorted(e['sequence'] for e in chosen))
        self.assertEqual(len({(e['pid'], e['tid']) for e in chosen}), 1)
        server = (run / 'cpp-server.log').read_text()
        self.assertIn('POST_SERVER_SELECT_C2S_ACCEPTED length=6', server)
        self.assertIn('ACCOUNT_CHARACTER_LIST_QUEUED length=78', server)
        self.assertIn('Server stopped cleanly', server)
        self.assertIn('hr=0 written=4', r['restoration'])

    def test_native_submit_authenticates_and_populates_server_list(self):
        from tools.strike_lab.current_login_command import submit_page
        run = ROOT / 'artifacts/runs/native-login-submit-20260920-01'
        r = json.loads((run / 'run.json').read_text())
        s = r['login_submission']
        raw, trap = submit_page(s['page']['address'], s['login_object'])
        self.assertEqual(raw.hex(), s['page']['hex'])
        self.assertEqual(raw[trap:trap+3], b'\xcc\x0f\x0b')
        self.assertEqual((s['state_after'], s['return_eax']), (15, 1))
        events = [json.loads(line) for line in (run / 'compat-events.jsonl').read_text().splitlines()]
        kinds = ('LOGIN_TEST_SUBMIT_RETURN', 'S2C0003_CONSUMED', 'LOGIN_TERMINAL_RETURN',
                 'LOGIN_STATE_CHANGE_RETURN', 'SERVER_LIST_UI_READY')
        chosen = [next(e for e in events if e.get('event_type') == kind) for kind in kinds]
        self.assertEqual([e['sequence'] for e in chosen], sorted(e['sequence'] for e in chosen))
        self.assertEqual(len({(e['pid'], e['tid']) for e in chosen}), 1)
        self.assertEqual(chosen[2]['eax'], 0)
        self.assertIn('state=2 previous=f', chosen[3]['ui_state'])
        self.assertIn('count=1 selected=0 enabled0=1 directory_count=1', chosen[4]['list_state'])
        self.assertTrue(r['milestones']['CONNECTED'])
        self.assertTrue(r['milestones']['FIRST_TX'])
        server = (run / 'cpp-server.log').read_text()
        self.assertIn('RECOVERED_ACCOUNT_BOUND account_id=1', server)
        self.assertIn('Server stopped cleanly', server)
        self.assertIn('hr=0 written=4', r['restoration'])
        # Overall run waited after the accepted list, not after a login failure.
        self.assertEqual(r['result'], 'HARD_TIMEOUT')

    def test_original_loop_initializes_real_login_panel(self):
        image = pinned_image()
        self.assertEqual(struct.unpack_from('<I', image, 0x5bf8 + 4)[0], 0x40530b)
        self.assertEqual(image[0x5320], 0xe8)
        self.assertEqual(0x5325 + struct.unpack_from('<i', image, 0x5321)[0], 0x67c0)
        run = ROOT / 'artifacts/runs/native-login-panel-20260920-01'
        r = json.loads((run / 'run.json').read_text())
        initial, ready = r['login_panel_initialization'], r['login_panel_ready']
        self.assertEqual((initial['pc'], ready['pc']), (0x405325, 0x405336))
        self.assertEqual((initial['login_state'], ready['login_state']), (1, 14))
        self.assertGreaterEqual(initial['panel_handle'], 0)
        self.assertEqual(initial['panel_handle'], ready['panel_handle'])
        self.assertEqual((initial['pid'], initial['tid']), (ready['pid'], ready['tid']))
        self.assertLess(initial['sequence'], ready['sequence'])
        self.assertEqual(r['result'], 'NATIVE_LOGIN_PANEL_READY')
        self.assertIn('hr=0 written=4', r['restoration'])
        self.assertFalse(r['milestones']['CONNECTED'])
        self.assertFalse(r['milestones']['FIRST_TX'])

    def test_native_menu_command_changes_only_prelogin_stage(self):
        from tools.strike_lab.current_login_command import call_page
        page, trap = call_page(0x2000000, 0x3000000)
        self.assertEqual(page[:4], b'\x6a\x01\x6a\x03')
        self.assertEqual(page[trap:], b'\xcc\x0f\x0b')
        with self.assertRaises(ValueError):
            call_page(0, 0x3000000)
        run = ROOT / 'artifacts/runs/native-login-command-20260920-01'
        r = json.loads((run / 'run.json').read_text())
        c = r['login_command']
        self.assertEqual(r['result'], 'NATIVE_LOGIN_MENU_COMMAND_RETURNED')
        self.assertEqual((c['state_after'], c['previous_after'], c['return_eax']), (1, 0, 1))
        self.assertEqual(c['login_object'], r['login_entry']['login_object'])
        raw, _ = call_page(c['page']['address'], c['login_object'])
        self.assertEqual(raw.hex(), c['page']['hex'])
        events = [json.loads(line) for line in (run / 'compat-events.jsonl').read_text().splitlines()]
        selected = [e for e in events if e.get('event_type') in (
            'NATIVE_LOGIN_LOOP_ENTRY', 'LOGIN_MENU_INITIALIZED', 'LOGIN_MENU_COMMAND_RETURN')]
        self.assertEqual(len(selected), 3)
        self.assertEqual(len({(e['pid'], e['tid']) for e in selected}), 1)
        self.assertEqual(selected[-1]['sp'], c['entry_sp'])
        self.assertIn('hr=0 written=4', r['restoration'])
        self.assertFalse(r['milestones']['CONNECTED'])
        self.assertFalse(r['milestones']['FIRST_TX'])

    def test_original_caller_and_live_owned_login_context(self):
        image = pinned_image()
        self.assertEqual(image[0xdf87], 0xe8)
        self.assertEqual(0xdf8c + struct.unpack_from('<i', image, 0xdf88)[0], 0x4da0)
        run = ROOT / 'artifacts/runs/native-login-entry-20260920-01'
        report = json.loads((run / 'run.json').read_text())
        events = [json.loads(line) for line in (run / 'compat-events.jsonl').read_text().splitlines()]
        entries = [e for e in events if e.get('event_type') == 'NATIVE_LOGIN_LOOP_ENTRY']
        self.assertEqual(len(entries), 1)
        e = entries[0]
        self.assertEqual((e['pc'], e['ret']), (0x404da0, 0x40df8c))
        self.assertEqual(e['application'], 0x5e00f8)
        self.assertTrue(0x10000 <= e['login_object'] < 0x7fffffff)
        self.assertEqual((e['login_state'], e['previous_login_state']), (0, 0))
        self.assertEqual(len(bytes.fromhex(e['arguments_hex'])), 20)
        self.assertEqual(report['result'], 'NATIVE_LOGIN_LOOP_ENTRY_OBSERVED')
        self.assertIn('hr=0 written=4', report['restoration'])
        self.assertFalse(report['milestones']['CONNECTED'])
        self.assertFalse(report['milestones']['FIRST_TX'])
        self.assertFalse(any(e.get('api') in ('connect', 'WSAConnect', 'send', 'WSASend') for e in events))


if __name__ == '__main__':
    unittest.main()
