"""Static byte/PE/Capstone write inventory; never native/parser/codec execution."""
from pathlib import Path
import hashlib,json,struct
import capstone,pefile
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
PIN=BASE/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
def sha(b):return hashlib.sha256(b).hexdigest()
def emit(p,obj):
    (ROOT/p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
refs=[];verified=[]
def load(p,h=None):
    b=p.read_bytes();actual=sha(b)
    if h and actual!=h:raise ValueError('Pinned source changed: '+str(p))
    refs.append(dict(path=str(p),bytes=len(b),sha256=actual));return b
def verify(name,h):
    p=BASE/name;s=json.loads(load(p/'seal.json',h));members=s['members']
    for m in members:
        b=(p/m['path']).read_bytes()
        if sha(b)!=m['sha256'] or len(b)!=m['bytes']:raise ValueError('Seal member differs')
    size=sum(m['bytes'] for m in members)
    if len(members)!=s['member_count'] or size!=s.get('member_bytes',s.get('retained_member_bytes',s.get('total_member_bytes'))):
        raise ValueError('Member accounting differs')
    verified.append(dict(package=name,seal_sha256=h,members=len(members),bytes=size,all_members_equal=True))
for name,h in [
    ('tw-native-f4-list-definition-key-source-335','c44c9c7c97f7f889600303fcb2758177bdfed74fc5f10f91f4c298dc89bd17af'),
    ('tw-native-petroom-key-membership-source-336','488b2275fba2abbf913ed21f4868ae675ddb10ac711d5f0d13a6e3555f02c9c9'),
    ('tw-native-spi-selector0-projection-source-337','802e0b2d22e16e5423c5882eac2325e45a35d67ef564d3d6327c3d38ce89ed9b'),
    ('tw-native-spi-numeric-input-source-338','fffa554ba06a9282c2334a7807d5b3a3cfa1ced42a7d24acbd7ef65e39e8b612'),
    ('tw-native-spi-numeric-classification-source-338','4822460aa146325aebd58050cc86a9f85ff98cf1f5d12ff8d985abb29e365658'),
    ('tw-native-spi-line-reader-source-339','ce9cb9b12a25519df6d5849833345799f516a5d788f82ba544ac71e31de775f9'),
    ('round339-rommaps-finite-numeric-source-audit','c6828b7fe939c4b0d1e00a77b7153daf382a0f8298c378702c4b33cb9263e9b8'),
]:verify(name,h)
mapped=load(PIN/'native-image.bin','149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763')
original=load(PIN/'originalPE.bin','5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde')
pe=pefile.PE(data=original,fast_load=True);md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);md.detail=True
out=ROOT/'native';out.mkdir(exist_ok=True)
cuts=[];parser=[]
def cut(name,a,z,data=False):
    b=mapped[a-0x400000:z-0x400000];off=pe.get_offset_from_rva(a-0x400000)
    if b!=original[off:off+len(b)]:raise ValueError('PE differs')
    (out/(name+'.bin')).write_bytes(b)
    r=dict(name=name,kind='data' if data else 'known-complete-method',start_va=f'{a:08X}',
        end_exclusive_va=f'{z:08X}',bytes=len(b),sha256=sha(b),original_pe_offset=off,pe_equal=True)
    ins=[]
    if not data:
        ins=list(md.disasm(b,a))
        if sum(i.size for i in ins)!=len(b):raise ValueError('Incomplete instruction cut')
        (out/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+''.join(
            f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins),encoding='utf-8',newline='\n')
        r.update(actual_entry_va=f'{a:08X}',returns=[f'{i.address:08X}' for i in ins if i.mnemonic.startswith('ret')])
    cuts.append(r);return ins
for name,a,z in [
    ('known-generic-parser-complete',0x459420,0x45995F),
    ('known-field-string-copy-complete',0x451AE0,0x451B2C),
    ('known-field-string-pointer-complete',0x451B60,0x451B98),
    ('known-field-number-complete',0x451BA0,0x451BDC),
    ('known-generic-row-loader-complete',0x4599B0,0x459A5F),
]:
    ins=cut(name,a,z)
    if a==0x459420:parser=ins
