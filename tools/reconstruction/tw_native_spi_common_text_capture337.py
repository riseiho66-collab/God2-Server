"""Static bytes/hash/PE/Capstone and retained raw token review only."""
from pathlib import Path
import hashlib,json
import capstone,pefile
ROOT=Path(__file__).resolve().parent
PIN=ROOT.parent/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
P335=ROOT.parent/'tw-native-f4-list-definition-key-source-335'
P336=ROOT.parent/'tw-native-petroom-key-membership-source-336'
def sha(x):return hashlib.sha256(x).hexdigest()
def emit(name,value):
    (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
refs=[]
def load(path,expected=None):
    raw=path.read_bytes();h=sha(raw)
    if expected and h!=expected:raise ValueError(f'Source changed: {path}')
    refs.append(dict(path=str(path),bytes=len(raw),sha256=h))
    return raw
mapped=load(PIN/'native-image.bin','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
original=load(PIN/'originalPE.bin','5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde')
pe=pefile.PE(data=original,fast_load=True)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
out=ROOT/'native';out.mkdir(exist_ok=True)
cuts=[]
def cut(name,start,end,kind,entry=None):
    raw=mapped[start-0x400000:end-0x400000];off=pe.get_offset_from_rva(start-0x400000)
    if raw!=original[off:off+len(raw)] or len(raw)!=end-start:raise ValueError('PE mismatch')
    (out/(name+'.bin')).write_bytes(raw)
    record=dict(name=name,kind=kind,span_start_va=f'{start:08X}',end_exclusive_va=f'{end:08X}',
                bytes=len(raw),sha256=sha(raw),original_pe_offset=off,pe_equal=True)
    if kind!='data':
        instructions=list(md.disasm(raw,start))
        if sum(i.size for i in instructions)!=len(raw):raise ValueError('Incomplete instruction span')
        (out/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+'\n'.join(
            f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}' for i in instructions)+'\n',encoding='utf-8',newline='\n')
        record.update(actual_entry_va=f'{(entry or start):08X}',
            returns=[f'{i.address:08X}' for i in instructions if i.mnemonic.startswith('ret')],
            direct_calls=[dict(va=f'{i.address:08X}',target=i.op_str) for i in instructions if i.mnemonic=='call'])
    cuts.append(record)
for name,start,end in [
    ('known-generic-parser-complete',0x459420,0x45995F),
    ('known-field-string-copy-complete',0x451AE0,0x451B2C),
    ('known-field-string-pointer-complete',0x451B60,0x451B98),
    ('known-token-capacity-complete',0x451920,0x451958),
    ('known-row-reader-complete',0x451A90,0x451AD8),
    ('known-tokenizer-complete',0x451BE0,0x451CD2),
    ('known-token-copy-leaf-complete',0x547B80,0x547C7E),
    ('numeric-wrapper-complete-open-child',0x5480B4,0x5480E8),
]:cut(name,start,end,'complete-method')
# True direct-call entry5489A0, with backwards branch to its needed return stub.
# Do not call548990 an entry or start a new fn at the interior backwards target.
cut('known-byte-find-complete-with-cold-return',0x548990,0x548A5C,
    'complete-method-with-pre-entry-return-stub',entry=0x5489A0)
for name,start,end in [('join-separator-LF',0x584BB0,0x584BB2),
                       ('empty-string-precondition',0x5B4640,0x5B4641),
                       ('numeric-format-open-child',0x5823B4,0x5823B7)]:cut(name,start,end,'data')
load(P335/'seal.json','c44c9c7c97f7f889600303fcb2758177bdfed74fc5f10f91f4c298dc89bd17af')
seal=json.loads(load(P336/'seal.json','488b2275fba2abbf913ed21f4868ae675ddb10ac711d5f0d13a6e3555f02c9c9'))
rows_pin=next(x['sha256'] for x in seal['members'] if x['path']=='rows.json')
rows=json.loads(load(P336/'rows.json',rows_pin))
checks=[]
for r in rows:
    fields=[bytes.fromhex(x) for x in r['raw_fields_hex']]
    if len(fields)!=26 or sha(b','.join(fields))!=r['source_record_sha256']:
        raise ValueError('Exact row token provenance differs')
    bad=[dict(field=i,byte=f'{b:02X}') for i,f in enumerate(fields) for b in [0,10,13,44] if b in f]
    if bad:raise ValueError('Selected finite source violates text-only delimiter scope')
    nonempty=[i for i in range(8,13) if fields[i]]
    join=b'\n'.join(fields[i] for i in nonempty)
    if len(fields[4])>37 or len(fields[7])>37 or len(join)>189 or max(map(len,fields))>255:
        raise ValueError('Selected finite input exceeds native text buffers')
    checks.append(dict(key=r['native_key'],row_sha256=r['source_record_sha256'],field_count=len(fields),
        field_lengths=[len(f) for f in fields],field4_name_bytes=len(fields[4]),field7_caption_bytes=len(fields[7]),
        nonempty_description_fields=nonempty,joined_description_bytes=len(join),
        meaningful_name_hex=fields[4].hex(),meaningful_caption_hex=fields[7].hex(),
        structural_nonempty_LF_join_hex=join.hex(),
        forbidden_octets=[],checks_are_static_source_only=True))
emit('selected22-text-bounds.json',checks)
emit('native/cuts.json',cuts)
emit('accounting.json',dict(cuts=len(cuts),complete_methods=9,
    code_bytes=sum(x['bytes'] for x in cuts if x['kind']!='data'),
    data_bytes=sum(x['bytes'] for x in cuts if x['kind']=='data'),
    selected_rows=len(checks),max_field_bytes=max(max(x['field_lengths']) for x in checks),
    max_name_bytes=max(x['field4_name_bytes'] for x in checks),max_caption_bytes=max(x['field7_caption_bytes'] for x in checks),
    min_join_bytes=min(x['joined_description_bytes'] for x in checks),max_join_bytes=max(x['joined_description_bytes'] for x in checks),
    full396_generated=0,native_methods_newly_credited=0,complete_routes_increment=0,
    capstone_version=capstone.__version__,pefile_version=pefile.__version__))
for path in [P335/'native/field-number-convert-complete.bin',P335/'native/row-loader-complete.bin',
             ROOT.parent/'tw-native-e5-egg-input-source-328/native/known-egg-open-complete.bin',
             P335/'native/known-list-population-complete.bin',
             Path('C:/Users/risei/Desktop/God2/God2-Server/tools/strike_lab/recover_companion_growth.py')]:load(path)
emit('source-references.json',refs)
print(json.dumps(json.loads((ROOT/'accounting.json').read_bytes())))
