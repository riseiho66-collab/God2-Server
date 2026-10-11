"""Original x86 bank items: native drag, quantity, pages and raw48 refresh.

Frozen bank money sources are imported, never changed. Presentation boundaries
are stubbed; no server economic rule or real Windows UI acceptance is inferred.
"""
import hashlib,json,struct
from pathlib import Path
import pefile
from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP
from tools.strike_lab.current_bank_20261002 import BankOracle
from tools.strike_lab.current_party_20261002 import UI,BODY
from tools.strike_lab.current_protocol_coverage import qualified_image,NativeLengths
ROOT=Path(__file__).resolve().parents[2]


class ItemsOracle(BankOracle):
    def __init__(self,raw):
        super().__init__(raw)
        del self.helpers[0x471610]
        del self.helpers[0x471720]
        self.helpers.update({0x547af7:0,0x4b2330:4,0x4b2620:4})
        self.put(UI+0x232dd0,'<h',8);self.flags(8,0x10)
        self.slot_draws=[];self.text_draws=[]
        catalog,record,mouse=0x32000000,0x33000000,0x34000000
        self.vm.mem_map(catalog,0xc0000);self.vm.mem_map(record,0x1000);self.vm.mem_map(mouse,0x20000)
        self.put(UI+0xcff70,'<I',catalog);self.put(UI+0xcff68,'<I',mouse)
        self.put(catalog+0xb2d40+3107*4,'<I',record)
        self.put(record+0x116,'<HH',0x22,99)
        self.put(record+0x11b,'<B',1)
        self.put(UI+0x839c0,'<I',3793)

    def hook(self,vm,address,size,data):
        if address in (0x5077c0,0x547af7) or (address in (0x507b20,0x507bb0) and
                int.from_bytes(self.read(vm.reg_read(UC_X86_REG_ESP)+4,2),'little')==8):
            esp=vm.reg_read(UC_X86_REG_ESP);ret=struct.unpack('<I',self.read(esp,4))[0]
            args=struct.unpack('<5I',self.read(esp+4,20));self.calls.append((address,args[:4]))
            cleanup=0
            if address==0x547af7:
                vm.mem_write(args[0],str(args[2]).encode()+b'\0')
            elif address==0x5077c0:
                self.text_draws.append({'widget':args[1]&0xffff,'index':args[2],
                    'format':hex(args[3]),'argument':args[4] if args[3]!=0x5b4640 else None})
            else:
                self.flags(8,0x30 if address==0x507b20 else 0x10);cleanup=4
            vm.reg_write(UC_X86_REG_EIP,ret);vm.reg_write(UC_X86_REG_ESP,esp+4+cleanup);return
        if address==0x5068c0:
            args=struct.unpack('<4I',self.read(vm.reg_read(UC_X86_REG_ESP)+4,16))
            self.slot_draws.append({'widget':args[0]&0xffff,'kind':args[1],
                                   'slot':args[2]&0xffff,'image':args[3]})
        super().hook(vm,address,size,data)

    def raw_cell(self,page,slot,quantity=10,kind=0):
        meta=struct.pack('<HH',3107,kind)+bytes(range(4,20))
        raw=bytes([quantity,slot,0,0])+meta
        self.vm.mem_write(self.cell(page,slot),raw);return raw


