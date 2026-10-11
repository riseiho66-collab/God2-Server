"""CUSTOM0081 real Application TCP, disposable schema50 own-server clone.

NOT_LIVE_CLIENT_UI: synthetic peers only, no client/desktop/formal writes.
Explicit candidate env, exclusive loopback2599, all old LAB flags absent.
Old kick/formal fixture sources are imported read-only, never rewritten.
"""
from contextlib import closing, contextmanager, ExitStack
import ast
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import struct
import unittest
import test_native_guild_formal_server_20261004 as formal
from test_current_movement import movement_wire

formal.BINARY = Path(os.environ['GOD2_GUILD_DISBAND_TEST_BINARY']) if os.environ.get('GOD2_GUILD_DISBAND_TEST_BINARY') else None


class GuildDisbandTests(formal.NativeGuildFormalTests):
    def guild_records(self, frames):
        # Announcement-enabled schema50 appends native98 to the same91/8E
        # logical frame. Extend ONLY this new fixture parser, not frozen tests.
        result = []
        for frame in frames:
            if not frame or frame[0] not in (0x91,0x92,0x8e,0x98): continue
            offset = 0
            while offset < len(frame):
                opcode = frame[offset]
                size = {0x91:22,0x92:2,0x8e:53}.get(opcode)
                if opcode == 0x98:
                    self.assertLessEqual(offset+3, len(frame))
                    size = int.from_bytes(frame[offset+1:offset+3], 'little')
                    self.assertGreaterEqual(size,4)
                self.assertIsNotNone(size, frame.hex()); self.assertLessEqual(offset+size, len(frame))
                record = frame[offset:offset+size]
                result.append(record)
                offset += size
        return result

    def rows(self, frames):
        return [record for record in self.guild_records(frames) if record[0] == 0x91]

    def open_panel(self, server, founder):
        self.send(server, founder, self.HELP); frames = self.drain(server, founder)
        self.assertEqual([(row[1],row[2]) for row in self.rows(frames)], [(0,3),(1,0)])
        header = next(record for record in self.guild_records(frames) if record[0] == 0x8e)
        self.assertEqual((header[14],header[20],header[24]), (6,1,20))

    @contextmanager
    def server(self, **options):
        # Preserve frozen fixture's initial default49 verification, then enable
        # formal announcement configuration and migrate ONLY this disposable DB.
        with super().server(**options) as server:
            server.config['world']['owned_guild_announcements'] = {'enabled': True}
            server.restart()
            self.assertEqual(server.endpoint, ('127.0.0.1', 2599))
            self.assertTrue(all(key not in server.environment for key in formal.LAB_FLAGS))
            with closing(sqlite3.connect(server.database)) as db:
                self.assertEqual(db.execute('SELECT MAX(version) FROM schema_migrations').fetchone(), (50,))
                self.assertEqual(db.execute('SELECT COUNT(*) FROM schema_migrations WHERE version=50').fetchone(), (1,))
                # Additional named identity fixtures, cloned ONLY in this private
                # save. Pending6 enters through actual TCP/native application.
                for identity, account, name in ((6, 'codexpending', b'PendingTCP'), (7, 'codexforeign', b'ForeignTCP')):
                    old_account = db.execute('SELECT account_id FROM recovered_characters WHERE id=5').fetchone()[0]
                    old = list(db.execute('SELECT * FROM accounts WHERE id=?', (old_account,)).fetchone())
                    # Existing recovered login uses byte-key account identities,
                    # not plain display names. Preserve that frozen contract.
                    old[0], old[1] = identity, 'god2-bytes:'+account.encode('ascii').hex()
                    db.execute('INSERT INTO accounts VALUES (' + ','.join('?' for _ in old) + ')', old)
                    character = list(db.execute('SELECT * FROM recovered_characters WHERE id=5').fetchone())
                    character[0:3] = identity, identity, 0
                    profile = bytearray(character[3]); profile[:16] = name + bytes(16-len(name))
                    character[3], character[4], character[6] = bytes(profile), name, 950
                    db.execute('INSERT INTO recovered_characters VALUES (' + ','.join('?' for _ in character) + ')', character)
                    for table in ('character_role_snapshots', 'character_resources'):
                        row = list(db.execute('SELECT * FROM '+table+' WHERE character_id=5').fetchone()); row[0] = identity
                        db.execute('INSERT INTO '+table+' VALUES (' + ','.join('?' for _ in row) + ')', row)
                    db.execute("INSERT INTO character_trade_wallets VALUES (?,100000,1,'CUSTOM-0063')", (identity,))
                    db.execute('INSERT INTO recovered_positions VALUES (?,4,3,132,126,1)', (identity,))
                db.execute("CREATE TABLE tcp_protected(v,blob BLOB,text TEXT)")
                db.execute("INSERT INTO tcp_protected VALUES(NULL,X'00017F','unchanged')")
                db.execute("INSERT INTO tcp_protected VALUES(1.25,X'','')")
                db.commit()
            self._case_serial = getattr(self, '_case_serial', 0)+1
            try:
                yield server
            finally:
                output = formal.ROOT/'artifacts/research/native-guild-management-0081/tcp-tests-v01'
                output.mkdir(parents=True, exist_ok=True)
                name = self._testMethodName+'-'+str(self._case_serial)+'-'+str(__import__('time').time_ns())
                (output/(name+'.server.log')).write_text(server.log(), encoding='utf-8')
                (output/(name+'.config.json')).write_text(json.dumps(server.config,ensure_ascii=False,indent=2), encoding='utf-8')

    @staticmethod
    def guild_chat(text):
        return b'\x2f' + struct.pack('<HBBH', len(text)+8, 3, 0xa5, 0) + text + b'\0'

    @staticmethod
    def announcement(text):
        return b'\x79' + struct.pack('<H', len(text)+4) + text + b'\0'

    def founder_panel(self, server, founder, pending=True):
        self.send(server, founder, self.HELP)
        frames = self.drain(server, founder)
        expected = [(0, 3), (1, 1)] + ([(2, 0)] if pending else [])
        self.assertEqual([(row[1], row[2]) for row in self.rows(frames)], expected)
        return frames

    @contextmanager
    def members(self, page=950, pending=True):
        with self.server() as server, ExitStack() as lifetime:
            founder = self.enter_peer(server, lifetime, 4, b'codexslow', page)
            member = self.enter_peer(server, lifetime, 5, b'codexfixed', 936 if page == 950 else 950)
            self.drain(server, founder)
            prompt = self.select(server, founder, self.menu(server, founder), 0)
            self.send(server, founder, self.membership(prompt, 'DisbandCave'))
            self.drain(server, founder); self.drain(server, member)
            prompt = self.select(server, member, self.menu(server, member), 1)
            self.send(server, member, self.membership(prompt, 'DisbandCave'))
            self.drain(server, member); self.drain(server, founder)
            self.open_panel(server, founder); self.send(server, founder, b'\x71\1')
            self.drain(server, founder); self.drain(server, member)
            pending_peer = None
            if pending:
                pending_peer = self.enter_peer(server, lifetime, 6, b'codexpending', page)
                self.drain(server, founder); self.drain(server, member)
                prompt = self.select(server, pending_peer, self.menu(server, pending_peer), 1)
                self.send(server, pending_peer, self.membership(prompt, 'DisbandCave'))
                self.drain_all(server, founder, member, pending_peer)
            # Keep independent unrelated guild/announcement rows as TEST_ONLY
            # controls. Not a native gameplay create claim or production grant.
            with closing(sqlite3.connect(server.database)) as db:
                row = list(db.execute('SELECT * FROM owned_guilds').fetchone()); guild_id = row[0]
                foreign = list(row); foreign[0:3] = guild_id+1, 'ProtectedCave', row[2]+1
                db.execute('INSERT INTO owned_guilds VALUES ('+','.join('?' for _ in foreign)+')', foreign)
                member_row = list(db.execute('SELECT * FROM owned_guild_members WHERE character_id=4').fetchone())
                member_row[0:3] = 7, guild_id+1, foreign[2]
                db.execute('INSERT INTO owned_guild_members VALUES ('+','.join('?' for _ in member_row)+')', member_row)
                governance = list(db.execute('SELECT * FROM owned_guild_governance_0078').fetchone())
                governance[0:4] = guild_id+1, 7, 7, foreign[2]
                db.execute('INSERT INTO owned_guild_governance_0078 VALUES ('+','.join('?' for _ in governance)+')', governance)
                db.execute("INSERT INTO owned_guild_announcements_0078 VALUES (?, 'protected foreign history', 1, 'CUSTOM_DESIGNED','CUSTOM-0078',?)",
                    (guild_id+1, formal.fixture.SOURCE_SHA))
                db.commit()
            self.founder_panel(server, founder, pending)
            self.send(server, founder, self.announcement(b'retained target announcement'))
            self.drain_all(server, founder, member, pending_peer)
            with closing(sqlite3.connect(server.database)) as db:
                self.assertEqual(db.execute('SELECT text_utf8 FROM owned_guild_announcements_0078 WHERE guild_id=?', (guild_id,)).fetchone(),
                    ('retained target announcement',))
            # A structurally valid but nonself75 is denied and consumes any
            # residual mutation permission without fabricating a quest-close.
            before_denial = self.saved(server)
            self.send(server, founder, b'\x75\1'); self.drain_all(server, founder, member, pending_peer)
            self.assertEqual(before_denial, self.saved(server))
            yield server, founder, member, pending_peer, guild_id

    def drain_all(self, server, *peers):
        return [self.drain(server, peer) for peer in peers if peer is not None]

    def unchanged(self, server, founder, peers, raw):
        before = self.saved(server)
        self.send(server, founder, raw); frames = self.drain_all(server, founder, *peers)
        self.assertEqual(before, self.saved(server), {'wire': raw.hex(), 'log_tail': server.log()[-8000:]})
        return frames

    def exact_retirement(self, before, after, target):
        self.assertEqual(set(before), set(after))
        allowed = {'owned_guilds', 'owned_guild_members', 'owned_guild_governance_0078', 'owned_guild_applications_0078'}
        for table in before:
            if table not in allowed:
                self.assertEqual(before[table], after[table], table)
        for table, column in (('owned_guild_members', 1), ('owned_guild_governance_0078', 0), ('owned_guild_applications_0078', 1)):
            expected = [raw for raw in before[table] if ast.literal_eval(raw)[column] != target]
            self.assertEqual(after[table], expected, table)
        old = [ast.literal_eval(raw) for raw in before['owned_guilds']]
        new = [ast.literal_eval(raw) for raw in after['owned_guilds']]
        self.assertEqual(len(old), len(new))
        for previous in old:
            current = next(row for row in new if row[0] == previous[0])
            if previous[0] != target:
                self.assertEqual(current, previous)
            else:
                self.assertEqual(current[:2]+current[3:], previous[:2]+previous[3:])
                self.assertEqual(current[2], max(row[2] for row in old)+1)

    def test_success_clear_all_audiences_replay_and_common_chat_both_locales(self):
        for page in (950, 936):
            with self.subTest(page=page), self.members(page) as (server, founder, member, pending, target):
                self.send(server, member, self.HELP); self.drain_all(server, member, founder, pending)
                self.founder_panel(server, founder)
                before = self.saved(server)
                self.send(server, founder, self.guild_chat(b'before-disband')+b'\x75\0', fragmented=True)
                own, other, waiting = self.drain_all(server, founder, member, pending)
                for frames in (own, other):
                    self.assertTrue(any(b'before-disband' in frame for frame in frames))
                    self.assertIn(b'\x2d'+bytes(16), frames)
                    self.assertIn(b'\x92\1\x92\2\x92\0', frames)
                self.assertFalse(any(frame == b'\x2d'+bytes(16) for frame in waiting), 'Pending applicant was never a member')
                after = self.saved(server); self.exact_retirement(before, after, target)
                self.assertIn('committed=true CUSTOM-0081', server.log())
                for actor in (founder, member):
                    self.send(server, actor, self.guild_chat(b'blocked-retired-guild'))
                    self.assertFalse(any(b'blocked-retired-guild' in f for frames in self.drain_all(server, founder, member, pending) for f in frames))
                # Remove pending world's peer to assert exactly TWO normal chat
                # recipients; this does not erase saved character/app data.
                pending.close(); self.drain_all(server, founder, member)
                self.send(server, member, self.chat(b'common-after-disband'))
                for frames in self.drain_all(server, member, founder):
                    self.assertTrue(any(b'common-after-disband' in frame for frame in frames), server.log()[-8000:])
                self.assertRegex(server.log(), r'NATIVE_CHAT[^\n]*recipients=2')
                for raw in (b'\x75\0', self.HELP+b'\x75\0', b'\x30\0\xb8\0\x75\0'):
                    self.unchanged(server, founder, (member,), raw)
                self.assertEqual(after, self.saved(server))

    def test_nonfounder_nonself_noauthority_stale_and_move_deny(self):
        with self.members() as (server, founder, member, pending, target):
            self.send(server, member, self.HELP); self.drain_all(server, member, founder, pending)
            for raw in (b'\x75\0', b'\x75\1', self.HELP+b'\x75\0'):
                self.unchanged(server, member, (founder,pending), raw)
            for raw in (b'\x75\0', self.HELP+b'\x75\0', b'\x30\0\xb8\0\x75\0'):
                self.unchanged(server, founder, (member,pending), raw)
            self.founder_panel(server, founder)
            self.unchanged(server, founder, (member,pending), b'\x75\1')
            self.unchanged(server, founder, (member,pending), b'\x75\0')
            self.founder_panel(server, founder)
            with closing(sqlite3.connect(server.database)) as db:
                db.execute('UPDATE owned_guilds SET revision=revision+1 WHERE id=?', (target,)); db.commit()
            self.unchanged(server, founder, (member,pending), b'\x30\0\xb8\0\x75\0')
            self.founder_panel(server, founder)
            # Native builder's true movement record, no synthetic state setter.
            founder.sendall(movement_wire(127,126,1)); self.drain_all(server, founder, member, pending)
            self.unchanged(server, founder, (member,pending), b'\x75\0')

    def test_help_denied_disband_cannot_lend_pending_or_announcement_authority(self):
        for suffix in (b'\x71\2', b'\x72\2', self.announcement(b'no-borrowed-save')):
            with self.subTest(suffix=suffix.hex()), self.members() as (server, founder, member, pending, target):
                # No75 publication before the batch. Help may publish readonly
                # native content, but every75 boundary must revoke before suffix.
                before = self.saved(server)
                self.unchanged(server, founder, (member,pending), self.HELP+b'\x75\0'+suffix)
                self.unchanged(server, founder, (member,pending), suffix)
                self.assertEqual(before, self.saved(server))
                # Fresh standalone open still enables the old frozen action.
                self.founder_panel(server, founder)
                self.send(server, founder, suffix); self.drain_all(server, founder, member, pending)
                with closing(sqlite3.connect(server.database)) as db:
                    if suffix[0] in (0x71,0x72):
                        self.assertEqual(db.execute('SELECT * FROM owned_guild_applications_0078 WHERE guild_id=?', (target,)).fetchall(), [])
                    else:
                        self.assertEqual(db.execute('SELECT text_utf8 FROM owned_guild_announcements_0078 WHERE guild_id=?', (target,)).fetchone(), ('no-borrowed-save',))

    def test_every_member_and_pending_persisted_battle_blocks_atomic_retirement(self):
        for identity in (4,5,6):
            with self.subTest(identity=identity), self.members() as (server, founder, member, pending, target):
                self.founder_panel(server, founder)
                # TEST_ONLY unsettled persistent reservation, not a claim of
                # actual Session InBattle animation or client battle entry.
                with closing(sqlite3.connect(server.database)) as db:
                    revision = db.execute('SELECT revision FROM character_resources WHERE character_id=?', (identity,)).fetchone()[0]
                    db.execute("INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES (?,?,'CUSTOM-0012')", (identity,revision)); db.commit()
                self.unchanged(server, founder, (member,pending), b'\x75\0')

    def test_online_projection_preflight_missing_resources_and_invalid_stored_codepage(self):
        for fault in ('missing_resources','invalid_codepage'):
            with self.subTest(fault=fault), self.members() as (server, founder, member, pending, target):
                self.send(server, member, self.HELP); self.drain_all(server, member, founder, pending)
                with closing(sqlite3.connect(server.database)) as db:
                    if fault == 'missing_resources': db.execute('DELETE FROM character_resources WHERE character_id=5')
                    else: db.execute('UPDATE recovered_characters SET name_codepage=0 WHERE id=5')
                    db.commit()
                # Fresh panel AFTER fault removes stale-snapshot ambiguity.
                self.founder_panel(server, founder)
                before = self.saved(server)
                self.send(server, founder, b'\x75\0'); own, other, waiting = self.drain_all(server, founder, member, pending)
                self.assertEqual(before, self.saved(server), {'fault':fault,'frames':[x.hex() for x in other], 'log_tail':server.log()[-10000:]})
                self.assertNotIn(b'\x2d'+bytes(16), other)
                # SQL failure did not close the member's authenticated session.
                self.send(server, member, b'\x30\0'); self.drain(server, member)
                self.unchanged(server, founder, (member,pending), b'\x75\0')

    def test_protected_trigger_rolls_back_and_consumes_authority(self):
        with self.members() as (server, founder, member, pending, target):
            self.founder_panel(server, founder)
            with closing(sqlite3.connect(server.database)) as db:
                db.execute("CREATE TRIGGER disband_side_effect AFTER DELETE ON owned_guild_members WHEN OLD.character_id=5 BEGIN UPDATE character_trade_wallets SET amount=amount+1 WHERE character_id=4; END")
                db.commit()
            self.unchanged(server, founder, (member,pending), b'\x75\0')
            with closing(sqlite3.connect(server.database)) as db:
                db.execute('DROP TRIGGER disband_side_effect'); db.commit()
            before = self.saved(server)
            self.unchanged(server, founder, (member,pending), b'\x75\0')
            self.founder_panel(server, founder); self.send(server, founder, b'\x75\0')
            self.drain_all(server, founder, member, pending); self.exact_retirement(before, self.saved(server), target)

    def test_malformed_later_record_rejects_before_prefix_chat_or_guild_write(self):
        for suffix in (b'\x75', b'\x75\x32', b'\x75\0\x71\x32'):
            with self.subTest(suffix=suffix.hex()), self.members() as (server, founder, member, pending, target):
                self.founder_panel(server, founder); before = self.saved(server)
                self.send(server, founder, self.chat(b'no-malformed-leak')+suffix)
                self.assertEqual(founder.recv(1), b'')
                for frames in self.drain_all(server, member, pending):
                    self.assertFalse(any(b'no-malformed-leak' in frame for frame in frames))
                self.assertEqual(before, self.saved(server))


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(GuildDisbandTests(name) for name in GuildDisbandTests.__dict__ if name.startswith('test_'))


if __name__ == '__main__':
    unittest.main()
