"""Conditional historical source-byte composition only; no target/parser execution."""
from pathlib import Path
import hashlib,json,struct
import pefile
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
def sha(b):return hashlib.sha256(b).hexdigest()
def emit(p,obj):
    (ROOT/p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
refs=[];verified=[]
def load(p,h=None):
    b=p.read_bytes();actual=sha(b)
    if h and actual!=h:raise ValueError('Pinned source changed: '+str(p))
    refs.append(dict(path=str(p),bytes=len(b),sha256=actual));return b
for name,h in [
    ('tw-native-f4-list-definition-key-source-335','c44c9c7c97f7f889600303fcb2758177bdfed74fc5f10f91f4c298dc89bd17af'),
    ('tw-native-petroom-key-membership-source-336','488b2275fba2abbf913ed21f4868ae675ddb10ac711d5f0d13a6e3555f02c9c9'),
    ('tw-native-spi-selector0-projection-source-337','802e0b2d22e16e5423c5882eac2325e45a35d67ef564d3d6327c3d38ce89ed9b'),
    ('tw-native-spi-numeric-input-source-338','fffa554ba06a9282c2334a7807d5b3a3cfa1ced42a7d24acbd7ef65e39e8b612'),
    ('tw-native-spi-numeric-classification-source-338','4822460aa146325aebd58050cc86a9f85ff98cf1f5d12ff8d985abb29e365658'),
    ('round338-spi-rommaps-retained-source-audit','c73d42c66cbd6a8c401ae9819f8a3a21e35d0201abaeebd0211bbafb8b42bb0c'),
    ('tw-native-rommaps-loader-source-339','1470774f340aa52781d709e34783006c5c7a96a33b983dd29160b65f5899c1e4'),
    ('tw-native-spi-line-reader-source-339','ce9cb9b12a25519df6d5849833345799f516a5d788f82ba544ac71e31de775f9'),
    ('round339-rommaps-finite-numeric-source-audit','c6828b7fe939c4b0d1e00a77b7153daf382a0f8298c378702c4b33cb9263e9b8'),
    ('tw-native-spi-generic-record-write-source-340','eea7b0a2c86f7cb32a75f869acd8503650299670ed45758d69f7069a3ebefa03'),
    ('tw-native-spi-allocation-zero-source-340','b68ef4dc5494bfe74e057ce0140fb0d955d8e462022cb831c4dc4af6188dcc4c'),
]:
    p=BASE/name;s=json.loads(load(p/'seal.json',h))
    for m in s['members']:
        b=(p/m['path']).read_bytes()
        if len(b)!=m['bytes'] or sha(b)!=m['sha256']:raise ValueError('Previous member differs')
    total=sum(m['bytes'] for m in s['members'])
    if len(s['members'])!=s['member_count'] or total!=s.get('member_bytes',s.get('retained_member_bytes',s.get('total_member_bytes'))):
        raise ValueError('Previous accounting differs')
    verified.append(dict(package=name,seal_sha256=h,member_count=len(s['members']),member_bytes=total,all_members_equal=True))
SOURCE=BASE/'tw-native-resource-custody-and-remote-opaque-314/source-entry/inputs/exact-restored/gamedata.csvZ.decoded'
raw=load(SOURCE,'75c3c37947a64b0917fbf8e546884d9bf893fe6a606d3e2b8f3b1857966b1815')
PIN=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
mapped=load(PIN/'native-image.bin','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
original=load(PIN/'originalPE.bin','5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde')
pe=pefile.PE(data=original,fast_load=True)
native=[]
for a,z,h,meaning in [
    (0x459420,0x45995F,'c44740ab39b972882d080ad4e8f65d86f03ca6d55f195e0df22def15b2b58ebf','known complete generic parser'),
    (0x54A550,0x54A5A8,'2af9ec6db955aa74b3de79ebe2752b3fa148e02935ac40304eb9ffc13ccf0d2c','complete selected zero fill'),
]:
    b=mapped[a-0x400000:z-0x400000];off=pe.get_offset_from_rva(a-0x400000)
    if sha(b)!=h or b!=original[off:off+len(b)]:raise ValueError('Native proof bytes differ')
    native.append(dict(start_va=f'{a:08X}',end_exclusive_va=f'{z:08X}',bytes=len(b),sha256=h,original_pe_offset=off,pe_equal=True,meaning=meaning))
for a,b in [(0x5B4640,b'\0'),(0x584BB0,b'\n\0')]:
    off=pe.get_offset_from_rva(a-0x400000)
    if mapped[a-0x400000:a-0x400000+len(b)]!=b or original[off:off+len(b)]!=b:raise ValueError('Literal differs')
def actual_line(offset,line):
    end=raw.find(b'\n',offset)+1;b=raw[offset:end]
    if end==0 or b[-2:]!=b'\r\n' or raw[:offset].count(b'\n')+1!=line:raise ValueError('Source line differs')
    return b
category=actual_line(1213,20);cat_fields=category[:-2].split(b',')
if cat_fields[2]!=b'SPI' or any(len(f)>37 for f in cat_fields[2:]):raise ValueError('SPI category input/bounds differ')
if actual_line(611197,8177)!=b'SPI,737\r\n' or actual_line(raw.find(b'ItemType,46\r\n'),10)!=b'ItemType,46\r\n':
    raise ValueError('Original bank counts differ')
category_facts=dict(original_category_count=46,category_stride=1602,SPI_category_ordinal=9,
    SPI_category_source_line=20,SPI_category_offset=1213,SPI_category_raw_line_hex=category.hex(),
    SPI_category_raw_line_sha256=sha(category),SPI_category_field_lengths=[len(f) for f in cat_fields],
    original_SPI_count=737,SPI_header_source_line=8177,SPI_header_offset=611197,SPI_header_raw_line_hex=b'SPI,737\r\n'.hex(),
    SPI_bank_requested_bytes=737*396,category_bank_requested_bytes=46*1602)
def decimal(token):
    if not 1<=len(token)<=5 or any(c<48 or c>57 for c in token):raise ValueError('Finite decimal shape differs')
    value=0
    for c in token:value=value*10+c-48
    if value>65535:raise ValueError('Selected finite value exceeds proved range')
    return value
R338=BASE/'round338-spi-rommaps-retained-source-audit'
ranges=[]
rom_lines=json.loads(load(R338/'rommaps57-source-line-cuts.json'))
if actual_line(4374,57).split(b',')[1]!=b'57':raise ValueError('RomMaps count differs')
for r in rom_lines:
    b=actual_line(r['decoded_offset'],r['source_line']);f=b[:-2].split(b',')
    if sha(b)!=r['raw_line_sha256'] or [x.hex() for x in f]!=r['raw_body_fields_hex']:raise ValueError('RomMaps raw input differs')
    slot,low,high=map(decimal,f[:3])
    if slot!=len(ranges) or low>high or len(f[3])+1>128:raise ValueError('RomMaps population domain differs')
    ranges.append(dict(slot=slot,low=low,high=high,source_line=r['source_line'],decoded_offset=r['decoded_offset'],raw_line_sha256=sha(b)))
if len(ranges)!=57:raise ValueError('Not57 ranges')
rows=json.loads(load(BASE/'tw-native-petroom-key-membership-source-336/rows.json','15adb695085dbf712f6ecb011cf3714ca9031aa40f00f98ac4bb39492f33479c'))
positions=json.loads(load(R338/'spi22-new-historical-source-offsets.json'))['rows']
prior_text=json.loads(load(BASE/'tw-native-spi-selector0-projection-source-337/selected22-text-bounds.json'))
prior_values=json.loads(load(BASE/'round339-rommaps-finite-numeric-source-audit/spi22-conditional-WORD116.json'))
prior_masks=json.loads(load(BASE/'tw-native-spi-generic-record-write-source-340/selected22-per-byte-write-coverage.json'))
records=[];concat=bytearray();canonical=bytearray();out=ROOT/'records';out.mkdir(exist_ok=True)
def atom(b):
    if not isinstance(b,bytes):b=str(b).encode('ascii')
    canonical.extend(struct.pack('<I',len(b)));canonical.extend(b)
atom('conditional-original-SPI396-source-composition340-v1');atom(sha(raw))
for s in verified:atom(s['seal_sha256'])
for r,pos,t,prior,mask in zip(rows,positions,prior_text,prior_values,prior_masks):
    key=r['native_key']
    if any(key!=x[k] for x,k in [(pos,'native_key'),(t,'key'),(prior,'key'),(mask,'key')]):raise ValueError('Row order differs')
    b=actual_line(pos['newly_qualified_historical_decoded_offset'],pos['source_line']);f=b[:-2].split(b',')
    if sha(b)!=pos['line_sha256'] or sha(b[:-2])!=r['source_record_sha256'] or [x.hex() for x in f]!=r['raw_fields_hex']:
        raise ValueError('Exact SPI raw source differs')
    if len(f)!=26 or any(c in b[:-2] for c in [0,10,13,26]):raise ValueError('SPI token shape differs')
    if [len(x) for x in f]!=mask['field_lengths'] or max(map(len,f))>34:raise ValueError('Field lengths differ')
    join=b'\n'.join(f[j] for j in range(8,13) if f[j])
    if f[4].hex()!=t['meaningful_name_hex'] or f[7].hex()!=t['meaningful_caption_hex'] or join.hex()!=t['structural_nonempty_LF_join_hex']:
        raise ValueError('Independent text relation differs')
    if len(f[4])>37 or len(f[7])>37 or len(join)>189:raise ValueError('Finite text copy bound differs')
    n={j:decimal(f[j]) for j in [0,3,5,6,13,*range(14,26)]}
    if n[0]!=key or any(n[j] not in [0,1] for j in range(14,26)):raise ValueError('Raw key/bit source differs')
    for j in [3,5,6,13,*range(14,26)]:
        if n[j]!=mask['conditional_numeric_operands'][str(j)]:raise ValueError('Independent scalar relation differs')
    hits=[x for x in ranges if x['low']<=n[3]<=x['high']];slot=hits[0]['slot'] if hits else 65535
    if slot!=prior['conditional_metadata_WORD116'] or slot!=mask['conditional_WORD116']:raise ValueError('Independent firstmatch differs')
    record=bytearray(396);write_mask=bytearray(396);events=[]
    def write(offset,value,site,source):
        if offset+len(value)>396:raise ValueError('Write exceeds396')
        record[offset:offset+len(value)]=value;write_mask[offset:offset+len(value)]=bytes([255])*len(value)
        events.append(dict(site=site,offset=offset,width_bytes=len(value),source=source))
    write(0x114,struct.pack('<H',n[3]),'0045945E','token3 lowWORD')
    write(8,f[4]+b'\0','0045946A','token4 fullCstring+NUL')
    write(0x2D,b'\0','00459473','forcedNUL AFTER copy')
    write(0,struct.pack('<I',n[5]),'00459480','token5 DWORD')
    write(4,struct.pack('<I',n[6]),'00459490','token6 DWORD')
    write(0x2E,f[7]+b'\0','00459493','token7 fullCstring+NUL')
    write(0x53,b'\0','0045949D','forcedNUL AFTER copy')
    write(0x54,join+b'\0','00459560/00459567','actual meaningful join+NUL;no fixed111 write')
    write(0x112,struct.pack('<H',n[13]),'00459574','token13 lowWORD')
    sites=['00459593','004595B1','004595D0','004595EF','0045960E','0045962D','0045964C','00459667',
           '00459687','004596A5','004596C4','004596EC']
    for j,site in enumerate(sites):
        bit=j if j<8 else j-8;offset=0x11A if j<8 else 0x11B
        value=(record[offset] & (255^(1<<bit))) | ((n[14+j]&1)<<bit)
        write(offset,bytes([value]),site,f'token{14+j} lowbit;preserveotherbits')
    write(0x116,struct.pack('<H',slot),'00459943','conditional firstinclusive RomMaps slotAX')
    write(0x118,b'\xff\xff','0045994A','literalWORD FFFF')
    if write_mask.hex()!=mask['written_mask_per_record_byte_hex']:raise ValueError('Independent exact write mask differs')
    if any(record[j] for j,x in enumerate(write_mask) if x==0) or record[0x11B]&0xF0:
        raise ValueError('Unwritten/priorbits changed from conditional allocationzero')
    ordinal=r['source_record_index'];physical=ordinal*396
    if not 0<=ordinal<737 or physical+396>737*396:raise ValueError('Physical slot out of original737 allocation')
    filename=f'records/SPI-key{key}-physical{ordinal}.conditional.bin';data=bytes(record);(ROOT/filename).write_bytes(data);concat.extend(data)
    records.append(dict(key=key,source_record_index=ordinal,original_bank_count=737,physical396_byte_offset=physical,
        source_line=r['source_line'],decoded_offset=pos['newly_qualified_historical_decoded_offset'],
        raw_source_line_sha256=sha(b),normalized_source_body_sha256=sha(b[:-2]),raw_fields_hex=[x.hex() for x in f],
        candidate_record_path=filename,conditional_record_bytes=396,conditional_record_sha256=sha(data),
        conditional_record_hex=data.hex(),write_event_count=len(events),write_events=events,
        all_unwritten_bytes_from_conditional_allocation_zero=True,BYTE11B_highF0_from_conditional_allocation_zero=True,
        conditional_WORD116=slot,matching_ranges=hits,observed_native_output=False,current_bank=False,
        source_projection_only=True,required_premises_document='CONDITIONS.md'))
    atom(key);atom(ordinal);atom(sha(b));atom(sha(data));atom(data)
if len(records)!=22 or [x['source_record_index'] for x in records]!=list(range(517,539)):raise ValueError('Not exact22 original physical slots')
(ROOT/'all22-conditional-records.bin').write_bytes(concat)
(ROOT/'canonical-conditional-source-fingerprint.bin').write_bytes(canonical)
emit('conditional22-record-manifest.json',records)
emit('actual-original-category-bank-facts.json',category_facts)
emit('native-proof-reference-comparisons.json',native)
emit('verified-prior-seals.json',verified)
emit('source-references.json',refs)
emit('accounting.json',dict(selected_rows=22,record_bytes_each=396,conditional_record_bytes_total=len(concat),
    original_SPI_count=737,source_record_indices_first=517,last=538,SPI_category_ordinal=9,category_count=46,
    concatenated_record_sha256=sha(concat),canonical_fingerprint_bytes=len(canonical),canonical_fingerprint_sha256=sha(canonical),
    new_native_methods=0,new_opcode=0,complete_routes_increment=0,
    observed_native_output=False,current_bank=False,native_execution=False,parser_execution=False,resource_decoding=False))
print((ROOT/'accounting.json').read_text())
