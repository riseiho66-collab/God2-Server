"""Isolated two-client qualification of owner-requested streamer cosmetics."""
import argparse
import json
from pathlib import Path
import sqlite3
import struct
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import private_chat_after_scene_20260927 as base
shared=base.shared
MANIFEST=Path(r'C:\Users\risei\Desktop\God2\Launcher-src\launcher-native\build\Release\x86\StreamerStyle\candidate.json')
manifest=json.loads(MANIFEST.read_text('utf-8'))
shared.fixture.CLIENT=Path(manifest['candidate'])
styles={2:1,3:2}

def prepare(args):
    candidate=shared.fixture.CLIENT
    base.require(shared.fixture.sha(candidate)==manifest['candidate_sha256'],'STREAMER_CLIENT_PIN')
    try:
        shared.fixture.CLIENT=candidate.parent/'God2-current-lab-2598.exe'
        base.prepare(args)
    finally:shared.fixture.CLIENT=candidate
    config_path=args.output/'server-config.json'
    config=json.loads(config_path.read_text('utf-8'))
    config.setdefault('development',{})['streamer_privileges']=True
    shared.dump(config_path,config)
    subprocess.run([str(args.server_candidate),'--config',str(config_path),'--migrate-only'],check=True,stdout=subprocess.DEVNULL)
    with sqlite3.connect(config['database']['path']) as db:
        db.execute('UPDATE recovered_characters SET streamer_privilege=1 WHERE id=2')
        db.execute('UPDATE recovered_characters SET streamer_privilege=2 WHERE id=3')
    shared.dump(args.output/'streamer-candidate.json',manifest)

def observe(client,recipients,evidence):
    style=styles[client['identity']]
    expected=((0xa0+style)<<24 | {1:0x4040ff,2:0xf37b08,3:0xc0ff}[style]) if style else 0xffffff
    for peer in recipients:
        address=struct.unpack('<I',shared.exact(peer['handle'],peer['ui']+0x39de8,4))[0]
        raw=shared.exact(peer['handle'],address,0x67f4)
        count,oldest,nxt=struct.unpack_from('<3I',raw,0x67e8)
        matches=[]
        for i in ((oldest+n)%200 for n in range(count)):
            text=raw[i*128:(i+1)*128].split(b'\0')[0]
            if evidence['text'].encode('cp'+str(peer.get('codepage',950))) in text:
                color=struct.unpack_from('<I',raw,0x64c8+i*4)[0]
                matches.append({'text_hex':text.hex(),'color':hex(color)})
                base.require(color==expected,'STREAMER_RING_COLOR_MISMATCH')
                base.require((b'/c0' in text and b'/c9' in text) if style else (b'/c0' not in text and b'/c9' not in text),'STREAMER_NAME_BODY_SPLIT_MISSING')
        base.require(matches,'STREAMER_ROW_MISSING')
        evidence.setdefault('streamer_rows',{})[str(peer['identity'])]=matches

def final(clients,result,args,talk):
    from window_snapshot import capture
    result['preview_red']=talk(clients[0],'主播1 中文123',clients)
    result['preview_blue']=talk(clients[1],'主播2 中文456',clients)
    result['screenshots']=[]
    for client in clients:
        result['screenshots']+=capture(client['process'].pid,args.output)
    result['streamer_diagnostics']={}
    for client in clients:
        def qualified():
            values=struct.unpack('<16I',shared.exact(client['handle'],manifest['module_exports']['StreamerDiagnostics'],64))
            return values if values[0] and values[1] and values[2] and values[9] and values[10] and values[12] else None
        values=base.wait_until(qualified,10,'STREAMER_RENDER_NOT_OBSERVED')
        result['streamer_diagnostics'][str(client['identity'])]=values
        base.require(values[13]>=700 and values[14]<700,'ACTUAL_GDI_FONT_WEIGHT_MISMATCH')
    database=args.output/'town-diagnostic-accounts.db'
    try:
        for style in (3,0):
            with sqlite3.connect(database) as db:db.execute('UPDATE recovered_characters SET streamer_privilege=? WHERE id=3',(style,))
            styles[3]=style
            result['style_'+str(style)]=talk(clients[1],'主播3 中文789' if style==3 else '普通玩家 中文000',clients)
            if globals().get('HEAD_OBSERVER'):result['head_style_'+str(style)]=HEAD_OBSERVER(clients,{2:1,3:style})
            base.time.sleep(2)
            for peer in clients:
                pictures=capture(peer['process'].pid,args.output)
                result['screenshots']+=pictures
                result.setdefault('style_screenshots',{}).setdefault(str(style),{})[str(peer['identity'])]=pictures
        for client in clients:
            values=struct.unpack('<16I',shared.exact(client['handle'],manifest['module_exports']['StreamerDiagnostics'],64))
            result.setdefault('all_style_diagnostics',{})[str(client['identity'])]=values
            base.require(values[3] and values[11],'TIKTOK_DRAW_MISSING')
        # Bubble lifetime expires naturally; capture unobstructed overhead labels.
        base.time.sleep(12)
        result['head_screenshots']=[]
        for client in clients:result['head_screenshots']+=capture(client['process'].pid,args.output)
    finally:
        with sqlite3.connect(database) as db:db.execute('UPDATE recovered_characters SET streamer_privilege=2 WHERE id=3')

def failure(clients,result,args):
    from window_snapshot import capture
    result['failure_screenshots']=[]
    for client in clients:
        result['failure_screenshots']+=capture(client['process'].pid,args.output)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--server-candidate',type=Path)
    parser.add_argument('--worker',action='store_true')
    parser.add_argument('--prepare-only',action='store_true')
    args=parser.parse_args()
    if args.worker:
        base.CHAT_OBSERVER=observe;base.FINAL_OBSERVER=final;base.FAILURE_OBSERVER=failure
        raise SystemExit(base.worker(args))
    shared.prepare=prepare;shared.__file__=str(Path(__file__).resolve())
    raise SystemExit(shared.owner(args))
