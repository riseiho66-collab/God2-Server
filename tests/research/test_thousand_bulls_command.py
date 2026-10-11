"""CUSTOM-0059 original mode5 producer oracle, not UI/live acceptance."""
import hashlib
from pathlib import Path
import struct
import unittest
from tools.skills import verify_shunying_command as bridge
from tools.strike_lab.current_skill_identity import decode_definitions

class ThousandBullsCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        bridge.CurrentSkillCommandTests.setUpClass()
        cls.addClassCleanup(bridge.CurrentSkillCommandTests.doClassCleanups)
    def test_native_mode5_whole_side_and_narrow_parser(self):
        root=Path(__file__).resolve().parents[2]
        source=decode_definitions((root.parent/'God2/Data2/Fight/Spg/cbspec2.bin').read_bytes())[0,73]
        self.assertEqual(hashlib.sha256(source.raw).hexdigest(),'2b4f992ef03b483b4dd1f539cdd4b733dacc085412a190d0aa9ee27ed287105f')
        self.assertEqual(source.raw[32:62].split(b'\0')[0].decode('cp950'),'鯨吞亂舞')
        self.assertEqual(struct.unpack_from('<H',source.raw,0x42)[0],100)
        self.assertEqual(source.raw[0x45],5)
        raw=bytearray(source.raw);raw[0]=150;raw[0x44]=7
        test=bridge.NativeSetupCommandTest();test.native_definition=bytes(raw)
        setup=bridge.CurrentSkillTargetSetupTests();setup.image=test.image
        test.native_setup=bridge.original_setup(setup,setup.target_machine(),5)
        self.assertEqual(test.native_setup,(1,1))
        for modes in ((1,0),(0,1)):
            for target in (0,13,14,27):
                wire,_,_,_=test.builder((target,),action=3,skill=True,skill_id=150,skill_kind=0,modes=modes)
                self.assertEqual(len(wire),17)
                self.assertEqual(wire[2],3)
                self.assertEqual(struct.unpack_from('<HH',wire,5),(0x3fff,0) if target<14 else (0,0x3fff))
                self.assertEqual(wire[13:17],b'\x96\0\0\0')
                self.assertIsNotNone(test.decode(wire))
                for bad_id in (126,149,151):
                    bad=bytearray(wire);bad[13]=bad_id
                    self.assertIsNone(test.decode(bytes(bad)))
                bad=bytearray(wire);bad[2]=0x83
                self.assertIsNone(test.decode(bytes(bad)))

if __name__=='__main__':unittest.main()
