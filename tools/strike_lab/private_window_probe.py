"""Capture a game's window from the private desktop inherited from the runner."""
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import sys
import time

from window_snapshot import capture


def find_game_windows():
    user = c.WinDLL('user32', use_last_error=True)
    callback = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    user.EnumWindows.argtypes = [callback, w.LPARAM]
    user.GetWindowTextW.argtypes = [w.HWND, w.LPWSTR, c.c_int]
    user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
    found = []

    @callback
    def visit(hwnd, _):
        title = c.create_unicode_buffer(1024)
        user.GetWindowTextW(hwnd, title, len(title))
        if title.value.startswith('XianJieZhuan'):
            pid = w.DWORD()
            user.GetWindowThreadProcessId(hwnd, c.byref(pid))
            found.append((pid.value, hwnd, title.value))
        return True

    user.EnumWindows(visit, 0)
    return found


def main():
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    account_options = [arg.split('=', 1)[1] for arg in sys.argv[2:] if arg.startswith('--account=')]
    account = account_options[0] if account_options else 'codexlab'
    if len(account_options) > 1 or not (3 <= len(account) <= 16 and account.isascii() and account.isalnum()):
        raise ValueError('invalid synthetic account name')
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        windows = find_game_windows()
        if windows:
            time.sleep(4)
            rows = capture(windows[0][0], output)
            action = None
            after = None
            if '--click-menu' in sys.argv[2:] or '--login' in sys.argv[2:] or '--select-server' in sys.argv[2:] or '--select-channel' in sys.argv[2:]:
                user = c.WinDLL('user32', use_last_error=True)
                user.GetClientRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
                user.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
                hwnd = windows[0][1]
                area = w.RECT()
                if user.GetClientRect(hwnd, c.byref(area)) and (area.right, area.bottom) in ((800, 600), (1024, 768)):
                    def click(x800, y600):
                        x = round(area.right * x800 / 800)
                        y = round(area.bottom * y600 / 600)
                        position = (y << 16) | x
                        # Message delivery targets the private window only.
                        sent = []
                        for code, key in ((0x200, 0), (0x201, 1), (0x202, 0)):
                            sent.append(bool(user.PostMessageW(hwnd, code, key, position)))
                            time.sleep(.3)
                        return {'point': [x, y], 'sent': sent}
                    sent = click(512, 464)
                    action = {'method': 'PostMessageW', 'window': [area.right, area.bottom],
                              **sent}
                    time.sleep(4)
                    after = capture(windows[0][0], output)
                    if '--login' in sys.argv[2:] or '--select-server' in sys.argv[2:] or '--select-channel' in sys.argv[2:]:
                        def type_text(value):
                            return [bool(user.PostMessageW(hwnd, 0x102, ord(char), 1))
                                    for char in value]
                        account_click = click(437, 232)
                        account_sent = type_text(account)
                        password_click = click(437, 263)
                        password_sent = type_text('labtest2345')
                        time.sleep(1)
                        filled = capture(windows[0][0], output)
                        progress = {'windows': windows, 'capture': rows, 'action': action,
                                    'after': after, 'filled': filled,
                                    'login': {'account_click': account_click,
                                              'account_chars_sent': account_sent,
                                              'password_click': password_click,
                                              'password_chars_sent': password_sent}}
                        (output / 'private-observation.json').write_text(json.dumps(
                            progress, ensure_ascii=False, indent=2), encoding='utf-8')
                        progress['login']['submit_click'] = click(452, 304)
                        time.sleep(4)
                        progress['submitted'] = capture(windows[0][0], output)
                        (output / 'private-observation.json').write_text(json.dumps(
                            progress, ensure_ascii=False, indent=2), encoding='utf-8')
                        if '--select-server' in sys.argv[2:] or '--select-channel' in sys.argv[2:]:
                            progress['server_row_click'] = click(330, 145)
                            progress['server_confirm_click'] = click(452, 413)
                            time.sleep(4)
                            progress['server_selected'] = capture(windows[0][0], output)
                            (output / 'private-observation.json').write_text(json.dumps(
                                progress, ensure_ascii=False, indent=2), encoding='utf-8')
                            if '--select-channel' in sys.argv[2:]:
                                progress['channel_row_click'] = click(330, 150)
                                progress['channel_confirm_click'] = click(452, 376)
                                time.sleep(4)
                                progress['channel_selected'] = capture(windows[0][0], output)
                                (output / 'private-observation.json').write_text(json.dumps(
                                    progress, ensure_ascii=False, indent=2), encoding='utf-8')
                                if '--interactive' in sys.argv[2:]:
                                    commands = output / 'commands.jsonl'
                                    offset = 0
                                    deadline = time.monotonic() + 600
                                    while time.monotonic() < deadline:
                                        if not commands.exists():
                                            time.sleep(.2)
                                            continue
                                        with commands.open('r', encoding='utf-8') as stream:
                                            stream.seek(offset)
                                            line = stream.readline()
                                            offset = stream.tell()
                                        if not line:
                                            time.sleep(.2)
                                            continue
                                        try:
                                            command = json.loads(line)
                                            ident = int(command['id'])
                                            verb = command['action']
                                            if verb == 'quit':
                                                return 0
                                            if verb == 'click':
                                                x, y = int(command['x']), int(command['y'])
                                                if not (0 <= x < 800 and 0 <= y < 600):
                                                    raise ValueError('click outside game client')
                                                result = click(x, y)
                                            elif verb == 'type':
                                                value = str(command['text'])
                                                if len(value) > 32 or not value.isascii():
                                                    raise ValueError('test text invalid')
                                                result = type_text(value)
                                            elif verb == 'snapshot':
                                                result = True
                                            else:
                                                raise ValueError('unknown command')
                                            time.sleep(max(0, min(5, float(command.get('wait', 2)))))
                                            image_rows = capture(windows[0][0], output)
                                            reply = {'id': ident, 'action': verb,
                                                     'result': result, 'capture': image_rows}
                                        except Exception as error:
                                            reply = {'id': command.get('id'), 'error': repr(error)}
                                        (output / f'response-{ident}.json').write_text(json.dumps(
                                            reply, ensure_ascii=False, indent=2), encoding='utf-8')
                        return 0
                else:
                    action = {'error': 'UNEXPECTED_CLIENT_SIZE'}
            (output / 'private-observation.json').write_text(json.dumps({
                'windows': windows, 'capture': rows, 'action': action, 'after': after,
            }, ensure_ascii=False, indent=2), encoding='utf-8')
            return 0
        time.sleep(.5)
    (output / 'private-observation.json').write_text(json.dumps({
        'error': 'GAME_WINDOW_NOT_FOUND',
    }), encoding='utf-8')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
