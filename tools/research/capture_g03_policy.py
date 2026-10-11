"""Run the bounded G03 experiment and read DEP policy at debugger-marked stops."""
import ctypes
from ctypes import wintypes as w
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time

HOME = Path(__file__).resolve().parents[2]
ROOT = HOME/'artifacts/capture_work/host-20260918-1430'


def query(pid):
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    k.OpenProcess.restype = w.HANDLE
    k.CloseHandle.argtypes = [w.HANDLE]
    k.GetProcessDEPPolicy.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD), ctypes.POINTER(w.BOOL)]
    k.GetProcessDEPPolicy.restype = w.BOOL
    handle = k.OpenProcess(0x400, False, pid)
    if not handle:
        return {'ok': False, 'winerror': ctypes.get_last_error()}
    try:
        flags, permanent = w.DWORD(), w.BOOL()
        ok = k.GetProcessDEPPolicy(handle, ctypes.byref(flags), ctypes.byref(permanent))
        return {'ok': bool(ok), 'flags': flags.value if ok else None,
                'permanent': bool(permanent.value) if ok else None,
                'winerror': None if ok else ctypes.get_last_error()}
    finally:
        k.CloseHandle(handle)


if __name__ == '__main__':
    output = ROOT/'output/g03-deep-policy.json'
    if output.exists():
        raise ValueError('Policy output already exists')
    process = subprocess.Popen([sys.executable, str(HOME/'tools/research/host_capture.py'),
        'capture', '--root', str(ROOT), '--script', str(ROOT/'output/capture-g03-deep.txt'),
        '--run-id', 'g03-deep'], cwd=HOME, creationflags=subprocess.CREATE_NO_WINDOW)
    records, seen = [], set()
    log = ROOT/'output/g03-deep-stdout.log'
    while process.poll() is None:
        native = log.read_text(encoding='ascii', errors='replace') if log.exists() else ''
        for stage, pid_hex in re.findall(r'^POLICY stage=(\w+) pid=([0-9a-f]+)\s*$', native, re.M):
            if stage not in seen:
                seen.add(stage)
                records.append({'stage': stage, 'pid': int(pid_hex, 16),
                    'queried_at': datetime.now(timezone.utc).isoformat(), **query(int(pid_hex, 16))})
        time.sleep(0.05)
    with output.open('x', encoding='utf-8') as stream:
        json.dump({'api': 'GetProcessDEPPolicy', 'access': 'PROCESS_QUERY_INFORMATION',
                   'read_only': True, 'records': records}, stream, indent=2)
    print(json.dumps(records))
    raise SystemExit(process.returncode)
