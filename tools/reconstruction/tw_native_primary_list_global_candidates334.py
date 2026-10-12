from pathlib import Path
import hashlib,json,time
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_AC_WRITE
from capstone.x86 import X86_OP_MEM,X86_OP_IMM
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-petegg-global-list-write-source-334')
INPUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry')
sha=lambda b:hashlib.sha256(b).hexdigest()
image=(INPUT/'native-image.bin').read_bytes();original=(INPUT/'originalPE.bin').read_bytes()
if sha(image)!='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763' or sha(original)!='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde':raise RuntimeError('Native pin drift')
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
sections=[];rows=[];decoded=0;started=time.monotonic()
for section in pe.sections:
 if section.Name.rstrip(b'\x00')!=b'.text':continue
 start=section.VirtualAddress;size=min(section.Misc_VirtualSize,section.SizeOfRawData);end=start+size
 native=image[start:end];off=section.PointerToRawData
 if native!=original[off:off+size]:raise RuntimeError('Executable mapped/PE whole span drift')
 sections.append(dict(name=section.Name.hex(),start_va=f'{start+0x400000:08X}',end_exclusive=f'{end+0x400000:08X}',bytes=size,original_pe_offset=off,PE_equal=True,sha256=sha(native)))
 for rva in range(start,end):
  # Every byte is a candidate entry, never aligned fullCFG proof.
  ins=next(md.disasm(image[rva:min(rva+15,end)],rva+0x400000,count=1),None)
  if ins is None:continue
  decoded+=1;reasons=[]
  for operand in ins.operands:
   if operand.type==X86_OP_MEM and operand.mem.disp in (0xa,0xa7f2f76) and ((operand.access&CS_AC_WRITE) or ins.mnemonic=='lea'):
    reasons.append(dict(kind='EXPLICIT_DISP_0A' if operand.mem.disp==0xa else 'PRIMARY_RELATIVE_OFFSET_PLUS_0A',base=md.reg_name(operand.mem.base),index=md.reg_name(operand.mem.index),scale=operand.mem.scale,access=operand.access,width=operand.size))
   if operand.type==X86_OP_IMM and ins.mnemonic=='add' and operand.imm in (0xa,0xa7f2f76):
    reasons.append(dict(kind='ADD_0A' if operand.imm==0xa else 'ADD_PRIMARY_OFFSET_PLUS_0A'))
  if reasons:
   raw=bytes(ins.bytes);peoff=pe.get_offset_from_rva(rva)
   if original[peoff:peoff+len(raw)]!=raw:raise RuntimeError('Candidate PE drift')
   rows.append(dict(va=f'{ins.address:08X}',bytes=raw.hex(),mnemonic=ins.mnemonic,operands=ins.op_str,reasons=reasons,original_pe_offset=peoff,PE_equal=True))
value=dict(scope='RAW_EVERY_NAMED_TEXT_BYTE_CANDIDATES_PE_FLAGS_NOT_EXECUTABLE_NOT_ALIGNED_CFG_OR_CONTEXT_ALIAS',sections=sections,decoded_candidates=decoded,exec_bytes=sum(s['bytes'] for s in sections),all_register_bases=True,indexed_forms=True,primary_offset_plus0a_forms=True,computed_aliases_indirect_nonexec_and_unrepresented_absolute_primary_pointers_open=True,candidates=rows,inputs=[dict(path=str(INPUT/n),bytes=len(raw),sha256=sha(raw),copied=False) for n,raw in [('native-image.bin',image),('originalPE.bin',original)]],new_complete_routes=0,global_game_absence_claim=False)
with (OUT/'named-text-explicit-candidates.json').open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(value,indent=2)+'\n')
with (OUT/'named-text-explicit-candidates.tsv').open('x',encoding='utf8',newline='\n') as f:
 f.write('va\tbytes\tmnemonic\toperands\treasons\n')
 for row in rows:f.write('\t'.join([row['va'],row['bytes'],row['mnemonic'],row['operands'],','.join(r['kind'] for r in row['reasons'])])+'\n')
print(json.dumps(dict(sections=sections,exec_bytes=value['exec_bytes'],decoded=decoded,raw_candidates=len(rows),elapsed_seconds=round(time.monotonic()-started,3))))
