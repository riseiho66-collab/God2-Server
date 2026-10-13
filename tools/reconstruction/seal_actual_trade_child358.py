from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;h=lambda b:hashlib.sha256(b).hexdigest()
def put(n,b):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def out(n,v):put(n,(json.dumps(v,indent=2)+'\n').encode())
report='''PASS bounded static source closure358: actual trade row refresh child49E0C0.

One authentic whole body49E0C0..49E19D:221 code bytes /73 aligned sites, sole
RET8 at49E19A, five direct branches all internally aligned. CodeSHAa7edbb4540a0d5ec6f4e948335362cb1fbf09b4a7f246bb289aa49f1e9c02bb1,
physicalPE offset644800. Zero qualified data bytes; three postRET NOP bytes are
boundary context only. The240B boundary window is discovery context, not code
coverage. Pinned mapped149c/physicalPE5fcf are read/hash-checked in place; every
retained cut equals both. No fullimage copies, target/native/CRT/API/VM/emulator/
parser/codec/resource/DBSQL/compiler/build/test/import/migrate/deploy execution.
No server tracked file mutation. Existing child tree is not expanded.

Prior35346/190578 and35730/88672 everymember unchanged; extra35570/77600 and
35654/92377 likewise verified. Combined200 members /449227 bytes, safe contained
paths, integer lengths/count/sums and perfile digests. Known caller49DE50 full
184B is referenced in place, not recaptured. Its authentic CALL49DEC9 supplies
ECX=retained suppliedU, group5 and pointerU866E8;49DED9 supplies group7 and pointer
U867A8. Actual WORLD4F primaryUI calling lineage was already qualified353. These
are two auxiliary banks, not canonicalU8560C. No borrower/synthetic fixture is
promoted. The parent itself and all known getters/reset/3B/41/producers gain no
new credit. Selected14 existing353/355/356 qualified ranges do not overlap the
new221B;357 has no whole-body qualification. Novelty is closure of the named
opaque child within this selected frontier, never global corpus novelty.

Formal1 reads signed lowWORD group into EBP with no local range/null guard;
true selected parent supplies5/7. Formal2 is fullDWORD rowbase and retained EBX
starts rowbase+4; EDI starts0 and increments to8 while EBX adds24. Eight supplied
rows and receiver/handle/catalog memory must be readable; normal child return
and native nonvolatile register ABI are explicit prerequisites. No canonical
row count/slot/ownership/rights gate follows from the loop.

First staged read at49E0D5 takes DWORDrow+4 and masks lowWORD key into49B720,
with two own-stack output cells. Those output lowWORDs are loaded signed into
5068C0 UI operands, receiverU+E2170, widgetWORD fromU+232DA4+2*group, slotEDI.
After BOTH children,49E10F rereads live rowDWORD4/key for49B770, with an own-stack
WORD output.49E124 rereads lowkey once more; TEST/JBE takes zero-key display
path. Otherwise signed WORD output<=1 takes empty-string display; only>1 loads
signed rowBYTE0 at49E134 for formatting via opaque5077C0 with literal58D300.
Other paths use known pointer5B4640. No string formatter or UI child is executed
or qualified as pure; literals are operands, no new data text interpretation.

The row+1..3 prefix is neither directly read nor written. Fullrow metadata
+4..23 is not copied; only lowkey/count reads occur. Direct nonstack stores are
ZERO, but child/global effects remain OPEN. Own stack output writes cannot be
called a canonical row write. AX/CX/DX widget partial loads precede FULLDWORD
pushes, retaining upper16 instead of canonicalizing it. Group bounds, current
receiver/row affinity, catalog/UI state and repeated-read consistency remain
conditions. Reads separated by opaque calls are not a single stable snapshot.

This actual trade refund descendant closes an authentic auxiliary field-read
primitive; it proves no reverse full24 copy, incoming full25 supplier, canonical
prefix8560D..F store, native1215/full50 initial population, acquisition or grant.
The genuine canonical material/owned instance-definition-original acquisition
supplier and server issuer remain OPEN. Directbody absence is not global writer
absence or invariance through children. No arbitrary rendering forest, fake
prefix/default fill or inferred entitlement is added.

Accounting:1 newly whole-covered authentic known child /221 distinct code bytes /
73 sites within selected prior opaque frontier. Method coverage may be credited
once for this closure; opcode/format/handler/phase/canonical material/acquisition/
server authority/fullroute credits ZERO. Parent/history/padding/rawwindow excluded.

First static helper failed before native cut because prior353 seal uses member
name rather than path; original and failure preserved, additivev2 succeededonce.
Overlap helper first failed on optional name label absent in prior356span; prior
extra verification output retained, additivev2 only reused byte-equal metadata.
All successful LF/noBOM helpers run once; native cut capture succeedsonce. No
upstream success helper was executed. All failed/partial/corrected custody is
included before immutable seal; no further native scope or359 work begins.
'''
put('REPORT.md',report.encode())
helpers=[]
for n in ['inspect_actual_trade_child358_v2.py','capture_actual_trade_child358.py','verify_selected_frontier358_v2.py','seal_actual_trade_child358.py']:
 b=(O/n).read_bytes();assert b'\r' not in b and not b.startswith(b'\xef\xbb\xbf');helpers.append(dict(path=n,bytes=len(b),sha256=h(b),successful_execution_count=1))
out('successful-LF-helper-metadata.json',helpers)
rows=[]
for p in sorted(O.rglob('*')):
 if not p.is_file():continue
 assert p.resolve().is_relative_to(O.resolve()) and p!=O/'seal.json'
 b=p.read_bytes();rows.append(dict(path=p.relative_to(O).as_posix(),bytes=len(b),sha256=h(b)))
seal=dict(verdict='PASS bounded authentic trade auxiliary-field child closure; canonical material unqualified',member_count=len(rows),member_bytes=sum(r['bytes'] for r in rows),members=rows,excludes='seal.json',qualified_complete_bodies=1,qualified_new_code_bytes=221,qualified_sites=73,data_bytes=0,selected_frontier_method_coverage_credit=1,canonical_material_credit=0,authority_credit=0,fullroute_credit=0)
out('seal.json',seal)
for r in rows:
 b=(O/r['path']).read_bytes();assert len(b)==r['bytes'] and h(b)==r['sha256']
print(json.dumps(dict(seal_sha256=h((O/'seal.json').read_bytes()),seal_bytes=(O/'seal.json').stat().st_size,members=len(rows),member_bytes=seal['member_bytes'],report_sha256=h((O/'REPORT.md').read_bytes()),report_bytes=(O/'REPORT.md').stat().st_size,qualified_code=221,sites=73,data=0)))
