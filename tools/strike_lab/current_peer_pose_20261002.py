"""Execute captured native77 remote consumer; renderer callback is isolated."""
import hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX
ROOT=Path(__file__).resolve().parents[2]
SHA='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
def prove():
    image=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    assert hashlib.sha256(image).hexdigest()==SHA
    vm=Uc(UC_ARCH_X86,UC_MODE_32)
    vm.mem_map(0x400000,(len(image)+4095)&~4095);vm.mem_write(0x400000,image)
    pool,stack,record,stop=0x10000000,0x30000000,0x31000000,0x32000000
    vm.mem_map(pool,0x14000)
    for page in (stack,record,stop):vm.mem_map(page,4096)
    callbacks=[]
    def hook(v,address,size,unused):
        if address==0x4fd160:
            esp=v.reg_read(UC_X86_REG_ESP)
            callbacks.append(struct.unpack('<I',v.mem_read(esp+4,4))[0])
            v.reg_write(UC_X86_REG_EIP,struct.unpack('<I',v.mem_read(esp,4))[0])
            v.reg_write(UC_X86_REG_ESP,esp+8)
        elif address==stop:v.emu_stop()
    vm.hook_add(UC_HOOK_CODE,hook)
    rows=[]
    # First/last pool entry qualify the actual unmodified identity lookup too.
    for slot in (0,127):
        for mode in (1,2,3):
            for direction in range(8):
                vm.mem_write(pool,bytes(0x14000))
                vm.mem_write(pool+8,struct.pack('<I',1))
                for i in range(128):vm.mem_write(pool+0x18+i*0x268,b'\xff'*4)
                actor=pool+0x18+slot*0x268
                vm.mem_write(actor,struct.pack('<I',4095))
                vm.mem_write(actor+0x3e,b'\xff\xff')
                vm.mem_write(record,struct.pack('<HBBBB',4095,0,(mode<<3)|direction,0,0))
                vm.mem_write(stack+0x800,struct.pack('<II',stop,record))
                vm.reg_write(UC_X86_REG_ECX,pool);vm.reg_write(UC_X86_REG_ESP,stack+0x800)
                callbacks.clear();vm.emu_start(0x4fb980,stop,count=5000)
                animation=struct.unpack('<H',vm.mem_read(actor+0x38,2))[0]
                assert animation==15+mode
                assert struct.unpack('<H',vm.mem_read(actor+0x3a,2))[0]==direction
                assert vm.mem_read(actor+0x79,1)==bytes([mode])
                assert callbacks==[actor]
                rows.append({'slot':slot,'mode':mode,'direction':direction,'animation':animation})
    lifecycle=[]
    world=0x33000000;vm.mem_map(world,4096)
    complete=False;refresh=[]
    def lifecycle_hook(v,address,size,unused):
        if address in (0x504080,0x502210):
            esp=v.reg_read(UC_X86_REG_ESP)
            if address==0x504080:v.reg_write(UC_X86_REG_EAX,int(complete))
            else:refresh.append(v.reg_read(UC_X86_REG_ECX))
            v.reg_write(UC_X86_REG_EIP,struct.unpack('<I',v.mem_read(esp,4))[0])
            v.reg_write(UC_X86_REG_ESP,esp+(8 if address==0x502210 else 4))
    vm.hook_add(UC_HOOK_CODE,lifecycle_hook)
    for mode in (1,2,3):
        for complete in (False,True):
            vm.mem_write(world+0x30,struct.pack('<I',15+mode))
            vm.mem_write(stack+0x800,struct.pack('<I',stop))
            vm.reg_write(UC_X86_REG_ECX,world);vm.reg_write(UC_X86_REG_ESP,stack+0x800)
            refresh.clear();vm.emu_start(0x502570,stop,count=1000)
            state=struct.unpack('<I',vm.mem_read(world+0x30,4))[0]
            ended=mode==3 and complete
            assert state==(0 if ended else 15+mode)
            assert refresh==([world] if ended else [])
            lifecycle.append({'mode':mode,'act_completed':complete,'state':state,'refreshes':len(refresh)})
    return {'image_sha256':SHA,'native_consumer':'004FB980','native_lookup':'004FC960',
            'native_lifecycle':'00502570; ACT completion and renderer callbacks isolated',
            'lifecycle_cases':lifecycle,'lifecycle_passed':len(lifecycle),
            'renderer_adapter':'004FD160 recorded only; no rendered-client acceptance',
            'live_acceptance':False,'passed':len(rows),'cases':rows}
if __name__=='__main__':
    result=prove()
    out=ROOT/'artifacts/research/native-peer-pose-20261002.json'
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'passed':result['passed'],'evidence':str(out)}))
