"""Two authenticated native-protocol sockets, CP950/CP936 common chat.

This checks real server routing and wire bytes without claiming rendered UI.
"""
from contextlib import ExitStack,closing
import hashlib
import sqlite3
import unittest
import tempfile
from pathlib import Path

import test_recovered_world_entry_server as world
from test_current_world_ready_builder import current_world_ready_wire
from test_current_movement import movement_wire


class RecoveredChatServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        world.RecoveredWorldEntryServerTests.setUpClass()

    def harness(self):
        w=world.RecoveredWorldEntryServerTests()
        h=w.harness()
        original=h.configuration
        def configuration(*args,**kwargs):
            result=original(*args,**kwargs)
            result['development']['recovered_movement']=True
            result['development']['recovered_navigation']=str(
                world.dual.ROOT/'artifacts/world-atlas/indoor-2-15.json')
            result['text']={'dictionary_root':str(world.dual.ROOT/'resources/opencc')}
            return result
        h.configuration=configuration
        return w,h

    @staticmethod
    def chat(h,text,encoding):
        legacy=text.encode(encoding)
        logical_length=len(legacy)+8
        return h.frame(0x2f,logical_length.to_bytes(2,'little')+bytes(4)+legacy+b'\0')

    def display(self,h,client,identity,text,encoding,simplified):
        text=self.speaker_names[identity]+": "+text
        legacy=text.encode(encoding)
        plain=h.read_frame(client,0x5c,len(legacy)+17)
        logical=plain[2:-1]
        self.assertEqual(int.from_bytes(logical[1:3],'little'),len(logical))
        self.assertEqual(logical[3:5],bytes(2))
        self.assertEqual(int.from_bytes(logical[5:9],'little'),identity)
        self.assertEqual(logical[9],0x80 if simplified else 0)
        self.assertEqual(logical[10:13],bytes(3))
        self.assertEqual(logical[13:-1].decode(encoding),text)
        self.assertEqual(logical[-1],0)

    def enter(self,w,h,stack,server,name,hero,language):
        login=stack.enter_context(h.connect(server.endpoint))
        endpoint=h.login(login,name=name)
        self.assertEqual(h.list_characters(login)[3],0)
        game=stack.enter_context(h.connect(endpoint))
        h.game_ready(game,name=name)
        h.create(game,hero)
        with closing(sqlite3.connect(server.database)) as db:
            identity=db.execute('SELECT id FROM recovered_characters WHERE account_id='
                '(SELECT id FROM accounts WHERE username=?)',('god2-bytes:'+name.lower().hex(),)).fetchone()[0]
        if not hasattr(self,"speaker_names"): self.speaker_names={}
        self.speaker_names[identity]=hero.decode("cp936" if language=="zh-CN" else "cp950")
        game.sendall(h.frame(0x18,b'\x01')+h.frame(0x1a,world.dual.selection_payload(0)))
        w.selected(h,game,identity,(17,13))
        game.sendall(current_world_ready_wire(identity,(4,2) if language=='zh-CN' else (4,3)))
        h.silent(game)
        return game,identity

    def test_saved_name_encoding_survives_language_switch_and_server_restart(self):
        for language,encoding,opposite,name in (
            ('zh-TW','cp950','cp936','測試'),('zh-CN','cp936','cp950','中文')):
            with self.subTest(language=language),tempfile.TemporaryDirectory() as folder:
                database=Path(folder)/'names.db'
                w,h=self.harness()
                with h.server(database=database) as server,ExitStack() as stack:
                    game,identity=self.enter(w,h,stack,server,world.dual.OWNER,name.encode(encoding),language)
                    game.sendall(self.chat(h,'123',encoding))
                    self.display(h,game,identity,'123',encoding,language=='zh-CN')
                with h.server(database=database,registration=False) as server,ExitStack() as stack:
                    login=stack.enter_context(h.connect(server.endpoint));endpoint=h.login(login)
                    h.list_characters(login)
                    game=stack.enter_context(h.connect(endpoint));h.game_ready(game)
                    game.sendall(h.frame(0x1a,world.dual.selection_payload(0)))
                    w.selected(h,game,identity,(17,13))
                    simplified=opposite=='cp936'
                    game.sendall(current_world_ready_wire(identity,(4,2 if simplified else 3)))
                    h.silent(game)
                    game.sendall(self.chat(h,'456',opposite))
                    self.display(h,game,identity,'456',opposite,simplified)
                    with closing(sqlite3.connect(database)) as db:
                        stored=db.execute('select name_bytes,name_codepage from recovered_characters where id=?',(identity,)).fetchone()
                        self.assertEqual(stored,(name.encode(encoding),int(encoding[2:])))
                        self.assertEqual(db.execute('pragma quick_check').fetchone(),('ok',))

    def test_same_scene_chat_converts_in_both_directions(self):
        w,h=self.harness()
        with h.server() as server,ExitStack() as stack:
            tw,tw_id=self.enter(w,h,stack,server,world.dual.OWNER,world.dual.HEROES[0],'zh-TW')
            cn,cn_id=self.enter(w,h,stack,server,world.dual.OTHER,world.dual.HEROES[1],'zh-CN')
            h.await_marker(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED',2)
            tw.sendall(self.chat(h,'漢字遊戲','cp950'))
            self.display(h,tw,tw_id,'漢字遊戲','cp950',False)
            self.display(h,cn,tw_id,'汉字游戏','cp936',True)
            cn.sendall(self.chat(h,'欢迎游戏','cp936'))
            self.display(h,tw,cn_id,'歡迎遊戲','cp950',False)
            self.display(h,cn,cn_id,'欢迎游戏','cp936',True)
            h.silent(tw)
            h.silent(cn)

    def test_name_prefix_is_owned_and_long_chinese_remains_valid(self):
        w,h=self.harness()
        with h.server() as server,ExitStack() as stack:
            tw,identity=self.enter(w,h,stack,server,world.dual.OWNER,b'LongPlayerName','zh-TW')
            h.await_marker(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED',1)
            tw.sendall(self.chat(h,'OtherPlayer: 123','cp950'))
            self.display(h,tw,identity,'OtherPlayer: 123','cp950',False)
            tw.sendall(self.chat(h,'漢'*120,'cp950'))
            # 14-byte name + separator consumes 16 of the native 254-byte bound.
            self.display(h,tw,identity,'漢'*119,'cp950',False)
            tw.sendall(self.chat(h,'still-connected','cp950'))
            self.display(h,tw,identity,'still-connected','cp950',False)

    def test_unrepresentable_recipient_character_keeps_chat_connected(self):
        w,h=self.harness()
        with h.server() as server,ExitStack() as stack:
            tw,tw_id=self.enter(w,h,stack,server,world.dual.OWNER,world.dual.HEROES[0],'zh-TW')
            cn,cn_id=self.enter(w,h,stack,server,world.dual.OTHER,world.dual.HEROES[1],'zh-CN')
            h.await_marker(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED',2)
            tw.sendall(self.chat(h,'遊戲‧','cp950'))
            self.display(h,tw,tw_id,'遊戲‧','cp950',False)
            self.display(h,cn,tw_id,'游戏?','cp936',True)
            cn.sendall(self.chat(h,'欢迎游戏','cp936'))
            self.display(h,tw,cn_id,'歡迎遊戲','cp950',False)
            self.display(h,cn,cn_id,'欢迎游戏','cp936',True)
            h.silent(tw)
            h.silent(cn)

    def test_captured_original_client_chat_wire_routes_to_both_languages(self):
        w,h=self.harness()
        source=world.dual.ROOT/'artifacts/runs/native-ui-chat-language-20260923-01/crypto-private'
        plain=(source/'packet-1803.plain.bin').read_bytes()
        wire=(source/'packet-1803.wire.bin').read_bytes()
        self.assertEqual(hashlib.sha256(plain).hexdigest(),
            '33c8ad06733951011b36d4c9324f230c84fd32a4240e36da3a6ab0d393afb481')
        self.assertEqual(len(plain),54)
        self.assertEqual(plain[2],0x2f)
        self.assertEqual(plain[3:5],(51).to_bytes(2,'little'))
        self.assertEqual(plain[-1],sum(value+0x3c for value in plain[:-1])&255)
        self.assertEqual(h.frame(plain[2],plain[3:-1]),wire)
        self.assertEqual(plain[9:-2].decode('cp950'),
            '遊戲邏輯及原客戶端的技能書使用流程尚未接通a')
        with h.server() as server,ExitStack() as stack:
            tw,tw_id=self.enter(w,h,stack,server,world.dual.OWNER,world.dual.HEROES[0],'zh-TW')
            cn,_=self.enter(w,h,stack,server,world.dual.OTHER,world.dual.HEROES[1],'zh-CN')
            h.await_marker(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED',2)
            tw.sendall(wire)
            self.display(h,tw,tw_id,'遊戲邏輯及原客戶端的技能書使用流程尚未接通a','cp950',False)
            self.display(h,cn,tw_id,'游戏逻辑及原客户端的技能书使用流程尚未接通a','cp936',True)
            h.silent(tw)
            h.silent(cn)

    def test_chat_and_movement_coalesced_in_one_tcp_write(self):
        w,h=self.harness()
        with h.server() as server,ExitStack() as stack:
            tw,tw_id=self.enter(w,h,stack,server,world.dual.OWNER,world.dual.HEROES[0],'zh-TW')
            cn,_=self.enter(w,h,stack,server,world.dual.OTHER,world.dual.HEROES[1],'zh-CN')
            h.await_marker(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED',2)
            tw.sendall(movement_wire(18,12,1)+self.chat(h,'漢字遊戲','cp950'))
            self.assertEqual(h.read_frame(tw,0x5d,5)[3],1)
            self.display(h,tw,tw_id,'漢字遊戲','cp950',False)
            self.display(h,cn,tw_id,'汉字游戏','cp936',True)
            with closing(sqlite3.connect(server.database)) as db:
                self.assertEqual(db.execute('SELECT scene,x,y FROM recovered_positions WHERE character_id=?',
                    (tw_id,)).fetchone(),(15,18,12))
            h.silent(tw)
            h.silent(cn)

    def test_chat_and_movement_in_one_world_frame_ack_first(self):
        w,h=self.harness()
        with h.server() as server,ExitStack() as stack:
            tw,tw_id=self.enter(w,h,stack,server,world.dual.OWNER,world.dual.HEROES[0],'zh-TW')
            cn,_=self.enter(w,h,stack,server,world.dual.OTHER,world.dual.HEROES[1],'zh-CN')
            h.await_marker(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED',2)
            legacy='漢字遊戲'.encode('cp950')
            chat=b'\x2f'+(len(legacy)+8).to_bytes(2,'little')+bytes(4)+legacy+b'\0'
            tw.sendall(h.frame(0x2e,bytes((18,0,12,0,1,0))+chat))
            self.assertEqual(h.read_frame(tw,0x5d,5)[3],1)
            self.display(h,tw,tw_id,'漢字遊戲','cp950',False)
            self.display(h,cn,tw_id,'汉字游戏','cp936',True)
            with closing(sqlite3.connect(server.database)) as db:
                self.assertEqual(db.execute('SELECT scene,x,y FROM recovered_positions WHERE character_id=?',
                    (tw_id,)).fetchone(),(15,18,12))
            h.silent(tw)
            h.silent(cn)

    def test_invalid_chat_cannot_commit_coalesced_movement(self):
        w,h=self.harness()
        with h.server() as server,ExitStack() as stack:
            tw,tw_id=self.enter(w,h,stack,server,world.dual.OWNER,world.dual.HEROES[0],'zh-TW')
            cn,_=self.enter(w,h,stack,server,world.dual.OTHER,world.dual.HEROES[1],'zh-CN')
            h.await_marker(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED',2)
            malformed=b'\x2f'+(9).to_bytes(2,'little')+bytes(4)+b'\x81\0'
            tw.sendall(h.frame(0x2e,bytes((18,0,12,0,1,0))+malformed))
            h.closed(tw)
            h.silent(cn)
            with closing(sqlite3.connect(server.database)) as db:
                self.assertIsNone(db.execute('SELECT x,y FROM recovered_positions WHERE character_id=?',
                    (tw_id,)).fetchone())

    def test_invalid_later_frame_preserves_prior_committed_movement(self):
        w,h=self.harness()
        with h.server() as server,ExitStack() as stack:
            tw,tw_id=self.enter(w,h,stack,server,world.dual.OWNER,world.dual.HEROES[0],'zh-TW')
            h.await_marker(server.root,'WORLD_INITIALIZER_TAIL_ACCEPTED',1)
            malformed=h.frame(0x2f,(9).to_bytes(2,'little')+bytes(4)+b'\x81\0')
            tw.sendall(movement_wire(18,12,1)+malformed)
            self.assertEqual(h.read_frame(tw,0x5d,5)[3],1)
            h.closed(tw)
            with closing(sqlite3.connect(server.database)) as db:
                self.assertEqual(db.execute('SELECT scene,x,y FROM recovered_positions WHERE character_id=?',
                    (tw_id,)).fetchone(),(15,18,12))


if __name__=='__main__':
    unittest.main()
