"""Round199 bounded native incoming skill/inventory source reading. Static file IO only."""
from pathlib import Path
import csv, json, hashlib
import pefile, capstone
ROOT=Path(__file__).resolve().parents[2]
REC=Path("C:/Users/risei/Desktop/God2-xjz/God2_opt_source_recovery_20260926_055734/decompiled")
PE=Path("C:/Users/risei/Desktop/God2-xjz/XJZ-CN/God2_opt.exe")
OUT=ROOT/"artifacts/integration/packet-connections-20261006/cn-native-skill-confirmation-frontier-01/agents/cn-learning-reply-frontier"
PIN="582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8"
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(n,v):
 p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def main():
 if OUT.exists():raise SystemExit("Preserve existing evidence; this tool does not overwrite epochs")
 OUT.mkdir(parents=True)
 original=[];current=[];context=[];native=[]
 def capture(p,n,role):
  b=p.read_bytes();q=OUT/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
  row=dict(path=str(p.resolve()),copy=n,bytes=len(b),sha256=sha(b));original.append(row)
  {"current":current,"context":context,"native":native}[role].append(row)
  return row
 raw=PE.read_bytes();assert sha(raw)==PIN
 pe=pefile.PE(data=raw,fast_load=True);md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
 refs=[]
 for p in [PE,REC/"functions.tsv",REC/"calls.tsv"]:
  b=p.read_bytes();refs.append(dict(path=str(p),bytes=len(b),sha256=sha(b),copy=None,disposition="Actual complete external original retained in place; not copied wholesale in this bounded small artifact"))
 functions=list(csv.DictReader((REC/"functions.tsv").open(encoding="utf-8"),delimiter="\t"))
 addresses=["004d5e60","004d5cc0","0048fcc0","004c9ae0","004c2b30","004c7a50","004c72e0","004c9b10"]
 selected=[]
 for i,a in enumerate(addresses):
  x=next(x for x in functions if x["address"].lower()==a);selected.append(x);capture(REC/x["file"],f"originals/native/n{i:02}.c","native")
 source=["AGENTS.md","docs/IMPLEMENTATION_PROVENANCE.md","docs/GOAL_ACCEPTANCE.md","src/cn/protocol/CnBattleInventorySlot.h","tools/reconstruction/cn_wrapper_route_frontier.py","tools/reconstruction/cn_battle_inventory_frontier192.py","tools/reconstruction/cn_learning_reply199.py"]
 for i,n in enumerate(source):capture(ROOT/n,f"originals/source/r{i:02}.txt","current")
 capture(Path(__file__),"epochs/tool-initial.py","context")
 dump("before-absence.json",dict(path=str(Path(__file__)),before="absent before this round tool creation",cpp_changes=0))
 specs=[(0x4c2b69,0x87,"new bounded raw data writes; whole canonical function previously retained"),(0x4c7a50,0x65,"new bounded raw ordinary-slot subtract/clear; whole canonical function previously retained"),(0x4c72e0,252,"retained whole S41 updater; round192 captured full native bytes"),(0x4d5e60,479,"retained whole WORLD34 consumer; prior193/195"),(0x4d5cc0,411,"retained whole WORLD35 consumer; prior193/195"),(0x4913d7,20,"retained incoming WORLD3B wrapper transfer"),(0x4913eb,20,"retained incoming WORLD3C wrapper transfer"),(0x4913ff,20,"retained incoming WORLD41 wrapper transfer and round192 bytes")]
 spans=[]
 for i,(a,n,role) in enumerate(specs):
  off=pe.get_offset_from_rva(a-pe.OPTIONAL_HEADER.ImageBase);b=raw[off:off+n];ins=list(md.disasm(b,a));assert sum(x.size for x in ins)==n
  stem=f"native/s{i:02}";q=OUT/(stem+".bin");q.parent.mkdir(exist_ok=True);q.write_bytes(b)
  (OUT/(stem+".tsv")).write_text("va\tbytes\tmnemonic\toperands\n"+"".join(f"0x{x.address:08X}\t{x.bytes.hex()}\t{x.mnemonic}\t{x.op_str}\n" for x in ins),encoding="utf-8")
  spans.append(dict(begin=f"0x{a:08X}",end_exclusive=f"0x{a+n:08X}",bytes=n,file_offset=off,sha256=sha(b),raw=stem+".bin",instructions=stem+".tsv",sites=len(ins),classification=role))
 relations=[dict(scope="4C2B69..4C2BF0 data-copy and quantity writes",raw_sites=["0x004C2B69","0x004C2B83","0x004C2B8B","0x004C2B8F","0x004C2BAB","0x004C2BC0","0x004C2BCF","0x004C2BDE","0x004C2BE8"],fact="S3B payload+4..0x23 full32B -> actual U+0x41AF8+slot*0x24 (record+4..0x23). Record+1..3 are not written in this bounded copy. Resource record+0x11B bit1 chooses BYTE-add payload0 versus force1; add is native BYTE arithmetic, signed quantity>30 clips30. This separate stackability flag is not prior item book byte+0x11A. No cost/custody or stack99 implementation."),dict(scope="4C7A50..4C7AB5 ordinary slots0..29",raw_sites=["0x004C7A5A","0x004C7A5D","0x004C7A7D","0x004C7A80","0x004C7A8F","0x004C7A97","0x004C7A99","0x004C7AAA"],fact="Ordinary slot uses payload BYTE2; payload BYTE3 subtracts from record BYTE0. Signed post-subtraction<=0 clears quantityBYTE0 and itemWORD4. No payload WORD0 read anywhere in complete canonical callee; this local scope is not a whole-protocol absence or authority proof. Prefix can invoke unrelated local callback; no permission inferred.")]
 findings=dict(round=199,cpp_files_changed=0,new_bounded_native_spans=2,new_bounded_native_bytes=236,new_native_relations=relations,retained_native_spans=6,retained_native_bytes=1202,new_whole_native_functions=0,whole_function_context="Existing source canonical and incoming cases retained; new only previously unsealed bounded raw field qualification, not global exhaustive uniqueness proof.",incoming_owner="4913D7/4913EB/4913FF all pass actual packet+1 and ECX=P+0x89B26C=U to S3B/S3C/S41 respectively. Same P/actual call/epoch only.",skill_update_scope="Retained WORLD34 4D5E60 writes matching subject WORDid row (U+430A8)+D8+n*3EC: append catalog pointer row258, flag0 at1F1+index, count1F0; WORLD35 4D5CC0 finds exact catalog pointer and writes flag3, does not remove pointer/count. Names/debugtext do not grant learning/cast.",inventory_scope="S3B/S3C/S41 operate directly U+41AF4+slot*24h, not the subject row skill storage; same owner does not establish request/reply correlation. S41 payloadWORD0 item,BYTE2 slot,BYTE3 absolute count; signed count<=0 clears item/count, retained proof.",source_qualification_actions=["Keep skill-flag3 and inventory slot clearing separate; neither is learned-skill deletion proof.","Keep S3B full32B record tail and untouched bytes1..3; never populate them with zero/defaults from this consumer.","Item custody/current/source generation must qualify actual common item source. S3C raw itemWORD cannot certify requested-item identity in this local consumer.","Do not promote native resource stackability/30 display cap into common ownership or owner-requested99 support."],gaps=["Actual C25/modal request to incoming S3B/S3C/S41/WORLD34/35 correlation and once authoritative common settlement remain OPEN.","Complete native use/learning result history, entitlement, spent custody and resulting learned state remain unsupplied.","No new opcode/phase/whole route; full game denominator and percentage unknown.","PE and TSV complete external originals hashed in place; only complete canonical C/source originals and bounded PE bytes copied in this small artifact.","Earlier exploratory4913CC was not instruction aligned and is excluded from evidence; formal copied dispatch blocks are exact4913D7/EB/FF."],new_opcode_bindings=0,new_phase_bindings=0,new_complete_routes=0,receiver_contexts=14,qualified_receiver_contexts=12,unresolved_helpers=[dict(va="0x0047DE70",phase=None,slot=None),dict(va="0x004812B0",phase=None,slot=None)],original_input_count=len(original),native_copies=len(native),current_source_count=len(current),context_count=len(context))
 dump("findings.json",findings);dump("native-spans.json",spans);dump("selected-function-metadata.json",selected);dump("native-input-references.json",refs);dump("native-original-inputs.json",native);dump("original-inputs.json",original);dump("current-source-origins.json",current);dump("context-origins.json",context);dump("LIST.json",original)
 print(json.dumps(dict(out=str(OUT),new_bytes=236,retained_bytes=1202,originals=len(original),current=len(current),native=len(native),sites=[x["sites"] for x in spans])))
if __name__=="__main__":main()
