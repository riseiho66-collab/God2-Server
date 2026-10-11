"""Own loopback server + original-code generated 2E, not live client acceptance."""
import json
import unittest
from collections import deque
from contextlib import closing
from pathlib import Path
import sqlite3
import struct
import tempfile

import test_recovered_world_entry_server as world
from test_current_world_ready_builder import current_world_ready_wire
from test_current_movement import movement_wire


class RecoveredMovementServerTests(unittest.TestCase):
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
            result['development']['recovered_navigation']=str(world.dual.ROOT/'artifacts/world-atlas/indoor-2-15.json')
            return result
        h.configuration=configuration
        return w,h

    def ready(self,w,h,game,identity,coordinates=None):
        h.game_ready(game)
        game.sendall(h.frame(0x1a,world.dual.selection_payload(0)))
        w.selected(h,game,identity,coordinates)
        game.sendall(current_world_ready_wire(identity))
        w.state_candidate(h,game)

    def ack(self,h,game,slot):
        self.assertEqual(h.read_frame(game,0x5d,5)[3],slot)

    def positions(self,database):
        with closing(sqlite3.connect(database)) as db:
            return db.execute('SELECT character_id,area,scene,x,y,revision FROM recovered_positions ORDER BY character_id').fetchall()

    def test_original_movement_fragmentation_batch_and_ring_wrap(self):
        w,h=self.harness()
        with h.server() as server:
            endpoint,identity=w.create(h,server)
            before=h.snapshot(server.database)
            with h.connect(endpoint) as game:
                self.ready(w,h,game,identity)
                wire=movement_wire(18,12,1,0)
                game.sendall(wire[:-1]);h.silent(game)
                self.assertEqual(self.positions(server.database),[])
                self.assertEqual(h.marker_count(server.root,'RECOVERED_MOVEMENT_ACCEPTED'),0)
                game.sendall(wire[-1:]);self.ack(h,game,1)
                # One original flush containing two logical records.
                game.sendall(movement_wire(0,0,0,0x5a,[(17,13,2),(18,12,3)]))
                self.ack(h,game,2);self.ack(h,game,3)
                # Two complete wire frames can arrive in the same TCP write.
                game.sendall(movement_wire(17,13,4,0xa5)+movement_wire(18,12,5,0xff))
                self.ack(h,game,4);self.ack(h,game,5)
                for step in range(6,43):
                    x,y=(18,12) if step&1 else (17,13)
                    game.sendall(movement_wire(x,y,step%40,step))
                    self.ack(h,game,step%40)
            h.unchanged(server.database,before)
            row=self.positions(server.database)
            self.assertEqual(len(row),1)
            self.assertEqual(row[0][:5],(identity,2,15,17,13))
            self.assertGreater(row[0][5],1)
            self.assertIn('position persistence enabled',h.logs(server.root))

    def test_town_application_entry_movement_and_reconnect(self):
        self.check_town_restart(False)

    def test_physical_npc_close_and_ground_move_share_one_frame(self):
        w,h=self.harness()
        original=h.configuration
        def configuration(*args,**kwargs):
            config=original(*args,**kwargs)
            config['development']['recovered_navigation']=str(
                world.dual.ROOT/'artifacts/world-atlas/town-2-4.json')
            config['development']['diagnostic_town']={
                'center_x':4,'center_y':3,'x':110,'y':70,
                'source_consensus':True,'spawn_guides':True}
            config['database']['path']=str(args[0]/'town-diagnostic-accounts.db')
            return config
        h.configuration=configuration
        body=bytearray(w.body)
        body[24:26]=(2|(4<<6)).to_bytes(2,'little')
        body[28:32]=((110<<2)|(70<<17)).to_bytes(4,'little')
        w.body=bytes(body)
        with h.server() as server:
            endpoint,identity=w.create(h,server)
            with h.connect(endpoint) as game:
                self.ready(w,h,game,identity,(110,70))
                game.sendall(h.frame(0x30,b'\0'))
                h.read_frame(game,0x72,45)
                game.sendall(h.frame(0x37,(1607).to_bytes(4,'little')))
                h.read_frame(game,0x7a,30)
                # Decrypted current-client frame from the physical click-away run:
                # 86 01 00 81 1a | 2e 6e 00 47 00 01 c2.
                game.sendall(h.frame(0x86,bytes.fromhex('0100811a2e6e00470001c2')))
                self.ack(h,game,1)
                game.sendall(h.frame(0x37,(1607).to_bytes(4,'little')))
                dialogue=h.read_frame(game,0x7a,30)[2:-1]
                self.assertEqual(int.from_bytes(dialogue[5:7],'little'),0x1235)
                h.silent(game)
            self.assertEqual(self.positions(server.database)[0][2:5],(4,110,71))
            logs=h.logs(server.root)
            self.assertIn('DIAGNOSTIC_QUEST_CANCEL_WITH_MOVEMENT_ACCEPTED',logs)
            self.assertNotIn('Recovered world policy or response rejected',logs)

    def test_town_cross_window_restart_preserves_location(self):
        self.check_town_restart(True)

    def test_first_saved_town_step_can_trigger_door(self):
        w,h=self.harness()
        navigation=world.dual.ROOT/'artifacts/world-atlas/town-2-4.json'
        original=h.configuration
        def configuration(*args,**kwargs):
            config=original(*args,**kwargs)
            config['development']['recovered_navigation']=str(navigation)
            config['development']['diagnostic_town']={
                'center_x':4,'center_y':3,'x':86,'y':71,
                'source_consensus':True,'spawn_guides':True,'door_routes':True,
                'indoor_navigation':str(world.dual.ROOT/'artifacts/world-atlas/indoor-2-15.json')}
            return config
        h.configuration=configuration
        body=bytearray(w.body)
        body[24:26]=(2|(4<<6)).to_bytes(2,'little')
        body[28:32]=((86<<2)|(71<<17)).to_bytes(4,'little')
        w.body=bytes(body)
        with tempfile.TemporaryDirectory(prefix='god2-first-door-') as directory:
            database=Path(directory)/'town-diagnostic-accounts.db'
            with h.server(database=database) as server:
                endpoint,identity=w.create(h,server)
                self.assertEqual(self.positions(database),[])
                with h.connect(endpoint) as game:
                    self.ready(w,h,game,identity,(86,71))
                    game.sendall(h.frame(0x30,b'\0'))
                    guides=h.read_frame(game,0x72,45)[2:-1]
                    self.assertEqual(int.from_bytes(guides[1:3],'little'),1606)
                    self.assertEqual(int.from_bytes(guides[22:24],'little'),1607)
                    self.assertEqual(self.positions(database),[])
                    game.sendall(movement_wire(86,70,1))
                    self.ack(h,game,1)
                    self.assertEqual(self.positions(database),[(identity,2,4,86,70,1)])
                    game.sendall(h.frame(0x30,b'\0'))
                    transition=h.read_frame(game,0x61,12)
                    self.assertEqual(transition[2:-1],bytes.fromhex('61c203000042002600'))
                    self.assertEqual(self.positions(database),[(identity,2,15,16,19,2)])
                    game.sendall(h.frame(0x1c,b'\x01\0\0\0'))
                    h.silent(game)
                self.assertIn('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED',h.logs(server.root))

    def test_fresh_town_spawn_and_npc_without_saved_position(self):
        w,h=self.harness()
        def read_logical(game):
            header=h.receive(game,2)
            size=int.from_bytes(header,'little')
            self.assertTrue(4<=size<=0xa03)
            plain=bytearray(header)
            previous=0
            for index,value in enumerate(h.receive(game,size-2)):
                previous=((value+3-previous)&255)^h.crypto_key[index&255]
                plain.append(previous)
            self.assertEqual(plain[-1],sum(x+0x3c for x in plain[:-1])&255)
            return plain[2:-1]
        original=h.configuration
        def configuration(*args,**kwargs):
            config=original(*args,**kwargs)
            config['development']['recovered_navigation']=str(
                world.dual.ROOT/'artifacts/world-atlas/town-2-4.json')
            for flag in ('diagnostic_battle_transition','diagnostic_battle_participants',
                         'diagnostic_battle_player_appearance','diagnostic_battle_animations',
                         'diagnostic_battle_skill_seed','diagnostic_battle_skill_settlement',
                         'diagnostic_battle_terminal','diagnostic_battle_resources',
                         'diagnostic_battle_after_movement'):
                config['development'][flag]=True
            config['development']['diagnostic_town']={
                'center_x':4,'center_y':3,'x':110,'y':70,
                'source_consensus':True,'spawn_guides':True,'quest_progress':True,
                'map_probe':True,'scene_probe':True,'scene_indoor_probe':True,
                'scene_indoor_transfer':True,'battle_after_quest':True,
                'indoor_navigation':str(world.dual.ROOT/'artifacts/world-atlas/indoor-2-15.json')}
            return config
        h.configuration=configuration
        body=bytearray(w.body)
        body[24:26]=(2|(4<<6)).to_bytes(2,'little')
        body[28:32]=((110<<2)|(70<<17)).to_bytes(4,'little')
        w.body=bytes(body)
        with tempfile.TemporaryDirectory(prefix='god2-fresh-town-') as directory:
            database=Path(directory)/'town-diagnostic-accounts.db'
            with h.server(database=database) as server:
                from tools.strike_lab.import_native_quests import import_catalog
                from tools.strike_lab.import_native_catalog import import_catalog as import_maps
                with closing(sqlite3.connect(database)) as db:
                    self.assertEqual(import_maps(db,world.dual.ROOT.parent/'God2')['rows'],144)
                    imported=import_catalog(db,world.dual.ROOT.parent/'God2')
                self.assertEqual(imported['descriptions'],2014)
                endpoint,identity=w.create(h,server)
                with h.connect(endpoint) as game:
                    self.ready(w,h,game,identity,(110,70))
                    game.sendall(h.frame(0x30,b'\0'))
                    guides=h.read_frame(game,0x72,45)[2:-1]
                    self.assertEqual(int.from_bytes(guides[1:3],'little'),1606)
                    self.assertEqual(int.from_bytes(guides[22:24],'little'),1607)
                    self.assertEqual(self.positions(database),[])
                    with closing(sqlite3.connect(database)) as db:
                        self.assertEqual(db.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots '
                            'WHERE character_id=? AND slot=0',(identity,)).fetchone(),(0,0,1))
                    game.sendall(h.frame(0x37,(1606).to_bytes(4,'little')))
                    dialogue=h.read_frame(game,0x7a,30)[2:-1]
                    self.assertEqual(int.from_bytes(dialogue[5:7],'little'),0x1234)
                    self.assertEqual(int.from_bytes(dialogue[7:9],'little'),894)
                    self.assertEqual(self.positions(database),[])
                    # Original UI can flush confirmation and the next NPC click
                    # as two logical records inside one encrypted world frame.
                    game.sendall(h.frame(0x85,bytes.fromhex('341202009a00')+
                                         b'\x37'+(1607).to_bytes(4,'little')))
                    journal=h.read_frame(game,0xdb,16)[2:-1]
                    self.assertEqual(int.from_bytes(journal[9:13],'little'),0x10001)
                    with closing(sqlite3.connect(database)) as db:
                        self.assertEqual(db.execute('SELECT stage,journal_description,revision '
                            'FROM diagnostic_town_guide_progress WHERE character_id=?',
                            (identity,)).fetchone(),(1,1,1))
                    self.assertEqual(self.positions(database),[])
                    dialogue=h.read_frame(game,0x7a,30)[2:-1]
                    self.assertEqual(int.from_bytes(dialogue[5:7],'little'),0x1235)
                    self.assertEqual(int.from_bytes(dialogue[7:9],'little'),899)
                    game.sendall(h.frame(0x85,bytes.fromhex('351202009a00')))
                    journal=h.read_frame(game,0xdb,16)[2:-1]
                    self.assertEqual(int.from_bytes(journal[9:13],'little'),0x20001)
                    game.sendall(h.frame(0x37,(1606).to_bytes(4,'little')))
                    dialogue=h.read_frame(game,0x7a,30)[2:-1]
                    self.assertEqual(int.from_bytes(dialogue[5:7],'little'),0x1236)
                    self.assertEqual(int.from_bytes(dialogue[7:9],'little'),896)
                    game.sendall(h.frame(0x85,bytes.fromhex('361202009a00')))
                    reward=h.read_frame(game,0xdb,21)[2:-1]
                    self.assertEqual(int.from_bytes(reward[9:13],'little'),0)
                    self.assertEqual(reward[13:18],bytes.fromhex('41c1150001'))
                    with closing(sqlite3.connect(database)) as db:
                        self.assertEqual(db.execute('SELECT stage,journal_description,revision '
                            'FROM diagnostic_town_guide_progress WHERE character_id=?',
                            (identity,)).fetchone(),(3,0,3))
                        self.assertEqual(db.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots '
                            'WHERE character_id=? AND slot=0',(identity,)).fetchone(),(5569,1,2))
                        self.assertEqual(db.execute('SELECT item_id,count,slot_revision,progress_revision '
                            'FROM diagnostic_town_guide_reward WHERE character_id=?',
                            (identity,)).fetchone(),(5569,1,2,3))
                    self.assertEqual(self.positions(database),[])
                    h.silent(game)
                self.assertIn('owned_initial_position_checked',h.logs(server.root))
            with closing(sqlite3.connect(database)) as db:
                saved={name:db.execute('SELECT * FROM '+name).fetchall() for name in (
                    'diagnostic_town_guide_progress','diagnostic_inventory_slots',
                    'diagnostic_town_guide_reward','recovered_positions')}
            with h.server(database=database,registration=False) as restarted:
                with h.connect(restarted.endpoint) as login:
                    endpoint=h.login(login)
                    self.assertEqual(h.list_characters(login)[3],1)
                    with h.connect(endpoint) as game:
                        self.ready(w,h,game,identity,(110,70))
                        game.sendall(h.frame(0x30,b'\0'))
                        restored=h.read_frame(game,0x72,245)[2:-1]
                        self.assertEqual(int.from_bytes(restored[1:3],'little'),1606)
                        self.assertEqual(int.from_bytes(restored[22:24],'little'),1607)
                        self.assertEqual(int.from_bytes(restored[51:55],'little'),0)
                        self.assertEqual(restored[237:242],bytes.fromhex('41c1150001'))
                        game.sendall(h.frame(0x85,bytes.fromhex('361202009a00')))
                        h.closed(game)
                with closing(sqlite3.connect(database)) as db:
                    self.assertEqual(db.execute('PRAGMA quick_check').fetchone(),('ok',))
                    for name,rows in saved.items():
                        self.assertEqual(db.execute('SELECT * FROM '+name).fetchall(),rows,name)
                # The reward can be used before the first movement save, even
                # after a cold restart; the transfer creates revision 1.
                with h.connect(restarted.endpoint) as login:
                    endpoint=h.login(login)
                    self.assertEqual(h.list_characters(login)[3],1)
                    with h.connect(endpoint) as game:
                        self.ready(w,h,game,identity,(110,70))
                        game.sendall(h.frame(0x30,b'\0'))
                        h.read_frame(game,0x72,245)
                        game.sendall(h.frame(0x25,bytes.fromhex('c1150000')))
                        transition=h.read_frame(game,0x61,12)
                        self.assertEqual(transition[2:-1],bytes.fromhex('61c203000046001a00'))
                        self.assertEqual(self.positions(database),[(identity,2,15,17,13,1)])
                        game.sendall(h.frame(0x1c,b'\x01\0\0\0'))
                        h.silent(game)
                self.assertIn('DIAGNOSTIC_TOWN_SCENE_CONTEXT_ACCEPTED',h.logs(restarted.root))
            body=bytearray(w.body)
            body[24:26]=(2|(15<<6)).to_bytes(2,'little')
            body[28:32]=((17<<2)|(13<<17)|2).to_bytes(4,'little')
            w.body=bytes(body)
            with h.server(database=database,registration=False) as indoor_restarted:
                with h.connect(indoor_restarted.endpoint) as login:
                    endpoint=h.login(login)
                    self.assertEqual(h.list_characters(login)[3],1)
                    with h.connect(endpoint) as game:
                        self.ready(w,h,game,identity,(17,13))
                        game.sendall(movement_wire(18,12,1))
                        self.ack(h,game,1)
                        self.assertEqual(self.positions(database),[(identity,2,15,18,12,2)])
                        game.sendall(h.frame(0x30,b'\0'))
                        header=h.receive(game,2)
                        length=int.from_bytes(header,'little')
                        self.assertTrue(12<=length<=0xa03)
                        encrypted=h.receive(game,length-2)
                        plain=bytearray(header)
                        previous=0
                        for index,value in enumerate(encrypted):
                            previous=((value+3-previous)&255)^h.crypto_key[index&255]
                            plain.append(previous)
                        self.assertEqual(plain[-1],sum(x+0x3c for x in plain[:-1])&255)
                        self.assertEqual(plain[2],0xdb)
                        self.assertEqual(plain[-6:-1],bytes.fromhex('41c1150001'))
                        game.sendall(h.frame(0x30,b'\0'))
                        header=h.receive(game,2)
                        length=int.from_bytes(header,'little')
                        encrypted=h.receive(game,length-2)
                        plain=bytearray(header)
                        previous=0
                        for index,value in enumerate(encrypted):
                            previous=((value+3-previous)&255)^h.crypto_key[index&255]
                            plain.append(previous)
                        self.assertEqual(plain[-1],sum(x+0x3c for x in plain[:-1])&255)
                        self.assertEqual(plain[-10:-1],b'\x82'+bytes(8))
                        game.sendall(h.frame(0x36,bytes(8)))
                        vitals_header=h.receive(game,2)
                        vitals_size=int.from_bytes(vitals_header,'little')
                        self.assertTrue(124<=vitals_size<=0xa03)
                        encrypted=h.receive(game,vitals_size-2)
                        vitals=bytearray(vitals_header)
                        previous=0
                        for index,value in enumerate(encrypted):
                            previous=((value+3-previous)&255)^h.crypto_key[index&255]
                            vitals.append(previous)
                        self.assertEqual(vitals[-1],sum(x+0x3c for x in vitals[:-1])&255)
                        self.assertEqual(vitals[2:5],bytes.fromhex('870180'))
                        bulk=vitals.index(0x88,5)
                        self.assertLessEqual(bulk+121,len(vitals)-1)
                        self.assertEqual(int.from_bytes(vitals[bulk+5:bulk+9],'little'),100)
                        self.assertEqual(int.from_bytes(vitals[bulk+9:bulk+13],'little'),50)
                        with closing(sqlite3.connect(database)) as db:
                            self.assertEqual(db.execute('SELECT count(*) FROM battle_reservations').fetchone(),(1,))
                            self.assertEqual(db.execute('SELECT count(*) FROM battle_settlements').fetchone(),(0,))
                            self.assertEqual(db.execute('SELECT hp,max_hp,mp,max_mp,design_id '
                                'FROM character_resources WHERE character_id=?',(identity,)).fetchone(),
                                (100,120,50,80,'CUSTOM-0012'))
                        def command(action,enemy):
                            return h.frame(0x35,struct.pack('<4BHHII',0,action,0,0,0,enemy,0,0))
                        game.sendall(command(0x0b,0))
                        h.silent(game)
                        game.sendall(command(1,1))
                        damage=read_logical(game)
                        self.assertEqual(damage[0],0x83)
                        with closing(sqlite3.connect(database)) as db:
                            self.assertEqual(db.execute('SELECT count(*) FROM battle_settlements').fetchone(),(1,))
                        game.sendall(command(0x0b,1))
                        result=read_logical(game)
                        self.assertEqual((result[0],len(result)),(0x89,57))
                        # Native world return resets the movement ring to slot 0.
                        game.sendall(movement_wire(17,13,1))
                        self.ack(h,game,1)
                        self.assertEqual(self.positions(database),[(identity,2,15,17,13,3)])
                self.assertEqual(self.positions(database),[(identity,2,15,17,13,3)])
            with closing(sqlite3.connect(database)) as db:
                settled={name:db.execute('SELECT * FROM '+name).fetchall() for name in (
                    'diagnostic_town_guide_progress','diagnostic_inventory_slots',
                    'diagnostic_town_guide_reward','recovered_positions',
                    'character_resources','character_experience','battle_reservations',
                    'battle_settlements')}
                self.assertEqual(len(settled['battle_settlements']),1)
                self.assertEqual(db.execute('PRAGMA integrity_check').fetchall(),[('ok',)])
            with h.server(database=database,registration=False) as completed_restarted:
                with h.connect(completed_restarted.endpoint) as login:
                    endpoint=h.login(login)
                    self.assertEqual(h.list_characters(login)[3],1)
                    with h.connect(endpoint) as game:
                        self.ready(w,h,game,identity,(17,13))
                        game.sendall(h.frame(0x30,b'\0'))
                        restored=read_logical(game)
                        self.assertEqual((len(restored),restored[:2]),(200,bytes.fromhex('db04')))
                        self.assertEqual(restored[-5:],bytes.fromhex('41c1150001'))
                with closing(sqlite3.connect(database)) as db:
                    for name,rows in settled.items():
                        self.assertEqual(db.execute('SELECT * FROM '+name).fetchall(),rows,name)
                    self.assertEqual(db.execute('PRAGMA integrity_check').fetchall(),[('ok',)])

    def check_town_restart(self,consensus):
        w,h=self.harness()
        navigation=world.dual.ROOT/'artifacts/world-atlas/town-2-4.json'
        source=json.loads(navigation.read_text())
        window=source['windows'][3*9+3]
        if consensus:
            from tools.strike_lab.town_probe_route import agreement_window
            window=agreement_window(source)
        cells=window['cells_hex']
        def available(x,y):
            offset=((y-window['origin_y'])*window.get('side',63)+x-window['origin_x'])*2
            return cells[offset:offset+2] in ('01','02')
        x,y=next((x,y) for y in range(63,84) for x in (range(105,124) if consensus else range(42,83))
                 if available(x,y) and available(x+1,y))
        original=h.configuration
        def configuration(*args,**kwargs):
            config=original(*args,**kwargs)
            config['development']['recovered_navigation']=str(navigation)
            config['development']['diagnostic_town']={'center_x':3,'center_y':3,'x':x,'y':y,'source_consensus':consensus}
            return config
        h.configuration=configuration
        # Same selected-frame oracle, with the independently recovered map fields.
        body=bytearray(w.body)
        body[24:26]=(2|(4<<6)).to_bytes(2,'little')
        body[28:32]=((x<<2)|(y<<17)).to_bytes(4,'little')
        w.body=bytes(body)
        with tempfile.TemporaryDirectory(prefix='god2-town-wire-') as directory:
            database=Path(directory)/'town-diagnostic-accounts.db'
            with h.server(database=database) as server:
                endpoint,identity=w.create(h,server)
                with h.connect(endpoint) as game:
                    self.ready(w,h,game,identity,(x,y))
                    game.sendall(movement_wire(x+1,y,1));self.ack(h,game,1)
                self.assertEqual(self.positions(database),[(identity,2,4,x+1,y,1)])
                with h.connect(endpoint) as game:
                    self.ready(w,h,game,identity,(x+1,y))
                    game.sendall(movement_wire(x,y,1));self.ack(h,game,1)
                self.assertEqual(self.positions(database),[(identity,2,4,x,y,2)])
                expected='CUSTOM-0019 source agreement gate' if consensus else 'fixed navigation window'
                self.assertIn('Town diagnostic: '+expected,h.logs(server.root))
                # Save a non-default coordinate before actually stopping the server.
                with h.connect(endpoint) as game:
                    self.ready(w,h,game,identity,(x,y))
                    game.sendall(movement_wire(x+1,y,1));self.ack(h,game,1)
                self.assertEqual(self.positions(database),[(identity,2,4,x+1,y,3)])
                saved=h.snapshot(database)
            with h.server(database=database,registration=False) as restarted:
                with h.connect(restarted.endpoint) as login:
                    endpoint=h.login(login)
                    listing=h.list_characters(login)
                    self.assertEqual(listing[3],1)
                    with h.connect(endpoint) as game:
                        self.ready(w,h,game,identity,(x+1,y))
                        self.assertEqual(self.positions(database),[(identity,2,4,x+1,y,3)])
                        game.sendall(movement_wire(x,y,1));self.ack(h,game,1)
                self.assertEqual(self.positions(database),[(identity,2,4,x,y,4)])
                h.unchanged(database,saved)

    def test_invalid_move_and_duplicate_never_get_success_ack(self):
        w,h=self.harness()
        with h.server() as server:
            endpoint,identity=w.create(h,server);before=h.snapshot(server.database)
            valid=movement_wire(18,12,1)
            cases=[movement_wire(18,12,2),movement_wire(18,12,40),movement_wire(19,13,1),
                   valid[:-1]+bytes([valid[-1]^1]),b'\xff\xff']
            for wire in cases:
                with self.subTest(wire=wire.hex()),h.connect(endpoint) as game:
                    self.ready(w,h,game,identity);game.sendall(wire);h.closed(game)
                self.assertEqual(self.positions(server.database),[])
            with h.connect(endpoint) as game:
                self.ready(w,h,game,identity)
                game.sendall(valid);self.ack(h,game,1)
                saved=self.positions(server.database)
                game.sendall(valid);h.closed(game)
                self.assertEqual(self.positions(server.database),saved)
            h.unchanged(server.database,before)

    def test_uninstalled_world_policy_rejects_before_position_commit(self):
        w,h=self.harness()
        with h.server() as server:
            endpoint,identity=w.create(h,server)
            before=h.snapshot(server.database)
            # Exact native85 fixture is independently checked through the C++
            # typed decoder in test_current_world_records. Item bytes are an
            # explicit synthetic request, not recovered inventory ownership.
            for suffix in (bytes.fromhex('85341202009aa5'),
                           bytes.fromhex('86efbe0010'),
                           bytes.fromhex('25341207ff')):
                with self.subTest(opcode=suffix[0]),h.connect(endpoint) as game:
                    self.ready(w,h,game,identity)
                    game.sendall(h.frame(0x2e,bytes((18,0,12,0,1,0xa5))+suffix))
                    h.closed(game)
                self.assertEqual(self.positions(server.database),[])
                h.unchanged(server.database,before)
            self.assertEqual(h.marker_count(server.root,'RECOVERED_MOVEMENT_ACCEPTED'),0)
            # Application installs world_records; unsupported policies reject
            # inside that handler, before committing the movement prefix.
            self.assertEqual(h.marker_count(server.root,'Recovered world policy or response rejected'),3)

    def test_reachable_blocked_neighbor_is_rejected(self):
        w,h=self.harness()
        grid=json.loads((world.dual.ROOT/'artifacts/world-atlas/indoor-2-15.json').read_text())['grid']
        cells=bytes.fromhex(grid['cells_hex']);side=grid['side']
        queue=deque([((17,13),[])])
        seen={(17,13)}
        path=blocked=None
        while queue and blocked is None:
            (x,y),steps=queue.popleft()
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    point=(x+dx,y+dy)
                    if not (0<=point[0]<side and 0<=point[1]<side):
                        continue
                    if cells[point[1]*side+point[0]]==0:
                        path,blocked=steps,point
                        break
                    if point not in seen:
                        seen.add(point);queue.append((point,steps+[point]))
                if blocked is not None:
                    break
        self.assertIsNotNone(blocked,'Native grid must contain a reachable obstacle boundary')
        with h.server() as server:
            endpoint,identity=w.create(h,server);before=h.snapshot(server.database)
            with h.connect(endpoint) as game:
                self.ready(w,h,game,identity)
                for step,(x,y) in enumerate(path,1):
                    game.sendall(movement_wire(x,y,step%40));self.ack(h,game,step%40)
                saved=self.positions(server.database)
                game.sendall(movement_wire(*blocked,(len(path)+1)%40));h.closed(game)
                self.assertEqual(self.positions(server.database),saved)
            h.unchanged(server.database,before)

    def test_world_tail_and_first_movement_coalescing(self):
        w,h=self.harness()
        with h.server() as server:
            endpoint,identity=w.create(h,server)
            for index,split in enumerate((None,1,9)):
                with self.subTest(split=split),h.connect(endpoint) as game:
                    h.game_ready(game)
                    game.sendall(h.frame(0x1a,world.dual.selection_payload(0)))
                    w.selected(h,game,identity,(17,13) if index==0 else (18,12))
                    tail=current_world_ready_wire(identity)
                    move=movement_wire(18,12,1)
                    if split is None:
                        game.sendall(tail+move)
                    else:
                        game.sendall(tail+move[:split])
                    if split is not None:
                        h.silent(game);game.sendall(move[split:])
                    self.ack(h,game,1)

    def test_duplicate_character_binding_does_not_evict_first_session(self):
        w,h=self.harness()
        with h.server() as server:
            endpoint,identity=w.create(h,server)
            with h.connect(endpoint) as first,h.connect(endpoint) as second:
                self.ready(w,h,first,identity)
                h.game_ready(second);second.sendall(h.frame(0x1a,world.dual.selection_payload(0)))
                h.closed(second)
                first.sendall(movement_wire(18,12,1,0));self.ack(h,first,1)
            with h.connect(endpoint) as reconnected:
                self.ready(w,h,reconnected,identity,(18,12))
                reconnected.sendall(movement_wire(18,12,1,255));self.ack(h,reconnected,1)

    def test_process_restart_restores_committed_position_and_new_ring(self):
        w,h=self.harness()
        with tempfile.TemporaryDirectory() as directory:
            database=Path(directory)/'position.db'
            with h.server(database=database) as server:
                endpoint,identity=w.create(h,server)
                with h.connect(endpoint) as game:
                    self.ready(w,h,game,identity)
                    game.sendall(movement_wire(18,12,1));self.ack(h,game,1)
                saved=self.positions(database)
                self.assertEqual(saved,[(identity,2,15,18,12,1)])
            with h.server(database=database,registration=False) as server:
                with h.connect(server.endpoint) as login:
                    endpoint=h.login(login);h.list_characters(login)
                    with h.connect(endpoint) as game:
                        self.ready(w,h,game,identity,(18,12))
                        self.assertEqual(self.positions(database),saved)
                        game.sendall(movement_wire(17,13,1));self.ack(h,game,1)
                self.assertEqual(self.positions(database),[(identity,2,15,17,13,2)])

    def test_database_failure_prevents_ack_and_position_mutation(self):
        w,h=self.harness()
        with h.server() as server:
            endpoint,identity=w.create(h,server)
            for operation in ('INSERT','UPDATE'):
                with self.subTest(operation=operation),h.connect(endpoint) as game:
                    self.ready(w,h,game,identity,(17,13))
                    if operation=='UPDATE':
                        game.sendall(movement_wire(17,13,1));self.ack(h,game,1)
                    saved=self.positions(server.database)
                    with closing(sqlite3.connect(server.database)) as db:
                        db.execute(f"CREATE TRIGGER deny_move BEFORE {operation} ON recovered_positions BEGIN SELECT RAISE(ABORT,'test write failure'); END")
                        db.commit()
                    slot=1 if operation=='INSERT' else 2
                    game.sendall(movement_wire(18,12,slot));h.closed(game)
                    self.assertEqual(self.positions(server.database),saved)
                    with closing(sqlite3.connect(server.database)) as db:
                        db.execute('DROP TRIGGER deny_move');db.commit()
            with h.connect(endpoint) as game:
                self.ready(w,h,game,identity,(17,13))
                game.sendall(movement_wire(18,12,1));self.ack(h,game,1)
            self.assertEqual(self.positions(server.database),[(identity,2,15,18,12,2)])

    def test_invalid_batched_move_does_not_commit_valid_prefix(self):
        w,h=self.harness()
        with h.server() as server:
            endpoint,identity=w.create(h,server)
            with h.connect(endpoint) as game:
                self.ready(w,h,game,identity)
                game.sendall(movement_wire(0,0,0,0xff,[(18,12,1),(30,30,2)]));h.closed(game)
            self.assertEqual(self.positions(server.database),[])
            with h.connect(endpoint) as game:
                self.ready(w,h,game,identity)
                game.sendall(movement_wire(18,12,1));self.ack(h,game,1)
            self.assertEqual(self.positions(server.database),[(identity,2,15,18,12,1)])


if __name__=='__main__':unittest.main()
