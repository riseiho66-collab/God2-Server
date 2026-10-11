"""Pinned native outcome conversion, not damage rules or full animation proof."""
import struct
import unittest

from tools.strike_lab.current_battle_entry import NativeRun, SP, BATTLE, PACKET_PAGE
from unicorn.x86_const import UC_X86_REG_ESP


class OutcomeMappingTests(unittest.TestCase):
    def test_skill_secondary27_can_replace_latched_death_but28_cannot(self):
        from tools.strike_lab.current_hit_formula import NativeHit, ACTOR, TARGET, CONTEXT
        from tools.strike_lab.recover_combat_rules import read_pinned, IMAGE, IMAGE_SHA256
        n = NativeHit(read_pinned(IMAGE,IMAGE_SHA256))
        self.assertEqual(n.image[0x171610+27], 89)
        n.prepare()
        n.write(ACTOR+0x23b, '<B', 0x80)  # source action index1 -> side1/slot0.
        n.write(TARGET+0x232, '<B', 9)
        n.write(TARGET+0x1eb, '<B', 9)
        n.write(TARGET+0xde8, '<I', 0)
        for wire, expected in ((28,9),(27,89)):
            n.execute(0x12c000,args=(0,0,0,wire,3),registers=dict(ECX=CONTEXT))
            self.assertEqual(n.read(TARGET+0x232,'<B')[0], expected)
            self.assertEqual(n.read(ACTOR+0x225,'<B')[0], expected)
            # This configures a pending skill result; it does not animate or heal.
            self.assertEqual(n.read(TARGET+0x1eb,'<B')[0], 9)
            self.assertEqual(n.read(TARGET+0xde8,'<I')[0], 0)
        self.assertIn(0x12c298, n.trace)

    def test_basic_and_skill_callers_read_different_outcome_offsets(self):
        for action,entry,offset in ((1,0x12c636,12),(3,0x12c865,14)):
            for wire,expected in ((0,9),(28,0)):
                n=NativeRun()
                record=bytearray(15)
                record[0]=0x83;record[1]=action;record[offset]=wire
                n.put(PACKET_PAGE,bytes(record))
                n.put(SP,bytes(64))
                n.registers(esi=PACKET_PAGE+1,ebx=BATTLE)
                n.run(entry,[(0x12c636,0x12c645),(0x12c865,0x12c881),
                             (0x12c000,0x12c0b3)],{0x12c0c0})
                sp=n.vm.reg_read(UC_X86_REG_ESP)
                args=struct.unpack('<5I',n.vm.mem_read(sp+4,20))
                self.assertEqual((args[3]&255,args[4]&255),(expected,action))

    def test_native_converter_distinguishes_zero_from_neutral_index(self):
        for action in (1, 3):
            for wire, expected in ((0, 9), (28, 0)):
                n=NativeRun()
                n.put(SP+4,struct.pack('<5I',1,0,0,wire,action))
                n.registers(ecx=BATTLE)
                n.run(0x12c000,[(0x12c000,0x12c0b3)],{0x12c0c0})
                sp=n.vm.reg_read(UC_X86_REG_ESP)
                args=struct.unpack('<5I',n.vm.mem_read(sp+4,20))
                # Native BYTE arguments retain unspecified upper register bits.
                self.assertEqual(tuple(value & 255 for value in args),(1,0,15,expected,action))
                self.assertIn(0x12c051,n.visits)


if __name__ == '__main__':
    unittest.main()
