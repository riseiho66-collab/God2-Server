"""Bounded MBD cell lead, with original x86 execution and no NPC grants."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import struct

import pefile
from .current_battle_entry import NativeRun, BASE, SP, RETURN, pinned_image
from .outdoor_mbd import parse_mbd
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESP

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT.parent / 'God2'
RECON = ROOT.parent.parent / 'God2-解殼EXE原始碼重建'
MBD = CLIENT / 'Data2/map/island03/cityi2/cityi2.mbd'
MBD_SHA = 'eba7aa7ae1ddc0381c7fe30d452fa251345aa9310386948b5eaf080c37d78e59'
SPANS = {'cell_draw_index_getter': (0x381d0, 0x38206),
         'previously_unexported_cell_draw_index_setter': (0x38210, 0x38266),
         'group_index_adjustment': (0x3b7db, 0x3b83b),
         'tile_lookup': (0x3b1b0, 0x3b1f8),
         'named_map_cell_writer': (0x3ff50, 0x4024c)}

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def draw_index(image, cell, x=0, y=0):
    n = NativeRun(image)
    owner, data = 0x11000000, 0x11001000
    n.put(owner, bytes(0x80)); n.put(data, cell)
    for off, value in ((8, data), (0xc, 1), (0x24, 1), (0x28, 1)):
        n.put32(owner+off, value)
    n.put32(SP+4, x & 0xffffffff); n.put32(SP+8, y & 0xffffffff)
    n.registers(ecx=owner)
    n.run(0x381d0, [(0x381d0, 0x38206)], set(), budget=40)
    actual = n.vm.reg_read(UC_X86_REG_EAX)
    expected = struct.unpack_from('<h', cell, 4)[0] if x == y == 0 else -1
    require(n.stop == RETURN and actual == (expected & 0xffffffff), 'Native getter mismatch')
    require(bytes(n.vm.mem_read(data, 8)) == cell and
            all(SP-16 <= addr < SP for _,addr,_,_ in n.writes), 'Getter changed non-stack state')
    require(n.vm.reg_read(UC_X86_REG_ESP) == SP+12, 'Getter stack mismatch')
    return expected

def set_index(image, value, count, x=0, y=0):
    n = NativeRun(image)
    owner, data, manager = 0x11000000, 0x11001000, 0x11002000
    cell = bytes.fromhex('010002000300a5d3')
    n.put(owner, bytes(0x80)); n.put(data, cell); n.put(manager, bytes(0x1000))
    for off, v in ((4, manager), (8, data), (0xc, 1), (0x24, 1), (0x28, 1)):
        n.put32(owner+off, v)
    n.put32(manager+0x910, count)
    for off, v in ((4, x), (8, y), (12, value)):
        n.put32(SP+off, v & 0xffffffff)
    n.registers(ecx=owner)
    n.run(0x38210, [(0x38210, 0x38266)], set(), budget=50)
    succeeds = x == y == 0 and value < count
    expected = bytearray(cell)
    if succeeds:
        struct.pack_into('<H', expected, 4, value & 0xffff)
    require(n.stop == RETURN and n.vm.reg_read(UC_X86_REG_EAX) == int(succeeds), 'Setter return mismatch')
    require(bytes(n.vm.mem_read(data, 8)) == bytes(expected), 'Setter writes unrelated field')
    require(n.vm.reg_read(UC_X86_REG_ESP) == SP+16, 'Setter stack mismatch')
    return {'value': value, 'tile_count': count, 'x': x, 'y': y, 'accepted': succeeds,
            'after_hex': bytes(expected).hex()}

def group_adjust(image, value, threshold, kind, matching=True, enabled=True):
    n = NativeRun(image)
    data, selected, current = 0x11000000, 0x11001000, 0x11002000
    cell = struct.pack('<hhhBB', 33, value, 50, 0xa5, 0xd3)
    n.put(data, cell); n.put(selected, bytes(0x30)); n.put(current, bytes(0x30))
    n.put32(selected+0x14, kind); n.put32(current+0x14, kind if matching else kind+1)
    for off, v in ((0x1c, int(enabled)), (0x24, selected), (0x34, data),
                   (0x38, 1), (0x10, threshold & 0xffffffff)):
        n.put32(SP+off, v)
    n.registers(eax=current, edi=0, esi=0)
    n.run(0x3b7db, [(0x3b7db, 0x3b83b)], {0x3b83b}, budget=45)
    expected = bytearray(cell)
    changes = enabled and matching and kind in (0, 1, 4) and value > threshold
    if changes:
        struct.pack_into('<h', expected, 2, value-1)
    require(n.stop == 0x3b83b and bytes(n.vm.mem_read(data, 8)) == bytes(expected), 'Group adjustment mismatch')
    require(n.vm.reg_read(UC_X86_REG_ESP) == SP, 'Adjustment stack mismatch')
    return {'value': value, 'threshold': threshold, 'tile_type': kind,
            'matching': matching, 'enabled': enabled, 'changed': changes}

def native_named_writer(image, cell):
    n = NativeRun(image)
    owner, data, handle = 0x11000000, 0x11001000, 0x12345678
    n.put(owner, struct.pack('<III', data, 1, 1)); n.put(data, cell)
    for i,value in enumerate((0,0,1,1,handle),1):
        n.put32(SP+4*i, value)
    n.registers(ecx=owner)
    start, calls = 0x3ff50, []
    for _ in range(21):
        n.run(start, [(0x3ff50,0x4024c)], {0x1471ff}, budget=500)
        if n.stop == RETURN:
            break
        require(n.stop == 0x1471ff, 'Unexpected writer control flow')
        sp = n.vm.reg_read(UC_X86_REG_ESP)
        require(n.get32(sp+4) == handle, 'Writer file handle mismatch')
        fmt_address = n.get32(sp+8)
        require(BASE <= fmt_address < BASE+len(image), 'Format outside pinned image')
        fmt = image[fmt_address-BASE:fmt_address-BASE+160].split(b'\0',1)[0]
        require(len(fmt)<160, 'Unbounded native format')
        count = len(re.findall(rb'%[-+0-9.]*d',fmt))
        arguments = [struct.unpack('<i',n.vm.mem_read(sp+12+4*i,4))[0] for i in range(count)]
        calls.append({'format_rva':hex(fmt_address-BASE),'format_ascii':fmt.decode('ascii'),
                      'format_hex':fmt.hex(),'arguments':arguments})
        # Adapt only CRT fprintf to an in-memory receipt; no client instruction changes.
        start = n.get32(sp)-BASE
        n.registers(esp=sp+4,eax=0)
    require(n.stop == RETURN and n.vm.reg_read(UC_X86_REG_EAX)==1 and
            n.vm.reg_read(UC_X86_REG_ESP)==SP+24, 'Native map writer did not fully return')
    word0,word2,word4,byte6,byte7 = struct.unpack('<hhhBB',cell)
    expected = {'TileNum':word4,'SpriteNum':byte7&15,'TileIdx':word0,
                'Pass':(byte7&0x30)>>4,'LinkIdx':word2,'PalNum':byte6&31}
    decoded, field = {}, None
    for call in calls:
        for name in expected:
            if name in call['format_ascii']:
                field=name
                break
        if field and len(call['arguments'])==1:
            decoded[field]=call['arguments'][0];field=None
    require(decoded==expected and len(calls)==20,'Native named cell outputs differ')
    require(bytes(n.vm.mem_read(data,8))==cell,'Native writer changed source cell')
    return {'native_fields':decoded,'original_fprintf_calls':calls,'full_return':True}

def report():
    image = pinned_image()
    current_exe = (CLIENT/'God2.exe').read_bytes()
    current = pefile.PE(data=current_exe).get_memory_mapped_image()
    spans = []
    for name, (start, end) in SPANS.items():
        require(current[start:end] == image[start:end], 'Current EXE span mismatch: '+name)
        spans.append({'name': name, 'rva_start': hex(start), 'rva_end': hex(end),
                      'sha256': sha(image[start:end])})
    raw = MBD.read_bytes(); require(sha(raw) == MBD_SHA, 'CityI2 MBD source changed')
    layout = parse_mbd(raw)
    require((layout['width'], layout['height']) == (12,12), 'CityI2 dimensions changed')
    unique = {}
    for block, offset in enumerate(layout['offsets']):
        if not offset:
            continue
        for cell_index in range(441):
            source = offset + cell_index*8
            cell = raw[source:source+8]
            if cell not in unique and len(unique) < 16:
                unique[cell] = {'block': block, 'cell': cell_index, 'file_offset': source,
                    'raw_cell_hex': cell.hex(), 'native_signed_draw_index': draw_index(image, cell),
                    'native_named_writer':native_named_writer(image,cell)}
    boundaries = [draw_index(image, next(iter(unique)), x, y) for x,y in ((-1,0),(1,0),(0,-1),(0,1))]
    setters = [set_index(image,v,100) for v in (-1,0,99,100,32767)]
    setters += [set_index(image,5,100,x,y) for x,y in ((-1,0),(1,0),(0,-1),(0,1))]
    adjustments = [group_adjust(image,v,t,k) for k in (0,1,4,2)
                   for v,t in ((-32768,-1),(-1,-1),(0,-1),(7,6),(32767,32767))]
    adjustments += [group_adjust(image,7,6,0,matching=False), group_adjust(image,7,6,0,enabled=False)]
    tsv = RECON/'decompiled/functions.tsv'
    functions = list(csv.DictReader(tsv.read_text('utf-8').splitlines(), delimiter='\t'))
    missing_setter = not any(int(row['entry'],16) == BASE+0x38210 for row in functions)
    inputs = []
    for va in (0x4381d0,0x438e50,0x439030,0x43b360,0x43a390,0x43a2e0,0x43b6c0,0x43ff50):
        path = RECON/f'decompiled/functions/{va:08x}_FUN_{va:08x}.c'
        inputs.append({'va': hex(va), 'pseudocode_sha256': sha(path.read_bytes())})
    return {'status':'PASS','scope':'CityI2 MBD cell lead only; no whole-client absence claim',
        'current_exe_sha256':sha(current_exe),'mbd_sha256':sha(raw),'native_spans':spans,
        'reconstructed_sources':inputs,'exported_functions_sha256':sha(tsv.read_bytes()),
        'setter_438210_absent_from_export':missing_setter,
        'source_cells':list(unique.values()),'getter_boundaries':boundaries,
        'setter_cases':setters,'group_adjustment_cases':adjustments,
        'counts':{'actual_source_getters':len(unique),'full_native_named_writers':len(unique),'getter_boundaries':len(boundaries),
                  'setter':len(setters),'group_adjustment':len(adjustments)},
        'field_evidence':{'word0':'tile index via43B1B0',
            'word2':'Native43FF50 LinkIdx;43B360 returns group ordinal;43B7DB..43B83B adjusts later same-type ordinals after tile-group removal',
            'word4':'Native43FF50 TileNum;4381D0 signed draw selector;438210 setter bound by tile manager+910;438E50/439030 forwards selector to449FD0',
            'byte6_low5':'438E50/439030 forwards to42B120 palette selection; other bits unqualified',
            'byte7_low4':'Native43FF50 SpriteNum, not a qualified NPC facing',
            'byte7_bits4_5':'Native43FF50 MAPv1.1 Pass field, not the separately qualified47440 base bit6',
            'byte7_bit6':'Prior qualified47440 base collision bit; other bits not all qualified'},
        'qualified_interactive_npc_placements':[], 'runtime_eligible':False,
        'remaining':'NPC pool identity/area/scene/facing still absent from this cell namespace. Missing Ghidra function boundaries mean exported text alone cannot certify all NPC sources.'}

def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args(); value = report()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':value['status'],'counts':value['counts'],
                      'qualified_interactive_npc_placements':0,'output':str(args.output)}))
if __name__ == '__main__':
    main()
