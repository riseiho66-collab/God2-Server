"""Current PE DA routing / component setters. Bounded slices, not rendered acceptance."""
import json
import struct
from .current_equipment_20260926 import EquipmentOracle, PIN, require
import unicorn as uc
from unicorn import x86_const as x

BASE, WORLD, STACK, DATA = 0x400000, 0x10000000, 0x30000000, 0x31000000
SP, STOP = STACK+0x8000, STACK+0xf000
MANAGER = WORLD+0x15383410

class Oracle:
    def __init__(self):
        self.image = EquipmentOracle().image
        self.v = v = uc.Uc(uc.UC_ARCH_X86, uc.UC_MODE_32)
        v.mem_map(BASE,(len(self.image)+4095)&~4095,uc.UC_PROT_READ|uc.UC_PROT_EXEC)
        v.mem_write(BASE,self.image)
        for a,n in ((STACK,0x10000),(DATA,0x10000),(MANAGER&~4095,0x19000),(WORLD+0xaa36000,0x171000)):
            v.mem_map(a,n)
        self.ranges=(); self.stops=set();self.writes=()
        v.hook_add(uc.UC_HOOK_CODE,self.code)
        v.hook_add(uc.UC_HOOK_MEM_WRITE,self.write)
    def code(self,v,a,n,_):
        if a in self.stops: v.emu_stop();return
        require(any(lo<=a and a+n<=hi for lo,hi in self.ranges),f'Unexpected instruction {a:x}')
    def write(self,v,access,a,n,value,_):
        require(any(lo<=a and a+n<=hi for lo,hi in ((STACK,STACK+0x10000),)+self.writes),f'Unexpected write {a:x}')
    def put(self,a,value):self.v.mem_write(a,struct.pack('<I',value))
    def run(self,entry,stops,ranges):
        self.stops=set(stops);self.ranges=ranges
        self.v.reg_write(x.UC_X86_REG_EFLAGS,2)
        self.v.emu_start(entry,0,count=10000)
        pc=self.v.reg_read(x.UC_X86_REG_EIP)
        require(pc in self.stops,'Instruction budget exhausted')
        return pc
    def call(self,entry,args,ranges,this=0):
        self.v.mem_write(SP,struct.pack('<'+'I'*(len(args)+1),STOP,*args))
        self.v.reg_write(x.UC_X86_REG_ESP,SP);self.v.reg_write(x.UC_X86_REG_ECX,this)
        self.run(entry,(STOP,),ranges)
        require(self.v.reg_read(x.UC_X86_REG_ESP)==SP+4+len(args)*4,'Stack imbalance')
    def route(self,local,identity,remote=False,selector=0,accessory=0):
        v=self.v;self.put(WORLD+0x1539683c,local)
        for i in range(128):self.put(MANAGER+0x18+i*0x268,0xffffffff)
        if remote:
            self.put(MANAGER+0x18,identity)
            v.mem_write(MANAGER+0x18+0x34,struct.pack('<H',selector))
            v.mem_write(MANAGER+0x18+0x40,struct.pack('<H',accessory))
        self.put(WORLD+0x15396880,(selector<<18)|(accessory<<10))
        block=bytes.fromhex('0020004000008000')
        packet=b'\xda'+struct.pack('<HHBB',identity,0,7,9)+block
        v.mem_write(DATA,b'\xcc'*32+packet+b'\xcc'*32)
        for reg,val in ((x.UC_X86_REG_ESP,SP),(x.UC_X86_REG_EBP,WORLD),(x.UC_X86_REG_EBX,DATA+32)):
            v.reg_write(reg,val)
        self.writes=((WORLD+0x1539aed1,WORLD+0x1539aed5),)
        stop=self.run(0x469369,(0x461270,0x46b517),((0x469369,0x4693cc),(0x469523,0x469541),(0x4fc990,0x4fc9d0),(0x503d30,0x503d88),(0x503f61,0x503f94)))
        expected=0x461270 if local==identity or remote else 0x46b517
        require(stop==expected,'DA routing mismatch')
        require(bytes(v.mem_read(DATA,79))==b'\xcc'*32+packet+b'\xcc'*32,'Packet/canary mutated')
        if stop==0x461270:
            esp=v.reg_read(x.UC_X86_REG_ESP)
            args=struct.unpack('<4I',v.mem_read(esp+4,16))
            require((args[0]&0xffff,args[1]&0xffff,args[2])==(selector,accessory,DATA+39),'DA component arguments')
            if local==identity:
                require(bytes(v.mem_read(WORLD+0x1539aed1,4))==b'\x07\0\0\x09','DA local scalars')
    def setters(self,override,variant):
        actor=DATA+0x1000; handles=DATA+0x2000;block=DATA+0x2100
        self.v.mem_write(actor,b'\xa5'*0x300)
        self.v.mem_write(actor+0x61,bytes([0x10 if override else 0]))
        self.v.mem_write(handles,struct.pack('<4H',0,1,511,0xffff))
        self.v.mem_write(block,bytes([0,variant*32,0,variant*32,0,variant*32,0x80,variant*32]))
        before=bytearray(self.v.mem_read(actor,0x300)); expected=bytearray(before)
        for i,h in enumerate((0,1,511,0xffff)):
            struct.pack_into('<H',expected,0x228+i*6,h)
            expected[0x22c+i*6]=7 if override else variant
            if not override:expected[0x251+i*2]=(0xa5&31)|(variant<<5)
        self.writes=((actor,actor+0x300),)
        self.call(0x4fc130,(handles,actor,0,block),((0x4fc130,0x4fc1b4),(0x4ff450,0x4ff480),(0x4ffa20,0x4ffa50)))
        require(bytes(self.v.mem_read(actor,0x300))==expected,'Remote setters/canary differ')
    def persist(self,block):
        self.v.mem_write(DATA,block);self.put(SP+0x10,DATA)
        for reg,val in ((x.UC_X86_REG_ESP,SP),(x.UC_X86_REG_EBP,WORLD),(x.UC_X86_REG_ESI,WORLD+0x1539683c)):
            self.v.reg_write(reg,val)
        self.writes=((WORLD+0x1539adc0,WORLD+0x1539adc8),)
        self.run(0x503ff4,(0x501810,),((0x503ff4,0x504018),))
        require(bytes(self.v.mem_read(WORLD+0x1539adc0,8))==block,'Local persisted block mismatch')

def verify():
    n=Oracle();count=0
    for op,size in ((0x36,11),(0x37,11),(0xda,15)):
        target=struct.unpack_from('<I',n.image,0x1324+4*op)[0]
        n.call(target,(),((target,target+6),))
        require(n.v.reg_read(x.UC_X86_REG_EAX)==size,'Native packet length');count+=1
    require(n.image[0x18a990:0x18a990+20].split(b'\0')[0]==b'\\Data\\Rom\\GodDoll\\','36/37 resource path')
    for local in (1,217,16383):
        for identity,remote in ((local,False),(local+1,False),(local+1,True)):
            for selector,accessory in ((0,0),(27,3),(91,119)):
                n.route(local,identity,remote,selector,accessory);count+=1
    for override in (False,True):
        for variant in range(8):n.setters(override,variant);count+=1
    for block in (bytes(8),bytes(range(8)),b'\xff'*8):n.persist(block);count+=1
    return {'status':'PASS','cases':count,'client_sha256':PIN,'lengths':{'36':11,'37':11,'DA':15},'scope':'native length routines; DA dispatch/local prefix/remote lookup until 61270; full 4FC130 plus real setters; local persisted block slice before 501810; no resource/render acceptance or item-to-appearance mapping'}
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))


