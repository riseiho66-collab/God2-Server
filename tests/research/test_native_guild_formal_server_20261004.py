"""CUSTOM-0078 formal CONFIG routes using disposable ordinary-name copies.
NOT_LIVE_CLIENT_UI: synthetic TCP peers on an explicitly selected owned localhost
candidate. Three lab env flags are absent. No source DB writes, desktop/client
access, import-time network or server startup. Defaults to exclusive port2599.
"""
from contextlib import closing,contextmanager,ExitStack
import ast,hashlib,json,os,socket,sqlite3,subprocess,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
import test_native_guild_entry_server_20261004 as entry_module
fixture=entry_module.fixture
ROOT=entry_module.ROOT
BINARY=Path(os.environ['GOD2_GUILD_FORMAL_TEST_BINARY']) if os.environ.get('GOD2_GUILD_FORMAL_TEST_BINARY') else None
PORT=int(os.environ.get('GOD2_GUILD_FORMAL_TEST_PORT','2599'))
LAB_FLAGS=('GOD2_NATIVE_WORLD_RECORDS_LAB','GOD2_NATIVE_GUILD_MEMBERSHIP_LAB','GOD2_NATIVE_GUILD_ENTRY_LAB')
def clean_environment(helper):
    env=helper.environment()
    for name in LAB_FLAGS:env.pop(name,None)
    env['GOD2_LOG_FILE_ONLY']='1'
    return env
