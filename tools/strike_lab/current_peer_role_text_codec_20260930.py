"""Execute original52F170/52F330 with explicit real Windows NLS API adapters.

The original conversion instructions and language-enabled accessor execute
unchanged. Only OS API boundaries marshal bounded emulated buffers to this
host's actual MultiByteToWideChar/WideCharToMultiByte/LCMapStringA. No game
callee, conversion result or character mapping is stubbed.
"""
import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'artifacts/tooling/crypto-oracle-python')]
import pefile
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_PROT_ALL
from unicorn import x86_const as x
from tools.strike_lab.current_peer_role_text_20260930 import CLIENT_SHA,MAPPED_SHA,require,sha

BASE=0x400000;STACK=0x3000000;INPUT=0x3100000;OUTPUT=0x3200000;RETURN=0x3300000;SP=STACK+0x7000
class Oracle:
    def __init__(self):
        self.raw=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
        current=(ROOT.parent/'God2/God2.exe').read_bytes();require(sha(self.raw)==MAPPED_SHA and sha(current)==CLIENT_SHA,'Image pin changed')
        self.current=pefile.PE(data=current).get_memory_mapped_image()
        for start,end in ((0x12f170,0x12f4fd),(0x131c30,0x131c36)):
            require(self.raw[start:end]==self.current[start:end],'Current conversion code changed')
        self.vm=Uc(UC_ARCH_X86,UC_MODE_32);self.vm.mem_map(BASE,(len(self.raw)+4095)&~4095);self.vm.mem_write(BASE,self.raw)
        for address,size in ((STACK,0x8000),(INPUT,0x1000),(OUTPUT,0x1000),(RETURN,0x1000)):self.vm.mem_map(address,size)
        self.vm.mem_write(0x59dcd8,struct.pack('<I',1));self.vm.mem_write(0x6f4cb0,struct.pack('<I',1))
        self.apis={self.u32(address):name for address,name in ((0x5703b0,'MultiByteToWideChar'),(0x5703b4,'WideCharToMultiByte'),(0x5703b8,'LCMapStringA'),(0x570404,'GetLastError'))}
        for page in {address&~4095 for address in self.apis}:self.vm.mem_map(page,4096)
        for address in self.apis:self.vm.mem_write(address,b'\xc3')
        self.kernel=c.WinDLL('kernel32',use_last_error=True)
        self.mb=self.kernel.MultiByteToWideChar;self.mb.argtypes=[c.c_uint,c.c_uint,c.c_void_p,c.c_int,c.c_void_p,c.c_int];self.mb.restype=c.c_int
        self.wc=self.kernel.WideCharToMultiByte;self.wc.argtypes=[c.c_uint,c.c_uint,c.c_void_p,c.c_int,c.c_void_p,c.c_int,c.c_void_p,c.c_void_p];self.wc.restype=c.c_int
        self.lc=self.kernel.LCMapStringA;self.lc.argtypes=[c.c_uint,c.c_uint,c.c_void_p,c.c_int,c.c_void_p,c.c_int];self.lc.restype=c.c_int
        self.calls=[];self.instructions=set();self.last_error=0
        self.vm.hook_add(UC_HOOK_CODE,self.code)
    def u32(self,address):return struct.unpack('<I',self.vm.mem_read(address,4))[0]
    def string(self,address,width=1):
        for size in range(0,2048,width):
            if bytes(self.vm.mem_read(address+size,width))==bytes(width):return bytes(self.vm.mem_read(address,size+width))
        raise ValueError('OS adapter string exceeds2048bytes')
    def code(self,vm,address,size,_):
        if address==RETURN:vm.emu_stop();return
        if address not in self.apis:
            require((0x52f170<=address<0x52f4fd) or (0x531c30<=address<0x531c36),f'Unexpected native conversion callee{address:x}')
            offset=address-BASE;require(bytes(vm.mem_read(address,size))==self.current[offset:offset+size],'Current instruction mismatch')
            self.instructions.add(address);return
        name=self.apis[address];sp=vm.reg_read(x.UC_X86_REG_ESP);arg=lambda n:self.u32(sp+4+4*n)
        if name=='GetLastError':result=self.last_error;argc=0;record={'api':name,'result':result}
        else:
            page,flags=arg(0),arg(1);source=self.string(arg(2),2 if name=='WideCharToMultiByte' else 1)
            require(arg(3)==0xffffffff,'Native OS conversion must use NUL length')
            pointer,capacity=arg(4),arg(5);require(capacity<=2048,'Native OS output capacity')
            require(pointer==0 if capacity==0 else pointer!=0,'Native OS size-query shape')
            input_buffer=c.create_string_buffer(source);output_buffer=c.create_string_buffer(max(4096,capacity*2));used=c.c_int(0)
            c.set_last_error(0)
            if name=='MultiByteToWideChar':
                require(page in (936,950) and flags==0,'Native MB page/flags');argc=6
                result=self.mb(page,flags,input_buffer,-1,output_buffer if pointer else None,capacity)
                written=result*2
            elif name=='WideCharToMultiByte':
                require(page in (936,950) and flags==0 and arg(6)==0 and arg(7)==0,'Native WC page/flags');argc=8
                result=self.wc(page,flags,input_buffer,-1,output_buffer if pointer else None,capacity,None,c.byref(used));written=result
            else:
                require(page==0x804 and flags in (0x2000000,0x4000000),'Native LCMap locale/flags');argc=6
                result=self.lc(page,flags,input_buffer,-1,output_buffer if pointer else None,capacity);written=result
            self.last_error=c.get_last_error()
            if pointer and result:
                require((STACK<=pointer and pointer+written<=STACK+0x8000) or (OUTPUT<=pointer and pointer+written<=OUTPUT+256),'Native OS write outside bounded output')
                vm.mem_write(pointer,bytes(output_buffer.raw[:written]))
            record={'api':name,'codepage_or_locale':page,'flags':flags,'source_hex':source.hex(),'capacity':capacity,'result':result,'used_default':bool(used.value)}
        self.calls.append(record);vm.reg_write(x.UC_X86_REG_EAX,result);vm.reg_write(x.UC_X86_REG_ESP,sp+4+4*argc);vm.reg_write(x.UC_X86_REG_EIP,self.u32(sp))
    def run(self,source,page):
        require(page in (936,950) and len(source)<=15 and b'\0' not in source,'Bounded input required')
        self.calls=[];self.vm.mem_write(INPUT,source+b'\0');self.vm.mem_write(OUTPUT,bytes([0xcc])*256)
        self.vm.mem_write(SP,struct.pack('<III',RETURN,INPUT,OUTPUT));self.vm.reg_write(x.UC_X86_REG_ESP,SP);self.vm.reg_write(x.UC_X86_REG_EFLAGS,2)
        try:self.vm.emu_start(0x52f170 if page==950 else 0x52f330,RETURN,count=50000,timeout=1000000)
        except Exception as error:
            raise ValueError(f'Native codec fault pc={self.vm.reg_read(x.UC_X86_REG_EIP):x} source={source.hex()} calls={self.calls}') from error
        require(self.vm.reg_read(x.UC_X86_REG_EIP)==RETURN and self.vm.reg_read(x.UC_X86_REG_ESP)==SP+4,'Native conversion return/cdecl stack')
        require(self.vm.reg_read(x.UC_X86_REG_EAX)==1,'Native conversion reported failure')
        result=self.string(OUTPUT)[:-1];require(bytes(self.vm.mem_read(OUTPUT+len(result)+1,255-len(result)))==bytes([0xcc])*(255-len(result)),'Output suffix changed')
        return {'source_page':page,'recipient_page':936 if page==950 else 950,'source_hex':source.hex(),'output_hex':result.hex(),
            'output_text':result.decode('cp936' if page==950 else 'cp950'),'used_default':any(row.get('used_default') for row in self.calls),'os_calls':list(self.calls)}

