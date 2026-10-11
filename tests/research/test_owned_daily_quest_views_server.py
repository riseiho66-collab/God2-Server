"""Isolated current candidate TCP daily display smoke; no native-client UI."""
from contextlib import ExitStack,closing
import hashlib,json,os,select,socket,sqlite3,subprocess,sys,time,unittest,uuid
from pathlib import Path
import test_recovered_dual_connection_server as dual
import test_inventory_move_server as inventory
from test_current_world_ready_builder import current_world_ready_wire

ROOT=dual.ROOT
sys.path.insert(0,str(ROOT))
from tools.strike_lab import import_native_quests,import_native_quest_sources,import_native_daily_quest_parsed
from tools.strike_lab.current_daily_quest_source_20260927 import CLIENT_SHA
SOURCE=ROOT/'artifacts/playtests/private-owned-map-view-20260926-02'
BINARY=Path(os.environ.get('GOD2_DAILY_TEST_BINARY',ROOT/'build-town-visibility/Release/god2-server.exe'))
MARKER='OWNED_DAILY_NPC_INTENT_UNRESOLVED'


class OwnedDailyQuestViewsServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):dual.RecoveredDualConnectionServerTests.crypto_key=dual.key(ROOT)

    def test_display_intent_denials_and_restart(self):
        here=ROOT/'artifacts/playtests'/('owned-daily-tcp-20260927-'+uuid.uuid4().hex[:8])
        here.mkdir(parents=True,exist_ok=False)
        result={'status':'RUNNING','artifact_directory':str(here),'server_binary':str(BINARY),
            'server_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':[],
            'peer':'synthetic TCP','current_client_ui_tested':False,'executable_quest_rules':False,
            'availability_origin':'CUSTOM_TEST_NOT_NATIVE'}
        def checkpoint():
            (here/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        checkpoint();print(json.dumps({'candidate_sha256':result['server_sha256'],'artifacts':str(here)}),flush=True)
        helper=dual.RecoveredDualConnectionServerTests();decoder=inventory.InventoryMoveServerTests()
        database=here/'town-diagnostic-accounts.db'
        try:
            with closing(sqlite3.connect((SOURCE/'town-diagnostic-accounts.db').resolve().as_uri()+'?mode=ro',uri=True)) as original:
                with closing(sqlite3.connect(database)) as db:original.backup(db)
            config=json.loads((SOURCE/'server-config.json').read_text('utf-8'))
            config['world']['clock']['enabled']=False
            config['world']['owned_daily_quest_views']={'enabled':True}
            config['database']['path']=str(database);config['logging']['file']=str(here/'server.log')
            config['server']['port']=helper.unused_port();endpoint=('127.0.0.1',config['server']['port'])
            config['development']['diagnostic_town']['player_visibility']=False
            cfg=here/'server-config.json'
            def write_config():cfg.write_text(json.dumps(config),encoding='utf-8')
            write_config();env=helper.environment();env['GOD2_LOG_FILE_ONLY']='1'
            with (here/'migration.log').open('wb') as log:
                subprocess.run([str(BINARY),'--config',str(cfg),'--migrate-only'],cwd=ROOT,env=env,
                    stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,check=True,timeout=25)
            with closing(sqlite3.connect(database)) as db:
                result['imports']={'descriptions':import_native_quests.import_catalog(db,ROOT.parent/'God2'),
                    'source':import_native_quest_sources.import_catalog(db,ROOT.parent/'God2'),
                    'parsed':import_native_daily_quest_parsed.import_catalog(db,ROOT.parent/'God2')}
                rows=db.execute('SELECT pair_index,pair_branch,logical FROM native_daily_quest_parsed ORDER BY ordinal LIMIT 9').fetchall()
                self.assertEqual(len(rows),9)
                logical=bytearray(172);logical[:4]=b'\xfd\xac\0\2';logical[164]=9
                for i,(index,branch,_) in enumerate(rows):logical[4+i*4:8+i*4]=bytes((index,branch,0,0x41 if i<8 else 0))
                logical=bytes(logical)
                db.execute('INSERT INTO character_daily_quest_lists(character_id,logical,revision,origin,provenance,client_sha256,design_id) '
                    "VALUES(4,?,1,'CUSTOM_TEST_NOT_NATIVE','isolated-daily-TCP-source-display-only',?,'CUSTOM-0049')",(logical,CLIENT_SHA));db.commit()
                self.assertEqual(db.execute('SELECT item_id FROM diagnostic_inventory_slots WHERE character_id=4 AND item_id=6346').fetchall(),[])
                result['migration30']=db.execute('SELECT name FROM schema_migrations WHERE version=30').fetchone()
            result['expected172_hex']=logical.hex();checkpoint()
            def saved():
                with closing(sqlite3.connect(database)) as db:
                    return '\n'.join(db.iterdump())
            def logtext():return (here/'server.log').read_text('utf-8',errors='replace')
            def markers():return logtext().count(MARKER)
            def select_payload(index=0,side=1,npc=None,tail=0,slot=255):
                row=rows[index];native=row[2]
                npc=int.from_bytes(native[2:4] if side==1 else native[4:6],'little') if npc is None else npc
                return bytes((1,row[0],row[1],slot))+npc.to_bytes(2,'little')+bytes((side,tail))
            with ExitStack() as lifetime:
                def launch():
                    output=lifetime.enter_context((here/'stdout.log').open('ab'))
                    process=subprocess.Popen([str(BINARY),'--config',str(cfg),'--run-for','120'],cwd=ROOT,env=env,
                        stdout=output,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                    lifetime.callback(helper.stop,process);deadline=time.monotonic()+8
                    while True:
                        self.assertIsNone(process.poll(),(here/'stdout.log').read_text('utf-8',errors='replace'))
                        try:
                            with socket.create_connection(endpoint,timeout=.1):return process
                        except OSError:self.assertLess(time.monotonic(),deadline);time.sleep(.025)
                def enter():
                    login=lifetime.enter_context(helper.connect(endpoint));helper.handshake(login)
                    credentials=(b'codexslow',b'labtest2345')
                    login.sendall(helper.frame(*dual.credential(4,*credentials)))
                    helper.read_frame(login,0x1d,176);helper.read_frame(login,4,8);address=helper.read_frame(login,5,12)
                    helper.read_frame(login,6,8);helper.read_frame(login,0x0a,20);self.assertEqual(helper.list_characters(login)[3],1)
                    game=lifetime.enter_context(helper.connect(('127.0.0.1',int.from_bytes(address[9:11],'little'))));helper.handshake(game,game=True)
                    game.sendall(helper.frame(*dual.credential(0,*credentials)));helper.read_frame(game,0x1f,128)
                    game.sendall(helper.frame(0x1a,dual.selection_payload(0)));helper.read_frame(game,2,26)
                    entry=helper.read_frame(game,0x2a,40);identity=int.from_bytes(entry[3:5],'little')&0x3fff
                    self.assertEqual(identity,4)
                    game.sendall(current_world_ready_wire(identity,(4,3)));helper.silent(game)
                    game.sendall(helper.frame(0x30,b'\0'));decoder.logical(helper,game)
                    while select.select([game],[],[],.15)[0]:decoder.logical(helper,game)
                    return game
                def case(name,wire,expected=None,accepted=False):
                    before=saved();count=markers();game.sendall(wire)
                    if expected is None:helper.silent(game)
                    else:self.assertEqual(decoder.logical(helper,game),expected)
                    if accepted:
                        deadline=time.monotonic()+2
                        while markers()==count and time.monotonic()<deadline:time.sleep(.02)
                    self.assertEqual(markers(),count+int(accepted),name)
                    self.assertEqual(saved(),before,name+' mutated SQLite')
                    result['cases'].append({'name':name,'status':'PASS','unresolved_marker_delta':int(accepted),'database_unchanged':True});checkpoint()
                process=launch();game=enter()
                case('unissued_D8_denied',helper.frame(0xd8,select_payload()))
                case('D7_exact172',helper.frame(0xd7,b'\0'),logical)
                case('start_NPC_readonly_intent',helper.frame(0xd8,select_payload(side=1)),accepted=True)
                case('end_NPC_readonly_intent',helper.frame(0xd8,select_payload(side=2)),accepted=True)
                for name,payload in [('wrong_NPC',select_payload(npc=65535)),('disabled_list_entry',select_payload(index=8)),
                    ('nonzero_opaque',select_payload(tail=1)),('wrong_ticket_slot',select_payload(slot=0))]:
                    case(name+'_denied',helper.frame(0xd8,payload))
                case('mixed_D7_D8_denied',helper.frame(0xd7,b'\0\xd8'+select_payload()))
                case('multiple_D8_denied',helper.frame(0xd8,select_payload()+b'\xd8'+select_payload()))
                case('mixed_D8_bagmove_denied',helper.frame(0xd8,select_payload()+b'\x24\0\5'))
                with closing(sqlite3.connect(database)) as db:db.execute('UPDATE character_daily_quest_lists SET revision=revision+1 WHERE character_id=4');db.commit()
                case('stale_revision_denied',helper.frame(0xd8,select_payload()))
                case('reissue_new_revision',helper.frame(0xd7,b'\0'),logical)
                case('reissued_intent',helper.frame(0xd8,select_payload()),accepted=True)
                with closing(sqlite3.connect(database)) as db:
                    self.assertNotEqual(db.execute('SELECT account_id FROM recovered_characters WHERE id=1').fetchone(),(4,))
                    db.execute('UPDATE character_daily_quest_lists SET character_id=1 WHERE character_id=4');db.commit()
                case('other_owner_D7_denied',helper.frame(0xd7,b'\0'))
                case('other_owner_D8_denied',helper.frame(0xd8,select_payload()))
                with closing(sqlite3.connect(database)) as db:db.execute('UPDATE character_daily_quest_lists SET character_id=4 WHERE character_id=1');db.commit()
                game.close();helper.stop(process)
                process=launch();game=enter()
                case('restart_unissued_D8_denied',helper.frame(0xd8,select_payload()))
                case('restart_D7_exact172',helper.frame(0xd7,b'\0'),logical)
                case('restart_readonly_intent',helper.frame(0xd8,select_payload()),accepted=True)
                game.close();helper.stop(process)
                config['world']['owned_daily_quest_views']['enabled']=False;write_config()
                process=launch();game=enter()
                case('flag_disabled_D7_denied',helper.frame(0xd7,b'\0'))
                case('flag_disabled_D8_denied',helper.frame(0xd8,select_payload()))
                game.close();helper.stop(process)
            # Separate derived clones keep the successful playable fixture intact.
            result['startup_denials']=[]
            for corruption in ('partial_parsed84','parsed_byte_changed','raw_and_hash_changed'):
                bad_dir=here/corruption;bad_dir.mkdir()
                bad=bad_dir/'town-diagnostic-accounts.db'
                with closing(sqlite3.connect(database)) as source_db,closing(sqlite3.connect(bad)) as db:
                    source_db.backup(db)
                    if corruption=='partial_parsed84':
                        db.execute('DELETE FROM native_daily_quest_parsed WHERE ordinal=84')
                    elif corruption=='parsed_byte_changed':
                        data=bytearray(db.execute('SELECT logical FROM native_daily_quest_parsed WHERE ordinal=0').fetchone()[0])
                        data[20]^=1
                        db.execute('UPDATE native_daily_quest_parsed SET logical=? WHERE ordinal=0',(bytes(data),))
                    else:
                        data=bytearray(db.execute('SELECT raw_record FROM native_daily_quest_source WHERE record_index=0').fetchone()[0])
                        data[-1]^=1;digest=hashlib.sha256(data).hexdigest()
                        db.execute('UPDATE native_daily_quest_source SET raw_record=?,record_sha256=? WHERE record_index=0',(bytes(data),digest))
                        # Keep per-row provenance references coherent while leaving
                        # parsed316 untouched: full raw source pin must reject this.
                        db.execute('UPDATE native_daily_quest_parsed SET source_record_sha256=? WHERE ordinal=0',(digest,))
                    db.commit();before='\n'.join(db.iterdump())
                bad_config=json.loads(json.dumps(config));bad_config['database']['path']=str(bad)
                bad_config['world']['owned_daily_quest_views']['enabled']=True
                bad_config['server']['port']=helper.unused_port();bad_config['logging']['file']=str(here/(corruption+'-server.log'))
                bad_path=here/(corruption+'-config.json');bad_path.write_text(json.dumps(bad_config),encoding='utf-8')
                completed=subprocess.run([str(BINARY),'--config',str(bad_path),'--run-for','2'],cwd=ROOT,env=env,
                    stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW,timeout=12)
                (here/(corruption+'-stdout.log')).write_bytes(completed.stdout)
                self.assertNotEqual(completed.returncode,0,corruption+' unexpectedly started')
                diagnostic=completed.stdout.decode('utf-8',errors='replace')
                log_path=Path(bad_config['logging']['file'])
                if log_path.exists():diagnostic+='\n'+log_path.read_text('utf-8',errors='replace')
                self.assertIn('Incomplete or changed daily native316 catalog',diagnostic,
                    corruption+' failed for unrelated startup reason')
                with closing(sqlite3.connect(bad)) as db:self.assertEqual('\n'.join(db.iterdump()),before,corruption+' startup mutated database')
                result['startup_denials'].append({'case':corruption,'returncode':completed.returncode,'database_unchanged':True,'diagnostic':diagnostic[-1800:]})
                checkpoint()
            result['status']='PASS';result['unresolved_marker_total']=markers()
            self.assertEqual(hashlib.sha256(BINARY.read_bytes()).hexdigest(),result['server_sha256'])
        except BaseException as error:
            result.update(status='FAIL',error=repr(error));raise
        finally:checkpoint()


if __name__=='__main__':unittest.main()
