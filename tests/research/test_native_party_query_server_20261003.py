"""Real Application/socket query59 tests against a disposable own-server clone."""
import sqlite3
import struct
import unittest
from contextlib import closing
from test_native_party_server import NativePartyServerTests


class PartyPositionQueryTests(NativePartyServerTests):
    @staticmethod
    def query(target, name=b'\xff' * 16):
        if len(name) != 16:
            raise ValueError('Native query must retain all sixteen advisory bytes')
        return b'\x59' + struct.pack('<H', target) + name

    def position_reply(self, state, peer, target, x, y):
        self.assertEqual(state.decoder.logical(state.helper, peer),
                         b'\x56' + struct.pack('<HHH', target, x, y))

    def test_query59_ungrouped_rejected_without_disconnect(self):
        with self.peers() as (s, first, other):
            for raw in (self.query(5), self.query(4), self.query(0), self.query(3000),
                        self.query(65535), self.query(5) + self.query(5)):
                self.send(s, first, raw)
                s.helper.silent(first)
                s.helper.silent(other)
            # The same authenticated sockets remain usable after the denials.
            self.accepted(s, first, other)
            self.send(s, first, self.query(5), fragmented=True)
            self.position_reply(s, first, 5, 129, 126)
            s.helper.silent(other)

    def test_query59_both_members_current_coordinates_and_opaque_names(self):
        with self.peers() as (s, first, other):
            self.accepted(s, first, other)
            for peer, target, coordinates in ((first, 5, (129, 126)), (other, 4, (126, 126))):
                for name in (bytes(16), b'forged-name\0\xff\xff\xff\xff', b'\xff' * 16):
                    self.send(s, peer, self.query(target, name), fragmented=True)
                    self.position_reply(s, peer, target, *coordinates)
            self.assertEqual(s.log().count('delivered=true CUSTOM-0072'), 6)

    def test_query59_mixed_batches_and_bilingual_common_chat(self):
        with self.peers() as (s, first, other):
            self.accepted(s, first, other)
            for raw in (self.query(5) + self.query(5), self.query(5) + b'\x1d\0\0',
                        self.query(5) + self.join(), self.query(4)):
                self.send(s, first, raw)
                s.helper.silent(first)
                s.helper.silent(other)
            for peer, target, page, speaker, coordinates in (
                (first, 5, 950, b'slowgirl', (129, 126)),
                (other, 4, 936, b'fixedgirl', (126, 126)),
            ):
                text=('隊伍定位' if page==950 else '队伍定位').encode('cp'+str(page))
                chat=b'\x2f'+struct.pack('<H',len(text)+8)+bytes(4)+text+b'\0'
                self.send(s, peer, self.query(target)+b'\x30\0'+chat)
                self.position_reply(s, peer, target, *coordinates)
                for recipient, recipient_page, message in (
                    (first, 950, '隊伍定位'), (other, 936, '队伍定位')
                ):
                    response=s.decoder.logical(s.helper,recipient)
                    self.assertEqual(response[0],0x5c)
                    self.assertEqual(response[13:-1],speaker+b': '+message.encode('cp'+str(recipient_page)))

    def test_query59_stale_location_and_departed_member_are_denied(self):
        with self.peers() as (s, first, other):
            self.accepted(s, first, other)
            with closing(sqlite3.connect(s.database)) as db:
                baseline=db.execute('select * from recovered_positions where character_id=5').fetchone()
                db.execute('update recovered_positions set revision=revision+1 where character_id=5')
                db.commit()
            try:
                self.send(s, first, self.query(5));s.helper.silent(first);s.helper.silent(other)
            finally:
                with closing(sqlite3.connect(s.database)) as db:
                    db.execute('update recovered_positions set revision=? where character_id=5',(baseline[5],))
                    db.commit()
            self.send(s, first, self.query(5));self.position_reply(s,first,5,129,126)
            self.send(s, first,b'\x5a'+struct.pack('<H',4)+bytes(16))
            for peer in (first,other):self.removed(s,peer,4,b'slowgirl')
            for peer,target in ((first,5),(other,4)):
                self.send(s,peer,self.query(target));s.helper.silent(peer)
            self.accepted(s,first,other)
            self.send(s,other,self.query(4));self.position_reply(s,other,4,126,126)


def load_tests(loader, tests, pattern):
    # Existing party acceptance runs independently. Select exactly these four
    # new cases, avoiding implicit reruns of inherited unrelated fixture tests.
    return unittest.TestSuite(PartyPositionQueryTests(name) for name in (
        'test_query59_ungrouped_rejected_without_disconnect',
        'test_query59_both_members_current_coordinates_and_opaque_names',
        'test_query59_mixed_batches_and_bilingual_common_chat',
        'test_query59_stale_location_and_departed_member_are_denied',
    ))
