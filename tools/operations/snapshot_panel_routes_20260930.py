"""Refresh the reviewed C2S88/74 candidate snapshot without deploying it."""

import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "artifacts/releases/packet-panel-88-74-20260930-candidate"
SOURCES = (
    "build-town-visibility/Release/god2-server-native-results.exe",
    "src/protocol/RecoveredWorldRecords.h",
    "src/handlers/RecoveredWorldService.cpp",
    "src/core/Application.cpp",
    "tests/test_recovered_world_records.cpp",
    "tests/test_recovered_world_service.cpp",
    "tests/research/test_current_opaque74_server.py",
    "tests/research/test_current_packet_gap_ledger.py",
    "tests/research/test_current_c2s_queue_callers.py",
    "tools/strike_lab/current_packet_gap_ledger.py",
    "tools/strike_lab/current_c2s_queue_callers.py",
    "tools/strike_lab/private_panel_88_74_20260930.py",
    "docs/research/packet-gap-ledger-20260930.md",
    "artifacts/research/packet-gap-ledger-20260930.json",
    "artifacts/research/c2s-queue-callers-20260930.json",
    "artifacts/playtests/private-panel-88-74-20260930-03/run-result.json",
    "artifacts/playtests/private-panel-88-74-20260930-03/ui-result.json",
    "artifacts/playtests/private-panel-88-74-20260930-03/server.log",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    SNAPSHOT.mkdir(parents=True, exist_ok=True)
    rows = []
    for relative in SOURCES:
        source = ROOT / relative
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = SNAPSHOT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if sha(source) != sha(destination):
            raise RuntimeError(f"Snapshot copy mismatch: {relative}")
        rows.append({"source": relative, "snapshot": relative, "sha256": sha(source)})
    manifest = {
        "format": "c2s-panel-88-74-candidate-snapshot-v2",
        "status": "candidate_only_not_deployed",
        "accepted_current_client": True,
        "whole_game_completion_percent": None,
        "files": rows,
    }
    (SNAPSHOT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "files": len(rows),
                      "executable_sha256": rows[0]["sha256"]}))


if __name__ == "__main__":
    main()
