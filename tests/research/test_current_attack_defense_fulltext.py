import json
from pathlib import Path
import unittest

from tools.strike_lab.current_attack_defense_fulltext import CLIENT, discover, scan_table, sha

ROOT = Path(__file__).resolve().parents[2]


class AttackDefenseFulltextTests(unittest.TestCase):
    def test_full_body_including_numeric_key_and_late_rows(self):
        prefix = b'0,unrelated\r\n' * 100
        source = prefix + b'520,' + '\u7269\u653b'.encode('cp950') + b'\r\n'
        report = scan_table(source)
        self.assertEqual(report['bytes_scanned'], len(source))
        self.assertEqual(report['lines_scanned'], 101)
        self.assertEqual(report['exact_label_rows'][0]['line'], 101)
        self.assertEqual(report['exact_label_rows'][0]['labels'][0]['decoded_offset'], len(prefix) + 4)

    def test_prose_is_not_a_numeric_column(self):
        report = scan_table('1,\u7269\u653b\u589e\u52a0150\r\n'.encode('cp950'))
        self.assertEqual(len(report['mention_rows']), 1)
        self.assertEqual(report['exact_label_rows'], [])

    def test_byte_offsets_crlf_eof_and_invalid_cp950_are_retained(self):
        source = b'1,\xff\r\n2,physical_attack'
        report = scan_table(source)
        self.assertEqual(report['cp950_invalid_lines'], 1)
        self.assertEqual(report['lines_scanned'], 2)
        self.assertEqual(report['exact_label_rows'][0]['decoded_offset'], 5)
        self.assertEqual(report['exact_label_rows'][0]['sha256'], sha(source[5:]))
        self.assertEqual(scan_table(b'')['lines_scanned'], 0)
        self.assertEqual(scan_table(b'1,a\rb')['lines_scanned'], 1)

    def test_current_full_inventory_reproduces_saved_index(self):
        actual = discover()
        saved = json.loads((ROOT / 'artifacts/research/current-attack-defense-fulltext-20260920.json').read_text())
        # Preserve the original evidence index: new bilingual tables expand
        # the current scan, rather than rewriting its historical source hashes.
        originals={f['path']:f for f in saved['files']}
        current={f['path']:f for f in actual['files']}
        self.assertTrue(set(originals).issubset(current))
        self.assertEqual({p:current[p] for p in originals},originals)
        additions=[f for p,f in current.items() if p not in originals]
        self.assertEqual(len(additions),44)
        self.assertTrue(all(f['path'].lower().endswith('-gb.csvz') for f in additions))
        self.assertEqual(actual['file_count'],118)
        self.assertEqual(sum(f['plain_bytes'] for f in originals.values()),7042927)
        self.assertEqual(sum(f['lines_scanned'] for f in originals.values()),76583)
        self.assertEqual(actual['original_monster_values_recovered'], 0)
        self.assertEqual(actual['database_promotions'], 0)
        exact_paths = {f['path'] for f in originals.values() if f['exact_label_rows']}
        self.assertEqual(exact_paths, {'Data2/Patch/Comm/ChangeDollCard.csvZ', 'Data2/Patch/Comm/message.csvZ'})
        self.assertTrue(all((CLIENT / f['path']).is_file() for f in actual['files']))


if __name__ == '__main__':
    unittest.main()
