from pathlib import Path
import hashlib,json,struct
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
D=Path(__file__).resolve().parent;U=D.parent/'round359-cn-custom-skill-action3-source';P=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
raw=P.read_bytes();assert sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
def at(va,size):
 off=pe.get_offset_from_rva(va-base);b=raw[off:off+size];assert len(b)==size;return b
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;lo=0x5634e0;end=0x563c19;b=at(lo,end-lo);ins=list(md.disasm(b,lo));assert len(b)==1849 and sum(i.size for i in ins)==len(b) and ins[0].bytes==b'\x55' and ins[-1].address==0x563c16 and ins[-1].mnemonic=='ret' and ins[-1].op_str=='0x20'
assert b[:664]==(U/'delta-partial/5634e0-entry-prefix.bin').read_bytes()
by={i.address:i for i in ins};targets=list(struct.unpack('<9I',at(0x563c1c,36)));assert all(t in by for t in targets)
branches=[];calls=[];pending=[lo];seen=set()
for i in ins:
 if i.mnemonic.startswith('j') and i.op_str.startswith('0x'):
  t=int(i.op_str,16);assert t in by;branches.append(dict(va=f'{i.address:08X}',target=f'{t:08X}'))
 if i.mnemonic=='call':calls.append(dict(va=f'{i.address:08X}',target=i.op_str,opaque=True))
while pending:
 va=pending.pop()
 if va in seen:continue
 assert va in by;seen.add(va);i=by[va]
 if i.mnemonic.startswith('ret'):continue
 if i.mnemonic=='jmp':
  if i.op_str.startswith('0x'):pending.append(int(i.op_str,16))
  else:assert i.address==0x563771 and i.op_str=='dword ptr [eax*4 + 0x563c1c]';pending.extend(targets)
 elif i.mnemonic.startswith('j'):pending.extend([int(i.op_str,16),va+i.size])
 else:pending.append(va+i.size)
assert len([i for i in ins if i.mnemonic.startswith('ret')])==1
put('qualified/5634e0-full-code.bin',b);put('qualified/5634e0-full-code.tsv',('va\thex\tmnemonic\toperands\treachable\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\t{int(i.address in seen)}\n' for i in ins)).encode())
put('qualified/switch9-targets.bin',at(0x563c1c,36));put('qualified/after-ret-padding.bin',at(0x563c19,3));put('qualified/next-authentic-entry-prefix.bin',at(0x563c40,17));assert at(0x563c40,3)==b'\x55\x8b\xec'
refs=[]
for rel in ['qualified/54c510-full-code.bin','qualified/54c510-full-code.tsv','child-qualified/556d40-full-code.bin','child-qualified/556d40-full-code.tsv','child-qualified/55e2f0-full-code.bin','child-qualified/556d40-target-table.bin','child-qualified/556d40-selector-table.bin','delta-partial/5634e0-entry-prefix.bin','delta-partial/5634e0-entry-prefix.tsv']:
 q=U/rel;bb=q.read_bytes();refs.append(dict(actual_path=q.as_posix(),bytes=len(bb),sha256=sha(bb),copied=False))
put('upstream-source-references.json',(json.dumps(refs,indent=2)+'\n').encode())
# Three actual aligned parent CALL spans; direct instructions are from already sealed complete parent.
parent=U/'child-qualified/556d40-full-code.tsv';lines=parent.read_text().splitlines()
selected=[line for line in lines[1:] if any(a<=int(line.split('\t')[0],16)<z for a,z in [(0x556e76,0x556e97),(0x557060,0x557084),(0x55713e,0x557160)])]
for line in selected:
 va,h,mn,op=line.split('\t');assert at(int(va,16),len(bytes.fromhex(h)))==bytes.fromhex(h)
put('actual-parent-three-call-excerpts.tsv',('va\thex\tmnemonic\toperands\n'+'\n'.join(selected)+'\n').encode())
t=struct.unpack('<14I',(U/'child-qualified/556d40-target-table.bin').read_bytes());selector=(U/'child-qualified/556d40-selector-table.bin').read_bytes();actions={str(i+1):f'{t[x]:08X}' for i,x in enumerate(selector)};assert actions['3']==actions['23']=='00556F7B' and actions['17']=='005573CE'
put('qualified-boundary-and-CFG.json',(json.dumps(dict(authentic_entry=f'{lo:08X}',end_exclusive=f'{end:08X}',whole_function=True,code_bytes=len(b),sites=len(ins),reachable_sites=len(seen),RET=[dict(va='00563C16',cleanup_bytes=32)],branches=branches,switch=dict(site='00563771',table='00563C1C',targets=[f'{t:08X}' for t in targets],bytes=36),padding_bytes=3,next_entry='00563C40',opaque_calls=calls,known_method_credit=0,global_method_novelty_claim=False,original_PE_only=True,independent_mapped_memory_proof=False,old_partial_overlap_bytes=664,new_body_extension_bytes=len(b)-664,action_table=actions),indent=2)+'\n').encode())
# All direct memory destinations, excluding comparison/test/read-only instructions.
stores=[dict(va=f'{i.address:08X}',hex=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in ins if i.op_str.split(',')[0].strip().endswith(']') and i.mnemonic in {'mov','add','sub','inc','dec','and','or','xor'}]
put('direct-memory-destination-inventory.json',(json.dumps(stores,indent=2)+'\n').encode())
assert sha(P.read_bytes())==PIN
print(json.dumps(dict(code_bytes=len(b),sites=len(ins),reachable_sites=len(seen),data_bytes=36,padding_bytes=3,extension_bytes=len(b)-664,calls=len(calls),direct_memory_destinations=len(stores))))
