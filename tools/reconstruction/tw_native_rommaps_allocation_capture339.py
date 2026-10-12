from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_GRP_CALL,CS_GRP_JUMP,CS_GRP_RET

OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-rommaps-loader-source-339')
PIN=OUT.parent/'tw-native-entry-body-alias-and-remote-opaque-315/native-entry'
image=(PIN/'native-image.bin').read_bytes();original=(PIN/'originalPE.bin').read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
start=0x547e23;end=0x547eb0;raw=image[start-0x400000:end-0x400000]
off=pe.get_offset_from_rva(start-0x400000);assert raw==original[off:off+len(raw)]
ins=list(md.disasm(raw,start));assert sum(i.size for i in ins)==len(raw)
branches=[dict(va=f'{i.address:08X}',mnemonic=i.mnemonic,target=i.op_str) for i in ins if i.group(CS_GRP_JUMP)]
returns=[dict(va=f'{i.address:08X}',operands=i.op_str) for i in ins if i.group(CS_GRP_RET)]
assert returns==[dict(va='00547EAB',operands='')]
assert all(start<=int(branch['target'],16)<end for branch in branches)
assert ins[-1].mnemonic=='jmp' and ins[-1].op_str=='0x547ea8'
imports=[dict(dll=d.dll.decode('ascii'),name=(s.name or b'').decode('ascii'),iat_va=f'{s.address:08X}') for d in pe.DIRECTORY_ENTRY_IMPORT for s in d.imports if s.address==0x570398]
assert len(imports)==1
native=OUT/'native'
(native/'allocation-helper-complete-with-cold-tail.bin').write_bytes(raw)
tsv='va\tbytes\tmnemonic\toperands\n'+'\n'.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}' for i in ins)+'\n'
(native/'allocation-helper-complete-with-cold-tail.tsv').write_text(tsv,encoding='utf8',newline='\n')
record=dict(name='allocation-helper-complete-with-cold-tail',start_va=f'{start:08X}',end_exclusive_va=f'{end:08X}',bytes=len(raw),sha256=sha(raw),original_pe_offset=off,mapped_equal=True,original_pe_equal=True,returns=returns,cold_tail='547EAC..547EB0 is reachable and JMPs547EA8; do not stop after RET547EAB',branches=branches,calls=[dict(va=f'{i.address:08X}',target=i.op_str) for i in ins if i.group(CS_GRP_CALL)],selected_iat_import=imports,scope='Complete actual direct547E23 allocation helper; callees opaque, no allocation execution or API call')
(OUT/'allocation-helper-cut.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(bytes=len(raw),sha256=sha(raw),imports=imports,returns=returns)))
