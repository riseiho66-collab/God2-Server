"""Original MED02 nonzero-slot producers and 41/24 response consumers.

Synthetic owned state, current source definitions; no native server healing,
debit/cap authority claim and no process/network/UI or database access.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from .current_weapon_fresh_tooltip_20260926 import FreshTooltip
from .current_equipment_projection_20260926 import (
    NativeItemMetadata, ROOT, PIN, require, pefile, BASE, UI, SLOTS, COMPANION,
    PACKET, SP, LENGTH, QUEUE, DEFINITIONS, x)
from unicorn import UC_HOOK_CODE

WORLD=UI-0xa7f2f6c
ACTOR=WORLD+0x1539683c
ROLE=ACTOR+0x90


class SupplyOracle(FreshTooltip):
    def __init__(self,image,definitions):
        super().__init__(image,{k:definitions[k] for k in (1,2)})
        v=self.vm
        v.mem_protect(DEFINITIONS,0xe0000,3)
        for ordinal,key in enumerate((3101,3107)):
            at=COMPANION+0x3000+ordinal*0x1000
            v.mem_write(at,definitions[key]['record'])
            v.mem_write(DEFINITIONS+0xb2d40+4*key,struct.pack('<I',at))
        v.mem_protect(DEFINITIONS,0xe0000,1)
        v.mem_map(ACTOR&~4095,0x6000)
        v.mem_write(UI+0x8688c,struct.pack('<I',ACTOR))
        v.mem_write(UI+0x86888,struct.pack('<I',ROLE))
        v.mem_write(ACTOR,struct.pack('<I',4))
        for off in (0x232dda,0x232dc8,0x232dea,0x232e20,0x232e52):v.mem_write(UI+off,b'\xff\xff')
        v.mem_write(UI+0x232e50,struct.pack('<h',1)) # valid HUD, absent renderer
        v.mem_write(ROLE+0xd4,b'\x02')
        for i in range(2):
            god=bytearray([0x31+i]*0x3ec)
            struct.pack_into('<H',god,0,101+i)
            struct.pack_into('<II',god,0x2c,37+i,100+i)
            v.mem_write(ROLE+0xd8+i*0x3ec,bytes(god))
        v.mem_write(ROLE+0xd0,struct.pack('<I',ROLE+0xd8))
        v.mem_write(COMPANION,bytes((i*7+3)&255 for i in range(216)))
        for slot in (42,43,44):self.put(slot,struct.pack('<HH',400+slot,32)+bytes([slot])*16)

    def bounded(self,start,stop,budget=500000):
        hook=self.vm.hook_add(UC_HOOK_CODE,lambda v,a,s,c:v.emu_stop(),begin=stop,end=stop)
        try:self.vm.emu_start(start,stop,count=budget)
        finally:self.vm.hook_del(hook)
        require(self.vm.reg_read(x.UC_X86_REG_EIP)==stop,'Native bounded return/budget')

    def reset_queue(self,poison=0xa5):
        self.vm.mem_write(LENGTH,bytes(4))
        self.vm.mem_write(SP-0x400,bytes([poison])*0x400)

    def queue(self):
        size=struct.unpack('<I',self.vm.mem_read(LENGTH,4))[0]
        require(size<100,'Queue size');return bytes(self.vm.mem_read(QUEUE,size))

    def cached_inventory(self,slot):
        v=self.vm;data=bytes(v.mem_read(SLOTS+slot*24+4,20));key=struct.unpack_from('<H',data)[0]
        px=struct.unpack_from('<h',self.image,0x1901c0+16*slot)[0]
        py=struct.unpack_from('<h',self.image,0x1901c4+16*slot)[0]
        v.mem_write(BASE+0x1b6810,bytes(8));v.mem_write(BASE+0x1926b2,struct.pack('<hh',px,py))
        v.mem_write(BASE+0x1b7830,struct.pack('<H',key));v.mem_write(BASE+0x1b7838,data)
        self.call(0x9a330,slot,4,budget=500000)
        require(not self.queue(),'Inventory click must await target')
        require(bytes(v.mem_read(UI+0x85600,4))==struct.pack('<HBB',key,slot,1),'Target-selection binding')
        require(struct.unpack('<H',v.mem_read(UI+0x232f36,2))[0]==7,'Target cursor mode7')

    def companions(self):
        v=self.vm
        return dict(gods=bytes(v.mem_read(ROLE+0xd8,2*0x3ec)).hex(),
                    selected=bytes(v.mem_read(ROLE+0xd0,5)).hex(),
                    pet_slots=bytes(v.mem_read(SLOTS+42*24,3*24)).hex(),
                    pet_cache=bytes(v.mem_read(COMPANION,216)).hex())


def verify():
    raw=(ROOT.parent/'God2/God2.exe').read_bytes()
    require(hashlib.sha256(raw).hexdigest()==PIN,'Current EXE pin')
    image=pefile.PE(data=raw).get_memory_mapped_image();loader=NativeItemMetadata()
    require(all(image[a:b]==loader.image[a:b] for a,b in loader.CODE),'Current definition parser identity')
    definitions={k:loader.item_row('WPN',k-1) for k in (1,2)}
    definitions.update({k:loader.item_row('MED02',k-3101) for k in (3101,3107)})
    require(definitions[3101]['record'][0x11a:0x11c]==bytes.fromhex('fb07'),'HP source flags')
    require(definitions[3107]['record'][0x11a:0x11c]==bytes.fromhex('fb01'),'MP source flags')
    n=SupplyOracle(image,definitions);v=n.vm;requests=[]
    for key,slot in ((3101,5),(3107,12)):
        n.put(slot,struct.pack('<HH',key,4)+bytes(16),3)
        n.reset_queue();before=bytes(v.mem_read(SLOTS,1200));n.cached_inventory(slot)
        n.call(0x66490,0xfffffff4,3,this=WORLD,budget=500000)
        request=n.queue()
        require(len(request)==7 and request[:6]==struct.pack('<BHHB',0x26,4,key,slot),'Inventory self target dispatcher')
        require(bytes(v.mem_read(SLOTS,1200))==before,'Producer must not debit')
        requests.append(dict(path='inventory cached hover -> mode7 -> world self target',key=key,slot=slot,wire_hex=request.hex()))
        # Actual shortcut dispatcher kind0 ->963C0: two different signed-count
        # duplicate slots prove descending search and rejection of count128.
        for duplicate_count,expected_slot in ((1,29),(127,29),(0,slot),(128,slot),(255,slot)):
            n.put(29,struct.pack('<HH',key,4)+bytes(16),duplicate_count)
            v.mem_write(UI+0xa3d08,bytes(4));v.mem_write(UI+0xa3d18,struct.pack('<HHH',0,key,0))
            n.reset_queue(0x5a);n.call(0xae520,0,budget=500000);request=n.queue()
            require(len(request)==7 and request[:6]==struct.pack('<BHHB',0x26,4,key,expected_slot),'Shortcut descending signed count selection')
            requests.append(dict(path='shortcut kind0 ->963C0',key=key,duplicate_count=duplicate_count,selected_slot=expected_slot,wire_hex=request.hex()))
        n.put(29,bytes(20),0)
    # A shortcut copies the actor's stored WORD as-is; no producer-side mask.
    identities=[]
    for actor_word in (1,4,0x3fff,0x4001,0xffff):
        v.mem_write(ACTOR,struct.pack('<I',actor_word));n.reset_queue();n.call(0xae520,0,budget=500000)
        require(struct.unpack_from('<H',n.queue(),1)[0]==actor_word,'Actor WORD preservation')
        identities.append(dict(actor_word=actor_word,wire_hex=n.queue().hex()))
    v.mem_write(ACTOR,struct.pack('<I',4))
    blocked=[]
    v.mem_write(UI+0x866e4,b'\x01')
    for entry,args in ((0xae520,(0,)),(0x964d0,(4,))):
        n.reset_queue();n.call(entry,*args,budget=500000)
        require(not n.queue(),'Native UI gate must block item request')
        blocked.append(hex(BASE+entry))
    v.mem_write(UI+0x866e4,b'\x00')
    responses=[]
    for key,slot,before,after,count in (
        (3101,5,(20,120,2,80),(120,120,2,80),2),
        (3101,5,(119,120,52,80),(120,120,52,80),1),
        (3107,12,(120,120,2,80),(120,120,52,80),2),
        (3107,12,(120,120,52,80),(120,120,80,80),0)):
        v.mem_write(ROLE+0x5c,struct.pack('<4I',*before));n.put(slot,struct.pack('<HH',key,4)+bytes(16),3)
        before_companions=n.companions();slot_before=bytes(v.mem_read(SLOTS+24*slot,24))
        occupancy=struct.pack('<BHBB',0x41,key,slot,count)
        v.mem_write(PACKET,occupancy);n.call(0x991e0,PACKET+1,budget=500000)
        expected=bytearray(slot_before);expected[0]=count;expected[4:6]=struct.pack('<H',key if count else 0)
        require(bytes(v.mem_read(SLOTS+24*slot,24))==expected,'41 absolute count/key with retained metadata')
        hp,maxhp,mp,maxmp=after;wire=bytes([0x24])+struct.pack('<4I',hp,mp,maxhp,maxmp)
        v.mem_write(PACKET,wire);v.reg_write(x.UC_X86_REG_EBP,WORLD);v.reg_write(x.UC_X86_REG_EBX,PACKET);v.reg_write(x.UC_X86_REG_ESP,SP)
        n.bounded(0x469f4d,0x46b517)
        require(bytes(v.mem_read(ROLE+0x5c,16))==struct.pack('<4I',*after),'24 final resources')
        require(n.companions()==before_companions,'41/24 modified God/pet state')
        responses.append(dict(key=key,slot=slot,before=list(before),after=list(after),count_after=count,
            wire_hex=(occupancy+wire).hex(),god_and_pet_all_bytes_unchanged=True))
    # Neutral vitals replay qualifies the consumer only. A server cap no-op
    # sends neither41 nor24; that no-send policy belongs to server/UI tests.
    at_cap=(120,120,80,80)
    v.mem_write(ROLE+0x5c,struct.pack('<4I',*at_cap))
    before_companions=n.companions();before_slots=bytes(v.mem_read(SLOTS,1200))
    v.mem_write(PACKET,bytes([0x24])+struct.pack('<4I',120,80,120,80))
    v.reg_write(x.UC_X86_REG_EBP,WORLD);v.reg_write(x.UC_X86_REG_EBX,PACKET);v.reg_write(x.UC_X86_REG_ESP,SP)
    n.bounded(0x469f4d,0x46b517)
    require(n.companions()==before_companions and bytes(v.mem_read(SLOTS,1200))==before_slots,'Neutral24 at cap changed companions/inventory')
    require(bytes(v.mem_read(ROLE+0x5c,16))==struct.pack('<4I',*at_cap),'Neutral24 at cap changed resources')
    # Counterexample is deliberate: stale/lower outgoingHP damages active God.
    v.mem_write(ROLE+0x5c,struct.pack('<4I',100,120,20,80))
    v.mem_write(ROLE+0xd8+0x2c,struct.pack('<I',37))
    v.mem_write(PACKET,struct.pack('<4I',90,20,120,80))
    n.call(0xe71e0,PACKET,0,0,0,budget=500000)
    require(struct.unpack('<I',v.mem_read(ROLE+0xd8+0x2c,4))[0]==27,'Negative control God HP loss')
    require({0x9a330,0x834e0,0x66490,0x964d0,0xae520,0x963c0,0x132e0,0x991e0,0xe71e0,0xe72d0,0xac070,0xe6db0}.issubset(n.pcs),'Original callee coverage')
    return dict(status='PASS',current_pe_sha256=PIN,requests=requests,actor_words=identities,responses=responses,blocked_entries=blocked,
        counts={'producer_vectors':len(requests)+len(identities),'blocked_producers':len(blocked),'full_response_pairs':len(responses),'neutral_full24':1,'negative_controls':1},
        source_rows={str(k):{'line':definitions[k]['source_line'],'native_flags':definitions[k]['record'][0x11a:0x11c].hex(),
            'record_sha256':hashlib.sha256(definitions[k]['record']).hexdigest()} for k in (3101,3107)},
        scope='Original cached-tooltip inventory activation, self target dispatcher and shortcut dispatcher; full41 and24 consumers with initialized absent-renderer HUD. Synthetic God/pet/state and cap operands. No full OS hit-test/keyboard, fresh potion tooltip, renderer or server healing/debit authority.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args();result=verify()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);temporary=args.output.with_suffix(args.output.suffix+'.pending')
        temporary.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(args.output)
    print(json.dumps(result if not args.output else {'status':result['status'],'counts':result['counts'],'output':str(args.output)},ensure_ascii=True))
