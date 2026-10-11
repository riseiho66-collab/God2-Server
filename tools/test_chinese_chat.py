"""Own-server placeholder socket acceptance for CUSTOM-0029 (not native GOD2)."""
import json
from pathlib import Path
import re
import shutil
import socket
import struct
import subprocess
import tempfile
import time

from fixture_combat_client import FixtureClient, wire_string


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "build" / "Release" / "god2-server.exe"


def receive_chat(client, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        client.socket.settimeout(max(0.1, deadline - time.monotonic()))
        header = client.socket.recv(4)
        if len(header) != 4:
            raise AssertionError("Truncated chat frame")
        length, opcode = struct.unpack("<HH", header)
        body = bytearray()
        while len(body) < length - 4:
            body.extend(client.socket.recv(length - 4 - len(body)))
        if opcode == 0x2010:  # asynchronous spawn
            continue
        if opcode != 0x2020:
            raise AssertionError(f"Unexpected opcode {opcode:04x}")
        sender = struct.unpack_from("<I", body)[0]
        count = struct.unpack_from("<H", body, 4)[0]
        assert count == len(body) - 6
        return sender, bytes(body[6:]).decode("utf-8")
    raise AssertionError("Chat timeout")


def send_chat(client, text):
    body = wire_string(text)
    client.socket.sendall(struct.pack("<HH", len(body) + 4, 0x1020) + body)


def main():
    assert SERVER.is_file()
    with tempfile.TemporaryDirectory(prefix="god2-chinese-chat-") as temp:
        folder = Path(temp)
        config = json.loads((ROOT / "config/server.json").read_text(encoding="utf-8"))
        config["server"]["port"] = 0
        config["protocol"]["packet_dump"] = False
        config["database"]["path"] = str(folder / "chat.sqlite")
        config["logging"]["file"] = str(folder / "server.log")
        scripts = folder / "scripts"
        shutil.copytree(ROOT / "scripts", scripts)
        npc_file = scripts / "npc/test_npc.lua"
        npc_script = npc_file.read_text(encoding="utf-8")
        npc_script = npc_script.replace("Hello, welcome to GOD2 rebuild server.", "欢迎遊戲")
        npc_script = npc_script.replace("Who are you?", "开始遊戲")
        npc_file.write_text(npc_script, encoding="utf-8")
        config["lua"]["bootstrap"] = str(scripts / "bootstrap.lua")
        config["lua"]["script_root"] = str(scripts)
        config["text"]["dictionary_root"] = str(ROOT / "resources/opencc")
        cfg = folder / "config/server.json"
        cfg.parent.mkdir()
        cfg.write_text(json.dumps(config), encoding="utf-8")
        process = subprocess.Popen([str(SERVER), "--config", str(cfg), "--run-for", "30"],
                                   cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding="utf-8", errors="replace",
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            port = None
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                line = process.stdout.readline()
                match = re.search(r"listening on 127\.0\.0\.1:(\d+)", line)
                if match:
                    port = int(match.group(1))
                    break
                if process.poll() is not None:
                    raise AssertionError(f"Server exited: {line}")
            assert port
            with FixtureClient(port=port) as first, FixtureClient(port=port) as second:
                first.login("chat-first")
                second.login("chat-second")
                send_chat(second, "/lang zh-CN")
                assert receive_chat(second)[1] == "Language: 简体中文"
                send_chat(first, "漢字遊戲")
                assert receive_chat(first)[1] == "漢字遊戲"
                assert receive_chat(second)[1] == "汉字游戏"
                send_chat(second, "汉字游戏")
                assert receive_chat(first)[1] == "漢字遊戲"
                assert receive_chat(second)[1] == "汉字游戏"
                send_chat(second, "/lang zh-TW")
                assert receive_chat(second)[1] == "語言：繁體中文"
                send_chat(first, "汉字游戏")
                assert receive_chat(first)[1] == "漢字遊戲"
                assert receive_chat(second)[1] == "漢字遊戲"
                for client, expected in ((first, "歡迎遊戲"), (second, "歡迎遊戲")):
                    reader = client.request(0x1030, struct.pack("<I", 1001), 0x2031)
                    assert reader.number("I") == 1001
                    dialogue = json.loads(reader.string())
                    reader.end()
                    assert dialogue["text"] == expected
                    assert dialogue["options"][0] == {"id": 1, "text": "開始遊戲"}
                send_chat(second, "/lang zh-CN")
                assert receive_chat(second)[1] == "Language: 简体中文"
                reader = second.request(0x1030, struct.pack("<I", 1001), 0x2031)
                assert reader.number("I") == 1001
                dialogue = json.loads(reader.string())
                reader.end()
                assert dialogue["text"] == "欢迎游戏"
                assert dialogue["options"][0] == {"id": 1, "text": "开始游戏"}
            print("Chinese chat and NPC dialogue accepted across two own-server sessions")
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