class NativeGuildFormalTests(entry_module.NativeGuildEntryTests):
    @classmethod
    def setUpClass(cls):
        if BINARY is None or not BINARY.is_file():raise AssertionError('Explicit formal candidate binary required')
        if not 1024<=PORT<=65535 or PORT in (2592,56430):raise AssertionError('Owned exclusive test port required')
        fixture.dual.RecoveredDualConnectionServerTests.crypto_key=fixture.dual.key(ROOT)
        print('NOT_LIVE_CLIENT_UI formal config TCP candidate',BINARY,'sha256',hashlib.sha256(BINARY.read_bytes()).hexdigest(),flush=True)
    @contextmanager
    def server(self,diagnostic=False,enabled=True,bundle="CUSTOM-0078-2996-v1",battle=False,teleport=False):
        helper=fixture.dual.RecoveredDualConnectionServerTests()
        source=fixture.SOURCE/'town-diagnostic-accounts.db';before=hashlib.sha256(source.read_bytes()).hexdigest()
        try:
            with tempfile.TemporaryDirectory(prefix='owned-guild-formal-test-') as tmp,ExitStack() as lifetime:
                here=Path(tmp);database=here/('diagnostic-accounts.db' if (diagnostic or battle) else 'town-diagnostic-accounts.db')
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
                        role=bytearray(db.execute('select logical from character_role_snapshots where character_id=?',(identity,)).fetchone()[0]);role[1]=50 if identity==4 else 1
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
                config['database']['path']=str(database);config['server'].update(host='127.0.0.1',port=PORT,character_port=0)
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
                if teleport:
                    config['world']={'clock':{'enabled':False},'owned_teleport_gem':{'enabled':True}}
                    config['development']['diagnostic_town'].update(player_visibility=False,
                        native_npc_placements_only=True,quest_progress=False,spawn_guides=True,
                        map_probe=False,door_routes=True,source_consensus=True,island_routes=True,
                        island_navigation=str(ROOT/'artifacts/world-atlas/island01-entry-2-0.json'))
                config.setdefault('world',{})['owned_guild_membership']={'enabled':enabled,'entry_resource_bundle':bundle}
                if battle:
                    # Existing standalone battle filename guard excludes town diagnostics.
                    config['development'].pop('diagnostic_town',None)
                    config['world'].pop('new_character_birthplace',None)
                    config['development']['recovered_navigation']=str(ROOT/'artifacts/world-atlas/indoor-2-15.json')
                    config['development'].update(diagnostic_battle_transition=True,diagnostic_battle_participants=True,
                        diagnostic_battle_terminal=True,diagnostic_battle_player_appearance=True,
                        diagnostic_battle_animations=True,native_monster_placements_only=False)
                cfg=here/'config.json';cfg.write_text(json.dumps(config),encoding='utf-8');endpoint=('127.0.0.1',PORT)
                # Never stop or reuse someone else's service occupying the lab port.
                with socket.socket() as check:
                    check.settimeout(.1)
                    self.assertNotEqual(check.connect_ex(endpoint),0,'Owned loopback test port already occupied')
                environment=clean_environment(helper)
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
                    if teleport:
                        # Exact qualified TEST_ONLY gem fixture from old gem TCP
                        # test: existing source2/0 to town2/4, no Kunlun guess.
                        item_source='70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
                        db.execute('insert or replace into recovered_positions values(4,2,0,477,210,20)')
                        db.execute('insert or replace into diagnostic_inventory_slots values(?,?,?,?,?,?,?)',
                            (4,12,16055,1,9,item_source,'CUSTOM-0015'))
                        metadata=bytes((0xb7,0x3e,8,4))+bytes(range(0x81,0x91))
                        db.execute('insert into character_teleport_gem_metadata values(?,?,?,?,?,?,?,?)',
                            (4,12,metadata,9,'CUSTOM_TEST_NOT_NATIVE',
                             'TCP isolated synthetic full20; no production grant',item_source,'CUSTOM-0057'))

                    db.commit()
                state=SimpleNamespace(helper=helper,decoder=fixture.inventory.InventoryMoveServerTests(),database=database,
                    endpoint=endpoint,process=process,log=lambda:(here/'server.log').read_text('utf-8',errors='replace'))
                state.config=config;state.cfg=cfg;state.here=here;state.environment=environment;state.output=output
                def restart(new_enabled=enabled,new_bundle=bundle,migrate_only=False,lab=None,expect_failure=False):
                    if state.process is not None:helper.stop(state.process)
                    state.process=None
                    config['world']['owned_guild_membership']={'enabled':new_enabled,'entry_resource_bundle':new_bundle}
                    cfg.write_text(json.dumps(config),encoding='utf-8');env=clean_environment(helper)
                    if lab:env.update(lab)
                    command=[str(BINARY),'--config',str(cfg)]
                    if migrate_only or expect_failure:
                        if migrate_only:command.append('--migrate-only')
                        done=subprocess.run(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                            timeout=20,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                        if expect_failure:self.assertNotEqual(done.returncode,0,done.stdout.decode('utf-8',errors='replace'))
                        else:self.assertEqual(done.returncode,0,done.stdout.decode('utf-8',errors='replace'))
                        return done
                    proc=subprocess.Popen(command+['--run-for','90'],cwd=ROOT,env=env,stdout=output,stderr=subprocess.STDOUT,
                        creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0));lifetime.callback(helper.stop,proc)
                    deadline=time.monotonic()+15
                    while True:
                        self.assertIsNone(proc.poll(),(here/'stdout.log').read_text('utf-8',errors='replace'))
                        try:
                            with socket.create_connection(endpoint,timeout=.1):break
                        except OSError:
                            self.assertLess(time.monotonic(),deadline,'Ordinary formal config restart failed');time.sleep(.025)
                    state.process=proc
                    return proc
                state.restart=restart
                yield state
                if state.process is not None:self.assertIsNone(state.process.poll(),state.log()[-4000:])
                with closing(sqlite3.connect(database)) as db:
                    self.assertEqual(db.execute('pragma quick_check').fetchone(),('ok',))
                    self.assertEqual(db.execute('pragma foreign_key_check').fetchall(),[])
        finally:self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before,'Read-only fixture changed')

    def guild_saved(self,s):
        return {name:rows for name,rows in self.saved(s).items() if name.startswith('owned_guild')}

    def create_and_approve(self,s,lifetime):
        founder=self.enter_peer(s,lifetime,4,b'codexslow',950);self.no_input(self.initial_frames)
        applicant=self.enter_peer(s,lifetime,5,b'codexfixed',936);self.no_input(self.initial_frames);self.drain(s,founder)
        prompt=self.select(s,founder,self.menu(s,founder),0)
        self.send(s,founder,self.membership(prompt,'FormalCave'));self.drain(s,founder);self.drain(s,applicant)
        prompt=self.select(s,applicant,self.menu(s,applicant),1)
        self.send(s,applicant,self.membership(prompt,'FormalCave'));self.drain(s,applicant);self.drain(s,founder)
        self.open_panel(s,founder);self.send(s,founder,b'\x71\x01')
        self.drain(s,founder);self.drain(s,applicant)
        with closing(sqlite3.connect(s.database)) as db:
            self.assertEqual(db.execute('select character_id from owned_guild_members order by character_id').fetchall(),[(4,),(5,)])
        return founder,applicant

    def test_formal_default49_without_lab_env_and_ordinary_parent(self):
        with self.server() as s:
            self.assertFalse(s.database.parent.name.startswith('private-native-blackbox-'))
            self.assertTrue(all(key not in s.environment for key in LAB_FLAGS))
            self.assertEqual(s.endpoint,('127.0.0.1',PORT))
            with closing(sqlite3.connect(s.database)) as db:
                self.assertEqual(db.execute('select max(version) from schema_migrations').fetchone(),(49,))
                self.assertEqual(db.execute('select count(*) from schema_migrations where version=49').fetchone(),(1,))
                self.assertEqual(db.execute('select count(*) from owned_guilds').fetchone(),(0,))

    def test_disabled_nonmember_never_receives_auto_input_or_entry(self):
        with self.server(enabled=False) as s,ExitStack() as lifetime:
            actor=self.enter_peer(s,lifetime,4,b'codexslow',950);self.no_input(self.initial_frames)
            frames=self.unchanged_request(s,actor,self.HELP)
            self.assertFalse(any(f and f[0] in (0x7a,0x8d) for f in frames))
            before=self.guild_saved(s)
            self.send(s,actor,b'\x6f\x01\0\xff\xff'+b'NoPermission'+bytes(4)+b'\0\xa5')
            self.drain(s,actor);self.assertEqual(self.guild_saved(s),before)

    def test_disabled_player_guild_cannot_fallback_0077_founder_or_member73(self):
        with self.server() as s:
            with ExitStack() as lifetime:self.create_and_approve(s,lifetime)
            before=self.guild_saved(s);s.restart(new_enabled=False)
            with ExitStack() as lifetime:
                founder=self.enter_peer(s,lifetime,4,b'codexslow',950);self.no_input(self.initial_frames)
                member=self.enter_peer(s,lifetime,5,b'codexfixed',936);self.no_input(self.initial_frames);self.drain(s,founder)
                for peer in (founder,member):
                    self.send(s,peer,self.HELP);frames=self.drain(s,peer)
                    self.assertFalse(any(f and f[0] in (0x7a,0x8d) for f in frames))
                    for logical in (b'\x73\0',b'\x30\0'+self.HELP+b'\x73\0'):
                        self.send(s,peer,logical);self.drain(s,peer)
                        self.assertEqual(self.guild_saved(s),before)

    def test_same_formal49_restart_and_migrate_only_preserve_membership(self):
        with self.server() as s:
            with ExitStack() as lifetime:self.create_and_approve(s,lifetime)
            before=self.saved(s);s.restart(migrate_only=True)
            self.assertEqual(self.saved(s),before)
            s.restart();self.assertEqual(self.saved(s),before)
            with ExitStack() as lifetime:
                member=self.enter_peer(s,lifetime,5,b'codexfixed',936);self.no_input(self.initial_frames)
                self.send(s,member,self.HELP);frames=self.drain(s,member)
                # Native cache clear/roster records may prefix the header in one logical frame.
                self.assertTrue(any(f[-53:-52]==b'\x8e' for f in frames),[f.hex() for f in frames])
                self.assertEqual(self.guild_saved(s),{k:v for k,v in before.items() if k.startswith('owned_guild')})

    def test_illegal_formal_resource_bundle_rejects_without_SQL_mutation(self):
        with self.server() as s:
            before=self.saved(s);done=s.restart(new_bundle='UNQUALIFIED',expect_failure=True)
            self.assertNotEqual(done.returncode,0);self.assertEqual(self.saved(s),before)

    def test_legacy_lab_environment_non2598_rejects_ordinary_clone(self):
        self.assertNotEqual(PORT,2598,'This case requires normal non-lab port')
        with self.server() as s:
            before=self.saved(s);done=s.restart(lab={key:'1' for key in LAB_FLAGS},expect_failure=True)
            self.assertNotEqual(done.returncode,0);self.assertEqual(self.saved(s),before)

    def test_real_diagnostic_battle_runtime_cancels_ordinary_entry(self):
        # Actual own-server C2S/Tick/battle initialization; TEST_ONLY diagnostic
        # encounter, never a production encounter or rendered-client proof.
        with self.server(battle=True) as s,ExitStack() as lifetime:
            actor=self.enter_peer(s,lifetime,4,b'codexslow',950);self.no_input(self.initial_frames)
            menu=self.menu(s,actor);before=self.guild_saved(s)
            for _ in range(4):
                if 'DIAGNOSTIC_BATTLE_TRANSITION_SENT' in s.log():break
                self.send(s,actor,b'\x30\0');self.drain(s,actor)
            self.assertIn('DIAGNOSTIC_BATTLE_TRANSITION_SENT',s.log())
            self.send(s,actor,b'\x36'+bytes(8));self.drain(s,actor)
            # Server parses this stale native choice in its true battle state;
            # rejection may close the peer, but may never open8D or mutate guild.
            self.send(s,actor,self.choice(menu,0))
            try:frames=self.drain(s,actor)
            except (EOFError,ConnectionError,OSError):frames=[]
            self.no_input(frames);self.assertEqual(self.guild_saved(s),before)

    def test_real_battle_return_old_selector_and_membership_do_not_revive(self):
        # Separate native-input leases, with real Session battle entry/release;
        # TEST_ONLY single-round diagnostic policy, not original battle rules.
        for input_open in (False,True):
            with self.subTest(input_open=input_open),self.server(battle=True) as s,ExitStack() as lifetime:
                actor=self.enter_peer(s,lifetime,4,b'codexslow',950);self.no_input(self.initial_frames)
                menu=self.menu(s,actor)
                prompt=self.select(s,actor,menu,0) if input_open else None
                before=self.guild_saved(s)
                self.send(s,actor,b'\x30\0');self.drain(s,actor)
                self.assertIn('DIAGNOSTIC_BATTLE_TRANSITION_SENT',s.log())
                self.send(s,actor,b'\x36'+bytes(8));self.drain(s,actor)
                # Qualified player diagnostic requires initial empty-target control.
                self.send(s,actor,b'\x35\0\x0b'+bytes(14));self.drain(s,actor)
                # Native C2S35 action1 target group1/bit0 (enemy14), then
                # animation receipt0B using the same verified group mask.
                basic=b'\x35\0\x01\0\0'+bytes(2)+b'\x01\0'+bytes(8)
                receipt=b'\x35\0\x0b\0\0'+bytes(2)+b'\x01\0'+bytes(8)
                self.send(s,actor,basic+receipt);self.drain(s,actor)
                self.assertIn('DIAGNOSTIC_FINISHED_BATTLE_RELEASED',s.log())
                old=self.membership(prompt,'CannotRevive') if input_open else self.choice(menu,0)
                frames=self.unchanged_request(s,actor,old)
                self.no_input(frames);self.assertEqual(self.guild_saved(s),before)

    def test_qualified_native_teleport_revision_cancels_old_selector_and_input(self):
        # Existing qualified2/0->2/4 fixture only. Native25/99 and1C transfer
        # completion through actual Application; no client/GUI or direct state.
        menu_wire=bytes.fromhex('6db73e180181000a0005000000')+bytes(16)
        transfer=bytes.fromhex('6102010000')+((56<<2)|(75<<17)).to_bytes(4,'little')
        for input_open in (False,True):
            with self.subTest(input_open=input_open),self.server(teleport=True) as s,ExitStack() as lifetime:
                actor=self.enter_peer(s,lifetime,4,b'codexslow',950);self.no_input(self.initial_frames)
                selector=self.menu(s,actor)
                prompt=self.select(s,actor,selector,0) if input_open else None
                before=self.guild_saved(s)
                self.send(s,actor,bytes.fromhex('25b73e0ca5'));frames=self.drain(s,actor)
                self.assertIn(menu_wire,frames)
                self.send(s,actor,bytes.fromhex('99b73e05a5'));frames=self.drain(s,actor)
                self.assertTrue(any(frame.endswith(transfer) for frame in frames),[f.hex() for f in frames])
                with closing(sqlite3.connect(s.database)) as db:
                    self.assertEqual(db.execute('select area,scene,x,y,revision from recovered_positions where character_id=4').fetchone(),(2,4,56,75,21))
                self.send(s,actor,bytes.fromhex('1c04000000'));self.drain(s,actor)
                self.send(s,actor,b'\x30\0');self.drain(s,actor)
                stale=self.membership(prompt,'TransferOld') if input_open else self.choice(selector,0)
                frames=self.unchanged_request(s,actor,stale)
                self.no_input(frames);self.assertEqual(self.guild_saved(s),before)
                # A fresh current owner can still obtain a menu after transfer;
                # stale denial is not merely a permanently unready scene.
                fresh=self.menu(s,actor);self.assertNotEqual(fresh[5:7],selector[5:7])


def load_tests(loader,tests,pattern):
    names=[name for name in entry_module.NativeGuildEntryTests.__dict__ if name.startswith('test_')]
    names.extend(name for name in NativeGuildFormalTests.__dict__ if name.startswith('test_'))
    return unittest.TestSuite(NativeGuildFormalTests(name) for name in names)
if __name__=='__main__':unittest.main()