for name,a,z in [('known-selector-target-table',0x459960,0x459984),
                  ('known-selector-index-table',0x459984,0x4599A7),
                  ('empty-string-literal',0x5B4640,0x5B4641),
                  ('LF-literal',0x584BB0,0x584BB2)]:cut(name,a,z,True)
direct=[]
for i in parser:
    if i.mnemonic=='mov' and i.operands[0].type==capstone.x86.X86_OP_MEM and md.reg_name(i.operands[0].mem.base)=='ebp':
        o=i.operands[0];common=i.address<0x45970D or i.address>=0x459933
        direct.append(dict(va=f'{i.address:08X}',raw_hex=i.bytes.hex(),offset=o.mem.disp,width_bytes=o.size,
            offset_hex=f'{o.mem.disp:X}',source_operand=i.op_str.split(', ',1)[1],
            scope='common-selected-selector0' if common else 'other-category-branch',direction='write-to-record'))
if sum(x['scope']=='common-selected-selector0' for x in direct)!=20:raise ValueError('Common direct store census differs')
table=mapped[0x459960-0x400000:0x4599A7-0x400000]
ptrs=struct.unpack('<9I',table[:36]);indices=table[36:]
selectors=[dict(selector=s,index=indices[s-1],target_va=f'{ptrs[indices[s-1]]:08X}') for s in range(1,36)]
emit('all-direct-EBP-record-stores.json',direct)
emit('selector1-35-table.json',selectors)
stack=[]
for i in parser:
    if i.mnemonic=='mov' and i.operands[0].type==capstone.x86.X86_OP_MEM and md.reg_name(i.operands[0].mem.base)=='esp':
        o=i.operands[0];stack.append(dict(va=f'{i.address:08X}',raw_hex=i.bytes.hex(),ESP_displacement=o.mem.disp,
            width_bytes=o.size,source=i.op_str.split(', ',1)[1],direction='write-to-scratch-stack-not-record'))
emit('direct-stack-store-census.json',stack)
emit('other-category-write-boundary.json',[
    dict(target='0045970D',selectors=[5],writes='token27 BYTE11C'),
    dict(target='00459721',selectors=[1,2,25,26],writes='token26 BYTE11C;token27 BYTE11D;token28 WORD11E;token29 BYTE120'),
    dict(target='00459763',selectors=[13,32],writes='tokens26..31 BYTE11C..121'),
    dict(target='004597C2',selectors=[34],writes='tokens26..35 BYTE11C..125'),
    dict(target='0045985D',selectors=[28],writes='token26 BYTE11C;token28 BYTE11D'),
    dict(target='00459880',selectors=[33],writes='14 pairs:token26+2i DWORD(11C+8i);token27+2i BYTE(120+8i)',
         loop_store_sites=['004598A1','004598A9'],last_offsets=['184..187','188'],padding_3bytes_each_pair_unwritten=True),
    dict(target='004598BE',selectors=[6],writes='token26 fullCstring+NUL to11C thenforcedBYTE12B0;token27 BYTE12C;token28 BYTE12D;token29 BYTE12E',
         helper_site='004598C9',forcedNUL_site='004598D2'),
    dict(target='00459904',selectors=[35],writes='token27 fullCstring+NUL to11C;token28 fullCstring+NUL to142;token29 BYTE168',
         helper_sites=['0045990F','0045991F'],no_forcedNUL_in_this_branch=True),
    dict(target='00459933',selectors=[3,4,7,8,9,10,11,12,14,15,16,17,18,19,20,21,22,23,24,27,29,30,31],writes='common tail only'),
])
raw=[]
for a,h,meaning in [
    (0x459448,'8bac241c050000','formalarg2 record pointer toEBP'),
    (0x4596D5,'8b942424050000','formalarg4 category selector toEDX'),
    (0x4596E6,'81e2ff000000','mask selector lowBYTE'),
    (0x4596F2,'8d42ff','selector0 yieldsFFFFFFFF'),
    (0x4596F5,'83f822','compare selector-1 against34'),
    (0x4596F8,'0f8735020000','unsignedJA skips specialwrites to459933'),
    (0x45943F,'8dbc2415010000','EDI is scratch SP115 notrecord'),
    (0x459446,'f3ab','REPSTOSD scratch local only'),
    (0x459544,'c68424d101000000','forced scratch descriptionindexBD NUL'),
]:
    b=bytes.fromhex(h);off=pe.get_offset_from_rva(a-0x400000)
    if b!=mapped[a-0x400000:a-0x400000+len(b)] or b!=original[off:off+len(b)]:raise ValueError('Raw instruction proof differs')
    raw.append(dict(va=f'{a:08X}',raw_hex=h,meaning=meaning,pe_equal=True))
