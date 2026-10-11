"""Pinned E3 receiver and first-generation pet panel. No original growth inference."""
import struct
from .current_monster_inspect_identity import NativeInspect, NativeItemMetadata, BASE
from .current_pet2_stat_labels import ASSET, RAW_SHA, PLAIN_SHA
from .current_four_stat_ui_binding import (CLIENT, IMAGE_PATH, IMAGE_SHA, pinned_read,
    decoded_source, parse_rom, select_action, descriptors, instructions, sha,
    X86_OP_MEM, X86_OP_IMM)

# name, original visual label, body offset, width, shift, mask, control, start, call
FIELDS=(
 ('current_hp','HP',0,2,0,0xffff,1,0xa1dd8,0xa1dee),
 ('current_mp','MP',4,2,0,0xffff,2,0xa1df3,0xa1e0a),
 ('maximum_hp','HP',2,2,0,0xffff,3,0xa1e58,0xa1e6f),
 ('maximum_mp','MP',6,2,0,0xffff,4,0xa1ebd,0xa1ed4),
 ('level','等級',0x23,1,0,0xff,5,0xa1ed9,0xa1eef),
 ('life_display_raw','生命',0x22,1,0,0xff,7,0xa1f33,0xa1f4b),
 ('physical_attack','物攻',8,4,0,0xfff,8,0xa1f99,0xa1fb2),
 ('physical_defense','物防',12,4,0,0xfff,9,0xa2000,0xa201a),
 ('magical_attack','魔攻',16,4,0,0xfff,10,0xa2068,0xa2082),
 ('magical_defense','魔防',20,4,0,0xfff,11,0xa20d0,0xa20e9),
 ('strength','力',16,4,12,0x3ff,13,0xa2138,0xa2155),
 ('constitution','體',16,4,22,0x3ff,12,0xa21a4,0xa21bb),
 ('intelligence','智',20,4,12,0x3ff,14,0xa220a,0xa2226),
 ('speed','速',20,4,22,0x3ff,15,0xa2274,0xa228b),
 ('strength_bonus','力+',24,4,24,0xff,21,0xa22e7,0xa22fe),
 ('constitution_bonus','體+',0x1e,1,0,0xff,20,0xa2303,0xa2319),
 ('intelligence_bonus','智+',0x1f,1,0,0xff,22,0xa231e,0xa2334),
 ('speed_bonus','速+',0x20,1,0,0xff,23,0xa2339,0xa2352),
 ('remaining_points','剩餘點數',0x24,2,0,0xffff,24,0xa2357,0xa236e),
 ('metal','金',8,4,12,0x3ff,25,0xa23bd,0xa23d9),
 ('wood','木',8,4,22,0x3ff,26,0xa2428,0xa243f),
 ('water','水',12,4,12,0x3ff,27,0xa248e,0xa24ab),
 ('fire','火',12,4,22,0x3ff,28,0xa24fa,0xa2511),
 ('earth','土',24,4,0,0x3ff,29,0xa2560,0xa257a),
 ('rebirth_count','轉生次數',0x27,1,0,0xff,30,0xa257f,0xa2595),
)

def audit():
    image=pinned_read(IMAGE_PATH,IMAGE_SHA)
    _,data=decoded_source(CLIENT/ASSET,RAW_SHA,PLAIN_SHA)
    panel,_=select_action(parse_rom(data),27)
    if panel['name']!='FPet_BGOpen' or struct.unpack_from('<4i',image,0x190e18)!=(0,0,252,427):
        raise ValueError('Original first-generation panel changed')
    code=instructions(image,0xa19f3,0xa1a1b)
    pushes=[i.operands[0].imm for i in code if i.mnemonic=='push' and i.operands[0].type==X86_OP_IMM]
    if pushes!=[-1,-1,0x590e28,0x3a98,0x590e18,28,27,36]:raise ValueError('Original panel constructor changed')
    controls=descriptors(image,0x190e38,32)
    fields=[]
    for name,label,offset,width,shift,mask,control,start,call in FIELDS:
        code=instructions(image,start,call+5)
        reads=[i for i in code if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[1].type==X86_OP_MEM
            and i.reg_name(i.operands[1].mem.base)=='ebx']
        shifts=[i.operands[1].imm for i in code if i.mnemonic=='shr']
        masks=[i.operands[1].imm for i in code if i.mnemonic=='and']
        pushes=[i.operands[0].imm for i in code if i.mnemonic=='push' and i.operands[0].type==X86_OP_IMM]
        if len(reads)!=1 or (reads[0].operands[1].mem.disp,reads[0].operands[1].size)!=(offset,width):
            raise ValueError('Native E3 field read changed: '+name)
        expected_mask=[mask] if width==4 and shift!=22 and shift!=24 else []
        expected_push_count=3 if name=='life_display_raw' else 2
        if shifts!=([shift] if shift else []) or masks!=expected_mask or len(pushes)!=expected_push_count or pushes[-1]!=control:
            raise ValueError('Native E3 extraction/control changed: '+name)
        if code[-1].mnemonic!='call' or code[-1].operands[0].imm!=0x1077c0:raise ValueError('Numeric consumer changed')
        fields.append(dict(name=name,label=label,body_offset=offset,logical_offset=offset+1,width=width,
            shift=shift,mask=mask,control=controls[control],start_rva=start,call_rva=call,code_sha256=sha(image[start:call+5])))
    return dict(image_sha256=IMAGE_SHA,asset_sha256=RAW_SHA,decoded_sha256=PLAIN_SHA,panel=panel,
        opcode=0xe3,logical_size=53,fields=fields,growth_formula_verified=False,wild_stats_verified=False)

