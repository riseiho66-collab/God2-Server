"""Pinned current-EXE C2S24 producer, actual queue append, and C++ codec oracle.

Never launches the game. No source/client/database mutations. UI render/error
work is stopped before entry. This does not infer native server move policy.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
CLIENT=ROOT.parent/'God2/God2.exe'
PIN='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
BASE=0x400000
UI=0x10000000
QUEUE=0x20000000
STACK=0x30000000
SP=STACK+0x8000
STOP=STACK+0xf000
MODALS=(0x232dea,0x232de6,0x232dfe,0x232e20)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


class NativeMove:
    def __init__(self, raw):
        sys.path.insert(0,str(ROOT/'artifacts/tooling/crypto-oracle-python'))
        import pefile
        import unicorn as uc
        from unicorn import x86_const
        require(hashlib.sha256(raw).hexdigest()==PIN,'Current client identity mismatch')
        pe=pefile.PE(data=raw)
        require(pe.OPTIONAL_HEADER.ImageBase==BASE,'Image base mismatch')
        mapped=pe.get_memory_mapped_image()
        self.x=x86_const
        self.vm=uc.Uc(uc.UC_ARCH_X86,uc.UC_MODE_32)
        self.vm.mem_map(BASE,(len(mapped)+4095)&~4095,uc.UC_PROT_READ|uc.UC_PROT_EXEC)
        self.vm.mem_write(BASE,mapped)
        for address,size in ((UI,0x240000),(QUEUE,0x5000),(STACK,0x10000)):
            self.vm.mem_map(address,size)
        self.vm.mem_write(UI+0x86874,struct.pack('<I',QUEUE))
        self.stop=STOP
        self.baseline_mode=False
        self.vm.hook_add(uc.UC_HOOK_CODE,self.code)
        self.vm.hook_add(uc.UC_HOOK_MEM_WRITE,self.write_check)
        self.spans={f'{a:08x}-{b:08x}':hashlib.sha256(pe.get_data(a-BASE,b-a)).hexdigest()
                    for a,b in ((0x496610,0x49671b),(0x4132e0,0x413368),
                                (0x49b5ac,0x49b5bb),(0x49ef1c,0x49ef2b),
                                (0x497fe0,0x498026),(0x4991e0,0x4992a9))}

    def code(self,vm,address,size,_):
        if address in (self.stop,0x475d60):
            vm.emu_stop()
            return
        require(0x496610<=address<0x49671b or 0x4132e0<=address<0x413368 or
                0x49b5ac<=address<0x49b5bb or 0x49ef1c<=address<0x49ef2b or
                self.baseline_mode and (0x497fe0<=address<0x498026 or 0x4991e0<=address<0x4992a9),
                f'Native execution escaped qualified spans: {address:08x}')

    def write_check(self,vm,access,address,size,value,_):
        require(STACK<=address and address+size<=STACK+0x10000 or
                QUEUE+0x36c4<=address and address+size<=QUEUE+0x40c8 or
                self.baseline_mode and any(a<=address and address+size<=b for a,b in
                    ((UI+0x85604,UI+0x85608),(UI+0x8560c,UI+0x85abc),
                     (UI+0x866a8,UI+0x866d0))),
                f'Unexpected native write: {address:08x}+{size}')

    def execute(self,source,destination,gate=0,modal=None,modal_flags=0x20,caller=None):
        vm=self.vm;x=self.x
        for offset in MODALS: vm.mem_write(UI+offset,b'\xff\xff')
        vm.mem_write(UI+0x866e4,struct.pack('<I',gate))
        if modal is not None:
            vm.mem_write(UI+modal,b'\x00\x00')
            vm.mem_write(UI+0xe2988,bytes([modal_flags]))
        vm.mem_write(STACK,b'\xa5'*0xf000)
        vm.mem_write(SP,struct.pack('<III',STOP,source,destination))
        vm.mem_write(QUEUE+0x36c4,struct.pack('<I',3))
        vm.mem_write(QUEUE+0x36c8,b'\x11\x22\x33'+b'\xcc'*16)
        vm.reg_write(x.UC_X86_REG_ESP,SP)
        vm.reg_write(x.UC_X86_REG_ECX,UI)
        vm.reg_write(x.UC_X86_REG_EFLAGS,2)
        self.stop=STOP if caller is None else {0x49b5ac:0x49b5bb,0x49ef1c:0x49ef2b}[caller]
        if caller is not None:
            vm.mem_write(UI+0x855f0,struct.pack('<H',source&0xffff))
            vm.reg_write(x.UC_X86_REG_ESI,UI)
            vm.reg_write(x.UC_X86_REG_EBX,destination)
        vm.emu_start(0x496610 if caller is None else caller,0,count=2000)
        eip=vm.reg_read(x.UC_X86_REG_EIP)
        blocked=modal is not None and bool(modal_flags&0x20) and gate==0
        require(eip==(0x475d60 if blocked else self.stop),'Native stop/budget mismatch')
        count=struct.unpack('<I',vm.mem_read(QUEUE+0x36c4,4))[0]
        expected=b'' if gate or blocked else bytes([0x24,source&255,destination&255])
        require(count==3+len(expected),'Native queue length mismatch')
        require(bytes(vm.mem_read(QUEUE+0x36c8,19))==b'\x11\x22\x33'+expected+b'\xcc'*(16-len(expected)),
                'Native queue bytes/canaries mismatch')
        if not blocked:
            require(vm.reg_read(x.UC_X86_REG_ESP)==(SP+12 if caller is None else SP),
                    'Native stack imbalance')
        return expected

    def verify_zero_baseline(self):
        """Run complete native reset and scalar grant up to resource refresh.

        This certifies the minimal fresh-slot state; it does not certify that
        a reused live slot has never received another metadata-producing record.
        """
        self.baseline_mode=True
        vm=self.vm;x=self.x
        cases=[]
        try:
            for item in (5569,3101,3107):
                for slot in (0,5,29):
                    vm.mem_write(UI+0x8560c-4,b'\xa5'*(1200+8))
                    vm.mem_write(SP,struct.pack('<I',STOP))
                    vm.reg_write(x.UC_X86_REG_ESP,SP)
                    vm.reg_write(x.UC_X86_REG_ECX,UI)
                    vm.reg_write(x.UC_X86_REG_EFLAGS,2)
                    self.stop=STOP
                    vm.emu_start(0x497fe0,0,count=2000)
                    require(vm.reg_read(x.UC_X86_REG_EIP)==STOP,'Initializer budget/return mismatch')
                    require(bytes(vm.mem_read(UI+0x8560c-4,1208))==b'\xa5'*4+bytes(1200)+b'\xa5'*4,
                            'Initializer did not zero exactly 50 complete inventory slots')
                    require(vm.reg_read(x.UC_X86_REG_ESP)==SP+4,'Initializer stack mismatch')
                    pointer=STACK+0x100
                    vm.mem_write(pointer,struct.pack('<HBB',item,slot,3))
                    vm.mem_write(SP,struct.pack('<II',STOP,pointer))
                    vm.reg_write(x.UC_X86_REG_ESP,SP)
                    vm.reg_write(x.UC_X86_REG_ECX,UI)
                    self.stop=0x4992a9
                    vm.emu_start(0x4991e0,0,count=2000)
                    require(vm.reg_read(x.UC_X86_REG_EIP)==self.stop,'Scalar consumer did not reach refresh boundary')
                    wanted=bytearray(1200)
                    wanted[slot*24]=3
                    wanted[slot*24+4:slot*24+6]=struct.pack('<H',item)
                    require(bytes(vm.mem_read(UI+0x8560c,1200))==bytes(wanted),
                            'Scalar grant changed the zero metadata baseline')
                    cases.append({'item_id':item,'slot':slot,'count':3,
                                  'slot_hex':bytes(vm.mem_read(UI+0x8560c+slot*24,24)).hex()})
        finally:
            self.baseline_mode=False
            self.stop=STOP
        return cases


def report(client,probe):
    native=NativeMove(client.read_bytes())
    pairs=[(a,b) for a in range(30) for b in range(30)]
    pairs.extend((i,255-i) for i in range(256))
    pairs.extend([(0x12345605,0xfedcba0c),(0xffffffff,0x80000000),
                  (30,49),(49,30),(50,255),(255,50)])
    wires=[native.execute(a,b).hex() for a,b in pairs]
    gate_count=0
    for gate in (1,0x80000000,0xffffffff):
        require(native.execute(5,12,gate=gate)==b'','Nonzero UI gate sent a record')
        gate_count+=1
    for modal in MODALS:
        for flags in (0,0x20,0xff):
            result=native.execute(5,12,modal=modal,modal_flags=flags)
            require(bool(result)==(not bool(flags&0x20)),'Modal gate mismatch')
            gate_count+=1
    caller_count=0
    for caller in (0x49b5ac,0x49ef1c):
        for source,destination in ((5,12),(12,5),(0,29),(29,0),(30,49),(0xab05,0x12340c)):
            native.execute(source,destination,caller=caller)
            caller_count+=1
    baseline=native.verify_zero_baseline()
    result=subprocess.run([str(probe)],input='\n'.join(wires)+'\n',text=True,
                          encoding='ascii',capture_output=True,timeout=60,check=True)
    actual=result.stdout.splitlines()
    expected=[f'{a&255} {b&255}' for a,b in pairs]
    require(actual==expected,'Compiled production codec disagrees with native output')
    return dict(result='PASS',client_sha256=PIN,producer_va='00496610',
                queue_va='004132e0',span_sha256=native.spans,
                layout='24 source_slot:u8 destination_slot:u8',logical_size=3,
                native_vectors=len(pairs),native_gate_vectors=gate_count,
                native_caller_suffix_vectors=caller_count,
                initialized_scalar_baseline=baseline,
                codec_pairs_exhaustive=65536,codec_opcode_cases=256,codec_length_cases=9,
                calls='0049A330/0049EAB0 use UI+855F0 as source, current UI slot as destination',
                scope='Native producer+queue in synthetic UI state; compiled production codec; no game/UI/server acceptance',
                remaining=['Official server swap/merge/equipment policy',
                           'Complete item metadata response and current-client own-server move acceptance'])


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--client',type=Path,default=CLIENT)
    ap.add_argument('--probe',type=Path,required=True)
    ap.add_argument('--report',type=Path)
    args=ap.parse_args()
    try:
        result=report(args.client,args.probe)
    except Exception as error:
        if args.report:
            args.report.parent.mkdir(parents=True,exist_ok=True)
            args.report.write_text(json.dumps({'result':'FAIL','error':str(error)},indent=2),encoding='utf-8')
        raise
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
