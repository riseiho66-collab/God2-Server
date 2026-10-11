"""Execute native result-panel polling with explicit offline state snapshots.

No client process, packet emission, helper substitution or UI actuation.
This does not establish the producers of animation-ready/panel state.
"""
import struct

from tools.strike_lab.current_battle_entry import NativeRun, BATTLE, SP
from unicorn.x86_const import UC_X86_REG_ESP

UI = 0x22000000
RANGES = ((0x1159f8, 0x115a40), (0x12aed0, 0x12aed7),
          (0x85260, 0x852a8))
runtime_mutation_enabled = False


def poll(*, result_received, manager_ready, panel_latch, panel_mode,
         handle, control_flags):
    for value in (result_received, manager_ready, panel_latch, panel_mode):
        if type(value) is not int or not 0 <= value <= 0xffffffff:
            raise ValueError('Expected explicit raw DWORD')
    if type(handle) is not int or not -32768 <= handle <= 32767:
        raise ValueError('Expected signed WORD handle')
    if type(control_flags) is not int or not 0 <= control_flags <= 255:
        raise ValueError('Expected raw control byte')
    n = NativeRun()
    for offset, value in ((0xa9df6bc, result_received),
                          (0x144c18, manager_ready),
                          (0xa9e9c50, panel_latch), (0x20, UI), (0x44, 0)):
        n.put32(BATTLE + offset, value)
    n.put32(UI + 0x23d620, panel_mode)
    for offset in (0x232df0, 0x232df2):
        n.put(UI + offset, struct.pack('<h', handle))
    if handle >= 0:
        n.put(UI + 0xe2988 + handle * 10760, bytes([control_flags]))
    n.registers(esi=BATTLE, ebx=0, edi=1)
    n.run(0x1159f8, RANGES, {0x85070, 0x115a40})
    return {
        'stop_rva': n.stop,
        'stage': n.get32(BATTLE + 0x44),
        'panel_latch': n.get32(BATTLE + 0xa9e9c50),
        'stack_delta': n.vm.reg_read(UC_X86_REG_ESP) - SP,
        'visits': n.visits,
    }


def loop_head(*, stage, manager_ready):
    for value in (stage, manager_ready):
        if type(value) is not int or not 0 <= value <= 0xffffffff:
            raise ValueError('Expected explicit raw DWORD')
    n = NativeRun()
    n.put32(BATTLE + 0x44, stage)
    n.put32(BATTLE + 0x144c18, manager_ready)
    n.registers(esi=BATTLE)
    n.run(0x11583c, ((0x11583c, 0x115855), (0x12aed0, 0x12aed7)),
          {0x115855, 0x115c40})
    return n.stop, n.vm.reg_read(UC_X86_REG_ESP) - SP
