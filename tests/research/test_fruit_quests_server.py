"""Disposable own-server fruit quest TCP regression; not current-client proof."""
from contextlib import ExitStack,closing
import hashlib,json,os,select,socket,sqlite3,struct,subprocess,sys,time,unittest,uuid
from pathlib import Path
from types import SimpleNamespace
import test_recovered_dual_connection_server as dual
import test_inventory_move_server as inventory
from test_current_world_ready_builder import current_world_ready_wire
ROOT=dual.ROOT
sys.path.insert(0,str(ROOT))
from tools.strike_lab import private_fruit_quests_20260927 as fixture
BINARY=Path(os.environ.get('GOD2_FRUIT_QUEST_BINARY',ROOT/'build-town-visibility/Release/god2-server-fruit-quests-20260927.exe'))


class FruitQuestServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):dual.RecoveredDualConnectionServerTests.crypto_key=dual.key(ROOT)

    def test_all_four_owned_quest_transactions(self):
        here=ROOT/'artifacts/playtests'/('fruit-quests-tcp-20260927-'+uuid.uuid4().hex[:8]);here.mkdir(parents=True)
        result={'status':'RUNNING','binary':str(BINARY),'server_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),
                'peer':'synthetic TCP','current_client_ui_tested':False,'quests':[]}
        def save():(here/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        save();print(json.dumps({'artifacts':str(here),'actual_server_sha256':result['server_sha256']}),flush=True)
        helper=dual.RecoveredDualConnectionServerTests();decoder=inventory.InventoryMoveServerTests()
        try:
            for mission in (234,236,237,238):
                output=here/str(mission);fixture.prepare(SimpleNamespace(output=output,mission=mission,server_candidate=BINARY))
                database=output/'town-diagnostic-accounts.db';cfg=output/'server-config.json';config=json.loads(cfg.read_text('utf-8'))
                config['server']['port']=helper.unused_port();config['world']['clock']['enabled']=False
                cfg.write_text(json.dumps(config),encoding='utf-8');endpoint=('127.0.0.1',config['server']['port']);quest=fixture.source_quest(mission)
                evidence={'mission':mission,'cases':[]};result['quests'].append(evidence)
                def db():return closing(sqlite3.connect(database))
                def state():
                    with db() as d:
                        return {'xp':d.execute('SELECT total FROM character_experience WHERE character_id=4').fetchone()[0],
                            'bag':[list(r) for r in d.execute('SELECT slot,item_id,count,revision FROM diagnostic_inventory_slots WHERE character_id=4 AND slot BETWEEN 0 AND 29 ORDER BY slot')],
                            'journal':d.execute('SELECT hex(values_blob),revision FROM character_quest_journals WHERE character_id=4').fetchone()}
                def full():
                    with db() as d:return '\n'.join(d.iterdump())
                def send(game,logical):game.sendall(helper.frame(logical[0],logical[1:]))
                def drain(game):
                    records=[]
                    while select.select([game],[],[],.15)[0]:records.append(decoder.logical(helper,game))
                    return records
                with ExitStack() as lifetime:
                    env=helper.environment();env['GOD2_LOG_FILE_ONLY']='1'
                    out=lifetime.enter_context((output/'stdout.log').open('wb'))
                    process=subprocess.Popen([str(BINARY),'--config',str(cfg),'--run-for','100'],cwd=ROOT,env=env,stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
                    lifetime.callback(helper.stop,process)
                    deadline=time.monotonic()+10
                    while True:
                        self.assertIsNone(process.poll(),'Candidate exited during startup')
                        try:
                            with socket.create_connection(endpoint,timeout=.1):break
                        except OSError:self.assertLess(time.monotonic(),deadline);time.sleep(.03)
                    def enter():
                        login=lifetime.enter_context(helper.connect(endpoint));helper.handshake(login);credentials=(b'codexslow',b'labtest2345')
                        login.sendall(helper.frame(*dual.credential(4,*credentials)));helper.read_frame(login,0x1d,176);helper.read_frame(login,4,8);address=helper.read_frame(login,5,12)
                        helper.read_frame(login,6,8);helper.read_frame(login,0x0a,20);self.assertEqual(helper.list_characters(login)[3],1)
                        game=lifetime.enter_context(helper.connect(('127.0.0.1',int.from_bytes(address[9:11],'little'))));helper.handshake(game,game=True)
                        game.sendall(helper.frame(*dual.credential(0,*credentials)));helper.read_frame(game,0x1f,128);game.sendall(helper.frame(0x1a,dual.selection_payload(0)))
                        helper.read_frame(game,2,26);entry=helper.read_frame(game,0x2a,40);self.assertEqual(int.from_bytes(entry[3:5],'little')&0x3fff,4)
                        game.sendall(current_world_ready_wire(4,(13,12)));helper.silent(game);send(game,b'\x30\0')
                        restore=drain(game);self.assertTrue(restore,'No world restore');evidence['cases'].append({'name':'world_entry','wire_hex':[r.hex() for r in restore]});return login,game
                    def open_dialogue(game,text):
                        send(game,b'\x37'+struct.pack('<I',quest['npc']['catalog_id']))
                        response=decoder.logical(helper,game)
                        self.assertEqual(response[:1],b'\x7a');self.assertEqual(len(response),27)
                        self.assertEqual(response[3],1);self.assertEqual(int.from_bytes(response[7:9],'little'),text)
                        return b'\x85'+response[5:7]+response[9:11]+response[4:5]+b'\0'
                    login,game=enter();initial=state();before=full()
                    send(game,struct.pack('<BHHBB',0x85,mission,0,0,0));drain(game);self.assertEqual(full(),before,'Unissued request mutated DB')
                    action=open_dialogue(game,quest['dialogue_candidates']['offer']['text_id']);send(game,action);reply=drain(game)
                    accepted=state();self.assertIsNotNone(accepted['journal']);journal=struct.unpack('<15I',bytes.fromhex(accepted['journal'][0]));self.assertIn((1<<16)|mission,journal)
                    self.assertEqual(accepted['bag'],initial['bag']);self.assertEqual(accepted['xp'],initial['xp'])
                    evidence['cases'].append({'name':'accept','action':action.hex(),'reply':[r.hex() for r in reply],'state':accepted});save()
                    game.close();login.close();time.sleep(.3);login,game=enter();self.assertEqual(state(),accepted,'Relogin changed accepted state')
                    action=open_dialogue(game,quest['dialogue_candidates']['completion']['text_id']);send(game,action);reply=drain(game)
                    completed=state();self.assertEqual(completed['xp'],initial['xp']+quest['external_historical']['reward_exp_reported'])
                    self.assertNotIn((1<<16)|mission,struct.unpack('<15I',bytes.fromhex(completed['journal'][0])))
                    item=quest['requirement']['item_key'];quantity=quest['requirement']['quantity']
                    self.assertEqual(sum(r[2] for r in initial['bag'] if r[1]==item)-sum(r[2] for r in completed['bag'] if r[1]==item),quantity)
                    evidence['cases'].append({'name':'submit','action':action.hex(),'reply':[r.hex() for r in reply],'state':completed})
                    before=full();send(game,action);drain(game);self.assertEqual(full(),before,'Submission replay changed DB')
                    evidence['cases'].append({'name':'replay','database_unchanged':True});save()
                evidence['status']='PASS'
            result['status']='PASS'
        except BaseException as error:result['error']=repr(error);result['status']='FAIL';raise
        finally:save()


if __name__=='__main__':unittest.main()
