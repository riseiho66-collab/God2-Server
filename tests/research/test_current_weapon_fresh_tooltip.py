"""Complete native fresh-tooltip return and exact source-text regression."""
from pathlib import Path
import json
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]


class WeaponFreshTooltipTests(unittest.TestCase):
    def test_native_fresh_hover_and_double_click_normal_and_optimized(self):
        previous=None
        for optimize in ([],['-O']):
            with self.subTest(optimized=bool(optimize)):
                result=subprocess.run([sys.executable,*optimize,'-X','utf8','-B','-m',
                    'tools.strike_lab.current_weapon_fresh_tooltip_20260926'],cwd=ROOT,
                    text=True,encoding='utf-8',capture_output=True,timeout=45,check=True)
                report=json.loads(result.stdout)
                self.assertEqual(report['status'],'PASS')
                self.assertEqual(report['count'],12)
                self.assertEqual(report['native_game_stubs'],0)
                self.assertEqual(report['instance_origin'],'CUSTOM_TEST_NOT_NATIVE')
                self.assertEqual(len(report['cases']),12)
                combinations=set()
                for case in report['cases']:
                    combinations.add((case['key'],case['slot'],case['event']))
                    self.assertTrue(case['fresh_cache_miss'] and case['native_return'] and case['widget_open'])
                    self.assertFalse(case['graphical_blit_tested'])
                    self.assertIn('品質:+0',case['formatter_cp950'])
                    self.assertIn('能力總和',case['formatter_cp950'])
                    self.assertEqual(len(bytes.fromhex(case['instance_hex'])),20)
                    expected=bytes([0x28,case['key'],0,case['slot'],1]) if case['event']==4 else b''
                    self.assertEqual(bytes.fromhex(case['request_hex']),expected)
                    texts=[bytes.fromhex(row['raw_hex']).decode('cp950') for row in case['formatted_controls']]
                    self.assertIn('(+0)菜刀' if case['key']==1 else '(+0)砍刀',texts)
                    self.assertIn('等級限定(1級)' if case['key']==1 else '等級限定(10級)',texts)
                self.assertEqual(combinations,{(key,slot,event) for key in (1,2) for slot in (0,1,34) for event in (0,4)})
                if previous is not None:self.assertEqual(report,previous)
                previous=report


if __name__=='__main__':unittest.main()
