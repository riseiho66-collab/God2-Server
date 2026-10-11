import unittest

import pefile
from tools.strike_lab import current_unpacked_protocol_match as audit


class CurrentUnpackedProtocolMatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe = audit.EXE.read_bytes()
        cls.reference = audit.REFERENCE.read_bytes()

    def test_pinned_regions_match(self):
        result = audit.compare(self.exe, self.reference)
        self.assertEqual(result['status'], 'MATCHED_SELECTED_PROTOCOL_REGIONS')
        self.assertEqual(len(result['regions']), 11)
        self.assertTrue(all(row['complete'] and row['match'] for row in result['regions']))
        self.assertFalse(result['runtime_gameplay_enabled_by_audit'])

    def test_each_region_detects_modified_instruction_or_table_byte(self):
        pe = pefile.PE(data=self.exe, fast_load=True)
        try:
            for name, start, end in audit.SLICES:
                with self.subTest(region=name):
                    changed = bytearray(self.exe)
                    changed[pe.get_offset_from_rva(start)] ^= 1
                    result = audit.compare(bytes(changed), self.reference)
                    self.assertEqual(result['status'], 'NOT_QUALIFIED')
                    self.assertFalse(next(row for row in result['regions'] if row['name'] == name)['match'])
        finally:
            pe.close()

    def test_identical_regions_do_not_override_changed_build_identity(self):
        changed = bytearray(self.reference)
        changed[0] ^= 1
        result = audit.compare(self.exe, bytes(changed))
        self.assertTrue(all(row['match'] for row in result['regions']))
        self.assertFalse(result['pinned_identity_match'])
        self.assertEqual(result['status'], 'NOT_QUALIFIED')

    def test_truncated_reference_is_not_a_match(self):
        result = audit.compare(self.exe, self.reference[:0x132e1])
        self.assertEqual(result['status'], 'NOT_QUALIFIED')
        self.assertFalse(all(row['complete'] for row in result['regions']))
