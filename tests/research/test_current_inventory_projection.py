"""Current PE full 3B/41 consumers, real MED definitions, inactive render controls.

No client/socket/DB process. Synthetic instance metadata is CUSTOM baseline.
The native lookup and icon mapping run; actual drawing/name tooltip is not tested.
"""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import test_inventory_request_blackbox_followup as compiler
from tools.strike_lab.current_item_metadata import NativeItemMetadata
from tools.strike_lab import recover_companion_growth as growth
from tools.strike_lab.current_item_transition import (
    NativeItemTransition, BASE, UI, SLOTS, SP, STACK, RETURN, PACKET, COMPANION,
    DEFINITIONS, UC_PROT_READ, UC_PROT_WRITE, UC_X86_REG_ESP, UC_X86_REG_ECX,
    UC_X86_REG_EIP, UC_X86_REG_EAX)

ROOT=Path(__file__).resolve().parents[2]
PIN='6bf75ef8ac1e0f6b2240800ff841d205788bd1b6512149584b5386b10f431e98'
FIXTURE=r'''
#include "protocol/RecoveredInventoryProjection.h"
#include <charconv>
#include <iostream>
#include <sstream>
#include <string>
int main(){
 for(std::string line;std::getline(std::cin,line);){
  std::istringstream in(line);unsigned slot,count;std::string hex,extra;
  if(!(in>>slot>>count>>hex)||(in>>extra)||slot>255||count>255||hex.size()!=40)return 3;
  god2::RecoveredInventoryProjection::Slot s{static_cast<std::uint8_t>(slot),static_cast<std::uint8_t>(count),{}};
  for(unsigned i=0;i<20;++i){unsigned n=0;auto p=std::from_chars(hex.data()+2*i,hex.data()+2*i+2,n,16);
   if(p.ec!=std::errc{}||p.ptr!=hex.data()+2*i+2)return 4;s.metadata[i]=static_cast<std::uint8_t>(n);}
  const auto encoded=god2::RecoveredInventoryProjection::encode(s);
  if(!encoded){std::cout<<"reject\n";continue;}
  constexpr char digits[]="0123456789abcdef";
  for(auto b:*encoded)std::cout<<digits[b>>4]<<digits[b&15];std::cout<<'\n';
 }
}
'''

class ProjectionMetadata(NativeItemMetadata):
    ITEM_SECTIONS=NativeItemMetadata.ITEM_SECTIONS+('SPI',)

def current_image():
    raw=(ROOT.parent/'God2/God2.exe').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN: raise RuntimeError('Current PE identity mismatch')
    pe=struct.unpack_from('<I',raw,60)[0]
    sections=struct.unpack_from('<H',raw,pe+6)[0]
    optsize=struct.unpack_from('<H',raw,pe+20)[0]
    image=bytearray(struct.unpack_from('<I',raw,pe+24+56)[0])
    headers=struct.unpack_from('<I',raw,pe+24+60)[0]
    image[:headers]=raw[:headers]
    for i in range(sections):
        at=pe+24+optsize+40*i
        _,rva,size,offset=struct.unpack_from('<IIII',raw,at+8)
        image[rva:rva+size]=raw[offset:offset+size]
    return bytes(image)

class ProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image=current_image()
        cls.temp=tempfile.TemporaryDirectory(prefix='god2-projection-')
        cls.addClassCleanup(cls.temp.cleanup)
        old=compiler.FIXTURE
        try:
            compiler.FIXTURE=FIXTURE
            cls.exe=compiler.build_fixture(Path(cls.temp.name))
        finally: compiler.FIXTURE=old
        loader=ProjectionMetadata()
        # RomMaps setup used the preserved mapped image; require its complete
        # permitted code ranges to be byte-identical to the current PE.
        for lo,hi in loader.CODE:
            if cls.image[lo:hi]!=loader.image[lo:hi]: raise RuntimeError('Native loader code changed')
        old_size=(len(loader.image)+4095)&~4095
        if len(cls.image)>old_size: loader.vm.mem_map(BASE+old_size,len(cls.image)-old_size)
        loader.vm.mem_write(BASE,cls.image)
        cls.definitions={item:loader.item_row('MED02',item-3101) for item in (3101,3107,3113)}
        map_index=next(i for i,row in enumerate(loader.sections['SPI']['records'])
                       if growth.decimal(growth.fields(row)[0])==5569)
        captured=ROOT/'artifacts/runs/native-town-map-item-catalog-20260921-01/native-town-map-item-catalog-20260921-01-result.json'
        raw=captured.read_bytes()
        if hashlib.sha256(raw).hexdigest()!='308e12397d17f8f947a5d51e7fd2f7d55efa298171532972784cdfd22a780c99':
            raise RuntimeError('Pinned map item native record changed')
        record=bytes.fromhex(json.loads(raw)['town_reward_item']['record_hex'])
        row=loader.sections['SPI']['records'][map_index]
        fields=growth.fields(row)
        if len(record)!=396 or record[8:8+len(fields[4])]!=fields[4]:
            raise RuntimeError('Native map definition does not match current SPI name')
        group,action=struct.unpack_from('<HH',record,0x116)
        cls.definitions[5569]={'source_line':row['source_line'],'record':record,
                              'group':group,'action':action}
        cls.vectors=0

    def candidate(self,commands):
        p=subprocess.run([str(self.exe)],input='\n'.join(commands)+'\n',text=True,
                         capture_output=True,timeout=20,check=True)
        lines=p.stdout.splitlines()
        self.assertEqual(len(lines),len(commands))
        return lines

    def native(self):
        n=NativeItemTransition()
        old_size=(len(n.image)+4095)&~4095
        if len(self.image)>old_size: n.vm.mem_map(BASE+old_size,len(self.image)-old_size)
        n.vm.mem_write(BASE,self.image) # Actual current mapped PE, not historical code.
        n.vm.mem_protect(DEFINITIONS,0xe0000,UC_PROT_READ|UC_PROT_WRITE)
        for ordinal,(item,d) in enumerate(self.definitions.items()):
            address=COMPANION+0x1000+ordinal*0x1000
            n.vm.mem_write(address,d['record'])
            n.vm.mem_write(DEFINITIONS+0xb2d40+item*4,struct.pack('<I',address))
        n.vm.mem_protect(DEFINITIONS,0xe0000,UC_PROT_READ)
        n.vm.mem_write(UI+0x85abd,b'\xff')
        return n

    def consume(self,n,logical):
        vm=n.vm
        offset=0
        while offset<len(logical):
            opcode=logical[offset];size={0x41:5,0x3b:25}[opcode]
            record=logical[offset:offset+size]
            self.assertEqual(len(record),size)
            slot=record[3] if opcode==0x41 else record[2]
            vm.mem_write(PACKET,record[1:])
            vm.mem_write(SP,struct.pack('<II',RETURN,PACKET))
            vm.reg_write(UC_X86_REG_ESP,SP);vm.reg_write(UC_X86_REG_ECX,UI)
            n._run(0x991e0 if opcode==0x41 else 0x98dd0,RETURN-BASE)
            self.assertEqual(vm.reg_read(UC_X86_REG_ESP),SP+8)
            for address,length in n.writes:
                self.assertTrue(STACK<=address and address+length<=STACK+0x4000 or
                    SLOTS+slot*24<=address and address+length<=SLOTS+(slot+1)*24,
                    f'Unexpected native write {address:x}+{length}')
            if opcode==0x3b:
                self.assertIn(0x59a60,n.visits)
                self.assertIn(0x9b720,n.visits)
            offset+=size

    def test_current_length_functions(self):
        n=self.native()
        for opcode,size in ((0x3b,25),(0x41,5)):
            entry=struct.unpack_from('<I',self.image,0x1324+opcode*4)[0]
            n.vm.mem_write(SP,struct.pack('<I',RETURN))
            n.vm.reg_write(UC_X86_REG_ESP,SP)
            n._run(entry-BASE,RETURN-BASE)
            self.assertEqual(n.vm.reg_read(UC_X86_REG_EAX),size)

    def test_poisoned_slot_baseline_and_explicit_metadata(self):
        cases=[]
        for item in self.definitions:
            for slot in (0,12,29):
                for count in (1,2,30,31,127):
                    for tail in (bytes(18),bytes(range(18))):
                        cases.append((slot,count,struct.pack('<H',item)+tail))
        responses=self.candidate([f'{s} {c} {m.hex()}' for s,c,m in cases])
        n=self.native()
        for (slot,count,metadata),text in zip(cases,responses,strict=True):
            with self.subTest(slot=slot,count=count,item=metadata[:2].hex(),tail=metadata[2:].hex()):
                before=bytes([0xa5])*1200
                n.vm.mem_write(SLOTS,before)
                logical=bytes.fromhex(text)
                self.assertEqual(len(logical),35)
                self.consume(n,logical)
                expected=bytearray(before);expected[slot*24]=count
                expected[slot*24+4:slot*24+24]=metadata
                self.assertEqual(bytes(n.vm.mem_read(SLOTS,1200)),bytes(expected))
                # Idempotence despite native 3B additive-count behavior.
                self.consume(n,logical)
                self.assertEqual(bytes(n.vm.mem_read(SLOTS,1200)),bytes(expected))
                type(self).vectors+=1

    def test_rejections_and_empty(self):
        cmds=['30 1 230c'+'00'*18,'255 1 230c'+'00'*18,
              '0 128 230c'+'00'*18,'0 0 230c'+'00'*18,'0 1 '+'00'*20]
        self.assertEqual(self.candidate(cmds),['reject']*len(cmds))
        n=self.native();n.vm.mem_write(SLOTS,bytes([0xa5])*1200)
        for slot in (0,29):
            output=self.candidate([f'{slot} 0 '+ '00'*20])[0]
            before=bytearray(n.vm.mem_read(SLOTS,1200))
            self.assertEqual(len(bytes.fromhex(output)),5)
            self.consume(n,bytes.fromhex(output))
            before[slot*24]=0;before[slot*24+4:slot*24+6]=b'\0\0'
            self.assertEqual(bytes(n.vm.mem_read(SLOTS,1200)),bytes(before))

    def test_baseline_keeps_native_definition_and_icon_lookup(self):
        n=self.native();vm=n.vm
        for item,definition in self.definitions.items():
            metadata=struct.pack('<H',item)+bytes(18)
            record=bytes.fromhex(self.candidate([f'12 2 {metadata.hex()}'])[0])
            self.consume(n,record)
            projected=struct.unpack('<H',vm.mem_read(SLOTS+12*24+4,2))[0]
            vm.mem_write(SP,struct.pack('<II',RETURN,projected))
            vm.reg_write(UC_X86_REG_ESP,SP);vm.reg_write(UC_X86_REG_ECX,DEFINITIONS)
            n._run(0x59a60,RETURN-BASE)
            pointer=vm.reg_read(UC_X86_REG_EAX)
            self.assertNotEqual(pointer,0)
            actual=bytes(vm.mem_read(pointer,396))
            self.assertEqual(actual,definition['record'])
            self.assertTrue(actual[8:].split(b'\0',1)[0]) # Loaded display name.
            vm.mem_write(PACKET+0x100,b'\xa5'*8)
            vm.mem_write(SP,struct.pack('<IIII',RETURN,projected,PACKET+0x100,PACKET+0x104))
            vm.reg_write(UC_X86_REG_ESP,SP);vm.reg_write(UC_X86_REG_ECX,UI)
            n._run(0x9b720,RETURN-BASE)
            self.assertEqual(vm.reg_read(UC_X86_REG_ESP),SP+16)
            output=bytes(vm.mem_read(PACKET+0x100,8))
            self.assertEqual(struct.unpack_from('<H',output,0)[0],definition['group'])
            self.assertEqual(struct.unpack_from('<H',output,4)[0],definition['action'])
            self.assertEqual(output[2:4]+output[6:8],b'\xa5'*4)

    @classmethod
    def tearDownClass(cls):
        # Test process exit, not report presence, is the acceptance authority.
        evidence={'current_pe_sha256':PIN,'vectors_executed':cls.vectors,
            'scope':'native full consumers, inactive controls; no live rendering or map acceptance',
            'instance_baseline':'CUSTOM id WORD plus 18 zero bytes',
            'records':{str(k):{'source_line':v['source_line'],'icon_group':v['group'],
                'icon_action':v['action'],'definition_sha256':hashlib.sha256(v['record']).hexdigest()}
                for k,v in cls.definitions.items()}}
        output=ROOT/'artifacts/reports/current-server-fill-20260926/inventory-projection-native.json'
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(evidence,indent=2),encoding='utf-8')

if __name__=='__main__': unittest.main()
