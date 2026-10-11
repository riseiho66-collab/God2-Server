"""Probe native login key messages on a private Windows desktop.

Only the result and session outcome are written; credentials stay in memory.
"""
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import sys
import time
import psutil

import private_unpacked_smoke as game


ROOT = Path(r"C:\Users\risei\Desktop\God2\God2")
USER = c.WinDLL("user32", use_last_error=True)
KERNEL = c.WinDLL("kernel32", use_last_error=True)
USER.CreateDesktopW.argtypes = [w.LPCWSTR, w.LPCWSTR, c.c_void_p, w.DWORD, w.DWORD, c.c_void_p]
USER.CreateDesktopW.restype = w.HANDLE
USER.EnumDesktopWindows.argtypes = [w.HANDLE, c.c_void_p, w.LPARAM]
USER.EnumDesktopWindows.restype = w.BOOL
USER.CloseDesktop.argtypes = [w.HANDLE]
USER.CloseDesktop.restype = w.BOOL
KERNEL.CreateProcessW.argtypes = [w.LPCWSTR, w.LPWSTR, c.c_void_p, c.c_void_p, w.BOOL,
                                   w.DWORD, c.c_void_p, w.LPCWSTR, c.c_void_p, c.c_void_p]
KERNEL.CreateProcessW.restype = w.BOOL
KERNEL.CloseHandle.argtypes = [w.HANDLE]
KERNEL.CloseHandle.restype = w.BOOL
KERNEL.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
KERNEL.OpenProcess.restype = w.HANDLE
KERNEL.VirtualQueryEx.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t]
KERNEL.VirtualQueryEx.restype = c.c_size_t
KERNEL.ReadProcessMemory.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t, c.c_void_p]
KERNEL.ReadProcessMemory.restype = w.BOOL
KERNEL.WriteProcessMemory.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t, c.c_void_p]
KERNEL.WriteProcessMemory.restype = w.BOOL


class StartupInfo(c.Structure):
    _fields_ = [("cb", w.DWORD), ("lpReserved", w.LPWSTR), ("lpDesktop", w.LPWSTR),
                ("lpTitle", w.LPWSTR), ("dwX", w.DWORD), ("dwY", w.DWORD),
                ("dwXSize", w.DWORD), ("dwYSize", w.DWORD),
                ("dwXCountChars", w.DWORD), ("dwYCountChars", w.DWORD),
                ("dwFillAttribute", w.DWORD), ("dwFlags", w.DWORD),
                ("wShowWindow", w.WORD), ("cbReserved2", w.WORD),
                ("lpReserved2", c.c_void_p), ("hStdInput", w.HANDLE),
                ("hStdOutput", w.HANDLE), ("hStdError", w.HANDLE)]


class ProcessInformation(c.Structure):
    _fields_ = [("hProcess", w.HANDLE), ("hThread", w.HANDLE),
                ("dwProcessId", w.DWORD), ("dwThreadId", w.DWORD)]


class MemoryInfo(c.Structure):
    _fields_ = [("BaseAddress", c.c_void_p), ("AllocationBase", c.c_void_p),
                ("AllocationProtect", w.DWORD), ("PartitionId", w.WORD),
                ("RegionSize", c.c_size_t), ("State", w.DWORD),
                ("Protect", w.DWORD), ("Type", w.DWORD)]


def in_memory_credential_shapes(pid):
    """Return only field shape comparisons; never persist credential bytes."""
    handle = KERNEL.OpenProcess(0x1010, False, pid)
    if not handle:
        return {"readable": False}
    matches = []
    try:
        address = 0x400000
        while address < 0x80000000:
            info = MemoryInfo()
            if not KERNEL.VirtualQueryEx(handle, c.c_void_p(address), c.byref(info), c.sizeof(info)):
                break
            end = info.BaseAddress + info.RegionSize
            if end <= address:
                break
            if info.State == 0x1000 and not (info.Protect & 0x101) and info.RegionSize <= 64 * 1024 * 1024:
                at = info.BaseAddress
                while at < end:
                    size = min(1024 * 1024, end - at)
                    buffer = c.create_string_buffer(size)
                    read = c.c_size_t()
                    if KERNEL.ReadProcessMemory(handle, c.c_void_p(at), buffer, size, c.byref(read)):
                        data = buffer.raw[:read.value]
                        position = 0
                        while True:
                            position = data.find(b"test1\x00", position)
                            if position < 0:
                                break
                            candidate = data[position + 24:position + 24 + 132].split(b"\x00", 1)[0]
                            if 0 < len(candidate) <= 20 and all(0x20 <= byte < 0x7f for byte in candidate):
                                expected = b"test1"
                                matches.append({"length": len(candidate),
                                                "exact": candidate == expected,
                                                "casefold": candidate.lower() == expected,
                                                "matching_positions": sum(a == b for a, b in zip(candidate, expected))})
                            position += 1
                    at += size
            address = end
    finally:
        KERNEL.CloseHandle(handle)
    return {"readable": True, "adjacent_fields": matches[:20]}


