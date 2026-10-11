"""Bounded offline teleport-item producer qualification, no live client/server.

Native ItemType/SPI parsers produce records. Owned-slot shortcut runs fully;
inventory-use event runs with only the tooltip presentation call adapted away.
All request branches, metadata lookup, producers and queue execute native code.
UI and ownership state are fixtures, not actual-client activation acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/research'))
from tools.strike_lab.current_deity_metadata import NativeDeityMetadata
from tools.strike_lab.recover_companion_growth import fields
import test_current_inventory as inv
from unicorn import UC_HOOK_CODE

class TeleportItems(NativeDeityMetadata):
    ITEM_SECTIONS=('GOD','SPI')
    def section_selector(self,section):return self.lookup_section(section)[1]

def verify():
    n=TeleportItems();rows=n.sections['SPI']['records']
    image=n.image
    client=ROOT.parent/'God2/God2.exe';raw=client.read_bytes()
    client_sha='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
    if hashlib.sha256(raw).hexdigest()!=client_sha:raise AssertionError('CURRENT_CLIENT_PIN')
    import pefile
    pe=pefile.PE(data=raw,fast_load=True)
    spans=((0x9a330,0x390),(0x96390,0x30),(0x963c0,0x100),(0x96350,0x33),
           (0x132e0,0x72),(0x103ad0,0x24),(0x10e7d0,0x10),
           (0x67860,0x200),(0x101810,0x80),(0xa6760,0x600))
    for rva,size in spans:
        off=pe.get_offset_from_rva(rva)
        if raw[off:off+size]!=image[rva:rva+size]:raise AssertionError('CURRENT_NATIVE_SPAN')
    test=inv.CurrentInventoryTests();test.image=image
    outputs=[]
    for key in (5571,5601,5605,5609):
        index=next(i for i,row in enumerate(rows) if fields(row)[0]==str(key).encode())
        parsed=n.item_row('SPI',index);record=parsed['record']
        if record[0x11a]!=0xf1:raise AssertionError('CURRENT_TELEPORT_ITEM_FLAGS')
        observations=[]
        for slot,route in ((0,'owned_slot'),(29,'owned_slot'),(0,'inventory_use_event')):
            vm=test.consumer_vm();resource,item=0x3800000,0x38bf000
            vm.mem_map(resource,0xc0000)
            vm.mem_write(resource+0xb2d40+4*key,struct.pack('<I',item));vm.mem_write(item,record)
            vm.mem_write(inv.UI+0xcff70,struct.pack('<I',resource))
            vm.mem_write(inv.UI+0x866e4,bytes(4))
            vm.mem_write(inv.UI+0x86874,struct.pack('<I',inv.routes.NET))
            vm.mem_write(inv.UI+0x8688c,struct.pack('<I',inv.MANAGER+0x100))
            vm.mem_write(inv.MANAGER+0x100,struct.pack('<H',4))
            for offset in (0x232dfe,0x232dda):vm.mem_write(inv.UI+offset,b'\xff\xff')
            vm.mem_write(inv.SLOTS,bytes(50*24))
            vm.mem_write(inv.SLOTS+24*slot,b'\x01')
            vm.mem_write(inv.SLOTS+24*slot+4,struct.pack('<H',key))
            vm.mem_write(inv.routes.NET+0x36c4,bytes(4))
            seen=[]
            vm.hook_add(UC_HOOK_CODE,lambda uc,address,size,data:seen.append(address))
            if route=='inventory_use_event':
                from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_ESP,UC_X86_REG_EIP
                def tooltip_only(uc,address,size,data):
                    sp=uc.reg_read(UC_X86_REG_ESP)
                    ret=struct.unpack('<I',uc.mem_read(sp,4))[0]
                    uc.reg_write(UC_X86_REG_EAX,0);uc.reg_write(UC_X86_REG_ESP,sp+28);uc.reg_write(UC_X86_REG_EIP,ret)
                vm.hook_add(UC_HOOK_CODE,tooltip_only,begin=0x49b820,end=0x49b820)
            try:
                if route=='owned_slot':test.call(vm,0x96390,slot,this=inv.UI)
                else:test.call(vm,0x9a330,slot,4,this=inv.UI)
            except Exception as error:
                from unicorn.x86_const import UC_X86_REG_EIP
                raise AssertionError(f'Item {key} slot {slot} PC {vm.reg_read(UC_X86_REG_EIP):x}: {error}') from error
            length=struct.unpack('<I',vm.mem_read(inv.routes.NET+0x36c4,4))[0]
            logical=bytes(vm.mem_read(inv.routes.NET+0x36c8,length))
            expected_opcode=0x25 if key==5571 or route=='inventory_use_event' else 0x26
            if logical[0]!=expected_opcode:raise AssertionError('NATIVE_ITEM_REQUEST_MISMATCH')
            if expected_opcode==0x25 and logical[:4]!=struct.pack('<BHB',0x25,key,slot):raise AssertionError('NATIVE_ITEM25_MISMATCH')
            chain=(0x496390,0x4963c0,0x459a60,0x4132e0) if route=='owned_slot' else (0x49a330,0x459a60,0x496350,0x4132e0)
            for address in chain:
                if address not in seen:raise AssertionError('NATIVE_ITEM_CHAIN_MISSING')
            if 0x4f6360 in seen:raise AssertionError('UNEXPECTED_TELEPORT_MENU_CHAIN')
            if bytes(vm.mem_read(item,len(record)))!=record:raise AssertionError('NATIVE_METADATA_CHANGED')
            observations.append({'slot':slot,'route':route,'logical_hex':logical.hex(),'queue_length':length,
                'original_chain':[hex(a) for a in chain],'tooltip_adapter':route=='inventory_use_event',
                'zero_control_producer_4157d0_reached':0x4157d0 in seen,'menu_receiver_4f6360_reached':False})
        outputs.append({'item':key,'source_line':parsed['source_line'],'SPI_category':n.lookup_section('SPI'),
                        'flags_11a':record[0x11a],'native_metadata_sha256':hashlib.sha256(record).hexdigest(),
                        'observations':observations})
    return {'accepted':True,'current_client_sha256':client_sha,
        'mapped_image_sha256':hashlib.sha256(image).hexdigest(),
        'current_native_spans':[{'rva':hex(r),'size':s,'matched':True} for r,s in spans],
        'items':outputs,'presentation_adapter':'49B820 tooltip only for inventory_use_event; owned_slot has no stubs','live_client_tested':False,
        'authority_boundary':'Native inventory use-event emits C2S25. Owned-slot shortcut emits25 for5571 but26 for5601/5605/5609. No S2C6D menu/context/destination/payment/cooldown association established.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args()
    result=verify();text=json.dumps(result,indent=2)+'\n'
    if a.output:a.output.write_text(text,encoding='utf-8')
    print(text)
