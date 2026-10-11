"""Disposable real TCP weapon/DA transaction and2A relogin acceptance.

Synthetic CUSTOM-0046/0047 operands only. No original item-to-appearance mapping,
renderer claim, production DB writes, or client/UI process is involved.
"""
from contextlib import ExitStack, closing
import json
import hashlib
import os
from pathlib import Path
import select
import socket
import sqlite3
import struct
import subprocess
import tempfile
import time
import unittest

import test_owned_weapon_transfers_server as weapon
from test_current_world_ready_builder import current_world_ready_wire
from tools.strike_lab.run_private_owned_companions import seed_weapon_appearance

ROOT=weapon.ROOT
BINARY=Path(os.environ.get('GOD2_OWNED_SERVER_CANDIDATE',
    ROOT/'build-town-visibility/Release/god2-server.exe'))


class OwnedPlayerAppearanceServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file():raise AssertionError('Built appearance candidate required; no shared build performed')
        print('OWNED_APPEARANCE_TEST_BINARY',str(BINARY),hashlib.sha256(BINARY.read_bytes()).hexdigest(),flush=True)
        weapon.dual.RecoveredDualConnectionServerTests.crypto_key=weapon.dual.key(ROOT)

    def test_missing_equip_atomic_afterstate_restart_and_unequip(self):
        helper=weapon.dual.RecoveredDualConnectionServerTests()
        decoder=weapon.inventory.InventoryMoveServerTests()
        with tempfile.TemporaryDirectory(prefix='god2-appearance-tcp-') as temporary, ExitStack() as lifetime:
            here=Path(temporary);database=here/'town-diagnostic-accounts.db'
            with closing(sqlite3.connect((weapon.SOURCE/database.name).resolve().as_uri()+'?mode=ro',uri=True)) as source:
                with closing(sqlite3.connect(database)) as target:
                    source.backup(target)
                    target.execute('update recovered_positions set area=2,scene=4,x=88,y=75,revision=revision+1 where character_id=4')
                    target.commit()
            config=json.loads((weapon.SOURCE/'server-config.json').read_text('utf-8'))
            config['database']['path']=str(database)
            config['server'].update(host='127.0.0.1',port=helper.unused_port(),character_port=0)
            config['logging'].update(file=str(here/'server.log'),level='debug')
            config['protocol']['packet_dump']=False
            config['development'].update(diagnostic_world_resources=False,diagnostic_world_supply=False,
                diagnostic_player_visibility=False,diagnostic_remote_actor=False,diagnostic_owned_weapon_appearance=True)
            config['development']['diagnostic_town'].update(player_visibility=False,
                native_npc_placements_only=True,quest_progress=False,map_probe=False)
            config.setdefault('world',{}).update(owned_weapon_transfers={'enabled':True},
                owned_player_appearance={'enabled':True},clock={'enabled':False})
            cfg=here/'config.json';cfg.write_text(json.dumps(config),encoding='utf-8')
            endpoint=('127.0.0.1',config['server']['port'])
            env=helper.environment();env['GOD2_LOG_FILE_ONLY']='1'
            flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
            migrated=subprocess.run([str(BINARY),'--config',str(cfg),'--migrate-only'],cwd=ROOT,env=env,
                creationflags=flags,capture_output=True,timeout=20)
            self.assertEqual(migrated.returncode,0,migrated.stdout.decode('utf-8',errors='replace')[-2000:])
            records=weapon.import_native_weapons.cached_records(ROOT/'artifacts/research/native-weapons-20260926/records.json')
            with closing(sqlite3.connect(database)) as db:
                weapon.import_native_weapons.import_catalog(db,records=records)
                instance=bytes.fromhex(weapon.seed_weapon_transfers(db)['instances'][0])
                # Explicit disposable class25 operand. Source19071 is male-only;
                # actor4 owns a validated female profile. No production grant.
                self.assertEqual(db.execute('select profile from recovered_characters where id=4').fetchone()[0][33],1)
                restricted=struct.pack('<HH',19071,25)+bytes(16)
                db.execute('update diagnostic_inventory_slots set item_id=19071,count=1 where character_id=4 and slot=2')
                db.execute("insert into character_weapon_slot_metadata values(4,2,?,1,'CUSTOM_TEST_NOT_NATIVE',"
                    "'TCP-source-sex-refusal/CUSTOM-0046',?,?,'CUSTOM-0046')",
                    (restricted,weapon.WEAPON_SOURCE_SHA,weapon.CURRENT_CLIENT_SHA))
                # Exercise missing actor4 while actor5 owns an explicit snapshot.
                other=b'\xda'+struct.pack('<HHBB',5,0,0x81,0x42)+bytes.fromhex('0120014001008100')
                db.execute("insert into character_player_appearance_snapshots values(5,?,?,7,'CUSTOM_TEST_NOT_NATIVE',"
                    "'isolated-other-owner',?,'CUSTOM-0047')",(other,other[7:],weapon.CURRENT_CLIENT_SHA))
                db.commit()

            def snapshot():
                with closing(sqlite3.connect(database)) as db:
                    self.assertEqual(db.execute('pragma quick_check').fetchone(),('ok',))
                    return {table:db.execute('select * from '+table+' order by 1,2').fetchall() for table in
                        ('diagnostic_inventory_slots','character_weapon_slot_metadata','character_player_appearance_snapshots',
                         'character_resources','character_role_snapshots','character_deities','character_deity_selection',
                         'character_pet2_slots','character_role_auxiliary_snapshots')}

            original=snapshot()

            def stable():
                actual=snapshot()
                for table in original:
                    if table in ('diagnostic_inventory_slots','character_weapon_slot_metadata','character_player_appearance_snapshots'):
                        self.assertEqual([r for r in actual[table] if r[0]!=4],[r for r in original[table] if r[0]!=4])
                    else:self.assertEqual(actual[table],original[table],table)

            def appearance():
                with closing(sqlite3.connect(database)) as db:
                    return db.execute('select logical,base_components,revision,origin,provenance,client_sha256,design_id '
                        'from character_player_appearance_snapshots where character_id=4').fetchone()

            def launch():
                output=lifetime.enter_context((here/'stdout.log').open('ab'))
                process=subprocess.Popen([str(BINARY),'--config',str(cfg),'--run-for','40'],cwd=ROOT,env=env,
                    creationflags=flags,stdout=output,stderr=subprocess.STDOUT)
                lifetime.callback(helper.stop,process)
                deadline=time.monotonic()+8
                while True:
                    self.assertIsNone(process.poll(),(here/'stdout.log').read_text('utf-8',errors='replace')[-2500:])
                    try:
                        with socket.create_connection(endpoint,timeout=.1):return process
                    except OSError:
                        self.assertLess(time.monotonic(),deadline,'Candidate did not listen');time.sleep(.025)

            def drain(game,required=False):
                frames=[decoder.logical(helper,game)] if required else []
                while select.select([game],[],[],.15)[0]:frames.append(decoder.logical(helper,game))
                return frames

            def reject(game,logical):
                before=snapshot()
                game.sendall(helper.frame(logical[0],logical[1:]));helper.silent(game)
                self.assertEqual(snapshot(),before,'Rejected input mutated inventory/appearance')

            def reject_source_sex(game):
                before=snapshot()
                game.sendall(helper.frame(0x28,weapon.selection(2,19071)[1:]))
                try:reply=decoder.logical(helper,game)
                except TimeoutError:
                    trace=(here/'server.log').read_text('utf-8',errors='replace')
                    self.fail('Source rejection reply missing: '+trace[-4500:])
                self.assertEqual(reply,b'\x02\x1b\0\x7f\x4a'+bytes(18))
                helper.silent(game)
                self.assertEqual(snapshot(),before,'Source-sex rejection mutated owned state')

            def enter(connections,expected):
                login=connections.enter_context(helper.connect(endpoint));helper.handshake(login)
                credentials=(b'codexslow',b'labtest2345')
                login.sendall(helper.frame(*weapon.dual.credential(4,*credentials)))
                helper.read_frame(login,0x1d,176);helper.read_frame(login,4,8)
                address=helper.read_frame(login,5,12)
                helper.read_frame(login,6,8);helper.read_frame(login,0x0a,20)
                self.assertEqual(helper.list_characters(login)[3],1)
                game=connections.enter_context(helper.connect(('127.0.0.1',int.from_bytes(address[9:11],'little'))))
                helper.handshake(game,game=True)
                game.sendall(helper.frame(*weapon.dual.credential(0,*credentials)));helper.read_frame(game,0x1f,128)
                game.sendall(helper.frame(0x1a,weapon.dual.selection_payload(0)));helper.read_frame(game,2,26)
                entry=decoder.logical(helper,game)
                self.assertEqual((len(entry),entry[0]),(37,0x2a))
                self.assertEqual(int.from_bytes(entry[1:3],'little')&0x3fff,4)
                if expected is not None:
                    self.assertEqual(entry[13:21],expected[0][7:])
                    self.assertEqual(entry[33:37],expected[0][3:7],
                        '2A lost saved transform/scalars or reset saved components')
                    self.assertEqual(appearance(),expected,'Login revised/reset appearance baseline')
                game.sendall(current_world_ready_wire(4,(4,3)));helper.silent(game)
                game.sendall(helper.frame(0x30,b'\0'));frames=drain(game,True)
                self.assertFalse(any(frame[:1] in (b'\xda',b'\x2c') for frame in frames),
                    'Initial2A restoration should not fabricate DA or final-stat snapshots')
                # Full20 saved instance is restored in the occupied slot.
                with closing(sqlite3.connect(database)) as db:
                    owned=db.execute('select m.slot,m.logical20 from character_weapon_slot_metadata m '
                        'join diagnostic_inventory_slots s using(character_id,slot) where m.character_id=4 and s.count=1').fetchall()
                for slot,raw in owned:self.assertIn(weapon.occupied(slot,raw),b''.join(frames))
                game.sendall(helper.frame(0x2e,struct.pack('<HHBB',88,75,1,0xa5)))
                self.assertEqual(decoder.logical(helper,game),b'\x5d\x01');helper.silent(game)
                stable()
                return game

            process=launch()
            with ExitStack() as connections:
                game=enter(connections,None)
                reject_source_sex(game)
                reject(game,weapon.selection(2,19072))
                reject(game,weapon.selection(2,19071)+b'\x24\x00\x05')
                reject(game,weapon.selection(0,1))
                self.assertIsNone(appearance(),'Missing owned appearance was auto-granted')
            helper.stop(process)
            self.assertEqual(snapshot(),original)

            with closing(sqlite3.connect(database)) as db:
                seed_weapon_appearance(db)
                raw=bytearray(db.execute('select logical from character_player_appearance_snapshots where character_id=4').fetchone()[0])
                # Nonzero synthetic raw scalars prevent a zero-default codec from
                # accidentally passing this transport-only preservation test.
                raw[5:7]=b'\x87\xf9'
                db.execute("update character_player_appearance_snapshots set logical=?,"
                    "provenance='isolated-TCP/profile-components/raw-scalars-87-f9/CUSTOM-0047' where character_id=4",(bytes(raw),))
                db.commit()
            baseline=appearance();self.assertEqual(baseline[2],1)
            equipped=bytearray(baseline[0]);equipped[13]&=15;equipped[14]=0
            self.assertNotEqual(bytes(equipped),baseline[0])

            def transfer(game,source,destination,expected_da,revision):
                before=snapshot();prior=appearance()
                game.sendall(helper.frame(0x28,weapon.selection(source,1)[1:]))
                reply=decoder.logical(helper,game)
                self.assertEqual(reply,weapon.clear(source)+weapon.clear(destination)+weapon.occupied(destination,instance)+expected_da,
                    'Expected full20 instance followed by exactly one complete DA; no stat records')
                saved=appearance()
                self.assertEqual(saved,(expected_da,baseline[1],revision,*baseline[3:]))
                self.assertEqual(saved[2],prior[2]+1)
                with closing(sqlite3.connect(database)) as db:
                    for slot,item,expected_raw in ((source,0,b'\0\0'+instance[2:]),(destination,1,instance)):
                        scalar=db.execute('select item_id,count,revision from diagnostic_inventory_slots where character_id=4 and slot=?',(slot,)).fetchone()
                        meta=db.execute('select logical20,revision,origin,provenance from character_weapon_slot_metadata where character_id=4 and slot=?',(slot,)).fetchone()
                        old=next(row for row in before['diagnostic_inventory_slots'] if row[:2]==(4,slot))
                        self.assertEqual(scalar,(item,int(bool(item)),old[4]+1))
                        self.assertEqual(meta[:2],(expected_raw,scalar[2]))
                        self.assertEqual(meta[2:],[('EMPTY_SLOT_POLICY','CUSTOM-0046/clear-previous-instance'),
                            ('CUSTOM_TEST_NOT_NATIVE','hidden-weapon-fixture/item1/CUSTOM-0046')][bool(item)])
                after=snapshot()
                for table in ('diagnostic_inventory_slots','character_weapon_slot_metadata'):
                    self.assertEqual([r for r in after[table] if r[:2] not in ((4,source),(4,destination))],
                        [r for r in before[table] if r[:2] not in ((4,source),(4,destination))],
                        'Unrelated owned instance changed during appearance transaction')
                helper.silent(game);stable()

            process=launch()
            with ExitStack() as connections:
                game=enter(connections,baseline)
                reject_source_sex(game)
                reject(game,weapon.selection(0,2))
                reject(game,weapon.selection(0,1)+b'\x24\x00\x05')
                transfer(game,0,34,bytes(equipped),2)
            helper.stop(process)
            saved_equipped=appearance();persisted=snapshot()
            process=launch()
            with ExitStack() as connections:
                game=enter(connections,saved_equipped)
                reject_source_sex(game)
                self.assertEqual(snapshot(),persisted,'Restart changed weapon/appearance revision or raw data')
                reject(game,weapon.selection(34,2))
                reject(game,weapon.selection(34,1)+weapon.selection(34,1))
                transfer(game,34,0,baseline[0],3)
            helper.stop(process)
            self.assertEqual(appearance()[1],baseline[1],'Immutable unequipped baseline changed')
            stable()
            self.assertEqual((here/'server.log').read_text('utf-8',errors='replace').count('OWNED_WEAPON_TRANSFER_COMMITTED'),2)


if __name__=='__main__':unittest.main()
