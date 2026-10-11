"""DIAGNOSTIC_NOT_ACCEPTANCE: unchanged native login/world-tail reproduction.

Default is read-only inspection. --execute requires a private tail-trace binary;
it clones only the failed private fixture DB and reuses its closed physical client.
No guild action, fixture grant/cleanup, working-client edit, screenshot, foreground
input, process-memory write or packet injection. At most three original launches.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib
import json
from pathlib import Path
import re
import socket
import struct
import subprocess
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'artifacts/playtests/gf-20261004-01/private-native-blackbox-0078-gf-20261004-01-950'
TRACE_BUILD=ROOT/'artifacts/research/native-guild-membership-0078/tail-trace-candidate-v01/build'
IMAGE_SHA='6e8f2c09385bbeaf10313745c863471c04cb751fdb44e6040b64978bc61bdcc2'
PROFILE_SHA='755d577e22a2cbff2fa17a0c9a1e64c62f94d907c876575806e3c756fe969ede'
RESOURCE_SHA={'Data2/Patch/Comm/MultiMessage03.csvZ':'20b0636e77e1ad72eb1d98c7a82e893b45db155982dc63ba6f6f16cd8195377d',
    'Data2/Patch/Comm/MultiMessage03-gb.csvZ':'ba31e53de24ec100c6e98231bc37daeb8e2ec11c1f1a76abf53e14c7429432fd'}
REJECT='World initialization tail contract rejected'
TRACE='OWNED_PRIVATE_WORLD_TAIL_TRACE '

def require(value,message):
    if not value:raise ValueError(message)

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def read(path):return json.loads(Path(path).read_text('utf-8-sig'))
def dump(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def utc():return datetime.now(timezone.utc).isoformat()

def helpers():
    sys.path[:0]=[str(ROOT),str(ROOT/'tools/strike_lab'),str(ROOT/'artifacts/tooling/crypto-oracle-python')]
    return importlib.import_module('private_guild_formal_entry_0078_v01_20261004')

def source_inputs():
    fixture=read(SOURCE/'fixture.json');client=fixture['clients']['950']
    image=Path(client['path']).resolve();profile=Path(client['profile']).resolve()
    require(image==SOURCE/'client-root/God2.exe' and profile==Path(str(image)+'.le.config'),
        'FIXED_PRIVATE_PHYSICAL_IMAGE_REQUIRED')
    require(Path(client['physical_root']).resolve()==image.parent,'PRIVATE_PHYSICAL_ROOT_CHANGED')
    pins={str(image):IMAGE_SHA,str(profile):PROFILE_SHA}
    require(client['sha256']==IMAGE_SHA and client['profile_sha256']==PROFILE_SHA,'FAILED_FIXTURE_IMAGE_PROFILE_CHANGED')
    for relative,expected in RESOURCE_SHA.items():pins[str(image.parent/relative)]=expected
    for path,expected in pins.items():
        require(Path(path).is_file() and Path(path).stat().st_nlink==1 and sha(path)==expected,'PRIVATE_INPUT_PIN_CHANGED:'+path)
    config=read(SOURCE/'server-config.json')
    require(config['server']['host']=='127.0.0.1' and config['server']['port']==2598
        and config['server'].get('character_port',0)==0,'FIXED_PRIVATE_SERVER_TARGET_REQUIRED')
    require(Path(config['database']['path']).resolve()==SOURCE/'town-diagnostic-accounts.db','FAILED_FIXTURE_DB_TARGET_CHANGED')
    return fixture,client,config,pins

def candidate(path):
    path=Path(path).resolve()
    require(path.is_relative_to(TRACE_BUILD.resolve()) and path.name=='god2-server.exe' and path.is_file(),
        'NEW_PRIVATE_TAIL_TRACE_BUILD_REQUIRED')
    return path

def worker(args):
    h=helpers();base=h.base;psutil=h.psutil
    fixture,client,_,pins=source_inputs();image=Path(client['path']);log=args.output/'server.log'
    before=h.desktop_names();clients=[];loaders=[]
    require(before['current'].startswith('God2Lab-') and before['current']!=before['input'],'OWNED_HIDDEN_DESKTOP_REQUIRED')
    result={'classification':'DIAGNOSTIC_NOT_ACCEPTANCE','accepted':False,'attempts':[],
        'rendered_pixels_tested':False,'memory_access':'VM_READ_ONLY','started_utc':utc()}
    def save():dump(args.output/'ui-result.json',result)
    def tail(offset):return log.read_text('utf-8',errors='replace')[offset:]
    def checked(offset):
        text=tail(offset)
        if REJECT in text:raise RuntimeError('TAIL_REJECT_DETECTED')
        return text
    def close(c):
        if c.get('handle'):base.peer.kernel.CloseHandle(c.pop('handle'))
        if c['process'].is_running():
            base.peer.user.PostMessageW(c['hwnd'],0x10,0,0)
            try:c['process'].wait(timeout=4)
            except psutil.TimeoutExpired:c['process'].terminate();c['process'].wait(timeout=5)
    def launch_attempt(event):
        offset=event['log_offset'];require(sha(image)==IMAGE_SHA,'PRIVATE_CLIENT_PIN_CHANGED')
        loader=subprocess.Popen([str(base.LE),'-run',str(image),'127.0.0.1','127.0.0.1','6001','1'],cwd=image.parent,
            creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        loaders.append(loader);event['loader_pid']=loader.pid;save()
        def found():
            checked(offset)
            matches=[p for p in psutil.process_iter(['exe']) if p.info['exe'] and Path(p.info['exe']).resolve()==image.resolve()]
            require(len(matches)<=1,'DUPLICATE_PRIVATE_IMAGE');return matches[0] if matches else None
        process=h.wait_until(found,35,'PRIVATE_CLIENT_MISSING')
        require(Path(process.cwd()).resolve()==image.parent.resolve(),'PRIVATE_CLIENT_CWD_NOT_PHYSICAL_ROOT')
        c={'process':process,'identity':4,'page':950};clients.append(c);event['client_pid']=process.pid;save()
        c['hwnd']=h.wait_until(lambda:base.peer.window_for(process.pid),35,'PRIVATE_WINDOW_MISSING')
        # Exact original formal-helper launch timings/events, not a timing repair.
        time.sleep(12);h.click(c['hwnd'],512,464);time.sleep(4)
        bound='RECOVERED_ACCOUNT_BOUND account_id=4';old=log.read_text('utf-8',errors='replace').count(bound)
        h.click(c['hwnd'],437,232);h.type_ascii(c['hwnd'],'codexslow')
        h.click(c['hwnd'],437,263);h.type_ascii(c['hwnd'],'labtest2345');h.click(c['hwnd'],452,304)
        h.wait_until(lambda:checked(offset).count(bound)>0 and log.read_text('utf-8',errors='replace').count(bound)>old,35,'LOGIN_FAILED')
        time.sleep(4);h.click(c['hwnd'],330,145);h.click(c['hwnd'],452,413);time.sleep(4)
        h.click(c['hwnd'],330,150);h.click(c['hwnd'],452,376);time.sleep(4);h.click(c['hwnd'],452,370)
        c['handle']=base.peer.kernel.OpenProcess(0x1010,False,process.pid);require(c['handle'],'VM_READ_HANDLE_REQUIRED')
        def observed_ui():
            checked(offset)
            try:return base.peer.find_ui(c['handle'],4,(0,3,4))
            except RuntimeError as error:
                if str(error)=='UI_STRUCTURE_MATCHES_4_0':return None
                raise
        c['ui']=h.wait_until(observed_ui,12,'NATIVE_UI_BASE_MISSING');event['ui_base']=hex(c['ui']);save()
        language,sub=struct.unpack('<HH',base.peer.exact(c['handle'],0x59dfd8,4))
        require(language==4 and sub!=2,'PRIVATE_LOCALE_MISMATCH')
        def world_ready():
            text=checked(offset)
            matches=list(re.finditer(r'OWNED_WORLD_SNAPSHOT_RESTORED session_id=(\d+) character_id=4 saved_player=true[^\r\n]*',text))
            if not matches:return None
            match=matches[-1];session=int(match.group(1));lines=text[match.end():].splitlines()
            completed=next((line for line in lines if 'session_id='+str(session)+' RECOVERED_WORLD_BATCH_HANDLED ' in line),None)
            return {'identity':4,'session':session,'snapshot':match.group(0),'completed_batch':completed} if completed else None
        event['world_readiness']=h.wait_until(world_ready,12,'OWNED_WORLD_PROJECTION_NOT_COMPLETED')
        event['world_ready']=True
        return c
    try:
        require(not any(key in h.os.environ for key in h.LAB_ENV),'DIAGNOSTIC_LAB_ENV_MUST_BE_ABSENT')
        for number in range(1,args.attempts+1):
            event={'attempt':number,'started_utc':utc(),'identity':4,'slot':0,'ui_base':None,'world_ready':False,
                'log_offset':len(log.read_text('utf-8',errors='replace'))};result['attempts'].append(event);save()
            c=None
            try:c=launch_attempt(event)
            except BaseException as error:event.update(error=str(error),traceback=traceback.format_exc())
            finally:
                for opened in reversed(clients):
                    if opened.get('handle') or opened['process'].is_running():
                        try:close(opened)
                        except BaseException as error:result.setdefault('cleanup_errors',[]).append(str(error))
                event['finished_utc']=utc();text=tail(event['log_offset']);event['server_log_tail']=text
                event['tail_rejected']=REJECT in text;event['trace_lines']=[line for line in text.splitlines() if TRACE in line]
                event['session_ids']=sorted({int(value) for value in re.findall(r'session_id=(\d+)',text)})
                save()
            if event.get('error') or event['tail_rejected']:break
        result['diagnostic_collected']=bool(result['attempts'])
    except BaseException as error:result.update(error=str(error),traceback=traceback.format_exc())
    finally:
        for c in reversed(clients):
            try:close(c)
            except BaseException as error:result.setdefault('cleanup_errors',[]).append(str(error))
        for loader in loaders:
            if loader.poll() is None:loader.terminate();loader.wait(timeout=5)
        result['desktop_before']=before;result['desktop_after']=h.desktop_names()
        result['desktop_unchanged']=before==result['desktop_after']
        result['all_clients_closed']=all(not c['process'].is_running() for c in clients)
        result['all_loaders_closed']=all(loader.poll() is not None for loader in loaders)
        result['private_pins_unchanged']=all(sha(path)==expected for path,expected in pins.items())
        result['diagnostic_complete']=bool(result.get('diagnostic_collected') and result['desktop_unchanged']
            and result['all_clients_closed'] and result['all_loaders_closed'] and result['private_pins_unchanged']
            and not result.get('cleanup_errors'));save()
    return 0 if result['diagnostic_complete'] else 1

def execute(args):
    h=helpers();base=h.base;psutil=h.psutil
    server=candidate(args.server);fixture,client,original,pins=source_inputs();image=Path(client['path']).resolve()
    require(args.output is not None,'NEW_DIAGNOSTIC_OUTPUT_REQUIRED');args.output=args.output.resolve()
    require(args.output.is_relative_to(ROOT/'artifacts/playtests') and args.output.name.startswith('private-native-blackbox-tail-')
        and not args.output.exists(),'NEW_PRIVATE_TAIL_OUTPUT_REQUIRED')
    require(not any(p.info['exe'] and Path(p.info['exe']).resolve()==image for p in psutil.process_iter(['exe'])),
        'REUSED_PRIVATE_CLIENT_MUST_BE_CLOSED')
    require(sha(base.RUNNER)==base.RUNNER_SHA and sha(base.LIVE)==base.CLIENT_SHA,'EXISTING_RUNNER_OR_WORKING_CLIENT_PIN_CHANGED')
    before=h.desktop_names();foreground=int(base.peer.user.GetForegroundWindow() or 0);protected=h.protected()
    files,databases=h.guard_sources(protected)
    files.update({'diagnostic_source_fixture':SOURCE/'fixture.json','diagnostic_source_config':SOURCE/'server-config.json',
        'diagnostic_driver':Path(__file__),'diagnostic_candidate':server})
    files.update({path:Path(path) for path in pins})
    databases.add(str(SOURCE/'town-diagnostic-accounts.db'))
    files_before={name:sha(path) for name,path in files.items()};db_before={path:h.snapshots(Path(path)) for path in databases}
    result={'classification':'DIAGNOSTIC_NOT_ACCEPTANCE','accepted':False,'started_utc':utc(),
        'candidate_path':str(server),'candidate_sha256':sha(server),'source_path':str(SOURCE),'max_attempts':args.attempts}
    process=runner=None;args.output.mkdir(parents=True,exist_ok=False)
    try:
        from tools.operations.owned_guild_release_v02_20261004 import backup_new
        database=args.output/'town-diagnostic-accounts.db';backup_new(SOURCE/'town-diagnostic-accounts.db',database)
        config=deepcopy(original);config['database']['path']=str(database);config['logging']['file']=str(args.output/'server.log')
        dump(args.output/'server-config.json',config);dump(args.output/'fixture.json',fixture)
        result['clone_before']=h.snapshots(database)
        with socket.socket() as probe:require(probe.connect_ex(('127.0.0.1',base.PORT))!=0,'PRIVATE_PORT_ALREADY_USED')
        with (args.output/'stdout.log').open('xb') as out,(args.output/'runner.log').open('xb') as runnerlog:
            process=subprocess.Popen([str(server),'--config',str(args.output/'server-config.json'),'--run-for','960'],
                cwd=ROOT,env=h.env_formal(),stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            result['server_pid']=process.pid
            def listening():
                require(process.poll() is None,'PRIVATE_SERVER_EXITED')
                with socket.socket() as probe:return probe.connect_ex(('127.0.0.1',base.PORT))==0
            h.wait_until(listening,15,'PRIVATE_SERVER_NOT_LISTENING')
            require(not any(key in psutil.Process(process.pid).environ() for key in h.LAB_ENV),'DIAGNOSTIC_SERVER_LAB_ENV_PRESENT')
            runner=subprocess.Popen([str(base.RUNNER),sys.executable,'-X','utf8','-B',str(Path(__file__).resolve()),
                '--worker','--output',str(args.output),'--attempts',str(args.attempts)],cwd=ROOT,env=h.env_formal(),
                stdout=runnerlog,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            result['runner_pid']=runner.pid;result['runner_exit']=runner.wait(timeout=600)
            result['ui']=read(args.output/'ui-result.json');result['clone_after']=h.snapshots(database)
    except BaseException as error:result.update(error=str(error),traceback=traceback.format_exc())
    finally:
        for own in (runner,process):
            if own is not None and own.poll() is None:
                children=psutil.Process(own.pid).children(recursive=True)
                for child in reversed(children):
                    try:child.terminate()
                    except psutil.NoSuchProcess:pass
                own.terminate();own.wait(timeout=5);_,alive=psutil.wait_procs(children,timeout=5)
                for child in alive:child.kill();child.wait(timeout=5)
        # Source input was closed before launch; only this exact disposable image
        # may be reaped if a loader escaped the tracked child process tree.
        for private in psutil.process_iter(['exe']):
            if private.info['exe'] and Path(private.info['exe']).resolve()==image:
                try:private.terminate();private.wait(timeout=5)
                except psutil.NoSuchProcess:pass
        result['files_before']=files_before;result['files_after']={name:sha(path) for name,path in files.items()}
        result['protected_files_unchanged']=result['files_before']==result['files_after']
        result['protected_DB_before']=db_before;result['protected_DB_after']={path:h.snapshots(Path(path)) for path in databases}
        result['protected_DB_exact']=result['protected_DB_before']==result['protected_DB_after']
        current=h.protected();result['protected_processes_exact']={pid:current[pid] for pid in protected if pid in current}==protected
        result['desktop_unchanged']=before==h.desktop_names();result['foreground_unchanged']=foreground==int(base.peer.user.GetForegroundWindow() or 0)
        result['all_owned_processes_closed']=(runner is None or runner.poll() is not None) and (process is None or process.poll() is not None)
        result['all_private_images_closed']=not any(p.info['exe'] and Path(p.info['exe']).resolve()==image for p in psutil.process_iter(['exe']))
        with socket.socket() as probe:result['exclusive_2598_released']=probe.connect_ex(('127.0.0.1',base.PORT))!=0
        result['finished_utc']=utc();result['diagnostic_complete']=bool(result.get('runner_exit')==0 and result.get('ui',{}).get('diagnostic_complete')
            and all(result[key] for key in ('protected_files_unchanged','protected_DB_exact','protected_processes_exact',
                'desktop_unchanged','foreground_unchanged','all_owned_processes_closed','all_private_images_closed','exclusive_2598_released')))
        dump(args.output/'run-result.json',result)
    return 0 if result['diagnostic_complete'] else 1

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--server',type=Path)
    parser.add_argument('--output',type=Path);parser.add_argument('--attempts',type=int,choices=(1,2,3),default=3)
    parser.add_argument('--execute',action='store_true');parser.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker:
        require(args.output is not None and args.output.resolve().name.startswith('private-native-blackbox-tail-'),'PRIVATE_WORKER_OUTPUT_REQUIRED')
        args.output=args.output.resolve();return worker(args)
    if not args.execute:
        _,_,config,pins=source_inputs()
        print(json.dumps({'classification':'DIAGNOSTIC_NOT_ACCEPTANCE','read_only':True,'server_or_UI_started':False,
            'source_pins':pins,'source_config_sha256':sha(SOURCE/'server-config.json'),'source_server':config['server'],
            'trace_candidate':None if args.server is None else str(candidate(args.server))},ensure_ascii=False,indent=2));return 0
    require(args.server is not None,'EXPLICIT_TRACE_SERVER_REQUIRED');return execute(args)

if __name__=='__main__':raise SystemExit(main())
