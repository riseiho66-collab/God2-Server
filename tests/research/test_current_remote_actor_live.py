"""Observation gate tests, not native runtime evidence."""
import copy
import unittest
import tempfile
import hashlib
import json
import sqlite3
import struct
import sys
from contextlib import closing
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

from tools.strike_lab.current_remote_actor_live import RemoteActorLifecycle,RemoteActorStatusLifecycle,configure_probe,snapshot


def sample(*, x=18, screen_x=100, state=0, remaining=0, empty=False):
    return dict(capacity=128,stride=0x268,clear_mode=1,display_mode=1,extra_mode=1,
        entries=[] if empty else [dict(identity=7,x=x,y=12,screen_x=screen_x,screen_y=100,
            movement_state=state,remaining_x=remaining,remaining_y=0,
            queue_read=0,queue_write=0,render_handle=1)])


class RemoteLifecycleTests(unittest.TestCase):
    def test_captured_native_sleep_set_clear_move_remove(self):
        self.check_captured_status_sequence('native-remote-status-20260921-01',(0x200,0))

    def test_captured_all_five_native_statuses(self):
        self.check_captured_status_sequence('native-remote-status-all-20260921-01',
                                           (0x100,0,0x200,0,0x400,0,0x800,0,0x1000,0))

    def test_captured_native_fight_title_set_and_clear(self):
        name='native-remote-fight-title-20260921-01'
        targets=(0x100,0,0x200,0,0x400,0,0x800,0,0x1000,0,1,0)
        self.check_captured_status_sequence(name,targets)
        run=Path(__file__).resolve().parents[2]/'artifacts/runs'/name
        samples=json.loads((run/'run.json').read_text())['remote_actor_lifecycle']['evidence']
        for index,field,value in ((11,'resource',9999),(11,'action',2),
                                  (11,'graphic_state',1),(11,'handle',-1),
                                  (12,'graphic_state',2)):
            gate=RemoteActorStatusLifecycle(targets)
            for previous in samples[:index]:gate.observe(previous)
            bad=copy.deepcopy(samples[index]);bad['entries'][0]['title'][field]=value
            with self.subTest(index=index,field=field),self.assertRaises(ValueError):
                gate.observe(bad)

    def check_captured_status_sequence(self,name,targets):
        root=Path(__file__).resolve().parents[2]
        run=root/'artifacts/runs'/name
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_REMOTE_ACTOR_POOL_LIFECYCLE_OBSERVED')
        self.assertIsNone(report.get('error'))
        samples=report['remote_actor_lifecycle']['evidence']
        self.assertEqual(len(samples),len(targets)+3)
        gate=RemoteActorStatusLifecycle(targets)
        self.assertEqual([gate.observe(s) for s in samples],[False]*(len(samples)-1)+[True])
        self.assertEqual([s['entries'][0]['status']['value'] for s in samples[1:-2]],list(targets))
        self.assertEqual(samples[2]['entries'][0]['status']['value'],0)
        for mutate in ('resource','action','graphic_state'):
            gate=RemoteActorStatusLifecycle(targets);gate.observe(samples[0])
            bad=copy.deepcopy(samples[1]);bad['entries'][0]['status'][mutate]=9999
            with self.subTest(field=mutate),self.assertRaises(ValueError):gate.observe(bad)
        gate=RemoteActorStatusLifecycle(targets);gate.observe(samples[0])
        with self.assertRaises(ValueError):gate.observe(samples[-2])
        records=[]
        metadata=[json.loads(p.read_text()) for p in (run/'crypto-private').glob('*.json')]
        for meta in sorted(metadata,key=lambda m:m['sequence']):
            if meta.get('direction')!='S2C' or meta.get('opcode') not in (0x6f,0x5e,0x73):continue
            plain=(run/'crypto-private'/meta['plain_file']).read_bytes()
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(sum(x+0x3c for x in plain[:-1])&255,plain[-1])
            records.append((meta['opcode'],plain))
        self.assertEqual([op for op,_ in records],[0x6f]+[0x5e]*(len(targets)+1)+[0x73])
        self.assertEqual([int.from_bytes(p[7:9],'little') for op,p in records if op==0x5e],list(targets)+[0])
        with closing(sqlite3.connect((run/'remote-actor-diagnostic.db').as_uri()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
            self.assertEqual(db.execute('select * from recovered_positions').fetchall(),[])

    def test_native_online_peer_observes_departure_and_rejoin(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/'native-held-rejoin-20260921-01'
        result=json.loads((run/'shared-result.json').read_text())
        self.assertTrue(result['held_reconnect_observed'])
        before=json.loads((run/'peer-0-visible.json').read_text())
        gone=json.loads((run/'peer-0-departed.json').read_text())
        after=json.loads((run/'peer-0-rejoined.json').read_text())
        newcomer=json.loads((run/'rejoin/peer-1-visible.json').read_text())
        self.assertEqual(gone['departure_sample']['entries'],[])
        self.assertEqual(before['client_pid'],gone['client_pid'])
        self.assertEqual(before['client_pid'],after['client_pid'])
        for key in ('manager','display_pool','local_components'):
            self.assertEqual(before['sample'][key],after['sample'][key])
        actor=after['sample']['entries'][0]
        self.assertEqual(actor['identity'],before['sample']['entries'][0]['identity'])
        self.assertEqual(actor['identity'],newcomer['local_identity'])
        self.assertEqual(newcomer['sample']['entries'][0]['identity'],after['local_identity'])
        original_peer=json.loads((run/'peer-1-visible.json').read_text())
        self.assertNotEqual(original_peer['client_pid'],newcomer['client_pid'])
        folder=root/before['run_id']
        report=json.loads((folder/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_SHARED_PLAYER_REJOIN_OBSERVED')
        self.assertIsNone(report.get('error'))
        events=[]
        metadata=[json.loads(p.read_text()) for p in (folder/'crypto-private').glob('*.json')]
        for meta in sorted(metadata,key=lambda m:m['sequence']):
            if meta.get('direction')!='S2C' or meta.get('opcode') not in (0x6f,0x73):continue
            plain=(folder/'crypto-private'/meta['plain_file']).read_bytes()
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(sum(x+0x3c for x in plain[:-1])&255,plain[-1])
            identity=int.from_bytes(plain[3:7],'little')
            if meta['opcode']==0x6f:identity&=4095
            self.assertEqual(identity,actor['identity'])
            events.append(meta['opcode'])
        self.assertEqual(events,[0x6f,0x73,0x6f])

    def test_captured_same_server_two_account_reconnect(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/'native-shared-reconnect-20260921-02'
        result=json.loads((run/'shared-result.json').read_text())
        first=json.loads((run/'shared-server.json').read_text())
        second=json.loads((run/'reconnect/shared-server.json').read_text())
        self.assertEqual(result['result'],'TWO_NATIVE_PLAYER_POOLS_OBSERVED')
        self.assertTrue(result['restored_positions_observed'])
        for key in ('pid','create_time','config','config_sha256','ports','client_profile'):
            self.assertEqual(first[key],second[key])
        self.assertEqual(result['live_reconnect']['server_pid'],first['pid'])
        self.assertEqual(result['live_reconnect']['server_create_time'],first['create_time'])
        self.assertTrue(set(result['client_pids']).isdisjoint(result['live_reconnect']['client_pids']))
        for peer in (0,1):
            before=json.loads((run/f'peer-{peer}-visible.json').read_text())
            after=json.loads((run/f'reconnect/peer-{peer}-visible.json').read_text())
            self.assertEqual(before['local_identity'],after['local_identity'])
            for evidence in (before,after):
                sample=evidence['sample'];actor=sample['entries'][0]
                self.assertEqual(sample['local_position_hex'],'120000000c000000')
                self.assertEqual(sample['local_ring_hex'],'010001')
                self.assertEqual((actor['x'],actor['y']),(18,12))
                self.assertNotEqual(actor['identity'],evidence['local_identity'])
                report=json.loads((root/evidence['run_id']/'run.json').read_text())
                self.assertEqual(report['result'],'NATIVE_SHARED_PLAYER_VISIBILITY_OBSERVED')
                self.assertIsNone(report.get('error'))
                self.assertNotIn('creation_submit',report)
            self.assertEqual(before['sample']['entries'][0]['identity'],after['sample']['entries'][0]['identity'])
        source=Path(result['restored_source']['path'])
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),result['restored_source']['sha256'])
        with closing(sqlite3.connect((run/'player-visibility-diagnostic.db').as_uri()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
            self.assertEqual([list(r) for r in db.execute('select * from recovered_positions order by character_id')],
                             result['restored_source']['positions'])

    def test_captured_two_player_restart_restores_native_positions(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/'native-shared-restore-20260921-01'
        result=json.loads((run/'shared-result.json').read_text())
        self.assertTrue(result['restored_positions_observed'])
        source=Path(result['restored_source']['path'])
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),result['restored_source']['sha256'])
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as original,closing(
                sqlite3.connect((run/'player-visibility-diagnostic.db').as_uri()+'?mode=ro',uri=True)) as restored:
            self.assertEqual(restored.execute('pragma integrity_check').fetchall(),[('ok',)])
            for query in ('select * from recovered_positions order by character_id',
                          'select id,account_id,name_bytes,profile from recovered_characters order by id'):
                self.assertEqual(restored.execute(query).fetchall(),original.execute(query).fetchall())
        identities=[]
        for peer in (0,1):
            evidence=json.loads((run/f'peer-{peer}-visible.json').read_text())
            sample=evidence['sample'];actor=sample['entries'][0]
            identities.append(evidence['local_identity'])
            self.assertEqual(sample['local_position_hex'],'120000000c000000')
            self.assertEqual(sample['local_ring_hex'],'010001')
            self.assertEqual((actor['x'],actor['y']),(18,12))
            self.assertNotEqual(actor['identity'],evidence['local_identity'])
            report=json.loads((root/evidence['run_id']/'run.json').read_text())
            self.assertEqual(report['result'],'NATIVE_SHARED_PLAYER_VISIBILITY_OBSERVED')
            self.assertIsNone(report.get('error'))
            self.assertEqual(bytes.fromhex(report['character_list_consumer']['copied_hex'])[0],1)
            self.assertNotIn('creation_submit',report)
        self.assertEqual(len(set(identities)),2)

    def test_captured_both_native_players_move_and_persist(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/'native-shared-bothmove-20260921-01'
        result=json.loads((run/'shared-result.json').read_text())
        self.assertTrue(result['simultaneous_movement'])
        identities=[]
        for peer in (0,1):
            moved=json.loads((run/f'peer-{peer}-moved.json').read_text())
            initial=json.loads((run/f'peer-{peer}-visible.json').read_text())
            actor=moved['sample']['entries'][0]
            identities.append(moved['local_identity'])
            self.assertNotEqual(actor['identity'],moved['local_identity'])
            self.assertEqual(actor['identity'],initial['sample']['entries'][0]['identity'])
            self.assertEqual(actor['text_fields'],initial['sample']['entries'][0]['text_fields'])
            self.assertEqual((actor['x'],actor['y'],actor['screen_x'],actor['screen_y']),(18,12,1240,500))
            self.assertEqual((actor['movement_state'],actor['queue_read'],actor['queue_write'],actor['remaining_x'],actor['remaining_y']),(0,3,3,0,0))
            producer=json.loads((run/f'peer-{peer}-path-completed.json').read_text())
            self.assertEqual(producer['run_id'],result['peers'][str(peer)])
            self.assertEqual([s['ack_hex'] for s in producer['steps']],['5d01','5d02','5d03'])
            self.assertEqual(producer['completion']['position_hex'],'120000000c000000')
            folder=root/result['peers'][str(peer)]
            report=json.loads((folder/'run.json').read_text())
            self.assertEqual(report['result'],'NATIVE_SHARED_PLAYER_MOVEMENT_OBSERVED')
            self.assertIsNone(report.get('error'))
            metadata=[json.loads(p.read_text()) for p in (folder/'crypto-private').glob('*.json')]
            positions=[]
            for meta in sorted(metadata,key=lambda m:m['sequence']):
                if meta.get('direction')!='S2C' or meta.get('opcode')!=0x5e:continue
                plain=(folder/'crypto-private'/meta['plain_file']).read_bytes()
                self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
                self.assertEqual(len(plain),16)
                self.assertEqual(sum(x+0x3c for x in plain[:-1])&255,plain[-1])
                self.assertEqual(int.from_bytes(plain[3:5],'little'),actor['identity'])
                packed=int.from_bytes(plain[11:15],'little')
                positions.append((packed&2047,(packed>>11)&2047))
            self.assertEqual(positions,[(18,12),(17,13),(18,12)])
        self.assertEqual(len(set(identities)),2)
        with closing(sqlite3.connect((run/'player-visibility-diagnostic.db').as_uri()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
            self.assertEqual(sorted(db.execute('select * from recovered_positions').fetchall()),
                             sorted((identity,2,15,18,12,3) for identity in identities))

    def test_captured_three_step_native_peer_movement(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/'native-shared-movement-20260921-04'
        result=json.loads((run/'shared-result.json').read_text())
        self.assertTrue(result['movement_observed'])
        moved=json.loads((run/'peer-0-moved.json').read_text())
        actor=moved['sample']['entries'][0]
        self.assertEqual((actor['x'],actor['y']),(18,12))
        self.assertEqual((actor['screen_x'],actor['screen_y']),(1240,500))
        self.assertEqual((actor['queue_read'],actor['queue_write']),(3,3))
        self.assertEqual((actor['movement_state'],actor['remaining_x'],actor['remaining_y']),(0,0,0))
        producer=json.loads((run/'peer-1-path-completed.json').read_text())
        self.assertEqual([s['ack_hex'] for s in producer['steps']],['5d01','5d02','5d03'])
        self.assertEqual(producer['completion']['position_hex'],'120000000c000000')
        positions=[]
        peer0=root/result['peers']['0']
        metadata=[json.loads(p.read_text()) for p in (peer0/'crypto-private').glob('*.json')]
        for meta in sorted(metadata,key=lambda m:m['sequence']):
            if meta.get('direction')!='S2C' or meta.get('opcode')!=0x5e:continue
            plain=(peer0/'crypto-private'/meta['plain_file']).read_bytes()
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(len(plain),16)
            self.assertEqual(sum(x+0x3c for x in plain[:-1])&255,plain[-1])
            self.assertEqual(int.from_bytes(plain[3:5],'little'),actor['identity'])
            packed=int.from_bytes(plain[11:15],'little')
            positions.append((packed&2047,(packed>>11)&2047))
        self.assertEqual(positions,[(18,12),(17,13),(18,12)])
        with closing(sqlite3.connect((run/'player-visibility-diagnostic.db').as_uri()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
            self.assertEqual(db.execute('select * from recovered_positions').fetchall(),[(actor['identity'],2,15,18,12,3)])

    def test_captured_native_peer_departure(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/'native-shared-departure-20260921-01'
        result=json.loads((run/'shared-result.json').read_text())
        self.assertTrue(result['departure_observed'])
        evidence=json.loads((run/'peer-0-departed.json').read_text())
        self.assertEqual(evidence['phase'],'REMOTE_DEPARTURE_OBSERVED')
        before=evidence['sample'];after=evidence['departure_sample']
        self.assertEqual(len(before['entries']),1)
        self.assertEqual(after['entries'],[])
        for key in ('manager','display_pool','capacity','stride','local_components'):
            self.assertEqual(before[key],after[key])
        peer0=root/result['peers']['0']
        report=json.loads((peer0/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_SHARED_PLAYER_DEPARTURE_OBSERVED')
        self.assertIsNone(report.get('error'))
        packets=[]
        for path in (peer0/'crypto-private').glob('*.json'):
            meta=json.loads(path.read_text())
            if meta.get('direction')!='S2C' or meta.get('opcode')!=0x73:continue
            plain=(path.parent/meta['plain_file']).read_bytes()
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertTrue(meta['checksum_valid'])
            self.assertEqual(len(plain),8)
            self.assertEqual(sum(x+0x3c for x in plain[:-1])&255,plain[-1])
            self.assertEqual(int.from_bytes(plain[3:5],'little'),before['entries'][0]['identity'])
            packets.append(plain)
        self.assertEqual(len(packets),1)

    def test_departure_requires_prior_visibility_release_and_same_process(self):
        from tools.strike_lab.shared_visibility_probe import observe
        from tools.strike_lab import current_login_command
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            database=folder/'test.db'
            with closing(sqlite3.connect(database)) as db,db:
                db.execute('create table recovered_characters(id integer,name_bytes blob)')
                db.executemany('insert into recovered_characters values(?,?)',[(1,b'CodexTrial'),(2,b'CodexPeer')])
            peers={'0':'run0','1':'run1'}
            server=SimpleNamespace(document=dict(peers=peers,observe_departure=True),
                                   database=database,manifest=folder/'manifest.json')
            state=sample(empty=True)
            state.update(manager=0x20000000+0x15383410,display_pool=0x20000000+0xaba32e0)
            with patch.dict(sys.modules,{'current_login_command':current_login_command}):
                self.assertEqual(observe(server,0,'run0',123,state),(False,None))
                (folder/'peer-0-visible.json').write_text(json.dumps(dict(run_id='run0',client_pid=123)))
                self.assertEqual(observe(server,0,'run0',123,state),(False,None))
                (folder/'release-visible.json').write_text(json.dumps(dict(peers=peers)))
                with self.assertRaises(ValueError):observe(server,0,'run0',124,state)
                self.assertTrue(observe(server,0,'run0',123,state)[0])
                self.assertEqual(observe(server,1,'run1',456,state),(False,None))
                state['display_pool']=0x20000000+0x39c
                with self.assertRaises(ValueError):observe(server,0,'run0',123,state)

    def test_battle_observer_requires_active_clear_and_combatant_return(self):
        from tools.strike_lab.shared_visibility_probe import observe
        from tools.strike_lab import current_login_command
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);database=folder/'test.db'
            with closing(sqlite3.connect(database)) as db,db:
                db.execute('create table recovered_characters(id integer,name_bytes blob)')
                db.executemany('insert into recovered_characters values(?,?)',[(1,b'CodexTrial'),(2,b'CodexPeer')])
            peers={'0':'run0','1':'run1'}
            server=SimpleNamespace(document=dict(peers=peers,observe_battle=True),database=database,
                                   manifest=folder/'manifest.json')
            state=sample(x=17)
            state.update(manager=0x20000000+0x15383410,display_pool=0x20000000+0xaba32e0)
            actor=state['entries'][0];actor.update(identity=1,y=13,
                text_fields=[b'CodexTrial'.hex(),'',''],display_texts=[b'  CodexTrial'.hex(),'',''],
                components=[dict(handle=i,variant=0) for i in range(4)],status=dict(value=0),
                title=dict(handle=3,graphic_state=1,action=1,resource=7,expected_resource=7))
            (folder/'release-visible.json').write_text(json.dumps(dict(peers=peers)))
            (folder/'peer-0-battle-started.json').write_text(json.dumps(dict(client_pid=123)))
            with patch.dict(sys.modules,{'current_login_command':current_login_command}):
                self.assertFalse(observe(server,1,'run1',456,state)[0])
                self.assertFalse((folder/'peer-1-fight-cleared.json').exists())
                actor['status']['value']=1;actor['title']['graphic_state']=2
                for field,value in (('action',2),('resource',99),('handle',-1),('graphic_state',1)):
                    bad=copy.deepcopy(state);bad['entries'][0]['title'][field]=value
                    with self.assertRaises(ValueError):observe(server,1,'run1',456,bad)
                self.assertFalse(observe(server,1,'run1',456,state)[0])
                actor['status']['value']=0
                with self.assertRaises(ValueError):observe(server,1,'run1',456,state)
                actor['title']['graphic_state']=1
                self.assertFalse(observe(server,1,'run1',456,state)[0])
                with self.assertRaises(ValueError):observe(server,1,'run1',457,state)
                completion=folder/'peer-0-battle-returned.json'
                completion.write_text(json.dumps(dict(run_id='run0',client_pid=999)))
                with self.assertRaises(ValueError):observe(server,1,'run1',456,state)
                completion.write_text(json.dumps(dict(run_id='run0',client_pid=123)))
                self.assertTrue(observe(server,1,'run1',456,state)[0])

    def test_captured_two_native_battle_title_lifecycle(self):
        from tools.strike_lab.shared_visibility_probe import observe
        from tools.strike_lab import current_login_command
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/'native-shared-battle-20260921-03'
        result=json.loads((run/'shared-result.json').read_text())
        self.assertEqual(result['result'],'TWO_NATIVE_BATTLE_TITLE_LIFECYCLE_OBSERVED')
        self.assertTrue(result['battle_title_observed']);self.assertFalse(result['world_accepted'])
        self.assertEqual(len(set(result['client_pids'])),2)
        peers=result['peers']
        reports=[json.loads((root/peers[str(i)]/'run.json').read_text()) for i in (0,1)]
        self.assertEqual(reports[0]['result'],'NATIVE_SOCKET_BATTLE_RETURNED_TO_WORLD_LOOP')
        self.assertEqual(reports[1]['result'],'NATIVE_SHARED_PLAYER_BATTLE_TITLE_CLEARED')
        for report in reports:self.assertIsNone(report.get('error'))
        required=('socket_action_return','socket_damage_return','socket_outcome_return',
                  'socket_battle_loop_return','socket_post_battle_world_loop_entry')
        for key in required:self.assertIn(key,reports[0])
        active=json.loads((run/'peer-1-fight.json').read_text())
        clear=json.loads((run/'peer-1-fight-cleared.json').read_text())
        self.assertEqual(active['client_pid'],clear['client_pid'])
        self.assertEqual(active['client_pid'],result['client_pids'][1])
        self.assertEqual(active['sample']['entries'][0]['status']['value'],1)
        self.assertEqual(clear['sample']['entries'][0]['status']['value'],0)
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            server=SimpleNamespace(document=dict(peers=peers,observe_battle=True),
                database=run/'player-visibility-diagnostic.db',manifest=folder/'manifest.json')
            (folder/'release-visible.json').write_text(json.dumps(dict(peers=peers)))
            for name in ('peer-0-battle-started.json','peer-0-battle-returned.json'):
                (folder/name).write_text((run/name).read_text())
            with patch.dict(sys.modules,{'current_login_command':current_login_command}):
                self.assertFalse(observe(server,1,peers['1'],active['client_pid'],active['sample'])[0])
                self.assertTrue(observe(server,1,peers['1'],clear['client_pid'],clear['sample'])[0])
        folder=root/peers['1']/'crypto-private'
        metadata=sorted((json.loads(p.read_text()) for p in folder.glob('*.json')),key=lambda m:m['sequence'])
        states=[]
        for meta in metadata:
            if meta.get('direction')!='S2C' or meta.get('opcode')!=0x5e:continue
            plain=(folder/meta['plain_file']).read_bytes()
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(len(plain),16)
            self.assertEqual(sum(v+0x3c for v in plain[:-1])&255,plain[-1])
            self.assertEqual(int.from_bytes(plain[3:5],'little'),1)
            states.append(int.from_bytes(plain[7:9],'little'))
        self.assertEqual(states,[1,0])
        with closing(sqlite3.connect((run/'player-visibility-diagnostic.db').as_uri()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
            self.assertEqual(db.execute('select * from recovered_positions').fetchall(),[])

    def test_captured_native_postbattle_repopulation_and_movement(self):
        self.check_native_postbattle('native-shared-postbattle-20260921-01')

    def test_captured_native_durable_battle_and_movement(self):
        name='native-shared-durable-20260921-01'
        self.check_native_postbattle(name)
        run=Path(__file__).resolve().parents[2]/'artifacts/runs'/name
        result=json.loads((run/'shared-result.json').read_text())
        self.assertTrue(result['battle_settlement_persisted'])
        config=json.loads((run/'config.json').read_text())
        self.assertTrue(config['development']['diagnostic_battle_resources'])
        for _ in range(2):
            with closing(sqlite3.connect((run/'player-visibility-diagnostic.db').as_uri()+'?mode=ro',uri=True)) as db:
                self.assertEqual(db.execute('select * from character_resources').fetchall(),[(1,100,120,50,80,2,'CUSTOM-0012')])
                self.assertEqual(db.execute('select * from battle_reservations').fetchall(),[(1,1,1,'CUSTOM-0012')])
                self.assertEqual(db.execute('select * from character_experience').fetchall(),[(1,0,'CUSTOM-0012')])
                self.assertEqual(db.execute('select battle_id,resource_revision,total_experience,design_id from battle_settlements').fetchall(),[(1,2,0,'CUSTOM-0012')])
                self.assertEqual(db.execute('select * from battle_checkpoints').fetchall(),[])

    def test_captured_native_checkpoint_battle_and_movement(self):
        self.check_native_checkpoint_battle('native-shared-checkpoint-20260921-01')

    def test_captured_native_pre_action_disconnect_recovery(self):
        name='native-battle-reconnect-20260921-02'
        self.check_native_checkpoint_battle(name)
        run=Path(__file__).resolve().parents[2]/'artifacts/runs'/name
        result=json.loads((run/'shared-result.json').read_text())
        self.assertTrue(result['pre_action_checkpoint_restored'])
        before=json.loads((run/'disconnected/checkpoint-rows.json').read_text())
        self.assertEqual(before['character_resources'],[[1,100,120,50,80,2,'CUSTOM-0012']])
        self.assertEqual(before['battle_reservations'],[[1,1,1,'CUSTOM-0012']])
        self.assertEqual(before['battle_settlements'],[])
        self.assertEqual(len(before['battle_checkpoints']),1)
        checkpoint=json.loads(before['battle_checkpoints'][0][1])
        self.assertEqual((checkpoint['id'],checkpoint['revision'],checkpoint['state']),(1,1,'active'))
        old=json.loads((run/'disconnected/shared-server.json').read_text())
        new=json.loads((run/'recovery-server.json').read_text())
        for key in ('pid','create_time','config','config_sha256','client_profile'):
            self.assertEqual(old[key],new[key])
        self.assertTrue(old['hold_pre_action_disconnect'])
        self.assertFalse(new['hold_pre_action_disconnect'])
        self.assertTrue(new['existing_characters'])
        for filename in ('peer-0-battle-started.json','peer-1-fight.json'):
            earlier=json.loads((run/'disconnected'/filename).read_text())
            later=json.loads((run/filename).read_text())
            self.assertNotEqual(earlier['client_pid'],later['client_pid'])
            self.assertNotEqual(earlier['run_id'],later['run_id'])

    def test_captured_native_terminal_disconnect_no_replayed_settlement(self):
        name='native-terminal-reconnect-20260921-01'
        self.check_native_postbattle(name)
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/name
        result=json.loads((run/'shared-result.json').read_text())
        self.assertTrue(result['terminal_settlement_preserved'])
        before=json.loads((run/'disconnected/checkpoint-rows.json').read_text())
        resumed=json.loads((run/'reconnected-checkpoint-rows.json').read_text())
        self.assertEqual(resumed['battle_checkpoints'][:1],before['battle_checkpoints'])
        self.assertEqual(resumed['battle_settlements'],before['battle_settlements'])
        self.assertEqual(before['character_resources'],[[1,100,120,50,80,3,'CUSTOM-0012']])
        self.assertEqual(resumed['character_resources'],[[1,100,120,50,80,4,'CUSTOM-0012']])
        self.assertEqual(resumed['battle_reservations'],[[1,1,1,'CUSTOM-0012'],[2,1,3,'CUSTOM-0012']])
        original=json.loads((run/'disconnected/shared-server.json').read_text())
        recovery=json.loads((run/'recovery-server.json').read_text())
        self.assertEqual((original['pid'],original['create_time']),(recovery['pid'],recovery['create_time']))
        held=json.loads((run/'disconnected/peer-0-terminal-held.json').read_text())
        returned=json.loads((run/'peer-0-battle-returned.json').read_text())
        self.assertNotEqual(held['client_pid'],returned['client_pid'])
        self.assertEqual(int.from_bytes(bytes.fromhex(held['event']['enemy_vitals_hex'])[:4],'little'),0)
        folder=root/original['peers']['0']/'crypto-private'
        commands=[]
        metadata=sorted((json.loads(p.read_text()) for p in folder.glob('*.json')),key=lambda m:m['sequence'])
        for meta in metadata:
            if meta.get('direction')!='C2S' or meta.get('opcode')!=0x35:continue
            plain=(folder/meta['plain_file']).read_bytes()
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(sum(v+0x3c for v in plain[:-1])&255,plain[-1])
            commands.append(plain[4])
        self.assertEqual(commands,[0x0b,1])  # Initial control and attack, no terminal receipt.
        with closing(sqlite3.connect((run/'player-visibility-diagnostic.db').as_uri()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('select * from character_resources').fetchall(),[(1,100,120,50,80,5,'CUSTOM-0012')])
            self.assertEqual(db.execute('select battle_id,resource_revision,total_experience,design_id from battle_settlements order by battle_id').fetchall(),[(1,3,0,'CUSTOM-0012'),(2,5,0,'CUSTOM-0012')])
            rows=db.execute('select * from battle_checkpoints order by battle_id').fetchall()
            self.assertEqual(list(rows[0]),before['battle_checkpoints'][0])
            self.assertEqual(len(rows),2)
            final=json.loads(rows[1][1])
            self.assertEqual((final['id'],final['revision'],final['state']),(2,2,'finished'))

    def test_captured_native_shared_three_skill_battle(self):
        name='native-shared-skills-20260921-01'
        self.check_native_postbattle(name)
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/name
        result=json.loads((run/'shared-result.json').read_text())
        self.assertTrue(result['skill_battle_observed'])
        report=json.loads((root/result['peers']['0']/'run.json').read_text())
        self.assertEqual(len(report['socket_skill_commands']),3)
        folder=root/result['peers']['0']/'crypto-private'
        metadata=sorted((json.loads(p.read_text()) for p in folder.glob('*.json')),key=lambda m:m['sequence'])
        skills=[]
        for meta in metadata:
            if meta.get('direction')!='C2S' or meta.get('opcode')!=0x35:continue
            plain=(folder/meta['plain_file']).read_bytes()
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(sum(v+0x3c for v in plain[:-1])&255,plain[-1])
            if plain[4]==3:skills.append(plain)
        self.assertEqual(len(skills),3)
        self.assertTrue(all(p[15:19]==b'\x01\0\0\0' for p in skills))
        with closing(sqlite3.connect((run/'player-visibility-diagnostic.db').as_uri()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('select * from character_resources').fetchall(),[(1,76,120,26,80,5,'CUSTOM-0012')])
            self.assertEqual(db.execute('select * from battle_reservations').fetchall(),[(1,1,1,'CUSTOM-0012')])
            self.assertEqual(db.execute('select battle_id,resource_revision,total_experience,design_id from battle_settlements').fetchall(),[(1,5,0,'CUSTOM-0012')])
            rows=db.execute('select document from battle_checkpoints').fetchall()
            self.assertEqual(len(rows),1)
            state=json.loads(rows[0][0])
            self.assertEqual((state['revision'],state['state'],state['winner']),(6,'finished',0))
            self.assertEqual(state['actors'][0][2:6],[76,120,26,80])
            self.assertEqual(state['actors'][14][2],0)

    def test_captured_native_shared_skill_recovery_matches_uninterrupted(self):
        self.check_native_skill_recovery('native-skill-reconnect-20260921-03')

    def test_serialized_catalog_startup_preserves_native_skill_recovery(self):
        name='native-mapfile-serial-20260921-02'
        self.check_native_skill_recovery(name)
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        initial=json.loads((root/name/'shared-server.json').read_text())
        final=json.loads((root/name/'shared-result.json').read_text())
        names=list(initial['peers'].values())+list(final['peers'].values())
        self.assertEqual(len(set(names)),4)
        pids=[]
        for peer in names:
            ready=json.loads((root/peer/'catalog-ready.json').read_text())
            self.assertEqual(ready['run_id'],peer)
            self.assertEqual((ready['stage'],ready['count']),('FIRST_BIND',144))
            self.assertGreater(ready['table'],0)
            pids.append(ready['client_pid'])
        self.assertEqual(len(set(pids)),4)
        self.assertEqual(pids[2:],final['client_pids'])

    def test_native_skill_recovery_survives_server_process_restart(self):
        self.check_native_skill_recovery('native-skill-restart-20260921-01',server_restart=True)

    def check_native_skill_recovery(self,name,server_restart=False):
        self.check_native_postbattle(name)
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/name
        result=json.loads((run/'shared-result.json').read_text())
        self.assertTrue(result['first_skill_checkpoint_restored'])
        before=json.loads((run/'disconnected/checkpoint-rows.json').read_text())
        resumed=json.loads((run/'reconnected-checkpoint-rows.json').read_text())
        self.assertEqual(before,resumed)
        self.assertEqual(before['character_resources'],[[1,88,120,42,80,3,'CUSTOM-0012']])
        self.assertEqual(before['battle_settlements'],[])
        state=json.loads(before['battle_checkpoints'][0][1])
        self.assertEqual((state['revision'],state['state'],state['actors'][14][2]),(3,'active',96))
        held=json.loads((run/'disconnected/peer-0-skill-held.json').read_text())
        self.assertEqual(len(held['animations']),2)
        self.assertFalse(any(a['timeout_fallback'] for a in held['animations']))
        self.assertEqual(len(held['settlement']),3)
        report=json.loads((root/result['peers']['0']/'run.json').read_text())
        self.assertEqual(len(report['socket_skill_commands']),2)
        self.assertEqual(len(report['socket_skill_settlement']),5)
        self.assertNotEqual(held['client_pid'],result['client_pids'][0])
        old=json.loads((run/'disconnected/shared-server.json').read_text())
        new=json.loads((run/'recovery-server.json').read_text())
        old_generation=(old['pid'],old['create_time'])
        new_generation=(new['pid'],new['create_time'])
        if server_restart:
            self.assertNotEqual(old_generation,new_generation)
            self.assertEqual(result['server_restart'],{'before':list(old_generation),'after':list(new_generation)})
            self.assertEqual(old['config_sha256'],new['config_sha256'])
            self.assertEqual(old['config'],new['config'])
        else:
            self.assertEqual(old_generation,new_generation)
        self.assertTrue(new['resume_skill_checkpoint'])
        tables=('battle_checkpoints','character_resources','battle_reservations',
                'character_experience','battle_settlements','recovered_positions')
        snapshots=[]
        for folder in (run,root/'native-shared-skills-20260921-01'):
            with closing(sqlite3.connect((folder/'player-visibility-diagnostic.db').as_uri()+'?mode=ro',uri=True)) as db:
                snapshots.append({table:db.execute('select * from '+table).fetchall() for table in tables})
        self.assertEqual(snapshots[0],snapshots[1])
        self.assertEqual((run/'hotbar-fixture-input.bin').read_bytes(),(run/'hotbar-fixture-final.bin').read_bytes())

    def check_native_checkpoint_battle(self,name):
        self.check_native_postbattle(name)
        run=Path(__file__).resolve().parents[2]/'artifacts/runs'/name
        result=json.loads((run/'shared-result.json').read_text())
        self.assertTrue(result['battle_settlement_persisted'])
        self.assertTrue(result['terminal_checkpoint_persisted'])
        config=json.loads((run/'config.json').read_text())
        self.assertTrue(config['development']['diagnostic_visibility_checkpoint'])
        with closing(sqlite3.connect((run/'player-visibility-diagnostic.db').as_uri()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('select * from character_resources').fetchall(),[(1,100,120,50,80,3,'CUSTOM-0012')])
            self.assertEqual(db.execute('select * from battle_reservations').fetchall(),[(1,1,1,'CUSTOM-0012')])
            self.assertEqual(db.execute('select * from character_experience').fetchall(),[(1,0,'CUSTOM-0012')])
            self.assertEqual(db.execute('select battle_id,resource_revision,total_experience,design_id from battle_settlements').fetchall(),[(1,3,0,'CUSTOM-0012')])
            rows=db.execute('select battle_id,document,resource_revision,policy_id,revival_document from battle_checkpoints').fetchall()
            self.assertEqual(len(rows),1)
            self.assertEqual((rows[0][0],*rows[0][2:]),(1,3,'CUSTOM-0012/diagnostic-v1',None))
            state=json.loads(rows[0][1])
            self.assertEqual((state['id'],state['revision'],state['state'],state['winner']),(1,2,'finished',0))
            self.assertEqual(state['actors'][0][2:6],[100,120,50,80])
            enemies=[a for a in state['actors'] if a and a[0]>=14]
            self.assertTrue(enemies)
            self.assertTrue(all(a[2]==0 for a in enemies))

    def check_native_postbattle(self,name):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/name
        result=json.loads((run/'shared-result.json').read_text())
        self.assertTrue(result['post_battle_movement_observed'])
        self.assertTrue(result['battle_title_observed']);self.assertFalse(result['world_accepted'])
        restored=json.loads((run/'peer-0-repopulated.json').read_text())
        returned=json.loads((run/'peer-0-battle-returned.json').read_text())
        moved=json.loads((run/'peer-1-moved.json').read_text())
        before=json.loads((run/'peer-1-fight.json').read_text())
        producer=json.loads((run/'peer-0-path-completed.json').read_text())
        self.assertEqual(restored['client_pid'],returned['client_pid'])
        self.assertEqual(moved['client_pid'],before['client_pid'])
        self.assertNotEqual(restored['client_pid'],moved['client_pid'])
        self.assertEqual(len(producer['steps']),3)
        peer=restored['sample']['entries'][0]
        self.assertEqual(peer['identity'],2)
        self.assertEqual(peer['text_fields'][0],b'CodexPeer'.hex())
        self.assertEqual(peer['display_texts'][0],b'  CodexPeer'.hex())
        self.assertTrue(0<=peer['render_handle']<4096)
        self.assertTrue(all(c['handle']>=0 for c in peer['components']))
        self.assertEqual(restored['sample']['clear_mode'],1)
        actor=moved['sample']['entries'][0]
        self.assertEqual((actor['identity'],actor['x'],actor['y'],actor['movement_state']),(1,18,12,0))
        self.assertEqual(actor['remaining_x'],0);self.assertEqual(actor['remaining_y'],0)
        self.assertEqual(actor['queue_read'],actor['queue_write'])
        prior=before['sample']['entries'][0]
        self.assertEqual((actor['screen_x'],actor['screen_y']),(prior['screen_x'],prior['screen_y']-40))
        self.assertEqual(actor['status']['value'],0);self.assertEqual(actor['title']['graphic_state'],1)
        expected_results=('NATIVE_MOVEMENT_PATH_COMPLETED','NATIVE_SHARED_PLAYER_BATTLE_MOVEMENT_OBSERVED')
        for i in (0,1):
            folder=root/result['peers'][str(i)]
            report=json.loads((folder/'run.json').read_text())
            self.assertEqual(report['result'],expected_results[i]);self.assertIsNone(report.get('error'))
            packets=[]
            metadata=sorted((json.loads(p.read_text()) for p in (folder/'crypto-private').glob('*.json')),key=lambda m:m['sequence'])
            for meta in metadata:
                if meta.get('direction')!='S2C' or meta.get('opcode')!=(0x6f if i==0 else 0x5e):continue
                plain=(folder/'crypto-private'/meta['plain_file']).read_bytes()
                self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
                self.assertEqual(sum(v+0x3c for v in plain[:-1])&255,plain[-1])
                packets.append(plain)
            if i==0:
                self.assertEqual(len(packets),2)
                self.assertEqual(packets[0],packets[1])
                self.assertEqual(int.from_bytes(packets[1][3:7],'little')&4095,2)
            else:
                self.assertEqual([int.from_bytes(p[7:9],'little') for p in packets],[1,0,0,0,0])
                points=[int.from_bytes(p[11:15],'little') for p in packets[2:]]
                self.assertEqual([(p&2047,(p>>11)&2047) for p in points],[(18,12),(17,13),(18,12)])
        with closing(sqlite3.connect((run/'player-visibility-diagnostic.db').as_uri()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
            self.assertEqual(db.execute('select * from recovered_positions').fetchall(),[(1,2,15,18,12,3)])

    def test_captured_two_native_clients_cross_bind(self):
        for suffix in ('05','06'):
            with self.subTest(run=suffix):
                self.check_two_native_clients_cross_bind(suffix)

    def check_two_native_clients_cross_bind(self,suffix):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/f'native-shared-visibility-20260921-{suffix}'
        result=json.loads((run/'shared-result.json').read_text())
        self.assertEqual(result['result'],'TWO_NATIVE_PLAYER_POOLS_OBSERVED')
        self.assertFalse(result['world_accepted'])
        peers=[json.loads((run/f'peer-{i}-visible.json').read_text()) for i in (0,1)]
        self.assertNotEqual(peers[0]['client_pid'],peers[1]['client_pid'])
        self.assertNotEqual(peers[0]['local_identity'],peers[1]['local_identity'])
        names=[b'CodexTrial',b'CodexPeer']
        with sqlite3.connect((run/'player-visibility-diagnostic.db').as_uri()+'?mode=ro',uri=True) as db:
            self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
            identities={bytes(name):identity for identity,name in db.execute('select id,name_bytes from recovered_characters')}
        for i,peer in enumerate(peers):
            self.assertEqual(peer['run_id'],result['peers'][str(i)])
            self.assertEqual(peer['local_identity'],identities[names[i]])
            report=json.loads((root/peer['run_id']/'run.json').read_text())
            self.assertEqual(report['result'],'NATIVE_SHARED_PLAYER_VISIBILITY_OBSERVED')
            self.assertIsNone(report.get('error'))
            state=peer['sample']
            self.assertEqual(state['display_pool'],state['manager']-0x15383410+0xaba32e0)
            self.assertEqual(len(state['entries']),1)
            actor=state['entries'][0]
            self.assertEqual(actor['identity'],peers[1-i]['local_identity'])
            self.assertEqual(actor['text_fields'][0],names[1-i].hex())
            self.assertEqual(actor['display_texts'][0],(b'  '+names[1-i]).hex())
            self.assertEqual((actor['x'],actor['y']),(17,13))
            self.assertEqual(len(actor['components']),4)
            self.assertTrue(all(c['handle']>=0 for c in actor['components']))

    def test_historical_owner_name_reaches_native_actor_only(self):
        self.check_captured_owner_name('native-remote-actor-name-20260921-01')

    def test_captured_second_public_identity(self):
        self.check_captured_owner_name('native-remote-actor-peer1-20260921-01',b'CodexPeer')

    def check_captured_owner_name(self,run_name,expected_name=None):
        root=Path(__file__).resolve().parents[2]
        run=root/'artifacts/runs'/run_name
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_REMOTE_ACTOR_POOL_LIFECYCLE_OBSERVED')
        self.assertIsNone(report.get('error'))
        # Historical captures read the local display pool: actor/name proof only.
        gate=RemoteActorLifecycle(require_components=True)
        samples=report['remote_actor_lifecycle']['evidence']
        self.assertEqual([gate.observe(s) for s in samples],[False,False,True])
        with sqlite3.connect((run/'remote-actor-diagnostic.db').as_uri()+'?mode=ro',uri=True) as db:
            rows=db.execute('select profile from recovered_characters where id=1').fetchall()
            self.assertEqual(len(rows),1)
            name=rows[0][0][:15].split(b'\0',1)[0]
            self.assertTrue(name)
            if expected_name is not None:
                self.assertEqual(name,expected_name)
                self.assertEqual(report['login_submission']['lab_peer'],1)
                self.assertEqual(db.execute('select a.username from accounts a join recovered_characters c '
                                            'on c.account_id=a.id where c.id=1').fetchall(),
                                 [('god2-bytes:'+b'codexpeer'.hex(),)])
            self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
            self.assertEqual(db.execute('select * from recovered_positions').fetchall(),[])
        folder=run/'crypto-private'
        spawns=[]
        for path in folder.glob('*.json'):
            meta=json.loads(path.read_text())
            if meta['direction']!='S2C':continue
            plain=(folder/meta['plain_file']).read_bytes()
            if len(plain)<4 or plain[2]!=0x6f:continue
            self.assertEqual(len(plain),84)
            self.assertEqual(int.from_bytes(plain[:2],'little'),len(plain))
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertTrue(meta['checksum_valid'])
            self.assertEqual(sum(value+0x3c for value in plain[:-1])&255,plain[-1])
            spawns.append(plain[3:-1])
        self.assertEqual(len(spawns),1)
        self.assertEqual(spawns[0][28:44],name+b'\0'*(16-len(name)))
        for evidence in samples[:2]:
            actor=evidence['entries'][0]
            self.assertEqual(actor['text_fields'],[name.hex(),'',''])
            self.assertNotIn('display_pool',evidence)

    def test_text_gate_checks_centering_and_stability(self):
        valid=sample()
        valid['manager']=0x10000000+0x15383410
        valid['display_pool']=0x10000000+0xaba32e0
        actor=valid['entries'][0]
        actor['text_fields']=[b'Player'.hex(),'','']
        actor['display_texts']=[b'    Player'.hex(),b'       '.hex(),b'       '.hex()]
        gate=RemoteActorLifecycle(require_text=True)
        self.assertFalse(gate.observe(valid))
        for field,value in (('text_fields',['','','']),('display_texts',['','','']),
                            ('text_fields',[(b'X'*16).hex(),'',''])):
            bad=copy.deepcopy(valid);bad['entries'][0][field]=value
            with self.assertRaises(ValueError):RemoteActorLifecycle(require_text=True).observe(bad)
        changed=copy.deepcopy(valid)
        changed['entries'][0]['text_fields'][0]=b'Other'.hex()
        changed['entries'][0]['display_texts'][0]=b'    Other'.hex()
        with self.assertRaises(ValueError):gate.observe(changed)

    def test_snapshot_follows_remote_not_local_display_pool(self):
        world=0x10000000;manager=world+0x15383410;remote=world+0xaba32e0
        records=bytearray(128*0x268)
        for index in range(128):struct.pack_into('<I',records,index*0x268,0xffffffff)
        struct.pack_into('<I',records,0,7)
        records[4:10]=b'Other\0'
        labels=b'    Other\0'+bytes(7)+b'       \0'+bytes(9)+b'       \0'+bytes(9)
        def memory(driver,address,size):
            if address==manager+8:return struct.pack('<I',remote)
            if address==manager+0x13418:return struct.pack('<III',1,1,1)
            if address==world+0xa7e04d0:return bytes(32)
            if manager+0x18<=address<manager+0x18+len(records):
                start=address-manager-0x18;return bytes(records[start:start+size])
            if address==remote+0x70:return labels
            self.fail('Snapshot read an unexpected pool/address')
        with patch.dict(sys.modules,{'pagefile_capacity_compat':SimpleNamespace(memory=memory)}):
            result=snapshot(None,world)
        self.assertEqual(result['display_pool'],remote)
        self.assertEqual(result['entries'][0]['display_texts'][0],b'    Other'.hex())

    def test_captured_projected_components(self):
        root=Path(__file__).resolve().parents[2]
        run=root/'artifacts/runs/native-remote-actor-projected-20260921-01'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_REMOTE_ACTOR_POOL_LIFECYCLE_OBSERVED')
        self.assertIsNone(report.get('error'))
        gate=RemoteActorLifecycle(require_components=True)
        samples=report['remote_actor_lifecycle']['evidence']
        self.assertEqual(len(samples),3)
        self.assertEqual([gate.observe(s) for s in samples],[False,False,True])
        self.assertEqual(samples[0]['local_components'],samples[1]['local_components'])
        folder=run/'crypto-private'
        packets={}
        for path in sorted(folder.glob('*.json')):
            meta=json.loads(path.read_text())
            if meta['direction']!='S2C':continue
            plain=(folder/meta['plain_file']).read_bytes()
            if len(plain)<4 or plain[2] not in (0x2a,0x6f,0x5e,0x73):continue
            self.assertNotIn(plain[2],packets)
            self.assertTrue(meta['checksum_valid'])
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(sum(v+0x3c for v in plain[:-1])&255,plain[-1])
            self.assertEqual(int.from_bytes(plain[:2],'little'),len(plain))
            packets[plain[2]]=plain[3:-1]
        self.assertEqual(set(packets),{0x2a,0x6f,0x5e,0x73})
        local,remote=packets[0x2a],packets[0x6f]
        self.assertEqual((len(local),len(remote)),(36,80))
        self.assertEqual(remote[20:28],local[12:20])
        self.assertEqual((int.from_bytes(remote[:4],'little')>>14)&127,local[2]&127)
        self.assertEqual(remote[5]&127,local[6])
        self.assertEqual(int.from_bytes(remote[:4],'little')&4095,7)
        self.assertEqual(packets[0x5e][:2],b'\x07\0')
        self.assertEqual(packets[0x73],b'\x07\0\0\0')
        log=(run/'cpp-server.log').read_text()
        self.assertNotIn('policy or response rejected',log)
        with sqlite3.connect((run/'remote-actor-diagnostic.db').as_uri()+'?mode=ro',uri=True) as db:
            self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
            self.assertEqual(db.execute('select * from recovered_positions').fetchall(),[])

    def test_component_gate_rejects_mismatch_and_missing_resource(self):
        valid=sample()
        valid['local_components']=[dict(handle=i,variant=i) for i in range(4)]
        valid['entries'][0]['components']=copy.deepcopy(valid['local_components'])
        gate=RemoteActorLifecycle(require_components=True)
        self.assertFalse(gate.observe(valid))
        for field,value in (('handle',-1),('variant',7)):
            bad=copy.deepcopy(valid);bad['entries'][0]['components'][0][field]=value
            with self.assertRaises(ValueError):RemoteActorLifecycle(require_components=True).observe(bad)
        bad=copy.deepcopy(valid)
        bad['local_components'][0]['handle']=-1
        bad['entries'][0]['components']=copy.deepcopy(bad['local_components'])
        with self.assertRaises(ValueError):RemoteActorLifecycle(require_components=True).observe(bad)

    def test_captured_native_socket_lifecycle(self):
        root=Path(__file__).resolve().parents[2]
        run=root/'artifacts/runs/native-remote-actor-lifecycle-20260921-03'
        report=json.loads((run/'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_REMOTE_ACTOR_POOL_LIFECYCLE_OBSERVED')
        self.assertIsNone(report.get('error'))
        gate=RemoteActorLifecycle()
        samples=report['remote_actor_lifecycle']['evidence']
        self.assertEqual(len(samples),3)
        self.assertFalse(gate.observe(samples[0]))
        self.assertFalse(gate.observe(samples[1]))
        self.assertTrue(gate.observe(samples[2]))
        self.assertEqual((samples[0]['entries'][0]['screen_x'],samples[0]['entries'][0]['screen_y']),(1240,500))
        self.assertEqual((samples[1]['entries'][0]['screen_x'],samples[1]['entries'][0]['screen_y']),(1280,480))
        folder=run/'crypto-private'
        expected={
            'packet-0521.json':'54006f0700000000000000000000004a00180000000000010001000100810052656d6f74654865726f0000000000000000000000000000000000000000000000000000000000000000000000000000000000001e',
            'packet-0837.json':'10005e0700000000000000136000006c',
            'packet-1147.json':'0800730700000026'}
        for name,hex_value in expected.items():
            meta=json.loads((folder/name).read_text())
            plain=(folder/meta['plain_file']).read_bytes()
            self.assertEqual(meta['direction'],'S2C')
            self.assertTrue(meta['checksum_valid'])
            self.assertEqual(hashlib.sha256(plain).hexdigest(),meta['plain_sha256'])
            self.assertEqual(plain.hex(),hex_value)
            self.assertEqual(int.from_bytes(plain[:2],'little'),len(plain))
            self.assertEqual(sum(value+0x3c for value in plain[:-1])&255,plain[-1])
        log=(run/'cpp-server.log').read_text()
        self.assertNotIn('policy or response rejected',log)
        for stage in range(3):self.assertEqual(log.count(f'stage={stage} CUSTOM-0026'),1)
        with sqlite3.connect((run/'remote-actor-diagnostic.db').as_uri()+'?mode=ro',uri=True) as db:
            self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
            self.assertEqual(db.execute('select * from recovered_positions').fetchall(),[])

    def test_probe_configuration_preserves_input_and_isolates_database(self):
        settings={'server':{'host':'127.0.0.1'},'database':{'path':'unchanged.db'},
            'development':dict(recovered_movement=True,recovered_world_entry=True,
                recovered_account_auth=True,recovered_dual_connection=True,
                recovered_character_creation=True,mock_login=False,
                diagnostic_battle_rounds=1,diagnostic_battle_transition=False)}
        before=copy.deepcopy(settings)
        with tempfile.TemporaryDirectory() as run:
            result=configure_probe(settings,run,1)
            self.assertEqual(settings,before)
            self.assertEqual(Path(result['database']['path']).name,'remote-actor-diagnostic.db')
            self.assertEqual(result['development']['diagnostic_remote_actor_language'],1)
            self.assertNotIn('diagnostic_battle_rounds',result['development'])
            for value in (-1,2,True,None):
                with self.assertRaises(ValueError):configure_probe(settings,run,value)
            bad=copy.deepcopy(settings);bad['development']['diagnostic_battle_transition']=True
            with self.assertRaises(ValueError):configure_probe(bad,run,0)
            bad=copy.deepcopy(settings);bad['development']['recovered_account_auth']=False
            with self.assertRaises(ValueError):configure_probe(bad,run,0)
            bad=copy.deepcopy(settings);bad['server']['host']='0.0.0.0'
            with self.assertRaises(ValueError):configure_probe(bad,run,0)
            Path(result['database']['path']).touch()
            with self.assertRaises(ValueError):configure_probe(settings,run,0)

    def test_ordered_lifecycle(self):
        gate=RemoteActorLifecycle()
        self.assertFalse(gate.observe(sample(empty=True)))
        self.assertFalse(gate.observe(sample()))
        self.assertFalse(gate.observe(sample(x=19,state=8,remaining=8,screen_x=108)))
        self.assertEqual(gate.stage,'move')
        self.assertFalse(gate.observe(sample(x=19,screen_x=116)))
        self.assertEqual(gate.stage,'remove')
        self.assertTrue(gate.observe(sample(empty=True)))
        self.assertEqual(len(gate.evidence),3)
        with self.assertRaises(ValueError):gate.observe(sample(empty=True))

    def test_empty_pool_is_not_removal_evidence(self):
        gate=RemoteActorLifecycle()
        for _ in range(5):self.assertFalse(gate.observe(sample(empty=True)))
        self.assertEqual(gate.stage,'spawn')
        gate.observe(sample())
        with self.assertRaises(ValueError):gate.observe(sample(empty=True))

    def test_logical_destination_alone_does_not_pass(self):
        for pending in (sample(x=19),sample(x=19,screen_x=116,state=8),
                        sample(x=19,screen_x=116,remaining=1)):
            gate=RemoteActorLifecycle();gate.observe(sample())
            self.assertFalse(gate.observe(pending))
            self.assertEqual(gate.stage,'move')
        gate=RemoteActorLifecycle();gate.observe(sample())
        pending=sample(x=19,screen_x=116)
        pending['entries'][0]['queue_write']=1
        gate.observe(pending)
        self.assertEqual(gate.stage,'move')

    def test_bad_identity_handle_pool_or_sequence_rejected(self):
        mutations=[('identity',8),('render_handle',-1),('render_handle',4096),
                   ('queue_read',40),('queue_write',-1)]
        for key,value in mutations:
            bad=sample();bad['entries'][0][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                RemoteActorLifecycle().observe(bad)
        bad=sample();bad['entries'].append(copy.deepcopy(bad['entries'][0]))
        with self.assertRaises(ValueError):RemoteActorLifecycle().observe(bad)
        bad=sample();bad['clear_mode']=0
        with self.assertRaises(ValueError):RemoteActorLifecycle().observe(bad)
        with self.assertRaises(ValueError):RemoteActorLifecycle().observe(sample(x=19))


if __name__=='__main__':
    unittest.main()
