"""CUSTOM0077 actual Application TCP; member header/self-leave, not UI proof."""
from contextlib import closing,contextmanager
import sqlite3,unittest
from test_native_guild_roster_server_20261003 import GuildRosterTests
class GuildPanelTests(GuildRosterTests):
    help_request=b'\x37\x7b\x08\0\0'
    def panel_header(self,s,peer,count=2):
        wire=s.decoder.logical(s.helper,peer);expected=bytearray(53)
        expected[0]=0x8e;expected[14]=6;expected[20]=count;expected[24]=50
        self.assertEqual(wire,bytes(expected))
    def saved_rows(self,s):
        with closing(sqlite3.connect(s.database)) as db:
            return {name:sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"'))
                    for (name,) in db.execute("select name from sqlite_schema where type='table' order by name").fetchall()}
    @contextmanager
    def mutation_three(self):
        # New0077 tests deliberately mutate OWNED disposable memberships or
        # revisions. Restore only these test-fixture rows before the frozen
        # inherited private-chat context checks that all saved data is exact.
        with self.three() as state:
            s=state[0]
            with closing(sqlite3.connect(s.database)) as db:
                tables={name:([r[1] for r in db.execute('pragma table_info('+name+')')],
                               db.execute('select * from '+name).fetchall())
                        for name in ('owned_guild_members','owned_guilds','character_role_snapshots')}
            try:yield state
            finally:
                with closing(sqlite3.connect(s.database)) as db:
                    db.execute('begin immediate');db.execute('drop trigger if exists test_leave_abort')
                    db.execute('delete from owned_guild_members')
                    columns,rows=tables['owned_guild_members']
                    db.executemany('insert into owned_guild_members values('+','.join('?' for _ in columns)+')',rows)
                    for name,key in (('owned_guilds','id'),('character_role_snapshots','character_id')):
                        columns,rows=tables[name];index=columns.index(key)
                        assigns=','.join('"'+c+'"=?' for c in columns if c!=key)
                        for row in rows:
                            values=tuple(value for i,value in enumerate(row) if i!=index)+(row[index],)
                            self.assertEqual(db.execute('update '+name+' set '+assigns+' where '+key+'=?',values).rowcount,1)
                    db.commit()
    def test_self_leave_both_locales_owner_only_and_last_member_retained_clock(self):
        for identity in (4,5):
            with self.subTest(identity=identity),self.mutation_three() as (s,first,other,outside):
                self.prime(s,first,other,outside)
                sender,remaining=(first,other) if identity==4 else (other,first)
                page=950 if identity==4 else 936;name='slowgirl' if identity==4 else 'fixedgirl'
                before=self.saved_rows(s)
                with closing(sqlite3.connect(s.database)) as db:
                    remaining_row=db.execute('select * from owned_guild_members where character_id!=?',(identity,)).fetchone()
                    other_guild=db.execute('select * from owned_guilds where id=2').fetchone()
                self.send(s,sender,b'\x73\0'+self.chat(b'leave-common',selector=0),fragmented=True)
                self.guild_name(s,sender,'',page)
                self.assertEqual(s.decoder.logical(s.helper,sender),b'\x92\1\x92\0')
                refreshed=s.decoder.logical(s.helper,remaining)
                self.assertEqual(refreshed[:4],b'\x92\1\x91\0');self.assertEqual(len(refreshed),24)
                for peer,cp in ((first,950),(other,936),(outside,950)):
                    self.ordinary_message(s,peer,identity,name.encode('ascii'),cp,'leave-common',0)
                after=self.saved_rows(s)
                self.assertEqual({k:v for k,v in before.items() if k not in ('owned_guilds','owned_guild_members')},
                                 {k:v for k,v in after.items() if k not in ('owned_guilds','owned_guild_members')})
                with closing(sqlite3.connect(s.database)) as db:
                    self.assertEqual(db.execute('select * from owned_guild_members').fetchall(),[remaining_row])
                    self.assertEqual(db.execute('select * from owned_guilds where id=2').fetchone(),other_guild)
                    self.assertEqual(db.execute('select revision from owned_guilds where id=1').fetchone(),(5,))
                # Duplicate confirmation and stale selected-guild input stay
                # denied; unrelated owned private chat still works.
                target='fixedgirl' if identity==4 else 'slowgirl'
                self.send(s,sender,b'\x73\0'+self.whisper(target,'after-leave-private'))
                for peer,cp in ((first,950),(other,936)):
                    self.message(s,peer,identity,name,target,cp,'after-leave-private')
                self.send(s,sender,self.guild('after-leave-guild',page)+self.help_request)
                self.silent(s,first,other,outside)
                self.assertEqual(self.saved_rows(s),after)
                self.send(s,remaining,b'\x73\0');self.guild_name(s,remaining,'')
                self.assertEqual(s.decoder.logical(s.helper,remaining),b'\x92\0')
                with closing(sqlite3.connect(s.database)) as db:
                    self.assertEqual(db.execute('select * from owned_guild_members').fetchall(),[])
                    self.assertEqual(db.execute('select revision from owned_guilds where id=1').fetchone(),(6,))
                self.silent(s,first,other,outside)
                self.assertEqual(s.log().count('slot=0 committed=true CUSTOM-0077'),2)
    def test_foreign_slot_nonmember_and_stale_snapshot_do_not_authorize_leave(self):
        with self.mutation_three() as (s,first,other,outside):
            self.prime(s,first,other,outside);before=self.saved_rows(s)
            for sender,slot in ((first,1),(first,49),(outside,0)):
                self.send(s,sender,bytes([0x73,slot]));self.silent(s,first,other,outside)
                self.assertEqual(self.saved_rows(s),before)
            with closing(sqlite3.connect(s.database)) as db:
                db.execute('update character_role_snapshots set revision=revision+1 where character_id=5');db.commit()
            stale=self.saved_rows(s)
            self.send(s,first,b'\x73\0');self.silent(s,first,other,outside)
            self.assertEqual(self.saved_rows(s),stale)
            self.send(s,first,self.chat(b'denied-leave-common',selector=0))
            for peer,cp in ((first,950),(other,936),(outside,950)):
                self.ordinary_message(s,peer,4,b'slowgirl',cp,'denied-leave-common',0)
    def test_failed_storage_rolls_back_without_breaking_coalesced_guild_chat(self):
        with self.mutation_three() as (s,first,other,outside):
            self.prime(s,first,other,outside)
            with closing(sqlite3.connect(s.database)) as db:
                db.execute("create trigger test_leave_abort before delete on owned_guild_members begin select raise(abort,'test failure'); end");db.commit()
            before=self.saved_rows(s)
            self.send(s,first,b'\x73\0'+self.guild('rollback-guild'))
            for peer,cp in ((first,950),(other,936)):
                self.display(s,peer,4,'slowgirl','rollback-guild',cp)
            self.silent(s,first,other,outside);self.assertEqual(self.saved_rows(s),before)
            self.assertIn('slot=0 committed=false CUSTOM-0077',s.log())
    def test_truncated_leave_rejects_entire_batch_without_chat_leak(self):
        with self.three() as (s,first,other,outside):
            self.prime(s,first,other,outside)
            self.send(s,first,self.guild('must-not-escape')+b'\x73')
            self.assertEqual(first.recv(1),b'')
            for peer in (other,outside):
                for record in self.drain(s,peer):self.assertNotEqual(record[0],0x5c)
                self.silent(s,peer)
    def test_stale_leave_not_reauthorized_by_same_batch_tick_notification_or_help(self):
        for prefix in (b'\x30\0',b'\xb8\0',self.help_request):
            with self.subTest(prefix=prefix.hex()),self.mutation_three() as (s,first,other,outside):
                self.prime(s,first,other,outside)
                with closing(sqlite3.connect(s.database)) as db:
                    db.execute('update owned_guild_members set guild_id=2,revision=4 where character_id=4');db.commit()
                before=self.saved_rows(s)
                self.send(s,first,prefix+b'\x73\0')
                for peer in (first,other,outside):
                    for wire in self.drain(s,peer):self.assertNotEqual(wire[0],0x5c)
                    self.silent(s,peer)
                self.assertEqual(self.saved_rows(s),before)
                self.assertIn('slot=0 committed=false CUSTOM-0077',s.log())
    def test_guild_chat_before_leave_delivered_after_leave_denied_in_native_order(self):
        with self.mutation_three() as (s,first,other,outside):
            self.prime(s,first,other,outside)
            self.send(s,first,self.guild('before-successful-leave')+b'\x73\0'+self.guild('after-successful-leave'))
            self.display(s,first,4,'slowgirl','before-successful-leave',950)
            self.display(s,other,4,'slowgirl','before-successful-leave',936)
            self.guild_name(s,first,'')
            self.assertEqual(s.decoder.logical(s.helper,first),b'\x92\1\x92\0')
            self.assertEqual(s.decoder.logical(s.helper,other)[:4],b'\x92\1\x91\0')
            self.silent(s,first,other,outside)
            lines=[line for line in s.log().splitlines() if 'NATIVE_GUILD_CHAT_REQUEST ' in line or 'OWNED_GUILD_SELF_LEAVE ' in line]
            self.assertIn('accepted=true',lines[-3]);self.assertIn('committed=true',lines[-2]);self.assertIn('accepted=false',lines[-1])
    def test_open_reopen_both_locales_no_unsolicited_tick_header(self):
        with self.three() as (s,first,other,outside):
            self.prime(s,first,other,outside)
            for peer in (first,other,first):
                self.send(s,peer,self.help_request,fragmented=True);self.panel_header(s,peer)
                self.silent(s,first,other,outside)
                self.send(s,peer,b'\xb8\0\x30\0');self.silent(s,first,other,outside)
            self.send(s,outside,self.help_request);self.silent(s,first,other,outside)
            self.assertEqual(s.log().count('OWNED_GUILD_READONLY_PANEL_OPEN '),3)
            self.assertIn('OWNED_GUILD_READONLY_PANEL_DENIED ',s.log())
    def test_coalesced_help_retains_all_four_chat_channels(self):
        with self.three() as (s,first,other,outside):
            self.prime(s,first,other,outside)
            self.send(s,first,self.help_request+self.chat(b'panel-common',selector=0))
            self.panel_header(s,first)
            for peer,page in ((first,950),(other,936),(outside,950)):
                self.ordinary_message(s,peer,4,b'slowgirl',page,'panel-common',0)
            self.accepted(s,first,other);self.silent(s,outside)
            self.send(s,other,self.chat(b'panel-party',selector=1)+self.help_request)
            self.panel_header(s,other)
            for peer,page in ((first,950),(other,936)):
                self.ordinary_message(s,peer,5,b'fixedgirl',page,'panel-party',1)
            self.send(s,first,self.help_request+self.whisper('fixedgirl','panel-private'))
            self.panel_header(s,first)
            for peer,page in ((first,950),(other,936)):
                self.message(s,peer,4,'slowgirl','fixedgirl',page,'panel-private')
            self.send(s,other,self.guild('panel-guild',936)+self.help_request+b'\xb8\0')
            self.panel_header(s,other)
            for peer,page in ((first,950),(other,936)):
                self.display(s,peer,5,'fixedgirl','panel-guild',page)
            self.silent(s,first,other,outside)
    def test_incomplete_saved_member_blocks_header_without_blocking_chat(self):
        with self.three() as (s,first,other,outside):
            self.prime(s,first,other,outside)
            with closing(sqlite3.connect(s.database)) as db:
                saved=db.execute('select * from character_role_snapshots where character_id=5').fetchone()
                db.execute('delete from character_role_snapshots where character_id=5');db.commit()
            try:
                self.send(s,first,self.help_request+self.guild('no-fake-header'))
                # The preserved party_member/private_peer gate rejects a peer
                # whose saved role is absent. Qualified sender still gets chat;
                # the corrupted recipient does not gain readiness from help.
                self.display(s,first,4,'slowgirl','no-fake-header',950)
                self.silent(s,first,other,outside)
                self.assertIn('OWNED_GUILD_READONLY_PANEL_DENIED ',s.log())
            finally:
                with closing(sqlite3.connect(s.database)) as db:
                    db.execute('insert into character_role_snapshots values(?,?,?,?)',saved);db.commit()
def load_tests(loader,tests,pattern):
    return unittest.TestSuite(GuildPanelTests(name) for name in GuildPanelTests.__dict__ if name.startswith('test_'))
if __name__=='__main__':unittest.main()
