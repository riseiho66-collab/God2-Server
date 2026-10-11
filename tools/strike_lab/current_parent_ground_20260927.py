"""Qualified parent-map ground pixels; live access is VM_READ only.

World kind1 is not map-manager kind1: successful parent MDL loading at
444F04..444F11 calls 4467F0(0), whose 44680D writes manager+30=0.
The non-indoor world entry at 50054D..50078A uses 449330 as town does.
No live code executes here; Unicorn verification uses an isolated fixture VM.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
IMAGE=ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin'
IMAGE_SHA='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
CLIENT=ROOT.parent/'God2/God2.exe'
CLIENT_SHA='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'

def ground_observation(handle,state,x,y,*,read):
    """Use the owned client's manager origin and camera, fail on wrong binding."""
    if (state['area'],state['scene'],state['kind']) not in ((2,0,1),(4,0,1)):
        raise AssertionError('UNQUALIFIED_PARENT_WORLD_KIND')
    if not (0<=x<0x4000 and 0<=y<=0x7fff):
        raise AssertionError('PARENT_COORDINATE_BOUNDS')
    bridge=struct.unpack('<I',read(handle,state['world']+0xa7e05dc,4))[0]
    manager=struct.unpack('<I',read(handle,bridge+0xbc,4))[0]
    kind=struct.unpack('<I',read(handle,manager+0x30,4))[0]
    if kind!=0:raise AssertionError('PARENT_MDL_MANAGER_NOT_OUTDOOR')
    ox,oy=struct.unpack('<2i',read(handle,manager+0x103c,8))
    lx,ly=x-ox,y-oy
    # The original getter indexes lx+21, ly+21 into its 63x63 window.
    if not (-21<=lx<42 and -21<=ly<42):raise AssertionError('PARENT_TARGET_OUTSIDE_LOADED_WINDOW')
    # Original 49330 ->49B30 for the manager's 63x63 outdoor window.
    # (+40,+20) is a tile interior; original493C0 verifies it below.
    pixel=(40*(lx+ly)+40-state['camera'][0],
           20*(ly-lx)+420-state['camera'][1])
    if not (160<=pixel[0]<630 and 120<=pixel[1]<440):
        raise AssertionError('PARENT_GROUND_NOT_VISIBLE')
    return {'pixel':list(pixel),'world_kind':1,'manager_kind':kind,
            'manager':hex(manager),'origin':[ox,oy],'camera':state['camera'],
            'target':[x,y],'projection_rva':'49330','inverse_rva':'493c0'}

def ground_point(handle,state,x,y,*,read=None):
    if read is None:
        from .private_weapon_peer_appearance_20260927 import exact
        read=exact
    return tuple(ground_observation(handle,state,x,y,read=read)['pixel'])

