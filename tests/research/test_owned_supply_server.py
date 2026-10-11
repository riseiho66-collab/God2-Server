"""Owned MED02 promotion TCP acceptance on disposable companion-preserving clones."""
from contextlib import ExitStack,closing
import hashlib,json,os,select,socket,sqlite3,struct,subprocess,sys,time,unittest,uuid
from pathlib import Path
import test_recovered_dual_connection_server as dual
import test_inventory_move_server as inventory
from test_current_world_ready_builder import current_world_ready_wire
ROOT=dual.ROOT
sys.path.insert(0,str(ROOT))
from tools.strike_lab import import_native_med02_recovery as native
SOURCE=ROOT/'artifacts/playtests/private-owned-companions-20260926-04'
BINARY=Path(os.environ.get('GOD2_OWNED_SUPPLY_BINARY',ROOT/'build-town-visibility/Release/god2-server.exe'))

class OwnedSupplyServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):dual.RecoveredDualConnectionServerTests.crypto_key=dual.key(ROOT)
    def test_owned_supply_preserves_companions_and_denies_invalid_state(self):
        here=ROOT/'artifacts/playtests'/('owned-supply-tcp-20260927-'+uuid.uuid4().hex[:8]);here.mkdir(parents=True)
        result={'status':'RUNNING','server_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),
                'binary':str(BINARY),'cases':[],'peer':'synthetic TCP','current_client_ui_tested':False}
        def checkpoint():(here/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        checkpoint();print(json.dumps({'sha256':result['server_sha256'],'artifacts':str(here)}),flush=True)
        helper=dual.RecoveredDualConnectionServerTests();decoder=inventory.InventoryMoveServerTests();database=here/'town-diagnostic-accounts.db'
        def connectdb():return closing(sqlite3.connect(database))
        def saved():
            with connectdb() as db:return '\n'.join(db.iterdump())
        def mutate(sql,values=()):
            with connectdb() as db:db.execute(sql,values);db.commit()
        companion_tables=('character_deities','character_deity_selection','character_pet2_slots')
        def companions():
            with connectdb() as db:return {t:db.execute('SELECT * FROM '+t+' ORDER BY 1,2').fetchall() for t in companion_tables}
        try:
            with closing(sqlite3.connect((SOURCE/'town-diagnostic-accounts.db').resolve().as_uri()+'?mode=ro',uri=True)) as source,connectdb() as db:source.backup(db)
            preserved=companions();self.assertEqual(len(preserved['character_deities']),2)
            config=json.loads((SOURCE/'server-config.json').read_text('utf-8'))
            config.setdefault('world',{})['clock']={'enabled':False};config['world']['owned_supply']={'enabled':True}
            config['development'].update(diagnostic_world_supply=False,diagnostic_world_resources=False)
            config['development']['diagnostic_town'].update(player_visibility=False,quest_progress=False,map_probe=False)
            config['database']['path']=str(database);config['logging']['file']=str(here/'server.log')
            config['server']['port']=helper.unused_port();endpoint=('127.0.0.1',config['server']['port'])
            cfg=here/'server-config.json';cfg.write_text(json.dumps(config),encoding='utf-8')
            env=helper.environment();env['GOD2_LOG_FILE_ONLY']='1'
            with (here/'migration.log').open('wb') as log:subprocess.run([str(BINARY),'--config',str(cfg),'--migrate-only'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,check=True,timeout=25)
            with connectdb() as db:
                result['import']=native.import_catalog(db,ROOT.parent/'God2')
                for slot,item,count in ((5,3101,2),(12,3107,3)):
                    db.execute('UPDATE diagnostic_inventory_slots SET item_id=?,count=?,revision=1,source_sha256=? WHERE character_id=4 AND slot=?',(item,count,native.SOURCE_SHA,slot))
                    self.assertEqual(db.execute('SELECT changes()').fetchone(),(1,))
                db.execute('UPDATE character_resources SET hp=20,max_hp=120,mp=2,max_mp=80,revision=1 WHERE character_id=4')
                role=bytearray(db.execute('SELECT logical FROM character_role_snapshots WHERE character_id=4').fetchone()[0]);struct.pack_into('<II',role,17,120,80)
                db.execute('UPDATE character_role_snapshots SET logical=? WHERE character_id=4',(bytes(role),));db.commit()
            self.assertEqual(companions(),preserved)
            def request(item=3101,slot=5,target=4,tail=0):return struct.pack('<BHHBB',0x26,target,item,slot,tail)
            def frame(logical):return helper.frame(logical[0],logical[1:])
            def state():
                with connectdb() as db:return (db.execute('SELECT hp,mp,revision FROM character_resources WHERE character_id=4').fetchone(),db.execute('SELECT slot,item_id,count,revision FROM diagnostic_inventory_slots WHERE character_id=4 AND slot IN(5,12) ORDER BY slot').fetchall())
            with ExitStack() as lifetime:
                def launch():
                    out=lifetime.enter_context((here/'stdout.log').open('ab'))
                    p=subprocess.Popen([str(BINARY),'--config',str(cfg),'--run-for','120'],cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                    lifetime.callback(helper.stop,p);deadline=time.monotonic()+8
                    while True:
                        self.assertIsNone(p.poll(),(here/'stdout.log').read_text('utf-8',errors='replace'))
                        try:
                            with socket.create_connection(endpoint,timeout=.1):return p
                        except OSError:self.assertLess(time.monotonic(),deadline);time.sleep(.025)
                def enter(expected_counts,label=None):
                    login=lifetime.enter_context(helper.connect(endpoint));helper.handshake(login);credentials=(b'codexslow',b'labtest2345')
                    login.sendall(helper.frame(*dual.credential(4,*credentials)));helper.read_frame(login,0x1d,176);helper.read_frame(login,4,8);address=helper.read_frame(login,5,12)
                    helper.read_frame(login,6,8);helper.read_frame(login,0x0a,20);self.assertEqual(helper.list_characters(login)[3],1)
                    g=lifetime.enter_context(helper.connect(('127.0.0.1',int.from_bytes(address[9:11],'little'))));helper.handshake(g,game=True)
                    g.sendall(helper.frame(*dual.credential(0,*credentials)));helper.read_frame(g,0x1f,128);g.sendall(helper.frame(0x1a,dual.selection_payload(0)))
                    helper.read_frame(g,2,26);entry=helper.read_frame(g,0x2a,40);self.assertEqual(int.from_bytes(entry[3:5],'little')&0x3fff,4)
                    g.sendall(current_world_ready_wire(4,(2,4)));helper.silent(g);g.sendall(helper.frame(0x30,b'\0'))
                    received=[decoder.logical(helper,g)]
                    while select.select([g],[],[],.15)[0]:received.append(decoder.logical(helper,g))
                    joined=b''.join(received)
                    if expected_counts is not None:
                        for slot,item,count in ((5,3101,expected_counts[0]),(12,3107,expected_counts[1])):
                            self.assertIn(inventory.projection(slot,item,count),joined,'Missing complete3B+41 supply slot restore')
                    else:
                        self.assertNotIn(inventory.projection(5,3120,2),joined,'Unqualified3120 projected as qualified supply')
                    self.assertEqual(companions(),preserved)
                    result['cases'].append({'name':label or 'world_restore_'+str(expected_counts),'status':'PASS','wire_hex':[v.hex() for v in received]});checkpoint()
                    return g
                def denied(name,logical):
                    before=saved();game.sendall(frame(logical));helper.silent(game);self.assertEqual(saved(),before,name+' changed DB');self.assertEqual(companions(),preserved)
                    result['cases'].append({'name':name,'status':'PASS','database_unchanged':True});checkpoint()
                def use(name,logical,item,slot,count,hp,mp):
                    game.sendall(frame(logical));reply=decoder.logical(helper,game)
                    expected=b'\x41'+struct.pack('<HBB',item,slot,count)+b'\x24'+struct.pack('<IIII',hp,mp,120,80)
                    self.assertEqual(reply,expected,name);self.assertEqual(state()[0][:2],(hp,mp));self.assertEqual(companions(),preserved)
                    result['cases'].append({'name':name,'status':'PASS','reply_hex':reply.hex(),'state':state()});checkpoint()
                process=launch();game=enter((2,3))
                for name,logical in [('wrong_target',request(target=1)),('wrong_item',request(item=3107)),('wrong_slot',request(slot=6)),('equipment_slot',request(slot=34)),('unknown_item',request(item=3120)),('duplicate',request()+request()),('mixed_bag_move',request()+b'\x24\5\6')]:denied(name,logical)
                mutate('UPDATE diagnostic_inventory_slots SET item_id=3120 WHERE character_id=4 AND slot=5');denied('owned_unmatched_MED02',request(item=3120));mutate('UPDATE diagnostic_inventory_slots SET item_id=3101 WHERE character_id=4 AND slot=5')
                mutate('UPDATE diagnostic_inventory_slots SET source_sha256=? WHERE character_id=4 AND slot=5',('0'*64,));denied('wrong_slot_source',request());mutate('UPDATE diagnostic_inventory_slots SET source_sha256=? WHERE character_id=4 AND slot=5',(native.SOURCE_SHA,))
                mutate('UPDATE character_resources SET hp=0 WHERE character_id=4');denied('dead_actor',request());mutate('UPDATE character_resources SET hp=20 WHERE character_id=4')
                mutate('UPDATE diagnostic_inventory_slots SET character_id=1 WHERE character_id=4 AND slot=5');denied('other_owner_slot',request());mutate('UPDATE diagnostic_inventory_slots SET character_id=4 WHERE character_id=1 AND slot=5')
                mutate("INSERT INTO battle_reservations(character_id,resource_revision,design_id) VALUES(4,1,'CUSTOM-0012')")
                denied('pending_battle',request());mutate('DELETE FROM battle_reservations WHERE character_id=4 AND resource_revision=1')
                use('HP100_plus_ticks',b'\x30\0'+request()+b'\x30\0',3101,5,1,120,2)
                denied('HP_at_cap_no_consume',request(tail=255))
                use('MP50_tail255_trailing1F',request(3107,12,tail=255)+b'\x1f\0',3107,12,2,120,52)
                use('MP50_clamp80',request(3107,12),3107,12,1,120,80)
                denied('both_full_no_consume',request(3107,12,tail=255))
                self.assertEqual(state(),((120,80,4),[(5,3101,1,2),(12,3107,1,3)]))
                before_restart=state();game.close();helper.stop(process);process=launch();game=enter((1,1));self.assertEqual(state(),before_restart)
                denied('restart_full_no_consume',request(3107,12,tail=255));game.close();helper.stop(process)
                original_database=database
                config['development']['diagnostic_town'].update(spawn_guides=True,native_npc_placements_only=True,quest_progress=True)
                for admission in ('fresh_world_no_bag_rows','fresh_world_owned_unqualified3120'):
                    admission_dir=here/admission;admission_dir.mkdir()
                    admission_db=admission_dir/'town-diagnostic-accounts.db'
                    with closing(sqlite3.connect(original_database)) as source_db,closing(sqlite3.connect(admission_db)) as db:
                        source_db.backup(db)
                        db.execute('DELETE FROM diagnostic_inventory_slots WHERE character_id=4')
                        if admission.endswith('3120'):
                            db.execute("INSERT INTO diagnostic_inventory_slots VALUES(4,5,3120,2,1,?,'CUSTOM-0015')",(native.SOURCE_SHA,))
                        db.commit()
                    database=admission_db;config['database']['path']=str(database);cfg.write_text(json.dumps(config),encoding='utf-8')
                    before=saved();process=launch();game=enter(None,admission)
                    # A second tick must leave the connection live and the complete
                    # clone unchanged: no auto grants or skipped unsupported rows.
                    game.sendall(frame(b'\x30\0'));helper.silent(game)
                    self.assertEqual(saved(),before,admission+' mutated world-entry save')
                    self.assertEqual(companions(),preserved)
                    result['cases'][-1].update(database_unchanged=True,connection_open_after_tick=True,
                        formal_guide_flags=dict(spawn_guides=True,native_npc_placements_only=True,quest_progress=True))
                    checkpoint();game.close();helper.stop(process)
                database=original_database;config['database']['path']=str(database);cfg.write_text(json.dumps(config),encoding='utf-8')
            result['startup_denials']=[]
            for corruption in ('missing_source','partial70','raw_changed','amount_changed'):
                bad_dir=here/corruption;bad_dir.mkdir();bad=bad_dir/'town-diagnostic-accounts.db'
                with connectdb() as original,closing(sqlite3.connect(bad)) as db:
                    original.backup(db)
                    if corruption=='missing_source':db.execute('DELETE FROM native_med02_recovery_declarations')
                    sql={'missing_source':"DELETE FROM native_data_sources WHERE dataset_id='current-med02-recovery-v1'",'partial70':'DELETE FROM native_med02_recovery_declarations WHERE item_id=3101','raw_changed':"UPDATE native_med02_recovery_declarations SET raw_record=CAST(X'30'||substr(raw_record,2) AS BLOB) WHERE item_id=3101",'amount_changed':'UPDATE native_med02_recovery_declarations SET declared_hp=101 WHERE item_id=3101'}[corruption]
                    db.execute(sql);db.commit();before='\n'.join(db.iterdump())
                conf=json.loads(json.dumps(config));conf['database']['path']=str(bad);conf['server']['port']=helper.unused_port();conf['logging']['file']=str(bad_dir/'server.log')
                path=bad_dir/'config.json';path.write_text(json.dumps(conf),encoding='utf-8')
                p=subprocess.run([str(BINARY),'--config',str(path),'--run-for','2'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,timeout=12)
                (bad_dir/'stdout.log').write_bytes(p.stdout);diagnostic=p.stdout.decode('utf-8',errors='replace')
                self.assertNotEqual(p.returncode,0,corruption);self.assertIn('MED02',diagnostic,corruption+' unrelated failure')
                with closing(sqlite3.connect(bad)) as db:self.assertEqual('\n'.join(db.iterdump()),before)
                result['startup_denials'].append({'case':corruption,'status':'PASS','error':diagnostic,'database_unchanged':True});checkpoint()
            result['status']='PASS';result['final_state']=state();result['companion_tables_unchanged']=companions()==preserved
            log=(here/'server.log').read_text('utf-8',errors='replace')
            supply_lines=[line for line in log.splitlines() if 'OWNED_SUPPLY_USE ' in line]
            consumed=[line for line in supply_lines if 'consumed=true ' in line]
            self.assertEqual(len(consumed),3,'Unexpected committed supply marker count')
            for before,after in (('hp_before=20','hp_after=120'),('mp_before=2','mp_after=52'),('mp_before=52','mp_after=80')):
                self.assertTrue(any(before in line and after in line for line in consumed),'Missing supply before/after marker')
            result['supply_markers']=supply_lines
            self.assertEqual(hashlib.sha256(BINARY.read_bytes()).hexdigest(),result['server_sha256'])
        except BaseException as error:result.update(status='FAIL',error=repr(error));raise
        finally:checkpoint()

if __name__=='__main__':unittest.main()
