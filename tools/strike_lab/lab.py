"""Small native frontends share this bounded, evidence-preserving lab backend."""
import argparse
import configparser
from contextlib import contextmanager
import ctypes
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import socket
import shutil
import sys
import time

HOME = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HOME / 'tools/research'))
CLIENT = HOME / 'artifacts/capture_work/host-20260918-1430/client'
RUNS = HOME / 'artifacts/probe-runs'
PROFILES = ('PROFILE_DIRECT_DEBUG', 'PROFILE_LAUNCHER_EQUIVALENT', 'PROFILE_STATICALLY_RECONSTRUCTED_STARTUP')


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@contextmanager
def profile_context(profile, root, run):
    settings = {
        root / 'config/display.settings': b'# God2 Classic Launcher display settings.\nFormat=God2ClassicDisplaySettingsV1\nWindowed=true\nResolution=800x600\nWidth=800\nHeight=600\n',
        root / 'ctserver.ini': ''.join(f'[serversarea{i}]\r\nservercount=1\r\nserver1_name=God2 Classic\r\nserver1_ip=127.0.0.1\r\n' + ('\r\n' if i == 1 else '') for i in (1, 2)).encode(),
    }
    if profile == PROFILES[2]:
        ini=root/'ddraw.ini'
        if not ini.is_file():
            raise ValueError('Source-reconstructed display context requires existing working-copy ddraw.ini')
        config=configparser.ConfigParser(interpolation=None,strict=True)
        config.read_string(ini.read_text(encoding='utf-8-sig'))
        if 'ddraw' not in config:
            raise ValueError('Missing ddraw section')
        for key,value in {'width':'800','height':'600','fullscreen':'false','windowed':'true','maintas':'true',
            'aspect_ratio':'4:3','boxing':'false','border':'true','savesettings':'0','resizable':'false'}.items():
            config['ddraw'][key]=value
        rendered=io.StringIO();config.write(rendered,space_around_delimiters=False)
        settings[ini]=rendered.getvalue().encode('utf-8')
    backups = {}
    prior = os.environ.get('GOD2_CLASSIC_RESOLUTION')
    try:
        if profile in PROFILES[1:]:
            os.environ['GOD2_CLASSIC_RESOLUTION'] = '800x600'
            for index, (path, data) in enumerate(settings.items()):
                path.parent.mkdir(parents=True, exist_ok=True)
                old = path.read_bytes() if path.exists() else None
                backups[path] = old
                if old is not None:
                    (run / f'original-config-{index}.bin').write_bytes(old)
                (run / f'applied-config-{index}.bin').write_bytes(data)
                path.write_bytes(data)
        yield
    finally:
        for path, old in backups.items():
            if old is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(old)
        if prior is None:
            os.environ.pop('GOD2_CLASSIC_RESOLUTION', None)
        else:
            os.environ['GOD2_CLASSIC_RESOLUTION'] = prior


