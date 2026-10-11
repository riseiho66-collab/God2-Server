"""Isolated TCP/SQLite check of town door and battle player presence.

The 2E movement wire and world-ready tail execute the captured original client
builders. This is a socket test, not a claim about a rendered client window.
"""
from contextlib import ExitStack, closing
import json
import os
from pathlib import Path
import socket
import struct
import sqlite3
import subprocess
import tempfile
import time
import unittest

import test_recovered_dual_connection_server as dual
import test_recovered_chat_server as chat_helper
from test_current_movement import movement_wire
from test_current_world_ready_builder import current_world_ready_wire


ROOT = dual.ROOT
SOURCE = ROOT / 'artifacts/playtests/private-chain-endtoend-20260924-01'
SAVE_SOURCE = ROOT / 'artifacts/playtests/private-game-2598-20260923-01/town-diagnostic-accounts.db'
BINARY = Path(os.environ.get('GOD2_VISIBILITY_TEST_BINARY', ROOT / 'build-town-visibility/Release/god2-server.exe'))


class TownPlayerVisibilityServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dual.RecoveredDualConnectionServerTests.setUpClass()

    @staticmethod
    def logical(helper, peer):
        header = helper.receive(peer, 2)
        length = int.from_bytes(header, 'little')
        assert 4 <= length <= 0xa03
        payload = helper.receive(peer, length - 2)
        plain = bytearray(header)
        previous = 0
        for index, value in enumerate(payload):
            previous = ((value + 3 - previous) & 255) ^ helper.crypto_key[index & 255]
            plain.append(previous)
        assert plain[-1] == sum(value + 0x3c for value in plain[:-1]) & 255
        return bytes(plain[2:-1])

    def test_early_door_before_first_tick_keeps_presence(self):
        self.test_town_door_and_battle_leave_then_rejoin_indoor(early_transfer=True)

    def test_town_door_and_battle_leave_then_rejoin_indoor(self, early_transfer=False):
        self.assertTrue(BINARY.is_file())
        self.assertTrue(SAVE_SOURCE.is_file())
        h = dual.RecoveredDualConnectionServerTests('test_explicit_character_port_matches_05_and_accepts_g')
        with tempfile.TemporaryDirectory(prefix='god2-town-presence-') as temporary, ExitStack() as stack:
            root = Path(temporary)
            database = root / 'town-diagnostic-accounts.db'
            with closing(sqlite3.connect(SAVE_SOURCE)) as source, closing(sqlite3.connect(database)) as target:
                source.backup(target)
                target.execute('update recovered_positions set scene=4,x=85,y=71,revision=revision+1 where character_id=4')
                target.execute('update recovered_positions set x=88,y=75,revision=revision+1 where character_id=1')
                target.execute('update recovered_positions set scene=15,x=17,y=13,revision=revision+1 where character_id=2')
                target.commit()
                self.assertEqual(target.execute('pragma quick_check').fetchone(), ('ok',))
            config = json.loads((SOURCE / 'server-config.json').read_text(encoding='utf-8'))
            config['server']['port'] = h.unused_port()
            config['database']['path'] = str(database)
            config['logging']['file'] = str(root / 'server.log')
            config['development']['diagnostic_town']['player_visibility'] = True
            config['development']['diagnostic_remote_actor_language'] = 0
            path = root / 'config.json'
            path.write_text(json.dumps(config), encoding='utf-8')
            output = stack.enter_context((root / 'stdout.log').open('wb'))
            process = subprocess.Popen([str(BINARY), '--config', str(path), '--run-for', '90'],
                                       cwd=ROOT, stdout=output, stderr=subprocess.STDOUT,
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            stack.callback(h.stop, process)
            endpoint = ('127.0.0.1', config['server']['port'])
            deadline = time.monotonic() + 5
            while True:
                if process.poll() is not None:
                    output.flush()
                    self.fail('Isolated server exited before listening: ' +
                              (root / 'stdout.log').read_text(encoding='utf-8', errors='replace')[-1500:])
                try:
                    probe = socket.create_connection(endpoint, timeout=.1)
                    probe.close()
                    break
                except OSError:
                    self.assertLess(time.monotonic(), deadline, 'Isolated server did not listen')
                    time.sleep(.025)

            first_frame = {}
            names = {}

            def enter(account, identity):
                login = stack.enter_context(h.connect(endpoint))
                h.handshake(login)
                password = b'labtest2345'
                login.sendall(h.frame(*dual.credential(4, account, password)))
                h.read_frame(login, 0x1d, 176)
                h.read_frame(login, 4, 8)
                address = h.read_frame(login, 5, 12)
                game_port = int.from_bytes(address[9:11], 'little')
                h.read_frame(login, 6, 8)
                h.read_frame(login, 0x0a, 20)
                listing = h.list_characters(login)
                self.assertEqual(listing[3], 1)
                names[identity]=listing[5:20].split(b"\0")[0].decode("cp950")
                game = stack.enter_context(h.connect(('127.0.0.1', game_port)))
                h.handshake(game, game=True)
                game.sendall(h.frame(*dual.credential(0, account, password)))
                h.read_frame(game, 0x1f, 128)
                game.sendall(h.frame(0x1a, dual.selection_payload(0)))
                h.read_frame(game, 2, 26)
                entry = h.read_frame(game, 0x2a, 40)
                self.assertEqual(int.from_bytes(entry[3:5], 'little') & 0x3fff, identity)
                game.sendall(current_world_ready_wire(identity, (4, 3)))
                h.silent(game)
                # Native 961A0(6D,1) queues exactly 6D 00. The transport
                # route must keep the world session open for the next action.
                game.sendall(h.frame(0x6d, b'\0'))
                h.silent(game)
                if early_transfer and identity == 2:
                    for sequence, (x, y) in enumerate([(16,14),(15,15),(14,16),(14,17),(15,18),(16,19),(16,20)],1):
                        game.sendall(movement_wire(x,y,sequence))
                        self.assertEqual(self.logical(h,game)[:2],bytes((0x5d,sequence)))
                    self.assertEqual(self.logical(h,game)[0],0x61)
                    game.sendall(h.frame(0x30,b'\0'))
                    h.silent(game)
                    game.sendall(h.frame(0x1c,b'\x04\x00\x01\x00'))
                    h.silent(game)
                game.sendall(h.frame(0x30, b'\0'))
                if identity == 2 and not early_transfer:
                    # First admission restores all owned bag cells even without
                    # town journal progress. This is not a presence broadcast.
                    expected = b''.join(bytes((0x41, 0, 0, slot, 0)) for slot in range(30))
                    self.assertEqual(self.logical(h, game), expected)
                    with closing(sqlite3.connect(database)) as db:
                        self.assertEqual(db.execute(
                            'select slot,item_id,count from diagnostic_inventory_slots '
                            'where character_id=2 order by slot').fetchall(),
                            [(slot, 0, 0) for slot in range(30)])
                    h.silent(game)
                else:
                    try:
                        guide = self.logical(h, game)
                    except Exception as error:
                        raise AssertionError((root / 'server.log').read_text(encoding='utf-8', errors='replace')[-2200:]) from error
                    self.assertTrue(guide)
                    first_frame[identity] = guide
                return game

            indoor = enter(b'codexnew', 2)
            town = enter(b'codexlab', 1)
            if early_transfer:
                other=self.logical(h,indoor)
                self.assertEqual(other[0],0x6f)
                self.assertEqual(int.from_bytes(other[1:5],'little')&0xfff,1)
                peer=first_frame[1] if first_frame[1][0]==0x6f else self.logical(h,town)
                self.assertEqual(peer[0],0x6f)
                self.assertEqual(int.from_bytes(peer[1:5],'little')&0xfff,2)
                return
            traveler = enter(b'codexslow', 4)
            town_spawn = self.logical(h, town)
            traveler_spawn = first_frame[4] if first_frame[4][0] == 0x6f else self.logical(h, traveler)
            self.assertEqual(town_spawn[0], 0x6f)
            self.assertEqual(int.from_bytes(town_spawn[1:5], 'little') & 0xfff, 4)
            self.assertEqual(traveler_spawn[0], 0x6f)
            self.assertEqual(int.from_bytes(traveler_spawn[1:5], 'little') & 0xfff, 1)
            if first_frame[4][0] == 0x6f:
                self.assertEqual(self.logical(h, traveler)[0], 0x72)
            h.silent(indoor)
            traveler.sendall(h.frame(0x25, bytes.fromhex('c1150000')))
            self.assertEqual(self.logical(h, traveler), bytes.fromhex('3f0100'))
            h.silent(town)

            traveler.sendall(movement_wire(86, 70, 1))
            step = self.logical(h, traveler)
            self.assertEqual(step[0], 0x5d)
            self.assertEqual(step[1], 1)
            transition = self.logical(h, traveler)
            self.assertEqual(transition[0], 0x61)
            moved = self.logical(h, town)
            removed = self.logical(h, town)
            self.assertEqual((moved[0], removed[0]), (0x5e, 0x73))
            self.assertEqual(int.from_bytes(moved[1:3], 'little'), 4)
            self.assertEqual(int.from_bytes(removed[1:3], 'little'), 4)
            h.silent(indoor)

            traveler.sendall(h.frame(0x30, b'\0'))
            h.silent(traveler)
            traveler.sendall(h.frame(0x1c, b'\x04\x00\x01\x00'))
            h.silent(traveler)
            traveler.sendall(h.frame(0x30, b'\0'))
            destination_frames = (self.logical(h, traveler), self.logical(h, traveler))
            indoor_spawn = self.logical(h, indoor)
            self.assertEqual(indoor_spawn[0], 0x6f)
            self.assertEqual(int.from_bytes(indoor_spawn[1:5], 'little') & 0xfff, 4)
            self.assertEqual(sum(frame[0] == 0x6f for frame in destination_frames), 1)
            self.assertEqual(next(int.from_bytes(frame[1:5], 'little') & 0xfff
                                  for frame in destination_frames if frame[0] == 0x6f), 2)
            h.silent(town)
            traveler.sendall(chat_helper.RecoveredChatServerTests.chat(h, '漢字遊戲', 'cp950'))
            for recipient in (traveler, indoor):
                delivered = self.logical(h, recipient)
                self.assertEqual(delivered[0], 0x5c)
                self.assertEqual(int.from_bytes(delivered[5:9], 'little'), 4)
                self.assertEqual(delivered[13:-1].decode('cp950'), names[4]+': 漢字遊戲')
            h.silent(town)
            with closing(sqlite3.connect(database)) as db:
                self.assertEqual(db.execute('select area,scene,x,y from recovered_positions where character_id=4').fetchone(),
                                 (2, 15, 16, 19))
                self.assertEqual(db.execute('pragma quick_check').fetchone(), ('ok',))

            path = [(16, 18), (16, 17), (16, 16), (16, 15), (16, 14),
                    (16, 13), (17, 12), (18, 12)]
            for sequence, (x, y) in enumerate(path, 1):
                if sequence == 1:
                    # Native 9A is diagnostic-only. It may share one decoded
                    # world frame with a real movement and periodic tick.
                    diagnostic = bytes((0x06, 0, 0, 0, 0))
                    movement = bytes((0x2e,)) + struct.pack('<HHBB', x, y, sequence, 0xff)
                    traveler.sendall(h.frame(0x9a, diagnostic + movement + b'\x30\0'))
                else:
                    traveler.sendall(movement_wire(x, y, sequence))
                self.assertEqual(self.logical(h, traveler)[:2], bytes((0x5d, sequence)))
                peer_move = self.logical(h, indoor)
                self.assertEqual(peer_move[0], 0x5e)
                self.assertEqual(int.from_bytes(peer_move[1:3], 'little'), 4)
            traveler.sendall(h.frame(0x30, b'\0'))
            battle_entry = self.logical(h, traveler)
            # CUSTOM-0033: the current-client initial command-window byte is
            # 30 only for this quest-gated town battle.
            self.assertEqual(battle_entry[-9:], bytes.fromhex('8200000000001e0000'))
            battle_leave = self.logical(h, indoor)
            self.assertEqual(battle_leave[0], 0x73)
            self.assertEqual(int.from_bytes(battle_leave[1:3], 'little'), 4)
            h.silent(town)

            def command(action, enemy):
                return h.frame(0x35, struct.pack('<4BHHII', 0, action, 0, 0, 0, enemy, 0, 0))

            traveler.sendall(h.frame(0x36, bytes(8)))
            self.assertEqual(self.logical(h, traveler)[0], 0x87)
            traveler.sendall(command(0x0b, 0))
            h.silent(traveler)
            traveler.sendall(command(1, 1))
            self.assertEqual(self.logical(h, traveler)[0], 0x83)
            traveler.sendall(command(0x0b, 1))
            self.assertEqual(self.logical(h, traveler)[0], 0x89)
            traveler.sendall(h.frame(0x30, b'\0'))
            indoor_return = self.logical(h, indoor)
            self.assertEqual(indoor_return[0], 0x6f)
            self.assertEqual(int.from_bytes(indoor_return[1:5], 'little') & 0xfff, 4)
            traveler_return = self.logical(h, traveler)
            self.assertEqual(traveler_return[0], 0x6f)
            self.assertEqual(int.from_bytes(traveler_return[1:5], 'little') & 0xfff, 2)
            h.silent(town)

            traveler.sendall(h.frame(0x30, b'\0'))
            h.silent(traveler)
            traveler.sendall(h.frame(0x1c, b'\x04\x00\x01\x00'))
            h.silent(traveler)
            exit_path = [(17, 13), (16, 14), (15, 15), (14, 16),
                         (14, 17), (15, 18), (16, 19), (16, 20)]
            for sequence, (x, y) in enumerate(exit_path, 1):
                traveler.sendall(movement_wire(x, y, sequence))
                self.assertEqual(self.logical(h, traveler)[:2], bytes((0x5d, sequence)))
                peer_move = self.logical(h, indoor)
                self.assertEqual(peer_move[0], 0x5e)
                self.assertEqual(int.from_bytes(peer_move[1:3], 'little'), 4)
            self.assertEqual(self.logical(h, traveler)[0], 0x61)
            indoor_leave = self.logical(h, indoor)
            self.assertEqual(indoor_leave[0], 0x73)
            self.assertEqual(int.from_bytes(indoor_leave[1:3], 'little'), 4)
            traveler.sendall(h.frame(0x30, b'\0'))
            h.silent(traveler)
            traveler.sendall(h.frame(0x1c, b'\x04\x00\x01\x00'))
            h.silent(traveler)
            traveler.sendall(h.frame(0x30, b'\0'))
            town_return = self.logical(h, town)
            self.assertEqual(town_return[0], 0x6f)
            self.assertEqual(int.from_bytes(town_return[1:5], 'little') & 0xfff, 4)
            rejoined_frames = (self.logical(h, traveler), self.logical(h, traveler))
            self.assertEqual(sum(frame[0] == 0x6f for frame in rejoined_frames), 1)
            self.assertEqual(next(int.from_bytes(frame[1:5], 'little') & 0xfff
                                  for frame in rejoined_frames if frame[0] == 0x6f), 1)
            traveler.sendall(h.frame(0x25, bytes.fromhex('c1150000')))
            self.assertEqual(self.logical(h, traveler), bytes.fromhex('3f0100'))
            h.silent(indoor)
            town.sendall(chat_helper.RecoveredChatServerTests.chat(h, '歡迎遊戲', 'cp950'))
            for recipient in (town, traveler):
                delivered = self.logical(h, recipient)
                self.assertEqual(delivered[0], 0x5c)
                self.assertEqual(int.from_bytes(delivered[5:9], 'little'), 1)
                self.assertEqual(delivered[13:-1].decode('cp950'), names[1]+': 歡迎遊戲')
            h.silent(indoor)
            traveler.close()
            disconnected = self.logical(h, town)
            self.assertEqual(disconnected[0], 0x73)
            self.assertEqual(int.from_bytes(disconnected[1:3], 'little'), 4)
            reconnected = enter(b'codexslow', 4)
            respawn = self.logical(h, town)
            self.assertEqual(respawn[0], 0x6f)
            self.assertEqual(int.from_bytes(respawn[1:5], 'little') & 0xfff, 4)
            restored_frames = (first_frame[4], self.logical(h, reconnected))
            self.assertEqual(sum(frame[0] == 0x6f for frame in restored_frames), 1)
            self.assertEqual(next(int.from_bytes(frame[1:5], 'little') & 0xfff
                                  for frame in restored_frames if frame[0] == 0x6f), 1)
            reconnected.sendall(h.frame(0x30, b'\0'))
            h.silent(reconnected)  # The settled tutorial fight cannot restart.
            reconnected.sendall(movement_wire(86, 72, 1))
            self.assertEqual(self.logical(h, reconnected)[:2], bytes((0x5d, 1)))
            resumed_move = self.logical(h, town)
            self.assertEqual(resumed_move[0], 0x5e)
            self.assertEqual(int.from_bytes(resumed_move[1:3], 'little'), 4)
            h.silent(indoor)
            with closing(sqlite3.connect(database)) as db:
                self.assertEqual(db.execute('select count(*) from battle_settlements').fetchone(), (1,))
                self.assertEqual(db.execute('select area,scene,x,y from recovered_positions where character_id=4').fetchone(),
                                 (2, 4, 86, 72))
                self.assertEqual(db.execute('pragma quick_check').fetchone(), ('ok',))


if __name__ == '__main__':
    unittest.main()
