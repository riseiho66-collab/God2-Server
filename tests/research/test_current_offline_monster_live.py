import struct
import unittest
import copy
import json
import hashlib
from pathlib import Path

from tools.strike_lab.current_offline_monster_live import call_page, identity_record, text_init_page, phase_call_page
from tools.strike_lab.current_offline_monster_live import LiveMonsterProbe
from tools.strike_lab.current_offline_vitals_live import diagnostic_record, call_page as vitals_page
from tools.strike_lab.current_offline_monster_review import audit_payload, review

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / 'artifacts/runs'


class OfflineMonsterCallTests(unittest.TestCase):
    def test_unclassified_stop_and_vitals_diagnostic_are_explicit(self):
        self.assertFalse(LiveMonsterProbe.handles(None))
        self.assertFalse(LiveMonsterProbe.handles('376'))
        self.assertTrue(LiveMonsterProbe.handles(376))
        raw = diagnostic_record()
        self.assertEqual(len(raw), 121)
        self.assertEqual(raw[:5], b'\x88' + bytes(4))
        for slot in range(14):
            self.assertEqual(struct.unpack_from('<II', raw, 5 + slot * 8), (1000 + slot, 50 + slot))
        code, trap = vitals_page(0x2000000, 0x3000000)
        self.assertEqual(code[:17].hex(), '6800010002b900000003b8908a5100ffd0')
        self.assertEqual(code[trap:trap + 3], b'\xcc\x0f\x0b')
        self.assertEqual(code[256:], raw)

    def test_phase_call_has_explicit_zero_argument_and_trap(self):
        code, trap = phase_call_page(0x2100000)
        self.assertEqual(code.hex(), '6a00b900001002b820ac5200ffd0cc0f0b')
        self.assertEqual(trap, 14)
        for pointer in (0, True, 0x80000000):
            with self.assertRaises(ValueError):
                phase_call_page(pointer)

    def test_live_phase_os_entry_and_stored_clock_evidence(self):
        run = RUNS / 'offline-phase-live-20260920-02'
        result = json.loads((run / 'offline-result.json').read_text())
        phase = result['phase_probe']
        events = [e for e in result['events'] if e.get('stage', '').startswith('PHASE_')]
        self.assertEqual([e['stage'] for e in events], [
            'PHASE_ENTRY', 'PHASE_CLOCK_CALL', 'PHASE_OS_CLOCK_ENTRY',
            'PHASE_CLOCK_RETURN', 'PHASE_RETURN'])
        self.assertEqual(len({(e['pid'], e['tid']) for e in events}), 1)
        self.assertEqual([e['pc'] for e in events], [0x52ac20, 0x52ae2f,
            phase['os_clock_target'], 0x52ae35, phase['page']['return_trap']])
        self.assertIn('winmm!timeGetTime', events[2]['native_stop'])
        self.assertEqual(events[2]['ret'], 0x52ae35)
        self.assertEqual(events[2]['sp'], events[1]['sp'] - 4)
        self.assertEqual(events[3]['sp'], events[1]['sp'])
        self.assertEqual(events[-1]['sp'], phase['entry_sp'])
        bridge = bytes.fromhex(phase['bridge_hex'])
        self.assertEqual(bridge[:4], bytes.fromhex('83ec00e9'))
        self.assertEqual(phase['clock_target'] + 8 + struct.unpack_from('<i', bridge, 4)[0],
                         phase['os_clock_target'])
        for name in ('before', 'after'):
            item = phase[name]
            raw = (run / Path(item['path']).name).read_bytes()
            self.assertEqual(len(raw), item['length'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item['sha256'])
        after = (run / 'phase-after.bin').read_bytes()
        self.assertEqual(struct.unpack_from('<I', after, 0x68)[0], events[3]['eax'])
        self.assertEqual(struct.unpack_from('<i', after, 0xc)[0], phase['count'])
        self.assertEqual(events[-1]['eax'], int(phase['count'] > 0))
        self.assertEqual(result['result'], 'NATIVE_PHASE_CLOCK_RETURNED')
        self.assertTrue(result['entry_patch_restored'])
        self.assertTrue(result['executable_disk_unchanged'])
        self.assertIn('hr=0 written=4', result['timer_restore'])
        self.assertFalse(any('transport_api' in e for e in result['events']))

    def test_identity_only_and_side(self):
        a, b = identity_record(0), identity_record(1)
        self.assertEqual(len(a), 45)
        self.assertEqual([i for i in range(45) if a[i] != b[i]], [1])
        self.assertEqual(b[1], 14)
        self.assertEqual(struct.unpack_from('<HH', a, 5), (0x400, 1))
        self.assertEqual(a[2:5], b'\0' * 3)
        self.assertEqual(a[10:], b'\0' * 35)

    def test_thunk_arguments_and_return_trap(self):
        page, trap = call_page(0x2000000, 0x3000000, 1)
        self.assertEqual(page[:17].hex(), '6800010002b900000003b8905c5100ffd0')
        self.assertEqual(trap, 17)
        self.assertEqual(page[trap:trap + 3], b'\xcc\x0f\x0b')
        self.assertEqual(page[0x100:], identity_record(1))

    def test_reject_invalid_inputs(self):
        for value in (-1, 2, True, '1'):
            with self.assertRaises(ValueError):
                identity_record(value)
        with self.assertRaises(ValueError):
            call_page(0, 0x3000000, 1)

    def test_native_text_initializer_argument_order(self):
        code, trap = text_init_page(0x2100000, 0x2200000, 0x2300000, 7)
        self.assertEqual(code.hex(), '680700000068000030026800002002b900001002b820f95100ffd0cc0f0b')
        self.assertEqual(trap, 27)
        with self.assertRaises(ValueError):
            text_init_page(0x2100000, 0x2200000, 0x2300000, -1)

    def test_real_both_side_constructor_evidence_and_vital_non_authority(self):
        for run_id, values in [('offline-monster-live-20260920-02', [0xcdcdcdcd] * 4),
                               ('offline-monster-live-20260920-03', [1] * 4)]:
            result = review(RUNS / run_id)
            self.assertTrue(result['native_monster_constructor_completed'], result['errors'])
            self.assertEqual(list(result['known_hp_mp_after_raw_u32']), values)
            self.assertEqual(result['original_attack_defense_values_recovered'], 0)
            self.assertFalse(result['vital_values_are_original_species_authority'])
            self.assertFalse(result['playable_single_player_verified'])

    def test_faulted_constructor_never_passes(self):
        result = review(RUNS / 'offline-monster-live-20260920-01')
        self.assertFalse(result['native_monster_constructor_completed'])

    def test_incomplete_or_mutated_native_evidence_fails(self):
        original = json.loads((RUNS / 'offline-monster-live-20260920-02/offline-result.json').read_text())
        for mutation in ('stage', 'pointer', 'packet', 'transport', 'stack', 'pc'):
            report = copy.deepcopy(original)
            if mutation == 'stage':
                report['events'] = [e for e in report['events'] if e.get('stage') != 'MONSTER_DISPLAY_INITIALIZER_RETURN']
            elif mutation == 'pointer':
                report['monster_probe']['text_init']['observed_bindings'][1] = 0
            elif mutation == 'packet':
                report['monster_probe']['record_hex'] = '00' * 45
            elif mutation == 'transport':
                report['events'][0]['transport_api'] = 'send'
            elif mutation == 'stack':
                report['monster_probe']['entry_sp'] += 4
            else:
                next(e for e in report['events'] if e.get('stage') == 'MONSTER_CONSTRUCTOR_ENTRY')['pc'] += 1
            self.assertFalse(audit_payload(report)['native_monster_constructor_completed'], mutation)


if __name__ == '__main__':
    unittest.main()
