"""Read-only static PE/source capture. No native or repository code execution."""
from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32

O=Path(__file__).resolve().parent
A=O.parent
P=A.parent/'20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
B=0x400000
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,v):
    p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise RuntimeError('Immutable existing '+str(p))
    p.write_bytes(v if isinstance(v,bytes) else (json.dumps(v,indent=2)+'\n').encode())
def ref(p):
    b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=sha(b),copied=False)
if (O/'capture-complete.json').exists():raise RuntimeError('No repeat capture')
verified=[]
for root in [A/'round353-native-item-computed-writer-source',A/'round352-native-item-row-prefix-writer-source',A.parent/'20261012/round347-normal-entry-native-readiness-source']:
    s=root/'seal.json';raw=s.read_bytes();seal=json.loads(raw)
    rows=seal['members']
    for row in rows:
        name=row.get('name',row.get('path'));blob=(root/name).read_bytes()
        assert len(blob)==row['bytes'] and sha(blob)==row['sha256'],name
    verified.append(dict(seal=ref(s),members=len(rows),bytes=sum(x['bytes'] for x in rows),individual_readback=True))
put('prior-individual-verification.json',verified)
m=(P/'native-image.bin').read_bytes();r=(P/'originalPE.bin').read_bytes()
assert sha(m)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(r)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=r,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32)
put('native-inputs.json',[ref(P/'native-image.bin'),ref(P/'originalPE.bin')])
sections=[];rep=[]
for s in pe.sections:
    lo=s.VirtualAddress;physical_end=lo+s.SizeOfRawData;hi=min(physical_end,len(m))
    sections.append(dict(name=s.Name.rstrip(b'\0').decode('ascii'),rva=lo,raw_pointer=s.PointerToRawData,raw_bytes=s.SizeOfRawData,virtual_bytes=s.Misc_VirtualSize,characteristics=s.Characteristics,execute=bool(s.Characteristics&0x20000000),mapped_intersection=[lo,hi],omitted_mapped_bytes=max(0,physical_end-hi)))
    for at in range(lo,max(lo,hi-1)):
        if m[at:at+2]!=b'\xf3\xa5':continue
        before=m[max(lo,at-100):at]
        values=[x for x in range(0x85600,0x85abd) if x.to_bytes(4,'little') in before]
        if values:
            off=pe.get_offset_from_rva(at)
            assert r[off:off+2]==m[at:at+2]
            rep.append(dict(va=f'{B+at:08X}',nearby_literals=[f'{x:X}' for x in values],qualification='raw F3A5 plus previous100-byte literal coincidence only; alignment, object, direction and count unqualified unless captured below'))
put('section-scan-scope.json',dict(sections=sections,limits='All physical-backed section intersections only. .imprec omitted mapped tail is not scanned. Execute-clear is not absence of code. Indirect helper copies, REP MOVSB, computed aliases without selected literals, farther derivations and arbitrary external writers are outside this finite census.'))
put('finite-rep-literal-candidates.json',rep)
spans=[('actual-selection-control-parent-whole',0x49c400,0x49c4a1,True),('actual-canonical-save-action-whole',0x49c4b0,0x49c767,True),('actual-saved-key-count-restore-whole',0x49c770,0x49c84c,True),('outer-selection-dispatch-selected-partial',0x499d48,0x499d70,False)]
cuts=[];aligned=[]
for name,lo,hi,whole in spans:
    blob=m[lo-B:hi-B];off=pe.get_offset_from_rva(lo-B)
    assert r[off:off+len(blob)]==blob
    ins=list(md.disasm(blob,lo));assert sum(x.size for x in ins)==len(blob)
    sites={x.address for x in ins}
    jumps=[]
    for x in ins:
        if x.mnemonic.startswith('j'):
            target=int(x.op_str,16) if x.op_str.startswith('0x') else None
            if whole:assert target in sites,(name,x.address,x.op_str)
            jumps.append(dict(va=f'{x.address:08X}',target=x.op_str,aligned_inside=target in sites))
        if x.mnemonic in ('call','jmp') and x.op_str.startswith('0x'):
            aligned.append((x.address,int(x.op_str,16)))
    if whole:assert ins[-1].mnemonic=='ret'
    put('native/'+name+'.bin',blob)
    put('native/'+name+'.tsv',('va\tbytes\tmnemonic\toperands\n'+''.join(f'{x.address:08X}\t{x.bytes.hex()}\t{x.mnemonic}\t{x.op_str}\n' for x in ins)).encode())
    cuts.append(dict(name=name,start_va=f'{lo:08X}',end_exclusive_va=f'{hi:08X}',bytes=len(blob),sha256=sha(blob),original_pe_offset=off,pe_equal=True,sites=len(ins),whole_function=whole,ret_sites=[dict(va=f'{x.address:08X}',cleanup=x.op_str) for x in ins if x.mnemonic=='ret'],calls=[dict(va=f'{x.address:08X}',target=x.op_str) for x in ins if x.mnemonic=='call'],jumps=jumps,new_global_method_credit=0))
put('qualified-spans.json',cuts)
callers=[]
for target in [0x49c400,0x49c4b0,0x49c770]:
    for s in pe.sections:
        lo=s.VirtualAddress;hi=min(lo+s.SizeOfRawData,len(m))
        for at in range(lo,max(lo,hi-4)):
            if m[at] in (0xe8,0xe9) and B+at+5+struct.unpack_from('<i',m,at+1)[0]==target:
                callers.append(dict(va=f'{B+at:08X}',target=f'{target:08X}',opcode=f'{m[at]:02X}',aligned_in_retained_cut=(B+at,target) in aligned))
put('relative-caller-candidates.json',dict(rows=callers,raw_count=len(callers),aligned_count=sum(x['aligned_in_retained_cut'] for x in callers),limits='Other raw hits remain unqualified; indirect callers and whole outer499D48 enclosing method are OPEN.'))
refs=[]
repo=Path('C:/Users/risei/Desktop/God2/God2-Server')
for name in ['docs/research/tw-native-item-row-alias-blacklist-chain-20261013.md','docs/research/current-inventory-move-producer-20260926.md','src/db/NativeEquipmentSnapshotRepository.h']:
    refs.append(ref(repo/name))
put('current-source-reference-hashes.json',refs)
summary=dict(whole_code_bytes=sum(x['bytes'] for x in cuts if x['whole_function']),partial_code_bytes=sum(x['bytes'] for x in cuts if not x['whole_function']),code_bytes=sum(x['bytes'] for x in cuts),sites=sum(x['sites'] for x in cuts),data_bytes=0,whole_bodies=3,raw_rep_candidates=len(rep),prefix_writer_open=True,new_method_opcode_format_route_credits=0)
put('capture-complete.json',summary)
print(json.dumps(summary,indent=2))
