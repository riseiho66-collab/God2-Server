"""Run a bounded, client-free capability probe inside an already mapped sandbox."""
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess

from tool_inventory import metadata

CHECKS = ('network_isolated', 'output_writable', 'source_artifact_preserved',
          'source_mapping_readonly', 'working_copy_preserved', 'tool_identity_preserved',
          'x86_tool', 'debugger_starts', 'x86_debug_execution')

ARTIFACT = 'fb72296cab5950b74d8f7c98155145f7c5f58749c3011adb0540325b60749dd1'


class Sandbox:
    def __init__(self, sandbox_id, output):
        self.sandbox_id, self.output = sandbox_id, Path(output)
        self.wsb = str(Path(os.environ['LOCALAPPDATA']) / 'Microsoft/WindowsApps/wsb.exe')

    def command(self, command, timeout=180):
        result = subprocess.run([self.wsb, 'exec', '--id', self.sandbox_id, '--command', command,
                                 '--run-as', 'System', '--raw'], capture_output=True, timeout=timeout,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise RuntimeError(result.stderr.decode('utf-8', errors='replace'))
        reply = json.loads(result.stdout.decode('utf-8-sig'))
        if reply.get('ExitCode') != 0:
            raise RuntimeError(f'Guest command failed: {reply}')

    def query(self, name, expression):
        if not re.fullmatch(r'[a-z0-9-]+', name) or (self.output / (name+'.json')).exists():
            raise ValueError('Invalid or previously used query name')
        # Native interactive commands only: no execution-policy setting or .ps1 loading.
        code = ("$ErrorActionPreference='Stop'; try { $value = & { " + expression
                + " }; ConvertTo-Json -InputObject $value -Depth 8 | Set-Content -Encoding UTF8 "
                + f"C:\\Output\\{name}.json }} catch {{ @{{error=$_.Exception.Message}} | ConvertTo-Json | Set-Content -Encoding UTF8 C:\\Output\\{name}.json; exit 1 }}")
        encoded = base64.b64encode(code.encode('utf-16le')).decode('ascii')
        try:
            self.command('powershell.exe -NoProfile -EncodedCommand '+encoded)
        except RuntimeError:
            if not (self.output / (name+'.json')).exists():
                raise
        value = json.loads((self.output / (name+'.json')).read_text(encoding='utf-8-sig'))
        if isinstance(value, dict) and 'error' in value:
            raise RuntimeError(value['error'])
        return value

    def launch(self, name, arguments, timeout_ms=30000):
        if not re.fullmatch(r'[a-z0-9-]+', name):
            raise ValueError('Invalid launch name')
        args = arguments.replace("'", "''")
        return self.query(name, f"""
        $si = New-Object Diagnostics.ProcessStartInfo
        $si.FileName = 'C:\\Debugger\\cdb.exe'
        $si.Arguments = '{args}'
        $si.WorkingDirectory = 'C:\\God2Work'
        $si.UseShellExecute = $false
        $si.CreateNoWindow = $true
        $si.RedirectStandardOutput = $true
        $si.RedirectStandardError = $true
        $p = New-Object Diagnostics.Process
        $p.StartInfo = $si
        $startedAt = [DateTime]::UtcNow.ToString('o')
        if (-not $p.Start()) {{ throw 'Process did not start' }}
        $stdout = $p.StandardOutput.ReadToEndAsync()
        $stderr = $p.StandardError.ReadToEndAsync()
        $timeout = -not $p.WaitForExit({timeout_ms})
        if ($timeout) {{ $p.Kill(); $p.WaitForExit() }}
        [IO.File]::WriteAllText('C:\\Output\\{name}-stdout.log', $stdout.Result)
        [IO.File]::WriteAllText('C:\\Output\\{name}-stderr.log', $stderr.Result)
        @{{pid=$p.Id; exit_code=$p.ExitCode; timed_out=$timeout; started_at=$startedAt; completed_at=[DateTime]::UtcNow.ToString('o')}}
        """)


def probe(sandbox, tool):
    report = dict(schema_version=1, sandbox_id=sandbox.sandbox_id,
                  captured_at=datetime.now(timezone.utc).isoformat(), status='BLOCKED', checks={}, errors=[])
    checks = report['checks']
    try:
        env = sandbox.query('native-environment', """
        $ips=@(Get-NetIPAddress | Where-Object { $_.IPAddress -ne '::1' -and $_.IPAddress -notlike '127.*' })
        $readonly=$false
        try { $s=[IO.File]::Open('C:\\Input\\Client\\God2.exe',[IO.FileMode]::Open,[IO.FileAccess]::Write,[IO.FileShare]::ReadWrite); $s.Dispose() }
        catch [UnauthorizedAccessException] { $readonly=$true }
        @{computer=$env:COMPUTERNAME; non_loopback_addresses=@($ips | Select-Object IPAddress,InterfaceAlias);
          source_readonly=$readonly; source_sha256=(Get-FileHash C:\\Input\\Client\\God2.exe -Algorithm SHA256).Hash}
        """)
        report['environment'] = env
        checks['network_isolated'] = not env['non_loopback_addresses']
        checks['source_mapping_readonly'] = env['source_readonly'] is True
        checks['source_artifact_preserved'] = env['source_sha256'].lower() == ARTIFACT
        checks['output_writable'] = True  # Guest query successfully wrote into the mapped output.
        if not all(checks.values()):
            raise RuntimeError('Isolation or source identity failed; refusing tool execution')
        copy = sandbox.query('native-working-copy', """
        if (Test-Path C:\\God2Work) { throw 'Working copy already exists' }
        New-Item -ItemType Directory C:\\God2Work | Out-Null
        Copy-Item C:\\Input\\Client\\God2.exe C:\\God2Work\\God2.exe
        Copy-Item C:\\Input\\Debugger C:\\Debugger -Recurse
        @{working_sha256=(Get-FileHash C:\\God2Work\\God2.exe -Algorithm SHA256).Hash;
          tool_sha256=(Get-FileHash C:\\Debugger\\cdb.exe -Algorithm SHA256).Hash}
        """)
        report.update(copy)
        checks['working_copy_preserved'] = copy['working_sha256'].lower() == ARTIFACT
        checks['tool_identity_preserved'] = copy['tool_sha256'].lower() == tool['sha256']
        checks['x86_tool'] = tool['architecture'] == 'x86'
        if not all(checks.values()):
            raise RuntimeError('Tool or working-copy identity changed')
        report['version_launch'] = sandbox.launch('cdb-version', '-version')
        checks['debugger_starts'] = (report['version_launch']['exit_code'] == 0
                                    and not report['version_launch']['timed_out'])
        if not checks['debugger_starts']:
            raise RuntimeError('Debugger version probe failed')
        report['debug_launch'] = sandbox.launch('cdb-x86-probe',
            '-cf C:\\Input\\Scripts\\probe-cdb.txt C:\\Windows\\SysWOW64\\cmd.exe /c exit')
        native = (sandbox.output / 'cdb-x86-probe-stdout.log').read_text(encoding='utf-8-sig')
        checks['x86_debug_execution'] = (report['debug_launch']['exit_code'] == 0
            and not report['debug_launch']['timed_out']
            and re.search(r'^GOD2_X86_DEBUG_PROBE_OK$', native, re.MULTILINE) is not None
            and re.search(r'^GOD2_PROBE pid=[0-9a-f]+ tid=[0-9a-f]+ pc=', native, re.MULTILINE) is not None)
        if all(checks.get(name) is True for name in CHECKS):
            report['status'] = 'RUNTIME_ENVIRONMENT_READY'
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        report['errors'].append(str(error))
        if 'application control' in str(error).lower():
            report['status'] = 'BLOCKED_EXTERNAL_POLICY'
    return report


def ready(report, expected_hash):
    return (report.get('status') == 'RUNTIME_ENVIRONMENT_READY'
            and str(report.get('tool_sha256', '')).lower() == expected_hash.lower()
            and all(report.get('checks', {}).get(name) is True for name in CHECKS))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sandbox-id', required=True)
    parser.add_argument('--debugger', type=Path, required=True)
    parser.add_argument('--output-directory', type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-fA-F0-9-]{36}', args.sandbox_id):
        parser.error('Invalid sandbox identifier')
    tool = metadata(args.debugger)
    if (args.debugger.name.lower() != 'cdb.exe' or tool['architecture'] != 'x86'
            or tool['signature_status'] != 'Valid' or 'O=Microsoft Corporation' not in (tool['signer'] or '')):
        parser.error('This probe accepts only the inventoried Microsoft-signed x86 CDB')
    output = args.output_directory.resolve(strict=True)
    report_path = output / 'environment-probe.json'
    if report_path.exists():
        parser.error('Probe output exists; do not overwrite')
    report = probe(Sandbox(args.sandbox_id, output), tool)
    report['tool'] = tool
    with report_path.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2))
    return 0 if ready(report, tool['sha256']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
