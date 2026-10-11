"""Owned-client diagnostic thunk; native dialogue action, not physical input."""
import struct


def confirm_page(address, ui):
    if not 0 < address <= 0xfffff000 or not 0 < ui <= 0xffdc0000:
        raise ValueError('Bounded 32-bit page and UI required')
    # Preserve the interrupted caller, including flags; C8500 is thiscall/no args.
    code = (b'\x9c\x60\xb9' + struct.pack('<I', ui)
            + b'\xb8' + struct.pack('<I', 0x4c8500)
            + b'\xff\xd0\x61\x9d\xcc\x0f\x0b')
    return code, len(code) - 3


def npc_request_page(address,ui,target):
    confirm_page(address,ui)
    if type(target) is not int or not 0<target<65535:
        raise ValueError('Bounded explicit NPC identity required')
    code=(b'\x9c\x60\x68'+struct.pack('<I',target)+b'\xb9'+struct.pack('<I',ui)
          +b'\xb8'+struct.pack('<I',0x496750)+b'\xff\xd0\x61\x9d\xcc\x0f\x0b')
    return code,len(code)-3


def advance_or_confirm_page(address,ui):
    confirm_page(address,ui)
    this=b'\xb9'+struct.pack('<I',ui)
    # Native C85B0(button3, event1) runs next-page, selection reset and redraw.
    # C8500 is used only on the last page. No page state is written by the thunk.
    advance=b'\x6a\x01\x6a\x03'+this+b'\xb8'+struct.pack('<I',0x4c85b0)+b'\xff\xd0'
    confirm=this+b'\xb8'+struct.pack('<I',0x4c8500)+b'\xff\xd0'
    code=(b'\x9c\x60\xa1'+struct.pack('<I',0x5b7bf4)+b'\x48\x3b\x05'+struct.pack('<I',0x5b7bf0)
          +b'\x74'+bytes([len(advance)+2])+advance+b'\xeb'+bytes([len(confirm)])+confirm
          +b'\x61\x9d\xcc\x0f\x0b')
    return code,len(code)-3


def close_page(address,ui):
    confirm_page(address,ui)
    code=(b'\x9c\x60\xb9'+struct.pack('<I',ui)+b'\xb8'+struct.pack('<I',0x4c8350)
          +b'\xff\xd0\x61\x9d\xcc\x0f\x0b')
    return code,len(code)-3


def town_resource_page(address,table):
    confirm_page(address,table)
    # Original 5F0E0 thiscall(group0, ordinal19), callee removes both arguments.
    code=(b'\x9c\x60\x6a\x13\x6a\x00\xb9'+struct.pack('<I',table)
          +b'\xb8'+struct.pack('<I',0x45f0e0)+b'\xff\xd0\x61\x9d\xcc\x0f\x0b')
    return code,len(code)-3


def map_item_request_page(address,ui):
    confirm_page(address,ui)
    code=(b'\x9c\x60\x6a\x00\xb9'+struct.pack('<I',ui)
          +b'\xb8'+struct.pack('<I',0x496390)+b'\xff\xd0\x61\x9d\xcc\x0f\x0b')
    return code,len(code)-3


def map_panel_snapshot(driver,ui):
    from pagefile_capacity_compat import memory
    def read(offset,size):return memory(driver,ui+offset,size)
    scene=int.from_bytes(read(0x8aa4c,4),'little')
    panel=int.from_bytes(read(0x232da8,2),'little',signed=True)
    result={'ui':ui,'scene':scene,'panel':panel,'blocked':int.from_bytes(read(0x232f58,4),'little'),
            'slot0_hex':read(0x8560c,24).hex()}
    if scene:
        result['scene_id']=int.from_bytes(memory(driver,scene+0xf0,2),'little')
        result['scene_flags']=int.from_bytes(memory(driver,scene+0xf4,4),'little')
        metadata=int.from_bytes(memory(driver,scene+0x1a0,4),'little')
        if metadata:
            result['scene_map_metadata']=dict(pointer=metadata,header_hex=memory(driver,metadata,0x28).hex())
    if 0<=panel<128:
        node=ui+0xe2988+10760*panel
        result.update(node=node,node_header_hex=memory(driver,node,48).hex(),
                      flags=int.from_bytes(memory(driver,node,2),'little'))
        handle=int.from_bytes(memory(driver,node+4,2),'little')
        renderer=int.from_bytes(read(0xe2178,4),'little')
        if renderer and handle<0x1000:
            obj=renderer+0x10+handle*0x290
            header=memory(driver,obj,0x74)
            bank=int.from_bytes(header[0x34:0x38],'little')
            action=int.from_bytes(header[0x38:0x3c],'little')
            result['render_object']=dict(pointer=obj,handle=handle,header_hex=header.hex(),bank=bank,action=action)
            if bank:result['render_object']['bank_header_hex']=memory(driver,bank,0x50).hex()
            if action:result['render_object']['action_header_hex']=memory(driver,action,0x40).hex()
    return result
