"""Read back finite native source, report conditional scope, seal every member."""
from pathlib import Path
import hashlib,json
from capstone import Cs,CS_ARCH_X86,CS_MODE_32,CS_AC_WRITE
from capstone.x86 import X86_OP_MEM
D=Path(__file__).resolve().parent
assert not (D/'seal.json').exists() and not (D/'PASS.json').exists()
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists(),n;p.write_bytes(b);assert p.read_bytes()==b
 return dict(path=n,bytes=len(b),sha256=sha(b))
def out(n,v):return put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
c=json.loads((D/'capture-complete.json').read_bytes());assert c['code_bytes']==355 and c['sites']==119
md=Cs(CS_ARCH_X86,CS_MODE_32);md.detail=True;summary=[];writes=[]
for a in json.loads((D/'qualified-whole-boundaries.json').read_bytes()):
 b=(D/'qualified'/f"{a['name']}.mapped.bin").read_bytes();rb=(D/'qualified'/f"{a['name']}.originalPE.bin").read_bytes()
 assert b==rb and len(b)==a['bytes'] and sha(b)==a['sha256']
 start=int(a['start_va'],16);end=int(a['end_exclusive_va'],16);ins=list(md.disasm(b,start));assert len(ins)==a['sites'] and sum(i.size for i in ins)==len(b)
 expected=('va\tbytes\tmnemonic\toperands\n'+''.join(f'{i.address:08X}\t{i.bytes.hex()}\t{i.mnemonic}\t{i.op_str}\n' for i in ins)).encode();assert expected==(D/'qualified'/f"{a['name']}.tsv").read_bytes()
 by={i.address:i for i in ins};seen=set();todo=[start]
 while todo:
  at=todo.pop()
  if at in seen:continue
  assert at in by;seen.add(at);i=by[at]
  if i.mnemonic=='ret':continue
  if i.mnemonic.startswith('j'):
   assert i.op_str.startswith('0x');todo.append(int(i.op_str,16))
   if i.mnemonic=='jmp':continue
  assert at+i.size<end;todo.append(at+i.size)
 assert seen==set(by)
 for i in ins:
  for op in i.operands:
   if op.type==X86_OP_MEM and op.access&CS_AC_WRITE:writes.append(dict(body=a['name'],va=f'{i.address:08X}',bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str,width=op.size,base=md.reg_name(op.mem.base),index=md.reg_name(op.mem.index),displacement=op.mem.disp))
 summary.append(dict(name=a['name'],bytes=len(b),sites=len(ins),reachable_sites=len(seen),all_sites_reachable_with_calls_returning=True,all_own_branches_aligned=True,indirect_own_jumps=0,ret_sites=a['returns']))