def verify():
    oracle=Oracle();rows=[]
    for page,values in ((950,('', 'RoleNativeProof','神仙','測試','AB神仙CD','一一一一一一一A','繁體')),
                        (936,('', 'RoleNativeProof','神仙','测试','AB神仙CD','一一一一一一一A','简体','专'))):
        for text in values:rows.append(oracle.run(text.encode('cp'+str(page)),page))
    for page,before,after in ((950,'測試','测试'),(936,'测试','測試'),(950,'神仙','神仙'),(936,'神仙','神仙'),(936,'专','專')):
        row=next(r for r in rows if r['source_page']==page and bytes.fromhex(r['source_hex']).decode('cp'+str(page))==before)
        require(row['output_text']==after and not row['used_default'],'Native CJK conversion differs')
    return {'accepted':True,'client_sha256':CLIENT_SHA,'mapped_sha256':MAPPED_SHA,'vectors':rows,'vector_count':len(rows),
        'original_conversion_instruction_count':len(oracle.instructions),'native_enabled_globals':{'59dcd8':1,'6f4cb0':1},
        'adapter':'Actual host Windows NLS APIs at the captured original OS import boundaries; no game or conversion result stubs.',
        'actual_client_acceptance':False}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    result=verify();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:result[key] for key in ('accepted','vector_count','original_conversion_instruction_count')}));return 0
if __name__=='__main__':raise SystemExit(main())
