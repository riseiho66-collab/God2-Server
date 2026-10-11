"""Bounded native appearance routing; not full rendering acceptance."""
import json
import struct
import sqlite3
from pathlib import Path
import unittest

from tools.strike_lab.current_battle_entry import (
    NativeRun, BATTLE, PACKET_PAGE, SP, native_length,
)
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_ECX


class BattlePlayerAppearanceTests(unittest.TestCase):
    def test_live_skill_selector_has_no_source_rows(self):
        root = Path(__file__).resolve().parents[2]
        run = root/'artifacts/runs/native-player-skill-prerequisite-20260921-02/run.json'
        evidence = json.loads(run.read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_PARTICIPANTS_GRANTED')
        state = evidence['socket_skill_prerequisites']
        self.assertEqual(state['scope'],'READ_ONLY_NOT_LEARNED_OWNERSHIP')
        self.assertEqual((state['current_bank'],state['bank_count'],state['selected_index']),(-1,0,-1))
        self.assertEqual(state['banks'],[])
        self.assertEqual((state['source_current'],state['source_row_count']),(-1,0))

    def test_player_terminal_returns_to_world_and_persists_movement(self):
        self.check_terminal_movement('native-player-terminal-20260921-02')

    def test_animated_player_terminal_returns_to_world_and_persists_movement(self):
        self.check_terminal_movement('native-player-animation-terminal-20260921-01')

    def test_corrected_outcomes_finish_then_restore_saved_position_in_fresh_client(self):
        self.check_terminal_movement('native-player-outcome-fixed-terminal-20260921-01')
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        restored=root/'native-player-outcome-fixed-restore-20260921-01'
        report=json.loads((restored/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(report['result'],'NATIVE_SAVED_POSITION_RESTORED')
        self.assertIsNone(report.get('error'))
        self.assertEqual(report['restored_position_hex'],'120000000c000000')
        self.assertEqual(bytes.fromhex(report['character_list_consumer']['copied_hex'])[0],1)
        with sqlite3.connect((restored/'diagnostic-accounts.db').resolve().as_uri()+'?mode=ro',uri=True) as db:
            self.assertEqual(db.execute('select character_id,area,scene,x,y,revision from recovered_positions').fetchall(),
                             [(1,2,15,18,12,3)])

    def check_terminal_movement(self,run_id):
        root = Path(__file__).resolve().parents[2]
        run = root / 'artifacts/runs' / run_id
        report = json.loads((run / 'run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_MOVEMENT_PATH_COMPLETED')
        self.assertEqual(bytes.fromhex(report['socket_participants'][0]['logical_hex'])[5:7],b'\x00\x20')
        keys = ('socket_damage_return','socket_outcome_return','socket_outcome_panel_return',
                'socket_battle_loop_return','socket_post_battle_world_loop_entry')
        sequences = [report[key]['sequence'] for key in keys]
        self.assertEqual(sequences,sorted(set(sequences)))
        self.assertEqual(bytes.fromhex(report['socket_damage_return']['enemy_vitals_hex'])[:4],bytes(4))
        self.assertEqual(len(report['movement_steps']),3)
        completion = report['movement_completion']
        self.assertEqual(completion['position_hex'],'120000000c000000')
        self.assertEqual(completion['motion_state'],0)
        self.assertGreater(completion['event']['sequence'],sequences[-1])
        with sqlite3.connect((run/'diagnostic-accounts.db').resolve().as_uri()+'?mode=ro',uri=True) as db:
            self.assertEqual(db.execute('select character_id,area,scene,x,y,revision from recovered_positions').fetchall(),
                             [(1,2,15,18,12,3)])
        log = (run/'diagnostic-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_FINISHED_BATTLE_RELEASED'),1)
        self.assertNotIn('Recovered world policy or response rejected',log)

    def test_player_two_exchanges_require_native_completion_before_rearm(self):
        root = Path(__file__).resolve().parents[2]
        run = root / 'artifacts/runs/native-player-two-rounds-20260921-04'
        report = json.loads((run / 'run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_SOCKET_DIAGNOSTIC_RETALIATION_APPLIED')
        rounds = report['socket_completed_rounds']
        self.assertEqual(len(rounds), 2)
        for turn, enemy, friendly in zip(rounds, (132,114), (88,76)):
            self.assertEqual(int.from_bytes(bytes.fromhex(turn['socket_damage_return']['enemy_vitals_hex'])[:4], 'little'),enemy)
            self.assertEqual(int.from_bytes(bytes.fromhex(turn['socket_retaliation_return']['enemy_vitals_hex'])[:4], 'little'),friendly)
        self.assertLess(rounds[0]['socket_retaliation_return']['sequence'],rounds[1]['socket_grant_entry']['sequence'])
        log = (run / 'diagnostic-server.log').read_text()
        self.assertEqual(log.count('DIAGNOSTIC_NEXT_ROUND_GRANTED'), 1)
        self.assertNotIn('Recovered world policy or response rejected', log)
        self.assertEqual(bytes.fromhex(report['socket_participants'][0]['logical_hex'])[5:7],b'\x00\x20')

    def test_live_control_latch_explains_missing_post_action_notification(self):
        root = Path(__file__).resolve().parents[2]
        report = json.loads((root / 'artifacts/runs/native-player-control-gate-20260921-01/run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_SOCKET_DIAGNOSTIC_RETALIATION_APPLIED')
        state = report['socket_retaliation_return']['control_gate']
        self.assertEqual(state, dict(result_received=0, manager_event=0, control_sent=1,
                                     bulk_seen=1, counter=0, completed_counter=0, target_count=1))
        n = NativeRun()
        for name, offset in (('result_received',0xa9df6bc),('manager_event',0x144c1c),
                             ('control_sent',0xa9e9c44),('bulk_seen',0xa9e9c48),
                             ('counter',0xa9e9c64),('completed_counter',0xa9e9c68),('target_count',0x45c)):
            n.put32(BATTLE + offset, state[name])
        n.registers(esi=BATTLE, ebx=0, edi=1)
        n.run(0x115a59, ((0x115a59,0x115add),), {0x115add,0x118e50})
        self.assertEqual(n.stop,0x115add)
        self.assertIn(0x115ab2,n.visits)
        self.assertNotIn(0x115ad8,n.visits)

    def test_player_live_attack_and_retaliation_but_not_second_round(self):
        root = Path(__file__).resolve().parents[2]
        run = root / 'artifacts/runs/native-player-two-rounds-20260921-03'
        report = json.loads((run / 'run.json').read_text())
        self.assertEqual(report['result'], 'HARD_TIMEOUT')
        rounds = report['socket_completed_rounds']
        self.assertEqual(len(rounds), 1)
        hit = rounds[0]
        self.assertEqual(bytes.fromhex(hit['socket_damage_entry']['logical_hex'])[9:13],
                         (132).to_bytes(4, 'little'))
        self.assertEqual(bytes.fromhex(hit['socket_damage_return']['enemy_vitals_hex'])[:4],
                         (132).to_bytes(4, 'little'))
        self.assertEqual(bytes.fromhex(hit['socket_retaliation_return']['enemy_vitals_hex'])[:4],
                         (88).to_bytes(4, 'little'))
        self.assertGreaterEqual(report['socket_participants'][0]['prior_render_handle'], 0)
        log = (run / 'diagnostic-server.log').read_text()
        self.assertNotIn('Recovered world policy or response rejected', log)
        self.assertNotIn('DIAGNOSTIC_NEXT_ROUND_GRANTED', log)

    def test_player_action_is_queued_but_live_server_rejects_batch(self):
        root = Path(__file__).resolve().parents[2]
        run = root / 'artifacts/runs/native-player-two-rounds-20260921-02'
        report = json.loads((run / 'run.json').read_text())
        action = report['socket_action_return']
        self.assertEqual(action['network_active'], 1)
        self.assertEqual(action['queued_length'], 17)
        logical = bytes.fromhex(action['queued_logical_hex'])
        self.assertEqual(logical[:13], bytes.fromhex('35000100000000010000000000'))
        # The last DWORD is unwritten native stack storage, not a fixed key.
        sent = (run / 'crypto-private/tx-input-0500.plain.bin').read_bytes()
        self.assertEqual(sent[2:-1], logical)
        self.assertIn('Recovered world policy or response rejected',
                      (run / 'diagnostic-server.log').read_text())
        self.assertFalse(report.get('socket_completed_rounds'))

    def test_live_appearance_creates_handle_before_player_identity(self):
        root = Path(__file__).resolve().parents[2]
        for name, outcome in (
                ('native-player-appearance-20260921-01', 'NATIVE_SOCKET_PARTICIPANTS_GRANTED'),
                ('native-player-two-rounds-20260921-01', 'EVENT_BUDGET_END')):
            report = json.loads((root / 'artifacts/runs' / name / 'run.json').read_text())
            self.assertEqual(report['result'], outcome)
            friendly, hostile = report['socket_participants']
            identity = bytes.fromhex(friendly['logical_hex'])
            self.assertEqual(identity[:7], bytes.fromhex('1c000001000020'))
            self.assertGreaterEqual(friendly['prior_render_handle'], 0)
            self.assertEqual(friendly['local_player_identity'], 1)
            metadata = bytes.fromhex(friendly['prior_metadata_hex'])
            self.assertEqual(metadata[46:54], bytes.fromhex('0180016001603100'))
            self.assertEqual(hostile['prior_render_handle'], -1)
            self.assertEqual(report['socket_grant_return']['first_grant'], 1)
            self.assertEqual(report['socket_actor_vitals'][0], '64000000320000007800000050000000')
            self.assertIsNot(report.get('world_accepted'), True)
            if outcome == 'EVENT_BUDGET_END':
                self.assertIn('socket_action_return', report)
                self.assertFalse(report.get('socket_completed_rounds'))

    def test_subtype_four_calls_original_appearance_handler(self):
        n = NativeRun()
        record = BATTLE + 0xa9e9cb1
        n.put(record, bytes([4, 0, 1]) + bytes(11))
        n.put(PACKET_PAGE, b'\x86')
        n.registers(esi=BATTLE, ebp=PACKET_PAGE, eax=0xdeadbe00)
        n.run(0x114332, ((0x114332, 0x114358), (0x114464, 0x11447a),
                         (0x1144c8, 0x1144d0)), {0x1177c0})
        sp = n.vm.reg_read(UC_X86_REG_ESP)
        self.assertEqual(n.stop, 0x1177c0)
        self.assertEqual(n.get32(sp), 0x5144d0)
        self.assertEqual(n.get32(sp + 4), record)
        self.assertEqual(n.vm.reg_read(UC_X86_REG_ECX), BATTLE)
        self.assertEqual(native_length(0x86), 17)

    def test_main_component_resource_arguments_and_variant_bits(self):
        # Independent instruction islands, not a continuous resource load.
        # Every value of each packed byte is exercised, including high bits.
        for value in range(256):
            n = NativeRun()
            first, second = value, 255 - value
            record = bytearray(14)
            record[3:5] = bytes([first, second])
            n.put(PACKET_PAGE, bytes(record))
            n.put32(SP + 0x14, BATTLE)
            n.put32(SP + 0x34, 7)  # Explicit diagnostic resource-family input.
            n.registers(ebp=PACKET_PAGE, esi=1, esp=SP)
            n.run(0x118527, ((0x118527, 0x118555),), {0x54e50})
            sp = n.vm.reg_read(UC_X86_REG_ESP)
            args = struct.unpack('<6I', n.vm.mem_read(sp + 4, 24))
            self.assertEqual(tuple(v & 255 for v in args),
                             (1, 7, first & 15, 0, first >> 4, second & 31))
            self.assertEqual(n.vm.reg_read(UC_X86_REG_ECX), BATTLE + 0x132740)

            actor = PACKET_PAGE + 0x1000
            metadata = SP + 0x38
            n.put(actor + 0x24, b'\x34\x01')
            n.put32(SP + 0x24, 13)
            n.put32(SP + 0x2c, BATTLE + 0x144938)
            n.registers(ebp=PACKET_PAGE, edi=actor, esi=1, esp=SP,
                        eax=0xa5a5a5a5, edx=0xa5a5a5a5)
            n.run(0x118650, ((0x118650, 0x118672),), {0x1216c0})
            sp = n.vm.reg_read(UC_X86_REG_ESP)
            args = struct.unpack('<6I', n.vm.mem_read(sp + 4, 24))
            self.assertEqual(args[0] & 65535, 0x134)
            self.assertEqual(args[1:4], (1, 13, 0))
            self.assertEqual(args[4] & 255, second >> 5)
            self.assertEqual(args[5], metadata)
            self.assertEqual(n.vm.reg_read(UC_X86_REG_ECX), BATTLE + 0x144938)

    def test_original_position_and_mode_prefix(self):
        # Stop BEFORE renderer/resource calls. No fake callee returns.
        for position in range(28):
            for mode, stop in ((0, 0x11890b), (1, 0x1182b9),
                               (2, 0x118a79)):
                with self.subTest(position=position, mode=mode):
                    n = NativeRun()
                    n.put(PACKET_PAGE, bytes([4, position, mode]) + bytes(11))
                    n.put32(SP + 4, PACKET_PAGE)
                    n.registers(ecx=BATTLE)
                    n.run(0x1177c0, ((0x1177c0, 0x117823),),
                          {0x11890b, 0x1182b9, 0x118a79})
                    sp = n.vm.reg_read(UC_X86_REG_ESP)
                    self.assertEqual(n.stop, stop)
                    self.assertEqual(n.vm.mem_read(sp + 0x10, 1)[0], position // 14)
                    self.assertEqual(n.vm.mem_read(sp + 0x24, 1)[0], position % 14)

    def test_observed_participants_start_without_render_handle(self):
        root = Path(__file__).resolve().parents[2]
        run = root / 'artifacts/runs/native-battle-player-prerequisite-20260921-01'
        report = json.loads((run / 'run.json').read_text())
        self.assertEqual(report['result'], 'NATIVE_SOCKET_PARTICIPANTS_GRANTED')
        events = [json.loads(line) for line in
                  (run / 'compat-events.jsonl').read_text().splitlines()]
        entries = [e for e in events if 'prior_render_handle' in e]
        self.assertEqual(len(entries), 2)
        self.assertEqual([bytes.fromhex(e['logical_hex'])[1] for e in entries], [0, 14])
        for event in entries:
            self.assertEqual(event['prior_render_handle'], -1)
            self.assertEqual(event['local_player_identity'], 1)
            self.assertEqual(bytes.fromhex(event['prior_metadata_hex']),
                             b'\xff\xff' + bytes(54))


if __name__ == '__main__':
    unittest.main()
