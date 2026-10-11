"""Round201 actual world subject auxiliary-row source. File/static PE only."""
from pathlib import Path
import csv,json,hashlib,sys
import pefile,capstone
R=Path(__file__).resolve().parents[2]
D=Path("C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled")
P=Path("C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe")
O=R/"artifacts/integration/packet-connections-20261006/cn-native-shared-book-request-source-01/agents/native-learned-row-source"
PIN="582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8"
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,v):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def source_ready():
 if (O/"findings.json").exists():raise SystemExit("Preserve existing source-ready epoch")
 O.mkdir(parents=True,exist_ok=True);orig=[];cur=[];native=[]
 def cp(p,n,role):
  b=p.read_bytes();q=O/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b);x=dict(path=str(p.resolve()),copy=n,bytes=len(b),sha256=sha(b));orig.append(x);{"current":cur,"native":native}[role].append(x)
 raw=P.read_bytes();assert sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);m=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 refs=[]
 for p in [P,D/"functions.tsv",D/"calls.tsv"]:
  b=p.read_bytes();refs.append(dict(path=str(p),bytes=len(b),sha256=sha(b),copy=None,disposition="Complete actual external original retained in place, not whole-file artifact copy"))
 rows=list(csv.DictReader((D/"functions.tsv").open(encoding="utf-8"),delimiter="\t"));meta=[]
 addresses=["004d5830","004d4e00","004d5e60","004d5cc0","0048fcc0","004d5880","004d5a10","004d5b20","004d58b0","00553bc0"]
 for i,a in enumerate(addresses):
  x=next(x for x in rows if x["address"].lower()==a);meta.append(x);cp(D/x["file"],f"originals/native/n{i:02}.c","native")
 for i,n in enumerate(["AGENTS.md","docs/IMPLEMENTATION_PROVENANCE.md","docs/GOAL_ACCEPTANCE.md","tools/reconstruction/cn_learned_row201.py"]):cp(R/n,f"originals/source/r{i:02}.txt","current")
 (O/"epochs/tool-initial.py").write_bytes(Path(__file__).read_bytes())
 calls=[]
 with (D/"calls.tsv").open(encoding="utf-8") as f:
  for x in csv.DictReader(f,delimiter="\t"):
   if x["target"].lower()=="004d5830":calls.append(x)
 specs=[(0x4d5830,76,"new whole pure world rawflags-to-auxiliary materializer"),(0x4d4e9d,13,"retained selector caller exact current row push and transfer"),(0x4d5d85,16,"retained WORLD35 exact row push/flag3/transfer"),(0x4d5f4f,99,"retained WORLD34 exact row push/append/count/page/transfer; old whole consumer not re-counted")]
 spans=[]
 for i,(a,n,role) in enumerate(specs):
  off=pe.get_offset_from_rva(a-pe.OPTIONAL_HEADER.ImageBase);b=raw[off:off+n];ins=list(m.disasm(b,a));assert sum(x.size for x in ins)==n
  stem=f"native/s{i:02}";q=O/(stem+".bin");q.parent.mkdir(exist_ok=True);q.write_bytes(b)
  (O/(stem+".tsv")).write_text("va\tbytes\tmnemonic\toperands\n"+"".join(f"0x{x.address:08X}\t{x.bytes.hex()}\t{x.mnemonic}\t{x.op_str}\n" for x in ins),encoding="utf-8")
  spans.append(dict(begin=f"0x{a:08X}",end_exclusive=f"0x{a+n:08X}",bytes=n,file_offset=off,sha256=sha(b),raw=stem+".bin",instructions=stem+".tsv",sites=len(ins),classification=role))
 relations=[dict(scope="4D5830 complete76B",raw_sites=["0x004D5833","0x004D5839","0x004D5840","0x004D5847","0x004D5850","0x004D585A","0x004D585E","0x004D5860","0x004D5864","0x004D5867","0x004D5872"],fact="BYTE primarycount row1F0; BYTE auxcount row5C reset0. Ascending sourceordinal, raw flags(row1F1+i)&0x02 nonzero copies exact DWORD(row258+4i) to row60+4auxcount and increments BYTEauxcount. Preserve null/duplicates/order and stale tail; no resource lookup, permission, semantic learned/cast labels or dedup."),dict(scope="actual original caller arguments, old whole consumers retained",raw_sites=["0x004D4E9D","0x004D4EA5","0x004D5D85","0x004D5D88","0x004D5D90","0x004D5F4F","0x004D5FAD"],fact="4D4E00 selects real row pointer then passes[V+D0]; WORLD35 passes matching rowEDI after flags3; WORLD34 saved rowESI stackarg survives intervening data updates then calls materializer. Same actual caller/row/epoch only, not common ID/grant. WORLD34 initialflag0 does not add that pointer to aux until some actual flag state qualifies; WORLD35 flag3 has mask02 set."),dict(scope="readonly actual row geometry qualification",raw_sites=["0x004D585A","0x004D5860","0x004D5864"],fact="Count5C is BYTE, not WORD. Row60..1F0 space has100 DWORD storage positions, but leaf has no explicit max100/null/bank/current checks. Own actual-row reader validates captured primary count<=100 from3EC layout; do not call this native progression/cap permission. Supply actual stored auxprefix, never emulate/synthesize its output.")]
 findings=dict(round=201,cpp_files_changed_by_agent=0,new_bounded_native_spans=1,new_bounded_native_bytes=76,new_native_relations=relations,retained_bounded_native_spans=3,retained_bounded_native_bytes=128,new_opcode_bindings=0,new_phase_bindings=0,new_complete_routes=0,receiver_contexts=14,qualified_receiver_contexts=12,unresolved_helpers=[dict(va="0x0047DE70",phase=None,slot=None),dict(va="0x004812B0",phase=None,slot=None)],coverage_scope="New local bounded capture. Exact limited193-196/repo inventory did not list this leaf; not a global uniqueness/absence proof.",world_battle_limit="This qualifies world-row rawflags -> actual auxiliary prefix only. Prior193 proves battle group2D4 actual rowpointer and initializer normalization/callee boundaries, not a rowaux-to-primary learned-list materializer. Retain distinct WORLD34/35 andS87 lifecycle; no complete battle bridge claim.",population_limit="Main skill count1F0/flags1F1/catalog pointers258 incoming authority/population/learned rights are still separate. New auxiliary source consumes actual existing fields; does not invent original learned grants.",source_action="Root may append readonly actual auxiliary prefix to existing CnPrebornSubjectState Selection using whole original3EC actualrow. Preserve exact pointer bytes/nulls/duplicates/order, no native memory runtime requirement, no simulated helper/defaults. Root2 final context must be latest fullfiles, while before201 epoch remains historical.",gaps=["Actual initial primary-list/count source, official learned entitlement and common subject identity/root/current/skill rights remain OPEN.","WORLD-to-battle primary materialization and initial87 history/cast authorization remain OPEN; samepointer/bank alone insufficient.","Aux-tail is not cleared by helper; no implicit zeroing or inactive-data substitution.","No render/formatter/glyph/155/52F330/52F170 interior followed and no test/build/runtime/native/API/codec/DB/SQL executed.","Full-game packet denominator/percentage unknown; no new opcode/phase/full route."],original_input_count=len(orig),native_full_copies=len(native),current_source_count=len(cur),root_final_context_pending=True)
 put("findings.json",findings);put("native-spans.json",spans);put("native-input-references.json",refs);put("selected-function-metadata.json",meta);put("derived-actual-calls.json",calls);put("native-original-inputs.json",native);put("original-inputs.json",orig);put("current-source-origins.json",cur);put("LIST.json",orig)
 put("qualification-correction.json",dict(initial_message_scope="Initially described aux as filling prior battle list bridge",corrected_scope="Actual pure leaf proves only world row auxiliary materialization. Re-read prior193 finalfindings and553BC0 fulloriginal: group2D4 is rowpointer only; no direct aux read/learned primary materializer proven. No oldseal altered.",source_not_native_proof="Parent messages/qualification correction are historical receipts, not native sources/current pins"))
 print(json.dumps(dict(stage="source-ready",out=str(O),new_bytes=76,retained_bytes=128,native=len(native),originals=len(orig),current=len(cur),sites=[x["sites"] for x in spans])))
