"""Capture an already running God2Lab desktop without switching the input desktop."""
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import subprocess
import sys
import time


def main() -> int:
    output = Path(sys.argv[1])
    type_text = sys.argv[2].split('=', 1)[1] if sys.argv[2].startswith('--type=') else None
    ansi_input = sys.argv[2].startswith('--self-ansi=')
    ime_input = sys.argv[2].startswith('--self-ime=')
    self_text = sys.argv[2].split('=', 1)[1] if sys.argv[2].startswith(('--self=', '--self-ansi=', '--self-ime=')) else (
        'hello' if sys.argv[2] == '--self' else None)
    click_mode = next((prefix for prefix in ('--click=', '--double=', '--dblmsg=', '--right=')
                       if sys.argv[2].startswith(prefix)), None)
    no_capture = '--no-capture' in sys.argv[3:]
    drag_mode = sys.argv[2].startswith('--drag=')
    battle_trigger = sys.argv[2].startswith('--battle-trigger=')
    battle_watch = sys.argv[2] == '--battle-watch'
    observe_only = sys.argv[2] == '--observe'
    key_mode = sys.argv[2].startswith('--key=')
    sender = Path(sys.argv[2]) if self_text is None and click_mode is None and not drag_mode and not key_mode and type_text is None and not battle_trigger and not battle_watch and not observe_only else None
    user = c.WinDLL('user32', use_last_error=True)
    user.GetProcessWindowStation.restype = w.HANDLE
    user.EnumDesktopsW.argtypes = [w.HANDLE, c.c_void_p, w.LPARAM]
    callback_type = c.WINFUNCTYPE(w.BOOL, w.LPWSTR, w.LPARAM)
    names = []

    @callback_type
    def visit(name, _):
        if name.startswith('God2Lab-'):
            names.append(name)
        return True

    if not user.EnumDesktopsW(user.GetProcessWindowStation(), visit, 0):
        raise c.WinError(c.get_last_error())
    if len(names) != 1:
        raise RuntimeError(f'Expected one private lab desktop, found {names!r}')
    user.OpenDesktopW.argtypes = [w.LPCWSTR, w.DWORD, w.BOOL, w.DWORD]
    user.OpenDesktopW.restype = w.HANDLE
    desktop = user.OpenDesktopW(names[0], 0, False, 0x01ff | 0x000f0000)
    if not desktop:
        raise c.WinError(c.get_last_error())
    user.SetThreadDesktop.argtypes = [w.HANDLE]
    if not user.SetThreadDesktop(desktop):
        raise c.WinError(c.get_last_error())

    from private_window_probe import find_game_windows
    from window_snapshot import capture
    windows = find_game_windows()
    if len(windows) != 1:
        raise RuntimeError(f'Expected one private game window, found {windows!r}')
    user.IsWindowUnicode.argtypes = [w.HWND]
    user.IsWindowUnicode.restype = w.BOOL
    kernel = c.WinDLL('kernel32', use_last_error=True)
    kernel.GetACP.restype = w.UINT
    print(f'window_unicode={bool(user.IsWindowUnicode(windows[0][1]))} sender_acp={kernel.GetACP()}',flush=True)
    output.mkdir(parents=True, exist_ok=True)
    if type_text is not None:
        if not (1 <= len(type_text) <= 32 and type_text.isascii() and type_text.isprintable()):
            raise ValueError('invalid synthetic private input')
        hwnd = windows[0][1]
        user.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
        for char in type_text:
            if not user.PostMessageW(hwnd, 0x102, ord(char), 1):
                raise c.WinError(c.get_last_error())
    elif key_mode:
        key = int(sys.argv[2].split('=', 1)[1])
        if not (1 <= key <= 255):
            raise ValueError('invalid virtual key')
        hwnd = windows[0][1]
        user.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
        for code in (0x100, 0x101):
            if not user.PostMessageW(hwnd, code, key, 0):
                raise c.WinError(c.get_last_error())
            time.sleep(.075)
    elif click_mode is not None or drag_mode or battle_trigger or battle_watch:
        prefix = '--battle-trigger=' if battle_trigger else click_mode
        if drag_mode:
            x, y, end_x, end_y = (int(part) for part in sys.argv[2].split('=', 1)[1].split(','))
        else:
            x, y = (0, 0) if battle_watch else (int(part) for part in sys.argv[2][len(prefix):].split(','))
        if not (0 <= x < 4096 and 0 <= y < 2160):
            raise ValueError('click outside original game client')
        hwnd = windows[0][1]
        user.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
        def post(code, point, key=0):
            if not user.PostMessageW(hwnd, code, key, point):
                raise c.WinError(c.get_last_error())
            time.sleep(.075)
        def click_at(px, py, second=None):
            point = (py << 16) | px
            if click_mode == '--right=':
                post(0x200, point)
                post(0x204, point, 2)
                post(0x205, point)
                return
            post(0x200, point)
            post(0x201, point, 1)
            post(0x202, point)
            if second is not None:
                post(0x203 if second == '--dblmsg=' else 0x201, point, 1)
                post(0x202, point)
        if battle_trigger or battle_watch:
            if len(sys.argv) != 4:
                raise ValueError('battle watch needs private server log path')
            log = Path(sys.argv[3])
            # The server may be appending a multibyte log line mid-read.
            marker = b'DIAGNOSTIC_BATTLE_TRANSITION_SENT'
            before = log.read_bytes().count(marker)
            (output / 'ready.txt').write_text(str(before), encoding='ascii')
            if battle_trigger:
                click_at(x, y)
            deadline = time.monotonic() + (600 if battle_watch else 12)
            while time.monotonic() < deadline:
                if log.read_bytes().count(marker) > before:
                    time.sleep(.8)
                    click_at(515, 157)
                    print('battle_target_clicked_after_transition', flush=True)
                    break
                time.sleep(.1)
            else:
                raise RuntimeError('private battle transition not seen after movement')
        elif drag_mode:
            start = (y << 16) | x
            post(0x200, start)
            post(0x201, start, 1)
            for step in range(1, 11):
                px = x + (end_x - x) * step // 10
                py = y + (end_y - y) * step // 10
                post(0x200, (py << 16) | px, 1)
            post(0x202, (end_y << 16) | end_x)
        else:
            click_at(x, y, click_mode if click_mode != '--click=' else None)
    elif self_text is not None:
        if not (1 <= len(self_text) <= 16) or any(ord(char) < 0x20 for char in self_text):
            raise ValueError('invalid private self-chat text')
        hwnd = windows[0][1]
        user.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
        for code, key in ((0x200, 0), (0x201, 1), (0x202, 0)):
            if not user.PostMessageW(hwnd, code, key, (584 << 16) | 200):
                raise c.WinError(c.get_last_error())
            time.sleep(.2)
        user.PostMessageA.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
        units = self_text.encode('cp936') if ansi_input else (ord(char) for char in self_text)
        post = user.PostMessageA if ansi_input else user.PostMessageW
        for unit in units:
            if not post(hwnd, 0x286 if ime_input else 0x102, unit, 1):
                raise c.WinError(c.get_last_error())
        user.PostMessageW(hwnd, 0x100, 0x0d, 0)
        user.PostMessageW(hwnd, 0x101, 0x0d, 0)
    elif not observe_only:
        process = subprocess.Popen([sys.executable, str(sender), '--immediate', '--mirror-recipient'])
    if not no_capture:
        time.sleep(3)
        screenshots = capture(windows[0][0], output)
        print('private_chat_capture=' + ','.join(str(row.get('image')) for row in screenshots), flush=True)
    if sender is not None:
        result = process.wait(timeout=25)
        if result:
            raise RuntimeError(f'Native chat sender failed: {result}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
