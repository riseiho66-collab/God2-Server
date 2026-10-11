#!/usr/bin/env python3
"""Loopback-only CUSTOM_TEST_NOT_NATIVE fixture client (Python stdlib only).

This protocol is not compatible with the original God2 client.
Example: python tools/fixture_combat_client.py --port 17070 --username test --autoplay
Integration: python tools/fixture_combat_client.py --self-test --server EXE --root REPO
"""

import argparse
import contextlib
import ipaddress
import json
import math
from pathlib import Path
import queue
import re
import secrets
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time


AUTHORITY = "CUSTOM_TEST_NOT_NATIVE"


class ProtocolError(Exception):
    pass


class ServerRejected(ProtocolError):
    """Do not echo server error text: it could contain credentials."""


def require(condition, message):
    if not condition:
        raise ProtocolError(message)


def wire_string(value):
    encoded = value.encode("utf-8")
    require(len(encoded) <= 65535, "String exceeds uint16 byte length")
    return struct.pack("<H", len(encoded)) + encoded


class Reader:
    def __init__(self, data):
        self.data = data
        self.offset = 0

    def take(self, count):
        require(self.offset + count <= len(self.data), "Truncated response payload")
        result = self.data[self.offset:self.offset + count]
        self.offset += count
        return result

    def number(self, fmt):
        return struct.unpack("<" + fmt, self.take(struct.calcsize("<" + fmt)))[0]

    def string(self):
        try:
            return self.take(self.number("H")).decode("utf-8", errors="strict")
        except UnicodeError:
            raise ProtocolError("Invalid UTF-8 response") from None

    def end(self):
        require(self.offset == len(self.data), "Trailing response payload")


def validate_snapshot(value):
    require(isinstance(value, dict), "Snapshot must be an object")
    require(value.get("authority") == AUTHORITY, "Unexpected snapshot authority")
    for field in ("battle_id", "turn"):
        require(type(value.get(field)) is int and 0 <= value[field] <= 0xffffffff,
                "Invalid snapshot " + field)
    require(value.get("outcome") in ("active", "won", "lost", "fled"), "Invalid outcome")
    for who in ("player", "monster"):
        stats = value.get(who)
        require(isinstance(stats, dict), "Missing combatant")
        for field in ("hp", "max_hp", "mp", "max_mp", "physical_attack", "magical_attack",
                      "physical_defense", "magical_defense"):
            require(type(stats.get(field)) is int and stats[field] >= 0,
                    "Invalid combatant " + field)
        require(stats["hp"] <= stats["max_hp"] and stats["mp"] <= stats["max_mp"],
                "Combatant exceeds resource maximum")
    for field in ("player_action", "monster_action"):
        action = value.get(field)
        require(isinstance(action, dict), "Missing action result")
        for key in ("damage", "mp_cost"):
            require(type(action.get(key)) is int and action[key] >= 0, "Invalid action result")
        require(type(action.get("critical")) is bool, "Invalid critical flag")
    return value


