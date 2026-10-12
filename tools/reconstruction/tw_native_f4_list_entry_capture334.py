from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-petegg-global-list-write-source-334')
INPUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry')
SERVER=Path('C:/Users/risei/Desktop/God2/God2-Server')
sha=lambda b:hashlib.sha256(b).hexdigest()
image=(INPUT/'native-image.bin').read_bytes();original=(INPUT/'originalPE.bin').read_bytes()
if sha(image)!='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763' or sha(original)!='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde':raise RuntimeError('Pin drift')
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);target=OUT/'native-final';target.mkdir(exist_ok=False);cuts=[]
def cut(name,va,end,scope,code=True):
 raw=image[va-0x400000:end-0x400000];off=pe.get_offset_from_rva(va-0x400000)
 if raw!=original[off:off+len(raw)]:raise RuntimeError('PE span drift')
 rows=list(md.disasm(raw,va)) if code else []
 if code and sum(i.size for i in rows)!=len(raw):raise RuntimeError('Decode incomplete')
 (target/(name+'.bin')).write_bytes(raw)
 if code:(target/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in rows),encoding='utf8',newline='\n')
 cuts.append(dict(name=name,va=f'{va:08X}',end_exclusive=f'{end:08X}',bytes=len(raw),code=code,instruction_sites=len(rows),sha256=sha(raw),original_pe_offset=off,original_pe_equal=True,scope=scope));return rows
world=struct.unpack_from('<I',image,0x6b5d4+4*0xf4)[0];leaf=struct.unpack_from('<I',image,0x1324+4*0xf4)[0]
if world!=0x469233 or leaf!=0x4012ac:raise RuntimeError('F4 actual cell drift')
cut('f4-world-jump-selection',0x468b61,0x468b68,'Actual WORLDindexedjump table reference; not wholeWorld/recredit')
cut('f4-world-cell',0x46b9a4,0x46b9a8,'Actual F4 WORLDcell',False)
cut('f4-world-case',0x469233,0x469245,'Actual F4 opcode advance EBX; primaryECX Main+A7F2F6C; bodyformal to4A3380')
cut('f4-length-jump-selection',0x401204,0x401216,'Actual lengthdomain/indexedjump reference; historical')
cut('f4-length-cell',0x4016f4,0x4016f8,'Actual F4 lengthcell',False)
lengthrows=cut('f4-length-leaf-complete',0x4012ac,0x4012b2,'Complete actual MOV EAX5/RET lengthleaf')
if image[0x12ac:0x12b2]!=bytes.fromhex('b805000000c3'):raise RuntimeError('Logical F4 lengthnot5')
rows=cut('f4-array-word-receiver-complete',0x4a3380,0x4a33e8,'Full actual receiver, bodyindex<24 directWORD population sameprimaryU; outside diagnostics opaque; noownedID/rules')
addresses={r.address for r in rows};jumps=[];calls=[]
for ins in rows:
 if ins.mnemonic.startswith('j'):
  dest=int(ins.op_str,16)
  if dest not in addresses:raise RuntimeError('Jump exitscomplete receiver')
  jumps.append(dict(va=f'{ins.address:08X}',target=f'{dest:08X}',kind=ins.mnemonic))
 if ins.mnemonic=='call':calls.append(dict(va=f'{ins.address:08X}',target=ins.op_str,scope='Opaque diagnostics child, nofinalstate claim'))
rets=[dict(va=f'{i.address:08X}',pop=i.op_str) for i in rows if i.mnemonic=='ret']
if rets!=[dict(va='004A33D2',pop='4'),dict(va='004A33E5',pop='4')]:raise RuntimeError('RETinventory drift')
(target/'control-flow.json').write_text(json.dumps(dict(rets=rets,jumps=jumps,opaque_calls=calls),indent=2)+'\n',encoding='utf8',newline='\n')
cut('f4-boundary-before',0x4a3374,0x4a3380,'Raw precedingpadding only; adjacentfunction notqualified',False)
cut('f4-boundary-after',0x4a33e8,0x4a33f0,'Raw followingpadding only; adjacentfunction notqualified',False)
literals=[]
for name,va in [('diagnostic-source-file',0x591134),('diagnostic-index-assert',0x5911fc),('diagnostic-format',0x5911bc)]:
 raw=image[va-0x400000:va-0x400000+256];pos=raw.find(b'\x00')
 if pos<0:raise RuntimeError('Literal limit')
 cut(name,va,va+pos+1,'Actual referenced diagnosticliteral withterminator; originalnative naming only',False)
 literals.append(dict(va=f'{va:08X}',bytes_hex=raw[:pos+1].hex(),ascii=raw[:pos].decode('ascii')))
