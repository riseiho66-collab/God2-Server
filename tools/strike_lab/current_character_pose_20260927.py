"""Bounded native S2C77 pose consumer arithmetic; not live acceptance."""
from pathlib import Path
import hashlib,json,struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP
ROOT=Path(__file__).resolve().parents[2]

def prove():
    image=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    vm=Uc(UC_ARCH_X86,UC_MODE_32);vm.mem_map(0x400000,(len(image)+4095)&~4095);vm.mem_write(0x400000,image)
    world=0x10000000;stack=0x30000000;record=0x31000000;stop=0x32000000
    for page in {world,(world+0x1539683c)&~4095,(world+0xa8797ed)&~4095,stack,record,stop}:
        vm.mem_map(page,4096)
    directions=[]
    def hook(v,address,size,unused):
        if address==0x503860:
            esp=v.reg_read(UC_X86_REG_ESP)
            directions.append(struct.unpack('<I',v.mem_read(esp+4,4))[0])
            destination=struct.unpack('<I',v.mem_read(esp,4))[0]
            v.reg_write(UC_X86_REG_ESP,esp+8);v.reg_write(UC_X86_REG_EIP,destination)
        elif address==stop:v.emu_stop()
    vm.hook_add(UC_HOOK_CODE,hook)
    rows=[]
    for mode in (1,2,3):
        for direction in range(8):
            vm.mem_write(world+0x1539683c,struct.pack('<I',4))
            vm.mem_write(world+0xa8797ed,bytes([direction]))
            vm.mem_write(world+0x30,struct.pack('<I',1))
            payload=struct.pack('<HBBBB',4,0,(mode<<3)|direction,0,0)
            vm.mem_write(record,payload);vm.mem_write(stack+0x800,struct.pack('<II',stop,record))
            vm.reg_write(UC_X86_REG_ECX,world);vm.reg_write(UC_X86_REG_ESP,stack+0x800)
            vm.emu_start(0x501610,stop,count=1000)
            state=struct.unpack('<I',vm.mem_read(world+0x30,4))[0]
            assert state==15+mode and directions[-1]==direction
            rows.append({'mode':mode,'direction':direction,'native_world_state':state})
    opcode=0x77
    length_target=struct.unpack_from('<I',image,0x1324+opcode*4)[0]
    length=struct.unpack_from('<I',image,length_target-0x400000+1)[0]
    target=struct.unpack_from('<I',image,0x6b5d4+opcode*4)[0]
    assert length==7 and target==0x469bba
    return {'authority':'NATIVE_CONSUMER_ARITHMETIC_ONLY','live_acceptance':False,
        'image_sha256':hashlib.sha256(image).hexdigest(),'opcode':'0x77','logical_length':length,
        'dispatch_target':hex(target),'consumer':'0x501610','qualified_rows':rows,
        'adapter':'503860 direction/renderer callback recorded and returned; original501610 pose state writes execute unchanged',
        'unread_tail':'payload5 is zero candidate, not recovered original server semantics'}

if __name__=='__main__':print(json.dumps(prove(),indent=2))
