"""Bounded static bank-destination/packet-source capture: hash/PE/Capstone only."""
from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
O=Path(__file__).resolve().parent
P=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry')
ROOT=Path('C:/Users/risei/Desktop/God2/God2-Server');B=0x400000
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,v):
    p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise RuntimeError('Preserve '+n)
    p.write_bytes(v if isinstance(v,bytes) else (json.dumps(v,indent=2)+'\n').encode())
m=(P/'native-image.bin').read_bytes();r=(P/'originalPE.bin').read_bytes()
assert sha(m)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(r)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=r,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32)
if (O/'capture-complete.json').exists() or (O/'seal.json').exists():raise RuntimeError('Preserve success')
spans=[('actual-local-offer-action-whole',0x49E440,0x49E78B,True),
       ('actual-own-offer-empty-slot-whole',0x49E290,0x49E2B0,True),
       ('known-offer-request-producer-whole',0x497290,0x4972CE,True),
       ('actual-peer-offer-incoming-whole',0x49DF10,0x49DF4A,True),
       ('actual-refund-aux-clear-whole',0x49DE50,0x49DF08,True),
       ('actual-trade-close-whole',0x49DD40,0x49DE2F,True),
       ('actual-local-action-parent-selected',0x49E326,0x49E359,False),
       ('world50-selected-case',0x46A071,0x46A083,False),
       ('world4F-selected-case',0x46A0A9,0x46A0C4,False),
       ('world52-selected-case',0x46A097,0x46A0A9,False),
       ('known-length25-leaf',0x401258,0x40125E,True),
       ('known-length3-leaf',0x4012DC,0x4012E2,True)]
