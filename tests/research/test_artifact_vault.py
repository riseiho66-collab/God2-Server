"""Static-only vault tests; synthetic PE bytes are never executed."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools/research/artifact_vault.py"
SPEC = importlib.util.spec_from_file_location("artifact_vault_under_test", MODULE_PATH)
vault_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vault_module)


def synthetic_pe(marker=0, virtual_size=0x300):
    """One PE32 section, with distinct raw (0x200) and virtual (0x1000) offsets."""
    data = bytearray(0x400)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 0x84, 0x14C, 1, 0, 0, 0, 0xE0, 0x102)
    optional = 0x98
    struct.pack_into("<H", data, optional, 0x10B)
    struct.pack_into("<III", data, optional + 16, 0x1000, 0x1000, 0x1000)
    struct.pack_into("<III", data, optional + 28, 0x400000, 0x1000, 0x200)
    struct.pack_into("<HH", data, optional + 40, 4, 0)
    struct.pack_into("<HH", data, optional + 48, 4, 0)
    struct.pack_into("<II", data, optional + 56, 0x2000, 0x200)
    struct.pack_into("<H", data, optional + 68, 3)
    struct.pack_into("<IIII", data, optional + 72, 0x100000, 0x1000, 0x100000, 0x1000)
    struct.pack_into("<I", data, optional + 92, 16)
    struct.pack_into("<8sIIIIIIHHI", data, 0x178, b".text\0\0\0", virtual_size,
                     0x1000, 0x200, 0x200, 0, 0, 0, 0, 0x60000020)
    data[0x200:] = bytes((index + marker) % 256 for index in range(0x200))
    return bytes(data)


class ArtifactVaultTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.vault = vault_module.Vault(self.base / "vault")
        self.source = self.base / "synthetic.exe"
        self.source.write_bytes(synthetic_pe())

    def ingest(self, marker=0, **kwargs):
        source = self.base / f"synthetic-{marker}.exe"
        source.write_bytes(synthetic_pe(marker))
        return self.vault.ingest(source, **kwargs)["artifact_id"]

    def rewrite_metadata(self, artifact_id, mutate, update_manifest=False):
        folder = self.vault.location(artifact_id)
        path = folder / "metadata.json"
        metadata = json.loads(path.read_bytes())
        mutate(metadata)
        raw = vault_module.json_bytes(metadata)
        path.write_bytes(raw)
        if update_manifest:
            manifest_path = folder / "hashes.json"
            manifest = json.loads(manifest_path.read_bytes())
            manifest["metadata_sha256"] = hashlib.sha256(raw).hexdigest()
            manifest_path.write_bytes(vault_module.json_bytes(manifest))

    def test_minimal_pe_is_valid_static_input(self):
        self.assertEqual(vault_module.pefile.__version__, "2024.8.26")
        pe = vault_module.inspect_pe(synthetic_pe())
        self.assertEqual(pe["architecture"], "x86")
        self.assertEqual(pe["entry_va"], 0x401000)
        self.assertEqual(pe["imports"], [])
        self.assertFalse(pe["pe_timestamp_trusted"])
        section, = pe["sections"]
        self.assertEqual((section["raw_offset"], section["rva"]), (0x200, 0x1000))
        self.assertEqual(section["raw_sha256"], hashlib.sha256(synthetic_pe()[0x200:]).hexdigest())

    def test_idempotent_ingestion_records_multiple_sources(self):
        first = self.vault.ingest(self.source)
        folder = self.vault.location(first["artifact_id"])
        before = (folder / "metadata.json").read_bytes()
        other = self.base / "copy.exe"
        other.write_bytes(self.source.read_bytes())
        self.assertEqual(self.vault.ingest(self.source), first)
        self.assertEqual(self.vault.ingest(other), first)
        self.assertEqual((folder / "metadata.json").read_bytes(), before)
        self.assertEqual(self.vault.ids(), [first["artifact_id"]])
        db = self.vault.connect()
        try:
            self.assertEqual(db.execute("SELECT count(*) FROM artifacts").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT count(*) FROM evidence").fetchone()[0], 1)
            paths = {row[0] for row in db.execute("SELECT path FROM sources")}
            self.assertEqual(paths, {str(self.source.resolve()), str(other.resolve())})
        finally:
            db.close()
        self.vault.verify(first["artifact_id"])

    def test_original_and_derived_provenance(self):
        parent = self.ingest()
        child = self.ingest(1, kind="unpacked", parent=parent)
        original = self.vault.verify(parent)
        derived = self.vault.verify(child)
        self.assertIsNone(original["parent_artifact"])
        self.assertEqual(original["unpack_status"], "NOT_ATTEMPTED")
        self.assertEqual(derived["parent_artifact"], parent)
        self.assertEqual(derived["unpack_status"], "UNVERIFIED_CANDIDATE")
        for artifact_id, slot in ((parent, "original"), (child, "unpacked")):
            self.assertTrue((self.vault.location(artifact_id) / slot / "client.exe").is_file())
            self.assertEqual(self.vault.verify(artifact_id)["oep_status"], "UNKNOWN")
        with self.assertRaises(ValueError):
            self.ingest(1)

    def test_invalid_parent_relations(self):
        parent = self.ingest()
        cases = [dict(kind="unpacked"), dict(parent=parent), dict(kind="bogus"),
                 dict(kind="unpacked", parent=parent),
                 dict(kind="unpacked", parent="../outside"),
                 dict(kind="unpacked", parent="f" * 64)]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises((ValueError, OSError)):
                self.vault.ingest(self.source, **kwargs)
        self.assertEqual(self.vault.ids(), [parent])

    def test_artifact_ids_reject_traversal_and_noncanonical_hashes(self):
        for artifact_id in ("../outside", "..\\outside", "/tmp/outside", "C:\\outside",
                            "a" * 63, "A" * 64, "a" * 64 + "\n", "a" * 64 + "/.."):
            with self.subTest(artifact_id=artifact_id), self.assertRaises(ValueError):
                self.vault.location(artifact_id)

    def test_binary_tamper_detected_by_verify_and_reingest(self):
        artifact_id = self.ingest()
        binary = self.vault.location(artifact_id) / "original/client.exe"
        data = bytearray(binary.read_bytes())
        data[-1] ^= 1
        binary.write_bytes(data)
        with self.assertRaises(ValueError):
            self.vault.verify(artifact_id)
        with self.assertRaises(ValueError):
            self.vault.ingest(self.source)

    def test_metadata_tamper_detected(self):
        artifact_id = self.ingest()
        self.rewrite_metadata(artifact_id, lambda meta: meta.update(initial_source="forged"))
        with self.assertRaises(ValueError):
            self.vault.verify(artifact_id)

    def test_rehashed_static_metadata_tamper_detected_without_index(self):
        artifact_id = self.ingest()
        self.rewrite_metadata(artifact_id, lambda meta: meta["pe"].update(entry_rva=0x1234), True)
        with self.assertRaises(ValueError):
            self.vault.verify(artifact_id, check_index=False)

    def test_rehashed_provenance_metadata_tamper_detected_by_index(self):
        artifact_id = self.ingest()
        self.rewrite_metadata(artifact_id, lambda meta: meta.update(initial_source="forged"), True)
        with self.assertRaises(ValueError):
            self.vault.verify(artifact_id)

    def test_truncated_pe_rejected_before_publication(self):
        for length in (0, 0x80, 0x178, 0x190, 0x200, 0x3FF):
            with self.subTest(length=length):
                self.source.write_bytes(synthetic_pe()[:length])
                with self.assertRaises(ValueError):
                    self.vault.ingest(self.source)
                self.assertEqual(self.vault.ids(), [])

    def test_truncated_stored_binary_rejected(self):
        artifact_id = self.ingest()
        binary = self.vault.location(artifact_id) / "original/client.exe"
        binary.write_bytes(binary.read_bytes()[:-1])
        with self.assertRaises(ValueError):
            self.vault.verify(artifact_id)

    def test_child_verification_detects_parent_binary_tamper(self):
        parent = self.ingest()
        child = self.ingest(1, kind="unpacked", parent=parent)
        binary = self.vault.location(parent) / "original/client.exe"
        binary.write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            self.vault.verify(child)

    def test_reingest_rejects_index_provenance_tamper(self):
        artifact_id = self.ingest()
        db = self.vault.connect()
        try:
            with db:
                db.execute("UPDATE artifacts SET kind='unpacked' WHERE id=?", (artifact_id,))
        finally:
            db.close()
        with self.assertRaises(ValueError):
            self.vault.ingest(self.source)

    def test_candidate_maps_raw_bytes_and_virtual_only_tail(self):
        meta = self.vault.verify(self.ingest())
        for rva, section, offset in ((0x1000, ".text", 0x200), (0x11FF, ".text", 0x3FF),
                                     (0x1200, ".text", None), (0x12FF, ".text", None),
                                     (0x1300, None, None), (-1, None, None)):
            with self.subTest(rva=rva):
                result = vault_module.candidate(meta, 0x400000 + rva)
                self.assertEqual(result["candidate_rva"], rva)
                self.assertEqual(result["section"], section)
                self.assertEqual(result["file_offset"], offset)
                self.assertEqual(result["file_backed"], offset is not None)
                self.assertEqual(result["oep_confidence"], "UNKNOWN")

    def test_candidate_raw_padding_and_overlapping_sections(self):
        meta = {"artifact_id": "a" * 64, "pe": vault_module.inspect_pe(synthetic_pe(virtual_size=0x100))}
        self.assertEqual(vault_module.candidate(meta, 0x401180)["file_offset"], 0x380)
        meta["pe"]["sections"].append(copy.deepcopy(meta["pe"]["sections"][0]))
        with self.assertRaises(ValueError):
            vault_module.candidate(meta, 0x401000)

    def test_compare_remains_static_even_for_identical_artifacts(self):
        left = self.vault.verify(self.ingest())
        right = self.vault.verify(self.ingest(1))
        for other in (left, right):
            with self.subTest(artifact=other["artifact_id"]):
                result = vault_module.compare(left, other)
                self.assertEqual(result["scope"], "ON_DISK_PE_ONLY")
                self.assertEqual(result["function_matching"], "NOT_PERFORMED")
                self.assertEqual(result["protocol_differences"], "UNKNOWN")
                self.assertEqual(result["changed_headers"], {})
        self.assertNotEqual(left["pe"]["sections"], right["pe"]["sections"])

    def test_ordinal_name_hint_is_not_promoted_to_named_import(self):
        meta = self.vault.verify(self.ingest())
        meta["pe"]["imports"] = [{"dll": "WS2_32.dll", "symbols": [
            {"name": "unverified_parser_hint", "ordinal": 12}]}]
        result = vault_module.compare(meta, meta)
        self.assertEqual(result["common_imports"], ["ws2_32.dll!#12"])


if __name__ == "__main__":
    unittest.main()
