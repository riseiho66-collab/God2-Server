"""Original x86 mapper/image selector with all current portrait resources."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.strike_lab.current_deity_portrait import audit

class CurrentDeityPortraitTests(unittest.TestCase):
    def test_original_mapper_selects_source_images_and_rejects_key100(self):
        proof=audit();rows=proof['keys']
        self.assertEqual(proof['native_template_keys'],list(range(1,35)))
        self.assertEqual([r['key'] for r in rows if r['image']],list(range(1,43))+list(range(101,109)))
        self.assertEqual((rows[100]['bank'],rows[100]['action'],rows[100]['image']),(5,99,None))
        self.assertEqual(rows[1]['image']['name'],'姜子牙')
        self.assertEqual(rows[34]['image']['name'],'女媧')
        self.assertEqual(rows[101]['image']['name'],'男劍客')
        self.assertEqual(rows[108]['image']['name'],'女藥師')
        self.assertGreater(proof['executed_instruction_count'],300)

if __name__=='__main__':unittest.main()
