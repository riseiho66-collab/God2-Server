from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
D=Path(__file__).resolve().parent;P=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
raw=P.read_bytes();assert sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase;md=Cs(CS_ARCH_X86,CS_MODE_32)
def at(va,size):
 off=pe.get_offset_from_rva(va-base);return raw[off:off+size]
refs=[]
extra_targets=[]
for table_name,va,size in [('556d40-nested-target-table',0x557444,20),('556d40-nested-selector-table',0x557458,21)]:
 data_raw=at(va,size);put('child-qualified/'+table_name+'.bin',data_raw)
 if size==20:extra_targets=list(struct.unpack('<5I',data_raw))
 else:assert max(data_raw)<5
for name,lo,hi,sw in [('556d40',0x556d40,0x5573f1,(0x556e33,0x5573f4,14,0x55742c,23)),('55e2f0',0x55e2f0,0x55e336,None)]:
 b=at(lo,hi-lo);ins=list(md.disasm(b,lo));assert sum(i.size for i in ins)==len(b) and ins[-1].mnemonic.startswith('ret');by={i.address:i for i in ins};targets=[];data=[]
 if sw:
  site,tva,count,sva,scount=sw;tb=at(tva,count*4);sb=at(sva,scount);targets=list(struct.unpack('<'+'I'*count,tb));assert max(sb)<count
  for t in targets:assert t in by
  put('child-qualified/'+name+'-target-table.bin',tb);put('child-qualified/'+name+'-selector-table.bin',sb);data=[{'va':f'{tva:08X}','bytes':len(tb),'targets':[f'{t:08X}' for t in targets]},{'va':f'{sva:08X}','bytes':len(sb),'selector':list(sb)}]
 for i in ins:
  if i.mnemonic.startswith('j') and i.op_str.startswith('0x'):assert int(i.op_str,16) in by
 seen=set();pending=[lo]
 while pending:
  va=pending.pop()
  if va in seen:continue
  i=by[va];seen.add(va)
  if i.mnemonic.startswith('ret'):continue
  if i.mnemonic=='jmp':
   if i.op_str.startswith('0x'):pending.append(int(i.op_str,16))
   else:
    if sw and va==sw[0]:pending.extend(targets)
    else:assert sw and va==0x5572eb;pending.extend(extra_targets)
  elif i.mnemonic.startswith('j'):pending.extend([int(i.op_str,16),va+i.size])
  else:pending.append(va+i.size)
 assert len(seen)==len(ins)
 put('child-qualified/'+name+'-full-code.bin',b);put('child-qualified/'+name+'-full-code.tsv',('va\thex\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode())
 refs.append({'entry':f'{lo:08X}','end_exclusive':f'{hi:08X}','bytes':len(b),'sha256':sha(b),'sites':len(ins),'all_reachable':True,'all_returns':[{'va':f'{i.address:08X}','operands':i.op_str} for i in ins if i.mnemonic.startswith('ret')],'opaque_calls':[{'va':f'{i.address:08X}','target':i.op_str} for i in ins if i.mnemonic=='call'],'tables':data,'known_method_credit':0})
# Exact direct parent input lineage and padding only, no invented functions.
parent=at(0x551f91,0x552080-0x551f91);pi=list(md.disasm(parent,0x551f91));assert sum(i.size for i in pi)==len(parent)
put('qualified/actual-551f91-parent-lineage.bin',parent);put('qualified/actual-551f91-parent-lineage.tsv',('va\thex\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in pi)).encode())
for name,va,size in [('54c510-padding',0x54cbb3,1),('556d40-padding',0x5573f1,3)]:put('child-qualified/'+name+'.bin',at(va,size))
put('qualified/child-boundary-proof.json',(json.dumps({'image':{'path':str(P),'sha256':PIN,'bytes':len(raw),'copied':False,'independent_mapped_memory_proof':False},'bodies':refs,'parent':{'start':'00551F91','end_exclusive':'00552080','bytes':len(parent),'sha256':sha(parent),'overlaps_prior_caller83_bytes':83},'padding_bytes':4,'limits':'Only necessary delta and primitive mask children; every other callee opaque. Known native-method/route credits0.'},indent=2)+'\n').encode());assert sha(P.read_bytes())==PIN
print(json.dumps({'bodies':[{'entry':v['entry'],'bytes':v['bytes'],'sites':v['sites']} for v in refs],'child_tables_bytes':120,'parent_bytes':len(parent)}))
