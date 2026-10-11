"""Actual loopback Application party routing; synthetic peers, not native UI.

Every process and save is an isolated clone managed by the role-text harness.
No formal server, player save or client is modified.
"""
from contextlib import contextmanager, ExitStack, closing
import json
import sqlite3
import struct
import unittest
import test_owned_role_text_server as fixture
from test_current_world_ready_builder import current_world_ready_wire
from test_current_movement import movement_wire
from tools.strike_lab.current_party_20261002 import Oracle, ACTOR, UI, BODY
from tools.strike_lab.current_protocol_coverage import qualified_image


class NativePartyServerTests(fixture.OwnedRoleTextServerTests):
    # Do not inherit the unrelated role-text test cases.
    __unittest_skip__ = False

    @contextmanager
    def peers(self, names=None, allow_movement=False):
        with self.server() as state, ExitStack() as lifetime:
            with closing(sqlite3.connect(state.database)) as db:
                # The old companion fixture omitted role5. Import its already
                # qualified synthetic role snapshot from the read-only peer
                # fixture into this disposable clone, preserving provenance.
                source = fixture.ROOT / 'artifacts/playtests/private-weapon-peer-20260927-04/town-diagnostic-accounts.db'
                with closing(sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True)) as origin:
                    snapshot = origin.execute('select * from character_role_snapshots where character_id=5').fetchone()
                    resources = origin.execute('select * from character_resources where character_id=5').fetchone()
                self.assertIsNotNone(snapshot)
                self.assertIsNotNone(resources)
                db.execute('insert or replace into character_role_snapshots values(?,?,?,?)', snapshot)
                db.execute('insert or replace into character_resources values(?,?,?,?,?,?,?)', resources)
                db.execute('update recovered_positions set area=4,scene=3,x=129,y=126 where character_id=5')
                for identity, (text, page) in (names or {}).items():
                    name = text.encode('cp' + str(page))
                    profile = bytearray(db.execute('select profile from recovered_characters where id=?', (identity,)).fetchone()[0])
                    profile[:16] = name + bytes(16 - len(name))
                    db.execute('update recovered_characters set profile=?,name_bytes=?,name_codepage=? where id=?',
                               (profile, name, page, identity))
                db.commit()
            games = []
            for identity, account, page in ((4, b'codexslow', 950), (5, b'codexfixed', 936)):
                games.append(self.enter_peer(state, lifetime, identity, account, page))
            def saved():
                with closing(sqlite3.connect(state.database)) as db:
                    return {name: (sql, sorted(repr(row) for row in db.execute('select * from "' + name.replace('"', '""') + '"')))
                            for name, sql in db.execute("select name,sql from sqlite_master where type='table' order by name").fetchall()
                            if not (allow_movement and name == 'recovered_positions')}
            before = saved()
            yield state, games[0], games[1]
            self.assertEqual(saved(), before, 'Transient parties changed saved data/schema')

    def enter_peer(self, state, lifetime, identity, account, page):
        h = state.helper
        login = lifetime.enter_context(h.connect(state.endpoint)); h.handshake(login)
        login.sendall(h.frame(*fixture.dual.credential(4, account, b'labtest2345')))
        h.read_frame(login, 0x1d, 176); h.read_frame(login, 4, 8)
        address = h.read_frame(login, 5, 12)
        h.read_frame(login, 6, 8); h.read_frame(login, 0x0a, 20)
        try: self.assertEqual(h.list_characters(login)[3], 1)
        except AssertionError as error:self.fail(str(error)+'\nCharacter-list server diagnostic:\n'+state.log()[-4000:])
        game = lifetime.enter_context(h.connect(('127.0.0.1', int.from_bytes(address[9:11], 'little'))))
        h.handshake(game, game=True)
        game.sendall(h.frame(*fixture.dual.credential(0, account, b'labtest2345')))
        h.read_frame(game, 0x1f, 128)
        game.sendall(h.frame(0x1a, fixture.dual.selection_payload(0)))
        h.read_frame(game, 2, 26); entry = h.read_frame(game, 0x2a, 40)
        self.assertEqual(int.from_bytes(entry[3:5], 'little') & 0x3fff, identity)
        game.sendall(current_world_ready_wire(identity, (4, 3) if page == 950 else (4, 2)))
        h.silent(game); game.sendall(h.frame(0x30, b'\0'))
        try: self.drain(state, game, first=True)
        except (AssertionError, TimeoutError): self.fail('Initial projection failed for ' + str(identity) + '\n' + state.log()[-6000:])
        return game

    def send(self, state, peer, logical, fragmented=False):
        wire = state.helper.frame(logical[0], logical[1:])
        if fragmented:
            peer.sendall(wire[:-1]); state.helper.silent(peer); peer.sendall(wire[-1:])
        else: peer.sendall(wire)

    @staticmethod
    def join(source=4, target=5): return b'\x6a' + struct.pack('<II', source, target)

    @staticmethod
    def answer(target=4, response=1): return b'\x58' + struct.pack('<HBB', target, response, 0xa5)

    def preview(self, state, leader, identity, name):
        try: b = state.decoder.logical(state.helper, leader)
        except TimeoutError: self.fail('Party preview missing; server log:\n' + state.log()[-6000:])
        self.assertEqual(len(b), 29); self.assertEqual(b[0], 0x54)
        self.assertEqual(b[1:17].split(b'\0', 1)[0], name)
        self.assertEqual(struct.unpack_from('<H', b, 17)[0], identity)
        self.assertGreater(struct.unpack_from('<I', b, 25)[0], 0)

    def roster(self, state, recipient, leader, own, other, other_name, coordinates):
        b = state.decoder.logical(state.helper, recipient)
        self.assertEqual(len(b), 78)
        records=[]; offset=0
        while offset<len(b):
            size={0x55:25,0x56:7,0x58:21}[b[offset]]
            records.append(b[offset:offset+size]);offset+=size
        self.assertEqual(sorted(r[0] for r in records), [0x55,0x55,0x56,0x58])
        roster=[r for r in records if r[0]==0x55]
        self.assertEqual({struct.unpack_from('<H', r, 1)[0] for r in roster}, {own,other})
        for row in roster:
            identity = struct.unpack_from('<H', row, 1)[0]
            self.assertIn(identity, (own, other))
            self.assertEqual(row[4], int(identity == leader))
        position=next(r for r in records if r[0]==0x56)
        vitals=next(r for r in records if r[0]==0x58)
        self.assertEqual(position, b'\x56' + struct.pack('<HHH', other, *coordinates))
        with closing(sqlite3.connect(state.database)) as db:
            hp, maximum_hp, mp, maximum_mp = db.execute(
                'select hp,max_hp,mp,max_mp from character_resources where character_id=?', (other,)).fetchone()
        self.assertEqual(vitals[1:], struct.pack('<HHIIII', other, 0, hp, mp, maximum_hp, maximum_mp))
        self.assertIn(other_name + b'\0', b''.join(roster))

    def accepted(self, state, requester, leader):
        self.send(state, requester, self.join(), fragmented=True)
        self.preview(state, leader, 4, b'slowgirl')
        state.helper.silent(requester)
        self.send(state, leader, self.answer())
        self.roster(state, requester, 5, 4, 5, b'fixedgirl', (129, 126))
        self.roster(state, leader, 5, 5, 4, b'slowgirl', (126, 126))

    def removed(self, state, recipient, identity, name):
        self.assertEqual(state.decoder.logical(state.helper, recipient),
                         b'\x57' + struct.pack('<H', identity) + name + bytes(16 - len(name)))

    def test_native_party_decline_busy_and_owned_source_validation(self):
        with self.peers() as (s, first, other):
            for raw in (self.join(5, 5), self.join(4, 4), self.join(4, 0x10005),
                        self.join() + self.join(), self.join() + b'\x1d\0\0'):
                self.send(s, first, raw); s.helper.silent(first); s.helper.silent(other)
            for response in (0, 2):
                self.send(s, first, self.join()); self.preview(s, other, 4, b'slowgirl')
                self.send(s, first, self.answer()); s.helper.silent(first); s.helper.silent(other)
                self.send(s, other, self.answer(response=response))
                s.helper.silent(first); s.helper.silent(other)
                self.send(s, other, self.answer()); s.helper.silent(first); s.helper.silent(other)

    def test_native_party_accept_kick_leave_and_cancel_pending(self):
        with self.peers() as (s, first, other):
            self.accepted(s, first, other)
            self.send(s, first, b'\x57' + struct.pack('<I', 5))
            s.helper.silent(first); s.helper.silent(other)
            self.send(s, other, b'\x57' + struct.pack('<I', 4))
            for peer in (first, other): self.removed(s, peer, 4, b'slowgirl')
            self.accepted(s, first, other)
            # Original raw16 name is advisory; ownership derives from the lease.
            self.send(s, first, b'\x5a' + struct.pack('<H', 4) + b'forged-name' + bytes(5))
            for peer in (first, other): self.removed(s, peer, 4, b'slowgirl')
            self.send(s, first, self.join()); self.preview(s, other, 4, b'slowgirl')
            self.send(s, first, b'\x5a' + struct.pack('<H', 4) + bytes(16))
            s.helper.silent(first); s.helper.silent(other)
            self.send(s, other, self.answer()); s.helper.silent(first); s.helper.silent(other)

    def test_native_party_leader_disconnect_clears_and_reconnect_has_no_membership(self):
        with self.peers() as (s, first, other):
            self.accepted(s, first, other)
            other.close()
            b = s.decoder.logical(s.helper, first)
            self.assertEqual(len(b), 38)
            self.assertEqual(b, b'\x57' + struct.pack('<H', 5) + b'fixedgirl' + bytes(7) +
                             b'\x57' + struct.pack('<H', 4) + b'slowgirl' + bytes(8))
            self.send(s, first, self.join()); s.helper.silent(first)
            with ExitStack() as lifetime:
                returned = self.enter_peer(s, lifetime, 5, b'codexfixed', 936)
                self.send(s, returned, b'\x57' + struct.pack('<I', 4))
                s.helper.silent(returned); s.helper.silent(first)
                self.accepted(s, first, returned)

    def test_variant_names_preserve_native_self_recognition(self):
        names = {4: ('台', 950), 5: ('臺', 936)}
        with self.peers(names=names) as (s, first, other):
            self.send(s, first, self.join()); self.preview(s, other, 4, '台'.encode('cp936'))
            self.send(s, other, self.answer())
            oracles = []
            for recipient, identity, page, text in ((first, 4, 950, '台'), (other, 5, 936, '臺')):
                b = s.decoder.logical(s.helper, recipient)
                own = text.encode('cp' + str(page))
                # Conversion would collide if self were also OpenCC-normalized.
                # Correct raw-self and translated-other names are distinct.
                o = Oracle(qualified_image()); o.vm.mem_write(ACTOR + 0x27, own + b'\0')
                offset = 0
                while offset < len(b):
                    size = {0x55:25, 0x56:7, 0x58:21}[b[offset]]
                    row = b[offset:offset+size]
                    if row[0] == 0x55:
                        if struct.unpack_from('<H', row, 1)[0] == identity:
                            self.assertEqual(row[9:25].split(b'\0', 1)[0], own)
                        o.call(0x4e9bc0, BODY, body=row[1:])
                    offset += size
                self.assertEqual(o.u32(ACTOR + 0x3f98), 1, 'Self misclassified as other')
                self.assertEqual(o.read(UI + 0xafeea, 1), bytes([identity == 5]))
                oracles.append(o)
            self.send(s, other, b'\x5a' + struct.pack('<H', 5) + bytes(16))
            for recipient, o in zip((first, other), oracles):
                b = s.decoder.logical(s.helper, recipient)
                self.assertEqual(b[0], 0x57)
                for offset in range(0, len(b), 19):o.call(0x4e9eb0, BODY, 0, body=b[offset+1:offset+19])
                self.assertEqual(o.u32(ACTOR + 0x3f98), 0)
                self.assertEqual(o.read(UI + 0xafeea, 1), b'\0')

    def test_party_movement_projects_before_next_tick_and_common_chat_survives(self):
        with self.peers(allow_movement=True) as (s, first, other):
            # A native queue may combine the join and common-chat records.
            text=b'Party hello';chat=b'\x2f'+struct.pack('<H',len(text)+8)+bytes(4)+text+b'\0'
            self.send(s, first, self.join()+chat)
            self.preview(s, other, 4, b'slowgirl')
            for peer in (first, other):
                b=s.decoder.logical(s.helper,peer);self.assertEqual(b[0],0x5c)
                self.assertEqual(b[13:-1],b'slowgirl: Party hello')
            self.send(s, other, self.answer())
            self.roster(s, first, 5, 4, 5, b'fixedgirl', (129,126))
            self.roster(s, other, 5, 5, 4, b'slowgirl', (126,126))
            for owner, speaker, page in ((first,b'slowgirl',950),(other,b'fixedgirl',936)):
                unicode='隊伍測試' if page==950 else '队伍测试';text=unicode.encode('cp'+str(page))
                chat=b'\x2f'+struct.pack('<H',len(text)+8)+bytes(4)+text+b'\0'
                # An already grouped requester cannot join again, but its
                # coalesced common chat must still reach both players.
                rejected_join=self.join(4,5) if page==950 else self.join(5,4)
                self.send(s,owner,rejected_join+chat)
                for recipient,recipient_page,expected in ((first,950,'隊伍測試'),(other,936,'队伍测试')):
                    b=s.decoder.logical(s.helper,recipient);self.assertEqual(b[0],0x5c)
                    self.assertEqual(b[13:-1],speaker+b': '+expected.encode('cp'+str(recipient_page)))
            for owner, observer, identity, coordinates in ((first,other,4,(127,126)),(other,first,5,(128,126))):
                owner.sendall(movement_wire(*coordinates,1))
                ack=s.decoder.logical(s.helper,owner);self.assertEqual(ack[0],0x5d)
                self.assertEqual(s.decoder.logical(s.helper,observer),b'\x56'+struct.pack('<HHH',identity,*coordinates))
                s.helper.silent(owner);s.helper.silent(observer)
                with closing(sqlite3.connect(s.database)) as db:
                    self.assertEqual(db.execute('select area,scene,x,y from recovered_positions where character_id=?',(identity,)).fetchone(),(4,3,*coordinates))

    def test_unavailable_resource_peer_rehydrates_missed_current_hp(self):
        with self.peers() as (s, first, other):
            self.accepted(s, first, other)
            # Disposable synthetic resource variant makes member5 unavailable
            # without changing saves on a real player or inventing battle data.
            with closing(sqlite3.connect(s.database)) as db:
                original=db.execute('select character_id,hp,max_hp from character_resources where character_id in (4,5) order by 1').fetchall()
                db.execute('update character_resources set hp=32768,max_hp=32768 where character_id=5');db.commit()
            self.send(s,other,b'\x30\0');s.helper.silent(other);s.helper.silent(first)
            with closing(sqlite3.connect(s.database)) as db:
                db.execute('update character_resources set hp=40 where character_id=4');db.commit()
            self.send(s,first,b'\x30\0');s.helper.silent(first);s.helper.silent(other)
            with closing(sqlite3.connect(s.database)) as db:
                db.execute('update character_resources set hp=?,max_hp=? where character_id=5',original[1][1:]);db.commit()
            self.send(s,other,b'\x30\0')
            for recipient,actor,position,hp in ((first,5,(129,126),original[1][1]),(other,4,(126,126),40)):
                b=s.decoder.logical(s.helper,recipient)
                self.assertEqual(b,b'\x56'+struct.pack('<HHH',actor,*position)+b'\x58'+struct.pack('<HHIIII',actor,0,hp,26,120,80))
            with closing(sqlite3.connect(s.database)) as db:
                db.executemany('update character_resources set hp=?,max_hp=? where character_id=?',[(hp,maximum,identity) for identity,hp,maximum in original]);db.commit()
            self.send(s,first,b'\x30\0');s.helper.silent(first)
            self.assertEqual(s.decoder.logical(s.helper,other),b'\x58'+struct.pack('<HHIIII',4,0,original[0][1],26,120,80))


# unittest inheritance is used only to borrow guarded fixture helpers.
for _name in tuple(vars(fixture.OwnedRoleTextServerTests)):
    if _name.startswith('test_'): setattr(NativePartyServerTests, _name, None)

if __name__ == '__main__': unittest.main()
