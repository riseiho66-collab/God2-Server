"""CUSTOM0078 Application entry TCP synthetic peers; NOT_LIVE_CLIENT_UI.

Only read-only copied saves, explicit candidate49 and loopback2598. Requires
GOD2_GUILD_ENTRY_TEST_BINARY explicitly; no server is launched on import/parse.
Existing leadership fixture imported read-only. Never touch desktop/clients.
"""
from contextlib import closing, contextmanager, ExitStack
import hashlib, json, os, select, socket, sqlite3, struct, subprocess, sys, tempfile, time, unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from test_native_guild_leadership_server_20261003 import GuildLeadershipTests
import test_owned_role_text_server as fixture

ROOT=fixture.ROOT
_BINARY=os.environ.get('GOD2_GUILD_ENTRY_TEST_BINARY')
BINARY=Path(_BINARY) if _BINARY else None

class NativeGuildEntryTests(GuildLeadershipTests):
    @classmethod
    def setUpClass(cls):
        if BINARY is None or not BINARY.is_file():raise AssertionError('Explicit build-matched entry candidate is required')
        fixture.dual.RecoveredDualConnectionServerTests.crypto_key=fixture.dual.key(ROOT)
        print('NOT_LIVE_CLIENT_UI entry TCP candidate:',BINARY,'SHA256',hashlib.sha256(BINARY.read_bytes()).hexdigest(),flush=True)

    @contextmanager
    def server(self,diagnostic=False):
        helper=fixture.dual.RecoveredDualConnectionServerTests()
        source=fixture.SOURCE/'town-diagnostic-accounts.db';before=hashlib.sha256(source.read_bytes()).hexdigest()
        try:
            with tempfile.TemporaryDirectory(prefix='private-native-blackbox-entry-tcp-') as tmp,ExitStack() as lifetime:
                here=Path(tmp);database=here/('diagnostic-accounts.db' if diagnostic else 'town-diagnostic-accounts.db')
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
                    if diagnostic:
                        # TEST_ONLY conversation with no owned quest/reward. The
                        # formal source remains read-only and byte-identical.
                        if db.execute("select 1 from sqlite_master where type='table' and name='character_quest_journals'").fetchone():
                            db.execute('delete from character_quest_journals where character_id in (4,5)')
                    db.commit()
                config=json.loads((fixture.SOURCE/'server-config.json').read_text('utf-8'))
                config['world']={'new_character_birthplace':{'area':4,'scene':3,'kind':0,'x':126,'y':126,
                    'navigation':str(ROOT/'artifacts/world-atlas/kunlun-4-3.json'),'coordinate_authority':'CUSTOM-0040'},'clock':{'enabled':False}}
                config['database']['path']=str(database);config['server'].update(host='127.0.0.1',port=2598,character_port=0)
                config['logging'].update(file=str(here/'server.log'),level='debug');config['protocol']['packet_dump']=False
                config['development']['diagnostic_town'].update(player_visibility=False,native_npc_placements_only=True,
                    quest_progress=False,spawn_guides=False,map_probe=False,door_routes=False)
                if diagnostic:
                    # Standalone diagnostic9A and the town fixture have distinct
                    # filename gates. Use the already qualified bootstrap2/15
                    # navigation and remove town/birthplace options; no gate is
                    # weakened or production map placement claimed.
                    config['development'].pop('diagnostic_town',None)
                    config['world']={'clock':{'enabled':False}}
                    config['development']['recovered_navigation']=str(ROOT/'artifacts/world-atlas/indoor-2-15.json')
                    config['development'].update(diagnostic_quest_dialogue=True,diagnostic_quest_npc=False,
                                                 diagnostic_world_resources=False,diagnostic_battle_transition=False)
                cfg=here/'config.json';cfg.write_text(json.dumps(config),encoding='utf-8');endpoint=('127.0.0.1',2598)
                # Never stop or reuse someone else's service occupying the lab port.
                with socket.socket() as check:
                    check.settimeout(.1)
                    self.assertNotEqual(check.connect_ex(endpoint),0,'Loopback lab2598 already occupied')
                environment=helper.environment();environment.update(GOD2_LOG_FILE_ONLY='1',GOD2_NATIVE_WORLD_RECORDS_LAB='1',GOD2_NATIVE_GUILD_MEMBERSHIP_LAB='1',GOD2_NATIVE_GUILD_ENTRY_LAB='1')
                output=lifetime.enter_context((here/'stdout.log').open('ab'))
                process=subprocess.Popen([str(BINARY),'--config',str(cfg),'--run-for','90'],cwd=ROOT,env=environment,
                    stdout=output,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                lifetime.callback(helper.stop,process);deadline=time.monotonic()+15
                while True:
                    self.assertIsNone(process.poll(),(here/'stdout.log').read_text('utf-8',errors='replace'))
                    try:
                        with socket.create_connection(endpoint,timeout=.1):break
                    except OSError:
                        self.assertLess(time.monotonic(),deadline,'Private entry candidate failed to listen');time.sleep(.025)
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

    HELP=b'\x37\x7b\x08\0\0'
    CLOSE=b'\x86\x13\0\x5a\xa5' # native opaque pointer words do not grant authority

    @staticmethod
    def choice(menu,value=0,context=None,request=None):
        nonce=int.from_bytes(menu[5:7],'little') if request is None else request
        return b'\x85'+struct.pack('<HHBB',nonce,value,menu[4] if context is None else context,0xa5)

    @staticmethod
    def chat(text):
        return b'\x2f'+struct.pack('<HBBH',len(text)+8,0,0xa5,0)+text+b'\0'

    def no_input(self,frames):
        self.assertFalse(any(frame and frame[0]==0x8d for frame in frames),[f.hex() for f in frames])

    def menu(self,s,peer,logical=None):
        before=self.saved(s);self.send(s,peer,self.HELP if logical is None else logical);frames=self.drain(s,peer)
        menus=[frame for frame in frames if frame and frame[0]==0x7a]
        self.assertEqual(len(menus),1,[f.hex() for f in frames]);menu=menus[0]
        self.assertEqual(len(menu),28);self.assertEqual(menu[:5],b'\x7a\x1c\0\4\xe7')
        self.assertEqual(menu[7:9],struct.pack('<H',2996));self.assertGreater(int.from_bytes(menu[5:7],'little'),0)
        self.assertEqual(menu[9:],bytes(19));self.no_input(frames);self.assertEqual(self.saved(s),before)
        return menu

    def select(self,s,peer,menu,value=0,fragmented=False):
        before=self.saved(s);self.send(s,peer,self.choice(menu,value),fragmented=fragmented)
        frames=self.drain(s,peer);self.assertEqual(self.saved(s),before)
        prompts=[frame for frame in frames if frame and frame[0]==0x8d]
        self.assertEqual(len(prompts),1,[f.hex() for f in frames]);prompt=prompts[0]
        self.assertEqual(len(prompt),5);self.assertEqual(prompt[3],value);self.assertEqual(prompt[4],0)
        self.assertGreater(int.from_bytes(prompt[1:3],'little'),0)
        return prompt

    @contextmanager
    def entered(self,page=950,both=False,diagnostic=False):
        with self.server(diagnostic=diagnostic) as s,ExitStack() as lifetime:
            actor=self.enter_peer(s,lifetime,4,b'codexslow',page);self.no_input(self.initial_frames)
            if both:
                other=self.enter_peer(s,lifetime,5,b'codexfixed',936 if page==950 else 950);self.no_input(self.initial_frames)
                self.drain(s,actor)
            else:other=None
            yield s,actor,other

    def unchanged_request(self,s,peer,logical,no_input=True):
        before=self.saved(s);self.send(s,peer,logical);frames=self.drain(s,peer)
        self.assertEqual(self.saved(s),before)
        if no_input:self.no_input(frames)
        return frames

    def rejected_closed_request(self,s,peer,logical):
        # Unissued/future E7 follows the preserved unclaimed QuestAction route:
        # EOF is a rejection, never an accepted entry or an input publication.
        before=self.saved(s);self.send(s,peer,logical)
        self.assertEqual(peer.recv(1),b'','Unissued/future entry action must reject without publishing an input')
        self.assertEqual(self.saved(s),before)

    def test_entry_create_apply_both_locales_no_auto_prompt_and_replay(self):
        for page in (950,936):
            with self.subTest(page=page),self.entered(page,both=True) as (s,founder,applicant):
                menu=self.menu(s,founder);prompt=self.select(s,founder,menu,0,fragmented=True)
                before=self.saved(s);wire=self.membership(prompt,'EntryCave')
                self.send(s,founder,wire,fragmented=True);self.drain(s,founder);self.drain(s,applicant)
                with closing(sqlite3.connect(s.database)) as db:
                    self.assertEqual(db.execute('select owner_character,created_cost,capacity from owned_guild_governance_0078').fetchall(),[(4,50000,20)])
                    self.assertEqual(db.execute('select character_id from owned_guild_members').fetchall(),[(4,)])
                    self.assertEqual(db.execute('select amount from character_trade_wallets where character_id=4').fetchone(),(50000,))
                after=self.saved(s)
                for name,rows in before.items():
                    if name not in ('owned_guilds','owned_guild_members','owned_guild_governance_0078','character_trade_wallets'):
                        self.assertEqual(after[name],rows,name)
                self.unchanged_request(s,founder,wire)
                self.unchanged_request(s,founder,self.choice(menu,0))
                menu=self.menu(s,applicant);prompt=self.select(s,applicant,menu,1)
                wire=self.membership(prompt,'eNtRyCaVe');before=self.saved(s)
                self.send(s,applicant,wire);self.drain(s,applicant);self.drain(s,founder)
                after=self.saved(s)
                with closing(sqlite3.connect(s.database)) as db:
                    self.assertEqual(db.execute('select character_id from owned_guild_applications_0078').fetchall(),[(5,)])
                    self.assertEqual(db.execute('select character_id from owned_guild_members').fetchall(),[(4,)])
                for name,rows in before.items():
                    if name not in ('owned_guild_applications_0078','sqlite_sequence'):
                        self.assertEqual(after[name],rows,name)
                self.unchanged_request(s,applicant,wire)
                # Pending applicant/founder cannot obtain another entry menu.
                for peer in (applicant,founder):
                    frames=self.unchanged_request(s,peer,self.HELP)
                    self.assertFalse(any(f and f[0]==0x7a for f in frames))
                self.assertIn('key=2996 entry=native_help_CUSTOM',s.log())

    def test_exit_cancel_illegal_choice_one_use_and_bad_identity_both_locales(self):
        for page in (950,936):
            with self.subTest(page=page),self.entered(page) as (s,peer,_):
                guessed=b'\x8d\x01\0\0\0'
                self.unchanged_request(s,peer,self.membership(guessed))
                for kind in ('exit','close','illegal'):
                    menu=self.menu(s,peer)
                    raw=self.CLOSE if kind=='close' else self.choice(menu,2 if kind=='exit' else 4)
                    self.unchanged_request(s,peer,raw)
                    self.unchanged_request(s,peer,self.choice(menu,0))
                    self.unchanged_request(s,peer,self.membership(guessed))
                menu=self.menu(s,peer);prompt=self.select(s,peer,menu,0);self.assertEqual(prompt[3],0)
                self.unchanged_request(s,peer,self.choice(menu,0))
            fake=b'\x7a\x1c\0\4\xe7\x01\0'+struct.pack('<H',2996)+bytes(19)
            for prefix in (b'',self.HELP,b'\x30\0'):
                with self.subTest(page=page,unissued_prefix=prefix.hex()),self.entered(page) as (s,peer,_):
                    self.rejected_closed_request(s,peer,prefix+self.choice(fake,0))
                    with ExitStack() as reconnect:
                        fresh=self.enter_peer(s,reconnect,4,b'codexslow',page);self.no_input(self.initial_frames)
                        self.unchanged_request(s,fresh,self.membership(b'\x8d\x01\0\0\0'))
                        self.rejected_closed_request(s,fresh,self.choice(fake,0))

    def test_mixed_help_choice_and_choice_membership_cannot_borrow_prefix(self):
        for page in (950,936):
            with self.subTest(page=page),self.entered(page) as (s,peer,_):
                menu=self.menu(s,peer)
                guessed=b'\x8d\x01\0\0\0'
                self.unchanged_request(s,peer,self.choice(menu,0)+self.membership(guessed))
                self.unchanged_request(s,peer,self.choice(menu,0))
                self.unchanged_request(s,peer,self.membership(guessed))
                # A fresh help cannot revive a stale choice inside the same batch.
                menu=self.menu(s,peer)
                self.unchanged_request(s,peer,self.HELP+self.choice(menu,0))
                self.unchanged_request(s,peer,self.choice(menu,0))
                # Two matching choices use at most one published authority.
                menu=self.menu(s,peer);before=self.saved(s)
                self.send(s,peer,self.choice(menu,0)+self.choice(menu,1));frames=self.drain(s,peer)
                prompts=[f for f in frames if f and f[0]==0x8d]
                self.assertEqual(len(prompts),1);self.assertEqual(prompts[0][3],0);self.assertEqual(self.saved(s),before)

    def test_tick_marker_old_panel_and_sql_staleness_never_grant_entry(self):
        with self.entered(both=True) as (s,peer,other):
            guessed=b'\x8d\x01\0\0\0';marker=self.membership(guessed)
            for raw in (b'\x30\0'+marker+b'\x73\0',
                        self.HELP+marker+b'\x73\0',b'\xb8\0'+marker+b'\x73\0'):
                frames=self.unchanged_request(s,peer,raw);self.no_input(frames)
            menu=self.menu(s,peer)
            self.unchanged_request(s,other,marker);self.rejected_closed_request(s,other,self.choice(menu,0))
            with closing(sqlite3.connect(s.database)) as db:db.execute('update character_role_snapshots set revision=revision+1 where character_id=4');db.commit()
            self.unchanged_request(s,peer,b'\x30\0'+self.choice(menu,0))
            self.unchanged_request(s,peer,self.choice(menu,0))
            menu=self.menu(s,peer);prompt=self.select(s,peer,menu,0)
            with closing(sqlite3.connect(s.database)) as db:db.execute('update character_role_snapshots set revision=revision+1 where character_id=4');db.commit()
            self.unchanged_request(s,peer,b'\x30\0'+self.membership(prompt))
            self.unchanged_request(s,peer,self.membership(prompt))

    def test_legal_coalesced_chat_delivered_but_cancels_modal_authority(self):
        for page in (950,936):
            with self.subTest(page=page),self.entered(page,both=True) as (s,peer,other):
                menu=self.menu(s,peer);before=self.saved(s)
                self.send(s,peer,self.chat(b'before-entry')+self.choice(menu,0)+self.chat(b'after-entry'))
                frames=self.drain(s,peer);others=self.drain(s,other)
                for received in (frames,others):
                    self.assertEqual([f[13:-1] for f in received if f and f[0]==0x5c],
                                     [b'slowgirl: before-entry',b'slowgirl: after-entry'])
                self.assertEqual(frames[0][0],0x5c)
                self.no_input(frames);self.assertEqual(self.saved(s),before)
                # Existing CUSTOM0078 modal policy: legal chat is delivered,
                # but it cancels entry/input authority before whole-batch use.
                self.unchanged_request(s,peer,self.choice(menu,0))
                menu=self.menu(s,peer);prompt=self.select(s,peer,menu,0)
                before=self.saved(s)
                self.send(s,peer,self.chat(b'cancel-input')+self.membership(prompt))
                for received in (self.drain(s,peer),self.drain(s,other)):
                    self.assertEqual([f[13:-1] for f in received if f and f[0]==0x5c],[b'slowgirl: cancel-input'])
                self.assertEqual(self.saved(s),before)
                self.unchanged_request(s,peer,self.membership(prompt))
                self.unchanged_request(s,other,self.membership(prompt))

    def test_published_ordinary_panel73_not_reauthorized_by_6f_help_prefix(self):
        with self.entered(both=True) as (s,founder,member):
            menu=self.menu(s,founder);prompt=self.select(s,founder,menu,0)
            self.send(s,founder,self.membership(prompt,'PanelCave'));self.drain(s,founder);self.drain(s,member)
            menu=self.menu(s,member);prompt=self.select(s,member,menu,1)
            self.send(s,member,self.membership(prompt,'PanelCave'));self.drain(s,member);self.drain(s,founder)
            self.open_panel(s,founder);self.send(s,founder,b'\x71\1');self.drain(s,founder);self.drain(s,member)
            marker=b'\x6f\1\0\xff\xff'+b'Unused'+bytes(10)+b'\0\xa5'
            for stale in (False,True):
                self.send(s,member,self.HELP);frames=self.drain(s,member)
                self.assertEqual([(r[1],r[2]) for r in self.rows(frames)],[(0,1),(1,3)])
                if stale:
                    with closing(sqlite3.connect(s.database)) as db:db.execute('update owned_guilds set revision=revision+1');db.commit()
                before=self.saved(s)
                self.send(s,member,b'\x30\0'+marker+self.HELP+b'\x73\0')
                self.drain(s,member);self.drain(s,founder);self.assertEqual(self.saved(s),before)
                with closing(sqlite3.connect(s.database)) as db:
                    self.assertEqual(db.execute('select character_id from owned_guild_members order by character_id').fetchall(),[(4,),(5,)])

    def test_existing_diagnostic_quest9a_is_not_entry_authority_or_swallowed(self):
        for page in (950,936):
            for entry_open in (False,True):
                with self.subTest(page=page,entry_open=entry_open),self.entered(page,diagnostic=True) as (s,peer,_):
                    dialogue=[f for f in self.initial_frames if f and f[0]==0x7a and len(f)==27 and f[3:5]==b'\x01\x9a']
                    self.assertEqual(len(dialogue),1,[f.hex() for f in self.initial_frames])
                    old=dialogue[0];self.assertEqual(int.from_bytes(old[5:7],'little'),0x1234)
                    if entry_open:self.menu(s,peer)
                    before=self.saved(s);count=s.log().count('DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED ')
                    action=b'\x85'+struct.pack('<HHBB',int.from_bytes(old[5:7],'little'),2,0x9a,0xa5)
                    self.send(s,peer,action);frames=self.drain(s,peer);self.no_input(frames)
                    self.assertEqual(self.saved(s),before)
                    self.assertEqual(s.log().count('DIAGNOSTIC_QUEST_CONFIRM_ACCEPTED '),count+1,
                                     'Authenticated preexisting quest9A must reach its original conversation consumer')
                    self.assertNotIn('OWNED_GUILD_ENTRY_CHOICE ',s.log(),'Quest9A cannot be consumed as entry choice')

    def test_help_chat_both_orders_preserve_chat_without_new_modal_permission(self):
        for page in (950,936):
            for prefix_chat in (False,True):
                with self.subTest(page=page,prefix_chat=prefix_chat),self.entered(page,both=True) as (s,peer,other):
                    benign=self.menu(s,peer,self.HELP+b'\x30\0\xb8\0')
                    self.unchanged_request(s,peer,self.choice(benign,2))
                    # Existing menu must be invalidated; no new menu may be
                    # published after help/chat whole-batch modal invalidation.
                    stale=self.menu(s,peer);before=self.saved(s)
                    text=b'chat-then-help' if prefix_chat else b'help-then-chat'
                    raw=self.chat(text)+self.HELP if prefix_chat else self.HELP+self.chat(text)
                    self.send(s,peer,raw);frames=self.drain(s,peer);others=self.drain(s,other)
                    for received in (frames,others):
                        self.assertEqual([f[13:-1] for f in received if f and f[0]==0x5c],[b'slowgirl: '+text])
                    self.assertFalse(any(f and f[0]==0x7a for f in frames),'Mixed help/chat must not publish new modal permission')
                    self.no_input(frames);self.assertEqual(self.saved(s),before)
                    self.unchanged_request(s,peer,self.choice(stale,0))
                    # The next guessed request is not issued; E7 alone grants
                    # nothing even if the client predicts a transport nonce.
                    self.rejected_closed_request(s,peer,self.choice(stale,0,request=int.from_bytes(stale[5:7],'little')+1))
                    with ExitStack() as reconnect:
                        fresh=self.enter_peer(s,reconnect,4,b'codexslow',page);self.no_input(self.initial_frames)
                        self.unchanged_request(s,fresh,self.membership(b'\x8d\x01\0\0\0'))
                        self.rejected_closed_request(s,fresh,self.choice(stale,0))

    def test_choice_close_batch_cancels_new_input_and_reverse_never_opens(self):
        for page in (950,936):
            with self.subTest(page=page),self.entered(page) as (s,peer,_):
                menu=self.menu(s,peer);before=self.saved(s)
                self.send(s,peer,self.choice(menu,0)+self.CLOSE);frames=self.drain(s,peer)
                prompts=[f for f in frames if f and f[0]==0x8d]
                self.assertLessEqual(len(prompts),1);self.assertEqual(self.saved(s),before)
                guessed=prompts[0] if prompts else b'\x8d\x01\0\0\0'
                self.unchanged_request(s,peer,self.membership(guessed,'ClosedInput'))
                self.unchanged_request(s,peer,self.choice(menu,0))
                menu=self.menu(s,peer)
                self.unchanged_request(s,peer,self.CLOSE+self.choice(menu,0))
                self.unchanged_request(s,peer,self.choice(menu,0))
                self.unchanged_request(s,peer,self.membership(guessed,'ClosedReverse'))

def load_tests(loader,tests,pattern):
    return unittest.TestSuite(NativeGuildEntryTests(name) for name in NativeGuildEntryTests.__dict__ if name.startswith('test_'))
if __name__=='__main__':unittest.main()
