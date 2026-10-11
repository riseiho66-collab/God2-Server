"""Independent bounds/integrity checks for the native fixed-field visual pack."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import wave


def verify(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert (manifest["width"], manifest["height"], manifest["frames"], manifest["fps"]) == (1040, 807, 240, 30)
    clip=manifest['clip']
    assert clip in ({'x':0,'y':99,'width':1040,'height':660},{'x':0,'y':0,'width':1040,'height':807})
    results = []
    for entry in manifest["files"]:
        file = root / entry["path"]
        digest = hashlib.sha256()
        with file.open("rb") as stream:
            while block := stream.read(1024 * 1024):
                digest.update(block)
        assert digest.hexdigest() == entry["sha256"]
        with file.open("rb") as stream:
            assert stream.read(8) == b"BULLFX01"
            assert struct.unpack("<4I", stream.read(16)) == (1040, 807, 240, 30)
            entries = [struct.unpack("<QI", stream.read(12)) for _ in range(240)]
            end = 24 + 240 * 12
            total_spans = 0
            visible = []
            upper_pixels = 0
            for tick, (offset, size) in enumerate(entries):
                assert offset == end and size >= 4
                stream.seek(offset)
                payload = stream.read(size)
                assert len(payload) == size
                count, = struct.unpack_from("<I", payload)
                cursor = 4
                previous = (-1, -1)
                for _ in range(count):
                    x, y, length, reserved = struct.unpack_from("<4H", payload, cursor)
                    cursor += 8
                    assert reserved == 0 and 0 < length <= 1040 and x + length <= 1040
                    assert clip['y'] <= y < clip['y']+clip['height'] and (y, x) > previous
                    if tick in (70,110,150,190) and y<99:upper_pixels += length
                    previous = y, x
                    assert cursor + length * 4 <= size
                    assert all(payload[cursor + 3:cursor + length * 4:4])
                    cursor += length * 4
                assert cursor == size
                if count:
                    visible.append(tick)
                total_spans += count
                end = offset + size
            assert end == file.stat().st_size == entry["bytes"]
            assert not any(tick < 25 for tick in visible)
            assert 239 not in visible
            assert 110 in visible and 190 in visible
            if clip['y']==0 and entry['path'].endswith('foreground.bfx'):
                assert upper_pixels>1000, 'Missing restored upper-edge pixels'
            results.append({"file": entry["path"], "frames": 240, "spans": total_spans,
                            "restored_upper_pixels_at_impacts":upper_pixels,
                            "first_visible": min(visible), "last_visible": max(visible), "sha256": digest.hexdigest()})
    for sample in manifest["samples"]:
        assert sample["friendly_max_alpha"] <= .18000001
    for entry in manifest["audio"]:
        assert hashlib.sha256((root / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    with wave.open(str(root / "bull-stampede-native-voice.wav")) as wav:
        assert (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()) == (1, 2, 44100, 352800)
    source = Path(manifest["source_root"])
    for name, pin in manifest["source_pins"].items():
        assert hashlib.sha256((source / name).read_bytes()).hexdigest() == pin
    return {"status": "PASS", "files": results, "source_pin_count": len(manifest["source_pins"]),
            "audio_seconds": 8, "scope": "offline visualpack integrity, not in-client acceptance"}


if __name__ == "__main__":
    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "artifacts/custom-skills/thousand-bulls/visualpack")
    result = verify(folder)
    (folder / "verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
