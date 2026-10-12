"""Static source capture and symbolic-domain arithmetic; no native/provider execution."""
from pathlib import Path
import hashlib
import json
import capstone
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
PEER = BASE / 'tw-native-petroom-action-context-source-341'
MAPPED = BASE / 'tw-native-entry-body-alias-and-remote-opaque-315/native-entry/native-image.bin'
ORIGINAL = BASE / 'tw-native-entry-body-alias-and-remote-opaque-315/native-entry/originalPE.bin'
def sha(b):
    return hashlib.sha256(b).hexdigest()
def emit(name,value):
    path = ROOT/name
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(value if isinstance(value,bytes) else value.encode('utf-8'))
def jemit(name,value):
    emit(name,json.dumps(value,ensure_ascii=False,indent=2)+'\n')

b = MAPPED.read_bytes()
p = ORIGINAL.read_bytes()
assert sha(b)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(p)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe = pefile.PE(data=p)
md = Cs(CS_ARCH_X86,CS_MODE_32)
md.detail = True
sealraw = (PEER/'seal.json').read_bytes()
assert sha(sealraw)=='d332146cfe45293f0231480c00f182e27b17ad55bef78c3b8df7092cc82fa018'
seal = json.loads(sealraw)
for member in seal['members']:
    raw = (PEER/member['path']).read_bytes()
    assert len(raw)==member['bytes'] and sha(raw)==member['sha256']
fullpath = PEER/'native/primary-pre-action-context-complete.bin'
fullraw = fullpath.read_bytes()
assert len(fullraw)==0x4D78C7-0x4D7230
fullpeoffset = pe.get_offset_from_rva(0xD7230)
assert fullraw==b[0xD7230:0xD78C7]==p[fullpeoffset:fullpeoffset+len(fullraw)]
fullins = list(md.disasm(fullraw,0x4D7230))
assert sum(i.size for i in fullins)==len(fullraw) and fullins[-1].mnemonic=='ret'
addresses = {i.address for i in fullins}
for i in fullins:
    if i.mnemonic.startswith('j') and i.operands[0].type==capstone.CS_OP_IMM:
        assert i.operands[0].imm in addresses
refs = [{'path':str(MAPPED),'bytes':len(b),'sha256':sha(b)},
        {'path':str(ORIGINAL),'bytes':len(p),'sha256':sha(p)},
        {'path':str(PEER/'seal.json'),'bytes':len(sealraw),'sha256':sha(sealraw),
         'verified_individual_members':len(seal['members'])},
        {'path':str(fullpath),'bytes':len(fullraw),'sha256':sha(fullraw),
         'original_pe_offset':fullpeoffset,'mapped_pe_equal':True,
         'complete_entry':'004D7230','end_exclusive':'004D78C7',
         'ret_sites':[f'{i.address:08X}' for i in fullins if i.mnemonic=='ret']}]
jemit('source-references.json',{'inputs':refs,'capstone':capstone.__version__,'pefile':pefile.__version__})
cuts=[]
for name,a,z in [('selected-counter-excerpt',0x4D76E0,0x4D776F),
                 ('initial-key-clock-excerpt',0x4D7230,0x4D7257)]:
    raw = b[a-0x400000:z-0x400000]
    off = pe.get_offset_from_rva(a-0x400000)
    assert raw==p[off:off+len(raw)]
    ins = list(md.disasm(raw,a))
    assert sum(i.size for i in ins)==len(raw)
    assert all(i.address in addresses for i in ins)
    emit('native/'+name+'.bin',raw)
    emit('native/'+name+'.tsv','va\traw_hex\tmnemonic\toperands\n'+''.join(
        f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins))
    cuts.append({'name':name,'start':f'{a:08X}','end_exclusive':f'{z:08X}',
                 'bytes':len(raw),'sha256':sha(raw),'original_pe_offset':off,
                 'mapped_pe_equal':True,'complete_function':False,
                 'enclosing_complete_function_reference':str(fullpath)})
