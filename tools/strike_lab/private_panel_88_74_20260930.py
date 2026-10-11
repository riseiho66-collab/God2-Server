"""Hidden-desktop original-client panel 88/74 acceptance against our server.

The original client, config and save are read-only inputs. A private client
copy changes only the loopback port, and all game processes run on a separate
desktop. The result does not certify the panel's full server-side features.
"""

import argparse
import ctypes as c
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import traceback

import psutil

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(Path(__file__).resolve().parent)]
import private_pet_reserve_move_20260930 as base
import private_login_keypath_probe as keys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ctrl_f(hwnd):
    """Use the client's Ctrl+F shortcut, preserving the hidden desktop."""
    user = keys.USER
    ctrl = 0x11
    f = 0x46
    ctrl_scan = user.MapVirtualKeyW(ctrl, 0)
    f_scan = user.MapVirtualKeyW(f, 0)
    for message, virtual_key, key_data in (
        (0x100, ctrl, 1 | ctrl_scan << 16),
        (0x100, f, 1 | f_scan << 16),
        (0x101, f, 1 | f_scan << 16 | 3 << 30),
        (0x101, ctrl, 1 | ctrl_scan << 16 | 3 << 30),
    ):
        if not user.PostMessageW(hwnd, message, virtual_key, key_data):
            raise OSError(c.get_last_error(), "Ctrl+F PostMessage")
        time.sleep(.10)


