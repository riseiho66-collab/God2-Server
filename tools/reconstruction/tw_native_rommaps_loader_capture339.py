from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_GRP_JUMP,CS_GRP_CALL,CS_GRP_RET

OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-rommaps-loader-source-339')
BASE=OUT.parent;PIN=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
sha=lambda b:hashlib.sha256(b).hexdigest()
refs=[]
def reference(path,scope):
    raw=path.read_bytes();refs.append(dict(path=str(path),bytes=len(raw),sha256=sha(raw),scope=scope,copied=False));return raw
def put(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf8',newline='\n')
image=reference(PIN/'native-image.bin','Pinned149c mapped image hashed in place, not copied')
original=reference(PIN/'originalPE.bin','Pinned5fc originalPE hashed in place, not copied')
assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
native=OUT/'native';native.mkdir(exist_ok=True)
cuts=[]
for name,start,end,kind in [('rommaps-loader-complete',0x459ef0,0x459fb7,'new-complete-method'),('rommaps-range-lookup-complete',0x459fc0,0x459ff7,'complete-selected-consumer'),('known-dispatch-header-count-category-prefix',0x45618b,0x4561dc,'known-selected-parent-span'),('known-dispatch-rommaps-selected-branch',0x456227,0x456272,'known-selected-parent-span'),('known-generic-parser-resource-tail',0x459933,0x45995f,'known-selected-parent-span')]:
    raw=image[start-0x400000:end-0x400000];off=pe.get_offset_from_rva(start-0x400000)
    assert raw==original[off:off+len(raw)]
    ins=list(md.disasm(raw,start));assert sum(i.size for i in ins)==len(raw)
    calls=[dict(va=f'{i.address:08X}',target=i.op_str) for i in ins if i.group(CS_GRP_CALL)]
    branches=[dict(va=f'{i.address:08X}',mnemonic=i.mnemonic,target=i.op_str) for i in ins if i.group(CS_GRP_JUMP)]
    returns=[dict(va=f'{i.address:08X}',operands=i.op_str) for i in ins if i.group(CS_GRP_RET)]
    if kind in ('new-complete-method','complete-selected-consumer'):
        assert len(returns)==1 and ins[-1].group(CS_GRP_RET)
        assert all(start<=int(branch['target'],16)<end for branch in branches)
    (native/(name+'.bin')).write_bytes(raw)
    tsv='va\tbytes\tmnemonic\toperands\n'+'\n'.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}' for i in ins)+'\n'
    (native/(name+'.tsv')).write_text(tsv,encoding='utf8',newline='\n')
    cuts.append(dict(name=name,kind=kind,start_va=f'{start:08X}',end_exclusive_va=f'{end:08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,mapped_equal=True,original_pe_equal=True,returns=returns,direct_calls=calls,branches=branches))
name='rommaps-dispatch-literal';start=0x58a13c;raw=image[start-0x400000:start-0x400000+8];off=pe.get_offset_from_rva(start-0x400000)
assert raw==b'RomMaps\0'==original[off:off+8]
(native/(name+'.bin')).write_bytes(raw)
cuts.append(dict(name=name,kind='data',start_va=f'{start:08X}',end_exclusive_va=f'{start+8:08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,mapped_equal=True,original_pe_equal=True))
put('cuts.json',cuts)
OLD=BASE/'tw-native-f4-list-definition-key-source-335/native'
OLD337=BASE/'tw-native-spi-selector0-projection-source-337/native'
comparisons=[]
for p,start in [(OLD/'section-dispatch-complete.bin',0x456130),(OLD/'generic-record-parser-complete.bin',0x459420),(OLD/'row-loader-complete.bin',0x4599b0),(OLD/'category-loader-complete.bin',0x459150),(OLD/'category-lookup-complete.bin',0x459380),(OLD/'field-number-output-complete.bin',0x451b30),(OLD/'field-number-complete.bin',0x451b50),(OLD/'field-number-convert-complete.bin',0x451ba0),(OLD/'field-string-copy-complete.bin',0x451ae0),(OLD337/'known-row-reader-complete.bin',0x451a90),(OLD337/'known-tokenizer-complete.bin',0x451be0),(OLD337/'known-token-capacity-complete.bin',0x451920)]:
    raw=reference(p,'Existing selected complete source referenced and independently compared; no recovery recredit')
    off=pe.get_offset_from_rva(start-0x400000)
    assert raw==image[start-0x400000:start-0x400000+len(raw)]==original[off:off+len(raw)]
    comparisons.append(dict(path=str(p),start_va=f'{start:08X}',end_exclusive_va=f'{start+len(raw):08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,mapped_equal=True,original_pe_equal=True))
put('known-source-comparisons.json',comparisons)
PRIOR=BASE/'round338-spi-rommaps-retained-source-audit'
for name in ['seal.json','source-window-facts.json','rommaps57-source-line-cuts.json','spi22-new-historical-source-offsets.json','references.json']:
    reference(PRIOR/name,'Immutable338 historical raw-source provenance in place; unchanged')
source_path=BASE/'tw-native-resource-custody-and-remote-opaque-314/source-entry/inputs/exact-restored/gamedata.csvZ.decoded'
source=reference(source_path,'Historical75c3 original input in place; no full copy and no parser execution')
assert sha(source)=='75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815'
lines=source.splitlines(keepends=True)
assert lines[9]==b'ItemType,46\r\n'
tags=[]
for i in range(10,56):
    fields=lines[i][:-2].split(b',');tags.append(fields[2])
assert len(tags)==46 and b'RomMaps' not in tags and tags[9]==b'SPI'
put('historical-itemtype-source-tags.json',dict(header_source_line=10,header_raw_hex=lines[9].hex(),rows=[dict(source_record_ordinal=i,source_line=i+11,token2_raw_hex=tag.hex(),token2_ascii=tag.decode('ascii')) for i,tag in enumerate(tags)],has_rommaps_literal=False,spi_ordinal=9,scope='Original source text only; no category bank population execution'))
rows=json.loads((PRIOR/'rommaps57-source-line-cuts.json').read_bytes())
assert len(rows)==57 and all(row['source_token0_ascii']==str(i) for i,row in enumerate(rows))
put('historical-source-qualification.json',dict(source_sha256=sha(source),rommaps_source_rows=57,source_token0_sequence='0..56',maximum_source_path_token3_bytes=max(len(bytes.fromhex(row['raw_body_fields_hex'][3])) for row in rows),source_extra_token4_preserved_but_unread_by_loader=True,header_count_ascii='57',numeric_converter_executed=False,numeric_native_outputs_created=False,current_ef297_equivalence=False,current_bank_observed=False,scope='Physical source order and literal fields only; exact original source lines and offsets retained in338'))
put('references.json',refs)
print(json.dumps(dict(complete_loader_bytes=199,complete_consumer_bytes=55,all_loader_returns=[x['returns'] for x in cuts if x['name']=='rommaps-loader-complete'],retained_selected_cuts=sum(x['bytes'] for x in cuts),existing_complete_cut_comparisons=len(comparisons),native_execution=0)))
