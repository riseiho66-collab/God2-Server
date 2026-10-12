from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
OUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-9c-list-input-source-333')
INPUT=Path('C:/Users/risei/.codex/artifact-archives/god2-server/20261012/tw-native-entry-body-alias-and-remote-opaque-315/native-entry')
SERVER=Path('C:/Users/risei/Desktop/God2/God2-Server')
sha=lambda b:hashlib.sha256(b).hexdigest()
image=(INPUT/'native-image.bin').read_bytes();original=(INPUT/'originalPE.bin').read_bytes()
if sha(image)!='149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763' or sha(original)!='5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde':raise RuntimeError('native input drift')
pe=pefile.PE(data=original);md=Cs(CS_ARCH_X86,CS_MODE_32);target=OUT/'native-final-v2';target.mkdir(exist_ok=False);cuts=[]
def cut(name,va,end,scope,code=True):
 raw=image[va-0x400000:end-0x400000];off=pe.get_offset_from_rva(va-0x400000)
 if original[off:off+len(raw)]!=raw:raise RuntimeError('PE range mismatch')
 rows=list(md.disasm(raw,va)) if code else []
 if code and sum(i.size for i in rows)!=len(raw):raise RuntimeError('static decode incomplete')
 (target/(name+'.bin')).write_bytes(raw)
 if code:(target/(name+'.tsv')).write_text('va\tbytes\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in rows),encoding='utf8')
 cuts.append(dict(name=name,va=f'{va:08X}',end_exclusive=f'{end:08X}',bytes=len(raw),code=code,instruction_sites=len(rows),sha256=sha(raw),original_pe_offset=off,original_pe_equal=True,scope=scope));return rows
worldcell=0x46b5d4+4*0x9c;lengthcell=0x401324+4*0x9c
if struct.unpack_from('<I',image,worldcell-0x400000)[0]!=0x468c8c or struct.unpack_from('<I',image,lengthcell-0x400000)[0]!=0x401276:raise RuntimeError('9C actualcells mismatch')
cut('9c-world-jump-selection',0x468b61,0x468b68,'Needed actual opcode indexed jump boundary; no whole WORLD qualification')
cut('9c-world-cell',worldcell,worldcell+4,'Actual selected9C cell from qualified WORLD table index9C',False)
cut('9c-world-case',0x468c8c,0x468c9e,'Actual opcode skip, same primaryUI=this and bodyarg call to4F34C0')
cut('9c-length-jump-selection',0x401204,0x401216,'Needed actual lengthswitch upperbound and indexedjump')
cut('9c-length-cell',lengthcell,lengthcell+4,'Actual selected9C length cell',False)
cut('9c-length-leaf-complete',0x401276,0x40127c,'Complete lengthleaf logical49, RET')
rows=cut('9c-receiver-complete',0x4f34c0,0x4f3741,'Full actual receiver, negativehandle earlygate/commonRET4, all direct bodyreads and UI formatting calls; descendantsopaque')
addr={i.address for i in rows};jumps=[];calls=[]
for i in rows:
 if i.mnemonic.startswith('j'):
  dest=int(i.op_str,16)
  if dest not in addr:raise RuntimeError('directjump outsidefullreceiver')
  jumps.append(dict(va=f'{i.address:08X}',target=f'{dest:08X}',kind=i.mnemonic))
 if i.mnemonic=='call':calls.append(dict(va=f'{i.address:08X}',target=i.op_str,scope='Opaque child only'))
rets=[dict(va=f'{i.address:08X}',pop=i.op_str) for i in rows if i.mnemonic=='ret']
if rets!=[dict(va='004F373E',pop='4')]:raise RuntimeError('RET inventory mismatch')
(target/'control-flow.json').write_text(json.dumps(dict(rets=rets,jumps=jumps,opaque_calls=calls),indent=2)+'\n')
cut('boundary-receiver-before',0x4f34b0,0x4f34c0,'Raw neighboring boundary only, no other opcode/method qualification',False)
cut('boundary-receiver-after',0x4f3741,0x4f3750,'Raw padding; next4F3750 remainsopaque',False)
formats=[]
for name,va in [('literal-format595238',0x595238),('literal-format5823B4',0x5823b4)]:
 rva=va-0x400000;span=image[rva:rva+64];pos=span.find(b'\x00')
 if pos<0:raise RuntimeError('bounded literal notterminated')
 cut(name,va,va+pos+1,'Exact native literal NULterminated within64B; bytes only no client codec',False)
 formats.append(dict(va=f'{va:08X}',raw_hex=span[:pos+1].hex()))
cut('9c-pointer-array9',0x5b8630,0x5b8654,'Actual9 DWORD pointer table for body2C/2D<9; values do not establish fulltransitively renderedstrings',False)
(target/'format-constants.json').write_text(json.dumps(dict(literals=formats,pointer_values=[f'{v:08X}' for v in struct.unpack_from('<9I',image,0x5b8630-0x400000)]),indent=2)+'\n')
refs=[dict(path=str(INPUT/n),bytes=len(b),sha256=sha(b),copied=False) for n,b in [('native-image.bin',image),('originalPE.bin',original)]]
for rel in ['artifacts/integration/packet-connections-20261006/s2c-world-consumer-frontier-v21.json','tools/strike_lab/current_protocol_coverage.py']:
 p=SERVER/rel;raw=p.read_bytes();refs.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),copied=False,scope='Selected tableaddress/source shape reference; this script not executed'))
(target/'input-references.json').write_text(json.dumps(refs,indent=2)+'\n')
(target/'cuts.json').write_text(json.dumps(cuts,indent=2)+'\n')
sources=[]
for n in ['AGENTS.md','docs/GOAL_ACCEPTANCE.md','docs/research/tw-native-petegg-e7-list-source-20261012.md','docs/research/tw-native-petegg-event-control-source-20261012.md']:
 p=SERVER/n
 if not p.exists():continue
 raw=p.read_bytes();dest=OUT/'source'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);sources.append(dict(path=str(p),bytes=len(raw),sha256=sha(raw),retained=str(dest.relative_to(OUT))))
(OUT/'source-references.json').write_text(json.dumps(sources,indent=2)+'\n')
metrics=dict(cuts=len(cuts),code_bytes=sum(c['bytes'] for c in cuts if c['code']),data_bytes=sum(c['bytes'] for c in cuts if not c['code']),instruction_sites=sum(c['instruction_sites'] for c in cuts),full_receiver_bytes=0x4f3741-0x4f34c0,receiver_ret_count=1,native_child_methods_opened=0,all_final_cuts_pe_equal=True,body_bytes=48,logical_bytes=49,actual_u0a_copy_found=False,semantic_list_recovery=False,global_native_new_coverage_claim=False,whole_denominator=None,completion_percent=None,new_complete_routes=0)
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');print(json.dumps(metrics));print(json.dumps(formats))
