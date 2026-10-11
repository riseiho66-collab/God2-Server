"""Disposable SQLite + real TCP owned raw2C restore; no live DB/client writes.

This is transport/persistence acceptance, not native UI or original stat values.
All inserted61byte snapshots are CUSTOM_TEST_NOT_NATIVE and exist only in the
TemporaryDirectory clone. Requires the candidate; never builds a shared target.
"""
from contextlib import ExitStack, closing
import json
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

import test_recovered_dual_connection_server as dual
import test_inventory_move_server as inventory
from test_current_world_ready_builder import current_world_ready_wire

ROOT=dual.ROOT
SOURCE=ROOT/'artifacts/playtests/private-owned-companions-20260926-01'
BINARY=Path(os.environ.get('GOD2_OWNED_SERVER_CANDIDATE',
    ROOT/'build-town-visibility/Release/god2-server-role-auxiliary.exe'))
CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'


def synthetic_snapshot(salt):
    raw=bytearray([0x2c]+[(i*37+salt)&255 for i in range(1,61)])
    # Two raw mask WORDs; untouched source padding is deliberately nonzero.
    struct.pack_into('<H',raw,37,0xa55a)
    struct.pack_into('<H',raw,41,0x8001)
    # Preserve high bits; never replace these with signed/transformed actor data.
    struct.pack_into('<4I',raw,45,0xffffffff,0x80000001,0xdeadbeef,0xfedcba98)
    return bytes(raw)


class OwnedRoleAuxiliaryServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file() or not (SOURCE/'town-diagnostic-accounts.db').is_file():
            raise AssertionError('Built auxiliary candidate and isolated companion source fixture required')
        dual.RecoveredDualConnectionServerTests.crypto_key=dual.key(ROOT)
        if len(dual.RecoveredDualConnectionServerTests.crypto_key)!=256:
            raise AssertionError('Native transport key fixture width')

    def test_missing_then_owned_raw_snapshot_once_per_world_and_restart(self):
        helper=dual.RecoveredDualConnectionServerTests()
        decoder=inventory.InventoryMoveServerTests()
        owned=synthetic_snapshot(19);other=synthetic_snapshot(73)
        self.assertEqual(len(owned),61)
        self.assertNotEqual(owned,other)
        with tempfile.TemporaryDirectory(prefix='god2-role-aux-tcp-') as tmp, ExitStack() as lifetime:
            here=Path(tmp);database=here/'town-diagnostic-accounts.db'
            with closing(sqlite3.connect((SOURCE/'town-diagnostic-accounts.db').resolve().as_uri()+'?mode=ro',uri=True)) as source:
                with closing(sqlite3.connect(database)) as target:source.backup(target)
            config=json.loads((SOURCE/'server-config.json').read_text('utf-8'))
            config['database']['path']=str(database)
            config['server'].update(host='127.0.0.1',port=helper.unused_port(),character_port=0)
            config['logging'].update(file=str(here/'server.log'),level='debug')
            config['protocol']['packet_dump']=False
            config['development']['diagnostic_world_resources']=False
            config['development']['diagnostic_world_supply']=False
            config['development']['diagnostic_town']['player_visibility']=False
            config['development']['diagnostic_town']['native_npc_placements_only']=True
            config.setdefault('world',{}).setdefault('clock',{})['enabled']=False
            cfg=here/'config.json';cfg.write_text(json.dumps(config),encoding='utf-8')
            endpoint=('127.0.0.1',config['server']['port'])

            def stable_saved():
                with closing(sqlite3.connect(database)) as db:
                    self.assertEqual(db.execute('pragma quick_check').fetchone(),('ok',))
                    return {table:db.execute('select * from '+table+' order by character_id').fetchall()
                            for table in ('character_resources','character_role_snapshots')}

            original=stable_saved()
            self.assertTrue(original['character_resources'],'Fixture must exercise existing resource preservation')

            def auxiliary_rows():
                with closing(sqlite3.connect(database)) as db:
                    return db.execute('select * from character_role_auxiliary_snapshots order by character_id').fetchall()

            def insert_fixture(character,raw):
                with closing(sqlite3.connect(database)) as db:
                    db.execute('PRAGMA foreign_keys=ON')
                    self.assertEqual(db.execute('select count(*) from recovered_characters where id=?',(character,)).fetchone(),(1,))
                    db.execute('insert into character_role_auxiliary_snapshots '
                        '(character_id,logical,revision,origin,provenance,client_sha256,design_id) '
                        "values(?,?,7,'CUSTOM_TEST_NOT_NATIVE','isolated-raw2C-TCP-test',?,'CUSTOM-0045')",
                        (character,raw,CLIENT_SHA));db.commit()

            def launch():
                output=lifetime.enter_context((here/'stdout.log').open('ab'))
                env=helper.environment();env['GOD2_LOG_FILE_ONLY']='1'
                process=subprocess.Popen([str(BINARY),'--config',str(cfg),'--run-for','40'],cwd=ROOT,
                    stdout=output,stderr=subprocess.STDOUT,env=env,
                    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                lifetime.callback(helper.stop,process)
                deadline=time.monotonic()+8
                while True:
                    self.assertIsNone(process.poll(),'Isolated auxiliary server exited during startup: '+
                        (here/'stdout.log').read_text('utf-8',errors='replace')[-2000:])
                    try:
                        with socket.create_connection(endpoint,timeout=.1):return process
                    except OSError:
                        self.assertLess(time.monotonic(),deadline,'Isolated server did not listen');time.sleep(.025)

            def drain(game,require_frame=False):
                frames=[]
                if require_frame:frames.append(decoder.logical(helper,game))
                while select.select([game],[],[],.15)[0]:frames.append(decoder.logical(helper,game))
                return frames

            def enter(expect,connections):
                login=connections.enter_context(helper.connect(endpoint));helper.handshake(login)
                credentials=(b'codexslow',b'labtest2345')
                login.sendall(helper.frame(*dual.credential(4,*credentials)))
                helper.read_frame(login,0x1d,176);helper.read_frame(login,4,8)
                address=helper.read_frame(login,5,12)
                helper.read_frame(login,6,8);helper.read_frame(login,0x0a,20)
                self.assertEqual(helper.list_characters(login)[3],1)
                game=connections.enter_context(helper.connect(('127.0.0.1',int.from_bytes(address[9:11],'little'))))
                helper.handshake(game,game=True)
                game.sendall(helper.frame(*dual.credential(0,*credentials)));helper.read_frame(game,0x1f,128)
                game.sendall(helper.frame(0x1a,dual.selection_payload(0)));helper.read_frame(game,2,26)
                entry=helper.read_frame(game,0x2a,40)
                identity=int.from_bytes(entry[3:5],'little')&0x3fff;self.assertEqual(identity,4)
                helper.silent(game) # No auxiliary snapshot before world admission.
                game.sendall(current_world_ready_wire(identity,(4,3)));helper.silent(game)
                game.sendall(helper.frame(0x30,b'\0'))
                frames=drain(game,require_frame=True)
                auxiliary=[frame for frame in frames if frame[:1]==b'\x2c']
                self.assertEqual(auxiliary,[] if expect is None else [expect],
                    'Owned raw2C missing, duplicated, rewritten or leaked from another owner')
                self.assertNotIn(other,frames,'Other character raw2C leaked')
                # It is an independent61byte initial snapshot, with all opaque
                # source masks/padding/high DWORDs retained, never a recomputation.
                if expect is not None:
                    self.assertEqual(len(auxiliary[0]),61)
                    self.assertEqual(tuple(struct.unpack_from('<H',auxiliary[0],offset)[0] for offset in (37,41)),
                                     (0xa55a,0x8001))
                    self.assertEqual(struct.unpack_from('<4I',auxiliary[0],45),(0xffffffff,0x80000001,0xdeadbeef,0xfedcba98))
                for _ in range(2):
                    game.sendall(helper.frame(0x30,b'\0'))
                    later=drain(game)
                    self.assertFalse(any(frame[:1]==b'\x2c' for frame in later),'Raw2C repeated on idle tick')
                self.assertEqual(stable_saved(),original,'Snapshot restoration changed saved resources/role values')

            # Candidate performs its real migrations on the disposable clone.
            process=launch()
            self.assertEqual(auxiliary_rows(),[],'Fixture unexpectedly already owns auxiliary rows')
            insert_fixture(5,other)
            before_missing=auxiliary_rows()
            with ExitStack() as connections:enter(None,connections)
            self.assertEqual(auxiliary_rows(),before_missing,'Missing owned snapshot was auto-seeded')
            helper.stop(process)
            self.assertNotIn('OWNED_ROLE_AUXILIARY_RESTORED',(here/'server.log').read_text('utf-8',errors='replace'))

            insert_fixture(4,owned)
            saved=auxiliary_rows()
            for restart in range(2):
                process=launch()
                with ExitStack() as connections:enter(owned,connections)
                self.assertEqual(auxiliary_rows(),saved,'Raw bytes/revisions/other owner changed across restore/restart')
                self.assertEqual(stable_saved(),original)
                helper.stop(process)
            log=(here/'server.log').read_text('utf-8',errors='replace')
            self.assertEqual(log.count('OWNED_ROLE_AUXILIARY_RESTORED'),2)
            self.assertEqual(auxiliary_rows(),saved)


if __name__=='__main__':unittest.main()
