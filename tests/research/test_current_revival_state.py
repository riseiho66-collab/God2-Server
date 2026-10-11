"""Original secondary89 consumer prefix; no full animation/HP revival claim."""
import unittest
from pathlib import Path
import subprocess

from tools.strike_lab.current_battle_entry import NativeRun, BATTLE, ROOT_OBJECT, SP

ENTITY = ROOT_OBJECT
RANGES = ((0x128dec,0x128e12),(0x1267c0,0x12681c))


class RevivalStateTests(unittest.TestCase):
    def test_first_revival_candidate_reaches_native_ally_effect_store(self):
        from tools.strike_lab.current_skill_effect_amount import consume_skill_amount
        executable=Path(__file__).resolve().parents[2]/'build/tests/Release/battle-revival.exe'
        emitted=bytes.fromhex(subprocess.check_output([str(executable),'--effect'],text=True,timeout=10))
        self.assertEqual(emitted,bytes.fromhex('83030000000200000001000803001b'))
        for target in range(1,14):
            raw = bytearray(emitted)
            raw[5:7] = (1 << target).to_bytes(2,'little')
            n = consume_skill_amount(3,8,1,target_position=target,logical_record=bytes(raw))
            self.assertEqual(n.stop,0x12b621)
            for pc in (0x12c537,0x12c7d2,0x12a95f,0x12c845,0x12b619):
                self.assertIn(pc,n.visits)

    def prepare(self, side, slot, state=89):
        n = NativeRun()
        n.put(BATTLE, bytes(4096))
        n.put(ENTITY, b'\xa5' * 4096)
        n.put(ENTITY+0x234, bytes(((side << 7) | slot,)))
        n.put(ENTITY+0x1de, b'\x01')
        n.put32(ENTITY+0xde8, 0)
        n.put32(ENTITY+0xdb8, 0xdeadbeef)
        n.put32(BATTLE+0x2f4, 0x80000000)
        n.put32(BATTLE+0x2f8, 0x40000000)
        n.registers(esi=BATTLE, ebp=ENTITY, ebx=state)
        return n

    def test_original_caller_reintroduces_all28_positions_before_renderer(self):
        for side in (0,1):
            for slot in range(14):
                n = self.prepare(side,slot)
                n.run(0x128dec,RANGES,{0x129870})
                self.assertEqual(n.stop,0x129870)
                self.assertIn(0x128df6,n.visits)  # actual CALL1267C0, not substituted.
                self.assertIn(0x126817,n.visits)
                expected = [0x80000000,0x40000000]
                expected[side] |= 1 << slot
                self.assertEqual([n.get32(BATTLE+0x2f4+i*4) for i in range(2)],expected)
                self.assertEqual(bytes(n.vm.mem_read(ENTITY+0x1de,1)),b'\x00')
                self.assertEqual(n.get32(ENTITY+0xdb8),0x10000000)
                self.assertEqual(n.get32(ENTITY+0xde8),0)
                nonstack = [(r,a,s,v) for r,a,s,v in n.writes if not SP-128 <= a < SP+128]
                self.assertEqual(nonstack,[(0x1267e5,ENTITY+0x1de,1,0),
                    (0x126809,BATTLE+0x2f4+side*4,4,expected[side]),
                    (0x12680d,ENTITY+0xdb8,4,0x10000000)])

    def test_non89_uses_general_consumer_without_revival_mutation(self):
        for state in (0,9,88,90):
            n = self.prepare(0,0,state)
            n.put32(SP+0x18,state)
            n.run(0x128dec,RANGES,{0x126430,0x129870})
            self.assertEqual(n.stop,0x126430)
            self.assertNotIn(0x1267c0,n.visits)
            self.assertEqual(n.get32(BATTLE+0x2f4),0x80000000)
            self.assertEqual(n.get32(ENTITY+0xdb8),0xdeadbeef)


if __name__ == '__main__':
    unittest.main()
