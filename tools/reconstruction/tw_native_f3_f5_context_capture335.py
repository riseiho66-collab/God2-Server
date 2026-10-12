from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-f3-f5-list-adjacency-source-335')
INPUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry')
sha=lambda b:hashlib.sha256(b).hexdigest()
image=(INPUT/'native-image.bin').read_bytes();original=(INPUT/'originalPE.bin').read_bytes()
assert sha(image)=='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763'
assert sha(original)=='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde'
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32)
target=OUT/'native-final';target.mkdir(exist_ok=False);cuts=[];flow={}
def cut(name,va,end,code,scope):
 raw=image[va-0x400000:end-0x400000];off=pe.get_offset_from_rva(va-0x400000);assert raw==original[off:off+len(raw)]
 rows=list(md.disasm(raw,va)) if code else []
 if code:assert sum(r.size for r in rows)==len(raw)
 (target/(name+'.bin')).write_bytes(raw)
 if code:(target/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+''.join(f'{r.address:08X}\t{r.bytes.hex()}\t{r.mnemonic}\t{r.op_str}\n' for r in rows),encoding='utf8',newline='\n')
 cuts.append(dict(name=name,va=f'{va:08X}',end_exclusive=f'{end:08X}',bytes=len(raw),code=code,instruction_sites=len(rows),original_pe_offset=off,original_pe_equal=True,sha256=sha(raw),scope=scope));return rows
cut('world-jump-selection',0x468b61,0x468b68,True,'Actual indexedWORLDtable reference only, historical parent')
cut('length-jump-selection',0x401204,0x401216,True,'Actual indexedlengthtable domain/reference only, historical parent')
for op,case,leaf,receiver,end,rets,padend in [(0xf3,0x469112,0x401318,0x4ce290,0x4ce4f2,[0x4ce4ef],0x4ce500),(0xf5,0x469100,0x4012fa,0x4ce140,0x4ce285,[0x4ce262,0x4ce282],0x4ce290)]:
 name=f'f{op&15}'
 assert struct.unpack_from('<I',image,0x6b5d4+4*op)[0]==case
 assert struct.unpack_from('<I',image,0x1324+4*op)[0]==leaf
 cell=0x46b5d4+4*op;cut(name+'-world-cell',cell,cell+4,False,'Selectedactual opcodecell')
 case_rows=cut(name+'-world-case',case,case+18,True,'Complete selectedcase, opcodeINC EBX/bodyformal andprimaryECX Main+A7F2F6C')
 assert [r.mnemonic for r in case_rows]==['inc','lea','push','call','jmp']
 assert case_rows[3].op_str==hex(receiver)
 cell=0x401324+4*op;cut(name+'-length-cell',cell,cell+4,False,'Selectedactual opcode lengthcell')
 leafrows=cut(name+'-length-leaf-complete',leaf,leaf+6,True,'Full leaf; F3 -2 variablemarker, F5 fixed29')
 assert image[leaf-0x400000:leaf-0x400000+6]==bytes.fromhex('b8feffffffc3' if op==0xf3 else 'b81d000000c3')
 rows=cut(name+'-receiver-complete',receiver,end,True,'Complete directreceiver only; nativeUI descendantsopaque; nofinalpoststate/rulesclaim')
 sites={r.address for r in rows};actualrets=[r.address for r in rows if r.mnemonic=='ret'];assert actualrets==rets
 jumps=[];calls=[]
 for r in rows:
  if r.mnemonic.startswith('j'):
   dest=int(r.op_str,16);assert dest in sites;jumps.append(dict(va=f'{r.address:08X}',target=f'{dest:08X}',kind=r.mnemonic))
  if r.mnemonic=='call':calls.append(dict(va=f'{r.address:08X}',target=r.op_str,scope='Opaque child; actual formal/rootargs in full TSV, nofinaleffectclaim'))
 flow[name]=dict(entry=f'{receiver:08X}',end_exclusive=f'{end:08X}',rets=[dict(va=f'{r.address:08X}',pop=r.op_str) for r in rows if r.mnemonic=='ret'],jumps=jumps,opaque_calls=calls)
 cut(name+'-padding-after',end,padend,False,'Raw boundary padding only')
(target/'cuts.json').write_text(json.dumps(cuts,indent=2)+'\n',encoding='utf8',newline='\n')
(target/'control-flow.json').write_text(json.dumps(flow,indent=2)+'\n',encoding='utf8',newline='\n')
inputs=[dict(path=str(INPUT/n),bytes=len(b),sha256=sha(b),copied=False) for n,b in [('native-image.bin',image),('originalPE.bin',original)]]
base=INPUT.parent.parent
for folder,names in [('tw-native-petegg-global-list-write-source-334',['seal.json','REPORT.md','native-final/f4-array-word-receiver-complete.bin']),('tw-native-petegg-e7-list-input-source-331',['seal.json','native/list-array-zero-initializer-complete.bin']),('tw-native-petegg-alternative-actions-source-330',['seal.json','native/alternative23-open-complete.bin','native/alternative23-action-complete.bin'])]:
 for name in names:
  p=base/folder/name;raw=p.read_bytes();inputs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),copied=False,scope='Selected prior sameU arraycontext; no fullclosure reaudit'))
(OUT/'input-references.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf8',newline='\n')
sources=[]
for rel in ['AGENTS.md','docs/GOAL_ACCEPTANCE.md','docs/research/tw-native-petegg-e7-list-source-20261012.md','docs/research/tw-native-petegg-deferred-b1-source-20261012.md']:
 p=Path('C:/Users/risei/Desktop/God2/God2-Server')/rel;raw=p.read_bytes();dest=OUT/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);sources.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),retained=str(dest.relative_to(OUT))))
(OUT/'source-references.json').write_text(json.dumps(sources,indent=2)+'\n',encoding='utf8',newline='\n')
metrics=dict(final_cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts if c['code']),data_bytes=sum(c['bytes'] for c in cuts if not c['code']),instruction_sites=sum(c['instruction_sites'] for c in cuts),f3_receiver_bytes=0x4ce4f2-0x4ce290,f5_receiver_bytes=0x4ce285-0x4ce140,f3_rets=1,f5_rets=2,f3_length_marker=-2,f3_fixed_logical_length=None,f5_logical_bytes=29,f5_body_bytes=28,same_primary_U=True,direct_low_U8_U0A_U3A_U3C_effect=False,children_opened=0,new_opcodes=0,new_complete_routes=0,runtime_gameplay_count=0,denominator=None,completion_percent=None)
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(metrics))
