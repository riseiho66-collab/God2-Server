"""CUSTOM-0074 actual Application TCP privacy acceptance on disposable saves.

Synthetic sockets test routing/state, not rendered original-client acceptance.
The third account/profile is cloned only inside the inherited temporary DB.
"""
from contextlib import closing, contextmanager, ExitStack
import sqlite3
import struct
import unittest

from test_native_party_server import NativePartyServerTests
import test_owned_role_text_server as fixture


class PrivateChatTests(NativePartyServerTests):
    @staticmethod
    def chat(text, selector=2, padding=0xa5, caller=0):
        return b'\x2f' + struct.pack('<HBBH', len(text)+8, selector, padding, caller) + text + b'\0'

    @classmethod
    def whisper(cls, target, message, page=950, **header):
        return cls.chat(('$'+target+' '+message).encode('cp'+str(page)), **header)

    @contextmanager
    def three(self, names=None, allow_movement=False):
        with self.server() as s, ExitStack() as lifetime:
            with closing(sqlite3.connect(s.database)) as db:
                source = fixture.ROOT / 'artifacts/playtests/private-weapon-peer-20260927-04/town-diagnostic-accounts.db'
                with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro', uri=True)) as origin:
                    snapshot = origin.execute('select * from character_role_snapshots where character_id=5').fetchone()
                    resources = origin.execute('select * from character_resources where character_id=5').fetchone()
                self.assertIsNotNone(snapshot); self.assertIsNotNone(resources)
                db.execute('insert or replace into character_role_snapshots values(?,?,?,?)', snapshot)
                db.execute('insert or replace into character_resources values(?,?,?,?,?,?,?)', resources)
                db.execute('update recovered_positions set area=4,scene=3,x=129,y=126 where character_id=5')
                self.assertIsNone(db.execute('select id from recovered_characters where id=6').fetchone())
                # Authentication stores the qualified bytes-namespace identity,
                # not the display ASCII credential; never alter auth behavior.
                db.execute('insert into accounts(id,username,password_hash,created_at) select 6,?,password_hash,created_at from accounts where id=5',
                           ('god2-bytes:'+b'privateoutside'.hex(),))
                db.execute('insert into accounts(id,username,password_hash,created_at) select 7,?,password_hash,created_at from accounts where id=5',
                           ('god2-bytes:'+b'privateunused'.hex(),))
                columns = [row[1] for row in db.execute('pragma table_info(recovered_characters)')]
                row = list(db.execute('select * from recovered_characters where id=5').fetchone())
                row[columns.index('id')]=6; row[columns.index('account_id')]=6
                profile = bytearray(row[columns.index('profile')]); profile[:16]=b'outsidegirl'+bytes(5)
                row[columns.index('profile')]=profile; row[columns.index('name_bytes')]=b'outsidegirl'
                db.execute('insert into recovered_characters values('+','.join('?' for _ in columns)+')', row)
                db.execute('insert into character_role_snapshots values(?,?,?,?)', (6,*snapshot[1:]))
                db.execute('insert into character_resources values(?,?,?,?,?,?,?)', (6,*resources[1:]))
                db.execute('insert into recovered_positions values(6,4,3,128,127,1)')
                # The accepted world initializer creates these exact zero-wallet
                # rows. Seed its documented defaults during fixture setup so the
                # invariant can include every table even before peer entry.
                db.executemany("insert into character_trade_wallets values(?,0,1,'CUSTOM-0063') on conflict(character_id) do nothing",
                               ((4,),(5,),(6,)))
                for identity,(text,page) in (names or {}).items():
                    name=text.encode('cp'+str(page))
                    profile=bytearray(db.execute('select profile from recovered_characters where id=?',(identity,)).fetchone()[0])
                    profile[:16]=name+bytes(16-len(name))
                    db.execute('update recovered_characters set profile=?,name_bytes=?,name_codepage=? where id=?', (profile,name,page,identity))
                db.commit()
            def saved():
                with closing(sqlite3.connect(s.database)) as db:
                    self.assertEqual(db.execute('pragma quick_check').fetchone(), ('ok',))
                    self.assertEqual(db.execute('pragma foreign_key_check').fetchall(), [])
                    return {name:(sql,sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"')))
                            for name,sql in db.execute("select name,sql from sqlite_master where type='table' order by name").fetchall()
                            if not (allow_movement and name=='recovered_positions')}
            before=saved()
            games=[self.enter_peer(s,lifetime,identity,account,page) for identity,account,page in
                   ((4,b'codexslow',950),(5,b'codexfixed',936),(6,b'privateoutside',950))]
            yield s,*games
            self.assertEqual(saved(),before,'Private chat changed saved rows or schema')

    def message(self,s,recipient,identity,source,target,page,text,mode=2):
        response=s.decoder.logical(s.helper,recipient)
        self.assertEqual(response[0],0x5c)
        self.assertEqual(struct.unpack_from('<H',response,1)[0],len(response))
        self.assertEqual(struct.unpack_from('<I',response,5)[0],identity)
        self.assertEqual(response[9],mode|(0x80 if page==936 else 0))
        self.assertEqual(response[13:-1],(source+': ['+target+'] '+text).encode('cp'+str(page)))
        self.assertEqual(response[-1],0)

    def silent(self,s,*peers):
        for peer in peers:s.helper.silent(peer)

    def test_bilingual_headers_privacy_and_mode9_reply(self):
        with self.three() as (s,first,other,outside):
            for owner,receiver,identity,source,target,page in (
                    (first,other,4,'slowgirl','fixedgirl',950),
                    (other,first,5,'fixedgirl','slowgirl',936)):
                for selector,caller in ((2,0),(0x82,0xffff),(2,6),(9,0xffff),(0x89,0)):
                    text='密語測試' if page==950 else '密语测试'
                    self.send(s,owner,self.whisper(target,text,page,selector=selector,caller=caller),fragmented=True)
                    for recipient,recipient_page,expected in ((first,950,'密語測試'),(other,936,'密语测试')):
                        self.message(s,recipient,identity,source,target,recipient_page,expected,mode=selector&0x7f)
                    self.silent(s,outside,first,other)
            # Third authenticated owner may address one peer; the unrelated first
            # peer must remain silent despite sharing the same visible world.
            self.send(s,outside,self.whisper('fixedgirl','outside-private',caller=4))
            self.message(s,outside,6,'outsidegirl','fixedgirl',950,'outside-private')
            self.message(s,other,6,'outsidegirl','fixedgirl',936,'outside-private')
            self.silent(s,first,outside,other)

    def test_missing_self_malformed_encoding_and_batch_atomicity(self):
        with self.three() as (s,first,other,outside):
            for wire in (self.whisper('absent','missing',caller=5),self.whisper('slowgirl','self'),
                         self.chat(b'no-dollar message'),self.chat(b'$fixedgirl'),
                         self.chat(b'$fixedgirl '),self.chat(b'$fixedgirl \x81'),
                         self.whisper('fixedgirl','first')+self.whisper('absent','second')):
                self.send(s,first,wire);self.silent(s,first,other,outside)
            # Every mixed mutation/other family denies before publication or SQL.
            for suffix in (self.join(),b'\x1d\0\0',b'\x20'+b'forbidden'+bytes(7),
                           self.chat(b'common',selector=0),self.chat(b'party',selector=1)):
                self.send(s,first,self.whisper('fixedgirl','mixed')+suffix)
                self.silent(s,first,other,outside)
            self.send(s,first,self.whisper('fixedgirl','one')+b'\x30\0'+self.whisper('outsidegirl','two',selector=9))
            self.message(s,first,4,'slowgirl','fixedgirl',950,'one')
            self.message(s,first,4,'slowgirl','outsidegirl',950,'two',mode=9)
            self.message(s,other,4,'slowgirl','fixedgirl',936,'one')
            self.message(s,outside,4,'slowgirl','outsidegirl',950,'two',mode=9)
            self.silent(s,first,other,outside)

    def test_exact_unicode_unique_target_no_name_normalization(self):
        names={4:('台',950),5:('臺',936),6:('外人',950)}
        with self.three(names=names) as (s,first,other,outside):
            self.send(s,first,self.whisper('臺','exact-target'))
            self.message(s,first,4,'台','臺',950,'exact-target')
            self.message(s,other,4,'台','臺',936,'exact-target')
            self.silent(s,outside,first,other)
            # OpenCC-normalizing 台 into 臺 would accidentally grant self routing.
            self.send(s,first,self.whisper('台','self'))
            self.silent(s,first,other,outside)
        with self.three(names={5:('同名',936),6:('同名',950)}) as (s,first,other,outside):
            for caller in (0,5,6,0xffff):
                self.send(s,first,self.whisper('同名','ambiguous',caller=caller))
                self.silent(s,first,other,outside)

    def test_stale_ownership_position_disconnect_and_relogin(self):
        with self.three() as (s,first,other,outside):
            with closing(sqlite3.connect(s.database)) as db:
                revision=db.execute('select revision from recovered_positions where character_id=5').fetchone()[0]
                db.execute('update recovered_positions set revision=revision+1 where character_id=5');db.commit()
            try:
                self.send(s,first,self.whisper('fixedgirl','stale-position'));self.silent(s,first,other,outside)
            finally:
                with closing(sqlite3.connect(s.database)) as db:
                    db.execute('update recovered_positions set revision=? where character_id=5',(revision,));db.commit()
            with closing(sqlite3.connect(s.database)) as db:
                db.execute('update recovered_characters set account_id=7 where id=5');db.commit()
            try:
                self.send(s,first,self.whisper('fixedgirl','stale-owner'));self.silent(s,first,other,outside)
            finally:
                with closing(sqlite3.connect(s.database)) as db:
                    db.execute('update recovered_characters set account_id=5 where id=5');db.commit()
            other.close()
            self.send(s,first,self.whisper('fixedgirl','offline'));self.silent(s,first,outside)
            with ExitStack() as lifetime:
                returned=self.enter_peer(s,lifetime,5,b'codexfixed',936)
                self.send(s,first,self.whisper('fixedgirl','rejoined',selector=9))
                self.message(s,first,4,'slowgirl','fixedgirl',950,'rejoined',mode=9)
                self.message(s,returned,4,'slowgirl','fixedgirl',936,'rejoined',mode=9)
                self.silent(s,outside,first,returned)

    def ordinary_message(self,s,recipient,identity,name,page,text,mode):
        b=s.decoder.logical(s.helper,recipient)
        self.assertEqual(b[0],0x5c);self.assertEqual(struct.unpack_from('<I',b,5)[0],identity)
        self.assertEqual(b[9],mode|(0x80 if page==936 else 0))
        self.assertEqual(b[13:-1],name+b': '+text.encode('cp'+str(page)))

    def test_common_party_regression_and_private_group_isolation(self):
        with self.three() as (s,first,other,outside):
            self.send(s,first,self.chat(b'common-survives',selector=0))
            for peer,page in ((first,950),(other,936),(outside,950)):
                self.ordinary_message(s,peer,4,b'slowgirl',page,'common-survives',0)
            self.accepted(s,first,other);self.silent(s,outside)
            self.send(s,other,self.chat(b'party-survives',selector=1))
            for peer,page in ((first,950),(other,936)):
                self.ordinary_message(s,peer,5,b'fixedgirl',page,'party-survives',1)
            self.silent(s,outside)
            self.send(s,first,self.whisper('outsidegirl','non-party-target'))
            self.message(s,first,4,'slowgirl','outsidegirl',950,'non-party-target')
            self.message(s,outside,4,'slowgirl','outsidegirl',950,'non-party-target')
            self.silent(s,other,first,outside)

    @staticmethod
    def positions(s):
        with closing(sqlite3.connect(s.database)) as db:
            return {row[0]:row for row in db.execute('select * from recovered_positions order by character_id')}

    def test_coalesced_movement_ack_party_projection_and_private_chat(self):
        with self.three(allow_movement=True) as (s,first,other,outside):
            self.accepted(s,first,other);self.silent(s,outside)
            for owner,observer,identity,source,target,page,x in (
                    (first,other,4,'slowgirl','fixedgirl',950,127),
                    (other,first,5,'fixedgirl','slowgirl',936,128)):
                before=self.positions(s)
                movement=b'\x2e'+struct.pack('<HHBB',x,126,1,0xa5)
                self.send(s,owner,movement+self.whisper(target,'move-private',page))
                self.assertEqual(s.decoder.logical(s.helper,owner),b'\x5d\x01')
                self.message(s,owner,identity,source,target,page,'move-private')
                self.assertEqual(s.decoder.logical(s.helper,observer),b'\x56'+struct.pack('<HHH',identity,x,126))
                self.message(s,observer,identity,source,target,936 if page==950 else 950,'move-private')
                self.silent(s,owner,observer,outside)
                after=self.positions(s)
                changed=sorted(key for key in before.keys()|after.keys() if before.get(key)!=after.get(key))
                self.assertEqual(changed,[identity])
                self.assertEqual(after[identity][:5],(identity,4,3,x,126))
                self.assertEqual(after[identity][5],(before[identity][5] if identity in before else 0)+1)

    def test_rejected_private_batch_does_not_apply_coalesced_movement(self):
        with self.three() as (s,first,other,outside):
            before=self.positions(s)
            movement=b'\x2e'+struct.pack('<HHBB',127,126,1,0xff)
            for target in ('absent','slowgirl'):
                self.send(s,first,movement+self.whisper(target,'denied-move'))
                self.silent(s,first,other,outside)
                self.assertEqual(self.positions(s),before)


NAMES=(
    'test_bilingual_headers_privacy_and_mode9_reply',
    'test_missing_self_malformed_encoding_and_batch_atomicity',
    'test_exact_unicode_unique_target_no_name_normalization',
    'test_stale_ownership_position_disconnect_and_relogin',
    'test_common_party_regression_and_private_group_isolation',
    'test_coalesced_movement_ack_party_projection_and_private_chat',
    'test_rejected_private_batch_does_not_apply_coalesced_movement',
)

def load_tests(loader,tests,pattern):
    return unittest.TestSuite(PrivateChatTests(name) for name in NAMES)

if __name__=='__main__':unittest.main()