jemit('cuts.json',cuts)
clock=[]
for descriptor in pe.DIRECTORY_ENTRY_IMPORT:
    for symbol in descriptor.imports:
        if symbol.address==0x5707BC:
            clock.append({'iat_va':f'{symbol.address:08X}','dll':descriptor.dll.decode('ascii'),
                          'symbol':symbol.name.decode('ascii')})
assert len(clock)==1 and clock[0]['symbol']=='timeGetTime'
jemit('clock-import.json',clock)

# These are source-domain constants and partitions, not sampled native inputs,
# projection invocations, observed clocks, or a synthetic test harness.
M=1<<32
L=1<<18
H=60000
jemit('symbolic-domain-proof.json',{
    'word_modulus':M,'low18_modulus':L,'low18_mask':L-1,'high14_mask':M-L,
    'difference':'d=(clock_gate_u32-U8C_at_gate_u32) mod 2^32',
    'cdq_mask':'s=0 for 0<=d<2^31; s=FFFFFFFF for 2^31<=d<2^32',
    'native_magnitude':'m=((d xor s)-s) mod 2^32',
    'partition':[{'d_inclusive':[0,(1<<31)-1],'m':'d'},
                 {'d_inclusive':[1<<31,M-1],'m':'2^32-d'}],
    'm_range_inclusive':[0,1<<31],
    'pass_unsigned_ge60000_d_inclusive':[H,M-H],
    'fail_d_inclusive':[[0,H-1],[M-H+1,M-1]],
    'boundary_domain':{'threshold':H,'last_negative_magnitude_pass_difference':M-H,
                       'minimum_signed_difference_magnitude':1<<31,
                       'wrap_decrement_magnitude':1},
    'first_u4c_transform':'write1=(a & FFFC0000) | (((a & 0003FFFF)+60) mod 2^18)',
    'no_low18_wrap_a_low_inclusive':[0,L-61],
    'low18_wrap_a_low_inclusive':[L-60,L-1],
    'second_u4c_operand':'b=DWORD U4C read at004D771D after second selected clock CALL004D771B',
    'row_payload':'b & 0003FFFF; equality b==write1 is NOT a source premise',
    'stage_order':['first U4C read a at7708','direct U4C write write1 at7718',
                   'second selected clock call at771B','second U4C read b at771D',
                   'direct U8C clock_return write at7720','live signedBYTE U8 read at7726',
                   'direct inventory row+8 DWORD store at7733'],
    'signed_byte_domain':[-128,127],
    'row_relative_offset':'85618h + 24*signedBYTE(U8_at7726)',
    'offset_domain_inclusive':[0x85618-24*128,0x85618+24*127],
    'category_gate':'WORD U+A6D4==0; no source semantic/category name established',
    'runtime_or_provider_execution':False})
jemit('accounting.json',{'excerpt_code_bytes':sum(x['bytes'] for x in cuts),
    'data_cut_bytes':0,'referenced_complete_method_bytes':len(fullraw),
    'new_method_credit':0,'new_opcode_credit':0,'connected_route_credit':0})
header = Path('C:/Users/risei/Desktop/God2/God2-Server/src/protocol/RecoveredPetEggLocalCounterSource.h')
headerraw = header.read_bytes()
assert sha(headerraw)=='f1138228f0c2e8f73d5da962785147446c8fbfb0461286b3318e4956bc544029'
emit('source/RecoveredPetEggLocalCounterSource.h',headerraw)
jemit('implementation-source-reference.json',{'path':str(header),'bytes':len(headerraw),
    'sha256':sha(headerraw),'review':'source text only, no compilation/import/provider execution',
    'matches_selected_native_staged_arithmetic':True})
print(json.dumps({'capture':'successful static source arithmetic only',
                  'excerpt_bytes':sum(x['bytes'] for x in cuts),'peer_members_verified':len(seal['members'])}))
