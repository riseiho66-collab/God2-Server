"""No desktop/client process: run complete native branches in isolated Unicorn."""
from pathlib import Path
import json
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]


class EquipmentProjectionTests(unittest.TestCase):
    def test_normal_and_optimized_oracles(self):
        previous=None
        for optimize in ([],['-O']):
            with self.subTest(optimize=bool(optimize)):
                proc=subprocess.run([sys.executable,*optimize,'-X','utf8','-B','-m',
                    'tools.strike_lab.current_equipment_projection_20260926'],cwd=ROOT,
                    capture_output=True,text=True,encoding='utf-8',timeout=45,check=True)
                report=json.loads(proc.stdout)
                self.assertEqual(report['status'],'PASS')
                self.assertEqual(report['transitions'],72)
                self.assertEqual(report['ui_requests'],73)
                self.assertEqual(report['equipment_clear_cases'],16)
                self.assertEqual(report['native_callee_stubs'],0)
                self.assertEqual(report['os_time_calls'],90)
                self.assertEqual(len(report['sound_calls']),90)
                self.assertEqual(report['sound_calls'].count(0x29d),54)
                self.assertEqual(report['sound_calls'].count(0x29e),36)
                self.assertEqual(report['original_icon_bindings'],{'1':[65,0],'2':[65,1]})
                self.assertEqual([s['name'] for s in report['sound_sources']],['ItemEquip.wav','ItemPlace.wav'])
                self.assertEqual(len(report['cases']),18)
                self.assertEqual(len(report['requests']),73)
                self.assertTrue(all(case['unequip_pending']==1 for case in report['cases']))
                if previous is not None:self.assertEqual(report,previous)
                previous=report


if __name__=='__main__':unittest.main()
