"""Local-artifact capsule integrity tests; no client execution or search."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.crypto_oracle import capsule


@unittest.skipUnless(capsule.DEFAULT_IMAGE.is_file() and capsule.DEFAULT_CLIENT.is_file(),
                     "Pinned local research artifacts are required")
class CapsuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.storage = tempfile.TemporaryDirectory()
        cls.path = capsule.extract(Path(cls.storage.name) / "capsule")
        cls.manifest = capsule.load_capsule(cls.path)

    @classmethod
    def tearDownClass(cls):
        cls.storage.cleanup()

    def setUp(self):
        self.path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def reject_manifest(self, change):
        altered = copy.deepcopy(self.manifest)
        change(altered)
        self.path.write_text(json.dumps(altered), encoding="utf-8")
        with self.assertRaises(capsule.CapsuleError):
            capsule.load_capsule(self.path)

    def test_exact_minimal_ranges_and_abi(self):
        manifest = capsule.load_capsule(self.path)
        self.assertEqual(manifest["entries"], capsule.ENTRIES)
        code = [r for r in manifest["regions"] if r["kind"] == "CODE"]
        self.assertEqual({r["address"] for r in code}, set(capsule.FUNCTIONS))
        self.assertEqual(sum(r["size"] for r in code), 540)
        self.assertEqual(manifest["abi"]["init_session"]["callee_pop_bytes"], 4)
        self.assertFalse(manifest["abi"]["init_session"]["sets_cipher_enabled"])
        self.assertEqual(manifest["abi"]["fields"]["feedback"]["offset"], 0x2556)
        for region in manifest["regions"]:
            self.assertEqual((self.path.parent / region["file"]).stat().st_size, region["size"])
        self.assertEqual([(r["address"], r["size"]) for r in manifest["regions"]
                          if r["kind"] == "CONSTANT_TABLE"], [(0x584C30, 1024)])

    def test_full_source_page_hash(self):
        with capsule.DEFAULT_IMAGE.open("rb") as source:
            source.seek(0x10000)
            expected = hashlib.sha256(source.read(4096)).hexdigest()
        self.assertEqual(self.manifest["code_pages"], [{"rva": 0x10000, "sha256": expected}])

    def test_direct_call_graph(self):
        self.assertEqual(self.manifest["direct_calls"], [
            {"instruction": 0x4104B2, "target": 0x410370},
            {"instruction": 0x4104C9, "target": 0x410420},
            {"instruction": 0x410591, "target": 0x410490},
            {"instruction": 0x410695, "target": 0x410910},
            {"instruction": 0x4106F5, "target": 0x410910},
        ])

    def test_rehashed_artifact_cannot_become_trusted(self):
        region = self.manifest["regions"][0]
        artifact = self.path.parent / region["file"]
        original = artifact.read_bytes()
        try:
            changed = bytes([original[0] ^ 1]) + original[1:]
            artifact.write_bytes(changed)
            with self.assertRaises(capsule.CapsuleError):
                capsule.load_capsule(self.path)
            self.reject_manifest(lambda m: m["regions"][0].update(sha256=hashlib.sha256(changed).hexdigest()))
        finally:
            artifact.write_bytes(original)

    def test_metadata_tampering(self):
        changes = [
            lambda m: m.update(format_version=2),
            lambda m: m.update(format_version=True),
            lambda m: m.update(image_base=0x500000),
            lambda m: m["entries"].update(init_session=0x410500),
            lambda m: m["regions"][0].update(address=0x410371),
            lambda m: m["regions"][0].update(size=4096),
            lambda m: m["regions"].pop(),
            lambda m: m["regions"].append(copy.deepcopy(m["regions"][0])),
            lambda m: m["code_pages"][0].update(sha256="0" * 64),
            lambda m: m["abi"].update(object_size=16),
            lambda m: m["original_exe"].update(sha256="0" * 64),
            lambda m: m["restored_image"].update(sha256="0" * 64),
        ]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                self.reject_manifest(change)

    def test_path_excursions(self):
        for name in ("../outside.bin", "..\\outside.bin", "C:\\outside.bin", "lookup.bin:stream"):
            with self.subTest(name=name):
                self.reject_manifest(lambda m: m["regions"][0].update(file=name))
                with self.assertRaises(capsule.CapsuleError):
                    capsule._artifact_path(self.path.parent, name)
        self.reject_manifest(lambda m: m["restored_image"].update(path="../source.bin"))

    def test_source_bytes_must_match_pin(self):
        wrong = Path(self.storage.name) / "wrong.bin"
        wrong.write_bytes(b"not the approved source")
        for identity in ("restored_image", "original_exe"):
            with self.subTest(identity=identity):
                self.reject_manifest(lambda m: m[identity].update(path=str(wrong.resolve())))
        with self.assertRaises(capsule.CapsuleError):
            capsule.extract(Path(self.storage.name) / "rejected", image_path=wrong)
        self.assertFalse((Path(self.storage.name) / "rejected").exists())

    def test_missing_artifact_rejected(self):
        artifact = self.path.parent / self.manifest["regions"][0]["file"]
        original = artifact.read_bytes()
        try:
            artifact.unlink()
            with self.assertRaises(capsule.CapsuleError):
                capsule.load_capsule(self.path)
        finally:
            artifact.write_bytes(original)

    def test_duplicate_keys_rejected(self):
        self.path.write_text('{"format_version": 1, "format_version": 1}', encoding="utf-8")
        with self.assertRaises(capsule.CapsuleError):
            capsule.load_capsule(self.path)

    def test_unresolved_and_indirect_calls_fail_closed(self):
        # Copy only the code window needed by dependency discovery.
        image = bytearray(0x11000)
        with capsule.DEFAULT_IMAGE.open("rb") as source:
            source.seek(0x10000)
            image[0x10000:0x11000] = source.read(4096)
        site = 0x10695
        original = bytes(image[site:site + 5])
        for replacement in (b"\xe8" + (0x547EB0 - 0x41069A).to_bytes(4, "little"),
                            b"\xff\xd0\x90\x90\x90"):
            image[site:site + 5] = replacement
            with self.assertRaises(capsule.CapsuleError):
                capsule._discover(image)
        image[site:site + 5] = original
        self.assertEqual(capsule._discover(image)[0], sorted(capsule.FUNCTIONS))


if __name__ == "__main__":
    unittest.main()
