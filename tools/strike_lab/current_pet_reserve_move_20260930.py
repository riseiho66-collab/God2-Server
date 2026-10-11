"""Execute current native pet42/43 click classifier,24 producer and queue.

Starts after the ordinary caller's source-definition lookup at49EB44. Does not
claim full mouse/resource execution or actual-client acceptance. No game callee
is replaced, no process is launched, and all writes are bounded.
"""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
from .current_inventory_move import ROOT, CLIENT, UI, QUEUE, STACK, SP, STOP, MODALS, require

PIN='9be38ef858bc9c63b6f296cae4a8e601ddcfaf614700e725c4bec44065b53336'


class NativeReserve:
    def __init__(self, raw):
        sys.path.insert(0,str(ROOT/'artifacts/tooling/crypto-oracle-python'))
        import pefile
        import unicorn as uc
        from unicorn import x86_const
        require(hashlib.sha256(raw).hexdigest()==PIN,'Current client identity mismatch')
        pe=pefile.PE(data=raw);require(pe.OPTIONAL_HEADER.ImageBase==0x400000,'Image base mismatch')
        mapped=pe.get_memory_mapped_image();self.x=x86_const
        self.vm=uc.Uc(uc.UC_ARCH_X86,uc.UC_MODE_32)
        self.vm.mem_map(0x400000,(len(mapped)+4095)&~4095,uc.UC_PROT_READ|uc.UC_PROT_EXEC)
        self.vm.mem_write(0x400000,mapped)
        for address,size in ((UI,0x240000),(QUEUE,0x5000),(STACK,0x10000)):
            self.vm.mem_map(address,size)
        self.vm.mem_write(UI+0x86874,struct.pack('<I',QUEUE))
        self.vm.hook_add(uc.UC_HOOK_CODE,self.code)
        self.vm.hook_add(uc.UC_HOOK_MEM_WRITE,self.write_check)
        self.spans={f'{a:08x}-{b:08x}':hashlib.sha256(pe.get_data(a-0x400000,b-a)).hexdigest()
            for a,b in ((0x496610,0x49671b),(0x4132e0,0x413368))}
        previous=json.loads((ROOT/'artifacts/reports/current-inventory-move-20260926/native-producer.json').read_text())
        for span,digest in self.spans.items():
            require(previous['span_sha256'][span]==digest,'Previously proven producer/queue code changed')

    def code(self, vm, address, size, context):
        if address in (STOP, 0x498c90, 0x475d60):
            vm.emu_stop()
            return
        require(0x49eb44 <= address < 0x49ebca or
                0x49ed9d <= address < 0x49ef3d or
                0x496610 <= address < 0x49671b or 0x4132e0 <= address < 0x413368,
                f'Native reserve execution escaped: {address:08x}')

    def write_check(self, vm, access, address, size, value, context):
        require(STACK <= address and address+size <= STACK+0x10000 or
                QUEUE+0x36c4 <= address and address+size <= QUEUE+0x40c8 or
                UI+0x855f0 <= address and address+size <= UI+0x855f2,
                f'Native reserve unexpected write: {address:08x}+{size}')

    def classify(self, source, destination, gate=0, modal=None):
        vm=self.vm;x=self.x
        for offset in MODALS:vm.mem_write(UI+offset,b'\xff\xff')
        if modal is not None:
            vm.mem_write(UI+modal,b'\x00\x00');vm.mem_write(UI+0xe2988,b'\x20')
        vm.mem_write(UI+0x866e4,struct.pack('<I',gate))
        vm.mem_write(UI+0x855f0,struct.pack('<h',source))
        vm.mem_write(STACK,b'\xa5'*0xf000)
        # Four saved registers, caller local, return and three caller args.
        vm.mem_write(SP,struct.pack('<9I',0,0,0,0,0,STOP,0,0,STACK+0x100))
        vm.mem_write(QUEUE+0x36c4,struct.pack('<I',3))
        vm.mem_write(QUEUE+0x36c8,b'\x11\x22\x33'+b'\xcc'*16)
        vm.reg_write(x.UC_X86_REG_ESP,SP);vm.reg_write(x.UC_X86_REG_ESI,UI)
        vm.reg_write(x.UC_X86_REG_EBX,destination);vm.reg_write(x.UC_X86_REG_EFLAGS,2)
        vm.emu_start(0x49eb44,0,count=2000)
        stopped=vm.reg_read(x.UC_X86_REG_EIP)
        count=struct.unpack('<I',vm.mem_read(QUEUE+0x36c4,4))[0]
        require(3 <= count <= 6,'Native reserve queue length')
        actual=bytes(vm.mem_read(QUEUE+0x36c8+3,count-3))
        expected=b'' if gate or modal is not None else bytes((0x24,source,destination))
        require(stopped==(0x475d60 if modal is not None and not gate else STOP),'Native reserve stop')
        require(actual==expected,'Native reserve wire mismatch')
        require(bytes(vm.mem_read(QUEUE+0x36c8,19))==b'\x11\x22\x33'+actual+b'\xcc'*(16-len(actual)),
                'Native reserve queue canaries')
        if stopped==STOP:
            require(vm.reg_read(x.UC_X86_REG_ESP)==SP+36,'Native caller stack balance')
            require(bytes(vm.mem_read(UI+0x855f0,2))==b'\xff\xff','Native caller selection cleanup')
        return dict(source=source,destination=destination,gate=gate,modal=modal,logical=actual.hex())


def verify():
    raw=CLIENT.read_bytes();native=NativeReserve(raw)
    cases=[]
    for source,destination in ((42,43),(43,42)):
        for gate in (0,1,0x80000000,0xffffffff):cases.append(native.classify(source,destination,gate))
        for modal in MODALS:cases.append(native.classify(source,destination,modal=modal))
    # The main producer's identity check applies to this independently bounded
    # classifier. Retain the exact new caller span from the current mapped PE.
    import pefile
    pe=pefile.PE(data=raw)
    spans=dict(native.spans)
    for a,b in ((0x49eb44,0x49ebca),(0x49ed9d,0x49ef3d)):
        spans[f'{a:08x}-{b:08x}']=hashlib.sha256(pe.get_data(a-0x400000,b-a)).hexdigest()
    return dict(result='PASS',client_sha256=PIN,cases=cases,span_sha256=spans,
        scope='original post-lookup caller classifier, complete24 producer and queue; no gameplay formula or actual-client acceptance',
        custom_policy='CUSTOM-0039 whole owned reserve-instance swap; no active44 mutation')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=verify();text=json.dumps(result,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text+'\n',encoding='utf-8')
    print(text)


if __name__=='__main__':main()
