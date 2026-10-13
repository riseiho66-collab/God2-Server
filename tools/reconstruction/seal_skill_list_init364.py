from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
def put(n,b):
 p=D/n;assert not p.exists();p.write_bytes(b);assert p.read_bytes()==b
def out(n,v):put(n,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
proof=json.loads((D/'qualified-own-body-and-caller-boundaries.json').read_bytes());assert proof['code_bytes']==710 and proof['sites']==190 and proof['caller_bytes']==66 and proof['caller_sites']==19
for ref in json.loads((D/'existing-provenance-references-in-place.json').read_bytes()):
 b=Path(ref['actual_path']).read_bytes();assert len(b)==ref['bytes'] and sha(b)==ref['sha256']
report="""# N364 original CN skill-list initialization source

PASS finite static source only. Original CN PE582f269535f86e95fcd77946821adf79a30d1bd33f21d566cf48c36fd221b3c8 /47,541,760 bytes is hash-referenced in place, no full image copy or independent mapped-memory pair. Approved own function553BC0 closes at553E86 exclusive:710 code bytes/190 aligned sites, all190 reached by the own finite CFG. All direct branches close on aligned own instructions; no own indirect table. SoleRET24h at553E83 cleans nine DWORD formals. TenCC padding bytes and next553E90 six-byte authentic prologue witness are excluded code. Old710-byte decompiler metadata now agrees with actual return/end, but prior canonical C is not treated as an independent byte-boundary witness. Discovery1024 envelope includes later unrelated functions and remains candidate-only.

Caller is separately retained66 bytes/19sites at54A6A5..54A6E7. ExactCALL is54A6DF (E8DC940000), ending54A6E4;54A6E4 is MOVESI,[EBP-4], not the CALL opcode. This qualifies the approved caller operand span without declaring the interior54A6A5 a function entry or claiming whole54A320 coverage. ImplicitECX L=H+A89658. Reverse PUSH mapping is nine actual formal cells:1 DWORD[H+20];2 DWORD[H+4];3 rawESI;4 H+BE86A8;5 H+BE86AA;6 H+BE86AC;7 DWORD[H+14]+90h;8 zeroextendedWORD[H+A8CC04];9 H+9D223C. Formal7 is EBP+20h, formal9 EBP+28h. Historical decompiler param8/param10 includes implicitthis; do not misnumber them as machine formal8/formal10. RawESI origin is OPEN in this bounded cut. Prior H14=R/H20=U affinities require the genuine prior owner/lifetime and no intervening field replacement; this caller proves live rereads, not arbitrary immutable world identity.

Bank/source relation is direct: formal9 DWORD stores L+3518 at553BF2, so native skill-definition bank is H+9D223C; this equals the already-qualified scene+149DF8+888444 loader namespace. It is the payload after the four-byte cbspec2 header, not the whole resource file. This initializer never parses thatbank, validates its declaredcounts, reads a skillrecord or turns source membership into learned ownership.

Primary first loop has16 iterations/stride2D0. It requests74FC50(destinationL+10+2D0*i,value0,bytes2D0); writes pagecountDWORD atL+2DC+2D0*i=1 and rowrefDWORD atL+2D4+2D0*i=formal7+D8+3EC*i. Actual live H14=R makes this R+90+D8+3EC*i, conditional on the prior provenance. Pageindex atL+2D8+2D0*i becomes signedIDIV remainder by the pagecount. During this loop, the separate100-byte zero request repeats SAME destinationL+26C for all16 iterations; it is not a per-row advancing auxiliary reset. That exact distinction is retained. Zero effects of74FC50 remain conditional on its existing native memset calling contract/readablewritable spans/return; this task neither expands nor executes the CRT child. It is not a synthetic full blank-state constructor.

The rawformal7 BYTECF becomesL+4, BYTED4 becomesL+5. L+C is computed as1+trunc((zeroextendedBYTED4-1)/6) (signed high-product magic2AAAAAAB); under its byte input it is1..43, includingD4==0→1. Native then calls opaque552870/553220, and afterwardsIDIV updatesL+8 using the currentL+C. No postchild nonzero divisor guard or Currentobserver exists here; child/lifetime/faultfree premises remain. No rowcount≤16, usableactor, learning count or page permission is inferred from this arithmetic.

A later16-group pass explicitly ANDs100 WORDs atL+14+2D0*i+2*j with7FFFh, preserving low15 and clearing bit15. It requests100-byte auxiliary clear atL+26C+2D0*i, then directly writes BYTE L+2D0+2D0*i=0. Unlike the earlier constant auxiliary call, this pass advances eachgroup. DWORD L+2E18 is set0, then opaque5540B0/5545C0 refresh children run. GUI window branch reads rawL+2E10 fromformal3+8, casts formal8lowWORD signed for407890, stores returnedAX atL+2E1C and only handle<1000h enters the remaining opaquewindow calls. No GUI/formatter/render/actor descendant was opened.

Secondary is independent:3 groups stride54h, each requestszero-fill atL+2D14+54*i for54bytes and sets pagecountDWORD L+2D60+54*i=1. WORD L+2D10=0100h (two distinctrawbytes), formal6 storesDWORD L+2E34, then opaque552CB0 runs. The final direct pass masks ten WORDs persecondarygroup atL+2D14+54*i+2*j with7FFFh. It does not mean100 secondaryskills or an automatic listcopy. EBX exhaustedloop/callee-saved convention supplies finalthree iterations; the direct masks themselves preserve whatever low15 values are live after the opaquechild.

Thirty-five directmemory destinations/14 staticCALL sites are inventoried; GUI/window and74FC50 effects remain separately opaque/conditional. Neither these resets nor source rowrefs prove a subject→learned battle list materializer, common64-bit actor ID, selected-controller grant or currently usable skill. No global absence follows from this onebody. Native bit15clear is state manipulation, not acquiring/forgetting skills or serverpermission.

Existing original87/38/loader/control bodies are referenced in place and not recredited: actual87 deferred5523F6→554750 retains fullrawWORD/bit14list/bit15state and computeddefinition pointers; actual38 at55240D→554200 testsreturnedAX signed before [H+20]→4D4E00;561BB0 loads the fixed original bank;86/5→54CD80 sets flags/selectednibbles/local clock. These consumers do not provide an actual committed learned issuer or remoteacceptance. The local543/54A parent and45B1C role/presentationprefix remain independent of commonowner identity; no559FB0 actor or UIforest was expanded here.

Original pinned CN catalog still declares125/130/87/111=453; kind0/126 and150 have no declared originalCN rows. CommonOwnerRule metadata is not an original row or a nativeeffect profile. Count125 alone is not an observedS87 incomingreject: the already-qualified554750 rawpointer writer is separate. Physicalbank padding/count-external addresses must not be promoted into definitions. Real blockers remain a separately versioned and qualified CNowner-custom full110/resource/ACT/ROM profile, genuine actor/list/epoch association and actual saved/committed87/control event supplier, with the same common battle/cost/once-settlement rules. This initializer closes source linkage/reset footprint only, not those missing suppliers or gameplay route.

Historical383? scope is explicitly oldselected553C7B..553DF9=382 bytes; currentwhole710 is local staticmethod evidence1. Prior otheroverlaps/history are not recounted, known/globalnewmethodcredit0. Newopcode/format/parser/handler/phase/fullroute credit0. N36326members/496,254 bytes were individually verifiedunchanged. No source product/client edit, native/API/CRT/VM/parser/resourcecodec execution, SQL/DB/build/compiler/tests/import/deploy. Successful helpersLF/noBOM/singleEOF ranonce. The capture emitted a nonfatal Pythoninvalid\m escape warning and malformed TSVheader; originalsuccessfulhelper/TSV remain unchanged, a separate additive header-only copy preserves every190 instructionrow byte. No successfulcapture was rerun, no evidence overwritten.
"""
# No speculative coverage label; explicit exact historical span only.
report=report.replace('Historical383? scope','Historical scope')
put('REPORT.md',report.encode());put('nonfatal-original-TSV-header-warning.txt',b'capture_skill_list_init364.py once exited0; Python SyntaxWarning invalid escape sequence \m at original line27 affected header only. Original helper/TSV retained. Additive correction changes one header byte to TAB, preserving190 instruction rows and native binary/CFG. No capture rerun.\n')
out('PASS.json',dict(verdict='PASS bounded original skill-list initializer source',code_bytes=710,sites=190,caller_bytes=66,caller_sites=19,sole_RET_pop_bytes=36,primary_groups=16,primary_word_masks_per_group=100,secondary_groups=3,secondary_word_masks_per_group=10,bank_source_H9D223C_to_L3518=True,actual_CALL_site='0054A6DF',learned_materializer_or_actor_join_proven=False,original_CN_custom126_150_profile_qualified=False,local_static_method_evidence=1,new_global_method_credit=0,new_route_credit=0,tracked_edits=0,product_execution=0))
helpers=[]
for name in ['discover_skill_list_init364.py','capture_skill_list_init364.py','correct_skill_list_tsv_header364.py','seal_skill_list_init364.py']:
 b=(D/name).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf') and b.endswith(b'\n') and not b.endswith(b'\n\n');helpers.append(dict(path=(D/name).as_posix(),bytes=len(b),sha256=sha(b),successful_execution_count=1))
out('successful-LF-helper-metadata.json',helpers);assert not(D/'seal.json').exists();members=[]
for p in sorted(D.rglob('*')):
 if p.is_file():
  b=p.read_bytes();members.append(dict(path=p.relative_to(D).as_posix(),bytes=len(b),sha256=sha(b)))
for m in members:
 b=(D/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
out('seal.json',dict(member_count=len(members),member_bytes=sum(m['bytes'] for m in members),members=members))
for m in json.loads((D/'seal.json').read_bytes())['members']:
 b=(D/m['path']).read_bytes();assert len(b)==m['bytes'] and sha(b)==m['sha256']
print(json.dumps(dict(member_count=len(members),member_bytes=sum(m['bytes'] for m in members),seal_bytes=len((D/'seal.json').read_bytes()),seal_sha256=sha((D/'seal.json').read_bytes()),helpers=helpers)))