emit('raw-instruction-review.json',raw)
operations=[
    dict(site='0045945E',offset=0x114,width=2,source='token3 lowWORD',kind='scalar'),
    dict(site='0045946A',offset=8,source='token4 fullCstring+NUL',kind='writehelper451AE0'),
    dict(site='00459473',offset=0x2D,width=1,source='literal0 AFTER fullcopy',kind='forcedNUL'),
    dict(site='00459480',offset=0,width=4,source='token5 DWORD',kind='scalar'),
    dict(site='00459490',offset=4,width=4,source='token6 DWORD',kind='scalar'),
    dict(site='00459493',offset=0x2E,source='token7 fullCstring+NUL',kind='writehelper451AE0'),
    dict(site='0045949D',offset=0x53,width=1,source='literal0 AFTER fullcopy',kind='forcedNUL'),
    dict(site='00459560/00459567',offset=0x54,source='nonempty token8..12 LF join+NUL',kind='REPcopy'),
    dict(site='00459574',offset=0x112,width=2,source='token13 lowWORD',kind='scalar'),
]
bit_sites=[0x459593,0x4595B1,0x4595D0,0x4595EF,0x45960E,0x45962D,0x45964C,0x459667,
           0x459687,0x4596A5,0x4596C4,0x4596EC]
for j,site in enumerate(bit_sites):
    bit=j if j<8 else j-8;off=0x11A if j<8 else 0x11B
    operations.append(dict(site=f'{site:08X}',offset=off,width=1,source=f'token{14+j} lowbit',kind='read-modify-write',
        replaced_mask=f'{1<<bit:02X}',preserved_mask=f'{255^(1<<bit):02X}'))
operations.extend([dict(site='00459943',offset=0x116,width=2,source='459FC0 AX conditional RomMaps ordinal',kind='scalar'),
                   dict(site='0045994A',offset=0x118,width=2,source='literalFFFF',kind='scalar')])
emit('selector0-ordered-write-operations.json',operations)
rows=json.loads(load(BASE/'tw-native-petroom-key-membership-source-336/rows.json',
    '15adb695085dbf712f6ecb011cf3714ca9031aa40f00f98ac4bb39492f33479c'))
rom=json.loads(load(BASE/'round339-rommaps-finite-numeric-source-audit/spi22-conditional-WORD116.json'))
text=json.loads(load(BASE/'tw-native-spi-selector0-projection-source-337/selected22-text-bounds.json',
    'ccdf87fdf03608eb5dea585eaf7f7084b54eac7eca549e870c28eeee7c5092a4'))
coverage=[]
def intervals(mask,predicate):
    found=[];a=None
    for j,x in enumerate(mask+[256]):
        yes=j<396 and predicate(x)
        if yes and a is None:a=j
        if not yes and a is not None:found.append(dict(start=a,end_exclusive=j));a=None
    return found