def verify():
    """Execute full original projection/inverse with no replacement hooks."""
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_ESP,UC_X86_REG_EIP
    raw=IMAGE.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=IMAGE_SHA:raise AssertionError('MAPPED_IMAGE_PIN')
    import pefile
    client_raw=CLIENT.read_bytes()
    if hashlib.sha256(client_raw).hexdigest()!=CLIENT_SHA:raise AssertionError('CURRENT_CLIENT_PIN')
    pe=pefile.PE(data=client_raw,fast_load=True)
    spans=((0x49330,0x120),(0x49b30,0x38),(0x49950,0x162),
           (0x44f04,0x12),(0x467f0,0x29),(0x10054d,0x30))
    for rva,size in spans:
        offset=pe.get_offset_from_rva(rva)
        if client_raw[offset:offset+size]!=raw[rva:rva+size]:
            raise AssertionError('CURRENT_CLIENT_NATIVE_SPAN_MISMATCH')
    vm=Uc(UC_ARCH_X86,UC_MODE_32);base=0x400000
    vm.mem_map(base,(len(raw)+4095)&~4095);vm.mem_write(base,raw)
    manager=0x7000000;stack=0x7100000;out=0x7200000;stop=0x7300000
    for p,n in ((manager,0x2000),(stack,0x10000),(out,0x1000),(stop,0x1000)):vm.mem_map(p,n)
    sp=stack+0x8000
    vm.mem_write(manager+0x30,struct.pack('<I',0))
    # Getter46FF0 requires a non-null center block; never dereferences that
    # pointer on this qualified kind0 branch. Fill the actual native63x63 pool.
    vm.mem_write(manager+0xfdc+4*4,struct.pack('<I',out))
    vm.mem_write(manager+0x103c,struct.pack('<2i',100,100))
    vm.mem_write(manager+0x50,b'\x5a'*(63*63))
    window_bounds=[]
    for x,y,expected in ((79,79,0x5a),(141,141,0x5a),(78,100,0),
                         (142,100,0),(100,78,0),(100,142,0)):
        vm.reg_write(UC_X86_REG_ECX,manager);vm.reg_write(UC_X86_REG_ESP,sp)
        vm.mem_write(sp,struct.pack('<3I',stop,x,y))
        vm.emu_start(base+0x46ff0,stop,count=1000)
        actual=vm.reg_read(UC_X86_REG_EAX)
        if actual!=expected or vm.reg_read(UC_X86_REG_EIP)!=stop or vm.reg_read(UC_X86_REG_ESP)!=sp+12:
            raise AssertionError('ORIGINAL_PARENT_WINDOW_BOUND_MISMATCH')
        window_bounds.append({'point':[x,y],'relative':[x-100,y-100],'native_cell':actual})
    def call(rva,a,b):
        vm.reg_write(UC_X86_REG_ECX,manager);vm.reg_write(UC_X86_REG_ESP,sp)
        vm.mem_write(sp,struct.pack('<5I',stop,a&0xffffffff,b&0xffffffff,out,out+4))
        vm.emu_start(base+rva,stop,count=2000)
        if vm.reg_read(UC_X86_REG_EIP)!=stop or vm.reg_read(UC_X86_REG_ESP)!=sp+20:
            raise AssertionError('NATIVE_PROJECTION_CALL_BOUND')
        return struct.unpack('<2i',vm.mem_read(out,8))
    samples=[]
    for origin,target in (((462,189),(475,209)),((462,189),(476,209)),
                          ((462,189),(477,209)),((294,336),(318,363)),
                          ((21,21),(0,0)),((0,0),(41,41))):
        lx,ly=target[0]-origin[0],target[1]-origin[1]
        projected=call(0x49330,lx,ly)
        expected=(40*(lx+ly),20*(ly-lx)+400)
        if projected!=expected:raise AssertionError('ORIGINAL_PARENT_PROJECTION_MISMATCH')
        interior=(projected[0]+40,projected[1]+20)
        recovered=call(0x493c0,*interior)
        if recovered!=(lx,ly):raise AssertionError('ORIGINAL_PARENT_INVERSE_MISMATCH')
        for camera in ((0,0),(880,60),(-120,80)):
            pixel=(interior[0]-camera[0],interior[1]-camera[1])
            if call(0x493c0,pixel[0]+camera[0],pixel[1]+camera[1])!=(lx,ly):
                raise AssertionError('ORIGINAL_PARENT_CAMERA_ROUNDTRIP')
        samples.append({'origin':origin,'target':target,'native_boundary':projected,'native_interior':interior,'native_inverse':recovered})
    return {'accepted':True,'mapped_image_sha256':IMAGE_SHA,'client_sha256':CLIENT_SHA,
            'current_client_native_spans':[{'rva':hex(rva),'size':size,'matched':True} for rva,size in spans],
            'loaded_window_relative_bounds':[-21,41], 'world_kind':1,'manager_kind':0,
            'native_getter_rva':'46ff0','native_window_bounds':window_bounds,
            'binding_source':'50054d(non2)->46c520->444b80;444f08(push0)->4467f0->44680d',
            'native_functions':['449330','4493c0','449b30','449950'],
            'sample_count':len(samples),'camera_roundtrips':len(samples)*3,'samples':samples,
            'live_client_tested':False,'rendered_pixels_tested':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args()
    result=verify();text=json.dumps(result,indent=2)+'\n'
    if a.output:a.output.write_text(text,encoding='utf-8')
    print(text)
