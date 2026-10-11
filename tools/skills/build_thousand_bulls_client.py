"""Candidate-only skill150 DATA extension, pinned to accepted post-Shunying client."""
from pathlib import Path
import csv
import io
import json
import struct
from PIL import Image
from tools.skills.build_shunying_client import (ROOT, CLIENT, CATALOG, ICONS, ROUTES,
    DISPLAY_ITEMS, DISPLAY_ITEMS_GB, chunks, chunk, sha, wrapped_literals, decode_csvz,
    decode_definitions)

OUTPUT = ROOT / "artifacts/custom-skills/thousand-bulls/client-candidate"
RELEASE = ROOT / "artifacts/releases/shunying-production-20260930/client-release.json"
PREVIEW = Path("C:/Users/risei/Desktop/封神OL技能模擬預覽")
ICON_SOURCE = ROOT / "artifacts/custom-skills/thousand-bulls/icon-redesign/bull-facing-player.png"
NAME = "牛轉仙界踏"
FILES = (CATALOG, ICONS, ROUTES, DISPLAY_ITEMS, DISPLAY_ITEMS_GB)


def make_catalog(source):
    original = decode_definitions(source)
    assert len(original) == 453 and struct.unpack_from("<I", source, 4)[0] == 126
    base = original[0, 73].raw
    assert base[68:70] == b"\x05\x05" and struct.unpack_from("<H", base, 66)[0] == 100
    out = bytearray(source)
    assert not any(out[8 + 126 * 110:8 + 150 * 110])
    struct.pack_into("<I", out, 4, 150)
    for identity in range(127, 151):
        record = bytearray(base if identity == 150 else bytes(110))
        record[0] = identity
        text = NAME if identity == 150 else "預留技能"
        record[2:32] = text.encode("cp950").ljust(30, b"\0")
        if identity == 150:
            record[32:62] = (NAME + " 全體物理").encode("cp950").ljust(30, b"\0")
        at = 8 + (identity - 1) * 110
        out[at:at + 110] = record
    parsed = decode_definitions(bytes(out))
    assert len(parsed) == 477 and all(parsed[k] == v for k, v in original.items())
    assert parsed[0, 150].raw[62:] == base[62:]
    return bytes(out), {"preserved_records": 453, "reserved": list(range(127, 150)),
        "base": 73, "reach": 5, "mode": 5, "mp": 100,
        "note": "10x physical damage is server authority; opaque native fields inherited unchanged"}


