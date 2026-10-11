"""CUSTOM0075 actual TCP guild audience on disposable owned saves; not UI proof."""
from contextlib import contextmanager,closing,ExitStack
import struct,sqlite3,unittest
from test_native_private_chat_server_20261003 import PrivateChatTests

SHA='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
class GuildChatTests(PrivateChatTests):
    @contextmanager
    def server(self):
        with super().server() as s:
            with closing(sqlite3.connect(s.database)) as db:
                for identity,name,rev in ((1,'labguild',3),(2,'labother',4)):
                    db.execute('insert into owned_guilds values(?,?,?,?,?,?)',
                               (identity,name,rev,'CUSTOM_DESIGNED','CUSTOM-0075',SHA))
                db.executemany('insert into owned_guild_members values(?,?,?,?,?,?)',
                               ((4,1,2,'CUSTOM_DESIGNED','CUSTOM-0075',SHA),(5,1,3,'CUSTOM_DESIGNED','CUSTOM-0075',SHA)))
                db.commit()
            yield s
    def drain(self,s,peer,first=False):
        result=super().drain(s,peer,first=first)
        if first:self.initial_records=result
        return result
    def enter_peer(self,s,lifetime,identity,account,page):
        self.initial_records=[]
        peer=super().enter_peer(s,lifetime,identity,account,page)
        expected=b'\x2dlabguild'+bytes(8)
        if identity in (4,5):self.assertIn(expected,self.initial_records,'Guild2D must arrive in initial projection without another tick')
        else:self.assertFalse(any(wire and wire[0]==0x2d for wire in self.initial_records))
        s.helper.silent(peer);return peer
    def guild_name(self,s,peer,name,page=950):
        wire=s.decoder.logical(s.helper,peer)
        encoded=name.encode('cp'+str(page))
        self.assertEqual(wire,b'\x2d'+encoded+bytes(16-len(encoded)))
    @classmethod
    def guild(cls,text,page=950,selector=3,caller=0):
        return cls.chat(text.encode('cp'+str(page)),selector=selector,caller=caller)
    def display(self,s,peer,identity,name,text,page):
        wire=s.decoder.logical(s.helper,peer)
        self.assertEqual(wire[0],0x5c);self.assertEqual(len(wire),struct.unpack_from('<H',wire,1)[0])
        self.assertEqual(struct.unpack_from('<I',wire,5)[0],identity)
        self.assertEqual(wire[9],3|(0x80 if page==936 else 0))
        self.assertEqual(wire[13:-1],(name+': '+text).encode('cp'+str(page)))
        self.assertEqual(wire[-1],0)
    def test_bilingual_owned_guild_audience_header_not_authority(self):
        with self.three() as (s,first,other,outside):
            for sender,identity,name,page in ((first,4,'slowgirl',950),(other,5,'fixedgirl',936)):
                for selector,caller in ((3,0),(0x83,0xffff),(3,6),(0x83,4)):
                    text='宗派測試' if page==950 else '宗派测试'
                    self.send(s,sender,self.guild(text,page,selector,caller),fragmented=True)
                    self.display(s,first,identity,name,'宗派測試',950)
                    self.display(s,other,identity,name,'宗派测试',936)
                    self.silent(s,first,other,outside)
            for caller in (0,4,5,0xffff):
                self.send(s,outside,self.guild('outsider',caller=caller));self.silent(s,first,other,outside)
    def test_rejects_malformed_and_mixed_without_mutation(self):
        with self.three() as (s,first,other,outside):
            self.send(s,first,self.chat(b'\x81',selector=3));self.silent(s,first,other,outside)
            for suffix in (self.join(),b'\x1d\0\0',b'\x20'+b'forbidden'+bytes(7),
                           self.chat(b'common',selector=0),self.chat(b'party',selector=1),self.whisper('fixedgirl','private')):
                self.send(s,first,self.guild('mixed')+suffix);self.silent(s,first,other,outside)
            self.send(s,first,self.guild('one')+b'\x30\0'+self.guild('two'))
            for recipient,page in ((first,950),(other,936)):
                self.display(s,recipient,4,'slowgirl','one',page);self.display(s,recipient,4,'slowgirl','two',page)
            self.silent(s,first,other,outside)
    def test_live_membership_clear_restore_and_other_guild_isolation(self):
        with self.three() as (s,first,other,outside):
            with closing(sqlite3.connect(s.database)) as db:
                saved=db.execute('select * from owned_guild_members where character_id=4').fetchone()
                db.execute('delete from owned_guild_members where character_id=4');db.commit()
            self.send(s,first,self.guild('left-selected-still3'));self.guild_name(s,first,'');self.silent(s,first,other,outside)
            with closing(sqlite3.connect(s.database)) as db:
                db.execute('insert into owned_guild_members values(?,?,?,?,?,?)',saved)
                db.execute('insert into owned_guild_members values(6,2,4,?,?,?)',('CUSTOM_DESIGNED','CUSTOM-0075',SHA));db.commit()
            self.send(s,first,self.guild('restored'));self.guild_name(s,first,'labguild')
            self.display(s,first,4,'slowgirl','restored',950);self.display(s,other,4,'slowgirl','restored',936)
            self.send(s,outside,self.guild('otherguild'));self.guild_name(s,outside,'labother')
            self.display(s,outside,6,'outsidegirl','otherguild',950);self.silent(s,first,other,outside)
            with closing(sqlite3.connect(s.database)) as db:db.execute('delete from owned_guild_members where character_id=6');db.commit()
            self.send(s,outside,self.guild('removed'));self.guild_name(s,outside,'');self.silent(s,first,other,outside)
    def test_stale_owner_provenance_and_relogin(self):
        with self.three() as (s,first,other,outside):
            with closing(sqlite3.connect(s.database)) as db:db.execute('update recovered_characters set account_id=7 where id=4');db.commit()
            self.send(s,first,self.guild('wrong-owner'));self.silent(s,first,other,outside)
            with closing(sqlite3.connect(s.database)) as db:db.execute('update recovered_characters set account_id=4 where id=4');db.commit()
            with closing(sqlite3.connect(s.database)) as db:db.execute('update owned_guild_members set revision=4 where character_id=5');db.commit()
            self.send(s,first,self.guild('invalid-generation'))
            self.display(s,first,4,'slowgirl','invalid-generation',950);self.silent(s,first,other,outside)
            with closing(sqlite3.connect(s.database)) as db:db.execute('update owned_guild_members set revision=3 where character_id=5');db.commit()
            other.close();self.send(s,first,self.guild('offline-member'))
            self.display(s,first,4,'slowgirl','offline-member',950);self.silent(s,first,outside)
            with ExitStack() as lifetime:
                returned=self.enter_peer(s,lifetime,5,b'codexfixed',936)
                self.send(s,returned,self.guild('returned',936))
                self.display(s,first,5,'fixedgirl','returned',950);self.display(s,returned,5,'fixedgirl','returned',936)
                self.silent(s,first,returned,outside)
    def test_exact_chinese_guild_name_projection_in_both_codepages(self):
        with self.three() as (s,first,other,outside):
            with closing(sqlite3.connect(s.database)) as db:
                db.execute("update owned_guilds set name_utf8='仙界' where id=1");db.commit()
            try:
                for peer,page in ((first,950),(other,936)):
                    self.send(s,peer,b'\x30\0');self.guild_name(s,peer,'仙界',page)
                self.send(s,first,self.guild('名稱測試'))
                self.display(s,first,4,'slowgirl','名稱測試',950)
                self.display(s,other,4,'slowgirl','名称测试',936);self.silent(s,first,other,outside)
            finally:
                with closing(sqlite3.connect(s.database)) as db:
                    db.execute("update owned_guilds set name_utf8='labguild' where id=1");db.commit()
                for peer,page in ((first,950),(other,936)):
                    self.send(s,peer,b'\x30\0');self.guild_name(s,peer,'labguild',page)
    def test_movement_ack_party_position_before_guild_delivery(self):
        with self.three(allow_movement=True) as (s,first,other,outside):
            self.accepted(s,first,other)
            move=b'\x2e'+struct.pack('<HHBB',127,126,1,0xa5)
            self.send(s,first,move+self.guild('moved'))
            self.assertEqual(s.decoder.logical(s.helper,first)[0],0x5d)
            self.display(s,first,4,'slowgirl','moved',950)
            self.assertEqual(s.decoder.logical(s.helper,other)[0],0x56)
            self.display(s,other,4,'slowgirl','moved',936);self.silent(s,first,other,outside)
            self.send(s,first,self.guild('bad-move-mixed')+move+self.whisper('fixedgirl','private'))
            self.silent(s,first,other,outside)
            self.send(s,first,b'\x5a'+struct.pack('<H',4)+bytes(16));self.removed(s,first,4,b'slowgirl');self.removed(s,other,4,b'slowgirl')

def load_tests(loader,tests,pattern):
    suite=unittest.TestSuite()
    for name in GuildChatTests.__dict__:
        if name.startswith('test_'):suite.addTest(GuildChatTests(name))
    return suite
if __name__=='__main__':unittest.main()
