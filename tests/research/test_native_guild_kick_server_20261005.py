"""CUSTOM0080 real Application TCP on a private clone, NOT live client UI."""
from contextlib import closing, contextmanager, ExitStack
import os
from pathlib import Path
import sqlite3
import struct
import unittest
import test_native_guild_formal_server_20261004 as formal

formal.BINARY = Path(os.environ['GOD2_GUILD_KICK_TEST_BINARY']) if os.environ.get('GOD2_GUILD_KICK_TEST_BINARY') else None


class GuildKickTests(formal.NativeGuildFormalTests):
    @contextmanager
    def members(self, page=950):
        with self.server() as server, ExitStack() as lifetime:
            founder = self.enter_peer(server, lifetime, 4, b'codexslow', page)
            member = self.enter_peer(server, lifetime, 5, b'codexfixed', 936 if page == 950 else 950)
            self.drain(server, founder)
            prompt = self.select(server, founder, self.menu(server, founder), 0)
            self.send(server, founder, self.membership(prompt, 'FormalCave'))
            self.drain(server, founder); self.drain(server, member)
            prompt = self.select(server, member, self.menu(server, member), 1)
            self.send(server, member, self.membership(prompt, 'FormalCave'))
            self.drain(server, member); self.drain(server, founder)
            with closing(sqlite3.connect(server.database)) as db:
                application = db.execute('SELECT * FROM owned_guild_applications_0078').fetchone()
                self.assertIsNotNone(application)
            self.open_panel(server, founder)
            self.send(server, founder, b'\x71\1')
            self.drain(server, founder); self.drain(server, member)
            yield server, founder, member, application

    def kick_panel(self, server, founder):
        self.send(server, founder, self.HELP)
        frames = self.drain(server, founder)
        self.assertEqual([(row[1], row[2]) for row in self.rows(frames)], [(0, 3), (1, 1)])
        return frames

    @staticmethod
    def guild_chat(text):
        return b'\x2f' + struct.pack('<HBBH', len(text)+8, 3, 0xa5, 0) + text + b'\0'

    def preserved(self, before, after):
        self.assertEqual(set(before), set(after))
        for table in before:
            if table not in ('owned_guilds', 'owned_guild_members'):
                self.assertEqual(before[table], after[table], table)

    def test_current_member_kick_clear_chat_and_replay_both_locales(self):
        for page in (950, 936):
            with self.subTest(page=page), self.members(page) as (server, founder, member, unused):
                self.send(server, member, self.HELP); self.drain(server, member)
                self.kick_panel(server, founder)
                before = self.saved(server)
                self.send(server, founder, self.guild_chat(b'before-kick') + b'\x72\1' + self.guild_chat(b'after-kick'), fragmented=True)
                own, target = self.drain(server, founder), self.drain(server, member)
                self.assertEqual([frame[13:-1] for frame in own if frame and frame[0] == 0x5c],
                    [b'slowgirl: before-kick', b'slowgirl: after-kick'])
                self.assertEqual([frame[13:-1] for frame in target if frame and frame[0] == 0x5c], [b'slowgirl: before-kick'])
                self.assertIn(b'\x2d' + bytes(16), target)
                self.assertIn(b'\x92\1\x92\0', target)
                self.assertEqual([(row[1], row[2]) for row in self.rows(own)], [(0, 3)])
                after = self.saved(server); self.preserved(before, after)
                with closing(sqlite3.connect(server.database)) as db:
                    self.assertEqual(db.execute('SELECT character_id FROM owned_guild_members').fetchall(), [(4,)])
                # Frozen guild/common channels remain separate batches: a
                # mixed-channel batch is deliberately denied by the old route.
                self.send(server, member, self.guild_chat(b'blocked-removed-member'))
                for frames in (self.drain(server, member), self.drain(server, founder)):
                    self.assertFalse(any(b'blocked-removed-member' in frame for frame in frames))
                self.send(server, member, self.chat(b'common-still-works'))
                target_after = self.drain(server, member); peer_frames = self.drain(server, founder)
                for frames in (target_after, peer_frames):
                    self.assertFalse(any(b'blocked-removed-member' in frame for frame in frames))
                    self.assertTrue(any(b'common-still-works' in frame for frame in frames),
                        {'frames': [frame.hex() for frame in frames], 'log_tail': server.log()[-7000:]})
                for raw in (b'\x72\1', b'\x30\0\xb8\0\x72\1', self.HELP+b'\x72\1'):
                    self.send(server, founder, raw); self.drain(server, founder); self.drain(server, member)
                    self.assertEqual(after, self.saved(server))

    def test_help_and_denied_kick_cannot_lend_authority_to_pending_suffix(self):
        for suffix in (b'\x71\1', b'\x72\1'):
            with self.subTest(suffix=suffix.hex()), self.members() as (server, founder, member, application):
                self.kick_panel(server, founder)
                # TEST_ONLY stale cached role1 now refers to a reapplication
                # role0. No production rows/source save are changed.
                with closing(sqlite3.connect(server.database)) as db:
                    db.execute('DELETE FROM owned_guild_members WHERE character_id=5')
                    db.execute('UPDATE owned_guilds SET revision=revision+1')
                    db.execute('INSERT INTO owned_guild_applications_0078 VALUES (' + ','.join('?' for _ in application) + ')', application)
                    db.commit()
                before = self.saved(server)
                self.send(server, founder, self.HELP + b'\x72\1' + suffix)
                self.drain(server, founder); self.drain(server, member)
                self.assertEqual(before, self.saved(server), 'Denied kick boundary must revoke prefix-created founder authority')
                self.send(server, founder, suffix); self.drain(server, founder)
                self.assertEqual(before, self.saved(server), 'Coalesced help never leaves authority behind')
                self.open_panel(server, founder); self.send(server, founder, suffix)
                self.drain(server, founder); self.drain(server, member)
                with closing(sqlite3.connect(server.database)) as db:
                    self.assertEqual(db.execute('SELECT * FROM owned_guild_applications_0078').fetchall(), [])
                    self.assertEqual(db.execute('SELECT character_id FROM owned_guild_members ORDER BY character_id').fetchall(),
                        [(4,), (5,)] if suffix[0] == 0x71 else [(4,)])

    def test_nonfounder_self_stale_help_prefix_and_readonly_never_grant(self):
        with self.members() as (server, founder, member, unused):
            before = self.saved(server)
            self.send(server, member, self.HELP); self.drain(server, member)
            for raw in (b'\x72\0', b'\x72\1', self.HELP+b'\x72\1'):
                self.send(server, member, raw); self.drain(server, member); self.drain(server, founder)
                self.assertEqual(before, self.saved(server))
            for raw in (b'\x72\1', self.HELP+b'\x72\1', b'\x30\0\xb8\0\x72\1'):
                self.send(server, founder, raw); self.drain(server, founder); self.drain(server, member)
                self.assertEqual(before, self.saved(server))
            self.kick_panel(server, founder)
            with closing(sqlite3.connect(server.database)) as db:
                db.execute('UPDATE owned_guilds SET revision=revision+1'); db.commit()
            stale = self.saved(server)
            self.send(server, founder, b'\x30\0\xb8\0\x72\1')
            self.drain(server, founder); self.drain(server, member)
            self.assertEqual(stale, self.saved(server))

    def test_sql_failure_consumes_authority_and_rolls_back_protected_trigger(self):
        trigger = "CREATE TRIGGER kick_side_effect AFTER DELETE ON owned_guild_members WHEN old.character_id=5 BEGIN UPDATE character_trade_wallets SET amount=amount+1 WHERE character_id=4; END"
        with self.members() as (server, founder, member, unused):
            self.kick_panel(server, founder)
            with closing(sqlite3.connect(server.database)) as db:
                db.execute(trigger); db.commit()
            before = self.saved(server)
            self.send(server, founder, b'\x72\1'); self.drain(server, founder); self.drain(server, member)
            self.assertEqual(before, self.saved(server))
            with closing(sqlite3.connect(server.database)) as db:
                db.execute('DROP TRIGGER kick_side_effect'); db.commit()
            self.send(server, founder, b'\x72\1'); self.drain(server, founder)
            self.assertEqual(before, self.saved(server))
            self.kick_panel(server, founder); self.send(server, founder, b'\x72\1')
            self.drain(server, founder); self.drain(server, member)
            self.preserved(before, self.saved(server))

    def test_malformed_slot_rejected_before_prefix_chat(self):
        with self.members() as (server, founder, member, unused):
            self.kick_panel(server, founder); before = self.saved(server)
            self.send(server, founder, self.guild_chat(b'no-leak')+b'\x72\x32')
            self.assertEqual(founder.recv(1), b'')
            self.assertEqual(self.drain(server, member), [])
            self.assertEqual(before, self.saved(server))


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(GuildKickTests(name) for name in GuildKickTests.__dict__ if name.startswith('test_'))


if __name__ == '__main__':
    unittest.main()