def prove():
    raw=qualified_image();exe=(ROOT.parent/'God2/God2.exe').read_bytes();mapped=pefile.PE(data=exe).get_memory_mapped_image()
    regions=((0x471610,0x471760),(0x4719b0,0x4724e0),(0x497510,0x497920),
             (0x49b720,0x49b7b0),(0x49f010,0x49f8d0),(0x4c9a20,0x4c9bd0),
             (0x4c9ed0,0x4ca600),(0x459a60,0x459a90))
    for a,b in regions:assert mapped[a-0x400000:b-0x400000]==raw[a-0x400000:b-0x400000],hex(a)
    assert NativeLengths(raw).query(0x48)[0]==29
    cases=[]
    def passed(case,**details):cases.append({'case':case,**details})
    for page in range(6):
        for slot in (0,2,49):
            for quantity in (0,1,10):
                o=ItemsOracle(raw);meta=bytes(20) if quantity==0 else struct.pack('<H',3107)+bytes(range(2,20))
                o.vm.mem_write(o.cell(page,slot),b'\xcc'*24)
                body=bytes([page,0xa1,0xa2,0xa3,quantity,slot,0xb1,0xb2])+meta
                o.call(0x471e50,BODY,body=body)
                assert o.read(o.cell(page,slot),24)==bytes([quantity,slot,0xcc,0xcc])+meta
                assert o.u32(UI+0x839a8+page*4)==1
                assert len(o.slot_draws)==(page==0)
                if page==0:
                    draw=o.slot_draws[-1]
                    assert draw['slot']==slot and draw['widget']==6
                    assert (draw['kind'],draw['image'])==((0x41,0xffffffff) if not quantity else (0x22,99))
                    text=o.text_draws[-1]
                    assert text['widget']==7 and text['index']==slot
                    assert text['argument']==(quantity if quantity else None)
                passed('48_load_or_clear_raw_metadata_and_native_draw',page=page,slot=slot,quantity=quantity)
    # All six storage pages are loadable, while UI page arrows only expose the
    # edition-dependent two or three pages. No page request is emitted.
    o=ItemsOracle(raw)
    for page in range(6):
        body=bytes([page,0,0,0,10,2,0,0])+struct.pack('<H',3107)+bytes(18)
        o.call(0x471e50,BODY,body=body)
    before=o.read(UI+0x839cc,7200)
    o.slot_draws.clear();o.text_draws.clear();o.call(0x4719b0,56,1)
    assert o.u32(UI+0x839a4)==1 and not o.queued
    assert o.read(UI+0x839cc,7200)==before and len(o.slot_draws)==50
    assert any(x['slot']==2 and x['image']==99 for x in o.slot_draws)
    assert o.text_draws[0]=={'widget':6,'index':2,'format':'0x5823b4','argument':2}
    passed('page_arrow_uses_preloaded_cells_and_draws_50_no_C2S',page=1)
    for quantity in (1,3,10):
        o=ItemsOracle(raw);o.put(UI+0x855f0,'<h',0)
        o.vm.mem_write(UI+0x8560c,bytes([10,0,0,0])+struct.pack('<H',3107)+bytes(18))
        original=o.read(UI+0x8560c,24)
        o.call(0x4723a0,2,1)
        assert o.u32(UI+0x23d5e4)==2 and o.u32(UI+0x23d5ec)==10
        assert o.read(UI+0x23d5f4,6)==struct.pack('<HBBBB',3793,0,0,2,10)
        assert o.visible(8) and not o.queued
        o.put(UI+0x23d5e8,'<I',quantity);o.call(0x4c9ed0)
        expected=b'\x63'+struct.pack('<HBBBB',3793,0,0,2,quantity)
        assert o.queued==[expected] and o.read(UI+0x8560c,24)==original
        passed('real_bag_to_bank_quantity_modal_mode2',quantity=quantity,record_hex=expected.hex(),optimistic_bag_mutation=False)
    for quantity in (1,3,10):
        o=ItemsOracle(raw);o.put(UI+0x83994,'<h',2);original=o.raw_cell(0,2)
        o.call(0x49f010,0x17,1,1)
        assert o.u32(UI+0x23d5e4)==3 and o.u32(UI+0x23d5ec)==10
        assert o.read(UI+0x23d5f4,6)==struct.pack('<HBBBB',3793,0,2,1,10)
        assert o.visible(8) and not o.queued
        o.put(UI+0x23d5e8,'<I',quantity);o.call(0x4c9ed0)
        expected=b'\x64'+struct.pack('<HBBBB',3793,0,2,1,quantity)
        assert o.queued==[expected] and o.read(o.cell(0,2),24)==original
        passed('real_bank_to_bag_quantity_modal_mode3',quantity=quantity,record_hex=expected.hex(),optimistic_bank_mutation=False)
    for destination_quantity in (0,7):
        o=ItemsOracle(raw);o.put(UI+0x83994,'<h',2)
        source=o.raw_cell(0,2,10);dest=(bytes(24) if destination_quantity==0 else o.raw_cell(0,3,7))
        o.call(0x4719b0,3,1)
        assert o.queued==[b'\x65'+struct.pack('<HBBBB',3793,0,2,3,1)]
        assert o.read(o.cell(0,2),24)==dest and o.read(o.cell(0,3),24)==source
        assert not o.visible(8)
        passed('real_bank_drag65_swaps_whole_raw24_cells_not_one_item',source_quantity=10,destination_quantity=destination_quantity)
    for kind in (0,0xd,0x20,0x22):
        for destination in (0,1,2,49):
            o=ItemsOracle(raw);o.put(UI+0x855f0,'<h',0)
            o.vm.mem_write(UI+0x8560c,bytes([1,0,0,0])+struct.pack('<HH',3107,kind)+bytes(16))
            o.call(0x4723a0,destination,1)
            allowed=(destination<2)==(kind in (0xd,0x20,0x22))
            assert bool(o.queued)==allowed
            passed('real_bank_slot_kind_compatibility',metadata_kind=kind,destination=destination,allowed=allowed)
    # 48 always replaces all20 metadata bytes, so a fresh 46mode0 followed by
    # qualified48 snapshots suffices without7/12. 7/12 keep upper metadata.
    o=ItemsOracle(raw);o.raw_cell(0,2,10)
    clear=bytes([0,0,0,0,0,2,0,0])+bytes(20)
    o.call(0x471e50,BODY,body=clear)
    assert o.read(o.cell(0,2),24)[4:]==bytes(20)
    passed('48_zero_metadata_clears_old_item_without46mode7_or12')
    result={'scope':'original x86 emulator only, external presentation boundaries stubbed, not live-client or server authority',
            'passed':len(cases),'failed':0,'cases':cases,'client_sha256':hashlib.sha256(exe).hexdigest(),
            'mapped_sha256':hashlib.sha256(raw).hexdigest(),'matched_regions':[[hex(a),hex(b)] for a,b in regions],
            'contract':{'48':'logical29 pageBYTE@1 opaque3 qtyBYTE@5 slotBYTE@6 opaque2 metadata20@9',
                        '63':'logical7 targetWORD@1 pageBYTE@3 bagSourceBYTE@4 bankDestBYTE@5 quantityBYTE@6',
                        '64':'logical7 targetWORD@1 pageBYTE@3 bankSourceBYTE@4 bagDestBYTE@5 quantityBYTE@6',
                        '65':'logical7 targetWORD@1 pageBYTE@3 bankSourceBYTE@4 bankDestBYTE@5 constant1@6; whole raw24 swap in caller'},
            'UI':'bank232DD2 slotcontrol0..49; 55prev/56next; bankSidebar232DD4 quantitylabels0..49; quantity232DD0 edit4 accept2 modes2/3',
            'limits':'storage6x50 exists; editionfield232F64==1 UI pages0..1 otherwise0..2; no proof original unlock rule',
            'unproved':['live rendered sprite/hitrects','server item authority/eligibility','original capacity/unlock rules']}
    out=ROOT/'artifacts/research/native-bank-items-20261002/oracle.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'passed':len(cases),'failed':0,'evidence':str(out)}));return result

if __name__=='__main__':prove()
