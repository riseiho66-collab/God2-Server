"""Actual disposable Application bank items; no original placements claimed."""
from contextlib import ExitStack,closing,contextmanager
import sqlite3,struct,unittest
import test_native_bank_server as bank
from tools.strike_lab.current_bank_items_20261002 import ItemsOracle,UI,BODY
from tools.strike_lab.current_protocol_coverage import qualified_image

class NativeBankItemsServerTests(unittest.TestCase):
    server=bank.NativeBankServerTests.server
    drain=bank.NativeBankServerTests.drain
    enter_peer=bank.NativeBankServerTests.enter_peer
    send=bank.NativeBankServerTests.send
    rows=staticmethod(bank.NativeBankServerTests.rows)
    response=bank.NativeBankServerTests.response
    @classmethod
    def setUpClass(cls):bank.NativeBankServerTests.setUpClass.__func__(cls)
    @contextmanager
    def peers(self):
        with bank.NativeBankServerTests.peers(self,bag_count=10) as peers:yield peers
    @staticmethod
    def request(opcode,page,source,destination,quantity=1,target=531):
        return bytes([opcode])+struct.pack('<HBBBB',target,page,source,destination,quantity)
    def records(self,s,game):
        out=[]
        for batch in self.drain(s,game,first=True):
            self.assertLessEqual(len(batch),0xa00,'Unbounded native frame')
            at=0
            while at<len(batch):
                n={0x46:13,0x47:9,0x27:5,0x48:29,0x41:5,0x3b:25}.get(batch[at])
                if batch[at]==0x5c:n=int.from_bytes(batch[at+1:at+3],'little')
                self.assertIsNotNone(n,'Unexpected bank item response')
                self.assertLessEqual(at+n,len(batch));out.append(batch[at:at+n]);at+=n
        return out
    def opened(self,s,game):
        self.send(s,game,b'\x37'+struct.pack('<I',531)+b'\x30\0')
        records=self.records(s,game)
        self.assertEqual([r[0] for r in records[:3]],[0x46,0x47,0x27])
        slots=records[3:];self.assertEqual(len(slots),300)
        self.assertEqual({(r[1],r[6]) for r in slots},{(p,i) for p in range(6) for i in range(50)})
        self.assertTrue(all(r[0]==0x48 for r in slots));return slots
    def verify_slots(self,records,expected):
        actual={(r[1],r[6]):(r[5],int.from_bytes(r[9:11],'little')) for r in records if r[0]==0x48}
        self.assertEqual(actual,expected)
        # Consume actual serialized C++48 replies in the pinned native
        # function, with the original catalogue/icon/count rendering path.
        o=ItemsOracle(qualified_image())
        for r in records:
            if r[0]!=0x48:continue
            o.call(0x471e50,BODY,body=r[1:])
            cell=o.read(o.cell(r[1],r[6]),24)
            self.assertEqual(cell[:2],bytes([r[5],r[6]]));self.assertEqual(cell[4:],r[9:])
    def saved(self,s):
        with closing(sqlite3.connect(s.database)) as db:
            return {'bag':db.execute('select character_id,slot,item_id,count,revision from diagnostic_inventory_slots where count>0 order by 1,2').fetchall(),
                    'vault':db.execute('select character_id,slot,item_id,count,revision from character_bank_item_slots where count>0 order by 1,2').fetchall(),
                    'receipts':db.execute('select count(*) from character_bank_item_receipts').fetchone()[0]}
    def test_two_languages_partial_whole_move_and_persisted_reopen(self):
        with self.peers() as (s,a,b):
            before=self.rows(s)
            for game in (a,b):
                self.opened(s,game)
                self.send(s,game,self.request(0x63,0,5,2,3),True)
                records=self.records(s,game);self.verify_slots(records,{(0,2):(3,3107)})
                self.assertEqual(records[-1],b'\x41'+struct.pack('<HBB',3107,5,7))
                self.send(s,game,self.request(0x65,0,2,3))
                self.verify_slots(self.records(s,game),{(0,2):(0,0),(0,3):(3,3107)})
                self.send(s,game,self.request(0x64,0,3,6,2))
                self.verify_slots(self.records(s,game),{(0,3):(1,3107)})
                self.send(s,game,self.request(0x63,1,5,4,7))
                self.verify_slots(self.records(s,game),{(1,4):(7,3107)})
                self.send(s,game,b'\x39'+struct.pack('<HH',531,1));s.helper.silent(game)
                cells=self.opened(s,game)
                self.verify_slots([r for r in cells if (r[1],r[6]) in ((0,3),(1,4))],{(0,3):(1,3107),(1,4):(7,3107)})
            after=self.rows(s)
            for name in before:
                if name not in ('diagnostic_inventory_slots','character_bank_item_slots','character_bank_item_receipts'):
                    self.assertEqual(before[name],after[name],'Unrelated or monetary state changed: '+name)
            saved=self.saved(s);self.assertEqual(saved['receipts'],8)
            self.assertEqual(saved['vault'],[(4,3,3107,1,3),(4,54,3107,7,2),(5,3,3107,1,3),(5,54,3107,7,2)])
            self.assertEqual(saved['bag'],[(4,6,3107,2,2),(5,6,3107,2,2)])
            a.close();b.close();s.helper.stop(s.process);s.process=s.launch()
            with ExitStack() as life:
                game=self.enter_peer(s,life,4,b'codexslow',950);cells=self.opened(s,game)
                self.verify_slots([r for r in cells if (r[1],r[6]) in ((0,3),(1,4))],{(0,3):(1,3107),(1,4):(7,3107)})
                self.assertEqual(self.rows(s),after,'Restart/open replayed writes or changed saved assets')
    def test_bad_target_reserved_pages_quantity_duplicates_and_mixed_money(self):
        with self.peers() as (s,a,b):
            before=self.rows(s)
            requests=[self.request(0x63,0,5,2,1,532),self.request(0x63,3,5,2),self.request(0x63,0,5,0),
                self.request(0x63,0,5,2,0),self.request(0x63,0,5,2,255),self.request(0x63,0,5,2)*2,
                self.request(0x63,0,5,2)+bank.NativeBankServerTests.request(0x61,1),
                self.request(0x63,0,5,2)+b'\x24\0\x01']
            for request in requests:
                self.opened(s,a);self.send(s,a,request);records=self.records(s,a)
                self.assertEqual(sum(r[0]==0x48 for r in records),300)
                self.assertEqual(self.rows(s),before,'Rejected request spent or created items/money')
            self.opened(s,a);self.send(s,a,b'\x39'+struct.pack('<HH',531,1));s.helper.silent(a)
            self.send(s,a,self.request(0x63,0,5,2));s.helper.silent(a)
            self.assertEqual(self.rows(s),before,'Closed-bank item request retained authority')
    def test_coalesced_chat_and_other_character_snapshot_are_preserved(self):
        with self.peers() as (s,a,b):
            self.opened(s,a);self.opened(s,b);before=self.rows(s)
            text=b'Bank items';chat=b'\x2f'+struct.pack('<H',len(text)+8)+bytes(4)+text+b'\0'
            self.send(s,a,self.request(0x63,0,5,2,3)+b'\x30\0'+chat)
            own,other=self.records(s,a),self.records(s,b)
            self.verify_slots([r for r in own if r[0]!=0x5c],{(0,2):(3,3107)})
            for response in (own[-1],other[-1]):
                self.assertEqual(response[0],0x5c);self.assertEqual(response[13:-1],b'slowgirl: Bank items')
            # Character5's pre-opened snapshot is independently valid.
            self.send(s,b,self.request(0x63,1,5,2,4));self.verify_slots(self.records(s,b),{(1,2):(4,3107)})
            saved=self.saved(s);self.assertEqual(saved['receipts'],2)
            self.assertEqual(saved['vault'],[(4,2,3107,3,2),(5,52,3107,4,2)])
            after=self.rows(s)
            for name in before:
                if name not in ('diagnostic_inventory_slots','character_bank_item_slots','character_bank_item_receipts'):
                    self.assertEqual(before[name],after[name],'Cross-character/chat altered unrelated state')

    def test_occupied_native65_swaps_whole_stacks_and_rejects_restore_both_cells(self):
        with self.peers() as (s,a,b):
            initial=self.rows(s)
            for game in (a,b):
                self.opened(s,game)
                for destination,quantity in ((2,3),(3,7)):
                    self.send(s,game,self.request(0x63,0,5,destination,quantity))
                    self.verify_slots(self.records(s,game),{(0,destination):(quantity,3107)})
                for source,destination,expected in (
                    (2,3,{(0,2):(7,3107),(0,3):(3,3107)}),
                    (3,2,{(0,2):(3,3107),(0,3):(7,3107)}),
                    (2,3,{(0,2):(7,3107),(0,3):(3,3107)})):
                    self.send(s,game,self.request(0x65,0,source,destination),True)
                    records=self.records(s,game)
                    self.assertEqual([r[0] for r in records],[0x48,0x48])
                    self.verify_slots(records,expected)
                before_rejection=self.rows(s)
                for request in (self.request(0x65,0,2,3,2),self.request(0x65,0,2,2),
                                self.request(0x65,0,4,3),self.request(0x65,0,2,0),
                                self.request(0x65,0,2,3,1,532)):
                    self.send(s,game,request)
                    records=self.records(s,game)
                    self.assertEqual(sum(r[0]==0x48 for r in records),300)
                    self.verify_slots([r for r in records if r[0]==0x48 and r[1]==0 and r[6] in (2,3)],
                                      {(0,2):(7,3107),(0,3):(3,3107)})
                    self.assertEqual(self.rows(s),before_rejection,'Rejected swap changed saved assets')
                    self.opened(s,game)
            saved=self.saved(s)
            self.assertEqual(saved['receipts'],10)
            self.assertEqual(saved['vault'],[(4,2,3107,7,5),(4,3,3107,3,5),(5,2,3107,7,5),(5,3,3107,3,5)])
            self.assertEqual(saved['bag'],[])
            after=self.rows(s)
            for name in initial:
                if name not in ('diagnostic_inventory_slots','character_bank_item_slots','character_bank_item_receipts'):
                    self.assertEqual(initial[name],after[name],'Swap altered unrelated player or monetary state: '+name)
            a.close();b.close();s.helper.stop(s.process);s.process=s.launch()
            with ExitStack() as life:
                for identity,name,language in ((4,b'codexslow',950),(5,b'codexfixed',936)):
                    game=self.enter_peer(s,life,identity,name,language)
                    slots=self.opened(s,game)
                    self.verify_slots([r for r in slots if r[1]==0 and r[6] in (2,3)],
                                      {(0,2):(7,3107),(0,3):(3,3107)})
                self.assertEqual(self.rows(s),after,'Restart/relogin changed whole-cell swap state')

if __name__=='__main__':unittest.main()
