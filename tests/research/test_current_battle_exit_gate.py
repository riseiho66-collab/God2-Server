"""Real native helper calls, not injected EAX return values."""
import unittest
import json
import struct
from pathlib import Path
from tools.strike_lab.current_battle_exit_gate import poll, loop_head


class BattleExitGateTests(unittest.TestCase):
    def test_native_post_battle_context_producer_arguments(self):
        from tools.strike_lab.current_battle_entry import NativeRun, SP, NET
        from unicorn.x86_const import UC_X86_REG_ESP
        for supplied in (0,1,0xffff,0x12345678,0xffffffff):
            n=NativeRun()
            n.put32(SP+4,supplied)
            n.registers(ecx=NET)
            n.run(0x157f0,((0x157f0,0x15839),(0x131c10,0x131c2d)),{0x132e0})
            sp=n.vm.reg_read(UC_X86_REG_ESP)
            self.assertEqual(n.get32(sp+4),0x1c)
            self.assertEqual(n.get32(sp+12),4)
            config=struct.unpack_from('<HH',n.image,0x19dfd8)
            self.assertEqual(n.get32(n.get32(sp+8)),(supplied & 0xffff) | (int(config==(4,2))<<16))
            self.assertIn(0x131c10,n.visits)
            self.assertEqual(n.stop,0x132e0)  # Queue/socket not claimed executed.

    def test_live_two_round_snapshot_has_no_result_or_panel_yet(self):
        root=Path(__file__).resolve().parents[2]
        report=json.loads((root/'artifacts/runs/native-socket-exit-state-20260921-01/run.json').read_text())
        self.assertEqual(report['result'],'NATIVE_SOCKET_DIAGNOSTIC_RETALIATION_APPLIED')
        self.assertEqual(len(report['socket_completed_rounds']),2)
        snapshot=report['socket_exit_prerequisites']
        self.assertEqual({k:snapshot[k] for k in ('result_received','manager_ready','panel_latch','stage')},
                         dict(result_received=0,manager_ready=1,panel_latch=0,stage=1))
        self.assertEqual((snapshot['panel_mode'],snapshot['selected_handle'],snapshot['control_flags']),
                         (0,14,19))
        end=report['socket_retaliation_return']
        self.assertEqual((snapshot['sequence'],snapshot['pid'],snapshot['tid']),
                         (end['sequence'],end['pid'],end['tid']))
        state=poll(**{k:snapshot[k] for k in ('result_received','manager_ready','panel_latch','panel_mode','control_flags')},
                   handle=snapshot['selected_handle'])
        self.assertEqual(state['stop_rva'],0x115a40)
        self.assertEqual(state['panel_latch'],0)
        self.assertEqual(loop_head(stage=snapshot['stage'],manager_ready=snapshot['manager_ready'])[0],0x115855)

    def test_panel_poll_modes_handles_and_all_flag_bytes(self):
        for mode in (0, 1, 2, 0xffffffff):
            for handle in (-1, 0, 3):
                for flags in range(256):
                    with self.subTest(mode=mode, handle=handle, flags=flags):
                        r=poll(result_received=1, manager_ready=1, panel_latch=1,
                               panel_mode=mode, handle=handle, control_flags=flags)
                        expected=5 if mode in (0,1) and handle >= 0 and flags & 0x20 else 0
                        self.assertEqual(r['stage'],expected)
                        self.assertEqual(r['stop_rva'],0x115a40)
                        self.assertEqual(r['stack_delta'],0)
                        self.assertIn(0x12aed0,r['visits'])
                        self.assertIn(0x85260,r['visits'])

    def test_unopened_panel_stops_at_real_show_function(self):
        for received in (0,1,2):
            for ready in (0,1,2,0xffffffff):
                r=poll(result_received=received, manager_ready=ready, panel_latch=0,
                       panel_mode=0, handle=0, control_flags=0x20)
                show=received==1 and ready==1
                self.assertEqual(r['stop_rva'],0x85070 if show else 0x115a40)
                self.assertEqual(r['panel_latch'],int(show))
                self.assertEqual(r['stage'],0)
                self.assertEqual(r['stack_delta'],-4 if show else 0)

    def test_preexisting_panel_latch_polls_without_received_or_ready(self):
        r=poll(result_received=0, manager_ready=0, panel_latch=7,
               panel_mode=1, handle=2, control_flags=0x20)
        self.assertEqual(r['stage'],5)
        self.assertNotIn(0x12aed0,r['visits'])
        self.assertIn(0x85260,r['visits'])

    def test_next_loop_requires_stage5_and_nonzero_ready(self):
        for stage in (0,4,5,6):
            for ready in (0,1,2,0xffffffff):
                end,delta=loop_head(stage=stage,manager_ready=ready)
                self.assertEqual(end,0x115c40 if stage==5 and ready else 0x115855)
                self.assertEqual(delta,0)


if __name__ == '__main__':
    unittest.main()