(target/'diagnostic-literals.json').write_text(json.dumps(literals,indent=2)+'\n',encoding='utf8',newline='\n')
refs=[]
for rva in range(0x1000,0x170000-4):
 if image[rva] in (0xe8,0xe9) and 0x400000+rva+5+struct.unpack_from('<i',image,rva+1)[0]==0x4a3380:
  refs.append(dict(va=f'{rva+0x400000:08X}',bytes=image[rva:rva+5].hex(),kind='CALL' if image[rva]==0xe8 else 'JMP',aligned_qualified=rva==0x6923b))
(OUT/'targeted-receiver-raw-references.json').write_text(json.dumps(dict(target='004A3380',scope='Only rawE8/E9 scans in named.text, noindirect/globalabsence',rows=refs),indent=2)+'\n',encoding='utf8',newline='\n')
headers=[dict(name=s.Name.hex(),rva=s.VirtualAddress,virtual_bytes=s.Misc_VirtualSize,raw_bytes=s.SizeOfRawData,characteristics=f'{s.Characteristics:08X}',execute_flag=bool(s.Characteristics&0x20000000)) for s in pe.sections]
(OUT/'original-pe-section-headers.json').write_text(json.dumps(headers,indent=2)+'\n',encoding='utf8',newline='\n')
(target/'cuts.json').write_text(json.dumps(cuts,indent=2)+'\n',encoding='utf8',newline='\n')
inputs=[dict(path=str(INPUT/n),bytes=len(b),sha256=sha(b),copied=False) for n,b in [('native-image.bin',image),('originalPE.bin',original)]]
prior=INPUT.parent.parent
for folder,names in [('tw-native-petegg-e7-list-input-source-331',['seal.json','native/list-array-zero-initializer-complete.bin','native/cuts.json']),('tw-native-petegg-alternative-actions-source-330',['seal.json','native/alternative23-open-complete.bin','native/alternative23-action-complete.bin']),('tw-native-petegg-list-address-candidates-333',['seal.json','candidates.json'])]:
 for name in names:
  p=prior/folder/name
  if not p.exists():continue
  raw=p.read_bytes();inputs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),copied=False,scope='Selected actualarray/reader/priorfinite scan reference, not wholeclosureaudit'))
(target/'input-references.json').write_text(json.dumps(inputs,indent=2)+'\n',encoding='utf8',newline='\n')
sources=[]
for rel in ['AGENTS.md','docs/GOAL_ACCEPTANCE.md','docs/research/tw-native-9c-and-petegg-list-boundaries-20261012.md','docs/research/tw-native-petegg-e7-list-source-20261012.md','docs/research/tw-native-petegg-deferred-b1-source-20261012.md']:
 p=SERVER/rel;raw=p.read_bytes();dest=OUT/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);sources.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),retained=str(dest.relative_to(OUT))))
(OUT/'source-references.json').write_text(json.dumps(sources,indent=2)+'\n',encoding='utf8',newline='\n')
metrics=dict(final_cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts if c['code']),data_bytes=sum(c['bytes'] for c in cuts if not c['code']),instruction_sites=sum(c['instruction_sites'] for c in cuts),full_receiver_bytes=104,receiver_rets=2,logical_bytes=5,body_bytes=4,same_primary_U_actual_writer=True,whole_uint16_value_preserved=True,raw_body_byte1_unread_directly=True,index_unsigned_max23=True,owned_item_identity_recovered=False,native_children_opened=0,global_native_coverage_claim=False,new_opcodes=0,new_complete_routes=0,denominator=None,completion_percent=None)
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(metrics))
