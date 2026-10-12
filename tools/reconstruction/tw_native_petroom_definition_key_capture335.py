"""Read-only static PE/Capstone source capture; no target execution or resource decoding."""
from pathlib import Path
import hashlib, json, struct
import capstone, pefile

ROOT = Path(__file__).resolve().parent
PIN = ROOT.parent / 'tw-native-entry-body-alias-and-remote-opaque-315' / 'native-entry'
INPUTS = [('native-image.bin','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'),
          ('originalPE.bin','5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde')]
def sha(data): return hashlib.sha256(data).hexdigest()
def emit(path, value):
    (ROOT/path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
buffers, refs = [], []
for name, expected in INPUTS:
    path = PIN/name
    data = path.read_bytes()
    if sha(data) != expected: raise ValueError('Pinned source changed')
    buffers.append(data)
    refs.append(dict(path=str(path),bytes=len(data),sha256=expected))
mapped, original = buffers
pe = pefile.PE(data=original, fast_load=True)
if pe.OPTIONAL_HEADER.ImageBase != 0x400000: raise ValueError('Unexpected base')
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
out = ROOT/'native'; out.mkdir(exist_ok=True)
cuts=[]
def read(va, size):
    rva=va-0x400000
    a=mapped[rva:rva+size]
    off=pe.get_offset_from_rva(rva)
    b=original[off:off+size]
    if len(a)!=size or a!=b: raise ValueError(f'PE mismatch {va:x}')
    return a,off
def cut(name,start,end,kind):
    raw,off=read(start,end-start)
    (out/(name+'.bin')).write_bytes(raw)
    rec=dict(name=name,kind=kind,start_va=f'{start:08X}',end_exclusive_va=f'{end:08X}',
             bytes=len(raw),sha256=sha(raw),original_pe_offset=off,pe_equal=True)
    if kind in ('complete-method','known-instruction-span'):
        instructions=list(md.disasm(raw,start))
        if sum(i.size for i in instructions)!=len(raw): raise ValueError('Incomplete disassembly')
        rows=['va\tbytes\tmnemonic\toperands']+[f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}' for i in instructions]
        (out/(name+'.tsv')).write_text('\n'.join(rows)+'\n',encoding='utf-8',newline='\n')
        rec['returns']=[f'{i.address:08X}' for i in instructions if i.mnemonic.startswith('ret')]
        rec['direct_calls']=[dict(va=f'{i.address:08X}',target=i.op_str) for i in instructions if i.mnemonic=='call']
    cuts.append(rec)
    return raw

# Actual entries, all returns. Historical row-slice RVAs 591C0 and 59A20
# are interior addresses of the enclosing complete methods, not new functions.
for name,start,end in [
    ('lookup-complete',0x459A60,0x459A7E),
    ('row-loader-complete',0x4599B0,0x459A5F),
    ('generic-record-parser-complete',0x459420,0x45995F),
    ('category-loader-complete',0x459150,0x45937D),
    ('category-lookup-complete',0x459380,0x45941B),
    ('section-dispatch-complete',0x456130,0x4570D6),
    ('field-string-copy-complete',0x451AE0,0x451B2C),
    ('field-number-output-complete',0x451B30,0x451B43),
    ('field-number-complete',0x451B50,0x451B5D),
    ('field-string-pointer-complete',0x451B60,0x451B98),
    ('field-number-convert-complete',0x451BA0,0x451BDC),
    ('known-list-population-complete',0x4DC710,0x4DC82D),
]: cut(name,start,end,'complete-method')
caseptrs=cut('generic-parser-case-pointers',0x459960,0x459984,'data')
indices=cut('generic-parser-case-index',0x459984,0x4599A7,'data')
tags=cut('category-tag-pointers',0x5897EC,0x58987C,'data')
cut('number-format-string',0x5823B4,0x5823B7,'data')
cut('itemtype-dispatch-name',0x58A144,0x58A14D,'data')
cut('known-primary-catalog-binding-span',0x4817C0,0x481811,'known-instruction-span')
cut('known-full20-key-lookup-span',0x4D5472,0x4D54B3,'known-instruction-span')
tagrows=[]
for index,ptr in enumerate(struct.unpack('<36I',tags)):
    rva=ptr-0x400000; end=mapped.index(0,rva)+1
    raw,off=read(ptr,end-rva)
    tagrows.append(dict(index=index,va=f'{ptr:08X}',raw_hex=raw.hex(),sha256=sha(raw),
                        bytes=len(raw),original_pe_offset=off,pe_equal=True))
emit('native/category-tag-strings.json',tagrows)
targets=struct.unpack('<9I',caseptrs)
rows=['selector_low8\tindex\ttarget_va']
for selector,index in enumerate(indices,1): rows.append(f'{selector}\t{index}\t{targets[index]:08X}')
(out/'generic-parser-selector-table.tsv').write_text('\n'.join(rows)+'\n',encoding='utf-8',newline='\n')
emit('input-references.json',refs)
emit('native/cuts.json',cuts)
emit('capture-accounting.json',dict(cut_count=len(cuts),method_count=sum(x['kind']=='complete-method' for x in cuts),
    complete_method_code_bytes=sum(x['bytes'] for x in cuts if x['kind']=='complete-method'),
    known_instruction_span_bytes=sum(x['bytes'] for x in cuts if x['kind']=='known-instruction-span'),
    code_bytes=sum(x['bytes'] for x in cuts if x['kind']!='data'),
    contiguous_data_bytes=sum(x['bytes'] for x in cuts if x['kind']=='data'),
    tag_string_extract_count=len(tagrows),tag_string_bytes=sum(x['bytes'] for x in tagrows),
    capstone_version=capstone.__version__,pefile_version=pefile.__version__,
    limits='Static source only. No resource decode, execution, runtime, emulator, codec, DB, build or tests.'))
print(json.dumps(json.loads((ROOT/'capture-accounting.json').read_text()),ensure_ascii=False))