assert len(writes)==7 and len([a for a in writes if a['base']=='esi'])==2
out('independent-retained-raw-instruction-readback.json',dict(bodies=summary,code_bytes=355,data_bytes=0,sites=119,all_TSV_rows_equal_retained_original_bytes=True,assumptions=['Opaque callees return with authentic ABI/stack cleanup, preserve callee-saved registers and do not fault.','Closed own branches do not prove opaque/global side effect absence.'],not_native_execution=True))
out('all-direct-explicit-memory-destinations.json',dict(writes=writes,implicit_push_pop_stack_effects='Complete TSV retains push/pop/prologue/epilogue; this list inventories explicit memory operands only.',external_direct_writes=2,caller_argument_cell_write='4AE5F3 writes original child formal1 argument cell: after two pushes ESP+1C equals prepush ESP+14; saved signextended id replaces that caller stack cell. 4A9110 RET8 restores ESP; 4A90D0 RET4 restores next push; 4834E0 must obey its nativeABI. At4AE618 ESP+14 reads the saved id lowBYTE.',register_premise='EBX holds signextended kind across known lookup/gate and opaque4834E0 only under native callee-saved ABI; ESI holds original U. No transitive write/purity claim.'))
report="""# TW world skill shortcut source, round365

Bounded static native source PASS. No canonical files changed. No client, native instruction, CRT, emulator, parser, codec, API, product, compiler, test, runtime or game database/SQL executed. Python reads/hashes/PE mapping/Capstone and source-only instruction arithmetic are the evidence.

## Actual finite bodies and retained prior scope

The selected mapped image149c1b4510a2dee85eb988d3f6c05785a69cbf50bb8fb751af7d9814a5a6e763 and originalPE5fcf8cbfaf31d2635b4541886336293249cde61c0877de6f5a435cc2b9559fde agree byte-for-byte for these two cuts only. Images remain in place under the retained315 native-entry package; no complete image copied and no whole-image equivalence asserted.

| Body | Exclusive extent | Bytes/sites | Returns |
|---|---|---:|---|
| World shortcut dispatcher |004AE520..004AE63F|287/88|4 RET4 at4AE5BE/4AE5DC/4AE632/4AE63C|
| Authentic direct input parent |004AB650..004AB694|68/31|plainRET4AB68B/4AB693|

Total355 code bytes,119 aligned/reachable sites,0 data bytes. Every own branch lands on an aligned retained instruction. No embedded switch or indirect own jump. Reachability assumes called children return; this is not execution. Historical current-med02-self-supply already invoked complete4AE520 through its type0 item arm; daily-quest work used type1. This delivery qualifies its actual type2 source arm/caller/order, not a newly discovered whole global method. All global method/opcode/full route credits0. Existing296111 members/6,839,078 B individually verified immutable, including complete4A9110 lookup. Existing64B4A90D0 gate is hash/PE referenced rather than recaptured or recredited. Older native test claims are read as historical provenance only; none rerun/imported here.

## Actual caller and source state

4AB650 preserves suppliedECX asEDI, initializesESI=0, then calls opaque418440 with this=[U+CFF64] andESI+70h. A nonzero returned scalar plus explicit signed0<=ESI<=9 reaches4AB675 E8A62E0000 ->4AE520, sameECX=EDI and one fullDWORD index. Nonzero shortcut result returns1; otherwise iterates through index9 then returns0. The parent supplies this index bound, not a server skill/keypress/turn permission. Equality of suppliedU with canonical live world owner still needs authentic invocation/object lifetime; this body does not establish a Main caller.

Child preserves sameECX asESI. ModeDWORD[U+A3D08]==0 reads six-byte tupleU+A3D18+6*shortcut. Mode1 reads role=[U+86888], sign-extends roleBYTECF, and reads U+A3D54+6*(shortcut+10*sign8(CF)). Neither child nor parent adds a CF/table/pointer bound. Other mode values skip stacktuple initialization and still read it; no native reject/zero safety can be claimed. Mode0/1, readable current source and correct object affinity are explicit prerequisites. TupleWORD0 dispatches; tupleWORD2/4 are later signed kind/id values.

## Type2 branch and exact ordered operands

4AE5DF compares tuple type to2. 4AE5E5 sign-extends tupleWORD4 toEAX(id),4AE5EA sign-extends tupleWORD2 toEBX(kind). It pushes id then kind;4AE5F7 calls existing4A9110 sameU. That complete read-only lookup follows U86888 -> roleD0 row, iterates unsigned rowBYTE1F0 and compares definitionBYTE1(kind)/BYTE0(id) through rowDWORD258[index]. It returns matching insertion ordinal or-1, not a cast result.

4AE5FC compares EAX to-1; equality exits0. Otherwise4AE604 calls existing4A90D0 with the ordinal and sameU. The gate follows current player role/menu again: nonnegative ordinal/non-null menu and definition, definitionBYTE67 nonzero, then unsigned uint32 playerMP(role+64)>=uint16 definitionWORD42. It has no positive ordinal upper check and writes no resource. Lookup and predicate separate rereads are not an atomic definition/role snapshot. They do not establish original server debit/refund/discount or once-cast timing.

After a nonzero gate return,4AE613 calls opaque4834E0(U,8,1). Only after that child returns,4AE61C writes kind lowBYTE(BL) toU23D870 and4AE622 writes saved id lowBYTE(DL) toU23D871, then returns1/RET4. Saved id was written at4AE5F3 into the caller argument cell: after two pushes ESP+1C equals prepushESP+14; later4AE618 reads that cell after native stack cleanup. EBX/ESI preservation across opaque child uses the authentic callee-saved ABI premise. The seven explicit memory stores are retained: four stacktuple stores, one caller argument-cell store, these two saved bytes. Parent has no explicit memory-destination store. PUSH/POP effects remain in full TSV.

Opaque4834E0 may alter live menu/role/cursor/other aliases; no global state invariance is proved. Earlier tuple kind/id bytes are the exact saved operands under the ABI; no current learned permission, remote actor, target legality, server MP cost or computation follows. Type0 calls4963C0 and type1 calls4A6760 remain opaque in this delivery; historical respective branch facts are not promoted to type2.

## Changed next source action and limits

This is a genuine world skill cursor/operand source separate from51xx BattleC35. Future narrowly bounded work can follow actual target/cursor invocation into497A90/C56 using savedU23D870/71 and its real actor target supplier; that queue producer, its complete parent, target identity, next-byte source and opaque mode transition are OPEN here. No new handler/factory or guessed opcode added. Root common-definition handoff for actualC35 must not reuse this world pointer gate as Battle actorMP authority.

DefinitionWORD42 remains client affordability/display metadata, BYTE67 a nonzero client predicate condition. The common453 content objective does not turn these fields into full skill damage formulas or acquisition rights. Existing51xx target helpers consume BYTE44/45 for geometry/scopes; receivedS83 amount+9 and display labels do not prove its sending-side formula. No attack/defense coefficient, hit/critical/status tick, MP subtraction or server producer closed in this package.

## Capture history and custody

Initial capture_world_skill_shortcut365.py failed with SyntaxError before execution/output because return was used as a dict keyword argument. Its exact9304B source and failure receipt remain immutable. Additive_v2 changes only that keyword to return_value and succeeded once. No capture success rerun. This sealer independently reads retained raw pairs/TSVs, records own CFG and explicit writes, then seals every individual member with strict integer sizes and SHA256; only seal.json excludes itself. All helpers LF/noBOM/singleEOF. No server report/ledger/build invoked.
"""
put('REPORT.md',report.encode())
helpers=[]
for n in ['capture_world_skill_shortcut365_v2.py','seal_world_skill_shortcut365.py']:
 b=(D/n).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf') and b.endswith(b'\n') and not b.endswith(b'\n\n');helpers.append(dict(path=n,bytes=len(b),sha256=sha(b),successful_execution_count=1,LF=True,single_EOF_LF=True))
