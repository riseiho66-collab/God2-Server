"""Static PE/hash/Capstone line reader only; no file decoder or target execution."""
from pathlib import Path
import hashlib,json
import capstone,pefile
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
PIN=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
def sha(b):return hashlib.sha256(b).hexdigest()
def emit(p,obj):
    (ROOT/p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
refs=[]
def load(p,h=None):
    b=p.read_bytes();actual=sha(b)
    if h and actual!=h:raise ValueError('Source changed: '+str(p))
    refs.append(dict(path=str(p),bytes=len(b),sha256=actual))
    return b
mapped=load(PIN/'native-image.bin','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
original=load(PIN/'originalPE.bin','5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde')
pe=pefile.PE(data=original,fast_load=True)
pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_IMPORT']])
imports=[dict(iat_va=f'{i.address:08X}',dll=e.dll.decode('ascii'),name=i.name.decode('ascii') if i.name else None)
    for e in getattr(pe,'DIRECTORY_ENTRY_IMPORT',[]) for i in e.imports
    if i.address in [0x5701D8,0x57045C,0x570404,0x570324,0x570418]]
emit('import-references.json',imports)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
out=ROOT/'native';out.mkdir(exist_ok=True)
cuts=[]
def cut(name,a,z,data=False):
    b=mapped[a-0x400000:z-0x400000];off=pe.get_offset_from_rva(a-0x400000)
    if b!=original[off:off+len(b)]:raise ValueError('Original PE mismatch')
    (out/(name+'.bin')).write_bytes(b)
    r=dict(name=name,kind='data' if data else 'complete-method',start_va=f'{a:08X}',
        end_exclusive_va=f'{z:08X}',bytes=len(b),sha256=sha(b),original_pe_offset=off,pe_equal=True)
    if not data:
        ins=list(md.disasm(b,a))
        if sum(i.size for i in ins)!=len(b):raise ValueError('Incomplete instruction boundary')
        (out/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+''.join(
            f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins),encoding='utf-8',newline='\n')
        r.update(actual_entry_va=f'{a:08X}',returns=[f'{i.address:08X}' for i in ins if i.mnemonic.startswith('ret')],
            direct_calls=[dict(va=f'{i.address:08X}',target=i.op_str) for i in ins if i.mnemonic=='call'])
    cuts.append(r)
for name,a,z in [
    ('reader-open-method-complete',0x451960,0x45199E),
    ('known-resource-text-opener-complete',0x402530,0x40266F),
    ('CRT-open-share-wrapper-complete',0x54716F,0x547182),
    ('CRT-open-stream-wrapper-complete',0x54713E,0x54716F),
    ('CRT-open-mode-parser-complete',0x54E343,0x54E4B3),
    ('CRT-descriptor-open-complete',0x552D19,0x552FE8),
    ('line-read-method-complete',0x547A95,0x547AF7),
    ('descriptor-read-wrapper-complete',0x54EEA7,0x54EF0C),
    ('descriptor-text-read-complete',0x54EF0C,0x54F0E5),
]:cut(name,a,z)
for name,a,z in [('mode-binary-read',0x582350,0x582353),('mode-text-read',0x582378,0x58237B),
                  ('suffix-Z',0x58236C,0x58236E)]:cut(name,a,z,True)
for p,h in [
    (BASE/'tw-native-spi-selector0-projection-source-337/seal.json','802e0b2d22e16e5423c5882eac2325e45a35d67ef564d3d6327c3d38ce89ed9b'),
    (BASE/'tw-native-spi-numeric-input-source-338/seal.json','fffa554ba06a9282c2334a7807d5b3a3cfa1ced42a7d24acbd7ef65e39e8b612'),
    (BASE/'tw-native-petroom-key-membership-source-336/seal.json','488b2275fba2abbf913ed21f4868ae675ddb10ac711d5f0d13a6e3555f02c9c9'),
    (BASE/'tw-native-spi-selector0-projection-source-337/native/known-row-reader-complete.bin','02fe24e347bf39d7dc314d2f52fb30d06a8df93ef3108db49b9425e54bfecd94'),
    (BASE/'tw-native-spi-numeric-input-source-338/native/stream-refill-complete-selected-string-EOF.bin','0b6453622e07698e6d43237ce55a4f6d8e3a3f38c853370cc973b7468d059756'),
    (BASE/'tw-native-f4-list-definition-key-source-335/native/section-dispatch-complete.tsv',None),
    (BASE/'tw-native-f4-list-definition-key-source-335/native/row-loader-complete.tsv',None),
    (Path('C:/Users/risei/Desktop/God2/God2-Server/docs/research/tw-native-resource-selection-source-20261008.md'),None),
]:load(p,h)
records=json.loads(load(BASE/'tw-native-petroom-key-membership-source-336/rows.json',
    '15adb695085dbf712f6ecb011cf3714ca9031aa40f00f98ac4bb39492f33479c'))
shapes=[]
for r in records:
    fields=[bytes.fromhex(x) for x in r['raw_fields_hex']];body=b','.join(fields)
    if sha(body)!=r['source_record_sha256']:raise ValueError('Normalized row differs')
    if 0x1A in body:raise ValueError('Selected body contains text-mode EOF1A')
    shapes.append(dict(key=r['native_key'],source_record_sha256=sha(body),normalized_body_bytes=len(body),
        final_field_hex=fields[25].hex(),hypothetical_CRLF_line_bytes=len(body)+2,
        contains_text_EOF_1A=False,
        scope='normalized retained row; CRLF input premise from retained336 original-source provenance'))
emit('selected22-line-shapes.json',shapes)
raw=[]
for a,h,meaning in [
    (0x54E362,'3c72','mode initial BYTE r'),(0x54E42C,'80cd40','mode lowercase t: OR CH40h'),
    (0x552D53,'f6c540','TEST open flags CH40h'),(0x552D60,'804dff80','OR local descriptor flags80h'),
    (0x552F43,'884c3004','store BYTE fd record+4'),(0x54EFD9,'a880','TEST fd flags AL80h'),
    (0x54F015,'3c0d','CMP inputBYTE CR'),(0x54F02E,'80380a','CMP next inputBYTE LF'),
    (0x54F033,'83451002','advance inputcursor by2'),(0x54F097,'c6030a','store BYTE LF'),
    (0x547AD4,'8807','copy input BYTE to line buffer'),(0x547AD7,'3c0a','stop after LF'),
]:
    b=bytes.fromhex(h);off=pe.get_offset_from_rva(a-0x400000)
    if mapped[a-0x400000:a-0x400000+len(b)]!=b or original[off:off+len(b)]!=b:raise ValueError('Raw proof differs')
    raw.append(dict(va=f'{a:08X}',raw_hex=h,meaning=meaning,pe_equal=True))
emit('raw-instruction-review.json',raw)
emit('native/cuts.json',cuts)
emit('source-references.json',refs)
emit('accounting.json',dict(complete_cuts=sum(c['kind']!='data' for c in cuts),
    code_bytes=sum(c['bytes'] for c in cuts if c['kind']!='data'),data_bytes=sum(c['bytes'] for c in cuts if c['kind']=='data'),
    selected_rows=len(shapes),max_normalized_line_bytes=max(s['normalized_body_bytes'] for s in shapes),
    complete_routes_increment=0,target_execution=False,resource_decoding=False,
    capstone_version=capstone.__version__,pefile_version=pefile.__version__))
print((ROOT/'accounting.json').read_text())
