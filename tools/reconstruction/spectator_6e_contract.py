"""Pinned static C2S 6E producer and five direct caller paths.

No client execution, game test, or spectator server lifecycle is performed.
"""
import hashlib
import json
import struct

import capstone
import pefile

from .archive_inputs import ArchivedInputs, SERVER
from .packet_connection_inventory import IMAGE, PIN, BASE, LENGTH_TABLE, WORLD_TABLE


CALLERS = (0x66274, 0x66642, 0x7b738, 0xdd02e, 0x1130a8)
SLICES = (
    (0x97d40, 0x97d71, '6E body builder: BYTE mode, three unwritten bytes, DWORD context'),
    (0x6626b, 0x66279, 'mode1 caller with scene handle'),
    (0x66639, 0x66647, 'mode1 caller with scene handle'),
    (0x7b733, 0x7b73d, 'mode1 caller gated by selected row state'),
    (0xdd029, 0xdd033, 'mode1 caller from UI callback'),
    (0x1130a1, 0x1130ad, 'mode2 caller with zero context and spectator state gate'),
)


def recover():
    reader = ArchivedInputs()
    try:
        raw = reader.read(IMAGE)
    finally:
        reader.close()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Mapped native image changed')
    pe = pefile.PE(data=raw, fast_load=True)
    section = next(s for s in pe.sections if s.Name.rstrip(b'\0') == b'.text')
    start = section.VirtualAddress
    end = min(len(raw), start + max(section.Misc_VirtualSize, section.SizeOfRawData))
    found = tuple(pc for pc in range(start, end-4) if raw[pc] == 0xe8 and
                  pc+5+struct.unpack_from('<i', raw, pc+1)[0] == 0x97d40)
    if found != CALLERS:
        raise ValueError(f'6E direct callers changed: {found}')
    if raw[0x97d66] != 0xe8 or 0x97d66+5+struct.unpack_from('<i', raw, 0x97d67)[0] != 0x132e0:
        raise ValueError('6E queue edge changed')
    leaf = struct.unpack_from('<I', raw, LENGTH_TABLE+0x6e*4)[0]-BASE
    dispatch = struct.unpack_from('<I', raw, WORLD_TABLE+0x6e*4)[0]-BASE
    if raw[leaf:leaf+6] != bytes.fromhex('b805000000c3') or dispatch != 0x6b517:
        raise ValueError('Independent S2C 6E length/default dispatch changed')
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    slices = []
    for begin, stop, purpose in SLICES:
        body=raw[begin:stop]
        ins=list(md.disasm(body, BASE+begin))
        if not ins or ins[-1].address+ins[-1].size!=BASE+stop:
            raise ValueError(f'Unaligned 6E native slice {begin:X}')
        slices.append({'rva':f'{begin:X}','end_rva_exclusive':f'{stop:X}',
                       'purpose':purpose,'sha256':hashlib.sha256(body).hexdigest(),
                       'bytes_hex':body.hex(),
                       'instructions':[{'rva':f'{i.address-BASE:X}',
                                        'instruction':f'{i.mnemonic} {i.op_str}'} for i in ins]})
    return {
        'format':'god2-current-native-c2s6e-static-v1',
        'native_image':IMAGE,'native_sha256':PIN,
        'method':'PINNED_TEXT_DIRECT_CALL_SCAN_AND_BOUNDED_DISASSEMBLY',
        'c2s':{'logical_size':9,'queue_rva':'97D66',
               'producer_rva':'97D40',
               'body':'mode BYTE, three bytes not initialized in the local producer, nonnegative signed DWORD context',
               'direct_caller_rvas':[f'{pc:X}' for pc in CALLERS],
               'mode1_caller_count':4,'mode2_caller_count':1,
               'mode2_context':0,
               'authorization':'NOT_ESTABLISHED'},
        's2c_same_opcode':{'logical_size':5,'length_leaf_rva':f'{leaf:X}',
                           'world_dispatch_rva':f'{dispatch:X}',
                           'world_dispatch':'DEFAULT',
                           'causal_reply':'NOT_PROVEN'},
        'slices':slices,
        'tests_builds_client_execution_live_mutation':False,
    }


def main():
    out=SERVER/'artifacts/integration/packet-connections-20261006/spectator6e-static-v1.json'
    if out.exists():
        raise FileExistsError('Preserve prior native evidence')
    out.write_text(json.dumps(recover(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'artifact':str(out),'method':'STATIC_SOURCE_ONLY'}))


if __name__=='__main__':
    main()
