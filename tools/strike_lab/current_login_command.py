"""Diagnostic native menu command; no credentials or authenticated state writes."""
import struct


def call_page(address, login):
    if any(type(p) is not int or not 0x10000 <= p < 0x7fff0000 for p in (address, login)):
        raise ValueError('Bounded32-bit pointers required')
    code = (b'\x6a\x01\x6a\x03\xb9' + struct.pack('<I', login)
            + b'\xb8' + struct.pack('<I', 0x406400) + b'\xff\xd0\xcc\x0f\x0b')
    return code, len(code) - 3


def lab_identity(peer=0):
    if type(peer) is not int or peer not in (0,1):
        raise ValueError('Only two fixed public laboratory identities are supported')
    return ((b'codexlab',b'CodexTrial'),(b'codexpeer',b'CodexPeer'))[peer]


def submit_page(address, login, peer=0):
    call_page(address, login)
    account,_=lab_identity(peer)
    code = b''
    for offset, text_offset in ((0x178db4, 0x100), (0x179940, 0x120)):
        code += (b'\x68' + struct.pack('<I', address + text_offset) + b'\xb9'
                 + struct.pack('<I', login + offset) + b'\xb8'
                 + struct.pack('<I', 0x50ec90) + b'\xff\xd0')
    code += (b'\x6a\x01\x6a\x05\xb9' + struct.pack('<I', login) + b'\xb8'
             + struct.pack('<I', 0x4068e0) + b'\xff\xd0\xcc\x0f\x0b')
    # Fixed public laboratory credentials only; never load personal credentials.
    return (code.ljust(0x100, b'\0') + account+b'\0').ljust(0x120, b'\0') + b'labtest2345\0', len(code) - 3


def select_page(address, login, channel=False):
    call_page(address, login)
    code = (b'\x6a\x01\x6a\x06\xb9' + struct.pack('<I', login)
            + b'\xb8' + struct.pack('<I', 0x407aa0 if channel else 0x407040) + b'\xff\xd0\xcc\x0f\x0b')
    return code, len(code) - 3


def creation_page(address, login, submit=False, peer=0):
    call_page(address, login)
    _,name=lab_identity(peer)
    code = b''
    if submit:
        code = (b'\x68' + struct.pack('<I', address + 0x100) + b'\xb9'
                + struct.pack('<I', login + 0x152a8) + b'\xb8'
                + struct.pack('<I', 0x50ec90) + b'\xff\xd0')
    code += (b'\x6a\x01\x6a\x11\xb9' + struct.pack('<I', login)
             + b'\xb8' + struct.pack('<I', 0x40a870 if submit else 0x4097a0)
             + b'\xff\xd0\xcc\x0f\x0b')
    trap = len(code) - 3
    return (code.ljust(0x100, b'\0') + name+b'\0' if submit else code), trap


def character_select_page(address, login):
    call_page(address, login)
    code=(b'\x6a\x01\x6a\x0a\xb9'+struct.pack('<I',login)
          +b'\xb8'+struct.pack('<I',0x4087b0)+b'\xff\xd0\xcc\x0f\x0b')
    return code,len(code)-3


def movement_step_page(address, world, step=1):
    call_page(address, world)
    if not 1 <= step <= 39:
        raise ValueError('Diagnostic movement step outside bounded sequence')
    # Diagnostic adjacent step only, after live spawn/ring validation.
    sx,sy,tx,ty=(17,13,18,12) if step%2 else (18,12,17,13)
    code=b''.join(b'\x6a'+bytes([value]) for value in (step,ty,tx,sy,sx))
    code+=b'\xb9'+struct.pack('<I',world)
    code+=b'\xb8'+struct.pack('<I',0x502700)+b'\xff\xd0\xcc\x0f\x0b'
    return code,len(code)-3


def supply_use_page(address, world):
    call_page(address, world)
    ui = world + 0xa7f2f6c
    call_page(address, ui)
    # Preserve interrupted world-frame registers/flags; original caller owns
    # lookup, target selection and queue append. No fabricated network bytes.
    code = (b'\x9c\x60\x6a\x00\xb9' + struct.pack('<I', ui)
            + b'\xb8' + struct.pack('<I', 0x496390) + b'\xff\xd0\x61\x9d\xcc\x0f\x0b')
    return code, len(code) - 3


def movement_path_page(address, world, step=1):
    movement_step_page(address, world, step)
    tx,ty=(18,12) if step%2 else (17,13)
    code=b'\x6a'+bytes([ty])+b'\x6a'+bytes([tx])+b'\xb9'+struct.pack('<I',world)
    code+=b'\xb8'+struct.pack('<I',0x5024c0)+b'\xff\xd0\xcc\x0f\x0b'
    return code,len(code)-3


def town_movement_path_page(address, world, x, y):
    call_page(address, world)
    if any(type(value) is not int or not 0 <= value < 189 for value in (x,y)):
        raise ValueError('Town target outside source map bounds')
    # Original path routine owns navigation, animation and the outgoing queue.
    code=b'\x68'+struct.pack('<I',y)+b'\x68'+struct.pack('<I',x)
    code+=b'\xb9'+struct.pack('<I',world)+b'\xb8'+struct.pack('<I',0x5024c0)
    code+=b'\xff\xd0\xcc\x0f\x0b'
    return code,len(code)-3
