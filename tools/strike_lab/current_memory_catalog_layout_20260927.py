"""Bounded current-PE evidence for read-only loaded catalog inspection.

Does not open a process, change game memory, launch a client, or create spawns.
Run: python -m tools.strike_lab.current_memory_catalog_layout_20260927
"""
import argparse
import csv
import hashlib
import json
import sys
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECON = ROOT.parent.parent / 'God2-解殼EXE原始碼重建'
sys.path.insert(0, str(ROOT / 'artifacts/tooling/crypto-oracle-python'))
import pefile
import capstone
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP
from .omega_assets import decode_csvz

CLIENT_SHA = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
MAPPED_SHA = '149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
GAME_SHA = '70a4e7dd1a1f66d7a70f5c5e97c77ef4063904cc473292758c5abd2da7bd8731'
PLAIN_SHA = '75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def verify_f8_native(image, base):
    """Execute whole small native cache writer, supplied nonempty server string.

    An offline emulator fixture; no functions are replaced/stubbed. This proves
    copying only, not authoritative values or valid server gameplay policy.
    """
    output=[]
    for key in (2936,2938,2939,6224):
        for level in (17,255):
            emu=Uc(UC_ARCH_X86,UC_MODE_32)
            emu.mem_map(base,(len(image)+4095)&~4095);emu.mem_write(base,image)
            owner=0x2000000;bodyaddr=0x2300000;stack=0x2400000;stop=0x2500000
            emu.mem_map(owner,0x200000);emu.mem_map(bodyaddr,0x1000)
            emu.mem_map(stack,0x2000);emu.mem_map(stop,0x1000)
            before=bytes((i*7+3)&255 for i in range(94));record=owner+0x121ea+key*94
            body=bytearray(122);body[0]=1;body[4]=level
            struct.pack_into('<I',body,8,key)
            body[0x34:0x44]=b'SERVER TEXT 16B\0'
            body[0x45:0x4d]=bytes.fromhex('785634129abcdef0')
            text=b'RECEIVED STATUS\0';body[0x4d:0x4d+len(text)]=text
            struct.pack_into('<h',body,0x78,-2)
            expected=bytearray(before)
            for src,dst,n in ((0,28,1),(4,29,1),(0x78,30,2),(0x34,32,16),(0x45,85,4),(0x49,89,4)):
                expected[dst:dst+n]=body[src:src+n]
            expected[48:48+len(text)]=text
            emu.mem_write(record,before);emu.mem_write(bodyaddr,bytes(body))
            sp=stack+0x1000;emu.mem_write(sp,struct.pack('<II',stop,bodyaddr))
            emu.reg_write(UC_X86_REG_ESP,sp);emu.reg_write(UC_X86_REG_ECX,owner)
            emu.emu_start(0x45ba30,stop,count=10000)
            actual=bytes(emu.mem_read(record,94))
            if actual!=expected or emu.reg_read(UC_X86_REG_ESP)!=sp+8 or emu.reg_read(UC_X86_REG_EIP)!=stop:
                raise ValueError('Native F8 whole-function output/return mismatch')
            output.append({'selector':key,'level_byte':level,'input122':body.hex(),
                'record94_before':before.hex(),'record94_after':actual.hex(),'full_return':True,
                'static_prefix28_unchanged':actual[:28]==before[:28]})
    return output

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--client', type=Path, default=ROOT.parent/'God2')
    p.add_argument('--output', type=Path, default=ROOT/'artifacts/research/memory-catalog-layout-20260927')
    a = p.parse_args()
    raw = (a.client/'God2.exe').read_bytes()
    mapped = (ROOT/'artifacts/capture_work/host-20260918-1430/output/native-master-01-stable.bin').read_bytes()
    packed = (a.client/'Data2/Patch/Comm/gamedata.csvZ').read_bytes()
    plain = decode_csvz(packed)
    for value, expected, label in [(raw, CLIENT_SHA, 'client'), (mapped, MAPPED_SHA, 'mapped'), (packed, GAME_SHA, 'gamedata'), (plain, PLAIN_SHA, 'decoded')]:
        if sha(value) != expected:
            raise ValueError('Identity changed: '+label)
    pe = pefile.PE(data=raw)
    image = pe.get_memory_mapped_image()
    base = pe.OPTIONAL_HEADER.ImageBase
    functions = {int(r['entry'],16):r for r in csv.DictReader((RECON/'decompiled/functions.tsv').open(encoding='utf-8-sig'),delimiter='\t')}
    chosen = (0x4558d0, 0x4570f0, 0x4578b0, 0x457a90, 0x4584a0, 0x45a000, 0x45a0a0, 0x45a1a0, 0x45ba30, 0x4cdc70)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    ranges = []
    for va in chosen:
        f = functions[va]
        end = int(f['end'],16)+1
        if end-va != int(f['body_bytes']):
            raise ValueError('Noncontiguous function: '+hex(va))
        ranges.append((va,end,f['pseudocode_file']))
    ranges.append((0x46aad6,0x46ab27,'world dispatcher F8 branch only'))
    evidence=[]
    a.output.mkdir(parents=True,exist_ok=True)
    for va,end,name in ranges:
        code=image[va-base:end-base]
        if code != mapped[va-base:end-base]:
            raise ValueError('Mapped code mismatch '+hex(va))
        ins=list(md.disasm(code,va))
        if sum(x.size for x in ins)!=len(code):
            raise ValueError('Incomplete linear decode '+hex(va))
        text='\n'.join(f'{x.address:08X}\t{x.bytes.hex()}\t{x.mnemonic}\t{x.op_str}' for x in ins)+'\n'
        (a.output/f'{va:08x}.asm.tsv').write_text(text,encoding='utf-8')
        evidence.append({'va':hex(va),'end_exclusive':hex(end),'bytes':len(code),'sha256':sha(code),
                         'mapped_identical':True,'raw_offset':hex(pe.get_offset_from_rva(va-base)),
                         'pseudocode':name,'instruction_count':len(ins)})
    rows=[];section=None
    for line,body in enumerate(plain.splitlines(),1):
        fields=body.split(b',')
        if fields[0]==b'NPCAppearData':section='NPCAppearData';continue
        if section=='NPCAppearData' and fields[0].isdigit() and len(fields)>=5:
            rows.append({'id':int(fields[0]),'name_hex':fields[1].hex(),'source_line':line,'field_count':len(fields),'raw_record_hex':body.hex(),'record_sha256':sha(body)})
        elif section=='NPCAppearData' and fields[0] and not fields[0].isdigit():
            section=None
    anchors=[]
    for key,observed in ((2936,0x635d36),(2938,0x635df2),(2939,0x635e50)):
        matches=[r for r in rows if r['id']==key]
        if len(matches)!=1:raise ValueError('NPC source anchor missing')
        anchors.append(dict(matches[0], observed_root_run02_name_address=hex(observed),
                            derived_catalog_owner=hex(observed-0x121ea-key*94)))
    if len({r['derived_catalog_owner'] for r in anchors})!=1:raise ValueError('Anchor owners disagree')
    result={'client_sha256':CLIENT_SHA,'mapped_sha256':MAPPED_SHA,'gamedata_sha256':GAME_SHA,
        'decoded_sha256':PLAIN_SHA,'native_ranges':evidence,'source_npc_row_count':len(rows),
        'source_npc_max_id':max(r['id'] for r in rows),'npc_anchors':anchors,
        'short_npc_source_rows':[r for r in rows if r['field_count']<9],
        'f8_native_vectors':verify_f8_native(image,base),
        'npc_static_prefix_bytes':28,'npc_server_mutable_tail_bytes':66,
        'npc_initializer_cleared_byte_offsets':[0,28,29,32,48],
        'f8_body_to_record':[{'body_offset':src,'record_offset':dst,'bytes':n} for src,dst,n in
             [(0,28,1),(4,29,1),(0x78,30,2),(0x34,32,16),(0x45,85,4),(0x49,89,4)]],
        'f8_string':{'body_offset':0x4d,'record_offset':0x30,'copy':'NUL-terminated; default ProgramMessage 1001 or 887 if empty'},
        'memory_plan':{'catalog_owner_observed_run02':'0x5e053c','npc_highwater':'C+0x121e8 signedWORD',
            'npc_records':'C+0x121ea+94*id; capacity7000; id is direct, not id-1',
            'mission':'count DWORD C+0xd2ac0; base DWORD C+0xd2ac4; stride40; id-1',
            'npc_mission':'max signedWORD C+0xb2c48; char** DWORD C+0xb2c4c; id-1',
            'npc_normal':'max signedWORD C+0xb2c3a; base DWORD C+0xb2c3c; stride44; id direct; validBYTE+0/stringptrDWORD+4',
            'eny_roots':'C+0xd2d9c;17 roots stride8 countDWORD+0 ptrDWORD+4',
            'eny_group':'descriptor stride12 sceneDWORD+0 countDWORD+4 recordsDWORD+8; record26 ordinal-1',
            'eny_record':'byte0 packed flags; byte1 resource code low8; name at+2 length16; component8 at+18',
            'eny_arena':'DWORD C+0xd2e24; source allocated7815 records; lookup-visible roots7791 records'},
        'boundary':'This run validates current image ranges and source anchors, not a new process-memory read. Root run02 supplies observed addresses. No coordinates, combat stats, quest events, rewards or spawns inferred.'}
    (a.output/'evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'native_ranges':len(evidence),'npc_source_rows':len(rows),'npc_max_id':result['source_npc_max_id'],'output':str(a.output)}))

if __name__=='__main__':main()