def launch(args):
    from trace_qualification import native
    import capture
    if args.observer == 'omega':
        import omega_capture as capture
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', args.run_id):
        raise ValueError('Run ID must be a short filename-safe identifier')
    dll = HOME / 'build-strike-lab/Release/God2Probe.dll'
    if not dll.is_file():
        raise ValueError('Build God2Probe.dll first')
    run = RUNS / args.run_id
    run.mkdir(parents=True, exist_ok=False)
    with profile_context(args.profile, CLIENT, run):
        # Environment values are allowlisted; unrelated credentials must not enter captures.
        keys = ('PATH','WINDIR','SYSTEMROOT','TEMP','TMP','GOD2_CLASSIC_RESOLUTION','__COMPAT_LAYER')
        write_json(run / 'context.json', {
            'profile': args.profile, 'run_id': args.run_id, 'working_directory': str(CLIENT),
            'arguments': ['127.0.0.1','127.0.0.1','6001','1'], 'client': str(CLIENT / 'God2.exe'),
            'environment': {key: os.environ.get(key) for key in keys},
            'environment_scope': 'Allowlisted values; all other inherited values intentionally omitted',
            'ansi_codepage': ctypes.windll.kernel32.GetACP(), 'oem_codepage': ctypes.windll.kernel32.GetOEMCP(),
            'user_locale_id': ctypes.windll.kernel32.GetUserDefaultLCID(),
            'startup_flags': 'CDB-controlled debug creation; not identical to undebugged launcher flags=0',
            'dll_search': 'Inherited PATH; no SetDllDirectory override',
            'equivalence_scope': 'Known native private-launcher env/config only; historical client/version equivalence unproven',
            'source_evidence': {'working_directory':'ProcessLauncher.cpp LaunchClient + client 0x52f550 cached GetCurrentDirectory',
                'resolution_environment':'ProcessLauncher.cpp kResolutionEnvironmentName/ScopedEnvironmentValue',
                'display_settings':'ClientDisplaySettings.cpp SerializeClientDisplaySettingsUtf8',
                'ddraw_settings':'For PROFILE_STATICALLY_RECONSTRUCTED_STARTUP: ClientDisplaySettings.cpp RequiredDirectDrawSettings; no binary resolution patch',
                'endpoint_config':'EndpointCompatibility.cpp BuildCtServerIniUtf8; substituted loopback only'},
            'probe_sha256': sha(dll), 'time': datetime.now(timezone.utc).isoformat(),
            'source_hashes': {str(p.relative_to(HOME)): sha(p) for p in (
                Path(__file__), Path(capture.__file__), Path(native.__file__),
                HOME/'tools/strike_lab/probe.cpp', HOME/'tools/strike_lab/frontend.cpp')},
        })
        observer = capture.Observer(run, dll)
        native.run(args.run_id, lab=observer)
        result_path = native.OUT / f'{args.run_id}-result.json'
        result = json.loads(result_path.read_text())
        write_json(run / 'result.json', result)
        write_json(run / 'sources.json', {str(p): sha(p) for p in native.OUT.glob(args.run_id + '-*') if p.is_file()})
        log = native.OUT / f'{args.run_id}-native.log'
        write_json(run / 'early-api-coverage.json', {
            'source': str(log), 'sha256':sha(log),
            'hits':re.findall(r'LAB_EARLY api=(\w+)',log.read_text(encoding='ascii',errors='replace')),
            'scope':'Pre-candidate entry-only markers; raw log retains context; no return observation'})
        for event in observer.events:
            if event.get('api') != 'connect' or 'sockaddr_marker' not in event:
                continue
            match = re.search(r'LAB_CONNECT af=([0-9a-f]+) port=([0-9a-f]+) ip=([0-9a-f]+)',event['sockaddr_marker'])
            if match and int(match[1],16)==2 and int(match[3],16)==0x0100007f:
                shutil.copyfile(log,run/'connect-native.log')
                write_json(run/'connect-evidence.json', {'kind':'RUNTIME_CONNECT_ENTRY','destination_ip':'127.0.0.1',
                    'port':socket.ntohs(int(match[2],16)),'native_log':'connect-native.log',
                    'native_sha256':sha(log),'sockaddr_marker':match[0], 'entry_sequence':event['sequence']})
                break
        if result['result'] in ('TOOL_ERROR','FAILED'):
            raise RuntimeError(result.get('error', result['result']))
    print(str(run))


def diff_values(left, right):
    return {key: {'left': left.get(key), 'right': right.get(key)}
            for key in sorted(left.keys() | right.keys()) if left.get(key) != right.get(key)}


