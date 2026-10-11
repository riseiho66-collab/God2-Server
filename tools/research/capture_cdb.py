"""Use the existing evidence workflow after a sandbox-only operational preflight."""
import argparse
import json
from pathlib import Path
import re

from runtime_environment_probe import ARTIFACT, Sandbox, ready


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sandbox-id', required=True)
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--script', default='capture-cdb-startup.txt')
    parser.add_argument('--copy-resources', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9-]+', args.run_id) or not re.fullmatch(r'capture-cdb-[a-z0-9-]+\.txt', args.script):
        parser.error('Invalid run/script name')
    output = args.output_directory.resolve(strict=True)
    report = json.loads((output / 'environment-probe.json').read_text(encoding='utf-8'))
    if report['sandbox_id'] != args.sandbox_id or not ready(report, report['tool']['sha256']):
        parser.error('Runtime environment is not ready in this sandbox')
    sandbox = Sandbox(args.sandbox_id, output)
    for log in output.glob('*-stdout.log'):
        if "Debuggee initialization failed, Win32 error 0n4551" in log.read_text(encoding='utf-8-sig', errors='replace'):
            parser.error('BLOCKED_EXTERNAL_POLICY: prior client policy denial; use an owner-approved environment')
    if any(output.glob('cdb-*-mapped.bin')):
        parser.error('Mapped images already exist; use a fresh capture directory')
    current = sandbox.query(args.run_id+'-preflight', """
        $ips=@(Get-NetIPAddress | Where-Object { $_.IPAddress -ne '::1' -and $_.IPAddress -notlike '127.*' })
        @{non_loopback_addresses=@($ips | Select-Object IPAddress,InterfaceAlias);
          source_sha256=(Get-FileHash C:\\Input\\Client\\God2.exe -Algorithm SHA256).Hash;
          working_sha256=(Get-FileHash C:\\God2Work\\God2.exe -Algorithm SHA256).Hash;
          tool_sha256=(Get-FileHash C:\\Debugger\\cdb.exe -Algorithm SHA256).Hash}
        """)
    if (current['non_loopback_addresses'] or current['source_sha256'].lower() != ARTIFACT
            or current['working_sha256'].lower() != ARTIFACT
            or current['tool_sha256'].lower() != report['tool']['sha256']):
        parser.error('Live preflight failed; no client launch')
    if args.copy_resources:
        sandbox.query(args.run_id+'-resources', """
            Get-ChildItem C:\\Input\\Client | Where-Object Name -ne 'God2.exe' |
                Copy-Item -Destination C:\\God2Work -Recurse
            @{working_sha256=(Get-FileHash C:\\God2Work\\God2.exe -Algorithm SHA256).Hash;
              completed_at=[DateTime]::UtcNow.ToString('o')}
            """)
    result = sandbox.launch(args.run_id, '-cf C:\\Input\\Scripts\\'+args.script+' C:\\God2Work\\God2.exe', 120000)
    print(json.dumps(result, indent=2))
    return 1 if result['timed_out'] or result['exit_code'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
