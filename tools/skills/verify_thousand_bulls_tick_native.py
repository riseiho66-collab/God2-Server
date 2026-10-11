"""Execute build-matched native text/HP/bar/phase7 instructions in Unicorn.

Only rendering allocation, actor lookup and pose/UI sinks are substituted.
This verifies ABI and state mechanics, not live visual acceptance.
"""
from pathlib import Path
import hashlib
import json
import struct
import unicorn as uc
from unicorn import x86_const as x
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from tools.skills.native_clone.clone_evidence import IMAGE

ROOT=Path(__file__).resolve().parents[2]
WAR=0x10000000
SOURCE=0x20000000
TARGET=0x20002000
DEFINITION=0x20004000
STACK=0x21000000
SP=STACK+0xF000
RETURN=0x22000000


def verify():
    image=IMAGE.read_bytes()
    assert hashlib.sha256(image).hexdigest()=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
    machine=uc.Uc(uc.UC_ARCH_X86,uc.UC_MODE_32)
    machine.mem_map(0x400000,(len(image)+4095)&~4095)
    machine.mem_write(0x400000,image)
    machine.mem_map(WAR,0xB000000)
    machine.mem_map(SOURCE,0x10000)
    machine.mem_map(STACK,0x10000)
    machine.mem_map(RETURN,4096)
    events=[]
    def write(address,value,fmt='<I'):machine.mem_write(address,struct.pack(fmt,value))
    def read(address,fmt='<I'):return struct.unpack(fmt,machine.mem_read(address,struct.calcsize(fmt)))[0]
    def done(pop,eax=0):
        stack=machine.reg_read(x.UC_X86_REG_ESP)
        ret=read(stack)
        machine.reg_write(x.UC_X86_REG_ESP,stack+4+pop)
        machine.reg_write(x.UC_X86_REG_EAX,eax)
        machine.reg_write(x.UC_X86_REG_EIP,ret)
    def sink(machine,address,size,context):
        stack=machine.reg_read(x.UC_X86_REG_ESP)
        args=lambda n:struct.unpack('<'+'I'*n,machine.mem_read(stack+4,n*4))
        owner=machine.reg_read(x.UC_X86_REG_ECX)
        if address==0x51e6e0:
            side,slot,kind=args(3)
            result=SOURCE if side&255==1 else TARGET
            done(12,result)
        elif address==0x5224a0:done(4,0)
        elif address==0x547af7:
            dest,fmt,value=args(3)
            text=bytes(machine.mem_read(fmt,32)).split(b'\0')[0]
            signed=struct.unpack('<i',struct.pack('<I',value))[0]
            rendered=text.replace(b'%d',str(signed).encode())
            machine.mem_write(dest,rendered+b'\0')
            events.append({'sprintf':signed,'format_hex':text.hex()})
            done(0,len(rendered))
        elif address==0x41b330:
            events.append({'release':args(1)[0]});done(4)
        elif address==0x51dc00:
            events.append({'allocate_text_at':owner,'args':list(args(6))})
            write(owner+0xA,37,'<h');done(24,37)
        elif address==0x51de40:
            text_owner,buffer=args(2)
            events.append({'set_text_at':text_owner,'text':bytes(machine.mem_read(buffer,30)).split(b'\0')[0].decode('ascii')})
            done(0)
        elif address in (0x51dd70,0x51dcc0):
            events.append({'text_visibility':hex(address),'owner':owner});done(0)
        elif address==0x508f50:
            slot,hp,mp=args(3)
            events.append({'bar':[slot&0xffff,hp,mp]});done(12)
        elif address==0x529870:
            events.append({'pose':list(args(3))});done(12)
        elif address==0x52a200:done(12)
        elif address==0x52a710:done(8)
    sinks=[0x51e6e0,0x5224a0,0x547af7,0x41b330,0x51dc00,0x51de40,0x51dd70,0x51dcc0,0x508f50,0x529870,0x52a200,0x52a710]
    for address in sinks:machine.hook_add(uc.UC_HOOK_CODE,sink,begin=address,end=address)
    def run(address,args=(),owner=WAR):
        machine.mem_write(SP,struct.pack('<'+'I'*(len(args)+1),RETURN,*[v&0xffffffff for v in args]))
        machine.reg_write(x.UC_X86_REG_ESP,SP)
        machine.reg_write(x.UC_X86_REG_ECX,owner)
        machine.reg_write(x.UC_X86_REG_EFLAGS,2)
        machine.emu_start(address,RETURN,count=200000,timeout=2000000)
        assert machine.reg_read(x.UC_X86_REG_EIP)==RETURN
        assert machine.reg_read(x.UC_X86_REG_ESP)==SP+4+len(args)*4
        return machine.reg_read(x.UC_X86_REG_EAX)
    write(SOURCE+0x1A,1,'<H');write(TARGET+0x1A,2,'<H')
    write(SOURCE+0x1E9,3,'<B');write(SOURCE+0x234,128,'<B')
    write(SOURCE+0xEC4,DEFINITION)
    machine.mem_write(DEFINITION,b'\x96\0'+bytes(108))
    write(SOURCE+0x239,4,'<B')
    write(SOURCE+0x28A+8,-32767,'<h')
    write(SOURCE+0x2D8+8,12,'<h')
    run(0x52b060,(1,0,0,0,-6553,0,0,28))
    assert read(SOURCE+0x239,'<B')==4
    assert read(SOURCE+0x28A+8,'<h')==-6553
    assert read(SOURCE+0x2D8+8,'<h')==37
    assert any(e.get('allocate_text_at')==SOURCE+0x310+4*16 for e in events)
    assert any(e.get('set_text_at')==SOURCE+0x310+4*16 for e in events)
    assert any(e.get('sprintf')==-6553 for e in events)
    assert any('release' in e for e in events)
    # Actual HP routine clamps [0,max] and publishes dirty flag for ownactor.
    write(WAR+0x2DC,TARGET);write(TARGET+0xDE8,7000);write(TARGET+0xDF0,10000)
    run(0x528a70,(TARGET,-6553));assert read(TARGET+0xDE8)==447
    assert read(WAR+0xA89785C)==1
    run(0x528a70,(TARGET,-1000));assert read(TARGET+0xDE8)==0
    write(TARGET+0xDEC,123);write(TARGET+0x1D8,5,'<h')
    run(0x52d9f0,(TARGET,));assert any(e.get('bar')==[5,0,123] for e in events)
    # Actual native phase7 uses source+224, not target+232, for finaldeath.
    write(WAR+0x2F4,1);write(WAR+0x2F8,1)
    write(SOURCE+0x239,1,'<B');write(SOURCE+0x23A,0,'<B')
    write(SOURCE+0x224,9,'<B');write(SOURCE+0x233,7,'<B')
    write(TARGET+0x232,0,'<B');write(TARGET+0x1EA,15,'<B')
    assert run(0x524820,(SOURCE,))==1
    assert read(SOURCE+0x239,'<B')==0 and read(SOURCE+0x259,'<B')==1
    assert read(TARGET+0x1EA,'<B')==9 and read(WAR+0x2F4)==0
    decoder=Cs(CS_ARCH_X86,CS_MODE_32)
    excerpt=[f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in decoder.disasm(image[0x124d86:0x124dcd],0x524d86)]
    assert any('dec byte ptr [ebp + 0x277]' in i for i in excerpt)
    result={'status':'PASS','image':str(IMAGE),'sha256':hashlib.sha256(image).hexdigest(),
        'checks':['52B060 ret32 and index239 -> damage28A/text310/nativepool2D8',
                  '528A70 HP clamp and dirty flag','52D9F0 bar args',
                  '524820 phase7 completion and authoritative224 death'],
        'events':events,'death_pending_counter_native_excerpt':excerpt,
        'limitation':'Native drawing sinks substituted; no live visual or render-loop acceptance'}
    out=ROOT/'artifacts/custom-skills/thousand-bulls/native-tick-oracle.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    r=verify();print(json.dumps({'status':r['status'],'checks':r['checks']}))
