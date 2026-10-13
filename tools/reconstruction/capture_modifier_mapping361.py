from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
D=Path(__file__).resolve().parent;A=D.parent;U=A/'round360-cn-custom-skill-health-consumer-source';N=A/'round359-cn-custom-skill-action3-source';P=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
def out(n,v):put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
raw=P.read_bytes();assert sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
def at(va,size):
 off=pe.get_offset_from_rva(va-base);b=raw[off:off+size];assert len(b)==size;return b
lo=0x562510;end=0x5625a8;b=at(lo,end-lo);md=Cs(CS_ARCH_X86,CS_MODE_32);ins=list(md.disasm(b,lo));assert len(b)==152 and sum(i.size for i in ins)==152 and ins[0].bytes==b'\x55' and ins[-1].address==0x5625a5 and ins[-1].mnemonic=='ret' and ins[-1].op_str=='0x14';by={i.address:i for i in ins};pending=[lo];seen=set();branches=[]
for i in ins:
 if i.mnemonic.startswith('j'):
  assert i.op_str.startswith('0x');t=int(i.op_str,16);assert t in by;branches.append(dict(va=f'{i.address:08X}',target=f'{t:08X}'))
while pending:
 va=pending.pop()
 if va in seen:continue
 assert va in by;seen.add(va);i=by[va]
 if i.mnemonic.startswith('ret'):continue
 if i.mnemonic=='jmp':pending.append(int(i.op_str,16))
 elif i.mnemonic.startswith('j'):pending.extend([int(i.op_str,16),va+i.size])
 else:pending.append(va+i.size)
