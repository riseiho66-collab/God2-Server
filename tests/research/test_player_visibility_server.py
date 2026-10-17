"""Taiwan Application sockets with both display scripts, not native-client E2E."""
from pathlib import Path
import struct
import tempfile
import unittest
import sqlite3
import json
from contextlib import closing,ExitStack

import test_recovered_position_blackbox as position
from test_current_world_ready_builder import current_world_ready_wire
from test_recovered_chat_server import RecoveredChatServerTests
from test_current_movement import movement_wire

dual=position.dual


class PlayerVisibilityServerTests(unittest.TestCase):
    harness=position.RecoveredPositionBlackboxTests.harness
    ready=position.RecoveredPositionBlackboxTests.ready
    select=position.RecoveredPositionBlackboxTests.select
    create_character=position.RecoveredPositionBlackboxTests.create_character
    ack=position.RecoveredPositionBlackboxTests.ack
    positions=position.RecoveredPositionBlackboxTests.positions

    @classmethod
    def setUpClass(cls):
        position.RecoveredPositionBlackboxTests.setUpClass()

    def test_visible_peers_exchange_converted_chat_and_keep_movement(self):
        w,h=self.harness()
        original=h.configuration
        def configuration(*args,**kwargs):
            config=original(*args,**kwargs)
            config['development']['diagnostic_player_visibility']=True
            config['development']['diagnostic_remote_actor_language']=0
            config['text']={'dictionary_root':str(dual.ROOT/'resources/opencc')}
            return config
        h.configuration=configuration
        chat=RecoveredChatServerTests('test_same_scene_chat_converts_in_both_directions')
        with tempfile.TemporaryDirectory(prefix='god2-visibility-chat-') as directory:
            with h.server(database=Path(directory)/'player-visibility-diagnostic.db') as server:
                endpoint,tw_id=w.create(h,server)
                simplified_id=self.create_character(h,server,dual.OTHER,b'VisibleChinese')
                chat.speaker_names={tw_id:dual.HEROES[0].decode('ascii'),simplified_id:'VisibleChinese'}
                with h.connect(endpoint) as tw,h.connect(endpoint) as simplified:
                    self.select(w,h,tw,tw_id)
                    tw.sendall(current_world_ready_wire(tw_id,(4,3)))
                    w.state_candidate(h,tw)
                    tw.sendall(h.frame(0x30,b'\0'))
                    h.silent(tw)
                    self.select(w,h,simplified,simplified_id,account=dual.OTHER)
                    simplified.sendall(current_world_ready_wire(simplified_id,(4,2)))
                    w.state_candidate(h,simplified)
                    simplified.sendall(h.frame(0x30,b'\0'))
                    for recipient,identity in ((tw,simplified_id),(simplified,tw_id)):
                        spawn=h.read_frame(recipient,0x6f,84)[3:-1]
                        self.assertEqual(int.from_bytes(spawn[:4],'little')&4095,identity)
                    tw.sendall(chat.chat(h,'漢字遊戲','cp950'))
                    chat.display(h,tw,tw_id,'漢字遊戲','cp950',False)
                    chat.display(h,simplified,tw_id,'汉字游戏','cp936',True)
                    simplified.sendall(chat.chat(h,'欢迎游戏','cp936'))
                    chat.display(h,tw,simplified_id,'歡迎遊戲','cp950',False)
                    chat.display(h,simplified,simplified_id,'欢迎游戏','cp936',True)
                    tw.sendall(movement_wire(18,12,1))
                    self.ack(h,tw,1)
                    update=h.read_frame(simplified,0x5e,16)[3:-1]
                    self.assertEqual(int.from_bytes(update[:2],'little'),tw_id)
                    tw.sendall(chat.chat(h,'測試','cp950'))
                    chat.display(h,tw,tw_id,'測試','cp950',False)
                    chat.display(h,simplified,tw_id,'测试','cp936',True)
                    self.assertEqual(self.positions(server.database),[(tw_id,2,15,18,12,1)])
                    with closing(sqlite3.connect(server.database)) as db:
                        self.assertEqual(db.execute('pragma quick_check').fetchone(),('ok',))

    def test_join_committed_batch_leave_and_reconnect(self):
        w,h=self.harness()
        original=h.configuration
        def configuration(*args,**kwargs):
            config=original(*args,**kwargs)
            config['development']['diagnostic_player_visibility']=True
            config['development']['diagnostic_remote_actor_language']=0
            return config
        h.configuration=configuration
        with tempfile.TemporaryDirectory(prefix='god2-visibility-') as directory:
            with h.server(database=Path(directory)/'player-visibility-diagnostic.db') as server:
                endpoint,first_id=w.create(h,server)
                other_name=b'VisibleOther'
                other_id=self.create_character(h,server,dual.OTHER,other_name)
                before=h.snapshot(server.database)
                with h.connect(endpoint) as first,h.connect(endpoint) as other:
                    self.ready(w,h,first,first_id)
                    first.sendall(h.frame(0x30,b'\0'));h.silent(first)
                    self.ready(w,h,other,other_id,account=dual.OTHER)
                    h.silent(first)
                    other.sendall(h.frame(0x30,b'\0'))
                    for recipient,identity,name in ((first,other_id,other_name),(other,first_id,dual.HEROES[0])):
                        spawn=h.read_frame(recipient,0x6f,84)[3:-1]
                        self.assertEqual(struct.unpack_from('<I',spawn)[0]&4095,identity)
                        self.assertEqual(spawn[28:44].split(b'\0',1)[0],name)
                        point=struct.unpack_from('<I',spawn,12)[0]
                        self.assertEqual(((point>>2)&32767,point>>17),(17,13))
                    first.sendall(movement_wire(0,0,0,records=[(18,12,1),(17,13,2)]))
                    self.ack(h,first,1);self.ack(h,first,2)
                    for expected in ((18,12),(17,13)):
                        update=h.read_frame(other,0x5e,16)[3:-1]
                        self.assertEqual(int.from_bytes(update[:2],'little'),first_id)
                        point=struct.unpack_from('<I',update,8)[0]
                        self.assertEqual((point&2047,(point>>11)&2047),expected)
                    h.silent(first);h.silent(other)
                    self.assertEqual(self.positions(server.database),[(first_id,2,15,17,13,1)])
                    first.close()
                    remove=h.read_frame(other,0x73,8)[3:-1]
                    self.assertEqual(int.from_bytes(remove,'little'),first_id)
                    with h.connect(endpoint) as reconnected:
                        self.ready(w,h,reconnected,first_id)
                        reconnected.sendall(h.frame(0x30,b'\0'))
                        h.read_frame(other,0x6f,84);h.read_frame(reconnected,0x6f,84)
                        reconnected.sendall(movement_wire(30,30,1))
                        h.closed(reconnected)
                        self.assertEqual(int.from_bytes(h.read_frame(other,0x73,8)[3:-1],'little'),first_id)
                        self.assertEqual(self.positions(server.database),[(first_id,2,15,17,13,1)])
                    h.silent(other)
                h.unchanged(server.database,before)

    def test_owned_battle_sets_title_until_terminal_receipt(self):
        self.check_battle_lifecycle()

    def test_owned_battle_persists_settlement(self):
        self.check_battle_lifecycle(persist=True)

    def test_owned_battle_failed_settlement_does_not_emit_success(self):
        self.check_battle_lifecycle(persist=True,fail_commit=True)

    def test_owned_pre_action_battle_reconnect_restores_checkpoint(self):
        self.check_battle_lifecycle(persist=True,checkpoint=True)

    def test_owned_checkpoint_settlement_failure_preserves_snapshot(self):
        self.check_battle_lifecycle(persist=True,checkpoint=True,fail_commit=True)

    def test_owned_checkpoint_changed_enemy_attack_is_rejected(self):
        self.check_battle_lifecycle(persist=True,checkpoint=True,alter_checkpoint=True)

    def test_owned_terminal_disconnect_keeps_committed_settlement(self):
        self.check_battle_lifecycle(persist=True,checkpoint=True,terminal_disconnect=True)

    def test_owned_first_skill_exchange_reconnect_finishes_remaining_rounds(self):
        self.check_battle_lifecycle(persist=True,checkpoint=True,skill_recovery=True)

    def test_owned_first_skill_exchange_rejects_changed_enemy(self):
        self.check_battle_lifecycle(persist=True,checkpoint=True,skill_recovery=True,alter_checkpoint=True)

    def check_battle_lifecycle(self,persist=False,fail_commit=False,checkpoint=False,alter_checkpoint=False,terminal_disconnect=False,skill_recovery=False):
        w,h=self.harness()
        original=h.configuration
        def configuration(*args,**kwargs):
            config=original(*args,**kwargs)
            for flag in ('diagnostic_player_visibility','diagnostic_visibility_battle',
                         'diagnostic_battle_transition','diagnostic_battle_participants',
                         'diagnostic_battle_player_appearance','diagnostic_battle_animations',
                         'diagnostic_battle_terminal'):
                config['development'][flag]=True
            config['development']['diagnostic_remote_actor_language']=0
            config['development']['diagnostic_battle_resources']=persist
            config['development']['diagnostic_visibility_checkpoint']=checkpoint
            if skill_recovery:
                for flag in ('diagnostic_visibility_skill_recovery','diagnostic_battle_skill_seed','diagnostic_battle_skill_settlement'):
                    config['development'][flag]=True
                config['development']['diagnostic_battle_rounds']=3
            return config
        h.configuration=configuration
        def read_logical(client):
            header=h.receive(client,2)
            size=int.from_bytes(header,'little')
            self.assertTrue(4<=size<=0xa03)
            plain=bytearray(header);previous=0
            for i,value in enumerate(h.receive(client,size-2)):
                previous=((value+3-previous)&255)^h.crypto_key[i&255]
                plain.append(previous)
            self.assertEqual(plain[-1],sum(x+0x3c for x in plain[:-1])&255)
            return plain[2:-1]
        def command(action,enemy):
            return h.frame(0x35,struct.pack('<4BHHII',0,action,0,0,0,enemy,0,0))
        def skill():
            return h.frame(0x35,struct.pack('<4BHHII',0,3,0,0,0,1,0,1))
        def read_entry(client):
            if skill_recovery:
                self.assertEqual(read_logical(client)[-9:],b'\x82'+b'\0'*8)
            else:h.read_frame(client,0x82,12)
        with tempfile.TemporaryDirectory(prefix='god2-visible-battle-') as directory:
            with h.server(database=Path(directory)/'player-visibility-diagnostic.db') as server:
                endpoint,identity=w.create(h,server)
                self.assertEqual(identity,1)
                other_id=self.create_character(h,server,dual.OTHER,b'BattleObserver')
                with h.connect(endpoint) as owner,h.connect(endpoint) as observer,ExitStack() as reconnects:
                    self.ready(w,h,owner,identity)
                    owner.sendall(h.frame(0x30,b'\0'));h.silent(owner)
                    self.ready(w,h,observer,other_id,account=dual.OTHER)
                    observer.sendall(h.frame(0x30,b'\0'))
                    h.read_frame(owner,0x6f,84);h.read_frame(observer,0x6f,84)
                    observer.sendall(h.frame(0x30,b'\0'));h.silent(observer)
                    owner.sendall(h.frame(0x30,b'\0'))
                    read_entry(owner)
                    h.silent(observer)  # Sending entry alone is not a battle binding.
                    owner.sendall(h.frame(0x36,b'\0'*8))
                    self.assertTrue(read_logical(owner))
                    marked=h.read_frame(observer,0x5e,16)[3:-1]
                    self.assertEqual(struct.unpack_from('<H',marked)[0],identity)
                    self.assertEqual(struct.unpack_from('<H',marked,4)[0],1)
                    if checkpoint:
                        if skill_recovery:
                            owner.sendall(command(0x0b,0));h.silent(owner)
                            owner.sendall(skill())
                            self.assertTrue(read_logical(owner));self.assertTrue(read_logical(owner))
                            h.silent(observer)
                        with closing(sqlite3.connect(server.database)) as db:
                            checkpoint_before=db.execute('select * from battle_checkpoints').fetchall()
                            resources_before=db.execute('select * from character_resources').fetchall()
                            reservations_before=db.execute('select * from battle_reservations').fetchall()
                            self.assertEqual(len(checkpoint_before),1)
                            self.assertEqual(resources_before[0][5],3 if skill_recovery else 2)
                            if skill_recovery:
                                self.assertEqual(resources_before,[(identity,88,120,42,80,3,'CUSTOM-0012')])
                                self.assertEqual(json.loads(checkpoint_before[0][1])['actors'][14][2],96)
                        owner.close()
                        self.assertEqual(int.from_bytes(h.read_frame(observer,0x73,8)[3:-1],'little'),identity)
                        if alter_checkpoint:
                            with closing(sqlite3.connect(server.database)) as db,db:
                                document=json.loads(checkpoint_before[0][1])
                                enemy=next(actor for actor in document['actors'] if actor and actor[0]>=14)
                                enemy[6]+=1
                                db.execute('update battle_checkpoints set document=?',
                                           (json.dumps(document,sort_keys=True,separators=(',',':')),))
                                altered=db.execute('select * from battle_checkpoints').fetchall()
                        owner=reconnects.enter_context(h.connect(endpoint))
                        self.ready(w,h,owner,identity)
                        owner.sendall(h.frame(0x30,b'\0'))
                        h.read_frame(owner,0x6f,84);h.read_frame(observer,0x6f,84)
                        owner.sendall(h.frame(0x30,b'\0'));read_entry(owner)
                        owner.sendall(h.frame(0x36,b'\0'*8))
                        if alter_checkpoint:
                            h.closed(owner)
                            self.assertEqual(int.from_bytes(h.read_frame(observer,0x73,8)[3:-1],'little'),identity)
                            h.silent(observer)
                            with closing(sqlite3.connect(server.database)) as db:
                                self.assertEqual(db.execute('select * from battle_checkpoints').fetchall(),altered)
                                self.assertEqual(db.execute('select * from character_resources').fetchall(),resources_before)
                                self.assertEqual(db.execute('select * from battle_reservations').fetchall(),reservations_before)
                                self.assertEqual(db.execute('select * from battle_settlements').fetchall(),[])
                            return
                        self.assertTrue(read_logical(owner))
                        self.assertEqual(h.read_frame(observer,0x5e,16)[3:-1],marked)
                        with closing(sqlite3.connect(server.database)) as db:
                            self.assertEqual(db.execute('select * from battle_checkpoints').fetchall(),checkpoint_before)
                            self.assertEqual(db.execute('select * from character_resources').fetchall(),resources_before)
                            self.assertEqual(db.execute('select * from battle_reservations').fetchall(),reservations_before)
                    owner.sendall(command(0x0b,0));h.silent(owner);h.silent(observer)
                    if skill_recovery:
                        owner.sendall(skill())
                        self.assertTrue(read_logical(owner));self.assertTrue(read_logical(owner))
                        owner.sendall(command(0x0b,1));self.assertTrue(read_logical(owner))
                        owner.sendall(skill());self.assertTrue(read_logical(owner))
                        h.silent(observer)
                        owner.sendall(h.frame(0x35,struct.pack('<4BHHII',0,0x0b,0,0,1,0,0,0)))
                        self.assertEqual(read_logical(owner)[0],0x89)
                        self.assertEqual(struct.unpack_from('<H',h.read_frame(observer,0x5e,16)[3:-1],4)[0],0)
                        owner.sendall(h.frame(0x30,b'\0'));h.read_frame(owner,0x6f,84)
                        owner.sendall(movement_wire(18,12,1));self.ack(h,owner,1)
                        h.read_frame(observer,0x5e,16)
                        with closing(sqlite3.connect(server.database)) as db:
                            self.assertEqual(db.execute('select * from character_resources').fetchall(),[(identity,76,120,26,80,5,'CUSTOM-0012')])
                            self.assertEqual(db.execute('select * from battle_reservations').fetchall(),reservations_before)
                            self.assertEqual(db.execute('select battle_id,resource_revision,total_experience,design_id from battle_settlements').fetchall(),[(1,5,0,'CUSTOM-0012')])
                            finished=json.loads(db.execute('select document from battle_checkpoints').fetchone()[0])
                            self.assertEqual((finished['revision'],finished['state'],finished['actors'][14][2]),(6,'finished',0))
                            self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
                        self.assertEqual(self.positions(server.database),[(identity,2,15,18,12,1)])
                        return
                    if persist:
                        with closing(sqlite3.connect(server.database)) as db,db:
                            baseline=db.execute('select * from character_resources').fetchall()
                            self.assertEqual(len(baseline),1)
                            self.assertEqual(db.execute('select count(*) from battle_reservations').fetchone(),(1,))
                            if fail_commit:
                                db.execute("create trigger reject_visible_settlement before insert on battle_settlements begin select raise(abort,'injected settlement failure'); end")
                    owner.sendall(command(1,1))
                    if fail_commit:
                        h.closed(owner)
                        self.assertEqual(int.from_bytes(h.read_frame(observer,0x73,8)[3:-1],'little'),identity)
                        h.silent(observer)
                        with closing(sqlite3.connect(server.database)) as db:
                            self.assertEqual(db.execute('select * from character_resources').fetchall(),baseline)
                            self.assertEqual(db.execute('select * from character_experience').fetchall(),[])
                            self.assertEqual(db.execute('select * from battle_settlements').fetchall(),[])
                            if checkpoint:
                                self.assertEqual(db.execute('select * from battle_checkpoints').fetchall(),checkpoint_before)
                        return
                    self.assertTrue(read_logical(owner))
                    h.silent(observer)  # Damage/finished snapshot alone cannot clear.
                    if terminal_disconnect:
                        tables=('battle_checkpoints','character_resources','battle_reservations',
                                'character_experience','battle_settlements')
                        with closing(sqlite3.connect(server.database)) as db:
                            committed={table:db.execute('select * from '+table).fetchall() for table in tables}
                            self.assertEqual(len(committed['battle_settlements']),1)
                            document=json.loads(committed['battle_checkpoints'][0][1])
                            self.assertEqual((document['state'],document['revision']),('finished',2))
                            self.assertEqual(committed['character_resources'][0][5],3)
                        owner.close()
                        self.assertEqual(int.from_bytes(h.read_frame(observer,0x73,8)[3:-1],'little'),identity)
                        owner=reconnects.enter_context(h.connect(endpoint))
                        self.ready(w,h,owner,identity)
                        owner.sendall(h.frame(0x30,b'\0'))
                        h.read_frame(owner,0x6f,84)
                        returned=h.read_frame(observer,0x6f,84)[3:-1]
                        self.assertEqual(int.from_bytes(returned[:4],'little')&4095,identity)
                        self.assertEqual(int.from_bytes(returned[6:8],'little'),0)
                        owner.sendall(movement_wire(18,12,1));self.ack(h,owner,1)
                        self.assertEqual(struct.unpack_from('<H',h.read_frame(observer,0x5e,16)[3:-1],4)[0],0)
                        self.assertEqual(self.positions(server.database),[(identity,2,15,18,12,1)])
                        h.silent(owner);h.silent(observer)
                        with closing(sqlite3.connect(server.database)) as db:
                            self.assertEqual({table:db.execute('select * from '+table).fetchall() for table in tables},committed)
                            self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])
                        return
                    owner.sendall(command(0x0b,1))
                    self.assertEqual(read_logical(owner)[0],0x89)
                    cleared=h.read_frame(observer,0x5e,16)[3:-1]
                    self.assertEqual(struct.unpack_from('<H',cleared,4)[0],0)
                    self.assertEqual(cleared[:4]+cleared[6:],marked[:4]+marked[6:])
                    owner.sendall(h.frame(0x30,b'\0'))
                    refreshed=h.read_frame(owner,0x6f,84)[3:-1]
                    self.assertEqual(int.from_bytes(refreshed[:4],'little')&4095,other_id)
                    owner.sendall(h.frame(0x30,b'\0'));h.silent(owner);h.silent(observer)
                    owner.sendall(movement_wire(18,12,1))
                    self.ack(h,owner,1)
                    moved=h.read_frame(observer,0x5e,16)[3:-1]
                    self.assertEqual(struct.unpack_from('<H',moved,4)[0],0)
                    self.assertEqual(self.positions(server.database),[(identity,2,15,18,12,1)])
                    owner.close()
                    self.assertEqual(int.from_bytes(h.read_frame(observer,0x73,8)[3:-1],'little'),identity)
                    h.silent(observer)
                if persist:
                    with closing(sqlite3.connect(server.database)) as db:
                        resources=db.execute('select * from character_resources').fetchall()
                        self.assertEqual(resources,[tuple([*baseline[0][:5],baseline[0][5]+1,'CUSTOM-0012'])])
                        self.assertEqual(db.execute('select * from character_experience').fetchall(),[(identity,0,'CUSTOM-0012')])
                        ledger=db.execute('select battle_id,resource_revision,total_experience,design_id from battle_settlements').fetchall()
                        self.assertEqual(ledger,[(1,resources[0][5],0,'CUSTOM-0012')])
                        if checkpoint:
                            final_checkpoint=db.execute('select * from battle_checkpoints').fetchall()
                            self.assertEqual(len(final_checkpoint),1)
                            self.assertNotEqual(final_checkpoint,checkpoint_before)
                        self.assertEqual(db.execute('pragma integrity_check').fetchall(),[('ok',)])


if __name__=='__main__':
    unittest.main()
