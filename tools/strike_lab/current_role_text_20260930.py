"""Bounded original C2S20 producer and S2C23 copy proof; no live acceptance.

Only current PE/mapped image is used. No process, UI, network or DB activity.
The complete producer and queue execute unchanged; receiver stops before its
UI refresh callees, so a passing copy slice is not a rendered-client result.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'artifacts/tooling/crypto-oracle-python'))
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_PROT_READ,UC_PROT_WRITE,UC_PROT_EXEC,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn import x86_const as x

BASE=0x400000
STACK,UI,CONNECTION,INPUT,RETURN,WORLD=0x3000000,0x3100000,0x3200000,0x3300000,0x3400000,0x4000000
SP=STACK+0x1000
MAPPED_SHA='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
CLIENT_SHA='9be38ef858bc9c63b6f296cae4a8e601ddcfaf614700e725c4bec44065b53336'
def require(value,message):
    if not value:raise ValueError(message)
def sha(raw):return hashlib.sha256(raw).hexdigest()

def verify():
    mapped=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    client=(ROOT.parent/'God2/God2.exe').read_bytes()
    require(sha(mapped)==MAPPED_SHA and sha(client)==CLIENT_SHA,'Current image pin changed')
    image=pefile.PE(data=client).get_memory_mapped_image()
    spans=[]
    for start,end in ((0x96890,0x968da),(0x132e0,0x13370),(0x69f02,0x69f48),(0x124c,0x1252),
                      (0xe7b20,0xe7c00),(0x81c20,0x81d20),(0xe7c80,0xe7ce0)):
        require(mapped[start:end]==image[start:end],'Mapped/current PE span differs')
        spans.append(dict(start_va=hex(BASE+start),end_va_exclusive=hex(BASE+end),sha256=sha(image[start:end])))
    require(struct.unpack_from('<I',mapped,0x1324+0x23*4)[0]==0x40124c,'S2C23 length leaf')
    require(mapped[0x124c:0x1252]==bytes.fromhex('b811000000c3'),'S2C23 length17')
    require(struct.unpack_from('<I',mapped,0x6b5d4+0x23*4)[0]==0x469f02,'S2C23 dispatch')
    vm=Uc(UC_ARCH_X86,UC_MODE_32)
    vm.mem_map(BASE,(len(mapped)+4095)&~4095,UC_PROT_READ|UC_PROT_EXEC);vm.mem_write(BASE,mapped)
    for address,size in ((STACK,0x2000),(UI,0x90000),(CONNECTION,0x5000),(INPUT,0x1000),(RETURN,0x1000),((WORLD+0x15396903)&~4095,0x1000)):
        vm.mem_map(address,size,UC_PROT_READ|UC_PROT_WRITE)
    vm.mem_write(UI+0x86874,struct.pack('<I',CONNECTION))
    state={}
    def code(vm,address,size,context):
        if address==state['stop']:vm.emu_stop();return
        require(any(start<=address and address+size<=end for start,end in state['code']),f'Unexpected original code boundary {address:08x}/{size}')
        state['instructions']+=1
    def write(vm,access,address,size,value,context):
        require(any(start<=address and address+size<=end for start,end in state['writes']),'Unexpected native write')
    vm.hook_add(UC_HOOK_CODE,code);vm.hook_add(UC_HOOK_MEM_WRITE,write)
    rows=[]
    texts=[bytes((0x41+i)%0x7f or 0x41 for i in range(n)) for n in range(16)]+['角色文字'.encode('cp950')]
    for text in texts:
        for salt in (0,0xa5,0xff):
            vm.mem_write(STACK,bytes([salt])*0x2000);vm.mem_write(SP,struct.pack('<II',RETURN,INPUT))
            vm.mem_write(INPUT,text+b'\0');vm.mem_write(CONNECTION+0x36c4,bytes(4))
            vm.mem_write(CONNECTION+0x36c8,bytes([0xcc])*32)
            for reg in (x.UC_X86_REG_EAX,x.UC_X86_REG_EBX,x.UC_X86_REG_EDX,x.UC_X86_REG_ESI,x.UC_X86_REG_EDI,x.UC_X86_REG_EBP):vm.reg_write(reg,0)
            vm.reg_write(x.UC_X86_REG_ECX,UI);vm.reg_write(x.UC_X86_REG_ESP,SP);vm.reg_write(x.UC_X86_REG_EFLAGS,2)
            state.update(stop=RETURN,code=[(0x496890,0x4968da),(0x4132e0,0x413370)],writes=[(STACK,STACK+0x2000),(CONNECTION+0x36c4,CONNECTION+0x36c8+17)],instructions=0)
            vm.emu_start(0x496890,RETURN,count=1000,timeout=100000)
            require(vm.reg_read(x.UC_X86_REG_EIP)==RETURN and vm.reg_read(x.UC_X86_REG_ESP)==SP+8,'Producer exact return/stack')
            produced=bytes(vm.mem_read(CONNECTION+0x36c8,17));count=struct.unpack('<I',vm.mem_read(CONNECTION+0x36c4,4))[0]
            require(count==17 and produced==b'\x20'+text+b'\0'+bytes([salt])*(15-len(text)),'Native C2S20 bytes/tail')
            require(bytes(vm.mem_read(CONNECTION+0x36c8+17,15))==bytes([0xcc])*15,'Queue suffix canary')
            producer_instructions=state['instructions']
            reply=b'\x23'+text+bytes(16-len(text))
            dest=WORLD+0x15396903
            vm.mem_write(INPUT,reply);vm.mem_write(dest-1,bytes([0xcc])*18)
            vm.reg_write(x.UC_X86_REG_ESP,SP);vm.reg_write(x.UC_X86_REG_EBP,WORLD);vm.reg_write(x.UC_X86_REG_EBX,INPUT);vm.reg_write(x.UC_X86_REG_EFLAGS,2)
            state.update(stop=0x469f2f,code=[(0x469f02,0x469f2f)],writes=[(STACK,STACK+0x2000),(dest,dest+len(text)+1)],instructions=0)
            vm.emu_start(0x469f02,0x469f2f,count=1000,timeout=100000)
            require(vm.reg_read(x.UC_X86_REG_EIP)==0x469f2f,'Receiver exact UI boundary')
            require(bytes(vm.mem_read(dest-1,18))==b'\xcc'+text+b'\0'+bytes([0xcc])*(16-len(text)),'Receiver string/canaries')
            rows.append(dict(text_hex=text.hex(),stack_salt=salt,c2s_hex=produced.hex(),s2c_hex=reply.hex(),producer_instructions=producer_instructions,receiver_instructions=state['instructions']))
    return dict(schema='current-role-text-v1',client_sha256=CLIENT_SHA,mapped_sha256=MAPPED_SHA,spans=spans,
        c2s_opcode='20',s2c_opcode='23',logical_size=17,qualified_vectors=len(rows),vectors=rows,
        semantics='Editable secondary role text at role+37/local actor+C7; human title/nickname label unqualified',
        acceptance='BOUNDED_NATIVE_PRODUCER_AND_RECEIVER_COPY_ONLY',runtime_acceptance=False,
        limits=['S2C receiver stops before4B1A00 UI/renderer refresh; no graphical acceptance.',
                'Native producer copies opaque stack after NUL; authoritative storage and S2C reply must use canonical zero tail.',
                'Peer6F logical45 shares the secondary renderer buffer81, but no new peer lifecycle is certified here.',
                'Authorization, persistence, encoding policy and moderation are server implementation policy.'])
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=verify();text=json.dumps(result,ensure_ascii=True,indent=2)+'\n'
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text,encoding='utf-8')
    else:print(text,end='')
    return 0
if __name__=='__main__':raise SystemExit(main())
