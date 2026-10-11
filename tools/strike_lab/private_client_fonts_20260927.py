"""Two language instances on a hidden desktop; native font and chat acceptance."""
import argparse,json,os,sqlite3,struct,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import psutil
import private_streamer_style_20260927 as style
base=style.base;shared=style.shared
FONT_MANIFEST=Path(r'C:\Users\risei\Desktop\God2\Launcher-src\launcher-native\build\Release\x86\ClientFonts\candidate.json')
font=json.loads(FONT_MANIFEST.read_text('utf-8'))
shared.fixture.CLIENT=Path(font['candidate'])
shared.fixture.CURRENT_CLIENT_SHA=font.get('deployment_base_sha256',font['source_sha256'])
PORT_COPY=shared.fixture.CLIENT.parent/('God2-font-base-'+shared.fixture.CURRENT_CLIENT_SHA[:12]+'-lab-2598.exe')

def prepare(args):
    shared.fixture.CLIENT=PORT_COPY
    try:base.prepare(args)
    finally:shared.fixture.CLIENT=Path(font['candidate'])
    shared.dump(args.output/'font-candidate.json',font)

original_popen=subprocess.Popen
launch_count=0
class OwnedProcess:
    def __init__(self,pid):self.pid=pid;self.process=psutil.Process(pid)
    def poll(self):
        try:return self.process.wait(timeout=0)
        except psutil.TimeoutExpired:return None
    def wait(self,timeout=None):
        try:return self.process.wait(timeout=timeout)
        except psutil.TimeoutExpired:raise subprocess.TimeoutExpired('owned font client',timeout)
    def terminate(self):self.process.terminate()
    def kill(self):self.process.kill()

def launch(command,*args,**kwargs):
    global launch_count
    if Path(command[0]).resolve()!=shared.fixture.CLIENT.resolve():return original_popen(command,*args,**kwargs)
    language='zh-TW' if launch_count==0 else 'zh-CN';launch_count+=1
    profile=Path(str(shared.fixture.CLIENT)+'.le.config')
    profile.write_text('<LEConfig><Profiles><Profile Name="God2 font qualification" Guid="9548b642-f82c-4883-a523-425904744e6f" MainMenu="false"><Parameter></Parameter><Location>'+language+'</Location><Timezone>Taipei Standard Time</Timezone><RunAsAdmin>false</RunAsAdmin><RedirectRegistry>false</RedirectRegistry><IsAdvancedRedirection>false</IsAdvancedRedirection><RunWithSuspend>false</RunWithSuspend></Profile></Profiles></LEConfig>',encoding='utf-8')
    before={p.pid for p in psutil.process_iter()}
    loader=original_popen([str(shared.fixture.CLIENT.parent/'compat-tools/LocaleEmulator/LEProc.exe'),'-run',*command],*args,**kwargs)
    def child():
        matches=[]
        for p in psutil.process_iter(['pid','exe']):
            if p.pid not in before and p.info['exe'] and Path(p.info['exe'])==shared.fixture.CLIENT:matches.append(p.pid)
        base.require(len(matches)<=1,'AMBIGUOUS_OWNED_FONT_PROCESS')
        return matches[0] if matches else None
    try:return OwnedProcess(base.wait_until(child,20,'LOCALE_CLIENT_NOT_STARTED'))
    finally:
        try:loader.wait(timeout=10)
        except subprocess.TimeoutExpired:loader.terminate();loader.wait(timeout=5)

def head_rows(client,identity):
    handle=client['handle'];role=struct.unpack('<I',shared.exact(handle,client['ui']+0x86888,4))[0]-0x90
    world=role-0x1539683c
    if identity==client['identity']:
        pool=world+0x39c;renderer=struct.unpack('<I',shared.exact(handle,world+0x1539ad80,4))[0]
    else:
        actor=shared.remote(handle,client['ui'],identity)
        if not actor:return None
        pool=world+0xaba32e0;renderer=actor['renderer']
    if not 0<=renderer<4096:return None
    graphic=struct.unpack('<H',shared.exact(handle,pool+renderer*0xa7e0+0x28,2))[0]
    if graphic>=4096:return None
    objects=struct.unpack('<I',shared.exact(handle,pool+4,4))[0]
    graph=struct.unpack('<I',shared.exact(handle,objects+4,4))[0]
    group=struct.unpack('<H',shared.exact(handle,objects+graphic*0x290+0x1e,2))[0]
    if group>=5000:return None
    cells=struct.unpack('<6h',shared.exact(handle,graph+group*200+0x1264,12))
    if cells[3]<0:return None
    row=shared.exact(handle,graph+0xf66e4+cells[3]*140,140);count=row[4]>>2
    markers=[list(row[140-count*2+i*2:142-count*2+i*2]) for i in range(count)]
    return {'renderer':renderer,'pool':hex(pool),'cell':cells[3],'row':row.hex(),'badge_ids':[b for a,b in markers if a&128 and b>=253]}

def check_heads(clients,expected):
    result={}
    for client in clients:
        for identity,style_id in expected.items():
            def ready():
                row=head_rows(client,identity)
                return row if row and row['badge_ids']==([252+style_id] if style_id else []) else None
            result[f"{client['identity']}_sees_{identity}"]=base.wait_until(ready,8,'OWN_OR_PEER_HEAD_BADGE_MISSING')
    return result

