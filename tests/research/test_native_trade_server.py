"""Actual isolated Application sockets, synthetic peers; native UI gate is separate."""
from contextlib import ExitStack, closing, contextmanager
import sqlite3
import struct
import unittest
import json
import test_owned_role_text_server as fixture
import test_native_party_server as party
from tools.strike_lab.current_trade_20261002 import PresentationOracle
from tools.strike_lab.current_protocol_coverage import qualified_image
from tools.strike_lab.current_party_20261002 import UI
from tools.strike_lab.discard_fixture_27_20261002 import copy_catalog

ITEM_SOURCE = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'


class NativeTradeServerTests(unittest.TestCase):
    server = fixture.OwnedRoleTextServerTests.server
    drain = fixture.OwnedRoleTextServerTests.drain
    enter_peer = party.NativePartyServerTests.enter_peer
    send = party.NativePartyServerTests.send

    @classmethod
    def setUpClass(cls):
        fixture.OwnedRoleTextServerTests.setUpClass.__func__(cls)

    @staticmethod
    def tables(state):
        with closing(sqlite3.connect(state.database)) as db:
            return {name: (sql, sorted(repr(row) for row in db.execute('select * from "' + name.replace('"', '""') + '"')))
                    for name, sql in db.execute("select name,sql from sqlite_master where type='table' and name not like 'sqlite_%'")}

    @contextmanager
    def peers(self):
        with self.server() as state, ExitStack() as lifetime:
            # Configure only this disposable clone; keep the shared fixture
            # and its tests unchanged. The first startup installs trade DDL.
            state.helper.stop(state.process)
            config_path=state.database.parent/'config.json'
            config=json.loads(config_path.read_text('utf-8'))
            config['world']['owned_supply']={'enabled':True}
            config_path.write_text(json.dumps(config),encoding='utf-8')
            with closing(sqlite3.connect(state.database)) as db:
                copy_catalog(db)
                source=fixture.ROOT/'artifacts/playtests/private-weapon-peer-20260927-04/town-diagnostic-accounts.db'
                with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)) as origin:
                    role=origin.execute('select * from character_role_snapshots where character_id=5').fetchone()
                    resources=origin.execute('select * from character_resources where character_id=5').fetchone()
                db.execute('insert or replace into character_role_snapshots values(?,?,?,?)',role)
                db.execute('insert or replace into character_resources values(?,?,?,?,?,?,?)',resources)
                db.execute('update recovered_positions set area=4,scene=3,x=129,y=126 where character_id=5')
                for identity,count,money in ((4,10,1000),(5,8,2000)):
                    db.execute('delete from diagnostic_inventory_slots where character_id=? and slot<30',(identity,))
                    db.execute('delete from character_weapon_slot_metadata where character_id=? and slot<30',(identity,))
                    for slot in range(30):
                        db.execute("insert into diagnostic_inventory_slots(character_id,slot,item_id,count,revision,source_sha256,design_id) values(?,?,?,?,1,?,'CUSTOM-0015')",
                                   (identity,slot,3107 if slot==0 else 0,count if slot==0 else 0,ITEM_SOURCE))
                    db.execute("insert into character_trade_wallets values(?,?,1,'CUSTOM-0063')",(identity,money))
                db.commit()
            state.process=state.launch()
            a=self.enter_peer(state,lifetime,4,b'codexslow',950)
            b=self.enter_peer(state,lifetime,5,b'codexfixed',936)
            baseline=self.tables(state)
            yield state,a,b,baseline

    def records(self,state,game):
        try:
            batches=self.drain(state,game,first=True)
        except TimeoutError:
            self.fail('No trade response; private server log:\n'+state.log()[-6000:])
        output=[]
        for batch in batches:
            offset=0
            while offset<len(batch):
                size={0x27:5,0x3b:25,0x41:5,0x4e:19,0x4f:3,0x50:25,0x51:9,0x52:3,0x53:3}.get(batch[offset])
                self.assertIsNotNone(size,'Unexpected trade record '+hex(batch[offset])+'\n'+state.log()[-3000:])
                output.append(batch[offset:offset+size]);offset+=size
            self.assertEqual(offset,len(batch))
        return output

    def open(self,s,a,b,target=5):
        self.send(s,a,b'\x29'+struct.pack('<HH',target,0));x=self.records(s,a);y=self.records(s,b)
        self.assertEqual([r[0] for r in x],[0x4e,0x27]);self.assertEqual([r[0] for r in y],[0x4e,0x27])
        self.assertEqual(struct.unpack_from('<H',x[0],17)[0],target)
        self.assertEqual(struct.unpack_from('<H',y[0],17)[0],4)

    def offer(self,s,own,peer,target,quantity,fragmented=False):
        self.send(s,own,b'\x2a'+struct.pack('<HBBH',3107,0,quantity,target),fragmented)
        records=self.records(s,peer);self.assertEqual(len(records),1)
        expected=b'\x50'+bytes([quantity,0,0,0])+struct.pack('<H',3107)+bytes(18)
        self.assertEqual(records[0],expected)
        # Execute the actual delivered instance in the build-pinned consumer.
        native=PresentationOracle(qualified_image());native.call(0x49df10,0x21000000,body=records[0][1:])
        self.assertEqual(native.read(UI+0x867a8,24),expected[1:])
        s.helper.silent(own)

    def assert_restore(self,s,game,money,count):
        records=self.records(s,game);self.assertEqual(records[0][0],0x4f)
        self.assertEqual(records[-1],b'\x27'+struct.pack('<I',money))
        counts={r[3]:r[4] for r in records if r[0]==0x41}
        self.assertEqual(len(counts),30);self.assertEqual(counts[0],count)

    def test_offer_cancel_and_disconnect_restore_without_spending(self):
        with self.peers() as (s,a,b,before):
            self.open(s,a,b);self.offer(s,a,b,5,3,True);self.offer(s,b,a,4,2)
            self.assertEqual(self.tables(s),before)
            self.send(s,b,b'\x2d\0');self.assert_restore(s,a,1000,10);self.assert_restore(s,b,2000,8)
            self.assertEqual(self.tables(s),before)
            self.open(s,a,b);self.offer(s,a,b,5,3);b.close();self.assert_restore(s,a,1000,10)
            self.assertEqual(self.tables(s),before)

    def test_two_party_commit_coalesced_money_confirm_and_relogin(self):
        with self.peers() as (s,a,b,before):
            self.open(s,a,b);self.offer(s,a,b,5,3);self.offer(s,b,a,4,2)
            self.send(s,a,b'\x2b'+struct.pack('<HHI',5,0xa5a5,100)+b'\x2c\0')
            self.assertEqual(self.records(s,b),[b'\x51'+bytes(4)+struct.pack('<I',100),b'\x53\x01\0'])
            self.assertEqual(self.tables(s),before,'Single confirm spent assets')
            self.send(s,b,b'\x2b'+struct.pack('<HHI',4,0x1234,20)+b'\x2c\0')
            x,y=self.records(s,a),self.records(s,b)
            self.assertEqual([r[0] for r in x[:3]],[0x51,0x53,0x52]);self.assertEqual(y[0][0],0x52)
            self.assertEqual(x[-1],b'\x27'+struct.pack('<I',920));self.assertEqual(y[-1],b'\x27'+struct.pack('<I',2080))
            with closing(sqlite3.connect(s.database)) as db:
                self.assertEqual(db.execute('select character_id,amount from character_trade_wallets order by 1').fetchall(),[(4,920),(5,2080)])
                self.assertEqual(db.execute('select character_id,slot,item_id,count from diagnostic_inventory_slots where count>0 order by 1,2').fetchall(),
                    [(4,0,3107,7),(4,1,3107,2),(5,0,3107,6),(5,1,3107,3)])
                self.assertEqual(db.execute('select count(*) from character_trade_receipts').fetchone(),(1,))
            after=self.tables(s)
            for table in before:
                if table not in ('character_trade_wallets','diagnostic_inventory_slots','character_trade_receipts'):
                    self.assertEqual(before[table],after[table],'Unrelated table changed: '+table)
            a.close();b.close()
            with ExitStack() as reconnect:
                again=self.enter_peer(s,reconnect,4,b'codexslow',950)
                self.send(s,again,b'\x2c\0');self.assert_restore(s,again,920,7)
            self.assertEqual(self.tables(s),after,'Relogin or duplicate confirm replayed settlement')

    def test_bad_target_duplicate_and_mixed_mutation_do_not_commit(self):
        with self.peers() as (s,a,b,before):
            self.open(s,a,b)
            self.send(s,a,b'\x2a'+struct.pack('<HBBH',3107,0,3,99))
            self.assert_restore(s,a,1000,10);self.assert_restore(s,b,2000,8)
            self.open(s,a,b)
            self.send(s,a,b'\x2b'+struct.pack('<HHI',5,0,100)+b'\x2b'+struct.pack('<HHI',5,0,100))
            self.assert_restore(s,a,1000,10);self.assert_restore(s,b,2000,8)
            self.open(s,a,b)
            self.send(s,a,b'\x2d\0\x24\0\x01')
            self.assert_restore(s,a,1000,10);self.assert_restore(s,b,2000,8)
            self.assertEqual(self.tables(s),before)


if __name__=='__main__':unittest.main()
