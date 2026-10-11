"""Observe and stop a disposable game on the caller's private desktop."""
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import psutil
import sys
import time


NAME = 'god2-current-lab-2598.exe'


def windows():
    user = c.WinDLL('user32', use_last_error=True)
    callback = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    user.EnumWindows.argtypes = [callback, w.LPARAM]
    user.GetClassNameW.argtypes = [w.HWND, w.LPWSTR, c.c_int]
    user.GetWindowTextW.argtypes = [w.HWND, w.LPWSTR, c.c_int]
    user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
    rows = []

    @callback
    def visit(hwnd, _):
        klass = c.create_unicode_buffer(128)
        title = c.create_unicode_buffer(256)
        pid = w.DWORD()
        user.GetClassNameW(hwnd, klass, len(klass))
        user.GetWindowTextW(hwnd, title, len(title))
        user.GetWindowThreadProcessId(hwnd, c.byref(pid))
        rows.append({'pid': pid.value, 'class': klass.value, 'title': title.value})
        return True

    user.EnumWindows(visit, 0)
    return rows


def main():
    output = Path(sys.argv[1])
    snapshots = []
    for _ in range(24):
        games = [p for p in psutil.process_iter(['pid', 'name', 'exe'])
                 if (p.info['name'] or '').lower() == NAME and
                 p.info['exe'] and Path(p.info['exe']).parent ==
                 Path('C:/Users/risei/Desktop/God2/God2')]
        snapshots.append({'processes': [p.info for p in games],
                          'windows': windows()})
        time.sleep(.5)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshots, ensure_ascii=False, indent=2), encoding='utf-8')
    for p in games:
        try:
            p.terminate()
        except psutil.NoSuchProcess:
            pass


if __name__ == '__main__':
    main()
