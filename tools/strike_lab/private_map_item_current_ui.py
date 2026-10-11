"""Exercise C2S25 map-item UI with the current client on a private desktop."""
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import psutil
import sqlite3
import sys
import time

from private_potion_ui import click, game_window, type_ascii, user


def state(db):
    with sqlite3.connect(f'file:{db.as_posix()}?mode=ro', uri=True) as conn:
        return {'slot': conn.execute(
                    'SELECT item_id,count,revision FROM diagnostic_inventory_slots '
                    'WHERE character_id=4 AND slot=0').fetchone(),
                'position': conn.execute(
                    'SELECT area,scene,x,y,revision FROM recovered_positions '
                    'WHERE character_id=4').fetchone()}


def double_click_message(hwnd, x, y):
    rect = w.RECT()
    if not user.GetClientRect(hwnd, c.byref(rect)):
        raise RuntimeError('GAME_WINDOW_RECT_UNAVAILABLE')
    px = round(x * rect.right / 800)
    py = round(y * rect.bottom / 600)
    point = (py << 16) | px
    for code, key in ((0x200, 0), (0x201, 1), (0x202, 0),
                      (0x203, 1), (0x202, 0)):
        if not user.PostMessageW(hwnd, code, key, point):
            raise OSError(c.get_last_error(), 'PostMessageW item double click failed')
        time.sleep(.12)
    return [px, py]


def main():
    output, db, server_log = map(Path, sys.argv[1:4])
    result = {'stages': [], 'before': state(db)}
    hwnd = None
    pid = None
    try:
        if result['before']['slot'][:2] != (5569, 1) or result['before']['position'][:2] != (2, 4):
            raise RuntimeError('ISOLATED_MAP_FIXTURE_UNEXPECTED')
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            hwnd, pid = game_window()
            if hwnd:
                break
            time.sleep(.2)
        if not hwnd:
            raise RuntimeError('GAME_WINDOW_NOT_FOUND')
        result['pid'] = pid
        result['stages'].append('game_window')
        time.sleep(2)
        click(hwnd, 512, 464)
        time.sleep(3)
        click(hwnd, 437, 232)
        type_ascii(hwnd, 'codexslow')
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
        result['stages'].append('world_entry_attempted')
        time.sleep(3)
        click(hwnd, 708, 584)
        time.sleep(2)
        result['stages'].append('inventory_open_attempted')
        result['item_point'] = double_click_message(hwnd, 580, 302)
        result['stages'].append('map_item_double_clicked')
        marker = 'DIAGNOSTIC_TOWN_MAP_CANDIDATE'
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if marker in server_log.read_text(encoding='utf-8', errors='replace'):
                break
            time.sleep(.2)
        result['server_candidate_seen'] = marker in server_log.read_text(
            encoding='utf-8', errors='replace')
        result['after'] = state(db)
        result['game_window_alive'] = game_window()[0] == hwnd
        result['accepted'] = (result['server_candidate_seen'] and
                              result['after'] == result['before'] and
                              result['game_window_alive'])
    except Exception as exc:
        result['error'] = repr(exc)
    finally:
        if hwnd:
            user.PostMessageW(hwnd, 0x10, 0, 0)
        if pid:
            try:
                game = psutil.Process(pid)
                if game.name().lower() == 'god2-current-lab-2598.exe':
                    game.terminate()
            except psutil.NoSuchProcess:
                pass
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if result.get('accepted') else 1


if __name__ == '__main__':
    raise SystemExit(main())
