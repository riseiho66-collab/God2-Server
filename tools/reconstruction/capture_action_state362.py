from pathlib import Path
import hashlib,json
import pefile
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
D=Path(__file__).resolve().parent;U=D.parent/'round361-cn-skill-queued-delta-reader-source';P=Path('C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe');PIN='582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8'
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);assert p.read_bytes()==b
def out(n,v):put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
raw=P.read_bytes();assert sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
def at(va,size):
 off=pe.get_offset_from_rva(va-base);b=raw[off:off+size];assert len(b)==size;return b
lo=0x564a30;end=0x564c6d;b=at(lo,end-lo);md=Cs(CS_ARCH_X86,CS_MODE_32);ins=list(md.disasm(b,lo));assert len(b)==573 and sum(i.size for i in ins)==573 and ins[0].bytes==b'\x55';by={i.address:i for i in ins};pending=[lo];seen=set();branches=[];rets=[];calls=[]
for i in ins:
 if i.mnemonic.startswith('j'):
  assert i.op_str.startswith('0x');t=int(i.op_str,16);assert t in by;branches.append(dict(va=f'{i.address:08X}',target=f'{t:08X}'))
 if i.mnemonic.startswith('ret'):assert i.op_str=='0x14';rets.append(f'{i.address:08X}')
 if i.mnemonic=='call':calls.append(dict(va=f'{i.address:08X}',target=i.op_str,opaque=True))
while pending:
 va=pending.pop()
 if va in seen:continue
 assert va in by;seen.add(va);i=by[va]
 if i.mnemonic.startswith('ret'):continue
 if i.mnemonic=='jmp':pending.append(int(i.op_str,16))
 elif i.mnemonic.startswith('j'):pending.extend([int(i.op_str,16),va+i.size])
 else:pending.append(va+i.size)
