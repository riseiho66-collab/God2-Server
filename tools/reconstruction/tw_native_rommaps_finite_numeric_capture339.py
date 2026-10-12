"""Static retained-byte arithmetic audit, never native/CRT/parser/codec execution."""
from pathlib import Path
import hashlib,json,struct
import pefile
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
RAW=BASE/'round338-spi-rommaps-retained-source-audit'
L339=BASE/'tw-native-rommaps-loader-source-339'
R339=BASE/'tw-native-spi-line-reader-source-339'
I338=BASE/'tw-native-spi-numeric-input-source-338'
C338=BASE/'tw-native-spi-numeric-classification-source-338'
P335=BASE/'tw-native-f4-list-definition-key-source-335'
PIN=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
def sha(b):return hashlib.sha256(b).hexdigest()
def emit(p,obj):
    (ROOT/p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
refs=[]
def load(p,h=None):
    b=p.read_bytes();actual=sha(b)
    if h and actual!=h:raise ValueError('Pinned source changed: '+str(p))
    refs.append(dict(path=str(p),bytes=len(b),sha256=actual))
    return b
seals=[]
def verify_seal(p,h):
    s=json.loads(load(p/'seal.json',h));members=s['members']
    for m in members:
        b=(p/m['path']).read_bytes()
        if len(b)!=m['bytes'] or sha(b)!=m['sha256']:raise ValueError('Seal member mismatch')
    total=sum(m['bytes'] for m in members)
    expected=s.get('member_bytes',s.get('retained_member_bytes',s.get('total_member_bytes')))
    if len(members)!=s['member_count'] or total!=expected:raise ValueError('Seal accounting mismatch')
    seals.append(dict(path=str(p),seal_sha256=h,member_count=len(members),member_bytes=total,all_members_equal=True))
verify_seal(RAW,'c73d42c66cbd6a8c401ae9819f8a3a21e35d0201abaeebd0211bbafb8b42bb0c')
verify_seal(L339,'1470774f340aa52781d709e34783006c5c7a96a33b983dd29160b65f5899c1e4')
verify_seal(R339,'ce9cb9b12a25519df6d5849833345799f516a5d788f82ba544ac71e31de775f9')
verify_seal(I338,'fffa554ba06a9282c2334a7807d5b3a3cfa1ced42a7d24acbd7ef65e39e8b612')
verify_seal(C338,'4822460aa146325aebd58050cc86a9f85ff98cf1f5d12ff8d985abb29e365658')
decoded_path=BASE/'tw-native-resource-custody-and-remote-opaque-314/source-entry/inputs/exact-restored/gamedata.csvZ.decoded'
decoded=load(decoded_path,'75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815')
mapped=load(PIN/'native-image.bin','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
original=load(PIN/'originalPE.bin','5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde')
pe=pefile.PE(data=original,fast_load=True)
instruction_reviews=[]
for pkg in [L339,R339]:
    for p in sorted((pkg/'native').glob('*.tsv')):
        lines=load(p).decode('utf-8').splitlines()[1:];count=0;size=0
        for line in lines:
            parts=line.split('\t');a=int(parts[0],16);b=bytes.fromhex(parts[1]);off=pe.get_offset_from_rva(a-0x400000)
            if b!=mapped[a-0x400000:a-0x400000+len(b)] or b!=original[off:off+len(b)]:raise ValueError('Instruction differs')
            count+=1;size+=len(b)
        instruction_reviews.append(dict(path=str(p),instructions=count,reviewed_bytes=size,both_images_equal=True))
for name in ['field-number-output-complete.tsv','field-number-complete.tsv','field-number-convert-complete.tsv']:
    p=P335/'native'/name;lines=load(p).decode('utf-8').splitlines()[1:]
    for line in lines:
        va,raw,*_=line.split('\t');a=int(va,16);b=bytes.fromhex(raw);off=pe.get_offset_from_rva(a-0x400000)
        if b!=mapped[a-0x400000:a-0x400000+len(b)] or b!=original[off:off+len(b)]:raise ValueError('Helper bytes differ')
    instruction_reviews.append(dict(path=str(p),instructions=len(lines),both_images_equal=True))
facts=[]
def decimal_fact(kind,position,token,line,offset,body_sha,slot=None,key=None):
    if not 1<=len(token)<=5 or any(c<48 or c>57 for c in token):raise ValueError('Finite decimal shape differs')
    value=0
    for c in token:value=value*10+c-48
    if value>65535:raise ValueError('Finite unsigned WORD range exceeded')
    r=dict(kind=kind,token_position=position,raw_hex=token.hex(),raw_ascii=token.decode('ascii'),byte_length=len(token),
        mathematical_source_value=value,source_line=line,decoded_line_offset=offset,source_body_sha256=body_sha,
        nonempty_ASCII_digits=True,no_sign_or_whitespace=True,no_DWORD_overflow=True,within_unsigned_WORD=True)
    if slot is not None:r['source_slot']=slot
    if key is not None:r['source_key']=key
    facts.append(r);return r
window=json.loads(load(RAW/'source-window-facts.json'))
hline=bytes.fromhex(window['header_raw_cp950_hex']);ho=window['header_decoded_offset']
if decoded[ho:ho+len(hline)]!=hline or decoded[:ho].count(b'\n')+1!=57:raise ValueError('Header offset differs')
hbody=hline[:-2]
header=decimal_fact('RomMaps-header-count',1,hbody.split(b',')[1],57,ho,sha(hbody))
if header['mathematical_source_value']!=57:raise ValueError('Count differs')
records=json.loads(load(RAW/'rommaps57-source-line-cuts.json'))
ranges=[]
for r in records:
    line=bytes.fromhex(r['raw_line_cp950_hex']);off=r['decoded_offset'];body=line[:-2]
    if line[-2:]!=b'\r\n' or decoded[off:off+len(line)]!=line or sha(line)!=r['raw_line_sha256']:
        raise ValueError('Original RomMaps line differs')
    if decoded[:off].count(b'\n')+1!=r['source_line'] or sha(body)!=r['raw_body_sha256']:raise ValueError('RomMaps source position differs')
    f=body.split(b',')
    if [x.hex() for x in f]!=r['raw_body_fields_hex']:raise ValueError('Raw fields differ')
    if len(f)!=5 or len(f[3])+1>128 or any(c in body for c in [0,10,13,26]):
        raise ValueError('RomMaps exact field/path/line shape exceeds qualified native scope')
    slot=decimal_fact('RomMaps-row',0,f[0],r['source_line'],off,sha(body))['mathematical_source_value']
    low=decimal_fact('RomMaps-row',1,f[1],r['source_line'],off,sha(body),slot=slot)['mathematical_source_value']
    high=decimal_fact('RomMaps-row',2,f[2],r['source_line'],off,sha(body),slot=slot)['mathematical_source_value']
    if slot!=r['source_order_ordinal'] or low>high:raise ValueError('Slot sequence/range differs')
    ranges.append(dict(slot=slot,low_WORD=low,high_WORD=high,source_line=r['source_line'],decoded_offset=off,
        raw_line_sha256=sha(line),raw_body_sha256=sha(body),raw_tokens0_1_2_hex=[x.hex() for x in f[:3]],
        raw_source_path_token3_hex=f[3].hex(),path_token3_bytes=len(f[3]),path_with_NUL_fits128=True,
        raw_body_bytes=len(body),source_only=True))
if [r['slot'] for r in ranges]!=list(range(57)):raise ValueError('Not exact source slots0..56')
P336=BASE/'tw-native-petroom-key-membership-source-336'
spi=json.loads(load(P336/'rows.json','15adb695085dbf712f6ecb011cf3714ca9031aa40f00f98ac4bb39492f33479c'))
positions=json.loads(load(RAW/'spi22-new-historical-source-offsets.json'))['rows']
matches=[]
for r,pos in zip(spi,positions):
    if r['native_key']!=pos['native_key']:raise ValueError('SPI order differs')
    off=pos['newly_qualified_historical_decoded_offset'];line=decoded[off:off+pos['line_bytes']];body=line[:-2]
    f=body.split(b',')
    if line[-2:]!=b'\r\n' or sha(line)!=pos['line_sha256'] or sha(body)!=r['source_record_sha256']:
        raise ValueError('SPI raw source differs')
    if decoded[:off].count(b'\n')+1!=r['source_line'] or [x.hex() for x in f]!=r['raw_fields_hex']:
        raise ValueError('SPI position/field bytes differ')
    icon=decimal_fact('SPI22-icon',3,f[3],r['source_line'],off,sha(body),key=r['native_key'])['mathematical_source_value']
    applicable=[x for x in ranges if x['low_WORD']<=icon<=x['high_WORD']]
    first=applicable[0] if applicable else None
    matches.append(dict(key=r['native_key'],source_record_index=r['source_record_index'],source_line=r['source_line'],
        decoded_offset=off,raw_line_sha256=sha(line),raw_body_sha256=sha(body),icon_token3_hex=f[3].hex(),
        conditional_metadata_WORD114=icon,matching_ranges=applicable,
        conditional_first_match_slot=first['slot'] if first else None,
        conditional_metadata_WORD116=first['slot'] if first else 65535,
        no_match_sentinel_WORD='FFFF',observed_native_output=False,full396_generated=False))
if len(facts)!=194 or len(matches)!=22:raise ValueError('Composition token count differs')
overlaps=[dict(first_slot=a['slot'],second_slot=b['slot'],inclusive_low=max(a['low_WORD'],b['low_WORD']),
    inclusive_high=min(a['high_WORD'],b['high_WORD'])) for i,a in enumerate(ranges) for b in ranges[i+1:]
    if max(a['low_WORD'],b['low_WORD'])<=min(a['high_WORD'],b['high_WORD'])]
canonical=bytearray()
def atom(b):
    if not isinstance(b,bytes):b=str(b).encode('ascii')
    canonical.extend(struct.pack('<I',len(b)));canonical.extend(b)
atom('round339-conditional-finite-source-projection-v1');atom(sha(decoded))
for s in seals:atom(s['seal_sha256'])
for r in facts:
    for k in ['kind','token_position','source_line','decoded_line_offset','source_body_sha256','raw_hex']:
        atom(r[k])
for m in matches:atom(m['key']);atom(m['conditional_metadata_WORD116'])
(ROOT/'canonical-source-projection-fingerprint.bin').write_bytes(canonical)
emit('finite194-token-facts.json',facts)
emit('rommaps57-conditional-ranges.json',ranges)
emit('spi22-conditional-WORD116.json',matches)
emit('verified-prior-seals.json',seals)
emit('native-instruction-source-review.json',instruction_reviews)
emit('source-references.json',refs)
emit('accounting.json',dict(token_count=len(facts),header_tokens=1,rommaps_row_tokens=171,SPI_icon_tokens=22,
    min_actual=min(f['mathematical_source_value'] for f in facts),max_actual=max(f['mathematical_source_value'] for f in facts),
    max_token_bytes=max(f['byte_length'] for f in facts),count_signed_WORD_safe=True,
    allocation_84h_times57_bytes=0x84*57,all_ranges_low_le_high=True,overlaps=overlaps,
    max_RomMaps_path_token3_bytes=max(r['path_token3_bytes'] for r in ranges),
    max_RomMaps_raw_body_bytes=max(r['raw_body_bytes'] for r in ranges),
    matched_icons=len([m for m in matches if m['conditional_first_match_slot'] is not None]),
    unmatched_icons=len([m for m in matches if m['conditional_first_match_slot'] is None]),
    candidate_slot_counts={str(s):sum(m['conditional_metadata_WORD116']==s for m in matches) for s in sorted(set(m['conditional_metadata_WORD116'] for m in matches))},
    canonical_fingerprint_bytes=len(canonical),canonical_fingerprint_sha256=sha(canonical),
    native_execution=False,parser_execution=False,current_bank_observed=False,full396_generated=False,
    new_methods=0,new_opcode=0,complete_route_increment=0))
print((ROOT/'accounting.json').read_text())
