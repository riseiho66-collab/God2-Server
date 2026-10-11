"""Real Application TCP regression of6F segmentation; synthetic peers, not UI."""
from contextlib import closing
import sqlite3,struct,unittest
from test_native_guild_panel_server_20261003 import GuildPanelTests

class GuildMembershipTests(GuildPanelTests):
    @staticmethod
    def membership(context=1,operation=0):
        name=b'Candidate'+b'\0'+bytes([0xa5])*6
        return b'\x6f'+struct.pack('<HH',context,0xffff)+name+bytes([operation,0xa5])
    def test_unsolicited_membership_does_not_mutate_or_break_ordered_common_chat(self):
        with self.three() as (s,first,other,outside):
            self.prime(s,first,other,outside);before=self.saved_rows(s)
            self.send(s,first,self.chat(b'before6f',selector=0)+self.membership()+self.chat(b'after6f',selector=0))
            for peer,cp in ((first,950),(other,936),(outside,950)):
                for text in ('before6f','after6f'):self.ordinary_message(s,peer,4,b'slowgirl',cp,text,0)
            self.silent(s,first,other,outside);self.assertEqual(self.saved_rows(s),before)
            self.assertIn('OWNED_GUILD_MEMBERSHIP_REQUEST',s.log());self.assertIn('accepted=false scope=disposable_lab',s.log())
    def test_tick_or_notification_or_help_before6f_cannot_refresh_stale_leave_lease(self):
        for prefix in (b'\x30\0',b'\xb8\0',self.help_request):
            with self.subTest(prefix=prefix.hex()),self.mutation_three() as (s,first,other,outside):
                self.prime(s,first,other,outside)
                with closing(sqlite3.connect(s.database)) as db:
                    db.execute('update owned_guild_members set guild_id=2,revision=4 where character_id=4');db.commit()
                before=self.saved_rows(s)
                self.send(s,first,prefix+self.membership()+b'\x73\0')
                for peer in (first,other,outside):
                    for wire in self.drain(s,peer):self.assertNotEqual(wire[0],0x5c)
                    self.silent(s,peer)
                self.assertEqual(self.saved_rows(s),before)
                self.assertIn('slot=0 committed=false CUSTOM-0077',s.log())
    def test_current_leave_still_commits_with6f_marker_and_later_marker_is_denied(self):
        with self.mutation_three() as (s,first,other,outside):
            self.prime(s,first,other,outside)
            self.send(s,first,self.membership()+b'\x73\0'+self.membership(2))
            self.guild_name(s,first,'')
            self.assertEqual(s.decoder.logical(s.helper,first),b'\x92\1\x92\0')
            self.assertEqual(s.decoder.logical(s.helper,other)[:4],b'\x92\1\x91\0')
            self.silent(s,first,other,outside)
            with closing(sqlite3.connect(s.database)) as db:
                self.assertIsNone(db.execute('select 1 from owned_guild_members where character_id=4').fetchone())
            self.assertIn('slot=0 committed=true CUSTOM-0077',s.log())
            self.assertEqual(s.log().count('OWNED_GUILD_MEMBERSHIP_REQUEST'),2)
    def test_malformed6f_rejects_entire_batch_without_chat_escape(self):
        for bad in (self.membership()[:-1],self.membership(operation=2),b'\x6f'+bytes(4)+b'A'*16+bytes(2)):
            with self.subTest(bad=bad.hex()),self.three() as (s,first,other,outside):
                self.prime(s,first,other,outside)
                self.send(s,first,self.chat(b'must-not-leak6f',selector=0)+bad)
                self.assertEqual(first.recv(1),b'')
                for peer in (other,outside):
                    for wire in self.drain(s,peer):self.assertNotEqual(wire[0],0x5c)
                    self.silent(s,peer)

def load_tests(loader,tests,pattern):
    return unittest.TestSuite(GuildMembershipTests(name) for name in GuildMembershipTests.__dict__ if name.startswith('test_'))
if __name__=='__main__':unittest.main()
