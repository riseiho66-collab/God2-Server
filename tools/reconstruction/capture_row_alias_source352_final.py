"""Bounded static-source capture only: read/hash/PE/Capstone; no target execution."""
from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
O=Path(__file__).resolve().parent/'qualified-final'
O.mkdir(exist_ok=False)
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012')
P=A/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server');B=0x400000
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,v):
    p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise RuntimeError('Preserve '+n)
    p.write_bytes(v if isinstance(v,bytes) else (json.dumps(v,indent=2)+'\n').encode())
def ref(p):
    b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=sha(b),copied=False)
if (O/'capture-complete.json').exists() or (O/'seal.json').exists():raise RuntimeError('Preserve success')
m=(P/'native-image.bin').read_bytes();r=(P/'originalPE.bin').read_bytes()
assert sha(m)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(r)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=r,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32)
save('capture-native-inputs.json',[ref(P/'native-image.bin'),ref(P/'originalPE.bin')])
priors=[]
for name,pin in [('round347-normal-entry-native-readiness-source','10d2c4abe81d233eb6dc415c1025b05913f4292da1a99d4f24ddb5a2f90742a5'),
    ('round346-initial-owned-material-main-plan',None),
    ('round351-native-item-ui-output-cell-source','fcc734b12be68398b651c72d8d807818f90ebf14e0a67b4c3b715924a6d46f43'),
    ('round348-native-item-material-helper-source','84f9106d09283a184b3361aff4d8a4bfbd5ac1946fedfe91a8fbae538f339c9f')]:
    base=A/name;raw=(base/'seal.json').read_bytes()
    if pin:assert sha(raw)==pin
    seal=json.loads(raw)
    for member in seal['members']:
        old=(base/member['path']).read_bytes();assert len(old)==member['bytes'] and sha(old)==member['sha256']
    priors.append(dict(seal=ref(base/'seal.json'),member_count=len(seal['members']),member_bytes=sum(x['bytes'] for x in seal['members']),all_individual_members_verified=True,copied=False))
save('prior-individual-verification.json',priors)
spans=[('known-row-getter-whole',0x498D30,0x498D62,True),
       ('actual-hotkey-selector-parent-whole',0x514890,0x514ABC,True),
       ('actual-row-alias-consumer-whole',0x514AC0,0x514B6A,True),
       ('parent-incoming-selected-partial',0x5159E1,0x5159F8,False),
       ('opaque-action-delegate-argument-guards-partial',0x518E50,0x518EE8,False),
       ('opaque-action-delegate-return-tail-partial',0x5192B2,0x5192D9,False)]
