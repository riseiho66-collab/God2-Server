"""Real Application loopback test with disposable saved role and synthetic auth.

No Windows input, client memory injection or formal database writes. This is a
wire peer, not live-client visual acceptance. The actual Application executable
performs authentication, world entry, battle admission, command and receipt.
"""
from pathlib import Path
import hashlib, json, secrets, socket, sqlite3, struct, sys, tempfile, time

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tests/research'),str(ROOT)]
import test_recovered_dual_connection_server as dual
from test_current_world_ready_builder import current_world_ready_wire
from test_same_session_battle_supply_server import SameSessionBattleSupplyServerTests as Wire

SOURCE=ROOT/'artifacts/playtests/private-shunying-manual-thousand-bulls-20260930-01'

def main():
    recording='--recording' in sys.argv
    dual.RecoveredDualConnectionServerTests.setUpClass()
    h=dual.RecoveredDualConnectionServerTests()
    out=Path(tempfile.mkdtemp(prefix='private-shunying-manual-bull-blackbox-',dir=ROOT/'artifacts/playtests'))
    database=out/'diagnostic-accounts.db'
    source_db=SOURCE/'diagnostic-accounts.db'
    before=hashlib.sha256(source_db.read_bytes()).hexdigest()
    with sqlite3.connect(source_db.resolve().as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(database) as dst:
        src.backup(dst)
    # A synthetic credential is assigned ONLY in this new disposable copy.
    with sqlite3.connect(database) as db:
        owner,token=db.execute('SELECT account_id,slot FROM recovered_characters WHERE id=6').fetchone()
        salt=secrets.token_bytes(16)
        digest=hashlib.pbkdf2_hmac('sha256',dual.PASSWORD,salt,600000).hex()
        db.execute('UPDATE accounts SET username=?,password_hash=? WHERE id=?',
            ('god2-bytes:'+dual.OWNER.hex(),'god2$pbkdf2-sha256$v1$600000$'+salt.hex()+'$'+digest,owner))
        db.commit()
    config=json.loads((SOURCE/'server-config.json').read_text(encoding='utf-8'))
    config['development']['diagnostic_recording_fixed_damage']=recording
    config['server'].update(port=h.unused_port(),character_port=0)
    config['database']['path']=str(database)
    config['logging']['file']=str(out/'server.log')
    endpoint=('127.0.0.1',config['server']['port'])
    report={'scope':'real Application TCP; synthetic authentication; no rendered-client acceptance',
        'accepted':False,'source_db_unchanged':False,'stages':[],'cast_frames':[]}
    def stage(name):
        report['stages'].append(name);print(name,flush=True)
    def drain(game):
        frames=[]
        while True:
            game.settimeout(.3)
            try: frames.append(Wire.logical(h,game))
            except socket.timeout: break
        game.settimeout(3)
        return frames
    def command(kind,enemy_mask=0,friendly_mask=0,skill=150):
        b=bytearray(16);b[0]=2;b[1]=kind
        struct.pack_into('<HH',b,4,friendly_mask,enemy_mask)
        if kind==3:b[12]=skill
        return h.frame(0x35,b)
    with (out/'stdout.log').open('wb') as log:
        process=h.launch(out,config,log,run_for=90)
        try:
            deadline=time.monotonic()+8
            while True:
                try:
                    with socket.create_connection(endpoint,.2):break
                except OSError:
                    if process.poll() is not None or time.monotonic()>deadline:raise RuntimeError('Listener failed')
                    time.sleep(.05)
            stage('actual Application listening on private ephemeral port')
            with h.connect(endpoint) as login:
                game_endpoint=h.login(login,fragmented=True)
                listing=h.list_characters(login)
                assert listing[3]>=1
                stage('L authentication and owned character listing accepted')
                with h.connect(game_endpoint) as game:
                    h.game_ready(game,fragmented=True)
                    game.sendall(h.frame(0x1a,dual.selection_payload(token)))
                    selected=h.read_frame(game,2,26);entry=h.read_frame(game,0x2a,40)
                    assert int.from_bytes(entry[3:5],'little')&0x3fff==6
                    drain(game)
                    game.sendall(current_world_ready_wire(6));drain(game)
                    stage('G authentication, selection and native world-ready accepted')
                    game.sendall(h.frame(0x30,b'\0'))
                    entry_frames=drain(game)
                    assert any(b'\x82' in f for f in entry_frames),[f.hex() for f in entry_frames]
                    if recording:
                        for skill in (126,150):assert any(bytes((0x34,102,0,skill)) in f for f in entry_frames)
                    game.sendall(h.frame(0x36,bytes(8)))
                    participants=drain(game)
                    assert any(b'\x87\x96\x80' in f for f in participants)
                    if recording:
                        assert any(b'\x87\x7e\x80' in f for f in participants)
                        for slot in range(14,28):
                            hp=bytes((0x86,0,slot,0,0))+struct.pack('<II',99999,99999)
                            assert any(hp in f for f in participants),('monster HP',slot)
                    stage('battle admission and skill150 grant accepted')
                    game.sendall(command(0x0b));drain(game)
                    previous_mp=9999
                    if recording:
                        remaining=[99999]*14
                        # Switch F1/F2 and basic attacks, then cross the lethal boundary.
                        sequence=[(1,0,1),(3,126,7),(3,150,0x3fff),(3,150,0x3fff),(1,0,1),(3,150,0x3fff)]
                        for cycle,(kind,skill,mask) in enumerate(sequence):
                            targets=[i for i,hp in enumerate(remaining) if hp and mask&(1<<i)]
                            if skill==126:
                                records=bytearray()
                                for n,target in enumerate(targets):
                                    b=bytearray(17);b[0:3]=bytes((0x35,2,0x83 if n+1<len(targets) else 3))
                                    struct.pack_into('<H',b,7,1<<target);b[13]=126;records.extend(b)
                                request=h.frame(0x35,records[1:])
                            else:request=command(kind,enemy_mask=mask,skill=skill)
                            game.sendall(request);frames=drain(game)
                            herd=skill==150
                            cost=100 if herd else 20 if skill==126 else 0
                            previous_mp-=cost
                            damage=next(f for f in frames if f.startswith(b'\x86\x01\x02')) if herd else next(f for f in frames if f.startswith(bytes((0x83,3 if skill else 1,2))))
                            start=17 if herd else 0;stride=15 if herd else 32
                            assert len(damage)==start+len(targets)*stride+121
                            if herd:assert int.from_bytes(damage[9:13],'little')==previous_mp
                            for n,target in enumerate(targets):
                                r=damage[start+n*stride:start+n*stride+15]
                                assert struct.unpack_from('<h',r,9)[0]==-9999
                                assert int.from_bytes(r[7:9],'little')==1<<target
                                remaining[target]=max(0,remaining[target]-(39996 if herd else 9999))
                                if not herd:
                                    hp=damage[start+n*stride+15:start+n*stride+32]
                                    assert hp[:3]==bytes((0x86,0,14+target))
                                    assert int.from_bytes(hp[5:9],'little')==99999
                                    assert int.from_bytes(hp[9:13],'little')==remaining[target]
                            report['cast_frames'].append({'cycle':cycle,'skill':skill,'display_per_hit':9999,'remaining_hp':remaining.copy(),'wire':damage.hex()})
                            game.sendall(command(0x0b,enemy_mask=0x3fff));receipt=drain(game)
                            if cycle<len(sequence)-1:assert any(len(f)==138 and f[121:126]==b'\x86\x05\0\x01\x02' for f in receipt)
                            stage(f'recording cycle{cycle+1}: skill{skill},9999 display and authoritative HP verified')
                        assert remaining==[0]*14
                        report['accepted']=True
                        report['recording']=True
                        return
                    for cycle in range(2):
                        request=command(3,enemy_mask=0x3fff)
                        game.sendall(request[:7]);h.silent(game)
                        game.sendall(request[7:])
                        frames=drain(game)
                        damage=next(f for f in frames if len(f)>=17 and f[:3]==b'\x86\x01\x02')
                        assert len(damage)==17+14*15+121,len(damage)
                        mp=int.from_bytes(damage[9:13],'little');assert mp==previous_mp-100,(mp,previous_mp)
                        previous_mp=mp
                        losses=[]
                        for n in range(14):
                            p=17+n*15;r=damage[p:p+15]
                            assert r[0:3]==b'\x83\x03\x02' and r[11:13]==b'\x96\0'
                            assert int.from_bytes(r[7:9],'little')==1<<n
                            losses.append(-struct.unpack_from('<h',r,9)[0])
                        assert losses==[6647 if cycle==0 else 3353]*14,losses
                        assert damage[-121]==0x88
                        report['cast_frames'].append({'cycle':cycle,'received_decoded_logical':damage.hex(),'mp':mp,'losses':losses})
                        game.sendall(command(0x0b,enemy_mask=0x3fff))
                        receipt=drain(game)
                        if cycle==0:assert any(len(f)==138 and f[0]==0x88 and f[121:126]==b'\x86\x05\0\x01\x02' for f in receipt),[f.hex() for f in receipt]
                        stage(f'cast {cycle+1}:14 targets,100MP once,correct physical loss and receipt')
                    assert process.poll() is None
                    report['accepted']=True
        except BaseException as exc:
            report['error']=type(exc).__name__+': '+str(exc)
            raise
        finally:
            h.stop(process)
            report['source_db_unchanged']=hashlib.sha256(source_db.read_bytes()).hexdigest()==before
            (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
            print('Evidence: '+str(out/'result.json'),flush=True)
    assert report['source_db_unchanged']
    print('PASS real Application authentication/world/battle/two-cast TCP flow')

if __name__=='__main__':main()
