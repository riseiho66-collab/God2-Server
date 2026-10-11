"""Probe physical skill-menu input in a private current-client battle."""
import json
from pathlib import Path
import psutil
import sqlite3
import subprocess
import sys
import time

from private_potion_ui import click, game_window, type_ascii, user


def db_state(db):
    with sqlite3.connect(f'file:{db.as_posix()}?mode=ro', uri=True) as conn:
        return {'position': conn.execute('SELECT area,scene,x,y,revision FROM recovered_positions '
                                         'WHERE character_id=4').fetchone(),
                'settlements': conn.execute('SELECT count(*) FROM battle_settlements').fetchone()[0],
                'resources': conn.execute('SELECT hp,max_hp,mp,max_mp,revision FROM character_resources '
                                          'WHERE character_id=4').fetchone()}


def wait_log(path, marker, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if marker in path.read_text(encoding='utf-8', errors='replace'):
            return True
        time.sleep(.2)
    return False


def native_ui(pid):
    helper = Path(__file__).with_name('private_inventory_memory.py')
    raw = subprocess.check_output([sys.executable, str(helper), str(pid), '5569'], timeout=12)
    parsed = json.loads(raw)
    return parsed['matches']


def main():
    output, db, server_log = map(Path, sys.argv[1:4])
    skill_x, skill_y = (int(value) for value in sys.argv[4].split(',')) if len(sys.argv) > 4 else (420, 283)
    fast = '--fast' in sys.argv[4:]
    immediate = '--immediate' in sys.argv[4:]
    delay_ms = next((int(flag.split('=', 1)[1]) for flag in sys.argv[4:]
                     if flag.startswith('--delay-ms=')), 0)
    if not 0 <= delay_ms <= 1500:
        raise ValueError('skill click delay outside bounded observation window')
    capture_requested = '--capture' in sys.argv[4:]
    observe_expiry = '--observe-expiry' in sys.argv[4:]
    action2_count = next((int(flag.split('=', 1)[1]) for flag in sys.argv[4:]
                          if flag.startswith('--observe-action2-count=')), 1)
    if not 1 <= action2_count <= 10:
        raise ValueError('action2 observation count outside bounded range')
    observe_defeat = '--observe-defeat' in sys.argv[4:]
    post_expiry_ms = next((int(flag.split('=', 1)[1]) for flag in sys.argv[4:]
                           if flag.startswith('--post-expiry-ms=')), 0)
    if not 0 <= post_expiry_ms <= 10000:
        raise ValueError('post-expiry wait outside bounded observation window')
    if not (0 <= skill_x < 800 and 0 <= skill_y < 600):
        raise ValueError('skill probe point outside baseline game area')
    result = {'stages': [], 'before': db_state(db)}
    hwnd = None
    pid = None
    try:
        if result['before']['position'][:4] != (2, 15, 18, 12) or result['before']['settlements']:
            raise RuntimeError('ISOLATED_BATTLE_FIXTURE_UNEXPECTED')
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
        if not wait_log(server_log, 'WORLD_INITIALIZER_TAIL_ACCEPTED', 20):
            raise RuntimeError('WORLD_INITIALIZER_NOT_ACCEPTED')
        result['stages'].append('world_entry_attempted')
        if not wait_log(server_log, 'DIAGNOSTIC_BATTLE_TRANSITION_SENT', 20):
            raise RuntimeError('BATTLE_TRANSITION_NOT_SENT')
        result['stages'].append('battle_transition_sent')
        if not wait_log(server_log, 'DIAGNOSTIC_VITALS88_SENT_AFTER_TIMER36', 20):
            raise RuntimeError('BATTLE_VITALS_NOT_SENT')
        result['stages'].append('battle_vitals_sent')
        if observe_expiry:
            for index in range(action2_count):
                deadline = time.monotonic() + 42
                while time.monotonic() < deadline:
                    if server_log.read_text(encoding='utf-8', errors='replace').count(
                            'DIAGNOSTIC_PLAYER_ACTION2') > index:
                        break
                    time.sleep(.2)
                else:
                    raise RuntimeError(f'BATTLE_ACTION2_{index + 1}_NOT_RECEIVED')
            if post_expiry_ms:
                time.sleep(post_expiry_ms / 1000)
            result['stages'].append('battle_action2_after_command_window')
            if observe_defeat:
                if not wait_log(server_log, 'DIAGNOSTIC_FINISHED_BATTLE_RELEASED', 20):
                    raise RuntimeError('BATTLE_DEFEAT_NOT_RELEASED')
                result['stages'].append('battle_defeat_released')
            result['after_skill_menu'] = db_state(db)
            result['log_after_skill_menu'] = server_log.read_text(
                encoding='utf-8', errors='replace').splitlines()[-30:]
            result['game_window_alive'] = game_window()[0] == hwnd
            return 0
        if fast and not immediate:
            if not wait_log(server_log, 'DIAGNOSTIC_PLAYER_ACTION2', 10):
                raise RuntimeError('BATTLE_ACTION2_NOT_RECEIVED')
            result['stages'].append('battle_action2_received')
        elif not immediate:
            time.sleep(2)
        if capture_requested and not fast:
            from window_snapshot import capture
            capture_dir = output.parent / 'battle-ui'
            capture_dir.mkdir(parents=True, exist_ok=True)
            result['battle_ui_capture'] = capture(pid, capture_dir)
        if not fast:
            result['ui_before_skill_menu'] = native_ui(pid)
        if delay_ms:
            time.sleep(delay_ms / 1000)
        result['skill_click_started_at'] = time.time()
        result['skill_menu_point'] = click(hwnd, skill_x, skill_y, interval=.01 if fast else .15)
        result['stages'].append('skill_menu_clicked')
        time.sleep(.2 if fast else 4)
        if capture_requested and fast:
            from window_snapshot import capture
            capture_dir = output.parent / 'after-skill-click'
            capture_dir.mkdir(parents=True, exist_ok=True)
            result['after_click_capture'] = capture(pid, capture_dir)
        result['ui_after_skill_menu'] = native_ui(pid)
        result['after_skill_menu'] = db_state(db)
        result['log_after_skill_menu'] = server_log.read_text(
            encoding='utf-8', errors='replace').splitlines()[-30:]
        result['game_window_alive'] = game_window()[0] == hwnd
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
    required = 'battle_defeat_released' if observe_defeat else 'battle_action2_after_command_window'
    return 0 if ('skill_menu_clicked' in result['stages'] or required in result['stages']) and result.get('game_window_alive') else 1


if __name__ == '__main__':
    raise SystemExit(main())