def final(clients,result,args,talk):
    result['head_badges_before_chat']=check_heads(clients,{2:1,3:2})
    result['login_head_badges']={str(c['identity']):c['login_head_badge'] for c in clients}
    result['login_head_screenshots']={str(c['identity']):c['login_head_screenshots'] for c in clients}
    result['name_rows']={}
    for client in clients:
        handle=client['handle'];role=struct.unpack('<I',shared.exact(handle,client['ui']+0x86888,4))[0]-0x90
        world=role-0x1539683c;pool=world+0xaba32e0
        objects=struct.unpack('<I',shared.exact(handle,pool+4,4))[0]
        graph=struct.unpack('<I',shared.exact(handle,objects+4,4))[0]
        rows=shared.exact(handle,graph+0xf66e4,512*0x8c)
        actors=[]
        for identity in (2,3):
            actor=shared.remote(handle,client['ui'],identity)
            if actor and 0<=actor['renderer']<4096:
                node=pool+actor['renderer']*0xa7e0
                actor['node_raw']=shared.exact(handle,node,0xc0).hex()
                graphic=struct.unpack_from('<H',bytes.fromhex(actor['node_raw']),0x28)[0]
                if graphic<4096:
                    group=struct.unpack('<H',shared.exact(handle,objects+graphic*0x290+0x1e,2))[0]
                    actor['group']=group
                    if group<5000:
                        cells=struct.unpack('<6h',shared.exact(handle,graph+group*200+0x1264,12))
                        actor['name_cells']=[{'cell':cell,'raw':shared.exact(handle,graph+0xf66e4+cell*140,140).hex()} for cell in cells if cell>=0]
                actors.append(actor)
        result['name_rows'][str(client['identity'])]={'graph':hex(graph),'actors':actors,'rows':[{'index':i,'raw':rows[i*140:(i+1)*140].hex()} for i in range(512) if b'test' in rows[i*140+12:(i+1)*140]]}
    shared.dump(args.output/'ui-result.json',result)
    result['native_fonts']={}
    for client in clients:
        diagnostic=struct.unpack('<8I',shared.exact(client['handle'],font['exports']['ClientFontDiagnostics'],32))
        face=shared.exact(client['handle'],font['exports']['ClientFontFace'],64).decode('utf-16-le').split('\0')[0]
        expected=(950,('Microsoft JhengHei','微軟正黑體')) if client['identity']==2 else (936,('Microsoft YaHei','微软雅黑','微軟雅黑'))
        result['native_fonts'][str(client['identity'])]={'codepage':diagnostic[0],'selected_face':face,'weight':diagnostic[2],'height':diagnostic[3],'counters':diagnostic}
        base.require(diagnostic[0]==expected[0] and face in expected[1],'FONT_OR_LANGUAGE_MISMATCH')
        base.require(diagnostic[6]==0,'FONT_CREATION_FAILED')
        base.require(diagnostic[2]<700,'ORDINARY_FONT_BECAME_BOLD')
        dimensions=struct.unpack('<4i',shared.exact(client['handle'],font['exports']['ClientFontDiagnostics']+32,16))
        result['native_fonts'][str(client['identity'])]['dimensions']={'original_width':dimensions[0],'original_height':dimensions[1],'new_width':dimensions[2],'new_height':dimensions[3]}
        base.require(dimensions[2]==0 and dimensions[3]<0,'NATURAL_FONT_PROPORTIONS_MISSING')
    result['traditional_chinese_chat']=talk(clients[0],'中文123',clients)
    result['simplified_chinese_chat']=talk(clients[1],'中文456',clients)
    style.final(clients,result,args,talk)

def login_observe(client):
    client['codepage']=950 if client['identity']==2 else 936
    client['login_head_badge']=check_heads([client],{client['identity']:1 if client['identity']==2 else 2})
    from window_snapshot import capture
    client['login_head_screenshots']=capture(client['process'].pid,args.output)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--server-candidate',type=Path);p.add_argument('--worker',action='store_true');p.add_argument('--prepare-only',action='store_true');args=p.parse_args()
    if args.worker:
        subprocess.Popen=launch;base.CHAT_OBSERVER=style.observe;base.FINAL_OBSERVER=final;base.FAILURE_OBSERVER=style.failure;base.LOGIN_OBSERVER=login_observe;style.HEAD_OBSERVER=check_heads
        raise SystemExit(base.worker(args))
    raw=bytearray(shared.fixture.LIVE_CLIENT.read_bytes());at=raw.index(bytes.fromhex('68 20 0a 00 00 68 9c 47 5b 00'));struct.pack_into('<I',raw,at+1,2598)
    if PORT_COPY.exists():base.require(PORT_COPY.read_bytes()==raw,'PORT_COPY_DRIFT')
    else:PORT_COPY.write_bytes(raw)
    base.require(shared.fixture.sha(shared.fixture.CLIENT)==font['candidate_sha256'],'FONT_CANDIDATE_DRIFT')
    shared.prepare=prepare;shared.__file__=str(Path(__file__).resolve())
    raise SystemExit(shared.owner(args))
