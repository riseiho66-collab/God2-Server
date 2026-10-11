"""CUSTOM0078 real Application TCP, synthetic peers: NOT_LIVE_CLIENT_UI.

Only copied TEST_ONLY saves, loopback2598 and explicit candidate49 are used.
Existing helpers are imported read-only; no client/desktop/formal DB changes.
"""
from contextlib import closing, contextmanager, ExitStack
import hashlib, json, os, select, socket, sqlite3, struct, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from test_native_party_server import NativePartyServerTests
import test_owned_role_text_server as fixture

ROOT=fixture.ROOT
BINARY=Path(os.environ.get('GOD2_GUILD_LEADERSHIP_TEST_BINARY',
    ROOT/'build-native-guild-leadership-20261003/Release/god2-server.exe'))

class GuildLeadershipTests(NativePartyServerTests):
    @classmethod
    def setUpClass(cls):
        if not BINARY.is_file():raise AssertionError('Build-matched leader candidate is required')
        fixture.dual.RecoveredDualConnectionServerTests.crypto_key=fixture.dual.key(ROOT)
        print('NOT_LIVE_CLIENT_UI leader TCP candidate:',BINARY,'SHA256',hashlib.sha256(BINARY.read_bytes()).hexdigest(),flush=True)

    @contextmanager
    def server(self):
        helper=fixture.dual.RecoveredDualConnectionServerTests()
        source=fixture.SOURCE/'town-diagnostic-accounts.db';before=hashlib.sha256(source.read_bytes()).hexdigest()
        try:
            with tempfile.TemporaryDirectory(prefix='private-native-blackbox-leader-tcp-') as tmp,ExitStack() as lifetime:
                here=Path(tmp);database=here/'town-diagnostic-accounts.db'
                with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True)) as origin,closing(sqlite3.connect(database)) as copy:
                    origin.backup(copy)
                with closing(sqlite3.connect(database)) as db:
                    db.execute('delete from character_deity_selection where character_id=4')
                    db.execute('delete from character_deities where character_id=4 and row_key=100')
                    db.execute('insert into character_deity_selection values(4,101,1)')
                    db.execute('delete from recovered_positions where character_id=4')
                    peer_source=ROOT/'artifacts/playtests/private-weapon-peer-20260927-04/town-diagnostic-accounts.db'
                    with closing(sqlite3.connect(peer_source.resolve().as_uri()+'?mode=ro',uri=True)) as peers:
                        for table in ('character_role_snapshots','character_resources'):
                            row=peers.execute('select * from '+table+' where character_id=5').fetchone();self.assertIsNotNone(row)
                            db.execute('insert or replace into '+table+' values('+','.join('?' for _ in row)+')',row)
                    db.execute('update recovered_positions set area=4,scene=3,x=129,y=126 where character_id=5')
                    for identity in (4,5):
                        role=bytearray(db.execute('select logical from character_role_snapshots where character_id=?',(identity,)).fetchone()[0]);role[1]=50
                        db.execute('update character_role_snapshots set logical=? where character_id=?',(role,identity))
                    db.commit()
                config=json.loads((fixture.SOURCE/'server-config.json').read_text('utf-8'))
                config['world']={'new_character_birthplace':{'area':4,'scene':3,'kind':0,'x':126,'y':126,
                    'navigation':str(ROOT/'artifacts/world-atlas/kunlun-4-3.json'),'coordinate_authority':'CUSTOM-0040'},'clock':{'enabled':False}}
                config['database']['path']=str(database);config['server'].update(host='127.0.0.1',port=2598,character_port=0)
                config['logging'].update(file=str(here/'server.log'),level='debug');config['protocol']['packet_dump']=False
                config['development']['diagnostic_town'].update(player_visibility=False,native_npc_placements_only=True,
                    quest_progress=False,spawn_guides=False,map_probe=False,door_routes=False)
                cfg=here/'config.json';cfg.write_text(json.dumps(config),encoding='utf-8');endpoint=('127.0.0.1',2598)
                # Never stop or reuse someone else's service occupying the lab port.
                with socket.socket() as check:
                    check.settimeout(.1)
                    self.assertNotEqual(check.connect_ex(endpoint),0,'Loopback lab2598 already occupied')
                environment=helper.environment();environment.update(GOD2_LOG_FILE_ONLY='1',GOD2_NATIVE_WORLD_RECORDS_LAB='1',GOD2_NATIVE_GUILD_MEMBERSHIP_LAB='1')
                output=lifetime.enter_context((here/'stdout.log').open('ab'))
                process=subprocess.Popen([str(BINARY),'--config',str(cfg),'--run-for','90'],cwd=ROOT,env=environment,
                    stdout=output,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                lifetime.callback(helper.stop,process);deadline=time.monotonic()+15
                while True:
                    self.assertIsNone(process.poll(),(here/'stdout.log').read_text('utf-8',errors='replace'))
                    try:
                        with socket.create_connection(endpoint,timeout=.1):break
                    except OSError:
                        self.assertLess(time.monotonic(),deadline,'Private leader candidate failed to listen');time.sleep(.025)
                with closing(sqlite3.connect(database)) as db:
                    self.assertEqual(db.execute('select max(version) from schema_migrations').fetchone(),(49,))
                    db.executemany("insert into character_trade_wallets values(?,100000,1,'CUSTOM-0063') on conflict(character_id) do update set amount=100000",[(4,),(5,)])
                    db.commit()
                state=SimpleNamespace(helper=helper,decoder=fixture.inventory.InventoryMoveServerTests(),database=database,
                    endpoint=endpoint,process=process,log=lambda:(here/'server.log').read_text('utf-8',errors='replace'))
                yield state
                self.assertIsNone(process.poll(),state.log()[-4000:])
                with closing(sqlite3.connect(database)) as db:
                    self.assertEqual(db.execute('pragma quick_check').fetchone(),('ok',))
                    self.assertEqual(db.execute('pragma foreign_key_check').fetchall(),[])
        finally:self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before,'Read-only fixture changed')

    def drain(self,s,peer,first=False):
        frames=super().drain(s,peer,first)
        if first:self.initial_frames=frames
        return frames

    @staticmethod
    def membership(prompt,name='WireCave'):
        raw=name.encode('ascii');assert prompt[0]==0x8d and len(prompt)==5
        return b'\x6f'+prompt[1:3]+b'\xff\xff'+raw+bytes(16-len(raw))+bytes([prompt[3],0xa5])

    def rows(self,frames):
        result=[]
        for frame in frames:
            if not frame or frame[0] not in (0x91,0x92,0x8e):continue
            offset=0
            while offset<len(frame):
                size={0x91:22,0x92:2,0x8e:53}.get(frame[offset]);self.assertIsNotNone(size,frame.hex())
                self.assertLessEqual(offset+size,len(frame));record=frame[offset:offset+size]
                if record[0]==0x91:result.append(record)
                offset+=size
        return result

    def saved(self,s):
        with closing(sqlite3.connect(s.database)) as db:
            return {name:sorted(repr(row) for row in db.execute('select * from "'+name.replace('"','""')+'"'))
                for (name,) in db.execute("select name from sqlite_schema where type='table' order by name").fetchall()}

    @contextmanager
    def ready(self,page=950):
        with self.server() as s,ExitStack() as lifetime:
            leader=self.enter_peer(s,lifetime,4,b'codexslow',page)
            prompt=next(r for r in self.initial_frames if r[0]==0x8d);self.assertEqual(prompt[3],0)
            self.send(s,leader,self.membership(prompt),fragmented=True);self.drain(s,leader)
            with closing(sqlite3.connect(s.database)) as db:
                self.assertEqual(db.execute('select owner_character from owned_guild_governance_0078').fetchone(),(4,))
                self.assertEqual(db.execute('select character_id from owned_guild_members').fetchall(),[(4,)])
            applicant=self.enter_peer(s,lifetime,5,b'codexfixed',936 if page==950 else 950)
            prompt=next(r for r in self.initial_frames if r[0]==0x8d);self.assertEqual(prompt[3],1)
            self.send(s,applicant,self.membership(prompt));self.drain(s,applicant);self.drain(s,leader)
            with closing(sqlite3.connect(s.database)) as db:self.assertEqual(db.execute('select character_id from owned_guild_applications_0078').fetchall(),[(5,)])
            yield s,leader,applicant

    def open_panel(self,s,leader):
        self.send(s,leader,b'\x37\x7b\x08\0\0');frames=self.drain(s,leader,first=True)
        rows=self.rows(frames);self.assertEqual([(r[1],r[2]) for r in rows],[(0,3),(1,0)])
        self.assertEqual(rows[1][6:22].split(b'\0',1)[0],b'fixedgirl')
        header=next(f[-53:] for f in frames if f[-53:-52]==b'\x8e')
        self.assertEqual((header[14],header[20],header[24]),(6,1,20))

    def test_approve_both_locales_replay_and_creator73_protection(self):
        for page in (950,936):
            with self.subTest(page=page),self.ready(page) as (s,leader,applicant):
                self.open_panel(s,leader);before=self.saved(s)
                for peer,slot in ((applicant,1),(leader,0),(leader,49)):
                    self.send(s,peer,bytes([0x71,slot]));self.drain(s,peer)
                    self.assertEqual(self.saved(s),before)
                self.send(s,leader,b'\x71\x01');leader_rows=self.rows(self.drain(s,leader,first=True))
                member_rows=self.rows(self.drain(s,applicant,first=True))
                self.assertEqual([(r[1],r[2]) for r in leader_rows],[(0,3),(1,1)])
                self.assertEqual([(r[1],r[2]) for r in member_rows],[(0,1),(1,3)])
                after=self.saved(s)
                for name,rows in before.items():
                    if name not in ('owned_guilds','owned_guild_members','owned_guild_applications_0078'):
                        self.assertEqual(after[name],rows,name)
                with closing(sqlite3.connect(s.database)) as db:
                    self.assertEqual(db.execute('select character_id from owned_guild_members order by character_id').fetchall(),[(4,),(5,)])
                    self.assertEqual(db.execute('select * from owned_guild_applications_0078').fetchall(),[])
                for raw in (b'\x71\x01',b'\x72\x01',b'\x73\0',b'\x30\0\xb8\0\x73\0'):
                    self.send(s,leader,raw);self.drain(s,leader);self.drain(s,applicant);self.assertEqual(self.saved(s),after)
                self.assertIn('action=113 slot=1 committed=true CUSTOM-0078',s.log())
                self.assertIn('slot=0 committed=false CUSTOM-0077',s.log())

    def test_reject_and_stale_tick_b8_help_or_membership_marker_cannot_grant(self):
        with self.ready() as (s,leader,applicant):
            for opcode in (0x71,0x72):
                for prefix in (b'\x30\0',b'\xb8\0',b'\x37\x7b\x08\0\0'):
                    self.open_panel(s,leader)
                    with closing(sqlite3.connect(s.database)) as db:db.execute('update owned_guilds set revision=revision+1');db.commit()
                    before=self.saved(s);self.send(s,leader,prefix+bytes([opcode,1]));self.drain(s,leader);self.drain(s,applicant)
                    self.assertEqual(self.saved(s),before)
            self.open_panel(s,leader);before=self.saved(s)
            marker=b'\x6f\x01\0\xff\xff'+b'Unused'+bytes(10)+b'\0\xa5'
            self.send(s,leader,b'\x30\0'+marker+b'\x71\x01\x73\0')
            self.drain(s,leader);self.drain(s,applicant);self.assertEqual(self.saved(s),before)
            self.open_panel(s,leader);self.send(s,leader,b'\x72\x01');self.drain(s,leader,first=True)
            with closing(sqlite3.connect(s.database)) as db:
                self.assertEqual(db.execute('select * from owned_guild_applications_0078').fetchall(),[])
                self.assertEqual(db.execute('select character_id from owned_guild_members').fetchall(),[(4,)])
            after=self.saved(s);self.send(s,leader,b'\x72\x01');self.drain(s,leader);self.assertEqual(self.saved(s),after)
            self.assertIn('action=114 slot=1 committed=true CUSTOM-0078',s.log())

    def test_chat_prefix_and_suffix_preserved_around_approve(self):
        with self.ready() as (s,leader,applicant):
            self.open_panel(s,leader)
            chat=lambda text:b'\x2f'+struct.pack('<HBBH',len(text)+8,0,0xa5,0)+text+b'\0'
            self.send(s,leader,chat(b'before-approve')+b'\x71\x01'+chat(b'after-approve'))
            for peer in (leader,applicant):
                frames=self.drain(s,peer,first=True);messages=[f[13:-1] for f in frames if f[0]==0x5c]
                self.assertEqual(messages,[b'slowgirl: before-approve',b'slowgirl: after-approve'])
                self.assertEqual(frames[0][0],0x5c,'Prefix common chat must precede mutation responses')
                self.assertTrue(self.rows(frames))
            with closing(sqlite3.connect(s.database)) as db:self.assertEqual(db.execute('select character_id from owned_guild_members order by character_id').fetchall(),[(4,),(5,)])

    def test_malformed_leadership_batch_closes_without_prefix_chat_or_sql(self):
        with self.ready() as (s,leader,applicant):
            self.open_panel(s,leader);before=self.saved(s)
            text=b'cannot-leak';chat=b'\x2f'+struct.pack('<HBBH',len(text)+8,0,0xa5,0)+text+b'\0'
            self.send(s,leader,chat+b'\x71\x32');self.assertEqual(leader.recv(1),b'')
            self.assertEqual(self.drain(s,applicant),[]);self.assertEqual(self.saved(s),before)

def load_tests(loader,tests,pattern):
    return unittest.TestSuite(GuildLeadershipTests(name) for name in GuildLeadershipTests.__dict__ if name.startswith('test_'))
if __name__=='__main__':unittest.main()
