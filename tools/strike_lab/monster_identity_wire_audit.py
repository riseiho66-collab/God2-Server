"""Read-only source-to-packet audit of the current diagnostic battle.

This deliberately reports the server's test values separately from original
monster values. It never connects to a server or changes the database.
"""

import argparse
import json
import sqlite3
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BINARY = ROOT / "build-monster-trace/tests/Release/recovered-battle-bootstrap.exe"
DEFAULT_DATABASE = ROOT / "god2.db"
DEFAULT_CATALOG = ROOT / "artifacts/research/current-monster-readable-20260924.json"


def u16(record, offset):
    return int.from_bytes(record[offset:offset + 2], "little")


def u32(record, offset):
    return int.from_bytes(record[offset:offset + 4], "little")


def parse_records(logical):
    sizes = {0x1C: 45, 0x86: 17, 0x88: 121}
    records = []
    offset = 0
    while offset < len(logical):
        opcode = logical[offset]
        if opcode not in sizes or offset + sizes[opcode] > len(logical):
            raise ValueError(f"Unknown or truncated record at {offset}: {opcode:02x}")
        record = logical[offset:offset + sizes[opcode]]
        row = {"logical_offset": offset, "opcode": f"{opcode:02X}"}
        if opcode == 0x1C:
            row.update(position=record[1], displayed_level=record[2],
                       identity_word=u16(record, 3), variant=u16(record, 5),
                       ordinal=u16(record, 7), area=record[9], scene=u16(record, 11))
        elif opcode == 0x86:
            row.update(subtype=record[1], position=record[2])
            if record[1] in (0, 1):
                row.update(maximum=u32(record, 5), current=u32(record, 9),
                           resource="HP" if record[1] == 0 else "MP")
        records.append(row)
        offset += sizes[opcode]
    return records


def audit(binary, database, catalog):
    logical = bytes.fromhex(subprocess.check_output(
        [str(binary), "--diagnostic-participant-logical"], text=True, timeout=10).strip())
    records = parse_records(logical)
    enemy = [r for r in records if r["opcode"] == "1C" and r["position"] == 14]
    enemy_hp = [r for r in records if r["opcode"] == "86" and
                r.get("subtype") == 0 and r["position"] == 14]
    if len(enemy) != 1 or len(enemy_hp) != 1:
        raise ValueError("Expected exactly one enemy identity and HP record")
    connection = sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)
    try:
        tables = [name for (name,) in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        region = None
        if "native_map_catalog" in tables:
            map_rows = connection.execute(
                "SELECT dataset_id,source_line,raw_record FROM native_map_catalog "
                "WHERE area=? AND scene=?",
                (enemy[0]["area"], enemy[0]["scene"])).fetchall()
            if len(map_rows) == 1:
                dataset, line, raw = map_rows[0]
                fields = raw.split(b",")
                if len(fields) >= 3:
                    region = {"dataset_id": dataset, "source_line": line,
                              "name_bytes_hex": fields[2].hex(),
                              "name_cp950": fields[2].decode("cp950")}
    finally:
        connection.close()
    monster_tables = [name for name in tables if "monster" in name.lower() or "enemy" in name.lower()]
    source = json.loads(catalog.read_text(encoding="utf-8"))
    matches = [r for r in source["records"] if r.get("lookup_visible") and
               (r["area"], r["scene"], r["ordinal"]) ==
               (enemy[0]["area"], enemy[0]["scene"], enemy[0]["ordinal"])]
    display_row = None
    if len(matches) == 1:
        match = matches[0]
        same_name = [r for r in source["records"] if r.get("lookup_visible") and
                     r["name_bytes_hex"] == match["name_bytes_hex"]]
        display_row = {"source": source["source"], "source_sha256": source["source_sha256"],
                       "source_line": match["source_line"], "source_offset": match["source_offset"],
                       "name_bytes_hex": match["name_bytes_hex"], "name_cp950": match["name_cp950"],
                       "same_name_display_keys": [{"area": r["area"], "scene": r["scene"],
                                                    "ordinal": r["ordinal"], "source_line": r["source_line"]}
                                                   for r in same_name],
                       "original_numeric_fields": match["original_numeric_fields"]}
    return {
        "packet_origin": "CUSTOM-0009/CUSTOM-0012 diagnostic server emission",
        "server_database": str(database),
        "server_monster_named_tables": monster_tables,
        "monster_identity_packet": enemy[0],
        "server_native_map_region": region,
        "client_display_row": display_row,
        "monster_hp_packet": enemy_hp[0],
        "logical_records": records,
        "native_value_status": "unrecovered",
        "join_status": "No qualified original monster stat row or original server sender supplied",
        "limits": ["The diagnostic area/scene/ordinal identifies an EnyName display row, not a proven wild species template.",
                   "The current quest battle is entered from area 2/scene 15; its area 1/scene 0 enemy display key is borrowed test appearance.",
                   "The diagnostic HP values and BattleActor attack/defense are custom test values.",
                   "Table-name inspection does not exclude all possible schemas or external original data."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=DEFAULT_BINARY)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.binary.resolve(), args.database.resolve(), args.catalog.resolve())
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
