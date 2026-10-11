"""Actual isolated bank Application TCP; native UI evidence is separate.

The NPC role and coordinates below are explicitly private test data. Formal
placement/role recovery is not established by this socket fixture.
"""
from contextlib import ExitStack,closing,contextmanager
import json,socket,sqlite3,struct,unittest
from unittest.mock import patch
import test_owned_role_text_server as fixture
import test_native_party_server as party
from tools.strike_lab.discard_fixture_27_20261002 import copy_catalog
from tools.strike_lab.bank_fixture_catalog_20261002 import copy_npc_catalog

SOURCE='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
IMAGE='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'

class NativeBankServerTests(unittest.TestCase):
    server=fixture.OwnedRoleTextServerTests.server
    drain=fixture.OwnedRoleTextServerTests.drain
    enter_peer=party.NativePartyServerTests.enter_peer
    send=party.NativePartyServerTests.send
    @classmethod
    def setUpClass(cls):fixture.OwnedRoleTextServerTests.setUpClass.__func__(cls)
    @contextmanager
    def peers(self,npc_x=128,bag_count=0):
        # Configure the fixture's owned launch endpoint before it is captured.
        # Never stop an unrelated port owner; fail if the port is occupied.
        with socket.socket() as probe:probe.bind(('127.0.0.1',2598))
        with patch.object(fixture.dual.RecoveredDualConnectionServerTests,'unused_port',return_value=2598),self.server() as s,ExitStack() as lifetime:
            s.helper.stop(s.process)
            cfg_path=s.database.parent/'config.json'
            config=json.loads(cfg_path.read_text('utf-8'))
            parent=s.database.parent/'private-native-blackbox-bank-tcp';parent.mkdir()
            target=parent/'town-diagnostic-accounts.db'
            with closing(sqlite3.connect(s.database)) as original,closing(sqlite3.connect(target)) as db:original.backup(db)
            s.database=target;s.endpoint=('127.0.0.1',2598)
            config['database']['path']=str(target);config['server'].update(port=2598,character_port=0)
            config['world']['owned_supply']={'enabled':True}
            cfg_path.write_text(json.dumps(config),encoding='utf-8')
            environment=s.helper.environment
            s.helper.environment=lambda:{**environment(),'GOD2_NATIVE_WORLD_RECORDS_LAB':'1'}
            with closing(sqlite3.connect(target)) as db:
                copy_catalog(db)
                copy_npc_catalog(db)
                peer=fixture.ROOT/'artifacts/playtests/private-weapon-peer-20260927-04/town-diagnostic-accounts.db'
                with closing(sqlite3.connect(peer.resolve().as_uri()+'?mode=ro',uri=True)) as source:
                    role=source.execute('select * from character_role_snapshots where character_id=5').fetchone()
                    resources=source.execute('select * from character_resources where character_id=5').fetchone()
                db.execute('insert or replace into character_role_snapshots values(?,?,?,?)',role)
                db.execute('insert or replace into character_resources values(?,?,?,?,?,?,?)',resources)
                db.execute('update recovered_positions set area=4,scene=3,x=129,y=126 where character_id=5')
                for identity in (4,5):
                    db.execute('delete from diagnostic_inventory_slots where character_id=? and slot<30',(identity,))
                    db.execute('delete from character_weapon_slot_metadata where character_id=? and slot<30',(identity,))
                    for slot in range(30):db.execute("insert into diagnostic_inventory_slots values(?,?,0,0,1,?,'CUSTOM-0015')",(identity,slot,SOURCE))
                    if bag_count:
                        db.execute('update diagnostic_inventory_slots set item_id=3107,count=? where character_id=? and slot=5',(bag_count,identity))
                    db.execute("insert into character_trade_wallets values(?,1000,1,'CUSTOM-0063')",(identity,))
                    db.execute("insert into character_bank_balances values(?,0,1,'CUSTOM-0064')",(identity,))
                    # Preallocate only this fixture's empty vault. Real startup
                    # creates no bank items; qualified opening allocates them.
                    if db.execute("select 1 from sqlite_master where name='character_bank_item_slots'").fetchone():
                        db.executemany("insert into character_bank_item_slots values(?,?,0,0,1,?,'CUSTOM-0015','CUSTOM-0065')",
                            [(identity,slot,'0'*64) for slot in range(300)])
                record=b'\x72'+struct.pack('<I',531)+bytes([21,0x60,0,0,1])+bytes(7)+struct.pack('<I',(126<<17)|(npc_x<<2))
                self.assertEqual(len(record),21)
                db.execute('insert into world_display_records values(4,3,114,531,?,?,?,?)',
                    (record,'ISOLATED_TEST_ONLY','explicit private test banker, not original placement',IMAGE))
                db.execute("insert into world_bank_service_points values(4,3,114,531,'ISOLATED_TEST_ONLY','explicit private test bank capability','CUSTOM-0064')")
                db.commit()
            s.process=s.launch()
            a=self.enter_peer(s,lifetime,4,b'codexslow',950)
            b=self.enter_peer(s,lifetime,5,b'codexfixed',936)
            yield s,a,b
    @staticmethod
    def rows(s):
        with closing(sqlite3.connect(s.database)) as db:
            return {name:(sql,sorted(repr(r) for r in db.execute('select * from "'+name.replace('"','""')+'"')))
                for name,sql in db.execute("select name,sql from sqlite_master where type='table'")}
    def response(self,s,game):
        try:return b''.join(self.drain(s,game,first=True))
        except TimeoutError:self.fail('Missing bank response:\n'+s.log()[-6000:])
    @staticmethod
    def sync(bank,wallet):return b'\x47'+struct.pack('<II',bank,0)+b'\x27'+struct.pack('<I',wallet)
    @staticmethod
    def request(opcode,amount,target=531):return bytes([opcode])+struct.pack('<IHH',amount,target,0xa5a5)
    def open(self,s,game,tail=b''):
        self.send(s,game,b'\x37'+struct.pack('<I',531)+tail)
        result=self.response(s,game)
        self.assertEqual(result[:13],b'\x46'+struct.pack('<I',531)+bytes(8))
        money=result[13:27]
        self.assert_empty_vault_projection(result[27:])
        return money
    def assert_empty_vault_projection(self,logical):
        self.assertEqual(len(logical),300*29)
        for index in range(300):
            expected=b'\x48'+bytes([index//50])+bytes(4)+bytes([index%50])+bytes(22)
            self.assertEqual(logical[index*29:(index+1)*29],expected)
    def test_two_languages_deposit_withdraw_close_disconnect_restart(self):
        with self.peers() as (s,a,b):
            before=self.rows(s)
            for game in (a,b):
                self.assertEqual(self.open(s,game,b'\x30\0'),self.sync(0,1000))
                self.send(s,game,self.request(0x61,300),True)
                self.assertEqual(self.response(s,game),self.sync(300,700))
                self.send(s,game,self.request(0x62,125))
                self.assertEqual(self.response(s,game),self.sync(175,825))
                self.send(s,game,b'\x39'+struct.pack('<HH',531,1));s.helper.silent(game)
                self.send(s,game,self.request(0x62,10));self.assertEqual(self.response(s,game),self.sync(175,825))
            after=self.rows(s)
            for table in before:
                if table not in ('character_trade_wallets','character_bank_balances','character_bank_receipts'):
                    self.assertEqual(after[table],before[table],'Unrelated save changed: '+table)
            with closing(sqlite3.connect(s.database)) as db:
                self.assertEqual(db.execute('select character_id,amount from character_bank_balances order by 1').fetchall(),[(4,175),(5,175)])
                self.assertEqual(db.execute('select count(*) from character_bank_receipts').fetchone(),(4,))
            a.close();b.close();s.helper.stop(s.process);s.process=s.launch()
            with ExitStack() as reconnect:
                game=self.enter_peer(s,reconnect,4,b'codexslow',950)
                self.send(s,game,self.request(0x62,1));self.assertEqual(self.response(s,game),self.sync(175,825))
                self.assertEqual(self.rows(s),after,'Restart replayed bank operation or altered saves')
                self.assertEqual(self.open(s,game),self.sync(175,825))
    def test_bad_target_signed_amount_duplicate_and_mixed_mutations(self):
        with self.peers() as (s,a,b):
            before=self.rows(s)
            for logical in (self.request(0x61,100,532),self.request(0x61,0),self.request(0x61,0x80000000),
                            self.request(0x61,100)+self.request(0x61,100),self.request(0x61,100)+b'\x24\0\x01'):
                self.open(s,a);self.send(s,a,logical)
                self.assertEqual(self.response(s,a),self.sync(0,1000));self.assertEqual(self.rows(s),before)
            # Preserve the existing unsupported-NPC rejection (connection
            # close); an absent service point must not become a bank opener.
            self.send(s,a,b'\x37'+struct.pack('<I',532));a.settimeout(2)
            self.assertEqual(a.recv(4096),b'','Unqualified NPC unexpectedly opened a bank')
            self.assertEqual(self.rows(s),before)

    def test_known_banker_refusal_preserves_active_trade_and_connection(self):
        with self.peers() as (s,a,b):
            before=self.rows(s)
            self.send(s,a,b'\x29'+struct.pack('<HH',5,0))
            for game in (a,b):
                opened=self.response(s,game)
                self.assertEqual(opened[0],0x4e)
                self.assertEqual(opened[-5:],b'\x27'+struct.pack('<I',1000))
            self.send(s,a,b'\x37'+struct.pack('<I',531)+b'\x30\0')
            s.helper.silent(a);s.helper.silent(b)
            self.assertEqual(self.rows(s),before,'Refused bank created or spent assets')
            self.send(s,a,b'\x2d\0')
            for game in (a,b):
                cancelled=self.response(s,game)
                self.assertEqual(cancelled[:3],b'\x4f\0\0')
                self.assertEqual(cancelled[-5:],b'\x27'+struct.pack('<I',1000))
            self.assertEqual(self.rows(s),before,'Bank refusal cancelled or settled trade')
            self.assertEqual(self.open(s,a),self.sync(0,1000))

    def test_coalesced_chat_and_distant_banker_refusal(self):
        text=b'Bank hello';chat=b'\x2f'+struct.pack('<H',len(text)+8)+bytes(4)+text+b'\0'
        for npc_x in (128,140):
            with self.peers(npc_x) as (s,a,b):
                before=self.rows(s)
                self.send(s,a,b'\x37'+struct.pack('<I',531)+b'\x30\0'+chat)
                own=self.response(s,a);other=self.response(s,b)
                if npc_x==128:
                    expected=b'\x46'+struct.pack('<I',531)+bytes(8)+self.sync(0,1000)
                    self.assertTrue(own.startswith(expected));own=own[len(expected):]
                    self.assert_empty_vault_projection(own[:300*29]);own=own[300*29:]
                for message in (own,other):
                    self.assertEqual(message[0],0x5c)
                    self.assertEqual(message[13:-1],b'slowgirl: Bank hello')
                self.assertEqual(self.rows(s),before,'Open/refusal/chat changed balances or unrelated saves')
                if npc_x==140:
                    self.send(s,a,self.request(0x61,100))
                    self.assertEqual(self.response(s,a),self.sync(0,1000))
                    self.assertEqual(self.rows(s),before,'Distant banker authorized deposit')

if __name__=='__main__':unittest.main()
