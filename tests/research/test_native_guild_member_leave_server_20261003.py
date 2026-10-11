"""CUSTOM0078 actual Application TCP member-leave: NOT_LIVE_CLIENT_UI.

NEW disposable candidate only. Frozen leadership helper imported read-only;
no port is used on import; caller supplies build-matched NEW candidate binary.
"""
from contextlib import closing, contextmanager
import os, sqlite3, struct, unittest
from pathlib import Path
import test_native_guild_leadership_server_20261003 as accepted

accepted.BINARY=Path(os.environ.get('GOD2_GUILD_MEMBER_LEAVE_TEST_BINARY',
    accepted.ROOT/'build-native-guild-member-leave-20261003/Release/god2-server.exe'))

class GuildMemberLeaveTests(accepted.GuildLeadershipTests):
    @contextmanager
    def members(self,page=950):
        with self.ready(page) as (s,leader,member):
            self.open_panel(s,leader);self.send(s,leader,b'\x71\1')
            self.drain(s,leader);self.drain(s,member)
            with closing(sqlite3.connect(s.database)) as db:
                self.assertEqual(db.execute('select character_id from owned_guild_members order by character_id').fetchall(),[(4,),(5,)])
            yield s,leader,member

    def member_panel(self,s,member):
        self.send(s,member,b'\x37\x7b\x08\0\0');frames=self.drain(s,member)
        self.assertEqual([(r[1],r[2]) for r in self.rows(frames)],[(0,1),(1,3)])
        self.assertTrue(any(f[-53:-52]==b'\x8e' for f in frames));return frames

    @staticmethod
    def chat(text,mode=3):
        return b'\x2f'+struct.pack('<HBBH',len(text)+8,mode,0xa5,0)+text+b'\0'

    def preserved_leave(self,before,after):
        self.assertEqual(set(before),set(after))
        for name,rows in before.items():
            if name not in ('owned_guilds','owned_guild_members'):self.assertEqual(after[name],rows,name)

    def test_qualified_member_leave_both_locales_cache_clear_chat_and_replay(self):
        for page in (950,936):
            with self.subTest(page=page),self.members(page) as (s,leader,member):
                self.member_panel(s,member);before=self.saved(s)
                with closing(sqlite3.connect(s.database)) as db:
                    oldguild=db.execute('select * from owned_guilds').fetchone()
                    founder=db.execute('select * from owned_guild_members where character_id=4').fetchone()
                self.send(s,member,self.chat(b'before-leave')+b'\x73\0'+self.chat(b'after-leave'),fragmented=True)
                own=self.drain(s,member);peer=self.drain(s,leader)
                for frames in (own,peer):
                    self.assertEqual([f[13:-1] for f in frames if f and f[0]==0x5c],[b'fixedgirl: before-leave'])
                    self.assertEqual(frames[0][0],0x5c,'Guild-chat prefix must precede mutation projection')
                self.assertIn(b'\x92\1\x92\0',own,'Remove non-self, then native self cache; no borrowed76 cache')
                self.assertIn(b'\x2d'+bytes(16),own,'Guild name must be cleared')
                self.assertEqual([(r[1],r[2]) for r in self.rows(peer)],[(0,3)])
                after=self.saved(s);self.preserved_leave(before,after)
                with closing(sqlite3.connect(s.database)) as db:
                    newguild=db.execute('select * from owned_guilds').fetchone()
                    self.assertGreater(newguild[2],oldguild[2]);self.assertEqual(newguild[:2]+newguild[3:],oldguild[:2]+oldguild[3:])
                    self.assertEqual(db.execute('select * from owned_guild_members').fetchall(),[founder])
                for raw in (b'\x73\0',b'\x30\0\xb8\0\x73\0',b'\x37\x7b\x08\0\0\x73\0'):
                    self.send(s,member,raw);self.drain(s,member);self.drain(s,leader);self.assertEqual(self.saved(s),after)
                self.send(s,leader,b'\x73\0');self.drain(s,leader);self.assertEqual(self.saved(s),after)
                self.assertIn('slot=0 committed=true player_created=true',s.log())

    def test_no_published_permission_foreignslot_creator_and_synthetic_open_prefix(self):
        with self.members() as (s,leader,member):
            before=self.saved(s)
            for peer,raw in ((member,b'\x73\0'),(member,b'\x37\x7b\x08\0\0\x73\0'),
                             (leader,b'\x73\0')):
                self.send(s,peer,raw);self.drain(s,peer);self.drain(s,leader if peer is member else member)
                self.assertEqual(self.saved(s),before)
            self.member_panel(s,member)
            for slot in (1,49):
                self.send(s,member,bytes([0x73,slot]));self.drain(s,member);self.assertEqual(self.saved(s),before)
            self.send(s,member,b'\x73\0');self.drain(s,member);self.drain(s,leader)
            with closing(sqlite3.connect(s.database)) as db:self.assertEqual(db.execute('select character_id from owned_guild_members').fetchall(),[(4,)])

    def test_stale_whole_batch_tick_b8_help_marker_and_owner_cannot_authorize(self):
        with self.members() as (s,leader,member):
            for prefix in (b'\x30\0',b'\xb8\0',b'\x37\x7b\x08\0\0',b'\x30\0\xb8\0\x37\x7b\x08\0\0'):
                self.member_panel(s,member)
                with closing(sqlite3.connect(s.database)) as db:db.execute('update owned_guilds set revision=revision+1');db.commit()
                before=self.saved(s);self.send(s,member,prefix+b'\x73\0');self.drain(s,member);self.drain(s,leader)
                self.assertEqual(self.saved(s),before)
            self.member_panel(s,member);before=self.saved(s)
            marker=b'\x6f\1\0\xff\xff'+b'Unused'+bytes(10)+b'\0\xa5'
            self.send(s,member,b'\x30\0'+marker+b'\x37\x7b\x08\0\0\x73\0');self.drain(s,member);self.drain(s,leader)
            self.assertEqual(self.saved(s),before,'6F whole-batch invalidation precedes prefix help')
            self.member_panel(s,member)
            with closing(sqlite3.connect(s.database)) as db:
                self.assertIsNotNone(db.execute('select id from accounts where id=3').fetchone())
                self.assertIsNone(db.execute('select id from recovered_characters where account_id=3 and slot=1').fetchone())
                db.execute('update recovered_characters set account_id=3,slot=1 where id=5');db.commit()
            foreign=self.saved(s);self.send(s,member,b'\x30\0\x73\0')
            self.assertEqual(member.recv(1),b'','Qualified SQL owner mismatch closes the stale connection')
            self.drain(s,leader)
            self.assertEqual(self.saved(s),foreign,'Foreign SQL character owner cannot reuse prior published lease')

    def test_sql_failure_and_protected_trigger_write_rollback_consume_permission(self):
        for trigger in (
            "CREATE TRIGGER leave_fail BEFORE DELETE ON owned_guild_members WHEN old.character_id=5 BEGIN SELECT RAISE(ABORT,'TEST_ONLY leave failure'); END",
            "CREATE TRIGGER leave_fail AFTER DELETE ON owned_guild_members WHEN old.character_id=5 BEGIN UPDATE character_trade_wallets SET amount=amount+1 WHERE character_id=4; END"):
            with self.subTest(trigger=trigger),self.members() as (s,leader,member):
                self.member_panel(s,member)
                with closing(sqlite3.connect(s.database)) as db:db.execute(trigger);db.commit()
                before=self.saved(s);self.send(s,member,b'\x73\0');self.drain(s,member);self.drain(s,leader)
                self.assertEqual(self.saved(s),before,'Transaction rollback includes revision/delete/trigger write')
                with closing(sqlite3.connect(s.database)) as db:db.execute('drop trigger leave_fail');db.commit()
                self.send(s,member,b'\x73\0');self.drain(s,member);self.assertEqual(self.saved(s),before,'Failed SQL consumes authority')
                self.member_panel(s,member);self.send(s,member,b'\x73\0');self.drain(s,member);self.drain(s,leader)
                self.preserved_leave(before,self.saved(s))
                with closing(sqlite3.connect(s.database)) as db:self.assertEqual(db.execute('select character_id from owned_guild_members').fetchall(),[(4,)])

    def test_malformed73_batch_rejects_before_prefix_chat_or_sql(self):
        with self.members() as (s,leader,member):
            self.member_panel(s,member);before=self.saved(s)
            self.send(s,member,self.chat(b'no-leak')+b'\x73\x32');self.assertEqual(member.recv(1),b'')
            self.assertEqual(self.drain(s,leader),[]);self.assertEqual(self.saved(s),before)

def load_tests(loader,tests,pattern):
    return unittest.TestSuite(GuildMemberLeaveTests(name) for name in GuildMemberLeaveTests.__dict__ if name.startswith('test_'))
if __name__=='__main__':unittest.main()