cuts=[]
for name,s,e,whole in spans:
    raw=m[s-B:e-B];off=pe.get_offset_from_rva(s-B);assert r[off:off+len(raw)]==raw
    ins=list(md.disasm(raw,s));assert sum(i.size for i in ins)==len(raw)
    sites={i.address for i in ins};jumps=[]
    for i in ins:
        if i.mnemonic.startswith('j'):
            target=int(i.op_str,16) if i.op_str.startswith('0x') else None
            if whole:assert target in sites
            jumps.append(dict(site=f'{i.address:08X}',target=i.op_str,within_cut=target in sites))
    if whole:assert ins[-1].mnemonic=='ret'
    save('native/'+name+'.bin',raw)
    save('native/'+name+'.tsv',('va\tbytes\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode())
    cuts.append(dict(name=name,start_va=f'{s:08X}',end_exclusive_va=f'{e:08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,pe_equal=True,sites=len(ins),whole_function=whole,ret_sites=[f'{i.address:08X}' for i in ins if i.mnemonic=='ret'],calls=[dict(site=f'{i.address:08X}',target=i.op_str) for i in ins if i.mnemonic=='call'],jumps=jumps,new_global_method_credit=0))
save('qualified-spans.json',cuts)
# Authentic direct CALL targets in retained complete parent; static raw census includes all sections.
raw_calls=[]
for target in [0x498D30,0x514AC0,0x514890]:
    sites=[]
    for section in pe.sections:
        lo=section.VirtualAddress;hi=min(lo+section.SizeOfRawData,len(m))
        for at in range(lo,hi-4):
            if m[at] in (0xE8,0xE9) and B+at+5+struct.unpack_from('<i',m,at+1)[0]==target:
                sites.append(dict(va=f'{B+at:08X}',opcode=f'{m[at]:02X}',qualification='raw relative candidate; only sites in qualified-spans aligned instructions are code-proved'))
    raw_calls.append(dict(target=f'{target:08X}',candidates=sites,indirect_targets_open=True))
save('relative-caller-census.json',raw_calls)
relations=dict(prefix_literal_scan=dict(raw_literal_hits=318,materialization_candidates=102,prefix_overlapping_fixed_displacement_store_candidates=0,global_absence_claim=False,excluded='Computed alias/bias, indirect calls/pointers, other object origins and bulk-copy destination derivations not exhaustively covered.'),
    getter=dict(formal_width='signed lowWORD',low=0,high=37,low_key_nonzero_required=True,count_not_checked=True,return_value='NULL or supplied_object+8560C+24*signedWORDslot',canonical_primary_U_affinity='conditional: live control+20 pointer must equal actual canonical U; no constructor or global affinity asserted'),
    consumer=dict(formal_width='signed lowBYTE',first_pointer_read='current DWORD[control+20]',first_getter_call='514ACF',opaque_children_before_key_read=['5156E0','51E6E0'],key_snapshot='WORD[first retained row+4] at514AF1',reverse_scan='EBX29 downward to signed lowBYTE input; current control20 reread each iteration; count>0 and lowkey matches capturedWORD',stores=[dict(va='514B34',width=2,destination='control+A9E9C7A',source='WORD[final ESIrow+4]'),dict(va='514B3B',width=1,destination='control+A9E9C7C',source='BL of final reverse counter'),dict(va='514B51',width=1,destination='control+44C',source='AL from first5156E0')],loop_limits='No final NULL check at514B2E. Input30..37 skips reverse loop with EBX29 and initial pointer. Failed search may mismatch EBX/finalrow or fault. No generic safe-selection/ownership statement.',
        delegate=dict(site='514B5D',target='518E50',arguments=['DWORD5','full EAX from second5156E0','DWORD1','pointer control+44C'],push_order=['514B4C pointer','514B4D one','514B58 EAX','514B59 five'],note='First two pushes survive zero-arg second5156E0. No request opcode is established by numeric5; delegate body omitted.')),
    parent=dict(input_choices=[0,1,2,3,4],gates='418610(current control+8, keycode70h..74h) tested in priority order; first true invokes514AC0; opaque predicate/time imports preserve calling convention and may affect current state.',all_slots_or_key_profile_claim=False),
    remaining_prefix_writer='OPEN: none qualified. Next alias source requires authentic concrete store/copy destination proof, not a global absence or zero-prefix premise.',credits=dict(methods=0,opcodes=0,formats=0,completed_routes=0))
save('source-relations.json',relations)
refs=[]
for name in ['docs/research/current-inventory-20260919.md','docs/research/current-item-transition-20260919.md','src/db/NativeEquipmentSnapshotRepository.h']:
    p=ROOT/name;refs.append(ref(p))
save('current-source-reference-hashes.json',refs)
save('capture-complete.json',dict(scope='Static-only source closure; no native execution',whole_code_bytes=sum(x['bytes'] for x in cuts if x['whole_function']),selected_partial_code_bytes=sum(x['bytes'] for x in cuts if not x['whole_function']),code_bytes=sum(x['bytes'] for x in cuts),data_bytes=0,sites=sum(x['sites'] for x in cuts),cuts=len(cuts),prefix_writer_open=True,credits=0))
print(json.dumps(json.loads((O/'capture-complete.json').read_bytes())))
