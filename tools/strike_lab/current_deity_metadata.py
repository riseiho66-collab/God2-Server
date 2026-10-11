"""Original ItemType -> GOD lookup and396-byte metadata parser, no formulas.

004561A7..004561D7 routes a recognized section through00459380 then004599B0.
The latter indexes and calls00459420. GOD is category ordinal2, selector0;
absence from the36 first-match item tags does not imply a different loader.
"""
import hashlib
import struct
from .current_item_metadata import NativeItemMetadata
from .recover_companion_growth import parse_sections,fields

class NativeDeityMetadata(NativeItemMetadata):
    ITEM_SECTIONS=('GOD',)
    CODE=NativeItemMetadata.CODE+((0x591c0,0x59350),(0x59380,0x5941b),(0x148810,0x148848))
    CATEGORIES=0x3800000

    def __init__(self):
        super().__init__()
        self.category_rows=parse_sections(self.decoded,('ItemType',))['ItemType']['records']
        if len(self.category_rows)!=46:raise ValueError('Current ItemType count changed')
        size=46*0x642
        self.vm.mem_map(self.CATEGORIES,0x20000)
        # Original59150 uses calloc(count,642h). Execute row slices against
        # that zeroed layout; allocation/file-stream adapters are not tested.
        self.vm.mem_write(self.CATEGORIES,b'\xa5'*16+bytes(size)+b'\xa5'*16)
        self.category_base=self.CATEGORIES+16
        for ordinal,row in enumerate(self.category_rows):
            self.tokenize(row,len(fields(row)))
            start=self.category_base+ordinal*0x642
            self.reg('EBP',start);self.reg('EBX',self.TABLE)
            self.vm.mem_write(self.SP+0x10,struct.pack('<I',self.TABLE))
            self.row(0x591c0,0x59350,range(len(fields(row))),
                     [(start,start+0x642),(self.TABLE+0xd2cc4,self.TABLE+0xd2d54)])
        if bytes(self.vm.mem_read(self.CATEGORIES,16))!=b'\xa5'*16 or bytes(self.vm.mem_read(self.category_base+size,16))!=b'\xa5'*16:
            raise AssertionError('Original category row exceeded allocation')
        self.vm.mem_write(self.TABLE+0xd2aa4,struct.pack('<IH',self.category_base,46))
        self.vm.mem_protect(self.CATEGORIES,0x20000,self.uc.UC_PROT_READ)
        self.binding=self.lookup_section('GOD')
        if self.binding!=(2,0):raise ValueError('Original GOD category binding changed')

    def lookup_section(self,section):
        raw=section.encode('ascii')
        if not 1<=len(raw)<=16:raise ValueError('Section query bound')
        self.vm.mem_write(self.INPUT,raw+b'\0');self.vm.mem_write(self.OUTPUT,b'\xa5'*16)
        found=self.call(0x59380,self.INPUT,self.OUTPUT,self.OUTPUT+4,
                        allowed=((self.OUTPUT,self.OUTPUT+1),(self.OUTPUT+4,self.OUTPUT+5)))
        if not found:raise ValueError('Original category section missing')
        out=bytes(self.vm.mem_read(self.OUTPUT,16));expected=bytearray(b'\xa5'*16)
        expected[0]=out[0];expected[4]=out[4]
        if out!=expected:raise AssertionError('Original category lookup output canary')
        return out[0],out[4]

    def section_selector(self,section):
        if section!='GOD':raise ValueError('Only qualified GOD section')
        ordinal,selector=self.lookup_section(section)
        if (ordinal,selector)!=self.binding:raise AssertionError('GOD category lookup changed')
        return selector

    def category_proof(self):
        data=bytes(self.vm.mem_read(self.category_base,46*0x642))
        return dict(category_count=46,category_stride=0x642,god_ordinal=2,branch_selector=0,
            category_bytes_sha256=hashlib.sha256(data).hexdigest(),
            source_rows=[dict(source_line=row['source_line'],raw_record_hex=row['raw_record_hex']) for row in self.category_rows],
            scope='Original tokenizer, full46 category row slices,59380 lookup. Zeroed allocation/stream fixture, no live writes.')
