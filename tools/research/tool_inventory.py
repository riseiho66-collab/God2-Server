"""Read-only discovery of known Windows debuggers; never launches a candidate."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pefile


def powershell(script):
    script = "$ErrorActionPreference='Stop'; " + script
    encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-EncodedCommand', encoded],
                            capture_output=True, timeout=60,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace'))
    return json.loads(result.stdout.decode('utf-8-sig'))


def metadata(path):
    path = Path(path).resolve(strict=True)
    quoted = str(path).replace("'", "''")
    info = powershell("[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
                      # Inherited PSModulePath may point at incompatible PowerShell 7 modules.
                      "Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Security/Microsoft.PowerShell.Security.psd1') -ErrorAction Stop; "
                      f"$p='{quoted}'; $s=Get-AuthenticodeSignature -LiteralPath $p; "
                      "$v=(Get-Item -LiteralPath $p).VersionInfo; "
                      "[ordered]@{version=$v.FileVersion; product_version=$v.ProductVersion; "
                      "signature_status=[string]$s.Status; signer=$s.SignerCertificate.Subject; "
                      "thumbprint=$s.SignerCertificate.Thumbprint} | ConvertTo-Json -Compress")
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    with pefile.PE(str(path), fast_load=True) as pe:
        arch = {0x14c: 'x86', 0x8664: 'x64', 0xaa64: 'arm64'}.get(pe.FILE_HEADER.Machine, 'UNKNOWN')
    return dict(path=str(path), sha256=digest, architecture=arch, **info,
                execution={'status': 'UNKNOWN', 'reason': 'Inventory does not execute tools'})


def discover(extra=()):
    candidates = set(map(Path, extra))
    for name in ('cdb.exe', 'windbg.exe', 'WinDbgX.exe', 'x32dbg.exe', 'x64dbg.exe', 'devenv.exe', 'msvsmon.exe'):
        found = shutil.which(name)
        if found:
            candidates.add(Path(found))
    patterns = (
        ('ProgramFiles(x86)', 'Windows Kits/*/Debuggers/*/cdb.exe'),
        ('ProgramFiles(x86)', 'Windows Kits/*/Debuggers/*/windbg.exe'),
        ('ProgramFiles', 'Microsoft Visual Studio/*/*/Common7/IDE/devenv.exe'),
        ('ProgramFiles', 'Microsoft Visual Studio/*/*/Common7/IDE/Remote Debugger/*/msvsmon.exe'),
    )
    for env, pattern in patterns:
        if os.environ.get(env):
            candidates.update(Path(os.environ[env]).glob(pattern))
    packages = powershell("[Console]::OutputEncoding=[Text.Encoding]::UTF8; "
                          "ConvertTo-Json -InputObject @(Get-AppxPackage '*WinDbg*' | Select-Object -ExpandProperty InstallLocation) -Compress")
    for package in packages:
        candidates.update(Path(package).glob('*/cdb.exe'))
        candidates.update(Path(package).glob('DbgX.Shell.exe'))
    records = []
    for path in sorted(candidates, key=str):
        try:
            records.append(metadata(path))
        except (OSError, ValueError, RuntimeError, pefile.PEFormatError) as error:
            records.append({'path': str(path), 'status': 'UNKNOWN', 'error': str(error)})
    return {'schema_version': 1, 'captured_at': datetime.now(timezone.utc).isoformat(),
            'environment': os.environ.get('COMPUTERNAME', 'UNKNOWN'), 'tools': records,
            'scope': 'Known install locations and explicit paths; not an exhaustive disk search'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', action='append', default=[])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; preserve prior inventory')
    report = discover(args.path)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps({'output': str(args.output), 'tools': len(report['tools'])}))


if __name__ == '__main__':
    main()
