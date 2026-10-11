"""No-screenshot original-client login probe on the runner's private desktop."""
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import pefile
import psutil
import sqlite3
import sys
import time

user = c.WinDLL('user32', use_last_error=True)
user.EnumWindows.argtypes = [c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM), w.LPARAM]
user.GetClassNameW.argtypes = [w.HWND, w.LPWSTR, c.c_int]
user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
user.GetClientRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
user.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
user.IsWindowUnicode.argtypes = [w.HWND]
user.FindWindowW.argtypes = [w.LPCWSTR, w.LPCWSTR]


def game_window():
    callback = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    windows = []

    @callback
    def visit(hwnd, _):
        name = c.create_unicode_buffer(128)
        if user.GetClassNameW(hwnd, name, len(name)) and name.value == 'XianJieWndClass':
            pid = w.DWORD()
            user.GetWindowThreadProcessId(hwnd, c.byref(pid))
            windows.append((hwnd, pid.value))
        return True

    user.EnumWindows(visit, 0)
    return windows[0] if windows else (None, None)


def click(hwnd, x, y):
    rect = w.RECT()
    if not user.GetClientRect(hwnd, c.byref(rect)) or rect.right <= 0 or rect.bottom <= 0:
        raise RuntimeError('GAME_WINDOW_RECT_UNAVAILABLE')
    x = round(x * rect.right / 800)
    y = round(y * rect.bottom / 600)
    position = (y << 16) | x
    for message, key in ((0x200, 0), (0x201, 1), (0x202, 0)):
        if not user.PostMessageW(hwnd, message, key, position):
            raise OSError(c.get_last_error(), 'PostMessageW click failed')
        time.sleep(.3)


def type_ascii(hwnd, value):
    for ch in value:
        if not user.PostMessageW(hwnd, 0x102, ord(ch), 1):
            raise OSError(c.get_last_error(), 'PostMessageW character failed')


def position(db):
    with sqlite3.connect(f'file:{db}?mode=ro', uri=True) as connection:
        rows = connection.execute('select * from recovered_positions where character_id=1').fetchall()
        return rows[0] if rows else None


def main():
    output, db = map(Path, sys.argv[1:3])
    server_log = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {'stages': [], 'before_position': position(db)}
    try:
        deadline = time.monotonic() + 50
        hwnd = pid = None
        while time.monotonic() < deadline:
            hwnd, pid = game_window()
            if hwnd:
                break
            dialog = user.FindWindowW(None, 'God2 C++ Support')
            if dialog:
                result['launcher_error_dialog'] = True
                user.PostMessageW(dialog, 0x10, 0, 0)
                raise RuntimeError('LAUNCHER_REPORTED_ERROR')
            time.sleep(.2)
        if not hwnd:
            raise RuntimeError('GAME_WINDOW_NOT_FOUND')
        rect = w.RECT()
        for _ in range(75):
            if user.GetClientRect(hwnd, c.byref(rect)) and (rect.right, rect.bottom) in ((800, 600), (1024, 768)):
                break
            time.sleep(.2)
        result.update(pid=pid, window_unicode=bool(user.IsWindowUnicode(hwnd)),
                      window_size=[rect.right, rect.bottom])
        result['external_ime_bridge_loaded'] = any(
            Path(item.path).name.lower() == 'god2imebridge.dll'
            for item in psutil.Process(pid).memory_maps())
        game_pe = pefile.PE(psutil.Process(pid).exe(), fast_load=True)
        result['embedded_ime_fix'] = any(
            section.Name.rstrip(b'\0') == b'.imefix' for section in game_pe.sections)
        if (rect.right, rect.bottom) not in ((800, 600), (1024, 768)):
            raise RuntimeError('GAME_WINDOW_SIZE_INVALID')
        result['stages'].append('game_window')
        time.sleep(2)
        click(hwnd, 512, 464)
        result['stages'].append('menu_clicked')
        time.sleep(3)
        click(hwnd, 437, 232)
        type_ascii(hwnd, 'codexlab')
        click(hwnd, 437, 263)
        type_ascii(hwnd, 'labtest2345')
        click(hwnd, 452, 304)
        result['stages'].append('login_submitted')
        time.sleep(4)
        click(hwnd, 330, 145)
        click(hwnd, 452, 413)
        result['stages'].append('server_selected')
        time.sleep(4)
        click(hwnd, 330, 150)
        click(hwnd, 452, 376)
        result['stages'].append('channel_selected')
        time.sleep(4)
        click(hwnd, 452, 370)
        result['stages'].append('character_selected')
        time.sleep(8)
        click(hwnd, 600, 400)
        time.sleep(5)
        result['after_position'] = position(db)
        result['stages'].append('movement_attempted')
        if server_log:
            # At 800x600 x=200 is the channel selector; the edit starts at
            # x=239. Prove focus and the C2S route with ASCII before probing
            # Unicode messages (which still do not validate physical IME).
            chat_log_start = len(server_log.read_bytes())
            before_count = server_log.read_bytes().count(b'NATIVE_CHAT_ACCEPTED')
            click(hwnd, 400, 584)
            type_ascii(hwnd, 'probe123')
            user.PostMessageW(hwnd, 0x100, 0x0d, 0)
            user.PostMessageW(hwnd, 0x101, 0x0d, 0)
            for _ in range(10):
                if server_log.read_bytes().count(b'NATIVE_CHAT_ACCEPTED') > before_count:
                    break
                time.sleep(1)
            result['ascii_chat_accepted'] = server_log.read_bytes().count(b'NATIVE_CHAT_ACCEPTED') > before_count
            before_count = server_log.read_bytes().count(b'NATIVE_CHAT_ACCEPTED')
            click(hwnd, 400, 584)
            user.PostMessageW(hwnd, 0x102, ord('中'), 1)
            user.PostMessageW(hwnd, 0x100, 0x0d, 0)
            user.PostMessageW(hwnd, 0x101, 0x0d, 0)
            new_line = b''
            for _ in range(20):
                lines = [line for line in server_log.read_bytes().splitlines()
                         if b'NATIVE_CHAT_ACCEPTED' in line]
                if len(lines) > before_count:
                    new_line = lines[-1]
                    break
                time.sleep(1)
            result['chinese_chat_accepted'] = bool(new_line)
            result['chinese_chat_two_legacy_bytes'] = b'legacy_bytes=2' in new_line
            # The file sink may flush the ASCII receipt only after the
            # Unicode probe. Reconcile both distinct payload lengths from
            # this isolated run instead of treating the earlier timeout as
            # a definitive rejection.
            receipts = [line for line in server_log.read_bytes()[chat_log_start:].splitlines()
                        if b'NATIVE_CHAT_ACCEPTED' in line]
            result['ascii_chat_accepted'] = any(b'legacy_bytes=8 ' in line for line in receipts)
            result['chinese_chat_accepted'] = any(b'legacy_bytes=2 ' in line for line in receipts)
            result['chinese_chat_two_legacy_bytes'] = result['chinese_chat_accepted']
            result['stages'].append('chinese_chat_submitted')
        result['game_window_alive'] = bool(game_window()[0])
        user.PostMessageW(hwnd, 0x10, 0, 0)
    except Exception as exc:
        result['error'] = repr(exc)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if not result.get('error') else 1


if __name__ == '__main__':
    raise SystemExit(main())
