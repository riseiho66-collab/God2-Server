"""Execute current native1D producer; queue boundary isolated, no invented reply."""
import hashlib,json,struct
from pathlib import Path
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP
from tools.strike_lab.current_protocol_coverage import qualified_image,NativeLengths

ROOT=Path(__file__).resolve().parents[2]
def prove():
    raw=qualified_image();vm=Uc(UC_ARCH_X86,UC_MODE_32)
    vm.mem_map(0x400000,(len(raw)+4095)&~4095);vm.mem_write(0x400000,raw)
    owner,stack,payload,stop=0x10000000,0x20000000,0x21000000,0x22000000
    vm.mem_map(owner,0x87000)
    for page in (stack,payload,stop):vm.mem_map(page,4096)
    vm.mem_write(owner+0x86874,struct.pack('<I',0x31000000));queued=[]
    def hook(v,address,size,_):
        if address==0x4132e0:
            esp=v.reg_read(UC_X86_REG_ESP)
            ret,opcode,ptr,count=struct.unpack('<4I',v.mem_read(esp,16))
            assert v.reg_read(UC_X86_REG_ECX)==0x31000000 and opcode==0x1d and count==2
            queued.append(bytes([opcode])+bytes(v.mem_read(ptr,count)))
            v.reg_write(UC_X86_REG_EIP,ret);v.reg_write(UC_X86_REG_ESP,esp+16)
        elif address==stop:v.emu_stop()
    vm.hook_add(UC_HOOK_CODE,hook)
    values=[0,0xffff,0x1234,0xa5a5]+[1<<bit for bit in range(16)]
    for value in values:
        vm.mem_write(payload,struct.pack('<H',value)+b'\xa5\x5a')
        vm.mem_write(stack+0x800,struct.pack('<II',stop,payload))
        vm.reg_write(UC_X86_REG_ECX,owner);vm.reg_write(UC_X86_REG_ESP,stack+0x800)
        queued.clear();vm.emu_start(0x497d80,stop,count=30)
        assert queued==[bytes([0x1d])+struct.pack('<H',value)]
        assert vm.reg_read(UC_X86_REG_ESP)==stack+0x808
    size,_=NativeLengths(raw).query(0x1d);assert size==173
    return {'native_image_sha256':hashlib.sha256(raw).hexdigest(),'producer':'00497D80',
        'queue_call':'00497D8F ->004132E0','c2s_logical_size':3,'s2c_same_opcode_size':size,
        'passed':len(values),'values':values,'native_server_effect':'UNQUALIFIED',
        'current_client_accepted':False}
if __name__=='__main__':
    d=prove();p=ROOT/'artifacts/research/native-options-1d-20261002.json'
    p.write_text(json.dumps(d,indent=2),encoding='utf-8');print(json.dumps({'passed':d['passed'],'artifact':str(p)}))
