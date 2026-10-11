import json
import hashlib
from pathlib import Path
import struct
import subprocess
import unittest

from tools.strike_lab.current_offline_battle_init import call_page, LiveBattleInitProbe

ROOT = Path(__file__).resolve().parents[2]


class OfflineBattleInitializationTests(unittest.TestCase):
    def test_explicit_revival_target_preserves_native_call_code(self):
        from tools.strike_lab.current_offline_vitals_live import action_call_page
        base, trap=action_call_page(0x2000000,0x3000000,skill=True)
        ally, ally_trap=action_call_page(0x2000000,0x3000000,skill=True,target=1)
        self.assertEqual((ally[:256],ally_trap),(base[:256],trap))
        self.assertEqual(ally[256:],b'\x01'+b'\xff'*13)
        for invalid in (-1,28,True,None):
            with self.assertRaises(ValueError):
                action_call_page(0x2000000,0x3000000,skill=True,target=invalid)

    def test_live_disconnected_basic_action_consumes_grant_and_decodes(self):
        from tools.strike_lab.current_offline_vitals_live import action_call_page
        page, trap = action_call_page(0x2000000, 0x3000000)
        self.assertEqual(page[trap:trap+3], b'\xcc\x0f\x0b')
        self.assertEqual(page[256:], b'\x0e' + b'\xff' * 13)
        run = ROOT / 'artifacts/runs/offline-battle-action-20260920-02'
        r = json.loads((run / 'offline-result.json').read_text())
        a = r['action_probe']
        events = [e for e in r['events'] if e.get('stage', '').startswith('ACTION_')]
        self.assertEqual([e['stage'] for e in events], ['ACTION_ENTRY', 'ACTION_POST_BUILD', 'ACTION_RETURN'])
        self.assertEqual([e['pc'] for e in events], [0x518e50, 0x5191ee, a['page']['return_trap']])
        self.assertEqual(events[0]['sp'], a['entry_sp'] - 20)
        self.assertEqual(events[-1]['sp'], a['entry_sp'])
        self.assertEqual(a['return_eax'], 1)
        self.assertEqual(a['controls_after'], [1, 0, 0])
        self.assertEqual(r['vitals_probe']['grant_controls'], [0, 1, 0])
        self.assertEqual(len({(e['pid'], e['tid']) for e in events}), 1)
        decoded = subprocess.check_output([str(ROOT / 'build/tests/Release/recovered-battle-command.exe'),
            '--decode', a['logical_hex']], text=True, timeout=10).strip()
        self.assertEqual(decoded, '0 0 0 0 1 0 1')
        self.assertEqual(r['result'], 'NATIVE_DISCONNECTED_ACTION_RETURNED')
        self.assertIsNone(r.get('error'))
        self.assertTrue(r['entry_patch_restored'])
        self.assertTrue(r['executable_disk_unchanged'])
        self.assertIn('hr=0 written=4', r['timer_restore'])
        self.assertFalse(any('transport_api' in e for e in r['events']))

    def test_live_bulk_initializes_counter_before_next_dispatch_grant(self):
        from tools.strike_lab.current_offline_vitals_live import diagnostic_payload
        r = json.loads((ROOT / 'artifacts/runs/offline-battle-grant-20260920-03/offline-result.json').read_text())
        v = r['vitals_probe']
        self.assertEqual(bytes.fromhex(v['payload_hex']), diagnostic_payload(True, True))
        self.assertEqual(v['ring_after_bulk'][2:4], [262, 279])
        self.assertEqual(v['ring_after'], v['ring_before'])
        self.assertEqual(v['grant_counter'], 0)
        self.assertEqual(v['rearm_entry'], {'counter': 0, 'ecx': r['battle_init_probe']['battle']})
        self.assertEqual(v['grant_controls'], [0, 1, 0])
        self.assertEqual(v['grant_actors'], [0, 255])
        events = [e for e in r['events'] if e.get('stage', '').startswith(('VITALS_', 'GRANT_'))]
        self.assertEqual([e['stage'] for e in events], [
            'VITALS_NATIVE_QUEUE', 'VITALS_LOOP_ENTRY', 'VITALS_DISPATCH_ENTRY',
            'VITALS_ENTRY', 'VITALS_BATCH', 'VITALS_CLEANUP', 'VITALS_DISPATCH_RETURN',
            'VITALS_DISPATCH_ENTRY', 'GRANT_ENTRY', 'GRANT_REARM_ENTRY',
            'GRANT_RETURN', 'VITALS_DISPATCH_RETURN'])
        self.assertEqual(events[9]['pc'], 0x5121f0)
        self.assertEqual(events[8]['sp'], events[10]['sp'])
        self.assertEqual(events[10]['eax'], 1)
        self.assertEqual(len({(e['pid'], e['tid']) for e in events}), 1)
        self.assertEqual(struct.unpack('<4I', bytes.fromhex(v['after_hex'][0])), (100, 50, 120, 80))
        self.assertEqual(v['after_hex'][14], '96000000cdcdcdcd96000000cdcdcdcd')
        self.assertEqual(r['result'], 'NATIVE_BATTLE_DISPATCH_RETURNED')
        self.assertIsNone(r.get('error'))
        self.assertTrue(r['entry_patch_restored'])
        self.assertTrue(r['executable_disk_unchanged'])
        self.assertIn('hr=0 written=4', r['timer_restore'])
        self.assertFalse(any('transport_api' in e for e in r['events']))

    def test_live_first_grant_returns_without_claiming_attack_rearm(self):
        from tools.strike_lab.current_offline_vitals_live import diagnostic_payload, grant_record, loop_call_page
        payload = diagnostic_payload(True, True)
        self.assertEqual(len(payload), 279)
        self.assertEqual(payload[262:], grant_record())
        self.assertEqual(grant_record(), bytes.fromhex('8605000100') + bytes(12))
        page, _ = loop_call_page(0x2000000, 0x3000000, True, True)
        self.assertEqual(struct.unpack_from('<I', page, 1)[0], 279)
        self.assertEqual(page[256:], payload)
        with self.assertRaises(ValueError):
            diagnostic_payload(False, True)
        r = json.loads((ROOT / 'artifacts/runs/offline-battle-grant-20260920-01/offline-result.json').read_text())
        v = r['vitals_probe']
        # Historical first-grant run put grant before bulk initialization.
        self.assertEqual(bytes.fromhex(v['payload_hex']), payload[:141] + grant_record() + payload[141:262])
        self.assertEqual(v['grant_stages'], ['GRANT_ENTRY', 'GRANT_RETURN'])
        self.assertEqual(v['grant_controls'], [0, 1, 0])
        self.assertEqual(v['grant_actors'], [0, 255])
        # Sentinel still prevents ordinary rearm: a grant is not an attack.
        self.assertEqual(v['grant_counter'], 0xffffffff)
        grants = [e for e in r['events'] if e.get('stage', '').startswith('GRANT_')]
        self.assertEqual([e['pc'] for e in grants], [0x517590, 0x5177b5])
        self.assertEqual(grants[0]['sp'], grants[1]['sp'])
        self.assertEqual(grants[1]['eax'], 1)
        bulk = next(e for e in r['events'] if e.get('stage') == 'VITALS_ENTRY')
        self.assertLess(grants[1]['sequence'], bulk['sequence'])
        self.assertEqual(len({(e['pid'], e['tid']) for e in grants + [bulk]}), 1)
        self.assertEqual(v['ring_queued'][2:4], [0, 279])
        self.assertEqual(v['ring_after'], v['ring_before'])
        self.assertEqual(r['result'], 'NATIVE_BATTLE_DISPATCH_RETURNED')
        self.assertIsNone(r.get('error'))
        self.assertTrue(r['entry_patch_restored'])
        self.assertTrue(r['executable_disk_unchanged'])
        self.assertIn('hr=0 written=4', r['timer_restore'])
        self.assertFalse(any('transport_api' in e for e in r['events']))

    def test_live_bounded_vitals_scalar_then_bulk_dispatch(self):
        from tools.strike_lab.current_offline_vitals_live import diagnostic_payload, diagnostic_record
        run = ROOT / 'artifacts/runs/offline-battle-actors-vitals-20260920-01'
        r = json.loads((run / 'offline-result.json').read_text())
        v = r['vitals_probe']
        payload = diagnostic_payload(True)
        self.assertEqual(len(payload), 262)
        self.assertEqual(bytes.fromhex(v['payload_hex']), payload)
        for offset, expected in zip((90, 107, 124), (
                '8600000000780000006400000000000000',
                '8601000000500000003200000000000000',
                '86000e0000960000009600000000000000')):
            self.assertEqual(payload[offset:offset + 17].hex(), expected)
        self.assertEqual(payload[141:], diagnostic_record(True))
        self.assertEqual(v['ring_queued'][2:4], [0, 262])
        self.assertEqual(v['ring_after'], v['ring_before'])
        self.assertEqual(v['ring_after'][2:4], [0, 0])
        before = [bytes.fromhex(s) for s in v['before_88_hex']]
        after = [bytes.fromhex(s) for s in v['after_hex']]
        self.assertEqual(len(before), 28)
        self.assertEqual(len(after), 28)
        self.assertEqual(struct.unpack('<4I', before[0]), (100, 50, 120, 80))
        self.assertEqual(before[14], bytes.fromhex('96000000cdcdcdcd96000000cdcdcdcd'))
        for i in range(28):
            expected = before[i] if i == 0 or i >= 14 else bytes(8) + before[i][8:]
            self.assertEqual(after[i], expected)
        for slot, info in zip((0, 14), v['created_actor_snapshots']):
            raw = (run / Path(info['path']).name).read_bytes()
            self.assertEqual(len(raw), 0xecc)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), info['sha256'])
            self.assertEqual(raw[0xde8:0xdf8], before[slot])
            self.assertTrue(0 <= struct.unpack_from('<h', raw, 0x1a)[0] < 4096)
        events = [e for e in r['events'] if e.get('stage', '').startswith(('BATTLE_', 'VITALS_'))]
        self.assertEqual(len({(e['pid'], e['tid']) for e in events}), 1)
        self.assertEqual(events[-1]['stage'], 'VITALS_DISPATCH_RETURN')
        self.assertEqual(events[-1]['sp'], v['dispatch_sp'] + 12)
        self.assertEqual(r['result'], 'NATIVE_BATTLE_DISPATCH_RETURNED')
        self.assertIsNone(r.get('error'))
        self.assertTrue(r['entry_patch_restored'])
        self.assertTrue(r['executable_disk_unchanged'])
        self.assertIn('hr=0 written=4', r['timer_restore'])
        self.assertFalse(any('transport_api' in e for e in r['events']))

    def test_live_two_native_participants_then_bulk_update(self):
        from tools.strike_lab.current_offline_vitals_live import diagnostic_payload, diagnostic_record, loop_call_page
        from tools.strike_lab.current_offline_monster_live import identity_record
        payload = diagnostic_payload(True)
        self.assertEqual(len(payload), 262)
        self.assertEqual(payload[:90], identity_record(0) + identity_record(1))
        page, _ = loop_call_page(0x2000000, 0x3000000, True)
        self.assertEqual(struct.unpack_from('<I', page, 1)[0], 262)
        self.assertEqual(page[256:], payload)
        run = ROOT / 'artifacts/runs/offline-battle-actors-20260920-01'
        r = json.loads((run / 'offline-result.json').read_text())
        v = r['vitals_probe']
        # Historical raw-parser experiment predates bounded-vitals payload v2.
        self.assertEqual(bytes.fromhex(v['payload_hex']), identity_record(0) + identity_record(1) + diagnostic_record())
        self.assertEqual(v['ring_queued'][2:4], [0, 211])
        self.assertEqual(v['ring_after'], v['ring_before'])
        self.assertEqual(len(v['created_actor_handles']), 2)
        self.assertTrue(all(0 <= h < 4096 for h in v['created_actor_handles']))
        for index, info in enumerate(v['created_actor_snapshots']):
            raw = (run / Path(info['path']).name).read_bytes()
            self.assertEqual(len(raw), 0xecc)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), info['sha256'])
            self.assertEqual(struct.unpack_from('<h', raw, 0x1a)[0], v['created_actor_handles'][index])
            self.assertEqual(raw[0xde8:0xdf8].hex(), v['before_88_hex'][index * 14])
        self.assertEqual(len(v['after_hex']), 28)
        for i in range(28):
            before = bytes.fromhex(v['before_88_hex'][i])
            after = bytes.fromhex(v['after_hex'][i])
            self.assertEqual(after, struct.pack('<II', 1000+i, 50+i) + before[8:] if i < 14 else before)
        self.assertEqual(r['result'], 'NATIVE_BATTLE_DISPATCH_RETURNED')
        self.assertIsNone(r.get('error'))
        events = [e for e in r['events'] if e.get('stage', '').startswith(('BATTLE_', 'VITALS_'))]
        self.assertEqual(len({(e['pid'], e['tid']) for e in events}), 1)
        self.assertTrue(r['entry_patch_restored'])
        self.assertTrue(r['executable_disk_unchanged'])
        self.assertFalse(any('transport_api' in e for e in r['events']))

    def test_live_native_queue_loop_dispatch_and_vitals_in_one_process(self):
        from tools.strike_lab.current_offline_vitals_live import loop_call_page
        page, trap = loop_call_page(0x2000000, 0x3000000)
        self.assertEqual(page[:10], bytes.fromhex('68790000006800010002'))
        self.assertEqual(page[trap:trap + 3], b'\xcc\x0f\x0b')
        self.assertIn(bytes.fromhex('83ec048bc450'), page[:trap])
        run = ROOT / 'artifacts/runs/offline-battle-dispatch-20260920-01'
        r = json.loads((run / 'offline-result.json').read_text())
        v = r['vitals_probe']
        events = [e for e in r['events'] if e.get('stage', '').startswith('VITALS_')]
        self.assertEqual([e['stage'] for e in events], [
            'VITALS_NATIVE_QUEUE', 'VITALS_LOOP_ENTRY', 'VITALS_DISPATCH_ENTRY',
            'VITALS_ENTRY', 'VITALS_BATCH', 'VITALS_CLEANUP', 'VITALS_DISPATCH_RETURN'])
        self.assertEqual([e['pc'] for e in events],
            [0x51d4e0, 0x515770, 0x5140c0, 0x518a90, 0x52d360, 0x516ac0, 0x515a51])
        init_events = [e for e in r['events'] if e.get('stage', '').startswith('BATTLE_')]
        self.assertEqual(len({(e['pid'], e['tid']) for e in events + init_events}), 1)
        self.assertLess(init_events[-1]['sequence'], events[0]['sequence'])
        self.assertEqual(events[-1]['sp'], events[2]['sp'] + 12)
        self.assertEqual(v['ring_before'], v['ring_after'])
        self.assertEqual(v['ring_queued'][2:4], [0, 121])
        self.assertEqual(v['ring_after'][2:4], [0, 0])
        self.assertEqual(len(v['after_hex']), 28)
        for i in range(28):
            before, after = bytes.fromhex(v['before_hex'][i]), bytes.fromhex(v['after_hex'][i])
            self.assertEqual(after, struct.pack('<II', 1000+i, 50+i) + before[8:] if i < 14 else before)
        self.assertEqual(r['result'], 'NATIVE_BATTLE_DISPATCH_RETURNED')
        self.assertIsNone(r.get('error'))
        self.assertTrue(r['entry_patch_restored'])
        self.assertTrue(r['executable_disk_unchanged'])
        self.assertIn('hr=0 written=4', r['timer_restore'])
        self.assertFalse(any('transport_api' in e for e in r['events']))

    def test_live_initialized_receiver_same_process_and_exact_vital_updates(self):
        run = ROOT / 'artifacts/runs/offline-initialized-vitals-20260920-01'
        r = json.loads((run / 'offline-result.json').read_text())
        init, vitals = r['battle_init_probe'], r['vitals_probe']
        events = [e for e in r['events'] if e.get('stage', '').startswith(('BATTLE_', 'VITALS_'))]
        self.assertEqual([e['stage'] for e in events], [
            'BATTLE_INIT_ENTRY', 'BATTLE_OWNERS_BOUND', 'BATTLE_TEXT_INITIALIZED', 'BATTLE_INIT_RETURN',
            'VITALS_ENTRY', 'VITALS_BATCH', 'VITALS_CLEANUP', 'VITALS_RETURN'])
        self.assertEqual(len({(e['pid'], e['tid']) for e in events}), 1)
        self.assertEqual([e['pc'] for e in events[4:]],
            [0x518a90, 0x52d360, 0x516ac0, vitals['page']['return_trap']])
        self.assertEqual(events[3]['sp'], vitals['entry_sp'])
        self.assertEqual(events[-1]['sp'], init['entry_sp'])
        self.assertEqual(events[-1]['eax'], 1)
        self.assertEqual(r['vitals_preflight']['role'], init['observed_role'])
        self.assertEqual(vitals['actors'], init['actor_pointers'][::6])
        self.assertEqual(len(vitals['before_hex']), 28)
        self.assertEqual(len(vitals['after_hex']), 28)
        for i, (before, after) in enumerate(zip(vitals['before_hex'], vitals['after_hex'])):
            a, b = bytes.fromhex(before), bytes.fromhex(after)
            self.assertEqual(b, struct.pack('<II', 1000 + i, 50 + i) + a[8:] if i < 14 else a)
        for key in ('controls_before', 'controls_after'):
            info = vitals[key]
            raw = (run / Path(info['path']).name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), info['sha256'])
            self.assertEqual(len(raw), info['length'])
        self.assertEqual(r['result'], 'NATIVE_VITALS_RECEIVER_RETURNED')
        self.assertIsNone(r.get('error'))
        self.assertTrue(r['entry_patch_restored'])
        self.assertTrue(r['executable_disk_unchanged'])
        self.assertIn('hr=0 written=4', r['timer_restore'])
        self.assertFalse(any('transport_api' in e for e in r['events']))

    def test_descriptor_and_immutable_zero_context(self):
        page, trap = call_page(0x2000000, 0x3000000, 0x4000000,
                               0x5000000, 0x6000000, 0x7000000)
        self.assertEqual(page[:17].hex(), '6880000002b900000003b8c0125100ffd0')
        self.assertEqual(page[trap:trap + 3], b'\xcc\x0f\x0b')
        self.assertEqual(struct.unpack_from('<7I', page, 0x80),
            (0x4000000, 0x2000100, 0xf7f2f6c, 0x6000000,
             0x1a39683c, 0x7000000, 0x1a383410))
        self.assertEqual(page[0x100:], bytes(0x3ec))
        self.assertFalse(LiveBattleInitProbe.handles(None))
        with self.assertRaises(ValueError):
            call_page(0, 0x3000000, 0x4000000, 0x5000000, 0x6000000, 0x7000000)

    def test_live_full_initializer_owns_role_and_returns(self):
        path = ROOT / 'artifacts/runs/offline-battle-init-20260920-01/offline-result.json'
        r = json.loads(path.read_text())
        state = r['battle_init_probe']
        events = [e for e in r['events'] if e.get('stage', '').startswith('BATTLE_')]
        self.assertEqual([e['stage'] for e in events], [
            'BATTLE_INIT_ENTRY', 'BATTLE_OWNERS_BOUND', 'BATTLE_TEXT_INITIALIZED', 'BATTLE_INIT_RETURN'])
        self.assertEqual([e['pc'] for e in events],
            [0x5112c0, 0x51132f, 0x51151b, state['page']['return_trap']])
        self.assertEqual(len({(e['pid'], e['tid']) for e in events}), 1)
        self.assertEqual(events[0]['sp'], state['entry_sp'] - 8)
        self.assertEqual(events[-1]['sp'], state['entry_sp'])
        self.assertEqual(events[-1]['eax'], 1)
        self.assertEqual(state['observed_role'], state['world'] + 0x1539683c)
        prefix = bytes.fromhex(state['battle_prefix_hex'])
        self.assertEqual(struct.unpack_from('<I', prefix, 0x14)[0], state['observed_role'])
        self.assertEqual(prefix[0x51:0x53], b'\xff\xff')
        controls = bytes.fromhex(state['control_hex'])
        self.assertEqual(struct.unpack_from('<I', controls, 0x64 - 0x28)[0], 0xffffffff)
        for field in (0x34, 0x38, 0x3c, 0x44):
            self.assertEqual(struct.unpack_from('<I', controls, field - 0x28)[0], 0)
        self.assertEqual(r['result'], 'NATIVE_BATTLE_INITIALIZER_RETURNED')
        self.assertIsNone(r.get('error'))
        self.assertTrue(r['entry_patch_restored'])
        self.assertTrue(r['executable_disk_unchanged'])
        self.assertIn('hr=0 written=4', r['timer_restore'])
        self.assertFalse(any('transport_api' in e for e in r['events']))


if __name__ == '__main__':
    unittest.main()