class FixtureClient:
    def __init__(self, host="127.0.0.1", port=17070, timeout=5.0):
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            raise ProtocolError("Host must be a numeric loopback address") from None
        require(address.is_loopback, "Only loopback connections are permitted")
        require(1 <= port <= 65535, "Port must be between 1 and 65535")
        require(math.isfinite(timeout) and timeout > 0, "Timeout must be finite and positive")
        self.timeout = timeout
        self.snapshot = None
        self.socket = socket.create_connection((str(address), port), timeout)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.socket.close()

    def _exact(self, count, deadline):
        data = bytearray()
        while len(data) < count:
            remaining = deadline - time.monotonic()
            require(remaining > 0, "Response deadline exceeded")
            self.socket.settimeout(remaining)
            part = self.socket.recv(count - len(data))
            require(bool(part), "Server disconnected during response")
            data.extend(part)
        return bytes(data)

    def request(self, opcode, payload, expected):
        require(len(payload) <= 65531, "Frame exceeds uint16 total length")
        deadline = time.monotonic() + self.timeout
        self.socket.settimeout(self.timeout)
        self.socket.sendall(struct.pack("<HH", len(payload) + 4, opcode) + payload)
        while True:
            length, response = struct.unpack("<HH", self._exact(4, deadline))
            require(length >= 4, "Invalid frame length")
            body = self._exact(length - 4, deadline)
            if response == 0x2010:
                self._spawn(body)
                continue
            if response == 0x2fff:
                reader = Reader(body)
                reader.string()
                reader.end()
                raise ServerRejected("Server rejected fixture request")
            require(response == expected, "Unexpected response opcode")
            return Reader(body)

    @staticmethod
    def _spawn(body):
        reader = Reader(body)
        result = {field: reader.number(fmt) for field, fmt in
                  (("session_id", "I"), ("character_id", "I"), ("map", "I"),
                   ("x", "i"), ("y", "i"), ("direction", "B"), ("hp", "I"), ("mp", "I"))}
        reader.end()
        return result

    def login(self, username, password="", version="fixture-combat-v1"):
        require(0 < len(username.encode("utf-8")) <= 64, "Invalid username length")
        require(len(password.encode("utf-8")) <= 256 and len(version.encode("utf-8")) <= 64,
                "Invalid login field length")
        reader = self.request(0x1000, b"", 0x2000)
        require(reader.string() == "GOD2 PLACEHOLDER v1", "Unexpected handshake")
        reader.end()
        reader = self.request(0x1001, b"".join(map(wire_string, (username, password, version))), 0x2001)
        require(reader.number("B") == 0, "Login failed")
        self.account_id = reader.number("I")
        reader.string()
        reader.end()
        reader = self.request(0x1002, b"", 0x2002)
        count = reader.number("H")
        require(0 < count <= 100, "Invalid character count")
        characters = []
        for _ in range(count):
            character = {"id": reader.number("I"), "name": reader.string()}
            for field, fmt in (("level", "I"), ("job", "I"), ("map", "I"), ("x", "i"), ("y", "i")):
                character[field] = reader.number(fmt)
            characters.append(character)
        reader.end()
        selected = characters[0]["id"]
        reader = self.request(0x1003, struct.pack("<I", selected), 0x2003)
        require(reader.number("B") == 0 and reader.number("I") == selected, "Character selection failed")
        reader.end()
        reader = self.request(0x1004, b"", 0x2004)
        entered = self._spawn(reader.data)
        require(entered["character_id"] == selected, "Wrong character entered world")
        return characters

    def combat(self, payload, expected=0x2041):
        reader = self.request(0x1040, payload, expected)
        encoded = reader.string()
        reader.end()
        try:
            snapshot = json.loads(encoded)
        except (ValueError, RecursionError):
            raise ProtocolError("Invalid snapshot JSON") from None
        self.snapshot = validate_snapshot(snapshot)
        return self.snapshot

    def start(self):
        return self.combat(b"\x00", 0x2040)

    def action_payload(self, skill=None):
        require(self.snapshot is not None, "Start a battle first")
        payload = struct.pack("<BII", 2 if skill is None else 1,
                              self.snapshot["battle_id"], self.snapshot["turn"])
        if skill is not None:
            require(skill in (1, 2, 3), "Unknown skill")
            payload += bytes([skill])
        return payload

    def act(self, skill):
        return self.combat(self.action_payload(skill))

    def flee(self):
        return self.combat(self.action_payload())


