"""Pinned native27 producer and absolute41 consumer; isolated x86 execution."""
import hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP
from tools.strike_lab.current_protocol_coverage import qualified_image,NativeLengths
ROOT=Path(__file__).resolve().parents[2]

def prove():
    raw=qualified_image();vm=Uc(UC_ARCH_X86,UC_MODE_32)
    vm.mem_map(0x400000,(len(raw)+4095)&~4095);vm.mem_write(0x400000,raw)
    ui,stack,payload,stop=0x10000000,0x20000000,0x21000000,0x22000000
    vm.mem_map(ui,0x87000)
    for page in (stack,payload,stop):vm.mem_map(page,4096)
    vm.mem_write(ui+0x86874,struct.pack('<I',0x31000000));queued=[]
    def hook(v,address,size,_):
        if address==0x4132e0:
            esp=v.reg_read(UC_X86_REG_ESP);ret,opcode,ptr,count=struct.unpack('<4I',v.mem_read(esp,16))
            assert v.reg_read(UC_X86_REG_ECX)==0x31000000 and opcode==0x27 and count==4
            queued.append(bytes([opcode])+bytes(v.mem_read(ptr,count)))
            v.reg_write(UC_X86_REG_EIP,ret);v.reg_write(UC_X86_REG_ESP,esp+16)
        elif address in (stop,0x4992a9):v.emu_stop()
    vm.hook_add(UC_HOOK_CODE,hook);producer=consumer=0
    for body in (bytes(4),bytes.fromhex('230c0504'),bytes.fromhex('c1150001'),bytes.fromhex('ffff80ff')):
        for modal in (0,1,0xffffffff):
            queued.clear();vm.mem_write(ui+0x866e4,struct.pack('<I',modal));vm.mem_write(payload,body)
            vm.mem_write(stack+0x800,struct.pack('<II',stop,payload))
            vm.reg_write(UC_X86_REG_ECX,ui);vm.reg_write(UC_X86_REG_ESP,stack+0x800)
            vm.emu_start(0x496720,stop,count=30)
            assert queued==([b'\x27'+body] if modal==0 else [])
            assert vm.reg_read(UC_X86_REG_ESP)==stack+0x808;producer+=1
    for slot in (0,5,29):
        for item,count in ((3107,3),(0,0),(3107,127),(3107,128)):
            before=bytes([7,0xa5,0x5a,0xcc])+struct.pack('<H',3107)+bytes(range(18))
            vm.mem_write(ui+0x8560c+24*slot,before)
            vm.mem_write(payload,struct.pack('<HBB',item,slot,count))
            vm.mem_write(stack+0x800,struct.pack('<II',stop,payload))
            vm.reg_write(UC_X86_REG_ECX,ui);vm.reg_write(UC_X86_REG_ESP,stack+0x800)
            vm.emu_start(0x4991e0,stop,count=100)
            after=bytes(vm.mem_read(ui+0x8560c+24*slot,24))
            expected=bytes([count if count<128 else 0])+before[1:4]+struct.pack('<H',item if 0<count<128 else 0)+before[6:]
            assert after==expected;consumer+=1
    assert NativeLengths(raw).query(0x41)[0]==5
    return {'native_image_sha256':hashlib.sha256(raw).hexdigest(),'producer':'00496720',
        'c2s_logical_size':5,'layout':'27,item_u16,slot_u8,quantity_u8',
        'producer_cases':producer,'consumer':'004991E0','consumer_cases':consumer,
        'scope':'Native packet/display only; destruction without ground drop is CUSTOM-0061',
        'current_client_accepted':False}
if __name__=='__main__':
    value=prove();out=ROOT/'artifacts/research/native-discard-27-20261002.json'
    out.write_text(json.dumps(value,indent=2),encoding='utf-8');print(json.dumps(value))
