"""Bounded static file/hash/PE/Capstone review; never execute target or parser."""
from pathlib import Path
import hashlib,json
import capstone,pefile
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
PIN=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
P337=BASE/'tw-native-spi-selector0-projection-source-337'
REVIEW=BASE/'round337-spi-numeric-conversion-review'
P336=BASE/'tw-native-petroom-key-membership-source-336'
def sha(b):return hashlib.sha256(b).hexdigest()
def emit(p,obj):
    (ROOT/p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
refs=[]
def load(p,expected=None):
    b=p.read_bytes(); h=sha(b)
    if expected and h!=expected:raise ValueError('Pinned input changed: '+str(p))
    refs.append(dict(path=str(p),bytes=len(b),sha256=h))
    return b
mapped=load(PIN/'native-image.bin','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
original=load(PIN/'originalPE.bin','5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde')
pe=pefile.PE(data=original,fast_load=True)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
out=ROOT/'native';out.mkdir(exist_ok=True)
cuts=[]
for name,a,z in [
    ('byte-string-length-complete',0x550140,0x5501BB),
    ('stream-byte-read-complete',0x550CD9,0x550CF3),
    ('eof-aware-pushback-complete',0x550CF3,0x550D0A),
    ('skip-whitespace-input-complete',0x550D0A,0x550D2E),
    ('stream-refill-complete-selected-string-EOF',0x54EAE3,0x54EBBF),
]:
    b=mapped[a-0x400000:z-0x400000];off=pe.get_offset_from_rva(a-0x400000)
    if b!=original[off:off+len(b)]:raise ValueError('PE mapping differs')
    ins=list(md.disasm(b,a))
    if sum(i.size for i in ins)!=len(b):raise ValueError('Incomplete instruction cut')
    (out/(name+'.bin')).write_bytes(b)
    (out/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+''.join(
        f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins),encoding='utf-8',newline='\n')
    cuts.append(dict(name=name,actual_entry_va=f'{a:08X}',end_exclusive_va=f'{z:08X}',
        bytes=len(b),sha256=sha(b),original_pe_offset=off,pe_equal=True,
        returns=[f'{i.address:08X}' for i in ins if i.mnemonic.startswith('ret')],
        direct_calls=[dict(va=f'{i.address:08X}',target=i.op_str) for i in ins if i.mnemonic=='call']))
load(P337/'seal.json','802e0b2d22e16e5423c5882eac2325e45a35d67ef564d3d6327c3d38ce89ed9b')
load(P337/'native/numeric-wrapper-complete-open-child.bin','ca5a1a6f6ef9b06d88f074bd83b37f016d70706bc21addcc4da137fd3c76cea0')
load(REVIEW/'seal.json')
scanner_path=REVIEW/'native/scanner-direct-body-retained.tsv'
scanner=load(scanner_path).decode('utf-8')
rows=scanner.splitlines()[1:]
selected=[]
for line in rows:
    va,raw,mn,operands=line.split('\t');a=int(va,16); b=bytes.fromhex(raw)
    off=pe.get_offset_from_rva(a-0x400000)
    if b!=mapped[a-0x400000:a-0x400000+len(b)] or b!=original[off:off+len(b)]:
        raise ValueError('Prior scanner instruction provenance differs')
    if (0x55027D<=a<0x550310 or 0x5503FE<=a<0x550467 or
        0x550AE8<=a<0x550BEF or 0x550C31<=a<0x550CA2):selected.append(line)
(ROOT/'scanner-selected-instruction-review.tsv').write_text(
    'va\tbytes\tmnemonic\toperands\n'+'\n'.join(selected)+'\n',encoding='utf-8',newline='\n')
seal=json.loads(load(P336/'seal.json','488b2275fba2abbf913ed21f4868ae675ddb10ac711d5f0d13a6e3555f02c9c9'))
row_sha=next(m['sha256'] for m in seal['members'] if m['path']=='rows.json')
records=json.loads(load(P336/'rows.json',row_sha))
positions=[0,3,5,6,*range(13,26)]
lex=[]
for r in records:
    f=[bytes.fromhex(x) for x in r['raw_fields_hex']]
    if len(f)!=26 or sha(b','.join(f))!=r['source_record_sha256']:raise ValueError('Row pin differs')
    tokens=[]
    for i in positions:
        token=f[i]
        if not token or any(c<0x30 or c>0x39 for c in token):raise ValueError('Not finite ASCII digits')
        tokens.append(dict(position=i,raw_hex=token.hex(),byte_length=len(token),
                           all_unsigned_ASCII_digits=True,contains_sign_or_whitespace=False))
    lex.append(dict(key=r['native_key'],source_record_sha256=r['source_record_sha256'],tokens=tokens))
emit('selected22-ascii-input-shapes.json',lex)
raw_review=[]
for a,h,meaning in [
    (0x5480BD,'c745ec49000000','DWORD descriptor+0C literal49h'),
    (0x5480C5,'8945e8','DWORD descriptor+08 input pointer'),
    (0x5480C8,'8945e0','DWORD descriptor+00 input pointer'),
    (0x5480D0,'8945e4','DWORD descriptor+04 byte length'),
    (0x550CDD,'ff4a04','DEC DWORD descriptor+04'),
    (0x550CE0,'7809','signed negative branch to550CEB'),
    (0x550CE4,'0fb601','MOVZX BYTE input toDWORD EAX'),
    (0x54EAEB,'a883','TEST AL flags83h'),
    (0x54EAF3,'a840','TEST AL flags40h'),
    (0x54EAF5,'0f85bf000000','JNE54EBBA whenstringbit40set'),
    (0x54EBBA,'83c8ff','OR EAX FFFFFFFFh EOF'),
    (0x550CF3,'837c2404ff','CMP DWORD formalarg1,-1'),
    (0x550CF8,'740f','JE550D09 return withoutpushback'),
    (0x550D14,'ff06','INC DWORD scanner readcount'),
    (0x550D27,'75e7','JNE550D10 whenpredicate nonzero'),
]:
    b=bytes.fromhex(h);off=pe.get_offset_from_rva(a-0x400000)
    if mapped[a-0x400000:a-0x400000+len(b)]!=b or original[off:off+len(b)]!=b:
        raise ValueError('Independent raw instruction review differs')
    raw_review.append(dict(va=f'{a:08X}',raw_hex=h,meaning=meaning,pe_equal=True))
emit('raw-instruction-review.json',raw_review)
emit('native/cuts.json',cuts)
emit('source-references.json',refs)
emit('accounting.json',dict(complete_input_methods=len(cuts),code_bytes=sum(c['bytes'] for c in cuts),
    data_bytes=0,prior_scanner_instructions_byte_checked=len(rows),selected_rows=len(lex),
    selected_numeric_token_positions=positions,selected_token_count=sum(len(r['tokens']) for r in lex),
    max_selected_token_bytes=max(t['byte_length'] for r in lex for t in r['tokens']),
    target_execution=False,parser_execution=False,numeric_projection_generated=False,
    complete_routes_increment=0,capstone_version=capstone.__version__,pefile_version=pefile.__version__))
print((ROOT/'accounting.json').read_text())
