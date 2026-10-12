from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_AC_WRITE
from capstone.x86 import X86_OP_MEM,X86_OP_IMM
A=Path.home()/'.codex/artifact-archives/god2-server/20261012'
D=A/'tw-native-petegg-list-address-candidates-333'
D.mkdir(exist_ok=False)
I=A/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
sha=lambda b:hashlib.sha256(b).hexdigest()
image=(I/'native-image.bin').read_bytes();original=(I/'originalPE.bin').read_bytes()
if sha(image)!='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763' or sha(original)!='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde':
    raise ValueError('Native pin differs')
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
rows=[]
for va in range(0x4d4b80,0x4dc900):
    ins=next(md.disasm(image[va-0x400000:va-0x400000+15],va,count=1),None)
    if ins is None:continue
    reasons=[]
    for op in ins.operands:
        if op.type==X86_OP_MEM and op.mem.disp==0xa and ((op.access&CS_AC_WRITE) or ins.mnemonic=='lea'):
            reasons.append(dict(kind='EXPLICIT_DISP_0A',base=md.reg_name(op.mem.base),
                                index=md.reg_name(op.mem.index),scale=op.mem.scale,
                                access=op.access,width=op.size))
        if op.type==X86_OP_IMM and op.imm==0xa and ins.mnemonic=='add':
            reasons.append(dict(kind='ADD_0A_RAW_CANDIDATE'))
    if reasons:
        raw=bytes(ins.bytes);off=pe.get_offset_from_rva(va-0x400000)
        if raw!=original[off:off+len(raw)]:raise ValueError('PE candidate differs')
        rows.append(dict(va=f'{va:08X}',bytes=raw.hex(),mnemonic=ins.mnemonic,
                         operands=ins.op_str,reasons=reasons,original_PE_offset=off,PE_equal=True))
value=dict(scope='RAW_EVERY_BYTE_CANDIDATES_ONLY_NOT_ALIGNED_CFG_OR_CONTEXT_ALIAS_PROOF',
           begin='004D4B80',end_exclusive='004DC900',all_register_bases=True,
           includes_indexed_displacement=True,includes_add_immediate_0A=True,
           computed_alias_writers_and_outside_range_open=True,candidates=rows,
           inputs=[dict(path=(I/n).as_posix(),bytes=len(b),sha256=sha(b),copied=False)
                   for n,b in [('native-image.bin',image),('originalPE.bin',original)]],
           new_opcodes=0,new_complete_routes=0,builds=0,tests=0,runtime=False,
           resource_codec=False,game_database_SQL=False,deploy=False)
with (D/'candidates.json').open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(value,indent=2)+'\n')
(D/'census-list-address333.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(root=D.as_posix(),candidates=len(rows),rows=rows)))