def worker(args):
    base.fixture.CLIENT = args.client.resolve()
    result = {"accepted": False, "client_pids": []}
    before_desktop = base.desktop_names()
    client = None
    log = args.output / "server.log"
    database = args.output / "town-diagnostic-accounts.db"
    try:
        base.require(before_desktop["current"].startswith("God2Lab-") and
                     before_desktop["current"] != before_desktop["input"], "HIDDEN_DESKTOP_REQUIRED")
        before_save = base.daily.stable_database(database)
        client = base.supply.login()
        result["client_pids"].append(client["process"].pid)
        base.require(client["process"].poll() is None, "CLIENT_EXITED_AFTER_LOGIN")
        result["widget_before"] = int.from_bytes(
            base.shared.exact(client["handle"], client["ui"] + 0x232E26, 2), "little", signed=True)
        if 0 <= result["widget_before"] < 128:
            result["flag_before"] = base.shared.exact(
                client["handle"], client["ui"] + 0xE2988 + result["widget_before"] * 0x2A08, 1)[0]
        result["mode_before"] = int.from_bytes(
            base.shared.exact(client["handle"], client["ui"] + 0x4092C, 4), "little")
        ctrl_f(client["hwnd"])

        def opened():
            widget = int.from_bytes(base.shared.exact(client["handle"], client["ui"] + 0x232E26, 2),
                                    "little", signed=True)
            if not 0 <= widget < 128:
                return None
            flags = base.shared.exact(client["handle"], client["ui"] + 0xE2988 + widget * 0x2A08, 1)[0]
            return widget if flags & 0x20 else None

        widget = base.wait_until(opened, 8, "PANEL_88_DID_NOT_OPEN")
        result["flag_after_first_f"] = base.shared.exact(
            client["handle"], client["ui"] + 0xE2988 + widget * 0x2A08, 1)[0]
        mode = int.from_bytes(base.shared.exact(client["handle"], client["ui"] + 0x4092C, 4), "little")
        result["panel"] = {"widget": widget, "mode": mode}
        base.require(mode in (0, 2), "PANEL_74_REQUIRES_MODE_0_OR_2")
        panel_base = client["ui"] + 0xE2170 + widget * 0x2A08
        entry = panel_base + 0x8B8 + 7 * 100
        hit = int.from_bytes(base.shared.exact(client["handle"], entry + 8, 2), "little", signed=True)
        manager = int.from_bytes(base.shared.exact(client["handle"], client["ui"] + 0xE2174, 4), "little")
        base.require(manager > 0x10000 and 0 <= hit < 0xC00, "PANEL_CONTROL7_HIT_MISSING")
        import struct
        active, left, top, right, bottom = struct.unpack(
            "<5i", base.shared.exact(client["handle"], manager + hit * 24, 20))
        result["control7_hit"] = {"hit": hit, "active": active, "rect": [left, top, right, bottom]}
        base.require(active != 0 and 0 <= left < right <= 800 and 0 <= top < bottom <= 600,
                     "PANEL_CONTROL7_NOT_ACTIVE")
        point = ((left + right) // 2, (top + bottom) // 2)
        result["control7_point"] = point
        base.click(client["hwnd"], *point)
        base.wait_until(lambda: "opcode=74 no_state_change no_reply" in log.read_text("utf-8", errors="replace"),
                        8, "NATIVE_74_NOT_SENT_BY_PANEL_CONTROL7")
        result["mode_after"] = int.from_bytes(
            base.shared.exact(client["handle"], client["ui"] + 0x4092C, 4), "little")
        base.require(result["mode_after"] == 1, "PANEL_DID_NOT_SWITCH_TO_MODE1")
        if "opcode=88 no_state_change no_reply" not in log.read_text("utf-8", errors="replace"):
            ctrl_f(client["hwnd"])
            base.wait_until(lambda: "opcode=88 no_state_change no_reply" in log.read_text("utf-8", errors="replace"),
                            8, "NATIVE_88_NOT_SENT_BY_PANEL_TOGGLE")
        base.require(client["process"].poll() is None, "CLIENT_EXITED_AFTER_PANEL_SWITCH")
        base.require(base.daily.stable_database(database) == before_save, "PANEL_CHANGED_SAVED_STATE")
        result["accepted"] = True
    except Exception as error:
        result["error"] = str(error)
        result["traceback"] = traceback.format_exc()
    finally:
        if client:
            try:
                base.shared.close_client(client)
            except Exception as error:
                result["cleanup_error"] = str(error)
        result["desktop_unchanged"] = before_desktop == base.desktop_names()
        result["all_clients_closed"] = not any(psutil.pid_exists(pid) for pid in result["client_pids"])
        result["accepted"] = bool(result["accepted"] and result["desktop_unchanged"] and
                                  result["all_clients_closed"] and not result.get("cleanup_error"))
        dump(args.output / "ui-result.json", result)
    return 0 if result["accepted"] else 1


def owner(args):
    args.output = args.output.resolve()
    args.client = args.client.resolve()
    args.server_candidate = args.server_candidate.resolve()
    sources = {"client": base.LIVE, "database": base.SOURCE,
               "config": base.SOURCE.with_name("server-config.json")}
    result = {"accepted": False, "source_before": {name: sha(path) for name, path in sources.items()},
              "candidate_sha256": sha(args.server_candidate)}
    server = runner = None
    try:
        with socket.socket() as probe:
            base.require(probe.connect_ex(("127.0.0.1", base.PORT)) != 0, "PRIVATE_PORT_IN_USE")
        base.prepare(args)
        environment = os.environ.copy()
        environment["GOD2_LOG_FILE_ONLY"] = "1"
        environment.pop("GOD2_PRIVATE_SIDECAR_COMMAND", None)
        with (args.output / "stdout.log").open("wb") as stdout, (args.output / "runner.log").open("wb") as runnerlog:
            server = subprocess.Popen([str(args.server_candidate), "--config", str(args.output / "server-config.json"),
                                       "--run-for", "160"], cwd=ROOT, env=environment, stdout=stdout,
                                      stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)

            def listening():
                base.require(server.poll() is None, "PRIVATE_SERVER_EXITED")
                with socket.socket() as probe:
                    return probe.connect_ex(("127.0.0.1", base.PORT)) == 0

            base.wait_until(listening, 10, "PRIVATE_SERVER_DID_NOT_LISTEN")
            command = [str(base.fixture.RUNNER), sys.executable, "-X", "utf8", "-B", str(Path(__file__).resolve()),
                       "--worker", "--output", str(args.output), "--client", str(args.client)]
            runner = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=runnerlog,
                                      stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
            result["runner_exit"] = runner.wait(timeout=145)
            result["ui"] = json.loads((args.output / "ui-result.json").read_text("utf-8"))
            result["accepted"] = result["runner_exit"] == 0 and result["ui"]["accepted"]
    except Exception as error:
        result["error"] = str(error)
        result["traceback"] = traceback.format_exc()
    finally:
        for process in (runner, server):
            if process is not None and process.poll() is None:
                descendants = psutil.Process(process.pid).children(recursive=True)
                for child in reversed(descendants):
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                process.terminate()
                process.wait(timeout=5)
                _, alive = psutil.wait_procs(descendants, timeout=5)
                for child in alive:
                    child.kill()
                    child.wait(timeout=5)
        result["source_after"] = {name: sha(path) for name, path in sources.items()}
        result["source_unchanged"] = result["source_before"] == result["source_after"]
        result["candidate_unchanged"] = sha(args.server_candidate) == result["candidate_sha256"]
        result["owned_processes_closed"] = all(process is None or process.poll() is not None
                                                for process in (runner, server))
        result["accepted"] = bool(result["accepted"] and result["source_unchanged"] and
                                  result["candidate_unchanged"] and result["owned_processes_closed"])
        if args.output.exists():
            dump(args.output / "run-result.json", result)
    print(json.dumps({key: result.get(key) for key in
                      ("accepted", "error", "source_unchanged", "owned_processes_closed")}, ensure_ascii=False))
    return 0 if result["accepted"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--client", type=Path, required=True)
    parser.add_argument("--server-candidate", type=Path)
    args = parser.parse_args()
    if args.worker:
        return worker(args)
    base.require(args.server_candidate is not None, "SERVER_CANDIDATE_REQUIRED")
    return owner(args)


if __name__ == "__main__":
    raise SystemExit(main())
