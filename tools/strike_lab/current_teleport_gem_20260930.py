"""Current16055 parser/use/remaining-charge oracle. Offline, no live process.

Native metadata, request dispatch/queue, and charge selection instructions run.
The inventory event's tooltip-only call is skipped; the charge slice stops just
before sprintf and checks its actual arguments. UI ownership state is synthetic.
No effect/menu-context/arrival/server-authority claim is made by this oracle.
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
from tools.strike_lab.recover_companion_growth import fields,parse_sections
from tools.strike_lab.omega_assets import decode_csvz
from tools.strike_lab import current_item_transition as transition
import test_current_inventory as inv
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EIP

CLIENT_SHA='9be38ef858bc9c63b6f296cae4a8e601ddcfaf614700e725c4bec44065b53336'
RESOURCE=0x3800000
ITEM=RESOURCE+0x30000

class GemMetadata(NativeDeityMetadata):
    ITEM_SECTIONS=('GOD','MIS02')
    def section_selector(self,section):return self.lookup_section(section)[1]

def require(condition,reason):
    if not condition:raise AssertionError(reason)

def verify():
    import pefile
    loader=GemMetadata();image=loader.image
    raw=(ROOT.parent/'God2/God2.exe').read_bytes()
    require(hashlib.sha256(raw).hexdigest()==CLIENT_SHA,'CURRENT_CLIENT_PIN')
    pe=pefile.PE(data=raw,fast_load=True)
    spans=set(loader.CODE)|{(0x9a330,0x9b5e0),(0x96350,0x964c0),
        (0x132e0,0x13352),(0x9f7d0,0x9f7ec),(0xb6424,0xb6447),
        (0xba6f4,0xba7e3),(0xb8872,0xb8887),(0xbc188,0xbc1f3),
        (0x1927f4,0x192804)}
    pins=[]
    for lo,hi in sorted(spans):
        native=image[lo:hi]
        require(pe.get_data(lo,hi-lo)==native,f'CURRENT_SPAN_{lo:x}')
        pins.append({'rva':hex(lo),'size':hi-lo,'sha256':hashlib.sha256(native).hexdigest()})
    rows=loader.sections['MIS02']['records']
    index=next(i for i,row in enumerate(rows) if fields(row)[0]==b'16055')
    parsed=loader.item_row('MIS02',index);record=parsed['record'];row=rows[index]
    require(loader.lookup_section('MIS02')==(33,24),'MIS02_BINDING')
    require(record[0x11a]==0xe1 and record[0x11b]==0,'GEM_FLAGS_OR_STACKING')
    category_dispatch=image[0xbc1d0+7]
    require(struct.unpack_from('<I',image,0xbc188+4*category_dispatch)[0]==0x4ba6f4,'TYPE8_DISPATCH')
    test=inv.CurrentInventoryTests();test.image=image
    vm=test.consumer_vm();vm.mem_map(RESOURCE,0xe0000)
    vm.mem_write(RESOURCE+0xb2d40+4*16055,struct.pack('<I',ITEM));vm.mem_write(ITEM,record)
    vm.mem_write(inv.UI+0xcff70,struct.pack('<I',RESOURCE))
    vm.mem_write(inv.UI+0x86874,struct.pack('<I',inv.routes.NET))
    vm.mem_write(inv.UI+0x8688c,struct.pack('<I',inv.MANAGER+0x100))
    vm.mem_write(inv.MANAGER+0x100,struct.pack('<H',4))
    for offset in (0x232dfe,0x232dda):vm.mem_write(inv.UI+offset,b'\xff\xff')
    seen=set();executed_request={}
    def current_instruction(uc,address,size,data):
        seen.add(address)
        if address==inv.routes.RETURN:return
        if address not in executed_request:
            require(0x400000<=address<0x400000+len(image),'REQUEST_EXECUTION_RANGE')
            rva=address-0x400000
            require(pe.get_data(rva,size)==image[rva:rva+size],'CURRENT_REQUEST_INSTRUCTION')
            executed_request[address]=size
    vm.hook_add(UC_HOOK_CODE,current_instruction)
    def tooltip_only(uc,address,size,data):
        sp=uc.reg_read(UC_X86_REG_ESP);ret=struct.unpack('<I',uc.mem_read(sp,4))[0]
        uc.reg_write(UC_X86_REG_EAX,0);uc.reg_write(UC_X86_REG_ESP,sp+28);uc.reg_write(UC_X86_REG_EIP,ret)
    vm.hook_add(UC_HOOK_CODE,tooltip_only,begin=0x49b820,end=0x49b820)
    requests=[]
    for slot in (0,12,29):
        for charge in (0,1,10,11,127):
            for route in ('inventory_use_event','owned_slot_shortcut'):
                vm.mem_write(inv.SLOTS,bytes(50*24))
                instance=struct.pack('<I',16055|(8<<16)|(charge<<25))+bytes(range(4,20))
                vm.mem_write(inv.SLOTS+24*slot,b'\x01\x37\x49\x59'+instance)
                vm.mem_write(inv.UI+0x866e4,bytes(4));vm.mem_write(inv.routes.NET+0x36c4,bytes(4));seen.clear()
                if route=='inventory_use_event':test.call(vm,0x9a330,slot,4,this=inv.UI)
                else:test.call(vm,0x96390,slot,this=inv.UI)
                size=struct.unpack('<I',vm.mem_read(inv.routes.NET+0x36c4,4))[0]
                wire=bytes(vm.mem_read(inv.routes.NET+0x36c8,size))
                expected=struct.pack('<BHB',0x25,16055,slot) if route=='inventory_use_event' else struct.pack('<BHHB',0x26,4,16055,slot)
                require(wire.startswith(expected) and len(wire)==len(expected)+1,'GEM_REQUEST_BYTES')
                require(0x459a60 in seen and 0x4132e0 in seen,'NATIVE_REQUEST_CHAIN')
                require(0x4f6360 not in seen and 0x4f6b30 not in seen,'NO_LOCAL_MENU_CONSTRUCTION')
                require(bytes(vm.mem_read(inv.SLOTS+24*slot+4,20))==instance,'USE_MUST_NOT_DECREMENT_LOCALLY')
                requests.append({'slot':slot,'charges':charge,'route':route,'logical_hex':wire.hex(),
                    'native_queue_length':size,'no_local_instance_change':True})
    # Direct producer gate covers every nonzero tested busy-state value. The UI
    # alert path is not adapted into a fake producer success.
    gates=[]
    for busy in (1,2,0xffffffff):
        for entry,args in ((0x96350,(16055,12,1)),(0x96390,(29,))):
            vm.mem_write(inv.UI+0x866e4,struct.pack('<I',busy));vm.mem_write(inv.routes.NET+0x36c4,bytes(4))
            test.call(vm,entry,*args,this=inv.UI)
            require(struct.unpack('<I',vm.mem_read(inv.routes.NET+0x36c4,4))[0]==0,'BUSY_GATE')
            gates.append({'entry_rva':hex(entry),'busy':busy,'queue_length':0})
    # Execute the type8 jump table and all original charge extraction/gate code.
    message_path=ROOT.parent/'God2/Data2/Patch/Comm/message.csvZ'
    message_raw=message_path.read_bytes()
    messages=parse_sections(decode_csvz(message_raw),('ProgramMsg',))['ProgramMsg']['records']
    msg_table=RESOURCE+0x10000;prefix=RESOURCE+0x20000;suffix=RESOURCE+0x20100
    vm.mem_write(RESOURCE+0xb2c68,struct.pack('<I',msg_table));vm.mem_write(RESOURCE+0xb2c6c,struct.pack('<H',1080))
    for ident,address in ((890,prefix),(891,suffix)):
        vm.mem_write(msg_table+(ident-1)*4,struct.pack('<I',address))
        vm.mem_write(address,fields(messages[ident-1])[1]+b'\0')
    stop_set={0x4b887a,0x4bbbce}
    stop_hook=vm.hook_add(UC_HOOK_CODE,lambda uc,address,size,data:uc.emu_stop() if address in stop_set else None)
    charges=[]
    try:
        for count in range(128):
            for flags in range(8):
                value=16055|(8<<16)|(flags<<22)|(count<<25)
                sp=inv.routes.STACK+0x1000
                vm.mem_write(sp-0x80,bytes(0x1800));vm.mem_write(sp+0x11a4,struct.pack('<I',16055))
                vm.reg_write(UC_X86_REG_ESP,sp);vm.reg_write(UC_X86_REG_EBP,inv.UI);vm.reg_write(UC_X86_REG_EAX,value)
                vm.emu_start(0x4b6424,0,count=1000)
                pc=vm.reg_read(UC_X86_REG_EIP);shown=1<=count<=10
                require(pc==(0x4b887a if shown else 0x4bbbce),'CHARGE_DISPLAY_GATE')
                if shown:
                    args=struct.unpack('<IIIII',vm.mem_read(vm.reg_read(UC_X86_REG_ESP),20))
                    require(args[1:]==(0x5927f4,prefix,count,suffix),'NATIVE_FORMAT_ARGUMENTS')
                charges.append({'count':count,'unrelated_flags':flags,'displayed':shown})
    finally:vm.hook_del(stop_hook)
    # This is an explicitly CUSTOM supplied menu, proving the native receiver,
    # row enable, selected-ID and99/cancel86 contracts, not original server causality.
    menu=struct.pack('<BHHBBBB',0x6d,16055,280,0x81,0,10,0)+bytes((5,0,0,0))+bytes(16)
    vm.mem_write(inv.PACKET_PAGE,menu[1:]);vm.mem_write(inv.UI+0x232e38,b'\xff\xff')
    vm.mem_write(inv.UI+0x790e0,b'\xff'*4)
    test.call(vm,0xf6360,inv.PACKET_PAGE,this=inv.UI)
    require(bytes(vm.mem_read(inv.UI+0x790ec,28))==menu[1:],'MENU_BODY_COPY')
    require(struct.unpack('<II',vm.mem_read(inv.UI+0x790e4,8))==(0,1),'MENU_SINGLE_PAGE')
    renderer_events=[]
    def rendering_only(uc,address,size,data):
        sp=uc.reg_read(UC_X86_REG_ESP);ret=struct.unpack('<I',uc.mem_read(sp,4))[0]
        renderer_events.append(hex(address));uc.reg_write(UC_X86_REG_ESP,sp+4);uc.reg_write(UC_X86_REG_EIP,ret)
    render_hooks=[vm.hook_add(UC_HOOK_CODE,rendering_only,begin=a,end=a) for a in (0x5077c0,0x50d010)]
    try:
        vm.mem_write(inv.UI+0x232e38,b'\0\0')
        test.call(vm,0xf7090,0,this=inv.UI)
        require(struct.unpack('<I',vm.mem_read(inv.UI+0x79108+0x148,4))[0]==1,'MENU_ROW_ENABLED')
        test.call(vm,0xf7160,0,this=inv.UI)
        require(struct.unpack('<I',vm.mem_read(inv.UI+0x790e0,4))[0]==5,'MENU_SELECTED_ID_NOT_INDEX')
    finally:
        for hook in render_hooks:vm.hook_del(hook)
    vm.mem_write(inv.UI+0x232e38,b'\xff\xff');vm.mem_write(inv.routes.NET+0x36c4,bytes(4))
    test.call(vm,0xf72b0,this=inv.UI)
    require(struct.unpack('<I',vm.mem_read(inv.routes.NET+0x36c4,4))[0]==5,'MENU_SELECTION_SIZE')
    selection=bytes(vm.mem_read(inv.routes.NET+0x36c8,5))
    require(selection==struct.pack('<BHB',0x99,16055,5)+bytes((inv.UI>>24,)),'MENU_SELECTION_BYTES')
    require(bytes(vm.mem_read(inv.UI+0x790ec,28))==bytes(28),'MENU_BODY_CLEARED')
    vm.mem_write(inv.routes.NET+0x36c4,bytes(4));test.call(vm,0xf6a00,this=inv.UI)
    cancellation=bytes(vm.mem_read(inv.routes.NET+0x36c8,5))
    require(cancellation==struct.pack('<BHH',0x86,4,inv.UI>>16),'MENU_CANCEL_OWN_ID_AND_POINTER_TAIL')
    menu_proof={'logical_hex':menu.hex(),'received_body_exact':True,'page':0,'pages':1,'enabled':True,
        'selected_id':5,'selection_logical_hex':selection.hex(),'cancel_logical_hex':cancellation.hex(),
        'body_cleared_after_send':True,'renderer_adapters':renderer_events,
        'opening_window_gate':'Inactive dialog skips display during receiver; display is not acceptance',
        'authority':'CUSTOM-0057 input menu; no original25-to6D association asserted'}
    # Full native3B/41 replacement, real parsed definition, inactive controls.
    # Synthetic instance bytes are explicit fixtures, not native grant authority.
    consumer=transition.NativeItemTransition();cv=consumer.vm
    cv.mem_protect(transition.DEFINITIONS,0xe0000,transition.UC_PROT_READ|transition.UC_PROT_WRITE)
    cv.mem_write(transition.COMPANION+0x1000,record)
    cv.mem_write(transition.DEFINITIONS+0xb2d40+16055*4,struct.pack('<I',transition.COMPANION+0x1000))
    cv.mem_protect(transition.DEFINITIONS,0xe0000,transition.UC_PROT_READ)
    cv.mem_write(transition.UI+0x85abd,b'\xff')
    executed={}
    def pin_instruction(uc,address,size,data):
        if address==transition.RETURN:return
        require(0x400000<=address<0x400000+len(image),'PROJECTION_EXECUTION_RANGE')
        rva=address-0x400000
        require(pe.get_data(rva,size)==image[rva:rva+size],'CURRENT_PROJECTION_INSTRUCTION')
        executed[address]=size
    cv.hook_add(UC_HOOK_CODE,pin_instruction)
    projections=[]
    for slot in (0,29):
        for count in (1,2,9,10):
            for flags in (0,7):
                metadata=struct.pack('<I',16055|(8<<16)|(flags<<22)|(count<<25))+bytes(range(4,20))
                before=bytes([0xa5])*1200;cv.mem_write(transition.SLOTS,before)
                batch=[struct.pack('<BHBB',0x41,0,slot,0),bytes((0x3b,1,slot,0,0))+metadata,
                    struct.pack('<BHBB',0x41,16055,slot,1)]
                for logical in batch:
                    cv.mem_write(transition.PACKET,logical[1:])
                    cv.mem_write(transition.SP,struct.pack('<II',transition.RETURN,transition.PACKET))
                    cv.reg_write(UC_X86_REG_ESP,transition.SP);cv.reg_write(transition.UC_X86_REG_ECX,transition.UI)
                    consumer._run(0x991e0 if logical[0]==0x41 else 0x98dd0,transition.RETURN-transition.BASE)
                    require(cv.reg_read(UC_X86_REG_ESP)==transition.SP+8,'PROJECTION_STACK')
                    for address,size in consumer.writes:
                        require(transition.STACK<=address and address+size<=transition.STACK+0x4000 or
                            transition.SLOTS+slot*24<=address and address+size<=transition.SLOTS+(slot+1)*24,
                            'PROJECTION_WRITE_BOUND')
                expected=bytearray(before);expected[slot*24]=1;expected[slot*24+4:slot*24+24]=metadata
                require(bytes(cv.mem_read(transition.SLOTS,1200))==bytes(expected),'FULL_INSTANCE_PROJECTION')
                projections.append({'slot':slot,'charges':count,'unrelated_flags':flags,
                    'logical_hex':b''.join(batch).hex(),'full_native_consumers':True})
    return {'accepted':True,'client_sha256':CLIENT_SHA,'mapped_image_sha256':hashlib.sha256(image).hexdigest(),
        'native_spans':pins,'metadata':{'source_line':parsed['source_line'],'decoded_offset':row['decoded_offset'],
            'source_row_sha256':row['sha256'],'raw_record_hex':row['raw_record_hex'],'category':33,'parser_selector':24,
            'flags_11a':record[0x11a],'flags_11b':record[0x11b],'record_hex':record.hex()},
        'requests':requests,'busy_gate_vectors':gates,'charge_vectors':charges,'projections':projections,'menu_contract':menu_proof,
        'request_charge_executed_instruction_count':len(executed_request),
        'projection_executed_instruction_count':len(executed),
        'message_sha256':hashlib.sha256(message_raw).hexdigest(),
        'charge_messages':[{'id':i,'source_line':messages[i-1]['source_line'],'raw_record_hex':messages[i-1]['raw_record_hex']} for i in (890,891)],
        'vectors':{'requests':len(requests),'busy_gates':len(gates),'charge_display':len(charges),'full_instance_projection':len(projections),'custom_menu_pipeline':1},
        'limits':'Offline synthetic owned state. Tooltip call skipped only on inventory event. Charge slice stops before sprintf. No native server reply/context/arrival/payment/cooldown authority recovered. No live client or server acceptance.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=verify();output=json.dumps(result,indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(output,encoding='utf-8')
    print(json.dumps({'accepted':result['accepted'],'vectors':result['vectors'],'output':str(args.output)}))
