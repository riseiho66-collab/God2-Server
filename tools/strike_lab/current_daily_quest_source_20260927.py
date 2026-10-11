"""Pinned full native daily display parser/lookup; never quest execution rules.

CRT calloc, fgets and decimal conversion are adapters. Game parser, tokenizer,
accessors, copies and pair lookup execute the current PE unchanged to return.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys

from .omega_assets import decode_csvz
from .recover_quests import parse_table
from .recover_companion_growth import _NativeRows

ROOT = Path(__file__).resolve().parents[2]
CLIENT_SHA = '6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
SOURCE = 'Data2/Patch/Comm/DayMissionDesc.csvZ'
SOURCE_SHA = '4a347d56706946d7004b2bd2118500ffc60844628fa461862b2f6d5320a90e54'
DECODED_SHA = '2848b95b0af99eac10ca4dff61a5533c13917127c4738039e263c60a1be45eaf'
CATALOG_SHA = 'df0bc3a96425c3440cd2fefc867840aa10e3ad35c4a3be32e332c6204f30236a'
STRINGS = ((2,20,30,'name'), (11,50,20,'restriction_text'),
           (12,70,41,'description_1'), (13,111,41,'description_2'),
           (14,152,41,'description_3'), (15,193,41,'start_text'),
           (16,234,41,'end_text'), (17,275,41,'reward_text'))
NUMBERS = ((0,0,'B','index'), (1,1,'B','branch'), (3,2,'H','start_npc_id'),
           (10,4,'H','end_npc_id'), (5,6,'H','start_time_raw'),
           (6,8,'H','end_time_raw'), (8,10,'H','rebirth_level_lower_raw'),
           (9,12,'H','rebirth_level_upper_raw'), (18,15,'B','accept_count_raw'))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class DailyNative(_NativeRows):
    HEAP = 0x3500000
    FILE = 0x12340000

    def __init__(self, image, lines):
        super().__init__(image)
        self.lines = list(lines)
        self.consumed = 0
        self.allocated = False
        self.vm.mem_map(self.HEAP, 0x10000)
        self.vm.mem_write(self.TABLE + 4, struct.pack('<I', self.FILE))
        self.vm.mem_write(self.TABLE + 8, struct.pack('<H', 19))
        self.calls = Counter()
        for address in (0x547e23, 0x547a95):
            self.vm.hook_add(self.uc.UC_HOOK_CODE, self.crt, begin=address, end=address)
        self.vm.hook_add(self.uc.UC_HOOK_CODE, self.observe)

    def observe(self, vm, address, size, context):
        if address in (0x457ff0,0x451a90,0x451be0,0x451b50,0x451ae0,0x458430):
            self.calls[f'{address:08x}'] += 1

    def crt(self, vm, address, size, context):
        sp = vm.reg_read(self.x86.UC_X86_REG_ESP)
        ret, a, b, c = struct.unpack('<4I', vm.mem_read(sp,16))
        if address == 0x547e23:
            require(0x457ff0 <= ret < 0x458430 and not self.allocated, 'Unexpected calloc caller')
            require(a == len(self.lines) and b == 316 and a*b <= 0x10000, 'Unexpected calloc size')
            self.allocated = True
            vm.mem_write(self.HEAP, bytes(a*b))
            result = self.HEAP
        else:
            require(0x451a90 <= ret < 0x451ae0 and b == 4096 and c == self.FILE, 'Unexpected fgets caller')
            require(self.STACK <= a and a+b <= self.STACK+0x10000, 'fgets outside stack')
            if self.consumed == len(self.lines):
                result = 0
            else:
                raw = self.lines[self.consumed].replace(b'\r\n',b'\n')
                require(raw.endswith(b'\n') and len(raw)<b and b'\0' not in raw, 'Invalid text line')
                vm.mem_write(a,raw+b'\0')
                self.consumed += 1
                result = a
        vm.reg_write(self.x86.UC_X86_REG_EAX,result)
        vm.reg_write(self.x86.UC_X86_REG_ESP,sp+4)
        vm.reg_write(self.x86.UC_X86_REG_EIP,ret)

    def call(self, address, *args):
        self.reg('ECX',self.TABLE)
        self.reg('ESP',self.SP)
        self.vm.mem_write(self.SP,struct.pack('<'+'I'*(1+len(args)),self.RETURN,*args))
        self.vm.emu_start(address,self.RETURN,count=2000000,timeout=10000000)
        require(self.vm.reg_read(self.x86.UC_X86_REG_EIP)==self.RETURN, f'Incomplete native return {address:x}')
        require(self.vm.reg_read(self.x86.UC_X86_REG_ESP)==self.SP+4+4*len(args), 'Native stack mismatch')
        return self.vm.reg_read(self.x86.UC_X86_REG_EAX)

    def parse(self):
        require(self.call(0x457ff0,len(self.lines))==1, 'Native parser rejected source')
        require(self.consumed==len(self.lines), 'Native source not completely consumed')
        count=struct.unpack('<H',self.vm.mem_read(self.TABLE+0xfc2dc,2))[0]
        require(count==len(self.lines),'Native count differs')
        return [bytes(self.vm.mem_read(self.HEAP+i*316,316)) for i in range(count)]

    def lookup(self, pair, expected):
        sentinel=b'\xa5'*316
        self.vm.mem_write(self.OUTPUT,sentinel)
        result=self.call(0x458430,*pair,self.OUTPUT)
        require(result==int(expected is not None),'Lookup return mismatch')
        require(bytes(self.vm.mem_read(self.OUTPUT,316))==(sentinel if expected is None else expected), 'Lookup copy mismatch')


def decode_row(raw):
    require(len(raw)==316,'Wrong row size')
    fields={name:struct.unpack_from('<'+fmt,raw,offset)[0] for _,offset,fmt,name in NUMBERS}
    fields['discriminator_is_R']=raw[14]
    fields['weekday_mask']=struct.unpack_from('<I',raw,16)[0]
    strings={}
    for _,offset,capacity,name in STRINGS:
        block=raw[offset:offset+capacity]
        text=block.split(b'\0',1)[0]
        strings[name]={'block_hex':block.hex(),'nul_terminated_in_block':b'\0' in block,
                       'cp950_hex':text.hex(),'display':text.decode('cp950',errors='backslashreplace')}
    return dict(scalars=fields,strings=strings)


def expected_row(tokens):
    # Match actual ordered unbounded copies, including source's42-byte strings
    # into41-byte blocks. A following field/row can overwrite the spill.
    row=bytearray(512)
    token=lambda i:tokens[i] if i<len(tokens) else b''
    for column,offset,fmt,_ in NUMBERS:
        value=int(token(column)) if token(column) else 0
        struct.pack_into('<'+fmt,row,offset,value & (255 if fmt=='B' else 65535))
    require(len(token(4))==8,'Weekday source width')
    struct.pack_into('<I',row,16,sum(1<<i for i in range(7) if token(4)[i+1:i+2]==b'1'))
    row[14]=int(token(7)[:1] in (b'R',b'r'))
    for column,offset,capacity,_ in STRINGS:
        data=token(column)
        require(len(data)<150,'Source exceeds native local string buffer')
        row[offset:offset+len(data)+1]=data+b'\0'
    return bytes(row[:316])


def audit(client):
    sys.path.insert(0,str(ROOT/'artifacts/tooling/crypto-oracle-python'))
    import pefile
    exe=(client/'God2.exe').read_bytes()
    require(sha(exe)==CLIENT_SHA,'Unqualified current PE')
    pe=pefile.PE(data=exe)
    require(pe.OPTIONAL_HEADER.ImageBase==0x400000 and pe.FILE_HEADER.Machine==0x14c,'Wrong PE architecture/base')
    image=pe.get_memory_mapped_image()
    packed=(client/SOURCE).read_bytes()
    require(sha(packed)==SOURCE_SHA,'Unqualified daily source')
    plain=decode_csvz(packed)
    require(sha(plain)==DECODED_SHA,'Unqualified decoded daily source')
    source=parse_table('daily',plain)
    lines=plain.splitlines(keepends=True)[5:]
    require(len(lines)==85 and source['declared_records']==85,'Unexpected row count')
    native=DailyNative(image,lines)
    parsed=native.parse()
    first={}
    rows=[]
    for ordinal,(record,raw) in enumerate(zip(source['records'],parsed)):
        tokens=[bytes.fromhex(v) for v in record['raw_fields_hex']]
        require(raw==expected_row(tokens),f'Full native row mismatch {ordinal}')
        pair=tuple(raw[:2]); first.setdefault(pair,raw)
        rows.append(dict(ordinal=ordinal,**record,parsed316_hex=raw.hex(),parsed316_sha256=sha(raw),**decode_row(raw)))
    for pair,raw in first.items():native.lookup(pair,raw)
    native.lookup((255,255),None)
    require((0,0) in first,'Pair zero missing');native.lookup((0,0),first[(0,0)])
    # Duplicate lookup regression uses only two actual complete source records.
    # Patch the second native key in isolated memory; no invented source values.
    second=parsed[1]
    native.vm.mem_write(native.HEAP+316,parsed[0][:2]+second[2:])
    native.lookup(tuple(parsed[0][:2]),parsed[0])
    native.vm.mem_write(native.HEAP+316,second)
    require(bytes(native.vm.mem_read(native.HEAP,85*316))==b''.join(parsed),'Lookup changed parsed catalog')
    require(sha(b''.join(parsed))==CATALOG_SHA,'Qualified parsed catalog fingerprint changed')
    require(sha((client/'God2.exe').read_bytes())==CLIENT_SHA and
            sha((client/SOURCE).read_bytes())==SOURCE_SHA,'Current input changed during native audit')
    return {'schema':'god2-current-daily-quest-native316-v1','qualification':'NATIVE_VERIFIED_DISPLAY_ONLY',
        'executable_quest_rules':False,'client_sha256':CLIENT_SHA,'source_file':SOURCE,
        'source_sha256':SOURCE_SHA,'decoded_sha256':DECODED_SHA,'source_header':source['header_fields'],
        'source_preamble_hex':source['preamble_hex'],'row_count':85,'record_size':316,
        'parsed_catalog_sha256':sha(b''.join(parsed)),
        'code_sha256':{name:sha(image[start:end]) for name,start,end in
            [('parser457ff0',0x57ff0,0x58430),('lookup458430',0x58430,0x58490),('tokenizer_accessors',0x51a90,0x51cd2)]},
        'native':{'status':'PASS','full_parser_return':True,'all_unique_lookup_returns':len(first),
            'missing_lookup_unchanged':True,'pair_zero_lookup':True,'duplicate_first_match':True,
            'calls':dict(sorted(native.calls.items())),
            'adapters':['calloc547E23','fgets547A95 text CRLF-to-LF','sscanf5480B4 decimal']},
        'rows':rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client',type=Path,default=ROOT.parent/'God2')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=audit(args.client)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','rows':result['row_count'],'parsed_catalog_sha256':result['parsed_catalog_sha256'],'output_sha256':sha(args.output.read_bytes())}))


if __name__=='__main__':main()
