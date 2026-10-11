"""Actual Application party chat; disposable loopback fixture, no formal saves."""
import sqlite3
import struct
import unittest
from contextlib import closing
from test_native_party_server import NativePartyServerTests


class PartyChatTests(NativePartyServerTests):
    @staticmethod
    def chat(text, selector=1, padding=0xa5, target=0):
        return b'\x2f'+struct.pack('<HBBH',len(text)+8,selector,padding,target)+text+b'\0'

    def message(self,s,recipient,identity,name,page,text,mode=1):
        response=s.decoder.logical(s.helper,recipient)
        self.assertEqual(response[0],0x5c)
        self.assertEqual(struct.unpack_from('<H',response,1)[0],len(response))
        self.assertEqual(struct.unpack_from('<I',response,5)[0],identity)
        self.assertEqual(response[9],mode|(0x80 if page==936 else 0))
        self.assertEqual(response[13:-1],name+b': '+text.encode('cp'+str(page)))
        self.assertEqual(response[-1],0)

    def test_party_chat_ungrouped_deny_then_owned_bilingual_headers(self):
        with self.peers() as (s,first,other):
            self.send(s,first,self.chat(b'ungrouped'));s.helper.silent(first);s.helper.silent(other)
            self.accepted(s,first,other)
            for owner,identity,name,page in ((first,4,b'slowgirl',950),(other,5,b'fixedgirl',936)):
                for selector,target in ((1,0),(0x81,0xffff),(1,0xff00)):
                    text=('隊伍測試' if page==950 else '队伍测试').encode('cp'+str(page))
                    self.send(s,owner,self.chat(text,selector=selector,target=target),fragmented=True)
                    for recipient,recipient_page,expected in ((first,950,'隊伍測試'),(other,936,'队伍测试')):
                        self.message(s,recipient,identity,name,recipient_page,expected)
            self.assertEqual(s.log().count('delivered=2 accepted=true CUSTOM-0073'),6)

    def test_party_chat_multiple_messages_and_mutating_mix_denied(self):
        with self.peers() as (s,first,other):
            self.accepted(s,first,other)
            for suffix in (self.join(),b'\x1d\0\0',b'\x59'+struct.pack('<H',5)+bytes(16),self.chat(b'common',selector=0)):
                self.send(s,first,self.chat(b'mixed')+suffix);s.helper.silent(first);s.helper.silent(other)
            self.send(s,first,self.chat(b'one')+b'\x30\0'+self.chat(b'two'))
            for recipient,page in ((first,950),(other,936)):
                for text in ('one','two'):self.message(s,recipient,4,b'slowgirl',page,text)
            # Accepted common path must retain original mode0 and broadcast.
            self.send(s,other,self.chat(b'common-survives',selector=0))
            for recipient,page in ((first,950),(other,936)):
                self.message(s,recipient,5,b'fixedgirl',page,'common-survives',mode=0)

    def test_party_chat_stale_revision_leave_rejoin(self):
        with self.peers() as (s,first,other):
            self.accepted(s,first,other)
            with closing(sqlite3.connect(s.database)) as db:
                revision=db.execute('select revision from recovered_positions where character_id=5').fetchone()[0]
                db.execute('update recovered_positions set revision=revision+1 where character_id=5');db.commit()
            try:
                self.send(s,first,self.chat(b'stale'));s.helper.silent(first);s.helper.silent(other)
            finally:
                with closing(sqlite3.connect(s.database)) as db:
                    db.execute('update recovered_positions set revision=? where character_id=5',(revision,));db.commit()
            self.send(s,first,b'\x5a'+struct.pack('<H',4)+bytes(16))
            for peer in (first,other):self.removed(s,peer,4,b'slowgirl')
            for peer in (first,other):
                self.send(s,peer,self.chat(b'left'));s.helper.silent(peer)
            self.accepted(s,first,other)
            self.send(s,other,self.chat(b'back'))
            for recipient,page in ((first,950),(other,936)):self.message(s,recipient,5,b'fixedgirl',page,'back')


def load_tests(loader,tests,pattern):
    return unittest.TestSuite(PartyChatTests(name) for name in (
        'test_party_chat_ungrouped_deny_then_owned_bilingual_headers',
        'test_party_chat_multiple_messages_and_mutating_mix_denied',
        'test_party_chat_stale_revision_leave_rejoin',
    ))