def make_icons(source, image):
    plain = decode_csvz(source)
    parts = list(chunks(plain))
    actions = [struct.unpack_from("<i", d)[0] for t, d, _ in parts if t == b"ACT_DATA"]
    images = sum(t.endswith(b"_RWIF") for t, _, _ in parts)
    assert actions == list(range(21001, 21127)) and images == 120 and len(parts) == 610
    template = next(d for t, d, _ in parts if t == b"ACT_DATA" and struct.unpack_from("<i", d)[0] == 21126)
    rgba = image.convert("RGBA")
    rgba = rgba.crop(rgba.getbbox())
    rgba.thumbnail((38, 38), Image.Resampling.LANCZOS)
    icon = Image.new("RGBA", (40, 40))
    icon.alpha_composite(rgba, ((40 - rgba.width) // 2, (40 - rgba.height) // 2))
    words = [(a // 17 << 12) | (b // 17 << 8) | (g // 17 << 4) | (r // 17)
             for r, g, b, a in icon.getdata()]
    spans = []
    for y in range(40):
        visible = [x for x in range(40) if words[y * 40 + x] >> 12]
        spans.extend((min(visible), max(visible) + 1) if visible else (0, 0))
    bitmap = struct.pack("<II1600H80H", 40, 40, *words, *spans)
    insertion = next(i for i, (t, _, _) in enumerate(parts) if t == b"ACT_DATA")
    extra = [chunk(b"TGA_RWIF", bitmap)]
    added = []
    for code in range(21127, 21151):
        populated = code == 21150
        header = bytearray(template)
        struct.pack_into("<i", header, 0, code)
        struct.pack_into("<2i", header, 16, int(populated), int(populated))
        header[24:48] = (NAME.encode("cp950") if populated else ("reserved" + str(code-21000)).encode()).ljust(24, b"\0")
        added.append(chunk(b"ACT_DATA", bytes(header)))
        if populated:
            added.extend([chunk(b"ACT_STEP", bytes.fromhex("00000100010000000000")),
                chunk(b"ACT_POOL", struct.pack("<hhBBHH", 0, 0, 0, 0, images, 0x030d)),
                chunk(b"ACTBLOCK", struct.pack("<5H", 0, 0, 40, 40, 0))])
    result = plain[:12] + b"".join(x[2] for x in parts[:insertion]) + b"".join(extra)
    result += b"".join(x[2] for x in parts[insertion:-1]) + b"".join(added) + parts[-1][2]
    final = list(chunks(result))
    restored = final[:insertion] + final[insertion + 1:len(parts)] + [final[-1]]
    assert [p[2] for p in restored] == [p[2] for p in parts]
    assert [struct.unpack_from("<i", d)[0] for t, d, _ in final if t == b"ACT_DATA"] == list(range(21001, 21151))
    encoded = wrapped_literals(result)
    assert decode_csvz(encoded) == result
    # Independently decode appended native ABGR4444 words for QA.
    decoded = Image.new("RGBA", (40, 40))
    for i, value in enumerate(struct.unpack_from("<1600H", bitmap, 8)):
        decoded.putpixel((i % 40, i // 40), ((value & 15)*2*255//31, ((value>>4)&15)*2*255//31,
            ((value>>8)&15)*2*255//31, (value>>12)*255//16))
    return encoded, icon, decoded, {"preserved_chunks": 610, "preserved_actions": 126,
        "image_index": images, "action_index": 149, "action_code": 21150, "format": "ABGR4444"}


def make_routes(source):
    plain = decode_csvz(source)
    rows = list(csv.reader(plain.decode("cp950").splitlines()))
    row = next(r.copy() for r in rows if r[:2] == ["r1", "73"])
    assert row[2] == "9073" and row[5] == "542"
    assert not any(r[:2] == ["r1", "150"] for r in rows)
    row[1], row[5], row[6] = "150", "-1", NAME + " custom native compositor"
    stream = io.StringIO(newline="")
    csv.writer(stream, lineterminator="\r\r\n").writerow(row)
    result = plain + (b"" if plain.endswith(b"\n") else b"\r\r\n") + stream.getvalue().encode("cp950")
    encoded = wrapped_literals(result)
    assert decode_csvz(encoded).startswith(plain)
    return encoded, row


def make_display(source, simplified):
    plain = decode_csvz(source)
    lines = plain.splitlines(keepends=True)
    at = next(i for i, line in enumerate(lines) if line.rstrip(b"\r\n") == b"SKB,382")
    rows = [line.rstrip(b"\r\n").split(b",") for line in lines[at+1:at+383]]
    assert len(rows) == 382 and not any(r[0] == b"6898" or r[26] == b"SpcA150" for r in rows)
    row = next(r.copy() for r in rows if r[26] == b"SpcA73")
    row[0], row[2], row[3], row[26] = b"6898", b"Spc01150", b"21150", b"SpcA150"
    codec = "cp936" if simplified else "cp950"
    row[4] = ("牛转仙界踏" if simplified else NAME).encode(codec)
    row[8] = ("全体物理技能" if simplified else "全體物理技能").encode(codec)
    row[9] = ("使用消耗 100 MP").encode(codec)
    row[10] = ("物理攻击 10倍" if simplified else "物理攻擊 10倍").encode(codec)
    ending = lines[at][len(lines[at].rstrip(b"\r\n")):]
    lines[at] = b"SKB,383" + ending
    lines.insert(at+383, b",".join(row)+ending)
    result = b"".join(lines)
    del lines[at+383]
    lines[at] = b"SKB,382" + ending
    assert b"".join(lines) == plain
    encoded = wrapped_literals(result)
    assert decode_csvz(encoded) == result
    return encoded, {"item_id": 6898, "alias": "SpcA150", "encoding": codec,
        "name_hex": row[4].hex(), "preserved_rows": 382, "grants_skill": False}


def build(client=CLIENT, output=OUTPUT):
    if Path(output).resolve() != OUTPUT.resolve():
        raise ValueError("Only isolated candidate output is allowed")
    pins = {e["path"]: e["sha256"] for e in json.loads(RELEASE.read_text())["files"]}
    sources = {name: (client/name).read_bytes() for name in FILES}
    for name, data in sources.items():
        if sha(data) != pins[name]:
            raise ValueError("Formal post-Shunying pin mismatch: " + name)
    out, detail = {}, {}
    out[CATALOG], detail[CATALOG] = make_catalog(sources[CATALOG])
    # Owner-approved icon direction: toward the player side, no ground shadow,
    # native-style skill background. Keep animation-frame assets independent.
    icon_source = ICON_SOURCE
    with Image.open(icon_source) as image:
        out[ICONS], icon, decoded, detail[ICONS] = make_icons(sources[ICONS], image)
    out[ROUTES], detail[ROUTES] = make_routes(sources[ROUTES])
    for name, simplified in [(DISPLAY_ITEMS, False), (DISPLAY_ITEMS_GB, True)]:
        out[name], detail[name] = make_display(sources[name], simplified)
    for name, data in out.items():
        file = output/name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
    icon.save(output/"icon-40.png")
    decoded.save(output/"icon-native-decoded.png")
    report = {"skill": NAME, "kind": 0, "id": 150, "status": "CANDIDATE_DATA_NOT_INSTALLED", "installed": False,
        "source_client": str(client), "release_manifest_sha256": sha(RELEASE.read_bytes()),
        "source_sha256": {k: sha(v) for k, v in sources.items()}, "output_sha256": {k: sha(v) for k, v in out.items()},
        "icon_source": str(icon_source), "icon_source_sha256": sha(icon_source.read_bytes()), "details": detail}
    (output/"manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    assert all(sha((client/k).read_bytes()) == sha(v) for k, v in sources.items())
    return report


if __name__ == "__main__":
    result = build()
    print(json.dumps({"status": result["status"], "id": result["id"], "output": str(OUTPUT)}))