cuts=[]
for name,s,e,whole in spans:
    raw=m[s-B:e-B];off=pe.get_offset_from_rva(s-B);assert r[off:off+len(raw)]==raw
    ins=list(md.disasm(raw,s));assert sum(i.size for i in ins)==len(raw),(name,'decode')
    sites={i.address for i in ins};branches=[]
    for i in ins:
        if i.mnemonic.startswith('j'):
            target=int(i.op_str,16) if i.op_str.startswith('0x') else None
            if whole:assert target in sites,(name,hex(i.address),i.op_str)
            branches.append(dict(site=f'{i.address:08X}',target=i.op_str,within_cut=target in sites))
    if whole:assert ins[-1].mnemonic=='ret'
    save('native/'+name+'.bin',raw)
    save('native/'+name+'.tsv',('va\tbytes\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode())
    cuts.append(dict(name=name,start_va=f'{s:08X}',end_exclusive_va=f'{e:08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,pe_equal=True,sites=len(ins),whole_function=whole,ret_sites=[dict(va=f'{i.address:08X}',cleanup=i.op_str) for i in ins if i.mnemonic=='ret'],calls=[dict(va=f'{i.address:08X}',target=i.op_str) for i in ins if i.mnemonic=='call'],branches=branches,new_global_method_credit=0))
data=[]
for op in [0x4F,0x50,0x52]:
    for kind,table in [('world',0x46B5D4),('length',0x401324)]:
        s=table+4*op;raw=m[s-B:s-B+4];off=pe.get_offset_from_rva(s-B);assert raw==r[off:off+4]
        name=f'{kind}{op:02X}-table-cell';save('native/'+name+'.bin',raw)
        data.append(dict(name=name,va=f'{s:08X}',bytes=4,original_pe_offset=off,sha256=sha(raw),pe_equal=True,target=f'{struct.unpack("<I",raw)[0]:08X}'))
save('qualified-spans.json',dict(code=cuts,data=data))
targets=[0x49E440,0x49E290,0x497290,0x49DF10,0x49DE50,0x49DD40]
callers=[]
for target in targets:
    found=[]
    for section in pe.sections:
        lo=section.VirtualAddress;hi=min(lo+section.SizeOfRawData,len(m))
        for at in range(lo,hi-4):
            if m[at] in [0xE8,0xE9] and B+at+5+struct.unpack_from('<i',m,at+1)[0]==target:
                found.append(dict(va=f'{B+at:08X}',opcode=f'{m[at]:02X}',instruction_proved_by_cut=any(x['start_va']<=f'{B+at:08X}'<x['end_exclusive_va'] for x in cuts)))
    callers.append(dict(target=f'{target:08X}',raw_relative_candidates=found,indirect_or_omitted_image_tail_open=True))
save('caller-candidates.json',callers)
relations=dict(banks=[dict(name='canonical native inventory',base='U8560C',rows=50,width=24,prefix_writer='OPEN'),dict(name='own offer auxiliary',base='U866E8',rows=8,width=24,prefix1_source='live source-slot lowBYTE at49E68B after native full24copy'),dict(name='peer offer auxiliary',base='U867A8',rows=8,width=24,prefix1_source='incoming50 body+1, selecting same auxiliary index0..7',prefix2_3_source='actual incoming body+2..3 copied unmodified')],
    canonical_U=dict(incoming='Selected WORLD4F/50/52 forms actual primary U=EBP+A7F2F6C',local_action='Supplied action object, propagated from selected49E2B0 parent through ESI/ECX. Equality with canonicalU additionally needs actual parent lifetime/object affinity; not inferred from offsets.'),
    local_copy=dict(source='current signedWORD[U855F0] after497290 child',destination='U+866E8+24*signedBP aux index',computation='8*(3*index+10CDDh)=866E8+24index',width=24,forward_DF0_required=True,source_prefix='copies whole native row then overwrites auxiliary row+1 only',prequeue_source_guard='0..29 or42 or43',postqueue_source_guard='NO repeat guard; live U855F0 reread',native_direct_writes='count BYTE and low keyWORD only; no direct prefix1..3 store',children='opaque except complete49E290 and497290; no global purity'),
    peer_copy=dict(selector='signed BYTE body+1 inclusive0..7',computation='8*(3*index+10CF5h)=867A8+24index',width=24,forward_DF0_required=True,postcopy_child='49E1A0(U,7,destination,index) opaque; no global prefix/state invariance'),
    offer_request=dict(opcode='2A',body_bytes=6,logical_bytes=7,queue_site='4972C3→4132E0',fields=['keyWORD from lowWORD formal2','source-slot lowBYTE formal3','literal quantityBYTE1','peerWORD from lowWORD formal1'],every_body_byte_written=True,no_authority=True),
    rollback=dict(case='4F',order=['49DE50','49DD40(0)'],direct_effects='Conditional low32 purse addition/reset; own/peer auxiliary count and lowkey clears across8rows; auxiliary prefix1..3/tails retained; native inventory rows not directly restored.',unknown_children_open=True),
    close=dict(case='52',order=['49DD40(0)'],direct_effects='UI/state fields only; no direct nativeinventory row prefix/full20 restoration.',unknown_children_open=True),
    no_prefix_writer_solved=True,original_server_issuer_eligibility_acquisition_fresh50_da_native5d_open=True,credits=dict(methods=0,opcodes=0,formats=0,completed_routes=0))
save('bank-source-relations.json',relations)
refs=[]
for name in ['src/protocol/RecoveredTrade.h','docs/research/native-owned-instance-trade-20261003.md','docs/research/current-inventory-move-producer-20260926.md']:
    p=ROOT/name;b=p.read_bytes();refs.append(dict(path=str(p),bytes=len(b),sha256=sha(b),copied=False,scope='Existing current-source coverage/provenance reference only; no historical tests/VM/parser executed'))
save('existing-source-reference-hashes.json',refs)
save('capture-complete.json',dict(scope='Static source only; six existing authentic bodies, two existing length leaves, four selected partials',six_body_bytes=sum(x['bytes'] for x in cuts[:6]),whole_code_bytes=sum(x['bytes'] for x in cuts if x['whole_function']),partial_code_bytes=sum(x['bytes'] for x in cuts if not x['whole_function']),code_bytes=sum(x['bytes'] for x in cuts),data_bytes=sum(x['bytes'] for x in data),sites=sum(x['sites'] for x in cuts),cut_count=len(cuts),prefix_writer_open=True,credits=0))
print(json.dumps(json.loads((O/'capture-complete.json').read_bytes())))