def diff(args):
    def load(root, name):
        return json.loads((root / name).read_text(encoding='utf-8'))
    result = {'context': diff_values(load(args.left,'context.json'), load(args.right,'context.json'))}
    left, right = load(args.left,'summary.json'), load(args.right,'summary.json')
    result['summary'] = diff_values(left, right)
    for key in ('paths','modules','resources'):
        a, b = set(left.get(key,[])), set(right.get(key,[]))
        result[key] = {'only_left': sorted(a-b), 'only_right': sorted(b-a)}
    result['snapshot_states'] = {'left': load(args.left,'snapshots.json'), 'right': load(args.right,'snapshots.json')}
    def write_signature(root):
        return [{'stop_rva': e['stop_rva'], 'old':{k:e['old'][k] for k in ('count','pointer')},
                 'new':{k:e['new'][k] for k in ('count','pointer')}}
                for e in load(root,'events.json') if e.get('event_type')=='STRING_TABLE_WRITE']
    a,b = write_signature(args.left),write_signature(args.right)
    result['object_writes']={'different':a!=b,'left':a,'right':b}
    a,b = (args.left/'selected-object.bin').read_bytes(),(args.right/'selected-object.bin').read_bytes()
    result['selected_memory']={'base_va':0x693180,'left_sha256':hashlib.sha256(a).hexdigest(),
        'right_sha256':hashlib.sha256(b).hexdigest(),'left_length':len(a),'right_length':len(b),
        'changed_offsets':[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]}
    write_json(args.output, result)
    print(json.dumps({'output': str(args.output), 'changed_summary_fields': list(result['summary'])}))


def confirmed_port(evidence):
    data = json.loads(evidence.read_text(encoding='utf-8'))
    if data.get('kind') != 'RUNTIME_CONNECT_ENTRY' or data.get('destination_ip') != '127.0.0.1':
        raise ValueError('A runtime-observed IPv4 loopback connect entry is required')
    port = data.get('port')
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('Invalid observed port')
    log = evidence.parent / data['native_log']
    if sha(log) != data['native_sha256']:
        raise ValueError('Evidence log identity mismatch')
    marker = data.get('sockaddr_marker', '')
    if not marker or marker not in log.read_text(encoding='ascii',errors='replace'):
        raise ValueError('Sockaddr marker absent from bound log')
    match = re.fullmatch(r'LAB_CONNECT af=([0-9a-f]+) port=([0-9a-f]+) ip=([0-9a-f]+)', marker)
    if not match or int(match[1],16) != 2 or int(match[3],16) != 0x0100007f or socket.ntohs(int(match[2],16)) != port:
        raise ValueError('Evidence fields disagree with raw sockaddr marker')
    return port


def listen(args):
    port = confirmed_port(args.evidence)
    args.output.mkdir(parents=True, exist_ok=False)
    deadline = time.monotonic() + args.seconds
    events = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        server.bind(('127.0.0.1', port))
        server.listen(1)
        server.settimeout(max(.1, deadline-time.monotonic()))
        try:
            client, peer = server.accept()
            with client, (args.output/'raw.bin').open('xb') as raw:
                total = 0
                while time.monotonic() < deadline and total < 1048576:
                    client.settimeout(max(.1, deadline-time.monotonic()))
                    data = client.recv(min(4096,1048576-total))
                    if not data:
                        events.append({'event':'close','timestamp':time.time()})
                        break
                    raw.write(data)
                    events.append({'event':'read','timestamp':time.time(),'offset':total,'length':len(data),'hex':data.hex()})
                    total += len(data)
        except socket.timeout:
            events.append({'event':'timeout','timestamp':time.time()})
        finally:
            write_json(args.output/'session.json', {'port':port,'send_policy':'SEND_NOTHING','events':events,
                'scope':'TCP read chunks, not recovered packet boundaries; use test credentials only'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tool', choices=('God2LabLauncher','God2SnapshotDiff','God2LoopbackProbe'))
    tool, rest = parser.parse_known_args()
    sub = argparse.ArgumentParser(prog=tool.tool)
    if tool.tool == 'God2LabLauncher':
        sub.add_argument('--profile', choices=PROFILES, required=True)
        sub.add_argument('--run-id', required=True)
        sub.add_argument('--observer', choices=('startup','omega'), default='startup')
        fn = launch
    elif tool.tool == 'God2SnapshotDiff':
        sub.add_argument('left', type=Path)
        sub.add_argument('right', type=Path)
        sub.add_argument('--output', type=Path, required=True)
        fn = diff
    else:
        sub.add_argument('--evidence', type=Path, required=True)
        sub.add_argument('--output', type=Path, required=True)
        sub.add_argument('--seconds', type=int, choices=range(1,121), default=30)
        fn = listen
    fn(sub.parse_args(rest))


if __name__ == '__main__':
    main()
