"""Measure and restore only the isolated desktop's game window; no screenshots."""
import json
from pathlib import Path
import sys
import time

import private_unpacked_smoke as game


def dimensions(hwnd):
    rect = game.w.RECT()
    if not game.user.GetClientRect(hwnd, game.c.byref(rect)):
        raise OSError(game.c.get_last_error(), 'GetClientRect failed')
    return [rect.right, rect.bottom]


def set_client_size(hwnd, width, height):
    game.user.GetWindowLongW.argtypes = [game.w.HWND, game.c.c_int]
    game.user.GetWindowLongW.restype = game.c.c_long
    style = game.user.GetWindowLongW(hwnd, -16) & 0xffffffff
    ex_style = game.user.GetWindowLongW(hwnd, -20) & 0xffffffff
    game.user.ShowWindow.argtypes = [game.w.HWND, game.c.c_int]
    game.user.ShowWindow(hwnd, 9)
    frame = game.w.RECT(0, 0, width, height)
    game.user.AdjustWindowRectEx.argtypes = [game.c.POINTER(game.w.RECT), game.w.DWORD,
                                             game.w.BOOL, game.w.DWORD]
    if not game.user.AdjustWindowRectEx(game.c.byref(frame), style, False, ex_style):
        raise OSError(game.c.get_last_error(), 'AdjustWindowRectEx failed')
    game.user.SetWindowPos.argtypes = [game.w.HWND, game.w.HWND, game.c.c_int,
                                       game.c.c_int, game.c.c_int, game.c.c_int,
                                       game.w.UINT]
    outer = [frame.right-frame.left, frame.bottom-frame.top]
    changed = bool(game.user.SetWindowPos(hwnd, None, 40, 40, *outer, 0x0040))
    time.sleep(2)
    return {'style': hex(style), 'ex_style': hex(ex_style),
            'requested_outer': outer, 'set_window_pos': changed,
            'client': dimensions(hwnd)}


def main():
    output = Path(sys.argv[1])
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {}
    hwnd = None
    try:
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            hwnd, pid = game.game_window()
            if hwnd:
                result['pid'] = pid
                break
            time.sleep(.2)
        if not hwnd:
            raise RuntimeError('GAME_WINDOW_NOT_FOUND')
        time.sleep(3)
        result['initial_client'] = dimensions(hwnd)
        result.update(set_client_size(hwnd, 1024, 768))
        game.user.PostMessageW(hwnd, 0x10, 0, 0)
    except Exception as exc:
        result['error'] = repr(exc)
        if hwnd:
            game.user.PostMessageW(hwnd, 0x10, 0, 0)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if not result.get('error') else 1


if __name__ == '__main__':
    raise SystemExit(main())
