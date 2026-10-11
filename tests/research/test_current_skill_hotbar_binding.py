"""Pinned native hotbar writer windows; not full UI or live cast acceptance."""
import struct
import unittest
import json
import tempfile
import subprocess
import sqlite3
from pathlib import Path

from tools.strike_lab.current_battle_entry import NativeRun, PACKET_PAGE, SP, pinned_image


class SkillHotbarBindingTests(unittest.TestCase):
    def test_live_low_mp_refusal_regrants_then_basic_and_retaliation_complete(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs/native-player-skill-mp-refusal-20260921-02'
        evidence=json.loads((root/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_ANIMATION_ROUNDS_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        refusal=evidence['socket_mp_refusal']
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(refusal['actor_vitals_hex'])),(100,7,120,80))
        self.assertEqual(refusal['regrant']['control_state'],dict(panel=0,waiting=0,first_grant=1,second_grant=0,counter=0,completed_counter=0))
        self.assertEqual(bytes.fromhex(evidence['socket_skill_command_return']['queued_logical_hex'])[2],3)
        self.assertEqual(bytes.fromhex(evidence['socket_action_return']['queued_logical_hex'])[2],1)
        self.assertEqual(len(evidence['socket_skill_commands']),1)
        self.assertEqual(int.from_bytes(bytes.fromhex(evidence['socket_damage_return']['enemy_vitals_hex'])[:4],'little'),132)
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(evidence['socket_retaliation_return']['enemy_vitals_hex'])),(88,7,120,80))
        sequences=[evidence['socket_skill_command_return']['sequence'],refusal['sequence'],
                   refusal['regrant']['sequence'],evidence['socket_action_return']['sequence'],
                   evidence['socket_damage_return']['sequence'],evidence['socket_retaliation_return']['sequence']]
        self.assertEqual(sequences,sorted(set(sequences)))
        self.assertEqual(len(evidence['animation_batch_completions']),2)
        for batch in evidence['animation_batch_completions']:
            self.assertEqual((batch['expected'],batch['completed'],batch['timeout_fallback']),(1,1,False))
        config=json.loads((root/'diagnostic-server-config.json').read_text(encoding='utf-8'))
        self.assertTrue(config['development']['diagnostic_battle_mp_refusal'])

    def test_live_terminal_skill_debits_once_and_returns_to_world(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs/native-player-skill-terminal-20260921-01'
        evidence=json.loads((root/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_MOVEMENT_PATH_COMPLETED')
        records=evidence['socket_skill_terminal_vitals']
        self.assertEqual(len(evidence['socket_skill_commands']),1)
        self.assertEqual(len(evidence['socket_skill_settlement']),2)
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(records[0]['actor_vitals_hex'])),(100,42,120,80))
        self.assertEqual(int.from_bytes(bytes.fromhex(records[1]['actor_vitals_hex'])[:4],'little'),0)
        batches=evidence['animation_batch_completions']
        self.assertEqual(len(batches),1)
        self.assertEqual((batches[0]['expected'],batches[0]['completed'],batches[0]['timeout_fallback']),(1,1,False))
        self.assertEqual(evidence['skill_animation_definition_hex'],'0100')
        sequences=[records[-1]['sequence'],batches[0]['sequence']]+[
            evidence[key]['sequence'] for key in ('socket_outcome_return','socket_outcome_panel_return',
                                                 'socket_battle_loop_return','socket_post_battle_world_loop_entry')]
        self.assertEqual(sequences,sorted(set(sequences)))
        self.assertEqual(evidence['movement_completion']['position_hex'],'120000000c000000')
        with sqlite3.connect((root/'diagnostic-accounts.db').resolve().as_uri()+'?mode=ro',uri=True) as db:
            self.assertEqual(db.execute('select character_id,area,scene,x,y,revision from recovered_positions').fetchall(),
                             [(1,2,15,18,12,3)])

    def test_live_corrected_outcomes_preserve_both_living_targets(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        evidence=json.loads((root/'native-player-skill-surviving-targets-20260921-02/run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_SKILL_ANIMATIONS_COMPLETED')
        self.assertEqual(evidence['skill_target_mask_watch']['initial_hex'],'0100000001000000')
        self.assertEqual(evidence.get('skill_target_mask_writes',[]),[])
        self.assertEqual(len(evidence['socket_skill_rounds']),2)
        for round_ in evidence['socket_skill_rounds']:
            self.assertEqual(round_['selection']['target_counts_hex'],'0101')
            self.assertEqual(round_['selection']['target_masks_hex'],'0100000001000000')
        self.assertEqual(len(evidence['animation_batch_completions']),4)
        for batch in evidence['animation_batch_completions']:
            self.assertEqual((batch['expected'],batch['completed']),(1,1))
            self.assertFalse(batch['timeout_fallback'])

    def test_live_regrant_clears_wait_but_second_selection_has_no_targets(self):
        path=Path(__file__).resolve().parents[2]/'artifacts/runs/native-player-skill-rearm-state-20260921-01/run.json'
        evidence=json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_SKILL_ANIMATIONS_COMPLETED')
        rounds=evidence['socket_skill_rounds']
        self.assertEqual(len(rounds),2)
        for index,round_ in enumerate(rounds):
            before=round_['grant_entry']['control_state']
            after=round_['grant_return']['control_state']
            command=round_['command']['control_state']
            self.assertEqual((before['panel'],before['counter']),(0,index))
            self.assertEqual(before['waiting'],index)
            self.assertEqual((after['waiting'],after['first_grant'],after['second_grant']),(0,1,0))
            self.assertEqual((command['waiting'],command['first_grant'],command['second_grant']),(1,0,0))
            self.assertEqual(command['counter'],index)
        # Retain this limitation: an explicit-target call is not normal targeting.
        self.assertEqual(rounds[0]['selection']['target_counts_hex'],'0101')
        self.assertEqual(rounds[1]['selection']['target_counts_hex'],'0000')
        self.assertEqual(rounds[1]['selection']['target_masks_hex'],'0000000000000000')

    def test_live_two_skill_rounds_require_new_grant_and_accumulate_cost(self):
        root=Path(__file__).resolve().parents[2]/'artifacts/runs'
        run=root/'native-player-skill-two-rounds-20260921-01'
        evidence=json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_SKILL_ANIMATIONS_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        rounds=evidence['socket_skill_rounds'];batches=evidence['animation_batch_completions']
        self.assertEqual(len(rounds),2)
        self.assertEqual(len(evidence['socket_skill_commands']),2)
        self.assertEqual(len(batches),4)
        for number,round_ in enumerate(rounds,1):
            self.assertEqual(round_['round'],number)
            self.assertLess(round_['grant_entry']['sequence'],round_['grant_return']['sequence'])
            self.assertLess(round_['grant_return']['sequence'],round_['selection']['sequence'])
            self.assertLess(round_['selection']['sequence'],round_['command']['sequence'])
            values=round_['vitals']
            self.assertEqual(len(values),3)
            self.assertEqual(struct.unpack_from('<I',bytes.fromhex(values[1]['actor_vitals_hex']))[0],150-54*number)
            self.assertEqual(struct.unpack('<4I',bytes.fromhex(values[2]['actor_vitals_hex'])),
                             (100-12*number,50-8*number,120,80))
        self.assertLess(batches[1]['sequence'],rounds[1]['grant_entry']['sequence'])
        for batch in batches:
            self.assertEqual((batch['expected'],batch['completed']),(1,1))
            self.assertFalse(batch['timeout_fallback'])
        self.assertLess(batches[-1]['sequence'],evidence['animation_finalization_return']['sequence'])
        log=(run/'diagnostic-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_NEXT_ROUND_GRANTED'),1)
        self.assertNotIn('accepted=false',log)

    def test_live_skill_and_retaliation_animations_finish_without_timeout(self):
        root = Path(__file__).resolve().parents[2]/'artifacts/runs'
        run = root/'native-player-skill-animation-20260921-01'
        evidence = json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_SKILL_ANIMATIONS_COMPLETED')
        self.assertIsNone(evidence.get('error'))
        self.assertEqual(evidence['skill_animation_definition_hex'],'0100')
        batches=evidence['animation_batch_completions']
        self.assertEqual(len(batches),2)
        for batch in batches:
            self.assertEqual((batch['expected'],batch['completed']),(1,1))
            self.assertFalse(batch['timeout_fallback'])
            self.assertLess(batch['elapsed_ms'],10000)
        vitals=evidence['socket_skill_settlement']
        self.assertEqual(len(vitals),3)
        self.assertLess(vitals[1]['sequence'],batches[0]['sequence'])
        self.assertLess(batches[0]['sequence'],vitals[2]['sequence'])
        self.assertLess(vitals[2]['sequence'],batches[1]['sequence'])
        self.assertLess(batches[1]['sequence'],evidence['animation_finalization_return']['sequence'])
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(vitals[-1]['actor_vitals_hex'])),(88,42,120,80))
        settings=json.loads((run/'diagnostic-server-config.json').read_text(encoding='utf-8'))
        self.assertTrue(settings['development']['diagnostic_battle_skill_settlement'])
        self.assertTrue(settings['development']['diagnostic_battle_animations'])

    def test_live_isolated_skill_mp_damage_and_retaliation_reach_client(self):
        root = Path(__file__).resolve().parents[2]/'artifacts/runs'
        failed = json.loads((root/'native-player-skill-settlement-20260921-01/run.json').read_text(encoding='utf-8'))
        self.assertEqual(failed['result'],'HARD_TIMEOUT')
        self.assertEqual(len(failed['socket_skill_settlement']),2)
        run = root/'native-player-skill-settlement-20260921-02'
        evidence = json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_SKILL_VITALS_SETTLED')
        self.assertIsNone(evidence.get('error'))
        records = evidence['socket_skill_settlement']
        self.assertEqual(len(records),3)
        for record,(kind,target,current,maximum) in zip(records,((1,0,42,80),(0,14,96,150),(0,0,88,120))):
            logical = bytes.fromhex(record['logical_hex'])
            self.assertEqual(len(logical),17)
            self.assertEqual(logical[:3],bytes((0x86,kind,target)))
            self.assertEqual(struct.unpack_from('<II',logical,5),(maximum,current))
            values = struct.unpack('<4I',bytes.fromhex(record['actor_vitals_hex']))
            self.assertEqual((values[kind],values[kind+2]),(current,maximum))
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(records[-1]['actor_vitals_hex'])),(88,42,120,80))
        settings = json.loads((run/'diagnostic-server-config.json').read_text(encoding='utf-8'))
        self.assertTrue(settings['development']['diagnostic_battle_skill_settlement'])
        self.assertFalse(settings['development']['diagnostic_battle_animations'])
        self.assertEqual((run/'hotbar-fixture-input.bin').read_bytes(),(run/'hotbar-fixture-final.bin').read_bytes())

    def test_live_skill_command_is_accepted_by_cpp_structural_decoder(self):
        from tools.strike_lab.current_offline_vitals_live import action_call_page
        root = Path(__file__).resolve().parents[2]
        evidence = json.loads((root/'artifacts/runs/native-player-skill-command-20260921-01/run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_SKILL_COMMAND_QUEUED')
        self.assertIsNone(evidence.get('error'))
        record = evidence['socket_skill_command_return']
        raw = bytes.fromhex(record['queued_logical_hex'])
        self.assertEqual(len(raw),17)
        self.assertEqual(record['queued_length'],17)
        self.assertEqual(raw[:4],bytes((0x35,0,3,0)))
        self.assertEqual(struct.unpack_from('<HH',raw,5),(0,1))
        self.assertEqual(raw[13:],bytes((1,0,0,0)))
        self.assertEqual(record['controls_hex'],'010000000000000000000000')
        decoded = subprocess.check_output([str(root/'build/tests/Release/recovered-skill-command.exe'),
                                          '--decode-sequence',raw.hex()],text=True,timeout=10)
        self.assertEqual(decoded.strip(),f'0 0 0 {raw[4]} 0 1 0 1')
        page = evidence['socket_skill_command_probe']['page']
        expected, trap = action_call_page(page['address'],evidence['socket_battle_entry']['battle'],skill=True)
        self.assertEqual(bytes.fromhex(page['hex']),expected)
        self.assertEqual(page['return_trap'],page['address']+trap)

    def test_live_original_selection_completes_mode_change_and_target_setup(self):
        from tools.strike_lab.current_offline_vitals_live import skill_select_call_page
        root = Path(__file__).resolve().parents[2]/'artifacts/runs'
        evidence = json.loads((root/'native-player-skill-select-20260921-01/run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_SKILL_SELECTED')
        self.assertIsNone(evidence.get('error'))
        before = evidence['socket_skill_prerequisites']
        self.assertEqual(before['selected_index'],-1)
        self.assertEqual(before['hotbar']['battle_action_mode'],1)
        after = evidence['socket_skill_select_return']
        self.assertEqual((after['selected_index'],after['battle_action_mode']),(0,3))
        self.assertEqual(struct.unpack('<II',bytes.fromhex(after['target_masks_hex'])),(1,1))
        self.assertEqual(struct.unpack('<4I',bytes.fromhex(after['target_setup_hex'])),(1,0,3,1))
        self.assertEqual(after['target_counts_hex'],'0101')
        page = evidence['socket_skill_select_probe']['page']
        raw, trap = skill_select_call_page(page['address'],evidence['socket_battle_entry']['battle'])
        self.assertEqual(bytes.fromhex(page['hex']),raw)
        self.assertEqual(page['return_trap'],page['address']+trap)
        self.assertNotIn('socket_action_return',evidence)

    def test_isolated_fixture_cleanup_and_existing_file_preservation(self):
        from tools.strike_lab.current_skill_hotbar_fixture import isolated_hotbar, fixture_bytes
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            client = root/'capture_work'/'host-test'/'client'
            client.mkdir(parents=True)
            run = root/'run'
            run.mkdir()
            path = client/'Save'/'CodexTrial.hky'
            with self.assertRaisesRegex(RuntimeError, 'exercise cleanup'):
                with isolated_hotbar(client, run, True):
                    self.assertEqual(path.read_bytes(),fixture_bytes())
                    self.assertEqual(len(fixture_bytes()),1068)
                    raise RuntimeError('exercise cleanup')
            self.assertFalse(path.exists())
            self.assertEqual((run/'hotbar-fixture-final.bin').read_bytes(),fixture_bytes())
            path.write_bytes(b'player data')
            with self.assertRaises(FileExistsError):
                with isolated_hotbar(client,run,True):
                    self.fail('Must not overwrite player data')
            self.assertEqual(path.read_bytes(),b'player data')

    def test_revival_fixture_changes_only_skill_identity_and_cleans_up(self):
        from tools.strike_lab.current_skill_hotbar_fixture import isolated_hotbar, fixture_bytes
        original = fixture_bytes()
        revival = fixture_bytes(revival=True)
        expected = bytearray(original)
        struct.pack_into('<HHH', expected, 60, 2, 3, 8)
        self.assertEqual(revival, bytes(expected))
        for invalid in (1, None, 'revival'):
            with self.assertRaises(ValueError):
                fixture_bytes(revival=invalid)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            client = root/'capture_work'/'host-test'/'client'
            client.mkdir(parents=True)
            run = root/'run'
            run.mkdir()
            path = client/'Save'/'CodexTrial.hky'
            with isolated_hotbar(client, run, True, revival=True):
                self.assertEqual(path.read_bytes(), revival)
            self.assertFalse(path.exists())
            self.assertEqual((run/'hotbar-fixture-final.bin').read_bytes(), revival)

    def test_live_native_loader_populates_only_requested_primary_slot(self):
        root = Path(__file__).resolve().parents[2]/'artifacts/runs'
        before = json.loads((root/'native-player-hotbar-loader-20260921-01/run.json').read_text(encoding='utf-8'))
        after = json.loads((root/'native-player-hotbar-loader-20260921-02/run.json').read_text(encoding='utf-8'))
        for evidence in (before,after):
            self.assertEqual(evidence['result'],'NATIVE_SOCKET_PARTICIPANTS_GRANTED')
            self.assertEqual(evidence['socket_skill_prerequisites']['selected_index'],-1)
        self.assertFalse(before['native_hotbar_load']['opened'])
        self.assertTrue(after['native_hotbar_load']['opened'])
        hotbar = after['socket_skill_prerequisites']['hotbar']
        self.assertEqual(bytes.fromhex(hotbar['primary_records_hex']),struct.pack('<HHH',2,0,1)+b'\xff'*54)
        self.assertEqual((hotbar['mode'],hotbar['source_row']),(1,0))

    def test_native_event_327_arms_binding_before_unqualified_ui_call(self):
        image = pinned_image()
        ui = 0x6800000
        for event in (0, 0x326, 0x327, 0x328, 0xffff):
            for prior in (0, 1):
                n = NativeRun(image)
                n.put32(ui + 0x232eac, prior)
                n.put(PACKET_PAGE, struct.pack('<H', event))
                n.put32(SP + 4, PACKET_PAGE)
                n.registers(ecx=ui)
                n.run(0x84e00, ((0x84e00, 0x84e1e),), {0x84e1e})
                self.assertEqual(n.get32(ui + 0x232eac), 1 if event == 0x327 else prior)

    def test_conditional_native_writer_preserves_other_hotbar_records(self):
        image = pinned_image()
        ui, source = 0x6800000, 0x6900000
        for row in range(16):
            for slot in range(10):
                for armed in (0, 1):
                    n = NativeRun(image)
                    n.put32(ui + 0x86888, source)
                    n.put(source + 0xcf, bytes((row,)))
                    n.put32(ui + 0x232eac, armed)
                    initial = b'\xff' * 960
                    n.put(ui + 0xa3d54, initial)
                    # Independent post-refresh window: EDI is learned-entry index.
                    kind, identifier = slot % 4, slot + 1
                    n.put32(SP + 0x1c, identifier)
                    n.registers(esi=ui, edi=slot, ebp=kind)
                    n.run(0xaa92a, ((0xaa92a, 0xaa99f),), {0xaa99f})
                    expected = bytearray(initial)
                    if armed:
                        struct.pack_into('<HHH', expected, row * 60 + slot * 6,
                                         2, kind, identifier)
                    self.assertEqual(bytes(n.vm.mem_read(ui + 0xa3d54, 960)), bytes(expected))
                    self.assertEqual(n.get32(ui + 0x232eac), 0)
                    allowed = {ui + 0x232eac}
                    if armed:
                        at = ui + 0xa3d54 + row * 60 + slot * 6
                        allowed.update((at, at + 2, at + 4))
                    self.assertTrue(all(address in allowed for _, address, _, _ in n.writes))

    def test_native_hotbar_file_format_strings(self):
        image = pinned_image()
        for offset, expected in ((0x185670, b'%s\\%s.hky'), (0x18567c, b'Save'),
                                 (0x18234c, b'wb'), (0x182350, b'rb')):
            self.assertEqual(image[offset:].split(b'\0', 1)[0], expected)


if __name__ == '__main__':
    unittest.main()
