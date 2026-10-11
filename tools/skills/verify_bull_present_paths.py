"""Execute pinned original432A20 for both presentation-mode branches."""
import hashlib
import json
import struct
import unicorn as uc
from unicorn import x86_const as x
from tools.skills.native_clone.clone_evidence import IMAGE, ROOT


def main():
    image = IMAGE.read_bytes()
    assert hashlib.sha256(image).hexdigest() == '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
    cases = []
    for mode in (0, 1):
        vm = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_32)
        vm.mem_map(0x400000, (len(image)+4095)&~4095)
        vm.mem_write(0x400000, image)
        base = 0x10000000
        vm.mem_map(base, 0x20000)
        renderer, screen, front, back, table, blit, stop, stack = [base+v for v in (0,0xd000,0xe000,0xe100,0xe200,0xe300,0xe400,0x1f000)]
        def put(address, value): vm.mem_write(address, struct.pack('<I', value))
        for address, value in ((renderer+0x50,mode),(renderer+0xc0e0,1),
                (renderer+0x9c,screen),(screen+0xc,front),(screen+0x10,back),
                (front+0x80,front+0x100),(back+0x80,back+0x100),
                (front+0x100,table),(table+0x14,blit),(stack,stop)):
            put(address,value)
        events = []
        def hook(vm, address, size, unused):
            pop = None
            if address == 0x403900: pop = 0
            elif address == 0x53ca50:
                assert vm.reg_read(x.UC_X86_REG_ECX) == screen
                events.append('screen_present'); pop = 12
            elif address == blit:
                args = struct.unpack('<6I',vm.mem_read(vm.reg_read(x.UC_X86_REG_ESP)+4,24))
                assert args == (front+0x100,0,back+0x100,0,0x1000000,0)
                events.append('direct_COM_Blt'); pop = 24
            if pop is not None:
                sp = vm.reg_read(x.UC_X86_REG_ESP)
                vm.reg_write(x.UC_X86_REG_EIP,struct.unpack('<I',vm.mem_read(sp,4))[0])
                vm.reg_write(x.UC_X86_REG_ESP,sp+4+pop)
        vm.hook_add(uc.UC_HOOK_CODE,hook)
        vm.reg_write(x.UC_X86_REG_ECX,renderer)
        vm.reg_write(x.UC_X86_REG_ESP,stack)
        vm.emu_start(0x432a20,stop,count=1000,timeout=1000000)
        assert vm.reg_read(x.UC_X86_REG_EIP)==stop and vm.reg_read(x.UC_X86_REG_ESP)==stack+4
        assert events == (['screen_present'] if mode==0 else ['direct_COM_Blt'])
        cases.append({'renderer_mode':mode,'events':events,'returns_normally':True})
    report={'status':'PASS','cases':cases,'scope':'Original presenter instructions; final OS/COM calls are sinks',
        'finding':'mode1 bypasses53CA50;432A20 wrapper covers both branches'}
    (ROOT/'artifacts/custom-skills/thousand-bulls/native-present-paths-20261001.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
