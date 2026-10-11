"""Real source resource outputs into original remote component setup, offline."""
import struct
import unittest

from tools.strike_lab.current_world_role_resources import NativeWorldRoleResources
from tools.strike_lab.current_role_doll_resources import BANK as ROM_BANK
from tools.strike_lab.current_indoor_resources import SCRATCH

ACTOR=0x7900000


class RemoteActorResourceTests(unittest.TestCase):
    def test_original_remote_component_setup_uses_source_loaded_handles(self):
        native=NativeWorldRoleResources()
        native.vm.mem_map(ACTOR,0x1000)
        component=ACTOR+0x224
        native.call(0xff370,this=component)
        native.call(0xff3c0,ROM_BANK,this=component)
        for first,second in ((0,0),(2,1),(6,6)):
            block=bytes([1,first<<5,1,second<<5,1,0,0x81,0])
            handles=native.load_components(block)
            self.assertTrue(all(value!=0xffff for value in handles[:4]))
            native.vm.mem_write(SCRATCH+0x5000,struct.pack('<6H',*handles))
            native.vm.mem_write(SCRATCH+0x5100,block)
            native.vm.mem_write(ACTOR+0x250,block)
            native.vm.mem_write(ACTOR+0x60,b'\0\0')
            native.call(0xfc130,SCRATCH+0x5000,ACTOR,0,SCRATCH+0x5100,this=ACTOR)
            stored=tuple(struct.unpack('<H',native.vm.mem_read(component+4+6*i,2))[0] for i in range(4))
            variants=tuple(native.vm.mem_read(component+8+6*i,1)[0] for i in range(4))
            self.assertEqual(stored,handles[:4])
            self.assertEqual(variants,(first,second,0,0))
            self.assertEqual(bytes(native.vm.mem_read(SCRATCH+0x5100,8)),block)
            before=(len(native.opens),len(native.parser_inputs),native.next_slot)
            self.assertEqual(native.load_components(block),handles)
            self.assertEqual((len(native.opens),len(native.parser_inputs),native.next_slot),before)
        self.assertGreater(len(native.parser_inputs),0)


if __name__=='__main__':
    unittest.main()
