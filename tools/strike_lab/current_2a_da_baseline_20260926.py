"""Pinned native2A field slices and live-read offsets; no UI, socket or DB writes."""
import json
import struct
from .current_weapon_appearance_20260926 import Oracle, WORLD, STACK, SP, DATA
from .current_equipment_20260926 import PIN, require
from unicorn import x86_const as x

ROLE=WORLD+0x1539683c
COMPONENTS=WORLD+0xa7e04d0


def verify():
    n=Oracle();v=n.v
    v.mem_map(COMPONENTS&~4095,4096)
    cases=0
    values=[(i*257,i,255-i) for i in range(256)]
    values.extend((key,0x87,0xf9) for key in (1,255,256,0x3fff,0x4001,0xfffe))
    for transform,scalar5,scalar6 in values:
        # Deliberately synthetic inputs, not original starting appearance.
        body=bytearray((i*31+scalar5)&255 for i in range(36))
        struct.pack_into('<HBB',body,32,transform,scalar5,scalar6)
        wire=b'\x2a'+body
        guarded=b'\xcc'*32+wire+b'\xcc'*32
        v.mem_write(DATA,guarded)
        v.mem_write(STACK,b'\xa5'*0x10000)
        n.put(SP+0xc,SP+0x28);n.put(SP+0x10,36)
        v.reg_write(x.UC_X86_REG_ESP,SP);v.reg_write(x.UC_X86_REG_EAX,DATA+32)
        n.writes=()
        # Actual415690 copy loop after queue lookup; stop before queue removal.
        n.run(0x4156fc,(0x415718,),((0x4156fc,0x415718),))
        require(bytes(v.mem_read(SP+0x28,36))==body,'2A body copy mismatch')
        v.reg_write(x.UC_X86_REG_ESP,SP)
        v.reg_write(x.UC_X86_REG_EBP,ROLE);v.reg_write(x.UC_X86_REG_EBX,WORLD)
        v.mem_write(ROLE+0x4694,b'\xa5'*6)
        n.writes=((ROLE+0x4695,ROLE+0x4699),)
        n.run(0x46827b,(0x468290,),((0x46827b,0x468290),))
        n.run(0x468558,(0x468564,),((0x468558,0x468564),))
        require(bytes(v.mem_read(ROLE+0x4694,6))==
            b'\xa5'+bytes((scalar5,))+struct.pack('<H',transform)+bytes((scalar6,0xa5)),
            'Native2A scalar sources/canaries differ')
        n.writes=((ROLE+0x4584,ROLE+0x458c),(ROLE+0x28,ROLE+0x2c))
        n.run(0x468328,(0x46834b,),((0x468328,0x46834b),))
        require(bytes(v.mem_read(ROLE+0x4584,8))==body[12:20],'Native2A saved component mismatch')
        # Actual identity mask in2A; DA itself must not re-mask its WORD.
        v.reg_write(x.UC_X86_REG_EAX,struct.unpack_from('<I',body)[0])
        n.writes=((ROLE,ROLE+8),)
        n.run(0x46861f,(0x468636,),((0x46861f,0x468636),))
        require(struct.unpack('<I',v.mem_read(ROLE,4))[0]==struct.unpack_from('<I',body)[0]&0x3fff,
                'Native2A identity mismatch')
        require(bytes(v.mem_read(DATA,len(guarded)))==guarded,'2A input/canary changed')
        cases+=1
    # Qualify exact readback offsets by executing both actual setters to return.
    v.mem_write(COMPONENTS,b'\xa5'*32)
    expected=bytearray(b'\xa5'*32)
    n.writes=((COMPONENTS,COMPONENTS+32),)
    for component,(handle,variant) in enumerate(((0,0),(1,3),(511,6),(0xffff,7))):
        n.call(0x4ff450,(component,handle),((0x4ff450,0x4ff46d),),this=COMPONENTS)
        n.call(0x4ffa20,(component,variant),((0x4ffa20,0x4ffa3b),),this=COMPONENTS)
        struct.pack_into('<H',expected,4+6*component,handle)
        expected[8+6*component]=variant
        require(bytes(v.mem_read(COMPONENTS,32))==expected,'Component readback offsets/canary mismatch')
        cases+=1
    return {'status':'PASS','cases':cases,'client_sha256':PIN,
        'body_copy_scalar_component_identity_cases':262,'native_component_setter_cases':4,
        'body_offsets':{'transform_key_le16':32,'raw_scalar5':34,'raw_scalar6':35,'components8':12},
        'scope':'Segmented native2A queue-copy/field stores and real setter returns. No world initialization, transform-resource eligibility or full DA renderer acceptance.'}


if __name__=='__main__':print(json.dumps(verify(),indent=2))
