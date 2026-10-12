"""Static address-materialization candidates. Linear windows are not CFG proof."""
from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
from capstone.x86 import X86_OP_MEM,X86_OP_IMM
O=Path(__file__).resolve().parent
P=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry')
m=(P/'native-image.bin').read_bytes();r=(P/'originalPE.bin').read_bytes()
assert hashlib.sha256(m).hexdigest()=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert hashlib.sha256(r).hexdigest()=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=r,fast_load=True);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
rows={}
for disp in range(0x8560c,0x8560c+24*50):
    needle=struct.pack('<I',disp)
    for s in pe.sections:
        lo=s.VirtualAddress;hi=lo+s.SizeOfRawData;at=m.find(needle,lo,hi)
        while at>=0:
            for start in range(max(lo,at-12),at+1):
                ins=next(md.disasm(m[start:start+15],start+0x400000,count=1),None)
                if ins is None or ins.mnemonic not in ['lea','add','mov','push']:continue
                match=any((op.type==X86_OP_MEM and op.mem.disp==disp and ins.mnemonic=='lea') or(op.type==X86_OP_IMM and op.imm==disp) for op in ins.operands)
                if not match:continue
                off=pe.get_offset_from_rva(ins.address-0x400000)
                assert r[off:off+ins.size]==bytes(ins.bytes)
                rows[ins.address]=dict(va=f'{ins.address:08X}',bytes=ins.bytes.hex(),mnemonic=ins.mnemonic,operands=ins.op_str,displacement=f'{disp:X}',relative=(disp-0x8560c)%24,pe_equal=True,qualification='UNALIGNED discovery candidate; alias/object unknown')
            at=m.find(needle,at+1,hi)
p=O/'row-pointer-candidates.json'
if p.exists():raise RuntimeError('preserve')
p.write_bytes((json.dumps(list(rows.values()),indent=2)+'\n').encode())
for a,row in sorted(rows.items()):
    if row['relative']<=3:
        print(json.dumps(row))
        print(' | '.join(f'{i.address:08X}:{i.mnemonic} {i.op_str}' for i in list(md.disasm(m[a-0x400000:a-0x400000+110],a))))
print('ALL_CANDIDATE_COUNT',len(rows))
