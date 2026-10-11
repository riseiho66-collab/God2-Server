"""Own-server TCP/restart checks with explicitly synthetic owned fixtures.

Requires the isolated native-catalog acceptance fixture; never writes its DB
or the live persistent database. This is transport evidence, not UI acceptance.
"""
from contextlib import ExitStack, closing
import json
import os
from pathlib import Path
import select
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

import test_recovered_dual_connection_server as dual
from test_current_world_ready_builder import current_world_ready_wire
import test_inventory_move_server as inventory
from test_current_movement import movement_wire

ROOT=dual.ROOT
sys.path.insert(0,str(ROOT))
SOURCE=ROOT/'artifacts/playtests/private-owned-companions-20260926-01'
BINARY=Path(os.environ.get('GOD2_OWNED_COMPANIONS_TEST_BINARY',ROOT/'build-town-visibility/Release/god2-server-native-results.exe'))

def clear(slot):return bytes((0x41,0,0,slot,0))
def pet_projection(row):
    slot,metadata,stats,_=row
    if not metadata:return clear(slot)
    return (clear(slot)+bytes((0x3b,1,slot,0,0))+metadata+
            bytes((0x41,metadata[0],metadata[1],slot,1))+stats)

class OwnedCompanionsServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file() or not (SOURCE/'town-diagnostic-accounts.db').is_file():
            raise AssertionError('Candidate and isolated owned-companion fixture required')
        dual.RecoveredDualConnectionServerTests.crypto_key=dual.key(ROOT)

    def test_selection_transfer_restart_lossless_restore(self):
        self.run_case()

    def test_native_only_suppresses_test_npcs_and_preserves_saved_data(self):
        self.run_case(native_only=True)

    def test_native_monster_policy_blocks_ready_indoor_fixture_without_reseeding(self):
        self.run_case(native_only=True,monster_only=True)

    def test_fresh_kunlun_spawn_movement_restart_and_owned_restore(self):
        self.run_case(native_only=True,kunlun_only=True)

    def test_owned_quest_journal_restore_restart_preserves_display_and_saved_state(self):
        self.run_case(native_only=True,kunlun_only=True,journal_only=True)

    def test_world_clock_initial_periodic_and_restart_synchronization(self):
        self.run_case(native_only=True,kunlun_only=True,clock_only=True)

    def run_case(self,native_only=False,monster_only=False,kunlun_only=False,journal_only=False,clock_only=False,pet1_only=False,deity_templates=False,deity_skill_catalog=False):
        helper=dual.RecoveredDualConnectionServerTests()
        decoder=inventory.InventoryMoveServerTests()
        with tempfile.TemporaryDirectory(prefix='god2-companions-tcp-') as tmp, ExitStack() as lifetime:
            here=Path(tmp);database=here/'town-diagnostic-accounts.db'
            with closing(sqlite3.connect((SOURCE/'town-diagnostic-accounts.db').resolve().as_uri()+'?mode=ro',uri=True)) as original:
                with closing(sqlite3.connect(database)) as copied:original.backup(copied)
            # Historical fixture used unrenderable key100. Correct this clone
            # only; preserve the old accepted evidence and all live saves.
            with closing(sqlite3.connect(database)) as prepared:
                rows=prepared.execute('select * from character_deities where character_id=4 order by row_key').fetchall()
                self.assertEqual([row[1] for row in rows],[100,101])
                prepared.execute('delete from character_deity_selection where character_id=4')
                prepared.execute('delete from character_deities where character_id=4')
                for row in rows:
                    values=list(row);key=row[1]-99 if deity_templates else row[1]+1;values[1]=key
                    for column,stride in ((2,19),(3,29),(4,4)):
                        raw=bytearray(values[column])
                        for offset in range(0,len(raw),stride):
                            raw[offset+1]=key if raw[offset+1]<128 else 256-key
                        values[column]=bytes(raw)
                    prepared.execute('insert into character_deities values(?,?,?,?,?,?,?,?,?)',values)
                prepared.execute('insert into character_deity_selection values(4,?,1)',(1 if deity_templates else 101,));prepared.commit()
            if deity_templates:
                from tools.strike_lab import import_native_deity_metadata as deity
                deity.install(database,deity.cached(ROOT/'artifacts/research/native-deity-metadata-20260927/records.json'))
            if deity_skill_catalog:
                self.assertTrue(deity_templates)
                from tools.strike_lab import import_native_skills
                from tools.strike_lab.owned_deity_skill_fixture import verified_catalog,assignments
                with closing(sqlite3.connect(database)) as prepared:
                    import_native_skills.import_catalog(prepared,ROOT.parent/'God2')
                    fixture=assignments(verified_catalog(prepared,ROOT.parent/'God2'))
                    template=prepared.execute('select * from character_deities where character_id=4 order by row_key limit 1').fetchone()
                    prepared.execute('delete from character_deity_selection where character_id=4')
                    prepared.execute('delete from character_deities where character_id=4')
                    for key,skills in fixture.items():
                        row=list(template);row[1]=key;row[4]=skills
                        for column in (2,3):
                            raw=bytearray(row[column]);raw[1]=key;row[column]=bytes(raw)
                        prepared.execute('insert into character_deities values(?,?,?,?,?,?,?,?,?)',row)
                    prepared.execute('insert into character_deity_selection values(4,1,1)');prepared.commit()
            config=json.loads((SOURCE/'server-config.json').read_text('utf-8'))
            if kunlun_only:
                config['world']={'new_character_birthplace':{'area':4,'scene':3,'kind':0,'x':126,'y':126,
                    'navigation':str(ROOT/'artifacts/world-atlas/kunlun-4-3.json'),'coordinate_authority':'CUSTOM-0040'}}
                with closing(sqlite3.connect(database)) as prepared:
                    prepared.execute('delete from recovered_positions where character_id=4');prepared.commit()
            if clock_only:config.setdefault('world',{})['clock']={'enabled':True,'sync_seconds':5}
            if monster_only:
                live_config=ROOT/'artifacts/releases/town-chat-welcome-20260924/server-config.json'
                config['development']=json.loads(live_config.read_text('utf-8'))['development']
                self.assertTrue(config['development']['diagnostic_battle_transition'])
                with closing(sqlite3.connect(database)) as prepared:
                    prepared.execute('update recovered_positions set area=2,scene=15,x=18,y=12,revision=revision+1 where character_id=4')
                    self.assertEqual(prepared.execute('select stage from diagnostic_town_guide_progress where character_id=4').fetchone(),(3,))
                    self.assertEqual(prepared.execute('select item_id,count from diagnostic_inventory_slots where character_id=4 and slot=0').fetchone(),(5569,1))
                    self.assertEqual(prepared.execute('select count(*) from battle_settlements').fetchone(),(0,))
                    prepared.commit()
            config['database']['path']=str(database)
            config['server'].update(host='127.0.0.1',port=helper.unused_port(),character_port=0)
            config['logging']['file']=str(here/'server.log')
            config['development']['diagnostic_town']['player_visibility']=False
            config['development']['diagnostic_town']['native_npc_placements_only']=native_only
            config['development']['native_monster_placements_only']=monster_only
            cfg=here/'config.json';cfg.write_text(json.dumps(config),encoding='utf-8')
            endpoint=('127.0.0.1',config['server']['port'])
            if pet1_only:
                from tools.strike_lab import import_native_pet1_metadata as pet1
                subprocess.run([str(BINARY),'--config',str(cfg),'--migrate-only'],cwd=ROOT,env=helper.environment(),
                    check=True,capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=30)
                pet1.install(database,pet1.cached(ROOT/'artifacts/research/native-pet1-20260927/records.json'))
                acceptance=ROOT/'artifacts/playtests/private-pet1-mixed-20260927-02/town-diagnostic-accounts.db'
                with closing(sqlite3.connect(acceptance.resolve().as_uri()+'?mode=ro',uri=True)) as accepted:
                    metadata,stats=accepted.execute('select metadata,stats from character_pet2_slots where character_id=4 and slot=43').fetchone()
                self.assertEqual((len(metadata),len(stats),stats[0],stats[0x27]),(20,53,0xe3,43))
                with closing(sqlite3.connect(database)) as prepared:
                    prepared.execute('update character_pet2_slots set metadata=?,stats=? where character_id=4 and slot=43',(metadata,stats));prepared.commit()

            def saved():
                with closing(sqlite3.connect(database)) as db:
                    self.assertEqual(db.execute('pragma quick_check').fetchone(),('ok',))
                    return {
                        'resources':db.execute('select * from character_resources order by character_id').fetchall(),
                        'roles':db.execute('select * from character_role_snapshots order by character_id').fetchall(),
                        'selection':db.execute('select row_key,revision from character_deity_selection where character_id=4').fetchone(),
                        'deities':db.execute('select declaration,status,skills from character_deities where character_id=4 order by row_key').fetchall(),
                        'pets':db.execute('select slot,metadata,stats,revision from character_pet2_slots where character_id=4 order by slot').fetchall(),
                        'other_pets':db.execute('select * from character_pet2_slots where character_id!=4 order by character_id,slot').fetchall()}

            def launch():
                output=lifetime.enter_context((here/'stdout.log').open('ab'))
                env=helper.environment();env['GOD2_LOG_FILE_ONLY']='1'
                process=subprocess.Popen([str(BINARY),'--config',str(cfg),'--run-for','50'],cwd=ROOT,env=env,
                    stdout=output,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                lifetime.callback(helper.stop,process)
                deadline=time.monotonic()+8
                while True:
                    self.assertIsNone(process.poll(),'Isolated server exited: '+(here/'stdout.log').read_text('utf-8',errors='replace'))
                    try:
                        with socket.create_connection(endpoint,timeout=.1):return process
                    except OSError:
                        self.assertLess(time.monotonic(),deadline);time.sleep(.025)

            def enter(expect_fixture=False):
                login=lifetime.enter_context(helper.connect(endpoint));helper.handshake(login)
                account,password=b'codexslow',b'labtest2345'
                login.sendall(helper.frame(*dual.credential(4,account,password)))
                helper.read_frame(login,0x1d,176);helper.read_frame(login,4,8)
                address=helper.read_frame(login,5,12)
                helper.read_frame(login,6,8);helper.read_frame(login,0x0a,20)
                self.assertEqual(helper.list_characters(login)[3],1)
                game=lifetime.enter_context(helper.connect(('127.0.0.1',int.from_bytes(address[9:11],'little'))))
                helper.handshake(game,game=True)
                game.sendall(helper.frame(*dual.credential(0,account,password)));helper.read_frame(game,0x1f,128)
                game.sendall(helper.frame(0x1a,dual.selection_payload(0)));helper.read_frame(game,2,26)
                entry=helper.read_frame(game,0x2a,40)
                if kunlun_only:
                    logical=entry[2:-1]
                    self.assertEqual(int.from_bytes(logical[25:27],'little'),(3<<6)|4)
                    self.assertEqual(logical[29]&3,0)
                identity=int.from_bytes(entry[3:5],'little')&0x3fff
                game.sendall(current_world_ready_wire(identity,(4,3)));helper.silent(game)
                game.sendall(helper.frame(0x30,b'\0'))
                frames=[decoder.logical(helper,game)]
                while select.select([game],[],[],.15)[0]:frames.append(decoder.logical(helper,game))
                if expect_fixture:
                    game.sendall(helper.frame(0x30,b'\0'))
                    decoder.logical(helper,game)
                    self.assertIn('DIAGNOSTIC_BATTLE_TRANSITION_SENT',
                                  (here/'server.log').read_text('utf-8',errors='replace'),
                                  'Control fixture did not reach encounter eligibility')
                    return game
                combined=b''.join(frames);state=saved()
                if clock_only:
                    clocks=[frame for frame in frames if frame[:1]==b'\x1a']
                    self.assertEqual(len(clocks),1)
                    clock=clocks[0];self.assertEqual(len(clock),4)
                    self.assertTrue(clock[1]<4 and clock[2]<60 and clock[3]<60)
                    phase=clock[1]*3600+clock[2]*60+clock[3]
                    self.assertLessEqual((int(time.time())-phase)%14400,2)
                # Saved 24 must precede any 30 deity binding.
                resources=next(row for row in state['resources'] if row[0]==4)
                role=next(row[1] for row in state['roles'] if row[0]==4)
                vitals=b'\x24'+b''.join(resources[index].to_bytes(4,'little') for index in (1,3,2,4))
                deity=b''.join(row[0] for row in state['deities'])
                selected=state['selection'][0]
                selected_status=None
                for declaration,status,skills in state['deities']:
                    if status[1]!=selected:deity+=status
                    else:selected_status=status
                    deity+=skills
                if selected_status:deity+=selected_status
                companions=deity+b''.join(pet_projection(row) for row in state['pets'])
                self.assertIn(role+vitals,combined)
                self.assertIn(companions,combined)
                self.assertLess(combined.index(role+vitals),combined.index(companions))
                if native_only:
                    for key,x,y in ((1606,110,69),(1607,112,70)):
                        diagnostic=(b'\x72'+key.to_bytes(4,'little')+bytes((20,0x60,0,0,1))+bytes(7)+
                                    ((y<<17)|(x<<2)).to_bytes(4,'little'))
                        self.assertNotIn(diagnostic,combined,'Unverified test NPC escaped native-only policy')
                    if not journal_only:
                        before=saved()
                        game.sendall(helper.frame(0x30,b'\0'))
                        helper.silent(game)
                        game.sendall(helper.frame(0x37,(1606).to_bytes(4,'little')))
                        helper.silent(game)
                        self.assertEqual(saved(),before,'Suppressed NPC interaction changed saved state')
                if journal_only:
                    self.assertIn(journal_projection,combined)
                    self.assertEqual(combined.count(journal_projection),1,'Journal duplicated or overwritten on world entry')
                if monster_only:
                    # Every frame is either saved projection or world restoration;
                    # an extra 82 entry record cannot be accepted as normal restore.
                    self.assertFalse(any(frame[:1]==b'\x82' for frame in frames))
                    game.sendall(helper.frame(0x30,b'\0'));helper.silent(game)
                    with closing(sqlite3.connect(database)) as observed:
                        self.assertEqual(observed.execute('select count(*) from battle_reservations').fetchone(),(0,))
                        self.assertEqual(observed.execute('select count(*) from battle_settlements').fetchone(),(0,))
                return game

            original=saved();process=launch()
            if journal_only:
                from tools.strike_lab import import_native_quests,import_native_quest_sources
                import struct
                values=[(1<<16)|44,(5<<16)|48,47]+[0]*11+[(3<<16)|50]
                blob=struct.pack('<15I',*values)
                journal_projection=b''.join(b'\xdb\x04'+bytes(3)+struct.pack('<II',slot,value) for slot,value in enumerate(values))
                with closing(sqlite3.connect(database)) as prepared:
                    import_native_quests.import_catalog(prepared,ROOT.parent/'God2')
                    import_native_quest_sources.import_catalog(prepared,ROOT.parent/'God2')
                    prepared.execute('insert into character_quest_journals values(4,?,1,?,?,?)',
                        (blob,'CUSTOM_TEST_NOT_NATIVE','isolated-tcp-journal-20260926','CUSTOM-0041'));prepared.commit()
            game=enter()
            if clock_only:
                # The shared frame helper owns a shorter per-frame deadline.
                # Wait for the periodic event separately, then decode normally.
                self.assertTrue(select.select([game],[],[],7)[0],'Periodic world clock missing')
                clock=decoder.logical(helper,game)
                self.assertEqual(clock[:1],b'\x1a');self.assertEqual(len(clock),4)
                phase=clock[1]*3600+clock[2]*60+clock[3]
                self.assertLessEqual((int(time.time())-phase)%14400,2)
            game.sendall(helper.frame(0x67,bytes((2 if deity_templates else 102,))))
            self.assertEqual(decoder.logical(helper,game),original['deities'][1][1])
            self.assertEqual(saved()['selection'],(2 if deity_templates else 102,2))
            for source,destination in ((42,44),(43,44),(44,42)):
                before=saved();rows={row[0]:row for row in before['pets']}
                metadata,stats=rows[source][1:3];self.assertTrue(metadata)
                game.sendall(helper.frame(0x28,metadata[:2]+bytes((source,1))))
                moved=bytearray(stats);moved[0x27 if moved[0]==0xe3 else 3]=destination
                existing=rows[destination]
                expected=clear(source)+clear(destination)
                if existing[1]:
                    swapped=bytearray(existing[2]);swapped[0x27 if swapped[0]==0xe3 else 3]=source
                    expected+=pet_projection((source,existing[1],bytes(swapped),0))[5:]
                expected+=pet_projection((destination,metadata,bytes(moved),0))[5:]
                self.assertEqual(decoder.logical(helper,game),expected)
                after=saved();self.assertEqual(after['resources'],original['resources'])
                self.assertEqual(after['roles'],original['roles']);self.assertEqual(after['other_pets'],original['other_pets'])
                target=next(row for row in after['pets'] if row[0]==destination)
                self.assertEqual(target[1:3],(metadata,bytes(moved)))
            if kunlun_only:
                game.sendall(movement_wire(127,126,1,0))
                self.assertEqual(decoder.logical(helper,game),b'\x5d\x01')
                with closing(sqlite3.connect(database)) as observed:
                    self.assertEqual(observed.execute('select area,scene,x,y,revision from recovered_positions where character_id=4').fetchone(),(4,3,127,126,1))
            committed=saved();game.close();helper.stop(process)
            process=launch();game=enter()
            self.assertEqual(saved(),committed,'Restart lost or reinitialized owned snapshots')
            if kunlun_only:
                with closing(sqlite3.connect(database)) as observed:
                    self.assertEqual(observed.execute('select area,scene,x,y,revision from recovered_positions where character_id=4').fetchone(),(4,3,127,126,1))
            log=(here/'server.log').read_text('utf-8',errors='replace')
            self.assertEqual(log.count('OWNED_PET2_SELECTION_COMMITTED'),3)
            self.assertEqual(log.count('OWNED_DEITY_SELECTION_COMMITTED'),1)
            if native_only:
                if not monster_only and not kunlun_only:self.assertIn('NATIVE_NPC_PLACEMENT_GAP',log)
                self.assertNotIn('DIAGNOSTIC_TOWN_GUIDES_SENT',log)
                self.assertEqual(log.count('NATIVE_NPC_INTERACTION_REJECTED'),0 if journal_only else 2,
                                 'Unrelated tick was treated as an NPC interaction')
            if journal_only:
                self.assertEqual(log.count('OWNED_QUEST_JOURNAL_RESTORED'),2)
                with closing(sqlite3.connect(database)) as observed:
                    self.assertEqual(observed.execute('select values_blob,revision,origin,provenance from character_quest_journals where character_id=4').fetchone(),
                        (blob,1,'CUSTOM_TEST_NOT_NATIVE','isolated-tcp-journal-20260926'))
            if monster_only:
                self.assertIn('NATIVE_MONSTER_PLACEMENT_GAP',log)
                self.assertNotIn('DIAGNOSTIC_BATTLE_TRANSITION_SENT',log)
                # Positive control in this disposable DB: same map, quest, item
                # and tick actually enter the fixture when the restriction is off.
                game.close();helper.stop(process)
                config['development']['native_monster_placements_only']=False
                cfg.write_text(json.dumps(config),encoding='utf-8')
                process=launch();game=enter(expect_fixture=True)
                self.assertEqual(saved(),committed,'Control entry changed saved companions/resources')

if __name__=='__main__':unittest.main()
