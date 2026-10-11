"""Original1C arrival identity/config producer, offline VM fixtures only."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/research'))
import test_current_route_advertisement as routes
from tools.strike_lab.current_battle_entry import NativeRun,SP,NET,WORLD
from unicorn import UC_PROT_READ,UC_PROT_WRITE
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP

def verify():
    image=(ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    if hashlib.sha256(image).hexdigest()!=routes.IMAGE_SHA:raise AssertionError('IMAGE_PIN')
    client=(ROOT.parent/'God2/God2.exe').read_bytes();client_sha=hashlib.sha256(client).hexdigest()
    if client_sha!='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98':raise AssertionError('CLIENT_PIN')
    import pefile
    pe=pefile.PE(data=client,fast_load=True)
    spans=((0x157f0,0x49),(0x131c10,0x1d),(0x6c4e2,0x1a),
           (0x65520,0x12),(0x65de9,0xe))
    for r,s in spans:
        off=pe.get_offset_from_rva(r)
        if client[off:off+s]!=image[r:r+s]:raise AssertionError('NATIVE_SPAN_MISMATCH')
    test=routes.CurrentRouteAdvertisementTests();test.image=image
    outputs=[]
    for config in (0,1):
        for identity in (1,2,4,0x3fff):
            vm=test.vm();vm.mem_protect(0x59d000,4096,UC_PROT_READ|UC_PROT_WRITE)
            vm.mem_write(0x59dfd8,struct.pack('<HH',4,2 if config else 0))
            vm.mem_write(routes.NET+0x36c4,bytes(4))
            # Full4157F0,531C10 and queue132E0, no stubs.
            test.call(vm,0x157f0,identity,this=routes.NET)
            size=struct.unpack('<I',vm.mem_read(routes.NET+0x36c4,4))[0]
            logical=bytes(vm.mem_read(routes.NET+0x36c8,size))
            expected=bytes([0x1c])+struct.pack('<HH',identity,config)
            if logical!=expected:raise AssertionError('ARRIVAL_IDENTITY_CONFIG_MISMATCH')
            outputs.append({'local_id':identity,'config':config,'logical_hex':logical.hex()})
    caller=[]
    for identity,send in ((2,0),(2,1),(4,1)):
        n=NativeRun();n.map(WORLD+0x1539683c,4);n.map(WORLD+0xa7e05e0,4)
        n.put32(WORLD+0x1539683c,identity);n.put32(WORLD+0xa7e05e0,NET)
        n.put32(SP+0x44,send);n.registers(esi=WORLD)
        n.run(0x6c4e2,((0x6c4e2,0x6c4fc),),{0x157f0,0x6c4fc})
        sp=n.vm.reg_read(UC_X86_REG_ESP)
        reached=n.stop==0x157f0
        if reached!=(send!=0):raise AssertionError('TRANSFER_RECEIPT_CALLER_GATE')
        supplied=n.get32(sp+4) if reached else None
        if reached and supplied!=identity:raise AssertionError('TRANSFER_CALLER_IDENTITY')
        caller.append({'local_id':identity,'second_argument_nonzero':bool(send),
                       'producer_reached':reached,'producer_argument':supplied})
    return {'accepted':True,'current_client_sha256':client_sha,'mapped_image_sha256':routes.IMAGE_SHA,
        'native_spans':[{'rva':hex(r),'size':s,'matched':True} for r,s in spans],
        'producer_vectors':outputs,'transfer_caller_vectors':caller,
        'meaning':'payload.lowWORD=local character ID, highWORD=531C10 config; neither is a literal caller type',
        'stubs_used':False,'live_client_tested':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args()
    r=verify();text=json.dumps(r,indent=2)+'\n'
    if a.output:a.output.write_text(text,encoding='utf-8')
    print(text)
