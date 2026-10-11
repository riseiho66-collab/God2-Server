"""Execute original deity portrait mapping and image selection, read-only assets.

ROM chunks are relocated into the native layout; this does not certify the
file loader or display blitter. No running-client memory writes or injection.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from .current_item_metadata import NativeItemMetadata
from .current_four_stat_ui_binding import CLIENT, parse_rom
from .omega_assets import decode_csvz
from .recover_companion_growth import parse_sections,fields

RAW_SHA='b24167375a7ad1de614bb4d41e55190d7a9e6538e9e0b6064f284c8f569f8b4e'
PLAIN_SHA='590693a6d7a5ad47c5addd3d36ea9352ea8ca22c658060d935c26dbe16ed1570'

class NativePortrait(NativeItemMetadata):
    CODE=NativeItemMetadata.CODE+((0xa9ac0,0xa9ae9),(0x1e710,0x1e7b2))
    BANK=0x3800000
    ASSETS=0x3900000

    def __init__(self):
        super().__init__()
        raw=(CLIENT/'Data3/Flow/Pic_God.romZ').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=RAW_SHA:raise ValueError('Portrait ROM changed')
        plain=decode_csvz(raw)
        if hashlib.sha256(plain).hexdigest()!=PLAIN_SHA:raise ValueError('Decoded portrait ROM changed')
        self.rom=parse_rom(plain,name_encoding='cp950')
        if len(self.rom['actions'])!=42:raise ValueError('Native portrait count changed')
        self.vm.mem_map(self.BANK,0x2000)
        self.vm.mem_map(self.ASSETS,0x200000)
        top=self.ASSETS
        def store(data):
            nonlocal top
            at=top;top+=(len(data)+15)&~15
            if top>self.ASSETS+0x200000:raise ValueError('Portrait resource bound')
            self.vm.mem_write(at,bytes(data));return at
        for i,palette in enumerate(self.rom['palettes']):
            self.vm.mem_write(self.BANK+8+i*4,struct.pack('<I',store(palette['data'])))
        images={i:store(image['data']) for i,image in enumerate(self.rom['images'])}
        for i,pointer in images.items():
            self.vm.mem_write(self.BANK+0x8c+i*4,struct.pack('<I',pointer))
        self.vm.mem_write(self.BANK+0x108c,struct.pack('<I',42))
        self.expected=[]
        for ordinal,action in enumerate(self.rom['actions']):
            if len(action['steps'])!=1 or len(action['pools'])>4:raise ValueError('Unqualified ACT layout')
            steps=action['steps'][0]['data']
            selected=next(steps[i:i+10] for i in range(0,len(steps),10) if steps[i]==0)
            pool_index=selected[3]
            pool=action['pools'][pool_index]['data']
            image_id=struct.unpack_from('<H',pool,6)[0]
            header=bytearray(0x640);header[:48]=action['data']
            struct.pack_into('<I',header,0x30,store(steps))
            for i,pool in enumerate(action['pools']):
                struct.pack_into('<I',header,0x630+4*i,store(pool['data']))
            self.vm.mem_write(self.BANK+0x1090+ordinal*4,struct.pack('<I',store(header)))
            self.expected.append((image_id,images[image_id]))
        self.vm.mem_protect(self.BANK,0x2000,self.uc.UC_PROT_READ)
        self.vm.mem_protect(self.ASSETS,0x200000,self.uc.UC_PROT_READ)

    def portrait(self,key):
        self.vm.mem_write(self.OUTPUT,b'\xa5'*64)
        self.call(0xa9ac0,key,self.OUTPUT,self.OUTPUT+4,this=self.OWNER,
                  allowed=((self.OUTPUT,self.OUTPUT+8),))
        bank,action=struct.unpack('<Ii',self.vm.mem_read(self.OUTPUT,8))
        if bank!=5 or action!=(key-1 if key<=100 else key-67):
            raise AssertionError('Native portrait mapper mismatch')
        image=None
        if action>=0:
            pointer=self.call(0x1e710,self.BANK,action,self.OUTPUT+16,
                              self.OUTPUT+20,self.OUTPUT+24,
                              allowed=((self.OUTPUT+16,self.OUTPUT+26),))
            if action<42:
                image_id,expected=self.expected[action]
                if pointer!=expected or struct.unpack('<H',self.vm.mem_read(self.OUTPUT+24,2))[0]!=image_id:
                    raise AssertionError('Original image selector mismatch')
                image=dict(index=image_id,pointer=hex(pointer),name=self.rom['actions'][action]['name'])
            elif pointer!=0:raise AssertionError('Original out-of-bank rejection missing')
        if bytes(self.vm.mem_read(self.OUTPUT+8,8))!=b'\xa5'*8 or bytes(self.vm.mem_read(self.OUTPUT+26,38))!=b'\xa5'*38:
            raise AssertionError('Portrait output canary overwritten')
        return dict(key=key,bank=bank,action=action,image=image,
                    restored_template_qualified=1<=key<=34,
                    named_profession_qualified=101<=key<=108)

def audit():
    native=NativePortrait()
    definitions=parse_sections(native.decoded,('GOD',))['GOD']['records']
    keys=[int(fields(row)[0])-0xaf0 for row in definitions]
    if keys!=list(range(1,35)):raise ValueError('Current deity source keys changed')
    rows=[native.portrait(key) for key in range(128)]
    return dict(raw_sha256=RAW_SHA,decoded_sha256=PLAIN_SHA,portrait_count=42,
                native_template_keys=keys,
                keys=rows,executed_instruction_count=len(native.executed),
                key100_rejected_by_original_image_selector=rows[100]['image'] is None,
                scope='Unchanged native mapper and image selector; relocated original ROM. Not growth/combat/acquisition.')

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();result=audit();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='keys'},ensure_ascii=False))

if __name__=='__main__':main()
