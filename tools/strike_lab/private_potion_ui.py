"""Exercise the original client's item UI on an isolated Windows desktop.

The caller supplies an independent SQLite backup and private server log. This
script never switches the user's input desktop or captures a screenshot.
"""
import ctypes as c
from ctypes import wintypes as w
import json
import os
from pathlib import Path
import psutil
import sqlite3
import subprocess
import sys
import time

user = c.WinDLL('user32', use_last_error=True)
user.EnumWindows.argtypes = [c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM), w.LPARAM]
user.GetClassNameW.argtypes = [w.HWND, w.LPWSTR, c.c_int]
user.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
user.GetClientRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
user.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]


def game_window():
    found = []

    @c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
    def visit(hwnd, _):
        name = c.create_unicode_buffer(128)
        if user.GetClassNameW(hwnd, name, len(name)) and name.value == 'XianJieWndClass':
            pid = w.DWORD()
            user.GetWindowThreadProcessId(hwnd, c.byref(pid))
            found.append((hwnd, pid.value))
        return True

    user.EnumWindows(visit, 0)
    return found[0] if len(found) == 1 else (None, None)


def click(hwnd, x, y, double=False, interval=.15):
    rect = w.RECT()
    if not user.GetClientRect(hwnd, c.byref(rect)) or rect.right <= 0 or rect.bottom <= 0:
        raise RuntimeError('GAME_WINDOW_RECT_UNAVAILABLE')
    x = round(x * rect.right / 800)
    y = round(y * rect.bottom / 600)
    pos = (y << 16) | x
    events = [(0x200, 0), (0x201, 1), (0x202, 0)]
    if double:
        events.extend([(0x203, 1), (0x202, 0)])
    for message, key in events:
        if not user.PostMessageW(hwnd, message, key, pos):
            raise OSError(c.get_last_error(), 'PostMessageW click failed')
        time.sleep(interval)
    return [x, y]


def type_ascii(hwnd, value):
    for char in value:
        if not user.PostMessageW(hwnd, 0x102, ord(char), 1):
            raise OSError(c.get_last_error(), 'PostMessageW character failed')


def drag(hwnd, start, end):
    rect = w.RECT()
    if not user.GetClientRect(hwnd, c.byref(rect)):
        raise RuntimeError('GAME_WINDOW_RECT_UNAVAILABLE')
    sx, sy = round(start[0] * rect.right / 800), round(start[1] * rect.bottom / 600)
    ex, ey = round(end[0] * rect.right / 800), round(end[1] * rect.bottom / 600)
    for code, key, x, y in [(0x200, 0, sx, sy), (0x201, 1, sx, sy)]:
        if not user.PostMessageW(hwnd, code, key, (y << 16) | x):
            raise OSError(c.get_last_error(), 'PostMessageW drag start failed')
        time.sleep(.12)
    for step in range(1, 11):
        x = sx + (ex - sx) * step // 10
        y = sy + (ey - sy) * step // 10
        if not user.PostMessageW(hwnd, 0x200, 1, (y << 16) | x):
            raise OSError(c.get_last_error(), 'PostMessageW drag move failed')
        time.sleep(.08)
    if not user.PostMessageW(hwnd, 0x202, 0, (ey << 16) | ex):
        raise OSError(c.get_last_error(), 'PostMessageW drag end failed')
    return [[sx, sy], [ex, ey]]


def state(db):
    with sqlite3.connect(f'file:{db.as_posix()}?mode=ro', uri=True) as conn:
        slot = conn.execute('SELECT item_id,count,revision FROM diagnostic_inventory_slots '
                            'WHERE character_id=1 AND slot=0').fetchone()
        resources = conn.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources '
                                 'WHERE character_id=1').fetchone()
        return {'slot': slot, 'resources': resources}


def ui_state(pid):
    helper = Path(__file__).with_name('private_inventory_memory.py')
    output = subprocess.check_output([sys.executable, str(helper), str(pid),
                                      str(int(os.environ.get('GOD2_PRIVATE_POTION_ITEM_ID', '3107')))], timeout=12)
    matches = json.loads(output)['matches']
    if len(matches) != 1:
        raise RuntimeError(f'EXPECTED_ONE_NATIVE_SLOT_RECORD_GOT_{len(matches)}')
    return matches[0]


