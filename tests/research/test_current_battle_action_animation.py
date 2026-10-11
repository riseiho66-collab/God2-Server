"""Bounded native83 execution and retained live diagnostic evidence."""
import json
from pathlib import Path
import struct
import unittest

from tools.strike_lab.current_battle_entry import (
    NativeRun, BATTLE, PACKET_PAGE, SP, native_length,
)
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_ECX


class BattleActionAnimationTests(unittest.TestCase):
    def test_both_rounds_finish_all_four_native_batches(self):
        run = Path(__file__).resolve().parents[2]/'artifacts/runs/native-player-animation-full-rounds-20260921-01'
        evidence = json.loads((run/'run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_ANIMATION_ROUNDS_COMPLETED')
        self.assertEqual(len(evidence['socket_completed_rounds']),2)
        batches = evidence['animation_batch_completions']
        self.assertEqual(len(batches),4)
        for batch in batches:
            self.assertEqual((batch['expected'],batch['completed']),(1,1))
            self.assertFalse(batch['timeout_fallback'])
            self.assertLess(batch['elapsed_ms'],10000)
        self.assertGreater(batches[-1]['sequence'],evidence['socket_completed_rounds'][-1]['socket_retaliation_return']['sequence'])
        self.assertGreater(evidence['animation_finalization_return']['sequence'],batches[-1]['sequence'])
        log = (run/'diagnostic-server.log').read_text(encoding='utf-8')
        self.assertEqual(log.count('DIAGNOSTIC_NEXT_ROUND_GRANTED'),1)
        self.assertNotIn('Recovered world policy or response rejected',log)

    def test_separate_groups_complete_without_native_timeout(self):
        root = Path(__file__).resolve().parents[2]/'artifacts/runs'
        old = json.loads((root/'native-player-animation-completion-20260921-01/run.json').read_text(encoding='utf-8'))
        failed = old['animation_batch_completions'][0]
        self.assertEqual((failed['expected'],failed['completed']),(2,1))
        self.assertTrue(failed['timeout_fallback'])
        self.assertGreater(failed['elapsed_ms'],10000)
        new = json.loads((root/'native-player-animation-completion-20260921-02/run.json').read_text(encoding='utf-8'))
        self.assertEqual(new['result'],'NATIVE_SOCKET_DIAGNOSTIC_RETALIATION_APPLIED')
        batches = new['animation_batch_completions']
        self.assertEqual(len(batches),2)
        for batch in batches:
            self.assertEqual((batch['expected'],batch['completed']),(1,1))
            self.assertFalse(batch['timeout_fallback'])
            self.assertLess(batch['elapsed_ms'],10000)
        self.assertLess(batches[-1]['sequence'],new['socket_completed_rounds'][1]['socket_grant_entry']['sequence'])

    def test_native_different_action_group_defers_next_record(self):
        for group in (0,1):
            n = NativeRun()
            current_group = PACKET_PAGE+0x100
            n.put32(current_group,0)
            n.put32(SP+0x28,current_group)
            n.put(BATTLE+0xa9e9cb3,bytes([group]))
            n.put32(BATTLE+0xa9ea4c4,1)
            n.registers(esi=BATTLE,edi=PACKET_PAGE)
            n.run(0x114389,((0x114389,0x1143c4),),{0x116ae0,0x1143c4})
            self.assertEqual(n.stop,0x116ae0 if group==0 else 0x1143c4)
            self.assertEqual(n.get32(BATTLE+0xa9ea4c4),1 if group==0 else 0)

    def test_native_completion_has_ten_second_fallback(self):
        for expected,completed,elapsed,stop in ((2,1,10000,0x1294ce),
                                               (2,1,10001,0x1294b6),
                                               (2,2,1,0x1294b6),
                                               (0,0,1,0x1294b6)):
            n = NativeRun()
            manager = BATTLE+0x144938
            n.put32(manager+0xa7fbc64,expected)
            n.put32(manager+0xa7fbc68,completed)
            n.registers(edi=manager,eax=elapsed,esi=0)
            n.run(0x129499,((0x129499,0x1294b6),),{0x1294b6,0x1294ce})
            self.assertEqual(n.stop,stop)

    def test_corrected_animation_receipt_allows_two_exchanges(self):
        root = Path(__file__).resolve().parents[2]
        evidence = json.loads((root/'artifacts/runs/native-player-animation-20260921-08/run.json').read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'NATIVE_SOCKET_DIAGNOSTIC_RETALIATION_APPLIED')
        rounds = evidence['socket_completed_rounds']
        self.assertEqual(len(rounds),2)
        for turn,expected in zip(rounds,((132,88),(114,76))):
            values = [int.from_bytes(bytes.fromhex(turn[key]['enemy_vitals_hex'])[:4],'little')
                      for key in ('socket_damage_return','socket_retaliation_return')]
            self.assertEqual(tuple(values),expected)

    def test_native_stage_nine_uses_general_update_not_basic_action(self):
        for stage, destination in ((9,0x1292e9),(17,0x1290cd)):
            n = NativeRun()
            actor = PACKET_PAGE+0x1000
            n.map(actor,0x1000)
            n.put(actor+0x1ea,bytes([stage]))
            n.registers(esi=actor)
            n.run(0x1290a8,((0x1290a8,0x1290cd),),{destination})
            self.assertEqual(n.stop,destination)

    def test_native_bulk_waits_for_action_batch_boundary(self):
        for pending in (0,1):
            n = NativeRun()
            flag = PACKET_PAGE+0x100
            n.put32(flag,pending)
            n.put32(SP+0x2c,flag)
            n.put32(BATTLE+0xa9ea4c4,1)
            n.registers(esi=BATTLE,edi=PACKET_PAGE)
            destination = 0x1145c0 if pending else 0x118a90
            n.run(0x114538,((0x114538,0x114555),),{destination})
            self.assertEqual(n.stop,destination)
            self.assertEqual(n.get32(BATTLE+0xa9ea4c4),0 if pending else 1)

    def test_live_actions_advance_without_second_round_acceptance(self):
        root = Path(__file__).resolve().parents[2]
        run = root/'artifacts/runs/native-player-animation-20260921-06/run.json'
        evidence = json.loads(run.read_text(encoding='utf-8'))
        self.assertEqual(evidence['result'],'HARD_TIMEOUT')
        self.assertNotIn('timeout_battle_snapshot_error',evidence)
        rounds = evidence['socket_completed_rounds']
        self.assertEqual(len(rounds),1)  # HP exchange, not completed animation.
        initial = rounds[0]['socket_retaliation_return']['actor_animation_states']
        self.assertEqual([bytes.fromhex(x)[3] for x in initial],[0x11,0x11])
        final = evidence['timeout_battle_state']
        self.assertEqual([x['slot'] for x in final['actors']],[0,14])
        self.assertEqual([bytes.fromhex(x['animation_hex'])[3] for x in final['actors']],[9,9])
        self.assertEqual(final['control_sent'],1)
        self.assertEqual(final['manager_event'],0)
        self.assertEqual(final['result_received'],0)

    def test_basic_result_formats_signed_hp_delta(self):
        for value in (0,18,0x7fff,0x8000,0xffee,0xffff):
            n = NativeRun()
            actor = PACKET_PAGE+0x1000
            n.map(actor,0x1000)
            n.put32(SP+0x60,value)
            n.put32(SP+0x64,0)
            n.put32(SP+0x68,0)
            n.registers(eax=1,ebp=actor)
            n.run(0x12b3c2,((0x12b3c2,0x12b4a1),),{0x147af7})
            sp=n.vm.reg_read(UC_X86_REG_ESP)
            self.assertEqual(n.get32(sp+8),0x59d968)
            self.assertEqual(bytes(n.vm.mem_read(0x59d968,7)),b'HP %+d\0')
            expected=value if value<0x8000 else value-0x10000
            self.assertEqual(n.get32(sp+12),expected & 0xffffffff)
            self.assertEqual(bytes(n.vm.mem_read(actor+0x286,2)),struct.pack('<H',value))

    def route(self, source, masks, *, manager=False, setup=False, result_word=0):
        n = NativeRun()
        record = bytearray(15)
        record[0:3] = bytes([0x83, 1, source])
        struct.pack_into('<HH', record, 5, *masks)
        struct.pack_into('<H', record, 9, result_word)
        n.put(PACKET_PAGE, bytes(record))
        n.put32(SP + 4, PACKET_PAGE)
        # Explicit existing-batch precondition. Initialization/render cleanup
        # is not bypassed in a live client or claimed executed in this test.
        n.put32(BATTLE + 0xa9df6b8, 1)
        n.put32(BATTLE + 0xa9e9c74, 0)
        n.put(BATTLE + 0x51, b'\x00')
        if manager:
            for position in range(28):
                actor = PACKET_PAGE + 0x2000 + position*0x1000
                n.put(actor, bytes(0x1000))
                n.put(actor+0x1a, struct.pack('<H',position+100))
                n.put(actor+0x235,b'\x70')
                n.put(actor+0x277,b'\x0b')
                n.put32(BATTLE+0x144938+0x38+24*position,actor)
        n.registers(ecx=BATTLE)
        ranges = [(0x116ae0,0x116b02),(0x116bb1,0x116bf4),
                         (0x116c0f,0x116cb2),(0x117152,0x117188),
                         (0x11e5e0,0x11e62b),(0x1169f0,0x116a7c)]
        if manager:
            ranges += [(0x12c520,0x12c636 if setup else 0x12c612),(0x11e6e0,0x11e770)]
        if setup:
            ranges += [(0x12a8d0,0x12a9cf)]
        n.run(0x116ae0, ranges,
              {0x12b060 if setup else 0x12a8d0 if manager else 0x12c520,0x116bf4,0x11719a})
        return n

    def test_original_action_setup_writes_and_result_arguments(self):
        for source,target in ((0,14),(14,0),(17,3)):
            for word in (0,18,0x7fff,0x8000,0xffff):
                masks = [0,0]
                masks[target//14] = 1 << (target%14)
                n = self.route(source,masks,manager=True,setup=True,result_word=word)
                self.assertEqual(n.stop,0x12b060)
                actor = PACKET_PAGE+0x2000+source*0x1000
                victim = PACKET_PAGE+0x2000+target*0x1000
                self.assertEqual(n.vm.mem_read(actor+0x1e9,2),b'\x01\x11')
                self.assertEqual(n.vm.mem_read(actor+0x233,1),b'\x00')
                self.assertEqual(n.vm.mem_read(actor+0x235,1)[0],0x70 | (target//14)<<7 | target%14)
                self.assertEqual(n.vm.mem_read(actor+0x277,1)[0],11)
                self.assertEqual(n.vm.mem_read(victim+0x277,1)[0],12)
                sp = n.vm.reg_read(UC_X86_REG_ESP)
                args = struct.unpack('<8I',n.vm.mem_read(sp+4,32))
                self.assertEqual(tuple(v&255 for v in args[:4]),
                                 (source//14,source%14,target//14,target%14))
                self.assertEqual(args[4]&65535,word)
                self.assertEqual(args[5],0)
                self.assertEqual(args[6]&255,0)
                self.assertEqual(args[7],0x22)

    def test_real_manager_lookup_reaches_action_setup(self):
        for source,target in ((0,14),(14,0),(17,3)):
            masks = [0,0]
            masks[target//14] = 1 << (target%14)
            n = self.route(source,masks,manager=True)
            self.assertEqual(n.stop,0x12a8d0)
            sp = n.vm.reg_read(UC_X86_REG_ESP)
            args = struct.unpack('<7I',n.vm.mem_read(sp+4,28))
            self.assertEqual(tuple(x&255 for x in args),
                             (1,source//14,source%14,target//14,target%14,0,0))
            self.assertIn(0x12c520,n.visits)
            self.assertIn(0x11e6e0,n.visits)

    def test_basic_action_for_all_source_positions_to_both_sides(self):
        self.assertEqual(native_length(0x83), 15)
        self.assertEqual(native_length(0x84), 15)
        for source in range(28):
            for target in (0,13,14,27):
                masks = [0,0]
                masks[target//14] = 1 << (target%14)
                n = self.route(source, masks)
                self.assertEqual(n.stop,0x12c520)
                sp = n.vm.reg_read(UC_X86_REG_ESP)
                args = struct.unpack('<5I',n.vm.mem_read(sp+4,20))
                self.assertEqual(args[0],PACKET_PAGE+1)
                self.assertEqual(tuple(v & 255 for v in args[1:]),
                                 (source//14,source%14,target//14,target%14))
                self.assertEqual(n.vm.reg_read(UC_X86_REG_ECX),BATTLE+0x144938)
                self.assertIn(0x11e5e0,n.visits)
                self.assertIn(0x1169f0,n.visits)

    def test_no_target_falls_back_to_source_and_multimask_uses_first_bit(self):
        for masks, expected in (((0,0),(1,3)),((8,1),(0,3)),((0,0x2001),(1,0))):
            n = self.route(17,masks)
            sp = n.vm.reg_read(UC_X86_REG_ESP)
            self.assertEqual(tuple(n.get32(sp+x)&255 for x in (16,20)),expected)

    def test_out_of_range_source_stops_before_manager(self):
        for source in (28,29,255):
            n = self.route(source,(1,0))
            self.assertEqual(n.stop,0x116bf4)  # Stop before native diagnostic logger.
            self.assertNotIn(0x117183,n.visits)


if __name__ == '__main__':
    unittest.main()
