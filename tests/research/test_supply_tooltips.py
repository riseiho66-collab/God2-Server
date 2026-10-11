import unittest
import json
from pathlib import Path
from tools.strike_lab.recover_supply_tooltips import declared_amounts, build


class SupplyTooltipTests(unittest.TestCase):
    def test_current_source_reproduces_saved_declarations(self):
        root = Path(__file__).resolve().parents[2]
        recovered = build(root.parent / 'God2')
        saved = json.loads((root / 'artifacts/world-atlas/supply-tooltips.json').read_text(encoding='utf-8'))
        self.assertEqual(recovered, saved)
        self.assertEqual((len(saved['records']),len(saved['unmatched_med02'])), (71,29))
        rows = {row['client_item_id']: row for row in saved['records']}
        self.assertEqual(rows[3107]['declared_recovery'], {'hp':0,'mp':50})
        self.assertEqual(rows[3113]['declared_recovery'], {'hp':500,'mp':150})
        for row in rows.values():
            self.assertFalse(row['runtime_eligible'])
            self.assertFalse(row['server_effect_verified'])
            self.assertEqual(declared_amounts(bytes.fromhex(row['tooltip_raw_hex'])), row['declared_recovery'])

    def test_exact_forms(self):
        for text, hp, mp in (('\u6062\u5fa9\u751f\u547d 100', 100, 0),
                             ('\u6062\u5fa9\u6cd5\u529b 50', 0, 50),
                             ('\u6062\u5fa9\u751f\u547d 500\uff0c\u6cd5\u529b 150', 500, 150)):
            self.assertEqual(declared_amounts(text.encode('cp950')), {'hp': hp, 'mp': mp})

    def test_unqualified_forms_not_guessed(self):
        prefix = '\u6062\u5fa9\u6cd5\u529b '
        for suffix in ('50%', '-50', '0', '2147483648', '50 extra', '50\n', ' 50', '50.5'):
            self.assertIsNone(declared_amounts((prefix+suffix).encode('cp950')))
        self.assertIsNone(declared_amounts(b''))
        with self.assertRaises(UnicodeDecodeError):
            declared_amounts(b'\xff')


if __name__ == '__main__':
    unittest.main()
