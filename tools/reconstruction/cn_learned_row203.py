"""203 exact primary world-row reset lifecycle; static native file capture only."""
from pathlib import Path
import csv,json,hashlib
import pefile,capstone
R=Path(__file__).resolve().parents[2]
D=Path("C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled")
P=Path("C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe")
O=R/"artifacts/integration/packet-connections-20261006/cn-primary-skill-definition-source-01/agents/primary-population-source"
PRIOR=R/"artifacts/integration/packet-connections-20261006/cn-native-shared-book-request-source-01/agents/native-learned-row-source"
PIN="582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8"
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,v):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def main():
 if O.exists():raise SystemExit("Preserve actual epochs; no overwrite")
 O.mkdir(parents=True);orig=[];cur=[];native=[];historical=[]
 def cp(p,n,role):
  b=p.read_bytes();q=O/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b);x=dict(path=str(p.resolve()),copy=n,bytes=len(b),sha256=sha(b));orig.append(x);{"current":cur,"native":native,"historical":historical}[role].append(x)
 raw=P.read_bytes();assert sha(raw)==PIN;pe=pefile.PE(data=raw,fast_load=True);md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 external=[]
 for p in [P,D/"functions.tsv",D/"calls.tsv"]:
  b=p.read_bytes();external.append(dict(path=str(p),bytes=len(b),sha256=sha(b),copy=None,disposition="Whole actual native input hashed in place, no whole PE/TSV artifact copy"))
 funcs=list(csv.DictReader((D/"functions.tsv").open(encoding="utf-8"),delimiter="\t"));meta=[]
 addresses=["00493fc0","0048fcc0","00492e70","004c73e0","004d2b50","004d5750"]
 for i,a in enumerate(addresses):
  x=next(x for x in funcs if x["address"].lower()==a);meta.append(x);cp(D/x["file"],f"originals/native/n{i:02}.c","native")
 for i,n in enumerate(["AGENTS.md","docs/IMPLEMENTATION_PROVENANCE.md","docs/GOAL_ACCEPTANCE.md","tools/reconstruction/cn_learned_row203.py","tools/reconstruction/cn_native_learned_skill_event_frontier196.py"]):cp(R/n,f"originals/source/r{i:02}.txt","current")
 for n in ["findings.json","seal.json","native-spans.json"]:cp(PRIOR/n,f"epochs/prior201-{n}","historical")
 (O/"epochs/tool-initial.py").write_bytes(Path(__file__).read_bytes())
 prior=json.loads((PRIOR/"seal.json").read_text(encoding="utf-8"))
 for x in prior["members"]:
  b=(PRIOR/x["path"]).read_bytes();assert len(b)==x["bytes"] and sha(b)==x["sha256"]
 put("prior201-read-receipt.json",dict(seal_sha256=sha((PRIOR/"seal.json").read_bytes()),members=len(prior["members"]),scope="All nested prior bytes read/hash-compared; sealed prior not changed or treated current source."))
 specs=[(0x493fc0,70,"new complete pure primary/aux row reset, not positive grant"),(0x4927fc,57,"new bounded actual R caller transfer and next identity/input progression; old whole WORLDdispatcher not new"),(0x493540,116,"retained initial source row/bank initialization from round196; no recount")]
 spans=[]
 for i,(a,n,role) in enumerate(specs):
  off=pe.get_offset_from_rva(a-pe.OPTIONAL_HEADER.ImageBase);b=raw[off:off+n];ins=list(md.disasm(b,a));assert sum(x.size for x in ins)==n
  stem=f"native/s{i:02}";q=O/(stem+".bin");q.parent.mkdir(exist_ok=True);q.write_bytes(b)
  (O/(stem+".tsv")).write_text("va\tbytes\tmnemonic\toperands\n"+"".join(f"0x{x.address:08X}\t{x.bytes.hex()}\t{x.mnemonic}\t{x.op_str}\n" for x in ins),encoding="utf-8")
  spans.append(dict(begin=f"0x{a:08X}",end_exclusive=f"0x{a+n:08X}",bytes=n,file_offset=off,sha256=sha(b),raw=stem+".bin",instructions=stem+".tsv",sites=len(ins),classification=role))
 calls=[]
 with (D/"calls.tsv").open(encoding="utf-8") as f:
  for x in csv.DictReader(f,delimiter="\t"):
   if x["target"].lower()=="00493fc0" or x["caller"].lower()=="00493fc0":calls.append(x)
 rel=[dict(scope="493FC0 full70B exact R stackarg and separate P ECX",raw_sites=["0x00493FC3","0x00493FC7","0x00493FCE","0x00493FD7","0x00493FDE","0x00493FE8","0x00493FEE","0x00493FF6","0x00493FFC"],fact="R164 rostercount BYTE0; R15F selectedindex BYTEFF; R160 selectedptr DWORD0; memset(R168,0,3EC0) clears sixteen whole3EC rows including primary count1F0/flags1F1/pointers258 ANDaux5C/60. It does not synthesize any definitions or learned grants. ECX=P saved separately; subsequent4C73E0 receives P89B26C inventoryowner. Do not confuse reset argument R with ECX owner P/U."),dict(scope="4927FC..492835 actual caller continuation",raw_sites=["0x004927FC","0x00492802","0x00492804","0x00492805","0x00492818","0x0049281F","0x00492821","0x00492830"],fact="Actual R=LEA P1478084 passed whole to reset with ECX=P. Afterreset current raw localDWORD &3FFF becomes R0 then C1F(1),C23(1) use exactU=P89B26C. Full canonical48FCC0 places this in WORLD caseCF success branch after local supplied object qualification. No learning/reply/cast/phase-right pairing inferred."),dict(scope="reset domain comparison, retained source-only",raw_sites=["0x00493FEE"],fact="Unlike WORLD30 count-only reset retaining aux stale prefix, this actualwhole-row memset clears primary/aux/flags/pointers together. Original scene initialization492E70 alsowhole-row clears after bank binding, already retained196; cannot recount as another learned population. Existing WORLD34 increment pointer/flag0 and35 flag3 remain distinct incoming history.")]
 f=dict(round=203,cpp_files_changed=0,new_bounded_native_spans=2,new_bounded_native_bytes=127,new_whole_pure_functions=1,new_native_relations=rel,retained_bounded_native_spans=1,retained_bounded_native_bytes=116,coverage_scope="New bounded local reset/caller capture only, not global unique coverage proof; old complete canonical contexts retained. Positive primary population remains unresolved beyond previously qualified incremental consumers.",primary_population="Exact native whole-row empty reset qualification recovered. No new positive learned-list population/resource lookup or WORLD→battle primary materialization; no auxprefix substituted for primary. Native source state is not an authoritative gameplay grant.",source_actions=["Retain whole sameR/epoch row lifecycle; exact reset invalidates previous primary/aux bytes and selected row pointer. Currentactualsnapshot must not revive old identity afterR0 replacement.","Retain WORLD30 count-only and whole-row reset as different typed source facts; do not impose one as universal invariant.","Common own actor/learned grant/save/replay authority still requires actual supplier; C1F/C23 local progression and full data do not replace that authority."],next_actual_leaf=dict(va="0x004D2B50",scope="Pure primary catalogpointer ordinal lookup underselectedrow; raw pointer membership only, not writer/grant. Its exact source callroot can be used next to qualify definition identity while genuine positive population remains an incoming history gap."),gaps=["Positive initial primarycount/pointer supplier beyond retained WORLD34/35 and original learned rights remain OPEN.","WORLDrow→battle primarymaterializer remains OPEN; GUI/render callees and552870/553220/552CB0 interiors not followed.","No opcode/phase/current connection qualification from CF label; whole game denominator/percentage unknown.","No formatter155/capacity/render/glyph/52F330/52F170 interior or native/emulator/codec/API/DB/SQL/build/test/runtime used.","Exploratory4927EF dump was misaligned and excluded; formalinstruction evidence starts4927FC.","Whole native PE andTSVs hashes referenced in place; actual completeC/source copies and bounded bytes retained."],new_opcode_bindings=0,new_phase_bindings=0,new_complete_routes=0,receiver_contexts=14,qualified_receiver_contexts=12,unresolved_helpers=[dict(va="0x0047DE70",phase=None,slot=None),dict(va="0x004812B0",phase=None,slot=None)],current_source_count=len(cur),native_canonical_count=len(native),historical_count=len(historical),original_input_count=len(orig))
 put("findings.json",f);put("native-spans.json",spans);put("native-input-references.json",external);put("selected-function-metadata.json",meta);put("xref-call-rows.json",calls);put("original-inputs.json",orig);put("native-original-inputs.json",native);put("current-source-origins.json",cur);put("historical-origins.json",historical);put("LIST.json",orig)
 print(json.dumps(dict(out=str(O),new=127,retained=116,current=len(cur),native=len(native),historical=len(historical),original=len(orig),sites=[x["sites"] for x in spans])))
if __name__=="__main__":main()