assert len(seen)==len(ins);assert len([i for i in ins if i.mnemonic.startswith('ret')])==1
put('qualified/562510-full-code.bin',b);put('qualified/562510-full-code.tsv',('va\thex\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode());put('qualified/after-ret-int3-padding.bin',at(end,8));assert at(end,8)==b'\xcc'*8;put('qualified/next-authentic-entry-prefix.bin',at(0x5625b0,6));assert at(0x5625b0,3)==b'\x55\x8b\xec'
first=at(0x7f6f40,13);second=at(0x7f6f50,67);put('qualified/formal3-map13.bin',first);put('qualified/formal4-map67.bin',second)
out('exact-BYTE-map-domain.json',dict(formal3=dict(table_VA='007F6F40',unsigned_lowBYTE_domain=list(range(13)),outputs=list(first),invalid_lowBYTE_default=15),formal4=dict(table_VA='007F6F50',unsigned_lowBYTE_domain=list(range(67)),outputs=list(second),invalid_lowBYTE_default=0),named_outcome_semantics_qualified=False))
# Reuse the immutable upstream parent only after exact saved reference/hash and current PE bytes.
parent=N/'child-qualified/556d40-full-code.tsv';ref=next(m for m in json.loads((U/'upstream-source-references.json').read_bytes()) if Path(m['actual_path']).resolve()==parent.resolve());pb=parent.read_bytes();assert len(pb)==ref['bytes'] and sha(pb)==ref['sha256'];selected=[line for line in pb.decode().splitlines()[1:] if 0x557084<=int(line.split('\t')[0],16)<0x5570a9]
for line in selected:
 va,h,mn,op=line.split('\t');assert at(int(va,16),len(bytes.fromhex(h)))==bytes.fromhex(h)
assert any(line.startswith('0055709E\t') and line.endswith('0x562510') for line in selected);put('actual-parent557084-5570a9-excerpt.tsv',('va\thex\tmnemonic\toperands\n'+'\n'.join(selected)+'\n').encode());out('needed-parent-source-reference.json',ref)
proof=dict(authentic_entry='00562510',end_exclusive='005625A8',whole_function=True,code_bytes=152,sites=len(ins),reachable_sites=len(seen),RET=dict(va='005625A5',pop_bytes=20),branches=branches,opaque_calls=[dict(va=f'{i.address:08X}',target=i.op_str) for i in ins if i.mnemonic=='call'],tables_bytes=80,padding_bytes=8,next_entry_witness_bytes=6,original_PE_sha256=PIN,independent_mapped_memory_proof=False,known_method_credit=0,new_route_credit=0)
out('qualified-boundary-and-call-proof.json',proof)
report=f"""# N361 original CN modifier mapping source

PASS bounded static closure. Despite the historical task directory name,562510 is not an actual queued-delta/HP reader. Authentic normal EBP entry562510 is reached by sealed parent55709E after5634E0. Whole code562510..5625A8 is152 bytes/{len(ins)} aligned sites, all{len(seen)} reached in the finite own CFG. The sole5625A5 RET14h cleans five DWORD formal cells. All{len(branches)} direct branches close on aligned own instructions; children are opaque. EightCC padding bytes and next5625B0 six-byte authentic prologue witness are not own code. Discovery3500 envelope includes later unrelated functions and is not credited whole code.

Original CN PE582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8 /47,541,760 bytes is hash-referenced in place only. No image copy or independent mapped-memory pair exists. All24 N360 members/113,578 bytes were individually verified before discovery, including unchanged1849-byte5634E0 source and its signed16 HP-labelled display limit. The parent excerpt is reused from already-known N359 whole556D40 TSV, checked against the saved N360 reference/hash and actual current original PE instruction bytes; no previous successful helper was rerun.

This receiver retains ECX Q in ESI. Formal3 is read as BYTE at562514, compared unsigned<0Dh. Valid0..12 indexes native13-byte table7F6F40; the result is stored only BYTE at EBP-4. Invalid13..255 takes two opaque diagnostic calls then stores BYTE0F. Formal4 is read as BYTE at56255B, compared unsigned<43h. Valid0..66 indexes native67-byte table7F6F50; the result overwrites only BYTE of original formal3 cell EBP+10h. Invalid67..255 takes one opaque diagnostic call then writes that BYTE0. Exact80 table bytes and every index/output are retained; they do not prove named miss/critical/death/immunity outcomes. Native table stability/readability and returning diagnostic/callee/frame lifetime are necessary premises.

Beyond the prologue/argument stack PUSHes, explicit MOV memory writes are solely local BYTE EBP-4 and BYTE formal3 EBP+10h. There is no own actor pointer lookup, actor+239 or actor+28A read, HP/maxHP read, HP addition/clamp/death flag store or64-bit arithmetic. Opaque children may have effects; this bounded body is not global absence evidence.

At56258B..56259C it pushes original formal5 wholeDWORD, modified originalformal3 wholeDWORD, local EBP-4 wholeDWORD, formal2 wholeDWORD, formal1 wholeDWORD and calls564A30 with unchanged Q. Thus childformal1/2/5 are forwarded; childformal3 is firstmap's lowBYTE plus original Q upper24 bits: prologue562513 PUSH ECX initialized EBP-4 as the whole incoming Q before the BYTE overwrite; childformal4 is secondmap's lowBYTE plus retained upper24 of the originalformal3 input cell. The exact local wholeDWORD is (Q & FFFFFF00h) | firstmapBYTE under ordinary frame/callee-return premises; it is not a zero-extended or signed marker. Selected authentic parent557090 MOVZXlogicalBYTE13 and55708B MOVZXlogicalBYTE14 prove original formal3/4 input upper24 zero; consequently selected childformal4's wholeDWORD is zero-extended secondmap. They do not replace original Q upper24 in EBP-4. Child564A30 width use remains OPEN and was not expanded. For general callers, retained upper24 of originalformal3 is also unqualified. Formal1/2 upper bytes remain as the real parent supplied; parent557087 MOVZXbodyaction proves formal5 low action and upperzero (03h/17h on the selected shared action arm).

The real next source is564A30, but whether it narrows those marker operands, reads actor+28A/current index, or mutates HP/death is not established. No direct amount argument passes through562510. Prior rawSI cache and signed HP-labelled presentation remain separate from actual HP mutation, server damage coefficients, custom CN learned grants/visual bridge, full cast/adoption and64-bit health semantics. Common source checkpoint integration elsewhere is not evidenced by this receiver.

Accounting: one locally complete known native source body, method/opcode/format/handler/phase/fullroute credits0. Code152 bytes, exacttable80 bytes, padding8 and boundary witness6 separate. Static read/hash/PE/Capstone only; no canonical source changes, native/client/CRT/API/VM/parser/codec/resource execution, SQL/database/import, compiler/build/tests. This finite task stops after source/seal delivery with all descendants opaque.
"""
put('REPORT.md',report.encode());out('PASS.json',dict(verdict='PASS bounded original modifier mapping',code_bytes=152,sites=len(ins),data_bytes=80,actual_HP_reader_proven=False,actual_HP_mutation_proven=False,child_width_use_qualified=False,new_global_method_credit=0,new_route_credit=0,product_execution=0,tracked_edits=0))
helpers=[]
for name in ['discover_queued_delta361.py','capture_modifier_mapping361.py']:
 h=(D/name).read_bytes();assert b'\r' not in h and not h.startswith(b'\xef\xbb\xbf');helpers.append(dict(path=(D/name).as_posix(),bytes=len(h),sha256=sha(h),successful_execution_count=1))
out('successful-LF-helper-metadata.json',helpers);assert sha(P.read_bytes())==PIN;assert not(D/'seal.json').exists();members=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  h=p.read_bytes();members.append(dict(path=p.relative_to(D).as_posix(),bytes=len(h),sha256=sha(h)))
for m in members:
 h=(D/m['path']).read_bytes();assert len(h)==m['bytes'] and sha(h)==m['sha256']
out('seal.json',dict(member_count=len(members),member_bytes=sum(m['bytes'] for m in members),members=members))
for m in json.loads((D/'seal.json').read_bytes())['members']:
 h=(D/m['path']).read_bytes();assert len(h)==m['bytes'] and sha(h)==m['sha256']
print(json.dumps(dict(members=len(members),member_bytes=sum(m['bytes'] for m in members),seal_sha256=sha((D/'seal.json').read_bytes()),seal_bytes=len((D/'seal.json').read_bytes()),proof=proof,helpers=helpers)))
