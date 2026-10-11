"""Isolated native-protocol socket proof for the first common-channel line."""
from contextlib import ExitStack, closing
import json
from pathlib import Path
import socket
import sqlite3
import subprocess
import tempfile
import time
import unittest

import test_recovered_dual_connection_server as dual
import test_town_player_visibility_server as presence
from test_current_world_ready_builder import current_world_ready_wire


ROOT = dual.ROOT
SOURCE = ROOT / 'artifacts/playtests/private-chain-endtoend-20260924-01'
SAVE_SOURCE = ROOT / 'artifacts/playtests/private-game-2598-20260923-01/town-diagnostic-accounts.db'
BINARY = ROOT / 'build-town-visibility/Release/god2-server.exe'


class TownChatWelcomeServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dual.RecoveredDualConnectionServerTests.setUpClass()

    def test_first_world_tick_emits_one_native_common_channel_line_per_language(self):
        h = dual.RecoveredDualConnectionServerTests('test_explicit_character_port_matches_05_and_accepts_g')
        self.assertTrue(BINARY.is_file())
        with tempfile.TemporaryDirectory(prefix='god2-town-welcome-') as temporary, ExitStack() as stack:
            root=Path(temporary)
            database=root/'town-diagnostic-accounts.db'
            with closing(sqlite3.connect(SAVE_SOURCE)) as source, closing(sqlite3.connect(database)) as target:
                source.backup(target)
                target.commit()
            config=json.loads((SOURCE/'server-config.json').read_text(encoding='utf-8'))
            config['server']['port']=h.unused_port()
            config['database']['path']=str(database)
            config['logging']['file']=str(root/'server.log')
            config['development']['diagnostic_town']['player_visibility']=True
            config['development']['diagnostic_remote_actor_language']=0
            config['development']['diagnostic_town']['chat_welcome']=True
            path=root/'config.json'
            path.write_text(json.dumps(config),encoding='utf-8')
            output=stack.enter_context((root/'stdout.log').open('wb'))
            process=subprocess.Popen([str(BINARY),'--config',str(path),'--run-for','40'],
                cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            stack.callback(h.stop,process)
            endpoint=('127.0.0.1',config['server']['port'])
            deadline=time.monotonic()+5
            while True:
                if process.poll() is not None:
                    output.flush()
                    self.fail('Isolated server exited: '+
                              (root/'stdout.log').read_text(encoding='utf-8',errors='replace')[-1500:])
                try:
                    probe=socket.create_connection(endpoint,timeout=.1)
                    probe.close()
                    break
                except OSError:
                    self.assertLess(time.monotonic(),deadline)
                    time.sleep(.025)

            for account,identity,flag,encoding,expected in (
                (b'codexlab',1,3,'cp950','歡迎來到仙界傳。'),
                (b'codexnew',2,2,'cp936','欢迎来到仙界传。')):
                with h.connect(endpoint) as login:
                    h.handshake(login)
                    password=b'labtest2345'
                    login.sendall(h.frame(*dual.credential(4,account,password)))
                    h.read_frame(login,0x1d,176)
                    h.read_frame(login,4,8)
                    address=h.read_frame(login,5,12)
                    game_port=int.from_bytes(address[9:11],'little')
                    h.read_frame(login,6,8)
                    h.read_frame(login,0x0a,20)
                    self.assertEqual(h.list_characters(login)[3],1)
                    with h.connect(('127.0.0.1',game_port)) as game:
                        h.handshake(game,game=True)
                        game.sendall(h.frame(*dual.credential(0,account,password)))
                        h.read_frame(game,0x1f,128)
                        game.sendall(h.frame(0x1a,dual.selection_payload(0)))
                        h.read_frame(game,2,26)
                        entry=h.read_frame(game,0x2a,40)
                        self.assertEqual(int.from_bytes(entry[3:5],'little')&0x3fff,identity)
                        game.sendall(current_world_ready_wire(identity,(4,flag)))
                        h.silent(game)
                        game.sendall(h.frame(0x30,b'\0'))
                        # A town may send NPC/journal records first; indoor may
                        # send the localized line as its first frame.
                        frames=[]
                        while len(frames)<3:
                            logical=presence.TownPlayerVisibilityServerTests.logical(h,game)
                            frames.append(logical)
                            if logical[0]==0x5c:break
                        self.assertEqual(sum(frame[0]==0x5c for frame in frames),1)
                        self.assertEqual(logical[0],0x5c)
                        self.assertEqual(int.from_bytes(logical[5:9],'little'),0x7fffffff)
                        self.assertEqual(logical[9],0x80 if flag==2 else 0)
                        self.assertEqual(logical[13:-1].decode(encoding),expected)
                        game.sendall(h.frame(0x30,b'\0'))
                        h.silent(game)
            with closing(sqlite3.connect(database)) as db:
                self.assertEqual(db.execute('pragma quick_check').fetchone(),('ok',))


if __name__=='__main__':
    unittest.main()
