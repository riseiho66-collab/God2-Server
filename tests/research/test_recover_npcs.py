import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.strike_lab.recover_npcs import MAX_BYTES, build_npcs, main, parse_spawn_insert, provenance, read_source


def sql(values='(1,2,3,4,0,32767)'):
    return ('INSERT INTO `god2_game`.`npc_spawns` '
            '(`spawn_id`,`npc_id`,`map_id`,`observed_client_entity_handle`,`position_x`,`position_y`) '
            'VALUES ' + values + ' ON DUPLICATE KEY UPDATE `spawn_id`=VALUES(`spawn_id`);').encode()


class RecoverNpcTests(unittest.TestCase):
    def test_actual_sources_reproduce_artifact_without_promoting_legacy(self):
        classic=Path('C:/God2Evidence/classic-20260820/files/God2-Classic-Server-Formal-Handoff-20260820-020345/ServerSource')
        xjz=ROOT/'artifacts/legacy-evidence/xjz-20260820/files/XJZ-Server-Cpp/server_implementation'
        result=build_npcs(classic,xjz,ROOT.parent/'God2')
        self.assertEqual(result,json.loads((ROOT/'artifacts/world-atlas/npcs.json').read_text()))
        self.assertEqual(result['counts']['placement_definitions'],2)
        self.assertEqual(result['counts']['current_template_rows'],319)
        self.assertEqual(result['counts']['current_map_bindings'],0)
        self.assertEqual(result['counts']['runtime_integrated'],0)
        for row in result['placements']:
            self.assertFalse(row['runtime_eligible'])
            self.assertIsNone(row['map']['current_area'])
            self.assertIsNone(row['map']['current_scene'])

    def test_deterministic_sorted_source_fields(self):
        raw = sql('(2,2,3,4,5,6),(1,2,3,5,0,32767)')
        self.assertEqual(parse_spawn_insert(raw), parse_spawn_insert(raw))
        self.assertEqual([r['spawn_id'] for r in parse_spawn_insert(raw)], [1, 2])

    def test_malformed_bounds_and_identifiers(self):
        for values in ('(1,2,3,4,-1,0)', '(1,2,3,4,0,32768)',
                       '(1,2,3,4,1.5,0)', '(0,2,3,4,0,0)',
                       '(1,2,NULL,4,0,0)', '(1,2,3,4,0)',
                       '(1,2,3,4,0,0),(1,2,3,4,0,0)'):
            with self.subTest(values=values), self.assertRaises(ValueError):
                parse_spawn_insert(sql(values))

    def test_no_expressions_or_extra_statements(self):
        for values in ('(1,2,3,4,abs(1),0)', '(1,2,3,4,0,0); DROP TABLE recovered;',
                       '(1,2,3,4,(SELECT 1),0)'):
            with self.subTest(values=values), self.assertRaises(ValueError):
                parse_spawn_insert(sql(values))

    def test_sql_length_bound(self):
        with self.assertRaises(ValueError):
            parse_spawn_insert(b' ' * (MAX_BYTES + 1))

    def test_provenance_hash_and_record_order(self):
        a = provenance('classic', 'source.sql', b'original', 'npc_spawns', 7, {'x': 1, 'y': 2})
        b = provenance('classic', 'source.sql', b'original', 'npc_spawns', 7, {'y': 2, 'x': 1})
        self.assertEqual(a, b)
        self.assertEqual(a['sha256'], hashlib.sha256(b'original').hexdigest())
        self.assertEqual(a['record_id'], 7)
        self.assertEqual(a['source_archive'], 'classic')

    def test_source_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                read_source(Path(directory).resolve(), '../outside')

    def test_output_cannot_touch_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SystemExit):
                main(['--classic-root', directory, '--xjz-root', directory,
                      '--client-root', directory, '--output', str(Path(directory) / 'npc.json')])


if __name__ == '__main__':
    unittest.main()