def login_state(pid):
    handle = KERNEL.OpenProcess(0x1010, False, pid)
    if not handle:
        return None
    try:
        pointer = c.c_uint32()
        count = c.c_size_t()
        if not KERNEL.ReadProcessMemory(handle, c.c_void_p(0x5e00f8 + 0x43c),
                                        c.byref(pointer), 4, c.byref(count)) or count.value != 4:
            return None
        state = c.c_uint32()
        if not KERNEL.ReadProcessMemory(handle, c.c_void_p(pointer.value + 0x178cec),
                                        c.byref(state), 4, c.byref(count)) or count.value != 4:
            return None
        return state.value
    finally:
        KERNEL.CloseHandle(handle)


def account_case_shape(pid, expected):
    """Inspect the native account edit buffer, returning comparisons only."""
    handle = KERNEL.OpenProcess(0x1010, False, pid)
    if not handle:
        return {"readable": False}
    try:
        pointer = c.c_uint32()
        count = c.c_size_t()
        if not KERNEL.ReadProcessMemory(handle, c.c_void_p(0x5e00f8 + 0x43c),
                                        c.byref(pointer), 4, c.byref(count)) or count.value != 4:
            return {"readable": False}
        # Account edit text starts at the embedded text control's +0x18.
        raw = c.create_string_buffer(48)
        address = pointer.value + 0x178db4 + 4 + 0x18
        if not KERNEL.ReadProcessMemory(handle, c.c_void_p(address), raw, 48,
                                        c.byref(count)):
            return {"readable": False}
        value = raw.raw.split(b"\x00", 1)[0]
        original = expected.encode("ascii")
        flags = {}
        for label, widget in (("account", 0x178db4), ("password", 0x179940)):
            control = pointer.value + widget + 4
            flags[label] = {}
            for offset in (0xb20, 0xb24, 0xb28, 0xb40, 0xb44, 0xb48):
                number = c.c_uint32()
                if KERNEL.ReadProcessMemory(handle, c.c_void_p(control + offset),
                                             c.byref(number), 4, c.byref(count)) and count.value == 4:
                    flags[label][hex(offset)] = number.value
        return {"readable": True, "length": len(value),
                "exact": value == original,
                "casefold": value.lower() == original.lower(),
                "lowercase": value == original.lower(), "flags": flags}
    finally:
        KERNEL.CloseHandle(handle)


def disable_account_lowercase_in_private_process(pid):
    handle = KERNEL.OpenProcess(0x1038, False, pid)
    if not handle:
        raise OSError(c.get_last_error(), "OpenProcess private game")
    try:
        pointer = c.c_uint32()
        count = c.c_size_t()
        if not KERNEL.ReadProcessMemory(handle, c.c_void_p(0x5e00f8 + 0x43c),
                                        c.byref(pointer), 4, c.byref(count)) or count.value != 4:
            raise RuntimeError("Login object unavailable")
        address = pointer.value + 0x178db4 + 4 + 0xb24
        zero = c.c_uint32(0)
        if not KERNEL.WriteProcessMemory(handle, c.c_void_p(address), c.byref(zero),
                                         4, c.byref(count)) or count.value != 4:
            raise OSError(c.get_last_error(), "Private account flag write")
    finally:
        KERNEL.CloseHandle(handle)


def game_window(desktop):
    found = []
    callback_type = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)

    @callback_type
    def visit(hwnd, unused):
        cls = c.create_unicode_buffer(128)
        if USER.GetClassNameW(hwnd, cls, len(cls)) and cls.value == "XianJieWndClass":
            found.append(hwnd)
        return True

    USER.EnumDesktopWindows(desktop, visit, 0)
    return found[0] if found else None


def native_error_window(desktop):
    found = []
    callback_type = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)

    @callback_type
    def visit(hwnd, unused):
        title = c.create_unicode_buffer(128)
        USER.GetWindowTextW(hwnd, title, len(title))
        if title.value in ("錯誤", "错误", "Error"):
            found.append(hwnd)
        return True

    USER.EnumDesktopWindows(desktop, visit, 0)
    return bool(found)