assert len(rets)==6 and len(seen)==len(ins) and ins[-1].address==0x564c6a;put('qualified/564a30-full-code.bin',b);put('qualified/564a30-full-code.tsv',('va\thex\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode());pad=at(end,3);assert pad==b'\xcc'*3;put('qualified/after-ret-padding.bin',pad);nextb=at(0x564c70,7);assert nextb[:3]==b'\x55\x8b\xec';put('qualified/next-authentic-entry-prefix.bin',nextb)
# Authentic parent whole body and original PUSH/partial-cell provenance preserved by reference.
parent=U/'qualified/562510-full-code.bin';pb=parent.read_bytes();assert pb==at(0x562510,152);ref=dict(actual_path=parent.as_posix(),bytes=len(pb),sha256=sha(pb),copied=False);out('actual-parent-source-reference.json',ref)
pt=(U/'qualified/562510-full-code.tsv').read_bytes();selected=[line for line in pt.decode().splitlines()[1:] if 0x56258b<=int(line.split('\t')[0],16)<0x5625a1]
for line in selected:
 va,h,mn,op=line.split('\t');assert at(int(va,16),len(bytes.fromhex(h)))==bytes.fromhex(h)
assert any(line.startswith('0056259C\t') and line.endswith('0x564a30') for line in selected);put('actual-parent56258b-5625a1-excerpt.tsv',('va\thex\tmnemonic\toperands\n'+'\n'.join(selected)+'\n').encode())
stores=[dict(va=f'{i.address:08X}',hex=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in ins if i.op_str.split(',')[0].strip().endswith(']') and i.mnemonic in {'mov','inc','dec','add','sub','and','or','xor'}];out('direct-memory-destinations.json',stores)
proof=dict(entry='00564A30',end_exclusive='00564C6D',whole_function=True,code_bytes=573,sites=len(ins),reachable_sites=len(seen),RET14h=rets,branches=branches,opaque_calls=calls,padding_bytes=3,next_entry_witness_bytes=7,own_table_bytes=0,original_PE_sha256=PIN,independent_mapped_memory_proof=False,new_global_method_credit=0,new_route_credit=0);out('qualified-boundary-and-CFG.json',proof)
report=f"""# N362 original CN action/modifier state consumer

PASS for finite static own-body closure, not an HP reader claim. Original pinned CN PE582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8 /47,541,760 bytes is hash-referenced in place only, no full image copy or independent mapped-memory pair. All19 N361 members/67,662 bytes were read individually before discovery; prior562510 and upstreamsigned16 HP-labelled display findings are unchanged. Authentic parent56259C CALL564A30 and its selected PUSH span match current PE bytes.

True564A30 entry55/8BEC to564C6D exclusive closes573 code bytes/{len(ins)} sites, all{len(seen)} reachable. All{len(branches)} direct branches target aligned own instructions; no own switch or embedded data table exists. SixRET14h sites clean five DWORD formal cells. ThreeCC padding bytes and next564C70 seven-byte authentic prologue witness are excluded code. Discovery's4000-byte envelope contains later unrelated code and remains candidate-only. Three opaque CALLs are retained: diagnostic53E3D0 at564A56/564BBD and generic actor lookup55E220 at564AC9; no child was expanded.

Same incoming ECX Q is retained in EDI. Formal1/2 are narrowed to BH/BL BYTE, with unsigned side<2 andposition<14 checks, otherwise diagnostic thencleanup. Valid actor A is Q+38+24*(14*side+position), and NULL skips. Formal5 action is readBYTE intoBL;03h and17h (decimal23) route564B91,0Dh separate564B68,others generic564AB0. Decimal17 is not17h. Formal3/4 are also consumed solely lowBYTE. This closes the N361 width question: childformal3's original Q upper24 bits, and general parentformal3/formal4 retained upperbits, are irrelevant to this body's marker reads; no zeroing or fullDWORD marker semantics is needed. Formal5 upperbits are ignored here too.

Selected03h/17h:564B91 reads BYTE A+239 as index i, sets EBX=A+i, then reads packedBYTE A+23A+i. Packed side isbit7 and positionlow4; bits4..6 are ignored. Position must be<14 or diagnostic+RET; side naturally0..1. The target B is read at Q+38+24*(14*packedside+packedposition). NULL or signedWORD B+1A<0 skips all writes. There is no opposing-side, ownership/learning or serverpermission check. Actor+239 itself has no own capacity bound; allocated array/frame/readability and ordinary calling-convention/callee-return premises remain necessary. A/B may alias; target current fields are then the actual alias values, not a synthetic independent snapshot.

The actual selected write order is exact: formal3 lowBYTE c goes toA+216+i at564BF3. If currentB+1EB==3 and c is neither82h nor5, A+208+liveBYTE239 becomes3 at564C13; otherwise it becomes c at564C24. Target B+1EB is only read, not written on this selected path. Formal4 lowBYTE d is read564C32. If currentB+232==9 andd!=59h, B+232 is preserved9 andA+224+liveBYTE239 becomes9 at564C43, thenRET. Otherwise B+232=d at564C52, followed by A+224+liveBYTE239=d at564C5F. Initial i versus later liveBYTE239 reads are retained exactly; on a valid selected path no opaque child intervenes, but external pointer/memory stability remains a premise. Literal3/9/82h/59h branches are native state/modifier predicates, not qualified death/immunity/outcome names.

For0Dh, Q+30B BYTE supplies a separate index; formal3/4 lowBYTE writeA+27A+index andA+27D+index, thenRET. Generic actions decode A+235 packedside/position through opaque55E220, require nonNULL andsignedWORDhandle>=0, then writeA+1E8/A+1EB andA/B+232 with corresponding literal overrides. Those other arms remain bounded code facts, not inferred HP/death semantics. All{len(stores)} direct memory destinations are retained with exact widths/order, separate from children effects.

There is NO own read ofqueuedWORD A+28A, no HP/maxHP read, no received amount add/subtract/clamp or64-bit health arithmetic, and no directly identified death flag. This closes actual BYTE marker consumption and selected action-state array writes only. N360's rawSI→A+28A array and signedHP-labelled formatting remain display/cache source; this chain has not recovered the actual HP application reader or original damage formula. No global absence claim follows from one body. The true queued-amount reader remains unlocated within this finite chain; neither generic55E220 nor arbitrary rendering descendants are promoted as next HP source.

Accounting: one already-known method locally closed; all newglobal method/opcode/format/parser/handler/phase/fullroute credits0. Code573 bytes; no own data table; padding3/nextwitness7 separate. Successful discovery/capture/seal ran once; original upstream immutable. PHASE1 pure static read/hash/PE/Capstone only: no canonical edits, client/native/API/CRT/VM/parser/codec/resource execution, SQL/database/build/compiler/tests/import/deploy. CN custom126/150 learned/actor/resource/87/cast/effect host, nativeHP death/clamp, poisonturn/maxHPdiv10 andwide64 application/adoption remain OPEN.
"""
put('REPORT.md',report.encode());out('PASS.json',dict(verdict='PASS bounded original action-state consumer',code_bytes=573,sites=len(ins),own_tables=0,formal3_4_lowBYTE_only=True,actor239_and_packed23A_reader=True,queued28A_HP_reader_qualified=False,current_HP_mutation_qualified=False,death_flag_semantics_qualified=False,new_native_method_credit=0,new_route_credit=0,tracked_edits=0,product_execution=0))
helpers=[]
for name in ['discover_action_state362.py','capture_action_state362.py']:
 h=(D/name).read_bytes();assert b'\r' not in h and not h.startswith(b'\xef\xbb\xbf') and h.endswith(b'\n') and not h.endswith(b'\n\n');helpers.append(dict(path=(D/name).as_posix(),bytes=len(h),sha256=sha(h),successful_execution_count=1))
out('successful-LF-helper-metadata.json',helpers);assert sha(P.read_bytes())==PIN;assert not(D/'seal.json').exists();members=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  h=p.read_bytes();members.append(dict(path=p.relative_to(D).as_posix(),bytes=len(h),sha256=sha(h)))
for m in members:
 h=(D/m['path']).read_bytes();assert len(h)==m['bytes'] and sha(h)==m['sha256']
out('seal.json',dict(member_count=len(members),member_bytes=sum(m['bytes'] for m in members),members=members))
for m in json.loads((D/'seal.json').read_bytes())['members']:
 h=(D/m['path']).read_bytes();assert len(h)==m['bytes'] and sha(h)==m['sha256']
print(json.dumps(dict(member_count=len(members),member_bytes=sum(m['bytes'] for m in members),seal_bytes=len((D/'seal.json').read_bytes()),seal_sha256=sha((D/'seal.json').read_bytes()),proof=proof,helpers=helpers)))
