"""Reviewer guard tests against the saved native run, not new live launches."""
from copy import deepcopy
import json
import unittest

from tools.strike_lab.current_offline_run_review import ROOT, audit_payload, review


class CurrentOfflineRunReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.run_dir = ROOT / 'artifacts/runs/offline-entry-loop-20260920-01'
        cls.report = json.loads((cls.run_dir / 'offline-result.json').read_text())

    def test_saved_native_evidence_is_bounded_to_engine_not_playability(self):
        result = review(self.run_dir)
        self.assertTrue(result['native_offline_scene_loop_verified'], result['errors'])
        self.assertEqual(result['completed_frame_presentations'], 3)
        self.assertFalse(result['visible_nonblank_world_verified'])
        self.assertFalse(result['playable_single_player_verified'])
        self.assertEqual(result['original_monster_values_recovered'], 0)

    def test_incomplete_transport_restoration_or_owner_evidence_fails(self):
        for key, value in (('entry_patch_restored', False), ('executable_disk_unchanged', False),
                           ('armed', ''), ('native_scene_call_returned', False), ('client_pid', -1)):
            report = deepcopy(self.report)
            report[key] = value
            self.assertFalse(audit_payload(report)['native_offline_scene_loop_verified'], key)
        report = deepcopy(self.report)
        report['events'][0]['transport_api'] = 'send'
        self.assertFalse(audit_payload(report)['native_offline_scene_loop_verified'])

    def test_no_promotion_from_entry_only_or_failed_presentation(self):
        for stage in ('WORLD_INITIALIZER', 'LOCAL_NULL_INPUT_BRANCH', 'PRESENTATION_RETURN'):
            report = deepcopy(self.report)
            event = next(event for event in report['events'] if event.get('stage') == stage)
            report['events'].remove(event)
            self.assertFalse(audit_payload(report)['native_offline_scene_loop_verified'], stage)
        report = deepcopy(self.report)
        event = next(event for event in report['events'] if event.get('stage') == 'PRESENTATION_RETURN')
        event['eax'] = 0x80004005
        self.assertFalse(audit_payload(report)['native_offline_scene_loop_verified'])

    def test_loop_bytes_null_input_and_return_frame_are_checked(self):
        mutations = (
            lambda r: r['loop_intervention'].update(hex='90'),
            lambda r: r['local_world_return'].update(esp=0),
            lambda r: r['offline_prerequisites'].update(connected_flags=[0, 1]),
            lambda r: next(e for e in r['events'] if e.get('stage') == 'INITIAL_ACTOR_DISPATCH').update(initializer_first_argument=1),
        )
        for mutate in mutations:
            report = deepcopy(self.report)
            mutate(report)
            self.assertFalse(audit_payload(report)['native_offline_scene_loop_verified'])


if __name__ == '__main__':
    unittest.main()
