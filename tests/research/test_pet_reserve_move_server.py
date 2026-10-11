"""Isolated own-server24 reserve reorder, rollback preflight and restart.

Uses copied synthetic acceptance fixtures; no service restart or live DB writes.
This proves socket/persistence integration, not current-client UI acceptance.
"""
from contextlib import ExitStack, closing
import hashlib
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

ROOT=dual.ROOT
sys.path.insert(0,str(ROOT))
SOURCE=ROOT/'artifacts/playtests/private-owned-companions-20260926-01'
BINARY=Path(os.environ.get('GOD2_PET_RESERVE_TEST_BINARY',ROOT/'build-town-visibility/Release/god2-server-native-results.exe'))


def clear(slot):return bytes((0x41,0,0,slot,0))


def occupied(row,slot):
    metadata,stats=row[2:4]
    if not metadata:return b''
    moved=bytearray(stats);moved[0x27 if moved[0]==0xe3 else 3]=slot
    return bytes((0x3b,1,slot,0,0))+metadata+bytes((0x41,metadata[0],metadata[1],slot,1))+moved


class PetReserveMoveServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file() or not (SOURCE/'town-diagnostic-accounts.db').is_file():
            raise AssertionError('Candidate and isolated companion fixture required')
        dual.RecoveredDualConnectionServerTests.crypto_key=dual.key(ROOT)
        print('Pet reserve candidate:',BINARY,'SHA256',hashlib.sha256(BINARY.read_bytes()).hexdigest(),flush=True)

    def test_native24_owned_reserves_restart(self):self.run_case(False)

    def test_native24_mixed_e3_fb_restart(self):self.run_case(True)

    def run_case(self,mixed):
        helper=dual.RecoveredDualConnectionServerTests();decoder=inventory.InventoryMoveServerTests()
        with tempfile.TemporaryDirectory(prefix='god2-pet-reserve-tcp-') as tmp, ExitStack() as lifetime:
            here=Path(tmp);database=here/'town-diagnostic-accounts.db'
            with closing(sqlite3.connect((SOURCE/'town-diagnostic-accounts.db').resolve().as_uri()+'?mode=ro',uri=True)) as original:
                with closing(sqlite3.connect(database)) as copied:original.backup(copied)
            # The historical fixture predates the key100 template rejection.
            # Delete its unrenderable deity on this disposable clone only.
            with closing(sqlite3.connect(database)) as prepared:
                prepared.execute('delete from character_deity_selection where character_id=4')
                prepared.execute('delete from character_deities where character_id=4 and row_key=100')
                prepared.execute('insert into character_deity_selection values(4,101,1)')
                prepared.execute('delete from recovered_positions where character_id=4');prepared.commit()
            config=json.loads((SOURCE/'server-config.json').read_text('utf-8'))
            config['world']={'new_character_birthplace':{'area':4,'scene':3,'kind':0,'x':126,'y':126,
                'navigation':str(ROOT/'artifacts/world-atlas/kunlun-4-3.json'),'coordinate_authority':'CUSTOM-0040'}}
            config['database']['path']=str(database)
            config['server'].update(host='127.0.0.1',port=helper.unused_port(),character_port=0)
            config['logging']['file']=str(here/'server.log')
            config['development']['diagnostic_town']['player_visibility']=False
            config['development']['diagnostic_town']['native_npc_placements_only']=True
            cfg=here/'config.json';cfg.write_text(json.dumps(config),encoding='utf-8')
            endpoint=('127.0.0.1',config['server']['port'])
            migrated=subprocess.run([str(BINARY),'--config',str(cfg),'--migrate-only'],cwd=ROOT,env=helper.environment(),
                capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=30)
            self.assertEqual(migrated.returncode,0,(migrated.stdout+migrated.stderr).decode('utf-8',errors='replace'))
            if mixed:
                from tools.strike_lab import import_native_pet1_metadata as pet1
                pet1.install(database,pet1.cached(ROOT/'artifacts/research/native-pet1-20260927/records.json'))
                accepted=ROOT/'artifacts/playtests/private-pet1-mixed-20260927-02/town-diagnostic-accounts.db'
                with closing(sqlite3.connect(accepted.resolve().as_uri()+'?mode=ro',uri=True)) as source:
                    meta,stats=source.execute('select metadata,stats from character_pet2_slots where character_id=4 and slot=43').fetchone()
                self.assertEqual((len(meta),len(stats),stats[0],stats[0x27]),(20,53,0xe3,43))
                with closing(sqlite3.connect(database)) as prepared:
                    prepared.execute('update character_pet2_slots set metadata=?,stats=? where character_id=4 and slot=43',(meta,stats));prepared.commit()

            def saved():
                with closing(sqlite3.connect(database)) as db:
                    return {table:db.execute('select * from '+table+' order by 1,2').fetchall() for table in (
                        'character_pet2_slots','character_deities','character_deity_selection','character_resources',
                        'character_role_snapshots','diagnostic_inventory_slots','battle_reservations','battle_settlements')}

            def launch():
                output=lifetime.enter_context((here/'stdout.log').open('ab'))
                env=helper.environment();env['GOD2_LOG_FILE_ONLY']='1'
                process=subprocess.Popen([str(BINARY),'--config',str(cfg),'--run-for','50'],cwd=ROOT,env=env,
                    stdout=output,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                lifetime.callback(helper.stop,process);deadline=time.monotonic()+10
                while True:
                    self.assertIsNone(process.poll(),(here/'stdout.log').read_text('utf-8',errors='replace'))
                    try:
                        with socket.create_connection(endpoint,timeout=.1):return process
                    except OSError:self.assertLess(time.monotonic(),deadline);time.sleep(.025)

            def enter():
                login=lifetime.enter_context(helper.connect(endpoint));helper.handshake(login)
                account,password=b'codexslow',b'labtest2345'
                login.sendall(helper.frame(*dual.credential(4,account,password)))
                helper.read_frame(login,0x1d,176);helper.read_frame(login,4,8);address=helper.read_frame(login,5,12)
                helper.read_frame(login,6,8);helper.read_frame(login,0x0a,20);self.assertEqual(helper.list_characters(login)[3],1)
                game=lifetime.enter_context(helper.connect(('127.0.0.1',int.from_bytes(address[9:11],'little'))))
                helper.handshake(game,game=True);game.sendall(helper.frame(*dual.credential(0,account,password)))
                helper.read_frame(game,0x1f,128);game.sendall(helper.frame(0x1a,dual.selection_payload(0)))
                helper.read_frame(game,2,26);entry=helper.read_frame(game,0x2a,40)
                identity=int.from_bytes(entry[3:5],'little')&0x3fff
                game.sendall(current_world_ready_wire(identity,(4,3)));helper.silent(game)
                before=saved();game.sendall(helper.frame(0x24,bytes((42,43))));helper.silent(game)
                self.assertEqual(saved(),before,'Unprojected native24 changed ownership')
                game.sendall(helper.frame(0x30,b'\0'));frames=[decoder.logical(helper,game)]
                while select.select([game],[],[],.15)[0]:frames.append(decoder.logical(helper,game))
                combined=b''.join(frames)
                for row in saved()['character_pet2_slots']:
                    if row[0]==4:self.assertIn(clear(row[1])+occupied(row,row[1]),combined)
                return game

            def swap(game,source,destination,with_ticks=False):
                before=saved();rows={r[1]:r for r in before['character_pet2_slots'] if r[0]==4}
                record=bytes((0x24,source,destination))
                if with_ticks:record=b'\x30\0'+record+b'\x30\0'
                game.sendall(helper.frame(record[0],record[1:]))
                expected=clear(source)+clear(destination)+occupied(rows[destination],source)+occupied(rows[source],destination)
                self.assertEqual(decoder.logical(helper,game),expected)
                after=saved();actual={r[1]:r for r in after['character_pet2_slots'] if r[0]==4}
                for slot,donor in ((source,destination),(destination,source)):
                    want=list(rows[donor]);want[1]=slot;want[4]=rows[slot][4]+1
                    if want[3]:
                        raw=bytearray(want[3]);raw[0x27 if raw[0]==0xe3 else 3]=slot;want[3]=bytes(raw)
                    self.assertEqual(actual[slot],tuple(want),'Native24 lost complete instance/provenance')
                for table in before:
                    if table=='character_pet2_slots':
                        self.assertEqual([r for r in after[table] if r[0]!=4 or r[1] not in (42,43)],
                            [r for r in before[table] if r[0]!=4 or r[1] not in (42,43)])
                    else:self.assertEqual(after[table],before[table],table+' changed')
                helper.silent(game)

            process=launch();game=enter();swap(game,42,43);swap(game,43,42,True)
            before=saved();game.sendall(helper.frame(0x24,bytes((42,42))));helper.silent(game)
            self.assertEqual(saved(),before,'Same reserve rewrote revisions')
            # Entire native batch rejects before movement or any reserve swap.
            game.sendall(helper.frame(0x24,b'\x2a\x2b\x24\x2b\x2a'));helper.closed(game)
            self.assertEqual(saved(),before,'Duplicate reserve operations partly committed')
            helper.stop(process);process=launch();game=enter()
            self.assertEqual(saved(),before,'Restart changed saved reserve order')
            swap(game,42,43)
            game.close();helper.stop(process)


if __name__=='__main__':unittest.main()