def trace_drag(hwnd, pid, start, end):
    rect = w.RECT()
    if not user.GetClientRect(hwnd, c.byref(rect)):
        raise RuntimeError('GAME_WINDOW_RECT_UNAVAILABLE')
    sx, sy = round(start[0] * rect.right / 800), round(start[1] * rect.bottom / 600)
    ex, ey = round(end[0] * rect.right / 800), round(end[1] * rect.bottom / 600)
    origin = (sy << 16) | sx
    destination = (ey << 16) | ex
    user.PostMessageW(hwnd, 0x200, 0, origin)
    user.PostMessageW(hwnd, 0x201, 1, origin)
    time.sleep(.35)
    after_down = ui_state(pid)
    for step in range(1, 11):
        x = sx + (ex - sx) * step // 10
        y = sy + (ey - sy) * step // 10
        user.PostMessageW(hwnd, 0x200, 1, (y << 16) | x)
        time.sleep(.08)
    time.sleep(.25)
    before_up = ui_state(pid)
    user.PostMessageW(hwnd, 0x202, 0, destination)
    time.sleep(.25)
    after_up = ui_state(pid)
    return {'points': [[sx, sy], [ex, ey]], 'after_down': after_down,
            'before_up': before_up, 'after_up': after_up}


def trace_press(hwnd, pid, point):
    rect = w.RECT()
    if not user.GetClientRect(hwnd, c.byref(rect)):
        raise RuntimeError('GAME_WINDOW_RECT_UNAVAILABLE')
    x, y = round(point[0] * rect.right / 800), round(point[1] * rect.bottom / 600)
    pos = (y << 16) | x
    user.PostMessageW(hwnd, 0x200, 0, pos)
    user.PostMessageW(hwnd, 0x201, 1, pos)
    time.sleep(.3)
    after_down = ui_state(pid)
    user.PostMessageW(hwnd, 0x202, 0, pos)
    time.sleep(.3)
    return {'point': [x, y], 'after_down': after_down, 'after_up': ui_state(pid)}