out('successful-LF-helper-metadata.json',helpers)
out('PASS.json',dict(verdict='PASS bounded source provenance',code_bytes=355,data_bytes=0,sites=119,whole_cuts=2,upstream_members_verified=111,upstream_bytes=6839078,tracked_edits=0,product_execution=0,new_global_method_credit=0,new_opcode_credit=0,completed_route_credit=0,formula_producer_qualified=False,C56_continuation_open=True))
rows=[]
for p in sorted(D.rglob('*')):
 if not p.is_file():continue
 assert p.resolve().is_relative_to(D.resolve()) and p.name!='seal.json';b=p.read_bytes();rows.append(dict(path=p.relative_to(D).as_posix(),bytes=len(b),sha256=sha(b)))
assert all(type(a['bytes']) is int for a in rows)
v=dict(kind='immutable individual-member source seal',member_count=len(rows),member_bytes=sum(a['bytes'] for a in rows),members=rows,exclusion='only top-level seal.json',tracked_changes=0,product_execution=0)
for a in rows:
 b=(D/a['path']).read_bytes();assert len(b)==a['bytes'] and sha(b)==a['sha256']
seal=put('seal.json',(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(dict(member_count=len(rows),member_bytes=v['member_bytes'],seal=seal,helpers=helpers)))
