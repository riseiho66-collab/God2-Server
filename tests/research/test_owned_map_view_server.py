"""Own-server TCP map presentation; copied disposable saves, never live data."""
from contextlib import ExitStack,closing
import json,os,select,socket,sqlite3,subprocess,tempfile,time,unittest
from pathlib import Path
import test_recovered_dual_connection_server as dual
import test_inventory_move_server as inventory
from test_current_world_ready_builder import current_world_ready_wire

ROOT=dual.ROOT
SOURCE=ROOT/'artifacts/playtests/private-owned-map-view-20260926-02'
BINARY=Path(os.environ.get('GOD2_MAP_VIEW_BINARY',ROOT/'build-town-visibility/Release/god2-server-owned-map-view.exe'))

class OwnedMapViewServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):dual.RecoveredDualConnectionServerTests.crypto_key=dual.key(ROOT)
    def test_kunlun_repeatable_owned_use_and_restart(self):self.run_case(5576,4,3)
    def test_town_repeatable_owned_use_without_quest(self):self.run_case(5569,2,4)
    def run_case(self,item,area,scene):
        helper=dual.RecoveredDualConnectionServerTests();decoder=inventory.InventoryMoveServerTests()
        with tempfile.TemporaryDirectory() as tmp,ExitStack() as lifetime:
            here=Path(tmp);database=here/'town-diagnostic-accounts.db'
            with closing(sqlite3.connect((SOURCE/'town-diagnostic-accounts.db').resolve().as_uri()+'?mode=ro',uri=True)) as original:
                with closing(sqlite3.connect(database)) as db:original.backup(db)
            config=json.loads((SOURCE/'server-config.json').read_text('utf-8'))
            config['world']['clock']['enabled']=False
            config['database']['path']=str(database);config['logging']['file']=str(here/'server.log')
            config['server']['port']=helper.unused_port();endpoint=('127.0.0.1',config['server']['port'])
            with closing(sqlite3.connect(database)) as db:
                db.execute('update diagnostic_inventory_slots set item_id=? where character_id=4 and slot=0',(item,))
                db.execute('update recovered_positions set area=?,scene=?,x=?,y=? where character_id=4',(area,scene,126 if area==4 else 88,126 if area==4 else 75));db.commit()
            cfg=here/'config.json';cfg.write_text(json.dumps(config),encoding='utf-8')
            def saved():
                with closing(sqlite3.connect(database)) as db:
                    return {name:db.execute('select * from '+name+' order by 1,2').fetchall() for name in
                        ('diagnostic_inventory_slots','character_resources','character_quest_journals','diagnostic_town_guide_progress','recovered_positions')}
            original=saved()
            def launch():
                output=lifetime.enter_context((here/'stdout.log').open('ab'))
                env=helper.environment();env['GOD2_LOG_FILE_ONLY']='1'
                process=subprocess.Popen([str(BINARY),'--config',str(cfg),'--run-for','40'],cwd=ROOT,env=env,
                    stdout=output,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
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
                game.sendall(current_world_ready_wire(identity,(4,3)));helper.silent(game)
                game.sendall(helper.frame(0x30,b'\0'));decoder.logical(helper,game)
                while select.select([game],[],[],.15)[0]:decoder.logical(helper,game)
                return game
            process=launch();game=enter()
            def use(value=item,slot=0,tail=0,extra=b''):
                game.sendall(helper.frame(0x25,value.to_bytes(2,'little')+bytes((slot,tail))+extra))
            for tail in (0,1,255):
                use(tail=tail,extra=b'\x1f\0');self.assertEqual(decoder.logical(helper,game),b'\x3f\1\0');self.assertEqual(saved(),original)
            for value,slot,extra in ((5569 if item==5576 else 5576,0,b''),(item,1,b''),(item,30,b''),(item,255,b''),
                                    (item,0,b'\x25'+item.to_bytes(2,'little')+b'\0\0'),(item,0,b'\x24\0\1')):
                use(value,slot,extra=extra)
                try:helper.silent(game)
                except AssertionError as error:raise AssertionError(f'denial {value}/{slot}/{extra.hex()}: '+(here/'server.log').read_text('utf-8',errors='replace')[-5000:]) from error
                self.assertEqual(saved(),original)
                use();self.assertEqual(decoder.logical(helper,game),b'\x3f\1\0')
            game.close();helper.stop(process)
            process=launch();game=enter();use();self.assertEqual(decoder.logical(helper,game),b'\x3f\1\0')
            self.assertEqual(saved(),original)
            log=(here/'server.log').read_text('utf-8',errors='replace')
            self.assertIn('OWNED_MAP_VIEW_READY',log);self.assertGreaterEqual(log.count('OWNED_MAP_VIEW_OPEN'),10)
if __name__=='__main__':unittest.main()
