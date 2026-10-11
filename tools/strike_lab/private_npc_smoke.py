"""No-screenshot, isolated-desktop original-client NPC click probe.

The caller must provide an isolated database and server log. This script only
posts input to the game window on its private desktop and writes probe data.
"""
import json
import os
from pathlib import Path
import sys
import time

import private_unpacked_smoke as game
import private_viewport_probe as viewport
import private_npc_memory as native_memory


def marker_count(path, marker):
    return path.read_bytes().count(marker) if path.exists() else 0


def main():
    output, database, server_log = map(Path, sys.argv[1:4])
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {'stages': [], 'attempts': []}
    try:
        deadline = time.monotonic() + 50
        hwnd = pid = None
        while time.monotonic() < deadline:
            hwnd, pid = game.game_window()
            if hwnd:
                break
            time.sleep(.2)
        if not hwnd:
            raise RuntimeError('GAME_WINDOW_NOT_FOUND')
        result['pid'] = pid
        result['initial_client_size'] = viewport.dimensions(hwnd)
        result['stages'].append('game_window')
        time.sleep(2)
        game.click(hwnd, 512, 464)
        time.sleep(3)
        game.click(hwnd, 437, 232)
        game.type_ascii(hwnd, 'codexlab')
        game.click(hwnd, 437, 263)
        game.type_ascii(hwnd, 'labtest2345')
        game.click(hwnd, 452, 304)
        result['stages'].append('login_submitted')
        time.sleep(4)
        game.click(hwnd, 330, 145)
        game.click(hwnd, 452, 413)
        time.sleep(4)
        game.click(hwnd, 330, 150)
        game.click(hwnd, 452, 376)
        time.sleep(4)
        game.click(hwnd, 452, 370)
        result['stages'].append('character_selected')
        time.sleep(8)
        result['position_at_entry'] = game.position(database)
        result['world_client_at_entry'] = viewport.dimensions(hwnd)
        expected_exe = Path(__file__).resolve().parents[3] / 'God2' / 'God2.exe'
        result['native_guides'] = native_memory.read_guides(pid, expected_exe)
        result['world_client_after_scan'] = viewport.dimensions(hwnd)
        baseline = marker_count(server_log, b'DIAGNOSTIC_NPC_REQUEST_ACCEPTED')
        result['npc_spawn_logged'] = b'DIAGNOSTIC_TOWN_GUIDES_SENT' in server_log.read_bytes()
        result['stages'].append('world_entered')
        # The read-only actor pool stores current client projection pixels.
        # Only issue a click when the observed viewport is exactly 800x600.
        if os.environ.get('GOD2_NPC_GEOMETRY_ONLY') == '1':
            points = []
            result['npc_click_skipped'] = 'GEOMETRY_PROBE_ONLY'
        elif (result['world_client_after_scan'] == [800, 600]
              and result['native_guides'].get('projected')):
            projected = result['native_guides']['projected'][0]
            points = [(round(projected[0]), round(projected[1]))]
        else:
            points = []
            result['npc_click_skipped'] = 'UNQUALIFIED_VIEWPORT'
        for x, y in points:
            if not game.game_window()[0]:
                raise RuntimeError('GAME_WINDOW_CLOSED_DURING_NPC_PROBE')
            game.click(hwnd, x, y)
            time.sleep(1.2)
            pos = game.position(database)
            accepted = marker_count(server_log, b'DIAGNOSTIC_NPC_REQUEST_ACCEPTED') > baseline
            result['attempts'].append({'point': [x, y], 'position': pos,
                                       'npc_accepted': accepted})
            if accepted or (pos and (abs(pos[3]-111)>4 or abs(pos[4]-70)>4)):
                break
        for _ in range(15):
            if marker_count(server_log, b'DIAGNOSTIC_NPC_REQUEST_ACCEPTED') > baseline:
                break
            time.sleep(1)
        result['npc_accepted'] = marker_count(server_log, b'DIAGNOSTIC_NPC_REQUEST_ACCEPTED') > baseline
        result['position_final'] = game.position(database)
        result['window_alive'] = bool(game.game_window()[0])
        game.user.PostMessageW(hwnd, 0x10, 0, 0)
    except Exception as exc:
        result['error'] = repr(exc)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if not result.get('error') else 1


if __name__ == '__main__':
    raise SystemExit(main())
