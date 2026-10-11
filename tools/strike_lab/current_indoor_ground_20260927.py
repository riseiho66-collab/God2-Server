"""Current original indoor projection/inverse on every registered room point.

Runs only the pinned original code in an isolated Unicorn VM, never a client.
Native extents at indoor+90/+94 are grid extents, not base-HMD width.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from .current_parent_ground_20260927 import ROOT,IMAGE,IMAGE_SHA,CLIENT,CLIENT_SHA

def verify():
    import pefile
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP
    raw=IMAGE.read_bytes();client=CLIENT.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==IMAGE_SHA
    assert hashlib.sha256(client).hexdigest()==CLIENT_SHA
    pe=pefile.PE(data=client,fast_load=True)
    spans=((0x49330,0x120),(0x49b30,0x38),(0x49950,0x162))
    for rva,size in spans:
        offset=pe.get_offset_from_rva(rva)
        assert client[offset:offset+size]==raw[rva:rva+size]
    vm=Uc(UC_ARCH_X86,UC_MODE_32);base=0x400000
    vm.mem_map(base,(len(raw)+4095)&~4095);vm.mem_write(base,raw)
    manager=0x7000000;indoor=0x7100000;stack=0x7200000;out=0x7300000;stop=0x7400000
    for address in (manager,indoor,stack,out,stop):vm.mem_map(address,0x2000)
    vm.mem_write(manager+0x30,struct.pack('<I',2))
    vm.mem_write(manager+0x1030,struct.pack('<I',indoor));sp=stack+0x1000
    def call(rva,a,b):
        vm.reg_write(UC_X86_REG_ECX,manager);vm.reg_write(UC_X86_REG_ESP,sp)
        vm.mem_write(sp,struct.pack('<5I',stop,a&0xffffffff,b&0xffffffff,out,out+4))
        vm.emu_start(base+rva,stop,count=2000)
        assert vm.reg_read(UC_X86_REG_EIP)==stop and vm.reg_read(UC_X86_REG_ESP)==sp+20
        return struct.unpack('<2i',vm.mem_read(out,8))
    samples=[];sources=[]
    for filename in ('town-doors-2.json','kunlun-doors-4.json'):
        path=ROOT/'artifacts/world-atlas'/filename;encoded=path.read_bytes();bundle=json.loads(encoded)
        sources.append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(encoded).hexdigest()})
        navigation={row['scene']:row for row in bundle['navigation']}
        for route in bundle['routes']:
            side=navigation[route['scene']]['grid']['side']
            vm.mem_write(indoor+0x90,struct.pack('<2I',side,side))
            for index,pair in enumerate(route['pairs']):
                for field in ('indoor_arrival','indoor_trigger'):
                    x,y=pair[field];assert 0<=x<side and 0<=y<side
                    native=call(0x49330,x,y)
                    expected=(40*(x+y),20*(((side+1)//2)*2-2-x+y))
                    assert native==expected
                    interior=(native[0]+40,native[1]+20)
                    assert call(0x493c0,*interior)==(x,y)
                    for camera in ((0,0),(880,60),(-120,80)):
                        pixel=(interior[0]-camera[0],interior[1]-camera[1])
                        assert call(0x493c0,pixel[0]+camera[0],pixel[1]+camera[1])==(x,y)
                    samples.append({'area':bundle['area'],'scene':route['scene'],'pair':index,
                                    'field':field,'side':side,'point':[x,y],'native':native})
    return {'accepted':True,'client_sha256':CLIENT_SHA,'mapped_image_sha256':IMAGE_SHA,
            'source_bundles':sources,'native_spans':[{'rva':hex(r),'size':n} for r,n in spans],
            'sample_count':len(samples),'camera_roundtrips':3*len(samples),'samples':samples,
            'live_client_tested':False,'rendered_pixels_tested':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=verify()
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:result[key] for key in ('accepted','sample_count','camera_roundtrips')}))