def key_ascii(hwnd, value):
    for char in value:
        vk = ord(char.upper())
        scan = USER.MapVirtualKeyW(vk, 0)
        down = 1 | (scan << 16)
        up = down | (3 << 30)
        if not USER.PostMessageW(hwnd, 0x100, vk, down):
            raise OSError(c.get_last_error(), "key down")
        time.sleep(.08)
        if not USER.PostMessageW(hwnd, 0x101, vk, up):
            raise OSError(c.get_last_error(), "key up")
        time.sleep(.08)


def main():
    output = Path(sys.argv[1])
    mode = sys.argv[2]
    if mode not in ("key", "char"):
        raise ValueError("mode")
    account = sys.argv[3] if len(sys.argv) > 3 else "test1"
    if not account.isascii() or not account.isalnum() or len(account) > 20:
        raise ValueError("account")
    output.parent.mkdir(parents=True, exist_ok=True)
    label = "God2LoginProbe" + str(int(time.time()))
    desktop = USER.CreateDesktopW(label, None, None, 0, 0x000F01FF, None)
    if not desktop:
        raise OSError(c.get_last_error(), "CreateDesktopW")
    info = ProcessInformation()
    hwnd = None
    game_pid = None
    result = {"mode": mode, "launched": False, "window": False, "submitted": False}
    try:
        startup = StartupInfo()
        startup.cb = c.sizeof(startup)
        startup.lpDesktop = label
        le = ROOT / "compat-tools/LocaleEmulator/LEProc.exe"
        exe = ROOT / "God2.exe"
        command = c.create_unicode_buffer(f'"{le}" -run "{exe}" 127.0.0.1 127.0.0.1 6001 1')
        if not KERNEL.CreateProcessW(None, command, None, None, False, 0, None,
                                     str(ROOT), c.byref(startup), c.byref(info)):
            raise OSError(c.get_last_error(), "CreateProcessW")
        result["launched"] = True
        deadline = time.monotonic() + 35
        while time.monotonic() < deadline:
            hwnd = game_window(desktop)
            if hwnd:
                break
            time.sleep(.25)
        if not hwnd:
            raise RuntimeError("game window timeout")
        pid_value = w.DWORD()
        USER.GetWindowThreadProcessId(hwnd, c.byref(pid_value))
        game_pid = pid_value.value
        result["window"] = True
        time.sleep(4)
        game.click(hwnd, 512, 464)
        time.sleep(2)
        result["state_before"] = login_state(game_pid)
        if "--disable-account-lowercase" in sys.argv[4:]:
            disable_account_lowercase_in_private_process(game_pid)
        writer = key_ascii if mode == "key" else game.type_ascii
        game.click(hwnd, 437, 232)
        writer(hwnd, account)
        time.sleep(.5)
        result["account_shape"] = account_case_shape(game_pid, account)
        game.click(hwnd, 437, 263)
        writer(hwnd, "wrong1" if "--wrong-password" in sys.argv[4:] else "test1")
        if len(sys.argv) <= 3 or "--submit" in sys.argv[4:]:
            submit_start = time.monotonic()
            game.click(hwnd, 452, 304)
            result["submitted"] = True
        result["state_after"] = login_state(game_pid)
        result["memory"] = in_memory_credential_shapes(game_pid)
        if "--wrong-password" in sys.argv[4:]:
            until = submit_start + 8
            while time.monotonic() < until and not native_error_window(desktop):
                time.sleep(.05)
            result["native_error_window"] = native_error_window(desktop)
            result["error_dialog_observed_within_ms"] = round((time.monotonic() - submit_start) * 1000)
        else:
            time.sleep(1 if len(sys.argv) > 3 else 6)
        result["state_later"] = login_state(game_pid)
    except Exception as exc:
        result["error"] = repr(exc)
    finally:
        if hwnd:
            USER.PostMessageW(hwnd, 0x10, 0, 0)
        if game_pid and psutil.pid_exists(game_pid):
            try:
                psutil.Process(game_pid).kill()
                psutil.Process(game_pid).wait(timeout=5)
            except psutil.NoSuchProcess:
                pass
        if info.hThread:
            KERNEL.CloseHandle(info.hThread)
        if info.hProcess:
            KERNEL.CloseHandle(info.hProcess)
        USER.CloseDesktop(desktop)
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if (not result.get("error") and
                 ("--wrong-password" not in sys.argv[4:] or result.get("native_error_window"))) else 1


if __name__ == "__main__":
    raise SystemExit(main())
