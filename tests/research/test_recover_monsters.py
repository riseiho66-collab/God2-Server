"""Tests use actual current-client rows, never replacement monster content."""
from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import sqlite3
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import recover_monsters as monsters
from tools.strike_lab.omega_assets import decode_csvz

CLIENT = ROOT.parent / 'God2'
CLASSIC = Path('C:/God2Evidence/classic-20260820/files/'
               'God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource')
XJZ = ROOT / 'artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation'
REQUIRED_UNKNOWN = {
    'level', 'hp', 'mp', 'constitution', 'strength', 'intelligence', 'speed',
    'physical_attack', 'physical_defense', 'magical_attack', 'magical_defense',
    'metal', 'wood', 'water', 'fire', 'earth', 'skills', 'drop_items', 'drop_rates',
}
LEGACY_UNKNOWN = {
    'server_template_id', 'level', 'hp', 'mp', 'damage', 'defense',
    'map', 'spawn_x', 'spawn_y', 'spawn_count', 'respawn', 'drops',
}


class MonsterRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = monsters.build_monsters(CLIENT, CLASSIC, XJZ)

    def test_every_current_client_row_is_byte_identical(self):
        for table in self.result['definition_tables']:
            decoded = decode_csvz((CLIENT / table['source']['file']).read_bytes())
            reconstructed = bytes.fromhex(table['preamble_hex'])
            for row in table['records']:
                raw = bytes.fromhex(row['raw_record_hex'])
                offset = row['source_offset']
                self.assertEqual(decoded[offset:offset + len(raw)], raw)
                self.assertEqual(monsters.digest(raw), row['source_record_sha256'])
                self.assertEqual(raw.rstrip(b'\r\n').split(b','),
                                 [bytes.fromhex(f) for f in row['raw_fields_hex']])
                reconstructed += raw
            self.assertEqual(reconstructed, decoded)
            self.assertEqual(table['records_imported'], len(table['records']))

    def test_normalized_fields_have_exact_source_header_and_value(self):
        for table in self.result['definition_tables']:
            for row in table['records']:
                for key, claim in row['known_fields'].items():
                    column = claim['source_column']
                    self.assertEqual(claim['header_hex'], table['header_fields_hex'][column])
                    if not claim['present']:
                        self.assertGreaterEqual(column, len(row['raw_fields_hex']))
                        self.assertIsNone(claim['value'])
                        continue
                    raw = bytes.fromhex(row['raw_fields_hex'][column])
                    value = (int(raw) if key in ('source_index', 'monster_code') else
                             raw.hex() if key == 'name_bytes' else raw.decode('ascii'))
                    self.assertEqual(claim['value'], value)

    def test_missing_columns_are_absent_not_defaulted(self):
        battle = self.result['definition_tables'][1]
        absent = [r for r in battle['records'] if not r['known_fields']['rom_path']['present']]
        self.assertEqual(len(absent), 7)
        self.assertTrue(all(r['known_fields']['rom_path']['value'] is None for r in absent))

    def assert_unknown_contract(self, result):
        expected = REQUIRED_UNKNOWN | LEGACY_UNKNOWN
        self.assertCountEqual(result['unknown_fields'], expected)
        self.assertTrue(expected.isdisjoint(result))
        self.assertEqual(result['counts']['runtime_integrated'], 0)
        self.assertEqual(result['counts']['spawn_instances_imported'], 0)
        self.assertEqual(result['spawn_instances'], [])
        for table in result['definition_tables']:
            self.assertTrue(table['records'])
            for row in table['records']:
                with self.subTest(kind=table['kind'], line=row['source_line']):
                    self.assertCountEqual(row['unknown_fields'], expected)
                    self.assertTrue(expected.isdisjoint(row['known_fields']))
                    self.assertTrue(expected.isdisjoint(row))
                    self.assertIs(row['runtime_eligible'], False)

    def test_all_requested_fields_explicitly_unknown_on_actual_rows(self):
        self.assertEqual([t['records_imported'] for t in self.result['definition_tables']],
                         [215, 215])
        self.assert_unknown_contract(self.result)

    def test_existing_synthetic_drop_fixture_never_promoted(self):
        fixture_path = CLASSIC / ('tests/God2.RecoveredDatabaseImporter.Tests/Fixtures/'
                                  'native-writer-monster-drop.jsonl')
        fixtures = [json.loads(line) for line in fixture_path.read_text(encoding='utf-8').splitlines()
                    if line.strip()]
        self.assertEqual(len(fixtures), 1)
        self.assertEqual(fixtures[0]['evidenceRefs'][0]['evidenceId'], 'SELFTEST-SE-17')
        self.assertEqual(fixtures[0]['observedClientRate'], 0.12)
        self.assertEqual(fixtures[0]['defaultDisabledRate'], 0)
        self.assertIsNone(fixtures[0]['authoritativeRate'])
        read_source = monsters.read_source

        # Feed the existing SELFTEST through each retained legacy JSON boundary.
        for relative in monsters.CLASSIC_JSON[1:]:
            def fixture_source(root, path):
                if Path(root) == CLASSIC and path == relative:
                    raw, source = read_source(root, path)
                    data = json.loads(raw)
                    data['records'].extend(fixtures)
                    data['recordCount'] = len(data['records'])
                    raw = json.dumps(data).encode('ascii')
                    return raw, {**source, 'sha256': monsters.digest(raw), 'size': len(raw)}
                return read_source(root, path)

            with self.subTest(source=relative), patch.object(monsters, 'read_source', fixture_source):
                result = monsters.build_monsters(CLIENT, CLASSIC, XJZ)
                legacy = next(entry for entry in result['legacy_json']
                              if entry['source']['file'] == relative)
                self.assertEqual(legacy['raw_records'][-1], fixtures[0])
                self.assertEqual(legacy['authority'],
                                 'legacy_claim_only; no current-client identity promotion')
                self.assert_unknown_contract(result)
                self.assertEqual(result['definition_tables'], self.result['definition_tables'])

    def test_no_visual_position_or_legacy_claim_promoted(self):
        self.assertEqual(self.result['spawn_instances'], [])
        for table in self.result['definition_tables']:
            for row in table['records']:
                self.assertFalse(row['runtime_eligible'])
                self.assertIn('level', row['unknown_fields'])
                self.assertNotIn('spawn_x', row['known_fields'])
        claim = self.result['legacy_json'][2]['raw_records'][0]
        self.assertEqual(claim['level'], 6)
        self.assertIsNone(claim['maximumHp'])
        self.assertFalse(claim['runtimeEligible'])

    def test_rejects_header_changes_duplicate_ids_and_bad_start(self):
        raw = decode_csvz((CLIENT / monsters.CLIENT_TABLES[0]).read_bytes())
        lines = raw.splitlines(keepends=True)
        for invalid in (b''.join(lines[:4] + [lines[4]] + lines[4:]),
                        raw.replace(b'ROM ', b'XXX ', 1),
                        raw.replace(b'1.02,5,', b'1.02,0,', 1)):
            with self.assertRaises(ValueError):
                monsters.parse_definition(invalid, 'field')

    def test_sqlite_read_only_and_denominators(self):
        path = XJZ / 'xjz_evidence.sqlite'
        connection = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
        try:
            with self.assertRaises(sqlite3.OperationalError):
                connection.execute('CREATE TABLE forbidden_recovery_write (id INTEGER)')
            for table, audit in self.result['xjz_audit']['tables'].items():
                count = connection.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                self.assertEqual(audit['source_rows'], count)
        finally:
            connection.close()

    def test_deterministic_complete_import(self):
        again = monsters.build_monsters(CLIENT, CLASSIC, XJZ)
        self.assertEqual(json.dumps(self.result, sort_keys=True), json.dumps(again, sort_keys=True))

    def test_output_cannot_overwrite_any_original_source(self):
        for root in (CLIENT, CLASSIC, XJZ):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                monsters.main(['--client', str(CLIENT), '--classic', str(CLASSIC),
                               '--xjz', str(XJZ), '--output', str(root / 'forbidden.json')])


if __name__ == '__main__':
    unittest.main()
