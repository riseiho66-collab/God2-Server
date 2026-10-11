"""CUSTOM0076 actual own-server TCP notifications and roster reconciliation."""
from contextlib import closing
import sqlite3,struct,unittest
from test_native_guild_chat_server_20261003 import GuildChatTests
class GuildRosterTests(GuildChatTests):
    def prime(self,s,*peers):
        for peer in peers:
            self.send(s,peer,b'\x30\0');self.drain(s,peer)
        self.silent(s,*peers)
    def test_panel_notification_preserves_all_four_chat_channels(self):
        with self.three() as (s,first,other,outside):
            self.prime(s,first,other,outside)
            self.send(s,first,b'\xb8\0'+self.chat(b'notify-common',selector=0),fragmented=True)
            for peer,page in ((first,950),(other,936),(outside,950)):
                self.ordinary_message(s,peer,4,b'slowgirl',page,'notify-common',0)
            self.accepted(s,first,other);self.silent(s,outside)
            self.send(s,other,b'\xb8\0'+self.chat(b'notify-party',selector=1))
            for peer,page in ((first,950),(other,936)):
                self.ordinary_message(s,peer,5,b'fixedgirl',page,'notify-party',1)
            self.send(s,first,self.whisper('fixedgirl','notify-private')+b'\xb8\0')
            for peer,page in ((first,950),(other,936)):
                self.message(s,peer,4,'slowgirl','fixedgirl',page,'notify-private')
            self.send(s,other,self.guild('notify-guild',936)+b'\xb8\0')
            for peer,page in ((first,950),(other,936)):
                self.display(s,peer,5,'fixedgirl','notify-guild',page)
            self.silent(s,first,other,outside)
            self.send(s,outside,b'\xb8\0');self.silent(s,first,other,outside)
            self.assertIn('OWNED_GUILD_PANEL_NOTIFICATION',s.log())
            self.assertIn('admitted=false CUSTOM-0076',s.log())
    def test_malformed_notification_rejects_entire_batch_and_closes_source(self):
        with self.three() as (s,first,other,outside):
            self.prime(s,first,other,outside)
            self.send(s,first,b'\xb8\x01'+self.guild('malformed'))
            self.assertEqual(first.recv(1),b'')
            for peer in (other,outside):
                for record in self.drain(s,peer):
                    self.assertNotEqual(record[0],0x5c,'Malformed batch leaked chat')
                self.silent(s,peer)
    def test_saved_level_update_and_membership_remove_restore_native_batches(self):
        with self.three() as (s,first,other,outside):
            self.prime(s,first,other,outside)
            with closing(sqlite3.connect(s.database)) as db:
                role=db.execute('select * from character_role_snapshots where character_id=5').fetchone()
                member=db.execute('select * from owned_guild_members where character_id=4').fetchone()
                changed=bytearray(role[1]);changed[1]=99
                db.execute('update character_role_snapshots set logical=?,revision=revision+1 where character_id=5',(changed,));db.commit()
            try:
                self.send(s,first,b'\xb8\0')
                wire=s.decoder.logical(s.helper,first)
                self.assertEqual(wire[:2],b'\x92\x01');self.assertEqual(len(wire),46)
                self.assertEqual(wire[2:4],b'\x91\0');self.assertEqual(wire[24:28],bytes([0x91,1,1,99]))
                self.send(s,first,b'\xb8\0');self.silent(s,first,other,outside)
                with closing(sqlite3.connect(s.database)) as db:
                    db.execute('delete from owned_guild_members where character_id=4');db.commit()
                self.send(s,first,b'\x30\0');self.guild_name(s,first,'')
                self.assertEqual(s.decoder.logical(s.helper,first),bytes([0x92,1,0x92,0]))
                self.send(s,first,b'\xb8\0');self.silent(s,first,other,outside)
                with closing(sqlite3.connect(s.database)) as db:
                    db.execute('insert into owned_guild_members values(?,?,?,?,?,?)',member);db.commit()
                self.send(s,first,b'\xb8\0');self.guild_name(s,first,'labguild')
                wire=s.decoder.logical(s.helper,first);self.assertEqual(len(wire),44)
                self.assertEqual(wire[:2],bytes([0x91,0]));self.assertEqual(wire[22:26],bytes([0x91,1,1,99]))
                self.silent(s,first,other,outside)
            finally:
                with closing(sqlite3.connect(s.database)) as db:
                    db.execute('insert or replace into character_role_snapshots values(?,?,?,?)',role)
                    db.execute('insert or replace into owned_guild_members values(?,?,?,?,?,?)',member);db.commit()
def load_tests(loader,tests,pattern):
    return unittest.TestSuite(GuildRosterTests(name) for name in GuildRosterTests.__dict__ if name.startswith('test_'))
if __name__=='__main__':unittest.main()
