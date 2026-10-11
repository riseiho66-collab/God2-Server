"""Build an isolated client DATA candidate for the owner-approved custom skill.

CUSTOM-0058: this is not a client runtime clone implementation or release installer. Existing
definitions, icon actions and native blade3 resources remain byte-identical.
Run from the server root: python -B -m tools.skills.build_shunying_client.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import struct

from PIL import Image

from tools.strike_lab.current_skill_identity import decode_definitions, SOURCE_SHA256
from tools.strike_lab.omega_assets import decode_csvz

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / "God2"
OUTPUT = ROOT / "artifacts/custom-skills/shunying/client-candidate"
ICON = Path("C:/Users/risei/AppData/Local/Temp/codex-clipboard-85f8c9f4-0d9d-4309-9ecb-3f4f4f6748b3.png")
NAME = "瞬影三煞斬"
CATALOG = "Data2/Fight/Spg/cbspec2.bin"
ICONS = "Data2/ItmImg/Ski01.romZ"
ROUTES = "Data2/Patch/SpgEft.csvZ"
DISPLAY_ITEMS = "Data2/Patch/Comm/gamedata.csvZ"
DISPLAY_ITEMS_GB = "Data2/Patch/Comm/gamedata-gb.csvZ"
PINS = {
    CATALOG: SOURCE_SHA256,
    ICONS: "50844735316f6989efc2c56a261ddb830b0815cee9f975745f6a3a0b4c61f6ea",
    ROUTES: "1c68e9e79028dc79f2110e0749bb5bdbe1f6f0cafaa6583006a397192ec1104f",
    DISPLAY_ITEMS: "70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731",
    DISPLAY_ITEMS_GB: "66c296fa27ebfbaa9434cb3e3707e23b79828b37ce7a0129d439b393ff00a7ff",
    "Data2/Fight/Spg/spg9006.ROMZ": "a5a93b93f0e67e57aad426236287575312d31bcaec52c8b7ac60619492c7d411",
    "Data2/Fight/Spg/spg9008.rtb": "ed4b7690d0f9c30d52e6e32ae9c011835c7d2267e3f6406a14683449eca4446a",
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def wrapped_literals(plain: bytes) -> bytes:
    """Valid native 05 16 LZSS stream; literals avoid new compressor semantics."""
    return b"\x05\x16" + struct.pack("<I", len(plain)) + b"\x00" + b"".join(
        b"\xff" + plain[i:i + 8] for i in range(0, len(plain), 8))


def chunks(plain: bytes):
    if plain[:12] != b"IGSROM02\0\0\0\0":
        raise ValueError("Unexpected native ROM header")
    pos = 12
    while pos < len(plain):
        tag, size = struct.unpack_from("<8sI", plain, pos)
        end = pos + 12 + size
        if end > len(plain):
            raise ValueError("Truncated native ROM chunk")
        yield tag, plain[pos + 12:end], plain[pos:end]
        pos = end


def chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack("<8sI", tag, len(data)) + data


def make_catalog(source: bytes):
    if sha(source) != SOURCE_SHA256:
        raise ValueError("Source catalog differs from qualified original; refusing overwrite")
    original = decode_definitions(source)
    if any((0, i) in original for i in range(122,127)) or struct.unpack_from("<I", source, 4)[0] != 121:
        raise ValueError("Expected original bank0 ending at121, reserve122..125 and skill126")
    base = original[0, 8]
    assert base.raw[2:32].split(b"\0")[0].decode("cp950") == "刀術Lv3"
    record = bytearray(base.raw)
    record[0] = 126
    # +3E is a separately consumed WORD. Constrain short text to [20,3E)
    # even though historical inventory scripts decoded the wider [20,40).
    for at, size, text in [(2, 30, NAME), (32, 30, NAME + " 最多三敵")]:
        encoded = text.encode("cp950")
        if len(encoded) >= size:
            raise ValueError("Custom name exceeds native NUL-terminated field")
        record[at:at + size] = encoded.ljust(size, b"\0")
    record[0x44] = 7  # CUSTOM-0058: any occupied enemy row, not the native blade3 reach3.
    record[0x45] = 16  # CUSTOM-0058: native three-target per-record command mode; UI acceptance pending.
    at = 8 + 125 * 110
    if any(source[8 + 121 * 110:at + 110]):
        raise ValueError("Unused skill slot has nonzero data")
    result = bytearray(source)
    struct.pack_into("<I", result, 4, 126)
    for identity in range(122,126):
        reserved = bytearray(110)
        reserved[0] = identity
        reserved[2:32] = "預留技能".encode("cp950").ljust(30, b"\0")
        offset = 8 + (identity - 1) * 110
        result[offset:offset + 110] = reserved
    result[at:at + 110] = record
    parsed = decode_definitions(bytes(result))
    assert len(parsed) == 453 and parsed[0, 126].raw == record
    assert all(parsed[key] == value for key, value in original.items())
    assert record[62:68] == base.raw[62:68] and record[70:] == base.raw[70:]
    return bytes(result), dict(base_kind=0, base_id=8, new_kind=0, new_id=126, reserved_ids=list(range(122,126)),
        record_offset=at, record_sha256=sha(record), preserved_original_records=len(original),
        changed_fields=["id", "name", "short_name", "reach_44", "target_mode_45"],
        reach_44=dict(value=7, native_blade3_value=3, origin="CUSTOM-0058_ANY_ENEMY_ROW"),
        target_mode_45=dict(value=16, origin="CUSTOM-0058_CANDIDATE_MAPPING",
            native_lookup_result=[3, 0], native_ui_max_count_verified=False,
            optional_fewer_targets_confirmation_verified=False),
        inherited_opaque_fields="All remaining blade3 bytes unchanged; no native damage formula inferred")


def make_icons(source: bytes, image: Image.Image):
    plain = decode_csvz(source)
    parts = list(chunks(plain))
    actions = [struct.unpack_from("<i", data)[0] for tag, data, _ in parts if tag == b"ACT_DATA"]
    images = sum(tag.endswith(b"_RWIF") for tag, _, _ in parts)
    if actions != list(range(21001, 21121)) or images != 119:
        raise ValueError("Unexpected native Ski01 layout; preserve and investigate")
    assert parts[-1][:2] == (b"FILE_END", b"")
    template = next(data for tag, data, _ in parts
        if tag == b"ACT_DATA" and struct.unpack_from("<i", data)[0] == 21008)
    rgba = image.convert("RGBA").resize((40, 40), Image.Resampling.LANCZOS)
    # Native ABGR4444 words, followed by per-row [first,last-exclusive] spans.
    pixels = list(rgba.get_flattened_data()) if hasattr(rgba, "get_flattened_data") else list(rgba.getdata())
    words = [(a // 17 << 12) | (b // 17 << 8) | (g // 17 << 4) | (r // 17)
             for r, g, b, a in pixels]
    spans = []
    for y in range(40):
        visible = [x for x in range(40) if words[y * 40 + x] >> 12]
        spans.extend((min(visible), max(visible) + 1) if visible else (0, 0))
    bitmap = struct.pack("<II", 40, 40) + struct.pack("<1600H", *words) + struct.pack("<80H", *spans)
    # Put new bitmap after original bitmaps and before actions. Existing image
    # ordinal references and complete original chunks are preserved.
    insertion = next(i for i, (tag, _, _) in enumerate(parts) if tag == b"ACT_DATA")
    out = plain[:12] + b"".join(p[2] for p in parts[:insertion]) + chunk(b"TGA_RWIF", bitmap)
    out += b"".join(p[2] for p in parts[insertion:-1])
    for code in range(21121,21127):
        populated = code == 21126
        header = bytearray(template)
        struct.pack_into("<i", header, 0, code)
        struct.pack_into("<2i", header, 16, int(populated), int(populated))
        header[24:48] = (NAME.encode("cp950") if populated else ("reserved" + str(code - 21000)).encode()).ljust(24, b"\0")
        out += chunk(b"ACT_DATA", bytes(header))
        if populated:
            out += chunk(b"ACT_STEP", bytes.fromhex("00000100010000000000"))
            out += chunk(b"ACT_POOL", struct.pack("<hhBBHH", 0, 0, 0, 0, images, 0x030d))
            out += chunk(b"ACTBLOCK", struct.pack("<5H", 0, 0, 40, 40, 0))
    out += parts[-1][2]  # Native loader stops here: all new actions precede FILE_END.
    final = list(chunks(out))
    original_parts = final[:insertion] + final[insertion + 1:len(parts)] + [final[-1]]
    assert [x[2] for x in original_parts] == [x[2] for x in parts]
    assert [i for i, (tag, _, _) in enumerate(final) if tag == b"FILE_END"] == [len(final) - 1]
    codes = [struct.unpack_from("<i", data)[0] for tag, data, _ in final if tag == b"ACT_DATA"]
    assert codes == list(range(21001, 21127))
    encoded = wrapped_literals(out)
    assert decode_csvz(encoded) == out
    return encoded, rgba, dict(native_icon_bank=1, action_index=125, action_code=21126,
        image_index=119, size=[40, 40], pixel_format="ABGR4444 TGA_RWIF", original_chunks_preserved=len(parts),
        original_actions_preserved=120, placeholder_actions=list(range(21121,21126)))


def make_routes(source: bytes):
    plain = decode_csvz(source)
    lines = plain.decode("cp950").replace("\r\r\n", "\n").splitlines()
    rows = list(csv.reader(lines))
    matches = [row for row in rows if len(row) > 5 and row[0] == "r1" and row[1] == "8"]
    assert len(matches) == 1
    assert not any(len(row) > 1 and row[0] == "r1" and row[1] in tuple(map(str,range(122,127))) for row in rows)
    row = matches[0].copy()
    assert row[2] == "9008" and row[5] == "324"
    row[1] = "126"
    row[6] = NAME + " CUSTOM candidate; native blade3 visual only"
    stream = io.StringIO(newline="")
    csv.writer(stream, lineterminator="\r\r\n").writerow(row)
    result = plain + (b"" if plain.endswith(b"\n") else b"\r\r\n") + stream.getvalue().encode("cp950")
    encoded = wrapped_literals(result)
    assert decode_csvz(encoded).startswith(plain)
    return encoded, row


def make_display_items(source: bytes, *, simplified: bool = False):
    """Supply the native SpcA126 name lookup; cbspec2 names are not used here.

    004A8E10 scans SKB IDs 6501..6899 for alias SpcA126. 0051BE90 reads
    the matching metadata name at +8 for the F1 battle prompt. Without this
    row the native caller uses its uninitialized output ID/name buffer.
    CUSTOM-0058: 6897 is unused in both pinned sources and within ItemType SKB.
    This client display metadata does not grant or sell a skill book.
    """
    relative = DISPLAY_ITEMS_GB if simplified else DISPLAY_ITEMS
    if sha(source) != PINS[relative]:
        raise ValueError("Unqualified skill display metadata source")
    plain = decode_csvz(source)
    lines = plain.splitlines(keepends=True)
    headers = [i for i, line in enumerate(lines) if line.rstrip(b"\r\n") == b"SKB,381"]
    if len(headers) != 1:
        raise ValueError("Expected original SKB section")
    at = headers[0]
    rows = [line.rstrip(b"\r\n").split(b",") for line in lines[at + 1:at + 382]]
    if any(row[0] == b"6897" or row[26] == b"SpcA126" for row in rows):
        raise ValueError("Custom skill display ID or alias already occupied")
    base = next(row for row in rows if row[0] == b"6508" and row[26] == b"SpcA08")
    row = base.copy()
    row[0], row[2], row[3], row[26] = b"6897", b"Spc01126", b"21126", b"SpcA126"
    row[4] = ("瞬影三煞斩" if simplified else NAME).encode("cp936" if simplified else "cp950")
    ending = lines[at][len(lines[at].rstrip(b"\r\n")):]
    inserted = b",".join(row) + ending
    lines[at] = b"SKB,382" + ending
    lines.insert(at + 382, inserted)
    result = b"".join(lines)
    # Remove only our row/count change: every original decoded byte must remain.
    restored = lines.copy()
    del restored[at + 382]
    restored[at] = b"SKB,381" + ending
    assert b"".join(restored) == plain
    encoded = wrapped_literals(result)
    assert decode_csvz(encoded) == result
    return encoded, dict(item_id=6897, skill_alias="SpcA126", icon=21126,
        encoding="cp936" if simplified else "cp950", original_rows_preserved=381,
        changed_columns=[0, 2, 3, 4, 26], name_hex=row[4].hex(),
        original_decoded_bytes_preserved=True, current_client_display=False)


def render_native_icon(encoded: bytes) -> Image.Image:
    """Resolve new ACT_STEP -> ACT_POOL -> TGA_RWIF, decode native stored pixels."""
    parts = list(chunks(decode_csvz(encoded)))
    images = [(tag, data) for tag, data, _ in parts if tag.endswith(b"_RWIF")]
    current = None
    steps, pools = [], []
    for tag, data, _ in parts:
        if tag == b"ACT_DATA":
            current = struct.unpack_from("<i", data)[0]
        elif current == 21126 and tag == b"ACT_STEP":
            steps.append(data)
        elif current == 21126 and tag == b"ACT_POOL":
            pools.append(data)
    assert len(steps) == len(pools) == 1 and steps[0][0] == 0
    pool_index = steps[0][3]
    px, py, flip_x, flip_y, image_index, _ = struct.unpack("<hhBBHH", pools[pool_index])
    assert (px, py, flip_x, flip_y, image_index) == (0, 0, 0, 0, 119)
    tag, pixels = images[image_index]
    assert tag == b"TGA_RWIF"
    width, height = struct.unpack_from("<II", pixels)
    assert (width, height) == (40, 40) and len(pixels) == 8 + width * height * 2 + height * 4
    decoded = Image.new("RGBA", (width, height))
    for y in range(height):
        first, end = struct.unpack_from("<HH", pixels, 8 + width * height * 2 + y * 4)
        assert 0 <= first <= end <= width
        for x in range(first, end):
            value = struct.unpack_from("<H", pixels, 8 + (y * width + x) * 2)[0]
            # Native 16-bit renderer: RGB nibble -> 5-bit channel (n<<1),
            # and alpha/16. Use the on-disk sprite, not the pre-conversion PNG.
            decoded.putpixel((x, y), ((value & 15) * 2 * 255 // 31,
                ((value >> 4) & 15) * 2 * 255 // 31,
                ((value >> 8) & 15) * 2 * 255 // 31, (value >> 12) * 255 // 16))
    return decoded


def build(client: Path = CLIENT, icon: Path = ICON, output: Path = OUTPUT):
    client, output = client.resolve(), output.resolve()
    if output != OUTPUT.resolve():
        raise ValueError("Candidate output is fixed; this tool cannot install into the live client")
    sources = {}
    def read(relative):
        raw = (client / relative).read_bytes()
        sources[relative] = sha(raw)
        if sources[relative] != PINS[relative]:
            raise ValueError("Unqualified source hash: " + relative)
        return raw
    catalog, catalog_info = make_catalog(read(CATALOG))
    with Image.open(icon) as supplied:
        icons, scaled, icon_info = make_icons(read(ICONS), supplied)
    routes, route_info = make_routes(read(ROUTES))
    payloads = {CATALOG: catalog, ICONS: icons, ROUTES: routes}
    display_info = {}
    for relative, simplified in ((DISPLAY_ITEMS, False), (DISPLAY_ITEMS_GB, True)):
        payloads[relative], display_info[relative] = make_display_items(read(relative), simplified=simplified)
    # Include the exact existing resources for reproducible handoff; never bake
    # a particular actor into slash sprites or replace native slash colors.
    for relative in ["Data2/Fight/Spg/spg9006.ROMZ", "Data2/Fight/Spg/spg9008.rtb"]:
        payloads[relative] = read(relative)
    for relative, raw in payloads.items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    scaled.save(output / "icon-40.png")
    render_native_icon(icons).save(output / "icon-native-decoded.png")
    (output / "icon-user-source.png").write_bytes(icon.read_bytes())
    for relative, expected in sources.items():
        assert sha((client / relative).read_bytes()) == expected, "Source was mutated"
    report = dict(skill=NAME, custom_design_id="CUSTOM-0058", status="CUSTOM_DATA_CANDIDATE_NOT_RUNTIME_ACCEPTED", installed=False,
        source_client=str(client), icon_source=str(icon), icon_source_sha256=sha(icon.read_bytes()),
        source_sha256=sources, output_sha256={k: sha(v) for k, v in payloads.items()},
        catalog=catalog_info, icon=icon_info, resource_route=route_info, display_metadata=display_info,
        acceptance=dict(catalog_parse=True, original_records_preserved=True, native_icon_pool_decode=True,
            original_icon_chunks_preserved=True, compressed_roundtrip=True,
            current_client_display=False, manual_target_confirmation=False,
            dynamic_caster_clones=False, native_hit_damage_timing=False),
        remaining=["Current-client selection and optional one/two/three-target confirmation",
            "Native action routing for new id126; native blade3 actor animation has not been proved for new id",
            "Dynamic caster appearance, flank clone spawn and enemy-facing clone renderer",
            "Per-target original blade3 hit events and floating damage synchronization",
            "Live own-server cast, settlement and natural return acceptance"])
    (output / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client", type=Path, default=CLIENT)
    parser.add_argument("--icon", type=Path, default=ICON)
    args = parser.parse_args()
    report = build(args.client, args.icon)
    print(json.dumps({"output": str(OUTPUT), "status": report["status"], "checks": report["acceptance"]}))