class NativePet1(NativeInspect):
    ITEM_SECTIONS=('COM',)
    def __init__(self):
        NativeItemMetadata.__init__(self)
        self.flow_active=False
        self.vm.hook_add(self.uc.UC_HOOK_CODE,self._flow_code)
        self.vm.hook_add(self.uc.UC_HOOK_MEM_READ,self._flow_read)
        for address,size in ((self.MESSAGE,0x1000),(self.OWNER+0x232000,0x1000)):
            self.vm.mem_map(address,size,self.uc.UC_PROT_READ|self.uc.UC_PROT_WRITE)
        self.definition=self.item_row('COM',0,retain=True)
        if (self.definition['key'],self.definition['selector'])!=(24001,32):raise ValueError('COM binding changed')
        self.vm.mem_protect(self.MESSAGE,0x1000,self.uc.UC_PROT_READ)
        self.vm.mem_protect(self.RECORD,0x1000,self.uc.UC_PROT_READ)
        for offset in (0x232dc8,0x232e64,0x232e50):self.vm.mem_write(self.OWNER+offset,b'\xff\xff')
        self.vm.mem_write(self.OWNER+0xa6d4,b'\xa5'*(156+8))

    def receive(self,body):
        if len(body)!=52 or body[0x26] not in (42,43,44):raise ValueError('E3 body/slot')
        self.prepare();self.vm.mem_write(self.MESSAGE,body)
        self.vm.mem_write(self.SP,struct.pack('<2I',BASE+0x1000,self.MESSAGE))
        self.reg('ECX',self.OWNER)
        dest=self.OWNER+0xa6d8+(body[0x26]-42)*52
        before=bytes(self.vm.mem_read(self.OWNER+0xa6d4,164))
        trace=self.slice(0xa2b70,(0x1000,),((0xa2b70,0xa2c85),(0xa2980,0xa2a04),
            (0x59a60,0x59a7e),(0xad080,0xad09b),(0xad547,0xad54f)),((dest,dest+52),))
        if self.value('ESP')!=self.SP+8:raise AssertionError('E3 receiver stack imbalance')
        expected=bytearray(before)
        if 0xa2bc7 in trace['pcs']:expected[4+(body[0x26]-42)*52:4+(body[0x26]-41)*52]=body
        if bytes(self.vm.mem_read(self.OWNER+0xa6d4,164))!=expected:raise AssertionError('E3 copied outside selected row')
        for reg in ('EBX','EBP','ESI','EDI'):
            if self.value(reg)!=0xa5a5a5a5:raise AssertionError('E3 callee register '+reg)
        return dict(record_address=dest,trace=trace)

    def numeric_fields(self,record):
        values={}
        for name,_,_,_,_,_,control,start,call in FIELDS:
            self.prepare();self.reg('EBX',record);self.reg('ESI',self.OWNER)
            self.slice(start,(call,),((start,call),))
            count=6 if name=='life_display_raw' else 5
            args=struct.unpack('<'+'I'*count,self.vm.mem_read(self.value('ESP'),count*4))
            if args[2]!=control:raise AssertionError('Original panel selected wrong control')
            if name=='life_display_raw' and args[5]!=100:raise AssertionError('Original life denominator changed')
            values[name]=args[4]
        return values

    def progress(self,record):
        self.prepare();self.reg('EBX',record);self.reg('ESI',self.OWNER)
        self.slice(0xa1d63,(0xa1d9c,),((0xa1d63,0xa1d9c),))
        return struct.unpack('<f',self.vm.mem_read(self.SP+0x1c,4))[0]

def diagnostic_body(slot=42):
    body=bytearray((17*i+0x81)&255 for i in range(52))
    struct.pack_into('<H',body,0x1c,24001);body[0x26]=slot
    return bytes(body)

if __name__=='__main__':
    import json
    print(json.dumps(audit(),ensure_ascii=True,indent=2))
