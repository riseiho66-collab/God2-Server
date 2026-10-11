"""Drift discovery must not silently certify changed runtime routes."""
import copy
import json
import subprocess
import sys
import unittest

from tools.strike_lab import current_protocol_coverage as coverage


class RouteDriftTests(unittest.TestCase):
    def test_all_changed_and_missing_pins_are_reported(self):
        files={path:{'sha256':digest,'text':''}
               for path,digest in coverage.ROUTE_SOURCE_SHA256.items()}
        baseline=coverage.route_drift_report(files)
        self.assertEqual(baseline['status'],'PINNED_SNAPSHOT_UNCHANGED')
        self.assertFalse(baseline['runtime_acceptance_granted'])
        paths=list(files)
        files[paths[0]]['sha256']='0'*64
        del files[paths[1]]
        original=copy.deepcopy(files)
        report=coverage.route_drift_report(files)
        self.assertEqual(report['status'],'REAUDIT_REQUIRED')
        self.assertEqual([(r['path'],r['status']) for r in report['changed_sources']],
                         [(paths[0],'CHANGED'),(paths[1],'MISSING')])
        self.assertFalse(report['all_original_packets_wired'])
        self.assertEqual(files,original)

    def test_current_cli_lists_discovery_and_keeps_failure_status(self):
        result=subprocess.run([sys.executable,'-B',str(coverage.ROOT/
            'tools/strike_lab/current_protocol_coverage.py'),'--route-drift'],
            cwd=coverage.ROOT,text=True,capture_output=True,timeout=30)
        self.assertEqual(result.returncode,2,result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report['status'],'REAUDIT_REQUIRED')
        self.assertIn('src/net/Session.cpp',{r['path'] for r in report['changed_sources']})
        self.assertIn('RecoveredNpcInteraction::opcode',report['current_world_case_labels'])
        references=report['runtime_references']['RecoveredQuestAction']
        self.assertIn('src/core/Application.cpp',{r['path'] for r in references})
        self.assertFalse(report['runtime_acceptance_granted'])


if __name__=='__main__':unittest.main()