def final():
 if (O/"seal.json").exists():raise SystemExit("Immutable sealed artifact")
 original=json.loads((O/"original-inputs.json").read_text(encoding="utf-8"));context=[]
 (O/"epochs/findings-source-ready.json").write_bytes((O/"findings.json").read_bytes())
 for i,n in enumerate(["src/cn/world/CnPrebornSubjectState.h","src/cn/world/CnPrebornSubjectState.cpp"]):
  p=R/n;b=p.read_bytes();copy=f"originals/root-final/f{i:02}.txt";q=O/copy;q.parent.mkdir(exist_ok=True);q.write_bytes(b);x=dict(path=str(p.resolve()),copy=copy,bytes=len(b),sha256=sha(b));original.append(x);context.append(x)
 put("original-inputs.json",original);put("context-origins.json",context);put("LIST.json",original)
 x=json.loads((O/"findings.json").read_text(encoding="utf-8"));x.update(original_input_count=len(original),root_final_context_pending=False,root_final_context_count=len(context));put("findings.json",x)
 (O/"epochs/tool-final.py").write_bytes(Path(__file__).read_bytes())
 print(json.dumps(dict(stage="final-context",originals=len(original),current=4,native=10,root_context=len(context))))
if __name__=="__main__":
 if "--final" in sys.argv:final()
 else:source_ready()
