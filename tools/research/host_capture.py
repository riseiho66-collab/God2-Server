"""Owner-authorized, program-firewalled host capture. Not VM/filesystem isolation."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from runtime_environment_probe import ARTIFACT
from tool_inventory import metadata, powershell

HOME = Path(__file__).resolve().parents[2]
PS = str(Path(os.environ.get('WINDIR', 'C:/Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)


def quote(value):
    return "'"+str(value).replace("'", "''")+"'"


def root_path(value):
    root = Path(value).resolve()
    allowed = (HOME/'artifacts/capture_work').resolve()
    if root.parent != allowed or not re.fullmatch(r'host-[a-z0-9-]+', root.name):
        raise ValueError('Host workspace must be a dedicated artifacts/capture_work/host-* directory')
    return root


def prepare(root, source, debugger):
    source, debugger = source.resolve(strict=True), debugger.resolve(strict=True)
    tool = metadata(debugger)
    if (debugger.name.lower() != 'cdb.exe' or tool['architecture'] != 'x86'
            or tool['signature_status'] != 'Valid' or 'O=Microsoft Corporation' not in (tool['signer'] or '')):
        raise ValueError('Need Microsoft-signed x86 CDB')
    if digest(source/'God2.exe') != ARTIFACT:
        raise ValueError('Source is not the bound original artifact')
    root.mkdir(parents=True, exist_ok=False)
    shutil.copytree(source, root/'client')
    shutil.copytree(debugger.parent, root/'debugger')
    (root/'output').mkdir()
    if digest(root/'client/God2.exe') != ARTIFACT:
        raise ValueError('Working copy mismatch')
    programs = sorted(str(p.resolve()) for folder in ('client', 'debugger') for p in (root/folder).rglob('*.exe'))
    request = {'created_at': datetime.now(timezone.utc).isoformat(), 'original': str(source/'God2.exe'),
               'artifact_id': ARTIFACT, 'working_copy_sha256': digest(root/'client/God2.exe'), 'tool': tool,
               'programs': programs, 'group': 'GOD2-Research-'+root.name,
               'limitation': 'Program-scoped firewall only; no filesystem isolation; does not constrain arbitrary external child executables.'}
    save(root/'host-request.json', request)
    return request


def firewall_query(request):
    group = quote(request['group'])
    return f"""
    $rules=@(Get-NetFirewallRule -PolicyStore ActiveStore -Group {group} -ErrorAction Stop | ForEach-Object {{
        @{{name=$_.Name;direction=[string]$_.Direction;action=[string]$_.Action;enabled=[string]$_.Enabled;
          profile=[string]$_.Profile;status=[string]$_.PrimaryStatus;enforcement=@($_.CimInstanceProperties['EnforcementStatus'].Value | ForEach-Object {{[int]$_}});
          program=($_ | Get-NetFirewallApplicationFilter).Program}}
    }})
    @{{rules=$rules;profiles=@(Get-NetFirewallProfile -PolicyStore ActiveStore | ForEach-Object {{
        @{{name=[string]$_.Name;enabled=[string]$_.Enabled;local_rules=[string]$_.AllowLocalFirewallRules}}
    }})}}
    """


def firewall_ready(state, programs):
    profiles = state.get('profiles', [])
    if len(profiles) != 3 or any(p.get('enabled') != 'True' or p.get('local_rules') == 'False' for p in profiles):
        return False
    for program in programs:
        for direction in ('Inbound', 'Outbound'):
            if not any(r.get('program', '').casefold() == program.casefold() and r.get('direction') == direction
                       and r.get('action') == 'Block' and r.get('enabled') == 'True' and r.get('profile') == 'Any'
                       and r.get('status') == 'OK' and isinstance(r.get('enforcement'), list)
                       and all(type(v) is int for v in r['enforcement'])
                       and 1 in r['enforcement'] and set(r['enforcement']) <= {1, 5}
                       for r in state.get('rules', [])):
                return False
    return True


def install_firewall(root, request):
    output = root/'output/firewall-install.json'
    if output.exists():
        raise ValueError('Firewall installation already recorded')
    relative = []
    for program in request['programs']:
        if not Path(program).resolve(strict=True).is_relative_to(root):
            raise ValueError('Rule path escapes dedicated workspace')
        relative.append(quote(Path(program).relative_to(root)))
    rules = f"""
    $root={quote(root)}; $group={quote(request['group'])}; $paths=@({','.join(relative)})
    for ($i=0; $i -lt $paths.Count; $i++) {{
        $program=Join-Path $root $paths[$i]
        foreach ($direction in @('Inbound','Outbound')) {{
            $name=$group+'-'+$i+'-'+$direction
            New-NetFirewallRule -Name $name -DisplayName $name -Group $group -Program $program -Direction $direction -Action Block -Enabled True -Profile Any -Protocol Any -RemoteAddress Any -PolicyStore PersistentStore | Out-Null
        }}
    }}
    """
    body = "$ErrorActionPreference='Stop'; try {\n"+rules+'\n$value=& { '+firewall_query(request)+' }; '
    body += f"$value | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath {quote(output)} -Encoding UTF8 "
    body += f"}} catch {{ @{{error=$_.Exception.Message}} | ConvertTo-Json | Set-Content -LiteralPath {quote(output)} -Encoding UTF8; exit 1 }}"
    encoded = base64.b64encode(body.encode('utf-16le')).decode('ascii')
    launch = (f"$p=Start-Process -FilePath {quote(PS)} -Verb RunAs -WindowStyle Hidden -PassThru "
              f"-ArgumentList '-NoProfile -EncodedCommand {encoded}'; @{{helper_pid=$p.Id}} | ConvertTo-Json")
    info = powershell(launch)
    save(root/'output/firewall-helper.json', info)
    deadline = time.monotonic()+90
    while not output.exists() and time.monotonic() < deadline:
        time.sleep(0.25)
    state = json.loads(output.read_text(encoding='utf-8-sig'))
    if not firewall_ready(state, request['programs']):
        raise ValueError('Effective firewall verification failed; no client may launch')
    return state


def launch(root, request, name, args, timeout=120):
    if not re.fullmatch(r'[a-z0-9-]+', name):
        raise ValueError('Invalid run name')
    output = root/'output'
    if any(output.glob(name+'*')):
        raise ValueError('Run outputs already exist')
    if digest(root/'client/God2.exe') != ARTIFACT or digest(request['original']) != ARTIFACT:
        raise ValueError('Original/working copy identity mismatch')
    if digest(root/'debugger/cdb.exe') != request['tool']['sha256']:
        raise ValueError('Debugger copy identity mismatch')
    state = powershell('[Console]::OutputEncoding=[Text.Encoding]::UTF8; $v=& { '+firewall_query(request)+' }; $v | ConvertTo-Json -Depth 8')
    if not firewall_ready(state, request['programs']):
        raise ValueError('Live firewall verification failed')
    save(output/(name+'-firewall.json'), state)
    command = [str(root/'debugger/cdb.exe'), *args]
    info = {'started_at': datetime.now(timezone.utc).isoformat(), 'command': command, 'elevated': False}
    with (output/(name+'-stdout.log')).open('xb') as stdout, (output/(name+'-stderr.log')).open('xb') as stderr:
        process = subprocess.Popen(command, cwd=root/'client', stdin=subprocess.DEVNULL,
                                   stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
        info['debugger_pid'] = process.pid
        try:
            info['exit_code'] = process.wait(timeout=timeout)
            info['timed_out'] = False
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=15)
            process.wait(timeout=15)
            info.update(timed_out=True, exit_code=process.returncode)
    info['completed_at'] = datetime.now(timezone.utc).isoformat()
    save(output/(name+'-result.json'), info)
    return info


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'firewall', 'probe', 'capture'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--debugger', type=Path)
    parser.add_argument('--script', type=Path)
    parser.add_argument('--run-id', default='startup')
    args = parser.parse_args()
    root = root_path(args.root)
    if powershell("([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator) | ConvertTo-Json"):
        parser.error('Capture orchestrator must not run elevated')
    if args.action == 'prepare':
        result = prepare(root, args.source, args.debugger)
    else:
        request = json.loads((root/'host-request.json').read_text())
        if args.action == 'firewall':
            result = install_firewall(root, request)
        elif args.action == 'probe':
            version = launch(root, request, 'probe-version', ['-version'], 30)
            benign = launch(root, request, 'probe-x86', ['-cf', str(Path(__file__).with_name('probe-cdb.txt')),
                           str(Path(os.environ['WINDIR'])/'SysWOW64/cmd.exe'), '/c', 'exit'], 30)
            native = (root/'output/probe-x86-stdout.log').read_bytes()
            result = {'ready': version['exit_code'] == 0 and benign['exit_code'] == 0 and not benign['timed_out']
                      and re.search(rb'(?m)^GOD2_X86_DEBUG_PROBE_OK\r?$', native) is not None,
                      'scope': 'HOST_PROGRAM_FIREWALL_NOT_VM_ISOLATION', 'version': version, 'benign': benign}
            save(root/'output/host-probe.json', result)
        else:
            if not json.loads((root/'output/host-probe.json').read_text())['ready']:
                parser.error('Host benign probe not ready')
            script = args.script.resolve(strict=True)
            if script.parent != root/'output':
                parser.error('Capture script must reside in this output directory')
            result = launch(root, request, args.run_id, ['-cf', str(script), str(root/'client/God2.exe')])
    print(json.dumps(result, indent=2))
    if args.action == 'capture' and (result['timed_out'] or result['exit_code'] != 0):
        return 1
    if args.action == 'probe' and not result['ready']:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
