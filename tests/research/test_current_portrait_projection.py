"""Native selection vs world-HUD portrait layers; render calls observed, not pixels."""
import hashlib
import struct
import unittest
import test_current_route_advertisement as r
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *

class PortraitTests(unittest.TestCase):
    vm=r.CurrentRouteAdvertisementTests.vm
    call=r.CurrentRouteAdvertisementTests.call
    run_to=r.CurrentRouteAdvertisementTests.run_to
    @classmethod
    def setUpClass(cls):
        cls.image=(r.ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        assert hashlib.sha256(cls.image).hexdigest()==r.IMAGE_SHA

    def render(self,sex,style,color,face,ornament,world):
        vm=self.vm(); ui=0x4000000
        vm.mem_map(ui,0x240000)
        vm.mem_write(ui+0x232e50,struct.pack('<H',7))
        vm.mem_write(ui+0x178cd0,struct.pack('<H',7))
        # C38..39 packs face in bits4..9 and ornament in bits10..15.
        packed=sex|(face<<4)|(ornament<<10)
        profile=bytes((style|(color<<5),0))+packed.to_bytes(2,'little')
        layers=[];variants=[]
        def observe(uc,pc,size,data):
            clean={0x5068c0:16,0x507150:20,0x507370:12,0x506bb0:16}.get(pc)
            if clean is None:return
            sp=uc.reg_read(UC_X86_REG_ESP)
            values=struct.unpack('<'+'I'*(1+clean//4),uc.mem_read(sp,4+clean))
            if pc==0x507150:layers.append((values[2]&65535,values[4]&65535))
            if pc==0x507370:variants.append(values[3]&65535)
            uc.reg_write(UC_X86_REG_ESP,sp+4+clean);uc.reg_write(UC_X86_REG_EIP,values[0])
        vm.hook_add(UC_HOOK_CODE,observe)
        if world:
            vm.mem_write(r.BODY,bytes((profile[0]&0xe7,))+profile[1:])
            self.call(vm,0xabe80,r.BODY,this=ui)
        else:
            vm.mem_write(r.BODY+0x16,profile[:2])
            vm.mem_write(r.BODY+0x18,packed.to_bytes(2,'little'))
            vm.mem_write(r.BODY+0x1a,bytes((sex,)))
            for reg,value in ((UC_X86_REG_ESP,r.SP),(UC_X86_REG_ESI,ui),(UC_X86_REG_EDI,r.BODY),
                              (UC_X86_REG_EBX,r.OUTPUT),(UC_X86_REG_EBP,ui+0x2808c)):
                vm.reg_write(reg,value)
            self.run_to(vm,0x7fbd,0x8011)
            vm.reg_write(UC_X86_REG_ESP,r.SP)
            vm.reg_write(UC_X86_REG_EBP,ui+0x2808c)
            self.run_to(vm,0x8067,0x810b)
        return layers,variants

    def test_world_layers_match_selection_for_both_sexes_and_all_colors(self):
        for sex in (0,1):
            for color in range(7):
                for style in range(32):
                    face,ornament=style%10,(style+3)%10
                    with self.subTest(sex=sex,color=color,style=style):
                        selected,sv=self.render(sex,style,color,face,ornament,False)
                        hud,hv=self.render(sex,style,color,face,ornament,True)
                        self.assertEqual(hud[:3],[(category+17,index) for category,index in selected])
                        self.assertEqual(hv[1],sv[0]) # first HUD variant clears accessory
                        self.assertEqual(hv[1],color)

if __name__=='__main__':unittest.main()
