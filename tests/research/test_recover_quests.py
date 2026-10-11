"""Current-client extraction fidelity and malformed-input regression checks."""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.strike_lab import recover_quests as quests
from tools.strike_lab.omega_assets import decode_csvz

CLIENT = ROOT.parent / 'God2'


@unittest.skipUnless((CLIENT / quests.PREFIX / 'Mission_data.csvZ').is_file(),
                     'Requires the original current-client evidence')
class QuestRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = quests.build_catalog(CLIENT)

    def test_all_decoded_bytes_and_row_hashes_round_trip(self):
        for table in self.catalog['tables'].values():
            raw = (CLIENT / table['source_file']).read_bytes()
            rebuilt = bytes.fromhex(table['preamble_hex'])
            for record in table['records']:
                row = b','.join(bytes.fromhex(f) for f in record['raw_fields_hex'])
                self.assertEqual(quests.digest(row), record['source_record_sha256'])
                rebuilt += row + bytes.fromhex(record['line_ending_hex'])
            self.assertEqual(rebuilt, decode_csvz(raw))
            self.assertEqual(quests.digest(raw), table['source_sha256'])
            self.assertEqual(quests.digest(rebuilt), table['decoded_sha256'])

    def test_actual_catalog_and_unknown_runtime_semantics(self):
        self.assertEqual(self.catalog['counts']['mission_definitions'], 418)
        self.assertEqual(self.catalog['counts']['objective_text_rows'], 2014)
        self.assertEqual(self.catalog['counts']['daily_records'], 85)
        self.assertEqual(self.catalog['validation']['structural_issues'], [])
        self.assertEqual(self.catalog['counts']['executable_transition_rules'], 0)
        for record in self.catalog['quests']:
            self.assertEqual(record['prerequisites'], 'UNKNOWN')
            self.assertEqual(record['transitions'], 'UNKNOWN')
        for record in self.catalog['requirement_records']:
            self.assertEqual(record['mission_data_relationship'], 'UNKNOWN')

    def test_every_reference_matches_its_source_column(self):
        for ref in self.catalog['references']:
            table = self.catalog['tables'][ref['table']]
            record = next(r for r in table['records'] if r['source_line'] == ref['source_line'])
            value = bytes.fromhex(record['raw_fields_hex'][ref['source_column'] - 1])
            self.assertEqual(int(value), ref['target_id'])
            self.assertEqual(ref['resolution'], 'UNKNOWN')

    def test_duplicate_keys_and_missing_declared_record_are_reported(self):
        tables = copy.deepcopy(self.catalog['tables'])
        tables['daily']['records'].append(copy.deepcopy(tables['daily']['records'][0]))
        tables['requirements']['records'].pop()
        issues = quests.recover(tables)['validation']['structural_issues']
        self.assertTrue(any(i['code'] == 'duplicate_key' and i['table'] == 'daily' for i in issues))
        self.assertTrue(any(i['code'] == 'record_count_mismatch' and i['table'] == 'requirements' for i in issues))

    def test_orphan_steps_and_changed_header_fail_closed(self):
        raw = decode_csvz((CLIENT / quests.PREFIX / 'Mission_data.csvZ').read_bytes())
        with self.assertRaisesRegex(ValueError, 'column header'):
            quests.parse_table('missions', raw.replace(b'STEP', b'OTHER', 1))
        tables = copy.deepcopy(self.catalog['tables'])
        tables['missions']['records'].pop(0)
        with self.assertRaisesRegex(ValueError, 'Orphan'):
            quests.recover(tables)

    def test_missing_optional_daily_fields_remain_null(self):
        rows = self.catalog['tables']['daily']['records']
        short = [r for r in rows if len(r['raw_fields_hex']) == 12]
        self.assertEqual(len(short), 5)
        self.assertTrue(all(r['fields']['reward_text'] is None for r in short))

    def test_cli_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as folder, redirect_stdout(io.StringIO()):
            output = Path(folder) / 'quests.json'
            args = ['--client', str(CLIENT), '--output', str(output)]
            self.assertEqual(quests.main(args), 0)
            first = output.read_bytes()
            self.assertEqual(quests.main(args), 0)
            self.assertEqual(first, output.read_bytes())
            self.assertEqual(json.loads(first), self.catalog)


if __name__ == '__main__':
    unittest.main()
