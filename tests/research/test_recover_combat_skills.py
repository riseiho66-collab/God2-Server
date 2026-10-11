"""Regression checks against retained real source rows, never demo combat rules."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab.recover_combat_skills import (
    MENU_SOURCE, SOURCE, build_catalog, lookup_definition, parse_skills, serialize,
)

ARTIFACT = Path(__file__).resolve().parents[2] / 'artifacts/world-atlas/combat-skills.json'


class CombatSkillRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(ARTIFACT.read_text(encoding='utf-8'))

    def source_slice(self):
        skills = self.catalog['skills']
        rows = [bytes.fromhex(row['raw_record_hex']) for row in skills['definitions']]
        return (bytes.fromhex(skills['header']['raw_record_hex']) + b'\r\nSKB,'
                + str(len(rows)).encode() + b'\r\n' + b'\r\n'.join(rows) + b'\r\n')

    def test_real_rows_roundtrip_and_provenance(self):
        parsed = parse_skills(self.source_slice())
        self.assertEqual(parsed['declared_records'], self.catalog['counts']['skill_books'])
        for actual, saved in zip(parsed['definitions'], self.catalog['skills']['definitions']):
            raw = bytes.fromhex(saved['raw_record_hex'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), saved['source_record_sha256'])
            self.assertEqual(actual['fields'], saved['fields'])
            self.assertEqual(actual['description_claims'], saved['description_claims'])
            for claim in saved['description_claims'].values():
                self.assertEqual(claim['source_text'], saved['fields'][claim['source_column']])
                self.assertEqual(claim['authority'], 'description_only')

    def test_actual_first_book_and_fail_closed_lookup(self):
        book = lookup_definition(self.catalog, 6501)
        self.assertEqual(book['description_claims']['mp_cost']['value'], 5)
        self.assertEqual(book['description_claims']['attack_range']['value'], 3)
        self.assertEqual(book['description_claims']['mp_cost']['source_column'], 9)
        with self.assertRaises(KeyError):
            lookup_definition(self.catalog, -1)
        with self.assertRaises(TypeError):
            lookup_definition(self.catalog, '6501')

    def test_rejects_truncated_duplicate_and_wrong_header(self):
        raw = self.source_slice()
        with self.assertRaises(ValueError):
            parse_skills(raw.rsplit(b'\r\n', 2)[0] + b'\r\n')
        with self.assertRaises(ValueError):
            parse_skills(raw.replace(b'6502,', b'6501,', 1))
        with self.assertRaises(ValueError):
            parse_skills(raw.replace(b'ITEM_ID,', b'UNKNOWN,', 1))
        with self.assertRaises(ValueError):
            parse_skills(raw.replace(b'SKB,381', b'SKB,380', 1))

    def test_unknown_fields_not_promoted(self):
        for entry in self.catalog['skills']['definitions']:
            self.assertNotIn('damage', entry)
            self.assertNotIn('runtime_skill_id', entry)
            self.assertTrue(all(claim['source_column'] in range(7, 13)
                                for claim in entry['description_claims'].values()))
        raw = self.source_slice()
        # Corrupt a label while retaining the real trailing numeric fields.
        raw = raw.replace('\u4f7f\u7528\u6d88\u8017 5 MP'.encode('cp950'), b'unknown', 1)
        first = parse_skills(raw)['definitions'][0]
        self.assertNotIn('mp_cost', first['description_claims'])

    def test_serialization_is_deterministic(self):
        self.assertEqual(serialize(self.catalog), serialize(copy.deepcopy(self.catalog)))
        self.assertEqual(serialize(self.catalog), ARTIFACT.read_text(encoding='utf-8'))

    def test_original_client_byte_identity_and_repeat_build(self):
        client = ARTIFACT.parents[3] / 'God2'
        if not (client / SOURCE).is_file():
            self.skipTest('Original client unavailable; source equivalence not checked')
        for relative, rows in (
            (SOURCE, self.catalog['skills']['definitions']),
            (MENU_SOURCE, self.catalog['menu_raw_records']),
        ):
            original = (client / relative).read_bytes()
            source = self.catalog['sources'][relative]
            self.assertEqual(hashlib.sha256(original).hexdigest(), source['sha256'])
            decoded = decode_csvz(original)
            self.assertEqual(hashlib.sha256(decoded).hexdigest(), source['decoded_sha256'])
            for row in rows:
                raw = bytes.fromhex(row['raw_record_hex'])
                offset = row['decoded_offset']
                self.assertEqual(decoded[offset:offset + len(raw)], raw)
                self.assertEqual(decoded.splitlines()[row['source_line'] - 1], raw)
        rebuilt = build_catalog(client, xjz_root=ARTIFACT.parents[2] /
                                'artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation')
        self.assertEqual(serialize(rebuilt), ARTIFACT.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
