"""Dated formal-client preservation and rejection regression; no live writes."""
import struct
import unittest

import pefile

from tools.skills import stage_shunying_production_client as release
from tools.skills import install_shunying_clone as trial


class ReleaseClientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = (release.CLIENT / 'God2.exe').read_bytes()
        cls.payloads, cls.report = release.prepare()

    def test_all_sections_imports_entry_chain_and_hooks_preserved(self):
        proof = release.verify_preservation(self.original, self.payloads['God2.exe'], self.report['bootstrap'])
        self.assertTrue(proof['original_entry_chain_preserved'])
        self.assertTrue(proof['all_15_hook_signatures_match'])
        self.assertEqual(2592, proof['original_port'])

    def test_wrong_formal_version_and_original_trial_api_reject(self):
        modified = self.original[:-1] + bytes([self.original[-1] ^ 1])
        with self.assertRaisesRegex(ValueError, 'exact version pin'):
            trial._make_pinned_image(modified, release.CLIENT / trial.DLL_NAME, expected_sha256=release.EXE_SHA256)
        with self.assertRaisesRegex(ValueError, 'exact pinned unmodified trial'):
            trial.make_patched_image(self.original, release.CLIENT / trial.DLL_NAME)
        with self.assertRaisesRegex(ValueError, 'exact version pin'):
            trial._make_pinned_image(self.payloads['God2.exe'], release.CLIENT / trial.DLL_NAME,
                                     expected_sha256=release.EXE_SHA256)

    def test_hook_corruption_is_rejected(self):
        corrupted = bytearray(self.original)
        at = pefile.PE(data=self.original).get_offset_from_rva(release.HOOKS[0][0])
        corrupted[at] ^= 1
        with self.assertRaisesRegex(ValueError, 'Hook signature mismatch'):
            release.verify_hooks(bytes(corrupted))

    def test_existing_section_corruption_and_broken_chain_rejected(self):
        patched = self.payloads['God2.exe']
        pe = pefile.PE(data=patched)
        corrupted = bytearray(patched)
        corrupted[pe.sections[0].PointerToRawData] ^= 1
        with self.assertRaisesRegex(ValueError, 'Original section content changed'):
            release.verify_preservation(self.original, bytes(corrupted), self.report['bootstrap'])
        code = bytearray.fromhex(self.report['bootstrap']['bootstrap_code_hex'])
        struct.pack_into('<i', code, len(code) - 4, 0)
        corrupted = bytearray(patched)
        entry = pe.get_offset_from_rva(pe.OPTIONAL_HEADER.AddressOfEntryPoint)
        corrupted[entry:entry + len(code)] = code
        details = dict(self.report['bootstrap'], bootstrap_code_hex=code.hex())
        with self.assertRaisesRegex(ValueError, 'Entry chain was replaced'):
            release.verify_preservation(self.original, bytes(corrupted), details)

    def test_accepted_resources_and_all_native_records_preserved(self):
        self.assertEqual(448, self.report['resources']['native_records_preserved'])
        self.assertEqual(600, self.report['resources']['native_icon_chunks_preserved'])
        for relative, (_, expected) in release.RESOURCE_PINS.items():
            self.assertEqual(expected, trial.sha(self.payloads[relative]))


if __name__ == '__main__':
    unittest.main()
