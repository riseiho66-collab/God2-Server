from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
D=Path(__file__).resolve().parent;R=Path('C:/Users/risei/Desktop/God2/God2-Server');P=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
raw=P.read_bytes();assert sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
def at(va,size):return raw[pe.get_offset_from_rva(va-base):pe.get_offset_from_rva(va-base)+size]
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True
lo=0x54c510;hi=0x54cbb3;b=at(lo,hi-lo);ins=list(md.disasm(b,lo));assert sum(i.size for i in ins)==len(b) and ins[-1].mnemonic=='ret' and ins[-1].op_str=='4'
starts={i.address for i in ins};targets=list(struct.unpack('<8I',at(0x54cbb4,32)));selector=list(at(0x54cbd4,23));assert max(selector)<len(targets)
for t in targets:assert t in starts
branches=[]
for i in ins:
 if i.mnemonic.startswith('j') and i.op_str.startswith('0x'):
  t=int(i.op_str,16);assert t in starts;(branches.append({'site':f'{i.address:08X}','target':f'{t:08X}'}))
# Finite aligned CFG only: calls are opaque, single actual switch has complete eight target cells.
by={i.address:i for i in ins};pending=[lo];seen=set()
while pending:
 va=pending.pop()
 if va in seen:continue
 i=by[va];seen.add(va)
 if i.mnemonic.startswith('ret'):continue
 if i.mnemonic=='jmp':
  if i.op_str.startswith('0x'):pending.append(int(i.op_str,16))
  else:
   assert va==0x54c681 and i.op_str=='dword ptr [eax*4 + 0x54cbb4]';pending.extend(targets)
 elif i.mnemonic.startswith('j'):
  pending.extend([int(i.op_str,16),va+i.size])
 else:pending.append(va+i.size)
assert seen<=starts
tsv='va\thex\tmnemonic\toperands\treachable\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\t{int(i.address in seen)}\n' for i in ins)
put('qualified/54c510-full-code.bin',b);put('qualified/54c510-full-code.tsv',tsv.encode());put('qualified/54c510-target-table.bin',at(0x54cbb4,32));put('qualified/54c510-selector-table.bin',at(0x54cbd4,23))
# Caller exact pinned bytes at the authentic retained dispatcher instructions.
caller=at(0x55202d,0x552080-0x55202d);ci=list(md.disasm(caller,0x55202d));assert sum(i.size for i in ci)==len(caller)
assert next(i for i in ci if i.address==0x55205e).op_str=='0x54c510'
old=R/'artifacts/integration/packet-connections-20261006/cn-battle-deferred-consumer-01/native/00551d50-cfg.asm';oldb=old.read_bytes()
for i in ci:assert any(l.startswith(f'{i.address:08x} {i.bytes.hex()}'.encode()) for l in oldb.splitlines())
put('qualified/actual-55202d-caller.bin',caller);put('qualified/actual-55202d-caller.tsv',('va\thex\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ci)).encode())
v={'image':{'path':str(P),'bytes':len(raw),'sha256':PIN,'base':f'{base:08X}','copied':False,'independent_mapped_memory_proof':False},'complete_own_body':{'entry':f'{lo:08X}','end_exclusive':f'{hi:08X}','bytes':len(b),'sha256':sha(b),'sites':len(ins),'reachable_sites':len(seen),'reachable_code_bytes':sum(i.size for i in ins if i.address in seen),'linear_unreachable_instruction_bytes':sum(i.size for i in ins if i.address not in seen),'all_returns':[{'va':f'{i.address:08X}','operands':i.op_str} for i in ins if i.mnemonic.startswith('ret')],'direct_branches':branches,'opaque_calls':[{'va':f'{i.address:08X}','target':i.op_str} for i in ins if i.mnemonic=='call']},'tables':{'target_va':'0054CBB4','target_bytes':32,'targets':[f'{t:08X}' for t in targets],'selector_va':'0054CBD4','selector_bytes':23,'selector':selector},'actual_caller':{'entry':'00551D50','cut_start':'0055202D','cut_end_exclusive':'00552080','bytes':len(caller),'old_exact_asm_path':str(old),'old_exact_asm_sha256':sha(oldb),'instruction_bytes_equal':True,'argument':'full logical record EBX pushed; ECX same ESI main; CALL55205E'},'limits':'All children opaque; old metadata1267 is not contiguous extent; complete own body authentic CFG/switch only; known method credit0'}
put('qualified/body-boundary-proof.json',(json.dumps(v,indent=2)+'\n').encode());assert sha(P.read_bytes())==PIN
print(json.dumps({'full_body_bytes':len(b),'sites':len(ins),'reachable':len(seen),'RET':v['complete_own_body']['all_returns'],'tables_bytes':55,'caller_bytes':len(caller)}))