@contextlib.contextmanager
def own_server(executable, root, timeout, enabled=True):
    """Drain stdout continuously, retaining only the loopback readiness port."""
    with tempfile.TemporaryDirectory(prefix="god2-fixture-combat-") as temp:
        folder = Path(temp)
        config = json.loads((root / "config" / "fixture-combat.json").read_text(encoding="utf-8-sig"))
        config["server"].update(host="127.0.0.1", port=0)
        config["database"]["path"] = str(folder / "fixture-combat.sqlite")
        config["logging"].update(file=str(folder / "server.log"), level="info")
        config["protocol"]["packet_dump"] = False
        config["lua"]["hot_reload"] = False
        for field in ("script_root", "bootstrap"):
            config["lua"][field] = str((root / config["lua"][field]).resolve())
        require(config["development"].get("fixture_battle") is True,
                "Base config must opt in with development.fixture_battle")
        config["development"]["fixture_battle"] = enabled
        path = folder / "config" / "fixture-combat.json"
        path.parent.mkdir()
        path.write_text(json.dumps(config), encoding="utf-8")
        process = subprocess.Popen([str(executable), "--config", str(path), "--run-for", "45"],
                                   cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding="utf-8", errors="replace",
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        ready = queue.Queue(maxsize=1)

        def drain():
            for line in process.stdout:
                match = re.search(r"listening on 127\.0\.0\.1:(\d+)\b", line)
                if match:
                    try:
                        ready.put_nowait(int(match.group(1)))
                    except queue.Full:
                        pass

        thread = threading.Thread(target=drain, daemon=True)
        thread.start()
        try:
            deadline = time.monotonic() + timeout
            while True:
                require(process.poll() is None, "Owned server exited before readiness")
                require(time.monotonic() < deadline, "Owned server readiness timed out")
                try:
                    port = ready.get(timeout=min(0.1, max(0.001, deadline - time.monotonic())))
                    break
                except queue.Empty:
                    continue
            require(1 <= port <= 65535, "Invalid readiness port")
            yield port
            require(process.poll() is None, "Owned server exited unexpectedly")
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            thread.join(timeout=5)
            process.stdout.close()


def expect_rejected(client, payload):
    try:
        client.combat(payload)
    except ServerRejected:
        return
    raise ProtocolError("Invalid action was accepted")


def check_initial(state):
    require(state["outcome"] == "active", "Battle did not start active")
    require((state["player"]["hp"], state["player"]["mp"], state["monster"]["hp"])
            == (120, 24, 100), "Unexpected initial fixture resources")


def check_action(before, after, cost):
    require(after["battle_id"] == before["battle_id"] and after["turn"] == before["turn"] + 1,
            "Action did not advance exactly one turn")
    require(after["player"]["mp"] == before["player"]["mp"] - cost,
            "Incorrect MP charge (or rejected action mutated state)")
    require(after["player_action"]["mp_cost"] == cost, "Incorrect action MP cost")
    damage = after["player_action"]["damage"]
    require(damage > 0 and after["monster"]["hp"] == max(0, before["monster"]["hp"] - damage),
            "Incorrect monster damage (or rejected action mutated state)")
    require(after["player"]["hp"] == max(0, before["player"]["hp"] - after["monster_action"]["damage"]),
            "Incorrect player damage (or rejected action mutated state)")


def self_test(args):
    summary = {"authority": AUTHORITY, "ok": False, "checks": []}
    stage = "configuration"
    try:
        require(args.server is not None, "--self-test requires --server")
        root = args.root.resolve()
        executable = args.server.resolve()
        require(executable.is_file(), "Server executable is missing")
        stage = "enabled server startup"
        with own_server(executable, root, max(10, args.timeout), True) as port:
            with FixtureClient(port=port, timeout=args.timeout) as first, FixtureClient(port=port, timeout=args.timeout) as second:
                stage = "two independent logins"
                token = secrets.token_hex(6)
                first.login("fixture_a_" + token)
                second.login("fixture_b_" + token)
                require(first.account_id != second.account_id, "Accounts are not distinct")
                a, b = first.start(), second.start()
                check_initial(a)
                check_initial(b)
                summary["checks"].append(stage)
                stage = "heavy attack"
                stale = first.action_payload(3)
                heavy = first.act(3)
                check_action(a, heavy, 20)
                require(heavy["player"]["mp"] == 4, "Heavy did not leave 4 MP")
                summary["checks"].append(stage)
                stage = "stale and insufficient MP rejected without mutation"
                expect_rejected(first, stale)
                expect_rejected(first, first.action_payload(3))
                after = first.act(1)
                check_action(heavy, after, 0)
                summary["checks"].append(stage)
                stage = "basic attacks terminate in victory"
                for _ in range(20):
                    if after["outcome"] != "active":
                        break
                    before = after
                    after = first.act(1)
                    check_action(before, after, 0)
                require(after["outcome"] == "won" and after["monster"]["hp"] == 0, "Basic attacks did not win")
                expect_rejected(first, first.action_payload(1))
                summary["checks"].append(stage)
                stage = "second client isolation"
                other = second.act(3)
                check_action(b, other, 20)
                require(other["player"]["mp"] == 4, "Second client resources changed")
                summary["checks"].append(stage)
                stage = "flee and restart"
                fled = second.flee()
                require(fled["outcome"] == "fled", "Flee did not terminate battle")
                require(fled["player"] == other["player"] and fled["monster"] == other["monster"],
                        "Flee mutated combatant resources")
                restarted = second.start()
                check_initial(restarted)
                require(restarted["battle_id"] != b["battle_id"], "Restart reused battle identity")
                expect_rejected(second, struct.pack("<BIIB", 1, b["battle_id"], b["turn"], 1))
                summary["checks"].append(stage)
                stage = "malformed and trailing actions rejected without mutation"
                valid = second.action_payload(1)
                for payload in (b"", b"\x7f", valid[:-1], valid + b"\x00", second.action_payload() + b"\x00"):
                    expect_rejected(second, payload)
                check_action(restarted, second.act(1), 0)
                summary["checks"].append(stage)
        stage = "disabled fixture rejected"
        with own_server(executable, root, max(10, args.timeout), False) as port:
            with FixtureClient(port=port, timeout=args.timeout) as client:
                client.login("fixture_disabled_" + secrets.token_hex(6))
                expect_rejected(client, b"\x00")
        summary["checks"].append(stage)
        summary["ok"] = True
    except Exception as exc:
        # Exception messages, server output and login responses may contain secrets.
        summary.update(failed_stage=stage, error=type(exc).__name__)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["ok"] else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=17070)
    parser.add_argument("--username", default="fixture_player")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--autoplay", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--server", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout must be finite and positive")
    if args.self_test:
        return self_test(args)
    try:
        with FixtureClient(args.host, args.port, args.timeout) as client:
            client.login(args.username)
            if args.autoplay:
                state = client.start()
                print(json.dumps(state, sort_keys=True))
                for _ in range(100):
                    if state["outcome"] != "active":
                        return 0 if state["outcome"] == "won" else 1
                    state = client.act(3 if state["player"]["mp"] >= 20 else 1)
                    print(json.dumps(state, sort_keys=True))
                raise ProtocolError("Autoplay turn limit exceeded")
            print(AUTHORITY + " | commands: start / 1 / 2 / 3 / flee / quit")
            while True:
                try:
                    command = input("> ").strip().lower()
                except EOFError:
                    return 0
                if command == "quit":
                    return 0
                if command not in ("start", "1", "2", "3", "flee"):
                    print("Commands: start / 1 / 2 / 3 / flee / quit")
                    continue
                if command != "start" and client.snapshot is None:
                    print("Start a battle first")
                    continue
                try:
                    state = client.start() if command == "start" else client.flee() if command == "flee" else client.act(int(command))
                    print(json.dumps(state, sort_keys=True))
                except ServerRejected:
                    print("Server rejected fixture request")
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(json.dumps({"authority": AUTHORITY, "ok": False, "error": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