def main():
    output, db, server_log = map(Path, sys.argv[1:4])
    item_id = int(os.environ.get('GOD2_PRIVATE_POTION_ITEM_ID', '3107'))
    if item_id not in (3101, 3107):
        raise ValueError('Private potion UI supports only 3101 and 3107')
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {'item_id': item_id, 'stages': [], 'before': state(db)}
    hwnd = None
    try:
        if result['before']['slot'][:2] != (item_id, 3) or (
                item_id == 3107 and result['before']['resources'][2:4] != (2, 80)) or (
                item_id == 3101 and not (0 < result['before']['resources'][0] <
                                         result['before']['resources'][1])):
            raise RuntimeError('ISOLATED_FIXTURE_UNEXPECTED')
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            hwnd, pid = game_window()
            if hwnd:
                break
            time.sleep(.2)
        if not hwnd:
            raise RuntimeError('GAME_WINDOW_NOT_FOUND')
        result['pid'] = pid
        rect = w.RECT()
        user.GetClientRect(hwnd, c.byref(rect))
        result['window_size'] = [rect.right, rect.bottom]
        result['stages'].append('game_window')
        time.sleep(2)
        click(hwnd, 512, 464)
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
        time.sleep(4)
        click(hwnd, 330, 150)
        click(hwnd, 452, 376)
        time.sleep(4)
        click(hwnd, 452, 370)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if 'WORLD_INITIALIZER_TAIL_ACCEPTED' in server_log.read_text(
                    encoding='utf-8', errors='replace'):
                break
            time.sleep(.2)
        else:
            raise RuntimeError('WORLD_INITIALIZER_NOT_ACCEPTED')
        time.sleep(3)
        result['stages'].append('world_entry_attempted')
        result['after_login'] = state(db)
        user.GetClientRect(hwnd, c.byref(rect))
        result['world_window_size'] = [rect.right, rect.bottom]
        result['inventory_button_point'] = click(hwnd, 708, 584)
        time.sleep(2)
        result['stages'].append('inventory_open_attempted')
        if '--trace-panel' in sys.argv[4:]:
            result['ui_after_open'] = ui_state(pid)
            result['stages'].append('action_widget_geometry_read')
        elif '--trace-native-shortcut' in sys.argv[4:]:
            result['ui_after_open'] = ui_state(pid)
            shortcuts = [child for child in result['ui_after_open']['action_widget_children']
                         if child['index'] == 10]
            if len(shortcuts) != 1 or shortcuts[0]['flags'] & 4 == 0:
                raise RuntimeError('NATIVE_SHORTCUT_10_NOT_FOUND')
            left, top, right, bottom = shortcuts[0]['rect']
            target = ((left + right) // 2, (top + bottom) // 2)
            result['drag_trace'] = trace_drag(hwnd, pid, (580, 302), target)
            result['stages'].append('native_shortcut_drag_traced')
            for message in (0x100, 0x101):
                user.PostMessageW(hwnd, message, 0x70, 0)
                time.sleep(.12)
            result['ui_after_f1'] = ui_state(pid)
            result['stages'].append('f1_pressed')
        elif '--trace-topbar' in sys.argv[4:]:
            result['action_clicks'] = [trace_press(hwnd, pid, point)
                                       for point in [(118, 45), (162, 45), (207, 45)]]
            result['stages'].append('topbar_clicks_traced')
        elif '--trace-action-click' in sys.argv[4:]:
            result['action_clicks'] = [trace_press(hwnd, pid, point)
                                       for point in [(580, 247), (650, 247), (700, 247)]]
            result['stages'].append('action_clicks_traced')
        elif '--trace-drag' in sys.argv[4:]:
            result['ui_after_open'] = ui_state(pid)
            result['drag_trace'] = trace_drag(hwnd, pid, (580, 302), (580, 247))
            result['stages'].append('drag_state_traced')
        elif '--trace-assignment' in sys.argv[4:]:
            result['ui_after_open'] = ui_state(pid)
            result['item_point'] = click(hwnd, 580, 302)
            result['ui_after_item_click'] = ui_state(pid)
            result['hotbar_drag_points'] = drag(hwnd, (580, 302), (580, 247))
            result['ui_after_hotbar_drag'] = ui_state(pid)
            result['hotbar_point'] = click(hwnd, 580, 247)
            result['ui_after_hotbar_click'] = ui_state(pid)
            result['stages'].append('assignment_state_traced')
            for message in (0x100, 0x101):
                user.PostMessageW(hwnd, message, 0x70, 0)
                time.sleep(.12)
            result['ui_after_f1'] = ui_state(pid)
            result['stages'].append('f1_pressed')
        elif '--hotbar' in sys.argv[4:] or '--assign-click' in sys.argv[4:]:
            if '--assign-click' in sys.argv[4:]:
                result['item_point'] = click(hwnd, 580, 302)
                result['hotbar_point'] = click(hwnd, 580, 247)
                result['stages'].append('item_then_hotbar_clicked')
            else:
                result['hotbar_drag_points'] = drag(hwnd, (580, 302), (580, 247))
                result['stages'].append('item_dragged_to_hotbar')
            time.sleep(1)
            for message in (0x100, 0x101):
                user.PostMessageW(hwnd, message, 0x70, 0)
                time.sleep(.12)
            result['stages'].append('f1_pressed')
        else:
            result['item_point'] = click(hwnd, 580, 302, double=True)
            result['stages'].append('item_double_clicked')
        if '--select-self' in sys.argv[4:]:
            time.sleep(1)
            click(hwnd, 400, 270)
            result['stages'].append('self_target_clicked')
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            current = state(db)
            if current != result['before']:
                break
            time.sleep(.2)
        result['after_use'] = current
        result['game_window_alive'] = game_window()[0] == hwnd
        result['server_log_tail'] = server_log.read_text(encoding='utf-8', errors='replace').splitlines()[-35:]
        expected_resources = ((min(result['before']['resources'][0] + 100,
                                   result['before']['resources'][1]),
                               result['before']['resources'][1],
                               result['before']['resources'][2],
                               result['before']['resources'][3]) if item_id == 3101
                              else (result['before']['resources'][0],
                                    result['before']['resources'][1], 52, 80))
        result['accepted'] = (current['slot'][:2] == (item_id, 2) and
                              tuple(current['resources'][:4]) == expected_resources and
                              current['resources'][4] == result['before']['resources'][4] + 1 and
                              result['game_window_alive'])
    except Exception as exc:
        result['error'] = repr(exc)
    finally:
        if hwnd:
            user.PostMessageW(hwnd, 0x10, 0, 0)
            # Only the disposable private-lab process launched for this test.
            try:
                game = psutil.Process(pid)
                if game.name().lower() in ('god2-private-lab-2598.exe',
                                          'god2-current-lab-2598.exe'):
                    game.terminate()
            except psutil.NoSuchProcess:
                pass
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if result.get('accepted') else 1


if __name__ == '__main__':
    raise SystemExit(main())