for r,t,m in zip(rows,text,rom):
    if r['native_key']!=t['key'] or r['native_key']!=m['key']:raise ValueError('Row order differs')
    f=[bytes.fromhex(x) for x in r['raw_fields_hex']]
    if sha(b','.join(f))!=r['source_record_sha256']:raise ValueError('Raw row differs')
    join=b'\n'.join(f[j] for j in range(8,13) if f[j])
    if len(f[4])>37 or len(f[7])>37 or len(join)>189 or max(map(len,f))>255:raise ValueError('Text input exceeds finite native scope')
    numeric={}
    for j in [3,5,6,13,*range(14,26)]:
        if not f[j] or any(c<48 or c>57 for c in f[j]) or len(f[j])>5:raise ValueError('Finite numeric input differs')
        n=0
        for c in f[j]:n=n*10+c-48
        numeric[str(j)]=n
    if any(n>65535 for n in numeric.values()) or any(numeric[str(j)] not in [0,1] for j in range(14,26)):
        raise ValueError('Finite scalar/bit domain differs')
    writes=[0]*396;known=[0]*396
    def mark(a,n,knowledge=255):
        if a+n>396:raise ValueError('Write mask exceeds record')
        for j in range(a,a+n):writes[j]=255;known[j]|=knowledge
    mark(0,8);mark(8,len(f[4])+1);mark(0x2D,1);mark(0x2E,len(f[7])+1);mark(0x53,1)
    mark(0x54,len(join)+1);mark(0x112,8);mark(0x11A,1);mark(0x11B,1,15)
    coverage.append(dict(key=r['native_key'],source_record_sha256=r['source_record_sha256'],
        source_record_index=r['source_record_index'],source_line=r['source_line'],field_lengths=[len(x) for x in f],
        name_length=len(f[4]),caption_length=len(f[7]),description_length=len(join),
        conditional_numeric_operands=numeric,conditional_WORD116=m['conditional_metadata_WORD116'],
        BYTE11A_replaced_mask='FF',BYTE11B_replaced_mask='0F',BYTE11B_preserved_mask='F0',
        written_mask_per_record_byte_hex=bytes(writes).hex(),conditional_known_bit_mask_per_record_byte_hex=bytes(known).hex(),
        touched_byte_count=sum(x!=0 for x in writes),fully_known_byte_count=sum(x==255 for x in known),
        partially_known_bytes=[dict(offset=0x11B,known_mask='0F',unmet_prior_bits='F0')],
        entirely_unwritten_intervals=intervals(writes,lambda x:x==0),
        uncovered_allocated_byte_count=sum(x==0 for x in writes),
        full396_generated=False,initial_zeroing_assumed=False,selector0_is_precondition=True))
emit('selected22-per-byte-write-coverage.json',coverage)
emit('selector0-region-map.json',[
    dict(start=0,end_exclusive=4,role='token5 DWORD'),dict(start=4,end_exclusive=8,role='token6 DWORD'),
    dict(start=8,end_exclusive=0x2E,role='token4 Cstring variablelen+NUL;forced2D0;otherbytesuntouched'),
    dict(start=0x2E,end_exclusive=0x54,role='token7 Cstring variablelen+NUL;forced530;otherbytesuntouched'),
    dict(start=0x54,end_exclusive=0x112,role='nonempty8..12 LF joinvariablelen+NUL;otherbytesuntouched'),
    dict(start=0x112,end_exclusive=0x114,role='token13 lowWORD'),
    dict(start=0x114,end_exclusive=0x116,role='token3 lowWORD'),
    dict(start=0x116,end_exclusive=0x118,role='conditionalRomMaps AX'),
    dict(start=0x118,end_exclusive=0x11A,role='literalWORD FFFF'),
    dict(start=0x11A,end_exclusive=0x11B,role='8bits replaced14..21'),
    dict(start=0x11B,end_exclusive=0x11C,role='low4bits replaced22..25;high4 preserved'),
    dict(start=0x11C,end_exclusive=0x18C,role='untouched selector0 finite22;initialization OPEN'),
])
emit('native/cuts.json',cuts)
emit('verified-prior-seals.json',verified)
emit('source-references.json',refs)
emit('accounting.json',dict(known_complete_cuts=sum(x['kind']!='data' for x in cuts),
    code_bytes=sum(x['bytes'] for x in cuts if x['kind']!='data'),data_bytes=sum(x['bytes'] for x in cuts if x['kind']=='data'),
    common_direct_record_stores=20,all_direct_EBP_record_stores=len(direct),selected_rows=len(coverage),
    min_touched_bytes=min(r['touched_byte_count'] for r in coverage),max_touched_bytes=max(r['touched_byte_count'] for r in coverage),
    fully_unwritten_common_suffix_start_hex='11C',fully_unwritten_common_suffix_bytes=112,
    max_all_raw_token_bytes=max(max(r['field_lengths']) for r in coverage),
    full396_generated=False,zero_initialization_qualified=False,selector0_initialization_qualified=False,
    new_method_credit=0,new_opcode=0,complete_route_increment=0,
    capstone_version=capstone.__version__,pefile_version=pefile.__version__))
print((ROOT/'accounting.json').read_text())
