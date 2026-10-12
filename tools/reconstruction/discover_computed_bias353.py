"""Static candidate discovery of alternate inventory origins/biases; no code proof."""
from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_MEM,X86_OP_IMM
O=Path(__file__).resolve().parent
A=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261013')
P=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry')
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,v):
    p=O/n
    if p.exists():raise RuntimeError('Preserve '+n)
    p.write_bytes((json.dumps(v,indent=2)+'\n').encode())
old=A/'round352-native-item-row-prefix-writer-source';sr=(old/'seal.json').read_bytes()
assert sha(sr)=='a88f087fff38d036f106fc279f3e70445341ec3b7fbc5210d9952f7f02a1d27c'
seal=json.loads(sr)
for row in seal['members']:
    b=(old/row['path']).read_bytes();assert len(b)==row['bytes'] and sha(b)==row['sha256']
save('prior352-individual-verification.json',dict(path=str(old/'seal.json'),sha256=sha(sr),member_count=len(seal['members']),member_bytes=sum(x['bytes'] for x in seal['members']),all_members_verified=True))
m=(P/'native-image.bin').read_bytes();r=(P/'originalPE.bin').read_bytes()
assert sha(m)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(r)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=r,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
save('native-inputs.json',[dict(path=str(P/n),bytes=len(b),sha256=sha(b),copied=False) for n,b in [('native-image.bin',m),('originalPE.bin',r)]])
save('section-scan-scope.json',[dict(name=s.Name.rstrip(b'\0').decode(),rva=s.VirtualAddress,raw_size=s.SizeOfRawData,raw_offset=s.PointerToRawData,mapped_end=min(len(m),s.VirtualAddress+s.SizeOfRawData),execute_flag=bool(s.Characteristics&0x20000000)) for s in pe.sections])
# Main absolute inventory offsets, before-row starts and scaled integral biases.
queries={}
for origin,base in [('U',0x8560c),('Main',0xa7f2f6c+0x8560c)]:
    for row in range(50):
        start=base+24*row
        for relative in range(-16,4):
            queries.setdefault(start+relative,[]).append(dict(origin=origin,row=row,relative=relative,kind='nearprefix displacement'))
    for factor in [2,4,8,16,24]:
        for remainder in range(16):
            if (base-remainder)%factor==0:
                queries.setdefault((base-remainder)//factor,[]).append(dict(origin=origin,factor=factor,remainder=remainder,kind='scaled base bias candidate'))
raw=[];instructions={}
for value,meanings in sorted(queries.items()):
    needle=struct.pack('<I',value)
    for s in pe.sections:
        lo=s.VirtualAddress;hi=min(lo+s.SizeOfRawData,len(m));at=m.find(needle,lo,hi)
        while at>=0:
            raw.append(dict(va=f'{at+0x400000:08X}',literal=hex(value),meanings=meanings))
            for begin in range(max(lo,at-12),at+1):
                i=next(md.disasm(m[begin:begin+15],begin+0x400000,count=1),None)
                if i is None:continue
                if not any((x.type==X86_OP_MEM and x.mem.disp==value) or(x.type==X86_OP_IMM and x.imm==value) for x in i.operands):continue
                off=pe.get_offset_from_rva(begin);assert bytes(i.bytes)==r[off:off+i.size]
                instructions[i.address]=dict(va=f'{i.address:08X}',bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str,meanings=meanings,pe_equal=True,qualification='UNALIGNED candidate only; origin/bias meaning unproved')
            at=m.find(needle,at+1,hi)
save('computed-bias-raw-hits.json',raw)
save('computed-bias-instruction-candidates.json',[instructions[x] for x in sorted(instructions)])
for x in sorted(instructions):
    i=instructions[x]
    if any(z['origin']=='Main' or z['kind']=='scaled base bias candidate' for z in i['meanings']):print(json.dumps(i))
print(json.dumps(dict(raw_hits=len(raw),instruction_candidates=len(instructions),limits='Mapped all-section intersections only; no global absence or computed/indirect exhaustiveness.')))
