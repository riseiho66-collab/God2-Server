"""Static byte-candidate discovery only; not instruction or method qualification."""
from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_AC_WRITE
from capstone.x86 import X86_OP_MEM
O=Path(__file__).resolve().parent
P=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry')
def h(b): return hashlib.sha256(b).hexdigest()
def save(n,x):
    p=O/n
    if p.exists():raise RuntimeError('preserve '+n)
    p.write_bytes((json.dumps(x,indent=2)+'\n').encode())
m=(P/'native-image.bin').read_bytes();r=(P/'originalPE.bin').read_bytes()
assert h(m)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert h(r)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=r,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
sections=[dict(name=s.Name.rstrip(b'\0').decode('ascii'),rva=s.VirtualAddress,virtual_size=s.Misc_VirtualSize,raw_offset=s.PointerToRawData,raw_size=s.SizeOfRawData,characteristics=s.Characteristics,execute=bool(s.Characteristics&0x20000000)) for s in pe.sections]
save('original-inputs.json',[dict(path=str(P/n),bytes=len(b),sha256=h(b),copied=False) for n,b in [('native-image.bin',m),('originalPE.bin',r)]])
save('all-section-scan-scope.json',dict(sections=sections,scope='ALL physical-backed sections irrespective of execute flags. Raw hits are candidates, not aligned code. Computed pointer stores are not covered.'))
found={};rawhits=[]
for disp in range(0x8560c,0x8560c+24*50):
    # All row displacement constants, including DWORD store at row+0.
    needle=struct.pack('<I',disp)
    for s in pe.sections:
        lo=s.VirtualAddress;hi=lo+s.SizeOfRawData;at=m.find(needle,lo,hi)
        while at>=0:
            rawhits.append(dict(literal=hex(disp),va=hex(at+0x400000),section=s.Name.rstrip(b'\0').decode()))
            for start in range(max(lo,at-12),at+1):
                ins=next(md.disasm(m[start:start+15],start+0x400000,count=1),None)
                if ins is None:continue
                for op in ins.operands:
                    if op.type!=X86_OP_MEM or op.mem.disp!=disp or not(op.access&CS_AC_WRITE):continue
                    relative=(disp-0x8560c)%24
                    if not any(relative<=x<relative+op.size for x in [1,2,3]):continue
                    key=ins.address
                    off=pe.get_offset_from_rva(key-0x400000)
                    assert r[off:off+ins.size]==bytes(ins.bytes)
                    found[key]=dict(va=hex(key),bytes=ins.bytes.hex(),mnemonic=ins.mnemonic,operands=ins.op_str,width=op.size,displacement=hex(disp),row_relative=relative,original_pe_offset=off,pe_equal=True,qualification='UNALIGNED raw candidate only')
            at=m.find(needle,at+1,hi)
save('row-literal-raw-hits.json',rawhits)
save('prefix-store-instruction-candidates.json',[found[k] for k in sorted(found)])
print(json.dumps(dict(raw_literal_hits=len(rawhits),prefix_store_candidates=len(found),candidates=[found[k] for k in sorted(found)]),indent=2))
