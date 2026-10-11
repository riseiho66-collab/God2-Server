"""Complete native fresh tooltip for synthetic restricted TWP operands."""
import hashlib,json,struct
from . import current_weapon_fresh_tooltip_20260926 as f

def verify():
    raw=(f.ROOT.parent/'God2/God2.exe').read_bytes()
    f.require(hashlib.sha256(raw).hexdigest()==f.PIN,'Current PE mismatch')
    image=f.pefile.PE(data=raw).get_memory_mapped_image();loader=f.NativeItemMetadata()
    f.require(all(image[a:b]==loader.image[a:b] for a,b in loader.CODE),'Metadata code mismatch')
    definitions={1:loader.item_row('WPN',0),2:loader.item_row('WPN',1),
        19071:loader.item_row('TWP',70),19072:loader.item_row('TWP',71)}
    n=f.FreshTooltip(image,definitions);v=n.vm;cases=[]
    for key in (19071,19072):
        data=struct.pack('<HH',key,25)+bytes(16)
        expected_name=definitions[key]['record'][8:46].split(b'\0')[0]
        restriction=definitions[key]['record'][46:276].split(b'\0')[0]
        for event in (0,4):
            n.put(1,data);before=bytes(v.mem_read(f.SLOTS,1200))
            v.mem_write(f.BASE+0x1b7830,b'\xff\xff');v.mem_write(f.BASE+0x1b7838,b'\xa5'*20)
            v.mem_write(n.tooltip_node,struct.pack('<H',0x11))
            v.mem_write(f.LENGTH,bytes(4));v.mem_write(f.QUEUE,b'\xa5'*16)
            n.formatted=[];n.weapon_output=[];n.fresh_visits=set()
            n.call(0x9a330,1,event,budget=500000)
            f.require(not n.weapon_frames and len(n.weapon_output)==1,'Native fresh formatter incomplete')
            f.require({0x9a330,0x9b820,0xb5be0,0xb45b0,0xb4200}.issubset(n.fresh_visits),'Required native branch absent')
            texts=[bytes.fromhex(row['raw_hex']) for row in n.formatted]
            f.require(any(expected_name in text for text in texts),'Source name not formatted')
            f.require(any(restriction in text for text in texts),'Source restriction not formatted')
            f.require(bytes(v.mem_read(f.BASE+0x1b7838,20))==data,'Fresh cache input mismatch')
            f.require(struct.unpack('<H',v.mem_read(n.tooltip_node,2))[0]&0x20,'Tooltip did not open')
            f.require(bytes(v.mem_read(f.SLOTS,1200))==before,'Native request mutated inventory')
            expected=struct.pack('<BHBB',0x28,key,1,1) if event==4 else b''
            length=struct.unpack('<I',v.mem_read(f.LENGTH,4))[0]
            f.require(length==len(expected) and bytes(v.mem_read(f.QUEUE,length))==expected,'Wrong native28')
            cases.append(dict(key=key,event=event,instance_hex=data.hex(),request_hex=expected.hex(),
                formatter_hex=n.weapon_output[0].hex(),controls=n.formatted,
                fresh_cache_miss=True,native_return=True,source_description_hex=restriction.hex()))
    return dict(status='PASS',client_sha256=f.PIN,instance_origin='CUSTOM_TEST_NOT_NATIVE',
        native_game_stubs=0,cases=cases,scope='Fresh native formatter and request return only; no legal generation, original stats, live pixel or renderer claim.')

if __name__=='__main__':print(json.dumps(verify(),indent=2))
