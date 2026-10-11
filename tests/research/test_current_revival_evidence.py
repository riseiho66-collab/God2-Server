import hashlib
import unittest

from tools.strike_lab.current_revival_evidence import build_evidence, IDS


class RevivalEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = build_evidence()
        cls.rows = {r['item_id']:r for r in cls.evidence['entries']}

    def test_pinned_raw_record_provenance(self):
        self.assertEqual(set(self.rows), set(IDS))
        for row in self.rows.values():
            source = row['source']
            raw = bytes.fromhex(source['raw_record_hex'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])
            fields = raw.rstrip(b'\r\n').decode('cp950').split(',')
            self.assertEqual(row['descriptions'], fields[7:13])
            self.assertEqual(int(fields[0]), row['item_id'])

    def test_skill_claims_match_explicit_text(self):
        for item,mp,hp in ((6808,66,'HP\u70ba1'),(6809,111,'HP30\uff05'),(6810,222,'HP\u5168\u6eff')):
            row = self.rows[item]
            self.assertEqual(row['source']['fields_cp950_display'][12], hp)
            self.assertIn(str(mp) + ' MP', row['descriptions'][2])
            self.assertEqual(row['claims']['mp_cost_text'], mp)
        self.assertEqual(self.rows[6872]['claims']['scope'], 'active_buff')
        self.assertEqual(self.rows[5539]['claims']['effect_text'], 'no_experience_loss_on_death_return')

    def test_no_runtime_promotion_or_generic_revival_rule(self):
        self.assertFalse(self.evidence['production_enabled'])
        self.assertFalse(self.evidence['runtime_formula_verified'])
        self.assertIn('ordinary defeat return destination and HP', self.evidence['unresolved'])
        for row in self.rows.values():
            self.assertFalse(row['executable'])
            self.assertEqual(row['authority'], 'description_only')

    def test_usage_cap_is_not_assumed_unlimited(self):
        limits = self.evidence['usage_limit_messages']
        self.assertIsNone(limits['numeric_limit'])
        self.assertEqual([r['fields_cp950_display'][0] for r in limits['records']], ['1285','1286','1287'])
        for row in limits['records']:
            self.assertIn('\u6b64\u6b21\u6230\u9b25\u4f7f\u7528\u6578\u91cf\u4e0a\u9650', row['fields_cp950_display'][2])


if __name__ == '__main__':
    unittest.main()
