from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_GRP_CALL,CS_GRP_JUMP,CS_GRP_RET
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-spi-allocation-zero-source-340')
BASE=OUT.parent;PIN=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
sha=lambda b:hashlib.sha256(b).hexdigest()
refs=[]
def ref(path,scope):
    b=path.read_bytes();refs.append(dict(path=str(path),bytes=len(b),sha256=sha(b),scope=scope,copied=False));return b
def put(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf8',newline='\n')
image=ref(PIN/'native-image.bin','Pinned mapped149c image, hashed in place')
original=ref(PIN/'originalPE.bin','Pinned originalPE5fc, hashed in place')
assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
native=OUT/'native';native.mkdir(exist_ok=True)
cuts=[]
def instructions(raw,start):
    ins=list(md.disasm(raw,start));assert sum(i.size for i in ins)==len(raw)
    return ins
def cut(name,start,end,scope,complete=False):
    raw=image[start-0x400000:end-0x400000];off=pe.get_offset_from_rva(start-0x400000)
    assert raw==original[off:off+len(raw)]
    ins=instructions(raw,start)
    branches=[dict(va=f'{i.address:08X}',mnemonic=i.mnemonic,target=i.op_str) for i in ins if i.group(CS_GRP_JUMP)]
    rets=[dict(va=f'{i.address:08X}',operands=i.op_str) for i in ins if i.group(CS_GRP_RET)]
    if complete:
        assert rets==[dict(va='0054A5A2',operands=''),dict(va='0054A5A7',operands='')]
        assert all(start<=int(b['target'],16)<end for b in branches)
    (native/(name+'.bin')).write_bytes(raw)
    (native/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+'\n'.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}' for i in ins)+'\n',encoding='utf8',newline='\n')
    cuts.append(dict(name=name,start_va=f'{start:08X}',end_exclusive_va=f'{end:08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,mapped_equal=True,original_pe_equal=True,scope=scope,returns=rets,branches=branches,direct_calls=[dict(va=f'{i.address:08X}',target=i.op_str) for i in ins if i.group(CS_GRP_CALL)]))
cut('byte-fill-complete',0x54a550,0x54a5a8,'New complete selected child; both returns, no callees',True)
cut('known-dispatch-category-row-loader-selected',0x456199,0x4561dc,'Existing complete dispatcher referenced below; selected formal argument wiring only')
cut('known-generic-byte11b-selector0-selected',0x459674,0x459700,'Existing complete generic method referenced below; bit preservation and selector0 default jump only')
known=[]
OLD=BASE/'tw-native-f4-list-definition-key-source-335/native'
for name,start,end in [('row-loader-complete',0x4599b0,0x459a5f),('category-loader-complete',0x459150,0x45937d),('category-lookup-complete',0x459380,0x45941b),('generic-record-parser-complete',0x459420,0x45995f),('section-dispatch-complete',0x456130,0x4570d6)]:
    path=OLD/(name+'.bin');raw=ref(path,'Already sealed335 complete method, independently compared; no recovery recredit')
    assert len(raw)==end-start
    off=pe.get_offset_from_rva(start-0x400000);assert raw==image[start-0x400000:end-0x400000]==original[off:off+len(raw)]
    ins=instructions(raw,start)
    known.append(dict(path=str(path),start_va=f'{start:08X}',end_exclusive_va=f'{end:08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,mapped_equal=True,original_pe_equal=True,returns=[dict(va=f'{i.address:08X}',operands=i.op_str) for i in ins if i.group(CS_GRP_RET)]))
path=BASE/'tw-native-rommaps-loader-source-339/native/allocation-helper-complete-with-cold-tail.bin'
raw=ref(path,'Already sealed339 complete allocator including cold tail; no recredit')
start=0x547e23;off=pe.get_offset_from_rva(start-0x400000)
assert len(raw)==141 and raw==image[start-0x400000:start-0x400000+len(raw)]==original[off:off+len(raw)]
known.append(dict(path=str(path),start_va='00547E23',end_exclusive_va='00547EB0',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,mapped_equal=True,original_pe_equal=True))
imports=[dict(dll=d.dll.decode('ascii'),name=(s.name or b'').decode('ascii'),iat_va=f'{s.address:08X}') for d in pe.DIRECTORY_ENTRY_IMPORT for s in d.imports if s.address==0x570398]
assert len(imports)==1 and imports[0]['dll'].lower()=='kernel32.dll' and imports[0]['name']=='HeapAlloc'
put('known-complete-method-comparisons.json',known);put('cuts.json',cuts)
tags=[]
for i in range(36):
    cell=0x5897ec+i*4;raw=image[cell-0x400000:cell-0x400000+4]
    off=pe.get_offset_from_rva(cell-0x400000);assert raw==original[off:off+4]
    va=struct.unpack('<I',raw)[0];end=image.index(b'\0',va-0x400000)+1;value=image[va-0x400000:end]
    soff=pe.get_offset_from_rva(va-0x400000);assert value==original[soff:soff+len(value)]
    tags.append(dict(index=i,cell_va=f'{cell:08X}',cell_original_pe_offset=off,pointer_hex=raw.hex(),string_va=f'{va:08X}',string_original_pe_offset=soff,raw_string_hex=value.hex(),string_sha256=sha(value),ascii=value[:-1].decode('ascii')))
assert len(tags)==36 and not any(t['raw_string_hex'].startswith(b'SPI'.hex()) for t in tags)
put('category36-tag-data.json',tags)
put('dependency-proof.json',dict(selected_import=imports,smallblock_success_call=dict(va='00547E9E',target='0054A550',argument1='EDI nonzero result from opaque54F58C',argument2=0,argument3='EBX original low32 count*stride product'),row_loader=dict(start='004599B0',end_exclusive='00459A5F',formal_count='signed lowWORD first stack argument',allocation_gate='count > 0 signed',stride=396,maximum_positive_product=32767*396,allocation_product_no32_overflow=True),category_loader=dict(start='00459150',end_exclusive='0045937D',formal_count='sign-extended lowWORD first stack argument',stride=1602,allocation_before_positive_row_gate=True,maximum_positive_product=32767*1602,positive_product_no32_overflow=True,negative_count_not_qualified=True),zero_helper=dict(start='0054A550',end_exclusive='0054A5A8',bytes=88,returns=['0054A5A2','0054A5A7'],callees=[],zero_length_no_stores=True,stores=['0054A573 BYTE alignment prefix','0054A591 REP STOSD bulk','0054A597 BYTE suffix'],required='Valid destination for requested length, normal DF-clear x86 calling environment; no fault/intervening modification'),conditional_spi=dict(category_selector_offset_hex='63D',selector_zero_if_no36_prefix_match_and_successful_zero_allocation=True,generic_selector_zero_takes='004596F8 ->00459933',byte11b_high_mask_hex='F0',selector0_unwritten_tail_hex='11C..18B',unwritten_tail_bytes=112,finite_string_bounds_separate_precondition=True,current_bank_observed=False,whole396_runtime_buffer_observed=False),native_execution=0,api_execution=0,scope='Source-only conditional initialization dependency; not observed native state or server authority'))
for folder in ['tw-native-f4-list-definition-key-source-335','tw-native-rommaps-loader-source-339']:
    sealpath=BASE/folder/'seal.json';ref(sealpath,'Upstream seal retained unchanged, referenced in place')
put('references.json',refs)
print(json.dumps(dict(new_complete_child_bytes=88,new_ret_count=2,existing_complete_comparisons=len(known),tags=len(tags),selected_cuts_bytes=sum(c['bytes'] for c in cuts),api_native_execution=0)))
